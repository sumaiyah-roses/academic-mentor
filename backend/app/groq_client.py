"""
Thin wrapper around the Groq API. Every agent goes through this single
function so retries, model choice, and error handling live in one place.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
        "and paste your key from https://console.groq.com/keys"
    )

client = Groq(api_key=_api_key)

# Groq deprecated llama-3.3-70b-versatile — this is their recommended replacement.
MODEL_NAME = "openai/gpt-oss-120b"


def call_llm(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.6,
    max_tokens: int = 1024,
) -> str:
    chat_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=chat_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
