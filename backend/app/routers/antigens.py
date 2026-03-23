from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ADC, Antibody, Antigen, Linker, Payload
from app.schemas.antigen import AntigenRead
from app.schemas.adc import ADCListItem

router = APIRouter(prefix="/api/v1/antigens", tags=["antigens"])


@router.get("", response_model=list[AntigenRead])
async def list_antigens(
    q: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Antigen)
    if q:
        stmt = stmt.where(Antigen.name.like(f"%{q}%"))
    stmt = stmt.order_by(Antigen.name).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{antigen_id}", response_model=AntigenRead)
async def get_antigen(antigen_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Antigen).where(Antigen.id == antigen_id)
    result = await db.execute(stmt)
    ag = result.scalar_one_or_none()
    if not ag:
        raise HTTPException(status_code=404, detail="Antigen not found")
    return ag


@router.get("/{antigen_id}/adcs", response_model=list[ADCListItem])
async def get_antigen_adcs(
    antigen_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Reverse 2-hop: Antigen <- Antibody <- ADC, queried from ADC side
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
        .where(Antibody.antigen_id == antigen_id)
        .order_by(ADC.name)
        .limit(per_page).offset((page - 1) * per_page)
    )
    result = await db.execute(stmt)
    return [ADCListItem.model_validate(row._mapping) for row in result]
