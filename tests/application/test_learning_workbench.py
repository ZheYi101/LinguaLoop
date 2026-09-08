from __future__ import annotations

import asyncio
import json

from lingualoop.application import LearningWorkbench
from lingualoop.cli import ConsoleSessionApp
from lingualoop.core import LanguageEnum, ProficiencyLevel
from lingualoop.providers import MockLearningLLMProvider


def test_workbench_load_start_send_and_export(tmp_path) -> None:
    async def run_case() -> None:
        workbench = LearningWorkbench(MockLearningLLMProvider())

        material = await workbench.load_material(
            title="Market trip",
            source_language=LanguageEnum.ENGLISH,
            target_language=LanguageEnum.ENGLISH,
            native_language=LanguageEnum.CHINESE,
            learner_level=ProficiencyLevel.A2,
            content="Yesterday I went to the market and bought apples.",
        )

        assert material.analysis is not None
        assert material.analysis.summary
        assert workbench.profile is not None
        assert workbench.profile.target_language is LanguageEnum.ENGLISH

        started = await workbench.start_session()
        assert started.assistant_message is not None
        assert started.session.current_instruction is not None

        answered = await workbench.send_message("Yesterday I go market and buy apple.")
        assert answered.assistant_message is not None
        assert answered.feedback_items
        assert answered.review_items

        exported = await workbench.export_json(tmp_path / "session.json")
        payload = json.loads(exported.read_text(encoding="utf-8"))

        assert payload["material"]["analysis"]["summary"]
        assert payload["session"]["messages"]
        assert payload["events"]

    asyncio.run(run_case())


def test_cli_command_flow(tmp_path) -> None:
    async def run_case() -> None:
        responses = iter(
            [
                "Market trip",
                "english",
                "english",
                "chinese",
                "A2",
                "Yesterday I went to the market and bought apples.",
                ".",
                "Yesterday I go market and buy apple.",
                "I go market and buy apple.",
            ]
        )
        outputs: list[str] = []

        def fake_input(prompt: str) -> str:
            return next(responses)

        app = ConsoleSessionApp(
            LearningWorkbench(MockLearningLLMProvider()),
            input_fn=fake_input,
            output_fn=outputs.append,
        )

        load = await app.handle_line("load")
        assert any(line.startswith("Loaded:") for line in load.lines)

        start = await app.handle_line("start")
        assert any("Session started." in line for line in start.lines)

        say = await app.handle_line("say")
        assert any(line.startswith("Assistant:") for line in say.lines)
        assert any(line.startswith("Feedback items:") for line in say.lines)
        assert any(line.startswith("Review items:") for line in say.lines)

        review = await app.handle_line("review")
        assert review.lines[0].startswith("Review items")

        exported_path = tmp_path / "cli-session.json"
        export = await app.handle_line(f"export {exported_path}")
        assert any("Exported to" in line for line in export.lines)
        assert exported_path.exists()

        summary = await app.handle_line("summary")
        assert any(line.startswith("Material:") for line in summary.lines)

        reset = await app.handle_line("reset")
        assert reset.lines == ["State reset."]

        quit_result = await app.handle_line("quit")
        assert quit_result.should_exit is True

    asyncio.run(run_case())
