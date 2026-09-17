#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้าง SQL ลงนิยาม workflow ของ SGI ลงตารางของ `@srm/glb-workflow`

    python3 tools/build_sgi_workflow_sql.py   →  output/sql/sgi_workflow_definition.sql

ที่มาของนิยาม
    `workflow_status_document.md` — ตาราง สถานะ × การดำเนินการ × ผู้ดำเนินการถัดไป × email
    (15 แถวข้อมูล · **แหล่งความจริงเดียว** ไฟล์นี้อ่านสดทุกครั้งที่ generate)
    โครงตารางของ engine จาก `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` ชีต `sample data`

⚠️ ตาราง `sps_store.workflow_*` เป็น **ตารางของ engine (ระบบเดิม)** — สคริปต์ผลลัพธ์จึง
   * `INSERT` อย่างเดียว · ไม่มี UPDATE/DELETE/DDL
   * ระบุ id เองทุกตัว **ไม่พึ่ง nextval** — วัดบนฐาน dev จริงแล้วพบว่า sequence ตามหลังข้อมูล
     (`workflow_workflow_id_seq.last_value = 1` แต่ `max(workflow_id) = 6`) เหมือนกรณี `email_template`
   * ใช้ `WHERE NOT EXISTS` ทุกคำสั่ง — รันซ้ำไม่เพิ่มแถว
   * มี preflight ที่ **หยุดทันที** ถ้ายังไม่เติมรหัสกลุ่มผู้อนุมัติจริง

🔴 สคริปต์นี้ **ยังใช้จริงไม่ได้จนกว่าจะเติม `GROUP_MAP`** — ดูหัวข้อ "ค้างอยู่" ท้ายไฟล์ผลลัพธ์
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workflow_status_document.md"
OUT = ROOT / "output" / "sql" / "sgi_workflow_definition.sql"

WORKFLOW_ID = 10          # 6 และ 9 ถูกใช้แล้วบน dev
VERSION_ID = 10
SEED_OWNER = "SGI-SETUP"

# state/status ใช้รูปแบบเดียวกับของเดิม: <workflow_id> + เลขลำดับ 5 หลัก
def sid(n: int) -> int:
    return WORKFLOW_ID * 100000 + n

# (section_code, state_id, state_name, status_name — **verbatim จาก SGI_DOC_STATUS ห้ามแก้คำ**)
STATES = [
    ("06", sid(1), "06-sbp-dsa", "รอฝ่าย SBP DSA ดำเนินการ"),
    ("08", sid(2), "08-sbp-dsa-officer", "รอเจ้าหน้าที่ SBP DSA ดำเนินการ"),
    ("01", sid(3), "01-business-promotion", "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ"),
    ("02", sid(4), "02-gm-business-promotion", "รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ"),
    ("03", sid(5), "03-avp-sbp", "รอผู้บริหารสำนักบริหาร SBP ดำเนินการ"),
    ("99", sid(99099), "99-finish", "เสร็จสิ้นดำเนินการ"),
]
STATE_OF = {s[0]: s[1] for s in STATES}
STATUS_OF = {s[0]: s[1] for s in STATES}      # status_id เท่ากับ state_id ตามแบบของ v6/v9

# กลุ่มผู้อนุมัติ 1 กลุ่มต่อ 1 section · group_id เริ่มที่ 100 (ของเดิมใช้ 1–4 · sequence อยู่ที่ 36)
GROUPS = [(100 + i, code, name) for i, (code, _sid, _sn, name) in enumerate(STATES[:5])]
GROUP_OF = {g[1]: g[0] for g in GROUPS}

# 🔴 รหัสกลุ่มจริงใน business_user.group_id ของแต่ละ section — **ยังไม่รู้ ต้องให้ทีมเจ้าของระบบเติม**
GROUP_MAP: dict[str, list[str]] = {"06": [], "08": [], "01": [], "02": [], "03": []}

# ---------------------------------------------------------------------
# เกณฑ์วงเงินอนุมัติ — **อ่านสดจาก common_code ตอนติดตั้ง ไม่ hardcode ลง SQL**
#   (แก้ 2026-09-17 หลัง review · เดิมฝัง 100000 ไว้ใน condition_json สองเส้น
#    ทำให้ถ้าธุรกิจแก้เกณฑ์ที่ common_code นิยาม workflow จะค้างค่าเก่าเงียบ ๆ)
#   แหล่งความจริง: common_code code_type = 'SGI_APPROVE_LIMIT' (มติ 2026-08-06)
# ---------------------------------------------------------------------
APPROVE_LIMIT_TYPE = "SGI_APPROVE_LIMIT"

# ---------------------------------------------------------------------
# 🔴 รูปแบบ `condition_json` — **เอกสารของ engine กับข้อมูลจริงในฐานไม่ตรงกัน**
#    (วัดบนฐาน dev 2026-09-17 · ยังไม่มีข้อสรุป — DECISIONS ข้อ 2.42)
#
#    เอกสาร `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` บรรทัด 98 เขียนว่า
#        object เดี่ยว `{"field","operator","value"}` · ตัวอย่าง value เป็น **ตัวเลข**
#        `{"field":"amount","operator":"<","value":1000}`
#    แต่แถวจริงใน `sps_store.workflow_route` เป็น
#        **array 16 แถว** `[{"field":"NextApproverStep","operator":"==","value":"602003"}]`
#        · object เดี่ยว 2 แถว · และ value เป็น **string ทั้ง 16 แถว** ไม่มีตัวเลขสักแถว
#
#    เลือก "object" ตามเอกสารไว้ก่อน เพราะ:
#      1. เป็น contract ที่เขียนเป็นลายลักษณ์อักษรของ lib
#      2. เงื่อนไขของเราเทียบ **จำนวนเงิน** ด้วย >= / < — เทียบแบบ string ให้ผลผิด
#         ('90000' > '100000' เป็นจริงถ้าเทียบแบบ string)
#    ⚠️ 16 แถวที่เป็น array ใช้ field `NextApproverStep`/`firstApproverStep` ซึ่งเป็น
#       routing ภายในของ engine เอง — อาจคนละเส้นทางโค้ดกับเงื่อนไขเชิงธุรกิจ
#    → **ต้องให้ทีม engine ยืนยันก่อน deploy** · ถ้าคำตอบคือ array ให้เปลี่ยนค่าเดียวตรงนี้
# ---------------------------------------------------------------------
CONDITION_SHAPE = "object"      # "object" (ตามเอกสาร) หรือ "array" (ตามข้อมูลจริง 16/18 แถว)
LIMIT_SQL = ("(SELECT code_value::numeric FROM common_code "
             f"WHERE code_type = '{APPROVE_LIMIT_TYPE}' AND coalesce(active_flag,'Y') = 'Y' "
             "ORDER BY seq_no LIMIT 1)")


def condition_sql(cond) -> str:
    """แปลง cond ของ ROUTES เป็น SQL ที่ใส่ใน condition_json"""
    if cond is None:
        return "NULL"
    if isinstance(cond, str) and cond.startswith("LIMIT"):
        op = cond[len("LIMIT"):]          # '>=' หรือ '<'
        obj = ("jsonb_build_object('field', 'compensateAmount', "
               f"'operator', '{op}', 'value', {LIMIT_SQL})")
        return f"jsonb_build_array({obj})" if CONDITION_SHAPE == "array" else obj
    if CONDITION_SHAPE == "array":
        return "jsonb_build_array(" + _sq(cond) + "::jsonb)"
    return _sq(cond) + "::jsonb"

# (from_section, event, seq, to_section, ปุ่ม/ผลการพิจารณา, email, condition_json)
ROUTES = [
    ("06", "submit",   1, "08", "ส่งเจ้าหน้าที่ SBP DSA", "EM-01",
     '{"field":"result","operator":"==","value":"ส่งเจ้าหน้าที่ SBP DSA"}'),
    ("06", "submit",   2, "01", "ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "EM-01",
     '{"field":"result","operator":"==","value":"ส่งหน่วยงานส่งเสริมธุรกิจ SBP"}'),
    ("06", "reject",   1, "99", "เห็นควรไม่ชดเชย", "EM-02", None),
    ("06", "cancel",   1, "99", "หยุดชดเชยประกันรายได้", "EM-02", None),
    ("08", "submit",   1, "06", "คำนวณเงินชดเชยเรียบร้อย", "EM-01", None),
    ("01", "approve",  1, "02", "เห็นควรชดเชย", "EM-01", None),
    ("01", "reject",   1, "99", "เห็นควรไม่ชดเชย", "EM-02", None),
    ("01", "sendback", 1, "06", "ส่งกลับฝ่าย SBP DSA", "EM-03", None),
    # 🔴 เกณฑ์วงเงิน **ห้าม hardcode** — แหล่งความจริงคือ common_code (SGI_APPROVE_LIMIT)
    #    ใส่ token LIMIT_SQL ไว้ แล้วตอน generate จะแทนด้วย subquery ที่อ่านค่าสดตอนติดตั้ง
    #    ถ้าธุรกิจเปลี่ยนเกณฑ์ใน common_code นิยาม route จะตามทันทีโดยไม่ต้อง generate ใหม่
    ("02", "approve",  1, "03", "เห็นควรชดเชย (≥ เกณฑ์วงเงิน)", "EM-01", "LIMIT>="),
    ("02", "approve",  2, "99", "เห็นควรชดเชย (< เกณฑ์วงเงิน)", "EM-02", "LIMIT<"),
    ("02", "reject",   1, "99", "เห็นควรไม่ชดเชย", "EM-02", None),
    ("02", "sendback", 1, "06", "ส่งกลับฝ่าย SBP DSA", "EM-03", None),
    ("03", "approve",  1, "99", "เห็นควรชดเชย", "EM-02", None),
    ("03", "reject",   1, "99", "เห็นควรไม่ชดเชย", "EM-02", None),
    ("03", "sendback", 1, "06", "ส่งกลับฝ่าย SBP DSA", "EM-03", None),
]

EMAIL_NAME = {
    "EM-01": "EM-01 SGI - เอกสารเปลี่ยนสถานะ",
    "EM-02": "EM-02 SGI - จบ workflow",
    "EM-03": "EM-03 SGI - ถูกส่งกลับ",
}


def _sq(v) -> str:
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def check_against_source() -> list[str]:
    """ตาราง transition ในโค้ดนี้ ต้องมีจำนวนแถวตรงกับ workflow_status_document.md"""
    bad = []
    if not SRC.exists():
        return [f"ไม่พบ {SRC.name} — แหล่งความจริงของ transition"]
    rows = [l for l in SRC.read_text(encoding="utf-8").split("\n")
            if l.startswith("|") and not l.startswith("|---") and "State No" not in l]
    data = [l for l in rows if not l.startswith("| - |")]        # ตัดแถว "สร้างเอกสาร"
    if len(data) != len(ROUTES):
        bad.append(f"workflow_status_document.md มี {len(data)} transition "
                   f"แต่ ROUTES ในตัว generator มี {len(ROUTES)} — ต้องตรงกัน")
    for code in ("06", "08", "01", "02", "03"):
        n_src = sum(1 for l in data if l.startswith(f"| {code} |"))
        n_own = sum(1 for r in ROUTES if r[0] == code)
        if n_src != n_own:
            bad.append(f"section {code}: เอกสารมี {n_src} transition · generator มี {n_own}")
    return bad


def build() -> str:
    L: list[str] = []
    a = L.append
    ready = all(GROUP_MAP.values())

    a("-- =====================================================================")
    a("--  นิยาม workflow ของระบบประกันรายได้ (SGI) สำหรับ @srm/glb-workflow")
    a("--  สร้างจาก tools/build_sgi_workflow_sql.py — **ห้ามแก้ไฟล์นี้ด้วยมือ**")
    a("-- ---------------------------------------------------------------------")
    a(f"--  workflow_id = {WORKFLOW_ID} · version_id = {VERSION_ID}")
    a(f"--  state/status {len(STATES)} ตัว · route {len(ROUTES)} เส้น · group {len(GROUPS)} กลุ่ม")
    a("--")
    a("--  แหล่งความจริงของ transition: `workflow_status_document.md` (อ่านสดตอน generate)")
    a("--  โครงตารางของ engine: `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` ชีต sample data")
    a("--")
    a("--  ⚠️ ตาราง workflow_* เป็นของ **engine (ระบบเดิม)** — ไฟล์นี้จึง INSERT อย่างเดียว")
    a("--     ไม่มี UPDATE / DELETE / DDL · ทุกคำสั่งมี WHERE NOT EXISTS (รันซ้ำไม่เพิ่มแถว)")
    a("--  🔴 **ระบุ id เองทุกตัว ไม่พึ่ง nextval** — วัดบนฐาน dev จริง 2026-09-16 พบว่า")
    a("--     workflow_workflow_id_seq.last_value = 1 แต่ max(workflow_id) = 6")
    a("--     sequence ตามหลังข้อมูลตัวเอง เหมือนกรณี email_template (ดู CLAUDE.md)")
    a("--")
    a("--  ทั้งไฟล์อยู่ในทรานแซกชันเดียว — ล้มกลางทาง = ไม่มีอะไรค้าง")
    a("-- =====================================================================")
    a("")
    a("\\set ON_ERROR_STOP on")
    a("")
    a("BEGIN;")
    a("SET search_path TO sps_store;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- advisory lock — กันสองคนติดตั้งนิยามพร้อมกัน (เพิ่ม 2026-09-17)")
    a("--   ตาราง workflow_* ไม่มี UNIQUE ครอบ (version_id, from_state_id, event, seq)")
    a("--   ถ้ารันซ้อนกัน WHERE NOT EXISTS ของทั้งสอง session จะเห็น \"ยังไม่มี\" พร้อมกัน")
    a("--   แล้วได้ route ซ้ำสองชุด · ล็อกนี้ปลดเองตอนจบทรานแซกชัน")
    a("-- ---------------------------------------------------------------------")
    a(f"SELECT pg_advisory_xact_lock({WORKFLOW_ID}, {VERSION_ID});")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- preflight")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE lim numeric;")
    a("BEGIN")
    a("    -- 🔴 id ชนของทีมอื่นไหม (เพิ่ม 2026-09-17 หลัง review)")
    a("    --    เดิมแค่ RAISE NOTICE แล้วปล่อยผ่าน · WHERE NOT EXISTS จะข้ามแถวที่ซ้ำเงียบ ๆ")
    a("    --    ผลคือได้นิยามครึ่งเดียวที่ชี้ไป workflow ของทีมอื่น — ต้อง fail-fast ทุก environment")
    a(f"    IF EXISTS (SELECT 1 FROM workflow WHERE workflow_id = {WORKFLOW_ID}")
    a(f"                 AND workflow_name <> 'ประกันรายได้ SBP (SGI)') THEN")
    a(f"        RAISE EXCEPTION 'workflow_id = {WORKFLOW_ID} ถูกใช้โดย workflow อื่นแล้ว (%) — "
      f"เลือก WORKFLOW_ID ใหม่ใน generator',")
    a(f"            (SELECT workflow_name FROM workflow WHERE workflow_id = {WORKFLOW_ID});")
    a("    END IF;")
    a(f"    IF EXISTS (SELECT 1 FROM workflow_version WHERE version_id = {VERSION_ID}")
    a(f"                 AND workflow_id <> {WORKFLOW_ID}) THEN")
    a(f"        RAISE EXCEPTION 'version_id = {VERSION_ID} เป็นของ workflow อื่นแล้ว — เลือก VERSION_ID ใหม่';")
    a("    END IF;")
    a(f"    IF EXISTS (SELECT 1 FROM workflow_state WHERE state_id BETWEEN {min(STATE_OF.values())}")
    a(f"                 AND {max(STATE_OF.values())} AND version_id <> {VERSION_ID}) THEN")
    a("        RAISE EXCEPTION 'ช่วง state_id ที่จะใช้ทับของ version อื่นแล้ว — เลือกช่วงใหม่';")
    a("    END IF;")
    a(f"    IF EXISTS (SELECT 1 FROM workflow_group WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]}")
    a(f"                 AND group_name NOT LIKE 'SGI %') THEN")
    a(f"        RAISE EXCEPTION 'ช่วง group_id {GROUPS[0][0]}–{GROUPS[-1][0]} ถูกใช้โดยกลุ่มอื่นแล้ว (%)',")
    a(f"            (SELECT string_agg(group_name, ', ') FROM workflow_group")
    a(f"              WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]} AND group_name NOT LIKE 'SGI %');")
    a("    END IF;")
    a("")
    a("    -- เกณฑ์วงเงินต้องมีใน common_code ก่อน ไม่งั้น condition_json ได้ value = NULL")
    a(f"    SELECT {LIMIT_SQL} INTO lim;")
    a("    IF lim IS NULL THEN")
    a(f"        RAISE EXCEPTION 'ยังไม่มีเกณฑ์วงเงินใน common_code ({APPROVE_LIMIT_TYPE}) — รัน sgi_seed_data.sql ก่อน';")
    a("    END IF;")
    a("    RAISE NOTICE 'เกณฑ์วงเงินที่จะใช้ในนิยาม route = %', lim;")
    a("    -- ทุก email template ที่ route อ้างถึง ต้องมีอยู่ก่อน ไม่งั้น email_id จะเป็น NULL เงียบ ๆ")
    for code in sorted(EMAIL_NAME):
        a(f"    IF NOT EXISTS (SELECT 1 FROM email_template WHERE email_template_name = {_sq(EMAIL_NAME[code])}) THEN")
        a(f"        RAISE EXCEPTION 'ยังไม่มี email template {code} — รัน sgi_seed_data.sql ก่อน';")
        a("    END IF;")
    if not ready:
        a("    RAISE EXCEPTION 'ยังไม่ได้เติมรหัสกลุ่มผู้อนุมัติจริง (GROUP_MAP) — ดูหัวข้อค้างอยู่ท้ายไฟล์';")
    a("END $$;")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- 1. workflow")
    a("-- ---------------------------------------------------------------------")
    a("INSERT INTO workflow (workflow_id, workflow_name, description, create_date)")
    a(f"SELECT {WORKFLOW_ID}, 'ประกันรายได้ SBP (SGI)', "
      f"'flow พิจารณาชดเชยรายได้ร้าน SP — 5 ขั้น 06→08→06→01→02→03', CURRENT_TIMESTAMP")
    a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow WHERE workflow_id = {WORKFLOW_ID});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a(f"-- 2. workflow_state — {len(STATES)} สถานะ")
    a("--    state_name เป็นรหัสภายใน · ชื่อที่ผู้ใช้เห็นอยู่ที่ workflow_status")
    a("-- ---------------------------------------------------------------------")
    for code, st, name, _label in STATES:
        a(f"INSERT INTO workflow_state (state_id, state_name, version_id, create_date)")
        a(f"SELECT {st}, {_sq(name)}, {VERSION_ID}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_state WHERE state_id = {st});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a(f"-- 3. workflow_status — {len(STATES)} สถานะ")
    a("--    🔴 status_name ต้อง **verbatim ตรงกับ common_code SGI_DOC_STATUS** ห้ามแก้คำ")
    a("--       (check_docs.py มีกฎดักความไม่ตรงกันระหว่างสองที่นี้)")
    a("-- ---------------------------------------------------------------------")
    for code, st, _name, label in STATES:
        a(f"INSERT INTO workflow_status (status_id, status_name, version_id, create_date)")
        a(f"SELECT {st}, {_sq(label)}, {VERSION_ID}, CURRENT_TIMESTAMP")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_status WHERE status_id = {st});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- 4. workflow_version")
    a("-- ---------------------------------------------------------------------")
    a("INSERT INTO workflow_version (version_id, workflow_id, initial_state_id, initial_status_id,")
    a("                              end_state_id, end_status_id, description, update_date,")
    a("                              url_main, url_param_mapping)")
    a(f"SELECT {VERSION_ID}, {WORKFLOW_ID}, {STATE_OF['06']}, {STATUS_OF['06']}, "
      f"{STATE_OF['99']}, {STATUS_OF['99']},")
    a("       'ประกันรายได้ SBP (SGI) — ขั้นแรกคือฝ่าย SBP DSA กดส่ง', CURRENT_TIMESTAMP,")
    a("       '/sgi/document', '{\"docNo\": {\"table\": \"sgi_compensation_documents\", \"column\": \"doc_no\"}}'")
    a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_version WHERE version_id = {VERSION_ID});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a(f"-- 5. workflow_group — 1 กลุ่มต่อ 1 ขั้น ({len(GROUPS)} กลุ่ม)")
    a("-- ---------------------------------------------------------------------")
    for gid, code, label in GROUPS:
        a(f"INSERT INTO workflow_group (group_id, group_name, approver_type)")
        a(f"SELECT {gid}, {_sq(f'SGI {code} — {label}')}, 'group'")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_group WHERE group_id = {gid});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- 6. workflow_group_map — ผูกกลุ่มกับ business_user.group_id ของจริง")
    a("-- ---------------------------------------------------------------------")
    if ready:
        n = 0
        for gid, code, _label in GROUPS:
            for key in GROUP_MAP[code]:
                n += 1
                a("INSERT INTO workflow_group_map (group_id, map_table, map_column, map_key)")
                a(f"SELECT {gid}, 'sps_store.business_user', 'group_id', {_sq(key)}")
                a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_group_map"
                  f" WHERE group_id = {gid} AND map_key = {_sq(key)});")
    else:
        a("-- 🔴 ยังเติมไม่ได้ — ไม่รู้ว่าแต่ละขั้นตรงกับ business_user.group_id ค่าไหน")
        a("--    ของเดิมบนฐาน dev ใช้รูปแบบนี้ (11 แถว):")
        a("--      INSERT INTO workflow_group_map (group_id, map_table, map_column, map_key)")
        a("--      VALUES (<group_id>, 'sps_store.business_user', 'group_id', '<เลขกลุ่มจริง>');")
        a("--    เติมค่าใน GROUP_MAP ของ tools/build_sgi_workflow_sql.py แล้ว generate ใหม่")
    a("")

    a("-- ---------------------------------------------------------------------")
    a(f"-- 7. workflow_route — {len(ROUTES)} เส้น (ตรงกับ workflow_status_document.md ทุกแถว)")
    a("--    email_id หาโดย lookup ชื่อ template — **ห้าม hardcode id** เพราะต่างกันทุก environment")
    a("-- ---------------------------------------------------------------------")
    for frm, event, seq, to, label, mail, cond in ROUTES:
        a(f"-- {frm} → {to} · {label}")
        a("INSERT INTO workflow_route (version_id, from_state_id, event, to_state_id, seq,")
        a("                            to_status_id, condition_json, approver_type, group_id, email_id)")
        gid = GROUP_OF.get(to)
        a(f"SELECT {VERSION_ID}, {STATE_OF[frm]}, {_sq(event)}, {STATE_OF[to]}, {seq},")
        a(f"       {STATUS_OF[to]}, {condition_sql(cond)}, "
          f"{'NULL' if gid is None else _sq('group')}, {gid if gid is not None else 'NULL'},")
        a(f"       (SELECT min(email_template_id) FROM email_template "
          f"WHERE email_template_name = {_sq(EMAIL_NAME[mail])})")
        a(f" WHERE NOT EXISTS (SELECT 1 FROM workflow_route WHERE version_id = {VERSION_ID}")
        a(f"                     AND from_state_id = {STATE_OF[frm]} AND event = {_sq(event)}"
          f" AND seq = {seq});")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ตรวจผลก่อน COMMIT")
    a("-- ---------------------------------------------------------------------")
    a("DO $$")
    a("DECLARE s integer; t integer; r integer; g integer; e integer; m integer; b integer;")
    a("BEGIN")
    a(f"    SELECT count(*) INTO s FROM workflow_state  WHERE version_id = {VERSION_ID};")
    a(f"    SELECT count(*) INTO t FROM workflow_status WHERE version_id = {VERSION_ID};")
    a(f"    SELECT count(*) INTO r FROM workflow_route  WHERE version_id = {VERSION_ID};")
    a(f"    SELECT count(*) INTO g FROM workflow_group  WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]};")
    a(f"    SELECT count(*) INTO e FROM workflow_route  WHERE version_id = {VERSION_ID} AND email_id IS NULL;")
    a(f"    IF s < {len(STATES)} OR t < {len(STATES)} OR r < {len(ROUTES)} OR g < {len(GROUPS)} THEN")
    a("        RAISE EXCEPTION 'นิยามไม่ครบ: states=% statuses=% routes=% groups=%', s, t, r, g;")
    a("    END IF;")
    a("    IF e > 0 THEN")
    a("        RAISE EXCEPTION '% route ยังไม่มี email_id — lookup ชื่อ template ไม่เจอ', e;")
    a("    END IF;")
    a("")
    a("    -- 🔴 group_map ต้องครบทุกกลุ่ม (เพิ่ม 2026-09-17 หลัง review)")
    a("    --    ไม่มี map = engine หาผู้อนุมัติไม่เจอ เอกสารจะค้างอยู่ที่ขั้นนั้นตลอดไป")
    a(f"    SELECT count(DISTINCT group_id) INTO m FROM workflow_group_map")
    a(f"      WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]};")
    a(f"    IF m < {len(GROUPS)} THEN")
    a(f"        RAISE EXCEPTION 'workflow_group_map ครบ % จาก {len(GROUPS)} กลุ่ม — "
      f"กลุ่มที่ไม่มี map จะหาผู้อนุมัติไม่เจอ', m;")
    a("    END IF;")
    a("")
    a("    -- condition_json ของเส้นที่ใช้เกณฑ์วงเงิน ต้องมี value เป็นตัวเลขจริง ไม่ใช่ null")
    a("    -- ⚠️ ตรวจ **เฉพาะเส้นเกณฑ์วงเงิน** (field = compensateAmount)")
    a("    --    เส้นอื่นมี value เป็นข้อความโดยตั้งใจ (ชื่อปุ่มผลการพิจารณา) — ไม่ใช่ความผิด")
    a(f"    SELECT count(*) INTO b FROM workflow_route WHERE version_id = {VERSION_ID}")
    if CONDITION_SHAPE == "array":
        a("      AND condition_json @> '[{\"field\":\"compensateAmount\"}]'::jsonb")
        a("      AND EXISTS (SELECT 1 FROM jsonb_array_elements(condition_json) e")
        a("                   WHERE e ->> 'field' = 'compensateAmount'")
        a("                     AND jsonb_typeof(e -> 'value') <> 'number');")
    else:
        a("      AND condition_json ->> 'field' = 'compensateAmount'")
        a("      AND jsonb_typeof(condition_json -> 'value') <> 'number';")
    a("    IF b > 0 THEN")
    a("        RAISE EXCEPTION '% route มี condition_json.value ที่ไม่ใช่ตัวเลข — "
      "อ่านเกณฑ์วงเงินจาก common_code ไม่สำเร็จ', b;")
    a("    END IF;")
    a("    RAISE NOTICE 'OK: states=% statuses=% routes=% groups=% group_map=%', s, t, r, g, m;")
    a("END $$;")
    a("")
    a("COMMIT;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ถอนนิยามนี้ (dev/uat เท่านั้น · ไม่รันอัตโนมัติ — ลอกไปรันเอง)")
    a("--   ⚠️ ลำดับสำคัญ: route → version → status/state → group_map → group → workflow")
    a(f"--   DELETE FROM sps_store.workflow_route      WHERE version_id = {VERSION_ID};")
    a(f"--   DELETE FROM sps_store.workflow_version    WHERE version_id = {VERSION_ID};")
    a(f"--   DELETE FROM sps_store.workflow_status     WHERE version_id = {VERSION_ID};")
    a(f"--   DELETE FROM sps_store.workflow_state      WHERE version_id = {VERSION_ID};")
    a(f"--   DELETE FROM sps_store.workflow_group_map  WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]};")
    a(f"--   DELETE FROM sps_store.workflow_group      WHERE group_id BETWEEN {GROUPS[0][0]} AND {GROUPS[-1][0]};")
    a(f"--   DELETE FROM sps_store.workflow            WHERE workflow_id = {WORKFLOW_ID};")
    a("-- ---------------------------------------------------------------------")
    a("")
    a("-- =====================================================================")
    a("-- 🔴 ค้างอยู่ — ต้องได้คำตอบก่อนรันจริง")
    a("-- =====================================================================")
    a("--  1. **รหัสกลุ่มผู้อนุมัติ** — แต่ละขั้น (06 · 08 · 01 · 02 · 03) ตรงกับ")
    a("--     `business_user.group_id` ค่าไหนบ้าง · ตอนนี้ GROUP_MAP ยังว่าง preflight จึงหยุดให้")
    a("--  2. **`condition_json` ที่ engine รองรับจริง** — สคริปต์นี้ใช้รูปแบบตามชีต sample data")
    a("--     (`{\"field\":…,\"operator\":…,\"value\":…}`) และอ่านค่าจาก `data_json` ของ transaction")
    a("--     ต้องยืนยันว่า engine เทียบ field ชื่อ `result` / `compensateAmount` ได้จริง")
    a("--  3. **สองเส้นทางจาก 06** (ส่ง 08 หรือ ส่ง 01) ใช้ event `submit` เหมือนกันแล้วแยกด้วย")
    a("--     condition บนค่า `result` — ถ้า engine ต้องการ event คนละชื่อ ต้องเพิ่มแถวใน")
    a("--     `workflow_event` ซึ่งเป็น **ตารางกลางไม่มี version_id** (กระทบทุก workflow)")
    a("--  4. **workflow_part / workflow_part_display** — ยังไม่ได้นิยาม (คุมว่าขั้นไหนแก้ส่วนไหนได้)")
    a("--  5. เจ้าของนิยามนี้คือ **ทีม @srm/glb-workflow** — ไฟล์นี้เป็นข้อเสนอให้ตรวจ ไม่ใช่ของที่ยิงเองได้")
    a("-- =====================================================================")
    return "\n".join(L) + "\n"


def main() -> int:
    bad = check_against_source()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = build()
    OUT.write_text(text, encoding="utf-8")
    forbidden = [k for k in ("UPDATE ", "DELETE FROM", "DROP ", "TRUNCATE", "ALTER ", "CREATE TABLE")
                 if any(k in l and not l.strip().startswith("--") for l in text.split("\n"))]
    print(f"เขียนแล้ว: {OUT.relative_to(ROOT)} · {text.count(chr(10))} บรรทัด")
    print(f"  state/status {len(STATES)} · route {len(ROUTES)} · group {len(GROUPS)}")
    print("  🔒 INSERT อย่างเดียว" if not forbidden else f"  ❌ พบคำสั่งต้องห้าม: {forbidden}")
    print("  ✅ จำนวน transition ตรงกับ workflow_status_document.md" if not bad
          else "\n".join("  ❌ " + b for b in bad))
    ready = all(GROUP_MAP.values())
    print("  🔴 GROUP_MAP ยังว่าง — preflight จะหยุดถ้าเอาไปรัน (ตั้งใจ)" if not ready
          else "  ✅ GROUP_MAP เติมครบแล้ว")
    return 1 if (bad or forbidden) else 0


if __name__ == "__main__":
    raise SystemExit(main())
