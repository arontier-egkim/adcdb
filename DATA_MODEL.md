# Data Model — Entity Relationship

## ER Diagram

```
                          ┌──────────────────┐
┌──────────────┐          │       ADC        │
│   Antigen    │          │──────────────────│
│──────────────│          │ id            PK │
│ id        PK │◀──┐      │ name             │
│ name         │   │      │ brand_name       │
│ synonyms JSON   │   │      │ synonyms JSON       │
│ gene_name    │   │      │ organization     │
│ uniprot_id   │   │      │ status           │
│ description  │   │      │ dar              │
└──────────────┘   │      │ conjugation_type │
                   │      │ indications JSON    │
┌──────────────┐   │      │ antibody_id   FK │──┐
│   Antibody   │   │      │ linker_id     FK │──┼──┐
│──────────────│   │      │ payload_id    FK │──┼──┼──┐
│ id        PK │◀──┼──────│                  │  │  │  │
│ name         │   │      │ structure_3d_path│  │  │  │
│ synonyms JSON   │   │      └──────────────────┘  │  │  │
│ type         │   │                │            │  │  │
│ subtype      │   │                │ 1:N        │  │  │
│ antigen_id FK│───┘                ▼            │  │  │
│ heavy_chain  │          ┌──────────────────┐   │  │  │
│ light_chain  │          │  ADCActivity     │   │  │  │
│ uniprot_id   │          │──────────────────│   │  │  │
└──────────────┘          │ id            PK │   │  │  │
                          │ adc_id        FK │   │  │  │
  (ADC reaches Antigen    │ activity_type    │   │  │  │
   via Antibody.antigen)  │ nct_number       │   │  │  │
                          │ phase            │   │  │  │
                          │ orr              │   │  │  │
                          │ model            │   │  │  │
                          │ tgi              │   │  │  │
                          │ ic50             │   │  │  │
                          │ cell_line        │   │  │  │
                          │ notes            │   │  │  │
                          └──────────────────┘   │  │  │
                                                 │  │  │
┌──────────────┐                                 │  │  │
│    Linker    │                                 │  │  │
│──────────────│                                 │  │  │
│ id        PK │◀────────────────────────────────┘  │  │
│ name         │                                    │  │
│ type         │    ┌──────────────┐                │  │
│ smiles       │    │   Payload    │                │  │
│ inchi        │    │──────────────│                │  │
│ inchikey     │    │ id        PK │◀───────────────┘  │
│ formula      │    │ name         │                   │
│ iupac_name   │    │ synonyms JSON   │                   │
│ mol_weight   │    │ target       │                   │
│ morgan_fp    │    │ moa          │                   │
└──────────────┘    │ smiles       │                   │
                    │ inchi        │                   │
                    │ inchikey     │                   │
                    │ formula      │                   │
                    │ iupac_name   │                   │
                    │ mol_weight   │                   │
                    │ morgan_fp    │                   │
                    └──────────────┘                   │
                           ▲                           │
                           └───────────────────────────┘
```

## Relationships

| From | To | Cardinality | Notes |
|------|----|-------------|-------|
| Antibody | Antigen | N:1 | An antibody binds one antigen (e.g. Trastuzumab → HER2) |
| ADC | Antibody | N:1 | Many ADCs can use the same antibody |
| ADC | Linker | N:1 | Many ADCs can use the same linker chemistry |
| ADC | Payload | N:1 | Many ADCs can carry the same payload (e.g., MMAE) |
| ADC | ADCActivity | 1:N | One ADC has many activity records (trials, assays) |

ADC reaches Antigen transitively: `adc.antibody.antigen`. No direct FK from ADC to Antigen.

**Query constraint:** This 2-hop path creates N+1 risk in both directions — forward (ADC lists needing antigen name) and reverse (antigen/component detail pages listing linked ADCs). All queries must use explicit JOINs from the ADC side. Set `lazy="raise"` on all ORM relationships. See ARCHITECTURE.md for exact query patterns per endpoint.

## Enums

**ADC Status:**
`approved` | `phase_3` | `phase_2` | `phase_1` | `investigative`

**Conjugation Type:**
`cysteine` | `lysine` | `site_specific`

**Activity Type:**
`clinical_trial` | `in_vivo` | `in_vitro`

**Linker Type:**
`cleavable` | `non_cleavable`

**Antibody Subtype:**
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
