# Frontend Agent — React + Vite + shadcn/ui

## Execution Steps

1. **Scaffold Vite project:** `npm create vite@latest frontend -- --template react-ts && cd frontend && npm install`
2. **Install deps:** `npm install react-router molstar @iktos-oss/rdkit-provider @iktos-oss/molecule-representation clsx tailwind-merge class-variance-authority tailwindcss-animate lucide-react sass-embedded tailwindcss @tailwindcss/vite`
3. **Configure Vite:** `vite.config.ts` — add `@tailwindcss/vite` plugin, path alias `@ → src/`.
4. **Configure TypeScript:** `tsconfig.app.json` — add `paths: { "@/*": ["./src/*"] }`.
5. **Create `src/globals.css`:** Blue theme HSL variables (primary `221.2 83.2% 53.3%`), `@font-face` for Geist, `@import "tailwindcss"`, `@plugin "tailwindcss-animate"`, `@theme inline` block for all color tokens.
6. **Copy font:** `GeistVF.woff` into `src/fonts/`.
7. **Copy RDKit WASM files to `public/`:**
   - `cp node_modules/@iktos-oss/rdkit-provider/lib/rdkit-worker-*.js public/`
   - `cp node_modules/@rdkit/rdkit/dist/RDKit_minimal.js public/`
   - `cp node_modules/@rdkit/rdkit/dist/RDKit_minimal.wasm public/`
8. **Create `src/lib/api.ts`:** `apiFetch` function using `import.meta.env.VITE_API_URL` (default `http://localhost:8001/api/v1`). Define all TypeScript interfaces: `ADC`, `ADCListItem`, `Antibody`, `Antigen`, `Linker`, `Payload`, `Activity`, `Stats`.
9. **Create `src/lib/utils.ts`:** `cn()` function (clsx + tailwind-merge).
10. **Create `src/components/Layout.tsx`:** Nav bar (ADCDB, Browse, Search, About) using React Router `<Link>` + `<Outlet>` + footer. Sticky header with backdrop blur.
11. **Create `src/main.tsx`:** `createRoot` + `<BrowserRouter>` + `<App />`, import `globals.css`.
12. **Create `src/App.tsx`:** Wrap `<Routes>` in `<RDKitProvider>`. Define all routes with `<Route element={<Layout />}>` wrapper. Import all page components.
13. **Create pages** in `src/pages/`:
    - `Home.tsx` — `useEffect` fetches `/stats`, shows total ADCs, top antigens, pipeline
    - `Browse.tsx` — `useSearchParams` for status filter, fetches `/adcs`, renders table
    - `Search.tsx` — 3 tabs (text/structure/sequence), fetches `/search`, `/search/structure`, `/search/sequence`
    - `ADCDetail.tsx` — `useParams` for id, fetches `/adcs/{id}`, shows components, activities, lazy-loads `MolViewer`
    - `AntibodyDetail.tsx` — fetches antibody + linked ADCs via `Promise.all`
    - `AntigenDetail.tsx` — fetches antigen + linked ADCs
    - `LinkerDetail.tsx` — fetches linker + linked ADCs, shows `MoleculeDrawing` after properties box
    - `PayloadDetail.tsx` — fetches payload + linked ADCs, shows `MoleculeDrawing` after properties box (skip if SMILES is `"C"` placeholder)
    - `About.tsx` — static content
    - `NotFound.tsx` — 404 with link to home
14. **Create `src/components/MolViewer.tsx`:** Mol* `createPluginUI` with `render: (component, element) => createRoot(element!).render(component)`. Layout: `showControls: true`, `regionState: { left: "hidden", top: "hidden", right: "hidden", bottom: "full" }` (sequence panel). Import `molstar/lib/mol-plugin-ui/skin/light.scss`. Fetches PDB from `/adcs/{id}/structure`. Shows fallback with download link on error.
15. **Create `src/components/MoleculeDrawing.tsx`:** `<MoleculeRepresentation>` with ACS1996 `details` prop (`bondLineWidth: 0.6, scaleBondWidth: false, fixedBondLength: 14.4, additionalAtomLabelPadding: 0.066, multipleBondOffset: 0.18, annotationFontScale: 0.5, minFontSize: 6, maxFontSize: 40`), `zoomable={true}`, 400x300 canvas. Cleans `[*:1]`/`[*:2]` → `[H]` before rendering.
16. **Update `index.html`:** Title "ADCDB", meta description.
17. **Clean up:** Delete Vite template files (`App.css`, `index.css`, `assets/`).
18. **Verify:** `npm run dev` → open `http://localhost:5173`, check homepage loads stats, browse shows ADCs, detail pages show 3D viewer and 2D drawings.

## Overview

SPA (no SSR). Blue theme. Mol* for 3D structures. RDKit WASM for 2D molecule drawings.

## Dependencies

- `react` 18 + `vite` — SPA framework
- `react-router` v7 — client-side routing
- `shadcn/ui` — component library (blue primary color, HSL `221.2 83.2% 53.3%`)
- `molstar` — 3D molecular viewer
- `@iktos-oss/rdkit-provider` + `@iktos-oss/molecule-representation` — 2D molecule rendering from SMILES via RDKit WASM
- `sass-embedded` — required by Mol* SCSS skin
- `clsx` + `tailwind-merge` + `class-variance-authority` — shadcn utilities

## Key Design Decisions

1. **SPA, not SSR** — Mol* v5 calls React internally. Next.js 14's SSR creates a React runtime conflict (`render is not a function`). Plain React + Vite = one React runtime = Mol* works.
2. **No state management library** — URL params (via `useSearchParams`) for search state, React state for UI.
3. **API calls via `fetch`** in `useEffect` — no axios, no SWR, no react-query. Simple `useState` + `useEffect` pattern for all data fetching.
4. **Mol* lazy-loaded** — `React.lazy(() => import('./MolViewer'))` + `<Suspense>`. It's heavy (~2MB), only load on ADC detail page.
5. **No CORS proxy needed** — Backend has CORSMiddleware. Frontend fetches directly from `http://localhost:8001`.

## Mol* 3D Viewer

**Component:** `src/components/MolViewer.tsx`

Uses `createPluginUI` from `molstar/lib/mol-plugin-ui` with React 18 render callback:

```tsx
const plugin = await createPluginUI({
  target: containerRef.current,
  spec: {
    ...DefaultPluginUISpec(),
    layout: {
      initial: {
        isExpanded: false,
        showControls: true,
        regionState: {
          left: "hidden",
          top: "hidden",
          right: "hidden",
          bottom: "full",  // sequence viewer
        },
      },
    },
  },
  render: (component, element) => {
    createRoot(element!).render(component);
  },
});
```

- Loads PDB from `GET /api/v1/adcs/{id}/structure`
- Sequence panel at the bottom — shows amino acid sequences, clickable to highlight in 3D
- Left/top/right panels hidden (no controls clutter)
- Must import `molstar/lib/mol-plugin-ui/skin/light.scss` (requires `sass-embedded`)
- Shows "Structure not yet available" when `structure_3d_path` is NULL

## RDKit WASM 2D Structures

**Component:** `src/components/MoleculeDrawing.tsx`

Uses `<MoleculeRepresentation>` from `@iktos-oss/molecule-representation` wrapped in `<RDKitProvider>` at the app root.

### Setup requirements

Three files must be in `public/` for the Web Worker to load:
- `public/rdkit-worker-2.10.2.js` — copied from `node_modules/@iktos-oss/rdkit-provider/lib/`
- `public/RDKit_minimal.js` — copied from `node_modules/@rdkit/rdkit/dist/`
- `public/RDKit_minimal.wasm` — copied from `node_modules/@rdkit/rdkit/dist/`

### ACS1996 Drawing Style

Exact values from RDKit's `rdMolDraw2D.SetACS1996Mode()`, passed via `details` prop:

```ts
const ACS1996_DETAILS = {
  bondLineWidth: 0.6,
  scaleBondWidth: false,
  fixedBondLength: 14.4,  // 2x ACS1996 default (7.2) for larger rendering
  additionalAtomLabelPadding: 0.066,
  multipleBondOffset: 0.18,
  annotationFontScale: 0.5,
  minFontSize: 6,
  maxFontSize: 40,
};
```

### Features
- `zoomable={true}` — mouse wheel zoom in/out (powered by `@visx/zoom`)
- 2x default scale via `fixedBondLength: 14.4` (double the ACS1996 spec 7.2)
- Canvas size: 400x300
- Linker SMILES with `[*:1]`/`[*:2]` cleaned to `[H]` before rendering
- Used on Linker and Payload detail pages, positioned after the properties box

### SMILES Display
- Monospace font (`font-mono`) for raw SMILES strings
- No forced line breaks — CSS `break-all` handles wrapping naturally

## Routes

| Path | Component | Data Source |
|------|-----------|-------------|
| `/` | `Home` | `GET /api/v1/stats` |
| `/browse` | `Browse` | `GET /api/v1/adcs?status=&q=` |
| `/search` | `Search` | `GET /api/v1/search`, `/search/structure`, `/search/sequence` |
| `/adc/:id` | `ADCDetail` | `GET /api/v1/adcs/{id}` + Mol* viewer |
| `/antibody/:id` | `AntibodyDetail` | `GET /api/v1/antibodies/{id}` + `/{id}/adcs` |
| `/antigen/:id` | `AntigenDetail` | `GET /api/v1/antigens/{id}` + `/{id}/adcs` |
| `/linker/:id` | `LinkerDetail` | `GET /api/v1/linkers/{id}` + `/{id}/adcs` + 2D drawing |
| `/payload/:id` | `PayloadDetail` | `GET /api/v1/payloads/{id}` + `/{id}/adcs` + 2D drawing |
| `/about` | `About` | Static |
| `*` | `NotFound` | Static |

## Page Data Fetching Pattern

All data pages follow the same pattern:

```tsx
const { id } = useParams();
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  apiFetch(`/endpoint/${id}`).then(setData).finally(() => setLoading(false));
}, [id]);
```

For pages with linked ADCs, use `Promise.all` to fetch both in parallel.

## API Client Types

Defined in `src/lib/api.ts`. Key types:

- `ADC` — full detail with nested `Antibody` (with nested `Antigen`), `Linker`, `Payload`, `Activity[]`
- `ADCListItem` — flat: `antibody_name`, `antigen_name`, `linker_name`, `payload_name`
- `Stats` — `total_adcs`, `top_antigens[]`, `top_payload_targets[]`, `pipeline{}`

API base URL from `import.meta.env.VITE_API_URL` (default `http://localhost:8001/api/v1`).

## File Structure

```
frontend/
├── index.html
├── vite.config.ts          # path alias @/ → src/, tailwindcss plugin
├── tsconfig.app.json       # paths: @/* → ./src/*
├── src/
│   ├── main.tsx            # createRoot + BrowserRouter + RDKitProvider
│   ├── App.tsx             # Routes + RDKitProvider wrapper
│   ├── globals.css         # Blue theme HSL vars + @font-face Geist
│   ├── lib/
│   │   ├── api.ts          # apiFetch + all TypeScript interfaces
│   │   └── utils.ts        # cn() (clsx + tailwind-merge)
│   ├── components/
│   │   ├── Layout.tsx      # Nav + Outlet + footer
│   │   ├── MolViewer.tsx   # Mol* 3D viewer (lazy-loaded)
│   │   ├── MoleculeDrawing.tsx  # 2D SMILES→SVG (ACS1996)
│   │   └── ui/             # shadcn primitives
│   ├── pages/
│   │   ├── Home.tsx, Browse.tsx, Search.tsx, About.tsx, NotFound.tsx
│   │   ├── ADCDetail.tsx, AntibodyDetail.tsx, AntigenDetail.tsx
│   │   └── LinkerDetail.tsx, PayloadDetail.tsx
│   └── fonts/
│       └── GeistVF.woff
└── public/
    ├── rdkit-worker-2.10.2.js
    ├── RDKit_minimal.js
    └── RDKit_minimal.wasm
```
