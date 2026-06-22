from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from database.models import WordsTraining
from schemas.words_training import WordsTrainingCreate, WordsTrainingUpdate


class WordsTrainingService:
    @staticmethod
    async def create(db: AsyncSession, obj_in: WordsTrainingCreate) -> WordsTraining:
        db_obj = WordsTraining(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def get(db: AsyncSession, id: UUID) -> WordsTraining | None:
        result = await db.execute(select(WordsTraining).filter(WordsTraining.id == id))
        return result.scalars().first()

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(WordsTraining).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_multi_paginated(
        db: AsyncSession,
        page: int = 1,
        size: int = 50,
        label: str | None = None,
        search: str | None = None,
    ):
        base_query = select(WordsTraining)
        if label:
            base_query = base_query.filter(WordsTraining.label == label)
        if search:
            base_query = base_query.filter(WordsTraining.comment.ilike(f"%{search}%"))

        # 1. Đếm tổng số lượng records
        count_query = select(func.count()).select_from(WordsTraining)
        if label:
            count_query = count_query.filter(WordsTraining.label == label)
        if search:
            count_query = count_query.filter(WordsTraining.comment.ilike(f"%{search}%"))

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 2. Lấy dữ liệu phân trang
        skip = (page - 1) * size
        query = base_query.offset(skip).limit(size)
        result = await db.execute(query)
        records = result.scalars().all()

        return records, total

    @staticmethod
    async def update(
        db: AsyncSession, db_obj: WordsTraining, obj_in: WordsTrainingUpdate
    ) -> WordsTraining:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete(db: AsyncSession, id: UUID) -> bool:
        db_obj = await WordsTrainingService.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False
