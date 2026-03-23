"""Seed the ADCDB database from curated JSON data."""

import asyncio
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import settings
from app.database import Base
from app.models import ADC, ADCActivity, Antibody, Antigen, Linker, Payload

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from uuid_utils import uuid7


def validate_smiles(smiles: str) -> bool:
    """Check if SMILES is parseable by RDKit. Allows [*:n] attachment points."""
    if not smiles or smiles == "C":  # placeholder
        return True
    # Replace attachment points temporarily for validation
    test = smiles.replace("[*:1]", "[H]").replace("[*:2]", "[H]")
    mol = Chem.MolFromSmiles(test)
    return mol is not None


def compute_morgan_fp(smiles: str) -> bytes | None:
    """Compute Morgan fingerprint (radius=2, 2048 bits) as bytes."""
    if not smiles or smiles == "C":
        return None
    test = smiles.replace("[*:1]", "[H]").replace("[*:2]", "[H]")
    mol = Chem.MolFromSmiles(test)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
    return fp.ToBitString().encode()


def compute_mol_weight(smiles: str) -> float | None:
    """Compute molecular weight from SMILES."""
    if not smiles or smiles == "C":
        return None
    test = smiles.replace("[*:1]", "[H]").replace("[*:2]", "[H]")
    mol = Chem.MolFromSmiles(test)
    if mol is None:
        return None
    return round(Descriptors.ExactMolWt(mol), 4)


async def seed():
    data_path = Path(__file__).parent / "sources" / "seed_data.json"
    with open(data_path) as f:
        data = json.load(f)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # --- Antigens ---
        antigen_map: dict[str, str] = {}
        for ag in data["antigens"]:
            ag_id = str(uuid7())
            antigen_map[ag["name"]] = ag_id
            session.add(Antigen(
                id=ag_id,
                name=ag["name"],
                synonyms=ag.get("synonyms"),
                gene_name=ag.get("gene_name"),
                uniprot_id=ag.get("uniprot_id"),
                description=ag.get("description"),
            ))
        await session.flush()
        print(f"Inserted {len(antigen_map)} antigens")

        # --- Payloads ---
        payload_map: dict[str, str] = {}
        for pl in data["payloads"]:
            if not validate_smiles(pl.get("smiles", "")):
                print(f"  WARN: Invalid SMILES for payload {pl['name']}, skipping SMILES")
                pl["smiles"] = None
            pl_id = str(uuid7())
            payload_map[pl["name"]] = pl_id
            mw = pl.get("mol_weight") or compute_mol_weight(pl.get("smiles", ""))
            session.add(Payload(
                id=pl_id,
                name=pl["name"],
                synonyms=pl.get("synonyms"),
                target=pl.get("target"),
                moa=pl.get("moa"),
                bystander_effect=pl.get("bystander_effect"),
                smiles=pl.get("smiles"),
                formula=pl.get("formula"),
                mol_weight=mw,
                morgan_fp=compute_morgan_fp(pl.get("smiles", "")),
            ))
        await session.flush()
        print(f"Inserted {len(payload_map)} payloads")

        # --- Linkers ---
        linker_map: dict[str, str] = {}
        for lk in data["linkers"]:
            smiles = lk.get("smiles", "")
            if smiles and not validate_smiles(smiles):
                print(f"  WARN: Invalid SMILES for linker {lk['name']}, skipping SMILES")
                smiles = None
            lk_id = str(uuid7())
            linker_map[lk["name"]] = lk_id
            session.add(Linker(
                id=lk_id,
                name=lk["name"],
                cleavable=lk.get("cleavable", True),
                cleavage_mechanism=lk.get("cleavage_mechanism"),
                coupling_chemistry=lk.get("coupling_chemistry"),
                smiles=smiles,
                formula=lk.get("formula"),
                mol_weight=compute_mol_weight(smiles) if smiles else None,
                morgan_fp=compute_morgan_fp(smiles) if smiles else None,
            ))
        await session.flush()
        print(f"Inserted {len(linker_map)} linkers")

        # --- Antibodies ---
        antibody_map: dict[str, str] = {}
        for ab in data["antibodies"]:
            antigen_name = ab.get("antigen")
            if antigen_name not in antigen_map:
                print(f"  WARN: Unknown antigen '{antigen_name}' for antibody {ab['name']}, skipping")
                continue
            ab_id = str(uuid7())
            antibody_map[ab["name"]] = ab_id
            session.add(Antibody(
                id=ab_id,
                name=ab["name"],
                synonyms=ab.get("synonyms"),
                isotype=ab.get("isotype"),
                origin=ab.get("origin"),
                antigen_id=antigen_map[antigen_name],
                heavy_chain_seq=ab.get("heavy_chain_seq"),
                light_chain_seq=ab.get("light_chain_seq"),
                uniprot_id=ab.get("uniprot_id"),
            ))
        await session.flush()
        print(f"Inserted {len(antibody_map)} antibodies")

        # --- ADCs ---
        adc_map: dict[str, str] = {}
        skipped = 0
        for adc in data["adcs"]:
            ab_name = adc.get("antibody")
            lk_name = adc.get("linker")
            pl_name = adc.get("payload")
            if ab_name not in antibody_map:
                print(f"  WARN: Unknown antibody '{ab_name}' for ADC {adc['name']}, skipping")
                skipped += 1
                continue
            if lk_name not in linker_map:
                print(f"  WARN: Unknown linker '{lk_name}' for ADC {adc['name']}, skipping")
                skipped += 1
                continue
            if pl_name not in payload_map:
                print(f"  WARN: Unknown payload '{pl_name}' for ADC {adc['name']}, skipping")
                skipped += 1
                continue

            adc_id = str(uuid7())
            adc_map[adc["name"]] = adc_id
            session.add(ADC(
                id=adc_id,
                name=adc["name"],
                brand_name=adc.get("brand_name"),
                synonyms=adc.get("synonyms"),
                organization=adc.get("organization"),
                status=adc.get("status", "investigative"),
                dar=adc.get("dar"),
                conjugation_site=adc.get("conjugation_site"),
                indications=adc.get("indications"),
                antibody_id=antibody_map[ab_name],
                linker_id=linker_map[lk_name],
                payload_id=payload_map[pl_name],
                linker_payload_smiles=adc.get("linker_payload_smiles"),
            ))
        await session.flush()
        print(f"Inserted {len(adc_map)} ADCs (skipped {skipped})")

        # --- Activities ---
        act_count = 0
        for act in data.get("activities", []):
            adc_name = act.get("adc")
            if adc_name not in adc_map:
                print(f"  WARN: Unknown ADC '{adc_name}' for activity, skipping")
                continue
            session.add(ADCActivity(
                id=str(uuid7()),
                adc_id=adc_map[adc_name],
                activity_type=act["activity_type"],
                nct_number=act.get("nct_number"),
                phase=act.get("phase"),
                orr=act.get("orr"),
                model=act.get("model"),
                tgi=act.get("tgi"),
                ic50_value=act.get("ic50_value"),
                ic50_unit=act.get("ic50_unit"),
                cell_line=act.get("cell_line"),
                notes=act.get("notes"),
            ))
            act_count += 1

        await session.commit()
        print(f"Inserted {act_count} activity records")
        print("Seed complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
