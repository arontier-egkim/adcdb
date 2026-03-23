# Data Model — Entity Relationship

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

## Relationships

| From | To | Cardinality | FK Constraint | Notes |
|------|----|-------------|---------------|-------|
| Antibody | Antigen | N:1 | ON DELETE RESTRICT | An antibody binds one antigen (e.g. Trastuzumab → HER2) |
| ADC | Antibody | N:1 | ON DELETE RESTRICT | Many ADCs can use the same antibody |
| ADC | Linker | N:1 | ON DELETE RESTRICT | Many ADCs can use the same linker chemistry |
| ADC | Payload | N:1 | ON DELETE RESTRICT | Many ADCs can carry the same payload (e.g., MMAE) |
| ADC | ADCActivity | 1:N | ON DELETE CASCADE | Activities have no meaning without their ADC |

ADC reaches Antigen transitively: `adc.antibody.antigen`. No direct FK from ADC to Antigen.

**Query constraint:** This 2-hop path creates N+1 risk in both directions — forward (ADC lists needing antigen name) and reverse (antigen/component detail pages listing linked ADCs). All queries must use explicit JOINs from the ADC side. Set `lazy="raise"` on all ORM relationships. See ARCHITECTURE.md for exact query patterns per endpoint.

**V1 limitation:** Antibody → Antigen is N:1. Bispecific antibodies cannot be represented. If needed, replace with a junction table.

## Unique Constraints

| Table | Column(s) | Notes |
|-------|-----------|-------|
| ADC | name | no duplicate ADC entries |
| Antibody | name | no duplicate antibodies |
| Antigen | name | no duplicate antigens |
| Linker | name | no duplicate linkers |
| Linker | inchikey | nullable — only enforced when value is present |
| Payload | name | no duplicate payloads |
| Payload | inchikey | molecular identity |

## Enums

**ADC Status:**
`approved` | `phase_3` | `phase_2` | `phase_1` | `investigative`

**Conjugation Site:**
`cysteine` | `lysine` | `engineered_cysteine` | `engineered_other`

**Activity Type:**
`clinical_trial` | `in_vivo` | `in_vitro`

**Antibody Origin:**
`chimeric` | `humanized` | `human` | `murine`

## Indexes

- `adc.name` — FULLTEXT index (text search via `MATCH ... AGAINST`)
- `adc.status` — B-tree (filter by pipeline stage)
- `antibody.name` — FULLTEXT
- `antigen.name` — FULLTEXT
- `payload.name` — FULLTEXT
- `linker.name` — FULLTEXT
- All `_id` foreign keys — B-tree (joins)
- JSON columns (`synonyms`, `indications`) — not indexable with FULLTEXT; searched via `JSON_SEARCH()` / `JSON_CONTAINS()`

## Notes on Array Fields

MariaDB has no native array type. `synonyms` and `indications` are stored as `JSON` columns. Queryable with `JSON_CONTAINS()` and `JSON_SEARCH()`. At this scale, no junction tables needed.

## Notes on Linker SMILES

Linker SMILES use labeled attachment points: `[*:1]` for the antibody-facing end, `[*:2]` for the payload-facing end. This makes standard InChI/InChIKey generation invalid for linkers (RDKit will error on wildcard atoms). Therefore `inchi` and `inchikey` on Linker are nullable.

## Notes on `linker_payload_smiles` (ADC field)

The pre-connected linker-payload molecule stored on the ADC record. This is **curated data, not computed** — because the linker-payload coupling reaction (e.g., PABC carbamate formation with MMAE's amine) is chemistry that can't be reliably automated. Only `[*:1]` (antibody attachment point) remains. The 3D pipeline reads this field directly.

## Notes on `structure_3d_path`

Nullable. Set to NULL when the 3D pipeline fails for any reason (antibody structure unavailable, conformer embedding fails, conjugation site unresolvable). The frontend checks for NULL and shows "Structure not yet available" instead of the Mol* viewer.
