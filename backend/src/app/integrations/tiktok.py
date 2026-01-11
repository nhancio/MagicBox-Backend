"""
TikTok Integration - Upload and publish videos using TikTok Marketing API.
"""
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings


class TikTokIntegration:
    """Integration for TikTok Marketing API."""
    
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"
    
    def __init__(self, access_token: str, advertiser_id: Optional[str] = None):
        self.access_token = access_token
        self.advertiser_id = advertiser_id
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for TikTok API."""
        return {
            "Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
    
    def publish_video(
        self,
        video_url: str,
        caption: str,
        privacy_level: str = "PUBLIC_TO_EVERYONE",  # PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, PRIVATE
    ) -> Dict[str, Any]:
        """
        Publish a video to TikTok.
        
        Args:
            video_url: URL to video file
            caption: Video caption
            privacy_level: Privacy setting
        
        Returns:
            Dict with video_id and video_url
        """
        if not self.advertiser_id:
            raise ValueError("TikTok advertiser_id is required")
        
        # TikTok requires video upload in multiple steps
        # Step 1: Initialize upload
        init_endpoint = f"{self.BASE_URL}/video/init/"
        
        init_data = {
            "advertiser_id": self.advertiser_id,
            "privacy_level": privacy_level,
        }
        
        init_response = httpx.post(
            init_endpoint,
            json=init_data,
            headers=self._get_headers(),
            timeout=30.0
        )
        init_response.raise_for_status()
        
        upload_url = init_response.json().get("data", {}).get("upload_url")
        publish_id = init_response.json().get("data", {}).get("publish_id")
        
        if not upload_url or not publish_id:
            raise ValueError("Failed to initialize TikTok upload")
        
        # Step 2: Upload video
        # Download video from URL
        video_response = httpx.get(video_url, timeout=300.0)
        video_response.raise_for_status()
        video_data = video_response.content
        
        # Upload to TikTok
        upload_response = httpx.put(
            upload_url,
            content=video_data,
            headers={"Content-Type": "video/mp4"},
            timeout=300.0
        )
        upload_response.raise_for_status()
        
        # Step 3: Publish video
        publish_endpoint = f"{self.BASE_URL}/video/publish/"
        
        publish_data = {
            "advertiser_id": self.advertiser_id,
            "publish_id": publish_id,
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level,
            }
        }
        
        publish_response = httpx.post(
            publish_endpoint,
            json=publish_data,
            headers=self._get_headers(),
            timeout=30.0
        )
        publish_response.raise_for_status()
        
        result = publish_response.json()
        video_id = result.get("data", {}).get("video_id")
        
        return {
            "post_id": video_id,
            "post_url": f"https://www.tiktok.com/@username/video/{video_id}" if video_id else None,
            "metadata": result,
        }
    
    def get_post_analytics(self, video_id: str) -> Dict[str, Any]:
        """Get analytics for a TikTok video."""
        if not self.advertiser_id:
            raise ValueError("TikTok advertiser_id is required")
        
        endpoint = f"{self.BASE_URL}/video/query/"
        
        params = {
            "advertiser_id": self.advertiser_id,
            "video_ids": [video_id],
        }
        
        response = httpx.get(
            endpoint,
            params=params,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        video_data = data.get("data", {}).get("videos", [])
        
        if video_data:
            stats = video_data[0].get("statistics", {})
            return {
                "likes": stats.get("like_count", 0),
                "comments": stats.get("comment_count", 0),
                "shares": stats.get("share_count", 0),
                "views": stats.get("view_count", 0),
            }
        
        return {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
        }
