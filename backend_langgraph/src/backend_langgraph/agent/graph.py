from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from backend_langgraph.services.groq_service import groq_chat
from backend_langgraph.services.mcp_tools_client import call_tool


class AgentState(TypedDict):
    user_id: str
    session_token: str
    user_prompt_template: str
    input: str
    refine_prompt: bool
    selected_intent: str
    tool_context: list[str]
    refined_input: str
    memory_written: bool
    output: str


async def _safe_call_tool(
    tool_name: str,
    arguments: dict[str, Any],
    session_token: str,
    fallback: Any,
) -> Any:
    try:
        return await call_tool(tool_name, arguments, session_token=session_token)
    except Exception:
        return fallback


async def _refine(state: AgentState) -> AgentState:
    if not state["refine_prompt"]:
        return {**state, "refined_input": state["input"]}

    refined = await _safe_call_tool(
        "refine_vague_prompt",
        {
            "prompt": state["input"],
            "user_custom_prompt": state["user_prompt_template"],
            "user_id": state["user_id"],
        },
        session_token=state["session_token"],
        fallback={"refined": state["input"]},
    )
    return {**state, "refined_input": str(refined.get("refined", state["input"]))}


async def _hydrate_user_context(state: AgentState) -> AgentState:
    profile = await _safe_call_tool(
        "fetch_user_context",
        {"user_id": state["user_id"]},
        session_token=state["session_token"],
        fallback={"recent_memories": [], "prompt_template": state["user_prompt_template"]},
    )
    profile_memories = profile.get("recent_memories", [])
    base_context = [str(item) for item in profile_memories][:3]
    profile_prompt = str(profile.get("prompt_template", "")).strip()
    merged_prompt = state["user_prompt_template"]
    if profile_prompt:
        merged_prompt = profile_prompt

    return {
        **state,
        "user_prompt_template": merged_prompt,
        "tool_context": [*state.get("tool_context", []), *base_context],
    }


async def _retrieve_context(state: AgentState) -> AgentState:
    classification = await _safe_call_tool(
        "classify_intent",
        {"prompt": state["refined_input"], "user_id": state["user_id"]},
        session_token=state["session_token"],
        fallback={"intent": "general"},
    )
    intent = str(classification.get("intent", "general"))

    context_lines: list[str] = [*state.get("tool_context", [])]
    if intent == "rag":
        rag_hits = await _safe_call_tool(
            "rag_query",
            {"query": state["refined_input"], "limit": 4, "user_id": state["user_id"]},
            session_token=state["session_token"],
            fallback=[],
        )
        context_lines.extend(str(item.get("text", "")) for item in rag_hits)
    elif intent == "wiki":
        wiki_hits = await _safe_call_tool(
            "wiki_search",
            {"query": state["refined_input"], "limit": 3, "user_id": state["user_id"]},
            session_token=state["session_token"],
            fallback=[],
        )
        context_lines.extend(str(item.get("summary", "")) for item in wiki_hits)
    elif intent == "memory":
        memories = await _safe_call_tool(
            "long_term_user_memory_search",
            {"query": state["refined_input"], "limit": 5, "user_id": state["user_id"]},
            session_token=state["session_token"],
            fallback=[],
        )
        context_lines.extend(str(item.get("text", "")) for item in memories)
    elif intent == "web":
        web_hits = await _safe_call_tool(
            "web_search",
            {"query": state["refined_input"], "limit": 3, "user_id": state["user_id"]},
            session_token=state["session_token"],
            fallback=[],
        )
        context_lines.extend(str(item.get("snippet", "")) for item in web_hits)

    return {**state, "selected_intent": intent, "tool_context": context_lines[:6]}


async def _respond(state: AgentState) -> AgentState:
    context = "\n".join(state.get("tool_context", []))
    system = (
        "Use the user prompt template and retrieved context to answer with factual precision.\n"
        f"User prompt template:\n{state['user_prompt_template']}"
    )
    user = (
        f"Refined user prompt:\n{state['refined_input']}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer in a concise, production-ready tone."
    )
    output = await groq_chat(system_prompt=system, user_prompt=user, temperature=0.2)
    compact = output
    if len(output.split()) > 220:
        compact = await _safe_call_tool(
            "summarize_text",
            {"text": output, "max_words": 180, "user_id": state["user_id"]},
            session_token=state["session_token"],
            fallback=output,
        )
    return {**state, "output": str(compact)}


async def _remember(state: AgentState) -> AgentState:
    memory_payload = (
        f"Prompt: {state['refined_input']}\n"
        f"Intent: {state['selected_intent']}\n"
        f"Answer: {state['output'][:1200]}"
    )
    result = await _safe_call_tool(
        "store_user_memory",
        {
            "user_id": state["user_id"],
            "text": memory_payload,
            "tags": ["agent", state["selected_intent"]],
        },
        session_token=state["session_token"],
        fallback={"status": "skipped"},
    )
    return {**state, "memory_written": str(result.get("status", "")) == "stored"}


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("refine", _refine)
    graph.add_node("hydrate_user_context", _hydrate_user_context)
    graph.add_node("retrieve_context", _retrieve_context)
    graph.add_node("respond", _respond)
    graph.add_node("remember", _remember)
    graph.set_entry_point("refine")
    graph.add_edge("refine", "hydrate_user_context")
    graph.add_edge("hydrate_user_context", "retrieve_context")
    graph.add_edge("retrieve_context", "respond")
    graph.add_edge("respond", "remember")
    graph.add_edge("remember", END)
    return graph.compile()
