#!/usr/bin/env python3
"""Genera i18n/seo_store_map.json: idioma de la web -> ficha de la App Store -> frase exacta (campo `nombre`).

Uso:  python -X utf8 tools/i18n/seo_map.py [carpeta_fichas]
Por defecto lee C:/Refrac/lm-39-temas/Documentacion/lanzamiento/fichas_3.9/appstore.
La frase es la que debe aparecer tal cual en <title> y meta description de cada idioma
(clave `seo.store_name` de i18n/<codigo>.json; build.py lo comprueba). Los idiomas sin ficha
quedan con "ficha": null y no tienen frase obligatoria todavia (se usara la del ingles + traduccion).
"""
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT = 'C:/Refrac/lm-39-temas/Documentacion/lanzamiento/fichas_3.9/appstore'
# codigo web -> fichero de ficha cuando no se llama igual
OVERRIDE = {'en': 'en-US', 'es': 'es-ES', 'pt': 'pt-PT', 'pt-br': 'pt-BR', 'zh-cn': 'zh-Hans'}


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    fichas = {os.path.basename(f)[:-5]: json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(folder, '*.json'))}
    cfg = json.load(open(os.path.join(ROOT, 'i18n', 'locales.json'), encoding='utf-8'))
    out = {}
    for loc in cfg['locales']:
        code = loc['code']
        cands = [OVERRIDE.get(code, code)] + sorted(k for k in fichas if k.split('-')[0] == code.split('-')[0])
        name = next((c for c in cands if c in fichas), None)
        out[code] = {
            'ficha': name,
            'nombre': fichas[name]['nombre'] if name else None,
            'subtitulo': fichas[name]['subtitulo'] if name else None,
            'estado_ficha': fichas[name].get('estado_idioma_asc') if name else None,
        }
    with open(os.path.join(ROOT, 'i18n', 'seo_store_map.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('con ficha: %d  sin ficha: %s' % (sum(1 for v in out.values() if v['ficha']), ', '.join(k for k, v in out.items() if not v['ficha'])))


if __name__ == '__main__':
    main()
