import json

from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase
from app.services.transcriber import Transcriber
from app.api.routes_auth import authenticated_user

router = APIRouter(prefix="/api/meetings", tags=["processing"])


def process_meeting(meeting_id: int) -> None:
    database = SQLiteDatabase(get_settings())
    meeting = database.get_meeting(meeting_id)
    if meeting is None:
        return
    try:
        database.update_meeting(meeting_id, status="processing")
        transcript = Transcriber().transcribe(meeting["file_path"])
        database.update_meeting(
            meeting_id,
            status="transcribed",
            language=transcript.language,
            duration=transcript.duration,
            transcript_json=json.dumps(transcript.model_dump(), ensure_ascii=False),
        )
    except Exception as error:
        database.update_meeting(meeting_id, status="failed", error_message=str(error))


@router.post("/{meeting_id}/process", status_code=202)
async def start_processing(meeting_id: int, background_tasks: BackgroundTasks, airgap_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user = authenticated_user(airgap_session)
    database = SQLiteDatabase(get_settings())
    meeting = database.get_meeting(meeting_id)
    if meeting is None or meeting.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting["status"] == "processing":
        return {"id": meeting_id, "status": "processing"}
    database.update_meeting(meeting_id, error_message=None, protocol_json=None)
    background_tasks.add_task(process_meeting, meeting_id)
    return {"id": meeting_id, "status": "processing"}


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: int, airgap_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user = authenticated_user(airgap_session)
    meeting = SQLiteDatabase(get_settings()).get_meeting(meeting_id)
    if meeting is None or meeting.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for key in ("transcript_json", "protocol_json"):
        if meeting.get(key):
            meeting[key] = json.loads(meeting[key])
    return meeting
