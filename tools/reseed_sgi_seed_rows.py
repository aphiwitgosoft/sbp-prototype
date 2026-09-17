#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ล้างแถว seed ของ SGI ในตารางระบบเดิม แล้วรัน sgi_seed_data.sql ใหม่ — ในทรานแซกชันเดียว

    PGHOST=... PGUSER=... PGPASSWORD=... python3 tools/reseed_sgi_seed_rows.py email_template --confirm

ทำไมต้องมีเครื่องมือนี้
    `sgi_seed_data.sql` ใช้ `INSERT ... WHERE NOT EXISTS` จึง **รันซ้ำแล้วไม่อัปเดตของเดิม**
    พอแก้ค่า seed (เช่น เนื้อความอีเมล) แล้วรันใหม่ ค่าเก่าจะค้างอยู่เงียบ ๆ
    หัวไฟล์ seed เขียนคำสั่งล้างไว้ให้ลอกไปรันเอง — สคริปต์นี้ทำให้ขั้นตอนนั้นตรวจสอบได้จริง

ขอบเขตที่บังคับไว้ (แก้ไม่ได้จาก command line)
    * ลบได้เฉพาะตารางใน ``ALLOWED`` และเฉพาะแถวที่ประทับ ``create_by/create_user = SEED_OWNER``
      → ไม่มีทางแตะแถวของทีมอื่น
    * ก่อนลบจะตรวจว่า **ไม่มีคอลัมน์ใดในฐานอ้างถึง id ที่กำลังจะลบ**
    * ลบ + seed อยู่ในทรานแซกชันเดียว — ล้มกลางทาง = ไม่มีอะไรหาย
    * ไม่ใส่ ``--confirm`` = dry-run (รายงานว่าจะลบอะไร แต่ไม่ยิง)

⚠️ credential อ่านจาก environment variable เท่านั้น — ห้ามใส่ค่าจริงลงไฟล์
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import apply_sgi_sql as A                      # noqa: E402  ใช้ guard ชุดเดียวกัน

try:
    import pg8000.native
except ImportError:  # pragma: no cover
    print("ต้องมี pg8000 (pip install pg8000)", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "output" / "sql" / "sgi_seed_data.sql"

# อ่าน SEED_OWNER จากซอร์สของ generator ตรง ๆ — ไม่ import เพราะ generator ต้องใช้ python-docx
# ซึ่ง venv ที่มี pg8000 ไม่มี (guard ของ apply_sgi_sql ก็เรียก python3 ของระบบด้วยเหตุผลเดียวกัน)
_GEN = (ROOT / "tools" / "build_sgi_schema_sql.py").read_text(encoding="utf-8")
_m = re.search(r'^SEED_OWNER\s*=\s*"([^"]+)"', _GEN, re.M)
if not _m:
    print("อ่าน SEED_OWNER จาก tools/build_sgi_schema_sql.py ไม่ได้", file=sys.stderr)
    raise SystemExit(2)
SEED_OWNER = _m.group(1)

# ตาราง → (คอลัมน์เจ้าของแถว, เงื่อนไขจำกัดขอบเขตเพิ่มเติม, คอลัมน์ id สำหรับตรวจการอ้างถึง)
ALLOWED = {
    "email_template": ("create_by", "email_template_name LIKE 'EM-0%'", "email_template_id"),
    "mas_param": ("create_by", "param_name LIKE 'SGI!_%' ESCAPE '!'", None),
    "common_code": ("create_user", "code_type LIKE 'SGI!_%' ESCAPE '!'", None),
    "common_code_type": ("create_user", "code_type LIKE 'SGI!_%' ESCAPE '!'", None),
    # ตารางของ SGI เอง — ไม่ใช่ของระบบเดิม จึงไม่มีคอลัมน์เจ้าของแถว ลบได้ทั้งตาราง
    "sgi_external_factors": (None, "1=1", None),
    "sgi_competitors": (None, "1=1", None),
}


def referencing_columns(con) -> list[tuple[str, str]]:
    """คอลัมน์ทุกตัวในสคีมาที่ชื่อบ่งว่าอาจเก็บ email_template_id"""
    return [(t, c) for t, c in con.run(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='sps_store' AND (column_name ILIKE '%email%id%' OR column_name='email_id') "
        "ORDER BY 1,2") if t != "email_template"]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    confirm = "--confirm" in sys.argv
    if not args:
        print(__doc__, file=sys.stderr)
        print("ตารางที่อนุญาต: " + " ".join(sorted(ALLOWED)), file=sys.stderr)
        return 2
    bad = [t for t in args if t not in ALLOWED]
    if bad:
        print(f"ตารางนอกขอบเขต: {bad} — อนุญาตเฉพาะ {sorted(ALLOWED)}", file=sys.stderr)
        return 2

    raw = SEED.read_text(encoding="utf-8")
    sql = A.strip_psql_meta(raw)
    problems = A.guard(SEED, sql)
    print("── guard ของไฟล์ seed ──")
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
        return 1
    print("  ✅ ไฟล์ตรงกับ generator · INSERT อย่างเดียว · ทรานแซกชันเดียว\n")

    for k in ("PGHOST", "PGUSER", "PGPASSWORD"):
        if not os.environ.get(k):
            print(f"ขาด environment variable: {k}", file=sys.stderr)
            return 2
    con = pg8000.native.Connection(
        user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"],
        host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "postgres"), ssl_context=True, timeout=300)
    try:
        con.run("SET search_path TO sps_store")
        print(f"ฐาน       : {os.environ['PGHOST']}")
        print(f"เจ้าของแถว : {SEED_OWNER}")
        print(f"โหมด      : {'🔴 ยิงจริง (--confirm)' if confirm else '🟢 dry-run'}\n")

        deletes = []
        for t in args:
            owner_col, scope, id_col = ALLOWED[t]
            where = f"{owner_col} = '{SEED_OWNER}' AND {scope}" if owner_col else scope
            n = con.run(f"SELECT count(*) FROM {t} WHERE {where}")[0][0]
            print(f"  {t}: จะลบ {n} แถว  ({where})")
            if id_col and n:
                ids = [str(r[0]) for r in con.run(f"SELECT {id_col} FROM {t} WHERE {where}")]
                print(f"    id: {', '.join(ids)}")
                refs = 0
                for rt, rc in referencing_columns(con):
                    refs += con.run(f'SELECT count(*) FROM "{rt}" WHERE "{rc}"::text = ANY(:i)', i=ids)[0][0]
                if refs:
                    print(f"    ❌ มีคอลัมน์อื่นอ้างถึง id เหล่านี้ {refs} แถว — หยุด ไม่ลบ")
                    return 1
                print("    ✅ ไม่มีที่ไหนอ้างถึง id เหล่านี้")
            deletes.append(f"DELETE FROM {t} WHERE {where};")

        if not confirm:
            print("\n🟢 dry-run จบ — ยังไม่ลบและยังไม่ seed · ใส่ --confirm เพื่อยิงจริง")
            return 0

        print("\n── กำลังลบ + seed ใหม่ (ทรานแซกชันเดียว) ──")
        con.run("BEGIN")
        try:
            for d in deletes:
                con.run(d)
            # ไฟล์ seed คุม BEGIN/COMMIT ของตัวเอง — ตัดออกเพราะเราคุมเอง
            body = "\n".join(l for l in sql.splitlines()
                             if l.strip().upper() not in ("BEGIN;", "COMMIT;"))
            con.run(body)
            con.run("COMMIT")
            print("  ✅ COMMIT แล้ว")
        except Exception:
            con.run("ROLLBACK")
            print("  ↩️ ROLLBACK — ฐานไม่เปลี่ยน")
            raise
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
