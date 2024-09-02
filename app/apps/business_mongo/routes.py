import uuid
from typing import TypeVar

from fastapi import Depends, Request
from usso.fastapi import jwt_access_security

from apps.base.handlers import create_dto
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from apps.base_mongo.models import BusinessEntity
from apps.base_mongo.routes import AbstractBaseRouter
from apps.business.schemas import (
    BusinessDataCreateSchema,
    BusinessDataUpdateSchema,
    BusinessSchema,
)
from core.exceptions import BaseHTTPException
from server.config import Settings

from .middlewares import get_business
from .models import Business

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractBusinessBaseRouter(AbstractBaseRouter[T, TS]):
    async def list_items(
        self,
        request: Request,
        offset: int = 0,
        limit: int = 10,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        items, total = await self.model.list_total_combined(
            user_id=user.uid if user else None,
            business_name=business.name,
            offset=offset,
            limit=limit,
        )
        items_in_schema = [self.list_item_schema(**item.model_dump()) for item in items]

        return PaginatedResponse(
            items=items_in_schema,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def retrieve_item(
        self,
        request: Request,
        uid,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(
            uid, business_name=business.name, user_id=user_id
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return item

    async def create_item(
        self,
        request: Request,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        item_data: TS = await create_dto(self.create_response_schema)(
            request, user.uid if user else None, business_name=business.name
        )
        item = await self.model.create_item(item_data.model_dump())

        await item.save()
        return item

    async def update_item(
        self,
        request: Request,
        uid,
        data: dict,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(
            uid, business_name=business.name, user_id=user_id
        )

        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        # item = await update_dto(self.model)(request, user)
        item = await self.model.update_item(item, data)
        return item

    async def delete_item(
        self,
        request: Request,
        uid,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = await self.model.get_item(
            uid, business_name=business.name, user_id=user_id
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item = await self.model.delete_item(item)
        return item


class BusinessRouter(AbstractBaseRouter[Business, BusinessSchema]):
    def __init__(self):
        super().__init__(
            model=Business,
            schema=BusinessSchema,
            user_dependency=jwt_access_security,
            prefix="/businesses",
        )

    def config_schemas(self, schema, **kwargs):
        super().config_schemas(schema, **kwargs)

        self.create_request_schema = BusinessDataCreateSchema
        self.update_request_schema = BusinessDataUpdateSchema

    async def create_item(
        self,
        request: Request,
        item: BusinessDataCreateSchema,
    ):
        return await super().create_item(request, item.model_dump())

    async def update_item(
        self,
        request: Request,
        uid: uuid.UUID,
        data: BusinessDataUpdateSchema,
    ):
        return await super().update_item(
            request, uid, data.model_dump(exclude_none=True)
        )


router = BusinessRouter().router
