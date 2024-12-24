import asyncio
from typing import AsyncGenerator

# from apps.business_mongo import models as business_mongo_models
from fastapi_mongo_base.core.db import init_mongo_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from apps.accounting import models as accounting_models
from apps.base.models import Base
from server.config import Settings

# from apps.business import models as business_models
# from apps.applications import models as applications_models


__all__ = ["accounting_models", "business_mongo_models"]

engine = create_async_engine(Settings.DATABASE_URL, future=True, echo=True)
async_session: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_sql_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


async def init_db():
    _, db = await asyncio.gather(init_sql_db(), init_mongo_db())
    return db
