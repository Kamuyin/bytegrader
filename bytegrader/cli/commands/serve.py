import os
import sys
from typing import Optional, Any
from urllib.parse import urlparse

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from traitlets.config import Application, PyFileConfigLoader
from traitlets import Unicode, Int

from bytegrader.config.config import BYTEGraderConfig
from bytegrader.hub import BYTEGraderHubApp
from bytegrader.core.observability import (
    capture_exception,
    init_observability,
    set_span_attributes,
)


class ServeCommand(Application):
    name = "bytegrader serve"
    description = "Start the BYTE Grader JupyterHub service."

    config_file = Unicode(
        "bytegrader_config.py",
        help="Path to the BYTE Grader service configuration file."
    ).tag(config=True)

    host = Unicode(
        "localhost",
        help="Host to bind the server to."
    ).tag(config=True)

    port = Int(
        12345,
        help="Port to bind the server to."
    ).tag(config=True)

    aliases = {
        "config": "ServeCommand.config_file",
        "host": "ServeCommand.host",
        "port": "ServeCommand.port"
    }

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.bgconfig = None

    def initialize(self, argv: Optional[list] = None):
        super().initialize(argv)

        try:
            config_loader = PyFileConfigLoader(self.config_file)
            config = config_loader.load_config()
            self.update_config(config)
        except Exception as e:
            self.log.error(f"Failed to load configuration file '{self.config_file}': {e}")
            capture_exception(
                e,
                tags={
                    "component": "serve_command",
                    "stage": "load_config",
                },
                extra={
                    "config_file": self.config_file,
                }
            )
            raise

        self.bgconfig = BYTEGraderConfig(parent=self)

    def start(self) -> None:
        tornado_app = None

        try:
            observability_state = init_observability(self.log)
            enabled = [name for name, active in observability_state.items() if active]
            if enabled:
                self.log.info("Observability backends enabled: %s", ", ".join(enabled))
            else:
                self.log.info("No observability backends configured.")
            set_span_attributes(
                {
                    "service.component": "serve_command",
                    "service.host": self.host,
                    "service.port": self.port,
                    "service.config_file": self.config_file,
                    "service.observability.enabled_backends": ",".join(enabled) if enabled else "",
                }
            )
        except Exception as e:
            self.log.warning("Observability initialisation failed: %s", e)
            capture_exception(
                e,
                tags={
                    "component": "serve_command",
                    "stage": "init_observability",
                }
            )

        try:
            self.log.debug("Starting BYTE Grader service with configuration: %s", self.bgconfig)
            hub_app = BYTEGraderHubApp(config=self.bgconfig)

            srv_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "")

            tornado_app = hub_app.create_tornado_app(srv_prefix)

            service_url = os.environ.get("JUPYTERHUB_SERVICE_URL")
            if service_url:
                url = urlparse(service_url)
                http_server = HTTPServer(tornado_app)
                http_server.listen(url.port, address=url.hostname)
                self.log.info(f"ByteGrader server starting at {service_url}")
            else:
                http_server = HTTPServer(tornado_app)
                http_server.listen(self.port, address=self.host)
                self.log.info(f"ByteGrader server starting at http://{self.host}:{self.port}")

            IOLoop.current().start()

        except KeyboardInterrupt:
            self.log.info("Shutting down BYTE Grader service...")
            if tornado_app and tornado_app.settings.get("db_mgr"):
                tornado_app.settings.get("db_mgr").close()
        except Exception as e:
            self.log.error(f"An error occurred while starting the BYTE Grader service: {e}")
            capture_exception(
                e,
                tags={
                    "component": "serve_command",
                    "stage": "run",
                }
            )
            sys.exit(-1)
