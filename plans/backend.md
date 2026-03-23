# Backend Agent — FastAPI + MariaDB

## Execution Steps

1. **Ensure MariaDB is running:** `docker compose up -d` (from project root)
2. **Create backend project:** `mkdir -p backend && cd backend && uv init --python 3.12`
3. **Install deps:** `uv add fastapi 'uvicorn[standard]' 'sqlalchemy[asyncio]' alembic asyncmy pydantic-settings uuid-utils rdkit biopython`
4. **Create directory structure:** `mkdir -p app/models app/schemas app/routers app/services app/structure structures && touch app/__init__.py app/models/__init__.py app/schemas/__init__.py app/routers/__init__.py app/services/__init__.py app/structure/__init__.py`
5. **Create `app/config.py`:** pydantic-settings with `DATABASE_URL`, `CORS_ORIGINS`, `PORT`, `STRUCTURES_DIR`. Env prefix `ADCDB_`.
6. **Create `app/database.py`:** async engine from `config.DATABASE_URL`, `async_sessionmaker`, `DeclarativeBase`, `get_db` dependency.
7. **Create ORM models in FK order:**
   - `app/models/antigen.py` — no FKs
   - `app/models/linker.py` — no FKs
   - `app/models/payload.py` — no FKs
   - `app/models/antibody.py` — FK → Antigen
   - `app/models/adc.py` — FKs → Antibody, Linker, Payload
   - `app/models/activity.py` — FK → ADC (CASCADE)
   - `app/models/__init__.py` — import all models
   - All PKs: `String(36)`, default `lambda: str(uuid7())`. All relationships: `lazy="raise"`. FULLTEXT indexes on `name`. UNIQUE constraints on `name` and `inchikey`.
8. **Init Alembic:** `uv run alembic init alembic`. Edit `alembic/env.py` for async: import `Base.metadata` and `app.models`, use `async_engine_from_config` + `run_sync` pattern. Set `sqlalchemy.url` from `app.config.settings`.
9. **Generate and run migration:** `uv run alembic revision --autogenerate -m "initial tables" && uv run alembic upgrade head`
10. **Create Pydantic schemas** in `app/schemas/`: `antigen.py`, `linker.py`, `payload.py`, `antibody.py` (nests `AntigenRead`), `adc.py` (nests all components + `ADCListItem` flat variant), `activity.py`.
11. **Create routers** in `app/routers/`: `adcs.py`, `antibodies.py`, `antigens.py`, `linkers.py`, `payloads.py`, `search.py`, `stats.py`. Each entity router has list, detail, and linked-ADCs endpoints. All use explicit JOINs per the query patterns below.
12. **Create services** in `app/services/`: `chemistry_service.py` (Morgan FP Tanimoto search), `sequence_service.py` (Biopython PairwiseAligner).
13. **Create `app/main.py`:** FastAPI app with `CORSMiddleware`, lifespan handler, include all routers, `/api/v1/health` endpoint.
14. **Create structure endpoints:** `GET /api/v1/adcs/{id}/structure` returns `FileResponse` for PDB file.
15. **Verify:** `uv run uvicorn app.main:app --port 8001` → `curl http://localhost:8001/api/v1/health` returns `{"status": "ok"}`.

## Overview

**No over-engineering. No abstract base classes. No repository pattern. Just routers → services → DB.**

```
┌──────────────────────┐
│   FastAPI Backend     │
│   (Python 3.12)       │
│   port 8001            │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│   MariaDB 11.4 LTS    │
└──────────────────────┘
           │
┌──────────▼───────────┐
│   File Storage        │
│   (PDB files)         │
└──────────────────────┘
```

## Dependencies

- `fastapi` + `uvicorn` — web server
- `sqlalchemy` 2.0 — ORM (async)
- `alembic` — migrations
- `asyncmy` — MariaDB async driver (actively maintained; `aiomysql` is abandoned since 2021)
- `pydantic` 2.x — schemas (comes with FastAPI)
- `pydantic-settings` — env-based config
- `uuid-utils` — UUIDv7 generation
- `rdkit` — chemistry (SMILES parsing, fingerprints, conformer generation)
- `biopython` — sequence alignment

## Key Design Decisions

1. **Async SQLAlchemy** — FastAPI is async, so use async sessions.
2. **No caching layer** — MariaDB is fast enough for this dataset size (thousands, not millions).
3. **File-based structure storage** — PDB files on disk, path stored in DB.
4. **RDKit (Python) for server-side chemistry** — molecular weight, fingerprints, 3D conformers. 2D depictions are handled client-side by RDKit WASM.
5. **No celery/task queue** — 3D structure generation is a batch job run offline, not on-demand.
6. **CORSMiddleware** — Frontend (port 5173) calls backend (port 8001). Add `CORSMiddleware` with `allow_origins=["http://localhost:5173"]`.
7. **UUIDv7 primary keys** — Time-sorted (RFC 9562) so B-tree inserts are sequential. Use `uuid7()` from `uuid_utils`.
8. **`lazy="raise"` on all ORM relationships** — Accidental lazy-loads throw at dev time instead of silently firing N+1 queries.
9. **ON DELETE RESTRICT on all component FKs** — Prevent accidental cascade deletion. ADCActivity uses ON DELETE CASCADE.

## ORM Models

Six tables. See DATA.md for full field definitions. Key points for implementation:

- All PKs: `String(36)`, default `lambda: str(uuid7())`
- All relationships: `lazy="raise"`
- JSON columns: `synonyms`, `indications` — use SQLAlchemy `JSON` type
- Binary columns: `morgan_fp` — use `LargeBinary`
- FULLTEXT indexes on all `name` columns (use `mariadb_prefix="FULLTEXT"`)
- B-tree index on `adc.status`
- Unique constraints on `name` fields and `inchikey` fields

## API Endpoints

```
GET  /api/v1/health                  # health check
GET  /api/v1/stats                   # aggregate counts for homepage

GET  /api/v1/adcs                    # list + filter (?status=, ?antigen=, ?q=) + paginate
GET  /api/v1/adcs/{id}              # detail with all components + activities
GET  /api/v1/adcs/{id}/structure    # serve PDB file (FileResponse)

GET  /api/v1/antibodies              # list
GET  /api/v1/antibodies/{id}        # detail with antigen
GET  /api/v1/antibodies/{id}/adcs   # linked ADCs

GET  /api/v1/antigens                # list
GET  /api/v1/antigens/{id}          # detail
GET  /api/v1/antigens/{id}/adcs     # linked ADCs (reverse 2-hop)

GET  /api/v1/linkers                 # list
GET  /api/v1/linkers/{id}           # detail
GET  /api/v1/linkers/{id}/adcs      # linked ADCs

GET  /api/v1/payloads                # list
GET  /api/v1/payloads/{id}          # detail
GET  /api/v1/payloads/{id}/adcs     # linked ADCs

GET  /api/v1/search?q=term          # unified text search
GET  /api/v1/search/structure?smiles=...  # SMILES similarity (Tanimoto)
GET  /api/v1/search/sequence?sequence=... # sequence similarity
```

## Query Strategy — Avoiding N+1

ADC reaches Antigen via `ADC → Antibody → Antigen` (2 hops). **Every endpoint** must use explicit JOINs.

**Global rule: No lazy-loading. Every relationship must be explicitly joined or eagerly loaded.**

### Forward queries (ADC → components)

**`GET /api/v1/adcs` — ADC list/search/browse (1 query)**

```sql
SELECT adc.*, ab.name AS antibody_name, ag.name AS antigen_name,
       l.name AS linker_name, p.name AS payload_name
FROM adc
JOIN antibody ab ON adc.antibody_id = ab.id
JOIN antigen ag  ON ab.antigen_id = ag.id
JOIN linker l    ON adc.linker_id = l.id
JOIN payload p   ON adc.payload_id = p.id
WHERE ... LIMIT 50 OFFSET 0
```

```python
stmt = (
    select(ADC)
    .options(
        joinedload(ADC.antibody).joinedload(Antibody.antigen),
        joinedload(ADC.linker),
        joinedload(ADC.payload),
    )
)
```

**`GET /api/v1/adcs/{id}` — ADC detail (2 queries)**

Query 1: ADC + all 4 components (same JOIN, `WHERE adc.id = :id`).
Query 2: Activities (`WHERE adc_id = :id`). Flat rows, no nested relationships.

### Reverse queries (component detail → linked ADCs)

**Always query from the ADC side with JOINs, never traverse backward through ORM relationships.**

**`GET /api/v1/antibodies/{id}` — (2 queries)**

```sql
SELECT ab.*, ag.name AS antigen_name FROM antibody ab
JOIN antigen ag ON ab.antigen_id = ag.id WHERE ab.id = :id

SELECT adc.*, l.name AS linker_name, p.name AS payload_name
FROM adc JOIN linker l ON adc.linker_id = l.id JOIN payload p ON adc.payload_id = p.id
WHERE adc.antibody_id = :antibody_id LIMIT 50 OFFSET 0
```

**`GET /api/v1/antigens/{id}` — worst case (e.g. HER2 = 1,311 ADCs)**

```sql
SELECT * FROM antigen WHERE id = :id

SELECT adc.*, ab.name AS antibody_name, l.name AS linker_name, p.name AS payload_name
FROM adc
JOIN antibody ab ON adc.antibody_id = ab.id
JOIN linker l ON adc.linker_id = l.id JOIN payload p ON adc.payload_id = p.id
WHERE ab.antigen_id = :antigen_id LIMIT 50 OFFSET 0
```

Paginate. Never load 1,311 ADCs at once.

**`GET /api/v1/linkers/{id}` and `GET /api/v1/payloads/{id}` — (2 queries each)**

Same pattern: entity + linked ADCs via 4-way JOIN from ADC side.

### Summary: max queries per endpoint

| Endpoint | Queries | Notes |
|----------|---------|-------|
| ADC list/browse/search | 1 | 4-way JOIN, paginated |
| ADC detail | 2 | components JOIN + activities |
| Antibody detail | 2 | antibody+antigen + linked ADCs |
| Antigen detail | 2 | antigen + linked ADCs (reverse 2-hop) |
| Linker detail | 2 | linker + linked ADCs |
| Payload detail | 2 | payload + linked ADCs |
| Unified search | 1 per entity type | max 5 |
| Stats | 3 | raw SQL aggregations |

## Search Implementation

**Text search:** MariaDB `FULLTEXT` index on `name` fields with `MATCH ... AGAINST`. For synonyms (JSON), use `JSON_SEARCH()` / `JSON_CONTAINS()`. For fuzzy matching, `LIKE '%term%'`.

**Structure similarity:** Convert query SMILES → Morgan fingerprint (radius=2, nbits=2048). Compare against pre-computed `morgan_fp` columns on Linker and Payload. Tanimoto coefficient. Return top-N. **Params must match index time.**

**Sequence similarity:** Biopython `Bio.Align.PairwiseAligner` against antibody heavy/light chain sequences. Normalize by query length.

## Stats Queries (raw SQL, no ORM)

```sql
SELECT ag.name, COUNT(adc.id) AS adc_count
FROM adc JOIN antibody ab ON adc.antibody_id = ab.id JOIN antigen ag ON ab.antigen_id = ag.id
GROUP BY ag.id ORDER BY adc_count DESC LIMIT 5

SELECT p.target, COUNT(adc.id) AS adc_count
FROM adc JOIN payload p ON adc.payload_id = p.id
GROUP BY p.target ORDER BY adc_count DESC LIMIT 5

SELECT status, COUNT(*) AS cnt FROM adc GROUP BY status
```

## File Structure

```
backend/
├── pyproject.toml
├── alembic/                  # DB migrations
│   ├── env.py               # async migration runner
│   └── versions/
├── app/
│   ├── main.py              # FastAPI app + CORSMiddleware
│   ├── config.py            # pydantic-settings (DATABASE_URL, CORS_ORIGINS, PORT)
│   ├── database.py          # async engine + session factory
│   ├── models/              # SQLAlchemy ORM
│   │   ├── antigen.py
│   │   ├── antibody.py      # FK → antigen
│   │   ├── linker.py
│   │   ├── payload.py
│   │   ├── adc.py           # FKs → antibody, linker, payload
│   │   └── activity.py      # FK → adc (CASCADE)
│   ├── schemas/             # Pydantic models
│   ├── routers/             # adcs, antibodies, antigens, linkers, payloads, search, stats
│   ├── services/            # chemistry_service.py, sequence_service.py
│   └── structure/           # conformer.py, assembler.py
└── structures/              # generated PDB files
```
