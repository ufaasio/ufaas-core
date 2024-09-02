import logging
import os
from typing import AsyncGenerator

import debugpy
import httpx
import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from apps.base_mongo import models as base_mongo_models
from server.config import Settings
from server.server import app as fastapi_app
from utils.basic import get_all_subclasses

from .constants import StaticData


# Async setup function to initialize the database with Beanie
async def init_db():
    client = AsyncMongoMockClient()
    database = client.get_database("test_db")
    await init_beanie(
        database=database,
        document_models=get_all_subclasses(base_mongo_models.BaseEntity),
    )


@pytest_asyncio.fixture(scope="session")
async def db():
    Settings.config_logger()
    logging.info("Initializing database")
    await init_db()
    logging.info("Database initialized")
    yield
    logging.info("Cleaning up database")

    # for model in get_all_subclasses(base_mongo_models.BaseEntity):
    #     print(f"Deleting all {model}")
    #     await model.delete_all()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture to provide an AsyncClient for FastAPI app."""
    # async with LifespanManager(fastapi_app) as manager:
    #     async with httpx.AsyncClient(
    #         transport=httpx.ASGITransport(app=manager.app), base_url="http://test"
    #     ) as ac:
    #         yield ac
    async with httpx.AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def access_token():
    data = {
        "refresh_token": StaticData.refresh_token,
    }
    async with httpx.AsyncClient(base_url="https://sso.ufaas.io") as client:
        response = await client.post("/auth/refresh", json=data)
        return response.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def setup_debugpy():
    # Check if we should start debugpy
    if os.getenv("DEBUGPY", "False").lower() in ("true", "1", "yes"):
        print("Starting debugpy for remote debugging...")
        debugpy.listen(("0.0.0.0", 3020))  # You can change the port if needed
        print("Waiting for debugger to attach...")
        debugpy.wait_for_client()
        print("Debugger attached!")
