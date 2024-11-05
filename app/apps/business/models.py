from sqlalchemy import JSON
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column
from ufaas_fastapi_business.schemas import Config

from apps.base.models import BaseEntity
from server.db import async_session


class Business(BaseEntity):
    name: Mapped[str] = mapped_column(index=True, unique=True)
    domain: Mapped[str] = mapped_column(index=True, unique=True)

    config: Mapped[Config] = mapped_column(JSON, default=Config())

    @classmethod
    async def get_by_origin(cls, origin: str):
        domain = origin.split("//")[-1].split("/")[0]
        async with async_session() as session:
            result = await session.execute(select(cls).where(cls.domain == domain))
            business = result.scalars().first()

        return business

    # wallets = relationship("Wallet", back_populates="business")
    # permissions = relationship("Permission", back_populates="business")
    # proposals = relationship("Proposal", back_populates="business")
    # transactions = relationship("Transaction", back_populates="business")
