import asyncio
import dataclasses as dc
import typing
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, scoped_session, Session

# Placeholder for custom error
class DbConnectionError(Exception):
    pass

@dc.dataclass
class BaseSessionManager:
    session_factory: typing.Union[scoped_session, async_scoped_session]

    def __post_init__(self):
        if not isinstance(self.session_factory, (scoped_session, async_scoped_session)):
            raise TypeError("session_factory must be scoped_session or async_scoped_session")

    # Synchronous session scope
    @contextmanager
    def session_scope_sync(self) -> typing.Iterator[Session]:
        session: Session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise DbConnectionError(f"Sync session error: {e}")
        finally:
            session.close()

    # Asynchronous session scope
    @asynccontextmanager
    async def session_scope_async(self) -> typing.AsyncIterator[AsyncSession]:
        session: AsyncSession = self.session_factory()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise DbConnectionError(f"Async session error: {e}")
        finally:
            await session.close()


@dc.dataclass
class SyncSessionManager(BaseSessionManager):
    engine: Engine

    @classmethod
    def create(cls, db_url: str, **kwargs: typing.Any) -> "SyncSessionManager":
        engine = create_engine(db_url, **kwargs)  # Fixed: Correct method to create a sync engine
        session_class = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
                expire_on_commit=False,
                future=True
            )
        )
        return cls(session_class, engine)


@dc.dataclass
class AsyncSessionManager(BaseSessionManager):
    engine: Engine

    @classmethod
    async def create(cls, db_url: str, **kwargs: typing.Any) -> "AsyncSessionManager":
        engine = create_async_engine(db_url, **kwargs)
        session_class = async_scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                future=True
            ),
            asyncio.current_task
        )
        return cls(session_class, engine)


# Unified Driver to handle both Sync and Async session managers
@dc.dataclass
class Driver:
    sync_session_manager: typing.Optional[SyncSessionManager] = None
    async_session_manager: typing.Optional[AsyncSessionManager] = None

    @classmethod
    async def create(cls, db_url_sync: str, db_url_async: str, **kwargs: typing.Any) -> "Driver":
        sync_session_manager = SyncSessionManager.create(db_url_sync, **kwargs)
        async_session_manager = await AsyncSessionManager.create(db_url_async, **kwargs)
        return cls(sync_session_manager, async_session_manager)

    # Property to get the sync engine
    @property
    def sync_engine(self) -> Engine:
        if not self.sync_session_manager:
            raise DbConnectionError("Synchronous session manager not initialized.")
        return self.sync_session_manager.engine

    # Property to get the async engine
    @property
    def async_engine(self) -> Engine:
        if not self.async_session_manager:
            raise DbConnectionError("Asynchronous session manager not initialized.")
        return self.async_session_manager.engine

    # Synchronous session scope
    @contextmanager
    def session_scope_sync(self) -> typing.Iterator[Session]:
        if not self.sync_session_manager:
            raise DbConnectionError("Synchronous session manager not initialized.")
        with self.sync_session_manager.session_scope_sync() as session:
            yield session

    # Asynchronous session scope
    @asynccontextmanager
    async def session_scope_async(self) -> typing.AsyncIterator[AsyncSession]:
        if not self.async_session_manager:
            raise DbConnectionError("Asynchronous session manager not initialized.")
        async with self.async_session_manager.session_scope_async() as session:
            yield session
