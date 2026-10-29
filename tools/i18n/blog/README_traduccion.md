# Traduccion del blog (47 idiomas)

El blog solo existe a mano en ingles (`blog/`) y espanol (`es/blog/`, slugs en espanol). Para los otros 47
idiomas se genera `/<codigo>/blog/` (indice) y `/<codigo>/blog/<slug-en>/` (mismo slug ingles) con
`tools/i18n/build_blog.py` a partir de `src/templates/blog-*.html` + `i18n/blog/<codigo>.json`.
`es` y `en` NO se regeneran.

## Que se entrega por idioma

Un unico fichero `i18n/blog/<codigo>.json` (UTF-8), plano `clave -> texto`, **con exactamente las mismas
193 claves que `i18n/blog/en.json`** (la fuente). Copia `en.json` a `<codigo>.json` y traduce los valores.
Los textos comunes (menu, pie, selector de idioma, "Get on Google Play"...) ya salen de `i18n/<codigo>.json`
y NO se tocan aqui.

Codigos: `ar bg bn ca cs da de el et fa fi fr gu he hi hr hu id is it ja kn ko lt lv ml mr nl no pa pl pt pt-br
ro ru sk sl sv sw ta te tr uk ur vi zh-cn zu`.

## Claves (193; ~20 400 caracteres, ~3 550 palabras por idioma)

Prefijo `blog.<alias>.`: `l99` = Lecturameter 1999, `hfr` = how-fast-do-i-really-read,
`fvm` = fantasy-vs-manga-reading-pace, `rtp` = reading-time-vs-pages, `egl` = export-goodreads-library.
Ademas `blog.common.*` (5) y `blog.index.*` (8).

| Sufijo | Uso | Notas |
|---|---|---|
| `title` | h1, `<title>`, og/twitter, JSON-LD, tarjeta del indice | texto plano |
| `description`, `og_description` | meta description, og/twitter, JSON-LD, tarjeta | texto plano |
| `tagline` | subtitulo bajo el h1 | |
| `h2_NN`, `p_NN`, `li_NN`, `figcaption_NN`, `label_NN` | cuerpo | algunos llevan HTML (abajo) |
| `alt_NN` | `alt` de imagenes | texto plano |
| `short_title` | enlace "Ver tambien" desde otros articulos | texto plano, corto |
| `val_time` | `29h 41m` (cifra con unidades) | adaptar solo las letras h/m |
| `blog.l99.footer_privacy` | enlace del pie "Privacy 1999" | |

### Claves de atributo (title, description, og_description, og_image_alt, site_title, short_title, alt_NN)
Van dentro de `content="..."`, `alt="..."` o `<title>`: **sin comillas dobles `"`, sin `<` `>`, y el `&` se
escribe `&amp;`**. Para comillas usa tipograficas del idioma (« » „ " 「」) o simples.

### Claves con HTML (hay que conservar las etiquetas, su orden y los `href`)
`<strong>`, `<em>`, `<a href="...">` (14 claves): `blog.l99.p_19`, `blog.hfr.p_01`, `blog.hfr.p_04`,
`blog.hfr.p_06`, `blog.fvm.p_02`, `p_03`, `p_04`, `p_06`, `p_07`, `p_09`, `blog.rtp.p_10`, `blog.egl.p_08`,
`p_10`, `p_11`. Traduce solo el texto entre etiquetas; las etiquetas pueden moverse dentro de la frase pero
deben ser las mismas y en el mismo orden (`<strong>` ... `</strong>`). Otras 5 claves llevan solo entidades
(`&middot;`, `&gt;`): conservalas tal cual (`blog.common.free_line` etc.).
`&gt;` en "Settings &gt; Export" es un `>` escapado: no lo escribas como `>`.

## Que NO traducir

- Marcas y nombres de producto, en caracteres latinos: **Lecturameter, Pagi, Lecturameter 1999, Goodreads,
  StoryGraph, Bookmory, Fable, ShelfBridge, Book Tracker, Babelio, Pagebound, Bookshelf, Delibrista, Google
  Play, App Store, Android, iOS, Pro, CSV, XLSX, ISBN, X, Reddit, Wittgenstein, Sanderson**.
- URLs y dominios (`goodreads.com`, `app.thestorygraph.com`, `https://...`), valores de `href`.
- Cifras: todas se conservan (se admite cambiar solo el separador decimal/millares: `0.63` -> `0,63`,
  `1,543` -> `1.543`; los digitos no cambian). Formatos como `YYYY/MM/DD` se conservan literales.
- Titulos de obras (The Dragon Reborn, Frieren, Chainsaw Man, Dan Da Dan, Hábito y mortaja) no se traducen.
  Los nombres de opciones de apps externas que se citan entre comillas ("My Books", "Import and export",
  "Export Library"...) se pueden dejar en ingles si asi aparecen en esa web, o traducir si esa web esta
  localizada; ante la duda, ingles.
- Los nombres de pantallas de la app de Lecturameter (Ajustes, Importar...) deben coincidir con la app en ese
  idioma (glosario: `tools/i18n/work/glossary/<codigo>.json`, si existe).
- No anadir emojis, ni quitar/anadir frases, ni cambiar los numeros de sesiones, paginas o minutos.
- Texto en primera persona (el autor): se mantiene.

## Validar

    python tools/i18n/blog/check_blog.py <codigo>            # un idioma (lee i18n/blog/<codigo>.json)
    python tools/i18n/blog/check_blog.py --all               # todos los presentes
    python tools/i18n/blog/check_blog.py --file ruta.json    # otro fichero

Falla (salida 1) si: faltan/sobran claves, hay claves vacias, las etiquetas HTML o los `href` difieren,
las entidades difieren, las cifras difieren, las URLs difieren, hay emojis nuevos, hay `"` `<` `>` o `&`
suelto en claves de atributo, o falta una marca. Avisa (no falla) si una marca aparece distinto numero de
veces o si hay claves identicas al ingles (posible texto sin traducir).

## Generar

    python tools/i18n/build_blog.py                  # todos los i18n/blog/<codigo>.json (menos en/es)
    python tools/i18n/build_blog.py --code de        # solo uno
    python tools/i18n/build.py                       # despues, para que los enlaces "Blog" de las
                                                     # paginas principales apunten a /<codigo>/blog/

Cada `<codigo>/blog/...` generado: `lang`/`dir`, canonical, hreflang entre todos los idiomas disponibles
(en y es incluidos con sus slugs espanoles), og/twitter, JSON-LD, selector de idioma que lleva al mismo
articulo. Ademas el script:

- anade las URLs al `sitemap.xml` entre `<!-- blog-i18n:start/end -->` (no toca las entradas existentes;
  `build.py` las respeta);
- anade entre `<!-- blog-i18n:start/end -->` los `hreflang` de los idiomas nuevos en los HTML en/es del blog
  (solo en `<head>`, el contenido no cambia).

Mientras no exista `i18n/blog/<codigo>.json`, `build.py` sigue enlazando al blog ingles. Si falta una clave,
el build falla sin escribir nada. Hay que commitear la salida generada.

Prueba sin tocar el repo: `python tools/i18n/build_blog.py --code de --src i18n/blog/_pilot_de.json --out <dir>`
(los ficheros que empiezan por `_` se ignoran en el build real).
