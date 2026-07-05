from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False, 
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def test_db_connection():
    """Test if database connection is working"""
    try:
        async with AsyncSessionLocal() as session:
            # Execute a simple query
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except SQLAlchemyError as e:
        print(f"❌ Database connection failed: {e}")
        return False