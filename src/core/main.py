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
from .memory_injection_guard import (
    filter_relevant_memories,
    build_memory_context_block,
    detect_topic_reset,
)
from .mode_router import (
    ResponseMode,
    anti_engineering_scaffolding_instruction,
    conversational_posture,
    detect_mode,
    explain_mode_choice,
    engineering_scaffolding_allowed,
    parse_mode_override,
)
from .insight_box import build_mode_guidance
from .capture_mode import is_leaflink_originated_message
from .confidence_layer import build_confidence_guidance, select_confidence_level
from .depth_escalation import build_depth_escalation_guidance, select_depth_escalation_level
from .dual_mode import build_dual_mode_guidance, hits_explanation_intent, select_response_shape_mode
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

# Developer Mode (global): when True, internal codebase details may be discussed without an explicit user ask.
DEVELOPER_MODE: bool = False

# Backend uptime for system.status
_APP_START_TIME = time.time()

# -------------------------------------------------------------------
# Paths, static files, templates, prompts
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Static dir (same level as src/) – CSS, JS, images only
STATIC_DIR = PROJECT_ROOT / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Benchmarks dir – methodology and benchmark docs (e.g. /benchmarks/whisperleaf_energy_methodology.md)
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
if BENCHMARKS_DIR.exists():
    app.mount("/benchmarks", StaticFiles(directory=str(BENCHMARKS_DIR)), name="benchmarks")

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
        "Speak plainly and help the user think through ideas. "
        "Never expose internal file paths, modules, or implementation details unless the user explicitly "
        "asks about WhisperLeaf's codebase or system design."
    )

# Per-turn reinforcement of prompts/system.md Voice Specification (tone, phrasing, safety style).
# Capture / LeafLink / dual-mode structure rules still override shape and brevity when active for that turn.
WHISPERLEAF_VOICE_SPEC_LAYER = (
    "WhisperLeaf voice (full spec in system prompt — Voice Specification): calm, grounded, conversational—not corporate. "
    "Practical-first; suggest rather than command (“you can try” vs “you should”); no fluff or stiff AI voice. "
    "For real-world how-to / health / tools / “what should I do”: start the **first sentence** with usable guidance—no abstract opening (“At a practical level…”, “One pattern…”). "
    "Prefer “Main thing is…”, “Start with…”, “You can try…”; short bullets for options; ~4–6 short lines or 3–5 sentences unless another mode says otherwise. "
    "Accuracy: common mainstream options only; if uncertain, stay general—don’t guess fringe specifics. "
    "Preferred tone examples: “I’d start with…”, “Main thing is…”, “If it gets worse…”, “If it hangs around a few days…”. "
    "Avoid: “Please note that…”, “It is important to…”, “consult a healthcare professional”, “it is essential…” as filler. "
    "Safety: one calm natural line when relevant; no repetitive warnings. "
    "If Capture Mode / LeafLink / Structure Mode shapes this turn, follow that shape but keep this tone."
)


def is_explicit_codebase_query(message: str) -> bool:
    """
    True when the user intentionally asks about WhisperLeaf's codebase or system design.
    Used to allow internal paths, modules, and architecture in the response.
    """
    triggers = [
        "whisperleaf codebase",
        "this project",
        "your system",
        "how is whisperleaf built",
        "how does whisperleaf work",
        "show me your code",
        "in your code",
        "your architecture",
        "your implementation",
    ]
    msg = (message or "").lower()
    if any(trigger in msg for trigger in triggers):
        return True
    # User names concrete repo paths or internal modules → developer intent.
    developer_signals = (
        "src/core",
        "memory_search_tool",
        "memory_injection_guard",
        "injection_guard",
        "test_memory_bleed",
    )
    if any(sig in msg for sig in developer_signals):
        return True
    # Broader WhisperLeaf implementation questions (not generic chat mentioning the name).
    if "whisperleaf" in msg and any(
        x in msg
        for x in (
            "codebase",
            "implementation",
            "source code",
            "repository",
            "repo layout",
            "how is",
            "where is",
            "which file",
            "your code",
            "this app",
        )
    ):
        return True
    if "whisperleaf" in msg and any(
        phrase in msg
        for phrase in (
            "how does whisperleaf",
            "how is whisperleaf",
            "whisperleaf architecture",
            "whisperleaf implemented",
            "whisperleaf's code",
        )
    ):
        return True
    return False


def allows_internal_codebase_context(message: str) -> bool:
    """
    True when WhisperLeaf may reference internal paths, modules, and architecture in replies.
    Either Developer Mode is on, or the user explicitly asked about the codebase.
    """
    return DEVELOPER_MODE or is_explicit_codebase_query(message)


def response_contains_internal_leak(text: str) -> bool:
    """
    Heuristic: assistant text likely exposes internal repo details.
    Used when the user did NOT ask an explicit codebase question — triggers rewrite/sanitize.
    """
    if not (text or "").strip():
        return False
    low = (text or "").lower()
    if any(
        p in low
        for p in (
            "src/core",
            "memory_search_tool",
            "injection_guard",
            "memory_injection_guard",
            "system prompt",
        )
    ):
        return True
    # Path-like references to this repo (avoid flagging every generic `foo.py` in code blocks).
    if re.search(r"(?:^|\s)(?:src|tests)[/\\][^\s\n`]+\.py", low):
        return True
    if re.search(r"src[/\\]core[/\\]", low):
        return True
    # Internal tool / wiring names
    if any(t in low for t in ("tools_registry", "register_tool", "capture_thought")):
        return True
    return False


SANITIZE_INTERNAL_REPLY_SYSTEM = (
    "You rewrite assistant replies for a user-facing privacy boundary. "
    "Remove internal repository paths (e.g. src/core, tests/...), specific .py file paths, "
    "WhisperLeaf-internal module names (memory_search_tool, memory_injection_guard), "
    "mentions of system prompts, internal tool or registry names. "
    "Keep the same helpful intent using generic language and portable examples. "
    "If the text is already free of such internals, return it unchanged. "
    "Output only the rewritten answer, with no preamble or meta-commentary."
)


async def rewrite_reply_without_internals(model_client: LocalModelClient, reply: str) -> str:
    """LLM fallback: genericize a reply that leaked internal details."""
    r = (reply or "").strip()
    if not r:
        return reply
    try:
        out = await model_client.chat(
            SANITIZE_INTERNAL_REPLY_SYSTEM,
            [{"role": "user", "content": "Rewrite the following assistant reply:\n\n" + r}],
        )
        return (out or r).strip()
    except Exception:
        return r


def is_general_capability_meta_query(user_message: str) -> bool:
    """
    Capability / identity questions (e.g. 'can you write code?') that should use a normal
    assistant posture — not execution artifacts or internal repo paths.
    """
    s = (user_message or "").strip().lower()
    if not s or len(s) > 120:
        return False
    if is_explicit_codebase_query(s):
        return False
    task_cues = (
        "function",
        "class ",
        "script",
        "api ",
        "endpoint",
        "bug",
        "implement",
        "fibonacci",
        "algorithm",
        "regex",
        "sql",
        "html",
        "docker",
        "kubernetes",
        "write a ",
        "write an ",
        "debug",
        "refactor",
        "patch",
        "error message",
        "stack trace",
    )
    if any(c in s for c in task_cues):
        return False
    phrases = (
        "can you write code",
        "can you code",
        "do you write code",
        "can you program",
        "are you a programmer",
        "what can you do",
        "what are you",
        "who are you",
        "how do you work",
        "are you an ai",
        "are you a bot",
        "do you know how to code",
    )
    if any(p in s for p in phrases):
        return True
    if s in ("help", "help?", "hi", "hello", "hey"):
        return True
    return False


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
async def landing(request: Request):
    """Marketing landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def app_splash(request: Request):
    """Minimal owl splash entry page."""
    # Existing minimal owl splash template
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
@app.get("/chat-ui", response_class=HTMLResponse)
async def chat(request: Request):
    """Main chat UI."""
    # Use the real chat template filename
    return templates.TemplateResponse(
        "whisperleaf_chat.html",
        {"request": request, "app_name": "WhisperLeaf"},
    )


@app.get("/transparency", response_class=HTMLResponse)
async def transparency(request: Request):
    """Transparency and benchmark page."""
    # Use the real transparency template filename
    return templates.TemplateResponse(
        "whisperleaf_transparency.html",
        {"request": request},
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


async def _build_memory_context(user_message: str, query: str, limit: int = 5):
    """
    Build a RELEVANT MEMORY context block via the Tool Bus (memory.search),
    then apply memory injection guardrails to prevent "memory bleed".

    Returns (block_string, injected_snippets_list) for model context and UI visibility.
    """
    result = await tool_bus.execute(
        "memory.search",
        {"query": (query or "").strip(), "top_k": limit},
        context={},
    )
    if not result.ok or not result.data:
        return ("", [])
    candidates = result.data.get("candidates") or []

    # Backwards compatibility: some older tool results may only provide `snippets`.
    if not candidates:
        snippets = result.data.get("snippets") or []
        candidates = [{"snippet": s, "score": None} for s in snippets if s]

    injected_candidates, debug = filter_relevant_memories(user_message, candidates)

    try:
        # Internal-only logging for development/debug. Not sent to the client directly.
        print(
            "[WhisperLeaf][memory-guard] topic_reset_detected=%s explicit_recall=%s memories_retrieved=%s memories_injected=%s best_score=%s"
            % (
                debug.get("topic_reset_detected"),
                debug.get("explicit_recall_detected"),
                debug.get("memories_retrieved"),
                debug.get("memories_injected"),
                debug.get("best_relevance_score", None),
            )
        )
    except Exception:
        pass

    # Optional: record audit only when the candidate looks like it maps to DB ids.
    for c in injected_candidates or []:
        try:
            mem_id = c.get("id")
            if isinstance(mem_id, int):
                record_audit(mem_id, "used_in_context", {"route": "chat", "guard": "memory_relevance_gating"})
        except Exception:
            pass

    if not injected_candidates:
        return ("", [])

    snippets_injected = [(c.get("snippet") or "").strip() for c in injected_candidates if (c.get("snippet") or "").strip()]
    if not snippets_injected:
        return ("", [])

    block = build_memory_context_block(injected_candidates)
    if not block:
        return ("", [])
    return (block, snippets_injected)


async def _build_docs_context(query: str, limit: int = 5):
    """
    Build RELEVANT DOCUMENTS context block via docs.search.
    Returns (block_str, source_names, excerpts) for context, citation, and preview.
    excerpts: list of {"name": title, "snippet": text} per chunk (for UI preview).
    """
    def _tokenize(text: str) -> List[str]:
        # Lightweight lexical gate to avoid attaching unrelated document snippets.
        return re.findall(r"[a-z0-9]{3,}", (text or "").lower())

    stop = {
        "the", "and", "for", "with", "that", "this", "from", "into", "about",
        "your", "you", "are", "was", "were", "have", "has", "had", "what",
        "when", "where", "which", "would", "could", "should", "there", "their",
        "them", "then", "than", "just", "also", "how", "why",
    }

    query_tokens = [t for t in _tokenize(query or "") if t not in stop]
    query_set = set(query_tokens)

    def _doc_relevance(item: Dict[str, Any]) -> float:
        # Prefer vector score if available; fallback to token overlap.
        raw_score = item.get("score")
        if isinstance(raw_score, (int, float)):
            return float(raw_score)
        snippet = (item.get("snippet") or item.get("content") or "").strip()
        s_tokens = set(t for t in _tokenize(snippet) if t not in stop)
        if not query_set or not s_tokens:
            return 0.0
        overlap = len(query_set & s_tokens)
        # Normalize by query length to avoid rewarding long snippets.
        return overlap / max(1, len(query_set))

    # If docs.search provides a similarity score, this threshold expects a moderately relevant match.
    # For lexical fallback overlap, this roughly means >= 1/3 overlap on short queries.
    RELEVANCE_THRESHOLD = 0.34

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
    kept_count = 0
    dropped_count = 0
    for r in items:
        rel = _doc_relevance(r)
        if rel < RELEVANCE_THRESHOLD:
            dropped_count += 1
            continue
        title = (r.get("title") or r.get("path") or "Document").strip()
        if title and title not in seen:
            seen.add(title)
            source_names.append(title)
        snippet = (r.get("snippet") or r.get("content") or "").strip()
        if snippet:
            kept_count += 1
            lines.append("%s: %s" % (title, snippet[:400] + ("..." if len(snippet) > 400 else "")))
            # Store full snippet for preview (cap length for payload)
            excerpts.append({"name": title, "snippet": snippet[:1200] + ("..." if len(snippet) > 1200 else "")})
    if kept_count or dropped_count:
        print(
            "[WhisperLeaf][docs-relevance] query=%r kept=%s dropped=%s threshold=%.2f"
            % ((query or "")[:80], kept_count, dropped_count, RELEVANCE_THRESHOLD)
        )
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
    manual_mode_override, message_for_model = parse_mode_override(message_for_model)

    def detect_simple_query(user_message: str) -> bool:
        """
        Simple query detector.
        Triggers for:
        - basic math (e.g. 2x2, 2*2, 12/3, 5+7)
        - short definition requests ("what is X", "define X")
        - very short factual queries (1–2 tokens)

        These should return direct answers only (enforced in generation path).
        """
        m = (user_message or "").strip()
        if not m:
            return False
        lower = m.lower().strip()

        # Basic math: digits + operator, very short.
        if re.fullmatch(r"\d+\s*([xX\*\+\-\/])\s*\d+", m.strip()):
            return True

        if lower.startswith("what is ") or lower.startswith("define "):
            tail = re.sub(r"^(what is|define)\s+", "", lower).strip(" ?.")
            if 0 < len(tail.split()) <= 4:
                return True

        tokens = re.findall(r"[a-z0-9]+", lower)
        if 1 <= len(tokens) <= 2 and len(lower) <= 10:
            return True

        return False

    def detect_tradeoff_query(user_message: str) -> bool:
        """Tradeoff detector for concise comparison posture (vs/better/compare)."""
        m = (user_message or "").lower()
        return (" vs " in m) or ("vs." in m) or ("better" in m) or ("compare" in m)

    def detect_depth_intent(user_message: str) -> str:
        """
        Rule-based depth intent classifier.
        Returns: "low" | "medium" | "high"

        LOW: short/broad topic questions, no qualifiers.
        HIGH: explicit procedural/analytical qualifiers (how exactly, step-by-step, compare, pros/cons, deep dive).
        MEDIUM: everything else.
        """
        m = (user_message or "").strip().lower()
        if not m:
            return "medium"

        high_cues = (
            "how exactly",
            "step by step",
            "step-by-step",
            "why does",
            "why do",
            "compare",
            "pros and cons",
            "pros/cons",
            "deep dive",
            "in detail",
            "walk me through",
            "break down",
            "breakdown",
            "analyze",
            "diagnose",
            "troubleshoot",
            "implementation",
            "examples",
            "example",
            "procedure",
            "show me",
            "i want to know how",
        )
        if any(cue in m for cue in high_cues):
            return "high"

        # MEDIUM: explanation-style "how does/how do" requests typically want
        # more than a one-line response, even when they're short.
        if "how does" in m or "how do" in m:
            return "medium"

        # LOW: very short and broad topic intro (and no explicit high cues)
        tokens = re.findall(r"[a-z0-9]+", m)
        low_broad_patterns = (
            r"^tell me about ",
            r"^what is ",
            r"^what are ",
            r"^define ",
            r"^who is ",
            r"^where is ",
        )
        is_low_intro = any(re.search(p, m) for p in low_broad_patterns)
        if len(tokens) <= 7 and is_low_intro:
            return "low"
        return "medium"

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
        # Use the live user message for pivot/relevance detection; use rewritten query only for retrieval.
        memory_block, memory_snippets = await _build_memory_context(message_for_model, memory_query, limit=5)
    except Exception as e:
        print("[WhisperLeaf chat] memory retrieval failed (continuing without): %s" % e)
        memory_block = ""
        memory_snippets = []
    used_memory = bool(memory_block)
    # Pivot/new-topic handling: if the user clearly switched topics but we injected no relevant memory,
    # instruct the model to avoid false continuity language ("as we discussed", "pick up where we left off")
    # and to keep the follow-up calm and focused.
    topic_reset_detected = detect_topic_reset(message_for_model)
    pivot_no_memory = topic_reset_detected and not memory_snippets
    pivot_response_guidance = (
        "Pivot guidance (fresh start): The user is switching topics. "
        "Do not imply you are continuing a previous discussion on this topic "
        "(avoid phrases like 'pick up where we left off', 'as we discussed', 'back to', or 'again'). "
        "Acknowledge the switch briefly and ask exactly ONE direct follow-up question "
        "to understand what the user wants next."
        if pivot_no_memory
        else ""
    )

    depth_intent = detect_depth_intent(message_for_model)
    if depth_intent == "low":
        depth_guidance = (
            "Depth control: respond in 2–4 sentences with one clear idea. "
            "Avoid long paragraphs and long lists. "
            "Optional follow-up: if appropriate, end with 'If you want, I can go deeper into X.' "
            "Do not ask generic multi-part questions."
        )
    elif depth_intent == "high":
        depth_guidance = (
            "Depth control: respond with a clearer structure (steps/breakdown) while staying calm and not overly verbose. "
            "Prefer 3–6 short steps or a short breakdown over long blocks of text. "
            "Avoid generic buzzwords and filler. "
            "Do not dump everything at once; expand only what is needed to answer the request."
        )
    else:
        depth_guidance = (
            "Depth control: respond with 3–6 sentences. "
            "You may include one small structured element (a short list or a brief contrast). "
            "Avoid multiple questions; either no follow-up or one precise question about the next thing the user cares about."
        )

    def detect_uncertainty(user_message: str, draft_response: str = "") -> bool:
        """
        Lightweight uncertainty detection for epistemic honesty.

        For now we trigger based on user intent (system internals, training, offline/capability
        questions). `draft_response` is optional for future use.
        """
        m = (user_message or "").lower()
        draft = (draft_response or "").lower()

        internals_cues = (
            "how do you work",
            "how does it work",
            "how do you respond",
            "training",
            "trained",
            "fine-tune",
            "fine tune",
            "learned",
            "offline",
            "internet",
            "without internet",
            "knowledge graph",
            "created from scratch",
            "architecture",
            "backend",
            "sse",
            "ollama",
            "online learning",
            "do you browse",
            "can you browse",
        )
        speculative_cues = (
            "note near a device",
            "online learning",
            "knowledge graph",
            "created from scratch",
            "guaranteed",
            "definitely",
        )

        if any(cue in m for cue in internals_cues):
            return True
        if draft and any(cue in draft for cue in speculative_cues):
            return True
        return False

    def build_epistemic_honesty_guidance(user_message: str) -> str:
        m = (user_message or "").lower()
        training_q = any(cue in m for cue in ("training", "trained", "fine-tune", "fine tune", "learned", "created from scratch"))
        offline_q = any(cue in m for cue in ("offline", "internet", "without internet", "do you browse", "can you browse"))
        # Generic capability boundary for internals/capability questions.
        unknown_q = not (training_q or offline_q)

        if training_q:
            return (
                "Epistemic honesty (training/internal question): "
                "Do not describe your training process, data, or internal architecture as if you know it. "
                "If asked about how you were trained or what you learned, explain the limitation plainly: "
                "you generate responses from patterns and the current conversation context, and you do not have access "
                "to your own training pipeline or environment details. "
                "If you are uncertain, say you don't know and offer a safe high-level explanation instead."
            )
        if offline_q:
            return (
                "Epistemic honesty (offline/capabilities question): "
                "If the user asks about offline usage, clarify what is and isn't possible: "
                "WhisperLeaf can use a local model when available, but it cannot rely on online lookups/browsing. "
                "It does not update its core model in real time; it responds based on patterns and the current context. "
                "If you are unsure whether a local model is running, say so and suggest checking the local model service."
            )
        if unknown_q:
            return (
                "Epistemic honesty (capability boundary): "
                "If you are not certain you can perform a task or access information, do not invent mechanisms. "
                "State the limit (e.g., 'I don't have a way to do that right now') and offer a safe alternative: "
                "help with steps, a conceptual explanation, or using available local features (documents/memories) when applicable."
            )
        return ""

    honesty_guidance = ""
    if detect_uncertainty(message_for_model):
        honesty_guidance = build_epistemic_honesty_guidance(message_for_model)

    # Response mode: conversational / creative / task-dev (engineering artifact) — see mode_router.py
    response_mode = manual_mode_override or detect_mode(message_for_model)
    if manual_mode_override is None and is_general_capability_meta_query(message_for_model):
        response_mode = ResponseMode.CONVERSATIONAL
    mode_source = "manual" if manual_mode_override is not None else "auto"
    # TODO(debug): include response_mode/mode_source in SSE metadata behind a debug flag.
    print(
        "[WhisperLeaf mode] %s (%s) | %s"
        % (response_mode.value, mode_source, explain_mode_choice(message_for_model)),
    )

    # LeafLink paste (early: explanation follow-up rules + dual-mode / Capture Mode below).
    _leaflink_capture_message = is_leaflink_originated_message(message_for_model)

    # Hard ban list for fabricated internal mechanism language.
    # This is instruction-only (prompt guidance), not a behavior rewrite.
    banned_internal_phrases = (
        "knowledge graph",
        "online learning",
        "internalized graph",
        "custom reasoning engine",
        "self-updating model",
        "self updating model",
        "self-updating",
        "self updating",
    )
    capability_hard_ban_guidance = (
        "Capability honesty: Do NOT claim or reference unverified internal mechanisms. "
        "Avoid these phrases entirely: "
        + ", ".join("'" + p + "'" for p in banned_internal_phrases)
        + ". "
        "When discussing capabilities, use only grounded terms that match the app: "
        "'current conversation context', 'stored memory snippets' (only if present), 'model training', 'local model'."
    )

    def detect_insight_opportunity(user_message: str) -> bool:
        """
        Selective insight injection trigger.
        - Never triggers in execution mode.
        - Triggers only on: why / tradeoff / compare / better / vs / pattern
        """
        m = (user_message or "").strip().lower()
        if not m:
            return False
        if response_mode in (ResponseMode.TASK_DEV, ResponseMode.CREATIVE):
            return False
        if honesty_guidance:
            return False

        cues = ("why", "tradeoff", "trade-off", "compare", "better", " vs ", "vs.", "pattern")
        return any(c in m for c in cues)

    insight_guidance = ""
    # Response style guardrails (localized per-request guidance).
    # Identity + WhisperLeaf Voice Specification: prompts/system.md; per-turn reinforcement below.
    previous_assistant_turns = sum(1 for m in (payload.history or []) if getattr(m, "role", None) == "assistant")
    wants_follow_up_question = (previous_assistant_turns % 2) == 1
    depth_level = select_depth_escalation_level(
        message_for_model,
        topic_reset_detected=topic_reset_detected,
        previous_assistant_turns=previous_assistant_turns,
        response_mode=response_mode,
        leaflink=_leaflink_capture_message,
    )
    if depth_level is not None:
        depth_guidance = (
            depth_guidance + "\n\n" + build_depth_escalation_guidance(depth_level)
        ).strip()
    confidence_level = select_confidence_level(
        message_for_model,
        has_honesty_guidance=bool(honesty_guidance),
        is_simple_query=detect_simple_query(message_for_model),
        response_mode=response_mode,
        leaflink=_leaflink_capture_message,
    )
    if confidence_level is not None:
        depth_guidance = (
            depth_guidance + "\n\n" + build_confidence_guidance(confidence_level)
        ).strip()
    _explanation_follow_turn = (
        hits_explanation_intent(message_for_model)
        and not _leaflink_capture_message
        and response_mode not in (ResponseMode.TASK_DEV, ResponseMode.CREATIVE)
    )
    if _explanation_follow_turn:
        if depth_level is not None and depth_level >= 2:
            follow_up_guidance_line = (
                "Explanation thread: **Depth escalation Level %d** applies—**do not** invite the user to go deeper; "
                "they already signaled curiosity or requested depth."
                % depth_level
            )
        elif depth_level == 1:
            follow_up_guidance_line = (
                "Explanation thread: follow **Depth escalation (Level 1)**—**at most one** short optional invitation to go deeper; "
                "low-pressure, no stacked options or multiple questions."
            )
        elif depth_intent == "low":
            follow_up_guidance_line = (
                "This is an explanation-style question: give a **short, clear, plain-language** answer first—"
                "**clarity over completeness**; do not front-load detail or sound like a textbook unless asked. "
                "You may end with **at most one** short, optional, low-pressure invitation to go deeper "
                "(e.g. \"I can go deeper into how it works if you want.\" / \"I can break down the parts one by one if that's useful.\" "
                "/ \"I can go deeper into the science or keep it plain-language.\")—or omit if it feels redundant. "
                "Do **not** stack multiple follow-ups or questions."
            )
        elif depth_intent == "high":
            follow_up_guidance_line = (
                "This is an explanation-style question: still open with a **compact gist**, then give the depth the user asked for. "
                "Optionally add **at most one** short invitation if more detail might still help—never multiple stacked prompts."
            )
        else:
            follow_up_guidance_line = (
                "This is an explanation-style question: start **simple and grounded**; avoid dumping everything upfront. "
                "After the main answer, you may add **at most one** short optional line inviting depth—calm and natural, not a script. "
                "Do not stack follow-ups."
            )
    elif depth_intent == "low":
        follow_up_guidance_line = (
            "End with either no follow-up or an optional offer to go deeper (no question)."
        )
    else:
        follow_up_guidance_line = (
            "End with exactly ONE optional follow-up question."
            if wants_follow_up_question
            else "End with a statement (no question)."
        )
    response_style_guidance = (
        WHISPERLEAF_VOICE_SPEC_LAYER
        + "\n\n"
        "Response structure: put the practical answer in the first sentence when the user wants steps, tools, health choices, or “what should I do”—no essay lead-in. "
        "Use short bullets for multiple options; keep explanations brief and action-tied. "
        "Avoid generic buzzwords and filler; when the user is discussing a domain, prefer 1–2 concrete, mechanism-level details over vague categories. "
        "Follow-up behavior: do not always end with a question. "
        + follow_up_guidance_line
        + " "
        "Use the optional-depth pattern **mainly** for explanation / information questions—not when the user needs urgent practical steps first. "
        "Do not use salesy enthusiasm. "
        "If pivot-specific guidance is present, follow that guidance for phrasing/follow-ups."
    )
    doc_block = ""
    doc_sources: List[str] = []
    doc_excerpts: List[Dict[str, str]] = []
    try:
        doc_block, doc_sources, doc_excerpts = await _build_docs_context(memory_query, limit=5)
    except Exception as e:
        print("[WhisperLeaf chat] docs context failed (continuing without): %s" % e)

    def detect_user_context_signals(injected_memory_snippets: List[str]) -> Dict[str, Any]:
        """
        Extract soft preference signals from injected memory/doc context.
        This is intentionally heuristic and privacy-safe: we only infer general interests,
        and we never expose past behavior/history to the user.
        """
        joined = " ".join(injected_memory_snippets or []).lower()

        interests: List[str] = []
        def _has(*words: str) -> bool:
            return all(w in joined for w in words)
        def _any(*words: str) -> bool:
            return any(w in joined for w in words)

        # Local/offline/privacy interest
        if _any("local", "offline", "private", "privacy", "sovereign", "document", "documents"):
            interests.append("local/offline privacy")

        # Building/engineering interest (documents, tools, benchmarks, measuring)
        if _any("build", "bench", "energy", "benchmark", "measure", "tool", "document", "chunks"):
            interests.append("building and benchmarking")

        # Memory/knowing-what-matters interest
        if _any("memory", "memories", "remember"):
            interests.append("memory-aware chats")

        interests = interests[:3]

        # Style cue (very soft): inferred from user's depth intent.
        if depth_intent == "low":
            style = "concise"
        elif depth_intent == "high":
            style = "structured"
        else:
            style = "balanced"

        return {
            "interests": interests,
            "style": style,
        }

    def detect_personalization_opportunity(
        user_message: str,
        context_signals: Dict[str, Any],
        topic_reset_detected: bool,
    ) -> bool:
        """
        Decide whether to add ONE subtle contextual adjustment.

        Rules:
        - never personalize for simple factual definition questions
        - never personalize when pivot reset detected but no relevant injected memory exists
        - overlap must be clear (avoid creepy guessing)
        """
        m = (user_message or "").lower().strip()
        if not m:
            return False

        # Don't personalize for simple definitions/facts.
        if any(p in m for p in ("what is ", "what are ", "define ", "who is ", "where is ", "2+2", "3+3")):
            return False

        if honesty_guidance:
            return False

        if topic_reset_detected and not memory_snippets:
            return False

        interests = context_signals.get("interests") or []
        if not interests:
            return False

        # Clear overlap checks based on interest category keywords.
        interest_hits = False
        if "local/offline privacy" in interests and any(w in m for w in ("local", "offline", "privacy", "private", "sovereign", "documents")):
            interest_hits = True
        if "building and benchmarking" in interests and any(w in m for w in ("build", "benchmark", "bench", "energy", "measure", "documents", "chunks", "system")):
            interest_hits = True
        if "memory-aware chats" in interests and any(w in m for w in ("memory", "memories", "remember", "context", "sources")):
            interest_hits = True

        # Allow reflective phrasing that invites tailoring.
        reflective_hits = any(w in m for w in ("in your case", "in my case", "for what i'm building", "for what i'm working on", "i'm building", "i'm working on"))
        return interest_hits or reflective_hits

    personalization_guidance = ""
    context_signals = detect_user_context_signals(memory_snippets)
    if response_mode != ResponseMode.CREATIVE and detect_personalization_opportunity(
        message_for_model, context_signals, topic_reset_detected
    ):
        interest_topic = (context_signals.get("interests") or [None])[0]
        if interest_topic:
            personalization_guidance = (
                "Lightweight personalization: If it fits naturally, append ONE short sentence AFTER your main answer "
                "that softly ties the guidance to the user's apparent focus (e.g., 'In your case, especially given your focus on local/offline privacy…'). "
                "Use cautious language (may/especially/if). Do not sound like surveillance, do not mention history, "
                "and do not add extra questions."
            )

    # user_mode shapes prompts; "execution" is reserved for TASK_DEV (structured engineering output only).
    if manual_mode_override is None and is_general_capability_meta_query(message_for_model):
        user_mode = "learning"
    elif response_mode == ResponseMode.TASK_DEV:
        user_mode = "execution"
    elif response_mode == ResponseMode.CREATIVE:
        user_mode = "creative"
    else:
        user_mode = conversational_posture(message_for_model)

    # Bypass optional layers for task-dev artifacts and direct creative output.
    if user_mode == "execution":
        personalization_guidance = ""
        insight_guidance = ""
    elif user_mode == "creative":
        personalization_guidance = ""

    def validate_execution_output(text: str) -> Dict[str, Any]:
        """
        Lightweight post-generation validator for execution artifacts.
        Returns: { ok: bool, issues: [str] }

        Requirements:
        - artifact-only (no intro/outro prose)
        - includes required sections
        - references at least one real WhisperLeaf component
        - avoids common generic/explanatory phrases
        """
        t = (text or "").strip()
        issues: List[str] = []
        if not t:
            return {"ok": False, "issues": ["empty_output"]}

        lower = t.lower()
        banned_explanations = (
            "this prompt",
            "this guides",
            "you can use",
            "for example",
            "for instance",
        )
        if any(p in lower for p in banned_explanations):
            issues.append("contains_explanatory_phrases")

        # Structure checks (must be present)
        required_headers = ("objective", "requirements", "files/functions", "tests")
        if not all(h in lower for h in required_headers):
            issues.append("missing_required_sections")

        real_components = (
            "src/core/main.py",
            "src/core/tools/memory_search_tool.py",
            "src/core/memory_injection_guard.py",
            "tests/test_memory_bleed_guard.py",
        )
        if not any(p.lower() in lower for p in real_components):
            issues.append("missing_real_component_references")

        generic_smells = (
            "placeholder",
            "keyword filtering",
            "filter keywords",
            "some function",
            "some file",
        )
        if any(p in lower for p in generic_smells):
            issues.append("generic_or_placeholder_logic")

        return {"ok": len(issues) == 0, "issues": issues}

    def strip_to_execution_artifact(text: str) -> str:
        """
        Best-effort cleanup: return only the artifact, starting at Objective.
        Removes obvious explanation lines outside required sections.
        """
        t = (text or "").strip()
        if not t:
            return ""
        lines = t.splitlines()
        start = 0
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("objective"):
                start = i
                break
        core = "\n".join(lines[start:]).strip()
        # Remove a few common explanatory lead-ins if they slipped inside.
        cleaned_lines = []
        for line in core.splitlines():
            l = line.strip().lower()
            if any(p in l for p in ("this prompt", "this guides", "you can use", "for example")):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()

    def trim_execution_artifact(text: str) -> str:
        """
        Tighten execution artifacts to feel senior-engineer crisp:
        - remove filler phrases
        - cap list sizes (Requirements <= 6, Tests <= 4)
        - avoid redundancy by keeping only the most concrete lines
        Preserves strict section structure.
        """
        t = strip_to_execution_artifact(text or "")
        if not t:
            return ""

        filler_phrases = (
            "ensure that",
            "make sure to",
            "you should",
            "consider",
            "this prompt",
            "this guides",
        )

        lines = [ln.rstrip() for ln in t.splitlines()]
        out: List[str] = []
        section = None
        req_count = 0
        test_count = 0

        def _is_header(line: str) -> bool:
            s = line.strip().lower()
            return s.startswith("objective") or s.startswith("requirements") or s.startswith("files/functions") or s.startswith("tests")

        def _clean_line(line: str) -> str:
            s = line
            low = s.lower()
            for fp in filler_phrases:
                if fp in low:
                    # drop the whole line if it's mostly filler
                    if len(s.strip()) <= len(fp) + 12:
                        return ""
                    # otherwise remove phrase
                    s = re.sub(re.escape(fp), "", s, flags=re.IGNORECASE).strip()
                    low = s.lower()
            # tighten common verbose patterns
            s = s.replace("Add a function that will", "Add")
            s = s.replace("Add a function that", "Add")
            s = s.replace("Make sure to include", "Include")
            return s.strip()

        for ln in lines:
            if not ln.strip():
                # keep single blank lines between sections
                if out and out[-1] != "":
                    out.append("")
                continue

            if _is_header(ln):
                section = ln.strip().split(":")[0].strip().lower()
                out.append(ln.strip())
                continue

            cleaned = _clean_line(ln)
            if not cleaned:
                continue

            low = cleaned.lower()
            if section == "requirements":
                # cap 6 items; keep numbered/bulleted lines only
                if low.startswith(("-", "*")) or re.match(r"^\d+[\).\s]", cleaned):
                    req_count += 1
                    if req_count <= 6:
                        out.append(cleaned)
                else:
                    # compress prose into a single bullet when possible
                    req_count += 1
                    if req_count <= 6:
                        out.append("- " + cleaned)
                continue

            if section == "tests":
                if low.startswith(("-", "*")) or re.match(r"^\d+[\).\s]", cleaned) or low.startswith("tests:"):
                    test_count += 1
                    if test_count <= 4:
                        out.append(cleaned)
                else:
                    test_count += 1
                    if test_count <= 4:
                        out.append("- " + cleaned)
                continue

            # Objective and Files/Functions: keep short, concrete lines
            out.append(cleaned)

        # Remove trailing blank lines
        while out and out[-1] == "":
            out.pop()
        return "\n".join(out).strip()

    # LeafLink: detected earlier for follow-up rules; same flag for insight gating + Capture Mode below.

    if not _leaflink_capture_message and detect_insight_opportunity(message_for_model):
        # Selective insight injection: one sentence, high-signal; off for task-dev and creative modes.
        # Skipped for LeafLink captures — Capture Mode handles end framing without extra "insight" sentences.
        # If personalization is also active, merge into the same single sentence.
        if personalization_guidance:
            insight_guidance = (
                "Selective insight (merged): After your main answer, add ONE short sentence (15–20 words) "
                "that combines either a tradeoff/pattern/implication with a soft 'in your case' tie-in. "
                "It must add new information (not restate), avoid fluff, avoid vague generalities, and must not be a question. "
                "If you can't add something genuinely new, omit the sentence."
            )
            personalization_guidance = ""
        else:
            insight_guidance = (
                "Selective insight: After your main answer, optionally add ONE short sentence (15–20 words). "
                "It must be a pattern, tradeoff, or hidden implication directly tied to the question. "
                "No motivational fluff, no obvious restatement, no vague generalities, and not a question. "
                "Validator: if it adds no new information, omit it."
            )

    _anti_spec = anti_engineering_scaffolding_instruction()
    mode_guidance = ""
    if user_mode == "execution" and engineering_scaffolding_allowed(response_mode):
        mode_guidance = (
            "Mode shaping: respond in an execution posture. Be concise and actionable. "
            "Direct-artifact rule: if the user asks for a prompt, command, code, checklist, or steps, "
            "output that artifact FIRST (as the first content block) with minimal preamble. "
            "Execution quality bar: the artifact must be system-aware and match WhisperLeaf's actual codebase. "
            "Do NOT use placeholder logic or arbitrary examples. "
            "Do NOT include an explanation layer (no prose outside the artifact) unless the user explicitly asks. "
            "Structure enforcement: include Objective, Requirements, Files/components to modify (use real paths), "
            "Concrete changes (functions/branches), and Tests to add/run. "
            "When relevant to this app, reference these real components: "
            "src/core/main.py (chat prompt assembly + SSE meta), "
            "src/core/tools/memory_search_tool.py (memory.search candidates), "
            "src/core/memory_injection_guard.py (pivot detection, relevance thresholds, blocked categories, caps), "
            "tests/test_memory_bleed_guard.py (guard tests). "
            "Quality check: before finalizing, verify the artifact mentions the correct files/functions/thresholds; "
            "if it is generic, rewrite silently to be specific and aligned, then output only the final artifact."
        )
    elif user_mode == "creative":
        mode_guidance = (
            "Mode shaping: creative request. Produce the creative output directly (poem, story, lyrics, names, etc.). "
            + _anti_spec
            + " "
            "Do not wrap the answer in software planning sections or a task checklist."
        )
    elif user_mode == "strategy":
        mode_guidance = (
            "Mode shaping: respond in a strategy posture. Present 2–3 options and the key tradeoff(s). "
            + _anti_spec
            + " "
            "Call out one implication. Keep it calm and not verbose."
        )
    else:
        mode_guidance = (
            "Mode shaping: conversational answer. Be natural and directly helpful. "
            + _anti_spec
            + " "
            "Give a clear explanation with a simple mental model when teaching; keep it grounded and concise."
        )

    # InsightBox (mode-aware framing guidance). Additive only; does not replace any existing behavior.
    try:
        insight_box_guidance = build_mode_guidance(response_mode)
        if insight_box_guidance:
            mode_guidance = (mode_guidance + "\n\n" + insight_box_guidance).strip()
    except Exception:
        # Guidance must never break chat request handling.
        pass

    # Dual Mode System: Structure vs Reflect (prompt shaping only).
    # LeafLink → structure (reuses Capture Mode v2 via build_dual_mode_guidance).
    # Practical / health / tools / “what should I do” → structure (dual_mode._hits_practical_action_first).
    # Document context → reflect by default unless structure forced by keywords or practical triggers.
    # Skipped for execution/creative posture.
    # Future: Builder Mode, Research Mode, or explicit client `response_shape`.
    _has_document_context = bool(doc_block and doc_block.strip())
    _response_shape_mode = None
    if user_mode not in ("execution", "creative"):
        _response_shape_mode = select_response_shape_mode(
            message_for_model,
            is_leaflink=_leaflink_capture_message,
            has_document_context=_has_document_context,
        )
    if _response_shape_mode:
        mode_guidance = (
            mode_guidance
            + "\n\n"
            + build_dual_mode_guidance(
                _response_shape_mode,
                {"leaflink": _leaflink_capture_message},
            )
        ).strip()

    user_facing_privacy_guidance = ""
    if user_mode != "execution" and not allows_internal_codebase_context(message_for_model):
        user_facing_privacy_guidance = (
            "User-facing boundary: Do not mention WhisperLeaf internal file paths (e.g. src/core/), "
            "specific .py paths in this repo, internal modules, system prompts, internal tool names, "
            "or non-public architecture. Do not repeat such details from retrieved context. "
            "Answer with portable examples and general software concepts unless the user explicitly "
            "asks about WhisperLeaf's codebase or system design."
        )

    if memory_block or doc_block:
        note = "Note: You may use the context below to answer.\n\n"
        parts = [note]
        if pivot_response_guidance:
            parts.insert(0, pivot_response_guidance)
        if response_style_guidance:
            parts.insert(0, response_style_guidance)
        if depth_guidance:
            parts.insert(0, depth_guidance)
        if honesty_guidance:
            parts.insert(0, honesty_guidance)
        # Hard ban applies for execution mode and for explicit capability/internal questions.
        if user_mode == "execution" or honesty_guidance:
            parts.insert(0, capability_hard_ban_guidance)
        if insight_guidance:
            parts.insert(0, insight_guidance)
        if personalization_guidance:
            parts.insert(0, personalization_guidance)
        if mode_guidance:
            # Final shaping layer: influences posture without announcing a "mode".
            parts.insert(0, mode_guidance)
        if user_facing_privacy_guidance:
            parts.insert(0, user_facing_privacy_guidance)
        if memory_block:
            parts.append(memory_block)
        if doc_block:
            parts.append(doc_block)
        user_content = "\n\n".join(parts) + "\n\nUser message:\n" + message_for_model
    else:
        if pivot_response_guidance or response_style_guidance:
            prefix_parts = []
            if pivot_response_guidance:
                prefix_parts.append(pivot_response_guidance)
            if response_style_guidance:
                prefix_parts.append(response_style_guidance)
            if depth_guidance:
                prefix_parts.append(depth_guidance)
            if honesty_guidance:
                prefix_parts.append(honesty_guidance)
            if user_mode == "execution" or honesty_guidance:
                prefix_parts.append(capability_hard_ban_guidance)
            if mode_guidance:
                prefix_parts.append(mode_guidance)
            if user_facing_privacy_guidance:
                prefix_parts.insert(0, user_facing_privacy_guidance)
            user_content = "\n\n".join(prefix_parts) + "\n\nUser message:\n" + message_for_model
        else:
            if mode_guidance and depth_guidance:
                _layers = [user_facing_privacy_guidance, mode_guidance, depth_guidance]
                user_content = "\n\n".join(x for x in _layers if x) + "\n\nUser message:\n" + message_for_model
            elif mode_guidance:
                if user_mode == "execution":
                    user_content = (
                        mode_guidance + "\n\n" + capability_hard_ban_guidance + "\n\nUser message:\n" + message_for_model
                    )
                else:
                    _layers = [user_facing_privacy_guidance, mode_guidance]
                    user_content = "\n\n".join(x for x in _layers if x) + "\n\nUser message:\n" + message_for_model
            else:
                if depth_guidance:
                    _layers = [user_facing_privacy_guidance, depth_guidance]
                    user_content = "\n\n".join(x for x in _layers if x) + "\n\nUser message:\n" + message_for_model
                elif user_facing_privacy_guidance:
                    user_content = user_facing_privacy_guidance + "\n\nUser message:\n" + message_for_model
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
    if DEVELOPER_MODE:
        effective_system += (
            "\n\n---\nDeveloper mode is enabled on this server: you may discuss WhisperLeaf's internal "
            "architecture, repository paths, modules, and implementation details when relevant.\n"
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
                simple_query = detect_simple_query(message_for_model)
                tradeoff_query = detect_tradeoff_query(message_for_model)
                # Creative output is often multi-line; do not force simple/tradeoff validators on it.
                if response_mode == ResponseMode.CREATIVE:
                    simple_query = False
                    tradeoff_query = False

                def _count_sentences(s: str) -> int:
                    return len(re.findall(r"[.!?]+", (s or "").strip()))

                def _contains_teaching(s: str) -> bool:
                    low = (s or "").lower()
                    return any(p in low for p in ("can be thought of as", "this means", "in this case"))

                def _validate_simple_reply(s: str) -> bool:
                    t = (s or "").strip()
                    if not t:
                        return False
                    if _contains_teaching(t):
                        return False
                    # Direct answer only (single sentence/line).
                    if _count_sentences(t) > 1:
                        return False
                    if "\n" in t:
                        return False
                    return True

                def _validate_tradeoff_reply(s: str) -> bool:
                    t = (s or "").strip()
                    if not t:
                        return False
                    # Max 3 sentences total (2-line main + 1 insight).
                    if _count_sentences(t) > 3:
                        return False
                    lines = [ln for ln in t.splitlines() if ln.strip()]
                    if len(lines) > 3:
                        return False
                    if len(lines) < 2:
                        return False
                    # Teaching language only allowed if user asked why/how.
                    if not any(w in (message_for_model or "").lower() for w in ("why", "how")) and _contains_teaching(t):
                        return False
                    # Require an insight line for tradeoff triggers.
                    if len(lines) < 3:
                        return False
                    return True

                # Simple/tradeoff enforcement: buffered generation + one rewrite pass.
                if simple_query or tradeoff_query:
                    reply = await model_client.chat(effective_system, messages)
                    reply = (reply or "").strip()
                    ok = _validate_simple_reply(reply) if simple_query else _validate_tradeoff_reply(reply)
                    if not ok:
                        if simple_query:
                            rewrite_instructions = (
                                "Rewrite to comply exactly:\n"
                                "- Output ONLY the direct answer.\n"
                                "- No explanation, no teaching ('this means', 'can be thought of as', 'in this case').\n"
                                "- No insight sentence.\n"
                                "- One line only.\n\n"
                                "Original:\n"
                            )
                        else:
                            rewrite_instructions = (
                                "Rewrite to comply exactly:\n"
                                "- Line 1–2: main answer (max two short lines).\n"
                                "- Line 3: ONE insight sentence (15–20 words) stating a tradeoff/pattern/implication.\n"
                                "- Total <= 3 sentences.\n"
                                "- No teaching language unless the user asked 'why' or 'how'.\n"
                                "- No questions.\n\n"
                                "Original:\n"
                            )
                        rewrite_messages = messages + [{"role": "user", "content": rewrite_instructions + reply}]
                        reply2 = await model_client.chat(effective_system, rewrite_messages)
                        reply2 = (reply2 or "").strip()
                        ok2 = _validate_simple_reply(reply2) if simple_query else _validate_tradeoff_reply(reply2)
                        reply = reply2 if ok2 else reply
                    if user_mode != "execution" and not allows_internal_codebase_context(message_for_model):
                        if response_contains_internal_leak(reply):
                            reply = await rewrite_reply_without_internals(model_client, reply)
                    full_reply = reply
                    yield _sse_message("chunk", full_reply)
                    yield _sse_message("done", "")
                    if session_id and session_id in CHAT_SESSIONS:
                        CHAT_SESSIONS[session_id].append({"role": "assistant", "content": full_reply})
                    return

                # Execution-mode stabilization: generate full artifact, validate, optionally rewrite once.
                if user_mode == "execution":
                    reply = await model_client.chat(effective_system, messages)
                    reply = (reply or "").strip()
                    v1 = validate_execution_output(reply)
                    if not v1.get("ok"):
                        # One internal rewrite pass (no extra user-visible text).
                        rewrite_instructions = (
                            "Rewrite the output to comply EXACTLY with the required execution artifact format:\n"
                            "- Objective (1 line)\n"
                            "- Requirements (numbered)\n"
                            "- Files/Functions to update\n"
                            "- Tests\n"
                            "No intro/outro prose. Must reference at least one real component path.\n"
                            "Brevity: keep each section minimal; Requirements <= 6 items; Tests <= 4 items.\n"
                            "Avoid filler phrases: 'ensure that', 'make sure to', 'you should', 'consider'.\n"
                            "Avoid phrases: 'this prompt', 'you can use', 'for example'.\n\n"
                            "Original output:\n"
                        )
                        rewrite_messages = messages + [{"role": "user", "content": rewrite_instructions + reply}]
                        reply2 = await model_client.chat(effective_system, rewrite_messages)
                        reply2 = (reply2 or "").strip()
                        v2 = validate_execution_output(reply2)
                        if v2.get("ok"):
                            reply = reply2
                        else:
                            reply = strip_to_execution_artifact(reply2 or reply)
                    full_reply = trim_execution_artifact(reply)
                    yield _sse_message("chunk", full_reply)
                    yield _sse_message("done", "")
                    if session_id and session_id in CHAT_SESSIONS:
                        CHAT_SESSIONS[session_id].append({"role": "assistant", "content": full_reply})
                    return

                chunk_count = 0
                # Emit a status event before we call the local model so the client can show
                # a warmup indicator even if the first token takes a while.
                try:
                    yield _sse_message(
                        "status",
                        json.dumps(
                            {
                                "step": "model_start",
                                "model": model_client.model_name,
                                "endpoint": model_client.base_url,
                            }
                        ),
                    )
                except Exception:
                    pass
                # Stream chunks to the client as they arrive.
                # Note: we still apply internal-leak rewriting to the final stored reply when needed,
                # but we do not buffer the entire response before emitting any content (avoids long silence/timeouts).
                async for chunk in model_client.chat_stream(effective_system, messages):
                    full_reply += chunk
                    chunk_count += 1
                    if chunk_count == 1:
                        print("[WhisperLeaf chat] first chunk received len=%s" % len(chunk))
                    yield _sse_message("chunk", chunk)
                if user_mode != "execution" and not allows_internal_codebase_context(message_for_model):
                    if response_contains_internal_leak(full_reply):
                        print("[WhisperLeaf chat] internal leak detected; rewriting stored reply")
                        full_reply = await rewrite_reply_without_internals(model_client, full_reply)
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


class DevModeBody(BaseModel):
    enabled: bool


@app.get("/api/dev-mode")
def get_dev_mode():
    return {"developer_mode": DEVELOPER_MODE}


@app.post("/api/dev-mode")
def set_dev_mode(body: DevModeBody):
    global DEVELOPER_MODE
    DEVELOPER_MODE = body.enabled
    return {"developer_mode": DEVELOPER_MODE}


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