"""
Thin wrapper around the Groq API. Every agent goes through this single
function so retries, model choice, and error handling live in one place.
"""

import os
import time
from groq import Groq, APITimeoutError, APIConnectionError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
        "and paste your key from https://console.groq.com/keys"
    )

# 60s timeout — the default was tight enough that a slow network hiccup could
# fail a request outright instead of just taking a bit longer.
client = Groq(api_key=_api_key, timeout=60.0)

# Groq deprecated llama-3.3-70b-versatile — this is their recommended replacement.
MODEL_NAME = "openai/gpt-oss-120b"


def _create(messages: list[dict], temperature: float, max_tokens: int):
    """One Groq request, with a single retry on transient network failures."""
    for attempt in range(2):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                # gpt-oss is a reasoning model: hidden reasoning tokens share the output
                # budget with the visible reply. At the default effort it can burn most of
                # the budget thinking, which truncated replies mid-sentence.
                extra_body={"reasoning_effort": "low"},
            )
        except (APITimeoutError, APIConnectionError) as e:
            if attempt == 0:
                time.sleep(2)
                continue
            raise RuntimeError(
                "Groq API timed out twice in a row — this is usually a network hiccup, "
                "not a bug. Try again in a moment."
            ) from e
        except APIStatusError as e:
            if e.status_code == 413:
                raise RuntimeError(
                    "The request was too large for Groq's free-tier rate limit "
                    "(8000 tokens/request). Try a shorter message, or ask for a smaller edit."
                ) from e
            raise


MAX_CONTINUATIONS = 2


def call_llm(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.6,
    max_tokens: int = 1024,
) -> str:
    chat_messages = [{"role": "system", "content": system_prompt}] + messages

    response = _create(chat_messages, temperature, max_tokens)
    choice = response.choices[0]
    text = choice.message.content or ""

    # Safety net: if the reply hit the token cap, ask the model to pick up where it stopped
    # instead of handing the user a half-finished answer.
    continuations = 0
    while choice.finish_reason == "length" and continuations < MAX_CONTINUATIONS:
        continuations += 1
        chat_messages_cont = chat_messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": "Continue exactly where you stopped. Do not repeat anything "
                           "you already wrote and do not add a preamble.",
            },
        ]
        response = _create(chat_messages_cont, temperature, max_tokens)
        choice = response.choices[0]
        text += choice.message.content or ""

    if not text.strip():
        raise RuntimeError(
            "The model returned an empty reply (its reasoning used up the token budget). "
            "Please resend your message."
        )
    return text
