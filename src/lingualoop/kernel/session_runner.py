from __future__ import annotations

from pydantic import BaseModel, Field
from requests import session

from lingualoop.core.domain import (
    CapabilityRequirement,
    FeedbackItem,
    LearningMaterial,
    Message,
    MessageRole,
    PracticeInstruction,
    PracticePlan,
    PracticeSession,
    ProficiencyLevel,
    ReviewItem,
    SessionEvent,
    SessionEventType,
    utc_now,
)
from lingualoop.core.ports import EventStore, LearningLLMProvider

DEFAULT_PATTERN_ID = "guided_roleplay"


class SessionStepResult(BaseModel):
    session: PracticeSession
    events: list[SessionEvent] = Field(default_factory=list)
    assistant_message: Message | None = None
    feedback_items: list[FeedbackItem] = Field(default_factory=list)
    review_items: list[ReviewItem] = Field(default_factory=list)


class DirectLearningSessionRunner:
    """Deterministic business runner before Langgraph owns orchestration"""

    def __init__(
        self, llm_provider: LearningLLMProvider, event_store: EventStore
    ) -> None:
        self._llm_provider = llm_provider
        self._event_store = event_store

    # todo: 完成这里; 还没写完这个文件
