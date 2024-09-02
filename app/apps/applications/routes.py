import aiohttp
from fastapi import Request, Response
from usso.fastapi import jwt_access_security

from apps.business.middlewares import get_business
from apps.business.models import Business
from apps.business.routes import AbstractBusinessBaseRouter
from core import exceptions

from .models import Application
from .schemas import AppSchema


class ApplicationRouter(AbstractBusinessBaseRouter[Application, AppSchema]):
    def __init__(self):
        super().__init__(
            model=Application,
            user_dependency=jwt_access_security,
            prefix="/apps",
            # tags=["Applications"],
        )


router = ApplicationRouter().router


async def proxy_request(
    request: Request,
    app_name: str,
    path: str,
    method: str,
):
    business: Business = await get_business(request)

    app: Application = await Application.find_one(
        Application.name == app_name, Application.business_name == business.name
    )
    if not app:
        raise exceptions.BaseHTTPException(
            status_code=404,
            error="Not Found",
            message=f"Application {app_name} not found",
        )

    url = f"{app.url}/{path}"
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=method,
            url=url,
            headers=request.headers,
            params=request.query_params,
            data=await request.body() if method in ["POST", "PUT", "PATCH"] else None,
        ) as response:
            content = await response.read()
            return Response(
                status_code=response.status,
                content=content,
                headers=dict(response.headers),
            )


@router.get("/{app_name}/{path:path}")
async def get_app(request: Request, app_name: str, path: str):
    return await proxy_request(request, app_name, path, "GET")


@router.post("/{app_name}/{path:path}")
async def post_app(request: Request, app_name: str, path: str):
    return await proxy_request(request, app_name, path, "POST")


@router.put("/{app_name}/{path:path}")
async def put_app(request: Request, app_name: str, path: str):
    return await proxy_request(request, app_name, path, "PUT")


@router.delete("/{app_name}/{path:path}")
async def delete_app(request: Request, app_name: str, path: str):
    return await proxy_request(request, app_name, path, "DELETE")


@router.patch("/{app_name}/{path:path}")
async def patch_app(request: Request, app_name: str, path: str):
    return await proxy_request(request, app_name, path, "PATCH")
