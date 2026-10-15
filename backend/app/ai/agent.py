import json
from collections.abc import AsyncIterator

from app.ai.llm_client import generate_mock_response, stream_mock_response
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.schemas import ChatRequest, ChatResponse


def get_mentor_response(request: ChatRequest) -> ChatResponse:
    """Normal (non-streaming) reply."""
    reply = generate_mock_response(
        system_prompt=SYSTEM_PROMPT,
        user_message=request.message,
    )
    return ChatResponse(response=reply)


async def stream_mentor_response(request: ChatRequest) -> AsyncIterator[str]:
    """Streaming reply, formatted as Server-Sent Events (SSE)."""
    try:
        async for chunk in stream_mock_response(SYSTEM_PROMPT, request.message):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        yield f"data: {json.dumps({'error': 'Something went wrong.'})}\n\n"