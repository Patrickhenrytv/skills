# setup.ps1 — One-command setup for SentimentTracker on Windows
# Run from the root of the skills repo:
#   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

function Write-OK($msg)   { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  ❌ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "  🧠 SentimentTracker — GenLayer Setup" -ForegroundColor Magenta
Write-Host "  ======================================" -ForegroundColor Magenta

# ── 1. Check prerequisites ────────────────────────────────────────
Write-Step "Checking prerequisites..."

# Node.js
try {
    $nodeVer = node --version 2>&1
    Write-OK "Node.js $nodeVer"
} catch {
    Write-Fail "Node.js not found. Install from https://nodejs.org"
    exit 1
}

# Python
try {
    $pyVer = python --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-Fail "Python not found. Install from https://python.org"
    exit 1
}

# Docker
try {
    $dockerVer = docker --version 2>&1
    Write-OK "Docker: $dockerVer"
} catch {
    Write-Warn "Docker not found. Needed for localnet. Install from https://docker.com"
}

# ── 2. Install GenLayer CLI ───────────────────────────────────────
Write-Step "Installing GenLayer CLI..."
try {
    $glVer = genlayer --version 2>&1
    Write-OK "GenLayer CLI already installed: $glVer"
} catch {
    Write-Host "  Installing genlayer globally via npm..." -ForegroundColor Gray
    npm install -g genlayer
    Write-OK "GenLayer CLI installed"
}

# ── 3. Install Python dependencies ───────────────────────────────
Write-Step "Installing Python dependencies..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
Write-OK "Python packages installed"

# ── 4. Set up .env ───────────────────────────────────────────────
Write-Step "Setting up environment..."
if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-OK "Created .env from .env.example"
    Write-Warn "Edit .env to configure your network and account"
} else {
    Write-OK ".env already exists"
}

# ── 5. Init GenLayer project ──────────────────────────────────────
Write-Step "Initializing GenLayer project..."
try {
    genlayer init --yes 2>&1 | Out-Null
    Write-OK "GenLayer initialized"
} catch {
    Write-Warn "genlayer init skipped (may already be initialized)"
}

# ── 6. Summary ───────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ✅  Setup complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Start local node:  genlayer up" -ForegroundColor Gray
Write-Host "    2. Run tests:         pytest tests/" -ForegroundColor Gray
Write-Host "    3. Deploy contract:   genlayer deploy --contract contracts/sentiment_tracker.py" -ForegroundColor Gray
Write-Host "    4. Open dashboard:    Open dashboard/index.html in your browser" -ForegroundColor Gray
Write-Host ""
