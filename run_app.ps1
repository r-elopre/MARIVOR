# Marivor Flask Application Launcher
Write-Host "🇵🇭 Starting Marivor Flask Application..." -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Change to project directory
Set-Location "c:\Users\ri\OneDrive\Marivor"

# Activate virtual environment and start Flask app
Write-Host "✅ Activating virtual environment..." -ForegroundColor Yellow
Write-Host "🚀 Starting Flask app..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1; python app.py

Write-Host "Press any key to continue..." -ForegroundColor Gray
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")