from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import PGSettings
from domain.models import Base, Visitor, Status
from helpers.open_ai_helper import Model


async def add_visitor(visitor: Visitor) -> None:
    factory = get_session_factory()
    async with factory() as session:
        session.add(visitor)
        await session.commit()


async def get_visitor(chat_id: int) -> Optional[Visitor]:
    factory = get_session_factory()
    async with factory() as session:
        visitor = await session.get(Visitor, chat_id)
        return visitor


async def get_all_visitors() -> List[Visitor]:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(Visitor))
        return result.scalars().unique().all()


async def get_all_admins() -> List[Visitor]:
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(Visitor).filter(Visitor.is_admin))
        return result.scalars().unique().all()


async def change_visitor_status(chat_id: int, status: Status):
    factory = get_session_factory()
    async with factory() as session:
        visitor = await session.get(Visitor, chat_id)
        visitor.status = status.value
        await session.commit()


async def change_visitor_model(chat_id: int, model: Model):
    factory = get_session_factory()
    async with factory() as session:
        visitor = await session.get(Visitor, chat_id)
        visitor.model = model.value
        await session.commit()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine_async(),
        expire_on_commit=False,
    )


def get_engine_async():
    return create_async_engine(
        PGSettings().db_connection_async(),
        isolation_level="REPEATABLE READ",
        pool_pre_ping=True
        # echo=True
    )


async def start_db_async():
    engine = get_engine_async()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
