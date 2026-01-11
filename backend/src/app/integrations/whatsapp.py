"""
WhatsApp Integration - Send notifications via WhatsApp Business API.
Uses Twilio WhatsApp API or WhatsApp Business API.
"""
import httpx
from typing import Dict, Any, Optional
from app.config.settings import settings


class WhatsAppIntegration:
    """Integration for sending WhatsApp messages."""
    
    # Using Twilio WhatsApp API (can be switched to WhatsApp Business API)
    TWILIO_BASE_URL = "https://api.twilio.com/2010-04-01"
    
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize WhatsApp integration.
        
        Args:
            account_sid: Twilio Account SID (or from settings)
            auth_token: Twilio Auth Token (or from settings)
        """
        self.account_sid = account_sid or getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = auth_token or getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '')
    
    def send_message(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message.
        
        Args:
            to: Recipient WhatsApp number (format: whatsapp:+1234567890)
            message: Message text
            media_url: Optional media URL
        
        Returns:
            Dict with success status and message SID
        """
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        
        if not self.whatsapp_number:
            raise ValueError("Twilio WhatsApp number not configured. Set TWILIO_WHATSAPP_NUMBER")
        
        # Ensure 'whatsapp:' prefix
        if not to.startswith('whatsapp:'):
            to = f'whatsapp:{to}'
        
        url = f"{self.TWILIO_BASE_URL}/Accounts/{self.account_sid}/Messages.json"
        
        data = {
            "From": self.whatsapp_number,
            "To": to,
            "Body": message,
        }
        
        if media_url:
            data["MediaUrl"] = media_url
        
        response = httpx.post(
            url,
            data=data,
            auth=(self.account_sid, self.auth_token),
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message_sid": result.get("sid"),
            "status": result.get("status"),
            "to": result.get("to"),
        }
    
    def send_notification(
        self,
        phone_number: str,
        post_title: str,
        scheduled_time: str,
        platform: str,
        post_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a pre-post notification.
        
        Args:
            phone_number: User's WhatsApp number
            post_title: Title/content preview of the post
            scheduled_time: When the post will be published (formatted)
            platform: Social media platform
            post_url: Optional preview URL
        
        Returns:
            Dict with success status
        """
        message = f"""🔔 MagicBox Post Reminder

Your scheduled post is going live in 1 hour!

📝 Post: {post_title[:50]}{'...' if len(post_title) > 50 else ''}
📅 Time: {scheduled_time}
🌐 Platform: {platform}

You can view or edit it in your MagicBox dashboard.
"""
        
        if post_url:
            message += f"\n🔗 Preview: {post_url}"
        
        return self.send_message(to=phone_number, message=message)
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Format phone number for WhatsApp (add country code if missing).
        
        Args:
            phone: Phone number (can be with or without country code)
        
        Returns:
            Formatted phone number
        """
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # If no +, assume it needs country code (default to +1 for US)
        if not cleaned.startswith('+'):
            # Try to detect country code or default
            if len(cleaned) == 10:
                cleaned = f'+1{cleaned}'  # US default
            else:
                cleaned = f'+{cleaned}'
        
        return cleaned
