from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lingualoop.core.domain import (
    LanguageEnum,
    LearningMaterial,
    MaterialSourceType,
    PracticeSession,
    ProficiencyLevel,
    ReviewItem,
    SessionUserProfile,
)
from lingualoop.core.ports import EventStore, LearningLLMProvider
from lingualoop.kernel import (
    DirectLearningSessionRunner,
    InMemoryEventStore,
    SessionStepResult,
)


class LearningWorkbench:
    """Thin application service for one text-learning session."""

    def __init__(
        self,
        provider: LearningLLMProvider,
        *,
        event_store: EventStore | None = None,
    ) -> None:
        self._provider = provider
        self._event_store = event_store or InMemoryEventStore()
        self._runner = DirectLearningSessionRunner(provider, self._event_store)
        self._material: LearningMaterial | None = None
        self._profile: SessionUserProfile | None = None
        self._session: PracticeSession | None = None

    @property
    def material(self) -> LearningMaterial | None:
        return self._material

    @property
    def profile(self) -> SessionUserProfile | None:
        return self._profile

    @property
    def session(self) -> PracticeSession | None:
        return self._session

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
    ) -> LearningMaterial:
        draft = LearningMaterial(
            title=title,
            source_language=source_language,
            content=content,
            source_type=source_type,
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
        return result

    async def send_message(self, user_content: str) -> SessionStepResult:
        if self._material is None:
            raise RuntimeError("Load a material before sending a message.")
        if self._session is None:
            raise RuntimeError("Start a session before sending a message.")

        result = await self._runner.handle_user_message(
            session=self._session,
            material=self._material,
            user_content=user_content,
        )
        self._session = result.session
        return result

    def review_items(self) -> list[ReviewItem]:
        if self._session is None:
            return []
        return list(self._session.review_items)

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
        }

        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def reset(self) -> None:
        self._event_store = InMemoryEventStore()
        self._runner = DirectLearningSessionRunner(self._provider, self._event_store)
        self._material = None
        self._profile = None
        self._session = None

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
        if self._session is None:
            return ["No active session."]
        if not self._session.review_items:
            return ["No review items yet."]

        lines = [f"Review items ({len(self._session.review_items)}):"]
        for index, item in enumerate(self._session.review_items, start=1):
            lines.append(f"{index}. {item.prompt}")
        return lines
