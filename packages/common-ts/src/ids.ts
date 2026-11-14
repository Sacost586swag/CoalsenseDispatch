import { webcrypto } from "node:crypto";

let lastMs = -1n;
let random = 0n;
const mask = (1n << 74n) - 1n;

function randomBits(): bigint {
  const bytes = webcrypto.getRandomValues(new Uint8Array(10));
  let value = 0n;
  for (const byte of bytes) value = (value << 8n) | BigInt(byte);
  return value & mask;
}

/** UUIDv7; orden creciente local incluso con reloj detenido o en retroceso. */
export function newId(): string {
  const now = BigInt(Date.now());
  if (now > lastMs) {
    lastMs = now;
    random = randomBits();
  } else if (random === mask) {
    lastMs += 1n;
    random = randomBits();
  } else {
    random += 1n;
  }
  if (lastMs < 0n || lastMs >= 1n << 48n) {
    throw new RangeError("El reloj está fuera del rango de UUIDv7.");
  }
  const value =
    (lastMs << 80n) |
    (7n << 76n) |
    ((random >> 62n) << 64n) |
    (2n << 62n) |
    (random & ((1n << 62n) - 1n));
  const hex = value.toString(16).padStart(32, "0");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Nanosegundos para intervalos; el origen no es una fecha de calendario. */
export function monotonicNs(): bigint {
  return process.hrtime.bigint();
}

export function wallClockIso(): string {
  return new Date().toISOString();
}
