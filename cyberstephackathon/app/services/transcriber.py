import logging
from pathlib import Path
from threading import Lock

from app.config import Settings, get_settings
from app.models.schemas import MeetingTranscript, TranscriptSegment

logger = logging.getLogger(__name__)


class Transcriber:
    """Lazy, process-local wrapper around faster-whisper."""

    _model: object | None = None
    _model_lock = Lock()

    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or get_settings()

    def _get_model(self) -> object:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    try:
                        # pyrefly: ignore [missing-import]
                        from faster_whisper import WhisperModel
                    except ImportError as error:
                        raise RuntimeError(
                            "Transcription dependencies are not installed. "
                            "Use Python 3.11 and run: pip install -r requirements-stt.txt"
                        ) from error
                    logger.info("Loading local Whisper model: %s", self.config.whisper_model)
                    self._model = WhisperModel(
                        self.config.whisper_model,
                        device=self.config.whisper_device,
                        compute_type=self.config.whisper_compute_type,
                    )
        return self._model

    def transcribe(self, audio_path: Path | str) -> MeetingTranscript:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")

        segments, info = self._get_model().transcribe(
            str(path), language=self.config.whisper_language, vad_filter=True
        )
        transcript_segments = [
            TranscriptSegment(start=segment.start, end=segment.end, speaker="UNKNOWN", text=segment.text.strip())
            for segment in segments
            if segment.text.strip()
        ]
        return MeetingTranscript(
            segments=transcript_segments,
            language=info.language,
            duration=float(info.duration or 0.0),
        )
