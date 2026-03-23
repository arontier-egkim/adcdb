# Deployment Guide

ADCDB is a local-development-first application. MariaDB runs in Docker; the backend (FastAPI) and frontend (Vite) run natively on the host.

## Prerequisites

| Tool | Version | Check command |
|------|---------|---------------|
| Docker + Docker Compose | latest (Compose V2) | `docker compose version` |
| Python | 3.12+ | `python3 --version` |
| uv (Python package manager) | latest | `uv --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| RDKit system library | 2025.09+ | `python3 -c "from rdkit import Chem; print(Chem.__version__)"` |

### Installing prerequisites

```bash
# macOS (Homebrew)
brew install python@3.12 node uv
brew install --cask docker

# RDKit -- install via conda/mamba if not available system-wide
# uv will pull the rdkit PyPI package if wheels are available for your platform
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADCDB_DATABASE_URL` | SQLAlchemy async connection string for MariaDB | `mysql+asyncmy://adcdb:adcdb_pass@127.0.0.1:3306/adcdb` | Yes |
| `ADCDB_CORS_ORIGINS` | JSON array of allowed frontend origins | `["http://localhost:5173"]` | Yes |
| `ADCDB_PORT` | Port for uvicorn to listen on | `8001` | No |
| `ADCDB_STRUCTURES_DIR` | Directory for generated PDB files (relative to `backend/`) | `structures` | No |

### Frontend (`frontend/.env`)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8001/api/v1` | Yes |

### Creating `.env` files

Copy the example files and adjust if needed:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The defaults work out of the box for local development. Only edit if you change ports or credentials.

## Initial Setup (from scratch)

### One-command setup

```bash
make setup
```

This runs the full pipeline:

1. Starts MariaDB in Docker (`docker compose up -d`)
2. Waits for MariaDB to pass its healthcheck
3. Runs Alembic migrations (creates all 6 tables)
4. Seeds the database with ~50 ADCs from `data/sources/seed_data.json`
5. Adds curated linker-payload SMILES (`data/add_lp_smiles.py`)
6. Generates 3D PDB structures via RDKit

### Then start the services

Open two separate terminals:

```bash
# Terminal 1 -- backend
make backend    # FastAPI on http://localhost:8001

# Terminal 2 -- frontend
make frontend   # Vite on http://localhost:5173
```

Open http://localhost:5173 in your browser.

### Manual step-by-step (if needed)

```bash
# 1. Install dependencies
make install-backend
make install-frontend

# 2. Create env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Start database
make db
make wait-db

# 4. Run migrations
make migrate

# 5. Seed data
make seed

# 6. Add linker-payload SMILES
make add-lp-smiles

# 7. Generate 3D structures
make structures

# 8. Start services
make backend    # in one terminal
make frontend   # in another terminal
```

## Makefile Reference

| Target | Description |
|--------|-------------|
| `make db` | Start MariaDB container |
| `make db-stop` | Stop MariaDB container |
| `make db-reset` | Destroy MariaDB volume and restart (deletes all data) |
| `make wait-db` | Block until MariaDB is healthy |
| `make install-backend` | Install Python dependencies with uv |
| `make install-frontend` | Install Node.js dependencies with npm |
| `make backend` | Start FastAPI dev server (port 8001) |
| `make frontend` | Start Vite dev server (port 5173) |
| `make migrate` | Run Alembic migrations |
| `make seed` | Seed database from seed_data.json |
| `make add-lp-smiles` | Add curated linker-payload SMILES to ADCs |
| `make structures` | Generate 3D PDB files |
| `make setup` | Full setup: db + wait + migrate + seed + add-lp-smiles + structures |

## Ports

| Service | Port | URL |
|---------|------|-----|
| MariaDB | 3306 | `mysql://127.0.0.1:3306/adcdb` |
| FastAPI backend | 8001 | http://localhost:8001 |
| Vite frontend | 5173 | http://localhost:5173 |
| FastAPI docs (Swagger) | 8001 | http://localhost:8001/docs |

## Docker Volumes

| Volume | Purpose |
|--------|---------|
| `adcdb-mariadb-data` | Persistent MariaDB data directory |

MariaDB data survives `docker compose down`. To fully reset, use `make db-reset` which runs `docker compose down -v`.

## Resetting the database

```bash
# Option 1: Re-run migrations on existing database
make migrate

# Option 2: Full reset (destroy and recreate)
make db-reset
make wait-db
make migrate
make seed
make add-lp-smiles
make structures
```

## Common Troubleshooting

### Port 3306 already in use

Another MySQL/MariaDB instance is running on the host. Either stop it or change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "3307:3306"
```

Then update `backend/.env`:

```
ADCDB_DATABASE_URL=mysql+asyncmy://adcdb:adcdb_pass@127.0.0.1:3307/adcdb
```

### "Can't connect to MySQL server" from backend

1. Check MariaDB is running: `docker compose ps`
2. Check it is healthy: `docker inspect adcdb-mariadb --format='{{.State.Health.Status}}'`
3. If unhealthy, check logs: `docker compose logs mariadb`
4. Verify `backend/.env` has the correct `ADCDB_DATABASE_URL`

### Migrations fail with "Table already exists"

The database already has tables from a previous run. Either:
- Skip the error (Alembic tracks migration state, this usually means it is already up to date)
- Reset: `make db-reset && make wait-db && make migrate`

### RDKit import error

RDKit requires native C++ libraries. If `import rdkit` fails:

```bash
# Option A: Install via conda
conda install -c conda-forge rdkit

# Option B: Check if the rdkit PyPI wheel supports your platform
uv pip install rdkit
```

### Structure generation fails

This is expected for some ADCs where linker-payload SMILES are missing or invalid. The `structure_3d_path` column will be NULL for those ADCs, and the frontend handles this gracefully by showing "Structure not available."

### Frontend shows "Network Error" or CORS error

1. Confirm the backend is running on port 8001
2. Check `frontend/.env` has `VITE_API_URL=http://localhost:8001/api/v1`
3. Check `backend/.env` has `ADCDB_CORS_ORIGINS=["http://localhost:5173"]`

### `make wait-db` times out

MariaDB can take 10-30 seconds on first start (initializing InnoDB). The timeout is 60 seconds. If it still fails:

```bash
docker compose logs mariadb   # check for errors
docker compose down -v         # clean slate
make db                        # try again
```
