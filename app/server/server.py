import logging
from contextlib import asynccontextmanager

import fastapi
from fastapi_mongo_base.core import app_factory

from apps.accounting.routes import router as accounting_router
from core.middlewares import DynamicCORSMiddleware

from . import config, db


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):  # type: ignore
    """Initialize application services."""
    config.Settings.config_logger()

    await db.init_db()
    logging.info("Startup complete")
    yield
    logging.info("Shutdown complete")


app = app_factory.create_app(
    settings=config.Settings(),
    lifespan=lifespan,
    origins=[
        "http://localhost:8000",
        "http://localhost:3000",
    ],
)


app.add_middleware(DynamicCORSMiddleware)


app.include_router(accounting_router, prefix="/api/v1")
app.include_router(accounting_router, prefix="/api/v1/apps/core")


# Mount the htmlcov directory to be served at /coverage
# from fastapi.staticfiles import StaticFiles

# app.mount(
#     "/coverage", StaticFiles(directory=config.Settings.coverage_dir), name="coverage"
# )


# @app.get("/api/v1/health")
# async def health():
#     return {"status": "ok"}


# @app.get(f"{config.Settings.base_path}/logs", include_in_schema=False)
# async def logs():
#     from collections import deque

#     with open(config.Settings.base_dir / "logs" / "info.log", "rb") as f:
#         last_100_lines = deque(f, maxlen=100)

#     return [line.decode("utf-8") for line in last_100_lines]
