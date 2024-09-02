import uuid

from pymongo import ASCENDING, IndexModel

from apps.base_mongo.models import BaseEntity, BusinessEntity


class Application(BaseEntity):
    name: str
    domain: str

    class Settings:
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
            IndexModel([("domain", ASCENDING)], unique=True),
        ]

    # permissions = relationship("Permission", back_populates="application")


class Permission(BusinessEntity):
    app_id: uuid.UUID
    write_access: bool = False

    class Settings:
        indexes = [
            IndexModel([("app_id", ASCENDING), ("user_id", ASCENDING)], unique=True),
        ]

    # business = relationship("Business", back_populates="permissions")
    # application = relationship("Application", back_populates="permissions")
