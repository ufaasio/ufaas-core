from apps.base.schemas import BaseEntitySchema


class AppSchema(BaseEntitySchema):
    name: str
    url: str
