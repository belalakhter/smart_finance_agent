import os
import json
import urllib.request
import urllib.error

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_URL = "https://api.tavily.com/search"


def web_search(query: str, max_results: int = 5) -> str:
    """
    Run a Tavily web search and return a formatted string of results.
    Returns an error string (not an exception) on failure so the agent
    can still respond gracefully.
    """
    if not TAVILY_API_KEY:
        return "[Web search unavailable: TAVILY_API_KEY not set]"

    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
    }).encode()

    req = urllib.request.Request(
        TAVILY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError as e:
        return f"[Web search failed: {e}]"
    except Exception as e:
        return f"[Web search error: {e}]"

    parts = []

    if data.get("answer"):
        parts.append(f"**Summary:** {data['answer']}\n")

    for r in data.get("results", [])[:max_results]:
        title   = r.get("title", "")
        url     = r.get("url", "")
        snippet = r.get("content", "")[:300]
        parts.append(f"- **{title}** ({url})\n  {snippet}")

    return "\n".join(parts) if parts else "[No results found]"


def should_search_web(user_message: str) -> bool:
    """
    Simple heuristic: trigger web search for questions that look like
    they need current/external information.
    """
    triggers = [
        "search", "latest", "current", "today", "news", "price",
        "weather", "who is", "what is", "when did", "where is",
        "how to", "find", "look up", "tell me about",
    ]
    msg_lower = user_message.lower()
    return any(t in msg_lower for t in triggers)