FROM python:3.11-slim

WORKDIR /app
COPY app.py .

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization:
# 1. Disable virtualenv creation (we are already in a container)
# 2. Install dependencies (no-interaction, no-ansi for cleaner logs)
RUN poetry config virtualenvs.create false \
      && poetry install --no-interaction --no-ansi --no-root

# Copy app code
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

