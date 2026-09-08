from typing import Protocol

from lingualoop.core.domain import (
    FeedbackItem,
    LanguageEnum,
    MaterialAnalysis,
    LearningMaterial,
    Message,
    PracticeInstruction,
    ProficiencyLevel,
    ReviewItem,
    SessionEvent,
)


class LearningLLMProvider(Protocol):
    """defining basic protocol of LLM
    protocol is similar to interface in Typescript and Java
    need to be implemented by other classes"""

    async def analyze_material(
        self,
        *,
        material: LearningMaterial,
        target_language: LanguageEnum,
        native_language: LanguageEnum,
    ) -> MaterialAnalysis: ...

    async def generate_task(
        self,
        *,
        material: LearningMaterial,
        learner_level: ProficiencyLevel,
        target_language: LanguageEnum,
    ) -> str: ...

    async def generate_reply(
        self,
        *,
        current_instruction: PracticeInstruction,
        material: LearningMaterial,
        message_history: list[Message],
        user_message: Message,
        corrections: list[FeedbackItem],
        target_language: LanguageEnum,
    ) -> str: ...

    async def correct_answer(
        self,
        *,
        current_instruction: PracticeInstruction,
        user_message: Message,
        target_language: LanguageEnum,
    ) -> list[FeedbackItem]: ...

    async def create_review_items(
        self,
        *,
        corrections: list[FeedbackItem],
        material: LearningMaterial,
    ) -> list[ReviewItem]: ...


class EventStore(Protocol):
    async def append(self, event: SessionEvent) -> None: ...

    async def append_many(self, events: list[SessionEvent]) -> None: ...

    async def list_session_events(self, session_id: str) -> list[SessionEvent]: ...
