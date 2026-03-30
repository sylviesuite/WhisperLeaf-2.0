# WhisperLeaf Beta

**WhisperLeaf** is a privacy-first local AI workspace: it runs on your computer, keeps your prompts and data on your device, and does not require the cloud for core use.

## Before you start

- **Python 3.11** (recommended). **Python 3.13** is not supported and may cause errors.
- **Windows** desktop (this beta package is set up for typical Windows use).
- **Optional:** [Ollama](https://ollama.com) if you want local LLM models.

## First-time setup

1. Unzip this folder anywhere you like (avoid paths with unusual permissions if you hit issues).
2. Open **Command Prompt** or **PowerShell** **in this folder** (the folder that contains `requirements.txt`).
3. Create a virtual environment:
   ```bat
   python -m venv .venv
   ```
4. Activate it:
   - **Command Prompt:** `\.venv\Scripts\activate.bat`
   - **PowerShell:** `.\.venv\Scripts\Activate.ps1`
5. Install dependencies:
   ```bat
   pip install -r requirements.txt
   ```

## Run the app

**Option A — double-click or run the batch launcher (after setup above):**

```bat
start_whisperleaf.bat
```

**Option B — PowerShell script (opens the browser when the server is ready):**

```powershell
powershell -ExecutionPolicy Bypass -File .\start_whisperleaf.ps1
```

**Option C — manual command** (from this folder, with the venv activated):

```bat
python -m uvicorn src.core.main:app --host 127.0.0.1 --port 8000
```

Then open in your browser:

**http://127.0.0.1:8000**

Marketing pages use `/`; chat is available at `/chat` once the server is running.

## What’s in this folder

| Item | Purpose |
|------|--------|
| `src/` | Application code (FastAPI entry: `src.core.main:app`) |
| `templates/` | HTML templates |
| `static/` | Static files and bundled UI assets under `static/assets/` |
| `config/` | Example config files (copy to active config as needed) |
| `requirements.txt` | Python dependencies |

## Packaging this beta as a ZIP

**Do not** include your local virtual environment or cache in the zip you share:

- Omit **`.venv/`**
- Omit **`__pycache__/`** and **`*.pyc`**

Recipients unzip, then follow **First-time setup** and **Run the app**.

## Troubleshooting

- **`python` not found:** Install Python 3.11 from [python.org](https://www.python.org/downloads/) and ensure “Add Python to PATH” was selected, then open a **new** terminal.
- **`pip install` fails:** Upgrade pip (`python -m pip install --upgrade pip`) and try again.
- **Port 8000 in use:** Stop the other program using that port, or run uvicorn with another port, e.g. `--port 8001`, and open `http://127.0.0.1:8001`.
- **Blank or unstyled marketing pages:** Ensure `static/assets/` is present (it ships with this package); the app serves those files at `/assets/`.
- **Models / chat behavior:** For local models, install and run **Ollama** if your setup expects it.
