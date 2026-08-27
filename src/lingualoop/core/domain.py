from enum import StrEnum
from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    User = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LearningMaterial(BaseModel):
    id: str
    title: str
    target_language: str
    naive_language: str
    content: str


class Message(BaseModel):
    role: MessageRole
    content: str


class FeedbackItem(BaseModel):
    error_type: str
    original: str
    corrected: str
    explanation: str


class ReviewItem(BaseModel):
    prompt: str
    answer: str
    source_feedback_id: str | None = None


class PracticeSession(BaseModel):
    id: str
    material_id: str
    learner_level: str
    messages: list[Message] = Field(default_factory=list)
    feedback_item: list[FeedbackItem] = Field(default_factory=list)
    review_item: list[ReviewItem] = Field(default_factory=list)
