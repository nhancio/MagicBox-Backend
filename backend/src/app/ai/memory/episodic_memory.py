"""
Episodic Memory - Manages event-based memory and user interaction patterns.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.models.activity_timeline import ActivityTimeline, ActivityType
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID


class EpisodicMemory:
    """Manages episodic memory based on user activities and events."""
    
    def __init__(self, db: Session, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id or get_context(CTX_USER_ID)
        self.tenant_id = tenant_id or get_context(CTX_TENANT_ID)
    
    def get_recent_activities(
        self,
        activity_types: Optional[List[ActivityType]] = None,
        days: int = 30,
        limit: int = 50,
    ) -> List[ActivityTimeline]:
        """Get recent user activities."""
        query = self.db.query(ActivityTimeline).filter(
            ActivityTimeline.tenant_id == self.tenant_id,
            ActivityTimeline.user_id == self.user_id,
            ActivityTimeline.created_at >= datetime.utcnow() - timedelta(days=days),
        )
        
        if activity_types:
            query = query.filter(ActivityTimeline.activity_type.in_(activity_types))
        
        return query.order_by(ActivityTimeline.created_at.desc()).limit(limit).all()
    
    def get_user_patterns(self, days: int = 90) -> Dict[str, Any]:
        """Analyze user patterns from activities."""
        activities = self.get_recent_activities(days=days, limit=1000)
        
        patterns = {
            "total_activities": len(activities),
            "activity_types": {},
            "most_active_day": None,
            "most_active_hour": None,
        }
        
        day_counts = {}
        hour_counts = {}
        
        for activity in activities:
            # Count by type
            activity_type = activity.activity_type.value
            patterns["activity_types"][activity_type] = patterns["activity_types"].get(activity_type, 0) + 1
            
            # Count by day/hour
            created_at = activity.created_at
            day_name = created_at.strftime("%A")
            hour = created_at.hour
            
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if day_counts:
            patterns["most_active_day"] = max(day_counts.items(), key=lambda x: x[1])[0]
        if hour_counts:
            patterns["most_active_hour"] = max(hour_counts.items(), key=lambda x: x[1])[0]
        
        return patterns
    
    def get_preferences(self) -> Dict[str, Any]:
        """Extract user preferences from activities."""
        activities = self.get_recent_activities(days=90, limit=500)
        
        preferences = {
            "preferred_content_types": {},
            "preferred_platforms": {},
            "common_topics": [],
        }
        
        for activity in activities:
            metadata = activity.extra_metadata or {}
            
            # Extract content type preferences
            content_type = metadata.get("content_type")
            if content_type:
                preferences["preferred_content_types"][content_type] = \
                    preferences["preferred_content_types"].get(content_type, 0) + 1
            
            # Extract platform preferences
            platform = metadata.get("platform")
            if platform:
                preferences["preferred_platforms"][platform] = \
                    preferences["preferred_platforms"].get(platform, 0) + 1
        
        return preferences
