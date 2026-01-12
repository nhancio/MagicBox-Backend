# Simple FFmpeg Installation - 3 Steps

## ⚡ Quickest Method (2 minutes)

### Step 1: Install Chocolatey (One-time setup)

**Open PowerShell as Administrator:**
- Press `Win + X`
- Click "Terminal (Admin)" or "PowerShell (Admin)"

**Paste and run:**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### Step 2: Install FFmpeg

**In the same PowerShell window, run:**
```powershell
choco install ffmpeg -y
```

### Step 3: Verify & Restart

**Check it worked:**
```powershell
ffmpeg -version
```

**You should see version information!**

**Now:**
1. ✅ Close ALL terminal windows
2. ✅ Open a NEW terminal
3. ✅ Restart your FastAPI server
4. ✅ Test video generation again

---

## 🎯 Alternative: Use the Batch Script

1. **Right-click** `install_ffmpeg_simple.bat`
2. Select **"Run as administrator"**
3. Follow the prompts

---

## 📋 Manual Installation (If above doesn't work)

### Download & Install

1. **Download FFmpeg:**
   - Go to: https://www.gyan.dev/ffmpeg/builds/
   - Click: **"ffmpeg-release-essentials.zip"** (latest version)

2. **Extract:**
   - Extract the ZIP file
   - Move the `ffmpeg-x.x.x-essentials_build` folder to `C:\`
   - Rename it to `ffmpeg`
   - You should have: `C:\ffmpeg\bin\ffmpeg.exe`

3. **Add to PATH:**
   - Press `Win + X` → **System**
   - Click **"Advanced system settings"**
   - Click **"Environment Variables"**
   - Under **"System variables"**, find **"Path"** → Click **"Edit"**
   - Click **"New"**
   - Type: `C:\ffmpeg\bin`
   - Click **OK** on all dialogs

4. **Verify:**
   - **Close ALL terminal windows**
   - Open a **NEW** PowerShell/CMD
   - Run: `ffmpeg -version`
   - You should see version info!

---

## ✅ After Installation

**Restart everything:**
1. Close all terminals
2. Open new terminal
3. Restart FastAPI server:
   ```powershell
   cd "E:\MagicBox Workspace\MagicBox-Backend\backend"
   uvicorn app.main:app --reload --app-dir src
   ```

**Test video generation:**
```json
POST /api/test/reel
{
  "topic": "Test video",
  "duration_seconds": 30,
  "generate_video": true
}
```

---

## 🆘 Troubleshooting

### "ffmpeg is not recognized"
- ✅ **Close and reopen** your terminal (PATH changes need new session)
- ✅ Restart your FastAPI server
- ✅ Verify: `echo $env:PATH` (PowerShell) should include `C:\ffmpeg\bin`

### Still not working?
1. Check if file exists: `Test-Path "C:\ffmpeg\bin\ffmpeg.exe"`
2. If missing, re-extract FFmpeg to `C:\ffmpeg\`
3. Restart your computer (sometimes needed for PATH)

---

## 📞 Need More Help?

See detailed guide: `INSTALL_FFMPEG_WINDOWS.md`
