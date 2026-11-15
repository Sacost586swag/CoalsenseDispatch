// Lee `turbo run <tarea> --dry=json` por stdin y falla si ningún paquete la ejecutaría
// (turbo sale con 0 cuando la tarea existe pero ningún paquete tiene el script).
// Solo cuentan entradas de la tarea pedida: las tareas de dependencia (p. ej. build) no.
// `audit` es un agregado sin comando propio; su trabajo real son las subtareas `audit:*`.
import { readFileSync } from "node:fs";

const task = process.argv[2] ?? "tarea";
let tasks;
try {
  tasks = JSON.parse(readFileSync(0, "utf8")).tasks;
} catch (error) {
  console.error(`::error::No se pudo leer el plan de turbo para ${task}: ${error.message}`);
  process.exit(1);
}
const ownTask = (name) => name === task || (task === "audit" && name.startsWith("audit:"));
const runnable = tasks.filter(
  (entry) => ownTask(entry.task) && entry.command !== "<NONEXISTENT>",
);
if (runnable.length < 1) {
  console.error(`::error::turbo run ${task} no ejecutaria ninguna tarea; una etapa vacia no cuenta como exito.`);
  process.exit(1);
}
console.log(`${task}: ${runnable.length} tarea(s) por ejecutar.`);
