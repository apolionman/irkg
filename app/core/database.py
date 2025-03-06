from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/irkg_db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
