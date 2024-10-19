import json
import logging
from contextlib import asynccontextmanager

import fastapi
import pydantic
from core import exceptions
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from json_advanced import dumps
from usso.exceptions import USSOException

from . import config, db


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):  # type: ignore
    """Initialize application services."""
    config.Settings.config_logger()

    await db.init_db()
    logging.info("Startup complete")
    yield
    logging.info("Shutdown complete")


app = fastapi.FastAPI(
    title=config.Settings.project_name.replace("-", " ").title(),
    # description=DESCRIPTION,
    version="0.1.0",
    contact={
        "name": "Mahdi Kiani",
        "url": "https://github.com/mahdikiani/FastAPILaunchpad",
        "email": "mahdikiany@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/mahdikiani/FastAPILaunchpad/blob/main/LICENSE",
    },
    lifespan=lifespan,
)


@app.exception_handler(exceptions.BaseHTTPException)
async def base_http_exception_handler(
    request: fastapi.Request, exc: exceptions.BaseHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "error": exc.error},
    )


@app.exception_handler(USSOException)
async def usso_exception_handler(request: fastapi.Request, exc: USSOException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "error": exc.error},
    )


@app.exception_handler(pydantic.ValidationError)
@app.exception_handler(fastapi.exceptions.ResponseValidationError)
async def pydantic_exception_handler(
    request: fastapi.Request, exc: pydantic.ValidationError
):
    return JSONResponse(
        status_code=500,
        content={
            "message": str(exc),
            "error": "Exception",
            "erros": json.loads(dumps(exc.errors())),
        },
    )


@app.exception_handler(fastapi.exceptions.RequestValidationError)
async def request_validation_exception_handler(
    request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError
):
    logging.error(
        f"request_validation_exception:  {request.url} {exc}\n{(await request.body())[:100]}"
    )
    from fastapi.exception_handlers import request_validation_exception_handler

    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: fastapi.Request, exc: Exception):
    import traceback

    traceback_str = "".join(traceback.format_tb(exc.__traceback__))
    # body = request._body

    logging.error(f"Exception: {traceback_str} {exc}")
    logging.error(f"Exception on request: {request.url}")
    # logging.error(f"Exception on request: {await request.body()}")
    return JSONResponse(
        status_code=500,
        content={"message": str(exc), "error": "Exception"},
    )


origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from core.middlewares import DynamicCORSMiddleware

app.add_middleware(DynamicCORSMiddleware)

from apps.accounting.routes import router as accounting_router

# from apps.business_mongo.routes import router as business_router

# app.include_router(business_router, prefix="/api/v1")
app.include_router(accounting_router, prefix="/api/v1")
app.include_router(accounting_router, prefix="/api/v1/apps/core")
# app.include_router(application_router, prefix="/api/v1")


# Mount the htmlcov directory to be served at /coverage
# from fastapi.staticfiles import StaticFiles
# app.mount(
#     "/coverage", StaticFiles(directory=config.Settings.coverage_dir), name="coverage"
# )


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


config.Settings.config_logger()
