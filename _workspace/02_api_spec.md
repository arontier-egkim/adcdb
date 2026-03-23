# API Specification

## General Information

- **Base URL**: `/api/v1`
- **Response Format**: JSON (except PDB file download)
- **Authentication**: None (V1 is read-only public)
- **CORS**: Allowed origins: `http://localhost:5173`, `http://localhost:3000`, `http://localhost:3001`
- **Pagination**: `page` (default 1, min 1) and `per_page` (default 50, min 1, max 100)

## Endpoint Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/health` | Health check | No |
| GET | `/api/v1/stats` | Homepage aggregate statistics | No |
| GET | `/api/v1/adcs` | List ADCs (paginated, filterable) | No |
| GET | `/api/v1/adcs/{id}` | ADC detail with all components + activities | No |
| GET | `/api/v1/adcs/{id}/structure` | Download PDB structure file | No |
| POST | `/api/v1/adcs` | Create new ADC | No |
| GET | `/api/v1/antibodies` | List antibodies (paginated) | No |
| GET | `/api/v1/antibodies/{id}` | Antibody detail with antigen | No |
| GET | `/api/v1/antibodies/{id}/adcs` | ADCs linked to antibody | No |
| GET | `/api/v1/antigens` | List antigens (paginated) | No |
| GET | `/api/v1/antigens/{id}` | Antigen detail | No |
| GET | `/api/v1/antigens/{id}/adcs` | ADCs targeting antigen (reverse 2-hop) | No |
| GET | `/api/v1/linkers` | List linkers (paginated) | No |
| GET | `/api/v1/linkers/{id}` | Linker detail | No |
| GET | `/api/v1/linkers/{id}/adcs` | ADCs using linker | No |
| GET | `/api/v1/payloads` | List payloads (paginated) | No |
| GET | `/api/v1/payloads/{id}` | Payload detail | No |
| GET | `/api/v1/payloads/{id}/adcs` | ADCs using payload | No |
| GET | `/api/v1/search` | Unified text search across all entities | No |
| GET | `/api/v1/search/structure` | SMILES structural similarity search | No |
| GET | `/api/v1/search/sequence` | Amino acid sequence similarity search | No |

---

## Detailed API Specifications

---

### GET /api/v1/health

Health check endpoint.

**Response** `200 OK`

```json
{
  "status": "ok"
}
```

---

### GET /api/v1/stats

Aggregate statistics for the homepage dashboard.

**Query**: 3 SQL queries (top antigens, top payload targets, pipeline counts) + 1 total count.

**Response** `200 OK`

```json
{
  "total_adcs": 49,
  "top_antigens": [
    { "name": "HER2", "count": 12 },
    { "name": "Trop-2", "count": 5 }
  ],
  "top_payload_targets": [
    { "name": "Microtubule", "count": 15 },
    { "name": "Topoisomerase I", "count": 8 }
  ],
  "pipeline": {
    "approved": 12,
    "phase_3": 5,
    "phase_2": 10,
    "phase_1": 8,
    "investigative": 14
  }
}
```

---

### GET /api/v1/adcs

List ADCs with flat component names. Single 4-way JOIN query.

**Query Parameters**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| status | string | No | - | Filter by status (approved, phase_3, phase_2, phase_1, investigative) |
| antigen | string | No | - | Filter by exact antigen name |
| payload_target | string | No | - | Filter by exact payload target |
| q | string | No | - | Name search (LIKE %q%) |
| page | int | No | 1 | Page number (>= 1) |
| per_page | int | No | 50 | Items per page (1-100) |

**Response** `200 OK`

```json
[
  {
    "id": "019654a3-...",
    "name": "Trastuzumab deruxtecan",
    "brand_name": "Enhertu",
    "status": "approved",
    "dar": 8.0,
    "organization": "Daiichi Sankyo / AstraZeneca",
    "antibody_name": "Trastuzumab",
    "antigen_name": "HER2",
    "linker_name": "MC-GGFG-AM",
    "payload_name": "DXd"
  }
]
```

**Notes**: Response is an array (not wrapped in pagination object). Ordered by `ADC.name` ASC.

---

### GET /api/v1/adcs/{adc_id}

Full ADC detail with nested components and activities. Uses `joinedload` for 4 relationships in 1 query + activities.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| adc_id | string (UUID) | ADC identifier |

**Response** `200 OK`

```json
{
  "id": "019654a3-...",
  "name": "Trastuzumab deruxtecan",
  "brand_name": "Enhertu",
  "synonyms": ["T-DXd", "DS-8201"],
  "organization": "Daiichi Sankyo / AstraZeneca",
  "status": "approved",
  "dar": 8.0,
  "conjugation_site": "cysteine",
  "indications": ["HER2+ breast cancer", "HER2+ gastric cancer"],
  "antibody_id": "019654a2-...",
  "linker_id": "019654a1-...",
  "payload_id": "019654a0-...",
  "linker_payload_smiles": "[*:1]CCCCCC(=O)NCC...",
  "structure_3d_path": "structures/019654a3-....pdb",
  "created_at": "2026-03-23T12:11:38",
  "updated_at": "2026-03-23T12:11:38",
  "antibody": {
    "id": "019654a2-...",
    "name": "Trastuzumab",
    "synonyms": null,
    "isotype": "IgG1",
    "origin": "humanized",
    "antigen_id": "019654a1-...",
    "heavy_chain_seq": "EVQLVESGGGLVQPGG...",
    "light_chain_seq": "DIQMTQSPSSLSAS...",
    "uniprot_id": "P04626",
    "antigen": {
      "id": "019654a1-...",
      "name": "HER2",
      "synonyms": ["ERBB2", "CD340"],
      "gene_name": "ERBB2",
      "uniprot_id": "P04626",
      "description": "Receptor tyrosine kinase..."
    }
  },
  "linker": {
    "id": "019654a1-...",
    "name": "MC-GGFG-AM",
    "cleavable": true,
    "cleavage_mechanism": "protease",
    "coupling_chemistry": "maleimide",
    "smiles": "[*:1]CCCCCC(=O)NCC(=O)NCC...",
    "inchi": null,
    "inchikey": null,
    "formula": "C24H32N4O6",
    "iupac_name": null,
    "mol_weight": 476.5432
  },
  "payload": {
    "id": "019654a0-...",
    "name": "DXd",
    "synonyms": ["MAAA-1181a", "exatecan derivative"],
    "target": "Topoisomerase I",
    "moa": "Topoisomerase I inhibitor",
    "bystander_effect": true,
    "smiles": "CCO...",
    "inchi": "InChI=1S/...",
    "inchikey": "XXXXXXXX...",
    "formula": "C21H20N2O5",
    "iupac_name": null,
    "mol_weight": 380.3912
  },
  "activities": [
    {
      "id": "019654a4-...",
      "adc_id": "019654a3-...",
      "activity_type": "clinical_trial",
      "nct_number": "NCT03248492",
      "phase": "Phase III",
      "orr": 79.7,
      "model": null,
      "tgi": null,
      "ic50_value": null,
      "ic50_unit": null,
      "cell_line": null,
      "notes": "DESTINY-Breast03"
    }
  ]
}
```

**Response** `404 Not Found`

```json
{ "detail": "ADC not found" }
```

---

### GET /api/v1/adcs/{adc_id}/structure

Download the predicted PDB structure file.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| adc_id | string (UUID) | ADC identifier |

**Response** `200 OK`

- Content-Type: `chemical/x-pdb`
- Content-Disposition: `attachment; filename="{adc_id}.pdb"`
- Body: PDB file content

**Response** `404 Not Found`

```json
{ "detail": "ADC not found" }
```
or
```json
{ "detail": "Structure not available" }
```
or
```json
{ "detail": "Structure file missing" }
```

---

### POST /api/v1/adcs

Create a new ADC record.

**Request Body**

```json
{
  "name": "Example ADC",
  "brand_name": null,
  "synonyms": null,
  "organization": "Example Pharma",
  "status": "investigative",
  "dar": 4.0,
  "conjugation_site": "cysteine",
  "indications": ["solid tumors"],
  "antibody_id": "019654a2-...",
  "linker_id": "019654a1-...",
  "payload_id": "019654a0-...",
  "linker_payload_smiles": null
}
```

**Response** `201 Created`

Returns full `ADCRead` object (same as GET detail).

---

### GET /api/v1/antibodies

List antibodies with nested antigen.

**Query Parameters**

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| q | string | No | - | Name search (LIKE %q%) |
| page | int | No | 1 | Page number |
| per_page | int | No | 50 | Items per page |

**Response** `200 OK`

```json
[
  {
    "id": "019654a2-...",
    "name": "Trastuzumab",
    "synonyms": null,
    "isotype": "IgG1",
    "origin": "humanized",
    "antigen_id": "019654a1-...",
    "heavy_chain_seq": "EVQLVESGGGLVQPGG...",
    "light_chain_seq": "DIQMTQSPSSLSAS...",
    "uniprot_id": "P04626",
    "antigen": {
      "id": "019654a1-...",
      "name": "HER2",
      "synonyms": ["ERBB2"],
      "gene_name": "ERBB2",
      "uniprot_id": "P04626",
      "description": "..."
    }
  }
]
```

---

### GET /api/v1/antibodies/{antibody_id}

Single antibody detail with nested antigen.

**Response** `200 OK` -- Same schema as list item.

**Response** `404 Not Found`

```json
{ "detail": "Antibody not found" }
```

---

### GET /api/v1/antibodies/{antibody_id}/adcs

ADCs linked to this antibody. Returns `ADCListItem[]`.

**Query Parameters**: `page`, `per_page`

**Response** `200 OK` -- Same schema as `GET /api/v1/adcs` list items.

---

### GET /api/v1/antigens

List antigens.

**Query Parameters**: `q`, `page`, `per_page`

**Response** `200 OK`

```json
[
  {
    "id": "019654a1-...",
    "name": "HER2",
    "synonyms": ["ERBB2", "CD340"],
    "gene_name": "ERBB2",
    "uniprot_id": "P04626",
    "description": "Receptor tyrosine kinase..."
  }
]
```

---

### GET /api/v1/antigens/{antigen_id}

Single antigen detail.

**Response** `200 OK` -- Same schema as list item.

**Response** `404 Not Found`

```json
{ "detail": "Antigen not found" }
```

---

### GET /api/v1/antigens/{antigen_id}/adcs

ADCs targeting this antigen (reverse 2-hop: Antigen <- Antibody <- ADC). Returns `ADCListItem[]`.

**Query Parameters**: `page`, `per_page`

**Response** `200 OK` -- Same schema as `GET /api/v1/adcs` list items.

---

### GET /api/v1/linkers

List linkers.

**Query Parameters**: `q`, `page`, `per_page`

**Response** `200 OK`

```json
[
  {
    "id": "019654a1-...",
    "name": "MC-VC-PABC",
    "cleavable": true,
    "cleavage_mechanism": "protease",
    "coupling_chemistry": "maleimide",
    "smiles": "[*:1]CCCCCC(=O)NC(CC(C)C)...[*:2]",
    "inchi": null,
    "inchikey": null,
    "formula": "C32H44N4O7",
    "iupac_name": null,
    "mol_weight": 600.7144
  }
]
```

---

### GET /api/v1/linkers/{linker_id}

Single linker detail.

**Response** `200 OK` -- Same schema as list item.

**Response** `404 Not Found`

```json
{ "detail": "Linker not found" }
```

---

### GET /api/v1/linkers/{linker_id}/adcs

ADCs using this linker. Returns `ADCListItem[]`.

**Query Parameters**: `page`, `per_page`

---

### GET /api/v1/payloads

List payloads.

**Query Parameters**: `q`, `page`, `per_page`

**Response** `200 OK`

```json
[
  {
    "id": "019654a0-...",
    "name": "MMAE",
    "synonyms": ["Monomethyl auristatin E"],
    "target": "Microtubule",
    "moa": "Microtubule inhibitor",
    "bystander_effect": true,
    "smiles": "CCC(C)C(C(CC...",
    "inchi": "InChI=1S/...",
    "inchikey": "XXXXXXXX...",
    "formula": "C39H65N5O7",
    "iupac_name": null,
    "mol_weight": 717.9643
  }
]
```

---

### GET /api/v1/payloads/{payload_id}

Single payload detail.

**Response** `200 OK` -- Same schema as list item.

**Response** `404 Not Found`

```json
{ "detail": "Payload not found" }
```

---

### GET /api/v1/payloads/{payload_id}/adcs

ADCs using this payload. Returns `ADCListItem[]`.

**Query Parameters**: `page`, `per_page`

---

### GET /api/v1/search

Unified text search across all entity types. Runs 5 independent LIKE queries (one per entity type), each limited to 10 results.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes (min 1 char) | Search term |

**Response** `200 OK`

```json
{
  "adcs": [
    { "id": "...", "name": "Trastuzumab deruxtecan", "status": "approved" }
  ],
  "antibodies": [
    { "id": "...", "name": "Trastuzumab" }
  ],
  "antigens": [
    { "id": "...", "name": "HER2", "gene_name": "ERBB2" }
  ],
  "linkers": [
    { "id": "...", "name": "MC-GGFG-AM" }
  ],
  "payloads": [
    { "id": "...", "name": "DXd" }
  ]
}
```

**Notes**: Antigen search matches both `name` and `gene_name` (via `OR`). All other entities match `name` only.

---

### GET /api/v1/search/structure

Search linkers and payloads by structural similarity (Tanimoto coefficient of Morgan fingerprints).

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| smiles | string | Yes (min 1 char) | Query SMILES string |

**Response** `200 OK`

```json
{
  "results": [
    {
      "id": "...",
      "name": "MMAE",
      "type": "payload",
      "smiles": "CCC(C)...",
      "similarity": 0.8532
    },
    {
      "id": "...",
      "name": "MC-VC-PABC",
      "type": "linker",
      "smiles": "[*:1]CCCCCC...",
      "similarity": 0.4211
    }
  ]
}
```

**Response** `200 OK` (invalid SMILES or no results)

```json
{
  "results": [],
  "message": "No results or invalid SMILES"
}
```

**Notes**: Morgan fingerprint params: radius=2, nbits=2048. `[*:n]` attachment points replaced with `[H]` before fingerprint computation. Results sorted by similarity descending, top 20 returned.

---

### GET /api/v1/search/sequence

Search antibodies by amino acid sequence similarity using Biopython PairwiseAligner.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| sequence | string | Yes (min 5 chars) | Amino acid sequence |

**Response** `200 OK`

```json
{
  "results": [
    {
      "id": "...",
      "name": "Trastuzumab",
      "chain": "heavy",
      "score": 245.5,
      "normalized_score": 0.9812
    }
  ]
}
```

**Response** `200 OK` (invalid sequence or no results)

```json
{
  "results": [],
  "message": "No results or invalid sequence"
}
```

**Notes**: Aligner params: local mode, match=2, mismatch=-1, open_gap=-2, extend_gap=-0.5. Normalized score = raw_score / (query_length * 2), capped at 1.0. Matches against both heavy and light chains; reports best-scoring chain. Results sorted by raw score descending, top 20 returned.

---

## Common Response Schema Reference

### ADCListItem

Used by: ADC list, all `/{entity_id}/adcs` endpoints.

```typescript
{
  id: string;
  name: string;
  brand_name: string | null;
  status: string;           // "approved" | "phase_3" | "phase_2" | "phase_1" | "investigative"
  dar: number | null;
  organization: string | null;
  antibody_name: string;
  antigen_name: string;
  linker_name: string;
  payload_name: string;
}
```

### ADCRead

Used by: ADC detail, ADC create response.

```typescript
{
  id: string;
  name: string;
  brand_name: string | null;
  synonyms: string[] | null;
  organization: string | null;
  status: string;
  dar: number | null;
  conjugation_site: string | null;
  indications: string[] | null;
  antibody_id: string;
  linker_id: string;
  payload_id: string;
  linker_payload_smiles: string | null;
  structure_3d_path: string | null;
  created_at: string;       // ISO datetime
  updated_at: string;       // ISO datetime
  antibody: AntibodyRead;   // nested
  linker: LinkerRead;       // nested
  payload: PayloadRead;     // nested
  activities: ActivityRead[]; // nested array
}
```

### Error Response

All 404 errors return:

```json
{ "detail": "Entity not found" }
```

FastAPI validation errors (422) return:

```json
{
  "detail": [
    {
      "loc": ["query", "param_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```
