#!/usr/bin/env python3
"""Extrae las claves traducibles (i18n/en.json, que ya incluye las legales) a tools/i18n/work/source.json:
{clave: {"en":..., "es":..., "note":...}}. Excluye URLs, numeros, nombres propios y claves de config
(esas se copian tal cual del ingles en apply.py). Uso: python tools/i18n/extract.py
"""
import json
import os
import re

from common import ROOT, WORK, flatten, load, note_for, plain, translatable


def main():
    en = flatten(load(os.path.join(ROOT, 'i18n', 'en.json')))
    es = flatten(load(os.path.join(ROOT, 'i18n', 'es.json')))
    src = {}
    for k, v in en.items():
        if translatable(k, v):
            e = {'en': v, 'es': es.get(k, '')}
            n = note_for(k, v)
            if n:
                e['note'] = n
            src[k] = e
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'source.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(src, f, ensure_ascii=False, indent=1)
    words = sum(len(plain(e['en']).split()) for e in src.values())
    print('%d claves traducibles (%d excluidas), %d palabras EN' % (len(src), len(en) - len(src), words))


if __name__ == '__main__':
    main()
