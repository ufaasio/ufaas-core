import logging
import os
from functools import lru_cache

import jwt
from fastapi import Request, WebSocket
from starlette.status import HTTP_401_UNAUTHORIZED
from usso.core import UserData
from usso.exceptions import USSOException

logger = logging.getLogger("usso")


class Usso():
    def __init__(self, jwks_url: str | None = None):
        if jwks_url is None:
            jwks_url = os.getenv("USSO_JWKS_URL")
        self.jwks_url = jwks_url

    @lru_cache
    @classmethod
    def get_jwks_keys(cls, jwks_url):
        return jwt.PyJWKClient(jwks_url)

    def get_authorization_scheme_param(
        self,
        authorization_header_value: str|None,
    ) -> tuple[str, str]:
        if not authorization_header_value:
            return "", ""
        scheme, _, param = authorization_header_value.partition(" ")
        return scheme, param

    def user_data_from_token(self, token: str, **kwargs) -> UserData | None:
        """Return the user associated with a token value."""
        try:
            # header = jwt.get_unverified_header(token)
            # jwks_url = header["jwk_url"]
            jwks_client = self.get_jwks_keys(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
            )
            if decoded["token_type"] != "access":
                raise USSOException(
                    status_code=401,
                    error="invalid_token_type",
                )
            decoded["token"] = token
            return UserData(**decoded)
        except jwt.exceptions.ExpiredSignatureError:
            if kwargs.get("raise_exception", True):
                raise USSOException(status_code=401, error="expired_signature")
        except jwt.exceptions.InvalidSignatureError:
            if kwargs.get("raise_exception", True):
                raise USSOException(status_code=401, error="invalid_signature")
        except jwt.exceptions.InvalidAlgorithmError:
            if kwargs.get("raise_exception", True):
                raise USSOException(
                    status_code=401,
                    error="invalid_algorithm",
                )
        except jwt.exceptions.InvalidIssuedAtError:
            if kwargs.get("raise_exception", True):
                raise USSOException(
                    status_code=401,
                    error="invalid_issued_at",
                )
        except jwt.exceptions.InvalidTokenError:
            if kwargs.get("raise_exception", True):
                raise USSOException(
                    status_code=401,
                    error="invalid_token",
                )
        except jwt.exceptions.InvalidKeyError:
            if kwargs.get("raise_exception", True):
                raise USSOException(
                    status_code=401,
                    error="invalid_key",
                )
        except USSOException as e:
            if kwargs.get("raise_exception", True):
                raise e
        except Exception as e:
            if kwargs.get("raise_exception", True):
                raise USSOException(
                    status_code=401,
                    error="error",
                    message=str(e),
                )
            logger.error(e)

    async def jwt_access_security(self, request: Request) -> UserData | None:
        """Return the user associated with a token value."""
        kwargs = {}
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, credentials = self.get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                token = credentials
                return self.user_data_from_token(token, **kwargs)

        cookie_token = request.cookies.get("usso_access_token")
        if cookie_token:
            return self.user_data_from_token(cookie_token, **kwargs)

        if kwargs.get("raise_exception", True):
            raise USSOException(
                status_code=HTTP_401_UNAUTHORIZED,
                error="unauthorized",
            )
        return None

    async def jwt_access_security_ws(self, websocket: WebSocket) -> UserData | None:
        """Return the user associated with a token value."""
        kwargs = {}
        authorization = websocket.headers.get("Authorization")
        if authorization:
            scheme, credentials = self.get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer":
                token = credentials
                return self.user_data_from_token(token, **kwargs)

        cookie_token = websocket.cookies.get("usso_access_token")
        if cookie_token:
            return self.user_data_from_token(cookie_token, **kwargs)

        if kwargs.get("raise_exception", True):
            raise USSOException(
                status_code=HTTP_401_UNAUTHORIZED,
                error="unauthorized",
            )
        return None
