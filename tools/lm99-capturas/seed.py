#!/usr/bin/env python3
"""Genera un dataDir de muestra para Lecturameter 99 (data.json v10 + timer.json + local.json + portadas)."""
import json, os, random, shutil, sys, time
from datetime import date, timedelta

S = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "normal"   # normal | tips | notimer
random.seed(1999)
shutil.rmtree(out, ignore_errors=True)
os.makedirs(os.path.join(out, "covers"))

now_ms = int(time.time() * 1000)
today = date(2026, 9, 24)

def ms_of(d, hour=21):
    return int(time.mktime(time.strptime(f"{d.isoformat()} {hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")) * 1000)

books = [
    dict(id=1001, title="Dracula", author="Bram Stoker", pages=418, status="READING", cover="dracula",
         start=date(2026, 9, 6), end=None, rating=None),
    dict(id=1002, title="The Time Machine", author="H. G. Wells", pages=118, status="FINISHED", cover="timemachine",
         start=date(2026, 8, 24), end=date(2026, 8, 30), rating=4.0),
    dict(id=1003, title="Frankenstein", author="Mary Shelley", pages=280, status="FINISHED", cover="frankenstein",
         start=date(2026, 7, 12), end=date(2026, 8, 2), rating=4.5),
    dict(id=1004, title="Pride and Prejudice", author="Jane Austen", pages=432, status="FINISHED", cover="pride",
         start=date(2026, 5, 18), end=date(2026, 6, 28), rating=5.0),
    dict(id=1005, title="Treasure Island", author="Robert Louis Stevenson", pages=240, status="PENDING", cover="treasure",
         start=None, end=None, rating=None),
    dict(id=1006, title="Don Quixote", author="Miguel de Cervantes", pages=1023, status="PENDING", cover="quixote",
         start=None, end=None, rating=None),
    dict(id=1007, title="A Princess of Mars", author="Edgar Rice Burroughs", pages=196, status="DROPPED", cover="mars",
         start=date(2026, 7, 3), end=None, rating=2.5),
]

sessions = []
sid = 5000

def add_sessions(b, start, end, total_pages, avg_ppm):
    """Reparte total_pages en sesiones entre start y end (no todos los dias)."""
    global sid
    days = (end - start).days + 1
    page = 1
    d = start
    while d <= end and page <= total_pages:
        if random.random() < 0.72:
            remaining = total_pages - page + 1
            pages = min(remaining, random.randint(12, 48))
            minutes = max(8, int(pages / avg_ppm * random.uniform(0.85, 1.2)))
            sid += 1
            sessions.append(dict(
                id=sid, bookId=b["id"], date=d.isoformat(), pages=pages, minutes=minutes, note="",
                startPage=page, endPage=page + pages - 1, readingIndex=0, startTimestamp=ms_of(d, random.choice([8, 13, 20, 22])),
                noteKind="COMMENT",
            ))
            page += pages
        d += timedelta(days=1)
    return page - 1

add_sessions(books[3], date(2026, 5, 18), date(2026, 6, 28), 432, 0.75)
add_sessions(books[6], date(2026, 7, 3), date(2026, 7, 9), 61, 0.7)
add_sessions(books[2], date(2026, 7, 12), date(2026, 8, 2), 280, 0.8)
add_sessions(books[1], date(2026, 8, 24), date(2026, 8, 30), 118, 0.9)
add_sessions(books[0], date(2026, 9, 6), date(2026, 9, 23), 214, 0.7)
sessions[-1]["note"] = "Capítulo del asilo: Renfield y las moscas."
sessions[-1]["noteKind"] = "COMMENT"

def book_json(b):
    events = []
    if b["start"]:
        events.append(dict(type="start", date=b["start"].isoformat(), occurrence=1))
    if b["end"]:
        events.append(dict(type="end", date=b["end"].isoformat(), occurrence=1))
    return dict(
        id=b["id"], title=b["title"], author=b["author"], pages=b["pages"],
        startDate=b["start"].isoformat() if b["start"] else None,
        endDate=b["end"].isoformat() if b["end"] else None,
        status=b["status"], rating=b["rating"], coverUrl=None, isbn=None, comment="",
        addedAt=ms_of(b["start"] or date(2026, 5, 10)) - 86400000, genre="", genres=[],
        importedFromGoodreads=False, isRereading=False, noCoverFound=False, editions=[],
        firstFunctionalPage=None, lastFunctionalPage=None,
        dropDate=date(2026, 7, 10).isoformat() if b["status"] == "DROPPED" else None,
        resumedDate=None, dateEvents=events, isFavorite=b["id"] == 1004, spinePhotoPath=None, edgesPhotoPath=None,
        issuesDismissed=False, quotesJson="[]", review=None, notesJson="[]", cardSnippetRef=None,
    )

data = dict(version=10, exportedAt=now_ms, books=[book_json(b) for b in books], sessions=sessions,
            themeMode="light", challenges=[])
with open(os.path.join(out, "data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

local_covers = {}
for b in books:
    src = os.path.join(S, "covers", b["cover"] + ".jpg")
    path = f"covers/local_{b['id']}.img"
    shutil.copyfile(src, os.path.join(out, path))
    local_covers[str(b["id"])] = path

all_tips = ["tip_welcome", "tip_first_book", "tip_first_session", "tip_gestures", "tip_timer_minimize"]
local = dict(localCovers=local_covers, timerMinimized=False, splitRatio=0.42, pagiVisible=True,
             tipsSeen=[] if mode == "tips" else all_tips)
with open(os.path.join(out, "local.json"), "w", encoding="utf-8") as f:
    json.dump(local, f, ensure_ascii=False)

if mode != "notimer":
    elapsed = (42 * 60 + 17) * 1000
    timer = dict(bookId=1001, startedAt=now_ms - elapsed, runningSince=now_ms - elapsed, accumulatedMs=0)
    with open(os.path.join(out, "timer.json"), "w") as f:
        json.dump(timer, f)

print(f"seed ok: {len(books)} libros, {len(sessions)} sesiones, modo {mode} -> {out}")
