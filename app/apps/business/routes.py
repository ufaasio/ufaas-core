from typing import TypeVar

from apps.base.models import BusinessEntity
from apps.base.routes import AbstractBaseRouter
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from core.exceptions import BaseHTTPException
from fastapi import Depends, Query, Request
from server.config import Settings
from server.db import get_db_session
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from usso.fastapi import jwt_access_security

from .handlers import create_dto_business, update_dto_business
from .middlewares import get_business
from .models import Business
from .schemas import BusinessSchema

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

        # Create the base query
        base_query = [
            self.model.is_deleted == False,
            self.model.business_name == business.name,
        ]

        # Apply user_id filtering if the model has a user_id attribute
        if hasattr(self.model, "user_id"):
            base_query.append(self.model.user_id == user.uid)

        # Query for getting the total count of items
        total_count_query = select(func.count()).filter(*base_query).subquery()

        # Create the base query for fetching the items
        items_query = (
            select(self.model)
            .filter(*base_query)
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
            .subquery()
        )

        # Combine both queries into a single select statement
        combined_query = select(total_count_query.c[0].label("total"), items_query)

        # Execute the combined query
        result = await session.execute(combined_query)
        rows = result.fetchall()

        # Extract total count and items
        total = rows[0]["total"] if rows else 0
        items = [row[self.model] for row in rows]

        return PaginatedResponse(items=items, offset=offset, limit=limit, total=total)

    async def retrieve_item(
        self,
        request: Request,
        uid: str,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)

        # Create the base query to get the item by its UID
        query = select(self.model).filter_by(
            uid=uid, is_deleted=False, business_name=business.name
        )

        # Apply user_id filtering if the model has a user_id attribute
        if hasattr(self.model, "user_id"):
            query = query.filter_by(user_id=user.uid)

        # Execute the query
        result = await session.execute(query)
        item = result.scalar_one_or_none()
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"item not found",
            )
        return item

    async def create_item(
        self,
        request: Request,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        item = await create_dto_business(self.model)(request, user)

        # Add the item to the session and commit the transaction
        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item

    async def update_item(
        self,
        request: Request,
        uid: str,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        item = await self.retrieve_item(request, uid, business, session)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"item not found",
            )

        item_data = await update_dto_business(self.model)(request, user, item)
        session.add(item_data)
        await session.commit()
        await session.refresh(item_data)

        return item_data

    async def delete_item(
        self,
        request: Request,
        uid: str,
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        await self.get_user(request)
        item = await self.retrieve_item(request, uid, business, session)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"item not found",
            )

        item.is_deleted = True
        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item


class BusinessRouter(AbstractBaseRouter[Business, BusinessSchema]):
    def __init__(self):
        super().__init__(
            model=Business,
            user_dependency=jwt_access_security,
            prefix="/businesses",
        )


router = BusinessRouter().router
