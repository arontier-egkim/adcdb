from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import ADC, ADCActivity, Antibody, Antigen, Linker, Payload
from app.schemas.adc import ADCCreate, ADCListItem, ADCRead

router = APIRouter(prefix="/api/v1/adcs", tags=["adcs"])


@router.get("", response_model=list[ADCListItem])
async def list_adcs(
    status: str | None = None,
    antigen: str | None = None,
    payload_target: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            ADC.id,
            ADC.name,
            ADC.brand_name,
            ADC.status,
            ADC.dar,
            ADC.organization,
            Antibody.name.label("antibody_name"),
            Antigen.name.label("antigen_name"),
            Linker.name.label("linker_name"),
            Payload.name.label("payload_name"),
        )
        .join(Antibody, ADC.antibody_id == Antibody.id)
        .join(Antigen, Antibody.antigen_id == Antigen.id)
        .join(Linker, ADC.linker_id == Linker.id)
        .join(Payload, ADC.payload_id == Payload.id)
    )
    if status:
        stmt = stmt.where(ADC.status == status)
    if antigen:
        stmt = stmt.where(Antigen.name == antigen)
    if payload_target:
        stmt = stmt.where(Payload.target == payload_target)
    if q:
        stmt = stmt.where(ADC.name.like(f"%{q}%"))
    stmt = stmt.order_by(ADC.name).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(stmt)
    return [ADCListItem.model_validate(row._mapping) for row in result]


@router.get("/{adc_id}", response_model=ADCRead)
async def get_adc(adc_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ADC)
        .options(
            joinedload(ADC.antibody).joinedload(Antibody.antigen),
            joinedload(ADC.linker),
            joinedload(ADC.payload),
            joinedload(ADC.activities),
        )
        .where(ADC.id == adc_id)
    )
    result = await db.execute(stmt)
    adc = result.unique().scalar_one_or_none()
    if not adc:
        raise HTTPException(status_code=404, detail="ADC not found")
    return adc


@router.get("/{adc_id}/structure")
async def get_adc_structure(adc_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ADC.structure_3d_path).where(ADC.id == adc_id)
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="ADC not found")
    if not row.structure_3d_path:
        raise HTTPException(status_code=404, detail="Structure not available")
    path = Path(row.structure_3d_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Structure file missing")
    return FileResponse(path, media_type="chemical/x-pdb", filename=f"{adc_id}.pdb")


@router.post("", response_model=ADCRead, status_code=201)
async def create_adc(data: ADCCreate, db: AsyncSession = Depends(get_db)):
    adc = ADC(**data.model_dump())
    db.add(adc)
    await db.commit()
    # Re-fetch with joins
    return await get_adc(adc.id, db)
