import asyncio

from lingualoop.core import (
    FeedbackItem,
    LanguageEnum,
    LearningMaterial,
    Message,
    PracticeInstruction,
    ProficiencyLevel,
    ReviewItem,
)
from lingualoop.engine.langgraph import build_learning_session_graph


class FakeLearningLLMProvider:
    async def generate_task(
        self,
        *,
        material: LearningMaterial,
        learner_level: ProficiencyLevel,
        target_language: LanguageEnum,
    ) -> str:
        return "Retell the material in one sentence."

    async def correct_answer(
        self,
        *,
        current_instruction: PracticeInstruction,
        user_message: Message,
        target_language: LanguageEnum,
    ) -> list[FeedbackItem]:
        return [
            FeedbackItem(
                error_type="grammar",
                original=user_message.content,
                corrected="Yesterday I went to the market.",
                explanation="Use past tense with yesterday.",
            )
        ]

    async def generate_reply(
        self,
        *,
        current_instruction: PracticeInstruction,
        material: LearningMaterial,
        message_history: list[Message],
        user_message: Message,
        corrections: list[FeedbackItem],
        target_language: LanguageEnum,
    ) -> str:
        return "Good start. Use past tense here."

    async def create_review_items(
        self,
        *,
        corrections: list[FeedbackItem],
        material: LearningMaterial,
    ) -> list[ReviewItem]:
        return [ReviewItem(prompt="Yesterday I ___ to the market.", answer="went")]


def test_langgraph_learning_session_smoke() -> None:
    async def run_case() -> None:
        material = LearningMaterial(
            title="Market trip",
            target_language=LanguageEnum.ENGLISH,
            native_language=LanguageEnum.CHINESE,
            content="Yesterday I went to the market.",
        )
        graph = build_learning_session_graph(FakeLearningLLMProvider())

        result = await graph.ainvoke(
            {
                "material": material,
                "learner_level": ProficiencyLevel.A2,
                "target_language": LanguageEnum.ENGLISH,
                "user_message": Message(
                    role="user",
                    content="Yesterday I go to market.",
                ),
            }
        )

        assert result["current_instruction"].prompt == (
            "Retell the material in one sentence."
        )
        assert result["assistant_message"] == "Good start. Use past tense here."
        assert len(result["corrections"]) == 1
        assert len(result["review_items"]) == 1

    asyncio.run(run_case())
