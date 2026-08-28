from typing import Protocol

from lingualoop.core.domain import FeedbackItem, Message, ReviewItem, SessionEvent


class LearningLLMProvider(Protocol):
    async def generate_task(
        self, *, material_text: str, learner_level: str, target_language: str
    ) -> str: ...

    async def generate_reply(
        self,
        *,
        task: str,
        material_text: str,
        message_history: list[Message],
        user_message: str,
        corrections: list[FeedbackItem],
        target_language: str,
    ) -> str: ...

    async def correct_answer(
        self,
        *,
        task: str,
        user_message: str,
        target_language: str,
    ) -> list[FeedbackItem]: ...

    async def create_review_items(
        self,
        *,
        corrections: list[FeedbackItem],
        material_text: str,
    ) -> list[ReviewItem]: ...


class EventStore(Protocol):
    async def append(self, event: SessionEvent) -> None: ...

    async def append_many(self, events: list[SessionEvent]) -> None: ...

    async def list_session_events(self, session_id: str) -> list[SessionEvent]: ...
