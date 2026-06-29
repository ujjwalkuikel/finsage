.PHONY: sim serve test web install-deps

sim:
	cd backend && python run_sim.py

serve:
	cd backend && uvicorn app.api.main:app --reload

test:
	cd backend && python -m pytest tests/

web:
	cd frontend && npm run dev

install-deps:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
