from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ADC, Antibody, Antigen, Linker, Payload
from app.services.chemistry_service import search_by_structure
from app.services.sequence_service import search_by_sequence

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("")
async def unified_search(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    term = f"%{q}%"

    # ADCs
    adc_stmt = (
        select(ADC.id, ADC.name, ADC.status)
        .where(ADC.name.like(term))
        .order_by(ADC.name)
        .limit(10)
    )
    adc_result = await db.execute(adc_stmt)
    adcs = [{"id": r.id, "name": r.name, "status": r.status} for r in adc_result]

    # Antibodies
    ab_stmt = (
        select(Antibody.id, Antibody.name)
        .where(Antibody.name.like(term))
        .order_by(Antibody.name)
        .limit(10)
    )
    ab_result = await db.execute(ab_stmt)
    antibodies = [{"id": r.id, "name": r.name} for r in ab_result]

    # Antigens
    ag_stmt = (
        select(Antigen.id, Antigen.name, Antigen.gene_name)
        .where(or_(Antigen.name.like(term), Antigen.gene_name.like(term)))
        .order_by(Antigen.name)
        .limit(10)
    )
    ag_result = await db.execute(ag_stmt)
    antigens = [{"id": r.id, "name": r.name, "gene_name": r.gene_name} for r in ag_result]

    # Linkers
    lk_stmt = (
        select(Linker.id, Linker.name)
        .where(Linker.name.like(term))
        .order_by(Linker.name)
        .limit(10)
    )
    lk_result = await db.execute(lk_stmt)
    linkers = [{"id": r.id, "name": r.name} for r in lk_result]

    # Payloads
    pl_stmt = (
        select(Payload.id, Payload.name)
        .where(Payload.name.like(term))
        .order_by(Payload.name)
        .limit(10)
    )
    pl_result = await db.execute(pl_stmt)
    payloads = [{"id": r.id, "name": r.name} for r in pl_result]

    return {
        "adcs": adcs,
        "antibodies": antibodies,
        "antigens": antigens,
        "linkers": linkers,
        "payloads": payloads,
    }


@router.get("/structure")
async def structure_similarity_search(
    smiles: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search linkers and payloads by SMILES structural similarity (Tanimoto)."""
    results = await search_by_structure(smiles, db)
    if not results:
        return {"results": [], "message": "No results or invalid SMILES"}
    return {"results": results}


@router.get("/sequence")
async def sequence_similarity_search(
    sequence: str = Query(..., min_length=5),
    db: AsyncSession = Depends(get_db),
):
    """Search antibodies by amino acid sequence similarity."""
    results = await search_by_sequence(sequence, db)
    if not results:
        return {"results": [], "message": "No results or invalid sequence"}
    return {"results": results}
