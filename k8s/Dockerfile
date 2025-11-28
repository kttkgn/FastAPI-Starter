# Use official Python image as base
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PATH="/opt/poetry/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Verify Poetry installation
RUN poetry --version

# Copy poetry.lock and pyproject.toml files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --only main

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.py

# Create logs directory
RUN mkdir -p logs

# Run as non-root user for security
RUN useradd -m appuser
USER appuser

# Set environment variables for production
ENV APP_ENV=prod \
    HOST=0.0.0.0 \
    PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["poetry", "run", "python", "scripts/start_app.py", "--env", "prod", "--host", "0.0.0.0", "--port", "8000"]

# Alternative command with uvicorn directly (if preferred)
# CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Labels for metadata
LABEL maintainer="Your Name <your.email@example.com>" \
      description="FastAPI application container" \
      version="1.0.0"