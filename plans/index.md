# ADCDB — Antibody-Drug Conjugate Database

A web database for browsing, searching, and visualizing Antibody-Drug Conjugates (ADCs) with predicted 3D structures.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 async, MariaDB 11.4 LTS |
| Frontend | React 18, Vite, shadcn/ui (blue), React Router v7 |
| 3D Viewer | Mol* (molstar) |
| 2D Structures | RDKit WASM (@iktos-oss/rdkit-provider), ACS1996 style |
| Chemistry (server) | RDKit Python |
| Search | MariaDB full-text, RDKit fingerprints (Tanimoto), Biopython PairwiseAligner |

## Data Model

```
Antigen ── Antibody ──┐
                      ├── ADC ── ADCActivity
Linker ───────────────┤
                      │
Payload ──────────────┘
```

Six tables. ADC is the hub. Antigen lives on Antibody (biologically correct). V1 limitation: no bispecific antibodies.

## Agent Docs

| Doc | Agent | What's inside |
|-----|-------|---------------|
| [backend.md](backend.md) | Backend developer | FastAPI setup, ORM models, all query patterns with exact SQL, N+1 avoidance, API endpoints, search implementation, CORS, UUIDv7 |
| [frontend.md](frontend.md) | Frontend developer | React + Vite + shadcn/ui, React Router routes, Mol* 3D viewer, RDKit WASM 2D drawings (ACS1996), page descriptions, API client types |
| [data.md](data.md) | Data collector/analyst | ER diagram, all table schemas, constraints, indexes, seed data sources, validation rules, 3D structure pipeline, SMILES conventions |

## API Contract (shared between backend and frontend)

```
GET  /api/v1/health
GET  /api/v1/stats

GET  /api/v1/adcs                    GET  /api/v1/adcs/{id}
GET  /api/v1/adcs/{id}/structure

GET  /api/v1/antibodies              GET  /api/v1/antibodies/{id}
GET  /api/v1/antibodies/{id}/adcs

GET  /api/v1/antigens                GET  /api/v1/antigens/{id}
GET  /api/v1/antigens/{id}/adcs

GET  /api/v1/linkers                 GET  /api/v1/linkers/{id}
GET  /api/v1/linkers/{id}/adcs

GET  /api/v1/payloads                GET  /api/v1/payloads/{id}
GET  /api/v1/payloads/{id}/adcs

GET  /api/v1/search?q=              GET  /api/v1/search/structure?smiles=
GET  /api/v1/search/sequence?sequence=
```

## Project Structure

```
adcdb/
├── backend/           → see BACKEND.md
│   ├── app/
│   │   ├── main.py, config.py, database.py
│   │   ├── models/, schemas/, routers/, services/
│   │   └── structure/
│   ├── alembic/
│   └── structures/
├── frontend/          → see FRONTEND.md
│   ├── src/
│   │   ├── pages/, components/, lib/
│   │   └── main.tsx, App.tsx, globals.css
│   └── public/        (RDKit WASM files)
├── data/              → see DATA.md
│   ├── seed.py, generate_structures.py
│   └── sources/seed_data.json
├── PLAN.md            ← you are here
├── BACKEND.md
├── FRONTEND.md
├── DATA.md
├── README.md
├── CLAUDE.md
├── Makefile
└── docker-compose.yml
```
