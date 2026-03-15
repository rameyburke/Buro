# Vite Migration Session (2026-03-15)

## Goal

Convert the frontend from Create React App (`react-scripts`) to Vite on a dedicated branch with minimal disruption to backend static serving, CI, and existing project workflows.

## Branch

- Created: `agent/migrate-react-to-vite`

## User Requests Captured

1. Plan a low-disruption React-to-Vite migration in a new branch.
2. Provide an exact execution checklist.
3. Implement the plan.
4. Export this feature session as markdown.

## What Changed

- Added Vite build tooling and React plugin.
- Preserved script names (`start`, `build`, `build:fast`) to reduce workflow disruption.
- Kept output compatibility for backend serving:
  - `outDir: build`
  - `assetsDir: static`
- Migrated HTML entry from CRA `public/index.html` to Vite root `index.html`.
- Switched app bootstrap entrypoint from `src/index.tsx` to `src/main.tsx`.
- Updated env handling for Vite with temporary CRA fallback:
  - `import.meta.env.VITE_API_URL`
  - fallback `process.env.REACT_APP_API_URL`
- Updated CI frontend build env key to `VITE_API_URL`.
- Updated README wording from CRA dev server to Vite dev server and clarified build output path.
- Added `vitest.config.ts` and constrained unit-test discovery to `src/**/*.{test,spec}.{ts,tsx}` to avoid colliding with Playwright e2e specs.

## Files Touched for Migration

- `.github/workflows/e2e.yml`
- `README.md`
- `frontend/.env`
- `frontend/index.html` (new)
- `frontend/package.json`
- `frontend/public/index.html` (deleted)
- `frontend/src/index.tsx` (deleted)
- `frontend/src/lib/api.ts`
- `frontend/src/main.tsx` (new)
- `frontend/tsconfig.json`
- `frontend/vite.config.ts` (new)
- `frontend/vitest.config.ts` (new)
- `frontend/package-lock.json` (dependency refresh)

## Commands Run

- `git status --short --branch`
- `git checkout -b agent/migrate-react-to-vite`
- `npm install` (frontend dependency migration)
- `npm run test` (Vitest; passWithNoTests)
- `npm run build` (Vite production build)

## Verification Results

- `npm run test`: passes with no unit tests found (expected, code 0).
- `npm run build`: successful; output generated in `frontend/build` with assets in `frontend/build/static`.

## Notes

- The repository already had unrelated uncommitted changes before migration; those were preserved.
- Root-level `package.json`/`package-lock.json` still reference `react-scripts`; this migration is scoped to `frontend/` to minimize disruption and avoid cross-project changes.
