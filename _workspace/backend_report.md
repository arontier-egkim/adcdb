# Backend Verification Report

## Summary

The backend codebase is well-implemented and closely follows the architecture docs, API spec, and plan. All endpoints are registered, all models match the DB schema, and the core services (chemistry, sequence) work correctly. Three minor issues were found and fixed.

## Verification Checklist

| Check | Status | Notes |
|-------|--------|-------|
| All ORM relationships use `lazy="raise"` | PASS | All 10 relationships across 6 models confirmed |
| All routers use explicit JOINs (no N+1) | PASS | Every ADCListItem query uses 4-way JOIN from ADC side |
| ADC queries JOIN through Antibody to reach Antigen (2 hops) | PASS | `ADC -> Antibody -> Antigen` in list, linked-ADC, and stats queries |
| Morgan fingerprints use radius=2, nbits=2048 | PASS | Verified in seed.py (index time) and chemistry_service.py (query time) |
| Schemas match the API spec | PASS | ADCRead, ADCListItem, AntibodyRead, AntigenRead, LinkerRead, PayloadRead, ActivityRead all match |
| Text search works (LIKE matching) | PASS | Unified search queries 5 entity types with `LIKE %q%`, antigen also matches gene_name |
| Structure search (Tanimoto) | PASS | Loads all fingerprints, computes Tanimoto, returns top 20 sorted by similarity |
| Sequence search (PairwiseAligner) | PASS | Local mode, match=2, mismatch=-1, open_gap=-2, extend_gap=-0.5, normalized by query length |
| Stats endpoint | PASS (fixed) | Top antigens, top payload targets, pipeline funnel, total count |
| Structure endpoint serves PDB files | PASS | FileResponse with `chemical/x-pdb` content type, handles missing ADC/structure/file |
| Seed data valid, FK insertion order correct | PASS | Antigens -> Payloads -> Linkers -> Antibodies -> ADCs -> Activities |
| Alembic migration async-configured | PASS | Uses `async_engine_from_config` + `run_sync` pattern |
| ON DELETE RESTRICT on component FKs | PASS | antibody_id, linker_id, payload_id all RESTRICT |
| ON DELETE CASCADE on ADCActivity | PASS | adc_id FK uses CASCADE |
| UUIDv7 primary keys | PASS | All models use `default=lambda: str(uuid7())` |
| CORS configured | PASS | localhost:5173, localhost:3000, localhost:3001 |
| FULLTEXT indexes created | PASS | On all name columns (antigen, antibody, linker, payload, adc) |
| B-tree index on adc.status | PASS | `ix_adc_status` |

## Issues Found and Fixed

### 1. Unused `uuid` import in antigen model

**File:** `backend/app/models/antigen.py`
**Issue:** `import uuid` on line 1 was unused (UUIDv7 comes from `uuid_utils`).
**Fix:** Removed the unused import.

### 2. Unused `AntibodyCreate` and `AntigenCreate` imports in routers

**Files:** `backend/app/routers/antibodies.py`, `backend/app/routers/antigens.py`
**Issue:** `AntibodyCreate` and `AntigenCreate` were imported but never used (no POST endpoints for those entities).
**Fix:** Removed the unused imports.

### 3. Stats `pipeline` response missing zero-count statuses

**File:** `backend/app/routers/stats.py`
**Issue:** The pipeline dict was built dynamically from DB query results, meaning statuses with zero ADCs would be absent from the response. The API spec shows all five status keys should always be present.
**Fix:** Changed to always return all five status keys (`approved`, `phase_3`, `phase_2`, `phase_1`, `investigative`) defaulting to 0.

## Known Acceptable Deviations

1. **Text search uses LIKE, not FULLTEXT MATCH...AGAINST** -- FULLTEXT indexes are created but queries use `LIKE '%term%'`. This is a documented simplification; LIKE is sufficient at current scale (~50 ADCs).

2. **RDKit deprecation warning** -- `GetMorganFingerprintAsBitVect` shows a deprecation warning suggesting `MorganGenerator`. The current API still works correctly and the parameters match (radius=2, nbits=2048).

3. **POST /api/v1/adcs exists but is not in the plan** -- The create endpoint is implemented in the adcs router. This is a reasonable addition for programmatic data entry.

## Files Modified

- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/app/models/antigen.py` -- removed unused import
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/app/routers/antibodies.py` -- removed unused import
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/app/routers/antigens.py` -- removed unused import
- `/Users/egkim/Developer/arontier-egkim/adcdb/backend/app/routers/stats.py` -- fixed pipeline response format
