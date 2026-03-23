# ADCDB — Antibody-Drug Conjugate Database

## What This Is

A web database for browsing, searching, and visualizing Antibody-Drug Conjugates (ADCs).
Similar to [adcdb.idrblab.net](https://adcdb.idrblab.net/) with one addition: **3D predicted structures of the full ADC conjugate**.

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **FastAPI** (Python 3.12) | Async, fast, easy ORM integration |
| Database | **MariaDB 11.4 LTS** | Relational data, stable long-term support |
| Frontend | **Next.js 14 + shadcn/ui** (blue theme) | App router, server components, clean UI |
| 3D Viewer | **Mol\*** (molstar) | Industry standard, handles large PDB/mmCIF |
| Chemistry | **RDKit** (server-side) | SMILES rendering, similarity search, molecular properties |
| Search | **MariaDB full-text + LIKE/COLLATE** | Good enough. No Elasticsearch needed. |

## Data Model

Six tables. ADC is the hub, Antibody owns the Antigen relationship.

```
Antigen ── Antibody ──┐
                      ├── ADC
Linker ───────────────┤
                      │
Payload ──────────────┘
```

**N+1 note:** ADC reaches Antigen via `ADC → Antibody → Antigen` (2 hops). All endpoints — forward (ADC lists) and reverse (component detail → linked ADCs) — must use explicit JOINs, never lazy-load. Set `lazy="raise"` on all ORM relationships. Every endpoint is analyzed with exact queries in ARCHITECTURE.md.

### ADC
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | str | e.g. "Trastuzumab deruxtecan" |
| brand_name | str | nullable, e.g. "Enhertu" |
| synonyms | JSON | |
| organization | str | developer/company |
| status | enum | Approved / Phase 3 / Phase 2 / Phase 1 / Investigative |
| dar | float | Drug-to-Antibody Ratio |
| conjugation_type | enum | cysteine / lysine / site_specific |
| indications | JSON | disease targets |
| antibody_id | FK → Antibody | |
| linker_id | FK → Linker | |
| payload_id | FK → Payload | |
| structure_3d_path | str | path to predicted PDB/mmCIF file |
| created_at | datetime | |
| updated_at | datetime | |

### Antibody
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | str | e.g. "Trastuzumab" |
| synonyms | JSON | |
| type | str | e.g. "IgG1" |
| subtype | enum | chimeric / humanized / human / murine |
| antigen_id | FK → Antigen | the target this antibody binds (e.g. Trastuzumab → HER2) |
| heavy_chain_seq | text | amino acid sequence |
| light_chain_seq | text | amino acid sequence |
| uniprot_id | str | external link |

### Antigen
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | str | e.g. "HER2" |
| synonyms | JSON | |
| gene_name | str | e.g. "ERBB2" |
| uniprot_id | str | |
| description | text | |

### Linker
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | str | e.g. "Mal-PEG4-Val-Cit-PABC" |
| type | enum | cleavable / non_cleavable |
| smiles | str | |
| inchi | str | |
| inchikey | str | |
| formula | str | molecular formula |
| iupac_name | str | |
| mol_weight | float | computed via RDKit |
| morgan_fp | binary | pre-computed Morgan fingerprint for similarity search |

### Payload
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | str | e.g. "MMAE" |
| synonyms | JSON | |
| target | str | e.g. "Microtubule" |
| moa | str | Mechanism of Action |
| smiles | str | |
| inchi | str | |
| inchikey | str | |
| formula | str | |
| iupac_name | str | |
| mol_weight | float | |
| morgan_fp | binary | pre-computed Morgan fingerprint for similarity search |

### ADCActivity (clinical/preclinical data per ADC)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| adc_id | FK → ADC | |
| activity_type | enum | clinical_trial / in_vivo / in_vitro |
| nct_number | str | for clinical trials |
| phase | str | |
| orr | float | Objective Response Rate |
| model | str | for in_vivo (xenograft type) |
| tgi | float | Tumor Growth Inhibition |
| ic50 | float | for in_vitro |
| cell_line | str | |
| notes | text | |

## Pages

| Route | What It Shows |
|-------|---------------|
| `/` | Landing: search bar, stats (top antigens, top payloads, pipeline funnel) |
| `/search` | Unified search with tabs: ADC / Antibody / Antigen / Payload / Linker |
| `/adc/[id]` | ADC detail: all fields, linked entities, activity data, **3D viewer** |
| `/antibody/[id]` | Antibody detail: sequences, linked ADCs |
| `/antigen/[id]` | Antigen detail: gene info, linked ADCs |
| `/linker/[id]` | Linker detail: 2D structure (SMILES render), properties |
| `/payload/[id]` | Payload detail: 2D structure, MOA, properties |
| `/browse` | Browse by status, antigen, payload target — filterable table |
| `/about` | Citations, data sources, contact |

## API Endpoints

```
GET  /api/v1/adcs                  # list + filter + paginate
GET  /api/v1/adcs/{id}             # detail
GET  /api/v1/adcs/{id}/structure   # serve 3D structure file
GET  /api/v1/antibodies            # list
GET  /api/v1/antibodies/{id}       # detail
GET  /api/v1/antigens              # list
GET  /api/v1/antigens/{id}         # detail
GET  /api/v1/linkers               # list
GET  /api/v1/linkers/{id}          # detail
GET  /api/v1/payloads              # list
GET  /api/v1/payloads/{id}         # detail
GET  /api/v1/search                # unified text search across all entities
GET  /api/v1/search/structure      # SMILES similarity search (RDKit)
GET  /api/v1/search/sequence       # sequence similarity (BLAST or simple alignment)
GET  /api/v1/stats                 # aggregate counts for homepage charts
```

## 3D Structure Feature (the differentiator)

**What:** For each ADC, we store a predicted 3D structure of the full conjugate — antibody + linker + payload assembled.

**How to generate:**
1. Antibody structure from **AlphaFold2** or **ESMFold** (or fetch from AlphaFold DB if available)
2. Linker + payload 3D conformer from **RDKit** (`AllChem.EmbedMolecule`)
3. Conjugation site attachment modeled based on known chemistry (e.g., Cys residues for maleimide linkers, Lys for NHS-ester)
4. Store as `.pdb` or `.mmcif` files on disk (or S3)

**Viewer:** Mol* embedded in the ADC detail page. Shows antibody as cartoon, linker-payload as ball-and-stick, colored by component.

**Pragmatic note:** Perfect atomic accuracy is not the goal. This is a *reference visualization* — good enough to show spatial relationship of components. We label it as "predicted/modeled" structure.

## Project Structure

```
adcdb/
├── backend/
│   ├── pyproject.toml
│   ├── alembic/              # DB migrations
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # settings
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── adc.py
│   │   │   ├── antibody.py
│   │   │   ├── antigen.py
│   │   │   ├── linker.py
│   │   │   ├── payload.py
│   │   │   └── activity.py
│   │   ├── schemas/          # Pydantic request/response
│   │   ├── routers/          # endpoint groups
│   │   ├── services/         # business logic (search, chem)
│   │   └── structure/        # 3D structure generation utils
│   └── structures/           # generated PDB/mmCIF storage
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── components.json       # shadcn config (blue theme)
│   ├── src/
│   │   ├── app/              # Next.js app router pages
│   │   ├── components/       # UI components
│   │   │   ├── ui/           # shadcn primitives
│   │   │   ├── mol-viewer.tsx    # Mol* wrapper
│   │   │   ├── search-bar.tsx
│   │   │   ├── stats-charts.tsx
│   │   │   └── entity-table.tsx
│   │   └── lib/              # API client, utils
│   └── public/
└── data/                     # seed data, scripts
    ├── seed.py               # populate DB from curated sources
    └── sources/              # raw data files
```

## Implementation Order

1. **Backend skeleton** — FastAPI app, DB models, Alembic, basic CRUD endpoints
2. **Seed data** — Script to populate a small dataset (~50 ADCs) for development
3. **Frontend skeleton** — Next.js + shadcn/ui setup (blue), layout, routing
4. **Search + Browse** — Full-text search, filterable tables
5. **Detail pages** — Entity detail views with linked data
6. **Homepage stats** — Charts (recharts or chart.js via shadcn charts)
7. **3D structure pipeline** — RDKit conformer generation, Mol* viewer integration
8. **Structure similarity search** — SMILES-based fingerprint search via RDKit
9. **Sequence similarity search** — Basic BLAST or Biopython pairwise alignment
10. **Polish** — Responsive design, loading states, error handling
