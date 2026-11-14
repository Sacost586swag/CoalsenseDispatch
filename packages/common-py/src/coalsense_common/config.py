"""Esquemas Pydantic; declarar los secretos como SecretStr."""

import os
from collections.abc import Mapping

from pydantic import BaseModel, ValidationError


class ConfigError(ValueError):
    """La configuración no permite iniciar la aplicación."""


def _names(items: list[str]) -> str:
    return ", ".join(dict.fromkeys(items))


def load_config[T: BaseModel](
    schema: type[T], env: Mapping[str, str] = os.environ
) -> T:
    """Validar el entorno sin exponer valores ni mensajes de validadores.

    Los nombres/alias del modelo corresponden a las variables de entorno.
    Usar SecretStr para secretos y evitar serializers que los revelen.
    El mensaje de ConfigError lista solo nombres de variables, nunca valores.
    """
    try:
        return schema.model_validate(dict(env))
    except ValidationError as error:
        # Solo `loc` y `type`: `msg`, `input` y `ctx` pueden contener valores.
        missing: list[str] = []
        invalid: list[str] = []
        for item in error.errors(include_input=False, include_context=False, include_url=False):
            name = ".".join(str(part) for part in item["loc"]) or "(raíz)"
            (missing if item["type"] == "missing" else invalid).append(name)
        parts = []
        if missing:
            parts.append(f"faltan: {_names(missing)}")
        if invalid:
            parts.append(f"inválidas: {_names(invalid)}")
        detail = "; ".join(parts)
    # Fuera del `except`: sin __context__ que arrastre el error original.
    raise ConfigError(f"La configuración no permite iniciar la aplicación ({detail}).")
