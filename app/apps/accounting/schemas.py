import uuid
from datetime import datetime

from apps.base.schemas import BaseEntitySchema


class TransactionSchema(BaseEntitySchema):
    wallet_id: uuid.UUID
    amount: float
    balance_after: float
    timestamp: datetime


class ProposalSchema(BaseEntitySchema):
    wallet_id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    currency: str
    status: str
    timestamp: datetime


class WalletSchema(BaseEntitySchema):
    business_id: uuid.UUID
    user_id: uuid.UUID
    currency: str
    balance: float
    transactions: list[TransactionSchema] = []
    proposals: list[ProposalSchema] = []


class PermissionSchema(BaseEntitySchema):
    business_id: uuid.UUID
    third_party_app_id: uuid.UUID
    can_submit_proposal: bool
