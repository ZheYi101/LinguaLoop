from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from lingualoop.application import LearningWorkbench
from lingualoop.core.domain import LanguageEnum, ProficiencyLevel, ReviewRating
from lingualoop.core.ports import LearningLLMProvider
from lingualoop.infrastructure.material_import import import_material_file
from lingualoop.providers import MockLearningLLMProvider, OpenAICompatibleLLMProvider


@dataclass
class CommandOutcome:
    lines: list[str]
    should_exit: bool = False


class ConsoleSessionApp:
    def __init__(
        self,
        workbench: LearningWorkbench,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._workbench = workbench
        self._input = input_fn
        self._output = output_fn

    async def run(self) -> int:
        self._output("LinguaLoop CLI")
        self._output("Type 'help' for commands.")
        while True:
            try:
                raw = self._input("lingualoop> ").strip()
            except (EOFError, KeyboardInterrupt):
                self._output("")
                return 0
            if not raw:
                continue

            result = await self.handle_line(raw)
            for line in result.lines:
                self._output(line)
            if result.should_exit:
                return 0

    async def handle_line(self, raw: str) -> CommandOutcome:
        try:
            command, args = _split_command(raw)
            if command in {"quit", "exit"}:
                return CommandOutcome(["Bye."], should_exit=True)
            if command == "help":
                return CommandOutcome(_help_lines())
            if command == "load":
                return CommandOutcome(await self._load_material())
            if command == "import":
                return CommandOutcome(await self._import_material(args))
            if command == "start":
                return CommandOutcome(await self._start_session())
            if command == "say":
                text = args or self._input("Message: ").strip()
                return CommandOutcome(await self._say(text))
            if command == "finish":
                return CommandOutcome(await self._finish())
            if command == "review":
                return CommandOutcome(self._workbench.review_lines())
            if command == "rate":
                return CommandOutcome(await self._rate(args))
            if command == "summary":
                return CommandOutcome(
                    [*self._workbench.overview_lines(), *self._workbench.session_lines()]
                )
            if command == "export":
                path_text = args or self._input("Export path [lingualoop-session.json]: ")
                path = Path(path_text.strip() or "lingualoop-session.json")
                exported = await self._workbench.export_json(path)
                return CommandOutcome([f"Exported to {exported}"])
            if command == "reset":
                self._workbench.reset()
                return CommandOutcome(["State reset."])

            if self._workbench.session is not None:
                return CommandOutcome(await self._say(raw))

            return CommandOutcome([f"Unknown command: {command}", "Type 'help' for commands."])
        except Exception as exc:
            return CommandOutcome([f"Error: {exc}"])

    async def _load_material(self) -> list[str]:
        title = self._prompt("Title: ")
        source_language = _prompt_enum(
            self._input,
            self._output,
            "Source language (e.g. english, chinese): ",
            LanguageEnum,
        )
        target_language = _prompt_enum(
            self._input,
            self._output,
            "Target language (e.g. english, chinese): ",
            LanguageEnum,
        )
        native_language = _prompt_enum(
            self._input,
            self._output,
            "Native language (e.g. chinese, english): ",
            LanguageEnum,
        )
        learner_level = _prompt_enum(
            self._input,
            self._output,
            "Learner level (A1/A2/B1/B2/C1/C2/unknown): ",
            ProficiencyLevel,
        )
        self._output("Paste material text. Finish with a single '.' line.")
        content = _read_multiline(self._input)

        material = await self._workbench.load_material(
            title=title,
            source_language=source_language,
            target_language=target_language,
            native_language=native_language,
            learner_level=learner_level,
            content=content,
        )

        lines = [
            f"Loaded: {material.title}",
            *self._workbench.overview_lines(),
            "Type 'start' to open the practice session.",
        ]
        return lines

    async def _import_material(self, path_text: str) -> list[str]:
        path = Path(path_text.strip() or self._input("File path: ").strip())
        imported = import_material_file(path)
        source_language = _prompt_enum(
            self._input,
            self._output,
            "Source language (e.g. english, chinese): ",
            LanguageEnum,
        )
        target_language = _prompt_enum(
            self._input,
            self._output,
            "Target language (e.g. english, chinese): ",
            LanguageEnum,
        )
        native_language = _prompt_enum(
            self._input,
            self._output,
            "Native language (e.g. chinese, english): ",
            LanguageEnum,
        )
        learner_level = _prompt_enum(
            self._input,
            self._output,
            "Learner level (A1/A2/B1/B2/C1/C2/unknown): ",
            ProficiencyLevel,
        )
        material = await self._workbench.load_imported_material(
            imported,
            source_language=source_language,
            target_language=target_language,
            native_language=native_language,
            learner_level=learner_level,
        )
        return [
            f"Imported: {material.title}",
            *imported.diagnostics,
            *self._workbench.overview_lines(),
            "Type 'start' to open the practice session.",
        ]

    async def _start_session(self) -> list[str]:
        result = await self._workbench.start_session()
        lines = ["Session started."]
        if result.assistant_message is not None:
            lines.append(f"Task: {result.assistant_message.content}")
        lines.extend(self._workbench.session_lines())
        return lines

    async def _say(self, user_text: str) -> list[str]:
        result = await self._workbench.send_message(user_text)
        lines = []
        if result.assistant_message is not None:
            lines.append(f"Assistant: {result.assistant_message.content}")
        if result.feedback_items:
            lines.append(f"Feedback items: {len(result.feedback_items)}")
            for item in result.feedback_items:
                lines.append(f"- {item.original} -> {item.corrected}")
        return lines or ["No response."]

    async def _finish(self) -> list[str]:
        result = await self._workbench.complete_session()
        review = result.session.review
        lines = ["Session completed."]
        if review is not None:
            lines.append(f"Summary: {review.summary}")
            if review.focus_areas:
                lines.append("Focus: " + "; ".join(review.focus_areas[:3]))
            if review.next_action:
                lines.append(f"Next: {review.next_action}")
        if result.review_items:
            lines.append(f"Review items: {len(result.review_items)}")
            for item in result.review_items[:3]:
                lines.append(f"- {item.prompt}")
        return lines

    async def _rate(self, args: str) -> list[str]:
        parts = args.split(maxsplit=2)
        if len(parts) < 2:
            return ["Usage: rate <review_id_or_number> <again|hard|good|easy> [answer]"]
        items = self._workbench.review_queue
        key = parts[0]
        item = items[int(key) - 1] if key.isdigit() and 0 < int(key) <= len(items) else next(
            (candidate for candidate in items if candidate.id == key),
            None,
        )
        if item is None:
            return [f"Review item not found: {key}"]
        rating = ReviewRating(parts[1].lower())
        answer = parts[2] if len(parts) == 3 else None
        outcome = await self._workbench.record_review_outcome(item.id, rating, answer)
        return [f"Recorded {outcome.rating.value}; next due at {outcome.next_due_at}."]

    def _prompt(self, message: str) -> str:
        return self._input(message).strip()


def _help_lines() -> list[str]:
    return [
        "Commands:",
        "  load    Load and analyze one material",
        "  import  Import .md/.markdown/.docx material",
        "  start   Start the practice session",
        "  say     Send a learner message",
        "  finish  Complete the session and create review items",
        "  review  Show review items",
        "  rate    Record review outcome",
        "  summary Show material/session summary",
        "  export  Save session JSON",
        "  reset   Clear current state",
        "  quit    Exit the CLI",
    ]


def _split_command(raw: str) -> tuple[str, str]:
    parts = raw.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return command, args


def _prompt_enum(
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
    prompt: str,
    enum_cls: type[LanguageEnum] | type[ProficiencyLevel],
) -> LanguageEnum | ProficiencyLevel:
    while True:
        raw = input_fn(prompt).strip()
        try:
            return _parse_enum(raw, enum_cls)
        except ValueError as exc:
            output_fn(f"Invalid value: {exc}")


def _parse_enum(
    raw: str, enum_cls: type[LanguageEnum] | type[ProficiencyLevel]
) -> LanguageEnum | ProficiencyLevel:
    candidate = raw.strip().lower()
    if not candidate:
        raise ValueError("value must not be blank")
    for member in enum_cls:
        if candidate in {member.name.lower(), str(member.value).lower()}:
            return member
    raise ValueError(f"expected one of {[member.value for member in enum_cls]}")


def _read_multiline(input_fn: Callable[[str], str]) -> str:
    lines: list[str] = []
    while True:
        line = input_fn("").rstrip("\n")
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def build_provider(use_mock: bool) -> LearningLLMProvider:
    if use_mock:
        return MockLearningLLMProvider()
    return OpenAICompatibleLLMProvider.from_env()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LinguaLoop CLI")
    parser.add_argument("--mock", action="store_true", help="Use the deterministic mock provider")
    args = parser.parse_args(argv)

    try:
        provider = build_provider(args.mock)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    app = ConsoleSessionApp(LearningWorkbench(provider))
    return asyncio.run(app.run())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
