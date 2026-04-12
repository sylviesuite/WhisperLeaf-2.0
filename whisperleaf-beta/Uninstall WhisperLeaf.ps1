$Host.UI.RawUI.WindowTitle = "WhisperLeaf Uninstaller"

function Write-Step { param($msg) Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "  $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  $msg" -ForegroundColor Yellow }

Write-Host ""
Write-Host "  WhisperLeaf Uninstaller" -ForegroundColor White
Write-Host "  ------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Stop WhisperLeaf if running ────────────────────────────────────────────
Write-Step "Checking for a running WhisperLeaf server..."
$netLine = netstat -ano 2>$null | Select-String "127\.0\.0\.1:8000\s+\S+\s+LISTENING"
if ($netLine) {
    $procId = ($netLine.Line.Trim() -split '\s+')[-1]
    try {
        Stop-Process -Id ([int]$procId) -Force -ErrorAction Stop
        Write-Ok "Stopped WhisperLeaf (PID $procId)."
        Start-Sleep -Milliseconds 800
    } catch {
        Write-Warn "Could not stop PID $procId — it may have already exited."
    }
} else {
    Write-Ok "WhisperLeaf is not running."
}

# ── 2. Remove shortcuts ────────────────────────────────────────────────────────
Write-Step "Removing shortcuts..."
$shellKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
try {
    $sf      = Get-ItemProperty $shellKey -ErrorAction Stop
    $desktop  = $sf.Desktop
    $programs = $sf.Programs
} catch {
    $desktop  = [Environment]::GetFolderPath('Desktop')
    $programs = [Environment]::GetFolderPath('Programs')
}
foreach ($dir in @($desktop, $programs)) {
    $lnk = Join-Path $dir "WhisperLeaf.lnk"
    if (Test-Path $lnk) {
        Remove-Item $lnk -Force
        Write-Ok "Removed: $lnk"
    }
}

# ── 3. Remove app files ────────────────────────────────────────────────────────
$installDir = Join-Path $env:LOCALAPPDATA "WhisperLeaf"
Write-Step "Removing app files from $installDir..."
if (Test-Path $installDir) {
    Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $installDir)) {
        Write-Ok "App files removed."
    } else {
        Write-Warn "Some files could not be removed (server may still be running)."
        Write-Warn "Close WhisperLeaf and run the uninstaller again."
    }
} else {
    Write-Ok "App directory not found — already removed."
}

# ── 4. Offer to remove Ollama ─────────────────────────────────────────────────
Write-Host ""
$ans = Read-Host "  Remove Ollama (the AI engine) as well? [y/N]"
if ($ans -match '^[Yy]') {
    $ollamaUnins = Join-Path $env:LOCALAPPDATA "Programs\Ollama\unins000.exe"
    if (Test-Path $ollamaUnins) {
        Write-Step "Uninstalling Ollama..."
        Start-Process $ollamaUnins -ArgumentList "/SILENT" -Wait
        Write-Ok "Ollama removed."
    } else {
        Write-Warn "Ollama uninstaller not found. Remove it via Settings > Apps if needed."
    }
} else {
    Write-Ok "Ollama kept. Remove it later via Settings > Apps if you want."
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  WhisperLeaf has been uninstalled." -ForegroundColor Green
Write-Host ""
Read-Host "  Press Enter to close"
