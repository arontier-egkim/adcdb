from datetime import datetime

from pydantic import BaseModel

from app.schemas.activity import ActivityRead
from app.schemas.antibody import AntibodyRead
from app.schemas.linker import LinkerRead
from app.schemas.payload import PayloadRead


class ADCBase(BaseModel):
    name: str
    brand_name: str | None = None
    synonyms: list[str] | None = None
    organization: str | None = None
    status: str = "investigative"
    dar: float | None = None
    conjugation_site: str | None = None
    indications: list[str] | None = None
    antibody_id: str
    linker_id: str
    payload_id: str
    linker_payload_smiles: str | None = None


class ADCCreate(ADCBase):
    pass


class ADCRead(ADCBase):
    id: str
    structure_3d_path: str | None = None
    created_at: datetime
    updated_at: datetime
    antibody: AntibodyRead
    linker: LinkerRead
    payload: PayloadRead
    activities: list[ActivityRead] = []

    model_config = {"from_attributes": True}


class ADCListItem(BaseModel):
    id: str
    name: str
    brand_name: str | None = None
    status: str
    dar: float | None = None
    organization: str | None = None
    antibody_name: str
    antigen_name: str
    linker_name: str
    payload_name: str

    model_config = {"from_attributes": True}
