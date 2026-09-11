from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Cookie, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase
from app.api.routes_auth import authenticated_user

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_meeting(file: UploadFile = File(...), airgap_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user = authenticated_user(airgap_session)
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio/video format")

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    target = settings.uploads_dir / f"{uuid4().hex}{extension}"
    size = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_size_mb * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="File is too large")
                output.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise

    database = SQLiteDatabase(settings)
    meeting_id = database.create_meeting(file.filename or target.name, target, int(user["id"]))
    return {"id": meeting_id, "filename": file.filename, "status": "uploaded"}


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: int, airgap_session: str | None = Cookie(default=None)) -> None:
    user = authenticated_user(airgap_session)
    database = SQLiteDatabase(get_settings())
    file_path = database.delete_meeting(meeting_id, int(user["id"]))
    if file_path is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    Path(file_path).unlink(missing_ok=True)


@router.get("")
async def list_meetings(airgap_session: str | None = Cookie(default=None)) -> list[dict[str, object]]:
    user = authenticated_user(airgap_session)
    return SQLiteDatabase(get_settings()).list_meetings(int(user["id"]))
