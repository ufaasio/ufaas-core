from typing import Any, Generic, Type, TypeVar

import singleton
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.exceptions import BaseHTTPException
from server.config import Settings
from server.db import get_db_session

from .handlers import create_dto, update_dto
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
        **kwargs,
    ):
        self.model = model
        self.user_dependency = user_dependency
        if prefix is None:
            prefix = f"/{self.model.__name__.lower()}s"
        if tags is None:
            tags = [self.model.__name__]
        self.router = APIRouter(prefix=prefix, tags=tags, **kwargs)
        self.config_schemas(**kwargs)
        self.config_routes(**kwargs)

    def config_schemas(self, **kwargs):
        self.list_response_schema = PaginatedResponse[TS]
        self.retrieve_response_schema = TS
        self.create_response_schema = TS
        self.update_response_schema = TS
        self.delete_response_schema = TS

        self.create_request_schema = TS
        self.update_request_schema = TS

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

    async def get_user(self, request: Request, *args, **kwargs):
        if self.user_dependency is None:
            return None
        return await self.user_dependency(request)

    async def list_items(
        self,
        request: Request,
        offset: int = 0,
        limit: int = 10,
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        # Create the base query
        query = select(self.model).filter_by(is_deleted=False)

        # Apply user_id filtering if the model has a user_id attribute
        if hasattr(self.model, "user_id"):
            query = query.filter_by(user_id=user.uid)

        # Apply sorting, offset, and limit
        query = query.order_by(self.model.created_at.desc()).offset(offset).limit(limit)

        # Apply offset and limit
        query = query.offset(offset).limit(limit)

        # Execute the query and fetch the results
        result = await session.execute(query)
        items = result.scalars().all()

        return items

    async def retrieve_item(
        self, request: Request, uid, session: AsyncSession = Depends(get_db_session)
    ):
        user = await self.get_user(request)

        # Create the base query to get the item by its UID
        query = select(self.model).filter_by(uid=uid, is_deleted=False)

        # Apply user_id filtering if the model has a user_id attribute
        if hasattr(self.model, "user_id"):
            query = query.filter_by(user_id=user.id)

        # Execute the query
        result = await session.execute(query)
        item = result.scalar_one_or_none()
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return item

    async def create_item(
        self, request: Request, session: AsyncSession = Depends(get_db_session)
    ):
        user = await self.get_user(request)
        item_data = await create_dto(self.model)(request, user)

        # Create a new item instance from the model
        item = self.model(**item_data.dict())

        # Add the item to the session and commit the transaction
        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item

    async def update_item(
        self,
        request: Request,
        uid: str,
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        item = await self.retrieve_item(request, uid, session)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item_data = await update_dto(self.model)(request, user, item)
        session.add(item_data)
        await session.commit()
        await session.refresh(item_data)

        return item_data

    async def delete_item(
        self,
        request: Request,
        uid: str,
        session: AsyncSession = Depends(get_db_session),
    ):
        await self.get_user(request)
        item = await self.retrieve_item(request, uid, session)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )

        item.is_deleted = True
        session.add(item)
        await session.commit()
        await session.refresh(item)

        return item
