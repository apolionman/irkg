from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv('.env')

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin_dgx:password123@localhost:5432/irkg_db"
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session