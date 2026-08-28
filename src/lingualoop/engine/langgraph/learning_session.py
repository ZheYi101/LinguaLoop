from typing import NotRequired, Required, TypedDict

from langgraph.graph import END, START, StateGraph

from lingualoop.core.domain import FeedbackItem, ReviewItem
from lingualoop.core.ports import LearningLLMProvider


class LearningState(TypedDict, total=False):
    material_text: Required[str]
    learner_level: Required[str]
    target_language: Required[str]
    user_message: Required[str]
    task: NotRequired[str]
    assistant_message: NotRequired[str]
    corrections: NotRequired[list[FeedbackItem]]
    review_items: NotRequired[list[ReviewItem]]


def build_learning_session_graph(llm_provider: LearningLLMProvider):
    async def create_task(state: LearningState) -> dict:
        task = await llm_provider.generate_task(
            material_text=state["material_text"],
            learner_level=state["learner_level"],
            target_language=state["target_language"],
        )
        return {"task": task}

    async def correct_answer(state: LearningState) -> dict:
        task = state.get("task")
        if task is None:
            raise ValueError("Learning.task is required before using correct_answer")
        corrections = await llm_provider.correct_answer(
            task=task,
            user_message=state["user_message"],
            target_language=state["target_language"],
        )
        return {"corrections": corrections}

    async def create_review_items(state: LearningState) -> dict:
        review_items = await llm_provider.create_review_items(
            corrections=state.get("corrections", []),
            material_text=state["material_text"],
        )
        return {"review_items": review_items}

    graph = StateGraph(LearningState)
    graph.add_node("create_review_items", create_review_items)
    graph.add_node("create_task", create_task)
    graph.add_node("correct_answer", correct_answer)

    graph.add_edge(START, "create_task")
    graph.add_edge("create_task", "correct_answer")
    graph.add_edge("correct_answer", "create_review_items")
    graph.add_edge("create_review_items", END)

    return graph.compile()
