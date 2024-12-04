install:
	poetry install

test:
	poetry run pytest

lint:
	ruff check && ruff format --check

fmt:
	ruff check --fix && ruff format

dev:
	redis-server & fastapi dev chat/api.py