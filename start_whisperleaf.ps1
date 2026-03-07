# WhisperLeaf launcher - run from project root
Set-Location $PSScriptRoot

# Activate venv so uvicorn is available
if (Test-Path ".venv\Scripts\Activate.ps1") {
    .\.venv\Scripts\Activate.ps1
}

Write-Host "WhisperLeaf starting at http://127.0.0.1:8000"

# When server is reachable, open browser (runs in background while server starts)
$openBrowser = {
    $url = "http://127.0.0.1:8000"
    $maxTries = 30
    $delaySec = 0.25
    foreach ($i in 1..$maxTries) {
        try {
            Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2 | Out-Null
            Start-Process $url
            break
        } catch { Start-Sleep -Seconds $delaySec }
    }
}
Start-Job -ScriptBlock $openBrowser | Out-Null

python -m uvicorn src.core.main:app --reload --host 127.0.0.1 --port 8000
