from __future__ import annotations
import asyncio
from dis import Instruction
from email import message

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
    async def start_session(
        self,
        *,
        material: LearningMaterial,
        profile_level: ProficiencyLevel,
        pattern_id: str = DEFAULT_PATTERN_ID,
    ) -> SessionStepResult:
        task = self._llm_provider.generate_task(
            material=material,
            learner_level=profile_level,
            target_language=material.target_language,
        )

        instruction = PracticeInstruction(
            prompt=task,
            focus_points=_focus_points_from_material(material),
        )

        plan = PracticePlan(
            pattern_id=pattern_id,
            title=f"{material.title} practice",
            instructions=[instruction],
        )

        assistant_message = Message(role=MessageRole.ASSISTANT, content=task)

        session = PracticeSession(
            material_id=material.id,
            pattern_id=pattern_id,
            learner_level=profile_level,
            plan=plan,
            messages=[assistant_message],
        )

        events = [
            SessionEvent(
                session_id=session.id,
                event_type=SessionEventType.SESSION_STARTED,
                payload={
                    "material_id": material.id,
                    "pattern_id": pattern_id,
                    "learner_level": str(profile_level),
                    "plan_id": plan.id,
                },
            ),
            _message_event(session.id, assistant_message),
        ]
        await self._event_store.append_many(events)
        return SessionStepResult(
            session=session, events=events, assistant_message=assistant_message
        )

    async def handler_user_message(
        self, *, session: PracticeSession, material: LearningMaterial, user_content: str
    ) -> SessionStepResult:
        instruction = session.current_instruction
        if instruction is None:
            raise ValueError("Practice session must have an active instruction")

        user_message = Message(role=MessageRole.USER, content=user_content)
        corrections = await self._llm_provider.correct_answer(
            current_instruction=instruction,
            user_message=user_message,
            target_language=material.target_language,
        )

        corrections = [
            (
                item
                if item.source_message_id is not None
                else item.model_copy(update={"source_message_id": user_message.id})
            )
            for item in corrections
        ]

        review_items_task = asyncio.create_task(
            self._llm_provider.create_review_items(
                corrections=corrections, material=material
            )
        )

        assistant_text_task = asyncio.create_task(
            self._llm_provider.generate_reply(
                current_instruction=instruction,
                material=material,
                message_history=[*session.messages, user_message],
                user_message=user_message,
                corrections=corrections,
                target_language=material.target_language,
            )
        )

        review_items, assistant_text = await asyncio.gather(
            review_items_task, assistant_text_task
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
