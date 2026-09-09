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
SEED_OWNER = "SGI-INSTALL"


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

# ค่าคงที่ธุรกิจที่โค้ดต้องอ่าน (แทนตาราง system_configs ที่ถูกตัดออก)
MAS_PARAMS = [
    ("SGI_APPROVE_LIMIT", "100000",
     "วงเงินอนุมัติเกณฑ์เดียว — ต่ำกว่านี้จบที่ GM (02) · ตั้งแต่นี้ขึ้นไปส่ง AVP (03) · มติประชุม 2026-08-18"),
    ("SGI_IMPACT_RADIUS_BKK_KM", "1",
     "รัศมีกระทบ กทม./ปริมณฑล (กิโลเมตร)"),
    ("SGI_IMPACT_RADIUS_UPC_KM", "2",
     "รัศมีกระทบต่างจังหวัด (กิโลเมตร)"),
    ("SGI_SALES_DATA_MIN_DAYS", "60",
     "จำนวนวันทำการขั้นต่ำที่ต้องมีข้อมูลยอดขาย — ไม่ครบขึ้นธงแดงและเข้าเงื่อนไข pre-accept"),
    ("SGI_GROWTH_RATE_THRESHOLD", "-10",
     "เกณฑ์ผลต่างอัตราเติบโต (%) — ต้องน้อยกว่าหรือเท่ากับค่านี้จึงเข้าข่ายชดเชย"),
    ("SGI_OUTLIER_SALES_DIFF", "50",
     "เกณฑ์ outlier ของยอดขายรายวัน (|sales_diff| ตั้งแต่ค่านี้ขึ้นไป) — ตัดออกจากการคำนวณ growth"),
    ("SGI_ZERO_AMOUNT_MAX_MONTHS", "3",
     "จำนวนเดือนสูงสุดที่ยอดชดเชยเป็น 0 ได้ติดกัน — เดือนถัดไปให้หยุดชดเชย"),
    ("SGI_PENDING_ACK_AGE_DAYS", "1",
     "อายุขั้นต่ำ (วัน) ที่ Job 10 ถือว่าข้อความขาออกค้างส่ง แล้วส่งอีเมลเตือน"),
    ("SGI_ALLOW_PENDING_DOWNLOAD", "N",
     "อนุญาตให้ดาวน์โหลดไฟล์แนบที่ scan_status = PENDING หรือไม่ (Y/N) — "
     "🔴 ตั้ง N ไว้ก่อนจนกว่าจะมี security sign-off (ข้อค้าง 2.10)"),
]

EMAIL_TEMPLATES = [
    ("EM-01", "SGI - เอกสารเปลี่ยนสถานะ", "[ประกันรายได้] เอกสาร {docNo} รอท่านดำเนินการ"),
    ("EM-02", "SGI - จบ workflow", "[ประกันรายได้] เอกสาร {docNo} เสร็จสิ้นดำเนินการ"),
    ("EM-03", "SGI - ถูกส่งกลับ", "[ประกันรายได้] เอกสาร {docNo} ถูกส่งกลับให้แก้ไข"),
    ("EM-04", "SGI - เตือนงานค้างรายสัปดาห์", "[ประกันรายได้] สรุปงานค้างของท่าน ประจำสัปดาห์"),
    ("EM-05", "SGI - Escalation งานค้าง", "[ประกันรายได้] แจ้งงานค้างเกินกำหนด {ageDays} วัน"),
    ("EM-06", "SGI - สรุปเปิด workflow ราย DV", "[ประกันรายได้] สรุปเอกสารที่เปิดใหม่ ประจำวัน"),
    ("EM-07", "SGI - Batch job จบด้วย Error", "[ประกันรายได้] batch job {jobName} ทำงานไม่สำเร็จ"),
    ("EM-08", "SGI - ข้อความขาออกค้างส่ง", "[ประกันรายได้] มีข้อความค้างส่งเกิน {ageDays} วัน"),
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
    a(f"--    ส่วนที่ 2 — ตารางของระบบ SBP เดิม  (common_code {len(SGI_DECISIONS)} แถว · "
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
    a(f"-- 2.1 common_code · code_type = 'SGI_DECISION' — ผลการพิจารณา {len(SGI_DECISIONS)} ค่า")
    a("--     ข้อความไทยเป็น verbatim จาก SRS/SDD **ห้ามแก้คำ** เพราะหน้าจอเทียบข้อความตรงตัว")
    a("--     (มติ DP-9 2026-08-10 ย้ายจากตาราง decisions มาไว้ที่ common_code ของระบบเดิม)")
    for i, (label, category) in enumerate(SGI_DECISIONS, start=1):
        a("INSERT INTO common_code (code_type, seq_no, code_value, code_name, active_flag, create_user, create_date)")
        a(f"SELECT 'SGI_DECISION', {i}, {_sq(category)}, {_sq(label)}, 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM common_code")
        a(f"                    WHERE code_type = 'SGI_DECISION' AND code_name = {_sq(label)});")
    a("")
    a(f"-- 2.2 mas_param — ค่าคงที่ธุรกิจ {len(MAS_PARAMS)} ตัว (แทนตาราง system_configs ที่ถูกตัดออก)")
    a("--     ทุก key ขึ้นต้นด้วย SGI_ จึงไม่ชนกับค่าของระบบเดิม")
    for name, value, desc in MAS_PARAMS:
        a("INSERT INTO mas_param (param_name, param_value, description, is_config, active_flag, create_by, create_date)")
        a(f"SELECT {_sq(name)}, {_sq(value)}, {_sq(desc)}, 'Y', 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM mas_param WHERE param_name = {_sq(name)});")
    a("")
    a(f"-- 2.3 email_template — {len(EMAIL_TEMPLATES)} template ของ SGI")
    a("--     ⚠️ body_format ปล่อยเป็นโครงเปล่าไว้ก่อน — เนื้อความจริงให้ทีมธุรกิจกรอกผ่านระบบเดิม")
    a("--     ⚠️ `email_template_id` มาจาก sequence จึงรู้ค่าล่วงหน้าไม่ได้ · หลังรันสคริปต์นี้")
    a("--        ต้องนำ id ที่ได้ไปผูกกับ `workflow_route.email_id` ของ @srm/glb-workflow")
    a("--        **ซึ่งเป็นตารางของ engine — ต้องให้ทีมเจ้าของ lib เป็นผู้ตั้ง ไม่ทำที่นี่**")
    for code, name, subject in EMAIL_TEMPLATES:
        full = f"{code} {name}"
        a("INSERT INTO email_template (email_template_name, email_template_desc, subject_format, body_format,")
        a("                            active_flag, create_by, create_date)")
        a(f"SELECT {_sq(full)}, {_sq(name)}, {_sq(subject)}, '', 'Y', {_sq(SEED_OWNER)}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM email_template WHERE email_template_name = {_sq(full)});")
    a("")

    # ------------------------------------------------------------ ตรวจผล
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ตรวจผลก่อน COMMIT")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE c integer; f integer; d integer; p integer; e integer;")
    a("BEGIN")
    a("    SELECT count(*) INTO c FROM sgi_competitors;")
    a("    SELECT count(*) INTO f FROM sgi_external_factors;")
    a("    SELECT count(*) INTO d FROM common_code   WHERE code_type = 'SGI_DECISION';")
    a("    SELECT count(*) INTO p FROM mas_param     WHERE param_name LIKE 'SGI\\_%';")
    a("    SELECT count(*) INTO e FROM email_template WHERE email_template_name LIKE 'EM-0%';")
    a(f"    IF c < {len(comps)} OR f < {len(factors)} OR d < {len(SGI_DECISIONS)}"
      f" OR p < {len(MAS_PARAMS)} OR e < {len(EMAIL_TEMPLATES)} THEN")
    a("        RAISE EXCEPTION 'seed ไม่ครบ: competitors=% factors=% decisions=% params=% templates=%', c, f, d, p, e;")
    a("    END IF;")
    a("    RAISE NOTICE 'OK: competitors=% factors=% decisions=% params=% templates=%', c, f, d, p, e;")
    a("END $$;")
    a("")
    a("COMMIT;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ถอน seed เฉพาะส่วนที่ 2 (ตารางระบบเดิม) — ใช้เมื่อต้องการยกเลิกการติดตั้ง")
    a(f"--   ลบได้ปลอดภัยเพราะทุกแถวประทับ '{SEED_OWNER}' ไว้")
    a("--   DELETE FROM common_code    WHERE code_type = 'SGI_DECISION'   "
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
