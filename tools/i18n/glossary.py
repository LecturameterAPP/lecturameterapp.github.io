#!/usr/bin/env python3
"""Glosario por idioma sacado de los strings de la app (solo lectura de C:/Refrac/lm-tronco).

Para cada termino EN de TERMS busca en los strings.xml EN las claves cuyo texto es exactamente ese
termino y toma, en cada idioma, la traduccion mas frecuente entre esas claves. Escribe
tools/i18n/work/glossary/<code>.json: {termino EN: texto de la app}. Los terminos sin equivalente
exacto en la app se listan en work/glossary/_missing.txt (por idioma solo se omiten los que faltan).
Uso: python tools/i18n/glossary.py
"""
import collections
import glob
import html
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
APP = 'C:/Refrac/lm-tronco'
OUT = os.path.join(ROOT, 'tools', 'i18n', 'work', 'glossary')

# codigo web -> sufijos de carpeta values-<sufijo> (en = 'values' sin sufijo + values-en)
SUFFIX = {
    'en': ['', 'en', 'en-rUS'], 'he': ['he', 'iw'], 'id': ['id', 'in'], 'pt-br': ['pt-rBR'],
    'zh-cn': ['zh-rCN'], 'no': ['no', 'nb'],
}

# Terminos de la web (EN, tal como se escriben en la app). Cada entrada: un texto o varios candidatos
# (se usa el primero que exista en la app).
TERMS = [
    # estados y estanterias
    'Reading', 'Finished', 'Rereading', 'Want to read', 'Dropped', 'Pending', 'To read', 'All books',
    'Books', 'Book', 'Comic', 'Comics', 'Manga', 'Audiobook', 'Audiobooks', 'Comic / Manga',
    'Wishlist', 'Library', 'Author', 'Title', 'Genre', 'Pages', 'Series', 'Saga', 'Sagas',
    'Shelves', 'Tags', 'Notes', 'Quotes', 'Rating', 'Favorites', 'Collection',
    # cronometro y sesiones
    'Timer', 'Reading session', 'Session', 'Sessions', 'Start', 'Pause', 'Stop', 'Resume',
    'Save session', 'Immersive mode', 'Immersive', 'Ambient sound', 'Sounds', 'History',
    'Minutes', 'Hours', 'Reading time', 'Pages per day', 'Speed', 'Streak',
    # estadisticas y logros
    'Statistics', 'Stats', 'Summary', 'Heatmap', 'Calendar', 'Your week', 'Your month', 'Year', 'Month',
    'Week', 'Day', 'Daily', 'Weekly', 'Monthly', 'Yearly', 'Goals', 'Goal', 'Daily goal', 'Progress',
    'Challenges', 'Challenge', 'Reading challenges', 'Bingo', 'Reading bingo', 'Quest', 'Quests',
    'Wrapped', 'Your Wrapped', 'Achievements', 'Badges', 'Global challenge', 'Leaderboard',
    # pantallas y ajustes
    'Settings', 'Search', 'Home', 'Add', 'Add book', 'Add books', 'Edit', 'Delete', 'Save', 'Cancel',
    'Share', 'Import', 'Export', 'Import / Export', 'Backup', 'Backups', 'Restore', 'Backup and restore',
    'Back up', 'Google Drive', 'iCloud', 'Reminders', 'Reminder', 'Notifications', 'Language',
    'Theme', 'Themes', 'Appearance', 'Widgets', 'Widget', 'Icon', 'App icon', 'App icons',
    'Scan barcode', 'Barcode', 'ISBN', 'Catalog', 'Covers', 'Cover', 'Filters', 'Sort', 'Order',
    # temas
    'Light', 'Dark', 'Aurora', 'OLED', 'Leather', 'Dusk', 'Twilight', 'Sunset', 'Auto', 'System',
    'Dark theme', 'Light theme', 'Accent color', 'Color',
    # Pagi y Pro
    'Pagi', 'Pagi skins', 'Skins', 'Skin', 'Pro', 'Lecturameter Pro', 'Unlock Pro', 'Free',
    'Premium', 'Tips', 'Tip', 'Support', 'Donate', 'Roadmap', 'What\'s new', 'Patch notes',
    'About', 'Help', 'Feedback', 'Contact', 'Privacy policy', 'Terms of service',
    # integraciones
    'KOSync', 'KOReader', 'Goodreads', 'StoryGraph', 'Sync', 'Server', 'Account',
    'Sign in', 'Sign out', 'Download', 'Open', 'Close', 'Continue', 'Next', 'Previous',
    # tipos y miscelanea
    'Percent', 'Pages read', 'Books read', 'Time', 'Total', 'Average', 'Longest session', 'Best day',
    'Languages', 'Offline', 'Done', 'Yes', 'No', 'Ok', 'Random', 'Pick a book', 'Another one',
]

PLACEHOLDER = re.compile(r'%|\{\d+\}|\\n|<')


def unescape(v):
    v = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', v, flags=re.S)
    v = v.replace("\\'", "'").replace('\\"', '"').replace('\\@', '@').replace('\\?', '?')
    v = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), v)
    return html.unescape(v).strip()


def clean(v):
    """Quita emojis/simbolos iniciales y puntuacion final ('⬛ OLED', 'Notes:', 'Sagas…')."""
    v = re.sub(r'^[^\w(]+', '', v.strip())
    return re.sub(r'[\s:.…]+$', '', v)


def collect():
    """{sufijo: {clave: texto}} de todos los values*/ *.xml del repo (sin build/)."""
    res = collections.defaultdict(dict)
    for f in glob.glob(APP + '/**/values*/*.xml', recursive=True):
        n = f.replace('\\', '/')
        if '/build/' in n or 'releaseTestpro' in n or '/iosApp' in n or '/worker/' in n:
            continue
        m = re.search(r'/values(?:-([A-Za-z\-]+))?/[^/]+\.xml$', n)
        if not m:
            continue
        suf = m.group(1) or ''
        try:
            t = open(f, encoding='utf-8').read()
        except OSError:
            continue
        for s in re.finditer(r'<string name="([^"]+)"([^>]*)>(.*?)</string>', t, re.S):
            if 'translatable="false"' in s.group(2):
                continue
            res[suf][s.group(1)] = clean(unescape(s.group(3)))
    return res


def main():
    res = collect()
    locales = json.load(open(os.path.join(ROOT, 'i18n', 'locales.json'), encoding='utf-8'))['locales']
    en = {}
    for suf in SUFFIX['en']:
        en.update(res.get(suf, {}))
    inv = collections.defaultdict(list)
    for k, v in en.items():
        if v and not PLACEHOLDER.search(v):
            inv[v.lower()].append(k)
    keys_for = {t: inv.get(t.lower(), []) for t in TERMS}
    os.makedirs(OUT, exist_ok=True)
    missing = collections.defaultdict(list)
    summary = {}
    for loc in locales:
        c = loc['code']
        tr = {}
        for suf in SUFFIX.get(c, [c]):
            tr.update(res.get(suf, {}))
        gl = {}
        for t in TERMS:
            vals = [tr[k] for k in keys_for[t] if k in tr and tr[k] and not PLACEHOLDER.search(tr[k])]
            if not vals:
                missing[t].append(c)
                continue
            gl[t] = collections.Counter(vals).most_common(1)[0][0]
        summary[c] = len(gl)
        with open(os.path.join(OUT, c + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(gl, f, ensure_ascii=False, indent=1, sort_keys=False)
    with open(os.path.join(OUT, '_missing.txt'), 'w', encoding='utf-8') as f:
        for t, cs in sorted(missing.items()):
            f.write('%s\t%s\n' % (t, 'TODOS' if len(cs) == len(locales) else ','.join(cs)))
    print('terminos', len(TERMS), 'por idioma min/max', min(summary.values()), max(summary.values()))
    print('sin equivalente en ningun idioma:', [t for t, cs in missing.items() if len(cs) == len(locales)])


if __name__ == '__main__':
    main()
