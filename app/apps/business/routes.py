from typing import TypeVar
from uuid import UUID

from apps.base.models import BusinessEntity
from apps.base.routes import AbstractBaseRouter
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from core.exceptions import BaseHTTPException
from fastapi import Depends, Query, Request
from server.config import Settings
from server.db import get_db_session
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from usso.fastapi import jwt_access_security

from .handlers import create_dto_business, update_dto_business
from .middlewares import get_business
from .models import Business
from .schemas import BusinessSchema, BusinessDataCreateSchema, BusinessDataUpdateSchema

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractBusinessBaseRouter(AbstractBaseRouter[T, TS]):

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        items = [
            self.schema(**item.__dict__)
            for item in await self.model.list_items(
                session,
                offset=offset,
                limit=limit,
                user_id=user.uid,
                business_name=business.name,
            )
        ]
        total = await self.model.total_count(
            session, user_id=user.uid, business_name=business.name
        )
        return PaginatedResponse(items=items, offset=offset, limit=limit, total=total)

    async def retrieve_item(
        self,
        request: Request,
        uid: str,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(session, uid, user_id, business.name)

        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return self.retrieve_response_schema(**item.__dict__)

    async def create_item(
        self,
        request: Request,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        item_data = await create_dto_business(self.model)(
            request, user, business_name=business.name
        )
        item = await self.model.create_item(session, item_data.model_dump())
        return self.create_response_schema(**item.__dict__)

    async def update_item(
        self,
        request: Request,
        uid: str,
        data: dict,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(session, uid, user_id, business.name)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"item not found",
            )

        item = await self.model.update_item(session, item, data)
        return self.update_response_schema(**item.__dict__)

    async def delete_item(
        self,
        request: Request,
        uid: str,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(session, uid, user_id, business.name)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item = await self.model.delete_item(session, item)
        return self.delete_response_schema(**item.__dict__)


class BusinessRouter(AbstractBaseRouter[Business, BusinessSchema]):
    def __init__(self):
        super().__init__(
            model=Business,
            schema=BusinessSchema,
            user_dependency=jwt_access_security,
            prefix="/businesses",
        )

    async def create_item(
        self,
        request: Request,
        item: BusinessDataCreateSchema,
        session: AsyncSession = Depends(get_db_session),
    ):
        return await super().create_item(request, item.model_dump(), session)

    async def update_item(
        self,
        request: Request,
        uid: UUID,
        data: BusinessDataUpdateSchema,
        session: AsyncSession = Depends(get_db_session),
    ):
        return await super().update_item(request, uid, data.model_dump(exclude_none=True), session)


router = BusinessRouter().router
