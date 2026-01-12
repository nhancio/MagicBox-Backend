"""
AI Video Generation Service - Using Veo 3.1 for video/reel generation.
Generates 30-second videos by creating multiple 5-8 second scenes and stitching them together.
"""
from typing import Optional, Dict, Any, List
from app.config.settings import settings
from pathlib import Path
import time
import tempfile
import os
import subprocess
import json

# Optional import for new Google Genai SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class AIVideoService:
    """Service for AI-powered video generation using Veo 3.1."""
    
    _client: Optional[Any] = None
    
    @classmethod
    def _get_client(cls):
        """Initialize and return Gemini client."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai not installed. Install: pip install google-genai")
        
        if cls._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured in environment variables")
            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return cls._client
    
    @staticmethod
    def _find_ffmpeg() -> Optional[str]:
        """
        Find FFmpeg executable path.
        Checks PATH first, then common installation locations.
        
        Returns:
            Path to ffmpeg executable, or None if not found
        """
        import platform
        import shutil
        
        # First, try to find in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # If not in PATH, check common Windows locations
        if platform.system() == "Windows":
            common_paths = [
                r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",  # Chocolatey (most common)
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                r"C:\tools\ffmpeg\bin\ffmpeg.exe",
                os.path.expanduser(r"~\AppData\Local\ffmpeg\bin\ffmpeg.exe"),
            ]
            for path in common_paths:
                if Path(path).exists():
                    return str(path)
        
        # Check common Linux/Mac locations
        elif platform.system() in ["Linux", "Darwin"]:
            common_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",  # macOS Apple Silicon
            ]
            for path in common_paths:
                if Path(path).exists():
                    return path
        
        return None
    
    @staticmethod
    def _check_ffmpeg() -> tuple:
        """
        Check if FFmpeg is available.
        
        Returns:
            Tuple of (is_available, error_message, ffmpeg_path)
        """
        ffmpeg_path = AIVideoService._find_ffmpeg()
        
        if not ffmpeg_path:
            return False, (
                "FFmpeg is not installed or not found. "
                "Please install FFmpeg:\n"
                "- Windows: See backend/INSTALL_FFMPEG_WINDOWS.md\n"
                "- Linux: sudo apt install ffmpeg\n"
                "- macOS: brew install ffmpeg\n"
                "After installation, restart your terminal and server."
            ), None
        
        # Verify it actually works
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                check=True,
                timeout=5,
                text=True
            )
            return True, None, ffmpeg_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return False, f"FFmpeg found at {ffmpeg_path} but failed to execute: {str(e)}", ffmpeg_path
    
    @staticmethod
    def _plan_scenes(total_duration: int, script_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Plan scenes for video generation.
        Breaks total duration into 5-6 scenes of 5-8 seconds each.
        
        Args:
            total_duration: Total video duration in seconds (e.g., 30)
            script_data: Optional script data with scenes/hook/script
        
        Returns:
            List of scene plans with timing and prompts
        """
        scenes = []
        scene_duration = 6  # 6 seconds per scene (optimal for Veo)
        num_scenes = (total_duration + scene_duration - 1) // scene_duration  # Ceiling division
        
        # Extract script information if available
        hook = script_data.get("hook", "") if script_data else ""
        script_text = script_data.get("script", "") if script_data else ""
        script_scenes = script_data.get("scenes", []) if script_data else []
        
        # Build base continuity description from script
        continuity_base = f"Style: Professional, engaging, suitable for social media marketing. "
        if hook:
            continuity_base += f"Opening hook: {hook}. "
        
        for i in range(num_scenes):
            start_time = i * scene_duration
            end_time = min((i + 1) * scene_duration, total_duration)
            actual_duration = end_time - start_time
            
            # Get scene-specific content if available
            scene_prompt = ""
            if script_scenes and i < len(script_scenes):
                scene_info = script_scenes[i]
                if isinstance(scene_info, dict):
                    visual = scene_info.get("visual", scene_info.get("visual_cue", ""))
                    dialogue = scene_info.get("dialogue", "")
                    scene_prompt = f"{visual}. {dialogue}"
                else:
                    scene_prompt = str(scene_info)
            else:
                # Fallback: extract relevant portion from script
                words_per_scene = len(script_text.split()) // num_scenes if script_text else 0
                start_word = i * words_per_scene
                end_word = (i + 1) * words_per_scene
                script_words = script_text.split() if script_text else []
                scene_prompt = " ".join(script_words[start_word:end_word]) if script_words else ""
            
            # Build full prompt with continuity
            if i == 0:
                # First scene: establish style
                full_prompt = f"""Cinematic marketing video scene ({actual_duration} seconds).
{continuity_base}
{scene_prompt if scene_prompt else f"Opening scene establishing the main message: {script_text[:100] if script_text else 'Professional marketing content'}"}
Camera: Smooth, professional movement. Ultra-realistic lighting."""
            elif i == num_scenes - 1:
                # Last scene: resolution/CTA
                full_prompt = f"""Cinematic marketing video scene ({actual_duration} seconds).
{continuity_base}
Continuation of the same scene and visual style. Lighting and camera style remain identical.
{scene_prompt if scene_prompt else "Closing scene with call to action or resolution."}
Camera: Maintains same style as previous scenes."""
            else:
                # Middle scenes: maintain continuity
                full_prompt = f"""Cinematic marketing video scene ({actual_duration} seconds).
{continuity_base}
Continuation of the same scene and visual style. Lighting and camera style remain identical.
{scene_prompt if scene_prompt else f"Continuing the narrative: {script_text[:100] if script_text else 'Professional marketing content'}"}
Camera: Smooth transition from previous scene, maintains consistent style."""
            
            scenes.append({
                "scene_number": i + 1,
                "start_time": start_time,
                "end_time": end_time,
                "duration": actual_duration,
                "prompt": full_prompt,
            })
        
        return scenes
    
    @staticmethod
    def _generate_single_scene(
        prompt: str,
        duration: int,
        scene_number: int,
        temp_dir: Path,
        poll_interval: int = 10,
    ) -> Optional[str]:
        """
        Generate a single scene video (5-8 seconds).
        
        Returns:
            Path to saved scene video, or None if failed
        """
        try:
            client = AIVideoService._get_client()
            
            print(f"Generating scene {scene_number} ({duration}s)...")
            
            # Start video generation with veo-3.1-generate-preview
            operation = client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=prompt,
            )
            
            # Poll the operation status until the video is ready
            while not operation.done:
                print(f"  Waiting for scene {scene_number}... (operation: {operation.name})")
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
            
            if not operation.response or not operation.response.generated_videos:
                print(f"  Scene {scene_number} generation failed: No video in response")
                return None
            
            # Download the generated video
            generated_video = operation.response.generated_videos[0]
            scene_path = temp_dir / f"scene_{scene_number:02d}.mp4"
            
            # Download video file
            try:
                video_data = client.files.download(file=generated_video.video)
                
                # Handle different return types
                if isinstance(video_data, bytes):
                    with open(scene_path, 'wb') as f:
                        f.write(video_data)
                elif hasattr(video_data, 'save'):
                    video_data.save(str(scene_path))
                elif hasattr(video_data, 'read'):
                    with open(scene_path, 'wb') as f:
                        chunk = video_data.read(8192)
                        while chunk:
                            f.write(chunk)
                            chunk = video_data.read(8192)
                elif hasattr(video_data, 'content'):
                    content = video_data.content
                    with open(scene_path, 'wb') as f:
                        f.write(content if isinstance(content, bytes) else bytes(content))
                else:
                    # Last resort
                    with open(scene_path, 'wb') as f:
                        f.write(bytes(video_data))
                
                if scene_path.exists():
                    print(f"  Scene {scene_number} saved: {scene_path}")
                    return str(scene_path)
                else:
                    print(f"  Scene {scene_number} file not created")
                    return None
                    
            except Exception as e:
                print(f"  Scene {scene_number} download error: {str(e)}")
                return None
                
        except Exception as e:
            print(f"  Scene {scene_number} generation error: {str(e)}")
            return None
    
    @staticmethod
    def _concatenate_videos(scene_paths: List[str], output_path: str) -> bool:
        """
        Concatenate multiple video files into one using FFmpeg.
        
        Args:
            scene_paths: List of paths to scene video files
            output_path: Path to save the final concatenated video
        
        Returns:
            True if successful, False otherwise
        """
        is_available, error_msg, ffmpeg_path = AIVideoService._check_ffmpeg()
        if not is_available or not ffmpeg_path:
            raise RuntimeError(error_msg or "FFmpeg is not available")
        
        # Create a temporary file list for FFmpeg concat
        temp_dir = Path(output_path).parent
        concat_file = temp_dir / "concat_list.txt"
        
        # Write file list (FFmpeg concat format)
        with open(concat_file, 'w', encoding='utf-8') as f:
            for scene_path in scene_paths:
                # Escape single quotes and use absolute path
                abs_path = Path(scene_path).absolute()
                f.write(f"file '{abs_path}'\n")
        
        try:
            
            # Use FFmpeg to concatenate videos
            cmd = [
                ffmpeg_path,  # Use full path instead of just "ffmpeg"
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",  # Copy codec (fast, no re-encoding)
                "-y",  # Overwrite output file
                output_path
            ]
            
            print(f"Concatenating {len(scene_paths)} scenes with FFmpeg...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"Video concatenated successfully: {output_path}")
                return True
            else:
                print(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("FFmpeg concatenation timed out")
            return False
        except Exception as e:
            print(f"FFmpeg concatenation error: {str(e)}")
            return False
        finally:
            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()
    
    @staticmethod
    def generate_video(
        prompt: str,
        output_path: Optional[str] = None,
        duration_seconds: int = 30,
        script_data: Optional[Dict[str, Any]] = None,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate a 30-second video using Veo 3.1 by creating multiple scenes and stitching them.
        
        Args:
            prompt: Base video generation prompt (used for context)
            output_path: Optional path to save the final video
            duration_seconds: Total video duration (default: 30)
            script_data: Optional script data with scenes/hook/script for better scene planning
            poll_interval: Seconds between polling for completion
        
        Returns:
            Dict with video path, operation status, and metadata
        """
        try:
            # Plan scenes
            scenes = AIVideoService._plan_scenes(duration_seconds, script_data)
            print(f"Planning {len(scenes)} scenes for {duration_seconds}-second video...")
            
            # Create temp directory for scenes
            temp_dir = Path(tempfile.gettempdir()) / f"video_gen_{abs(hash(prompt))}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate each scene
            scene_paths = []
            failed_scenes = []
            
            for scene in scenes:
                scene_path = AIVideoService._generate_single_scene(
                    prompt=scene["prompt"],
                    duration=scene["duration"],
                    scene_number=scene["scene_number"],
                    temp_dir=temp_dir,
                    poll_interval=poll_interval,
                )
                
                if scene_path:
                    scene_paths.append(scene_path)
                else:
                    failed_scenes.append(scene["scene_number"])
            
            if not scene_paths:
                return {
                    "success": False,
                    "error": "All scenes failed to generate",
                    "video_path": None
                }
            
            if failed_scenes:
                print(f"Warning: {len(failed_scenes)} scenes failed: {failed_scenes}")
            
            # Determine final output path
            if output_path:
                final_path = output_path
                output_dir = Path(output_path).parent
                if output_dir and not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)
            else:
                temp_dir_final = Path(tempfile.gettempdir())
                temp_dir_final.mkdir(parents=True, exist_ok=True)
                final_path = str(temp_dir_final / f"generated_video_{abs(hash(prompt))}.mp4")
            
            # Concatenate scenes
            if not AIVideoService._concatenate_videos(scene_paths, final_path):
                return {
                    "success": False,
                    "error": "Failed to concatenate video scenes",
                    "video_path": None,
                    "scene_paths": scene_paths,  # Return scene paths in case user wants to stitch manually
                }
            
            # Clean up individual scene files (optional - comment out if you want to keep them)
            # for scene_path in scene_paths:
            #     try:
            #         Path(scene_path).unlink()
            #     except:
            #         pass
            
            # Verify final file
            if not Path(final_path).exists():
                return {
                    "success": False,
                    "error": "Final video file was not created",
                    "video_path": None,
                }
            
            file_size = Path(final_path).stat().st_size
            
            return {
                "success": True,
                "video_path": final_path,
                "prompt": prompt,
                "metadata": {
                    "model": "veo-3.1-generate-preview",
                    "duration_seconds": duration_seconds,
                    "num_scenes": len(scene_paths),
                    "failed_scenes": failed_scenes,
                    "file_size_bytes": file_size,
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "video_path": None
            }
