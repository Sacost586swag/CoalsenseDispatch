"""Errores de autenticación en el formato común; los textos salen del catálogo `es`."""

from dataclasses import dataclass
from math import ceil

from coalsense_common import AppError
from coalsense_common.i18n_es import es

CATALOG_KEYS = (
    "auth.rateLimited.message",
    "auth.wait.second",
    "auth.wait.seconds",
    "auth.wait.minute",
    "auth.wait.minutes",
    "auth.code.invalid.message",
    "auth.code.gone.message",
    "auth.request.invalid.message",
    "auth.tls.required.message",
    "auth.session.required.message",
    "auth.device.notFound.message",
    "auth.session.notFound.message",
    "auth.forbidden.message",
    "auth.next.askAccess",
    "auth.send.failed.message",
    "auth.pairing.notClaimed.message",
    "auth.pairing.busy.message",
    "auth.pairing.claimMismatch.message",
    "auth.next.retryAfterWait",
    "auth.next.requestNewCode",
    "auth.next.checkCode",
    "auth.next.checkData",
    "auth.next.useHttps",
    "auth.next.signIn",
    "auth.next.retry",
    "state.error.message",
)


@dataclass(eq=False)
class AuthError(AppError):
    """`to_dict()` sigue siendo el formato común; el estado HTTP viaja aparte."""

    status: int = 400
    retry_after_s: int | None = None


def _error(
    code: str, message: str, next_action: str, status: int, *, recoverable: bool = True, **fmt: str
) -> AuthError:
    return AuthError(code, es[message].format(**fmt), recoverable, [es[next_action]], status=status)


def wait_text(seconds: int) -> str:
    if seconds < 60:
        return es["auth.wait.second"] if seconds <= 1 else es["auth.wait.seconds"].format(n=seconds)
    minutes = ceil(seconds / 60)
    return es["auth.wait.minute"] if minutes == 1 else es["auth.wait.minutes"].format(n=minutes)


def throttled(seconds: int) -> AuthError:
    error = _error(
        "auth.rate_limited",
        "auth.rateLimited.message",
        "auth.next.retryAfterWait",
        429,
        wait=wait_text(seconds),
    )
    error.retry_after_s = seconds
    return error


def code_invalid() -> AuthError:
    return _error("auth.code.invalid", "auth.code.invalid.message", "auth.next.checkCode", 400)


def code_gone() -> AuthError:
    return _error("auth.code.gone", "auth.code.gone.message", "auth.next.requestNewCode", 400)


def request_invalid() -> AuthError:
    return _error(
        "auth.request.invalid", "auth.request.invalid.message", "auth.next.checkData", 400
    )


def tls_required() -> AuthError:
    return _error("auth.tls.required", "auth.tls.required.message", "auth.next.useHttps", 400)


def session_required() -> AuthError:
    return _error("auth.session.required", "auth.session.required.message", "auth.next.signIn", 401)


def device_not_found() -> AuthError:
    return _error(
        "auth.device.not_found", "auth.device.notFound.message", "auth.next.checkData", 404
    )


def session_not_found() -> AuthError:
    return _error(
        "auth.session.not_found", "auth.session.notFound.message", "auth.next.checkData", 404
    )


def forbidden() -> AuthError:
    return _error("auth.forbidden", "auth.forbidden.message", "auth.next.askAccess", 403)


def pairing_not_claimed() -> AuthError:
    return _error(
        "auth.pairing.not_claimed", "auth.pairing.notClaimed.message", "auth.next.retry", 409
    )


def pairing_busy() -> AuthError:
    return _error("auth.pairing.busy", "auth.pairing.busy.message", "auth.next.requestNewCode", 409)


def claim_mismatch() -> AuthError:
    return _error(
        "auth.pairing.claim_mismatch", "auth.pairing.claimMismatch.message", "auth.next.retry", 409
    )


def send_failed() -> AuthError:
    return _error("auth.send.failed", "auth.send.failed.message", "auth.next.retry", 502)


def generic(status: int) -> AuthError:
    return _error(
        f"http.{status}",
        "state.error.message",
        "auth.next.retry",
        status,
        recoverable=status >= 500,
    )
