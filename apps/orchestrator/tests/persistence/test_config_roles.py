"""Configuración y ámbito sin base de datos; sin credenciales en errores ni en agentes."""

import secrets
import ssl
from dataclasses import replace
from urllib.parse import unquote, urlsplit

import pytest
from coalsense_common import new_id
from coalsense_orchestrator.auth.scopes import CONTENT_READ
from coalsense_orchestrator.auth.sessions import Principal
from coalsense_orchestrator.persistence.config import DatabaseSettings
from coalsense_orchestrator.persistence.roles import (
    PersistenceError,
    agent_environment,
    person_scope,
)
from pydantic import SecretStr


def test_default_database_settings_require_verified_tls_and_mask_credentials() -> None:
    secret = secrets.token_hex(32)
    settings = DatabaseSettings.from_connection(
        username="runtime", password=SecretStr(secret), host="db.example", database="work"
    )
    tls = settings.tls()
    assert isinstance(tls, ssl.SSLContext)
    assert tls.check_hostname and tls.verify_mode == ssl.CERT_REQUIRED
    assert secret not in repr(settings) + str(settings.dsn)
    local = DatabaseSettings.from_connection(
        username="runtime",
        password=SecretStr(secret),
        host="127.0.0.1",
        database="work",
        testing_local=True,
    )
    assert local.tls() is False


def test_connection_components_escape_delimiters_in_passwords() -> None:
    secret = "@:/#?%" + secrets.token_hex(16)
    settings = DatabaseSettings.from_connection(
        username="runtime", password=SecretStr(secret), host="db.example", database="work"
    )
    parsed = urlsplit(settings.dsn.get_secret_value())
    assert unquote(parsed.password or "") == secret
    assert parsed.hostname == "db.example" and parsed.path == "/work"


@pytest.mark.parametrize("field", ["username", "password", "database"])
def test_malformed_unicode_in_connection_components_has_no_encoding_error_context(
    field: str,
) -> None:
    arguments = {
        "username": "runtime",
        "password": SecretStr(secrets.token_hex(32)),
        "host": "db.example",
        "database": "work",
    }
    arguments[field] = SecretStr("\ud800") if field == "password" else "\ud800"
    with pytest.raises(PersistenceError, match="^persistence.configuration.invalid$") as caught:
        DatabaseSettings.from_connection(**arguments)  # type: ignore[arg-type]
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "suffix",
    [
        "@db.example/work?sslmode=disable",
        "@db.example/work?sslmode=require",
        "@db.example/work?sslmode=verify-full&sslmode=disable",
        "@db.example/work?options=role%3Dadmin",
        "@db.example/work#fragment",
        "@db.example/",
        "@db.example:invalid/work",
        "@db.example:70000/work",
    ],
)
def test_invalid_config_is_rejected_without_credential_or_parser_error_context(suffix: str) -> None:
    secret = secrets.token_hex(32)
    with pytest.raises(PersistenceError, match="^persistence.configuration.invalid$") as caught:
        DatabaseSettings.from_dsn(f"postgresql://runtime:{secret}" + suffix)
    assert secret not in str(caught.value)
    assert caught.value.__context__ is None


def test_remote_database_cannot_use_the_explicit_local_testing_exception() -> None:
    with pytest.raises(PersistenceError):
        DatabaseSettings.from_dsn(
            "postgresql://runtime:" + secrets.token_hex(32) + "@db.example/work", testing_local=True
        )


def test_agent_environment_never_inherits_database_or_provider_credentials() -> None:
    inherited = {
        "COALSENSE_DATABASE_URL": secrets.token_hex(32),
        "PGPASSWORD": secrets.token_hex(32),
        "pgpassfile": "private",
        "ANTHROPIC_API_KEY": secrets.token_hex(32),
        "PYTHONPATH": "private",
        "HTTPS_PROXY": "private",
        "AWS_SECRET_ACCESS_KEY": "private",
        "SYSTEMROOT": "system",
        "TEMP": "temporary",
        "LANG": "es_EC.UTF-8",
    }
    assert agent_environment(inherited) == {
        "SYSTEMROOT": "system",
        "TEMP": "temporary",
        "LANG": "es_EC.UTF-8",
    }


def test_principal_cannot_change_the_person_id_via_an_input_field() -> None:
    person = Principal(new_id(), new_id(), new_id(), "person", frozenset({CONTENT_READ}))
    assert str(person_scope(person, CONTENT_READ)) == person.account_id
    for actor in (
        replace(person, role="operator"),
        replace(person, scopes=frozenset()),
        replace(person, role="caregiver"),
        replace(person, account_id="invalid"),
    ):
        with pytest.raises(PersistenceError, match="^persistence.access.denied$"):
            person_scope(actor, CONTENT_READ)
