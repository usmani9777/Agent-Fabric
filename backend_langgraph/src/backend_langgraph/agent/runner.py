from functools import lru_cache
from typing import Any

from backend_langgraph.agent.graph import build_graph


@lru_cache(maxsize=1)
def get_compiled_graph() -> Any:
    return build_graph()


async def run_agent(
    user_id: str,
    user_prompt_template: str,
    user_input: str,
    session_token: str,
    refine_prompt: bool,
) -> dict[str, Any]:
    graph = get_compiled_graph()
    result = await graph.ainvoke(
        {
            "user_id": user_id,
            "session_token": session_token,
            "user_prompt_template": user_prompt_template,
            "input": user_input,
            "refine_prompt": refine_prompt,
            "selected_intent": "general",
            "tool_context": [],
            "refined_input": user_input,
            "memory_written": False,
            "output": "",
        }
    )
    return {
        "refined_input": str(result.get("refined_input", user_input)),
        "selected_intent": str(result.get("selected_intent", "general")),
        "tool_context": [str(item) for item in result.get("tool_context", [])],
        "memory_written": bool(result.get("memory_written", False)),
        "output": str(result.get("output", "")),
    }
