"""
Instagram Integration - Post to Instagram Business accounts using Graph API.
"""
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings


class InstagramIntegration:
    """Integration for Instagram Graph API."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str, instagram_account_id: Optional[str] = None):
        self.access_token = access_token
        self.instagram_account_id = instagram_account_id
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        instagram_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish a post to Instagram.
        
        Args:
            content: Post caption
            media_urls: List of image URLs (single image for feed post)
            instagram_account_id: Instagram Business Account ID
        
        Returns:
            Dict with post_id and post_url
        """
        account_id = instagram_account_id or self.instagram_account_id
        if not account_id:
            raise ValueError("Instagram Business Account ID is required")
        
        if not media_urls or len(media_urls) == 0:
            raise ValueError("Instagram posts require at least one image")
        
        # Step 1: Create media container
        media_url = media_urls[0]  # Instagram feed posts support single image
        
        container_data = {
            "image_url": media_url,
            "caption": content,
            "access_token": self.access_token,
        }
        
        container_response = httpx.post(
            f"{self.BASE_URL}/{account_id}/media",
            data=container_data,
            timeout=30.0
        )
        container_response.raise_for_status()
        container_id = container_response.json().get("id")
        
        # Step 2: Publish the media container
        publish_data = {
            "creation_id": container_id,
            "access_token": self.access_token,
        }
        
        publish_response = httpx.post(
            f"{self.BASE_URL}/{account_id}/media_publish",
            data=publish_data,
            timeout=30.0
        )
        publish_response.raise_for_status()
        
        result = publish_response.json()
        post_id = result.get("id")
        
        return {
            "post_id": post_id,
            "post_url": f"https://www.instagram.com/p/{post_id}/" if post_id else None,
            "metadata": result,
        }
    
    def publish_reel(
        self,
        content: str,
        video_url: str,
        cover_url: Optional[str] = None,
        instagram_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a reel to Instagram."""
        account_id = instagram_account_id or self.instagram_account_id
        if not account_id:
            raise ValueError("Instagram Business Account ID is required")
        
        # Create reel container
        container_data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": content,
            "access_token": self.access_token,
        }
        
        if cover_url:
            container_data["thumb_offset"] = 0  # Use first frame or cover
        
        container_response = httpx.post(
            f"{self.BASE_URL}/{account_id}/media",
            data=container_data,
            timeout=60.0  # Longer timeout for video upload
        )
        container_response.raise_for_status()
        container_id = container_response.json().get("id")
        
        # Wait for processing (Instagram requires this for videos)
        # In production, use webhooks or polling
        
        # Publish
        publish_data = {
            "creation_id": container_id,
            "access_token": self.access_token,
        }
        
        publish_response = httpx.post(
            f"{self.BASE_URL}/{account_id}/media_publish",
            data=publish_data,
            timeout=60.0
        )
        publish_response.raise_for_status()
        
        result = publish_response.json()
        post_id = result.get("id")
        
        return {
            "post_id": post_id,
            "post_url": f"https://www.instagram.com/reel/{post_id}/" if post_id else None,
            "metadata": result,
        }
    
    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for an Instagram post."""
        endpoint = f"{self.BASE_URL}/{post_id}"
        
        params = {
            "fields": "like_count,comments_count,engagement",
            "access_token": self.access_token,
        }
        
        response = httpx.get(endpoint, params=params, timeout=30.0)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "likes": data.get("like_count", 0),
            "comments": data.get("comments_count", 0),
            "shares": 0,  # Instagram doesn't provide share count
            "views": data.get("engagement", {}).get("reach", 0),
        }
