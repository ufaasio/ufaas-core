import uuid
from typing import Any, Generic, Type, TypeVar

import singleton
from fastapi import APIRouter, Query, Request

from core.exceptions import BaseHTTPException
from server.config import Settings

from .handlers import create_dto
from .models import BaseEntity
from .schemas import BaseEntitySchema, PaginatedResponse

# Define a type variable
T = TypeVar("T", bound=BaseEntity)
TS = TypeVar("TS", bound=BaseEntitySchema)


class AbstractBaseRouter(Generic[T, TS], metaclass=singleton.Singleton):
    def __init__(
        self,
        model: Type[T],
        user_dependency: Any,
        *args,
        prefix: str = None,
        tags: list[str] = None,
        schema: Type[TS] = None,
        **kwargs,
    ):
        self.model = model
        self.schema = schema
        self.user_dependency = user_dependency
        if prefix is None:
            prefix = f"/{self.model.__name__.lower()}s"
        if tags is None:
            tags = [self.model.__name__]
        self.router = APIRouter(prefix=prefix, tags=tags, **kwargs)
        self.config_schemas(self.schema, **kwargs)
        self.config_routes(**kwargs)

    @classmethod
    def config_schemas(cls, schema, **kwargs):
        cls.list_response_schema = PaginatedResponse[schema]
        cls.list_item_schema = schema
        cls.retrieve_response_schema = schema
        cls.create_response_schema = schema
        cls.update_response_schema = schema
        cls.delete_response_schema = schema

        cls.create_request_schema = schema
        cls.update_request_schema = schema

    def config_routes(self, **kwargs):
        self.router.add_api_route(
            "/",
            self.list_items,
            methods=["GET"],
            response_model=self.list_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.retrieve_item,
            methods=["GET"],
            response_model=self.retrieve_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/",
            self.create_item,
            methods=["POST"],
            response_model=self.create_response_schema,
            status_code=201,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.update_item,
            methods=["PATCH"],
            response_model=self.update_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.delete_item,
            methods=["DELETE"],
            response_model=self.delete_response_schema,
            # status_code=204,
        )

    async def get_item(
        self,
        uid: uuid.UUID,
        user_id: uuid.UUID = None,
        business_name: str = None,
        **kwargs,
    ):
        item = await self.model.get_item(
            uid, user_id=user_id, business_name=business_name, **kwargs
        )
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return item

    async def get_user(self, request: Request, *args, **kwargs):
        if self.user_dependency is None:
            return None
        return await self.user_dependency(request)

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        items, total = await self.model.list_total_combined(
            offset=offset, limit=limit, user_id=user.uid if user else None
        )

        items_in_schema = [self.list_item_schema(**item.__dict__) for item in items]
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(
        self,
        request: Request,
        uid: uuid.UUID,
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id)
        return self.retrieve_response_schema(**item.__dict__)

    async def create_item(
        self,
        request: Request,
        item: dict,
    ):
        user = await self.get_user(request)
        # TODO self.create_request_schema is not a valid input for create_dto because many times it does not have user_id
        item_data: TS = await create_dto(self.create_response_schema)(
            request, user_id=user.uid if user else None
        )
        item = await self.model.create_item(item_data.model_dump())
        return self.create_response_schema(**item.__dict__)

    async def update_item(
        self,
        request: Request,
        uid: uuid.UUID,
        data: dict,
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id)
        item = await self.model.update_item(item, data)
        return self.update_response_schema(**item.__dict__)

    async def delete_item(
        self,
        request: Request,
        uid: uuid.UUID,
    ):
        user = await self.get_user(request)
        user_id = user.uid if user else None
        item = self.get_item(uid, user_id=user_id)
        item = await self.model.delete_item(item)
        return self.delete_response_schema(**item.__dict__)
