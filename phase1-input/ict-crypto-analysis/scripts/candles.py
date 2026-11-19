"""محمّل الشموع المشترك بين سكربتات ICT.

يقبل:
- JSON محفوظ من أداة get_candlestick في Crypto.com: قائمة أو {"data": [...]}،
  ويُقبل نص قبل البيانات. الترتيب يُعالج تلقائيًا (الأحدث أولًا غالبًا).
- CSV بأعمدة time,open,high,low,close (وvolume اختياري). إن كان الأحدث في الأعلى يُعكس تلقائيًا.

يعيد قائمة شموع مرتبة من الأقدم إلى الأحدث، وكل شمعة: t و o و h و l و c و v.
"""
import csv
import json
from datetime import datetime, timezone


def _rows_from(obj):
    rows = obj.get("data") if isinstance(obj, dict) else obj
    if isinstance(rows, list) and rows and isinstance(rows[0], dict) and "open" in rows[0]:
        return rows
    return None


def _read_json_rows(path):
    raw = open(path, encoding="utf-8").read()
    try:
        rows = _rows_from(json.loads(raw))
        if rows:
            return rows
    except ValueError:
        pass
    dec = json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch not in "{[":
            continue
        try:
            obj, _ = dec.raw_decode(raw, i)
        except ValueError:
            continue
        rows = _rows_from(obj)
        if rows:
            return rows
    raise SystemExit("لم أجد شموعًا (open/high/low/close) داخل ملف JSON")


def _sort_key(t):
    s = str(t).strip()
    try:
        x = float(s)
        return x / 1000.0 if x > 1e11 else x  # بالمللي ثانية
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _display_time(t):
    s = str(t).strip()
    try:
        x = float(s)
    except ValueError:
        return s
    if x > 1e11:
        x /= 1000.0
    return datetime.fromtimestamp(x, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(x):
    return float(x) if x not in (None, "") else 0.0


def load_candles(path, kind):
    """kind: 'json' أو 'csv'."""
    items = []
    if kind == "json":
        for r in _read_json_rows(path):
            items.append((r.get("timestamp", r.get("time")), r))
    else:
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                items.append((r.get("time"), r))
    if not items:
        raise SystemExit("الملف لا يحتوي شموعًا")

    keys = [_sort_key(t) if t not in (None, "") else None for t, _ in items]
    if all(k is not None for k in keys):
        order = sorted(range(len(items)), key=lambda i: keys[i])
    elif kind == "json":
        order = list(reversed(range(len(items))))  # مخرجات الموصّل من الأحدث للأقدم
    else:
        order = list(range(len(items)))  # CSV بلا وقت: يُفترض من الأقدم للأحدث

    candles = []
    for i in order:
        t, r = items[i]
        candles.append(dict(
            t=_display_time(t) if t not in (None, "") else str(len(candles)),
            o=float(r["open"]), h=float(r["high"]), l=float(r["low"]), c=float(r["close"]),
            v=_num(r.get("volume")),
        ))
    return candles
