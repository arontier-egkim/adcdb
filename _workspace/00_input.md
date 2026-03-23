# ADCDB — Full Build Input

## Feature Description
Build the complete ADCDB (Antibody-Drug Conjugate Database) web application with predicted 3D structures. This includes a FastAPI backend, React frontend, MariaDB database, data seeding pipeline, and 3D structure generation.

## Scope
Full build — completing and verifying all layers of an existing scaffolded project.

## Existing Code Analysis
The project already has substantial scaffolding:

### Backend (~1300 lines)
- **Infrastructure**: `config.py`, `database.py`, `main.py` — FastAPI app with CORS, async SQLAlchemy
- **Models**: 6 ORM models (Antigen, Antibody, Linker, Payload, ADC, ADCActivity)
- **Schemas**: Pydantic models for all entities
- **Routers**: 7 routers (adcs, antibodies, antigens, linkers, payloads, search, stats)
- **Services**: `chemistry_service.py` (Morgan FP Tanimoto), `sequence_service.py` (Biopython)
- **Structure**: `conformer.py`, `assembler.py` for 3D generation
- **Alembic**: Migration setup present

### Frontend (~1200 lines)
- **Framework**: React 18 + Vite + TypeScript, shadcn/ui blue theme
- **Pages**: Home, Browse, Search, ADCDetail, AntibodyDetail, AntigenDetail, LinkerDetail, PayloadDetail, About, NotFound
- **Components**: Layout, MolViewer (Mol*), MoleculeDrawing (RDKit WASM)
- **Lib**: API client with types, utils

### Data (~1200 lines)
- **Seed**: `seed.py` with RDKit validation, `seed_data.json` (~887 lines, ~50 ADCs)
- **LP SMILES**: `add_lp_smiles.py` for curated linker-payload SMILES
- **3D Pipeline**: `generate_structures.py` for batch PDB generation

### Infrastructure
- `docker-compose.yml` — MariaDB 11.4
- `Makefile` — db, backend, frontend, migrate, seed, structures, setup targets
- 32 existing PDB files in `backend/structures/`

## Execution Mode
**Full Pipeline** — All 5 agents. Architect reviews existing code and produces design docs, then backend-dev + frontend-dev + devops run in parallel to verify/complete implementations, finally QA reviews everything.

## Key Constraints (from CLAUDE.md)
- All ORM relationships use `lazy="raise"`
- All ADC queries use explicit JOINs
- Antigen is on Antibody, not ADC
- Morgan fingerprints: radius=2, nbits=2048
- `linker_payload_smiles` is curated data, not computed
- `structure_3d_path` is nullable
