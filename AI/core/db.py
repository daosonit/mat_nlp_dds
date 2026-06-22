import os
import logging
import asyncpg

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.warning("DATABASE_URL không tồn tại trong biến môi trường!")
                return
            try:
                # Tạo connection pool với asyncpg
                self.pool = await asyncpg.create_pool(
                    dsn=database_url,
                    min_size=1,
                    max_size=10,
                )
                logger.info("Đã kết nối thành công tới PostgreSQL (asyncpg pool).")
            except Exception as e:
                logger.error(f"Lỗi khi kết nối tới CSDL: {e}")
                raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Đã đóng kết nối PostgreSQL.")

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
