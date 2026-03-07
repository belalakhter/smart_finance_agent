from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentState:
    chat_id: str
    messages: list[dict]          
    last_user_message: str = ""
    rag_context: Optional[str] = None     
    web_results: Optional[str] = None     
    final_reply: Optional[str] = None     
    error: Optional[str] = None