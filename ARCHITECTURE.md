# WhisperLeaf Architecture

## Core Principle

WhisperLeaf is a local-first personal AI designed for sovereignty, privacy, and long-term ownership by the user. The system is built so that intelligence runs on hardware the user controls, with data remaining on the user’s machine. The architecture prioritizes human agency, calm interaction, and sustainable local computation over centralized cloud services.

---

## Local AI Core

The AI model runs locally using engines such as **Ollama** or **llama.cpp**. WhisperLeaf talks to a local HTTP API (e.g. Ollama’s `/api/chat`), so no user content is sent to remote inference services. Model choice, base URL, and timeouts are configurable via environment variables. The stack supports both one-shot completion and streaming responses, with the system prompt and conversation history built and sent from the application server running on the user’s machine.

---

## Memory System

WhisperLeaf uses a layered memory system:

- **Short-term conversation memory** — The current chat session keeps in-memory (and optionally persisted) message history. This provides immediate context for the model within a conversation.
- **Long-term personal memory** — A local store (e.g. SQLite) holds user-specified and optionally auto-saved “memories” (facts, preferences, notes). These can be tagged with visibility, source, and timestamps, and are injected into the model context when relevant.
- **Vector search over stored knowledge** — Where supported, embeddings and vector search (e.g. over documents or memory entries) allow retrieval of relevant past content. Fallbacks exist when vector backends are unavailable, so the system still works without them.

Together, these layers support both coherent dialogue and long-term personal context without relying on remote memory or user profiling.

---

## Document Intelligence

WhisperLeaf can ingest user documents and build searchable representations. Documents are processed locally; text is extracted and can be chunked and embedded. Embeddings are stored in a local vector store so that later queries (e.g. from the user or the assistant) can retrieve relevant passages. This document intelligence runs on the user’s machine, so document content never has to leave the device unless the user explicitly exports or shares it.

---

## Privacy Model

All personal data remains on the user’s machine unless explicitly exported. Conversation history, memories, and ingested documents are stored locally. No telemetry or usage data is sent to external servers by default. The privacy model is “local by default”: the architecture assumes that the server and data live on the same machine (or a trusted network) as the user, with no requirement to send sensitive data to third parties.

---

## Offline Operation

WhisperLeaf is designed to function without internet access. The local model (Ollama, llama.cpp, or similar) runs on the same machine as the application. Memory, document store, and UI are all local. Once the model and dependencies are installed, the system can run fully offline, with no dependency on external APIs for core chat, memory, or document retrieval. Network is only needed for optional features (e.g. fetching external resources or updates, if the user enables them).

---

## Modular Design

Components are modular and replaceable:

- **Memory** — Storage backends (e.g. SQLite for long-term memory, in-memory or persisted conversation history) can be swapped or extended without changing the rest of the stack.
- **Models** — The local model client speaks a simple HTTP interface; switching between Ollama, llama.cpp, or another compatible server is a configuration change.
- **Ingestion** — Document processing, chunking, and embedding pipelines can be updated or replaced (e.g. different embedders or vector stores).
- **UI** — The web UI (templates, static assets) is separate from the core API; front-end and back-end can evolve independently.

This modularity allows the project to adapt to new local models, storage backends, and interfaces while keeping the same overall architecture.

---

## Future Hardware Nodes

The concept of **WhisperLeaf Nodes** extends the architecture to dedicated personal AI devices: small computers that run the same WhisperLeaf software stack locally. These nodes could be always-on, low-power, and optionally **solar-powered**, acting as private hubs for memory, documents, and local inference. By keeping the same local-first design, Nodes would offer the same sovereignty and privacy guarantees as a laptop or desktop installation, in a form factor suited to home or off-grid use.

---

## Ecosystem Direction

WhisperLeaf is the foundation for a privacy-first AI ecosystem centered around user ownership. The architecture supports a path from a single desktop or server instance to multiple Nodes, shared local models, and interoperable tools—all under the user’s control. The goal is an ecosystem where intelligence is personal, local, and sustainable, rather than locked into centralized platforms and subscriptions.
