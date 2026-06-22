"""init words_training

Revision ID: 33fcec63cde5
Revises:
Create Date: 2026-06-22 10:12:30.588398

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "33fcec63cde5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS cars;")

    # Create enum type
    sentiment_type = postgresql.ENUM(
        "positive",
        "negative",
        "neutral",
        name="sentiment_type",
        schema="cars",
        create_type=False,
    )
    sentiment_type.create(op.get_bind(), checkfirst=True)

    # Create table
    op.create_table(
        "words_training",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column(
            "label",
            postgresql.ENUM(
                "positive",
                "negative",
                "neutral",
                name="sentiment_type",
                schema="cars",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("segmented_text", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="cars",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("words_training", schema="cars")
    op.execute("DROP TYPE IF EXISTS cars.sentiment_type;")
