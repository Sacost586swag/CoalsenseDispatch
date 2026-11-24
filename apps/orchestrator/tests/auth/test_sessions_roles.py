"""T-00-011: sesiones por dispositivo, roles y revocación (REQ-00-022, 023, 024; P-00-4).

Todo el tiempo pasa por un reloj falso: ninguna prueba duerme.
"""

import dataclasses
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from coalsense_common import new_id
from coalsense_common.i18n_es import es
from coalsense_orchestrator.auth import errors
from coalsense_orchestrator.auth.codes import EmailCodeService
from coalsense_orchestrator.auth.memory import InMemoryAuditSink, InMemoryAuthRepository
from coalsense_orchestrator.auth.pairing import PairingService
from coalsense_orchestrator.auth.ports import Account, AuthDeps, Device, Session
from coalsense_orchestrator.auth.rate_limit import RateLimiter
from coalsense_orchestrator.auth.revocation import RevocationService
from coalsense_orchestrator.auth.roles import RequireScopes
from coalsense_orchestrator.auth.routes import create_app
from coalsense_orchestrator.auth.scopes import (
    APPROVAL_DECIDE,
    CONTENT_READ,
    CONTENT_SCOPES,
    CONTENT_WRITE,
    DEVICES_MANAGE,
    OPS_HEALTH,
    OPS_METRICS,
    ROLE_SCOPES,
    scopes_for,
)
from coalsense_orchestrator.auth.sessions import (
    CREDENTIAL,
    ROTATE_AFTER_S,
    SessionService,
    credential_hash,
)
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from httpx import Response

KEY = b"k" * 32
EMAIL = "Persona@Ejemplo.org"
ERROR_KEYS = {"code", "message_es", "recoverable", "next_actions"}
ROTATED = "x-credential-rotated"
REF = "ref-secreta-del-companion-" + "x" * 24
YEAR_S = 365 * 24 * 3600


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

    def send_code(self, email: str, code: str) -> None:
        self.sent.append((email, code))


class FakeVault:
    def seal(self, email: str) -> bytes:
        return b"sealed:" + email.encode()


def bearer(credential: str) -> dict[str, str]:
    return {"authorization": f"Bearer {credential}"}


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
            limiter=RateLimiter(self.clock),
            key=KEY,
        )
        self.sessions = SessionService(self.deps)
        self.revocation = RevocationService(self.deps)
        self.emails = EmailCodeService(self.deps, self.sender, FakeVault(), self.sessions)
        self.pairing = PairingService(self.deps, self.sessions)
        self.app: FastAPI = create_app(
            self.emails,
            self.pairing,
            self.sessions,
            self.revocation,
            trusted_proxies=frozenset({"testclient"}),
        )
        # Rutas de prueba: las de contenido y las técnicas de otras tareas aún no existen.
        self.probe("/probe/read", CONTENT_READ)
        self.probe("/probe/write", CONTENT_WRITE)
        self.probe("/probe/approve", APPROVAL_DECIDE)
        self.probe("/probe/health", OPS_HEALTH)
        self.api = TestClient(self.app, base_url="https://testserver")

    def probe(self, path: str, scope: str) -> None:
        def handler() -> dict[str, bool]:
            return {"ok": True}

        self.app.add_api_route(path, handler, dependencies=[Depends(RequireScopes(scope))])

    def login(self, email: str = EMAIL) -> dict[str, str]:
        self.clock.advance(900)  # pasa la espera entre pedidos de código del mismo correo
        assert self.api.post("/auth/code/request", json={"email": email}).status_code == 202
        body = {"email": email, "code": self.sender.sent[-1][1], "device_label": "Mi equipo"}
        response = self.api.post("/auth/code/verify", json=body)
        assert response.status_code == 200, response.text
        result: dict[str, str] = response.json()
        return result

    def staff(self, role: str) -> tuple[Account, str]:
        """Cuenta con un rol dado (el alta por correo solo crea `person`) y su credencial."""
        account = Account(new_id(), role, b"x", new_id(), "o***@e***", "es", self.clock.now_iso())
        self.repo.add_account(account)
        device = Device(new_id(), account.id, "Equipo", self.clock.now_iso())
        self.repo.add_device(device)
        return account, self.sessions.issue(account, device).value

    def get(self, path: str, credential: str | None = None) -> Response:
        headers = bearer(credential) if credential else {}
        return self.api.get(path, headers=headers)


@pytest.fixture
def env() -> Env:
    return Env()


def assert_error(response: Response, status: int, code: str) -> dict[str, object]:
    assert response.status_code == status, response.text
    body: dict[str, object] = response.json()
    assert set(body) == ERROR_KEYS
    assert body["code"] == code
    return body


# --- credencial: emisión y almacenamiento ---------------------------------------------------


def test_login_issues_one_opaque_credential_stored_only_as_hmac(env: Env) -> None:
    login = env.login()
    credential = login["credential"]
    assert CREDENTIAL.fullmatch(credential)  # token_urlsafe(32): 256 bits
    session = env.repo.sessions[login["session_id"]]
    assert session.device_id == login["device_id"]
    assert session.credential_hash == credential_hash(KEY, credential)
    assert credential not in repr(env.repo.sessions) and credential not in repr(session)
    other = env.login("otra@ejemplo.org")
    assert other["credential"] != credential
    assert env.get("/probe/read", credential).status_code == 200


def test_pairing_confirm_issues_the_initial_credential(env: Env) -> None:
    person = env.login()
    code = env.api.post(
        "/auth/pairing/start", json={"client_ref": REF, "device_label": "Companion"}
    ).json()["code"]
    claim = env.api.post(
        "/auth/pairing/claim", json={"code": code}, headers=bearer(person["credential"])
    )
    assert claim.status_code == 202
    state = env.api.post("/auth/pairing/status", json={"client_ref": REF}).json()
    confirmed = env.api.post(
        "/auth/pairing/confirm", json={"client_ref": REF, "claim_id": state["claim_id"]}
    )
    assert confirmed.status_code == 200 and confirmed.headers["cache-control"] == "no-store"
    body = confirmed.json()
    session = env.repo.sessions[body["session_id"]]
    assert session.device_id == body["device_id"]
    assert session.credential_hash == credential_hash(KEY, body["credential"])
    assert env.get("/probe/read", body["credential"]).status_code == 200


def test_credential_is_delivered_once_with_no_store(env: Env) -> None:
    assert env.api.post("/auth/code/request", json={"email": EMAIL}).status_code == 202
    body = {"email": EMAIL, "code": env.sender.sent[-1][1], "device_label": "Mi equipo"}
    response = env.api.post("/auth/code/verify", json=body)
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "header",
    [None, "", "Bearer", "Bearer ", "Basic abc", "Bearer corta", "Bearer " + "ñ" * 43, "x" * 43],
)
def test_missing_or_malformed_credential_is_401_not_500(env: Env, header: str | None) -> None:
    headers = {"authorization": header.encode("latin-1", "replace")} if header is not None else {}
    response = env.api.get("/probe/read", headers=headers)  # type: ignore[arg-type]
    assert_error(response, 401, "auth.session.required")


def test_unknown_credential_is_401(env: Env) -> None:
    env.login()
    assert_error(env.get("/probe/read", "A" * 43), 401, "auth.session.required")


# --- rotación y gracia -----------------------------------------------------------------------


def test_no_rotation_before_the_interval(env: Env) -> None:
    credential = env.login()["credential"]
    env.clock.advance(ROTATE_AFTER_S - 1)
    response = env.get("/probe/read", credential)
    assert response.status_code == 200 and ROTATED not in response.headers


def test_rotation_after_the_interval_returns_a_new_credential(env: Env) -> None:
    credential = env.login()["credential"]
    env.clock.advance(ROTATE_AFTER_S)
    response = env.get("/probe/read", credential)
    new = response.headers[ROTATED]
    assert CREDENTIAL.fullmatch(new) and new != credential
    assert response.headers["cache-control"] == "no-store"
    assert env.get("/probe/read", new).status_code == 200
    assert ROTATED not in env.get("/probe/read", new).headers  # recién emitida: no rota de nuevo


def test_old_credential_has_a_single_grace_use(env: Env) -> None:
    old = env.login()["credential"]
    env.clock.advance(ROTATE_AFTER_S)
    first = env.get("/probe/read", old).headers[ROTATED]  # la respuesta se "perdió"
    retry = env.get("/probe/read", old)  # el cliente reintenta con la que tiene
    assert retry.status_code == 200
    recovered = retry.headers[ROTATED]  # la gracia entrega una vigente: no pierde la sesión
    assert env.get("/probe/read", recovered).status_code == 200
    assert_error(env.get("/probe/read", old), 401, "auth.session.required")  # gracia gastada
    assert env.get("/probe/read", first).status_code == 200  # la del primer giro vale una vez
    assert_error(env.get("/probe/read", first), 401, "auth.session.required")


def test_crossing_requests_never_lose_the_session(env: Env) -> None:
    """Dos pedidos con la misma credencial vieja: sirve la que el cliente guarde al final."""
    old = env.login()["credential"]
    env.clock.advance(ROTATE_AFTER_S)
    a = env.get("/probe/read", old).headers[ROTATED]
    b = env.get("/probe/read", old).headers[ROTATED]  # llegó cruzado, usa la gracia
    for kept in (a, b):  # cualquiera de las dos respuestas puede ser la última en llegar
        assert env.get("/probe/read", kept).status_code == 200


def test_rotation_is_audited_without_the_credential(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    login = env.login()
    env.clock.advance(ROTATE_AFTER_S)
    new = env.get("/probe/read", login["credential"]).headers[ROTATED]
    env.get("/probe/read", new)
    events = [(e.event, e.result) for e in env.audit.events]
    assert ("auth.session.issued", "ok") in events and ("auth.session.rotated", "ok") in events
    secrets = {login["credential"], new, credential_hash(KEY, new)}
    secrets |= {credential_hash(KEY, login["credential"])}
    blob = repr(env.audit.events) + caplog.text
    assert not any(secret in blob for secret in secrets)
    for event in env.audit.events:
        fields = {"event", "result", "at", "account_id", "device_id"}
        assert set(dataclasses.asdict(event)) == fields


# --- sin cierre por inactividad -------------------------------------------------------------


def test_session_survives_inactivity_while_work_is_pending(env: Env) -> None:
    """Dejar trabajo pendiente años sin usar la sesión no la cierra: solo la revocación."""
    credential = env.login()["credential"]
    env.clock.advance(5 * YEAR_S)
    response = env.get("/probe/read", credential)
    assert response.status_code == 200
    assert env.get("/probe/read", response.headers[ROTATED]).status_code == 200


def test_nothing_in_the_session_can_expire() -> None:
    assert not [f.name for f in dataclasses.fields(Session) if re.search("expir|idle", f.name)]
    sql = (Path(__file__).parents[2] / "migrations" / "0002_sessions.sql").read_text("utf-8")
    assert re.search(r"create table session\b", sql, re.I)
    for column in ("device_id", "scopes", "rotated_at", "revoked_at", "credential_hash"):
        assert re.search(rf"\b{column}\b", sql)
    assert not re.search(r"expir(es|y|ation|ed_at)\b|idle", re.sub(r"--.*", "", sql), re.I)
    assert not re.search(r"\bcredential\s+text", sql, re.I)  # solo el HMAC


# --- revocación inmediata --------------------------------------------------------------------


def test_revoking_a_device_invalidates_its_credential_at_once(env: Env) -> None:
    laptop = env.login()
    phone = env.login()  # mismo correo, otro dispositivo
    assert env.get("/probe/read", laptop["credential"]).status_code == 200
    revoke = env.api.post(
        f"/auth/devices/{laptop['device_id']}/revoke", headers=bearer(phone["credential"])
    )
    assert revoke.status_code == 200 and revoke.json() == {"revoked": True}
    assert_error(env.get("/probe/read", laptop["credential"]), 401, "auth.session.required")
    assert env.get("/probe/read", phone["credential"]).status_code == 200  # la otra sigue
    assert env.repo.sessions[laptop["session_id"]].revoked_at  # sin esperar a nada
    events = [(e.event, e.result, e.device_id) for e in env.audit.events]
    assert ("auth.device.revoked", "ok", laptop["device_id"]) in events  # se informa


def test_revoked_device_also_loses_the_grace_credential(env: Env) -> None:
    laptop = env.login()
    phone = env.login()
    env.clock.advance(ROTATE_AFTER_S)
    env.get("/probe/read", laptop["credential"])  # rota: la vieja queda en gracia
    env.api.post(f"/auth/devices/{laptop['device_id']}/revoke", headers=bearer(phone["credential"]))
    assert_error(env.get("/probe/read", laptop["credential"]), 401, "auth.session.required")


def test_revoking_a_session_closes_it_at_once_but_keeps_the_device(env: Env) -> None:
    laptop = env.login()
    phone = env.login()
    response = env.api.post(
        f"/auth/sessions/{laptop['session_id']}/revoke", headers=bearer(phone["credential"])
    )
    assert response.status_code == 200
    assert_error(env.get("/probe/read", laptop["credential"]), 401, "auth.session.required")
    assert env.repo.devices[laptop["device_id"]].revoked_at is None
    again = env.api.post(
        f"/auth/sessions/{laptop['session_id']}/revoke", headers=bearer(phone["credential"])
    )
    assert_error(again, 404, "auth.session.not_found")
    assert ("auth.session.revoked", "ok") in [(e.event, e.result) for e in env.audit.events]


def test_cannot_revoke_someone_elses_device_or_session(env: Env) -> None:
    mine = env.login()
    theirs = env.login("otra@ejemplo.org")
    for path in (
        f"/auth/devices/{theirs['device_id']}/revoke",
        f"/auth/sessions/{theirs['session_id']}/revoke",
    ):
        response = env.api.post(path, headers=bearer(mine["credential"]))
        assert response.status_code == 404  # igual que si no existiera
    assert env.get("/probe/read", theirs["credential"]).status_code == 200


def test_revoking_requires_a_session(env: Env) -> None:
    login = env.login()
    response = env.api.post(f"/auth/devices/{login['device_id']}/revoke")
    assert_error(response, 401, "auth.session.required")


# --- roles y alcances ------------------------------------------------------------------------


def test_scope_table_is_explicit_and_operator_has_no_content_scope() -> None:
    assert set(ROLE_SCOPES) == {"person", "caregiver", "operator", "company"}
    operator = scopes_for("operator")
    assert operator == {OPS_METRICS, OPS_HEALTH}
    assert all(scope.startswith("ops:") for scope in operator)
    assert not operator & CONTENT_SCOPES
    assert scopes_for("person") >= {CONTENT_READ, CONTENT_WRITE, APPROVAL_DECIDE, DEVICES_MANAGE}
    assert APPROVAL_DECIDE not in scopes_for("caregiver")  # V-12: no aprueba por la persona
    assert not scopes_for("company") & CONTENT_SCOPES
    assert scopes_for("inventado") == frozenset()


@pytest.mark.parametrize("path", ["/probe/read", "/probe/write", "/probe/approve"])
def test_operator_gets_403_on_content(env: Env, path: str) -> None:
    _, credential = env.staff("operator")
    assert_error(env.get(path, credential), 403, "auth.forbidden")
    assert env.get("/probe/health", credential).status_code == 200  # lo técnico sí


def test_person_cannot_use_ops_and_caregiver_cannot_approve(env: Env) -> None:
    assert_error(env.get("/probe/health", env.login()["credential"]), 403, "auth.forbidden")
    _, caregiver = env.staff("caregiver")
    assert env.get("/probe/read", caregiver).status_code == 200
    assert_error(env.get("/probe/approve", caregiver), 403, "auth.forbidden")


def test_forbidden_is_the_common_error_in_plain_spanish(env: Env) -> None:
    _, credential = env.staff("operator")
    body = assert_error(env.get("/probe/read", credential), 403, "auth.forbidden")
    assert body["message_es"] == es["auth.forbidden.message"]
    assert body["next_actions"] == [es["auth.next.askAccess"]]
    denied = [e for e in env.audit.events if e.event == "auth.scope.denied"]
    assert denied and denied[0].result == "failed"


def test_stored_scopes_cannot_widen_the_role(env: Env) -> None:
    """Aunque la fila de sesión del operador trajera `content:read`, el rol manda."""
    account, credential = env.staff("operator")
    session = next(s for s in env.repo.sessions.values() if s.credential_hash)
    session.scopes = session.scopes | {CONTENT_READ}
    assert_error(env.get("/probe/read", credential), 403, "auth.forbidden")
    assert account.role == "operator"


def test_role_change_applies_to_open_sessions(env: Env) -> None:
    account, credential = env.staff("caregiver")
    assert env.get("/probe/read", credential).status_code == 200
    account.role = "operator"  # el cambio de rol rige en el siguiente pedido
    assert_error(env.get("/probe/read", credential), 403, "auth.forbidden")


PUBLIC = {  # entrada: no hay sesión todavía o el companion se identifica con su client_ref
    ("POST", "/auth/code/request"),
    ("POST", "/auth/code/verify"),
    ("POST", "/auth/pairing/start"),
    ("POST", "/auth/pairing/status"),
    ("POST", "/auth/pairing/confirm"),
    ("POST", "/auth/pairing/reject"),
}


def declared(route: APIRoute) -> frozenset[str] | None:
    found = [d.call for d in route.dependant.dependencies if isinstance(d.call, RequireScopes)]
    return frozenset().union(*(c.scopes for c in found)) if found else None


def test_p_00_4_every_route_is_public_or_declares_scopes_and_operator_never_reads_content(
    env: Env,
) -> None:
    """Propiedad: nada se sirve sin alcances declarados y `operator` no toca contenido."""
    _, operator = env.staff("operator")
    content_routes = 0
    for route in env.app.routes:
        assert isinstance(route, APIRoute)
        scopes = declared(route)
        for method in route.methods:
            if (method, route.path) in PUBLIC:
                assert scopes is None
                continue
            if (method, route.path) == ("GET", "/auth/session"):
                assert scopes == frozenset()  # sesión propia, sin alcances de contenido
                assert_error(env.api.get(route.path), 401, "auth.session.required")
                continue
            assert scopes, f"{method} {route.path} no declara alcances"
            content_routes += bool(scopes & CONTENT_SCOPES)
            if not scopes <= scopes_for("operator"):  # todo lo no técnico, contenido incluido
                path = re.sub(r"\{[^}]+\}", "x", route.path)
                response = env.api.request(method, path, headers=bearer(operator))
                assert_error(response, 403, "auth.forbidden")
    assert content_routes >= 3


def test_every_operator_scope_is_technical() -> None:
    for scope in scopes_for("operator"):
        assert re.fullmatch(r"ops:[a-z]+", scope)
    assert CONTENT_SCOPES.isdisjoint(scopes_for("operator"))


def test_session_summary_requires_a_live_session_and_never_returns_credentials(env: Env) -> None:
    assert_error(env.api.get("/auth/session"), 401, "auth.session.required")
    login = env.login()
    response = env.get("/auth/session", login["credential"])
    assert response.status_code == 200
    assert response.json() == {
        "account_id": login["account_id"],
        "device_id": login["device_id"],
        "session_id": login["session_id"],
        "role": "person",
    }
    assert response.headers["cache-control"] == "no-store"
    env.revocation.revoke_session(login["account_id"], login["session_id"])
    assert_error(env.get("/auth/session", login["credential"]), 401, "auth.session.required")


def test_operator_can_inspect_only_its_own_session_metadata(env: Env) -> None:
    account, credential = env.staff("operator")
    response = env.get("/auth/session", credential)
    assert response.status_code == 200
    assert response.json()["role"] == "operator"
    assert response.json()["account_id"] == account.id
    assert set(response.json()) == {"account_id", "device_id", "session_id", "role"}


def test_catalog_keys_exist() -> None:
    for key in errors.CATALOG_KEYS:
        assert key in es


# --- arrastrado de la revisión de T-00-010 ---------------------------------------------------


def start_and_claim(env: Env, person: dict[str, str]) -> str:
    code = env.api.post(
        "/auth/pairing/start", json={"client_ref": REF, "device_label": "Companion"}
    ).json()["code"]
    env.api.post("/auth/pairing/claim", json={"code": code}, headers=bearer(person["credential"]))
    claim_id: str = env.api.post("/auth/pairing/status", json={"client_ref": REF}).json()[
        "claim_id"
    ]
    return claim_id


@pytest.mark.parametrize("action", ["confirm", "reject"])
def test_non_ascii_claim_id_is_a_409_not_a_500(env: Env, action: str) -> None:
    start_and_claim(env, env.login())
    quiet = TestClient(env.app, base_url="https://testserver", raise_server_exceptions=False)
    for bad in ("reclamación-ñ", "😀", "é" * 36):
        response = quiet.post(
            f"/auth/pairing/{action}", json={"client_ref": REF, "claim_id": bad}
        )
        assert_error(response, 409, "auth.pairing.claim_mismatch")


@pytest.mark.parametrize("action", ["confirm", "reject"])
def test_restart_wait_resets_after_confirm_or_reject(env: Env, action: str) -> None:
    person = env.login()
    claim_id = start_and_claim(env, person)
    done = env.api.post(f"/auth/pairing/{action}", json={"client_ref": REF, "claim_id": claim_id})
    assert done.status_code == 200
    again = env.api.post(
        "/auth/pairing/start", json={"client_ref": REF, "device_label": "Companion"}
    )
    assert again.status_code == 201  # sin tiempo de espera de por medio: no escala tras decidir


def test_restart_wait_still_applies_without_a_decision(env: Env) -> None:
    body = {"client_ref": REF, "device_label": "Companion"}
    assert env.api.post("/auth/pairing/start", json=body).status_code == 201
    assert_error(env.api.post("/auth/pairing/start", json=body), 429, "auth.rate_limited")
