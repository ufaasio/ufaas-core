import json
from enum import Enum

from apps.base_mongo.models import OwnedEntity
from pydantic import BaseModel, model_validator
from pymongo import ASCENDING, IndexModel
from server.config import Settings

class Config(BaseModel):
    cors_domains: str = ""
    jwt_secret: dict = json.loads(Settings.JWT_SECRET)

    def __hash__(self):
        return hash(self.model_dump_json())

class Business(OwnedEntity):
    name: str
    description: str | None = None
    domain: str
    config: Config

    class Settings:
        indexes = [
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
    def validate_domain(data: dict):
        if not data.get("domain"):
            business_name_domain = f"{data.get('name')}.{Settings.root_url}"
            data["domain"] = business_name_domain

        return data
