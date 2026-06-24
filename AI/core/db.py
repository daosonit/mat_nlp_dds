import os
import asyncpg



class DatabasePool:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                return

            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace(
                    "postgresql+asyncpg://", "postgresql://", 1
                )

            try:
                # Tạo connection pool với asyncpg
                self.pool = await asyncpg.create_pool(
                    dsn=database_url,
                    min_size=1,
                    max_size=10,
                )
            except Exception as e:
                raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args):
        """Thực thi câu SELECT và trả về danh sách kết quả"""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query: str, *args):
        """Thực thi câu INSERT/UPDATE/DELETE"""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args: list):
        """Thực thi nhiều dữ liệu cùng lúc cho INSERT/UPDATE"""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.executemany(query, args)


db = DatabasePool()
