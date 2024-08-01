import uuid
from apps.base.schemas import BaseEntitySchema


class AppSchema(BaseEntitySchema):
    name: str
    domain: str


class PermissionSchema(BaseEntitySchema):
    business_id: uuid.UUID
    third_party_app_id: uuid.UUID
    can_submit_proposal: bool
