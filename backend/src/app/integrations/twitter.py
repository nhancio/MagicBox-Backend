"""
Twitter/X Integration - Post tweets using Twitter API v2.
"""
import httpx
import base64
from typing import Dict, Any, List, Optional
from app.config.settings import settings


class TwitterIntegration:
    """Integration for Twitter API v2."""
    
    BASE_URL = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1"
    
    def __init__(self, access_token: str, access_token_secret: Optional[str] = None):
        self.access_token = access_token
        self.access_token_secret = access_token_secret
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Twitter API."""
        # For OAuth 2.0 Bearer token
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Publish a tweet to Twitter/X.
        
        Args:
            content: Tweet text (max 280 characters)
            media_urls: Optional list of image URLs
        
        Returns:
            Dict with tweet_id and tweet_url
        """
        if len(content) > 280:
            raise ValueError("Twitter posts are limited to 280 characters")
        
        endpoint = f"{self.BASE_URL}/tweets"
        
        data = {
            "text": content,
        }
        
        # Add media if provided
        if media_urls:
            # Upload media first, then attach to tweet
            media_ids = []
            for url in media_urls[:4]:  # Twitter allows max 4 images
                media_id = self._upload_media(url)
                if media_id:
                    media_ids.append(media_id)
            
            if media_ids:
                data["media"] = {"media_ids": media_ids}
        
        response = httpx.post(
            endpoint,
            json=data,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        tweet_data = result.get("data", {})
        tweet_id = tweet_data.get("id")
        
        return {
            "post_id": tweet_id,
            "post_url": f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else None,
            "metadata": result,
        }
    
    def _upload_media(self, media_url: str) -> Optional[str]:
        """Upload media to Twitter and return media_id."""
        # Download media
        media_response = httpx.get(media_url, timeout=30.0)
        media_response.raise_for_status()
        media_data = media_response.content
        
        # Upload to Twitter
        upload_endpoint = f"{self.UPLOAD_URL}/media/upload.json"
        
        files = {
            "media": media_data
        }
        
        # Twitter requires OAuth 1.0a for media upload
        # For simplicity, we'll use a simplified approach
        # In production, implement full OAuth 1.0a signing
        response = httpx.post(
            upload_endpoint,
            files=files,
            timeout=30.0
        )
        
        if response.status_code == 200:
            return response.json().get("media_id_string")
        
        return None
    
    def get_post_analytics(self, tweet_id: str) -> Dict[str, Any]:
        """Get analytics for a Twitter post."""
        endpoint = f"{self.BASE_URL}/tweets/{tweet_id}"
        
        params = {
            "tweet.fields": "public_metrics",
        }
        
        response = httpx.get(
            endpoint,
            params=params,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        tweet = data.get("data", {})
        metrics = tweet.get("public_metrics", {})
        
        return {
            "likes": metrics.get("like_count", 0),
            "comments": metrics.get("reply_count", 0),
            "shares": metrics.get("retweet_count", 0),
            "views": metrics.get("impression_count", 0),
        }
