"""consent subjects mapping

Revision ID: c4e8a91f2b07
Revises: 931386b9e96b
Create Date: 2026-08-17 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4e8a91f2b07"
down_revision: Union[str, Sequence[str], None] = "931386b9e96b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "consent_subjects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("external_id", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "channel",
            "external_id",
            name="uq_consent_subjects_channel_external",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("consent_subjects")
