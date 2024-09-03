import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, as_declarative, declared_attr, mapped_column
from sqlalchemy.sql import func

# Base = declarative_base()


@as_declarative()
class BaseEntity:
    id: Any
    __name__: str
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    uid: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), onupdate=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # name: Mapped[str | None] = mapped_column(nullable=True)

    @classmethod
    def create_exclude_set(cls) -> list[str]:
        return ["uid", "created_at", "updated_at", "is_deleted"]

    @classmethod
    def create_field_set(cls) -> list:
        return []

    @classmethod
    def update_exclude_set(cls) -> list:
        return ["uid", "created_at", "updated_at"]

    @classmethod
    def update_field_set(cls) -> list:
        return []

    @classmethod
    async def get_item(
        cls,
        uid: uuid.UUID,
        user_id: uuid.UUID = None,
        business_name: str = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        from server.db import async_session

        base_query = [cls.is_deleted == is_deleted, cls.uid == uid]

        if hasattr(cls, "user_id"):
            base_query.append(cls.user_id == user_id)
        if hasattr(cls, "business_name"):
            base_query.append(cls.business_name == business_name)

        async with async_session() as session:
            query = select(cls).filter(*base_query)
            result = await session.execute(query)
            item = result.scalar_one_or_none()
        return item

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
        from server.db import async_session

        base_query = [cls.is_deleted == is_deleted]

        if hasattr(cls, "user_id"):
            base_query.append(cls.user_id == user_id)
        if hasattr(cls, "business_name"):
            base_query.append(cls.business_name == business_name)

        items_query = (
            select(cls)
            .filter(*base_query)
            .order_by(cls.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        async with async_session() as session:
            items_result = await session.execute(items_query)
            items = items_result.scalars().all()
        return items

    @classmethod
    async def total_count(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        is_deleted: bool = False,
    ):
        from server.db import async_session

        # Create the base query
        base_query = [cls.is_deleted == is_deleted]

        # Apply user_id filtering if the model has a user_id attribute
        if hasattr(cls, "user_id"):
            base_query.append(cls.user_id == user_id)
        if hasattr(cls, "business_name"):
            base_query.append(cls.business_name == business_name)

        # Query for getting the total count of items
        total_count_query = select(func.count()).filter(*base_query)  # .subquery()

        async with async_session() as session:
            total_result = await session.execute(total_count_query)
        total = total_result.scalar()

        return total

    @classmethod
    async def list_total_combined(
        cls,
        session: AsyncSession,
        user_id: uuid.UUID = None,
        business_name: str = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
    ) -> tuple[list["BaseEntity"], int]:
        items = await cls.list_items(
            session,
            user_id=user_id,
            business_name=business_name,
            offset=offset,
            limit=limit,
            is_deleted=is_deleted,
        )
        total = await cls.total_count(
            session, user_id=user_id, business_name=business_name, is_deleted=is_deleted
        )
        return items, total

        # TODO Not completed
        base_query = [cls.is_deleted == is_deleted]

        if hasattr(cls, "user_id"):
            base_query.append(cls.user_id == user_id)
        if hasattr(cls, "business_name"):
            base_query.append(cls.business_name == business_name)

        total_count_query = select(func.count()).filter(*base_query)  # .subquery()

        # Create the base query for fetching the items
        items_query = (
            select(cls)
            .filter(*base_query)
            .order_by(cls.created_at.desc())
            .offset(offset)
            .limit(limit)
            # .subquery()
        )

        # Combine both queries into a single select statement
        combined_query = select(
            total_count_query.subquery().c[0].label("total"), items_query.subquery()
        )
        # Execute the combined query
        # result = await session.execute(combined_query)
        # res2 = result.fetchall()
        # res = result.scalars().all()

    @classmethod
    async def create_item(cls, data: dict):
        from server.db import async_session

        item = cls(**data)
        async with async_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item

    @classmethod
    async def update_item(cls, item: "BaseEntity", data: dict):
        from server.db import async_session

        for key, value in data.items():
            if cls.update_field_set() and key not in cls.update_field_set():
                continue
            if cls.update_exclude_set() and key in cls.update_exclude_set():
                continue

            setattr(item, key, value)

        async with async_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item

    @classmethod
    async def delete_item(cls, item: "BaseEntity"):
        from server.db import async_session

        item.is_deleted = True
        async with async_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item


Base = BaseEntity


class OwnedEntity(BaseEntity):
    __abstract__ = True

    user_id: Mapped[uuid.UUID] = mapped_column(index=True)

    @classmethod
    def create_exclude_set(cls) -> list:
        return super().create_exclude_set() + ["user_id"]

    @classmethod
    def update_exclude_set(cls) -> list:
        return super().update_exclude_set() + ["user_id"]


class BusinessEntity(BaseEntity):
    __abstract__ = True

    business_name: Mapped[str] = mapped_column(index=True)

    @classmethod
    def create_exclude_set(cls) -> list[str]:
        return super().create_exclude_set() + ["business_name"]

    @classmethod
    def update_exclude_set(cls) -> list[str]:
        return super().update_exclude_set() + ["business_name"]


class BusinessOwnedEntity(OwnedEntity, BusinessEntity):
    __abstract__ = True

    @classmethod
    def create_exclude_set(cls) -> list[str]:
        return list(set(super().create_exclude_set() + ["business_name", "user_id"]))

    @classmethod
    def update_exclude_set(cls) -> list[str]:
        return list(set(super().update_exclude_set() + ["business_name", "user_id"]))


class ImmutableBase(BaseEntity):
    __abstract__ = True

    @staticmethod
    def prevent_update(mapper, connection, target):
        if connection.in_transaction() and target.id is not None:
            raise ValueError("Updates are not allowed for this object")

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, "before_update", cls.prevent_update)


class ImmutableOwnedEntity(ImmutableBase, OwnedEntity):
    __abstract__ = True


class ImmutableBusinessEntity(ImmutableBase, BusinessEntity):
    __abstract__ = True


class ImmutableBusinessOwnedEntity(ImmutableBase, BusinessOwnedEntity):
    __abstract__ = True
