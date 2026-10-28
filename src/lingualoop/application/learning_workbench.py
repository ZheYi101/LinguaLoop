from __future__ import annotations

import json
import re
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from lingualoop.core.domain import (
    LanguageEnum,
    LearningMaterial,
    MaterialTrack,
    MaterialSourceType,
    NormalizationStatus,
    PracticeSession,
    ProficiencyLevel,
    ReviewItem,
    ReviewOutcome,
    ReviewRating,
    ReviewStatus,
    SessionUserProfile,
    SessionStatus,
    DiscussionTopic,
    PracticeOptions,
    SubtitleCue,
)
from lingualoop.core.ports import EventStore, LearningLLMProvider
from lingualoop.kernel import (
    DirectLearningSessionRunner,
    SessionStepResult,
)
from lingualoop.infrastructure import SQLiteStore
from lingualoop.infrastructure.material_import import ImportedMaterial
from lingualoop.application.material_preparation import prepare_material, MAX_TOPICS, preparation_cache_key
from lingualoop.core.preparation_validation import validate_dialogue_preparation, validate_prepared_topic


class LearningWorkbench:
    """Thin application service for one text-learning session."""

    def __init__(
        self,
        provider: LearningLLMProvider,
        *,
        event_store: EventStore | None = None,
    ) -> None:
        self._provider = provider
        self._event_store = event_store or SQLiteStore()
        self._runner = DirectLearningSessionRunner(provider, self._event_store)
        self._material: LearningMaterial | None = None
        self._profile: SessionUserProfile | None = None
        self._session: PracticeSession | None = None
        self._materials: list[LearningMaterial] = []
        self._review_items: list[ReviewItem] = []
        self._preparation_task: asyncio.Task | None = None
        self._preparation_tasks: set[asyncio.Task] = set()
        self._preparation_lock = asyncio.Lock()
        self._preparation_status = "idle"
        self._preparation_calls = 0
        self._generation = 0
        self._sending = False
        self.is_analyzing = False
        self._hydrate()

    @property
    def material(self) -> LearningMaterial | None:
        return self._material

    @property
    def profile(self) -> SessionUserProfile | None:
        return self._profile

    @property
    def session(self) -> PracticeSession | None:
        return self._session

    @property
    def preparation_status(self) -> str:
        return self._preparation_status

    @property
    def preparation_diagnostics(self) -> list[dict[str, Any]]:
        return list(getattr(self._provider, "preparation_diagnostics", []))

    @property
    def materials(self) -> list[LearningMaterial]:
        return list(self._materials)

    @property
    def review_queue(self) -> list[ReviewItem]:
        if isinstance(self._event_store, SQLiteStore):
            return self._event_store.list_review_items()
        return list(self._review_items)

    @property
    def due_review_items(self) -> list[ReviewItem]:
        if isinstance(self._event_store, SQLiteStore):
            return self._event_store.list_review_items(due_only=True)
        now = datetime.now(timezone.utc)
        return [
            item for item in self._review_items
            if item.status is ReviewStatus.ACTIVE and (item.due_at is None or item.due_at <= now)
        ]

    @property
    def due_review_count(self) -> int:
        return len(self.due_review_items)

    async def load_material(
        self,
        *,
        title: str,
        source_language: LanguageEnum,
        target_language: LanguageEnum,
        native_language: LanguageEnum,
        learner_level: ProficiencyLevel,
        content: str,
        source_type: MaterialSourceType = MaterialSourceType.TEXT,
        raw_content: str | None = None,
        normalized_content: str | None = None,
        source_path: str | None = None,
        track: MaterialTrack = MaterialTrack.ARTICLE_READING,
        subtitle_cues: list[SubtitleCue] | None = None,
    ) -> LearningMaterial:
        draft = LearningMaterial(
            title=title,
            source_language=source_language,
            content=normalized_content or content,
            source_type=source_type,
            raw_content=raw_content or content,
            normalized_content=normalized_content or content,
            source_path=source_path,
            track=track,
            normalization_status=NormalizationStatus.NORMALIZED,
            subtitle_cues=subtitle_cues or [],
            profile=SessionUserProfile(profile_level=learner_level, native_language=native_language,
                                       target_language=target_language),
        )
        same = next((item for item in self._materials if item.title == draft.title and item.content == draft.content
                     and item.profile == draft.profile and item.source_language == draft.source_language), None)
        if same:
            if getattr(self._provider, 'offline_read_only', False):
                return self.select_material(same.id)
            draft = draft.model_copy(update={'id': same.id, 'created_at': same.created_at,
                'analysis': same.analysis, 'analysis_cache_key': same.analysis_cache_key})
        source_hash, cache_key = preparation_cache_key(self._provider, draft, draft.profile)
        cached = self._event_store.get_preparation_cache(cache_key) if isinstance(self._event_store, SQLiteStore) else None
        # The material may also contain custom topics added after canonical preparation.
        if same and same.analysis_cache_key == cache_key and same.analysis and same.analysis.preparation_complete:
            cached = same.analysis
        if cached:
            draft = draft.model_copy(update={'analysis': cached, 'analysis_cache_key': cache_key})
        self._material = draft
        self._cancel_preparation()
        self._profile = draft.profile
        self._session = None
        self._upsert_material(draft)
        if cached:
            self.select_material(draft.id)
            return self._material
        return await self.analyze_current_material()

    async def analyze_current_material(self, *, profile: SessionUserProfile | None = None) -> LearningMaterial:
        if getattr(self._provider, 'offline_read_only', False):
            raise RuntimeError('AI 服务尚未配置，本地整理资料会保留。请配置 .env 后重启再继续整理。')
        if profile is not None and self._material is not None:
            old_profile = self._material.profile
            self._profile = profile
            self._material = self._material.model_copy(update={"profile": profile,
                "analysis": self._material.analysis if old_profile == profile else None})
            self._upsert_material(self._material)
        if self._material is None or self._profile is None:
            raise RuntimeError("请先选择材料并设置语言。")
        source_hash, cache_key = preparation_cache_key(self._provider, self._material, self._profile)
        if self._material.analysis_cache_key != cache_key:
            cached = self._event_store.get_preparation_cache(cache_key) if isinstance(self._event_store, SQLiteStore) else None
            prior = self._material.analysis if self._material.analysis_cache_key is None else None
            self._material = self._material.model_copy(update={'analysis': cached or prior, 'analysis_cache_key': cache_key})
        self._cancel_preparation()
        async def persist_progress(analysis):
            self._material = self._material.model_copy(update={"analysis": analysis})
            self._upsert_material(self._material)
            if isinstance(self._event_store, SQLiteStore):
                self._event_store.save_preparation_cache(cache_key, source_hash, analysis)
        self.is_analyzing = True
        try:
            analysis = await prepare_material(self._provider, self._material, self._profile, persist_progress)
        finally:
            self.is_analyzing = False
        self._material = self._material.model_copy(update={"analysis": analysis})
        self._upsert_material(self._material)
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.save_preparation_cache(cache_key, source_hash, analysis)
        return self._material

    async def load_imported_material(
        self,
        imported: ImportedMaterial,
        *,
        title: str | None = None,
        source_language: LanguageEnum,
        target_language: LanguageEnum,
        native_language: LanguageEnum,
        learner_level: ProficiencyLevel,
        track: MaterialTrack = MaterialTrack.ARTICLE_READING,
    ) -> LearningMaterial:
        return await self.load_material(
            title=title or imported.title,
            source_language=source_language,
            target_language=target_language,
            native_language=native_language,
            learner_level=learner_level,
            content=imported.normalized_content,
            source_type=imported.source_type,
            raw_content=imported.raw_content,
            normalized_content=imported.normalized_content,
            source_path=imported.source_path,
            track=track,
            subtitle_cues=imported.subtitle_cues,
        )

    def select_material(self, material_id: str) -> LearningMaterial:
        material = next((item for item in self._materials if item.id == material_id), None)
        if material is None:
            raise ValueError(f"Material not found: {material_id}")
        self._cancel_preparation()
        self._material = material
        sessions = self._stored_sessions_for(material.id)
        self._session = _runtime_session(sessions[0]) if sessions else None
        if self._session is not None:
            self._profile = self._session.profile
        else:
            self._profile = material.profile
        return material

    @property
    def sessions(self) -> list[PracticeSession]:
        if isinstance(self._event_store, SQLiteStore):
            return self._event_store.list_sessions(material_id=self._material.id if self._material else None)
        return [self._session] if self._session else []

    def select_session(self, session_id: str) -> PracticeSession:
        if not isinstance(self._event_store, SQLiteStore):
            raise ValueError('本地历史记录不可用。')
        session = self._event_store.get_session(session_id)
        if session is None:
            raise ValueError('找不到这次对话，请刷新历史列表。')
        material = self._event_store.get_material(session.material_id)
        if material is None:
            raise ValueError('这次对话对应的材料已不存在。')
        self._cancel_preparation()
        self._session = _runtime_session(session)
        self._material = material
        self._profile = session.profile
        return self._session

    async def start_session(self, *, topic_id: str | None = None,
                            custom_topic: str | None = None,
                            options: PracticeOptions | None = None,
                            profile: SessionUserProfile | None = None) -> SessionStepResult:
        if self._material is None:
            raise RuntimeError("Load a material before starting a session.")
        if self._material.analysis is None or not self._material.analysis.preparation_complete:
            raise RuntimeError("材料仍有未整理的章节，请先完成材料分析。")
        selected_profile = profile or self._profile
        if selected_profile is None:
            raise RuntimeError("Set a profile before starting a session.")

        if self._session is not None and self._session.status is SessionStatus.ACTIVE:
            raise RuntimeError("请先结束当前对话，再开始新的话题。")
        topics = self._material.analysis.topics if self._material.analysis else []
        topic = None
        if custom_topic and custom_topic.strip():
            if len(custom_topic.strip()) > 500:
                raise ValueError("自定义话题最多 500 字符，请简要描述想聊什么。")
            topic = await self._provider.prepare_custom_topic(material=self._material, title=custom_topic.strip(),
                target_language=selected_profile.target_language, native_language=selected_profile.native_language)
            topic = validate_prepared_topic(topic, self._material.content)
            if self._material.analysis:
                analysis = self._material.analysis.model_copy(update={"topics": [*topics, topic]})
                self._material = self._material.model_copy(update={"analysis": analysis})
                self._upsert_material(self._material)
        elif topic_id:
            topic = next((item for item in topics if item.id == topic_id), None)
            if topic is None:
                raise ValueError("所选话题已失效，请重新选择。")
        elif topics:
            topic = topics[0]
        if topic is None:
            raise ValueError("请先分析材料或输入一个自定义话题。")
        selected_options = options or PracticeOptions()
        # Custom topics and a changed target language need a fresh opening;
        # the topic title itself may be in the learner's native language.
        if selected_options.mode.value == "discussion" and (
            not custom_topic and self._material.profile and
            self._material.profile.target_language is not selected_profile.target_language
        ):
            opening = await self._provider.generate_task(
                material=self._material, learner_level=selected_profile.profile_level,
                target_language=selected_profile.target_language, topic=topic, options=selected_options,
            )
            topic = topic.model_copy(update={"opening_question": opening})
        result = await self._runner.start_session(
            material=self._material,
            profile=selected_profile,
            topic=topic,
            options=selected_options,
        )
        self._session = result.session
        self._profile = result.session.profile
        self._save_session(self._session)
        self._preparation_calls = 0
        self._schedule_preparation()
        return result

    async def send_message(self, user_content: str, *, on_delta: Callable[[str], None] | None = None) -> SessionStepResult:
        if len(user_content) > 4000:
            raise ValueError("单条发言最多 4000 字符，请拆成几次发言。")
        if self._material is None:
            raise RuntimeError("Load a material before sending a message.")
        if self._session is None:
            raise RuntimeError("Start a session before sending a message.")
        if self._session.status is not SessionStatus.ACTIVE:
            raise RuntimeError("Start a new session before sending more messages.")
        if self._sending:
            raise RuntimeError("上一条消息仍在生成，请稍候。")
        self._sending = True
        self._cancel_preparation()
        try:
            result = await self._runner.handle_user_message(
                session=self._session, material=self._material,
                user_content=user_content, on_delta=on_delta,
            )
            self._session = result.session
            self._save_session(self._session)
        finally:
            self._sending = False
        self._schedule_preparation()
        return result

    def review_items(self) -> list[ReviewItem]:
        return self.review_queue

    async def complete_session(self) -> SessionStepResult:
        if self._material is None or self._session is None:
            raise RuntimeError("Start a session before completing it.")
        self._cancel_preparation()
        result = await self._runner.complete_session(
            session=self._session,
            material=self._material,
        )
        self._session = result.session
        self._review_items = [
            item for item in self._review_items
            if item.source_session_id != self._session.id
        ]
        self._review_items.extend(result.review_items)
        self._save_session(self._session)
        return result

    async def record_review_outcome(
        self, review_item_id: str, rating: ReviewRating, answer: str | None = None
    ) -> ReviewOutcome:
        item = next((candidate for candidate in self.review_queue if candidate.id == review_item_id), None)
        if item is None:
            raise ValueError(f"Review item not found: {review_item_id}")
        if rating in {ReviewRating.GOOD, ReviewRating.EASY} and not _review_answer_matches(
            submitted=answer,
            expected=item.answer,
        ):
            raise ValueError(
                "Review answer does not match the expected answer closely enough for good/easy. "
                "Use again or hard to record an incorrect attempt."
            )
        now = datetime.now(timezone.utc)
        intervals = {
            ReviewRating.AGAIN: timedelta(minutes=10),
            ReviewRating.HARD: timedelta(days=1),
            ReviewRating.GOOD: timedelta(days=3),
            ReviewRating.EASY: timedelta(days=7),
        }
        next_due = now + intervals[rating]
        status = ReviewStatus.MASTERED if rating is ReviewRating.EASY else ReviewStatus.ACTIVE
        updated = item.model_copy(update={"due_at": next_due, "status": status})
        outcome = ReviewOutcome(
            review_item_id=item.id,
            rating=rating,
            answer=answer,
            next_due_at=next_due,
        )
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.save_review_item(updated)
        else:
            self._review_items = [
                updated if candidate.id == updated.id else candidate
                for candidate in self._review_items
            ]
        await self._event_store.append(
            self._review_event(outcome, item.source_session_id or "review")
        )
        return outcome

    async def update_review_status(self, review_item_id: str, status: ReviewStatus) -> None:
        item = next((candidate for candidate in self.review_queue if candidate.id == review_item_id), None)
        if item is None:
            raise ValueError(f"Review item not found: {review_item_id}")
        updated = item.model_copy(update={"status": status})
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.save_review_item(updated)
        else:
            self._review_items = [
                updated if candidate.id == updated.id else candidate
                for candidate in self._review_items
            ]
        event_type = {
            ReviewStatus.PAUSED: "review.paused",
            ReviewStatus.IGNORED: "review.ignored",
            ReviewStatus.ARCHIVED: "review.archived",
            ReviewStatus.DELETED: "review.deleted",
        }.get(status)
        if event_type:
            from lingualoop.core.domain import SessionEvent, SessionEventType
            await self._event_store.append(
                SessionEvent(
                    session_id=item.source_session_id or "review",
                    event_type=SessionEventType(event_type),
                    payload={"review_item_id": item.id},
                )
            )

    async def export_json(self, path: Path) -> Path:
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        session_id = self._session.id if self._session is not None else None
        events = (
            await self._event_store.list_session_events(session_id)
            if session_id is not None
            else []
        )

        payload: dict[str, Any] = {
            "material": self._material.model_dump(mode="json") if self._material else None,
            "profile": self._profile.model_dump(mode="json") if self._profile else None,
            "session": self._session.model_dump(mode="json") if self._session else None,
            "events": [event.model_dump(mode="json") for event in events],
            "review_queue": [item.model_dump(mode="json") for item in self.review_queue],
        }

        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def reset(self) -> None:
        self._cancel_preparation()
        self._material = None
        self._profile = None
        self._session = None
        self._review_items = self.review_queue

    def overview_lines(self) -> list[str]:
        lines: list[str] = []
        if self._material is None:
            return ["No material loaded."]

        lines.append(f"Material: {self._material.title}")
        lines.append(f"Source language: {self._material.source_language.value}")
        if self._profile is not None:
            lines.append(f"Target language: {self._profile.target_language.value}")
            lines.append(f"Learner level: {self._profile.profile_level.value}")
        if self._material.analysis is not None:
            lines.append(f"Summary: {self._material.analysis.summary}")
            if self._material.analysis.keywords:
                lines.append("Keywords: " + ", ".join(self._material.analysis.keywords))
            if self._material.analysis.suggested_goals:
                lines.append(
                    "Goals: " + "; ".join(self._material.analysis.suggested_goals)
                )
        return lines

    def session_lines(self) -> list[str]:
        if self._session is None:
            return ["No active session."]

        lines = [
            f"Session: {self._session.id}",
            f"Status: {self._session.status.value}",
            f"Messages: {len(self._session.messages)}",
            f"Feedback items: {len(self._session.feedback_items)}",
            f"Review items: {len(self._session.review_items)}",
        ]
        if self._session.completed_at is not None:
            lines.append(f"Completed at: {self._session.completed_at.isoformat()}")
        if self._session.status is SessionStatus.COMPLETED and self._session.review is not None:
            review = self._session.review
            lines.append(f"Review summary: {review.summary}")
            if review.focus_areas:
                lines.append("Focus: " + "; ".join(review.focus_areas[:3]))
            if review.next_action:
                lines.append(f"Next action: {review.next_action}")
        elif self._session.current_instruction is not None:
            lines.append("Current task:")
            lines.append(self._session.current_instruction.prompt)
        if self._session.status is SessionStatus.COMPLETED and self._session.current_instruction is not None:
            lines.append("Historical task:")
            lines.append(self._session.current_instruction.prompt)
        if self._session.messages:
            last_message = self._session.messages[-1]
            lines.append(f"Last message [{last_message.role.value}]: {last_message.content}")
        return lines

    def review_lines(self, *, due_only: bool = True) -> list[str]:
        all_items = self.review_queue
        items = self.due_review_items if due_only else all_items
        if not items:
            if due_only and all_items:
                return [
                    f"今日到期复习项（0 项；全部复习项 {len(all_items)} 项，可用 review --all 查看）。"
                ]
            return ["今日到期复习项（0 项）。" if due_only else "全部复习项（0 项）。"]

        if due_only:
            lines = [
                f"今日到期复习项（{len(items)} 项；全部复习项 {len(all_items)} 项，可用 review --all 查看）："
            ]
        else:
            lines = [f"全部复习项（{len(items)} 项；今日到期 {self.due_review_count} 项）："]
        for index, item in enumerate(items, start=1):
            due = item.due_at.isoformat() if item.due_at is not None else "now"
            lines.append(f"{index}. {item.prompt} (due: {due})")
        return lines

    def _hydrate(self) -> None:
        if not isinstance(self._event_store, SQLiteStore):
            return
        self._materials = self._event_store.list_materials()
        self._review_items = self._event_store.list_review_items()
        sessions = self._event_store.list_sessions()
        if sessions:
            latest = sessions[0]
            self._session = _runtime_session(latest)
            self._material = self._event_store.get_material(latest.material_id)
            self._profile = latest.profile
        elif self._materials:
            self._material = self._materials[0]
            self._profile = self._material.profile

    async def aclose(self) -> None:
        self._cancel_preparation()
        if self._preparation_tasks:
            await asyncio.gather(*self._preparation_tasks, return_exceptions=True)
        close = getattr(self._provider, "aclose", None)
        if close:
            await close()
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.close()

    def _cancel_preparation(self) -> None:
        self._generation += 1
        task = self._preparation_task
        self._preparation_task = None
        self._preparation_status = "idle"
        if task and not task.done():
            task.get_loop().call_soon_threadsafe(task.cancel)

    def _schedule_preparation(self) -> None:
        session, material = self._session, self._material
        prepare = getattr(self._provider, "prepare_dialogue", None)
        if not session or not material or prepare is None or self._preparation_calls >= 12:
            return
        self._preparation_calls += 1
        generation = self._generation
        revision = len(session.messages)
        self._preparation_status = "preparing"

        async def run():
            try:
                async with self._preparation_lock:
                    if generation != self._generation:
                        return
                    prepared = await asyncio.wait_for(prepare(material=material, session=session), timeout=45)
                if (generation != self._generation or not self._session or
                    self._session.id != session.id or len(self._session.messages) != revision or
                    self._session.status is not SessionStatus.ACTIVE):
                    return
                if prepared.based_on_message_count != revision:
                    return
                prepared = validate_dialogue_preparation(prepared, material.content)
                self._session = self._session.model_copy(update={"preparation": prepared})
                self._save_session(self._session)
                self._preparation_status = "ready"
            except asyncio.CancelledError:
                pass
            except Exception:
                if generation == self._generation:
                    self._preparation_status = "unavailable"

        task = asyncio.create_task(run(), name=f"prepare-{session.id}-{revision}")
        self._preparation_task = task
        self._preparation_tasks.add(task)
        task.add_done_callback(self._preparation_tasks.discard)

    def _upsert_material(self, material: LearningMaterial) -> None:
        self._materials = [item for item in self._materials if item.id != material.id]
        self._materials.insert(0, material)
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.save_material(material)

    def _save_session(self, session: PracticeSession) -> None:
        if isinstance(self._event_store, SQLiteStore):
            self._event_store.save_session(session)

    def _stored_sessions_for(self, material_id: str) -> list[PracticeSession]:
        if isinstance(self._event_store, SQLiteStore):
            return self._event_store.list_sessions(material_id=material_id)
        return []

    @staticmethod
    def _review_event(outcome: ReviewOutcome, session_id: str):
        from lingualoop.core.domain import SessionEvent, SessionEventType
        return SessionEvent(
            session_id=session_id,
            event_type=SessionEventType.REVIEW_OUTCOME_RECORDED,
            payload=outcome.model_dump(mode="json"),
        )


def _review_answer_matches(*, submitted: str | None, expected: str) -> bool:
    submitted_text = _normalize_review_answer(submitted or "")
    expected_text = _normalize_review_answer(expected)
    if not submitted_text or not expected_text:
        return False
    return (
        submitted_text == expected_text
        or expected_text in submitted_text
        or submitted_text in expected_text
    )


def _runtime_session(session: PracticeSession) -> PracticeSession:
    """Upgrade only future behaviour of old active sessions; historical messages stay intact."""
    if session.options is None and session.status is SessionStatus.ACTIVE:
        return session.model_copy(update={"options": PracticeOptions(difficulty=session.profile.profile_level)})
    return session


def _normalize_review_answer(value: str) -> str:
    text = value.casefold().strip()
    text = re.sub(r"[^\w\s]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
