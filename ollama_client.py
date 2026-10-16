"""Tiny wrapper around the local Ollama HTTP API (no data leaves the machine)."""
import requests

import config


def embed(text: str) -> list[float]:
    """Return a 768-dim embedding from nomic-embed-text."""
    resp = requests.post(
        f"{config.OLLAMA_URL}/api/embed",
        json={"model": config.EMBED_MODEL, "input": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def chat(system_prompt: str, user_prompt: str) -> str:
    """Send one system + one user message to llama3.1 and return the reply text."""
    resp = requests.post(
        f"{config.OLLAMA_URL}/api/chat",
        json={
            "model": config.CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0},  # deterministic answers make demos repeatable
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
