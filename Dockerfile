FROM python:3.13-slim

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Spotify token cache lives on the mounted volume
ENV CACHE_PATH=/data/.cache

WORKDIR /app

# 1. Dependency definitions first so this layer caches
COPY pyproject.toml uv.lock ./

# 2. Install ONLY third-party dependencies
RUN uv export --frozen --no-dev --no-emit-workspace --format requirements-txt -o requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt

# 3. Application source
COPY src/ ./src
COPY README.md ./

# 4. Install the local project without re-downloading dependencies
RUN uv pip install --system --no-cache --no-deps .

# 5. Non-root user; /data is where the token cache is mounted
RUN useradd -m appuser && mkdir -p /data && chown -R appuser:appuser /app /data
USER appuser

CMD ["python", "-m", "spotifylyricstreamer.main"]
