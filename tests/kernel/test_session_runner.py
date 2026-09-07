import asyncio

from lingualoop.core import (
    FeedbackItem,
    LanguageEnum,
    LearningMaterial,
    Message,
    PracticeInstruction,
    ProficiencyLevel,
    ReviewItem,
    SessionEventType,
    SessionUserProfile,
)
from lingualoop.kernel import DirectLearningSessionRunner, InMemoryEventStore


class FakeLearningLLMProvider:
    async def generate_task(
        self,
        *,
        material: LearningMaterial,
        learner_level: ProficiencyLevel,
        target_language: LanguageEnum,
    ) -> str:
        return f"Retell '{material.title}' in {target_language.value} at {learner_level.value}."

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
        return [
            ReviewItem(
                prompt="Yesterday I ___ to the market.",
                answer="went",
                source_feedback_id=corrections[0].id,
            )
        ]


def test_direct_runner_starts_session_with_plan_and_events() -> None:
    async def run_case() -> None:
        material = _material()
        store = InMemoryEventStore()
        runner = DirectLearningSessionRunner(FakeLearningLLMProvider(), store)

        result = await runner.start_session(
            material=material,
            profile=_profile(),
        )

        assert result.session.material_id == material.id
        assert result.session.current_instruction is not None
        assert result.session.current_instruction.prompt.startswith("Retell")
        assert result.assistant_message == result.session.messages[0]
        assert [event.event_type for event in result.events] == [
            SessionEventType.SESSION_STARTED,
            SessionEventType.ASSISTANT_MESSAGE_ADDED,
        ]
        assert await store.list_session_events(result.session.id) == result.events

    asyncio.run(run_case())


def test_direct_runner_handles_user_message_with_feedback_and_review_items() -> None:
    async def run_case() -> None:
        material = _material()
        store = InMemoryEventStore()
        runner = DirectLearningSessionRunner(FakeLearningLLMProvider(), store)
        started = await runner.start_session(
            material=material,
            profile=_profile(),
        )

        result = await runner.handle_user_message(
            session=started.session,
            material=material,
            user_content="Yesterday I go to market.",
        )

        user_message = result.session.messages[1]
        assert len(result.session.messages) == 3
        assert result.assistant_message is not None
        assert result.assistant_message.content == "Good start. Use past tense here."
        assert result.feedback_items[0].source_message_id == user_message.id
        assert result.review_items[0].source_session_id == started.session.id
        assert [event.event_type for event in result.events] == [
            SessionEventType.USER_MESSAGE_ADDED,
            SessionEventType.ASSISTANT_MESSAGE_ADDED,
            SessionEventType.FEEDBACK_CREATED,
            SessionEventType.REVIEW_ITEMS_CREATED,
        ]
        assert len(await store.list_session_events(started.session.id)) == 6

    asyncio.run(run_case())


def _material() -> LearningMaterial:
    return LearningMaterial(
        title="Market trip",
        source_language=LanguageEnum.CHINESE,
        content="Yesterday I went to the market.",
    )


def _profile() -> SessionUserProfile:
    return SessionUserProfile(
        profile_level=ProficiencyLevel.A2,
        native_language=LanguageEnum.CHINESE,
        target_language=LanguageEnum.ENGLISH,
    )
