# WhisperLeaf Playbook

A central strategic document for the WhisperLeaf project. Use it to align vision, product decisions, and development with the project’s core principles.

---

## 1. Vision

WhisperLeaf is a **privacy-first personal AI** that runs entirely on the user’s computer. It supports **cognitive sovereignty**: the idea that your thinking, knowledge, and AI assistance stay under your control, on your machine, with no requirement to send data to remote services.

The goal is not to replace cloud AI for every use case, but to offer a clear alternative where privacy, ownership, and local control come first.

---

## 2. Core Principles

- **Privacy First**  
  No user data is sent to external AI providers. All inference, memory, and document processing run locally. The system is designed so that sensitive or personal content never leaves the user’s device.

- **User Sovereignty**  
  The user owns their data, their memories, and their documents. They can inspect, delete, or export what the system stores. The product does not lock them in or make their data dependent on a remote service.

- **Transparency**  
  Users can see what context the AI used for each answer: which memories and which document excerpts were retrieved. There are no hidden pipelines or opaque “magic”; behavior is explainable and auditable.

- **Simplicity**  
  The product avoids unnecessary complexity. Features are focused and understandable. The interface stays calm and minimal so that the core value—local, private AI assistance—remains clear.

---

## 3. Product Identity

WhisperLeaf is a **personal AI workspace and knowledge engine**, not only a chatbot. It combines:

- Conversational AI for questions and reasoning  
- Document ingestion and retrieval so users can ask about their own files  
- A persistent memory system that learns from the conversation  
- Context transparency so users see what the AI used to answer  

The workspace is a single, coherent place where the user’s knowledge (documents + memories) and the local model work together, in private.

---

## 4. Core Capabilities

- **Local AI via Ollama**  
  Inference runs through a local model server (e.g. Ollama). The user chooses the model; WhisperLeaf sends prompts and streams responses over a local connection. No third party sees the conversation.

- **Document Intelligence**  
  Users upload documents (e.g. .txt, .md). The system chunks, indexes, and retrieves relevant passages so the AI can answer questions using the user’s own content. Citations and excerpt previews show which parts of which documents were used.

- **Memory System**  
  The system can store and recall facts or preferences mentioned in conversation. Memories are stored locally and retrieved when relevant to the current question. Users can view and delete stored memories.

- **Context Transparency**  
  Each assistant response can show what context was used: memory snippets, document sources, and excerpts. An expandable context panel under responses makes this visible without cluttering the main chat.

- **Private Workspace**  
  Chat history, session state, documents, and memories are kept on the user’s machine. The UI is designed to feel like a focused workspace: sidebar for system status, documents, and actions; main area for conversation and context.

---

## 5. User Journey (Sales Funnel)

1. **Ad / Post**  
   User encounters WhisperLeaf (social, blog, community, or search).

2. **Landing Page**  
   Clear value proposition: local, private AI. No hype; straightforward explanation of what it does and why it matters.

3. **Short Demo**  
   A simple, concrete demo: upload a document, ask a question, see the AI answer using that document. No account required to try.

4. **What Makes WhisperLeaf Different**  
   Emphasis on privacy, local execution, document + memory intelligence, and transparency. Comparison with “send-everything-to-the-cloud” alternatives is implicit rather than aggressive.

5. **Purchase Page**  
   Clear pricing and delivery (e.g. download or license). Friction kept minimal.

6. **Download**  
   User obtains the application (installer or package). Instructions for dependencies (e.g. Ollama) are easy to find.

7. **Onboarding**  
   First-run experience checks for a local model, explains installation if needed, and introduces the workspace. “Start Chatting” leads into the main interface without overwhelming the user.

---

## 6. First-Run Experience

The ideal onboarding flow:

1. **Welcome**  
   Brief welcome screen that explains: WhisperLeaf runs locally, you can upload documents, and memories are saved privately.

2. **Model Readiness**  
   The app checks whether a local model (e.g. via Ollama) is available.  
   - If **yes**: show “Local model detected. You’re ready to chat.”  
   - If **no**: show “Local model not running” with short instructions (e.g. install Ollama, run `ollama run llama3.2`).

3. **Start Chatting**  
   A single primary action (“Start Chatting”) dismisses onboarding and focuses the user on the chat input. A small help control (e.g. “?”) allows reopening the welcome/help content later.

4. **Persistence**  
   “Seen onboarding” is stored (e.g. in localStorage) so returning users go straight to the chat. First-run is shown only once per device/browser.

The tone is calm and instructional, not alarming. The goal is to get the user to a working chat with minimal steps.

---

## 7. Key Message

**“Your AI. Your data. Your computer.”**

This positioning statement captures ownership (your AI), data control (your data), and place of execution (your computer). Use it in landing copy, onboarding, and high-level product communication. Keep supporting copy simple and consistent with this line.

---

## 8. Demo Flow

The core demo is minimal and repeatable:

1. **Upload document**  
   User uploads a document (e.g. a .txt or .md file) via the sidebar Documents section.

2. **Ask a question**  
   User asks a question in chat that relates to the document’s content.

3. **AI answers using the document**  
   The system retrieves relevant chunks, injects them into context, and the model answers. The response shows “Sources” and optional excerpt previews so the user sees the link between the document and the answer.

No accounts, no cloud, no complexity. The demo proves: local AI + your documents = useful, transparent answers.

---

## 9. Long-Term Vision

WhisperLeaf can evolve into a **personal AI operating environment**:

- **Tools**  
  Extensible tooling (e.g. search, summarization, structured tasks) that all run locally and respect the same privacy and transparency principles.

- **Knowledge Workspace**  
  A unified space for documents, memories, and conversations—searchable, linkable, and under the user’s control.

- **Local-First Architecture**  
  All core capabilities (inference, retrieval, memory, tools) run on the user’s machine. Optional sync or backup could be added later without compromising the default of “nothing leaves the device.”

The product stays focused on the individual user and their machine. It does not aim to become a multi-tenant SaaS; it aims to be the best local, private AI workspace.

---

## 10. Design Philosophy

The interface should feel:

- **Calm**  
  No aggressive prompts, flashing elements, or urgency. Typography, spacing, and motion are restrained.

- **Minimal**  
  Only what’s needed is shown. Sidebar, chat, and context panels stay clear. Decorative elements are subtle or absent.

- **Focused**  
  The primary task is conversation and knowledge (documents + memory). Secondary actions (e.g. New Session, Clear Chat, Documents, Memories) are available but don’t compete with the main flow.

- **Trustworthy**  
  Transparency (context used, sources, excerpts) and clear status (model readiness, memory/documents) build confidence. Copy is honest and precise rather than promotional.

---

## 11. Things to Protect

These should not be compromised as the product evolves:

- **Privacy**  
  No sending of user content to remote AI or analytics by default. Local-first is non-negotiable for the core experience.

- **Transparency**  
  Users must be able to see what context (memories, documents, excerpts) was used for an answer. No hidden context or opaque RAG.

- **Simplicity**  
  Avoid feature creep that obscures the core value. Prefer a small set of clear capabilities over a large set of half-implemented ones.

- **User Control**  
  Users can delete memories, remove documents, clear chat, and start new sessions. They are not locked into behaviors they didn’t choose.

When in doubt, favor these four over short-term convenience or growth tactics that undermine them.

---

## 12. Current Project Status

As of this playbook, WhisperLeaf includes:

- **Local model integration**  
  Backend talks to Ollama (or compatible API) for chat and streaming. Model availability is checked at startup and exposed to the UI.

- **Streaming chat**  
  SSE-based streaming from backend to frontend; message state and UI (e.g. thinking indicator, copy, context panel) are aligned.

- **Document ingestion and retrieval**  
  Upload of .txt/.md files; chunking and vector indexing (e.g. ChromaDB); retrieval and injection into context; document list and search in the sidebar.

- **Memory system**  
  Semantic and keyword memory storage and retrieval; optional query rewriting; memories injected into context; memory list and delete in the UI; “memory saved” notifications.

- **Context transparency**  
  Sources and excerpts under assistant messages; expandable context panel (memories + documents + excerpts); excerpt preview overlay when clicking a source.

- **Onboarding**  
  First-run welcome, model readiness message, “Start Chatting,” and a help control to reopen onboarding. “Seen onboarding” stored in localStorage.

The architecture is a FastAPI backend, a single-page chat UI (vanilla JS), and local persistence for documents and memory. The playbook should be updated as major capabilities or architecture decisions change.

---

## 13. Next Development Focus

Priority for the next phase:

- **Stability**  
  Harden existing flows: streaming, session handling, document and memory retrieval, timeouts, and error handling. Fix edge cases before adding new features.

- **Usability**  
  Improve clarity of labels, onboarding, and feedback (e.g. model status, upload and indexing, context panel). Reduce confusion for new users.

- **Ease of installation**  
  Clear docs and in-app guidance for installing and running a local model (e.g. Ollama). Smoother first-run when the model is missing or slow.

Emphasize **stability, usability, and ease of installation** over rapid feature expansion. A reliable, understandable, easy-to-install product will serve the vision better than a broad but brittle feature set.

---

## Future Concepts (Do Not Implement Yet)

Ideas saved for later phases of WhisperLeaf development. These are recorded so the thinking is preserved; development focus remains on stabilizing and launching the core product.

### WhisperLeaf Hive (Future Community Concept)

WhisperLeaf Hive is a potential future community space for independent WhisperLeaf users.

The idea is that while each WhisperLeaf instance runs locally and privately on a user's machine, the people who use them may benefit from sharing ideas, workflows, and research with one another.

The Hive would be a place where WhisperLeaf owners could gather to discuss topics such as:

- private AI workflows  
- local model setups  
- thinking and writing techniques using AI  
- research methods  
- philosophy of cognitive sovereignty  
- experiments with local AI tools  

**Important principle:** The Hive should **not be built until WhisperLeaf has an active user base**. Community spaces created too early often feel empty and fragile.

**Estimated trigger point for considering the Hive:** 500–1000 active WhisperLeaf users. When that threshold exists, a simple community hub could be created to support idea sharing among users.

**Possible forms the Hive could take in the future:**

- curated community page on the WhisperLeaf website  
- discussion board or forum  
- GitHub Discussions  
- small invite-based community space  

The Hive is intended to support the broader philosophy behind WhisperLeaf: *"Independent AI tools used by independent thinkers."*

For now this concept is recorded here so the idea is preserved, but development focus remains on stabilizing and launching the core WhisperLeaf product.

---

## Launch Strategy

Goal: Reach the first 1,000 WhisperLeaf users.

**Core message:**  
"Private AI that runs entirely on your computer."

**Primary audience:**

- developers  
- researchers  
- writers  
- privacy-focused users  
- indie hackers  

**Launch assets:**

- founder story / essay  
- short demo video (about 60–90 seconds)  
- simple landing page  
- launch post explaining the philosophy of WhisperLeaf  

**Initial launch platforms:**

- Hacker News  
- Reddit (privacy, self-hosting, local AI communities)  
- indie hacker and developer forums  

**Pricing approach:**

- one-time purchase model  
- early adopter pricing around $39–$49  

**Success milestone:**  
First 1,000 paid WhisperLeaf users.

---

## Product Roadmap

This roadmap organizes development so ideas are captured without disrupting focus.

### Phase 1 — Core Product

Focus on stability and usability.

- clean interface  
- reliable local model support  
- document interaction  
- stable performance  
- simple onboarding experience  

Goal: a stable WhisperLeaf product ready for launch.

### Phase 2 — Growth

Improve usability and reach more users.

- improved onboarding  
- workflow examples  
- documentation and tutorials  
- better demo materials  

Goal: reach 1,000+ active users.

### Phase 3 — Ecosystem

Build tools and community around the core product.

Possible future ideas:

- WhisperLeaf Hive community space  
- plugin system  
- shared workflows  
- research and knowledge library  

Goal: WhisperLeaf becomes a broader platform for private AI thinking tools.

---

*This playbook is a living document. Update it when vision, principles, or strategy change, and use it to guide design and product decisions.*
