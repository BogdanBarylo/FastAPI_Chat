install:
	poetry install

test:
	poetry run pytest

lint:
	poetry run ruff check && poetry run ruff format --check

fmt:
	ruff check --fix && ruff format

dev:
	redis-server & fastapi dev chat/api.py