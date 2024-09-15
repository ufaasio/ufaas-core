from fastapi_mongo_base.models import OwnedEntity
from pydantic import model_validator
from pymongo import ASCENDING, IndexModel

from apps.business_mongo.schemas import Config
from server.config import Settings


class Business(OwnedEntity):
    name: str
    domain: str
    description: str | None = None
    config: Config = Config()

    class Settings(OwnedEntity.Settings):
        indexes = OwnedEntity.Settings.indexes + [
            IndexModel([("name", ASCENDING)], unique=True),
            IndexModel([("domain", ASCENDING)], unique=True),
        ]

    @property
    def root_url(self):
        if self.domain.startswith("http"):
            return self.domain
        return f"https://{self.domain}"

    @classmethod
    async def get_by_origin(cls, origin: str):
        return await cls.find_one(cls.domain == origin)

    @classmethod
    async def get_by_name(cls, name: str):
        return await cls.find_one(cls.name == name)

    @model_validator(mode="before")
    def validate_domain(cls, data: dict):
        if not data.get("domain"):
            business_name_domain = f"{data.get('name')}.{Settings.root_url}"
            data["domain"] = business_name_domain

        return data

    @classmethod
    async def create_item(cls, data: dict):
        business = await super().create_item(data)
        await business.create_wallet()
        return business

    async def create_wallet(self) -> bool:
        from apps.accounting.models import Wallet

        wallet = await Wallet.create_item(
            {
                # "uid": self.uid,
                "user_id": self.user_id,
                "business_name": self.name,
            }
        )

        return bool(wallet)
