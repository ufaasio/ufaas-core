import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from apps.base.schemas import BusinessOwnedEntitySchema
from utils.numtools import decimal_amount


class WalletSchema(BusinessOwnedEntitySchema):
    pass


class WalletDetailSchema(BusinessOwnedEntitySchema):
    balance: dict[str, Decimal] = {}


class WalletCreateSchema(BaseModel):
    user_id: uuid.UUID
    meta_data: dict[str, Any] | None = None


class WalletUpdateSchema(BaseModel):
    meta_data: dict[str, Any] | None = None


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
    meta_data: dict[str, Any] | None = None
    description: str | None = None


class WalletHoldUpdateSchema(BaseModel):
    expires_at: datetime | None = None
    status: str | None = None
    meta_data: dict[str, Any] | None = None
    description: str | None = None


class TransactionSchema(BusinessOwnedEntitySchema):
    proposal_id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    currency: str
    balance: Decimal
    description: str | None = None
    note: str | None


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
    meta_data: dict[str, Any] | None = None


class ProposalUpdateSchema(BaseModel):
    # status: str | None
    task_status: Literal["init"] | None = None
    description: str | None = None
    note: str | None = None
    meta_data: dict[str, Any] | None = None
