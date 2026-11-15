<#
  Starts the backend (http://localhost:8000) and the frontend (http://localhost:5173) in two new PowerShell windows.
  Run from the repository root:   powershell -ExecutionPolicy Bypass -File scripts\start-dev.ps1
  First time? Do the one-off setup from the README (Quick start) before running this.
#>
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $py)) { Write-Host "Backend virtual environment missing. See README > Quick start, step 1." -ForegroundColor Red; exit 1 }
if (-not (Test-Path (Join-Path $root "backend\.env"))) { Write-Host "backend\.env missing. Copy backend\.env.example to backend\.env and add your API key (README > Quick start, step 2)." -ForegroundColor Red; exit 1 }
if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) { Write-Host "Frontend dependencies missing. Run 'npm install' inside frontend (README > Quick start, step 3)." -ForegroundColor Red; exit 1 }

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; & '$py' -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "Starting... open http://localhost:5173  (admin console: http://localhost:5173/admin/login)" -ForegroundColor Green
Write-Host "API docs (Swagger): http://localhost:8000/docs"
