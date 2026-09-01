"""Skeleton-code generator สำหรับเอกสาร LLDD ฝั่ง BE (API).

entry point: ``be_skeleton_blocks(topic, ctx)`` -> ``list[dict]``

โมดูลนี้ **ห้าม import จาก build_lldd_documents.py** (กัน circular import) จึงประกาศ
helper p/h/bullets/table/code ของตัวเองที่คืน dict รูปแบบเดียวกับ renderer

convention ที่ยึด (จาก SBP/srm-sps-spsap-store-backend.md + SBP/srm-sps-spsap-sbp-bff.md):

store-backend (NestJS 11 + TypeORM + PostgreSQL schema ``sps_store``)
  * 2 DataSource — ``TypeOrmModule.forRootAsync`` (replication) และ custom provider
    ``DATA_SOURCE`` (``src/database/database.providers.ts``) ที่ override ``query()``
    ให้ SELECT/WITH วิ่งไป slave pool · module ธุรกิจส่วนใหญ่ inject ``DATA_SOURCE`` แล้วยิง raw SQL
  * repository provider แบบ factory ใน ``src/providers/<domain>/`` ผูก token string
  * entity อยู่ ``src/entitys/`` (สะกดตามต้นฉบับ) และไม่ประกาศ relation
  * guard ระดับ controller ``HttpHeaderGuard`` (x-api-key) · ``@UserId()`` อ่าน ``request.userId``
  * ResponseInterceptor ห่อทุก response เป็น ``{success, data}``
  * workflow ใช้ ``@srm/glb-workflow`` ผ่าน ``WorkflowService`` (DataSource ชื่อ ``workflow-connection``)

BFF (NestJS ไม่มี DB)
  * ``src/modules/<feature>/`` + client service ที่ต่อจาก ``BaseClientService``
    (ตั้ง ``baseUrl``/``defaultHeaders`` ตอน ``onModuleInit``)
  * ResponseInterceptor ห่อเป็น ``{success, data, requestId}``
  * SGI รับ identity ผ่าน header ``x-api-key`` / ``x-user-id`` / ``x-user-group-id`` /
    ``x-user-permissions``
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["be_skeleton_blocks"]


# --------------------------------------------------------------------------------------
# block helpers (รูปแบบเดียวกับ renderer ใน build_lldd_documents.py บรรทัด ~137-160)
# --------------------------------------------------------------------------------------
def p(text: str) -> dict[str, Any]:
    return {"type": "p", "text": text}


def h(level: int, text: str) -> dict[str, Any]:
    return {"type": f"h{level}", "text": text}


def bullets(items: list[str]) -> dict[str, Any]:
    return {"type": "bullets", "items": list(items)}


def table(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}


def code(text: str, lang: str = "") -> dict[str, Any]:
    return {"type": "code", "text": text, "lang": lang}


# --------------------------------------------------------------------------------------
# ตารางที่ "ไม่ใช่ของ SGI" — ใช้ของระบบ SBP เดิม/workflow engine จึงไม่สร้าง entity
# (ตามการตัดสินใจ 2026-08-05 และ 2026-08-06 ใน database.md)
# --------------------------------------------------------------------------------------
REUSED_TABLES: dict[str, str] = {
    # มติ DP-9 (2026-08-10): decisions ย้ายไป common_code ของระบบเดิม (code_type = SGI_DECISION)
    "decisions": "common_code (code_type = SGI_DECISION)",
    "stores": "store / mas_store / sevenshop (store-backend)",
    "zones": "mas_zone (store-backend)",
    "branch_types": "common_code (store-backend)",
    "employees": "business_user (store-backend)",
    "email_template": "email_template + email_sent + @gosoft-sbp/email-lib",
    "email_templates": "email_template + email_sent + @gosoft-sbp/email-lib",
    "system_configs": "mas_param (store-backend)",
    "mas_param": "mas_param (store-backend)",
    "roles": "auth-backend groups",
    "menus": "auth-backend menus",
    "menu_permissions": "auth-backend permissions ต่อ URL",
    "user_accounts": "AWS Cognito + auth-backend users",
    "operator_assignments": "auth-backend group + scope (business_user_group)",
    "document_statuses": "workflow_status (@srm/glb-workflow)",
    "workflow_sections": "workflow_state (@srm/glb-workflow)",
    "workflow_instances": "workflow_transaction (@srm/glb-workflow)",
    "workflow_tasks": "workflow_approver (@srm/glb-workflow)",
}

_WORKFLOW_PREFIX = "workflow_"

# --------------------------------------------------------------------------------------
# endpoint ที่ถูกตัดออกจากดีไซน์แล้ว (api.md — ตัดสินใจ 2026-08-05/06)
# 14 เส้น RBAC/ผู้ปฏิบัติงาน ใช้ auth-backend ของระบบ SBP เดิม จึงห้าม generate controller
# --------------------------------------------------------------------------------------
CUT_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/operators", "auth-backend group + scope (จัดการที่หน้า /setting/manage-user-rights)"),
    ("/employees/search", "employee backend เดิมของระบบ SBP"),
    ("/roles", "auth-backend groups"),
    ("/menus", "auth-backend menus"),
    ("/menu-permissions", "auth-backend /groups/{id}/permissions"),
    ("/auth/", "BFF + AWS Cognito (login/refresh/profile)"),
)

# --------------------------------------------------------------------------------------
# เจ้าของ endpoint — 1 เส้น = 1 เอกสาร เพื่อไม่ให้ NestJS มี controller 2 ตัวจอง route เดียวกัน
# (เอกสารที่ไม่ใช่เจ้าของจะ generate เป็น "หมายเหตุอ้างอิง" แทน @Get/@Post ซ้ำ)
# --------------------------------------------------------------------------------------
ENDPOINT_OWNER: dict[str, str] = {
    "GET /api/v1/sgi/document/tasks": "LLDD-BE-API-Document-List-Search",
    "POST /api/v1/sgi/document/{docNo}/actions": "LLDD-BE-API-Document-Workflow-Actions",
    "GET /api/v1/sgi/document/{docNo}/timeline": "LLDD-BE-API-Document-Workflow-Actions",
}

# --------------------------------------------------------------------------------------
# ตารางที่ถูกตัดจาก target design 20 ตาราง — SQL ที่ยังอ้างถึงต้องมีคำเตือนกำกับเสมอ
# --------------------------------------------------------------------------------------
CUT_TABLE_REPLACEMENT: dict[str, str] = {
    "workflow_instances": "workflow_transaction (@srm/glb-workflow) ผ่าน getTransaction()/initializeWorkflow()",
    "workflow_tasks": "workflow_approver / workflow_history (@srm/glb-workflow) ผ่าน getPendingFlowByUser()/eventWorkflow()",
    "workflow_sections": "workflow_state / route (@srm/glb-workflow)",
    "document_statuses": "workflow_status (@srm/glb-workflow)",
    "stores": "store / mas_store / sevenshop (store-backend) หรือ sgi_impacted_stores ของ SGI",
    "zones": "mas_zone (store-backend)",
    "employees": "business_user (store-backend)",
    "system_configs": "mas_param (store-backend)",
    "email_templates": "email_template + email_sent (@gosoft-sbp/email-lib)",
    "branch_types": "common_code (store-backend)",
    "roles": "auth-backend groups",
    "menus": "auth-backend menus",
    "menu_permissions": "auth-backend permissions ต่อ URL",
    "operator_assignments": "auth-backend group + scope",
    "user_accounts": "AWS Cognito + auth-backend users",
}

# ชื่อคอลัมน์ที่ SQL ตัวอย่างเก่ายังใช้อยู่แต่ไม่ตรงกับ entity ที่ skeleton ประกาศ
CUT_COLUMN_ALIASES: dict[str, str] = {
    "total_compensation_amount": "compensate_amount",
    "d.year": "d.account_year",
    "d.month": "d.account_month",
}


def _cut_reason(path: str) -> str:
    clean = str(path or "").split(" (")[0].strip()
    if clean.startswith("/api/v1"):
        clean = clean[len("/api/v1"):] or "/"
    for prefix, reason in CUT_PREFIXES:
        if clean == prefix.rstrip("/") or clean.startswith(prefix.rstrip("/") + "/"):
            return reason
    return ""


# --------------------------------------------------------------------------------------
# คอลัมน์อ้างอิงของตาราง SGI (สรุปจาก database.md — Canonical Column Contract)
#   table -> (ClassName, [(column, tsType, columnOptions, isPk)])
# --------------------------------------------------------------------------------------
COLUMN_HINTS: dict[str, tuple[str, list[tuple[str, str, str, bool]]]] = {
    "sgi_compensation_documents": (
        "CompensationDocument",
        [
            ("doc_no", "string", "type: 'varchar', length: 12", True),
            ("impact_process_id", "number", "type: 'bigint', nullable: true", False),
            ("impacted_store_code", "string", "type: 'char', length: 5", False),
            ("status_code", "string", "type: 'varchar', length: 2", False),
            ("current_section_code", "string", "type: 'varchar', length: 2", False),
            ("round_no", "number", "type: 'int', nullable: true", False),
            ("loop_no", "number", "type: 'int', nullable: true", False),
            ("statement_id", "string", "type: 'varchar', length: 30, nullable: true", False),
            ("statement_date", "Date", "type: 'date', nullable: true", False),
            ("account_year", "number", "type: 'int', nullable: true", False),
            ("account_month", "number", "type: 'int', nullable: true", False),
            ("compensate_amount", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
            ("allmap_url", "string", "type: 'text', nullable: true", False),
            ("approver_snapshot", "Record<string, unknown>", "type: 'jsonb', nullable: true", False),
            ("created_at", "Date", "type: 'timestamptz', nullable: true", False),
            ("updated_at", "Date", "type: 'timestamptz', nullable: true", False),
        ],
    ),
    "sgi_document_new_stores": (
        "DocumentNewStore",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("new_store_code", "string", "type: 'char', length: 5", False),
            ("distance_km", "string", "type: 'numeric', precision: 6, scale: 2, nullable: true", False),
            ("compensate_percent", "string", "type: 'numeric', precision: 5, scale: 2", False),
            ("compensate_amount", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
            ("open_date", "Date", "type: 'date', nullable: true", False),
        ],
    ),
    "sgi_document_competitors": (
        "DocumentCompetitor",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("competitor_code", "string", "type: 'varchar', length: 20", False),
            ("branch_name", "string", "type: 'varchar', length: 200, nullable: true", False),
            ("zone_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("subzone_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("open_date", "Date", "type: 'date', nullable: true", False),
            ("close_date", "Date", "type: 'date', nullable: true", False),
            ("source_system", "string", "type: 'varchar', length: 10", False),
        ],
    ),
    "sgi_document_external_factors": (
        "DocumentExternalFactor",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("factor_code", "string", "type: 'varchar', length: 20", False),
            ("start_date", "Date", "type: 'date', nullable: true", False),
            ("end_date", "Date", "type: 'date', nullable: true", False),
            ("remark", "string", "type: 'text', nullable: true", False),
        ],
    ),
    "sgi_document_attachments": (
        "DocumentAttachment",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("section_code", "string", "type: 'varchar', length: 2", False),
            ("file_name", "string", "type: 'varchar', length: 255", False),
            ("file_path", "string", "type: 'varchar', length: 1000", False),
            ("file_size", "number", "type: 'int'", False),
            ("content_type", "string", "type: 'varchar', length: 100, nullable: true", False),
            ("upload_status", "string", "type: 'varchar', length: 1, nullable: true", False),
            ("upload_message", "string", "type: 'varchar', length: 500, nullable: true", False),
            ("purge_flag", "string", "type: 'char', length: 1, nullable: true", False),
            ("uploaded_by", "string", "type: 'varchar', length: 50", False),
            ("uploaded_at", "Date", "type: 'timestamptz'", False),
        ],
    ),
    "sgi_consideration_logs": (
        "ConsiderationLog",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("section_code", "string", "type: 'varchar', length: 2", False),
            ("decision_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("result", "string", "type: 'varchar', length: 200", False),
            ("result_category", "string", "type: 'varchar', length: 10", False),
            ("detail", "string", "type: 'text', nullable: true", False),
            ("consider_by", "string", "type: 'varchar', length: 50", False),
            ("action_datetime", "Date", "type: 'timestamptz'", False),
        ],
    ),
    "sgi_compensation_histories": (
        "CompensationHistory",
        [
            ("id", "number", "type: 'bigint'", True),
            ("store_code", "string", "type: 'char', length: 5", False),
            ("ref_doc_no", "string", "type: 'varchar', length: 12, nullable: true", False),
            ("compensate_year", "number", "type: 'int'", False),
            ("compensate_month", "number", "type: 'int'", False),
            ("compensate_amount", "string", "type: 'numeric', precision: 15, scale: 2", False),
            ("submit_account_month", "string", "type: 'varchar', length: 7, nullable: true", False),
            ("submit_status", "string", "type: 'char', length: 1, nullable: true", False),
        ],
    ),
    "sgi_fgi_impact_processes": (
        "FgiImpactProcess",
        [
            ("id", "number", "type: 'bigint'", True),
            ("impacted_store_code", "string", "type: 'char', length: 5", False),
            ("period_year", "number", "type: 'int'", False),
            ("period_month", "number", "type: 'int'", False),
            ("action_status", "string", "type: 'char', length: 1", False),
            ("workflow_generation_status", "string", "type: 'char', length: 1", False),
            ("last_compensation_amount", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
            ("created_at", "Date", "type: 'timestamptz', nullable: true", False),
        ],
    ),
    "sgi_fgi_impact_stores": (
        "FgiImpactStore",
        [
            ("id", "number", "type: 'bigint'", True),
            ("impact_process_id", "number", "type: 'bigint'", False),
            ("impacted_store_code", "string", "type: 'char', length: 5", False),
            ("new_store_code", "string", "type: 'char', length: 5", False),
            ("verify_status", "string", "type: 'char', length: 1", False),
            ("compensate_percent", "string", "type: 'numeric', precision: 5, scale: 2, nullable: true", False),
            ("period_year", "number", "type: 'int'", False),
            ("period_month", "number", "type: 'int'", False),
        ],
    ),
    "sgi_fgi_impact_sales_summaries": (
        "FgiImpactSalesSummary",
        [
            ("id", "number", "type: 'bigint'", True),
            ("impact_process_id", "number", "type: 'bigint'", False),
            ("growth_rate_diff", "string", "type: 'numeric', precision: 7, scale: 2, nullable: true", False),
            ("total_working_days", "number", "type: 'int', nullable: true", False),
            ("period_year", "number", "type: 'int'", False),
            ("period_month", "number", "type: 'int'", False),
        ],
    ),
    "sgi_fgi_impact_competitors": (
        "FgiImpactCompetitor",
        [
            ("id", "number", "type: 'bigint'", True),
            ("impact_process_id", "number", "type: 'bigint'", False),
            ("competitor_code", "string", "type: 'varchar', length: 20", False),
            ("branch_name", "string", "type: 'varchar', length: 200, nullable: true", False),
            ("zone_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("open_date", "Date", "type: 'date', nullable: true", False),
        ],
    ),
    "sgi_sales_transactions": (
        "SalesTransaction",
        [
            ("id", "number", "type: 'bigint'", True),
            ("sales_summary_id", "number", "type: 'bigint'", False),
            ("txn_date", "Date", "type: 'date'", False),
            ("window_no", "number", "type: 'int'", False),
            ("sales_amount", "string", "type: 'numeric', precision: 15, scale: 2", False),
            ("sales_diff", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
            ("is_outlier", "boolean", "type: 'boolean', default: false", False),
        ],
    ),
    "sgi_interface_transactions": (
        "InterfaceTransaction",
        [
            ("id", "number", "type: 'bigint'", True),
            ("data_name", "string", "type: 'varchar', length: 50", False),
            ("direction", "string", "type: 'varchar', length: 3", False),
            ("business_key", "string", "type: 'varchar', length: 100, nullable: true", False),
            ("doc_no", "string", "type: 'varchar', length: 12, nullable: true", False),
            ("impact_process_id", "number", "type: 'bigint', nullable: true", False),
            ("sales_summary_id", "number", "type: 'bigint', nullable: true", False),
            ("file_name", "string", "type: 'varchar', length: 255, nullable: true", False),
            ("status", "string", "type: 'varchar', length: 20", False),
            ("sent_at", "Date", "type: 'timestamptz', nullable: true", False),
            ("acked_at", "Date", "type: 'timestamptz', nullable: true", False),
            ("return_code", "string", "type: 'varchar', length: 10, nullable: true", False),
        ],
    ),
    "sgi_external_factors": (
        "ExternalFactor",
        [
            ("factor_code", "string", "type: 'varchar', length: 20", True),
            ("factor_name", "string", "type: 'varchar', length: 200", False),
            ("description", "string", "type: 'text', nullable: true", False),
            ("is_active", "boolean", "type: 'boolean', default: true", False),
        ],
    ),
    "sgi_impacted_stores": (
        "ImpactedStore",
        [
            ("store_code", "string", "type: 'char', length: 5", True),
            ("store_name", "string", "type: 'varchar', length: 200", False),
            ("zone_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("region_code", "string", "type: 'varchar', length: 10, nullable: true", False),
            ("store_type", "string", "type: 'varchar', length: 5, nullable: true", False),
            ("transfer_sbp_date", "Date", "type: 'date', nullable: true", False),
            ("is_active", "boolean", "type: 'boolean', default: true", False),
        ],
    ),
    "sgi_competitors": (
        "Competitor",
        [
            ("competitor_code", "string", "type: 'varchar', length: 2", True),
            ("name_th", "string", "type: 'varchar', length: 200", False),
            ("name_en", "string", "type: 'varchar', length: 200, nullable: true", False),
            ("is_active", "boolean", "type: 'boolean', default: true", False),
        ],
    ),
    "sgi_document_cost_details": (
        "DocumentCostDetail",
        [
            ("id", "number", "type: 'bigint'", True),
            ("doc_no", "string", "type: 'varchar', length: 12", False),
            ("new_store_code", "string", "type: 'char', length: 5, nullable: true", False),
            ("cost_year", "number", "type: 'int'", False),
            ("cost_month", "number", "type: 'int'", False),
            ("cost_target", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
            ("cost_amount", "string", "type: 'numeric', precision: 15, scale: 2, nullable: true", False),
        ],
    ),
    "sgi_document_running_numbers": (
        "DocumentRunningNumber",
        [
            ("year", "number", "type: 'int'", True),
            ("last_running_no", "number", "type: 'int', default: 0", False),
        ],
    ),
    "job_configs": (
        "JobConfig",
        [
            ("job_no", "string", "type: 'varchar', length: 5", True),
            ("job_name", "string", "type: 'varchar', length: 200", False),
            ("cron_expression", "string", "type: 'varchar', length: 50, nullable: true", False),
            ("is_enabled", "boolean", "type: 'boolean', default: true", False),
            ("params", "Record<string, unknown>", "type: 'jsonb', nullable: true", False),
            ("updated_by", "string", "type: 'varchar', length: 50, nullable: true", False),
            ("updated_at", "Date", "type: 'timestamptz', nullable: true", False),
        ],
    ),
    "job_run_histories": (
        "JobRunHistory",
        [
            ("id", "number", "type: 'bigint'", True),
            ("job_no", "string", "type: 'varchar', length: 5", False),
            ("run_status", "string", "type: 'varchar', length: 20", False),
            ("started_at", "Date", "type: 'timestamptz'", False),
            ("finished_at", "Date", "type: 'timestamptz', nullable: true", False),
            ("total_records", "number", "type: 'int', default: 0", False),
            ("success_records", "number", "type: 'int', default: 0", False),
            ("failed_records", "number", "type: 'int', default: 0", False),
            ("error_message", "string", "type: 'text', nullable: true", False),
            ("triggered_by", "string", "type: 'varchar', length: 50, nullable: true", False),
        ],
    ),
    # ⚠️ store-backend มีตารางนี้อยู่แล้วในชื่อ **เอกพจน์** `fcs_qssi_score` (sps_store)
    #    และมีโค้ดเขียนอยู่จริง (performance.service.ts) — ห้ามสร้างตาราง/entity ซ้ำ
    "fcs_qssi_score": (
        "FcsQssiScore",
        [
            ("id", "number", "type: 'bigint'", True),
            ("store_id", "string", "type: 'char', length: 5", False),
            ("category_code", "string", "type: 'varchar', length: 5", False),
            ("period_year", "number", "type: 'int'", False),
            ("period_month", "number", "type: 'int'", False),
            ("score", "string", "type: 'numeric', precision: 7, scale: 2, nullable: true", False),
        ],
    ),
}


# --------------------------------------------------------------------------------------
# string helpers
# --------------------------------------------------------------------------------------
def _pascal(text: str) -> str:
    parts = [w for w in re.split(r"[^0-9A-Za-z]+", str(text)) if w]
    return "".join(w[:1].upper() + w[1:] for w in parts)


def _camel(text: str) -> str:
    pas = _pascal(text)
    return pas[:1].lower() + pas[1:] if pas else ""


def _singular(word: str) -> str:
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("sses"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _entity_class(tname: str) -> str:
    hint = COLUMN_HINTS.get(tname)
    if hint:
        return hint[0]
    return _pascal(_singular(tname))


def _clip(text: str, width: int = 78) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[: width - 1] + "…"


# --------------------------------------------------------------------------------------
# topic -> feature identity
# --------------------------------------------------------------------------------------
def _feature(topic: Any) -> tuple[str, str]:
    """คืน (slug, PascalName) จาก topic.file เช่น BE/LLDD-BE-API-Document-List-Search."""
    raw = str(getattr(topic, "file", "") or "sgi-feature")
    name = raw.split("/")[-1]
    for prefix in ("LLDD-BE-API-", "LLDD-BE-", "LLDD-"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    name = name.replace("_", "-")
    slug = "-".join(w.lower() for w in re.split(r"[^0-9A-Za-z]+", name) if w)
    return (slug or "feature"), (_pascal(name) or "Feature")


# --------------------------------------------------------------------------------------
# endpoints
# --------------------------------------------------------------------------------------
_PATH_OK = re.compile(r"^/[A-Za-z0-9/_{}.\-]+$")
_HTTP_VERBS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_VERB_WORD = {"GET": "get", "POST": "create", "PUT": "update", "PATCH": "patch", "DELETE": "remove"}


class _Endpoint:
    __slots__ = ("method", "path", "purpose", "request", "response", "segments", "params", "handler")

    def __init__(self, method: str, path: str, purpose: str, request: Any, response: Any) -> None:
        self.method = method
        self.path = path
        self.purpose = purpose
        self.request = request if isinstance(request, dict) else {}
        self.response = response if isinstance(response, dict) else {}
        self.segments = [s for s in path.strip("/").split("/") if s]
        self.params = [s[1:-1] for s in self.segments if s.startswith("{") and s.endswith("}")]
        self.handler = ""

    @property
    def nest_segments(self) -> list[str]:
        return [(":" + s[1:-1]) if s.startswith("{") else s for s in self.segments]

    @property
    def payload_keys(self) -> dict[str, Any]:
        """key ของ request ที่ไม่ใช่ path param (path param ใช้ @Param แยก)."""
        return {k: v for k, v in self.request.items() if k not in self.params}


def _collect_endpoints(topic: Any, doc_name: str = "") -> tuple[list[_Endpoint], list[list[str]]]:
    """แยก endpoint ที่ implement ได้จริง ออกจากเส้นที่เป็น contract กลาง/ของระบบเดิม/ของเอกสารอื่น."""
    implementable: list[_Endpoint] = []
    external: list[list[str]] = []
    for spec in list(getattr(topic, "apis", []) or []):
        method = str(getattr(spec, "method", "") or "").upper().strip()
        path = str(getattr(spec, "path", "") or "").strip()
        purpose = str(getattr(spec, "purpose", "") or "")
        if method not in _HTTP_VERBS or "*" in path or not _PATH_OK.match(path):
            reason = (
                "contract กลาง/wildcard — ไม่ผูกกับ controller ใดเส้นเดียว"
                if "*" in path or method not in _HTTP_VERBS
                else "endpoint ของระบบ SBP เดิม — เรียกใช้ ไม่ต้อง implement ใหม่"
            )
            external.append([f"{method} {path}".strip(), _clip(purpose, 60), reason])
            continue
        cut = _cut_reason(path)
        if cut:
            external.append([f"{method} {path}", _clip(purpose, 60),
                             f"**ตัดออกจากดีไซน์แล้ว** (มติ 2026-08-05/06) — ใช้ {cut}"])
            continue
        owner = ENDPOINT_OWNER.get(f"{method} {path}")
        if owner and doc_name and owner != doc_name:
            external.append([f"{method} {path}", _clip(purpose, 60),
                             f"**reference — implement ที่เอกสาร `{owner}`** (1 เส้น = 1 เจ้าของ "
                             "ไม่ประกาศ controller ซ้ำ ไม่งั้น NestJS จะ register ทับกันเงียบ ๆ)"])
            continue
        implementable.append(
            _Endpoint(method, path, purpose, getattr(spec, "request", None), getattr(spec, "response", None))
        )
    _assign_handlers(implementable)
    return implementable, external


def _assign_handlers(endpoints: list[_Endpoint]) -> None:
    used: set[str] = set()
    for ep in endpoints:
        literals = [s for s in ep.segments if not s.startswith("{")]
        literals = [s for s in literals if s not in {"api", "v1"}]
        tail = literals[-1] if literals else "root"
        prev = literals[-2] if len(literals) > 1 else ""
        if tail == "actions" and ep.method == "POST":
            name = "submitAction"
        elif tail == "ack":
            name = "receiveAck" + _pascal(prev)
        elif tail == "export":
            name = "export" + _pascal(prev)
        elif tail == "search":
            name = "search" + _pascal(prev)
        elif tail == "timeline":
            name = "getTimeline"
        elif tail == "summary":
            name = "get" + _pascal(prev) + "Summary"
        else:
            name = _VERB_WORD.get(ep.method, "handle") + _pascal(" ".join(literals) or "root")
            if ep.segments and ep.segments[-1].startswith("{"):
                name += "By" + _pascal(ep.segments[-1][1:-1])
        candidate, n = name, 2
        while candidate in used:
            candidate = f"{name}{n}"
            n += 1
        used.add(candidate)
        ep.handler = candidate


# store-backend **ไม่มี global prefix** (main.ts คอมเมนต์ `app.setGlobalPrefix("api")` ทิ้งไว้)
# และ controller ตัวอื่นใช้ base เป็นชื่อโดเมนล้วน ('store', 'statement', 'common', 'master')
# ส่วน '/api/v1' เป็น prefix ของ **BFF** (NEXT_PUBLIC_BFF_API_URL=.../api/v1) — คนละชั้นกัน
BACKEND_PREFIX = "sgi"


def _strip_api_prefix(segments: list[str]) -> list[str]:
    out = list(segments)
    if out[:2] == ["api", "v1"]:
        out = out[2:]
    return out


def _controller_base(endpoints: list[_Endpoint]) -> str:
    """base path ร่วมของ controller ฝั่ง store-backend (prefix `sgi/…` ไม่ใช่ `api/v1/…`)."""
    if not endpoints:
        return BACKEND_PREFIX
    common = _strip_api_prefix(endpoints[0].segments)
    for ep in endpoints[1:]:
        merged: list[str] = []
        for a, b in zip(common, _strip_api_prefix(ep.segments)):
            if a != b:
                break
            merged.append(a)
        common = merged
    while common and common[-1].startswith("{"):
        common.pop()
    if len(endpoints) == 1 and len(common) == len(_strip_api_prefix(endpoints[0].segments)):
        common = common[:-1]
    return "/".join([BACKEND_PREFIX] + common)


def _relative_route(ep: _Endpoint, base: str) -> str:
    base_parts = [x for x in base.split("/") if x and x != BACKEND_PREFIX]
    rest = [(":" + s[1:-1]) if s.startswith("{") else s for s in _strip_api_prefix(ep.segments)][len(base_parts):]
    return "/".join(rest)


# --------------------------------------------------------------------------------------
# db tables
# --------------------------------------------------------------------------------------
def _split_tables(topic: Any) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """คืน (own, reused) โดย own = ตารางที่ SGI ต้องสร้าง entity เอง."""
    own: list[tuple[str, str, str]] = []
    reused: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for row in list(getattr(topic, "db_tables", []) or []):
        cells = list(row) + ["", "", ""]
        raw_name, rw, usage = str(cells[0]), str(cells[1]), str(cells[2])
        # ตัด "(...)" ทิ้งก่อนแยก "/" เพราะ tag อย่าง "(@srm/glb-workflow)" มี "/" อยู่ข้างใน
        cleaned = re.sub(r"\(.*?\)", " ", raw_name)
        for part in cleaned.split("/"):
            name = part.strip()
            if not name or " " in name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            if key.startswith(_WORKFLOW_PREFIX) or key in REUSED_TABLES:
                reused.append((name, rw, REUSED_TABLES.get(key, "workflow engine @srm/glb-workflow")))
            else:
                own.append((name, rw, usage))
    return own, reused


# --------------------------------------------------------------------------------------
# workflow use cases
# --------------------------------------------------------------------------------------
def _workflow_plan(topic: Any, endpoints: list[_Endpoint], reused: list[tuple[str, str, str]]) -> list[list[str]]:
    """เลือก use case ของ @srm/glb-workflow ให้ตรงกับ endpoint จริงของ topic."""
    plan: list[list[str]] = []
    for ep in endpoints:
        path = ep.path.lower()
        label = f"{ep.method} {ep.path}"
        if path.endswith("/actions") and ep.method == "POST":
            plan.append([label, "getPermissionEvents() → eventWorkflow()", "ตรวจสิทธิ์ event ของผู้ใช้ก่อนเดิน state และบันทึก history"])
        elif "/sgi/workflow/instances" in path and ep.method == "POST":
            plan.append([label, "initializeWorkflow() → addPreApprover()", "เปิด transaction ใหม่ (referenceId = docNo) แล้วผูกผู้อนุมัติ state 06"])
        elif "/sgi/workflow/instances" in path:
            plan.append([label, "getTransaction()", "อ่าน currentState ของ instance ตาม referenceId"])
        elif path.endswith("/timeline"):
            plan.append([label, "getHistory()", "timeline การเปลี่ยน state (fromState/toState/event/remark)"])
        # ⚠️ ห้ามใช้ substring "pending" — จะไปโดน /sgi/interface/pending-ack ซึ่งเป็น watchdog ACK ของ STA
        #    (อ่าน sgi_interface_transactions) ไม่ใช่ inbox ของ workflow engine
        elif path.rstrip("/").endswith("/sgi/document/tasks"):
            plan.append([label, "getPendingFlowByUser()", "inbox งานค้างของ userId/groupId ที่ BFF ส่งมาใน header"])
        elif "/sgi/workflow/summary" in path:
            plan.append([label, "getPendingFlowByUser() (aggregate)", "นับงานค้างต่อ state แล้วรวมกับ workflow_generation_status W/Y/N"])
    if not plan and any(t[0].lower().startswith(_WORKFLOW_PREFIX) for t in reused):
        plan.append(["(อ่านสถานะประกอบ)", "getTransaction()", "อ่านสถานะปัจจุบันของเอกสารเพื่อประกอบ response"])
    return plan


# --------------------------------------------------------------------------------------
# DTO generation
# --------------------------------------------------------------------------------------
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def _field_index(topic: Any) -> dict[str, tuple[str, str, str]]:
    index: dict[str, tuple[str, str, str]] = {}
    for row in list(getattr(topic, "fields", []) or []):
        cells = list(row) + ["", "", "", ""]
        raw_name = str(cells[0])
        fmt, rule, behavior = str(cells[1]), str(cells[2]), str(cells[3])
        for part in re.split(r"[/|]", raw_name):
            key = part.strip()
            if key:
                index.setdefault(key, (fmt, rule, behavior))
                index.setdefault(_camel(key), (fmt, rule, behavior))
    return index


def _dto_property(name: str, example: Any, info: tuple[str, str, str] | None) -> tuple[str, list[str], str]:
    """คืน (tsType, decorators, comment) ของ property หนึ่งตัว."""
    fmt = (info[0] if info else "") or ""
    rule = (info[1] if info else "") or ""
    note = (info[2] if info else "") or ""
    low_fmt, low_rule = fmt.lower(), rule.lower()

    ts = "string"
    if isinstance(example, bool):
        ts = "boolean"
    elif isinstance(example, (int, float)):
        ts = "number"
    elif isinstance(example, list):
        ts = "string[]"
    elif isinstance(example, dict):
        ts = "Record<string, unknown>"
    if "integer" in low_fmt or low_fmt.strip() == "int":
        ts = "number"
    elif "number" in low_fmt:
        ts = "number"
    elif "array" in low_fmt:
        ts = "string[]"
    elif "boolean" in low_fmt:
        ts = "boolean"
    elif "multipart" in low_fmt:
        ts = "Express.Multer.File"

    # pagination เป็น optional เสมอตาม API Contract (page >= 1 default 1 · size <= 100 default 20)
    # เดิมตัดสิน required จากคำว่า "optional" ในคอลัมน์ Validation ของตารางฟิลด์อย่างเดียว
    # ทำให้ `page/size | integer | page>=1 size<=100` กลายเป็น @IsNotEmpty() แล้วเรียกโดยไม่ส่ง page โดน 400
    always_optional = name.lower() in {"page", "size", "limit", "offset", "pagesize", "sort", "order"}
    optional = always_optional or "optional" in low_rule or example is None
    decos: list[str] = ["@IsOptional()" if optional else "@IsNotEmpty()"]

    if ts == "Express.Multer.File":
        decos = ["// TODO: ใช้ FileInterceptor + ValidationPipe แยก ไม่ผ่าน class-validator"]
        return ts, decos, note
    if ts == "number":
        decos.append("@Type(() => Number)")
        decos.append("@IsInt()" if "decimal" not in low_fmt else "@IsNumber()")
    elif ts == "boolean":
        decos.append("@Type(() => Boolean)")
        decos.append("@IsBoolean()")
    elif ts == "string[]":
        decos.append("@IsArray()")
        decos.append("@IsString({ each: true })")
    elif ts == "Record<string, unknown>":
        decos.append("@IsObject()")
    else:
        decos.append("@IsString()")

    enum_values = [v.strip() for v in fmt.split("|")] if "|" in fmt and len(fmt) < 40 else []
    if enum_values and all(_IDENT.match(v.replace("-", "")) or v.isalnum() for v in enum_values):
        decos.append("@IsIn([" + ", ".join(f"'{v}'" for v in enum_values) + "])")
    if "yyyy/xxxxx" in low_fmt:
        decos.append(r"@Matches(/^\d{4}\/\d{5}$/, { message: 'เลขที่เอกสารต้องอยู่ในรูปแบบ YYYY/xxxxx (ค.ศ.)' })")
    elif "yyyy-mm-dd" in low_fmt:
        decos.append(r"@Matches(/^\d{4}-\d{2}-\d{2}$/)")
    elif "yyyy-mm" in low_fmt:
        decos.append(r"@Matches(/^\d{4}-\d{2}$/)")
    if "5 digits" in low_rule or "5 digits" in low_fmt or "5 หลัก" in rule:
        decos.append(r"@Matches(/^\d{5}$/, { message: 'รหัสร้านต้องเป็นตัวเลข 5 หลัก และคงเลขศูนย์นำหน้า' })")
    if "พ.ศ." in fmt and ts == "number":
        decos.append("@Min(2500)")
        decos.append("@Max(2600)")
    lname = name.lower()
    if lname == "page":
        decos.append("@Min(1)")
    if lname in {"size", "limit", "pagesize"}:
        decos.append("@Min(1)")
        decos.append("@Max(100)")
    if lname == "reason":
        decos.append("@MaxLength(500)")
    return ts, decos, note


def _dto_class(class_name: str, source: dict[str, Any], skip: set[str], fields: dict[str, tuple[str, str, str]],
               header: str, max_props: int = 8, force_optional: set[str] | None = None) -> list[str]:
    force_optional = force_optional or set()
    lines = [f"// {header}", f"export class {class_name} {{"]
    count = 0
    for key, example in source.items():
        if not _IDENT.match(str(key)) or key in skip:
            continue
        if count >= max_props:
            lines.append("  // TODO: เพิ่ม property ที่เหลือของ payload นี้ให้ครบตามหัวข้อฟิลด์ของเอกสารนี้")
            break
        info = fields.get(key) or fields.get(_camel(key))
        ts, decos, note = _dto_property(key, example, info)
        if key in force_optional and decos and decos[0] == "@IsNotEmpty()":
            decos[0] = "@IsOptional()"
            note = (note + " · " if note else "") + "required เฉพาะบาง endpoint — ตรวจซ้ำใน service"
        if note:
            lines.append(f"  /** {_clip(note, 90)} */")
        for deco in decos:
            lines.append(f"  {deco}")
        optional_mark = "?" if any(d.startswith("@IsOptional") for d in decos) else ""
        lines.append(f"  {key}{optional_mark}: {ts};")
        lines.append("")
        count += 1
    if count == 0:
        lines.append("  // TODO: endpoint นี้ไม่มี body/query ใน LLDD — เพิ่ม property เมื่อสรุป payload แล้ว")
    if lines[-1] == "":
        lines.pop()
    lines.append("}")
    return lines


_DTO_IMPORTS = [
    "// src/modules/sgi-<feature>/dto/sgi-<feature>.dto.ts",
    "import { Type } from 'class-transformer';",
    "import {",
    "  IsArray, IsBoolean, IsIn, IsInt, IsNotEmpty, IsNumber, IsObject, IsOptional,",
    "  IsString, Matches, Max, MaxLength, Min,",
    "} from 'class-validator';",
    "",
    "// ValidationPipe ระดับ global ตั้ง whitelist + forbidNonWhitelisted + transform ไว้แล้ว (main.ts)",
    "// property ที่ไม่ประกาศที่นี่จะถูก reject เป็น 400 อัตโนมัติ",
]


def _dto_spec(topic: Any, endpoints: list[_Endpoint], pascal: str, slug: str) -> dict[str, Any]:
    """วางแผน DTO ของโมดูล: คืนชื่อคลาสที่ "สร้างจริง" ให้ controller อ้างอิงได้ตรงกัน."""
    fields = _field_index(topic)
    header = [line.replace("<feature>", slug) for line in _DTO_IMPORTS]
    parts: list[str] = []
    body_classes: dict[str, str] = {}

    get_eps = [ep for ep in endpoints if ep.method == "GET"]
    query_source: dict[str, Any] = {}
    query_skip: set[str] = set()
    for ep in get_eps:
        query_skip.update(ep.params)
        for k, v in ep.payload_keys.items():
            query_source.setdefault(k, v)
    # key ที่ไม่ได้อยู่ครบทุก GET endpoint ต้องเป็น optional ใน DTO ร่วม
    force_optional = {
        k for k in query_source
        if sum(1 for ep in get_eps if k in ep.payload_keys) < len(get_eps)
    } if len(get_eps) > 1 else set()

    query_class = f"{pascal}QueryDto" if query_source else ""
    if query_class:
        parts.append("\n".join(header + [""] + _dto_class(
            query_class, query_source, query_skip, fields,
            "query ร่วมของ GET ทุกเส้นในโมดูลนี้ (path param ใช้ @Param แยก)",
            max_props=6, force_optional=force_optional)))

    for ep in endpoints:
        if ep.method == "GET" or not ep.payload_keys or len(body_classes) >= 3:
            continue
        cls = _pascal(ep.handler) + "BodyDto"
        lines = _dto_class(cls, ep.payload_keys, set(ep.params), fields,
                           f"body ของ {ep.method} {ep.path}", max_props=6)
        parts.append("\n".join((header + [""] if not parts else []) + lines))
        body_classes[ep.handler] = cls

    remaining = [f"{ep.method} {ep.path}" for ep in endpoints
                 if ep.method != "GET" and ep.payload_keys and ep.handler not in body_classes]
    if remaining:
        parts[-1] += ("\n\n// TODO: สร้าง BodyDto ของ endpoint ที่เหลือด้วยรูปแบบเดียวกัน: "
                      + ", ".join(remaining[:4]) + (" …" if len(remaining) > 4 else ""))
    if not parts:
        parts.append("\n".join(header + [""] + _dto_class(
            f"{pascal}RequestDto", {}, set(), fields, "payload ของโมดูลนี้")))
    return {"query_class": query_class, "body_classes": body_classes, "parts": parts}


# --------------------------------------------------------------------------------------
# code blocks — store-backend
# --------------------------------------------------------------------------------------
def _has_body(ep: _Endpoint) -> bool:
    return ep.method in {"POST", "PUT", "PATCH", "DELETE"} and bool(ep.payload_keys)


def _signature(ep: _Endpoint, dto: dict[str, Any]) -> dict[str, list[str]]:
    """แหล่งความจริงเดียวของ argument list — controller และ service ต้องใช้ผลลัพธ์นี้ทั้งคู่
    จึงไม่มีทางที่จำนวน/ลำดับพารามิเตอร์สองฝั่งจะไม่ตรงกัน
    """
    query_class = dto.get("query_class") or ""
    body_classes: dict[str, str] = dto.get("body_classes") or {}
    controller: list[str] = [f"@Param('{name}') {_camel(name)}: string" for name in ep.params]
    service: list[str] = [f"{_camel(name)}: string" for name in ep.params]
    call: list[str] = [_camel(name) for name in ep.params]
    if ep.method == "GET" and ep.payload_keys:
        cls = query_class or "Record<string, string>"
        controller.append(f"@Query() query: {cls}")
        service.append(f"query: {cls}")
        call.append("query")
    if _has_body(ep):
        cls = body_classes.get(ep.handler) or "Record<string, unknown>"
        controller.append(f"@Body() body: {cls}")
        service.append(f"body: {cls}")
        call.append("body")
    controller.append("@UserId() userId: string")
    service.append("userId: string")
    call.append("userId")
    return {"controller": controller, "service": service, "call": call}


def _controller_code(topic: Any, slug: str, pascal: str, base: str, dto: dict[str, Any],
                     chunk: list[_Endpoint], part: int, total_parts: int,
                     seen_dtos: set[str] | None = None) -> str:
    query_class = dto.get("query_class") or ""
    body_classes: dict[str, str] = dto.get("body_classes") or {}

    imports_nest = ["Controller", "UseGuards"]
    for ep in chunk:
        imports_nest.append("Delete" if ep.method == "DELETE" else ep.method.capitalize())
        if ep.params:
            imports_nest.append("Param")
        if ep.method == "GET" and ep.payload_keys:
            imports_nest.append("Query")
        if _has_body(ep):
            imports_nest.append("Body")
    ordered = [x for x in ["Body", "Controller", "Delete", "Get", "Param", "Patch", "Post", "Put", "Query", "UseGuards"]
               if x in set(imports_nest)]

    dto_names: list[str] = []
    if query_class and any(ep.method == "GET" and ep.payload_keys for ep in chunk):
        dto_names.append(query_class)
    for ep in chunk:
        if _has_body(ep) and ep.handler in body_classes:
            dto_names.append(body_classes[ep.handler])
    dto_names = list(dict.fromkeys(dto_names))

    head_note = f"  (ส่วนที่ {part}/{total_parts} — คลาสเดียวกัน)" if total_parts > 1 else ""
    lines = [f"// src/modules/sgi-{slug}/sgi-{slug}.controller.ts" + head_note]
    if part == 1:
        lines += [
            "import { " + ", ".join(ordered) + " } from '@nestjs/common';",
            "import { HttpHeaderGuard } from '../../guards/http-header.guard';",
            "import { UserId } from '../../common/decorators/user-id.decorator';",
            f"import {{ Sgi{pascal}Service }} from './sgi-{slug}.service';",
        ]
        if dto_names:
            lines.append("import { " + ", ".join(dto_names) + " } from './dto/sgi-" + slug + ".dto';")
        lines += [
            "",
            f"// {getattr(topic, 'title', '')}",
            "// BFF เรียกด้วย x-api-key และแนบ x-user-id / x-user-group-id / x-user-permissions มาให้",
            f"@Controller('{base}')",
            "@UseGuards(HttpHeaderGuard)",
            f"export class Sgi{pascal}Controller {{",
            f"  constructor(private readonly service: Sgi{pascal}Service) {{}}",
            "",
        ]
    else:
        extra = [x for x in dto_names if x not in (seen_dtos or set())]
        if extra:
            lines.append("// import เพิ่ม: " + ", ".join(extra))
        lines.append(f"// (method ต่อไปนี้อยู่ในคลาส Sgi{pascal}Controller เดียวกับส่วนที่ 1)")
        lines.append("")
    if seen_dtos is not None:
        seen_dtos.update(dto_names)

    for ep in chunk:
        route = _relative_route(ep, base)
        deco = "Delete" if ep.method == "DELETE" else ep.method.capitalize()
        sig = _signature(ep, dto)
        args, call = sig["controller"], sig["call"]
        lines.append(f"  // {ep.method} {ep.path} — {_clip(ep.purpose, 70)}")
        lines.append(f"  @{deco}('{route}')" if route else f"  @{deco}()")
        signature = ", ".join(args)
        if len(f"  {ep.handler}({signature}) {{") > 100:
            lines.append(f"  {ep.handler}(")
            for arg in args:
                lines.append(f"    {arg},")
            lines.append("  ) {")
        else:
            lines.append(f"  {ep.handler}({signature}) {{")
        lines.append("    // TODO: ตรวจ x-user-permissions ก่อนเรียก service ถ้า endpoint นี้จำกัดสิทธิ์เมนู")
        lines.append(f"    return this.service.{ep.handler}({', '.join(call)});")
        lines.append("  }")
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    if part == total_parts:
        lines.append("}")
    return "\n".join(lines)


def _service_code(topic: Any, endpoints: list[_Endpoint], own: list[tuple[str, str, str]], slug: str,
                  pascal: str, wf_plan: list[list[str]], dto: dict[str, Any]) -> str:
    """service ต้องมี method ครบทุกเส้นที่ controller เรียก และ signature ต้องตรงกันเป๊ะ

    (เดิม emit แค่ 1 read + 1 write ทำให้ controller เรียก method ที่ service ไม่มี และ
    arity ไม่ตรงกันเพราะ query ถูกใส่ให้ทุก GET เสมอ — ตอนนี้ทั้งสองฝั่งใช้ ``_signature()`` ตัวเดียวกัน)
    """
    read_ep = next((e for e in endpoints if e.method == "GET"), None)
    write_ep = next((e for e in endpoints if e.method in {"POST", "PUT", "PATCH", "DELETE"}), None)
    main_table = own[0][0] if own else "sgi_compensation_documents"
    write_table = next((t[0] for t in own if str(t[1]).upper() in {"W", "R/W"}), main_table)
    uses_wf = bool(wf_plan)

    lines = [
        f"// src/modules/sgi-{slug}/sgi-{slug}.service.ts",
        "import { Inject, Injectable, Logger, NotFoundException, NotImplementedException } from '@nestjs/common';",
        "import { DataSource } from 'typeorm';",
    ]
    if uses_wf:
        lines.append("import { WorkflowService } from '../workflow/workflow.service';")
    lines += [
        f"import {{ SGI_SQL }} from './sgi-{slug}.sql';",
        "",
        "@Injectable()",
        f"export class Sgi{pascal}Service {{",
        f"  private readonly logger = new Logger(Sgi{pascal}Service.name);",
    ]
    if uses_wf:
        lines.append("  // versionId ของ workflow ประกันรายได้ (ตั้งใน env เหมือน COOPERATION_WORKFLOW_VERSION_ID)")
        lines.append("  private readonly versionId = Number(process.env.SGI_WORKFLOW_VERSION_ID);")
    lines.append("")
    lines.append("  constructor(")
    lines.append("    // DATA_SOURCE override query(): SELECT/WITH ไป slave pool, write ไป master")
    lines.append("    @Inject('DATA_SOURCE') private readonly dataSource: DataSource,")
    if uses_wf:
        lines.append("    private readonly workflow: WorkflowService,")
    lines.append("  ) {}")
    lines.append("")

    if not endpoints:
        lines += [
            "  // TODO: topic นี้ยังไม่มี endpoint ที่ implement ได้ตรง ๆ — service ทำหน้าที่ contract กลาง",
            "  async ping() {",
            f"    return this.dataSource.query('SELECT 1 AS ok FROM {main_table} LIMIT 1');",
            "  }",
            "}",
        ]
        return "\n".join(lines)

    for ep in endpoints:
        sig = ", ".join(_signature(ep, dto)["service"])
        has_query = ep.method == "GET" and bool(ep.payload_keys)
        lines.append(f"  // {ep.method} {ep.path} — {_clip(ep.purpose, 70)}")
        if ep is read_ep:
            lines.append(f"  async {ep.handler}({sig}) {{")
            if has_query:
                lines.append("    const page = Number(query.page ?? 1);")
                lines.append("    const size = Math.min(Number(query.size ?? 20), 100);")
            else:
                lines.append("    const page = 1;")
                lines.append("    const size = 100; // endpoint นี้ไม่มี query param — ไม่แบ่งหน้า")
            lines += [
                f"    // SQL เต็มอยู่ในหัวข้อ Database SQL ของเอกสารนี้ (คีย์ '{ep.method} {ep.path}')",
                "    // ⚠️ SQL ตัวอย่างบางเส้นเขียนด้วย named parameter (:size/:offset) แต่ dataSource.query()",
                "    //    รับเฉพาะ positional $1..$n — ต้องแปลงชื่อเป็นลำดับก่อน หรือใช้ QueryBuilder แทน",
                f"    const rows = await this.dataSource.query(SGI_SQL.{ep.handler}, [",
                "      // TODO: เรียงพารามิเตอร์ให้ตรงกับ $1..$n ของ SQL จริง",
                "      userId, (page - 1) * size, size,",
                "    ]);",
                "    // TODO: total ต้องมาจาก COUNT(*) แยก query หรือ window function ไม่ใช่ rows.length",
                "    return { page, size, total: rows.length, items: rows };",
                "  }",
                "",
            ]
            continue
        if ep is write_ep:
            first_key = _camel(ep.params[0]) if ep.params else "body.docNo"
            lines += [
                f"  // mutation ต้องอยู่ใน transaction เดียว (ไม่มี audit ของ master แล้ว · 2026-08-07)",
                f"  async {ep.handler}({sig}) {{",
                "    const runner = this.dataSource.createQueryRunner();",
                "    await runner.connect();",
                "    await runner.startTransaction();",
                "    try {",
                f"      // TODO: lock แถวเป้าหมายของ {write_table} ด้วย SELECT ... FOR UPDATE ก่อนเขียน",
                f"      const [current] = await runner.query(SGI_SQL.{ep.handler}Lock, [{first_key}]);",
                "      if (!current) {",
                "        throw new NotFoundException('ไม่พบข้อมูลที่ต้องการ');",
                "      }",
                f"      await runner.query(SGI_SQL.{ep.handler}, [/* TODO: ผูกค่าจาก body */]);",
                "      await runner.commitTransaction();",
            ]
            if uses_wf:
                lines += [
                    "      // ⚠️ workflow engine อยู่คนละ DataSource ('workflow-connection' ของ @srm/glb-workflow)",
                    "      //    จึง **atomic ร่วมกับ transaction ข้างบนไม่ได้** — ต้อง commit ฝั่ง SGI ให้เสร็จก่อน",
                    "      //    แล้วค่อย eventWorkflow (idempotency key = referenceId = docNo)",
                    "      // TODO: เรียก workflow use case ตามตารางหัวข้อ Workflow ด้านล่าง + retry",
                    "      // TODO: ถ้า eventWorkflow ล้มเหลว ต้องมี compensating action และบันทึกผลลง",
                    "      //       sgi_consideration_logs เพื่อให้ job reconcile ตามเก็บได้",
                ]
            lines += [
                "      return { message: 'saved' };",
                "    } catch (error) {",
                "      await runner.rollbackTransaction();",
                "      this.logger.error(error);",
                "      throw error;",
                "    } finally {",
                "      await runner.release();",
                "    }",
                "  }",
                "",
            ]
            continue
        # เส้นที่เหลือ: stub ที่ signature ตรงกับ controller เพื่อให้ TypeScript ผ่านตั้งแต่วันแรก
        lines += [
            f"  async {ep.handler}({sig}) {{",
            f"    // TODO: implement ตาม business rule ของ {ep.method} {ep.path}",
            f"    //       (SQL อยู่ในหัวข้อ Database SQL คีย์ '{ep.method} {ep.path}')",
            f"    throw new NotImplementedException('{ep.handler} ยังไม่ implement');",
            "  }",
            "",
        ]
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("}")
    return "\n".join(lines)


def _workflow_code(slug: str, pascal: str, wf_plan: list[list[str]]) -> str:
    kinds = " ".join(row[1] for row in wf_plan)
    lines = [
        f"// src/modules/sgi-{slug}/sgi-{slug}.workflow.ts (หรือรวมไว้ใน service เดียวกัน)",
        "// WorkflowService = wrapper ของ @srm/glb-workflow ที่ store-backend มีอยู่แล้ว",
        "// (DataSource แยกชื่อ 'workflow-connection', ทุก use case ห่อด้วย TypeOrmUnitOfWork)",
        "",
    ]
    if "initializeWorkflow" in kinds:
        lines += [
            "  // เปิด workflow ใหม่แทน K2 REST StartInstance — referenceId = docNo",
            "  const transactionId = await this.workflow.initializeWorkflow({",
            "    versionId: this.versionId,",
            "    referenceId: docNo,",
            "    userId: Number(userId),",
            "  });",
            "  // ผูกผู้อนุมัติล่วงหน้าของ section 06 (prepared approver)",
            "  await this.workflow.addPreApprover({",
            "    versionId: this.versionId,",
            "    referenceId: docNo,",
            "    stateId: SECTION_STATE_ID['06'], // TODO: map section 06/08/01/02/03 -> stateId ของ workflow version",
            "    approver: Number(approverUserId), // TODO: resolve จาก auth-backend group ตามโซน/ฝ่าย",
            "    seq: 1,",
            "    userId: Number(userId),",
            "  });",
            "",
        ]
    if "eventWorkflow" in kinds:
        lines += [
            "  // ตรวจก่อนว่า user มีสิทธิ์ยิง event นี้จริง (กันกดซ้ำ/กดข้ามคน)",
            "  const permitted = await this.workflow.getPermissionEvents({",
            "    versionId: this.versionId,",
            "    referenceId: docNo,",
            "    userData: { userId, userGroup: groupId },",
            "  });",
            "  // TODO: ตรวจว่า body.result map เป็น event ที่อยู่ใน permitted ก่อนเรียก eventWorkflow",
            "  await this.workflow.eventWorkflow({",
            "    versionId: this.versionId,",
            "    referenceId: docNo,",
            "    event, // TODO: map decision_code -> event ของ workflow definition",
            "    remark: body.comment,",
            "    userId: Number(userId),",
            "    nextApproverId, // TODO: ผู้อนุมัติขั้นถัดไป (undefined ได้ถ้า definition กำหนดเอง)",
            "  });",
            "",
        ]
    if "getPendingFlow" in kinds:
        lines += [
            "  // inbox งานค้าง — ใช้ร่วมกับ /api/workflow/pending ของ backlog เดิมได้",
            "  const pending = await this.workflow.getPendingFlowByUser({",
            "    userData: { userId: Number(userId), groupId: Number(groupId) },",
            "    versionId: this.versionId,",
            "  });",
            "  // TODO: join referenceId (= doc_no) กลับไปที่ sgi_compensation_documents เพื่อเติมข้อมูลเอกสาร",
            "",
        ]
    if "getHistory" in kinds:
        lines += [
            "  // timeline การเปลี่ยน state",
            "  const history = await this.workflow.getHistory({ versionId: this.versionId, referenceId: docNo });",
            "  // TODO: merge กับ sgi_consideration_logs (engine history ไม่มี decision_code/ไฟล์แนบ)",
            "",
        ]
    if "getTransaction" in kinds:
        lines += [
            "  // สถานะปัจจุบันของเอกสาร",
            "  const trx = await this.workflow.getTransaction({ versionId: this.versionId, referenceId: docNo });",
            "  // TODO: map currentState -> statusCode/statusName ที่ FE ใช้",
            "",
        ]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _entity_code(tname: str) -> str:
    cls = _entity_class(tname)
    hint = COLUMN_HINTS.get(tname)
    lines = [
        f"// src/entitys/{tname.replace('_', '-')}.entity.ts",
        "import { Column, Entity, PrimaryColumn } from 'typeorm';",
        "",
        f"@Entity({{ name: '{tname}', schema: process.env.DB_SCHEMA }})",
        f"export class {cls} {{",
    ]
    if not hint:
        lines += [
            "  @PrimaryColumn({ name: 'id', type: 'bigint' })",
            "  id: number;",
            "",
            f"  // TODO: เติมคอลัมน์ที่เหลือของ {tname} ตาม database.md (Canonical Column Contract)",
            "  //       และห้ามประกาศ relation — โมดูลนี้ join ด้วย raw SQL ตาม convention ของทีม",
        ]
    else:
        for col, ts, opts, is_pk in hint[1]:
            deco = "PrimaryColumn" if is_pk else "Column"
            lines.append(f"  @{deco}({{ name: '{col}', {opts} }})")
            optional = "?" if "nullable: true" in opts else ""
            lines.append(f"  {_camel(col)}{optional}: {ts};")
            lines.append("")
        lines.append("  // TODO: ตรวจความยาว/precision กับ DDL จริงใน sql/deploy-sgi-*.sql ก่อน merge")
        lines.append("  //       entity ชุดนี้ไม่ประกาศ relation ตาม convention (join ด้วย raw SQL)")
    lines.append("}")
    return "\n".join(lines)


def _providers_module_code(own: list[tuple[str, str, str]], slug: str, pascal: str, uses_wf: bool) -> str:
    entities = [t[0] for t in own][:3]
    if not entities:
        entities = ["sgi_compensation_documents"]
    imports = "\n".join(
        f"import {{ {_entity_class(t)} }} from '../../entitys/{t.replace('_', '-')}.entity';" for t in entities
    )
    provider_rows: list[str] = []
    for t in entities:
        token = t.upper().rstrip("S") + "_REPOSITORY" if not t.endswith("ies") else t.upper() + "_REPOSITORY"
        provider_rows += [
            "  {",
            f"    provide: '{token}',",
            f"    useFactory: (dataSource: DataSource) => dataSource.getRepository({_entity_class(t)}),",
            "    inject: ['DATA_SOURCE'],",
            "  },",
        ]
    provider_const = f"sgi{pascal}Providers"
    lines = [
        "// src/providers/sgi/sgi.ts — repository provider แบบ factory (ไม่ใช้ TypeOrmModule.forFeature)",
        "// convention ของโฟลเดอร์ providers คือ 1 ไฟล์ต่อโดเมน ตั้งชื่อตามโดเมน (business_user/business_user.ts,",
        "// common_code/common_code.ts …) ไม่ใช่ index.ts",
        "//",
        "// ⚠️ ไฟล์นี้ใช้ร่วมกันทุกเอกสาร BE ของ SGI — ให้ **merge array เพิ่ม** เข้าไฟล์เดิม ห้ามเขียนทับ",
        "//    (ชื่อ const แยกต่อเอกสารไว้แล้วเพื่อไม่ให้ชนกัน)",
        "import { DataSource } from 'typeorm';",
        imports,
        "",
        f"export const {provider_const} = [",
        *provider_rows,
        "];",
        "",
        f"// src/modules/sgi-{slug}/sgi-{slug}.module.ts",
        "import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';",
        "import { DatabaseModule } from '../../database/database.module';",
        "// UserContextMiddleware อ่าน header x-user-id แล้วเซ็ต request.userId ที่ @UserId() ใช้",
        "// — app.module.ts **ไม่ได้** apply แบบ global (มีแค่ HttpContext/LoggerContext) แต่ละโมดูลต้อง apply เอง",
        "// (ดู evaluation-process.module.ts / inform-evaluate.module.ts / cooperation-request.module.ts)",
        "import { UserContextMiddleware } from '../../common/middleware/user-context.middleware';",
    ]
    if uses_wf:
        lines.append("import { WorkflowModule } from '../workflow/workflow.module';")
    lines += [
        f"import {{ {provider_const} }} from '../../providers/sgi/sgi';",
        f"import {{ Sgi{pascal}Controller }} from './sgi-{slug}.controller';",
        f"import {{ Sgi{pascal}Service }} from './sgi-{slug}.service';",
        "",
        "@Module({",
        "  imports: [DatabaseModule" + (", WorkflowModule" if uses_wf else "") + "],",
        f"  controllers: [Sgi{pascal}Controller],",
        f"  providers: [Sgi{pascal}Service, ...{provider_const}],",
        f"  exports: [Sgi{pascal}Service],",
        "})",
        f"export class Sgi{pascal}Module implements NestModule {{",
        "  configure(consumer: MiddlewareConsumer) {",
        "    // ถ้าไม่ apply ตรงนี้ userId จะเป็น undefined เงียบ ๆ ทุก endpoint",
        f"    consumer.apply(UserContextMiddleware).forRoutes(Sgi{pascal}Controller);",
        "  }",
        "}",
        "// TODO: register module นี้ใน app.module.ts (imports) พร้อมกับโมดูล SGI ตัวอื่น",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# code blocks — BFF
# --------------------------------------------------------------------------------------
def _bff_client_code() -> str:
    return "\n".join([
        "// src/common/client-services/sgi-client.service.ts",
        "import { Injectable, Logger, OnModuleInit } from '@nestjs/common';",
        "import { BaseClientService } from './base-client.service';",
        "",
        "@Injectable()",
        "export class SgiClientService extends BaseClientService implements OnModuleInit {",
        "  protected logger: Logger = new Logger(SgiClientService.name);",
        "",
        "  onModuleInit() {",
        "    // TODO: ถ้า deploy SGI แยก service ให้เพิ่ม API_SGI_BACKEND_* ใน AppConfigService",
        "    //       ตอนนี้ชี้ store backend ตัวเดียวกับ StoreClientService",
        "    this.defaultHeaders[this.config.api.store.key.name] = this.config.api.store.key.value;",
        "    this.baseUrl = this.config.api.store.url;",
        "  }",
        "}",
        "// BaseClientService แกะ { success, data } ให้แล้ว — service ฝั่ง BFF จึงได้ data ตรง ๆ",
        "// TODO: เพิ่ม SgiClientService ใน providers/exports ของ ClientServiceModule (@Global)",
    ])


def _bff_code(endpoints: list[_Endpoint], slug: str, pascal: str) -> str:
    sample = endpoints[:3]
    lines = [
        f"// src/modules/sgi-{slug}/sgi-{slug}.service.ts (BFF)",
        "import { Injectable } from '@nestjs/common';",
        "import { SgiClientService } from '@common/client-services/sgi-client.service';",
        "",
        "@Injectable()",
        f"export class Sgi{pascal}BffService {{",
        "  constructor(private readonly client: SgiClientService) {}",
        "",
        "  // BFF ไม่มี DB — หน้าที่เดียวคือแนบ user context แล้ว forward",
        "  private userHeaders(user: any) {",
        "    return {",
        "      'x-user-id': user?.userId,",
        "      'x-user-group-id': user?.groupId,",
        "      'x-user-permissions': (user?.permissions ?? []).join(','),",
        "    };",
        "  }",
        "",
    ]
    for ep in sample:
        args = ["params: any", "user: any"] if ep.method == "GET" else ["body: any", "user: any"]
        path_expr = "'" + ep.path + "'"
        if ep.params:
            path_expr = "`" + re.sub(r"\{(\w+)\}", lambda m: "${" + _camel(m.group(1)) + "}", ep.path) + "`"
            args = [f"{_camel(x)}: string" for x in ep.params] + args
        lines.append(f"  {ep.handler}({', '.join(args)}) {{")
        if ep.method == "GET":
            lines.append(f"    return this.client.get({path_expr}, {{ params, headers: this.userHeaders(user) }});")
        elif ep.method == "DELETE":
            lines.append(f"    return this.client.delete({path_expr}, {{ headers: this.userHeaders(user) }});")
        else:
            verb = ep.method.lower()
            lines.append(f"    return this.client.{verb}({path_expr}, body, {{ headers: this.userHeaders(user) }});")
        lines.append("  }")
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    lines += [
        "}",
        "",
        f"// ---------- src/modules/sgi-{slug}/sgi-{slug}.controller.ts (BFF) ----------",
        "import { Body, Controller, Delete, Get, Param, Post, Put, Query, Req, UseGuards } from '@nestjs/common';",
        "import { AuthGuard } from '@nestjs/passport';",
        "",
        "// เลือก prefix แบบเดียวทั้งโมดูล: ใช้ '/bff/sgi/...' (ห้ามปนกับแบบไม่มี /bff)",
        f"@Controller('bff/sgi/{slug}')",
        "@UseGuards(AuthGuard('jwt'))",
        f"export class Sgi{pascal}BffController {{",
        f"  constructor(private readonly service: Sgi{pascal}BffService) {{}}",
    ]
    for ep in sample[:2]:
        deco = ep.method.capitalize() if ep.method != "DELETE" else "Delete"
        route = "/".join(ep.nest_segments[2:]) if len(ep.nest_segments) > 2 else "/".join(ep.nest_segments)
        args = [f"@Param('{x}') {_camel(x)}: string" for x in ep.params]
        call = [_camel(x) for x in ep.params]
        if ep.method == "GET":
            args.append("@Query() query: any")
            call.append("query")
        elif ep.method != "DELETE":
            args.append("@Body() body: any")
            call.append("body")
        args.append("@Req() req: any")
        call.append("req.user")
        lines += [
            "",
            f"  // proxy ของ {ep.method} {ep.path}",
            f"  @{deco}('{route}')",
            f"  {ep.handler}({', '.join(args)}) {{",
            f"    return this.service.{ep.handler}({', '.join(call)});",
            "  }",
        ]
    lines += [
        "}",
        "// TODO: register module ใน app.module.ts ของ BFF และเพิ่ม SgiClientService ใน ClientServiceModule (@Global)",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# SQL section
# --------------------------------------------------------------------------------------
def _sql_lookup(ctx: Any) -> dict[str, str]:
    if isinstance(ctx, dict):
        raw = ctx.get("sql_by_path")
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
    return {}


def _sql_for(ep: _Endpoint, sql_by_path: dict[str, str]) -> str | None:
    for key in (f"{ep.method} {ep.path}", f"{ep.method} /api/v1{ep.path}"):
        if key in sql_by_path:
            return sql_by_path[key]
    return None


_TABLE_TOKEN_RE = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-z_][a-z0-9_]*)", re.I)


def _sql_warnings(sql: str) -> list[str]:
    """คำเตือนที่ต้องแปะเหนือบล็อก SQL — SQL ตัวอย่างมาจาก `SQL_BY_PATH` (plan-api.html)
    ซึ่งบางเส้นยังเขียนไว้ก่อนมติ 2026-08-06/07 (34 -> 24 -> 22 -> 21 ตาราง)
    """
    lines: list[str] = []
    hit_tables: list[str] = []
    for m in _TABLE_TOKEN_RE.finditer(sql or ""):
        tname = m.group(1).lower()
        if tname in CUT_TABLE_REPLACEMENT and tname not in hit_tables:
            hit_tables.append(tname)
    if hit_tables:
        lines.append("-- ⚠️ SQL ตัวอย่างนี้ยังอ้างตารางที่ถูกตัดจาก target design 20 ตารางแล้ว")
        lines.append("--    ห้าม implement ตามตัวอักษร ให้แทนที่ก่อนใช้งาน:")
        for tname in hit_tables:
            lines.append(f"--      {tname}  ->  {CUT_TABLE_REPLACEMENT[tname]}")
    hit_cols = [old for old in CUT_COLUMN_ALIASES if old in (sql or "")]
    if hit_cols:
        lines.append("-- ⚠️ ชื่อคอลัมน์ต่อไปนี้ไม่ตรงกับ entity ที่หัวข้อ Entity ของเอกสารนี้ประกาศไว้:")
        for old in hit_cols:
            lines.append(f"--      {old}  ->  {CUT_COLUMN_ALIASES[old]}")
    if ":" in (sql or "") and re.search(r"(?<![:\w]):[a-zA-Z_][a-zA-Z0-9_]*", sql or ""):
        lines.append("-- ⚠️ SQL นี้ใช้ named parameter (:name) แต่ `dataSource.query()` ของ store-backend")
        lines.append("--    รับเฉพาะ positional $1..$n — ต้องแปลงเป็นลำดับ หรือรันผ่าน QueryBuilder")
    if lines:
        lines.append("")
    return lines


_ALIAS_RE = re.compile(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)(?:\s+(?:AS\s+)?([a-z][a-z0-9_]*))?", re.I)
_COND_RE = re.compile(r"\b([a-z][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\s*(?:=|>=|<=|>|<|IN\b|LIKE\b|BETWEEN\b)", re.I)
_SQL_KEYWORDS = {"on", "where", "group", "order", "left", "inner", "outer", "join", "using", "set", "and", "or", "as", "select"}


def _index_proposals(sqls: list[str], own_names: set[str]) -> list[list[str]]:
    alias: dict[str, str] = {}
    per_table: dict[str, list[str]] = {}
    for sql in sqls:
        try:
            for m in _ALIAS_RE.finditer(sql):
                tname, a = m.group(1).lower(), (m.group(2) or "").lower()
                if a in _SQL_KEYWORDS:
                    a = ""
                alias[a or tname] = tname
                alias.setdefault(tname, tname)
            for m in _COND_RE.finditer(sql):
                a, col = m.group(1).lower(), m.group(2).lower()
                tname = alias.get(a)
                if not tname or tname not in own_names:
                    continue
                cols = per_table.setdefault(tname, [])
                if col not in cols:
                    cols.append(col)
        except Exception:  # pragma: no cover - parser ต้องไม่ทำให้เอกสารพัง
            continue
    rows: list[list[str]] = []
    for tname, cols in per_table.items():
        hint = COLUMN_HINTS.get(tname)
        pk_cols = {c for c, _ts, _o, is_pk in hint[1] if is_pk} if hint else set()
        pick = [c for c in cols if c != "id" and c not in pk_cols][:3]
        if not pick:
            # ทุกคอลัมน์ที่ใช้กรองเป็น PK อยู่แล้ว — ไม่ต้องเสนอ index เพิ่ม
            continue
        idx = f"idx_{tname}_{'_'.join(pick)}"[:63]
        rows.append([
            tname,
            f"CREATE INDEX {idx} ON {tname} ({', '.join(pick)});",
            "ข้อเสนอ — อนุมานจากคอลัมน์ที่ปรากฏใน WHERE/JOIN ของ SQL ด้านบน ต้องวัด EXPLAIN ก่อนใช้จริง",
        ])
    return rows


def _fallback_index_proposals(own: list[tuple[str, str, str]]) -> list[list[str]]:
    presets = {
        "sgi_compensation_documents": "CREATE UNIQUE INDEX uk_compensation_documents_business ON sgi_compensation_documents (impacted_store_code, account_year, account_month, round_no);",
        "sgi_consideration_logs": "CREATE INDEX idx_consideration_logs_doc_no ON sgi_consideration_logs (doc_no, action_datetime DESC);",
        "sgi_document_attachments": "CREATE INDEX idx_document_attachments_doc_no ON sgi_document_attachments (doc_no, section_code);",
        "sgi_document_new_stores": "CREATE INDEX idx_document_new_stores_doc_no ON sgi_document_new_stores (doc_no);",
        "sgi_document_competitors": "CREATE INDEX idx_document_competitors_doc_no ON sgi_document_competitors (doc_no, source_system);",
        "sgi_document_external_factors": "CREATE INDEX idx_document_external_factors_doc_no ON sgi_document_external_factors (doc_no);",
        "sgi_sales_transactions": "CREATE INDEX idx_sales_transactions_summary ON sgi_sales_transactions (sales_summary_id, window_no, txn_date);",
        "sgi_fgi_impact_processes": "CREATE INDEX idx_fgi_impact_processes_gate ON sgi_fgi_impact_processes (workflow_generation_status, period_year, period_month);",
        "sgi_interface_transactions": "CREATE INDEX idx_interface_transactions_pending ON sgi_interface_transactions (data_name, status, sent_at);",
        "sgi_compensation_histories": "CREATE INDEX idx_compensation_histories_store ON sgi_compensation_histories (store_code, compensate_year, compensate_month);",
        "sgi_fgi_impact_sales_summaries": "CREATE INDEX idx_fgi_impact_sales_summaries_process ON sgi_fgi_impact_sales_summaries (impact_process_id);",
    }
    rows: list[list[str]] = []
    for tname, _rw, _usage in own:
        ddl = presets.get(tname)
        if ddl:
            rows.append([tname, ddl, "อนุมานจากเงื่อนไข query ที่เอกสารนี้ระบุ — สร้างพร้อมสคริปต์ deploy ของ SGI"])
    return rows


# --------------------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------------------
def be_skeleton_blocks(topic: Any, ctx: Any = None) -> list[dict[str, Any]]:
    """สร้าง block ส่วน "Skeleton Code" + "Database SQL" ของเอกสาร LLDD BE หนึ่งฉบับ.

    ทุกอย่าง data-driven จาก ``topic`` (apis / fields / db_tables) จึงต่างกันจริงตามเอกสาร
    ``ctx`` รองรับคีย์: ``sql_by_path`` (dict คีย์ ``"METHOD /api/v1<path>"``),
    ``skeleton_section`` และ ``sql_section`` (เลขหัวข้อ)
    """
    ctx = ctx if isinstance(ctx, dict) else {}
    sec_code = str(ctx.get("skeleton_section", "5.96"))
    sec_sql = str(ctx.get("sql_section", "5.97"))

    slug, pascal = _feature(topic)
    doc_name = str(getattr(topic, "file", "") or "").split("/")[-1]
    endpoints, external = _collect_endpoints(topic, doc_name)
    own, reused = _split_tables(topic)
    wf_plan = _workflow_plan(topic, endpoints, reused)
    uses_wf = bool(wf_plan)
    base = _controller_base(endpoints)
    dto_spec = _dto_spec(topic, endpoints, pascal, slug)
    sql_by_path = _sql_lookup(ctx)

    blocks: list[dict[str, Any]] = [
        h(2, f"{sec_code} Skeleton Code (store-backend + BFF)"),
        p(
            "โครงโค้ดตั้งต้นของเอกสารฉบับนี้ ยึด convention จริงของ "
            "`srm-sps-spsap-store-backend` (NestJS 11 + TypeORM, schema `sps_store`, custom provider "
            "`DATA_SOURCE` ที่ route SELECT ไป slave pool) และ `srm-sps-spsap-sbp-bff` "
            "(ไม่มี DB, forward ผ่าน client service). ทุกจุดที่ต้องเติมกำกับด้วย `// TODO:` "
            "และ response ทุกเส้นถูกห่อเป็น `{success, data}` โดย ResponseInterceptor อยู่แล้ว "
            "จึงห้าม service ห่อซ้ำ"
        ),
    ]

    # 1) ผังไฟล์
    if not endpoints:
        blocks.append(h(3, f"{sec_code}.1 ผังไฟล์ที่ต้องสร้าง"))
        blocks.append(p(
            "**เอกสารฉบับนี้ไม่ต้องสร้างไฟล์ใหม่** — ทุก endpoint ที่อยู่ในตาราง API เป็น contract กลาง "
            "หรือถูก implement ที่เอกสารอื่น/ระบบ SBP เดิมแล้ว (ดูตารางด้านล่าง) การสร้าง controller "
            "ซ้ำจะทำให้ NestJS มี 2 controller จอง route เดียวกันแล้ว register ตัวแรกชนะเงียบ ๆ"
        ))
        if external:
            blocks.append(table(["Endpoint", "จุดประสงค์", "implement ที่ไหน"], external))
        blocks.append(h(3, f"{sec_code}.2 สัญญากลางที่ต้องยึด"))
        blocks.append(code(
            "// src/common/interceptors/response.interceptor.ts (มีอยู่แล้ว — ห้ามห่อซ้ำใน service)\n"
            "// success : { success: true, data }\n"
            "// error   : { success: false, data: null, error: { code, message } }\n"
            "// TODO: endpoint ของ SGI ทุกเส้นต้องคืน error message ภาษาไทย verbatim ตาม SRS ผ่าน HttpException เท่านั้น",
            "ts",
        ))
        blocks.append(h(2, f"{sec_sql} Database SQL"))
        blocks.append(p("ไม่มี SQL เฉพาะของเอกสารนี้ — SQL ของแต่ละเส้นอยู่ในเอกสารเจ้าของ endpoint ตามตารางด้านบน"))
        return blocks

    file_rows: list[list[str]] = [
        [f"store-backend · src/modules/sgi-{slug}/sgi-{slug}.controller.ts",
         f"route ทั้งหมดของเอกสารนี้ ({len(endpoints)} เส้น) + `@UseGuards(HttpHeaderGuard)` + `@UserId()`"],
        [f"store-backend · src/modules/sgi-{slug}/sgi-{slug}.service.ts",
         "business logic — inject `'DATA_SOURCE'` แล้วยิง raw SQL, mutation ใช้ QueryRunner transaction"],
        [f"store-backend · src/modules/sgi-{slug}/sgi-{slug}.sql.ts",
         f"เก็บ SQL ต่อ endpoint (คัดจากหัวข้อ {sec_sql}) แยกออกจาก service ให้ทดสอบ/รีวิวง่าย"],
        [f"store-backend · src/modules/sgi-{slug}/dto/sgi-{slug}.dto.ts",
         "DTO + class-validator ตาม validation ในหัวข้อฟิลด์ของเอกสารนี้"],
        [f"store-backend · src/modules/sgi-{slug}/sgi-{slug}.module.ts",
         "ประกอบ controller/service/providers แล้ว register ที่ `app.module.ts`"],
    ]
    for tname, _rw, _usage in own[:3]:
        shared = " — **entity ร่วมหลายเอกสาร: ประกาศครั้งเดียวแล้วอ้างอิง อย่าสร้างซ้ำ**" \
            if tname in {"sgi_compensation_documents", "sgi_consideration_logs", "sgi_document_attachments"} else ""
        file_rows.append([
            f"store-backend · src/entitys/{tname.replace('_', '-')}.entity.ts",
            f"entity ของ `{tname}` (`@Entity({{schema: process.env.DB_SCHEMA}})`, ไม่ประกาศ relation){shared}",
        ])
    file_rows.append(["store-backend · src/providers/sgi/sgi.ts",
                      "repository provider แบบ factory ผูก token string กับ `DATA_SOURCE` — "
                      "**ไฟล์ร่วมของทุกเอกสาร BE ให้ merge array เพิ่ม ห้ามเขียนทับ**"])
    file_rows.append(["store-backend · sql/deploy-sgi-" + slug + ".sql",
                      "DDL production แบบ idempotent (ทีมนี้ไม่ใช้ migration เป็นหลัก)"])
    file_rows.append(["BFF · src/common/client-services/sgi-client.service.ts",
                      "client ต่อจาก `BaseClientService` ตั้ง baseUrl + `x-api-key` ตอน `onModuleInit`"])
    file_rows.append([f"BFF · src/modules/sgi-{slug}/sgi-{slug}.controller.ts",
                      "route ฝั่ง BFF prefix `/bff/sgi/…` + `@UseGuards(AuthGuard('jwt'))`"])
    file_rows.append([f"BFF · src/modules/sgi-{slug}/sgi-{slug}.service.ts",
                      "แนบ `x-user-id` / `x-user-group-id` / `x-user-permissions` แล้ว forward ไป backend"])
    blocks.append(h(3, f"{sec_code}.1 ผังไฟล์ที่ต้องสร้าง"))
    blocks.append(table(["Path", "หน้าที่"], file_rows))

    if external:
        blocks.append(p("เส้นที่ไม่ต้อง implement ใหม่ในเอกสารนี้:"))
        blocks.append(table(["Endpoint", "จุดประสงค์", "เหตุผล"], external))

    idx = 2
    # 2) controller
    blocks.append(h(3, f"{sec_code}.{idx} Controller (store-backend)"))
    idx += 1
    if endpoints:
        chunks = [endpoints[i : i + 4] for i in range(0, len(endpoints), 4)][:3]
        seen_dtos: set[str] = set()
        for n, chunk in enumerate(chunks, start=1):
            blocks.append(code(
                _controller_code(topic, slug, pascal, base, dto_spec, chunk, n, len(chunks), seen_dtos), "ts"))
        shown = sum(len(c) for c in chunks)
        if len(endpoints) > shown:
            blocks.append(p(f"(แสดง {shown} เส้นแรกจากทั้งหมด {len(endpoints)} เส้น — เส้นที่เหลือใช้รูปแบบเดียวกัน "
                            "และต้องประกาศครบทุกเส้นในไฟล์จริง)"))
    else:
        blocks.append(p("เอกสารนี้ไม่มี endpoint ที่ผูกกับ controller โดยตรง (เป็น contract กลาง/อ้างอิงระบบเดิม) "
                        "จึงไม่มี controller ใหม่ — ให้ยึด interceptor/filter/guard กลางที่มีอยู่แล้วแทน"))
        blocks.append(code(
            "// src/common/interceptors/response.interceptor.ts (มีอยู่แล้ว — ห้ามห่อซ้ำใน service)\n"
            "// success : { success: true, data }\n"
            "// error   : { success: false, data: null, error: { code, message } }\n"
            "// TODO: endpoint ของ SGI ทุกเส้นต้องคืน error message ภาษาไทย verbatim ตาม SRS ผ่าน HttpException เท่านั้น",
            "ts",
        ))

    # 3) DTO
    blocks.append(h(3, f"{sec_code}.{idx} DTO + Validation"))
    idx += 1
    for part in dto_spec["parts"]:
        blocks.append(code(part, "ts"))

    # 4) service
    blocks.append(h(3, f"{sec_code}.{idx} Service (inject `DATA_SOURCE` + raw SQL)"))
    idx += 1
    blocks.append(p("service ประกาศ method ครบทุกเส้นที่ controller เรียก และ **signature มาจากแหล่งเดียวกับ "
                    "controller** (จำนวน/ลำดับพารามิเตอร์จึงตรงกันเสมอ) — เส้นที่ยังไม่ได้ implement เป็น stub "
                    "ที่ `throw new NotImplementedException(...)` ให้ TypeScript compile ผ่านตั้งแต่วันแรก"))
    blocks.append(code(_service_code(topic, endpoints, own, slug, pascal, wf_plan, dto_spec), "ts"))

    # 5) workflow
    if uses_wf:
        blocks.append(h(3, f"{sec_code}.{idx} Workflow (`@srm/glb-workflow`)"))
        idx += 1
        blocks.append(p(
            "✅ **ชื่อ function ของ engine — ยึด LLDD ของ lib (ยืนยันแล้ว 2026-08-14)** · API จริงคือ 8 ตัวตามชีต `Detail` ของ `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` (เอกสารของ lib เอง): `initializeWorkflow` · `eventWorkflow` · `getPermissionEvents` · `getHistory` · `getTransaction` · `getPendingFlowByUser` · `getWorkflowsByUser` · `addPreApprover` · ชื่อที่เคยขัดกันไม่ใช่ชื่อ API — *Trigger Event* เป็นชื่อหัวข้อขั้นตอนภายใน `eventWorkflow` และ `*UseCase` เป็น class ที่ store-backend ห่อไว้ใช้เอง (ดู `LLDD-BE-Workflow-Engine-Definition` หัวข้อ 5.3)"
        ))
        blocks.append(table(["Endpoint", "Use case ที่ต้องเรียก", "เหตุผล"], wf_plan))
        blocks.append(code(_workflow_code(slug, pascal, wf_plan), "ts"))

    # 6) entity
    if own:
        blocks.append(h(3, f"{sec_code}.{idx} Entity (TypeORM)"))
        idx += 1
        for tname, _rw, _usage in own[:2]:
            blocks.append(code(_entity_code(tname), "ts"))
        if len(own) > 2:
            blocks.append(p("ตารางที่เหลือของเอกสารนี้ (" + ", ".join(f"`{t[0]}`" for t in own[2:]) +
                            ") ใช้รูปแบบ entity เดียวกัน — คอลัมน์อ้างจาก `database.md`"))
    if reused:
        blocks.append(p("ตารางที่ **ไม่ต้องสร้าง entity** เพราะใช้ของระบบเดิม/workflow engine:"))
        blocks.append(table(["Object", "R/W", "ใช้ของระบบเดิมตัวไหน"], [[t[0], t[1], t[2]] for t in reused]))

    # 7) providers + module
    blocks.append(h(3, f"{sec_code}.{idx} Repository Providers + Module wiring"))
    idx += 1
    blocks.append(code(_providers_module_code(own, slug, pascal, uses_wf), "ts"))

    # 8) BFF
    blocks.append(h(3, f"{sec_code}.{idx} BFF Proxy (module + controller + client service)"))
    idx += 1
    blocks.append(p("BFF ยังไม่มีฟีเจอร์ประกันรายได้เลย จึงต้องสร้าง module ใหม่ + client service ใหม่ทั้งชุด "
                    "และเลือก prefix แบบเดียวทั้งโมดูล (ที่นี่ใช้ `/bff/sgi/…`) เพื่อไม่ให้ปนแบบที่มี/ไม่มี `/bff` "
                    "เหมือนโมดูลเดิม"))
    blocks.append(code(_bff_client_code(), "ts"))
    blocks.append(code(_bff_code(endpoints, slug, pascal), "ts"))

    # ---------------- Database SQL ----------------
    blocks.append(h(2, f"{sec_sql} Database SQL"))
    blocks.append(h(3, f"{sec_sql}.1 ตารางที่อ่าน/เขียน"))
    if own or reused:
        rows = [[t[0], t[1], t[2]] for t in own] + [[t[0], t[1], "ใช้ของระบบเดิม: " + t[2]] for t in reused]
        blocks.append(table(["Table / Object", "R/W", "Usage"], rows))
    else:
        blocks.append(p("เอกสารนี้ไม่ระบุตารางที่ใช้โดยตรง — ให้ยึด DB Mapping ของ LLDD ที่เกี่ยวข้อง"))

    blocks.append(h(3, f"{sec_sql}.2 SQL จริงต่อ Endpoint"))
    used_sqls: list[str] = []
    matched = 0
    for ep in endpoints:
        sql = _sql_for(ep, sql_by_path)
        if not sql:
            continue
        matched += 1
        blocks.append(p(f"**{ep.method} {ep.path}** — {_clip(ep.purpose, 110)}"))
        warn = _sql_warnings(sql)
        blocks.append(code("\n".join(warn) + sql if warn else sql, "sql"))
        used_sqls.append(sql)
    if matched == 0:
        blocks.append(p("ยังไม่มี SQL ตัวอย่างที่ผูกกับ endpoint ของเอกสารนี้ใน `SQL_BY_PATH` (`plan-api.html`) "
                        "— ให้เพิ่มที่นั่นก่อน แล้วเอกสารจะดึงมาแสดงอัตโนมัติ (ห้ามเขียน SQL ใหม่ในเอกสารนี้)"))
    elif matched < len(endpoints):
        blocks.append(p(f"(มี SQL ตัวอย่าง {matched} จาก {len(endpoints)} เส้น — เส้นที่เหลือยังไม่ถูกกำหนดใน `SQL_BY_PATH`)"))

    blocks.append(h(3, f"{sec_sql}.3 Index / Constraint ที่ควรมี (ข้อเสนอ)"))
    own_names = {t[0] for t in own}
    proposals = _index_proposals(used_sqls, own_names) if used_sqls else []
    if not proposals:
        proposals = _fallback_index_proposals(own)
    if proposals:
        blocks.append(table(["Table", "DDL ที่เสนอ", "ที่มา / หมายเหตุ"], proposals))
        blocks.append(p("ทั้งหมดเป็น **ข้อเสนอ** ไม่ใช่ข้อกำหนดจาก SRS — ให้ตรวจกับ `EXPLAIN ANALYZE` บนข้อมูลจริง "
                        "และรวมเข้าไฟล์ `sql/deploy-sgi-*.sql` แบบ idempotent (`CREATE INDEX IF NOT EXISTS`) "
                        "ตาม pattern ที่ทีมใช้อยู่"))
    else:
        blocks.append(p("ยังไม่มีข้อมูลเงื่อนไข query พอจะเสนอ index — รอ SQL ต่อ endpoint ครบก่อน"))
    return blocks
