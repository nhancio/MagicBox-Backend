"""Quick test - run this to test all services"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing AI Services...\n")

# Test imports
try:
    from app.services.ai_service import AIService
    from app.services.ai_image_service import AIImageService
    from app.services.ai_video_service import AIVideoService
    from app.config.settings import settings
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Check API key
if not settings.GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set")
    sys.exit(1)
print(f"✅ API key configured ({len(settings.GEMINI_API_KEY)} chars)\n")

# Test 1: Text
print("1. Testing TEXT generation (Gemini 3 Pro)...")
try:
    result = AIService.generate_post(topic="Test post", tone="professional")
    if result.get("success"):
        print(f"   ✅ SUCCESS - Content: {len(result.get('content', ''))} chars")
    else:
        print(f"   ❌ FAILED: {result.get('error')}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 2: Image
print("\n2. Testing IMAGE generation (Gemini 2.5 Flash Image)...")
try:
    result = AIImageService.generate_image(
        prompt="A simple red circle on white background",
        output_path="test_img.png"
    )
    if result.get("success"):
        print(f"   ✅ SUCCESS - Image saved to: {result.get('image_path')}")
    else:
        print(f"   ❌ FAILED: {result.get('error')}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 3: Video (skip - takes too long)
print("\n3. Testing VIDEO generation (Veo 3.1)...")
print("   ⏭️  SKIPPED (takes 5-10 minutes)")
print("   Uncomment in script to test")

print("\n✅ Tests complete!")
