from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env')

# Load database URL from .env or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin_dgx:password123@pg_dgx:5432/irkg_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL query logging (optional, useful for debugging)
    pool_pre_ping=True,
    pool_size=10,       # Adjust based on concurrency needs
    max_overflow=20     # Allow extra temporary connections if needed
)

# Define session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get an async session
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session  # Yield session correctly
