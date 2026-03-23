# Frontend Verification Report

## Summary

Read all 18 source files in `frontend/src/`, plus `package.json`, `vite.config.ts`, `tsconfig.app.json`, and `index.html`. Verified against `plans/frontend.md` and `_workspace/02_api_spec.md`. The codebase was largely correct and well-structured. Found and fixed 4 issues; TypeScript compiles cleanly after all changes.

## Checklist (Plan Compliance)

| Item | Status |
|------|--------|
| Routes match plan (/, /browse, /search, /about, /adc/:id, /antibody/:id, /antigen/:id, /linker/:id, /payload/:id, *) | OK |
| Layout: sticky nav with backdrop blur, Outlet, footer | OK |
| Home: fetches /stats, displays total_adcs, top_antigens, pipeline | OK |
| Browse: status filter, table with links | OK (enhanced with `q` search) |
| Search: 3 tabs (text, structure, sequence) | OK |
| ADCDetail: fetches /adcs/{id}, shows components, activities, lazy MolViewer | OK |
| AntibodyDetail: fetches antibody + /adcs via Promise.all | OK (added light chain) |
| AntigenDetail: fetches antigen + /adcs | OK |
| LinkerDetail: fetches linker + /adcs, MoleculeDrawing after properties | OK |
| PayloadDetail: fetches payload + /adcs, MoleculeDrawing (skips SMILES="C") | OK |
| About: static content | OK |
| NotFound: 404 with link to home | OK |
| MolViewer: lazy-loaded, createPluginUI with React 18 render callback | OK |
| MolViewer: regionState left/top/right hidden, bottom full | OK |
| MolViewer: imports light.scss, error fallback with download link | OK |
| MoleculeDrawing: ACS1996 details (all 7 params match plan exactly) | OK |
| MoleculeDrawing: cleans [*:n] to [H], zoomable=true, 400x300 | OK |
| RDKit WASM files in public/ (rdkit-worker, RDKit_minimal.js, .wasm) | OK |
| RDKitProvider wraps Routes in App.tsx | OK |
| Blue theme HSL variables (primary 221.2 83.2% 53.3%) | OK |
| Tailwind CSS v4 with @tailwindcss/vite plugin | OK |
| @theme inline block for color tokens | OK |
| Geist font in src/fonts/ | OK |
| Path alias @/ -> src/ in vite.config.ts and tsconfig.app.json | OK |
| cn() utility (clsx + tailwind-merge) | OK |
| sass-embedded in devDependencies (for Mol* SCSS) | OK |
| No SSR, no state management library, useState+useEffect pattern | OK |
| API base from VITE_API_URL env with localhost:8001 default | OK |

## Issues Found and Fixed

### 1. ADC interface missing fields (api.ts)

The `ADC` TypeScript interface was missing `antibody_id`, `linker_id`, `payload_id`, and `linker_payload_smiles` fields that are present in the API spec's `ADCRead` response schema. Added all four fields.

### 2. Linker and Payload interfaces missing fields (api.ts)

Both `Linker` and `Payload` interfaces were missing `inchi`, `inchikey`, and `iupac_name` fields that the API returns. Added all three fields to each interface.

### 3. AntibodyDetail missing light chain sequence (AntibodyDetail.tsx)

The page only displayed the heavy chain sequence. Added a section to display the light chain sequence when available, matching the same style as the heavy chain section.

### 4. Browse page missing name search (Browse.tsx)

The API supports a `q` query parameter for name filtering on `GET /adcs`, but the Browse page had no search input. Added a text input that reads/writes the `q` search parameter, and included `q` in the API fetch URL and the useEffect dependency array.

### 5. Search page structure result link fallback (Search.tsx)

The fallback type for structure similarity results was `"antibody"`, but structure search returns linker/payload results. Changed the fallback to use `"payload"` for the structure tab and `"antibody"` for the sequence tab.

## Files Modified

- `frontend/src/lib/api.ts` -- Added missing fields to ADC, Linker, Payload interfaces
- `frontend/src/pages/AntibodyDetail.tsx` -- Added light chain sequence display
- `frontend/src/pages/Browse.tsx` -- Added name search input with `q` param support
- `frontend/src/pages/Search.tsx` -- Fixed structure result link fallback type

## Compilation

TypeScript compiles cleanly with zero errors after all changes (`npx tsc -b --noEmit` produces no output).
