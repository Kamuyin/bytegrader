from traitlets.config import get_config

from bytegrader.config.config import BYTEGraderConfig, LTIConfig, LTISyncTaskConfig, DatabaseConfig, AutogradeConfig

c = get_config()
db_config = DatabaseConfig()
db_config.uri = "sqlite:///bytegrader.db"
db_config.echo = False
db_config.asset_path = "asset_storage"
c.BYTEGraderConfig.database = db_config

lti = LTIConfig()
lti.enabled = True
lti.lms_url = "http://localhost:7070"
lti.token_url = "http://localhost:7070/mod/lti/token.php"
lti.client_id = "kAMVAJOKfGKhIrQ"
lti.key_path = "./private.pem"
lti.platform = "moodle"
lti.lti_url = "http://localhost:7070/mod/lti/services.php"
lti.nrps_url = "http://localhost:7070/mod/lti/services.php"

lti.sync_task.enabled = True
lti.sync_task.interval = "1m"
c.BYTEGraderConfig.lti = lti

autograde = AutogradeConfig()
autograde.enabled = True
autograde.cooldown_period = "5m"
autograde.executor_class = "bytegrader.autograde.executors.WasmExecutor"
c.BYTEGraderConfig.autograde = autograde
c.WasmExecutor.wasm_path = "/home/akame/bytegrader/testenv/wasm/bin/python-3.11.1.wasm"
c.WasmExecutor.stdlib_path = "/home/akame/bytegrader/testenv/wasm/lib/python3.11"