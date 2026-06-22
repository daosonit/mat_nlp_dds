import asyncio
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if present
from core.db import db


async def test_connection():
    print("Testing connection...")
    await db.connect()

    # Try a simple query
    try:
        result = await db.fetch("SELECT 1 AS test_number")
        print("Fetch result:", dict(result[0]))
    except Exception as e:
        print("Error during fetch:", e)

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_connection())
