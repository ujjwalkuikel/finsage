.PHONY: sim serve test web install-deps

ifeq ($(OS),Windows_NT)
    PYTHON = ../.venv/Scripts/python
    UVICORN = ../.venv/Scripts/uvicorn
else
    PYTHON = ../.venv/bin/python
    UVICORN = ../.venv/bin/uvicorn
endif

sim:
	cd backend && $(PYTHON) run_sim.py

serve:
	cd backend && $(UVICORN) app.api.main:app --reload

test:
	cd backend && $(PYTHON) -m pytest tests/

web:
	cd frontend && npm run dev

install-deps:
	uv venv
	uv pip install -r backend/requirements.txt
	cd frontend && npm install
