"""
YouTube Integration - Upload videos and manage content using YouTube Data API v3.
"""
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings

# Optional imports for YouTube API
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    Credentials = None
    build = None
    MediaFileUpload = None


class YouTubeIntegration:
    """Integration for YouTube Data API v3."""
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        if not YOUTUBE_AVAILABLE:
            raise ImportError("Google API client libraries not installed. Install: pip install google-api-python-client google-auth google-auth-oauthlib")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._service = None
    
    def _get_service(self):
        """Get YouTube API service client."""
        if self._service is None:
            credentials = Credentials(
                token=self.access_token,
                refresh_token=self.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
            )
            self._service = build(
                self.API_SERVICE_NAME,
                self.API_VERSION,
                credentials=credentials
            )
        return self._service
    
    def upload_video(
        self,
        video_file_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "private",  # private, unlisted, public
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube.
        
        Args:
            video_file_path: Path to video file
            title: Video title
            description: Video description
            tags: Optional list of tags
            category_id: YouTube category ID
            privacy_status: private, unlisted, or public
        
        Returns:
            Dict with video_id and video_url
        """
        service = self._get_service()
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }
        
        media = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)
        
        insert_request = service.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        # Execute upload
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        
        return {
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
            "metadata": response,
        }
    
    def upload_video_from_url(
        self,
        video_url: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "private",
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube from a URL.
        Downloads the video first, then uploads.
        """
        import tempfile
        import os
        
        # Download video
        response = httpx.get(video_url, timeout=300.0)
        response.raise_for_status()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        try:
            result = self.upload_video(
                video_file_path=tmp_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
            )
        finally:
            os.unlink(tmp_path)
        
        return result
    
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """Get analytics for a YouTube video."""
        service = self._get_service()
        
        # Get video statistics
        video_response = service.videos().list(
            part='statistics,snippet',
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            raise ValueError(f"Video {video_id} not found")
        
        video = video_response['items'][0]
        stats = video.get('statistics', {})
        
        return {
            "views": int(stats.get('viewCount', 0)),
            "likes": int(stats.get('likeCount', 0)),
            "comments": int(stats.get('commentCount', 0)),
            "shares": 0,  # YouTube API doesn't provide share count directly
        }
