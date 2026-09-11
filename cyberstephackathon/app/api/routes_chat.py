import json

import httpx
from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_auth import authenticated_user
from app.config import get_settings
from app.db.sqlite import SQLiteDatabase

router = APIRouter(prefix="/api/meetings", tags=["chat"])


class ChatMessage(BaseModel):
    question: str = Field(min_length=1, max_length=5_000)


@router.post("/{meeting_id}/chat")
async def chat_about_meeting(
    meeting_id: int,
    payload: ChatMessage,
    airgap_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    user = authenticated_user(airgap_session)
    meeting = SQLiteDatabase(get_settings()).get_meeting(meeting_id)
    if not meeting or meeting.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.get("transcript_json"):
        raise HTTPException(status_code=409, detail="Transcript is not ready")
    transcript = json.loads(meeting["transcript_json"])
    protocol = json.loads(meeting["protocol_json"]) if meeting.get("protocol_json") else {}
    question = payload.question.lower()
    if any(word in question for word in ("решени", "решено", "решили")):
        decisions = protocol.get("decisions", [])
        return {"answer": "\n".join(decisions) if decisions else "В протоколе встречи решения не зафиксированы."}
    if any(word in question for word in ("задач", "поручен", "action item")):
        actions = protocol.get("action_items", [])
        if not actions:
            return {"answer": "В протоколе встречи поручения не зафиксированы."}
        return {"answer": "\n".join(f"{item.get('task', '')} — {item.get('assignee') or 'ответственный не указан'}" for item in actions)}
    if any(word in question for word in ("риск", "блокер", "проблем")):
        risks = protocol.get("risks", [])
        return {"answer": "\n".join(risks) if risks else "В протоколе встречи риски и блокеры не зафиксированы."}
    context = "\n".join(segment["text"] for segment in transcript["segments"])
    prompt = (
        "Ответь только по приведённому транскрипту. Не выдумывай факты, имена и события. "
        "Если ответа нет, ответь: В транскрипте ответа нет.\n"
        f"ТРАНСКРИПТ:\n{context}\nВОПРОС: {payload.question}"
    )
    try:
        async with httpx.AsyncClient(base_url=get_settings().ollama_base_url, timeout=120) as client:
            response = await client.post("/api/generate", json={"model": get_settings().ollama_model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "num_predict": 250}})
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"Local Ollama unavailable: {error}") from error
    return {"answer": response.json().get("response", "")}
