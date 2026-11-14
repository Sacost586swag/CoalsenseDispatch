# Product

<!-- impeccable:product-schema 1 -->

Fuente: `.kiro/steering/product.md`, `accessibility.md` y `safety.md`, confirmados por el operador. Si este archivo y el steering chocan, gana el steering.

## Platform

web

(La app web es Next.js y PWA. La interfaz del companion de escritorio es una WebView que reutiliza `packages/ui`, así que comparte el mismo lenguaje web.)

## Stack

Next.js + TypeScript para la web; `packages/ui` como design system accesible; companion en Python 3.12 con WebView. Todo marcado `[SUPUESTO]` en `tech.md`.

## Users

- **Persona usuaria ("la persona"):** discapacidad física (movilidad reducida, en cama, cuadriplejia, ELA) o depresión, o ambas. Usa voz, cabeza y gestos (y más adelante mirada o switch). Persona de ejemplo: lesión medular cervical; suele conservar cabeza, cuello y habla; usa el equipo en cama, en silla reclinada o en silla de ruedas; se cansa y hace pausas frecuentes. Su trabajo: producir trabajo pagado con ayuda de agentes.
- **Cuidador/a:** configura el equipo y acompaña, con permisos delegados y revocables.
- **Contacto de confianza:** recibe alertas solo si la persona lo autorizó.
- **Operador:** administra la plataforma; no ve contenido privado.

## Product Purpose

Un sistema operativo de IA que permite controlar la computadora sin las manos y convertir "puedo mover el cursor" en "puedo cobrar por un trabajo". El propósito de fondo es romper la indefensión aprendida: cada interacción deja una experiencia real de control. El éxito se mide en tareas completadas por la persona por semana y en días hasta el primer ingreso `[SUPUESTO]`. No se mide el estado de ánimo.

## Positioning

El acceso físico (voz, cabeza, mirada) ya existe gratis y abierto. Lo escaso es la capa de arriba: un ciclo de control en el que la persona elige, los agentes ejecutan, la persona revisa y aprueba, el resultado sale al mundo y queda un logro. La IA nunca decide por la persona.

## Operating Context

- Uso en cama, silla reclinada o silla de ruedas; el ángulo de la cámara cambia y las posturas varían.
- Voz que puede ser baja o variar con la fatiga; pausas frecuentes; todo se puede pausar y retomar sin perder avance.
- Windows primero; cámara web común; procesamiento de cámara y micrófono en el dispositivo.
- Tres tareas del MVP: redactar y enviar un correo o mensaje profesional; convertir notas dictadas en un documento ordenado; preparar una publicación para redes lista para publicar.

## Capabilities and Constraints

- Ninguna acción con efecto externo sin aprobación explícita de la persona. Dial de autonomía por tipo de tarea; por defecto, la persona aprueba todo.
- Alto, Deshacer y Ayuda humana siempre activos en toda modalidad y en toda pantalla.
- Sin precisión motora fina ni límites de tiempo. Nada vence por inacción.
- No es terapia: no diagnostica, no trata, no promete efectos clínicos. Ante señales de crisis deriva a una persona con mensajes fijos.
- Terminología obligatoria en `.kiro/specs/GLOSARIO.md` (por ejemplo "aprobación", "tarea", "logro", "cuidador/a", "Alto").
- Fuera del MVP: mercado B2B y pagos, app Android, habla atípica.

## Brand Commitments

- Nombre: **Coalsense Dispatch**.
- Voz: español de Ecuador, llano, frases cortas, segunda persona, sin culpa, sin presión y sin infantilizar.
- Palabras que nunca aparecen: terapia, tratamiento, cura, diagnóstico, "mejora tu depresión", "fallaste".
- Personalidad `[SUPUESTO]`: cálido, sereno y capaz; dignidad y competencia, nunca lástima.

## Evidence on Hand

- Investigación base: `docs/IA contra la indefensión aprendida — Investigación base.md`.
- No hay logo, ilustraciones, testimonios, clientes ni cifras de resultados. No se fabrican: se usan marcadores hasta que el operador entregue los assets.

## Product Principles

1. La persona decide, la IA ejecuta.
2. Control real, pequeño y repetido: el progreso solo suma, sin rachas ni pérdidas.
3. Toda función funciona con cualquier modalidad de entrada, sin manos.
4. Privacidad por defecto: video, audio y perfil nunca salen del dispositivo ni llegan al modelo.
5. Lo que protege a la persona va antes que lo que la expone.

## Accessibility & Inclusion

WCAG 2.2 AA como mínimo, con AAA en tamaño de objetivo (2.5.5) y tiempo (2.2.3, 2.2.6). Objetivos de 44×44 px como mínimo y 64 px en modo cabeza `[SUPUESTO]`. Reglas AX-01 a AX-17 de `.kiro/steering/accessibility.md`, que ganan sobre cualquier decisión estética.
