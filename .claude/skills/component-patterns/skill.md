---
name: component-patterns
description: "React component design pattern library. Provides Compound/Render Props/HOC/Custom Hooks patterns, state management strategies, and folder structure conventions as a frontend-dev extension skill. Use for requests like 'component patterns', 'React patterns', 'state management', 'folder structure', 'Custom Hook', 'component separation'."
---

# Component Patterns — React Component Design Patterns

A reference for component patterns, state management strategies, and project structure that the frontend-dev agent uses during frontend development.

## Target Agent

`frontend-dev` — Applies this skill's patterns directly to component design and state management.

## Component Design Patterns

### 1. Compound Components
Parent and child share implicit state. Suited for: Tab, Accordion, Dropdown, Select.

### 2. Custom Hooks (Extraction Pattern)
Extracts state logic into reusable Hooks. Naming: `use` prefix — `useSearch`, `useMolViewer`, `useADCData`.

### 3. Container/Presentational Separation
Separates data logic from UI presentation. Suited for large-scale apps and testability.

### 4. Headless Component
Provides behavior/state without UI. Suited for sharing logic independent of design system.

## State Management Strategy

| State Type | Recommended Tool | Rationale |
|-----------|-----------------|-----------|
| UI Local State | useState, useReducer | Component-internal |
| Server State | fetch + useEffect (or React Query) | API data |
| URL State | useSearchParams | Filters, pagination |
| Form State | React Hook Form + Zod | Integrated validation |

## Performance Optimization Patterns

| Pattern | When | Tool |
|---------|------|------|
| Memoization | Expensive computation | `useMemo`, `React.memo` |
| Lazy Loading | Initial bundle size | `React.lazy` |
| Virtualization | 1000+ item lists | `@tanstack/react-virtual` |
| Debounce | Search, input | Custom hook |

## Error Handling Patterns

| HTTP Status | Client Handling |
|------------|----------------|
| 404 | Not Found page |
| 422 | Per-field form error display |
| 500 | Generic error UI + retry button |

## Accessibility (a11y) Checklist

- [ ] Alt text on all images
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] ARIA labels
- [ ] Color contrast 4.5:1 or above
- [ ] Semantic HTML
