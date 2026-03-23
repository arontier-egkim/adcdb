from pydantic import BaseModel


class ActivityBase(BaseModel):
    activity_type: str
    nct_number: str | None = None
    phase: str | None = None
    orr: float | None = None
    model: str | None = None
    tgi: float | None = None
    ic50_value: float | None = None
    ic50_unit: str | None = None
    cell_line: str | None = None
    notes: str | None = None


class ActivityCreate(ActivityBase):
    adc_id: str


class ActivityRead(ActivityBase):
    id: str
    adc_id: str

    model_config = {"from_attributes": True}
