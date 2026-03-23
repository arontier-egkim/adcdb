from pydantic import BaseModel


class PayloadBase(BaseModel):
    name: str
    synonyms: list[str] | None = None
    target: str | None = None
    moa: str | None = None
    bystander_effect: bool | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    formula: str | None = None
    iupac_name: str | None = None
    mol_weight: float | None = None


class PayloadCreate(PayloadBase):
    pass


class PayloadRead(PayloadBase):
    id: str

    model_config = {"from_attributes": True}
