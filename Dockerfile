FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml .

COPY poetry.lock .

COPY chat/ ./chat/

COPY Makefile .

RUN poetry install --without dev --no-interaction --no-ansi

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "chat.api:app", "--host", "0.0.0.0", "--port", "8000"]
