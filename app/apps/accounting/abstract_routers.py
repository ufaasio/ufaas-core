import uuid
from typing import Any, Type, TypeVar

from apps.base.models import BusinessEntity as BusinessEntitySQL
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from apps.base_mongo.models import BusinessEntity
from apps.business.routes import AbstractBusinessBaseRouter as AbstractBusinessSQLRouter
from apps.business_mongo.middlewares import AuthorizationData, authorization_middleware
from apps.business_mongo.routes import AbstractBusinessBaseRouter
from core.exceptions import BaseHTTPException
from fastapi import Depends, Query, Request
from server.config import Settings
from server.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractAuthRouter(AbstractBusinessBaseRouter[T, TS]):
    async def get_auth(self, request: Request) -> AuthorizationData:
        return await authorization_middleware(request)

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        auth = await self.get_auth(request)
        items, total = await self.model.list_total_combined(
            user_id=auth.user_id,
            business_name=auth.business.name,
            offset=offset,
            limit=limit,
        )

        items_in_schema = [self.list_item_schema(**item.model_dump()) for item in items]

        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        item = await self.model.get_item(
            uid=uid, user_id=auth.user_id, business_name=auth.business.name
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return item

    async def create_item(self, request: Request, data: dict):
        auth = await self.get_auth(request)
        item = self.model(
            business_name=auth.business.name,
            **data.model_dump(),
        )
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(self, request: Request, uid: uuid.UUID, data: dict):
        auth = await self.get_auth(request)

        item = await self.model.get_item(
            uid,
            business_name=auth.business.name,
            user_id=auth.user_id,  # if auth.user_id else auth.user.uid
        )

        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        item = await self.model.update_item(item, data.model_dump())
        return item

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)

        item = await self.model.get_item(
            uid, business_name=auth.business.name, user_id=auth.user_id
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item = await self.model.delete_item(item)
        return item


TSQL = TypeVar("TSQL", bound=BusinessEntitySQL)


class AbstractAuthSQLRouter(AbstractBusinessSQLRouter[TSQL, TS]):
    def __init__(
        self,
        model: Type[TSQL],
        user_dependency: Any,
        *args,
        prefix: str = None,
        tags: list[str] = None,
        schema: Type[TS] = None,
        **kwargs,
    ):
        super().__init__(
            model=model,
            user_dependency=user_dependency,
            *args,
            prefix=prefix,
            tags=tags,
            schema=schema,
            **kwargs,
        )

    async def get_auth(self, request: Request) -> AuthorizationData:
        return await authorization_middleware(request)

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
        session: AsyncSession = Depends(get_db_session),
    ):
        auth = await self.get_auth(request)
        items, total = await self.model.list_total_combined(
            session=session,
            user_id=auth.user_id,
            business_name=auth.business.name,
            offset=offset,
            limit=limit,
        )

        items_in_schema = [self.schema(**item.__dict__) for item in items]
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(
        self,
        request: Request,
        uid: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
    ):
        auth = await self.get_auth(request)
        item = await self.model.get_item(
            session, uid, user_id=auth.user_id, business_name=auth.business.name
        )

        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return self.retrieve_response_schema(**item.__dict__)

    async def create_item(self, request: Request, data: dict):
        auth = await self.get_auth(request)
        item = self.model(
            business_name=auth.business.name,
            **data.model_dump(),
        )
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(self, request: Request, uid: uuid.UUID, data: dict):
        auth = await self.get_auth(request)

        item = await self.model.get_item(
            uid,
            business_name=auth.business.name,
            user_id=auth.user_id,  # if auth.user_id else auth.user.uid
        )

        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        item = await self.model.update_item(item, data.model_dump())
        return item

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)

        item = await self.model.get_item(
            uid, business_name=auth.business.name, user_id=auth.user_id
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item = await self.model.delete_item(item)
        return item
