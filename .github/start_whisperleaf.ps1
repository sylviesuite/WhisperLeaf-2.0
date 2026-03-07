# Project root (parent of .github when script is in .github/)
$ProjectRoot = if (Split-Path -Leaf $PSScriptRoot -eq ".github") { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
Set-Location $ProjectRoot

# Activate venv so uvicorn is available
if (Test-Path ".venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
}

Write-Host "Starting WhisperLeaf at http://127.0.0.1:8000"
python -m uvicorn src.core.main:app --reload --host 127.0.0.1 --port 8000

pause