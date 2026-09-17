#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""โหลด CSV โซน A เข้าตารางพัก `sgi_mig_ora_*` — ตัวแทน `psql \\copy`

    PGPASSWORD=... python3 tools/apply_ora_stage.py [--confirm]

ทำไมต้องมีตัวนี้
────────────────
เครื่องนี้**ไม่มี `psql`** จึงรัน `\\copy` ใน `output/sql/k2_migration_1b_stage_oracle.sql`
ไม่ได้ · ตัวนี้อ่านสคริปต์ชุดเดียวกันแล้วเล่นตามทีละส่วนผ่าน pg8000
(`COPY … FROM STDIN` ทำงานได้ปกติ) — **ตรรกะและลำดับยึดจากไฟล์ที่ generate เสมอ**

ลำดับเหมือนไฟล์ทุกประการ:
  1. CREATE TABLE (src ยอม NULL · ไม่มี DEFAULT) + TRUNCATE
  2. COPY live  → UPDATE src = 'LIVE'
  3. COPY bk    → UPDATE src = 'BK'
  4. SET NOT NULL + index + ANALYZE
  5. ตรวจจำนวนแถวแยกตาม src เทียบสถิติต้นทาง — ไม่ตรง = ROLLBACK

ทั้งหมดอยู่ใน **ทรานแซกชันเดียว** · ไม่ใส่ --confirm = dry-run
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pg8000.native

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "output" / "sql" / "k2_migration_1b_stage_oracle.sql"
ROWS = ROOT / "output" / "legacy-oracle" / "rows"
DEFAULT_HOST = ("srm-sps-spsap-postgres-instance-dev-new"
                ".cluster-cxsegsg200gm.ap-southeast-1.rds.amazonaws.com")


COPY_RE = re.compile(r"^\\copy (\w+) \((.*?)\) FROM :'dump'/([\w.]+) WITH \((.*?)\)$")


def steps(text: str):
    """เดินไฟล์จากบนลงล่าง คืน ('sql', คำสั่ง) หรือ ('copy', (ตาราง, คอลัมน์, ไฟล์, options))

    🔴 **ต้องรักษาลำดับของไฟล์ไว้** — บล็อกตรวจจำนวนแถวอยู่ท้ายไฟล์และต้องรันหลัง COPY
       ถ้าแยก COPY ออกไปทำทีหลัง บล็อกตรวจจะเห็นตารางว่างแล้ว RAISE ทันที
    """
    buf, in_do = [], False
    for line in text.split("\n"):
        st = line.strip()
        m = COPY_RE.match(st)
        if m and not in_do:
            if "".join(buf).strip():
                yield "sql", "\n".join(buf)
            buf = []
            yield "copy", (m.group(1), m.group(2), m.group(3), m.group(4))
            continue
        if not in_do and (st.startswith("\\") or st.startswith("--") or not st):
            continue
        if st.startswith("DO $$"):
            in_do = True
        buf.append(line)
        if in_do:
            if st.endswith("END $$;"):
                in_do = False
                yield "sql", "\n".join(buf); buf = []
        elif st.endswith(";"):
            yield "sql", "\n".join(buf); buf = []
    if "".join(buf).strip():
        yield "sql", "\n".join(buf)


def main() -> int:
    confirm = "--confirm" in sys.argv
    if not os.environ.get("PGPASSWORD"):
        print("ขาด PGPASSWORD — ส่งผ่าน env เท่านั้น", file=sys.stderr); return 2
    if not ROWS.is_dir():
        print(f"ยังไม่มี {ROWS} — รัน tools/dump_legacy_oracle_rows.py --confirm ก่อน", file=sys.stderr)
        return 2

    text = SQL.read_text(encoding="utf-8")
    host = os.environ.get("PGHOST") or DEFAULT_HOST
    if "-dev-" not in host:
        print(f"ปฏิเสธ: host ไม่ใช่ฐาน dev → {host}", file=sys.stderr); return 2

    # แผนการโหลด: อ่านจากบรรทัด \copy ในไฟล์ที่ generate — ไม่เดาเอง
    loads = []
    for m in re.finditer(r"^\\copy (\w+) \((.*?)\) FROM :'dump'/([\w.]+) WITH \((.*?)\)$",
                         text, re.M):
        loads.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    # คำสั่ง UPDATE src ที่ตามหลัง \copy แต่ละบรรทัด
    srcs = re.findall(r"^UPDATE (\w+) SET src = '(\w+)' WHERE src IS NULL;$", text, re.M)

    print(f"ฐาน   : {host}")
    print(f"สคริปต์: {SQL.relative_to(ROOT)}")
    print(f"โหมด  : {'🔴 โหลดจริง (--confirm)' if confirm else '🟢 dry-run'}\n")
    print(f"{'ตารางพัก':<42}{'ไฟล์':>12}  src")
    missing = []
    for i, (tbl, cols, fname, opts) in enumerate(loads):
        f = ROWS / fname
        src = srcs[i][1] if i < len(srcs) else "?"
        n = sum(1 for _ in f.open(encoding="utf-8")) - 1 if f.exists() else -1
        print(f"  {tbl:<40}{(f'{n:,}' if n >= 0 else 'ไม่มีไฟล์'):>12}  {src}")
        if n < 0:
            missing.append(fname)
    if missing:
        print(f"\n🛑 ขาดไฟล์ {len(missing)}: {', '.join(missing)}"); return 1
    if not confirm:
        print(f"\n🟢 dry-run จบ · ใส่ --confirm เพื่อโหลดจริง ({len(loads)} ไฟล์)"); return 0

    c = pg8000.native.Connection(user=os.environ.get("PGUSER", "sps_store"),
        password=os.environ["PGPASSWORD"], host=host,
        port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "postgres"), ssl_context=True, timeout=3600)
    c.run("SET search_path TO sps_store")
    c.run("BEGIN")
    try:
        done = 0
        for kind, item in steps(text):
            if kind == "copy":
                tbl, cols, fname, opts = item
                with (ROWS / fname).open("rb") as f:
                    c.run(f"COPY {tbl} ({cols}) FROM STDIN WITH ({opts})", stream=f)
                done += 1
                continue
            stmt = item.strip()
            if stmt.upper().startswith(("BEGIN", "COMMIT", "SET SEARCH_PATH")):
                continue
            up = stmt.upper()
            # guard: ทุกคำสั่งต้องแตะเฉพาะตารางพักของเรา
            assert "SGI_MIG_ORA_" in up, f"คำสั่งนอกขอบเขต: {stmt.splitlines()[0][:70]}"
            assert not re.search(r"\bDROP\s+TABLE\b", up), "มีคำสั่ง DROP — ปฏิเสธ"
            c.run(stmt)
            if up.startswith("UPDATE") and "SET SRC" in up:
                m = re.match(r"UPDATE (\w+) SET src = '(\w+)'", stmt)
                if m:
                    n = c.run(f"SELECT count(*) FROM {m.group(1)} WHERE src = '{m.group(2)}'")[0][0]
                    print(f"  ✅ {m.group(1):<40}{n:>10,} แถว  src={m.group(2)}")
        print(f"\n  COPY สำเร็จ {done} ไฟล์ · ผ่านบล็อกตรวจจำนวนแถวแล้ว")
        c.run("COMMIT")
        print("\n✅ COMMIT")
    except Exception:
        c.run("ROLLBACK"); print("\n🛑 ROLLBACK — ฐานไม่ถูกแตะ"); raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
