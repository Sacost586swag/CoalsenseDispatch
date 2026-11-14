# Referencias de diseño para la capa de entrada

Qué patrones se toman de cada proyecto y cómo encajan con la spec `01-capa-de-entrada`. Revisado el 2026-11-14. De Talon no se copia código ni se embebe nada (EULA, V-10): solo se toman ideas de diseño.

## 1. Project Gameface (Google)

**Licencia y estado:** Apache 2.0. Repositorio archivado y de solo lectura desde el 5 de septiembre de 2025. Si se reutiliza código, se hace fork propio con atribución en el archivo de avisos de terceros, y nunca se depende del repositorio original.

**Qué es:** cursor controlado con la cabeza y clics o teclas con gestos faciales, con una webcam común. Usa MediaPipe Face Landmarker (BlazeFace, FaceMesh V2 y Blendshape V2). Tiene versión Windows (Python) y Android.

### Patrones que se toman

| Patrón | Cómo lo hace Gameface | Cómo se usa en Coalsense |
| --- | --- | --- |
| **Mapeo de blendshapes a acciones** | Un archivo de vínculos por dispositivo (`configs/default/mouse_bindings.json`, `keyboard_bindings.json`). Cada vínculo es `gesto: [dispositivo, acción, umbral, tipo_de_disparo]`. Los nombres de gesto salen de `src/shape_list.py`. | El gesto no produce un clic: produce una **intención** tipada de `packages/intents` que pasa por el bus. Los vínculos viven en el perfil de capacidad, validados con JSON Schema. Así Alto, Deshacer y Ayuda funcionan igual que con voz. |
| **Umbral por gesto** | Un umbral de 0.0 a 1.0 por vínculo. | Se amplía a dos umbrales con histéresis (`on` y `off`, con `off < on`), sostenimiento (`hold_ms`) y enfriamiento (`cooldown_ms`), según `01/design.md`. El umbral lo calcula la calibración y la persona lo ajusta. |
| **Cursor por un punto de la cara, no por el iris** | `cursor.json` usa `tracking_vert_idxs: [8]`: un vértice de FaceMesh en la parte alta del puente de la nariz, entre las cejas `[verificar en el mapa uv_unwrap_full.png]`. No sigue la mirada. | Se adopta: un punto rígido de la frente o el entrecejo es más estable que el iris con lentes y luz baja, y deja los ojos libres para mirar. La mirada queda `[POST-MVP]`. |
| **Suavizado y velocidad** | `pointer_smooth` (suavizado del cursor), `shape_smooth` (evita parpadeo de acciones), `spd_up/down/left/right` (velocidad por dirección), `mouse_acceleration`, `hold_trigger_ms` (500 ms por defecto), `tick_interval_ms` (16 ms). | Se toman los mismos ajustes como campos del perfil, todos ajustables por la persona (AX-03). Velocidad por dirección es útil si un lado del cuello tiene menos movilidad `[SUPUESTO]`. |
| **Modo por dirección de la cabeza** | `use_transformation_matrix` controla con la orientación de la cabeza e ignora el punto. | Base para el **control de ritmo** de D-03 en `01/design.md`: la inclinación fija una velocidad, con zona muerta. Gameface por defecto usa posición; Coalsense usa ritmo por defecto para cansar menos el cuello `[SUPUESTO: validar con personas reales]`. |
| **Calibración con vista de cámara en vivo** | La app muestra la cámara y, por gesto, una barra con el valor actual del blendshape frente al umbral `[verificar en el código del fork; el README no lo detalla]`. | La calibración muestra la cámara solo en local, con el valor del gesto y el umbral dibujados, y termina en la zona de práctica. Los fallos se atribuyen al equipo o a la luz, no a la persona (AX-12). |

### Lo que no se toma

- Disparar clics y teclas directo desde el gesto: rompe el bus, Alto universal y la bitácora.
- Puntería fina como única vía: siempre existe una alternativa sin puntería (números en pantalla, cuadrícula), por C-03.
- Configuración en archivos JSON editados a mano: la persona configura desde la interfaz, sin manos.

## 2. Talon

**Licencia:** el núcleo tiene EULA y no es software libre. No se embebe, no se redistribuye y no se copia código. Solo se toman ideas de diseño.

### Patrones que se toman

| Patrón | Cómo lo hace Talon | Cómo se usa en Coalsense |
| --- | --- | --- |
| **Gramática declarativa** | Archivos `.talon` con dos partes: un encabezado de contexto (por ejemplo `app:`, `os:`, `mode:`, `tag:`) arriba de una línea con un guion, y abajo las reglas (frase → acciones). Las listas (`{user.x}`) traducen palabras habladas a valores. Las capturas (`<user.x>`) son piezas reutilizables de gramática. Hay partes opcionales y alternativas. Si dos archivos aplican, gana el contexto más específico. | Archivos de comandos en **YAML validado con JSON Schema** (D-06 de `01/design.md`), con la misma idea: contexto + frase → intención con parámetros, listas y piezas reutilizables. El resultado siempre es una intención del bus, no una acción directa. |
| **Ruidos como disparadores** | Reconoce ruidos como `pop` (chasquido de labios) y `hiss` (siseo), con vínculos tipo `noise(pop)`. Uso típico: pop para clic, hiss sostenido para desplazar. | Candidato para una modalidad de "switch por sonido" para personas con habla cansada o baja `[POST-MVP, SUPUESTO]`. Un ruido sería un switch del perfil, nunca una aprobación por sí solo, por el riesgo de falsos disparos. Se evalúa con fixtures de ruido de fondo. |
| **Modo de comandos frente a modo de dictado** | Modos de comando, dictado, mixto y sueño. Se cambia diciendo `command mode`, `dictation mode`, `mixed mode`, `wake up`, `go to sleep`. En dictado algunas órdenes siguen activas (por ejemplo, "coma"). Un indicador muestra el modo actual. | Se adoptan los modos **comando, dictado y sueño** (término "modo de voz" del glosario). Alto, Deshacer y Ayuda funcionan en todos los modos con un detector separado (D-05); en dictado, Alto debe ir aislado por silencio (S-08). El modo actual siempre está visible y se anuncia por voz si la persona lo activa (AX-10). |

## 3. talonhub/community

**Licencia:** MIT (verificada el 2026-11-14, archivo LICENSE). Se puede reutilizar con aviso de copyright. Aun así, sus archivos están escritos para el motor de Talon, así que se toma sobre todo la **organización**, no los archivos.

### Organización que se toma

| Carpeta en community | Qué contiene | Equivalente en Coalsense |
| --- | --- | --- |
| `core/` | Teclas, formato de texto, edición, ventanas y pestañas, cambio de aplicación, cuadrícula del mouse, ayuda. | `commands/core/`: comandos base del companion, números en pantalla, cuadrícula y ayuda. |
| `apps/` | Comandos por aplicación. | `commands/apps/`: por aplicación, activados por contexto. |
| `tags/` | Comandos que se activan por etiqueta (navegador, terminal). | Contextos activables por etiqueta en el encabezado del archivo. |
| `plugin/` | Mouse, repetir, captura de pantalla, símbolos. | Funciones con lógica propia en `adapters/` y `actuator/`. |
| `settings.talon` y `settings/` | Ajustes en un solo archivo. | Ajustes en el perfil de capacidad, editables sin manos. |

Convenciones útiles: una frase por regla, listas en archivos aparte (`.talon-list`), y reemplazo de una lista creando otra con un contexto más específico en vez de editar la original. Se aplica igual con YAML: la persona puede sobrescribir una lista sin tocar los archivos base.

## 4. Pendientes de verificar

- Punto anatómico exacto del vértice 8 de FaceMesh (mapa `assets/images/uv_unwrap_full.png` de Gameface).
- Cómo dibuja Gameface la barra de umbral en la calibración (leer el código en el fork, no en el repositorio archivado).
- Reglas actuales de los ruidos de Talon (la documentación oficial está en `talonvoice.com/docs`; las páginas de la wiki comunitaria se movieron).

## Fuentes

- [google/project-gameface](https://github.com/google/project-gameface) y su [`Windows/README.md`](https://github.com/google/project-gameface/blob/main/Windows/README.md); [`configs/default/cursor.json`](https://github.com/google/project-gameface/blob/main/Windows/configs/default/cursor.json).
- [talonhub/community](https://github.com/talonhub/community).
- [Talon: uso básico (modos)](https://talon.wiki/Basic%20Usage/basic_usage) y [documentación oficial](https://talonvoice.com/docs/).
- [Wiki de Talon: archivos .talon](https://talon-wiki-refactor.netlify.app/customization/talon-files) y [listas](https://talon-wiki-refactor.netlify.app/Customization/talon_lists).
- [Changelog de Talon](https://talonvoice.com/dl/latest/changelog.html) (vínculos `noise(pop)`).
