import asyncio
from typing import AsyncGenerator

from apps.accounting import models as accounting_models
from apps.base.models import Base

# from apps.business_mongo import models as business_mongo_models
from beanie import init_beanie
from fastapi_mongo_base import models as base_mongo_models
from motor.motor_asyncio import AsyncIOMotorClient
from server.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi_mongo_base._utils import basic

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


async def init_mongo_db():
    client = AsyncIOMotorClient(Settings.mongo_uri)
    db = client.get_database(Settings.project_name)
    await init_beanie(
        database=db,
        document_models=[
            cls
            for cls in basic.get_all_subclasses(base_mongo_models.BaseEntity)
            if not (
                hasattr(cls, "Settings")
                and getattr(cls.Settings, "__abstract__", False)
            )
        ],
    )
    return db


async def init_db():
    _, db = await asyncio.gather(init_sql_db(), init_mongo_db())
    return db
