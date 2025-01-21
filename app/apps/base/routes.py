from typing import TypeVar

from apps.base.models import BusinessEntity
from fastapi_mongo_base.routes import AbstractBaseRouter
from fastapi_mongo_base.schemas import BusinessEntitySchema
from ufaas_fastapi_business.routes import AbstractAuthRouter, AbstractBusinessBaseRouter

from .models import BaseEntity
from .schemas import BaseEntitySchema

# Define a type variable
TSQL = TypeVar("TSQL", bound=BaseEntity)
TS = TypeVar("TS", bound=BaseEntitySchema)


class AbstractSQLBaseRouter(AbstractBaseRouter[TSQL, TS]):
    pass


TBSQL = TypeVar("TBSQL", bound=BusinessEntity)
TBS = TypeVar("TBS", bound=BusinessEntitySchema)


class AbstractSQLBusinessRouter(
    AbstractSQLBaseRouter[TBSQL, TBS], AbstractBusinessBaseRouter[TBSQL, TBS]
):
    pass


class AbstractAuthSQLRouter(
    AbstractSQLBusinessRouter[TBSQL, TBS], AbstractAuthRouter[TBSQL, TBS]
):
    pass
