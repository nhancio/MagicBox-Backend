"""
Facebook Integration - Post to Facebook Pages using Graph API.
"""
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings


class FacebookIntegration:
    """Integration for Facebook Graph API."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish a post to Facebook.
        
        Args:
            content: Post text content
            media_urls: Optional list of image/video URLs
            page_id: Facebook Page ID (if posting to page)
        
        Returns:
            Dict with post_id and post_url
        """
        if page_id:
            endpoint = f"{self.BASE_URL}/{page_id}/feed"
        else:
            # Post to user's timeline (requires 'me' endpoint)
            endpoint = f"{self.BASE_URL}/me/feed"
        
        data = {
            "message": content,
            "access_token": self.access_token,
        }
        
        # Add media if provided
        if media_urls:
            if len(media_urls) == 1:
                # Single image
                data["url"] = media_urls[0]
            else:
                # Multiple images - use photos endpoint
                # First upload photos, then create post with photo IDs
                photo_ids = []
                for url in media_urls:
                    photo_data = {
                        "url": url,
                        "access_token": self.access_token,
                    }
                    photo_response = httpx.post(
                        f"{self.BASE_URL}/{page_id or 'me'}/photos",
                        data=photo_data,
                        timeout=30.0
                    )
                    if photo_response.status_code == 200:
                        photo_ids.append(photo_response.json().get("id"))
                
                if photo_ids:
                    data["attached_media"] = [{"media_fbid": pid} for pid in photo_ids]
        
        response = httpx.post(endpoint, data=data, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        post_id = result.get("id")
        
        return {
            "post_id": post_id,
            "post_url": f"https://www.facebook.com/{post_id}" if post_id else None,
            "metadata": result,
        }
    
    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a Facebook post."""
        endpoint = f"{self.BASE_URL}/{post_id}"
        
        params = {
            "fields": "likes.summary(true),comments.summary(true),shares,reactions.summary(true)",
            "access_token": self.access_token,
        }
        
        response = httpx.get(endpoint, params=params, timeout=30.0)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
            "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
            "shares": data.get("shares", {}).get("count", 0),
            "reactions": data.get("reactions", {}).get("summary", {}).get("total_count", 0),
            "views": 0,  # Facebook doesn't provide view count in basic API
        }
    
    def get_user_pages(self) -> List[Dict[str, Any]]:
        """Get list of Facebook Pages the user manages."""
        endpoint = f"{self.BASE_URL}/me/accounts"
        
        params = {
            "access_token": self.access_token,
            "fields": "id,name,access_token",
        }
        
        response = httpx.get(endpoint, params=params, timeout=30.0)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
