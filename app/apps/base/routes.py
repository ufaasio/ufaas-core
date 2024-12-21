from typing import TypeVar

from fastapi_mongo_base.routes import AbstractBaseRouter

from .models import BaseEntity
from .schemas import BaseEntitySchema

# Define a type variable
TSQL = TypeVar("TSQL", bound=BaseEntity)
TS = TypeVar("TS", bound=BaseEntitySchema)


class AbstractSQLBaseRouter(AbstractBaseRouter[TSQL, TS]):
    pass
