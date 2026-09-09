from __future__ import annotations

import re
from collections import Counter

from lingualoop.core.domain import (
    FeedbackItem,
    FeedbackType,
    LanguageEnum,
    LearningMaterial,
    MaterialAnalysis,
    MaterialExpression,
    Message,
    PracticeInstruction,
    ProficiencyLevel,
    ReviewItem,
    ReviewItemKind,
    SessionReview,
)
from lingualoop.core.ports import LearningLLMProvider


class MockLearningLLMProvider(LearningLLMProvider):
    """Deterministic provider for CLI demos and offline tests."""

    async def analyze_material(
        self,
        *,
        material: LearningMaterial,
        target_language: LanguageEnum,
        native_language: LanguageEnum,
    ) -> MaterialAnalysis:
        words = _tokenize(material.content)
        keywords = [word for word, _ in Counter(words).most_common(5)]
        expressions = [
            MaterialExpression(
                text=word,
                meaning=f"Useful word from the material: {word}",
                example=f"Use {word} in your own sentence.",
            )
            for word in keywords[:3]
        ]
        summary = _first_sentence(material.content) or material.title
        difficulties = []
        if any(word in words for word in {"went", "bought", "was", "were"}):
            difficulties.append("simple past tense")
        if any(word in words for word in {"the", "a", "an"}):
            difficulties.append("article usage")

        return MaterialAnalysis(
            summary=f"{summary} ({native_language.value})",
            keywords=keywords,
            expressions=expressions,
            difficulties=difficulties,
            suggested_goals=[
                f"Retell the material in {target_language.value}",
                "Reuse one or two expressions from the text",
            ],
        )

    async def generate_task(
        self,
        *,
        material: LearningMaterial,
        learner_level: ProficiencyLevel,
        target_language: LanguageEnum,
    ) -> str:
        if material.analysis and material.analysis.keywords:
            focus = ", ".join(material.analysis.keywords[:3])
            return (
                f"Retell the material in one or two sentences. "
                f"Try to include: {focus}."
            )
        return "Retell the material in one or two sentences."

    async def generate_reply(
        self,
        *,
        current_instruction: PracticeInstruction,
        material: LearningMaterial,
        message_history: list[Message],
        user_message: Message,
        corrections: list[FeedbackItem],
        target_language: LanguageEnum,
    ) -> str:
        if corrections:
            fixes = "; ".join(
                f"{item.original} -> {item.corrected}" for item in corrections[:3]
            )
            return (
                f"Good effort. Focus on these fixes: {fixes}. "
                f"Try adding one more detail from the material."
            )
        return "Good effort. Try adding one more detail from the material."

    async def correct_answer(
        self,
        *,
        current_instruction: PracticeInstruction,
        user_message: Message,
        target_language: LanguageEnum,
    ) -> list[FeedbackItem]:
        lowered = f" {user_message.content.lower()} "
        feedback: list[FeedbackItem] = []
        if " go " in lowered or lowered.strip().startswith("i go"):
            feedback.append(
                FeedbackItem(
                    error_type=FeedbackType.GRAMMAR,
                    original="go",
                    corrected="went",
                    explanation="Use the simple past tense for completed actions.",
                )
            )
        if " buy " in lowered or lowered.strip().startswith("i buy"):
            feedback.append(
                FeedbackItem(
                    error_type=FeedbackType.GRAMMAR,
                    original="buy",
                    corrected="bought",
                    explanation="Use the simple past tense for completed actions.",
                )
            )
        if not feedback:
            feedback.append(
                FeedbackItem(
                    error_type=FeedbackType.OTHER,
                    original=user_message.content,
                    corrected=user_message.content.strip().rstrip(".") + ".",
                    explanation="Mock provider fallback feedback.",
                )
            )
        return feedback

    async def create_review_items(
        self,
        *,
        corrections: list[FeedbackItem],
        material: LearningMaterial,
    ) -> list[ReviewItem]:
        if corrections:
            correction = corrections[0]
            return [
                ReviewItem(
                    kind=ReviewItemKind.CLOZE,
                    prompt=f"Rewrite this using the correction: {correction.original} -> ____",
                    answer=correction.corrected,
                )
            ]
        return [
            ReviewItem(
                kind=ReviewItemKind.CLOZE,
                prompt=f"Summarize the material: {material.title}",
                answer=material.analysis.summary if material.analysis else material.content,
            )
        ]

    async def summarize_session(
        self,
        *,
        session,
        material: LearningMaterial,
        target_language: LanguageEnum,
    ) -> SessionReview:
        review_items = await self.create_review_items(
            corrections=session.feedback_items[-3:],
            material=material,
        )
        return SessionReview(
            summary=(
                f"You completed {len([m for m in session.messages if m.role.value == 'user'])} "
                f"learner response(s) around {material.title}."
            ),
            focus_areas=[
                item.explanation for item in session.feedback_items[:3]
            ],
            feedback_items=session.feedback_items[-5:],
            review_items=review_items[:3],
            next_action="Return later and produce the review answers without looking at the answer first.",
        )


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "is",
        "was",
        "were",
        "it",
        "i",
        "you",
        "we",
        "they",
        "he",
        "she",
        "that",
        "this",
        "with",
        "for",
        "on",
        "at",
        "as",
        "be",
        "by",
    }
    return [word for word in words if len(word) > 2 and word not in stopwords]


def _first_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    match = re.split(r"(?<=[.!?])\s+", stripped, maxsplit=1)
    return match[0].strip()
