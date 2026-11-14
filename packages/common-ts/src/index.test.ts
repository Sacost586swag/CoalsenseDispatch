// Conserva el punto de entrada del script node --test existente.
await import(new URL("../tests/common.test.ts", import.meta.url).href);
