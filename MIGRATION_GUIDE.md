# Alembic Migration Guide

This guide will help you create and run database migrations for all the new models.

## Prerequisites

1. Ensure your `.env` file has `DATABASE_URL` set:
   ```
   DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/magic
   ```

2. Make sure you're in the `backend` directory:
   ```bash
   cd backend
   ```

## Step 1: Create a New Migration

Generate a new migration that will detect all the new models:

```bash
alembic revision --autogenerate -m "Add all architecture models"
```

This will:
- Detect all models imported in `migrations/env.py`
- Create a new migration file in `migrations/versions/`
- Include all table creations, foreign keys, indexes, etc.

## Step 2: Review the Migration

Before running, review the generated migration file:
- Check that all tables are included
- Verify foreign key relationships
- Ensure indexes are created
- Check for any issues with pgvector (for embeddings table)

The migration file will be in: `backend/migrations/versions/XXXXX_add_all_architecture_models.py`

## Step 3: Run the Migration

Apply the migration to create all tables:

```bash
alembic upgrade head
```

This will:
- Create all tables in your database
- Set up all foreign key constraints
- Create indexes
- Set up pgvector extension (if needed)

## Step 4: Verify

Check that all tables were created:

```bash
# Connect to your database and run:
\dt

# Or using psql:
psql -U postgres -d magic -c "\dt"
```

You should see all these tables:
- users
- roles
- tenants
- user_tenant_roles
- projects
- brand_personas
- conversations
- conversation_messages
- agents
- runs
- artifacts
- prompt_versions
- embeddings
- llm_usage_records
- plans
- quotas
- tenant_usage_daily
- ai_models
- invoices
- credit_accounts
- credit_transactions
- social_accounts
- social_posts
- activity_timeline
- events
- error_logs

## Troubleshooting

### Issue: pgvector extension not found

If you get an error about pgvector, you need to install it:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run this in your PostgreSQL database before running migrations.

### Issue: Migration conflicts

If you have existing migrations, you may need to:
1. Check current migration status: `alembic current`
2. If needed, stamp to a specific revision: `alembic stamp head`
3. Then create new migration: `alembic revision --autogenerate -m "Add all models"`

### Issue: Import errors

If you get import errors, ensure:
- All models are properly imported in `migrations/env.py`
- All model files exist and are valid Python
- Dependencies are installed: `pip install -r requirements.txt`

## Next Steps

After migrations are complete:
1. Verify the roles table is seeded (should happen on app startup)
2. Test creating a user
3. Test creating a project
4. Test creating a conversation

## Rollback (if needed)

If you need to rollback:

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```
