# WhisperLeaf TEST_PLAN.md
## Pre-Release Stability Test for MVP v0.1

## Purpose

This test is designed to reveal the majority of hidden bugs in WhisperLeaf before freezing MVP v0.1.

It focuses on the dangerous seams between:

- chat UI
- SSE streaming
- Tool Bus
- memory search
- context injection
- session persistence
- sidebar history
- loading / watchdog state

This is not a unit test plan.  
This is an end-to-end stability test.

---

## Test Name

**Dirty Session Test**

---

## Pass Criteria

WhisperLeaf passes only if all of the following are true:

- no UI lockups
- no duplicate messages
- no missing messages
- no broken message ordering
- no permanently stuck loading or thinking state
- no assistant response attached to the wrong user message
- no crash after empty memory results
- no crash after tool failure
- no broken session reload
- no broken sidebar conversation history
- next prompt still works after every failure case

---

## Test Environment

Run this test in the normal WhisperLeaf desktop UI with:

- backend running
- SSE streaming enabled
- Tool Bus enabled
- memory.search enabled
- query rewriting enabled
- sidebar history enabled

If available, also test once with:

- docs.search enabled
- system.status enabled

---

## Logging Requirements

Before running this test, make sure the following are visible in logs if possible:

- incoming user message
- rewritten query
- Tool Bus dispatch
- tool result or tool error
- SSE stream opened
- SSE stream completed
- watchdog triggered or cleared
- session save event
- session reload event

---

## Dirty Session Test Script

### Step 1 — Baseline conversation

Send:

> My name is Steven and I'm building WhisperLeaf as a private thinking assistant.

Expected:

- user message renders correctly
- assistant streams correctly
- stream completes cleanly
- no duplicate bubble
- no CSS breakage
- no sidebar corruption

Then send:

> What am I building?

Expected:

- memory/search path works
- answer refers to WhisperLeaf correctly
- no crash in memory context injection
- no duplicate response
- thinking indicator clears normally

---

### Step 2 — Vague input

Send:

> help

Expected:

- no hang
- no malformed tool behavior
- answer is graceful
- rewritten query does not become nonsense
- stream completes normally

Then send:

> that thing from before

Expected:

- system handles ambiguity safely
- memory path does not overfire or fail badly
- response stays coherent
- no loading state gets stuck

---

### Step 3 — Long input stress

Paste a large paragraph, for example:

> WhisperLeaf is meant to become a private thinking environment with memory, tools, and document awareness. I want it to feel calm, coherent, and useful. I do not want it to become noisy or bloated. Please summarize this, extract the main goals, and rewrite it as a short product statement.

Expected:

- large input renders correctly
- no smashed text
- no overflow bug
- assistant streams all chunks in order
- no dropped response tail
- layout remains stable
- sidebar remains usable

---

### Step 4 — Rapid-fire send test

Send two prompts quickly, back to back:

> Summarize WhisperLeaf in one sentence.

Immediately after:

> Now make it more poetic.

Expected:

- no cross-wired responses
- no duplicate streams
- no assistant message attached to wrong prompt
- second prompt does not break first stream
- watchdog does not falsely trigger
- final UI state remains clean

---

### Step 5 — Empty / no-result memory search

Send:

> What did I say earlier about penguins in previous conversations?

Expected:

- memory.search can return empty safely
- no crash when memory result is empty
- assistant gives graceful fallback
- no corrupted context block
- next prompt still works

Then verify by sending:

> Okay, now summarize WhisperLeaf again.

Expected:

- normal operation resumes immediately
- no hidden stuck state from previous empty result

---

### Step 6 — Tool path test

Trigger an active tool path through normal UI flow.

Examples:
- memory.search
- docs.search
- system.status

If `system.status` exists, send:

> Show system status.

Expected:

- Tool Bus dispatch occurs correctly
- tool result formats correctly
- assistant does not break stream format
- no raw object dump unless intended
- no UI crash from structured tool output

If `docs.search` exists, send:

> Search my docs for anything about WhisperLeaf architecture.

Expected:

- Tool Bus calls docs.search correctly
- result comes back cleanly
- no malformed result rendering
- assistant remains responsive after tool use

---

### Step 7 — Simulated tool failure

Force one tool to fail intentionally.

Examples:
- throw controlled error from memory.search
- return malformed payload from docs.search
- timeout system.status deliberately

Then send a prompt that triggers the failing tool.

Expected:

- WhisperLeaf does not crash
- assistant returns graceful fallback
- no permanent spinner or thinking indicator
- stream ends cleanly even on error
- next prompt still works normally

Immediately after failure, send:

> Are you still working?

Expected:

- system responds normally
- no poisoned state remains from failed tool call

---

### Step 8 — Sidebar session persistence test

After a multi-message conversation:

- verify session appears in sidebar
- open another session if available
- return to the original session

Expected:

- message history is intact
- no duplicated assistant messages
- no missing user messages
- ordering is preserved
- selected session matches displayed content

Then refresh the page and reopen the same session.

Expected:

- persisted history reloads correctly
- no hydration duplication
- no blank chat area
- no half-rendered streaming bubbles
- thinking indicator is not stuck

---

### Step 9 — Mid-stream interruption test

Ask a prompt that will stream for a few seconds, for example:

> Write a detailed reflection on why a private personal AI matters in the future.

During streaming:

- refresh the page
  or
- navigate away and back
  or
- switch sessions and return

Expected:

- no orphaned loading state
- no corrupted partial bubble
- no endless stream ghost
- watchdog cleans up correctly
- app recovers gracefully

After reload, send:

> Continue normally.

Expected:

- new prompt works immediately
- session remains usable
- no invisible stream conflict remains

---

### Step 10 — Final recovery test

After all of the above, send:

> Give me a clean one-sentence description of WhisperLeaf.

Expected:

- response is fast and normal
- no leftover state bugs
- no duplicate assistant bubble
- no broken formatting
- no stale error state

This step confirms system recovery after stress.

---

## Bug Tracking Sheet

Use this table while testing:

| Step | Scenario | Expected | Actual | Pass/Fail | Notes / Fix Needed |
|------|----------|----------|--------|-----------|--------------------|
| 1 | Baseline memory recall | Correct recall, clean stream |  |  |  |
| 2 | Vague input | Graceful response |  |  |  |
| 3 | Long input | Stable render, full stream |  |  |  |
| 4 | Rapid-fire sends | Correct ordering |  |  |  |
| 5 | Empty memory result | Graceful fallback |  |  |  |
| 6 | Tool invocation | Clean tool result |  |  |  |
| 7 | Tool failure | No crash, recovery works |  |  |  |
| 8 | Session reload | No duplicates or missing messages |  |  |  |
| 9 | Mid-stream interruption | Clean recovery |  |  |  |
| 10 | Final recovery | System fully usable |  |  |  |

---

## High-Risk Failure Patterns to Watch For

Pay special attention to these:

### Message-level bugs
- duplicate assistant bubbles
- duplicate user bubbles
- assistant reply attached to wrong user message
- partial response never completes
- out-of-order messages

### Streaming bugs
- stuck thinking indicator
- stuck loading spinner
- watchdog not clearing dead streams
- stream continues after session change
- stream writes into old bubble after refresh

### Tool Bus bugs
- tool called twice
- tool error crashes chat
- malformed tool result breaks render
- empty tool result causes bad fallback
- rewritten query causes wrong tool behavior

### Persistence bugs
- duplicate hydration after reload
- missing final assistant response after refresh
- sidebar points to wrong session
- old session content mixes with current session

### UI bugs
- input bar displaced
- text overlap or smashing
- sidebar collapse breaks chat width
- long message overflows container
- thought/status indicator never clears

---

## Release Decision Rule

WhisperLeaf is ready for MVP v0.1 freeze only if:

- Dirty Session Test passes end to end
- no critical failures remain
- any minor failures have known causes and safe workarounds
- system fully recovers after intentional failure scenarios

If one of these is false, do not freeze yet.

---

## Recommended Follow-Up After This Test

If this test reveals bugs, fix in this order:

1. stuck loading / thinking states
2. wrong message ordering
3. duplicate messages
4. failed recovery after tool error
5. session reload / persistence bugs
6. minor UI rendering issues

---

## Summary

The Dirty Session Test is the single most useful pre-release stability check for WhisperLeaf because it tests the real product under real conditions:

- ambiguity
- long context
- fast interaction
- empty results
- tool success
- tool failure
- reloads
- interrupted streams

If WhisperLeaf survives this cleanly, MVP v0.1 is likely stable enough to freeze.
