"""Chemistry services: fingerprint computation and similarity search."""

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Linker, Payload


def smiles_to_morgan_fp(smiles: str):
    """Convert SMILES to Morgan fingerprint bitvect (radius=2, 2048 bits)."""
    clean = smiles.replace("[*:1]", "[H]").replace("[*:2]", "[H]")
    mol = Chem.MolFromSmiles(clean)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)


def fp_from_stored_bytes(data: bytes):
    """Reconstruct bitvect from stored bit string bytes."""
    if not data:
        return None
    bit_string = data.decode()
    fp = DataStructs.ExplicitBitVect(len(bit_string))
    for i, c in enumerate(bit_string):
        if c == "1":
            fp.SetBit(i)
    return fp


async def search_by_structure(
    smiles: str, db: AsyncSession, top_n: int = 20
) -> list[dict]:
    """Search linkers and payloads by structural similarity to query SMILES."""
    query_fp = smiles_to_morgan_fp(smiles)
    if query_fp is None:
        return []

    results = []

    # Search linkers
    lk_stmt = select(Linker.id, Linker.name, Linker.smiles, Linker.morgan_fp).where(
        Linker.morgan_fp.is_not(None)
    )
    lk_result = await db.execute(lk_stmt)
    for row in lk_result:
        stored_fp = fp_from_stored_bytes(row.morgan_fp)
        if stored_fp is None:
            continue
        sim = DataStructs.TanimotoSimilarity(query_fp, stored_fp)
        results.append({
            "id": row.id,
            "name": row.name,
            "type": "linker",
            "smiles": row.smiles,
            "similarity": round(sim, 4),
        })

    # Search payloads
    pl_stmt = select(Payload.id, Payload.name, Payload.smiles, Payload.morgan_fp).where(
        Payload.morgan_fp.is_not(None)
    )
    pl_result = await db.execute(pl_stmt)
    for row in pl_result:
        stored_fp = fp_from_stored_bytes(row.morgan_fp)
        if stored_fp is None:
            continue
        sim = DataStructs.TanimotoSimilarity(query_fp, stored_fp)
        results.append({
            "id": row.id,
            "name": row.name,
            "type": "payload",
            "smiles": row.smiles,
            "similarity": round(sim, 4),
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_n]
