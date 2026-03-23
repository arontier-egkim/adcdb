# Test Plan

## Test Strategy

- **Coverage Target**: 80% or above for backend services and routers
- **Test Levels**: Unit / Integration / E2E
- **Test Pyramid**: Unit (70%) > Integration (20%) > E2E (10%)
- **Pattern**: AAA (Arrange, Act, Assert)
- **Independence**: All tests are self-contained; no inter-test dependencies

## Test Tool Stack

| Category | Tool | Purpose |
|----------|------|---------|
| Backend Unit/Integration | pytest + httpx + pytest-asyncio | FastAPI endpoints, services |
| Backend DB | SQLite (in-memory) | Isolated DB for integration tests |
| Frontend Unit | Vitest | Functions, hooks, utilities |
| Frontend Component | Testing Library | React components |
| E2E Tests | Playwright | User flows |
| Chemistry Tests | pytest + RDKit | Fingerprint, conformer logic |

## Test Matrix

| Feature | Unit Test | Integration Test | E2E Test | Priority |
|---------|-----------|-----------------|----------|----------|
| Chemistry Service (Morgan FP, Tanimoto) | Yes | - | - | P0 |
| Sequence Service (PairwiseAligner) | Yes | - | - | P0 |
| Structure Module (conformer, assembler) | Yes | - | - | P1 |
| ADC List Endpoint | - | Yes | - | P0 |
| ADC Detail Endpoint | - | Yes | - | P0 |
| ADC Structure Endpoint | - | Yes | - | P1 |
| ADC Create Endpoint | - | Yes | - | P1 |
| Antibody/Antigen/Linker/Payload CRUD | - | Yes | - | P0 |
| Linked ADC Endpoints | - | Yes | - | P0 |
| Text Search Endpoint | - | Yes | - | P0 |
| Structure Search Endpoint | - | Yes | - | P1 |
| Sequence Search Endpoint | - | Yes | - | P1 |
| Stats Endpoint | - | Yes | - | P0 |
| Health Endpoint | - | Yes | - | P0 |
| Browse Page | - | - | Yes | P0 |
| Search Page (all tabs) | - | - | Yes | P1 |
| ADC Detail + 3D Viewer | - | - | Yes | P1 |

## Test Scenarios

### Unit Tests -- Chemistry Service

| # | Scenario | Input | Expected Result | Type |
|---|----------|-------|----------------|------|
| U-1 | Valid SMILES to Morgan FP | `"CCO"` | Returns ExplicitBitVect, length 2048 | Unit |
| U-2 | Invalid SMILES returns None | `"invalid_smiles"` | Returns None | Unit |
| U-3 | SMILES with attachment points | `"[*:1]CCCC[*:2]"` | Replaces with [H], returns valid FP | Unit |
| U-4 | Empty SMILES | `""` | Returns None | Unit |
| U-5 | FP from stored bytes roundtrip | Stored bytes from valid SMILES | Reconstructed FP matches original | Unit |
| U-6 | FP from None/empty bytes | `None`, `b""` | Returns None | Unit |
| U-7 | Tanimoto self-similarity | Same SMILES twice | Similarity = 1.0 | Unit |
| U-8 | Tanimoto different molecules | Ethanol vs Benzene | 0.0 < similarity < 1.0 | Unit |
| U-9 | Morgan FP uses radius=2 nbits=2048 | Valid mol | FP length is 2048 | Unit |

### Unit Tests -- Sequence Service

| # | Scenario | Input | Expected Result | Type |
|---|----------|-------|----------------|------|
| U-10 | Valid amino acid sequence | `"EVQLVESGGGLVQ"` | Returns cleaned uppercase string | Unit |
| U-11 | Invalid characters in sequence | `"EVQLV123"` | Returns None | Unit |
| U-12 | Whitespace handling | `"EVQ LVE"` | Returns `"EVQLVE"` (whitespace stripped) | Unit |
| U-13 | Empty sequence | `""` | Returns None | Unit |
| U-14 | All valid amino acids | All 20 standard AAs | Returns cleaned string | Unit |

### Unit Tests -- Structure Module

| # | Scenario | Input | Expected Result | Type |
|---|----------|-------|----------------|------|
| U-15 | Generate conformer from valid LP SMILES | `"[*:1]CCCCCC(=O)NCC"` | Returns Mol object with 3D coords | Unit |
| U-16 | Generate conformer from None | `None` | Returns None | Unit |
| U-17 | Generate conformer from invalid SMILES | `"invalid"` | Returns None | Unit |
| U-18 | mol_to_pdb_block produces valid PDB | Valid Mol | PDB string contains HETATM lines | Unit |
| U-19 | assemble_adc with valid inputs | LP SMILES + cysteine + DAR=4 | Returns PDB string with ATOM and HETATM | Unit |
| U-20 | assemble_adc with no LP SMILES | `None` | Returns None | Unit |
| U-21 | generate_and_save creates file | Valid inputs + temp dir | File exists on disk, returns path | Unit |

### Integration Tests -- API Endpoints

| # | Scenario | Input | Expected Result | Type |
|---|----------|-------|----------------|------|
| I-1 | GET /api/v1/health | - | `{"status": "ok"}` | Integration |
| I-2 | GET /api/v1/adcs (list) | - | Returns array of ADCListItem | Integration |
| I-3 | GET /api/v1/adcs with status filter | `?status=approved` | Only approved ADCs returned | Integration |
| I-4 | GET /api/v1/adcs with q filter | `?q=test` | Filtered by name LIKE | Integration |
| I-5 | GET /api/v1/adcs/{id} (detail) | Valid ADC id | Returns ADCRead with nested components | Integration |
| I-6 | GET /api/v1/adcs/{id} (not found) | Invalid UUID | 404 response | Integration |
| I-7 | GET /api/v1/adcs/{id}/structure (no structure) | ADC with null structure_3d_path | 404 "Structure not available" | Integration |
| I-8 | POST /api/v1/adcs | Valid ADCCreate body | 201 with ADCRead response | Integration |
| I-9 | GET /api/v1/antibodies | - | Returns array with nested antigen | Integration |
| I-10 | GET /api/v1/antibodies/{id} | Valid id | Returns AntibodyRead with antigen | Integration |
| I-11 | GET /api/v1/antibodies/{id}/adcs | Valid id | Returns ADCListItem array | Integration |
| I-12 | GET /api/v1/antigens | - | Returns array of AntigenRead | Integration |
| I-13 | GET /api/v1/antigens/{id}/adcs | Valid id | Returns ADCListItem array (2-hop JOIN) | Integration |
| I-14 | GET /api/v1/linkers | - | Returns array of LinkerRead | Integration |
| I-15 | GET /api/v1/payloads | - | Returns array of PayloadRead | Integration |
| I-16 | GET /api/v1/search?q=test | Search term | Returns results grouped by entity type | Integration |
| I-17 | GET /api/v1/stats | - | Returns total_adcs, top_antigens, pipeline | Integration |
| I-18 | Pagination params | `?page=1&per_page=5` | Max 5 results returned | Integration |
| I-19 | Invalid pagination (page=0) | `?page=0` | 422 validation error | Integration |
| I-20 | per_page exceeds max (>100) | `?per_page=200` | 422 validation error | Integration |

### E2E Test Scenarios

| # | Scenario | Steps | Expected Result | Type |
|---|----------|-------|----------------|------|
| E-1 | Browse ADCs | Navigate to /browse, verify table loads | Table with ADC rows visible | E2E |
| E-2 | Filter by status | Click "Approved" filter on Browse | Only approved ADCs shown | E2E |
| E-3 | ADC detail page | Click an ADC name from Browse | Detail page with components, activities | E2E |
| E-4 | Text search | Go to /search, type "HER2", submit | Results include HER2-targeting ADCs | E2E |
| E-5 | Navigate to component | From ADC detail, click antibody link | Antibody detail page loads | E2E |

## Test Configuration

### pytest Configuration (backend/pyproject.toml additions)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Test Dependencies (to add to pyproject.toml)

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
    "aiosqlite>=0.20",
]
```

## Key Test Rules

1. All ORM relationship tests must verify `lazy="raise"` is enforced (accessing unloaded relationships raises)
2. Morgan fingerprint tests must verify `radius=2, nbits=2048` consistency between index and query time
3. ADC queries must be tested with explicit JOINs (no lazy loading)
4. Nullable `structure_3d_path` must be tested: frontend shows "not yet available", API returns 404
5. Antigen access path must go through `adc.antibody.antigen` (2-hop), never direct
6. Text search uses LIKE (not FULLTEXT MATCH), confirmed at current scale
