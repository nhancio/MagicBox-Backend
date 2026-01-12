# Install FFmpeg on Windows

## Quick Installation (Recommended)

### Option 1: Using Chocolatey (Easiest)

1. **Install Chocolatey** (if not already installed):
   ```powershell
   # Run PowerShell as Administrator
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install FFmpeg**:
   ```powershell
   choco install ffmpeg
   ```

3. **Verify installation**:
   ```powershell
   ffmpeg -version
   ```

### Option 2: Manual Installation

1. **Download FFmpeg**:
   - Go to: https://www.gyan.dev/ffmpeg/builds/
   - Download: `ffmpeg-release-essentials.zip` (or latest version)

2. **Extract**:
   - Extract to: `C:\ffmpeg\`
   - You should have: `C:\ffmpeg\bin\ffmpeg.exe`

3. **Add to PATH**:
   - Press `Win + X` → System → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" → Edit
   - Click "New" → Add: `C:\ffmpeg\bin`
   - Click OK on all dialogs

4. **Verify**:
   - Open **new** PowerShell/Command Prompt
   - Run: `ffmpeg -version`

### Option 3: Using Scoop

```powershell
scoop install ffmpeg
```

## Verify Installation

After installation, **restart your terminal** and run:

```powershell
ffmpeg -version
```

You should see FFmpeg version information.

## Troubleshooting

### "ffmpeg is not recognized"
- Make sure you **restarted your terminal** after adding to PATH
- Verify PATH: `echo $env:PATH` (PowerShell) or `echo %PATH%` (CMD)
- Check if ffmpeg.exe exists: `Test-Path "C:\ffmpeg\bin\ffmpeg.exe"`

### Still not working?
1. Close ALL terminal windows
2. Open a NEW terminal
3. Run `ffmpeg -version` again

## After Installation

Once FFmpeg is installed, restart your FastAPI server and try the video generation again:

```json
POST /api/test/reel
{
  "topic": "Your topic",
  "duration_seconds": 30,
  "generate_video": true
}
```
