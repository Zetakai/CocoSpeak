# CocoSpeak TTS GUI App Build Script (PyQt6 Version)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building CocoSpeak TTS GUI App (PyQt6)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if PyInstaller is available
try {
    $pyinstallerVersion = pyinstaller --version 2>&1
    Write-Host "PyInstaller found: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: PyInstaller is not installed" -ForegroundColor Red
    Write-Host "Please run: pip install pyinstaller" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# Build the exe
Write-Host "Building with PyInstaller..." -ForegroundColor Yellow
pyinstaller cocospeak.spec

# Create empty models folder outside the exe directory
Write-Host "Creating empty models folder..." -ForegroundColor Yellow
if (-not (Test-Path "dist\cocospeak\models")) {
    New-Item -ItemType Directory -Path "dist\cocospeak\models" -Force
}

# Check if build was successful
if (Test-Path "dist\cocospeak\cocospeak.exe") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable created at: dist\cocospeak\cocospeak.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "New Features in PyQt6 Version:" -ForegroundColor Yellow
    Write-Host "• Modern PyQt6 interface with better performance" -ForegroundColor White
    Write-Host "• Real-time download progress for online models" -ForegroundColor White
    Write-Host "• Robust hotkey system with clear error messages" -ForegroundColor White
    Write-Host "• Smart text preprocessing for character compatibility" -ForegroundColor White
    Write-Host "• Enhanced queue system with real-time status" -ForegroundColor White
    Write-Host "• Better error handling and user feedback" -ForegroundColor White
    Write-Host ""
    Write-Host "To distribute, send the entire 'dist' folder." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Note: The app requires the 'models' folder to be present." -ForegroundColor Magenta
    Write-Host ""
    Read-Host "Press Enter to continue"
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above." -ForegroundColor Yellow
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "• Missing dependencies - run: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "• PyInstaller not installed - run: pip install pyinstaller" -ForegroundColor White
    Write-Host "• Python version too old - need Python 3.8+" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to continue"
} 