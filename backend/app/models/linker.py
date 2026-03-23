from sqlalchemy import Index, LargeBinary, Numeric, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class Linker(Base):
    __tablename__ = "linker"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    cleavable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cleavage_mechanism: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coupling_chemistry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    smiles: Mapped[str | None] = mapped_column(Text, nullable=True)
    inchi: Mapped[str | None] = mapped_column(Text, nullable=True)
    inchikey: Mapped[str | None] = mapped_column(String(27), unique=True, nullable=True)
    formula: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iupac_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    mol_weight: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    morgan_fp: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    adcs: Mapped[list["ADC"]] = relationship(back_populates="linker", lazy="raise")

    __table_args__ = (
        Index("ix_linker_name_ft", "name", mariadb_prefix="FULLTEXT"),
    )
