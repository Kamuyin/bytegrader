from __future__ import annotations

from typing import Any, Dict

from bytegrader.core.observability.sentry import (
	init_sentry as sentry_init,
	capture_exception as sentry_capture_exception,
	capture_message as sentry_capture_message,
)

from bytegrader.core.observability.opentelemetry import (
	init_otel as otel_init,
	record_exception as otel_record_exception,
	record_event as otel_record_event,
	instrument_sqlalchemy as otel_instrument_sqlalchemy,
	is_otel_enabled,
	set_span_attributes as otel_set_span_attributes,
	set_user_context as otel_set_user_context,
)

__all__ = [
	"init_observability",
	"init_sentry",
	"init_otel",
	"capture_exception",
	"capture_message",
	"instrument_sqlalchemy",
	"set_span_attributes",
	"set_user_context",
	"otel_enabled",
]


def init_observability(logger) -> Dict[str, bool]:
	sentry_active = bool(sentry_init(logger))
	otel_active = bool(otel_init(logger))
	return {"sentry": sentry_active, "opentelemetry": otel_active}


def init_sentry(logger) -> bool:
	return bool(sentry_init(logger))


def init_otel(logger) -> bool:
	return bool(otel_init(logger))


def _merge_attributes(tags: Dict[str, Any] | None, extra: Dict[str, Any] | None) -> Dict[str, Any]:
	attributes: Dict[str, Any] = {}
	if tags:
		attributes.update({f"tag.{key}": value for key, value in tags.items()})
	if extra:
		attributes.update({f"extra.{key}": value for key, value in extra.items()})
	return attributes


def capture_exception(exc: Exception, *, tags: Dict[str, Any] | None = None,
					  extra: Dict[str, Any] | None = None) -> bool:
	sentry_captured = bool(sentry_capture_exception(exc, tags=tags, extra=extra))
	otel_attrs = _merge_attributes(tags, extra)
	if otel_attrs:
		otel_set_span_attributes({f"error.{key}": value for key, value in otel_attrs.items()})
	otel_recorded = bool(otel_record_exception(exc, attributes=otel_attrs))
	return sentry_captured or otel_recorded


def capture_message(message: str, *, level: str = "info",
					tags: Dict[str, Any] | None = None,
					extra: Dict[str, Any] | None = None) -> bool:
	sentry_captured = bool(sentry_capture_message(message, level=level, tags=tags, extra=extra))

	attributes = _merge_attributes(tags, extra)
	attributes.update({
		"log.severity": level,
		"log.message": message,
	})
	otel_set_span_attributes(
		{
			key: value
			for key, value in attributes.items()
			if key.startswith("tag.") or key.startswith("extra.") or key.startswith("log.")
		}
	)
	otel_recorded = bool(otel_record_event("log", attributes=attributes))
	return sentry_captured or otel_recorded


def instrument_sqlalchemy(engine) -> bool:
	return bool(otel_instrument_sqlalchemy(engine))


def set_span_attributes(attributes: Dict[str, Any]) -> bool:
	return otel_set_span_attributes(attributes)


def set_user_context(*, user_id: str | None = None, username: str | None = None,
					 is_admin: bool | None = None) -> bool:
	return otel_set_user_context(user_id=user_id, username=username, is_admin=is_admin)


def otel_enabled() -> bool:
	return is_otel_enabled()