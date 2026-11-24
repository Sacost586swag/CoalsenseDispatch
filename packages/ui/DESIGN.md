# Diseño de los componentes y su catálogo

Fuente: `src/tokens/base.ts`, temas, `src/components/`, `PRODUCT.md` de la raíz y
las decisiones vinculantes de `design-system/coalsense-dispatch/MASTER.md`.

La superficie del catálogo usa modo Operate: elegir un ejemplo, observar su estado
y probarlo. Conserva el mundo visual ya construido. Fondo cálido `#FAF7F2`, texto
`#1F1B16`, acción principal `#9A3412`, Alto `#B91C1C`, foco `#1D4ED8` y Atkinson
Hyperlegible autoalojada. El tema de alto contraste procede de `high-contrast.ts`.

Los tamaños, colores y espaciados del catálogo consumen los tokens. El texto base
es 18 px relativo a la preferencia del navegador. Los objetivos miden al menos
44 × 44 px; en modo cabeza y en la barra persistente, 64 × 64 px. La separación
de acciones es 16 px. El texto puede ampliarse al 200 % y las etiquetas largas
se dividen para evitar desplazamiento horizontal.

La navegación muestra etiquetas visibles en español y marca el ejemplo actual.
Cada estado tiene una URL. Los ejemplos no realizan acciones con efecto externo.
Los avisos no desaparecen solos, las aprobaciones no vencen ni tienen una opción
preseleccionada. Alto, Deshacer y Ayuda humana permanecen sobre los diálogos.

Precedencia aplicada: AX-05 y AX-14 ganan sobre recomendaciones genéricas de las
skills de diseño. No se añaden movimientos, estados que dependen de hover,
ilustraciones ni logos. El marco del aviso existente se conserva para no cambiar
el diseño compartido durante la construcción del catálogo.

La verificación automatizada cubre ambos temas con axe-core, incluido contraste,
geometría real, teclado y reflujo. La revisión con personas reales y las revisiones
cruzadas del hito siguen pendientes; estas pruebas no las sustituyen.
