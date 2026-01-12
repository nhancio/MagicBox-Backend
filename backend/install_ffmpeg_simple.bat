@echo off
echo ========================================
echo FFmpeg Installation Helper for Windows
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Checking for Chocolatey...
where choco >nul 2>&1
if %errorLevel% equ 0 (
    echo Chocolatey found! Installing FFmpeg...
    choco install ffmpeg -y
    if %errorLevel% equ 0 (
        echo.
        echo SUCCESS! FFmpeg installed via Chocolatey.
        echo.
        echo Verifying installation...
        ffmpeg -version
        echo.
        echo Installation complete! Please restart your terminal and FastAPI server.
        pause
        exit /b 0
    )
) else (
    echo Chocolatey not found.
    echo.
)

echo.
echo ========================================
echo Manual Installation Required
echo ========================================
echo.
echo Option 1: Install Chocolatey first, then run this script again
echo   - Visit: https://chocolatey.org/install
echo   - Or run PowerShell as Admin and paste:
echo     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
echo.
echo Option 2: Manual Installation
echo   1. Download from: https://www.gyan.dev/ffmpeg/builds/
echo   2. Download: ffmpeg-release-essentials.zip
echo   3. Extract to: C:\ffmpeg\
echo   4. Add C:\ffmpeg\bin to System PATH
echo      - Win+X -^> System -^> Advanced -^> Environment Variables
echo      - Edit Path -^> New -^> C:\ffmpeg\bin
echo.
echo After installation, restart your terminal and run: ffmpeg -version
echo.
pause
