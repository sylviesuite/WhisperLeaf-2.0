# DIRTY SESSION TEST REVIEW

**Date:** MVP v0.1 stabilization  
**Reference:** TEST_PLAN.md (Dirty Session Test)  
**Scope:** Stability verification only; no new features, no architecture changes.

---

## A. Code paths reviewed

| File path | Purpose |
|-----------|---------|
| `static/js/chat.js` | Chat UI controller: send path, SSE read loop, message rendering, thinking step, sidebar history, stream guard, request lock, watchdog |
| `static/js/chat.js` → `sendMessage()` | Single send path; sets streamId, creates bubble, fetches, calls streamAssistantResponse(res, streamId) |
| `static/js/chat.js` → `streamAssistantResponse(response, streamId)` | SSE parsing, chunk/status/done/error handling, isActiveStream() guard, updateStreamingBubble, finalizeStreamingBubble, setStreamingBubbleError |
| `static/js/chat.js` → `appendMessage()`, `createStreamingBubble()`, `updateStreamingBubble()`, `finalizeStreamingBubble()`, `setStreamingBubbleError()` | Message bubble rendering and streaming bubble lifecycle |
| `static/js/chat.js` → `setThinkingStep()`, `clearThinkingStep()` | Thinking-step status line |
| `static/js/chat.js` → `loadSessionHistory()`, `clearSession()` | Session load (GET /api/chat/history), clear (POST /api/chat/clear), DOM replace then append with skipSidebarRefresh |
| `static/js/chat.js` → `refreshSidebarHistory()` | Sidebar conversation list from .message.user[data-message-id], scroll-to-message |
| `src/core/main.py` → `chat_endpoint()` | POST /api/chat: memory_query rewrite, _build_memory_context (Tool Bus memory.search), generate() SSE stream (status, meta, chunk, done/error) |
| `src/core/main.py` → `_build_memory_context()` | tool_bus.execute("memory.search", ...); empty result returns ""; no throw |
| `src/core/main.py` → `get_chat_history()` | GET /api/chat/history; returns CHAT_SESSIONS[session_id] |
| `src/core/tools/bus.py` → `ToolBus.execute()` | call_tool; returns ToolResult(ok, data, error); catches KeyError and Exception |
| `src/core/tools/memory_search_tool.py` → `_run_memory_search()`, handler | memory.search tool; returns {snippets, entries_for_audit}; exceptions caught in handler/bus |
| `src/core/tools/docs_search_tool.py` → `_run_docs_search()`, handler | docs.search tool; returns []; vector_store.search wrapped in try/except |
| `src/core/tools/system_status_tool.py` → handler | system.status tool; returns dict; try/except returns safe fallback |
| `src/core/tools_registry.py` → `call_tool()` | Dispatches to registered handler; raises KeyError if unknown |

---

## B. Likely pass areas

- **Request lock:** `isSending` guard at top of `sendMessage()`; Send button disabled via `setSendingState(true)`; prevents double submit under normal UI use.
- **Active stream guard:** `currentStreamId` set per request; chunks/done/error only update UI when `isActiveStream()`; old stream completion does not finalize or write to the new bubble.
- **Thinking indicator clearing:** All exit paths (done, error, !res.ok, !res.body, catch, finally) call `clearThinkingStep()` and `stopThinking()` (where applicable); finally always runs `setSendingState(false)`.
- **Watchdog:** 25s timeout calls stopThinking, clearThinkingStep, setSendingState(false); prevents permanently stuck “sending” state.
- **Empty memory:** `_build_memory_context` returns `""` when `not result.ok`, no `result.data`, or no snippets; chat builds messages without memory block; no crash.
- **Tool Bus / tool failure:** `ToolBus.execute` catches exceptions and returns `ToolResult(ok=False, error=...)`; `_build_memory_context` checks `result.ok` and returns `""`; no uncaught tool error in chat path.
- **Session reload:** `loadSessionHistory()` clears `chatWindow.innerHTML`, sets `state.history = list`, then appends messages once with `skipSidebarRefresh: true`, then `refreshSidebarHistory()` once; no duplicate hydration.
- **Sidebar history:** Derived from DOM (`.message.user`); refreshed after append user message and after load/clear; no separate persistence layer that could desync.

---

## C. Likely failure risks still present

- **Rapid-fire (Step 4):** If the user somehow triggers two sends (e.g. double Enter or script), the second request is blocked by `isSending`; the only way to get two concurrent streams is if the lock were bypassed. With the guard, the first stream’s late chunks would be ignored once the second stream is active; the second stream’s bubble is the only one updated. Risk: low if lock is never bypassed.
- **Mid-stream refresh (Step 9):** On page refresh during streaming, the in-flight fetch is abandoned; `loadSessionHistory()` runs on init and replaces DOM. No client-side cleanup of the abandoned stream (no AbortController); server may still be streaming. Risk: server-side resource use only; UI state is clean after reload.
- **docs.search / system.status in chat:** These tools are registered and callable via Tool Bus but are not invoked from the chat endpoint; only memory.search is used in the chat flow. So “tool path test” for docs.search/system.status would require a separate API (e.g. POST /api/tools/call) or future integration. Risk: TEST_PLAN Step 6 for docs/search and system.status is not fully covered by the current chat UI flow.

---

## D. Minimal fixes made

| File path | What changed | Why |
|-----------|--------------|-----|
| `static/js/chat.js` | Added `const streamId = crypto.randomUUID();` and `this.state.currentStreamId = streamId;` at start of `sendMessage()` before creating bubble and fetch. | `streamId` was passed to `streamAssistantResponse(res, streamId)` but never defined, which would throw ReferenceError at runtime and break all streaming. |
| `static/js/chat.js` | When stream receives `done` or `error` and `!isActiveStream()`, call `console.warn('[WhisperLeaf] Stale stream done/error/completed, ignored.')`. | Lightweight defensive logging to confirm during manual test (Steps 4, 9) that stale streams are discarded and do not update the UI. |

---

## E. Manual test sequence to run now

Run in order with backend running and SSE streaming enabled.

**Step 1 — Baseline**  
- Send: `My name is Steven and I'm building WhisperLeaf as a private thinking assistant.`  
- Then send: `What am I building?`  
- Expect: user/assistant render correctly, stream completes, no duplicate bubble, thinking clears, memory path used.

**Step 2 — Vague input**  
- Send: `help`  
- Then send: `that thing from before`  
- Expect: no hang, graceful answer, no stuck loading.

**Step 3 — Long input**  
- Paste: `WhisperLeaf is meant to become a private thinking environment with memory, tools, and document awareness. I want it to feel calm, coherent, and useful. I do not want it to become noisy or bloated. Please summarize this, extract the main goals, and rewrite it as a short product statement.`  
- Expect: large input and full response render, no overflow, layout stable.

**Step 4 — Rapid-fire**  
- Send: `Summarize WhisperLeaf in one sentence.`  
- Immediately send: `Now make it more poetic.`  
- Expect: no cross-wired responses; if first stream finishes after second started, console may show “Stale stream … ignored” (expected).

**Step 5 — Empty memory**  
- Send: `What did I say earlier about penguins in previous conversations?`  
- Then send: `Okay, now summarize WhisperLeaf again.`  
- Expect: no crash, graceful fallback, next prompt works.

**Step 6 — Tool path**  
- memory.search: covered by Step 1 / “What am I building?”.  
- docs.search / system.status: call via POST /api/tools/call with body `{"name": "docs.search", "payload": {"query": "WhisperLeaf architecture"}}` or `{"name": "system.status", "payload": {}}` and confirm response shape; chat UI does not invoke these yet.

**Step 7 — Tool failure**  
- Optional: temporarily force memory.search to fail (e.g. raise in tool); send a normal message.  
- Expect: error message in bubble, thinking clears, next prompt works.

**Step 8 — Session persistence**  
- Have a short conversation; refresh page.  
- Expect: history reloads, no duplicate messages, sidebar matches.

**Step 9 — Mid-stream interruption**  
- Send: `Write a detailed reflection on why a private personal AI matters in the future.`  
- While streaming, refresh or navigate away and back.  
- Expect: after reload, no stuck indicator; send “Continue normally.” and get a normal response.

**Step 10 — Final recovery**  
- Send: `Give me a clean one-sentence description of WhisperLeaf.`  
- Expect: normal response, no duplicate bubble, no stale error state.

---

## F. Release recommendation

**PASS READY** for MVP v0.1 freeze, with the following notes:

- The only code defect found and fixed was the missing `streamId` definition in `sendMessage()`, which would have broken streaming.
- Stale-stream logging is in place to verify guard behavior during manual Steps 4 and 9.
- Empty memory and tool failure paths are safe; session reload and sidebar logic are consistent and do not introduce duplication.
- Run the manual sequence above once before freeze; if all steps pass, the release decision rule in TEST_PLAN.md is satisfied.
