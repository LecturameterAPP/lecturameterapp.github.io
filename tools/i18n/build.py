#!/usr/bin/env python3
"""Generador estatico de la landing: plantillas + i18n/<code>.json -> HTML.

Uso:  python tools/i18n/build.py
Solo libreria estandar. Ver tools/i18n/README.md.
"""
import json
import os
import posixpath
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MARK = re.compile(r'\{\{(json:)?([A-Za-z0-9_.@\-]+)\}\}')


class BuildError(Exception):
    pass


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def rel(from_dir, target):
    """Ruta relativa (con ./ o ../) desde from_dir hasta target; ambos relativos a la raiz del sitio."""
    r = posixpath.relpath(target.rstrip('/') or '.', from_dir.rstrip('/') or '.')
    if r == '.':
        r = './'
    elif not r.startswith('..'):
        r = './' + r
    if (target.endswith('/') or r.endswith('..') or r == '.') and not r.endswith('/'):
        r += '/'
    return r


def page_dir(loc, page):
    return loc['path'].strip('/') and (loc['path'].strip('/') + '/' + page['dir']) or page['dir']


def build_vars(cfg, loc, pname, page, others):
    pdir = page_dir(loc, page).rstrip('/')
    here = pdir
    site = cfg['site_url']
    v = {
        'code': loc['code'],
        'dir': loc['dir'],
        'img': loc['img'],
        'shots99': loc['shots99'],
        'og_locale': loc['og_locale'],
        'site_url': site,
        'root': rel(here, ''),
        'home': rel(here, loc['path'].lstrip('/')),
        'link_blog': rel(here, loc['blog']),
        'link_1999': rel(here, loc['path'].lstrip('/') + 'lecturameter-1999/'),
        'page_url': site + pdir + ('/' if pdir else ''),
        'head_redirect': '',
    }
    for k, p in loc['features'].items():
        v['link_feat_' + k] = rel(here, p)
    # idioma alterno (solo para el boton ES/EN provisional del paso 1)
    alt = [o for o in others if o is not loc]
    if len(alt) == 1:
        a = alt[0]
        v['alt_href'] = rel(here, page_dir(a, page))
        v['alt_code_upper'] = a['code'].upper()
    # og:locale:alternate
    v['og_locale_alternates'] = ''.join(
        '    <meta property="og:locale:alternate" content="%s">\n' % o['og_locale'] for o in others if o is not loc)
    # hreflang
    lines = []
    for o in others:
        u = site + page_dir(o, page).rstrip('/')
        u += '/' if page_dir(o, page) else ''
        lines.append('    <link rel="alternate" hreflang="%s" href="%s">\n' % (o['hreflang'], u))
    xd = site + page['dir']
    lines.append('    <link rel="alternate" hreflang="x-default" href="%s">\n' % xd)
    v['hreflang_links'] = ''.join(lines)
    return v


def render(text, variables, strings, where, errors, depth=0):
    if depth > 6:
        raise BuildError('plantillas anidadas en bucle en ' + where)

    def sub(m):
        as_json, key = m.group(1), m.group(2)
        if key in variables:
            val = variables[key]
        elif key in strings:
            val = strings[key]
        else:
            errors.append('%s: clave inexistente {{%s}}' % (where, key))
            return m.group(0)
        if '{{' in val:
            val = render(val, variables, strings, where, errors, depth + 1)
        if as_json:
            val = json.dumps(val, ensure_ascii=False)[1:-1]
        return val
    return MARK.sub(sub, text)


def main():
    cfg = load_json(os.path.join(ROOT, 'i18n', 'locales.json'))
    locales = cfg['locales']
    errors = []
    written = []
    for loc in locales:
        strings = load_json(os.path.join(ROOT, 'i18n', loc['code'] + '.json'))
        for pname, page in cfg['pages'].items():
            tpl_path = os.path.join(ROOT, 'src', 'templates', page['template'])
            with open(tpl_path, encoding='utf-8', newline='') as f:
                tpl = f.read()
            variables = build_vars(cfg, loc, pname, page, locales)
            where = '%s/%s' % (loc['code'], page['template'])
            out = render(tpl, variables, strings, where, errors)
            out_rel = page_dir(loc, page) + 'index.html'
            written.append((os.path.join(ROOT, *out_rel.split('/')), out))
    if errors:
        for e in sorted(set(errors)):
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
    for path, out in written:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('ok', os.path.relpath(path, ROOT).replace(os.sep, '/'))


if __name__ == '__main__':
    try:
        main()
    except BuildError as e:
        print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
