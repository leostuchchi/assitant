.PHONY: run test install update

run:
	cd backend && python -m uvicorn api_entrypoint:app --host 0.0.0.0 --port 8000 --reload

test:
	cd backend && python test_api.py

install:
	pip install -r requirements.txt

update-db:
	cd backend && python update_database.py

fix-db:
	cd backend && python database_fixes.py

monitor:
	cd backend && python database_monitor.py
