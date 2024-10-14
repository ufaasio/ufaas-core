import json
from typing import Any

from core.currency import Currency
from fastapi_mongo_base.schemas import OwnedEntitySchema
from pydantic import BaseModel, model_validator
from server.config import Settings
from usso.fastapi.auth_middleware import JWTConfig


class Config(BaseModel):
    core_url: str = "https://core.ufaas.io/"
    api_os_url: str = "https://core.ufaas.io/api/v1/apps"
    sso_url: str = "https://sso.ufaas.io/app-auth/access"
    core_sso_url: str = "https://sso.ufaas.io/app-auth/access"

    allowed_origins: list[str] = []
    jwt_config: JWTConfig = JWTConfig(**json.loads(Settings.JWT_CONFIG))
    default_currency: str = "IRR"

    def __hash__(self):
        return hash(self.model_dump_json())


class BusinessSchema(OwnedEntitySchema):
    name: str
    domain: str

    description: str | None = None
    config: Config = Config()


class BusinessDataCreateSchema(BaseModel):
    name: str
    domain: str | None = None

    meta_data: dict[str, Any] | None = None
    description: str | None = None
    config: Config = Config()

    @model_validator(mode="before")
    def validate_domain(cls, data: dict):
        if not data.get("domain"):
            business_name_domain = f"{data.get('name')}.{Settings.root_url}"
            data["domain"] = business_name_domain

        return data


class BusinessDataUpdateSchema(BaseModel):
    name: str | None = None
    domain: str | None = None
    meta_data: dict[str, Any] | None = None
    description: str | None = None
    config: Config | None = None
