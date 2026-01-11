from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import contextvars

request_context = contextvars.ContextVar("request_context", default={})


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_context.set({})
        response = await call_next(request)
        return response


def set_context(key: str, value):
    ctx = request_context.get()
    ctx[key] = value
    request_context.set(ctx)


def get_context(key: str):
    return request_context.get().get(key)
