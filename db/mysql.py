# 3. db/mysql.py
import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# 1. Use create_async_engine for async support
engine = create_async_engine(
    os.getenv("MYSQL_URL"),
    pool_pre_ping=True,
    echo=False  # Set to True to see generated SQL statements
)

# 2. Use AsyncSession for the session class and expire_on_commit=False
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 3. 'get_db' is now an async generator
async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# 4. 'insert_row' is now an async function and accepts the session
async def insert_row(db: AsyncSession, table_name: str, values: dict):
    """
    Insert a single row into a given table using an async session.

    Args:
        db (AsyncSession): The database session from the dependency.
        table_name (str): Name of the table to insert into.
        values (dict): Dictionary of column-value pairs.
    """
    # Note: Reflecting the table on every call is inefficient.
    # It's better to define your table models elsewhere and import them.
    # But to keep your logic, we do it here.
    async with engine.connect() as conn:
        metadata = MetaData()
        table = await conn.run_sync(
            lambda sync_conn: Table(table_name, metadata, autoload_with=sync_conn)
        )

    stmt = insert(table).values(values)
    result = await db.execute(stmt)
    await db.commit()
    return result.lastrowid