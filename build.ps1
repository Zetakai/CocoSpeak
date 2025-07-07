# TTS GUI App Build Script
Write-Host "Building TTS GUI App..." -ForegroundColor Green
Write-Host ""

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
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable created at: dist\cocospeak\cocospeak.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To distribute, send the entire 'dist' folder." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Note: You may need to manually add trainer/VERSION file after build." -ForegroundColor Magenta
    Write-Host ""
    Read-Host "Press Enter to continue"
} else {
    Write-Host ""
    Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to continue"
} 