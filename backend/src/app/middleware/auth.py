"""
Authentication Middleware - extracts user_id, tenant_id, and role from JWT token.
Enhanced to extract all context needed for multi-tenant RBAC.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from jose import jwt, JWTError
from app.config.settings import settings
from app.middleware.request_context import set_context
from app.config.constants import CTX_USER_ID, CTX_TENANT_ID, CTX_ROLE


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced auth middleware that extracts user_id, tenant_id, and role from JWT.
    Follows architecture: JWT contains sub (user_id), tenant_id, and role.
    """
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                )
                # Extract user_id, tenant_id, and role from JWT payload
                user_id = payload.get("sub")
                tenant_id = payload.get("tenant_id")
                role = payload.get("role")
                
                if user_id:
                    set_context(CTX_USER_ID, user_id)
                if tenant_id:
                    set_context(CTX_TENANT_ID, tenant_id)
                if role:
                    set_context(CTX_ROLE, role)
            except JWTError:
                # Invalid token - continue without setting context
                pass

        return await call_next(request)
