# ADCDB

Antibody-Drug Conjugate Database with predicted 3D structures.

## Quick Start

```bash
make setup     # Start MariaDB, run migrations, seed data, generate structures
make backend   # Start FastAPI on port 8001
make frontend  # Start Vite dev server on port 5173
```

## Docs

- **plans/index.md** — Overview, tech stack, API contract, project structure (start here)
- **plans/backend.md** — Backend agent: FastAPI, queries, N+1 avoidance, endpoints
- **plans/frontend.md** — Frontend agent: React, Mol* 3D viewer, RDKit WASM 2D drawings
- **plans/data.md** — Data agent: schema, seed sources, validation, 3D pipeline

## Key Rules

- All ORM relationships use `lazy="raise"` — no accidental lazy-loading
- All ADC queries use explicit JOINs (see BACKEND.md for per-endpoint patterns)
- Antigen is on Antibody, not ADC — ADC reaches antigen via `adc.antibody.antigen`
- Morgan fingerprints: radius=2, nbits=2048 — must match at index and query time
- `linker_payload_smiles` is curated data, not computed
- `structure_3d_path` is nullable — NULL means generation failed
