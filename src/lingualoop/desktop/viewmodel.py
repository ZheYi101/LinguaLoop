"""QML-facing application state for the desktop and mobile shells."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, QThread, Signal, Slot, QUrl

from lingualoop.application import LearningWorkbench
from lingualoop.core import LanguageEnum, MaterialSourceType, ProficiencyLevel
from lingualoop.kernel import SessionStepResult


AsyncOperation = Callable[[], Coroutine[Any, Any, Any]]


class _AsyncWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, operation: AsyncOperation) -> None:
        super().__init__()
        self._operation = operation

    @Slot()
    def run(self) -> None:
        try:
            self.succeeded.emit(asyncio.run(self._operation()))
        except Exception as exc:  # noqa: BLE001 - forwarded to the UI
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class LearningViewModel(QObject):
    """Small, stable QML API over :class:`LearningWorkbench`.

    Domain models stay in Python. QML receives plain strings and dictionaries so
    the UI is not coupled to Pydantic or LangGraph implementation details.
    """

    busyChanged = Signal()
    errorOccurred = Signal(str)
    statusChanged = Signal()
    materialChanged = Signal()
    sessionChanged = Signal()
    messagesChanged = Signal()
    feedbackItemsChanged = Signal()
    reviewItemsChanged = Signal()

    def __init__(self, workbench: LearningWorkbench, provider_label: str) -> None:
        super().__init__()
        self._workbench = workbench
        self._provider_label = provider_label
        self._busy = False
        self._status = f"就绪。当前模式：{provider_label}"
        self._messages: list[dict[str, str]] = []
        self._feedback_items: list[dict[str, str]] = []
        self._review_items: list[dict[str, str]] = []
        self._threads: list[QThread] = []

    @Property(str, constant=True)
    def providerLabel(self) -> str:
        return self._provider_label

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(bool, notify=materialChanged)
    def hasMaterial(self) -> bool:
        return self._workbench.material is not None

    @Property(bool, notify=sessionChanged)
    def hasSession(self) -> bool:
        return self._workbench.session is not None

    @Property(str, notify=materialChanged)
    def materialSummary(self) -> str:
        material = self._workbench.material
        if material is None:
            return "尚未加载材料。"
        lines = [f"材料：{material.title}", f"材料语言：{material.source_language.value}"]
        if self._workbench.profile is not None:
            profile = self._workbench.profile
            lines.extend(
                [f"目标语言：{profile.target_language.value}", f"学习等级：{profile.profile_level.value}"]
            )
        if material.analysis is not None:
            lines.append(f"摘要：{material.analysis.summary}")
            if material.analysis.keywords:
                lines.append("关键词：" + "、".join(material.analysis.keywords))
            if material.analysis.difficulties:
                lines.append("难点：" + "、".join(material.analysis.difficulties))
            if material.analysis.suggested_goals:
                lines.append("目标：" + "；".join(material.analysis.suggested_goals))
        return "\n".join(lines)

    @Property(str, notify=sessionChanged)
    def currentTask(self) -> str:
        session = self._workbench.session
        if session is None or session.current_instruction is None:
            return "尚未开始练习。"
        return session.current_instruction.prompt

    @Property(str, notify=sessionChanged)
    def sessionSummary(self) -> str:
        if self._workbench.session is None:
            return "尚未开始练习。"
        return "\n".join(self._workbench.session_lines())

    @Property(list, notify=messagesChanged)
    def messages(self) -> list[dict[str, str]]:
        return self._messages

    @Property(list, notify=feedbackItemsChanged)
    def feedbackItems(self) -> list[dict[str, str]]:
        return self._feedback_items

    @Property(list, notify=reviewItemsChanged)
    def reviewItems(self) -> list[dict[str, str]]:
        return self._review_items

    @Slot(str, str, str, str, str, str)
    def loadMaterial(
        self,
        title: str,
        content: str,
        source_language: str,
        target_language: str,
        native_language: str,
        learner_level: str,
    ) -> None:
        if not title.strip() or not content.strip():
            self.errorOccurred.emit("请填写材料标题和材料内容。")
            return

        async def operation() -> Any:
            return await self._workbench.load_material(
                title=title,
                content=content,
                source_language=LanguageEnum(source_language),
                target_language=LanguageEnum(target_language),
                native_language=LanguageEnum(native_language),
                learner_level=ProficiencyLevel(learner_level),
                source_type=MaterialSourceType.TEXT,
            )

        self._run_operation("正在分析材料...", operation, self._after_material_loaded)

    @Slot()
    def startPractice(self) -> None:
        self._run_operation("正在生成练习任务...", self._workbench.start_session, self._after_session_changed)

    @Slot(str)
    def sendMessage(self, content: str) -> None:
        if not content.strip():
            self.errorOccurred.emit("请输入练习回答。")
            return

        self._run_operation(
            "正在获取 AI 回复...",
            lambda: self._workbench.send_message(content),
            self._after_session_changed,
        )

    @Slot(str)
    def exportSession(self, path_text: str) -> None:
        path = _local_path(path_text)
        if path is None:
            self.errorOccurred.emit("请选择导出文件。")
            return
        self._run_operation(
            "正在导出会话...",
            lambda: self._workbench.export_json(path),
            lambda exported: self._set_status(f"已导出到 {exported}"),
        )

    @Slot()
    def resetSession(self) -> None:
        if self._busy:
            self.errorOccurred.emit("当前还有操作正在运行。")
            return
        self._workbench.reset()
        self._messages = []
        self._feedback_items = []
        self._review_items = []
        self._set_status(f"状态已重置。当前模式：{self._provider_label}")
        self.materialChanged.emit()
        self.sessionChanged.emit()
        self.messagesChanged.emit()
        self.feedbackItemsChanged.emit()
        self.reviewItemsChanged.emit()

    def _run_operation(
        self,
        status: str,
        operation: AsyncOperation,
        on_success: Callable[[Any], None],
    ) -> None:
        if self._busy:
            self.errorOccurred.emit("当前还有操作正在运行。")
            return
        self._busy = True
        self.busyChanged.emit()
        self._set_status(status)

        thread = QThread(self)
        worker = _AsyncWorker(operation)
        worker.moveToThread(thread)
        thread.worker = worker  # type: ignore[attr-defined]
        worker.succeeded.connect(on_success)
        worker.failed.connect(self._on_operation_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.started.connect(worker.run)
        thread.finished.connect(lambda: self._operation_finished(thread))
        self._threads.append(thread)
        thread.start()

    @Slot(str)
    def _on_operation_failed(self, message: str) -> None:
        self.errorOccurred.emit(f"操作失败：{message}")
        self._set_status("操作失败，请检查网络或配置。")

    def _operation_finished(self, thread: QThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        thread.deleteLater()
        self._busy = False
        self.busyChanged.emit()
        if self._status.endswith("..."):
            self._set_status(f"就绪。当前模式：{self._provider_label}")

    def _after_material_loaded(self, _material: Any) -> None:
        self._messages = []
        self._feedback_items = []
        self._review_items = []
        self.materialChanged.emit()
        self.sessionChanged.emit()
        self.messagesChanged.emit()
        self.feedbackItemsChanged.emit()
        self.reviewItemsChanged.emit()
        self._set_status("材料分析完成，可以开始练习。")

    def _after_session_changed(self, result: SessionStepResult) -> None:
        session = result.session
        self._messages = [
            {"role": message.role.value, "content": message.content}
            for message in session.messages
        ]
        self._feedback_items = [
            {
                "original": item.original,
                "corrected": item.corrected,
                "explanation": item.explanation,
            }
            for item in session.feedback_items
        ]
        self._review_items = [
            {"prompt": item.prompt, "answer": item.answer}
            for item in session.review_items
        ]
        self.sessionChanged.emit()
        self.messagesChanged.emit()
        self.feedbackItemsChanged.emit()
        self.reviewItemsChanged.emit()
        self._set_status("练习已更新。")

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _local_path(value: str) -> Path | None:
    if not value.strip():
        return None
    url = QUrl(value)
    if url.isValid() and url.isLocalFile():
        return Path(url.toLocalFile())
    return Path(value).expanduser()
