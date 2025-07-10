@echo off
echo ========================================
echo Building CocoSpeak TTS GUI App (PyQt6)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if PyInstaller is available
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please run: pip install pyinstaller
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build the exe
echo Building with PyInstaller...
pyinstaller cocospeak.spec

REM Create empty models folder outside the exe directory
echo Creating empty models folder...
if not exist "dist\cocospeak\models" mkdir "dist\cocospeak\models"

REM Check if build was successful
if exist "dist\cocospeak\cocospeak.exe" (
    echo.
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo Executable created at: dist\cocospeak\cocospeak.exe
    echo.
    echo New Features in PyQt6 Version:
    echo • Modern PyQt6 interface with better performance
    echo • Real-time download progress for online models
    echo • Robust hotkey system with clear error messages
    echo • Smart text preprocessing for character compatibility
    echo • Enhanced queue system with real-time status
    echo • Better error handling and user feedback
    echo.
    echo To distribute, send the entire 'dist' folder.
    echo.
    echo Note: The app requires the 'models' folder to be present.
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo.
    echo Check the error messages above.
    echo Common issues:
    echo • Missing dependencies - run: pip install -r requirements.txt
    echo • PyInstaller not installed - run: pip install pyinstaller
    echo • Python version too old - need Python 3.8+
    echo.
    pause
) 