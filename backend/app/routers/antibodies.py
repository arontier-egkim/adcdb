from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import ADC, Antibody, Antigen, Linker, Payload
from app.schemas.antibody import AntibodyRead
from app.schemas.adc import ADCListItem

router = APIRouter(prefix="/api/v1/antibodies", tags=["antibodies"])


@router.get("", response_model=list[AntibodyRead])
async def list_antibodies(
    q: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Antibody).options(joinedload(Antibody.antigen))
    if q:
        stmt = stmt.where(Antibody.name.like(f"%{q}%"))
    stmt = stmt.order_by(Antibody.name).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(stmt)
    return result.unique().scalars().all()


@router.get("/{antibody_id}", response_model=AntibodyRead)
async def get_antibody(antibody_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Antibody)
        .options(joinedload(Antibody.antigen))
        .where(Antibody.id == antibody_id)
    )
    result = await db.execute(stmt)
    ab = result.unique().scalar_one_or_none()
    if not ab:
        raise HTTPException(status_code=404, detail="Antibody not found")
    return ab


@router.get("/{antibody_id}/adcs", response_model=list[ADCListItem])
async def get_antibody_adcs(
    antibody_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            ADC.id, ADC.name, ADC.brand_name, ADC.status, ADC.dar, ADC.organization,
            Antibody.name.label("antibody_name"),
            Antigen.name.label("antigen_name"),
            Linker.name.label("linker_name"),
            Payload.name.label("payload_name"),
        )
        .join(Antibody, ADC.antibody_id == Antibody.id)
        .join(Antigen, Antibody.antigen_id == Antigen.id)
        .join(Linker, ADC.linker_id == Linker.id)
        .join(Payload, ADC.payload_id == Payload.id)
        .where(ADC.antibody_id == antibody_id)
        .order_by(ADC.name)
        .limit(per_page).offset((page - 1) * per_page)
    )
    result = await db.execute(stmt)
    return [ADCListItem.model_validate(row._mapping) for row in result]
