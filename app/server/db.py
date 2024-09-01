from typing import AsyncGenerator

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from server.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from utils.basic import get_all_subclasses

engine = create_async_engine(Settings.DATABASE_URL, future=True, echo=True)
async_session: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db():
    from apps.accounting import models as accounting_models
    from apps.applications import models as applications_models
    from apps.base.models import Base
    from apps.base_mongo import models as base_mongo_models

    # from apps.business import models as business_models
    [accounting_models, applications_models]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    client = AsyncIOMotorClient(Settings.mongo_uri)
    db = client.get_database(Settings.project_name)
    await init_beanie(
        database=db, document_models=get_all_subclasses(base_mongo_models.BaseEntity)
    )
    return db
