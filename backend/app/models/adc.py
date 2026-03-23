from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class ADC(Base):
    __tablename__ = "adc"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    synonyms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="investigative")
    dar: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    conjugation_site: Mapped[str | None] = mapped_column(String(30), nullable=True)
    indications: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    antibody_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("antibody.id", ondelete="RESTRICT"), nullable=False
    )
    linker_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("linker.id", ondelete="RESTRICT"), nullable=False
    )
    payload_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payload.id", ondelete="RESTRICT"), nullable=False
    )
    linker_payload_smiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure_3d_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    antibody: Mapped["Antibody"] = relationship(back_populates="adcs", lazy="raise")
    linker: Mapped["Linker"] = relationship(back_populates="adcs", lazy="raise")
    payload: Mapped["Payload"] = relationship(back_populates="adcs", lazy="raise")
    activities: Mapped[list["ADCActivity"]] = relationship(
        back_populates="adc", lazy="raise", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_adc_name_ft", "name", mariadb_prefix="FULLTEXT"),
        Index("ix_adc_status", "status"),
    )
