"""
LinkedIn Integration - Post content using LinkedIn API v2.
"""
import httpx
from typing import Dict, Any, List, Optional
from app.config.settings import settings


class LinkedInIntegration:
    """Integration for LinkedIn API v2."""
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for LinkedIn API."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
    
    def publish_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        visibility: str = "PUBLIC",  # PUBLIC or CONNECTIONS
    ) -> Dict[str, Any]:
        """
        Publish a post to LinkedIn.
        
        Args:
            content: Post text content
            media_urls: Optional list of image URLs
            visibility: PUBLIC or CONNECTIONS
        
        Returns:
            Dict with post_id and post_url
        """
        # Get user's URN (Universal Resource Name)
        user_urn = self._get_user_urn()
        
        # Create share content
        share_data = {
            "author": user_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE" if not media_urls else "IMAGE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        # Add media if provided
        if media_urls:
            media_assets = []
            for url in media_urls[:9]:  # LinkedIn allows max 9 images
                # Register image
                image_urn = self._register_image(url)
                if image_urn:
                    media_assets.append({
                        "status": "READY",
                        "media": image_urn,
                    })
            
            if media_assets:
                share_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets
        
        endpoint = f"{self.BASE_URL}/ugcPosts"
        
        response = httpx.post(
            endpoint,
            json=share_data,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        post_id = result.get("id")
        
        return {
            "post_id": post_id,
            "post_url": None,  # LinkedIn doesn't provide direct URL in response
            "metadata": result,
        }
    
    def _get_user_urn(self) -> str:
        """Get user's LinkedIn URN."""
        endpoint = f"{self.BASE_URL}/me"
        
        response = httpx.get(
            endpoint,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        return f"urn:li:person:{data.get('id')}"
    
    def _register_image(self, image_url: str) -> Optional[str]:
        """Register an image with LinkedIn and return URN."""
        # Download image
        image_response = httpx.get(image_url, timeout=30.0)
        image_response.raise_for_status()
        image_data = image_response.content
        
        # Upload to LinkedIn
        upload_endpoint = "https://api.linkedin.com/v2/assets?action=registerUpload"
        
        upload_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": self._get_user_urn(),
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }
        
        response = httpx.post(
            upload_endpoint,
            json=upload_data,
            headers=self._get_headers(),
            timeout=30.0
        )
        response.raise_for_status()
        
        upload_data = response.json()
        upload_url = upload_data.get("value", {}).get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")
        asset = upload_data.get("value", {}).get("asset")
        
        if upload_url and asset:
            # Upload image
            upload_response = httpx.put(
                upload_url,
                content=image_data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=30.0
            )
            upload_response.raise_for_status()
            
            return asset
        
        return None
    
    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for a LinkedIn post."""
        # LinkedIn analytics require different endpoints
        # This is a simplified version
        endpoint = f"{self.BASE_URL}/socialActions/{post_id}"
        
        response = httpx.get(
            endpoint,
            headers=self._get_headers(),
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                "comments": data.get("commentsSummary", {}).get("totalComments", 0),
                "shares": data.get("sharesSummary", {}).get("totalShares", 0),
                "views": 0,  # Requires separate analytics API
            }
        
        return {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
        }
