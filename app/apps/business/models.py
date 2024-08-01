from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import BaseEntity


class Business(BaseEntity):
    name: Mapped[str] = mapped_column(index=True)
    domain: Mapped[str] = mapped_column(index=True)

    # wallets = relationship("Wallet", back_populates="business")
    # permissions = relationship("Permission", back_populates="business")
    # proposals = relationship("Proposal", back_populates="business")
    # transactions = relationship("Transaction", back_populates="business")
