# Handoff 24-09-2026 — Lecturameter 1999 en la web

Rama: `claude/busy-fermi-xuc4tk` (commits `bfd1f06`, `ee9244c` y este). Todo commiteado y pusheado.
NO fusionado a `main`: Víctor revisa los textos antes de publicar. Pages sirve `main`.

## 1. Dónde viven los textos

| Texto | Fichero | Dónde dentro del fichero |
|---|---|---|
| Sección landing ES | `es/index.html` | `<section ... id="lm1999">`, entre "Pronto en iOS" (diferencias) y el FAQ |
| Sección landing EN | `index.html` | mismo `id="lm1999"`, misma posición |
| Entrada blog ES | `es/blog/lecturameter-1999/index.html` | `<main>`: hero (título + entradilla) y 7 secciones |
| Entrada blog EN | `blog/lecturameter-1999/index.html` | idem |
| Tarjeta en índice blog | `es/blog/index.html`, `blog/index.html` | primera `.post-card` |
| Metadatos | `<head>` de las dos entradas | `title`, `description`, `og:*`, `twitter:*`, JSON-LD `BlogPosting` |

Enlaces añadidos: pill "1999" en la nav de portada y de los índices/entradas del blog, enlace "Lecturameter 1999"
en el footer (columna Producto), dos URL en `sitemap.xml` (lastmod 2026-09-24, también en las dos portadas).
CSS nuevo al final de `styles.css` (`.lm99-grid`, `.lm99-diff`, `.lm99-cta`), versión `styles.css?v=6.3` en las dos portadas.

## 2. Capturas

`capturas-1999/` (9 PNG, 1080x2400, 256 colores, 60-90 KB):
`lm99_biblioteca`, `lm99_cronometro`, `lm99_crono_minimizado`, `lm99_guardar_sesion`, `lm99_historial`,
`lm99_informe`, `lm99_informe_calendario`, `lm99_nuevo_libro`, `lm99_pagi_consejo`.

Se renderizaron desde el código real de `lecturameter-rebuilds/lm-1999` (`b428c06`) en un target JVM de
Compose Multiplatform, con Roboto, sin barra de estado del móvil y con datos de muestra (7 clásicos con
portadas de dominio público de Standard Ebooks, 39 sesiones generadas). Herramienta y receta en
`tools/lm99-capturas/README.md`. Si se prefieren capturas del 13T Pro con la biblioteca real, basta con
sustituir los PNG con el mismo nombre; las páginas declaran `width="1080" height="2400"`.

## 3. Decisiones tomadas hoy (Víctor)

- El producto se llama Lecturameter 1999. "Lecturameter 99" solo aparece dentro de la app (título de ventana).
- Llegará gratis a Play Store y App Store, después de Lecturameter para iOS y de la 3.7. Sin fecha.
- Narrativa: iOS resultó más fácil de lo previsto y 3.7 iba medio hecha; hubo tiempo para el experimento de
  los siete rebuilds; el 1999 fue el favorito y se terminó como ejercicio divertido.
- Sin em dashes, sin emojis, sin la muletilla "no es X, es Y" en los textos.

## 4. Pendiente, en orden

1. **Víctor revisa los textos** (ES es la fuente; EN es traducción directa). Tras el OK: `git checkout main && git merge claude/busy-fermi-xuc4tk && git push`.
2. **Formulario de lista de espera del 1999** (pedido el 24-09, sin hacer). Especificación:
   - Mismo mecanismo que la lista iOS (`submitIosWaitlist` en `main.js`: mailto a `lecturameter.app@gmail.com`
     con captcha de suma). Añadir `window.submitLm99Waitlist(e, lang)` que no rompa el existente.
   - Campos: email (obligatorio), nombre (opcional), dos casillas "Android" e "iOS" (se pueden marcar una o las dos,
     al menos una obligatoria), captcha, botón "Avísame" / "Notify me".
   - Asunto del mailto: `Lecturameter 1999 waitlist`; cuerpo con email, nombre y plataformas.
   - Ojo: el generador de captcha actual usa `document.querySelector('.ios-captcha-question')` (solo el primero).
     Cambiarlo a `querySelectorAll` para que el segundo formulario también reciba `data-expected`.
   - Colocarlo dentro de `#lm1999`, después del bloque "Qué cambia respecto a Lecturameter", sustituyendo o
     acompañando a `.lm99-cta`. Reutilizar clases `.ios-waitlist`, `.ios-captcha-row`, `.ios-note`, `.ios-status`.
   - Subir `main.js?v=5.5` en `index.html` y `es/index.html`.
3. **Documentación del repo principal**: añadir en `Lecturameter/Documentacion/manual/MD10` (landing) la sección
   `#lm1999`, las dos entradas de blog y la carpeta `capturas-1999/`. No se tocó desde esta sesión (repo distinto).
4. **App 1999, idiomas** (idea de Víctor 24-09, fuera de esta web): traducir `lm-1999` a los 40 idiomas de la app real
   reutilizando sus recursos de i18n con otra UI, y añadir un selector de idioma. Cuando exista, actualizar en la web
   la línea "Solo en castellano, de momento" (sección y blog, ES y EN) y la nota del blog EN
   "The app is in Spanish for now, so the screenshots are too.", y rehacer capturas en inglés si se quiere.
5. iOS del 1999: `rememberOpenTextFile` / `rememberCreateTextFile` son stubs en `Platform.ios.kt`. Hay que implementarlos
   antes de App Store. Los textos de la web no lo mencionan.

## 5. Verificado / sin probar

- Verificado: render en Chromium local de la sección ES/EN a 1280 y 390 px, entrada ES, índice EN; sin errores JS;
  lightbox con `data-lbx`; cada afirmación de los textos contrastada con el código de `lm-1999`.
- Sin probar: ancla `#lm1999` desde el menú hamburguesa en móvil real; Safari; validación W3C del HTML nuevo.
