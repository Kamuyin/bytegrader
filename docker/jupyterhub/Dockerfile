# =============================================================================
# JupyterHub Dockerfile for BYTEGrader deployment
# Includes LTI Authenticator and DockerSpawner
# =============================================================================

FROM quay.io/jupyterhub/jupyterhub:5

LABEL maintainer="BYTEGrader Team"
LABEL description="JupyterHub configured for BYTEGrader with LTI authentication"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    jupyterhub-ltiauthenticator>=1.6.0 \
    dockerspawner>=13.0.0 \
    psycopg2-binary \
    oauthenticator \
    jupyterhub-nativeauthenticator

# Create directories
RUN mkdir -p /srv/jupyterhub/keys /srv/jupyterhub/lti-config

# Copy configuration
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

WORKDIR /srv/jupyterhub

# Expose JupyterHub port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/hub/health || exit 1

# Default command
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
