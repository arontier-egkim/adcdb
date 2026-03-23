# Data Agent — Schema, Seeding, 3D Pipeline

## Execution Steps

1. **Ensure MariaDB is running and migrations applied:** `docker compose up -d` then `cd backend && uv run alembic upgrade head`. Verify tables: `docker exec adcdb-mariadb mariadb -u adcdb -padcdb_pass adcdb -e "SHOW TABLES;"` — should show 6 tables + `alembic_version`.
2. **Create seed data directory:** `mkdir -p data/sources`
3. **Create `data/sources/seed_data.json`:** Curated JSON with ~50 ADCs. Structure:
   - `antigens[]` — name, gene_name, uniprot_id, description (~16 entries)
   - `payloads[]` — name, synonyms, target, moa, bystander_effect, smiles, formula, mol_weight (~10)
   - `linkers[]` — name, cleavable, cleavage_mechanism, coupling_chemistry, smiles (with `[*:1]`/`[*:2]`), formula (~10)
   - `antibodies[]` — name, isotype, origin, antigen (name reference), uniprot_id (~20)
   - `adcs[]` — name, brand_name, synonyms, organization, status, dar, conjugation_site, indications, antibody/linker/payload (name references) (~50)
   - `activities[]` — adc (name reference), activity_type, nct_number, phase, orr, ic50_value, ic50_unit, cell_line, tgi, model (~20)
4. **Create `data/seed.py`:** Script that reads `seed_data.json` and inserts in FK order: Antigens → Linkers → Payloads → Antibodies → ADCs → Activities. For each row:
   - Validate SMILES with `Chem.MolFromSmiles()` (replace `[*:n]` with `[H]` for validation)
   - Compute Morgan fingerprint (radius=2, nbits=2048) for linkers and payloads
   - Compute mol_weight via RDKit `Descriptors.ExactMolWt` if not provided
   - Build name→ID maps for FK resolution
   - Log warnings for invalid rows, don't block the batch
5. **Run seed:** `cd backend && uv run python ../data/seed.py`. Verify: `curl http://localhost:8001/api/v1/stats` shows `total_adcs: 49`.
6. **Create `data/add_lp_smiles.py`:** Script to add `linker_payload_smiles` to ADCs. Define pre-connected SMILES for known linker+payload combos (vedotin = MC-VC-PABC+MMAE, deruxtecan = MC-GGFG-AM+DXd, etc.) with `[*:1]` marking antibody attachment. Match ADCs by name pattern.
7. **Run LP SMILES script:** `cd backend && uv run python ../data/add_lp_smiles.py`. Verify: should update ~32 ADCs.
8. **Create `data/generate_structures.py`:** Batch script that for each ADC with `linker_payload_smiles` and no `structure_3d_path`:
   - Generate linker-payload 3D conformer (RDKit ETKDGv3 + MMFF94 minimization)
   - Generate approximate IgG template antibody
   - Place DAR copies at conjugation sites
   - Save combined PDB to `backend/structures/{adc_id}.pdb`
   - Update `structure_3d_path` in DB
   - On failure: set `structure_3d_path = NULL`, log error, continue
9. **Run structure generation:** `cd backend && uv run python ../data/generate_structures.py`. Verify: should generate ~32 PDB files.
10. **Final verification:**
    - `curl http://localhost:8001/api/v1/stats` — shows correct counts
    - `curl http://localhost:8001/api/v1/adcs?per_page=3` — returns ADC list items
    - `curl http://localhost:8001/api/v1/adcs/{id}/structure` — returns PDB content

## ER Diagram

```
                          ┌───────────────────┐
┌──────────────┐          │       ADC         │
│   Antigen    │          │───────────────────│
│──────────────│          │ id          UUIDv7│
│ id     UUIDv7│◀──┐      │ name        UNIQUE│
│ name   UNIQUE│   │      │ brand_name        │
│ synonyms JSON│   │      │ synonyms JSON     │
│ gene_name    │   │      │ organization      │
│ uniprot_id   │   │      │ status            │
│ description  │   │      │ dar               │
└──────────────┘   │      │ conjugation_site  │
                   │      │ indications JSON  │
┌──────────────┐   │      │ antibody_id    FK │──┐
│   Antibody   │   │      │ linker_id      FK │──┼──┐
│──────────────│   │      │ payload_id     FK │──┼──┼──┐
│ id     UUIDv7│◀──┼──────│                   │  │  │  │
│ name   UNIQUE│   │      │ linker_payload_smi│  │  │  │
│ synonyms JSON│   │      │ structure_3d_path*│  │  │  │
│ isotype      │   │      │ created_at        │  │  │  │
│ origin       │   │      │ updated_at        │  │  │  │
│ antigen_id FK│───┘      └───────────────────┘  │  │  │
│ heavy_chain  │                   │ 1:N         │  │  │
│ light_chain  │                   ▼             │  │  │
│ uniprot_id   │          ┌───────────────────┐  │  │  │
└──────────────┘          │  ADCActivity      │  │  │  │
                          │───────────────────│  │  │  │
                          │ id          UUIDv7│  │  │  │
                          │ adc_id         FK │  │  │  │
                          │ activity_type     │  │  │  │
                          │ nct_number        │  │  │  │
                          │ phase             │  │  │  │
                          │ orr               │  │  │  │
                          │ model             │  │  │  │
                          │ tgi               │  │  │  │
                          │ ic50_value        │  │  │  │
                          │ ic50_unit         │  │  │  │
                          │ cell_line         │  │  │  │
                          │ notes             │  │  │  │
                          └───────────────────┘  │  │  │
                                                 │  │  │
┌──────────────────┐                             │  │  │
│    Linker        │                             │  │  │
│──────────────────│                             │  │  │
│ id         UUIDv7│◀────────────────────────────┘  │  │
│ name       UNIQUE│                                │  │
│ cleavable        │   ┌──────────────────┐         │  │
│ cleavage_mech    │   │   Payload        │         │  │
│ coupling_chem    │   │──────────────────│         │  │
│ smiles           │   │ id         UUIDv7│◀────────┘  │
│ inchi            │   │ name       UNIQUE│            │
│ inchikey  UNIQUE*│   │ synonyms JSON   │            │
│ formula          │   │ target          │            │
│ iupac_name       │   │ moa             │            │
│ mol_weight       │   │ bystander_effect│            │
│ morgan_fp        │   │ smiles          │            │
└──────────────────┘   │ inchi           │            │
                       │ inchikey  UNIQUE│            │
  * nullable —         │ formula         │            │
    invalid when       │ iupac_name      │            │
    SMILES has         │ mol_weight      │            │
    attachment points  │ morgan_fp       │            │
                       └──────────────────┘            │
                              ▲                        │
                              └────────────────────────┘
```

## Table Schemas

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

### ADCActivity
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

## Relationships

| From | To | Cardinality | FK Constraint | Notes |
|------|----|-------------|---------------|-------|
| Antibody | Antigen | N:1 | ON DELETE RESTRICT | An antibody binds one antigen (e.g. Trastuzumab → HER2) |
| ADC | Antibody | N:1 | ON DELETE RESTRICT | Many ADCs can use the same antibody |
| ADC | Linker | N:1 | ON DELETE RESTRICT | Many ADCs can use the same linker chemistry |
| ADC | Payload | N:1 | ON DELETE RESTRICT | Many ADCs can carry the same payload (e.g., MMAE) |
| ADC | ADCActivity | 1:N | ON DELETE CASCADE | Activities have no meaning without their ADC |

ADC reaches Antigen transitively: `adc.antibody.antigen`. No direct FK.

**V1 limitation:** Antibody → Antigen is N:1. Bispecific antibodies cannot be represented. If needed, replace with a junction table.

## Unique Constraints

| Table | Column(s) | Notes |
|-------|-----------|-------|
| ADC | name | no duplicate ADC entries |
| Antibody | name | no duplicate antibodies |
| Antigen | name | no duplicate antigens |
| Linker | name | no duplicate linkers |
| Linker | inchikey | nullable — only enforced when present |
| Payload | name | no duplicate payloads |
| Payload | inchikey | molecular identity |

## Enums

**ADC Status:** `approved` | `phase_3` | `phase_2` | `phase_1` | `investigative`

**Conjugation Site:** `cysteine` | `lysine` | `engineered_cysteine` | `engineered_other`

**Activity Type:** `clinical_trial` | `in_vivo` | `in_vitro`

**Antibody Origin:** `chimeric` | `humanized` | `human` | `murine`

## Indexes

- `adc.name` — FULLTEXT (text search via `MATCH ... AGAINST`)
- `adc.status` — B-tree (filter by pipeline stage)
- `antibody.name` — FULLTEXT
- `antigen.name` — FULLTEXT
- `payload.name` — FULLTEXT
- `linker.name` — FULLTEXT
- All `_id` foreign keys — B-tree (joins)
- JSON columns (`synonyms`, `indications`) — not indexable with FULLTEXT; searched via `JSON_SEARCH()` / `JSON_CONTAINS()`

## Notes on JSON Fields

MariaDB has no native array type. `synonyms` and `indications` are stored as `JSON` columns. Queryable with `JSON_CONTAINS()` and `JSON_SEARCH()`.

## Notes on SMILES Fields

SMILES fields on Linker and Payload are consumed in two places:

1. **Server-side (Python RDKit):** Morgan fingerprint computation, molecular weight, 3D conformer generation. Handles `[*:1]`/`[*:2]` by replacing with `[H]` before processing.
2. **Client-side (RDKit WASM):** 2D SVG rendering with ACS1996 drawing style. Cleaned `[*:1]`/`[*:2]` → `[H]` before rendering.

### Linker SMILES attachment points

`[*:1]` = antibody-facing end, `[*:2]` = payload-facing end. Makes InChI/InChIKey invalid for linkers (RDKit errors on wildcard atoms). Therefore `inchi`/`inchikey` on Linker are nullable.

## Notes on `linker_payload_smiles`

The pre-connected linker-payload molecule on the ADC record. **Curated data, not computed** — the coupling reaction (e.g., PABC carbamate with MMAE's amine) can't be reliably automated. Only `[*:1]` (antibody attachment point) remains. The 3D pipeline reads this field directly.

## Notes on `structure_3d_path`

Nullable. NULL when the 3D pipeline fails. Frontend shows "Structure not yet available" instead of Mol* viewer.

## Data Sources

- Published ADC literature and FDA approval documents
- ChEMBL for payload/linker structures (SMILES)
- UniProt for antibody sequences and antigen info
- ClinicalTrials.gov for trial data (NCT numbers)
- AlphaFold DB for antibody structures

## Seed Validation Rules

Fail-fast per row, don't block the batch:

- SMILES parseable by `Chem.MolFromSmiles()` — reject row if not
- Amino acid sequences contain only valid residue letters (ACDEFGHIKLMNPQRSTVWY)
- InChIKey matches SMILES where both are provided (`Chem.inchi.MolToInchiKey`)
- `linker_payload_smiles` contains exactly one `[*:1]` attachment point
- Morgan fingerprints computed and stored at index time (radius=2, nbits=2048)

## Seed Insertion Order (FK constraints)

1. Antigens (no FK dependencies)
2. Linkers (no FK dependencies)
3. Payloads (no FK dependencies)
4. Antibodies (FK → Antigen)
5. ADCs (FK → Antibody, Linker, Payload)
6. ADCActivity (FK → ADC)

## 3D Structure Pipeline

Runs as a batch script (`data/generate_structures.py`), NOT as part of the web app.

```
For each ADC with linker_payload_smiles:
  1. Build full IgG from template (PDB 1HZH) + sequence superposition
  2. Take linker_payload_smiles from ADC record ([*:1] = Ab end)
  3. Record [*:1] atom index, replace with [H], embed (ETKDGv3), minimize (MMFF94)
  4. Identify conjugation sites on antibody by conjugation_site type
  5. Place DAR copies of linker-payload at sites (rigid-body toward target residue)
  6. Save combined PDB → store path in DB
  7. On ANY failure: set structure_3d_path = NULL, log error, continue
```

### Why template-based IgG

AlphaFold DB stores individual chains, not the IgG tetramer. ESMFold predicts single chains. Superpose antibody sequences onto a template IgG crystal structure (PDB 1HZH) via backbone fitting. Simpler and sufficient for reference visualization.

### Why `linker_payload_smiles` on ADC, not computed

The linker's `[*:2]` connects to the payload via specific chemistry (e.g., PABC carbamate to MMAE's secondary amine). Simulating this computationally is fragile. Store the pre-connected molecule as curated data.

### Conjugation site identification

Driven by `adc.conjugation_site`:
- `cysteine`: interchain disulfide S-S bonds (IgG1: C220, C226, C229 EU numbering)
- `lysine`: surface-exposed Lys by solvent-accessible surface area
- `engineered_cysteine` / `engineered_other`: known residue position from literature

### Linker-payload placement

- `coupling_chemistry` on Linker determines bond geometry (maleimide → thioether, NHS → amide, click → triazole)
- Orient `[*:1]` attachment atom toward target residue's side-chain terminus
- Approximate rigid-body placement, not covalent docking

### PDB chain IDs

H/A (heavy chains), L/B (light chains), D/E/F/G/I/J/K/M (drug-linker units)

The assembly is approximate — showing topology, not MD simulation. Label as "predicted/modeled structure."

## File Structure

```
data/
├── seed.py                    # database seeder with RDKit validation
├── add_lp_smiles.py           # add linker_payload_smiles to ADCs
├── generate_structures.py     # batch 3D PDB generation
└── sources/
    └── seed_data.json         # curated ~50 ADCs with components + activities
```
