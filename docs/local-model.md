## Running the Local Model for WhisperLeaf

WhisperLeaf is designed to use a fully local LLM server (no cloud calls). The FastAPI backend talks to this local model via the `LocalModelClient` in `src/core/local_model.py`.

### 1. Start a local model server (Ollama)

The default configuration assumes an Ollama server running on your machine:

```bash
ollama serve
```

Then pull and run a model, for example `mistral`:

```bash
ollama pull mistral
```

By default, WhisperLeaf will send chat requests to:

- Base URL: `http://localhost:11434`
- Model name: `mistral`

### 2. Optional: configure a different URL or model

You can override the defaults with environment variables:

```bash
export WHISPERLEAF_MODEL_URL="http://localhost:11434"
export WHISPERLEAF_MODEL_NAME="mistral"
```

On Windows PowerShell:

```powershell
$env:WHISPERLEAF_MODEL_URL = "http://localhost:11434"
$env:WHISPERLEAF_MODEL_NAME = "mistral"
```

You can point `WHISPERLEAF_MODEL_URL` at any compatible local HTTP LLM server (e.g. a llama.cpp HTTP endpoint) as long as it accepts an Ollama-style `/api/chat` request body.

### 3. Start the WhisperLeaf API

From the project root:

```bash
uvicorn src.core.main:app --reload
```

Then open the chat UI in your browser:

```text
http://127.0.0.1:8000/
```

If the local model server is not running or not reachable, the `/api/chat` endpoint will return a friendly error message that the UI displays in the chat window.

