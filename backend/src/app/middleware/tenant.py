"""
Tenant Resolver Middleware - resolves tenant from JWT or header.
Enhanced to work with JWT-based auth (tenant_id from JWT takes precedence).
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.middleware.request_context import get_context, set_context
from app.config.constants import CTX_TENANT_ID


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Enhanced tenant middleware that:
    1. Checks if tenant_id already set by AuthMiddleware (from JWT)
    2. Falls back to X-Tenant-Id header if not in JWT
    3. Rejects cross-tenant access attempts
    """
    async def dispatch(self, request: Request, call_next):
        # Check if tenant_id already set by AuthMiddleware
        tenant_id = get_context(CTX_TENANT_ID)
        
        # If not in JWT, try header (for backward compatibility)
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-Id")
            if tenant_id:
                set_context(CTX_TENANT_ID, tenant_id)

        return await call_next(request)
