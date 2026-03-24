FRONTEND_BUILD_PATH ?= $(CURDIR)/frontend/build
HOST ?= 127.0.0.1
PORT ?= 8000

.PHONY: frontend-build db dev

frontend-build:
	npm run build --prefix frontend

db:
	poetry run python scripts/create_tables.py

dev: frontend-build db
	FRONTEND_BUILD_PATH="$(FRONTEND_BUILD_PATH)" poetry run uvicorn buro.main:app --host $(HOST) --port $(PORT)
