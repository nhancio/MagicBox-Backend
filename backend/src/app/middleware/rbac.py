"""
RBAC Middleware - enforces role-based access control.
Enhanced to extract role from JWT and validate permissions.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.middleware.request_context import get_context, set_context
from app.config.constants import CTX_ROLE, CTX_USER_ID, CTX_TENANT_ID


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Enhanced RBAC middleware that:
    1. Checks if role already set by AuthMiddleware (from JWT)
    2. Falls back to header if not in JWT
    3. Validates required permissions for protected routes
    """
    
    # Define protected routes and required roles
    PROTECTED_ROUTES = {
        "/api/projects": ["OWNER", "ADMIN", "EDITOR"],
        "/api/conversations": ["OWNER", "ADMIN", "EDITOR", "VIEWER"],
        "/api/artifacts": ["OWNER", "ADMIN", "EDITOR", "VIEWER"],
        "/api/runs": ["OWNER", "ADMIN", "EDITOR"],
        "/api/billing": ["OWNER", "ADMIN"],
        "/api/users": ["OWNER", "ADMIN"],
    }
    
    async def dispatch(self, request: Request, call_next):
        # Check if role already set by AuthMiddleware
        role = get_context(CTX_ROLE)
        
        # If not in JWT, try header (for backward compatibility)
        if not role:
            role = request.headers.get("X-User-Role", "VIEWER")
            set_context(CTX_ROLE, role)
        
        # Check permissions for protected routes
        path = request.url.path
        user_id = get_context(CTX_USER_ID)
        tenant_id = get_context(CTX_TENANT_ID)
        
        # Skip auth check for public routes
        if path.startswith("/health") or path.startswith("/api/auth"):
            return await call_next(request)
        
        # Require authentication for API routes
        if path.startswith("/api") and not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        # Require tenant context for tenant-scoped routes
        if path.startswith("/api") and not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "Tenant context required"}
            )
        
        # Check route-specific permissions
        for route_prefix, allowed_roles in self.PROTECTED_ROUTES.items():
            if path.startswith(route_prefix):
                if role not in allowed_roles:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"}
                    )
                break
        
        return await call_next(request)
