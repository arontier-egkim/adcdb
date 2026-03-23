from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ADC, Antibody, Antigen, Linker, Payload
from app.schemas.payload import PayloadRead
from app.schemas.adc import ADCListItem

router = APIRouter(prefix="/api/v1/payloads", tags=["payloads"])


@router.get("", response_model=list[PayloadRead])
async def list_payloads(
    q: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Payload)
    if q:
        stmt = stmt.where(Payload.name.like(f"%{q}%"))
    stmt = stmt.order_by(Payload.name).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{payload_id}", response_model=PayloadRead)
async def get_payload(payload_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Payload).where(Payload.id == payload_id)
    result = await db.execute(stmt)
    pl = result.scalar_one_or_none()
    if not pl:
        raise HTTPException(status_code=404, detail="Payload not found")
    return pl


@router.get("/{payload_id}/adcs", response_model=list[ADCListItem])
async def get_payload_adcs(
    payload_id: str,
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
        .where(ADC.payload_id == payload_id)
        .order_by(ADC.name)
        .limit(per_page).offset((page - 1) * per_page)
    )
    result = await db.execute(stmt)
    return [ADCListItem.model_validate(row._mapping) for row in result]
