from typing import TypeVar

from fastapi import Request
from usso import UserData

from apps.base.models import BusinessEntity, BusinessOwnedEntity
from apps.business.models import Business

from .middlewares import get_business

T = TypeVar("T", bound=BusinessEntity)
OT = TypeVar("OT", bound=BusinessOwnedEntity)


def create_dto_business(cls: OT):

    async def dto(request: Request, user: UserData | None = None, **kwargs):
        business: Business = await get_business(request)
        form_data: dict = await request.json()
        form_data.update(kwargs)
        form_data["business_name"] = business.name
        if form_data.get("user_id") and user.uid == business.user_id:
            return cls(**form_data)

        if user:
            form_data["user_id"] = user.uid

        return cls(**form_data)

    return dto


def update_dto_business(cls: OT):

    async def dto(request: Request, item: OT, user=None, **kwargs):
        form_data = await request.json()
        kwargs = {}
        if user:
            kwargs["user_id"] = user.uid

        for key, value in form_data.items():
            setattr(item, key, value)

        return item

    return dto
