import json

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Response

from app.config import get_settings
from app.db.sqlite import SQLiteDatabase
from app.models.schemas import MeetingProtocol, MeetingTranscript
from app.services.analyzer import MeetingAnalyzer
from app.services.exporter import export_csv, export_json, export_pdf
from app.api.routes_auth import authenticated_user

router = APIRouter(prefix="/api/meetings", tags=["results"])


@router.post("/{meeting_id}/analyze")
async def analyze_meeting(meeting_id: int, airgap_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user = authenticated_user(airgap_session)
    database = SQLiteDatabase(get_settings())
    meeting = database.get_meeting(meeting_id)
    if not meeting or meeting.get("user_id") != user["id"] or not meeting.get("transcript_json"):
        raise HTTPException(status_code=409, detail="Transcript is not ready")
    transcript = MeetingTranscript.model_validate(json.loads(meeting["transcript_json"]))
    try:
        protocol = await MeetingAnalyzer().analyze(transcript)
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(status_code=503, detail=f"Local Ollama analysis unavailable: {error}") from error
    database.update_meeting(meeting_id, status="analyzed", protocol_json=json.dumps(protocol.model_dump(), ensure_ascii=False))
    return protocol.model_dump()


@router.get("/{meeting_id}/export/{format}")
async def export_meeting(meeting_id: int, format: str, airgap_session: str | None = Cookie(default=None)) -> Response:
    user = authenticated_user(airgap_session)
    meeting = SQLiteDatabase(get_settings()).get_meeting(meeting_id)
    if not meeting or meeting.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    protocol = MeetingProtocol.model_validate(json.loads(meeting["protocol_json"])) if meeting.get("protocol_json") else None
    transcript = MeetingTranscript.model_validate(json.loads(meeting["transcript_json"])) if meeting.get("transcript_json") else None
    if format == "json":
        return Response(export_json(transcript, protocol), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="meeting-{meeting_id}.json"'})
    if format == "csv" and protocol:
        return Response(export_csv(protocol), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="meeting-{meeting_id}.csv"'})
    if format == "pdf" and protocol:
        return Response(export_pdf(protocol), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="meeting-{meeting_id}.pdf"'})
    raise HTTPException(status_code=409, detail="Requested export is not available")
