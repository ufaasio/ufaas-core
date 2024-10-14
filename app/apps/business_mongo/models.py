import uuid

from aiocache import cached
from fastapi_mongo_base._utils.basic import try_except_wrapper
from pydantic import model_validator
from server.config import Settings
from usso.async_session import AsyncUssoSession

from .schemas import BusinessSchema

# class Business(OwnedEntity):
#     name: str
#     domain: str
#     description: str | None = None
#     config: Config = Config()

#     class Settings(OwnedEntity.Settings):
#         indexes = OwnedEntity.Settings.indexes + [
#             IndexModel([("name", ASCENDING)], unique=True),
#             IndexModel([("domain", ASCENDING)], unique=True),
#         ]

#     @property
#     def root_url(self):
#         if self.domain.startswith("http"):
#             return self.domain
#         return f"https://{self.domain}"

#     @classmethod
#     async def get_by_origin(cls, origin: str):
#         return await cls.find_one(cls.domain == origin)

#     @classmethod
#     async def get_by_name(cls, name: str):
#         return await cls.find_one(cls.name == name)

#     @model_validator(mode="before")
#     def validate_domain(cls, data: dict):
#         if not data.get("domain"):
#             business_name_domain = f"{data.get('name')}.{Settings.root_url}"
#             data["domain"] = business_name_domain

#         return data


#     @classmethod
#     async def create_item(cls, data: dict):
#         business = await super().create_item(data)
#         await business.create_wallet()
#         return business
class Business(BusinessSchema):
    @property
    def root_url(self):
        if self.domain.startswith("http"):
            return self.domain
        return f"https://{self.domain}"

    @classmethod
    @cached(ttl=60 * 10)
    @try_except_wrapper
    async def _get_query(
        cls,
        name: str = None,
        origin: str = None,
        user_id: uuid.UUID = None,
        uid: uuid.UUID = None,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ):
        params = {"offset": offset, "limit": limit}
        if user_id:
            params["user_id"] = str(user_id)
        if name:
            params["name"] = name
        if origin:
            params["origin"] = origin
        if uid:
            params["uid"] = str(uid)

        async with AsyncUssoSession(
            api_key=Settings.USSO_API_KEY,
            sso_refresh_url=f"{Settings.USSO_URL}/auth/refresh",
            user_id=Settings.USSO_USER_ID,
        ) as client:
            async with client.get(
                url=Settings.business_domains_url, params=params
            ) as response:
                response.raise_for_status()
                return await response.json()

    @classmethod
    async def get_query(
        cls,
        name: str = None,
        origin: str = None,
        user_id: uuid.UUID = None,
        uid: uuid.UUID = None,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ):
        return (
            await cls._get_query(
                name=name,
                origin=origin,
                user_id=user_id,
                uid=uid,
                offset=offset,
                limit=limit,
                *args,
                **kwargs,
            )
            or {}
        )

    @classmethod
    async def get_with_query(cls, name: str = None, origin: str = None):
        businesses_dict = await cls.get_query(name=name, origin=origin)
        if not businesses_dict:
            return
        businesses_list = businesses_dict.get("items")
        if not businesses_list:
            return
        business = BusinessSchema(**businesses_list[0])
        return business

    @classmethod
    async def get_by_origin(cls, origin: str):
        schema_index = origin.find("://")
        if schema_index == -1:
            schema_index = 0
        else:
            schema_index += 3
        origin = origin[schema_index:]
        return await cls.get_with_query(origin=origin)

    @classmethod
    async def get_by_name(cls, name: str):
        return await cls.get_with_query(name=name)

    @model_validator(mode="before")
    def validate_domain(cls, data: dict):
        if not data.get("domain"):
            business_name_domain = f"{data.get('name')}.{Settings.root_url}"
            data["domain"] = business_name_domain

        return data

    @classmethod
    async def list_items(
        cls,
        user_id: uuid.UUID = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ) -> tuple[list["Business"], int]:
        business_dict = await cls.get_query(
            user_id=user_id,
            offset=offset,
            limit=limit,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        return [BusinessSchema(**item) for item in business_dict.get("items", [])]

    @classmethod
    async def total_count(
        cls,
        user_id: uuid.UUID = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        business_dict = await cls.get_query(
            user_id=user_id,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        return business_dict.get("total", 0)

    @classmethod
    async def list_total_combined(
        cls,
        user_id: uuid.UUID = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ) -> tuple[list["Business"], int]:
        return await cls.list_items(
            user_id=user_id,
            offset=offset,
            limit=limit,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        ), await cls.total_count(
            user_id=user_id, is_deleted=is_deleted, *args, **kwargs
        )

    @classmethod
    async def get_item(cls, uid: uuid.UUID, user_id: uuid.UUID = None, *args, **kwargs):
        business_dict = await cls.get_query(uid=uid, user_id=user_id, *args, **kwargs)
        businesses_list = business_dict.get("items", [])
        if not businesses_list:
            return
        business = BusinessSchema(**businesses_list[0])
        return business

    async def save(self):
        pass

    async def delete(self):
        pass
