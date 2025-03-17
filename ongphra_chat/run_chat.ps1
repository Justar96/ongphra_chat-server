# run_chat.ps1
Write-Host "Starting Fortune Telling Chat Interface..."

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $scriptDir

# Check and install dependencies
Write-Host "Checking dependencies..."
$requirementsFile = Join-Path $scriptDir "chat_requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "Installing/upgrading dependencies..."
    python -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error installing dependencies. Please check your Python installation and try again." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Warning: chat_requirements.txt not found. Dependencies may be missing." -ForegroundColor Yellow
}

# Get command line arguments
$arguments = @()
foreach ($arg in $args) {
    $arguments += $arg
}

# Set default values
$serverHost = "127.0.0.1"
$port = 8080
$debug = $false

# Parse arguments
for ($i = 0; $i -lt $arguments.Count; $i++) {
    switch ($arguments[$i]) {
        "--host" {
            $serverHost = $arguments[++$i]
        }
        "--port" {
            $port = $arguments[++$i]
        }
        "--debug" {
            $debug = $true
        }
    }
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Using Python: $pythonVersion"
} catch {
    Write-Host "Error: Python not found. Please install Python 3.8 or later." -ForegroundColor Red
    exit 1
}

# Run the chat interface
$chatInterface = Join-Path $scriptDir "chat_interface.py"
if (-not (Test-Path $chatInterface)) {
    Write-Host "Error: chat_interface.py not found at: $chatInterface" -ForegroundColor Red
    exit 1
}

$pythonArgs = @(
    $chatInterface,
    "--host", $serverHost,
    "--port", $port
)
if ($debug) {
    $pythonArgs += "--debug"
}

Write-Host "Running on http://$($serverHost):$($port)"
Write-Host "Using Python script: $($pythonArgs[0])"

try {
    python $pythonArgs
} catch {
    Write-Host "Error running chat interface: $_" -ForegroundColor Red
    exit 1
} 