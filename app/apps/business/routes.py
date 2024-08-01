from typing import TypeVar

from usso.fastapi import jwt_access_security

from apps.base.models import BusinessEntity
from apps.base.routes import AbstractBaseRouter
from apps.base.schemas import BusinessEntitySchema

from .models import Business
from .schemas import BusinessSchema

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractBusinessBaseRouter(AbstractBaseRouter[T, TS]):
    # async def list_items(
    #     self,
    #     request: Request,
    #     offset: int = 0,
    #     limit: int = 10,
    #     business: Business = Depends(get_business),
    # ):
    #     user = await self.get_user(request)
    #     limit = max(1, min(limit, Settings.page_max_limit))

    #     items_query = (
    #         self.model.get_query(business_name=business.name, user_id=user.uid)
    #         .sort("-created_at")
    #         .skip(offset)
    #         .limit(limit)
    #     )
    #     items = await items_query.to_list()
    #     return items

    # async def retrieve_item(
    #     self,
    #     request: Request,
    #     uid,
    #     business: Business = Depends(get_business),
    # ):
    #     user = await self.get_user(request)
    #     item = await self.model.get_item(
    #         uid, business_name=business.name, user_id=user.uid
    #     )
    #     if item is None:
    #         raise BaseHTTPException(
    #             status_code=404,
    #             error="item_not_found",
    #             message=f"{self.model.__name__.capitalize()} not found",
    #         )
    #     return item

    # async def create_item(
    #     self,
    #     request: Request,
    #     # business: Business = Depends(get_business),
    # ):
    #     user = await self.get_user(request)
    #     item = await create_dto_business(self.model)(request, user)

    #     await item.save()
    #     return item

    # async def update_item(
    #     self,
    #     request: Request,
    #     uid,
    #     # business: Business = Depends(get_business),
    # ):
    #     user = await self.get_user(request)
    #     item = await update_dto_business(self.model)(request, user)
    #     if item is None:
    #         raise BaseHTTPException(
    #             status_code=404,
    #             error="item_not_found",
    #             message=f"{self.model.__name__.capitalize()} not found",
    #         )
    #     await item.save()
    #     return item

    # async def delete_item(
    #     self,
    #     request: Request,
    #     uid,
    #     business: Business = Depends(get_business),
    # ):
    #     user = await self.get_user(request)
    #     item = await self.model.get_item(
    #         uid, business_name=business.name, user_id=user.uid
    #     )
    #     if item is None:
    #         raise BaseHTTPException(
    #             status_code=404,
    #             error="item_not_found",
    #             message=f"{self.model.__name__.capitalize()} not found",
    #         )
    #     item.is_deleted = True
    #     await item.save()
    #     return item
    pass


class BusinessRouter(AbstractBaseRouter[Business, BusinessSchema]):
    def __init__(self):
        super().__init__(
            model=Business,
            user_dependency=jwt_access_security,
            prefix="/businesses",
        )


router = BusinessRouter().router
