# @coalsense/ui

Tokens, temas y componentes base accesibles compartidos por la web y la WebView.
Valores vinculantes: sección «Decisiones del orquestador» de MASTER.md. Las reglas de
`.kiro/steering/accessibility.md` ganan sobre cualquier estilo.

Los tokens no tienen dependencias; los componentes requieren React 19 como peer.

## Tokens y temas (`@coalsense/ui`)

Exportaciones: defaultTheme (también default), highContrast, reducedMotion,
defineTheme, toCssVariables, contrastRatio, relativeLuminance, tokens base y el
catálogo `es`.

defineTheme clona el tema y valida el clon (un getter hostil no puede colar un valor
bajo después de la validación), exige objetivos min/head >= 44 CSS px, gap >= 16,
textScale entre 1 y 2 y movimiento de opacidad de 0–150 ms. Los literales de objetivo
inválidos fallan en TypeScript; los números dinámicos se validan en ejecución.

toCssVariables(theme) devuelve una hoja completa con :root y la media query
prefers-reduced-motion: reduce. Insertarla en la web o WebView y reemplazarla al cambiar
de tema. Para texto al 200%: defineTheme({ ...highContrast, textScale: 2 }).

## Componentes (`@coalsense/ui/components`)

Button, Link, TextField, Dialog, NumberedList, Progress, StatusBanner, Stepper, StateScreen,
ApprovalCard y StopUndoBar. Se
importan aparte para que los tokens se usen sin React. Importar también, una vez:

- `@coalsense/ui/components.css`: clases `cs-*`, solo con variables de los tokens.
- `@coalsense/ui/fonts.css`: Atkinson Hyperlegible 400 y 700 autoalojada (OFL, ver
  `src/fonts/OFL.txt`), `font-display: swap`, sin CDN.
- La hoja de `toCssVariables(theme)`.

Reglas que cumplen todos:

- El nombre accesible es el texto visible: no aceptan `aria-label`, `aria-labelledby`
  ni `title` (2.5.3). Sin botones de solo icono.
- Objetivo mínimo `var(--target-min)` en ambas dimensiones; `var(--target-head)` bajo
  `:root[data-input-mode="head"]`; separación `var(--target-gap)` en sus grupos de
  acciones. Foco de `var(--ring-width)` que nunca se quita.
- Deshabilitado (Button, Link, TextField) = `aria-disabled` + guarda del manejador
  (no activa ni envía formularios), sigue enfocable y acepta `disabledReason` (clave
  del catálogo) que se muestra como texto y se enlaza con `aria-describedby`. Nunca el
  atributo nativo `disabled`. `loading` bloquea clic y envío y anuncia «Cargando» en una
  región viva siempre montada (Button y TextField).
- Sin `:hover`, pulsación larga ni gestos; sin animación; ningún temporizador (la
  prueba lo verifica sobre el código). StatusBanner solo desaparece al pulsar
  Descartar. Dialog no se cierra solo, ni al pulsar el fondo; Escape cierra solo con
  `closeOnEscape`.
- Estados: Button normal, foco, activo, deshabilitado, cargando; Link normal, foco,
  activo, deshabilitado; TextField normal, foco, activo, deshabilitado, error;
  Progress determinado e indeterminado (cargando); StatusBanner info, éxito, atención,
  error (el tipo va en texto); Stepper hecho, actual, pendiente (en texto).
- Textos solo del catálogo `i18n/es.ts` (la auditoría de copy falla con literales).

### Barra de Alto y Deshacer, estados y aprobaciones (T-00-015)

- `StateScreen {state, whatHappened?, actions[1+], stillWorks[]}`: cargando, vacío, error,
  sin conexión, calibración fallida y modalidad no detectada; qué pasó (región viva siempre
  montada), acciones (la primera es la principal) y qué sigue funcionando.
- `ApprovalCard {what, recipient, effect, children, onApprove, onReject, onDecideLater}`:
  tres acciones del mismo peso, sin preselección ni foco inicial en una acción (el foco va
  al título), sin temporizador. `children` es el contenido exacto a aprobar.
- `StopUndoBar {onStop, onUndo, onHelp, undoAvailable}`: fija abajo, objetivos de
  `--target-head`, publica su altura real en `--stop-bar-reserved` y deja un espaciador
  al final del contenido. Sus controles se registran solos en el registro de navegación.
  Montarla una vez por pantalla.

Marcar cualquier barra propia con `data-cs-stop-bar` (constante `STOP_BAR_ATTRIBUTE`). El Dialog no
usa `aria-modal` (dejaría la barra fuera del árbol accesible): mientras está abierto
pone `inert` en todo salvo el diálogo y la barra (y sus ancestros) y lo restaura al
cerrar. Además: el fondo del diálogo termina por encima del hueco
`--stop-bar-reserved` (por defecto `--target-min` + 2 × `--space-md`, redefinible),
la barra queda en `--layer-stop-bar` (200) sobre el fondo (`--layer-dialog`, 100) y
sus controles forman parte del ciclo de Tab del diálogo. Se asume la barra abajo.

## Pruebas

`pnpm test` corre `node --test` (tokens) y Vitest (componentes, jsdom). Los componentes
se prueban con axe-core por componente y estado; solo `color-contrast` está apagado
porque jsdom no pinta y T-00-013 ya prueba los pares. jsdom no calcula layout: el
tamaño de objetivo se comprueba en la hoja y en las clases; la medición geométrica real
llega en T-00-017 (Playwright).
