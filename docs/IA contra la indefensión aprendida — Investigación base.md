# IA contra la indefensión aprendida — Investigación base

Nov 6, 2026 · @Sebastian

## Resumen ejecutivo

La oportunidad no está en dar acceso a la computadora, que ya es gratis y open source, sino en convertir ese acceso en ingreso con un agente de IA que la persona dirige. La neurociencia respalda el enfoque: la pasividad es la respuesta por defecto al estrés prolongado, y lo que protege es *aprender que uno tiene control*.

- **Ciencia:** el control vivido protege de forma duradera (Maier, Seligman, Baratta); el dominio de tareas es la fuente más fuerte de autoeficacia (Bandura); la activación conductual funciona en depresión.
- **Evidencia de ingreso:** una herramienta de IA subió 11% el ingreso de trabajadores sordos y redujo su brecha salarial de 8% a 3%.
- **Modelo que sobrevive:** paga la empresa, no la persona (Inclusively, Be My Eyes, Specialisterne).
- **Ecuador:** más de 1 millón de personas con discapacidad, 67.623 con empleo formal, y una cuota legal del 4% que obliga a contratar.
- **Trampa a evitar:** venderlo como terapia con IA (Woebot cerró; Illinois multa US$10.000).

## Marco psicológico: la pasividad no se aprende, el control sí

La ciencia corrigió la teoría original: la pasividad es la respuesta por defecto ante estrés prolongado, y lo que se aprende es que uno tiene control. Por eso el producto no debe "motivar": debe fabricar experiencias de control reales, pequeñas y repetidas.

| Hallazgo | Fuente | Qué implica para el producto |
| --- | --- | --- |
| El estrés prolongado produce la debilitación por sí solo; aprender una respuesta de control activa la corteza prefrontal medial, que frena esa respuesta | [Maier y Seligman 2016](https://dc2.philarchive.org/rec/MAILHA); [Baratta, Seligman y Maier 2023](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2023.1170417/full) | Cada sesión termina con algo que la persona hizo y que tuvo un efecto visible |
| Una experiencia previa de control protege contra estrés futuro, en otros contextos, y la protección dura | [Baratta et al. 2023](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2023.1170417/full) | La primera victoria va el día 1: el onboarding es una tarea completada, no un tutorial |
| La protección depende de aprendizaje dirigido a metas, no de hábitos automáticos | [Baratta et al. 2023](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2023.1170417/full) | La persona decide y dirige; la IA ejecuta. Si la IA hace todo sola, el control vuelve a ser de la máquina |
| El dominio de tareas es la fuente más poderosa de autoeficacia; le sigue ver a pares similares lograrlo | [Bandura 1977](https://www.simplypsychology.org/self-efficacy.html) | Registro visible de logros e ingresos; mentores y casos de pares con discapacidad |
| La activación conductual funciona en depresión: 26 ensayos, SMD −0.74 frente a control y superior a medicación en 4 ensayos | [Ekers et al. 2014](https://research.leedstrinity.ac.uk/en/publications/behavioural-activation-for-depression-an-update-of-meta-analysis-/) | Acción antes que motivación: micro-tareas agendadas con resultado inmediato |

La frase de Baratta et al. que resume la tesis: "control actively leads to protection". Ese es el mecanismo que la vertical tiene que vender y medir.

## Repos open source de acceso: la capa de entrada ya está resuelta

Controlar una computadora con la cara, los ojos o la voz ya existe gratis y con código abierto. Ninguno de estos proyectos convierte ese acceso en ingreso: ahí está el hueco.

| Proyecto | Qué hace | Licencia y estado | Qué tomar |
| --- | --- | --- | --- |
| [Project Gameface (Google)](https://developers.googleblog.com/2023/06/project-gameface.html) | Mueve el cursor con la cabeza y hace clic con gestos faciales (cejas, boca) usando una webcam común | Open source en [GitHub](https://github.com/google/project-gameface); Python + MediaPipe (478 puntos faciales, 52 gestos) | Base lista para control sin manos en Windows; nació con un streamer cuadripléjico, Lance Carr |
| [OptiKey](https://github.com/OptiKey/OptiKey) | Teclado en pantalla controlado con la mirada; escribir correos y usar el PC solo con los ojos | GPL v3, Windows; 4.4k estrellas | Referencia madura para usuarios con ELA/EMN; funciona con eye tracker, mouse o webcam |
| [EyeGestures](https://awesome.ecosyste.ms/projects/github.com%2Fnativesensors%2Feyegestures) | Eye tracking con webcam o cámara de celular, sin hardware caro | GPL-3.0, Python + versión JavaScript; último push abril 2025 | Eye tracking dentro de una app web propia |
| [ACAT (Intel)](https://GitHub.com/intel/acat) | Teclado simulado, predicción de palabras y voz sintética; hecho para Stephen Hawking | Apache 2.0, Windows 10/11; entradas: teclado, cámara, BCI, switches | Arquitectura de "actuadores" intercambiables: una sola app, muchos tipos de cuerpo |
| [Talon](https://blakewatson.com/journal/speaking-in-code-hands-free-input-with-talon/) | Control total del PC por voz, sonidos y mirada; se usa para programar | Gratis (no confirmado open source); comandos de la comunidad en GitHub | Prueba de que alguien con atrofia muscular espinal trabaja como desarrollador; la curva de aprendizaje es la barrera |
| [Cboard](https://www.GitHub.com/cboard-org/cboard) | Tablero de comunicación aumentativa (AAC) con símbolos y voz, en el navegador | GPL-3.0, PWA; 40+ idiomas, símbolos ARASAAC | Comunicación para quien no puede hablar; símbolos ARASAAC son de origen español |
| [Project Euphonia / Relate (Google)](https://sites.research.google/euphonia/about/) | Reconocimiento de voz personalizado para habla atípica | Dataset cerrado; herramientas de GitHub para entrenar modelos propios; solo inglés | Hueco claro: no hay equivalente maduro en español |
| [Look to Speak (Google)](https://www.boia.org/blog/googles-new-look-to-speak-app-lets-you-communicate-through-eye-gaze-tracking) | Elegir frases con la mirada en un celular Android | App gratuita, no open source | Interfaz mínima: dos direcciones de mirada bastan para comunicar |

Lectura: el acceso físico (entrada) es commodity. Lo escaso es la capa de arriba: convertir "puedo mover el cursor" en "puedo cobrar por un trabajo".

## Empleo e ingreso digital: seis modelos que ya existen

Los modelos que sobreviven cobran a empresas, no a la persona con discapacidad. El dato más fuerte a favor de la tesis: una herramienta de IA de comunicación subió 11% el ingreso de repartidores con discapacidad auditiva y redujo su brecha salarial de 8% a 3% ([AEI, abril 2026](https://ctse.aei.org/how-artificial-intelligence-is-reshaping-work-for-americans-with-disabilities/), resumiendo un estudio de la Universidad de Toronto).

| Modelo | Ejemplo | Quién paga | Tracción | Lección |
| --- | --- | --- | --- | --- |
| Matching laboral con ajustes declarados | [Inclusively](https://disabilityscoop.com/?p=30367) (EE.UU., 2020) | Empresas, suscripción anual | \~US$7M levantados; \~50 empresas y \~900 ONG aliadas | Las ONG son el canal de captación de usuarios; las empresas, el de ingreso |
| Plataforma de empleo con herramientas de IA por tipo de discapacidad | [Enabled Talent](https://betakit.com/?p=391640) (Canadá, 2025) | No publicado | 8.000 usuarios, 12 organizaciones (agosto 2025) | Fundador con baja visión; entró a programas de startups de AWS, Microsoft y Nvidia |
| Empleo directo de talento neurodivergente que se vende como servicio B2B | [Specialisterne](https://dobetter.esade.edu/en/inclusivity-financial-sustainability) (Dinamarca, 2004) | Empresas, contratos de servicio (testing, datos) | 26 países; más de 10.000 personas empleadas | El servicio directo da ingreso estable pero escala lento; la consultoría escala pero es menos predecible |
| Anotación de datos para IA con trabajadores con discapacidad | [Zhide](https://www.sixthtone.com/news/1014882) (Shanghái), [AcmeAI y Daivergent](https://humansintheloop.org/data-labeling-companies-with-a-social-impact/) | Empresas de IA | Zhide: 80 anotadores en 5 oficinas | Riesgo real: la automatización ya mató su negocio de call center; el anotador entrena a su reemplazo. Negociaron pago por hora en vez de por pieza |
| Gratis para el usuario, la empresa paga | [Be My Eyes](https://en.wikipedia.org/wiki/Be_My_Eyes) (Dinamarca, 2015) | Alianzas corporativas (Microsoft, Hilton, Tesco) | \~1M usuarios ciegos, \~10M voluntarios; Be My AI con GPT-4 desde 2023 | Una capa de IA encima de una comunidad existente se adoptó en semanas |
| Becas de formación tecnológica | [Por Talento Digital, Fundación ONCE](https://sid-inico.usal.es/noticias/fundacion-once-concede-mas-de-500-becas-tecnologicas-a-personas-con-discapacidad-con-su-programa-por-talento-digital/) (España, 2020) | Fundación | 541 becas a 2026 en IA, ciberseguridad, datos, web | Forma, pero no publica tasa de inserción: la formación sola no prueba ingreso |

Dos señales más:

- Un estudio de EY con más de 300 empleados con discapacidad o neurodivergentes en 17 organizaciones reportó impacto positivo de Copilot en su experiencia de trabajo, sin medir productividad ([IWIM/EY 2025](https://internationalwim.org/iwim-reports/genai-for-accessibility-more-human-not-less/)).
- El trabajo remoto se está achicando: en Reino Unido las vacantes 100% remotas cayeron de 8,7% a 4,3%, y 79% de \~1.200 adultos con discapacidad no aplicaría a un puesto sin opción remota ([Allwork, feb. 2026](https://allwork.space/2026/02/remote-jobs-are-disappearing-and-disabled-workers-are-paying-the-price)). El empleo remoto tradicional no basta; el ingreso por cuenta propia gana peso.

## IA y depresión: entrar por el trabajo, no por la terapia

La terapia con IA es terreno regulado y caro; una herramienta de productividad que aplica activación conductual no lo es. La vertical debe posicionarse como lo segundo, con derivación humana obligatoria ante señales de crisis.

| Caso | Qué pasó | Lección |
| --- | --- | --- |
| [Therabot (Dartmouth)](https://www.technologyreview.com/2025/03/28/1114001/the-first-trial-of-generative-ai-therapy-shows-it-might-help-with-depression/) | Ensayo aleatorizado de 8 semanas, 210 personas, NEJM AI (marzo 2025): síntomas de depresión bajaron 51% | Funcionó con datos clínicos curados y un psiquiatra revisando cada mensaje al inicio. Los autores advierten que no valida a la industria en general |
| [Woebot](https://www.statnews.com/2025/07/02/woebot-mental-health-chatbot-shuts-down-founder-says-ai-moving-faster-than-regulators/) | El chatbot pionero de terapia cerró su app en 2025 | Costo de la aprobación FDA y la imposibilidad de usar LLMs bajo esa regulación. Vender "terapia" ata el producto al regulador |
| [Ley WOPR, Illinois](https://www.axios.com/local/chicago/2025/08/06/illinois-ai-therapy-ban-mental-health-regulation) | Desde agosto 2025 prohíbe que una IA diagnostique o tome decisiones terapéuticas; multa de US$10.000 | Quedan permitidas las apps de bienestar y el uso administrativo. Otras jurisdicciones pueden copiarla |

Contexto local: el Ministerio de Salud Pública registró más de 1,2 millones de atenciones de salud mental en 2025, de ellas unas 146.000 por depresión, la segunda causa después de la ansiedad ([MSP vía EFE, enero 2026](https://elnuevodiario.com.do/ecuador-registro-mas-de-12-millones-de-atenciones-en-salud-mental-en-2025/)).

Pregunta abierta: qué dice la regulación ecuatoriana sobre apps de salud mental con IA. No encontré norma específica; hay que verificarlo con un abogado antes de lanzar.

## Ecuador y LatAm: la ley ya crea demanda pagada

En Ecuador más de un millón de personas viven con alguna discapacidad, pero solo 67.623 tienen empleo formal activo, y la ley obliga a las empresas a contratarlas. Esa cuota es un comprador B2B ya existente.

| Dato | Cifra | Fuente |
| --- | --- | --- |
| Personas con alguna discapacidad (INEC) | Más de 1 millón; 7 de cada 100 personas de 5 años o más (Censo 2022) | [DPL News, mar. 2026](https://dplnews.com/ecuador-claro-y-conadis-impulsan-los-emprendimientos/); [Primicias, ago. 2025](https://www.primicias.ec/revistagestion/analisis/personas-discapacidad-pobreza-103707/) |
| Registradas con carné (MSP) | 471.205 (enero 2022); 297.543 en edad de trabajar | [Vistazo, dic. 2022](https://www.vistazo.com/amp/enfoque/inclusividad-laboral-que-estipula-la-ley-organica-de-discapacidades-en-el-ecuador-HY4023328) |
| Con empleo formal activo | 67.623 (35.144 física); Azuay 4.197 | [El Diario, dic. 2025](https://www.eldiario.ec/ecuador/ministerio-del-trabajo-impulsa-programa-para-ampliar-la-inclusion-laboral-de-personas-con-discapacidad-en-ecuador-04122025/) |
| Cuota laboral obligatoria | 4%: una persona con discapacidad por cada 25 trabajadores, público y privado | [Vistazo, dic. 2022](https://www.vistazo.com/amp/enfoque/inclusividad-laboral-que-estipula-la-ley-organica-de-discapacidades-en-el-ecuador-HY4023328) |
| Multa por incumplir | Hasta 15 salarios básicos | Ídem |
| Despido sin causa | Indemnización de 18 meses del mejor salario | Ídem |
| América Latina | 1 de cada 7 personas; 150 millones proyectados a 2050; más informalidad y menos ingreso | [BID, dic. 2024](https://finanzasdigital.com/politicas-inclusion-discapacidad-america-latina-caribe-2024/) |

Tres detalles que importan para la vertical:

- **Sustitutos.** La cuota se puede cubrir hasta la mitad con "sustitutos": familiares que cuidan a una persona con discapacidad severa (75% o más), con jornada de 6 horas. El cuidador también es usuario posible.
- **El Estado ya forma, pero no da herramientas de IA.** El programa "Inclusión laboral con derechos" (diciembre 2025) ofrece cursos de 45 a 90 horas vía Encuentra Empleo y SECAP, gratis. Claro y CONADIS capacitan a emprendedores con discapacidad en marketing digital (marzo 2026).
- **Brecha de registro.** Hay más de un millón según el censo y \~471.000 con carné (cifras de años distintos). Quien no tiene carné no cuenta para la cuota.

Pregunta abierta: qué porcentaje de empresas obligadas cumple la cuota hoy. No hay cifra pública reciente en lo que revisé.

## Patrones que se repiten y huecos de mercado

El patrón claro: el acceso está resuelto, la plata la ponen las empresas, y nadie une acceso, agente de IA e ingreso en español.

**Lo que se repite**

1. **La capa de entrada es gratis y abierta.** Gameface, OptiKey, EyeGestures, ACAT y Talon cubren cara, ojos, voz y switches. No hay que construirla.
2. **El usuario no paga; paga la empresa.** Inclusively cobra suscripción a empleadores, Be My Eyes vive de alianzas corporativas, Specialisterne vende servicios B2B.
3. **Los fundadores tienen la experiencia en carne propia o en su familia.** Enabled Talent (fundador con baja visión), Inclusively (prima con síndrome de Down), Gameface (co-diseñado con Lance Carr). Es credibilidad y es canal.
4. **Formar no es lo mismo que generar ingreso.** Por Talento Digital lleva 541 becas y no publica tasa de inserción.
5. **El trabajo de bajo valor es frágil.** La anotación de datos con personas con discapacidad existe, pero la automatización ya eliminó el call center de Zhide.
6. **Vender "terapia con IA" es una trampa regulatoria.** Woebot cerró; Illinois multa.

**Huecos que encontré**

- No hay reconocimiento de voz para habla atípica maduro en español (Euphonia y Relate solo en inglés).
- Ningún proyecto revisado mide "experiencias de control" como métrica de producto, aunque la ciencia dice que ese es el mecanismo.
- En Ecuador existe demanda obligatoria (cuota del 4%) y oferta de personas que no pueden desplazarse, pero no encontré un puente de trabajo remoto aumentado con IA entre ambas.
- Los programas públicos forman (SECAP, Claro + CONADIS) pero no entregan un agente que ejecute el trabajo junto a la persona.

## Implicaciones para la vertical \[AI-proposed\]

Todo lo de esta sección es propuesta mía a partir de la investigación, no algo que hayas decidido. Mi lectura: la vertical no es "IA para discapacitados"; es un **copiloto de trabajo que devuelve el control**, vendido a empresas y validado con ingreso real.

**El ciclo de control que el producto debería repetir** (aplica Baratta 2023 + Bandura + activación conductual)

1. La persona elige una tarea concreta con resultado visible (no la IA).
2. El agente de IA ejecuta lo pesado con la entrada que la persona tenga: voz, mirada, cabeza.
3. La persona revisa y aprueba: la decisión final es suya.
4. El resultado sale al mundo: entregable enviado, pago recibido.
5. Queda registrado como logro acumulado, y la siguiente meta es un poco más grande.

**Decisiones que la investigación sugiere**

| Tema | Sugerencia | Por qué |
| --- | --- | --- |
| Posicionamiento | Herramienta de trabajo e ingreso, no de salud mental | Evita la trampa regulatoria de Woebot e Illinois |
| Quién paga | Empresas que deben cumplir la cuota del 4%, con talento remoto aumentado por IA | Demanda obligatoria que ya existe; patrón Inclusively y Specialisterne |
| Canal de usuarios | CONADIS, fundaciones, asociaciones de pacientes | Inclusively creció con \~900 ONG aliadas |
| Tipo de trabajo | Por encima de anotar datos: servicios que una persona con un agente puede entregar | La anotación es la primera que se automatiza |
| Capa de acceso | Integrar, no construir (Gameface, Voice Access, EyeGestures) | Ya es gratis y abierta |
| Métrica norte | Tareas completadas por la persona por semana, y días hasta el primer ingreso | Mide el mecanismo (control) y el resultado (dinero) |
| Seguridad | Protocolo de derivación humana ante señales de crisis desde el día 1 | Usuarios con depresión; Therabot necesitó supervisión humana |

**Decisiones abiertas para ti**

- ¿Proyecto aparte o módulo de Arthur/NUCLOUD?
- ¿Primer segmento: discapacidad física (la mayoría del empleo formal, 35.144) o depresión? Mezclar ambos en el piloto complica medir.
- ¿Piloto con tu mamá y 5 personas en Cuenca antes de escribir código?

## Útil hoy: control del celular y la PC desde la cama, gratis

Antes de construir nada, estas herramientas ya dan control a alguien en cama, y sirven para probar la tesis en casa. Ninguna reemplaza lo que indique el equipo médico o de fisioterapia.

| Herramienta | Dispositivo | Qué permite | Fuente |
| --- | --- | --- | --- |
| Voice Access | Android | Abrir apps, tocar, escribir y desplazarse solo con la voz; en español | [Ayuda de Google](https://support.google.com/accessibility/android/answer/6151848?hl=es) |
| Eye Tracking | iPhone o iPad con iOS 18 o superior | Navegar con la mirada usando la cámara frontal, sin hardware extra | [MacRumors](https://www.macrumors.com/2024/05/15/ios-18-accessibility-features) |
| Look to Speak | Android | Elegir frases con la mirada para comunicarse | [BOIA](https://www.boia.org/blog/googles-new-look-to-speak-app-lets-you-communicate-through-eye-gaze-tracking) |
| Project Gameface | PC con webcam | Mover el cursor con la cabeza y hacer clic con gestos de la cara | [Google](https://developers.googleblog.com/2023/06/project-gameface.html) |

Idea de prueba: medir con tu mamá qué tareas puede completar sola en una semana con estas herramientas. Esa observación es el primer dato real de la vertical.

## Fuentes

Páginas abiertas para esta investigación:

- [Baratta, Seligman y Maier (2023), From helplessness to controllability, Frontiers in Psychiatry](https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2023.1170417/full)
- [Maier y Seligman (2016), Learned helplessness at fifty, ficha PhilArchive](https://dc2.philarchive.org/rec/MAILHA)
- [Fuentes de autoeficacia de Bandura, Simply Psychology](https://www.simplypsychology.org/self-efficacy.html)
- [Ekers et al. (2014), meta-análisis de activación conductual](https://research.leedstrinity.ac.uk/en/publications/behavioural-activation-for-depression-an-update-of-meta-analysis-/)
- [Project Gameface, Google Developers](https://developers.googleblog.com/2023/06/project-gameface.html)
- [OptiKey, GitHub](https://github.com/OptiKey/OptiKey)
- [EyeGestures, ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fnativesensors%2Feyegestures)
- [ACAT, Intel GitHub](https://GitHub.com/intel/acat)
- [Talon y Blake Watson](https://blakewatson.com/journal/speaking-in-code-hands-free-input-with-talon/)
- [Cboard, GitHub](https://www.GitHub.com/cboard-org/cboard)
- [Project Euphonia, Google Research](https://sites.research.google/euphonia/about/)
- [AEI: IA y trabajo para personas con discapacidad (abr. 2026)](https://ctse.aei.org/how-artificial-intelligence-is-reshaping-work-for-americans-with-disabilities/)
- [EY / IWIM: GenAI for accessibility (2025)](https://internationalwim.org/iwim-reports/genai-for-accessibility-more-human-not-less/)
- [Inclusively, Disability Scoop](https://disabilityscoop.com/?p=30367)
- [Enabled Talent, BetaKit (ago. 2025)](https://betakit.com/?p=391640)
- [Specialisterne, Esade Do Better](https://dobetter.esade.edu/en/inclusivity-financial-sustainability)
- [Zhide y anotación de datos, Sixth Tone (abr. 2024)](https://www.sixthtone.com/news/1014882)
- [Empresas de etiquetado con impacto social, Humans in the Loop](https://humansintheloop.org/data-labeling-companies-with-a-social-impact/)
- [Be My Eyes, Wikipedia](https://en.wikipedia.org/wiki/Be_My_Eyes)
- [Por Talento Digital, SID-INICO (ago. 2026)](https://sid-inico.usal.es/noticias/fundacion-once-concede-mas-de-500-becas-tecnologicas-a-personas-con-discapacidad-con-su-programa-por-talento-digital/)
- [Trabajo remoto y discapacidad, Allwork (feb. 2026)](https://allwork.space/2026/02/remote-jobs-are-disappearing-and-disabled-workers-are-paying-the-price)
- [Therabot, MIT Technology Review (mar. 2025)](https://www.technologyreview.com/2025/03/28/1114001/the-first-trial-of-generative-ai-therapy-shows-it-might-help-with-depression/)
- [Cierre de Woebot, STAT (jul. 2025)](https://www.statnews.com/2025/07/02/woebot-mental-health-chatbot-shuts-down-founder-says-ai-moving-faster-than-regulators/)
- [Ley WOPR de Illinois, Axios (ago. 2025)](https://www.axios.com/local/chicago/2025/08/06/illinois-ai-therapy-ban-mental-health-regulation)
- [Salud mental en Ecuador 2025, MSP vía EFE](https://elnuevodiario.com.do/ecuador-registro-mas-de-12-millones-de-atenciones-en-salud-mental-en-2025/)
- [Inclusión laboral con derechos, El Diario (dic. 2025)](https://www.eldiario.ec/ecuador/ministerio-del-trabajo-impulsa-programa-para-ampliar-la-inclusion-laboral-de-personas-con-discapacidad-en-ecuador-04122025/)
- [Ley Orgánica de Discapacidades, Vistazo (dic. 2022)](https://www.vistazo.com/amp/enfoque/inclusividad-laboral-que-estipula-la-ley-organica-de-discapacidades-en-el-ecuador-HY4023328)
- [Discapacidad y pobreza, Primicias (ago. 2025)](https://www.primicias.ec/revistagestion/analisis/personas-discapacidad-pobreza-103707/)
- [Claro y CONADIS, DPL News (mar. 2026)](https://dplnews.com/ecuador-claro-y-conadis-impulsan-los-emprendimientos/)
- [Informe BID sobre discapacidad, Finanzas Digital (dic. 2024)](https://finanzasdigital.com/politicas-inclusion-discapacidad-america-latina-caribe-2024/)
- [Voice Access, Ayuda de Google](https://support.google.com/accessibility/android/answer/6151848?hl=es)
- [Eye Tracking en iOS 18, MacRumors](https://www.macrumors.com/2024/05/15/ios-18-accessibility-features)
- [Look to Speak, BOIA](https://www.boia.org/blog/googles-new-look-to-speak-app-lets-you-communicate-through-eye-gaze-tracking)
