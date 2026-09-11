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
            "Ты аккуратный секретарь встречи. Анализируй ТОЛЬКО факты из транскрипта. "
            "Ничего не выдумывай и не повторяй случайные фразы как решения или задачи. "
            "Если в тексте нет решений, вопросов, задач или рисков — верни пустой массив. "
            "Ответь только одним валидным JSON без markdown и пояснений. "
            "Используй ровно такую структуру: "
            '{"summary":"3-5 предложений о фактах встречи",'
            '"decisions":[],"topics":[],"open_questions":[],'
            '"action_items":[{"assignee":null,"task":"","deadline":null,"priority":"medium"}],'
            '"risks":[]}. '
            "В action_items добавляй только явно сформулированные поручения; не создавай задачу из вопроса. "
            "Язык ответа — русский.\n\nТРАНСКРИПТ:\n" + text
        )
        async with httpx.AsyncClient(base_url=self.config.ollama_base_url, timeout=180) as client:
            response = await client.post(
                "/api/generate",
                json={
                    "model": self.config.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "num_predict": 500},
                },
            )
            response.raise_for_status()
        payload: dict[str, Any] = response.json()
        result = json.loads(payload["response"])
        return MeetingProtocol.model_validate(result)
