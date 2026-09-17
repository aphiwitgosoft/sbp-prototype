#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ดึง **แถวจริง** ของโซน A จากฐาน Oracle FCS_FRN ออกมาเป็น CSV

    ORA_USER=... ORA_PASSWORD=... ORA_HOST=... ORA_SID=... \\
        python3 tools/dump_legacy_oracle_rows.py [--confirm] [--table NAME]

ต่างจาก `tools/introspect_legacy_oracle.py` อย่างไร
──────────────────────────────────────────────────
ตัวนั้นสกัด **โครงสร้าง + สถิติ + โดเมน** (ไม่มีแถวสักแถว) — เป็นตัวบล็อก migration มาตลอด
ตัวนี้ดึง **แถวจริง** ของ 10 ตารางที่ migration ต้องใช้ ทั้งฝั่ง live และ `*_BK_20250515`
ออกมาเป็น CSV ที่ `output/sql/k2_migration_1b_stage_oracle.sql` โหลดเข้าได้ทันที

🔒 **SELECT ล้วน** — ไม่มี INSERT/UPDATE/DELETE/DDL สักคำสั่ง · มี guard ตรวจก่อนยิงทุกคิวรี
⚠️ credential อ่านจาก env เท่านั้น **ห้ามใส่ลงไฟล์**
⚠️ ผลลัพธ์เป็นข้อมูลธุรกิจจริง → `output/legacy-oracle/` อยู่ใน `.gitignore` แล้ว

รูปแบบ CSV — ต้องตรงกับที่ขั้น 1b คาดไว้เป๊ะ
    HEADER true · NULL เขียนเป็นข้อความ `NULL` · UTF-8 · ลำดับคอลัมน์ตาม schema.sql
    วันที่เขียนเป็น ISO `YYYY-MM-DD HH24:MI:SS` เพื่อให้ `::date` / `::timestamp` ฝั่ง PostgreSQL อ่านได้
"""
from __future__ import annotations

import csv
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

try:
    import oracledb
except ImportError:
    print("ต้องติดตั้ง oracledb ก่อน:  python3 -m pip install oracledb", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "output" / "legacy-oracle" / "schema.sql"
OUT = ROOT / "output" / "legacy-oracle" / "rows"

# 10 ตารางที่ migration ใช้ — ชุดเดียวกับ ORA_NEEDED ใน tools/build_k2_migration_sql.py
NEEDED = [
    "FGI_IMPACT_STORE_ON_PROCESS", "FGI_IMPACT_STORE", "FGI_IMPACT_STORE_COMPENSATE",
    "FGI_IMPACT_STORE_INFO", "FGI_NEW_STORE_INFO", "FGI_NEW_STORE_COMPENSATE",
    "FGI_IMPACT_STORE_SALES", "FGI_IMPACT_STORE_SALES_TRN", "FGI_IMPACT_COMPETITOR",
    "FGI_CONFIRM_RECEIVE_DATA",
]
BK_SUFFIX = "_BK_20250515"
NULL_TOKEN = "NULL"      # ต้องตรงกับ WITH (NULL 'NULL') ของขั้น 1b
BATCH = 5000


def columns_of() -> dict[str, list[str]]:
    """อ่านลำดับคอลัมน์จาก schema.sql — **แหล่งเดียวกับที่ generator ใช้สร้างตารางพัก**

    ถ้าอ่านจาก Oracle ตรง ๆ แล้วลำดับต่างจาก schema.sql แม้ช่องเดียว `\\copy` จะเลื่อนคอลัมน์ทั้งไฟล์
    """
    text = SCHEMA.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \((.*?)\n\);", text, re.S):
        name, body = m.group(1), m.group(2)
        cols = []
        for line in body.split("\n"):
            line = line.strip().rstrip(",")
            if not line or line.startswith("--") or line.upper().startswith(("CONSTRAINT", "PRIMARY KEY")):
                continue
            cols.append(line.split()[0])
        out[name] = cols
    return out


def fmt(v) -> str:
    """แปลงค่า Oracle → ข้อความใน CSV"""
    if v is None:
        return NULL_TOKEN
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, Decimal):
        # ตัด .0 ที่ Oracle ใส่ให้ NUMBER ที่ไม่มีทศนิยม — ฝั่งปลายทาง cast เป็น int
        return format(v.normalize(), "f")
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    s = str(v)
    # ค่าที่เป็นข้อความ 'NULL' จริง ๆ จะแยกจาก NULL ไม่ออก — เตือนไว้ (ยังไม่เคยเจอ)
    return s


def guard(sql: str) -> None:
    banned = ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "TRUNCATE ", "ALTER ", "CREATE ", "MERGE ")
    up = " " + sql.upper().replace("\n", " ") + " "
    for w in banned:
        if w in up:
            raise SystemExit(f"🛑 คิวรีมีคำสั่งเขียนข้อมูล ({w.strip()}) — ปฏิเสธ: {sql[:80]}")
    if not up.strip().startswith("SELECT"):
        raise SystemExit(f"🛑 ไม่ใช่ SELECT — ปฏิเสธ: {sql[:80]}")


def main() -> int:
    confirm = "--confirm" in sys.argv
    only = None
    if "--table" in sys.argv:
        only = sys.argv[sys.argv.index("--table") + 1].upper()

    for k in ("ORA_USER", "ORA_PASSWORD", "ORA_HOST", "ORA_SID"):
        if not os.environ.get(k):
            print(f"ขาด environment variable: {k}", file=sys.stderr)
            return 2
    if not SCHEMA.exists():
        print(f"ยังไม่มี {SCHEMA} — รัน tools/introspect_legacy_oracle.py ก่อน", file=sys.stderr)
        return 2

    cols_of = columns_of()
    dsn = oracledb.makedsn(os.environ["ORA_HOST"], int(os.environ.get("ORA_PORT", "1521")),
                           sid=os.environ["ORA_SID"])
    con = oracledb.connect(user=os.environ["ORA_USER"], password=os.environ["ORA_PASSWORD"],
                           dsn=dsn, tcp_connect_timeout=30)
    cur = con.cursor()

    have = {r[0] for r in cur.execute("SELECT table_name FROM user_tables").fetchall()}

    plan: list[tuple[str, str, list[str]]] = []      # (ตาราง Oracle, ไฟล์ปลายทาง, คอลัมน์)
    for base in NEEDED:
        if only and base != only:
            continue
        cols = cols_of.get(base)
        if not cols:
            print(f"  ⚠️ {base}: ไม่มีใน schema.sql — ข้าม")
            continue
        for src in (base, base + BK_SUFFIX):
            if src in have:
                plan.append((src, src + ".csv", cols))

    print(f"ฐาน   : {os.environ['ORA_HOST']} · SID {os.environ['ORA_SID']} · user {os.environ['ORA_USER']}")
    print(f"โหมด  : {'🔴 ดึงจริง (--confirm)' if confirm else '🟢 dry-run (นับแถวอย่างเดียว)'}")
    print(f"ปลายทาง: {OUT.relative_to(ROOT)}/\n")
    print(f"{'ตาราง':<46}{'แถวจริง':>10}  คอลัมน์")

    total = 0
    counts: dict[str, int] = {}
    for src, fname, cols in plan:
        q = f"SELECT count(*) FROM {src}"
        guard(q)
        n = cur.execute(q).fetchone()[0]
        counts[src] = n
        total += n
        # คอลัมน์ของตาราง BK ต้องเท่าตาราง live ไม่งั้น \copy เลื่อน
        real = [r[0] for r in cur.execute(
            "SELECT column_name FROM user_tab_columns WHERE table_name = :t ORDER BY column_id",
            t=src).fetchall()]
        mark = "✅" if set(real) >= set(c.upper() for c in cols) else "🛑 คอลัมน์ไม่ครบ"
        print(f"  {src:<44}{n:>10,}  {len(cols)} {mark}")
        if mark.startswith("🛑"):
            missing = sorted(set(c.upper() for c in cols) - set(real))
            print(f"      ขาด: {', '.join(missing)}")
    print(f"\nรวม {total:,} แถว · {len(plan)} ไฟล์")

    if not confirm:
        print("\n🟢 dry-run จบ — ยังไม่เขียนไฟล์ · ใส่ --confirm เพื่อดึงจริง")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    print()
    for src, fname, cols in plan:
        q = f"SELECT {', '.join(cols)} FROM {src}"
        guard(q)
        cur.execute(q)
        cur.arraysize = BATCH
        path = OUT / fname
        written = 0
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cols)
            while True:
                rows = cur.fetchmany(BATCH)
                if not rows:
                    break
                w.writerows([[fmt(v) for v in r] for r in rows])
                written += len(rows)
        ok = written == counts[src]
        print(f"  {'✅' if ok else '🛑'} {src:<44}{written:>10,} แถว  "
              f"{path.stat().st_size/1048576:.1f} MB" + ("" if ok else f"  ≠ {counts[src]:,}"))
        if not ok:
            print("      🛑 จำนวนแถวที่เขียนไม่ตรงกับ count(*) — ข้อมูลอาจเปลี่ยนระหว่างดึง")

    size = sum(f.stat().st_size for f in OUT.glob("*.csv"))
    print(f"\n✅ ดึงครบ {len(plan)} ไฟล์ · {total:,} แถว · {size/1048576:.1f} MB")
    print(f"   โหลดต่อด้วย: output/sql/k2_migration_1b_stage_oracle.sql (ชี้ :dump ไปที่โฟลเดอร์นี้)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
