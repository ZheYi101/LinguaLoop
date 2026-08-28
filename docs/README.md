# 文档目录

本文档目录按读者意图分类。新文档优先放入对应子目录，避免所有内容堆在 `docs/` 根目录。

## Product

- [Project Brief](./product/PROJECT_BRIEF.md): 项目愿景、目标用户、产品原则和非目标。
- [MVP Spec](./product/MVP_SPEC.md): 第一版 MVP 范围、用户故事、初始数据对象和验收标准。

## Architecture

- [Architecture](./architecture/ARCHITECTURE.md): 初始系统架构、模块边界和关键用例。
- [Agent Core Architecture](./architecture/AGENT_CORE_ARCHITECTURE.md): Python-first Agent Kernel、LangGraph adapter 和 typed LLM 调用规划。
- [Extension Architecture](./architecture/PLUGIN_ARCHITECTURE.md): Core / Plugins / Patterns 三层扩展架构。
- [Core Concepts](./architecture/CORE_CONCEPTS.md): 当前 `src/lingualoop/core` 中核心模型、Provider、EventStore 和常见 Python/Pydantic 写法说明。

## Planning

- [Roadmap](./planning/ROADMAP.md): Phase 0 到 Phase 3 的开发路线图。

## Decisions

- [Technical Decisions](./decisions/TECH_DECISIONS.md): 会影响长期维护的技术决策记录。

## Root Documents

- [Repository Guide](../AGENTS.md): coding agents 的仓库工作约定。
- [Contributing](../CONTRIBUTING.md): 开源贡献规范。


DEFAULT_PATTERN_ID = "guided_roleplay"


class SessionStepResult(BaseModel):
    session: PracticeSession
    events: list[SessionEvent] = Field(default_factory=list)
    assistant_message: Message | None = None
    feedback_items: list[FeedbackItem] = Field(default_factory=list)
    review_items: list[ReviewItem] = Field(default_factory=list)


class DirectLearningSessionRunner:
    """Deterministic business runner before LangGraph owns orchestration."""

    def __init__(self, llm_provider: LearningLLMProvider, event_store: EventStore) -> None:
        self._llm_provider = llm_provider
        self._event_store = event_store

    async def start_session(
        self,
        *,
        material: LearningMaterial,
        profile_level: ProficiencyLevel | str,
        pattern_id: str = DEFAULT_PATTERN_ID,
    ) -> SessionStepResult:
        task = await self._llm_provider.generate_task(
            material_text=material.content,
            learner_level=str(profile_level),
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
            required_capabilities=[CapabilityRequirement(name="llm.generate")],
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
            session=session,
            events=events,
            assistant_message=assistant_message,
        )

    async def handle_user_message(
        self,
        *,
        session: PracticeSession,
        material: LearningMaterial,
        content: str,
    ) -> SessionStepResult:
        instruction = session.current_instruction
        if instruction is None:
            raise ValueError("Practice session must have an active instruction")

        user_message = Message(role=MessageRole.USER, content=content)
        corrections = await self._llm_provider.correct_answer(
            task=instruction.prompt,
            user_message=content,
            target_language=material.target_language,
        )
        corrections = [
            item
            if item.source_message_id is not None
            else item.model_copy(update={"source_message_id": user_message.id})
            for item in corrections
        ]
        assistant_text = await self._llm_provider.generate_reply(
            task=instruction.prompt,
            material_text=material.content,
            message_history=[*session.messages, user_message],
            user_message=content,
            corrections=corrections,
            target_language=material.target_language,
        )
        assistant_message = Message(role=MessageRole.ASSISTANT, content=assistant_text)
        review_items = await self._llm_provider.create_review_items(
            corrections=corrections,
            material_text=material.content,
        )
        review_items = [
            item
            if item.source_session_id is not None
            else item.model_copy(update={"source_session_id": session.id})
            for item in review_items
        ]

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
                    payload={"feedback_ids": [item.id for item in corrections]},
                )
            )
        if review_items:
            events.append(
                SessionEvent(
                    session_id=updated_session.id,
                    event_type=SessionEventType.REVIEW_ITEMS_CREATED,
                    payload={"review_item_ids": [item.id for item in review_items]},
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
    return [*material.analysis.keywords, *[expr.text for expr in material.analysis.expressions]]


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
