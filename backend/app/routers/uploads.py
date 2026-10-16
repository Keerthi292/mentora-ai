from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.schemas import UploadResponse
from app.services import upload_service

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload an image, PDF or text/code file (max MAX_UPLOAD_MB)."""
    return await upload_service.save_upload(db, user_id, file)


@router.get("/{upload_id}")
def download_file(
    upload_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> FileResponse:
    upload = upload_service.get_upload(db, upload_id, user_id)
    media_type = upload.content_type
    if media_type == "text/plain":
        media_type = "text/plain; charset=utf-8"
    return FileResponse(
        upload_service.file_path(upload.id),
        media_type=media_type,
        headers={
            # Show in the browser, keep the original name when saved
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(upload.filename)}",
            # Never let the browser guess a different (e.g. HTML) type
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=31536000, immutable",
        },
    )


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    upload_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    upload_service.delete_upload(db, upload_id, user_id)
