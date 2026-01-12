from fastapi import APIRouter
from app.api.v1.users import router as users_router
from app.api.v1.projects import router as projects_router
from app.api.v1.auth import router as auth_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.artifacts import router as artifacts_router
from app.api.v1.agents import router as agents_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.social_oauth import router as social_oauth_router
from app.api.v1.connectors import router as connectors_router
from app.api.v1.project_agents import router as project_agents_router
from app.api.v1.agent_chat import router as agent_chat_router
from app.api.v1.test_generation import router as test_generation_router

# New content and social routers
try:
    from app.api.v1.content import router as content_router
    from app.api.v1.social import router as social_router
    from app.api.v1.chat_content import router as chat_content_router
    from app.api.v1.credits import router as credits_router
    from app.api.v1.scheduling import router as scheduling_router
    CONTENT_AVAILABLE = True
except ImportError as e:
    CONTENT_AVAILABLE = False
    content_router = None
    social_router = None
    chat_content_router = None
    credits_router = None
    scheduling_router = None
    print(f"Warning: Content features not available: {e}")

api_router = APIRouter(prefix="/api")

# Register domain routers here
# Auth endpoints (no authentication required)
api_router.include_router(auth_router)

# Protected endpoints (require authentication)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(conversations_router)
api_router.include_router(artifacts_router)
api_router.include_router(agents_router)
api_router.include_router(analytics_router)
api_router.include_router(social_oauth_router)
api_router.include_router(connectors_router)
api_router.include_router(project_agents_router)
api_router.include_router(agent_chat_router)
api_router.include_router(test_generation_router)

# Content and social endpoints (require google-generativeai)
if CONTENT_AVAILABLE:
    if content_router:
        api_router.include_router(content_router)
    if social_router:
        api_router.include_router(social_router)
    if chat_content_router:
        api_router.include_router(chat_content_router)
    if credits_router:
        api_router.include_router(credits_router)
    if scheduling_router:
        api_router.include_router(scheduling_router)
