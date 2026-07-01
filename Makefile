.PHONY: install browser run test lint docker-up docker-down

install:
	python -m pip install -e ".[dev]"

browser:
	playwright install chromium

run:
	uvicorn app.main:app --reload

test:
	pytest -q

lint:
	ruff check .

docker-up:
	docker compose up --build

docker-down:
	docker compose down
