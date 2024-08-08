from apps.base.schemas import BaseEntitySchema


class BusinessSchema(BaseEntitySchema):
    name: str
    domain: str
