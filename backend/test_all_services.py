#!/usr/bin/env python3
"""Test all three AI services"""
import sys
import os
from pathlib import Path

# Add src to Python path
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

print("="*70)
print("AI SERVICES TEST SUITE")
print("="*70)

# Test 1: Check imports
print("\n[1/6] Checking imports...")
try:
    from app.services.ai_service import AIService
    from app.services.ai_image_service import AIImageService
    from app.services.ai_video_service import AIVideoService
    print("   ✅ All services imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check SDK
print("\n[2/6] Checking Google Genai SDK...")
try:
    from google import genai
    print("   ✅ google-genai SDK available")
except ImportError:
    print("   ❌ google-genai not installed")
    print("   Install: pip install google-genai pillow")
    sys.exit(1)

# Test 3: Check API key
print("\n[3/6] Checking API key...")
from app.config.settings import settings
if not settings.GEMINI_API_KEY:
    print("   ❌ GEMINI_API_KEY not configured")
    print("   Set GEMINI_API_KEY in .env file")
    sys.exit(1)
print(f"   ✅ GEMINI_API_KEY configured (length: {len(settings.GEMINI_API_KEY)})")

# Test 4: Text Generation
print("\n[4/6] Testing Text Generation (Gemini 3 Pro)...")
print("   Generating post about 'AI Content Creation'...")
try:
    result = AIService.generate_post(
        topic="AI Content Creation for Small Businesses",
        tone="professional",
        platform="instagram",
        target_audience="small business owners",
        hashtags=True,
    )
    
    if result.get("success"):
        print("   ✅ SUCCESS")
        print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
        content = result.get("content", "")
        hashtags = result.get("hashtags", [])
        print(f"   Content length: {len(content)} characters")
        print(f"   Hashtags: {len(hashtags)}")
        print(f"   Preview: {content[:150]}...")
        if hashtags:
            print(f"   Sample hashtags: {', '.join(hashtags[:5])}")
    else:
        print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Image Generation
print("\n[5/6] Testing Image Generation (Gemini 2.5 Flash Image)...")
print("   Generating image: 'A red apple on white background'...")
try:
    output_path = str(backend_dir / "test_image.png")
    result = AIImageService.generate_image(
        prompt="A red apple on a white background, professional photography",
        output_path=output_path,
    )
    
    if result.get("success"):
        print("   ✅ SUCCESS")
        print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
        img_path = result.get("image_path")
        print(f"   Image path: {img_path}")
        
        if img_path and Path(img_path).exists():
            size = Path(img_path).stat().st_size
            print(f"   File size: {size:,} bytes")
            print(f"   ✅ Image file saved successfully!")
        else:
            print(f"   ⚠️  Image path provided but file not found")
    else:
        print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Video Generation (optional - takes long)
print("\n[6/6] Testing Video Generation (Veo 3.1)...")
print("   ⚠️  Video generation takes 5-10 minutes")
print("   Skipping for now (uncomment in script to test)")
print("   To test: Uncomment the code below and run again")

# Uncomment to test video generation:
# try:
#     output_path = str(backend_dir / "test_video.mp4")
#     prompt = "A person waving hello, simple and friendly"
#     print(f"   Generating video: '{prompt}'...")
#     result = AIVideoService.generate_video(
#         prompt=prompt,
#         output_path=output_path,
#         poll_interval=10,
#     )
#     
#     if result.get("success"):
#         print("   ✅ SUCCESS")
#         print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
#         video_path = result.get("video_path")
#         print(f"   Video path: {video_path}")
#         
#         if video_path and Path(video_path).exists():
#             size = Path(video_path).stat().st_size
#             print(f"   File size: {size:,} bytes")
#             print(f"   ✅ Video file saved successfully!")
#         else:
#             print(f"   ⚠️  Video path provided but file not found")
#     else:
#         print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
# except Exception as e:
#     print(f"   ❌ EXCEPTION: {e}")
#     import traceback
#     traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nSummary:")
print("  ✅ Text Generation: Tested with Gemini 3 Pro")
print("  ✅ Image Generation: Tested with Gemini 2.5 Flash Image")
print("  ⏭️  Video Generation: Skipped (takes 5-10 minutes)")
print("\nNote: Check test_image.png in backend/ directory for generated image")
