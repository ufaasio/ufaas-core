from typing import TypeVar

from fastapi_mongo_base.schemas import BusinessEntitySchema
from ufaas_fastapi_business.routes import AbstractAuthRouter, AbstractBusinessBaseRouter

from apps.base.models import BusinessEntity
from apps.base.routes import AbstractSQLBaseRouter

TSQL = TypeVar("TSQL", bound=BusinessEntity)
TS = TypeVar("TS", bound=BusinessEntitySchema)


class AbstractSQLBusinessRouter(
    AbstractSQLBaseRouter[TSQL, TS], AbstractBusinessBaseRouter[TSQL, TS]
):
    pass


class AbstractAuthSQLRouter(
    AbstractSQLBusinessRouter[TSQL, TS], AbstractAuthRouter[TSQL, TS]
):
    pass
