import os
import logging
from typing import Any, Dict, Optional

try:
    import sentry_sdk  # type: ignore
    from sentry_sdk import Hub  # type: ignore
    from sentry_sdk.integrations.tornado import TornadoIntegration  # type: ignore
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration  # type: ignore
    from sentry_sdk.integrations.logging import LoggingIntegration  # type: ignore
except ImportError:
    sentry_sdk = None
    Hub = None
    TornadoIntegration = None
    SqlalchemyIntegration = None
    LoggingIntegration = None

_log = logging.getLogger(__name__)


def init_sentry(logger):
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry disabled (no SENTRY_DSN).")
        return False

    if (
        sentry_sdk is None
        or TornadoIntegration is None
        or SqlalchemyIntegration is None
        or LoggingIntegration is None
    ):
        logger.info("Sentry SDK not installed. Skipping Sentry initialisation.")
        return False

    release = os.getenv("SENTRY_RELEASE")
    if not release:
        try:
            from importlib.metadata import version
            release = f"bytegrader@{version('bytegrader')}"
        except Exception:
            release = None

    sentry_sdk.init(
        dsn=dsn,
        release=release,
        environment=os.getenv("SENTRY_ENV", "development"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0")),
        send_default_pii=os.getenv("SENTRY_SEND_PII", "false").lower() == "true",
        integrations=[
            TornadoIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.ERROR,
                event_level=logging.ERROR
            )
        ],
        ignore_errors=[

        ],
        attach_stacktrace=True,
    )
    logger.info("Sentry initialised (dsn=%s).", dsn)

    return True


def _has_active_client() -> bool:
    if Hub is None:
        return False
    try:
        hub = Hub.current
    except Exception:
        return False
    return bool(hub and hub.client)


def capture_exception(exc: Exception, *, tags: Optional[Dict[str, Any]] = None,
                      extra: Optional[Dict[str, Any]] = None) -> bool:
    if sentry_sdk is None or not _has_active_client():
        return False

    try:
        with sentry_sdk.push_scope() as scope:
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
        return True
    except Exception:
        return False


def capture_message(message: str, *, level: str = "info",
                    tags: Optional[Dict[str, Any]] = None,
                    extra: Optional[Dict[str, Any]] = None) -> bool:
    if sentry_sdk is None or not _has_active_client():
        return False

    try:
        with sentry_sdk.push_scope() as scope:
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
        return True
    except Exception:
        return False
