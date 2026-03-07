import logging
from app.agent.state import AgentState
from app.agent.nodes import node_prepare, node_rag, node_web_search, node_llm

logger = logging.getLogger(__name__)

_PIPELINE = [
    node_prepare,
    node_rag,
    node_web_search,
    node_llm,
]


def run_agent(chat_id: str, messages: list[dict]) -> str:
    """
    Entry-point called by the chat route.

    Args:
        chat_id:  UUID string of the current chat (for logging / future use).
        messages: Full conversation history as
                  [{"role": "user"|"assistant", "content": "..."}, ...]

    Returns:
        The assistant's reply as a plain string.
    """
    state = AgentState(chat_id=chat_id, messages=messages)

    for node_fn in _PIPELINE:
        try:
            state = node_fn(state)
        except Exception as e:
            logger.error(f"[graph] node {node_fn.__name__} raised: {e}", exc_info=True)
            return f"An error occurred in {node_fn.__name__}: {e}"

    return state.final_reply or "I was unable to generate a response."