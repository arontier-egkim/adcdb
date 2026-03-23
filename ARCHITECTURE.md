# Architecture

## Overview

```
┌─────────────────────┐     ┌──────────────────────┐
│   Next.js Frontend  │────▶│   FastAPI Backend     │
│   (shadcn/ui, blue) │     │   (Python 3.12)       │
│   port 3000         │     │   port 8000            │
└─────────────────────┘     └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │   MariaDB 11.4 LTS    │
                            └──────────────────────┘
                                       │
                            ┌──────────▼───────────┐
                            │   File Storage        │
                            │   (PDB/mmCIF files)   │
                            └──────────────────────┘
```

## Backend (FastAPI)

**No over-engineering. No abstract base classes. No repository pattern. Just routers → services → DB.**

### Dependencies (minimal)
- `fastapi` + `uvicorn` — web server
- `sqlalchemy` 2.0 — ORM (async)
- `alembic` — migrations
- `aiomysql` — MariaDB async driver
- `pydantic` 2.x — schemas (comes with FastAPI)
- `rdkit` — chemistry (SMILES parsing, fingerprints, conformer generation)
- `biopython` — sequence alignment

### Key Design Decisions

1. **Async SQLAlchemy** — FastAPI is async, so use async sessions. Simple.
2. **No caching layer** — MariaDB is fast enough for this dataset size (thousands, not millions). Add Redis later only if needed.
3. **File-based structure storage** — PDB files on disk, path stored in DB. No blob storage. If you outgrow disk, move to S3.
4. **RDKit for everything chemistry** — molecular weight, fingerprints, 2D depictions, 3D conformers. One library.
5. **No celery/task queue** — 3D structure generation is a batch job run offline, not on-demand. Pre-compute and store.

### Query Strategy — Avoiding N+1

Moving `antigen_id` to Antibody (biologically correct) creates a 2-hop path for every query that needs antigen info. **Every endpoint** is analyzed below.

**Global rule: No lazy-loading. Every relationship must be explicitly joined or eagerly loaded.**

Set `lazy="raise"` on all SQLAlchemy relationships so accidental lazy-loads throw an error at dev time instead of silently firing queries.

#### Forward queries (ADC → components)

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

Query 1: ADC + all 4 components (same JOIN as above, `WHERE adc.id = :id`).
Query 2: Activities for this ADC (`WHERE adc_id = :id`). Flat rows, no nested relationships.

#### Reverse queries (component detail → linked ADCs)

These are the dangerous ones. Every component detail page shows "linked ADCs".

**`GET /api/v1/antibodies/{id}` — Antibody detail (1 query)**

```sql
SELECT ab.*, ag.name AS antigen_name FROM antibody ab
JOIN antigen ag ON ab.antigen_id = ag.id
WHERE ab.id = :id
```

Linked ADCs (1 query — JOIN from ADC side, not lazy-load from Antibody):

```sql
SELECT adc.*, l.name AS linker_name, p.name AS payload_name
FROM adc
JOIN linker l  ON adc.linker_id = l.id
JOIN payload p ON adc.payload_id = p.id
WHERE adc.antibody_id = :antibody_id
```

**`GET /api/v1/antigens/{id}` — Antigen detail (worst case, e.g. HER2 = 1,311 ADCs)**

Do NOT traverse Antigen → Antibodies → ADCs. Go from ADC side with JOINs:

```sql
-- 1 query for the antigen itself
SELECT * FROM antigen WHERE id = :id

-- 1 query for ALL linked ADCs (reverse 2-hop, but as a single JOIN)
SELECT adc.*, ab.name AS antibody_name,
       l.name AS linker_name, p.name AS payload_name
FROM adc
JOIN antibody ab ON adc.antibody_id = ab.id
JOIN linker l    ON adc.linker_id = l.id
JOIN payload p   ON adc.payload_id = p.id
WHERE ab.antigen_id = :antigen_id
LIMIT 50 OFFSET 0
```

Paginate. Never load 1,311 ADCs at once.

**`GET /api/v1/linkers/{id}` — Linker detail (2 queries)**

```sql
SELECT * FROM linker WHERE id = :id

SELECT adc.*, ab.name AS antibody_name, ag.name AS antigen_name,
       p.name AS payload_name
FROM adc
JOIN antibody ab ON adc.antibody_id = ab.id
JOIN antigen ag  ON ab.antigen_id = ag.id
JOIN payload p   ON adc.payload_id = p.id
WHERE adc.linker_id = :linker_id
LIMIT 50 OFFSET 0
```

**`GET /api/v1/payloads/{id}` — Payload detail (2 queries)**

Same pattern as Linker, swapping `payload_id` filter and joining Linker instead.

#### Search queries

**`GET /api/v1/search` — Unified text search**

Search across entity `name` fields with `MATCH ... AGAINST`. Return results grouped by entity type. For ADC results, use the full 4-JOIN query. For Antibody results, join Antigen. For Linker/Payload/Antigen results, no joins needed — they're flat.

**`GET /api/v1/search/structure` — SMILES similarity**

RDKit computes Tanimoto in Python. Query returns Linker/Payload rows ranked by similarity. No linked-ADC expansion needed in search results — user clicks through to detail page.

**`GET /api/v1/search/sequence` — Sequence similarity**

Returns Antibody rows ranked by alignment score. Same as structure search — no ADC expansion in results.

#### Stats queries

**`GET /api/v1/stats` — Aggregation (raw SQL, no ORM objects)**

```sql
-- Top antigens by ADC count
SELECT ag.name, COUNT(adc.id) AS adc_count
FROM adc
JOIN antibody ab ON adc.antibody_id = ab.id
JOIN antigen ag  ON ab.antigen_id = ag.id
GROUP BY ag.id ORDER BY adc_count DESC LIMIT 5

-- Top payload targets
SELECT p.target, COUNT(adc.id) AS adc_count
FROM adc JOIN payload p ON adc.payload_id = p.id
GROUP BY p.target ORDER BY adc_count DESC LIMIT 5

-- Pipeline funnel
SELECT status, COUNT(*) AS cnt FROM adc GROUP BY status
```

#### Summary: max queries per endpoint

| Endpoint | Queries | Notes |
|----------|---------|-------|
| ADC list/browse/search | 1 | 4-way JOIN, paginated |
| ADC detail | 2 | components JOIN + activities |
| Antibody detail | 2 | antibody+antigen + linked ADCs with JOIN |
| Antigen detail | 2 | antigen + linked ADCs via reverse 2-hop JOIN, paginated |
| Linker detail | 2 | linker + linked ADCs with JOIN |
| Payload detail | 2 | payload + linked ADCs with JOIN |
| Unified search | 1 per entity type | max 5 (one per tab) |
| Stats | 3 | raw SQL aggregations |

### Search Implementation

**Text search:** MariaDB `FULLTEXT` index on `name` fields (VARCHAR/TEXT) with `MATCH ... AGAINST` in natural language or boolean mode. For synonyms (JSON columns), use `JSON_SEARCH()` or `JSON_CONTAINS()`. For fuzzy/partial matching on names, use `LIKE '%term%'`. One query, no external search engine.

**Structure similarity:** Convert query SMILES → Morgan fingerprint (RDKit). Compare against pre-computed fingerprints (`morgan_fp` column on Linker and Payload tables) stored as binary in DB. Tanimoto coefficient. Return top-N.

**Sequence similarity:** For antibody sequence search, use Biopython's `Bio.Align.PairwiseAligner` for small-scale. If dataset grows, set up a local BLAST DB.

## Frontend (Next.js + shadcn/ui)

### Dependencies (minimal)
- `next` 14 — framework
- `shadcn/ui` — component library (blue primary color)
- `@tanstack/react-table` — data tables (comes with shadcn)
- `molstar` — 3D molecular viewer
- `recharts` — homepage charts (shadcn has chart components built on this)

### Key Design Decisions

1. **Server components by default** — fetch data on the server, render HTML. Client components only for interactive bits (search bar, 3D viewer, charts).
2. **No state management library** — URL params for search state, React state for UI. That's it.
3. **API calls via `fetch`** — no axios, no SWR, no react-query. Next.js `fetch` with caching is enough.
4. **Mol\* as a client component** — lazy-loaded, only on ADC detail page. It's heavy (~2MB), don't load it everywhere.

## 3D Structure Pipeline (Offline)

This runs as a batch script, NOT as part of the web app.

```
For each ADC:
  1. Get antibody sequence → predict structure (ESMFold API or AlphaFold DB)
  2. Get linker SMILES → generate 3D conformer (RDKit)
  3. Get payload SMILES → generate 3D conformer (RDKit)
  4. Assemble: attach linker-payload at conjugation site on antibody
  5. Save as .pdb → store path in DB
```

**Conjugation site logic** (driven by `adc.conjugation_type` field):
- Cysteine conjugation (most common): attach at interchain disulfide Cys residues
- Lysine conjugation: attach at surface-exposed Lys
- Site-specific: attach at engineered site (if known)

**Antigen resolution:** ADC has no direct antigen FK. The antigen is resolved via `adc.antibody.antigen` — because the antibody-antigen binding is a biological property of the antibody itself.

The assembly is approximate. We're showing topology, not running MD simulations.

## Data Seeding

Initial data sourced from:
- Published ADC literature and FDA approval documents
- ChEMBL for payload/linker structures (SMILES)
- UniProt for antibody sequences and antigen info
- ClinicalTrials.gov for trial data (NCT numbers)
- AlphaFold DB for antibody structures where available

Seed script reads curated CSV/JSON files and populates the DB.
