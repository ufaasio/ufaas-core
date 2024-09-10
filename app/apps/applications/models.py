import uuid

from apps.base_mongo.models import BaseEntity, OwnedEntity
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from .schemas import AppDomainSchema, AuthorizedDomainSchema


class Application(OwnedEntity):
    name: str
    domain: str
    api_doc_url: str
    is_active: bool = False

    permissions: list[uuid.UUID] = []
    description: str | None = None
    logo: str | None = None
    is_published: bool = False

    support_email: str | None = None
    app_domain_info: AppDomainSchema = AppDomainSchema()
    developer_contact_emails: list[str] = []
    test_users: list[uuid.UUID | str] = []

    authorized_domains: AuthorizedDomainSchema = AuthorizedDomainSchema()

    @classmethod
    def create_exclude_set(cls) -> list[str]:
        return super().create_exclude_set() + ["is_active"]

    class Settings:
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
            IndexModel([("domain", ASCENDING)], unique=True),
        ]


class BasePermission(BaseEntity):
    scope: str = Field(
        description="Permission scope",
        json_schema_extra={"index": True, "unique": True},
    )
    description: str | None = None

    class Settings:
        indexes = [
            IndexModel([("scope", ASCENDING)], unique=True),
        ]
