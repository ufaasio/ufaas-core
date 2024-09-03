import uuid
from typing import TypeVar

from fastapi import Depends, Query, Request
from usso.fastapi import jwt_access_security

from apps.base.handlers import create_dto
from apps.base.models import BusinessEntity
from apps.base.routes import AbstractBaseRouter
from apps.base.schemas import BusinessEntitySchema, PaginatedResponse
from server.config import Settings

from .middlewares import get_business
from .models import Business
from .schemas import BusinessDataCreateSchema, BusinessDataUpdateSchema, BusinessSchema

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractBusinessBaseRouter(AbstractBaseRouter[T, TS]):

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        items, total = await self.model.list_total_combined(
            offset=offset,
            limit=limit,
            user_id=user.uid,
            business_name=business.name,
        )
        items_in_schema = [self.schema(**item.__dict__) for item in items]
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(
        self,
        request: Request,
        uid: uuid.UUID,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id, business_name=business.name)
        return self.retrieve_response_schema(**item.__dict__)

    async def create_item(
        self,
        request: Request,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        item_data: TS = await create_dto(self.create_response_schema)(
            request, user_id=user.uid if user else None, business_name=business.name
        )
        item = await self.model.create_item(item_data.model_dump())

        return self.create_response_schema(**item.__dict__)

    async def update_item(
        self,
        request: Request,
        uid: uuid.UUID,
        data: dict,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id, business_name=business.name)

        item = await self.model.update_item(item, data)
        return self.update_response_schema(**item.__dict__)

    async def delete_item(
        self,
        request: Request,
        uid: uuid.UUID,
        business: Business = Depends(get_business),
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id, business_name=business.name)

        item = await self.model.delete_item(item)
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
    ):
        return await super().create_item(item.model_dump())

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
