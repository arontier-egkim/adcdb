from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ADC, Antibody, Antigen, Payload

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Top 5 antigens by ADC count
    ag_stmt = (
        select(Antigen.name, func.count(ADC.id).label("count"))
        .join(Antibody, Antibody.antigen_id == Antigen.id)
        .join(ADC, ADC.antibody_id == Antibody.id)
        .group_by(Antigen.id)
        .order_by(func.count(ADC.id).desc())
        .limit(5)
    )
    ag_result = await db.execute(ag_stmt)
    top_antigens = [{"name": r.name, "count": r.count} for r in ag_result]

    # Top 5 payload targets
    pt_stmt = (
        select(Payload.target, func.count(ADC.id).label("count"))
        .join(ADC, ADC.payload_id == Payload.id)
        .where(Payload.target.is_not(None))
        .group_by(Payload.target)
        .order_by(func.count(ADC.id).desc())
        .limit(5)
    )
    pt_result = await db.execute(pt_stmt)
    top_targets = [{"name": r.target, "count": r.count} for r in pt_result]

    # Pipeline funnel
    pipe_stmt = (
        select(ADC.status, func.count().label("count"))
        .group_by(ADC.status)
    )
    pipe_result = await db.execute(pipe_stmt)
    pipeline = {r.status: r.count for r in pipe_result}

    # Totals
    total_stmt = select(func.count()).select_from(ADC)
    total = (await db.execute(total_stmt)).scalar()

    return {
        "total_adcs": total,
        "top_antigens": top_antigens,
        "top_payload_targets": top_targets,
        "pipeline": pipeline,
    }
