# =============================================================================
# BYTEGrader Configuration for Docker Deployment
# This file is mounted into the bytegrader container
# =============================================================================

import os
from traitlets.config import get_config

from bytegrader.config.config import (
    BYTEGraderConfig,
    LTIConfig,
    LTISyncTaskConfig,
    DatabaseConfig,
    AutogradeConfig
)

c = get_config()

# =============================================================================
# Database Configuration
# =============================================================================

db_config = DatabaseConfig()

# Get database URI from environment variable
db_uri = os.environ.get('BYTEGRADER_DB_URI')
if db_uri:
    db_config.uri = db_uri
else:
    # Fallback to SQLite for development
    db_config.uri = "sqlite:///bytegrader.db"

db_config.echo = os.environ.get('BYTEGRADER_DB_ECHO', 'false').lower() == 'true'
db_config.asset_path = os.environ.get('BYTEGRADER_ASSET_PATH', '/app/assets')

c.BYTEGraderConfig.database = db_config

# =============================================================================
# LTI Configuration
# =============================================================================

lti = LTIConfig()

lti.enabled = os.environ.get('LTI_ENABLED', 'true').lower() == 'true'
lti.lms_url = os.environ.get('LTI_LMS_URL', 'http://moodle:8080')
lti.token_url = os.environ.get('LTI_TOKEN_URL', 'http://moodle:8080/mod/lti/token.php')
lti.client_id = os.environ.get('LTI_CLIENT_ID', 'bytegrader-lti-client')
lti.key_path = os.environ.get('LTI_KEY_PATH', '/app/keys/private.pem')
lti.platform = os.environ.get('LTI_PLATFORM', 'moodle')
lti.lti_url = os.environ.get('LTI_LTI_URL', 'http://moodle:8080/mod/lti/services.php')
lti.nrps_url = os.environ.get('LTI_NRPS_URL', 'http://moodle:8080/mod/lti/services.php')

# LTI Sync Task
lti.sync_task = LTISyncTaskConfig()
lti.sync_task.enabled = os.environ.get('LTI_SYNC_ENABLED', 'true').lower() == 'true'
lti.sync_task.interval = os.environ.get('LTI_SYNC_INTERVAL', '5m')

c.BYTEGraderConfig.lti = lti

# =============================================================================
# Autograde Configuration
# =============================================================================

autograde = AutogradeConfig()

autograde.enabled = os.environ.get('AUTOGRADE_ENABLED', 'true').lower() == 'true'
autograde.workers = int(os.environ.get('AUTOGRADE_WORKERS', '4'))
autograde.cooldown_period = os.environ.get('AUTOGRADE_COOLDOWN', '5m')
autograde.executor_class = os.environ.get(
    'AUTOGRADE_EXECUTOR',
    'bytegrader.autograde.executors.simple.SimpleExecutor'
)

c.BYTEGraderConfig.autograde = autograde

# =============================================================================
# Logging
# =============================================================================

import logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('DEBUG', 'false').lower() == 'true' else logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s'
)
