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

Scrubbing runs on the package handler (so records propagated from child loggers
such as `coalsense.auth.sub` are covered), on the package loggers, and inside
the JSON formatter itself, which scrubs any record that skipped the filters.
Scrubbing is idempotent. Key matching ignores case and separators, so
`file_name`, `file-name` and `fileName` all match `filename`; `path` is also a
default content key (`file_path`, `attachment_path`). User file names are
content. Source-code metadata on the record (`pathname`, `filename`, `module`,
`funcName`, `lineno`) is not content: it is preserved for other formatters, but
the JSON line does not emit it. Keys are applied only to `extra`, never to
standard record attributes.

`configure_logging` keys accumulate: calling it again without `content_keys`
(or with fewer) never forgets earlier custom keys, so a later caller cannot
silently weaken scrubbing; empty keys are ignored. Out of scope: loggers not
created with `get_logger`, third-party loggers and `logging.captureWarnings`
write through the root logger and our handler never sees them. Only a handler
with this package's formatter scrubs such records.
