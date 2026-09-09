from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
)
from lingualoop.core.ports import EventStore, LearningLLMProvider
from lingualoop.kernel import (
    DirectLearningSessionRunner,
    SessionStepResult,
)
from lingualoop.infrastructure import SQLiteStore
from lingualoop.infrastructure.material_import import ImportedMaterial


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
        )
        analysis = await self._provider.analyze_material(
            material=draft,
            target_language=target_language,
            native_language=native_language,
        )
        material = draft.model_copy(update={"analysis": analysis})
        self._material = material
        self._profile = SessionUserProfile(
            profile_level=learner_level,
            native_language=native_language,
            target_language=target_language,
        )
        self._session = None
        self._upsert_material(material)
        return material

    async def load_imported_material(
        self,
        imported: ImportedMaterial,
        *,
        source_language: LanguageEnum,
        target_language: LanguageEnum,
        native_language: LanguageEnum,
        learner_level: ProficiencyLevel,
        track: MaterialTrack = MaterialTrack.ARTICLE_READING,
    ) -> LearningMaterial:
        return await self.load_material(
            title=imported.title,
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
        )

    def select_material(self, material_id: str) -> LearningMaterial:
        material = next((item for item in self._materials if item.id == material_id), None)
        if material is None:
            raise ValueError(f"Material not found: {material_id}")
        self._material = material
        sessions = self._stored_sessions_for(material.id)
        self._session = sessions[0] if sessions else None
        if self._session is not None:
            self._profile = self._session.profile
        return material

    async def start_session(self) -> SessionStepResult:
        if self._material is None:
            raise RuntimeError("Load a material before starting a session.")
        if self._profile is None:
            raise RuntimeError("Set a profile before starting a session.")

        result = await self._runner.start_session(
            material=self._material,
            profile=self._profile,
        )
        self._session = result.session
        self._save_session(self._session)
        return result

    async def send_message(self, user_content: str) -> SessionStepResult:
        if self._material is None:
            raise RuntimeError("Load a material before sending a message.")
        if self._session is None:
            raise RuntimeError("Start a session before sending a message.")
        if self._session.status is not SessionStatus.ACTIVE:
            raise RuntimeError("Start a new session before sending more messages.")

        result = await self._runner.handle_user_message(
            session=self._session,
            material=self._material,
            user_content=user_content,
        )
        self._session = result.session
        self._save_session(self._session)
        return result

    def review_items(self) -> list[ReviewItem]:
        return self.review_queue

    async def complete_session(self) -> SessionStepResult:
        if self._material is None or self._session is None:
            raise RuntimeError("Start a session before completing it.")
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
            f"Messages: {len(self._session.messages)}",
            f"Feedback items: {len(self._session.feedback_items)}",
            f"Review items: {len(self._session.review_items)}",
        ]
        if self._session.current_instruction is not None:
            lines.append("Current task:")
            lines.append(self._session.current_instruction.prompt)
        if self._session.messages:
            last_message = self._session.messages[-1]
            lines.append(f"Last message [{last_message.role.value}]: {last_message.content}")
        return lines

    def review_lines(self) -> list[str]:
        items = self.review_queue
        if not items:
            return ["No review items yet."]

        lines = [f"Review items ({len(items)}), due now: {self.due_review_count}:"]
        for index, item in enumerate(items, start=1):
            lines.append(f"{index}. {item.prompt}")
        return lines

    def _hydrate(self) -> None:
        if not isinstance(self._event_store, SQLiteStore):
            return
        self._materials = self._event_store.list_materials()
        self._review_items = self._event_store.list_review_items()
        sessions = self._event_store.list_sessions()
        if sessions:
            latest = sessions[0]
            self._session = latest
            self._material = self._event_store.get_material(latest.material_id)
            self._profile = latest.profile
        elif self._materials:
            self._material = self._materials[0]

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
            return [
                session for session in self._event_store.list_sessions()
                if session.material_id == material_id
            ]
        return []

    @staticmethod
    def _review_event(outcome: ReviewOutcome, session_id: str):
        from lingualoop.core.domain import SessionEvent, SessionEventType
        return SessionEvent(
            session_id=session_id,
            event_type=SessionEventType.REVIEW_OUTCOME_RECORDED,
            payload=outcome.model_dump(mode="json"),
        )
