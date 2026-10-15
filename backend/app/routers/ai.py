from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.ai.agent import get_mentor_response, stream_mentor_response
from app.ai.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/ai", tags=["AI Mentor"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return get_mentor_response(request)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_mentor_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # stops proxies like nginx from buffering
        },
    )