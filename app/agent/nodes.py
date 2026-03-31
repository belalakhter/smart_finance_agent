import asyncio
import logging
import json

from app.agent.state import AgentState
from app.agent.memory import trim_messages, last_user_message
from app.agent.mcp_client import web_search, should_search_web
from app.llm.llm_client import chat_completion
from app.llm.prompts import (
    AGENT_SYSTEM_PROMPT,
    RAG_CONTEXT_TEMPLATE,
    WEB_SEARCH_TEMPLATE,
    ROUTER_PROMPT,
    QUERY_REFORMULATE_PROMPT,
)

logger = logging.getLogger(__name__)


def node_prepare(state: AgentState) -> AgentState:
    """Extract information and trim history."""
    state.last_user_message = last_user_message(state.messages)
    state.messages = trim_messages(state.messages)
    return state


def node_router(state: AgentState) -> AgentState:
    """
    Decide between:
    - Strategy A: Semantic RAG + History (for follow-ups/conversational)
    - Strategy B: Pure Graph Context (for factual extraction/entity-based)
    """
    if not state.last_user_message:
        return state

    try:
        decision_raw = chat_completion(
            messages=[{"role": "user", "content": state.last_user_message}],
            system_prompt=ROUTER_PROMPT,
            temperature=0,
        )
        decision = decision_raw.strip().upper()[:1]
        state.strategy = decision if decision in ["A", "B"] else "A"
        logger.info(f"[router] Selected strategy: {state.strategy}")
        if state.strategy == "A":
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in state.messages[:-1]])
            reformulated = chat_completion(
                messages=[{"role": "user", "content": f"History:\n{history_str}\n\nQuestion: {state.last_user_message}"}],
                system_prompt=QUERY_REFORMULATE_PROMPT,
                temperature=0,
            )
            state.search_query = reformulated.strip()
        else:
            state.search_query = state.last_user_message

    except Exception as e:
        logger.warning(f"Router node failed: {e}")
        state.strategy = "A"
        state.search_query = state.last_user_message

    return state


def node_rag_semantic(state: AgentState) -> AgentState:
    """Strategy A: Semantic RAG using full history context."""
    if state.strategy != "A" or not state.search_query:
        return state

    state.rag_context = _sync_rag_query(state.search_query, mode="hybrid")
    return state


def node_rag_graph(state: AgentState) -> AgentState:
    """Strategy B: Pure Graph context without history dependence."""
    if state.strategy != "B" or not state.search_query:
        return state
    state.rag_context = _sync_rag_query(state.search_query, mode="graph")
    return state


def _sync_rag_query(query: str, mode: str) -> str:
    try:
        from app.rag.rag_processing import HybridRAGService
        rag = HybridRAGService()
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _rag_call(rag, query, mode))
                    context = future.result(timeout=15)
            else:
                context = loop.run_until_complete(_rag_call(rag, query, mode))
        except RuntimeError:
            context = asyncio.run(_rag_call(rag, query, mode))
            
        if context and "[No relevant" not in context:
            return RAG_CONTEXT_TEMPLATE.format(context=context)
    except Exception as e:
        logger.warning(f"RAG query failed: {e}")
    return ""


async def _rag_call(rag, query: str, mode: str) -> str:
    await rag.initialize()
    result = await rag.query(query, mode=mode)
    await rag.finalize()
    return result


def node_web_search(state: AgentState) -> AgentState:
    """Run Tavily web search if needed."""
    if not state.last_user_message or not should_search_web(state.last_user_message):
        return state

    try:
        results = web_search(state.last_user_message)
        if results and not results.startswith("["):
            state.web_results = WEB_SEARCH_TEMPLATE.format(
                query=state.last_user_message,
                results=results,
            )
    except Exception as e:
        logger.warning(f"Web search node failed: {e}")

    return state


def node_llm(state: AgentState) -> AgentState:
    """Final assembly and LLM response."""

    system_parts = [AGENT_SYSTEM_PROMPT]

    if state.rag_context:
        system_parts.append(state.rag_context)

    if state.web_results:
        system_parts.append(state.web_results)

    system_prompt = "\n\n".join(system_parts)

    messages = state.messages
    if state.strategy == "B":
        messages = [{"role": "user", "content": state.last_user_message}]

    try:
        reply = chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        state.final_reply = reply
    except Exception as e:
        logger.error(f"LLM node failed: {e}")
        state.final_reply = f"Error: {e}"

    return state