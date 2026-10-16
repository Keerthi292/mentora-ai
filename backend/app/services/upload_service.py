"""Business rules for uploaded files: allowed types, size limit, storage on disk.

The file type is decided from the file's first bytes (not its name or the
browser's Content-Type), and text files are always served as text/plain, so an
uploaded .html file can never run as a web page.
"""

import secrets
from pathlib import Path, PurePath

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Upload
from app.repositories import upload_repository

CHUNK = 1024 * 1024

# First bytes of each allowed binary type
_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"%PDF-", "application/pdf"),
]

# Text and code files, accepted if they are valid UTF-8
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml", ".ini", ".xml", ".log",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".sql", ".sh",
    ".java", ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".rb", ".php", ".kt", ".swift",
}

ALLOWED_DESCRIPTION = "images (PNG, JPEG, WebP, GIF), PDFs, or text/code files"


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _detect_type(head: bytes, filename: str, data_path: Path) -> str | None:
    for signature, content_type in _SIGNATURES:
        if head.startswith(signature):
            return content_type
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if PurePath(filename).suffix.lower() in TEXT_EXTENSIONS:
        try:
            data_path.read_text(encoding="utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            return None
    return None


def file_path(upload_id: str) -> Path:
    return Path(settings.UPLOAD_DIR) / upload_id


async def save_upload(db: Session, user_id: int, file: UploadFile) -> Upload:
    """Check and store an uploaded file. 400 for a wrong type, 413 if too big."""
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    upload_id = secrets.token_hex(16)
    path = file_path(upload_id)
    size = 0
    head = b""
    try:
        # Stream to disk in chunks, stopping as soon as the limit is passed
        with path.open("wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File is too large (max {settings.MAX_UPLOAD_MB} MB).",
                    )
                if len(head) < 16:
                    head += chunk[: 16 - len(head)]
                out.write(chunk)

        if size == 0:
            raise _bad_request("The file is empty.")
        filename = PurePath(file.filename or "file").name[:255]  # no folders, just the name
        content_type = _detect_type(head, filename, path)
        if content_type is None:
            raise _bad_request(f"Unsupported file type. Upload {ALLOWED_DESCRIPTION}.")

        return upload_repository.create_upload(
            db,
            {"id": upload_id, "user_id": user_id, "filename": filename, "content_type": content_type, "size": size},
        )
    except BaseException:
        path.unlink(missing_ok=True)  # never keep a rejected or half-written file
        raise


def get_upload(db: Session, upload_id: str, user_id: int) -> Upload:
    upload = upload_repository.get_upload(db, upload_id, user_id)
    if upload is None or not file_path(upload.id).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return upload


def delete_upload(db: Session, upload_id: str, user_id: int) -> None:
    upload = upload_repository.get_upload(db, upload_id, user_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    upload_repository.delete_upload(db, upload)
    file_path(upload_id).unlink(missing_ok=True)


def read_uploads(db: Session, upload_ids: list[str], user_id: int) -> list[tuple[Upload, bytes]]:
    """The user's files with their bytes, in the given order. Missing ones are skipped."""
    found = upload_repository.get_uploads(db, upload_ids, user_id)
    files = []
    for upload_id in upload_ids:
        upload = found.get(upload_id)
        path = file_path(upload_id)
        if upload is not None and path.is_file():
            files.append((upload, path.read_bytes()))
    return files
