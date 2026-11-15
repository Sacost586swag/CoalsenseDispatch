"""One-line technical logs. Messages must be constant event identifiers."""

import json
import logging
import math
import re
from collections.abc import Iterable
from typing import Any

from .errors import AppError
from .ids import new_id, wall_clock_iso

_CONTENT_KEYS = (
    "text",
    "body",
    "dictation",
    "profile",
    "filename",
    "recipient",
    "prompt",
    "completion",
    "audio",
    "video",
    "landmarks",
)
_OMITTED = "[omitido]"
_STANDARD = frozenset(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}
_loggers: dict[str, logging.Logger] = {}
_level = logging.INFO
_keys: tuple[str, ...] = _CONTENT_KEYS


def _event(value: object) -> str:
    if type(value) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", value):
        return value
    return _OMITTED


def _exception(error: BaseException) -> dict[str, str]:
    result = {"type": _event(type(error).__name__), "id": new_id()}
    if isinstance(error, AppError):
        result["code"] = _event(error.code)
    return result


def _scrub(
    value: Any, keys: tuple[str, ...], depth: int = 0, ancestors: frozenset[int] = frozenset()
) -> Any:
    # A depth bound also handles cycles without invoking repr/str on user objects.
    if depth >= 16 or id(value) in ancestors:
        return _OMITTED
    ancestors = ancestors | {id(value)}
    if isinstance(value, BaseException):
        return _exception(value)
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else _OMITTED
    if type(value) is str:
        return value if len(value) <= 64 else _OMITTED
    if type(value) is dict:
        return {
            key: _scrub(item, keys, depth + 1, ancestors)
            for key, item in value.items()
            if type(key) is str and len(key) <= 64 and not any(part in key.lower() for part in keys)
        }
    if type(value) in (list, tuple):
        return [_scrub(item, keys, depth + 1, ancestors) for item in value]
    return _OMITTED


class _Scrubber(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        error = record.exc_info[1] if record.exc_info else None
        exception = _exception(error) if error is not None else None
        message = _event(record.msg) if not record.args else _OMITTED
        name, levelname, levelno = _event(record.name), _event(record.levelname), record.levelno
        # Scrub the complete record, including args and extra, before any formatter.
        clean = _scrub(record.__dict__, _keys)
        record.__dict__.clear()
        record.__dict__.update(clean)
        record.name, record.levelname, record.levelno = name, levelname, levelno
        record.msg = message
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        record.__dict__["_safe_exception"] = exception
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD and key != "_safe_exception"
        }
        payload = {
            "timestamp": wall_clock_iso(),
            "level": record.levelname,
            "logger": _event(record.name),
            "message": record.msg,
            "extra": extra,
        }
        exception = record.__dict__.get("_safe_exception")
        if exception is not None:
            payload["exception"] = exception
        return json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _install(logger: logging.Logger) -> None:
    logger.setLevel(_level)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.filters.clear()
    logger.addFilter(_Scrubber())
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)


def configure_logging(level: int | str, content_keys: Iterable[str] = ()) -> None:
    """Configure owned loggers; custom content keys extend the mandatory defaults."""
    global _level, _keys
    # Use stdlib level validation before changing global configuration.
    probe = logging.Logger("coalsense.level.validation", level)
    keys = tuple(key.lower() for key in content_keys)
    _level, _keys = probe.level, _CONTENT_KEYS + keys
    for logger in _loggers.values():
        _install(logger)


def get_logger(name: str) -> logging.Logger:
    """Return an isolated stdlib logger configured for JSON on stderr."""
    if name not in _loggers:
        logger = logging.getLogger(f"coalsense.{name}")
        _install(logger)
        _loggers[name] = logger
    return _loggers[name]
