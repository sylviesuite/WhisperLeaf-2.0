@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo WhisperLeaf: virtual environment not found.
    echo Create it first, then install dependencies:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo WhisperLeaf starting at http://127.0.0.1:8000
echo Press Ctrl+C to stop the server.
echo.
python -m uvicorn src.core.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause
