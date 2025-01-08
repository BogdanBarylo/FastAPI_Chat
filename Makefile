install:
	poetry install

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov=chat --cov-report=xml --cov-report=term-missing

lint:
	poetry run ruff check && poetry run ruff format --check

lint-mypy:
	poetry run mypy chat

fmt:
	ruff check --fix && ruff format

dev:
	redis-server & fastapi dev chat/api.py