from pathlib import Path
from threading import Lock

from app.config import Settings, get_settings


class Diarizer:
    """Lazy optional pyannote wrapper; the core service does not import torch at startup."""

    _pipeline: object | None = None
    _lock = Lock()

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or get_settings()

    def _get_pipeline(self) -> object:
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    try:
                        from pyannote.audio import Pipeline
                    except ImportError as error:
                        raise RuntimeError(
                            "Diarization dependencies are not installed. Install requirements-ml.txt in Python 3.11."
                        ) from error
                    if not self.config.huggingface_token:
                        raise RuntimeError(
                            "HUGGINGFACE_TOKEN is required. Accept the pyannote model terms and add a read token to .env."
                        )
                    self._pipeline = Pipeline.from_pretrained(
                        self.config.diarization_model,
                        use_auth_token=self.config.huggingface_token,
                    )
        return self._pipeline

    def diarize(self, audio_path: Path | str) -> list[dict[str, float | str]]:
        diarization = self._get_pipeline()(str(audio_path))
        return [
            {"start": float(turn.start), "end": float(turn.end), "speaker": str(speaker)}
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]
