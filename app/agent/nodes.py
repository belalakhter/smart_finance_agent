import asyncio
import logging

from app.agent.state import AgentState
from app.agent.memory import trim_messages, last_user_message
from app.agent.mcp_client import web_search, should_search_web
from app.llm.llm_client import chat_completion
from app.llm.prompts import (
    AGENT_SYSTEM_PROMPT,
    RAG_CONTEXT_TEMPLATE,
    WEB_SEARCH_TEMPLATE,
)

logger = logging.getLogger(__name__)


def node_prepare(state: AgentState) -> AgentState:
    """Extract the latest user message and trim history."""
    state.last_user_message = last_user_message(state.messages)
    state.messages = trim_messages(state.messages)
    return state

def node_rag(state: AgentState) -> AgentState:
    """Query LightRAG for relevant document context."""
    if not state.last_user_message:
        return state

    try:
        from app.rag.lite_rag import LiteRAGService

        rag = LiteRAGService()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        _rag_query(rag, state.last_user_message)
                    )
                    context = future.result(timeout=15)
            else:
                context = loop.run_until_complete(
                    _rag_query(rag, state.last_user_message)
                )
        except RuntimeError:
            context = asyncio.run(_rag_query(rag, state.last_user_message))

        if context and "[No relevant" not in context:
            state.rag_context = RAG_CONTEXT_TEMPLATE.format(context=context)

    except Exception as e:
        logger.warning(f"RAG node failed: {e}")

    return state


async def _rag_query(rag, question: str) -> str:
    await rag.initialize()
    result = await rag.query(question, mode="hybrid")
    await rag.finalize()
    return result or ""

def node_web_search(state: AgentState) -> AgentState:
    """Run Tavily web search if the question warrants it."""
    if not state.last_user_message:
        return state

    if not should_search_web(state.last_user_message):
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
    """Assemble context and call the LLM for a final reply."""

    system_parts = [AGENT_SYSTEM_PROMPT]

    if state.rag_context:
        system_parts.append(state.rag_context)

    if state.web_results:
        system_parts.append(state.web_results)

    system_prompt = "\n\n".join(system_parts)

    try:
        reply = chat_completion(
            messages=state.messages,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        state.final_reply = reply
    except Exception as e:
        logger.error(f"LLM node failed: {e}")
        state.final_reply = f"I encountered an error generating a response: {e}"
        state.error = str(e)

    return state