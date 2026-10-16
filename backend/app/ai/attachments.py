"""Files attached to chat messages, loaded from uploads for the model.

Gemini gets images and PDFs as raw bytes and text/code files as text. A request
can only carry so much inline data, so the newest files are kept first and older
ones that don't fit are replaced by a note saying so (never silently dropped).
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services import upload_service

# Gemini's inline request limit is about 20 MB; keep a safety margin
MAX_INLINE_BYTES = 18 * 1024 * 1024
MAX_TEXT_CHARS = 50_000  # per text/code file


@dataclass
class Attachment:
    filename: str
    content_type: str
    data: bytes | None  # None = known file, but left out (too big for this request)


def load_attachments(db: Session, user_id: int, ids_newest_first: Iterable[str]) -> dict[str, Attachment]:
    """{id: Attachment} for the user's files. Ids that don't exist are left out."""
    unique_ids = list(dict.fromkeys(ids_newest_first))
    attachments: dict[str, Attachment] = {}
    budget = MAX_INLINE_BYTES
    for upload, data in upload_service.read_uploads(db, unique_ids, user_id):
        if upload.content_type == "text/plain":
            data = data.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS].encode()
        if len(data) <= budget:
            budget -= len(data)
            attachments[upload.id] = Attachment(upload.filename, upload.content_type, data)
        else:
            attachments[upload.id] = Attachment(upload.filename, upload.content_type, None)
    return attachments
