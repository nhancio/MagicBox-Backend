"""
Analytics API - Aggregated metrics for dashboard/analytics pages.
Computed from persisted DB data (social_posts, artifacts, social_accounts).
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.social_account import SocialAccount
from app.db.models.artifact import Artifact
from app.dependencies.auth import get_current_user, require_project


router = APIRouter(prefix="/projects/{project_id}/analytics", tags=["Analytics"])


@router.get("/overview")
def analytics_overview(
    project_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Return aggregated metrics for the Analytics + Dashboard pages.
    All numbers are derived from DB rows (no mock).
    """
    try:
        tenant_id = current_user.tenant_id
        since = datetime.utcnow() - timedelta(days=days)

        # Social metrics (published + scheduled; metrics mostly meaningful for published)
        posts_q = db.query(SocialPost).filter(SocialPost.tenant_id == tenant_id)

        total_posts = posts_q.count()
        published_posts = posts_q.filter(SocialPost.status == PostStatus.PUBLISHED).count()
        scheduled_posts = posts_q.filter(SocialPost.status == PostStatus.SCHEDULED).count()

        metrics_row = (
            db.query(
                func.coalesce(func.sum(SocialPost.views_count), 0).label("views"),
                func.coalesce(func.sum(SocialPost.likes_count), 0).label("likes"),
                func.coalesce(func.sum(SocialPost.comments_count), 0).label("comments"),
                func.coalesce(func.sum(SocialPost.shares_count), 0).label("shares"),
            )
            .filter(SocialPost.tenant_id == tenant_id)
            .one()
        )

        total_impressions = int(metrics_row.views or 0)
        total_engagements = int((metrics_row.likes or 0) + (metrics_row.comments or 0) + (metrics_row.shares or 0))
        engagement_rate = (total_engagements / total_impressions * 100.0) if total_impressions > 0 else 0.0

        # AI artifacts generated (created in DB by content/chat endpoints)
        artifacts_total = db.query(Artifact).filter(Artifact.tenant_id == tenant_id).count()
        artifacts_last_period = (
            db.query(Artifact)
            .filter(Artifact.tenant_id == tenant_id, Artifact.created_at >= since)
            .count()
        )

        # Platform breakdown (counts by platform using join to social_accounts)
        platform_rows = (
            db.query(
                SocialAccount.platform.label("platform"),
                func.count(SocialPost.id).label("posts"),
                func.coalesce(func.sum(SocialPost.views_count), 0).label("views"),
                func.coalesce(func.sum(SocialPost.likes_count), 0).label("likes"),
                func.coalesce(func.sum(SocialPost.comments_count), 0).label("comments"),
                func.coalesce(func.sum(SocialPost.shares_count), 0).label("shares"),
            )
            .join(SocialAccount, SocialAccount.id == SocialPost.social_account_id)
            .filter(SocialPost.tenant_id == tenant_id)
            .group_by(SocialAccount.platform)
            .all()
        )

        platforms = []
        for r in platform_rows:
            p_impressions = int(r.views or 0)
            p_engagements = int((r.likes or 0) + (r.comments or 0) + (r.shares or 0))
            platforms.append(
                {
                    "platform": r.platform.value if hasattr(r.platform, "value") else str(r.platform),
                    "posts": int(r.posts or 0),
                    "impressions": p_impressions,
                    "engagements": p_engagements,
                    "engagement_rate": (p_engagements / p_impressions * 100.0) if p_impressions > 0 else 0.0,
                }
            )

        return {
            "success": True,
            "period_days": days,
            "overview": {
                "total_impressions": total_impressions,
                "total_engagements": total_engagements,
                "engagement_rate": round(engagement_rate, 2),
                "total_posts": total_posts,
                "published_posts": published_posts,
                "scheduled_posts": scheduled_posts,
                "artifacts_total": artifacts_total,
                "artifacts_last_period": artifacts_last_period,
            },
            "platforms": platforms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute analytics: {str(e)}")


@router.get("/top-content")
def analytics_top_content(
    project_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Return top content by views_count (DB-backed)."""
    try:
        tenant_id = current_user.tenant_id
        posts = (
            db.query(SocialPost, SocialAccount)
            .join(SocialAccount, SocialAccount.id == SocialPost.social_account_id)
            .filter(SocialPost.tenant_id == tenant_id)
            .order_by(SocialPost.views_count.desc(), SocialPost.created_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "items": [
                {
                    "id": post.id,
                    "platform": acc.platform.value,
                    "account_name": acc.account_name,
                    "content": post.content,
                    "status": post.status.value,
                    "published_at": post.published_at.isoformat() if post.published_at else None,
                    "external_url": post.external_url,
                    "metrics": {
                        "views": post.views_count,
                        "likes": post.likes_count,
                        "comments": post.comments_count,
                        "shares": post.shares_count,
                    },
                }
                for (post, acc) in posts
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load top content: {str(e)}")

