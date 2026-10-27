"""Utilidades compartidas por extract.py y apply.py (aplanado de i18n/en.json y reglas de exclusion)."""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WORK = os.path.join(ROOT, 'tools', 'i18n', 'work')

# Marcas de los textos: {{var}}, %s, %d, %1$s, {0}
PLACEHOLDER = re.compile(r'\{\{[^}]*\}\}|%\d*\$?[sd]|\{\d+\}')
URL = re.compile(r'https?://[^\s"<>]+|mailto:[^\s"<>]+|[\w.+-]+@[\w-]+\.[\w.]+')
BRANDS = ['Lecturameter', 'Pagi', 'Google Play', 'App Store', 'KOSync', 'KOReader', 'Goodreads', 'StoryGraph',
          'Storygraph', 'TestFlight', 'Google Drive', 'iCloud', 'Reddit', 'PayPal', 'Ko-fi', 'Linktree',
          'Instagram', 'X / Twitter', 'Discord', 'iOS', 'Android', 'OLED', 'Pro', 'FAQ', 'ISBN', 'Wrapped']


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def flatten(d):
    """clave -> texto; listas: 'clave#i'; listas de objetos: 'clave#i.campo'."""
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = v
        else:
            for i, x in enumerate(v):
                if isinstance(x, str):
                    out['%s#%d' % (k, i)] = x
                else:
                    for f, t in x.items():
                        out['%s#%d.%s' % (k, i, f)] = t
    return out


def plain(v):
    """Texto sin etiquetas, entidades ni marcadores."""
    v = re.sub(r'<[^>]*>', ' ', v)
    v = re.sub(r'&#?\w+;', ' ', v)
    v = PLACEHOLDER.sub(' ', v)
    return URL.sub(' ', v)


def translatable(key, en):
    """False para URLs, numeros, precios, nombres propios y claves de config."""
    base = key.split('#')[0]
    if base.endswith('.href') or base.startswith('anchor.'):
        return False
    t = plain(en)
    for b in BRANDS:
        t = t.replace(b, ' ')
    if not re.search(r'[^\W\d_]', t):
        return False
    return True


def note_for(key, en):
    base = key.split('#')[0]
    notes = []
    if base.endswith('.alt'):
        notes.append('texto alternativo de imagen')
    elif base.endswith('.aria-label'):
        notes.append('etiqueta de accesibilidad de un boton/enlace')
    elif base.startswith('head.'):
        notes.append('etiqueta SEO (title/description/og); sin comillas dobles')
    elif base.startswith('js.'):
        notes.append('frase corta de Pagi que sale al tocarlo')
    elif base.startswith('legal.') and re.search(r'\.(h\d|dtitle)_', base):
        notes.append('titulo')
    elif base.startswith('legal.'):
        notes.append('texto legal: traduce con fidelidad, sin anadir ni quitar')
    elif base.startswith('common.nav.') or base.startswith('common.footer.'):
        notes.append('enlace/etiqueta de navegacion')
    if '<' in en:
        notes.append('contiene HTML: conserva las etiquetas y los href')
    if PLACEHOLDER.search(en):
        notes.append('conserva los marcadores ' + ' '.join(sorted(set(PLACEHOLDER.findall(en)))))
    if base.endswith('@live'):
        notes.append('variante cuando iOS esta publicada')
    return '; '.join(notes)
