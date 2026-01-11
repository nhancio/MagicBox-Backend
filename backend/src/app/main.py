from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.v1.endpoints import api_router
from app.db.database import SessionLocal
from app.db.models.role import Role
from app.config.constants import ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from app.middleware.auth import AuthMiddleware
from app.middleware.tenant import TenantMiddleware
from app.middleware.rbac import RBACMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware

app = FastAPI(
    title="MagicBox Backend",
    version="1.0.0",
    description="AI-first, multi-tenant content creation platform",
)

# CORS configuration for frontend integration - updated
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Vite alternative port
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "https://magicbox.nhancio.com",  # Production frontend
        "https://*.netlify.app",  # Netlify preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def custom_openapi():
    """Custom OpenAPI schema with Bearer token authentication."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add Bearer token security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # Add/update Bearer token security scheme
    openapi_schema["components"]["securitySchemes"]["Bearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token (just the token, Swagger will add 'Bearer' prefix automatically). Token obtained from /api/auth/login or /api/auth/register"
    }
    
    # Remove old security schemes
    if "HTTPBearer" in openapi_schema["components"]["securitySchemes"]:
        del openapi_schema["components"]["securitySchemes"]["HTTPBearer"]
    if "Bearer Token" in openapi_schema["components"]["securitySchemes"]:
        del openapi_schema["components"]["securitySchemes"]["Bearer Token"]
    
    # Apply security to all endpoints except auth and health endpoints
    for path, path_item in openapi_schema["paths"].items():
        if not path.startswith("/api/auth") and path != "/health" and path != "/openapi.json":
            for method, operation in path_item.items():
                if isinstance(operation, dict) and "operationId" in operation:
                    # Set security to use "Bearer" scheme
                    if "security" in operation:
                        # Replace any existing security
                        operation["security"] = [{"Bearer": []}]
                    else:
                        operation["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add middleware - LAST added runs FIRST on request!
# Desired order: RequestContext -> Auth -> Tenant -> RBAC -> RateLimit
# So we add in REVERSE: RateLimit, RBAC, Tenant, Auth, RequestContext
app.add_middleware(RateLimitMiddleware)  # Added 1st, runs LAST (closest to route)
app.add_middleware(RBACMiddleware)  # Added 2nd, runs 4th
app.add_middleware(TenantMiddleware)  # Added 3rd, runs 3rd
app.add_middleware(AuthMiddleware)  # Added 4th, runs 2nd
app.add_middleware(RequestContextMiddleware)  # Added 5th, runs FIRST (initialize context)

# Include all API routes
app.include_router(api_router)


@app.on_event("startup")
def seed_roles():
    """Initialize roles in the database if they don't exist."""
    db = SessionLocal()
    try:
        # Define all required roles
        required_roles = [ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER]
        
        # Get existing roles
        existing_roles = {role.name for role in db.query(Role).all()}
        
        # Create missing roles
        for role_name in required_roles:
            if role_name not in existing_roles:
                role = Role(name=role_name)
                db.add(role)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding roles: {e}")
    finally:
        db.close()


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
