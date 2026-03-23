"""Batch generate 3D structures for all ADCs that have linker_payload_smiles.

When run with --regenerate, clears existing structure_3d_path values first
so all structures are rebuilt (useful after template upgrades).
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import ADC
from app.structure.assembler import generate_and_save


async def main():
    parser = argparse.ArgumentParser(description="Generate 3D structures for ADCs")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Clear existing structure_3d_path values and regenerate all structures",
    )
    args = parser.parse_args()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    structures_dir = str(Path(__file__).resolve().parent.parent / "backend" / "structures")

    async with session_factory() as session:
        if args.regenerate:
            # Clear existing structure paths so all ADCs are regenerated
            result = await session.execute(
                update(ADC)
                .where(ADC.linker_payload_smiles.is_not(None))
                .values(structure_3d_path=None)
            )
            await session.commit()
            print(f"Cleared structure_3d_path for {result.rowcount} ADCs")

        result = await session.execute(
            select(ADC.id, ADC.name, ADC.linker_payload_smiles, ADC.conjugation_site, ADC.dar)
            .where(ADC.linker_payload_smiles.is_not(None))
            .where(ADC.structure_3d_path.is_(None))
        )
        adcs = result.all()
        print(f"Found {len(adcs)} ADCs needing structure generation")

        success = 0
        failed = 0
        for adc in adcs:
            try:
                path = generate_and_save(
                    adc_id=adc.id,
                    linker_payload_smiles=adc.linker_payload_smiles,
                    conjugation_site=adc.conjugation_site,
                    dar=float(adc.dar) if adc.dar else 4.0,
                    output_dir=structures_dir,
                )
                if path:
                    await session.execute(
                        update(ADC).where(ADC.id == adc.id).values(structure_3d_path=path)
                    )
                    success += 1
                    print(f"  OK: {adc.name}")
                else:
                    failed += 1
                    print(f"  FAIL: {adc.name} -- conformer generation returned None")
            except Exception as e:
                failed += 1
                print(f"  FAIL: {adc.name} -- {e}")

        await session.commit()
        print(f"\nDone: {success} succeeded, {failed} failed")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
