@echo off
setlocal
cd /d "%~dp0"

echo.
echo  Building WhisperLeaf Installer...
echo  -----------------------------------

REM ── Check Python ────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Python not found. Install Python 3.10+ and add it to PATH.
  pause & exit /b 1
)

REM ── Install build dependencies ───────────────────────────────────────────────
echo  Installing build dependencies...
python -m pip install pyinstaller pillow --quiet
if errorlevel 1 (
  echo  ERROR: Failed to install build dependencies.
  pause & exit /b 1
)

REM ── Locate bundled assets ────────────────────────────────────────────────────
set ZIP=..\whisperleaf-site\downloads\whisperleaf-beta.zip
set OWL=..\whisperleaf-site\assets\images\owl.png
set ICO=..\whisperleaf-site\favicon.ico
set REQ=..\whisperleaf-beta\requirements.txt

if not exist "%ZIP%" (
  echo  ERROR: App zip not found at %ZIP%
  pause & exit /b 1
)
if not exist "%OWL%" (
  echo  ERROR: owl.png not found at %OWL%
  pause & exit /b 1
)
if not exist "%ICO%" (
  echo  ERROR: favicon.ico not found at %ICO%
  pause & exit /b 1
)

REM ── Build ────────────────────────────────────────────────────────────────────
echo  Building installer exe...
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name "WhisperLeafInstaller" ^
  --add-data "%ZIP%;." ^
  --add-data "%OWL%;." ^
  --add-data "%ICO%;." ^
  --add-data "%REQ%;." ^
  --icon "%ICO%" ^
  --clean ^
  bootstrap.py

if errorlevel 1 (
  echo  ERROR: PyInstaller build failed.
  pause & exit /b 1
)

REM ── Copy output ──────────────────────────────────────────────────────────────
if exist "dist\WhisperLeafInstaller.exe" (
  copy /Y "dist\WhisperLeafInstaller.exe" "..\whisperleaf-site\downloads\WhisperLeafInstaller.exe" >nul
  echo.
  echo  ✓ Built: whisperleaf-site\downloads\WhisperLeafInstaller.exe
  echo  ✓ Ready to deploy to Netlify.
) else (
  echo  ERROR: Output exe not found.
  pause & exit /b 1
)

echo.
pause
