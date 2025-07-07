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

REM Create empty models folder outside the exe directory
echo Creating empty models folder...
if not exist "dist\cocospeak\models" mkdir "dist\cocospeak\models"

REM Check if build was successful
if exist "dist\cocospeak\cocospeak.exe" (
    echo.
    echo Build successful!
    echo Executable created at: dist\cocospeak\cocospeak.exe
    echo.
    echo To distribute, send the entire 'dist' folder.
    echo.
    pause
) else (
    echo.
    echo Build failed! Check the error messages above.
    echo.
    pause
) 