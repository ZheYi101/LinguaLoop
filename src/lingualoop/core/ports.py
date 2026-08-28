from typing import Protocol

from lingualoop.core.domain import FeedbackItem, ReviewItem


class LearningLLMProvider(Protocol):
    async def generate_task(
        self, *, material_text: str, learner_level: str, target_language: str
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
