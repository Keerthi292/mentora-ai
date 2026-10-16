import json
from collections.abc import AsyncIterator, Mapping

from app.ai.attachments import Attachment
from app.ai.llm_client import LLMError, generate_response, stream_response
from app.ai.prompts import TIP_REQUEST, build_system_prompt
from app.ai.schemas import ChatMessage, ChatRequest, ChatResponse, TipResponse
from app.config import settings


def recent_history(history: list[ChatMessage]) -> list[ChatMessage]:
    """The newest CHAT_HISTORY_LIMIT messages, starting with a user message
    (so the mentor never sees a reply without the question it answered)."""
    limit = settings.CHAT_HISTORY_LIMIT
    recent = history[-limit:] if limit > 0 else []
    while recent and recent[0].role == "assistant":
        recent = recent[1:]
    return recent


def attachment_ids(request: ChatRequest) -> list[str]:
    """Ids of the files the model will see, newest first: this message's
    attachments, then those in the recent history."""
    ids = list(request.attachments)
    for message in reversed(recent_history(request.history)):
        ids.extend(message.attachments)
    return ids


def get_mentor_response(
    request: ChatRequest, profile: str | None, files: Mapping[str, Attachment] | None = None
) -> ChatResponse:
    """Normal (non-streaming) reply. Raises LLMError if the model call fails.

    `profile` is the user's saved data from app/ai/context.py (None if unavailable);
    `files` are the attached files from app/ai/attachments.py.
    """
    reply = generate_response(
        system_prompt=build_system_prompt(profile),
        user_message=request.message,
        history=recent_history(request.history),
        attachments=request.attachments,
        files=files,
    )
    return ChatResponse(response=reply)


def get_daily_tip(profile: str | None) -> TipResponse:
    """One short personal tip for the dashboard. Raises LLMError if the model call fails."""
    tip = generate_response(system_prompt=build_system_prompt(profile), user_message=TIP_REQUEST)
    return TipResponse(tip=tip.strip())


async def stream_mentor_response(
    request: ChatRequest, profile: str | None, files: Mapping[str, Attachment] | None = None
) -> AsyncIterator[str]:
    """Streaming reply, formatted as Server-Sent Events (SSE).

    Success:  data: {"token": "..."} ... data: [DONE]
    Failure:  data: {"error": "..."}  (no [DONE], so the client knows it failed)
    """
    try:
        async for chunk in stream_response(
            build_system_prompt(profile),
            request.message,
            recent_history(request.history),
            request.attachments,
            files,
        ):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    except LLMError as exc:
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    except Exception:
        yield f"data: {json.dumps({'error': 'Something went wrong.'})}\n\n"
