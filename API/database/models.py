import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Enum,
    func,
    Index,
    text,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database.session import Base


class SentimentType(enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class WordsTraining(Base):
    __tablename__ = "words_training"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    comment = Column(Text, nullable=False)
    label = Column(Enum(SentimentType, name="sentiment_type"), nullable=False)
    score = Column(Float, nullable=True)
    segmented_text = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Word(Base):
    __tablename__ = "words"

    uuid = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    text = Column(Text, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
