# common-py

Paquete Python `coalsense_common`: configuración, errores, ids, registros e indicadores de función.

Esqueleto vacío de T-00-001. Lo llenan T-00-007, T-00-008 y T-00-009.
### Structured technical logging

```python
from coalsense_common import configure_logging, get_logger

configure_logging("INFO", content_keys=["secret", "token"])
log = get_logger("auth")
log.info("auth.code_sent", extra={"id": "request-1", "result": "ok"})
# Inside an except block: log.exception("auth.failed")
```

The stdlib logger emits one JSON line to stderr and does not propagate to root
handlers. Configuration updates existing package loggers without duplicate
handlers; it owns their handlers and filters. Use `get_logger` for each logger.
Messages must be constant event identifiers (1–64 ASCII letters, digits, `.`,
`_`, `-`, starting with a letter). Runtime validation cannot prove a string is a
source-code literal: never concatenate or interpolate user content. Formatting
arguments are discarded and make the message `[omitido]`.

Keys match case-insensitive substrings, recursively in dictionaries and lists.
Custom keys extend the mandatory text/body/dictation/profile/filename/recipient/
prompt/completion/audio/video/landmarks list. Unknown strings longer than 64
Unicode code points become `[omitido]`; conservatively this cap also applies to
metadata strings. Short unknown strings are retained, so content must always
use marked keys. Do not put content in keys, logger names, event identifiers or
error codes. Unknown objects, cycles, nonfinite numbers and nesting at depth 16
are omitted. Input containers are not mutated.

Exceptions emit only type and a fresh correlation id, plus the safe `AppError`
code. Exception messages, chained exceptions, cached exception text and stack
traces are never formatted. No dependencies were added.
