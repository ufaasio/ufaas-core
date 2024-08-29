import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel

from apps.base.models import BaseEntity
from server.config import Settings


class Config(BaseModel):
    cors_domains: str = ""
    trash_timeout: int = 30  # days
    singed_file_timeout: int = 60 * 60  # seconds
    jwt_secret: dict = json.loads(Settings.JWT_SECRET)


class Business(BaseEntity):
    name: Mapped[str] = mapped_column(index=True, unique=True)
    domain: Mapped[str] = mapped_column(index=True, unique=True)

    config: Config

    @classmethod
    async def get_by_origin(cls, origin: str, session: AsyncSession):
        domain = origin.split("//")[-1].split("/")[0]
        result = await session.execute(select(cls).where(cls.domain == domain))
        business = result.scalars().first()

        return business

    # wallets = relationship("Wallet", back_populates="business")
    # permissions = relationship("Permission", back_populates="business")
    # proposals = relationship("Proposal", back_populates="business")
    # transactions = relationship("Transaction", back_populates="business")
