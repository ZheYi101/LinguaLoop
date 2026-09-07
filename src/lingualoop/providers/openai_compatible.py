from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from lingualoop.core.domain import (
    FeedbackItem,
    FeedbackType,
    LanguageEnum,
    LearningMaterial,
    Message,
    PracticeInstruction,
    ProficiencyLevel,
    ReviewItem,
    ReviewItemKind,
)
from lingualoop.core.ports import LearningLLMProvider


class OpenAICompatibleLLMSettings(BaseModel):
    """OpenAI-compatible runtime settings loaded from environment."""

    api_key: SecretStr
    base_url: str
    reasoning_model: str
    dialogue_model: str | None = None
    disable_thinking: bool = False
    timeout: int = 30
    temperature: float = 0

    @classmethod
    def from_env(cls, prefix: str = "OPENAI_") -> "OpenAICompatibleLLMSettings":
        return cls(
            api_key=SecretStr(_required_env(f"{prefix}API_KEY")),
            base_url=normalize_openai_base_url(_required_env(f"{prefix}BASE_URL")),
            reasoning_model=_required_env(f"{prefix}REASONING_MODEL"),
            dialogue_model=_optional_env(f"{prefix}DIALOGUE_MODEL"),
            disable_thinking=_env_flag(f"{prefix}DISABLE_THINKING"),
        )

    def reasoning_client_kwargs(self) -> dict[str, Any]:
        return _chat_model_kwargs(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.reasoning_model,
            timeout=self.timeout,
            temperature=self.temperature,
            disable_thinking=self.disable_thinking,
        )

    def dialogue_client_kwargs(self) -> dict[str, Any]:
        model = self.dialogue_model or self.reasoning_model
        return _chat_model_kwargs(
            api_key=self.api_key,
            base_url=self.base_url,
            model=model,
            timeout=self.timeout,
            temperature=self.temperature,
            disable_thinking=self.disable_thinking,
        )


class OpenAICompatibleLLMProvider(LearningLLMProvider):
    """LearningLLMProvider implementation for OpenAI-compatible endpoints."""

    def __init__(
        self,
        settings: OpenAICompatibleLLMSettings,
        *,
        reasoning_client: BaseChatModel | None = None,
        dialogue_client: BaseChatModel | None = None,
    ) -> None:
        self._settings = settings
        self._reasoning_client: BaseChatModel = reasoning_client or ChatOpenAI(
            **settings.reasoning_client_kwargs()
        )
        self._dialogue_client: BaseChatModel = dialogue_client or ChatOpenAI(
            **settings.dialogue_client_kwargs()
        )

    @classmethod
    def from_env(cls, prefix: str = "OPENAI_") -> "OpenAICompatibleLLMProvider":
        return cls(OpenAICompatibleLLMSettings.from_env(prefix=prefix))

    async def generate_task(
        self,
        *,
        material: LearningMaterial,
        learner_level: ProficiencyLevel,
        target_language: LanguageEnum,
    ) -> str:
        messages = [
            SystemMessage(content=_reasoning_system_prompt(target_language)),
            HumanMessage(
                content=(
                    "Create one concise practice task.\n"
                    f"Target language: {target_language.value}\n"
                    f"Learner level: {learner_level.value}\n"
                    f"Material title: {material.title}\n"
                    f"Material content:\n{material.content}"
                )
            ),
        ]
        return await self._invoke_text(self._reasoning_client, messages)

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
        messages = [
            SystemMessage(content=_dialogue_system_prompt(target_language)),
            HumanMessage(
                content=(
                    "Reply to the learner in a short, natural way.\n"
                    f"Task: {current_instruction.prompt}\n"
                    f"Material: {material.content}\n"
                    f"History: {_messages_to_text(message_history)}\n"
                    f"Learner answer: {user_message.content}\n"
                    f"Corrections: {_feedback_to_text(corrections)}"
                )
            ),
        ]
        return await self._invoke_text(self._dialogue_client, messages)

    async def correct_answer(
        self,
        *,
        current_instruction: PracticeInstruction,
        user_message: Message,
        target_language: LanguageEnum,
    ) -> list[FeedbackItem]:
        # TODO: replace with stricter prompt + parser when you settle the schema.
        messages = [
            SystemMessage(
                content=(
                    "Return only a JSON array. Each item must contain "
                    "error_type, original, corrected, explanation."
                )
            ),
            HumanMessage(
                content=(
                    f"Task: {current_instruction.prompt}\n"
                    f"Learner answer: {user_message.content}\n"
                    f"Target language: {target_language.value}"
                )
            ),
        ]
        content = await self._invoke_text(self._reasoning_client, messages)
        return _parse_feedback_items(content)

    async def create_review_items(
        self,
        *,
        corrections: list[FeedbackItem],
        material: LearningMaterial,
    ) -> list[ReviewItem]:
        # TODO: add richer item generation once review-item schema stabilizes.
        if not corrections:
            return []

        messages = [
            SystemMessage(
                content=(
                    "Return only a JSON array. Each item must contain prompt, answer, "
                    "and optionally kind."
                )
            ),
            HumanMessage(
                content=(
                    f"Material title: {material.title}\n"
                    f"Material content: {material.content}\n"
                    f"Corrections: {_feedback_to_text(corrections)}"
                )
            ),
        ]
        content = await self._invoke_text(self._reasoning_client, messages)
        return _parse_review_items(content)

    async def _invoke_text(
        self, client: BaseChatModel, messages: list[BaseMessage]
    ) -> str:
        response = await client.ainvoke(messages)
        content = response.content
        if isinstance(content, str):
            return content.strip()
        return str(content).strip()


def normalize_openai_base_url(raw_base_url: str) -> str:
    base_url = raw_base_url.strip().rstrip("/")
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"OPENAI_BASE_URL is not a valid URL: {raw_base_url!r}")
    if parsed.path in ("", "/"):
        return f"{base_url}/v1"
    return base_url


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Set {name} before creating OpenAICompatibleLLMProvider")
    return value.strip()


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _chat_model_kwargs(
    *,
    api_key: SecretStr,
    base_url: str,
    model: str,
    timeout: int,
    temperature: float,
    disable_thinking: bool,
) -> dict[str, Any]:
    extra_body = {"thinking": {"type": "disabled"}} if disable_thinking else None
    return {
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "timeout": timeout,
        "temperature": temperature,
        "use_responses_api": False,
        "extra_body": extra_body,
    }


def _reasoning_system_prompt(target_language: LanguageEnum) -> str:
    return (
        "You are LinguaLoop's reasoning model. "
        f"Use {target_language.value} as the target language."
    )


def _dialogue_system_prompt(target_language: LanguageEnum) -> str:
    return (
        "You are LinguaLoop's dialogue model. "
        f"Respond naturally in {target_language.value}."
    )


def _messages_to_text(messages: list[Message]) -> str:
    if not messages:
        return "(none)"
    return "\n".join(f"{message.role.value}: {message.content}" for message in messages)


def _feedback_to_text(corrections: list[FeedbackItem]) -> str:
    if not corrections:
        return "(none)"
    return json.dumps(
        [
            {
                "original": item.original,
                "corrected": item.corrected,
                "explanation": item.explanation,
                "error_type": str(item.error_type),
            }
            for item in corrections
        ],
        ensure_ascii=False,
    )


def _parse_feedback_items(content: str) -> list[FeedbackItem]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON feedback content: {content[:500]}"
        ) from exc
    if not isinstance(payload, list):
        raise ValueError("feedback response must be a JSON array")

    items: list[FeedbackItem] = []
    for raw_item in payload:
        if not isinstance(raw_item, dict):
            continue
        original = str(raw_item.get("original", "")).strip()
        corrected = str(raw_item.get("corrected", "")).strip()
        explanation = str(raw_item.get("explanation", "")).strip()
        if original and corrected and explanation:
            items.append(
                FeedbackItem(
                    error_type=str(raw_item.get("error_type", FeedbackType.OTHER)),
                    original=original,
                    corrected=corrected,
                    explanation=explanation,
                )
            )
    return items


def _parse_review_items(content: str) -> list[ReviewItem]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON review content: {content[:500]}"
        ) from exc
    if not isinstance(payload, list):
        raise ValueError("review response must be a JSON array")

    items: list[ReviewItem] = []
    for raw_item in payload:
        if not isinstance(raw_item, dict):
            continue
        prompt = str(raw_item.get("prompt", "")).strip()
        answer = str(raw_item.get("answer", "")).strip()
        if prompt and answer:
            items.append(
                ReviewItem(
                    kind=_review_item_kind(raw_item.get("kind")),
                    prompt=prompt,
                    answer=answer,
                )
            )
    return items


def _review_item_kind(value: Any) -> ReviewItemKind:
    if isinstance(value, str):
        try:
            return ReviewItemKind(value)
        except ValueError:
            return ReviewItemKind.CLOZE
    return ReviewItemKind.CLOZE
