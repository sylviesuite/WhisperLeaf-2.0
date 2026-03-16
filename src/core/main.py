"""
Main FastAPI application for Sovereign AI / WhisperLeaf.
"""

from pathlib import Path
import json
import os
import re
import tempfile
import time
import uuid
from typing import List, Optional, Dict, Any, Literal

import httpx
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db, init_database
from .models import Document, User
from .vault import VaultManager
from .vector_store import VectorStore
from .document_processor import DocumentProcessor
from .memory_manager import MemoryManager
from .memory_search import MemorySearch
from .memory_models import (
    PrivacyLevel,
    MemoryEntry,
    MemoryType,
    EmotionalContext,
    MemoryMetadata,
)
from .chat_engine import generate_reply
from .local_model import LocalModelClient
from .memory import (
    init_memory_db,
    save_memory,
    get_recent_memories,
    get_recent_memory_entries,
    get_memory_count,
    search_memories_by_query,
    set_visibility as memory_set_visibility,
    get_audit_events,
    get_memory,
    list_memories,
    delete_memory,
    record_audit,
    VISIBILITY_VALUES,
)
from .tools_registry import register_tool, list_tools, call_tool
from .tools import tool_bus, register_memory_search_tool, register_docs_search_tool, register_system_status_tool

# -------------------------------------------------------------------
# FastAPI app + middleware
# -------------------------------------------------------------------

app = FastAPI(
    title="Sovereign AI API",
    description="API for the Sovereign AI system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock down for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend uptime for system.status
_APP_START_TIME = time.time()

# -------------------------------------------------------------------
# Paths, static files, templates, prompts
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Static dir (same level as src/) – CSS, JS, images only
STATIC_DIR = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates – HTML pages
TEMPLATES_DIR = PROJECT_ROOT / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# System prompt (WhisperLeaf identity)
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system.md"
try:
    SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    SYSTEM_PROMPT = (
        "You are WhisperLeaf. You are a calm, thoughtful AI assistant that runs privately on the user's machine. "
        "Help the user think clearly, explore ideas, solve problems, and reason carefully. "
        "Prioritize clarity, independence, privacy, and thoughtful discussion. "
        "Avoid corporate tone, unnecessary apologies, and mentioning training data or large tech companies. "
        "Speak plainly and help the user think through ideas."
    )

# Local model client (Ollama / local LLM server)
model_client = LocalModelClient()

# Model availability: set by startup health check (do not block startup if unavailable)
MODEL_AVAILABLE = False


async def _check_model_health() -> None:
    """Lightweight check that Ollama (or local model service) is reachable. Does not block startup."""
    global MODEL_AVAILABLE
    url = f"{model_client.base_url}/api/version"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            r.raise_for_status()
        MODEL_AVAILABLE = True
        print("[WhisperLeaf] Model service is available at %s" % model_client.base_url)
    except Exception as e:
        print("[WhisperLeaf] Model service not reachable at %s: %s. Start Ollama to use chat." % (model_client.base_url, e))
        MODEL_AVAILABLE = False


# Data / memory dirs
DATA_DIR = PROJECT_ROOT / "data"
memory_manager = MemoryManager(data_dir=str(DATA_DIR))
memory_search = MemorySearch(data_dir=str(DATA_DIR), memory_manager=memory_manager)
register_memory_search_tool(memory_search)
vault_manager = VaultManager()
vector_store = VectorStore(data_dir=str(DATA_DIR))
document_processor = DocumentProcessor()
DOCUMENTS_DIR = DATA_DIR / "documents"
DOCUMENTS_INDEX_PATH = DOCUMENTS_DIR / "index.json"
register_docs_search_tool(vector_store)
register_system_status_tool(
    model_name=model_client.model_name,
    get_memory_count=get_memory_count,
    get_docs_count=lambda: (vector_store.get_collection_stats() or {}).get("count", 0),
    get_tools_count=lambda: len(list_tools()),
    start_time=_APP_START_TIME,
)


def _register_tools() -> None:
    """Register built-in tools (capture_thought, search_memories, reflect)."""

    async def capture_thought_handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        text = (payload.get("text") or "").strip()
        if not text:
            return {"saved": False, "error": "Missing or empty text"}
        source = payload.get("source") or "capture_thought"
        memory_id = save_memory(text, source=source)
        return {"saved": True, "id": memory_id}

    def search_memories_handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        limit = min(int(payload.get("limit", 5)), 50)
        entries = get_recent_memory_entries(limit=limit, exclude_blocked=True)
        return {"entries": entries}

    async def reflect_handler(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (payload.get("prompt") or payload.get("text") or "").strip()
        if not prompt:
            return {"reflection": "", "error": "Missing prompt or text"}
        client = context.get("model_client")
        if not client:
            return {"reflection": "", "error": "Model client not available"}
        system = "You are reflecting on the following. Reply with a brief, thoughtful reflection (1-3 sentences)."
        reply = await client.chat(system, [{"role": "user", "content": prompt}])
        return {"reflection": (reply or "").strip()}

    register_tool(
        "capture_thought",
        "Store a thought or note in memory (same as remember).",
        {"type": "object", "properties": {"text": {"type": "string"}, "source": {"type": "string"}}, "required": ["text"]},
        capture_thought_handler,
    )
    register_tool(
        "search_memories",
        "Return recent memories (excluding blocked).",
        {"type": "object", "properties": {"limit": {"type": "integer", "default": 5}}, "required": []},
        search_memories_handler,
    )
    register_tool(
        "reflect",
        "Get a short LLM reflection on the given prompt.",
        {"type": "object", "properties": {"prompt": {"type": "string"}, "text": {"type": "string"}}, "required": []},
        reflect_handler,
    )


_register_tools()

# -------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database and components on startup."""
    init_database()
    init_memory_db(str(DATA_DIR / "whisperleaf_memory.db"))
    print("Sovereign AI API server started successfully")

# -------------------------------------------------------------------
# Startup: model health check (non-blocking; server still launches if Ollama is down)
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_model_health_check():
    await _check_model_health()


# -------------------------------------------------------------------
# Basic routes: status, home, chat UI
# -------------------------------------------------------------------

@app.get("/api/status")
async def api_status():
    """Simple status endpoint (former JSON root)."""
    return {"message": "Sovereign AI API", "version": "1.0.0"}


@app.get("/api/model/status")
async def api_model_status():
    """Model availability from startup health check. UI can show a message when unavailable."""
    return {"model_available": MODEL_AVAILABLE}


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page: templates/index.html."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat UI: templates/whisperleaf_chat.html."""
    return templates.TemplateResponse(
        "whisperleaf_chat.html",
        {"request": request, "app_name": "WhisperLeaf"},
    )

# -------------------------------------------------------------------
# Memory-backed chat endpoint
# -------------------------------------------------------------------

class MemoryChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    top_k: Optional[int] = None
    mode: Optional[str] = None


def _serialize_memory_used(memory_entry, score: float) -> Dict[str, Any]:
    """Build a small dict for memories_used in the chat response."""
    content_src = memory_entry.content or memory_entry.title or ""
    snippet = content_src[:100]
    if len(content_src) > 100:
        snippet = snippet.rstrip() + "..."
    return {
        "id": memory_entry.id,
        "title": memory_entry.title or "",
        "snippet": snippet,
        "mood": getattr(memory_entry.emotional_context, "primary_mood", None) or "",
        "score": round(score, 4),
    }


def _chat_message_to_memory(message: str, session_id: Optional[str]) -> MemoryEntry:
    """Build a MemoryEntry for a user chat message with minimal metadata."""
    tags = ["source:chat", "role:user"]
    if session_id:
        tags.append(f"session_id:{session_id}")
    return MemoryEntry(
        memory_type=MemoryType.CONVERSATION,
        title="Chat",
        content=message,
        emotional_context=EmotionalContext(primary_mood="neutral"),
        metadata=MemoryMetadata(tags=tags),
        privacy_level=PrivacyLevel.PRIVATE,
    )


@app.post("/api/chat-memory")
async def memory_chat(request: MemoryChatRequest):
    """
    Chat endpoint with persistent memory:
    - stores user message
    - retrieves relevant memories
    - generates reply
    - returns reply, memories_used, session_id
    """
    session_id = request.session_id or str(uuid.uuid4())
    top_k = 5 if request.top_k is None else request.top_k

    # Store user message in memory before generating reply
    try:
        entry = _chat_message_to_memory(request.message, session_id)
        if memory_manager.store_memory(entry):
            memory_search.add_memory_to_search(entry)
    except Exception:
        # Don't crash on memory issues
        pass

    try:
        memory_results = memory_search.semantic_search(
            query=request.message,
            limit=top_k,
            privacy_level=PrivacyLevel.PRIVATE,
        )
    except Exception:
        memory_results = []

    mode = request.mode or "system"
    reply = generate_reply(request.message, memory_results, mode=mode)
    memories_used = [_serialize_memory_used(m, s) for m, s in memory_results]

    return {
        "reply": reply,
        "memories_used": memories_used,
        "session_id": session_id,
    }

# -------------------------------------------------------------------
# Simple stateless chat endpoint (browser-managed history)
# -------------------------------------------------------------------

# In-memory session persistence: session_id -> list of {role, content}
# Capped to avoid unbounded growth; oldest session evicted when full.
MAX_CHAT_SESSIONS = 500
CHAT_SESSIONS: Dict[str, List[Dict[str, str]]] = {}


def _evict_chat_session_if_needed(session_id: Optional[str]) -> None:
    """If at cap and session_id is new, evict oldest session (insertion order)."""
    if not session_id or session_id in CHAT_SESSIONS:
        return
    if len(CHAT_SESSIONS) >= MAX_CHAT_SESSIONS:
        oldest = next(iter(CHAT_SESSIONS), None)
        if oldest:
            CHAT_SESSIONS.pop(oldest, None)

Role = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    history: List[ChatMessage]


# Max conversation messages sent to the model (last N only); ~12 exchanges = 24 messages
MAX_CONTEXT_MESSAGES = 24

# Session conversation summaries: session_id -> summary text (for context when history is trimmed)
SESSION_SUMMARIES: Dict[str, str] = {}

# Summarization prompt and limits
SUMMARY_SYSTEM = (
    "You are a concise summarizer. Summarize conversation excerpts. "
    "Capture important facts, decisions, user goals, and key context. "
    "Output only the summary, no preamble or labels."
)
MAX_SUMMARY_CHARS = 2000
MAX_EXCERPT_CHARS_PER_MESSAGE = 600


def _format_messages_for_summary(
    messages: List[Dict[str, str]], max_per_message: int = MAX_EXCERPT_CHARS_PER_MESSAGE
) -> str:
    """Format message list for summarization; truncate long messages to stay within token limits."""
    parts = []
    for m in messages:
        role = (m.get("role") or "user").capitalize()
        content = (m.get("content") or "").strip()
        if len(content) > max_per_message:
            content = content[: max_per_message - 3].rstrip() + "..."
        parts.append("%s: %s" % (role, content))
    return "\n\n".join(parts)


async def _summarize_and_store_older(
    session_id: str,
    older_messages: List[Dict[str, str]],
) -> None:
    """
    Summarize the older portion of the conversation and store in SESSION_SUMMARIES.
    If a summary already exists, ask the model to merge the new excerpt into it.
    On failure (e.g. model unavailable), leaves existing summary unchanged.
    """
    if not older_messages or not session_id:
        return
    excerpt = _format_messages_for_summary(older_messages)
    if not excerpt.strip():
        return
    prev = (SESSION_SUMMARIES.get(session_id) or "").strip()
    if prev:
        prompt = (
            "Update this conversation summary with the following new excerpt. "
            "Preserve important facts, decisions, user goals, and key context. "
            "Output only the updated summary, no preamble.\n\n"
            "Current summary:\n%s\n\nNew excerpt:\n%s"
        ) % (prev[:1500] if len(prev) > 1500 else prev, excerpt)
    else:
        prompt = (
            "Summarize this conversation excerpt. "
            "Capture important facts, decisions, user goals, and key context. "
            "Output only the summary, no preamble.\n\nExcerpt:\n%s"
        ) % excerpt
    try:
        summary = await model_client.chat(SUMMARY_SYSTEM, [{"role": "user", "content": prompt}])
        if summary and summary.strip():
            text = summary.strip()
            if len(text) > MAX_SUMMARY_CHARS:
                text = text[: MAX_SUMMARY_CHARS - 3].rstrip() + "..."
            SESSION_SUMMARIES[session_id] = text
            print("[WhisperLeaf] Session summary updated for session %s (%s chars)" % (session_id[:8], len(text)))
    except Exception as e:
        print("[WhisperLeaf] Summarization failed (continuing without): %s" % e)


def _sse_message(event: str, data: str) -> bytes:
    """Format one SSE message (event + data lines, then blank line)."""
    lines = [f"event: {event}"]
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    lines.append("")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _should_auto_save_memory(text: str) -> bool:
    """
    Heuristic: only auto-save likely-stable facts (no questions, no tiny/huge messages).
    Deterministic, no extra dependencies.
    """
    if not text:
        return False
    s = text.strip()
    if len(s) < 12 or len(s) > 500:
        return False
    if s.endswith("?"):
        return False
    lower = s.lower()
    prefixes = (
        "i am ",
        "i'm ",
        "i have ",
        "i live ",
        "i work ",
        "i prefer ",
        "my project ",
        "we are working on ",
    )
    if any(lower.startswith(p) for p in prefixes):
        return True
    if "my goal" in lower or "my plan" in lower or "my setup" in lower:
        return True
    return False


# Keywords that suggest the text is sensitive; auto-memory skips when present.
_SENSITIVE_KEYWORDS = (
    "password",
    "passcode",
    "api key",
    "apikey",
    "secret",
    "token",
    "ssh",
    "private key",
    "seed phrase",
    "ssn",
    "social security",
)


def _looks_sensitive(text: str) -> bool:
    """
    True if the text appears to contain secrets or PII. Used only to skip
    auto-memory; "remember:" is unaffected (explicit user intent).
    Deterministic, no extra dependencies.
    """
    if not text:
        return False
    lower = text.lower()
    for kw in _SENSITIVE_KEYWORDS:
        if kw in lower:
            return True
    if re.search(r"\d{16,}", text):
        return True
    if "begin" in lower and "private key" in lower:
        return True
    return False


REWRITE_QUERY_SYSTEM = (
    "You rewrite user messages into short semantic memory search queries. "
    "Output only the query: noun phrases and key topics, no explanation or punctuation."
)


async def _rewrite_memory_query(user_message: str) -> str:
    """
    Rewrite the user message into a short semantic retrieval query.
    On failure or empty result, returns the original message (caller should still fall back).
    """
    if not (user_message or "").strip():
        return (user_message or "").strip()
    try:
        reply = await model_client.chat(
            REWRITE_QUERY_SYSTEM,
            [{"role": "user", "content": (user_message or "").strip()}],
        )
        if not reply:
            return (user_message or "").strip()
        # First line only, stripped, reasonable length for retrieval
        query = reply.split("\n")[0].strip()
        if not query:
            return (user_message or "").strip()
        return query[:200].strip()
    except Exception:
        return (user_message or "").strip()


async def _build_memory_context(query: str, limit: int = 5):
    """
    Build a RELEVANT MEMORY context block via the Tool Bus (memory.search).
    Formats tool result and records used_in_context for simple-memory entries.
    Returns (block_string, snippets_list) for model context and UI visibility.
    """
    result = await tool_bus.execute(
        "memory.search",
        {"query": (query or "").strip(), "top_k": limit},
        context={},
    )
    if not result.ok or not result.data:
        return ("", [])
    snippets = result.data.get("snippets") or []
    entries_for_audit = result.data.get("entries_for_audit") or []
    for e in entries_for_audit:
        try:
            record_audit(e["id"], "used_in_context", {"route": "chat"})
        except Exception:
            pass
    if not snippets:
        return ("", [])
    block = "RELEVANT MEMORY:\n" + "\n".join("- " + s for s in snippets)
    return (block, list(snippets))


async def _build_docs_context(query: str, limit: int = 5):
    """
    Build RELEVANT DOCUMENTS context block via docs.search.
    Returns (block_str, source_names, excerpts) for context, citation, and preview.
    excerpts: list of {"name": title, "snippet": text} per chunk (for UI preview).
    """
    result = await tool_bus.execute(
        "docs.search",
        {"query": (query or "").strip(), "top_k": limit},
        context={},
    )
    if not result.ok or not result.data:
        return ("", [], [])
    items = result.data if isinstance(result.data, list) else []
    if not items:
        return ("", [], [])
    lines = []
    seen = set()
    source_names: List[str] = []
    excerpts: List[Dict[str, str]] = []
    for r in items:
        title = (r.get("title") or r.get("path") or "Document").strip()
        if title and title not in seen:
            seen.add(title)
            source_names.append(title)
        snippet = (r.get("snippet") or r.get("content") or "").strip()
        if snippet:
            lines.append("%s: %s" % (title, snippet[:400] + ("..." if len(snippet) > 400 else "")))
            # Store full snippet for preview (cap length for payload)
            excerpts.append({"name": title, "snippet": snippet[:1200] + ("..." if len(snippet) > 1200 else "")})
    if not lines:
        return ("", [], [])
    block = "RELEVANT DOCUMENTS:\n" + "\n".join("- " + line for line in lines)
    return (block, source_names, excerpts)


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Chat endpoint: streams assistant reply as SSE. Conversation state is
    managed on the client. Supports "remember: ..." and "no memory: ...".
    """
    raw_message = (payload.message or "").strip()
    print("[WhisperLeaf chat] POST /api/chat message_len=%s history_len=%s" % (len(raw_message), len(payload.history or [])))

    # Reject empty messages so the client always gets a well-formed response
    if not raw_message:
        async def empty_message_stream():
            yield _sse_message("error", "Please enter a message.")
        return StreamingResponse(
            empty_message_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    # "remember: ..." always stores and returns short reply
    if raw_message.lower().startswith("remember:"):
        text = raw_message[9:].strip()
        if text:
            save_memory(text, source="chat")
        reply = "I've remembered that."
        sid = getattr(payload, "session_id", None)
        if sid:
            _evict_chat_session_if_needed(sid)
            session_list = [{"role": m.role, "content": m.content} for m in payload.history]
            session_list.append({"role": "assistant", "content": reply})
            CHAT_SESSIONS[sid] = session_list

        async def remember_stream() -> Any:
            yield _sse_message("chunk", reply)
            if text:
                yield _sse_message("memory_saved", json.dumps({"text": text[:200] + ("..." if len(text) > 200 else "")}))
            yield _sse_message("done", "")

        return StreamingResponse(
            remember_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # "no memory: ..." never stores; strip prefix and send rest to model
    no_memory = raw_message.lower().startswith("no memory:")
    message_for_model = raw_message[10:].strip() if no_memory else raw_message

    # Automatic memory: save likely-stable facts (deterministic heuristic)
    saved_memory_notification = None
    if not no_memory and message_for_model and _should_auto_save_memory(message_for_model):
        clean = message_for_model.strip()
        if not _looks_sensitive(clean):
            save_memory(clean)
            snippet = clean[:80] + ("..." if len(clean) > 80 else "")
            print(f"Auto-saved memory: {snippet}")
            saved_memory_notification = {"text": clean[:200] + ("..." if len(clean) > 200 else "")}

    # Build messages with semantic/keyword memory context when available
    messages = [{"role": m.role, "content": m.content} for m in payload.history]
    memory_query = message_for_model
    memory_block = ""
    memory_snippets: List[str] = []
    try:
        memory_query = await _rewrite_memory_query(message_for_model)
        if not (memory_query or "").strip():
            memory_query = message_for_model
        memory_block, memory_snippets = await _build_memory_context(memory_query, limit=5)
    except Exception as e:
        print("[WhisperLeaf chat] memory retrieval failed (continuing without): %s" % e)
        memory_block = ""
        memory_snippets = []
    used_memory = bool(memory_block)
    doc_block = ""
    doc_sources: List[str] = []
    doc_excerpts: List[Dict[str, str]] = []
    try:
        doc_block, doc_sources, doc_excerpts = await _build_docs_context(memory_query, limit=5)
    except Exception as e:
        print("[WhisperLeaf chat] docs context failed (continuing without): %s" % e)
    if memory_block or doc_block:
        note = "Note: You may use the context below to answer.\n\n"
        parts = [note]
        if memory_block:
            parts.append(memory_block)
        if doc_block:
            parts.append(doc_block)
        user_content = "\n\n".join(parts) + "\n\nUser message:\n" + message_for_model
    else:
        user_content = message_for_model
    messages.append({"role": "user", "content": user_content})

    session_id = getattr(payload, "session_id", None)
    if session_id:
        _evict_chat_session_if_needed(session_id)
        session_list = [{"role": m.role, "content": m.content} for m in payload.history]
        existing = CHAT_SESSIONS.get(session_id, [])
        if len(session_list) >= len(existing):
            CHAT_SESSIONS[session_id] = session_list

    # When beyond context window: summarize older portion and store as session memory, then trim
    if len(messages) > MAX_CONTEXT_MESSAGES:
        older_count = len(messages) - MAX_CONTEXT_MESSAGES
        if session_id and older_count > 0:
            await _summarize_and_store_older(session_id, messages[:older_count])
        messages = messages[-MAX_CONTEXT_MESSAGES:]

    # Include conversation summary in system context when present (so model sees prior context)
    session_summary = (SESSION_SUMMARIES.get(session_id, "") or "").strip() if session_id else ""
    effective_system = (
        (SYSTEM_PROMPT + "\n\n--- Conversation context so far ---\n" + session_summary)
        if session_summary
        else SYSTEM_PROMPT
    )

    async def generate() -> Any:
        full_reply = ""
        try:
            if saved_memory_notification:
                yield _sse_message("memory_saved", json.dumps(saved_memory_notification))
            if doc_sources:
                yield _sse_message(
                    "doc_sources",
                    json.dumps({"sources": doc_sources, "excerpts": doc_excerpts}),
                )
            if used_memory:
                status = json.dumps({
                    "step": "memory_search",
                    "query": (memory_query or "")[:40].strip(),
                })
                yield _sse_message("status", status)
                meta = json.dumps({
                    "used_memory": True,
                    "memory_count": len(memory_snippets),
                    "snippets": memory_snippets,
                })
                yield _sse_message("meta", meta)
            try:
                chunk_count = 0
                async for chunk in model_client.chat_stream(effective_system, messages):
                    full_reply += chunk
                    chunk_count += 1
                    if chunk_count == 1:
                        print("[WhisperLeaf chat] first chunk received len=%s" % len(chunk))
                    yield _sse_message("chunk", chunk)
                print("[WhisperLeaf chat] stream done chunks=%s reply_len=%s" % (chunk_count, len(full_reply)))
                if full_reply:
                    print("[WhisperLeaf debug] assembled backend reply (first 120 chars): %r" % full_reply[:120])
                yield _sse_message("done", "")
                if session_id and session_id in CHAT_SESSIONS:
                    CHAT_SESSIONS[session_id].append({"role": "assistant", "content": full_reply})
            except httpx.ConnectError:
                print("[WhisperLeaf chat] model ConnectError (is Ollama running?)")
                yield _sse_message(
                    "error",
                    "Cannot reach the local model. Please start Ollama (or your local LLM server) and try again.",
                )
            except httpx.HTTPStatusError as e:
                print("[WhisperLeaf chat] model HTTPStatusError: %s" % e)
                if e.response is not None and e.response.status_code == 404:
                    yield _sse_message(
                        "error",
                        "Model not found. Install it in Ollama (e.g. ollama pull llama3.2) and try again.",
                    )
                else:
                    yield _sse_message("error", "Local model error: %s" % (e,))
            except Exception as e:
                print("[WhisperLeaf chat] unexpected error: %s" % e)
                yield _sse_message("error", "Something went wrong. Please try again.")
        except (BrokenPipeError, ConnectionResetError) as e:
            print("[WhisperLeaf] client disconnected or connection reset: %s" % e)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/chat/history")
async def get_chat_history(session_id: Optional[str] = Query(None)):
    """Return persisted messages for the given session. Safe if session_id missing or unknown."""
    return {"history": CHAT_SESSIONS.get(session_id or "", [])}


class ChatClearBody(BaseModel):
    session_id: Optional[str] = None


@app.post("/api/chat/clear")
async def clear_chat_session(body: ChatClearBody):
    """Clear persisted history and session summary for the given session."""
    if body.session_id:
        CHAT_SESSIONS.pop(body.session_id, None)
        SESSION_SUMMARIES.pop(body.session_id, None)
    return {"ok": True}


# -------------------------------------------------------------------
# Memory permissions + audit (Trust Layer)
# -------------------------------------------------------------------

class MemoryVisibilityBody(BaseModel):
    visibility: Literal["normal", "private", "pinned", "blocked"]


@app.post("/api/memory/{memory_id}/visibility")
async def set_memory_visibility(memory_id: int, body: MemoryVisibilityBody):
    """Set visibility for a memory. Blocked memories are never returned in search/context."""
    if body.visibility not in VISIBILITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid visibility")
    ok = memory_set_visibility(memory_id, body.visibility)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"memory_id": memory_id, "visibility": body.visibility}


@app.get("/api/memory/{memory_id}/audit")
async def get_memory_audit(memory_id: int, limit: int = 50):
    """Return the last N audit events for a memory (default 50)."""
    if get_memory(memory_id) is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    events = get_audit_events(memory_id, limit=min(limit, 200))
    return {"memory_id": memory_id, "events": events}


@app.get("/api/memories")
async def api_list_memories(limit: int = Query(200, ge=1, le=500)):
    """List saved memories for the management UI (newest first)."""
    return {"memories": list_memories(limit=limit)}


@app.delete("/api/memory/{memory_id}")
async def api_delete_memory(memory_id: int):
    """Delete a saved memory by id."""
    if not delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True, "memory_id": memory_id}


# -------------------------------------------------------------------
# Tools Registry (plugin layer)
# -------------------------------------------------------------------

@app.get("/api/tools")
async def api_list_tools():
    """List registered tools (name, description, input_schema)."""
    return {"tools": list_tools()}


class ToolCallBody(BaseModel):
    name: str
    payload: Dict[str, Any] = {}


@app.post("/api/tools/call")
async def api_call_tool(body: ToolCallBody):
    """Execute a tool by name with the given payload."""
    try:
        context = {"model_client": model_client}
        result = await call_tool(body.name, body.payload or {}, context)
        return {"ok": True, "result": result}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------
# Document ingestion (simple upload, chunk, embed, search)
# -------------------------------------------------------------------

def _load_documents_index() -> Dict[str, Any]:
    """Load document index from disk. Returns dict doc_id -> {title, filename, chunks_count, uploaded_at}."""
    if not DOCUMENTS_INDEX_PATH.exists():
        return {}
    try:
        with open(DOCUMENTS_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_documents_index(index: Dict[str, Any]) -> None:
    """Persist document index to disk."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCUMENTS_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


@app.post("/api/documents/upload")
async def upload_document_ingest(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
):
    """Upload a document: store locally, extract text, chunk, and add to vector store."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "document"
    ext = Path(filename).suffix.lower()
    if ext not in document_processor.get_supported_types():
        raise HTTPException(
            status_code=400,
            detail="Unsupported type. Supported: %s" % ", ".join(document_processor.get_supported_types()),
        )
    doc_id = str(uuid.uuid4())
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ") or "doc"
    stored_path = DOCUMENTS_DIR / f"{doc_id}_{safe_name}"
    try:
        content = await file.read()
        stored_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file: %s" % e)
    try:
        processed = document_processor.process_document(str(stored_path))
        if processed["processing_status"] != "success":
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Processing failed: %s" % processed.get("processing_status", "error"))
        chunks = processed.get("chunks") or []
        if not chunks and processed.get("text", "").strip():
            chunks = [processed["text"].strip()[:10000]]
        title_str = (title or filename or doc_id).strip()
        vector_store.add_chunks(
            document_id=doc_id,
            chunks=chunks,
            metadata={"title": title_str, "filename": filename},
        )
        index = _load_documents_index()
        index[doc_id] = {
            "title": title_str,
            "filename": filename,
            "chunks_count": len(chunks),
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _save_documents_index(index)
        return {
            "id": doc_id,
            "title": title_str,
            "chunks_count": len(chunks),
            "word_count": processed.get("word_count", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Ingestion failed: %s" % e)


@app.get("/api/documents")
async def list_ingested_documents():
    """List ingested documents (from index)."""
    index = _load_documents_index()
    return {
        "documents": [
            {"id": doc_id, **meta}
            for doc_id, meta in index.items()
        ]
    }


@app.delete("/api/documents/{document_id}")
async def delete_ingested_document(document_id: str):
    """Remove document from index, vector store, and delete stored file."""
    index = _load_documents_index()
    if document_id not in index:
        raise HTTPException(status_code=404, detail="Document not found")
    meta = index[document_id]
    vector_store.remove_document(document_id)
    filename = meta.get("filename", "")
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ") or "doc"
    stored_path = DOCUMENTS_DIR / f"{document_id}_{safe_name}"
    if stored_path.exists():
        try:
            stored_path.unlink()
        except Exception:
            pass
    del index[document_id]
    _save_documents_index(index)
    return {"ok": True, "id": document_id}


# -------------------------------------------------------------------
# Vault management endpoints
# -------------------------------------------------------------------

@app.post("/api/vault/documents")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    tags: Optional[str] = Form(None),
    user_id: str = Form("default_user"),  # TODO: auth
    db: Session = Depends(get_db),
):
    """Upload a document to the vault."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Process tags
            tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

            # Add document to vault
            document = vault_manager.add_document(
                file_path=temp_file_path,
                title=title,
                user_id=user_id,
                db=db,
                tags=tag_list,
                metadata={"original_filename": file.filename},
            )

            # Process document content for vector store
            processed_doc = document_processor.process_document(document.file_path)

            if processed_doc["processing_status"] == "success" and processed_doc["text"]:
                # Add to vector store
                vector_store.add_document(
                    document_id=document.id,
                    content=processed_doc["text"],
                    metadata={
                        "title": document.title,
                        "content_type": document.content_type,
                        "tags": document.tags,
                        "word_count": processed_doc.get("word_count", 0),
                    },
                )

            return {
                "id": document.id,
                "title": document.title,
                "content_type": document.content_type,
                "file_size": document.file_size,
                "processing_status": processed_doc["processing_status"],
                "word_count": processed_doc.get("word_count", 0),
            }

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@app.get("/api/vault/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = None,
    content_type: Optional[str] = None,
    user_id: str = "default_user",  # TODO: auth
    db: Session = Depends(get_db),
):
    """List documents in the vault."""
    try:
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

        documents = vault_manager.list_documents(
            user_id=user_id,
            db=db,
            skip=skip,
            limit=limit,
            tags=tag_list,
            content_type=content_type,
        )

        return [
            {
                "id": doc.id,
                "title": doc.title,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "tags": doc.tags,
                "metadata": doc.metadata_json,
            }
            for doc in documents
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.get("/api/vault/documents/{document_id}")
async def get_document(
    document_id: str,
    user_id: str = "default_user",  # TODO: auth
    db: Session = Depends(get_db),
):
    """Get document details."""
    try:
        document = vault_manager.get_document(document_id, user_id, db)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": document.id,
            "title": document.title,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "source_url": document.source_url,
            "source_type": document.source_type,
            "tags": document.tags,
            "metadata": document.metadata_json,
            "content_hash": document.content_hash,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")


@app.delete("/api/vault/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = "default_user",  # TODO: auth
    db: Session = Depends(get_db),
):
    """Delete a document from the vault."""
    try:
        # Remove from vector store first
        vector_store.remove_document(document_id)

        # Remove from vault
        success = vault_manager.delete_document(document_id, user_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# -------------------------------------------------------------------
# Search + statistics + processing endpoints
# -------------------------------------------------------------------

@app.post("/api/vault/search")
async def search_documents(
    query: str = Form(...),
    n_results: int = Form(10),
    document_ids: Optional[str] = Form(None),
    user_id: str = Form("default_user"),  # TODO: auth
):
    """Search documents using semantic similarity."""
    try:
        doc_ids = [doc_id.strip() for doc_id in document_ids.split(",")] if document_ids else None

        results = vector_store.search(
            query=query,
            n_results=n_results,
            document_ids=doc_ids,
        )

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@app.get("/api/vault/statistics")
async def get_vault_statistics(
    user_id: str = "default_user",  # TODO: auth
    db: Session = Depends(get_db),
):
    """Get vault statistics."""
    try:
        vault_stats = vault_manager.get_vault_statistics(user_id, db)
        vector_stats = vector_store.get_collection_stats()

        return {
            "vault": vault_stats,
            "vector_store": vector_stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@app.get("/api/processing/supported-types")
async def get_supported_types():
    """Get supported document types."""
    return {
        "supported_types": document_processor.get_supported_types(),
        "vault_allowed_extensions": list(vault_manager.allowed_extensions),
    }

# -------------------------------------------------------------------
# Dev entrypoint
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )