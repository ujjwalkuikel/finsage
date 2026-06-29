# Frontend — AII Platform

Clean white dashboard (Tsenta-style) in React + Vite + Tailwind. Talks to the
FastAPI backend; the dev server proxies `/api` to `http://127.0.0.1:8000`.

## Run
```bash
# 1) start the backend first (in ../backend):
#    uvicorn app.api.main:app --reload
# 2) then, here:
npm install
npm run dev          # opens http://localhost:5173
```

## Structure
- `src/App.jsx` — dashboard page (header, stat cards, trades table)
- `src/components/` — Sidebar, StatCard, TradesTable
- `src/lib/api.js` — backend client

## Notes
- shadcn/ui components can be added incrementally (`npx shadcn@latest add card table`)
  — the current components are hand-rolled in the same visual language so the app
  runs immediately without the shadcn setup step.
- Design tokens (colors, fonts) live in `tailwind.config.js`. Numbers use a
  monospace with tabular figures — the ledger/ticker signature from docs/02 §6.
