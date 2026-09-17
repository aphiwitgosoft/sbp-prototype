#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สำรองข้อมูลฝั่ง SGI ของฐาน dev ก่อนทำ migration

    PGPASSWORD='...' python3 tools/backup_sgi_dev.py [--confirm]
    (host/user/database ของฐาน dev เป็นค่าตั้งต้นในไฟล์ · override ได้ด้วย PGHOST/PGUSER/PGDATABASE)

ทำไมต้องมีเครื่องมือนี้ (แทน pg_dump)
    เครื่องที่ใช้งานอยู่**ไม่มี `pg_dump` / `psql`** — เครื่องมือนี้ใช้ `COPY … TO STDOUT`
    ผ่าน pg8000 ซึ่งเป็น **การอ่านล้วน** และได้ CSV ที่ `COPY … FROM` กลับเข้าไปได้ตรง ๆ

ขอบเขตที่สำรอง (= ทุกอย่างที่ migration แตะได้)
    1. ตาราง `sgi_*` **ของเราเองทุกตัว** (ทั้งตารางจริงและตารางพัก) — โครง + ข้อมูล
    2. **เฉพาะแถวของ SGI** ในตารางของระบบเดิม 4 ตัว
       (`common_code_type` · `common_code` · `mas_param` · `email_template`)
       → ไม่แตะ ไม่คัดลอกข้อมูลของทีมอื่นออกมา

⚠️ ตารางพักที่ใหญ่มาก (`sgi_mig_k2_*`) ข้ามการ dump ข้อมูลโดยตั้งใจ — ต้นทางคือ CSV
   ใน `docs/data_bk_all/` ที่ยังอยู่ · สำรองไว้แค่จำนวนแถวเพื่อใช้ตรวจว่ากู้คืนครบ
   (บังคับ dump ได้ด้วย `--full-staging`)

🔒 SELECT/COPY TO ล้วน — ไม่มีคำสั่งเขียนข้อมูลสักคำสั่ง
⚠️ ผลลัพธ์มีข้อมูลธุรกิจจริง — เขียนลง `backup/` ซึ่งอยู่ใน `.gitignore`
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import pg8000.native
except ImportError:  # pragma: no cover
    print("ต้องมี pg8000 (pip install pg8000)", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
BACKUP_ROOT = ROOT / "backup"

# ตารางของระบบเดิมที่ seed ของเราแตะ — สำรองเฉพาะแถวของ SGI เท่านั้น
LEGACY_SCOPE = {
    "common_code_type": "code_type LIKE 'SGI!_%' ESCAPE '!'",
    "common_code": "code_type LIKE 'SGI!_%' ESCAPE '!'",
    "mas_param": "param_name LIKE 'SGI!_%' ESCAPE '!'",
    "email_template": "create_by = 'SGI-SETUP'",
}
BIG_STAGING_PREFIX = "sgi_mig_"


# ค่าตั้งต้นของฐาน **dev** (ไม่ใช่ prod) — host/user ไม่ใช่ความลับ และมีบันทึกอยู่แล้วใน
# SBP/db-schema-sps_store.md · override ได้ด้วย env · **รหัสผ่านไม่มีค่าตั้งต้น ต้องส่งผ่าน env เสมอ**
DEFAULT_HOST = ("srm-sps-spsap-postgres-instance-dev-new-instance-1"
                ".cxsegsg200gm.ap-southeast-1.rds.amazonaws.com")
DEFAULT_USER = "sps_store"
DEFAULT_DB = "postgres"


def connect():
    host = os.environ.get("PGHOST") or DEFAULT_HOST
    user = os.environ.get("PGUSER") or DEFAULT_USER
    if not os.environ.get("PGPASSWORD"):
        print("ขาด PGPASSWORD — ส่งผ่าน env เท่านั้น เช่น\n"
              "    PGPASSWORD='...' python3 tools/backup_sgi_dev.py", file=sys.stderr)
        raise SystemExit(2)
    if "-dev-" not in host:
        print(f"ปฏิเสธ: host ไม่ใช่ฐาน dev → {host}", file=sys.stderr)
        raise SystemExit(2)
    os.environ["PGHOST"], os.environ["PGUSER"] = host, user
    return pg8000.native.Connection(
        user=user, password=os.environ["PGPASSWORD"],
        host=host, port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", DEFAULT_DB), ssl_context=True, timeout=1800)


def table_ddl(c, table: str) -> str:
    """ประกอบ CREATE TABLE จาก information_schema — พอให้กู้โครงกลับได้"""
    cols = c.run("""SELECT column_name, data_type, character_maximum_length, numeric_precision,
                           numeric_scale, is_nullable, column_default
                      FROM information_schema.columns
                     WHERE table_schema='sps_store' AND table_name=:t ORDER BY ordinal_position""", t=table)
    parts = []
    for name, dt, clen, prec, scale, nul, dflt in cols:
        t = dt
        if dt == "character varying" and clen:
            t = f"VARCHAR({clen})"
        elif dt == "character" and clen:
            t = f"CHAR({clen})"
        elif dt == "numeric" and prec is not None:
            t = f"NUMERIC({prec},{scale})"
        elif dt == "timestamp without time zone":
            t = "TIMESTAMP"
        elif dt == "timestamp with time zone":
            t = "TIMESTAMPTZ"
        line = f"    {name} {t}"
        if dflt:
            line += f" DEFAULT {dflt}"
        if nul == "NO":
            line += " NOT NULL"
        parts.append(line)
    return f"CREATE TABLE sps_store.{table} (\n" + ",\n".join(parts) + "\n);"


def main() -> int:
    confirm = "--confirm" in sys.argv
    full_staging = "--full-staging" in sys.argv
    c = connect()
    c.run("SET search_path TO sps_store")

    own = [r[0] for r in c.run("""SELECT table_name FROM information_schema.tables
             WHERE table_schema='sps_store' AND table_type='BASE TABLE'
               AND table_name LIKE 'sgi!_%' ESCAPE '!' ORDER BY 1""")]
    real = [t for t in own if not t.startswith(BIG_STAGING_PREFIX)]
    staging = [t for t in own if t.startswith(BIG_STAGING_PREFIX)]

    plan: list[tuple[str, str | None, bool]] = []          # (ตาราง, where, dump ข้อมูลไหม)
    for t in real:
        plan.append((t, None, True))
    for t in staging:
        plan.append((t, None, full_staging))
    for t, w in LEGACY_SCOPE.items():
        plan.append((t, w, True))

    print(f"ฐาน      : {os.environ['PGHOST']}")
    print(f"รุ่น      : {c.run('SELECT version()')[0][0].split(',')[0]}")
    print(f"โหมด     : {'🔴 สำรองจริง (--confirm)' if confirm else '🟢 dry-run (ยังไม่เขียนไฟล์)'}")
    print(f"ตารางพัก : {'dump ข้อมูลด้วย (--full-staging)' if full_staging else 'ข้ามข้อมูล เก็บแค่จำนวนแถว'}\n")

    print(f"{'ตาราง':<40}{'แถว':>10}  ขอบเขต")
    total = 0
    rows_of = {}
    for t, where, dump in plan:
        n = c.run(f"SELECT count(*) FROM {t}" + (f" WHERE {where}" if where else ""))[0][0]
        rows_of[t] = n
        total += n if dump else 0
        scope = "ทั้งตาราง" if where is None else "เฉพาะแถว SGI"
        if not dump:
            scope += " · ข้ามข้อมูล (กู้จาก docs/data_bk_all/ ได้)"
        print(f"  {t:<38}{n:>10,}  {scope}")
    print(f"\nรวมแถวที่จะเขียนลงไฟล์ {total:,}")

    if not confirm:
        print("\n🟢 dry-run จบ — ยังไม่เขียนไฟล์ · ใส่ --confirm เพื่อสำรองจริง")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = BACKUP_ROOT / f"sgi-dev-{stamp}"
    (out / "data").mkdir(parents=True, exist_ok=True)
    print(f"\nเขียนลง {out.relative_to(ROOT)}")

    ddl: list[str] = []
    manifest = {"created_at": datetime.now().isoformat(timespec="seconds"),
                "host": os.environ["PGHOST"], "schema": "sps_store",
                "full_staging": full_staging, "tables": {}}

    for t, where, dump in plan:
        ddl.append(table_ddl(c, t) if t not in LEGACY_SCOPE else
                   f"-- {t} เป็นตารางของระบบเดิม — ไม่เก็บ DDL (ห้ามสร้างทับ)")
        entry = {"rows": rows_of[t], "where": where, "dumped": dump}
        if dump:
            src = t if where is None else f"(SELECT * FROM {t} WHERE {where})"
            buf = io.BytesIO()
            c.run(f"COPY {src} TO STDOUT WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')", stream=buf)
            f = out / "data" / f"{t}.csv"
            f.write_bytes(buf.getvalue())
            entry["file"] = f"data/{t}.csv"
            entry["bytes"] = f.stat().st_size
            print(f"  ✅ {t:<38}{rows_of[t]:>10,} แถว  {entry['bytes']/1024:.0f} KB")
        else:
            print(f"  ⏭️  {t:<38}{rows_of[t]:>10,} แถว  (ข้ามข้อมูล)")
        manifest["tables"][t] = entry

    (out / "schema.sql").write_text(
        "-- snapshot โครงตารางฝั่ง SGI ณ เวลาสำรอง — ใช้ดูเทียบ ไม่ใช่สคริปต์ติดตั้ง\n"
        "-- ตัวติดตั้งจริงคือ output/sql/sgi_schema.sql ที่ generate จาก DDL ต้นฉบับ\n\n"
        + "\n\n".join(ddl) + "\n", encoding="utf-8")
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    restore = ["# วิธีกู้คืน", "",
               f"สำรองเมื่อ **{manifest['created_at']}** จาก `{manifest['host']}`", "",
               "⚠️ ไฟล์ทั้งหมดมีข้อมูลธุรกิจจริง — โฟลเดอร์ `backup/` อยู่ใน `.gitignore`", "",
               "## ลำดับการกู้ (สำคัญ — FK ผูกกันอยู่)", "",
               "```sql", "BEGIN;", "SET search_path TO sps_store;", ""]
    for t, where, dump in plan:
        if not dump:
            restore.append(f"-- {t}: ไม่ได้ dump ข้อมูล · โหลดใหม่จาก docs/data_bk_all/ "
                           f"ด้วย k2_migration_1_stage.sql (ควรได้ {rows_of[t]:,} แถว)")
            continue
        if where is None:
            restore.append(f"TRUNCATE {t} CASCADE;")
        else:
            restore.append(f"DELETE FROM {t} WHERE {where};   -- แตะเฉพาะแถวของ SGI")
        restore.append(f"\\copy {t} FROM 'data/{t}.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')")
        restore.append(f"ANALYZE {t};")
        restore.append("")
    restore += ["COMMIT;", "```", "",
                "## ตรวจหลังกู้", "", "| ตาราง | แถวที่ควรได้ |", "|---|---:|"]
    for t, _w, _d in plan:
        restore.append(f"| `{t}` | {rows_of[t]:,} |")
    (out / "RESTORE.md").write_text("\n".join(restore) + "\n", encoding="utf-8")

    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"\n✅ สำรองเสร็จ · {len(plan)} ตาราง · {size/1048576:.1f} MB")
    print(f"   {out.relative_to(ROOT)}/manifest.json · RESTORE.md · schema.sql · data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
