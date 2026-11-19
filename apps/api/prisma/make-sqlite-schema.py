#!/usr/bin/env python3
"""Generate the local-dev SQLite schema from the canonical PostgreSQL schema
(../../prisma/schema.prisma). SQLite has no enums or scalar lists in Prisma,
so: enum -> String, String[] -> Json. Models stay otherwise identical.
Production uses the canonical PostgreSQL schema directly."""
import re
from pathlib import Path

src = Path(__file__).resolve().parents[3] / "prisma" / "schema.prisma"
text = src.read_text(encoding="utf-8")

enums = re.findall(r"enum\s+(\w+)\s*\{[^}]*\}", text)
text = re.sub(r"enum\s+\w+\s*\{[^}]*\}\n?", "", text)
for e in enums:
    text = re.sub(rf"\b{e}\b(\[\])?", "String", text)
text = text.replace("String[]", "Json")
# enum defaults must become string defaults; Json list defaults are not
# allowed on scalar Json fields, so drop them (app/seed supplies values)
text = re.sub(r"@default\(([A-Z][A-Z_0-9]*)\)", r'@default("\1")', text)
text = re.sub(r"\s*@default\(\[[^\]]*\]\)", "", text)
text = text.replace('provider  = "postgresql"', 'provider = "sqlite"')
text = re.sub(r"\n\s*directUrl.*", "", text)
header = "// AUTO-GENERATED local-dev SQLite schema — see make-sqlite-schema.py\n// Canonical production schema: ../../prisma/schema.prisma (PostgreSQL)\n"
out = Path(__file__).resolve().parent / "schema.prisma"
out.write_text(header + text, encoding="utf-8")
print(f"wrote {out} (enums->String: {enums})")
