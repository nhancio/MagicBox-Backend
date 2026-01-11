from fastapi import FastAPI
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

# Add middleware (order matters!)
app.add_middleware(RequestContextMiddleware)  # Must be first - initialize context
app.add_middleware(AuthMiddleware)  # Extract user/tenant/role from JWT
app.add_middleware(TenantMiddleware)  # Resolve tenant context
app.add_middleware(RBACMiddleware)  # Enforce RBAC
app.add_middleware(RateLimitMiddleware)  # Rate limiting (last - after auth)

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
