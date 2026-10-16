"""Database access for uploads. No HTTP or business rules here, only queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Upload


def get_upload(db: Session, upload_id: str, user_id: int) -> Upload | None:
    # Filter by user_id too, so users can only see their own files
    stmt = select(Upload).where(Upload.id == upload_id, Upload.user_id == user_id)
    return db.scalars(stmt).first()


def get_uploads(db: Session, upload_ids: list[str], user_id: int) -> dict[str, Upload]:
    """{id: Upload} for the ids that exist and belong to the user."""
    if not upload_ids:
        return {}
    stmt = select(Upload).where(Upload.id.in_(upload_ids), Upload.user_id == user_id)
    return {upload.id: upload for upload in db.scalars(stmt)}


def create_upload(db: Session, data: dict) -> Upload:
    upload = Upload(**data)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def delete_upload(db: Session, upload: Upload) -> None:
    db.delete(upload)
    db.commit()
