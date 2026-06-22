from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from database.session import get_db
from schemas.words_training import (
    WordsTrainingCreate,
    WordsTrainingUpdate,
    WordsTrainingResponse,
)
from schemas.pagination import PaginatedResponse, PaginationMeta
from services.words_training_service import WordsTrainingService
from api.dependencies import verify_jwt_token

router = APIRouter(
    prefix="/words-training",
    tags=["Words Training Data"],
    dependencies=[Depends(verify_jwt_token)],
)


@router.get("", response_model=PaginatedResponse[WordsTrainingResponse])
async def read_words_training_list(
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    size: int = Query(50, ge=1, le=100, description="Số lượng bản ghi trên một trang"),
    label: str = Query(None, description="Lọc theo nhãn"),
    search: str = Query(None, description="Tìm kiếm nội dung comment"),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách các dòng dữ liệu (phân trang chuẩn)"""
    records, total = await WordsTrainingService.get_multi_paginated(
        db,
        page=page,
        size=size,
        label=label,
        search=search,
    )
    total_pages = (total + size - 1) // size

    return PaginatedResponse(
        data=records,
        meta=PaginationMeta(
            total_records=total,
            current_page=page,
            page_size=size,
            total_pages=total_pages,
        ),
    )
