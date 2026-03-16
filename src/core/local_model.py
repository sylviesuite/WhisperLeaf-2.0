"""
Async local LLM client for WhisperLeaf.

Uses an Ollama / llama.cpp style HTTP API running locally.
Thin wrapper around the HTTP endpoint; keeps all data on the user's machine.
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx


class LocalModelClient:
    """
    Minimal async client for a local chat-style LLM HTTP API.

    Expects an endpoint compatible with Ollama's /api/chat:
      POST {base_url}/api/chat
      {
        "model": "<model_name>",
        "messages": [{"role": "...", "content": "..."}],
        "stream": false
      }
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("WHISPERLEAF_MODEL_URL")
            or "http://localhost:11434"
        ).rstrip("/")
        self.model_name = (
            model_name
            or os.getenv("WHISPERLEAF_MODEL_NAME")
            or "llama3.2"
        )
        self.timeout = timeout

    async def chat(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Send a chat completion request to the local model.

        - system_prompt: long-form system instructions (WhisperLeaf identity)
        - messages: prior turns, each {"role": "user"|"assistant", "content": "..."}
        Returns the assistant reply text.
        """

        full_messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": full_messages,
            "stream": False,
            "options": {"num_ctx": 4096},
        }

        model_endpoint = f"{self.base_url}/api/chat"
        prompt_length = sum(len(m.get("content", "")) for m in full_messages)

        # This assumes an Ollama-style /api/chat endpoint.
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(model_endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Example Ollama response: {"message": {"content": "..."}}
        msg = data.get("message") or {}
        content = msg.get("content")
        if not content:
            content = data.get("content") or ""
        content = (content or "").strip()
        if not content:
            raise RuntimeError("Local model returned an empty response.")

        response_length = len(content)
        print(
            "[WhisperLeaf model debug]",
            "MODEL_ENDPOINT=", model_endpoint,
            "MODEL_NAME=", self.model_name,
            "PROMPT_LENGTH=", prompt_length,
            "RESPONSE_LENGTH=", response_length,
        )
        return content

    async def chat_stream(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """
        Stream chat completion from the local model (Ollama-style NDJSON).

        Yields content chunks as they are generated.
        """
        full_messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": full_messages,
            "stream": True,
            "options": {"num_ctx": 4096},
        }
        model_endpoint = f"{self.base_url}/api/chat"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", model_endpoint, json=payload) as resp:
                resp.raise_for_status()
                buffer = ""
                chunk_count = 0
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        msg = data.get("message") or {}
                        content = msg.get("content") or data.get("response") or data.get("delta") or ""
                        if content is not None and content != "":
                            chunk_count += 1
                            if chunk_count <= 3:
                                print("[WhisperLeaf debug] raw chunk from Ollama: %r" % content)
                            yield content
                if chunk_count == 0:
                    print("[WhisperLeaf model] chat_stream received 0 content chunks from %s (check model name: %s)" % (model_endpoint, self.model_name))

