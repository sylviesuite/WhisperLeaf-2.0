# WhisperLeaf System Hardening Review

## Tested Scenarios and Fixes

### 1. Empty message handling

| Layer | Behavior | Status |
|-------|----------|--------|
| **Frontend** | `sendMessage()` sets `setSendingState(true)` first, then trims; if empty, `setSendingState(false)` and return. No request sent. | Already robust |
| **Backend** | Rejects empty with SSE stream containing single `error` event: "Please enter a message." | Already robust |

**Fixes applied:** None required.

---

### 2. Rapid message submission

| Layer | Behavior | Status |
|-------|----------|--------|
| **Frontend** | Guard `if (this.state.isSending) return` and immediate `setSendingState(true)` so a second Enter/click sees `isSending` true. | Already robust |

**Fixes applied:** None required.

---

### 3. Model unavailable (Ollama not running)

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | `generate()` catches `httpx.ConnectError` and yields `error` event with user-facing message. Session not appended. | Already robust |
| **Frontend** | On `error` event: `stopWatchdog`, `stopThinking`, `clearThinkingStep`, `setStreamingBubbleError`, then return. `finally` in `sendMessage()` runs `setSendingState(false)`. | Already robust |
| **Health check** | Startup check and `/api/model/status`; UI shows banner when unavailable. | Already present |

**Fixes applied:** None required.

---

### 4. Extremely long conversations

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | `MAX_CONTEXT_MESSAGES = 24`; older messages summarized and stored in `SESSION_SUMMARIES`; only last 24 sent to model. Session cap `MAX_CHAT_SESSIONS = 500` with eviction. | Already robust |

**Fixes applied:** None required.

---

### 5. Session clearing and summary reset

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | `POST /api/chat/clear` pops both `CHAT_SESSIONS[session_id]` and `SESSION_SUMMARIES[session_id]`. | Already robust |
| **Frontend** | `clearSession()` and `newSession()` clear `state.messages`, `currentStreamingId`, `currentStreamId`, call `syncDomFromMessages()`, and call clear API. | Already robust |

**Fixes applied:** None required.

---

### 6. Memory deletion during active conversation

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | Memory retrieval is per-request; deleting a memory only affects future requests. No in-memory cache of retrieval results. | No issue |
| **Frontend** | "Memories used" panel shows last turn’s snippets; deleting a memory only updates the Saved Memories list. No conflict. | No issue |

**Fixes applied:** None required.

---

### 7. Browser refresh during streaming

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | If client disconnects, `yield` can raise `BrokenPipeError` or `ConnectionResetError`. Unhandled, this could log tracebacks. | **Fixed** |
| **Frontend** | Refresh aborts the in-flight request so the server sees disconnect sooner; UI is replaced so no stale state. | **Fixed** |

**Fixes applied:**
- **Backend (`main.py`):** Wrapped the body of `generate()` in `try/except (BrokenPipeError, ConnectionResetError)` so client disconnect is logged and the generator exits without traceback.
- **Frontend (`chat.js`):** Added `AbortController` for the chat `fetch`. On `beforeunload` and `pagehide`, the controller is aborted so the request is cancelled. On `AbortError`, `onAbort()` runs (stop watchdog, thinking, show "Request cancelled.", `setSendingState(false)`). Listeners are removed in `finally`.

---

### 8. Multiple browser tabs (same session)

| Layer | Behavior | Status |
|-------|----------|--------|
| **Backend** | A request from Tab B with stale (shorter) history was overwriting `CHAT_SESSIONS[session_id]`, so Tab A’s longer session could be lost. | **Fixed** |

**Fixes applied:**
- **Backend (`main.py`):** When setting `CHAT_SESSIONS[session_id]`, only overwrite if the new history is at least as long as the existing one: `if len(session_list) >= len(existing): CHAT_SESSIONS[session_id] = session_list`. This avoids replacing a longer session (e.g. from another tab) with shorter history.

---

## Files Modified

| File | Change |
|------|--------|
| **`src/core/main.py`** | 1) Session overwrite guard: only set `CHAT_SESSIONS[session_id]` when `len(session_list) >= len(existing)`. 2) In `generate()`, wrap body in `try/except (BrokenPipeError, ConnectionResetError)` and log on client disconnect. |
| **`static/js/chat.js`** | 1) Create `AbortController` for chat request; pass `signal` to `fetch`. 2) On `beforeunload` and `pagehide`, call `abort()`. 3) On `AbortError` in catch, call `onAbort()` and return. 4) In `finally`, remove `beforeunload`/`pagehide` listeners. |

---

## Summary of Improvements

- **Multi-tab:** Server no longer overwrites a longer session with shorter history from another tab.
- **Refresh during stream:** Client cancels the request on unload; server handles client disconnect without tracebacks.
- **No architectural changes;** only defensive checks and cleanup.
