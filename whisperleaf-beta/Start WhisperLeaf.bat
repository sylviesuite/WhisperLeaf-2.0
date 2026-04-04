@echo off
setlocal
cd /d "%~dp0"

echo.
echo  WhisperLeaf
echo  ------------------------------------

REM ── 1. Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo  ERROR: Python was not found.
  echo  Please install Python 3.10 or later from https://www.python.org
  echo  Make sure to check "Add Python to PATH" during installation.
  echo.
  pause
  exit /b 1
)

REM ── 2. First-run setup: create venv and install requirements ─────────────────
if not exist ".venv\Scripts\activate.bat" (
  echo  Setting up WhisperLeaf for the first time...
  echo  This may take a few minutes. Please wait.
  echo.

  python -m venv .venv
  if errorlevel 1 (
    echo.
    echo  ERROR: Failed to create virtual environment.
    echo  Try running this file as Administrator, or check your Python installation.
    echo.
    pause
    exit /b 1
  )

  call ".venv\Scripts\activate.bat"
  python -m pip install --upgrade pip --quiet
  pip install -r "%~dp0requirements.txt" --quiet
  if errorlevel 1 (
    echo.
    echo  ERROR: Failed to install dependencies.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
  )

  echo  Setup complete!
  echo.
) else (
  call ".venv\Scripts\activate.bat"
)

REM ── 3. Check for port conflict ────────────────────────────────────────────────
netstat -ano | findstr /R /C:"127\.0\.0\.1:8000 .* LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo  Port 8000 is already in use.
  echo  Please close the other WhisperLeaf window or free the port, then try again.
  echo.
  pause
  exit /b 1
)

REM ── 4. Launch ────────────────────────────────────────────────────────────────
echo  Starting WhisperLeaf...
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000/"

python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo.
  echo  WhisperLeaf exited with an error.
  pause
  exit /b 1
)

endlocal
