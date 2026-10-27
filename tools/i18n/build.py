#!/usr/bin/env python3
"""Generador estatico de la landing: plantillas + i18n/<code>.json -> HTML.

Uso:  python tools/i18n/build.py
Solo libreria estandar. Ver tools/i18n/README.md.
"""
import datetime
import html
import json
import os
import posixpath
import re
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MARK = re.compile(r'\{\{(json:|shot:|shot_abs:)?([A-Za-z0-9_.@\-]+)\}\}')


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
    # redireccion por idioma: solo en las paginas del idioma por defecto (raiz)
    if loc['path'] == '/':
        v['head_redirect'] = redirect_script(cfg, page, others)
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


def pick(strings, key, live):
    """Texto de una clave; si iOS esta publicada y existe la variante 'clave@live', usa esa."""
    if live and key + '@live' in strings:
        return strings[key + '@live']
    return strings[key]


def js_payload(strings, live=False):
    """Claves js.* -> objeto JSON que lee main.js (script#lm-i18n). Seguro dentro de <script>."""
    data = {k[3:]: pick(strings, k, live) for k in strings if k.startswith('js.') and not k.endswith('@live')}
    raw = json.dumps(data, ensure_ascii=False)
    return raw.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


REDIRECT_JS = (
    "(function(){try{var L=%s;var s=null;try{s=localStorage.getItem('lm_lang')}catch(e){}var t=null;"
    "if(s){if(L[s])t=s}else{var ls=navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||''];"
    "for(var i=0;i<ls.length;i++){var l=String(ls[i]).toLowerCase().replace('_','-');var c;"
    "if(l==='pt-br')c='pt-br';else if(l.indexOf('pt')===0)c='pt';else if(l.indexOf('zh')===0)c='zh-cn';"
    "else if(l==='nb'||l==='nn'||l.indexOf('nb-')===0||l.indexOf('nn-')===0)c='no';"
    "else if(l==='iw'||l.indexOf('iw-')===0)c='he';else if(l==='in'||l.indexOf('in-')===0)c='id';"
    "else c=l.split('-')[0];if(L[c]){t=c;break}}}"
    "if(t&&t!=='%s')location.replace(L[t]+location.hash)}catch(e){}})();")


def redirect_script(cfg, page, locales):
    table = {o['code']: '/' + page_dir(o, page) for o in locales}
    return '    <script>' + (REDIRECT_JS % (json.dumps(table, separators=(',', ':')), cfg['default_locale'])) + '</script>\n'


GLOBE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
         '<path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/></svg>')


def lang_picker(loc, page, locales, strings, indent):
    """Selector de idioma: cada opcion es un <a href> real a la misma pagina en ese idioma."""
    here = page_dir(loc, page).rstrip('/')
    esc = html.escape
    opts = []
    for o in locales:
        target = page_dir(o, page)
        cur = o is loc
        opts.append(
            '<a href="%s" lang="%s" hreflang="%s" data-code="%s" data-search="%s"%s>%s</a>' % (
                rel(here, target), esc(o['code']), esc(o['hreflang']), esc(o['code']),
                esc((o['nativeName'] + ' ' + o['code']).lower()),
                ' class="current" aria-current="true"' if cur else '', esc(o['nativeName'])))
    lines = [
        '<div class="lang-picker">',
        '    <button type="button" class="nav-lang-btn lang-btn" aria-haspopup="true" aria-expanded="false"'
        ' aria-controls="lang-panel" aria-label="%s">' % esc(strings['common.lang.label']),
        '        ' + GLOBE,
        '        <span class="long">%s</span><span class="short">%s</span> <span aria-hidden="true">▾</span>' % (
            esc(loc['nativeName']), esc(loc['code'].upper())),
        '    </button>',
        '    <div class="lang-panel" id="lang-panel" hidden>',
        '        <input type="search" class="lang-search" placeholder="%s" aria-label="%s" autocomplete="off">' % (
            esc(strings['common.lang.search']), esc(strings['common.lang.search'])),
        '        <div class="lang-grid">',
    ] + ['            ' + x for x in opts] + [
        '        </div>',
        '    </div>',
        '</div>',
    ]
    return ('\n' + indent).join(lines)


WARNINGS = []


def make_shot_resolver(cfg, loc, errors, where):
    """{{shot:nombre.ext}}: busca la captura en la carpeta de la version actual y, si falta,
    en la de la version anterior (con aviso). Config: screenshots.<version>.{dir,suffix}."""
    cur = cfg['current_release']
    order = cfg['release_order']
    chain = [v for v in reversed(order[:order.index(cur) + 1]) if v in cfg.get('screenshots', {})]

    def resolve(name):
        base, ext = os.path.splitext(name)
        first = None
        for ver in chain:
            sc = cfg['screenshots'][ver]
            rel_path = sc['dir'].format(code=loc['code'], img=loc['img']) + base + sc['suffix'].format(
                code=loc['code'], img=loc['img']) + ext
            if os.path.exists(os.path.join(ROOT, *rel_path.split('/'))):
                if first is not None:
                    WARNINGS.append('captura %s: no existe en %s/%s (%s); se usa la de %s' % (
                        name, chain[0], loc['code'], first, ver))
                return rel_path
            if first is None:
                first = rel_path
        errors.append('%s: no existe la captura %s en ninguna version (%s)' % (where, name, first))
        return first or name
    return resolve


def vkey(version):
    return version.replace('.', '_')


def release_vars(cfg, strings, where, errors):
    """Contenido que depende de la version: notas, historial y roadmap (segun current_release)."""
    cur = cfg['current_release']
    order = cfg['release_order']
    if cur not in order:
        raise BuildError('current_release %s no esta en release_order' % cur)
    live = bool(cfg.get('ios_live'))
    v = {'release_version': cur}
    notes = strings.get('release.%s.new' % vkey(cur))
    if not notes:
        errors.append('%s: faltan las notas release.%s.new' % (where, vkey(cur)))
        return v
    fixes = strings.get('release.%s.fixes' % vkey(cur), [])
    li = '                    <li>%s</li>'
    v['notes_new_items'] = '\n'.join(li % x for x in notes)
    v['notes_fix_items'] = '\n'.join(li % x for x in fixes)
    v['has_notes_fixes'] = '1' if fixes else ''
    # historial: versiones <= actual con notas, de la mas nueva a la mas antigua
    items = []
    for ver in reversed(order[:order.index(cur) + 1]):
        new = strings.get('release.%s.new' % vkey(ver))
        if not new:
            continue
        fx = strings.get('release.%s.fixes' % vkey(ver), [])
        li6 = '                        <li>%s</li>'
        block = ['            <div class="faq-item">',
                 '                <button class="faq-q">v%s &middot; %s</button>' % (ver, strings['release.%s.headline' % vkey(ver)]),
                 '                <div class="faq-a"><div class="faq-a-inner">',
                 '                    ' + strings['home.history.new'], '                    <ul>']
        block += [li6 % x for x in new] + ['                    </ul>']
        if fx:
            block += ['                    ' + strings['home.history.fixes'], '                    <ul>']
            block += [li6 % x for x in fx] + ['                    </ul>']
        block += ['                </div></div>', '            </div>']
        items.append('\n'.join(block))
    v['history_items'] = '\n'.join(items)
    # roadmap: la version siguiente, solo si hay contenido para ella
    nxt = order[order.index(cur) + 1] if order.index(cur) + 1 < len(order) else None
    cards = strings.get('roadmap.%s.cards' % vkey(nxt)) if nxt else None
    v['has_roadmap'] = '1' if cards else ''
    if cards:
        v['roadmap_heading'] = strings['roadmap.%s.heading' % vkey(nxt)]
        v['roadmap_sub'] = strings['roadmap.%s.sub' % vkey(nxt)]
        out = []
        for i, c in enumerate(cards):
            out += ['            <div class="roadmap-item%s">' % (' glow' if i == 0 else ''),
                    '                <span class="roadmap-tag planned">%s</span>' % nxt,
                    '                <h3>%s</h3>' % c['title'],
                    '                <p>%s</p>' % c['text'],
                    '            </div>']
        v['roadmap_items'] = '\n'.join(out)
    else:
        v['roadmap_heading'] = v['roadmap_sub'] = v['roadmap_items'] = ''
    return v


IF_RE = re.compile(r'^[ \t]*\{\{#(if|unless) (\w+)\}\}\n(.*?)^[ \t]*\{\{/(?:if|unless)\}\}\n', re.S | re.M)


def resolve_ifs(text, variables):
    """Bloques {{#if var}}...{{/if}} y {{#unless var}}...{{/unless}}, cada marcador en su propia linea."""
    def sub(m):
        truthy = bool(variables.get(m.group(2)))
        return m.group(3) if (truthy if m.group(1) == 'if' else not truthy) else ''
    return IF_RE.sub(sub, text)


def render(text, variables, strings, where, errors, depth=0):
    if depth > 6:
        raise BuildError('plantillas anidadas en bucle en ' + where)
    if depth == 0:
        text = resolve_ifs(text, variables)
    live = bool(variables.get('ios_live'))

    def sub(m):
        prefix, key = m.group(1), m.group(2)
        as_json = prefix == 'json:'
        if prefix in ('shot:', 'shot_abs:'):
            path = urllib.parse.quote(variables['__shot'](key))
            return (variables['root'] if prefix == 'shot:' else variables['site_url']) + path
        if key in variables:
            val = variables[key]
        elif key in strings:
            val = pick(strings, key, live)
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
    if cfg.get('ios_live') and not cfg.get('app_store_url'):
        raise BuildError('ios_live es true pero app_store_url esta vacio en i18n/locales.json')
    for loc in locales:
        strings = load_json(os.path.join(ROOT, 'i18n', loc['code'] + '.json'))
        for pname, page in cfg['pages'].items():
            tpl_path = os.path.join(ROOT, 'src', 'templates', page['template'])
            with open(tpl_path, encoding='utf-8', newline='') as f:
                tpl = f.read()
            where = '%s/%s' % (loc['code'], page['template'])
            variables = build_vars(cfg, loc, pname, page, locales)
            variables.update(release_vars(cfg, strings, where, errors))
            variables['__shot'] = make_shot_resolver(cfg, loc, errors, where)
            variables['ios_live'] = '1' if cfg.get('ios_live') else ''
            variables['ios_url'] = cfg['app_store_url'] if cfg.get('ios_live') else cfg['testflight_url']
            variables['lm_i18n_json'] = js_payload(strings, bool(cfg.get('ios_live')))
            variables['lang_picker'] = lang_picker(loc, page, locales, strings, ' ' * 12)
            where = '%s/%s' % (loc['code'], page['template'])
            out = render(tpl, variables, strings, where, errors)
            out_rel = page_dir(loc, page) + 'index.html'
            written.append((os.path.join(ROOT, *out_rel.split('/')), out))
    if errors:
        for e in sorted(set(errors)):
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
    changed = set()
    for path, out in written:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        prev = None
        if os.path.exists(path):
            with open(path, encoding='utf-8', newline='') as f:
                prev = f.read().replace(CRLF, LF)
        if prev != out:
            changed.add(path)
        with open(path, 'w', encoding='utf-8', newline=LF) as f:
            f.write(out)
        print('ok     ' if prev == out else 'updated', os.path.relpath(path, ROOT).replace(os.sep, '/'))
    update_sitemap(cfg, changed)
    for w in sorted(set(WARNINGS)):
        print('WARNING:', w, file=sys.stderr)


CRLF = '\r\n'
LF = '\n'


def update_sitemap(cfg, changed):
    """Regenera en sitemap.xml las entradas de las paginas generadas; el resto queda tal cual."""
    path = os.path.join(ROOT, 'sitemap.xml')
    with open(path, encoding='utf-8', newline='') as f:
        text = f.read().replace(CRLF, LF)
    site = cfg['site_url']
    locales = cfg['locales']
    block_re = re.compile(r'  <url>\n.*?\n  </url>\n', re.S)
    existing = {}
    for m in block_re.finditer(text):
        existing[re.search(r'<loc>(.*?)</loc>', m.group(0)).group(1)] = m.group(0)
    groups = []
    for page in cfg['pages'].values():
        urls = []
        for o in locales:
            d = page_dir(o, page)
            urls.append((site + d, os.path.join(ROOT, *(d + 'index.html').split('/'))))
        groups.append((page, urls))
    owner = {}
    for gi, (page, urls) in enumerate(groups):
        for u, _p in urls:
            owner[u] = gi
    default = [o for o in locales if o['code'] == cfg['default_locale']][0]
    today = datetime.date.today().isoformat()

    def make_group(gi):
        page, urls = groups[gi]
        base = existing.get(site + page_dir(default, page), '')
        out = ''
        for u, fpath in urls:
            old = existing.get(u, base)

            def field(name, dflt):
                mm = re.search(r'<%s>(.*?)</%s>' % (name, name), old)
                return mm.group(1) if mm else dflt
            lastmod = today if fpath in changed else field('lastmod', today)
            alts = ''.join(
                '    <xhtml:link rel="alternate" hreflang="%s" href="%s" />\n' % (x['hreflang'], site + page_dir(x, page))
                for x in locales)
            alts += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s" />\n' % (site + page_dir(default, page))
            out += ('  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n    <changefreq>%s</changefreq>\n'
                    '    <priority>%s</priority>\n  </url>\n') % (
                u, alts, lastmod, field('changefreq', 'monthly'), field('priority', '0.8'))
        return out
    emitted = set()
    res = []
    pos = 0
    for m in block_re.finditer(text):
        res.append(text[pos:m.start()])
        pos = m.end()
        u = re.search(r'<loc>(.*?)</loc>', m.group(0)).group(1)
        if u in owner:
            gi = owner[u]
            if gi not in emitted:
                emitted.add(gi)
                res.append(make_group(gi))
        else:
            res.append(m.group(0))
    tail = text[pos:]
    for gi in range(len(groups)):
        if gi not in emitted:
            res.append(make_group(gi))
    res.append(tail)
    with open(path, 'w', encoding='utf-8', newline=LF) as f:
        f.write(''.join(res))


if __name__ == '__main__':
    try:
        main()
    except BuildError as e:
        print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
