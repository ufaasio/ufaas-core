import asyncio
import uuid

from fastapi import Query, Request

from apps.base.schemas import PaginatedResponse
from apps.base_mongo.routes import AbstractTaskRouter
from apps.business_mongo.middlewares import AuthorizationData, AuthorizationException
from core.exceptions import BaseHTTPException
from server.config import Settings

from .abstract_routers import AbstractAuthRouter, AbstractAuthSQLRouter
from .models import Proposal, Transaction, Wallet, WalletHold
from .schemas import (
    ProposalCreateSchema,
    ProposalSchema,
    ProposalUpdateSchema,
    TransactionSchema,
    WalletCreateSchema,
    WalletDetailSchema,
    WalletHoldCreateSchema,
    WalletHoldSchema,
    WalletHoldUpdateSchema,
    WalletSchema,
    WalletUpdateSchema,
)


class WalletRouter(AbstractAuthRouter[Wallet, WalletSchema]):
    def __init__(self):
        super().__init__(
            model=Wallet,
            schema=WalletSchema,
            user_dependency=None,
            # prefix="/wallets",
            tags=["Accounting"],
        )

    def config_schemas(self, schema, **kwargs):
        super().config_schemas(schema)
        self.retrieve_response_schema = WalletDetailSchema
        self.create_request_schema = WalletCreateSchema
        self.update_request_schema = WalletUpdateSchema

    async def list_items(
        self,
        request: Request,
        user_id: uuid.UUID | None = None,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        auth = await self.get_auth(request)
        paginated_response = await super().list_items(request, offset, limit)

        if auth.business_or_user == "Business" or paginated_response.total > 0:
            return paginated_response

        items = [
            await self.model.create_item(
                dict(user_id=auth.user_id, business_name=auth.business.name)
            )
        ]
        total = 1
        items_in_schema = [self.list_item_schema(**item.model_dump()) for item in items]
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(self, request: Request, uid: uuid.UUID):
        item: Wallet = await super().retrieve_item(request, uid)
        balance = await item.get_balance()
        return self.retrieve_response_schema(**item.model_dump(), balance=balance)

    async def create_item(self, request: Request, data: WalletCreateSchema):
        auth = await self.get_auth(request)
        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot create wallet")
        return await super().create_item(request, data.model_dump())

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: WalletUpdateSchema
    ):
        auth = await self.get_auth(request)
        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot update wallet")
        return await super().update_item(
            request, uid, data.model_dump(exclude_none=True)
        )

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot create wallet")
        return await super().delete_item(request, uid)


class WalletHoldRouter(AbstractAuthRouter[WalletHold, WalletHoldSchema]):
    def __init__(self):
        super().__init__(
            model=WalletHold,
            schema=WalletHoldSchema,
            user_dependency=None,
            prefix="/wallets/{wallet_id:uuid}/holds",
            tags=["Hold"],
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
            "/{currency}",
            self.list_items,
            methods=["GET"],
            response_model=self.list_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{currency}",
            self.create_item,
            methods=["POST"],
            response_model=self.create_response_schema,
            status_code=201,
        )

    async def list_items(
        self,
        request: Request,
        wallet_id: uuid.UUID | None = None,
        currency: str | None = None,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        auth = await self.get_auth(request)

        items, total = await self.model.list_total_combined(
            user_id=auth.user_id,
            business_name=auth.business.name,
            wallet_id=wallet_id,
            currency=currency,
            offset=offset,
            limit=limit,
        )

        items_in_schema = [self.list_item_schema(**item.model_dump()) for item in items]

        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def create_item(
        self,
        request: Request,
        wallet_id: uuid.UUID,
        currency: str,
        data: WalletHoldCreateSchema,
    ):
        auth = await self.get_auth(request)

        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot create wallet hold")

        wallet: Wallet = await WalletRouter().get_item(
            wallet_id, business_name=auth.business.name
        )
        if wallet is None:
            raise BaseHTTPException(404, error="not_found", message="Wallet not found")

        data = data.model_dump() | dict(
            business_name=auth.business.name,
            wallet_id=wallet_id,
            currency=currency,
            user_id=wallet.user_id,
            wallet=wallet,
        )

        item = self.model(**data)
        await item.save()
        return self.create_response_schema(**item.model_dump())

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: WalletHoldUpdateSchema
    ):
        auth = await self.get_auth(request)
        if auth.business_or_user == "User":
            raise AuthorizationException("User cannot update wallet hold")
        return await super().update_item(
            request, uid, data.model_dump(exclude_none=True)
        )


class WalletHoldHRouter(WalletHoldRouter):
    def __init__(self):
        super(WalletHoldRouter, self).__init__(
            model=WalletHold,
            schema=WalletHoldSchema,
            user_dependency=None,
            prefix="/holds",
            tags=["Hold"],
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
            "/{uid:uuid}",
            self.update_item,
            methods=["PATCH"],
            response_model=self.update_response_schema,
            status_code=200,
        )


class TransactionRouter(AbstractAuthSQLRouter[Transaction, TransactionSchema]):
    def __init__(self):
        super().__init__(
            model=Transaction,
            schema=TransactionSchema,
            user_dependency=None,
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

    async def get_in_schema(self, item: Transaction):
        return self.schema(**item.__dict__, note=await item.note())

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

        items_in_schema = await asyncio.gather(
            *[self.get_in_schema(item) for item in items]
        )
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        item = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )
        return await self.get_in_schema(item)


class ProposalRouter(
    AbstractAuthRouter[Proposal, ProposalSchema],
    AbstractTaskRouter[Proposal, ProposalSchema],
):
    def __init__(self):
        super().__init__(
            model=Proposal,
            schema=ProposalSchema,
            user_dependency=None,
            # prefix="/proposal",
            # tags=["Accounting"],
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
        self.router.add_api_route(
            "/{uid:uuid}/start",
            self.start_item,
            methods=["POST"],
            response_model=self.retrieve_response_schema,
            status_code=200,
        )

    async def get_auth(self, request: Request) -> AuthorizationData:
        auth = await super().get_auth(request)
        if auth.business_or_user == "User":
            raise AuthorizationException("User do not have access to proposal")
        return auth

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        return await super().list_items(request, offset, limit)

    async def retrieve_item(self, request: Request, uid: uuid.UUID):
        return await super().retrieve_item(request, uid)

    async def create_item(self, request: Request, data: ProposalCreateSchema):
        if data.task_status and data.task_status not in ["draft", "init"]:
            raise BaseHTTPException(
                400, error="invalid_status", message="Invalid task status"
            )

        auth = await self.get_auth(request)
        data = data.model_dump() | dict(
            business_name=auth.business.name,
            issuer_id=auth.business.user_id,
            user_id=auth.business.user_id,
        )

        item: Proposal = self.model(**data)
        await item.save()

        if item.task_status == "init":
            return await self.start_item(request, item.uid)

        return self.create_response_schema(**item.model_dump())

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: ProposalUpdateSchema
    ):
        auth = await self.get_auth(request)
        item = await self.get_item(
            uid, business_name=auth.business.name, user_id=auth.user_id
        )

        if item.task_status != "draft":
            raise BaseHTTPException(
                400, error="invalid_status", message="Invalid task status"
            )

        if data.task_status and data.task_status != "init":
            raise BaseHTTPException(
                400, error="invalid_status", message="Invalid task status"
            )

        item: Proposal = await self.model.update_item(item, data.model_dump())

        if item.task_status == "init":
            return await self.start_item(request, item.uid)

        return item

    async def start_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        item: Proposal = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )
        await item.start_processing()
        return ProposalSchema(**item.model_dump())


wallet_router = WalletRouter().router
wallet_hold_router = WalletHoldRouter().router
wallet_hold_router_business = WalletHoldHRouter().router
transaction_router = TransactionRouter().router
proposal_router = ProposalRouter().router
