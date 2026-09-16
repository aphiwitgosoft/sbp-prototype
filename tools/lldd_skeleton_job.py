"""Skeleton-code block generator สำหรับเอกสาร LLDD ฝั่ง Batch Job (Job 1–10 + 8b).

entry point: ``job_skeleton_blocks(topic, ctx) -> list[dict]``

ผลิต block ส่วน "Skeleton Code" ที่ data-driven จาก job dict ใน ``JOBS``
(``job-batch.html``) ที่ generator อ่านมาให้แล้วผ่าน ``ctx["job"]`` — flow / tables /
params / meta ของแต่ละ job ทำให้ skeleton ของแต่ละฉบับต่างกันจริง

convention ที่ยึด (ตัดสินใจ 2026-08-06):
  * ไม่มีตาราง ``job_configs`` / ``job_run_histories`` และไม่มี Job Admin API
    → cron/พารามิเตอร์อยู่ใน backend config (env/config file), ผลการรันเขียน
      application log แบบ structured + ``sgi_interface_transactions``
  * runner กันรันซ้อนด้วย PostgreSQL advisory lock (ไม่ใช่แถว RUNNING ในตาราง)
  * job error → ส่งอีเมลผ่าน ``@gosoft-sbp/email-lib`` ของระบบเดิม
  * ไฟล์ interface ยังใช้กลไกเดิม (fixed-width + encoding เดิม)
  * โครง NestJS ตาม ``srm-sps-spsap-sop-sgi-batch``: ``@Inject('DATA_SOURCE')`` (token เดียวกับที่
    repo จริงใช้ใน entity provider ``inject: ["DATA_SOURCE"]`` และที่ store-backend ใช้ในทุก service —
    **ไม่ใช่ decorator ``InjectDataSource`` ของ @nestjs/typeorm ซึ่งไม่มีใน repo ทั้งสองตัว** · แก้ 2026-09-04),
    repository provider แบบ factory token string, entity ใน ``src/entitys/``,
    workflow ผ่าน ``@srm/glb-workflow``

ห้าม import จาก build_lldd_documents.py (กัน circular import) — helper ประกาศเองด้านล่าง
"""

from __future__ import annotations

import io
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# block helpers (รูปแบบเดียวกับ build_lldd_documents.py)
# ---------------------------------------------------------------------------



# unique key เชิงธุรกิจของแต่ละตาราง — คัดจาก CONSTRAINT ใน DDL (tools/build_lldd_documents.py)
# ใช้เติม ON CONFLICT ใน skeleton ให้ตรงของจริง แทนที่จะปล่อยเป็น TODO ให้ dev เดา
BUSINESS_UNIQUE_KEYS: dict[str, str] = {
    "sgi_fgi_impact_stores": "impacted_store_code, new_store_code, impact_month",
    "sgi_fgi_impact_competitors": "impact_process_id, competitor_store_code, period_key",
    "sgi_fgi_impact_processes": "impacted_store_code, impact_month",
    "sgi_sales_transactions": "sales_summary_id, txn_date, window_no",
    "sgi_document_competitors": "doc_no, competitor_store_code",
    "sgi_document_new_stores": "doc_no, new_store_code",
    "sgi_compensation_documents": "source, impacted_store_code, impact_month, new_store_code, round_no",
    "sgi_interface_transactions": "data_name, direction, business_key, period_key",
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
    if lang == "sql":
        import build_lldd_documents as _BA   # import ตอนเรียก (โมดูลนั้น import ไฟล์นี้ตอนโหลด)
        text = _BA.to_positional_sql(text)
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



def _canonical_job_name(no: str) -> str:
    """ชื่อ job ที่ลงทะเบียนจริง — อ่านจาก JOB_RUN_CONTRACT ของ build_lldd_documents (แหล่งเดียว)"""
    try:
        from build_lldd_documents import JOB_RUN_CONTRACT  # type: ignore
        return str((JOB_RUN_CONTRACT.get(str(no)) or {}).get("job", "") or "")
    except Exception:
        return ""


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
    (("publish", "Publish", "MQ"), "Publish"),
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

# sentinel ที่ใช้บอกว่า "ลูปของ record เริ่มตรงนี้" — แทรกก่อนขั้นแรกที่มี branch ระดับ record
_LOOP_MARK = "@@RECORD_LOOP_START@@"

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
    # tx:0 = ขั้นที่ตั้งใจให้อยู่ "นอก" DB transaction (เช่น publish MQ ของ Job 6)
    # — ต้องกันออกจาก write_indexes ไม่งั้นขอบเขต transaction จะลากคลุมไปด้วย
    if step.get("tx") == 0:
        return False
    text = f"{step.get('t', '')} {step.get('d', '')}"
    if step.get("k") not in {"p", "io"}:
        return False
    # ขั้นที่ "ตั้งค่าคอลัมน์สถานะ" ก็เป็น write แม้ข้อความจะไม่มีคำว่า update/บันทึก
    # (เจอจริง 2026-09-09 ที่ Job 2: ขั้นเติมข้อมูล master และขั้นตั้ง verify_status = P
    #  หลุดออกนอกขอบเขต transaction ทั้งคู่ เหลือแค่ขั้น insert อยู่ข้างใน)
    if re.search(r"\w+_status\s*=", text) or "เติมข้อมูล" in text or "enrich" in text.lower():
        return True
    return any(hint in text for hint in _WRITE_HINTS)


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
    "job_run_histories": "ยกเลิกแล้ว — ผลการรันเขียน application log แบบ structured + sgi_interface_transactions",
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
    """ผังไฟล์บน SBP/srm-sps-spsap-sop-sgi-batch (มติ 2026-09-02 — ย้ายมาจาก store-backend)

    repo นี้วาง module เป็น src/modules/<กลุ่ม>/<งาน>.service.ts + <กลุ่ม>.module.ts
    และ dispatch job ด้วย switch ใน src/main.ts — ไม่มี runner/scheduler แยก
    """
    # ชื่อที่ลงทะเบียนใน src/main.ts ต้องเป็น "ชื่อเดียว" กับหัวข้อ 5.95 ของเอกสารฉบับเดียวกัน
    # (เจอจริง 2026-09-09: หัวข้อ 5.95 เขียน sgi-import-impact-store แต่ skeleton สร้าง
    #  sgi-job-2-import-impact-store จากชื่อโฟลเดอร์ -> ลงทะเบียนผิดชื่อแล้ว dispatcher หา job ไม่เจอ)
    job_name = _canonical_job_name(no) or f"sgi-{folder}"
    root = "src/modules/sgi"
    rows = [
        [
            f"{root}/{base}.service.ts",
            f"คลาส `{pascal}Service` — **`execute(input)` เป็น entry point เดียว** เรียงตาม flow ของ Job {no} ทีละขั้น "
            "ครอบ transaction เอง และจบด้วย structured log สรุป metrics (แบบเดียวกับ `ImportQssiService.execute(body)` ที่มีอยู่)",
        ],
        [
            f"{root}/{base}.service.spec.ts",
            "unit test ของ service — repo นี้วาง spec ไว้ข้างไฟล์จริงเสมอ (`jest` + `npm run test:ci` มี coverage/SonarQube)",
        ],
        [
            f"{root}/dto/{base}-input.dto.ts",
            f"DTO ของ `INPUT` (JSON) พร้อม `class-validator` ตามตารางในหัวข้อ 5.95 — parse ไม่ผ่านต้อง fail ก่อนแตะ DB",
        ],
        [
            f"{root}/sgi.module.ts",
            "NestJS module ของกลุ่มงานประกันรายได้ — ผูก service ทุกตัวของ SGI เข้ากับ `TypeOrmModule` (ไฟล์ร่วมของทุก job ให้ merge ไม่ใช่เขียนทับ)",
        ],
        [
            "src/main.ts",
            f"**เพิ่ม `case '{job_name}':`** ในสวิตช์เดิม → `await import('./modules/sgi/{base}.service')` แล้ว `app.get({pascal}Service).execute(input)` "
            "(ไฟล์กลางของทุก job — เป็นจุด merge conflict ที่ต้องระวัง)",
        ],
        [
            "src/entities/sgi-*.entity.ts",
            "entity ของตาราง `sgi_*` ที่หัวข้อ Reference DB Mapping อ้างถึง — **ยังไม่มีใน repo เลยสักตัว** ต้องสร้างใหม่ทั้งหมด",
        ],
        [
            "src/config/config.ts",
            f"เพิ่ม `export const sgiJob{_job_slug(no)}Config` ตามแบบของไฟล์นี้ (โปรเจกต์ไม่ใช้ `registerAs`) — ค่าคงที่ทางธุรกิจของ Job {no}",
        ],
    ]
    return [
        h(2, f"5.94 ผังไฟล์ที่ต้องสร้าง (Job {no}) — บน `srm-sps-spsap-sop-sgi-batch`"),
        p(
            f"โครงไฟล์ของ Job {no} ({job.get('cls', '-')} เดิม) วางใต้ `src/modules/sgi/` ตาม convention ที่ repo นี้ใช้อยู่จริง "
            "(ดูตัวอย่างที่ `src/modules/performance/import-qssi.service.ts`): service ถือ logic ทั้งหมด, inject `DataSource`/repository "
            "ผ่าน TypeORM, ยิง raw SQL ได้ตรง, และ **ไม่มี controller** เพราะ repo นี้ไม่เปิด HTTP"
        ),
        p(
            "**สิ่งที่ reuse ได้ทันที ไม่ต้องเขียนใหม่** — ต่างจากแผนเดิมที่ตั้งไว้บน store-backend ซึ่งต้องสร้าง runner ทั้งชุดเอง: "
            "`src/main.ts` (dispatcher + `BATCH_START`/`BATCH_END` + `runId` + log ลง `integration_log` อัตโนมัติ) · "
            "`src/modules/rabbitMQ/rabbitmq.service.ts` (`publishMessage`) · `src/shared/services/s3.service.ts` · "
            "`StatementService.decodeThaiFileContent()` (WINDOWS-874 auto-detect) · `@gosoft-sbp/email-lib` · `@srm/glb-log`"
        ),
        p(
            "⚠️ **สิ่งที่ repo นี้ยังไม่มี และเป็นงานตั้งต้นจริง**: (1) ไม่มี `@Cron` เลย — ตารางเวลาต้องตั้งเป็น **AWS Batch scheduled event** "
            "(2) ไม่มี distributed lock (`pg_try_advisory_lock`) — การกันรันซ้อนพึ่ง AWS Batch queue ถ้างานไหนรับความเสี่ยงนี้ไม่ได้ต้องเพิ่มเอง "
            "(3) `publishMessage` เป็น fire-and-forget **ไม่มี publisher confirm และไม่มี outbox** — งานที่ต้องการ **transactional outbox + publisher confirm** (Job 6 · และ `sgi_reflow` ฝั่ง BE) ต้องสร้างกลไกเพิ่มเอง ไม่ใช่ reuse ได้เลย · ⚠️ ไม่มี ACK ระดับธุรกิจให้รอ (มติ 2026-09-08 ข้อ 2.13) "

            "(4) ยังไม่มี entity/ตาราง `sgi_*` แม้แต่ตัวเดียว"
        ),
        table(["Path", "หน้าที่"], rows),
        h(3, f"การลงทะเบียนใน `src/main.ts` (job `{job_name}`)"),
        code(
            f"""// src/main.ts — เพิ่มเคสนี้ในสวิตช์เดิม (เรียงต่อจาก job ของ SGI ตัวก่อนหน้า)
      case '{job_name}': {{
        const {{ {pascal}Service }} = await import('./modules/sgi/{base}.service');
        const {base.replace('-', '')}Service = app.get({pascal}Service);
        await {base.replace('-', '')}Service.execute(input);   // input = JSON ที่ parse จาก INPUT/argv[2] แล้ว
        break;
      }}""",
            "js",
        ),
        p(
            f"`main.ts` เรียก `StatementService.logInterfest('{job_name}', input)` ให้อยู่แล้วก่อนเข้าสวิตช์ "
            "→ **ไม่ต้องเขียน log ลง `integration_log` เองซ้ำ** · และ `BATCH_END` ที่ท้ายไฟล์จะสรุป `batchStatus` + `durationMs` ให้อัตโนมัติ "
            "หน้าที่ของ service คือ throw เมื่อทำงานไม่สำเร็จเท่านั้น"
        ),
    ]


def _decision_rule_hint(no: str, text: str) -> list[str]:
    """ดึงเงื่อนไขจริงของ job นั้นจากหัวข้อ 5.96 มาแปะไว้เหนือ method ที่ต้องเขียน

    เพิ่ม 2026-09-07: เดิม method ตัดสินใจมีแต่ `// TODO: เงื่อนไขจริงตามผัง` ทั้งที่เอกสาร
    ฉบับเดียวกันมีตารางเงื่อนไขอยู่แล้ว — dev ต้องเลื่อนหาเอง จึงยกมาไว้ตรงจุดที่ต้องใช้
    """
    try:
        import build_lldd_documents as _BA
        rules = (_BA.JOB_DECISION_RULES.get(str(no)) or {}).get("rules") or []
    except Exception:  # pragma: no cover
        return []
    if not rules:
        return ["เงื่อนไขจริง: ดูหัวข้อ \"เงื่อนไขตัดสิน (Decision Rules)\" ของเอกสารฉบับนี้"]
    words = {w for w in re.split(r"[\s·/()]+", text) if len(w) > 3}
    best, score = None, 0
    for row in rules:
        cand = {w for w in re.split(r"[\s·/()]+", str(row[0])) if len(w) > 3}
        hit = len(words & cand)
        if hit > score:
            best, score = row, hit
    if not best:
        return ["เงื่อนไขจริง: ดูตารางในหัวข้อ \"เงื่อนไขตัดสิน (Decision Rules)\" ของเอกสารฉบับนี้"]
    clean = lambda t: " ".join(re.sub(r"\*\*|`", "", str(t)).split())
    return [
        f"เงื่อนไขจริง (จากหัวข้อเงื่อนไขตัดสิน): {clean(best[0])}",
        f"  ตัดสินจาก: {clean(best[1])}",
        f"  ผ่านเมื่อ: {clean(best[2])}",
        f"  ไม่ผ่านแล้วทำอะไร: {clean(best[3])}" if len(best) > 3 else "",
    ][:4]


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
            # 🔴 ห้ามคืน true ทิ้งไว้ (แก้ 2026-09-07) — stub ที่ "ผ่านเสมอ" คือ stub ที่ deploy ขึ้น prod
            #    ได้โดยไม่มีใครรู้ · ให้ throw เพื่อให้ล้มดังตั้งแต่รอบรันแรก แล้วแนบเงื่อนไขจริงจาก 5.96 ไว้ให้
            ret = (f"    throw new Error('{name}: ยังไม่ได้ implement — "
                   f"ห้าม deploy ทั้งที่ยังไม่เขียนเงื่อนไขจริง');")
        elif kind == "err":
            continue
        else:
            name = f"step{order:02d}{_verb(text + ' ' + detail, 'Process')}"
            sig = f"  async {name}(state: JobState, manager?: EntityManager): Promise<void> {{"
            # ขั้นที่ไม่ทำอะไรเลยแต่ job รายงานว่าสำเร็จ = ข้อมูลหายเงียบ ๆ · ให้ throw เหมือนกัน
            ret = (f"    throw new Error('{name}: ยังไม่ได้ implement — "
                   f"ดู SQL ที่หัวข้อ Repository / SQL และกติกาที่หัวข้อเงื่อนไขตัดสิน');")
        if name in seen:
            continue
        seen.add(name)
        head = [f"  // {text}"]
        if kind == "d":
            head += [f"  //   {line}" for line in _decision_rule_hint(no, text + " " + detail)]
        methods += head + [sig, ret, "  }", ""]
    runner = "\n".join([
        "// src/modules/sgi/sgi-job.types.ts — สัญญากลางของทุก job ของ SGI (ประกาศครั้งเดียว ใช้ร่วมทั้ง 10 ฉบับ)",
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
        p("service อ้าง `JobRunContext` / `JobRunResult` / `JobState` / `JobFailedError` — ทั้งหมดนิยาม "
          "ครั้งเดียวใน `src/modules/sgi/sgi-job.types.ts` (ไฟล์ร่วมของทุก job ให้ merge ไม่ใช่เขียนทับ) และ service "
          "ต้องมี method ครบตามตารางขั้นตอนด้านล่าง มิฉะนั้น `execute(input)` จะเรียก method ที่ไม่มีอยู่"),
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
    # job ที่ถูกกระตุ้นด้วยข้อความ (consumer SubmitJob) **ต้องไม่มีฟิลด์ cron เลย**
    # ไม่งั้นจะมีคนเอาไปตั้ง schedule แล้วรันซ้อนกับ consumer (เจอจริง 2026-09-09 ที่ Job 11)
    event_driven = str(job.get("cron", "")).strip().lower() == "event-driven"
    factory: list[str] = [
        "  // TODO: ยืนยันค่า default ทุกตัวกับ Ops ก่อนขึ้น production (ไม่มีหน้าจอแก้ค่าแล้ว)",
        f"  enabled = (process.env.SGI_JOB{slug}_ENABLED ?? 'true') === 'true';",
    ]
    if event_driven:
        iface.append("  /** ⚠️ job นี้เป็น event-driven — **ไม่มีและต้องไม่มี** cron/schedule")
        iface.append("   *  ตัวกระตุ้นคือข้อความในคิว RabbitMQ ที่ job นี้ bind เอง (1 ข้อความ = 1 หน่วยงาน · มติ 2026-09-12)")
        iface.append("   *  ห้ามประกาศ SGI_JOB" + slug + "_CRON หรือตั้ง AWS Batch scheduled event ให้ job นี้")
        iface.append("   *  เพราะจะรันซ้อนกับ consumer แล้วประมวลผลข้อความซ้ำ */")
    else:
        factory.append(f"  cron = process.env.SGI_JOB{slug}_CRON ?? {_ts_string(job.get('cron', ''))};")
        iface.append("  /** ตารางเวลาของ job นี้ — บันทึกไว้เพื่ออ้างอิงเท่านั้น ตัวจริงตั้งที่ AWS Batch scheduled event */")
        iface.append("  cron: string;")
    # พารามิเตอร์ในผังบางตัว **ต้องไม่กลายเป็น config** (เจอจริง 2026-09-09 ที่ Job 2):
    #   - cron  : generator ประกาศให้แล้วด้านบน · ประกาศซ้ำ = duplicate property คอมไพล์ไม่ผ่าน
    #   - argument : ระบบใหม่รับ argument เป็น JSON ผ่าน INPUT (หัวข้อ 5.95) ไม่ใช่ env สตริง
    #                'ALL|2569|06' เป็นรูปแบบของระบบเดิม + เป็นปี พ.ศ. ขัดกับสัญญา input ทั้งฉบับ
    _declared = {"enabled", "cron", "mailTo"}
    for key, row in zip(keys, params[:12]):
        label = str(row[0])
        if key in _declared:
            continue
        if key == "argument" or "argument" in label.lower():
            iface.append("  /** ⚠️ ไม่มีฟิลด์นี้โดยตั้งใจ — argument ของระบบใหม่มาจาก `INPUT` (JSON) ตามหัวข้อ 5.95")
            iface.append("   *  ไม่ใช่ env สตริงแบบ `ZONES|YYYY|MM` ของระบบเดิม (และค่านั้นเป็นปี พ.ศ.)")
            iface.append("   *  ถ้าต้องการค่าตั้งต้นของงวด ให้คำนวณ \"เดือนที่แล้ว\" ตามเวลา Asia/Bangkok ในโค้ด */")
            continue
        _declared.add(key)
        value = row[1] if len(row) > 1 else ""
        kind = str(row[2]) if len(row) > 2 else "text"
        editable = bool(row[3]) if len(row) > 3 else True
        note = str(row[4]) if len(row) > 4 else ""
        env = f"SGI_JOB{slug}_{_upper_snake(key)}"
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
        f"  mailTo = process.env.SGI_JOB{slug}_MAIL_TO ?? ''; "
        f"// TODO: ผู้รับอีเมลแจ้ง error คั่นด้วย comma (เดิม: {job.get('meta', {}).get('mail', '-')})"
    )
    iface.append("  /** ผู้รับอีเมลเมื่อ job ล้มเหลว — เก็บเป็น string คั่น comma ให้ตรง signature ของ")
    iface.append("      `EmailLibService.sendMail({ mailTo })` ที่รับ string ไม่ใช่ string[] */")
    iface.append("  mailTo: string;")

    text = "\n".join([
        f"// src/config/config.ts — เพิ่มบล็อกนี้ต่อท้าย (repo ใช้ export const ไม่ใช้ registerAs)",
        "// convention จริงของ sop-sgi-batch คือ `export const` ใน `src/config/config.ts` (ไม่ใช้ registerAs · ดูของเดิมที่",
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
        f"export class SgiJob{slug}Config implements Job{slug}Config {{",
        *factory,
        "}",
        "",
        f"// TODO: เพิ่ม SgiJob{slug}Config ใน providers/exports ของ AppConfigModule (@Global) เหมือน AppConfig",
    ])
    return [
        h(2, f"5.95 Config Schema ของ Job {no} (backend config / env)"),
        p(
            (
                f"🔴 **Job {no} เป็น event-driven — ไม่มีตารางเวลา และห้ามตั้ง** · "
                f"ตัวกระตุ้นคือข้อความในคิว RabbitMQ ที่ job นี้ bind/consume เอง "
                f"(1 ข้อความ = 1 การรัน · มติ 2026-09-08 ข้อ 2.11) · "
                f"**ห้ามประกาศ `SGI_JOB{slug}_CRON` และห้ามตั้ง AWS Batch scheduled event ให้ job นี้** "
                f"เพราะจะรันซ้อนกับ consumer แล้วประมวลผลข้อความซ้ำ · "
                f"`SGI_JOB{slug}_ENABLED=false` ให้ `execute()` จบทันทีแบบ SUCCESS พร้อม log เหตุผล"
            )
            if str(job.get("cron", "")).strip().lower() == "event-driven"
            else (
                f"ตารางเวลาของ Job {no} คือ `{job.get('cron', '-')}` ({job.get('cronTh', '-')}) — "
                "⚠️ **ตัวจริงตั้งที่ AWS Batch scheduled event ไม่ใช่ในโค้ด** (repo นี้ไม่มี `@Cron` เลย) "
                f"ค่า `SGI_JOB{slug}_CRON` เก็บไว้เป็นเอกสารประกอบ/ตรวจสอบเท่านั้น · "
                f"`SGI_JOB{slug}_ENABLED=false` ให้ `execute()` จบทันทีแบบ SUCCESS พร้อม log เหตุผล "
                "(กันกรณี AWS Batch ยังยิงเข้ามา)"
            )
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
    # ขั้น reconcile/ตรวจก่อน commit ที่อยู่ "ต่อจาก" ขั้นเขียนสุดท้าย ต้องอยู่ในขอบเขต transaction ด้วย
    # (เจอจริง 2026-09-09 ที่ Job 3: reconcile อยู่นอก transaction ที่ commit ไปแล้ว
    #  ข้อความ "Rollback" ในผังจึงเป็นไปไม่ได้ — ต้องตรวจก่อน commit เท่านั้น)
    if tx_end >= 0:
        _k = tx_end + 1
        while _k < len(steps):
            _st = steps[_k]
            _t = f"{_st.get('t', '')} {_st.get('d', '')} {_st.get('no', '')}"
            if _st.get("k") == "d" and re.search(r"reconcile|rollback|ก่อน commit|จำนวนต้นทาง", _t, re.I):
                tx_end = _k
                _k += 1
                continue
            break

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
            #   err  = ล้มทั้ง job (rollback)
            #   end  = จบทั้ง job
            #   mark = ผลทางธุรกิจระดับ record — บันทึกสถานะแล้วไป record ถัดไป (ไม่ล้ม job)
            #   ว่าง = branch ระดับ record ที่ตีความเองไม่ได้
            # จึงห้ามเดาว่าเป็น "skip" ทุกกรณี (เดิมนับ skipped แล้วไหลต่อไปทำขั้นถัดไป ซึ่งผิดทั้งสองทาง)
            # ป้ายที่แสดงในตาราง — ใช้คำไทยเพื่อไม่ให้ชนกับ guard ที่มองหาคำกริยาอังกฤษ
            branch_kind = {"mark": "บันทึกผลแล้วไป record ถัดไป",
                           "err": "err", "end": "end"}.get(no_kind, no_kind or "branch")
            rows.append([order, kind_label.get(kind, kind), text, f"{method}()", f"[{branch_kind}] {fail}"])
            _pos_before_step = len(body)
            body.append((indent, f"// ขั้นที่ {order} (decision): {text}" + (f" · TODO: {detail}" if detail else "")))
            body.append((indent, f"const ok{order:02d} = await this.{service_var}.{method}(state);"))
            if no_kind == "err":
                body.append((
                    indent,
                    f"if (!ok{order:02d}) throw new JobFailedError('JOB{_job_slug(job_no)}_STEP{order:02d}', "
                    f"{_ts_string(fail)});",
                ))
            elif no_kind == "mark":
                # ลูปของ record ต้องเปิด **ก่อน** ขั้นที่ตัดสินรายแถวขั้นแรก ไม่ใช่หลัง
                if not any(l == _LOOP_MARK for _i, l in body):
                    body.insert(_pos_before_step, (indent, _LOOP_MARK))
                # NO = ผลทางธุรกิจปกติ ไม่ใช่ error — บันทึกสถานะของ record นี้แล้ว "ไป record ถัดไป"
                # ห้าม throw (จะทำให้เคสธุรกิจปกติกลายเป็น job ล้มเหลว) และห้ามไหลไปขั้นถัดไป
                body.append((indent, f"if (!ok{order:02d}) {{ // NO → {fail}"))
                body.append((indent, f"  await this.{service_var}.mark{order:02d}(state, manager);"
                                     if indent >= 4 else
                                     f"  await this.{service_var}.mark{order:02d}(state);"))
                body.append((indent, "  state.marked += 1;"))
                if indent >= 4:
                    # อยู่ใน callback ของ dataSource.transaction() — `continue` ใช้ไม่ได้ (คนละ function)
                    # ต้อง return ออกจาก callback เพื่อ **commit ผลการ mark** แล้วให้ลูปข้างนอกไป record ถัดไป
                    body.append((indent, "  return; // ออกจาก transaction แบบ commit — ผล mark ต้องถูกบันทึก"))
                else:
                    body.append((indent, "  continue; // ไป record ถัดไป — ไม่ใช่ error ของทั้ง job"))
                body.append((indent, "}"))
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
        f"// src/modules/sgi/{base}.service.ts — execute(input) เป็น entry point เดียว",
        "import { Inject, Injectable, Logger } from '@nestjs/common';",
        "import type { DataSource, EntityManager } from 'typeorm';",
        f"import {{ {pascal}Service, type JobState }} from './{base}.service';",
        "// 4 symbol นี้นิยามใน src/modules/sgi/sgi-job.types.ts (ไฟล์ร่วมของทุก job — ดูหัวข้อก่อนหน้า)",
        "import { JobFailedError, JobSkippedError, JobRunContext, JobRunResult } from '../../runner';",
        "",
        "@Injectable()",
        f"export class {pascal}Job {{",
        f"  static readonly jobNo = '{no}';",
        f"  private readonly logger = new Logger({pascal}Job.name);",
        "",
        "  constructor(",
        "    // TODO: repo นี้ตั้ง replication ใน typeorm.config.ts อยู่แล้ว — SELECT ไป slave, write ไป master อัตโนมัติ",
        "    @Inject('DATA_SOURCE') private readonly dataSource: DataSource,",
        f"    private readonly {service_var}: {pascal}Service,",
        "  ) {}",
        "",
        "  async run(ctx: JobRunContext): Promise<JobRunResult> {",
        "    const startedAt = Date.now();",
        f"    // TODO: state ถือ candidates ที่อ่านมา + counter (read/written/skipped/rejected/marked)",
        f"    //       และค่าจาก job{slug}Config — ทุก counter ต้องถูกอัปเดตจาก record จริง ไม่ใช่ค่าคงที่",
        f"    const state = this.{service_var}.createState(ctx);",
        "    try {",
    ]

    # ถ้ามี branch ระดับ record (`continue`/`return` ต่อ record) ต้องมี **ลูปครอบจริง**
    # (เจอจริง 2026-09-09 ที่ Job 2: skeleton มี `continue` แต่ไม่มี for/while เลย -> คอมไพล์ไม่ผ่าน)
    has_record_branch = any(l == _LOOP_MARK for _i, l in body)

    in_tx = False
    for indent, line in body:
        if line == _LOOP_MARK:
            lines.extend([
                "      // TODO: candidate มาจากขั้นอ่านข้อมูลด้านบน — ลูปนี้จำเป็นเพราะมี branch ระดับ record",
                "      //       (ขั้นที่ตัดสินรายแถวจะ `continue`/`return` ออกจากรอบของ record นั้น)",
                "      //       เยื้องบรรทัดในลูปให้เรียบร้อยตอนคัดลอกเข้าโปรเจกต์จริง",
                "      for (const record of state.candidates) {",
            ])
            continue
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
    if has_record_branch:
        lines.append("      }")

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
        "// src/modules/sgi/sgi-job.lock.ts (ของใหม่ — repo นี้ยังไม่มีกลไกกันรันซ้อนใด ๆ)",
        "import { Inject, Injectable, Logger } from '@nestjs/common';",
        "import type { DataSource } from 'typeorm';",
        "",
        "// TODO: ห้ามใช้แถวสถานะ RUNNING ในตารางเป็นตัวกัน (ไม่มีตาราง job_run_histories แล้ว)",
        "//       ใช้ PostgreSQL advisory lock ระดับ session แทน — ปลดอัตโนมัติเมื่อ connection หลุด",
        "export const SGI_JOB_LOCK_CLASS_ID = 861000; // namespace ของระบบ SGI",
        f"export const JOB_LOCK_KEYS: Record<string, number> = {{ '{no}': {lock_key} /* TODO: เพิ่มให้ครบทุก job */ }};",
        "",
        "@Injectable()",
        "export class BatchRunner {",
        "  private readonly logger = new Logger(BatchRunner.name);",
        "  constructor(@Inject('DATA_SOURCE') private readonly dataSource: DataSource) {}",
        "",
        "  // period = งวดที่รอบนี้ทำงาน ('YYYY-MM') — เป็นส่วนหนึ่งของคีย์ล็อก ไม่ใช่แค่หมายเลข job",
        "  // (เจอจริง 2026-09-09: ล็อกด้วย jobNo อย่างเดียว = คนละงวดก็รันพร้อมกันไม่ได้",
        "  //  ทั้งที่เอกสารระบุว่าคนละงวดต้องรันขนานกันได้ · ส่ง period = null ถ้าต้องการล็อกทั้ง job)",
        "  async runExclusive<T>(jobNo: string, period: string | null, fn: () => Promise<T>): Promise<T | { status: 'SKIPPED_LOCKED' }> {",
        "    // TODO: ต้องใช้ QueryRunner (connection เดียวบน master) — dataSource.query() ของโปรเจกต์นี้",
        "    //       route SQL ที่ขึ้นต้นด้วย SELECT ไป slave pool ทำให้ lock ไปตกที่ replica คนละ connection",
        "    const runner = this.dataSource.createQueryRunner('master');",
        "    await runner.connect();",
        "    // pg_try_advisory_lock(int4, int4) — objectId ต้องอยู่ในช่วง int4",
        "    //   ล็อกทั้ง job : objectId = JOB_LOCK_KEYS[jobNo]",
        "    //   ล็อกรายงวด  : ผสมงวดเข้าไปด้วย hashtext() แล้วบีบให้อยู่ในช่วงที่ปลอดภัย",
        "    const baseId = JOB_LOCK_KEYS[jobNo];",
        "    const objectId = period === null ? baseId",
        "      : (await runner.query('SELECT (hashtext($1) & 2147483647) % 1000000 + $2 * 1000000 AS id',",
        "                            [period, baseId]))[0].id;",
        "    try {",
        "      const [{ locked }] = await runner.query(",
        "        'SELECT pg_try_advisory_lock($1, $2) AS locked',",
        "        [SGI_JOB_LOCK_CLASS_ID, objectId],",
        "      );",
        "      if (!locked) {",
        "        // TODO: รอบนี้ข้ามไปเฉย ๆ ไม่ถือเป็น error และไม่ต้องส่งอีเมล",
        "        this.logger.warn(JSON.stringify({ event: 'job.skipped.locked', jobNo, period }));",
        "        return { status: 'SKIPPED_LOCKED' };",
        "      }",
        "      return await fn();",
        "    } finally {",
        "      // TODO: ปลด lock ทุกกรณี แล้วคืน connection เข้า pool",
        "      await runner.query('SELECT pg_advisory_unlock($1, $2)', [SGI_JOB_LOCK_CLASS_ID, objectId]);",
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
        h(2, f"5.97 การกันรันซ้อนของ Job {no} (PostgreSQL advisory lock — **ของใหม่**)"),
        p(
            f"{note} — runner ล็อกด้วย `pg_try_advisory_lock` ก่อนเริ่มขั้นแรกเสมอ "
            "และรอบที่ล็อกไม่ได้ให้จบด้วยสถานะ SKIPPED_LOCKED (ไม่ใช่ FAILED)"
        ),
        code(text, "ts"),
    ]


# ---------------------------------------------------------------------------
# section 5 — repository / SQL
# ---------------------------------------------------------------------------


# ตารางของระบบ SBP เดิมที่ SGI **อ่านอย่างเดียว** — ห้าม generate INSERT/UPDATE ให้เด็ดขาด
#   (เจอจริง 2026-09-04: Job 10 ถูก generate `INSERT INTO email_sent ...` ทั้งที่คอมเมนต์บรรทัดบน
#    เขียนไว้เองว่า "lib เขียน log ให้เอง · SGI ไม่ INSERT เอง")
EXISTING_SYSTEM_READONLY: dict[str, str] = {
    "email_template": "อ่าน template ผ่าน `@gosoft-sbp/email-lib` เท่านั้น — ระบบ SBP เดิมเป็นเจ้าของ",
    "email_sent": "**`@gosoft-sbp/email-lib` เขียนให้เอง** — SGI ห้าม INSERT/UPDATE ตารางนี้",
    "business_user": "master ผู้ใช้ของ auth-backend — อ่านอีเมล/กลุ่มเท่านั้น",
    "mas_param": "runtime = read-only · เขียนได้เฉพาะตอน seed/cutover",
    "common_code": "runtime = read-only · เขียนได้เฉพาะตอน seed/cutover",
    "common_code_type": "runtime = read-only · เขียนได้เฉพาะตอน seed/cutover",
    "mas_store": "master ร้านของระบบเดิม — อ่านอย่างเดียว",
    "store": "master ร้านของระบบเดิม — อ่านอย่างเดียว",
    "sevenshop": "master ร้านของระบบเดิม — อ่านอย่างเดียว",
    "mas_zone": "master ภาคของระบบเดิม — อ่านอย่างเดียว",
    "fcs_qssi_score": "ระบบ SBP เดิม import ให้แล้ว (23.9 ล้านแถว) — อ่านอย่างเดียว ห้ามแก้ constraint/index",
}

_DDL_COLS_CACHE: dict[str, set[str]] | None = None


def _ddl_columns() -> dict[str, set[str]]:
    """คอลัมน์จริงของแต่ละตารางจาก DDL — ใช้ตัดสินว่าตารางนั้น "มีงวด" จริงไหม"""
    global _DDL_COLS_CACHE
    if _DDL_COLS_CACHE is not None:
        return _DDL_COLS_CACHE
    out: dict[str, set[str]] = {}
    try:
        import build_lldd_documents as _BA  # import ตอนเรียก เพราะ _BA import ไฟล์นี้ตอนโหลด
        ddl = "\n\n".join(sql for _t, sql in _BA.database_ddl_sections())
        for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\(([\s\S]*?)\n\);", ddl):
            body = re.sub(r"--[^\n]*", "", m.group(2))
            cols, depth, buf = set(), 0, ""
            for ch in body:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                if ch == "," and depth == 0:
                    parts, buf = buf, ""
                    w = re.match(r"([a-z_][a-z_0-9]*)\s+\S", parts.strip())
                    if w and w.group(1).upper() not in ("CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK", "FOREIGN"):
                        cols.add(w.group(1))
                else:
                    buf += ch
            w = re.match(r"([a-z_][a-z_0-9]*)\s+\S", buf.strip())
            if w and w.group(1).upper() not in ("CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK", "FOREIGN"):
                cols.add(w.group(1))
            out[m.group(1)] = cols
    except Exception:  # pragma: no cover
        pass
    _DDL_COLS_CACHE = out
    return out


_DDL_PK_CACHE: dict[str, list[str]] | None = None


def _ddl_primary_keys() -> dict[str, list[str]]:
    """PK จริงของแต่ละตาราง — ใช้เป็น ORDER BY ที่ทำให้ลำดับคงที่ (แทน TODO เดิม)"""
    global _DDL_PK_CACHE
    if _DDL_PK_CACHE is not None:
        return _DDL_PK_CACHE
    out: dict[str, list[str]] = {}
    try:
        import build_lldd_documents as _BA
        ddl = "\n\n".join(sql for _t, sql in _BA.database_ddl_sections())
        for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\(([\s\S]*?)\n\);", ddl):
            body = re.sub(r"--[^\n]*", "", m.group(2))
            inline = re.search(r"^\s*([a-z_][a-z_0-9]*)\s+[^,\n]*PRIMARY KEY", body, re.M)
            table_level = re.search(r"PRIMARY KEY\s*\(([^)]*)\)", body)
            if inline:
                out[m.group(1)] = [inline.group(1)]
            elif table_level:
                out[m.group(1)] = [c.strip() for c in table_level.group(1).split(",")]
    except Exception:  # pragma: no cover
        pass
    _DDL_PK_CACHE = out
    return out


# คอลัมน์ที่ห้ามปรากฏในตัวอย่าง SELECT ของเอกสาร (เอกสารถูกแจกทั้งทีม)
SENSITIVE_COLUMNS: set[str] = {"password", "passwd", "secret", "token", "id_card", "citizen_id"}

# WHERE ที่ "รู้อยู่แล้ว" ของตารางระบบเดิม — ไม่ต้องปล่อยเป็น 1 = 1
#   ที่มา: FgiConstant (GM_GROUP_ID=38 · OPT_GROUP_ID=15) และ db-schema-sps_store.md
LEGACY_WHERE: dict[str, str] = {
    "business_user": "group_id IN ($1 /* GM_GROUP_ID = 38 */, $2 /* OPT_GROUP_ID = 15 */)\n"
                     "   AND email IS NOT NULL AND email <> ''",
    "email_template": "email_template_id = $1  -- เลข template มาจาก workflow_route.email_id ห้าม hardcode",
    "mas_param": "active_flag = 'Y' AND param_code = $1\n"
                 "   -- ⚠️ ตารางนี้ไม่มี PK/unique (93,763 แถว) — ต้อง LIMIT 1 เสมอ",
    "common_code": "code_type = $1 AND active_flag = 'Y'",
    "fcs_qssi_score": "category = $1 AND score_period = $2\n"
                      "   -- ⚠️ ต้องวนตรวจ **ทีละหมวด** ตาม categoryQssi = 8,9,12,1,10,16\n"
                      "   --    ห้ามใช้ category IN (...) รวบเดียว (ดูหัวข้อ SQL ตรวจความครบของ QSSI)",
    "workflow_transaction": "version_id = $1 AND current_state_id = ANY($2)\n"
                            "   -- ⚠️ ตารางนี้ไม่มี PK และไม่มี index เลย (19,327 แถว) — ประเมินต้นทุน query ก่อนใช้",
}

_LEGACY_COLS_CACHE: dict[str, list[str]] | None = None


def _legacy_columns() -> dict[str, list[str]]:
    """คอลัมน์จริงของตารางระบบเดิม อ่านจาก `SBP/db-schema-sps_store.md` (ตารางฐานจริงที่ dump ไว้)

    เพิ่ม 2026-09-04: เดิม skeleton ของตารางระบบเดิมออกมาเป็น `SELECT /* TODO: columns */`
    ทั้งที่โครงจริงมีให้อ่านอยู่แล้วในไฟล์นี้ — ไม่มีเหตุผลจะปล่อยเป็นช่องว่าง
    """
    global _LEGACY_COLS_CACHE  # noqa: PLW0603
    if _LEGACY_COLS_CACHE is not None:
        return _LEGACY_COLS_CACHE
    out: dict[str, list[str]] = {}
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "SBP", "db-schema-sps_store.md")
    try:
        text = io.open(path, encoding="utf-8").read()
    except Exception:  # pragma: no cover
        _LEGACY_COLS_CACHE = out
        return out
    for m in re.finditer(r"^#+ +`?([a-z_][a-z_0-9]*)`?[^\n]*\n([\s\S]*?)(?=\n#+ |\Z)", text, re.M):
        cols = re.findall(r"^\| *\d+ *\| *`([a-z_][a-z_0-9]*)`", m.group(2), re.M)
        if cols:
            out.setdefault(m.group(1), cols)
    _LEGACY_COLS_CACHE = out
    return out


def _column_list(name: str, limit: int = 12) -> str:
    """รายชื่อคอลัมน์จริงสำหรับ SELECT — ตัดที่ limit แล้วบอกให้ตัดต่อเองถ้าไม่ได้ใช้ครบ"""
    cols = sorted(_ddl_columns().get(name, set()))
    if not cols:
        # ชื่อที่มี schema prefix เช่น sps_store.workflow_transaction ต้องตัด prefix ก่อนค้น
        legacy = _legacy_columns().get(name) or _legacy_columns().get(name.split(".")[-1])
        # 🔴 คอลัมน์อ่อนไหวห้ามโผล่ในตัวอย่าง SELECT ของเอกสาร
        legacy = [c for c in (legacy or []) if c not in SENSITIVE_COLUMNS] or None
        if legacy:
            shown = legacy[:limit]
            return (", ".join(shown)
                    + f"   -- คอลัมน์จริงจาก SBP/db-schema-sps_store.md (ทั้งตารางมี {len(legacy)} คอลัมน์) "
                      "· ตัดที่ job นี้ไม่ได้ใช้ออก")
        return "/* TODO: ตารางของระบบเดิม — เปิด db-schema-sps_store.md แล้วเลือกเฉพาะคอลัมน์ที่ใช้ */"
    pk = _ddl_primary_keys().get(name, [])
    ordered = pk + [c for c in cols if c not in pk]
    shown = ordered[:limit]
    tail = f"   -- ตัดคอลัมน์ที่ job นี้ไม่ได้ใช้ออก (ทั้งตารางมี {len(cols)} คอลัมน์)"
    return ", ".join(shown) + tail


_DDL_REQUIRED_CACHE: dict[str, list[str]] | None = None


def _ddl_required_columns() -> dict[str, list[str]]:
    """คอลัมน์ NOT NULL ที่ไม่มี DEFAULT — INSERT ขาดตัวไหนก็พังทันที จึงต้องอยู่ในลิสต์เสมอ"""
    global _DDL_REQUIRED_CACHE
    if _DDL_REQUIRED_CACHE is not None:
        return _DDL_REQUIRED_CACHE
    out: dict[str, list[str]] = {}
    try:
        import build_lldd_documents as _BA
        ddl = "\n\n".join(sql for _t, sql in _BA.database_ddl_sections())
        for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)\s*\(([\s\S]*?)\n\);", ddl):
            body = re.sub(r"--[^\n]*", "", m.group(2))
            need: list[str] = []
            depth, buf = 0, ""
            for ch in body + ",":
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                if ch == "," and depth == 0:
                    part = " ".join(buf.split())
                    buf = ""
                    w = re.match(r"([a-z_][a-z_0-9]*)\s+(\S+)(.*)$", part)
                    if not w or w.group(1).upper() in ("CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK", "FOREIGN"):
                        continue
                    rest = w.group(3).upper()
                    if "NOT NULL" in rest and "DEFAULT" not in rest and "SERIAL" not in w.group(2).upper():
                        need.append(w.group(1))
                else:
                    buf += ch
            out[m.group(1)] = need
    except Exception:  # pragma: no cover
        pass
    _DDL_REQUIRED_CACHE = out
    return out


def _writable_columns(name: str, limit: int = 14) -> list[str]:
    """คอลัมน์ที่ job เขียนได้จริง — ตัด serial PK และคอลัมน์เวลาที่มี DEFAULT ออก

    ⚠️ คอลัมน์ NOT NULL ที่ไม่มี DEFAULT ต้องอยู่ในลิสต์เสมอ ต่อให้เกิน limit
    (ไม่งั้น INSERT ที่ generate ออกมาจะพังตอนรัน — เจอจริง 2026-09-04)
    """
    cols = sorted(_ddl_columns().get(name, set()))
    pk = _ddl_primary_keys().get(name, [])
    skip = {"id", "created_at", "updated_at"}
    required = [c for c in _ddl_required_columns().get(name, []) if c not in skip]
    head = [c for c in pk if c not in skip and c not in required]
    rest = [c for c in cols if c not in skip and c not in pk and c not in required]
    return required + head + rest[: max(0, limit - len(required) - len(head))]


def _insert_columns(name: str) -> str:
    cols = _writable_columns(name)
    return ", ".join(cols) if cols else "/* TODO: ตารางของระบบเดิม — ดู db-schema-sps_store.md */"


def _insert_values(name: str) -> str:
    cols = _writable_columns(name)
    if not cols:
        return "/* TODO: bind params */"
    return ", ".join(f"${i + 1} /* {c} */" for i, c in enumerate(cols))



# คำที่สัญญา rerun/idempotency ใช้บอกว่า "conflict แล้วต้องข้าม ไม่ทับของเดิม"
_SKIP_ON_CONFLICT = ("do nothing", "ไม่อัปเดต", "ห้ามอัปเดต", "ถูกข้าม", "ข้ามเงียบ")


def _conflict_is_skip(job: dict[str, Any]) -> bool:
    """conflict แล้วต้อง DO NOTHING หรือ DO UPDATE — ตัดสินจากสัญญา rerun ของ job เอง

    เจอจริง 2026-09-09: Job 2 ประกาศไว้ว่า "คู่เดิมถูกข้าม — รันซ้ำไม่อัปเดตของเดิม"
    แต่ SQL ที่ generate ออกมาเป็น DO UPDATE ทับทุกคอลัมน์ รวมถึง verify_status และ
    adjust_compensate_percent/adjust_compensation_amount ที่ผู้ใช้แก้ไว้ในหน้าจอ
    ผูก SQL เข้ากับสัญญาที่ประกาศไว้ตรง ๆ เพื่อให้ทั้งสองอย่างขัดกันไม่ได้อีก
    """
    if str(job.get("onConflict", "")).strip().lower() == "nothing":
        return True
    text = str((job.get("meta") or {}).get("rerun", "")).lower()
    return any(w in text for w in _SKIP_ON_CONFLICT)

def _do_update_set(name: str) -> str:
    """คอลัมน์ที่ยอมให้ทับตอน upsert = คอลัมน์ที่เขียนได้ ลบคีย์ที่ใช้ชน conflict ออก"""
    keys = {c.strip() for c in (BUSINESS_UNIQUE_KEYS.get(name) or "").split(",") if c.strip()}
    # updated_at / updated_by ถูกเติมเป็นบรรทัดสุดท้ายเสมอ — ถ้าใส่ซ้ำตรงนี้ PostgreSQL จะ error
    # 42601 "multiple assignments to same column" (เจอจริง 2026-09-09 ในทุก job ที่ตารางมี updated_by)
    keys |= {"updated_at", "updated_by"}
    cols = [c for c in _writable_columns(name, limit=20) if c not in keys]
    if not cols:
        return "/* TODO: คอลัมน์ที่ยอมให้ทับ */"
    return ", ".join(f"{c} = EXCLUDED.{c}" for c in cols) + ","



def _lock_key_where(name: str) -> str:
    """คีย์ที่ใช้ปิดท้าย UPDATE หลัง SELECT ... FOR UPDATE

    เจอจริง 2026-09-09: generator ใส่ `id = ANY($1)` ให้ทุกตาราง แต่ `sgi_impacted_stores`
    ไม่มีคอลัมน์ `id` เลย (PK คือ `store_code`) — SQL ที่ได้จึงคัดลอกไปรันไม่ได้
    """
    cols = _ddl_columns().get(name, set())
    if "id" in cols:
        return "id = ANY($1);"
    pk = [c for c in (_ddl_primary_keys().get(name) or []) if c in cols]
    if pk:
        return " AND ".join(f"{c} = ANY(${i})" for i, c in enumerate(pk, start=1)) + ";"
    return "/* TODO: ตารางนี้ไม่มีทั้ง id และ PK ใน DDL — ระบุคีย์เอง */ 1 = 0;"


def _updated_by(name: str, no: str) -> str:
    """เติม updated_by ให้เฉพาะตารางที่มีคอลัมน์นี้จริง — ไม่งั้น SQL พังตอนรัน"""
    return f", updated_by = 'JOB{_job_slug(no)}'" if "updated_by" in _ddl_columns().get(name, set()) else ""


def _order_by(name: str) -> str:
    pk = _ddl_primary_keys().get(name) or []
    if pk:
        return ", ".join(pk) + "   -- PK ทำให้ลำดับคงที่ระหว่างแบ่งหน้า"
    uniq = BUSINESS_UNIQUE_KEYS.get(name)
    if uniq:
        return uniq + "   -- business unique key (ตารางนี้ไม่มี PK คอลัมน์เดียว)"
    legacy = _legacy_columns().get(name) or _legacy_columns().get(name.split(".")[-1])
    if legacy:
        # ตารางระบบเดิมส่วนใหญ่ไม่มี PK ที่ dump ไว้ — ใช้คอลัมน์ id ตัวแรกที่เจอเป็นคีย์เรียง
        for candidate in legacy:
            if candidate.endswith("_id") or candidate == "id":
                return candidate + "   -- ตารางระบบเดิมไม่มี PK ที่ประกาศไว้ · ใช้คอลัมน์นี้ให้ลำดับคงที่"
        return legacy[0] + "   -- ตารางระบบเดิมไม่มี PK ที่ประกาศไว้ · ยืนยันคีย์เรียงกับเจ้าของระบบก่อนใช้"
    return "/* TODO: คีย์ที่ทำให้ลำดับคงที่ */"


def _bare_table(name: str) -> str:
    """ตัดคำอธิบายในวงเล็บออกจากชื่อตาราง — ป้ายกำกับอย่าง `(ระบบ SBP เดิม)` ห้ามหลุดเข้า SQL

    เจอจริง 2026-09-04: skeleton ออกมาเป็น `FROM email_template (ระบบ SBP เดิม)` ซึ่งรันไม่ได้
    """
    return str(name).split(" (")[0].strip()


def _sql_for_table(name: str, mode: str, usage: str, no: str, job: dict[str, Any]) -> list[str]:
    mode = (mode or "R").upper()
    label = str(name)
    name = _bare_table(name)
    lines = [f"-- [{mode}] {label} : {usage}"]
    if name.startswith("("):
        # ไม่ใช่ตารางจริง เช่น "(application log แบบ structured)" หรือ "(backend config)"
        # ⚠️ เดิมเช็คทีหลัง `mode == "R"` จึงไม่เคยทำงาน — skeleton ออกมาเป็น `FROM (backend config)`
        lines.extend([
            f"-- {label} ไม่ใช่ตารางในฐานข้อมูล — ไม่มี SQL",
            "-- อ่านค่าจาก config/env ตอน bootstrap · บันทึกผลการรันเป็น structured log บรรทัดเดียวจบ",
            "-- (jobNo · runId · period · counts · durationMs · outcome)",
            "",
        ])
        return lines
    if name in EXISTING_SYSTEM_READONLY and mode != "R":
        lines.append(f"-- 🔴 ห้ามเขียนตารางนี้ — {EXISTING_SYSTEM_READONLY[name]}")
        lines.append("--    ถ้าต้องบันทึกร่องรอย ให้ลงที่ `sgi_interface_transactions` หรือ structured log ของ job แทน")
        lines.append("")
        return lines
    if name in _REPLACED_TABLES:
        lines.append(f"-- TODO: ห้ามเขียน SQL ตรงกับตารางนี้ — {_REPLACED_TABLES[name]}")
        lines.append("")
        return lines
    if name == "sgi_interface_transactions" and mode == "R":
        lines.extend([
            "-- อ่านรายการขาออกที่ broker ยังไม่ publisher confirm (มติ 2026-09-08 ข้อ 2.13 — ไม่ใช่การรอ ACK จาก STA)",
            "SELECT id, data_name, direction, status, business_key, period_key, file_name, created_at",
            "  FROM sgi_interface_transactions",
            f" WHERE data_name = ANY($1)  -- TODO: รายการ interface ที่ Job {no} เฝ้าดู (ไม่ใช่ job_no ของตัวเอง)",
            "   AND (outbox_status IS NULL OR outbox_status <> 'CONFIRMED')  -- ยังไม่ได้ publisher confirm",
            "   AND created_at < NOW() - ($2 || ' hours')::interval  -- TODO: threshold จาก config",
            " ORDER BY created_at;",
            "",
        ])
        return lines
    if name == "sgi_interface_transactions":
        lines.extend([
            "-- บันทึกผลการรับส่งระดับ record ของ interface (แทน job_run_histories ที่ยกเลิกไปแล้ว)",
            "INSERT INTO sgi_interface_transactions",
            "  (run_id, data_name, direction, status, business_key, period_key,",
            "   file_name, file_checksum, created_at)",
            f"VALUES ($1 /* run_id = correlation id ของรอบรัน Job {no} จาก application log */,",
            f"        $2 /* TODO: data_name ของ Job {no} */, $3 /* IN|OUT|INTERNAL */, 'READY',",
            "        $4 /* business key ของแถว */, $5 /* YYYYMM */, $6, $7, NOW())",
            "ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;",
            "",
        ])
        return lines
    # ⚠️ เดิมเดา "มีงวด" จากชื่อตาราง (`"impact" in name`) ทำให้ sgi_impacted_stores ซึ่ง**ไม่มี**
    #    impact_year/impact_month ถูก generate WHERE ที่คอลัมน์ไม่มีจริง — ตอนนี้ดูจาก DDL จริง
    _cols = _ddl_columns().get(name, set())
    _period = [c for c in ("impact_year", "impact_month", "impact_month_key", "period_key") if c in _cols]
    has_period = len(_period) >= 1
    if has_period:
        period_filter = " WHERE " + " AND ".join(
            f"{c} = ${i + 1}" for i, c in enumerate(_period[:2])) + "  -- คอลัมน์งวดจริงของตารางนี้ตาม DDL"
    elif (name.split(".")[-1]) in LEGACY_WHERE:
        period_filter = " WHERE " + LEGACY_WHERE[name.split(".")[-1]]
    elif name in EXISTING_SYSTEM_READONLY:
        period_filter = f" WHERE /* เงื่อนไขคัดแถว — {EXISTING_SYSTEM_READONLY[name]} */ 1 = 1"
    else:
        # ⚠️ เดิมปล่อย `1 = 1` เปล่า ๆ (แก้ 2026-09-07) — ถ้าตารางมีคอลัมน์ที่ใช้คัดแถวได้จริง
        #    ให้เขียนเงื่อนไขนั้นลงไปเลย เหลือแค่ค่าที่ job ตัดสิน ไม่ใช่ให้ dev ไปหาเองว่าจะกรองด้วยอะไร
        _pk = [c for c in _ddl_primary_keys().get(name, []) if c != "id"]
        _pick = next((c for c in ("doc_no", "impact_process_id", "sales_summary_id",
                                  "impacted_store_code", "store_code", "ref_doc_no",
                                  "status_code", "accounting_status", "is_active") if c in _cols),
                     _pk[0] if _pk else None)
        if _pick == "is_active":
            period_filter = " WHERE is_active = TRUE   -- คัดเฉพาะร้านที่ยัง active (ตารางนี้ไม่มีคอลัมน์งวด)"
        elif _pick:
            period_filter = (f" WHERE {_pick} = $1"
                             f"   -- คีย์ที่ job นี้ใช้คัดแถว (ตารางนี้ไม่มีคอลัมน์งวดของตัวเอง)")
        else:
            period_filter = (f" WHERE /* ตารางนี้ไม่มีทั้งคอลัมน์งวดและคีย์คัดแถว — เลือกจาก: "
                             f"{', '.join(sorted(_cols)[:6]) or 'ดู DDL'} */ 1 = 1")
    _n_period = min(len(_period), 2) if has_period else 0
    if not has_period:
        # WHERE ของตารางระบบเดิมอาจใช้ $n ไปแล้ว — LIMIT/OFFSET ต้องต่อเลขจากตรงนั้น
        _used = re.findall(r"\$(\d+)", period_filter)
        _n_period = max((int(x) for x in _used), default=0)
    if mode == "R":
        page_params = f"${_n_period + 1} OFFSET ${_n_period + 2}"
        lines.extend([
            "-- คอลัมน์มาจาก DDL จริงของตารางนี้ (ห้าม SELECT *) · ตรวจว่ามี index รองรับ WHERE ก่อนขึ้น prod",
            f"SELECT {_column_list(name)}",
            f"  FROM {name}",
            period_filter,
            f" ORDER BY {_order_by(name)}",
            f" LIMIT {page_params};  -- อ่านเป็น chunk กัน memory บวม",
            "",
        ])
        return lines
    if mode in {"R/W", "RW"}:
        lines.extend([
            "-- อ่าน candidate แบบล็อกแถว กันรอบอื่น/pod อื่นแย่งอัปเดตแถวเดียวกัน",
            f"SELECT {_column_list(name, limit=8)}",
            f"  FROM {name}",
            period_filter,
            "   FOR UPDATE SKIP LOCKED;",
            "",
            f"UPDATE {name}",
            "   SET /* TODO: คอลัมน์สถานะ/ผลคำนวณที่ job นี้เขียน */",
            f"       updated_at = NOW(){_updated_by(name, no)}",
            f" WHERE /* คีย์ที่ล็อกไว้จาก SELECT ... FOR UPDATE ข้างบน */ {_lock_key_where(name)}",
            "",
        ])
        return lines
    conflict = BUSINESS_UNIQUE_KEYS.get(name)
    lines.extend([
        "-- คอลัมน์มาจาก DDL จริง — ตัดคอลัมน์ที่ job นี้ไม่ได้เขียนออก แล้วเลื่อนเลข $n ให้ตรง",
        f"INSERT INTO {name}",
        f"  ({_insert_columns(name)})",
        f"VALUES ({_insert_values(name)})",
        (f"ON CONFLICT ({conflict})   -- unique key จริงตาม DDL ของ {name} (ห้ามเดา)"
         if conflict else (
             "-- ⚠️ ตารางของ @srm/glb-workflow — SGI ห้าม INSERT/UPDATE ตรง ต้องเรียกผ่าน engine เท่านั้น\n"
             "--    (workflow_transaction ไม่มี PK และไม่มี index เลย — กันซ้ำที่ระดับ application ของ SGI)\n"
             "ON CONFLICT (/* ไม่ใช้ — ลบ statement นี้ทิ้งแล้วเรียก engine แทน */)"
             if name.startswith("workflow_") else
             "-- ⚠️ ตารางนี้ไม่มี business unique key ใน DDL จริง — ON CONFLICT ใช้ไม่ได้\n"
             "--    fcs_qssi_score: reuse ตารางเดิมแบบอ่านอย่างเดียว — ห้ามแก้ constraint/index ของตารางเดิม\n"
             "--    ระหว่างยังไม่ปิด: ลบงวดเดิมก่อนแล้ว INSERT ใหม่ใน transaction เดียว\n"
             "ON CONFLICT (/* ยังใช้ไม่ได้ — ดูหมายเหตุด้านบน */)"
         )),
    ])
    # สัญญา idempotency ของแต่ละ job เป็นตัวชี้ว่า conflict แล้วต้องทับหรือข้าม —
    # ถ้าสัญญาเขียนว่า DO NOTHING แล้ว SQL กลับ DO UPDATE จะทับผลที่ downstream/ผู้ใช้แก้ไว้
    # (เจอจริง 2026-09-09: Job 2 ประกาศ "ห้ามอัปเดตทับ" แต่ SQL เป็น DO UPDATE ทุกคอลัมน์)
    if conflict and _conflict_is_skip(job):
        lines.extend([
            "DO NOTHING;   -- ตามสัญญา idempotency ของ job นี้: คู่ที่มีอยู่แล้วต้องข้ามเงียบ ห้ามอัปเดตทับ",
            "-- ⚠️ DO NOTHING ไม่คืนแถว — ถ้าต้องใช้ id ต่อ ให้ SELECT ซ้ำด้วย business key",
            "",
        ])
    else:
        lines.extend([
            f"DO UPDATE SET {_do_update_set(name)}",
            f"       updated_at = NOW(){_updated_by(name, no)};",
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
        f"(`{{provide: '{_upper_snake(_camel(_tokens(pascal)))}_REPOSITORY', useFactory: (ds) => ds.getRepository(Entity), inject: [DataSource]}}`) "
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
        "// src/modules/sgi/sgi-job-failure.notifier.ts (ใช้ @gosoft-sbp/email-lib ที่ repo มีอยู่แล้ว)",
        "import { Injectable, Logger } from '@nestjs/common';",
        "// ชื่อ method ของ lib ที่ repo นี้เรียกจริงคือ `sendMail` (ไม่ใช่ sendEmail) และ",
        "// `mailTo` / `mailCc` เป็น **string** คั่นด้วย comma — ดู evaluation-process.service.ts,",
        "// external-audit.service.ts, statement.service.ts, inform-evaluate.service.ts, performance.service.ts",
        "import { EmailLibService } from '@gosoft-sbp/email-lib';",
        "import type { JobRunContext } from './runner';",
        "",
        "@Injectable()",
        "export class JobFailureNotifier {",
        "  private readonly logger = new Logger(JobFailureNotifier.name);",
        "  // TODO: ใช้ lib อีเมลของระบบเดิม — template อยู่ในตาราง email_template และ log ลง email_sent อัตโนมัติ",
        "  //       (ตั้งชื่อ property ว่า mailService ตาม call site เดิมของ sop-sgi-batch)",
        "  constructor(private readonly mailService: EmailLibService) {}",
        "",
        "  async notifyFailure(jobNo: string, ctx: JobRunContext, error: Error): Promise<void> {",
        f"    // TODO: ผู้รับของ Job {no} เดิมคือ {meta.get('mail', '-')} — ย้ายมาเป็น env SGI_JOB{slug}_MAIL_TO",
        f"    const recipients = (process.env.SGI_JOB{slug}_MAIL_TO ?? '').split(',').map((s) => s.trim()).filter(Boolean);",
        "    if (!recipients.length) {",
        "      this.logger.warn(JSON.stringify({ event: 'job.mail.skipped', jobNo, reason: 'NO_RECIPIENT' }));",
        "      return;",
        "    }",
        "    try {",
        "      await this.mailService.sendMail({",
        "        // TODO: emailId = id ของ template EM-07 (แจ้ง error batch) ในตาราง email_template",
        "        emailId: Number(process.env.SGI_JOB_FAIL_EMAIL_TEMPLATE_ID),",
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
        f"กติกา rerun ของ Job {no}: {meta.get('rerun', 'รันซ้ำได้แบบ idempotent — กันซ้ำด้วย business key ของรอบนั้น')}",
        f"ขอบเขต transaction ที่ต้องรักษาเมื่อรันซ้ำ: {meta.get('trans', 'ยังไม่ระบุ')}",
        f"ความเสี่ยงที่ต้องตรวจก่อน/หลังรันซ้ำ: {meta.get('risk', 'ยังไม่ระบุ')}",
        f"ตรวจว่ารอบก่อนหน้าไม่ได้ค้าง lock อยู่ (`SELECT * FROM pg_locks WHERE locktype = 'advisory'`) ก่อนสั่งรันนอกรอบ",
        # ⚠️ repo ปลายทาง (sop-sgi-batch) ไม่มีไฟล์ dist/batch/cli.js — dispatcher คือ dist/main.js
        #    รับ input เป็น JSON: local ใช้ env JOB_NAME/INPUT · AWS Batch ใช้ argv[3]/argv[2]
        f"สั่งรันนอกรอบผ่าน CLI/runbook เท่านั้น (ไม่มีหน้าจอและไม่มี Job Admin API) — "
        f"local: `JOB_NAME={_canonical_job_name(no) or 'sgi-<job>'} INPUT='{{\"year\":2026,\"month\":6}}' npm run start` · "
        f"AWS Batch: `node dist/main.js '{{\"year\":2026,\"month\":6}}' {_canonical_job_name(no) or 'sgi-<job>'}` "
        f"(quote เดี่ยวครอบ JSON เสมอ) · ตรวจผลด้วย `echo $?` ต้องเป็น 0 เมื่อสำเร็จ",
        f"หลังรันซ้ำ ตรวจ output `{job.get('out', '-')}` และ log บรรทัด `job.finish` ว่า read/written/skipped/rejected ตรงกับที่คาด",
        "ถ้ารอบก่อนล้มเหลวกลางทาง ตรวจ `sgi_interface_transactions` ของงวดนั้นว่ามีแถวค้างสถานะ READY/PENDING หรือไม่ ก่อนสั่งรันใหม่",
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
