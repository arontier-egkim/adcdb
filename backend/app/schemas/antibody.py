from pydantic import BaseModel

from app.schemas.antigen import AntigenRead


class AntibodyBase(BaseModel):
    name: str
    synonyms: list[str] | None = None
    isotype: str | None = None
    origin: str | None = None
    antigen_id: str
    heavy_chain_seq: str | None = None
    light_chain_seq: str | None = None
    uniprot_id: str | None = None


class AntibodyCreate(AntibodyBase):
    pass


class AntibodyRead(AntibodyBase):
    id: str
    antigen: AntigenRead

    model_config = {"from_attributes": True}
