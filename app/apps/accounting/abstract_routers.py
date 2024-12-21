from typing import TypeVar

from fastapi_mongo_base.models import BusinessEntity
from fastapi_mongo_base.schemas import BusinessEntitySchema
from ufaas_fastapi_business.routes import AbstractAuthRouter

from apps.base.models import BusinessEntity as BusinessEntitySQL
from apps.business.routes import AbstractSQLBusinessRouter as AbstractSQLBusinessRouter

T = TypeVar("T", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


# class AbstractAuthRouter(AbstractBusinessRouter[T, TS]):
#     async def get_auth(self, request: Request) -> AuthorizationData:
#         return await authorization_middleware(request)

#     async def list_items(
#         self,
#         request: Request,
#         offset: int = Query(0, ge=0),
#         limit: int = Query(10, ge=0, le=Settings.page_max_limit),
#     ):
#         auth = await self.get_auth(request)
#         items, total = await self.model.list_total_combined(
#             user_id=auth.user_id,
#             business_name=auth.business.name,
#             offset=offset,
#             limit=limit,
#         )

#         items_in_schema = [self.list_item_schema(**item.model_dump()) for item in items]

#         return PaginatedResponse(
#             items=items_in_schema, offset=offset, limit=limit, total=total
#         )

#     async def retrieve_item(self, request: Request, uid: uuid.UUID):
#         auth = await self.get_auth(request)
#         item = await self.get_item(
#             uid, user_id=auth.user_id, business_name=auth.business.name
#         )
#         return item

#     async def create_item(self, request: Request, data: dict):
#         auth = await self.get_auth(request)
#         item = self.model(
#             business_name=auth.business.name,
#             **data,
#         )
#         await item.save()
#         return item

#     async def update_item(self, request: Request, uid: uuid.UUID, data: dict):
#         auth = await self.get_auth(request)
#         item = await self.get_item(
#             uid, user_id=auth.user_id, business_name=auth.business.name
#         )

#         item = await self.model.update_item(item, data)
#         return item

#     async def delete_item(self, request: Request, uid: uuid.UUID):
#         auth = await self.get_auth(request)
#         item = await self.get_item(
#             uid, user_id=auth.user_id, business_name=auth.business.name
#         )
#         item = await self.model.delete_item(item)
#         return item


TSQL = TypeVar("TSQL", bound=BusinessEntitySQL)


class AbstractAuthSQLRouter(
    AbstractSQLBusinessRouter[TSQL, TS], AbstractAuthRouter[TSQL, TS]
):
    pass
