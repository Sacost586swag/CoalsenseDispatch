# @coalsense/common-ts

Configuración, errores, ids, registros e indicadores de función compartidos para TypeScript.

Esqueleto vacío de T-00-001. Lo llenan T-00-007, T-00-008 y T-00-009.

La prueba usa `node --test` (sin dependencias). Vitest se añade cuando haga falta (ver `tech.md`).

### Structured technical logging

```typescript
import { createLogger } from "@coalsense/common-ts";

const log = createLogger("auth", { level: "INFO", contentKeys: ["secret", "token"] });
log.info("auth.code_sent", { id: "request-1", result: "ok" });
// In a catch block: log.error("auth.failed", { error });
```

Methods: `debug`, `info`, `warn`, `error`, `critical`. Optional `sink(line)`
receives newline-terminated JSON; the default writes to stderr. Keys match
case-insensitive substrings recursively, and `contentKeys` extends the mandatory
text/body/dictation/profile/filename/recipient/prompt/completion/audio/video/
landmarks list. Unknown strings over 64 Unicode code points become `[omitido]`;
the cap conservatively also applies to metadata. Short unknown strings remain.
Unknown object instances, accessors, cycles, nonfinite numbers and nesting at
depth 16 are omitted without invoking serializers. Input objects stay unchanged.

Messages must be constant event identifiers (1–64 ASCII letters, digits, `.`,
`_`, `-`, starting with a letter). Invalid messages become `[omitido]`. Runtime
validation cannot prove literal origin: never interpolate content. Content must
use marked keys, never keys themselves, logger names, event ids or error codes.
Errors anywhere in metadata emit only their type and a fresh correlation id,
plus safe `AppError.code`; messages, causes and stacks are excluded. No new
dependencies. Python exposes the equivalent policy through stdlib logging.

Key matching ignores case and separators (`file_name`, `file-name`, `fileName`
all match `filename`); `path` is a default content key. User file names are
content. Only own enumerable data properties are read: Map, Set, Symbol keys and
values, class instances (prototype `toJSON` is never called), getters, array
accessor items and non-enumerable fields (`stack`, `message`) are omitted or
skipped, including errors with a null prototype.
