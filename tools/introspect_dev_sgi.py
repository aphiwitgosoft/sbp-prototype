#!/usr/bin/env python3
"""
สกัดโครงสร้าง + ข้อมูลจริงจากฐาน **PostgreSQL dev ของระบบ SBP** (ปลายทางของ SGI) ออกมา 3 ไฟล์

    output/legacy-sgi/schema.sql   DDL ของตารางที่ SGI แตะ (คอลัมน์ · PK · unique · index)
    output/legacy-sgi/data.json    ข้อมูลเชิงสถิติที่ใช้ตอบข้อค้าง (machine-readable)
    output/legacy-sgi/README.md    รายงานภาษาคน + ข้อสรุปต่อข้อค้างแต่ละข้อ

คู่กับ `tools/introspect_legacy_oracle.py` ที่สกัดฐาน **Oracle ของระบบเดิม (As-Is)**
ตัวนี้สกัดฝั่ง **ปลายทาง** — ตารางของระบบ SBP ที่ SGI จะไปอยู่ร่วมด้วย

⚠️ credential อ่านจาก environment variable เท่านั้น — **ห้ามใส่ค่าจริงลงไฟล์นี้หรือไฟล์ผลลัพธ์**
    PGHOST · PGPORT · PGDATABASE · PGUSER · PGPASSWORD

    PGHOST=... PGUSER=... PGPASSWORD=... python3 tools/introspect_dev_sgi.py

ทุกคำสั่งเป็น SELECT ล้วน — มี guard ปฏิเสธคำสั่งที่ขึ้นต้นด้วยคำที่เขียนข้อมูล
ผลลัพธ์อยู่ใน .gitignore เพราะมีข้อมูลธุรกิจจริง
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import pg8000.native
except ImportError:  # pragma: no cover
    print("ต้องติดตั้ง pg8000 ก่อน:  python3 -m pip install pg8000", file=sys.stderr)
    raise SystemExit(2)

OUT_DIR = Path(__file__).resolve().parent.parent / "output" / "legacy-sgi"
SCHEMA = "sps_store"

# ตารางของระบบเดิมที่ SGI อ่าน/เขียน — ชุดเดียวกับที่ build_sgi_existing_stub_sql.py จำลอง
STUB_TABLES = [
    "mas_store", "fr_store", "juristic", "mas_zone", "common_code", "common_code_type",
    "mas_param", "email_template", "email_sent", "business_user", "fcs_qssi_score",
    "workflow_transaction", "workflow_history",
]
# ตารางของ @srm/glb-workflow ที่เหลือ — ต้องรู้ของจริงก่อนทำ workflow definition (P0-WF-01)
WORKFLOW_TABLES = [
    "workflow", "workflow_version", "workflow_state", "workflow_status", "workflow_event",
    "workflow_route", "workflow_group", "workflow_group_map", "workflow_approver",
    "workflow_part", "workflow_part_display",
]

BLOCK = ("insert", "update", "delete", "drop", "truncate", "alter",
         "create", "grant", "revoke", "copy", "call", "do")
MAX_DISTINCT = 60


def _jsonable(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return f"<binary {len(v)} bytes>"
    return v


class Db:
    """ตัวห่อ connection ที่ **ปฏิเสธคำสั่งที่เขียนข้อมูล** ตั้งแต่ก่อนส่งถึงเซิร์ฟเวอร์"""

    def __init__(self) -> None:
        missing = [k for k in ("PGHOST", "PGUSER", "PGPASSWORD") if not os.environ.get(k)]
        if missing:
            print(f"ขาด environment variable: {', '.join(missing)}", file=sys.stderr)
            raise SystemExit(2)
        self.host = os.environ["PGHOST"]
        self.con = pg8000.native.Connection(
            user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"],
            host=self.host, port=int(os.environ.get("PGPORT", "5432")),
            database=os.environ.get("PGDATABASE", "postgres"),
            ssl_context=True, timeout=120,
        )

    def q(self, sql: str, **params) -> list[list]:
        head = sql.lstrip().lower()
        if any(head.startswith(w) for w in BLOCK):
            raise RuntimeError(f"สคริปต์นี้อ่านอย่างเดียว — ปฏิเสธคำสั่ง: {sql[:60]}")
        return self.con.run(sql, **params)

    def one(self, sql: str, **params):
        rows = self.q(sql, **params)
        return rows[0][0] if rows else None

    def close(self) -> None:
        self.con.close()


# --------------------------------------------------------------------------- schema
def collect_schema(db: Db, tables: list[str]) -> dict:
    out: dict[str, dict] = {}
    for t in tables:
        cols = db.q(
            "SELECT column_name, data_type, character_maximum_length, numeric_precision,"
            "       numeric_scale, is_nullable, column_default "
            "  FROM information_schema.columns "
            " WHERE table_schema = :s AND table_name = :t ORDER BY ordinal_position",
            s=SCHEMA, t=t)
        if not cols:
            out[t] = {"exists": False}
            continue
        cons = db.q(
            "SELECT con.conname, con.contype,"
            "       (SELECT string_agg(a.attname, ',' ORDER BY x.ord)"
            "          FROM unnest(con.conkey) WITH ORDINALITY x(attnum, ord)"
            "          JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = x.attnum) AS cols"
            "  FROM pg_constraint con"
            "  JOIN pg_class c ON c.oid = con.conrelid"
            "  JOIN pg_namespace n ON n.oid = c.relnamespace"
            " WHERE n.nspname = :s AND c.relname = :t ORDER BY con.contype, con.conname",
            s=SCHEMA, t=t)
        idx = db.q(
            "SELECT indexname, indexdef FROM pg_indexes"
            " WHERE schemaname = :s AND tablename = :t ORDER BY indexname",
            s=SCHEMA, t=t)
        rows = db.one(f'SELECT count(*) FROM {SCHEMA}."{t}"')
        out[t] = {
            "exists": True,
            "row_count": rows,
            "columns": [
                {"name": c[0], "type": c[1], "max_len": c[2], "precision": c[3],
                 "scale": c[4], "nullable": c[5] == "YES", "default": c[6]}
                for c in cols],
            "constraints": [{"name": c[0], "type": c[1], "columns": c[2]} for c in cons],
            "indexes": [{"name": i[0], "definition": i[1]} for i in idx],
        }
    return out


def _pg_type(c: dict) -> str:
    t = c["type"]
    if t in ("character varying", "character") and c["max_len"]:
        return f"{'varchar' if t.startswith('character v') else 'char'}({c['max_len']})"
    if t == "numeric" and c["precision"]:
        return f"numeric({c['precision']},{c['scale'] or 0})"
    return {"timestamp without time zone": "timestamp",
            "timestamp with time zone": "timestamptz",
            "double precision": "float8"}.get(t, t)


def render_schema_sql(schema: dict, host: str) -> str:
    L = [
        "-- =====================================================================",
        "--  DDL ของตารางระบบ SBP ที่ SGI แตะ — สกัดจากฐาน **dev จริง**",
        "-- =====================================================================",
        "--  สร้างโดย tools/introspect_dev_sgi.py — ห้ามแก้ด้วยมือ",
        f"--  ฐาน: {host}  ·  schema: {SCHEMA}",
        f"--  เวลา: {datetime.now().isoformat(timespec='seconds')}",
        "--  ⚠️ ไฟล์นี้เป็น **ภาพสะท้อนของจริง** ไม่ใช่สิ่งที่ต้องรัน — ห้ามเอาไปติดตั้งทับ",
        "-- =====================================================================",
        "",
    ]
    for t, info in schema.items():
        if not info.get("exists"):
            L.append(f"-- ❌ ไม่มีตาราง {t} ในฐานนี้")
            continue
        L.append(f"-- {t}  ·  {info['row_count']:,} แถว")
        L.append(f'CREATE TABLE {SCHEMA}."{t}" (')
        body = []
        for c in info["columns"]:
            line = f'    {c["name"]:<34} {_pg_type(c)}'
            if not c["nullable"]:
                line += " NOT NULL"
            if c["default"]:
                line += f" DEFAULT {c['default']}"
            body.append(line)
        pk = [x for x in info["constraints"] if x["type"] == "p"]
        if pk:
            body.append(f'    CONSTRAINT {pk[0]["name"]} PRIMARY KEY ({pk[0]["columns"]})')
        else:
            body.append("    -- 🔴 ไม่มี PRIMARY KEY")
        L.append(",\n".join(body))
        L.append(");")
        for i in info["indexes"]:
            L.append(f"-- index: {i['definition']}")
        L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- data
def collect_data(db: Db) -> dict:
    q: dict = {}

    q["server"] = {
        "version": db.one("SELECT version()"),
        "server_version_num": db.one("SHOW server_version_num"),
        "question": "เราทดสอบบน PostgreSQL 16 — ฐาน dev เป็นรุ่นเดียวกันหรือไม่",
    }

    q["sgi_tables_installed"] = {
        "count": db.one("SELECT count(*) FROM information_schema.tables "
                        " WHERE table_schema = :s AND table_name LIKE 'sgi!_%' ESCAPE '!'", s=SCHEMA),
        "names": [r[0] for r in db.q(
            "SELECT table_name FROM information_schema.tables "
            " WHERE table_schema = :s AND table_name LIKE 'sgi!_%' ESCAPE '!' ORDER BY 1", s=SCHEMA)],
        "question": "sgi_schema.sql เคยถูกติดตั้งลงฐานนี้แล้วหรือยัง (preflight จะหยุดถ้ามี)",
    }

    # ── ค่า SGI ที่ถูก seed ไปแล้ว — ต้นเหตุของข้อขัดแย้งเรื่องชื่อ parameter ──
    q["sgi_seeded"] = {
        "question": "มีใคร seed ค่าของ SGI ลงตารางระบบเดิมไปแล้วหรือยัง · ใช้ชื่อ/เจ้าของอะไร",
        "common_code_type": [
            {"code_type": r[0], "name": r[1], "active": r[2], "create_user": r[3],
             "create_date": _jsonable(r[4])}
            for r in db.q("SELECT code_type, code_type_name, active_flag, create_user, create_date"
                          f"  FROM {SCHEMA}.common_code_type"
                          " WHERE code_type LIKE 'SGI!_%' ESCAPE '!' ORDER BY code_type")],
        "common_code": [
            {"code_type": r[0], "seq_no": r[1], "code_value": r[2], "code_name": r[3],
             "active": r[4], "create_user": r[5]}
            for r in db.q("SELECT code_type, seq_no, code_value, code_name, active_flag, create_user"
                          f"  FROM {SCHEMA}.common_code"
                          " WHERE code_type LIKE 'SGI!_%' ESCAPE '!' ORDER BY code_type, seq_no")],
        "mas_param": [
            {"param_name": r[0], "param_value": r[1], "description": r[2],
             "active": r[3], "create_by": r[4]}
            for r in db.q("SELECT param_name, param_value, description, active_flag, create_by"
                          f"  FROM {SCHEMA}.mas_param"
                          " WHERE param_name LIKE 'SGI!_%' ESCAPE '!' ORDER BY param_name")],
        "email_template_sgi": db.one(
            f"SELECT count(*) FROM {SCHEMA}.email_template WHERE create_by IN ('SGI-INSTALL','SGI-SETUP')"),
    }

    # ── โซน: ตัวเชื่อมผู้รับอีเมลของ Job 8b / Job 12 ──
    zone_store = [r[0] for r in db.q(
        f"SELECT DISTINCT btrim(zone_cd) FROM {SCHEMA}.mas_store"
        " WHERE coalesce(btrim(zone_cd),'') <> '' ORDER BY 1")]
    zone_user_cd = [r[0] for r in db.q(
        f"SELECT DISTINCT btrim(zone_cd) FROM {SCHEMA}.business_user"
        " WHERE coalesce(btrim(zone_cd),'') <> '' ORDER BY 1")]
    zone_user_code = [r[0] for r in db.q(
        f"SELECT DISTINCT btrim(zone_code) FROM {SCHEMA}.business_user"
        " WHERE coalesce(btrim(zone_code),'') <> '' ORDER BY 1")]
    q["zone_join"] = {
        "question": "Job 8b/12 หาผู้รับด้วย bu.zone_cd = ms.zone_cd — join ติดจริงกี่ค่า",
        "mas_store_zone_cd": zone_store,
        "business_user_zone_cd": zone_user_cd,
        "business_user_zone_code": zone_user_code,
        "overlap_zone_cd": sorted(set(zone_store) & set(zone_user_cd)),
        "mas_store_rows": db.one(f"SELECT count(*) FROM {SCHEMA}.mas_store"),
        "mas_store_zone_cd_null_or_blank": db.one(
            f"SELECT count(*) FROM {SCHEMA}.mas_store WHERE coalesce(btrim(zone_cd),'') = ''"),
        "business_user_rows": db.one(f"SELECT count(*) FROM {SCHEMA}.business_user"),
        "business_user_zone_both_blank": db.one(
            f"SELECT count(*) FROM {SCHEMA}.business_user"
            " WHERE coalesce(btrim(zone_cd),'') = '' AND coalesce(btrim(zone_code),'') = ''"),
    }

    q["business_user_groups"] = {
        "question": "group_id 15 (OPT/DV) และ 38 (GM) ที่ Job 8b/12 ใช้ มีคนอยู่จริงไหม",
        "counts": {str(r[0]): r[1] for r in db.q(
            f"SELECT group_id, count(*) FROM {SCHEMA}.business_user"
            " WHERE group_id IN (15, 38) GROUP BY group_id ORDER BY 1")},
    }

    # ── โดเมนจริงของคอลัมน์ที่กฎตัดสินของ Job 2 ใช้ ──
    q["mas_store_status_type"] = {
        "question": "ชุดรหัสประเภทร้านที่กฎ P/N ของ Job 2 อ้าง (B/FAM/FB1/FB2/FC1/FVB/FVC/FPT1/F)",
        "domain": [{"value": r[0], "rows": r[1]} for r in db.q(
            f"SELECT coalesce(btrim(status_type),'(ว่าง)'), count(*) FROM {SCHEMA}.mas_store"
            " GROUP BY 1 ORDER BY 2 DESC LIMIT :n", n=MAX_DISTINCT)],
    }

    q["common_code_types_in_use"] = {
        "question": "code_type ที่ระบบเดิมใช้อยู่ — ตรวจว่า SGI_* ไม่ชนของใคร",
        "total": db.one(f"SELECT count(DISTINCT code_type) FROM {SCHEMA}.common_code"),
        "starting_with_sgi": [r[0] for r in db.q(
            f"SELECT DISTINCT code_type FROM {SCHEMA}.common_code"
            " WHERE code_type LIKE 'SGI%' ORDER BY 1")],
    }

    q["fcs_qssi_score"] = {
        "question": "Job 6 อ่านคะแนน QSSI จากตารางนี้ — มีข้อมูลจริงไหม",
        "rows": db.one(f"SELECT count(*) FROM {SCHEMA}.fcs_qssi_score"),
        "columns": [r[0] for r in db.q(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema = :s AND table_name = 'fcs_qssi_score' ORDER BY ordinal_position",
            s=SCHEMA)],
    }

    # ── workflow engine — ของจริงก่อนทำ definition (P0-WF-01) ──
    q["workflow"] = {
        "question": "มี workflow version/state/status/route ของใครอยู่แล้วบ้าง — SGI ต้องขอ version ใหม่",
        "counts": {},
        "versions": [],
    }
    for t in ("workflow", "workflow_version", "workflow_state", "workflow_status",
              "workflow_event", "workflow_route", "workflow_transaction"):
        try:
            q["workflow"]["counts"][t] = db.one(f'SELECT count(*) FROM {SCHEMA}."{t}"')
        except Exception as exc:                       # pragma: no cover
            q["workflow"]["counts"][t] = f"อ่านไม่ได้: {exc}"
    try:
        q["workflow"]["versions"] = [
            {"version_id": r[0], "workflow_id": r[1], "initial_state_id": r[2],
             "end_state_id": r[3], "description": r[4], "url_main": r[5]}
            for r in db.q("SELECT version_id, workflow_id, initial_state_id, end_state_id,"
                          f"       description, url_main FROM {SCHEMA}.workflow_version"
                          " ORDER BY version_id")]
    except Exception as exc:                           # pragma: no cover
        q["workflow"]["versions"] = f"อ่านไม่ได้: {exc}"

    q["email_template"] = {
        "question": "template EM-01..08 ที่ SGI ต้องใช้ มีอยู่แล้วหรือยัง",
        "rows": db.one(f"SELECT count(*) FROM {SCHEMA}.email_template"),
        "sgi_owned": [
            {"id": r[0], "name": r[1], "active": r[2], "create_by": r[3]}
            for r in db.q("SELECT email_template_id, email_template_name, active_flag, create_by"
                          f"  FROM {SCHEMA}.email_template"
                          " WHERE create_by IN ('SGI-INSTALL','SGI-SETUP') ORDER BY email_template_id")],
    }

    return q


def _verdict(data: dict) -> list[tuple[str, str, str]]:
    """(หัวข้อ, ผล, ข้อสรุป) — ตัดสินจากข้อมูลจริงเท่านั้น"""
    out = []
    v = data["server"]["server_version_num"]
    major = int(str(v)[:2])
    out.append(("รุ่นของฐาน",
                "🔴 ต่างจากที่ทดสอบ" if major != 16 else "✅ ตรงกับที่ทดสอบ",
                f"dev เป็น PostgreSQL {data['server']['version'].split()[1]} "
                f"แต่ชุดทดสอบทั้งหมดรันบน 16 — ต้องรันซ้ำบนรุ่นเดียวกับ dev ก่อนขึ้น UAT"))

    n = data["sgi_tables_installed"]["count"]
    out.append(("ตาราง sgi_ ในฐาน",
                "✅ ยังไม่ติดตั้ง" if n == 0 else f"⚠️ มีแล้ว {n} ตาราง",
                "preflight ของ sgi_schema.sql จะผ่าน ติดตั้งใหม่ได้"
                if n == 0 else "preflight จะหยุด — ต้องตัดสินใจว่าจะ rollback ก่อนหรือ migrate"))

    s = data["sgi_seeded"]
    seeded = len(s["common_code"]) + len(s["mas_param"]) + len(s["common_code_type"])
    owners = sorted({r["create_user"] for r in s["common_code_type"] if r["create_user"]} |
                    {r["create_by"] for r in s["mas_param"] if r["create_by"]})
    out.append(("ค่า SGI ที่ถูก seed ไปแล้ว",
                "✅ ยังไม่มี" if seeded == 0 else f"🔴 มีแล้ว {seeded} แถว (เจ้าของ {', '.join(owners)})",
                "seed ของเราลงได้เลย" if seeded == 0 else
                "ชื่อ/ค่าที่ติดตั้งไว้ต้องเป็นมาตรฐาน — seed ที่ใช้ชื่อต่างจะสร้างค่าคู่ขนานที่ไม่มีใครรู้ว่าตัวไหนจริง"))

    z = data["zone_join"]
    out.append(("โซนสำหรับหาผู้รับอีเมล (Job 8b/12)",
                "✅ join ได้" if z["overlap_zone_cd"] else "🔴 join ไม่ติดเลย",
                f"mas_store.zone_cd = {z['mas_store_zone_cd']} · "
                f"business_user.zone_cd = {z['business_user_zone_cd']} · "
                f"ซ้อนกัน {len(z['overlap_zone_cd'])} ค่า · "
                f"mas_store ว่าง/NULL {z['mas_store_zone_cd_null_or_blank']:,} จาก {z['mas_store_rows']:,} แถว"))

    g = data["business_user_groups"]["counts"]
    out.append(("group_id 15 / 38",
                "✅ มีจริงทั้งคู่" if {"15", "38"} <= set(g) else "🔴 ขาด",
                " · ".join(f"group {k} = {v:,} คน" for k, v in g.items()) or "ไม่พบทั้งสองกลุ่ม"))

    e = data["email_template"]
    out.append(("email template ของ SGI",
                "✅ มีแล้ว" if e["sgi_owned"] else "🔴 ยังไม่มี",
                f"ทั้งตารางมี {e['rows']:,} แถว · เป็นของ SGI {len(e['sgi_owned'])} แถว"))

    w = data["workflow"]["counts"]
    out.append(("workflow engine",
                "ℹ️ ข้อมูลอ้างอิง",
                " · ".join(f"{k}={v:,}" if isinstance(v, int) else f"{k}={v}"
                           for k, v in w.items())))
    return out


def render_markdown(schema: dict, data: dict, host: str) -> str:
    L = [
        "# ฐาน dev ของระบบ SBP — ภาพจริงที่ SGI ต้องไปอยู่ร่วมด้วย",
        "",
        "> สร้างโดย `tools/introspect_dev_sgi.py` · **SELECT ล้วน ไม่มีคำสั่งที่เขียนข้อมูล**",
        f"> ฐาน: `{host}` · schema `{SCHEMA}`",
        f"> เวลา: {datetime.now().isoformat(timespec='seconds')}",
        ">",
        "> ⚠️ ไฟล์ในโฟลเดอร์นี้อยู่ใน `.gitignore` เพราะมีข้อมูลธุรกิจจริง",
        "> คู่กับ `output/legacy-oracle/` ที่สกัดฝั่ง **Oracle ของระบบเดิม (As-Is)**",
        "",
        "## ข้อสรุปต่อข้อค้าง",
        "",
        "| หัวข้อ | ผล | รายละเอียด |",
        "|---|---|---|",
    ]
    for topic, res, detail in _verdict(data):
        L.append(f"| {topic} | {res} | {detail} |")

    L += ["", "## ค่าของ SGI ที่ถูกติดตั้งลงฐานไปแล้ว", ""]
    s = data["sgi_seeded"]
    if s["mas_param"]:
        L += ["### `mas_param`", "", "| param_name | ค่า | เจ้าของ |", "|---|---|---|"]
        L += [f"| `{r['param_name']}` | {r['param_value']} | {r['create_by']} |" for r in s["mas_param"]]
        L.append("")
    if s["common_code"]:
        L += ["### `common_code`", "", "| code_type | code_value | code_name | เจ้าของ |", "|---|---|---|---|"]
        L += [f"| `{r['code_type']}` | `{r['code_value']}` | {r['code_name']} | {r['create_user']} |"
              for r in s["common_code"]]
        L.append("")

    L += ["## ตารางที่ตรวจ", "", "| ตาราง | แถว | PK | index |", "|---|---|---|---|"]
    for t, info in schema.items():
        if not info.get("exists"):
            L.append(f"| `{t}` | — | ❌ ไม่มีตารางนี้ | — |")
            continue
        pk = [c for c in info["constraints"] if c["type"] == "p"]
        L.append(f"| `{t}` | {info['row_count']:,} | "
                 f"{'`' + pk[0]['columns'] + '`' if pk else '🔴 ไม่มี'} | {len(info['indexes'])} |")

    L += ["", "## อ่านต่อ", "",
          "| เรื่อง | ที่ไหน |", "|---|---|",
          "| DDL ที่สกัดได้ | `output/legacy-sgi/schema.sql` |",
          "| ข้อมูลดิบแบบ machine-readable | `output/legacy-sgi/data.json` |",
          "| ฝั่ง Oracle ของระบบเดิม | `output/legacy-oracle/README.md` |",
          "| stub ที่ใช้ตอนเทส | `output/sql/sgi_existing_stub.sql` |", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- main
def main() -> int:
    db = Db()
    try:
        schema = collect_schema(db, STUB_TABLES + WORKFLOW_TABLES)
        data = collect_data(db)
    finally:
        db.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "schema.sql").write_text(render_schema_sql(schema, db.host), encoding="utf-8")
    (OUT_DIR / "data.json").write_text(
        json.dumps({"source": db.host, "schema": SCHEMA,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "tables": schema, "questions": data},
                   ensure_ascii=False, indent=1, default=_jsonable), encoding="utf-8")
    (OUT_DIR / "README.md").write_text(render_markdown(schema, data, db.host), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_DIR}/schema.sql · data.json · README.md")
    for topic, res, _ in _verdict(data):
        print(f"  {res:<28} {topic}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
