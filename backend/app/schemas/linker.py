from pydantic import BaseModel


class LinkerBase(BaseModel):
    name: str
    cleavable: bool = True
    cleavage_mechanism: str | None = None
    coupling_chemistry: str | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    formula: str | None = None
    iupac_name: str | None = None
    mol_weight: float | None = None


class LinkerCreate(LinkerBase):
    pass


class LinkerRead(LinkerBase):
    id: str

    model_config = {"from_attributes": True}
