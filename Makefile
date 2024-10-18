install:
	poetry install

test:
	poetry run pytest

lint:
	poetry run flake8 chat

dev:
	redis-server & uvicorn chat.main:app --reload