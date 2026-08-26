import asyncio
from graphs.learning_session import build_learning_session_graph


class FakeLLMProvider:
    async def generate_task(
        self,
        *,
        material_text: str,
        learner_level: str,
        target_language: str,
    ) -> str:
        return f"请用 {target_language} 复述这段材料，难度为 {learner_level}。"

    async def correct_answer(
        self,
        *,
        task: str,
        user_message: str,
        target_language: str,
    ) -> list[dict]:
        return [
            {
                "type": "grammar",
                "original": user_message,
                "corrected": "Yesterday I went to the market.",
                "explanation": "go 应该改成 went，因为 Yesterday 是过去时间。",
            }
        ]

    async def create_review_items(
        self,
        *,
        corrections: list[dict],
        material_text: str,
    ) -> list[dict]:
        return [
            {
                "prompt": "Yesterday I ___ to the market.",
                "answer": "went",
            }
        ]


input_state = {
    "material_text": "Yesterday I went to the market.",
    "learner_level": "A2",
    "target_language": "English",
    "user_message": "Yesterday I go to market.",
}

compiled_graph = build_learning_session_graph(FakeLLMProvider())

result = asyncio.run(compiled_graph.ainvoke(input_state))

print(type(result))
print(result.keys())

for key, value in result.items():
    print("----", key)
    print(value)
