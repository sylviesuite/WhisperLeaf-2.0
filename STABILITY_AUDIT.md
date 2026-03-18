# WhisperLeaf Stability Audit

Stability review across chat engine, session management, memory, scrolling, UI, architecture, and error handling. **No new features** — only reliability, maintainability, and UX risks with concrete fixes.

---

## Top 10 Stability Risks (Prioritized)

### 1. **Unbounded in-memory session store (CHAT_SESSIONS)**  
**Priority: High — Reliability**

- **Risk:** `CHAT_SESSIONS` is a plain dict; every new session_id adds an entry. Long-lived or busy servers grow without bound and can OOM.
- **Fix applied:** Cap size with `MAX_CHAT_SESSIONS = 500`. Before adding a new session, call `_evict_chat_session_if_needed(session_id)` and evict the oldest session (insertion order) when at cap. Existing sessions are only updated, not duplicated.
- **Location:** `src/core/main.py` — `CHAT_SESSIONS`, `_evict_chat_session_if_needed()`, and calls before each `CHAT_SESSIONS[session_id] = ...`.

---

### 2. **Clear during stream: detached bubble and stale reference**  
**Priority: High — UX / Reliability**

- **Risk:** User clicks Clear while a response is streaming. DOM is cleared with `chatWindow.innerHTML = ''` but `state.currentStreamingBubble` still points to the removed node. The stream keeps calling `updateStreamingBubble` / `finalizeStreamingBubble` on a detached node; state is left inconsistent.
- **Fix applied:** In `clearSession()`, set `this.state.currentStreamingBubble = null` before clearing the DOM. In-flight stream updates then no-op when they check `currentStreamingBubble`.
- **Location:** `static/js/chat.js` — `clearSession()`.

---

### 3. **Stale stream leaves an extra, unfinalized assistant bubble**  
**Priority: High — UX**

- **Risk:** User sends message B while the response to A is still streaming. Only the latest stream (B) is applied to the UI, but the assistant bubble for A remains in the DOM with a streaming cursor and partial text. User sees two assistant bubbles, one “stuck” streaming.
- **Fix applied:** In `createStreamingBubble()`, before creating the new bubble, remove any existing assistant messages that still contain `.streaming-cursor` (unfinalized). Then set `currentStreamingBubble = null` so only the new bubble is tracked.
- **Location:** `static/js/chat.js` — `createStreamingBubble()`.

---

### 4. **Unbounded memory accumulation (SQLite + vector store)**  
**Priority: High — Long-term reliability**

- **Risk:** Every “remember:”, auto-save, and tool-saved thought inserts into SQLite and (where used) the vector store. There is no cap or pruning; DB and index grow indefinitely and can slow retrieval and bloat disk.
- **Recommendation:** Introduce a simple three-tier model and cap “active” usage:
  - **Active:** Recent N memories (e.g. last 500 by `created_at`) — used for search and context.
  - **Archived:** Older memories kept in DB but excluded from default search (or searched with lower priority / limit).
  - **Forgotten:** Deleted or visibility=blocked; not returned.
  Implement a configurable cap on “active” count (e.g. keep last 500); when inserting, if over cap, mark oldest as archived or run a periodic job that moves/archives old entries. Do not delete user data by default; prefer “archive” so it can be re-included later if needed.

---

### 5. **Session history load fails silently**  
**Priority: Medium — UX**

- **Risk:** `loadSessionHistory()` uses `if (!res.ok) return;` and `catch (_) {}`. On network or server error the user gets no feedback; the chat stays empty or shows a previous state with no explanation.
- **Recommendation:** Keep behavior (no toast or modal), but add a single `console.warn('[WhisperLeaf] Failed to load session history.', e)` in the catch and when `!res.ok` so support and logs can diagnose. Optionally set a data-attribute on the chat container (e.g. `data-session-load-failed`) for future UI or a11y use.

---

### 6. **No AbortController for in-flight chat request**  
**Priority: Medium — Resource / consistency**

- **Risk:** If the user clears the chat or navigates away while a response is streaming, the fetch body reader keeps running. Wasted work and possible updates after unmount if the component were ever reused.
- **Recommendation:** Create an `AbortController` per send, pass `signal` into `fetch()`, and call `abort()` when: (a) the user clicks Clear (in `clearSession()`), and (b) on `beforeunload` or `pagehide` if you want to cancel on leave. Ensures stream stops when the user explicitly clears or leaves.

---

### 7. **Scroll container vs message container naming**  
**Priority: Low — Maintainability**

- **Risk:** `chatMessages` (`.chat-window`) is the scroll container; `chatWindow` (`#chatWindow`, messages-inner) is where messages are appended. The names are easy to swap by mistake and cause wrong scroll or wrong append target.
- **Fix applied:** Inline comments in `cacheElements()`: `chatMessages` = scroll container, `chatWindow` = messages-inner append target.
- **Recommendation:** Consider renaming to `chatScrollContainer` and `messagesInner` in a future refactor for clarity.

---

### 8. **Error response body parsing**  
**Priority: Low — Edge-case UX**

- **Risk:** On `!res.ok` we do `res.json().catch(() => ({}))`. If the server returns non-JSON (e.g. HTML 500), we show “Request failed” and lose the real message. Rare but confusing.
- **Recommendation:** Try `res.json()` first; on catch, use `res.text()` and pass a short slice (e.g. first 200 chars) into the error message so the user sees something like “Request failed: <!DOCTYPE …” or the actual server message when available.

---

### 9. **Session lifecycle and “switching” are undefined**  
**Priority: Low — Clarity / future-proofing**

- **Risk:** There is a single `sessionId` per tab (from `sessionStorage`). Clear clears backend and UI but does not create a new session ID; “switching sessions” is not implemented. Backend has no notion of “closed” or “active”; it’s a single in-memory map.
- **Recommendation:** Document current behavior: one session per tab; Clear = clear messages and backend store for that session ID; no multi-tab or multi-session UI. If you later add session switching, define lifecycle (e.g. start → active → closed) and ensure backend eviction and frontend `sessionId` stay in sync.

---

### 10. **Message rendering and layout**  
**Priority: Low — Already in good shape**

- **Verified:** Messages use `textContent` (no innerHTML) so XSS is avoided. `.message` has `white-space: pre-wrap`, `word-break: break-word`, `overflow-wrap: anywhere` so text wraps and doesn’t break layout. Input bar has `flex-shrink: 0` so it stays visible. `finalizeStreamingBubble` replaces content in one go (`innerHTML = ''` then `appendChild`) so no intermediate layout flicker.
- **Recommendation:** Keep current approach. If you add rich content later, use a sanitizer and still avoid raw `innerHTML` with user/assistant content.

---

## Summary of Fixes Applied in This Audit

| # | Item | Change |
|---|------|--------|
| 1 | CHAT_SESSIONS unbounded | Added `MAX_CHAT_SESSIONS = 500` and `_evict_chat_session_if_needed()`; call before adding a new session. |
| 2 | Clear during stream | Set `this.state.currentStreamingBubble = null` at start of `clearSession()`. |
| 3 | Stale stream bubble | In `createStreamingBubble()`, remove any `.message.assistant` that contains `.streaming-cursor`, then set `currentStreamingBubble = null` before creating the new bubble. |
| 7 | Naming clarity | Comments in `cacheElements()` for `chatMessages` (scroll container) and `chatWindow` (append target). |

---

## Memory System: Suggested Structure

- **Active memory:** Last N entries (e.g. 500) by `created_at`; included in semantic/keyword search and in context injection. Enforce with a limit in queries or a “active” flag/table.
- **Archived memory:** Older entries; stored but not (or rarely) included in default search to keep retrieval fast and context size bounded. Can be re-activated or queried separately.
- **Forgotten:** `visibility = 'blocked'` or soft-delete; never returned in search or context.

This keeps the current behavior for small-scale use while giving a path to cap resource use and keep response times stable as data grows.

---

## Error Handling (Current State)

- **Failed AI response:** Caught in `generate()`; SSE `error` event with message; frontend shows it in the assistant bubble and finalizes. OK.
- **Document parsing:** `DocumentProcessor` is a stub and does not throw; no change needed for stability.
- **Memory retrieval failure:** `_build_memory_context` and tools return `""` or safe fallbacks; chat continues without memory. OK.
- **Session load error:** Handled silently (see risk #5); only recommendation is logging and optional data-attribute.

No new features were added; only stability-related fixes and documentation.
