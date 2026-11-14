# Accesibilidad: reglas de acceso sin manos

> Estas reglas **ganan sobre cualquier decisión estética**. Las skills de diseño y `packages/ui` están subordinadas a este archivo. El estilo visual no está en las specs; los mínimos de abajo sí.

Base: WCAG 2.2 nivel AA como mínimo. Objetivos AAA en tamaño de objetivo (2.5.5) y en tiempo (2.2.3 y 2.2.6).

## Reglas

| ID | Regla |
| --- | --- |
| AX-01 | **Sin manos.** Toda función se puede operar con cada modalidad de entrada compatible (voz, cabeza/gestos, mirada con dwell, switch con escaneo, teclado/mouse) o tiene un equivalente. Ninguna depende de una sola modalidad. |
| AX-02 | **Sin precisión motora fina.** Nada requiere clic preciso, arrastre, doble clic rápido, pulsación larga ni gestos con trayectoria (2.5.1, 2.5.7). El arrastre es una alternancia (inicia / termina). El doble clic es una sola orden. |
| AX-03 | **Sin límite de tiempo.** Ninguna función depende de un plazo. Nada expira: una aprobación pendiente sigue pendiente. Toda temporización de interacción (dwell, intervalo de escaneo, sostenimiento de un gesto) la ajusta la persona. Las sesiones no se cierran por inactividad mientras haya trabajo pendiente. |
| AX-04 | **Tamaño de objetivo.** Todo control interactivo mide al menos 44×44 px CSS (2.5.5 AAA; el mínimo AA 2.5.8 es 24×24). Los controles adyacentes tienen separación suficiente para no confundirse por temblor (valor en los tokens de `packages/ui`). |
| AX-05 | **Alto y Deshacer siempre visibles y operables** en toda pantalla, nunca tapados por un modal, un teclado virtual ni un panel. |
| AX-06 | **Etiqueta visible = nombre accesible** (2.5.3). La persona activa un control diciendo lo que ve. Nombres cortos y únicos por pantalla. |
| AX-07 | **Teclado y foco.** Todo operable con teclado (2.1.1), sin atajos de una sola tecla activos por defecto (2.1.4), foco visible y no oculto (2.4.7, 2.4.11), orden lógico. |
| AX-08 | **Entradas concurrentes.** No se limita la modalidad que la persona puede usar ni se obliga a cambiar entre ellas (2.5.6). |
| AX-09 | **Aprobaciones.** Muestran en lenguaje llano qué se aprueba, a quién llega y qué efecto tiene. Sin opción preseleccionada. Rechazar es tan fácil como aprobar. Existe "decidir después", que no expira. Nunca se aprueba por inacción. |
| AX-10 | **Retroalimentación multicanal.** Todo estado crítico (alto, modalidad no detectada, aprobación pendiente) se comunica por más de un canal (visual y audio local) y nunca solo por color (1.4.1). La persona elige los canales. |
| AX-11 | **Estados obligatorios en toda pantalla.** Cargando, vacío, error, sin conexión y, cuando aplique, calibración fallida y modalidad no detectada. Cada estado dice qué pasó, ofrece al menos una acción operable por cualquier modalidad y dice qué sigue funcionando. |
| AX-12 | **Lenguaje.** Español llano, frases cortas. No culpa ("fallaste"), no infantiliza, no presiona ("¡date prisa!"). Los fallos de calibración se atribuyen al equipo o a la configuración, no a la persona. |
| AX-13 | **Carga cognitiva y ánimo.** Una acción principal por pantalla [SUPUESTO]. Sin rachas que castiguen ni contadores de pérdida: el progreso solo suma. Se puede pausar y retomar sin perder avance. Sin notificaciones insistentes. |
| AX-14 | **Movimiento y luz.** Sin destellos de más de tres por segundo (2.3.1). Se respeta `prefers-reduced-motion`. Sin reproducción ni avance automático, salvo el escaneo que la persona configuró. |
| AX-15 | **Visibilidad mínima.** Contraste de texto 4.5:1 (1.4.3) y de componentes 3:1 (1.4.11), reflujo (1.4.10), espaciado de texto (1.4.12), modo de alto contraste y texto ampliable. |
| AX-16 | **Autenticación sin manos** (3.3.8). Sin CAPTCHA de puntería ni pruebas cognitivas. Recuperación de acceso con la misma regla. |
| AX-17 | **Interfaz del cuidador/a.** Cumple lo mismo y no puede ocultar a la persona lo que el cuidador/a hizo. |

## Precedencia

1. Seguridad y vertical (`product.md`, `safety.md`).
2. Este archivo.
3. Requisitos de la spec.
4. Estilo visual (skills de diseño).

Si un estilo choca con una regla de aquí, se cambia el estilo.

## Cómo se verifica

- axe-core en CI sobre cada pantalla y cada estado (AX-11).
- Playwright sin puntero: solo teclado e intenciones simuladas por el bus.
- Comprobación geométrica del tamaño de objetivo (axe cubre 24×24; el 44×44 se verifica con una regla propia).
- Reproducción de grabaciones (landmarks y audio) por modalidad.
- Lista de revisión manual con personas usuarias reales antes de cada hito.

Una tarea `[UI]` no está terminada hasta pasar estas comprobaciones. Los requisitos de UI describen **estados y comportamiento**, no estilo.
