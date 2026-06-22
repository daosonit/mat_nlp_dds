from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from database.models import SentimentType


class WordsTrainingBase(BaseModel):
    comment: str
    label: SentimentType
    score: Optional[float] = None
    segmented_text: Optional[str] = None
    model_used: Optional[str] = None


class WordsTrainingCreate(WordsTrainingBase):
    pass


class WordsTrainingUpdate(BaseModel):
    comment: Optional[str] = None
    label: Optional[SentimentType] = None
    score: Optional[float] = None
    segmented_text: Optional[str] = None
    model_used: Optional[str] = None


class WordsTrainingResponse(WordsTrainingBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
