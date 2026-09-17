#!/usr/bin/env python3
"""ชุดตรวจความถูกต้องของเอกสาร SGI — รันก่อนส่งมอบทุกครั้ง

    python3 tools/check_docs.py

ตรวจ 2 ฝั่ง:
  A. ฝั่ง SGI เอง  — จำนวนตาราง · FK · ลิงก์ · ตาราง markdown · จำนวนเอกสาร
  B. ฝั่งระบบเดิม    — ตาราง/คอลัมน์ของ sps_store ที่เราอ้าง ต้องมีจริง ·
                       ชื่อ function ของ @srm/glb-workflow ต้องอยู่ใน API 8 ตัว ·
                       ชื่อคอลัมน์ของ email-lib ต้องเป็นชื่อ production

ฝั่ง B สำคัญเพราะ audit ชุดเดิมตรวจแต่ DDL ของเรา ทำให้ชื่อคอลัมน์ของระบบเดิม
ที่เขียนผิด (เช่น workflow_transaction.approver ที่จริงคือ current_approver)
หลุดรอดไปได้ทุกครั้ง
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CANON_TABLES = 21          # 20 CREATE + fcs_qssi_score ที่ reuse ของเดิม (รับ F8+F1 เข้าโครง 2026-08-21)
CANON_DOCS = 42           # 39 topic + LLDD-API + LLDD-Database + LLDD-To-Be (นับจาก .md เท่านั้น)
#   LLDD-Database-Dictionary **ไม่นับ** เพราะส่งมอบเป็น PDF อย่างเดียว (มติผู้ใช้ 2026-09-09)
#   ไม่มีชั่วโมง/เจ้าของ จึงไม่กระทบยอด 829 ชม.
#   (ตัด Job 1 ImportQSSI 2026-08-24 · เพิ่ม Job 11 ConsumeStaCompensate + Job 12 NotifyPendingWork 2026-09-02)
CANON_ENDPOINTS = 28       # 6 กลุ่ม (เอกสาร 11 · Lookup 2 · Master 8 · รายงาน 2 · Workflow 3 · Interface 2)
LLDDV2_FEATURES = 8
LLDDV2_JOBS = 12           # Jobs 2–12 + 8b
#   Interface 3 → 2 เมื่อ 2026-09-08 — ตัด POST /sgi/interface/sta/ack (มติข้อ 2.13 · สเปก STA ไม่มี ACK แบบ HTTP)            # 38 topic + LLDD-API + LLDD-Database
ENGINE_API = {
    "initializeWorkflow", "eventWorkflow", "getPermissionEvents", "getHistory",
    "getTransaction", "getPendingFlowByUser", "getWorkflowsByUser", "addPreApprover",
}
# ชื่อที่เอกสาร lib email เสนอไว้ แต่ production ใช้ชื่ออื่น
EMAIL_DOC_ONLY = {
    "sent_by": "send_by",
    "subject_mail": "subject_format",
    "body_mail": "body_format",
    "email_name": "email_template_name",
}
NOT_COLUMN = {
    "md", "ts", "js", "py", "html", "json", "sql", "png", "csv", "xlsx", "pdf", "docx",
    "module", "service", "controller", "repository", "entity", "dto", "spec", "config",
    "job", "key", "url", "interface", "guard", "provider", "e2e", "test", "mjs", "sh",
}

results: list[tuple[str, list[str]]] = []


def check(name: str, bad: list[str]) -> None:
    results.append((name, sorted(set(bad))))


def read(path: str) -> str:
    return io.open(path, encoding="utf-8").read()


DOC_FILES = [f for f in (
    glob.glob("*.md") + glob.glob("*.html")
    + glob.glob("LLDD/md/**/*.md", recursive=True) + glob.glob("tools/*.py")
) if os.path.basename(f) != "check_docs.py"]

# ------------------------------------------------------------- B. ฝั่งระบบเดิม
schema: dict[str, set[str]] = {}
cur = None
for line in io.open("SBP/db-schema-sps_store.md", encoding="utf-8"):
    m = re.match(r"^### ([a-z_0-9]+)\s*$", line)
    if m:
        cur = m.group(1)
        schema[cur] = set()
        continue
    if cur:
        m = re.match(r"^\|\s*\d+\s*\|\s*`([a-z_0-9]+)`", line)
        if m:
            schema[cur].add(m.group(1))

EXISTING_TABLES = set(schema)

# ---------------------------------------------------------------- A. ฝั่ง SGI
ddl = read("LLDD/md/LLDD-Database.md")
created = set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)", ddl))
check(f"ตารางในขอบเขต = {CANON_TABLES} (CREATE + fcs_qssi_score ที่ reuse)",
      [] if len(created) + 1 == CANON_TABLES else
      [f"CREATE {len(created)} ตาราง + fcs_qssi_score = {len(created)+1} ≠ {CANON_TABLES}"])

fk_bad = []
for m in re.finditer(r"REFERENCES\s+([a-z_0-9]+)\s*\(", ddl):
    if m.group(1) not in created:
        fk_bad.append(f"REFERENCES {m.group(1)} — ไม่มี CREATE TABLE")
check("FK ชี้ตารางที่ไม่ได้ CREATE", fk_bad)

# ── #33 ค่าที่เอกสารเขียนลงคอลัมน์ enum ต้องอยู่ใน CHECK constraint ของ DDL ────────────
#   เจอจริง 2026-09-02: Job 8 INSERT data_name='DOCUMENT_CREATE' และ Job 11 ใช้
#   'STA_UPDATE_COMPENSATE' ทั้งที่ CHECK ไม่รับ → INSERT จะพังตอนรันจริงโดยไม่มีใครเห็นตอนรีวิว
_enum_bad: list[str] = []
_ENUM_COLS = [
    ("sgi_interface_transactions", "data_name"),
    ("sgi_fgi_impact_compensations", "compensate_status"),
    ("sgi_fgi_impact_stores", "verify_status"),
    ("sgi_fgi_impact_stores", "sales_request_status"),
    ("sgi_fgi_impact_processes", "flag_action"),
    ("sgi_fgi_impact_sales_summaries", "sales_status"),
]
for _tbl, _col in _ENUM_COLS:
    _m = re.search(_col + r"\s+VARCHAR\(\d+\)[^,]*?CHECK \(" + _col + r" IN \((.*?)\)\)", ddl, re.S) \
         or re.search(_col + r"\s+CHAR\(\d+\)[^,]*?CHECK \(" + _col + r" IN \((.*?)\)\)", ddl, re.S)
    if not _m:
        _enum_bad.append(f"{_tbl}.{_col} — หา CHECK ใน DDL ไม่เจอ")
        continue
    _allowed = set(re.findall(r"'([A-Za-z_]+)'", _m.group(1)))
    for _f in DOC_FILES + ["database.md", "api.md", "workflow.md"]:
        _t = read(_f)
        for _mm in re.finditer(_col + r"\s*=\s*'([A-Za-z_]{2,})'", _t):
            if _mm.group(1) not in _allowed:
                _enum_bad.append(f"{_f} :: {_tbl}.{_col} = '{_mm.group(1)}' ไม่อยู่ใน CHECK")
        if _col == "data_name":
            for _mm in re.finditer(r"'([A-Z_]{4,})',\s*'(?:IN|OUT|INTERNAL)'", _t):
                if _mm.group(1) not in _allowed:
                    _enum_bad.append(f"{_f} :: INSERT data_name '{_mm.group(1)}' ไม่อยู่ใน CHECK")
check("ค่า enum ที่เอกสารใช้ไม่อยู่ใน CHECK ของ DDL", sorted(set(_enum_bad)))

# ── #34 error code ต้องมาจาก catalog กลางเท่านั้น ───────────────────────────────
#   เจอจริง 2026-09-02: FE-Create-Document ตั้งชื่อ FS_FIELD_SCHEMA_INVALID เอง (catalog ใช้
#   FS_BRIDGE_SCHEMA_INVALID) และ CODE_DUPLICATE ถูกใช้ 3 จุดโดยไม่เคยอยู่ใน catalog
_cc = read("LLDD/md/BE/LLDD-BE-API-Common-Contracts.md")
_err_bad: list[str] = []
if "### 5.1 Error and Popup Catalog" in _cc:
    _i = _cc.index("### 5.1 Error and Popup Catalog")
    _j = _cc.index("### 5.2", _i)
    _catalog = set(re.findall(r"^\| ([A-Z][A-Z0-9_]{4,}) \|", _cc[_i:_j], re.M))
    # run state ของ batch job ไม่ใช่ error code ของ API
    _job_states = {"SKIPPED_LOCKED", "JOB_FAILED", "INVALID_JOB_INPUT"}
    _suffix = ("_REQUIRED", "_INVALID", "_NOT_FOUND", "_TOO_LARGE", "_DENIED",
               "_CONFLICT", "_EXPIRED", "_LOCKED", "_DUPLICATE", "_BLOCKED", "_UNSUPPORTED")
    for _f in DOC_FILES + ["api.md", "plan-api.html"]:
        for _m in re.finditer(r"\b([A-Z][A-Z0-9_]{4,})\b", read(_f)):
            _c = _m.group(1)
            if _c.endswith(_suffix) and _c not in _catalog and _c not in _job_states:
                _err_bad.append(f"{_f} :: error code {_c} ไม่มีใน catalog กลาง (5.1)")
else:
    _err_bad.append("หาหัวข้อ 5.1 Error and Popup Catalog ไม่เจอ")
check("error code ที่ใช้ไม่อยู่ใน catalog กลาง", sorted(set(_err_bad)))

# ── #35 ข้อความ validation ไทยในโปรโตไทป์ ต้องมีในเอกสาร LLDD ด้วย ──────────────
#   กติกาโครงการ: ข้อความ popup/validation เป็น verbatim จาก SRS ห้าม paraphrase
#   ถ้าไม่มีในเอกสาร dev ที่สร้างจาก LLDD จะไม่ได้ข้อความเดียวกับที่ตกลงไว้
#   เจอจริง 2026-09-02: "กรุณาเลือกสถานะก่อนค้นหาข้อมูล" และ
#   "กรุณาเลือกไฟล์ที่ต้องการแนบ ก่อนกดแนบเอกสาร" อยู่ในโปรโตไทป์แต่ไม่มีใน LLDD
_PROTO_SCREENS = ["k2-document.html", "k2-list-waiting.html", "k2-list-related.html",
                  "k2-report.html", "k2-create.html", "k2-factors.html", "k2-competitors.html"]
_lldd_text = "".join(read(_f) for _f in DOC_FILES if _f.startswith("LLDD/md/"))
_msg_bad: list[str] = []
for _f in _PROTO_SCREENS:
    for _m in re.finditer(r"'(กรุณา[^']{5,110}|ท่านยัง[^']{5,110}|โปรด[^']{5,110})'", read(_f)):
        if _m.group(1) not in _lldd_text:
            _msg_bad.append(f"{_f} :: \"{_m.group(1)}\" ไม่มีในเอกสาร LLDD ฉบับใดเลย")
check("ข้อความ validation ไทยในโปรโตไทป์ที่ไม่มีในเอกสาร LLDD", sorted(set(_msg_bad)))

# ── #36 กติกา idempotency ต้องตรงกับ SQL ที่เขียนไว้จริงในฉบับเดียวกัน ─────────────
#   เจอจริง 2026-09-02: LLDD Job 2 บอกในหัวข้อเงื่อนไขตัดสินว่า "พบแล้วให้ข้าม ห้าม UPDATE ทับ"
#   แต่ Write query กลับเป็น ON CONFLICT ... DO UPDATE — เอกสารฉบับเดียวกันสั่งตรงข้ามกันเอง
_conflict_bad: list[str] = []
for _f in [_x for _x in DOC_FILES if _x.startswith("LLDD/md/Jobs/")]:
    _t = read(_f)
    _m = re.search(r"\| Idempotency / dedup \| ([^|]+)\|", _t)
    if not _m:
        continue
    _rule = _m.group(1)
    _w = re.search(r"#### Write / upsert query\s*\n+```sql\s*(.*?)```", _t, re.S)
    if not _w:
        continue
    _sql = re.sub(r"--[^\n]*", "", _w.group(1))   # ตัดคอมเมนต์ก่อน ไม่งั้นคำว่า DO NOTHING ในคอมเมนต์จะกลบผลตรวจ
    _says_skip = ("ห้ามอัปเดตทับ" in _rule) or ("ข้ามเงียบ" in _rule)
    _says_update = "อัปเดตค่าที่เปลี่ยน" in _rule
    _has_nothing = "DO NOTHING" in _sql
    _has_update = re.search(r"ON CONFLICT[^;]*DO UPDATE", _sql, re.S) is not None
    if _says_skip and _has_update and not _has_nothing:
        _conflict_bad.append(f"{_f} :: idempotency บอกว่า 'ห้ามอัปเดตทับ' แต่ SQL เป็น ON CONFLICT DO UPDATE")
    if _says_update and _has_nothing and not _has_update:
        _conflict_bad.append(f"{_f} :: idempotency บอกว่า 'อัปเดตค่าที่เปลี่ยน' แต่ SQL เป็น DO NOTHING")
check("กติกา idempotency ขัดกับ SQL ในฉบับเดียวกัน", sorted(set(_conflict_bad)))

# ── #37 ตารางที่ SQL ในเอกสารแตะ ต้องประกาศใน "Reference DB Mapping" ของฉบับนั้น ────
#   เจอจริง 2026-09-02: 7 ฉบับมี SQL join ตารางที่หัวข้อ 8 ไม่ได้ประกาศ — dev ที่ตั้ง
#   repository/สิทธิ์จากหัวข้อ 8 จะพลาดตาราง แล้วไปเจอตอน runtime
_DECL = re.compile(r"\b(sgi_[a-z_0-9]+|workflow_[a-z_]+|business_user|common_code[a-z_]*|mas_param"
                   r"|email_[a-z]+|store|mas_store|sevenshop|fcs_qssi_score|juristic|fr_store|integration_log)\b")
_map_bad: list[str] = []
for _f in [_x for _x in DOC_FILES if _x.startswith(("LLDD/md/BE/", "LLDD/md/Jobs/"))]:
    _t = read(_f)
    _m = re.search(r"## 8\. Reference DB Mapping.*?\n(.*?)(?=\n## )", _t, re.S)
    if not _m:
        continue
    _declared = set(_DECL.findall(_m.group(1)))
    _sql = " ".join(re.findall(r"```sql\s*(.*?)```", _t, re.S))
    _used = {_u for _u in re.findall(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z_0-9.]*)", _sql)
             if _u.startswith(("sgi_", "sps_store."))}
    for _u in sorted(_used):
        if _u.split(".")[-1] not in _declared:
            _map_bad.append(f"{_f} :: SQL แตะ {_u} แต่ไม่ได้ประกาศในหัวข้อ 8 Reference DB Mapping")
check("ตารางที่ SQL แตะแต่ไม่ประกาศใน Reference DB Mapping", sorted(set(_map_bad)))


DROPPED = {"workflow_instances", "workflow_tasks", "workflow_sections", "document_statuses",
           "status_email_rules", "audit_logs", "job_configs", "job_run_histories",
           "email_templates", "system_configs", "roles", "menus", "menu_permissions",
           "user_accounts", "operator_assignments", "stores", "zones", "branch_types",
           "employees", "decisions"}
sql_bad = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    s = read(f)
    for m in re.finditer(r"\b(?:FROM|JOIN|INSERT INTO|UPDATE)\s+([a-z_0-9]+)", s):
        t = m.group(1)
        if t in DROPPED:
            line = s[:m.start()].count("\n") + 1
            ctx = s[max(0, m.start() - 120): m.start()]
            if "❌" in ctx or "ไม่สร้าง" in ctx or "ถูกตัด" in ctx or "ห้าม" in ctx:
                continue
            sql_bad.append(f"{f}:{line} → {t}")
check("SQL อ้างตารางที่ถูกตัดออกจากโครง", sql_bad)

def sql_blocks(text: str) -> str:
    """คืนเฉพาะเนื้อใน ```sql fence — กัน prose ภาษาไทยที่มีคำว่า UPDATE/FROM หลุดเข้ามา"""
    return "\n".join(m.group(1) for m in re.finditer(r"```sql\n(.*?)```", text, re.S))


def _split_defs(body: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


# คอลัมน์ NOT NULL ที่ไม่มี DEFAULT → INSERT ต้องส่งค่าเสมอ
required: dict[str, list[str]] = {}
all_cols: dict[str, set[str]] = {}
for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\((.*?)\n\);", ddl, re.S):
    name = m.group(1)
    body = "\n".join(l.split("--")[0] for l in m.group(2).split("\n"))
    req, cols = [], set()
    for d in _split_defs(body):
        d = d.strip()
        if not d or d.upper().startswith(("CONSTRAINT", "UNIQUE", "PRIMARY", "FOREIGN", "CHECK")):
            continue
        c = re.match(r"([a-z_0-9]+)\s+(.*)$", d, re.S)
        if not c:
            continue
        col, rest = c.group(1), " ".join(c.group(2).upper().split())
        cols.add(col)
        if "NOT NULL" in rest and "DEFAULT" not in rest and "SERIAL" not in rest and "PRIMARY KEY" not in rest:
            req.append(col)
    all_cols[name] = cols
    if req:
        required[name] = req

nn_bad = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    s_ = read(f)
    for m in re.finditer(r"INSERT INTO ([a-z_0-9]+)\s*\(([^)]*)\)", s_, re.S):
        t, raw = m.group(1), m.group(2)
        if t not in required or "TODO" in raw or "/*" in raw:
            continue
        cols = {c.strip() for c in raw.replace("\n", " ").split(",")}
        gap = [c for c in required[t] if c not in cols]
        if gap:
            nn_bad.append(f"{f}:{s_[:m.start()].count(chr(10))+1} {t} ขาด {', '.join(gap)}")
check("INSERT ขาดคอลัมน์ NOT NULL ที่ไม่มี DEFAULT", nn_bad)

# ตารางที่ SQL อ้างแต่ไม่มีทั้งใน DDL ของเราและใน schema ของระบบเดิม (จับชื่อที่พิมพ์ผิด/ตายไปแล้ว)
# object ที่ไม่ใช่ตารางของทั้งสองระบบแต่ถูกต้อง — system catalog + view ภายนอก
# คำสงวนที่ตามหลัง FROM/JOIN/UPDATE ได้ แต่ไม่ใช่ชื่อตาราง
_SQL_WORDS = {
    "set", "lateral", "of", "skip", "only", "all", "distinct", "nowait",
    "select", "where", "as", "on", "using", "share", "key", "no", "locked",
}
SQL_ALIAS_OK = {
    "dual", "unnest", "generate_series", "values", "json_to_recordset",
    "pg_locks",                                    # ตรวจ advisory lock กันรันซ้อน
    "allmap_seven_impact_view",                    # ชื่อเดิมที่เคยใช้ในเอกสาร — คงไว้กันของเก่าพัง
    "seven_impact_view",                           # allmapssa.SEVEN_IMPACT_VIEW (SQL Server GSMALLMAP) — Job 2
    "competitor_impact_view",                      # allmapssa.COMPETITOR_IMPACT_VIEW (SQL Server) — Job 3
    "allmap_competitor_impact_view",               # view คู่แข่งของ ALLMAP — Job 3
}
ghost = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    full = read(f)
    s_ = sql_blocks(full)
    # ชื่อ CTE ที่ประกาศในไฟล์เดียวกัน (WITH x AS (...) , y AS (...)) ไม่ใช่ตาราง
    ctes = set(re.findall(r"(?:WITH|,)\s+([a-z][a-z_0-9]*)\s+AS\s*\(", s_, re.I))
    ctes |= set(re.findall(r"RETURNING[^;]*?\)\s*(?:,)?\s*([a-z][a-z_0-9]*)\s+AS\s*\(", s_, re.I))
    # รองรับ schema qualifier ทุกแบบ ไม่ใช่แค่ sps_store. — วิวของ ALLMAP อยู่บน SQL Server
    # และเขียนเป็น allmapssa.SEVEN_IMPACT_VIEW (ตัวพิมพ์ใหญ่) เดิมจับ "allmapssa" มาเป็นชื่อตาราง
    # `IS NOT DISTINCT FROM x.col` มีคำว่า FROM แต่ตามด้วยคอลัมน์ ไม่ใช่ตาราง
    s_ = re.sub(r"IS\s+(?:NOT\s+)?DISTINCT\s+FROM", "IS_DISTINCT", s_, flags=re.I)
    for m in re.finditer(r"\b(?:FROM|JOIN|INSERT INTO|UPDATE)\s+(?:([A-Za-z][\w]*)\.)?([A-Za-z][\w]*)", s_):
        t = m.group(2).lower()
        if t in _SQL_WORDS:      # UPDATE ... SET · FOR UPDATE SKIP LOCKED · JOIN LATERAL ฯลฯ
            continue
        if t in created or t in EXISTING_TABLES or t in SQL_ALIAS_OK or t in DROPPED or t in ctes:
            continue
        ghost.append(f"{f} → {t}")
check("SQL อ้างตารางที่ไม่มีอยู่จริงเลย (ทั้งของเราและระบบเดิม)", ghost)

# จำนวน endpoint: plan-api.html (แหล่งจริง · ตัด /* */ ที่เป็นเส้นยกเลิกออก) ต้อง = CANON_ENDPOINTS
_plan = re.sub(r"/\*.*?\*/", "", read("plan-api.html"), flags=re.S)
_eps = re.findall(r"m:\s*'(GET|POST|PUT|PATCH|DELETE)'[^}]*?p:\s*'([^']+)'", _plan)
check(f"endpoint ที่ยังใช้งานใน plan-api.html = {CANON_ENDPOINTS}",
      [] if len(_eps) == CANON_ENDPOINTS else [f"นับได้ {len(_eps)}"])

# ทุกเส้นของ SGI ต้องอยู่ใต้ namespace /api/v1/sgi/ (มติ 2026-08-25)
# เหตุผล: SGI อยู่ใน store-backend ตัวเดิมที่มี /document /report /interface/... อยู่ก่อนแล้ว
check("endpoint ของ SGI ที่ไม่ได้อยู่ใต้ /api/v1/sgi/",
      [f"{m} {pth}" for m, pth in _eps if not pth.startswith("/api/v1/sgi/")])

# ต้องอยู่ในกลุ่มใดกลุ่มหนึ่งใน 6 กลุ่ม (ตรงกับ 6 กลุ่มใน api.md แบบ 1:1)
SGI_GROUPS = ("document", "lookup", "master", "report", "workflow", "interface")
check(f"endpoint ที่ไม่ได้อยู่ใน 6 กลุ่มของ sgi ({'/'.join(SGI_GROUPS)})",
      [f"{m} {pth}" for m, pth in _eps
       if pth.startswith("/api/v1/sgi/")
       and pth[len("/api/v1/sgi/"):].split("/")[0] not in SGI_GROUPS])

# api.md เขียนแบบรวมแถวได้ (GET/POST/PUT/DELETE | /a · /a/{id}) — ขยายแล้วต้องได้เท่ากัน
_api = read("api.md")
# นับเฉพาะในหัวข้อ "รายการ endpoint ทั้ง 6 กลุ่ม" — ท้ายไฟล์มีตารางของกลุ่มที่ถูกตัดออกแล้ว
_start = _api.index("## รายการ endpoint ทั้ง 6 กลุ่ม")
_end = _api.index("## กฎธุรกิจสำคัญที่ผูกกับ API", _start)
_scope = _api[_start:_end]
# นับเป็นคู่ (verb, path) ที่เขียนไว้ชัดเจน — เลิกเดาจาก "จำนวน verb ในแถวรวม" ซึ่งอ่านได้หลายแบบ
_pairs = set()
for _line in _scope.split("\n"):
    if not _line.startswith("|"):
        continue
    _cells = _line.split("|")
    # แบบ A (ชัดเจน): VERB `path` เขียนติดกัน — ใช้ได้ทุกคอลัมน์ เช่น "GET `/sgi/master/factors` · POST `/sgi/master/factors`"
    _explicit = re.findall(r"\b(GET|POST|PUT|PATCH|DELETE)\s+`(/[^`]+)`", _line)
    if _explicit:
        _pairs |= set(_explicit)
        continue
    # แบบ B (แถวเก่า): คอลัมน์แรกเป็น verb เดียว คอลัมน์ถัดไปเป็น path ใน backtick
    _m = re.match(r"^\s*(GET|POST|PUT|PATCH|DELETE)\s*$", _cells[1]) if len(_cells) > 2 else None
    if _m:
        for _pa in re.findall(r"`(/[^`]+)`", _cells[2]):
            _pairs.add((_m.group(1), _pa))
_n = len(_pairs)
check(f"endpoint ที่ api.md ระบุ (ขยายแถวรวม) = {CANON_ENDPOINTS}",
      [] if _n == CANON_ENDPOINTS else [f"นับได้ {_n} — api.md กับ plan-api.html ไม่ตรงกัน"])

# โครงหัวข้อของเอกสารส่งมอบ: เลขห้ามซ้ำ · ห้ามข้ามเลขระดับบน · h2 ห้ามใส่เลขทศนิยม
import collections as _c
head_dup, head_gap, head_lvl = [], [], []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    t = read(f)
    tops = [int(x) for x in re.findall(r"^## ([0-9]+)\.", t, re.M)]
    if tops:
        for n in range(1, max(tops) + 1):
            if n not in tops:
                head_gap.append(f"{f} → ไม่มีหัวข้อ {n}")
    for k, v in _c.Counter(re.findall(r"^#{2,4}\s+([0-9]+(?:\.[0-9]+)*)\s", t, re.M)).items():
        if v > 1:
            head_dup.append(f"{f} → หัวข้อ {k} ซ้ำ {v} ครั้ง")
    for m in re.finditer(r"^## ([0-9]+\.[0-9]+) ", t, re.M):
        head_lvl.append(f"{f} → '## {m.group(1)}' ควรเป็น h3")
check("เลขหัวข้อซ้ำในเอกสารเดียวกัน", head_dup)
check("เลขหัวข้อระดับบนกระโดด (ขาดเลข)", head_gap)
check("h2 ที่ใส่เลขทศนิยม (ควรเป็น h3)", head_lvl)

# ฟีเจอร์/ตารางที่ถูกตัดไปแล้ว ห้ามถูกอ้างแบบ "สั่งให้ทำ" (อ้างได้เฉพาะเมื่อมีคำกำกับว่าตัดแล้ว)
CUT_FEATURES = {
    "operator_assignments": "ตาราง operator (ตัด 2026-08-05)",
    "menu_permissions": "สิทธิ์เมนู (ตัด 2026-08-05)",
    "system_configs": "Global Config (ตัด 2026-08-06)",
    "email_templates": "หน้า Email Template (ตัด 2026-08-06)",
    "k2-list-abnormal": "หน้าข้อมูลผิดปกติ (ลบ 2026-08-06)",
    "job_configs": "Batch Job Admin (ตัด 2026-08-06)",
    "job_run_histories": "Batch Job Admin (ตัด 2026-08-06)",
    "audit_logs": "ระบบ audit ของ master (ยกเลิก 2026-08-07)",
    "status_email_rules": "ตารางกฎอีเมล (ตัด 2026-08-14)",
    "workflow_tasks": "ตาราง workflow ของ SGI (ตัด 2026-08-06)",
}
_okctx = re.compile(r"ตัด|ยกเลิก|ลบ|ไม่สร้าง|ไม่มี|❌|~~|ถูกเอาออก|แทนด้วย|เดิม|removed|dropped")
cut_bad = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    lines = read(f).split("\n")
    for i, line in enumerate(lines, 1):
        if _okctx.search(line):
            continue
        for k, label in CUT_FEATURES.items():
            if k in line:
                cut_bad.append(f"{f}:{i} {k} — {label}")
check("อ้างฟีเจอร์ที่ถูกตัดโดยไม่มีคำกำกับ", cut_bad)

# ชั่วโมงต้องตรงกันทุกที่ที่ประกาศ: README · CSV · portal · main index · LLDD-To-Be
import csv as _csv
hour_bad = []
_readme = read("LLDD/md/README.md")
_m = re.search(r"Total estimate:\s*(\d+)\s*hours\s*\(implementation (\d+) \+ unit test (\d+)\)", _readme)
if not _m:
    hour_bad.append("LLDD/md/README.md อ่านบรรทัด Total estimate ไม่ได้")
else:
    GRAND, IMPL, UT = (int(x) for x in _m.groups())
    if IMPL + UT != GRAND:
        hour_bad.append(f"README: {IMPL} + {UT} != {GRAND}")
    with io.open("LLDD/Main-Index-FE-BE-Job.csv", encoding="utf-8-sig") as fh:
        rows = list(_csv.DictReader(fh))
    # แถวที่ "นับในยอดรวม" = N คือ role pack ที่ชั่วโมงถูกนับไว้ที่ FE - Document Detail แล้ว
    # (มีอยู่ใน CSV เพื่อให้เห็นครบ 37 ฉบับ แต่ต้องไม่บวกซ้ำ)
    _counted = [r for r in rows if (r.get("นับในยอดรวม") or "Y").strip().upper() != "N"]
    c_tot = sum(int(r["ชั่วโมงรวม"]) for r in _counted)
    c_impl = sum(int(r["implementation"]) for r in _counted)
    c_ut = sum(int(r["unit test"]) for r in _counted)
    if (c_tot, c_impl, c_ut) != (GRAND, IMPL, UT):
        hour_bad.append(f"CSV รวม {c_tot}/{c_impl}/{c_ut} != README {GRAND}/{IMPL}/{UT}")
    _sys_path = os.path.join(ROOT, "tools")
    if _sys_path not in sys.path:
        sys.path.insert(0, _sys_path)
    import build_lldd_documents as _BL  # noqa: E402
    _norm = {t.title.replace("LLDD ", "", 1): t for t in _BL.topics()}
    _csv_titles = {r["หัวข้อ"].strip() for r in rows}
    for _miss in sorted(set(_norm) - _csv_titles):
        hour_bad.append(f"CSV ขาดเอกสาร: {_miss}")
    for r in rows:
        _t = _norm.get(r["หัวข้อ"].strip())
        if not _t:
            hour_bad.append(f"CSV มีแถวที่ไม่ใช่เอกสารจริง: {r['หัวข้อ']}")
            continue
        _want = (_BL.total_hours(_t), _t.hours, _BL.unit_test_hours(_t))
        _got = (int(r["ชั่วโมงรวม"]), int(r["implementation"]), int(r["unit test"]))
        if _want != _got:
            hour_bad.append(f"CSV {r['หัวข้อ']} ชั่วโมง {_got} != {_want}")
        _flag = (r.get("นับในยอดรวม") or "Y").strip().upper()
        _should = "N" if _BL.is_document_detail_role_doc(_t.file) else "Y"
        if _flag != _should:
            hour_bad.append(f"CSV {r['หัวข้อ']} คอลัมน์ 'นับในยอดรวม' = {_flag} ควรเป็น {_should}")
    if f"<b>{GRAND}</b>" not in read("LLDD/index.html"):
        hour_bad.append(f"portal LLDD/index.html ไม่ได้แสดง {GRAND} ชั่วโมง")
    _tobe = read("LLDD/md/LLDD-To-Be.md")
    # โครงใหม่: แถว "รวมงานที่ To-Be เพิ่ม" + แถว TB-0 (ฐานราก · ไม่นับเป็นเวลาของ To-Be) ต้องบวกได้ยอดรวมทั้งชุด
    _add = re.search(r"\*\*รวมงานที่ To-Be เพิ่ม\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(\d+)\*\*", _tobe)
    _base = re.search(r"\|\s*TB-0\s*\|[^|]*\|[^|]*\|\s*\*(\d+)\*\s*\|\s*\*(\d+)\*\s*\|\s*\*(\d+)\*", _tobe)
    if not _add or not _base:
        hour_bad.append("LLDD-To-Be อ่านแถวสรุป (รวมงานที่ To-Be เพิ่ม / TB-0 ฐานราก) ไม่ได้")
    else:
        _a = [int(x) for x in _add.groups()]
        _b = [int(x) for x in _base.groups()]
        if _a[0] + _a[1] != _a[2]:
            hour_bad.append(f"LLDD-To-Be แถว To-Be: FE {_a[0]} + BE {_a[1]} != {_a[2]}")
        if _b[0] + _b[1] != _b[2]:
            hour_bad.append(f"LLDD-To-Be แถว TB-0: FE {_b[0]} + BE {_b[1]} != {_b[2]}")
        if _a[2] + _b[2] != GRAND:
            hour_bad.append(f"LLDD-To-Be: To-Be {_a[2]} + ฐานราก {_b[2]} = {_a[2] + _b[2]} != {GRAND}")
    _mi = read("LLDD/md/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.md")
    # นับเฉพาะหัวข้อ 4 (ภาระงานต่อคน) — หัวข้อ 3 ใช้รูปแบบเดียวกันแต่เป็นรายเอกสาร
    _s4 = _mi[_mi.index("## 4. Workload Balance"): _mi.index("## 5. ")]
    owner_tot = sum(int(x) for x in re.findall(r"\*\*(\d+)\*\* \(impl \d+ \+ test \d+\)", _s4))
    if owner_tot != GRAND:
        hour_bad.append(f"main index ผลรวมต่อคน {owner_tot} != {GRAND}")
check("ชั่วโมงไม่ตรงกันระหว่างไฟล์ (README/CSV/portal/main index/To-Be)", hour_bad)

# ชั่วโมง unit test กับหัวข้อ Unit Test Scope ต้องมาคู่กันเสมอ (ห้ามคิดเงินแต่ไม่บอกว่าเทสอะไร)
ut_bad = []
for f in glob.glob("LLDD/md/FE/*.md") + glob.glob("LLDD/md/BE/*.md") + glob.glob("LLDD/md/Jobs/*.md"):
    t = read(f)
    has_hours = bool(re.search(r"unit test (\d+) \(\d+%\)", t))
    has_scope = "## " in t and re.search(r"^#{1,3} \d+\. Unit Test Scope", t, re.M) is not None
    if has_hours and not has_scope:
        ut_bad.append(f"{f} มีชั่วโมง unit test แต่ไม่มีหัวข้อ Unit Test Scope")
    if has_scope and not has_hours:
        ut_bad.append(f"{f} มีหัวข้อ Unit Test Scope แต่ไม่มีชั่วโมงใน Overview")
    if has_scope:
        sec = t[t.index("Unit Test Scope"):]
        sec = sec.split("\n## ")[0]
        cases = [l for l in sec.split("\n") if l.startswith("| ") and "---" not in l]
        if len(cases) - 1 < 5:
            ut_bad.append(f"{f} Unit Test Scope มีเพียง {max(len(cases)-1,0)} เคส (ควร >= 5)")
check("ชั่วโมง unit test ไม่มีหัวข้อขอบเขตกำกับ", ut_bad)

# ทุกเอกสารต้องบอก repo ปลายทาง
repo_bad = [f for f in glob.glob("LLDD/md/FE/*.md") + glob.glob("LLDD/md/BE/*.md") + glob.glob("LLDD/md/Jobs/*.md")
            if "Target repository" not in read(f)]
check("เอกสารไม่ระบุ repo ปลายทาง", repo_bad)

# ---------------------------------------------------------------- C. ฝั่ง HTML
import glob as _g
_html = sorted(_g.glob("*.html"))
_contract = [f for f in _html if "assets/sbp.js" in read(f)]
_standalone = [f for f in _html if f not in _contract]

# หน้าที่ใช้ sbp.js ต้องครบ page contract: data-page + <aside id="sidebar"></aside> ว่าง
contract_bad = []
for f in _contract:
    t = read(f)
    if "data-page=" not in t:
        contract_bad.append(f"{f} ไม่มี data-page")
    if not re.search(r'<aside id="sidebar">\s*</aside>', t):
        contract_bad.append(f"{f} #sidebar ไม่ว่าง (sbp.js เป็นคนเติม)")
check("หน้า HTML ผิด page contract", contract_bad)

# CLAUDE.md ต้องบอกจำนวนหน้าให้ตรงของจริง
_claude = read("CLAUDE.md")
_m = re.search(r"\*\*(\d+) contract pages\*\*", _claude)
# เจอจริง 2026-09-08: ประโยคเดียวกันมีเลขสองตัว ("19 contract pages ... two of the 18")
# ตัวแรกถูกอัปเดต ตัวหลังค้าง — จึงต้องตรวจ *ทุก* เลขที่อ้างชุดหน้า contract ในประโยคนั้น
_pg_bad = []
for _m2 in re.finditer(r"two of the (\d+) are kept-for-reference", _claude):
    if int(_m2.group(1)) != len(_contract):
        _pg_bad.append(f"CLAUDE.md :: 'two of the {_m2.group(1)}' แต่ของจริงมี {len(_contract)} contract page")
# จำนวนหน้า prototype ที่เอกสารแผนงานอ้าง (ไม่นับ index.html ที่เป็น redirect stub)
_pages_real = len([f for f in _html if f != "index.html"])
for _f2 in ("DECISIONS-รอตัดสินใจ.md",):
    if not os.path.exists(_f2):
        continue
    for _m3 in re.finditer(r"prototype \*\*(\d+) หน้า\*\*", read(_f2)):
        if int(_m3.group(1)) != _pages_real:
            _pg_bad.append(f"{_f2} :: 'prototype {_m3.group(1)} หน้า' แต่ของจริง {_pages_real} "
                           "(นับ *.html ทั้งหมด ไม่รวม index.html ที่เป็น redirect stub)")
check("จำนวนหน้า prototype ที่เอกสารอ้าง ไม่ตรงของจริง", sorted(set(_pg_bad)))

check("จำนวน contract page ใน CLAUDE.md ไม่ตรงของจริง",
      [] if (_m and int(_m.group(1)) == len(_contract))
      else [f"CLAUDE.md บอก {_m.group(1) if _m else '?'} · ของจริง {len(_contract)}"])

# MODULES ต้องไม่ชี้ไฟล์ที่ไม่มี
_js = read("assets/sbp.js")
_mods = _js[_js.index("var MODULES"): _js.index("\n  ];", _js.index("var MODULES"))]
_active = "\n".join(l for l in _mods.split("\n") if not l.strip().startswith("//"))
check("MODULES ชี้ไฟล์ HTML ที่ไม่มีจริง",
      [f"MODULES → {h}" for h in set(re.findall(r"href:'([^']+)'", _active)) if not os.path.exists(h)])

# ทุก data-entity ต้องมีใน SCHEMAS ของ sbp.js
_i = _js.index("var SCHEMAS = {")
_depth, _end = 0, _i
for _k in range(_i + len("var SCHEMAS = "), len(_js)):
    if _js[_k] == "{":
        _depth += 1
    elif _js[_k] == "}":
        _depth -= 1
        if _depth == 0:
            _end = _k
            break
_schemas = set(re.findall(r"^\s{4}(\w+)\s*:\s*\[", _js[_i:_end], re.M))
ent_bad = []
for f in _html:
    for m in re.finditer(r'data-entity="([^"]+)"', read(f)):
        if m.group(1) not in _schemas and m.group(1) != "k2doc":
            ent_bad.append(f"{f} → data-entity={m.group(1)} ไม่มีใน SCHEMAS")
check("data-entity ที่ไม่มี SCHEMAS รองรับ", ent_bad)

# inline <script> ทุกหน้าต้อง parse เป็น JS ได้จริง
# นับวงเล็บเอาไม่ได้ — ข้อความไทย/SQL ในสตริงมีวงเล็บเดี่ยวเต็มไปหมด จึงใช้ node parse ตรง ๆ
import shutil as _sh
import subprocess as _sp
sc_bad = []
if _sh.which("node"):
    _probe = r"""
const fs=require('fs');
let bad=[];
for (const f of process.argv.slice(1)) {
  const h=fs.readFileSync(f,'utf8');
  const ms=[...h.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)];
  ms.forEach((m,i)=>{ try{ new Function(m[1]); }catch(e){ bad.push(f+' script#'+i+' : '+e.message); } });
}
process.stdout.write(bad.join('\n'));
"""
    out = _sp.run(["node", "-e", _probe, *_html], capture_output=True, text=True).stdout.strip()
    sc_bad = [l for l in out.split("\n") if l]
    check("inline <script> parse ไม่ผ่าน", sc_bad)
else:
    check("inline <script> parse ไม่ผ่าน (ข้าม — ไม่พบ node)", [])

links = []
for f in glob.glob("*.md") + glob.glob("LLDD/md/**/*.md", recursive=True):
    base = os.path.dirname(f)
    for m in re.finditer(r"\[[^\]]*\]\(([^)#][^)]*)\)", read(f)):
        t = m.group(1).split("#")[0].strip()
        if not t or t.startswith(("http", "mailto")):
            continue
        if not os.path.exists(os.path.join(base, t)) and not os.path.exists(t):
            links.append(f"{f} → {t}")
check("ลิงก์ชี้ไฟล์ที่ไม่มีจริง", links)

def _cells(row: str) -> int:
    """นับช่องของแถวตาราง — ตัด \\| ที่ escape และ pipe ใน `inline code` ออกก่อน"""
    row = row.replace("\\|", "")
    row = re.sub(r"`[^`]*`", "", row)
    return row.count("|")


tbl_bad = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True) + glob.glob("*.md"):
    lines = read(f).split("\n")
    for i, ln in enumerate(lines[:-2]):
        if not ln.startswith("|") or not re.match(r"^\|[\s:| -]+\|$", lines[i + 1] or ""):
            continue
        want = _cells(ln)
        for j in range(i + 2, len(lines)):
            row = lines[j]
            if not row.startswith("|"):
                break
            got = _cells(row)
            if got != want:
                tbl_bad.append(f"{f}:{j+1} ({got} ช่อง ≠ หัวตาราง {want})")
check("ตาราง markdown จำนวนช่องไม่ตรงหัวตาราง", tbl_bad)

docs = [f for f in glob.glob("LLDD/md/**/*.md", recursive=True)
        if os.path.basename(f) not in {"README.md"}]
check(f"จำนวนเอกสาร LLDD = {CANON_DOCS}",
      [] if len(docs) == CANON_DOCS + 1 else [f"นับได้ {len(docs)} (รวม main index)"])

WATCH = {t for t in schema if t.startswith("workflow") or t in {
    "email_template", "email_sent", "business_user", "common_code", "mas_param",
    "integration_log", "upload_general", "fcs_qssi_score", "store", "mas_store",
    "mas_zone", "fml_email_account"}}

qual = re.compile(r"sps_store\.([a-z_0-9]+)")
dotted = re.compile(r"\b(" + "|".join(sorted(WATCH, key=len, reverse=True)) + r")\.([a-z_][a-z_0-9]*)\b")
fn = re.compile(r"\b(triggerEvent|addPreparedApprover|getPendingFlow|eventWorkflow|initializeWorkflow|"
                r"getPermissionEvents|getHistory|getTransaction|getPendingFlowByUser|"
                r"getWorkflowsByUser|addPreApprover)\s*\(")

tbl_miss, col_miss, fn_bad, mail_bad = [], [], [], []
for f in DOC_FILES:
    try:
        s = read(f)
    except Exception:
        continue
    for t in set(qual.findall(s)):
        if t not in schema and t not in NOT_COLUMN and not t.endswith("_"):
            tbl_miss.append(f"{f} :: sps_store.{t}")
    for t, c in set(dotted.findall(s)):
        if c in NOT_COLUMN or c.isdigit():
            continue
        if t in schema and c not in schema[t]:
            col_miss.append(f"{f} :: {t}.{c}")
    for name in set(fn.findall(s)):
        if name not in ENGINE_API:
            fn_bad.append(f"{f} :: {name}()")
    if "email_sent" in s or "email_template" in s:
        for bad, good in EMAIL_DOC_ONLY.items():
            for m in re.finditer(r"(?<![a-z_`])" + bad + r"(?![a-z_])", s):
                ctx = s[max(0, m.start() - 130): m.start() + 60].replace("\n", " ")
                if re.search(r"ไม่ใช่|ควรเป็น|เสนอ|ไม่ตรง|production คือ|เอกสาร lib", ctx):
                    continue
                mail_bad.append(f"{f} :: {bad} → ควรเป็น {good}")

check("ตาราง sps_store ที่อ้างแต่ไม่มีจริง", tbl_miss)
check("คอลัมน์ของตารางระบบเดิมที่ไม่มีจริง", col_miss)
check("ชื่อ function ของ engine นอก API 8 ตัว", fn_bad)
check("ใช้ชื่อคอลัมน์ email ผิดแบบสั่งให้ทำตาม", mail_bad)

# ---------------------------------------- worklist.html ต้องตรงกับ LLDD (งานที่ต้อง trigger event)
wl_bad: list[str] = []
_wl = os.path.join(ROOT, "worklist.html")
if os.path.exists(_wl):
    import json as _json

    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import build_lldd_documents as B  # noqa: E402

    with open(_wl, encoding="utf-8") as _fh:
        _m = re.search(r"const DATA = (\{.*?\});", _fh.read(), re.S)
    if not _m:
        wl_bad.append("worklist.html :: หา const DATA ไม่เจอ — สร้างใหม่ด้วย tools/build_worklist.py")
    else:
        _tasks = _json.loads(_m.group(1))["tasks"].values()
        _have = {t["file"].rsplit("/", 1)[-1] for t in _tasks if t.get("triggerEvent")}
        _want = set(B.WORKFLOW_TRIGGER_CONTRACTS)
        for _k in sorted(_want - _have):
            wl_bad.append(f"worklist.html :: {_k} มีหัวข้อ trigger event ใน LLDD แต่การ์ดงานไม่แสดง")
        for _k in sorted(_have - _want):
            wl_bad.append(f"worklist.html :: {_k} แสดง trigger event แต่ LLDD ไม่มีหัวข้อนี้")
        _steps = B.dependency_steps(B.topics())
        for _t in _tasks:
            _s = _steps.get(_t["file"])
            if _s is not None and _t.get("step") not in (None, _s):
                wl_bad.append(f"worklist.html :: {_t['file']} step {_t.get('step')} ≠ {_s} ของ LLDD")

        # ตาราง runtime ของ engine ห้ามมีป้าย "W" เปล่า — ต้องกำกับว่าเขียนผ่าน lib
        for _t in _tasks:
            for _r in _t.get("dbTables", []):
                _n = str(_r[0]).split("(")[0].strip().split("/")[0].strip()
                if _n.startswith("workflow") and re.fullmatch(r"\s*W\s*", str(_r[1])):
                    wl_bad.append(
                        f"{_t['file']} :: {_r[0]} ป้าย R/W = 'W' เปล่า — ต้องเป็น 'W (ผ่าน lib)' "
                        "เพราะ SGI ห้าม INSERT/UPDATE ตาราง engine ตรง"
                    )

check("worklist.html ไม่ตรงกับ LLDD (trigger event / ลำดับขั้น)", wl_bad)

# LLDD/index.html (พอร์ทัล) กับ LLDD/md/README.md สร้างโดย build_document_portal() ซึ่ง **รันเฉพาะตอน
# build เต็ม --formats md,docx,pdf** เท่านั้น · ถ้าใครรัน --formats md อย่างเดียว พอร์ทัลจะค้างเวอร์ชันเก่า
# เงียบ ๆ (เจอจริง 2026-09-02: index.html ยังเขียน "Job 1-10" และชั่วโมง role pack ไม่เป็นตัวเลข)
portal_bad: list[str] = []
_portal = os.path.join(ROOT, "LLDD", "index.html")
_readme = os.path.join(ROOT, "LLDD", "md", "README.md")
if os.path.exists(_portal):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import build_lldd_documents as _B  # noqa: E402
    _html = read(_portal)
    _rd = read(_readme) if os.path.exists(_readme) else ""
    _topics = {t.file: t for t in _B.topics()}
    _rows = {}
    for _r in re.findall(r"<tr>(.*?)</tr>", _html, re.S):
        _m = re.search(r'href="pdf/([^"]+)\.pdf"', _r)
        if _m:
            _rows[_m.group(1)] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _r)).strip()
    for _k, _t in _topics.items():
        if _k not in _rows:
            portal_bad.append(f"index.html ไม่มีแถวของ {_k}")
            continue
        _row, _h = _rows[_k], _B.total_hours(_t)
        if f"{_h}h" not in _row:
            portal_bad.append(f"index.html :: {_k} ไม่แสดงชั่วโมง {_h}h (ต้องเป็นตัวเลขเสมอ) → {_row[:80]}")
        _own = _t.owner.split("<")[1].split(">")[0] if "<" in _t.owner else _t.owner.split()[0]
        if _own not in _row:
            portal_bad.append(f"index.html :: {_k} เจ้าของไม่ตรง (ควรเป็น {_own})")
        if _rd and f"| {_B.doc_id(_t)} |" not in _rd:
            portal_bad.append(f"README.md ไม่มีแถวของ {_B.doc_id(_t)}")
    for _l in re.findall(r'href="([^"]+)"', _html):
        if not _l.startswith(("http", "#")) and not os.path.exists(os.path.join(ROOT, "LLDD", _l)):
            portal_bad.append(f"index.html ลิงก์ไปไฟล์ที่ไม่มีจริง: {_l}")
    _txt = re.sub(r"<[^>]+>", " ", _html)
    _jobs = sorted({j for j in re.findall(r"LLDD-BE-Job-(\d+b?)-", "\n".join(_topics))})
    if "Job 1-10" in _txt and "1" not in _jobs:
        portal_bad.append("index.html ยังเขียน 'Job 1-10' ทั้งที่ Job 1 ถูกตัดออกแล้ว")
    _grand = sum(_B.total_hours(t) for t in _topics.values() if not _B.is_document_detail_role_doc(t.file))
    if str(_grand) not in _txt:
        portal_bad.append(f"index.html ไม่แสดงยอดชั่วโมงรวม {_grand}")
check("LLDD/index.html ไม่ตรงกับชุด md (ต้อง build เต็ม md,docx,pdf)", portal_bad)

# ทุกที่ที่เขียน sgi_<ตาราง>.<คอลัมน์> ต้องมีคอลัมน์นั้นจริงใน DDL
# (เจอจริง 2026-09-02: sgi_consideration_logs.actor_user_id ที่คอลัมน์จริงคือ consider_by
#  และ sgi_impacted_stores.transfer_sbp_date ที่ entity ใน LLDD map ไว้แต่ DDL ยังไม่มี)
sgi_col_bad: list[str] = []
_own_cols: dict[str, list[str]] = {}
for _m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\((.*?)\n\);", ddl, re.S):
    _body = re.sub(r"--[^\n]*", "", _m.group(2))
    _parts, _depth, _cur = [], 0, ""
    for _ch in _body:
        if _ch == "(":
            _depth += 1
        if _ch == ")":
            _depth -= 1
        if _ch == "," and _depth == 0:
            _parts.append(_cur); _cur = ""
        else:
            _cur += _ch
    _parts.append(_cur)
    _own_cols[_m.group(1)] = [
        _x.strip().split()[0] for _x in _parts
        if _x.strip() and not _x.strip().upper().startswith(
            ("CONSTRAINT", "PRIMARY KEY", "UNIQUE", "CHECK", "FOREIGN KEY"))
    ]
for _f in DOC_FILES + ["CLAUDE.md", "database.md", "api.md", "workflow.md"]:
    if not os.path.exists(_f):
        continue
    for _m in re.finditer(r"\b(sgi_[a-z_0-9]+)\.([a-z_][a-z_0-9]*)\b", read(_f)):
        _tb, _c = _m.group(1), _m.group(2)
        if _tb in _own_cols and _c not in _own_cols[_tb]:
            _msg = f"{_f} :: {_tb}.{_c} ไม่มีคอลัมน์นี้ใน DDL"
            if _msg not in sgi_col_bad:
                sgi_col_bad.append(_msg)
check("อ้างคอลัมน์ของตาราง SGI ที่ไม่มีใน DDL", sgi_col_bad)

# endpoint เดียวกันที่ประกาศในหลายเอกสาร LLDD ต้องไม่ใช้ "ชื่อฟิลด์คนละชื่อสำหรับของเดียวกัน"
# (เจอจริง 2026-09-02: attachmentId ฝั่ง FE vs attachId ฝั่ง BE · waitingDays vs daysPending)
api_field_bad: list[str] = []
_syspath = os.path.join(ROOT, "tools")
if _syspath not in sys.path:
    sys.path.insert(0, _syspath)
import build_lldd_documents as _BA  # noqa: E402
# ชื่อที่ถือเป็น "คู่ขัดกัน" — ถ้าเจอทั้งคู่ในชุดเอกสารเดียวกันของ endpoint เดียวกัน ให้ฟ้อง
_ALIAS_PAIRS = [("attachId", "attachmentId"), ("daysPending", "waitingDays"),
                ("compensateAmount", "compensationAmount"), ("roundNo", "round"),
                ("editableSections", "canEditSections"), ("ageHours", "ageDays"),
                # เจอจริง 2026-09-02: POST /sgi/interface/sta/ack ถูกนิยาม 2 ที่ด้วยชื่อคนละชุด
                # (plan-api.html ใช้ trackingId/receiveDate · ApiSpec ใน generator ใช้ transactionId/receivedAt)
                # STA เป็นทีมภายนอก — implement ได้ชุดเดียวเท่านั้น
                ("trackingId", "transactionId"), ("receiveDate", "receivedAt")]
_ep_fields: dict[tuple[str, str], dict[str, set[str]]] = {}
for _t in _BA.topics():
    for _a in _t.apis:
        if not _a.path.startswith("/api/v1/sgi") or "*" in _a.path:
            continue
        # ตรวจทั้ง request และ response — การขัดกันของ sta/ack (2026-09-02) อยู่ที่ "request" ล้วน ๆ
        _keys = set()
        for _payload in (_a.response, _a.request):
            if _payload:
                _keys |= set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', _BA.api_json(_payload)))
        _ep_fields.setdefault((_a.method, _a.path), {})[_t.file] = _keys
for _ep, _docs in _ep_fields.items():
    _seen = {}
    for _doc, _keys in _docs.items():
        for _k in _keys:
            _seen.setdefault(_k, []).append(_doc)
    for _x, _y in _ALIAS_PAIRS:
        if _x in _seen and _y in _seen:
            api_field_bad.append(
                f"{_ep[0]} {_ep[1]} :: ใช้ทั้ง '{_x}' ({_seen[_x][0]}) และ '{_y}' ({_seen[_y][0]}) — ต้องเลือกชื่อเดียว")
# ชื่อฟิลด์ในตัวอย่าง response ของ plan-api.html ต้องไม่ขัดกับชุดเอกสาร LLDD ด้วย
_plan_res = re.sub(r"/\*.*?\*/", "", read("plan-api.html"), flags=re.S)
for _blk in re.findall(r"m:\s*'(?:GET|POST|PUT|PATCH|DELETE)',\s*p:\s*'(/api/v1/sgi[^']+)'(.*?)(?=\n\s*\{\s*m:|\n\s*\];)", _plan_res, re.S):
    _path, _body = _blk
    # ตรวจทั้ง res: และ req: — ความขัดกันของ POST /sgi/interface/sta/ack (2026-09-02) อยู่ใน req: ล้วน ๆ
    _pf: set[str] = set()
    for _key in ("res", "req"):
        _r = re.search(_key + r":'((?:[^'\\]|\\.)*)'", _body)
        if _r:
            _pf |= set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', _r.group(1)))
    if not _pf:
        continue
    _lf: set[str] = set()
    for _ep, _docs in _ep_fields.items():
        if _ep[1] == _path:
            for _k in _docs.values():
                _lf |= _k
    for _x, _y in _ALIAS_PAIRS:
        if (_x in _pf and _y in _lf) or (_y in _pf and _x in _lf):
            _m2 = f"{_path} :: plan-api.html กับ LLDD ใช้ชื่อฟิลด์ต่างกัน ('{_x}' / '{_y}')"
            if _m2 not in api_field_bad:
                api_field_bad.append(_m2)
check("ชื่อฟิลด์ API ขัดกันระหว่างเอกสาร", api_field_bad)

# ── #38 จำนวน batch job ต้องตรงกันทุกไฟล์ที่พูดถึง ─────────────────────────────
#   เจอจริง 2026-09-02: เพิ่ม Job 11/12 แล้วแต่ api.md / plan-flow.html / flow-fgi.html /
#   workflow.md ยังเขียน "Jobs 2-10 + 8b" หรือ "11 jobs" อยู่ — แหล่งความจริงคือ JOBS ใน job-batch.html
_job_nos = {str(_j.get("no")) for _j in _BA.read_js_array_from_html("job-batch.html", "JOBS")}
_job_count = len(_job_nos)
_count_bad: list[str] = []
for _f in ["api.md", "workflow.md", "plan-flow.html", "flow-fgi.html", "CLAUDE.md", "database.md"]:
    _t = read(_f)
    for _m in re.finditer(r"(?:ทั้ง|รวม)?\s*(\d+)\s*(?:jobs|job|entry point|ตัว)\b", _t):
        _n = int(_m.group(1))
        # สนใจเฉพาะประโยคที่พูดถึง batch job จริง ๆ
        _ctx = _t[max(0, _m.start() - 90):_m.end() + 40]
        if ("batch" in _ctx.lower() or "Batch" in _ctx or "Jobs" in _ctx) and 8 <= _n <= 20 and _n != _job_count:
            _count_bad.append(f"{_f} :: เขียนว่า {_n} job แต่ JOBS ใน job-batch.html มี {_job_count} ตัว")
check(f"จำนวน batch job ไม่ตรงกับ JOBS ({_job_count} ตัว)", sorted(set(_count_bad)))

# ── #39 job ใหม่ต้องถูกประกาศใน JOB_DEPENDENCIES ────────────────────────────────
#   เจอจริง 2026-09-02: Job 11/12 ไม่อยู่ในกราฟ ทำให้ worklist จัดคิวให้เริ่มตั้งแต่ขั้น 3
#   ทั้งที่ Job 11 ต้องรอ Job 6 และ Job 12 ต้องรอ Job 8b — แผนงานรายสัปดาห์จึงสั้นกว่าจริง
_dep_bad = [
    f"Job {_n} ไม่มีใน JOB_DEPENDENCIES — worklist จะจัดคิวให้เริ่มเร็วเกินจริง"
    for _n in sorted(_job_nos - set(_BA.JOB_DEPENDENCIES) - {"2"})   # Job 2 เป็นต้นสาย ไม่มี predecessor
]
check("job ที่ไม่ได้ประกาศ dependency", _dep_bad)

# ── #40 ค่า result ที่ FE ส่ง ต้องเป็น 7-enum verbatim ─────────────────────────
#   BE ตรวจ result แบบตรงตัว — เจอจริง 2026-09-02: role 01/02/03/06 ใส่ "ป้ายปุ่ม"
#   ลงช่อง value ทำให้ 4 ใน 5 บทบาทจะได้ 422 ตอน submit ทั้งที่ไม่มีใครเขียนผิด
_RESULT_ENUM = {
    "เห็นควรชดเชย", "เห็นควรไม่ชดเชย", "หยุดชดเชยประกันรายได้",
    "ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "ส่งเจ้าหน้าที่ SBP DSA",
    "คำนวณเงินชดเชยเรียบร้อย", "ส่งกลับ",
}
_enum_val_bad: list[str] = []
for _f in [_x for _x in DOC_FILES if "LLDD-FE-Document-Detail-Role-" in _x]:
    for _m in re.finditer(r'"value": "([^"]+)"', read(_f)):
        if _m.group(1) not in _RESULT_ENUM:
            _enum_val_bad.append(f"{_f} :: actionOptions.value = '{_m.group(1)}' ไม่อยู่ใน 7-enum ของ result")
check("ค่า result ของ FE ไม่อยู่ใน 7-enum", sorted(set(_enum_val_bad)))

# ── #41 อ้าง email template นอกชุด 8 ฉบับของระบบ SBP เดิม ────────────────────
#   SGI อ่าน email_template ของระบบเดิมอย่างเดียว สร้าง template ใหม่เองไม่ได้
#   เจอจริง 2026-09-02: LLDD Job 12 ตั้ง "EM-09 เตือนงานค้าง" ขึ้นมาเอง ทั้งที่ EM-04/EM-05
#   คือ "เตือนรายสัปดาห์" และ "escalation" ที่มีอยู่แล้วตรงกับงานนั้นพอดี
_em_bad = [
    f"{_f} :: อ้าง {_m.group(0)} แต่ชุด template ของระบบเดิมมีแค่ EM-01…EM-08"
    for _f in DOC_FILES
    for _m in re.finditer(r"\bEM-(?:09|1[0-9])\b", read(_f))
]
check("อ้าง email template นอกชุด EM-01…EM-08", sorted(set(_em_bad)))

# ── #42 SRS ที่ส่งมอบต้องมี job ครบเท่า JOBS ────────────────────────────────────
#   build_integrated_srs.py อ่าน snapshot tmp/prototype_data.json — ถ้า snapshot เก่า
#   SRS จะถูกสร้างจากข้อมูลเก่าโดยไม่ error (เจอจริง 2026-09-02: SRS พิมพ์แค่ 10 job
#   ทั้งที่เพิ่ม Job 11/12 ไปแล้ว) · build ตัวนั้นมี guard เรื่องเวลาไฟล์แล้ว
#   ข้อนี้ตรวจ "ผลลัพธ์ที่ส่งมอบจริง" อีกชั้น เผื่อมีคนรัน build ก่อนแล้วลืม re-extract
_srs_md = "output/srs/SRS-ระบบประกันรายได้-SGI-Integrated-v1.0.md"
_srs_bad: list[str] = []
if os.path.exists(_srs_md):
    _srs_text = read(_srs_md)
    _in_srs = set(re.findall(r"^\| (\d+b?) \| [A-Z]\w+ \|", _srs_text, re.M))
    _missing = sorted(_job_nos - _in_srs, key=lambda x: (len(x), x))
    if _missing:
        _srs_bad.append(
            f"ตารางงาน Batch ใน SRS ขาด Job {', '.join(_missing)} — "
            "รัน `node tmp/extract_js_data.mjs` แล้ว `python3 tools/build_integrated_srs.py` ใหม่")
check("SRS ที่ส่งมอบมี job ไม่ครบ", _srs_bad)

# 43) entity TypeORM ในเอกสารต้องมีคอลัมน์ตรงกับ DDL ทุกตัว
#   เจอจริง 2026-09-02: COLUMN_HINTS ใน tools/lldd_skeleton_be.py เขียนมือคู่ขนานกับ DDL แล้วหลุด
#   **ทั้ง 18 ตาราง** — เช่น sgi_document_new_stores ประกาศ compensate_amount ทั้งที่ DDL ชื่อ
#   compensation_amount · sgi_document_competitors ประกาศ zone_code/subzone_code ที่ไม่มีอยู่จริง
#   แก้ที่รากด้วยการ generate entity จาก DDL แล้ว · ข้อนี้กันไม่ให้ใครกลับไปเขียนมือคู่ขนานอีก
_ent_bad: list[str] = []
try:
    import build_lldd_documents as _BB  # noqa: F401  (ต้องโหลดก่อน เพื่อให้ skeleton import กลับได้)
    import lldd_skeleton_be as _SK
    _ddl_cols = _SK._ddl_entity_columns()
    for _t, (_cls, _flds) in _SK.COLUMN_HINTS.items():
        if _t not in _ddl_cols:
            continue   # ตารางของระบบเดิม (เช่น fcs_qssi_score) ไม่มี CREATE TABLE ในชุดเรา
        if not _flds:
            continue   # สถานะที่ถูกต้อง: ยุบเหลือชื่อคลาส แล้ว generate คอลัมน์จาก DDL
        _hand = {f[0] for f in _flds}
        _real = {c[0] for c in _ddl_cols[_t]}
        if _hand - _real:
            _ent_bad.append(f"{_t}: COLUMN_HINTS มีคอลัมน์ที่ DDL ไม่มี {sorted(_hand - _real)}")
        if _real - _hand:
            _ent_bad.append(f"{_t}: COLUMN_HINTS ขาดคอลัมน์ที่ DDL มี {sorted(_real - _hand)}")
except Exception as _e:   # pragma: no cover
    _ent_bad.append(f"ตรวจ entity ไม่ได้: {_e}")
check("entity ในเอกสารไม่ตรงกับ DDL", _ent_bad)

# 44) คอลัมน์ที่ SQL ตัวอย่างเขียนถึง ต้องมีอยู่จริงใน DDL
#   INSERT INTO sgi_x (a, b, c) · UPDATE sgi_x SET a = ... · sgi_x.col
#   เจอจริง 2026-09-02: SQL_BY_PATH เขียน sgi_document_new_stores.compensate_amount ซึ่งไม่มีในตาราง
_sqlcol_bad: list[str] = []
try:
    _cols_of = {t: {c[0] for c in cs} for t, cs in _SK._ddl_entity_columns().items()}
    _seen_bad: set[tuple[str, str]] = set()
    for _f in DOC_FILES:
        _t = read(_f)
        _hits: list[tuple[str, str]] = []
        for _m in re.finditer(r"INSERT INTO\s+(sgi_\w+)\s*\(([^)]*)\)", _t):
            _hits += [(_m.group(1), _c.strip().strip("`")) for _c in _m.group(2).split(",")]
        for _m in re.finditer(r"UPDATE\s+(sgi_\w+)(?:\s+\w+)?\s+SET\s+([\s\S]*?)(?=\bWHERE\b|\bFROM\b|\bRETURNING\b|;|```)", _t):
            _hits += [(_m.group(1), _c) for _c in re.findall(r"(?:^|,)\s*([a-z_][a-z_0-9]*)\s*=", _m.group(2))]
        _hits += re.findall(r"\b(sgi_[a-z_0-9]+)\.([a-z_][a-z_0-9]*)\b", _t)
        for _tbl, _c in _hits:
            if _tbl not in _cols_of or not re.match(r"^[a-z_][a-z_0-9]*$", _c or ""):
                continue
            if _c not in _cols_of[_tbl] and (_tbl, _c) not in _seen_bad:
                _seen_bad.add((_tbl, _c))
                _sqlcol_bad.append(f"{_tbl}.{_c} — SQL อ้างถึงแต่ DDL ไม่มีคอลัมน์นี้ ({_f})")
except Exception as _e:   # pragma: no cover
    _sqlcol_bad.append(f"ตรวจคอลัมน์ใน SQL ไม่ได้: {_e}")
check("SQL อ้างคอลัมน์ที่ไม่มีใน DDL", _sqlcol_bad)

# 45) route ที่ controller skeleton ประกาศ ต้องได้ path ตรงกับ comment เหนือมัน
#   เจอจริง 2026-09-04: _controller_base เติม BACKEND_PREFIX ทับ path ที่มี `sgi` อยู่แล้ว
#   → ทุกฉบับออกมาเป็น @Controller('sgi/sgi/document') + @Get('document/tasks')
#     รวม prefix ของ RouterModule แล้วได้ /api/v1/sgi/sgi/sgi/document/document/tasks (พังทุกเส้น)
#   สูตรตรวจ: '/api/v1/sgi/' + base + route ต้องเท่ากับ path ใน comment (แปลง {x} เป็น :x)
_route_bad: list[str] = []
for _f in DOC_FILES:
    if not _f.startswith("LLDD/md/BE/"):
        continue
    _t = read(_f)
    for _cm in re.finditer(r"@Controller\('([^']*)'\)([\s\S]*?)\n```", _t):
        _base, _body = _cm.group(1), _cm.group(2)
        if "BffController" in _body:
            # ฝั่ง BFF ไม่มี RouterModule prefix — path ต้องเท่ากับที่ FE เรียกจริง (มี `sgi/` ในตัว)
            if not _base.startswith("sgi"):
                _route_bad.append(f"{_f}: BFF @Controller('{_base}') ต้องขึ้นต้นด้วย `sgi` ให้ตรงกับที่ FE เรียก")
            for _m in re.finditer(
                    r"//\s*proxy ของ (?:GET|POST|PUT|PATCH|DELETE)\s+(/api/v1/sgi/\S+)\s*\n\s*"
                    r"@\w+\((?:'([^']*)')?\)", _body):
                _want = re.sub(r"\{(\w+)\}", r":\1", _m.group(1)).rstrip("/")
                _got = ("/api/v1/" + "/".join(x for x in [_base, _m.group(2) or ""] if x)).rstrip("/")
                if _want != _got:
                    _route_bad.append(f"{_f}: BFF proxy ควรเป็น {_want} แต่ decorator ให้ {_got}")
            continue
        if _base.split("/")[0] == "sgi":
            _route_bad.append(f"{_f}: @Controller('{_base}') — ห้ามมี `sgi/` (RouterModule ใส่ให้แล้ว)")
        for _m in re.finditer(
                r"//\s*(?:GET|POST|PUT|PATCH|DELETE)\s+(/api/v1/sgi/[^\s]+)[^\n]*\n\s*"
                r"@(?:Get|Post|Put|Patch|Delete)\((?:'([^']*)')?\)", _body):
            _want = re.sub(r"\{(\w+)\}", r":\1", _m.group(1)).rstrip("/")
            _got = ("/api/v1/sgi/" + "/".join(x for x in [_base, _m.group(2) or ""] if x)).rstrip("/")
            if _want != _got:
                _route_bad.append(f"{_f}: comment บอก {_want} แต่ decorator ให้ {_got}")
check("route ของ controller ไม่ตรงกับ path จริง", _route_bad)

# 46) วิธี inject DataSource ต้องตรงกับ repo จริงทั้งสองตัว
#   store-backend และ sop-sgi-batch ใช้ token 'DATA_SOURCE' ทั้งคู่ (@Inject('DATA_SOURCE') /
#   entity provider inject: ["DATA_SOURCE"]) · **ไม่มี @InjectDataSource() ของ @nestjs/typeorm เลย**
_inject_bad = [f"{_f}: ใช้ @InjectDataSource() ซึ่งไม่มีใน repo จริง — ต้องเป็น @Inject('DATA_SOURCE')"
               for _f in DOC_FILES if "@InjectDataSource()" in read(_f)]
check("วิธี inject DataSource ไม่ตรงกับ repo จริง", _inject_bad)

# 47) DTO ที่รับอาร์เรย์ของ object ต้องเป็น nested DTO ไม่ใช่ string[]
#   เจอจริง 2026-09-04: _dto_property แปลง list ทุกชนิดเป็น string[] + @IsString({each:true})
#   payload จริง (newStores/competitors/externalFactors) จึงโดน ValidationPipe ตีกลับ 400 ทุกครั้ง
#   ตรวจ: ฟิลด์ที่ตารางฟิลด์บอกว่าเป็น array<object> ต้องไม่ประกาศเป็น string[] ใน DTO
_dtoarr_bad: list[str] = []
for _f in DOC_FILES:
    if not _f.startswith("LLDD/md/BE/"):
        continue
    _t = read(_f)
    _objarr = set(re.findall(r"^\| (\w+) \| array<object> \|", _t, re.M))
    for _name in sorted(_objarr):
        if re.search(rf"^\s+{_name}\??: string\[\];", _t, re.M):
            _dtoarr_bad.append(f"{_f}: `{_name}` เป็น array<object> แต่ DTO ประกาศเป็น string[]")
    for _m in re.finditer(r"@Type\(\(\) => (\w+ItemDto)\)", _t):
        if f"export class {_m.group(1)}" not in _t:
            _dtoarr_bad.append(f"{_f}: อ้าง {_m.group(1)} แต่ไม่มีคลาสนี้ในเอกสาร")
check("DTO ของอาร์เรย์ object ประกาศผิดชนิด", _dtoarr_bad)

# 48) จำนวนเอกสาร LLDD ที่เขียนเป็นตัวเลขในไฟล์อื่น ต้องตรงกับยอดจริง
#   เจอจริง 2026-09-04: CLAUDE.md และ DECISIONS ยังเขียน "40 ฉบับ" หลังชุดโตเป็น 42
#   ยอดจริงคำนวณสดใน LLDD/md/README.md ("Documents: N") — ใช้ค่านั้นเป็นตัวตั้ง
_cnt_bad: list[str] = []
_readme = read("LLDD/md/README.md") if os.path.exists("LLDD/md/README.md") else ""
_m_docs = re.search(r"^- Documents: (\d+)", _readme, re.M)
_m_hours = re.search(r"^- Total estimate: (\d+) hours", _readme, re.M)
if _m_docs:
    _n_docs = _m_docs.group(1)
    for _f in ("CLAUDE.md", "DECISIONS-รอตัดสินใจ.md", "README.md"):
        if not os.path.exists(_f):
            continue
        # ตรวจเฉพาะ "ยอดชุดส่งมอบ" ที่เขียนตัวหนาไว้ — ประโยคเล่าเรื่องอย่าง
        # "เอกสาร LLDD 3 ฉบับ map ไว้" หมายถึงเอกสาร 3 ฉบับเจาะจง ไม่ใช่ยอดรวม จึงไม่นับ
        for _m in re.finditer(r"LLDD \*\*(\d+) ฉบับ\*\*|เอกสารส่งมอบ \*\*(\d+) ฉบับ\*\*", read(_f)):
            # ข้ามประโยคที่เล่าประวัติ (มีลูกศร → เช่น "41 → 40 ฉบับ")
            if "→" in read(_f)[max(0, _m.start() - 30):_m.start() + 12]:
                continue
            _got = _m.group(1) or _m.group(2)
            if _got != _n_docs:
                _cnt_bad.append(f"{_f}: เขียน {_got} ฉบับ แต่ยอดจริงคือ {_n_docs}")
if _m_hours:
    _n_hours = _m_hours.group(1)
    for _f in ("CLAUDE.md", "DECISIONS-รอตัดสินใจ.md", "estimate-sgi-project-hours.md"):
        if not os.path.exists(_f):
            continue
        _txt = read(_f)
        for _m in re.finditer(r"รวม(?:ทั้งโครงการ)?[^\n]{0,20}?\*{0,2}(\d{3}) ชั่วโมง", _txt):
            if _m.group(1) != _n_hours and "→" not in _txt[max(0, _m.start() - 30):_m.start() + 12]:
                _cnt_bad.append(f"{_f}: เขียนรวม {_m.group(1)} ชั่วโมง แต่ยอดจริงคือ {_n_hours}")
check("จำนวนเอกสาร/ชั่วโมงที่เขียนไว้ไม่ตรงยอดจริง", _cnt_bad)

# 49) SQL ในเอกสารต้องเป็น PostgreSQL ที่รันได้จริง — ตรวจ syntax ที่พังแน่ ๆ
#   เจอจริง 2026-09-04 (ผู้ใช้ชี้): Job 12 เขียน `BETWEEN ANY (:age_windows)` ซึ่งไม่มีใน PostgreSQL
#   (ANY ใช้กับตัวเปรียบเทียบเดี่ยวเท่านั้น) · และ skeleton หลุด `FROM email_template (ระบบ SBP เดิม)`
#   คือเอา "ป้ายกำกับ" ไปเป็นชื่อตาราง · รวมถึง `FROM (backend config)` ที่ไม่ใช่ตารางจริง
_sqlsyn_bad: list[str] = []
_BAD_SQL_PATTERNS = [
    (r"BETWEEN\s+(?:ANY|ALL)\s*\(", "`BETWEEN ANY/ALL (...)` ไม่ใช่ syntax ของ PostgreSQL"),
    (r"\b(?:FROM|JOIN|INTO|UPDATE)\s+[a-z_][a-z_0-9.]*\s+\((?![\s]*(?:SELECT|VALUES|unnest|LATERAL))[^)]*[ก-๙]",
     "ชื่อตารางมีคำอธิบายภาษาไทยติดมา (ป้ายกำกับหลุดเข้า SQL)"),
    (r"\b(?:FROM|JOIN|INTO|UPDATE)\s+\((?![\s]*(?:SELECT|VALUES|unnest|LATERAL))", "อ้างสิ่งที่ไม่ใช่ตารางจริงเป็นตาราง"),
]
for _f in DOC_FILES:
    if not (_f.endswith(".md") or _f.endswith(".html")):
        continue
    for _blk in re.findall(r"```sql\n([\s\S]*?)```", read(_f)):
        _clean = re.sub(r"--[^\n]*", "", _blk)
        for _pat, _why in _BAD_SQL_PATTERNS:
            _m = re.search(_pat, _clean)
            if _m:
                _sqlsyn_bad.append(f"{_f}: {_why} — `{' '.join(_m.group(0).split())[:60]}`")
                break
check("SQL ในเอกสารมี syntax ที่รันไม่ได้", _sqlsyn_bad)

# 50) ตารางของระบบ SBP เดิมที่ reuse แบบอ่านอย่างเดียว ห้ามมี INSERT/UPDATE/DELETE ในเอกสาร
#   เจอจริง 2026-09-04: Job 10 ถูก generate `INSERT INTO email_sent (...)` ทั้งที่คอมเมนต์บรรทัดบน
#   เขียนไว้เองว่า email-lib เขียนให้ · เขียนตารางของระบบเดิมคือแตะระบบที่มีอยู่แล้ว (ห้ามตามข้อตกลง)
_ro_bad: list[str] = []
try:
    import lldd_skeleton_job as _SJ
    _RO = set(_SJ.EXISTING_SYSTEM_READONLY)
except Exception as _e:   # pragma: no cover
    _RO = set()
    _ro_bad.append(f"อ่านรายชื่อตาราง read-only ไม่ได้: {_e}")
for _f in DOC_FILES:
    if not _f.endswith(".md"):
        continue
    for _blk in re.findall(r"```sql\n([\s\S]*?)```", read(_f)):
        _clean = re.sub(r"--[^\n]*", "", _blk)
        for _m in re.finditer(r"\b(INSERT INTO|UPDATE|DELETE FROM)\s+([a-z_][a-z_0-9]*)", _clean):
            if _m.group(2) in _RO:
                _ro_bad.append(f"{_f}: {_m.group(1)} {_m.group(2)} — ตารางของระบบ SBP เดิม อ่านอย่างเดียว")
check("เขียนตารางของระบบเดิมที่ต้องอ่านอย่างเดียว", sorted(set(_ro_bad)))

# 51) บล็อก SQL ในเอกสารต้องคัดลอกไปรันได้ — ห้ามมี named parameter และห้ามเป็นช่องว่างเปล่า
#   เจอจริง 2026-09-04 (ผู้ใช้ชี้): เอกสารพิมพ์ `:name` 480 จุด ทั้งที่ระบุเองว่า dataSource.query()
#   รับเฉพาะ $1..$n · และ skeleton หลายที่เป็น `SELECT /* TODO: columns */ ... WHERE 1 = 1`
#   ซึ่งไม่ใช่สเปก แต่เป็นช่องว่าง · ตอนนี้ตัวสร้างแปลงเป็น $n และเติมคอลัมน์จาก DDL ให้แล้ว
_sqlparam_bad: list[str] = []
_NAMED = re.compile(r"(?<![:\w]):[a-zA-Z_]\w*")
for _f in DOC_FILES:
    if not _f.startswith("LLDD/md/"):
        continue
    for _blk in re.findall(r"```sql\n([\s\S]*?)```", read(_f)):
        _clean = re.sub(r"--[^\n]*", "", _blk)
        _clean = re.sub(r"'[^']*'", "''", _clean)      # ตัด string literal
        _hit = _NAMED.search(_clean)
        if _hit:
            _sqlparam_bad.append(
                f"{_f}: ใช้ named parameter `{_hit.group(0)}` — dataSource.query() รับเฉพาะ $1..$n")
        if re.search(r"SELECT\s*/\* *TODO", _clean) or re.search(r"\(\s*/\* *TODO[^)]*\)\s*\n\s*VALUES", _clean):
            _sqlparam_bad.append(f"{_f}: บล็อก SQL ยังเป็นช่องว่าง (SELECT/INSERT ไม่มีรายชื่อคอลัมน์)")
check("SQL ในเอกสารคัดลอกไปรันไม่ได้", sorted(set(_sqlparam_bad)))

# 52) ห้ามเอกสารบอกว่า "ยังไม่มี LLDD สำหรับงานนี้" ทั้งที่เอกสารนั้นมีอยู่แล้ว
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): Job 10 ยังเขียนว่างานเตือน/escalation "ยังไม่มีเอกสาร LLDD"
#   และ G6 ยัง 🔴 ค้าง ทั้งที่ LLDD-BE-Job-12-NotifyPendingWork ถูกสร้างตั้งแต่ 2026-09-02
#   วิธีตรวจ: ประโยคที่มีคำว่า "ไม่มีเอกสาร/ยังไม่มี LLDD" ห้ามอยู่ในประโยคเดียวกับชื่อเอกสารที่มีจริง
#   และห้ามพูดถึงงานที่มีเอกสารแล้วว่าไม่มี โดยไม่มีเครื่องหมายว่าปิดแล้ว
_stale_bad: list[str] = []
_doc_names = {os.path.basename(_p)[:-3] for _p in glob.glob("LLDD/md/**/*.md", recursive=True)}
_NEG = ("ยังไม่มีเอกสาร", "ไม่มีเอกสาร LLDD", "ยังไม่มีเจ้าของเอกสาร", "ยังไม่มี LLDD")
for _f in DOC_FILES:
    if not _f.startswith("LLDD/md/"):
        continue
    _t = read(_f)
    for _sent in re.split(r"(?<=[·\n|])", _t):
        if not any(_n in _sent for _n in _NEG):
            continue
        if "✅" in _sent or "ปิดแล้ว" in _sent:
            continue   # เขียนกำกับไว้แล้วว่าปิด — เป็นประวัติ ไม่ใช่ข้อความค้าง
        for _name in re.findall(r"\b(LLDD-[A-Za-z0-9\-]+)", _sent):
            if _name in _doc_names:
                _stale_bad.append(f"{_f}: บอกว่าไม่มีเอกสาร ทั้งที่ `{_name}` มีอยู่จริง")
# งานที่มีเอกสารของตัวเองแล้ว ห้ามมีข้อค้างเปิดค้างในเอกสารฉบับอื่นที่พูดถึงงานเดียวกัน
try:
    import build_lldd_documents as _BC
    for _no, _spec in _BC.JOB_DECISION_RULES.items():
        for _row in _spec.get("gaps", []):
            _txt = " ".join(str(x) for x in _row)
            if "✅" in str(_row[0]):
                continue
            for _name in re.findall(r"\b(LLDD-BE-Job-[A-Za-z0-9\-]+)", _txt):
                if _name in _doc_names:
                    _stale_bad.append(
                        f"JOB_DECISION_RULES['{_no}']: ข้อค้างยังเปิดอยู่ แต่อ้าง `{_name}` ที่มีเอกสารแล้ว")
except Exception as _e:   # pragma: no cover
    _stale_bad.append(f"ตรวจข้อค้างของ job ไม่ได้: {_e}")
check("เอกสารบอกว่าไม่มี LLDD ทั้งที่มีแล้ว", sorted(set(_stale_bad)))

# 53) ระดับหัวข้อ markdown ห้ามกระโดด (H2 → H4)
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): 43 จุดใน 34 ไฟล์ — หัวข้อ section ของ skeleton เป็น `##`
#   แต่หัวข้อลูกเป็น `####` ทำให้สารบัญและ accessibility ผิดโครง
#   ต้นเหตุ: 3 track (FE/BE/Job) จัดระดับคนละแบบ · ตอนนี้ใช้ level_skeleton_blocks() ร่วมกัน
_head_bad: list[str] = []
# ครอบไฟล์แปลง SRS ด้วย (แก้ 2026-09-08) — ระดับหัวข้อเป็นของ "ตัวแปลง" ไม่ใช่เนื้อหาใน PDF
#   (ตรวจ PDF แล้ว: จุดนั้นเป็นตาราง No./Panel/Content ไม่มีลำดับ # ## ### เลย) จึงจัดให้ถูกได้
#   โดยไม่กระทบข้อกำหนด — แต่ **ห้ามแก้ข้อความ** ของไฟล์แปลงเด็ดขาด
_HEAD_SCOPE = [f for f in DOC_FILES if f.startswith("LLDD/md/") and f.endswith(".md")]
if os.path.exists("SRS_Income_Compensation_v3.1.md"):
    _HEAD_SCOPE.append("SRS_Income_Compensation_v3.1.md")
for _f in _HEAD_SCOPE:
    _prev, _fence = None, False
    for _n, _l in enumerate(read(_f).split("\n"), 1):
        if _l.startswith("```"):
            _fence = not _fence
            continue
        if _fence:
            continue
        _m = re.match(r"^(#{1,6}) ", _l)
        if not _m:
            continue
        _lv = len(_m.group(1))
        if _prev and _lv > _prev + 1:
            _head_bad.append(f"{_f}:{_n} หัวข้อกระโดด H{_prev} → H{_lv} ({_l[:50]})")
        _prev = _lv
check("ระดับหัวข้อ markdown กระโดด", _head_bad)

# 54) ข้อความรูป `<Word>` ที่ไม่ใช่ tag จริง ต้องถูก escape ไม่งั้น renderer กลืนหาย
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): ชื่อเล่น `Aphiwit <Bank> Khammoon` ตรงรูปแบบ HTML open tag พอดี
#   browser ทิ้ง element ที่ไม่รู้จัก → ชื่อเล่นหายหมด · เรื่องเดียวกันกิน `array<object>` ในตารางสัญญา API
_pseudo_bad: list[str] = []
try:
    import build_lldd_documents as _BD
    _OK_TAGS = _BD._REAL_HTML_TAGS
except Exception:   # pragma: no cover
    _OK_TAGS = {"br", "iframe", "b", "i", "code", "span", "a", "img"}
for _f in DOC_FILES:
    if not (_f.startswith("LLDD/md/") and _f.endswith(".md")):
        continue
    _fence = False
    for _n, _l in enumerate(read(_f).split("\n"), 1):
        if _l.startswith("```"):
            _fence = not _fence
            continue
        if _fence:
            continue
        for _m in re.finditer(r"<(/?)([A-Za-z][A-Za-z0-9]*)(\s*/?)>", _l):
            if _m.group(2).lower() not in _OK_TAGS:
                _pseudo_bad.append(f"{_f}:{_n} `{_m.group(0)}` จะถูก renderer กลืน — ต้อง escape เป็น &lt;…&gt;")
                break
check("ข้อความหน้าตาเหมือน HTML tag ที่จะถูกกลืน", _pseudo_bad)

# 55) ทุกหน้า HTML ต้องมี lang · viewport · title · favicon
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): 3 ไฟล์ไม่มี lang · หลาย diagram ไม่มี viewport
#   และทุกหน้าไม่ประกาศ favicon ทำให้ browser ยิง /favicon.ico แล้วได้ 404
_head_meta_bad: list[str] = []
for _f in sorted(glob.glob("*.html") + glob.glob("LLDD/*.html")
                 + glob.glob("output/**/*.html", recursive=True)):
    _head = read(_f)[:4000]
    if not re.search(r"<html[^>]*\blang=", _head):
        _head_meta_bad.append(f"{_f}: ไม่มี lang บน <html>")
    if 'name="viewport"' not in _head:
        _head_meta_bad.append(f"{_f}: ไม่มี viewport meta — มือถือจะย่อทั้งหน้า")
    if "<title" not in _head:
        _head_meta_bad.append(f"{_f}: ไม่มี <title>")
    if 'rel="icon"' not in _head:
        _head_meta_bad.append(f"{_f}: ไม่ประกาศ favicon — browser จะยิง /favicon.ico แล้วได้ 404")
check("หน้า HTML ขาด lang/viewport/title/favicon", _head_meta_bad)

# 56) นโยบายดาวน์โหลดไฟล์แนบต้องเป็นข้อความชุดเดียวทุกฉบับ
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): 4 เอกสารเขียนกันคนละอย่าง — "เฉพาะ CLEAN" / "PENDING ก็ได้" /
#   "BLOCKED,PENDING ไม่ได้" / "scanStatus=CLEAN" · เรื่องนี้กระทบ security + BE + FE + test case
#   พร้อมกัน จึงต้องมาจาก ATTACHMENT_DOWNLOAD_POLICY_* ตัวเดียวเท่านั้น
_scan_bad: list[str] = []
_BANNED = [
    ("อนุญาตเฉพาะ CLEAN", "ระบุ CLEAN อย่างเดียว โดยไม่พูดถึงสวิตช์ PENDING"),
    ("scanStatus=CLEAN", "ระบุ CLEAN อย่างเดียว โดยไม่พูดถึงสวิตช์ PENDING"),
    ("BLOCKED/PENDING ดาวน์โหลดไม่ได้", "ปิด PENDING ตายตัว ขัดกับนโยบายที่ใช้สวิตช์"),
]
for _f in DOC_FILES:
    _t = read(_f)
    for _phrase, _why in _BANNED:
        if _phrase in _t:
            _scan_bad.append(f"{_f}: `{_phrase}` — {_why}")
    # SQL ที่กรอง scan_status ต้องรองรับสวิตช์ ไม่ใช่ล็อก CLEAN ไว้ตายตัว
    #   เจอจริง 2026-09-07 (ผู้ใช้ชี้): query download-all กรอง scan_status = 'CLEAN' อย่างเดียว
    #   ถ้าเปิดสวิตช์ให้ PENDING ดาวน์โหลดได้ zip จะยังไม่รวมไฟล์เหล่านั้น = สวิตช์ไม่ทำงานจริง
    for _blk in re.findall(r"```sql\n([\s\S]*?)```", _t):
        _clean_sql = re.sub(r"--[^\n]*", "", _blk)
        if re.search(r"scan_status\s*=\s*'CLEAN'", _clean_sql) and "PENDING" not in _clean_sql:
            _scan_bad.append(f"{_f}: SQL ล็อก `scan_status = 'CLEAN'` ตายตัว — สวิตช์ "
                             "SGI_ALLOW_PENDING_DOWNLOAD จะไม่มีผลกับ query นี้")
    # อัปโหลดต้องตั้ง PENDING ไม่ใช่ CLEAN (ระบบยังไม่มีตัวสแกน)
    for _blk in re.findall(r"INSERT INTO sgi_document_attachments[\s\S]{0,900}?;", _t):
        if re.search(r"'CLEAN'", re.sub(r"--[^\n]*", "", _blk)):
            _scan_bad.append(f"{_f}: INSERT ไฟล์แนบตั้ง scan_status = 'CLEAN' "
                             "— ต้องเป็น 'PENDING' เพราะยังไม่เคยสแกนจริง")
# ทุกฉบับที่พูดถึงการดาวน์โหลดไฟล์แนบ ต้องอ้างสวิตช์ตัวเดียวกัน
for _f in ("LLDD/md/BE/LLDD-BE-API-Attachment-Sales-Timeline.md",
           "LLDD/md/FE/LLDD-FE-Document-Detail.md",
           "LLDD/md/LLDD-API.md"):
    if os.path.exists(_f) and "SGI_ALLOW_PENDING_DOWNLOAD" not in read(_f):
        _scan_bad.append(f"{_f}: ไม่ได้อ้างสวิตช์ `SGI_ALLOW_PENDING_DOWNLOAD` — นโยบายจะหลุดกันอีก")
check("นโยบายดาวน์โหลดไฟล์แนบไม่ตรงกัน", _scan_bad)

# 57) owner / ชั่วโมง / จำนวนสัปดาห์ ในเอกสารต้องตรงกับข้อมูลจริง
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): README บอก Bank ถือ migration + batch + workflow definition
#   แต่ Main Index บอกถือแค่ batch job · prose ในไฟล์เดียวกันยังเป็นการแบ่งงานรุ่น 2026-08-07
#   และ "25 working days = about 7 weeks" (จริง 5) · "everyone else 92-123 hours" (จริง Vava 145)
_plan_bad: list[str] = []
try:
    import build_lldd_documents as _BP
    _rows = _BP.owner_workload()
    _hours = {o: c for o, c, _r, _j in _rows}
    _job_owner = [r for r in _rows if r[3]]
    _readme = read("LLDD/md/README.md") if os.path.exists("LLDD/md/README.md") else ""
    _main = ""
    for _p in glob.glob("LLDD/md/LLDD-Main-Index*.md"):
        _main = read(_p)
    # ก) ชั่วโมงของแต่ละคนที่ปรากฏในเอกสาร ต้องตรงกับที่คำนวณได้
    for _o, _c in _hours.items():
        _short = re.search(r"<([^>]+)>", _o)
        _short = _short.group(1) if _short else _o.split()[0]
        for _label, _txt in (("README.md", _readme), ("Main-Index", _main)):
            if not _txt:
                continue
            for _m in re.finditer(re.escape(_short) + r"[^\n|]{0,60}?\*\*(\d{2,3})\*\*", _txt):
                if int(_m.group(1)) != _c:
                    _plan_bad.append(f"{_label}: {_short} เขียน {_m.group(1)} ชม. แต่คำนวณได้ {_c}")
    # ข) ห้ามบอกว่ามีคนถือ batch job มากกว่า 1 คน ถ้าข้อมูลจริงรวมที่คนเดียว
    if len(_job_owner) == 1:
        _owner_jobs = set(_job_owner[0][3])
        # ชื่อของคนที่ **ไม่ได้ถือ job** ห้ามปรากฏใกล้ ๆ การไล่เลข Job (แถวของเจ้าของ job เองไม่นับ)
        _no_job = [(_o, re.search(r"<([^>]+)>", _o).group(1) if re.search(r"<([^>]+)>", _o) else _o.split()[0])
                   for _o, _c, _r, _j in _rows if not _j]
        for _label, _txt in (("README.md", _readme), ("Main-Index", _main)):
            for _line in _txt.split("\n"):
                if _job_owner[0][1 - 1] in _line or _job_owner[0][0] in _line:
                    continue   # แถว/ประโยคของเจ้าของ job เอง
                for _full, _short in _no_job:
                    if _short in _line and re.search(r"(?:รับ|เป็นเจ้าของ)[^\n|]{0,40}?Job\s*[0-9]", _line):
                        _plan_bad.append(f"{_label}: ยังเขียนว่า {_short} รับ Job อยู่ "
                                         f"ทั้งที่ batch job ทั้งหมดอยู่กับ {_job_owner[0][0]} คนเดียว")
    # ค) จำนวนสัปดาห์ที่เขียนไว้ ต้องตรงกับ ชั่วโมง ÷ ชม./สัปดาห์
    for _label, _txt in (("README.md", _readme), ("Main-Index", _main)):
        # เทียบเฉพาะประโยคที่ "บอกว่าชั่วโมงเท่านี้ = กี่สัปดาห์" จริง ๆ
        #   เลขสัปดาห์ที่ตามหลังคำว่า กรอบ/เพดาน/ceiling คือ "กรอบเวลา" ไม่ใช่การแปลงชั่วโมง
        for _m in re.finditer(
                r"(\d{2,3})\s*(?:hours|ชม\.|ชั่วโมง)[^\n|]{0,80}?(?:=|คือ|เท่ากับ|that is|is)\s*\**"
                r"(\d+(?:\.\d+)?)\s*(?:weeks|สัปดาห์)", _txt):
            _pre = _txt[max(0, _m.start(2) - 24):_m.start(2)]
            if re.search(r"กรอบ|เพดาน|ceiling|within", _pre):
                continue
            _h, _wk = int(_m.group(1)), float(_m.group(2))
            _real = _h / _BP.HOURS_PER_WEEK
            if _h in _hours.values() and abs(_real - _wk) > 0.6:
                _plan_bad.append(f"{_label}: {_h} ชม. เขียนว่า {_wk} สัปดาห์ แต่จริง {_real:.1f}")
except Exception as _e:   # pragma: no cover
    _plan_bad.append(f"ตรวจ owner/ชั่วโมงไม่ได้: {_e}")
check("owner/ชั่วโมง/สัปดาห์ ไม่ตรงกับข้อมูลจริง", sorted(set(_plan_bad)))

# 63) ห้ามมีประโยคที่อ้างว่า "จบใน 4 สัปดาห์" ขณะที่ตัวเลขบอกว่ายังเกินกรอบ
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): แถว workload บอกว่าย้ายงาน "เพื่อให้สายงาน job จบใน 4 สัปดาห์"
#   แต่บรรทัดกติกาเวลาในไฟล์เดียวกันบอก 211 ชม. = 5.0 สัปดาห์ เกินกรอบ 41 ชม.
#   ประโยคแบบนี้อันตรายกว่าตัวเลขผิด เพราะทำให้คนอ่านเชื่อว่าแผนลงตัวแล้ว
_fit_bad: list[str] = []
try:
    import build_lldd_documents as _BF
    _ceiling = 4 * _BF.HOURS_PER_WEEK
    _over = [(o, c) for o, c, _r, _j in _BF.owner_workload() if c > _ceiling]
    if _over:
        _CLAIM = re.compile(r"(?:เพื่อให้|ทำให้|จึง)[^\n|]{0,40}?จบใน 4 ?สัปดาห์|ลงกรอบ 4 ?สัปดาห์แล้ว"
                            r"|fits? (?:in|within) 4 weeks|finish(?:es)? in 4 weeks")
        for _f in DOC_FILES:
            for _line in read(_f).split("\n"):
                for _cell in (_line.split("|") if "|" in _line else [_line]):
                    if not _CLAIM.search(_cell):
                        continue
                    if "ยังเกิน" in _cell or "ไม่ลงกรอบ" in _cell or "does not fit" in _cell:
                        continue   # เขียนกำกับไว้แล้วว่ายังไม่ลง
                    _fit_bad.append(
                        f"{_f}: อ้างว่าจบใน 4 สัปดาห์ แต่ "
                        + " · ".join(f"{_BF._short_name(o)} {c} ชม. (เกิน {c - _ceiling:g})" for o, c in _over)
                        + f" — `{' '.join(_cell.split())[:70]}`")
except Exception as _e:   # pragma: no cover
    _fit_bad.append(f"ตรวจคำอ้าง 4 สัปดาห์ไม่ได้: {_e}")
check("อ้างว่าจบใน 4 สัปดาห์ ทั้งที่ยังเกินกรอบ", sorted(set(_fit_bad)))

# 64) email template ที่ประกาศไว้ ต้องถูกผูกกับจุดส่งจริงครบทุกฉบับ
#   เจอจริง 2026-09-07: workflow.md ประกาศ 8 ฉบับ (EM-01..EM-08) แต่ **EM-02 (จบงาน) และ
#   EM-03 (ส่งกลับ) ไม่เคยถูกอ้างที่ไหนเลย** — ตารางสถานะมีแต่คอลัมน์ผู้รับ (TO) ไม่เคยบอก template
#   dev ที่ตั้ง workflow_route.email_id จึงต้องเดาเอง ทั้งที่ "จบงาน" กับ "ส่งกลับ" เป็น transition ที่เกิดบ่อยที่สุด
_em_bad: list[str] = []
_em_seen: dict[str, int] = {}
for _f in DOC_FILES:
    for _m in re.finditer(r"\bEM-(\d{2})\b", read(_f)):
        _em_seen[_m.group(1)] = _em_seen.get(_m.group(1), 0) + 1
for _i in range(1, 9):
    if f"{_i:02d}" not in _em_seen:
        _em_bad.append(f"EM-{_i:02d} ประกาศไว้ในชุด 8 ฉบับ แต่ไม่มีเอกสารไหนอ้างถึงเลย "
                       "— ต้องผูกกับจุดส่งจริง ไม่งั้น workflow_route.email_id ตั้งไม่ได้")
for _code in sorted(_em_seen):
    if not (1 <= int(_code) <= 8):
        _em_bad.append(f"EM-{_code} อยู่นอกชุด EM-01…EM-08")
# ตารางสถานะต้องมีคอลัมน์ template ไม่ใช่บอกแต่ผู้รับ
if os.path.exists("workflow_status_document.md"):
    _wsd = read("workflow_status_document.md")
    if "Email template" not in _wsd:
        _em_bad.append("workflow_status_document.md: ตาราง transition ไม่มีคอลัมน์ Email template "
                       "— ระบุแต่ผู้รับ (TO) ยังตั้ง workflow_route.email_id ไม่ได้")
check("email template ที่ประกาศไว้ไม่ถูกผูกกับจุดส่ง", _em_bad)

# 65) error code ในแคตตาล็อกกลาง ต้องถูกผูกกับ flow/endpoint จริงอย่างน้อยหนึ่งที่
#   เจอจริง 2026-09-07: 5 code ถูกนิยามไว้ครบ (รหัส · HTTP · ข้อความไทย) แต่ไม่มีเอกสารไหน
#   บอกว่าเส้นไหน/จอไหนโยนมัน — code ที่ไม่มีใครโยนคือ code ตาย หรือคือพฤติกรรมที่ยังไม่ได้ออกแบบ
#   (ATTACHMENT_FILE_REQUIRED · FILE_TYPE_UNSUPPORTED · FS_BRIDGE_ORIGIN_INVALID ·
#    FS_BRIDGE_SUBMIT_FAILED · REPORT_STATUS_REQUIRED)
_errcode_bad: list[str] = []
_cat_file = "LLDD/md/BE/LLDD-BE-API-Common-Contracts.md"
if os.path.exists(_cat_file):
    _codes = set(re.findall(r"^\| ([A-Z][A-Z0-9_]{4,})\s*\|", read(_cat_file), re.M))
    _seen: dict[str, int] = {}
    for _f in DOC_FILES:
        for _c in re.findall(r"\b([A-Z][A-Z0-9_]{6,})\b", read(_f)):
            if _c in _codes:
                _seen[_c] = _seen.get(_c, 0) + 1
    for _c in sorted(_codes):
        if _seen.get(_c, 0) <= 1:
            _errcode_bad.append(f"`{_c}` อยู่ในแคตตาล็อกแต่ไม่มี flow/endpoint ไหนอ้างถึงเลย "
                                "— ต้องระบุว่าเส้นไหนหรือหน้าจอไหนโยน code นี้")
check("error code ในแคตตาล็อกที่ไม่ถูกผูกกับ flow", _errcode_bad)

# 66) ลิงก์รูปใน .md ทุกไฟล์ต้องชี้ไฟล์ที่มีจริง (path สัมพัทธ์กับที่อยู่ของ .md เอง)
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): SRS ที่ส่งมอบอ้างรูปด้วย "ชื่อไฟล์เปล่า ๆ" ทั้งที่รูปอยู่ใต้
#   screenshots/slices|modals → เสียทั้ง 43 จุด เปิด .md แล้วไม่เห็นรูปสักรูป
#   (DOCX/PDF ไม่โดนเพราะฝังรูปเข้าไฟล์ ทำให้ปัญหาซ่อนอยู่จนกว่าจะมีคนเปิด .md)
_img_bad: list[str] = []
for _f in sorted(glob.glob("**/*.md", recursive=True)):
    if _f.startswith(("SBP/", "LLDD/pdf", "LLDD/word", "node_modules")):
        continue
    _d = os.path.dirname(_f) or "."
    for _m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", read(_f)):
        _src = _m.group(1)
        if _src.startswith(("http://", "https://", "data:")):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(_d, _src.split("#")[0]))):
            _img_bad.append(f"{_f}: ลิงก์รูป `{_src}` ไม่มีไฟล์จริง "
                            "— path ต้องสัมพัทธ์กับที่อยู่ของ .md ไม่ใช่ชื่อไฟล์เปล่า")
check("ลิงก์รูปใน .md ชี้ไฟล์ที่ไม่มีจริง", sorted(set(_img_bad))[:20])

# 67) ค่ากติกาเวลาทำงานและยอด CSV ในเอกสารแผน ต้องตรงกับค่าจริง
#   เจอจริง 2026-09-08 (ผู้ใช้ชี้): activity-plan และ estimate ยังเขียน 8 ชม./วัน · 40 ชม./สัปดาห์
#   · 30 ชม./สัปดาห์ (ค่าก่อนมติ 2026-08-25) และ CLAUDE.md ยังเขียน 37 topic / 32 แถว / 824 ชม.
#   ค่าจริงคือ 8.5 · 42.5 และ CSV 39 แถว / 34 แถวที่นับยอด / 829 ชม.
_rule_bad: list[str] = []
try:
    import build_lldd_documents as _BR
    _hd, _hw = _BR.HOURS_PER_DAY, _BR.HOURS_PER_WEEK
    import csv as _csvmod
    _rows = list(_csvmod.DictReader(io.open("LLDD/Main-Index-FE-BE-Job.csv", encoding="utf-8-sig"))) \
        if os.path.exists("LLDD/Main-Index-FE-BE-Job.csv") else []
    _yes = [r for r in _rows if (r.get("นับในยอดรวม") or "").strip() == "Y"]
    _csv_hours = sum(int(r["ชั่วโมงรวม"]) for r in _yes) if _yes else 0
    for _f in ("activity-plan-sbp-mall-fe-be.md", "estimate-sbpgi-project-hours.md",
               "CLAUDE.md", "LLDD/md/README.md"):
        if not os.path.exists(_f):
            continue
        for _line in read(_f).split("\n"):
            if "แก้ 2026-09-08" in _line or "เดิมเขียน" in _line:
                continue   # ประโยคที่บันทึกค่าเก่าไว้เป็นประวัติ
            for _m in re.finditer(r"(\d+(?:\.\d+)?)\s*ชม\./วัน", _line):
                if float(_m.group(1)) != _hd:
                    _rule_bad.append(f"{_f}: เขียน {_m.group(1)} ชม./วัน แต่ค่าจริงคือ {_hd}")
            for _m in re.finditer(r"(\d+(?:\.\d+)?)\s*ชม\./สัปดาห์", _line):
                # "6 คน × 42.5 = 255 ชม./สัปดาห์" คือกำลังทีมทั้งทีม ไม่ใช่ค่าต่อคน
                # (เทียบด้วยตัวเลขเท่านั้น — ห้ามข้ามทั้งบรรทัดเพราะคำว่า "คน"
                #  ไม่งั้นบรรทัดที่มี "170 ชม./คน" จะรอดไปทั้งบรรทัด)
                if float(_m.group(1)) == 6 * _hw:
                    continue
                if float(_m.group(1)) != _hw:
                    _rule_bad.append(f"{_f}: เขียน {_m.group(1)} ชม./สัปดาห์ แต่ค่าจริงคือ {_hw}")
            for _m in re.finditer(r"(\d+)\s*`Y` rows sum to \*{0,2}(\d+)", _line):
                if int(_m.group(1)) != len(_yes) or int(_m.group(2)) != _csv_hours:
                    _rule_bad.append(f"{_f}: เขียน {_m.group(1)} แถว รวม {_m.group(2)} ชม. "
                                     f"แต่ CSV จริงคือ {len(_yes)} แถว รวม {_csv_hours} ชม.")
except Exception as _e:   # pragma: no cover
    _rule_bad.append(f"ตรวจกติกาเวลาไม่ได้: {_e}")
check("กติกาเวลาทำงาน/ยอด CSV ในเอกสารแผนไม่ตรงค่าจริง", sorted(set(_rule_bad)))

# 68) service skeleton ห้ามอ้าง query.* / body.* ที่ DTO ในเอกสารเดียวกันไม่ได้ประกาศ
#   เจอจริง 2026-09-08 ตอนเติม body ตามมติทางเลือก ค.: service อ้าง query.page/query.size
#   และ body.docNo ทั้งที่ DTO ของเส้นนั้นไม่มี — คอมไพล์ไม่ผ่านตั้งแต่บรรทัดแรก
#   (เป็นข้อผิดเดิมของ template ไม่ใช่ของ body ที่เพิ่งเติม)
_dtoref_bad: list[str] = []
for _f in DOC_FILES:
    if not _f.startswith("LLDD/md/BE/"):
        continue
    _t = read(_f)
    _i = _t.find(".service.ts")
    if _i < 0:
        continue
    _i = _t.rfind("// src/modules", 0, _i)
    _j = _t.find("\n```", _i)
    _body = "\n".join(l for l in _t[_i:_j].split("\n") if not l.strip().startswith("//"))
    _dto: dict[str, set] = {}
    for _m in re.finditer(r"export class (\w+Dto)\s*\{([\s\S]*?)\n\}", _t):
        _dto[_m.group(1)] = set(re.findall(r"^  (\w+)\??:", _m.group(2), re.M))
    _q = set().union(*[v for k, v in _dto.items() if k.endswith("QueryDto")]) if any(
        k.endswith("QueryDto") for k in _dto) else set()
    _b = set().union(*[v for k, v in _dto.items() if k.endswith("BodyDto")]) if any(
        k.endswith("BodyDto") for k in _dto) else set()
    for _x in sorted(set(re.findall(r"query\.(\w+)", _body))):
        if _x not in _q:
            _dtoref_bad.append(f"{_f}: service อ้าง `query.{_x}` แต่ DTO ไม่ได้ประกาศ")
    for _x in sorted(set(re.findall(r"body\.(\w+)", _body))):
        if _x not in _b:
            _dtoref_bad.append(f"{_f}: service อ้าง `body.{_x}` แต่ DTO ไม่ได้ประกาศ")
check("service อ้างฟิลด์ที่ DTO ไม่มี", _dtoref_bad)

# 69) ไฟล์ skill ต้องไม่ตกยุคจากข้อเท็จจริงปัจจุบัน
#   เจอจริง 2026-09-08: domain.md เขียนว่าเลขเอกสารเป็น **พ.ศ.** ทั้งที่มติ 2026-08-06 คือ **ค.ศ.**
#   · SKILL.md ยังเขียน "Jobs 1–10" ทั้งที่ตัด Job 1 และเพิ่ม Job 11/12 แล้ว
#   · architecture.md ใช้ path เก่า (/documents, /workflows) ก่อนมติ namespace 2026-08-25
#   skill คือสิ่งที่ agent อ่านก่อนลงมือ — ผิดตรงนี้แปลว่างานรอบถัดไปเริ่มจากข้อมูลผิด
_skill_bad: list[str] = []
_SKILL_DIR = os.path.join(".claude", "skills", "sbp-prototype")
_skill_files = [os.path.join(_SKILL_DIR, "SKILL.md")] + sorted(
    glob.glob(os.path.join(_SKILL_DIR, "references", "*.md")))
_BANNED_SKILL = [
    (r"`YYYY/xxxxx`[^\n]{0,40}\*\*ปี พ\.ศ\.\*\*", "เลขที่เอกสารเป็น **ค.ศ.** ไม่ใช่ พ.ศ. (มติ 2026-08-06)"),
    (r"Jobs? 1[-–]10", "ตัด Job 1 ImportQSSI แล้ว (2026-08-24) และเพิ่ม Job 11/12 — ชุดปัจจุบันคือ Jobs 2–12 + 8b"),
    (r"`POST /documents[`/]", "path ปัจจุบันคือ `/api/v1/sgi/document` (มติ namespace 2026-08-25 + rename 2026-09-01)"),
    (r"`POST /workflows/instances`", "path ปัจจุบันคือ `/api/v1/sgi/workflow/instances`"),
]
for _f in _skill_files:
    if not os.path.exists(_f):
        continue
    _t = read(_f)
    for _pat, _why in _BANNED_SKILL:
        if re.search(_pat, _t):
            _skill_bad.append(f"{_f}: {_why}")
    # ทุกหน้าใน MODULES ต้องถูกพูดถึงใน architecture.md
    if _f.endswith("architecture.md") and os.path.exists("assets/sbp.js"):
        _js = read("assets/sbp.js")
        _i = _js.find("MODULES")
        _seg = _js[_i:_js.find("\n];", _i)]
        for _h in sorted({h.split("?")[0] for h in re.findall(r"href:\s*'([^']+)'", _seg)}):
            if _h not in _t:
                _skill_bad.append(f"{_f}: หน้า `{_h}` อยู่ใน MODULES แต่ skill ไม่พูดถึง")
# repo ปลายทางของ batch/consumer ต้องถูกอ้างใน skill
for _need, _why in ((("srm-sps-spsap-sop-sgi-batch",), "repo ปลายทางของ batch job"),
                    (("srm-sps-spsap-sop-sgi-batch",), "repo ที่ job consume EAI/RabbitMQ เอง (มติ 2026-09-12)")):
    if not any(any(n in read(_f) for n in _need) for _f in _skill_files if os.path.exists(_f)):
        _skill_bad.append(f"skill ไม่ได้อ้าง `{_need[0]}` — {_why}")
check("ไฟล์ skill ตกยุคจากข้อเท็จจริงปัจจุบัน", _skill_bad)

# 70) เอกสารห้ามบอกว่าไฟล์ "ยังอยู่" ทั้งที่ถูกลบไปแล้ว · และ JS ห้าม query element ที่ถอดออกแล้ว
#   เจอจริง 2026-09-08 (ผู้ใช้ชี้): CLAUDE.md บรรทัด 13/146 บอกว่า REACT-TODO-CHECKLIST.md ถูกลบ
#   แต่บรรทัด 152 บอกว่า "survives" · และ syncStatActive() ยัง query `#statGrid` ที่ถอดออกตั้งแต่ 2026-08-06
_ghost_bad: list[str] = []
_SURVIVE = re.compile(r"`([A-Za-z0-9_.\-]+\.md)`[^\n]{0,40}(?:survives|ยังอยู่|ยังใช้ได้)")
for _f in ("CLAUDE.md", "README.md"):
    if not os.path.exists(_f):
        continue
    for _m in _SURVIVE.finditer(read(_f)):
        if not os.path.exists(_m.group(1)):
            _ghost_bad.append(f"{_f}: บอกว่า `{_m.group(1)}` ยังอยู่ แต่ไฟล์ถูกลบไปแล้ว")
# element id ที่ถูกถอดออก ห้ามถูก query ในสคริปต์ของหน้าเดียวกัน
for _f in sorted(glob.glob("*.html")):
    _t = read(_f)
    # ต้องเป็นการอ้าง id จริง ๆ — getElementById(...) หรือ querySelector('#id')
    #   (ห้ามจับ querySelectorAll('tbody tr') ที่เป็น tag selector)
    # (?!\s*\+) กันกรณีประกอบ id แบบ getElementById('bulkBar' + suffix) ซึ่ง id จริงคือ bulkBarW/bulkBarR
    _ids = set(re.findall(r"""getElementById\(\s*['"]([A-Za-z][\w-]*)['"]\s*\)""", _t))
    _ids |= set(re.findall(r"""querySelectorAll?\(\s*['"]#([A-Za-z][\w-]*)['"]\s*\)""", _t))
    for _id in sorted(_ids):
        if _id in ("sidebar", "toast-stack", "statGrid"):
            continue   # sbp.js เป็นคนสร้าง หรือเป็น hook ที่ตั้งใจให้ว่าง
        if f'id="{_id}"' not in _t and f"id='{_id}'" not in _t and f'id=\\"{_id}' not in _t:
            _ghost_bad.append(f"{_f}: สคริปต์ query `#{_id}` แต่ไม่มี element นี้ในหน้า (dead code)")
check("อ้างไฟล์/element ที่ถูกลบไปแล้ว", sorted(set(_ghost_bad))[:12])

# 71) คอลัมน์ของตารางระบบเดิมที่อ้างผ่าน alias ใน SQL ต้องมีจริงใน db-schema-sps_store.md
#   เพิ่ม 2026-09-08 ตอนไล่ API/DB เทียบกับ repo ที่เพิ่งวิเคราะห์ — เดิมข้อ 44 ตรวจเฉพาะ
#   `ตาราง.คอลัมน์` แบบเต็มชื่อ ยังไม่ครอบกรณี `FROM fcs_qssi_score q ... q.month`
_alias_bad: list[str] = []
_schema_file = os.path.join("SBP", "db-schema-sps_store.md")
if os.path.exists(_schema_file):
    _sch = read(_schema_file)
    _legacy_tabs: dict[str, set] = {}
    for _m in re.finditer(r"^### ([a-z_][a-z_0-9]*)\n([\s\S]*?)(?=\n### |\Z)", _sch, re.M):
        _legacy_tabs[_m.group(1)] = set(
            re.findall(r"^\| *\d+ *\| *`([a-z_][a-z_0-9]*)`", _m.group(2), re.M))
    for _f in DOC_FILES:
        if not _f.endswith(".md"):
            continue
        for _blk in re.findall(r"```sql\n([\s\S]*?)```", read(_f)):
            _c = re.sub(r"--[^\n]*", "", _blk)
            for _tb, _al in re.findall(r"\b(?:FROM|JOIN)\s+([a-z_][a-z_0-9]*)\s+([a-z][a-z0-9]?)\b", _c):
                if _tb not in _legacy_tabs:
                    continue
                for _col in re.findall(r"\b" + re.escape(_al) + r"\.([a-z_][a-z_0-9]*)\b", _c):
                    if _col not in _legacy_tabs[_tb]:
                        _alias_bad.append(f"{_f}: `{_tb} {_al}` → `{_al}.{_col}` "
                                          f"ไม่มีคอลัมน์นี้ใน {_schema_file}")
    # 🔴 เพิ่ม 2026-09-14 — ต้องสแกน **โค้ด batch job** ด้วย ไม่ใช่เฉพาะบล็อก ```sql ในเอกสาร
    #   รอบตรวจที่ห้าพบว่า Job 6/8/8b/12 อ้างคอลัมน์ที่ไม่มีจริงถึง 4 จุด แล้วรอดมาได้
    #   เพราะกฎนี้มองแค่ไฟล์ .md ส่วนโค้ดจริงอยู่ใน .ts ของอีก repo
    #   (ตัวเต็มที่ให้ PostgreSQL parse จริงอยู่ที่ tools/check_sgi_sql_columns.py ซึ่งต้องใช้ docker)
    _job_src = os.path.join("SBP", "srm-sps-spsap-sop-sgi-batch", "src", "modules", "sgi")
    if os.path.isdir(_job_src):
        for _name in sorted(os.listdir(_job_src)):
            if not _name.endswith(".ts") or _name.endswith(".spec.ts"):
                continue
            _raw = re.sub(r"--[^\n]*", "", read(os.path.join(_job_src, _name)))
            # ⚠️ ต้องแยกทีละ template literal — alias ตัวเดียว (`s`) ถูกใช้กับคนละตารางในคนละคำสั่ง
            #    ถ้าสแกนทั้งไฟล์รวดเดียวจะได้ false positive ทันที
            for _c in re.split(r"`", _raw):
                for _tb, _al in re.findall(
                        r"\b(?:FROM|JOIN)\s+\$\{this\.schema\}\.([a-z_][a-z_0-9]*)\s+([a-z][a-z0-9_]?)\b", _c):
                    if _tb not in _legacy_tabs:
                        continue
                    for _col in re.findall(r"\b" + re.escape(_al) + r"\.([a-z_][a-z_0-9]*)\b", _c):
                        if _col not in _legacy_tabs[_tb]:
                            _alias_bad.append(f"{_name}: `{_tb} {_al}` → `{_al}.{_col}` "
                                              f"ไม่มีคอลัมน์นี้ใน {_schema_file}")
check("SQL อ้างคอลัมน์ของตารางระบบเดิมผิด (ผ่าน alias)", sorted(set(_alias_bad))[:12])

# 58) ห้ามเขียนช่วงเลข batch job ด้วยมือ — ชุดงานโตแล้วข้อความจะตกยุคทันที
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): ยังค้าง "Jobs 2-10 + 8b" อยู่ 4 ที่ หลังเพิ่ม Job 11/12 เมื่อ 2026-09-02
#   และ LLDD-To-Be ระบุแค่ "Job 2-6, Job 10" ทั้งที่ทุก job เป็นงานฐานราก TB-0 หมด
#   ข้อยกเว้น: ประโยคที่อ้าง "เอกสารต้นทาง Batch v4.0" ซึ่งมีแค่ 2-10 + 8b จริง ๆ ถือว่าถูก
_jobrange_bad: list[str] = []
try:
    import build_lldd_documents as _BJ
    _n_jobs = len(_BJ.job_numbers())
    # จับเฉพาะสำนวน "ชุดเต็ม" แบบเก่า คือช่วงจบที่ 10 แล้วพ่วง 8b — ช่วงย่อยอย่าง "Jobs 2–3"
    # ที่ระบุว่าขั้นตอนไหนใช้ job ใด เป็นการเขียนที่ถูกต้อง ไม่ใช่การอ้างชุดทั้งหมด
    _RANGE = re.compile(r"Jobs?\s*2\s*[-–]\s*(10)\s*(?:\+|และ|/)\s*8b")
    # รวม SRS ที่ส่งมอบด้วย — ไฟล์นั้นสร้างจาก snapshot จึงตกยุคได้เงียบ ๆ (เจอจริง 2026-09-07)
    # 2026-09-08: เดิมสแกนแค่ LLDD/ + living docs 4 ไฟล์ จึงหลุด job-batch.html (คอมเมนต์หัวไฟล์)
    # และ .claude/skills/**/domain.md (EM-07) — ขยายให้ครอบทุกไฟล์เอกสาร + skill
    _scan_files = list(DOC_FILES)
    _scan_files += glob.glob("output/srs/*.md")
    _scan_files += glob.glob(".claude/skills/**/*.md", recursive=True)
    for _f in _scan_files:
        if not os.path.exists(_f):
            continue
        for _n, _l in enumerate(read(_f).split("\n"), 1):
            _m = _RANGE.search(_l)
            if not _m or int(_m.group(1)) >= 12:
                continue
            _ctx = _l
            if ("v4.0" in _ctx or "Batch v4.0" in _ctx or "11" in _ctx.split(_m.group(0))[-1][:60]
                    or "12 job" in _ctx or "12 ตัว" in _ctx):
                continue   # อ้างเอกสารต้นทาง หรือมีการเติม Job 11/12 กำกับไว้แล้ว
            _jobrange_bad.append(f"{_f}:{_n} เขียน `{_m.group(0)}` แต่ชุดจริงมี {_n_jobs} job — "
                                 "ใช้ job_list_label() แทนการพิมพ์ช่วงเลขเอง")
except Exception as _e:   # pragma: no cover
    _jobrange_bad.append(f"ตรวจช่วงเลข job ไม่ได้: {_e}")
check("ข้อความอ้างช่วง batch job ตกยุค", sorted(set(_jobrange_bad)))

# 59) skeleton ห้ามมี stub ที่ "ผ่านเงียบ ๆ" และห้ามมี SQL ที่เป็นช่องว่างเปล่า
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): method ตัดสินใจของ job คืน `return true` ทิ้งไว้
#   — stub แบบนี้ deploy ขึ้น prod ได้โดยไม่มีใครรู้เพราะมันไม่ล้ม · ต้อง throw เท่านั้น
#   ส่วน `throw new NotImplementedException(...)` **ถือว่าถูก** — ล้มดัง ไม่ใช่ผ่านเงียบ
_stub_bad: list[str] = []
_SILENT = [
    (r"return true;\s*//\s*TODO", "method ตัดสินใจคืน true ทิ้งไว้ — stub ที่ผ่านเสมอ ต้อง throw แทน"),
    (r"return false;\s*//\s*TODO", "method ตัดสินใจคืน false ทิ้งไว้ — stub ที่ไม่ผ่านเสมอ ต้อง throw แทน"),
    (r"<h1[^>]*>\{/\*\s*TODO", "หัวข้อหน้าจอยังเป็น TODO ทั้งที่ชื่อหน้าจออยู่ในเอกสารแล้ว"),
]
for _f in DOC_FILES:
    if not (_f.startswith("LLDD/md/") and _f.endswith(".md")):
        continue
    _t = read(_f)
    for _pat, _why in _SILENT:
        if re.search(_pat, _t):
            _stub_bad.append(f"{_f}: {_why}")
    for _blk in re.findall(r"```sql\n([\s\S]*?)```", _t):
        if re.search(r"WHERE\s*/\*\s*TODO", _blk):
            _stub_bad.append(f"{_f}: SQL ยังมี `WHERE /* TODO */` — เขียนเงื่อนไขจริงหรือระบุคอลัมน์ที่ต้องเลือก")
check("skeleton มี stub ที่ผ่านเงียบ ๆ", sorted(set(_stub_bad)))

# 60) หน้า HTML ที่มีความกว้างตายตัว ต้องมีกล่องเลื่อนของตัวเอง ไม่ดันทั้งหน้า
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): 6 หน้าใน output/diagrams มี .sheet{width:1580-1878px}
#   ล้นทั้งบน desktop 1440px และมือถือ · แผ่นโปสเตอร์แบบนี้ทำ responsive แบบพับเนื้อหาไม่ได้
#   (เลย์เอาต์ผูกกับความกว้าง) วิธีที่ถูกคือให้ **กล่อง** เลื่อน ไม่ใช่ให้ทั้งหน้าเลื่อน
_fixedw_bad: list[str] = []
for _f in sorted(glob.glob("output/diagrams/*.html") + glob.glob("*.html")):
    _t = read(_f)
    _m = re.search(r"\.sheet\s*\{[^}]*?width:\s*(\d{3,})px", _t)
    if not _m:
        continue
    if 'class="sheet-scroll"' not in _t:   # ต้องมี div ครอบจริง ไม่ใช่แค่มี CSS ประกาศไว้
        _fixedw_bad.append(f"{_f}: .sheet กว้างตายตัว {_m.group(1)}px แต่ไม่มี .sheet-scroll ครอบ "
                           "— หน้าจะล้นทั้ง desktop และมือถือ")
    elif "@media print" not in _t:
        _fixedw_bad.append(f"{_f}: มีกล่องเลื่อนแล้วแต่ไม่มี @media print — ตอนพิมพ์จะโดนตัด")
check("หน้ากว้างตายตัวไม่มีกล่องเลื่อน", _fixedw_bad)

# 61) ตารางในหน้า HTML ที่ generate ต้องมีกล่องเลื่อน — และต้องแก้ที่ "ตัวสร้าง" ไม่ใช่ที่ output
#   เจอจริง 2026-09-07: แก้ LLDD/index.html ตรง ๆ แล้ว build รอบถัดไปลบทิ้ง (เกิดซ้ำ 2 ครั้ง
#   ทั้งเรื่อง favicon และเรื่องกล่องเลื่อน) · ตรวจที่ผลลัพธ์เพื่อจับว่าตัวสร้างยังไม่ได้แก้
#   ตรวจที่ "ตัวสร้าง" โดยตรง เพราะนั่นคือจุดที่ต้องแก้ — ถ้าไปแก้ไฟล์ output จะโดน build ทับ
#   (ไม่ตรวจนับจำนวน <table> ในผลลัพธ์ เพราะบางตารางอยู่ในกล่องเลื่อนของ layout อยู่แล้ว
#    ความถูกต้องจริงยืนยันด้วยการวัดใน browser ที่ 390px/1440px ไม่ใช่ด้วยการนับ tag)
_gentbl_bad: list[str] = []
for _src, _what in ((os.path.join("tools", "build_lldd_documents.py"), "พอร์ทัล LLDD/index.html"),
                    (os.path.join("tools", "build_er_diagram.py"), "หน้า ER er-sgi-complete.html")):
    if not os.path.exists(_src):
        continue
    _t = read(_src)
    if "table-scroll" not in _t and "tbl-scroll" not in _t:
        _gentbl_bad.append(f"{_src}: ไม่มีกล่องเลื่อนของตารางใน{_what} "
                           "— ห้ามแก้ที่ไฟล์ output เพราะ build รอบถัดไปจะลบทิ้ง")
check("ตารางในหน้าที่ generate ไม่มีกล่องเลื่อน", _gentbl_bad)

# 62) กฎ "ยอดชดเชย 0 เดือน 1–3" ต้องระบุปลายทางเป็น 08 เท่านั้น
#   เจอจริง 2026-09-07 (ผู้ใช้ชี้): ยังค้าง `01` อยู่ 7 ที่ รวม workflow.md และ api.md ซึ่งเป็น
#   แหล่งความจริงหลัก · มติ 2026-09-01 เปลี่ยนปลายทางจาก 01 เป็น 08 แล้ว
#   dev ที่อ่าน Job 8b จะเปิด workflow ผิด state ทั้งชุด — ผลกระทบถึงหน้าจอและ test case
_zero_bad: list[str] = []
_ZERO_CTX = re.compile(
    r"(?:ยอดชดเชย(?:เป็น)? *0|ยอด *0)[^\n|]{0,80}?(?:เดือน(?: ?ที่)? *1\s*[–\-]\s*3|1\s*[–\-]\s*3 *เดือน|ไม่เกิน 3 เดือน|<= *3 *เดือน|≤ *3 *เดือน)[^\n|]{0,90}")
for _f in DOC_FILES:
    _t = read(_f)
    # ตัดทีละ "ช่อง" (บรรทัด หรือเซลล์ตาราง) แล้วตัดสินจากทั้งช่อง ไม่ใช่หน้าต่างตัวอักษร
    for _line in _t.split("\n"):
        for _cell in (_line.split("|") if "|" in _line else [_line]):
            if not _ZERO_CTX.search(_cell):
                continue
            # ตัดวันที่ออกก่อน ไม่งั้น "2026-09-01" จะถูกนับเป็นการอ้างขั้น 01
            _probe = re.sub(r"\d{4}-\d{2}-\d{2}", " ", _cell)
            if not re.search(r"(?<![\d-])01(?![\d-])", _probe):
                continue
            # ระบุ 08 หรือเรียกด้วย "ชื่อขั้น" ของ 08 ไว้แล้ว = ถูกต้อง (เลข 01 ที่เหลือคือค่าเดิม)
            if "08" in _probe or "เจ้าหน้าที่ SBP DSA" in _probe:
                continue
            _zero_bad.append(f"{_f}: `{' '.join(_cell.split())[:90]}` — ปลายทางต้องเป็น 08 (มติ 2026-09-01)")
check("กฎยอดชดเชย 0 ระบุปลายทางผิดเป็น 01", sorted(set(_zero_bad)))

# ---------------------------------------------------------------- #72 sta/ack
# มติ 2026-09-08 (ข้อ 2.13): ตัด POST /sgi/interface/sta/ack ทิ้ง — สเปก STA
# (STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md) มีแค่ 3 ข้อความบน RabbitMQ ไม่มี ACK แบบ HTTP
# ถ้าเส้นนี้โผล่กลับมาเป็น endpoint/สถานะ ACKED ที่ไหน แปลว่ามีคนเขียนย้อนมติ
_ack_bad = []
_ACK_OK = ("ตัด", "~~", "หมดความเสี่ยง", "ไม่มี ACK", "ถูกตัด", "2026-09-08", "ไม่ใช่ ACK")
for _f in DOC_FILES:
    _t = read(_f)
    for _line in _t.split("\n"):
        if "sta/ack" in _line and not any(k in _line for k in _ACK_OK):
            _ack_bad.append(f"{_f}: `{' '.join(_line.split())[:90]}` — เส้นนี้ถูกตัดแล้ว (ข้อ 2.13)")
        if "'ACKED'" in _line or '"ACKED"' in _line or "=ACKED" in _line or "= ACKED" in _line:
            if not any(k in _line for k in _ACK_OK):
                _ack_bad.append(f"{_f}: `{' '.join(_line.split())[:90]}` — status ไม่มีค่า ACKED แล้ว ใช้ COMPLETED / outbox_status = CONFIRMED")
check("อ้าง POST /sgi/interface/sta/ack หรือสถานะ ACKED ที่ตัดไปแล้ว (ข้อ 2.13)", sorted(set(_ack_bad)))

# ------------------------------------------------------- #73 ตัวเลขข้อค้างใน DECISIONS
# เจอจริง 2026-09-08: หัวข้อบอก "15 ข้อ" แต่ไล่นับแถวจริงได้ 16 — ตัวเลขสรุปเขียนมือจึงค้างทุกครั้งที่ปิดข้อ
_dec_bad = []
_dec_f = "DECISIONS-รอตัดสินใจ.md"
if os.path.exists(_dec_f):
    _dt = read(_dec_f).split("\n")
    _grp, _cnt = None, {}
    for _line in _dt:
        _m = re.match(r"^## .*กลุ่ม (\d)", _line)
        if _m:
            _grp = _m.group(1); _cnt.setdefault(_grp, 0)
        if _grp and re.match(r"^\| \*\*\d+\.\d+\*\*", _line):
            if "✅" not in _line.split("|")[1]:
                _cnt[_grp] += 1
        elif _grp and re.match(r"^### \d+\.\d+ ", _line):
            _cnt[_grp] += 1
    _open = sum(_cnt.values())
    _head = read(_dec_f)
    for _lbl, _pat, _want in [
        ("ตารางสรุปส่วนที่ 1", r"\*\*เรื่องที่รอตัดสินใจ\*\* \| 🟠 \*\*(\d+) ข้อ\*\*", _open),
        ("หัวข้อส่วนที่ 2", r"# ส่วนที่ 2 · เรื่องที่ยังต้องตัดสินใจ \((\d+) ข้อ\)", _open),
        ("บรรทัดแบ่งกลุ่ม", r"กระทบ schema/สัญญา \*\*(\d+)\*\*", _cnt.get("2", 0)),
    ]:
        _m2 = re.search(_pat, _head)
        if not _m2:
            _dec_bad.append(f"{_lbl}: หาไม่เจอ — รูปแบบเปลี่ยนไป guard ตามไม่ทัน")
        elif int(_m2.group(1)) != _want:
            _dec_bad.append(f"{_lbl}: เขียน {_m2.group(1)} แต่ไล่นับแถวจริงได้ {_want}")
check("ตัวเลขข้อค้างใน DECISIONS ไม่ตรงกับจำนวนแถวจริง", sorted(set(_dec_bad)))

# ------------------------------------------------- #74 ตารางลูกที่ FK ไป doc_no
# เจอจริง 2026-09-08: คอมเมนต์ DDL เขียน "ตารางลูก 8 ตัว ... FK ด้วย doc_no แบบ NOT NULL"
# แต่ database.md กับ LLDD-BE-Data-Migration-Cutover นับ 6 — ของจริงคือ FK 8 ตาราง ในนั้น
# NOT NULL แค่ 6 (compensation_histories.ref_doc_no กับ interface_transactions.doc_no เป็น nullable)
_fk_bad = []
_fk_all, _fk_nn, _cur = [], [], None
for _line in ddl.split("\n"):
    _m = re.match(r"CREATE TABLE (\w+)", _line)
    if _m:
        _cur = _m.group(1)
    if "REFERENCES sgi_compensation_documents(doc_no)" in _line:
        _fk_all.append(_cur)
        if "NOT NULL" in _line:
            _fk_nn.append(_cur)
for _f in DOC_FILES:
    for _line in read(_f).split("\n"):
        _m2 = re.search(r"ตารางลูก(?:ทั้ง)?\s*(\d+)\s*ตัว[^\n]{0,140}?NOT NULL", _line)
        if _m2 and int(_m2.group(1)) != len(_fk_nn):
            _fk_bad.append(f"{_f}: เขียน 'ตารางลูก {_m2.group(1)} ตัว ... NOT NULL' แต่ DDL มี {len(_fk_nn)} ตัวที่ NOT NULL (FK ทั้งหมด {len(_fk_all)})")
        _m3 = re.search(r"ตารางลูกทั้ง\s*(\d+)\s*FK ไป", _line)
        if _m3 and int(_m3.group(1)) != len(_fk_nn):
            _fk_bad.append(f"{_f}: เขียน 'ตารางลูกทั้ง {_m3.group(1)} FK ไป doc_no' แต่ DDL มี {len(_fk_nn)} ตัวที่ NOT NULL")
check("จำนวนตารางลูกที่ FK doc_no แบบ NOT NULL ไม่ตรงกับ DDL", sorted(set(_fk_bad)))

# --------------------------------------------- #75 job ที่ consumer เป็นตัวกระตุ้น
# เจอจริง 2026-09-08: Job 11 ประกาศ trigger = "ข้อความจากคิว (1 ข้อความ = 1 การรัน)"
# แต่ฟิลด์ cron ยังเป็น "*/10 * * * *" (drain-then-exit ของดีไซน์เก่า) แล้วเลขนั้นไหลไป LLDD + SRS
_cron_bad = []
try:
    import build_lldd_documents as _BC
    for _j in _BC.read_js_array_from_html("job-batch.html", "JOBS"):
        _trig = " ".join(str(_p) for _row in _j.get("params", []) for _p in _row)
        # ต้องเป็น "รับ" ข้อความเท่านั้น — Job 6 พูดถึง RabbitMQ เหมือนกันแต่เป็นฝั่ง publish
        _consumer_driven = ("job consume เอง" in _trig or "1 ข้อความ = 1" in _trig)
        _has_cron = bool(re.match(r"^[\d*/, -]+$", str(_j.get("cron", "")).strip()))
        # ข้อยกเว้น: job ที่ประกาศ "โหมด safety-net" ไว้ชัดเจน (เช่น Job 5 ที่ยังสแกนไฟล์เองได้
        # ถ้า consumer ไม่ยิงมา) — cron ของมันคือตารางของโหมดสำรอง ไม่ใช่ตัวกระตุ้นหลัก
        _blob = _trig + str(_j.get("desc", "")) + str(_j.get("cronTh", ""))
        _fallback = "safety-net" in _blob or "สำรอง" in _blob
        if _consumer_driven and _has_cron and not _fallback:
            _cron_bad.append(
                f"Job {_j['no']}: trigger เป็น consumer (event-driven) แต่ cron ยังเป็น "
                f"`{_j['cron']}` — ตั้ง cron เป็น 'event-driven' ไม่งั้นเลขนี้จะไหลไป LLDD/SRS")
except Exception as _e:   # pragma: no cover
    _cron_bad.append(f"ตรวจ cron ของ job ไม่ได้: {_e}")
check("job ที่ consumer เป็นตัวกระตุ้น แต่ยังประกาศ cron", sorted(set(_cron_bad)))

# ------------------------------------- #76 เลขหัวข้อ Workflow Trigger Event Contract
# เจอจริง 2026-09-08: CLAUDE.md ยังเขียนว่าเอกสาร Job 8b ใช้ `5.95` แต่ของจริงเลื่อนเป็น `5.97`
# ตั้งแต่ 2026-09-02 (5.95 กลายเป็น "การลงทะเบียน job", 5.96 เป็น "เงื่อนไขตัดสิน")
_tec_bad = []
_tec_real = {}
for _f in glob.glob("LLDD/md/**/*.md", recursive=True):
    for _line in read(_f).split("\n"):
        _m = re.match(r"#+ (5\.\d+) Workflow Trigger Event Contract", _line)
        if _m:
            _tec_real.setdefault("Jobs/" if "/Jobs/" in _f else "BE/", set()).add(_m.group(1))
_job_no = sorted(_tec_real.get("Jobs/", set()))
_be_no = sorted(_tec_real.get("BE/", set()))
for _f in ["CLAUDE.md"] + glob.glob(".claude/skills/**/*.md", recursive=True):
    if not os.path.exists(_f):
        continue
    for _line in read(_f).split("\n"):
        if "Workflow Trigger Event Contract" not in _line:
            continue
        # ตรวจเฉพาะเลขที่ "ประกาศว่าใช้ในเอกสารไหน" — เลขที่ถูกพูดถึงในคำอธิบาย
        # (เช่น "เลื่อนจาก `5.95`") ไม่ใช่การประกาศ จึงไม่นับ
        for _n, _who in re.findall(r"[`*]{0,3}(5\.\d+)[`*]{0,3}\s*ในเอกสาร (BE|Job)", _line):
            _want = _be_no if _who == "BE" else _job_no
            if _n not in _want:
                _tec_bad.append(f"{_f}: บอกว่าเอกสาร {_who} ใช้หัวข้อ `{_n}` แต่ของจริงคือ {_want}")
check("เลขหัวข้อ Workflow Trigger Event Contract ที่เอกสารอ้าง ไม่ตรงกับ LLDD", sorted(set(_tec_bad)))

# ------------------------------------------- #77 ปี พ.ศ. หลุดเข้าตัวอย่าง payload
# เจอจริง 2026-09-08: ตัวอย่าง requestId เป็น "job8b-88123-256907" (256907 = พ.ศ. 2569 เดือน 07)
# ทั้งที่ทั้งระบบตกลงใช้ ค.ศ. — ข้อยกเว้นคือไฟล์ interface (FRBC0001/AMS06001) และ argument ของ ALLMAP
_be_bad = []
_BE_OK = ("พ.ศ.", "ALLMAP", "AMS06001", "FRBC0001", "windows-874", "WINDOWS-874", "แปลง", "ระบบเดิม",
          "2569|", "|2569", "SDD", "SRS", "ประชุม")
for _f in DOC_FILES:
    if _f.startswith("SDD-GI-Compensation/") or _f.startswith("STA/"):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if any(k in _line for k in _BE_OK):
            continue
        # ปี พ.ศ. 2560-2579 ที่ติดกับเดือน 2 หลัก หรืออยู่ในรูป doc_no
        for _m in re.finditer(r"(?<![\d.])(25[67]\d)(0[1-9]|1[0-2])(?![\d])|(?<![\d])(25[67]\d)/\d{5}", _line):
            _be_bad.append(f"{_f}:{_i} `{' '.join(_line.split())[:80]}` — พบปี พ.ศ. ในตัวอย่าง ต้องใช้ ค.ศ.")
check("ปี พ.ศ. หลุดเข้าตัวอย่าง payload / doc_no (ต้องเป็น ค.ศ.)", sorted(set(_be_bad)))

# ------------------------------------------ #78 ชื่อเอกสาร LLDD ถูกตัดกลางคำ
# เจอจริง 2026-09-08: _clip() ใน lldd_skeleton_be.py ตัด purpose ของ endpoint จน
# "LLDD-BE-API-Report-and-Master-Data" เหลือ "LLDD-BE-API-Report-and-Ma…"
# = ทำลายข้อมูลชิ้นเดียวที่คอมเมนต์นั้นมีไว้บอก (ให้ไปดูเอกสารไหนต่อ)
_trunc_bad = []
_doc_names = {os.path.basename(_p)[:-3] for _p in glob.glob("LLDD/md/**/*.md", recursive=True)}
for _f in glob.glob("LLDD/md/**/*.md", recursive=True):
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        for _m in re.finditer(r"(LLDD-[A-Za-z0-9-]+)…", _line):
            if _m.group(1) not in _doc_names:
                _trunc_bad.append(
                    f"{_f}:{_i} `{_m.group(1)}…` — ชื่อเอกสารถูกตัดกลางคำ (ไม่ตรงกับเอกสารจริงสักฉบับ)")
check("ชื่อเอกสาร LLDD ถูกตัดกลางคำจนอ้างอิงไม่ได้", sorted(set(_trunc_bad)))

# --------------------------------------------- #79 query ต้องกรอง soft-delete
# เจอจริง 2026-09-08: sgi_document_attachments มี deleted_flag CHAR(1) เป็น soft delete
# และเอกสารเองระบุนโยบายว่า "ต้อง deleted_flag = 'N'" แต่ SQL ของ 3 เส้น
# (list ไฟล์แนบ · ดาวน์โหลดรายไฟล์ · download-all) ไม่ได้กรองเลย
# → ไฟล์ที่ลบไปแล้วยังถูกลิสต์และดาวน์โหลดได้
_soft_bad = []
_SOFT = {"sgi_document_attachments": "deleted_flag"}
for _f in DOC_FILES:
    _t = read(_f)
    for _tbl, _col in _SOFT.items():
        for _m in re.finditer(r"FROM " + _tbl + r"(.{0,450})", _t, re.S):
            _seg = _m.group(1).split(";")[0]
            if _col not in _seg:
                _ln = _t[: _m.start()].count("\n") + 1
                _soft_bad.append(
                    f"{_f}:{_ln} query บน {_tbl} ไม่ได้กรอง {_col} — "
                    f"ไฟล์ที่ลบแบบ soft delete จะยังถูกอ่าน/ดาวน์โหลดได้")
check("query บนตารางที่มี soft delete ไม่ได้กรองคอลัมน์นั้น", sorted(set(_soft_bad)))

# ---------------------------------------- #81 จำนวน index / CHECK ที่เอกสารอ้าง ต้องตรง DDL จริง
# เจอจริง 2026-09-17 (รีวิวภายนอกจับได้): เพิ่ม index รองรับ FK 3 เส้น + CHECK account_month
# ลง DDL แล้ว **แต่ไม่ได้ไล่แก้ที่อื่นที่อ้างตัวเลขไว้** → CLAUDE.md · database.md · llddv2
# ยังเขียน "24 index" กับ "26 CHECK" ค้างอยู่ 5 จุด ทำให้ checklist ติดตั้ง/ตรวจรับคลาดเคลื่อน
# กติกา: ตัวเลขที่เขียนติดคำว่า index/CHECK ในเอกสารหลัก ต้องตรงกับที่นับได้จาก sgi_schema.sql
#        เว้นแต่กำกับว่าเป็นยอดของรอบก่อน (คำว่า "ยอดตอนนั้น" / "เป็นของรอบนั้น")
_cnt_bad = []
_schema_p = "output/sql/sgi_schema.sql"
if os.path.exists(_schema_p):
    _sch = read(_schema_p)
    _live_idx = len(re.findall(r"^CREATE INDEX ", _sch, re.M))
    _live_chk = len(re.findall(r"CHECK \(", _sch))
    for _f in ["CLAUDE.md", "database.md", "LLDD/md/LLDD-Database.md"] + \
              sorted(glob.glob("llddv2/**/*.md", recursive=True)):
        if not os.path.exists(_f):
            continue
        for _ln_no, _ln in enumerate(read(_f).split("\n"), 1):
            if "ยอดตอนนั้น" in _ln or "เป็นของรอบนั้น" in _ln or "ยอดจริงคำนวณสด" in _ln:
                continue
            # บรรทัด DDL ไม่ใช่การอ้างจำนวน — `DEFAULT 0 CHECK (x >= 0)` เคยถูกอ่านว่า "0 CHECK"
            if "CHECK (" in _ln or "CREATE INDEX" in _ln:
                continue
            for _m in re.finditer(r"(\d+)\s*(?:\*\*)?\s*(index|indexes)\b", _ln):
                if int(_m.group(1)) != _live_idx:
                    _cnt_bad.append(f"{_f}:{_ln_no} เขียน {_m.group(1)} index "
                                    f"แต่ sgi_schema.sql มี {_live_idx}")
            for _m in re.finditer(r"(\d+)\s*(?:\*\*)?\s*CHECK\b", _ln):
                if int(_m.group(1)) != _live_chk:
                    _cnt_bad.append(f"{_f}:{_ln_no} เขียน {_m.group(1)} CHECK "
                                    f"แต่ sgi_schema.sql มี {_live_chk}")
check("จำนวน index / CHECK ที่เอกสารอ้าง ไม่ตรงกับ DDL จริง", sorted(set(_cnt_bad)))

# ---------------------------------------- #80 ตาราง owner/ชั่วโมง ต้องตรงกับ owner_workload()
# เจอจริง 2026-09-08: DECISIONS-รอตัดสินใจ.md มีตาราง 2 ชุดในหัวข้อเดียวกัน — ชุดใหม่ถูก
# (Bank 211 · Vava 145 · Pete 139) แต่ชุดเก่ายุค 800 ชม. (Bank 280 · Vava 102 · Pete 84)
# ยังวางอยู่เหมือนเป็นของปัจจุบัน และหัวข้อบอก "เกินเพดาน 126 ชม." ซึ่งไม่ตรงสักชุด
# กติกา: แถว "| ชื่อเล่น | ตัวเลข |" ต้องตรงกับ owner_workload() เว้นแต่กำกับว่า *(ตกยุค)*
_ow_bad = []
try:
    import build_lldd_documents as _BO
    _live = {}
    for _name, _h, _raw, _ in _BO.owner_workload():
        _nick = _name.split("<")[1].split(">")[0] if "<" in _name else _name
        _live[_nick] = _h
    for _f in ["DECISIONS-รอตัดสินใจ.md", "activity-plan-sbp-mall-fe-be.md",
               "estimate-sbpgi-project-hours.md"]:
        if not os.path.exists(_f):
            continue
        for _i, _line in enumerate(read(_f).split("\n"), 1):
            # ยกเว้นเฉพาะแถวที่กำกับ *(ตกยุค)* ชัดเจนเท่านั้น — คำว่า "เดิม" ใช้ไม่ได้
            # เพราะแถวที่ผิดจริงก็มักมี <small>(เดิม …)</small> ติดมาด้วย
            if "ตกยุค" in _line:
                continue
            _m = re.match(r">?\s*\|\s*\*{0,2}(Bank|Vava|Pete|lin|But|New)\*{0,2}[^|]*\|\s*\*{0,2}(\d{2,4})\*{0,2}\s*\|", _line)
            if _m and _live.get(_m.group(1)) != int(_m.group(2)):
                _ow_bad.append(f"{_f}:{_i} {_m.group(1)} = {_m.group(2)} ชม. "
                               f"แต่ owner_workload() ให้ {_live.get(_m.group(1))} — "
                               "ถ้าเป็นตัวเลขเก่าให้กำกับ *(ตกยุค)* ไว้ในแถวนั้น")
except Exception as _e:   # pragma: no cover
    _ow_bad.append(f"ตรวจตาราง owner ไม่ได้: {_e}")
check("ตาราง owner/ชั่วโมง ไม่ตรงกับ owner_workload()", sorted(set(_ow_bad)))

# ----------------------------------- #81 สูตรแยกกลุ่มใน api.md ต้องตรงกับหัวข้อกลุ่มจริง
# เจอจริง 2026-09-08 (ผู้ใช้ชี้): api.md เขียน "(11 + 3 + 8 + 2 + 3 + 3)" = 30 ไม่ใช่ 28
# และยังเป็นเลข Lookup/Interface ก่อนตัด /decisions (DP-9) กับ POST /sgi/interface/sta/ack (ข้อ 2.13)
# กติกา: ตัวเลขในวงเล็บต้องมาจากหัวข้อ "### N. ... (X เส้น" ของไฟล์เดียวกัน และผลรวมต้อง = CANON_ENDPOINTS
_brk_bad = []
_api = read("api.md")
_heads = [int(_m.group(2)) for _m in re.finditer(r"^### ([2-9])\. .*?\((\d+) เส้น", _api, re.M)]
for _m in re.finditer(r"(\d+ กลุ่ม / (\d+) เส้น)\*{0,2}\s*\(([\d\s+]+)\)", _api):
    _parts = [int(_x) for _x in re.findall(r"\d+", _m.group(3))]
    _stated = int(_m.group(2))
    if sum(_parts) != _stated:
        _brk_bad.append(f"api.md :: ({' + '.join(map(str, _parts))}) = {sum(_parts)} "
                        f"แต่บรรทัดเดียวกันบอก {_stated} เส้น")
    if _parts != _heads:
        _brk_bad.append(f"api.md :: สูตรแยกกลุ่ม {_parts} ไม่ตรงกับหัวข้อกลุ่มจริง {_heads}")
    if sum(_parts) != CANON_ENDPOINTS:
        _brk_bad.append(f"api.md :: สูตรแยกกลุ่มรวมได้ {sum(_parts)} แต่ CANON_ENDPOINTS = {CANON_ENDPOINTS}")
if _heads and sum(_heads) != CANON_ENDPOINTS:
    _brk_bad.append(f"api.md :: หัวข้อกลุ่มรวมได้ {sum(_heads)} แต่ CANON_ENDPOINTS = {CANON_ENDPOINTS}")
check("สูตรแยกกลุ่มใน api.md ไม่ตรงกับหัวข้อกลุ่ม/ยอดรวม", sorted(set(_brk_bad)))

# ------------------------------- #82 อ้าง endpoint ที่ถูกตัดไปแล้วว่ายังใช้อยู่
# เจอจริง 2026-09-08 (ผู้ใช้ชี้): workflow.md:380 ต้นบรรทัดเขียน "Lookup 2" ถูก
# แต่กลางบรรทัดเดียวกันยังบอก "กลุ่ม Lookup เหลือ 3 เส้น" และลิสต์ `/decisions` ที่ตัดไปตั้งแต่ DP-9
# กติกา: ชื่อเส้นที่ถูกตัดแล้ว ถ้าโผล่ในเอกสารต้องมีคำกำกับว่าตัดแล้ว/ประวัติ
_cut_bad = []
_CUT_EPS = {
    "/decisions": "ตัดตามมติ DP-9 (2026-08-10) — ใช้ GET /common/common-code?codeType=SGI_DECISION",
    "/dashboard/summary": "ตัด 2026-08-06 พร้อมการถอด stat card",
    "/stores/search": "ใช้ GET /store/search ของระบบเดิม",
    "/branch-types": "ใช้ GET /common/common-code ของระบบเดิม",
}
_CUT_OK = ("ตัด", "~~", "เดิม", "ยกเลิก", "ประวัติ", "แทน", "ถูกลบ", "หมดความเสี่ยง", "→",
           "ถอด", "ออกแล้ว", "deleted", "removed", "dropped", "was cut")
# ไฟล์ที่เป็น "ภาพถ่ายลงวันที่" — เนื้อในตกยุคได้ แต่ต้องมีป้ายเตือนที่หัวไฟล์
_SNAPSHOT_FILES = {"LLDD-Phase4-4.3-SBP-Operating-Management-Income-Guarantee.md": "ห้ามใช้เป็นสเปกปัจจุบัน"}
for _f, _banner in _SNAPSHOT_FILES.items():
    if os.path.exists(_f) and _banner not in read(_f)[:2000]:
        _cut_bad.append(f"{_f} :: เป็นเอกสารภาพถ่ายลงวันที่ แต่ป้ายเตือน '{_banner}' ที่หัวไฟล์หายไป")
for _f in DOC_FILES:
    if _f.startswith("SDD-GI-Compensation/") or _f in _SNAPSHOT_FILES:
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        for _ep, _why in _CUT_EPS.items():
            # ต้องเป็นการอ้างเส้นแบบ path จริง ไม่ใช่คำธรรมดา
            if not re.search(r"[`/\s]" + re.escape(_ep) + r"[`\s,)]", _line):
                continue
            if any(_k in _line for _k in _CUT_OK):
                continue
            # แถวตารางแมป "เส้นที่ตัด | เส้นของระบบเดิมที่ใช้แทน" — ตัวแทนอยู่ในแถวเดียวกันแล้ว
            if _line.lstrip().startswith("|") and re.search(r"/(store|common|statement|api)/", _line):
                continue
            _cut_bad.append(f"{_f}:{_i} อ้าง `{_ep}` โดยไม่บอกว่าถูกตัดแล้ว — {_why}")
check("อ้าง endpoint ที่ถูกตัดไปแล้วเหมือนยังใช้อยู่", sorted(set(_cut_bad)))

# ------------------------------------- #83 จำนวนเส้นที่มีแท็บ Flowchart
# เจอจริง 2026-09-08: workflow.md บอก "4 เส้นที่ซับซ้อนมีแท็บ Flowchart" ทั้งที่
# FLOWCHART_BY_PATH เหลือ 3 (เส้นที่ 4 คือ POST /jobs/{jobNo}/run ถูกลบพร้อม Batch Job Admin)
_fc_bad = []
_papi = read("plan-api.html")
_fi = _papi.find("FLOWCHART_BY_PATH")
_fj = _papi.find("\n  };", _fi)
_n_fc = len(re.findall(r"^\s*'(?:GET|POST|PUT|PATCH|DELETE) [^']+':", _papi[_fi:_fj], re.M))
for _f in DOC_FILES:
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        for _m in re.finditer(r"\*{0,2}(\d+) เส้นที่ซับซ้อน\*{0,2}[^\n]{0,40}Flowchart", _line):
            if int(_m.group(1)) != _n_fc:
                _fc_bad.append(f"{_f}:{_i} บอก {_m.group(1)} เส้นมีแท็บ Flowchart "
                               f"แต่ FLOWCHART_BY_PATH มี {_n_fc}")
check("จำนวนเส้นที่มีแท็บ Flowchart ไม่ตรงกับ FLOWCHART_BY_PATH", sorted(set(_fc_bad)))

# --------------------------------- #84 ยอดรวม endpoint ที่พิมพ์ไว้ในเอกสารทุกไฟล์
# เจอจริง 2026-09-08 (ผู้ใช้ชี้): ประโยค "รายการ endpoint ทั้ง 29 เส้นของ SGI" ถูก hardcode
# ไว้ที่เดียวใน generator แล้วกระจายไปค้างใน LLDD 16 ฉบับ (job 12 + BE 4)
# ขณะที่ LLDD-API.md แหล่งหลักเป็น 28 ถูกแล้ว → กฎเดิมจับไม่ได้เพราะดูแค่ api.md/plan-api.html
# กติกา: เลขที่ติดกับคำว่า "เส้นของ SGI" / "เส้น 6 กลุ่ม" / "endpoints" ต้อง = CANON_ENDPOINTS
# เว้นแต่บรรทัดนั้นเป็นบันทึกประวัติ (มีลูกศร → หรือคำว่าตัด/เดิม)
_tot_bad = []
_TOT_OK = ("→", "ตัด", "เดิม", "ยกเลิก", "ประวัติ", "~~", "ตกยุค", "ห้ามใช้เป็นสเปกปัจจุบัน", "ไม่นับ")
# ต้องเป็นสำนวน "ยอดรวมทั้งชุด" จริง ๆ — "2-endpoint group" (กลุ่มข้อมูลผิดปกติ) ไม่ใช่ยอดรวม
_TOT_PAT = re.compile(
    r"(\d+)\s*(?:เส้นของ SGI|เส้น 6 กลุ่ม|เส้น · 6 กลุ่ม|เส้น/6 กลุ่ม)"
    r"|(\d+)-endpoint / 6-group"
    r"|(\d+) endpoints? / 6 (?:groups?|กลุ่ม)")
_scan = list(DOC_FILES) + glob.glob("LLDD/md/**/*.md", recursive=True) \
        + glob.glob(".claude/skills/**/*.md", recursive=True) + glob.glob("output/srs/*.md")
for _f in sorted(set(_scan)):
    if not os.path.exists(_f) or _f.startswith("SDD-GI-Compensation/"):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if any(_k in _line for _k in _TOT_OK):
            continue
        for _m in _TOT_PAT.finditer(_line):
            _num = next((_g for _g in _m.groups() if _g), None)
            if _num and int(_num) != CANON_ENDPOINTS:
                _tot_bad.append(f"{_f}:{_i} เขียน `{_m.group(0).strip()}` "
                                f"แต่ยอดจริงคือ {CANON_ENDPOINTS} เส้น")
check("ยอดรวม endpoint ที่พิมพ์ไว้ในเอกสาร ไม่ตรงกับยอดจริง", sorted(set(_tot_bad)))

# ---------------------------- #85 ประโยค "ตัวเลขปัจจุบัน …" ต้องตรงเสมอ
# เจอจริง 2026-09-08 (ผู้ใช้ชี้): gap-analysis เขียนไทม์ไลน์การตัดยาว ๆ แล้วจบด้วย
# "ตัวเลขปัจจุบัน 20 ตาราง / 29 endpoint 6 กลุ่ม (… Interface 3)" ซึ่งตกยุค 2 รอบ
# (ขาด DP-9 2026-08-10 และข้อ 2.13 2026-09-08)
# ⚠️ กฎ #84 จับไม่ได้เพราะบรรทัดนั้นมี "→"/"ตัด" อยู่ด้วย เลยถูกยกเว้นทั้งบรรทัด —
#    แต่คำว่า "ตัวเลขปัจจุบัน" คือการประกาศค่า ณ วันนี้ ต้องตรงเสมอไม่ว่าบรรทัดจะเล่าประวัติหรือไม่
_cur_bad = []
_CUR_PAT = re.compile(
    r"ตัวเลขปัจจุบัน\**\s*(?:(\d+)\s*ตาราง)?\s*/?\s*(?:(\d+)\s*endpoint)?[^\n]{0,120}")
for _f in DOC_FILES + glob.glob(".claude/skills/**/*.md", recursive=True):
    if not os.path.exists(_f):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        for _m in _CUR_PAT.finditer(_line):
            _tbl, _ep = _m.group(1), _m.group(2)
            if _tbl and int(_tbl) != CANON_TABLES:
                _cur_bad.append(f"{_f}:{_i} 'ตัวเลขปัจจุบัน {_tbl} ตาราง' แต่ของจริง {CANON_TABLES}")
            if _ep and int(_ep) != CANON_ENDPOINTS:
                _cur_bad.append(f"{_f}:{_i} 'ตัวเลขปัจจุบัน {_ep} endpoint' แต่ของจริง {CANON_ENDPOINTS}")
            # ส่วนแจกแจงกลุ่มที่ตามหลังในประโยคเดียวกัน
            _tail = _line[_m.end() - 120:] if _m.end() > 120 else _line[_m.start():]
            for _g, _want in (("Lookup", 2), ("Interface", 2), ("Master Data", 8),
                              ("เอกสาร", 11), ("รายงาน", 2), ("Workflow", 3)):
                _gm = re.search(re.escape(_g) + r"\s+(\d+)", _tail)
                if _gm and int(_gm.group(1)) != _want:
                    _cur_bad.append(
                        f"{_f}:{_i} 'ตัวเลขปัจจุบัน …' แจกแจง {_g} {_gm.group(1)} แต่ของจริง {_want}")
check("ประโยค 'ตัวเลขปัจจุบัน …' ไม่ตรงกับยอดจริง", sorted(set(_cur_bad)))

# ------------------------------------ #86 กลุ่ม sidebar ที่ skill บอก ต้องตรงกับ MODULES
# เจอจริง 2026-09-08: skill/architecture.md ยังลิสต์ `ผู้ดูแลระบบ (Admin)` เป็นกลุ่มปัจจุบัน
# ทั้งที่ MODULES ใน assets/sbp.js เหลือ 4 กลุ่ม (ลบกลุ่ม Admin ทั้งกลุ่มเมื่อ 2026-08-06)
_grp_bad = []
_js = read("assets/sbp.js")
_gi = _js.find("var MODULES")
_gj = _js.find("];", _gi)
_gblk = "\n".join(_l for _l in _js[_gi:_gj].split("\n") if not _l.strip().startswith("//"))
_live_groups = []
for _m in re.finditer(r"group:\s*'([^']+)'", _gblk):
    if _m.group(1) not in _live_groups:
        _live_groups.append(_m.group(1))
for _f in glob.glob(".claude/skills/**/*.md", recursive=True) + ["CLAUDE.md"]:
    if not os.path.exists(_f):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if "กลุ่ม sidebar render" not in _line and "sidebar groups render" not in _line:
            continue
        _named = re.findall(r"`([^`]+)`", _line)
        for _g in _named:
            _gone = any(_k in _line for _k in ("ไม่มีอยู่แล้ว", "ลบ", "is gone", "gone", "removed", "ตัด"))
            if _g in ("ผู้ดูแลระบบ (Admin)", "Admin") and not _gone:
                _grp_bad.append(f"{_f}:{_i} ลิสต์กลุ่ม `{_g}` เป็นกลุ่มปัจจุบัน แต่ MODULES มีแค่ {_live_groups}")
        # ชื่อกลุ่มอาจถูกพูดถึงซ้ำในประโยคเดียวกัน (เช่น "ย้ายไปกลุ่ม `Flow`") — ตัดซ้ำก่อนเทียบลำดับ
        _cur = []
        for _g in _named:
            if _g in _live_groups and _g not in _cur:
                _cur.append(_g)
        if _cur and _cur != _live_groups:
            _grp_bad.append(f"{_f}:{_i} ลำดับกลุ่ม {_cur} ไม่ตรงกับ MODULES {_live_groups}")
check("กลุ่ม sidebar ที่เอกสารระบุ ไม่ตรงกับ MODULES ใน sbp.js", sorted(set(_grp_bad)))

# --------------------------- #87 สำนวน "รอ ACK จาก STA" ที่ขัดกับมติข้อ 2.13
# เจอจริง 2026-09-08 (ผู้ใช้ชี้): แก้ Job 10 ให้ใช้ publisher confirm แล้ว แต่คำอธิบาย
# ยังเป็นสำนวนเดิม — "ACK ค้าง ≥ 1 วัน" (api.md) · "watchdog ACK" (workflow.md)
# · "pending ACK watchdog" (LLDD-BE-Job-Batch-Email-SRM)
# ชื่อ path /interface/pending-ack คงไว้เพื่อ compatibility ได้ แต่ "คำอธิบาย" ต้องไม่สื่อว่ารอ ACK จาก STA
_ackw_bad = []
# 2026-09-09: ขยายให้ครอบคำที่หลุดมาได้ — เจอค้างใน boilerplate ของ Job ทั้ง 12 ฉบับ
# ("transactional outbox + ACK") และในคำอธิบายคอลัมน์/ตาราง ("รับไฟล์/ACK กลับ" · "สถานะ ACK")
_ACKW = ("ACK ค้าง", "watchdog ACK", "pending ACK", "ACK watchdog",
         "ยังไม่มี ACK", "ยังไม่ได้ ACK", "STA ACK callback",
         "outbox + ACK", "และ ACK", "/ACK", "สถานะ ACK", "ACK/purge", "บันทึก ACK")
# บรรทัดที่กำลัง "ปฏิเสธ" สำนวนนั้นอยู่ ถือว่าถูก
_ACKW_OK = ("ไม่ใช่การรอ ACK", "ไม่ใช่ ACK", "ไม่มี ACK", "ห้ามตีความว่ารอ ACK",
            "ถูกตัด", "2026-09-08", "ตัดเมื่อ", "compatibility")
# สำนวนที่ "ผิดเสมอ" ไม่ว่าบรรทัดจะมีคำอธิบาย/วันที่มติกำกับหรือไม่ —
# เพราะเป็นการบรรยายกลไกผิด ไม่ใช่การอ้างอิงประวัติ (เจอจริง 2026-09-09: บรรทัดที่มี
# "(มติ 2026-09-08)" อยู่ด้วย เลยรอดจาก whitelist ระดับบรรทัดไปทั้งบรรทัด)
_ACKW_ALWAYS = ("outbox + ACK", "transactional outbox + ACK", "ACK/purge", "สถานะ ACK", "บันทึก ACK")
for _f in DOC_FILES + glob.glob(".claude/skills/**/*.md", recursive=True):
    if not os.path.exists(_f):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        for _w in _ACKW_ALWAYS:
            if _w in _line:
                _ackw_bad.append(
                    f"{_f}:{_i} ใช้สำนวน `{_w}` — กลไกจริงคือ publisher confirm "
                    "(มติข้อ 2.13) · สำนวนนี้ผิดเสมอ แม้บรรทัดจะมีคำอธิบายกำกับ")
        if any(_k in _line for _k in _ACKW_OK):
            continue
        for _w in _ACKW:
            if _w in _ACKW_ALWAYS:
                continue
            if _w in _line:
                _ackw_bad.append(
                    f"{_f}:{_i} ใช้สำนวน `{_w}` — มติข้อ 2.13 (2026-09-08) เปลี่ยนเป็น "
                    "publisher confirm ของ RabbitMQ แล้ว ไม่มี ACK ระดับธุรกิจจาก STA")
check("คำอธิบายยังสื่อว่ารอ ACK จาก STA (ขัดกับมติข้อ 2.13)", sorted(set(_ackw_bad)))

# ------------------------- #88 พจนานุกรมข้อมูลต้องครบทุกตาราง/ทุกคอลัมน์ใน DDL
# เพิ่ม 2026-09-08 พร้อมเอกสาร LLDD-Database-Dictionary
# เหตุผล: เอกสารอธิบายคอลัมน์จะ "ตามหลัง schema" ทันทีที่มีคนเพิ่มคอลัมน์ใหม่แล้วลืมอธิบาย
#         กฎนี้บังคับให้ DDL กับพจนานุกรมตรงกัน 1:1 ทั้งสองทาง
#         (มีคอลัมน์แต่ไม่มีคำอธิบาย = ผิด · มีคำอธิบายแต่ไม่มีคอลัมน์ = ผิด)
_dict_bad: list[str] = []
try:
    from lldd_db_dictionary import coverage_gaps as _dict_gaps, TABLE_DOCS as _DICT_T
    _dict_bad = list(_dict_gaps())
    # เอกสารนี้ส่งมอบเป็น **PDF อย่างเดียว** (มติผู้ใช้ 2026-09-09) — ไม่มี .md/.docx/.html
    # จึงตรวจจาก PDF: ต้องมีอยู่จริง และต้องมีครบทุกตารางที่พจนานุกรมประกาศไว้
    _dpdf = "LLDD/pdf/LLDD-Database-Dictionary.pdf"
    if not os.path.exists(_dpdf):
        _dict_bad.append(f"{_dpdf} :: ยังไม่ถูกสร้าง — รัน tools/build_lldd_documents.py --formats md,docx,pdf")
    else:
        try:
            _ptxt = subprocess.run(["pdftotext", "-layout", _dpdf, "-"],
                                   capture_output=True, text=True, timeout=90).stdout
        except Exception:
            _ptxt = ""
        if _ptxt:
            for _t in _DICT_T:
                if _t not in _ptxt:
                    _dict_bad.append(f"{_dpdf} :: ไม่มีตาราง {_t} — PDF ค้างเวอร์ชันเก่า ให้ build ใหม่")
            _ddl_cols = __import__("lldd_db_dictionary").ddl_columns_by_table()
            _misscol = [f"{_t}.{_c}" for _t, _cs in _ddl_cols.items() for _c, _ in _cs
                        if _t in _DICT_T and _c not in _ptxt]
            if _misscol:
                _dict_bad.append(f"{_dpdf} :: คอลัมน์ {len(_misscol)} ตัวไม่ปรากฏใน PDF "
                                 f"(เช่น {', '.join(_misscol[:3])}) — เลย์เอาต์ตัดข้อความทิ้ง")
    # ห้ามมี .md/.docx/.html ของเอกสารนี้หลงเหลือ (ถ้ามีแปลว่ามีคนเปิด render_all กลับมา)
    for _leftover in ("LLDD/md/LLDD-Database-Dictionary.md",
                      "LLDD/word/LLDD-Database-Dictionary.docx",
                      "database-dictionary.html"):
        if os.path.exists(_leftover):
            _dict_bad.append(f"{_leftover} :: เอกสารนี้ส่งมอบเป็น PDF อย่างเดียว — ไฟล์นี้ไม่ควรมี")
except Exception as _e:   # pragma: no cover
    _dict_bad.append(f"ตรวจพจนานุกรมข้อมูลไม่ได้: {_e}")
check("พจนานุกรมข้อมูลไม่ครบ/ไม่ตรงกับ DDL", sorted(set(_dict_bad)))

# ------------------------------- #90 batch job ห้ามเรียก @srm/glb-workflow เอง
# มติผู้ใช้ 2026-09-09: workflow lib ใช้กับ flow K2 (เอกสาร/การอนุมัติ) เท่านั้น
# Job 8b เรียก POST /sgi/workflow/instances แทน — ฝั่ง BE เป็นผู้เรียก engine ที่เดียว
# กฎนี้กันไม่ให้ชื่อ function ของ lib ไหลกลับเข้าเอกสารฝั่ง Job อีก
_jw_bad = []
_ENGINE_FN = ("initializeWorkflow", "addPreApprover", "eventWorkflow", "getPermissionEvents",
              "getPendingFlowByUser", "getWorkflowsByUser", "getTransaction", "getHistory")
# อ่านตารางของ engine ด้วย SQL แบบ read-only ไม่ถือว่า "เรียก lib" — ที่ห้ามคือเรียก function ของ lib
_JW_OK = ("ไม่เรียก", "ไม่แตะ", "2026-09-09", "BE เป็นผู้เรียก", "ผ่าน BE API", "ห้าม",
          "อ่านอย่างเดียว", "read-only")
for _f in glob.glob("LLDD/md/Jobs/*.md") + ["job-batch.html"]:
    if not os.path.exists(_f):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if any(_k in _line for _k in _JW_OK):
            continue
        for _fn in _ENGINE_FN:
            if _fn in _line:
                _jw_bad.append(f"{_f}:{_i} อ้าง `{_fn}` ของ @srm/glb-workflow — "
                               "batch job ต้องเรียก POST /sgi/workflow/instances แทน (มติ 2026-09-09)")
# และต้องไม่มีเอกสารฝั่ง Job อยู่ใน WORKFLOW_TRIGGER_CONTRACTS
try:
    import build_lldd_documents as _BW
    _job_keys = [_k for _k in _BW.WORKFLOW_TRIGGER_CONTRACTS if "-Job-" in _k]
    if _job_keys:
        _jw_bad.append(f"WORKFLOW_TRIGGER_CONTRACTS ยังมีเอกสารฝั่ง Job: {_job_keys} — "
                       "ฝั่ง job ไม่มีหัวข้อ trigger event แล้ว (มติ 2026-09-09)")
except Exception as _e:   # pragma: no cover
    _jw_bad.append(f"ตรวจ WORKFLOW_TRIGGER_CONTRACTS ไม่ได้: {_e}")
check("batch job เรียก @srm/glb-workflow เอง (ต้องผ่าน BE API)", sorted(set(_jw_bad)))

# --------------------------- #112 ไฟล์ .sql ต้องตรงกับ generator แบบ "ทุกไบต์"
# เพิ่ม 2026-09-16 — กฎ #91 ตรวจเชิงโครงสร้าง (มี CREATE TABLE ครบไหม) จึง **มองไม่เห็น
# comment ที่ตกยุค** · เจอของจริงวันนี้: แก้จำนวนแถวที่ generator แล้วลืม regenerate
# ไฟล์ .sql บนดิสก์ยังค้าง 23,958,780 ทั้งที่ generator ให้ 24,284,545
# วิธี: generate ใหม่ลง temp แล้วเทียบไบต์ต่อไบต์ — ต่างแม้จุดเดียวคือไฟล์ค้างเวอร์ชันเก่า
_gen_bad: list[str] = []
try:
    import tempfile, shutil, pathlib
    import build_sgi_schema_sql as _BS2
    _real = pathlib.Path("output/sql")
    # temp dir ต้องอยู่ **ในรีโป** — generator คำนวณ path แบบ relative_to(ROOT)
    with tempfile.TemporaryDirectory(dir="output") as _td:
        _tmp = pathlib.Path(_td)
        _saved = _BS2.OUT_DIR
        _BS2.OUT_DIR = _tmp
        try:
            _BS2.main()
        finally:
            _BS2.OUT_DIR = _saved
        for _gf in sorted(_tmp.glob("*.sql")):
            _cur = _real / _gf.name
            if not _cur.exists():
                _gen_bad.append(f"output/sql/{_gf.name} :: ยังไม่ถูกสร้าง — รัน tools/build_sgi_schema_sql.py")
            elif _cur.read_bytes() != _gf.read_bytes():
                _gen_bad.append(f"output/sql/{_gf.name} :: ไม่ตรงกับ generator — ไฟล์ค้างเวอร์ชันเก่า "
                                f"ให้รัน python3 tools/build_sgi_schema_sql.py")
except Exception as _e:                                   # pragma: no cover
    _gen_bad.append(f"ตรวจ determinism ของ output/sql ไม่ได้: {_e}")
check("ไฟล์ .sql ไม่ตรงกับ generator (ค้างเวอร์ชันเก่า)", sorted(set(_gen_bad)))

# --------------------------- #91 สคริปต์ SQL ต้องตรงกับ DDL และต้องปลอดภัย
# เพิ่ม 2026-09-09 พร้อม output/sql/ — สคริปต์ติดตั้ง schema + seed ลงฐาน SBP เดิม
# เหตุผล: ไฟล์ .sql generate จาก DDL ชุดเดียวกับเอกสาร ถ้าใครแก้ DDL แล้วลืม generate ใหม่
#         ไฟล์ที่ DBA เอาไปรันจะไม่ตรงกับเอกสาร — และต้องกันไม่ให้มีคำสั่งแตะระบบเดิม
_sql_bad: list[str] = []
_SQL_DIR = "output/sql"
_sql_main = os.path.join(_SQL_DIR, "sgi_schema.sql")
_sql_seed = os.path.join(_SQL_DIR, "sgi_seed_data.sql")
try:
    import build_sgi_schema_sql as _BS
    if not os.path.exists(_sql_main):
        _sql_bad.append(f"{_sql_main} :: ยังไม่ถูกสร้าง — รัน tools/build_sgi_schema_sql.py")
    else:
        _sm = read(_sql_main)
        _ddl_tables = {_BS.table_of(_st) for _t, _st in _BS.collect()["creates"]}
        for _t2 in sorted(_ddl_tables):
            if f"CREATE TABLE {_t2}" not in _sm:
                _sql_bad.append(f"{_sql_main} :: ขาด CREATE TABLE {_t2} — ไฟล์ค้างเวอร์ชันเก่า ให้ generate ใหม่")
        # ห้ามมีคำสั่งใดแตะตารางที่ไม่ใช่ sgi_
        for _m in re.finditer(r"^(?:CREATE TABLE|ALTER TABLE)\s+(\w+)", _sm, re.M):
            if not _m.group(1).startswith("sgi_"):
                _sql_bad.append(f"{_sql_main} :: {_m.group(0)} แตะตารางที่ไม่ใช่ของ SGI")
        for _kw in ("DROP TABLE", "TRUNCATE", "DELETE FROM"):
            for _ln in _sm.split("\n"):
                if _kw in _ln and not _ln.strip().startswith("--"):
                    _sql_bad.append(f"{_sql_main} :: มี {_kw} ในสคริปต์ติดตั้ง — ต้องไม่มี")
    if not os.path.exists(_sql_seed):
        _sql_bad.append(f"{_sql_seed} :: ยังไม่ถูกสร้าง — รัน tools/build_sgi_schema_sql.py")
    else:
        _ss = read(_sql_seed)
        _sql_rb = os.path.join("output", "sql", "sgi_schema_rollback.sql")
        # seed แตะตารางระบบเดิมได้ แต่ต้อง INSERT อย่างเดียวและรันซ้ำได้
        for _kw in ("UPDATE ", "DELETE FROM", "TRUNCATE", "DROP "):
            for _ln in _ss.split("\n"):
                if _kw in _ln and not _ln.strip().startswith("--"):
                    _sql_bad.append(f"{_sql_seed} :: มี {_kw.strip()} ที่ไม่ใช่คอมเมนต์ — "
                                    "seed ต้อง INSERT อย่างเดียว ห้ามแก้/ลบแถวของระบบเดิม")
        # ⚠️ ห้าม split(";") ตรง ๆ — body_format ของ email_template เป็น HTML ที่มี `&nbsp;`
        #    การแยกแบบไร้เดียงสาจะหั่นกลางคำสั่ง แล้วรายงานว่า "ไม่มี WHERE NOT EXISTS" ทั้งที่มี
        #    (เจอจริง 2026-09-16 ตอนใส่ body_format จริงลง seed)
        def _sql_split(_text: str) -> list:
            _out, _buf, _i, _n, _instr = [], [], 0, len(_text), False
            while _i < _n:
                _c = _text[_i]
                if _instr:
                    _buf.append(_c)
                    if _c == "'":
                        if _i + 1 < _n and _text[_i + 1] == "'":
                            _buf.append(_text[_i + 1]); _i += 2; continue
                        _instr = False
                    _i += 1; continue
                if _c == "'":
                    _instr = True; _buf.append(_c); _i += 1; continue
                if _c == "-" and _i + 1 < _n and _text[_i + 1] == "-":
                    _j = _text.find("\n", _i)
                    _j = _n if _j < 0 else _j
                    _buf.append(_text[_i:_j]); _i = _j; continue
                if _c == ";":
                    _out.append("".join(_buf)); _buf = []; _i += 1; continue
                _buf.append(_c); _i += 1
            if "".join(_buf).strip():
                _out.append("".join(_buf))
            return _out

        # ---- นิยาม workflow ต้องตรงกับ workflow_status_document.md และกับ SGI_DOC_STATUS ----
        # เพิ่ม 2026-09-16 พร้อมกับ tools/build_sgi_workflow_sql.py
        _wf_f = os.path.join("output", "sql", "sgi_workflow_definition.sql")
        _wsd = "workflow_status_document.md"
        if os.path.exists(_wf_f) and os.path.exists(_wsd):
            _wf = read(_wf_f)
            _routes = len(re.findall(r"^INSERT INTO workflow_route", _wf, re.M))
            _trans = [l for l in read(_wsd).split("\n")
                      if l.startswith("|") and not l.startswith("|---")
                      and "State No" not in l and not l.startswith("| - |")]
            if _routes != len(_trans):
                _sql_bad.append(f"{_wf_f} :: มี {_routes} route แต่ {_wsd} มี {len(_trans)} transition")
            _wf_status = set(re.findall(r"INSERT INTO workflow_status[^;]*?SELECT \d+, '([^']+)'", _wf, re.S))
            _seed_status = set(re.findall(r"'SGI_DOC_STATUS', \d+, '\d+', '([^']+)'", _ss))
            for _n in sorted(_wf_status ^ _seed_status):
                _sql_bad.append(f"ชื่อสถานะ \"{_n}\" ไม่ตรงกันระหว่าง workflow_status กับ common_code SGI_DOC_STATUS")
            for _kw in ("UPDATE ", "DELETE FROM", "DROP ", "TRUNCATE", "ALTER ", "CREATE TABLE"):
                for _ln in _wf.split("\n"):
                    if _kw in _ln and not _ln.strip().startswith("--"):
                        _sql_bad.append(f"{_wf_f} :: มี {_kw.strip()} ที่ไม่ใช่คอมเมนต์ — "
                                        "ตาราง workflow_* เป็นของ engine ต้อง INSERT อย่างเดียว")

        # ---- DO block ท้าย seed ต้องตรวจทุกกลุ่มที่ seed ลง ----
        # เจอจริง 2026-09-16: seed ลง 8 กลุ่มแต่ DO ตรวจแค่ 6 — `common_code_type` และ
        # `SGI_APPROVE_LIMIT` ไม่ถูกตรวจเลย = ติดตั้งไม่ครบแล้วยัง COMMIT ผ่าน
        # (ต้นเหตุเดียวกับคำสั่งล้างที่ตกสองตัวนี้ไป — เพิ่มทีหลังแล้วลืมอัปเดตหลายที่พร้อมกัน)
        _do = re.search(r"-- ตรวจผลก่อน COMMIT.*?END \$\$;", _ss, re.S)
        if not _do:
            _sql_bad.append(f"{_sql_seed} :: ไม่มี DO block ตรวจผลก่อน COMMIT")
        else:
            _dob = _do.group(0)
            for _grp, _pat in (("sgi_competitors", r"FROM sgi_competitors"),
                               ("sgi_external_factors", r"FROM sgi_external_factors"),
                               ("common_code_type", r"FROM common_code_type"),
                               ("SGI_DECISION", r"code_type = 'SGI_DECISION'"),
                               ("SGI_DOC_STATUS", r"code_type = 'SGI_DOC_STATUS'"),
                               ("SGI_APPROVE_LIMIT", r"code_type = 'SGI_APPROVE_LIMIT'"),
                               ("mas_param", r"FROM mas_param"),
                               ("email_template", r"FROM email_template")):
                if not re.search(_pat, _dob):
                    _sql_bad.append(f"{_sql_seed} :: DO block ตรวจผลไม่ได้นับ `{_grp}` ที่ seed ลงไว้ — "
                                    "ติดตั้งไม่ครบแล้วจะ COMMIT ผ่าน")
        # ---- ตัวเลขที่หัวไฟล์ประกาศ ต้องตรงกับจำนวน INSERT จริง ----
        _cnt = collections.Counter(re.findall(r"^INSERT INTO (\w+)", _ss, re.M))
        _head_seed = _ss[:_ss.index("BEGIN;")] if "BEGIN;" in _ss else ""
        for _lbl, _pat2, _tbl in (("common_code", r"common_code (\d+) แถว", "common_code"),
                                  ("common_code_type", r"common_code_type (\d+) แถว", "common_code_type"),
                                  ("mas_param", r"mas_param (\d+) แถว", "mas_param"),
                                  ("email_template", r"email_template (\d+) แถว", "email_template")):
            _m2 = re.search(_pat2, _head_seed)
            if _m2 and int(_m2.group(1)) != _cnt[_tbl]:
                _sql_bad.append(f"{_sql_seed} :: หัวไฟล์บอก {_lbl} {_m2.group(1)} แถว "
                                f"แต่ในไฟล์ INSERT จริง {_cnt[_tbl]} แถว")

        # ---- คำสั่งล้าง seed ต้องครอบคลุมทุกตารางระบบเดิมที่ seed แตะ ----
        # เจอจริง 2026-09-16: หัวไฟล์ seed สั่งลบแค่ 3 ตาราง (ไม่มี `common_code_type`) และ
        # `common_code` กรองแค่ 2 code_type ทั้งที่ seed ลง 3 ตัว → ลบตามแล้วเหลือขยะ 4 แถวบนฐาน dev จริง
        # แล้วติดตั้งใหม่จะได้ค่าเก่าค้างเงียบ ๆ เพราะ INSERT ... WHERE NOT EXISTS ข้ามให้
        _seed_ins = {m.group(1) for m in re.finditer(r"^INSERT INTO (\w+)", _ss, re.M)}
        _legacy_ins = {t for t in _seed_ins if not t.startswith("sgi_")}
        _seed_del = set(re.findall(r"^--\s+DELETE FROM (?:sps_store\.)?(\w+)", _ss, re.M))
        for _t in sorted(_legacy_ins - _seed_del):
            _sql_bad.append(f"{_sql_seed} :: seed INSERT ลง `{_t}` แต่คำสั่งล้างในหัวไฟล์ไม่มีตารางนี้ — "
                            "ถอนแล้วจะเหลือขยะ")
        if os.path.exists(_sql_rb):
            _rb_del = set(re.findall(r"^--\s+DELETE FROM (?:sps_store\.)?(\w+)", read(_sql_rb), re.M))
            for _t in sorted(_seed_del ^ _rb_del):
                _sql_bad.append(f"คำสั่งล้างใน seed กับใน rollback ไม่ตรงกันที่ตาราง `{_t}` — "
                                "สองไฟล์ต้องถอนของชุดเดียวกัน")
        # ทุก code_type ที่ seed ลง ต้องถูกคำสั่งล้างครอบคลุม
        _types = set(re.findall(r"INSERT INTO common_code_type[^;]*?SELECT '(\w+)'", _ss, re.S))
        for _ln in re.findall(r"^--\s+DELETE FROM common_code\s.*$", _ss, re.M):
            _in_list = re.search(r"code_type IN \(([^)]*)\)", _ln)
            if _in_list:
                _covered = set(re.findall(r"'(\w+)'", _in_list.group(1)))
                for _t in sorted(_types - _covered):
                    _sql_bad.append(f"{_sql_seed} :: คำสั่งล้าง common_code ไม่ครอบคลุม code_type `{_t}` ที่ seed ลงไว้")

        # ---- email_template ต้องตรงรูปแบบของ "ของเดิม" ไม่ใช่รูปแบบที่เราคิดเอง ----
        # เจอจริง 2026-09-16: seed เขียน subject เป็น `{docNo}` แต่ทั้งตาราง (193 จุด) ใช้ `${docNo}`
        # และเว้น body_format/sender/email_from ว่างไว้ ทั้งที่ 126/126 แถวของระบบเดิมมีครบ
        for _st in _sql_split(_ss):
            if "INSERT INTO email_template" not in _st:
                continue
            for _col in ("body_format", "sender", "email_from"):
                if _col not in _st:
                    _sql_bad.append(f"{_sql_seed} :: INSERT email_template ไม่ได้ใส่คอลัมน์ {_col} — "
                                    "ของระบบเดิมมีครบทุกแถว")
            for _lit in re.findall(r"'((?:[^']|'')*)'", _st):
                for _bad_ph in re.findall(r"(?<!\$)\{([A-Za-z][\w]*)\}", _lit):
                    _sql_bad.append(f"{_sql_seed} :: email_template ใช้ตัวแปร " + "{" + _bad_ph + "}" +
                                    " — ต้องเป็น ${" + _bad_ph + "} ตามรูปแบบของตารางเดิม")

        for _stmt in _sql_split(_ss):
            if "INSERT INTO" in _stmt and "WHERE NOT EXISTS" not in _stmt:
                _mm = re.search(r"INSERT INTO (\w+)", _stmt)
                _sql_bad.append(f"{_sql_seed} :: INSERT ลง {_mm.group(1) if _mm else '?'} "
                                "ไม่มี WHERE NOT EXISTS — รันซ้ำแล้วจะได้แถวซ้ำ")
        # จำนวน master ต้องตรงกับหน้าจอที่เป็นต้นทาง
        _n_comp = len(_BS.read_competitors())
        _n_fact = len(_BS.read_factors())
        if _ss.count("INSERT INTO sgi_competitors") != _n_comp:
            _sql_bad.append(f"{_sql_seed} :: แบรนด์คู่แข่งใน seed ไม่ตรงกับ k2-competitors.html ({_n_comp} รายการ)")
        if _ss.count("INSERT INTO sgi_external_factors") != _n_fact:
            _sql_bad.append(f"{_sql_seed} :: ปัจจัยภายนอกใน seed ไม่ตรงกับ k2-factors.html ({_n_fact} รายการ)")
except Exception as _e:   # pragma: no cover
    _sql_bad.append(f"ตรวจสคริปต์ SQL ไม่ได้: {_e}")
check("สคริปต์ SQL ไม่ตรงกับ DDL หรือมีคำสั่งที่ไม่ปลอดภัย", sorted(set(_sql_bad)))

# ------------------- #92 job ที่ event-driven ต้องไม่มี cron/schedule ในเอกสาร
# เจอจริง 2026-09-09 (ผู้ใช้ชี้): เอกสาร Job 11 บอกพร้อมกันว่าเป็น event-driven
# (consumer เรียก SubmitJob) แต่ก็บอกว่า "ตัวจริงตั้งที่ AWS Batch scheduled event"
# และยังประกาศ SGI_JOB11_CRON ไว้ — เป็นคนละ trigger contract
# ถ้าทีมพัฒนาอ่านแล้วตั้ง schedule ตามนั้น job จะรันซ้อนกับ consumer แล้วประมวลผลข้อความซ้ำ
_ed_bad: list[str] = []
try:
    import build_lldd_documents as _BE2
    _ed_generic: dict[str, list[int]] = {}
    for _j in _BE2.read_js_array_from_html("job-batch.html", "JOBS"):
        if str(_j.get("cron", "")).strip().lower() != "event-driven":
            continue
        _no = _j["no"]
        _slug = str(_no).upper()
        _doc = [_p for _p in glob.glob("LLDD/md/Jobs/*.md")
                if re.search(rf"LLDD-BE-Job-{re.escape(str(_no))}-", os.path.basename(_p))]
        for _p2 in _doc:
            for _i, _line in enumerate(read(_p2).split("\n"), 1):
                # อนุญาตเฉพาะบรรทัดที่ "ห้าม" เท่านั้น
                if "ห้าม" in _line or "ไม่มีและต้องไม่มี" in _line:
                    continue
                if f"SGI_JOB{_slug}_CRON" in _line:
                    _ed_bad.append(f"{_p2}:{_i} job {_no} เป็น event-driven แต่ยังประกาศ "
                                   f"SGI_JOB{_slug}_CRON — จะมีคนเอาไปตั้ง schedule ซ้อนกับ consumer")
                # ข้อความพื้นฐานของ repo ("repo นี้ไม่มี @Cron · ตารางเวลาตั้งที่ AWS Batch")
                # เป็นความจริงที่ใช้ร่วมทุก job — ที่ผิดคือประโยคที่ผูก schedule เข้ากับ *job นี้*
                if re.search(r"ตารางเวลาของ Job\s*" + re.escape(str(_no)) + r"\b", _line) \
                        and "AWS Batch scheduled event" in _line:
                    _ed_bad.append(f"{_p2}:{_i} job {_no} เป็น event-driven แต่ยังบอกว่า "
                                   "'ตารางเวลาของ job นี้ตั้งที่ AWS Batch scheduled event' — "
                                   "ขัดกับ trigger ของ consumer")
                # และถ้ามีข้อความพื้นฐานเรื่อง schedule ต้องมีข้อยกเว้นกำกับไว้ในเอกสารเดียวกัน
                if "AWS Batch scheduled event" in _line and "ยกเว้น" not in _line:
                    _ed_generic.setdefault(_p2, []).append(_i)
                if re.search(r"cron:\s*string", _line):
                    _ed_bad.append(f"{_p2}:{_i} job {_no} เป็น event-driven แต่ config ยังมีฟิลด์ cron")
    # เอกสารของ job event-driven ที่มีข้อความ schedule แบบพื้นฐาน ต้องมีข้อยกเว้นอย่างน้อย 1 แห่ง
    for _p3, _lines in _ed_generic.items():
        if "ยกเว้น" not in read(_p3):
            _ed_bad.append(f"{_p3} :: พูดถึง 'AWS Batch scheduled event' {len(_lines)} จุด "
                           "แต่ไม่มีข้อความยกเว้นบอกว่า job นี้เป็น event-driven ห้ามตั้ง schedule")
except Exception as _e:   # pragma: no cover
    _ed_bad.append(f"ตรวจ job event-driven ไม่ได้: {_e}")
check("job ที่ event-driven ยังมี cron/schedule ในเอกสาร", sorted(set(_ed_bad)))

# ------------- #93 สถานะปลายทางของ outbox ต้องตรงกับโดเมนใน DDL ทุกที่
# เจอจริง 2026-09-09 (ผู้ใช้ชี้): LLDD-BE-API-Document-Workflow-Actions บอกว่าได้ publisher
# confirm แล้ว "update เป็น SENT" แต่ DDL กำหนดว่าขาออกจบที่
# outbox_status = 'CONFIRMED' + status = 'COMPLETED'  (SENT = ยิงแล้วแต่ยังไม่ confirm)
# ถ้าทำตามเอกสารนั้น แถวจะค้างที่ SENT แล้ว Job 10 จะเตือนไม่หยุด
#
# ตรวจเฉพาะประโยคที่ **สั่งเปลี่ยนสถานะ** เท่านั้น — ประโยคที่เป็นคำถามใน decision node
# ("ได้ publisher confirm?") หรือบอกว่าใครเป็นคนเขียน ไม่ใช่คำสั่ง จึงไม่นับ
_ob_bad: list[str] = []
_OB_VERB = r"(update|อัปเดต|ตั้ง|เปลี่ยน|mark|จึง)"
for _f in DOC_FILES:
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if "publisher confirm" not in _line:
            continue
        # ผิดชัดเจน: บอกว่า confirm แล้วให้เป็น SENT
        if re.search(r"publisher confirm[^\n]{0,80}" + _OB_VERB + r"[^\n]{0,30}[`']?SENT", _line):
            _ob_bad.append(f"{_f}:{_i} บอกว่าได้ publisher confirm แล้วตั้งเป็น SENT — "
                           "SENT แปลว่ายิงแล้วแต่ยังไม่ confirm · ปลายทางคือ "
                           "outbox_status = 'CONFIRMED' + status = 'COMPLETED'")
            continue
        # ประโยคที่สั่งเปลี่ยนสถานะหลัง confirm ต้องระบุ CONFIRMED
        if re.search(r"(?<!ไม่)(?<!ยังไม่)(ได้|เมื่อได้|หลังได้)\s*publisher confirm[^\n]{0,60}" + _OB_VERB, _line) \
                and not re.search(r"(ยังไม่|ไม่)ได้\s*publisher confirm", _line) \
                and "CONFIRMED" not in _line:
            _ob_bad.append(f"{_f}:{_i} สั่งเปลี่ยนสถานะหลังได้ publisher confirm "
                           "แต่ไม่ได้ระบุ outbox_status = 'CONFIRMED'")
# และห้ามมีที่ไหนบอกว่าขาออก "จบ" ที่ SENT
for _f in DOC_FILES:
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if re.search(r"(จบที่|สิ้นสุดที่|ปลายทางคือ)\s*[`']?SENT", _line):
            _ob_bad.append(f"{_f}:{_i} บอกว่าขาออกจบที่ SENT — DDL กำหนดให้จบที่ COMPLETED")
check("สถานะปลายทางของ outbox ไม่ตรงกับโดเมนใน DDL", sorted(set(_ob_bad)))

# --------------------- #94 PDF ต้องไม่มีอักขระที่ฟอนต์ไม่มี glyph (กล่อง □)
# เจอจริง 2026-09-09 (ผู้ใช้ชี้): PDF แสดง ⚠️ 🔴 ✅ เป็นกล่อง □ เพราะฟอนต์ที่ใช้สร้าง PDF
# (Arial Unicode) ไม่มี glyph emoji เลย — พบ 964 จุดในชุดเอกสาร
# แก้ด้วย pdf_safe_text() ที่แปลงเป็นสัญลักษณ์ขาวดำตอนเรนเดอร์ PDF (md/html/docx ไม่กระทบ)
# กฎนี้กันไม่ให้ emoji "ตัวใหม่" ที่ยังไม่มีในตารางแปลง หลุดเข้า PDF อีก
_glyph_bad: list[str] = []
try:
    from reportlab.pdfbase.ttfonts import TTFont as _TTF
    import build_lldd_documents as _BG
    _cmap = _TTF("GlyphCheck", _BG.FONT).face.charToGlyph
    # 1) ตารางแปลงต้องครอบคลุมอักขระทุกตัวที่ "ต้นทางเอกสาร" ใช้แล้วฟอนต์ไม่มี
    _srcs = glob.glob("LLDD/md/**/*.md", recursive=True) + glob.glob("tools/*.py")
    _uncovered: dict[str, int] = {}
    for _sf in _srcs:
        for _ch in read(_sf):
            if ord(_ch) > 0x2000 and ord(_ch) not in _cmap:
                if _BG.pdf_safe_text(_ch) == _ch:      # แปลงแล้วยังเหมือนเดิม = ยังไม่มีในตาราง
                    _uncovered[_ch] = _uncovered.get(_ch, 0) + 1
    for _ch, _n in sorted(_uncovered.items()):
        _glyph_bad.append(f"U+{ord(_ch):05X} ({_ch}) ใช้ {_n} จุด แต่ฟอนต์ PDF ไม่มี glyph "
                          "และยังไม่มีในตาราง _PDF_GLYPH_FALLBACK → จะขึ้นเป็นกล่อง □ ใน PDF")
    # 2) ตรวจ PDF ที่สร้างแล้วจริง ๆ (สุ่มไฟล์ใหญ่ที่สุดเพื่อไม่ให้ชุดตรวจช้า)
    _pdfs = sorted(glob.glob("LLDD/pdf/**/*.pdf", recursive=True),
                   key=lambda p2: os.path.getsize(p2), reverse=True)[:4]
    for _pf in _pdfs:
        try:
            _pt = subprocess.run(["pdftotext", "-layout", _pf, "-"],
                                 capture_output=True, text=True, timeout=60).stdout
        except Exception:
            continue
        _miss = sorted({_c for _c in _pt if ord(_c) > 0x2000 and ord(_c) not in _cmap})
        if _miss:
            _glyph_bad.append(f"{_pf} :: มีอักขระที่ฟอนต์ไม่มี glyph "
                              f"{[f'U+{ord(c):05X}' for c in _miss[:5]]} — จะแสดงเป็นกล่อง □")
except Exception as _e:   # pragma: no cover
    _glyph_bad.append(f"ตรวจ glyph ของ PDF ไม่ได้: {_e}")
check("PDF มีอักขระที่ฟอนต์ไม่มี glyph (จะขึ้นเป็นกล่อง)", sorted(set(_glyph_bad)))

# ------------ #95 วันที่หัวไฟล์ + ข้ออ้าง "บล็อก" ที่ปิดไปแล้ว
# เจอจริง 2026-09-09 (ผู้ใช้ชี้): DECISIONS บอกว่า migration ติด F8/F1 อยู่
# ทั้งที่ส่วนประวัติในไฟล์เดียวกันระบุว่าปิดตั้งแต่ 2026-08-21 · และหัวไฟล์ยังเป็น 2026-08-24
# ทั้งที่เนื้อหามีมติถึง 2026-09-08/09
_hdr_bad: list[str] = []
_DATED_DOCS = ("DECISIONS-รอตัดสินใจ.md",)
for _f in _DATED_DOCS:
    if not os.path.exists(_f):
        continue
    _t = read(_f)
    _all = sorted(set(re.findall(r"20\d\d-\d\d-\d\d", _t)))
    _m = re.search(r"\*\*ปรับปรุง:\*\*\s*(20\d\d-\d\d-\d\d)", _t)
    if not _m:
        _hdr_bad.append(f"{_f} :: หาบรรทัด '**ปรับปรุง:**' ไม่เจอ")
    elif _all and _m.group(1) < _all[-1]:
        _hdr_bad.append(f"{_f} :: หัวไฟล์บอกปรับปรุง {_m.group(1)} "
                        f"แต่ในไฟล์มีมติถึง {_all[-1]} — วันที่หัวไฟล์ตกยุค")
    # ข้อที่ปิดไปแล้วต้องไม่ถูกอ้างว่ายัง "บล็อก" อยู่
    for _closed, _when in (("F8/F1", "2026-08-21"), ("F8 + F1", "2026-08-21")):
        for _i, _line in enumerate(_t.split("\n"), 1):
            if _closed in _line and "บล็อก" in _line and "ไม่บล็อกแล้ว" not in _line:
                _hdr_bad.append(f"{_f}:{_i} อ้างว่า {_closed} ยังบล็อกอยู่ "
                                f"แต่ปิดไปแล้วเมื่อ {_when} (ประวัติอยู่ในไฟล์เดียวกัน)")
# ตารางที่สคริปต์ติดตั้งสร้างจริง ห้ามมีเอกสารไหนบอกว่า "สร้างไม่ได้"
# (เจอจริง 2026-09-09: DP-11 เขียนว่า sgi_compensation_histories สร้างไม่ได้
#  ขณะที่ sgi_schema.sql สร้างตารางนี้จริง — ที่ยังตัดสินไม่ได้คือใครเขียนข้อมูล ไม่ใช่ตัวตาราง)
try:
    _sql_txt = read("output/sql/sgi_schema.sql") if os.path.exists("output/sql/sgi_schema.sql") else ""
    _created = set(re.findall(r"CREATE TABLE (\w+)", _sql_txt))
    for _f2 in DOC_FILES:
        for _i2, _l2 in enumerate(read(_f2).split("\n"), 1):
            if "สร้างไม่ได้" not in _l2 or "ไม่ได้บล็อกการสร้างตาราง" in _l2:
                continue
            for _tb in _created:
                if _tb in _l2:
                    _hdr_bad.append(f"{_f2}:{_i2} บอกว่า {_tb} 'สร้างไม่ได้' "
                                    "แต่ output/sql/sgi_schema.sql สร้างตารางนี้จริง")
except Exception as _e:   # pragma: no cover
    _hdr_bad.append(f"ตรวจตารางที่ 'สร้างไม่ได้' ไม่ได้: {_e}")
check("วันที่หัวไฟล์ตกยุค หรืออ้างข้อที่ปิดแล้วว่ายังบล็อก", sorted(set(_hdr_bad)))

# --------------- #96 ตัวกรองบนหน้ารายการ ต้องมี query param รองรับครบ
# เจอจริง 2026-09-09 (ผู้ใช้ชี้ว่า Query Params ไม่ครบ): หน้ารายการมีช่องกรอง 11 ช่อง
# แต่ API ประกาศแค่ year/storeCode/status/page/size — และชื่อยังผิด (storeCode ทั้งที่ SQL
# กับ response ใช้ impactedStoreCode) · endpoint มี page/size ถ้าไม่ส่งตัวกรองขึ้น server
# ตัวกรองจะทำงานแค่แถวในหน้านั้น
_flt_bad: list[str] = []
# ช่องกรองบนหน้าจอ (id ใน k2-list-*.html) -> query param ที่ต้องมี
_SCREEN_FILTER_PARAM = {
    "fSearch": "keyword", "fStatus": "status", "fRegion": "regionCode",
    "fType": "storeType", "fDateFrom": "createdFrom", "fDateTo": "createdTo",
    "fDropMin": "salesDeclineMin", "fDropMax": "salesDeclineMax",
    "fCompMin": "compensationMin", "fCompMax": "compensationMax",
    "fDayMin": "daysPendingMin", "fDayMax": "daysPendingMax",
    "fResult": "result",
}
try:
    import build_lldd_documents as _BF
    _list_specs = {}
    for _t in _BF.topics():
        for _a in (_t.apis or []):
            # ⚠️ ต้องแยกตาม method — POST /sgi/document ใช้ path เดียวกับ GET
            #    ถ้าไม่แยก คีย์ของ POST จะกลบว่า GET ขาดพารามิเตอร์
            if (getattr(_a, "path", "") in ("/api/v1/sgi/document", "/api/v1/sgi/document/tasks")
                    and _a.method.upper() == "GET"):
                _list_specs.setdefault(_a.path, set()).update((_a.request or {}).keys())
    _screen = read("k2-list-waiting.html") + read("k2-list-related.html")
    for _fid, _param in sorted(_SCREEN_FILTER_PARAM.items()):
        if f'id="{_fid}"' not in _screen and f'id="{_fid}R"' not in _screen:
            continue
        for _path, _params in _list_specs.items():
            # daysPending มีเฉพาะกล่องงาน · result มีเฉพาะหน้า "ที่เกี่ยวข้อง"
            if _param.startswith("daysPending") and _path != "/api/v1/sgi/document/tasks":
                continue
            if _param == "result" and _path != "/api/v1/sgi/document":
                continue
            if _param not in _params:
                _flt_bad.append(f"{_path} :: ไม่มี query param `{_param}` ที่รองรับช่องกรอง "
                                f"`#{_fid}` บนหน้ารายการ — endpoint มี page/size "
                                "ถ้าไม่กรองที่ server ตัวกรองจะทำงานแค่แถวในหน้านั้น")
    # ชื่อ param ต้องตรงกับที่ SQL ผูกจริง
    _sql = _BF.api_sql_map().get("GET /api/v1/sgi/document", "")
    if _sql and "storeCode" in " ".join(_list_specs.get("/api/v1/sgi/document", set())) \
            and ":impactedStoreCode" in _sql:
        _flt_bad.append("/api/v1/sgi/document :: query param ใช้ชื่อ `storeCode` "
                        "แต่ SQL ผูก `:impactedStoreCode` — FE จะส่งชื่อผิด")
except Exception as _e:   # pragma: no cover
    _flt_bad.append(f"ตรวจตัวกรองหน้ารายการไม่ได้: {_e}")
# ทุก endpoint ใน SQL_BY_PATH ต้อง parse ออกมาเป็นสตริงได้จริง
# เจอจริง 2026-09-09: เติม SQL ที่มี single quote โดยไม่ escape ทำให้ค่าเป็น None เงียบ ๆ
# แล้วหัวข้อ "SQL จริงต่อ Endpoint" ในเอกสารจะหายไปโดยไม่มีใครรู้
try:
    _smap = _BF.api_sql_map()
    for _k, _v in sorted(_smap.items()):
        if not isinstance(_v, str) or not _v.strip():
            _flt_bad.append(f"SQL_BY_PATH['{_k}'] :: parse ไม่ได้/ว่าง (ได้ {type(_v).__name__}) — "
                            "มักเกิดจาก single quote ใน SQL ที่ยังไม่ escape เป็น \\' ในสตริง JS")
except Exception as _e:   # pragma: no cover
    _flt_bad.append(f"อ่าน SQL_BY_PATH ไม่ได้: {_e}")
check("ตัวกรองบนหน้ารายการไม่มี query param รองรับ", sorted(set(_flt_bad)))

# ------------- #97 query param ที่ประกาศ ต้องตรงกับ bind ใน SQL ทุกเส้น
# ต่อยอดจาก #96 (ผู้ใช้ชี้ว่า Query Params ไม่ครบ) — ทำเป็นกฎทั่วไปกับ **ทุก GET endpoint**
# เจอเพิ่ม 6 เส้นด้วยกฎนี้: /tasks ประกาศ sectionCode ทั้งที่มาจาก JWT ·
#   tracking ประกาศ status/sentFrom/sentTo แต่ SQL ไม่กรอง · master/* ประกาศ active แต่ไม่กรอง ·
#   workflow/summary ประกาศ period แต่ SQL รวมทุกงวด · pending-ack ประกาศ dataName แต่ไม่กรอง ·
#   รายงานประกาศ region/storeType เอกพจน์ที่ตายแล้ว และ periodStatementFrom/To ไม่ตรงกับ :psFrom/:psTo
_qp_bad: list[str] = []
# ค่าที่มาจาก JWT/ระบบ ไม่ใช่ client ส่ง — ไม่ต้องประกาศเป็น query param
_QP_INTERNAL = {"page", "size", "off", "offset", "statusDone", "sgiVersionId", "sectionFromJwt",
                "userId", "empId", "serviceActor", "allowPendingDownload", "thresholdHours",
                "referenceId", "salesSummaryId", "pending"}
try:
    import build_lldd_documents as _BQ
    _sqlmap = _BQ.api_sql_map()
    _specs: dict[str, set] = {}
    for _t in _BQ.topics():
        for _a in (_t.apis or []):
            if _a.method.upper() == "GET" and "/sgi/" in getattr(_a, "path", "") and "*" not in _a.path:
                _specs.setdefault(f"{_a.method} {_a.path}", set()).update((_a.request or {}).keys())

    def _binds(_sql: str) -> set:
        _sql = re.sub(r"::\w+", "", _sql)          # ตัด cast ::date ::text ออกก่อน
        return set(re.findall(r"(?<!:):(\w+)", _sql)) | set(re.findall(r"/\* (\w+) \*/", _sql))

    for _k in sorted(_specs):
        _sql = _sqlmap.get(_k) or ""
        if not _sql or "เงื่อนไขเดียวกับ" in _sql:   # export ใช้เงื่อนไขของ search — ไม่ซ้ำ SQL
            continue
        _b = _binds(_sql)
        _q = _specs[_k]
        _ex = sorted(x for x in _q - _b - _QP_INTERNAL if "{" + x + "}" not in _k)
        _ms = sorted(x for x in _b - _q - _QP_INTERNAL if "{" + x + "}" not in _k)
        for _x in _ex:
            _qp_bad.append(f"{_k} :: ประกาศ query param `{_x}` แต่ SQL ไม่ได้ใช้ — "
                           "ตัวกรองจะไม่ทำงานจริง")
        for _x in _ms:
            _qp_bad.append(f"{_k} :: SQL ผูก `:{_x}` แต่ไม่ได้ประกาศเป็น query param — "
                           "FE จะไม่รู้ว่าต้องส่งอะไร")
except Exception as _e:   # pragma: no cover
    _qp_bad.append(f"ตรวจ query param เทียบ SQL ไม่ได้: {_e}")
check("query param ที่ประกาศ ไม่ตรงกับ bind ใน SQL", sorted(set(_qp_bad)))

# ----------- #98 คอลัมน์บนตารางหน้ารายการ ต้องมี field ใน response
# เจอจริง 2026-09-09: ตารางหน้ารายการมีคอลัมน์ "ผู้ดำเนินการ (เจ้าของงาน)" และ prototype
# สร้างค่าให้จริง แต่ response ของ /sgi/document/tasks ไม่มี field ไหนรองรับเลย
# → FE เรนเดอร์คอลัมน์นั้นไม่ได้จากสัญญาที่เขียนไว้
_col_bad: list[str] = []
_COL_FIELD = {
    "ครั้งที่": "roundNo",
    "เลขที่เอกสาร": "docNo",
    "รหัสร้าน": "impactedStoreCode",
    "ชื่อร้านถูกกระทบ": "impactedStoreName",
    "ภาค": "regionCode",
    "ยอดขายที่ลดลง": "salesDeclinePercent",
    "จำนวนเงินที่ชดเชย": "totalCompensationAmount",
    "ผู้ดำเนินการ (เจ้าของงาน)": "currentOwner",
    "สถานะ": "statusCode",
    "รอ (วัน)": "daysPending",
}
try:
    import build_lldd_documents as _BC2
    _fields: set = set()
    for _t in _BC2.topics():
        for _a in (_t.apis or []):
            if getattr(_a, "path", "") in ("/api/v1/sgi/document", "/api/v1/sgi/document/tasks") \
                    and _a.method.upper() == "GET":
                _items = (_a.response or {}).get("items") or []
                if _items and isinstance(_items[0], dict):
                    _fields.update(_items[0].keys())
    _screen2 = read("k2-list-waiting.html")
    _ths = [re.sub(r"<[^>]+>", "", _x).strip()
            for _x in re.findall(r"<th[^>]*>(.*?)</th>", _screen2, re.S)]
    for _col, _fld in _COL_FIELD.items():
        if _col in _ths and _fld not in _fields:
            _col_bad.append(f"ตารางหน้ารายการมีคอลัมน์ '{_col}' แต่ response ของ "
                            f"/sgi/document(/tasks) ไม่มี field `{_fld}` — FE เรนเดอร์คอลัมน์นี้ไม่ได้")
except Exception as _e:   # pragma: no cover
    _col_bad.append(f"ตรวจคอลัมน์หน้ารายการไม่ได้: {_e}")
check("คอลัมน์บนตารางหน้ารายการไม่มี field ใน response", sorted(set(_col_bad)))

# --------- #99 การ์ดบนหน้าเอกสาร/รายงาน ต้องมีข้อมูลจาก API รองรับ
# เจอจริง 2026-09-09: k2-document.html มี 10 การ์ด แต่ response ของ
# GET /sgi/document/{docNo} ประกาศแค่ impactedStore + newStores —
# คู่แข่ง · ปัจจัยอื่นๆ · เอกสารแนบ · คำนวณเงินชดเชย · ประวัติการชดเชย · ผลการพิจารณา ไม่มีที่มา
# (SQL อ่าน 6 ตารางอยู่แล้วแต่ response ไม่ประกาศ · และยังขาดอีก 2 ตารางที่การ์ดต้องใช้)
_card_bad: list[str] = []
_DOC_CARD_KEY = {
    "ข้อมูลร้านถูกกระทบ": "impactedStore",
    "แผนที่ (POI จากระบบ AllMap)": "allmapUrl",
    "ร้านเปิดใหม่ (ที่ทำให้เกิดผลกระทบ)": "newStores",
    "ร้านคู่แข่งเปิดกระทบ": "competitors",
    "ปัจจัยอื่นๆ": "externalFactors",
    "เอกสารแนบทั้งหมด": "attachments",
    "คำนวณเงินชดเชย": "costDetails",
    "ประวัติการชดเชย": "compensationHistories",
    "ผลการพิจารณา (ประวัติ)": "considerationLogs",
    "พิจารณา (ส่งดำเนินการ)": "actionOptions",
}
_CARD_TABLE = {
    "competitors": "sgi_document_competitors",
    "externalFactors": "sgi_document_external_factors",
    "attachments": "sgi_document_attachments",
    "costDetails": "sgi_document_cost_details",
    "compensationHistories": "sgi_compensation_histories",
    "considerationLogs": "sgi_consideration_logs",
    "newStores": "sgi_document_new_stores",
}
try:
    import build_lldd_documents as _BD
    _resp: set = set()
    for _t in _BD.topics():
        for _a in (_t.apis or []):
            if getattr(_a, "path", "") == "/api/v1/sgi/document/{docNo}" and _a.method.upper() == "GET":
                _resp.update((_a.response or {}).keys())
    _doc_html = read("k2-document.html")
    _cards = [" ".join(re.sub(r"<[^>]+>", "", _m).split())
              for _m in re.findall(r'<div class="card-head"[^>]*>\s*<h2[^>]*>(.*?)</h2>', _doc_html, re.S)]
    _sql_doc = _BD.api_sql_map().get("GET /api/v1/sgi/document/{docNo}") or ""
    for _card, _key in _DOC_CARD_KEY.items():
        if _card not in _cards:
            continue
        if _key not in _resp:
            _card_bad.append(f"k2-document.html มีการ์ด '{_card}' แต่ response ของ "
                             f"GET /sgi/document/{{docNo}} ไม่มี `{_key}` — FE เรนเดอร์การ์ดนี้ไม่ได้")
        _tbl = _CARD_TABLE.get(_key)
        if _tbl and _tbl not in _sql_doc:
            _card_bad.append(f"การ์ด '{_card}' ต้องใช้ตาราง {_tbl} แต่ SQL ของ endpoint นี้ไม่ได้อ่าน")
except Exception as _e:   # pragma: no cover
    _card_bad.append(f"ตรวจการ์ดหน้าเอกสารไม่ได้: {_e}")
check("การ์ดบนหน้าเอกสารไม่มีข้อมูลจาก API รองรับ", sorted(set(_card_bad)))

# ------ #100 เอกสาร batchjob/ ต้องไม่ยืนยันว่า "สำเร็จแล้วไม่เหลือ W" (ขัดกับ legacy)
# เจอจริง 2026-09-09: JOB-02 test case 4.2 เขียนว่า "ไม่มีแถวไหนเหลือ W — ต้องเป็น N หรือ P เท่านั้น"
# แต่โค้ดเดิมเหลือ W ได้จริง เมื่อ branchtype เป็น NULL (ตรรกะสามค่า → ไม่เข้าทั้ง DENY และ PASS)
# guard นี้กันคำยืนยันผิด + บังคับให้เอกสารที่พูดถึงวงจร W ต้องมี metric remainingWCount
_bj_bad = []
_BJ_NEVER = [
    "ไม่มีแถวไหนเหลือ",
    "ไม่เหลือแถว `W`",
    "ต้องไม่เหลือ `W`",
    "ไม่มีแถว `W` เหลือ",
]
_bj_dir = "batchjob"
if os.path.isdir(_bj_dir):
    for _fn in sorted(os.listdir(_bj_dir)):
        if not _fn.endswith(".md") or _fn == "README.md":
            continue
        _p = os.path.join(_bj_dir, _fn)
        _txt = read(_p)
        for _lno, _line in enumerate(_txt.split("\n"), 1):
            for _bad in _BJ_NEVER:
                if _bad in _line:
                    _bj_bad.append(f"{_p}:{_lno} ยืนยันว่าไม่เหลือแถว W — ขัดกับ legacy (ดูข้อ 2.15)")
        # เอกสารที่อธิบายวงจร flag_verify/W ต้องมี metric + alert
        if "flag_verify" in _txt and "'W'" in _txt and "remainingWCount" not in _txt:
            _bj_bad.append(f"{_p} อธิบายวงจรสถานะ W แต่ไม่มี metric remainingWCount + alert")
check("เอกสาร batchjob ยืนยันว่าไม่เหลือแถว W (ขัดกับ legacy)", sorted(set(_bj_bad)))

# --- #101 เอกสาร batchjob: รายการ NOT NULL/DEFAULT ต้องตรงกับ DDL จริง
# เจอจริง 2026-09-09: JOB-02 เขียนว่า sales_request_status ตั้งเป็น 'W' "เฉพาะแถวที่เป็น P"
# แต่ DDL เป็น NOT NULL DEFAULT 'W' → แถว N ก็ได้ 'W' ด้วย (คนละมิติกับ verify_status)
# guard นี้ไล่ทุกคอลัมน์ที่เอกสาร batchjob อ้างว่า "มี DEFAULT" / "ต้องใส่ค่าเอง" เทียบกับ DDL
_dflt_bad = []
_ddl_cols = {}     # (table, column) -> (default_value|None, not_null)
_KW = ("PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT", "EXCLUDE")
for _blk in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", ddl, re.S):
    _tbl, _body = _blk.group(1), _blk.group(2)
    # ตัดคอมเมนต์ -- ทิ้งก่อน มิฉะนั้น comma/วงเล็บในคอมเมนต์จะทำให้ split พัง
    _body = "\n".join(re.sub(r"--.*$", "", _ln) for _ln in _body.split("\n"))
    _parts, _depth, _buf = [], 0, ""
    for _ch in _body:
        if _ch == "(":
            _depth += 1
        elif _ch == ")":
            _depth -= 1
        if _ch == "," and _depth == 0:
            _parts.append(_buf); _buf = ""
        else:
            _buf += _ch
    _parts.append(_buf)
    for _d in _parts:
        _d = _d.strip()
        _m = re.match(r"(\w+)\s+[A-Za-z]", _d)
        if not _m or _m.group(1).upper() in _KW:
            continue
        _dm = re.search(r"\bDEFAULT\s+('[^']*'|[\w()]+)", _d)
        _ddl_cols[(_tbl, _m.group(1))] = (_dm.group(1) if _dm else None, "NOT NULL" in _d)

_bj_dir = "batchjob"
if os.path.isdir(_bj_dir) and _ddl_cols:
    for _fn in sorted(os.listdir(_bj_dir)):
        if not _fn.endswith(".md") or _fn == "README.md":
            continue
        _p = os.path.join(_bj_dir, _fn)
        _txt = read(_p)
        # ก) บรรทัด "ที่เหลือมี `DEFAULT` ให้แล้ว — col='v' · col='v' …"
        for _blk2 in re.findall(r"ที่เหลือมี `DEFAULT` ให้แล้ว(.+?)\n\*\*", _txt, re.S):
            for _c, _v in re.findall(r"`(\w+)=('[^']*'|[\w.]+)`", _blk2):
                _seen = [dv for (tt, cc), (dv, nn) in _ddl_cols.items() if cc == _c]
                if not _seen:
                    _dflt_bad.append(f"{_p}: อ้างคอลัมน์ `{_c}` ที่ไม่มีใน DDL")
                elif _v not in _seen:
                    _dflt_bad.append(
                        f"{_p}: `{_c}` DEFAULT ในเอกสาร {_v} · DDL มีแต่ {sorted(set(map(str, _seen)))}")
        # ข) ตาราง "คอลัมน์ที่ NOT NULL และไม่มี DEFAULT — ต้องใส่ค่าเอง"
        _sec = re.search(r"NOT NULL` และ \*\*ไม่มี DEFAULT\*\*.+?\n\n(.+?)\n\n", _txt, re.S)
        if _sec:
            for _t, _cells in re.findall(r"^\| `(\w+)` \| (.+?) \|$", _sec.group(1), re.M):
                if "ไม่มี —" in _cells or "ไม่มี -" in _cells:
                    _claim = set()
                else:
                    _claim = set(re.findall(r"`(\w+)`", _cells))
                _real = {c for (tt, c), (dv, nn) in _ddl_cols.items()
                         if tt == _t and nn and dv is None and c != "id"}
                for _c in sorted(_claim - _real):
                    _dflt_bad.append(f"{_p}: `{_t}.{_c}` ไม่ได้เป็น NOT NULL-ไม่มี-DEFAULT ตาม DDL")
                for _c in sorted(_real - _claim):
                    _dflt_bad.append(f"{_p}: `{_t}.{_c}` เป็น NOT NULL ไม่มี DEFAULT แต่เอกสารไม่ได้ระบุ")
check("เอกสาร batchjob ระบุ NOT NULL/DEFAULT ไม่ตรงกับ DDL", sorted(set(_dflt_bad)))

# --- #102 ค่าที่เอกสารบอกว่าเซ็ตลงคอลัมน์ ต้องอยู่ในโดเมน CHECK ของ DDL
# เจอจริง 2026-09-09: LLDD Job 2 เขียน "ตั้ง sales_request_status = W / N / P" หลายจุด
# ตอนนั้น DDL คือ CHECK IN ('W','P','Y','E') — ไม่มี 'N'
# (มติ 2026-09-12 ข้อ 2.37 ขยายโดเมนเป็น W/P/Y/N/E แล้ว โดย 'N' = ได้ยอดขายแต่ยอดไม่ตก
#  ซึ่งคนละความหมายกับ verify_status = 'N' ที่แปลว่าคู่ร้านถูกตัดทิ้ง — กฎนี้ยังจำเป็นอยู่)
# ต้นทางคือ JOBS ใน job-batch.html ที่ generator อ่านไปสร้างทั้ง flowchart · ตาราง · skeleton
# ตรวจเฉพาะคอลัมน์ที่โดเมนเป็น "ตัวอักษรเดียวทุกค่า" (W/P/N …) เพื่อไม่ให้ชนกับโดเมนคำเต็ม
_dom_bad = []
_dom = {}
for _cm in re.finditer(r"(\w+)\s+(?:CHAR|VARCHAR)\(\d+\)[^,\n]*?CHECK\s*\(\s*\1\s+IN\s*\(([^)]*)\)", ddl):
    _vals = set(re.findall(r"'([^']*)'", _cm.group(2)))
    if _vals and all(len(v) == 1 for v in _vals):
        _dom.setdefault(_cm.group(1), set()).update(_vals)
# คอลัมน์ชื่อซ้ำข้ามตาราง ตรวจไม่ได้แบบไม่รู้ตาราง — ข้ามไป
_AMBIG = {c for c in _dom
          if len(re.findall(r"\b" + c + r"\s+(?:CHAR|VARCHAR)\(", ddl)) > 1}
for _p in sorted(glob.glob("LLDD/md/**/*.md", recursive=True)) + ["job-batch.html"]:
    if not os.path.exists(_p):
        continue
    for _lno, _line in enumerate(read(_p).split("\n"), 1):
        # จับ  col = X   /  col = 'X'   และค่าที่ต่อกันด้วย / · ,  เช่น "= W / N / P"
        for _m in re.finditer(
                r"\b(\w+)\s*=\s*('?[A-Z]'?(?![A-Za-z_])(?:\s*[/·,]\s*'?[A-Z]'?(?![A-Za-z_]))*)", _line):
            _c = _m.group(1)
            if _c not in _dom or _c in _AMBIG:
                continue
            for _v in re.findall(r"[A-Z]", _m.group(2)):
                if _v not in _dom[_c]:
                    _dom_bad.append(
                        f"{_p}:{_lno} `{_c} = {_v}` ไม่อยู่ในโดเมน CHECK ของ DDL "
                        f"({'/'.join(sorted(_dom[_c]))})")
check("เอกสารเซ็ตค่าที่อยู่นอกโดเมน CHECK ของ DDL", sorted(set(_dom_bad)))

# --- #103 SQL/skeleton ที่ generate ต้องไม่ขัดกับสัญญาของ job ฉบับเดียวกัน
# เจอจริง 2026-09-09 ใน LLDD Job 2 สามเรื่องพร้อมกัน:
#   (ก) DO UPDATE SET ใส่ updated_by ซ้ำสองครั้ง -> PostgreSQL error 42601
#   (ข) หัวข้อ idempotency ประกาศ "DO NOTHING / ห้ามอัปเดตทับ" แต่ SQL เป็น DO UPDATE ทับทุกคอลัมน์
#   (ค) เส้น NO ของ decision ที่เป็นผลธุรกิจปกติ (DENY) กลับ throw JobFailedError = job ล้มทั้งตัว
_gen_bad = []
for _f in sorted(glob.glob("LLDD/md/Jobs/*.md")):
    _txt = read(_f)
    # (ก) คอลัมน์ซ้ำใน DO UPDATE SET — statement เดียวกันห้ามกำหนดคอลัมน์เดิมสองครั้ง
    for _m in re.finditer(r"DO UPDATE SET (.+?);", _txt, re.S):
        _cols = re.findall(r"(?:^|,)\s*(\w+)\s*=", _m.group(1))
        _dup = {c for c in _cols if _cols.count(c) > 1}
        if _dup:
            _gen_bad.append(f"{_f} :: DO UPDATE SET กำหนดคอลัมน์ซ้ำ {sorted(_dup)} "
                            "— PostgreSQL error 42601 multiple assignments to same column")
    # (ข) สัญญา idempotency บอก DO NOTHING แต่ SQL ของตารางเดียวกันเป็น DO UPDATE
    _pledge = re.search(r"\| Idempotency / dedup \| ([^|]*)\|", _txt)
    if _pledge and "DO NOTHING" in _pledge.group(1):
        _tb = re.search(r"UNIQUE\(([^)]*)\)", _pledge.group(1))
        _key = _tb.group(1).replace(" ", "") if _tb else None
        for _m in re.finditer(r"ON CONFLICT \(([^)]*)\)[^;]*?DO UPDATE", _txt, re.S):
            if _key and _m.group(1).replace(" ", "").split("--")[0].strip(", ") == _key:
                _gen_bad.append(f"{_f} :: ประกาศ idempotency เป็น DO NOTHING "
                                f"แต่ SQL ของคีย์เดียวกันใช้ DO UPDATE — จะทับข้อมูลที่ downstream/ผู้ใช้แก้ไว้")
    # (ค) เส้น NO ที่ข้อความบอกว่าเป็นการ "บันทึกสถานะ/คงสถานะ" แต่ skeleton throw
    for _m in re.finditer(r"if \(!ok(\d+)\) throw new JobFailedError\([^)]*?'([^']*)'\)", _txt):
        _msg = _m.group(2)
        if re.search(r"(verify_status|_status)\s*=\s*[A-Z]|คงสถานะ|คงค่า|บันทึก reject|ไม่ rollback", _msg):
            _gen_bad.append(f"{_f} :: ขั้นที่ {_m.group(1)} เส้น NO เป็นผลทางธุรกิจ ('{_msg}') "
                            "แต่ skeleton throw JobFailedError — ใช้ noKind:'mark' แทน")
check("SQL/skeleton ที่ generate ขัดกับสัญญาในฉบับเดียวกัน", sorted(set(_gen_bad)))

# --- #104 skeleton ต้องสอดคล้องกับหัวข้ออื่นในเอกสาร Job ฉบับเดียวกัน
# เจอจริง 2026-09-09 ใน LLDD Job 2 สี่เรื่อง:
#   (ก) ชื่อ job ที่ลงทะเบียนใน main.ts ไม่ตรงกับชื่อ canonical ในหัวข้อ 5.95
#   (ข) config class ประกาศ property ซ้ำ (cron สองครั้ง) -> TypeScript คอมไพล์ไม่ผ่าน
#   (ค) config มี argument = 'ALL|2569|06' ทั้งที่สัญญา input เป็น JSON ผ่าน INPUT
#   (ง) `continue` อยู่ใน callback ของ dataSource.transaction() -> ใช้ไม่ได้ (คนละ function)
_sk_bad = []
for _f in sorted(glob.glob("LLDD/md/Jobs/*.md")):
    _txt = read(_f)
    # (ก) ชื่อ job
    _canon = re.search(r"ลงทะเบียนเป็น job ชื่อ \*\*`([\w-]+)`\*\*", _txt)
    if _canon:
        for _m in re.finditer(r"case '([\w-]+)'", _txt):
            if _m.group(1).startswith("sgi-") and _m.group(1) != _canon.group(1):
                _sk_bad.append(f"{_f} :: skeleton ลงทะเบียน '{_m.group(1)}' "
                               f"แต่ชื่อ canonical คือ '{_canon.group(1)}'")
    # (ข) property ซ้ำใน config class/interface
    for _blk in re.finditer(r"export (?:interface|class) \w+[^{]*\{(.*?)\n\}", _txt, re.S):
        # เอาเฉพาะบรรทัดที่เป็น property จริง (`name: Type;` / `name = value;`)
        # ไม่นับ modifier (private/readonly/async/static) และไม่นับ method (`name(...)`)
        _props = [c for c in re.findall(r"^\s{2}(\w+)\s*[?:=][^(=]", _blk.group(1), re.M)
                  if c not in {"private", "public", "protected", "readonly",
                               "async", "static", "constructor", "get", "set"}]
        _dup = {c for c in _props if _props.count(c) > 1}
        if _dup:
            _sk_bad.append(f"{_f} :: config ประกาศ property ซ้ำ {sorted(_dup)} — TypeScript คอมไพล์ไม่ผ่าน")
    # (ค) argument แบบ legacy ใน config ทั้งที่สัญญา input เป็น JSON
    if "INPUT" in _txt and re.search(r"argument\s*=\s*process\.env", _txt):
        _sk_bad.append(f"{_f} :: config อ่าน argument จาก env แบบสตริง legacy "
                       "ทั้งที่สัญญา input เป็น JSON ผ่าน INPUT")
    # (ง) continue ภายใน callback ของ transaction
    for _m in re.finditer(r"dataSource\.transaction\(async[^\n]*\n(.*?)\n\s{6}\}\);", _txt, re.S):
        if re.search(r"^\s+continue;", _m.group(1), re.M):
            _sk_bad.append(f"{_f} :: มี `continue` อยู่ใน callback ของ dataSource.transaction() "
                           "— ใช้ไม่ได้เพราะเป็นคนละ function (ต้อง return เพื่อ commit แล้วให้ลูปข้างนอกไปต่อ)")
check("skeleton ขัดกับหัวข้ออื่นในเอกสาร Job ฉบับเดียวกัน", sorted(set(_sk_bad)))

# --- #105 ON CONFLICT ต้องอ้างคอลัมน์ที่มีจริงใน DDL ของตารางนั้น
# เจอจริง 2026-09-12: LLDD Job 7 เขียน ON CONFLICT (doc_no, competitor_code)
# แต่ DDL เปลี่ยนเป็น competitor_store_code ไปแล้ว -> SQL prepare ไม่ผ่าน
_oc_bad = []
_oc_cols = {}
for _blk in re.finditer(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", ddl, re.S):
    _t = _blk.group(1)
    _body = "\n".join(re.sub(r"--.*$", "", _ln) for _ln in _blk.group(2).split("\n"))
    # หนึ่งบรรทัดประกาศได้หลายคอลัมน์ (คั่นด้วย comma) — ต้อง split ที่ depth 0
    _parts, _depth, _buf = [], 0, ""
    for _ch in _body:
        if _ch == "(":
            _depth += 1
        elif _ch == ")":
            _depth -= 1
        if _ch == "," and _depth == 0:
            _parts.append(_buf); _buf = ""
        else:
            _buf += _ch
    _parts.append(_buf)
    _oc_cols[_t] = {_cm.group(1) for _cm in
                    (re.match(r"\s*(\w+)\s+[A-Za-z]", _p) for _p in _parts)
                    if _cm and _cm.group(1).upper() not in
                    ("PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT", "EXCLUDE")}
for _f in sorted(glob.glob("LLDD/md/**/*.md", recursive=True)) + ["plan-api.html"]:
    if not os.path.exists(_f):
        continue
    _txt = read(_f)
    # จับคู่ INSERT INTO <table> ... ON CONFLICT (<cols>) ที่อยู่ใน statement เดียวกัน
    for _m in re.finditer(r"INSERT INTO\s+(\w+)(.{0,2000}?)ON CONFLICT\s*\(([^)]*)\)", _txt, re.S):
        _t, _cols = _m.group(1), _m.group(3)
        if _t not in _oc_cols or "/*" in _cols:
            continue
        for _c in re.findall(r"\b([a-z][a-z_0-9]*)\b", _cols):
            if _c not in _oc_cols[_t]:
                _oc_bad.append(f"{_f} :: ON CONFLICT ของ {_t} อ้าง `{_c}` ที่ไม่มีใน DDL")
check("ON CONFLICT อ้างคอลัมน์ที่ไม่มีใน DDL", sorted(set(_oc_bad)))

# --- #106 ค่า canonical ของ enum ที่เขียนเป็น literal ต้องใช้ค่าเดียวทั้งระบบ
# เจอจริง 2026-09-12: source_system ใช้ทั้ง 'ALM' และ 'ALLMAP' — prune จะไม่ตรงกลุ่ม
_enum_bad = []
_CANON = {
    # ฟิลด์ -> (ค่าที่เลือกแล้ว, ค่าที่ห้ามใช้ซ้ำ)
    "source_system": ("ALLMAP", {"ALM"}),
}
_enum_files = (sorted(glob.glob("LLDD/md/**/*.md", recursive=True))
               + sorted(glob.glob("batchjob/JOB-*.md"))
               + ["job-batch.html", "plan-api.html", "database.md"])
for _f in _enum_files:
    if not os.path.exists(_f):
        continue
    for _lno, _line in enumerate(read(_f).split("\n"), 1):
        if "canonical" in _line or "migrate" in _line or "เลือกค่า" in _line:
            continue        # บรรทัดที่อธิบายการเลือกค่าเอง
        for _fld, (_ok, _bad_vals) in _CANON.items():
            for _bv in _bad_vals:
                if re.search(_fld + r"\s*=\s*'?" + _bv + r"'?(?![A-Z])", _line):
                    _enum_bad.append(
                        f"{_f}:{_lno} `{_fld} = {_bv}` — ค่า canonical คือ '{_ok}' ค่าเดียว")
check("ค่า canonical ของ enum ถูกเขียนหลายค่า", sorted(set(_enum_bad)))

# --- #107 job ที่ประกาศ dependency กัน ต้องไม่ใช้ cron เดียวกัน
# เจอจริง 2026-09-12: Job 2 กับ Job 3 เป็น `0 07 7 * *` ทั้งคู่ ทั้งที่ Job 3 ต้องรอ parent จาก Job 2
# และ Jobs 7/8/9 เป็น `30 17 7-31 * *` ทั้งสามตัว ทั้งที่ 7 กับ 9 ต้องรอ doc_no จาก Job 8
# cron เดียวกัน = ไม่มีอะไรรับประกันลำดับ (race ทุกรอบ)
_dep_bad = []
try:
    import build_lldd_documents as _BD
    _cron = {str(_j["no"]): str(_j.get("cron", "")).strip()
             for _j in _BD.read_js_array_from_html("job-batch.html", "JOBS")}
    for _job, _ups in _BD.JOB_DEPENDENCIES.items():
        _c = _cron.get(_job, "")
        # นับเฉพาะ cron ที่เป็นตารางเวลาจริง — 'event-driven' / 'after-job-8' ไม่ใช่
        if not re.match(r"^[\d*/, -]+$", _c):
            continue
        for _u in _ups:
            if _cron.get(_u, "") == _c:
                _dep_bad.append(
                    f"Job {_job} ขึ้นกับ Job {_u} แต่ cron เท่ากัน (`{_c}`) — "
                    f"ลำดับไม่ถูกบังคับ ต้องตั้ง dependency ที่ scheduler หรือเหลื่อมเวลา")
except Exception as _e:   # pragma: no cover
    _dep_bad.append(f"ตรวจ cron/dependency ไม่ได้: {_e}")
check("job ที่ขึ้นต่อกัน แต่ใช้ cron เดียวกัน", sorted(set(_dep_bad)))

# --- #108 generator ต้อง deterministic — ห้ามหยิบ "ตัวแรก" จาก set
# เจอจริง 2026-09-12: lldd_skeleton_be.py ใช้ next(iter(body_props)) ที่ body_props เป็น set
# ทำให้ build ติดกันสองครั้งได้ `body.impactMonth` กับ `body.roundNo` สลับกัน
# → เอกสารที่ commit ไว้กับที่ generate ใหม่ diff กันทั้งที่ source ไม่เปลี่ยน
# ตรวจด้วย AST แยกตาม scope (ชื่อซ้ำข้ามฟังก์ชันไม่นับ) — ไม่ใช้การเดาจากชื่อตัวแปร
_ndet_bad: list[str] = []


def _ndet_scan(path: str) -> None:
    import ast
    try:
        tree = ast.parse(read(path))
    except SyntaxError as exc:
        _ndet_bad.append(f"{path}: parse ไม่ผ่าน ({exc})")
        return

    def _is_set_expr(node) -> bool:
        """นิพจน์นี้ให้ set (ลำดับไม่คงที่) หรือไม่"""
        if isinstance(node, (ast.Set, ast.SetComp)):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "set":
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.Sub)):
            return _is_set_expr(node.left) or _is_set_expr(node.right)
        return False

    def _root_name(node):
        while isinstance(node, (ast.Subscript, ast.Attribute)):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    def _sorted_wrapped(node) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in {"sorted", "len", "sum", "min", "max", "any", "all"}

    _NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
    # ฟังก์ชันที่ "ยุบ" ลำดับทิ้ง — วนบน set แล้วส่งให้ตัวเหล่านี้ ผลคงที่เสมอ
    _SAFE_REDUCERS = {"set", "frozenset", "dict", "sum", "len", "any", "all",
                      "min", "max", "sorted", "Counter"}

    def _own_nodes(scope):
        """ทุก node ที่เป็นของ scope นี้เอง — ไม่ลงไปในฟังก์ชัน/คลาสที่ซ้อนอยู่
        (ถ้าลงไปด้วย ชื่อตัวแปรของ scope ข้างในจะถูกนับปนกับข้างนอก → false positive)"""
        # กรองตั้งแต่ชั้นแรก — ถ้าปล่อย FunctionDef ชั้นบนเข้า stack ลูกของมันจะถูก push ต่อ
        # แล้วตัวแปรในฟังก์ชันจะไหลมาปนกับ scope แม่ (bug ที่ทำให้ _dedupe โผล่เป็น <module>)
        out, stack = [], [n for n in scope.body if not isinstance(n, _NESTED)]
        while stack:
            node = stack.pop()
            out.append(node)
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, _NESTED):
                    stack.append(child)
        return out

    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        # ชื่อที่ถูก assign เป็น set ภายใน scope นี้เท่านั้น
        setnames: set[str] = set()
        own = _own_nodes(scope)
        for node in own:
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                value = getattr(node, "value", None)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if value is not None and _is_set_expr(value):
                    for tgt in targets:
                        if isinstance(tgt, ast.Name):
                            setnames.add(tgt.id)
        parent = {}
        for node in own:
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, _NESTED):
                    parent[child] = node
        for node in own:
            bad_name = why = None
            at = node
            forced = False   # True = ฟ้องโดยไม่ต้องรู้ว่าเป็น set (ค่าที่มาจาก dict.get()/พารามิเตอร์)
            # (1) next(iter(X)) — หยิบ "ตัวแรก" จาก collection ที่ลำดับไม่การันตี  ← bug ที่เจอจริง
            #     bug จริงเขียนว่า next(iter(dto.get("body_props", []))) — ชื่อ set ไม่โผล่ใน scope เลย
            #     จึงต้องฟ้องที่ "รูปแบบ" ไม่ใช่ที่ชื่อตัวแปร · ถ้าลำดับไม่สำคัญให้เขียน sorted(...)[0]
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "next" \
                    and node.args and isinstance(node.args[0], ast.Call) \
                    and isinstance(node.args[0].func, ast.Name) and node.args[0].func.id == "iter" \
                    and node.args[0].args:
                _inner = node.args[0].args[0]
                if not _sorted_wrapped(_inner) and not isinstance(_inner, (ast.List, ast.Tuple)):
                    bad_name, why, forced = (_root_name(_inner) or "<expr>"), "next(iter(...))", True
            # (2) list(X)[n] / tuple(X)[n] — index เข้าไปในลำดับที่ไม่คงที่
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id in {"list", "tuple"} and node.value.args:
                _inner = node.value.args[0]
                if not _sorted_wrapped(_inner) and not isinstance(_inner, (ast.List, ast.Tuple)):
                    bad_name, why, forced = (_root_name(_inner) or "<expr>"), \
                        f"{node.value.func.id}(...)[...]", True
            # (3) X.pop() บน set — คืนสมาชิกแบบสุ่มลำดับ
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "pop" and not node.args:
                bad_name, why = _root_name(node.func.value), ".pop()"
            # (4) for ... in X: ที่ "สร้างผลลัพธ์แบบเรียงลำดับ" (append/extend/insert/+=/yield)
            elif isinstance(node, (ast.For, ast.AsyncFor)) and not _sorted_wrapped(node.iter):
                _emits = any(
                    (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr in {"append", "extend", "insert", "add_run", "write"})
                    or isinstance(n, (ast.AugAssign, ast.Yield, ast.YieldFrom))
                    for st in node.body for n in ast.walk(st))
                if _emits:
                    bad_name, why = _root_name(node.iter), "วนลูปสร้างผลลัพธ์เรียงลำดับ"
            # (5) list/generator comprehension บน set ที่ผลลัพธ์ยังคงลำดับไว้
            #     (ถ้าเป็น set/dict comprehension หรือถูกยุบด้วย sum/len/min/... ทันที → ลำดับไม่มีผล)
            elif isinstance(node, ast.comprehension) and not _sorted_wrapped(node.iter):
                comp = parent.get(node)
                if isinstance(comp, (ast.ListComp, ast.GeneratorExp)):
                    consumer = parent.get(comp)
                    safe = isinstance(consumer, ast.Call) and isinstance(consumer.func, ast.Name) \
                        and consumer.func.id in _SAFE_REDUCERS
                    if not safe:
                        bad_name, why, at = _root_name(node.iter), "comprehension เก็บลำดับ", node.iter
            if bad_name and (forced or bad_name in setnames):
                fn = getattr(scope, "name", "<module>")
                _ndet_bad.append(
                    f"{path}:{getattr(at, 'lineno', '?')} · {fn}() · {why} บน set `{bad_name}` — "
                    "ผลไม่คงที่ระหว่าง build · ใช้ sorted() ครอบก่อน")


for _f in ("tools/lldd_skeleton_be.py", "tools/lldd_skeleton_job.py",
           "tools/build_lldd_documents.py", "tools/lldd_db_dictionary.py",
           "tools/build_sgi_schema_sql.py"):
    if os.path.exists(_f):
        _ndet_scan(_f)
check("generator ไม่ deterministic (หยิบลำดับจาก set โดยไม่เรียงก่อน)", sorted(set(_ndet_bad)))

# --- #109 CREATE INDEX ต้องอ้างคอลัมน์ที่มีจริงใน DDL
# เจอจริง 2026-09-12 ตอนรัน output/sql/sgi_schema.sql กับ PostgreSQL 16 จริงครั้งแรก:
#   CREATE INDEX idx_impact_competitor_code ON sgi_fgi_impact_competitors(competitor_code);
#   -> ERROR: column "competitor_code" does not exist
# คอลัมน์ถูกแยกเป็น competitor_store_code + brand_code ตอนแก้ identity ของคู่แข่ง (2026-09-09)
# แต่ index ไม่ได้ตามไปด้วย · กฎ #105 ดักเฉพาะ ON CONFLICT จึงมองไม่เห็นจุดนี้
# ทั้งไฟล์อยู่ใน transaction เดียว = พังข้อเดียวคือติดตั้งไม่ได้ทั้งชุด
_idx_bad = []
# _ddl_cols เป็น dict[(table, column)] -> (default, not_null) ที่กฎ #101/#102 สร้างไว้แล้ว
_cols_by_table: dict[str, set[str]] = {}
for (_t, _c) in _ddl_cols:
    _cols_by_table.setdefault(_t, set()).add(_c)
for _m in re.finditer(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+([\w.]+)\s*\(([^)]*)\)", ddl):
    _name, _tbl, _cols = _m.group(1), _m.group(2).split(".")[-1], _m.group(3)
    _known = _cols_by_table.get(_tbl)
    if not _known:
        continue   # ตารางของระบบเดิม — ไม่มี DDL ให้เทียบ
    for _col in _cols.split(","):
        # ตัด DESC/ASC/NULLS FIRST/opclass และนิพจน์ (index บนนิพจน์ไม่ตรวจชื่อคอลัมน์)
        _c = _col.strip().split()[0].strip() if _col.strip() else ""
        if not _c or "(" in _col or not re.fullmatch(r"\w+", _c):
            continue
        if _c.lower() not in {k.lower() for k in _known}:
            _idx_bad.append(
                f"{_name}: อ้าง {_tbl}.{_c} ที่ไม่มีใน DDL "
                f"(คอลัมน์จริง: {', '.join(sorted(_known))[:120]}...)")
check("CREATE INDEX อ้างคอลัมน์ที่ไม่มีใน DDL", sorted(set(_idx_bad)))

# --- #110 โดเมนจริงจากฐาน Oracle เดิม ต้องไม่ขัดกับ CHECK ที่ DDL ใหม่ประกาศ
# ใช้ผลจาก tools/introspect_legacy_oracle.py (output/legacy-oracle/data.json)
# ข้ามไปเงียบ ๆ ถ้ายังไม่เคยรัน — ไม่บังคับให้ทุกคนต้องต่อ VPN ถึงจะ check เอกสารได้
# จุดประสงค์: ค่าที่มีอยู่จริงในระบบเดิมแต่ไม่อยู่ในโดเมนของ DDL ใหม่ = migration ล้มแน่นอน
_legacy_path = "output/legacy-oracle/data.json"
_legacy_bad = []
if os.path.exists(_legacy_path):
    _legacy = json.loads(read(_legacy_path))
    _src = str(_legacy.get("source", ""))
    # ค่าที่เอกสาร migration ประกาศการแมปไว้แล้ว — key = ชื่อคอลัมน์ต้นทาง (FLAG_VERIFY ฯลฯ)
    _mig = read("LLDD/md/BE/LLDD-BE-Data-Migration-Cutover.md")
    _mig_section = _mig.split("### 5.2.1")[1].split("### 5.2.2")[0] if "### 5.2.1" in _mig else ""
    _declared_map: dict[str, set[str]] = {}
    for _dm in re.finditer(r"`[A-Z_]*\.?(\w+)`\s*=\s*`([^`]+)`", _mig_section):
        for _val in re.split(r"\s*/\s*", _dm.group(2)):
            _declared_map.setdefault(_dm.group(1), set()).add(_val.strip())
    if not _declared_map:
        _legacy_bad.append("LLDD-BE-Data-Migration-Cutover ข้อ 5.2.1 ไม่มีตารางแมปค่า — กฎนี้ตรวจอะไรไม่ได้")


    # โดเมนที่ DDL ของเอกสารประกาศไว้:  col CHAR(n) ... CHECK (col IN ('a','b'))
    _doc_domains: dict[str, set[str]] = {}
    for _m in re.finditer(r"(\w+)\s+(?:CHAR|VARCHAR)\(\d+\)[^,\n]*?CHECK\s*\(\s*\1\s+IN\s*\(([^)]*)\)", ddl):
        _doc_domains[_m.group(1)] = {v.strip().strip("'") for v in _m.group(2).split(",") if v.strip()}

    # ค่า "ปลายทาง" ที่ตารางแมปสัญญาไว้ ต้องอยู่ในโดเมนของคอลัมน์ปลายทางจริง
    # ไม่งั้นถ้ามีใครหด CHECK ให้แคบลง กฎนี้จะเงียบเพราะค่าต้นทางถูก "ประกาศแมปไว้แล้ว"
    # (เจอจริง 2026-09-12: ถอด 'P' ออกจาก sales_status แล้วกฎไม่ฟ้อง)
    _mig_lines = [ln for ln in _mig_section.split("\n") if ln.startswith("|")]
    for _ln in _mig_lines:
        for _tm2 in re.finditer(r"`(?:sgi_\w+\.)?(\w+)\s*=\s*'([^']+)'`", _ln):
            _col, _val = _tm2.group(1), _tm2.group(2)
            _dom2 = _doc_domains.get(_col)
            if _dom2 and _val not in _dom2:
                _legacy_bad.append(
                    f"ตารางแมป 5.2.1 สัญญาว่าแมปเป็น {_col} = '{_val}' "
                    f"แต่โดเมนจริงของ DDL คือ {sorted(_dom2)} — สองที่นี้ขัดกันเอง")

    for _key, _info in (_legacy.get("data", {}).get("domains") or {}).items():
        _note = str(_info.get("note", ""))
        _tm = re.search(r"(sgi_\w+)\.(\w+)\s+CHECK", _note)
        if not _tm:
            continue                       # โดเมนที่ไม่ได้ผูกกับ CHECK ของ DDL ใหม่ (เช่น datasource)
        _target_col = _tm.group(2)
        _allowed = _doc_domains.get(_target_col)
        if not _allowed:
            continue
        _seen = {v for v in (_info.get("values") or {}) if v != "<NULL>"}
        # ค่าที่ประกาศการแมปไว้แล้วในตาราง 5.2.1 ของ LLDD-BE-Data-Migration-Cutover ไม่นับว่าพัง
        # (จุดประสงค์ของกฎนี้คือกัน "ค่าที่ไม่มีใครรู้ว่าจะทำยังไง" ไม่ใช่บังคับให้โดเมนตรงกันเป๊ะ)
        _outside = sorted(_seen - _allowed - _declared_map.get(_key.split(".")[-1], set()))
        if _outside:
            _legacy_bad.append(
                f"{_key}: ฐานเดิมมีค่า {_outside} ที่ไม่อยู่ในโดเมนของ "
                f"{_tm.group(1)}.{_target_col} ({sorted(_allowed)}) — migration จะล้ม "
                f"[ที่มา {_src}]")
check("โดเมนจริงในฐานเดิม ขัดกับ CHECK ของ DDL ใหม่", sorted(set(_legacy_bad)))

# --- #111 ชื่อสถานะเอกสารต้องตรงกันระหว่าง common_code (SGI) กับ workflow_status (engine)
# รหัส 2 ตัวอักษร 06/08/01/02/03/99 เป็นของ SGI · engine ถือแค่ status_id (integer) + status_name
# ชื่อไทยจึงถูกเขียนไว้ 2 ที่: seed common_code (SGI_DOC_STATUS) และเอกสาร Workflow-Engine-Definition
# ถ้าสองที่นี้หลุดจากกัน หน้าจอกับ inbox กลางจะแสดงคนละชื่อสำหรับสถานะเดียวกัน
_st_bad = []
try:
    import importlib
    _bs = importlib.import_module("build_sgi_schema_sql")
    _seed_names = [n for _c, n in getattr(_bs, "SGI_DOC_STATUSES", [])]
except Exception as _e:      # pragma: no cover
    _seed_names = []
    _st_bad.append(f"อ่าน SGI_DOC_STATUSES จาก build_sgi_schema_sql ไม่ได้: {_e}")
if _seed_names:
    _wf = read("LLDD/md/BE/LLDD-BE-Workflow-Engine-Definition.md")
    _row = [ln for ln in _wf.split("\n") if "workflow_status (sps_store)" in ln]
    if not _row:
        _st_bad.append("LLDD-BE-Workflow-Engine-Definition ไม่มีแถว workflow_status (sps_store)")
    else:
        for _n in _seed_names:
            if _n not in _row[0]:
                _st_bad.append(
                    f"ชื่อสถานะ '{_n}' อยู่ใน seed common_code (SGI_DOC_STATUS) "
                    f"แต่ไม่มีในแถว workflow_status ของ LLDD-BE-Workflow-Engine-Definition")
check("ชื่อสถานะเอกสารไม่ตรงกันระหว่าง common_code กับ workflow_status ของ engine", sorted(set(_st_bad)))

# --- #112 ตาราง FGI_* ที่มีข้อมูลจริง ต้องปรากฏในแผน migration
# เจอจริง 2026-09-13: FGI_IMPACT_STORE_INFO (429) · FGI_NEW_STORE_INFO (492) ·
#   FGI_NEW_STORE_COMPENSATE (473) · FGI_WS_LOG (20,704) มีข้อมูลจริงแต่ไม่อยู่ในตาราง
#   Source-to-Target ข้อ 5.1 เลย — รวม 22,098 แถวที่ไม่มีใครระบุว่าจะทำอย่างไร
# ใช้ row_counts จาก output/legacy-oracle/data.json (ข้ามไปถ้ายังไม่เคยรัน extractor)
_mig_bad = []
if os.path.exists(_legacy_path):
    _lg = json.loads(read(_legacy_path))
    _counts = (_lg.get("data") or {}).get("row_counts") or {}
    _mig_doc = read("LLDD/md/BE/LLDD-BE-Data-Migration-Cutover.md").upper()
    for _t, _n in sorted(_counts.items()):
        if not _t.startswith("FGI_") or "_BK_" in _t or not _n:
            continue          # ตาราง backup ไม่ต้อง migrate
        if _t not in _mig_doc:
            _mig_bad.append(
                f"{_t}: มี {_n:,} แถวในฐานเดิม แต่ไม่ปรากฏใน LLDD-BE-Data-Migration-Cutover เลย "
                "— ต้องระบุปลายทาง หรือระบุชัดว่า **ไม่ migrate** พร้อมเหตุผล")
check("ตาราง FGI_* ที่มีข้อมูลจริง แต่ไม่มีในแผน migration", sorted(set(_mig_bad)))

# ------------------------------------------------------------------- LLDDv2
# LLDDv2 เป็น Markdown ที่เขียนใหม่แบบ feature-centric จึงตรวจแยกจากกฎของ generator
# ชุดเดิมด้านบน (ไม่เอาไฟล์ใหม่ไปปนกับ regex ของ SQL/skeleton เดิม)
_v2_root = "llddv2"
_v2_required = [
    "PLAN-LLDDV2.md", "README.md",
    *[f"00-foundation/{i:02}-{name}.md" for i, name in enumerate([
        "system-overview", "glossary-and-business-rules", "api-security-and-error-contract",
        "database-and-migration", "workflow-engine", "integrations-and-operations",
        "decision-register",
    ], 1)],
    *[f"features/{i:02}-{name}.md" for i, name in enumerate([
        "worklist-and-document-search", "document-creation-pipeline",
        "document-detail-and-editing", "workflow-actions-and-timeline",
        "attachments-and-sales-data", "master-data", "status-report-and-export",
        "interface-tracking",
    ], 1)],
    "jobs/00-job-pipeline-overview.md",
    "jobs/JOB-02-ImportImpactStore.md", "jobs/JOB-03-ImportImpactCompetitor.md",
    "jobs/JOB-04-PrepareImpactStoreToIAS.md", "jobs/JOB-05-ImportImpactSaleFromIAS.md",
    "jobs/JOB-06-ExportImpactStoreToSTA.md", "jobs/JOB-07-SyncCompetitorToDocument.md",
    "jobs/JOB-08-CreateCompensationDocument.md", "jobs/JOB-08b-StartInternalWorkflow.md",
    "jobs/JOB-09-SyncNewStoreToDocument.md", "jobs/JOB-10-NotifyNoReceiveData.md",
    "jobs/JOB-11-ConsumeStaCompensate.md", "jobs/JOB-12-NotifyPendingWork.md",
    "references/API-CATALOG.md", "references/DATABASE-DICTIONARY.md",
    "references/CONFIG-AND-ENV-CATALOG.md", "references/ERROR-CATALOG.md",
    "references/TEST-AND-DELIVERY.md", "templates/FEATURE-TEMPLATE.md",
    "templates/JOB-TEMPLATE.md",
]
check("LLDDv2 มีไฟล์บังคับครบ", [
    p for p in _v2_required if not os.path.isfile(os.path.join(_v2_root, p))
])

_v2_files = sorted(glob.glob("llddv2/**/*.md", recursive=True))
_v2_features = sorted(glob.glob("llddv2/features/[0-9][0-9]-*.md"))
_v2_jobs = sorted(glob.glob("llddv2/jobs/JOB-*.md"))
check(f"LLDDv2 feature = {LLDDV2_FEATURES}", [] if len(_v2_features) == LLDDV2_FEATURES else [
    f"พบ {len(_v2_features)} ฉบับ: {', '.join(_v2_features)}"
])
check(f"LLDDv2 job = {LLDDV2_JOBS} (Jobs 2–12 + 8b)", [] if len(_v2_jobs) == LLDDV2_JOBS else [
    f"พบ {len(_v2_jobs)} ฉบับ: {', '.join(_v2_jobs)}"
])

# หัวข้อมาตรฐานต้องมีครบและเรียง 1..17 / 1..18 เพื่อให้ reviewer หา contract เดิมได้ทุกฉบับ
_heading_bad = []
for _f, _last in [(f, 17) for f in _v2_features] + [(f, 18) for f in _v2_jobs]:
    _nums = [int(n) for n in re.findall(r"^##\s+(\d+)\.", read(_f), re.M)]
    if _nums != list(range(1, _last + 1)):
        _heading_bad.append(f"{_f}: หัวข้อเลข {_nums} ต้องเป็น 1..{_last}")
check("LLDDv2 feature/job ใช้หัวข้อมาตรฐานครบและเรียงถูก", _heading_bad)

# ทุก feature/job ต้องมี flowchart และ sequence จริงอย่างน้อยอย่างละหนึ่ง block
# Static parser นี้ตรวจ fence/declaration/edge ขั้นต่ำ; สามารถเสริม mmdc ใน CI ได้โดยไม่เปลี่ยน contract
_mermaid_bad = []
for _f in _v2_features + _v2_jobs:
    _txt = read(_f)
    _blocks = re.findall(r"```mermaid\s*\n(.*?)```", _txt, re.S)
    _kinds = [b.strip().splitlines()[0].strip() if b.strip() else "" for b in _blocks]
    if not any(k.startswith(("flowchart ", "graph ")) for k in _kinds):
        _mermaid_bad.append(f"{_f}: ไม่มี Mermaid Flowchart")
    if "sequenceDiagram" not in _kinds:
        _mermaid_bad.append(f"{_f}: ไม่มี Mermaid Sequence Diagram")
    for _idx, _b in enumerate(_blocks, 1):
        _first = _b.strip().splitlines()[0].strip() if _b.strip() else ""
        if not _first.startswith(("flowchart ", "graph ", "sequenceDiagram", "stateDiagram")):
            _mermaid_bad.append(f"{_f}: Mermaid block {_idx} ไม่ขึ้นต้นด้วยชนิด diagram ที่รองรับ")
        if _first == "sequenceDiagram" and ("participant " not in _b or "->>" not in _b):
            _mermaid_bad.append(f"{_f}: Sequence block {_idx} ไม่มี participant/arrow")
        if _first.startswith(("flowchart ", "graph ")) and "-->" not in _b:
            _mermaid_bad.append(f"{_f}: Flowchart block {_idx} ไม่มี edge")
check("LLDDv2 Mermaid flowchart/sequence มีโครงสร้าง parseable ขั้นต่ำ", _mermaid_bad)

_v2_table_bad = []
def _v2_cell_count(row: str) -> int:
    row = row.replace("\\|", "")
    row = re.sub(r"`[^`]*`", "", row)
    return row.count("|")

for _f in _v2_files:
    _lines = read(_f).splitlines()
    for _i, _line in enumerate(_lines[:-1]):
        if not _line.startswith("|") or not re.match(r"^\|[\s:| -]+\|$", _lines[_i + 1]):
            continue
        _want = _v2_cell_count(_line)
        for _j in range(_i + 2, len(_lines)):
            if not _lines[_j].startswith("|"):
                break
            _got = _v2_cell_count(_lines[_j])
            if _got != _want:
                _v2_table_bad.append(f"{_f}:{_j + 1} ({_got} ช่อง ≠ หัวตาราง {_want})")
check("LLDDv2 ตาราง Markdown มีจำนวนช่องตรงหัวตาราง", _v2_table_bad)

check("LLDDv2 เอกสารหลักไม่เกิน 500 บรรทัด", [
    f"{_f}: {len(read(_f).splitlines())} บรรทัด" for _f in _v2_files
    if not "/references/" in _f and len(read(_f).splitlines()) > 500
])

# ลิงก์ Markdown ภายในต้องเปิดไฟล์ได้จริง; anchor และ URL ภายนอกไม่ใช่ target filesystem
_link_bad = []
for _f in _v2_files:
    _txt = read(_f)
    for _m in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", _txt):
        _target = _m.group(1).strip()
        if not _target or _target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        _path = _target.split("#", 1)[0].split("?", 1)[0]
        if _path.startswith("<") and _path.endswith(">"):
            _path = _path[1:-1]
        _resolved = os.path.normpath(os.path.join(os.path.dirname(_f), _path))
        if not os.path.exists(_resolved):
            _line = _txt[:_m.start()].count("\n") + 1
            _link_bad.append(f"{_f}:{_line} -> {_target}")
check("LLDDv2 Markdown links ชี้ไฟล์ที่มีจริง", _link_bad)

# Catalog API ต้องตรง plan-api.html แบบ method/path ทุกตัว ไม่ใช่แค่จำนวนเท่ากัน
_api_catalog_path = "llddv2/references/API-CATALOG.md"
_v2_eps = []
if os.path.exists(_api_catalog_path):
    for _line in read(_api_catalog_path).splitlines():
        _m = re.match(r"^\|\s*\d+\s*\|\s*`(GET|POST|PUT|PATCH|DELETE)\s+([^`]+)`\s*\|", _line)
        if _m:
            _v2_eps.append((_m.group(1), _m.group(2)))
_api_trace_bad = []
if len(_v2_eps) != CANON_ENDPOINTS:
    _api_trace_bad.append(f"API Catalog มี {len(_v2_eps)} เส้น ต้องมี {CANON_ENDPOINTS}")
if set(_v2_eps) != set(_eps):
    for _x in sorted(set(_eps) - set(_v2_eps)):
        _api_trace_bad.append(f"Catalog ขาด {_x[0]} {_x[1]}")
    for _x in sorted(set(_v2_eps) - set(_eps)):
        _api_trace_bad.append(f"Catalog เกิน {_x[0]} {_x[1]}")
for _line in read(_api_catalog_path).splitlines() if os.path.exists(_api_catalog_path) else []:
    if re.match(r"^\|\s*\d+\s*\|", _line):
        _cells = [c.strip() for c in _line.strip().strip("|").split("|")]
        if len(_cells) < 6 or any(not c for c in _cells[2:6]):
            _api_trace_bad.append(f"traceability ไม่ครบ: {_line[:160]}")
check("LLDDv2 API Catalog = 28 และตรง plan-api พร้อม traceability", _api_trace_bad)

# Database Dictionary ต้องมี owner/reader/writer และชื่อตรง DDL 20 + reuse 1
_db_catalog_path = "llddv2/references/DATABASE-DICTIONARY.md"
_v2_tables = []
_db_trace_bad = []
for _line in read(_db_catalog_path).splitlines() if os.path.exists(_db_catalog_path) else []:
    _m = re.match(r"^\|\s*\d+\s*\|\s*`([a-z_0-9]+)`\s*\|", _line)
    if not _m:
        continue
    _v2_tables.append(_m.group(1))
    _cells = [c.strip() for c in _line.strip().strip("|").split("|")]
    if len(_cells) < 6 or any(not c for c in (_cells[2], _cells[4], _cells[5])):
        _db_trace_bad.append(f"owner/reader/writer ไม่ครบ: {_line[:160]}")
_canon_v2_tables = created | {"fcs_qssi_score"}
if len(_v2_tables) != CANON_TABLES:
    _db_trace_bad.append(f"Database Dictionary มี {len(_v2_tables)} ตาราง ต้องมี {CANON_TABLES}")
if set(_v2_tables) != _canon_v2_tables:
    _db_trace_bad.extend(f"Dictionary ขาด {_x}" for _x in sorted(_canon_v2_tables - set(_v2_tables)))
    _db_trace_bad.extend(f"Dictionary เกิน {_x}" for _x in sorted(set(_v2_tables) - _canon_v2_tables))
check("LLDDv2 Database Dictionary = 20 new + 1 reuse พร้อม owner/read/write", _db_trace_bad)

_db_col_bad = []
_v2_cols_by_table: dict[str, set[str]] = {}
for _line in read(_db_catalog_path).splitlines() if os.path.exists(_db_catalog_path) else []:
    _m = re.match(r"^\|\s*`(sgi_[a-z_0-9]+|fcs_qssi_score)`\s*\|\s*(.*?)\s*\|$", _line)
    if _m:
        _v2_cols_by_table[_m.group(1)] = set(re.findall(r"`([a-z_0-9]+)`", _m.group(2)))
for _table in sorted(_canon_v2_tables):
    _expected_cols = schema.get(_table, set()) if _table == "fcs_qssi_score" else all_cols.get(_table, set())
    _documented_cols = _v2_cols_by_table.get(_table)
    if _documented_cols is None:
        _db_col_bad.append(f"{_table}: ไม่มีแถว canonical columns")
        continue
    for _col in sorted(_expected_cols - _documented_cols):
        _db_col_bad.append(f"{_table}: dictionary ขาดคอลัมน์ {_col}")
    for _col in sorted(_documented_cols - _expected_cols):
        _db_col_bad.append(f"{_table}: dictionary มีคอลัมน์ที่ไม่มีใน schema {_col}")
check("LLDDv2 canonical columns ตรง DDL/schema จริงครบทุกตาราง", _db_col_bad)

# ห้ามประกาศ Ready ขณะที่เอกสารยังมี BLOCKED; ตรวจเฉพาะ status metadata ช่วงต้นไฟล์
_ready_bad = []
for _f in _v2_files:
    _txt = read(_f)
    _head = "\n".join(_txt.splitlines()[:8])
    if re.search(r"(?:Document status|สถานะเอกสาร):\s*`?Ready`?", _head, re.I) \
            and re.search(r"\bBLOCKED\b", _txt, re.I):
        _ready_bad.append(f"{_f}: status Ready แต่ยังมี BLOCKED")
check("LLDDv2 ไม่มีเอกสาร Ready ที่ยังมี BLOCKED", _ready_bad)

# Code path ของ Job ที่ประกาศ AS-BUILT ต้องเปิดพบจริง
_job_service_expected = {
    "02": "job-2-import-impact-store.service.ts",
    "03": "job-3-import-impact-competitor.service.ts",
    "04": "job-4-prepare-impact-store-to-ias.service.ts",
    "05": "job-5-import-impact-sale-from-ias.service.ts",
    "06": "job-6-export-impact-store-to-sta.service.ts",
    "07": "job-7-sync-competitor-to-document.service.ts",
    "08": "job-8-create-compensation-document.service.ts",
    "08b": "job-8b-start-internal-workflow.service.ts",
    "09": "job-9-sync-new-store-to-document.service.ts",
    "10": "job-10-notify-no-receive-data.service.ts",
    "11": "job-11-consume-sta-compensate.service.ts",
    "12": "job-12-notify-pending-work.service.ts",
}
_code_path_bad = []
for _no, _service in _job_service_expected.items():
    _source = os.path.join("SBP/srm-sps-spsap-sop-sgi-batch/src/modules/sgi", _service)
    _doc_matches = glob.glob(f"llddv2/jobs/JOB-{_no}-*.md")
    if not os.path.isfile(_source):
        _code_path_bad.append(f"Job {_no}: ไม่พบ source {_source}")
    if len(_doc_matches) != 1 or (len(_doc_matches) == 1 and _service not in read(_doc_matches[0])):
        _code_path_bad.append(f"Job {_no}: เอกสารไม่อ้าง service จริง {_service}")
check("LLDDv2 Job code path เปิดพบและอ้างตรง service ปัจจุบัน", _code_path_bad)

# ------------------------------------------------------------------- รายงานผล
print(f"schema sps_store: {len(schema)} ตาราง · ตรวจ {len(DOC_FILES)} ไฟล์\n")
print(f"{'ตรวจ':<52}{'ผิด':>5}")
print("─" * 74)
total = 0
for name, bad in results:
    total += len(bad)
    print(f"  {name:<50}{len(bad):>4}  {'✅' if not bad else '❌'}")
    for x in bad[:10]:
        print(f"       • {x}")
    if len(bad) > 10:
        print(f"       … อีก {len(bad)-10} รายการ")
print("─" * 74)
print("  สรุป: ผ่านทุกข้อ ✅" if not total else f"  พบปัญหา {total} จุด ❌")
sys.exit(1 if total else 0)
