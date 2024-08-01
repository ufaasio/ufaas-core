import uuid
from datetime import datetime
from decimal import Decimal

from apps.base.schemas import BaseEntitySchema, BusinessEntitySchema, BusinessOwnedEntitySchema


class WalletSchema(BusinessOwnedEntitySchema):
    balance: Decimal
    held_amount: Decimal
    # transactions: list[TransactionSchema] = []
    # proposals: list[ProposalSchema] = []


class WalletHoldSchema(BusinessOwnedEntitySchema):
    wallet_id: uuid.UUID
    amount: Decimal
    expires_at: datetime
    status: str


class TransactionSchema(BusinessOwnedEntitySchema):
    proposal_id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    currency: str
    balance: Decimal
    description: str
    note: str

from .models import Participant
class ProposalSchema(BusinessOwnedEntitySchema):
    issuer_id: uuid.UUID
    amount: Decimal
    description: str
    note: str
    status: str
    participants: list[Participant]