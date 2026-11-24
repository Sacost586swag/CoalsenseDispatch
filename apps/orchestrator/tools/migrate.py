"""Comando administrativo: plan por defecto; --apply ejecuta con credenciales separadas."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from coalsense_orchestrator.persistence.config import DatabaseSettings
from coalsense_orchestrator.persistence.migrations import MigrationError, run_migrations
from coalsense_orchestrator.persistence.roles import PersistenceError


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--local-test", action="store_true")
    args = parser.parse_args()
    dsn = os.environ.get("COALSENSE_MIGRATION_DATABASE_URL")
    if not dsn:
        print(json.dumps({"code": "migration.configuration.missing"}))
        return 2
    code = "migration.failed"
    try:
        settings = DatabaseSettings.from_dsn(dsn, testing_local=args.local_test)
        result = asyncio.run(
            run_migrations(
                settings,
                Path(__file__).resolve().parents[1] / "migrations",
                apply=args.apply,
            )
        )
        print(json.dumps({"applied" if args.apply else "pending": list(result)}))
        return 0
    except MigrationError as error:
        code = str(error)
    except PersistenceError:
        code = "migration.configuration.invalid"
    except Exception:
        pass
    print(json.dumps({"code": code}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
