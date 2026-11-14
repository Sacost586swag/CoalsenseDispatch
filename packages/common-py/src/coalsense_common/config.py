"""Esquemas Pydantic; declarar los secretos como SecretStr."""

import os
from collections.abc import Mapping

from pydantic import BaseModel, ValidationError


class ConfigError(ValueError):
    """La configuración no permite iniciar la aplicación."""


def load_config[T: BaseModel](
    schema: type[T], env: Mapping[str, str] = os.environ
) -> T:
    """Validar el entorno sin exponer valores ni mensajes de validadores.

    Los nombres/alias del modelo corresponden a las variables de entorno.
    Usar SecretStr para secretos y evitar serializers que los revelen.
    """
    try:
        return schema.model_validate(dict(env))
    except ValidationError:
        # No conservar el error original: puede incluir el entorno completo.
        pass
    raise ConfigError("La configuración es inválida o faltan variables requeridas.")
