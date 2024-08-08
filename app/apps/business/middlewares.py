from apps.business.models import Business
from core.exceptions import BaseHTTPException
from fastapi import Depends, Request
from server.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


async def get_business(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    business = await Business.get_by_origin(request.url.hostname, session)
    if not business:
        raise BaseHTTPException(404, "business_not_found", "business not found")
    return business
