import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.settings import settings

# SQLite async URL format: sqlite+aiosqlite:///path/to/db.sqlite
DB_URL = f"sqlite+aiosqlite:///{settings.CONFIG_PATH.replace('.json', '.db')}"

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
