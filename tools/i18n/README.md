# Generador de la landing (i18n)

Las paginas `index.html`, `es/index.html`, `lecturameter-1999/index.html` y
`es/lecturameter-1999/index.html` NO se editan a mano: salen de
`src/templates/*.html` + `i18n/<codigo>.json` + `i18n/locales.json`.

## Regenerar

    python tools/i18n/build.py

Solo libreria estandar. Si falta una clave en algun idioma, o una plantilla
usa una clave inexistente, el build falla y no escribe nada. Hay que
commitear la salida generada (GitHub Pages sirve los HTML tal cual).

## Marcadores

- `{{clave}}`: texto de `i18n/<codigo>.json` (puede llevar HTML) o variable calculada
  (`root`, `home`, `img`, `link_feat_*`, `link_blog`, `link_1999`, `page_url`...).
- `{{json:clave}}`: igual, escapado para ir dentro de una cadena JSON (JSON-LD).

## Anadir un idioma

1. Anadir su bloque en `i18n/locales.json` (`code`, `hreflang`, `path`, `dir`,
   `nativeName`, `og_locale`, `img`, `shots99`, `blog`, `features`).
2. Copiar `i18n/en.json` a `i18n/<codigo>.json` y traducir los valores (todas las claves).
3. `python tools/i18n/build.py` y commitear.
