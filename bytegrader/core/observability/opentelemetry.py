from __future__ import annotations

import logging
import os
from typing import Dict, Iterable, Mapping, Optional, Tuple

_OTEL_ENABLED = False
_SQLA_ENGINES: set[int] = set()
_REQUESTS_INSTRUMENTED = False
_TORNADO_INSTRUMENTED = False


def _parse_headers(raw_headers: str | None) -> Dict[str, str] | None:
    if not raw_headers:
        return None

    headers: Dict[str, str] = {}
    for item in raw_headers.split(","):
        item = item.strip()
        if not item:
            continue
        key, _, value = item.partition("=")
        if not key:
            continue
        headers[key.strip()] = value.strip()
    return headers or None


def _headers_sequence(headers: Dict[str, str] | None) -> Optional[Iterable[Tuple[str, str]]]:
    if not headers:
        return None
    return tuple(headers.items())


def is_otel_enabled() -> bool:
    return _OTEL_ENABLED


def init_otel(logger: logging.Logger) -> bool:
    global _OTEL_ENABLED, _REQUESTS_INSTRUMENTED, _TORNADO_INSTRUMENTED

    if _OTEL_ENABLED:
        return True

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OpenTelemetry disabled (no OTEL_EXPORTER_OTLP_ENDPOINT).")
        return False

    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
        from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore[import-not-found]
        from opentelemetry.instrumentation.tornado import TornadoInstrumentor  # type: ignore[import-not-found]
        from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace.export import (  # type: ignore[import-not-found]
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except ImportError as exc:
        logger.warning("OpenTelemetry packages not installed: %s", exc)
        return False

    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc").lower()
    headers = _parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))

    try:
        exporter = _build_exporter(endpoint, protocol, headers)
    except Exception as exc:
        logger.error("Failed to configure OTLP exporter: %s", exc, exc_info=True)
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", "bytegrader")
    service_version = os.getenv("OTEL_SERVICE_VERSION")

    resource_attributes = {"service.name": service_name}
    if service_version:
        resource_attributes["service.version"] = service_version

    tracer_provider = TracerProvider(resource=Resource.create(resource_attributes))
    trace.set_tracer_provider(tracer_provider)

    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    if os.getenv("OTEL_EXPORTER_CONSOLE", "").lower() in {"1", "true", "yes"}:
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    if not _REQUESTS_INSTRUMENTED:
        try:
            RequestsInstrumentor().instrument()
            _REQUESTS_INSTRUMENTED = True
        except Exception as exc:
            logger.warning("Requests instrumentation failed: %s", exc)

    if not _TORNADO_INSTRUMENTED:
        try:
            TornadoInstrumentor().instrument()
            _TORNADO_INSTRUMENTED = True
        except Exception as exc:
            logger.warning("Tornado instrumentation failed: %s", exc)

    _OTEL_ENABLED = True
    logger.info("OpenTelemetry tracing enabled (endpoint=%s, protocol=%s).", endpoint, protocol)
    return True


def _build_exporter(endpoint: str, protocol: str,
                    headers: Dict[str, str] | None):
    if protocol in {"http", "http/protobuf"}:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter as HTTPExporter,
        )

        return HTTPExporter(endpoint=endpoint, headers=headers)

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import-not-found]
        OTLPSpanExporter as GRPCExporter,
    )

    return GRPCExporter(endpoint=endpoint, headers=_headers_sequence(headers))


def record_exception(exc: Exception, *, attributes: Optional[Dict[str, object]] = None) -> bool:
    if not _OTEL_ENABLED:
        return False

    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
        from opentelemetry.trace import Status, StatusCode  # type: ignore[import-not-found]

        span = trace.get_current_span()
        if not span or not span.is_recording():
            return False

        span.record_exception(exc, attributes=attributes)
        span.set_status(Status(StatusCode.ERROR, str(exc)))
        return True
    except Exception:  # pragma: no cover - defensive
        return False


def record_event(name: str, *, attributes: Optional[Dict[str, object]] = None) -> bool:
    if not _OTEL_ENABLED:
        return False

    try:
        from opentelemetry import trace  # type: ignore[import-not-found]

        span = trace.get_current_span()
        if not span or not span.is_recording():
            return False

        span.add_event(name, attributes=attributes)
        return True
    except Exception:  # pragma: no cover - defensive
        return False


def instrument_sqlalchemy(engine) -> bool:
    if not _OTEL_ENABLED or engine is None:
        return False

    engine_id = id(engine)
    if engine_id in _SQLA_ENGINES:
        return False

    try:
        from opentelemetry.instrumentation.sqlalchemy import (  # type: ignore[import-not-found]
            SQLAlchemyInstrumentor,
        )

        SQLAlchemyInstrumentor().instrument(engine=engine)
        _SQLA_ENGINES.add(engine_id)
        return True
    except ImportError:  # pragma: no cover - optional dependency
        return False
    except Exception:  # pragma: no cover - instrumentation failure
        return False


def set_span_attributes(attributes: Mapping[str, object]) -> bool:
    if not _OTEL_ENABLED:
        return False

    if not attributes:
        return False

    try:
        from opentelemetry import trace  # type: ignore[import-not-found]

        span = trace.get_current_span()
        if not span or not span.is_recording():
            return False

        for key, value in attributes.items():
            span.set_attribute(key, value)
        return True
    except Exception:  # pragma: no cover - defensive
        return False


def set_user_context(user_id: Optional[str] = None, username: Optional[str] = None,
                     is_admin: Optional[bool] = None) -> bool:
    if not _OTEL_ENABLED:
        return False

    attributes: Dict[str, object] = {}
    if user_id:
        attributes["enduser.id"] = user_id
    if username:
        attributes["enduser.username"] = username
    if is_admin is not None:
        attributes["enduser.is_admin"] = bool(is_admin)

    if not attributes:
        return False

    return set_span_attributes(attributes)
