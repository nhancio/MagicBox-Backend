"""
Rate Limiting Middleware - enforces rate limits per user and tenant.
Follows architecture: rate limiting per user and per tenant.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.middleware.request_context import get_context
from app.config.constants import CTX_USER_ID, CTX_TENANT_ID
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware that tracks:
    - Per-user rate limits
    - Per-tenant rate limits
    """
    
    # Rate limit configuration: (requests, window_seconds)
    USER_RATE_LIMIT = (100, 60)  # 100 requests per minute per user
    TENANT_RATE_LIMIT = (1000, 60)  # 1000 requests per minute per tenant
    
    def __init__(self, app):
        super().__init__(app)
        # In-memory storage (use Redis in production)
        self.user_requests: Dict[str, list] = defaultdict(list)
        self.tenant_requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        user_id = get_context(CTX_USER_ID)
        tenant_id = get_context(CTX_TENANT_ID)
        
        now = datetime.utcnow()
        
        # Check user rate limit
        if user_id:
            user_limit, user_window = self.USER_RATE_LIMIT
            self._cleanup_old_requests(self.user_requests[user_id], user_window)
            
            if len(self.user_requests[user_id]) >= user_limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {user_limit} requests per {user_window} seconds."
                    },
                    headers={"Retry-After": str(user_window)}
                )
            
            self.user_requests[user_id].append(now)
        
        # Check tenant rate limit
        if tenant_id:
            tenant_limit, tenant_window = self.TENANT_RATE_LIMIT
            self._cleanup_old_requests(self.tenant_requests[tenant_id], tenant_window)
            
            if len(self.tenant_requests[tenant_id]) >= tenant_limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Tenant rate limit exceeded. Maximum {tenant_limit} requests per {tenant_window} seconds."
                    },
                    headers={"Retry-After": str(tenant_window)}
                )
            
            self.tenant_requests[tenant_id].append(now)
        
        return await call_next(request)
    
    @staticmethod
    def _cleanup_old_requests(requests_list: list, window_seconds: int):
        """Remove requests older than the window."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        requests_list[:] = [req_time for req_time in requests_list if req_time > cutoff]
