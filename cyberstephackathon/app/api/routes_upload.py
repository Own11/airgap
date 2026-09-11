from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_meeting(file: UploadFile = File(...)) -> dict[str, object]:
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio/video format")

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    target = settings.uploads_dir / f"{uuid4().hex}{extension}"
    with target.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            output.write(chunk)

    database = SQLiteDatabase(settings)
    meeting_id = database.create_meeting(file.filename or target.name, target)
    return {"id": meeting_id, "filename": file.filename, "status": "uploaded"}


@router.get("")
async def list_meetings() -> list[dict[str, object]]:
    return SQLiteDatabase(get_settings()).list_meetings()
