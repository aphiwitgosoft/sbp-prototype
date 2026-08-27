#!/usr/bin/env python3
"""สร้าง worklist.html — หน้าจัดการงานสไตล์ Notion จากข้อมูลชุดเดียวกับ LLDD

    python3 tools/build_worklist.py

เชื่อม 3 ชั้นเข้าด้วยกัน คลิกข้ามกันได้:
    งาน (37 หัวข้อจาก LLDD 40 ฉบับ)  ->  API ที่งานนั้นเรียก  ->  ตาราง DB ที่ API นั้นแตะ
พร้อมตาราง "กำลังคนเทียบกรอบเวลา" ที่คำนวณจากกติกาเวลาเดียวกับ LLDD (HOURS_PER_DAY / เป้า 4 สัปดาห์)

ข้อมูลทั้งหมด derive จากแหล่งเดียวกับเอกสารส่งมอบ จึงไม่มีทางหลุดจากกัน:
  * งาน/ชั่วโมง/owner/scope/flow/acceptance/unit test -> tools/build_lldd_documents.py
  * SQL ต่อ endpoint                                   -> plan-api.html (SQL_BY_PATH)
  * DDL ของตาราง                                       -> LLDD/md/LLDD-Database.md
ไฟล์ผลลัพธ์ self-contained (ไม่มี CDN/ไฟล์แนบ) เปิดออฟไลน์ได้
"""
from __future__ import annotations

import html
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "tools"))

import build_lldd_documents as B  # noqa: E402


# --------------------------------------------------------------------------- data
def slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()


def parse_ddl() -> dict[str, dict]:
    """ดึงคอลัมน์ของแต่ละตารางจาก Executable DDL"""
    text = (ROOT / "LLDD/md/LLDD-Database.md").read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\((.*?)\n\);", text, re.S):
        name, body = m.group(1), m.group(2)
        # ตัดคอมเมนต์ทีละบรรทัดก่อนเสมอ — คอมเมนต์มีทั้ง comma และวงเล็บ
        # ถ้าไม่ตัดก่อน ตัวแยกคอลัมน์จะนับ depth ผิดแล้วคอลัมน์หายไปเงียบ ๆ
        notes: dict[str, str] = {}
        clean_lines = []
        for line in body.split("\n"):
            code_part, _, note = line.partition("--")
            clean_lines.append(code_part)
            cm0 = re.match(r"\s*([a-z_0-9]+)\s", code_part)
            if note.strip() and cm0:
                notes[cm0.group(1)] = note.strip()
        body = "\n".join(clean_lines)
        cols, constraints = [], []
        depth, cur = 0, ""
        for ch in body:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                cols.append(cur); cur = ""
            else:
                cur += ch
        cols.append(cur)
        parsed = []
        for raw in cols:
            d = " ".join(raw.split())
            if not d:
                continue
            if d.upper().startswith(("CONSTRAINT", "UNIQUE", "PRIMARY", "FOREIGN", "CHECK")):
                constraints.append(d)
                continue
            cm = re.match(r"([a-z_0-9]+)\s+(.*)$", d)
            if not cm:
                continue
            parsed.append({
                "name": cm.group(1),
                "type": cm.group(2),
                "note": notes.get(cm.group(1), ""),
                "pk": "PRIMARY KEY" in cm.group(2).upper(),
                "fk": (re.search(r"REFERENCES\s+([a-z_0-9]+)", cm.group(2), re.I).group(1)
                       if re.search(r"REFERENCES\s+([a-z_0-9]+)", cm.group(2), re.I) else None),
                "required": "NOT NULL" in cm.group(2).upper(),
            })
        out[name] = {"name": name, "columns": parsed, "constraints": constraints}
    return out


def parse_sql_by_path() -> dict[str, str]:
    """ดึง SQL ตัวอย่างต่อ endpoint จาก plan-api.html (ข้ามส่วนที่อยู่ใน /* */)"""
    text = (ROOT / "plan-api.html").read_text(encoding="utf-8")
    start = text.index("SQL_BY_PATH")
    body = text[start: text.index("\n  };", start)]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    out: dict[str, str] = {}
    for m in re.finditer(r"'((?:GET|POST|PUT|PATCH|DELETE) [^']+)':\s*\n?\s*'((?:[^'\\]|\\.)*)'", body):
        sql = m.group(2)
        sql = sql.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
        out[m.group(1)] = sql
    return out


def parse_existing_schema() -> dict[str, dict]:
    """คอลัมน์ของตารางระบบ SBP เดิมจาก dump จริง — ใช้ทำหน้าให้คลิกดูได้เหมือนตารางของเรา"""
    out: dict[str, dict] = {}
    cur = None
    for line in io.open(ROOT / "SBP/db-schema-sps_store.md", encoding="utf-8"):
        m = re.match(r"^### ([a-z_0-9]+)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = {"name": cur, "columns": [], "constraints": [], "existing": True}
            continue
        if cur:
            m = re.match(r"^\|\s*\d+\s*\|\s*`([a-z_0-9]+)`\s*(🔑)?\s*\|\s*([^|]+)\|\s*([YN])\s*\|([^|]*)\|", line)
            if m:
                out[cur]["columns"].append({
                    "name": m.group(1), "type": m.group(3).strip(),
                    "note": ("default: " + m.group(5).strip()) if m.group(5).strip() else "",
                    "pk": bool(m.group(2)), "fk": None, "required": m.group(4) == "N",
                })
    return out


# ชื่อที่หลุดมาจากการตัดคำในคอลัมน์ "ตาราง/Object" ของเอกสาร ไม่ใช่ชื่อตาราง
NOT_TABLE = {"mssql", "ora", "auth-backend", "backend", "application", "config", "และ", "หรือ"}


def clean_table_name(raw: str) -> str | None:
    n = str(raw).replace("sps_store.", "").split("/")[0].split("(")[0].strip()
    n = re.split(r"[ ,]", n)[0].strip("`")
    if not n or n.lower() in NOT_TABLE or n.isdigit() or not re.fullmatch(r"[a-z_][a-z_0-9]*", n):
        return None
    return n


def canonical_endpoints() -> set[str]:
    """29 เส้นที่ยังใช้งานจริงใน plan-api.html (ตัด /* */ ที่เป็นเส้นยกเลิกออก)"""
    text = re.sub(r"/\*.*?\*/", "", (ROOT / "plan-api.html").read_text(encoding="utf-8"), flags=re.S)
    return {f"{m.group(1)} {m.group(2)}"
            for m in re.finditer(r"m:\s*'(GET|POST|PUT|PATCH|DELETE)'[^}]*?p:\s*'([^']+)'", text)}


def api_kind(key: str, canon: set[str]) -> str:
    """own = 29 เส้นของ SBPGI · external = API ของระบบ SBP เดิม · contract = pseudo (/*) ในเอกสารสัญญากลาง"""
    if "/*" in key:
        return "contract"
    if key in canon:
        return "own"
    return "external"


TABLE_RE = re.compile(r"\b(?:FROM|JOIN|INSERT INTO|UPDATE|REFERENCES)\s+(?:sps_store\.)?([a-z_][a-z_0-9]*)", re.I)


def build_model() -> dict:
    topics = B.topics()
    canon = canonical_endpoints()
    existing = parse_existing_schema()
    ddl = parse_ddl()
    sqls = parse_sql_by_path()
    preds = B.document_dependencies(topics)
    billable = [t for t in topics if not B.is_document_detail_role_doc(t.file)]
    # ลำดับขั้นต้องคิดจาก topic "ทั้งหมด" (รวม role pack 5 ฉบับที่ชั่วโมงรวมอยู่ในเอกสารแม่)
    # ไม่งั้น FE-Testing-Delivery จะได้ step 5 ขณะที่ build_planner_tasks.py ได้ 6 — ต้องตรงกัน
    steps = B.dependency_steps(topics)
    # ตารางเวลาแบบรู้จัก dependency + คิวของเจ้าของงาน (ชั่วโมงรวม impl + unit test)
    sched = B.build_topic_schedule(billable)
    base = min(s for s, _ in sched.values()) if sched else None

    tasks, apis, tables = {}, {}, {}
    for name, info in ddl.items():
        tables[name] = {**info, "usedByApi": [], "usedByTask": []}

    for t in topics:
        tid = slug(t.file)
        ut = B.unit_test_hours(t)
        task = {
            "id": tid,
            "file": t.file,
            "title": t.title.replace("LLDD ", ""),
            "track": "Job" if "/Jobs/" in t.file else t.track,
            "owner": t.owner,
            "ownerShort": t.owner.split("<")[1].split(">")[0] if "<" in t.owner else t.owner,
            "hours": t.hours,
            "unitTest": ut,
            "total": t.hours + ut,
            "repo": B.target_repo_row(t)[1],
            "objective": t.objective,
            "scope": list(t.scope),
            "fields": [list(f) for f in t.fields],
            "actions": [list(a) for a in t.actions],
            "flow": list(t.flow),
            "acceptance": list(t.acceptance),
            "tests": list(t.tests),
            "dbTables": [list(d) for d in t.db_tables],
            # หัวข้อ Workflow Trigger Event Contract ของ LLDD — แหล่งเดียวกับ build_lldd_documents.py
            "triggerEvent": [list(r) for r in B.WORKFLOW_TRIGGER_CONTRACTS.get(t.file.rsplit("/", 1)[-1], [])],
            "apis": [f"{a.method} {a.path}" for a in t.apis],
            "deps": sorted(slug(d) for d in preds.get(t.file, set())),
            "step": steps.get(t.file),
            "startDay": (sched[t.file][0] - base).days if t.file in sched else None,
            "endDay": (sched[t.file][1] - base).days if t.file in sched else None,
            "included": B.is_document_detail_role_doc(t.file),
            "unitTestCases": unit_test_cases(t),
        }
        tasks[tid] = task
        for spec in t.apis:
            key = f"{spec.method} {spec.path}"
            entry = apis.setdefault(key, {
                "id": slug(key), "method": spec.method, "path": spec.path,
                "purpose": spec.purpose, "request": spec.request, "response": spec.response,
                "sql": sqls.get(key, ""), "tasks": [], "tables": [],
                "kind": api_kind(key, canon),
            })
            if tid not in entry["tasks"]:
                entry["tasks"].append(tid)
        for row in t.db_tables:
            tname = clean_table_name(row[0])
            if not tname:
                continue
            if tname not in tables and tname in existing:
                tables[tname] = {**existing[tname], "usedByApi": [], "usedByTask": []}
            if tname in tables and tid not in tables[tname]["usedByTask"]:
                tables[tname]["usedByTask"].append(tid)

    for key, api in apis.items():
        found = []
        for m in TABLE_RE.finditer(api["sql"] or ""):
            n = m.group(1)
            if n not in tables and n in existing:
                tables[n] = {**existing[n], "usedByApi": [], "usedByTask": []}
            if n in tables and n not in found:
                found.append(n)
        api["tables"] = found
        for n in found:
            if api["id"] not in tables[n]["usedByApi"]:
                tables[n]["usedByApi"].append(api["id"])

    # กติกาเวลา + ภาระงานต่อคน — ดึงจาก build_lldd_documents ตัวเดียวกับที่ LLDD ใช้ ไม่ hardcode
    weeks = 4
    ceiling = weeks * B.HOURS_PER_WEEK
    load: dict[str, int] = {}
    for t in billable:
        load[t.owner] = load.get(t.owner, 0) + B.total_hours(t)
    owners = [
        {
            "name": o,
            "short": o.split("<")[1].split(">")[0] if "<" in o else o,
            "hours": h,
            "days": round(h / B.HOURS_PER_DAY, 1),
            "weeks": round(h / B.HOURS_PER_WEEK, 2),
            "over": max(0, h - ceiling),
        }
        for o, h in sorted(load.items(), key=lambda x: -x[1])
    ]
    meta = {
        "hoursPerDay": B.HOURS_PER_DAY,
        "daysPerWeek": B.WORKDAYS_PER_WEEK,
        "hoursPerWeek": B.HOURS_PER_WEEK,
        "targetWeeks": weeks,
        "ceiling": ceiling,
        "teamCapacity": ceiling * len(owners),
        "totalHours": sum(load.values()),
        "owners": owners,
    }
    return {"tasks": tasks, "apis": apis, "tables": tables, "meta": meta}


def unit_test_cases(topic) -> list[list[str]]:
    blocks = B.unit_test_scope_blocks(topic, 99)
    for b in blocks:
        if b.get("type") == "table":
            return [[str(c) for c in row] for row in b["rows"]]
    return []


# --------------------------------------------------------------------------- render
CSS = """
*{box-sizing:border-box}
:root{
  --bg:#ffffff; --sidebar:#fbfbfa; --ink:#37352f; --muted:#787774; --line:#e9e9e7;
  --hover:#f1f1ef; --sel:#e8f0fe; --accent:#2383e2; --code:#eb5757; --codebg:#f7f6f3;
  --fe:#0f7b6c; --febg:#ddedea; --be:#0b6e99; --bebg:#ddebf1; --job:#9065b0; --jobbg:#eae4f2;
  --get:#0f7b6c; --post:#0b6e99; --put:#d9730d; --del:#e03e3e;
}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#191919; --sidebar:#202020; --ink:#e6e6e4; --muted:#9b9a97; --line:#2f2f2f;
  --hover:#2a2a2a; --sel:#28405c; --codebg:#2b2b2b; --febg:#16332e; --bebg:#132b38; --jobbg:#2a2136;
}}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);
  font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans Thai","Sarabun",Inter,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{display:flex;min-height:100vh}
/* sidebar */
.side{width:290px;flex:0 0 290px;background:var(--sidebar);border-right:1px solid var(--line);
  height:100vh;position:sticky;top:0;overflow-y:auto;padding:14px 8px 40px}
.brand{display:flex;align-items:center;gap:9px;padding:6px 10px 12px;font-weight:700;font-size:15px}
.back{display:block;margin:0 10px 12px;padding:6px 10px;border-radius:6px;font-size:12.8px;
  color:var(--muted);border:1px solid var(--line)}
.back:hover{background:var(--hover);color:var(--ink);border-color:var(--accent)}
.brand .dot{width:22px;height:22px;border-radius:6px;background:linear-gradient(135deg,#2383e2,#0f7b6c);
  display:grid;place-items:center;color:#fff;font-size:12px}
.search{width:100%;padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);
  color:var(--ink);font-size:13.5px;margin:0 0 12px}
.search:focus{outline:2px solid var(--accent);outline-offset:-1px}
.grp{margin:14px 0 4px;padding:0 10px;font-size:11.5px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);display:flex;justify-content:space-between}
.nav a{display:flex;gap:8px;align-items:baseline;padding:5px 10px;border-radius:6px;font-size:13.7px;
  color:var(--ink);cursor:pointer;line-height:1.4}
.nav a:hover{background:var(--hover)}
.nav a.on{background:var(--sel);font-weight:600}
.nav a .h{margin-left:auto;color:var(--muted);font-size:11.5px;flex:0 0 auto}
.nav a .ic{flex:0 0 auto;opacity:.75}
/* main */
main{flex:1;min-width:0;padding:38px 56px 120px;max-width:1080px}
h1{font-size:33px;line-height:1.25;margin:0 0 6px;font-weight:700;letter-spacing:-.4px}
h2{font-size:19px;margin:34px 0 10px;font-weight:600;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:15.5px;margin:22px 0 8px;font-weight:600}
p{margin:8px 0}
.sub{color:var(--muted);font-size:14px;margin:0 0 18px}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 22px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:20px;
  font-size:12.5px;background:var(--hover);color:var(--ink);white-space:nowrap}
.chip b{font-weight:600}
.tag{padding:2px 9px;border-radius:5px;font-size:11.5px;font-weight:600}
.tag.FE{background:var(--febg);color:var(--fe)} .tag.BE{background:var(--bebg);color:var(--be)}
.tag.Job{background:var(--jobbg);color:var(--job)}
.m{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;font-weight:700;
  padding:2px 7px;border-radius:4px;color:#fff}
.m.GET{background:var(--get)} .m.POST{background:var(--post)}
.m.PUT{background:var(--put)} .m.DELETE{background:var(--del)} .m.PATCH{background:var(--put)}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
p code,td code,li code{background:var(--codebg);color:var(--code);padding:1px 5px;border-radius:4px;font-size:.88em}
pre{background:var(--codebg);border:1px solid var(--line);border-radius:8px;padding:14px 16px;
  overflow-x:auto;font-size:12.6px;line-height:1.6;margin:10px 0}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.6px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:7px 11px;text-align:left;vertical-align:top}
th{background:var(--hover);font-weight:600;font-size:12.6px;white-space:nowrap}
ul,ol{margin:8px 0;padding-left:22px} li{margin:4px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:11px;margin:14px 0}
.card{border:1px solid var(--line);border-radius:9px;padding:13px 15px;cursor:pointer;background:var(--bg)}
.card:hover{background:var(--hover);border-color:var(--accent)}
.card .t{font-weight:600;font-size:14.2px;margin:6px 0 4px}
.card .d{color:var(--muted);font-size:12.6px;line-height:1.5}
.pill{display:inline-block;padding:2px 8px;border-radius:5px;background:var(--hover);
  font-size:12.2px;margin:2px 4px 2px 0;cursor:pointer;border:1px solid var(--line)}
.pill:hover{border-color:var(--accent);background:var(--sel)}
.crumb{font-size:12.8px;color:var(--muted);margin:0 0 14px}
.crumb a{cursor:pointer} .crumb a:hover{color:var(--accent);text-decoration:underline}
.note{border-left:3px solid var(--accent);background:var(--hover);padding:10px 14px;border-radius:0 7px 7px 0;margin:12px 0;font-size:13.6px}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:11px;margin:18px 0 6px}
.kpi div{border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.kpi b{display:block;font-size:25px;font-weight:700;letter-spacing:-.5px}
.kpi small{color:var(--muted);font-size:12.2px}
.empty{color:var(--muted);font-style:italic;font-size:13.5px}
/* ---- Kanban (ClickUp style) ---- */
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 18px}
.bar select,.bar button{padding:6px 11px;border:1px solid var(--line);border-radius:7px;background:var(--bg);
  color:var(--ink);font-size:13px;font-family:inherit;cursor:pointer}
.bar button:hover,.bar select:hover{border-color:var(--accent)}
.board{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(268px,1fr);gap:12px;
  overflow-x:auto;padding-bottom:18px;align-items:start}
.col{background:var(--sidebar);border:1px solid var(--line);border-radius:11px;padding:10px;min-height:140px}
.col.over{border-color:var(--accent);background:var(--sel)}
.col h4{margin:2px 4px 10px;font-size:13px;font-weight:600;display:flex;align-items:center;gap:7px}
.col h4 .n{margin-left:auto;font-weight:500;color:var(--muted);font-size:11.8px}
.col h4 .sw{width:9px;height:9px;border-radius:50%;flex:0 0 auto}
.kc{background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:10px 11px;margin-bottom:8px;
  cursor:grab;font-size:13px;line-height:1.45}
.kc:hover{border-color:var(--accent)}
.kc.drag{opacity:.45}
.kc .kt{font-weight:600;margin:5px 0 6px;font-size:13.4px}
.kc .km{color:var(--muted);font-size:11.8px;display:flex;flex-wrap:wrap;gap:8px}
.kc .lock{color:var(--put)}
.kc a.open{color:var(--accent);font-size:11.8px}
.legend{color:var(--muted);font-size:12.5px;margin:6px 0 0}
/* ---- Work Plan (งาน x สัปดาห์) ---- */
.plan{overflow-x:auto;border:1px solid var(--line);border-radius:11px;margin:14px 0}
.plan table{margin:0;border-collapse:separate;border-spacing:0;display:table;min-width:100%}
.plan th,.plan td{border:0;border-bottom:1px solid var(--line);padding:0;font-size:12.8px}
.plan thead th{background:var(--hover);position:sticky;top:0;z-index:3;padding:8px 6px;
  text-align:center;font-size:11.8px;font-weight:600;white-space:nowrap}
.plan .tname{position:sticky;left:0;z-index:2;background:var(--bg);min-width:270px;max-width:270px;
  padding:8px 12px;border-right:1px solid var(--line)}
.plan thead .tname{z-index:4;background:var(--hover)}
.plan tbody tr:hover .tname{background:var(--hover)}
.plan .tname a{font-weight:600;font-size:13px;display:block;line-height:1.35}
.plan .tname .sm{color:var(--muted);font-size:11.5px;margin-top:2px;display:flex;gap:8px;flex-wrap:wrap}
.plan .wk{min-width:60px;text-align:center;vertical-align:middle;padding:5px 3px}
.plan .wk.wknd{background:var(--hover)}
.bar2{height:19px;border-radius:5px;display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:10.5px;font-weight:600;letter-spacing:.02em}
.bar2.FE{background:#0f7b6c}.bar2.BE{background:#0b6e99}.bar2.Job{background:#9065b0}
.plan .grp td{background:var(--hover);font-weight:600;font-size:12.4px;padding:6px 12px;
  position:sticky;left:0}
.milestone{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 0;font-size:12.6px;color:var(--muted)}
@media (max-width:900px){.wrap{flex-direction:column}.side{width:100%;height:auto;position:static;flex:none}main{padding:24px 18px 80px}}
"""

JS = r"""
const $ = (s,r=document)=>r.querySelector(s);
const esc = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const md = s => esc(s)
  .replace(/`([^`]+)`/g,'<code>$1</code>')
  .replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
const T = DATA.tasks, A = DATA.apis, D = DATA.tables, M = DATA.meta;
const apiId = k => A[k] ? A[k].id : null;
const byId = (obj,id) => Object.values(obj).find(x=>x.id===id);

/* ตารางกำลังคน — ตัวเลขทั้งหมดมาจาก DATA.meta ซึ่ง derive จาก build_lldd_documents (HOURS_PER_DAY ฯลฯ)
   จึงเปลี่ยนตามกติกาเวลาใน LLDD โดยอัตโนมัติ ไม่ต้องแก้หน้านี้ */
function capacityCard(){
  const over=M.owners.filter(o=>o.over>0);
  const rows=M.owners.map(o=>{
    const pct=Math.min(100, Math.round(o.hours/M.ceiling*100)), bad=o.over>0;
    return `<tr><td><b>${esc(o.short)}</b></td>`+
      `<td style="text-align:right">${o.hours}</td><td style="text-align:right">${o.days}</td><td style="text-align:right">${o.weeks}</td>`+
      `<td style="min-width:170px"><div style="background:var(--bd);border-radius:4px;height:9px;overflow:hidden">`+
      `<div style="width:${bad?100:pct}%;height:100%;background:${bad?'#e03e3e':'#0f7b6c'}"></div></div></td>`+
      `<td>${bad?`<b style="color:#e03e3e">เกิน ${o.over} ชม.</b>`:`เหลือ ${M.ceiling-o.hours} ชม.`}</td></tr>`;
  }).join('');
  const warn = over.length
    ? `<div class="note" style="border-left:3px solid #e03e3e">⚠️ <b>แผนยังไม่ลงตัว</b> — `+
      over.map(o=>`<b>${esc(o.short)}</b> ${o.hours} ชม. (${o.weeks} สัปดาห์) เกินเพดาน ${o.over} ชม.`).join(' · ')+
      ` · ดูทางเลือกในข้อ 1.0 ของ <code>DECISIONS-รอตัดสินใจ.md</code></div>`
    : `<div class="note" style="border-left:3px solid #0f7b6c">✅ ทุกคนอยู่ในกรอบ ${M.targetWeeks} สัปดาห์</div>`;
  return `<h2>กำลังคนเทียบกรอบเวลา</h2>
  <p class="sub">กติกาเวลาจาก LLDD: <b>${M.targetWeeks} สัปดาห์ × ${M.daysPerWeek} วัน × ${M.hoursPerDay} ชม./วัน = ${M.ceiling} ชม./คน</b> ·
  ทีม ${M.owners.length} คน = ${M.teamCapacity} ชม. เทียบงาน ${M.totalHours} ชม. (${Math.round(M.totalHours/M.teamCapacity*100)}% utilization)</p>
  ${warn}
  <table><thead><tr><th>คน</th><th style="text-align:right">ชม.</th><th style="text-align:right">วัน</th><th style="text-align:right">สัปดาห์</th><th>ภาระเทียบเพดาน</th><th>สถานะ</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function table(head, rows){
  if(!rows.length) return '<p class="empty">— ไม่มีข้อมูลในหัวข้อนี้ —</p>';
  return '<table><thead><tr>'+head.map(h=>'<th>'+esc(h)+'</th>').join('')+
    '</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+
    '</tbody></table>';
}
function list(items){ return items.length? '<ul>'+items.map(i=>'<li>'+md(i)+'</li>').join('')+'</ul>' : '<p class="empty">— ไม่มี —</p>'; }
const KIND={own:'',external:' 🔗 ระบบเดิม',contract:' 📄 สัญญากลาง'};
function apiPill(k){ const a=A[k]; if(!a) return '<span class="pill">'+esc(k)+'</span>';
  return '<a class="pill" href="#/api/'+a.id+'"><span class="m '+a.method+'">'+a.method+'</span> '+esc(a.path)+esc(KIND[a.kind]||'')+'</a>'; }
function dbPill(n){ const t=D[n]; return t? '<a class="pill" href="#/db/'+n+'">🗄 '+esc(n)+'</a>' : '<span class="pill">'+esc(n)+'</span>'; }
function taskPill(id){ const t=T[id]; return t? '<a class="pill" href="#/task/'+id+'"><span class="tag '+t.track+'">'+t.track+'</span> '+esc(t.title)+'</a>' : ''; }

function renderHome(){
  const ts=Object.values(T).filter(t=>!t.included);
  const sum=k=>ts.reduce((a,b)=>a+b[k],0);
  const grp=k=>ts.filter(t=>t.track===k);
  return `<h1>Worklist — ระบบประกันรายได้ (SBPGI)</h1>
  <p class="sub">หน้าจัดการงานที่ประกอบจากเอกสาร LLDD ชุดเดียวกับที่ส่งมอบ — คลิกงานเพื่อดูวิธีทำ คลิก API เพื่อดูสัญญาและ SQL คลิกตารางเพื่อดูโครงสร้าง</p>
  <div class="kpi">
    <div><b>${ts.length}</b><small>งานทั้งหมด</small></div>
    <div><b>${grp('FE').length}</b><small>Frontend</small></div>
    <div><b>${grp('BE').length}</b><small>Backend</small></div>
    <div><b>${grp('Job').length}</b><small>Batch Job</small></div>
    <div><b>${Object.values(A).filter(a=>a.kind==='own').length}</b><small>API ของ SBPGI</small></div>
    <div><b>${Object.values(A).filter(a=>a.kind==='external').length}</b><small>API ระบบเดิม</small></div>
    <div><b>${Object.values(D).filter(t=>!t.existing).length}</b><small>ตาราง SBPGI</small></div>
    <div><b>${Object.values(D).filter(t=>t.existing).length}</b><small>ตารางระบบเดิม</small></div>
    <div><b>${sum('total')}</b><small>ชั่วโมงรวม</small></div>
  </div>
  <div class="note" style="border-left:3px solid #2f6fed"><b>กระทบยอดกับเอกสาร LLDD:</b>
  <b>งาน ${ts.length}</b> = การ์ดงานตั้งต้น + <b>${Object.values(T).filter(t=>t.included).length}</b> role pack ที่รวมอยู่ใน FE-Document-Detail = <b>${Object.values(T).length} หัวข้อ</b> · บวกเอกสารอ้างอิง 3 ฉบับ (LLDD-API / LLDD-Database / LLDD-To-Be ที่ไม่คิดชั่วโมงแยก) = <b>LLDD 40 ฉบับ</b> ที่ส่งมอบ &nbsp;·&nbsp;
  <b>API ${Object.values(A).filter(a=>a.kind==='own').length}</b> = ครบ 29 เส้นตาม <code>api.md</code> พอดี (ที่เห็นเพิ่มคือ ${Object.values(A).filter(a=>a.kind==='external').length} เส้นของระบบเดิม และ ${Object.values(A).filter(a=>a.kind==='contract').length} รายการ pseudo <code>/*</code> จากเอกสารสัญญากลาง ซึ่งไม่นับเป็น endpoint) &nbsp;·&nbsp;
  <b>ตาราง ${Object.values(D).filter(t=>!t.existing).length}</b> = จำนวน <code>CREATE TABLE</code> ใน DDL — <code>database.md</code> นับเป็น <b>20 ตาราง</b> เพราะรวม <code>fcs_qssi_score</code> ที่ reuse ของระบบเดิมแบบอ่านอย่างเดียว (หน้านี้จัดอยู่ในกลุ่มตารางระบบเดิม)</div>
  ${capacityCard()}
  <div class="note"><b>อ่านยังไง:</b> เริ่มที่กลุ่มงานทางซ้าย → เปิดงานที่รับผิดชอบ → ในหน้างานจะมี <b>ขั้นตอนการทำงาน</b>, <b>เกณฑ์ตรวจรับ</b> และ <b>ขอบเขต unit test</b> ครบ ·
  ส่วน <b>API ที่ต้องต่อ</b> และ <b>ตารางที่แตะ</b> กดเข้าไปดูรายละเอียดต่อได้ทันที</div>
  <p style="margin:16px 0"><a class="pill" href="#/board" style="padding:8px 16px;font-size:14px">🗂 เปิด Kanban Board</a>
  <a class="pill" href="#/plan" style="padding:8px 16px;font-size:14px">📅 เปิดแผนงานรายสัปดาห์</a></p>
  <h2>งานตามสาย</h2>
  ${['FE','BE','Job'].map(k=>{
    const g=grp(k); if(!g.length) return '';
    return `<h3><span class="tag ${k}">${k==='FE'?'Frontend':k==='BE'?'Backend':'Batch Job'}</span> ${g.length} งาน · ${g.reduce((a,b)=>a+b.total,0)} ชม.</h3>
    <div class="cards">`+g.map(t=>`<a class="card" href="#/task/${t.id}">
      <span class="tag ${t.track}">${t.track}</span>
      <div class="t">${esc(t.title)}</div>
      <div class="d">${esc(t.objective).slice(0,120)}…</div>
      <div class="d" style="margin-top:7px">👤 ${esc(t.ownerShort)} · ⏱ ${t.total} ชม. · 🔌 ${t.apis.length} API${t.triggerEvent.length?' · <span title="ต้องเรียก workflow engine">⚙️ WF</span>':''}</div>
    </a>`).join('')+`</div>`;
  }).join('')}`;
}

function renderTask(id){
  const t=T[id]; if(!t) return '<h1>ไม่พบงานนี้</h1>';
  const ut = t.unitTest ? `${t.total} ชม. <small style="color:var(--muted)">(impl ${t.hours} + unit test ${t.unitTest})</small>` : `${t.hours} ชม.`;
  return `<div class="crumb"><a href="#/">Worklist</a> / ${t.track} / ${esc(t.title)}</div>
  <h1>${esc(t.title)}</h1>
  <p class="sub">${md(t.objective)}</p>
  <div class="meta">
    <span class="chip"><span class="tag ${t.track}">${t.track}</span></span>
    <span class="chip">👤 <b>${esc(t.owner)}</b></span>
    <span class="chip">⏱ <b>${ut}</b></span>
    ${t.step?`<span class="chip">📶 ลำดับขั้น <b>${t.step}</b></span>`:''}
    <span class="chip">📄 <b>${esc(t.file)}</b></span>
  </div>
  <div class="note">📦 <b>โค้ดไปวางที่:</b> ${md(t.repo)}</div>
  ${t.included?'<div class="note">ℹ️ ชั่วโมงของงานนี้นับรวมอยู่ใน <b>FE - Document Detail</b> แล้ว ไม่นับซ้ำในยอดรวม</div>':''}
  <h2>1. ขอบเขตงาน</h2>${list(t.scope)}
  <h2>2. ขั้นตอนการทำงาน</h2>
  ${t.flow.length?'<ol>'+t.flow.map(f=>'<li>'+md(f)+'</li>').join('')+'</ol>':'<p class="empty">— ไม่มี —</p>'}
  <h2>3. ฟิลด์ / รูปแบบ / การตรวจสอบ</h2>
  ${table(['ฟิลด์ / UI','รูปแบบ','การตรวจสอบ','พฤติกรรม'], t.fields.map(f=>f.map(md)))}
  <h2>4. ปุ่ม / การกระทำของผู้ใช้</h2>
  ${table(['การกระทำ','ทริกเกอร์','เรียกอะไร','ผลที่ได้'], t.actions.map(a=>a.map(md)))}
  <h2>5. API ที่ต้องต่อ</h2>
  ${t.apis.length? t.apis.map(apiPill).join(' ') : '<p class="empty">— งานนี้ไม่เรียก API โดยตรง —</p>'}
  <h2>6. ตารางฐานข้อมูลที่แตะ</h2>
  ${t.dbTables.length? table(['ตาราง / Object','R/W','การใช้งาน'],
      t.dbTables.map(d=>[dbPill(String(d[0]).replace('sps_store.','').split(/[ /(]/)[0])+' <span class="mono" style="color:var(--muted);font-size:12px">'+esc(d[0])+'</span>', md(d[1]), md(d[2])]))
    : '<p class="empty">— ไม่ระบุ —</p>'}
  ${t.triggerEvent.length? `<h2>6b. Workflow Trigger Event <small style="font-weight:400;color:var(--muted)">— งานนี้ต้องเรียก @srm/glb-workflow</small></h2>
  <div class="note">🔴 ตาราง <code>sps_store.workflow_*</code> เป็นของ lib — <b>อ่านอย่างเดียว</b> ห้าม INSERT/UPDATE ตรง · ทุกการเรียกต้องผ่าน <code>WorkflowGateway</code> กลาง</div>
  ${table(['จุดที่เรียก','Engine function','พารามิเตอร์หลัก','กติกา / transaction boundary'], t.triggerEvent.map(r=>r.map(md)))}` : ''}
  <h2>7. เกณฑ์ตรวจรับ</h2>${list(t.acceptance)}
  <h2>8. ขอบเขต Unit Test${t.unitTest?` <small style="font-weight:400;color:var(--muted)">— ${t.unitTest} ชั่วโมง</small>`:''}</h2>
  ${t.unitTestCases.length? table(['สิ่งที่ทดสอบ','ประเภท','เกณฑ์ผ่าน'], t.unitTestCases.map(r=>r.map(md)))
    : '<p class="empty">— เอกสารนี้ไม่คิด unit test แยก (เป็นเอกสารสัญญา/ออกแบบ) —</p>'}
  <h2>9. Developer Test Checklist (end-to-end)</h2>${list(t.tests)}
  ${t.deps.length?`<h2>10. ต้องรอให้งานเหล่านี้เสร็จก่อน</h2>${t.deps.map(taskPill).join(' ')}`:''}`;
}

function renderApi(id){
  const k=Object.keys(A).find(x=>A[x].id===id); const a=A[k];
  if(!a) return '<h1>ไม่พบ API เส้นนี้</h1>';
  return `<div class="crumb"><a href="#/">Worklist</a> / API / ${esc(a.path)}</div>
  <h1><span class="m ${a.method}">${a.method}</span> <span class="mono" style="font-size:23px">${esc(a.path)}</span></h1>
  <p class="sub">${md(a.purpose)}</p>
  ${a.kind==='external'?'<div class="note">🔗 <b>เส้นนี้เป็น API ของระบบ SBP เดิม</b> — SBPGI เรียกใช้ ไม่ได้สร้างเอง จึงไม่นับใน 29 เส้นของโครงการ</div>':''}
  ${a.kind==='contract'?'<div class="note">📄 <b>ไม่ใช่ endpoint จริง</b> — เป็นสัญญากลางที่บังคับใช้กับ <i>ทุกเส้น</i> (envelope · error · auth · pagination) จึงเขียนเป็น <code>/*</code></div>':''}
  <h2>1. งานที่เรียกเส้นนี้</h2>${a.tasks.map(taskPill).join(' ')||'<p class="empty">—</p>'}
  <h2>2. Request</h2><pre>${esc(JSON.stringify(a.request,null,2))}</pre>
  <h2>3. Response</h2><pre>${esc(JSON.stringify(a.response,null,2))}</pre>
  <h2>4. ตารางที่ SQL เส้นนี้แตะ</h2>
  ${a.tables.length? a.tables.map(dbPill).join(' ') : '<p class="empty">— ไม่พบตารางในตัวอย่าง SQL —</p>'}
  <h2>5. ตัวอย่าง SQL</h2>
  ${a.sql? '<pre>'+esc(a.sql)+'</pre>' : '<p class="empty">— ยังไม่มีตัวอย่าง SQL สำหรับเส้นนี้ —</p>'}`;
}

function renderDb(name){
  const t=D[name]; if(!t) return '<h1>ไม่พบตารางนี้</h1>';
  return `<div class="crumb"><a href="#/">Worklist</a> / Database / ${esc(name)}</div>
  <h1 class="mono">🗄 ${esc(name)}</h1>
  <p class="sub">${t.columns.length} คอลัมน์ · ${t.constraints.length} constraint</p>
  ${t.existing?'<div class="note">🔗 <b>ตารางของระบบ SBP เดิม</b> (schema <code>sps_store</code>) — SBPGI <b>ห้าม CREATE และห้ามแก้โครงสร้าง</b> · คอลัมน์ที่แสดงมาจาก dump ฐานข้อมูลจริง</div>':''}
  <h2>1. คอลัมน์</h2>
  ${table(['คอลัมน์','ชนิด','บังคับ','FK','หมายเหตุ'], t.columns.map(c=>[
    '<span class="mono">'+esc(c.name)+'</span>'+(c.pk?' 🔑':''),
    '<span class="mono" style="font-size:12.4px">'+esc(c.type)+'</span>',
    c.required?'✔':'',
    c.fk? dbPill(c.fk) : '',
    esc(c.note)]))}
  <h2>2. Constraint</h2>
  ${t.constraints.length? '<pre>'+t.constraints.map(esc).join('\n')+'</pre>' : '<p class="empty">— ไม่มี —</p>'}
  <h2>3. API ที่ใช้ตารางนี้</h2>
  ${t.usedByApi.length? t.usedByApi.map(i=>{const k=Object.keys(A).find(x=>A[x].id===i);return apiPill(k);}).join(' ') : '<p class="empty">—</p>'}
  <h2>4. งานที่อ้างตารางนี้</h2>
  ${t.usedByTask.length? t.usedByTask.map(taskPill).join(' ') : '<p class="empty">—</p>'}`;
}

function buildNav(){
  const g=(label,items,extra='')=>`<div class="grp"><span>${label}</span><span>${items.length}</span></div><div class="nav">${items.join('')}</div>`;
  const ts=Object.values(T);
  const link=(href,ic,txt,h='')=>`<a href="${href}" data-s="${esc(txt).toLowerCase()}"><span class="ic">${ic}</span><span>${esc(txt)}</span>${h?`<span class="h">${h}</span>`:''}</a>`;
  let out=`<div class="nav">${link('#/','🏠','ภาพรวม')}${link('#/board','🗂','Kanban Board')}${link('#/plan','📅','แผนงานรายสัปดาห์')}</div>`;
  [['FE','Frontend','🎨'],['BE','Backend','⚙️'],['Job','Batch Job','⏰']].forEach(([k,label,ic])=>{
    // งาน role pack นับชั่วโมงรวมอยู่ใน Document Detail แล้ว — ทำเครื่องหมายกันเข้าใจผิดว่านับซ้ำ
    out+=g(label, ts.filter(t=>t.track===k).map(t=>link('#/task/'+t.id, ic, t.title, t.included?'incl.':t.total+'h')));
  });
  const apiLink=k=>link('#/api/'+A[k].id,'<span class="m '+A[k].method+'" style="font-size:9.5px;padding:1px 4px">'+A[k].method+'</span>',A[k].path);
  out+=g('API ของ SBPGI', Object.keys(A).filter(k=>A[k].kind==='own').sort().map(apiLink));
  out+=g('API ระบบเดิม (reuse)', Object.keys(A).filter(k=>A[k].kind==='external').sort().map(apiLink));
  // kind='contract' เป็น pseudo endpoint (/*) ของเอกสารสัญญากลาง ไม่ใช่เส้นจริง จึงไม่ขึ้นเมนู
  out+=g('Database (SBPGI)', Object.keys(D).filter(n=>!D[n].existing).sort().map(n=>link('#/db/'+n,'🗄',n)));
  out+=g('Database ระบบเดิม (reuse)', Object.keys(D).filter(n=>D[n].existing).sort().map(n=>link('#/db/'+n,'🗄',n)));
  return out;
}

/* ---------- Kanban board (สถานะเก็บใน localStorage ของเครื่องผู้ใช้) ---------- */
const COLS=[['todo','ยังไม่เริ่ม','#9b9a97'],['doing','กำลังทำ','#2383e2'],
            ['review','รอรีวิว','#d9730d'],['blocked','ติดปัญหา','#e03e3e'],['done','เสร็จแล้ว','#0f7b6c']];
const BK='sbpgi.worklist.board.v1', FK='sbpgi.worklist.filter.v1';
const BOARD_FILE='worklist-board.json';   // baseline ที่ commit ขึ้น git ได้
const ORDER=Object.keys(T).sort();        // ลำดับคงที่ ใช้เข้ารหัสสถานะลง URL
const CODE=COLS.map(c=>c[0]);

/* localStorage ใช้ไม่ได้เมื่อเปิดด้วย file:// หรือปิดคุกกี้ — ต้องกันทุกจุด
   ไม่งั้น setItem จะ throw แล้วทำให้ drag-drop/ตัวกรองตายทั้งอัน (เจอจริง 2026-08-18) */
const LS={
  get(k){ try{ return localStorage.getItem(k); }catch(e){ return null; } },
  set(k,v){ try{ localStorage.setItem(k,v); return true; }catch(e){ LS.warn(); return false; } },
  del(k){ try{ localStorage.removeItem(k); }catch(e){} },
  warned:false,
  warn(){ if(LS.warned) return; LS.warned=true;
    const el=document.createElement('div');
    el.className='note'; el.style.cssText='position:fixed;right:16px;bottom:16px;max-width:420px;z-index:99;background:var(--bg);box-shadow:0 6px 24px rgba(0,0,0,.25)';
    el.innerHTML='⚠️ <b>บันทึกสถานะลงเครื่องไม่ได้</b> — เบราว์เซอร์บล็อก localStorage (มักเกิดเมื่อเปิดไฟล์ตรงด้วย <code>file://</code>) · '+
      'กระดานยังลากได้ปกติแต่จะหายเมื่อปิดหน้า · เปิดผ่าน <code>python3 -m http.server</code> แล้วเข้า <code>localhost</code> เพื่อให้บันทึกได้';
    document.body.appendChild(el); setTimeout(()=>el.remove(),12000);
  }
};
const loadF=()=>{try{return JSON.parse(LS.get(FK))||{track:'',owner:''}}catch(e){return {track:'',owner:''}}};
const saveF=f=>LS.set(FK,JSON.stringify(f));
let BOARD={};                              // สถานะปัจจุบันในหน่วยความจำ (แหล่งความจริงตอนใช้งาน)
const saveB=b=>{BOARD=b;LS.set(BK,JSON.stringify(b));};
const statusOf=id=>BOARD[id]||'todo';

/* --- เข้ารหัสสถานะทั้งกระดานเป็นสตริงสั้น ๆ เพื่อแชร์ผ่านลิงก์ (38 ตัวอักษร) --- */
function encodeBoard(b){ return ORDER.map(id=>CODE.indexOf(b[id]||'todo')).join(''); }
function decodeBoard(str){
  const out={};
  [...String(str)].forEach((ch,i)=>{ const c=CODE[+ch]; if(c&&c!=='todo'&&ORDER[i]) out[ORDER[i]]=c; });
  return out;
}

/* --- ลำดับความสำคัญของแหล่งสถานะ: URL > localStorage > ไฟล์ baseline ใน git --- */
async function initBoard(){
  const m=location.hash.match(/[?&]b=([0-4]+)/);
  if(m){ BOARD=decodeBoard(m[1]); LS.set(BK,JSON.stringify(BOARD)); return 'url'; }
  try{ const raw=LS.get(BK); if(raw){ BOARD=JSON.parse(raw); return 'local'; } }catch(e){}
  try{
    const r=await fetch(BOARD_FILE,{cache:'no-store'});
    if(r.ok){ BOARD=await r.json(); return 'file'; }
  }catch(e){}
  BOARD={}; return 'empty';
}
let BOARD_SRC='empty';

function downloadBoard(){
  const blob=new Blob([JSON.stringify(BOARD,null,2)+'\n'],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download=BOARD_FILE;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

function renderBoard(){
  const f=loadF();
  const owners=[...new Set(Object.values(T).map(t=>t.ownerShort))].sort();
  const ts=Object.values(T).filter(t=>(!f.track||t.track===f.track)&&(!f.owner||t.ownerShort===f.owner));
  const cols=COLS.map(([k,label,c])=>{
    const items=ts.filter(t=>statusOf(t.id)===k);
    const hrs=items.reduce((a,x)=>a+(x.included?0:x.total),0);
    return `<div class="col" data-col="${k}">
      <h4><span class="sw" style="background:${c}"></span>${label}<span class="n">${items.length} · ${hrs}h</span></h4>
      ${items.map(t=>{
        const blocked=t.deps.filter(d=>statusOf(d)!=='done');
        return `<div class="kc" draggable="true" data-id="${t.id}">
          <span class="tag ${t.track}">${t.track}</span>
          <div class="kt">${esc(t.title)}</div>
          <div class="km"><span>👤 ${esc(t.ownerShort)}</span><span>⏱ ${t.included?'incl.':t.total+'h'}</span>
            <span>🔌 ${t.apis.length}</span>${t.triggerEvent.length?'<span title="ต้องเรียก workflow engine">⚙️ WF</span>':''}${t.step?`<span>📶 ${t.step}</span>`:''}
            ${blocked.length?`<span class="lock" title="รอ ${blocked.length} งาน">🔒 ${blocked.length}</span>`:''}</div>
          <a class="open" draggable="false" href="#/task/${t.id}">เปิดรายละเอียด →</a>
        </div>`}).join('')||'<p class="empty" style="margin:4px">— ว่าง —</p>'}
    </div>`}).join('');
  return `<h1>Kanban Board</h1>
  <p class="sub">ลากการ์ดข้ามคอลัมน์เพื่อเปลี่ยนสถานะ — สถานะเก็บใน localStorage ของเครื่องคุณเอง (ไม่ได้ sync กับใคร)</p>
  <div class="bar">
    <select id="fTrack"><option value="">ทุกสาย</option>${['FE','BE','Job'].map(k=>`<option value="${k}"${f.track===k?' selected':''}>${k}</option>`).join('')}</select>
    <select id="fOwner"><option value="">ทุกคน</option>${owners.map(o=>`<option${f.owner===o?' selected':''}>${esc(o)}</option>`).join('')}</select>
    <button id="bLink">🔗 คัดลอกลิงก์แชร์</button>
    <button id="bSave">💾 บันทึกเป็นไฟล์</button>
    <button id="bLoad">📂 โหลดจากไฟล์</button>
    <input id="fFile" type="file" accept="application/json,.json" hidden>
    <button id="bReset">ล้างสถานะ</button>
  </div>
  <div class="note" style="margin-top:0">
    <b>สถานะเก็บที่ไหน</b> — ทำงานประจำวันเก็บใน <b>localStorage</b> ของเครื่องคุณเอง (auto) ·
    จะแชร์ให้ทีมดูเร็ว ๆ ใช้ <b>🔗 ลิงก์แชร์</b> (ฝังสถานะไว้ในลิงก์ ไม่ต้องแตะ git) ·
    จะเก็บเป็นหลักฐานทีมให้กด <b>💾 บันทึกเป็นไฟล์</b> แล้ว commit <code>worklist-board.json</code> ขึ้น git —
    หน้าเว็บจะอ่านไฟล์นี้เป็นค่าตั้งต้นให้คนที่เปิดครั้งแรกโดยอัตโนมัติ ·
    <b>ที่มาของสถานะรอบนี้: ${({url:'ลิงก์แชร์',local:'localStorage ของเครื่องนี้',file:BOARD_FILE+' ใน git',empty:'ยังไม่เคยตั้งค่า'})[BOARD_SRC]||BOARD_SRC}</b>
  </div>
  <div class="board">${cols}</div>
  <p class="legend">🔒 = ยังมีงานที่ต้องเสร็จก่อน (ดูหัวข้อ dependency ในหน้างาน) · 📶 = ลำดับขั้นตามแผน · 🔌 = จำนวน API ที่ต้องต่อ · การ์ดที่เป็น <b>incl.</b> คือ role pack ที่นับชั่วโมงรวมใน Document Detail แล้ว</p>`;
}

function wireBoard(){
  let dragId=null;
  document.querySelectorAll('.kc').forEach(el=>{
    el.addEventListener('dragstart',e=>{dragId=el.dataset.id;el.classList.add('drag');e.dataTransfer.effectAllowed='move';});
    el.addEventListener('dragend',()=>{dragId=null;el.classList.remove('drag');});
  });
  document.querySelectorAll('.col').forEach(col=>{
    col.addEventListener('dragover',e=>{e.preventDefault();col.classList.add('over');});
    col.addEventListener('dragleave',()=>col.classList.remove('over'));
    col.addEventListener('drop',e=>{
      e.preventDefault();col.classList.remove('over');
      if(!dragId) return;
      saveB({...BOARD, [dragId]: col.dataset.col}); route();
    });
  });
  const f=loadF();
  $('#fTrack').onchange=e=>{f.track=e.target.value;saveF(f);route();};
  $('#fOwner').onchange=e=>{f.owner=e.target.value;saveF(f);route();};
  $('#bReset').onclick=()=>{ if(confirm('ล้างสถานะงานทั้งหมดกลับเป็น "ยังไม่เริ่ม" ?')){LS.del(BK);BOARD={};route();} };
  $('#bSave').onclick=downloadBoard;
  $('#bLoad').onclick=()=>$('#fFile').click();
  $('#fFile').onchange=async e=>{
    const f=e.target.files[0]; if(!f) return;
    try{ saveB(JSON.parse(await f.text())); BOARD_SRC='ไฟล์ที่โหลดเข้ามา'; route(); }
    catch(err){ alert('อ่านไฟล์ไม่ได้: '+err.message); }
  };
  $('#bLink').onclick=async()=>{
    const url=location.origin+location.pathname+'#/board?b='+encodeBoard(BOARD);
    try{ await navigator.clipboard.writeText(url); $('#bLink').textContent='คัดลอกลิงก์แล้ว ✓';
         setTimeout(()=>$('#bLink').textContent='🔗 คัดลอกลิงก์แชร์',1800); }
    catch(e){ prompt('คัดลอกลิงก์นี้',url); }
  };
}

/* ---------- Work Plan: งานเป็นแถว · สัปดาห์เป็นคอลัมน์ ---------- */
const DAYS_PER_WEEK=M.daysPerWeek;   // กติกาเวลามาจาก LLDD (build_lldd_documents) ไม่ฝังตายตัวในหน้านี้
const weekOf=d=>Math.floor(d/DAYS_PER_WEEK);

function renderPlan(){
  const f=loadF();
  const all=Object.values(T).filter(t=>t.startDay!=null);
  const groupByOwner=!f.track&&!f.owner;
  // จัดกลุ่มเมื่อไร ต้องเรียงตามคนก่อน ไม่งั้นแถวของแต่ละคนจะกระจายแล้วหัวข้อซ้ำ
  const ts=all.filter(t=>(!f.track||t.track===f.track)&&(!f.owner||t.ownerShort===f.owner))
              .sort((a,b)=> groupByOwner
                ? (a.ownerShort.localeCompare(b.ownerShort)||a.startDay-b.startDay)
                : (a.startDay-b.startDay||a.step-b.step));
  if(!ts.length) return '<h1>แผนงานรายสัปดาห์</h1><p class="empty">ไม่มีงานตามตัวกรองนี้</p>';
  const maxW=Math.max(...all.map(t=>weekOf(t.endDay)));
  const weeks=[...Array(maxW+1).keys()];
  const owners=[...new Set(all.map(t=>t.ownerShort))].sort();

  const head='<tr><th class="tname">งาน</th>'+weeks.map(w=>`<th>W${w+1}</th>`).join('')+'</tr>';
  let body='', lastOwner=null;
  ts.forEach(t=>{
    const s=weekOf(t.startDay), e=weekOf(t.endDay), dur=t.endDay-t.startDay+1;
    if(groupByOwner&&t.ownerShort!==lastOwner){
      lastOwner=t.ownerShort;
      const mine=ts.filter(x=>x.ownerShort===lastOwner);
      {const cap=M.owners.find(o=>o.short===lastOwner||o.name===lastOwner);
        const tag=cap? (cap.over>0
          ? ` · <b style="color:#e03e3e">${cap.weeks} สัปดาห์ — เกินเพดาน ${M.ceiling} ชม. อยู่ ${cap.over} ชม.</b>`
          : ` · <b style="color:#0f7b6c">${cap.weeks} สัปดาห์ — อยู่ในกรอบ ${M.targetWeeks} สัปดาห์</b>`) : '';
        body+=`<tr class="grp"><td colspan="${weeks.length+1}">👤 ${esc(lastOwner)} — ${mine.length} งาน · ${mine.reduce((a,b)=>a+b.total,0)} ชม.${tag}</td></tr>`;}
    }
    body+=`<tr><td class="tname"><a href="#/task/${t.id}">${esc(t.title)}</a>
      <div class="sm"><span class="tag ${t.track}">${t.track}</span><span>👤 ${esc(t.ownerShort)}</span>
      <span>⏱ ${t.total}h</span><span>📶 ${t.step}</span></div></td>`;
    weeks.forEach(w=>{
      if(w===s){
        body+=`<td class="wk" colspan="${e-s+1}"><div class="bar2 ${t.track}" title="${esc(t.title)} · ${dur} วันทำการ">${dur}d</div></td>`;
      } else if(w<s||w>e){ body+='<td class="wk"></td>'; }
    });
    body+='</tr>';
  });

  // ภาระงานรวมต่อสัปดาห์ (ชั่วโมงที่ตกในแต่ละสัปดาห์ เฉลี่ยตามความยาวงาน)
  const load=weeks.map(()=>0);
  all.forEach(t=>{ const dur=t.endDay-t.startDay+1, per=t.total/dur;
    for(let d=t.startDay;d<=t.endDay;d++) load[weekOf(d)]+=per; });
  const foot='<tr><td class="tname"><b>ภาระงานรวม/สัปดาห์</b><div class="sm">${M.owners.length} คน × ${M.hoursPerWeek} ชม. = ${M.owners.length*M.hoursPerWeek} ชม./สัปดาห์ · เป้าหมาย ${M.targetWeeks} สัปดาห์ (${M.ceiling} ชม./คน)</div></td>'+
    weeks.map(w=>`<td class="wk"><b style="color:${load[w]>180?'var(--del)':'var(--muted)'}">${Math.round(load[w])}h</b></td>`).join('')+'</tr>';

  return `<h1>แผนงานรายสัปดาห์ (Work Plan)</h1>
  <p class="sub">ลำดับงานคำนวณจาก <b>dependency จริง</b> + คิวของเจ้าของงาน (หนึ่งคนทำได้ทีละฉบับ) ·
  ความยาวแท่งมาจาก <b>ชั่วโมงรวม impl + unit test</b> ที่ ${M.hoursPerDay} ชม./วัน · ไม่ผูกกับปฏิทินจริง จึงนับเป็น W1, W2, …</p>
  <div class="bar">
    <select id="fTrack"><option value="">ทุกสาย</option>${['FE','BE','Job'].map(k=>`<option value="${k}"${f.track===k?' selected':''}>${k}</option>`).join('')}</select>
    <select id="fOwner"><option value="">ทุกคน</option>${owners.map(o=>`<option${f.owner===o?' selected':''}>${esc(o)}</option>`).join('')}</select>
    <a class="pill" href="#/board" style="padding:6px 12px">🗂 ดูแบบ Kanban</a>
  </div>
  <div class="plan"><table><thead>${head}</thead><tbody>${body}${foot}</tbody></table></div>
  <p class="milestone"><span>🟩 FE</span><span>🟦 BE</span><span>🟪 Batch Job</span>
    <span>📶 = ลำดับขั้น (งานขั้นเดียวกันเริ่มพร้อมกันได้)</span>
    <span>รวม ${all.length} งาน · ${all.reduce((a,b)=>a+b.total,0)} ชม. · ${maxW+1} สัปดาห์</span></p>
  <div class="note">งาน role pack 5 ฉบับไม่แสดงในแผนนี้ เพราะชั่วโมงถูกนับรวมใน <b>FE - Document Detail</b> แล้ว (ไม่นับซ้ำ)</div>`;
}

function wirePlan(){
  const f=loadF();
  $('#fTrack').onchange=e=>{f.track=e.target.value;saveF(f);route();};
  $('#fOwner').onchange=e=>{f.owner=e.target.value;saveF(f);route();};
}

function route(){
  const h=location.hash.replace(/^#/,'')||'/';
  const p=h.split('/').filter(Boolean);
  let html;
  if(p[0]==='board') html=renderBoard();
  else if(p[0]==='plan') html=renderPlan();
  else if(p[0]==='task') html=renderTask(p[1]);
  else if(p[0]==='api') html=renderApi(p[1]);
  else if(p[0]==='db') html=renderDb(decodeURIComponent(p[1]));
  else html=renderHome();
  $('main').innerHTML=html;
  if(p[0]==='board') wireBoard();
  if(p[0]==='plan') wirePlan();
  document.querySelectorAll('.nav a').forEach(a=>a.classList.toggle('on', a.getAttribute('href')===location.hash));
  window.scrollTo(0,0);
}
addEventListener('hashchange',route);
$('#nav').innerHTML=buildNav();
$('.search').addEventListener('input',e=>{
  const q=e.target.value.trim().toLowerCase();
  document.querySelectorAll('.nav a').forEach(a=>{
    a.style.display = !q || (a.dataset.s||'').includes(q) ? '' : 'none';
  });
});
initBoard().then(src=>{ BOARD_SRC=src; route(); });
"""


def render(model: dict) -> str:
    data = json.dumps(model, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Worklist — ระบบประกันรายได้ SBPGI</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <aside class="side">
    <div class="brand"><span class="dot">SB</span><span>SBPGI Worklist</span></div>
    <!-- หน้านี้อยู่ในเมนูกลุ่ม Plan ของ sbp.js แต่เป็น standalone (มี sidebar ของตัวเอง) จึงต้องมีทางกลับเอง -->
    <a class="back" href="k2-list-waiting.html">← กลับระบบประกันรายได้</a>
    <div style="padding:0 10px"><input class="search" placeholder="ค้นหางาน / API / ตาราง…"></div>
    <div id="nav"></div>
  </aside>
  <main></main>
</div>
<script>const DATA = {data};</script>
<script>{JS}</script>
</body>
</html>
"""


def main() -> None:
    model = build_model()
    out = ROOT / "worklist.html"
    out.write_text(render(model), encoding="utf-8")
    _own = sum(1 for a in model["apis"].values() if a.get("kind") == "own")
    _ext = sum(1 for a in model["apis"].values() if a.get("kind") == "external")
    _ctr = sum(1 for a in model["apis"].values() if a.get("kind") == "contract")
    _new = sum(1 for t in model["tables"].values() if not t.get("existing"))
    _old = len(model["tables"]) - _new
    print(f"worklist.html · งาน {len(model['tasks'])} หัวข้อ (LLDD 40 ฉบับ) · "
          f"API {_own} ของ SBPGI + {_ext} ระบบเดิม + {_ctr} pseudo · "
          f"ตาราง {_new} SBPGI + {_old} ระบบเดิม · {out.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
