"""Talks to the Gemini API (official Google Gen AI SDK, package `google-genai`).

The rest of the app only sees `generate_response`, `stream_response`,
`generate_json` (structured answers, e.g. a parsed resume) and
`generate_with_tools` (the page assistant), plus `LLMError`.
Every failure is raised as an LLMError with a message that is safe to show to
the user; nothing here returns a fake reply.
"""

import logging
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from contextlib import aclosing
from functools import lru_cache
from typing import TypeVar

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.ai.attachments import Attachment
from app.ai.schemas import ChatMessage
from app.config import settings

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMError(Exception):
    """A model call failed. `str(error)` is safe to show to the user."""

    status_code = 502  # HTTP status for the non-streaming endpoint

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class LLMNotConfiguredError(LLMError):
    status_code = 503


class LLMRateLimitError(LLMError):
    status_code = 429


# Gemini sometimes answers "503 overloaded" or another 5xx for a moment. Try a
# request up to 3 times, waiting ~1 s then ~2 s. 429 (quota / rate limit) is not
# retried: those don't clear in seconds, and the user gets a message saying when.
RETRY_ATTEMPTS = 3
RETRY_STATUS_CODES = [500, 502, 503, 504]


def _http_options(timeout_seconds: float) -> types.HttpOptions:
    return types.HttpOptions(
        timeout=int(timeout_seconds * 1000),
        retry_options=types.HttpRetryOptions(
            attempts=RETRY_ATTEMPTS,
            initial_delay=1.0,
            max_delay=4.0,
            jitter=0.5,
            http_status_codes=RETRY_STATUS_CODES,
        ),
    )


@lru_cache
def _create_client(api_key: str, timeout_seconds: float) -> genai.Client:
    # Cached per key/timeout, so a changed setting gets a fresh client
    return genai.Client(api_key=api_key, http_options=_http_options(timeout_seconds))


def _get_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY.get_secret_value().strip() if settings.GEMINI_API_KEY else ""
    if not api_key:
        raise LLMNotConfiguredError(
            "The AI mentor is not configured: GEMINI_API_KEY is missing in backend/.env."
        )
    return _create_client(api_key, settings.GEMINI_TIMEOUT_SECONDS)


def _config(system_prompt: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(system_instruction=system_prompt)


# Files Gemini can read as raw bytes; text files are sent as text instead
_INLINE_TYPES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}


def _file_parts(ids: Sequence[str], files: Mapping[str, Attachment]) -> list[types.Part]:
    parts = []
    for file_id in ids:
        file = files.get(file_id)
        if file is None:
            parts.append(types.Part(text="[An attached file is no longer available.]"))
        elif file.data is None:
            parts.append(types.Part(text=f'[Attached file "{file.filename}" was left out: too large to resend.]'))
        elif file.content_type in _INLINE_TYPES:
            parts.append(types.Part(text=f'Attached file "{file.filename}":'))
            parts.append(types.Part.from_bytes(data=file.data, mime_type=file.content_type))
        elif file.content_type == "text/plain":
            text = file.data.decode("utf-8", errors="replace")
            parts.append(types.Part(text=f'Attached file "{file.filename}":\n```\n{text}\n```'))
        else:
            parts.append(types.Part(text=f'[Attached file "{file.filename}" ({file.content_type}) can\'t be read by the model.]'))
    return parts


def _contents(
    user_message: str,
    history: Sequence[ChatMessage],
    attachments: Sequence[str] = (),
    files: Mapping[str, Attachment] | None = None,
) -> list[types.Content]:
    """The conversation in Gemini's format: earlier turns, then the new message.

    Each message becomes its text plus its attached files. Gemini calls the
    assistant "model". Back-to-back messages from the same side (e.g. a question
    whose reply failed, then a retry) are joined into one turn.
    """
    files = files or {}
    messages = [*((m.role, m.content, m.attachments) for m in history), ("user", user_message, attachments)]
    turns: list[tuple[str, list[types.Part]]] = []
    for role, text, ids in messages:
        gemini_role = "model" if role == "assistant" else "user"
        parts = ([types.Part(text=text)] if text else []) + _file_parts(ids, files)
        if turns and turns[-1][0] == gemini_role:
            previous = turns[-1][1]
            if previous and parts and previous[-1].text is not None and parts[0].text is not None:
                previous[-1] = types.Part(text=f"{previous[-1].text}\n\n{parts[0].text}")
                parts = parts[1:]
            previous.extend(parts)
        else:
            turns.append((gemini_role, parts))
    return [types.Content(role=role, parts=parts) for role, parts in turns]


def _rate_limit_message(exc: errors.APIError) -> str:
    """Say which Gemini limit was hit and when to retry, from the 429 error's details."""
    daily = False
    retry_seconds = None
    details = (exc.details or {}).get("error", {}).get("details", []) if isinstance(exc.details, dict) else []
    for detail in details:
        for violation in detail.get("violations", []):
            if "PerDay" in str(violation.get("quotaId", "")):
                daily = True
        delay = str(detail.get("retryDelay", ""))
        if delay.endswith("s"):
            try:
                retry_seconds = float(delay[:-1])
            except ValueError:
                pass

    if retry_seconds is None:
        wait = "in a moment"
    elif retry_seconds >= 3600:
        wait = f"in about {round(retry_seconds / 3600)} hours"
    elif retry_seconds >= 60:
        wait = f"in about {round(retry_seconds / 60)} minutes"
    else:
        wait = f"in {max(1, round(retry_seconds))} seconds"

    if daily:
        return (
            f"Today's free Gemini limit for this model is used up. It resets {wait}. "
            "(You can switch GEMINI_MODEL in backend/.env to keep chatting.)"
        )
    return f"The AI mentor is receiving too many requests right now. Please try again {wait}."


def _to_llm_error(exc: Exception) -> LLMError:
    """Turn an SDK / network exception into an LLMError and log it (never the key)."""
    if isinstance(exc, LLMError):
        return exc

    if isinstance(exc, errors.APIError):
        logger.warning("Gemini API error %s %s: %s", exc.code, exc.status, exc.message)
        if exc.code == 429:
            return LLMRateLimitError(_rate_limit_message(exc))
        if exc.code in (401, 403) or (exc.code == 400 and "API key" in (exc.message or "")):
            return LLMNotConfiguredError(
                "The AI mentor is not configured correctly: Gemini rejected the API key."
            )
        if exc.code == 404:
            return LLMNotConfiguredError(
                f'The AI mentor is not configured correctly: Gemini model "{settings.GEMINI_MODEL}" was not found.'
            )
        if exc.code is not None and exc.code >= 500:
            return LLMError("The AI service is temporarily unavailable. Please try again.", 503)
        return LLMError("The AI service could not process this request.")

    if isinstance(exc, httpx.TimeoutException):
        logger.warning("Gemini request timed out")
        return LLMError("The AI service took too long to respond. Please try again.", 504)

    if isinstance(exc, httpx.HTTPError):
        logger.warning("Could not reach Gemini: %s", type(exc).__name__)
        return LLMError("Could not reach the AI service. Please try again.", 503)

    logger.exception("Unexpected error while calling Gemini")
    return LLMError("Something went wrong while generating a reply.")


def _blocked_message(response: types.GenerateContentResponse) -> str:
    """Explain an empty reply (usually blocked by Gemini's safety filters)."""
    feedback = response.prompt_feedback
    if feedback and feedback.block_reason:
        logger.info("Gemini blocked the prompt: %s", feedback.block_reason)
    return "The AI mentor could not answer this message. Please try rephrasing it."


def generate_response(
    system_prompt: str,
    user_message: str,
    history: Sequence[ChatMessage] = (),
    attachments: Sequence[str] = (),
    files: Mapping[str, Attachment] | None = None,
) -> str:
    """Return the model's full reply. `history` is the earlier conversation, oldest first."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=_contents(user_message, history, attachments, files),
            config=_config(system_prompt),
        )
    except Exception as exc:
        raise _to_llm_error(exc) from exc

    text = response.text
    if not text:
        raise LLMError(_blocked_message(response))
    return text


def generate_json(system_prompt: str, parts: Sequence[types.Part], schema: type[ModelT]) -> ModelT:
    """Ask for a reply shaped like the Pydantic model `schema` (Gemini's JSON mode) and parse it."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[types.Content(role="user", parts=list(parts))],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
    except Exception as exc:
        raise _to_llm_error(exc) from exc

    if not response.text:
        raise LLMError(_blocked_message(response))
    try:
        return schema.model_validate_json(response.text)
    except ValidationError as exc:
        logger.warning("Gemini returned JSON that doesn't match %s: %s", schema.__name__, exc)
        raise LLMError("The AI service returned an unexpected answer. Please try again.") from exc


# Most requests need 1-2 tool calls; stop a model that keeps calling tools
MAX_TOOL_ROUNDS = 6


def generate_with_tools(
    system_prompt: str,
    user_message: str,
    history: Sequence[ChatMessage],
    tools: Sequence[types.FunctionDeclaration],
    call_tool: Callable[[str, dict], dict],
) -> str:
    """Let Gemini call `tools` (run by `call_tool(name, args)`) until it answers with text."""
    client = _get_client()
    contents = _contents(user_message, history)
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[types.Tool(function_declarations=list(tools))],
    )
    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = client.models.generate_content(model=settings.GEMINI_MODEL, contents=contents, config=config)
        except Exception as exc:
            raise _to_llm_error(exc) from exc

        calls = response.function_calls
        if not calls:
            if not response.text:
                raise LLMError(_blocked_message(response))
            return response.text
        # Send the model's turn back unchanged (it carries Gemini's thought signatures),
        # then the result of each call
        contents.append(response.candidates[0].content)
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(name=call.name, response=call_tool(call.name, dict(call.args or {})))
                    for call in calls
                ],
            )
        )
    raise LLMError("That took too many steps. Please ask for one change at a time.")


async def stream_response(
    system_prompt: str,
    user_message: str,
    history: Sequence[ChatMessage] = (),
    attachments: Sequence[str] = (),
    files: Mapping[str, Attachment] | None = None,
) -> AsyncIterator[str]:
    """Yield the model's reply as text chunks, as Gemini produces them."""
    client = _get_client()
    got_text = False
    last_chunk = None
    try:
        stream = await client.aio.models.generate_content_stream(
            model=settings.GEMINI_MODEL,
            contents=_contents(user_message, history, attachments, files),
            config=_config(system_prompt),
        )
        # aclosing() closes the Gemini connection if our caller stops early
        # (e.g. the browser disconnected)
        async with aclosing(stream):
            async for chunk in stream:
                last_chunk = chunk
                if chunk.text:
                    got_text = True
                    yield chunk.text
    except Exception as exc:
        raise _to_llm_error(exc) from exc

    if not got_text:
        if last_chunk is None:
            raise LLMError("The AI mentor returned an empty reply. Please try again.")
        raise LLMError(_blocked_message(last_chunk))
