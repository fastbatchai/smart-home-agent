FROM python:3.10-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install the application dependencies
COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen --no-cache --group device-api

COPY data data 
COPY device_service/ smarthome-device

CMD ["uv", "run", "python", "smarthome-device/device_service.py", "--port", "8000", "--host", "0.0.0.0"]