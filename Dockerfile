# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Fail fast and keep the image clean and reproducible.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy only what the build needs so the layer cache stays stable.
COPY pyproject.toml README.md ./
COPY src ./src

# Install the runtime package (no dev extras) and drop to an unprivileged user.
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser

USER appuser

ENTRYPOINT ["asset-manager"]
CMD ["--help"]
