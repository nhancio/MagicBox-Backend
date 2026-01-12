# 30-Second Video Generation with Veo 3.1

## Overview

Veo 3.1 can only generate 5-8 second clips per request. To create 30-second videos, we use a **multi-scene generation and stitching approach**:

1. **Break 30 seconds into 5-6 scenes** (6 seconds each)
2. **Generate each scene separately** with Veo 3.1
3. **Maintain visual continuity** between scenes
4. **Stitch scenes together** using FFmpeg

## Architecture

### Scene Planning
- Automatically divides 30 seconds into 5-6 scenes
- Each scene is 6 seconds (optimal for Veo)
- Uses script data (hook, scenes, dialogue) to create scene-specific prompts
- Maintains continuity by reusing character descriptions and style phrases

### Continuity Strategy
To prevent visual drift between scenes:
- **Re-describe the same character** in each scene
- **Reuse style phrases verbatim** (lighting, camera style)
- **Reference previous action** explicitly
- **Maintain consistent visual identity** across all scenes

### Video Stitching
- Uses FFmpeg to concatenate scene clips
- Fast concatenation (no re-encoding) using `-c copy`
- Creates temporary concat file for FFmpeg
- Cleans up intermediate files after stitching

## Prerequisites

### 1. Install FFmpeg

**Windows:**
```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
# Add to PATH after installation
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version
```

### 2. Python Dependencies
Already included in `requirements.txt`:
- `google-genai>=0.1.0`
- Standard library: `subprocess`, `tempfile`, `pathlib`

## Usage

### API Endpoint

```json
POST /api/test/reel
{
  "topic": "Product demonstration for marketing",
  "duration_seconds": 30,
  "generate_video": true
}
```

### Direct Service Call

```python
from app.services.ai_video_service import AIVideoService

# With script data (recommended)
script_data = {
    "hook": "Stop showing features. Nobody cares.",
    "script": "Your full script text...",
    "scenes": [
        {
            "visual": "Speaker close-up, looking intense",
            "dialogue": "Stop showing features. Nobody cares."
        },
        # ... more scenes
    ]
}

result = AIVideoService.generate_video(
    prompt="Base prompt for context",
    duration_seconds=30,
    script_data=script_data,  # Optional but recommended
    output_path=None,  # Saves to temp directory if None
)
```

## How It Works

### Step 1: Scene Planning
```python
scenes = [
    {
        "scene_number": 1,
        "start_time": 0,
        "end_time": 6,
        "duration": 6,
        "prompt": "Cinematic marketing video scene (6 seconds)..."
    },
    # ... 4-5 more scenes
]
```

### Step 2: Generate Each Scene
- Each scene is generated independently with Veo 3.1
- Scenes are saved as `scene_01.mp4`, `scene_02.mp4`, etc.
- Progress is logged for each scene

### Step 3: Concatenate with FFmpeg
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4
```

### Step 4: Return Final Video
- Final 30-second video is saved
- Individual scene files are kept (for debugging)
- Returns path to final video

## Response Format

```json
{
  "success": true,
  "video_path": "C:\\Users\\...\\Temp\\generated_video_xxx.mp4",
  "prompt": "Base prompt...",
  "metadata": {
    "model": "veo-3.1-generate-preview",
    "duration_seconds": 30,
    "num_scenes": 5,
    "failed_scenes": [],
    "file_size_bytes": 1234567
  }
}
```

## Error Handling

### FFmpeg Not Found
```json
{
  "success": false,
  "error": "FFmpeg is not installed or not in PATH. Please install FFmpeg: https://ffmpeg.org/download.html"
}
```

### Scene Generation Failure
- If some scenes fail, the video will still be created with successful scenes
- `failed_scenes` array indicates which scenes failed
- Minimum 1 scene required for success

### Concatenation Failure
- Returns individual scene paths in `scene_paths` for manual stitching
- Error message explains the issue

## Performance

- **Total Time**: 5-10 minutes for 30-second video
  - ~1-2 minutes per scene (5-6 scenes)
  - ~10 seconds for FFmpeg concatenation
- **API Calls**: 5-6 Veo API calls (one per scene)
- **File Size**: ~5-15 MB per 30-second video (depends on quality)

## Best Practices

1. **Provide Script Data**: Pass `script_data` with scenes for better scene planning
2. **Consistent Prompts**: Use similar style descriptions across scenes
3. **Character Continuity**: Re-describe characters in each scene prompt
4. **Error Monitoring**: Check `failed_scenes` in response metadata
5. **File Cleanup**: Optionally clean up scene files after stitching (commented out in code)

## Troubleshooting

### Video is shorter than 30 seconds
- Check if some scenes failed (`failed_scenes` in metadata)
- Verify all scenes were generated successfully

### Visual inconsistency between scenes
- Ensure continuity prompts are being used
- Re-describe characters and style in each scene
- Consider using more detailed scene descriptions

### FFmpeg errors
- Verify FFmpeg is installed: `ffmpeg -version`
- Check FFmpeg is in PATH
- Ensure scene files exist before concatenation

### Slow generation
- Normal: 5-10 minutes for 30-second video
- Each scene takes 1-2 minutes
- Consider async processing for better UX

## Future Improvements

- [ ] Async scene generation (parallel processing)
- [ ] Automatic audio addition (TTS or music)
- [ ] Scene transition effects
- [ ] Quality optimization per scene
- [ ] Progress tracking API
- [ ] Scene retry logic for failed scenes
