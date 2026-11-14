# @coalsense/ui

Tokens y temas accesibles compartidos por la web y la WebView, sin dependencias.
Valores vinculantes: sección «Decisiones del orquestador» de MASTER.md.

Exportaciones: defaultTheme (también default), highContrast, reducedMotion,
defineTheme, toCssVariables, contrastRatio, relativeLuminance y tokens base.

defineTheme valida objetivos min/head >= 44 CSS px, textScale entre 1 y 2 y
movimiento de opacidad de 0–150 ms. Los literales de objetivo inválidos fallan
en TypeScript; los números dinámicos se validan en ejecución. Los tokens son
readonly en TypeScript.

toCssVariables(theme) devuelve una hoja completa con :root y la media query
prefers-reduced-motion: reduce. Esta anula la duración también en alto contraste.
Insertar la hoja en la web o WebView y reemplazarla al cambiar de tema.
Para texto al 200%: defineTheme({ ...highContrast, textScale: 2 }).

Los consumidores deben aplicar --target-min a ambas dimensiones mínimas,
--target-head en modo cabeza y --target-gap entre controles; usar --font-base
(rem multiplicados por --text-scale), --font-line-height y --font-family.
Las transiciones usan --motion-property y --motion-duration. Mantener el foco
visible con --ring-width y --color-ring. Las variables no estilizan controles
automáticamente: los componentes deben permitir crecimiento, reflujo y zoom.

Pares de texto comprobados: foreground/background, secondaryText/background,
onPrimary/primary, onAccent/accent y onStop/stop. Bordes, foco, primario, acento
y Alto se comprueban contra background. Otras combinaciones requieren medición.
Alto contraste usa blanco/negro para acento y Alto; siguen siendo obligatorias
sus etiquetas visibles y no depender solo del color.

La fuente se declara con fallback de sistema; su archivo y licencia llegan en
T-00-014. No se descarga aquí.

Scripts idénticos a common-ts: lint, typecheck, test (node --test) y build.
Build emite solo src en dist; typecheck incluye pruebas y casos @ts-expect-error.
El paquete expone tipos desde src y ejecución desde dist.
