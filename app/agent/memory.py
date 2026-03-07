
MAX_HISTORY_PAIRS = 10  


def trim_messages(messages: list[dict], max_pairs: int = MAX_HISTORY_PAIRS) -> list[dict]:
    """
    Return at most `max_pairs` user+assistant pairs from the tail of the
    conversation, always preserving the very first system message if present.
    """
    system_msgs = [m for m in messages if m.get("role") == "system"]
    convo_msgs  = [m for m in messages if m.get("role") != "system"]
    
    trimmed = convo_msgs[-(max_pairs * 2):]

    return system_msgs + trimmed


def last_user_message(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""