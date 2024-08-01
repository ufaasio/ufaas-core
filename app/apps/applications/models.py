import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import BaseEntity, BusinessEntity


class Application(BaseEntity):
    name: Mapped[str] = mapped_column(index=True)
    domain: Mapped[str] = mapped_column(index=True)

    permissions = relationship("Permission", back_populates="application")


class Permission(BusinessEntity):
    app_id: Mapped[uuid.UUID] = mapped_column(index=True)
    write_access: Mapped[bool] = mapped_column(default=False)

    # business = relationship("Business", back_populates="permissions")
    application = relationship("Application", back_populates="permissions")
