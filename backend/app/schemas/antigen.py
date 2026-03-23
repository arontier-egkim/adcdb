from pydantic import BaseModel


class AntigenBase(BaseModel):
    name: str
    synonyms: list[str] | None = None
    gene_name: str | None = None
    uniprot_id: str | None = None
    description: str | None = None


class AntigenCreate(AntigenBase):
    pass


class AntigenRead(AntigenBase):
    id: str

    model_config = {"from_attributes": True}
