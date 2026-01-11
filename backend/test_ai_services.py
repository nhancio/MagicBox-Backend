"""
Test script for AI Services:
1. AIService (Gemini 3 Pro) - Text generation
2. AIImageService (Gemini 2.5 Flash Image) - Image generation
3. AIVideoService (Veo 3.1) - Video generation
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.services.ai_service import AIService
from app.services.ai_image_service import AIImageService
from app.services.ai_video_service import AIVideoService
from app.config.settings import settings

def test_text_generation():
    """Test AIService with Gemini 3 Pro for text generation."""
    print("\n" + "="*60)
    print("TEST 1: Text Generation (Gemini 3 Pro)")
    print("="*60)
    
    try:
        result = AIService.generate_post(
            topic="5 Tips for Small Business Marketing",
            tone="professional",
            platform="instagram",
            target_audience="small business owners",
            hashtags=True,
        )
        
        if result.get("success"):
            print("✅ Text Generation: SUCCESS")
            print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
            print(f"   Content Length: {len(result.get('content', ''))} chars")
            print(f"   Hashtags: {len(result.get('hashtags', []))} hashtags")
            print(f"\n   Content Preview:")
            print(f"   {result.get('content', '')[:200]}...")
            return True
        else:
            print(f"❌ Text Generation: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Text Generation: EXCEPTION")
        print(f"   Error: {str(e)}")
        return False


def test_image_generation():
    """Test AIImageService with Gemini 2.5 Flash Image."""
    print("\n" + "="*60)
    print("TEST 2: Image Generation (Gemini 2.5 Flash Image)")
    print("="*60)
    
    try:
        prompt = "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
        output_path = "test_generated_image.png"
        
        result = AIImageService.generate_image(
            prompt=prompt,
            output_path=output_path,
        )
        
        if result.get("success"):
            print("✅ Image Generation: SUCCESS")
            print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
            print(f"   Image Path: {result.get('image_path', 'N/A')}")
            print(f"   Prompt: {prompt[:80]}...")
            
            # Check if file exists
            if result.get("image_path") and Path(result.get("image_path")).exists():
                file_size = Path(result.get("image_path")).stat().st_size
                print(f"   File Size: {file_size} bytes")
                print(f"   ✅ Image file saved successfully!")
            else:
                print(f"   ⚠️  Image path provided but file not found")
            
            return True
        else:
            print(f"❌ Image Generation: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Image Generation: EXCEPTION")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_video_generation():
    """Test AIVideoService with Veo 3.1."""
    print("\n" + "="*60)
    print("TEST 3: Video Generation (Veo 3.1)")
    print("="*60)
    
    try:
        prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""
        
        output_path = "test_generated_video.mp4"
        
        print(f"   Starting video generation...")
        print(f"   Prompt: {prompt[:100]}...")
        print(f"   This may take several minutes...")
        
        result = AIVideoService.generate_video(
            prompt=prompt,
            output_path=output_path,
            poll_interval=10,  # Check every 10 seconds
        )
        
        if result.get("success"):
            print("✅ Video Generation: SUCCESS")
            print(f"   Model: {result.get('metadata', {}).get('model', 'unknown')}")
            print(f"   Video Path: {result.get('video_path', 'N/A')}")
            print(f"   Operation: {result.get('operation_name', 'N/A')}")
            
            # Check if file exists
            if result.get("video_path") and Path(result.get("video_path")).exists():
                file_size = Path(result.get("video_path")).stat().st_size
                print(f"   File Size: {file_size} bytes")
                print(f"   ✅ Video file saved successfully!")
            else:
                print(f"   ⚠️  Video path provided but file not found")
            
            return True
        else:
            print(f"❌ Video Generation: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Video Generation: EXCEPTION")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AI SERVICES TEST SUITE")
    print("="*60)
    print(f"GEMINI_API_KEY configured: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    
    if not settings.GEMINI_API_KEY:
        print("\n❌ ERROR: GEMINI_API_KEY not configured!")
        print("   Please set GEMINI_API_KEY in your .env file")
        return
    
    results = {
        "text": False,
        "image": False,
        "video": False,
    }
    
    # Test 1: Text Generation
    results["text"] = test_text_generation()
    
    # Test 2: Image Generation
    results["image"] = test_image_generation()
    
    # Test 3: Video Generation (may take longer)
    print("\n⚠️  Note: Video generation can take 5-10 minutes. Continue? (y/n)")
    # For automated testing, we'll skip video by default
    # Uncomment the next line to test video generation
    # results["video"] = test_video_generation()
    print("   Skipping video test (uncomment in script to test)")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Text Generation (Gemini 3 Pro):  {'✅ PASS' if results['text'] else '❌ FAIL'}")
    print(f"Image Generation (Gemini 2.5):    {'✅ PASS' if results['image'] else '❌ FAIL'}")
    print(f"Video Generation (Veo 3.1):       {'✅ PASS' if results['video'] else '⏭️  SKIPPED'}")
    
    total = sum(1 for v in results.values() if v)
    print(f"\nTotal: {total}/3 tests passed")
    
    if results["text"] and results["image"]:
        print("\n✅ Core services (text + image) are working!")
    else:
        print("\n❌ Some services failed. Check errors above.")


if __name__ == "__main__":
    main()
