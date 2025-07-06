@echo off
echo Building TTS GUI App...
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build the exe
echo Building with PyInstaller...
pyinstaller cocospeak.spec

REM Check if build was successful
if exist "dist\cocospeak\cocospeak.exe" (
    echo.
    echo Build successful!
    echo Executable created at: dist\cocospeak\cocospeak.exe
    echo.
    echo To distribute, send the entire 'dist\cocospeak' folder.
    echo.
    pause
) else (
    echo.
    echo Build failed! Check the error messages above.
    echo.
    pause
) 