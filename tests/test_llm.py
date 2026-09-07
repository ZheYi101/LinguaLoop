import os
from typing import TypedDict
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import SecretStr

load_dotenv()

RUN_REAL_AI_TESTS = os.getenv("RUN_REAL_AI_TESTS", "").strip() == "1"


def env_or_skip(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Set {name} to run the real OpenAI-compatible smoke test.")
    return value


def normalize_openai_base_url(raw_base_url: str) -> str:
    base_url = raw_base_url.strip().rstrip("/")
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        pytest.fail(f"OPENAI_BASE_URL is not a valid URL: {raw_base_url!r}")
    if parsed.path in ("", "/"):
        return f"{base_url}/v1"
    return base_url


def build_openai_llm() -> ChatOpenAI:
    api_key = env_or_skip("OPENAI_API_KEY")
    base_url = normalize_openai_base_url(env_or_skip("OPENAI_BASE_URL"))
    model = env_or_skip("OPENAI_MODEL")

    return ChatOpenAI(
        model=model,
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=0,
        timeout=30,
        use_responses_api=False,
    )


def llm_node(state: MessagesState) -> dict:
    """Call the configured OpenAI-compatible LLM."""
    system_prompt = SystemMessage(
        content="You are a concise language learning assistant. Answer in Chinese."
    )
    response = build_openai_llm().invoke([system_prompt, *state["messages"]])

    return {"messages": [response]}


def is_model_routing_error(error: Exception) -> bool:
    message = str(error)
    return "model_not_found" in message or "No available channel for model" in message


def test_llm_graph_smoke():
    builder = StateGraph(MessagesState)

    builder.add_node("llm", llm_node)
    builder.add_edge(START, "llm")
    builder.add_edge("llm", END)
    graph = builder.compile()
    try:
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="What is LinguaLoop? Reply in Chinese.")
                ]
            }
        )
    except Exception as exc:
        if is_model_routing_error(exc):
            pytest.fail(
                "Configured MODEL is not available for the current API key "
                "group. Run `python scripts/list_openai_models.py` and set "
                "MODEL to one of the returned model ids."
            )
        raise

    assert "messages" in result
    assert str(result["messages"][-1].content).strip()
