"""
Database models - export all models for Alembic migrations.
"""
from app.db.models.user import User
from app.db.models.role import Role
from app.db.models.tenant import Tenant
from app.db.models.user_tenant_role import UserTenantRole
from app.db.models.project import Project
from app.db.models.brand_persona import BrandPersona
from app.db.models.conversation import Conversation, ConversationMessage
from app.db.models.agent import Agent
from app.db.models.run import Run, RunStatus
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus
from app.db.models.prompt_version import PromptVersion
from app.db.models.embedding import Embedding, EmbeddingType, EmbeddingSource
from app.db.models.llm_usage import LLMUsageRecord, UsageType
from app.db.models.plan import Plan
from app.db.models.quota import Quota
from app.db.models.tenant_usage_daily import TenantUsageDaily
from app.db.models.ai_model import AIModel
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.credit_account import CreditAccount
from app.db.models.credit_transaction import CreditTransaction
from app.db.models.social_account import SocialAccount, SocialPlatform
from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.activity_timeline import ActivityTimeline, ActivityType
from app.db.models.event import Event, EventType, EventStatus
from app.db.models.error_log import ErrorLog, ErrorSeverity

__all__ = [
    # Core
    "User",
    "Role",
    "Tenant",
    "UserTenantRole",
    # Projects & Branding
    "Project",
    "BrandPersona",
    # Conversations
    "Conversation",
    "ConversationMessage",
    # AI
    "Agent",
    "Run",
    "RunStatus",
    "Artifact",
    "ArtifactType",
    "ArtifactStatus",
    "PromptVersion",
    "AIModel",
    # Embeddings & RAG
    "Embedding",
    "EmbeddingType",
    "EmbeddingSource",
    # Usage & Billing
    "LLMUsageRecord",
    "UsageType",
    "Plan",
    "Quota",
    "TenantUsageDaily",
    "Invoice",
    "InvoiceStatus",
    "CreditAccount",
    "CreditTransaction",
    # Social
    "SocialAccount",
    "SocialPlatform",
    "SocialPost",
    "PostStatus",
    # Audit & Events
    "ActivityTimeline",
    "ActivityType",
    "Event",
    "EventType",
    "EventStatus",
    "ErrorLog",
    "ErrorSeverity",
]

