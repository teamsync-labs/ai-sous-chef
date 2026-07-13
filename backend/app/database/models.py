from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class TestTable(Base):
    __tablename__ = "test_table"

    request_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        unique=False,
        nullable=False
    )
    input_type: Mapped[int] = mapped_column(
        Integer,
        unique=False,
        nullable=False
    )
    status: Mapped[int] = mapped_column(
        Integer,
        unique=False,
        nullable=False
    )
