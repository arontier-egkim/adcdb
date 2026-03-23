# Architecture

## Overview

```
┌─────────────────────┐     ┌──────────────────────┐
│  React+Vite Frontend│────▶│   FastAPI Backend     │
│   (shadcn/ui, blue) │     │   (Python 3.12)       │
│   port 5173         │     │   port 8001            │
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
- `asyncmy` — MariaDB async driver (actively maintained; `aiomysql` is abandoned since 2021)
- `pydantic` 2.x — schemas (comes with FastAPI)
- `rdkit` — chemistry (SMILES parsing, fingerprints, conformer generation)
- `biopython` — sequence alignment

### Key Design Decisions

1. **Async SQLAlchemy** — FastAPI is async, so use async sessions. Simple.
2. **No caching layer** — MariaDB is fast enough for this dataset size (thousands, not millions). Add Redis later only if needed.
3. **File-based structure storage** — PDB files on disk, path stored in DB. No blob storage. If you outgrow disk, move to S3.
4. **RDKit (Python) for server-side chemistry** — molecular weight, fingerprints, 3D conformers. 2D depictions are handled client-side by RDKit WASM (see decision #6).
5. **No celery/task queue** — 3D structure generation is a batch job run offline, not on-demand. Pre-compute and store.
6. **CORSMiddleware** — Frontend (Vite default port 5173) calls backend (port 8001). Add `CORSMiddleware` to the FastAPI app with `allow_origins=["http://localhost:5173"]` in dev. Without this, the browser blocks every API call.
7. **UUIDv7 primary keys** — Time-sorted (RFC 9562) so B-tree inserts are sequential. Avoids page fragmentation that random UUID v4 causes in MariaDB. Use `uuid7()` from the `uuid_utils` package.
8. **`lazy="raise"` on all ORM relationships** — Accidental lazy-loads throw at dev time instead of silently firing N+1 queries.
9. **ON DELETE RESTRICT on all component FKs** — Prevent accidental cascade deletion. ADCActivity uses ON DELETE CASCADE (activities have no meaning without their ADC).

### Query Strategy — Avoiding N+1

Moving `antigen_id` to Antibody (biologically correct) creates a 2-hop path for every query that needs antigen info. **Every endpoint** is analyzed below.

**Global rule: No lazy-loading. Every relationship must be explicitly joined or eagerly loaded.**

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

These are the dangerous ones. Every component detail page shows "linked ADCs". **Always query from the ADC side with JOINs, never traverse backward through ORM relationships.**

**`GET /api/v1/antibodies/{id}` — Antibody detail (2 queries)**

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
LIMIT 50 OFFSET 0
```

**`GET /api/v1/antigens/{id}` — Antigen detail (worst case, e.g. HER2 = 1,311 ADCs)**

Do NOT traverse Antigen → Antibodies → ADCs. Go from ADC side with JOINs:

```sql
SELECT * FROM antigen WHERE id = :id

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

RDKit computes Tanimoto in Python. Query returns Linker/Payload rows ranked by similarity. No linked-ADC expansion in search results — user clicks through to detail page. **Fingerprint params must match index time: radius=2, nbits=2048.**

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

**Structure similarity:** Convert query SMILES → Morgan fingerprint (RDKit, radius=2, nbits=2048). Compare against pre-computed fingerprints (`morgan_fp` column on Linker and Payload tables) stored as binary in DB. Tanimoto coefficient. Return top-N. Parameters must be identical at index and query time.

**Sequence similarity:** For antibody sequence search, use Biopython's `Bio.Align.PairwiseAligner` for small-scale. If dataset grows, set up a local BLAST DB.

## Frontend (React + Vite + shadcn/ui)

### Dependencies (minimal)
- `react` 18 + `vite` — SPA framework (no SSR)
- `react-router` v7 — client-side routing
- `shadcn/ui` — component library (blue primary color)
- `molstar` — 3D molecular viewer (uses React internally — requires shared React runtime, which is why we use Vite instead of Next.js)
- `@iktos-oss/rdkit-provider` + `@iktos-oss/molecule-representation` — 2D molecule rendering from SMILES via RDKit WASM
- `recharts` — homepage charts

### Key Design Decisions

1. **SPA, not SSR** — Mol* v5 calls React internally. Next.js 14's SSR creates a React runtime conflict (`render is not a function`). Plain React + Vite = one React runtime = Mol* works.
2. **No state management library** — URL params (via `useSearchParams`) for search state, React state for UI. That's it.
3. **API calls via `fetch`** in `useEffect` — no axios, no SWR, no react-query. Simple `useState` + `useEffect` pattern for all data fetching.
4. **Mol\* lazy-loaded** — `React.lazy(() => import('./MolViewer'))` + `<Suspense>`. It's heavy (~2MB), only load on ADC detail page.
5. **No CORS proxy needed** — Backend has CORSMiddleware. Frontend fetches directly from `http://localhost:8001`.
6. **RDKit WASM for 2D structures** — `<RDKitProvider>` wraps the app root (loads WASM once). The worker file (`rdkit-worker-2.10.2.js`), `RDKit_minimal.js`, and `RDKit_minimal.wasm` must be in the `public/` folder so the browser can load them. `<MoleculeRepresentation>` renders interactive SVGs from SMILES on Linker and Payload detail pages via a `<MoleculeDrawing>` wrapper component. Linker SMILES with attachment points (`[*:1]`, `[*:2]`) are cleaned to `[H]` before rendering. **Drawing style: ACS1996** — exact values from RDKit's `rdMolDraw2D.SetACS1996Mode()`, passed via the `details` prop to `<MoleculeRepresentation>`:

   ```
   bondLineWidth: 0.6
   scaleBondWidth: false
   fixedBondLength: 7.2
   additionalAtomLabelPadding: 0.066
   multipleBondOffset: 0.18
   annotationFontScale: 0.5
   minFontSize: 6
   maxFontSize: 40
   ```

   **Zoom and scale:** `<MoleculeRepresentation>` is set with `zoomable={true}` for mouse wheel zoom in/out (powered by `@visx/zoom`, already a dependency). The molecule renders at 2x default scale by doubling `fixedBondLength` from 7.2 to 14.4 — this makes bonds (and thus the entire molecule) twice as large inside the 400x300 canvas. All other ACS1996 parameters remain at their spec values.

## 3D Structure Pipeline (Offline)

This runs as a batch script, NOT as part of the web app.

```
For each ADC:
  1. Build full IgG from template (PDB 1HZH) + sequence superposition
  2. Take linker_payload_smiles from ADC record ([*:1] = Ab end)
  3. Record [*:1] atom index, replace with [H], embed (ETKDGv3), minimize (MMFF94)
  4. Identify conjugation sites on antibody by conjugation_site type
  5. Place DAR copies of linker-payload at sites (rigid-body toward target residue)
  6. Save combined PDB → store path in DB
  7. On ANY failure: set structure_3d_path = NULL, log error, continue
```

**Why template-based IgG, not AlphaFold/ESMFold directly:**
AlphaFold DB stores individual chains, not the IgG tetramer. ESMFold predicts single chains. To get a full 2H+2L IgG, superpose the antibody's specific heavy/light chain sequences onto a template IgG crystal structure (e.g., PDB 1HZH) using backbone fitting. This is simpler and sufficient for reference visualization.

**Why `linker_payload_smiles` on ADC, not computed from separate SMILES:**
The linker's `[*:2]` end connects to the payload via specific chemistry (e.g., PABC carbamate to MMAE's secondary amine). Simulating this reaction computationally is fragile and error-prone. Instead, store the pre-connected molecule in `adc.linker_payload_smiles` with `[*:1]` marking the antibody attachment atom. This is a curated datum, not a computed one.

**Conjugation site identification** (driven by `adc.conjugation_site`):
- `cysteine`: find interchain disulfide S-S bonds in PDB (IgG1: C220, C226, C229 EU numbering). These Cys become available after partial reduction.
- `lysine`: compute solvent-accessible surface area per Lys residue. Select most exposed.
- `engineered_cysteine` / `engineered_other`: use known residue position from literature.

**Linker-payload placement:**
- The `coupling_chemistry` field on Linker tells us the bond geometry at the antibody end (maleimide → thioether, NHS → amide, click → triazole).
- Orient the `[*:1]` attachment atom toward the target residue's side-chain terminus.
- This is approximate rigid-body placement, not covalent docking.

**Antigen resolution:** ADC has no direct antigen FK. The antigen is resolved via `adc.antibody.antigen` — because the antibody-antigen binding is a biological property of the antibody itself.

The assembly is approximate. We're showing topology, not running MD simulations. Label as "predicted/modeled structure."

## Data Seeding

Initial data sourced from:
- Published ADC literature and FDA approval documents
- ChEMBL for payload/linker structures (SMILES)
- UniProt for antibody sequences and antigen info
- ClinicalTrials.gov for trial data (NCT numbers)
- AlphaFold DB for antibody structures where available

Seed script reads curated CSV/JSON files and populates the DB. Run after Alembic migrations.

**Validation on import** (fail-fast per row, don't block the batch):
- SMILES parseable by `Chem.MolFromSmiles()` — reject row if not
- Amino acid sequences contain only valid residue letters (ACDEFGHIKLMNPQRSTVWY)
- InChIKey matches SMILES where both are provided (`Chem.inchi.MolToInchiKey`)
- `linker_payload_smiles` contains exactly one `[*:1]` attachment point
- Morgan fingerprints computed and stored at index time (radius=2, nbits=2048)
