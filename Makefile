.PHONY: up down logs test lint smoke

up:
	docker compose up -d --build --wait

down:
	docker compose down -v

logs:
	docker compose logs -f api audio_extractor transcriber analyzer

test:
	pytest

lint:
	ruff check .

smoke:
	python scripts/smoke_test.py
