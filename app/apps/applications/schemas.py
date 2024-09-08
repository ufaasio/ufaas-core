import uuid

from apps.base.schemas import BaseEntitySchema


class AppDomainSchema(BaseEntitySchema):
    homepage: str | None = None
    terms_of_service: str | None = None
    privacy_policy: str | None = None


class AuthorizedDomainSchema(BaseEntitySchema):
    authorized_redirect_uris: list[str] = []
    authorized_origins: list[str] = []

    @property
    def authorized_domains(self):
        from urllib.parse import urlparse

        return list(
            set(
                urlparse(uri).netloc
                for uri in self.authorized_redirect_uris + self.authorized_origins
            )
        )


class AppSchema(BaseEntitySchema):
    name: str
    domain: str


class PermissionSchema(BaseEntitySchema):
    business_id: uuid.UUID
    third_party_app_id: uuid.UUID
    can_submit_proposal: bool
