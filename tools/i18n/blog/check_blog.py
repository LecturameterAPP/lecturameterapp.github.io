#!/usr/bin/env python3
"""Valida i18n/blog/<code>.json contra i18n/blog/en.json.

Uso:  python tools/i18n/blog/check_blog.py <codigo> [<codigo> ...]
      python tools/i18n/blog/check_blog.py --file ruta.json     (otro fichero, se compara con en.json)
      python tools/i18n/blog/check_blog.py --all                (todos los i18n/blog/<code>.json salvo en/es)

Errores (salida 1): claves que faltan o sobran, valores vacios, etiquetas HTML distintas (nombre, orden y
href), entidades (&middot; ...) distintas, numeros distintos (se comparan las cifras, no los separadores:
1,543 == 1.543), URLs distintas, emojis anadidos, comillas dobles / '<' / '&' sueltos en claves que
van a atributos, marcas ausentes. Avisos (no fallan): marca con distinto numero de apariciones,
valor identico al ingles en textos de mas de 4 palabras.
Solo libreria estandar.
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
BLOG = os.path.join(ROOT, 'i18n', 'blog')
BRANDS = ['Lecturameter', 'Pagi', 'Goodreads', 'StoryGraph', 'Bookmory', 'ShelfBridge', 'Google Play', 'App Store']
TAG = re.compile(r'<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)([^>]*)>')
HREF = re.compile(r'href\s*=\s*"([^"]*)"')
ENTITY = re.compile(r'&#?[A-Za-z0-9]+;')
URL = re.compile(r'https?://[^\s"<>]+|[\w.+-]+@[\w-]+\.[\w.]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|io|co)\b')
DIGITS = re.compile(r'\d+')
EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]')
BARE_AMP = re.compile(r'&(?!#?[A-Za-z0-9]+;)')


def is_attr_key(k):
    last = k.rsplit('.', 1)[-1]
    return (last in ('title', 'description', 'og_description', 'og_image_alt', 'site_title', 'short_title')
            or last.startswith('alt_'))


def tags(v):
    out = []
    for m in TAG.finditer(v):
        out.append((m.group(1), m.group(2).lower()))
    return out


def check(en, tr, label='?'):
    errors, warns = [], []
    for k in en:
        if k not in tr:
            errors.append('falta la clave %s' % k)
    for k in tr:
        if k not in en:
            errors.append('clave desconocida %s' % k)
    for k, e in en.items():
        if k not in tr:
            continue
        v = tr[k]
        if not isinstance(v, str):
            errors.append('%s: el valor debe ser texto' % k)
            continue
        if not v.strip():
            errors.append('%s: vacia' % k)
            continue
        if tags(e) != tags(v):
            errors.append('%s: etiquetas HTML distintas (en: %s | tr: %s)' % (
                k, ' '.join(('/' if c else '') + n for c, n in tags(e)) or '-',
                ' '.join(('/' if c else '') + n for c, n in tags(v)) or '-'))
        if HREF.findall(e) != HREF.findall(v):
            errors.append('%s: href distintos (en: %s | tr: %s)' % (k, HREF.findall(e), HREF.findall(v)))
        if Counter(ENTITY.findall(e)) != Counter(ENTITY.findall(v)):
            errors.append('%s: entidades distintas (en: %s | tr: %s)' % (k, ENTITY.findall(e), ENTITY.findall(v)))
        if Counter(DIGITS.findall(e)) != Counter(DIGITS.findall(v)):
            errors.append('%s: cifras distintas (en: %s | tr: %s)' % (k, DIGITS.findall(e), DIGITS.findall(v)))
        if Counter(URL.findall(e)) != Counter(URL.findall(v)):
            errors.append('%s: URLs/dominios distintos (en: %s | tr: %s)' % (k, URL.findall(e), URL.findall(v)))
        if EMOJI.search(v) and not EMOJI.search(e):
            errors.append('%s: emoji anadido' % k)
        if is_attr_key(k):
            if '"' in v or '<' in v or '>' in v:
                errors.append('%s: no puede llevar comillas dobles ni < > (va en un atributo/title)' % k)
            if BARE_AMP.search(v):
                errors.append('%s: "&" suelto; escribe &amp;' % k)
        for b in BRANDS:
            ce, ct = e.count(b), v.count(b)
            if ce and not ct:
                errors.append('%s: falta la marca "%s" (no se traduce ni se transcribe)' % (k, b))
            elif ce != ct:
                warns.append('%s: la marca "%s" aparece %d veces (en: %d)' % (k, b, ct, ce))
        if v == e and len(re.sub(r'<[^>]*>', ' ', e).split()) > 4:
            warns.append('%s: identico al ingles' % k)
    return errors, warns


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    en = load(os.path.join(BLOG, 'en.json'))
    jobs = []
    if argv[0] == '--file':
        jobs.append((argv[1], argv[1]))
    elif argv[0] == '--all':
        for f in sorted(os.listdir(BLOG)):
            if f.endswith('.json') and not f.startswith('_') and f[:-5] not in ('en', 'es'):
                jobs.append((f[:-5], os.path.join(BLOG, f)))
    else:
        for c in argv:
            jobs.append((c, os.path.join(BLOG, c + '.json')))
    bad = 0
    for label, path in jobs:
        if not os.path.exists(path):
            print('%s: no existe %s' % (label, path))
            bad += 1
            continue
        try:
            tr = load(path)
        except ValueError as ex:
            print('%s: JSON invalido: %s' % (label, ex))
            bad += 1
            continue
        errors, warns = check(en, tr, label)
        same = [w for w in warns if w.endswith('identico al ingles')]
        for w in warns:
            if w not in same:
                print('%s: AVISO %s' % (label, w))
        if same:
            print('%s: AVISO %d claves identicas al ingles (sin traducir?): %s' % (
                label, len(same), ', '.join(w.split(':')[0] for w in same[:8]) + (' ...' if len(same) > 8 else '')))
        for e in errors:
            print('%s: ERROR %s' % (label, e))
        print('%s: %s (%d claves, %d errores, %d avisos)' % (
            label, 'OK' if not errors else 'FALLA', len(tr), len(errors), len(warns)))
        bad += bool(errors)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
