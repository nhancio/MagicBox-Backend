"""Simple test for AI services"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("="*60)
print("Testing AI Services")
print("="*60)

# Test 1: Check imports
print("\n1. Testing imports...")
try:
    from app.services.ai_service import AIService
    print("   ✅ AIService imported")
except Exception as e:
    print(f"   ❌ AIService import failed: {e}")
    sys.exit(1)

try:
    from app.services.ai_image_service import AIImageService
    print("   ✅ AIImageService imported")
except Exception as e:
    print(f"   ❌ AIImageService import failed: {e}")
    sys.exit(1)

try:
    from app.services.ai_video_service import AIVideoService
    print("   ✅ AIVideoService imported")
except Exception as e:
    print(f"   ❌ AIVideoService import failed: {e}")
    sys.exit(1)

# Test 2: Check SDK availability
print("\n2. Testing Google Genai SDK...")
try:
    from google import genai
    print("   ✅ google-genai SDK available")
except ImportError as e:
    print(f"   ❌ google-genai SDK not installed: {e}")
    print("   Install with: pip install google-genai")
    sys.exit(1)

# Test 3: Check API key
print("\n3. Checking API key...")
from app.config.settings import settings
if settings.GEMINI_API_KEY:
    print(f"   ✅ GEMINI_API_KEY configured (length: {len(settings.GEMINI_API_KEY)})")
else:
    print("   ❌ GEMINI_API_KEY not configured")
    print("   Set GEMINI_API_KEY in .env file")
    sys.exit(1)

# Test 4: Test text generation
print("\n4. Testing Text Generation (Gemini 3 Pro)...")
try:
    result = AIService.generate_post(
        topic="Test post about AI content generation",
        tone="professional",
        platform="instagram",
    )
    if result.get("success"):
        print(f"   ✅ Text generation successful")
        print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
        print(f"   Content length: {len(result.get('content', ''))} chars")
        print(f"   Preview: {result.get('content', '')[:100]}...")
    else:
        print(f"   ❌ Text generation failed: {result.get('error')}")
except Exception as e:
    print(f"   ❌ Exception: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test image generation
print("\n5. Testing Image Generation (Gemini 2.5 Flash Image)...")
try:
    result = AIImageService.generate_image(
        prompt="A simple test image of a red apple on a white background",
        output_path="test_image.png",
    )
    if result.get("success"):
        print(f"   ✅ Image generation successful")
        print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
        print(f"   Image path: {result.get('image_path', 'N/A')}")
        from pathlib import Path
        if result.get("image_path") and Path(result.get("image_path")).exists():
            size = Path(result.get("image_path")).stat().st_size
            print(f"   File size: {size} bytes")
    else:
        print(f"   ❌ Image generation failed: {result.get('error')}")
except Exception as e:
    print(f"   ❌ Exception: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test video generation (commented out - takes too long)
print("\n6. Testing Video Generation (Veo 3.1)...")
print("   ⏭️  Skipping (takes 5-10 minutes, uncomment to test)")
# try:
#     result = AIVideoService.generate_video(
#         prompt="A simple test video of a person waving hello",
#         output_path="test_video.mp4",
#         poll_interval=10,
#     )
#     if result.get("success"):
#         print(f"   ✅ Video generation successful")
#         print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
#         print(f"   Video path: {result.get('video_path', 'N/A')}")
#     else:
#         print(f"   ❌ Video generation failed: {result.get('error')}")
# except Exception as e:
#     print(f"   ❌ Exception: {e}")
#     import traceback
#     traceback.print_exc()

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
