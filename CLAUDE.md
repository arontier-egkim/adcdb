# ADCDB

Antibody-Drug Conjugate Database with predicted 3D structures.

## Quick Start

```bash
make setup     # Start MariaDB, run migrations, seed data, generate structures
make backend   # Start FastAPI on port 8001
make frontend  # Start Vite dev server on port 5173
```

## Stack

- **Backend:** FastAPI + Python 3.12 + MariaDB 11.4 LTS + SQLAlchemy async + asyncmy
- **Frontend:** React 18 + Vite + shadcn/ui (blue) + Mol* for 3D viewer
- **Database:** MariaDB 11.4 LTS in Docker

## Key Rules

- All ORM relationships use `lazy="raise"` — no accidental lazy-loading
- All ADC queries use explicit JOINs (see ARCHITECTURE.md for per-endpoint patterns)
- Antigen is on Antibody, not ADC — ADC reaches antigen via `adc.antibody.antigen`
- Morgan fingerprints: radius=2, nbits=2048 — must match at index and query time
- `linker_payload_smiles` is curated data, not computed
- `structure_3d_path` is nullable — NULL means generation failed
