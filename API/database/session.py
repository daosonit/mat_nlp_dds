import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from dotenv import load_dotenv

load_dotenv()

# Lấy DATABASE_URL từ biến môi trường.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nlp_db"
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=True)

from sqlalchemy import MetaData

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

metadata = MetaData(schema="cars")
Base = declarative_base(metadata=metadata)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
