import json
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.models.schemas import MeetingProtocol, MeetingTranscript


class MeetingAnalyzer:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or get_settings()

    async def analyze(self, transcript: MeetingTranscript) -> MeetingProtocol:
        text = "\n".join(f"{segment.speaker}: {segment.text}" for segment in transcript.segments)
        prompt = (
            "Проанализируй протокол встречи на русском языке. Верни только JSON без markdown "
            "с полями summary (строка), decisions (массив строк), topics (массив строк), "
            "open_questions (массив строк), action_items (массив объектов assignee/task/deadline/priority), "
            "risks (массив строк).\n\nТРАНСКРИПТ:\n" + text
        )
        async with httpx.AsyncClient(base_url=self.config.ollama_base_url, timeout=180) as client:
            response = await client.post(
                "/api/generate",
                json={"model": self.config.ollama_model, "prompt": prompt, "stream": False, "format": "json"},
            )
            response.raise_for_status()
        payload: dict[str, Any] = response.json()
        result = json.loads(payload["response"])
        return MeetingProtocol.model_validate(result)
