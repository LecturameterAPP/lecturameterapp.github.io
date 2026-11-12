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
MARK = re.compile(r'\{\{(json:|shot:|shot_abs:|shot99:|shot99_abs:|@t:|@href:|@aria:)?([A-Za-z0-9_.@/\-]+)\}\}')
PARTIAL_RE = re.compile(r'^[ \t]*\{\{> ([a-z_]+)\}\}\r?\n', re.M)


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


def page_locales(page, locales):
    """Idiomas en los que existe una pagina (pages.<x>.only_locales o las claves de pages.<x>.paths; sin ninguno, todos)."""
    codes = page.get('only_locales') or (list(page['paths']) if page.get('paths') else None)
    return [l for l in locales if not codes or l['code'] in codes]


def page_dir(loc, page):
    """Carpeta (desde la raiz del sitio) de la pagina en ese idioma. `paths` fija la ruta completa por idioma
    (paginas escritas a mano en en/es); si no, ruta del idioma + page.dir."""
    if page.get('paths'):
        return page['paths'][loc['code']]
    return loc['path'].strip('/') and (loc['path'].strip('/') + '/' + page['dir']) or page['dir']


def page_template(page, loc):
    t = page['template']
    return t[loc['code']] if isinstance(t, dict) else t


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
        'hreflang': loc['hreflang'],
        'site_url': site,
        'root': rel(here, ''),
        'home': rel(here, loc['path'].lstrip('/')),
        'link_blog': rel(here, loc['blog']),
        'link_1999': rel(here, loc['path'].lstrip('/') + 'lecturameter-1999/'),
        'page_url': site + pdir + ('/' if pdir else ''),
        'head_redirect': '',
        'drakehold_url': 'https://drakehold.pages.dev/?utm_source=lecturameter' + ('&amp;lang=es' if loc['code'] == 'es' else ''),
    }
    for k, p in loc['features'].items():
        v['link_feat_' + k] = rel(here, p)
    # enlaces legales: es/en -> originales (/privacidad.html...); resto -> traducciones /<code>/privacy/...
    for lk, lp in cfg.get('legal_pages', {}).items():
        if loc.get('legal_original'):
            v['link_' + lk] = rel(here, lp['original'])
        else:
            v['link_' + lk] = rel(here, loc['path'].lstrip('/') + lp['dir'])
    # politica de cookies: pagina propia solo en los idiomas de pages.cookies.only_locales; el resto apunta a la inglesa
    ck = cfg['pages'].get('cookies')
    if ck:
        ck_codes = ck.get('only_locales')
        ck_loc = loc if (not ck_codes or loc['code'] in ck_codes) else [o for o in others if o['code'] == cfg['default_locale']][0]
        v['link_cookies'] = rel(here, page_dir(ck_loc, ck))
    v['play_url'] = cfg['play_url']
    v['play_1999_url'] = cfg['play_1999_url']
    # Google Play del 1999: con play_1999_live=false (ficha aun no publica) no se enlaza a Play ni se anuncia como disponible
    live99 = bool(cfg.get('play_1999_live'))
    ios99 = cfg.get('app_store_1999_url', '')
    v['play_1999_live'] = '1' if live99 else ''
    v['install_1999_url'] = cfg['play_1999_url'] if (live99 or not ios99) else ios99
    v['sameas_1999_json'] = ', '.join('"%s"' % u for u in ((cfg['play_1999_url'] if live99 else ''), ios99) if u)
    if page.get('original'):
        v['legal_original_url'] = rel(here, page['original']) + '?lang=en'
    elif pname == 'cookies':
        # aviso de traduccion orientativa: solo en los idiomas que no son es/en; enlaza a la version inglesa
        v['legal_original'] = '1' if loc.get('legal_original') else ''
        dflt = [o for o in others if o['code'] == cfg['default_locale']]
        if dflt:
            v['legal_original_url'] = rel(here, page_dir(dflt[0], page))
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
    dflt = [o for o in others if o['code'] == cfg['default_locale']]
    xd = site + (page_dir(dflt[0], page) if dflt else page['dir'])
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


def lang_picker(loc, page, locales, strings, indent, targets=None):
    """Selector de idioma: cada opcion es un <a href> real a la misma pagina en ese idioma.
    `targets` (opcional, usado por build_blog.py): {codigo: ruta} -> solo esos idiomas, con esa ruta."""
    here = (targets[loc['code']] if targets is not None else page_dir(loc, page)).rstrip('/')
    esc = html.escape
    opts = []
    for o in locales:
        if targets is not None and o['code'] not in targets:
            continue
        target = targets[o['code']] if targets is not None else page_dir(o, page)
        cur = o is loc
        href = rel(here, target)
        if targets is None and page.get('original') and o.get('legal_original'):
            href = rel(here, page['original']) + '?lang=' + o['code']
        opts.append(
            '<a href="%s" lang="%s" hreflang="%s" data-code="%s" data-search="%s"%s>%s</a>' % (
                href, esc(o['code']), esc(o['hreflang']), esc(o['code']),
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


def resolve_shot99(loc, name):
    """{{shot99:[subdir/]fichero}}: captura del 1999. Si el idioma tiene su version en WebP
    (capturas-1999/[subdir/]<code>/<fichero>.webp) se usa (tambien es y en); si no, la de siempre (shots99 / img)."""
    sub, _, fname = name.rpartition('/')
    base = os.path.splitext(fname)[0]
    own = 'capturas-1999/' + (sub + '/' if sub else '') + loc['code'] + '/' + base + '.webp'
    if os.path.exists(os.path.join(ROOT, *own.split('/'))):
        return own
    if sub:
        return 'capturas-1999/%s/%s/%s' % (sub, loc['img'], fname)
    return 'capturas-1999/' + loc['shots99'] + fname


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
            # captura propia del idioma (solo idiomas que la tengan): screenshots.<v>.localized
            loz = sc.get('localized')
            if loz and name in loz['files']:
                lp = loz['dir'].format(code=loc['code'], img=loc['img']) + loz['files'][name]
                if os.path.exists(os.path.join(ROOT, *lp.split('/'))):
                    return lp
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


def release_label(cfg, ver, loc):
    """Nombre publico de una version en texto agnostico de plataforma (p. ej. «3.9 / iOS 1.1.0»),
    segun release_labels en locales.json. En idiomas RTL va aislado como LTR para que la barra no se invierta."""
    label = cfg.get('release_labels', {}).get(ver, ver)
    if label != ver and loc is not None and loc.get('dir') == 'rtl':
        label = '<span dir="ltr">%s</span>' % label
    return label


def release_vars(cfg, strings, where, errors, loc=None):
    """Contenido que depende de la version: notas, historial y roadmap (segun current_release)."""
    cur = cfg['current_release']
    order = cfg['release_order']
    if cur not in order:
        raise BuildError('current_release %s no esta en release_order' % cur)
    live = bool(cfg.get('ios_live'))
    v = {'release_version': cur, 'release_label': release_label(cfg, cur, loc)}
    notes = strings.get('release.%s.new' % vkey(cur))
    if not notes:
        errors.append('%s: faltan las notas release.%s.new' % (where, vkey(cur)))
        return v
    fixes = strings.get('release.%s.fixes' % vkey(cur), [])
    li = '                    <li>%s</li>'
    v['notes_new_items'] = '\n'.join(li % x for x in notes)
    v['notes_new_short'] = '\n'.join(li % x for x in notes[:4])
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
                 '                <button class="faq-q">v%s &middot; %s</button>' % (release_label(cfg, ver, loc), strings['release.%s.headline' % vkey(ver)]),
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
                    '                <span class="roadmap-tag planned">%s</span>' % release_label(cfg, nxt, loc),
                    '                <h3>%s</h3>' % c['title'],
                    '                <p>%s</p>' % c['text'],
                    '            </div>']
        v['roadmap_items'] = '\n'.join(out)
    else:
        v['roadmap_heading'] = v['roadmap_sub'] = v['roadmap_items'] = ''
    # pagina /roadmap/: lo ya publicado (versiones <= actual con roadmap.<v>.cards), la mas nueva arriba
    blocks = []
    for ver in reversed(order[:order.index(cur) + 1]):
        pcards = strings.get('roadmap.%s.cards' % vkey(ver))
        if not pcards or 'roadmap.page.published' not in strings:
            continue
        label = release_label(cfg, ver, loc)
        out = ['        <div class="roadmap-block">',
               '            <div class="section-head"><h2>%s</h2></div>' % strings['roadmap.page.published'].replace('{{pub_label}}', label),
               '            <div class="roadmap-list">']
        for c in pcards:
            out += ['                <div class="roadmap-item">',
                    '                    <span class="roadmap-tag released">%s</span>' % label,
                    '                    <h3>%s</h3>' % c['title'],
                    '                    <p>%s</p>' % c['text'],
                    '                </div>']
        out += ['            </div>', '        </div>']
        blocks.append(NL.join(out))
    v['roadmap_published_html'] = NL.join(blocks)
    return v


NL = '\n'
NEW_PAGES = ('news', 'roadmap', 'faq', 'platforms', 'pro', 'universe')
CUR_KEYS = ('home', 'universe', 'pro', 'lm99', 'blog', 'news', 'roadmap', 'faq', 'platforms', 'privacy', 'terms', 'cookies', 'contact')
CURRENT_OF = {'universe': 'universe', 'news': 'news', 'roadmap': 'roadmap', 'faq': 'faq', 'platforms': 'platforms', 'pro': 'pro',
              'cookies': 'cookies', 'lm1999': 'lm99', 'legal_privacy': 'privacy', 'legal_terms': 'terms',
              'legal_privacy99': 'privacy', 'blog': 'blog'}


def nav_vars(cfg, loc, strings, here, is_home, current=''):
    """Enlaces de la cabecera y el pie comunes (src/partials/nav.html y footer.html) para ese idioma y esa pagina.
    En la portada los anclas son locales (#features) para que siga el scroll-spy; en el resto apuntan a la portada."""
    prefix = loc['path'].lstrip('/')
    home = rel(here, prefix)
    base = '' if is_home else home
    v = {
        'link_home': home,
        'home_abs': cfg['site_url'] + prefix,
        'link_features_all': base + '#' + strings['anchor.features'],
        'link_themes': base + '#' + strings['anchor.themes'],
        'link_events': base + '#' + strings['anchor.events'],
        'link_contact': rel(here, 'contact.html'),
        'link_regional': rel(here, 'precios-regionales.html'),
        'link_activate': rel(here, 'activar-pro.html'),
    }
    # Paginas nuevas (fase 2): mientras no existan en cfg['pages'], enlazan al ancla equivalente de la portada
    # (o se ocultan con show_<pagina>, via {{#if}} en los parciales).
    fallback = {'pro': strings['anchor.pricing'], 'news': strings['anchor.whatsnew'], 'faq': 'faq',
                'platforms': strings['anchor.ios_differences'], 'roadmap': 'roadmap', 'universe': 'universe'}
    for sl in NEW_PAGES:
        if sl in cfg['pages']:
            v['link_page_' + sl] = rel(here, prefix + sl + '/')
            v['show_' + sl] = '1'
        else:
            v['link_page_' + sl] = base + '#' + fallback[sl]
            v['show_' + sl] = '1' if sl != 'roadmap' else ''
    for c in CUR_KEYS:
        v['cur_' + c] = ' aria-current="page"' if c == current else ''
    return v


def bilingual_lang_controls(locales, seg, indent):
    """Controles de idioma de las paginas bilingues escritas a mano (boton ES/EN y, si hay version traducida
    en /<code>/<seg>/, selector con los 49 idiomas). Es lo que llevaban antes."""
    lines = ['<button type="button" class="nav-lang-btn" data-en="ES" data-es="EN" '
             'onclick="setLang(document.documentElement.lang === \'es\' ? \'en\' : \'es\')">ES</button>']
    if seg:
        opts = []
        for o in locales:
            lang_attr = '' if o['code'] in ('en', 'es') else ' lang="%s"' % html.escape(o['code'])
            opts.append('<option value="%s"%s>%s</option>' % (html.escape(o['code']), lang_attr, html.escape(o['nativeName'])))
        lines.append('<select class="nav-lang-select" id="legalLangSelect" aria-label="Language" title="Language" '
                     'data-seg="%s">%s</select>' % (seg, ''.join(opts)))
    return (NL + indent).join(lines)


def list_vars(strings, where, errors):
    """Listas de i18n (secciones Pausado, Cards, Eventos) -> HTML ya montado."""
    def get(key):
        if key not in strings:
            errors.append('%s: falta la clave %s' % (where, key))
            return []
        return strings[key]
    v = {}
    v['paused_cards_html'] = '\n'.join(
        '            <div class="paused-card reveal-up"><h3>%s</h3><p>%s</p></div>' % (c['title'], c['text'])
        for c in get('home.paused.cards'))
    v['quickmenu_cards_html'] = '\n'.join(
        '            <div class="paused-card qm-card reveal-up"><h3>%s</h3><p>%s</p></div>' % (c['title'], c['text'])
        for c in get('home.quickmenu.cards'))
    v['quickmenu_groups_html'] = '\n'.join(
        '                    <div class="qm-group%s"><p class="qm-group-title">%s</p><p>%s</p></div>'
        % (' is-current' if i == 0 else '', c['title'], c['text'])
        for i, c in enumerate(get('home.quickmenu.groups')))
    v['cards_chips_html'] = '\n'.join('                <li>%s</li>' % c for c in get('home.cards.chips'))
    v['cards_steps_html'] = '\n'.join(
        '            <li class="share-step reveal-up"><h3>%s</h3><p>%s</p></li>' % (c['title'], c['text'])
        for c in get('home.cards.steps'))
    v['events_read_items_html'] = '\n'.join('                <li>%s</li>' % c for c in get('home.events.read.items'))
    v['events_quest_items_html'] = '\n'.join('                <li>%s</li>' % c for c in get('home.events.quest.items'))
    return v


IF_RE = re.compile(r'^[ \t]*\{\{#(if|unless) (\w+)\}\}\r?\n(.*?)^[ \t]*\{\{/(?:if|unless)\}\}\r?\n', re.S | re.M)


def resolve_ifs(text, variables):
    """Bloques {{#if var}}...{{/if}} y {{#unless var}}...{{/unless}}, cada marcador en su propia linea."""
    def sub(m):
        truthy = bool(variables.get(m.group(2)))
        return m.group(3) if (truthy if m.group(1) == 'if' else not truthy) else ''
    return IF_RE.sub(sub, text)


PARTIALS = {}


def expand_partials(text, where=''):
    """{{> nombre}} (en su propia linea) -> contenido de src/partials/<nombre>.html."""
    def sub(m):
        name = m.group(1)
        if name not in PARTIALS:
            path = os.path.join(ROOT, 'src', 'partials', name + '.html')
            if not os.path.exists(path):
                raise BuildError('%s: parcial inexistente {{> %s}}' % (where, name))
            with open(path, encoding='utf-8', newline='') as f:
                PARTIALS[name] = f.read().replace(CRLF, LF)
        return PARTIALS[name]
    return PARTIAL_RE.sub(sub, text)


def lookup(key, variables, strings, where, errors, live, depth):
    if key in variables:
        val = variables[key]
    elif key in strings:
        val = pick(strings, key, live)
    else:
        errors.append('%s: clave inexistente {{%s}}' % (where, key))
        return None
    if '{{' in val:
        val = render(val, variables, strings, where, errors, depth + 1)
    return val


def bilingual_marker(prefix, key, variables, strings, where, errors, live, depth):
    """{{@t:clave}} / {{@href:variable}} / {{@aria:clave}}: texto, enlace o aria-label. En paginas bilingues
    (variables['__bi'] con las variables y textos del segundo idioma) llevan tambien los atributos data-en/es que lee setLang."""
    bi = variables.get('__bi')
    a = lookup(key, variables, strings, where, errors, live, depth)
    if a is None:
        return ''
    b = lookup(key, bi['variables'], bi['strings'], where, errors, live, depth) if bi else a
    if b is None:
        b = a
    if prefix == '@t:':
        if a == b:
            return a
        return '<span data-en="%s" data-es="%s">%s</span>' % (a, b, a)
    if prefix == '@href:':
        out = 'href="%s"' % a
        if a != b:
            out += ' data-href-en="%s" data-href-es="%s"' % (a, b)
        return out
    out = 'aria-label="%s"' % a
    if a != b:
        out += ' data-aria-en="%s" data-aria-es="%s"' % (a, b)
    return out


def render(text, variables, strings, where, errors, depth=0):
    if depth > 6:
        raise BuildError('plantillas anidadas en bucle en ' + where)
    if depth == 0:
        text = expand_partials(text, where)
        text = resolve_ifs(text, variables)
    live = bool(variables.get('ios_live'))

    def sub(m):
        prefix, key = m.group(1), m.group(2)
        if prefix in ('@t:', '@href:', '@aria:'):
            return bilingual_marker(prefix, key, variables, strings, where, errors, live, depth)
        as_json = prefix == 'json:'
        if prefix in ('shot99:', 'shot99_abs:'):
            path = urllib.parse.quote(resolve_shot99(variables['__loc'], key))
            return (variables['root'] if prefix == 'shot99:' else variables['site_url']) + path
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


def fix_legal_links(out, root):
    """Los textos legales traducidos traen hrefs relativos a la raiz del sitio (copiados del original);
    en /<code>/<pagina>/ hay que anteponer la ruta a la raiz. Solo toca el cuerpo .legal-content."""
    i = out.find('class="legal-content"')
    j = out.find('<footer', i)
    if i < 0 or j < 0:
        return out
    def sub(m):
        u = m.group(2)
        if re.match(r'(?i)^([a-z][a-z0-9+.-]*:|#|/|\.\./|//)', u):
            return m.group(0)
        if u.startswith('./'):
            u = u[2:]
        return m.group(1) + root + u + m.group(3)
    return out[:i] + re.sub(r'(<a\s[^>]*?href=")([^"]*)(")', sub, out[i:j]) + out[j:]


def parse_only(argv):
    """--only es,en  (o --only=es,en): genera solo esos idiomas; no toca ni borra el resto."""
    for i, a in enumerate(argv):
        if a == '--only' and i + 1 < len(argv):
            return [c.strip() for c in argv[i + 1].split(',') if c.strip()]
        if a.startswith('--only='):
            return [c.strip() for c in a[7:].split(',') if c.strip()]
    return None


def check_seo(strings, where, errors):
    """seo.store_name (frase exacta de la ficha de tienda de ese idioma) debe aparecer en title y description."""
    name = strings.get('seo.store_name')
    if not name:
        errors.append('%s: falta seo.store_name (frase de la ficha de tienda, ver i18n/seo_store_map.json)' % where)
        return
    for k in ('head.index.title', 'head.index.description'):
        if name not in strings.get(k, ''):
            errors.append('%s: %s no contiene la frase de tienda "%s"' % (where, k, name))


def main():
    cfg = load_json(os.path.join(ROOT, 'i18n', 'locales.json'))
    # un idioma solo existe si tiene i18n/<code>.json (los demas estan dados de alta pero pendientes)
    cfg['locales'] = [l for l in cfg['locales'] if os.path.exists(os.path.join(ROOT, 'i18n', l['code'] + '.json'))]
    # blog: enlazar a /<code>/blog/ solo si existe i18n/blog/<code>.json (el resto sigue al blog ingles)
    for l in cfg['locales']:
        if l['code'] not in ('en', 'es') and os.path.exists(os.path.join(ROOT, 'i18n', 'blog', l['code'] + '.json')):
            l['blog'] = l['path'].lstrip('/') + 'blog/'
    locales = cfg['locales']
    only = parse_only(sys.argv[1:])
    if only is not None:
        unknown = [c for c in only if c not in [l['code'] for l in locales]]
        if unknown:
            raise BuildError('--only: idiomas desconocidos o sin i18n/<codigo>.json: ' + ', '.join(unknown))
    errors = []
    written = []
    if cfg.get('ios_live') and not cfg.get('app_store_url'):
        raise BuildError('ios_live es true pero app_store_url esta vacio en i18n/locales.json')
    strings_by = {l['code']: load_json(os.path.join(ROOT, 'i18n', l['code'] + '.json')) for l in locales}

    def make_variables(loc, pname, page, plocs):
        strings = strings_by[loc['code']]
        where = '%s/%s' % (loc['code'], page_template(page, loc))
        variables = build_vars(cfg, loc, pname, page, plocs)
        variables.update(release_vars(cfg, strings, where, errors, loc))
        if page_template(page, loc) == 'index.html':
            variables.update(list_vars(strings, where, errors))
        variables['__loc'] = loc
        variables['__shot'] = make_shot_resolver(cfg, loc, errors, where)
        variables['ios_live'] = '1' if cfg.get('ios_live') else ''
        variables['ios_url'] = cfg['app_store_url'] if cfg.get('ios_live') else cfg['testflight_url']
        variables['testflight_1999_url'] = cfg['testflight_1999_url']
        variables['app_store_1999_url'] = cfg.get('app_store_1999_url', '')
        variables['lm_i18n_json'] = js_payload(strings, bool(cfg.get('ios_live')))
        pdir = page_dir(loc, page).rstrip('/')
        current = page.get('current') or CURRENT_OF.get(pname, '')
        variables.update(nav_vars(cfg, loc, strings, pdir, pname == 'index', current))
        if not variables['show_roadmap'] and variables.get('has_roadmap'):
            variables['show_roadmap'] = '1'
        if page.get('bilingual'):
            variables['lang_picker'] = bilingual_lang_controls(locales, page.get('lang_seg'), ' ' * 12)
        else:
            variables['lang_picker'] = lang_picker(loc, page, plocs, strings, ' ' * 12)
        # paginas nuevas de Recursos/Pro: title, description y nombre (migas) desde i18n
        key = page.get('i18n_key')
        if key:
            for var, k in (('page_title', 'head.%s.title' % key), ('page_description', 'head.%s.description' % key),
                           ('page_name', page['name_key'])):
                if k not in strings:
                    errors.append('%s: falta la clave %s' % (where, k))
                else:
                    variables[var] = strings[k]
        return variables

    for loc in locales:
        if only is not None and loc['code'] not in only:
            continue
        strings = strings_by[loc['code']]
        check_seo(strings, loc['code'], errors)
        todo = list(cfg['pages'].items())
        if not loc.get('legal_original'):
            todo += [('legal_' + k, dict(v, legal=True)) for k, v in cfg.get('legal_pages', {}).items()]
        for pname, page in todo:
            plocs = page_locales(page, locales)
            if loc not in plocs:
                continue
            tname = page_template(page, loc)
            tpl_path = os.path.join(ROOT, 'src', 'templates', *tname.split('/'))
            with open(tpl_path, encoding='utf-8', newline='') as f:
                tpl = f.read().replace(CRLF, LF)
            where = '%s/%s' % (loc['code'], tname)
            variables = make_variables(loc, pname, page, plocs)
            if page.get('bilingual'):
                other = [o for o in locales if o['code'] == ('es' if loc['code'] == 'en' else 'en')][0]
                variables['__bi'] = {'variables': make_variables(other, pname, dict(page, paths={other['code']: ''}), [other]),
                                     'strings': strings_by[other['code']]}
            out = render(tpl, variables, strings, where, errors)
            if page.get('legal'):
                out = fix_legal_links(out, variables['root'])
            out_rel = page.get('file') or (page_dir(loc, page) + 'index.html')
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
    hand = inject_chrome(cfg, locales, strings_by, errors)
    if errors:
        for e in sorted(set(errors)):
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)
    print('chrome %d paginas a mano' % len(hand))
    update_sitemap(cfg, changed)
    for w in sorted(set(WARNINGS)):
        print('WARNING:', w, file=sys.stderr)


CRLF = '\r\n'
LF = '\n'


NAV_RE = re.compile(r'<nav class="nav-bar">.*?</nav>\n', re.S)
FOOT_RE = re.compile(r'<footer class="site-footer">.*?</footer>\n', re.S)
OLD_FOOT_RE = re.compile(r'\n[ \t]*<div class="footer">[^\n]*</div>(?=\n)')
CTRL_RE = re.compile(r'nav-theme-btn[^>]*>[^<]*</button>\s*(.*?)\s*<a (?:data-track="[^"]*" )?href="https://play\.google', re.S)


def hand_variables(cfg, loc, strings, here):
    """Variables de cabecera y pie para una pagina escrita a mano que vive en la carpeta `here` (sin / final)."""
    prefix = loc['path'].lstrip('/')
    v = {
        'root': rel(here, ''),
        'home': rel(here, prefix),
        'site_url': cfg['site_url'],
        'link_blog': rel(here, loc['blog']),
        'link_1999': rel(here, prefix + 'lecturameter-1999/'),
        'link_cookies': rel(here, prefix + 'cookies/'),
        'ios_url': cfg['app_store_url'] if cfg.get('ios_live') else cfg['testflight_url'],
        'ios_live': '1' if cfg.get('ios_live') else '',
        'drakehold_url': 'https://drakehold.pages.dev/?utm_source=lecturameter' + ('&amp;lang=es' if loc['code'] == 'es' else ''),
    }
    for k, p in loc['features'].items():
        v['link_feat_' + k] = rel(here, p)
    for lk, lp in cfg.get('legal_pages', {}).items():
        v['link_' + lk] = rel(here, lp['original']) if loc.get('legal_original') else rel(here, prefix + lp['dir'])
    return v


def inject_chrome(cfg, locales, strings_by, errors):
    """Paso reproducible para las paginas escritas a mano (locales.json -> hand_pages): sustituye su <nav> y su <footer>
    por los parciales src/partials/nav.html y footer.html (un pie nuevo si la pagina no lo tenia), conserva el selector
    de idioma propio de cada pagina, quita el mini-pie antiguo y aplica noindex si se pide. Es idempotente."""
    import glob as _glob
    by = {l['code']: l for l in locales}
    done = []
    for ent in cfg.get('hand_pages', []):
        files = [ent['file']] if 'file' in ent else sorted(
            os.path.relpath(f, ROOT).replace(os.sep, '/') for f in _glob.glob(os.path.join(ROOT, *ent['glob'].split('/'))))
        for f in files:
            path = os.path.join(ROOT, *f.split('/'))
            with open(path, encoding='utf-8', newline='') as fh:
                text = fh.read().replace(CRLF, LF)
            here = posixpath.dirname(f)
            bil = ent.get('bilingual')
            loc = by['en'] if bil else by[ent['loc']]
            strings = strings_by[loc['code']]
            where = 'hand:' + f
            m = CTRL_RE.search(text)
            if not m:
                errors.append('%s: no se encuentran los controles de idioma de la cabecera' % where)
                continue
            variables = hand_variables(cfg, loc, strings, here)
            variables.update(nav_vars(cfg, loc, strings, here, False, ent.get('current', '')))
            variables.update(release_vars(cfg, strings, where, errors, loc))
            if not variables.get('show_roadmap') and variables.get('has_roadmap'):
                variables['show_roadmap'] = '1'
            variables['lang_picker'] = m.group(1)
            if bil:
                es = by['es']
                ev = hand_variables(cfg, es, strings_by['es'], here)
                ev.update(nav_vars(cfg, es, strings_by['es'], here, False, ent.get('current', '')))
                variables['__bi'] = {'variables': ev, 'strings': strings_by['es']}
            nav = render('{{> nav}}\n', variables, strings, where, errors)
            foot = render('{{> footer}}\n', variables, strings, where, errors)
            out = NAV_RE.sub(lambda _m: nav, text, count=1)
            if FOOT_RE.search(out):
                out = FOOT_RE.sub(lambda _m: foot, out, count=1)
            else:
                i = out.index(nav) + len(nav)
                j = out.find('<script', i)
                j = j if j >= 0 else out.index('</body>', i)
                out = out[:j] + foot + out[j:]
            out = OLD_FOOT_RE.sub('', out)
            out = re.sub(r'(styles\.css|main\.js|hit\.js)\?v=[0-9.]+', r'\1?v=8.0', out)
            if ent.get('noindex'):
                out = out.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">')
            if bil:
                # Una sola URL sirve es y en (cambio por JS): hreflang en/es/x-default apuntan a ella, sin ?lang= ni copias
                # traducidas (/<codigo>/privacy/ etc. son noindex y no pueden ser alternates). noindex -> sin hreflang.
                out = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n', '', out)
                if not ent.get('noindex'):
                    u = cfg['site_url'] + f
                    alts = ''.join('    <link rel="alternate" hreflang="%s" href="%s">\n' % (h, u) for h in ('en', 'es', 'x-default'))
                    out = re.sub(r'(    <link rel="canonical" href="[^"]*">\n)', lambda _m: _m.group(1) + alts, out, count=1)
            if out != text:
                with open(path, 'w', encoding='utf-8', newline=LF) as fh:
                    fh.write(out)
            done.append(f)
    return done


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
        for o in page_locales(page, locales):
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
                for x in page_locales(page, locales))
            alts += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s" />\n' % (site + page_dir(default, page))
            out += ('  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n    <changefreq>%s</changefreq>\n'
                    '    <priority>%s</priority>\n  </url>\n') % (
                u, alts, lastmod, field('changefreq', page.get('changefreq', 'monthly')), field('priority', page.get('priority', '0.8')))
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
