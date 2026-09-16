# -*- coding: utf-8 -*-
"""สร้างสคริปต์ SQL ที่รันได้จริง สำหรับสร้างตารางใหม่ 3 โซนของ SGI ลงฐานข้อมูล SBP เดิม

    python3 tools/build_sgi_schema_sql.py     →  output/sql/

ทำไมต้อง generate ไม่เขียนมือ
    DDL ต้นฉบับอยู่ใน ``build_lldd_documents.database_ddl_sections()`` ที่เดียว
    (เอกสาร LLDD-Database ก็อ่านจากตรงนั้น) ถ้าเขียน .sql แยกด้วยมือ อีกไม่นานสองฝั่งจะไม่ตรงกัน
    ไฟล์นี้จึงดึง DDL ชุดเดียวกันมา **เรียงลำดับตาม dependency แล้วตรวจซ้ำ** ก่อนเขียนออกไป

สิ่งที่สคริปต์ผลลัพธ์รับประกัน
    * แตะเฉพาะตารางที่ขึ้นต้นด้วย ``sgi_`` เท่านั้น — **ไม่มี DDL ใดแตะตารางของระบบเดิม**
      (ตรวจอัตโนมัติ: FK ทุกเส้นชี้เข้าในกลุ่มตารางที่สคริปต์นี้สร้างเอง)
    * ลำดับการสร้างปลอดภัยเชิง dependency (ตรวจด้วย topological check)
    * ทั้งไฟล์อยู่ใน transaction เดียว — ล้มกลางทาง = ไม่มีอะไรค้าง
    * มี preflight ที่ **หยุดทันทีถ้ามีตาราง sgi_ อยู่แล้ว** กันรันซ้ำแล้วสถานะครึ่ง ๆ กลาง ๆ
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_lldd_documents as B  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "sql"
TARGET_SCHEMA = "sps_store"


# ---------------------------------------------------------------------------
# ตัวแยกคำสั่ง SQL — ต้องเคารพ string literal และคอมเมนต์ ไม่งั้น ';' ในข้อความจะทำให้แยกผิด
# ---------------------------------------------------------------------------
def split_statements(sql: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    in_str = False
    while i < n:
        ch = sql[i]
        if in_str:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":     # '' คือ escape ของ '
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if ch == "'":
            in_str = True
            buf.append(ch)
            i += 1
            continue
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":      # คอมเมนต์ถึงท้ายบรรทัด
            j = sql.find("\n", i)
            j = n if j < 0 else j
            buf.append(sql[i:j])
            i = j
            continue
        if ch == ";":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf))
    return out


def strip_comments(stmt: str) -> str:
    lines = []
    for line in stmt.split("\n"):
        cut = None
        in_str = False
        k = 0
        while k < len(line):
            if line[k] == "'":
                in_str = not in_str
            elif not in_str and line[k] == "-" and k + 1 < len(line) and line[k + 1] == "-":
                cut = k
                break
            k += 1
        lines.append(line[:cut] if cut is not None else line)
    return "\n".join(lines).strip()


def classify(stmt: str) -> str:
    code = strip_comments(stmt)
    if not code:
        return "comment"
    head = code.split()[0].upper()
    if head == "CREATE":
        return "create_index" if re.match(r"CREATE\s+(UNIQUE\s+)?INDEX", code, re.I) else "create_table"
    if head == "ALTER":
        return "alter"
    return "other"


def table_of(stmt: str) -> str:
    code = strip_comments(stmt)
    m = re.search(r"CREATE TABLE\s+(\w+)", code, re.I) or re.search(r"ALTER TABLE\s+(\w+)", code, re.I)
    return m.group(1) if m else ""


def fks_of(stmt: str) -> set[str]:
    return set(re.findall(r"REFERENCES\s+(\w+)\s*\(", strip_comments(stmt), re.I))


# ---------------------------------------------------------------------------
def collect() -> dict[str, list]:
    creates, alters, indexes, skipped = [], [], [], []
    for title, body in B.database_ddl_sections():
        for stmt in split_statements(body):
            kind = classify(stmt)
            if kind == "comment":
                continue
            if kind == "create_table":
                creates.append((title, stmt))
            elif kind == "create_index":
                indexes.append((title, stmt))
            elif kind == "alter":
                alters.append((title, stmt))
            else:
                # ตัวอย่าง DML (เช่น WITH purge_candidates ... DELETE) ไม่ใช่ DDL — ไม่เอาเข้าสคริปต์
                skipped.append((title, strip_comments(stmt)[:70]))
    return {"creates": creates, "alters": alters, "indexes": indexes, "skipped": skipped}


ZONE_OF_TITLE = {"5.1": "C", "5.2": "A", "5.3": "B"}


def zone_of(title: str) -> str:
    return ZONE_OF_TITLE.get(title.split()[0], "?")


ZONE_RANK = {"C": 0, "A": 1, "B": 2}


def order_creates(creates: list) -> tuple[list, list]:
    """เรียงตาม dependency ของ FK แต่ **จัดกลุ่มตามโซนให้อ่านง่าย**

    ใช้ Kahn's algorithm โดยเลือกตารางที่ ``พร้อมสร้าง`` ตัวที่โซนมาก่อนเสมอ (C → A → B)
    ผลลัพธ์จึงเป็นบล็อกโซนต่อเนื่องเท่าที่ dependency ยอมให้ ไม่สลับไปมาแบบ topological ล้วน
    """
    by_table = {table_of(s): (t, s) for t, s in creates}
    deps = {tbl: {d for d in fks_of(s) if d in by_table and d != tbl} for tbl, (t, s) in by_table.items()}
    ordered: list[str] = []
    problems: list[str] = []
    remaining = dict(deps)
    while remaining:
        ready = [t for t, d in remaining.items() if not (d - set(ordered))]
        if not ready:
            problems.append(f"FK วนกันเอง แยกลำดับไม่ได้: {sorted(remaining)}")
            ordered.extend(sorted(remaining))
            break
        # โซนก่อน แล้วค่อยชื่อ — ได้ผลลัพธ์เดิมทุกครั้ง (deterministic)
        ready.sort(key=lambda t: (ZONE_RANK.get(zone_of(by_table[t][0]), 9), t))
        pick = ready[0]
        ordered.append(pick)
        remaining.pop(pick)
    return [by_table[t] for t in ordered], problems


def validate(data: dict, ordered: list) -> list[str]:
    bad: list[str] = []
    own = {table_of(s) for _, s in data["creates"]}
    for _, s in data["creates"]:
        tbl = table_of(s)
        if not tbl.startswith("sgi_"):
            bad.append(f"CREATE TABLE {tbl} ไม่ได้ขึ้นต้นด้วย sgi_ — สคริปต์นี้ต้องสร้างเฉพาะตารางใหม่ของ SGI")
        for ref in fks_of(s):
            if ref not in own:
                bad.append(f"{tbl} มี FK ชี้ไป {ref} ซึ่งไม่ได้อยู่ในชุดที่สคริปต์สร้าง — จะไปแตะตารางระบบเดิม")
        if "PRIMARY KEY" not in strip_comments(s).upper():
            bad.append(f"{tbl} ไม่มี PRIMARY KEY")
    for _, s in data["alters"]:
        if not table_of(s).startswith("sgi_"):
            bad.append(f"ALTER TABLE {table_of(s)} แตะตารางที่ไม่ใช่ของ SGI")
    for _, s in data["indexes"]:
        m = re.search(r"\bON\s+(\w+)", strip_comments(s), re.I)
        if m and not m.group(1).startswith("sgi_"):
            bad.append(f"CREATE INDEX บนตาราง {m.group(1)} ซึ่งไม่ใช่ของ SGI")
    seen_pos = {table_of(s): i for i, (_, s) in enumerate(ordered)}
    for i, (_, s) in enumerate(ordered):
        for ref in fks_of(s):
            if ref in seen_pos and ref != table_of(s) and seen_pos[ref] > i:
                bad.append(f"ลำดับผิด: {table_of(s)} ถูกสร้างก่อน {ref} ที่มันอ้างถึง")
    return bad


def build() -> tuple[Path, Path, list[str]]:
    data = collect()
    ordered, problems = order_creates(data["creates"])
    problems += validate(data, ordered)

    tables = [table_of(s) for _, s in ordered]
    zones: dict[str, list[str]] = {}
    for t, s in ordered:
        zones.setdefault(zone_of(t), []).append(table_of(s))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    L: list[str] = []
    a = L.append

    a("-- =====================================================================")
    a("--  SGI — สร้างตารางใหม่ 3 โซน (A / B / C) ลงฐานข้อมูลของระบบ SBP เดิม")
    a("-- =====================================================================")
    a("--  สร้างอัตโนมัติจาก tools/build_sgi_schema_sql.py")
    a("--  ต้นฉบับ DDL: build_lldd_documents.database_ddl_sections()  (แหล่งเดียวกับเอกสาร LLDD-Database)")
    a("--  ⚠️ ห้ามแก้ไฟล์นี้ด้วยมือ — แก้ที่ต้นฉบับแล้วรันสคริปต์ใหม่")
    a("--")
    a(f"--  ตารางที่สร้าง : {len(tables)} ตาราง"
      f"  (โซน A {len(zones.get('A', []))} · โซน B {len(zones.get('B', []))} · โซน C {len(zones.get('C', []))})")
    a(f"--  index         : {len(data['indexes'])}")
    a(f"--  FK เพิ่มภายหลัง: {len(data['alters'])}  (ALTER สำหรับ FK ข้ามโซน)")
    a(f"--  schema ปลายทาง: {TARGET_SCHEMA}")
    a("--")
    a("--  ความปลอดภัย")
    a("--    * ทุกคำสั่งแตะเฉพาะตารางที่ขึ้นต้นด้วย sgi_ เท่านั้น")
    a("--    * ไม่มี DROP / TRUNCATE / ALTER ตารางของระบบเดิมแม้แต่คำสั่งเดียว")
    a("--    * FK ทุกเส้นชี้เข้าในกลุ่ม sgi_ ด้วยกันเอง — ตรวจอัตโนมัติตอน generate")
    a("--    * ตารางของระบบเดิมที่ SGI ใช้ (fcs_qssi_score · store · common_code · mas_param ·")
    a("--      business_user · email_template · sps_store.workflow_*) ถูก **อ่านอย่างเดียว** ไม่ถูกแตะที่นี่")
    a("--    * ทั้งไฟล์อยู่ใน transaction เดียว — ล้มกลางทางจะ rollback ทั้งหมด")
    a("-- =====================================================================")
    a("")
    a("\\set ON_ERROR_STOP on")
    a("")
    a("BEGIN;")
    a("")
    a(f"SET search_path TO {TARGET_SCHEMA};")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- PREFLIGHT — หยุดทันทีถ้าสภาพแวดล้อมไม่พร้อม")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE existing_count integer;")
    a("BEGIN")
    a("    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata")
    a(f"                   WHERE schema_name = '{TARGET_SCHEMA}') THEN")
    a(f"        RAISE EXCEPTION 'ไม่พบ schema {TARGET_SCHEMA} — ต่อผิดฐานข้อมูลหรือเปล่า';")
    a("    END IF;")
    a("")
    a("    SELECT count(*) INTO existing_count")
    a("      FROM information_schema.tables")
    a(f"     WHERE table_schema = '{TARGET_SCHEMA}' AND table_name LIKE 'sgi\\_%';")
    a("    IF existing_count > 0 THEN")
    a("        RAISE EXCEPTION 'มีตาราง sgi_ อยู่แล้ว % ตาราง — สคริปต์นี้สำหรับติดตั้งครั้งแรกเท่านั้น "
      "(ถ้าต้องการติดตั้งใหม่ ให้รัน sgi_schema_rollback.sql ก่อน)', existing_count;")
    a("    END IF;")
    a("END $$;")
    a("")

    current_zone = None
    for title, stmt in ordered:
        z = zone_of(title)
        if z != current_zone:
            current_zone = z
            a("")
            a("-- =====================================================================")
            a(f"-- โซน {z} — {title.split('—', 1)[-1].strip()}")
            a(f"--   ตารางในโซนนี้: {', '.join(zones.get(z, []))}")
            a("-- =====================================================================")
            a("")
        a(stmt.strip() + ";")
        a("")

    if data["alters"]:
        a("")
        a("-- =====================================================================")
        a("-- FK ข้ามโซน — เพิ่มหลังสร้างตารางครบทั้งสองฝั่งแล้ว")
        a("-- =====================================================================")
        a("")
        for _, stmt in data["alters"]:
            a(stmt.strip() + ";")
            a("")

    a("")
    a("-- =====================================================================")
    a(f"-- INDEX และ UNIQUE บางส่วน ({len(data['indexes'])} รายการ)")
    a("-- =====================================================================")
    a("")
    for _, stmt in data["indexes"]:
        a(stmt.strip() + ";")
        a("")

    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ตรวจผลก่อน COMMIT — จำนวนต้องตรงตามที่ประกาศไว้หัวไฟล์")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE t integer; i integer;")
    a("BEGIN")
    a("    SELECT count(*) INTO t FROM information_schema.tables")
    a(f"     WHERE table_schema = '{TARGET_SCHEMA}' AND table_name LIKE 'sgi\\_%';")
    a("    SELECT count(*) INTO i FROM pg_indexes")
    a(f"     WHERE schemaname = '{TARGET_SCHEMA}' AND indexname LIKE 'idx\\_%';")
    a(f"    IF t <> {len(tables)} THEN")
    a(f"        RAISE EXCEPTION 'สร้างตารางได้ % ตาราง แต่ต้องได้ {len(tables)}', t;")
    a("    END IF;")
    a("    RAISE NOTICE 'OK: ตาราง sgi_ = % · index idx_ = %', t, i;")
    a("END $$;")
    a("")
    a("COMMIT;")
    a("")
    a("-- ตรวจด้วยตาอีกชั้นหลัง COMMIT:")
    a("--   SELECT table_name FROM information_schema.tables")
    a(f"--    WHERE table_schema = '{TARGET_SCHEMA}' AND table_name LIKE 'sgi\\_%' ORDER BY 1;")

    main_path = OUT_DIR / "sgi_schema.sql"
    main_path.write_text("\n".join(L) + "\n", encoding="utf-8")

    # ----------------------------------------------------------- rollback
    R: list[str] = []
    r = R.append
    r("-- =====================================================================")
    r("--  ROLLBACK — ลบตารางใหม่ของ SGI ทั้งหมด")
    r("-- =====================================================================")
    r("--  ⚠️ ใช้กับ dev/uat เท่านั้น — คำสั่งนี้ลบข้อมูลทิ้งถาวร")
    r("--  ลบเฉพาะตารางที่ขึ้นต้นด้วย sgi_ ที่สคริปต์ sgi_schema.sql สร้างไว้")
    r("--  ไม่แตะตารางของระบบ SBP เดิมแม้แต่ตารางเดียว")
    r("--")
    r("--  🔴 สิ่งที่สคริปต์นี้ **ไม่ได้ลบ** (ตั้งใจ — เป็นตารางของระบบเดิม)")
    r(f"--     common_code_type {len(SGI_CODE_TYPES)} แถว (code_type LIKE 'SGI/_%')")
    r(f"--     common_code   {len(SGI_DECISIONS) + len(SGI_DOC_STATUSES) + len(SGI_APPROVE_LIMITS)} แถว (code_type LIKE 'SGI/_%')")
    r(f"--     mas_param     {len(MAS_PARAMS)} แถว (param_name LIKE 'SGI/_%')")
    r(f"--     email_template {len(EMAIL_TEMPLATES)} แถว (create_by = '{SEED_OWNER}')")
    r("--")
    r("--  ⚠️ **กับดักที่ต้องรู้** — sgi_seed_data.sql ใช้ INSERT ... WHERE NOT EXISTS")
    r("--     ถ้าแก้ค่า seed (เช่น เกณฑ์ใน mas_param) แล้วติดตั้งใหม่ **ค่าเก่าจะค้างอยู่**")
    r("--     เพราะแถวยังอยู่ seed จึงข้ามไป · ต้องลบแถวเก่าด้วยมือก่อน แล้วค่อยรัน seed ใหม่")
    r("--")
    r("--  คำสั่งล้างแถวเหล่านี้ (dev/uat เท่านั้น · ไม่รันอัตโนมัติ — ลอก 4 บรรทัดนี้ไปรันเอง)")
    r("--  ⚠️ ลบ common_code ก่อน common_code_type เสมอ — ทะเบียน type ต้องหายทีหลังค่าที่อ้างมัน")
    r("--     DELETE FROM sps_store.common_code      WHERE code_type  LIKE 'SGI/_%' ESCAPE '/';")
    r("--     DELETE FROM sps_store.common_code_type WHERE code_type  LIKE 'SGI/_%' ESCAPE '/';")
    r("--     DELETE FROM sps_store.mas_param        WHERE param_name LIKE 'SGI/_%' ESCAPE '/';")
    r(f"--     DELETE FROM sps_store.email_template   WHERE create_by  = '{SEED_OWNER}';")
    r("-- =====================================================================")
    r("")
    r("\\set ON_ERROR_STOP on")
    r("")
    r("BEGIN;")
    r(f"SET search_path TO {TARGET_SCHEMA};")
    r("")
    for t in reversed(tables):
        r(f"DROP TABLE IF EXISTS {t} CASCADE;")
    r("")
    r("COMMIT;")
    rollback_path = OUT_DIR / "sgi_schema_rollback.sql"
    rollback_path.write_text("\n".join(R) + "\n", encoding="utf-8")

    return main_path, rollback_path, problems




# ===========================================================================
# สคริปต์ที่ 2 — INSERT ข้อมูลตั้งต้นที่ระบบต้องมีก่อนใช้งานจริง
# ===========================================================================
# แบ่ง 2 กลุ่มชัดเจน เพราะระดับความเสี่ยงต่างกันมาก
#   กลุ่มที่ 1  ตาราง sgi_* ของเราเอง          — ปลอดภัย ไม่กระทบใคร
#   กลุ่มที่ 2  ตารางของระบบ SBP เดิม          — **เพิ่มแถวเท่านั้น** ห้าม UPDATE/DELETE ของเดิม
#              (common_code · mas_param · email_template)
# ทุกคำสั่งเป็น INSERT ... WHERE NOT EXISTS จึงรันซ้ำได้โดยไม่เกิดแถวซ้ำ
# และไม่ใช้ ON CONFLICT เพราะยังยืนยัน unique constraint ของตารางระบบเดิมไม่ได้
# ---------------------------------------------------------------------------
SEED_LOCK_CLASS = 861000   # namespace เดียวกับ SgiJobLockService
SEED_LOCK_KEY = 1          # 1 = การติดตั้ง seed ของ SGI
SEED_OWNER = "SGI-SETUP"   # 🔴 2026-09-16 — ให้ตรงกับที่ติดตั้งในฐาน dev จริง


def _sq(v: str) -> str:
    """escape ค่าเป็น SQL string literal"""
    return "'" + str(v).replace("'", "''") + "'"


def read_competitors() -> list[tuple[str, str, str, str]]:
    """11 แบรนด์คู่แข่ง — อ่านสดจาก k2-competitors.html (หน้าจอที่คัดลอกจาก K2 เดิม)"""
    text = (ROOT / "k2-competitors.html").read_text(encoding="utf-8")
    rows = re.findall(r"\['(\d{2})',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\]", text)
    return [(c, th, en, rm) for c, th, en, rm in rows]


def read_factors() -> list[tuple[str, str, str]]:
    """ปัจจัยภายนอก — อ่านสดจากตารางในหน้า k2-factors.html"""
    text = (ROOT / "k2-factors.html").read_text(encoding="utf-8")
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", text, re.S):
        tds = [re.sub(r"<[^>]+>", "", c).strip()
               for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) >= 4 and re.match(r"^F\d{3}$", tds[1]):
            out.append((tds[1], tds[2], tds[3]))
    return out


# ผลการพิจารณา 7 ค่า — ข้อความไทย verbatim จาก SRS/SDD ห้ามแก้คำ
SGI_DECISIONS = [
    ("เห็นควรชดเชย", "APPROVE"),
    ("เห็นควรไม่ชดเชย", "REJECT"),
    ("หยุดชดเชยประกันรายได้", "REJECT"),
    ("ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "PENDING"),
    ("ส่งเจ้าหน้าที่ SBP DSA", "PENDING"),
    ("ส่งกลับฝ่าย SBP DSA", "PENDING"),
    ("คำนวณเงินชดเชยเรียบร้อย", "PENDING"),
]

# สถานะเอกสาร 6 ค่า — มติ 2026-09-13 (DECISIONS ข้อ 2.31)
# รหัสเป็นของ SGI เอง · sps_store.workflow_status ของ engine มีแค่ status_id (integer) + status_name
# จึงใช้เป็นแหล่ง lookup ของรหัส 2 ตัวอักษรไม่ได้ — เก็บที่ common_code แบบเดียวกับ SGI_DECISION
# ข้อความไทยเป็น verbatim จาก workflow_status_document.md **ห้ามแก้คำ**
SGI_DOC_STATUSES = [
    ("06", "รอฝ่าย SBP DSA ดำเนินการ"),
    ("08", "รอเจ้าหน้าที่ SBP DSA ดำเนินการ"),
    ("01", "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ"),
    ("02", "รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ"),
    ("03", "รอผู้บริหารสำนักบริหาร SBP ดำเนินการ"),
    ("99", "เสร็จสิ้นดำเนินการ"),
]

# ทะเบียน code type ของ SGI — **ต้อง INSERT ก่อนแถวใน common_code เสมอ**
# `sps_store.common_code_type` เป็น PK บน `code_type` และมีของจริงอยู่ 378 แถว
# ถ้าลง `common_code` โดยไม่มีทะเบียน type หน้าจอ/สคริปต์ที่ไล่จาก type จะมองไม่เห็นค่าของ SGI เลย
# (ที่มา: `SBP/db-schema-sps_store.md` · `LLDD-BE-Integration-SBP-Platform` §5.5.2)
SGI_CODE_TYPES = [
    ("SGI_DECISION",     "ผลการพิจารณาเอกสารประกันรายได้"),
    ("SGI_DOC_STATUS",   "สถานะเอกสารประกันรายได้"),
    ("SGI_APPROVE_LIMIT", "วงเงินอนุมัติของระบบประกันรายได้"),
]

# วงเงินอนุมัติ
# 🔴 แก้ 2026-09-16 — **ยึดของที่ติดตั้งในฐาน dev จริง** (มติผู้ใช้)
#    เอกสาร `LLDD-BE-Integration-SBP-Platform` §5.5.2 เขียน contract ว่า code_value = 'THRESHOLD'
#    แต่ฐาน dev ถูก seed ไปแล้วเมื่อ 2026-08-27 (เจ้าของ SGI-SETUP) ด้วย **code_value = '100000'**
#    ถ้า seed ของเราใช้ 'THRESHOLD' → `WHERE NOT EXISTS` จะไม่เจอแถวเดิม แล้ว **insert เพิ่มเป็นแถวที่สอง**
#    ผลคือ SGI_APPROVE_LIMIT มี 2 แถว active แล้วฝั่งที่อ่านเลือกไม่ถูกว่าตัวไหนจริง
# ⚠️ `code_name` ถือ**ตัวเลข** — ฝั่งที่อ่านต้องแปลงเป็นตัวเลข และ fail-fast เมื่อไม่มีค่า/มีหลายแถว/แปลงไม่ได้
SGI_APPROVE_LIMITS = [
    ("100000", "100000",
     "วงเงินอนุมัติเกณฑ์เดียว — ต่ำกว่านี้จบที่ GM (02) · ตั้งแต่นี้ขึ้นไปส่ง AVP (03) · มติประชุม 2026-08-18"),
]

# ค่าคงที่ธุรกิจที่โค้ดต้องอ่าน (แทนตาราง system_configs ที่ถูกตัดออก)
MAS_PARAMS = [
    # 🔴 `SGI_APPROVE_LIMIT` **ย้ายออกไปอยู่ common_code แล้ว 2026-09-15**
    #    เอกสารกำหนดแหล่งเดียวไว้ที่ `common_code` มาตั้งแต่ต้น
    #    (`database.md` ตาราง "ใครเป็นเจ้าของค่า" · `LLDD-BE-Integration-SBP-Platform` §5.5.2
    #     ระบุ contract เป๊ะ: code_value = 'THRESHOLD' · code_name = '100000')
    #    แต่ seed กลับใส่ลง `mas_param` — ถ้าปล่อยไว้จะมีสองแหล่งที่ขัดกันได้
    #    และ `GET /sgi/lookup/workflow-sections` ออกแบบให้อ่านจาก common_code
    ("SGI_IMPACT_RADIUS_BKK", "1",
     "รัศมีกระทบ กทม./ปริมณฑล (กิโลเมตร)"),
    ("SGI_IMPACT_RADIUS_UPC", "2",
     "รัศมีกระทบต่างจังหวัด (กิโลเมตร)"),
    ("SGI_SALES_DAYS_MIN", "60",
     "จำนวนวันทำการขั้นต่ำที่ต้องมีข้อมูลยอดขาย — ไม่ครบขึ้นธงแดงและเข้าเงื่อนไข pre-accept"),
    ("SGI_GROWTH_RATE_MAX", "-10",
     "เกณฑ์ผลต่างอัตราเติบโต (%) — ต้องน้อยกว่าหรือเท่ากับค่านี้จึงเข้าข่ายชดเชย"),
    ("SGI_OUTLIER_SALES_DIFF", "50",
     "เกณฑ์ outlier ของยอดขายรายวัน — |sales_diff| (หน่วย **เปอร์เซ็นต์**) ตั้งแต่ค่านี้ขึ้นไป · "
     "⚠️ แก้คำอธิบาย 2026-09-13: วัน outlier **ไม่ได้ถูกตัดออก** จากการคำนวณ growth "
     "แต่ถูกแทนด้วย 0 โดยตัวหารยังนับอยู่ (ดู ImportJdbc สูตร AVG ของ Job 5)"),
    # ── ค่าคงที่ธุรกิจของ Job 6 — ระบบเดิมเก็บใน ApplicationResources.properties ──
    #    ทั้งสามตัวเป็นค่าที่ธุรกิจขอเปลี่ยนได้ จึงห้าม hardcode ในโค้ด (batchjob/JOB-06 หัวข้อ 12)
    ("SGI_STA_INIT_START_DAY", "7",
     "วันของเดือนที่เริ่มเปิดรอบชดเชยใหม่ส่ง STA (`dateStartInitToSTA` เดิม) — "
     "วันที่ 1 ถึงวันก่อนหน้านี้ Job 6 ยังซิงก์สถานะแต่ไม่เปิดรอบใหม่"),
    ("SGI_STA_NUM_WAIT_PAY", "3",
     "จำนวนงวดรอจ่าย (`numWaitPay` เดิม) — ใช้คำนวณงวด Statement ที่ STA จะตัดจ่าย"),
    ("SGI_QSSI_CATEGORIES", "8,9,12,1,10,16",
     "หมวดคะแนน QSSI ที่ต้องครบก่อนเปิดรอบชดเชยใหม่ (`categoryQssi` เดิม) — "
     "ต้องครบทั้ง 6 หมวดจากงวด max เดียวกัน ในกรอบ 3 เดือน"),
    ("SGI_ZERO_AMOUNT_MAX_MONTHS", "3",
     "จำนวนเดือนสูงสุดที่ยอดชดเชยเป็น 0 ได้ติดกัน — เดือนถัดไปให้หยุดชดเชย"),
    ("SGI_PENDING_ACK_AGE_DAYS", "1",
     "อายุขั้นต่ำ (วัน) ที่ Job 10 ถือว่าข้อความขาออกค้างส่ง แล้วส่งอีเมลเตือน"),
    ("SGI_ALLOW_PENDING_DOWNLOAD", "N",
     "อนุญาตให้ดาวน์โหลดไฟล์แนบที่ scan_status = PENDING หรือไม่ (Y/N) — "
     "🔴 ตั้ง N ไว้ก่อนจนกว่าจะมี security sign-off (ข้อค้าง 2.10)"),
]

# ---------------------------------------------------------------------------
# email_template — ยึดรูปแบบจาก **แถวจริงในฐาน dev** ไม่ใช่รูปแบบที่เราคิดขึ้นเอง
# วัดจากช่วง id 1501010–1501044 = ชุด template ของระบบประกันรายได้เดิม 33 แถว (2026-09-16)
#
#   • ตัวแปรเป็น `${ชื่อ}` ไม่ใช่ `{ชื่อ}` — ของจริงใช้ ${} 193 จุด · {} เปล่าเพียง 5 จุด
#   • `sender` = **อีเมลผู้ส่ง** · `email_from` = **ชื่อที่แสดง** (สลับกับที่ชื่อคอลัมน์ชวนให้เข้าใจ)
#     คู่ที่ชุดประกันรายได้เดิมใช้ครบทั้ง 33 แถว: noreply@cpall.co.th / SBP Mall System
#   • `body_format` เป็น HTML เต็มฉบับเสมอ (126/126 แถวของระบบเดิมมีเนื้อหา ไม่มีแถวว่าง)
#     โครงเดิมคงไว้ทั้งหมดรวมทั้ง `<title>Untitled Document</title>` — ตามที่ผู้ใช้สั่งว่า
#     ส่วนที่เรายังไม่มีข้อมูลของตัวเองให้ยึดตาม data เดิมไปก่อน
#   • ตัวแปรที่ของเดิมมีอยู่แล้ว **ใช้ชื่อเดิม ห้ามตั้งใหม่**:
#     ${compCurrentUser} ${compStoreCode} ${compStoreName} ${branchTypeI} ${compLoopNo} ${link}
#     ที่เพิ่มใหม่เพราะระบบเดิมไม่มีแนวคิดนี้: ${docNo} ${ageDays} ${pendingCount}
#                                             ${newDocCount} ${jobName} ${runId} ${errorMessage}
# ⚠️ เนื้อความจริงยังต้องให้ทีมธุรกิจตรวจ — ชุดนี้คือโครงที่ "ส่งออกไปแล้วอ่านรู้เรื่อง"
#    ไม่ใช่ข้อความที่ผ่าน sign-off แล้ว
# ---------------------------------------------------------------------------
EMAIL_SENDER = "noreply@cpall.co.th"     # คอลัมน์ sender     = อีเมลผู้ส่ง
EMAIL_FROM = "SBP Mall System"           # คอลัมน์ email_from = ชื่อที่แสดง
EMAIL_LINK_LINE = "คลิก Link เพื่อดำเนินการประกันรายได้ ${link}"
EMAIL_STORE_LINE = ("สาขา ${compStoreCode}#${compStoreName} Type ${branchTypeI} "
                    "&nbsp;ครั้งที่ ${compLoopNo}")


def _email_body(topic: str, details: list[str], action: str, closing: str) -> str:
    """ประกอบ body_format ตามโครงเดียวกับ template ของระบบเดิมทุกบรรทัด"""
    detail_html = "".join(f"{line}<br />\n" for line in details)
    return (
        "<html>\n"
        "<head>\n"
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
        "<title>Untitled Document</title>\n"
        "</head>\n"
        "<body>\n"
        "<p>เรียน ${compCurrentUser}</p>\n"
        f"<div >เรื่อง &nbsp;{topic} &nbsp;<br />\n"
        f"{detail_html}"
        "<br />\n"
        f"{action}</div>\n"
        "<br>\n"
        f"<div>{closing}<br />\n"
        "ขอบคุณค่ะ</div>\n"
        "</body>\n"
        "</html>"
    )


_DO = "แจ้งเพื่อโปรดดำเนินการ"      # ปิดท้ายแบบที่ template เดิมใช้กับงานที่ต้องลงมือ
_FYI = "แจ้งเพื่อทราบ"               # ปิดท้ายแบบแจ้งให้ทราบ
_CHECK = "แจ้งเพื่อโปรดตรวจสอบ"      # ปิดท้ายของอีเมลฝั่งระบบ (ไม่มีปุ่มให้กด)

# (code, ชื่อ, subject_format, body_format)
EMAIL_TEMPLATES = [
    ("EM-01", "SGI - เอกสารเปลี่ยนสถานะ",
     "[ประกันรายได้] เอกสาร ${docNo} รอท่านดำเนินการ",
     _email_body("พิจารณาดำเนินการประกันรายได้",
                 ["เอกสารเลขที่ ${docNo}", EMAIL_STORE_LINE],
                 EMAIL_LINK_LINE, _DO)),
    ("EM-02", "SGI - จบ workflow",
     "[ประกันรายได้] เอกสาร ${docNo} เสร็จสิ้นดำเนินการ",
     _email_body("แจ้งผลการพิจารณาประกันรายได้ (เสร็จสิ้นกระบวนการ)",
                 ["เอกสารเลขที่ ${docNo}", EMAIL_STORE_LINE],
                 EMAIL_LINK_LINE, _FYI)),
    ("EM-03", "SGI - ถูกส่งกลับ",
     "[ประกันรายได้] เอกสาร ${docNo} ถูกส่งกลับให้แก้ไข",
     _email_body("เอกสารประกันรายได้ถูกส่งกลับให้แก้ไข",
                 ["เอกสารเลขที่ ${docNo}", EMAIL_STORE_LINE],
                 EMAIL_LINK_LINE, _DO)),
    ("EM-04", "SGI - เตือนงานค้างรายสัปดาห์",
     "[ประกันรายได้] สรุปงานค้างของท่าน ประจำสัปดาห์",
     _email_body("สรุปเอกสารประกันรายได้ที่รอท่านดำเนินการ ประจำสัปดาห์",
                 ["จำนวนเอกสารที่รอดำเนินการ ${pendingCount} ฉบับ"],
                 EMAIL_LINK_LINE, _DO)),
    ("EM-05", "SGI - Escalation งานค้าง",
     "[ประกันรายได้] แจ้งงานค้างเกินกำหนด ${ageDays} วัน",
     _email_body("มีเอกสารรอท่านดำเนินการพิจารณาประกันรายได้มาแล้ว ${ageDays} วัน "
                 "หากครบ 60 วันเอกสารจะถูกยกเลิก",
                 ["จำนวนเอกสารที่รอดำเนินการ ${pendingCount} ฉบับ"],
                 EMAIL_LINK_LINE, _DO)),
    ("EM-06", "SGI - สรุปเปิด workflow ราย DV",
     "[ประกันรายได้] สรุปเอกสารที่เปิดใหม่ ประจำวัน",
     _email_body("สรุปเอกสารประกันรายได้ที่เปิดใหม่ ประจำวัน",
                 ["จำนวนเอกสารที่เปิดใหม่ ${newDocCount} ฉบับ"],
                 EMAIL_LINK_LINE, _FYI)),
    ("EM-07", "SGI - Batch job จบด้วย Error",
     "[ประกันรายได้] batch job ${jobName} ทำงานไม่สำเร็จ",
     _email_body("batch job ${jobName} ของระบบประกันรายได้ทำงานไม่สำเร็จ",
                 ["รหัสการรัน (runId) ${runId}", "ข้อความจากระบบ ${errorMessage}"],
                 "โปรดตรวจสอบ application log ของ job รอบดังกล่าว", _CHECK)),
    ("EM-08", "SGI - ข้อความขาออกค้างส่ง",
     "[ประกันรายได้] มีข้อความค้างส่งเกิน ${ageDays} วัน",
     _email_body("มีข้อความขาออกของระบบประกันรายได้ค้างส่งเกิน ${ageDays} วัน",
                 ["จำนวนข้อความที่ค้างส่ง ${pendingCount} รายการ"],
                 "โปรดตรวจสอบสถานะ publisher confirm ของคิวขาออก", _CHECK)),
]


def build_seed() -> Path:
    comps = read_competitors()
    factors = read_factors()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    L: list[str] = []
    a = L.append

    a("-- =====================================================================")
    a("--  SGI — ข้อมูลตั้งต้นที่ต้องมีก่อนเปิดใช้งาน (seed / master / common)")
    a("-- =====================================================================")
    a("--  สร้างอัตโนมัติจาก tools/build_sgi_schema_sql.py")
    a("--  ⚠️ ห้ามแก้ไฟล์นี้ด้วยมือ — แก้ที่ต้นทางแล้ว generate ใหม่")
    a("--  ต้องรัน sgi_schema.sql ให้เสร็จก่อนเสมอ")
    a("--")
    a("--  แบ่ง 2 กลุ่มตามระดับความเสี่ยง")
    a(f"--    ส่วนที่ 1 — ตาราง sgi_* ของเราเอง  ({len(comps)} แบรนด์คู่แข่ง · {len(factors)} ปัจจัยภายนอก · ตัวนับเลขเอกสาร)")
    # 🔴 แก้ 2026-09-15 — เดิมนับเฉพาะ SGI_DECISIONS ทำให้หัวไฟล์บอก "7 แถว"
    #    ทั้งที่ลง common_code จริง 13 แถว (ตก SGI_DOC_STATUSES ไป 6 แถว)
    #    คนอ่านหัวไฟล์เพื่อรู้ว่าจะมีอะไรเข้าตารางของระบบเดิมบ้าง — นับผิดคือบอกผิด
    a(f"--    ส่วนที่ 2 — ตารางของระบบ SBP เดิม  "
      f"(common_code {len(SGI_DECISIONS) + len(SGI_DOC_STATUSES)} แถว "
      f"= SGI_DECISION {len(SGI_DECISIONS)} + SGI_DOC_STATUS {len(SGI_DOC_STATUSES)} · "
      f"mas_param {len(MAS_PARAMS)} แถว · email_template {len(EMAIL_TEMPLATES)} แถว)")
    a("--")
    a("--  ความปลอดภัยของส่วนที่ 2")
    a("--    * **INSERT อย่างเดียว** ไม่มี UPDATE / DELETE / TRUNCATE แถวเดิมของระบบเดิมแม้แต่คำสั่งเดียว")
    a("--    * ทุกคำสั่งเป็น INSERT ... WHERE NOT EXISTS — รันซ้ำได้ ไม่เกิดแถวซ้ำ ไม่ทับของเดิม")
    a("--    * ใช้ค่า code_type / param_name ที่ขึ้นต้นด้วย SGI_ เท่านั้น จึงไม่ชนกับ key ของระบบเดิม")
    a(f"--    * ทุกแถวประทับ create_user/create_by = '{SEED_OWNER}' เพื่อให้ย้อนกลับมาลบได้แม่นยำ")
    a("-- =====================================================================")
    a("")
    a("\\set ON_ERROR_STOP on")
    a("")
    a("BEGIN;")
    a("")
    a(f"SET search_path TO {TARGET_SCHEMA};")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- 🔴 DEPLOYMENT LOCK — กัน seed สองรอบรันทับกัน")
    a("-- ---------------------------------------------------------------------")
    a("--  `INSERT ... WHERE NOT EXISTS` กันซ้ำได้เฉพาะเมื่อรัน**ทีละรอบ**")
    a("--  ถ้าสอง session รันพร้อมกัน ต่างฝ่ายต่างไม่เห็นแถวที่อีกฝ่ายยังไม่ commit (READ COMMITTED)")
    a("--  → ได้แถวซ้ำทั้งคู่ · พิสูจน์กับ PostgreSQL 16 จริงแล้ว 2026-09-16 (ได้ 2 แถวที่ควรมี 1)")
    a("--")
    a("--  ⚠️ ใช้ ON CONFLICT แทนไม่ได้ — `common_code` / `mas_param` ของระบบเดิม **ไม่มี unique constraint**")
    a("--     และเป็นตารางของทีมอื่น เราเพิ่ม constraint เองไม่ได้ตามกติกาโครงการ")
    a("--  advisory lock จึงเป็นทางเดียวที่กันได้โดยไม่แตะโครงสร้างของระบบเดิม")
    a("--  ปลดอัตโนมัติตอน COMMIT/ROLLBACK (xact) — ไม่มีทางค้างแม้ script ตาย")
    a(f"SELECT pg_advisory_xact_lock({SEED_LOCK_CLASS}, {SEED_LOCK_KEY});")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- PREFLIGHT — ต้องมีตารางของ SGI แล้ว และต้องมีตารางของระบบเดิมที่จะเพิ่มข้อมูลลงไป")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("BEGIN")
    a("    IF NOT EXISTS (SELECT 1 FROM information_schema.tables")
    a(f"                   WHERE table_schema = '{TARGET_SCHEMA}' AND table_name = 'sgi_competitors') THEN")
    a("        RAISE EXCEPTION 'ยังไม่มีตารางของ SGI — ต้องรัน sgi_schema.sql ก่อน';")
    a("    END IF;")
    a("    IF NOT EXISTS (SELECT 1 FROM information_schema.tables")
    a(f"                   WHERE table_schema = '{TARGET_SCHEMA}' AND table_name = 'common_code') THEN")
    a("        RAISE EXCEPTION 'ไม่พบตาราง common_code ของระบบเดิม — ต่อผิดฐานข้อมูลหรือเปล่า';")
    a("    END IF;")
    a("    IF NOT EXISTS (SELECT 1 FROM information_schema.tables")
    a(f"                   WHERE table_schema = '{TARGET_SCHEMA}' AND table_name = 'common_code_type') THEN")
    a("        RAISE EXCEPTION 'ไม่พบตาราง common_code_type — ต้องลงทะเบียน code type ก่อนลงค่าใน common_code';")
    a("    END IF;")
    a("END $$;")
    a("")

    # ---------------------------------------------------------- ส่วนที่ 1
    a("")
    a("-- =====================================================================")
    a("-- ส่วนที่ 1 — ตารางของ SGI เอง (ปลอดภัย ไม่กระทบระบบเดิม)")
    a("-- =====================================================================")
    a("")
    a(f"-- 1.1 master แบรนด์คู่แข่ง {len(comps)} รายการ (รหัส 01-{comps[-1][0]}) — ตรงตามหน้าจอ K2 เดิม")
    a("--     อ่านสดจาก k2-competitors.html ตอน generate จึงไม่มีทางไม่ตรงกับหน้าจอ")
    for code, th, en, remark in comps:
        a(f"INSERT INTO sgi_competitors (competitor_code, name_th, name_en, remark, is_active)")
        a(f"SELECT {_sq(code)}, {_sq(th)}, {_sq(en)}, "
          f"{_sq(remark) if remark else 'NULL'}, TRUE")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM sgi_competitors WHERE competitor_code = {_sq(code)});")
    a("")
    a(f"-- 1.2 master ปัจจัยภายนอก {len(factors)} รายการ")
    for code, name, remark in factors:
        a(f"INSERT INTO sgi_external_factors (factor_code, factor_name, factor_remark, is_active)")
        a(f"SELECT {_sq(code)}, {_sq(name)}, {_sq(remark) if remark else 'NULL'}, TRUE")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM sgi_external_factors WHERE factor_code = {_sq(code)});")
    a("")
    a("-- 1.3 ตัวนับเลขเอกสารของปีปัจจุบัน (ปี ค.ศ. · เริ่มที่ 0 = ยังไม่ออกเลขใด)")
    a("--     ถ้าไม่มีแถวนี้ การออกเลขเอกสารใบแรกของปีจะล้ม")
    a("INSERT INTO sgi_document_running_numbers (year, last_running_no, updated_by)")
    a(f"SELECT EXTRACT(YEAR FROM CURRENT_DATE)::smallint, 0, {_sq(SEED_OWNER)}")
    a(" WHERE NOT EXISTS (SELECT 1 FROM sgi_document_running_numbers")
    a("                    WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)::smallint);")
    a("")

    # ---------------------------------------------------------- ส่วนที่ 2
    a("")
    a("-- =====================================================================")
    a("-- ส่วนที่ 2 — ตารางของระบบ SBP เดิม (เพิ่มแถวเท่านั้น ห้ามแตะของเดิม)")
    a("-- =====================================================================")
    a("")
    a(f"-- 2.0 common_code_type — ทะเบียน code type ของ SGI {len(SGI_CODE_TYPES)} ตัว")
    a("--     🔴 **ต้องมาก่อน 2.1/2.1b/2.1c เสมอ** — `common_code_type` เป็น PK บน code_type")
    a("--     ถ้าลง common_code โดยไม่มีทะเบียน type หน้าจอ/สคริปต์ที่ไล่จาก type จะมองไม่เห็นค่าของ SGI")
    for code_type, type_name in SGI_CODE_TYPES:
        a("INSERT INTO common_code_type (code_type, code_type_name, active_flag, create_user, create_date)")
        a(f"SELECT {_sq(code_type)}, {_sq(type_name)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM common_code_type WHERE code_type = {_sq(code_type)});")
    a("")
    a(f"-- 2.1 common_code · code_type = 'SGI_DECISION' — ผลการพิจารณา {len(SGI_DECISIONS)} ค่า")
    a("--     ข้อความไทยเป็น verbatim จาก SRS/SDD **ห้ามแก้คำ** เพราะหน้าจอเทียบข้อความตรงตัว")
    a("--     (มติ DP-9 2026-08-10 ย้ายจากตาราง decisions มาไว้ที่ common_code ของระบบเดิม)")
    for i, (label, category) in enumerate(SGI_DECISIONS, start=1):
        a("INSERT INTO common_code (code_type, seq_no, code_value, code_name, active_flag, create_user, create_date)")
        a(f"SELECT 'SGI_DECISION', {i}, {_sq(category)}, {_sq(label)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM common_code")
        a(f"                    WHERE code_type = 'SGI_DECISION' AND code_name = {_sq(label)});")
    a("")
    a(f"-- 2.1b common_code · code_type = 'SGI_DOC_STATUS' — สถานะเอกสาร {len(SGI_DOC_STATUSES)} ค่า")
    a("--     รหัสเป็นของ SGI เอง (มติ 2026-09-13 ข้อ 2.31) — sps_store.workflow_status ของ engine")
    a("--     มีแค่ status_id (integer) + status_name จึงใช้เป็นแหล่ง lookup ของรหัสไม่ได้")
    a("--     ข้อความไทยเป็น verbatim จาก workflow_status_document.md **ห้ามแก้คำ**")
    for i, (code, label) in enumerate(SGI_DOC_STATUSES, start=1):
        a("INSERT INTO common_code (code_type, seq_no, code_value, code_name, active_flag, create_user, create_date)")
        a(f"SELECT 'SGI_DOC_STATUS', {i}, {_sq(code)}, {_sq(label)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM common_code")
        a(f"                    WHERE code_type = 'SGI_DOC_STATUS' AND code_value = {_sq(code)});")
    a("")
    a(f"-- 2.1c common_code · code_type = 'SGI_APPROVE_LIMIT' — วงเงินอนุมัติ {len(SGI_APPROVE_LIMITS)} ค่า")
    a("--     🔴 ย้ายมาจาก mas_param เมื่อ 2026-09-15 — เอกสารกำหนดแหล่งเดียวไว้ที่ common_code")
    a("--     contract: code_value = '100000' · code_name = ตัวเลขวงเงิน — **ยึดของที่ติดตั้งในฐาน dev จริง**")
    a("--     (เอกสาร LLDD §5.5.2 เดิมเขียน 'THRESHOLD' ซึ่งไม่ตรงกับแถวที่ seed ไปเมื่อ 2026-08-27)")
    a("--     ⚠️ ฝั่งที่อ่านต้องแปลง code_name เป็นตัวเลข และ fail-fast เมื่อไม่มีค่า/มีหลายแถว active")
    for i, (code_value, amount, desc) in enumerate(SGI_APPROVE_LIMITS, start=1):
        a(f"--     {desc}")
        a("INSERT INTO common_code (code_type, seq_no, code_value, code_name, active_flag, create_user, create_date)")
        a(f"SELECT 'SGI_APPROVE_LIMIT', {i}, {_sq(code_value)}, {_sq(amount)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM common_code")
        a(f"                    WHERE code_type = 'SGI_APPROVE_LIMIT' AND code_value = {_sq(code_value)});")
    a("")
    a(f"-- 2.2 mas_param — ค่าคงที่ธุรกิจ {len(MAS_PARAMS)} ตัว (แทนตาราง system_configs ที่ถูกตัดออก)")
    a("--     ทุก key ขึ้นต้นด้วย SGI_ จึงไม่ชนกับค่าของระบบเดิม")
    for name, value, desc in MAS_PARAMS:
        a("INSERT INTO mas_param (param_name, param_value, description, is_config, active_flag, create_by, create_date)")
        a(f"SELECT {_sq(name)}, {_sq(value)}, {_sq(desc)}, 'Y', 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM mas_param WHERE param_name = {_sq(name)});")
    a("")
    a(f"-- 2.3 email_template — {len(EMAIL_TEMPLATES)} template ของ SGI")
    a("--     รูปแบบทุกช่องยึดจากแถวจริงของระบบเดิม (ช่วง id 1501010–1501044 = template ประกันรายได้เดิม)")
    a("--     ตัวแปรเป็น ${ชื่อ} ไม่ใช่ {ชื่อ} · sender = อีเมลผู้ส่ง · email_from = ชื่อที่แสดง")
    a("--     ⚠️ เนื้อความยังไม่ผ่าน business sign-off — เป็นโครงที่อ่านรู้เรื่องไว้ก่อน")
    a("--        การแก้ subject/body จริงทำที่หน้าจอของระบบ SBP เดิม (SGI อ่านอย่างเดียว)")
    a("--     ⚠️ **ห้ามพึ่ง sequence ของตารางนี้** — วัดบนฐาน dev จริง 2026-09-16 พบว่า")
    a("--        `email_template_email_template_id_seq.last_value` = 1201012 แต่ `max(email_template_id)`")
    a("--        = 1501044 · id ถูกแจกเป็นช่วงตามทีม/migration (1–6007 · 1101001–1101006 ·")
    a("--        1201001–1201013 · 1501010–1501044) ไม่ได้มาจาก nextval() · ปล่อยให้ default ทำงาน")
    a("--        จะได้ 1201012 ซึ่งมีแถวอยู่แล้ว → duplicate key ทั้ง transaction ล้ม")
    a("--        จึงคำนวณ id เองจาก max()+1 · advisory lock ที่หัวไฟล์กันสองเครื่องคำนวณพร้อมกัน")
    a("--        **ไม่แตะ sequence ของระบบเดิม** (เป็น object ของทีมอื่น — setval เป็นสิทธิ์ของเจ้าของ)")
    a("--     ⚠️ `email_template_id` จึงรู้ค่าล่วงหน้าไม่ได้ · หลังรันสคริปต์นี้")
    a("--        ต้องนำ id ที่ได้ไปผูกกับ `workflow_route.email_id` ของ @srm/glb-workflow")
    a("--        **ซึ่งเป็นตารางของ engine — ต้องให้ทีมเจ้าของ lib เป็นผู้ตั้ง ไม่ทำที่นี่**")
    for code, name, subject, body in EMAIL_TEMPLATES:
        full = f"{code} {name}"
        a("INSERT INTO email_template (email_template_id, email_template_name, email_template_desc, subject_format,")
        a("                            body_format, sender, email_from, active_flag, create_by, create_date)")
        a("SELECT (SELECT COALESCE(max(email_template_id), 0) + 1 FROM email_template),")
        a(f"       {_sq(full)}, {_sq(name)}, {_sq(subject)},")
        a(f"       {_sq(body)},")
        a(f"       {_sq(EMAIL_SENDER)}, {_sq(EMAIL_FROM)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM email_template WHERE email_template_name = {_sq(full)});")
    a("")

    # ------------------------------------------------------------ ตรวจผล
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ตรวจผลก่อน COMMIT")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE c integer; f integer; d integer; s integer; p integer; e integer;")
    a("BEGIN")
    a("    SELECT count(*) INTO c FROM sgi_competitors;")
    a("    SELECT count(*) INTO f FROM sgi_external_factors;")
    a("    SELECT count(*) INTO d FROM common_code   WHERE code_type = 'SGI_DECISION';")
    a("    SELECT count(*) INTO s FROM common_code   WHERE code_type = 'SGI_DOC_STATUS';")
    a("    SELECT count(*) INTO p FROM mas_param     WHERE param_name LIKE 'SGI\\_%';")
    a("    SELECT count(*) INTO e FROM email_template WHERE email_template_name LIKE 'EM-0%';")
    a(f"    IF c < {len(comps)} OR f < {len(factors)} OR d < {len(SGI_DECISIONS)}"
      f" OR s < {len(SGI_DOC_STATUSES)} OR p < {len(MAS_PARAMS)} OR e < {len(EMAIL_TEMPLATES)} THEN")
    a("        RAISE EXCEPTION 'seed ไม่ครบ: competitors=% factors=% decisions=% docStatuses=% params=% templates=%', c, f, d, s, p, e;")
    a("    END IF;")
    a("    RAISE NOTICE 'OK: competitors=% factors=% decisions=% docStatuses=% params=% templates=%', c, f, d, s, p, e;")
    a("END $$;")
    a("")
    a("COMMIT;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ถอน seed เฉพาะส่วนที่ 2 (ตารางระบบเดิม) — ใช้เมื่อต้องการยกเลิกการติดตั้ง")
    a(f"--   ลบได้ปลอดภัยเพราะทุกแถวประทับ '{SEED_OWNER}' ไว้")
    a("--   DELETE FROM common_code    WHERE code_type IN ('SGI_DECISION','SGI_DOC_STATUS')   "
      f"AND create_user = {_sq(SEED_OWNER)};")
    a("--   DELETE FROM mas_param      WHERE param_name LIKE 'SGI\\_%'     "
      f"AND create_by   = {_sq(SEED_OWNER)};")
    a("--   DELETE FROM email_template WHERE email_template_name LIKE 'EM-0%' "
      f"AND create_by   = {_sq(SEED_OWNER)};")
    a("-- ---------------------------------------------------------------------")

    path = OUT_DIR / "sgi_seed_data.sql"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def main() -> int:
    main_path, rollback_path, problems = build()
    seed_path = build_seed()
    data = collect()
    ordered, _ = order_creates(data["creates"])
    print(f"{main_path.relative_to(ROOT)} · {len(ordered)} ตาราง · "
          f"{len(data['indexes'])} index · {len(data['alters'])} ALTER")
    print(f"{rollback_path.relative_to(ROOT)}")
    print(f"{seed_path.relative_to(ROOT)} · คู่แข่ง {len(read_competitors())} · ปัจจัย {len(read_factors())} · decision {len(SGI_DECISIONS)} · param {len(MAS_PARAMS)} · template {len(EMAIL_TEMPLATES)}")
    if data["skipped"]:
        print(f"  ข้ามคำสั่งที่ไม่ใช่ DDL {len(data['skipped'])} รายการ (ตัวอย่าง DML ในเอกสาร):")
        for t, snip in data["skipped"]:
            print(f"    - [{t.split('—')[0].strip()}] {snip}")
    if problems:
        print("  ❌ พบปัญหา:")
        for p in problems:
            print(f"    - {p}")
        return 1
    print("  ✅ ตรวจแล้ว: ทุกคำสั่งแตะเฉพาะตาราง sgi_ · FK ไม่ออกนอกกลุ่ม · ลำดับ dependency ถูกต้อง · ทุกตารางมี PK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
