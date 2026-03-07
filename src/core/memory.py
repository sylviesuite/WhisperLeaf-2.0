"""
Simple SQLite-backed memory store for WhisperLeaf.
Stores and recalls notes between sessions. Local file only; no cloud.
Includes visibility, source, and audit log for the Trust Layer.
"""

from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

_DB_PATH: str | None = None

# Visibility: normal, private, pinned, blocked. Blocked never returned.
VISIBILITY_VALUES = ("normal", "private", "pinned", "blocked")
AUDIT_EVENT_TYPES = (
    "created",
    "searched",
    "used_in_context",
    "updated",
    "deleted",
    "blocked",
    "unblocked",
    "pinned",
    "unpinned",
)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'normal',
    source TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS memory_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    meta_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
)
"""


def _migrate_add_columns(conn: sqlite3.Connection) -> None:
    """Add new columns if they do not exist (SQLite has no IF NOT EXISTS for columns)."""
    cur = conn.execute("PRAGMA table_info(memories)")
    cols = {row[1] for row in cur.fetchall()}
    if "visibility" not in cols:
        conn.execute("ALTER TABLE memories ADD COLUMN visibility TEXT NOT NULL DEFAULT 'normal'")
    if "source" not in cols:
        conn.execute("ALTER TABLE memories ADD COLUMN source TEXT")
    if "updated_at" not in cols:
        conn.execute(
            "ALTER TABLE memories ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )


def init_memory_db(db_path: str | None = None) -> None:
    """
    Initialize the memory database and create/update tables.
    Call once at server startup.
    """
    global _DB_PATH
    if db_path is None:
        base = Path(__file__).resolve().parents[2]
        db_path = str(base / "data" / "whisperleaf_memory.db")
    _DB_PATH = db_path

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(_CREATE_TABLE)
        conn.execute(_CREATE_AUDIT_TABLE)
        _migrate_add_columns(conn)


def _get_conn() -> sqlite3.Connection:
    if not _DB_PATH:
        raise RuntimeError("Memory DB not initialized; call init_memory_db() first.")
    return sqlite3.connect(_DB_PATH)


def record_audit(
    memory_id: int,
    event_type: str,
    meta_json: Optional[Dict[str, Any]] = None,
) -> None:
    """Append an audit event for a memory. No-op if DB not initialized."""
    if not _DB_PATH or event_type not in AUDIT_EVENT_TYPES:
        return
    meta_str = json.dumps(meta_json) if meta_json else None
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO memory_audit_events (memory_id, event_type, meta_json, created_at) VALUES (?, ?, ?, ?)",
            (memory_id, event_type, meta_str, datetime.utcnow().isoformat()),
        )


def save_memory(text: str, source: Optional[str] = None) -> Optional[int]:
    """
    Store a memory. Text is saved as-is. visibility=normal, created_at/updated_at set.
    Returns the new memory id, or None if skipped (empty text) or DB not initialized.
    """
    if not _DB_PATH:
        raise RuntimeError("Memory DB not initialized; call init_memory_db() first.")
    text = (text or "").strip()
    if not text:
        return None
    visibility = "normal"
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO memories (content, visibility, source, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (text, visibility, source or None, now, now),
        )
        memory_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    record_audit(memory_id, "created", {"source": source})
    return memory_id


def get_recent_memory_entries(
    limit: int = 5,
    exclude_blocked: bool = True,
) -> List[Dict[str, Any]]:
    """
    Return the most recent memories as list of {id, content, visibility, source, created_at}.
    If exclude_blocked, visibility='blocked' are omitted. Logs 'searched' audit for each returned.
    """
    if not _DB_PATH:
        return []
    where = "WHERE visibility != 'blocked'" if exclude_blocked else ""
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT id, content, visibility, source, created_at FROM memories {where} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    entries = [
        {
            "id": row["id"],
            "content": row["content"],
            "visibility": row["visibility"],
            "source": row["source"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    for e in entries:
        record_audit(e["id"], "searched")
    return entries


def get_recent_memories(limit: int = 5) -> List[str]:
    """
    Return the most recent memories (newest first), as a list of content strings.
    Blocked memories are never returned.
    """
    entries = get_recent_memory_entries(limit=limit, exclude_blocked=True)
    return [e["content"] for e in entries]


def set_visibility(memory_id: int, visibility: str) -> bool:
    """
    Set visibility for a memory. visibility must be in VISIBILITY_VALUES.
    Records audit event (blocked/unblocked/pinned/unpinned/updated). Returns True if row updated.
    """
    if not _DB_PATH or visibility not in VISIBILITY_VALUES:
        return False
    prev_visibility: Optional[str] = None
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT visibility FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if row:
            prev_visibility = row[0]
        cur = conn.execute(
            "UPDATE memories SET visibility = ?, updated_at = ? WHERE id = ?",
            (visibility, datetime.utcnow().isoformat(), memory_id),
        )
        if cur.rowcount == 0:
            return False
    pv = prev_visibility
    if pv is not None:
        if visibility == "blocked" and pv != "blocked":
            record_audit(memory_id, "blocked")
        elif visibility != "blocked" and pv == "blocked":
            record_audit(memory_id, "unblocked")
        elif visibility == "pinned" and pv != "pinned":
            record_audit(memory_id, "pinned")
        elif visibility != "pinned" and pv == "pinned":
            record_audit(memory_id, "unpinned")
        else:
            record_audit(memory_id, "updated", {"visibility": visibility})
    return True


def get_memory(memory_id: int) -> Optional[Dict[str, Any]]:
    """Return one memory by id or None."""
    if not _DB_PATH:
        return None
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, content, visibility, source, created_at, updated_at FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
    if not row:
        return None
    return dict(row)


def get_audit_events(memory_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return the last N audit events for a memory (newest first)."""
    if not _DB_PATH:
        return []
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, memory_id, event_type, meta_json, created_at FROM memory_audit_events WHERE memory_id = ? ORDER BY created_at DESC LIMIT ?",
            (memory_id, limit),
        ).fetchall()
    out = []
    for row in rows:
        meta = json.loads(row["meta_json"]) if row["meta_json"] else None
        out.append(
            {
                "id": row["id"],
                "memory_id": row["memory_id"],
                "event_type": row["event_type"],
                "meta_json": meta,
                "created_at": row["created_at"],
            }
        )
    return out
