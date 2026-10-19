from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

MAX_ATTACHMENTS = 5  # files per message

# Empty text is allowed when the message has attachments (checked below)
MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=2000),
]

# Earlier messages can be longer: they include the mentor's own replies
HistoryText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=20000),
]

# An uploaded file's id (from POST /api/uploads)
AttachmentId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]


class ChatMessage(BaseModel):
    """One earlier message in the conversation."""

    role: Literal["user", "assistant"]
    content: HistoryText = ""
    attachments: list[AttachmentId] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)

    @model_validator(mode="after")
    def not_empty(self):
        if not self.content and not self.attachments:
            raise ValueError("A message needs text or attachments")
        return self


class ChatRequest(BaseModel):
    message: MessageText = ""
    # Files uploaded with this message
    attachments: list[AttachmentId] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)
    # Earlier messages of this conversation, oldest first. Only the newest
    # CHAT_HISTORY_LIMIT are used (see app/ai/agent.py).
    history: list[ChatMessage] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def not_empty(self):
        if not self.message and not self.attachments:
            raise ValueError("Type a message or attach a file")
        return self


class ChatResponse(BaseModel):
    response: str


class TipResponse(BaseModel):
    tip: str


# --- Page assistant (the small chat on the Skills, Goals, Career and Projects pages) ---


class AssistantRequest(BaseModel):
    page: Literal["skills", "goals", "career", "projects"]
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    # Earlier messages of this little chat, oldest first
    history: list[ChatMessage] = Field(default_factory=list, max_length=40)


class AssistantResponse(BaseModel):
    reply: str
    # What was changed, e.g. "Updated Docker (DevOps, advanced, learning)"
    actions: list[str]
    changed: bool  # True if the page should reload its data
