import fastapi
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from apps.business_mongo.models import Business
from core.exceptions import BaseHTTPException


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def get_allowed_origins(self, origin, **kwargs):
        business = await Business.get_by_origin(origin)
        if not business:
            return []
        return business.config.allowed_origins

    async def dispatch(self, request: fastapi.Request, call_next):
        origin = request.headers.get("origin")
        allowed_origins = await self.get_allowed_origins(origin=origin)
        headers = {}
        if origin in allowed_origins:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, *",
            }

        if request.method == "OPTIONS":
            return PlainTextResponse("", status_code=200, headers=headers)

        if origin and origin not in allowed_origins:
            raise BaseHTTPException(
                status_code=403,
                error="origin_not_allowed",
                message="Origin not allowed",
            )

        response: fastapi.Response = await call_next(request)
        response.headers.update(headers)
        return response
