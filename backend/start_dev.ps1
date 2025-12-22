# Development startup script
Write-Host "Starting Retail Shelf AI - Development Mode" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting services..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start Redis (if not running)
Write-Host "Checking Redis..." -ForegroundColor Yellow
$redis = Get-Process redis-server -ErrorAction SilentlyContinue
if (-not $redis) {
    Write-Host "Please start Redis manually:" -ForegroundColor Red
    Write-Host "  docker run -d -p 6379:6379 redis" -ForegroundColor White
    Write-Host ""
}

# Start API server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start Celery worker, run in another terminal:" -ForegroundColor Yellow
Write-Host "  celery -A app.tasks.training_tasks worker --loglevel=info" -ForegroundColor White
Write-Host ""

python run.py
