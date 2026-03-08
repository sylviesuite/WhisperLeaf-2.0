"""
Main FastAPI application for Sovereign AI / WhisperLeaf.
"""

from pathlib import Path
import json
import os
import re
import tempfile
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
    search_memories_by_query,
    set_visibility as memory_set_visibility,
    get_audit_events,
    get_memory,
    record_audit,
    VISIBILITY_VALUES,
)
from .tools_registry import register_tool, list_tools, call_tool

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
    SYSTEM_PROMPT = "You are WhisperLeaf, a privacy-first local AI assistant."

# Local model client (Ollama / local LLM server)
model_client = LocalModelClient()

# Data / memory dirs
DATA_DIR = PROJECT_ROOT / "data"
memory_manager = MemoryManager(data_dir=str(DATA_DIR))
memory_search = MemorySearch(data_dir=str(DATA_DIR), memory_manager=memory_manager)
vault_manager = VaultManager()
vector_store = VectorStore()
document_processor = DocumentProcessor()


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
# Basic routes: status, home, chat UI
# -------------------------------------------------------------------

@app.get("/api/status")
async def api_status():
    """Simple status endpoint (former JSON root)."""
    return {"message": "Sovereign AI API", "version": "1.0.0"}


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
CHAT_SESSIONS: Dict[str, List[Dict[str, str]]] = {}

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


def _build_memory_context(query: str, limit: int = 5) -> str:
    """
    Build a RELEVANT MEMORY context block for the model. Tries semantic search (MemorySearch),
    then keyword search over simple memory (memory.search_memories_by_query), then recency fallback.
    Returns empty string if no memories. Records used_in_context for simple-memory entries.
    """
    snippets: List[str] = []
    entries_for_audit: List[Dict[str, Any]] = []

    try:
        results = memory_search.semantic_search(
            query=(query or "").strip(),
            limit=limit,
            privacy_level=PrivacyLevel.PRIVATE,
        )
        if results:
            for entry, _ in results:
                content = (getattr(entry, "content", None) or "").strip()
                if content:
                    snippets.append(content[:400] + ("..." if len(content) > 400 else ""))
    except Exception:
        pass

    if not snippets:
        try:
            entries_for_audit = search_memories_by_query(
                (query or "").strip(), limit=limit, exclude_blocked=True
            )
            if entries_for_audit:
                for e in entries_for_audit:
                    content = (e.get("content") or "").strip()
                    if content:
                        snippets.append(content[:400] + ("..." if len(content) > 400 else ""))
        except Exception:
            entries_for_audit = []

    if not snippets:
        entries_for_audit = get_recent_memory_entries(limit=limit, exclude_blocked=True)
        snippets = [
            (e.get("content") or "").strip()[:400]
            + ("..." if len((e.get("content") or "")) > 400 else "")
            for e in entries_for_audit
            if (e.get("content") or "").strip()
        ]

    for e in entries_for_audit:
        try:
            record_audit(e["id"], "used_in_context", {"route": "chat"})
        except Exception:
            pass

    if not snippets:
        return ""
    return "RELEVANT MEMORY:\n" + "\n".join("- " + s for s in snippets)


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """
    Chat endpoint: streams assistant reply as SSE. Conversation state is
    managed on the client. Supports "remember: ..." and "no memory: ...".
    """
    raw_message = (payload.message or "").strip()

    # "remember: ..." always stores and returns short reply
    if raw_message.lower().startswith("remember:"):
        text = raw_message[9:].strip()
        if text:
            save_memory(text, source="chat")
        reply = "I've remembered that."
        sid = getattr(payload, "session_id", None)
        if sid:
            session_list = [{"role": m.role, "content": m.content} for m in payload.history]
            session_list.append({"role": "user", "content": raw_message})
            session_list.append({"role": "assistant", "content": reply})
            CHAT_SESSIONS[sid] = session_list

        async def remember_stream() -> Any:
            yield _sse_message("chunk", reply)
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
    if not no_memory and message_for_model and _should_auto_save_memory(message_for_model):
        clean = message_for_model.strip()
        if not _looks_sensitive(clean):
            save_memory(clean)
            snippet = clean[:80] + ("..." if len(clean) > 80 else "")
            print(f"Auto-saved memory: {snippet}")

    # Build messages with semantic/keyword memory context when available
    messages = [{"role": m.role, "content": m.content} for m in payload.history]
    memory_block = _build_memory_context(message_for_model, limit=5)
    used_memory = bool(memory_block)
    if memory_block:
        note = "Note: You may use the relevant memory context below to answer consistently.\n\n"
        user_content = note + memory_block + "\n\nUser message:\n" + message_for_model
    else:
        user_content = message_for_model
    messages.append({"role": "user", "content": user_content})

    session_id = getattr(payload, "session_id", None)
    if session_id:
        session_list = [{"role": m.role, "content": m.content} for m in payload.history]
        session_list.append({"role": "user", "content": raw_message})
        CHAT_SESSIONS[session_id] = session_list

    async def generate() -> Any:
        full_reply = ""
        if used_memory:
            meta = json.dumps({"used_memory": True, "memory_count": max(1, memory_block.count("- "))})
            yield _sse_message("meta", meta)
        try:
            async for chunk in model_client.chat_stream(SYSTEM_PROMPT, messages):
                full_reply += chunk
                yield _sse_message("chunk", chunk)
            yield _sse_message("done", "")
            if session_id and session_id in CHAT_SESSIONS:
                CHAT_SESSIONS[session_id].append({"role": "assistant", "content": full_reply})
        except httpx.ConnectError:
            yield _sse_message(
                "error",
                "WhisperLeaf cannot reach the local model server. "
                "Please start Ollama (or your local LLM server) and try again.",
            )
        except httpx.HTTPStatusError as e:
            yield _sse_message("error", f"Local model error: {e!s}")
        except Exception as e:
            yield _sse_message("error", f"Unexpected error: {e!s}")

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
    """Clear persisted history for the given session."""
    if body.session_id:
        CHAT_SESSIONS.pop(body.session_id, None)
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