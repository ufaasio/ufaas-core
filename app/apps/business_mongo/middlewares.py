from apps.business_mongo.models import Business
from core.exceptions import BaseHTTPException
from fastapi import Request


async def get_business(
    request: Request,
):
    business = await Business.get_by_origin(request.url.hostname)
    if not business:
        raise BaseHTTPException(404, "business_not_found", "business not found")
    return business
