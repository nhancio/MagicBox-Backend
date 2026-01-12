# FFmpeg Installation Script for Windows
# Run this script as Administrator

Write-Host "FFmpeg Installation Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Check if Chocolatey is installed
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue

if ($chocoInstalled) {
    Write-Host "Chocolatey is installed. Installing FFmpeg via Chocolatey..." -ForegroundColor Cyan
    choco install ffmpeg -y
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg installed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Verifying installation..." -ForegroundColor Cyan
        ffmpeg -version
        Write-Host ""
        Write-Host "SUCCESS! FFmpeg is now installed." -ForegroundColor Green
        Write-Host "Please restart your terminal and FastAPI server." -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "Chocolatey installation failed. Trying manual installation..." -ForegroundColor Yellow
    }
} else {
    Write-Host "Chocolatey is not installed." -ForegroundColor Yellow
    Write-Host "Would you like to install Chocolatey first? (Y/N)" -ForegroundColor Cyan
    $response = Read-Host
    if ($response -eq "Y" -or $response -eq "y") {
        Write-Host "Installing Chocolatey..." -ForegroundColor Cyan
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Chocolatey installed. Installing FFmpeg..." -ForegroundColor Cyan
            choco install ffmpeg -y
            if ($LASTEXITCODE -eq 0) {
                Write-Host "FFmpeg installed successfully!" -ForegroundColor Green
                ffmpeg -version
                Write-Host ""
                Write-Host "SUCCESS! Please restart your terminal and FastAPI server." -ForegroundColor Green
                exit 0
            }
        }
    }
}

# Manual installation fallback
Write-Host ""
Write-Host "Manual Installation Instructions:" -ForegroundColor Yellow
Write-Host "1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Cyan
Write-Host "2. Download: ffmpeg-release-essentials.zip" -ForegroundColor Cyan
Write-Host "3. Extract to: C:\ffmpeg\" -ForegroundColor Cyan
Write-Host "4. Add C:\ffmpeg\bin to your system PATH" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use the detailed guide: backend/INSTALL_FFMPEG_WINDOWS.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "After installation, restart your terminal and run: ffmpeg -version" -ForegroundColor Yellow
