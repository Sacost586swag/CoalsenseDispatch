import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest
from coalsense_common import (
    AppError,
    ConfigError,
    load_config,
    monotonic_ns,
    new_id,
    wall_clock_iso,
)
from pydantic import BaseModel, SecretStr, field_validator


class Settings(BaseModel):
    PORT: int
    TOKEN: SecretStr

    @field_validator("TOKEN")
    @classmethod
    def validate_token(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 8:
            raise ValueError(f"Inválido: {value.get_secret_value()}")
        return value


def test_config_success_and_redaction(monkeypatch, caplog):
    env = {"PORT": "8000", "TOKEN": "fake-test-token"}
    config = load_config(Settings, env)
    assert config.PORT == 8000
    assert config.TOKEN.get_secret_value() == env["TOKEN"]
    with caplog.at_level(logging.INFO):
        logging.info("%s %r", config, config)
    for output in (str(config), repr(config), config.model_dump_json(), caplog.text):
        assert env["TOKEN"] not in output
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert load_config(Settings).PORT == 8000


@pytest.mark.parametrize("env", [
    {"TOKEN": "fake-test-token"},
    {"PORT": "8000", "TOKEN": "bad"},
    {"PORT": "invalid", "TOKEN": "fake-test-token"},
])
def test_config_failure_is_safe(env):
    with pytest.raises(ConfigError) as caught:
        load_config(Settings, env)
    output = "".join(traceback.format_exception(caught.value)) + repr(caught.value)
    assert "configuración" in str(caught.value)
    assert env["TOKEN"] not in output


def test_error_golden():
    golden = json.loads((Path(__file__).parent / "fixtures/error_golden.json").read_text("utf-8"))
    assert AppError(**golden).to_dict() == golden
    assert json.loads(json.dumps(AppError(**golden).to_dict())) == golden


def test_ids():
    start = int(datetime.now().timestamp() * 1000)
    values = [new_id() for _ in range(10_000)]
    assert len(set(values)) == 10_000
    assert values == sorted(values)
    for value in values:
        parsed = UUID(value)
        assert parsed.version == 7
        assert (parsed.int >> 62) & 3 == 2
    assert start <= int(values[0].replace("-", "")[:12], 16)


def test_ids_with_frozen_and_backward_clock(monkeypatch):
    from coalsense_common import ids

    now = 2_000_000_000_000_000_000
    monkeypatch.setattr(ids.time, "time_ns", lambda: now)
    values = [new_id() for _ in range(10_000)]
    now -= 1_000_000_000
    values.append(new_id())
    assert values == sorted(set(values))


def test_timestamps():
    first = monotonic_ns()
    assert isinstance(first, int)
    assert monotonic_ns() >= first
    value = wall_clock_iso()
    assert value.endswith("Z")
    assert datetime.fromisoformat(value).utcoffset().total_seconds() == 0
