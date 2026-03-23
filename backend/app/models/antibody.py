from sqlalchemy import ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class Antibody(Base):
    __tablename__ = "antibody"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    synonyms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    isotype: Mapped[str | None] = mapped_column(String(20), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    antigen_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("antigen.id", ondelete="RESTRICT"), nullable=False
    )
    heavy_chain_seq: Mapped[str | None] = mapped_column(Text, nullable=True)
    light_chain_seq: Mapped[str | None] = mapped_column(Text, nullable=True)
    uniprot_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    antigen: Mapped["Antigen"] = relationship(back_populates="antibodies", lazy="raise")
    adcs: Mapped[list["ADC"]] = relationship(back_populates="antibody", lazy="raise")

    __table_args__ = (
        Index("ix_antibody_name_ft", "name", mariadb_prefix="FULLTEXT"),
    )
