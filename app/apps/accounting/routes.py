import uuid

from apps.base.schemas import PaginatedResponse
from apps.business.routes import AbstractBusinessBaseRouter as AbstractBusinessSQLRouter
from apps.business_mongo.middlewares import AuthorizationData, AuthorizationException
from core.exceptions import BaseHTTPException
from fastapi import Query, Request
from server.config import Settings

from .abstract_routers import AbstractAuthRouter
from .models import Proposal, Transaction, Wallet, WalletHold
from .schemas import (
    ProposalCreateSchema,
    ProposalSchema,
    ProposalUpdateSchema,
    TransactionSchema,
    WalletCreateSchema,
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
        self.retrieve_response_schema = WalletSchema
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
                user_id=auth.user_id, business_name=auth.business.name
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
        return WalletSchema(**item.model_dump(), balance=balance)

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
        return await super().update_item(request, uid, data.model_dump())

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
            prefix="/wallet",
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
            "/{wallet_id:uuid}/holds",
            self.list_items,
            methods=["GET"],
            response_model=self.list_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{wallet_id:uuid}/holds/{currency}",
            self.list_items,
            methods=["GET"],
            response_model=self.list_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/holds/{uid:uuid}",
            self.retrieve_item,
            methods=["GET"],
            response_model=self.retrieve_response_schema,
            status_code=200,
        )
        self.router.add_api_route(
            "/{wallet_id:uuid}/holds/{currency}",
            self.create_item,
            methods=["POST"],
            response_model=self.create_response_schema,
            status_code=201,
        )
        self.router.add_api_route(
            "/holds/{uid:uuid}",
            self.update_item,
            methods=["PATCH"],
            response_model=self.update_response_schema,
            status_code=200,
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

    async def retrieve_item(self, request: Request, uid: uuid.UUID):
        super().retrieve_item(request, uid)

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

        wallet: Wallet = await Wallet.get_item(wallet_id, auth.business.name)
        if wallet is None:
            raise BaseHTTPException(404, error="not_found", message="Wallet not found")

        data = data.model_dump() | dict(
            business_name=auth.business.name,
            wallet_id=wallet_id,
            currency=currency,
            user_id=wallet.user_id,
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
        return await super().update_item(request, uid, data.model_dump())


class TransactionRouter(AbstractBusinessSQLRouter[Transaction, TransactionSchema]):
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


class ProposalRouter(AbstractAuthRouter[Proposal, ProposalSchema]):
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
        return await super().create_item(request, data)

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: ProposalUpdateSchema
    ):
        return await super().update_item(request, uid, data)


wallet_router = WalletRouter().router
wallet_hold_router = WalletHoldRouter().router
transaction_router = TransactionRouter().router
proposal_router = ProposalRouter().router
