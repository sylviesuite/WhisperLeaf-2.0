"""
Ollama LLM client for WhisperLeaf chat.
Calls local Ollama at localhost:11434. Returns None on failure (caller can fall back).
"""

import os
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CHAT_TIMEOUT = int(os.getenv("OLLAMA_CHAT_TIMEOUT", "60"))


def chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> Optional[str]:
    """
    Send messages to Ollama chat API. Returns assistant content or None on failure.
    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
    """
    if not REQUESTS_AVAILABLE:
        return None
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=CHAT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message")
        if isinstance(msg, dict) and msg.get("content"):
            return msg["content"].strip()
        return None
    except Exception:
        return None
