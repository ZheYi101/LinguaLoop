from __future__ import annotations

from pydantic import BaseModel, Field

from lingualoop.core.domain import (
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
    SessionUserProfile,
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
    """Deterministic business runner before LangGraph owns orchestration."""

    def __init__(
        self, llm_provider: LearningLLMProvider, event_store: EventStore
    ) -> None:
        self._llm_provider = llm_provider
        self._event_store = event_store

    async def start_session(
        self,
        *,
        material: LearningMaterial,
        profile: SessionUserProfile,
        pattern_id: str = DEFAULT_PATTERN_ID,
    ) -> SessionStepResult:
        task_prompt = await self._llm_provider.generate_task(
            material=material,
            learner_level=profile.profile_level,
            target_language=profile.target_language,
        )

        instruction = PracticeInstruction(
            prompt=task_prompt,
            focus_points=_focus_points_from_material(material),
        )

        plan = PracticePlan(
            pattern_id=pattern_id,
            title=f"{material.title} practice",
            instructions=[instruction],
        )

        assistant_message = Message(role=MessageRole.ASSISTANT, content=task_prompt)

        session = PracticeSession(
            material_id=material.id,
            pattern_id=pattern_id,
            plan=plan,
            profile=profile,
            messages=[assistant_message],
        )

        events = [
            SessionEvent(
                session_id=session.id,
                event_type=SessionEventType.SESSION_STARTED,
                payload={
                    "material_id": material.id,
                    "pattern_id": pattern_id,
                    "learner_level": str(profile.profile_level),
                    "plan_id": plan.id,
                },
            ),
            _message_event(session.id, assistant_message),
        ]
        await self._event_store.append_many(events)
        return SessionStepResult(
            session=session, events=events, assistant_message=assistant_message
        )

    async def handle_user_message(
        self, *, session: PracticeSession, material: LearningMaterial, user_content: str
    ) -> SessionStepResult:
        instruction = session.current_instruction
        if instruction is None:
            raise ValueError("Practice session must have an active instruction")

        user_message = Message(role=MessageRole.USER, content=user_content)
        corrections = await self._llm_provider.correct_answer(
            current_instruction=instruction,
            user_message=user_message,
            target_language=session.profile.target_language,
        )

        corrections = [
            (
                item
                if item.source_message_id is not None
                else item.model_copy(update={"source_message_id": user_message.id})
            )
            for item in corrections
        ]

        assistant_text = await self._llm_provider.generate_reply(
            current_instruction=instruction,
            material=material,
            message_history=[*session.messages, user_message],
            user_message=user_message,
            corrections=corrections,
            target_language=session.profile.target_language,
        )

        review_items = await self._llm_provider.create_review_items(
            corrections=corrections, material=material
        )
        review_items = [
            (
                item
                if item.source_session_id is not None
                else item.model_copy(update={"source_session_id": session.id})
            )
            for item in review_items
        ]
        assistant_message = Message(role=MessageRole.ASSISTANT, content=assistant_text)

        updated_session = session.model_copy(
            update={
                "messages": [*session.messages, user_message, assistant_message],
                "feedback_items": [*session.feedback_items, *corrections],
                "review_items": [*session.review_items, *review_items],
                "updated_at": utc_now(),
            }
        )

        events = [
            _message_event(updated_session.id, user_message),
            _message_event(updated_session.id, assistant_message),
        ]

        if corrections:
            events.append(
                SessionEvent(
                    session_id=updated_session.id,
                    event_type=SessionEventType.FEEDBACK_CREATED,
                    payload={
                        "feedback_ids": [item.id for item in corrections],
                    },
                )
            )

        if review_items:
            events.append(
                SessionEvent(
                    session_id=updated_session.id,
                    event_type=SessionEventType.REVIEW_ITEMS_CREATED,
                    payload={
                        "review_item_ids": [item.id for item in review_items],
                    },
                )
            )

        await self._event_store.append_many(events)

        return SessionStepResult(
            session=updated_session,
            events=events,
            assistant_message=assistant_message,
            feedback_items=corrections,
            review_items=review_items,
        )

    async def handler_user_message(
        self, *, session: PracticeSession, material: LearningMaterial, user_content: str
    ) -> SessionStepResult:
        return await self.handle_user_message(
            session=session, material=material, user_content=user_content
        )


def _focus_points_from_material(material: LearningMaterial) -> list[str]:
    if material.analysis is None:
        return []

    return [
        *material.analysis.keywords,
        *[expr.text for expr in material.analysis.expressions],
    ]


def _message_event(session_id: str, message: Message) -> SessionEvent:
    event_type = (
        SessionEventType.USER_MESSAGE_ADDED
        if message.role == MessageRole.USER
        else SessionEventType.ASSISTANT_MESSAGE_ADDED
    )

    return SessionEvent(
        session_id=session_id,
        event_type=event_type,
        payload={
            "message_id": message.id,
            "role": message.role.value,
            "content": message.content,
        },
    )
