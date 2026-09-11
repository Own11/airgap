# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class TranscriptSegment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start: float = Field(ge=0)
    end: float = Field(ge=0)
    speaker: str = "UNKNOWN"
    text: str


class MeetingTranscript(BaseModel):
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str | None = None
    duration: float = Field(default=0.0, ge=0)


class ActionItem(BaseModel):
    assignee: str | None = None
    task: str
    deadline: str | None = None
    priority: str = "medium"


class MeetingProtocol(BaseModel):
    summary: str
    decisions: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
