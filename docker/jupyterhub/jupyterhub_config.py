# =============================================================================
# JupyterHub Configuration for BYTEGrader
# Configured for LTI authentication and Docker spawning
# =============================================================================

import os
import json
import sys

# =============================================================================
# Core JupyterHub Configuration
# =============================================================================

c = get_config()  # noqa: F821

# Network configuration
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = '0.0.0.0'

# Generate a unique key for cookie signing if not provided
c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/jupyterhub_cookie_secret'

# Proxy configuration
c.ConfigurableHTTPProxy.should_start = True
c.ConfigurableHTTPProxy.auth_token = os.environ.get('CONFIGPROXY_AUTH_TOKEN', '')

# Database for persistent state
db_url = os.environ.get('JUPYTERHUB_DB_URL', 'sqlite:///jupyterhub.sqlite')
if db_url.startswith('postgresql://'):
    c.JupyterHub.db_url = db_url
else:
    c.JupyterHub.db_url = 'sqlite:////srv/jupyterhub/jupyterhub.sqlite'

# =============================================================================
# Authentication Configuration
# =============================================================================

# Try to load LTI configuration from the shared volume
lti_config_path = '/srv/jupyterhub/lti-config/lti_tool_config.json'
use_lti_auth = False

if os.path.exists(lti_config_path):
    try:
        with open(lti_config_path, 'r') as f:
            lti_config = json.load(f)
        use_lti_auth = True
        print(f"[INFO] Loaded LTI configuration from {lti_config_path}")
    except Exception as e:
        print(f"[WARNING] Failed to load LTI config: {e}")
        lti_config = {}
else:
    print(f"[INFO] LTI config not found at {lti_config_path}, using native authenticator")
    lti_config = {}

if use_lti_auth and lti_config.get('client_id'):
    # Use LTI 1.3 Authenticator
    from ltiauthenticator.lti13.auth import LTI13Authenticator
    
    c.JupyterHub.authenticator_class = LTI13Authenticator
    
    # LTI 1.3 Configuration
    c.LTI13Authenticator.issuer = lti_config.get('issuer', os.environ.get('LTI_ISSUER', 'http://moodle:8080'))
    c.LTI13Authenticator.client_id = [lti_config.get('client_id', os.environ.get('LTI_CLIENT_ID', ''))]
    c.LTI13Authenticator.authorize_url = lti_config.get('authorize_url', os.environ.get('LTI_AUTHORIZE_URL', ''))
    c.LTI13Authenticator.token_url = lti_config.get('token_url', os.environ.get('LTI_TOKEN_URL', ''))
    c.LTI13Authenticator.jwks_endpoint = lti_config.get('jwks_url', os.environ.get('LTI_JWKS_URL', ''))
    
    # Username claim from LTI
    c.LTI13Authenticator.username_key = 'preferred_username'
    
    # Allow all users authenticated via LTI
    c.Authenticator.allow_all = True
    
    print("[INFO] LTI 1.3 Authenticator configured")
else:
    # Fallback to Native Authenticator for development/testing
    from nativeauthenticator import NativeAuthenticator
    
    c.JupyterHub.authenticator_class = NativeAuthenticator
    c.NativeAuthenticator.open_signup = True
    c.NativeAuthenticator.minimum_password_length = 6
    c.NativeAuthenticator.check_common_password = False
    
    # Create admin user
    c.Authenticator.admin_users = {'admin'}
    c.Authenticator.allowed_users = {'admin'}
    c.Authenticator.allow_all = True
    
    print("[INFO] Native Authenticator configured (fallback)")

# =============================================================================
# Docker Spawner Configuration
# =============================================================================

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Docker network - must match the docker-compose network
c.DockerSpawner.network_name = os.environ.get('DOCKER_NETWORK_NAME', 'bytegrader-network')

# Use internal Docker network IP
c.DockerSpawner.use_internal_ip = True

# Notebook image
c.DockerSpawner.image = os.environ.get('DOCKER_NOTEBOOK_IMAGE', 'quay.io/jupyter/base-notebook:latest')

# Container naming
c.DockerSpawner.name_template = 'jupyter-{username}'

# Remove containers when stopped
c.DockerSpawner.remove = True

# Notebook directory inside container
notebook_dir = '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir

# Volumes for user data persistence
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': notebook_dir
}

# Environment variables for spawned containers
c.DockerSpawner.environment = {
    'BYTEGRADER_SERVICE_URL': os.environ.get('BYTEGRADER_SERVICE_URL', 'http://bytegrader:12345'),
    'GRANT_SUDO': 'no',
}

# Resource limits (optional, adjust as needed)
# c.DockerSpawner.mem_limit = '2G'
# c.DockerSpawner.cpu_limit = 1.0

# Debug mode for spawner
c.DockerSpawner.debug = True

# =============================================================================
# BYTEGrader Service Configuration
# =============================================================================

bytegrader_service_url = os.environ.get('BYTEGRADER_SERVICE_URL', 'http://bytegrader:12345')
bytegrader_api_token = os.environ.get('BYTEGRADER_SERVICE_TOKEN', '')

c.JupyterHub.services = [
    {
        'name': 'bytegrader',
        'url': bytegrader_service_url,
        'api_token': bytegrader_api_token,
    }
]

# Service tokens
if bytegrader_api_token:
    c.JupyterHub.service_tokens = {
        bytegrader_api_token: 'bytegrader'
    }

# =============================================================================
# Security Configuration
# =============================================================================

# Allow named servers
c.JupyterHub.allow_named_servers = False

# Shutdown servers on logout
c.JupyterHub.shutdown_on_logout = False

# Timeout configurations
c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 60

# Idle culler (optional)
# c.JupyterHub.services.append({
#     'name': 'idle-culler',
#     'command': [
#         sys.executable,
#         '-m', 'jupyterhub_idle_culler',
#         '--timeout=3600'
#     ],
# })

# =============================================================================
# Logging Configuration
# =============================================================================

c.JupyterHub.log_level = 'DEBUG'
c.Spawner.debug = True
c.DockerSpawner.debug = True

print("[INFO] JupyterHub configuration loaded successfully")
