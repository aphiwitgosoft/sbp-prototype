#!/usr/bin/env python3
"""ชุดตรวจความถูกต้องของเอกสาร SBPGI — รันก่อนส่งมอบทุกครั้ง

    python3 tools/check_docs.py

ตรวจ 2 ฝั่ง:
  A. ฝั่ง SBPGI เอง  — จำนวนตาราง · FK · ลิงก์ · ตาราง markdown · จำนวนเอกสาร
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
CANON_DOCS = 40           # 37 topic + LLDD-API + LLDD-Database + LLDD-To-Be (ตัด Job 1 ImportQSSI 2026-08-24)
CANON_ENDPOINTS = 29       # 6 กลุ่ม (เอกสาร 11 · Lookup 2 · Master 8 · รายงาน 2 · Workflow 3 · Interface 3)            # 38 topic + LLDD-API + LLDD-Database
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

# ---------------------------------------------------------------- A. ฝั่ง SBPGI
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
    # แบบ A (ชัดเจน): VERB `path` เขียนติดกัน — ใช้ได้ทุกคอลัมน์ เช่น "GET `/factors` · POST `/factors`"
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
    "workflow_tasks": "ตาราง workflow ของ SBPGI (ตัด 2026-08-06)",
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
    c_tot = sum(int(r["ชั่วโมงรวม"]) for r in rows)
    c_impl = sum(int(r["implementation"]) for r in rows)
    c_ut = sum(int(r["unit test"]) for r in rows)
    if (c_tot, c_impl, c_ut) != (GRAND, IMPL, UT):
        hour_bad.append(f"CSV รวม {c_tot}/{c_impl}/{c_ut} != README {GRAND}/{IMPL}/{UT}")
    if f"<b>{GRAND}</b>" not in read("LLDD/index.html"):
        hour_bad.append(f"portal LLDD/index.html ไม่ได้แสดง {GRAND} ชั่วโมง")
    _tobe = read("LLDD/md/LLDD-To-Be.md")
    _tm = re.search(r"\*\*รวมทั้งชุดส่งมอบ\*\*[^|]*\|[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*", _tobe)
    if not _tm:
        hour_bad.append("LLDD-To-Be อ่านแถวรวมทั้งชุดส่งมอบไม่ได้")
    elif int(_tm.group(3)) != GRAND or int(_tm.group(1)) + int(_tm.group(2)) != GRAND:
        hour_bad.append(f"LLDD-To-Be รวม {_tm.group(3)} (FE {_tm.group(1)} + BE {_tm.group(2)}) != {GRAND}")
    _mi = read("LLDD/md/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.md")
    # นับเฉพาะหัวข้อ 4 (ภาระงานต่อคน) — หัวข้อ 3 ใช้รูปแบบเดียวกันแต่เป็นรายเอกสาร
    _s4 = _mi[_mi.index("## 4. Workload Balance"): _mi.index("## 5. ")]
    owner_tot = sum(int(x) for x in re.findall(r"\*\*(\d+)\*\* \(impl \d+ \+ test \d+\)", _s4))
    if owner_tot != GRAND:
        hour_bad.append(f"main index ผลรวมต่อคน {owner_tot} != {GRAND}")
check("ชั่วโมงไม่ตรงกันระหว่างไฟล์ (README/CSV/portal/main index/To-Be)", hour_bad)

# ชั่วโมง unit test กับหัวข้อ Unit Test Scope ต้องมาคู่กันเสมอ (ห้ามคิดเงินแต่ไม่บอกว่าเทสอะไร)
ut_bad = []
for f in glob.glob("LLDD/md/FE/*.md") + glob.glob("LLDD/md/BE/*.md") + glob.glob("LLDD/md/BE/Jobs/*.md"):
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
repo_bad = [f for f in glob.glob("LLDD/md/FE/*.md") + glob.glob("LLDD/md/BE/*.md") + glob.glob("LLDD/md/BE/Jobs/*.md")
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
