"""Trocea source.json para traducir por partes y junta las partes.

  python tools/i18n/chunk.py show <n>          -> imprime la parte n (0..N-1) como JSON {clave: {en, es, note?}}
  python tools/i18n/chunk.py count             -> numero de partes
  python tools/i18n/chunk.py merge <codigo>    -> junta work/out/_parts/<codigo>/*.json en work/out/<codigo>.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
SOURCE = os.path.join(WORK, "source.json")
WORDS_PER_PART = 1300


def parts():
    src = json.load(open(SOURCE, encoding="utf-8"))
    out, cur, words = [], {}, 0
    for key, val in src.items():
        cur[key] = val
        words += len(str(val.get("en", "")).split())
        if words >= WORDS_PER_PART:
            out.append(cur)
            cur, words = {}, 0
    if cur:
        out.append(cur)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "count":
        print(len(parts()))
    elif cmd == "show":
        print(json.dumps(parts()[int(sys.argv[2])], ensure_ascii=False, indent=1))
    elif cmd == "merge":
        code = sys.argv[2]
        pdir = os.path.join(WORK, "out", "_parts", code)
        merged = {}
        for name in sorted(os.listdir(pdir)):
            if name.endswith(".json"):
                merged.update(json.load(open(os.path.join(pdir, name), encoding="utf-8")))
        dest = os.path.join(WORK, "out", code + ".json")
        json.dump(merged, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(merged)} claves -> {dest}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
