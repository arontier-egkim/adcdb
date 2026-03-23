from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.database import Base


class ADCActivity(Base):
    __tablename__ = "adc_activity"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid7()))
    adc_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("adc.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    nct_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    orr: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tgi: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ic50_value: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    ic50_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cell_line: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    adc: Mapped["ADC"] = relationship(back_populates="activities", lazy="raise")
