import os
from typing import Optional
from openai import OpenAI

_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
)

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def chat_completion(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Send a list of {"role": "user"|"assistant", "content": "..."} messages
    to OpenAI and return the assistant reply as a string.
    """
    formatted: list[dict] = []

    if system_prompt:
        formatted.append({"role": "system", "content": system_prompt})

    for m in messages:
        formatted.append({"role": m["role"], "content": m["content"]})

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=formatted,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content