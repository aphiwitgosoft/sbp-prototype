"""Skeleton-code block generator สำหรับเอกสาร LLDD ฝั่ง Batch Job (Job 1–10 + 8b).

entry point: ``job_skeleton_blocks(topic, ctx) -> list[dict]``

ผลิต block ส่วน "Skeleton Code" ที่ data-driven จาก job dict ใน ``JOBS``
(``job-batch.html``) ที่ generator อ่านมาให้แล้วผ่าน ``ctx["job"]`` — flow / tables /
params / meta ของแต่ละ job ทำให้ skeleton ของแต่ละฉบับต่างกันจริง

convention ที่ยึด (ตัดสินใจ 2026-08-06):
  * ไม่มีตาราง ``job_configs`` / ``job_run_histories`` และไม่มี Job Admin API
    → cron/พารามิเตอร์อยู่ใน backend config (env/config file), ผลการรันเขียน
      application log แบบ structured + ``interface_transactions``
  * runner กันรันซ้อนด้วย PostgreSQL advisory lock (ไม่ใช่แถว RUNNING ในตาราง)
  * job error → ส่งอีเมลผ่าน ``@gosoft-sbp/email-lib`` ของระบบเดิม
  * ไฟล์ interface ยังใช้กลไกเดิม (fixed-width + encoding เดิม)
  * โครง NestJS ตาม ``srm-sps-spsap-store-backend``: custom provider ``DATA_SOURCE``,
    repository provider แบบ factory token string, entity ใน ``src/entitys/``,
    workflow ผ่าน ``@srm/glb-workflow``

ห้าม import จาก build_lldd_documents.py (กัน circular import) — helper ประกาศเองด้านล่าง
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# block helpers (รูปแบบเดียวกับ build_lldd_documents.py)
# ---------------------------------------------------------------------------



# unique key เชิงธุรกิจของแต่ละตาราง — คัดจาก CONSTRAINT ใน DDL (tools/build_lldd_documents.py)
# ใช้เติม ON CONFLICT ใน skeleton ให้ตรงของจริง แทนที่จะปล่อยเป็น TODO ให้ dev เดา
BUSINESS_UNIQUE_KEYS: dict[str, str] = {
    "fgi_impact_stores": "impacted_store_code, new_store_code, impact_month",
    "fgi_impact_competitors": "impact_process_id, competitor_code, period_key",
    "fgi_impact_processes": "impacted_store_code, impact_month",
    "sales_transactions": "sales_summary_id, txn_date, window_no",
    "document_competitors": "doc_no, competitor_code",
    "document_new_stores": "doc_no, new_store_code",
    "compensation_documents": "source, impacted_store_code, impact_month, new_store_code, round_no",
    "interface_transactions": "data_name, direction, business_key, period_key",
}

def p(text: str) -> dict[str, Any]:
    return {"type": "p", "text": text}


def h(level: int, text: str) -> dict[str, Any]:
    return {"type": f"h{level}", "text": text}


def bullets(items: list[str]) -> dict[str, Any]:
    return {"type": "bullets", "items": [str(i) for i in items]}


def table(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}


def code(text: str, lang: str = "") -> dict[str, Any]:
    return {"type": "code", "text": text, "lang": lang}


# ---------------------------------------------------------------------------
# naming helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")
_ASCII_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def _tokens(name: str) -> list[str]:
    return _TOKEN_RE.findall(name or "")


def _kebab(name: str) -> str:
    parts = [t.lower() for t in _tokens(name)]
    return "-".join(parts) or "job"


def _pascal(name: str) -> str:
    return "".join(t.capitalize() for t in _tokens(name)) or "Job"


def _camel(words: list[str]) -> str:
    words = [w for w in words if w]
    if not words:
        return "param"
    head = words[0].lower()
    return head + "".join(w.capitalize() for w in words[1:])


def _upper_snake(camel: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", camel)
    return s.upper()


def _job_slug(no: str) -> str:
    """'8b' -> '8B' สำหรับ env prefix"""
    return re.sub(r"[^A-Za-z0-9]", "", str(no)).upper()


# ---------------------------------------------------------------------------
# param key mapping (label ภาษาไทย/อังกฤษ -> key TS)
# ---------------------------------------------------------------------------

_THAI_KEY_HINTS: list[tuple[str, str]] = [
    ("กำหนดการรัน", "cron"),
    ("งวดข้อมูล", "period"),
    ("งวด", "period"),
    ("เงื่อนไขวันปัจจุบัน", "currentDateRule"),
    ("เงื่อนไขอายุ", "storeAgeRule"),
    ("เงื่อนไข", "condition"),
    ("เกณฑ์", "threshold"),
    ("กฎ", "rule"),
    ("หน้าต่างคำนวณ", "calcWindow"),
    ("หน้าต่าง", "window"),
    ("วันทำการ", "workingDays"),
    ("ปลายทาง", "destination"),
    ("ต้นทาง", "sourcePath"),
    ("ผู้รับ", "recipients"),
    ("อีเมล", "email"),
    ("จำนวน", "count"),
    ("ขนาด", "size"),
    ("ไฟล์", "file"),
    ("สถานะ", "status"),
    ("รหัส", "code"),
    ("ร้าน", "store"),
    ("เวลา", "time"),
    ("รอบ", "round"),
]

_SKIP_ASCII = {"th", "yyyy", "mm", "dd", "utf", "ph"}


def _param_key(label: str, index: int) -> str:
    ascii_tokens = [t for t in _ASCII_RE.findall(label or "") if t.lower() not in _SKIP_ASCII]
    if ascii_tokens:
        words: list[str] = []
        for token in ascii_tokens[:3]:
            for part in token.split("_"):
                words.extend(_tokens(part) or [part])
        key = _camel([w.lower() for w in words if w])
        if key and key[0].isalpha():
            return key
    for needle, key in _THAI_KEY_HINTS:
        if needle in (label or ""):
            return key
    return f"param{index}"


def _dedupe(keys: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for key in keys:
        if key in seen:
            seen[key] += 1
            out.append(f"{key}{seen[key]}")
        else:
            seen[key] = 1
            out.append(key)
    return out


def _ts_string(value: Any) -> str:
    text = str(value if value is not None else "")
    text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    return f"'{text}'"


def _is_number(value: Any) -> bool:
    try:
        float(str(value).replace(",", ""))
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# flow step -> method name
# ---------------------------------------------------------------------------

_VERB_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("ดาวน์โหลด", "download"), "Download"),
    (("เชื่อมต่อ SFTP", "SFTP", "เชื่อมต่อ"), "Connect"),
    (("อ่านไฟล์", "รับไฟล์"), "ReadFile"),
    (("อ่าน",), "Read"),
    (("เขียนไฟล์", "สร้างไฟล์"), "WriteFile"),
    (("ย้ายไฟล์", "backup", "quarantine"), "Archive"),
    (("อัปโหลด", "upload", "ส่งไฟล์"), "Upload"),
    (("upsert", "Upsert"), "Upsert"),
    (("insert", "บันทึก"), "Insert"),
    (("อัปเดต", "update", "พลิกธง", "ตั้งค่า", "แก้สถานะ"), "Update"),
    (("ลบ",), "Delete"),
    (("คำนวณ", "calc"), "Calculate"),
    (("dedup", "Dedup", "จับคู่"), "Dedup"),
    (("parse", "แปลง"), "Parse"),
    (("workflow", "Workflow", "instance", "task"), "Workflow"),
    (("เอกสาร", "doc_no", "document"), "Document"),
    (("เมล", "อีเมล", "แจ้ง", "notify"), "Notify"),
    (("ตรวจ", "validate", "reconcile"), "Validate"),
    (("seed", "เตรียม"), "Prepare"),
    (("เติมข้อมูล", "enrich", "map "), "Enrich"),
    (("กำหนดงวด", "งวด"), "ResolvePeriod"),
    (("query", "SELECT", "ค้น", "เลือก"), "Query"),
    (("rollback", "Rollback"), "Rollback"),
    (("commit", "Commit"), "Commit"),
]

_WRITE_HINTS = (
    "insert", "upsert", "update", "ลบ", "บันทึก", "อัปเดต", "พลิกธง", "เขียน",
    "สร้าง", "commit", "Commit", "seed", "task", "instance", "tracking",
)


def _table_note(text: str) -> str:
    """แทนคำที่อ้างตารางซึ่งถูกตัดไปแล้ว ด้วย use case ของ @srm/glb-workflow / ตารางระบบเดิม

    (ผังใน job-batch.html ยังเขียนว่า "insert workflow_instances + workflow_tasks" ซึ่งขัดกับ
    หัวข้อ Repository/SQL ของเอกสารฉบับเดียวกันที่ห้ามเขียน SQL ตรงกับสองตารางนี้)
    """
    out = str(text or "")
    swap = {
        "workflow_instances + workflow_tasks": "workflow transaction + prepared approver ผ่าน @srm/glb-workflow",
        "workflow_instances": "workflow transaction (`sps_store.workflow_transaction` ผ่าน initializeWorkflow ของ @srm/glb-workflow)",
        "workflow_tasks": "prepared approver (`sps_store.workflow_approver` ผ่าน addPreApprover ของ @srm/glb-workflow)",
        "workflow_sections": "`sps_store.workflow_state` (@srm/glb-workflow)",
        "document_statuses": "`sps_store.workflow_status` (@srm/glb-workflow)",
    }
    for old, new in swap.items():
        if old in out:
            out = out.replace(old, new)
    return out


def _verb(text: str, fallback: str) -> str:
    for needles, verb in _VERB_HINTS:
        for needle in needles:
            if needle in (text or ""):
                return verb
    return fallback


def _is_write_step(step: dict[str, Any]) -> bool:
    text = f"{step.get('t', '')} {step.get('d', '')}"
    return step.get("k") in {"p", "io"} and any(hint in text for hint in _WRITE_HINTS)


# ---------------------------------------------------------------------------
# ctx / topic extraction
# ---------------------------------------------------------------------------


def _job_from_ctx(ctx: Any) -> dict[str, Any]:
    if isinstance(ctx, dict):
        job = ctx.get("job")
        if isinstance(job, dict):
            return job
        if any(key in ctx for key in ("flow", "tables", "params", "meta")):
            return ctx
    job = getattr(ctx, "job", None)
    if isinstance(job, dict):
        return job
    return {}


def _job_no(topic: Any, job: dict[str, Any]) -> str:
    if job.get("no"):
        return str(job["no"])
    file_name = str(getattr(topic, "file", "") or "")
    match = re.search(r"LLDD-BE-Job-([0-9]+[a-zA-Z]?)-", file_name)
    if match:
        return match.group(1)
    return "X"


def _job_name(topic: Any, job: dict[str, Any]) -> str:
    if job.get("name"):
        return str(job["name"])
    file_name = str(getattr(topic, "file", "") or "")
    match = re.search(r"LLDD-BE-Job-[0-9]+[a-zA-Z]?-(.+)$", file_name)
    if match:
        return match.group(1).replace("-", "")
    return "BatchJob"


def _flow_steps(topic: Any, job: dict[str, Any]) -> list[dict[str, Any]]:
    flow = job.get("flow")
    if isinstance(flow, list) and flow and isinstance(flow[0], dict):
        return [dict(item) for item in flow]
    # fallback: topic.flow เป็น list[str] ("ข้อความ | No: ... (รายละเอียด)")
    steps: list[dict[str, Any]] = []
    for raw in getattr(topic, "flow", []) or []:
        text = str(raw)
        detail = ""
        no_branch = ""
        detail_match = re.search(r"\(([^()]*)\)\s*$", text)
        if detail_match:
            detail = detail_match.group(1)
            text = text[: detail_match.start()].strip()
        if " | No: " in text:
            text, no_branch = text.split(" | No: ", 1)
        plain = text.strip()
        kind = "d" if no_branch else "p"
        if plain in {"เริ่ม", "Start"}:
            kind = "start"
        elif plain in {"จบ", "End", "Commit / จบ", "จบการทำงาน"}:
            kind = "end"
        steps.append({
            "k": kind,
            "t": plain,
            "d": detail,
            "no": no_branch.strip(),
        })
    return steps


def _params(topic: Any, job: dict[str, Any]) -> list[list[Any]]:
    params = job.get("params")
    if isinstance(params, list) and params:
        return [list(item) for item in params]
    rows: list[list[Any]] = []
    for field in getattr(topic, "fields", []) or []:
        name = field[0] if len(field) > 0 else "param"
        value = field[1] if len(field) > 1 else ""
        note = field[3] if len(field) > 3 else ""
        rows.append([name, value, "number" if _is_number(value) else "text", 1, note])
    return rows


def _tables(topic: Any, job: dict[str, Any]) -> list[list[Any]]:
    tables = job.get("tables")
    if isinstance(tables, list) and tables:
        return [list(item) for item in tables]
    return [list(item) for item in (getattr(topic, "db_tables", []) or [])]


# ตารางที่ถูกยกเลิก/แทนที่ตามการตัดสินใจ 2026-08-06 — ห้าม generate SQL ตรง ๆ
_REPLACED_TABLES: dict[str, str] = {
    "job_configs": "ยกเลิกแล้ว — cron/พารามิเตอร์อยู่ใน backend config (env/config file)",
    "job_run_histories": "ยกเลิกแล้ว — ผลการรันเขียน application log แบบ structured + interface_transactions",
    "workflow_instances": "ใช้ @srm/glb-workflow (`sps_store.workflow_transaction`) ผ่าน initializeWorkflow แทน SQL ตรง",
    "workflow_tasks": "ใช้ @srm/glb-workflow (`sps_store.workflow_approver` / `workflow_history`) ผ่าน addPreApprover + eventWorkflow",
    "workflow_sections": "ใช้ @srm/glb-workflow (`sps_store.workflow_state` / `workflow_route`) แทน",
    "document_statuses": "ใช้ @srm/glb-workflow (`sps_store.workflow_status`) แทน",
    "email_templates": "ใช้ตาราง email_template + email_sent ของระบบเดิม ผ่าน @gosoft-sbp/email-lib",
    "stores": "ใช้ store / mas_store / sevenshop ของระบบเดิม",
    "zones": "ใช้ mas_zone ของระบบเดิม",
    "employees": "ใช้ business_user ของระบบเดิม",
    "system_configs": "ใช้ mas_param ของระบบเดิม",
    "branch_types": "ใช้ common_code ของระบบเดิม",
}


# ---------------------------------------------------------------------------
# section 1 — ผังไฟล์
# ---------------------------------------------------------------------------


def _file_map_blocks(no: str, folder: str, base: str, pascal: str, job: dict[str, Any]) -> list[dict[str, Any]]:
    root = f"src/batch/sbpgi/{folder}"
    rows = [
        [
            f"{root}/{base}.job.ts",
            f"คลาส `{pascal}Job` — `run(ctx)` เรียงตาม flow ของ Job {no} ทีละขั้น, ครอบ transaction, จบด้วย structured log",
        ],
        [
            f"{root}/{base}.service.ts",
            f"คลาส `{pascal}Service` — logic ต่อขั้น (อ่าน/parse/คำนวณ/เขียน) + repository token ที่ inject จาก `DATA_SOURCE`",
        ],
        [
            f"{root}/{base}.config.ts",
            f"คลาส `SbpgiJob{_job_slug(no)}Config` (แบบเดียวกับ `src/config/app.config.ts` — โปรเจกต์นี้ไม่ใช้ `registerAs`) "
            f"— cron และพารามิเตอร์ทั้ง {len(job.get('params', []) or [])} ตัวของ Job {no} อ่านจาก env/config file (ไม่มีตาราง job_configs)",
        ],
        [
            f"{root}/{base}.module.ts",
            "NestJS module ผูก job + service + repository provider (factory token string) เข้ากับ `DatabaseModule`",
        ],
        [
            "src/batch/runner.ts",
            "ตัวรันกลาง: resolve job ตาม jobNo, กันรันซ้อนด้วย advisory lock, จับ error → แจ้งเตือน, เขียน structured log สรุป (ใช้ร่วมทั้ง 11 job)",
        ],
        [
            "src/batch/scheduler.ts",
            f"ลงทะเบียน cron จาก config (`SBPGI_JOB{_job_slug(no)}_CRON` = `{job.get('cron', '-')}`) และรองรับสั่งรันนอกรอบผ่าน CLI/runbook",
        ],
        [
            "src/batch/job-failure.notifier.ts",
            "ส่งอีเมลแจ้งผู้ดูแลเมื่อ job ล้มเหลว ผ่าน `EmailLibService` ของ `@gosoft-sbp/email-lib` (log ลง `email_sent` ให้อัตโนมัติ)",
        ],
    ]
    return [
        h(2, f"5.94 ผังไฟล์ที่ต้องสร้าง (Job {no})"),
        p(
            f"โครงไฟล์ของ Job {no} ({job.get('cls', '-')} เดิม) วางใต้ `src/batch/sbpgi/` ของ store-backend "
            "โดยใช้ convention เดียวกับ module ธุรกิจอื่น: inject custom provider `DATA_SOURCE` แล้วยิง raw SQL, "
            "repository ประกาศเป็น factory provider ที่ใช้ token string, entity อยู่ใน `src/entitys/`"
        ),
        p(
            "**หมายเหตุสำคัญ — `src/batch/*` ทั้งชุดเป็นของใหม่ที่ยังไม่มีใน store-backend**: ปัจจุบัน repo "
            "ไม่มีโฟลเดอร์ `src/batch` เลย และแม้จะติดตั้ง `@nestjs/schedule` ไว้แล้วก็ยัง**ไม่มี `@Cron`/"
            "`@Interval` แม้แต่จุดเดียว** ดังนั้น `runner.ts` / `scheduler.ts` / `cli.js` / "
            "`job-failure.notifier.ts` คือ **งานตั้งต้นของ Phase แรก** ที่ต้องสร้างเองทั้งหมด พร้อม register "
            "`ScheduleModule.forRoot()` ใน `app.module.ts` — ไม่ใช่ของเดิมที่ reuse ได้"
        ),
        table(["Path", "หน้าที่"], rows),
    ]


def _runner_contract_blocks(no: str, pascal: str, steps: list[dict[str, Any]], service_var: str) -> list[dict[str, Any]]:
    """สัญญาของชั้นกลางที่ job class อ้างถึง (JobRunContext/JobRunResult/JobState/JobFailedError)

    เดิม job class import 4 ตัวนี้จาก '../../runner' แต่ไม่มีเอกสารไหนนิยามให้เลย
    """
    methods: list[str] = []
    seen: set[str] = set()
    for index, step in enumerate(steps):
        kind = str(step.get("k", "p"))
        text = str(step.get("t", "")).strip()
        detail = str(step.get("d", "") or "").strip()
        order = index + 1
        if kind == "start" or kind == "end":
            continue
        if kind == "d":
            name = f"check{order:02d}{_verb(text + ' ' + detail, 'Condition')}"
            sig = f"  async {name}(state: JobState): Promise<boolean> {{"
            ret = "    return true; // TODO: เงื่อนไขจริงตามผัง"
        elif kind == "err":
            continue
        else:
            name = f"step{order:02d}{_verb(text + ' ' + detail, 'Process')}"
            sig = f"  async {name}(state: JobState, manager?: EntityManager): Promise<void> {{"
            ret = "    // TODO: implement"
        if name in seen:
            continue
        seen.add(name)
        methods += [f"  // {text}", sig, ret, "  }", ""]
    runner = "\n".join([
        "// src/batch/runner.ts — สัญญากลางของทุก job (ประกาศครั้งเดียว ใช้ร่วมทั้ง 11 ฉบับ)",
        "",
        "export interface JobRunContext {",
        "  jobNo: string;",
        "  period: string;        // YYYYMM ของงวดที่รัน",
        "  triggeredBy: string;   // 'CRON' | userId ที่สั่งรันนอกรอบ",
        "  params?: Record<string, string>;",
        "}",
        "",
        "export interface JobRunResult {",
        "  event: 'job.finish';",
        "  jobNo: string;",
        "  jobName: string;",
        "  status: 'SUCCESS' | 'SKIPPED' | 'SKIPPED_LOCKED' | 'FAILED';",
        "  period: string;",
        "  output: string;",
        "  read: number; written: number; skipped: number; rejected: number;",
        "  durationMs: number;",
        "}",
        "",
        "/** counter + ค่าที่ทุกขั้นของ job ใช้ร่วมกัน (service เป็นผู้สร้างผ่าน createState) */",
        "export interface JobState {",
        "  period: string;",
        "  read: number; written: number; skipped: number; rejected: number;",
        "  // TODO: เพิ่ม field เฉพาะของ job นี้ (เช่น rows ที่อ่านมา, path ไฟล์ที่เขียน)",
        "  [key: string]: unknown;",
        "}",
        "",
        "/** error ที่ทำให้ job จบเป็น FAILED และส่งอีเมลแจ้งผู้ดูแล */",
        "export class JobFailedError extends Error {",
        "  constructor(public readonly code: string, message: string) { super(message); }",
        "}",
        "",
        "/** ใช้ออกจาก transaction เมื่อสาขา NO บอกให้ข้ามงวด/เรคคอร์ด — runner สรุปเป็น SKIPPED ไม่ใช่ FAILED */",
        "export class JobSkippedError extends Error {}",
    ])
    service = "\n".join([
        f"// {pascal}Service — method ที่ job class เรียก (1 method ต่อ 1 ขั้นในตารางด้านบน)",
        "import { Inject, Injectable } from '@nestjs/common';",
        "import type { DataSource, EntityManager } from 'typeorm';",
        "import type { JobRunContext, JobState } from '../../runner';",
        "export type { JobState };",
        "",
        "@Injectable()",
        f"export class {pascal}Service {{",
        "  constructor(@Inject('DATA_SOURCE') private readonly dataSource: DataSource) {}",
        "",
        "  createState(ctx: JobRunContext): JobState {",
        "    return { period: ctx.period, read: 0, written: 0, skipped: 0, rejected: 0 };",
        "  }",
        "",
        *methods,
        "}",
    ])
    return [
        h(3, f"5.96.1 สัญญาของชั้นกลาง (`runner.ts`) + โครง service ของ Job {no}"),
        p("job class อ้าง `JobRunContext` / `JobRunResult` / `JobState` / `JobFailedError` — ทั้งหมดนิยาม "
          "ครั้งเดียวใน `src/batch/runner.ts` (ไฟล์ร่วมของทุก job ให้ merge ไม่ใช่เขียนทับ) และ service "
          "ต้องมี method ครบตามตารางขั้นตอนด้านล่าง มิฉะนั้น job class จะเรียก method ที่ไม่มีอยู่"),
        code(runner, "ts"),
        code(service, "ts"),
    ]


# ---------------------------------------------------------------------------
# section 2 — config schema
# ---------------------------------------------------------------------------


def _config_blocks(no: str, folder: str, base: str, pascal: str, params: list[list[Any]], job: dict[str, Any]) -> list[dict[str, Any]]:
    slug = _job_slug(no)
    keys = _dedupe([_param_key(str(row[0]), idx) for idx, row in enumerate(params, start=1)])
    iface: list[str] = ["  /** เปิด/ปิด job รอบถัดไปโดยไม่ต้อง deploy โค้ด */", "  enabled: boolean;"]
    factory: list[str] = [
        "  // TODO: ยืนยันค่า default ทุกตัวกับ Ops ก่อนขึ้น production (ไม่มีหน้าจอแก้ค่าแล้ว)",
        f"  enabled = (process.env.SBPGI_JOB{slug}_ENABLED ?? 'true') === 'true';",
        f"  cron = process.env.SBPGI_JOB{slug}_CRON ?? {_ts_string(job.get('cron', ''))};",
    ]
    iface.append("  /** cron ของ job นี้ (อ่านตอน bootstrap ของ scheduler.ts) */")
    iface.append("  cron: string;")
    for key, row in zip(keys, params[:12]):
        label = str(row[0])
        value = row[1] if len(row) > 1 else ""
        kind = str(row[2]) if len(row) > 2 else "text"
        editable = bool(row[3]) if len(row) > 3 else True
        note = str(row[4]) if len(row) > 4 else ""
        env = f"SBPGI_JOB{slug}_{_upper_snake(key)}"
        # ค่า default ที่เป็นข้อความอธิบาย (เช่น "|sales_diff| ≥ 50") ต้องเป็น string เสมอ
        ts_type = "number" if (kind == "number" and _is_number(value)) else "string"
        iface.append(f"  /** {label}{(' — ' + note) if note else ''} */")
        iface.append(f"  {key}: {ts_type};")
        comment = "แก้ผ่าน env/config file แล้ว deploy" if editable else "ค่าคงที่ทางธุรกิจ — เปลี่ยนต้องผ่านการอนุมัติ"
        if "⚠️" in note:
            # ยกคำเตือนจาก note มาไว้บนบรรทัดค่า default ด้วย ไม่ให้ dev อ่านข้ามไป
            comment = note.split("⚠️", 1)[1].strip() + " (⚠️)"
        if ts_type == "number":
            factory.append(f"  {key} = Number(process.env.{env} ?? {str(value).replace(',', '')}); // TODO: {comment}")
        else:
            factory.append(f"  {key} = process.env.{env} ?? {_ts_string(value)}; // TODO: {comment}")
    factory.append(
        f"  mailTo = process.env.SBPGI_JOB{slug}_MAIL_TO ?? ''; "
        f"// TODO: ผู้รับอีเมลแจ้ง error คั่นด้วย comma (เดิม: {job.get('meta', {}).get('mail', '-')})"
    )
    iface.append("  /** ผู้รับอีเมลเมื่อ job ล้มเหลว — เก็บเป็น string คั่น comma ให้ตรง signature ของ")
    iface.append("      `EmailLibService.sendMail({ mailTo })` ที่รับ string ไม่ใช่ string[] */")
    iface.append("  mailTo: string;")

    text = "\n".join([
        f"// {'src/batch/sbpgi/' + folder + '/' + base + '.config.ts'}",
        "// convention จริงของ store-backend คือคลาส config (`src/config/app.config.ts` ที่ export ผ่าน",
        "// `AppConfigModule` แบบ @Global แล้วอ่าน process.env ตรง ๆ) — โปรเจกต์นี้ **ไม่ได้ใช้ registerAs**",
        "// แม้แต่จุดเดียว จึงประกาศเป็นคลาสให้รีวิว/ทดสอบเหมือน config ตัวอื่น",
        "import { Injectable } from '@nestjs/common';",
        "",
        f"// TODO: Job {no} ไม่มีตาราง job_configs และไม่มี Job Admin API แล้ว (ตัดสินใจ 2026-08-06)",
        "// TODO: ค่าทุกตัวอ่านจาก env/config file ของ backend เท่านั้น — เปลี่ยนค่า = แก้ config แล้ว deploy",
        f"export interface Job{slug}Config {{",
        *iface,
        "}",
        "",
        "@Injectable()",
        f"export class SbpgiJob{slug}Config implements Job{slug}Config {{",
        *factory,
        "}",
        "",
        f"// TODO: เพิ่ม SbpgiJob{slug}Config ใน providers/exports ของ AppConfigModule (@Global) เหมือน AppConfig",
    ])
    return [
        h(2, f"5.95 Config Schema ของ Job {no} (backend config / env)"),
        p(
            f"cron ปัจจุบันของ Job {no} คือ `{job.get('cron', '-')}` ({job.get('cronTh', '-')}) — "
            f"ประกาศเป็น `SBPGI_JOB{slug}_CRON` และอ่านตอน bootstrap ของ `scheduler.ts`; "
            "ถ้า `enabled=false` scheduler ต้องไม่ลงทะเบียน cron ของ job นี้"
        ),
        code(text, "ts"),
    ]


# ---------------------------------------------------------------------------
# section 3 — job class
# ---------------------------------------------------------------------------


def _step_map_rows(steps: list[dict[str, Any]], service_var: str) -> tuple[list[list[Any]], list[tuple[int, str]]]:
    """คืน (rows ของตาราง step map, บรรทัดโค้ดของ run() พร้อมระดับ indent)"""
    kind_label = {
        "start": "start", "end": "end", "p": "process",
        "io": "io", "d": "decision", "err": "error",
    }
    rows: list[list[Any]] = []
    body: list[tuple[int, str]] = []
    write_indexes = [i for i, s in enumerate(steps) if _is_write_step(s)]
    tx_start = min(write_indexes) if write_indexes else -1
    tx_end = max(write_indexes) if write_indexes else -2

    for index, step in enumerate(steps):
        kind = str(step.get("k", "p"))
        text = _table_note(str(step.get("t", "")).strip())
        detail = _table_note(str(step.get("d", "") or "").strip())
        no_branch = str(step.get("no", "") or "").strip()
        no_kind = str(step.get("noKind", "") or "").strip()
        job_no = str(step.get("jobNo", "")) or "X"
        order = index + 1
        indent = 4 if tx_start <= index <= tx_end else 3
        if kind == "start":
            rows.append([order, kind_label.get(kind, kind), text, "createState()", "-"])
            continue
        if kind == "end":
            rows.append([order, kind_label.get(kind, kind), text, "summarize()", "-"])
            continue
        if kind == "d":
            method = f"check{order:02d}{_verb(text + ' ' + detail, 'Condition')}"
            fail = no_branch or "ไม่ผ่าน → บันทึก skip"
            # ผัง (job-batch.html) ให้ความหมายของเส้น NO มาเท่าที่ `noKind` ระบุเท่านั้น:
            #   err = ล้มทั้ง job · end = จบทั้ง job · ว่าง = branch ระดับ record ที่ตีความเองไม่ได้
            # จึงห้ามเดาว่าเป็น "skip" ทุกกรณี (เดิมนับ skipped แล้วไหลต่อไปทำขั้นถัดไป ซึ่งผิดทั้งสองทาง)
            branch_kind = no_kind or "branch"
            rows.append([order, kind_label.get(kind, kind), text, f"{method}()", f"[{branch_kind}] {fail}"])
            body.append((indent, f"// ขั้นที่ {order} (decision): {text}" + (f" · TODO: {detail}" if detail else "")))
            body.append((indent, f"const ok{order:02d} = await this.{service_var}.{method}(state);"))
            if no_kind == "err":
                body.append((
                    indent,
                    f"if (!ok{order:02d}) throw new JobFailedError('JOB{_job_slug(job_no)}_STEP{order:02d}', "
                    f"{_ts_string(fail)});",
                ))
            elif no_kind == "end":
                # NO = จบทั้ง job ตามผัง — ต้องออกทันที ห้ามไหลไปทำขั้นถัดไป
                # (NOTE: ค่า indent ของ tuple ต้องคงเป็น 3/4 เพราะใช้เป็นสัญญาณขอบเขต transaction
                #  การเยื้องภายในบล็อกจึงใส่เป็นช่องว่างนำหน้าใน string แทน)
                body.append((indent, f"if (!ok{order:02d}) {{ // NO → {fail}"))
                if indent >= 4:
                    body.append((indent, "  throw new JobSkippedError('NO branch'); // ใน transaction: โยนออกเพื่อ rollback"))
                    body.append((indent, "  // runner จับ JobSkippedError แล้วสรุปเป็น SKIPPED (ไม่ใช่ FAILED)"))
                else:
                    body.append((indent, "  return this.summarize(state, 'SKIPPED', startedAt);"))
                body.append((indent, "}"))
            else:
                body.append((indent, f"if (!ok{order:02d}) {{ // NO → {fail}"))
                body.append((indent, "  // TODO: เส้น NO ของขั้นนี้เป็น branch ระดับ record — ผังไม่ได้ระบุว่าหยุดหรือไปต่อ"))
                body.append((indent, "  //   ถ้าเป็น 'ข้ามรายการ'      -> state.skipped += 1; แล้ว continue ในลูปของ record"))
                body.append((indent, "  //   ถ้าเป็น 'ตั้งค่าแล้วไปต่อ' -> เรียก service ตั้งค่าสถานะ แล้วเดินขั้นถัดไป (ห้าม return)"))
                body.append((indent, "  //   ถ้าเป็น 'คงสถานะเดิม/ไม่เปิดงาน' -> หยุดเฉพาะ record นี้ ห้ามไหลไปขั้นถัดไป"))
                body.append((indent, "}"))
            continue
        if kind == "err":
            method = f"step{order:02d}{_verb(text + ' ' + detail, 'Recover')}"
            rows.append([order, kind_label.get(kind, kind), text, f"{method}()", "รันใน catch block ของ run()"])
            body.append((indent, f"// ขั้นที่ {order} (error path — ดู catch ท้าย run()): {text}"))
            continue
        method = f"step{order:02d}{_verb(text + ' ' + detail, 'Process')}"
        rows.append([
            order,
            kind_label.get(kind, kind),
            text,
            f"{method}()",
            "throw JobFailedError เมื่อทำไม่สำเร็จ",
        ])
        body.append((indent, f"// ขั้นที่ {order}: {text}" + (f" · TODO: {detail}" if detail else "")))
        arg = "state, manager" if tx_start <= index <= tx_end else "state"
        body.append((indent, f"await this.{service_var}.{method}({arg});"))
    return rows, body


def _job_class_blocks(
    no: str, folder: str, base: str, pascal: str, steps: list[dict[str, Any]], job: dict[str, Any]
) -> list[dict[str, Any]]:
    service_var = "service"
    for step in steps:
        step["jobNo"] = no
    rows, body = _step_map_rows(steps[:14], service_var)
    write_indexes = [i for i, s in enumerate(steps[:14]) if _is_write_step(s)]
    tx_note = str(job.get("meta", {}).get("trans", "")) or "ยืนยันขอบเขต transaction กับ BA"
    slug = _job_slug(no)

    lines: list[str] = [
        f"// src/batch/sbpgi/{folder}/{base}.job.ts",
        "import { Inject, Injectable, Logger } from '@nestjs/common';",
        "import type { DataSource, EntityManager } from 'typeorm';",
        f"import {{ {pascal}Service, type JobState }} from './{base}.service';",
        "// 4 symbol นี้นิยามใน src/batch/runner.ts (ดูหัวข้อ 5.96.1)",
        "import { JobFailedError, JobSkippedError, JobRunContext, JobRunResult } from '../../runner';",
        "",
        "@Injectable()",
        f"export class {pascal}Job {{",
        f"  static readonly jobNo = '{no}';",
        f"  private readonly logger = new Logger({pascal}Job.name);",
        "",
        "  constructor(",
        "    // TODO: DATA_SOURCE = custom provider ที่ route SELECT/WITH ไป slave pool และ write ไป master",
        "    @Inject('DATA_SOURCE') private readonly dataSource: DataSource,",
        f"    private readonly {service_var}: {pascal}Service,",
        "  ) {}",
        "",
        "  async run(ctx: JobRunContext): Promise<JobRunResult> {",
        "    const startedAt = Date.now();",
        f"    // TODO: state ถือ counter (read/written/skipped/rejected) และค่าจาก job{slug}Config",
        f"    const state = this.{service_var}.createState(ctx);",
        "    try {",
    ]

    in_tx = False
    for indent, line in body:
        if indent == 4 and not in_tx:
            lines.append(f"      // === transaction boundary === TODO: {tx_note}")
            lines.append("      await this.dataSource.transaction(async (manager: EntityManager) => {")
            in_tx = True
        if indent == 3 and in_tx:
            lines.append("      });")
            in_tx = False
        lines.append(("  " * indent) + line)
    if in_tx:
        lines.append("      });")

    lines.extend([
        "      return this.summarize(state, 'SUCCESS', startedAt);",
        "    } catch (error) {",
        f"      // TODO: error path ของ Job {no} — {job.get('meta', {}).get('risk', 'ตรวจ risk ในเอกสาร')}",
        f"      this.logger.error(JSON.stringify({{ event: 'job.failed', jobNo: '{no}', period: ctx.period,",
        "        triggeredBy: ctx.triggeredBy, durationMs: Date.now() - startedAt, error: (error as Error).message }));",
        "      // TODO: แจ้งผู้ดูแลผ่าน JobFailureNotifier (หัวข้อ 5.99.1) — runner เป็นผู้เรียกให้",
        "      throw error;",
        "    }",
        "  }",
        "",
        "  private summarize(state: JobState, status: JobRunResult['status'], startedAt = Date.now()): JobRunResult {",
        "    // TODO: structured log บรรทัดเดียวจบ — ไม่มีตาราง job_run_histories แล้ว (2026-08-06)",
        "    const summary = {",
        f"      event: 'job.finish', jobNo: '{no}', jobName: '{job.get('name', pascal)}', status,",
        f"      period: state.period, output: {_ts_string(job.get('out', '-'))},",
        "      read: state.read, written: state.written, skipped: state.skipped,",
        "      rejected: state.rejected, durationMs: Date.now() - startedAt,",
        "    };",
        "    this.logger.log(JSON.stringify(summary));",
        "    return summary as JobRunResult;",
        "  }",
        "}",
    ])

    blocks: list[dict[str, Any]] = [h(2, f"5.96 Job Class — `run(ctx)` ของ Job {no} ทีละขั้นตามผัง")]
    blocks += _runner_contract_blocks(no, pascal, steps[:14], service_var)
    blocks += [
        h(3, f"5.96.2 `run(ctx)` ของ Job {no}"),
        p(
            f"ทุกขั้นใน `run()` ตรงกับ flowchart ของ Job {no} หนึ่งต่อหนึ่ง (decision และ error path รวมอยู่ด้วย) — "
            "method ที่ต้อง implement ใน service ตามตารางนี้"
        ),
        table(["ลำดับ", "ชนิด", "ขั้นตอนจากผัง", "Method ที่ต้อง implement", "เส้นทาง NO / error"], rows),
        code("\n".join(lines), "ts"),
    ]
    return blocks


# ---------------------------------------------------------------------------
# section 4 — concurrency guard
# ---------------------------------------------------------------------------


def _lock_blocks(no: str, pascal: str, job: dict[str, Any]) -> list[dict[str, Any]]:
    digits = re.sub(r"[^0-9]", "", str(no)) or "0"
    suffix = "1" if re.search(r"[a-zA-Z]", str(no)) else "0"
    lock_key = f"{digits}{suffix}"
    text = "\n".join([
        "// src/batch/runner.ts (ส่วนกันรันซ้อน)",
        "import { Inject, Injectable, Logger } from '@nestjs/common';",
        "import type { DataSource } from 'typeorm';",
        "",
        "// TODO: ห้ามใช้แถวสถานะ RUNNING ในตารางเป็นตัวกัน (ไม่มีตาราง job_run_histories แล้ว)",
        "//       ใช้ PostgreSQL advisory lock ระดับ session แทน — ปลดอัตโนมัติเมื่อ connection หลุด",
        "export const SBPGI_JOB_LOCK_CLASS_ID = 861000; // namespace ของระบบ SBPGI",
        f"export const JOB_LOCK_KEYS: Record<string, number> = {{ '{no}': {lock_key} /* TODO: เพิ่มครบทั้ง 11 job */ }};",
        "",
        "@Injectable()",
        "export class BatchRunner {",
        "  private readonly logger = new Logger(BatchRunner.name);",
        "  constructor(@Inject('DATA_SOURCE') private readonly dataSource: DataSource) {}",
        "",
        "  async runExclusive<T>(jobNo: string, fn: () => Promise<T>): Promise<T | { status: 'SKIPPED_LOCKED' }> {",
        "    // TODO: ต้องใช้ QueryRunner (connection เดียวบน master) — dataSource.query() ของโปรเจกต์นี้",
        "    //       route SQL ที่ขึ้นต้นด้วย SELECT ไป slave pool ทำให้ lock ไปตกที่ replica คนละ connection",
        "    const runner = this.dataSource.createQueryRunner('master');",
        "    await runner.connect();",
        "    const objectId = JOB_LOCK_KEYS[jobNo];",
        "    try {",
        "      const [{ locked }] = await runner.query(",
        "        'SELECT pg_try_advisory_lock($1, $2) AS locked',",
        "        [SBPGI_JOB_LOCK_CLASS_ID, objectId],",
        "      );",
        "      if (!locked) {",
        "        // TODO: รอบนี้ข้ามไปเฉย ๆ ไม่ถือเป็น error และไม่ต้องส่งอีเมล",
        "        this.logger.warn(JSON.stringify({ event: 'job.skipped.locked', jobNo }));",
        "        return { status: 'SKIPPED_LOCKED' };",
        "      }",
        "      return await fn();",
        "    } finally {",
        "      // TODO: ปลด lock ทุกกรณี แล้วคืน connection เข้า pool",
        "      await runner.query('SELECT pg_advisory_unlock($1, $2)', [SBPGI_JOB_LOCK_CLASS_ID, objectId]);",
        "      await runner.release();",
        "    }",
        "  }",
        "}",
    ])
    risk = str(job.get("meta", {}).get("risk", ""))
    note = (
        f"Job {no} มีข้อควรระวังจาก legacy: {risk}"
        if risk
        else f"Job {no} ต้องกันรันซ้อนทั้งกรณี cron ซ้อนกับ manual rerun และกรณีหลาย pod"
    )
    return [
        h(2, f"5.97 การกันรันซ้อนของ Job {no} (PostgreSQL advisory lock)"),
        p(
            f"{note} — runner ล็อกด้วย `pg_try_advisory_lock` ก่อนเริ่มขั้นแรกเสมอ "
            "และรอบที่ล็อกไม่ได้ให้จบด้วยสถานะ SKIPPED_LOCKED (ไม่ใช่ FAILED)"
        ),
        code(text, "ts"),
    ]


# ---------------------------------------------------------------------------
# section 5 — repository / SQL
# ---------------------------------------------------------------------------


def _sql_for_table(name: str, mode: str, usage: str, no: str, job: dict[str, Any]) -> list[str]:
    mode = (mode or "R").upper()
    lines = [f"-- [{mode}] {name} : {usage}"]
    if name in _REPLACED_TABLES:
        lines.append(f"-- TODO: ห้ามเขียน SQL ตรงกับตารางนี้ — {_REPLACED_TABLES[name]}")
        lines.append("")
        return lines
    if name == "interface_transactions" and mode == "R":
        lines.extend([
            "-- TODO: อ่านรายการที่ยังไม่ได้ ACK (safety net) — ยืนยันชื่อสถานะ/คอลัมน์เวลากับ database.md",
            "SELECT id, data_name, direction, status, business_key, period_key, file_name, created_at",
            "  FROM interface_transactions",
            f" WHERE data_name = ANY($1)  -- TODO: รายการ interface ที่ Job {no} เฝ้าดู (ไม่ใช่ job_no ของตัวเอง)",
            "   AND status IN ('READY', 'SENT')  -- TODO: สถานะที่ถือว่ายังไม่มี ACK",
            "   AND created_at < NOW() - ($2 || ' hours')::interval  -- TODO: threshold จาก config",
            " ORDER BY created_at;",
            "",
        ])
        return lines
    if name == "interface_transactions":
        lines.extend([
            "-- TODO: บันทึก ACK ระดับ record ของไฟล์ interface (แทน job_run_histories ที่ยกเลิกไปแล้ว)",
            "INSERT INTO interface_transactions",
            "  (run_id, data_name, direction, status, business_key, period_key,",
            "   file_name, file_checksum, created_at)",
            f"VALUES ($1 /* run_id = correlation id ของรอบรัน Job {no} จาก application log */,",
            f"        $2 /* TODO: data_name ของ Job {no} */, $3 /* IN|OUT|INTERNAL */, 'READY',",
            "        $4 /* business key ของแถว */, $5 /* YYYYMM */, $6, $7, NOW())",
            "ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;",
            "",
        ])
        return lines
    has_period = "impact" in name or name.startswith("fgi_") or name.startswith("fcs_")
    period_filter = (
        " WHERE impact_year = $1 AND impact_month = $2  -- TODO: ยืนยันชื่อคอลัมน์งวดกับ database.md"
        if has_period
        else " WHERE /* TODO: เงื่อนไขงวด/สถานะที่ job นี้คัดแถว */ 1 = 1"
    )
    if mode == "R":
        page_params = "$3 OFFSET $4" if has_period else "$1 OFFSET $2"
        lines.extend([
            "-- TODO: เติมเฉพาะคอลัมน์ที่ job ใช้จริง (ห้าม SELECT *) และตรวจว่ามี index รองรับ WHERE นี้",
            "SELECT /* TODO: columns */",
            f"  FROM {name}",
            period_filter,
            " ORDER BY /* TODO: คีย์ที่ทำให้ลำดับคงที่ */",
            f" LIMIT {page_params};  -- TODO: อ่านเป็น chunk กัน memory บวม",
            "",
        ])
        return lines
    if mode in {"R/W", "RW"}:
        lines.extend([
            "-- TODO: อ่าน candidate แบบล็อกแถว กันรอบอื่น/pod อื่นแย่งอัปเดตแถวเดียวกัน",
            "SELECT /* TODO: PK + คอลัมน์ที่ต้องใช้ */",
            f"  FROM {name}",
            period_filter,
            "   FOR UPDATE SKIP LOCKED;",
            "",
            f"UPDATE {name}",
            "   SET /* TODO: คอลัมน์สถานะ/ผลคำนวณที่ job นี้เขียน */",
            f"       updated_at = NOW(), updated_by = 'JOB{_job_slug(no)}'",
            " WHERE /* TODO: PK ที่ล็อกไว้ */ id = ANY($1);",
            "",
        ])
        return lines
    if name.startswith("("):
        # ไม่ใช่ตารางจริง (เช่น "(application log แบบ structured)" ที่มาแทน job_run_histories ที่ถูกตัด)
        lines.extend([
            f"-- {name} ไม่ใช่ตารางในฐานข้อมูล — ไม่มี SQL",
            "-- บันทึกผลการรันเป็น structured log บรรทัดเดียวจบ (jobNo · runId · period · counts · durationMs · outcome)",
            "",
        ])
        return lines
    conflict = BUSINESS_UNIQUE_KEYS.get(name)
    lines.extend([
        "-- TODO: เติมคอลัมน์ payload จริงจาก database.md",
        f"INSERT INTO {name}",
        "  (/* TODO: business key + payload + created_by, created_at */)",
        "VALUES (/* TODO: bind params ตามลำดับคอลัมน์ด้านบน */)",
        (f"ON CONFLICT ({conflict})   -- unique key จริงตาม DDL ของ {name} (ห้ามเดา)"
         if conflict else (
             "-- ⚠️ ตารางของ @srm/glb-workflow — SBPGI ห้าม INSERT/UPDATE ตรง ต้องเรียกผ่าน engine เท่านั้น\n"
             "--    (workflow_transaction ไม่มี PK และไม่มี index เลย · ข้อค้าง DP-2)\n"
             "ON CONFLICT (/* ไม่ใช้ — ลบ statement นี้ทิ้งแล้วเรียก engine แทน */)"
             if name.startswith("workflow_") else
             "-- ⚠️ ตารางนี้ไม่มี business unique key ใน DDL จริง — ON CONFLICT ใช้ไม่ได้\n"
             "--    fcs_qssi_score: ข้อค้าง DP-4 (การเพิ่ม unique index ต้อง sign-off เจ้าของ performance.service.ts)\n"
             "--    ระหว่างยังไม่ปิด: ลบงวดเดิมก่อนแล้ว INSERT ใหม่ใน transaction เดียว\n"
             "ON CONFLICT (/* ยังใช้ไม่ได้ — ดูหมายเหตุด้านบน */)"
         )),
        "DO UPDATE SET /* TODO: คอลัมน์ที่ยอมให้ทับ */",
        f"       updated_at = NOW(), updated_by = 'JOB{_job_slug(no)}';",
        "",
    ])
    return lines


def _sql_blocks(no: str, pascal: str, tables: list[list[Any]], job: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [h(2, f"5.98 Repository / SQL หลักของ Job {no}")]
    if not tables:
        blocks.append(p(f"Job {no} ไม่มีตารางที่ระบุไว้ในผัง — ให้เติม mapping ตาราง R/W ก่อนเขียน repository"))
        return blocks

    rows = [
        [
            str(row[0]),
            str(row[1]) if len(row) > 1 else "R",
            str(row[2]) if len(row) > 2 else "",
            _REPLACED_TABLES.get(str(row[0]), "เขียน SQL ตรงผ่าน DATA_SOURCE"),
        ]
        for row in tables
    ]
    blocks.append(p(
        f"repository ของ Job {no} ประกาศเป็น factory provider "
        f"(`{{provide: '{_upper_snake(_camel(_tokens(pascal)))}_REPOSITORY', useFactory: (ds) => ds.getRepository(Entity), inject: ['DATA_SOURCE']}}`) "
        "แล้วยิง raw SQL ตามแบบ module ธุรกิจอื่นของ store-backend (schema `sps_store` มาจาก search_path)"
    ))
    blocks.append(table(["ตาราง", "R/W", "การใช้งานตามผัง", "หมายเหตุ target design"], rows))

    sql_lines: list[str] = [
        f"-- Job {no} {job.get('name', pascal)} — query หลักที่ต้อง implement",
        "-- TODO: ทุก statement รันผ่าน DATA_SOURCE (SELECT ไป slave, write ไป master) และ",
        "--       write ทั้งหมดต้องอยู่ใน transaction เดียวกับที่ระบุใน 5.96",
        "",
    ]
    for row in tables[:4]:
        name = str(row[0])
        mode = str(row[1]) if len(row) > 1 else "R"
        usage = str(row[2]) if len(row) > 2 else ""
        sql_lines.extend(_sql_for_table(name, mode, usage, no, job))
    blocks.append(code("\n".join(sql_lines).rstrip(), "sql"))
    return blocks


# ---------------------------------------------------------------------------
# section 6 — notification + rerun checklist
# ---------------------------------------------------------------------------


def _notify_blocks(no: str, pascal: str, job: dict[str, Any]) -> list[dict[str, Any]]:
    slug = _job_slug(no)
    meta = job.get("meta", {}) or {}
    text = "\n".join([
        "// src/batch/job-failure.notifier.ts",
        "import { Injectable, Logger } from '@nestjs/common';",
        "// ชื่อ method ของ lib ที่ store-backend เรียกจริงคือ `sendMail` (ไม่ใช่ sendEmail) และ",
        "// `mailTo` / `mailCc` เป็น **string** คั่นด้วย comma — ดู evaluation-process.service.ts,",
        "// external-audit.service.ts, statement.service.ts, inform-evaluate.service.ts, performance.service.ts",
        "import { EmailLibService } from '@gosoft-sbp/email-lib';",
        "import type { JobRunContext } from './runner';",
        "",
        "@Injectable()",
        "export class JobFailureNotifier {",
        "  private readonly logger = new Logger(JobFailureNotifier.name);",
        "  // TODO: ใช้ lib อีเมลของระบบเดิม — template อยู่ในตาราง email_template และ log ลง email_sent อัตโนมัติ",
        "  //       (ตั้งชื่อ property ว่า mailService ตาม call site เดิมทุกที่ใน store-backend)",
        "  constructor(private readonly mailService: EmailLibService) {}",
        "",
        "  async notifyFailure(jobNo: string, ctx: JobRunContext, error: Error): Promise<void> {",
        f"    // TODO: ผู้รับของ Job {no} เดิมคือ {meta.get('mail', '-')} — ย้ายมาเป็น env SBPGI_JOB{slug}_MAIL_TO",
        f"    const recipients = (process.env.SBPGI_JOB{slug}_MAIL_TO ?? '').split(',').map((s) => s.trim()).filter(Boolean);",
        "    if (!recipients.length) {",
        "      this.logger.warn(JSON.stringify({ event: 'job.mail.skipped', jobNo, reason: 'NO_RECIPIENT' }));",
        "      return;",
        "    }",
        "    try {",
        "      await this.mailService.sendMail({",
        "        // TODO: emailId = id ของ template EM-07 (แจ้ง error batch) ในตาราง email_template",
        "        emailId: Number(process.env.SBPGI_JOB_FAIL_EMAIL_TEMPLATE_ID),",
        "        mailTo: recipients.join(','), // signature รับ string ไม่ใช่ string[]",
        "        mailCc: '',",
        "        param: {",
        f"          jobNo, jobName: {_ts_string(job.get('name', pascal))},",
        f"          jobTitle: {_ts_string(job.get('th', ''))},",
        "          period: ctx.period, triggeredBy: ctx.triggeredBy,",
        f"          output: {_ts_string(job.get('out', '-'))},",
        "          errorMessage: error.message,",
        f"          rerunNote: {_ts_string(meta.get('rerun', ''))},",
        "        },",
        "      });",
        "    } catch (mailError) {",
        "      // TODO: ส่งเมลไม่สำเร็จห้ามกลบ error เดิมของ job — log แล้วปล่อยผ่าน",
        "      this.logger.error(JSON.stringify({ event: 'job.mail.failed', jobNo, error: (mailError as Error).message }));",
        "    }",
        "  }",
        "}",
    ])

    checklist = [
        f"กติกา rerun ของ Job {no}: {meta.get('rerun', 'ยังไม่ระบุ — ต้องยืนยันกับ Ops ก่อนขึ้น production')}",
        f"ขอบเขต transaction ที่ต้องรักษาเมื่อรันซ้ำ: {meta.get('trans', 'ยังไม่ระบุ')}",
        f"ความเสี่ยงที่ต้องตรวจก่อน/หลังรันซ้ำ: {meta.get('risk', 'ยังไม่ระบุ')}",
        f"ตรวจว่ารอบก่อนหน้าไม่ได้ค้าง lock อยู่ (`SELECT * FROM pg_locks WHERE locktype = 'advisory'`) ก่อนสั่งรันนอกรอบ",
        f"สั่งรันนอกรอบผ่าน CLI/runbook เท่านั้น (ไม่มีหน้าจอและไม่มี Job Admin API): "
        f"`node dist/batch/cli.js --job={no} --period=<YYYYMM>`",
        f"หลังรันซ้ำ ตรวจ output `{job.get('out', '-')}` และ log บรรทัด `job.finish` ว่า read/written/skipped/rejected ตรงกับที่คาด",
        "ถ้ารอบก่อนล้มเหลวกลางทาง ตรวจ `interface_transactions` ของงวดนั้นว่ามีแถวค้างสถานะ READY/PENDING หรือไม่ ก่อนสั่งรันใหม่",
    ]
    return [
        h(2, f"5.99 การแจ้งเตือนและการรันซ้ำของ Job {no}"),
        h(3, "5.99.1 อีเมลแจ้งผู้ดูแลเมื่อ job ล้มเหลว"),
        p(
            "ใช้ `EmailLibService` จาก `@gosoft-sbp/email-lib` ตัวเดียวกับที่ระบบเดิมใช้ "
            "(inform-evaluate / external-audit / statement PTT) — ไม่สร้างกลไกส่งเมลใหม่"
        ),
        code(text, "ts"),
        h(3, "5.99.2 Checklist การ rerun"),
        bullets(checklist),
    ]


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def job_skeleton_blocks(topic: Any, ctx: Any = None) -> list[dict[str, Any]]:
    """สร้าง block ส่วน Skeleton Code ของเอกสาร LLDD ฝั่ง Job

    topic : dataclass Topic ของ build_lldd_documents.py
    ctx   : dict ที่มี key ``job`` (dict จาก array JOBS ใน job-batch.html) หรือ job dict ตรง ๆ
    """
    try:
        job = _job_from_ctx(ctx)
        no = _job_no(topic, job)
        name = _job_name(topic, job)
        pascal = _pascal(name)
        kebab = _kebab(name)
        folder = f"job-{str(no).lower()}-{kebab}"
        base = folder
        params = _params(topic, job)
        steps = _flow_steps(topic, job)
        tables = _tables(topic, job)

        blocks: list[dict[str, Any]] = []
        blocks.extend(_file_map_blocks(no, folder, base, pascal, job))
        blocks.extend(_config_blocks(no, folder, base, pascal, params, job))
        if steps:
            blocks.extend(_job_class_blocks(no, folder, base, pascal, steps, job))
        blocks.extend(_lock_blocks(no, pascal, job))
        blocks.extend(_sql_blocks(no, pascal, tables, job))
        blocks.extend(_notify_blocks(no, pascal, job))
        return blocks
    except Exception as error:  # pragma: no cover - generator ต้องไม่ล้มทั้งเล่ม
        return [
            h(2, "5.94 Skeleton Code"),
            p(f"ไม่สามารถสร้าง skeleton code อัตโนมัติได้ ({type(error).__name__}: {error}) — ให้เติมด้วยมือตามผังใน 5.9x"),
        ]


if __name__ == "__main__":  # pragma: no cover - smoke test เร็ว ๆ
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_lldd_documents import be_job_topics, load_batch_jobs  # type: ignore

    for topic, job in zip(be_job_topics(), load_batch_jobs()):
        blocks = job_skeleton_blocks(topic, {"job": job})
        print(topic.file, "->", len(blocks), "blocks")
        json.dumps(blocks, ensure_ascii=False)
