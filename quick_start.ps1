# Quick Start Script for Retail Shelf AI
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Retail Shelf AI - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Python
try {
    $pythonVersion = python --version
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Node.js
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Redis check
Write-Host ""
Write-Host "Checking Redis..." -ForegroundColor Yellow
$redis = Get-Process redis-server -ErrorAction SilentlyContinue
if (-not $redis) {
    Write-Host "⚠ Redis not running. Starting with Docker..." -ForegroundColor Yellow
    docker run -d -p 6379:6379 --name redis redis:7-alpine
    Start-Sleep -Seconds 3
    Write-Host "✓ Redis started" -ForegroundColor Green
} else {
    Write-Host "✓ Redis already running" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Backend..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

cd backend

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

Write-Host "Testing database connection..." -ForegroundColor Yellow
python test_db.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Frontend..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

cd ../frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "✓ Dependencies already installed" -ForegroundColor Green
}

cd ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application, open 3 terminals:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1 - Backend API:" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python run.py" -ForegroundColor White
Write-Host "  → http://localhost:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Terminal 2 - Celery Worker:" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  celery -A app.tasks.training_tasks worker --loglevel=info" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 3 - Frontend:" -ForegroundColor Cyan
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host "  → http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use Docker:" -ForegroundColor Yellow
Write-Host "  docker-compose up -d" -ForegroundColor White
Write-Host ""
