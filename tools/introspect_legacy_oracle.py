#!/usr/bin/env python3
"""
สกัดโครงสร้าง + ข้อมูลจริงจากฐาน Oracle ของระบบเดิม (As-Is) ออกมาเป็น 3 ไฟล์

    output/legacy-oracle/schema.sql   DDL ของตาราง FGI_* (คอลัมน์ · constraint · index)
    output/legacy-oracle/data.json    ข้อมูลเชิงสถิติที่ใช้ตอบข้อค้างของ LLDD (machine-readable)
    output/legacy-oracle/README.md    รายงานภาษาคน + ข้อสรุปต่อข้อค้างแต่ละข้อ

⚠️ credential อ่านจาก environment variable เท่านั้น — **ห้ามใส่ค่าจริงลงไฟล์นี้หรือไฟล์ผลลัพธ์**
    ORA_USER · ORA_PASSWORD · ORA_DSN ("host:1521/service" หรือ "host:1521:SID")

    ORA_USER=... ORA_PASSWORD=... ORA_DSN=... python3 tools/introspect_legacy_oracle.py

ทุกคำสั่งเป็น SELECT ล้วน — ไม่มี INSERT/UPDATE/DELETE/DDL แม้แต่คำสั่งเดียว
ผลลัพธ์ถูกใช้ต่อโดย tools/check_docs.py (กฎ #110) เพื่อเทียบกับสิ่งที่เอกสาร LLDD อ้างไว้
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import oracledb
except ImportError:  # pragma: no cover
    print("ต้องติดตั้ง oracledb ก่อน:  python3 -m pip install oracledb", file=sys.stderr)
    raise SystemExit(2)

OUT_DIR = Path(__file__).resolve().parent.parent / "output" / "legacy-oracle"

# ตารางที่สนใจ — อ่านชื่อจากโค้ด Java เดิมใน batchjob/fcsJar
TABLE_PREFIXES = ("FGI_",)
EXTRA_TABLES = ("MAS_STORE", "FR_STORE", "JURISTIC")

# คอลัมน์ที่ต้องรู้ "โดเมนจริง" เพราะ DDL ใหม่ใส่ CHECK constraint ไว้
# (table, column, เหตุผล/สิ่งที่ DDL ใหม่อ้างไว้)
DOMAIN_COLUMNS = [
    ("FGI_IMPACT_STORE", "FLAG_VERIFY", "sgi_fgi_impact_stores.verify_status CHECK IN ('W','P','N')"),
    ("FGI_IMPACT_STORE", "CREATE_BY", "sgi_fgi_impact_stores.created_by CHECK IN ('ALM','STA','USER')"),
    ("FGI_IMPACT_STORE", "UPDATE_BY", "sgi_fgi_impact_stores.updated_by CHECK IN ('ALM','STA','USER')"),
    ("FGI_IMPACT_STORE", "DISTANCE_UNIT", "แปลงเป็น distance_km — โค้ดรับ KM/M เท่านั้น"),
    ("FGI_IMPACT_STORE", "RADIUS_UNIT", "ไม่มีที่เก็บใน schema ใหม่"),
    ("FGI_IMPACT_STORE_ON_PROCESS", "FLAG_ACTION", "sgi_fgi_impact_processes.flag_action CHECK IN ('Y','W','N')"),
    ("FGI_IMPACT_STORE_ON_PROCESS", "DATASOURCE", "sgi_fgi_impact_processes.datasource — ALM/STA/PRO/REA (ไม่มี CHECK)"),
    ("FGI_IMPACT_STORE_SALES", "FLAG_VERIFY", "sgi_fgi_impact_sales_summaries.sales_status CHECK IN ('W','P','Y','N','E')"),
    ("FGI_IMPACT_STORE_COMPENSATE", "COMPENSATE_STATUS", "โดเมนของสถานะการจ่ายชดเชย"),
]

MAX_DISTINCT = 60          # โดเมนที่กว้างกว่านี้ถือว่าไม่ใช่ enum
SAMPLE_ROWS = 40


# --------------------------------------------------------------------------- utils
def _jsonable(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    return value


def fetch(cur, sql, params=None):
    cur.execute(sql, params or {})
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, (_jsonable(v) for v in row))) for row in cur.fetchall()]


def try_fetch(cur, sql, params=None):
    """คิวรีที่ตารางอาจไม่มี/ไม่มีสิทธิ์ — คืน error แทนที่จะล้มทั้งสคริปต์"""
    try:
        return fetch(cur, sql, params), None
    except Exception as exc:
        return [], str(exc).splitlines()[0]


# --------------------------------------------------------------------------- schema
def collect_schema(cur) -> dict:
    where = " OR ".join([f"table_name LIKE '{p}%'" for p in TABLE_PREFIXES])
    extra = ", ".join(f"'{t}'" for t in EXTRA_TABLES)
    tables = fetch(cur, f"""
        SELECT table_name FROM user_tables
         WHERE ({where}) OR table_name IN ({extra})
         ORDER BY table_name""")
    names = [t["TABLE_NAME"] for t in tables]

    columns = fetch(cur, f"""
        SELECT table_name, column_id, column_name, data_type, data_length,
               data_precision, data_scale, nullable, data_default
          FROM user_tab_columns
         WHERE ({where}) OR table_name IN ({extra})
         ORDER BY table_name, column_id""")

    constraints = fetch(cur, f"""
        SELECT c.table_name, c.constraint_name, c.constraint_type, c.search_condition_vc,
               c.r_constraint_name, cc.column_name, cc.position
          FROM user_constraints c
          JOIN user_cons_columns cc ON cc.constraint_name = c.constraint_name
         WHERE (c.table_name LIKE 'FGI_%' OR c.table_name IN ({extra}))
         ORDER BY c.table_name, c.constraint_name, cc.position""")

    indexes = fetch(cur, f"""
        SELECT i.table_name, i.index_name, i.uniqueness, ic.column_name, ic.column_position
          FROM user_indexes i
          JOIN user_ind_columns ic ON ic.index_name = i.index_name
         WHERE (i.table_name LIKE 'FGI_%' OR i.table_name IN ({extra}))
         ORDER BY i.table_name, i.index_name, ic.column_position""")

    return {"tables": names, "columns": columns, "constraints": constraints, "indexes": indexes}


def render_schema_sql(schema: dict) -> str:
    out = [
        "-- =====================================================================",
        "--  โครงสร้างจริงของฐาน Oracle ระบบเดิม (As-Is) — สกัดด้วย",
        "--  tools/introspect_legacy_oracle.py  · ห้ามแก้ด้วยมือ",
        "--",
        "--  ⚠️ ไฟล์นี้เป็น **ภาพของระบบเดิม** ไม่ใช่ DDL ที่จะติดตั้ง",
        "--     DDL ของระบบใหม่อยู่ที่ output/sql/sgi_schema.sql",
        "-- =====================================================================",
        "",
    ]
    by_table: dict[str, list[dict]] = {}
    for col in schema["columns"]:
        by_table.setdefault(col["TABLE_NAME"], []).append(col)

    cons_by_table: dict[str, list[dict]] = {}
    for con in schema["constraints"]:
        cons_by_table.setdefault(con["TABLE_NAME"], []).append(con)

    for table in schema["tables"]:
        cols = by_table.get(table, [])
        if not cols:
            continue
        out.append(f"CREATE TABLE {table} (")
        lines = []
        for col in cols:
            lines.append(f"    {col['COLUMN_NAME']:<30} {_type_of(col)}"
                         f"{'' if col['NULLABLE'] == 'Y' else ' NOT NULL'}"
                         f"{_default_of(col)}")
        # PK / UK จาก constraint
        pk = _grouped(cons_by_table.get(table, []), "P")
        uk = _grouped(cons_by_table.get(table, []), "U")
        for name, cols_ in pk.items():
            lines.append(f"    CONSTRAINT {name} PRIMARY KEY ({', '.join(cols_)})")
        for name, cols_ in uk.items():
            lines.append(f"    CONSTRAINT {name} UNIQUE ({', '.join(cols_)})")
        out.append(",\n".join(lines))
        out.append(");")
        for con in cons_by_table.get(table, []):
            if con["CONSTRAINT_TYPE"] == "C" and con.get("SEARCH_CONDITION_VC"):
                cond = str(con["SEARCH_CONDITION_VC"]).strip()
                if not re.fullmatch(r'"?\w+"?\s+IS\s+NOT\s+NULL', cond, re.I):
                    out.append(f"--   CHECK {con['CONSTRAINT_NAME']}: {cond}")
        out.append("")

    idx_by_name: dict[tuple[str, str, str], list[str]] = {}
    for idx in schema["indexes"]:
        key = (idx["TABLE_NAME"], idx["INDEX_NAME"], idx["UNIQUENESS"])
        idx_by_name.setdefault(key, []).append(idx["COLUMN_NAME"])
    if idx_by_name:
        out.append("-- ------------------------------------------------------------------ index")
        for (table, name, uniq), cols_ in sorted(idx_by_name.items()):
            kw = "UNIQUE INDEX" if uniq == "UNIQUE" else "INDEX"
            out.append(f"CREATE {kw} {name} ON {table}({', '.join(cols_)});")
    return "\n".join(out) + "\n"


def _grouped(cons: list[dict], ctype: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for con in cons:
        if con["CONSTRAINT_TYPE"] == ctype:
            out.setdefault(con["CONSTRAINT_NAME"], []).append(con["COLUMN_NAME"])
    return out


def _type_of(col: dict) -> str:
    dt = col["DATA_TYPE"]
    if dt in ("VARCHAR2", "CHAR", "NVARCHAR2"):
        return f"{dt}({col['DATA_LENGTH']})"
    if dt == "NUMBER":
        if col["DATA_PRECISION"] is None:
            return "NUMBER"
        return f"NUMBER({col['DATA_PRECISION']},{col['DATA_SCALE'] or 0})"
    return dt


def _default_of(col: dict) -> str:
    dflt = col.get("DATA_DEFAULT")
    return f" DEFAULT {str(dflt).strip()}" if dflt else ""


# --------------------------------------------------------------------------- data
def collect_data(cur, schema: dict) -> dict:
    data: dict = {"row_counts": {}, "domains": {}, "questions": {}, "errors": {}}

    for table in schema["tables"]:
        rows, err = try_fetch(cur, f"SELECT COUNT(*) AS c FROM {table}")
        if err:
            data["errors"][f"count:{table}"] = err
        else:
            data["row_counts"][table] = rows[0]["C"]

    known_cols = {(c["TABLE_NAME"], c["COLUMN_NAME"]) for c in schema["columns"]}
    for table, column, note in DOMAIN_COLUMNS:
        if (table, column) not in known_cols:
            data["errors"][f"domain:{table}.{column}"] = "ไม่มีคอลัมน์นี้ในฐานจริง"
            continue
        rows, err = try_fetch(cur, f"""
            SELECT {column} AS val, COUNT(*) AS c
              FROM {table} GROUP BY {column}
             ORDER BY COUNT(*) DESC FETCH FIRST {MAX_DISTINCT} ROWS ONLY""")
        if err:
            data["errors"][f"domain:{table}.{column}"] = err
            continue
        data["domains"][f"{table}.{column}"] = {
            "note": note,
            "values": {("<NULL>" if r["VAL"] is None else str(r["VAL"])): r["C"] for r in rows},
        }

    # ── คำถามที่ปิดข้อค้างของ LLDD โดยตรง ─────────────────────────────────
    q = data["questions"]

    # ข้อ 4.4 — PERIOD_YEAR ของวิว ALLMAP เป็น พ.ศ. หรือ ค.ศ.
    # FGI_IMPACT_STORE.YEAR คัดลอกตรงจาก PERIOD_YEAR (ImportStoreMapper.java:39)
    rows, err = try_fetch(cur, """
        SELECT year AS y, COUNT(*) AS c FROM fgi_impact_store GROUP BY year ORDER BY year""")
    if err:
        data["errors"]["year_era"] = err
    else:
        years = [int(r["Y"]) for r in rows if r["Y"] is not None]
        q["year_era"] = {
            "question": "PERIOD_YEAR ของวิว ALLMAP เป็น พ.ศ. หรือ ค.ศ. (DECISIONS 4.4)",
            "distribution": {str(r["Y"]): r["C"] for r in rows},
            "verdict": _year_verdict(years),
        }

    # ข้อ 2.15 — แถวตกร่องค้าง W และ branchtype ที่หายไป
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS w_total,
               SUM(CASE WHEN branchtype_i IS NULL THEN 1 ELSE 0 END) AS null_bt_i,
               SUM(CASE WHEN branchtype_n IS NULL THEN 1 ELSE 0 END) AS null_bt_n
          FROM fgi_impact_store WHERE flag_verify = 'W'""")
    if err:
        data["errors"]["stuck_w"] = err
    elif rows:
        q["stuck_w"] = {
            "question": "แถวที่ค้าง W และสาเหตุ branchtype หาย (DECISIONS 2.15)",
            **rows[0],
        }

    # ข้อ 2.15 (ต่อ) — snapshot ของ branchtype ต่างจาก master ปัจจุบันแค่ไหน
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN ms.branch_id IS NULL THEN 1 ELSE 0 END) AS no_master,
               SUM(CASE WHEN ms.branch_id IS NOT NULL
                         AND NVL(fis.branchtype_i,'~') <> NVL(ms.status_type,'~')
                        THEN 1 ELSE 0 END) AS differs
          FROM fgi_impact_store fis
          LEFT JOIN mas_store ms ON ms.branch_id = fis.storecode_i
         WHERE fis.create_by = 'ALM'""")
    if err:
        data["errors"]["branchtype_drift"] = err
    elif rows:
        q["branchtype_drift"] = {
            "question": "ใช้ mas_store ปัจจุบันแทน snapshot แล้วผล P/N ต่างกี่แถว (DECISIONS 2.15)",
            **rows[0],
        }

    rows, err = try_fetch(cur, """
        SELECT fis.branchtype_i AS snapshot_type, ms.status_type AS master_type,
               fis.flag_verify AS flag_verify, COUNT(*) AS c
          FROM fgi_impact_store fis
          JOIN mas_store ms ON ms.branch_id = fis.storecode_i
         WHERE fis.create_by = 'ALM'
           AND NVL(fis.branchtype_i,'~') <> NVL(ms.status_type,'~')
         GROUP BY fis.branchtype_i, ms.status_type, fis.flag_verify
         ORDER BY COUNT(*) DESC FETCH FIRST 30 ROWS ONLY""")
    if not err:
        q["branchtype_drift_detail"] = rows

    # คีย์กันซ้ำของ schema ใหม่จะทำ migration ล้มหรือไม่
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS duplicate_groups FROM (
            SELECT storecode_i, storecode_n, year, month
              FROM fgi_impact_store
             GROUP BY storecode_i, storecode_n, year, month HAVING COUNT(*) > 1)""")
    if err:
        data["errors"]["pair_uniqueness"] = err
    elif rows:
        q["pair_uniqueness"] = {
            "question": "UNIQUE (impacted_store_code, new_store_code, impact_month) ของ schema ใหม่ทำ migration ล้มไหม",
            **rows[0],
        }

    # แถวแม่: หนึ่งร้าน + หนึ่งงวด ต้องมีแถวเดียว (uq_impact_process)
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS duplicate_groups FROM (
            SELECT storecode_i, start_compensate_year, start_compensate_month
              FROM fgi_impact_store_on_process
             GROUP BY storecode_i, start_compensate_year, start_compensate_month
            HAVING COUNT(*) > 1)""")
    if not err and rows:
        q["process_uniqueness"] = {
            "question": "uq_impact_process (impacted_store_code, impact_month) ทำ migration ล้มไหม",
            **rows[0],
        }

    # ── ความยาว/ช่วงค่าจริง เทียบกับชนิดคอลัมน์ของ DDL ใหม่ ──────────────
    rows, err = try_fetch(cur, """
        SELECT MAX(LENGTH(storecode_i)) AS max_len_i,
               MAX(LENGTH(storecode_n)) AS max_len_n,
               MIN(distance) AS min_dist, MAX(distance) AS max_dist,
               COUNT(DISTINCT LENGTH(storecode_i)) AS len_variants
          FROM fgi_impact_store""")
    if not err and rows:
        q["column_widths"] = {
            "question": "ความกว้างจริงของรหัสร้าน/ระยะทาง เทียบกับ VARCHAR(5) · NUMERIC(8,3) ของ DDL ใหม่",
            **rows[0]}

    # ── cross-tab ของสถานะกับแหล่งที่มา + ช่วงปี ─────────────────────────
    rows, err = try_fetch(cur, """
        SELECT flag_verify, create_by, COUNT(*) AS c,
               MIN(year) AS min_y, MAX(year) AS max_y
          FROM fgi_impact_store
         GROUP BY flag_verify, create_by ORDER BY COUNT(*) DESC""")
    if not err:
        q["flag_verify_by_source"] = rows

    # ── คอลัมน์ที่ DDL ใหม่บังคับ NOT NULL แต่ของเดิมมี NULL ──────────────
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN flag_verify IS NULL THEN 1 ELSE 0 END) AS null_flag_verify,
               SUM(CASE WHEN create_by   IS NULL THEN 1 ELSE 0 END) AS null_create_by,
               SUM(CASE WHEN month IS NULL OR year IS NULL THEN 1 ELSE 0 END) AS null_period,
               SUM(CASE WHEN storecode_n IS NULL THEN 1 ELSE 0 END) AS null_storecode_n,
               SUM(CASE WHEN distance IS NULL THEN 1 ELSE 0 END) AS null_distance
          FROM fgi_impact_store""")
    if not err and rows:
        q["not_null_gaps"] = {
            "question": "คอลัมน์ที่ DDL ใหม่เป็น NOT NULL แต่ของเดิมมี NULL (migration ล้ม)",
            **rows[0]}

    # ── คู่ที่ซ้ำ — ซ้ำเพราะอะไร ────────────────────────────────────────
    rows, err = try_fetch(cur, """
        SELECT storecode_i, storecode_n, year, month, COUNT(*) AS c,
               COUNT(DISTINCT create_by) AS distinct_create_by,
               COUNT(DISTINCT flag_verify) AS distinct_flag_verify,
               COUNT(DISTINCT distance) AS distinct_distance
          FROM fgi_impact_store
         GROUP BY storecode_i, storecode_n, year, month
        HAVING COUNT(*) > 1
         ORDER BY COUNT(*) DESC FETCH FIRST 20 ROWS ONLY""")
    if not err:
        q["duplicate_pairs_detail"] = rows

    # ── แถวแม่: มีคอลัมน์งวดของตัวเองไหม / ซ้ำกันแบบไหน ──────────────────
    rows, err = try_fetch(cur, """
        SELECT storecode_i, start_compensate_year AS sy, start_compensate_month AS sm,
               COUNT(*) AS c, COUNT(DISTINCT flag_action) AS distinct_flag_action,
               COUNT(DISTINCT datasource) AS distinct_datasource
          FROM fgi_impact_store_on_process
         GROUP BY storecode_i, start_compensate_year, start_compensate_month
        HAVING COUNT(*) > 1
         ORDER BY COUNT(*) DESC FETCH FIRST 20 ROWS ONLY""")
    if not err:
        q["duplicate_process_detail"] = rows

    # ── สัญญา fr_store: ร้านหนึ่งร้านมีหลายสัญญาในงวดเดียวจริงไหม ────────
    rows, err = try_fetch(cur, """
        SELECT COUNT(*) AS stores_with_multi_contract FROM (
            SELECT store_id FROM fr_store
             WHERE NVL(status,'-') <> 'D' AND store_id <> '00000' AND cancel_type IS NOT NULL
             GROUP BY store_id HAVING COUNT(*) > 1)""")
    if not err and rows:
        q["multi_contract"] = {
            "question": "ร้านที่มีสัญญา fr_store มากกว่า 1 ฉบับ (ตัวตัดสินว่าต้องมี dense_rank จริงไหม)",
            **rows[0]}

    # ── โปรไฟล์ระยะทางของแถว ALM (แถวที่ Job 2 เป็นคนสร้าง) ──────────────
    rows, err = try_fetch(cur, """
        SELECT create_by, distance_unit, COUNT(*) AS c,
               SUM(CASE WHEN distance = 0 THEN 1 ELSE 0 END) AS zero_distance,
               SUM(CASE WHEN distance IS NULL THEN 1 ELSE 0 END) AS null_distance,
               MIN(distance) AS min_d, MAX(distance) AS max_d
          FROM fgi_impact_store
         GROUP BY create_by, distance_unit ORDER BY COUNT(*) DESC""")
    if not err:
        q["distance_profile"] = rows

    # ── ตาราง _BK_20250515 = ข้อมูลประวัติจริง (live ถูกรีเซ็ต 2025-05-15) ──
    #    728 แถวใน live เป็นแค่ข้อมูลหลังรีเซ็ต — โดเมนจริงต้องดูจากชุดนี้
    bk = "FGI_IMPACT_STORE_BK_20250515"
    if bk in schema["tables"] or True:
        for col in ("FLAG_VERIFY", "CREATE_BY", "UPDATE_BY", "DISTANCE_UNIT"):
            rows, err = try_fetch(cur, f"""
                SELECT {col} AS val, COUNT(*) AS c FROM {bk}
                 GROUP BY {col} ORDER BY COUNT(*) DESC FETCH FIRST {MAX_DISTINCT} ROWS ONLY""")
            if not err:
                data["domains"][f"{bk}.{col}"] = {
                    "note": f"ข้อมูลประวัติก่อนรีเซ็ต — โดเมนจริงของ {col}",
                    "values": {("<NULL>" if r["VAL"] is None else str(r["VAL"])): r["C"] for r in rows},
                }

        rows, err = try_fetch(cur, f"""
            SELECT year AS y, COUNT(*) AS c FROM {bk} GROUP BY year ORDER BY year""")
        if not err:
            years = [int(r["Y"]) for r in rows if r["Y"] is not None]
            q["year_era_history"] = {
                "question": "ปีในข้อมูลประวัติ (ชุดใหญ่ 26k แถว) — ยืนยันซ้ำข้อ 4.4",
                "distribution": {str(r["Y"]): r["C"] for r in rows},
                "verdict": _year_verdict(years)}

        rows, err = try_fetch(cur, f"""
            SELECT COUNT(*) AS duplicate_groups FROM (
                SELECT storecode_i, storecode_n, year, month FROM {bk}
                 GROUP BY storecode_i, storecode_n, year, month HAVING COUNT(*) > 1)""")
        if not err and rows:
            q["pair_uniqueness_history"] = {
                "question": "UNIQUE (I, N, งวด) เทียบกับข้อมูลประวัติทั้งหมด", **rows[0]}

        rows, err = try_fetch(cur, f"""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN ms.branch_id IS NULL THEN 1 ELSE 0 END) AS no_master,
                   SUM(CASE WHEN ms.branch_id IS NOT NULL
                             AND NVL(fis.branchtype_i,'~') <> NVL(ms.status_type,'~')
                            THEN 1 ELSE 0 END) AS differs
              FROM {bk} fis LEFT JOIN mas_store ms ON ms.branch_id = fis.storecode_i
             WHERE fis.create_by = 'ALM'""")
        if not err and rows:
            q["branchtype_drift_history"] = {
                "question": "branchtype snapshot vs master — ข้อมูลประวัติทั้งหมด (ข้อ 2.15)", **rows[0]}

        rows, err = try_fetch(cur, f"""
            SELECT fis.branchtype_i AS snapshot_type, ms.status_type AS master_type,
                   fis.flag_verify AS flag_verify, COUNT(*) AS c
              FROM {bk} fis JOIN mas_store ms ON ms.branch_id = fis.storecode_i
             WHERE fis.create_by = 'ALM'
               AND NVL(fis.branchtype_i,'~') <> NVL(ms.status_type,'~')
             GROUP BY fis.branchtype_i, ms.status_type, fis.flag_verify
             ORDER BY COUNT(*) DESC FETCH FIRST 30 ROWS ONLY""")
        if not err:
            q["branchtype_drift_history_detail"] = rows

        rows, err = try_fetch(cur, f"""
            SELECT COUNT(*) AS w_total,
                   SUM(CASE WHEN branchtype_i IS NULL THEN 1 ELSE 0 END) AS null_bt_i
              FROM {bk} WHERE flag_verify = 'W'""")
        if not err and rows:
            q["stuck_w_history"] = {
                "question": "แถวค้าง W ในข้อมูลประวัติ (ข้อ 2.15)", **rows[0]}

        rows, err = try_fetch(cur, """
            SELECT flag_action, datasource, COUNT(*) AS c
              FROM fgi_impact_store_on_process_bk_20250515
             GROUP BY flag_action, datasource ORDER BY COUNT(*) DESC""")
        if not err:
            q["flag_action_history"] = rows

    # ── ตัวเลขชี้ขาดของข้อ 2.15: เปลี่ยนไปใช้ master แล้ว "ผลตัดสินพลิก" กี่แถว ────
    #    ค่าต่างกันเฉย ๆ ไม่สำคัญ — สำคัญคือข้ามเส้นเกณฑ์หรือไม่
    elig = "('B','FAM','FB1','FB2','FC1','FVB','FVC')"
    rows, err = try_fetch(cur, f"""
        SELECT COUNT(*) AS total_alm,
               SUM(CASE WHEN (CASE WHEN fis.branchtype_i IN {elig} THEN 1 ELSE 0 END)
                        <>   (CASE WHEN ms.status_type   IN {elig} THEN 1 ELSE 0 END)
                        THEN 1 ELSE 0 END) AS eligibility_flips_i,
               SUM(CASE WHEN (CASE WHEN fis.branchtype_n = 'F' THEN 1 ELSE 0 END)
                        <>   (CASE WHEN msn.status_type  = 'F' THEN 1 ELSE 0 END)
                        THEN 1 ELSE 0 END) AS company_flag_flips_n
          FROM FGI_IMPACT_STORE_BK_20250515 fis
          JOIN mas_store ms  ON ms.branch_id  = fis.storecode_i
          LEFT JOIN mas_store msn ON msn.branch_id = fis.storecode_n
         WHERE fis.create_by = 'ALM'""")
    if not err and rows:
        q["eligibility_flip"] = {
            "question": "เปลี่ยน branchtype จาก snapshot เป็น mas_store ปัจจุบัน แล้วผล P/N พลิกกี่แถว (ข้อ 2.15)",
            **rows[0]}

    # สาเหตุจริงของแถวที่ค้าง W (เอกสารเดาว่า W1 branchtype หาย — ตรวจกับข้อมูลจริง)
    rows, err = try_fetch(cur, f"""
        SELECT COUNT(*) AS w_total,
               SUM(CASE WHEN branchtype_i IS NULL THEN 1 ELSE 0 END) AS w1_null_bt_i,
               SUM(CASE WHEN branchtype_i IS NOT NULL AND branchtype_i NOT IN {elig}
                         AND branchtype_i <> 'FPT1' THEN 1 ELSE 0 END) AS w4_unknown_type,
               SUM(CASE WHEN sbp_start_date_i IS NULL THEN 1 ELSE 0 END) AS w3_no_contract,
               SUM(CASE WHEN branchtype_i = 'FPT1' THEN 1 ELSE 0 END) AS fpt1_rows
          FROM FGI_IMPACT_STORE_BK_20250515 WHERE flag_verify = 'W'""")
    if not err and rows:
        q["stuck_w_causes"] = {
            "question": "สาเหตุจริงของแถวที่ค้าง W — W1 branchtype หาย / W3 ไม่มีสัญญา / W4 ประเภทนอกชุด",
            **rows[0]}

    rows, err = try_fetch(cur, f"""
        SELECT branchtype_i, COUNT(*) AS c FROM FGI_IMPACT_STORE_BK_20250515
         WHERE flag_verify = 'W' GROUP BY branchtype_i ORDER BY COUNT(*) DESC
         FETCH FIRST 20 ROWS ONLY""")
    if not err:
        q["stuck_w_branchtypes"] = rows

    # โดเมนของตารางยอดขายในข้อมูลประวัติ
    for tbl, col, note in [("FGI_IMPACT_STORE_SALES_BK_20250515", "FLAG_VERIFY",
                            "sgi_fgi_impact_sales_summaries.sales_status CHECK IN ('W','P','Y','N','E')")]:
        rows, err = try_fetch(cur, f"""
            SELECT {col} AS val, COUNT(*) AS c FROM {tbl}
             GROUP BY {col} ORDER BY COUNT(*) DESC""")
        if not err:
            data["domains"][f"{tbl}.{col}"] = {
                "note": note,
                "values": {("<NULL>" if r["VAL"] is None else str(r["VAL"])): r["C"] for r in rows}}

    return data


def _year_verdict(years: list[int]) -> str:
    if not years:
        return "ไม่มีข้อมูล — สรุปไม่ได้"
    be = [y for y in years if 2500 <= y <= 2599]
    ad = [y for y in years if 1990 <= y <= 2199]
    if be and not ad:
        return "BE — วิวเก็บเป็น พ.ศ. ต้องตั้ง SGI_JOB2_ALLMAP_YEAR_ERA=BE"
    if ad and not be:
        return "AD — วิวเก็บเป็น ค.ศ. ค่าตั้งต้นปัจจุบัน (AD) ถูกต้องแล้ว"
    if ad and be:
        return f"ปนกัน ⚠️ ค.ศ. {len(ad)} ค่า · พ.ศ. {len(be)} ค่า — ต้องทำ data cleanup ก่อน migrate"
    return f"ค่านอกช่วงที่คาด: {sorted(set(years))[:10]}"


# --------------------------------------------------------------------------- report
def render_markdown(schema: dict, data: dict, dsn_label: str) -> str:
    q = data["questions"]
    out = [
        "# ฐาน Oracle ระบบเดิม (As-Is) — ข้อมูลจริงที่สกัดมา",
        "",
        f"สร้างโดย `tools/introspect_legacy_oracle.py` · ฐาน `{dsn_label}` · "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "> เอกสารนี้ **generate อัตโนมัติ ห้ามแก้ด้วยมือ** · ไม่มี credential อยู่ในไฟล์",
        "> ใช้ตอบข้อค้างใน `DECISIONS-รอตัดสินใจ.md` ด้วยข้อมูลจริงแทนการอ่านโค้ด",
        "",
        "## ข้อสรุปต่อข้อค้าง",
        "",
        "| ข้อ | คำถาม | ผลจากข้อมูลจริง |",
        "|---|---|---|",
    ]

    if "year_era" in q:
        dist = q["year_era"]["distribution"]
        span = f"{min(dist)}–{max(dist)}" if dist else "ไม่มีข้อมูล"
        out.append(f"| **4.4** | `PERIOD_YEAR` พ.ศ. หรือ ค.ศ. | ปีที่พบ **{span}** → {q['year_era']['verdict']} |")
    if "branchtype_drift" in q:
        d = q["branchtype_drift"]
        out.append(f"| **2.15** | ใช้ master แทน snapshot แล้วต่างกี่แถว | ทั้งหมด {d['TOTAL']} · "
                   f"ไม่มีใน master {d['NO_MASTER']} · **ประเภทต่างกัน {d['DIFFERS']}** |")
    if "stuck_w" in q:
        d = q["stuck_w"]
        out.append(f"| **2.15** | แถวค้าง `W` มีจริงแค่ไหน | `W` = {d['W_TOTAL']} แถว · "
                   f"`branchtype_i` เป็น NULL {d['NULL_BT_I']} · `branchtype_n` NULL {d['NULL_BT_N']} |")
    if "pair_uniqueness" in q:
        n = q["pair_uniqueness"]["DUPLICATE_GROUPS"]
        verdict = "✅ migrate ได้" if n == 0 else f"❌ **{n} กลุ่มซ้ำ** ต้อง cleanup ก่อน"
        out.append(f"| — | `UNIQUE (I, N, งวด)` ของ schema ใหม่ | {verdict} |")
    if "process_uniqueness" in q:
        n = q["process_uniqueness"]["DUPLICATE_GROUPS"]
        verdict = "✅ migrate ได้" if n == 0 else f"❌ **{n} กลุ่มซ้ำ** ต้อง cleanup ก่อน"
        out.append(f"| — | `uq_impact_process` ของ schema ใหม่ | {verdict} |")

    out += ["", "## โดเมนจริงของคอลัมน์สถานะ", "",
            "เทียบกับ `CHECK` ที่ DDL ใหม่ประกาศไว้ — ค่าที่อยู่นอกโดเมนจะทำ migration ล้ม", ""]
    for key, info in data["domains"].items():
        vals = info["values"]
        out.append(f"**`{key}`** — {info['note']}")
        out.append("")
        out.append("| ค่า | จำนวนแถว |")
        out.append("|---|---|")
        for val, cnt in vals.items():
            out.append(f"| `{val}` | {cnt:,} |")
        out.append("")

    out += ["## จำนวนแถวต่อตาราง", "", "| ตาราง | แถว |", "|---|---|"]
    for table, cnt in sorted(data["row_counts"].items(), key=lambda kv: -kv[1]):
        out.append(f"| `{table}` | {cnt:,} |")

    if data["errors"]:
        out += ["", "## คิวรีที่ทำไม่สำเร็จ", "",
                "(ตารางไม่มีในสคีมานี้ หรือไม่มีสิทธิ์อ่าน — ไม่ใช่ข้อผิดพลาดของสคริปต์เสมอไป)", "",
                "| คิวรี | ข้อความ |", "|---|---|"]
        for key, err in data["errors"].items():
            out.append(f"| `{key}` | {err} |")

    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    user = os.environ.get("ORA_USER")
    pwd = os.environ.get("ORA_PASSWORD")
    dsn = os.environ.get("ORA_DSN")
    if not (user and pwd and dsn):
        print("ต้องตั้ง ORA_USER / ORA_PASSWORD / ORA_DSN ก่อน", file=sys.stderr)
        return 2

    # ป้ายกำกับที่ปลอดภัยพอจะเขียนลงไฟล์ — ตัด credential ออกเสมอ
    dsn_label = re.sub(r"^[^@]*@", "", dsn)

    try:
        conn = oracledb.connect(user=user, password=pwd, dsn=dsn, tcp_connect_timeout=20)
    except Exception as exc:
        print(f"เชื่อมต่อไม่สำเร็จ: {str(exc).splitlines()[0]}", file=sys.stderr)
        return 1

    with conn, conn.cursor() as cur:
        schema = collect_schema(cur)
        if not schema["tables"]:
            print("ไม่พบตาราง FGI_* ในสคีมานี้ — ต่อผิด user หรือเปล่า", file=sys.stderr)
            return 1
        data = collect_data(cur, schema)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "schema.sql").write_text(render_schema_sql(schema), encoding="utf-8")
    (OUT_DIR / "data.json").write_text(
        json.dumps({"source": dsn_label, "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "schema": schema, "data": data}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (OUT_DIR / "README.md").write_text(render_markdown(schema, data, dsn_label), encoding="utf-8")

    print(f"เขียนแล้ว {OUT_DIR}/schema.sql · data.json · README.md")
    print(f"  ตาราง {len(schema['tables'])} · คอลัมน์ {len(schema['columns'])} · "
          f"โดเมนที่เก็บ {len(data['domains'])} · คำถามที่ตอบได้ {len(data['questions'])}")
    for key, info in data["questions"].items():
        if isinstance(info, dict) and "verdict" in info:
            print(f"  → {key}: {info['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
