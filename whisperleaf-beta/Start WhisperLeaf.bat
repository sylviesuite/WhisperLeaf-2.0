@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo ERROR: .venv not found. Create a virtual environment in this folder first.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

REM Check for port conflicts before launching uvicorn.
REM If 8000 is already bound, exit cleanly instead of showing a long traceback.
netstat -ano | findstr /R /C:"127\.0\.0\.1:8000 .* LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo Port 8000 is already in use. Please close the other WhisperLeaf window or free the port, then try again.
  pause
  exit /b 1
)

REM Open the UI shortly after launch so the server has time to bind (no --reload).
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000/"

python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo.
  echo WhisperLeaf exited with an error.
  pause
  exit /b 1
)

endlocal
