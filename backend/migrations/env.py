import sys
import os
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Setup paths EARLY
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

# --------------------------------------------------
# 2. Load environment IMMEDIATELY
# --------------------------------------------------
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# --------------------------------------------------
# 3. Alembic config
# --------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------
# 4. Import Base + ALL models
# --------------------------------------------------
from app.db.base import Base

# IMPORTANT: import every model so metadata is complete
# Import all models from __init__.py to ensure all tables are detected
from app.db.models import (
    # Core
    User,
    Role,
    Tenant,
    UserTenantRole,
    # Projects & Branding
    Project,
    BrandPersona,
    # Conversations
    Conversation,
    ConversationMessage,
    # AI
    Agent,
    Run,
    Artifact,
    PromptVersion,
    AIModel,
    # Embeddings & RAG
    Embedding,
    # Usage & Billing
    LLMUsageRecord,
    Plan,
    Quota,
    TenantUsageDaily,
    Invoice,
    CreditAccount,
    CreditTransaction,
    # Social
    SocialAccount,
    SocialPost,
    # Audit & Events
    ActivityTimeline,
    Event,
    ErrorLog,
)

target_metadata = Base.metadata

# --------------------------------------------------
# 5. Database URL (SINGLE SOURCE OF TRUTH)
# --------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# Set Alembic config explicitly
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# --------------------------------------------------
# Offline migrations
# --------------------------------------------------
def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# --------------------------------------------------
# Online migrations (FIXED)
# --------------------------------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.QueuePool,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# --------------------------------------------------
# Run
# --------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
