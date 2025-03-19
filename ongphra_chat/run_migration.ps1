# run_migration.ps1
# PowerShell script to run the database migration

# Ensure we're in the right directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath

Write-Host "Starting database migration script..." -ForegroundColor Cyan

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "No virtual environment found. Running with system Python." -ForegroundColor Yellow
}

try {
    # Run the migration script
    Write-Host "Running database migration..." -ForegroundColor Green
    python -m app.db.migrate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Migration completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Migration failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "An error occurred while running the migration: $_" -ForegroundColor Red
    exit 1
} finally {
    # Deactivate virtual environment if we activated it
    if (Test-Path function:deactivate) {
        deactivate
    }
}

Write-Host "Migration script completed." -ForegroundColor Cyan 