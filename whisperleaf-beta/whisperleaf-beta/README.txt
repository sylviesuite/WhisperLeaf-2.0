IMPORTANT:
Use Python 3.11. Python 3.13 is not supported and may cause runtime errors.

Full guide (setup, zip packaging, troubleshooting): README.md

WhisperLeaf Beta (Local AI Workspace)

Requirements:
- (Optional) Ollama for local models

Setup:

1. Open PowerShell in this folder
2. Create virtual environment:
   python -m venv .venv

3. Activate:
   .\.venv\Scripts\Activate

4. Install dependencies:
   pip install -r requirements.txt

5. Start WhisperLeaf:
   powershell -ExecutionPolicy Bypass -File .\start_whisperleaf.ps1

6. Open:
   http://127.0.0.1:8000

Notes:
- Runs fully local
- No cloud connections
- First run may take longer
- UI assets (CSS, owl image, marketing JS) ship under static/assets/; FastAPI serves them at /assets/ so the beta folder needs no external whisperleaf-site copy.
