import assert from "node:assert/strict";
import { test } from "node:test";
import { handleAuth, SESSION_COOKIE, readConfig } from "../../src/features/auth/server.ts";

const config = { publicOrigin: "https://app.example.org", apiOrigin: "https://api.example.org" };
const credential = "A".repeat(43);
const rotated = "B".repeat(43);
function request(action: string, body: unknown = {}, extra: Record<string, string> = {}) {
  return new Request(`${config.publicOrigin}/api/auth/${action}`, {
    method: "POST",
    headers: { origin: config.publicOrigin, "content-type": "application/json", ...extra },
    body: JSON.stringify(body),
  });
}

test("verification puts the secret only in a secure HttpOnly cookie", async () => {
  const response = await handleAuth(
    request("verify-code", {
      email: "persona@example.org",
      code: "123456",
      device_label: "Mi equipo",
    }),
    "verify-code",
    config,
    async (url, init) => {
      assert.equal(url, `${config.apiOrigin}/auth/code/verify`);
      assert.equal(init?.redirect, "error");
      assert.equal(init?.cache, "no-store");
      return Response.json({
        account_id: "account",
        device_id: "device",
        session_id: "session",
        credential,
        created: true,
      });
    },
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { authenticated: true });
  assert.match(response.headers.get("set-cookie") ?? "", /HttpOnly; Secure; SameSite=Strict/);
  assert.match(response.headers.get("set-cookie") ?? "", /Path=\//);
  assert.equal(response.headers.get("cache-control"), "no-store");
});

test("rejects forged origin, non-JSON, unknown action and oversized bodies before network", async () => {
  const transport = async () => {
    throw new Error("Network must not be called");
  };
  for (const [req, action, status] of [
    [request("request-code", {}, { origin: "https://evil.example.org" }), "request-code", 403],
    [request("request-code", {}, { "content-type": "text/plain" }), "request-code", 415],
    [request("unknown"), "unknown", 404],
    [request("constructor"), "constructor", 404],
    [request("request-code", { email: "x".repeat(9000) }), "request-code", 413],
    [request("request-code", { email: "persona@example.org", credential }), "request-code", 400],
  ] as const) {
    const response = await handleAuth(req, action, config, transport);
    assert.equal(response.status, status);
  }
});

test("session summary forwards the cookie and persists rotation without exposing it", async () => {
  const req = new Request(`${config.publicOrigin}/api/auth/session`, {
    headers: { cookie: `${SESSION_COOKIE}=${credential}` },
  });
  const response = await handleAuth(req, "session", config, async (_url, init) => {
    assert.equal(new Headers(init?.headers).get("authorization"), `Bearer ${credential}`);
    return Response.json(
      { account_id: "a", device_id: "d", session_id: "s", role: "person" },
      {
        headers: { "x-credential-rotated": rotated },
      },
    );
  });
  assert.equal(response.status, 200);
  assert.match(response.headers.get("set-cookie") ?? "", new RegExp(rotated));
  assert.equal((await response.text()).includes(rotated), false);
  assert.equal(response.headers.has("x-credential-rotated"), false);
});

test("401 removes a revoked cookie; transport failure keeps the session and hides exceptions", async () => {
  const req = () =>
    new Request(`${config.publicOrigin}/api/auth/session`, {
      headers: { cookie: `${SESSION_COOKIE}=${credential}` },
    });
  const revoked = await handleAuth(req(), "session", config, async () =>
    Response.json({}, { status: 401 }),
  );
  assert.equal(revoked.status, 401);
  assert.match(revoked.headers.get("set-cookie") ?? "", /Max-Age=0/);
  const unavailable = await handleAuth(req(), "session", config, async () => {
    throw new Error(credential);
  });
  assert.equal(unavailable.status, 503);
  assert.equal(unavailable.headers.has("set-cookie"), false);
  assert.equal((await unavailable.text()).includes(credential), false);
});

test("no cookie means no upstream request; no arbitrary upstream data reaches the browser", async () => {
  const anonymous = await handleAuth(
    new Request(`${config.publicOrigin}/api/auth/session`),
    "session",
    config,
    async () => {
      throw new Error("Unexpected network");
    },
  );
  assert.equal(anonymous.status, 401);
  const malformed = await handleAuth(
    request("request-code", { email: "persona@example.org" }),
    "request-code",
    config,
    async () => Response.json({ requested: true, private: credential }),
  );
  assert.deepEqual(await malformed.json(), { requested: true });
});

test("configuration rejects insecure or credential-bearing origins without echoing values", () => {
  assert.deepEqual(
    readConfig({
      COALSENSE_WEB_ORIGIN: config.publicOrigin,
      COALSENSE_AUTH_ORIGIN: config.apiOrigin,
    }),
    config,
  );
  for (const value of [
    undefined,
    "http://example.org",
    "https://user:xxx@example.org",
    "https://example.org/path",
  ]) {
    assert.throws(
      () => readConfig({ COALSENSE_WEB_ORIGIN: value, COALSENSE_AUTH_ORIGIN: config.apiOrigin }),
      (error: Error) =>
        !error.message.includes("private") && error.message.includes("COALSENSE_WEB_ORIGIN"),
    );
  }
});

test("sign out revokes the authenticated session with the latest rotation before deleting its cookie", async () => {
  const calls: string[] = [];
  const response = await handleAuth(
    request("sign-out", {}, { cookie: `${SESSION_COOKIE}=${credential}` }),
    "sign-out",
    config,
    async (url, init) => {
      calls.push(url);
      if (url.endsWith("/auth/session"))
        return Response.json(
          { account_id: "a", device_id: "d", session_id: "s", role: "person" },
          {
            headers: { "x-credential-rotated": rotated },
          },
        );
      assert.equal(new Headers(init?.headers).get("authorization"), `Bearer ${rotated}`);
      return Response.json({ revoked: true });
    },
  );
  assert.deepEqual(calls, [
    `${config.apiOrigin}/auth/session`,
    `${config.apiOrigin}/auth/sessions/s/revoke`,
  ]);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("set-cookie") ?? "", /Max-Age=0/);
  assert.deepEqual(await response.json(), { signed_out: true });
});

test("failed revocation preserves access, including a rotation received during the session check", async () => {
  const response = await handleAuth(
    request("sign-out", {}, { cookie: `${SESSION_COOKIE}=${credential}` }),
    "sign-out",
    config,
    async (url) => {
      if (url.endsWith("/auth/session"))
        return Response.json(
          { account_id: "a", device_id: "d", session_id: "s", role: "person" },
          {
            headers: { "x-credential-rotated": rotated },
          },
        );
      throw new Error("private upstream details");
    },
  );
  assert.equal(response.status, 503);
  assert.match(response.headers.get("set-cookie") ?? "", new RegExp(rotated));
  assert.doesNotMatch(response.headers.get("set-cookie") ?? "", /Max-Age=0/);
  assert.doesNotMatch(await response.text(), /private upstream details/);
});

test("malformed credentials and arbitrary upstream errors are never reflected", async () => {
  const verified = request("verify-code", {
    email: "p@example.org",
    code: "123456",
    device_label: "Mi equipo",
  });
  const invalid = await handleAuth(verified, "verify-code", config, async () =>
    Response.json({ credential: credential + "\n" }),
  );
  assert.equal(invalid.status, 502);
  assert.equal(invalid.headers.has("set-cookie"), false);
  const failed = await handleAuth(
    request("request-code", { email: "p@example.org" }),
    "request-code",
    config,
    async () =>
      Response.json(
        { code: credential, message_es: credential, next_actions: [credential] },
        { status: 500 },
      ),
  );
  assert.equal((await failed.text()).includes(credential), false);
});

test("duplicate cookies and missing Origin cannot trigger authenticated actions", async () => {
  const transport = async () => {
    throw new Error("Network must not be called");
  };
  const ambiguous = request(
    "pair",
    { code: "123456" },
    { cookie: `${SESSION_COOKIE}=${credential}; ${SESSION_COOKIE}=${rotated}` },
  );
  assert.equal((await handleAuth(ambiguous, "pair", config, transport)).status, 401);
  const noOrigin = request("request-code", { email: "p@example.org" });
  noOrigin.headers.delete("origin");
  assert.equal((await handleAuth(noOrigin, "request-code", config, transport)).status, 403);
});
