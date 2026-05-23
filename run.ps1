# ==============================================================================
# TeamLedgerBot — Dev Environment Launcher (run.ps1)
# ==============================================================================
# Purpose: Start FastAPI Backend & Vite+React Frontend concurrently.
# Usage: Execute `.\run.ps1` inside PowerShell.
# ==============================================================================

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         🚀 Initializing TeamLedgerBot Dev Env...        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RootDir = Get-Location

# 1. Verify and Update Config files
Write-Host "[1/4] ⚙️ Checking Environment Variables..." -ForegroundColor Yellow

# Backend CORS Configuration Check
$BackendEnvPath = Join-Path $RootDir "backend\.env"
if (Test-Path $BackendEnvPath) {
    $BackendEnvContent = Get-Content $BackendEnvPath -Raw
    if ($BackendEnvContent -notmatch "CORS_ORIGINS=.*http://localhost:5173") {
        Write-Host "  ⚠️ CORS missing port 5173. Auto-fixing..." -ForegroundColor Gray
        $BackendEnvContent = $BackendEnvContent -replace "CORS_ORIGINS=http://localhost:3000", "CORS_ORIGINS=http://localhost:5173,http://localhost:3000"
        Set-Content $BackendEnvPath $BackendEnvContent
        Write-Host "  ✅ Backend CORS configuration fixed!" -ForegroundColor Green
    } else {
        Write-Host "  ✅ Backend CORS environment variable is valid." -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ backend/.env file not found! Copy from .env.example first." -ForegroundColor Red
    Exit
}

# Frontend API Configuration Check
$FrontendEnvPath = Join-Path $RootDir "frontend\.env"
if (Test-Path $FrontendEnvPath) {
    $FrontendEnvContent = Get-Content $FrontendEnvPath -Raw
    if ($FrontendEnvContent -notmatch "VITE_API_BASE_URL=http://localhost:8000") {
        Write-Host "  ⚠️ Frontend API base URL is empty. Auto-configuring to localhost..." -ForegroundColor Gray
        $FrontendEnvContent = $FrontendEnvContent -replace "VITE_API_BASE_URL=", "VITE_API_BASE_URL=http://localhost:8000"
        Set-Content $FrontendEnvPath $FrontendEnvContent
        Write-Host "  ✅ Frontend API base URL configured successfully!" -ForegroundColor Green
    } else {
        Write-Host "  ✅ Frontend API base URL is valid." -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ frontend/.env file not found! Copy from .env.example first." -ForegroundColor Red
    Exit
}

# 2. Boot FastAPI Backend Server
Write-Host "[2/4] 🐍 Starting FastAPI Backend in a new window..." -ForegroundColor Yellow
$BackendDir = Join-Path $RootDir "backend"
$BackendCommand = "Set-Location '$BackendDir'; if (Test-Path '.venv') { . '.venv\Scripts\Activate.ps1' }; Write-Host 'Running database migrations...' -ForegroundColor Cyan; alembic upgrade head; Write-Host 'Booting FastAPI on port 8000...' -ForegroundColor Green; uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "$BackendCommand" -WindowStyle Normal
Write-Host "  ✅ Backend launch command dispatched!" -ForegroundColor Green

# 3. Boot Vite Frontend Server
Write-Host "[3/4] ⚡ Starting Vite Frontend in a new window..." -ForegroundColor Yellow
$FrontendDir = Join-Path $RootDir "frontend"
$FrontendCommand = "Set-Location '$FrontendDir'; if (-not (Test-Path 'node_modules')) { Write-Host 'node_modules missing. Installing dependencies...' -ForegroundColor Cyan; npm install }; Write-Host 'Launching Vite dev server...' -ForegroundColor Green; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "$FrontendCommand" -WindowStyle Normal
Write-Host "  ✅ Frontend launch command dispatched!" -ForegroundColor Green

# 4. Launch Verification Pages
Write-Host "[4/4] 🌐 Opening browser verification pages..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Open Frontend homepage
Start-Process "http://localhost:5173"
# Open Backend Swagger Docs
Start-Process "http://localhost:8000/docs"

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "     🎉 Services successfully launched!" -ForegroundColor Green
Write-Host "     - Frontend Client:  http://localhost:5173" -ForegroundColor Green
Write-Host "     - Backend API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
