import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from fastapi_mongo_base.schemas import BusinessOwnedEntitySchema
from fastapi_mongo_base.utils.bsontools import decimal_amount
from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from core.currency import Currency


class WalletType(str, Enum):
    user = "user"
    business = "business"
    app = "app"
    app_operational = "app_operational"
    app_income = "app_income"


class WalletSchema(BusinessOwnedEntitySchema):
    wallet_type: WalletType = WalletType.user
    main_currency: Currency = Currency.none

    is_default: bool = True

    @classmethod
    def create_exclude_set(cls) -> list[str]:
        return list(
            set(super().create_exclude_set() + ["business_name", "user_id"]) - {"uid"}
        )

    @field_serializer("wallet_type")
    def serialize_wallet_type(self, wallet_type: WalletType) -> str:
        return wallet_type.value

    @field_serializer("main_currency")
    def serialize_main_currency(self, main_currency: Currency) -> str:
        return main_currency.value


class WalletDetailSchema(WalletSchema):
    balance: dict[str, Decimal] = {}

    model_config = ConfigDict(allow_inf_nan=True)

    @field_serializer("balance")
    def serialize_balance(self, balance: dict[str, Decimal]) -> dict[str, Decimal]:
        return {k: (v if v.is_finite() else Decimal(0)) for k, v in balance.items()}


class WalletCreateSchema(BaseModel):
    user_id: uuid.UUID
    meta_data: dict | None = None

    wallet_type: WalletType = WalletType.user
    main_currency: Currency = Currency.none
    is_default: bool = False

    @model_validator(mode="before")
    def validate_wallet_type(cls, values: dict):
        if values.get("wallet_type") and not values.get("main_currency"):
            raise ValueError("main_currency is required for income wallet")
        return values


class WalletUpdateSchema(BaseModel):
    meta_data: dict | None = None
    is_default: bool | None = None


class WalletHoldSchema(BusinessOwnedEntitySchema):
    wallet_id: uuid.UUID
    currency: str
    amount: Decimal
    expires_at: datetime
    status: str
    description: str | None = None

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        return decimal_amount(value)


class WalletHoldCreateSchema(BaseModel):
    amount: Decimal
    expires_at: datetime
    status: str = "active"
    meta_data: dict | None = None
    description: str | None = None


class WalletHoldUpdateSchema(BaseModel):
    expires_at: datetime | None = None
    status: str | None = None
    meta_data: dict | None = None
    description: str | None = None


class TransactionSchema(BusinessOwnedEntitySchema):
    proposal_id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    currency: str
    balance: Decimal
    description: str | None = None
    note: str | None = None

    model_config = ConfigDict(allow_inf_nan=True)

    @field_serializer("balance", "amount")
    def serialize_balance(self, value):
        return str(value)


class TransactionNoteUpdateSchema(BaseModel):
    note: str


class Participant(BaseModel):
    wallet_id: uuid.UUID
    amount: Decimal

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        return decimal_amount(value)


class ProposalSchema(BusinessOwnedEntitySchema):
    issuer_id: uuid.UUID
    amount: Decimal
    description: str | None = None
    note: str | None = None
    currency: str
    # status: str
    task_status: str
    participants: list[Participant]

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        return decimal_amount(value)


class ProposalCreateSchema(BaseModel):
    amount: Decimal
    description: str | None = None
    note: str | None = None
    currency: str
    task_status: Literal["draft", "init"] = "draft"
    participants: list[Participant]
    meta_data: dict | None = None


class ProposalUpdateSchema(BaseModel):
    # status: str | None
    task_status: Literal["init"] | None = None
    description: str | None = None
    note: str | None = None
    meta_data: dict | None = None
