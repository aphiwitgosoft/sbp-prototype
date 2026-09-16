#!/usr/bin/env python3
"""
ติดตั้งสคริปต์ SQL ของ SGI ลงฐานจริง — พร้อม **guard ก่อนยิง**

    PGHOST=... PGUSER=... PGPASSWORD=... python3 tools/apply_sgi_sql.py output/sql/sgi_schema.sql --confirm

⚠️ credential อ่านจาก environment variable เท่านั้น — **ห้ามใส่ค่าจริงลงไฟล์**
⚠️ ไม่ใส่ `--confirm` = dry-run (ตรวจอย่างเดียว ไม่ยิงอะไรลงฐาน)
⚠️ `--trial` = รันจริงบนฐานจริงแล้ว **ROLLBACK เสมอ** — ใช้พิสูจน์ว่าไฟล์รันผ่าน
   (syntax · constraint · duplicate key) โดยไม่เขียนอะไรค้างไว้ · ใช้คู่กับ --confirm ไม่ได้

guard ที่ตรวจก่อนยิงทุกครั้ง:
  1. ไฟล์ต้องตรงกับ generator (ไม่ใช่ไฟล์ที่ใครแก้ด้วยมือ)
  2. ทุก CREATE/ALTER TABLE ต้องแตะตารางที่ขึ้นต้นด้วย sgi_ เท่านั้น
  3. ห้ามมี DROP / TRUNCATE / DELETE / UPDATE ที่ไม่ได้อยู่ในคอมเมนต์
  4. ไฟล์ต้องอยู่ในทรานแซกชันเดียว (BEGIN … COMMIT) — พังกลางทางต้องไม่เหลือขยะ
  5. รายงานสภาพฐานก่อน–หลัง ให้เทียบได้

ไฟล์ rollback ได้รับการยกเว้นข้อ 3 (หน้าที่ของมันคือลบ) แต่ต้องลบเฉพาะ sgi_
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pg8000.native
except ImportError:  # pragma: no cover
    print("ต้องติดตั้ง pg8000 ก่อน:  python3 -m pip install pg8000", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
DESTRUCTIVE = ("DROP", "TRUNCATE", "DELETE FROM", "UPDATE ")


def strip_psql_meta(sql: str) -> str:
    """ตัดคำสั่งเฉพาะของ psql (\\set · \\echo · \\d) ที่ driver ไม่รู้จัก"""
    return "\n".join(l for l in sql.split("\n") if not l.lstrip().startswith("\\"))


def guard(path: Path, sql: str) -> list[str]:
    bad: list[str] = []
    is_rollback = "rollback" in path.name

    # 1) ตรงกับ generator ไหม
    if path.name in ("sgi_schema.sql", "sgi_seed_data.sql", "sgi_schema_rollback.sql"):
        # ⚠️ generator ต้องใช้ python-docx/reportlab ซึ่งมักอยู่ใน python ของระบบ ไม่ใช่ venv ของ driver
        #    จึงเรียกผ่าน subprocess แทนการ import ตรง — ให้เครื่องมือนี้ทำงานได้ทั้งสองแบบ
        script = (
            "import sys,tempfile,pathlib;sys.path.insert(0,'tools');"
            "import build_sgi_schema_sql as BS;"
            "d=tempfile.mkdtemp(dir='output');"
            "saved=BS.OUT_DIR;BS.OUT_DIR=pathlib.Path(d);BS.main();BS.OUT_DIR=saved;"
            "print(d)"
        )
        try:
            r = subprocess.run([os.environ.get("SGI_PYTHON", "python3"), "-c", script],
                               cwd=ROOT, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                bad.append(f"generate ใหม่เพื่อเทียบไม่สำเร็จ: {r.stderr.strip().splitlines()[-1][:120]}")
            else:
                td = Path(r.stdout.strip().splitlines()[-1])
                gen = td / path.name
                if gen.exists() and gen.read_bytes() != path.read_bytes():
                    bad.append("ไฟล์ไม่ตรงกับ generator — อาจถูกแก้ด้วยมือ · รัน build_sgi_schema_sql.py ก่อน")
                import shutil
                shutil.rmtree(td, ignore_errors=True)
        except Exception as exc:                      # pragma: no cover
            bad.append(f"ตรวจความตรงกับ generator ไม่ได้: {exc}")

    # 2) CREATE/ALTER ต้องแตะเฉพาะ sgi_
    for m in re.finditer(r"^(CREATE TABLE|ALTER TABLE|CREATE INDEX.*?ON)\s+(\S+)", sql, re.M):
        target = m.group(2).split("(")[0].strip()
        if not target.startswith("sgi_"):
            bad.append(f"แตะตารางที่ไม่ใช่ของ SGI: {m.group(0)[:70]}")

    # 3) คำสั่งทำลาย
    for line in sql.split("\n"):
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        for kw in DESTRUCTIVE:
            if s.upper().startswith(kw):
                obj = s.split()[-1].rstrip(";").split(".")[-1]
                if is_rollback and (obj.startswith("sgi_") or "sgi_" in s):
                    continue
                bad.append(f"มีคำสั่งทำลาย: {s[:70]}")

    # 4) ทรานแซกชันเดียว
    if sql.count("\nBEGIN;") + sql.startswith("BEGIN;") < 1 or "COMMIT;" not in sql:
        bad.append("ไฟล์ไม่ได้อยู่ในทรานแซกชันเดียว (ต้องมี BEGIN … COMMIT)")
    return bad


def snapshot(con) -> dict:
    q = lambda s: con.run(s)[0][0]
    return {
        "ตาราง sgi_": q("SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema='sps_store' AND table_name LIKE 'sgi!_%' ESCAPE '!'"),
        "index idx_": q("SELECT count(*) FROM pg_indexes "
                        "WHERE schemaname='sps_store' AND indexname LIKE 'idx!_%' ESCAPE '!'"),
        "ตารางทั้งหมด": q("SELECT count(*) FROM information_schema.tables "
                          "WHERE table_schema='sps_store' AND table_type='BASE TABLE'"),
        "common_code SGI": q("SELECT count(*) FROM sps_store.common_code "
                             "WHERE code_type LIKE 'SGI!_%' ESCAPE '!'"),
        "mas_param SGI": q("SELECT count(*) FROM sps_store.mas_param "
                           "WHERE param_name LIKE 'SGI!_%' ESCAPE '!'"),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    confirm = "--confirm" in sys.argv
    trial = "--trial" in sys.argv
    if confirm and trial:
        print("เลือกได้อย่างเดียว: --trial หรือ --confirm", file=sys.stderr)
        return 2
    if not path.exists():
        print(f"ไม่พบไฟล์ {path}", file=sys.stderr)
        return 2
    raw = path.read_text(encoding="utf-8")
    sql = strip_psql_meta(raw)

    print(f"ไฟล์      : {path}")
    print(f"ขนาด      : {len(raw):,} ไบต์ · {raw.count(chr(10)):,} บรรทัด")
    mode = ("🔴 ยิงจริง (--confirm)" if confirm else
            "🟡 trial (รันจริงแล้ว ROLLBACK)" if trial else
            "🟢 dry-run (ยังไม่ยิง)")
    print(f"โหมด      : {mode}\n")

    bad = guard(path, sql)
    print("── guard ก่อนยิง ──")
    if bad:
        for b in bad:
            print(f"  ❌ {b}")
        print("\nหยุด — แก้ปัญหาข้างบนก่อน")
        return 1
    print("  ✅ ไฟล์ตรงกับ generator")
    print("  ✅ ทุก CREATE/ALTER แตะเฉพาะตาราง sgi_")
    print("  ✅ ไม่มีคำสั่งทำลายนอกขอบเขต")
    print("  ✅ อยู่ในทรานแซกชันเดียว\n")

    for k in ("PGHOST", "PGUSER", "PGPASSWORD"):
        if not os.environ.get(k):
            print(f"ขาด environment variable: {k}", file=sys.stderr)
            return 2
    con = pg8000.native.Connection(
        user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"],
        host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "postgres"), ssl_context=True, timeout=300)
    try:
        print(f"ฐาน       : {os.environ['PGHOST']}")
        print(f"รุ่น       : {con.run('SELECT version()')[0][0].split(',')[0]}\n")
        before = snapshot(con)
        print("── ก่อนรัน ──")
        for k, v in before.items():
            print(f"  {k:<22}{v:>6}")
        if not confirm and not trial:
            print("\n🟢 dry-run จบ — ยังไม่มีอะไรถูกเขียนลงฐาน")
            print("   ใส่ --trial เพื่อลองรันจริงแล้ว ROLLBACK · --confirm เพื่อยิงจริง")
            return 0
        run_sql = re.sub(r"(?im)^COMMIT;\s*$", "ROLLBACK;", sql) if trial else sql
        print("\n── กำลังรัน ──")
        con.run(run_sql)
        print("  ✅ รันจบโดยไม่มี error" + ("  (ROLLBACK แล้ว)" if trial else ""))
        after = snapshot(con)
        print("\n── หลังรัน ──")
        for k, v in after.items():
            d = v - before[k]
            print(f"  {k:<22}{v:>6}   {'+' + str(d) if d > 0 else ('' if d == 0 else str(d))}")
        if trial:
            same = all(after[k] == before[k] for k in before)
            print("\n🟡 trial จบ — " + ("ฐานกลับสภาพเดิมครบทุกตัวนับ ✅" if same
                                        else "⚠️ ตัวนับไม่กลับสภาพเดิม — ตรวจด่วน"))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
