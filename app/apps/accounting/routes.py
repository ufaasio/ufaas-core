import asyncio
import uuid

import fastapi
from apps.business_mongo.middlewares import AuthorizationData, AuthorizationException
from core.exceptions import BaseHTTPException
from fastapi import Query, Request
from fastapi_mongo_base.routes import AbstractTaskRouter
from fastapi_mongo_base.schemas import PaginatedResponse
from server.config import Settings

from .abstract_routers import AbstractAuthRouter, AbstractAuthSQLRouter
from .models import Proposal, Transaction, TransactionNote, Wallet, WalletHold
from .schemas import (
    ProposalCreateSchema,
    ProposalSchema,
    ProposalUpdateSchema,
    TransactionNoteUpdateSchema,
    TransactionSchema,
    WalletCreateSchema,
    WalletDetailSchema,
    WalletHoldCreateSchema,
    WalletHoldSchema,
    WalletHoldUpdateSchema,
    WalletUpdateSchema,
)


class WalletRouter(AbstractAuthRouter[Wallet, WalletDetailSchema]):
    def __init__(self):
        super().__init__(
            model=Wallet,
            schema=WalletDetailSchema,
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

        items, total = await self.model.list_total_combined(
            user_id=auth.user_id,
            business_name=auth.business.name,
            offset=offset,
            limit=limit,
        )
        balances = await asyncio.gather(*[item.get_balance() for item in items])
        items_in_schema = [
            self.list_item_schema(**item.model_dump(), balance=balance)
            for item, balance in zip(items, balances)
        ]
        paginated_response = PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

        if auth.issuer_type == "Business" or paginated_response.total > 0:
            # TODO check waht to do if app
            return paginated_response

        items = [
            await self.model.create_item(
                dict(
                    user_id=auth.user_id,
                    business_name=auth.business.name,
                    main_currency=auth.business.config.default_currency,
                    wallet_type="user",
                )
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
        if auth.issuer_type == "User":
            raise AuthorizationException("User cannot create wallet")

        # TODO check if creating with this wallet_type is authorized

        item: Wallet = await super().create_item(request, data.model_dump())
        balance = await item.get_balance()
        return self.create_response_schema(**item.model_dump(), balance=balance)

    async def update_item(
        self, request: Request, uid: uuid.UUID, data: WalletUpdateSchema
    ):
        auth = await self.get_auth(request)
        if auth.issuer_type == "User":
            raise AuthorizationException("User cannot update wallet")

        # TODO check app permissions

        item: Wallet = await super().update_item(
            request, uid, data.model_dump(exclude_none=True)
        )
        balance = await item.get_balance()
        return self.update_response_schema(**item.model_dump(), balance=balance)

    async def delete_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        if auth.issuer_type == "User":
            raise AuthorizationException("User cannot create wallet")

        # item = await super().delete_item(request, uid)
        item: Wallet = await self.get_item(
            uid, user_id=auth.user_id, business_name=auth.business.name
        )
        balance = await item.get_balance()
        for key, value in balance.items():
            if value != 0:
                raise BaseHTTPException(
                    400,
                    error="not_empty",
                    message=f"Wallet is not empty {key}: {value}",
                )

        item = await self.model.delete_item(item)
        return self.delete_response_schema(**item.model_dump(), balance=balance)


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

        if auth.issuer_type == "User":
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
        if auth.issuer_type == "User":
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
        self.router.add_api_route(
            "/{uid:uuid}",
            self.update_item,
            methods=["PATCH"],
            response_model=self.update_response_schema,
            status_code=200,
        )

    async def get_in_schema(self, item: Transaction):
        return self.schema(**item.__dict__, note=await item.get_note())

    async def list_items(
        self,
        request: Request,
        wallet_id: uuid.UUID | None = None,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        auth = await self.get_auth(request)
        items, total = await self.model.list_total_combined(
            user_id=auth.user_id,
            business_name=auth.business.name,
            wallet_id=wallet_id,
            offset=offset,
            limit=limit,
        )

        items_in_schema = await asyncio.gather(
            *[self.get_in_schema(item) for item in items]
        )
        return PaginatedResponse(
            items=items_in_schema, offset=offset, limit=limit, total=total
        )

    async def retrieve_item(
        self, request: Request, uid: uuid.UUID, wallet_id: uuid.UUID | None = None
    ):
        auth = await self.get_auth(request)
        item = await self.get_item(
            uid=uid,
            user_id=auth.user_id,
            business_name=auth.business.name,
            wallet_id=wallet_id,
        )
        return await self.get_in_schema(item)

    async def update_item(
        self,
        request: Request,
        uid: uuid.UUID,
        data: TransactionNoteUpdateSchema,
        wallet_id: uuid.UUID | None = None,
    ):
        auth = await self.get_auth(request)
        item: Transaction = await self.get_item(
            uid,
            user_id=auth.user_id,
            business_name=auth.business.name,
            wallet_id=wallet_id,
        )
        await TransactionNote(
            transaction_id=uid,
            business_name=item.business_name,
            user_id=auth.user_id,
            **data.model_dump(),
        ).save()
        return await self.get_in_schema(item)


class TransactionWRouter(TransactionRouter):
    def __init__(self):
        super(TransactionRouter, self).__init__(
            model=Transaction,
            schema=TransactionSchema,
            user_dependency=None,
            prefix="/wallets/{wallet_id:uuid}/transactions",
            tags=["Accounting"],
        )

    def config_routes(self, **kwargs):
        super().config_routes(**kwargs)


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
        if auth.issuer_type == "User":
            raise AuthorizationException("User do not have access to proposal")
        return auth

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
    ):
        return await super().list_items(request, offset, limit)

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

        item: Proposal = await self.model.update_item(
            item, data.model_dump(exclude_none=True)
        )

        if item.task_status == "init":
            return await self.start_item(request, item.uid)

        return item

    async def start_item(self, request: Request, uid: uuid.UUID):
        auth = await self.get_auth(request)
        # TODO check who can start processing of the proposal
        item: Proposal = await self.get_item(
            uid, business_name=auth.business.name
        )
        await item.start_processing()
        return ProposalSchema(**item.model_dump())


wallet_router = WalletRouter().router
wallet_hold_router = WalletHoldRouter().router
wallet_hold_router_business = WalletHoldHRouter().router
transaction_router = TransactionRouter().router
transaction_wallet_router = TransactionWRouter().router
proposal_router = ProposalRouter().router

router = fastapi.APIRouter()
router.include_router(wallet_router)
router.include_router(wallet_hold_router)
router.include_router(wallet_hold_router_business)
router.include_router(transaction_router)
router.include_router(transaction_wallet_router)
router.include_router(proposal_router)
