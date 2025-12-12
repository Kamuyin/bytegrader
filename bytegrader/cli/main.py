import logging
import sys

from traitlets import Unicode
from traitlets.config import Application

from bytegrader.cli.commands.serve import ServeCommand


class BYTEGraderCLI(Application):
    name = "bytegrader"
    description = "BYTE Grader - JupyterHub assignment management tool with LTI support"

    subcommands = {
        'serve': (ServeCommand, "Start the BYTE Grader JupyterHub service."),
    }

    log_level = Unicode('DEBUG', help="Logging level").tag(config=True)
    log_format = Unicode(
        "%(asctime)s [%(name)s] %(levelname)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        help="Logging format").tag(config=False)

    def start(self):
        self._init_logging()
        self._configure_logger(self)
        self.log.info("Starting BYTEGrader from main")

        if self.subapp is None:
            self.log.info("No subcommand specified. Use --help to see available commands.")
            self.print_help()
            return

        self._configure_logger(self.subapp)
        self.subapp.start()

    def _init_logging(self):
        log_level = getattr(logging, self.log_level)
        logging.basicConfig(
            level=log_level,
            format=self.log_format,
            stream=sys.stdout,
        )
        self.log.setLevel(log_level)

    def _configure_logger(self, app):
        log_level = getattr(logging, self.log_level)
        app.log.setLevel(log_level)
        if app.log.handlers:
            for handler in app.log.handlers:
                handler.setFormatter(logging.Formatter(self.log_format))


def main():
    return BYTEGraderCLI.launch_instance()


if __name__ == "__main__":
    sys.exit(main())