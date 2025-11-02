FROM node:20-slim AS frontend-builder

WORKDIR /app

RUN corepack enable && corepack prepare yarn@stable --activate

COPY package.json tsconfig.json ./
COPY src/ ./src/
COPY style/ ./style/

RUN yarn install --frozen-lockfile || yarn install
RUN yarn build:lib

COPY bytegrader/extensions/ ./bytegrader/extensions/

# Build
FROM python:3.11-slim AS python-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN corepack enable && corepack prepare yarn@3.5.0 --activate

COPY pyproject.toml setup.py requirements.txt ./
COPY bytegrader/ ./bytegrader/
COPY etc/ ./etc/
COPY src/ ./src/
COPY style/ ./style/
COPY package.json tsconfig.json .yarnrc.yml ./
COPY .yarn/ ./.yarn/

RUN pip install --no-cache-dir --upgrade pip wheel setuptools hatchling hatch-jupyter-builder

RUN yarn install --immutable || yarn install
RUN yarn build:lib

RUN pip install --no-cache-dir jupyterlab>=4.2.0

RUN jupyter labextension build . --development False

RUN pip install build && python -m build --wheel

FROM python:3.11-slim AS runtime

LABEL maintainer="Kamuyin"
LABEL description="BYTEGrader - JupyterHub assignment grading service"
LABEL version="0.0.1"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN groupadd -r bytegrader && useradd -r -g bytegrader bytegrader

# Copy the built wheel from builder
COPY --from=python-builder /app/dist/*.whl /tmp/

# Install the wheel and dependencies
RUN pip install --no-cache-dir /tmp/*.whl \
    && pip install --no-cache-dir psycopg2-binary \
    && rm -rf /tmp/*.whl

# Create necessary directories
RUN mkdir -p /app/data /app/assets /app/config \
    && chown -R bytegrader:bytegrader /app

# Copy configuration example
COPY example/bytegrader_config.py /app/config/bytegrader_config.py.example

# Switch to non-root user
USER bytegrader

# Expose the default port
EXPOSE 12345

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:12345/auth/whoami || exit 1

# Default command
CMD ["bytegrader", "serve", "--config=/app/config/bytegrader_config.py"]
