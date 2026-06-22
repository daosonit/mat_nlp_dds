from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total_records: int
    current_page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta
