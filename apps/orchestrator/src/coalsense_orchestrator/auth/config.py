"""Configuración de autenticación: clave HMAC como secreto, nunca en código ni en logs."""

from pydantic import BaseModel, SecretStr, field_validator


class AuthSettings(BaseModel):
    AUTH_HMAC_KEY: SecretStr
    # Direcciones de proxies de confianza, separadas por coma. Solo ellos pueden fijar
    # `X-Forwarded-Proto` y `X-Forwarded-For`.
    AUTH_TRUSTED_PROXIES: str = ""

    @field_validator("AUTH_HMAC_KEY")
    @classmethod
    def _long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("La clave es demasiado corta.")
        return value

    @property
    def key(self) -> bytes:
        return self.AUTH_HMAC_KEY.get_secret_value().encode()

    @property
    def proxies(self) -> frozenset[str]:
        return frozenset(p.strip() for p in self.AUTH_TRUSTED_PROXIES.split(",") if p.strip())
