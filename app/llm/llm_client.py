import os
import google.generativeai as genai
from typing import Optional

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))

_model = genai.GenerativeModel("gemini-2.0-flash")


def chat_completion(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Send a list of {"role": "user"|"assistant", "content": "..."} messages
    to Gemini and return the assistant reply as a string.
    """
    history = []
    last_user_msg = ""

    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        if role == "user":
            last_user_msg = m["content"]
            history.append({"role": "user", "parts": [m["content"]]})
        else:
            history.append({"role": "model", "parts": [m["content"]]})

    sys_instruction = system_prompt or ""

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=sys_instruction if sys_instruction else None,
    )

    chat = model.start_chat(history=history[:-1] if history else [])

    response = chat.send_message(
        last_user_msg,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )

    return response.text