# ADCDB — Antibody-Drug Conjugate Database

## What This Is

A web database for browsing, searching, and visualizing Antibody-Drug Conjugates (ADCs).
Similar to [adcdb.idrblab.net](https://adcdb.idrblab.net/) with one addition: **3D predicted structures of the full ADC conjugate**.

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **FastAPI** (Python 3.12) | Async, fast, easy ORM integration |
| Database | **MariaDB 11.4 LTS** | Relational data, stable long-term support |
| Frontend | **React 18 + Vite + shadcn/ui** (blue theme) | SPA, React Router, no SSR conflicts with Mol* |
| 3D Viewer | **Mol\*** (molstar) | Industry standard, handles large PDB/mmCIF |
| Chemistry | **RDKit** (server-side) | SMILES rendering, similarity search, molecular properties |
| Search | **MariaDB full-text + LIKE/COLLATE** | Good enough. No Elasticsearch needed. |

## Data Model

Six tables. ADC is the hub, Antibody owns the Antigen relationship.

```
Antigen ── Antibody ──┐
                      ├── ADC ── ADCActivity
Linker ───────────────┤
                      │
Payload ──────────────┘
```

**N+1 note:** ADC reaches Antigen via `ADC → Antibody → Antigen` (2 hops). All endpoints — forward (ADC lists) and reverse (component detail → linked ADCs) — must use explicit JOINs, never lazy-load. Set `lazy="raise"` on all ORM relationships. Every endpoint is analyzed with exact queries in ARCHITECTURE.md.

**V1 limitation:** Antibody → Antigen is N:1. Bispecific antibodies (e.g. amivantamab targeting EGFR+MET) cannot be represented. This is a known simplification. If bispecific ADCs become a priority, replace with a junction table (`antibody_antigen`).

### ADC
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK, time-sorted to avoid B-tree fragmentation |
| name | str | e.g. "Trastuzumab deruxtecan", UNIQUE |
| brand_name | str | nullable, e.g. "Enhertu" |
| synonyms | JSON | |
| organization | str | developer/company |
| status | enum | approved / phase_3 / phase_2 / phase_1 / investigative |
| dar | float | Drug-to-Antibody Ratio (average) |
| conjugation_site | enum | cysteine / lysine / engineered_cysteine / engineered_other |
| indications | JSON | disease targets |
| antibody_id | FK → Antibody | ON DELETE RESTRICT |
| linker_id | FK → Linker | ON DELETE RESTRICT |
| payload_id | FK → Payload | ON DELETE RESTRICT |
| linker_payload_smiles | str | pre-connected linker+payload molecule, `[*:1]` = Ab attachment point |
| structure_3d_path | str | nullable; path to predicted PDB file, NULL if generation failed |
| created_at | datetime | |
| updated_at | datetime | |

### Antibody
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK |
| name | str | e.g. "Trastuzumab", UNIQUE |
| synonyms | JSON | |
| isotype | str | e.g. "IgG1", "IgG4" — immunoglobulin class/subclass |
| origin | enum | chimeric / humanized / human / murine |
| antigen_id | FK → Antigen | ON DELETE RESTRICT |
| heavy_chain_seq | text | amino acid sequence (single chain) |
| light_chain_seq | text | amino acid sequence (single chain) |
| uniprot_id | str | external link |

### Antigen
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK |
| name | str | e.g. "HER2", UNIQUE |
| synonyms | JSON | |
| gene_name | str | e.g. "ERBB2" |
| uniprot_id | str | |
| description | text | |

### Linker
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK |
| name | str | e.g. "MC-Val-Cit-PABC", UNIQUE |
| cleavable | bool | true = cleavable, false = non-cleavable |
| cleavage_mechanism | str | nullable; protease / acid_labile / disulfide_reduction / photo |
| coupling_chemistry | str | maleimide / nhs_ester / click / sortase / transglutaminase |
| smiles | str | with attachment points: `[*:1]` (Ab end), `[*:2]` (payload end) |
| inchi | str | nullable — invalid when SMILES has attachment points |
| inchikey | str | nullable, UNIQUE when present |
| formula | str | molecular formula |
| iupac_name | str | |
| mol_weight | float | computed via RDKit |
| morgan_fp | binary | Morgan fingerprint, radius=2, nbits=2048 |

### Payload
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK |
| name | str | e.g. "MMAE", UNIQUE |
| synonyms | JSON | |
| target | str | e.g. "Microtubule" — intracellular target |
| moa | str | Mechanism of Action |
| bystander_effect | bool | can released payload kill antigen-negative neighboring cells? |
| smiles | str | |
| inchi | str | |
| inchikey | str | UNIQUE |
| formula | str | |
| iupac_name | str | |
| mol_weight | float | |
| morgan_fp | binary | Morgan fingerprint, radius=2, nbits=2048 |

### ADCActivity (clinical/preclinical data per ADC)
| Field | Type | Notes |
|-------|------|-------|
| id | UUIDv7 | PK |
| adc_id | FK → ADC | ON DELETE CASCADE |
| activity_type | enum | clinical_trial / in_vivo / in_vitro |
| nct_number | str | for clinical trials |
| phase | str | |
| orr | float | Objective Response Rate (%) |
| model | str | for in_vivo (xenograft type) |
| tgi | float | Tumor Growth Inhibition (%) |
| ic50_value | float | for in_vitro |
| ic50_unit | str | nM, μM, etc. |
| cell_line | str | |
| notes | text | |

## Pages

| Route | What It Shows |
|-------|---------------|
| `/` | Landing: search bar, stats (top antigens, top payloads, pipeline funnel) |
| `/search` | Unified search with tabs: ADC / Antibody / Antigen / Payload / Linker |
| `/adc/:id` | ADC detail: all fields, linked entities, activity data, **3D viewer** |
| `/antibody/:id` | Antibody detail: sequences, linked ADCs |
| `/antigen/:id` | Antigen detail: gene info, linked ADCs |
| `/linker/:id` | Linker detail: 2D structure (SMILES render), properties |
| `/payload/:id` | Payload detail: 2D structure, MOA, properties |
| `/browse` | Browse by status, antigen, payload target — filterable table |
| `/about` | Citations, data sources, contact |

## API Endpoints

```
GET  /api/v1/adcs                  # list + filter + paginate
GET  /api/v1/adcs/{id}             # detail
GET  /api/v1/adcs/{id}/structure   # serve 3D structure file
GET  /api/v1/antibodies            # list
GET  /api/v1/antibodies/{id}       # detail
GET  /api/v1/antibodies/{id}/adcs  # linked ADCs for this antibody
GET  /api/v1/antigens              # list
GET  /api/v1/antigens/{id}         # detail
GET  /api/v1/antigens/{id}/adcs    # linked ADCs (reverse 2-hop via antibody)
GET  /api/v1/linkers               # list
GET  /api/v1/linkers/{id}          # detail
GET  /api/v1/linkers/{id}/adcs     # linked ADCs for this linker
GET  /api/v1/payloads              # list
GET  /api/v1/payloads/{id}         # detail
GET  /api/v1/payloads/{id}/adcs    # linked ADCs for this payload
GET  /api/v1/search                # unified text search across all entities
GET  /api/v1/search/structure      # SMILES similarity search (RDKit)
GET  /api/v1/search/sequence       # sequence similarity (BLAST or simple alignment)
GET  /api/v1/stats                 # aggregate counts for homepage charts
```

## 3D Structure Feature (the differentiator)

**What:** For each ADC, we store a predicted 3D structure of the full conjugate — antibody + linker + payload assembled.

**How to generate:**
1. **Full IgG structure:** AlphaFold DB and ESMFold predict single chains, not the IgG tetramer. Use a **template-based approach**: take an experimental IgG crystal structure (e.g., PDB 1HZH) and superpose the specific antibody's heavy/light chain sequences onto it using sequence alignment + backbone fitting. This gives a full 2H+2L tetramer adequate for reference visualization. Fall back to ESMFold single-chain prediction only if template fitting fails.
2. **Linker-payload conformer:** The ADC table stores a `linker_payload_smiles` field — the pre-connected linker-payload molecule with `[*:1]` marking the antibody attachment atom. This avoids computationally simulating the linker-payload coupling reaction. Generate 3D conformer: record the atom index of `[*:1]`, replace `[*:1]` with `[H]`, embed with `AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())`, minimize with `AllChem.MMFFOptimizeMolecule(mol)`. The recorded atom index becomes the attachment point for step 4.
3. **Identify conjugation sites on antibody:**
   - Cysteine: locate interchain disulfide Cys residues (typically C220, C226, C229 in IgG1 by EU numbering). Parse the PDB, find S-S bonds between heavy-heavy or heavy-light chains.
   - Lysine: identify surface-exposed Lys residues (solvent-accessible surface area > threshold via `FreeSASA` or BioPython).
   - Engineered: use the known engineered residue position from literature.
4. **Attach:** Place linker-payload conformer at each conjugation site (number of copies = DAR). Orient the `[*:1]` attachment atom toward the target residue's side-chain terminus. This is approximate rigid-body placement, not covalent docking. Combine into a single PDB: antibody chains as ATOM records, each linker-payload unit as HETATM records.
5. **Save as `.pdb`** with chain IDs: H/h (heavy pair), L/l (light pair), D1/D2/.../Dn (drug-linker units). Store path in `adc.structure_3d_path`.
6. **Graceful failure:** If any step fails (antibody not in AlphaFold DB, conformer embedding fails, conjugation site unresolvable), set `structure_3d_path = NULL`, log the error, continue to the next ADC. Do not block the batch.

**Viewer:** Mol* embedded in the ADC detail page. Shows antibody as cartoon, linker-payload as ball-and-stick, colored by component. Label: "Predicted/modeled structure — approximate spatial arrangement."

## Project Structure

```
adcdb/
├── backend/
│   ├── pyproject.toml
│   ├── alembic/              # DB migrations
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORSMiddleware
│   │   ├── config.py         # settings
│   │   ├── database.py       # SQLAlchemy async engine + session
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
│   ├── index.html            # Vite entry point
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json       # shadcn config (blue theme, rsc: false)
│   ├── src/
│   │   ├── main.tsx          # React createRoot entry
│   │   ├── App.tsx           # BrowserRouter + Routes + Layout
│   │   ├── globals.css       # Blue theme CSS vars + @font-face
│   │   ├── pages/            # Route components
│   │   ├── components/       # UI components
│   │   │   ├── ui/           # shadcn primitives
│   │   │   ├── MolViewer.tsx # Mol* createPluginUI (lazy-loaded)
│   │   │   ├── Layout.tsx    # Nav + footer shell
│   │   │   └── ErrorBoundary.tsx
│   │   └── lib/              # API client, utils
│   └── public/
└── data/                     # seed data, scripts
    ├── seed.py               # populate DB from curated sources
    └── sources/              # raw data files
```

## Implementation Order

1. **Backend skeleton** — FastAPI app with CORSMiddleware, DB models with unique constraints and ON DELETE, Alembic, basic CRUD endpoints
2. **Seed data** — Script to populate a small dataset (~50 ADCs) with validation: SMILES parseable by RDKit, sequences are valid amino acids, InChIKey matches SMILES where provided
3. **Frontend skeleton** — React + Vite + shadcn/ui (blue), React Router, layout
4. **Search + Browse** — Full-text search, filterable tables
5. **Detail pages** — Entity detail views with linked data
6. **Homepage stats** — Charts (recharts or chart.js via shadcn charts)
7. **3D structure pipeline** — Conformer generation, site identification, assembly, Mol* viewer
8. **Structure similarity search** — SMILES-based fingerprint search via RDKit (radius=2, 2048 bits)
9. **Sequence similarity search** — Basic BLAST or Biopython pairwise alignment
10. **Polish** — Responsive design, loading states, error handling
