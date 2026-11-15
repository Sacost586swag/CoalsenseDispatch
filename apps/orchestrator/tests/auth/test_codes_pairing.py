"""T-00-010: autenticación sin contraseña (REQ-00-020, 021, 025, 026, 027; P-00-3).

Todo el tiempo pasa por un reloj falso: ninguna prueba duerme.
"""

import dataclasses
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from coalsense_common import ConfigError, load_config
from coalsense_common.i18n_es import es
from coalsense_orchestrator.auth import errors
from coalsense_orchestrator.auth.codes import (
    MAIL_CAP_PER_HOUR,
    MAX_ATTEMPTS,
    PAIRING_ALPHABET,
    EmailCodeService,
    email_lookup,
    hash_code,
    new_email_code,
    new_pairing_code,
    normalize_email_code,
    normalize_pairing_code,
)
from coalsense_orchestrator.auth.codes import (
    lookup as lookup_of,
)
from coalsense_orchestrator.auth.config import AuthSettings
from coalsense_orchestrator.auth.memory import InMemoryAuditSink, InMemoryAuthRepository
from coalsense_orchestrator.auth.pairing import MAX_CLAIMS, PairingService
from coalsense_orchestrator.auth.ports import AuthDeps, CodeRecord
from coalsense_orchestrator.auth.rate_limit import RateLimiter
from coalsense_orchestrator.auth.routes import create_app
from fastapi import Request
from fastapi.testclient import TestClient
from httpx import Response

KEY = b"k" * 32
EMAIL = "Persona@Ejemplo.org"
ERROR_KEYS = {"code", "message_es", "recoverable", "next_actions"}
CAP_S = 900
REF = "ref-secreta-del-companion-" + "x" * 24  # lo genera el companion; solo viaja a la API


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def monotonic_s(self) -> float:
        return self.t

    def now_iso(self) -> str:
        return (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=self.t)).isoformat()

    def advance(self, seconds: float) -> None:
        self.t += seconds


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.fail = False

    def send_code(self, email: str, code: str) -> None:
        if self.fail:
            raise RuntimeError(f"smtp caído para {email} con {code}")
        self.sent.append((email, code))

    @property
    def last(self) -> str:
        return self.sent[-1][1]


class FakeVault:
    def seal(self, email: str) -> bytes:
        return b"sealed:" + bytes(b ^ 0x5A for b in email.encode())


def who(request: Request) -> str:
    account = request.headers.get("x-account")
    if not account:
        raise errors.session_required()
    return account


class Env:
    def __init__(self) -> None:
        self.clock = FakeClock()
        self.repo = InMemoryAuthRepository()
        self.audit = InMemoryAuditSink()
        self.sender = FakeSender()
        self.deps = AuthDeps(
            repo=self.repo,
            audit=self.audit,
            clock=self.clock,
            limiter=RateLimiter(self.clock, cap_s=CAP_S),
            key=KEY,
        )
        self.emails = EmailCodeService(self.deps, self.sender, FakeVault())
        self.pairing = PairingService(self.deps)
        self.app = create_app(
            self.emails,
            self.pairing,
            trusted_proxies=frozenset({"testclient"}),
            current_account=who,
        )
        self.api = TestClient(self.app, base_url="https://testserver")

    def request(self, email: str = EMAIL, ip: str | None = None) -> int:
        headers = {"x-forwarded-for": ip} if ip else {}
        response = self.api.post("/auth/code/request", json={"email": email}, headers=headers)
        return response.status_code

    def verify(self, code: str, email: str = EMAIL, ip: str | None = None) -> Response:
        headers = {"x-forwarded-for": ip} if ip else {}
        body = {"email": email, "code": code, "device_label": "Mi computador"}
        return self.api.post("/auth/code/verify", json=body, headers=headers)

    def login(self, email: str = EMAIL) -> dict[str, str]:
        assert self.request(email) == 202
        response = self.verify(self.sender.last, email)
        assert response.status_code == 200, response.text
        body: dict[str, str] = response.json()
        return body

    def start_pairing(self, ref: str = REF) -> str:
        response = self.api.post(
            "/auth/pairing/start", json={"client_ref": ref, "device_label": "Companion sala"}
        )
        assert response.status_code == 201, response.text
        code: str = response.json()["code"]
        return code

    def claim(self, account: str, code: str) -> Response:
        return self.api.post(
            "/auth/pairing/claim", json={"code": code}, headers={"x-account": account}
        )

    def companion(self, action: str, ref: str = REF) -> Response:
        return self.api.post(f"/auth/pairing/{action}", json={"client_ref": ref})


@pytest.fixture
def env() -> Env:
    return Env()


def assert_error(response: Response, status: int, code: str) -> dict[str, object]:
    assert response.status_code == status, response.text
    body: dict[str, object] = response.json()
    assert set(body) == ERROR_KEYS
    assert body["code"] == code
    assert isinstance(body["recoverable"], bool)
    assert body["message_es"] and isinstance(body["next_actions"], list)
    return body


def wrong_code(real: str) -> str:
    return f"{(int(real) + 1) % 10**6:06d}"


# --- códigos -------------------------------------------------------------------------------


def test_code_shapes() -> None:
    for _ in range(300):
        assert re.fullmatch(r"\d{6}", new_email_code())
        pairing = new_pairing_code()
        assert len(pairing) == 6 and set(pairing) <= set(PAIRING_ALPHABET)
    assert not set("0O1I") & set(PAIRING_ALPHABET)


def test_dictated_codes_are_normalized() -> None:
    assert normalize_email_code(" 123 456 ") == "123456"
    assert normalize_email_code("12345") == ""
    assert normalize_pairing_code("k7m-2qx") == "K7M2QX"
    assert normalize_pairing_code("K7M 2QX ") == "K7M2QX"


def test_hash_is_keyed_and_bound_to_subject() -> None:
    a = hash_code(KEY, "email", "s1", "123456")
    assert a != "123456" and len(a) == 64
    assert a != hash_code(KEY, "email", "s2", "123456")
    assert a != hash_code(b"x" * 32, "email", "s1", "123456")
    assert a != hash_code(KEY, "device", "s1", "123456")


def test_record_has_no_expiry_field() -> None:
    assert not [f.name for f in dataclasses.fields(CodeRecord) if "expir" in f.name]


# --- REQ-00-020 / 021: código por correo ---------------------------------------------------


def test_email_login_creates_account_device_and_audits(env: Env) -> None:
    body = env.login()
    assert body["created"] is True and body["account_id"] and body["device_id"]
    env.clock.advance(CAP_S)
    again = env.login()
    assert again["created"] is False and again["account_id"] == body["account_id"]
    names = [(e.event, e.result) for e in env.audit.events]
    assert names.count(("auth.account.created", "ok")) == 1
    assert names.count(("auth.login", "ok")) == 2


def test_only_hash_is_stored_and_email_is_sealed(env: Env) -> None:
    env.request()
    code = env.sender.last
    stored = repr(env.repo.codes)
    assert code not in stored
    assert hash_code(KEY, "email", email_lookup(KEY, EMAIL), code) in stored
    env.verify(code)
    dump = repr(env.repo.accounts) + repr(env.repo.devices)
    assert EMAIL not in dump and EMAIL.lower() not in dump


def test_unknown_and_known_email_look_the_same(env: Env) -> None:
    env.login()
    env.clock.advance(CAP_S)
    first = env.api.post("/auth/code/request", json={"email": EMAIL})
    env.clock.advance(CAP_S)
    second = env.api.post("/auth/code/request", json={"email": "otra@ejemplo.org"})
    assert first.status_code == second.status_code == 202 and first.json() == second.json()


def test_p_00_3_code_never_expires_by_time(env: Env) -> None:
    env.request()
    code = env.sender.last
    env.clock.advance(10 * 365 * 24 * 3600)
    assert env.verify(code).status_code == 200


def test_code_is_single_use(env: Env) -> None:
    env.request()
    code = env.sender.last
    assert env.verify(code).status_code == 200
    env.clock.advance(CAP_S)
    assert_error(env.verify(code), 400, "auth.code.gone")


def test_new_code_invalidates_previous(env: Env) -> None:
    env.request()
    old = env.sender.last
    env.clock.advance(CAP_S)
    env.request()
    new = env.sender.last
    stale = old if old != new else wrong_code(new)
    assert_error(env.verify(stale), 400, "auth.code.invalid")
    env.clock.advance(CAP_S)
    assert env.verify(new).status_code == 200


def test_attempts_exceeded_invalidates_code_not_account(env: Env) -> None:
    env.request()
    code = env.sender.last
    for _ in range(MAX_ATTEMPTS - 1):
        assert_error(env.verify(wrong_code(code)), 400, "auth.code.invalid")
        env.clock.advance(CAP_S)
    assert_error(env.verify(wrong_code(code)), 400, "auth.code.gone")
    env.clock.advance(CAP_S)
    assert_error(env.verify(code), 400, "auth.code.gone")  # ni el correcto sirve ya
    env.clock.advance(CAP_S)
    assert env.request() == 202  # la cuenta sigue disponible
    assert env.verify(env.sender.last).status_code == 200


def test_correct_code_on_last_attempt_still_works(env: Env) -> None:
    env.request()
    code = env.sender.last
    for _ in range(MAX_ATTEMPTS - 1):
        env.verify(wrong_code(code))
        env.clock.advance(CAP_S)
    assert env.verify(code).status_code == 200


def test_send_failure_is_a_recoverable_error(env: Env) -> None:
    env.sender.fail = True
    response = env.api.post("/auth/code/request", json={"email": EMAIL})
    body = assert_error(response, 502, "auth.send.failed")
    assert body["recoverable"] is True and EMAIL not in response.text


# --- REQ-00-025: espera creciente, nunca bloqueo permanente --------------------------------


def test_limiter_waits_grow_then_cap_and_never_lock() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock, cap_s=CAP_S)
    waits = []
    for _ in range(14):
        limiter.fail("k")
        waits.append(limiter.retry_after("k"))
        clock.advance(waits[-1])
    assert waits[:5] == [2, 4, 8, 16, 32] and max(waits) == CAP_S and waits[-1] == CAP_S
    assert limiter.retry_after("k") == 0
    clock.advance(10 * CAP_S)
    limiter.fail("k")
    assert limiter.retry_after("k") == 2  # tras un descanso la espera vuelve a empezar
    limiter.reset("k")
    assert limiter.retry_after("k") == 0


def test_wrong_codes_get_growing_wait_in_plain_spanish(env: Env) -> None:
    env.request()
    code = env.sender.last
    assert_error(env.verify(wrong_code(code)), 400, "auth.code.invalid")
    blocked = env.verify(code)  # incluso el correcto espera
    assert_error(blocked, 429, "auth.rate_limited")
    assert blocked.headers["retry-after"] == "2"
    assert "2 segundos" in blocked.json()["message_es"]
    env.clock.advance(1)
    again = env.verify(code)
    assert again.headers["retry-after"] == "1"  # insistir no alarga la espera
    assert "1 segundo" in again.json()["message_es"]
    env.clock.advance(1)
    assert env.verify(code).status_code == 200


def test_never_permanent_lock_after_many_failures(env: Env) -> None:
    for _ in range(40):
        env.verify("000000", ip="9.9.9.9")
        env.clock.advance(CAP_S)
    assert env.request(ip="9.9.9.9") == 202
    assert env.verify(env.sender.last, ip="9.9.9.9").status_code == 200


def test_wait_is_per_ip_too(env: Env) -> None:
    env.verify("000000", email="a@ejemplo.org", ip="7.7.7.7")
    other = env.verify("000000", email="b@ejemplo.org", ip="7.7.7.7")
    assert_error(other, 429, "auth.rate_limited")
    fresh = env.verify("000000", email="c@ejemplo.org", ip="8.8.8.8")
    assert_error(fresh, 400, "auth.code.gone")


def test_requests_are_throttled_but_do_not_block_verification(env: Env) -> None:
    assert env.request() == 202
    assert env.request() == 429
    assert env.verify(env.sender.last).status_code == 200


# --- I1: un tercero no puede dejar a la persona en espera ----------------------------------


def test_third_party_on_another_ip_cannot_delay_the_person(env: Env) -> None:
    attacker, person = "6.6.6.6", "1.1.1.1"
    for _ in range(8):  # el atacante insiste con el correo de la persona hasta una espera larga
        env.request(ip=attacker)
        env.verify("000000", ip=attacker)
        env.clock.advance(CAP_S)
    env.request(ip=attacker)
    env.verify("000000", ip=attacker)
    assert_error(env.verify("000000", ip=attacker), 429, "auth.rate_limited")
    assert env.request(ip=attacker) == 429
    assert env.request(ip=person) == 202  # la persona entra sin esperar
    assert env.verify(env.sender.last, ip=person).status_code == 200


def test_waits_are_keyed_by_ipv6_64_prefix(env: Env) -> None:
    env.verify("000000", ip="2001:db8:1:2::1")
    same_network = env.verify("000000", ip="2001:db8:1:2:ffff::9")
    assert_error(same_network, 429, "auth.rate_limited")
    other_network = env.verify("000000", ip="2001:db8:1:3::1")
    assert_error(other_network, 400, "auth.code.gone")  # otra red /64: sin espera


def test_shared_ip_resets_on_success_for_that_email(env: Env) -> None:
    ip = "3.3.3.3"
    env.request(ip=ip)
    code = env.sender.last
    assert_error(env.verify(wrong_code(code), ip=ip), 400, "auth.code.invalid")
    env.clock.advance(2)
    assert env.verify(code, ip=ip).status_code == 200
    env.clock.advance(CAP_S)
    env.request(ip=ip)
    assert_error(env.verify("999999", ip=ip), 400, "auth.code.invalid")
    blocked = env.verify("999999", ip=ip)
    assert blocked.headers["retry-after"] == "2"  # la cuenta de fallos volvió a empezar


def test_many_successful_logins_from_one_ip_do_not_build_a_long_wait(env: Env) -> None:
    for number in range(12):  # residencia o consultorio detrás de una misma IP
        email = f"persona{number}@ejemplo.org"
        assert env.request(email, ip="4.4.4.4") == 202
        assert env.verify(env.sender.last, email, ip="4.4.4.4").status_code == 200
        env.clock.advance(1)
    assert env.request("otra@ejemplo.org", ip="4.4.4.4") == 202


def test_account_wide_cap_limits_mail_flooding_but_slides(env: Env) -> None:
    for number in range(MAIL_CAP_PER_HOUR):
        assert env.request(ip=f"10.0.0.{number + 1}") == 202
        env.clock.advance(5)
    flood = env.api.post(
        "/auth/code/request", json={"email": EMAIL}, headers={"x-forwarded-for": "10.9.9.9"}
    )
    assert_error(flood, 429, "auth.rate_limited")
    assert 0 < int(flood.headers["retry-after"]) <= 3600
    env.clock.advance(3600)
    assert env.request(ip="10.9.9.9") == 202  # nunca permanente


# --- emparejamiento de dispositivo ---------------------------------------------------------


def test_pairing_binds_only_after_the_companion_confirms(env: Env) -> None:
    account = env.login()["account_id"]
    devices_before = len(env.repo.devices)
    code = env.start_pairing()
    assert len(code) == 6 and set(code) <= set(PAIRING_ALPHABET)
    assert env.companion("status").json() == {"state": "waiting", "hint": None}
    claimed = env.claim(account, code.lower())  # dictado en minúsculas
    assert claimed.status_code == 202 and claimed.json() == {"status": "pending"}
    assert len(env.repo.devices) == devices_before  # reclamar no crea el dispositivo
    state = env.companion("status").json()
    assert state["state"] == "claimed" and state["hint"] == "p***@e***.org"
    assert EMAIL.lower() not in repr(state)
    confirmed = env.companion("confirm")
    assert confirmed.status_code == 200
    device = env.repo.devices[confirmed.json()["device_id"]]
    assert device.account_id == account and device.label == "Companion sala"
    assert ("auth.device.paired", "ok") in [(e.event, e.result) for e in env.audit.events]
    env.clock.advance(CAP_S)
    assert_error(env.claim(account, code), 400, "auth.code.gone")  # un solo uso
    assert_error(env.companion("confirm"), 400, "auth.code.gone")


def test_attacker_claim_then_victim_rejects_leaves_no_device(env: Env) -> None:
    attacker = env.login("atacante@ejemplo.org")["account_id"]
    env.clock.advance(CAP_S)
    devices_before = set(env.repo.devices)
    code = env.start_pairing()
    assert env.claim(attacker, code).status_code == 202
    assert env.companion("status").json()["hint"] == "a***@e***.org"  # la víctima lo ve
    assert env.companion("reject").status_code == 200
    assert set(env.repo.devices) == devices_before
    env.clock.advance(CAP_S)
    assert_error(env.claim(attacker, code), 400, "auth.code.gone")
    assert_error(env.companion("confirm"), 400, "auth.code.gone")
    assert ("auth.pairing.rejected", "ok") in [(e.event, e.result) for e in env.audit.events]


def test_confirm_needs_a_claim_and_a_known_client_ref(env: Env) -> None:
    env.start_pairing()
    assert_error(env.companion("confirm"), 409, "auth.pairing.not_claimed")
    unknown = env.companion("confirm", ref="otra-ref-" + "y" * 40)
    assert_error(unknown, 400, "auth.code.gone")
    assert_error(env.companion("reject", ref="otra-ref-" + "y" * 40), 429, "auth.rate_limited")


def test_pairing_claim_budget_invalidates_the_code(env: Env) -> None:
    account = env.login()["account_id"]
    code = env.start_pairing()
    for _ in range(MAX_CLAIMS):
        assert env.claim(account, code).status_code == 202
        env.clock.advance(CAP_S)
    assert_error(env.claim(account, code), 400, "auth.code.gone")
    env.clock.advance(CAP_S)
    assert_error(env.companion("confirm"), 400, "auth.code.gone")


def test_client_ref_is_stored_only_as_hmac(env: Env) -> None:
    env.start_pairing()
    assert REF not in repr(env.repo.codes)


def test_pairing_code_never_expires_by_time(env: Env) -> None:
    account = env.login()["account_id"]
    code = env.start_pairing()
    env.clock.advance(5 * 365 * 24 * 3600)
    assert env.claim(account, code).status_code == 202
    env.clock.advance(5 * 365 * 24 * 3600)
    assert env.companion("confirm").status_code == 200


def test_pairing_new_code_from_same_companion_invalidates_old(env: Env) -> None:
    account = env.login()["account_id"]
    old = env.start_pairing()
    env.clock.advance(CAP_S)
    new = env.start_pairing()
    assert old != new
    assert_error(env.claim(account, old), 400, "auth.code.gone")
    env.clock.advance(CAP_S)
    assert env.claim(account, new).status_code == 202


def test_pairing_wrong_codes_wait_and_recover(env: Env) -> None:
    account = env.login()["account_id"]
    code = env.start_pairing()
    assert_error(env.claim(account, "AAAAAA"), 400, "auth.code.gone")
    assert_error(env.claim(account, code), 429, "auth.rate_limited")
    env.clock.advance(2)
    assert env.claim(account, code).status_code == 202


def test_pairing_requires_a_signed_in_account(env: Env) -> None:
    code = env.start_pairing()
    response = env.api.post("/auth/pairing/claim", json={"code": code})
    assert_error(response, 401, "auth.session.required")
    plain = TestClient(create_app(env.emails, env.pairing), base_url="https://testserver")
    response = plain.post("/auth/pairing/claim", json={"code": code}, headers={"x-account": "a"})
    assert_error(response, 401, "auth.session.required")


def test_revoke_device_audits_and_checks_owner(env: Env) -> None:
    login = env.login()
    path = f"/auth/devices/{login['device_id']}/revoke"
    stranger = env.api.post(path, headers={"x-account": "otra-cuenta"})
    assert_error(stranger, 404, "auth.device.not_found")
    mine = {"x-account": login["account_id"]}
    assert env.api.post(path, headers=mine).status_code == 200
    assert env.repo.devices[login["device_id"]].revoked_at is not None
    event = next(
        e for e in env.audit.events if (e.event, e.result) == ("auth.device.revoked", "ok")
    )
    assert event.account_id == login["account_id"] and event.device_id == login["device_id"]
    assert_error(env.api.post(path, headers=mine), 404, "auth.device.not_found")
    failed = [
        e for e in env.audit.events if (e.event, e.result) == ("auth.device.revoked", "failed")
    ]
    assert len(failed) == 2 and failed[0].account_id == "otra-cuenta"  # M6: también se registra


# --- REQ-00-026: TLS -----------------------------------------------------------------------


def test_plain_http_is_rejected_with_common_error(env: Env) -> None:
    http = TestClient(env.app, base_url="http://testserver")
    response = http.post("/auth/code/request", json={"email": EMAIL})
    body = assert_error(response, 400, "auth.tls.required")
    assert body["recoverable"] is True
    assert env.sender.sent == []


def test_forwarded_proto_only_from_trusted_proxy(env: Env) -> None:
    headers = {"x-forwarded-proto": "https"}
    http = TestClient(env.app, base_url="http://testserver")
    ok = http.post("/auth/code/request", json={"email": EMAIL}, headers=headers)
    assert ok.status_code == 202
    other = create_app(env.emails, env.pairing, trusted_proxies=frozenset({"10.0.0.1"}))
    untrusted = TestClient(other, base_url="http://testserver")
    refused = untrusted.post("/auth/code/request", json={"email": EMAIL}, headers=headers)
    assert_error(refused, 400, "auth.tls.required")


def test_forwarded_proto_uses_the_rightmost_value(env: Env) -> None:
    """I3: el cliente puede anteponer "https"; vale lo que añadió el último proxy."""
    http = TestClient(env.app, base_url="http://testserver")
    body = {"email": EMAIL}
    forged = http.post(
        "/auth/code/request", json=body, headers={"x-forwarded-proto": "https, http"}
    )
    assert_error(forged, 400, "auth.tls.required")
    env.clock.advance(CAP_S)
    honest = http.post(
        "/auth/code/request", json=body, headers={"x-forwarded-proto": "http, https"}
    )
    assert honest.status_code == 202


def test_trusted_proxies_accept_cidr_ranges(env: Env) -> None:
    app = create_app(env.emails, env.pairing, trusted_proxies=frozenset({"10.0.0.0/8"}))
    inside = TestClient(app, base_url="http://testserver", client=("10.1.2.3", 50000))
    outside = TestClient(app, base_url="http://testserver", client=("11.1.2.3", 50000))
    headers = {"x-forwarded-proto": "https"}
    assert (
        inside.post("/auth/code/request", json={"email": EMAIL}, headers=headers).status_code == 202
    )
    refused = outside.post("/auth/code/request", json={"email": EMAIL}, headers=headers)
    assert_error(refused, 400, "auth.tls.required")


def test_https_responses_send_hsts(env: Env) -> None:
    response = env.api.post("/auth/code/request", json={"email": EMAIL})
    assert "max-age" in response.headers["strict-transport-security"]


# --- errores comunes sin eco de datos ------------------------------------------------------


def test_validation_and_unknown_routes_use_common_format_without_echo(env: Env) -> None:
    bad = env.api.post("/auth/code/request", json={"email": "no-es-correo-secreto"})
    body = assert_error(bad, 400, "auth.request.invalid")
    assert "secreto" not in bad.text and body["recoverable"] is True
    assert_error(env.api.get("/auth/nada"), 404, "http.404")
    incomplete = env.api.post("/auth/code/verify", json={"email": EMAIL})
    assert_error(incomplete, 400, "auth.request.invalid")


def test_accented_messages_reach_the_person_as_real_utf8(env: Env) -> None:
    env.request()
    response = env.verify(wrong_code(env.sender.last))
    assert response.json()["message_es"] == "Ese código no coincide."
    assert response.json()["next_actions"] == ["Revisa el código e inténtalo de nuevo."]
    assert "Ã" not in response.text
    http = TestClient(env.app, base_url="http://testserver")
    refused = http.post("/auth/code/request", json={"email": EMAIL})
    assert refused.json()["message_es"] == "Esta conexión no es segura."


def test_unexpected_errors_log_the_route_not_the_path(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)

    def boom(*_: object) -> None:
        raise RuntimeError(f"fallo con {EMAIL}")

    env.emails.request = boom  # type: ignore[method-assign]
    quiet = TestClient(env.app, base_url="https://testserver", raise_server_exceptions=False)
    response = quiet.post("/auth/code/request", json={"email": EMAIL})
    assert_error(response, 500, "http.500")
    routes = [r for r in caplog.records if getattr(r, "route", None)]
    assert routes and routes[0].route == "/auth/code/request"  # type: ignore[attr-defined]
    assert not any(hasattr(r, "path") for r in caplog.records)
    assert EMAIL not in caplog.text


def test_deps_repr_never_shows_the_key(env: Env) -> None:
    assert KEY.decode() not in repr(env.deps) and "kkkkkkkk" not in repr(env.deps)


def test_failed_account_creation_does_not_burn_the_code(env: Env) -> None:
    """M2: si falla crear la cuenta, el código sigue sirviendo (se consume al final)."""

    class FlakyVault(FakeVault):
        broken = True

        def seal(self, email: str) -> bytes:
            if self.broken:
                raise RuntimeError("bóveda caída")
            return super().seal(email)

    vault = FlakyVault()
    env.emails = EmailCodeService(env.deps, env.sender, vault)
    env.api = TestClient(
        create_app(env.emails, env.pairing, trusted_proxies=frozenset({"testclient"})),
        base_url="https://testserver",
        raise_server_exceptions=False,
    )
    env.request()
    code = env.sender.last
    assert env.verify(code).status_code == 500
    assert not env.repo.accounts and not env.repo.devices
    vault.broken = False
    assert env.verify(code).status_code == 200


def test_every_message_key_is_in_the_catalog() -> None:
    assert errors.CATALOG_KEYS
    for key in errors.CATALOG_KEYS:
        assert key in es


# --- REQ-00-027: bitácora y logs sin secretos ----------------------------------------------


def test_audit_and_logs_never_hold_codes_hashes_or_emails(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    env.request()
    first = env.sender.last
    env.verify(wrong_code(first))
    env.clock.advance(CAP_S)
    env.verify(first)
    account = env.login()["account_id"]
    pairing_code = env.start_pairing()
    env.claim(account, pairing_code)
    env.companion("status")
    env.companion("confirm")
    env.sender.fail = True
    env.clock.advance(CAP_S)
    env.request()
    lookup = email_lookup(KEY, EMAIL)
    plain = {first, wrong_code(first), pairing_code, EMAIL, EMAIL.lower(), lookup, REF}
    plain.add(env.repo.accounts[account].email_hint)
    plain.add(lookup_of(KEY, "client", REF))
    plain |= {code for _, code in env.sender.sent}
    hashed = {hash_code(KEY, "email", lookup, c) for c in plain}
    hashed.add(hash_code(KEY, "device", "", pairing_code))
    blob = repr(env.audit.events) + caplog.text
    assert env.audit.events
    for secret in plain | hashed:
        assert secret not in blob
    for event in env.audit.events:
        fields = {"event", "result", "at", "account_id", "device_id"}
        assert set(dataclasses.asdict(event)) == fields


# --- configuración y migración -------------------------------------------------------------


def test_config_requires_a_long_secret_and_never_prints_it() -> None:
    with pytest.raises(ConfigError) as missing:
        load_config(AuthSettings, {})
    assert "AUTH_HMAC_KEY" in str(missing.value)
    weak = "corta-pero-privada"
    with pytest.raises(ConfigError) as short:
        load_config(AuthSettings, {"AUTH_HMAC_KEY": weak})
    assert weak not in str(short.value)
    good = load_config(
        AuthSettings, {"AUTH_HMAC_KEY": "z" * 40, "AUTH_TRUSTED_PROXIES": "10.0.0.1, 10.0.0.2"}
    )
    assert "zzzz" not in repr(good) and good.proxies == frozenset({"10.0.0.1", "10.0.0.2"})
    cidr = load_config(
        AuthSettings, {"AUTH_HMAC_KEY": "z" * 40, "AUTH_TRUSTED_PROXIES": "10.0.0.0/8"}
    )
    assert cidr.proxies == frozenset({"10.0.0.0/8"})
    with pytest.raises(ConfigError):  # un proxy mal escrito no se acepta en silencio
        load_config(AuthSettings, {"AUTH_HMAC_KEY": "z" * 40, "AUTH_TRUSTED_PROXIES": "proxy-raro"})


def test_migration_has_no_expiry_and_no_plain_email() -> None:
    sql = (Path(__file__).parents[2] / "migrations" / "0001_auth.sql").read_text(encoding="utf-8")
    for table in ("account", "device", "pairing_code"):
        assert re.search(rf"create table {table}\b", sql, re.I)
    assert not re.search(r"expir", sql, re.I)
    assert re.search(r"email_ciphertext\s+bytea", sql, re.I)
    assert re.search(r"email_lookup\s+text", sql, re.I)
    assert not re.search(r"\bemail\s+text", sql, re.I)
