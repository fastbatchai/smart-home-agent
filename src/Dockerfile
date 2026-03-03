FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install the application dependencies
COPY uv.lock pyproject.toml README.md ./
COPY src src

# Sync dependencies and install the package (this happens during build, not runtime)
RUN uv sync --frozen --no-cache

COPY .env .env

CMD ["uv", "run", "python", "src/main.py", "--port", "8001", "--host", "0.0.0.0"]
