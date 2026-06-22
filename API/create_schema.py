import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# Lấy DATABASE_URL từ biến môi trường.
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

print(f"Connecting to {db_url} to create schema...")
engine = create_engine(db_url)
with engine.connect() as conn:
    from sqlalchemy import text

    conn.execute(text("CREATE SCHEMA IF NOT EXISTS cars"))
    conn.commit()
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS cars"))
    conn.commit()
print("Schema 'cars' created successfully.")

# python create_schema.py
# alembic revision --autogenerate -m "create_car_comments_table"
# alembic upgrade head
