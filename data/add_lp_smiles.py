"""Add linker_payload_smiles to ADCs that have known linker+payload combos."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings
from app.models import ADC

# Pre-connected linker-payload SMILES with [*:1] = antibody attachment
# These are simplified representations for 3D visualization
LP_SMILES = {
    # MC-VC-PABC + MMAE (vedotin)
    "MC-VC-PABC|MMAE": "[*:1]CCCCCC(=O)NC(CC(C)C)C(=O)NC(CCCNC(N)=O)C(=O)NC1=CC=C(C=C1)COC(=O)NC(CC2=CC=CC=C2)C(=O)O",
    # MC-GGFG-AM + DXd (deruxtecan)
    "MC-GGFG-AM|DXd": "[*:1]CCCCCC(=O)NCC(=O)NCC(=O)NC(CC1=CC=CC=C1)C(=O)NCC(=O)OC2=CC3=CC4=C(C=C3C(=O)N2)CN5C4=CC6=C5C(=O)OCC6(CC)O",
    # SMCC + DM1 (emtansine)
    "SMCC|DM1": "[*:1]CCCCCCNC(=O)CC1CC(=O)N(C1=O)SC",
    # CL2A + SN-38 (govitecan)
    "CL2A|SN-38": "[*:1]CCNC(=O)COCCOCCOCCNC(=O)OC1=CC2=C(C=C1)NC(=O)C3=CC4=C(C=C3C2=O)CN5C4=CC6=C(C5=O)COC(=O)C6(CC)O",
    # MC-VC-PABC + MMAF (mafodotin)
    "MC-VC-PABC|MMAF": "[*:1]CCCCCC(=O)NC(CC(C)C)C(=O)NC(CCCNC(N)=O)C(=O)NC1=CC=C(C=C1)COC(=O)NC(CC2=CC=CC=C2)C(=O)O",
    # MC linker + MMAF
    "MC linker|MMAF": "[*:1]CCCCCCCC(=O)NC(CC(C)C)C(=O)O",
}

# Map ADC patterns to LP_SMILES keys
ADC_LP_MAP = {
    "vedotin": "MC-VC-PABC|MMAE",
    "deruxtecan": "MC-GGFG-AM|DXd",
    "emtansine": "SMCC|DM1",
    "govitecan": "CL2A|SN-38",
    "mafodotin": "MC linker|MMAF",
}


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sf() as session:
        result = await session.execute(
            select(ADC.id, ADC.name).where(ADC.linker_payload_smiles.is_(None))
        )
        adcs = result.all()
        updated = 0

        for adc in adcs:
            name_lower = adc.name.lower()
            for pattern, key in ADC_LP_MAP.items():
                if pattern in name_lower:
                    smiles = LP_SMILES[key]
                    await session.execute(
                        update(ADC).where(ADC.id == adc.id).values(linker_payload_smiles=smiles)
                    )
                    updated += 1
                    break

        await session.commit()
        print(f"Updated {updated} ADCs with linker_payload_smiles")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
