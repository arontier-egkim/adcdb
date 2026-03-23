# Architecture Design Document

## Project Overview

- **Project Name**: ADCDB (Antibody-Drug Conjugate Database)
- **Description**: A web database for browsing, searching, and visualizing Antibody-Drug Conjugates (ADCs) with predicted 3D structures. Provides comprehensive data on ADCs, their component molecules, and clinical/preclinical activity.
- **Target Users**: Pharmaceutical researchers, medicinal chemists, and biologists working with ADCs.

## Functional Requirements

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| FR-1 | Browse ADCs | Paginated table of all ADCs with status filter, showing antibody/antigen/linker/payload names | P0 |
| FR-2 | ADC Detail | Full ADC record with nested components, activities, and 3D structure viewer | P0 |
| FR-3 | Component Detail | Detail pages for Antibody, Antigen, Linker, Payload with linked ADC lists | P0 |
| FR-4 | 3D Structure Viewer | Mol* viewer showing predicted IgG + linker-payload assembly (PDB format) | P0 |
| FR-5 | 2D Molecule Drawing | RDKit WASM rendering of linker/payload SMILES with ACS1996 style | P0 |
| FR-6 | Text Search | Unified search across all entity names with LIKE matching | P0 |
| FR-7 | Structure Similarity | SMILES input -> Tanimoto similarity against linker/payload Morgan fingerprints | P1 |
| FR-8 | Sequence Similarity | Amino acid sequence input -> PairwiseAligner against antibody heavy/light chains | P1 |
| FR-9 | Homepage Stats | Aggregate counts: total ADCs, top antigens, top payload targets, pipeline funnel | P0 |
| FR-10 | PDB Download | Direct download of PDB structure files via API | P1 |

## Non-Functional Requirements

| # | Category | Requirement |
|---|----------|-------------|
| NFR-1 | Performance | All API responses < 500ms. No N+1 queries. Max 2 queries per endpoint. |
| NFR-2 | Data Integrity | All ORM relationships use `lazy="raise"` to prevent accidental lazy-loading. |
| NFR-3 | Security | CORS restricted to frontend origins. No authentication in V1 (read-only public DB). |
| NFR-4 | Scalability | Dataset is thousands of records, not millions. No caching layer needed. |
| NFR-5 | Availability | MariaDB in Docker with persistent volume. Backend stateless. |
| NFR-6 | Maintainability | Simple 3-tier architecture: routers -> services -> DB. No repository pattern. |

## Technology Stack

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Frontend Runtime | React | 19.2 | SPA avoids SSR conflicts with Mol* (which calls React internally) |
| Frontend Build | Vite | 8.0 | Fast HMR, native ESM |
| Frontend Styling | Tailwind CSS v4 + shadcn/ui | 4.2 | Utility-first CSS, consistent component library |
| Frontend Router | React Router | v7 | Client-side routing with `useSearchParams` for state |
| 3D Viewer | Mol* (molstar) | 5.7 | Industry-standard molecular viewer, React 18+ compatible |
| 2D Structures | @iktos-oss/rdkit-provider + molecule-representation | 2.10/1.12 | RDKit WASM for client-side SMILES -> SVG rendering |
| Backend Framework | FastAPI | 0.135+ | Async Python, auto-generated OpenAPI docs |
| Backend ORM | SQLAlchemy 2.0 (async) | 2.0.48+ | Async session support, explicit JOIN control |
| DB Driver | asyncmy | 0.2.11+ | Actively maintained async MariaDB driver |
| Database | MariaDB | 11.4 LTS | FULLTEXT indexes, JSON columns, stable LTS release |
| Migrations | Alembic | 1.18+ | SQLAlchemy-native migration tool |
| Chemistry (server) | RDKit Python | 2025.9+ | Fingerprints, conformer generation, SMILES validation |
| Biology | Biopython | 1.86+ | PairwiseAligner for sequence similarity |
| Package Mgmt (Python) | uv | latest | Fast Python package manager |
| Package Mgmt (JS) | npm | latest | Standard Node.js package manager |
| Containerization | Docker Compose | latest | MariaDB only; app runs natively |

## System Architecture

```mermaid
graph TB
    subgraph Browser
        SPA["React SPA<br/>(port 5173)"]
        MOLSTAR["Mol* 3D Viewer"]
        RDKIT_WASM["RDKit WASM<br/>(Web Worker)"]
    end

    subgraph "Backend Server"
        FASTAPI["FastAPI<br/>(port 8001)"]
        ROUTERS["Routers<br/>adcs, antibodies, antigens,<br/>linkers, payloads, search, stats"]
        SERVICES["Services<br/>chemistry_service<br/>sequence_service"]
        STRUCTURE["Structure Module<br/>conformer, assembler"]
    end

    subgraph "Data Layer"
        MARIADB["MariaDB 11.4 LTS<br/>(Docker, port 3306)"]
        PDB_FILES["PDB Files<br/>(backend/structures/)"]
    end

    subgraph "Offline Batch"
        SEED["data/seed.py"]
        ADD_LP["data/add_lp_smiles.py"]
        GEN_3D["data/generate_structures.py"]
    end

    SPA -->|"fetch /api/v1/*"| FASTAPI
    MOLSTAR -->|"fetch PDB"| FASTAPI
    FASTAPI --> ROUTERS
    ROUTERS --> SERVICES
    ROUTERS -->|"SQLAlchemy async"| MARIADB
    SERVICES -->|"SQLAlchemy async"| MARIADB
    ROUTERS -->|"FileResponse"| PDB_FILES

    SEED -->|"insert"| MARIADB
    ADD_LP -->|"update"| MARIADB
    GEN_3D -->|"read ADC, write PDB"| MARIADB
    GEN_3D -->|"RDKit conformer"| STRUCTURE
    GEN_3D -->|"save .pdb"| PDB_FILES
```

## Data Flow

### Read Path (user browsing)

```
Browser -> GET /api/v1/adcs -> FastAPI Router
  -> SQLAlchemy SELECT with JOINs (ADC + Antibody + Antigen + Linker + Payload)
  -> MariaDB
  -> Pydantic serialization -> JSON response
```

### 3D Structure Path

```
Browser -> ADCDetail page -> checks structure_3d_path != null
  -> lazy-loads MolViewer component
  -> GET /api/v1/adcs/{id}/structure -> FileResponse (PDB)
  -> Mol* parses PDB -> renders 3D
```

### Search Path (structure similarity)

```
Browser -> GET /api/v1/search/structure?smiles=...
  -> chemistry_service.search_by_structure()
  -> Convert query SMILES to Morgan FP (radius=2, nbits=2048)
  -> Load all linker/payload fingerprints from DB
  -> Compute Tanimoto similarity in Python
  -> Return sorted top-N results
```

### Offline Data Pipeline

```
1. make db          -> Docker starts MariaDB
2. make migrate     -> Alembic creates 6 tables
3. make seed        -> seed.py loads seed_data.json, computes fingerprints
4. add_lp_smiles.py -> Matches ADC names to curated linker-payload SMILES
5. make structures  -> generate_structures.py builds PDB files via RDKit + template IgG
```

## Directory Structure

```
adcdb/
├── CLAUDE.md                     # Project instructions
├── Makefile                      # Build/run commands
├── docker-compose.yml            # MariaDB 11.4 container
├── plans/                        # Agent planning docs
│   ├── index.md                  # Overview + API contract
│   ├── backend.md                # Backend implementation guide
│   ├── frontend.md               # Frontend implementation guide
│   └── data.md                   # Data schema + pipeline guide
├── _workspace/                   # Architecture design docs (this directory)
│   ├── 01_architecture.md
│   ├── 02_api_spec.md
│   └── 03_db_schema.md
├── backend/
│   ├── pyproject.toml            # Python deps (uv)
│   ├── alembic/
│   │   ├── env.py                # Async migration runner
│   │   └── versions/
│   │       └── db45559cbb4e_initial_tables.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app + CORS + router registration
│   │   ├── config.py             # pydantic-settings (DATABASE_URL, CORS, PORT, STRUCTURES_DIR)
│   │   ├── database.py           # async engine + session factory + Base
│   │   ├── models/
│   │   │   ├── __init__.py       # Re-exports all models
│   │   │   ├── antigen.py        # No FKs
│   │   │   ├── linker.py         # No FKs, has morgan_fp
│   │   │   ├── payload.py        # No FKs, has morgan_fp
│   │   │   ├── antibody.py       # FK -> antigen
│   │   │   ├── adc.py            # FKs -> antibody, linker, payload
│   │   │   └── activity.py       # FK -> adc (CASCADE)
│   │   ├── schemas/
│   │   │   ├── __init__.py       # Empty
│   │   │   ├── antigen.py        # AntigenBase, AntigenCreate, AntigenRead
│   │   │   ├── antibody.py       # Nests AntigenRead
│   │   │   ├── linker.py
│   │   │   ├── payload.py
│   │   │   ├── activity.py
│   │   │   └── adc.py            # ADCRead (nested), ADCListItem (flat)
│   │   ├── routers/
│   │   │   ├── __init__.py       # Empty
│   │   │   ├── adcs.py           # list, detail, structure, create
│   │   │   ├── antibodies.py     # list, detail, linked ADCs
│   │   │   ├── antigens.py       # list, detail, linked ADCs
│   │   │   ├── linkers.py        # list, detail, linked ADCs
│   │   │   ├── payloads.py       # list, detail, linked ADCs
│   │   │   ├── search.py         # text, structure, sequence
│   │   │   └── stats.py          # Homepage aggregates
│   │   ├── services/
│   │   │   ├── __init__.py       # Empty
│   │   │   ├── chemistry_service.py  # Morgan FP Tanimoto search
│   │   │   └── sequence_service.py   # Biopython PairwiseAligner
│   │   └── structure/
│   │       ├── __init__.py       # Empty
│   │       ├── conformer.py      # RDKit ETKDGv3 conformer generation
│   │       └── assembler.py      # IgG template + LP placement
│   └── structures/               # Generated PDB files ({adc_id}.pdb)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts            # @tailwindcss/vite, path alias @/ -> src/
│   ├── tsconfig.app.json         # paths: @/* -> ./src/*
│   ├── index.html
│   ├── public/                   # RDKit WASM files (copied from node_modules)
│   └── src/
│       ├── main.tsx              # createRoot + BrowserRouter
│       ├── App.tsx               # RDKitProvider + Routes
│       ├── globals.css           # Blue theme HSL vars + Geist font
│       ├── lib/
│       │   ├── api.ts            # apiFetch + all TypeScript interfaces
│       │   └── utils.ts          # cn() (clsx + tailwind-merge)
│       ├── components/
│       │   ├── Layout.tsx        # Nav + Outlet + footer
│       │   ├── MolViewer.tsx     # Mol* 3D viewer (lazy-loaded)
│       │   └── MoleculeDrawing.tsx  # RDKit WASM 2D (ACS1996 style)
│       ├── pages/
│       │   ├── Home.tsx          # Stats dashboard
│       │   ├── Browse.tsx        # ADC table with status filter
│       │   ├── Search.tsx        # 3-tab search (text/structure/sequence)
│       │   ├── ADCDetail.tsx     # Full ADC + 3D viewer + activities
│       │   ├── AntibodyDetail.tsx
│       │   ├── AntigenDetail.tsx
│       │   ├── LinkerDetail.tsx  # Includes MoleculeDrawing
│       │   ├── PayloadDetail.tsx # Includes MoleculeDrawing (skips "C" placeholder)
│       │   ├── About.tsx
│       │   └── NotFound.tsx
│       └── fonts/
│           └── GeistVF.woff
└── data/
    ├── seed.py                   # DB seeder with RDKit validation
    ├── add_lp_smiles.py          # Add curated linker-payload SMILES
    ├── generate_structures.py    # Batch 3D PDB generation
    └── sources/
        └── seed_data.json        # Curated ~50 ADCs
```

## Key Design Decisions

### 1. SPA over SSR

**Decision**: Plain React + Vite SPA, no Next.js.

**Rationale**: Mol* v5 calls React internally. Next.js SSR creates a React runtime conflict (`render is not a function`). A single-runtime SPA avoids this entirely.

**Trade-off**: No SSR means no SEO benefits, but this is an internal research tool, not a public-facing site.

### 2. lazy="raise" on all ORM relationships

**Decision**: Every SQLAlchemy relationship uses `lazy="raise"`.

**Rationale**: Prevents accidental N+1 queries at development time. Any unloaded relationship access throws immediately instead of silently issuing a SQL query.

**Trade-off**: Requires explicit `joinedload()` or `selectinload()` in every query that needs related data. This is intentional -- every JOIN is visible and auditable.

### 3. UUIDv7 primary keys

**Decision**: All PKs are `String(36)` with UUIDv7 default.

**Rationale**: UUIDv7 (RFC 9562) embeds a timestamp, so B-tree inserts are sequential (no random-write fragmentation). Globally unique without a central sequence.

**Trade-off**: 36-byte string PKs are larger than auto-increment integers. Acceptable for this dataset size.

### 4. File-based PDB storage

**Decision**: PDB files stored on disk at `backend/structures/{adc_id}.pdb`, path recorded in DB.

**Rationale**: PDB files are text (10-100KB each). Serving via `FileResponse` is simpler and more efficient than storing BLOBs in the DB.

**Trade-off**: Requires filesystem access. Not suitable for serverless deployment without an object store.

### 5. In-process fingerprint search

**Decision**: Tanimoto similarity computed in Python by loading all fingerprints from DB and comparing in-memory.

**Rationale**: With ~20 linkers and ~10 payloads, loading all fingerprints is trivial. No need for a chemical cartridge (e.g., RDKit PostgreSQL extension).

**Trade-off**: Will not scale beyond a few thousand molecules. If the dataset grows significantly, consider a dedicated chemical search engine.

### 6. Curated linker_payload_smiles

**Decision**: The pre-connected linker-payload molecule is stored as curated data on the ADC record, not computed from separate linker + payload SMILES.

**Rationale**: The coupling reaction (e.g., PABC carbamate with MMAE's amine) varies by chemistry and cannot be reliably automated.

### 7. Template-based IgG structures

**Decision**: 3D structures use an approximate IgG Y-shaped template with linker-payload conformers placed at conjugation sites.

**Rationale**: Full antibody structure prediction (AlphaFold, ESMFold) produces single chains, not the IgG tetramer. Template superposition is simpler and sufficient for visualization.

**Trade-off**: Structures are approximate topology only, not suitable for quantitative analysis.

## Implementation Status vs. Plan

| Component | Plan Status | Implementation Status | Notes |
|-----------|-------------|----------------------|-------|
| ORM Models (6 tables) | Specified | COMPLETE | All models match spec exactly |
| Alembic Migration | Specified | COMPLETE | Single migration creates all tables |
| Pydantic Schemas | Specified | COMPLETE | All schemas with nested relations |
| ADC Router | Specified | COMPLETE | list, detail, structure, create |
| Antibody Router | Specified | COMPLETE | list, detail, linked ADCs |
| Antigen Router | Specified | COMPLETE | list, detail, linked ADCs |
| Linker Router | Specified | COMPLETE | list, detail, linked ADCs |
| Payload Router | Specified | COMPLETE | list, detail, linked ADCs |
| Search Router | Specified | COMPLETE | text, structure, sequence |
| Stats Router | Specified | COMPLETE | top antigens, targets, pipeline |
| Chemistry Service | Specified | COMPLETE | Morgan FP Tanimoto |
| Sequence Service | Specified | COMPLETE | Biopython PairwiseAligner |
| Structure Module | Specified | COMPLETE | Conformer + assembler |
| Frontend Pages | Specified | COMPLETE | All 10 pages implemented |
| MolViewer | Specified | COMPLETE | Mol* with React 18 render |
| MoleculeDrawing | Specified | COMPLETE | ACS1996 style |
| Seed Script | Specified | COMPLETE | With RDKit validation |
| LP SMILES Script | Specified | COMPLETE | Pattern-matched updates |
| Structure Gen Script | Specified | COMPLETE | Batch PDB generation |

### Observations and Minor Gaps

1. **React version**: `package.json` shows React 19.2, while the plan says React 18. This is fine -- Mol* and all dependencies are compatible. The `createRoot` render callback pattern still works.

2. **Text search uses LIKE, not FULLTEXT**: The search router and list endpoints use `LIKE '%term%'` instead of `MATCH ... AGAINST`. FULLTEXT indexes are created but unused in queries. LIKE with leading wildcard cannot use the FULLTEXT index. This is a known simplification -- FULLTEXT `MATCH ... AGAINST` in boolean mode would be more efficient for larger datasets but LIKE works fine at current scale.

3. **No add_lp_smiles.py in Makefile**: The `add_lp_smiles.py` script is not wired into `make setup`. It must be run manually after seeding. This may mean seed_data.json already contains `linker_payload_smiles` for some ADCs, with `add_lp_smiles.py` filling in the rest.

4. **ADC create endpoint exists but is not in the plan**: `POST /api/v1/adcs` is implemented in the adcs router but not listed in the API contract. This is a reasonable addition for programmatic data entry.

5. **Unused imports**: `AntigenCreate` in antigens router and `AntibodyCreate` in antibodies router are imported but never used (no POST endpoints for those entities).

## Handoff Notes for Frontend

- **API base URL**: `import.meta.env.VITE_API_URL` defaults to `http://localhost:8001/api/v1`
- **All TypeScript interfaces** are in `src/lib/api.ts` and match the Pydantic schemas exactly
- **Mol* is lazy-loaded** via `React.lazy()` + `Suspense` -- only loaded on ADCDetail page
- **MoleculeDrawing** cleans `[*:n]` attachment points to `[H]` before rendering
- **PayloadDetail** skips 2D drawing when SMILES is `"C"` (placeholder)
- **State management**: URL params via `useSearchParams` for Browse filters; React state for everything else
- **No shadcn/ui components directory**: The UI is built with raw Tailwind CSS classes following shadcn design patterns (border-border, bg-muted, text-primary, etc.) but no `components/ui/` primitives are installed yet

## Handoff Notes for Backend

- **All queries use explicit JOINs** -- never traverse ORM relationships lazily
- **ADCListItem** is a flat Pydantic model constructed from column-level `select()`, not from ORM objects
- **ADCRead** uses `joinedload()` for nested serialization
- **Fingerprint storage**: Morgan FP stored as bit string bytes (`"01001..."` encoded to bytes), reconstructed via `fp_from_stored_bytes()`
- **Config**: All settings via `ADCDB_` env prefix (e.g., `ADCDB_DATABASE_URL`)
- **ON DELETE RESTRICT** on Antibody, Linker, Payload FKs; **ON DELETE CASCADE** on ADCActivity

## Handoff Notes for QA

- **Verify N+1 prevention**: Enable SQLAlchemy `echo=True` and confirm each endpoint fires at most 2 SQL statements
- **Test SMILES edge cases**: Empty SMILES, `"C"` placeholder, SMILES with `[*:1]`/`[*:2]` attachment points
- **Test null structure_3d_path**: ADCDetail should show "not yet available" message, not crash
- **Test pagination**: `page` and `per_page` params on all list endpoints
- **Test 404s**: Invalid UUIDs should return 404, not 500

## Handoff Notes for DevOps

- **Docker**: Only MariaDB runs in Docker. Backend and frontend run natively.
- **Environment variables**:
  - `ADCDB_DATABASE_URL` (default: `mysql+asyncmy://adcdb:adcdb_pass@127.0.0.1:3306/adcdb`)
  - `ADCDB_CORS_ORIGINS` (default: `["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]`)
  - `ADCDB_PORT` (default: `8001`)
  - `ADCDB_STRUCTURES_DIR` (default: `structures`)
  - `VITE_API_URL` (frontend, default: `http://localhost:8001/api/v1`)
- **Ports**: Backend 8001, Frontend 5173, MariaDB 3306
- **Persistent volume**: `adcdb-mariadb-data` for MariaDB data
- **Setup sequence**: `make setup` runs db -> migrate -> seed -> structures
