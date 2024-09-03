import uuid
from typing import Any, Type, TypeVar

from fastapi import Query, Request

from apps.base.models import BusinessEntity as BusinessEntitySQL
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from apps.base_mongo.models import BusinessEntity
from apps.business.routes import AbstractBusinessBaseRouter as AbstractBusinessSQLRouter
from apps.business_mongo.middlewares import AuthorizationData, authorization_middleware
from apps.business_mongo.routes import AbstractBusinessBaseRouter
from server.config import Settings

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
        item = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )
        return item

    async def create_item(self, request: Request, data: dict):
        auth = await self.get_auth(request)
        item = self.model(
            business_name=auth.business.name,
            **data,
        )
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(self, request: Request, uid: uuid.UUID, data: dict):
        auth = await self.get_auth(request)
        item = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )

        item = await self.model.update_item(item, data)
        return item

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        item = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )
        item = await self.model.delete_item(item)
        return item


T_SQL = TypeVar("T_SQL", bound=BusinessEntitySQL)


class AbstractAuthSQLRouter(AbstractBusinessSQLRouter[T_SQL, TS]):
    def __init__(
        self,
        model: Type[T_SQL],
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
    ):
        auth = await self.get_auth(request)
        items, total = await self.model.list_total_combined(
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
    ):
        auth = await self.get_auth(request)
        item = await self.get_item(
            request, uid, user_id=auth.user_id, business_name=auth.business.name
        )
        return self.retrieve_response_schema(**item.__dict__)

    async def create_item(self, request: Request, data: dict):
        auth = await self.get_auth(request)
        item = self.model(
            business_name=auth.business.name,
            **data,
        )
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(self, request: Request, uid: uuid.UUID, data: dict):
        auth = await self.get_auth(request)
        item = await self.get_item(
            request, uid, user_id=auth.user_id, business_name=auth.business.name
        )
        item = await self.model.update_item(item, data)
        return item

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        item = await self.get_item(
            request, uid, user_id=auth.user_id, business_name=auth.business.name
        )
        item = await self.model.delete_item(item)
        return item
