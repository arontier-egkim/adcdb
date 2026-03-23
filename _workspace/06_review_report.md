# Code Review & Test Report

## Overall Assessment

- **Deployment Readiness**: Ready (with minor recommendations below)
- **Test Coverage**: 77 tests passing (36 integration, 23 unit chemistry/sequence, 18 unit structure)
- **Code Quality**: High -- clean architecture, consistent patterns, well-separated concerns

## Test Results Summary

| Test Suite | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| API Endpoints (integration) | 36 | 36 | 0 |
| Chemistry Service (unit) | 14 | 14 | 0 |
| Sequence Service (unit) | 10 | 10 | 0 |
| Structure Module (unit) | 17 | 17 | 0 |
| **Total** | **77** | **77** | **0** |

## Security Review

### CORS Configuration -- PASS

CORS is restricted to explicit frontend origins (`localhost:5173`, `localhost:3000`, `localhost:3001`). `allow_methods=["*"]` and `allow_headers=["*"]` are permissive but acceptable for a read-only internal tool with no authentication.

### SQL Injection -- PASS

All queries use SQLAlchemy ORM with parameterized queries. No raw SQL strings are constructed from user input. The `LIKE` patterns in search endpoints use SQLAlchemy's `.like()` method which properly parameterizes the value.

### XSS -- PASS (frontend)

React automatically escapes output in JSX. No use of `dangerouslySetInnerHTML`. API responses are JSON only. SMILES strings displayed in `<pre>` tags are safely escaped.

### Path Traversal -- PASS

The structure endpoint (`GET /adcs/{id}/structure`) reads `structure_3d_path` from the database, not from user input. The path is set by the trusted offline pipeline. The `FileResponse` call uses the DB-stored path directly. However, see recommendation R-1 below.

### No Authentication -- ACCEPTABLE

V1 is explicitly designed as a read-only public database. The only write endpoint is `POST /api/v1/adcs` which is undocumented and would need authentication in production. See recommendation R-3.

## Findings

### Required Fixes -- None

No critical security or functionality issues were found. All endpoints work correctly, all ORM relationships use `lazy="raise"`, all queries use explicit JOINs, and Morgan fingerprint parameters (radius=2, nbits=2048) are consistent between index and query time.

### Previously Fixed Issues (by other agents)

The backend and frontend agents already fixed several issues before this review:

1. **Stats pipeline missing zero-count statuses** (fixed in stats.py) -- All 5 status keys now always present
2. **Unused imports** (fixed in antigen model, antibodies/antigens routers) -- Cleaned up
3. **Missing TypeScript interface fields** (fixed in api.ts) -- ADC, Linker, Payload interfaces now complete
4. **Missing light chain display** (fixed in AntibodyDetail.tsx) -- Now shows both chains
5. **Browse page missing name search** (fixed in Browse.tsx) -- Added `q` parameter support
6. **Search structure result link fallback** (fixed in Search.tsx) -- Correct type for structure/sequence tabs

### Recommended Fixes (Quality/Performance)

#### R-1: Structure endpoint path validation (Minor, Security Hardening)

**File**: `backend/app/routers/adcs.py`, line 85

The structure endpoint does `Path(row.structure_3d_path)` using the DB value directly. While this is safe because the path comes from a trusted pipeline, a defense-in-depth approach would validate that the resolved path stays within the expected `structures/` directory.

```python
# Current
path = Path(row.structure_3d_path)

# Recommended
base = Path(settings.STRUCTURES_DIR).resolve()
path = Path(row.structure_3d_path).resolve()
if not str(path).startswith(str(base)):
    raise HTTPException(status_code=404, detail="Structure file missing")
```

#### R-2: LIKE search with unescaped wildcards (Minor, Correctness)

**Files**: `backend/app/routers/adcs.py` (line 51), `search.py` (line 19), and all entity list endpoints

The `q` parameter is inserted directly into LIKE patterns (`f"%{q}%"`). If a user submits `%` or `_` as a search term, those are LIKE wildcards and would match unintended rows. At current scale this is a non-issue, but for correctness:

```python
# Current
stmt = stmt.where(ADC.name.like(f"%{q}%"))

# Recommended (escape LIKE wildcards)
escaped_q = q.replace("%", "\\%").replace("_", "\\_")
stmt = stmt.where(ADC.name.like(f"%{escaped_q}%"))
```

#### R-3: POST /api/v1/adcs has no validation guards (Minor, Security)

**File**: `backend/app/routers/adcs.py`, line 91

The create endpoint accepts any valid JSON body matching `ADCCreate` with no authentication. While V1 is explicitly read-only public, this write endpoint is exposed. Consider either:
- Removing it until authentication is added
- Adding a simple API key check
- Documenting it as intentional

#### R-4: RDKit deprecation warning (Minor, Maintenance)

**Files**: `backend/app/services/chemistry_service.py`, `data/seed.py`

`AllChem.GetMorganFingerprintAsBitVect()` shows a deprecation warning suggesting `rdFingerprintGenerator.GetMorganGenerator()`. The current API still works but should be migrated before the next major RDKit release:

```python
# Current
fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)

# Recommended migration
from rdkit.Chem import rdFingerprintGenerator
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fp = gen.GetFingerprint(mol)
```

Both `seed.py` (index time) and `chemistry_service.py` (query time) must be updated together to maintain consistency.

#### R-5: FULLTEXT indexes unused (Minor, Performance)

**Files**: All model files with FULLTEXT indexes, search router

FULLTEXT indexes are created on all `name` columns but the search endpoints use `LIKE '%term%'` which cannot use these indexes. At current scale (~50 ADCs) this is fine, but if the dataset grows, switching to `MATCH ... AGAINST` in boolean mode would leverage these indexes.

#### R-6: `allow_credentials=True` with `allow_origins` list (Minor, Security)

**File**: `backend/app/main.py`, line 22

`allow_credentials=True` is set but the application has no authentication (no cookies, no sessions). This is harmless but unnecessary. Removing it would be cleaner:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Notes

1. **N+1 Query Prevention**: All 10 ORM relationships across 6 models use `lazy="raise"`. Every endpoint that needs related data uses explicit `joinedload()` or column-level `select()`. The ADC list endpoint uses a 4-way column-level JOIN (not ORM object loading) which is the most efficient pattern.

2. **Antigen Access Path**: Verified that antigen is always accessed via `adc.antibody.antigen` (2-hop). The antigen linked-ADC endpoint correctly uses `Antibody.antigen_id == antigen_id` in its WHERE clause with a 2-hop JOIN from ADC side.

3. **Morgan Fingerprint Consistency**: Verified `radius=2, nbits=2048` in both:
   - Index time: `data/seed.py` line 40
   - Query time: `app/services/chemistry_service.py` line 17
   - Storage format: bit string bytes (2048 chars) in both locations

4. **Nullable structure_3d_path Handling**: Backend returns 404 "Structure not available" when path is NULL. Frontend checks `adc.structure_3d_path` before rendering MolViewer and shows "Predicted 3D structure not yet available" message.

5. **Curated linker_payload_smiles**: The field is set by `add_lp_smiles.py` based on pattern matching, not computed. The `POST /api/v1/adcs` endpoint accepts it as optional input. This matches the project rule.

6. **Test Infrastructure**: Tests use in-memory SQLite via `aiosqlite` with dependency injection override, providing fast isolated test execution without requiring MariaDB. All fixtures are function-scoped for full test independence.

## Code Quality Checklist

- [x] Python type hints used consistently (all models, schemas, services, routers)
- [x] Pydantic validation on all inputs (schemas with proper types, Query params with ge/le constraints)
- [x] SQLAlchemy relationships use `lazy="raise"` (all 10 relationships verified)
- [x] No N+1 queries (all endpoints use explicit JOINs)
- [x] TypeScript strict mode, no `any` (interfaces match Pydantic schemas)
- [x] Error handling consistency (404 with descriptive detail messages on all detail endpoints)
- [x] No hardcoded environment variables (all via `pydantic-settings` with `ADCDB_` prefix)
- [x] Frontend correctly handles nullable fields (structure_3d_path, SMILES "C" placeholder)
- [x] UUIDv7 primary keys across all models
- [x] ON DELETE RESTRICT on component FKs, CASCADE on activities

## Files Created

- `/Users/egkim/Developer/arontier-egkim/adcdb/_workspace/04_test_plan.md` -- Test plan
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/__init__.py` -- Test package init
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/conftest.py` -- Shared fixtures (DB engine, session, httpx client, seed data)
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/test_chemistry_service.py` -- 14 unit tests for Morgan FP and Tanimoto
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/test_sequence_service.py` -- 10 unit tests for sequence validation
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/test_structure.py` -- 17 unit tests for conformer and assembly
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/tests/test_api_endpoints.py` -- 36 integration tests for all API endpoints

## Files Modified

- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/pyproject.toml` -- Added dev dependency group (pytest, httpx, aiosqlite) and pytest config
