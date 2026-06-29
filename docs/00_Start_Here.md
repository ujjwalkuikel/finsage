# 00 — Start Here

**AI Investment Intelligence Platform (AII Platform)**
Author: Ujjwal Kuikel · Status: Planning + early build · Living documents

---

## What this folder is

This is the design documentation for the platform. It is written so anyone —
you in six months, a collaborator, or an AI coding agent — can understand what
we're building and why, without re-deriving the decisions.

Read in this order:

1. **01_Project_Overview.md** — the vision, the philosophy, and every feature,
   organized into what to build first vs. later. Start here.
2. **02_System_Architecture.md** — how the system is structured (the layers),
   the tech stack, the frontend design direction, and the rules that keep it clean.
3. **03_Data_Sources.md** — every data/broker decision, what each costs, and the
   cheapest combination that covers everything.
4. **04_Build_Roadmap.md** — the phased build order. Each phase is usable on its own.
5. **05_Strategies_and_Validation.md** — the trading strategies and the rigorous
   testing methodology that decides which ones are real.

## The one-line summary

> An investment copilot where **LLMs reason and deterministic software calculates**:
> AI agents research, remember, and explain; a deterministic engine computes
> indicators, validates strategies, sizes positions, and executes — with the human
> in control and risk owned by code, never by an AI.

## The code

The `backend/` folder already contains a working deterministic engine (the
foundation layer). Run it:

```bash
cd backend
python run_sim.py                  # runs a simulation, no installs needed
pip install -r requirements.txt
uvicorn app.main:app --reload      # dashboard at http://127.0.0.1:8000
```

Everything else in these docs builds on top of that engine.
