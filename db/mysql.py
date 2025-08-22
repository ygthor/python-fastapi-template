# 3. db/mysql.py
from sqlalchemy import create_engine, MetaData, insert, Table
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("MYSQL_URL"))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def insert_row(table_name: str, values: dict):
    """
    Insert a single row into a given table using SQLAlchemy Core.

    Args:
        table_name (str): Name of the table to insert into.
        values (dict): Dictionary of column-value pairs.

    Example:
        insert_row("api_call_logs", {"endpoint": "/api", "status_code": 200})
    """
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    stmt = insert(table).values(values)

    with engine.connect() as conn:
        result = conn.execute(stmt)
        conn.commit()
        return result.lastrowid