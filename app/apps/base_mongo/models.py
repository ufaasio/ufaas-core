import uuid
from datetime import datetime

from apps.base.schemas import (
    BaseEntitySchema,
    BusinessEntitySchema,
    BusinessOwnedEntitySchema,
    OwnedEntitySchema,
)
from beanie import Document, Insert, Replace, Save, SaveChanges, Update, before_event
from pymongo import ASCENDING, IndexModel

from .tasks import TaskMixin


class BaseEntity(BaseEntitySchema, Document):
    class Settings:
        keep_nulls = False
        validate_on_save = True

        indexes = [
            IndexModel([("uid", ASCENDING)], unique=True),
        ]

    @before_event([Insert, Replace, Save, SaveChanges, Update])
    async def pre_save(self):
        self.updated_at = datetime.now()

    @classmethod
    def get_query(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        base_query = [cls.is_deleted == is_deleted]
        if hasattr(cls, "user_id"):
            base_query.append(cls.user_id == user_id)
        if hasattr(cls, "business_name"):
            base_query.append(cls.business_name == business_name)

        query = cls.find(*base_query)
        return query

    @classmethod
    async def get_item(
        cls,
        uid,
        user_id: uuid.UUID = None,
        business_name: str = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ) -> "BaseEntity":
        query = cls.get_query(
            user_id=user_id,
            business_name=business_name,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        ).find(cls.uid == uid)
        items = await query.to_list()
        if not items:
            return None
        if len(items) > 1:
            raise ValueError("Multiple items found")
        return items[0]

    @classmethod
    async def list_items(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        query = cls.get_query(
            user_id=user_id,
            business_name=business_name,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )

        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        return items

    @classmethod
    async def total_count(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        query = cls.get_query(
            user_id=user_id,
            business_name=business_name,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        return await query.count()

    @classmethod
    async def list_total_combined(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ) -> tuple[list["BaseEntity"], int]:
        query = cls.get_query(
            user_id=user_id,
            business_name=business_name,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        total = await query.count()

        return items, total

    @classmethod
    async def create_item(cls, data: dict):
        item = cls(**data)
        await item.save()
        return item

    @classmethod
    async def update_item(cls, item: "BaseEntity", data: dict):
        for key, value in data.items():
            if cls.update_field_set() and key not in cls.update_field_set():
                continue
            if cls.update_exclude_set() and key in cls.update_exclude_set():
                continue

            setattr(item, key, value)

        await item.save()
        return item

    @classmethod
    async def delete_item(cls, item: "BaseEntity"):
        item.is_deleted = True
        await item.save()
        return item


class OwnedEntity(OwnedEntitySchema, BaseEntity):
    @classmethod
    async def get_item(cls, uid, user_id, *args, **kwargs) -> "OwnedEntity":
        if user_id == None:
            raise ValueError("user_id is required")
        return await super().get_item(uid, user_id=user_id, *args, **kwargs)


class BusinessEntity(BusinessEntitySchema, BaseEntity):
    @classmethod
    async def get_item(cls, uid, business_name, *args, **kwargs) -> "BusinessEntity":
        if business_name == None:
            raise ValueError("business_name is required")
        return await super().get_item(uid, business_name=business_name, *args, **kwargs)

    async def get_business(self):
        from apps.business_mongo.models import Business

        return await Business.get_by_name(self.business_name)


class BusinessOwnedEntity(BusinessOwnedEntitySchema, BaseEntity):
    @classmethod
    async def get_item(
        cls, uid, business_name, user_id, *args, **kwargs
    ) -> "BusinessOwnedEntity":
        if business_name == None:
            raise ValueError("business_name is required")
        if user_id == None:
            raise ValueError("user_id is required")
        return await super().get_item(
            uid, business_name=business_name, user_id=user_id, *args, **kwargs
        )


class BaseEntityTaskMixin(BaseEntity, TaskMixin):
    pass


class ImmutableBase(BaseEntity):

    class Config:
        frozen = True

    @classmethod
    async def update_item(cls, item: "BaseEntity", data: dict):
        raise ValueError("Immutable items cannot be updated")

    @classmethod
    async def delete_item(cls, item: "BaseEntity"):
        raise ValueError("Immutable items cannot be deleted")


class ImmutableOwnedEntity(ImmutableBase, OwnedEntity):
    pass


class ImmutableBusinessEntity(ImmutableBase, BusinessEntity):
    pass


class ImmutableBusinessOwnedEntity(ImmutableBase, BusinessOwnedEntity):
    pass
