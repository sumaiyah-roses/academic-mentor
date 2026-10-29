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
                    "This request (the conversation so far plus space reserved for the reply) exceeded "
                    "Groq's free-tier limit of 8000 tokens. Try again; if it repeats, start a new "
                    "session or ask for a smaller edit."
                ) from e
            raise


MAX_CONTINUATIONS = 2

# Groq's free tier rejects any single request where (prompt tokens + max_tokens) > 8000.
# Stay well under that, since our token estimate below is approximate.
REQUEST_TOKEN_BUDGET = 6500
MIN_CONTINUATION_ROOM = 300


def _estimate_tokens(messages: list[dict]) -> int:
    # Deliberately pessimistic (~3 chars/token): Markdown tables and symbols tokenise densely.
    return sum(len(m["content"]) for m in messages) // 3 + 50


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

    # Safety net: if the reply hit the token cap, ask the model to pick up where it stopped.
    # Each continuation re-sends the partial reply, so it must fit the request budget —
    # otherwise the retry itself would trigger the 413 "request too large" error.
    continuations = 0
    cut_short = False
    while choice.finish_reason == "length" and continuations < MAX_CONTINUATIONS:
        chat_messages_cont = chat_messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": "Continue exactly where you stopped. Do not repeat anything "
                           "you already wrote and do not add a preamble.",
            },
        ]
        room = REQUEST_TOKEN_BUDGET - _estimate_tokens(chat_messages_cont)
        if room < MIN_CONTINUATION_ROOM:
            cut_short = True
            break
        continuations += 1
        response = _create(chat_messages_cont, temperature, min(max_tokens, room))
        choice = response.choices[0]
        text += choice.message.content or ""

    if choice.finish_reason == "length":
        cut_short = True

    if not text.strip():
        raise RuntimeError(
            "The model returned an empty reply (its reasoning used up the token budget). "
            "Please resend your message."
        )
    if cut_short:
        text += "\n\n*(Reply was cut short by the free-tier size limit — type “continue” for the rest.)*"
    return text
