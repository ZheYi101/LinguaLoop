from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Language ability level(A1 is lowest)
class ProficiencyLevel(StrEnum):
    """user's ability of target language"""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    UNKNOWN = "unknown"


class CorrectionIntensity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MaterialSourceType(StrEnum):
    TEXT = "text"
    ARTICLE = "article"
    SUBTITLE = "subtitle"
    CHAT_LOG = "chat_log"
    NOTE = "note"
    OTHER = "other"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackType(StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    FLUENCY = "fluency"
    PRAGMATICS = "pragmatics"
    OTHER = "other"


class ReviewItemKind(StrEnum):
    CLOZE = "cloze"  # Fill-in-the-Blank
    REWRITE = "rewrite"
    RECALL = "recall"
    EXPRESSION = "expression"


class SessionEventType(StrEnum):
    SESSION_STARTED = "session.started"
    USER_MESSAGE_ADDED = "message.user_added"
    ASSISTANT_MESSAGE_ADDED = "message.assistant_added"
    FEEDBACK_CREATED = "feedback.created"
    REVIEW_ITEMS_CREATED = "review_items.created"
    SESSION_COMPLETED = "session.completed"


class LanguageEnum(StrEnum):
    """contain all supported language(in fact just randomly listed)"""

    CHINESE = "chinese"
    ENGLISH = "english"
    JAPANESE = "japanese"
    FRENCH = "french"
    GERMANY = "germany"
    SPANISH = "spanish"


class CapabilityRequirement(DomainModel):
    name: str
    min_version: str = "1.0"
    optional: bool = False


class UserProfile(DomainModel):
    id: str = Field(default_factory=lambda: new_id("user"))
    native_language: LanguageEnum
    target_language: LanguageEnum
    learner_level: ProficiencyLevel = ProficiencyLevel.UNKNOWN
    correction_intensity: CorrectionIntensity = CorrectionIntensity.MEDIUM
    goals: list[str] = Field(default_factory=list)

    @field_validator("native_language", "target_language")
    @classmethod
    def _language_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("language fields must not be blank")
        return value


class MaterialExpression(DomainModel):
    text: str
    meaning: str | None = None
    example: str | None = None


class MaterialAnalysis(DomainModel):
    summary: str
    keywords: list[str] = Field(default_factory=list)
    expressions: list[MaterialExpression] = Field(default_factory=list)
    difficulties: list[str] = Field(default_factory=list)
    suggested_goals: list[str] = Field(default_factory=list)


class LearningMaterial(DomainModel):
    id: str = Field(default_factory=lambda: new_id("mat"))
    title: str
    target_language: LanguageEnum
    native_language: LanguageEnum
    content: str
    source_type: MaterialSourceType = MaterialSourceType.TEXT
    analysis: MaterialAnalysis | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("title", "target_language", "native_language", "content")
    @classmethod
    def _required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("required text fields must not be blank")
        return value


class PracticeInstruction(DomainModel):
    """a concrete practice instruction produced by ai,
    which equals to a small task to practice, inside a `PracticeSession`"""

    id: str = Field(default_factory=lambda: new_id("instruction"))
    prompt: str
    expected_output: str | None = None
    focus_points: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PracticePlan(DomainModel):
    id: str = Field(default_factory=lambda: new_id("plan"))
    pattern_id: str
    title: str
    instructions: list[PracticeInstruction] = Field(default_factory=list)


class Message(DomainModel):
    """refer to all sentences shown in the chat block, no matter by human or ai"""

    id: str = Field(default_factory=lambda: new_id("msg"))
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)
    feedback_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def _content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message content must not be blank")
        return value


class FeedbackItem(DomainModel):
    id: str = Field(default_factory=lambda: new_id("feedback"))
    error_type: FeedbackType | str = FeedbackType.OTHER
    original: str
    corrected: str
    explanation: str
    source_message_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ReviewItem(DomainModel):
    id: str = Field(default_factory=lambda: new_id("review"))
    kind: ReviewItemKind = ReviewItemKind.CLOZE
    prompt: str
    answer: str
    source_feedback_id: str | None = None
    source_session_id: str | None = None
    due_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class PracticeSession(DomainModel):
    id: str = Field(default_factory=lambda: new_id("session"))
    material_id: str
    pattern_id: str
    learner_level: ProficiencyLevel
    status: SessionStatus = SessionStatus.ACTIVE
    plan: PracticePlan | None = None
    messages: list[Message] = Field(default_factory=list)
    feedback_items: list[FeedbackItem] = Field(default_factory=list)
    review_items: list[ReviewItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def current_instruction(self) -> PracticeInstruction | None:
        if self.plan is None or not self.plan.instructions:
            return None
        return self.plan.instructions[-1]  # return the latest instruction


class SessionEvent(DomainModel):
    id: str = Field(default_factory=lambda: new_id("event"))
    session_id: str
    event_type: SessionEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=utc_now)


class PatternManifest(DomainModel):
    id: str
    name: str
    description: str
    required_capabilities: list[str] = Field(default_factory=list)


class PluginManifest(DomainModel):
    id: str
    name: str
    version: str
    provided_capabilities: list[str] = Field(default_factory=list)
