from apps.base.schemas import PaginatedResponse
from apps.business.middlewares import get_business
from apps.business.models import Business
from apps.business.routes import AbstractBusinessBaseRouter
from fastapi import Depends, Query, Request
from server.config import Settings
from server.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from usso.fastapi import jwt_access_security

from .models import Proposal, Transaction, Wallet, WalletHold
from .schemas import ProposalSchema, TransactionSchema, WalletHoldSchema, WalletSchema


class WalletRouter(AbstractBusinessBaseRouter[Wallet, WalletSchema]):
    def __init__(self):
        super().__init__(
            model=Wallet,
            user_dependency=jwt_access_security,
            # prefix="/wallets",
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
        # self.router.add_api_route(
        #     "/",
        #     self.create_item,
        #     methods=["POST"],
        #     response_model=self.create_response_schema,
        #     status_code=201,
        # )

    async def list_items(
        self,
        request: Request,
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=0, le=Settings.page_max_limit),
        business: Business = Depends(get_business),
        session: AsyncSession = Depends(get_db_session),
    ):
        user = await self.get_user(request)
        limit = max(1, min(limit, Settings.page_max_limit))

        items = [
            self.schema(**item.__dict__)
            for item in await self.model.list_items(
                session,
                offset=offset,
                limit=limit,
                user_id=user.uid,
                business_name=business.name,
            )
        ]
        total = await self.model.total_count(
            session, user_id=user.uid, business_name=business.name
        )
        return PaginatedResponse(items=items, offset=offset, limit=limit, total=total)


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
