from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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


class ConsentSubject(Base):
    """Канал + внешний id → внутренний id для журнала. Сайт сюда не пишем."""

    __tablename__ = "consent_subjects"
    __table_args__ = (
        UniqueConstraint(
            "channel",
            "external_id",
            name="uq_consent_subjects_channel_external",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=False)
