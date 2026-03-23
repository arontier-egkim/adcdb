from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class Antigen(Base):
    __tablename__ = "antigen"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    synonyms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    gene_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uniprot_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    antibodies: Mapped[list["Antibody"]] = relationship(back_populates="antigen", lazy="raise")

    __table_args__ = (
        Index("ix_antigen_name_ft", "name", mariadb_prefix="FULLTEXT"),
    )
