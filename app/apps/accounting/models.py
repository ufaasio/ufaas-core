import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from beanie import Link
from pydantic import field_validator
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.models import ImmutableBusinessOwnedEntity
from apps.base_mongo.models import BusinessOwnedEntity
from apps.base_mongo.tasks import TaskMixin

from .schemas import Participant


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Wallet(BusinessOwnedEntity):

    async def get_holds(
        self, currency: str | None = None, status: StatusEnum | None = StatusEnum.ACTIVE
    ):
        return await WalletHold.get_holds(
            user_id=self.user_id,
            business_name=self.business_name,
            wallet_id=self.uid,
            currency=currency,
            status=status,
        )

    async def get_transactions(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ):
        from server.db import async_session

        base_query = [Transaction.wallet_id == self.uid]
        if to_date is None:
            to_date = datetime.now()
        if from_date and to_date:
            base_query.append(Transaction.created_at >= from_date)
            base_query.append(Transaction.created_at <= to_date)

        async with async_session() as session:
            query = select(Transaction).where(*base_query).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_currencies(self):
        from server.db import async_session

        async with async_session() as session:
            query = (
                select(Transaction.currency)
                .where(Transaction.wallet_id == self.uid)
                .distinct()
            )
            result = await session.execute(query)
            return [item[0] for item in result.scalars().all()]

    async def get_balance(self, currency: str | None = None) -> dict[str, Decimal]:
        from server.db import async_session

        balance = {}
        if currency is None:
            for currency in await self.get_currencies():
                balance.update(await self.get_balance(currency))
            return balance

        async with async_session() as session:
            query = (
                select(Transaction.balance)
                .where(
                    Transaction.wallet_id == self.uid, Transaction.currency == currency
                )
                .order_by(Transaction.created_at.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return {currency: result.scalars().one_or_none() or Decimal(0)}

    async def get_held_amount(
        self,
        currency: str | None = None,
        status: StatusEnum | None = None,
    ) -> Decimal:
        current_time = datetime.now()
        pipeline = [
            {
                "$match": {
                    "wallet_id": self.uid,
                    "status": "active",
                    "expires_at": {"$gt": current_time},
                    "currency": currency,
                }
            },
            {"$group": {"_id": None, "total_amount": {"$sum": "$amount"}}},
        ]

        result = await WalletHold.aggregate(pipeline).to_list()

        if result:
            return Decimal(result[0]["total_amount"])
        else:
            return Decimal("0.00")


class WalletHold(BusinessOwnedEntity):
    wallet_id: uuid.UUID
    amount: Decimal
    expires_at: datetime
    status: StatusEnum
    currency: str
    description: str | None
    wallet: Link[Wallet]

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        from bson.decimal128 import Decimal128

        if type(value) == Decimal128:
            return Decimal(value.to_decimal())
        return value

    @classmethod
    def get_holds_query(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
    ):
        base_query = [
            cls.is_deleted == is_deleted,
            cls.user_id == user_id,
            cls.business_name == business_name,
        ]
        if wallet_id:
            base_query.append(cls.wallet_id == wallet_id)
        if currency:
            base_query.append(cls.currency == currency)

        if status:
            base_query.append(cls.status == status)

        if to_date is None:
            to_date = datetime.now()
        if from_date and to_date:
            base_query.append(cls.created_at >= from_date)
            base_query.append(cls.created_at <= to_date)
        else:
            base_query.append(cls.expires_at > datetime.now())

        return cls.find(*base_query)

    @classmethod
    async def get_holds(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        items = await cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
        ).to_list()

        return items

    @classmethod
    async def list_items(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ):
        offset, limit = cls.adjust_pagination(offset, limit)
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )

        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        return items

    @classmethod
    async def total_count(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )

        return await query.count()

    @classmethod
    async def list_total_combined(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ) -> tuple[list["WalletHold"], int]:
        offset, limit = cls.adjust_pagination(offset, limit)
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        total = await query.count()

        return items, total


class Transaction(ImmutableBusinessOwnedEntity):
    proposal_id: Mapped[uuid.UUID] = mapped_column(index=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    currency: Mapped[str] = mapped_column(index=True)
    balance: Mapped[Decimal]
    description: Mapped[str | None]

    async def note(self) -> str:
        query = TransactionNote.find(TransactionNote.transaction_id == self.uid).sort(
            "-created_at"
        )
        note = await query.to_list()
        return note[0].note if note else None


class TransactionNote(BusinessOwnedEntity):
    transaction_id: uuid.UUID
    note: str


class Proposal(BusinessOwnedEntity, TaskMixin):
    issuer: Literal["user", "business", "app"] = "business"
    issuer_id: uuid.UUID
    amount: Decimal
    currency: str
    description: str | None = None
    note: str | None = None
    # status: str | None

    participants: list[Participant]

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        from bson.decimal128 import Decimal128

        if type(value) == Decimal128:
            return Decimal(value.to_decimal())
        return value

    async def get_transactions(self):
        from server.db import async_session

        async with async_session() as session:
            query = select(Transaction).where(Transaction.proposal_id == self.uid)
            result = await session.execute(query)
            return result.scalars().all()

    async def start_processing(self):
        from .services import process_proposal

        await process_proposal(self)
