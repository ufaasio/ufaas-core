import uuid
from typing import Literal

from apps.business_mongo.models import Business
from core.exceptions import BaseHTTPException
from fastapi import Request

from apps.base.auth_middlewares import Usso, UserData
from pydantic import BaseModel


class AuthorizationData(BaseModel):
    user: UserData | None
    user_id: uuid.UUID | None
    business: Business | None
    business_or_user: Literal["Business", "User"] | None
    authorized: bool = False
    app_id: str | None = None

class AuthorizationException(BaseHTTPException):
    def __init__(self, message: str):
        super().__init__(403, "authorization_error", message)

async def get_business(
    request: Request,
) -> Business:
    business = await Business.get_by_origin(request.url.hostname)
    if not business:
        raise BaseHTTPException(404, "business_not_found", "business not found")
    return business


async def authorized_request(request: Request) -> bool:
    return True


async def business_or_user(
    request: Request,
) -> tuple[Literal["Business", "User"], UserData]:
    business = await get_business(request)
    user = await Usso(jwt_secret=business.config.jwt_secret).jwt_access_security(
        request
    )

    if business.user_id == user.uid:
        return "Business", user
    return "User", user


async def authorization_middleware(request: Request) -> AuthorizationData:
    authorization = AuthorizationData()

    authorization.business = await get_business(request)
    authorization.user = await Usso(
        jwt_secret=authorization.business.config.jwt_secret
    ).jwt_access_security(request)

    if authorization.business.user_id == authorization.user.uid:
        authorization.business_or_user = "Business"
        authorization.user_id = (
            request.query_params.get("user_id")
            or request.path_params.get("user_id")
            or (await request.json()).get("user_id")
        )
    else:
        authorization.business_or_user = "User"
        authorization.user_id = authorization.user.uid

    # authorization.app_id = request.headers.get("X-App-Id")
    authorization.authorized = await authorized_request(request)

    return authorization
