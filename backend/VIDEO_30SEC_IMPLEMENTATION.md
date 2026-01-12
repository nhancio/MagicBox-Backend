# 30-Second Video Generation Implementation

## Summary

Updated the video generation system to create **30-second videos** by generating multiple 5-8 second scenes and stitching them together with FFmpeg.

## Changes Made

### 1. **AIVideoService** (`backend/src/app/services/ai_video_service.py`)
- ✅ Complete rewrite to support multi-scene generation
- ✅ Scene planning: Breaks 30 seconds into 5-6 scenes (6 seconds each)
- ✅ Continuity management: Maintains visual consistency between scenes
- ✅ FFmpeg integration: Concatenates scene clips into final video
- ✅ Error handling: Handles failed scenes gracefully

**Key Methods:**
- `_plan_scenes()`: Plans scenes based on duration and script data
- `_generate_single_scene()`: Generates one 5-8 second scene
- `_concatenate_videos()`: Stitches scenes together with FFmpeg
- `generate_video()`: Main method (updated signature)

**New Parameters:**
- `duration_seconds` (default: 30)
- `script_data` (optional): Dict with hook, script, scenes for better planning

### 2. **Test Endpoint** (`backend/src/app/api/v1/test_generation.py`)
- ✅ Updated to pass `duration_seconds` and `script_data` to video service
- ✅ Better integration with reel script data

### 3. **Reel Agents**
- ✅ `reel_agent.py`: Updated to use new video generation parameters
- ✅ `reel_chat_agent.py`: Updated to use new video generation parameters

## How It Works

### Step 1: Scene Planning
```
30 seconds → 5 scenes × 6 seconds each
```

Each scene gets:
- Specific timing (0-6s, 6-12s, etc.)
- Scene-specific prompt based on script
- Continuity descriptions to maintain visual consistency

### Step 2: Generate Scenes
```
Scene 1: 0-6s   → scene_01.mp4
Scene 2: 6-12s  → scene_02.mp4
Scene 3: 12-18s → scene_03.mp4
Scene 4: 18-24s → scene_04.mp4
Scene 5: 24-30s → scene_05.mp4
```

Each scene is generated independently with Veo 3.1.

### Step 3: Stitch with FFmpeg
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy final_video.mp4
```

### Step 4: Return Final Video
- Final 30-second video saved
- Individual scene files kept (for debugging)
- Metadata includes scene count and any failures

## Prerequisites

### Install FFmpeg

**Windows:**
```powershell
choco install ffmpeg
# Or download from: https://ffmpeg.org/download.html
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Verify:**
```bash
ffmpeg -version
```

## Usage

### API Endpoint
```json
POST /api/test/reel
{
  "topic": "Product demonstration",
  "duration_seconds": 30,
  "generate_video": true
}
```

### Direct Service Call
```python
from app.services.ai_video_service import AIVideoService

result = AIVideoService.generate_video(
    prompt="Base prompt",
    duration_seconds=30,
    script_data={
        "hook": "Stop showing features",
        "script": "Full script text...",
        "scenes": [...]
    }
)
```

## Response Format

```json
{
  "success": true,
  "video_path": "C:\\Users\\...\\Temp\\generated_video_xxx.mp4",
  "metadata": {
    "model": "veo-3.1-generate-preview",
    "duration_seconds": 30,
    "num_scenes": 5,
    "failed_scenes": [],
    "file_size_bytes": 1234567
  }
}
```

## Performance

- **Time**: 5-10 minutes for 30-second video
  - ~1-2 minutes per scene (5-6 scenes)
  - ~10 seconds for FFmpeg concatenation
- **API Calls**: 5-6 Veo API calls (one per scene)
- **File Size**: ~5-15 MB per video

## Error Handling

### FFmpeg Not Found
Returns error with installation instructions.

### Scene Generation Failure
- Video still created with successful scenes
- `failed_scenes` array indicates which failed
- Minimum 1 scene required

### Concatenation Failure
- Returns individual scene paths for manual stitching
- Error message explains issue

## Files Modified

1. ✅ `backend/src/app/services/ai_video_service.py` - Complete rewrite
2. ✅ `backend/src/app/api/v1/test_generation.py` - Updated endpoint
3. ✅ `backend/src/app/ai/agents/reel_agent.py` - Updated agent
4. ✅ `backend/src/app/ai/agents/reel_chat_agent.py` - Updated agent

## Documentation

- 📄 `backend/docs/VIDEO_GENERATION_30SEC.md` - Detailed documentation
- 📄 `backend/VIDEO_30SEC_IMPLEMENTATION.md` - This file

## Testing

1. **Install FFmpeg** (see Prerequisites)
2. **Test endpoint:**
   ```bash
   POST /api/test/reel
   {
     "topic": "Test video",
     "duration_seconds": 30,
     "generate_video": true
   }
   ```
3. **Check response:**
   - `success: true`
   - `video_path` points to final video
   - `metadata.num_scenes` should be 5
   - `metadata.failed_scenes` should be empty

## Next Steps

- [ ] Add progress tracking API
- [ ] Implement async scene generation (parallel)
- [ ] Add automatic audio/music
- [ ] Scene retry logic for failed scenes
- [ ] Quality optimization
