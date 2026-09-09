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

import io
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CANON_TABLES = 20          # 19 CREATE + fcs_qssi_score ที่ reuse ของเดิม (รับ F8+F1 เข้าโครง 2026-08-21)
CANON_DOCS = 42           # 39 topic + LLDD-API + LLDD-Database + LLDD-To-Be (นับจาก .md เท่านั้น)
#   LLDD-Database-Dictionary **ไม่นับ** เพราะส่งมอบเป็น PDF อย่างเดียว (มติผู้ใช้ 2026-09-09)
#   ไม่มีชั่วโมง/เจ้าของ จึงไม่กระทบยอด 829 ชม.
#   (ตัด Job 1 ImportQSSI 2026-08-24 · เพิ่ม Job 11 ConsumeStaCompensate + Job 12 NotifyPendingWork 2026-09-02)
CANON_ENDPOINTS = 28       # 6 กลุ่ม (เอกสาร 11 · Lookup 2 · Master 8 · รายงาน 2 · Workflow 3 · Interface 2)
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
SQL_ALIAS_OK = {
    "dual", "unnest", "generate_series", "values", "json_to_recordset",
    "pg_locks",                                    # ตรวจ advisory lock กันรันซ้อน
    "allmap_seven_impact_view",                    # allmapssa.SEVEN_IMPACT_VIEW (SQL Server GSMALLMAP) — Job 2
    "allmap_competitor_impact_view",               # view คู่แข่งของ ALLMAP — Job 3
}
ghost = []
for f in glob.glob("LLDD/md/**/*.md", recursive=True):
    full = read(f)
    s_ = sql_blocks(full)
    # ชื่อ CTE ที่ประกาศในไฟล์เดียวกัน (WITH x AS (...) , y AS (...)) ไม่ใช่ตาราง
    ctes = set(re.findall(r"(?:WITH|,)\s+([a-z][a-z_0-9]*)\s+AS\s*\(", s_, re.I))
    ctes |= set(re.findall(r"RETURNING[^;]*?\)\s*(?:,)?\s*([a-z][a-z_0-9]*)\s+AS\s*\(", s_, re.I))
    for m in re.finditer(r"\b(?:FROM|JOIN|INSERT INTO|UPDATE)\s+(?:sps_store\.)?([a-z][a-z_0-9]*)", s_):
        t = m.group(1)
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
                    (("srm-sps-spsap-store-consumer",), "repo ตัวรับ EAI/RabbitMQ (มติ 2026-09-08)")):
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
# เจอจริง 2026-09-08: Job 11 ประกาศ trigger = "ข้อความจาก store-consumer (1 ข้อความ = 1 การรัน)"
# แต่ฟิลด์ cron ยังเป็น "*/10 * * * *" (drain-then-exit ของดีไซน์เก่า) แล้วเลขนั้นไหลไป LLDD + SRS
_cron_bad = []
try:
    import build_lldd_documents as _BC
    for _j in _BC.read_js_array_from_html("job-batch.html", "JOBS"):
        _trig = " ".join(str(_p) for _row in _j.get("params", []) for _p in _row)
        _consumer_driven = "store-consumer" in _trig or "1 ข้อความ = 1 การรัน" in _trig
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
_ACKW = ("ACK ค้าง", "watchdog ACK", "pending ACK", "ACK watchdog",
         "ยังไม่มี ACK", "ยังไม่ได้ ACK", "STA ACK callback")
# บรรทัดที่กำลัง "ปฏิเสธ" สำนวนนั้นอยู่ ถือว่าถูก
_ACKW_OK = ("ไม่ใช่การรอ ACK", "ไม่ใช่ ACK", "ไม่มี ACK", "ห้ามตีความว่ารอ ACK",
            "ถูกตัด", "2026-09-08", "ตัดเมื่อ", "compatibility")
for _f in DOC_FILES + glob.glob(".claude/skills/**/*.md", recursive=True):
    if not os.path.exists(_f):
        continue
    for _i, _line in enumerate(read(_f).split("\n"), 1):
        if any(_k in _line for _k in _ACKW_OK):
            continue
        for _w in _ACKW:
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
