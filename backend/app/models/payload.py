from sqlalchemy import JSON, Boolean, Index, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class Payload(Base):
    __tablename__ = "payload"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    synonyms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    moa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bystander_effect: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    smiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    inchi: Mapped[str | None] = mapped_column(Text, nullable=True)
    inchikey: Mapped[str | None] = mapped_column(String(27), unique=True, nullable=True)
    formula: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iupac_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    mol_weight: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    morgan_fp: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    adcs: Mapped[list["ADC"]] = relationship(back_populates="payload", lazy="raise")

    __table_args__ = (
        Index("ix_payload_name_ft", "name", mariadb_prefix="FULLTEXT"),
    )
