"""
Social Media Platform Integrations.
"""
from app.integrations.facebook import FacebookIntegration
from app.integrations.instagram import InstagramIntegration
from app.integrations.linkedin import LinkedInIntegration
from app.integrations.twitter import TwitterIntegration
from app.integrations.tiktok import TikTokIntegration

# YouTube integration requires additional dependencies
try:
    from app.integrations.youtube import YouTubeIntegration
    __all__ = [
        "FacebookIntegration",
        "InstagramIntegration",
        "YouTubeIntegration",
        "LinkedInIntegration",
        "TwitterIntegration",
        "TikTokIntegration",
    ]
except ImportError:
    # YouTube integration not available without google-api-python-client
    __all__ = [
        "FacebookIntegration",
        "InstagramIntegration",
        "LinkedInIntegration",
        "TwitterIntegration",
        "TikTokIntegration",
    ]
