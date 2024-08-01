from usso.fastapi import jwt_access_security

from apps.business.routes import AbstractBusinessBaseRouter

from .models import Proposal, Transaction, Wallet, WalletHold


class WalletRouter(AbstractBusinessBaseRouter[Wallet]):
    def __init__(self):
        super().__init__(
            model=Wallet,
            user_dependency=jwt_access_security,
            prefix="/wallet",
            tags=["accounting"],
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


class WalletHoldRouter(AbstractBusinessBaseRouter[WalletHold]):
    def __init__(self):
        super().__init__(
            model=WalletHold,
            user_dependency=jwt_access_security,
            prefix="/wallet-hold",
            tags=["accounting"],
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


class TransactionRouter(AbstractBusinessBaseRouter[Transaction]):
    def __init__(self):
        super().__init__(
            model=Transaction,
            user_dependency=jwt_access_security,
            prefix="/transaction",
            tags=["accounting"],
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


class ProposalRouter(AbstractBusinessBaseRouter[Proposal]):
    def __init__(self):
        super().__init__(
            model=Proposal,
            user_dependency=jwt_access_security,
            prefix="/proposal",
            tags=["accounting"],
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
