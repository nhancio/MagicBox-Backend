# Quick Fix: Install FFmpeg for 30-Second Video Generation

## The Issue
Your video generation is failing because **FFmpeg is not installed**. FFmpeg is required to stitch multiple 5-8 second scenes into a final 30-second video.

## Quick Solution (Choose One)

### Option 1: Install via Chocolatey (Recommended - Easiest)

1. **Open PowerShell as Administrator**:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Install Chocolatey** (if not installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

3. **Install FFmpeg**:
   ```powershell
   choco install ffmpeg -y
   ```

4. **Verify**:
   ```powershell
   ffmpeg -version
   ```

5. **Restart your terminal and FastAPI server**

### Option 2: Use Installation Script

1. **Open PowerShell as Administrator**
2. **Navigate to backend folder**:
   ```powershell
   cd "E:\MagicBox Workspace\MagicBox-Backend\backend"
   ```
3. **Run the script**:
   ```powershell
   .\install_ffmpeg.ps1
   ```

### Option 3: Manual Installation

1. **Download FFmpeg**:
   - Go to: https://www.gyan.dev/ffmpeg/builds/
   - Download: `ffmpeg-release-essentials.zip`

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
   - **Close and reopen** your terminal
   - Run: `ffmpeg -version`

## After Installation

1. **Close ALL terminal windows**
2. **Open a NEW terminal**
3. **Restart your FastAPI server**:
   ```powershell
   cd "E:\MagicBox Workspace\MagicBox-Backend\backend"
   uvicorn app.main:app --reload --app-dir src
   ```

4. **Test video generation**:
   ```json
   POST /api/test/reel
   {
     "topic": "Test video",
     "duration_seconds": 30,
     "generate_video": true
   }
   ```

## Verify It's Working

After installation, you should see:
- ✅ `ffmpeg -version` shows version info
- ✅ Video generation completes successfully
- ✅ Response includes `video_path` with a 30-second video

## Troubleshooting

### "ffmpeg is not recognized" after installation
- **Close and reopen** your terminal (PATH changes require new session)
- Verify PATH: `echo $env:PATH` (should include ffmpeg path)
- Restart your FastAPI server

### Still not working?
1. Check if FFmpeg exists: `Test-Path "C:\ffmpeg\bin\ffmpeg.exe"`
2. Verify PATH includes FFmpeg directory
3. Restart your computer (sometimes needed for PATH changes)

## Need Help?

See detailed guide: `backend/INSTALL_FFMPEG_WINDOWS.md`
