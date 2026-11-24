/** Same-origin authentication bridge. Secrets stay in an HttpOnly cookie, never JSON or logs. */
import { es } from "../../../../../packages/ui/src/i18n/es.ts";

export const SESSION_COOKIE = "__Host-coalsense-session";
const TOKEN = /^[A-Za-z0-9_-]{43}$/;
const validCredential = (value: string) => value.length === 43 && TOKEN.test(value);
const COOKIE_FLAGS = "; Path=/; HttpOnly; Secure; SameSite=Strict";
const LIMIT = 8192;
export type AuthConfig = { publicOrigin: string; apiOrigin: string };
type Transport = (url: string, init?: RequestInit) => Promise<Response>;
type JsonObject = Record<string, unknown>;

function origin(value: string | undefined, name: string): string {
  try {
    if (!value) throw new Error();
    const url = new URL(value);
    if (
      url.protocol !== "https:" ||
      url.username ||
      url.password ||
      url.pathname !== "/" ||
      url.search ||
      url.hash
    )
      throw new Error();
    return url.origin;
  } catch {
    throw new Error(`Invalid configuration: ${name}`);
  }
}

export function readConfig(env: Record<string, string | undefined> = process.env): AuthConfig {
  return {
    publicOrigin: origin(env.COALSENSE_WEB_ORIGIN, "COALSENSE_WEB_ORIGIN"),
    apiOrigin: origin(env.COALSENSE_AUTH_ORIGIN, "COALSENSE_AUTH_ORIGIN"),
  };
}

function object(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function authError(status: number, code = "auth.unavailable"): Response {
  const keys: Record<string, keyof typeof es> = {
    "auth.code.invalid": "auth.code.invalid.message",
    "auth.code.gone": "auth.code.gone.message",
    "auth.session.required": "auth.session.required.message",
    "auth.forbidden": "auth.forbidden.message",
    "auth.rate_limited": "auth.wait.message",
  };
  const message = es[keys[code] ?? "auth.unavailable.message"];
  return json(
    {
      code,
      message_es: message,
      recoverable: status !== 403,
      next_actions: [es["auth.next.retry"]],
    },
    status,
  );
}

function json(body: unknown, status = 200): Response {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

function cookie(request: Request): string | undefined {
  const entries = (request.headers.get("cookie") ?? "").split(";").map((entry) => entry.trim());
  const found = entries.filter((entry) => entry.startsWith(`${SESSION_COOKIE}=`));
  if (found.length !== 1) return undefined;
  const token = found[0]?.slice(SESSION_COOKIE.length + 1);
  return token && validCredential(token) ? token : undefined;
}

const actions = {
  "request-code": { path: "/auth/code/request", fields: { email: 254 } },
  "verify-code": { path: "/auth/code/verify", fields: { email: 254, code: 32, device_label: 80 } },
  pair: { path: "/auth/pairing/claim", fields: { code: 32 } },
  "sign-out": { path: "", fields: {} },
} as const;

export async function handleAuth(
  request: Request,
  action: string,
  config: AuthConfig,
  transport: Transport = fetch,
): Promise<Response> {
  if (!Object.hasOwn(actions, action) && action !== "session") return authError(404, "http.404");
  const sessionQuery = action === "session";
  if (request.method !== (sessionQuery ? "GET" : "POST")) return authError(405, "http.405");
  let data: JsonObject = {};
  if (!sessionQuery) {
    if (request.headers.get("origin") !== config.publicOrigin)
      return authError(403, "auth.forbidden");
    if (request.headers.get("content-type")?.split(";")[0]?.trim() !== "application/json")
      return authError(415, "http.415");
    if (Number(request.headers.get("content-length")) > LIMIT) return authError(413, "http.413");
    try {
      const text = await request.text();
      if (text.length > LIMIT) return authError(413, "http.413");
      const value: unknown = JSON.parse(text);
      if (!object(value)) return authError(400, "auth.request.invalid");
      const fields = actions[action as keyof typeof actions].fields;
      if (Object.keys(value).length !== Object.keys(fields).length)
        return authError(400, "auth.request.invalid");
      for (const [key, max] of Object.entries(fields)) {
        const item = value[key];
        if (typeof item !== "string" || !item.trim() || item.length > max)
          return authError(400, "auth.request.invalid");
      }
      data = value;
    } catch {
      return authError(400, "auth.request.invalid");
    }
  }
  let credential = cookie(request);
  let replacement: string | undefined;
  let clear = false;
  if ((sessionQuery || action === "pair" || action === "sign-out") && !credential)
    return authError(401, "auth.session.required");

  const upstream = async (path: string, method: string, body?: JsonObject) => {
    const response = await transport(`${config.apiOrigin}${path}`, {
      method,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(15_000), // [SUPUESTO] red; no limita el tiempo de la persona
      headers: {
        "content-type": "application/json",
        ...(credential ? { authorization: `Bearer ${credential}` } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const rotated = response.headers.get("x-credential-rotated");
    if (rotated && validCredential(rotated)) credential = replacement = rotated;
    if (response.status === 401) clear = true;
    return response;
  };
  const finish = (response: Response) => {
    if (clear) response.headers.set("Set-Cookie", `${SESSION_COOKIE}=${COOKIE_FLAGS}; Max-Age=0`);
    else if (replacement)
      response.headers.set("Set-Cookie", `${SESSION_COOKIE}=${replacement}${COOKIE_FLAGS}`);
    return response;
  };
  const failure = async (response: Response) => {
    let code = response.status === 401 ? "auth.session.required" : "auth.unavailable";
    try {
      const result: unknown = await response.json();
      if (
        object(result) &&
        typeof result.code === "string" &&
        ["auth.code.invalid", "auth.code.gone", "auth.forbidden", "auth.rate_limited"].includes(
          result.code,
        )
      )
        code = result.code;
    } catch {
      /* Nunca reenviar cuerpos o errores arbitrarios del servicio. */
    }
    return finish(authError(response.status, code));
  };
  try {
    if (sessionQuery || action === "sign-out") {
      const response = await upstream("/auth/session", "GET");
      if (!response.ok) return await failure(response);
      const body: unknown = await response.json();
      if (
        !object(body) ||
        !["account_id", "device_id", "session_id", "role"].every(
          (key) => typeof body[key] === "string",
        )
      )
        return finish(authError(502));
      if (sessionQuery)
        return finish(
          json({
            account_id: body.account_id,
            device_id: body.device_id,
            session_id: body.session_id,
            role: body.role,
          }),
        );
      const revoked = await upstream(
        `/auth/sessions/${encodeURIComponent(String(body.session_id))}/revoke`,
        "POST",
      );
      if (!revoked.ok) return await failure(revoked);
      clear = true;
      return finish(json({ signed_out: true }));
    }
    const definition = actions[action as keyof typeof actions];
    const response = await upstream(definition.path, "POST", data);
    if (!response.ok) return await failure(response);
    if (action === "verify-code") {
      const result: unknown = await response.json();
      if (
        !object(result) ||
        typeof result.credential !== "string" ||
        !validCredential(result.credential)
      )
        return finish(authError(502));
      replacement = result.credential;
      return finish(json({ authenticated: true }));
    }
    return finish(json(action === "pair" ? { status: "pending" } : { requested: true }));
  } catch {
    return finish(authError(503));
  }
}
