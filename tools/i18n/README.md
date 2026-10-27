# Generador de la landing (i18n)

Las paginas `index.html`, `es/index.html`, `lecturameter-1999/index.html` y
`es/lecturameter-1999/index.html` NO se editan a mano: salen de
`src/templates/*.html` + `i18n/<codigo>.json` + `i18n/locales.json`.
El build tambien regenera en `sitemap.xml` las entradas de esas paginas (con sus
`xhtml:link` alternates) y deja el resto del sitemap como esta.

## Regenerar

    python tools/i18n/build.py

Solo libreria estandar. Si falta una clave en algun idioma, una plantilla usa una
clave inexistente o falta una captura en todas las versiones, el build falla y no
escribe nada. Hay que commitear la salida generada (GitHub Pages sirve los HTML tal
cual). Las capturas que faltan solo en la version actual salen como `WARNING` en consola.

## Marcadores en las plantillas

- `{{clave}}`: texto de `i18n/<codigo>.json` (puede llevar HTML) o variable calculada
  (`root`, `home`, `img`, `link_feat_*`, `link_blog`, `link_1999`, `page_url`, `ios_url`...).
- `{{json:clave}}`: igual, escapado para ir dentro de una cadena JSON (JSON-LD).
- `{{shot:nombre.jpg}}` / `{{shot_abs:nombre.jpg}}`: ruta (relativa / absoluta) de una captura,
  segun `screenshots` en `locales.json` (ver "Capturas por version").
- `{{#if var}}...{{/if}}` y `{{#unless var}}...{{/unless}}`, cada marcador en su propia linea.
- `clave@live`: variante de una clave que se usa cuando `ios_live` es true.
- Claves `js.*`: se inyectan en `<script id="lm-i18n">` y las lee `main.js` (pueden ser listas).

## Anadir un idioma

1. Anadir su bloque en `i18n/locales.json` (`code`, `hreflang`, `path`, `dir`,
   `nativeName`, `og_locale`, `img`, `shots99`, `blog`, `features`).
2. Copiar `i18n/en.json` a `i18n/<codigo>.json` y traducir los valores (todas las claves,
   incluidas `release.*`, `roadmap.*`, las variantes `@live` y los `anchor.*`, que pueden
   repetir los del ingles).
3. Capturas de ese idioma en las carpetas de `screenshots` (ver abajo).
4. `python tools/i18n/build.py` y commitear.

## iOS publicada (`ios_live`)

En `i18n/locales.json`: `"ios_live": true` y `"app_store_url": "https://apps.apple.com/..."`.
Con eso todos los CTA de iPhone pasan a "Download on the App Store" con esa URL y
desaparece TestFlight. Si `ios_live` es true con `app_store_url` vacio, el build falla.

## Contenido por version

`current_release` (p. ej. `"3.8"`) y `release_order` (`["3.7","3.8","3.9"]`) mandan:

- Notas de parche: `release.<v>.new` / `release.<v>.fixes` (listas, `3.8` -> `release.3_8.*`).
- Historial: las versiones <= `current_release` con notas, la mas nueva arriba
  (`release.<v>.headline` es el titular). Las entradas 3.6 y 3.5 estan a mano en la plantilla.
- Roadmap: `roadmap.<siguiente>.heading|sub|cards` de la version que sigue en `release_order`.
  Si no tiene contenido, la seccion, su enlace de nav, el del pie y el boton de las notas desaparecen.

### Capturas por version

`screenshots.<v>.dir` y `.suffix` en `locales.json` (admiten `{code}` e `{img}`):

- 3.8: `capturas para v3/` + `<nombre>_<img>.<ext>` (las actuales).
- 3.9: `capturas/3.9/<codigo>/<nombre>.<ext>` (sin sufijo).

Si falta una captura en la version actual el build usa la de la version anterior y avisa.

### El dia que sale la 3.9

1. `i18n/locales.json`: `"current_release": "3.9"`.
2. Copiar las capturas nuevas a `capturas/3.9/<codigo>/` (mismos nombres que las de 3.8 sin el
   sufijo de idioma, p. ej. `captura_libros_real_claro.jpg`, `tema_ocaso.jpg`). Las que falten
   seguiran saliendo de 3.8 con un WARNING.
3. Repasar `release.3_9.*` en cada idioma contra las notas reales de Play de la 3.9: el texto actual
   es un BORRADOR sacado solo de `promo_39_*_v2.json`. Sin 3.10 en `release_order`, el roadmap se oculta.
4. `python tools/i18n/build.py`, mirar los WARNING, revisar la web en local y commitear la salida.
