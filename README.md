# ADCDB — Antibody-Drug Conjugate Database

A web database for browsing, searching, and visualizing Antibody-Drug Conjugates (ADCs) with predicted 3D structures.

## Prerequisites

- **Docker** — for MariaDB 11.4 LTS
- **Python 3.12** — backend
- **uv** — Python package manager (`brew install uv`)
- **Node.js 18+** — frontend
- **npm** — comes with Node.js

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> adcdb && cd adcdb

# 2. Install backend dependencies
cd backend && uv sync && cd ..

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. One command to set up everything
make setup
```

`make setup` does the following:

1. Starts MariaDB 11.4 LTS in Docker
2. Waits for it to be ready
3. Runs Alembic migrations (creates all 6 tables)
4. Seeds the database with ~50 ADCs, antibodies, linkers, payloads, antigens, and activity data
5. Generates 3D structure PDB files for 32 ADCs

Then start both servers:

```bash
# Terminal 1 — backend
make backend

# Terminal 2 — frontend
make frontend
```

Open http://localhost:5173 in your browser.

## Makefile Commands

| Command           | What it does                                                    |
| ----------------- | --------------------------------------------------------------- |
| `make db`         | Start MariaDB Docker container                                  |
| `make migrate`    | Run Alembic database migrations                                 |
| `make seed`       | Seed database with ~50 ADCs                                     |
| `make structures` | Generate 3D PDB files for all ADCs with `linker_payload_smiles` |
| `make backend`    | Start FastAPI server on port 8001 (with hot reload)             |
| `make frontend`   | Start Vite dev server on port 5173                              |
| `make setup`      | Run db + migrate + seed + structures in order                   |

## URLs

| Service      | URL                                                    |
| ------------ | ------------------------------------------------------ |
| Frontend     | http://localhost:5173                                  |
| Backend API  | http://localhost:8001/api/v1                           |
| Swagger docs | http://localhost:8001/docs                             |
| MariaDB      | localhost:3306 (user: `adcdb`, password: `adcdb_pass`) |

## Project Structure

```
adcdb/
├── backend/                 # FastAPI + Python 3.12
│   ├── app/
│   │   ├── main.py          # FastAPI app + CORS
│   │   ├── config.py        # Settings (env vars)
│   │   ├── database.py      # SQLAlchemy async engine
│   │   ├── models/          # ORM models (6 tables)
│   │   ├── schemas/         # Pydantic request/response
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Chemistry + sequence search
│   │   └── structure/       # 3D structure generation
│   ├── alembic/             # Database migrations
│   └── structures/          # Generated PDB files
├── frontend/                # React 18 + Vite + shadcn/ui
│   └── src/
│       ├── pages/           # Route components
│       ├── components/      # MolViewer, Layout, UI
│       └── lib/             # API client, utilities
├── data/                    # Seed scripts + source data
│   ├── seed.py              # Database seeder with RDKit validation
│   ├── generate_structures.py
│   └── sources/seed_data.json
├── docker-compose.yml       # MariaDB 11.4 LTS
├── Makefile                 # All commands
├── PLAN.md                  # Full project plan
├── ARCHITECTURE.md          # Query patterns, design decisions
└── DATA_MODEL.md            # ER diagram, constraints, indexes
```

## API Endpoints

```
GET  /api/v1/health                  # Health check
GET  /api/v1/stats                   # Homepage stats (top antigens, pipeline)

GET  /api/v1/adcs                    # List ADCs (filter: ?status=approved&q=name)
GET  /api/v1/adcs/{id}              # ADC detail with all components + activities
GET  /api/v1/adcs/{id}/structure    # Download PDB file

GET  /api/v1/antibodies              # List antibodies
GET  /api/v1/antibodies/{id}        # Antibody detail
GET  /api/v1/antibodies/{id}/adcs   # ADCs using this antibody

GET  /api/v1/antigens                # List antigens
GET  /api/v1/antigens/{id}          # Antigen detail
GET  /api/v1/antigens/{id}/adcs     # ADCs targeting this antigen

GET  /api/v1/linkers                 # List linkers
GET  /api/v1/linkers/{id}           # Linker detail
GET  /api/v1/linkers/{id}/adcs      # ADCs using this linker

GET  /api/v1/payloads                # List payloads
GET  /api/v1/payloads/{id}          # Payload detail
GET  /api/v1/payloads/{id}/adcs     # ADCs using this payload

GET  /api/v1/search?q=term          # Text search across all entities
GET  /api/v1/search/structure?smiles=...  # SMILES similarity (Tanimoto)
GET  /api/v1/search/sequence?sequence=... # Sequence similarity (PairwiseAligner)
```

## Environment Variables

Copy the example files and adjust if needed:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

**Backend** (`backend/.env`):

| Variable             | Default                                                 | Description          |
| -------------------- | ------------------------------------------------------- | -------------------- |
| `ADCDB_DATABASE_URL` | `mysql+asyncmy://adcdb:adcdb_pass@127.0.0.1:3306/adcdb` | MariaDB connection   |
| `ADCDB_CORS_ORIGINS` | `["http://localhost:5173"]`                             | Allowed CORS origins |
| `ADCDB_PORT`         | `8001`                                                  | Server port          |

**Frontend** (`frontend/.env`):

| Variable       | Default                        | Description          |
| -------------- | ------------------------------ | -------------------- |
| `VITE_API_URL` | `http://localhost:8001/api/v1` | Backend API base URL |

## Tech Stack

| Layer              | Technology                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| Backend            | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Alembic                                                  |
| Database           | MariaDB 11.4 LTS, asyncmy driver                                                                       |
| Frontend           | React 18, Vite, shadcn/ui (blue theme), React Router v7                                                |
| 3D Viewer          | Mol\* (molstar)                                                                                        |
| 2D Structures      | RDKit WASM (`@iktos-oss/rdkit-provider` + `@iktos-oss/molecule-representation`), ACS1996 drawing style |
| Chemistry (server) | RDKit Python (fingerprints, conformers, molecular properties)                                          |
| Sequence           | Biopython PairwiseAligner                                                                              |
