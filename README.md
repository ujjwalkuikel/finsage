# AI Investment Intelligence Platform (AII Platform)

An investment copilot that combines **agentic AI** (LLM agents that research,
remember, and explain) with **algorithmic trading** (a deterministic engine that
computes, validates, sizes, and executes). Core principle: **LLMs reason,
software calculates, and risk is owned by code — never by an AI.**

## Read the docs first
Everything is in `docs/`, written so anyone can follow it:

1. `docs/00_Start_Here.md` — orientation
2. `docs/01_Project_Overview.md` — vision, philosophy, all features (two tiers)
3. `docs/02_System_Architecture.md` — layers, stack, frontend direction
4. `docs/03_Data_Sources.md` — every data/broker decision and cost
5. `docs/04_Build_Roadmap.md` — phased build order
6. `docs/05_Strategies_and_Validation.md` — strategies + the testing gauntlet

## Run the engine (works today, no installs needed)
```bash
cd backend
python run_sim.py                  # runs a simulation, populates the ledger
pip install -r requirements.txt
uvicorn app.api.main:app --reload      # API + minimal dashboard at http://127.0.0.1:8000
```

## Run the React frontend (clean dashboard)
```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173 (proxies /api to the backend)
```

## Status
Phase 1 (deterministic spine) is working: strategy engine, simulated execution,
ledger, minimal dashboard. See the roadmap for what's next.
