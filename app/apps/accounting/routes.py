import uuid
from apps.business_mongo.models import Business
from apps.base.schemas import PaginatedResponse
from apps.business_mongo.routes import AbstractBusinessBaseRouter
from fastapi import Depends, Query, Request
from server.config import Settings
from server.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from usso.fastapi import jwt_access_security
from core.exceptions import BaseHTTPException
from .models import Proposal, Transaction, Wallet, WalletHold
from .schemas import (
    ProposalSchema,
    TransactionSchema,
    WalletHoldSchema,
    WalletSchema,
    WalletUpdateSchema,
    WalletCreateSchema,
)
from apps.business_mongo.middlewares import (
    AuthorizationData,
    authorization_middleware,
    get_business,
    AuthorizationException,
)


class WalletRouter(AbstractBusinessBaseRouter[Wallet, Wallet]):
    def __init__(self):
        super().__init__(
            model=Wallet,
            # prefix="/wallets",
            tags=["Accounting"],
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
        if auth.business_or_user == "User" and total == 0:
            items = [
                await self.model.create_item(
                    user_id=auth.user_id, business_name=auth.business.name
                )
            ]
            total = 1

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

    async def create_item(self, request: Request, data: WalletCreateSchema):
        auth = await self.get_auth(request)

        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot create wallet")

        item = self.model(
            business_name=auth.business.name,
            **data.model_dump(),
        )
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: WalletUpdateSchema
    ):
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

        # if auth.business_or_user == "User":
        #     item.meta_data["user"] = data.meta_data
        # else:
        #     item.meta_data["business"] = data.meta_data

        item = await self.model.update_item(item, **data.model_dump())
        return item

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)

        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot create wallet")

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


class WalletHoldRouter(AbstractBusinessBaseRouter[WalletHold, WalletHoldSchema]):
    def __init__(self):
        super().__init__(
            model=WalletHold,
            user_dependency=jwt_access_security,
            prefix="/wallet-holds",
            tags=["Accounting"],
        )

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


class TransactionRouter(AbstractBusinessBaseRouter[Transaction, TransactionSchema]):
    def __init__(self):
        super().__init__(
            model=Transaction,
            user_dependency=jwt_access_security,
            # prefix="/transactions",
            tags=["Accounting"],
        )

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


class ProposalRouter(AbstractBusinessBaseRouter[Proposal, ProposalSchema]):
    def __init__(self):
        super().__init__(
            model=Proposal,
            user_dependency=jwt_access_security,
            # prefix="/proposal",
            tags=["Accounting"],
        )

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
        # self.router.add_api_route(
        #     "/{uid:uuid}",
        #     self.update_item,
        #     methods=["PATCH"],
        #     response_model=self.update_response_schema,
        #     status_code=200,
        # )
        # self.router.add_api_route(
        #     "/{uid:uuid}",
        #     self.delete_item,
        #     methods=["DELETE"],
        #     response_model=self.delete_response_schema,
        #     # status_code=204,
        # )


wallet_router = WalletRouter().router
wallet_hold_router = WalletHoldRouter().router
transaction_router = TransactionRouter().router
proposal_router = ProposalRouter().router
