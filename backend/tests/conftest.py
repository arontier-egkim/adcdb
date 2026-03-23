"""Shared test fixtures for ADCDB backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from uuid_utils import uuid7

from app.database import Base, get_db
from app.main import app
from app.models import ADC, ADCActivity, Antibody, Antigen, Linker, Payload

# Use aiosqlite for in-memory test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def db_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine):
    """Provide a transactional session for each test."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture()
async def client(db_engine):
    """Provide an httpx AsyncClient bound to the FastAPI app with test DB."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture()
async def seed_data(db_session: AsyncSession):
    """Insert minimal seed data and return IDs for reference."""
    # Antigen
    antigen_id = str(uuid7())
    db_session.add(Antigen(
        id=antigen_id,
        name="HER2",
        synonyms=["ERBB2", "CD340"],
        gene_name="ERBB2",
        uniprot_id="P04626",
        description="Receptor tyrosine kinase",
    ))

    antigen_id2 = str(uuid7())
    db_session.add(Antigen(
        id=antigen_id2,
        name="Trop-2",
        gene_name="TACSTD2",
    ))

    # Linker
    linker_id = str(uuid7())
    db_session.add(Linker(
        id=linker_id,
        name="MC-VC-PABC",
        cleavable=True,
        cleavage_mechanism="protease",
        coupling_chemistry="maleimide",
        smiles="[*:1]CCCCCC(=O)NC(CC(C)C)C(=O)O",
        formula="C12H22N2O3",
        mol_weight=242.3,
    ))

    # Payload
    payload_id = str(uuid7())
    db_session.add(Payload(
        id=payload_id,
        name="MMAE",
        synonyms=["Monomethyl auristatin E"],
        target="Microtubule",
        moa="Microtubule inhibitor",
        bystander_effect=True,
        smiles="CCC(C)C(C(CC(=O)N1CCCC1C(OC)C(C)C(=O)NC(CC2=CC=CC=C2)C(=O)O)OC)NC(=O)C(NC)CC3=CC=CC=C3",
        formula="C39H65N5O7",
        mol_weight=717.9643,
    ))

    payload_id2 = str(uuid7())
    db_session.add(Payload(
        id=payload_id2,
        name="DXd",
        target="Topoisomerase I",
        smiles="C",  # placeholder
    ))

    # Antibody
    antibody_id = str(uuid7())
    db_session.add(Antibody(
        id=antibody_id,
        name="Trastuzumab",
        isotype="IgG1",
        origin="humanized",
        antigen_id=antigen_id,
        heavy_chain_seq="EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTR",
        light_chain_seq="DIQMTQSPSSLSASVGDRVTITCRASQDVNTAVAWYQQKPGKAPKLLIYSASFLYSGVP",
        uniprot_id="P04626",
    ))

    antibody_id2 = str(uuid7())
    db_session.add(Antibody(
        id=antibody_id2,
        name="Sacituzumab",
        isotype="IgG1",
        origin="humanized",
        antigen_id=antigen_id2,
    ))

    await db_session.flush()

    # ADC
    adc_id = str(uuid7())
    db_session.add(ADC(
        id=adc_id,
        name="Trastuzumab deruxtecan",
        brand_name="Enhertu",
        synonyms=["T-DXd", "DS-8201"],
        organization="Daiichi Sankyo / AstraZeneca",
        status="approved",
        dar=8.0,
        conjugation_site="cysteine",
        indications=["HER2+ breast cancer", "HER2+ gastric cancer"],
        antibody_id=antibody_id,
        linker_id=linker_id,
        payload_id=payload_id,
        linker_payload_smiles="[*:1]CCCCCC(=O)NCC(=O)O",
    ))

    adc_id2 = str(uuid7())
    db_session.add(ADC(
        id=adc_id2,
        name="Sacituzumab govitecan",
        brand_name="Trodelvy",
        status="approved",
        dar=7.6,
        antibody_id=antibody_id2,
        linker_id=linker_id,
        payload_id=payload_id2,
    ))

    adc_id3 = str(uuid7())
    db_session.add(ADC(
        id=adc_id3,
        name="Test Phase 1 ADC",
        status="phase_1",
        antibody_id=antibody_id,
        linker_id=linker_id,
        payload_id=payload_id,
    ))

    await db_session.flush()

    # Activity
    activity_id = str(uuid7())
    db_session.add(ADCActivity(
        id=activity_id,
        adc_id=adc_id,
        activity_type="clinical_trial",
        nct_number="NCT03248492",
        phase="Phase III",
        orr=79.7,
        notes="DESTINY-Breast03",
    ))

    await db_session.commit()

    return {
        "antigen_id": antigen_id,
        "antigen_id2": antigen_id2,
        "linker_id": linker_id,
        "payload_id": payload_id,
        "payload_id2": payload_id2,
        "antibody_id": antibody_id,
        "antibody_id2": antibody_id2,
        "adc_id": adc_id,
        "adc_id2": adc_id2,
        "adc_id3": adc_id3,
        "activity_id": activity_id,
    }
