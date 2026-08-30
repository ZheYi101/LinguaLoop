import pytest
from pydantic import ValidationError

from lingualoop.core import (
    LanguageEnum,
    LearningMaterial,
    Message,
    MessageRole,
    PracticeInstruction,
    PracticePlan,
    PracticeSession,
    ProficiencyLevel,
)


def test_learning_material_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        LearningMaterial(
            title="Market trip",
            target_language=LanguageEnum.ENGLISH,
            native_language=LanguageEnum.CHINESE,
            content="   ",
        )


def test_language_enum_fields_remain_enums() -> None:
    material = LearningMaterial(
        title="Market trip",
        target_language=LanguageEnum.ENGLISH,
        native_language=LanguageEnum.CHINESE,
        content="Yesterday I went to the market.",
    )

    assert material.target_language is LanguageEnum.ENGLISH
    assert material.native_language is LanguageEnum.CHINESE


def test_message_rejects_blank_content() -> None:
    with pytest.raises(ValidationError):
        Message(role=MessageRole.USER, content=" ")


def test_domain_models_forbid_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        LearningMaterial(
            title="Market trip",
            target_language=LanguageEnum.ENGLISH,
            native_language=LanguageEnum.CHINESE,
            content="Yesterday I went to the market.",
            unknown_field=True,
        )


def test_practice_session_current_instruction_returns_latest_instruction() -> None:
    first = PracticeInstruction(prompt="Introduce yourself.")
    second = PracticeInstruction(prompt="Retell the material.")
    session = PracticeSession(
        material_id="mat_1",
        pattern_id="guided_roleplay",
        learner_level=ProficiencyLevel.A2,
        plan=PracticePlan(
            pattern_id="guided_roleplay",
            title="Market trip practice",
            instructions=[first, second],
        ),
    )

    assert session.current_instruction == second
