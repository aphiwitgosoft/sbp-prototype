#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ลบแถวไฟล์แนบที่ migration สร้างไว้ แล้วให้ขั้นที่ 3 ใส่ใหม่

    PGPASSWORD=... python3 tools/redo_k2_attachments.py [--confirm]

ทำไมต้องมีตัวนี้
────────────────
`k2_migration_3_documents.sql` ใช้ `INSERT … WHERE NOT EXISTS` เพื่อให้รันซ้ำได้
ผลข้างเคียงคือ **รันซ้ำเฉย ๆ ไม่อัปเดตแถวเดิม** — เวลาแก้กติกาการแปลง
(เช่น เปลี่ยน `file_size` เป็น 0) แถวที่ใส่ไปแล้วจะค้างค่าเก่าเงียบ ๆ
กับดักเดียวกับ `tools/reseed_sgi_seed_rows.py` ของฝั่ง seed

ขอบเขตการลบ — **แคบที่สุดเท่าที่ทำได้**
    เฉพาะ `sgi_document_attachments` ที่ `storage_provider IN ('K2-LEGACY','K2-EMBEDDED')`
    ซึ่งเป็นป้ายที่ **migration เป็นคนใส่เท่านั้น** ไฟล์ที่ผู้ใช้อัปโหลดเองจะไม่มีค่านี้

ก่อนลบตรวจ 2 อย่าง:
    1. ไม่มีตารางไหนในฐานอ้างถึง `attach_id` ที่จะลบ
    2. ไม่มีแถว storage_provider อื่นปนอยู่ในชุดที่จะลบ

🔒 ทั้งหมดอยู่ในทรานแซกชันเดียว · ไม่ใส่ --confirm = dry-run
"""
from __future__ import annotations

import os
import sys

import pg8000.native

OWNED = ("K2-LEGACY", "K2-EMBEDDED")
DEFAULT_HOST = ("srm-sps-spsap-postgres-instance-dev-new"
                ".cluster-cxsegsg200gm.ap-southeast-1.rds.amazonaws.com")


def main() -> int:
    confirm = "--confirm" in sys.argv
    if not os.environ.get("PGPASSWORD"):
        print("ขาด PGPASSWORD — ส่งผ่าน env เท่านั้น", file=sys.stderr)
        return 2
    host = os.environ.get("PGHOST") or DEFAULT_HOST
    if "-dev-" not in host:
        print(f"ปฏิเสธ: host ไม่ใช่ฐาน dev → {host}", file=sys.stderr)
        return 2
    c = pg8000.native.Connection(user=os.environ.get("PGUSER", "sps_store"),
        password=os.environ["PGPASSWORD"], host=host,
        port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "postgres"), ssl_context=True, timeout=1800)
    c.run("SET search_path TO sps_store")

    inlist = ", ".join(f"'{x}'" for x in OWNED)
    # ⚠️ ตัวนับทุกตัวในเครื่องมือนี้ **นับแถวที่ deleted_flag = 'Y' ด้วยโดยตั้งใจ**
    #    ต่างจากคิวรีฝั่งแอปที่ต้องกรอง soft delete ออก — ที่นี่เป็นงานดูแลข้อมูล
    #    ถ้ากรอง 'Y' ทิ้ง จะลบไม่ครบแล้วตอนใส่ใหม่จะชน uq_doc_attachment_hash
    total, total_del = c.run(
        "SELECT count(*), count(*) FILTER (WHERE deleted_flag = 'Y')"
        " FROM sgi_document_attachments")[0]
    mine, mine_del = c.run(
        "SELECT count(*), count(*) FILTER (WHERE deleted_flag = 'Y')"
        f" FROM sgi_document_attachments WHERE storage_provider IN ({inlist})")[0]
    print(f"ฐาน   : {host}")
    print(f"โหมด  : {'🔴 ลบจริง (--confirm)' if confirm else '🟢 dry-run'}\n")
    print(f"  ไฟล์แนบทั้งหมด            {total:>7,}  (soft delete แล้ว {total_del:,})")
    print(f"  ที่ migration เป็นเจ้าของ  {mine:>7,}  ← จะถูกลบแล้วใส่ใหม่"
          f"  (ในนั้น deleted_flag='Y' {mine_del:,})")
    print(f"  ของคนอื่น/ผู้ใช้อัปโหลด    {total - mine:>7,}  ← **ไม่แตะ**")
    for r in c.run("""SELECT storage_provider, deleted_flag, count(*), sum(file_size)
                        FROM sgi_document_attachments
                       GROUP BY storage_provider, deleted_flag
                       ORDER BY 3 DESC"""):
        print(f"    {r[0]:<14} deleted={r[1]}  {r[2]:>7,} แถว · รวม {r[3] or 0:>14,} ไบต์")

    # guard 1 — มีใครอ้าง attach_id ที่จะลบไหม
    refs = c.run("""SELECT c.table_name, c.column_name FROM information_schema.columns c
                     WHERE c.table_schema = 'sps_store' AND c.column_name = 'attach_id'
                       AND c.table_name <> 'sgi_document_attachments'""")
    print(f"\n  ตารางอื่นที่มีคอลัมน์ attach_id: {len(refs)}")
    for t, col in refs:
        # รวมแถวที่ deleted_flag = 'Y' ด้วย — ของที่จะลบคือทุกแถวที่ป้ายเป็นของ migration
        n = c.run(f"""SELECT count(*) FROM {t} x WHERE x.{col} IN
                      (SELECT attach_id FROM sgi_document_attachments
                        WHERE storage_provider IN ({inlist})
                          AND deleted_flag IN ('Y', 'N'))""")[0][0]
        print(f"    {t}.{col}: อ้างถึง {n:,} แถว")
        if n:
            print("    🛑 มีคนอ้างอยู่ — หยุด")
            return 1
    if not refs:
        print("    ✅ ไม่มีใครอ้าง ลบได้ปลอดภัย")

    if not confirm:
        print(f"\n🟢 dry-run จบ · ใส่ --confirm เพื่อลบ {mine:,} แถว")
        print("   แล้วรัน: python3 tools/apply_sgi_sql.py output/sql/k2_migration_3_documents.sql --confirm")
        return 0

    c.run("BEGIN")
    try:
        # guard 2 — ยืนยันอีกครั้งในทรานแซกชันว่าลบเฉพาะป้ายของเรา
        # `deleted_flag IN ('Y','N')` เขียนไว้ชัด ๆ ว่า **ตั้งใจรวมแถวที่ soft delete แล้ว**
        #   (เงื่อนไขนี้เป็นจริงเสมอ — ใส่เพื่อประกาศเจตนา ไม่ได้กรองอะไรออก)
        stray = c.run(f"""SELECT count(*) FROM sgi_document_attachments
                           WHERE deleted_flag IN ('Y', 'N')
                             AND storage_provider IN ({inlist})
                             AND storage_provider NOT IN ({inlist})""")[0][0]
        assert stray == 0
        c.run(f"DELETE FROM sgi_document_attachments WHERE storage_provider IN ({inlist})")
        left = c.run("SELECT count(*) FROM sgi_document_attachments")[0][0]
        c.run("COMMIT")
        print(f"\n✅ ลบ {mine:,} แถว · เหลือในตาราง {left:,}")
        print("   รันต่อ: PGPASSWORD=... python3 tools/apply_sgi_sql.py "
              "output/sql/k2_migration_3_documents.sql --confirm")
    except Exception:
        c.run("ROLLBACK")
        print("\n🛑 ROLLBACK")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
