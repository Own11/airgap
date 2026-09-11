from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_auth import authenticated_user
from app.config import get_settings
from app.db.sqlite import SQLiteDatabase

router = APIRouter(prefix="/api/meetings", tags=["transcript"])


class ManualTranscript(BaseModel):
    text: str = Field(min_length=1, max_length=500_000)
    language: str = "ru"


@router.post("/{meeting_id}/transcript")
async def save_manual_transcript(
    meeting_id: int,
    payload: ManualTranscript,
    airgap_session: str | None = Cookie(default=None),
) -> dict[str, object]:
    user = authenticated_user(airgap_session)
    database = SQLiteDatabase(get_settings())
    meeting = database.get_meeting(meeting_id)
    if not meeting or meeting.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    transcript = {
        "segments": [{"start": 0.0, "end": 0.0, "speaker": "UNKNOWN", "text": payload.text}],
        "language": payload.language,
        "duration": 0.0,
    }
    import json

    database.update_meeting(meeting_id, status="transcribed", language=payload.language, transcript_json=json.dumps(transcript, ensure_ascii=False), error_message=None)
    return {"id": meeting_id, "status": "transcribed", "transcript": transcript}
