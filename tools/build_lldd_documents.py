from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
from datetime import date, timedelta
from html import escape
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Image as PdfImage,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from build_integrated_srs import target_job


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "LLDD"
LEGACY_JAVA_ROOT = ROOT.parent / "fcsJar"
FORMAT_DIRS = {"md": "md", "docx": "word", "pdf": "pdf"}
IMG = ROOT / "output/srs/screenshots/full"
SLICE = ROOT / "output/srs/screenshots/slices"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
LLDD_START_DATE = date(2026, 7, 29)
LLDD_END_DATE = date(2026, 8, 27)
WORKDAYS_PER_WEEK = 5
HOURS_PER_DAY = 6
HOURS_PER_WEEK = WORKDAYS_PER_WEEK * HOURS_PER_DAY
MIN_WORK_WEEKS_EXCLUSIVE = 3.0
MAX_WORK_WEEKS = 4.5
FE_OWNER_KITTISAK = "Kittisak <New> Kaeowika"
FE_OWNER_PEERAKORN = "Peerakorn <Pete> Sakunkaewphithak"
FE_OWNER = "Chidchanok <lin> Saengamnat"
BANK_BE_OWNER = "Aphiwit <Bank> Khammoon"
BE_OWNER = "Tunyatorn <Vava> Kiatkongphongsa"
BE_OWNER_BUTSABA = "Butsaba <But> Podamrong"
ATTACHMENT_ALLOWED_EXTENSIONS = "vsd, dwg, afp, pdf, mda, zip, wav, mp3, gif, jpg, tif, tiff, htm, html, txt, xml, mpg, mov, ivs, doc, docx, xls, xlsx, pps, ppt, pot, csv"
JOB_ESTIMATES: dict[str, int] = {
    "1": 13,
    "2": 13,
    "3": 10,
    "4": 13,
    "5": 13,
    "6": 15,
    "7": 10,
    "8": 13,
    "8b": 10,
    "9": 10,
    "10": 9,
}

HIGH_LEVEL_ESTIMATES: dict[str, int] = {
    "FE/LLDD-FE-Integration-Contracts": 18,
    "FE/LLDD-FE-Foundation": 42,
    "FE/LLDD-FE-Overview": 39,
    "FE/LLDD-FE-Document-Lists": 42,
    "FE/LLDD-FE-Create-Document": 30,
    "FE/LLDD-FE-Document-Detail": 72,
    "FE/LLDD-FE-Report": 30,
    "FE/LLDD-FE-Master-Config": 30,
    "FE/LLDD-FE-Batch-Monitor": 24,
    "FE/LLDD-FE-Email-Template": 21,
    "FE/LLDD-FE-Testing-Delivery": 24,
    "BE/LLDD-BE-API-Common-Contracts": 15,
    "BE/LLDD-BE-API-Dashboard-Summary": 18,
    "BE/LLDD-BE-API-Document-List-Search": 21,
    "BE/LLDD-BE-API-Document-Create-Update": 27,
    "BE/LLDD-BE-API-Document-Detail-Aggregate": 27,
    "BE/LLDD-BE-API-Document-Workflow-Actions": 24,
    "BE/LLDD-BE-API-Workflow-Instances": 21,
    "BE/LLDD-BE-API-Attachment-Sales-Timeline": 21,
    "BE/LLDD-BE-API-Lookup-RBAC-Email": 30,
    "BE/LLDD-BE-API-Report-Master-Config": 30,
    "BE/LLDD-BE-Job-Batch-Email-SRM": 24,
}


@dataclass
class ApiSpec:
    method: str
    path: str
    purpose: str
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    buttons: list[str] = field(default_factory=list)


@dataclass
class Topic:
    file: str
    title: str
    track: str
    days: float
    hours: int
    owner: str
    objective: str
    screenshots: list[str]
    scope: list[str]
    fields: list[tuple[str, str, str, str]]
    actions: list[tuple[str, str, str, str]]
    apis: list[ApiSpec]
    flow: list[str]
    acceptance: list[str]
    tests: list[str]
    db_tables: list[tuple[str, str, str]] = field(default_factory=list)
    flow_diagram: str | None = None


def p(text: str) -> dict[str, Any]:
    return {"type": "p", "text": text}


def h(level: int, text: str) -> dict[str, Any]:
    return {"type": f"h{level}", "text": text}


def bullets(items: list[str]) -> dict[str, Any]:
    return {"type": "bullets", "items": items}


def table(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}


def image(path: str, caption: str) -> dict[str, Any]:
    return {"type": "image", "path": path, "caption": caption}


def code(text: str, lang: str = "") -> dict[str, Any]:
    return {"type": "code", "text": text, "lang": lang}


def payload(title: str, text: str) -> dict[str, Any]:
    return {"type": "payload", "title": title, "text": text}


def pagebreak() -> dict[str, Any]:
    return {"type": "pagebreak"}


LEGACY_JOB_SOURCES: dict[str, dict[str, Any]] = {
    "1": {
        "input": "QSSI score files from configured SFTP/import paths plus common-code category mapping.",
        "progress": "download/find files, parse pipe-delimited records, stage temp rows, map category scores, delete existing period/category rows, insert final scores, backup source files, send status mail.",
        "output": "FCS_QSSI_SCORE refreshed for the target period/category set; temp rows cleared; run summary contains file name, success/fail status, record count, and error detail.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fcs/main/ImportQSSI.java", "31-246", "Legacy main entrypoint, SFTP/file orchestration, backup, and success/fail email."],
            ["fcsJar/src/th/co/gosoft/fcs/controller/ImportQSSIController.java", "55-212, 456-481", "Read QSSI files, map rows to score models, delete/insert score data in batches."],
            ["fcsJar/src/th/co/gosoft/fcs/dao/jdbc/ImportQSSIScoreJdbc.java", "17-77", "Insert/delete/query FCS_QSSI_SCORE and FCS_TMP_QSSI_SCORE."],
        ],
    },
    "2": {
        "input": "Period year/month, optional zone filter, and ALLMAP SEVEN_IMPACT_VIEW rows.",
        "progress": "query candidate impacted stores, deduplicate by store/month, batch insert impact-store master data, derive related new-store/impact-store records, update verification flags.",
        "output": "FGI_IMPACT_STORE and related impact/new-store tables contain imported candidates for the requested period with duplicate-safe status.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ImportImpactStore.java", "24-186", "Legacy main entrypoint for impacted-store import."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportStoreJdbc.java", "30-84, 170-484", "Query SEVEN_IMPACT_VIEW and insert/update FGI impact/new-store records."],
        ],
    },
    "3": {
        "input": "Period year/month and competitor impact data from ALLMAP COMPETITOR_IMPACT_VIEW.",
        "progress": "validate period, skip when period already exists, query competitor view, insert in chunks inside a transaction, send status mail.",
        "output": "FGI_IMPACT_COMPETITOR rows for the target period; run status is success/no-data/failed with inserted-count reconciliation.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ImportImpactCompetitor.java", "16-48", "Legacy main entrypoint and notification wrapper."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ImportController.java", "483-598", "Validate params, skip duplicates, query source, chunk insert competitors."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportJdbc.java", "200-241", "Count existing period, query COMPETITOR_IMPACT_VIEW, insert FGI_IMPACT_COMPETITOR."],
        ],
    },
    "4": {
        "input": "FGI_IMPACT_STORE_SALES rows waiting for IAS sales data and export file/SFTP parameters.",
        "progress": "query eligible stores, write outbound IAS request file, upload to SFTP, backup file, record success/failure and notification.",
        "output": "IAS request file containing store/open-date pairs; run history includes generated file name and exported row count.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/PrepareImpactStoreToIAS.java", "28-243", "Legacy main entrypoint, file generation, upload, backup, notification."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportStoreJdbc.java", "99-115", "Query FGI_IMPACT_STORE_SALES rows eligible for IAS request."],
        ],
    },
    "5": {
        "input": "IAS sales response files from configured source path; file name pattern and pipe-delimited daily sales records.",
        "progress": "scan files, validate pattern, parse daily sales windows, derive before/after impact metrics, write transaction rows, update working-day counts and growth status, backup processed files.",
        "output": "FGI_IMPACT_STORE_SALES_TRN and FGI_IMPACT_STORE_SALES updated; confirm-receive rows written; source file moved to backup or error recorded.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ImportImpactSaleFromIAS.java", "9-19", "Legacy main entrypoint that delegates to import controller."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ImportController.java", "101-411", "Parse IAS file, compute sales windows, prepare inserts/updates, backup and notify."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportJdbc.java", "136-182, 517-804", "Update verification flags, working days, growth-rate calculations, cleanup old files."],
        ],
    },
    "6": {
        "input": "Approved/initial compensation data from FGI impact/new-store tables plus QSSI score lookup and FS export configuration.",
        "progress": "query rows for FS, generate compensation interface payload, insert/update compensate records, upload/export, backup, notify.",
        "output": "FS outbound data and FGI compensation tables synchronized; run summary includes exported counts and file/status.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ExportImpactStoreToFS.java", "19-68", "Legacy main entrypoint for exporting impact-store compensation to FS."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "119-180, 386-970", "Query FS export data and insert/update impact/new-store compensation records."],
        ],
    },
    "7": {
        "input": "FGI_IMPACT_COMPETITOR rows linked to active impact-process records and BPM/export confirmation state.",
        "progress": "query latest competitor rows, skip already-confirmed transactions, create outbound payload per competitor, upload/export, insert confirm-receive rows.",
        "output": "Competitor sync payload/output for downstream workflow; confirm-receive rows prevent duplicate export.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ExportCompetitor.java", "9-20", "Legacy main entrypoint for competitor export."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ExportController.java", "659-760", "Query competitor data, generate file content, upload, backup, notification."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1596-1628", "Query latest competitor rows eligible for export."],
        ],
    },
    "8": {
        "input": "Impact-store compensation rows in initial status with workflow sequence values and no prior confirm-receive output.",
        "progress": "update BPM sequence, query eligible impact-store rows, refresh not-OPT data, generate workflow payload, insert confirm-receive rows, upload/export, notify.",
        "output": "Impact-store workflow create payload/output with generated sequence numbers and duplicate guard.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ExportImpactStoreFlowToBPM.java", "9-17", "Legacy main entrypoint for exporting impact-store flow data."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ExportController.java", "518-657", "Build impact-store BPM payload, write file, upload, backup, notification."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1654-1692", "Query impact-store rows eligible for workflow export."],
        ],
    },
    "8b": {
        "input": "Impact-store rows waiting to start workflow plus generated workflow/document identifiers.",
        "progress": "select waiting rows, start workflow instance, update generated-flow flag per transaction, log success/failure.",
        "output": "Workflow instances started and source rows marked generated; failed rows remain rerunnable with error detail.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/StartK2WorkFlow.java", "16-51", "Legacy main entrypoint for starting K2 workflow."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/StartFlowJdbc.java", "17-173", "Select rows for workflow start and update generated-flow flags."],
        ],
    },
    "9": {
        "input": "New-store compensation rows linked to active impact-process records, plus BPM/export SFTP parameters.",
        "progress": "query eligible new-store rows, filter process errors, write outbound new-store payload, insert confirm-receive rows, upload/export, backup, notify.",
        "output": "New-store sync payload/output and confirm-receive rows keyed by NEW_STORE_INFO_ID/month/year.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ExportOpenStore.java", "1-22", "Legacy main entrypoint; constant job name is ExportNewStoreToBPM."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ExportController.java", "404-516, 893-961", "Query new stores, create payload content, upload, backup, notification."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1558-1594", "Query new-store rows eligible for export."],
        ],
    },
    "10": {
        "input": "FGI_CONFIRM_RECEIVE_DATA rows without return_code after the waiting threshold.",
        "progress": "query missing receive data, group by data_name/interface_type, build notification message, send admin mail, close run.",
        "output": "Notification sent for overdue receive confirmations; run status records grouped counts or no-data success.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/NotifyNoReceiveData.java", "16-37", "Legacy main entrypoint for missing-receive notification."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ManageCompensateController.java", "748-775", "Build and send notification content for missing receive data."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1894-1917", "Query confirm-receive rows without return_code."],
        ],
    },
}


JOB_IMPLEMENTATION_SPECS: dict[str, dict[str, str]] = {
    "1": {
        "repository": "qssiScoreRepository",
        "read": """SELECT store_code, category_code, score_period, score_value, source_checksum
FROM fcs_qssi_scores
WHERE score_period = :score_period
ORDER BY store_code, category_code;""",
        "write": """INSERT INTO fcs_qssi_scores
    (store_code, category_code, score_period, score_value, source_file_name, source_checksum, updated_at)
VALUES (:store_code, :category_code, :score_period, :score_value, :source_file_name, :source_checksum, CURRENT_TIMESTAMP)
ON CONFLICT (store_code, category_code, score_period)
DO UPDATE SET score_value = EXCLUDED.score_value,
              source_file_name = EXCLUDED.source_file_name,
              source_checksum = EXCLUDED.source_checksum,
              updated_at = CURRENT_TIMESTAMP;""",
        "idempotency": "SHA-256 ของไฟล์ + UNIQUE(store_code, category_code, score_period); checksum เดิมให้ SKIP โดยไม่ลบข้อมูลเดิม",
        "transaction": "parse/validate นอก transaction; upsert คะแนนทั้งไฟล์และบันทึก interface tracking ใน transaction เดียว",
        "security": "credential อ่านด้วย secretRef=secret/sbpgi/interfaces/qssi; SFTP บังคับ strict host-key verification จาก known_hosts และห้ามเก็บ password/private key ใน job_configs",
        "steps": "downloadAndVerifyQssiFiles|parseQssiFiles|upsertScores|archiveInboundFiles",
    },
    "2": {
        "repository": "impactStoreRepository",
        "read": """SELECT impacted_store_code, new_store_code, impact_month, distance_km, region_code, zone_code, branch_type
FROM allmap_seven_impact_view
WHERE impact_month = :impact_month
  AND (:zone_code IS NULL OR zone_code = :zone_code)
  AND distance_km <= CASE
        WHEN region_code = ANY(:bangkok_metro_region_codes) THEN 1.000
        ELSE 2.000
      END;""",
        "write": """INSERT INTO fgi_impact_stores
    (impact_process_id, impacted_store_code, new_store_code, impact_month, distance_km, updated_at)
VALUES (:impact_process_id, :impacted_store_code, :new_store_code, :impact_month, :distance_km, CURRENT_TIMESTAMP)
ON CONFLICT (impacted_store_code, new_store_code, impact_month)
DO UPDATE SET distance_km = EXCLUDED.distance_km,
              impact_process_id = EXCLUDED.impact_process_id,
              updated_at = CURRENT_TIMESTAMP;""",
        "idempotency": "UNIQUE(impacted_store_code, new_store_code, impact_month); rerun อัปเดตค่าที่เปลี่ยนแต่ไม่สร้างคู่ร้านซ้ำ",
        "transaction": "สร้าง/หา fgi_impact_processes และ upsert candidate ทีละ chunk ใน transaction; chunk fail rollback เฉพาะ chunk",
        "security": "ALLMAP connection ใช้ datasource secretRef และ TLS verify-full; job parameter เก็บได้เฉพาะ datasource alias ไม่เก็บ username/password",
        "steps": "loadAllmapCandidates|resolveImpactProcesses|upsertImpactPairs|reconcileImportedPairs",
    },
    "3": {
        "repository": "impactCompetitorRepository",
        "read": """SELECT impact_process_id, competitor_code, name_th, branch_th, opened_date, closed_date, period_key
FROM allmap_competitor_impact_view
WHERE period_key = :period_key;""",
        "write": """INSERT INTO fgi_impact_competitors
    (impact_process_id, competitor_code, name_th, branch_th, opened_date, closed_date, period_key, updated_at)
VALUES (:impact_process_id, :competitor_code, :name_th, :branch_th, :opened_date, :closed_date, :period_key, CURRENT_TIMESTAMP)
ON CONFLICT (impact_process_id, competitor_code, period_key)
DO UPDATE SET name_th = EXCLUDED.name_th,
              branch_th = EXCLUDED.branch_th,
              opened_date = EXCLUDED.opened_date,
              closed_date = EXCLUDED.closed_date,
              updated_at = CURRENT_TIMESTAMP;""",
        "idempotency": "UNIQUE(impact_process_id, competitor_code, period_key); source row ซ้ำในไฟล์/วิวต้อง deduplicate ก่อน upsert",
        "transaction": "validate งวดก่อนอ่าน; upsert ทีละ chunk และ commit หลัง reconcile จำนวน input/success/reject ของ chunk ตรงกัน",
        "security": "ALLMAP datasource ใช้ secretRef และ TLS verify-full; จำกัด DB user เป็น SELECT เฉพาะ source view",
        "steps": "loadCompetitorPeriod|deduplicateCompetitors|upsertCompetitors|reconcileCompetitorCount",
    },
    "4": {
        "repository": "iasRequestRepository",
        "read": """SELECT s.id, s.impact_process_id, s.impacted_store_code, s.new_store_code, s.impact_month
FROM fgi_impact_stores s
WHERE s.sales_request_status = 'W'
ORDER BY s.id
FOR UPDATE SKIP LOCKED;""",
        "write": """UPDATE fgi_impact_stores
SET sales_request_status = 'P', updated_at = CURRENT_TIMESTAMP
WHERE id = ANY(:impact_store_ids) AND sales_request_status = 'W';

INSERT INTO interface_transactions
    (run_id, data_name, direction, status, impact_process_id, business_key, period_key,
     file_name, file_checksum, outbox_status, purge_after)
SELECT :run_id, 'IAS_SALES_REQUEST', 'OUT', 'READY', impact_process_id,
       impacted_store_code || ':' || new_store_code, impact_month,
       :file_name, :file_checksum, 'READY', CURRENT_TIMESTAMP + INTERVAL '180 days'
FROM fgi_impact_stores
WHERE id = ANY(:impact_store_ids)
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;""",
        "idempotency": "ชื่อไฟล์ deterministic จาก period+runId และ UNIQUE(data_name,direction,business_key,period_key); outbox retry ใช้ transaction เดิม ไม่สร้าง request ซ้ำ",
        "transaction": "สร้างไฟล์ temp, fsync, atomic rename และคำนวณ checksum ให้สำเร็จก่อน; จากนั้น transaction เดียว lock W, update W→P และ insert outbox READY; ห้าม commit W→P ก่อนมี durable file",
        "security": "IAS SFTP credential ใช้ secretRef=secret/sbpgi/interfaces/ias; strict known_hosts, modern cipher, timeout และห้าม editable password/private key",
        "steps": "lockWaitingSalesRequests|writeDurableIasFile|markPendingAndCreateOutbox|dispatchIasOutbox",
    },
    "5": {
        "repository": "iasSalesRepository",
        "read": """SELECT t.sales_summary_id, t.txn_date, t.sales_amount, t.window_no, t.source_checksum
FROM sales_transactions t
JOIN fgi_impact_sales_summaries s ON s.id = t.sales_summary_id
WHERE s.impact_process_id = :impact_process_id
ORDER BY t.sales_summary_id, t.txn_date, t.window_no;""",
        "write": """INSERT INTO sales_transactions
    (sales_summary_id, txn_date, window_no, sales_amount, sales_diff, is_outlier, source_checksum)
VALUES (:sales_summary_id, :txn_date, :window_no, :sales_amount, :sales_diff, :is_outlier, :source_checksum)
ON CONFLICT (sales_summary_id, txn_date, window_no)
DO UPDATE SET sales_amount = EXCLUDED.sales_amount,
              sales_diff = EXCLUDED.sales_diff,
              is_outlier = EXCLUDED.is_outlier,
              source_checksum = EXCLUDED.source_checksum;

UPDATE fgi_impact_sales_summaries
SET total_working_days = :total_working_days,
    growth_rate_before = :growth_rate_before,
    growth_rate_after = :growth_rate_after,
    growth_rate_diff = :growth_rate_diff,
    sales_status = :sales_status,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :sales_summary_id;""",
        "idempotency": "checksum กันไฟล์ซ้ำ + UNIQUE(sales_summary_id,txn_date,window_no); คำนวณ summary ใหม่จาก transaction rows ทุก rerun",
        "transaction": "upsert รายวันและ update summary ของ sales_summary_id เดียวกันใน transaction; checksum/file tracking commit พร้อมกัน",
        "security": "IAS inbound SFTP ใช้ secretRef, strict known_hosts และ quarantine ไฟล์ที่ checksum/รูปแบบไม่ผ่านก่อน parse",
        "steps": "downloadAndStageIasSales|validateSalesWindows|upsertDailySales|recalculateSalesSummaries",
    },
    "6": {
        "repository": "statementExportRepository",
        "read": """SELECT d.doc_no, d.impact_process_id, s.id AS sales_summary_id,
       d.total_compensation_amount, q.score_value
FROM compensation_documents d
JOIN fgi_impact_sales_summaries s ON s.impact_process_id = d.impact_process_id
LEFT JOIN fcs_qssi_scores q ON q.store_code = d.impacted_store_code AND q.score_period = d.impact_month
JOIN LATERAL (
    SELECT c.result_category
    FROM consideration_logs c
    WHERE c.doc_no = d.doc_no
    ORDER BY c.action_datetime DESC
    LIMIT 1
) latest_decision ON latest_decision.result_category = 'APPROVE'
WHERE d.status_code = '99'
  AND NOT EXISTS (
      SELECT 1 FROM interface_transactions i
      WHERE i.data_name = 'COMPENSATE_APPROVE_I' AND i.direction = 'OUT'
        AND i.doc_no = d.doc_no AND i.status IN ('READY','SENT','ACKED'));""",
        "write": """INSERT INTO interface_transactions
    (run_id, data_name, direction, status, doc_no, impact_process_id, sales_summary_id,
     business_key, period_key, file_name, file_checksum, outbox_status, purge_after)
VALUES (:run_id, 'COMPENSATE_APPROVE_I', 'OUT', 'READY', :doc_no, :impact_process_id,
        :sales_summary_id, :doc_no, :period_key, :file_name, :file_checksum, 'READY',
        CURRENT_TIMESTAMP + INTERVAL '365 days')
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;

WITH purge_candidates AS (
    SELECT id
    FROM interface_transactions
    WHERE data_name = ANY(:purge_data_names)
      AND status IN ('ACKED','COMPLETED')
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
    ORDER BY id
    LIMIT :purge_batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;""",
        "idempotency": "UNIQUE(data_name,direction,business_key,period_key); STA ACK เปลี่ยน transaction เดิมเป็น ACKED ไม่ insert แถวใหม่",
        "transaction": "สร้าง payload/checksum ก่อน แล้ว insert outbox READY; dispatcher ส่งและเปลี่ยน SENT แยก transaction; callback ACK เปลี่ยน ACKED แบบ compare-and-set",
        "security": "STA endpoint/SFTP ใช้ secretRef=secret/sbpgi/interfaces/sta, TLS 1.2+ verify-full หรือ strict known_hosts; certificate/key rotation ไม่ต้องแก้เอกสารหรือ job param",
        "steps": "loadApprovedCompensations|buildStatementPayload|enqueueStatementOutbox|purgeAcknowledgedTracking",
    },
    "7": {
        "repository": "documentCompetitorRepository",
        "read": """SELECT d.doc_no, c.competitor_code, c.name_th, c.branch_th, c.opened_date, c.closed_date
FROM fgi_impact_competitors c
JOIN compensation_documents d ON d.impact_process_id = c.impact_process_id
WHERE c.period_key = :period_key;""",
        "write": """INSERT INTO document_competitors
    (doc_no, competitor_code, name_th, branch_th, opened_date, closed_date, source_system, updated_at)
VALUES (:doc_no, :competitor_code, :name_th, :branch_th, :opened_date, :closed_date, 'ALLMAP', CURRENT_TIMESTAMP)
ON CONFLICT (doc_no, competitor_code)
DO UPDATE SET name_th = EXCLUDED.name_th, branch_th = EXCLUDED.branch_th,
              opened_date = EXCLUDED.opened_date, closed_date = EXCLUDED.closed_date,
              updated_at = CURRENT_TIMESTAMP;

DELETE FROM document_competitors dc
WHERE dc.doc_no = :doc_no
  AND dc.source_system = 'ALLMAP'
  AND NOT EXISTS (
      SELECT 1
      FROM fgi_impact_competitors src
      JOIN compensation_documents d ON d.impact_process_id = src.impact_process_id
      WHERE d.doc_no = dc.doc_no
        AND src.period_key = :period_key
        AND src.competitor_code = dc.competitor_code
  );""",
        "idempotency": "UNIQUE(doc_no,competitor_code); upsert และ prune เฉพาะ source_system=ALLMAP ให้ target ตรง source ปัจจุบันโดยไม่ลบแถว USER",
        "transaction": "upsert + prune document_competitors และ tracking INTERNAL_DB_WRITE ใน transaction เดียวต่อ doc_no",
        "security": "service account ภายในมีสิทธิ์ SELECT source และ INSERT/UPDATE target เท่านั้น; ไม่มี external credential",
        "steps": "loadLatestDocumentCompetitors|upsertDocumentCompetitors|recordInternalCompetitorSync|reconcileDocumentCompetitors",
    },
    "8": {
        "repository": "compensationDocumentRepository",
        "read": """SELECT p.id AS impact_process_id, p.impacted_store_code, p.impact_month,
       SUM(COALESCE(s.adjust_compensation_amount, s.forecast_compensation_amount, 0)) AS total_compensation_amount
FROM fgi_impact_processes p
JOIN fgi_impact_stores s ON s.impact_process_id = p.id
WHERE p.process_status = 'READY_DOCUMENT'
GROUP BY p.id, p.impacted_store_code, p.impact_month;""",
        "write": """INSERT INTO compensation_documents
    (doc_no, be_year, running_no, impact_process_id, impacted_store_code, impact_month,
     source, status_code, current_section_code, total_compensation_amount, created_by)
VALUES (:doc_no, :be_year, :running_no, :impact_process_id, :impacted_store_code, :impact_month,
        'FS', '06', '06', :total_compensation_amount, 'JOB-8')
ON CONFLICT (impact_process_id) DO NOTHING;

INSERT INTO interface_transactions
    (run_id, data_name, direction, status, impact_process_id, doc_no,
     business_key, period_key, outbox_status, purge_after, completed_at)
SELECT :run_id, 'DOCUMENT_CREATE', 'INTERNAL', 'COMPLETED', d.impact_process_id, d.doc_no,
       CAST(d.impact_process_id AS VARCHAR), d.impact_month, 'COMPLETED',
       CURRENT_TIMESTAMP + INTERVAL '365 days', CURRENT_TIMESTAMP
FROM compensation_documents d
WHERE d.impact_process_id = :impact_process_id
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;""",
        "idempotency": "UNIQUE(impact_process_id) และ UNIQUE(be_year,running_no); lock running number ต่อปีใน transaction; conflict ต้องคืน/อ้าง doc_no เดิม และยอมให้เลขที่จองกระโดดโดยห้าม reuse",
        "transaction": "lock เลขรัน + insert document + update process + INTERNAL_DB_WRITE tracking ใน transaction เดียว",
        "security": "internal service account เท่านั้น; ห้ามสร้างไฟล์ BPM06001O, ห้าม SFTP และห้ามเก็บ K2 credential",
        "steps": "loadDocumentCandidates|allocateDocumentNumbers|createCompensationDocuments|recordDocumentCreation",
    },
    "8b": {
        "repository": "workflowRepository",
        "read": """WITH locked_process AS (
    SELECT p.id
    FROM fgi_impact_processes p
    JOIN compensation_documents d ON d.impact_process_id = p.id
    WHERE p.workflow_generation_status = 'W'
      AND NOT EXISTS (SELECT 1 FROM workflow_instances w WHERE w.doc_no = d.doc_no)
    ORDER BY p.id
    FOR UPDATE OF p SKIP LOCKED
), gate AS (
    SELECT p.id AS impact_process_id, d.doc_no, d.current_section_code,
           CASE
             WHEN BOOL_OR(ns.branch_type IS NULL OR ns.branch_type NOT IN ('FAM','FB1','FC1','FB2','FVB','FVC')) THEN 'N'
             WHEN BOOL_OR(pair.distance_km > CASE
                    WHEN impacted.region_code = ANY(:bangkok_metro_region_codes) THEN 1.000
                    ELSE 2.000
                  END) THEN 'N'
             WHEN ist.opt_dv_user_id IS NULL OR BTRIM(ist.opt_dv_user_id) = '' THEN 'W'
             WHEN impacted.juristic_name IS NULL OR BOOL_OR(ns.juristic_name IS NULL) THEN 'W'
             WHEN BOOL_OR(impacted.juristic_name = ns.juristic_name) THEN 'W'
             WHEN ss.growth_rate_diff IS NULL OR ss.growth_rate_diff > -10 THEN 'W'
             WHEN ss.sales_status NOT IN ('Y','N') THEN 'W'
             ELSE 'Y'
           END AS gate_decision
    FROM locked_process lp
    JOIN fgi_impact_processes p ON p.id = lp.id
    JOIN compensation_documents d ON d.impact_process_id = p.id
    JOIN impacted_stores ist ON ist.store_code = p.impacted_store_code
    JOIN stores impacted ON impacted.store_code = p.impacted_store_code
    JOIN fgi_impact_stores pair ON pair.impact_process_id = p.id
    JOIN stores ns ON ns.store_code = pair.new_store_code
    LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = p.id
    GROUP BY p.id, d.doc_no, d.current_section_code, ist.opt_dv_user_id,
             impacted.juristic_name, ss.growth_rate_diff, ss.sales_status
)
SELECT * FROM gate;""",
        "write": """UPDATE fgi_impact_processes
SET workflow_generation_status = 'N', updated_at = CURRENT_TIMESTAMP
WHERE id = :impact_process_id
  AND workflow_generation_status = 'W'
  AND :gate_decision = 'N';

INSERT INTO workflow_instances (instance_id, doc_no, instance_status, started_at, started_by)
SELECT :instance_id, :doc_no, 'ACTIVE', CURRENT_TIMESTAMP, 'JOB-8B'
WHERE :gate_decision = 'Y';
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status, opened_at)
SELECT :instance_id, :doc_no, '06', 'OPEN', CURRENT_TIMESTAMP
WHERE :gate_decision = 'Y';
UPDATE fgi_impact_processes
SET workflow_generation_status = 'Y', updated_at = CURRENT_TIMESTAMP
WHERE id = :impact_process_id
  AND workflow_generation_status = 'W'
  AND :gate_decision = 'Y';

-- gate_decision='W' ไม่เปลี่ยนสถานะ; บันทึก reason ลง job_run_histories เพื่อ rerun.""",
        "idempotency": "UNIQUE(workflow_instances.doc_no) และ OPEN-task partial unique index; instance เดิมให้ skip",
        "transaction": "lock process + evaluate gate + branch N/W/Y; เฉพาะ Y จึง create instance/task และ W→Y ใน transaction เดียว, N ต้อง persist ถาวร, W คงเดิมเพื่อ rerun",
        "security": "internal service token จาก workload identity/secretRef; ห้าม Basic Auth หรือ K2 REST credential เดิม",
        "steps": "lockWorkflowCandidates|evaluateGenerationGate|startInternalWorkflows|notifyWorkflowOwners",
    },
    "9": {
        "repository": "documentNewStoreRepository",
        "read": """SELECT d.doc_no, s.new_store_code,
       COALESCE(s.adjust_compensate_percent, s.forecast_compensate_percent) AS compensate_percent,
       COALESCE(s.adjust_compensation_amount, s.forecast_compensation_amount) AS compensation_amount
FROM fgi_impact_stores s
JOIN compensation_documents d ON d.impact_process_id = s.impact_process_id
WHERE s.impact_month = :impact_month;""",
        "write": """INSERT INTO document_new_stores
    (doc_no, new_store_code, compensate_percent, compensation_amount, source_system, updated_at)
VALUES (:doc_no, :new_store_code, :compensate_percent, :compensation_amount, 'FGI', CURRENT_TIMESTAMP)
ON CONFLICT (doc_no, new_store_code)
DO UPDATE SET compensate_percent = EXCLUDED.compensate_percent,
              compensation_amount = EXCLUDED.compensation_amount,
              updated_at = CURRENT_TIMESTAMP;

DELETE FROM document_new_stores dns
WHERE dns.doc_no = :doc_no
  AND dns.source_system = 'FGI'
  AND NOT EXISTS (
      SELECT 1
      FROM fgi_impact_stores src
      JOIN compensation_documents d ON d.impact_process_id = src.impact_process_id
      WHERE d.doc_no = dns.doc_no
        AND src.impact_month = :impact_month
        AND src.new_store_code = dns.new_store_code
  );

SELECT CASE WHEN ABS(SUM(compensate_percent) - 100) <= 0.0001 THEN TRUE ELSE FALSE END AS allocation_valid
FROM document_new_stores
WHERE doc_no = :doc_no;""",
        "idempotency": "UNIQUE(doc_no,new_store_code); upsert + prune เฉพาะ source_system=FGI ให้ target ตรง impact set ปัจจุบัน โดยไม่ลบแถว USER",
        "transaction": "upsert + prune ร้านของ doc_no, validate ผลรวม 100% และ tracking INTERNAL_DB_WRITE ใน transaction เดียว; ไม่ครบให้ rollback",
        "security": "internal service account least privilege; ไม่มี SFTP/BPM credential หรือ editable external endpoint",
        "steps": "loadNewStoreAllocations|validateAllocationValues|upsertDocumentNewStores|reconcileAllocationTotals",
    },
    "10": {
        "repository": "pendingAckRepository",
        "read": """SELECT id, data_name, business_key, file_name, sent_at
FROM interface_transactions
WHERE direction = 'OUT'
  AND status = 'SENT'
  AND acked_at IS NULL
  AND sent_at < CURRENT_TIMESTAMP - (:threshold_hours * INTERVAL '1 hour')
ORDER BY sent_at;""",
        "write": """INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
SELECT 'interface_transactions', CAST(id AS VARCHAR), 'PENDING_ACK_NOTIFIED',
       jsonb_build_object('notification_date', CURRENT_DATE, 'data_name', data_name),
       'JOB-10', CURRENT_TIMESTAMP
FROM interface_transactions i
WHERE i.id = ANY(:transaction_ids)
  AND NOT EXISTS (
      SELECT 1 FROM audit_logs a
      WHERE a.table_name = 'interface_transactions' AND a.ref_key = CAST(i.id AS VARCHAR)
        AND a.action_type = 'PENDING_ACK_NOTIFIED'
        AND (a.new_value ->> 'notification_date')::date = CURRENT_DATE);""",
        "idempotency": "notification marker ต่อ interface transaction ต่อวัน; rerun วันเดียวกันไม่ส่งอีเมลซ้ำ",
        "transaction": "อ่าน pending แบบ read-only; reserve notification marker ก่อนส่ง; ส่งล้มเหลว mark FAILED และ retry ด้วย marker เดิม",
        "security": "Notification Service ใช้ workload identity/secretRef; recipient อ่านจาก status_email_rules ไม่ hardcode",
        "steps": "loadOverdueAcknowledgements|reserveNotificationMarkers|sendPendingAckDigest|closeNotificationMarkers",
    },
}


def api_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


API_REQUIRED_QUERY_FIELDS: dict[str, set[str]] = {
    "/api/v1/documents": {"year"},
    "/api/v1/reports/status-summary": {"year", "status", "result", "resultCategory"},
    "/api/v1/reports/status-summary/export": {"year", "status", "result", "resultCategory"},
}


def api_value_type(value: Any) -> str:
    if value is None:
        return "string | null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        if not value:
            return "array<object>"
        return f"array<{api_value_type(value[0])}>"
    if isinstance(value, dict):
        return "object"
    return "string"


def api_field_constraint(field_path: str, value: Any) -> str:
    name = field_path.split(".")[-1].replace("[]", "").lower()
    if name in {"page"}:
        return ">= 1; default 1"
    if name in {"size"}:
        return "1..100; default 20"
    if name.endswith("storecode"):
        return "exactly 5 digits; preserve leading zero"
    if name in {"docno"}:
        return "พ.ศ. YYYY/xxxxx"
    if name.endswith("datetime") or name.endswith("at") or name.endswith("date") or name.endswith("month"):
        return "ISO-8601 ค.ศ.; nullable only when type includes null"
    if name.endswith("percent"):
        return "number 0..100 with 2 decimals"
    if "amount" in name:
        return "number >= 0 with 2 decimals"
    if name in {"statuscode", "nextsection", "sectioncode", "rolecode"}:
        return "canonical code; do not replace with display label"
    if name in {"reason", "comment"}:
        return "trimmed UTF-8 Thai text; required by operation/business rule"
    if isinstance(value, list):
        return "JSON array; element type shown in Type column"
    if isinstance(value, dict):
        return "JSON object; nested fields listed below"
    return "UTF-8; use value domain described by endpoint purpose"


def api_schema_rows(spec: ApiSpec, body: Any, direction: str) -> list[list[str]]:
    if body is None:
        return [["-", "none", "No", "Endpoint has no JSON body/query object"]]

    rows: list[list[str]] = []
    required_query = API_REQUIRED_QUERY_FIELDS.get(spec.path, set())

    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            if path:
                required = "Yes" if direction == "response" or spec.method.upper() != "GET" else ("Yes" if path in required_query else "No")
                rows.append([path, "object", required, api_field_constraint(path, value)])
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                walk(child, child_path)
            return
        if isinstance(value, list):
            required = "Yes" if direction == "response" or spec.method.upper() != "GET" else ("Yes" if path in required_query else "No")
            rows.append([path, api_value_type(value), required, api_field_constraint(path, value)])
            if value and isinstance(value[0], dict):
                for key, child in value[0].items():
                    walk(child, f"{path}[].{key}")
            return
        if direction == "response":
            required = "No" if value is None else "Yes"
        elif spec.method.upper() == "GET":
            required = "Yes" if path in required_query else "No"
        else:
            required = "No" if value is None else "Yes"
        rows.append([path or "value", api_value_type(value), required, api_field_constraint(path or "value", value)])

    walk(body)
    return rows or [["-", "none", "No", "No fields"]]


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-")


def fmt_days(days: float) -> str:
    return f"{days:.1f}".rstrip("0").rstrip(".")


def fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def is_workday(d: date) -> bool:
    return d.weekday() < 5


def next_workday(d: date) -> date:
    current = d
    while not is_workday(current):
        current += timedelta(days=1)
    return current


def add_workdays(start: date, workdays: int) -> date:
    current = next_workday(start)
    remaining = max(1, workdays) - 1
    while remaining:
        current += timedelta(days=1)
        if is_workday(current):
            remaining -= 1
    return current


def build_topic_schedule(topics_list: list[Topic], start_date: date = LLDD_START_DATE) -> dict[str, tuple[date, date]]:
    schedule: dict[str, tuple[date, date]] = {}
    used_hours_by_owner: dict[str, int] = {}
    for topic in topics_list:
        used_hours = used_hours_by_owner.get(topic.owner, 0)
        start_day_offset = used_hours // HOURS_PER_DAY
        end_day_offset = (used_hours + topic.hours - 1) // HOURS_PER_DAY
        start = add_workdays(start_date, start_day_offset + 1)
        end = add_workdays(start_date, end_day_offset + 1)
        if start < start_date or end > LLDD_END_DATE or end < start:
            raise ValueError(f"Invalid schedule window for {topic.file}: {start} - {end}")
        schedule[topic.file] = (start, end)
        used_hours_by_owner[topic.owner] = used_hours + topic.hours
    return schedule


def image_path(name: str) -> Path:
    path = IMG / name
    if path.exists():
        return path
    path = SLICE / name
    if path.exists():
        return path
    return ROOT / "output/srs/screenshots" / name


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: Any, bold: bool = False) -> None:
    cell.text = ""
    para = cell.paragraphs[0]
    run = para.add_run(str(text) if text is not None else "")
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    run.font.size = Pt(9)
    run.bold = bold
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.keep_together = True
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_row_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def add_docx_table(doc: Document, headers: list[str], rows: list[list[Any]]) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i, head in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], head, True)
        set_cell_shading(t.rows[0].cells[i], "E8EEF5")
    set_row_cant_split(t.rows[0])
    for row in rows:
        cells = t.add_row().cells
        normalized = list(row[: len(headers)]) + [""] * max(0, len(headers) - len(row))
        for i, val in enumerate(normalized):
            set_cell_text(cells[i], val)
        set_row_cant_split(t.rows[-1])
    doc.add_paragraph()


def add_docx_payload(doc: Document, title: str, text: str) -> None:
    t = doc.add_table(rows=2, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    header = t.rows[0].cells[0]
    set_cell_text(header, title, True)
    set_cell_shading(header, "DDEBFF")
    body = t.rows[1].cells[0]
    body.text = ""
    para = body.paragraphs[0]
    para.paragraph_format.keep_together = True
    run = para.add_run(text)
    run.font.name = "Courier New"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
    run.font.size = Pt(8)
    para.paragraph_format.space_after = Pt(0)
    set_cell_shading(body, "F7FAFE")
    for row in t.rows:
        set_row_cant_split(row)
    doc.add_paragraph()


def add_docx_image(doc: Document, path: Path, caption: str) -> None:
    if not path.exists():
        doc.add_paragraph(f"[ไม่พบรูปภาพ: {path.name}]")
        return
    pic = doc.add_paragraph()
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.paragraph_format.keep_with_next = True
    pic.add_run().add_picture(str(path), width=Inches(6.2))
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.keep_together = True
    for run in cap.runs:
        run.font.size = Pt(9)
        run.font.italic = True


def build_docx(title: str, blocks: list[dict[str, Any]], out_path: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    styles["Normal"].font.size = Pt(10)
    for style_name, size, color in [
        ("Heading 1", 16, "1F4D78"),
        ("Heading 2", 13, "2E74B5"),
        ("Heading 3", 11, "1F4D78"),
    ]:
        st = styles[style_name]
        st.font.name = "Arial"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.keep_together = True

    title_p = doc.add_paragraph()
    title_run = title_p.add_run(title)
    title_run.font.name = "Arial"
    title_run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    title_run.font.size = Pt(20)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor.from_string("0B2545")
    doc.add_paragraph("SBP Mall - ระบบประกันรายได้ | Low Level Design Document")

    header = section.header.paragraphs[0]
    header.text = title
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        run.font.name = "Arial"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor.from_string("66717F")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("หน้า ")
    footer_run.font.name = "Arial"
    footer_run.font.size = Pt(8)
    page_field = OxmlElement("w:fldSimple")
    page_field.set(qn("w:instr"), "PAGE")
    footer._p.append(page_field)

    heading_pending = False
    page_break_pending = False
    figure_no = 0
    for block in blocks:
        btype = block["type"]
        if btype == "h1":
            para = doc.add_heading(block["text"], level=1)
            para.paragraph_format.page_break_before = page_break_pending
            page_break_pending = False
            para.paragraph_format.keep_with_next = True
            para.paragraph_format.keep_together = True
            heading_pending = True
        elif btype == "h2":
            para = doc.add_heading(block["text"], level=2)
            para.paragraph_format.page_break_before = page_break_pending
            page_break_pending = False
            para.paragraph_format.keep_with_next = True
            para.paragraph_format.keep_together = True
            heading_pending = True
        elif btype == "h3":
            para = doc.add_heading(block["text"], level=3)
            para.paragraph_format.page_break_before = page_break_pending
            page_break_pending = False
            para.paragraph_format.keep_with_next = True
            para.paragraph_format.keep_together = True
            heading_pending = True
        elif btype == "p":
            para = doc.add_paragraph(block["text"])
            if heading_pending:
                para.paragraph_format.keep_with_next = False
            heading_pending = False
        elif btype == "bullets":
            for item in block["items"]:
                para = doc.add_paragraph(item, style="List Bullet")
                para.paragraph_format.keep_together = True
            heading_pending = False
        elif btype == "table":
            add_docx_table(doc, block["headers"], block["rows"])
            heading_pending = False
        elif btype == "image":
            figure_no += 1
            add_docx_image(doc, ROOT / block["path"], f"รูปที่ {figure_no}: {block['caption']}")
            heading_pending = False
        elif btype == "code":
            para = doc.add_paragraph()
            run = para.add_run(block["text"])
            run.font.name = "Courier New"
            run.font.size = Pt(7 if block.get("lang") == "java" else 8)
            para.paragraph_format.left_indent = Inches(0.2)
            para.paragraph_format.keep_together = False
            heading_pending = False
        elif btype == "payload":
            add_docx_payload(doc, block["title"], block["text"])
            heading_pending = False
        elif btype == "pagebreak":
            page_break_pending = True
            heading_pending = False

    while doc.paragraphs and not doc.paragraphs[-1].text.strip():
        trailing = doc.paragraphs[-1]._element
        trailing.getparent().remove(trailing)
    doc.save(out_path)


def init_pdf_styles():
    if os.path.exists(FONT):
        pdfmetrics.registerFont(TTFont("TH", FONT))
        pdfmetrics.registerFont(TTFont("TH-Bold", FONT))
        base = "TH"
    else:
        base = "Helvetica"
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("TitleTH", parent=ss["Title"], fontName=base, fontSize=18, leading=24, textColor=colors.HexColor("#0B2545"), alignment=TA_LEFT),
        "h1": ParagraphStyle("H1TH", parent=ss["Heading1"], fontName=base, fontSize=14, leading=18, textColor=colors.HexColor("#1F4D78"), spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("H2TH", parent=ss["Heading2"], fontName=base, fontSize=12, leading=16, textColor=colors.HexColor("#2E74B5"), spaceBefore=8, spaceAfter=4),
        "h3": ParagraphStyle("H3TH", parent=ss["Heading3"], fontName=base, fontSize=10.5, leading=14, textColor=colors.HexColor("#1F4D78"), spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("BodyTH", parent=ss["BodyText"], fontName=base, fontSize=9.2, leading=13, spaceAfter=5),
        "small": ParagraphStyle("SmallTH", parent=ss["BodyText"], fontName=base, fontSize=8, leading=10, spaceAfter=3),
        "code": ParagraphStyle("CodeTH", parent=ss["Code"], fontName=base, fontSize=7.4, leading=9, backColor=colors.HexColor("#F4F6F9"), borderPadding=4),
        "java": ParagraphStyle("JavaTH", parent=ss["Code"], fontName=base, fontSize=6.4, leading=7.8, backColor=colors.HexColor("#F4F6F9"), borderPadding=4),
    }


def para(text: Any, style: ParagraphStyle) -> Paragraph:
    esc = str(text if text is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    esc = esc.replace("\n", "<br/>")
    return Paragraph(esc, style)


def code_para(text: Any, style: ParagraphStyle) -> Paragraph:
    escaped_lines = []
    for line in str(text if text is not None else "").splitlines():
        leading = len(line) - len(line.lstrip(" "))
        body = line[leading:].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_lines.append("&nbsp;" * leading + body)
    esc = "<br/>".join(escaped_lines)
    return Paragraph(esc, style)


def add_pdf_table(story: list[Any], styles: dict[str, ParagraphStyle], headers: list[str], rows: list[list[Any]]) -> None:
    data = [[para(h, styles["small"]) for h in headers]]
    for row in rows:
        normalized = list(row[: len(headers)]) + [""] * max(0, len(headers) - len(row))
        data.append([para(v, styles["small"]) for v in normalized])
    col_count = max(1, len(headers))
    widths = [7.0 * inch / col_count] * col_count
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D2DC")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


def add_pdf_payload(story: list[Any], styles: dict[str, ParagraphStyle], title: str, text: str) -> None:
    data = [
        [para(title, styles["small"])],
        [code_para(text, styles["code"])],
    ]
    t = Table(data, colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BFD0E6")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBFF")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F7FAFE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


def add_pdf_image(story: list[Any], styles: dict[str, ParagraphStyle], path: Path, caption: str) -> None:
    if not path.exists():
        story.append(para(f"[ไม่พบรูปภาพ: {path.name}]", styles["body"]))
        return
    with Image.open(path) as im:
        w, h = im.size
    max_w = 7.0 * inch
    max_h = 4.4 * inch
    scale = min(max_w / w, max_h / h, 1.0)
    story.append(KeepTogether([PdfImage(str(path), width=w * scale, height=h * scale), para(caption, styles["small"]), Spacer(1, 8)]))


def build_pdf(title: str, blocks: list[dict[str, Any]], out_path: Path) -> None:
    styles = init_pdf_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=0.55 * inch, rightMargin=0.55 * inch, topMargin=0.55 * inch, bottomMargin=0.55 * inch)
    story: list[Any] = [Paragraph(title, styles["title"]), para("SBP Mall - ระบบประกันรายได้ | Low Level Design Document", styles["body"]), Spacer(1, 8)]
    figure_no = 0
    for block in blocks:
        btype = block["type"]
        if btype in ("h1", "h2", "h3"):
            min_space = {"h1": 1.6 * inch, "h2": 1.15 * inch, "h3": 0.9 * inch}[btype]
            story.append(CondPageBreak(min_space))
            story.append(Paragraph(block["text"], styles[btype]))
        elif btype == "p":
            story.append(para(block["text"], styles["body"]))
        elif btype == "bullets":
            story.append(ListFlowable([ListItem(para(i, styles["body"])) for i in block["items"]], bulletType="bullet", leftIndent=16))
        elif btype == "table":
            add_pdf_table(story, styles, block["headers"], block["rows"])
        elif btype == "image":
            figure_no += 1
            add_pdf_image(story, styles, ROOT / block["path"], f"รูปที่ {figure_no}: {block['caption']}")
        elif btype == "code":
            story.append(code_para(block["text"], styles["java"] if block.get("lang") == "java" else styles["code"]))
        elif btype == "payload":
            before = len(story)
            add_pdf_payload(story, styles, block["title"], block["text"])
            story[before:] = [KeepTogether(story[before:])]
        elif btype == "pagebreak":
            story.append(PageBreak())

    def add_page_number(canvas, pdf_doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#66717F"))
        canvas.drawCentredString(A4[0] / 2, 0.28 * inch, f"{pdf_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = ["| " + " | ".join(cell(header) for header in headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        normalized = list(row[: len(headers)]) + [""] * max(0, len(headers) - len(row))
        out.append("| " + " | ".join(cell(value) for value in normalized) + " |")
    return "\n".join(out)


ARTIFACT_LABELS = {
    "workflow.md": "Workflow design",
    "api.md": "API design",
    "database.md": "Database design",
    "plan-api.html": "API specification screen",
    "plan-database.html": "Database design screen",
    "plan-flow.html": "Integrated flow screen",
    "plan-email.html": "Email template screen",
    "job-batch.html": "Batch job console",
    "system-config.html": "Global config screen",
    "index.html": "Portal screen",
    "k2-create.html": "Create Document screen",
    "k2-document.html": "Document Detail screen",
    "k2-report.html": "Status Report screen",
    "k2-list-waiting.html": "Task Inbox screen",
    "k2-list-related.html": "Related Documents screen",
    "k2-list-abnormal.html": "Abnormal Data screen",
    "k2-operators.html": "Operator Master screen",
    "k2-factors.html": "External Factor Master screen",
    "k2-permissions.html": "RBAC Matrix screen",
}


def scrub_pdf_reference(match: re.Match[str]) -> str:
    stem = Path(match.group(1)).name
    if stem.startswith("LLDD-"):
        return f"{stem}.pdf"
    return "ไฟล์" + Path(stem).stem.replace("-", " ")


def scrub_lldd_text(value: Any) -> str:
    text = str(value)
    text = re.sub(
        r"(?i)(?:[A-Za-z0-9_.-]+/)*(LLDD-[A-Za-z0-9-]+)(?:\.(?:md|docx|pdf))?",
        lambda m: f"{m.group(1)}.pdf",
        text,
    )
    for source, target in ARTIFACT_LABELS.items():
        text = text.replace(source, target)
    text = re.sub(r"(?i)\bSRS\b", "ข้อกำหนดทางธุรกิจ", text)
    text = re.sub(r"([\w./\-\u0E00-\u0E7F]+)\.md\b", lambda m: Path(m.group(1)).name.replace("-", " "), text, flags=re.IGNORECASE)
    text = re.sub(r"([\w./\-\u0E00-\u0E7F]+)\.html\b", lambda m: Path(m.group(1)).name.replace("-", " ") + " screen", text, flags=re.IGNORECASE)
    text = re.sub(r"([\w./\-\u0E00-\u0E7F]+)\.docx\b", lambda m: Path(m.group(1)).stem.replace("-", " "), text, flags=re.IGNORECASE)
    text = re.sub(r"([\w./\-\u0E00-\u0E7F]+)\.pdf\b", scrub_pdf_reference, text, flags=re.IGNORECASE)
    return text


def scrub_lldd_block(block: dict[str, Any], preserve_java: bool = False) -> dict[str, Any]:
    cleaned = dict(block)
    if preserve_java and cleaned.get("type") == "code" and cleaned.get("lang") == "java":
        return cleaned
    for key in ("text", "title", "caption"):
        if key in cleaned:
            cleaned[key] = scrub_lldd_text(cleaned[key])
    for key in ("headers", "items"):
        if key in cleaned:
            cleaned[key] = [scrub_lldd_text(item) for item in cleaned[key]]
    if "rows" in cleaned:
        cleaned["rows"] = [[scrub_lldd_text(cell) for cell in row] for row in cleaned["rows"]]
    return cleaned


def scrub_lldd_blocks(blocks: list[dict[str, Any]], preserve_java: bool = False) -> list[dict[str, Any]]:
    return [scrub_lldd_block(block, preserve_java=preserve_java) for block in blocks]


def delivery_intro_blocks(is_job: bool) -> list[dict[str, Any]]:
    rows = [
        ["วัตถุประสงค์", "ใช้เป็นรายละเอียดระดับพัฒนาสำหรับออกแบบ ลงมือพัฒนา ตรวจทาน และทดสอบขอบเขตที่ระบุในฉบับนี้"],
        ["ลำดับการอ่าน", "เริ่มจาก Overview และ Scope จากนั้นตรวจ Field/Validation, Implementation, Contract, Processing Flow, Acceptance Criteria และ Test Checklist ตามลำดับ"],
        ["ผลลัพธ์ที่คาดหวัง", "ผู้อ่านสามารถระบุ input, ขั้นตอนประมวลผล, output, เงื่อนไขผิดพลาด และหลักฐานการทดสอบได้จากเนื้อหาในฉบับเดียว"],
    ]
    if is_job:
        rows.append(["Java เดิม", "ภาคผนวกท้ายฉบับระบุ source file, ช่วงบรรทัด และ code Java เดิมสำหรับตรวจเทียบ behavior ก่อนย้ายระบบ"])
    return [
        h(1, "แนวทางการใช้เอกสาร"),
        table(["หัวข้อ", "คำอธิบาย"], rows),
        p("คำว่า Input, Progress และ Output ในเอกสารนี้หมายถึงข้อมูลตั้งต้น ลำดับการทำงาน และผลลัพธ์ที่ตรวจสอบได้ของขอบเขตที่กำลังพัฒนา"),
        pagebreak(),
    ]


def parse_line_ranges(value: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for part in value.split(","):
        match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", part)
        if match:
            ranges.append((int(match.group(1)), int(match.group(2))))
    return ranges


def compact_excerpt_ranges(start: int, end: int, max_lines: int = 24) -> list[tuple[int, int]]:
    if end - start + 1 <= max_lines:
        return [(start, end)]
    half = max_lines // 2
    return [(start, start + half - 1), (end - half + 1, end)]


def legacy_java_appendix_blocks(document_key: str) -> list[dict[str, Any]]:
    if "/Jobs/" not in document_key:
        return []
    job_no = document_key.split("LLDD-BE-Job-", 1)[1].split("-", 1)[0]
    legacy = LEGACY_JOB_SOURCES.get(job_no)
    if not legacy:
        return []

    blocks: list[dict[str, Any]] = [
        pagebreak(),
        h(1, "ภาคผนวก: Java Source เดิม"),
        p("Code ในส่วนนี้คัดจาก Java source เดิมโดยตรงและคงข้อความตามต้นฉบับ ใช้เลขบรรทัดที่ระบุหน้าทุก snippet เพื่อตรวจเทียบ business behavior, SQL, transaction และ error handling"),
    ]
    for source_index, (relative_path, line_ranges, responsibility) in enumerate(legacy["sources"], start=1):
        source_path = ROOT.parent / relative_path
        if not source_path.exists():
            blocks.extend([
                h(2, f"J{source_index}. {relative_path}"),
                p(f"ไม่พบ Java source ที่ {relative_path}; ต้องตรวจ path ก่อนเริ่มพัฒนา"),
            ])
            continue
        source_lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
        first_excerpt = True
        for declared_start, declared_end in parse_line_ranges(line_ranges):
            actual_start = max(1, declared_start)
            actual_end = min(len(source_lines), declared_end)
            for excerpt_start, excerpt_end in compact_excerpt_ranges(actual_start, actual_end):
                if not first_excerpt:
                    blocks.append(pagebreak())
                heading = f"J{source_index}. {Path(relative_path).name} — lines {excerpt_start}-{excerpt_end}"
                blocks.extend([
                    h(2, heading),
                    table(["รายการ", "รายละเอียด"], [
                        ["Source file", relative_path],
                        ["Original lines", f"{excerpt_start}-{excerpt_end}"],
                        ["Responsibility", responsibility],
                    ]),
                    code("\n".join(source_lines[excerpt_start - 1:excerpt_end]), "java"),
                ])
                first_excerpt = False
    return blocks


def prepare_delivery_blocks(title: str, blocks: list[dict[str, Any]], document_key: str) -> tuple[str, list[dict[str, Any]]]:
    is_job = "/Jobs/" in document_key
    combined = [*delivery_intro_blocks(is_job), *blocks, *legacy_java_appendix_blocks(document_key)]
    return scrub_lldd_text(title), scrub_lldd_blocks(combined, preserve_java=is_job)


def build_md(title: str, blocks: list[dict[str, Any]], out_path: Path) -> None:
    lines = [f"# {title}", "", "SBP Mall - ระบบประกันรายได้ | Low Level Design Document", ""]
    figure_no = 0
    for block in blocks:
        btype = block["type"]
        if btype == "h1":
            lines.extend([f"## {block['text']}", ""])
        elif btype == "h2":
            lines.extend([f"### {block['text']}", ""])
        elif btype == "h3":
            lines.extend([f"#### {block['text']}", ""])
        elif btype == "p":
            lines.extend([block["text"], ""])
        elif btype == "bullets":
            lines.extend([f"- {i}" for i in block["items"]])
            lines.append("")
        elif btype == "table":
            lines.extend([md_table(block["headers"], block["rows"]), ""])
        elif btype == "image":
            figure_no += 1
            caption = f"รูปที่ {figure_no}: {block['caption']}"
            rel = os.path.relpath(ROOT / block["path"], out_path.parent)
            lines.extend([f"![{caption}]({rel})", "", f"_{caption}_", ""])
        elif btype == "code":
            lines.extend([f"```{block.get('lang', '')}", block["text"], "```", ""])
        elif btype == "payload":
            lines.extend([f"#### {block['title']}", "", "```json", block["text"], "```", ""])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def render_all(title: str, blocks: list[dict[str, Any]], base: Path, formats: set[str]) -> None:
    relative_base = base.relative_to(OUT)
    if "md" in formats:
        md_path = (OUT / FORMAT_DIRS["md"] / relative_base).with_suffix(".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        build_md(title, blocks, md_path)
    delivery_title, delivery_blocks = prepare_delivery_blocks(title, blocks, str(relative_base))
    if "docx" in formats:
        docx_path = (OUT / FORMAT_DIRS["docx"] / relative_base).with_suffix(".docx")
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        build_docx(delivery_title, delivery_blocks, docx_path)
    if "pdf" in formats:
        pdf_path = (OUT / FORMAT_DIRS["pdf"] / relative_base).with_suffix(".pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        build_pdf(delivery_title, delivery_blocks, pdf_path)


def topic_blocks(topic: Topic) -> list[dict[str, Any]]:
    if topic.file == "FE/LLDD-FE-Testing-Delivery":
        return testing_delivery_blocks(topic)
    is_batch_monitor = is_batch_monitor_doc(topic.file)
    blocks: list[dict[str, Any]] = [
        h(1, "1. Overview"),
        table(["รายการ", "รายละเอียด"], [
            ["Track", topic.track],
            ["Estimate", f"{topic.hours} ชั่วโมง"],
            ["Owner", topic.owner],
            ["Objective", topic.objective],
        ]),
        h(1, "2. Screen / Functional Scope"),
        bullets(topic.scope),
    ]
    if not is_batch_monitor:
        blocks.insert(2, p("Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint"))
    if topic.screenshots:
        blocks.append(h(1, "3. Screenshot Reference"))
        for shot in topic.screenshots:
            blocks.append(image(str(image_path(shot).relative_to(ROOT)), f"Screenshot: {shot}"))
    if topic.flow_diagram and not is_batch_monitor:
        draw_flow_diagram(topic.title, topic.flow, topic.flow_diagram)
        blocks.extend([
            h(1, "4. Implementation Flow Diagram (Reference)"),
            image(topic.flow_diagram, f"Implementation flow reference: {topic.title}"),
        ])
    blocks.extend([
        h(1, "4. Field, Format, and Validation" if is_batch_monitor else "5. Field, Format, and Validation"),
        table(["Field / UI", "Format", "Validation", "Behavior"], topic.fields),
    ])
    blocks.extend(topic_extra_blocks(topic.file))
    blocks.extend(topic_io_contract_blocks(topic))
    blocks.extend(implementation_detail_blocks(topic))
    blocks.extend([
        h(1, "5. Button / User Action Mapping" if is_batch_monitor else "6. Button / User Action Mapping"),
        table(["Action", "Trigger", "UI Area", "Expected Result"] if is_batch_monitor else ["Action", "Trigger", "API / Service", "Expected Result"], topic.actions),
    ])
    blocks.append(h(1, "6. API Contract" if is_batch_monitor else "7. API Contract"))
    for spec in topic.apis:
        blocks.extend([
            h(2, f"{spec.method} {spec.path}"),
            p(spec.purpose),
        ])
        if spec.buttons:
            blocks.append(table(["Triggered by"], [[b] for b in spec.buttons]))
        if spec.request is not None:
            request_title = "Query Params" if spec.method.upper() == "GET" else "Request"
            blocks.append(payload(request_title, api_json(spec.request)))
        blocks.append(h(3, "Request Field Schema"))
        blocks.append(table(["Field", "Type", "Required", "Constraint / Meaning"], api_schema_rows(spec, spec.request, "request")))
        if spec.response is not None:
            blocks.append(payload("Response", api_json(spec.response)))
        blocks.append(h(3, "Response Field Schema"))
        blocks.append(table(["Field", "Type", "Required", "Constraint / Meaning"], api_schema_rows(spec, spec.response, "response")))
    if is_batch_monitor:
        blocks.extend([
            h(1, "7. Tab Interaction Flow"),
            table(["Step", "Description"], [[i + 1, s] for i, s in enumerate(topic.flow)]),
            h(1, "8. Acceptance Criteria"),
            bullets(topic.acceptance),
            h(1, "9. Developer Test Checklist"),
            table(["No", "Test"], [[i + 1, t] for i, t in enumerate(topic.tests)]),
        ])
        return blocks
    if topic.db_tables:
        blocks.extend([
            h(1, "8. Reference DB Mapping (No Database Page Work)"),
            p("ส่วนนี้เป็นข้อมูลอ้างอิงสำหรับการ implement API/Job เท่านั้น ไม่ใช่งานสร้างหน้า Database, ไม่ใช่งานออกแบบ DB page และไม่ถูกนับเป็น deliverable แยกของ FE/BE"),
            table(["Table / Object", "R/W", "Usage"], topic.db_tables),
        ])
    blocks.extend([
        h(1, "9. Processing Flow"),
        table(["Step", "Description"], [[i + 1, s] for i, s in enumerate(topic.flow)]),
        h(1, "10. Acceptance Criteria"),
        bullets(topic.acceptance),
        h(1, "11. Developer Test Checklist"),
        table(["No", "Test"], [[i + 1, t] for i, t in enumerate(topic.tests)]),
    ])
    return blocks


def common_doc_fields() -> list[tuple[str, str, str, str]]:
    return [
        ("docNo", "YYYY/xxxxx", "required when opening existing document", "ใช้ปี พ.ศ. และ running 5 หลัก"),
        ("storeCode", "string 5 digits", "numeric length = 5", "แสดง leading zero"),
        ("amount", "number, 2 decimals", ">= 0", "format `#,##0.00` บาท"),
        ("percent", "number, 2 decimals", "0-100", "ใช้ `%` และรวม allocation ต้องเท่ากับ 100"),
        ("date", "DD/MM/YYYY", "valid date", "FE แสดง พ.ศ. หาก source เป็น ISO ค.ศ."),
        ("attachment", "file", "<= 5 MB", f"รองรับ {ATTACHMENT_ALLOWED_EXTENSIONS}"),
    ]


def topic_extra_blocks(file_key: str) -> list[dict[str, Any]]:
    if file_key == "FE/LLDD-FE-Create-Document":
        return create_document_fs_iframe_blocks()
    if file_key == "FE/LLDD-FE-Master-Config":
        return master_config_screen_blocks()
    if file_key == "FE/LLDD-FE-Document-Detail":
        return document_detail_role_blocks()
    role_profile = document_detail_role_profile(file_key)
    if role_profile:
        return document_detail_single_role_blocks(role_profile)
    if file_key == "BE/LLDD-BE-API-Common-Contracts":
        return common_contract_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Create-Update":
        return document_create_update_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Workflow-Actions":
        return workflow_action_transition_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Detail-Aggregate":
        return document_detail_aggregate_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Attachment-Sales-Timeline":
        return attachment_storage_extra_blocks()
    return []


def workflow_action_transition_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Canonical Workflow Transition Matrix"),
        p("BE ต้องคำนวณ transition จาก currentSection, result และ totalCompensationAmount ภายใน transaction; FE ส่งเพียง result/comment และห้ามส่ง nextSection เอง"),
        table(["Current", "Result / condition", "statusCode", "nextSection", "Task effect"], [
            ["06", "ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "08", "08", "close 06; open 08"],
            ["08", "คำนวณเงินชดเชยเรียบร้อย", "01", "01", "close 08; open 01"],
            ["01", "เห็นควรชดเชย", "02", "02", "close 01; open 02"],
            ["02", "เห็นควรชดเชย และ totalCompensationAmount > 100000", "03", "03", "close 02; open 03"],
            ["02", "เห็นควรชดเชย และ totalCompensationAmount <= 100000", "99", "null", "close 02; complete instance"],
            ["03", "เห็นควรชดเชย", "99", "null", "close 03; complete instance"],
            ["ทุก section ที่รองรับ", "ส่งกลับ", "รหัส section ปลายทางตาม action option", "section ปลายทาง", "close current; reopen target with new task id"],
            ["06", "เห็นควรไม่ชดเชย หรือ หยุดชดเชยประกันรายได้", "99", "null", "close 06; complete instance"],
        ]),
        h(2, "5.2 Action Response Type"),
        table(["Field", "Type", "Required", "Rule"], [
            ["statusCode", "enum 06|08|01|02|03|99", "Yes", "ค่าหลัง commit; 99 = เสร็จสิ้น"],
            ["nextSection", "enum 06|08|01|02|03 | null", "Yes", "null เมื่อ workflow จบ"],
            ["message", "string", "Yes", "ข้อความผล mutation สำหรับแสดงผู้ใช้"],
        ]),
    ]


def master_config_screen_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Screen Boundary and Route Matrix"),
        p("หัวข้อนี้ประกอบด้วย 4 หน้าจออิสระ แต่ละหน้ามี route, state, validation และ endpoint ของตนเอง ห้าม implement เป็น form/table เดียวที่สลับชนิดข้อมูลด้วยเงื่อนไขใน component เดียว"),
        table(["Screen", "Route / Component", "Primary model", "Main operations"], [
            ["SCR-08 ผู้ปฏิบัติงาน", "/admin/operators / OperatorAssignmentPage", "OperatorAssignment", "search employee, list, add, edit, deactivate, audit reason"],
            ["SCR-09 ปัจจัยภายนอก", "/admin/external-factors / ExternalFactorPage", "ExternalFactor", "list, add, edit, delete, duplicate-code guard"],
            ["SCR-10 สิทธิ์เมนู", "/admin/menu-permissions / MenuPermissionPage", "MenuPermissionMatrix", "load roles/menus, toggle canView, save per menu, refresh guard"],
            ["SCR-11 ตั้งค่าระบบ", "/admin/system-config / SystemConfigPage", "SystemConfig", "list, typed editor, immutable-key guard, audit reason"],
        ]),
        h(2, "5.2 SCR-08 Operator Assignment"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["id", "integer", "response only", "row key"],
            ["employeeId", "string", "required; selected from employee search", "store employee id, not display name"],
            ["employeeName", "string", "read-only", "filled from selected employee"],
            ["positionCode", "enum 06|08|01|02|03", "required", "workflow position selector"],
            ["zoneCode", "string | null", "optional by position", "preserve leading zero if numeric-looking"],
            ["active", "boolean", "required", "deactivation requires reason"],
            ["reason", "string", "required for create/update/deactivate", "audit dialog before submit"],
        ]),
        h(2, "5.3 SCR-09 External Factor"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["factorCode", "string", "required; unique; immutable after create", "uppercase and trim before submit"],
            ["factorName", "string", "required; 1..200 chars", "Thai UTF-8 supported"],
            ["description", "string | null", "optional; max 1000 chars", "multiline editor"],
            ["active", "boolean", "required", "inactive rows remain visible under filter"],
            ["reason", "string", "required for mutation", "include in request and audit"],
        ]),
        h(2, "5.4 SCR-10 Menu Permission Matrix"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["menuCode", "string", "required; row key", "one menu per row"],
            ["menuName", "string", "response only", "Thai display label"],
            ["permissions[].roleCode", "string", "required", "one column per role"],
            ["permissions[].canView", "boolean", "required", "toggle; dirty state tracked per menu"],
            ["reason", "string", "required on save", "save one menu row atomically"],
        ]),
        h(2, "5.5 SCR-11 System Config"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["key", "string", "required; unique; immutable", "configuration key"],
            ["value", "string | number | boolean", "required; validate by valueType", "typed control, never secret input"],
            ["valueType", "enum STRING|INTEGER|DECIMAL|BOOLEAN|URL", "required", "drives editor and validation"],
            ["editable", "boolean", "response only", "false disables edit/delete"],
            ["description", "string", "required", "explain runtime impact"],
            ["reason", "string", "required for mutation", "audit dialog before submit"],
        ]),
        h(2, "5.6 Screen-level Acceptance"),
        bullets([
            "แต่ละ SCR มี route/component/state แยกและสามารถ test/release แยกกันได้",
            "mutation ทุกหน้าส่ง reason และ refresh เฉพาะ resource ที่เปลี่ยน",
            "SCR-08 ไม่รับ employeeName ที่พิมพ์เองแทน employeeId จากผลค้นหา",
            "SCR-09 กัน factorCode ซ้ำทั้ง client response handling และ BE error",
            "SCR-10 rollback toggle เมื่อ save ล้มเหลวและคง dirty indication",
            "SCR-11 ไม่ render secret value และห้ามแก้ record ที่ editable=false",
        ]),
    ]


def testing_delivery_blocks(topic: Topic) -> list[dict[str, Any]]:
    return [
        h(1, "1. Overview"),
        table(["รายการ", "รายละเอียด"], [
            ["Track", topic.track], ["Estimate", f"{topic.hours} ชั่วโมง"], ["Owner", topic.owner],
            ["Document type", "FE verification and release handover specification; not an application screen"],
            ["Objective", topic.objective],
        ]),
        h(1, "2. Delivery Scope"),
        bullets([
            "Regression suites for Dashboard, document lists/create/detail/actions, report, master/config, batch monitor and email template",
            "Contract verification against the endpoint schemas embedded in each feature LLDD",
            "Responsive and browser checks for supported viewports",
            "UAT defect triage, retest evidence and release handover",
            "No screen route, UI field table or synthetic API endpoint is created by this work item",
        ]),
        h(1, "3. Test Suite Matrix"),
        table(["Suite", "Coverage", "Entry condition", "Required evidence"], [
            ["FE-SMOKE", "app bootstrap, menus, dashboard, open list/detail", "deploy reachable and test user available", "timestamped run result and failed-step detail"],
            ["FE-DOC", "create, edit section, attachment, action, timeline and role views", "fixture documents for sections 06/08/01/02/03", "case ID, docNo, requestId and screenshots for failures"],
            ["FE-REPORT", "required filters, 19 columns, totals, CSV parity", "known report fixture and expected aggregate", "query snapshot, row count, totals and exported checksum"],
            ["FE-ADMIN", "SCR-08/09/10/11 plus email template", "admin role and reversible test data", "before/after values and audit reference"],
            ["FE-BATCH", "job selection, editable params, locked params, run history", "job metadata/run fixtures", "request/response capture and UI state"],
            ["FE-RESP", "desktop 1440, tablet 768, mobile 390", "latest supported browsers", "page checklist with overflow/modal/navigation result"],
        ]),
        h(1, "4. Environment and Fixture Contract"),
        table(["Item", "Required content", "Control"], [
            ["Build identity", "commit SHA, build number, deploy timestamp", "freeze before regression"],
            ["API identity", "base URL and contract version", "no production credentials in evidence"],
            ["Role users", "one account per tested RBAC role/profile", "masked identifiers in shared evidence"],
            ["Document fixtures", "docNo per current section plus <=100,000 and >100,000 cases", "resettable or uniquely generated"],
            ["File fixtures", "valid type, >5MB, unsupported type, AV-blocked stub", "checksum recorded"],
            ["Job fixtures", "SUCCESS/FAILED/RUNNING/QUEUED histories", "read-only unless manual-run case"],
        ]),
        h(1, "5. Execution and Defect Flow"),
        table(["Step", "Action", "Exit rule"], [
            [1, "Record build/environment and run FE-SMOKE", "all smoke cases pass before broad regression"],
            [2, "Execute feature suites using fixed fixtures", "each case has pass/fail and evidence reference"],
            [3, "Log defects with severity, route, role, data key, steps and expected/actual", "defect is reproducible or explicitly closed as non-reproducible"],
            [4, "Retest fixes and run impacted regression", "no Critical/High open; Medium has accepted disposition"],
            [5, "Run responsive/browser matrix and release checklist", "all mandatory cells pass"],
            [6, "Produce handover summary", "build identity, known limitations, evidence index and rollback note complete"],
        ]),
        h(1, "6. Release Gate"),
        table(["Gate", "Pass condition"], [
            ["Functional", "All Critical/High feature and workflow cases pass"],
            ["Contract", "No request/response field mismatch against feature LLDD schema tables"],
            ["Visual", "No blocked action, clipped modal/table or unusable navigation at required viewports"],
            ["Security", "Unauthorized routes/actions fail closed; evidence contains no token/secret"],
            ["Data", "Report totals/export parity and action transitions reconcile with persisted result"],
            ["Handover", "Known limitations, rollback steps and test evidence index are complete"],
        ]),
        h(1, "7. Developer / QA Checklist"),
        table(["No", "Check"], [[i + 1, test] for i, test in enumerate(topic.tests)]),
    ]


def create_document_fs_iframe_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Tab Structure"),
        p("หน้า Create Document ต้องมี tab แยกสำหรับสร้างเอกสารจาก FS โดย UI หลักยังเป็น form ของ SBP Mall แต่มี hidden iframe ของ FS เป็น source/submit target จริง"),
        table(
            ["Tab", "Purpose", "Render behavior"],
            [
                ["สร้างเอกสารทั่วไป", "สร้างเอกสาร MANUAL/out-of-condition ผ่าน API ของ SBPGI", "ใช้ form ปกติและ submit POST /api/v1/documents"],
                ["เอกสารจาก FS", "สร้างเอกสารโดยอ้าง field/form ของ FS เดิม", "โหลด FS iframe แบบ hidden แล้วสร้าง SBP form mirror ตาม field ที่พบใน iframe"],
            ],
        ),
        h(2, "5.2 FS iframe Integration Contract"),
        table(
            ["Item", "Required behavior", "Dev note"],
            [
                ["iframe element", "`<iframe id=\"fsCreateFrame\" hidden>` อยู่ในหน้า Create Document", "iframe ต้อง load ก่อน render field mirror; แสดง loading state ระหว่างรอ"],
                ["iframe source", "URL มาจาก config เช่น `fs.createDocumentUrl`", "ห้าม hardcode URL ใน component"],
                ["Access model", "ถ้า same-origin ให้ใช้ DOM adapter; ถ้า cross-origin ให้ใช้ SBP-FS Bridge Protocol v1 ด้านล่างเท่านั้น", "ตรวจ event.origin และ event.source ทุกข้อความ; protocol ไม่พร้อมให้ fail closed พร้อม code FS_BRIDGE_UNAVAILABLE"],
                ["Field discovery", "อ่าน input/select/textarea ใน FS form แล้ว map เป็น SBP field model", "ใช้ name/id/data-label/required/type/options จาก FS เป็น metadata"],
                ["Hidden source of truth", "FS iframe เป็น submit target จริง; SBP form เป็น mirror สำหรับ UX/validation", "ห้าม submit API โดยตรงแทน FS ใน tab นี้ เว้นแต่ FS callback ระบุให้ทำ"],
                ["Submit target", "เมื่อ user กดส่ง ให้ sync values ทั้งหมดเข้า iframe แล้ว trigger submit ของ FS form", "ป้องกัน double submit และรอ iframe load/callback หลัง submit"],
            ],
        ),
        h(2, "5.3 FS Field Mapping"),
        table(
            ["SBP mirror field", "FS iframe field source", "Mapping rule"],
            [
                ["impactedStoreCode", "input[name=impactedStoreCode] หรือ field ที่ FS ระบุเป็นร้านถูกกระทบ", "คง string 5 digits; leading zero ต้องไม่หาย"],
                ["newStoreCode", "input[name=newStoreCode] หรือ field ร้านเปิดใหม่ของ FS", "คง string 5 digits; validate ก่อน sync"],
                ["impactMonth", "month/date field ของ FS", "SBP แสดง พ.ศ. ได้ แต่ sync เป็น format ที่ FS field ต้องการ"],
                ["statementPeriod", "period field ของ FS", "required สำหรับ FS tab"],
                ["roundNo", "round/sequence field ของ FS", "default 1 ถ้า FS field ว่างและ metadata อนุญาต"],
                ["reason/remark", "textarea/input remark ของ FS", "trim ก่อน sync; preserve Thai text"],
                ["dynamicFields[]", "field เพิ่มเติมที่พบใน FS form", "render ตาม type/options/required จาก FS และเก็บ mapping ไว้ใน form state"],
            ],
        ),
        h(2, "5.4 Change and Submit Flow"),
        table(
            ["Step", "FE behavior", "Failure handling"],
            [
                ["1. Open FS tab", "โหลด hidden iframe จาก config และรอ iframe load", "timeout แสดง error พร้อม retry; ไม่ render empty form"],
                ["2. Discover fields", "อ่าน field metadata จาก iframe form แล้วสร้าง SBP mirror form", "field required แต่ไม่รู้ label ให้ใช้ name/id เป็น fallback"],
                ["3. User changes value", "update SBP state แล้ว sync ค่าเข้า iframe field ทันที", "ถ้า sync field ไม่พบ ให้ mark fieldMappingError และห้าม submit"],
                ["4. Client validate", "validate required/type/range ตาม metadata จาก FS และ validation กลางของ SBP", "แสดง inline error ใน SBP form"],
                ["5. Submit", "sync all values อีกครั้ง, dispatch input/change event ใน iframe, แล้ว submit FS form", "disable submit จนกว่า iframe submit result/callback กลับมา"],
                ["6. Handle result", "รับ FS_SUBMIT_RESULT ที่ requestId ตรงกับคำขอ; success navigate ไป detail เมื่อมี docNo", "timeout หรือ schema ไม่ถูกต้องให้ปลด submitting state และแสดง error ที่ retry ได้; ห้ามเดาสถานะสำเร็จ"],
            ],
        ),
        h(2, "5.5 SBP-FS Bridge Protocol v1"),
        table(["Envelope field", "Type", "Required", "Rule"], [
            ["protocolVersion", "literal `1.0`", "Yes", "reject version อื่นด้วย FS_PROTOCOL_VERSION_UNSUPPORTED"],
            ["type", "message enum", "Yes", "FS_FORM_READY | SBP_FIELD_DISCOVERY_REQUEST | FS_FIELD_SCHEMA | SBP_SET_VALUES | SBP_SUBMIT | FS_SUBMIT_RESULT | FS_ERROR"],
            ["requestId", "UUID string", "Yes", "สร้างใหม่ต่อ request และใช้ correlate response"],
            ["correlationId", "UUID string | null", "Response only", "ต้องเท่ากับ requestId ของ message ที่ตอบ"],
            ["timestamp", "ISO-8601 string", "Yes", "ใช้ตรวจ stale message; ไม่ใช้เป็น authorization"],
            ["source", "literal `SBP` | `FS`", "Yes", "ต้องสอดคล้องกับ window ฝั่งผู้ส่ง"],
            ["payload", "object", "Yes", "validate ตาม type ก่อนใช้"],
        ]),
        h(3, "Message payload schemas"),
        table(["Message type", "Payload fields", "Response / rule"], [
            ["FS_FORM_READY", "formId:string, capabilities:string[], schemaVersion:string", "SBP ส่ง SBP_FIELD_DISCOVERY_REQUEST เมื่อ capabilities มี FIELD_SCHEMA"],
            ["SBP_FIELD_DISCOVERY_REQUEST", "formId:string", "FS ตอบ FS_FIELD_SCHEMA ด้วย correlationId"],
            ["FS_FIELD_SCHEMA", "formId:string, fields:FsFieldDescriptor[]", "descriptor ทุกตัวต้องผ่าน schema ด้านล่าง"],
            ["SBP_SET_VALUES", "formId:string, values:Record<string,string|number|boolean|null>", "FS validate key ที่รู้จักและตอบ FS_ERROR เมื่อ map ไม่ได้"],
            ["SBP_SUBMIT", "formId:string, values:Record<...>, clientReference:string", "idempotent ต่อ requestId; ห้าม submit ซ้ำ"],
            ["FS_SUBMIT_RESULT", "success:boolean, fsReference:string|null, docNo:string|null, fieldErrors:FieldError[]", "success=true ต้องมี fsReference; docNo เป็น optional"],
            ["FS_ERROR", "code:string, message:string, retryable:boolean, field:string|null", "FE แสดง message และเปิด retry เฉพาะ retryable=true"],
        ]),
        table(["FsFieldDescriptor field", "Type", "Required", "Constraint"], [
            ["name", "string", "Yes", "unique within form; key used by values map"],
            ["label", "string", "Yes", "UTF-8 display label"],
            ["type", "enum text|number|date|month|select|radio|checkbox|textarea|hidden", "Yes", "unknown type is rejected"],
            ["required", "boolean", "Yes", "drives client validation"],
            ["readOnly", "boolean", "Yes", "read-only field is never overwritten by SBP"],
            ["value", "string|number|boolean|null", "Yes", "initial value"],
            ["options", "array<{value:string,label:string}>|null", "For select/radio", "selected value must exist in options"],
            ["constraints", "{min,max,minLength,maxLength,pattern}|null", "No", "FE and FS both validate"],
        ]),
        h(3, "Handshake, security and timeout"),
        table(["Phase", "Required behavior", "Timeout / failure"], [
            ["Origin setup", "allowlist มาจาก config และ targetOrigin ต้องเป็น origin เฉพาะ ห้ามใช้ `*`", "origin ไม่ตรงให้ ignore และ security log โดยไม่ log payload"],
            ["Ready", "รอ FS_FORM_READY จาก iframe window เดียวกัน", "10s -> FS_BRIDGE_TIMEOUT; retry reload iframe ได้ 1 ครั้ง"],
            ["Schema", "ส่ง discovery และ validate FS_FIELD_SCHEMA", "5s หรือ schema invalid -> FS_FIELD_SCHEMA_INVALID"],
            ["Value sync", "ส่ง SBP_SET_VALUES พร้อม requestId ใหม่และ debounce 150ms", "FS_ERROR ผูก correlationId กลับ field"],
            ["Submit", "ส่ง SBP_SUBMIT หนึ่งครั้งและ disable submit", "30s -> FS_SUBMIT_TIMEOUT; user retry สร้าง requestId ใหม่"],
            ["Result", "ยอมรับเฉพาะ correlationId ที่ pending และ source/origin ถูกต้อง", "late/duplicate result ถูก ignore แบบ idempotent"],
        ]),
        h(3, "Protocol example"),
        payload("FS_FIELD_SCHEMA", api_json({
            "protocolVersion": "1.0", "type": "FS_FIELD_SCHEMA", "requestId": "6f6c8cf0-7df1-4a1a-9e7f-4d953667a824",
            "correlationId": "a8e88f2a-e83b-47ce-99f5-fdcad1876095", "timestamp": "2026-07-22T10:15:00+07:00", "source": "FS",
            "payload": {"formId": "income-guarantee-create", "fields": [{"name": "impactedStoreCode", "label": "รหัสร้านถูกกระทบ", "type": "text", "required": True, "readOnly": False, "value": "00788", "options": None, "constraints": {"pattern": "^[0-9]{5}$"}}]}
        })),
        h(2, "5.6 Acceptance Criteria for FS Tab"),
        bullets([
            "tab เอกสารจาก FS ต้องโหลด hidden iframe และสร้าง mirror form จาก field metadata ได้",
            "เมื่อ user เปลี่ยนค่าใน SBP form ค่าเดียวกันต้องถูก sync เข้า iframe field ที่ map ไว้",
            "กด submit ต้อง sync ทุก field อีกครั้งก่อน submit FS iframe form",
            "field ที่ required ใน FS ต้องแสดง required ใน SBP mirror form",
            "store code 5 หลักต้องไม่สูญเสีย leading zero ระหว่าง SBP form -> iframe",
            "cross-origin ต้อง handshake, discover schema, sync, submit และรับผลผ่าน SBP-FS Bridge Protocol v1 ครบ",
            "message ที่ origin/source/version/correlationId ไม่ถูกต้องต้องถูก ignore หรือ reject แบบ fail closed",
            "timeout และ FS_ERROR ต้องออกจาก loading/submitting state และ retry ได้ตาม retryable flag",
        ]),
    ]


def is_document_detail_role_doc(file_key: str) -> bool:
    return file_key.startswith("FE/LLDD-FE-Document-Detail-Role")


def is_batch_monitor_doc(file_key: str) -> bool:
    return file_key == "FE/LLDD-FE-Batch-Monitor"


def role_profile_code(profile: dict[str, Any]) -> str:
    return f"P-{profile['code']}"


def implementation_detail_blocks(topic: Topic) -> list[dict[str, Any]]:
    if is_document_detail_role_doc(topic.file):
        return role_doc_implementation_blocks(topic)
    if is_batch_monitor_doc(topic.file):
        return batch_monitor_implementation_blocks()
    if "/Jobs/" in topic.file:
        return job_implementation_blocks(topic)
    if topic.track == "FE":
        return fe_implementation_blocks(topic)
    return be_implementation_blocks(topic)


def topic_io_contract_blocks(topic: Topic) -> list[dict[str, Any]]:
    if is_batch_monitor_doc(topic.file):
        return [
            h(2, "4.93 Input / Progress / Output Contract"),
            table(
                ["Stage", "Contract for implementation"],
                [
                    ["Input", "Selected jobNo, editable parameter form values, run-history filters, and current operator permission."],
                    ["Progress", "Load job list, select job, render params/history tabs, validate changed params, save with audit, refresh history after manual run."],
                    ["Output", "Updated job parameter snapshot, visible run-history status, validation messages, and audit reference for saved changes."],
                ],
            ),
        ]
    if "/Jobs/" in topic.file:
        job_no = topic.file.split("LLDD-BE-Job-", 1)[1].split("-", 1)[0]
        legacy = LEGACY_JOB_SOURCES.get(job_no, {})
        rows = [
            ["Input", legacy.get("input", "Job parameters, source files/tables, schedule period, and service-token context defined by this job.")],
            ["Progress", legacy.get("progress", "Create run record, load input, process in chunks, update checkpoint/summary, and expose current state through run history.")],
            ["Output", legacy.get("output", "Target rows/files/interfaces updated according to DB mapping; run history stores status, counts, output reference, and error detail.")],
        ]
        return [
            h(1, "5.1 Input / Progress / Output Contract"),
            table(["Stage", "Contract for implementation"], rows),
        ]

    request_sources = [f"{api.method} {api.path}" for api in topic.apis[:3]]
    db_outputs = [row[0] for row in topic.db_tables if str(row[1]).upper() in {"W", "R/W"}][:3]
    flow_summary = "; ".join(topic.flow[:4]) if topic.flow else "Validate request, apply business rule, persist or render result, and return normalized status."
    rows = [
        ["Input", "; ".join(request_sources) if request_sources else "User action, route/query state, form values, and permission context for this feature."],
        ["Progress", flow_summary],
        ["Output", "; ".join(db_outputs) if db_outputs else "Rendered UI state or normalized API response with status/message and audit-ready trace reference."],
    ]
    return [
        h(1, "5.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], rows),
    ]


def legacy_job_source_blocks(job_no: str) -> list[dict[str, Any]]:
    legacy = LEGACY_JOB_SOURCES.get(job_no)
    if not legacy:
        return []
    return [
        h(2, "5.92 Legacy Java Source Reference"),
        table(
            ["Legacy file", "Line range", "Responsibility to carry forward"],
            legacy["sources"],
        ),
        p("Line ranges refer to the legacy Java implementation under /Users/bank_mac/gosoft/java/SBP/fcsJar. Use these ranges to preserve business behavior while implementing the target Node job."),
    ]


def node_job_skeleton(job_no: str, topic: Topic) -> str:
    function_name = re.sub(r"[^A-Za-z0-9]+", " ", topic.title).title().replace(" ", "")
    function_name = re.sub(r"^\d+", "", function_name)
    spec = JOB_IMPLEMENTATION_SPECS[job_no]
    steps = spec["steps"].split("|")
    step_lines = []
    for index, step in enumerate(steps, start=1):
        previous = "undefined" if index == 1 else f"step{index - 1}"
        step_lines.append(f"    const step{index} = await services.{step}(ctx, {previous});")
    return f"""export async function run{function_name}(ctx, services) {{
  const run = await services.jobRuns.acquire({{
    jobNo: "{job_no}", period: ctx.period, triggeredBy: ctx.triggeredBy
  }});

  try {{
    ctx = {{ ...ctx, runId: run.id, repository: services.{spec['repository']} }};
{chr(10).join(step_lines)}
    const result = step{len(steps)};
    await services.jobRuns.finish(run.id, "SUCCESS", result.metrics);
    return {{ runId: run.id, status: "SUCCESS", ...result }};
  }} catch (error) {{
    await services.jobRuns.finish(run.id, "FAILED", {{
      errorCode: error.code ?? "JOB_FAILED",
      errorMessage: error.message
    }});
    throw error;
  }}
}}"""


def batch_monitor_implementation_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "4.90 Developer Implementation Scope"),
        table(
            ["Area", "Implementation detail", "Definition of done"],
            [
                ["Page shell", "แสดงรายการ job เพื่อเลือก job ที่ต้องดูรายละเอียด และเปิด detail panel ของ job ที่เลือก", "เลือก job แล้ว panel แสดงชื่อ job, คำอธิบาย, tags และ tab default เป็นแบบฟอร์มพารามิเตอร์"],
                ["Tab set", "สร้างเฉพาะ 2 tab ที่ต้องใช้งานจริง: แบบฟอร์มพารามิเตอร์ และประวัติการรัน", "ไม่มี requirement ให้ dev ทำ tab Flowchart การทำงาน หรือ Database ที่ใช้ใน scope นี้"],
                ["Form parameter", "render field ตาม metadata ของแต่ละ job โดยแยก editable/read-only ให้ชัด", "field ที่ read-only แก้ไม่ได้, editable field validate ก่อนบันทึก และส่งเฉพาะค่าที่แก้ได้"],
                ["History run", "แสดงประวัติ run ของ job ที่เลือก พร้อม status, เวลาเริ่ม, เวลาจบ, duration, trigger, ผู้สั่ง และ summary/error", "sort ล่าสุดก่อน, filter status ได้ถ้ามี control บนหน้า, เปิด row เพื่อดู log/detail ได้"],
                ["Reference material", "flowchart การทำงานและฐานข้อมูลที่ใช้เป็นเอกสารอ้างอิงสำหรับ dev เท่านั้น", "ไม่ถูกนับเป็น UI deliverable ของ Batch Monitor และไม่ต้องทำรายละเอียดเทคนิค backend/storage ในเอกสารนี้"],
            ],
        ),
        h(2, "4.91 Two-tab Behavior"),
        table(
            ["Tab", "Visible content", "Editable / Action rule"],
            [
                ["แบบฟอร์มพารามิเตอร์", "ข้อมูลรอบการรัน, cron/schedule, source/target path, file prefix, encoding, batch size, manual run period และ note/runbook ที่เกี่ยวข้อง", "แก้ได้เฉพาะ field ที่ metadata ระบุ editable; save button disabled จนกว่าจะมีการแก้ไขและ validate ผ่าน"],
                ["ประวัติการรัน", "ตาราง run history, status badge, start/end time, duration, trigger type, operator, result summary และปุ่มดูรายละเอียด log", "เป็น read-only; action หลักคือเปิดรายละเอียด run/log จาก row ที่เลือก"],
            ],
        ),
        h(2, "4.92 UI States and Error Handling"),
        table(
            ["State", "Trigger", "UI behavior"],
            [
                ["No selected job", "เปิดหน้าครั้งแรกก่อนเลือก job", "แสดง placeholder ให้เลือก job จากรายการ และไม่แสดง form/history ของ job ใด"],
                ["Loading selected job", "เลือก job หรือ refresh detail", "แสดง loading placeholder เฉพาะ detail panel โดยไม่ clear รายการ job ด้านบน"],
                ["Dirty parameter form", "แก้ editable field แล้ว", "แสดง unsaved indicator, เปิดปุ่มบันทึก และเตือนเมื่อเปลี่ยน job/tab ออกจาก form หากยังไม่บันทึก"],
                ["Validation error", "required/format/range ไม่ผ่าน", "แสดง inline error ใต้ field และไม่บันทึกค่า"],
                ["Empty history", "job ยังไม่มี run history ใน filter ปัจจุบัน", "แสดง empty state ใน tab ประวัติการรัน โดยไม่ซ่อน tab"],
            ],
        ),
    ]


FE_COMPONENT_DETAILS: dict[str, list[tuple[str, str]]] = {
    "FE/LLDD-FE-Integration-Contracts": [
        ("สร้าง shared API client ตัวเดียวสำหรับ base URL, trace header, timeout และ response envelope", "ทุก feature import client กลางและไม่มี axios/fetch instance แยก"),
        ("อ่าน access token จาก platform auth store, แนบ Bearer token และทำ refresh แบบ single-flight", "401 พร้อมกัน refresh ครั้งเดียว, replay request เดิม และไม่สร้างหน้า Login ใหม่"),
        ("แปลง HTTP/Axios failure เป็น ApiError พร้อม code, message, fieldErrors และ traceId โดยไม่แก้ข้อความจาก BE", "validation banner/inline error แสดงข้อความและ traceId จาก response ได้ครบ"),
        ("ให้ formatter กลางสำหรับ ค.ศ./พ.ศ., เดือน, เงิน, percent และ docNo โดยไม่เปลี่ยนค่าที่ส่ง API", "payload ใช้ ค.ศ.; UI แสดง พ.ศ. และรูปแบบเงิน/docNo ตรงกันทุกหน้า"),
        ("กำหนด PageResponse<T> และ state loading/empty/error/retry สำหรับ list ทุกชนิด", "DataTable/Pager รักษา page/filter เดิมและไม่มี list shape เฉพาะหน้า"),
        ("กำหนด typed action request/response และ consume statusCode/nextSection ที่ BE คำนวณ", "FE ส่งเฉพาะ result/comment และไม่มี client-side workflow routing"),
        ("สร้าง sidebar, route guard, visibleSections, editableSections และ actionOptions จาก platform/menu API", "ไม่ hardcode RBAC role เป็นสิทธิ์เมนูหรือ section ที่แก้ไขได้"),
    ],
    "FE/LLDD-FE-Foundation": [
        ("ประกอบ app bootstrap, environment validation, providers และ error boundary โดยไม่สร้าง business screen", "เปิด application shell ได้เมื่อ config ครบ และ fail-fast พร้อมข้อความเมื่อ config ขาด"),
        ("ลงทะเบียน route/module ของ SBP Mall และเชื่อม route guard กับ menuCode จาก API", "ทุก route เข้าได้เฉพาะเมื่อ menu contract อนุญาตและ unknown route ไป not-found"),
        ("จัดโครงสร้าง DTO, API adapter และ query key กลางให้ response typing ตรงกับ contract", "TypeScript build ผ่านและ feature ไม่ cast unknown response แบบ ad hoc"),
        ("รวม status/menu/action constants และ label resolver โดยให้ API dictionary เป็น source of truth", "unknown code แสดง fallback ที่ trace ได้และไม่เพิ่มสถานะเองใน component"),
        ("สร้าง fixture/mock ให้ใช้ schema เดียวกับ response จริง รวม success, empty และ error", "สลับ mock/real adapter ได้โดยไม่แก้ component props หรือ table mapping"),
        ("กำหนด token และ shared UI สำหรับ table, form, modal, badge และ responsive breakpoints", "shared component ใช้งานได้บน desktop/tablet/mobile โดยข้อความและ control ไม่ล้น"),
    ],
    "FE/LLDD-FE-Overview": [
        ("map ค่า waitingTasks, storesThisMonth, compensationThisMonth และ abnormalStores ลง KPI cards", "ทั้งค่าศูนย์/ค่าปกติ format ถูกต้องและ card ไม่คำนวณข้อมูลเพิ่มเอง"),
        ("แสดง task summary/pending queue พร้อม link ไป waiting list โดยรักษา filter ที่เกี่ยวข้อง", "จำนวนงานตรง response และ click card เปิดรายการรอดำเนินการ"),
        ("แปลง monthlyChart เป็น series/axis/tooltip และรองรับเดือนที่ไม่มีข้อมูล", "กราฟแสดงครบทุกเดือน, ค่า 0 ไม่ทำให้ chart blank และ tooltip format เงินถูกต้อง"),
        ("แปลง statusChart ด้วยสี/label จาก dictionary และแสดง legend ที่อ่านได้", "ยอดรวม segment ตรง API และ unknown status ใช้ fallback color/label"),
        ("แยก skeleton, empty, partial-data, error และ retry state โดยไม่ล้างข้อมูลเดิมระหว่าง refresh", "ผู้ใช้ retry ได้และ layout ไม่กระโดดหรือล้นใน mobile"),
    ],
    "FE/LLDD-FE-Document-Lists": [
        ("โหลดงานของผู้ใช้จาก /tasks และ map 9 คอลัมน์หลักพร้อม task owner/status", "waiting list แสดง 9 คอลัมน์ตรง type และรักษา leading zero ของรหัสร้าน"),
        ("ค้นหาเอกสารจาก /documents โดยบังคับปีและแสดงเอกสารที่เกี่ยวข้องตาม permission", "ไม่ call API เมื่อไม่มีปี และ empty result ไม่แสดงข้อมูลจาก query ก่อนหน้า"),
        ("serialize docNo/year/status/store filters ลง query state และ restore เมื่อย้อนกลับจาก detail", "Search/Clear/refresh ให้ผลซ้ำได้และ pagination ใช้ filter ชุดเดียวกัน"),
        ("ควบคุม page/size/sort และ row navigation โดยใช้ docNo เป็น stable key", "เปลี่ยนหน้าไม่ reset filter และเปิด detail ของ row ที่เลือกถูกเลขเอกสาร"),
        ("คำนวณ presentation flag จาก salesDataDays < 60 โดยไม่ใช้ waitingDays แทน", "แถวผิดปกติเป็นสีแดงพร้อม accessible label เฉพาะเมื่อยอดขายไม่ครบ 60 วัน"),
    ],
    "FE/LLDD-FE-Create-Document": [
        ("เป็นเจ้าของ source/activeTab, draft state และ unsaved-change guard ของหน้า create", "สลับ MANUAL/FS แล้ว field ที่ไม่เกี่ยวข้องไม่รั่วเข้า payload"),
        ("render manual form, store selectors, period, roundNo และ reason สำหรับเอกสารนอกเงื่อนไข", "required/format ผ่านก่อน POST และ docNo จาก response ใช้เปิด detail"),
        ("โหลด hidden FS iframe ด้วย config URL และจัด lifecycle timeout/origin/callback", "iframe load/error/timeout มี state ชัดเจนและไม่ submit ก่อน bridge พร้อม"),
        ("ค้นหา impacted/new store, คง leading zero และเติมชื่อ/ภาคจากรายการที่เลือก", "เลือกผิด type ไม่ได้และ clear selection ล้าง dependent fields ครบ"),
        ("แปลงเดือน/ปีที่แสดงเป็น พ.ศ. ไป payload YYYY-MM ค.ศ. พร้อม source-specific validation", "period/statementPeriod/roundNo ส่ง type และ format ตรง API"),
        ("สร้าง mirror field registry จาก FS metadata และ sync input/select/textarea เข้า iframe", "ทุก field มี mapping/type/event และ missing mapping block submit ด้วย FS_FIELD_MAPPING_MISSING"),
        ("รวม client validation, API fieldErrors และ FS bridge errors ใต้ control ที่เกี่ยวข้อง", "focus ไป error แรกและข้อความเดิมคงอยู่จนผู้ใช้แก้ field นั้น"),
        ("แยก Save Draft, Submit MANUAL และ Submit FS พร้อม disable/confirm/dedup ระหว่าง request", "double click ไม่สร้างซ้ำและ success/error แสดงผลตาม channel ที่ส่งจริง"),
    ],
    "FE/LLDD-FE-Document-Detail": [
        ("โหลดและแสดง docNo, status, impacted store, impact month และ current operator จาก aggregate response", "header refresh หลัง mutation และ status badge resolve จาก statusCode"),
        ("render new-store, competitor และ factor collections ด้วย row key และ typed value mapping", "ข้อมูลอ่าน/แก้/ลบตรง editableSections และ percent รวมตรวจได้ 100"),
        ("ใช้ visibleSections/editableSections/canAction เป็น source of truth สำหรับ DOM และ focusable controls", "section ที่ซ่อนไม่อยู่ใน DOM และ read-only section ไม่มี mutation control"),
        ("สร้าง action radio/comment/confirm จาก actionOptions และ requireComment ที่ API ส่งมา", "ไม่ hardcode route/nextSection และ block submit เมื่อ result/comment ไม่ครบ"),
        ("รวม consideration history, workflow timeline และ invalidate หลัง save/upload/action", "ลำดับเวลาใหม่สุดถูกต้องและข้อมูลหลัง submit ไม่ค้างจาก cache เดิม"),
        ("upload ด้วย allowlist/5MB/scan state และ download ผ่าน authorized BE stream", "BLOCKED/PENDING ดาวน์โหลดไม่ได้และ success แสดงชื่อ/ขนาดไฟล์จาก metadata"),
        ("เปิด ALLMAP/map และ sales detail ด้วย doc/store context โดยไม่ expose credential", "link/adapter ส่ง identifier ถูกตัวและ failure กลับสู่หน้า detail ได้"),
    ],
    "FE/LLDD-FE-Testing-Delivery": [
        ("จัด regression matrix ครบ route, role profile, happy path และ typed error path", "ทุก route หลักมีผลทดสอบพร้อม browser/viewport/evidence"),
        ("ตรวจ desktop/tablet/mobile สำหรับ table, modal, form, chart และ navigation", "ไม่มี overflow/overlap และ control สำคัญใช้งานได้ทุก viewport ที่กำหนด"),
        ("เทียบ request/response fixture กับ API field schema และ error catalog", "schema mismatch เป็นศูนย์และไม่มี toy payload ที่ขาด required field"),
        ("ผูก defectId กับ test case, retest build ที่แก้ และเก็บ before/after evidence", "Critical/High defect ปิดพร้อมหลักฐานและ regression รอบเกี่ยวข้องผ่าน"),
        ("ประเมิน build/typecheck, secret scan, contract parity และ unresolved blocker ก่อน release", "release gate fail-closed เมื่อข้อบังคับข้อใดไม่ผ่าน"),
        ("จัด delivery note, test summary, known limitations และ reproducible verification commands", "ผู้รับมอบตรวจซ้ำได้โดยไม่มี token/secret หรือไฟล์ QA ชั่วคราว"),
    ],
    "FE/LLDD-FE-Report": [
        ("จัดการ filter store/month/type/status/result/region/statement period พร้อม dependency validation", "status/result required และช่วง from-to ทุกคู่ตรวจผ่านก่อน Preview/Export"),
        ("map response เป็น summary line, chart และตาราง 19 คอลัมน์ด้วย formatter กลาง", "คอลัมน์/ยอดรวม/วันที่/leading zero ตรง response และข้อมูลยอดขายผิดปกติใช้ salesDataDays"),
        ("แสดง preview/detail โดยใช้ filter snapshot เดียวกับผลลัพธ์ที่กำลังดู", "เปิดเอกสารถูก docNo และปิด modal แล้ว filter/table ไม่ reset"),
        ("ส่ง filter snapshot ล่าสุดไป export endpoint และจัดการ queued/download/error state", "export ใช้เงื่อนไขเดียวกับ preview และชื่อไฟล์/content type ตรง response"),
        ("รองรับ fixture สำหรับ 0 แถว, หลาย region/type, เกิน threshold และยอดขายไม่ครบ 60 วัน", "sample verification ครอบคลุม chart/table/export parity โดยไม่ฝังข้อมูลทดสอบใน production"),
    ],
    "FE/LLDD-FE-Master-Config": [
        ("โหลด/ค้นหา/เพิ่ม/แก้/ปิด operator โดยเลือก employee จาก employee search", "duplicate/invalid employee ถูก block และ mutation สำเร็จ refresh row/audit"),
        ("จัดการ factor CRUD รวม DELETE เฉพาะรายการที่ไม่ถูกใช้งานและต้องมี reason", "factorCode ซ้ำไม่ได้, conflict แสดงข้อความ และ deleted row หายหลัง refresh"),
        ("render role x menu matrix จาก canAccess และบันทึก permission ราย menu", "toggle optimistic ได้เฉพาะเมื่อ rollback on error และค่าหลัง reload ตรงฐานข้อมูล"),
        ("render config ตาม valueType/unit/isEditable และกัน secret/locked config จากการแก้", "type/range validation ผ่านและ isEditable=false ไม่มี enabled mutation control"),
        ("ใช้ modal mode ADD/EDIT/DELETE แยก initial values, validation และ confirm copy", "เปลี่ยน mode ไม่ทิ้ง stale field และปุ่ม submit กัน double request"),
        ("บังคับ reason สำหรับ mutation และแสดง auditId/updatedBy/updatedAt หลังบันทึก", "mutation ที่ไม่มี reason ไม่ออก request และ evidence trace กลับ audit log ได้"),
    ],
    "FE/LLDD-FE-Email-Template": [
        ("โหลดรายการ template พร้อม code, subject, channel, updatedAt และ active state", "ค้นหา/เลือก template ใช้ code เป็น key และ empty state ไม่แสดง editor ค้าง"),
        ("แก้ subject/body ด้วย dirty state, variable validation และ reason ก่อนบันทึก", "save disabled เมื่อไม่เปลี่ยนค่า/invalid และ reload แล้วค่าใหม่ตรง API"),
        ("แสดง variable catalog และ insert token ณ cursor โดยไม่เปลี่ยน syntax", "unknown/missing variable ถูกแจ้งก่อน preview/save"),
        ("เรียก preview endpoint ด้วย sample variables และ render subject/body แบบปลอดภัย", "preview ไม่ execute HTML/script และแสดง missing-variable error ตรง contract"),
        ("ยืนยัน reset default พร้อม reason และแสดง diff/ผลลัพธ์หลัง reset", "cancel ไม่เปลี่ยนค่า; confirm แล้ว editor/list refresh เป็น default version"),
        ("แสดง From/To/Cc/recipient rule แบบ read-only จาก notification contract", "ผู้ใช้แก้ recipient rule จากหน้านี้ไม่ได้และ label ตรง rule ที่ backend ส่ง"),
    ],
}


def fe_implementation_blocks(topic: Topic) -> list[dict[str, Any]]:
    feature_name = topic.title.replace("LLDD FE - ", "")
    api_rows = []
    for index, spec in enumerate(topic.apis):
        endpoint_path = spec.path.split("?", 1)[0]
        matching_actions = [
            f"{action} ({trigger})"
            for action, trigger, service, _ in topic.actions
            if endpoint_path in service or service in spec.path
        ]
        if spec.buttons:
            invoked_by = ", ".join(spec.buttons)
        elif matching_actions:
            invoked_by = "; ".join(matching_actions)
        elif topic.actions:
            action, trigger, _, _ = topic.actions[index % len(topic.actions)]
            invoked_by = f"{action} ({trigger})"
        else:
            invoked_by = "contract verification step ที่ระบุใน test matrix ของเอกสารนี้"
        api_rows.append([f"{spec.method} {spec.path}", spec.purpose, invoked_by])
    if not api_rows:
        api_rows = [["No direct endpoint", "งานนี้ไม่สร้าง endpoint จำลอง", "ใช้ผลทดสอบ/บริการจาก feature ที่ตรวจ"]]
    component_rows = []
    component_details = FE_COMPONENT_DETAILS.get(topic.file)
    if component_details and len(component_details) != len(topic.scope):
        raise ValueError(f"FE component detail count mismatch for {topic.file}")
    for index, scope_item in enumerate(topic.scope, start=1):
        if component_details:
            responsibility, done_rule = component_details[index - 1]
        else:
            field_hint = topic.fields[(index - 1) % len(topic.fields)][0] if topic.fields else "localState"
            responsibility = f"จัดการ {scope_item} ใน {feature_name} ด้วย typed state `{field_hint}` ตาม field/action contract ของเอกสารนี้"
            done_rule = topic.acceptance[(index - 1) % len(topic.acceptance)] if topic.acceptance else f"{scope_item} ผ่าน component และ interaction test"
        component_rows.append([f"C{index:02d}", scope_item, responsibility, done_rule])
    action_rows = [[action, trigger, service, result] for action, trigger, service, result in topic.actions]
    if not action_rows:
        action_rows = [["Render/read-only", "feature load", "local/shared state", "แสดงผลตาม scope โดยไม่มี mutation"]]
    failure_rows = []
    for index, case in enumerate(topic.tests[:6], start=1):
        expected = topic.acceptance[(index - 1) % len(topic.acceptance)] if topic.acceptance else "UI ต้องอยู่ใน state ที่ retry หรือแก้ข้อมูลได้"
        failure_rows.append([f"FE-{index:02d}", case, expected])
    return [
        h(2, f"5.90 {feature_name} Component Contract"),
        table(["ID", "Component / Scope", "Single responsibility", "Definition of done"], component_rows),
        h(2, f"5.91 {feature_name} API Adapter Map"),
        table(["Endpoint", "Typed adapter purpose", "Invoked by"], api_rows),
        h(2, f"5.92 {feature_name} Interaction State Machine"),
        table(["Action", "Trigger", "API / State transition", "Expected visible result"], action_rows),
        h(2, f"5.93 {feature_name} Feature Failure Checks"),
        table(["Case", "Feature-specific scenario", "Expected evidence"], failure_rows),
    ]


def be_implementation_blocks(topic: Topic) -> list[dict[str, Any]]:
    endpoint_rows = []
    for index, spec in enumerate(topic.apis, start=1):
        endpoint_rows.append([
            f"{spec.method} {spec.path}",
            spec.purpose,
            topic.flow[(index - 1) % len(topic.flow)] if topic.flow else "validate -> execute -> map response",
            topic.acceptance[(index - 1) % len(topic.acceptance)] if topic.acceptance else "contract test ผ่าน",
        ])
    if not endpoint_rows:
        endpoint_rows = [["Internal service", topic.objective, "เรียกจาก use case ภายในเท่านั้น", topic.acceptance[0] if topic.acceptance else "service test ผ่าน"]]
    sequence_rows = []
    for index, step in enumerate(topic.flow, start=1):
        failure = topic.tests[(index - 1) % len(topic.tests)] if topic.tests else "failure ต้อง rollback หรือ fail closed"
        sequence_rows.append([index, step, failure])
    if not sequence_rows:
        sequence_rows = [[1, "อ่านข้อมูลตาม DB Mapping และคืนผลตาม contract", "ไม่พบข้อมูลคืน typed error"]]
    return [
        h(2, "5.90 Endpoint Implementation Contract"),
        table(["Endpoint", "Use-case owner", "Service/repository behavior", "Definition of done"], endpoint_rows),
        h(2, "5.91 Backend Execution Sequence"),
        table(["Step", "Behavior specific to this LLDD", "Failure/test evidence"], sequence_rows),
    ]


def job_implementation_blocks(topic: Topic) -> list[dict[str, Any]]:
    job_no = topic.file.split("LLDD-BE-Job-", 1)[1].split("-", 1)[0]
    spec = JOB_IMPLEMENTATION_SPECS[job_no]
    legacy = LEGACY_JOB_SOURCES[job_no]
    stage_rows = []
    for index, step_name in enumerate(spec["steps"].split("|"), start=1):
        stage_rows.append([index, step_name, spec["repository"], "คืน metrics และ throw typed error; transaction/rerun ใช้ contract ด้านล่าง"])
    blocks = [
        h(2, f"5.90 Job {job_no} Execution Stages"),
        p(legacy["progress"]),
        table(["Order", "Service step", "Repository", "Output / failure contract"], stage_rows),
        h(2, f"5.91 Job {job_no} Run Evidence"),
        table(["Evidence", "Job-specific value", "Acceptance"], [
            ["Input identity", legacy["input"], "snapshot input file/business key/period in run record"],
            ["Output identity", legacy["output"], "reconcile input, success, reject and skipped counts"],
            ["Dedup proof", spec["idempotency"], "rerun fixture produces no duplicate target business key"],
            ["Transaction proof", spec["transaction"], "injected failure leaves no partial committed state outside documented boundary"],
            ["Security proof", spec["security"], "config/log/error contains no plaintext secret"],
        ]),
    ]
    blocks.extend(legacy_job_source_blocks(job_no))
    blocks.extend([
        h(2, "5.93 Target Repository and SQL Contract"),
        table(
            ["Contract", "Target implementation"],
            [
                ["Repository", spec["repository"]],
                ["Idempotency / dedup", spec["idempotency"]],
                ["Transaction boundary", spec["transaction"]],
                ["Security", spec["security"]],
            ],
        ),
        h(3, "Input / candidate query"),
        code(spec["read"], "sql"),
        h(3, "Write / upsert query"),
        code(spec["write"], "sql"),
        h(2, "5.94 Target Node Implementation"),
        p("โครงสร้างนี้ระบุ service/repository เฉพาะงานและต้อง implement ตาม SQL, transaction, idempotency และ security contract ด้านบน โดยทุกขั้นต้องคืน metrics สำหรับ reconcile และ run history"),
        code(node_job_skeleton(job_no, topic), "js"),
    ])
    if job_no == "4":
        blocks.extend([
            h(2, "5.95 Job 4 Atomic File / Outbox Sequence"),
            table(
                ["Order", "Required action", "Failure behavior"],
                [
                    [1, "lock candidate W ด้วย FOR UPDATE SKIP LOCKED และสร้าง payload ใน memory", "validation fail: rollback lock; สถานะยัง W"],
                    [2, "เขียน temporary file, fsync, atomic rename และคำนวณ SHA-256", "write/rename/checksum fail: ลบ temp; สถานะยัง W; ไม่สร้าง outbox"],
                    [3, "transaction เดียว update W→P และ insert interface_transactions/outbox READY", "DB fail: rollback W→P และ outbox; durable file คงไว้ให้ cleanup/reconcile โดย checksum"],
                    [4, "dispatcher อ่าน READY แล้วส่ง SFTP; compare checksum ก่อนส่ง", "ส่ง fail: outbox ยัง READY/FAILED_RETRY; ห้ามเปลี่ยน candidate กลับ W เพื่อไม่ให้สร้างไฟล์ซ้ำ"],
                    [5, "ส่งสำเร็จ mark SENT; callback/import ที่สัมพันธ์กัน mark ACKED", "ใช้ transaction id เดิมตลอด lifecycle"],
                ],
            ),
        ])
    if job_no == "6":
        blocks.extend([
            h(2, "5.95 Tracking Retention / Purge SQL"),
            p("Purge ทำได้เฉพาะ ACKED/COMPLETED ที่ครบ purge_after และไม่อยู่ใน legal hold; ต้องรันเป็น batch จำกัดจำนวนเพื่อไม่ lock ตารางยาว"),
            code("""WITH purge_candidates AS (
    SELECT id
    FROM interface_transactions
    WHERE status IN ('ACKED', 'COMPLETED')
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
      AND data_name = ANY(:sta_data_names)
    ORDER BY id
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;""", "sql"),
        ])
    if job_no == "8":
        blocks.extend([
            h(2, "5.95 Job 8 Document Number Gap and Rerun Policy"),
            p("Job 8 ใช้ running number แบบ monotonic ต่อปี พ.ศ. ช่องว่างของเลขเอกสารจาก concurrent rerun หรือ ON CONFLICT เป็นพฤติกรรมที่ยอมรับได้ เพราะเลขที่มีหน้าที่รับประกัน uniqueness ไม่ได้รับประกันความต่อเนื่อง"),
            table(
                ["Case", "Required behavior", "Evidence / metric"],
                [
                    ["Rerun พบ impact_process_id เดิมก่อนจองเลข", "คืน/ข้ามด้วย doc_no เดิมโดยไม่จอง running_no เพิ่มเมื่อ fast lookup พบข้อมูลแล้ว", "duplicateExistingCount + existingDocNo"],
                    ["Concurrent worker ชน ON CONFLICT หลังจองเลข", "ยอมให้ running_no ที่จองแล้วกลายเป็น gap; ห้ามลด sequence และห้ามนำเลขกลับมาใช้", "numberGapCount + conflictedImpactProcessId"],
                    ["Conflict path", "อ่าน compensation_documents ด้วย impact_process_id แล้วใช้ d.doc_no เดิมสำหรับ tracking/reconcile", "tracking.doc_no ตรงกับเอกสารที่ commit อยู่จริง"],
                    ["New document path", "insert document และ INTERNAL_DB_WRITE tracking ใน transaction เดียว", "createdCount และ trackingCount เพิ่มเท่ากัน"],
                    ["Audit/runbook", "อธิบายว่าเลขอาจไม่ต่อเนื่องแต่ต้องไม่ซ้ำและตรวจสอบย้อนกลับได้", "ไม่มีขั้นตอน manual reuse หรือ renumber"],
                ],
            ),
        ])
    return blocks


def role_doc_implementation_blocks(topic: Topic) -> list[dict[str, Any]]:
    profile = document_detail_role_profile(topic.file)
    if not profile:
        raise ValueError(f"Missing role profile for {topic.file}")
    profile_code = f"P-{profile['code']}"
    visible = ", ".join(profile["visible"])
    hidden = ", ".join(profile["hidden"]) if profile["hidden"] else "ไม่มี section ที่ซ่อนเพิ่มจาก profile"
    editable = ", ".join(profile["editable"]) if profile["editable"] else "ไม่มี; business section ทั้งหมด read-only"
    actions = "; ".join(action[0] for action in profile["actions"])
    comment_rules = "; ".join(f"{action}: {rule}" for action, rule in profile["actions"])
    return [
        h(2, f"5.90 {topic.title.replace('LLDD FE - ', '')} Implementation Steps"),
        table(
            ["Step", "Implementation detail", "Check"],
            [
                ["Load exact profile", f"เรียก GET /api/v1/documents/{{docNo}} และยืนยัน roleProfileCode={profile_code}, statusCode={profile['code']} ก่อน render action state", f"profile mismatch ต้อง fail closed; ไม่ใช้ role switcher เพื่อจำลอง {profile_code}"],
                ["Render profile sections", f"render เฉพาะ visibleSections ของ {profile_code}: {visible}; ซ่อน: {hidden}", "section ที่ซ่อนต้องไม่อยู่ใน DOM และ section key ที่ไม่รู้จักต้อง log/ignore แบบ fail closed"],
                ["Apply edit boundary", f"เปิด mutation control เฉพาะ editableSections ของ {profile_code}: {editable}", "read-only section ไม่มี focusable input/save/add/delete และ payload ต้องไม่มี field นอก editableSections"],
                ["Attachment control", f"canUploadAttachment={str(profile['upload']).lower()} สำหรับ {profile['short']}; ใช้ allowlist, 5 MB และ scan-status contract", "ปุ่ม upload ตรง flag, FILE_TOO_LARGE/FILE_SCAN_BLOCKED แสดงที่ attachment section"],
                ["Render exact action set", f"แสดง actionOptions ของ {profile_code} เท่านั้น: {actions}; comment rules: {comment_rules}", "radio label/requireComment มาจาก API และ FE ไม่คำนวณ nextSection"],
                ["Submit and reload", f"ส่ง result/comment สำหรับ {profile_code} แล้ว invalidate detail, timeline, task/list cache", f"หลัง submit ต้องโหลด status/actionOptions ใหม่และไม่คง action set ของ {profile_code} เมื่อ workflow เปลี่ยนขั้น"],
            ],
        ),
    ]


def document_detail_role_profiles() -> list[dict[str, Any]]:
    common_read = [
        "doc-header",
        "sec-sales",
        "sec-map",
        "sec-newstore",
        "sec-competitor",
        "sec-factor",
        "sec-attach",
        "sec-comp-history",
        "sec-decision-history",
        "sec-action",
    ]
    return [
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA",
            "code": "06",
            "name": "ฝ่าย SBP DSA",
            "short": "SBP DSA",
            "status": "รอฝ่าย SBP DSA ดำเนินการ",
            "purpose": "ตรวจความครบถ้วนเบื้องต้นและเลือกส่งต่อ/ยุติตามผลพิจารณา",
            "visible": common_read,
            "editable": [],
            "hidden": ["sec-calc"],
            "upload": True,
            "summary": [
                "เห็นข้อมูลเอกสารครบสำหรับตรวจสอบ แต่ทุก section เนื้อหาเป็น read-only",
                "เพิ่มเอกสารแนบประกอบการพิจารณาได้",
                "ไม่เห็น section คำนวณเงินชดเชย",
            ],
            "fields": [
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment required เมื่อเลือก เห็นควรไม่ชดเชย"],
            ],
            "actions": [
                ["เห็นควรไม่ชดเชย", "ต้องกรอก comment"],
                ["หยุดชดเชยประกันรายได้", "comment optional"],
                ["ส่งฝ่ายส่งเสริมธุรกิจ SBP", "comment optional"],
                ["ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "comment optional"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-06 แล้ว sec-calc ต้องไม่ render",
                "section ร้านเปิดใหม่/คู่แข่ง/ปัจจัยต้องไม่มี input/edit/delete/save",
                "ไม่เลือก result แล้วกดส่ง ต้องแสดง popup verbatim",
                "เลือก เห็นควรไม่ชดเชย โดยไม่กรอก comment ต้อง error ACTION_COMMENT_REQUIRED",
                "upload ไฟล์เกิน 5 MB ต้อง error FILE_TOO_LARGE",
            ],
        },
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer",
            "code": "08",
            "name": "เจ้าหน้าที่ SBP DSA",
            "short": "SBP DSA Officer",
            "status": "รอเจ้าหน้าที่ SBP DSA ดำเนินการ",
            "purpose": "ตรวจ/ยืนยันผลคำนวณเงินชดเชยและส่งผลพิจารณา",
            "visible": common_read + ["sec-calc"],
            "editable": [],
            "hidden": [],
            "upload": True,
            "summary": [
                "เห็น section คำนวณเงินชดเชยเพิ่มเติมจากบทบาทอื่น",
                "section คำนวณเป็น display-only ไม่ใช่ editor",
                "เพิ่มเอกสารแนบและส่ง action ได้",
            ],
            "fields": [
                ["คำนวณเงินชดเชย", "baseCompensationAmount, totalCompensatePercent, totalCompensationAmount, approvalLimitIndicator", "read-only; แสดง <=100,000 หรือ >100,000 จาก API"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment ตาม actionOptions.requireComment"],
            ],
            "actions": [
                ["คำนวณเงินชดเชยเรียบร้อย", "comment optional"],
                ["ส่งกลับฝ่าย SBP DSA", "comment ตาม actionOptions.requireComment"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-08 แล้ว sec-calc ต้องแสดง",
                "sec-calc ต้องไม่มี input/button บันทึก",
                "section ร้านเปิดใหม่/คู่แข่ง/ปัจจัยต้อง read-only",
                "action radio แสดงเฉพาะ 2 รายการของ role 08",
                "หลัง submit ต้อง reload detail/timeline/status",
            ],
        },
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion",
            "code": "01",
            "name": "ฝ่ายส่งเสริมธุรกิจฯ",
            "short": "Business Promotion",
            "status": "รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ",
            "purpose": "ปรับข้อมูลร้านเปิดใหม่ ร้านคู่แข่ง ปัจจัยอื่น และส่งผลพิจารณา",
            "visible": common_read,
            "editable": ["sec-newstore", "sec-competitor", "sec-factor"],
            "hidden": ["sec-calc"],
            "upload": True,
            "summary": [
                "เป็น role profile เดียวที่แก้เนื้อหาเอกสารได้",
                "แก้ % ชดเชย เพิ่ม/แก้/ลบร้านคู่แข่ง และเพิ่ม/แก้/ลบปัจจัยอื่นได้",
                "ไม่เห็น section คำนวณเงินชดเชย",
            ],
            "fields": [
                ["ร้านเปิดใหม่", "newStoreCode, newStoreName, openDate, distanceKm, compensatePercent, calculatedCompensationAmount", "แก้ได้เฉพาะ compensatePercent; ผลรวมต้องเท่ากับ 100"],
                ["ร้านคู่แข่ง", "competitorName, openedImpactDate, detail, remark", "เพิ่ม/แก้/ลบได้; ต้องเลือกร้านคู่แข่งก่อนบันทึก"],
                ["ปัจจัยอื่นๆ", "factorName, startDate, endDate, detail, remark", "เพิ่ม/แก้/ลบได้; endDate ต้องไม่ก่อน startDate"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment required เมื่อเลือก เห็นควรไม่ชดเชย"],
            ],
            "actions": [
                ["เห็นควรชดเชย", "comment optional"],
                ["เห็นควรไม่ชดเชย", "ต้องกรอก comment"],
                ["ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)", "comment ตาม actionOptions.requireComment"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-01 แล้ว sec-newstore/sec-competitor/sec-factor ต้อง editable",
                "แก้ compensatePercent แล้วรวมไม่ครบ 100 ต้อง error COMPENSATE_PERCENT_INVALID",
                "เพิ่มร้านคู่แข่งโดยไม่เลือก competitor ต้อง error COMPETITOR_REQUIRED",
                "เพิ่มปัจจัยอื่นโดยไม่เลือก factor ต้อง error EXTERNAL_FACTOR_REQUIRED",
                "sec-calc ต้องไม่ render สำหรับ role 01",
            ],
        },
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion",
            "code": "02",
            "name": "GM ส่งเสริมธุรกิจฯ",
            "short": "GM Business Promotion",
            "status": "รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ",
            "purpose": "อ่านข้อมูลประกอบการอนุมัติวงเงินและส่งผลพิจารณา",
            "visible": common_read,
            "editable": [],
            "hidden": ["sec-calc"],
            "upload": True,
            "summary": [
                "เห็นข้อมูลเอกสารทั้งหมดแบบ read-only",
                "เพิ่มเอกสารแนบประกอบการอนุมัติได้",
                "FE แสดงข้อความช่วยตัดสินจากยอดชดเชยรวม แต่ไม่คำนวณปลายทาง action เอง",
            ],
            "fields": [
                ["ข้อมูลประกอบอนุมัติ", "totalCompensationAmount, approvalLimitIndicator", "read-only จาก API; ใช้แสดง <=100,000 หรือ >100,000"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment ตาม actionOptions.requireComment"],
            ],
            "actions": [
                ["เห็นควรชดเชย", "comment optional"],
                ["เห็นควรไม่ชดเชย", "comment ตาม actionOptions.requireComment"],
                ["ส่งกลับฝ่ายส่งเสริมธุรกิจ SBP", "comment ตาม actionOptions.requireComment"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-02 แล้วทุก business section ต้อง read-only",
                "sec-calc ต้องไม่ render",
                "action radio แสดงเฉพาะ 3 รายการของ role 02",
                "แสดง totalCompensationAmount/approvalLimitIndicator โดยไม่คำนวณ route ใน FE",
                "หลัง submit ต้อง reload detail/timeline/status",
            ],
        },
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP",
            "code": "03",
            "name": "AVP สำนักบริหาร SBP",
            "short": "AVP SBP",
            "status": "รอผู้บริหารสำนักบริหาร SBP ดำเนินการ",
            "purpose": "อ่านข้อมูลประกอบการอนุมัติระดับสูงและส่งผลพิจารณา",
            "visible": common_read,
            "editable": [],
            "hidden": ["sec-calc"],
            "upload": True,
            "summary": [
                "เห็นข้อมูลเอกสารทั้งหมดแบบ read-only",
                "ต้องเห็นประวัติพิจารณา/timeline เพื่อประกอบการตัดสินใจ",
                "เพิ่มเอกสารแนบและส่ง action ได้",
            ],
            "fields": [
                ["ข้อมูลประกอบอนุมัติ", "doc-header, totalCompensationAmount, considerationHistory, timeline", "read-only ทั้งหมด"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment ตาม actionOptions.requireComment"],
            ],
            "actions": [
                ["เห็นควรชดเชย", "comment optional"],
                ["เห็นควรไม่ชดเชย", "comment ตาม actionOptions.requireComment"],
                ["ส่งกลับ GM ส่งเสริมธุรกิจฯ", "comment ตาม actionOptions.requireComment"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-03 แล้วทุก business section ต้อง read-only",
                "sec-calc ต้องไม่ render",
                "history/timeline ต้องแสดงก่อนส่ง action ได้",
                "action radio แสดงเฉพาะ 3 รายการของ role 03",
                "หลัง submit ต้อง reload detail/timeline/status",
            ],
        },
    ]


def document_detail_role_profile(file_key: str) -> dict[str, Any] | None:
    for profile in document_detail_role_profiles():
        if profile["file"] == file_key:
            return profile
    return None


def document_detail_role_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Role-based Render Contract (ไม่ใช่ Routing Spec)"),
        p("หน้า Document Detail ต้องแสดงผลตาม role profile ที่ API ส่งมาเท่านั้น โดย role profile ระบุ visibleSections, editableSections และ actionOptions สำหรับผู้ใช้ที่ login จริง FE ไม่ต้องมี role switcher และไม่ต้องฝังตาราง action routing ใน production"),
        h(3, "Section Inventory"),
        table(
            ["Section key", "UI section", "Default display", "Editable by"],
            [
                ["doc-header", "ข้อมูลร้านถูกกระทบ", "read-only", "-"],
                ["sec-sales", "แนวโน้มยอดขายรายวัน", "read-only", "-"],
                ["sec-map", "แผนที่ AllMap", "read-only", "-"],
                ["sec-newstore", "ร้านเปิดใหม่", "read-only", "role profile 01"],
                ["sec-competitor", "ร้านคู่แข่งเปิดกระทบ", "read-only", "role profile 01"],
                ["sec-factor", "ปัจจัยอื่นๆ", "read-only", "role profile 01"],
                ["sec-attach", "เอกสารแนบทั้งหมด", "visible + upload", "all action roles upload"],
                ["sec-calc", "คำนวณเงินชดเชย", "hidden", "visible-only role profile 08"],
                ["sec-comp-history", "ประวัติการชดเชย", "read-only", "-"],
                ["sec-decision-history", "ผลการพิจารณา (ประวัติ)", "read-only", "-"],
                ["sec-action", "พิจารณา / ส่งดำเนินการ", "visible", "current action role"],
            ],
        ),
        h(3, "Role × Section Display Matrix"),
        p("E = แก้ไขได้, R = อ่านอย่างเดียว, H = ซ่อน, Upload = เพิ่มเอกสารแนบได้"),
        table(
            ["Section", "06 ฝ่าย SBP DSA", "08 จนท. SBP DSA", "01 ฝ่ายส่งเสริมธุรกิจฯ", "02 GM ส่งเสริมฯ", "03 AVP สำนักบริหาร SBP"],
            [
                ["doc-header", "R", "R", "R", "R", "R"],
                ["sec-sales", "R", "R", "R", "R", "R"],
                ["sec-map", "R", "R", "R", "R", "R"],
                ["sec-newstore", "R", "R", "E", "R", "R"],
                ["sec-competitor", "R", "R", "E", "R", "R"],
                ["sec-factor", "R", "R", "E", "R", "R"],
                ["sec-attach", "R+Upload", "R+Upload", "R+Upload", "R+Upload", "R+Upload"],
                ["sec-calc", "H", "R", "H", "H", "H"],
                ["sec-comp-history", "R", "R", "R", "R", "R"],
                ["sec-decision-history", "R", "R", "R", "R", "R"],
                ["sec-action", "Action set 06", "Action set 08", "Action set 01", "Action set 02", "Action set 03"],
            ],
        ),
        h(3, "Action Panel Options"),
        table(
            ["Role profile", "Radio options shown", "Required comment rule"],
            [
                ["06 ฝ่าย SBP DSA", "เห็นควรไม่ชดเชย; หยุดชดเชยประกันรายได้; ส่งฝ่ายส่งเสริมธุรกิจ SBP; ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "บังคับเมื่อเลือก เห็นควรไม่ชดเชย"],
                ["08 เจ้าหน้าที่ SBP DSA", "คำนวณเงินชดเชยเรียบร้อย; ส่งกลับฝ่าย SBP DSA", "บังคับเมื่อ actionOptions.requireComment=true"],
                ["01 ฝ่ายส่งเสริมธุรกิจฯ", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)", "บังคับเมื่อเลือก เห็นควรไม่ชดเชย"],
                ["02 GM ส่งเสริมธุรกิจฯ", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; ส่งกลับฝ่ายส่งเสริมธุรกิจ SBP", "บังคับเมื่อ actionOptions.requireComment=true"],
                ["03 AVP สำนักบริหาร SBP", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; ส่งกลับ GM ส่งเสริมธุรกิจฯ", "บังคับเมื่อ actionOptions.requireComment=true"],
            ],
        ),
        h(3, "Role Detail Documents"),
        p("รายละเอียดแบบอ่านง่ายแยกตามบทบาทอยู่ในเอกสารลูก 5 ฉบับด้านล่าง เอกสารหลักนี้เก็บเฉพาะ contract กลางและ matrix รวม"),
        table(
            ["Role", "เอกสารรายละเอียด", "เนื้อหาหลัก"],
            [
                [profile["code"], f"{Path(profile['file']).name}.pdf", profile["purpose"]]
                for profile in document_detail_role_profiles()
            ],
        ),
        h(3, "Validation Popup Text"),
        table(
            ["Condition", "Popup message"],
            [
                ["กดส่งดำเนินการโดยไม่เลือกผลการพิจารณา", "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ"],
                ["result ที่ requireComment=true แต่ comment ว่าง", "กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ"],
                ["ผลรวม %ชดเชยร้านเปิดใหม่ไม่เท่ากับ 100", "โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100%"],
            ],
        ),
    ]


def document_detail_single_role_blocks(profile: dict[str, Any]) -> list[dict[str, Any]]:
    section_rows = []
    for key, label in [
        ("doc-header", "ข้อมูลร้านถูกกระทบ"),
        ("sec-sales", "แนวโน้มยอดขายรายวัน"),
        ("sec-map", "แผนที่ AllMap"),
        ("sec-newstore", "ร้านเปิดใหม่"),
        ("sec-competitor", "ร้านคู่แข่งเปิดกระทบ"),
        ("sec-factor", "ปัจจัยอื่นๆ"),
        ("sec-attach", "เอกสารแนบทั้งหมด"),
        ("sec-calc", "คำนวณเงินชดเชย"),
        ("sec-comp-history", "ประวัติการชดเชย"),
        ("sec-decision-history", "ผลการพิจารณา (ประวัติ)"),
        ("sec-action", "พิจารณา / ส่งดำเนินการ"),
    ]:
        if key in profile["hidden"]:
            state = "Hidden"
            control = "ไม่ render section"
        elif key in profile["editable"]:
            state = "Editable"
            control = "เปิด input/action เฉพาะ field ที่ระบุในเอกสารนี้"
        elif key == "sec-attach" and profile["upload"]:
            state = "Read-only + Upload"
            control = "ดูรายการไฟล์และเพิ่มไฟล์แนบได้"
        elif key == "sec-action":
            state = "Action"
            control = "แสดง radio result, textarea comment, ปุ่มส่งดำเนินการ"
        elif key in profile["visible"]:
            state = "Read-only"
            control = "แสดงข้อมูลและปิด input/editor"
        else:
            state = "Hidden"
            control = "ไม่ render section"
        section_rows.append([key, label, state, control])

    response = {
        "docNo": "2569/00123",
        "statusCode": profile["code"],
        "viewerRbacRoleCode": "R-XX",
        "roleProfileCode": role_profile_code(profile),
        "visibleSections": profile["visible"],
        "editableSections": profile["editable"],
        "canUploadAttachment": profile["upload"],
        "canAction": True,
        "actionOptions": [{"label": row[0], "requireComment": "ต้องกรอก" in row[1]} for row in profile["actions"]],
    }
    return [
        h(2, "5.1 Role View Summary"),
        table(
            ["Item", "Value"],
            [
                ["Role profile", f"{role_profile_code(profile)} - {profile['name']}"],
                ["Workflow section/status code", profile["code"]],
                ["Document status shown", profile["status"]],
                ["Purpose on this page", profile["purpose"]],
                ["Editable sections", ", ".join(profile["editable"]) if profile["editable"] else "-"],
                ["Hidden sections", ", ".join(profile["hidden"]) if profile["hidden"] else "-"],
                ["Attachment upload", "Allowed" if profile["upload"] else "Not allowed"],
            ],
        ),
        h(2, "5.2 What This Role Sees"),
        bullets(profile["summary"]),
        h(2, "5.3 Section-by-section Behavior"),
        table(["Section key", "UI section", "State for this role", "Control behavior"], section_rows),
        h(2, "5.4 Editable Form Fields"),
        table(["Area", "Fields", "Validation / Behavior"], profile["fields"]),
        h(2, "5.5 Action Panel"),
        p("FE ต้อง render ตัวเลือกจาก `actionOptions` ที่ API ส่งมาเท่านั้น และส่ง payload `{result,comment}` โดยไม่คำนวณปลายทาง action เอง"),
        table(["Radio option", "Comment rule"], profile["actions"]),
        h(2, "5.6 API Response Example"),
        payload("GET /api/v1/documents/{docNo} response", api_json(response)),
        h(2, "5.7 Validation Popup Text"),
        table(
            ["Condition", "Popup message"],
            [
                ["กดส่งดำเนินการโดยไม่เลือกผลการพิจารณา", "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ"],
                ["result ที่ requireComment=true แต่ comment ว่าง", "กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ"],
                ["ผลรวม %ชดเชยร้านเปิดใหม่ไม่เท่ากับ 100", "โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100%"],
            ],
        ),
        h(2, "5.8 Role-specific Test Checklist"),
        table(["No", "Test"], [[i + 1, item] for i, item in enumerate(profile["tests"])]),
    ]


def document_detail_role_topic(profile: dict[str, Any]) -> Topic:
    forward_action = {
        "06": ("ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "08", "08"),
        "08": ("คำนวณเงินชดเชยเรียบร้อย", "01", "01"),
        "01": ("เห็นควรชดเชย", "02", "02"),
        "02": ("เห็นควรชดเชย", "03", "03"),
        "03": ("เห็นควรชดเชย", None, "99"),
    }[profile["code"]]
    return Topic(
        profile["file"],
        f"LLDD FE - Document Detail Role {profile['code']} {profile['short']}",
        "FE",
        1.2,
        10,
        FE_OWNER_KITTISAK,
        f"อธิบายหน้าจอ Document Detail สำหรับ role {profile['code']} - {profile['name']}",
        [],
        [
            f"Role profile {role_profile_code(profile)} - {profile['name']}",
            "Visible/read-only/hidden section behavior",
            "Editable field and validation behavior",
            "Attachment upload behavior",
            "Action panel options and API response sample",
        ],
        [
            ("roleProfileCode", role_profile_code(profile), "must match API response", "ใช้เลือก view profile เฉพาะบทบาทนี้; แยก namespace จาก workflow section code"),
            ("statusCode", profile["code"], "from API", "workflow status/section code ปัจจุบัน ไม่ใช่ role profile"),
            ("visibleSections", "string[]", "from API", "FE แสดงเฉพาะ section ใน array"),
            ("editableSections", "string[]", "from API", "FE เปิด input/button เฉพาะ section ใน array"),
            ("actionOptions", "array", "from API", "FE render radio จาก array โดยไม่ hardcode"),
        ],
        [
            ("Load detail", "เปิดเอกสาร", "GET /api/v1/documents/{docNo}", "render role profile"),
            ("Save editable section", "ปุ่มบันทึก", "PUT /api/v1/documents/{docNo}", "ใช้เฉพาะ role ที่มี editableSections"),
            ("Upload attachment", "เลือกไฟล์", "POST /api/v1/documents/{docNo}/attachments", "append attachment when allowed"),
            ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/documents/{docNo}/actions", "submit selected result"),
        ],
        [
            ApiSpec("GET", "/api/v1/documents/{docNo}", f"โหลด role profile {role_profile_code(profile)} สำหรับหน้า detail", {"docNo": "2569/00123"}, {"docNo": "2569/00123", "statusCode": profile["code"], "viewerRbacRoleCode": "R-XX", "roleProfileCode": role_profile_code(profile), "visibleSections": profile["visible"], "editableSections": profile["editable"], "actionOptions": [{"label": row[0], "requireComment": "ต้องกรอก" in row[1]} for row in profile["actions"]]}),
            ApiSpec("POST", "/api/v1/documents/{docNo}/actions", f"ตัวอย่าง positive-path จาก section {profile['code']}; Section 02 ใช้กรณียอดรวมมากกว่า 100,000 บาท", {"result": forward_action[0], "comment": "ส่งดำเนินการตามลำดับ"}, {"statusCode": forward_action[2], "nextSection": forward_action[1], "message": "submitted"}),
        ],
        [
            "Load document detail",
            "Apply visibleSections and editableSections",
            "Render fields/actions for this role only",
            "Validate popup text",
            "Submit action or save allowed section",
            "Reload detail/timeline/status",
        ],
        [
            "ไม่แสดง role switcher ใน production",
            "section ที่ hidden ต้องไม่ render",
            "section ที่ read-only ต้องไม่มี editable control",
            "action panel ตรงกับ actionOptions จาก API",
        ],
        profile["tests"],
        flow_diagram=f"LLDD/assets/flows/{sanitize_filename(profile['file'])}.png",
    )


def document_detail_role_topics() -> list[Topic]:
    return [document_detail_role_topic(profile) for profile in document_detail_role_profiles()]


def common_contract_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Error and Popup Catalog"),
        p("ทุก endpoint ต้องใช้ code และ message จาก catalog เดียวกันเมื่อเข้าเงื่อนไขเดียวกัน"),
        table(
            ["code", "HTTP / Scope", "Trigger", "message"],
            [
                ["ACTION_RESULT_REQUIRED", "422", "submit action โดยไม่เลือกผลการพิจารณา", "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ"],
                ["ACTION_COMMENT_REQUIRED", "422", "result ที่ต้องมี comment แต่ comment ว่าง", "กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ"],
                ["COMPENSATE_PERCENT_INVALID", "422", "ผลรวม % ชดเชยร้านเปิดใหม่ไม่เท่ากับ 100", "โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100%"],
                ["COMPETITOR_REQUIRED", "422", "บันทึกร้านคู่แข่งโดยไม่เลือก competitorCode", "กรุณาเลือกร้านคู่แข่งก่อนบันทึก"],
                ["EXTERNAL_FACTOR_REQUIRED", "422", "บันทึกปัจจัยอื่นโดยไม่เลือก factorCode", "กรุณาเลือกปัจจัยอื่นก่อนบันทึก"],
                ["REPORT_DATE_RANGE_INVALID", "422", "impactMonthFrom มากกว่า impactMonthTo", "เดือนเริ่มต้นต้องไม่มากกว่าเดือนสิ้นสุด"],
                ["FILE_TOO_LARGE", "413", "attachment > 5 MB", "ไฟล์แนบมีขนาดเกิน 5 MB"],
                ["FILE_TYPE_UNSUPPORTED", "415", "extension/content type ไม่อยู่ใน allowlist", "ชนิดไฟล์ไม่อนุญาตให้อัปโหลด"],
                ["FILE_SCAN_BLOCKED", "422", "AV scan พบไวรัสหรือ scan failed", "ไฟล์แนบไม่ผ่านการตรวจสอบความปลอดภัย"],
                ["FORBIDDEN", "403", "ไม่มีสิทธิ์เมนู/เอกสาร/task", "กรุณาติดต่อผู้ดูแลระบบ"],
                ["DUPLICATE_DOCUMENT", "409", "business key ซ้ำตอนสร้างเอกสาร", "ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว"],
                ["CONFLICT", "409", "resource/task ถูกเปลี่ยนหรือเงื่อนไขปัจจุบันไม่ตรงกับคำขอ", "ข้อมูลมีการเปลี่ยนแปลง กรุณาโหลดข้อมูลล่าสุดแล้วดำเนินการใหม่"],
                ["STALE_VERSION", "409", "versionNo ที่ส่งมาไม่ตรงกับ compensation_documents.version_no", "ข้อมูลถูกแก้ไขโดยผู้ใช้อื่น กรุณาโหลดข้อมูลล่าสุดแล้วลองอีกครั้ง"],
                ["FS_BRIDGE_UNAVAILABLE", "FE", "hidden iframe ไม่ตอบ FS_FORM_READY ภายในเวลาที่กำหนด", "ไม่สามารถเชื่อมต่อแบบฟอร์ม FS ได้ กรุณาลองอีกครั้ง"],
                ["FS_BRIDGE_ORIGIN_INVALID", "FE", "event.origin ไม่ตรง allowlist", "ไม่สามารถยืนยันแหล่งที่มาของแบบฟอร์ม FS ได้"],
                ["FS_BRIDGE_SCHEMA_INVALID", "FE", "FS_FIELD_SCHEMA ไม่ตรง message schema หรือมี field type ที่ไม่รองรับ", "ข้อมูลแบบฟอร์ม FS ไม่ถูกต้อง กรุณาติดต่อผู้ดูแลระบบ"],
                ["FS_BRIDGE_SUBMIT_FAILED", "FE", "FS_SUBMIT_RESULT ไม่สำเร็จหรือ FS_ERROR ตอน submit", "ส่งแบบฟอร์ม FS ไม่สำเร็จ กรุณาตรวจสอบข้อมูลแล้วลองอีกครั้ง"],
            ],
        ),
        h(2, "5.2 Endpoint Role Matrix"),
        p("Matrix นี้เป็น baseline สำหรับ BE authorization guard; menu-level visibility ยังคงมาจาก menu_permissions"),
        table(
            ["Endpoint group", "Endpoint pattern", "Allowed roles / identity"],
            [
                ["Current user/menu", "/auth/me, /me/menus", "authenticated user"],
                ["Task inbox", "GET /tasks", "authenticated user with assigned task access"],
                ["Document read/list/timeline/sales", "GET /documents*, GET /documents/{docNo}/timeline, GET /documents/{docNo}/sales", "document participant or report/admin role explicitly granted"],
                ["Document create", "POST /documents", "02 HQ, 03 User Admin, 01 Admin"],
                ["Document update/action/attachment upload", "PUT /documents/{docNo}, POST /documents/{docNo}/actions, POST /documents/{docNo}/attachments", "current action owner; admin override only with policy and audit reason"],
                ["Attachment download", "GET /documents/{docNo}/attachments/{attachId}/download", "same as document read; attachment belongs to doc and scanStatus=CLEAN"],
                ["Lookup", "/stores/search, /competitors, /document-statuses", "authenticated user with related menu access"],
                ["Master/RBAC/config", "/operators*, /factors*, /menu-permissions*, /roles*, /menus*, /configs*", "admin/HQ roles according to menu_permissions"],
                ["Reports", "/reports/status-summary*", "admin/HQ/report roles and accounting service user"],
                ["Internal workflow/interface", "/workflows/instances, /interfaces/* callback", "service token or API key only"],
            ],
        ),
    ]


def document_detail_aggregate_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Document Section Keys"),
        p("Aggregate API ต้องคืน key มาตรฐานให้ FE ใช้ render role profile โดยไม่ต้องคำนวณสิทธิ์จากรหัส workflow ใน client"),
        table(
            ["Section key", "UI section", "Render rule"],
            [
                ["doc-header", "ข้อมูลร้านถูกกระทบ / header", "read-only ทุก role"],
                ["sec-sales", "แนวโน้มยอดขายรายวัน", "read-only ทุก role"],
                ["sec-map", "แผนที่ AllMap", "read-only ทุก role"],
                ["sec-newstore", "ร้านเปิดใหม่", "editable เมื่อ BE ส่งใน editableSections"],
                ["sec-competitor", "ร้านคู่แข่งเปิดกระทบ", "editable เมื่อ BE ส่งใน editableSections"],
                ["sec-factor", "ปัจจัยอื่นๆ", "editable เมื่อ BE ส่งใน editableSections"],
                ["sec-attach", "เอกสารแนบทั้งหมด", "upload ได้เมื่อ canUploadAttachment=true"],
                ["sec-calc", "คำนวณเงินชดเชย", "visible เมื่อ BE ส่งใน visibleSections"],
                ["sec-comp-history", "ประวัติการชดเชย", "read-only ทุก role"],
                ["sec-decision-history", "ผลการพิจารณา (ประวัติ)", "read-only ทุก role"],
                ["sec-action", "พิจารณา / ส่งดำเนินการ", "visible เมื่อ canAction=true"],
            ],
        ),
        h(2, "5.2 Role Profile Output"),
        p("BE เป็น source of truth ของ role profile แต่เอกสารนี้ไม่ฝังตาราง route workflow; รายละเอียดการแสดงผลต่อบทบาทอยู่ใน LLDD-FE-Document-Detail"),
        table(
            ["Response field", "Meaning", "FE usage"],
            [
                ["viewerRbacRoleCode", "รหัส role/RBAC ของผู้ใช้ เช่น R-01/R-02/R-10", "แสดง/trace เท่านั้น ไม่ map เป็น section"],
                ["roleProfileCode", "profile สำหรับหน้า Document Detail เช่น P-06/P-08/P-01/P-02/P-03", "เลือกชุด visible/edit/action ที่ BE คำนวณแล้ว; แยก namespace จาก statusCode"],
                ["visibleSections", "section key ที่ต้องแสดง", "ซ่อน section ที่ไม่อยู่ใน array"],
                ["editableSections", "section key ที่แก้ไขได้", "เปิด input/button เฉพาะ section เหล่านี้"],
                ["canUploadAttachment", "boolean", "เปิด/ปิด upload control"],
                ["canAction", "boolean", "เปิด/ปิด action panel"],
                ["actionOptions", "array ของ label + requireComment", "render radio โดยไม่คำนวณปลายทาง"],
            ],
        ),
    ]


def document_create_update_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 docNo Generator and Concurrency Rules"),
        p("เลขเอกสารเป็น business identifier ของระบบ จึงต้อง generate ฝั่ง BE ใน transaction เดียวกับการสร้างเอกสาร และต้องไม่ให้ FE หรือ Job สร้างเลขเอง"),
        table(
            ["Rule", "Required behavior", "Implementation note"],
            [
                ["Format", "YYYY/xxxxx โดย YYYY เป็นปี พ.ศ. และ running 5 หลัก", "ตัวอย่าง 2569/00124; เก็บ doc_no เป็น string และเก็บ be_year/running_no แยกเพื่อ index"],
                ["Sequence scope", "running reset ตามปี พ.ศ.", "unique key `(be_year, running_no)` และ unique `doc_no`"],
                ["Lock strategy", "lock row sequence ด้วย `SELECT ... FOR UPDATE` หรือ database sequence ต่อปี", "ห้ามอ่าน max(running_no)+1 แบบไม่มี lock"],
                ["Transaction boundary", "generate docNo, insert compensation_documents, insert first workflow task และ audit ใน transaction เดียว", "ถ้าสร้าง task ไม่สำเร็จต้อง rollback ทั้งชุด"],
                ["Gap policy", "เลขที่ถูก commit แล้วห้าม reuse; rollback ก่อน commit ไม่ควรเผยแพร่ docNo ให้ client", "ถ้าใช้ native sequence ที่เกิด gap ได้ต้องบันทึก policy นี้ใน runbook"],
                ["Duplicate guard", "business key ซ้ำต้องคืน 409 ก่อน generate docNo ใหม่เมื่อเป็นไปได้", "business key อย่างน้อย impactedStoreCode+impactMonth+newStoreCode+roundNo+source"],
                ["Idempotency", "requestId ใช้ trace/retry แต่ไม่แทน duplicate business key", "ถ้า retry request เดิมหลัง success ให้คืน docNo เดิมเมื่อจับคู่ requestId ได้"],
            ],
        ),
        h(2, "5.2 Create Document Transaction Flow"),
        table(
            ["Step", "Service behavior", "Rollback / error rule"],
            [
                ["1. Validate input", "ตรวจ required, format, store exists, period, source, roundNo", "invalid คืน 400/422 ก่อน lock sequence"],
                ["2. Check duplicate", "query business key บน compensation_documents", "พบเอกสารเดิมคืน 409 DUPLICATE_DOCUMENT พร้อม docNo เดิมถ้าอนุญาตให้แสดง"],
                ["3. Start transaction", "เปิด transaction และ lock sequence row ของปี พ.ศ.", "lock timeout คืน 409/503 ตามมาตรฐาน platform"],
                ["4. Generate docNo", "เพิ่ม running_no และประกอบ doc_no", "ยังไม่ส่ง response จนกว่า commit สำเร็จ"],
                ["5. Insert document", "insert compensation_documents และ child rows เริ่มต้น", "fail ต้อง rollback sequence/document"],
                ["6. Open first task", "insert workflow_instances/workflow_tasks section 06 หรือเรียก workflow service ภายใน transaction boundary ที่กำหนด", "fail ต้อง rollback document"],
                ["7. Audit and commit", "insert audit_logs แล้ว commit", "หลัง commit จึง return docNo/statusCode"],
            ],
        ),
        h(2, "5.3 Required Developer Tests for docNo"),
        table(
            ["Test", "Expected result"],
            [
                ["ยิง POST /documents พร้อมกัน 20 request ในปีเดียวกัน", "ได้ docNo ไม่ซ้ำ running เรียงตาม commit และไม่มี duplicate key error ที่หลุดเป็น 500"],
                ["สร้าง duplicate business key", "คืน 409 DUPLICATE_DOCUMENT และไม่ consume docNo ใหม่ถ้า duplicate ถูกพบก่อน lock sequence"],
                ["จำลอง error หลัง insert document ก่อน insert task", "rollback แล้วไม่เหลือ compensation_documents/workflow_tasks/audit partial"],
                ["เปลี่ยนปี พ.ศ.", "running เริ่มที่ 00001 ของปีใหม่"],
            ],
        ),
        h(2, "5.4 docNo Generator SQL Reference"),
        code("""-- Lock sequence row for the Buddhist year before generating docNo.
SELECT be_year, next_running_no
FROM document_number_sequences
WHERE be_year = :beYear
FOR UPDATE;

-- Create sequence row when the year is first used.
INSERT INTO document_number_sequences (be_year, next_running_no, created_at, updated_at)
SELECT :beYear, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM document_number_sequences WHERE be_year = :beYear
);

-- Consume the next number inside the same transaction as document creation.
UPDATE document_number_sequences
SET next_running_no = next_running_no + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE be_year = :beYear
RETURNING be_year, next_running_no;

INSERT INTO compensation_documents (
    doc_no, be_year, running_no, impacted_store_code, impact_month,
    new_store_code, round_no, source, status_code, created_by, created_at
) VALUES (
    :docNo, :beYear, :runningNo, :impactedStoreCode, :impactMonth,
    :newStoreCode, :roundNo, :source, '06', :userId, CURRENT_TIMESTAMP
);""", "sql"),
    ]


def attachment_storage_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Attachment Storage and Security Design"),
        p("Attachment API ต้องจัดการ binary file จริง ไม่ใช่บันทึก metadata อย่างเดียว โดย BE เป็นเจ้าของ storage adapter, virus scan, authorization และ streaming response"),
        table(
            ["Item", "Required value / convention", "Developer note"],
            [
                ["Storage provider", "`OBJECT_STORAGE` ผ่าน adapter กลาง", "รองรับ S3-compatible/MinIO/NAS ตาม env โดย service code ไม่ผูก vendor โดยตรง"],
                ["Bucket/container", "`sbpgi-{env}-attachments`", "แยก dev/test/prod และกำหนด lifecycle/backup ที่ infra"],
                ["Object key", "`documents/{beYear}/{docNoSafe}/{attachId}/{sha256Prefix}-{safeFileName}`", "`docNoSafe` แทน `/` ด้วย `-`; sanitize filename ก่อนใช้ใน key"],
                ["Quarantine path", "`quarantine/{runDate}/{uuid}`", "ไฟล์ใหม่ต้องเข้า quarantine ก่อน scan; ยัง download ไม่ได้"],
                ["Allowed extension", ATTACHMENT_ALLOWED_EXTENSIONS, "ตรวจทั้ง extension และ content type/magic bytes เท่าที่ platform รองรับ"],
                ["AV scan status", "PENDING -> CLEAN หรือ BLOCKED/FAILED", "download อนุญาตเฉพาะ CLEAN; BLOCKED/FAILED คืน FILE_SCAN_BLOCKED"],
                ["Max size", "5 MB ต่อไฟล์", "เกินให้คืน 413 FILE_TOO_LARGE ก่อน upload เข้า storage"],
            ],
        ),
        h(2, "5.2 Attachment Metadata Fields"),
        table(
            ["Field", "Meaning", "Required behavior"],
            [
                ["attachId", "primary key/identifier", "คืนให้ FE หลัง upload"],
                ["docNo", "เลขเอกสาร", "attachment ต้อง belong กับ document นี้เท่านั้น"],
                ["sectionCode", "workflow section ตอน upload", "บันทึกจาก request และ validate กับ current task/permission"],
                ["originalFileName", "ชื่อไฟล์จากผู้ใช้", "เก็บเพื่อแสดงผลและ Content-Disposition"],
                ["contentType", "MIME type", "ใช้ร่วมกับ extension validation"],
                ["fileSizeBytes", "ขนาดไฟล์", "ต้อง <= 5 MB"],
                ["storageProvider/bucketName/objectKey", "ตำแหน่ง binary", "ห้าม expose objectKey ตรงให้ FE"],
                ["sha256", "checksum", "ใช้ตรวจ duplicate/corruption"],
                ["scanStatus/scannedAt/scanMessage", "ผล AV scan", "download ได้เฉพาะ CLEAN"],
                ["uploadedBy/uploadedAt/deletedFlag", "audit metadata", "soft delete เท่านั้นเมื่อมีการลบภายหลัง"],
            ],
        ),
        h(2, "5.3 Upload Flow"),
        table(
            ["Step", "Backend behavior", "Error / response"],
            [
                ["1. Authorize", "ตรวจผู้ใช้มีสิทธิ์อ่านเอกสารและ canUploadAttachment/current task owner", "ไม่มีสิทธิ์คืน 403"],
                ["2. Validate multipart", "ตรวจ file present, size, extension, content type, sectionCode", "คืน 400/413/415 ตาม catalog"],
                ["3. Hash and quarantine", "stream file คำนวณ sha256 และเขียน quarantine object", "storage fail คืน 503 และไม่ insert metadata CLEAN"],
                ["4. Scan", "เรียก AV scanner แบบ sync หรือ async ตาม platform; ระหว่าง PENDING ห้าม download", "พบไวรัสตั้ง BLOCKED และคืน FILE_SCAN_BLOCKED"],
                ["5. Promote", "เมื่อ CLEAN ให้ move/copy ไป objectKey ถาวรและ insert/update metadata", "metadata ต้องมี objectKey และ scanStatus=CLEAN"],
                ["6. Respond", "คืน attachId, fileName, fileSizeBytes, scanStatus, uploadedAt", "ไม่คืน bucket/objectKey ให้ FE"],
            ],
        ),
        h(2, "5.4 Download Flow and Authorization"),
        table(
            ["Step", "Backend behavior", "Error / response"],
            [
                ["1. Validate path", "ตรวจ docNo/attachId และ attachment belongs to docNo", "ไม่พบคืน 404"],
                ["2. Authorize read", "สิทธิ์เท่ากับ document read หรือ report/admin ที่ได้รับสิทธิ์", "ไม่มีสิทธิ์คืน 403"],
                ["3. Check scan", "อนุญาตเฉพาะ scanStatus=CLEAN และ deletedFlag=false", "PENDING/BLOCKED/FAILED คืน 422 FILE_SCAN_BLOCKED"],
                ["4. Stream", "stream binary ผ่าน BE หรือ signed internal stream ตาม platform", "ตั้ง Content-Type และ Content-Disposition จาก metadata"],
                ["5. Audit", "บันทึก download audit เมื่อ policy กำหนด", "ต้อง trace userId/docNo/attachId/requestId ได้"],
            ],
        ),
        h(2, "5.5 Download Endpoint Contract"),
        table(
            ["Method", "Path", "Response"],
            [
                ["GET", "/api/v1/documents/{docNo}/attachments/{attachId}/download", "binary stream; headers Content-Type, Content-Length, Content-Disposition"],
            ],
        ),
        h(2, "5.6 Attachment Repository SQL Reference"),
        code("""-- Insert metadata after storage write and AV scan pass.
INSERT INTO document_attachments (
    doc_no, section_code, file_name, mime_type, file_size,
    storage_provider, bucket, object_key, sha256,
    scan_status, scanned_at, uploaded_by, uploaded_at, deleted_flag
) VALUES (
    :docNo, :sectionCode, :fileName, :mimeType, :fileSize,
    :storageProvider, :bucket, :objectKey, :sha256,
    'CLEAN', CURRENT_TIMESTAMP, :userId, CURRENT_TIMESTAMP, 'N'
)
RETURNING attach_id;

-- Load attachment for download. Authorization is checked in service before streaming.
SELECT
    attach_id, doc_no, file_name, mime_type, file_size,
    storage_provider, bucket, object_key, sha256, scan_status
FROM document_attachments
WHERE doc_no = :docNo
  AND attach_id = :attachId
  AND deleted_flag = 'N';""", "sql"),
    ]


def read_js_value_from_html(html_file: str, var_name: str, open_char: str, close_char: str) -> Any:
    html = (ROOT / html_file).read_text(encoding="utf-8")
    marker = f"var {var_name} = "
    start = html.index(marker) + len(marker)
    bracket_start = html.index(open_char, start)
    depth = 0
    in_str: str | None = None
    escape = False
    end = bracket_start
    for i, ch in enumerate(html[bracket_start:], bracket_start):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"', "`"):
            in_str = ch
            continue
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    js_text = html[bracket_start:end]
    node = (
        "let s='';"
        "process.stdin.setEncoding('utf8');"
        "process.stdin.on('data', c => s += c);"
        "process.stdin.on('end', () => {"
        "  const value = (new Function('return ' + s))();"
        "  console.log(JSON.stringify(value));"
        "});"
    )
    proc = subprocess.run(["node", "-e", node], input=js_text, text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def read_js_array_from_html(html_file: str, var_name: str) -> list[dict[str, Any]]:
    return read_js_value_from_html(html_file, var_name, "[", "]")


def read_js_object_from_html(html_file: str, var_name: str) -> dict[str, Any]:
    return read_js_value_from_html(html_file, var_name, "{", "}")


def load_batch_jobs() -> list[dict[str, Any]]:
    jobs = read_js_array_from_html("job-batch.html", "JOBS")
    by_no = {str(j["no"]): j for j in jobs}
    selected: list[dict[str, Any]] = []
    for no in ["1", "2", "3", "4", "5", "6", "7", "8", "8b", "9", "10"]:
        if no not in by_no:
            continue
        selected.append(target_job(dict(by_no[no])))
    return selected


def draw_flow_diagram(title: str, steps: list[str], out_rel: str) -> str:
    out_path = ROOT / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font_path = FONT if os.path.exists(FONT) else "/System/Library/Fonts/Supplemental/Arial.ttf"
    title_font = ImageFont.truetype(font_path, 24)
    body_font = ImageFont.truetype(font_path, 17)
    small_font = ImageFont.truetype(font_path, 13)
    multi_col = len(steps) > 9
    width = 1600 if multi_col else 1400
    box_w = 680 if multi_col else 1020
    box_h = 74
    gap = 38
    top = 92
    rows = math.ceil(len(steps) / 2) if multi_col else len(steps)
    height = top + rows * (box_h + gap) + 48
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((70, 34), title, fill="#0B2545", font=title_font)
    col_gap = 80
    x_positions = [(width - (box_w * 2 + col_gap)) // 2, (width - (box_w * 2 + col_gap)) // 2 + box_w + col_gap] if multi_col else [(width - box_w) // 2]

    def wrap_text(text: str, max_px: int) -> list[str]:
        words = re.split(r"(\s+)", text)
        lines: list[str] = []
        current = ""
        for token in words:
            candidate = current + token
            if d.textlength(candidate, font=body_font) <= max_px:
                current = candidate
            else:
                if current.strip():
                    lines.append(current.strip())
                current = token.strip()
        if current.strip():
            lines.append(current.strip())
        return lines[:3]

    for idx, step in enumerate(steps):
        col = 1 if multi_col and idx >= rows else 0
        row_idx = idx - rows if col else idx
        x = x_positions[col]
        y = top + row_idx * (box_h + gap)
        fill = "#EEF4FF"
        outline = "#96B4F0"
        if "?" in step or "ผ่าน" in step or "สำเร็จ" in step:
            fill = "#FFFAF0"
            outline = "#E2B45A"
        if any(word in step for word in ["ล้มเหลว", "Rollback", "error", "FAIL", "ค้าง", "ไม่ผ่าน"]):
            fill = "#FDECEC"
            outline = "#D98A8A"
        d.rounded_rectangle([x, y, x + box_w, y + box_h], radius=16, fill=fill, outline=outline, width=3)
        d.ellipse([x + 20, y + 20, x + 54, y + 54], fill="#2F6FED")
        d.text((x + 37, y + 37), str(idx + 1), fill="white", font=small_font, anchor="mm")
        lines = wrap_text(step, box_w - 116)
        line_top = y + 18 if len(lines) <= 2 else y + 10
        for line_idx, line in enumerate(lines):
            d.text((x + 76, line_top + line_idx * 21), line, fill="#2B3440", font=body_font)
        is_last_in_col = multi_col and idx == rows - 1
        if idx < len(steps) - 1 and not is_last_in_col:
            ax = x + box_w // 2
            ay1 = y + box_h + 5
            ay2 = y + box_h + gap - 8
            d.line([ax, ay1, ax, ay2], fill="#8493A5", width=3)
            d.polygon([(ax - 8, ay2 - 2), (ax + 8, ay2 - 2), (ax, ay2 + 12)], fill="#8493A5")
        elif is_last_in_col and idx < len(steps) - 1:
            ax1 = x + box_w + 10
            ay = y + box_h // 2
            ax2 = x_positions[1] - 14
            d.line([ax1, ay, ax2, ay], fill="#8493A5", width=3)
            d.polygon([(ax2 - 2, ay - 8), (ax2 - 2, ay + 8), (ax2 + 12, ay)], fill="#8493A5")
    img.save(out_path)
    return out_rel


def flow_steps_from_job(job: dict[str, Any]) -> list[str]:
    steps = []
    for item in job.get("flow", []):
        text = item.get("t", "")
        if item.get("no"):
            text += f" | No: {item['no']}"
        if item.get("d"):
            text += f" ({item['d']})"
        steps.append(text)
    return steps


def job_topic(job: dict[str, Any]) -> Topic:
    no = str(job["no"])
    owner = BANK_BE_OWNER
    estimated_hours = JOB_ESTIMATES[no]
    params = job.get("params", [])
    fields = [(p[0], p[1], "แก้ไขได้" if p[3] else "ค่าคงที่/แก้ผ่านหน้าจอไม่ได้", p[4] if len(p) > 4 else "") for p in params]
    db_tables = [tuple(row) for row in job.get("tables", [])]
    flow = flow_steps_from_job(job)
    flow_file = f"LLDD/assets/flows/BE-Job-{no}-{sanitize_filename(job['name'])}.png"
    scope = [
        f"Main class/script: {job.get('cls', '-')} / {job.get('script', '-')}",
        f"Phase: {job.get('phase', '-')}",
        f"Output: {job.get('out', '-')}",
        f"Estimate: {estimated_hours} ชั่วโมง",
        "Runbook, rerun rule, risk และ history ต้องตามข้อมูลหน้า Batch Job",
    ]
    if no == "8b":
        scope.append("Depends on LLDD-BE-API-Workflow-Instances; Job 8b เรียก Workflow Engine ภายในและไม่ duplicate Gen Flow Gate logic")
    return Topic(
        f"BE/Jobs/LLDD-BE-Job-{no}-{sanitize_filename(job['name'])}",
        f"LLDD BE - Job {no} {job['name']}",
        "BE",
        round(estimated_hours / HOURS_PER_DAY, 1),
        estimated_hours,
        owner,
        f"{job.get('th', job['name'])}: {job.get('desc', '')}",
        [],
        scope,
        fields or [("jobNo", no, "required", "รหัสงาน Batch")],
        [
            ("เปิดดูรายละเอียด Job", "GET", f"GET /api/v1/jobs/{no}", "คืน params/metadata ล่าสุด"),
            ("บันทึกพารามิเตอร์", "PUT", f"PUT /api/v1/jobs/{no}/params", "บันทึกเฉพาะ key ที่ editable และ audit"),
            ("สั่งรันทันที", "POST", f"POST /api/v1/jobs/{no}/run", "สร้าง run history สถานะ RUNNING/QUEUED"),
            ("เปิด/ปิดใช้งาน", "PUT", f"PUT /api/v1/jobs/{no}/enabled", "บันทึก enabled + audit พร้อม reason"),
        ],
        [
            ApiSpec("GET", f"/api/v1/jobs/{no}", "อ่าน metadata และพารามิเตอร์ของ Job", {"jobNo": no}, {"jobNo": no, "name": job["name"], "cron": job.get("cron"), "enabled": True, "params": [{"label": p[0], "value": p[1], "editable": bool(p[3])} for p in params[:4]]}),
            ApiSpec("PUT", f"/api/v1/jobs/{no}/params", "แก้ไขพารามิเตอร์ที่อนุญาตเท่านั้น", {"params": {"cron": job.get("cron")}, "reason": "ปรับรอบรันตาม Operations"}, {"message": "saved"}),
            ApiSpec("POST", f"/api/v1/jobs/{no}/run", "สั่งรัน manual โดย guard ไม่ให้รันซ้อน", {"period": "2569-07"}, {"runId": f"JOB{no}-RUN-001", "status": "RUNNING"}),
            ApiSpec("GET", f"/api/v1/jobs/{no}/runs", "อ่านประวัติการรันล่าสุด", {"page": 1, "size": 20}, {"items": [{"startedAt": job.get("run", ["-"])[0], "status": job.get("run", ["", "UNKNOWN"])[1]}]}),
        ],
        flow,
        [
            "อ่าน/แก้พารามิเตอร์ได้ตาม editable flag เท่านั้น",
            "การสั่งรันต้องตรวจ enabled และไม่มีรอบ RUNNING เดิม",
            "ต้องบันทึก job_run_histories และ audit_logs สำหรับทุก mutation",
            "DB/table mapping ใช้เป็น reference สำหรับ implement Job เท่านั้น ไม่ใช่งานสร้างหน้า Database",
            "รองรับ rerun rule และ risk note ตาม runbook",
        ],
        [
            "GET job detail",
            "PUT params with editable key",
            "PUT params locked business key must fail",
            "POST run while running must fail",
            "GET run histories",
            "ตรวจผลกระทบตารางตาม R/W mapping reference",
        ],
        db_tables=db_tables,
        flow_diagram=flow_file,
    )


def be_job_topics() -> list[Topic]:
    return [job_topic(job) for job in load_batch_jobs()]


def topics() -> list[Topic]:
    base = [
        Topic(
            "FE/LLDD-FE-Integration-Contracts",
            "LLDD FE - Integration Contracts",
            "FE",
            2.8,
            24,
            FE_OWNER,
            "กำหนดสัญญากลางฝั่ง Frontend สำหรับการ consume API ทุกหน้า: auth/session, error handling, pagination, format, document action และ RBAC/menu gating",
            [],
            [
                "Shared API client contract",
                "Auth/JWT consumption from platform reference",
                "Error display and validation message mapping",
                "Date/year/money/docNo formatting",
                "Pagination, list empty/loading/error state",
                "Document action result enum and response consumption",
                "RBAC/menu gating and editable section flags",
            ],
            [
                ("Authorization", "Bearer JWT", "required except /auth/login and /auth/refresh", "แนบโดย axios interceptor เท่านั้น; component ห้าม set header เอง"),
                ("ApiError", "{code,message}", "message required", "แสดง message จาก BE ตรง ๆ; fallback ใช้เฉพาะ network/no response"),
                ("PageResponse<T>", "{page,size,total,items}", "page>=1 size<=100", "ใช้กับ DataTable/Pager ทุกหน้า"),
                ("date/month", "ISO ค.ศ. YYYY-MM-DD / YYYY-MM", "payload uses CE", "แสดง พ.ศ. ผ่าน formatDateThai/formatMonthThai จุดเดียว"),
                ("docNo", "YYYY/xxxxx พ.ศ.", "do not split except route params", "route ใช้ /documents/:year/:running แล้วประกอบ docNo"),
                ("result", "verbatim from actionOptions", "required before submit action", "ส่งเป็น payload `{result, comment}` เท่านั้น"),
                ("ActionResponse", "{statusCode,nextSection,message}", "required after action", "invalidate detail/timeline/tasks แล้ว resolve label จาก /document-statuses"),
                ("MenuItem", "{menuCode,label,route,group}", "from /me/menus", "sidebar filter ด้วย menuCode จาก API; ไม่ hardcode role"),
                ("canEditSections", "string[]", "from document detail", "ใช้เปิด/ปิด section editor; FE ไม่คำนวณสิทธิ์เอง"),
            ],
            [
                ("Attach token", "ทุก API call", "shared/api/client.ts", "Authorization header จาก auth store"),
                ("Refresh token", "401 non-auth endpoint", "POST /api/v1/auth/refresh", "single-flight แล้ว replay request เดิม"),
                ("Show API error", "catch AxiosError", "apiErrorMessage()", "แสดงข้อความไทยจาก BE ตรง ๆ"),
                ("Render list", "GET list endpoint", "PageResponse<T>", "DataTable/Pager ใช้ shape เดียวกัน"),
                ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/documents/{docNo}/actions", "ส่ง `{result, comment}` และ consume `{statusCode,nextSection,message}`"),
                ("Gate route/menu", "login/bootstrap", "GET /api/v1/me/menus", "สร้าง sidebar และ route guard จาก menuCode"),
            ],
            [
                ApiSpec("ALL", "/api/v1/*", "Error contract กลางสำหรับ FE ทุกหน้า", None, {"code": "VALIDATION", "message": "ข้อความภาษาไทยตรงตาม SRS"}),
                ApiSpec("GET", "/api/v1/*?page=1&size=20", "List/pagination contract กลาง", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("POST", "/api/v1/documents/{docNo}/actions", "Document action contract ตัวอย่างเมื่อ currentSection=01 จึงเปลี่ยนไป 02; FE ห้ามส่งหรือคำนวณปลายทางเอง", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("GET", "/api/v1/me/menus", "Menu/RBAC contract สำหรับ sidebar และ route guard", {}, {"menus": [{"menuCode": "k2-report", "label": "รายงานสรุปสถานะ", "route": "/reports/income-audit", "group": "ระบบประกันรายได้"}]}),
            ],
            [
                "Bootstrap env and API client",
                "Login or restore session with refresh token",
                "Load /auth/me and /me/menus",
                "Render routes/sidebar from menu contract",
                "All feature hooks use shared API client and PageResponse/Error types",
                "Document action sends `{result, comment}` only and consumes `{statusCode,nextSection,message}`",
                "All display formatting goes through shared/lib/format.ts",
            ],
            [
                "ไม่มี feature ใดสร้าง axios instance เอง",
                "ทุก API error แสดง message จาก BE โดยไม่ paraphrase",
                "ทุก list endpoint ใช้ PageResponse shape เดียวกัน",
                "วันที่ใน payload เป็น ค.ศ.; หน้าจอแสดง พ.ศ. จาก formatter กลาง",
                "Sidebar และ route access มาจาก /me/menus ไม่ hardcode role",
                "FE ไม่คำนวณ action routing เอง; ใช้ role profile และ actionOptions จาก API",
            ],
            ["401 refresh single-flight", "403 route guard", "error message passthrough", "pagination pager mapping", "date BE display", "action response invalidation", "menu filtering by API"],
        ),
        Topic(
            "FE/LLDD-FE-Foundation",
            "LLDD FE - Application Foundation and Shared UI",
            "FE",
            7.1,
            60,
            FE_OWNER,
            "เตรียม foundation ฝั่ง Frontend สำหรับ SBP Mall: routing, API client, constants, shared state, formatters, mock mapping และ shared UI primitives; เอกสารนี้ไม่ใช่หน้าจอ Dashboard",
            [],
            ["Non-screen technical foundation", "Route/module registry เฉพาะ SBP Mall", "API client และ response typing", "Shared constants/menu/status mapping", "Mock data mapping", "CSS/tokens สำหรับ table/form/modal/responsive"],
            [
                ("routePath", "string", "required", "ต้อง map กับเมนู SBP Mall"),
                ("apiBaseUrl", "URL", "required by env", "ใช้กับทุก API call"),
                ("statusCode", "string", "must map to status dictionary", "ใช้ร่วมกับ StatusBadge"),
                ("mockData", "JSON", "schema compatible with API response", "ใช้ก่อน BE พร้อม"),
            ],
            [
                ("Register module route", "bootstrap", "client router", "route guard รู้จักหน้า SBP Mall"),
                ("Call API", "React Query hook", "shared API client", "standard loading/error handling"),
            ],
            [
                ApiSpec("GET", "/api/v1/document-statuses", "โหลดสถานะเอกสารสำหรับ dropdown/badge", {}, {"items": [{"code": "06", "label": "รอฝ่าย SBP DSA ดำเนินการ"}]}),
                ApiSpec("GET", "/api/v1/me/menus", "โหลดเมนูสำหรับสร้าง sidebar/route guard", {}, {"menus": [{"menuCode": "k2-overview", "route": "/"}]}),
            ],
            ["Initialize app config", "Register SBP Mall routes", "Create shared API client", "Prepare constants/formatters", "Wire shared UI primitives"],
            ["ไม่มี screenshot หรือ dashboard behavior ในเอกสารนี้", "ทุก route ถูก register ผ่าน module registry", "API error shape ใช้ร่วมกัน", "ไม่มี dependency กับ Login/Auth ใหม่", "CSS responsive base พร้อม"],
            ["route registration", "API base missing", "status unknown", "mock response compatible", "shared formatter output"],
        ),
        Topic(
            "FE/LLDD-FE-Overview",
            "LLDD FE - Overview Dashboard",
            "FE",
            6.5,
            55,
            FE_OWNER,
            "สร้างหน้า Dashboard เพื่อสรุปงานรอดำเนินการ สาขาประกันรายได้ ยอดชดเชย และกราฟสถานะ",
            ["index-01.png", "index-02.png"],
            ["KPI cards 4 กล่อง", "Task summary และ pending queue", "Monthly compensation chart", "Pending status chart", "Loading/empty/error state"],
            [
                ("year", "พ.ศ. YYYY", "optional default current year", "ใช้กับ query dashboard"),
                ("totalPending", "integer", ">= 0", "แสดงจำนวนงานค้าง"),
                ("compensationAmount", "number", ">= 0", "แสดงล้านบาท 2 decimal"),
                ("statusChart", "array", "ต้องมี label/value/color", "render SVG chart"),
            ],
            [
                ("Refresh dashboard", "เปิดหน้า/กด refresh", "GET /api/v1/dashboard/summary", "update KPI + charts"),
                ("Click pending card", "card งานรอดำเนินการ", "navigate /documents/waiting", "เปิดรายการเอกสารรอ"),
            ],
            [
                ApiSpec("GET", "/api/v1/dashboard/summary", "ดึงข้อมูล Dashboard", {"year": 2569}, {"waitingTasks": 24, "storesThisMonth": 342, "compensationThisMonth": 8420000.0, "abnormalStores": 5, "monthlyChart": [{"month": "ม.ค.", "amount": 7200000.0}], "statusChart": [{"statusCode": "06", "label": "รอฝ่าย SBP DSA ดำเนินการ", "count": 8}]}),
            ],
            ["Initial route `/`", "Call dashboard API", "Map KPI values", "Render charts", "Show error state if API fails"],
            ["KPI ตรงกับ API response", "กราฟไม่ blank", "ข้อความไม่ล้นใน mobile", "กด card แล้วไปหน้ารายการถูกต้อง"],
            ["โหลดหน้าสำเร็จ", "API error แสดง retry", "ค่าศูนย์แสดง empty state", "responsive desktop/mobile"],
        ),
        Topic(
            "FE/LLDD-FE-Document-Lists",
            "LLDD FE - Document Lists",
            "FE",
            8.2,
            70,
            FE_OWNER_PEERAKORN,
            "สร้างหน้ารายการเอกสารรอดำเนินการและเอกสารที่เกี่ยวข้อง",
            ["k2-list-waiting-01.png", "k2-list-waiting-02.png", "k2-list-related-01.png"],
            ["Waiting list", "Related document list", "Search/filter/status filter", "Pagination/row action", "Red flag for sales data < 60 days"],
            [
                ("docNo", "YYYY/xxxxx", "optional search", "ถ้าคลิก row ส่งไป detail"),
                ("year", "พ.ศ. YYYY", "required สำหรับ /documents", "default current year"),
                ("status", "status code/string", "optional single select", "ใช้ filter chip"),
                ("table.docNo", "YYYY/xxxxx", "column 1", "เลขที่เอกสารและลิงก์เปิด detail"),
                ("table.impactedStoreCode", "string 5 digits", "column 2", "รหัสร้านถูกกระทบ; คง leading zero"),
                ("table.impactedStoreName", "string", "column 3", "ชื่อร้านถูกกระทบ"),
                ("table.impactMonth", "YYYY-MM", "column 4", "FE แสดงเดือน/ปี พ.ศ."),
                ("table.statusCode/statusName", "code + label", "column 5", "เก็บ code และ resolve label จาก dictionary"),
                ("table.operatorName", "string|null", "column 6", "ผู้ถือ task ปัจจุบันหรือ '-'"),
                ("table.daysPending", "integer", "column 7; >=0", "จำนวนวันรอดำเนินการ"),
                ("table.totalCompensationAmount", "decimal", "column 8; >=0", "format #,##0.00"),
                ("table.salesDataDays", "integer", "column 9; <60 = abnormal", "row สีแดงและ label ผิดปกติ"),
            ],
            [
                ("Search", "ปุ่มค้นหา", "GET /api/v1/tasks หรือ /documents", "reload table"),
                ("Clear", "ปุ่มเคลียร์", "client state", "reset filters"),
                ("Open detail", "click row", "navigate /documents/:docNo", "เปิดเอกสาร"),
            ],
            [
                ApiSpec("GET", "/api/v1/tasks", "รายการเอกสารรอดำเนินการ", {"page": 1, "size": 20, "status": "06"}, {"page": 1, "size": 20, "total": 24, "items": [{"docNo": "2569/00123", "impactedStoreCode": "01234", "impactedStoreName": "สาขาตัวอย่าง", "impactMonth": "2026-06", "statusCode": "06", "statusName": "รอฝ่าย SBP DSA ดำเนินการ", "operatorName": "สมชาย ใจดี", "daysPending": 3, "totalCompensationAmount": 48200.0, "salesDataDays": 58}]}),
                ApiSpec("GET", "/api/v1/documents", "ค้นหาเอกสารที่เกี่ยวข้อง ต้องระบุปี", {"year": 2569, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 342, "items": [{"docNo": "2569/00124", "impactedStoreCode": "01235", "impactedStoreName": "สาขาตัวอย่าง 2", "impactMonth": "2026-06", "statusCode": "99", "statusName": "เสร็จสิ้น", "operatorName": None, "daysPending": 0, "totalCompensationAmount": 72500.0, "salesDataDays": 60}]}),
            ],
            ["Read route mode", "Bind filter values", "Call list API", "Render table", "Apply abnormal row style", "Navigate to detail on row click"],
            ["ตาราง 9 คอลัมน์หลักครบ", "ปีเป็น required เมื่อใช้ /documents", "ยอดขายไม่ครบ 60 วันแสดงแดง", "pagination คง filter เดิม"],
            ["ค้นหาด้วย docNo", "filter status", "เปิด detail", "empty result", "abnormal row"],
        ),
        Topic(
            "FE/LLDD-FE-Create-Document",
            "LLDD FE - Create Document",
            "FE",
            4.9,
            42,
            FE_OWNER_KITTISAK,
            "สร้างหน้าสร้างเอกสารประกันรายได้แบบ Manual และแบบเอกสารจาก FS โดยใช้ SBP mirror form sync เข้า hidden FS iframe",
            ["k2-create-01.png"],
            ["Create form shell", "Tab: สร้างเอกสารทั่วไป", "Tab: เอกสารจาก FS ผ่าน hidden iframe", "Store selector", "Period/source fields", "FS field discovery/mirror form", "Validation", "Draft/save/submit UI"],
            [
                ("source", "MANUAL|FS", "required", "แสดง section ตาม source; payload ใช้ชื่อ field `source`"),
                ("activeTab", "MANUAL|FS_IFRAME", "required UI state", "เลือก tab สร้างเอกสารทั่วไปหรือเอกสารจาก FS"),
                ("fsIframeUrl", "URL", "required for FS tab", "อ่านจาก config; ใช้โหลด hidden iframe ของ FS"),
                ("fsFieldMap", "array", "required after iframe load", "metadata ของ input/select/textarea ที่อ่านจาก iframe เพื่อ render SBP mirror form"),
                ("fsMirrorValues", "object", "required for FS tab", "state ของ form ฝั่ง SBP ที่ sync เข้า hidden iframe เมื่อ change/submit"),
                ("impactedStoreCode", "string 5 digits", "required", "ค้นหาด้วย popup ร้านถูกกระทบ; คง leading zero"),
                ("impactedStoreName", "string", "readonly after select", "เติมอัตโนมัติหลังเลือกร้าน"),
                ("newStoreCode", "string 5 digits", "required", "เลือกร้านเปิดใหม่จาก popup; ส่งรหัสร้านและคง leading zero"),
                ("impactMonth", "YYYY-MM", "required", "month picker; FE แสดง พ.ศ. แต่ส่ง ค.ศ."),
                ("statementPeriod", "YYYY-MM", "required for FS", "Period Statement จาก SRS SCR-02"),
                ("roundNo", "integer >= 1", "required/default 1", "ครั้งที่ของเอกสาร/งวดชดเชย"),
                ("reason", "text", "required for MANUAL/out-of-condition", "เหตุผลการสร้างเอกสารนอกเงื่อนไข; trim ก่อนส่ง"),
            ],
            [
                ("Search store", "แว่นขยาย", "GET /api/v1/stores/search", "เลือก impacted/new store"),
                ("Open FS tab", "tab เอกสารจาก FS", "Load hidden iframe from fsIframeUrl", "discover FS fields and render SBP mirror form"),
                ("Change FS mirror value", "input/select ใน SBP mirror form", "iframe value sync service", "ส่งค่าเข้า field ใน hidden iframe และ dispatch input/change"),
                ("Save draft", "ปุ่มบันทึก", "POST /api/v1/documents", "สร้าง draft"),
                ("Submit", "ปุ่มส่งดำเนินการ", "POST /api/v1/documents", "สร้างเอกสารและเริ่ม workflow"),
                ("Submit FS iframe", "ปุ่มส่งใน tab เอกสารจาก FS", "sync all mirror values + submit iframe form", "submit form ของ FS ใน hidden iframe"),
            ],
            [
                ApiSpec("GET", "/api/v1/stores/search", "ค้นหาร้านสำหรับ popup", {"q": "012", "type": "impacted"}, {"items": [{"storeCode": "01234", "storeName": "สาขาตัวอย่าง", "regionCode": "RS"}]}),
                ApiSpec("GET", "/api/v1/configs/fs.createDocumentUrl", "อ่าน URL สำหรับโหลด FS iframe ใน tab เอกสารจาก FS", {}, {"configKey": "fs.createDocumentUrl", "value": "https://fs.example/create-document"}),
                ApiSpec("POST", "/api/v1/documents", "สร้างเอกสาร", {"source": "MANUAL", "impactMonth": "2026-07", "statementPeriod": "2026-07", "impactedStoreCode": "01234", "newStoreCode": "22864", "roundNo": 1, "reason": "สร้างเอกสารนอกเงื่อนไข"}, {"docNo": "2569/00001", "statusCode": "06", "message": "created"}),
            ],
            ["User opens create page", "Choose tab: สร้างเอกสารทั่วไป or เอกสารจาก FS", "For FS tab load hidden iframe and discover fields", "Render SBP mirror form from iframe field metadata", "Search/select store or input period/source", "On change sync value into hidden iframe", "Validate", "Submit SBP API or submit hidden FS iframe", "Navigate to detail or show FS submit result"],
            ["required fields ทำงาน", "docNo ได้จาก API for MANUAL", "FS tab loads iframe and renders mirror form", "changing SBP mirror field updates hidden iframe field", "FS submit syncs all values before iframe submit", "validation message ชัดเจน"],
            ["ไม่เลือก store", "period format ผิด", "submit success", "API duplicate error", "FS iframe load timeout", "FS field mapping missing", "FS submit callback success/error"],
        ),
        Topic(
            "FE/LLDD-FE-Document-Detail",
            "LLDD FE - Document Detail and Action",
            "FE",
            11.5,
            98,
            FE_OWNER_KITTISAK,
            "สร้างหน้าเอกสารรายละเอียดและ Action Panel โดยแสดงผลตาม role profile ของผู้ใช้ที่ login",
            ["k2-document-01.png", "k2-document-02.png", "k2-document-03.png"],
            ["Document header", "Store impact/new-store/factor sections", "Role-based visible/editable sections", "Action panel by role profile", "History/timeline", "Attachment upload/download", "Map/ALLMAP link"],
            common_doc_fields() + [
                ("result", "verbatim from actionOptions", "required on submit action", "FE แสดง radio ตาม `actionOptions` จาก API เท่านั้น"),
                ("comment", "text", "required บาง result", "trim before submit"),
                ("compensatePercent", "number", "sum = 100", "validate before save"),
            ],
            [
                ("Save section", "ปุ่มบันทึก", "PUT /api/v1/documents/{docNo}", "save partial"),
                ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/documents/{docNo}/actions", "submit selected result and reload status"),
                ("Upload file", "เลือกไฟล์", "POST /api/v1/documents/{docNo}/attachments", "append attachment"),
                ("Open sales", "ข้อมูลยอดขายเพิ่มเติม", "GET /api/v1/documents/{docNo}/sales", "show chart/detail"),
            ],
            [
                ApiSpec("GET", "/api/v1/documents/{docNo}", "โหลดรายละเอียดเอกสารพร้อม role profile สำหรับหน้า detail", {"docNo": "2569/00123"}, {"docNo": "2569/00123", "statusCode": "06", "viewerRbacRoleCode": "R-XX", "roleProfileCode": "P-06", "visibleSections": ["doc-header", "sec-sales", "sec-map", "sec-newstore", "sec-competitor", "sec-factor", "sec-attach", "sec-comp-history", "sec-decision-history", "sec-action"], "editableSections": [], "canUploadAttachment": True, "canAction": True, "actionOptions": [{"label": "เห็นควรไม่ชดเชย", "requireComment": True}, {"label": "หยุดชดเชยประกันรายได้", "requireComment": False}, {"label": "ส่งฝ่ายส่งเสริมธุรกิจ SBP", "requireComment": False}, {"label": "ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "requireComment": False}], "impactedStore": {"storeCode": "01234"}, "newStores": []}),
                ApiSpec("PUT", "/api/v1/documents/{docNo}", "บันทึกส่วนย่อย เช่น ร้านเปิดใหม่/คู่แข่ง/ปัจจัย", {"newStores": [{"newStoreCode": "22864", "compensatePercent": 100}]}, {"message": "saved"}),
                ApiSpec("POST", "/api/v1/documents/{docNo}/actions", "ส่งผลพิจารณาที่เลือกจาก actionOptions; ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("POST", "/api/v1/documents/{docNo}/attachments", "แนบไฟล์", {"file": "multipart/form-data <= 5MB"}, {"attachmentId": "att-001", "fileName": "evidence.pdf"}),
            ],
            ["Load document detail", "Render role profile from API", "User edits allowed sections only", "Validate fields and popup text", "Confirm action", "Submit selected result", "Reload detail/timeline/status"],
            ["ส่วน read-only แก้ไม่ได้", "% ชดเชยรวม 100", "action required result", "upload limit 5MB", "timeline reload หลัง submit"],
            ["เปิดเอกสาร", "save section", "submit without result", "submit approve", "upload too large", "timeline display"],
        ),
        Topic(
            "FE/LLDD-FE-Testing-Delivery",
            "LLDD FE - Testing and Delivery",
            "FE",
            3.5,
            30,
            FE_OWNER_PEERAKORN,
            "กำหนด regression, responsive pass, API payload adjustment และ delivery note สำหรับ FE",
            [],
            ["Manual regression", "Responsive pass", "API contract verification", "UAT defect retest", "Release gate", "Delivery evidence"],
            [
                ("viewport", "desktop/tablet/mobile", "must verify key pages", "ใช้ browser responsive mode"),
                ("apiContractVersion", "string", "must match BE", "บันทึกใน delivery note"),
                ("defectId", "string", "required for UAT fix", "trace กลับ defect log"),
            ],
            [
                ("Run route regression", "เริ่ม regression suite", "test matrix state", "บันทึก pass/fail/evidence ต่อ route และ role profile"),
                ("Change viewport", "เลือก desktop/tablet/mobile", "browser responsive state", "ตรวจ overflow, modal, table, chart และ navigation"),
                ("Verify API contract", "replay fixture/request", "schema comparison", "แสดง field/type/error mismatch แบบ trace กลับ endpoint"),
                ("Retest defect", "เลือก defectId ที่แก้แล้ว", "retest status transition", "แนบ before/after evidence และผล regression ที่เกี่ยวข้อง"),
                ("Evaluate release gate", "กดสรุป readiness", "build/typecheck/defect/secret/contract checks", "ได้ PASS หรือ BLOCKED พร้อมเหตุผลราย gate"),
                ("Prepare delivery evidence", "ปิดรอบทดสอบ", "delivery bundle state", "สร้าง test summary/known limitations/verification commands โดยไม่มี secret"),
            ],
            [],
            ["Run page-by-page regression", "Verify responsive", "Compare API payload", "Fix UAT defects", "Run build check", "Prepare delivery note"],
            ["ทุกหน้าหลักไม่มี layout broken", "API payload ตรง contract", "UAT defects critical/high ปิดแล้ว", "delivery note พร้อม"],
            ["desktop regression ครบทุก route หลัก", "tablet/mobile regression", "request/response schema mismatch ต้องเป็นศูนย์", "Critical/High defects ต้องปิด", "report preview/export parity", "action transition 06→08→01→02→03→99", "delivery evidence ไม่มี token/secret"],
        ),
        Topic(
            "FE/LLDD-FE-Report",
            "LLDD FE - Status Summary Report",
            "FE",
            5.9,
            50,
            FE_OWNER_PEERAKORN,
            "สร้างรายงานตรวจสอบประกันรายได้พร้อม Preview และ Export CSV",
            ["k2-report-01.png", "k2-report-02.png"],
            ["Report filters", "Summary table", "Preview/detail modal", "Export action", "Sample data verification"],
            [
                ("impactedStoreCode", "string 5 digits", "optional; numeric only when input", "คง leading zero; ปุ่มแว่นขยายเรียก popup เลือกร้านที่ถูกกระทบ"),
                ("impactedStoreName", "string", "readonly", "แสดงอัตโนมัติหลังเลือกรหัสร้าน; ไม่ส่งเป็น filter หลักถ้ามี storeCode"),
                ("newStoreCode", "string 5 digits", "optional; numeric only when input", "รหัสร้านเปิดกระทบ/ร้านเปิดใหม่; คง leading zero"),
                ("impactMonthFrom", "YYYY-MM", "optional; month picker", "ส่งเป็น ค.ศ. เช่น 2026-05; FE แสดงเดือน/ปี พ.ศ. ในตาราง"),
                ("impactMonthTo", "YYYY-MM", "optional; month picker; must be >= from", "ถ้า from > to ให้แสดง validation ก่อน call API"),
                ("storeTypes", "array enum A|B|C|D", "optional multi select", "checkbox เลือกได้มากกว่า 1; ส่งเป็น comma/query array"),
                ("status", "statusCode string", "required single select", "บังคับเลือก 1 สถานะก่อน Preview/Export; options ตรงกับ document_statuses"),
                ("resultCategory", "APPROVE|REJECT", "required radio", "APPROVE=ประกันรายได้, REJECT=ไม่ประกันรายได้"),
                ("regions", "array enum", "optional multi select", "รองรับ BE, BS, NEU, REU, RSU, BG, BW, RC, RN, BN, NEL, REL, RSL และภาคใหม่จาก API"),
                ("statementPeriodFrom", "YYYY-MM", "optional month picker", "Period Statement From; ส่ง ค.ศ. format YYYY-MM"),
                ("statementPeriodTo", "YYYY-MM", "optional month picker; must be >= from", "Period Statement To; validate range ก่อน call API"),
                ("page", "integer", "default 1; >=1", "pagination ของ preview table"),
                ("size", "integer", "default 20; max 100", "BE จำกัด page size เพื่อกัน query หนัก"),
                ("resultTable.storeCode", "string 5 digits", "display only", "คอลัมน์ 1 รหัสร้านถูกกระทบ"),
                ("resultTable.storeName", "string", "display only", "คอลัมน์ 2 ชื่อร้านถูกกระทบ"),
                ("resultTable.region", "string", "display only", "คอลัมน์ 3 ภาค"),
                ("resultTable.storeType", "string", "display only", "คอลัมน์ 4 ประเภทร้าน"),
                ("resultTable.impactMonth", "MM/YYYY พ.ศ.", "display only", "คอลัมน์ 5 เดือนปีที่ถูกกระทบ"),
                ("resultTable.transferToSpDate", "DD/MM/YYYY พ.ศ.", "nullable", "คอลัมน์ 6 วันที่โอนเป็นร้าน SP"),
                ("resultTable.statementPeriod", "MM/YYYY พ.ศ.", "nullable", "คอลัมน์ 7 Period Statement"),
                ("resultTable.newStoreCode", "string 5 digits or '-'", "display only", "คอลัมน์ 8 รหัสร้านเปิดใหม่"),
                ("resultTable.newStoreName", "string or '-'", "display only", "คอลัมน์ 9 ชื่อร้านเปิดใหม่"),
                ("resultTable.newStoreRegion", "string or '-'", "display only", "คอลัมน์ 10 ภาค (ร้านใหม่)"),
                ("resultTable.newStoreType", "string or '-'", "display only", "คอลัมน์ 11 ประเภทร้าน (ร้านใหม่)"),
                ("resultTable.compensationAmount", "number #,##0.00", ">=0", "คอลัมน์ 12 ยอดเงินชดเชย; align right"),
                ("resultTable.statusName", "string/status badge", "required", "คอลัมน์ 13 สถานะ; สี badge ตาม status"),
                ("resultTable.operatorName", "string", "nullable", "คอลัมน์ 14 ชื่อ-นามสกุลผู้ดำเนินการ"),
                ("resultTable.resultText", "string", "nullable", "คอลัมน์ 15 ผลการพิจารณา"),
                ("resultTable.waitingDays", "integer", ">=0", "คอลัมน์ 16 รอดำเนินการ (วัน)"),
                ("derived.salesDataDays", "integer", "<60 = abnormal", "ข้อมูลประกอบสำหรับ class flag-red; ไม่ใช่ waitingDays"),
                ("resultTable.roundNo", "integer", ">=1", "คอลัมน์ 17 ครั้งที่"),
                ("resultTable.createdDate", "DD/MM/YYYY พ.ศ.", "required", "คอลัมน์ 18 วันที่สร้าง"),
                ("resultTable.docNo", "YYYY/xxxxx", "required", "คอลัมน์ 19 เลขที่เอกสาร; ใช้เปิด detail/preview"),
            ],
            [
                ("เปิด popup ร้าน", "ปุ่มแว่นขยายข้างรหัสร้านที่ถูกกระทบ", "GET /api/v1/stores/search?type=impacted", "เลือก store แล้วเติม storeCode/storeName"),
                ("Preview Report", "ปุ่ม Preview Report", "GET /api/v1/reports/status-summary", "validate required แล้ว render summary line/chart/table 19 columns"),
                ("เคลียร์ค่าเริ่มใหม่", "ปุ่มเคลียร์ค่าเริ่มใหม่", "client state", "reset filter, summary, table และ error message"),
                ("Export CSV to Batch", "ปุ่ม Export CSV to Batch ด้านบน/ท้าย filter", "GET /api/v1/reports/status-summary/export", "ส่ง filter ชุดเดียวกับ preview แล้ว download/queue CSV"),
                ("Hover chart", "hover bar chart", "client chart tooltip", "แสดง tooltip จำนวนเอกสาร/ยอดเงินตามภาค"),
                ("Open detail", "คลิกเลขที่เอกสารหรือ row", "navigate /documents/{docNo} หรือ preview modal", "เปิดเอกสารที่เกี่ยวข้อง"),
            ],
            [
                ApiSpec("GET", "/api/v1/stores/search", "Popup เลือกร้านที่ถูกกระทบ", {"q": "00788", "type": "impacted"}, {"items": [{"storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13", "region": "RS", "storeType": "FR Type B"}]}),
                ApiSpec("GET", "/api/v1/reports/status-summary", "Preview รายงานและข้อมูล chart/summary", {"impactedStoreCode": "00788", "newStoreCode": "00990", "impactMonthFrom": "2026-05", "impactMonthTo": "2026-05", "storeTypes": ["A", "B"], "status": "06", "resultCategory": "APPROVE", "regions": ["RS", "BN"], "statementPeriodFrom": "2026-05", "statementPeriodTo": "2026-05", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 10, "summary": {"totalItems": 10, "totalCompensationAmount": 439100.0, "overThresholdItems": 1, "abnormalSalesItems": 2}, "charts": {"status": [{"label": "รอฝ่าย SBP DSA ดำเนินการ", "value": 2}], "regionAmount": [{"region": "RS", "amount": 73850.0}]}, "items": [{"impactedStoreCode": "00788", "impactedStoreName": "รัตนอุทิศ ซ.13", "region": "RS", "storeType": "FR Type B", "impactMonth": "2026-05", "transferToSpDate": "2026-03-01", "statementPeriod": "2026-05", "newStoreCode": "00990", "newStoreName": "เซเว่นฯ รัตนาธิเบศร์ 12", "newStoreRegion": "RS", "newStoreType": "FR Type A", "compensationAmount": 48200.0, "statusName": "รอฝ่าย SBP DSA ดำเนินการ", "operatorName": "สมชาย ใจดี", "resultText": "-", "waitingDays": 2, "roundNo": 1, "createdDate": "2026-06-12", "docNo": "2569/00123"}]}),
                ApiSpec("GET", "/api/v1/reports/status-summary/export", "Export CSV to Batch ด้วย filter เดียวกับ preview", {"sameAsPreview": True, "format": "csv"}, {"contentType": "text/csv; charset=utf-8", "fileName": "status-summary-2569.csv", "queuedToBatch": True}),
            ],
            ["เปิดหน้า Report", "โหลด reference status/region/store type ถ้ามี API", "ผู้ใช้ระบุ filter", "Validate status/result และช่วงเดือน", "กด Preview แล้ว call report API", "แปลงวันที่ ค.ศ. จาก API เป็น พ.ศ. สำหรับแสดง", "render summary line, chart และ table 19 คอลัมน์", "กด Export แล้วส่ง filter เดียวกันไป export API"],
            ["status และ resultCategory เป็น required ก่อน preview/export", "month range ทุกคู่ต้อง from <= to", "ตารางแสดง 19 คอลัมน์ครบและ export ออกครบ 19 คอลัมน์", "ยอดเงิน format #,##0.00 และ total summary ตรงกับผลรวม API", "แถวข้อมูลยอดขายไม่ครบ 60 วันใช้ class flag-red โดยอิง derived.salesDataDays < 60", "export ใช้ filter เดียวกับ preview ล่าสุด"],
            ["ไม่เลือก status แล้ว preview ต้อง block", "ไม่เลือก resultCategory แล้ว export ต้อง block", "impactMonthFrom > impactMonthTo ต้อง error REPORT_DATE_RANGE_INVALID", "ค้นหาด้วยร้านถูกกระทบ", "เลือกหลาย region/storeType", "render table 19 columns", "export csv utf-8", "empty result แสดง summary เป็น 0"],
        ),
        Topic(
            "FE/LLDD-FE-Master-Config",
            "LLDD FE - Master and Config",
            "FE",
            6.5,
            55,
            FE_OWNER_PEERAKORN,
            "สร้างหน้าจอผู้ปฏิบัติงาน ปัจจัยภายนอก สิทธิ์เมนู และตั้งค่าระบบ",
            ["k2-operators-01.png", "k2-factors-01.png", "k2-permissions-01.png", "k2-permissions-02.png", "system-config-01.png", "system-config-02.png"],
            ["Operator master", "External factor master", "Menu permission", "System/Global Config (SCR-11)", "CRUD modal", "Audit/reason"],
            [
                ("employeeName", "string", "required", "เลือกจาก popup/search"),
                ("position", "dropdown", "required", "เลือกตำแหน่ง"),
                ("factorCode", "string", "required unique", "ห้ามซ้ำ"),
                ("reason", "text", "required on edit/delete", "บันทึก audit"),
                ("configValue", "string/number/boolean", "validate by type", "ห้ามแก้ is_editable=false"),
            ],
            [
                ("Add/Edit/Delete", "modal action", "POST/PUT/DELETE master API", "update table + audit"),
                ("Search employee", "แว่นขยาย", "GET /api/v1/employees/search", "select employee"),
                ("Save permission", "toggle permission", "PUT /api/v1/menu-permissions/{menuCode}", "save matrix"),
            ],
            [
                ApiSpec("GET", "/api/v1/operators", "SCR-08 list/filter ผู้ปฏิบัติงาน", {"q": "สมชาย", "positionCode": "06", "active": True, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"id": 1, "employeeId": "E001", "employeeName": "สมชาย ใจดี", "positionCode": "06", "zoneCode": "01", "active": True, "updatedAt": "2026-07-22T10:00:00+07:00"}]}),
                ApiSpec("POST", "/api/v1/operators", "SCR-08 เพิ่มผู้ปฏิบัติงาน", {"employeeId": "E001", "positionCode": "06", "zoneCode": "01", "active": True, "reason": "เพิ่มผู้รับผิดชอบ"}, {"id": 1, "message": "saved", "auditId": 901}),
                ApiSpec("PUT", "/api/v1/operators/{id}", "SCR-08 แก้ไข/ปิดใช้งานผู้ปฏิบัติงาน", {"positionCode": "08", "zoneCode": "01", "active": True, "reason": "ย้ายหน้าที่"}, {"id": 1, "message": "saved", "auditId": 902}),
                ApiSpec("GET", "/api/v1/employees/search", "SCR-08 popup ค้นหาพนักงาน", {"q": "E001", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"employeeId": "E001", "employeeName": "สมชาย ใจดี", "email": "somchai@example.test", "active": True}]}),
                ApiSpec("GET", "/api/v1/factors", "SCR-09 list/filter ปัจจัยภายนอก", {"q": "ถนน", "active": True, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"factorCode": "F001", "factorName": "ก่อสร้างถนน", "description": "ผลกระทบจากการก่อสร้าง", "active": True, "updatedAt": "2026-07-22T10:00:00+07:00"}]}),
                ApiSpec("POST", "/api/v1/factors", "SCR-09 เพิ่มปัจจัยภายนอก", {"factorCode": "F001", "factorName": "ก่อสร้างถนน", "description": "ผลกระทบจากการก่อสร้าง", "active": True, "reason": "เพิ่ม master"}, {"factorCode": "F001", "message": "saved", "auditId": 903}),
                ApiSpec("PUT", "/api/v1/factors/{code}", "SCR-09 แก้ไขปัจจัยภายนอก", {"factorName": "ก่อสร้างถนนระยะยาว", "description": "กระทบการเข้าร้าน", "active": True, "reason": "ปรับคำอธิบาย"}, {"factorCode": "F001", "message": "saved", "auditId": 904}),
                ApiSpec("DELETE", "/api/v1/factors/{code}", "SCR-09 ลบปัจจัยภายนอกที่ไม่ถูกใช้งาน", {"reason": "ยกเลิกค่า master"}, {"factorCode": "F001", "deleted": True, "auditId": 907}),
                ApiSpec("GET", "/api/v1/menu-permissions", "อ่าน matrix สิทธิ์เมนูทุก role", {"roleCode": "04"}, {"items": [{"menuCode": "k2-report", "roleCode": "04", "canView": True}]}),
                ApiSpec("PUT", "/api/v1/menu-permissions/{menuCode}", "บันทึกสิทธิ์เมนูรายเมนู", {"roleCode": "04", "canView": True, "reason": "ปรับสิทธิ์รายงาน"}, {"message": "saved"}),
                ApiSpec("GET", "/api/v1/configs", "SCR-11 list ค่าระบบ", {"q": "ATTACHMENT", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"key": "MAX_ATTACHMENT_MB", "value": 5, "valueType": "INTEGER", "editable": False, "description": "ขนาดไฟล์แนบสูงสุด", "updatedAt": "2026-07-22T10:00:00+07:00"}]}),
                ApiSpec("POST", "/api/v1/configs", "SCR-11 เพิ่มค่าระบบที่ไม่ใช่ secret", {"key": "REPORT_PAGE_SIZE", "value": 20, "valueType": "INTEGER", "description": "จำนวนแถวเริ่มต้น", "reason": "เพิ่มค่า report"}, {"key": "REPORT_PAGE_SIZE", "message": "saved", "auditId": 905}),
                ApiSpec("PUT", "/api/v1/configs/{key}", "SCR-11 แก้ค่าระบบที่ editable=true", {"value": 50, "reason": "เพิ่มจำนวนแถว"}, {"key": "REPORT_PAGE_SIZE", "value": 50, "valueType": "INTEGER", "editable": True, "message": "saved", "auditId": 906}),
            ],
            ["Open master page", "Load table", "Open modal", "Validate required/reason", "Call API", "Reload table/audit"],
            ["แก้ master ต้องมี reason", "factorCode ซ้ำไม่ได้", "permission toggle save ได้", "config type validate"],
            ["add operator", "edit factor without reason", "duplicate factor", "save permission", "edit locked config"],
        ),
        Topic(
            "FE/LLDD-FE-Batch-Monitor",
            "LLDD FE - Batch Job Monitor",
            "FE",
            3.5,
            30,
            FE_OWNER_KITTISAK,
            "สร้างหน้า Batch Job Monitor เฉพาะ 2 tab คือ แบบฟอร์มพารามิเตอร์ และประวัติการรัน สำหรับดู/แก้ค่าพารามิเตอร์ที่อนุญาตและตรวจสอบ run history ของ job",
            ["job-batch-02.png", "job-batch-03.png"],
            ["Job selector/list สำหรับเลือก job ที่ต้องดูรายละเอียด", "Tab: แบบฟอร์มพารามิเตอร์", "Tab: ประวัติการรัน", "Editable parameter form ตาม metadata ของ job", "Locked parameter display สำหรับค่าที่แก้ไม่ได้", "Run history table และ run log/detail drawer"],
            [
                ("selectedJobNo", "string", "required after selecting job", "รหัส job เช่น 1, 8b, 10"),
                ("activeTab", "enum", "formParameter หรือ historyRun", "default เป็น formParameter เมื่อเลือก job"),
                ("editableParams", "object/list", "editable=true เท่านั้น", "แสดง input/select/date ตาม field metadata และบันทึกเฉพาะ field ที่แก้ได้"),
                ("lockedParams", "object/list", "read-only", "แสดงเป็น disabled/read-only พร้อม badge ค่าคงที่หรือแก้ไม่ได้"),
                ("runHistory", "array", "read-only", "แสดง runId, status, start/end time, duration, trigger, operator, summary/error"),
                ("runStatus", "enum", "SUCCESS, FAILED, RUNNING, QUEUED", "ใช้ status badge สีตาม dictionary และ resolve label จาก statusCode"),
            ],
            [
                ("Select job", "click job row", "Job selector/list", "โหลด detail panel ของ job ที่เลือกและเปิด tab แบบฟอร์มพารามิเตอร์"),
                ("Open Form Parameter tab", "click tab", "แบบฟอร์มพารามิเตอร์", "แสดง editable/read-only parameter fields ของ job ที่เลือก"),
                ("Edit parameter", "change input/select/date", "แบบฟอร์มพารามิเตอร์", "validate field, mark form dirty และเปิดปุ่มบันทึกเมื่อข้อมูลถูกต้อง"),
                ("Save parameter form", "click save", "แบบฟอร์มพารามิเตอร์", "บันทึกเฉพาะ editable parameter values และแสดง saved state"),
                ("Open History Run tab", "click tab", "ประวัติการรัน", "แสดง run history ล่าสุดของ job ที่เลือก"),
                ("Open run detail", "click history row/detail", "ประวัติการรัน", "เปิด drawer/modal รายละเอียด run log แบบ read-only"),
            ],
            [
                ApiSpec("GET", "/api/v1/jobs", "โหลดรายการ job และสถานะล่าสุด", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 11, "items": [{"jobNo": "8b", "name": "StartInternalWorkflow", "enabled": True, "scheduleMode": "AFTER_JOB", "scheduleExpression": "8", "currentStatus": "SUCCESS", "lastRunId": 4451, "lastRunAt": "2026-07-22T05:35:00+07:00"}]}),
                ApiSpec("GET", "/api/v1/jobs/{jobNo}", "โหลด metadata/parameter schema ของ job ที่เลือก", {"jobNo": "8b"}, {"jobNo": "8b", "name": "StartInternalWorkflow", "enabled": True, "scheduleMode": "AFTER_JOB", "scheduleExpression": "8", "parameters": [{"key": "period", "label": "งวดข้อมูล", "type": "MONTH", "value": "2026-07", "editable": True, "required": True}, {"key": "workflowApi", "label": "Workflow API", "type": "STRING", "value": "/api/v1/workflows/instances", "editable": False, "required": True}]}),
                ApiSpec("PUT", "/api/v1/jobs/{jobNo}/params", "บันทึกเฉพาะ parameter ที่ editable", {"params": {"period": "2026-07"}, "reason": "ปรับงวด manual run"}, {"jobNo": "8b", "configVersion": 12, "updatedKeys": ["period"], "message": "saved"}),
                ApiSpec("PUT", "/api/v1/jobs/{jobNo}/enabled", "เปิด/ปิด job", {"enabled": False, "reason": "ปิดชั่วคราวช่วงปิดงบ"}, {"jobNo": "8b", "enabled": False, "message": "saved"}),
                ApiSpec("POST", "/api/v1/jobs/{jobNo}/run", "สั่ง manual run โดยกัน run ซ้อน", {"params": {"period": "2026-07"}, "reason": "rerun หลังแก้ข้อมูลต้นทาง"}, {"runId": 4452, "jobNo": "8b", "status": "QUEUED", "queuedAt": "2026-07-22T11:00:00+07:00"}),
                ApiSpec("GET", "/api/v1/jobs/{jobNo}/runs", "โหลดประวัติการรันล่าสุดก่อน", {"status": "FAILED", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"runId": 4450, "jobNo": "8b", "status": "FAILED", "triggerType": "MANUAL", "triggeredBy": "E001", "startedAt": "2026-07-22T05:20:00+07:00", "endedAt": "2026-07-22T05:21:30+07:00", "durationSec": 90, "readCount": 10, "successCount": 9, "rejectCount": 1, "errorCode": "GEN_FLOW_GATE_NOT_READY", "errorMessage": "ข้อมูลผู้อนุมัติยังไม่ครบ"}]}),
            ],
            ["Open Batch Monitor", "Select job from job selector/list", "Render detail panel with Form Parameter tab as default", "Edit editable parameter fields and save valid changes", "Switch to History Run tab", "Open a run history row to inspect log/detail"],
            ["เอกสารนี้กำหนด UI ที่ต้องทำเพียง 2 tab: แบบฟอร์มพารามิเตอร์ และประวัติการรัน", "flowchart การทำงานและฐานข้อมูลที่ใช้เป็น reference/dev lookup เท่านั้น ไม่ใช่ implementation scope ของเอกสารนี้", "รายละเอียดเทคนิค backend/storage ของ batch ไม่อยู่ในเอกสาร FE Batch Monitor", "locked parameter ต้องแก้ไม่ได้และต้องไม่ถูกส่งเป็นค่าที่ user แก้ไข", "history run เป็น read-only และเปิดรายละเอียด log ได้จาก row ที่เลือก"],
            ["select job and default to form parameter tab", "edit editable parameter and validate required/range", "confirm locked parameter remains read-only", "save parameter form sends editable values only", "switch to history run tab and sort latest first", "open run detail/log from history row", "verify flowchart/database tabs are not required deliverables"],
        ),
        Topic(
            "FE/LLDD-FE-Email-Template",
            "LLDD FE - Email Template and Notification Config",
            "FE",
            3.5,
            30,
            FE_OWNER,
            "สร้างหน้า Email Template และ Notification Config สำหรับอ่าน/แก้/preview/reset template อีเมลของระบบประกันรายได้ โดยแยกจากหน้า Batch Job Monitor",
            ["plan-email-01.png", "plan-email-02.png", "plan-email-03.png"],
            ["Email template list", "Template edit form", "Variable helper", "Preview modal", "Reset default confirm", "Notification recipient config display"],
            [
                ("templateCode", "EM-xx", "required", "เลือก template ที่ต้องแก้"),
                ("subject", "text", "required", "รองรับ variable token เช่น {{docNo}}"),
                ("body", "text/html", "required", "preview variable ก่อนบันทึก"),
                ("reason", "text", "required on save/reset", "บันทึก audit_logs"),
            ],
            [
                ("Open template", "click template", "GET /api/v1/email-templates/{code}", "show subject/body/variables"),
                ("Preview email", "preview", "POST /api/v1/email-templates/{code}/preview", "render variable sample"),
                ("Save template", "save", "PUT /api/v1/email-templates/{code}", "update template"),
                ("Reset default", "reset", "POST /api/v1/email-templates/{code}/reset", "restore default template"),
            ],
            [
                ApiSpec("GET", "/api/v1/email-templates", "รายการ template ของ SBP Mall", {}, {"items": [{"templateCode": "EM-01", "subject": "แจ้งเตือน {{docNo}}"}]}),
                ApiSpec("GET", "/api/v1/email-templates/{code}", "อ่าน template รายตัว", {"code": "EM-01"}, {"templateCode": "EM-01", "subject": "แจ้งเตือน {{docNo}}", "body": "...", "variables": ["docNo", "statusName"]}),
                ApiSpec("POST", "/api/v1/email-templates/{code}/preview", "preview ด้วย sample variables", {"variables": {"docNo": "2569/00123"}}, {"subject": "แจ้งเตือน 2569/00123", "body": "..."}),
                ApiSpec("PUT", "/api/v1/email-templates/{code}", "บันทึก template", {"subject": "แจ้งเตือน {{docNo}}", "body": "...", "reason": "ปรับข้อความ"}, {"message": "saved"}),
            ],
            ["Load templates", "Open template detail", "Edit subject/body", "Render preview", "Confirm save/reset with reason", "Reload audit/latest template"],
            ["subject/body required", "save/reset ต้องมี reason", "preview render variable ได้", "From/To/Cc แสดงตาม rule แต่ไม่แก้ในหน้านี้", "reset ต้อง confirm"],
            ["load templates", "open template", "preview variable", "save without reason", "reset default", "invalid token warning"],
        ),
        Topic(
            "BE/LLDD-BE-API-Common-Contracts",
            "LLDD BE - API Common Contracts",
            "BE",
            2.4,
            20,
            BE_OWNER_BUTSABA,
            "กำหนดสัญญากลางของ REST API ทุกเส้นเพื่อไม่ให้ endpoint รายตัวตีความต่างกัน: transport/auth/error/format/pagination/action/RBAC/audit/idempotency",
            [],
            [
                "Base URL, content type, charset and request tracing",
                "Auth/JWT platform validation and service-token exception",
                "Standard success envelopes for list/detail/mutation",
                "Standard error envelope and HTTP status mapping",
                "Field format for date/month/docNo/storeCode/amount/percent",
                "Document action input/output contract",
                "RBAC/menu permission and editable section guard",
                "Audit/reason and idempotency rules",
            ],
            [
                ("Base URL", "/api/v1", "required", "ทุก endpoint ใช้ prefix นี้"),
                ("Content-Type", "application/json; charset=utf-8", "required for JSON", "multipart เฉพาะ attachments"),
                ("Authorization", "Bearer <JWT>", "required for user endpoints", "validate signature/expiry/role; platform provides token"),
                ("X-Service-Token", "opaque service token", "required for internal workflow/batch callbacks", "ใช้กับ /workflows/instances และ external callback ที่ไม่ใช่ user JWT"),
                ("X-Request-Id", "uuid/string", "optional but logged", "ถ้าไม่ส่ง BE generate แล้วคืนใน log/trace"),
                ("ErrorEnvelope", "{code,message}", "message Thai verbatim", "ห้ามเพิ่ม error shape อื่นใน endpoint รายตัว"),
                ("PageResponse<T>", "{page,size,total,items}", "page>=1 size<=100", "ใช้กับทุก GET list"),
                ("MutationResponse", "{message}", "message optional for simple save", "ถ้า workflow action ใช้ ActionResponse แทน"),
                ("docNo", "YYYY/xxxxx พ.ศ.", "path/query", "URL encode slash ตาม client/router; service ประกอบกลับเป็น docNo"),
                ("storeCode/newStoreCode", "string 5 digits", "preserve leading zero", "ห้ามใช้ numeric id แทนรหัสร้านใน payload"),
                ("date/month", "ISO-8601 ค.ศ.", "YYYY-MM-DD / YYYY-MM", "FE แปลง พ.ศ. เฉพาะ display"),
                ("amount/percent", "number", "2 decimal", "format display อยู่ FE; BE validate precision/range"),
                ("result", "verbatim from actionOptions", "required for /actions", "ต้องเป็นค่าที่ BE ส่งมาใน role profile ของเอกสารนั้น"),
                ("ActionResponse", "{statusCode,nextSection,message}", "required for /actions", "FE resolve label จาก /document-statuses; mutation response ไม่คืน label ไทยซ้ำ"),
                ("reason", "text", "required for master/config/email/RBAC mutation", "write audit_logs ใน transaction เดียว"),
            ],
            [
                ("Authenticate user endpoint", "middleware", "auth.verifyJwt", "req.user = employeeId/roleCode/sectionCode"),
                ("Authorize menu/role", "middleware/service", "rbac.requireMenu/requireRole", "403 FORBIDDEN เมื่อไม่มีสิทธิ์"),
                ("Validate request", "controller", "zod schema", "400 VALIDATION envelope"),
                ("Return list", "repository/service", "PageResponse<T>", "pagination shape เดียวกัน"),
                ("Submit document action", "service", "documentAction.service.submit", "return ActionResponse"),
                ("Write audit", "transaction", "audit.service.write", "reason/updated_by/old_value/new_value"),
                ("Handle idempotency", "service", "requestId/business key", "duplicate returns existing result or 409 per endpoint rule"),
            ],
            [
                ApiSpec("ALL", "/api/v1/*", "Standard error envelope", None, {"code": "VALIDATION", "message": "ข้อความภาษาไทยตรงตาม SRS"}),
                ApiSpec("GET", "/api/v1/*", "Standard list envelope เมื่อ endpoint เป็นรายการ", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("POST", "/api/v1/documents/{docNo}/actions", "Document action contract กลาง; ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("GET", "/api/v1/me/menus", "RBAC/menu contract กลาง", {}, {"menus": [{"menuCode": "k2-report", "label": "รายงานสรุปสถานะ", "route": "/reports/income-audit", "group": "ระบบประกันรายได้", "canAccess": True}]}),
            ],
            [
                "Request enters logging middleware and request id is attached",
                "Auth middleware validates JWT or service token by endpoint allowlist",
                "RBAC guard checks role/menu/current workflow task owner",
                "Validate params/query/body with shared schema conventions",
                "Service executes business rule and document action if relevant",
                "Mutation writes domain row and audit/reason in the same transaction",
                "Controller maps result to standard envelope or throws AppError",
                "Error handler maps all failures to `{code,message}` only",
            ],
            [
                "ทุก endpoint ต้องใช้ common contract นี้",
                "ไม่มี endpoint คืน error shape อื่นนอกจาก `{code,message}`",
                "401/403/404/409/422/413/415 mapping คงที่และ test ได้",
                "GET list ทุกเส้นคืน `{page,size,total,items}`",
                "/actions รับ `{result,comment}` เท่านั้นและคืน `{statusCode,nextSection,message}`",
                "RBAC ใช้ role/menu/current task owner ฝั่ง BE เป็น source of truth",
                "mutation ที่ต้องมี reason ต้องเขียน audit_logs/consideration_logs/job_run_histories ตามโดเมน",
            ],
            ["missing JWT 401", "role forbidden 403", "validation error 400", "not found 404", "duplicate conflict 409", "list envelope", "action transition envelope", "audit reason required", "service token endpoint"],
        ),
        Topic(
            "BE/LLDD-BE-API-Dashboard-Summary",
            "LLDD BE - API Dashboard Summary",
            "BE",
            3.3,
            28,
            BE_OWNER_BUTSABA,
            "ออกแบบ Backend APIs สำหรับ Dashboard KPI, pending summary, monthly chart และ status chart",
            [],
            ["Dashboard summary service", "KPI query", "Monthly compensation chart", "Status chart", "Cache 5 minutes"],
            [
                ("year", "พ.ศ. YYYY", "optional default current year", "ใช้ filter summary"),
                ("month", "YYYY-MM", "optional", "ใช้คำนวณยอดชดเชยเดือนปัจจุบัน"),
                ("sectionCode", "string", "optional", "filter งานค้างตาม section"),
            ],
            [
                ("Dashboard summary", "GET", "dashboard.service.getSummary", "return KPI/charts"),
                ("Refresh cache", "internal", "cache.invalidateDashboard", "refresh after document/status change"),
            ],
            [
                ApiSpec("GET", "/api/v1/dashboard/summary", "Dashboard summary API", {"year": 2569}, {"waitingTasks": 24, "storesThisMonth": 342, "compensationThisMonth": 8420000.0, "abnormalStores": 5, "monthlyChart": [], "statusChart": []}),
            ],
            ["Validate query", "Aggregate workflow_tasks/compensation_documents/compensation_histories", "Build chart datasets", "Cache response", "Return normalized JSON"],
            ["KPI ตรงกับ query", "cache TTL ไม่เกิน 5 นาที", "empty data คืน 0 ไม่คืน null"],
            ["dashboard fixture", "empty dashboard", "status chart count", "cache invalidation"],
        ),
        Topic(
            "BE/LLDD-BE-API-Document-List-Search",
            "LLDD BE - API Document List and Search",
            "BE",
            3.3,
            28,
            BE_OWNER_BUTSABA,
            "ออกแบบ APIs สำหรับงานรอดำเนินการและค้นหาเอกสารที่เกี่ยวข้อง",
            [],
            ["Inbox tasks API", "Document search API", "Pagination", "Status/year filter", "Abnormal row support"],
            common_doc_fields() + [
                ("year", "พ.ศ. YYYY", "required for /documents", "ไม่ระบุคืน 400 ตาม SRS"),
                ("page/size", "integer", "page>=1 size<=100", "pagination"),
            ],
            [
                ("Inbox tasks", "GET", "task.service.searchOpenTasks", "return waiting list"),
                ("Document search", "GET", "document.service.search", "return related list"),
            ],
            [
                ApiSpec("GET", "/api/v1/tasks", "Inbox tasks API", {"sectionCode": "06", "page": 1, "size": 20}, {"items": [{"docNo": "2569/00123", "waitingDays": 3}]}),
                ApiSpec("GET", "/api/v1/documents", "Document search API", {"year": 2569, "storeCode": "00788", "status": "06", "page": 1}, {"items": [{"docNo": "2569/00123", "statusCode": "06"}]}),
            ],
            ["Read JWT section/role", "Validate year for documents", "Build filter query", "Join impacted_stores", "Return page result"],
            ["year missing fails for /documents", "leading zero storeCode preserved", "pagination returns total", "status filter works"],
            ["tasks by section", "documents missing year", "store search", "empty result"],
        ),
        Topic(
            "BE/LLDD-BE-API-Document-Create-Update",
            "LLDD BE - API Document Create and Update",
            "BE",
            4.2,
            36,
            BE_OWNER,
            "ออกแบบ APIs สำหรับสร้างเอกสารใหม่และบันทึกส่วนย่อยของเอกสาร",
            [],
            ["Create document", "Duplicate guard", "Running doc number", "Partial update", "Business validation"],
            common_doc_fields() + [
                ("requestId", "string", "optional", "ใช้ trace request; duplicate guard หลักเป็น business key"),
                ("source", "MANUAL|FS", "required", "แยกแหล่งสร้างเอกสาร"),
            ],
            [
                ("Create document", "POST", "document.service.create", "create doc + first workflow task"),
                ("Update document section", "PUT", "document.service.updateSections", "save editable sections"),
            ],
            [
                ApiSpec("POST", "/api/v1/documents", "Create document API", {"impactedStoreCode": "00788", "impactMonth": "2026-06", "source": "MANUAL", "newStoreCode": "00990", "roundNo": 1, "reason": "manual create", "requestId": "uuid"}, {"docNo": "2569/00124", "statusCode": "06"}),
                ApiSpec("PUT", "/api/v1/documents/{docNo}", "Update document partial sections", {"newStores": [{"newStoreCode": "00990", "compensatePercent": 100}]}, {"message": "saved"}),
            ],
            ["Validate required fields", "Check duplicate store/month", "Generate docNo", "Insert compensation_documents", "Open workflow task", "Save section updates in transaction"],
            ["duplicate business key returns 409", "docNo format YYYY/xxxxx", "compensatePercent sum=100", "requestId trace does not replace business duplicate guard"],
            ["create success", "create duplicate", "update allocation invalid", "permission denied section"],
        ),
        Topic(
            "BE/LLDD-BE-API-Document-Detail-Aggregate",
            "LLDD BE - API Document Detail Aggregate",
            "BE",
            4.5,
            38,
            BE_OWNER_BUTSABA,
            "ออกแบบ aggregate API สำหรับโหลดรายละเอียดเอกสารครบทุก section ให้หน้า FE detail",
            [],
            ["Document aggregate query", "Role profile output", "Store impact/new-store/factor mapping", "Compensation summary", "Related master lookup"],
            common_doc_fields() + [
                ("docNo", "YYYY/xxxxx", "required path param", "หาเอกสารและ section ทั้งหมด"),
                ("visibleSections/editableSections", "array", "computed by BE", "FE render ตาม key ที่ส่งมาเท่านั้น"),
                ("actionOptions", "array", "computed by BE", "radio options + requireComment สำหรับ action panel"),
            ],
            [
                ("Get detail", "GET", "documentAggregate.service.getByDocNo", "return 12 sections"),
                ("Get lookup", "GET", "lookup service", "return status/competitors/factors"),
            ],
            [
                ApiSpec("GET", "/api/v1/documents/{docNo}", "Document aggregate API", {"docNo": "2569/00123"}, {"docNo": "2569/00123", "statusCode": "06", "viewerRbacRoleCode": "R-XX", "roleProfileCode": "P-06", "visibleSections": ["doc-header", "sec-sales", "sec-map", "sec-newstore", "sec-competitor", "sec-factor", "sec-attach", "sec-comp-history", "sec-decision-history", "sec-action"], "editableSections": [], "canUploadAttachment": True, "canAction": True, "actionOptions": [{"label": "เห็นควรไม่ชดเชย", "requireComment": True}], "impactedStore": {"storeCode": "00788"}, "newStores": []}),
                ApiSpec("GET", "/api/v1/competitors", "Competitor lookup", {"q": "lotus"}, {"items": [{"competitorCode": "C007", "competitorName": "Lotus Express"}]}),
            ],
            ["Validate docNo", "Load header", "Load child sections", "Compute role profile", "Map to FE response shape", "Return aggregate"],
            ["404 when doc not found", "role profile output matches FE Document Detail spec", "nullable section returns empty array", "amount/date formatting source consistent"],
            ["detail success", "detail not found", "role profile output", "empty child sections"],
        ),
        Topic(
            "BE/LLDD-BE-API-Document-Workflow-Actions",
            "LLDD BE - API Document Workflow Actions",
            "BE",
            4.0,
            34,
            BE_OWNER_BUTSABA,
            "ออกแบบ APIs สำหรับรับผลพิจารณา ตรวจสิทธิ์ action และบันทึก audit/consideration log",
            [],
            ["Submit action", "Action owner guard", "Amount threshold reference", "Send back result", "Audit and email rule"],
            [
                ("docNo", "YYYY/xxxxx", "required", "path param"),
                ("result", "verbatim from actionOptions", "required", "ต้องเป็นค่าที่ API detail ส่งมาให้ผู้ใช้ในเอกสารนั้น"),
                ("comment", "text", "required for return/reject", "trim ก่อนบันทึก"),
            ],
            [
                ("Submit action", "POST", "documentAction.service.submit", "submit result and update status"),
                ("Write audit", "transaction", "considerationLog.repository.insert", "record action history"),
                ("Send email", "async", "notification.service.sendByStatusRule", "notify next owner"),
            ],
            [
                ApiSpec("POST", "/api/v1/documents/{docNo}/actions", "Document action API ตัวอย่างเมื่อ currentSection=01 จึงเปลี่ยนไป 02", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("GET", "/api/v1/documents/{docNo}/timeline", "Timeline API", {"docNo": "2569/00123"}, {"items": [{"section": "06", "result": "ชดเชย"}]}),
            ],
            ["Lock current action task", "Validate owner and selected result against actionOptions", "Apply server-side business rule", "Update document/task", "Insert consideration_logs", "Trigger email"],
            ["non-owner returns 403", "missing result returns exact SRS message", "invalid result for this role profile returns 422", "duplicate submit blocked by current open task lock", "audit written in same transaction"],
            ["submit compensate", "submit not compensate", "send back", "invalid result", "duplicate action"],
        ),
        Topic(
            "BE/LLDD-BE-API-Workflow-Instances",
            "LLDD BE - Workflow Engine and API Workflow Instances",
            "BE",
            3.3,
            28,
            BE_OWNER,
            "ออกแบบ Workflow Engine ภายในและ POST /api/v1/workflows/instances สำหรับเปิด workflow จาก Job 8b แทน K2 REST StartInstance โดยเป็นเจ้าของ Gen Flow Gate W/Y/N",
            [],
            [
                "Internal Workflow Engine API only",
                "No FE screen and no Flow page work",
                "Gen Flow Gate W/Y/N owner",
                "Require compensation document created by Job 8",
                "Create workflow instance and first task section 06",
                "Idempotency and rerun behavior for Job 8b",
            ],
            [
                ("impactProcessId", "integer/string", "required", "อ้าง fgi_impact_processes และ compensation_documents ที่ Job 8 สร้างแล้ว"),
                ("sourceJobNo", "string", "required fixed 8b", "ใช้ trace job_run_histories และ audit"),
                ("requestId", "uuid", "required", "idempotency key ต่อ impactProcessId + sourceJobNo"),
                ("workflow_generation_status", "W|Y|N", "computed", "W=รอ rerun, Y=เปิด workflow สำเร็จ, N=ไม่เข้าเกณฑ์ถาวร เช่น branch type นอกเซ็ต"),
                ("branchType", "FAM|FB1|FC1|FB2|FVB|FVC", "required by gate", "นอกเซ็ตตั้ง workflow_generation_status=N"),
                ("growthRateDiff", "number", "<= -10 required by gate", "ไม่ผ่านด้วยข้อมูลยังไม่พร้อมให้คง W และคืน 422 พร้อมเหตุผล"),
                ("salesStatus", "Y|N", "required by gate", "ค่าอื่นคง W และคืน 422"),
            ],
            [
                ("Open workflow", "POST", "workflowInstance.service.openFromImpact", "ผ่าน gate แล้วสร้าง/คืน instance"),
                ("Check status", "GET", "/api/v1/workflows/instances/{id}", "อ่าน instance status"),
                ("Summary", "GET", "/api/v1/workflows/summary", "ตัวเลข W/Y/N และงานค้างต่อ section"),
            ],
            [
                ApiSpec("POST", "/api/v1/workflows/instances", "เปิด workflow ภายในจาก impact process; เรียกโดย Job 8b ผ่าน service token ไม่ใช่ FE", {"impactProcessId": 901234, "sourceJobNo": "8b", "requestId": "job8b-901234-256907"}, {"docNo": "2569/00123", "instanceId": "WF-2569-00123", "workflowGenerationStatus": "Y", "firstSection": "06", "statusCode": "06", "status": "รอฝ่าย SBP DSA ดำเนินการ"}),
                ApiSpec("GET", "/api/v1/workflows/instances/{id}", "อ่านสถานะ workflow instance", {"id": "WF-2569-00123"}, {"instanceId": "WF-2569-00123", "docNo": "2569/00123", "status": "ACTIVE", "currentSection": "06"}),
                ApiSpec("GET", "/api/v1/workflows/summary", "สรุป W/Y/N และงานค้างต่อ section สำหรับ monitor", {"period": "2569-07"}, {"workflowGeneration": {"W": 12, "Y": 342, "N": 8}, "openTasksBySection": [{"sectionCode": "06", "count": 24}]}),
            ],
            [
                "Validate service token and idempotency key",
                "Load impact process and current workflow_generation_status",
                "Reject if status is already Y and return existing doc/instance idempotently",
                "Evaluate Gen Flow Gate in one service: status W, branch type allowlist, DV present, juristic different, growth_rate_diff <= -10, sales_status in Y/N",
                "If branch type outside allowlist, update workflow_generation_status=N and return 200 with reason for permanent skip",
                "If required data is missing/not ready, keep workflow_generation_status=W and return 422 reason so Job 8b can rerun",
                "If gate passes, require compensation_documents from Job 8, create workflow_instances/workflow_tasks first section 06, then update fgi_impact_processes.workflow_generation_status=Y in one transaction",
                "Enqueue notification summary outside transaction after commit",
            ],
            [
                "ไม่มี FE screen หรือ Flow page deliverable เพิ่มจาก LLDD นี้",
                "Job 8b ต้องเรียก API/service นี้และไม่ duplicate Gen Flow Gate",
                "ไม่เรียก K2 REST StartInstance และไม่สร้างไฟล์ BPM06001O/2O/3O",
                "ผ่าน gate แล้ว transaction ต้องมี document + instance + first task + Y ครบ หรือ rollback ทั้งหมด",
                "branch type นอกเซ็ตต้องตั้ง N แบบถาวร; ข้อมูลยังไม่พร้อมต้องคง W",
                "idempotent rerun ไม่สร้าง docNo/instance/task ซ้ำ",
            ],
            ["gate pass creates workflow", "branch type invalid sets N", "missing DV keeps W", "duplicate request returns existing instance", "transaction rollback on task insert failure", "service token missing returns 401"],
        ),
        Topic(
            "BE/LLDD-BE-API-Attachment-Sales-Timeline",
            "LLDD BE - API Attachment Sales and Timeline",
            "BE",
            3.5,
            30,
            BE_OWNER,
            "ออกแบบ APIs สำหรับไฟล์แนบ ข้อมูลยอดขายเพิ่มเติม และ timeline/history",
            [],
            ["Attachment metadata", "Upload/download adapter", "Sales 4 windows", "Timeline query", "File validation"],
            common_doc_fields() + [
                ("file", "multipart", "<=5MB", "validate extension and content type"),
                ("sectionCode", "string", "required on upload", "บันทึกว่าแนบในขั้นไหน"),
            ],
            [
                ("Upload attachment", "POST multipart", "attachment.service.upload", "store file and metadata"),
                ("Download attachment", "GET", "attachment.service.download", "stream file"),
                ("Get sales", "GET", "sales.service.getDocumentSales", "return sales windows"),
            ],
            [
                ApiSpec("POST", "/api/v1/documents/{docNo}/attachments", "Upload attachment API", {"file": "multipart <= 5MB", "sectionCode": "06"}, {"attachId": 771, "fileName": "evidence.pdf"}),
                ApiSpec("GET", "/api/v1/documents/{docNo}/sales", "Sales detail API", {"docNo": "2569/00123"}, {"growthRateDiff": -12.45, "totalWorkingDays": 60, "windows": [{"label": "ก่อนเปิด 15 วัน", "rows": []}]}),
                ApiSpec("GET", "/api/v1/documents/{docNo}/timeline", "Timeline/history API", {"docNo": "2569/00123"}, {"items": []}),
            ],
            ["Validate docNo/permission", "Validate file size/type", "Store file metadata", "Load sales summary and transactions", "Return timeline ordered by action time"],
            ["file >5MB returns 413", "unsupported file type returns 415", "sales windows are ordered", "timeline newest/oldest order matches FE expectation"],
            ["upload success", "upload too large", "download missing file", "sales not found", "timeline empty"],
        ),
        Topic(
            "BE/LLDD-BE-API-Lookup-RBAC-Email",
            "LLDD BE - API Lookup RBAC and Email Template",
            "BE",
            4.7,
            40,
            BE_OWNER,
            "ออกแบบ APIs ที่ตกหล่นจาก shared lookup, RBAC/menu permission, audit log และ email template ของ SBP Mall",
            [],
            ["Lookup APIs", "Employee search", "Role/menu/menu-permission CRUD", "Audit log search", "Email template CRUD/reset", "Auth endpoints are platform reference only"],
            [
                ("q", "string", "optional", "ใช้ค้นหา stores/employees/competitors"),
                ("type", "impacted|new", "required for stores/search", "เลือกแหล่ง impacted_stores หรือ stores"),
                ("roleCode", "00-10", "required for permission", "อ้าง roles"),
                ("menuCode", "string", "required for permission", "อ้าง menus"),
                ("templateCode", "EM-01..EM-08", "required", "email template key"),
                ("reason", "text", "required mutation", "บันทึก audit_logs"),
            ],
            [
                ("Store lookup", "GET", "lookup.service.searchStores", "return impacted/new stores"),
                ("Employee lookup", "GET", "employee.service.search", "return employees for operator popup"),
                ("Permission save", "PUT", "rbac.service.saveMenuPermission", "update can_access and audit"),
                ("Email template save/reset", "PUT/POST", "notificationTemplate.service", "update/reset template and audit"),
            ],
            [
                ApiSpec("GET", "/api/v1/stores/search", "ค้นหาร้านสำหรับ popup", {"q": "00788", "type": "impacted"}, {"items": [{"storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13"}]}),
                ApiSpec("GET", "/api/v1/document-statuses", "รายการสถานะเอกสาร verbatim", {}, {"items": [{"statusCode": "06", "statusName": "รอฝ่าย SBP DSA ดำเนินการ"}]}),
                ApiSpec("GET", "/api/v1/workflow-sections", "รายการ section 5 ขั้น", {}, {"items": [{"sectionCode": "06", "sectionName": "ฝ่าย SBP DSA"}]}),
                ApiSpec("GET", "/api/v1/employees/search", "ค้นหาพนักงานสำหรับ master/operator", {"q": "สมชาย"}, {"items": [{"employeeId": "E001", "employeeName": "สมชาย ใจดี"}]}),
                ApiSpec("GET", "/api/v1/menu-permissions", "อ่าน matrix สิทธิ์เมนูทุก role", {"roleCode": "04"}, {"items": [{"menuCode": "k2-report", "roleCode": "04", "canAccess": True}]}),
                ApiSpec("PUT", "/api/v1/menu-permissions/{menuCode}", "บันทึกสิทธิ์เมนูรายเมนู", {"roleCode": "04", "canAccess": True, "reason": "ปรับสิทธิ์รายงาน"}, {"message": "saved"}),
                ApiSpec("GET", "/api/v1/roles", "อ่านรายการ role", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 11, "items": [{"roleCode": "04", "roleName": "ผู้ดูแลระบบ", "system": True, "active": True}]}),
                ApiSpec("POST", "/api/v1/roles", "สร้าง role", {"roleCode": "11", "roleName": "ผู้ตรวจสอบ", "active": True, "reason": "เพิ่มบทบาทผู้ตรวจสอบ"}, {"roleCode": "11", "roleName": "ผู้ตรวจสอบ", "system": False, "active": True}),
                ApiSpec("PUT", "/api/v1/roles/{roleCode}", "แก้ role ที่ไม่ใช่ system role", {"roleName": "ผู้ตรวจสอบอาวุโส", "active": True, "reason": "ปรับชื่อบทบาท"}, {"roleCode": "11", "roleName": "ผู้ตรวจสอบอาวุโส", "system": False, "active": True}),
                ApiSpec("DELETE", "/api/v1/roles/{roleCode}", "ลบ role ที่ไม่ถูกใช้งาน", {"reason": "ยกเลิกบทบาททดสอบ"}, {"roleCode": "11", "deleted": True}),
                ApiSpec("POST", "/api/v1/menus", "สร้างเมนูและสิทธิ์เริ่มต้นทุก role", {"menuCode": "k2-audit", "menuName": "ประวัติการแก้ไข", "route": "/audit", "sortOrder": 90, "active": True, "reason": "เพิ่มเมนูตรวจสอบ"}, {"menuCode": "k2-audit", "created": True}),
                ApiSpec("PUT", "/api/v1/menus/{menuCode}", "แก้เมนู", {"menuName": "ประวัติการแก้ไขข้อมูล", "route": "/audit", "sortOrder": 90, "active": True, "reason": "ปรับชื่อเมนู"}, {"menuCode": "k2-audit", "updated": True}),
                ApiSpec("DELETE", "/api/v1/menus/{menuCode}", "ลบเมนูพร้อมสิทธิ์ที่เกี่ยวข้อง", {"reason": "ยกเลิกเมนูทดสอบ"}, {"menuCode": "k2-audit", "deleted": True}),
                ApiSpec("GET", "/api/v1/audit-logs", "ค้นประวัติการแก้ master", {"tableName": "roles", "refKey": "11", "action": "UPDATE", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"auditId": 9901, "tableName": "roles", "refKey": "11", "action": "UPDATE", "reason": "ปรับชื่อบทบาท", "changedBy": "E001", "changedAt": "2026-07-22T10:15:00+07:00"}]}),
                ApiSpec("GET", "/api/v1/email-templates", "อ่านรายการ email template", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 8, "items": [{"code": "EM-01", "name": "แจ้งสร้างเอกสาร", "subject": "เอกสาร {{docNo}}", "updatedAt": "2026-07-22T09:00:00+07:00"}]}),
                ApiSpec("GET", "/api/v1/email-templates/{code}", "อ่าน email template รายตัว", {"code": "EM-01"}, {"code": "EM-01", "name": "แจ้งสร้างเอกสาร", "subject": "เอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "variables": ["docNo"], "fromRule": "SYSTEM", "toRule": "NEXT_SECTION", "ccRule": "NONE"}),
                ApiSpec("PUT", "/api/v1/email-templates/{code}", "แก้ subject/body โดย recipient rule คงเดิม", {"subject": "แจ้งเอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "reason": "ปรับถ้อยคำ"}, {"code": "EM-01", "subject": "แจ้งเอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "updatedAt": "2026-07-22T10:20:00+07:00"}),
                ApiSpec("POST", "/api/v1/email-templates/{code}/reset", "รีเซ็ต template รายตัว", {"reason": "คืนค่าเริ่มต้น"}, {"code": "EM-01", "reset": True}),
                ApiSpec("POST", "/api/v1/email-templates/reset-all", "รีเซ็ต template ทั้งหมด", {"reason": "คืนค่าเริ่มต้นก่อน UAT"}, {"resetCount": 8}),
            ],
            ["Validate query/role/menu/template", "Read/write table by domain", "Apply reason requirement", "Write audit_logs", "Return standard envelope for list endpoints"],
            ["status label ต้องเป็น verbatim", "permission mutation ต้อง audit", "email recipient From/To/Cc ล็อกจาก status_email_rules", "Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้"],
            ["store lookup", "status lookup", "permission save without reason", "email template reset", "audit log search"],
        ),
        Topic(
            "BE/LLDD-BE-API-Report-Master-Config",
            "LLDD BE - API Report Master Config",
            "BE",
            5.6,
            48,
            BE_OWNER,
            "ออกแบบ APIs สำหรับรายงาน Master Data และ System Config",
            [],
            ["Report query service", "CSV export", "Operator/factor CRUD", "System/Global Config (SCR-11)", "Report filters"],
            [
                ("year", "พ.ศ. YYYY", "required for report", "return 400 if missing"),
                ("status", "statusCode string", "required", "6 สถานะเอกสาร; verbatim จาก document_statuses"),
                ("result", "APPROVE|REJECT", "required for report", "maps to consideration latest result"),
                ("region", "array/string", "optional", "13 region codes; multi-select"),
                ("storeType", "array/string", "optional", "A/B/C/D; multi-select"),
                ("impactedStoreCode", "string 5 digits", "optional", "คง leading zero"),
                ("newStoreCode", "string 5 digits", "optional", "คง leading zero"),
                ("reason", "text", "required mutation", "audit reason"),
                ("page/size", "integer", "page>=1 size<=100", "pagination"),
            ],
            [
                ("Report preview", "GET", "report.service.search", "paginated rows"),
                ("Report export", "GET", "report.service.exportCsv", "csv stream"),
                ("Master mutation", "POST/PUT/DELETE", "master.service.save", "audit log"),
            ],
            [
                ApiSpec("GET", "/api/v1/reports/status-summary", "รายงานตรวจสอบประกันรายได้", {"year": 2569, "status": "06", "result": "APPROVE", "region": ["RSU"], "storeType": ["A"], "impactedStoreCode": "00788", "newStoreCode": "00990", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("GET", "/api/v1/reports/status-summary/export", "Export CSV", {"year": 2569, "status": "06", "result": "APPROVE", "region": ["RSU"], "storeType": ["A"], "impactedStoreCode": "00788", "newStoreCode": "00990"}, {"fileName": "status-summary.csv"}),
                ApiSpec("GET", "/api/v1/operators", "อ่าน operator assignments", {"employeeId": "E001", "positionCode": "06", "active": True, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"id": 101, "employeeId": "E001", "employeeName": "สมชาย ใจดี", "positionCode": "06", "zoneCode": "01", "active": True}]}),
                ApiSpec("POST", "/api/v1/operators", "สร้าง operator assignment", {"employeeId": "E001", "positionCode": "06", "zoneCode": "01", "active": True, "reason": "มอบหมายผู้ปฏิบัติงาน"}, {"id": 101, "employeeId": "E001", "positionCode": "06", "zoneCode": "01", "active": True}),
                ApiSpec("PUT", "/api/v1/operators/{id}", "แก้ operator assignment", {"positionCode": "08", "zoneCode": "01", "active": True, "reason": "ย้ายหน้าที่"}, {"id": 101, "employeeId": "E001", "positionCode": "08", "zoneCode": "01", "active": True}),
                ApiSpec("DELETE", "/api/v1/operators/{id}", "ยกเลิก operator assignment", {"reason": "สิ้นสุดการมอบหมาย"}, {"id": 101, "deleted": True}),
                ApiSpec("GET", "/api/v1/factors", "อ่านปัจจัยภายนอก", {"q": "ก่อสร้าง", "active": True, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "description": "ปิดช่องทางจราจร", "active": True}]}),
                ApiSpec("POST", "/api/v1/factors", "สร้างปัจจัยภายนอก", {"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "description": "ปิดช่องทางจราจร", "active": True, "reason": "เพิ่มปัจจัยใหม่"}, {"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "active": True}),
                ApiSpec("PUT", "/api/v1/factors/{code}", "แก้ปัจจัยภายนอก", {"factorName": "ก่อสร้างและปิดถนน", "description": "ปิดช่องทางจราจรบางส่วน", "active": True, "reason": "ปรับคำอธิบาย"}, {"factorCode": "ROAD", "factorName": "ก่อสร้างและปิดถนน", "active": True}),
                ApiSpec("DELETE", "/api/v1/factors/{code}", "ลบปัจจัยภายนอกที่ไม่ถูกใช้งาน", {"reason": "ยกเลิกค่าทดสอบ"}, {"factorCode": "ROAD", "deleted": True}),
                ApiSpec("GET", "/api/v1/configs", "อ่าน system config", {"q": "UPLOAD", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"key": "UPLOAD_MAX_MB", "value": 5, "valueType": "INTEGER", "editable": True, "description": "ขนาดไฟล์สูงสุด"}]}),
                ApiSpec("GET", "/api/v1/configs/{key}", "อ่าน config ราย key", {"key": "UPLOAD_MAX_MB"}, {"key": "UPLOAD_MAX_MB", "value": 5, "valueType": "INTEGER", "editable": True, "description": "ขนาดไฟล์สูงสุด"}),
                ApiSpec("POST", "/api/v1/configs", "สร้าง config ที่ไม่ใช่ secret", {"key": "UPLOAD_WARN_MB", "value": 4, "valueType": "INTEGER", "editable": True, "description": "ระดับเตือนขนาดไฟล์", "reason": "เพิ่มค่าเตือน"}, {"key": "UPLOAD_WARN_MB", "value": 4, "valueType": "INTEGER", "editable": True}),
                ApiSpec("PUT", "/api/v1/configs/{key}", "แก้ config ที่ editable=true", {"value": 6, "description": "ขนาดไฟล์สูงสุด", "reason": "ปรับตามนโยบายไฟล์"}, {"key": "UPLOAD_MAX_MB", "value": 6, "valueType": "INTEGER", "editable": True}),
                ApiSpec("DELETE", "/api/v1/configs/{key}", "ลบ config ที่ editable=true และไม่ถูกใช้งาน", {"reason": "ยกเลิกค่าทดสอบ"}, {"key": "UPLOAD_WARN_MB", "deleted": True}),
            ],
            ["Validate filter", "Build query", "Apply pagination/export mode", "Return rows or CSV", "For mutations validate reason and write audit"],
            ["missing year/status/result fails", "export uses same filters as preview", "master edit requires reason", "config locked value cannot edit"],
            ["report missing year", "report export", "factor duplicate", "operator audit", "config locked"],
        ),
        Topic(
            "BE/LLDD-BE-Job-Batch-Email-SRM",
            "LLDD BE - Job Batch Email and SRM Integration",
            "BE",
            6.4,
            54,
            BE_OWNER_BUTSABA,
            "ออกแบบ Backend contracts สำหรับ Batch Job Admin, interface tracking/pending ACK, Email Template Service และ SRM Integration Adapter",
            [],
            ["Batch Job Admin APIs ครบ 6 endpoints", "Interface tracking และ pending ACK APIs", "Job runner guard/history", "Notification adapter", "STA ACK callback", "SRM integration inbound is optional/reference"],
            [
                ("jobNo", "string", "required", "maps to job registry"),
                ("sourceRefNo", "string", "required for SRM", "idempotency key"),
                ("templateCode", "EM-xx", "required", "email template key"),
                ("transactionId", "uuid", "generated", "integration log key"),
            ],
            [
                ("Run job", "POST", "jobRunner.run", "queued/run history"),
                ("Receive SRM", "POST", "srmIntegration.ingest", "transaction result"),
                ("Preview email", "POST", "emailTemplate.render", "merged subject/body"),
            ],
            [
                ApiSpec("GET", "/api/v1/jobs", "รายการ 11 job entry points พร้อมสถานะล่าสุด", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 11, "items": [{"jobNo": "8b", "name": "StartInternalWorkflow", "enabled": True, "scheduleMode": "AFTER_JOB", "scheduleExpression": "8", "currentStatus": "SUCCESS", "lastRunId": 4451, "lastRunAt": "2026-07-22T05:35:00+07:00"}]}),
                ApiSpec("GET", "/api/v1/jobs/{jobNo}", "รายละเอียด job และ typed parameter metadata", {"jobNo": "8b"}, {"jobNo": "8b", "name": "StartInternalWorkflow", "enabled": True, "scheduleMode": "AFTER_JOB", "scheduleExpression": "8", "parameters": [{"key": "period", "label": "งวดข้อมูล", "type": "MONTH", "value": "2026-07", "editable": True, "required": True}]}),
                ApiSpec("PUT", "/api/v1/jobs/{jobNo}/params", "บันทึกเฉพาะ parameter key ที่ metadata ระบุ editable", {"params": {"period": "2026-07"}, "reason": "ปรับงวด rerun"}, {"jobNo": "8b", "configVersion": 12, "updatedKeys": ["period"], "message": "saved"}),
                ApiSpec("PUT", "/api/v1/jobs/{jobNo}/enabled", "เปิด/ปิด job พร้อม audit reason", {"enabled": False, "reason": "ปิดชั่วคราวช่วงปิดงบ"}, {"jobNo": "8b", "enabled": False, "message": "saved"}),
                ApiSpec("POST", "/api/v1/jobs/{jobNo}/run", "สั่ง manual run/retry โดยตรวจ enabled และ concurrent run", {"params": {"period": "2026-07"}, "reason": "rerun หลังแก้ข้อมูล"}, {"runId": 4452, "jobNo": "8b", "status": "QUEUED", "queuedAt": "2026-07-22T11:00:00+07:00"}),
                ApiSpec("GET", "/api/v1/jobs/{jobNo}/runs", "ประวัติการรันแบบแบ่งหน้า", {"status": "FAILED", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"runId": 4450, "jobNo": "8b", "status": "FAILED", "triggerType": "MANUAL", "triggeredBy": "E001", "startedAt": "2026-07-22T05:20:00+07:00", "endedAt": "2026-07-22T05:21:30+07:00", "durationSec": 90, "readCount": 10, "successCount": 9, "rejectCount": 1, "errorCode": "GEN_FLOW_GATE_NOT_READY", "errorMessage": "ข้อมูลผู้อนุมัติยังไม่ครบ"}]}),
                ApiSpec("GET", "/api/v1/interfaces/tracking", "ค้นสถานะ interface ตาม dataset/business key/status/ช่วงเวลา", {"dataName": "COMPENSATE_INIT_I", "status": "SENT", "pending": True, "sentFrom": "2026-07-01T00:00:00+07:00", "sentTo": "2026-07-22T23:59:59+07:00", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"trackingId": 9912, "dataName": "COMPENSATE_INIT_I", "direction": "OUT", "businessKey": "2569/00098", "docNo": "2569/00098", "fileName": "COMPENSATE_INIT_I_25690722.dat", "status": "SENT", "sentAt": "2026-07-20T17:02:00+07:00", "ackedAt": None, "returnCode": None, "ageHours": 41}]}),
                ApiSpec("GET", "/api/v1/interfaces/pending-ack", "รายการ ACK ค้างตาม watchdog rule อายุอย่างน้อย 1 วัน", {"thresholdHours": 24, "dataName": "COMPENSATE_INIT_I", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "count": 1, "items": [{"trackingId": 9912, "dataName": "COMPENSATE_INIT_I", "businessKey": "2569/00098", "docNo": "2569/00098", "fileName": "COMPENSATE_INIT_I_25690722.dat", "sentAt": "2026-07-20T17:02:00+07:00", "ageHours": 41, "returnCode": None}]}),
                ApiSpec("GET", "/api/v1/email-templates/{code}", "อ่าน template และ merge-variable metadata", {"code": "EM-01"}, {"code": "EM-01", "name": "แจ้งสร้างเอกสาร", "subject": "เอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "variables": ["docNo"], "fromRule": "SYSTEM", "toRule": "NEXT_SECTION", "ccRule": "NONE"}),
                ApiSpec("PUT", "/api/v1/email-templates/{code}", "บันทึก subject/body", {"subject": "แจ้งเอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "reason": "ปรับถ้อยคำ"}, {"code": "EM-01", "subject": "แจ้งเอกสาร {{docNo}}", "body": "กรุณาตรวจสอบเอกสาร {{docNo}}", "updatedAt": "2026-07-22T10:20:00+07:00"}),
                ApiSpec("POST", "/api/v1/email-templates/{code}/preview", "render template โดยไม่บันทึก", {"variables": {"docNo": "2569/00123"}}, {"subject": "แจ้งเอกสาร 2569/00123", "body": "กรุณาตรวจสอบเอกสาร 2569/00123"}),
                ApiSpec("POST", "/api/v1/email-templates/{code}/reset", "รีเซ็ต template รายตัว", {"reason": "คืนค่าเริ่มต้น"}, {"code": "EM-01", "reset": True}),
                ApiSpec("POST", "/api/v1/interfaces/sta/ack", "STA ACK callback ให้ Job 10 เป็น safety net", {"transactionId": "TX-001", "returnCode": "A", "receivedAt": "2026-07-20T10:00:00+07:00"}, {"message": "acknowledged"}),
                ApiSpec("POST", "/api/v1/integrations/srm/income-guarantee", "รับข้อมูลประกันรายได้จาก SRM", {"sourceSystem": "SRM", "sourceRefNo": "SRM-001", "impactedStoreCode": "01234", "periodMonth": "2569-07"}, {"transactionId": "TX-001", "successRecords": 1, "failedRecords": 0}),
            ],
            ["Receive request", "Validate schema", "Check idempotency", "Process records", "Log success/failure", "Return summary"],
            ["job run guard prevents duplicate running job", "SRM duplicate skipped", "email preview renders variables", "failed records include detail"],
            ["run job", "run duplicate", "SRM missing field", "SRM duplicate", "email preview", "template save"],
        ),
    ]
    base.extend(document_detail_role_topics())
    db_map = {
        "BE/LLDD-BE-API-Dashboard-Summary": [
            ("workflow_tasks", "R", "นับงานค้างและ pending queue"),
            ("compensation_documents", "R", "นับเอกสาร/ร้านในงวด"),
            ("compensation_histories", "R", "ยอดชดเชยรายเดือน"),
            ("fgi_impact_sales_summaries", "R", "จำนวนข้อมูลผิดปกติ total_working_days < 60"),
        ],
        "BE/LLDD-BE-API-Document-List-Search": [
            ("workflow_tasks", "R", "อ่าน inbox ตาม section/role"),
            ("compensation_documents", "R", "ค้นเอกสารตาม year/status/store"),
            ("impacted_stores", "R", "ชื่อร้าน ภาค และข้อมูลร้าน"),
            ("fgi_impact_sales_summaries", "R", "flag ข้อมูลผิดปกติ/ยอดขายไม่ครบ 60 วัน"),
        ],
        "BE/LLDD-BE-API-Document-Create-Update": [
            ("compensation_documents", "R/W", "สร้างหัวเอกสารและแก้ไข section หลัก"),
            ("workflow_instances / workflow_tasks", "W", "เปิด workflow งานแรกตอนสร้างเอกสาร"),
            ("document_new_stores", "R/W", "ร้านเปิดใหม่และ % ชดเชย"),
            ("document_competitors", "R/W", "ร้านคู่แข่งในเอกสาร"),
            ("document_external_factors", "R/W", "ปัจจัยภายนอกในเอกสาร"),
            ("compensation_documents unique guard", "R", "กัน duplicate ด้วย business key: impact_process_id หรือ source + impacted_store_code + impact_month + new_store_code + round_no"),
        ],
        "BE/LLDD-BE-API-Document-Detail-Aggregate": [
            ("compensation_documents", "R", "หัวเอกสาร สถานะ และ section ปัจจุบัน"),
            ("impacted_stores", "R", "ข้อมูลร้านถูกกระทบ"),
            ("document_new_stores", "R", "ร้านเปิดใหม่และ compensate_percent"),
            ("document_competitors", "R", "คู่แข่ง"),
            ("document_external_factors", "R", "ปัจจัยภายนอก"),
            ("document_attachments", "R", "metadata ไฟล์แนบ"),
            ("consideration_logs", "R", "timeline/history"),
        ],
        "BE/LLDD-BE-API-Document-Workflow-Actions": [
            ("workflow_tasks", "R/W", "lock/close/open task ตาม transition"),
            ("compensation_documents", "W", "อัปเดต status/current_section/result"),
            ("consideration_logs", "W", "บันทึกผลพิจารณาและ comment"),
            ("status_email_rules", "R", "ผู้รับอีเมลตาม status"),
            ("workflow_tasks current-open lock", "R/W", "กัน action ซ้ำด้วย lock task ปัจจุบัน + closed_at"),
        ],
        "BE/LLDD-BE-API-Workflow-Instances": [
            ("fgi_impact_processes / fgi_impact_stores", "R/W", "อ่านข้อมูล impact และอัปเดต workflow_generation_status W/Y/N"),
            ("compensation_documents", "R/W", "create-if-missing จาก impact process และผูก docNo"),
            ("workflow_instances", "R/W", "สร้าง instance ACTIVE แทน K2 StartInstance"),
            ("workflow_tasks", "W", "เปิด first task section 06"),
            ("document_statuses / workflow_sections", "R", "lookup statusCode/status และ section แรก"),
            ("job_run_histories", "W", "บันทึกผลเรียกจาก Job 8b"),
            ("audit_logs", "W", "audit permanent skip N และ manual rerun"),
        ],
        "BE/LLDD-BE-API-Attachment-Sales-Timeline": [
            ("document_attachments", "R/W", "metadata ไฟล์แนบและ section ที่แนบ"),
            ("compensation_documents", "R", "ตรวจเอกสารและ impact_process_id"),
            ("fgi_impact_sales_summaries", "R", "หัวข้อมูลยอดขาย growth_rate_diff/total_working_days"),
            ("sales_transactions", "R", "ยอดขายรายวัน 4 windows"),
            ("consideration_logs", "R", "timeline/history"),
        ],
        "BE/LLDD-BE-API-Lookup-RBAC-Email": [
            ("stores / impacted_stores", "R", "store picker สำหรับร้านถูกกระทบ/ร้านเปิดใหม่"),
            ("document_statuses / workflow_sections", "R", "lookup สถานะ verbatim และ section 5 ขั้น"),
            ("employees", "R", "popup ค้นหาพนักงาน"),
            ("roles / menus / menu_permissions", "R/W", "RBAC/menu matrix"),
            ("email_templates / status_email_rules", "R/W", "เนื้อหา template และผู้รับที่ล็อกตามสถานะ"),
            ("audit_logs", "R/W", "ประวัติ mutation ของ RBAC/email/master"),
        ],
        "BE/LLDD-BE-API-Report-Master-Config": [
            ("compensation_documents", "R", "แหล่งข้อมูลรายงานและ filter status/year"),
            ("compensation_histories", "R", "ยอดเงินชดเชยและงวด statement"),
            ("consideration_logs", "R", "ผลพิจารณาล่าสุด APPROVE/REJECT"),
            ("operator_assignments", "R/W", "ผู้ปฏิบัติงาน"),
            ("external_factors", "R/W", "master ปัจจัยภายนอก"),
            ("system_configs", "R/W", "ค่ากำหนดกลาง"),
            ("audit_logs", "W", "ประวัติการแก้ไข operator/factor/config"),
        ],
        "BE/LLDD-BE-Job-Batch-Email-SRM": [
            ("job_configs", "R/W", "enabled, cron, params ของ batch"),
            ("job_run_histories", "R/W", "ประวัติการรันและสถานะล่าสุด"),
            ("interface_transactions", "R/W", "tracking file/API interface และ ACK"),
            ("email_templates", "R/W", "subject/body template"),
            ("status_email_rules", "R", "TO/CC ตามสถานะ"),
            ("audit_logs", "R/W", "audit การแก้ job/email"),
        ],
    }
    for topic in base:
        if not topic.flow_diagram and not is_batch_monitor_doc(topic.file):
            topic.flow_diagram = f"LLDD/assets/flows/{sanitize_filename(topic.file)}.png"
        if not topic.db_tables and topic.file in db_map:
            topic.db_tables = db_map[topic.file]
    base.extend(be_job_topics())
    for topic in base:
        if topic.file in HIGH_LEVEL_ESTIMATES:
            topic.hours = HIGH_LEVEL_ESTIMATES[topic.file]
        topic.days = round(topic.hours / HOURS_PER_DAY, 1)
    return base


def main_doc_blocks(all_topics: list[Topic]) -> list[dict[str, Any]]:
    order = {
        "FE/LLDD-FE-Integration-Contracts": 5,
        "FE/LLDD-FE-Foundation": 10,
        "FE/LLDD-FE-Overview": 20,
        "FE/LLDD-FE-Document-Lists": 30,
        "FE/LLDD-FE-Create-Document": 40,
        "FE/LLDD-FE-Document-Detail": 50,
        "FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA": 51,
        "FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer": 52,
        "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion": 53,
        "FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion": 54,
        "FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP": 55,
        "FE/LLDD-FE-Report": 60,
        "FE/LLDD-FE-Master-Config": 70,
        "FE/LLDD-FE-Batch-Monitor": 80,
        "FE/LLDD-FE-Email-Template": 85,
        "FE/LLDD-FE-Testing-Delivery": 90,
        "BE/LLDD-BE-API-Common-Contracts": 105,
        "BE/LLDD-BE-API-Dashboard-Summary": 110,
        "BE/LLDD-BE-API-Document-List-Search": 120,
        "BE/LLDD-BE-API-Document-Create-Update": 130,
        "BE/LLDD-BE-API-Document-Detail-Aggregate": 140,
        "BE/LLDD-BE-API-Document-Workflow-Actions": 150,
        "BE/LLDD-BE-API-Workflow-Instances": 155,
        "BE/LLDD-BE-API-Attachment-Sales-Timeline": 160,
        "BE/LLDD-BE-API-Lookup-RBAC-Email": 170,
        "BE/LLDD-BE-API-Report-Master-Config": 180,
        "BE/LLDD-BE-Job-Batch-Email-SRM": 190,
    }
    ordered = sorted(all_topics, key=lambda t: order.get(t.file, 999))
    counted_topics = [t for t in ordered if not is_document_detail_role_doc(t.file)]
    be_jobs = [t for t in counted_topics if "/Jobs/" in t.file]
    high_level = [t for t in counted_topics if "/Jobs/" not in t.file]
    role_docs = [t for t in ordered if is_document_detail_role_doc(t.file)]
    fe = [t for t in high_level if t.track == "FE"]
    be = [t for t in high_level if t.track == "BE"]
    schedule = build_topic_schedule(counted_topics)
    rows = [
        [
            t.track,
            t.title.replace("LLDD ", ""),
            f"{t.hours}",
            fmt_date(schedule[t.file][0]),
            fmt_date(schedule[t.file][1]),
            t.owner,
            Path(t.file).name,
        ]
        for t in high_level
    ]
    owner_stats: dict[str, dict[str, Any]] = {}
    for topic in counted_topics:
        key = topic.owner
        owner_stats.setdefault(key, {"hours": 0, "tracks": set(), "topics": [], "start": schedule[topic.file][0], "end": schedule[topic.file][1]})
        owner_stats[key]["hours"] += topic.hours
        owner_stats[key]["tracks"].add(topic.track)
        owner_stats[key]["topics"].append(topic.title.replace("LLDD FE - ", "").replace("LLDD BE - ", ""))
        owner_stats[key]["start"] = min(owner_stats[key]["start"], schedule[topic.file][0])
        owner_stats[key]["end"] = max(owner_stats[key]["end"], schedule[topic.file][1])
    owner_order = [
        FE_OWNER_KITTISAK,
        FE_OWNER_PEERAKORN,
        FE_OWNER,
        BE_OWNER_BUTSABA,
        BE_OWNER,
        BANK_BE_OWNER,
    ]
    continuity = {
        FE_OWNER_KITTISAK: "FE document journey: Create Document -> Document Detail/Action -> Batch Monitor",
        FE_OWNER_PEERAKORN: "FE list, reporting and admin journey: Document Lists -> Report -> Master/Config -> Testing/Delivery",
        FE_OWNER: "FE shared contracts and experience: Integration Contracts -> Foundation -> Overview -> Email Template/Notification Config",
        BE_OWNER_BUTSABA: "BE common/read/action/operations: Common Contracts -> Dashboard/List -> Detail Aggregate -> Workflow Actions -> Batch/Email/SRM",
        BE_OWNER: "BE command/workflow/support APIs: Create/Update -> Workflow Instances -> Attachment/Sales/Timeline -> Lookup/RBAC/Email -> Report/Master/Config",
        BANK_BE_OWNER: "BE batch ownership: Job 1-10 และ 8b ตั้งแต่ source analysis, migration, test, rerun ไปจนถึง handover",
    }
    owner_rows = []
    for key in owner_order:
        if key not in owner_stats:
            continue
        hours = owner_stats[key]["hours"]
        role = "FE & BE" if len(owner_stats[key]["tracks"]) > 1 else next(iter(owner_stats[key]["tracks"]))
        owner_rows.append([role, key, hours, fmt_date(owner_stats[key]["start"]), fmt_date(owner_stats[key]["end"]), continuity[key]])

    if set(owner_stats) != set(owner_order):
        raise ValueError("LLDD schedule must include all six developers")
    for owner, stats in owner_stats.items():
        work_weeks = stats["hours"] / HOURS_PER_WEEK
        if not (MIN_WORK_WEEKS_EXCLUSIVE < work_weeks <= MAX_WORK_WEEKS):
            raise ValueError(f"{owner} workload {fmt_days(work_weeks)} weeks is outside >3 to 4.5 weeks")

    def summary_scope(topic: Topic, count: int) -> str:
        items = topic.scope[:count]
        if topic.file == "FE/LLDD-FE-Master-Config" and "System/Global Config (SCR-11)" not in items:
            items.append("System/Global Config (SCR-11)")
        return ", ".join(items)

    return [
        h(1, "1. Purpose"),
        p("เอกสารหลักนี้เป็น LLDD Index สำหรับ Phase #4 - 4.3 SBP Operating Management ประกันรายได้ โดยสรุปหัวข้อใหญ่ของงาน FE/BE เฉพาะระบบประกันรายได้ (SBP Mall) และเชื่อมไปยังเอกสาร LLDD รายละเอียดของแต่ละหัวข้อ"),
        h(1, "2. Scope"),
        bullets([
            "ครอบคลุมเฉพาะระบบประกันรายได้ (SBP Mall)",
            "งาน FE/BE ในเอกสารนี้นับเฉพาะหน้าจอ module SBP Mall และ API/Job/Service ที่รองรับระบบประกันรายได้เท่านั้น",
            "งานออกแบบ flow ระดับระบบและ schema ระดับองค์กรไม่ถูกนับซ้ำเป็นงานหน้าจอ FE",
            "รายละเอียดที่จำเป็นต่อการพัฒนา การตรวจรับ และการส่งมอบถูกรวมไว้ใน LLDD แต่ละฉบับ",
            "รูปหน้าจอในหัวข้อ FE ใช้อธิบายองค์ประกอบและพฤติกรรมที่ต้องพัฒนา",
            "ไม่รวมการพัฒนา Login/Auth ของ platform และกระบวนการภายนอกขอบเขต SBP Mall",
        ]),
        h(1, "2.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], [
            ["Input", "Topic inventory, owner assignment, estimates, screenshots, API/job/database scope, and schedule assumptions for the SBP Mall income-guarantee work package."],
            ["Progress", "Use this index to sequence FE/BE work, confirm owner workload, locate detailed topic documents, and track dependency readiness before development starts."],
            ["Output", "A single implementation index with activity plan, owner workload, FE/BE summaries, job breakdown, dependencies, and deliverable checklist."],
        ]),
        h(1, "2.2 Schedule Assumption"),
        table(["Item", "Value"], [
            ["Start date for every owner", fmt_date(LLDD_START_DATE)],
            ["Target finish", fmt_date(LLDD_END_DATE)],
            ["Maximum delivery window", "ไม่เกิน 4.5 work weeks (22.5 วันทำงาน / 135 ชั่วโมงต่อคน)"],
            ["Allocation per developer", "มากกว่า 3 work weeks และไม่เกิน 4.5 work weeks หรือมากกว่า 90 ชั่วโมงและไม่เกิน 135 ชั่วโมงต่อคน"],
            ["Working-time rule", f"1 สัปดาห์ = {WORKDAYS_PER_WEEK} วันทำงาน, 1 วัน = {HOURS_PER_DAY} ชั่วโมง, รวม {HOURS_PER_WEEK} ชั่วโมงต่อสัปดาห์; ทำงานจันทร์-ศุกร์"],
            ["Task sequencing", f"หัวข้อเป็น delivery window ที่ทำต่อเนื่องหรือ overlap ได้ตาม dependency ภายใน {fmt_date(LLDD_START_DATE)} ถึง {fmt_date(LLDD_END_DATE)}; Aphiwit รับเฉพาะ Job 1-10 และ 8b"],
            ["Estimate interpretation", "แสดง delivery estimate เป็นชั่วโมงเท่านั้น โดยรวม buffer ตามความยาก ความเสี่ยงด้าน integration และ rerun แล้ว"],
        ]),
        h(1, "3. High Level Activity Plan"),
        table(["Track", "หัวข้อ", "ชั่วโมง", "Start Date", "End Date", "Owner", "เอกสารรายละเอียด"], rows),
        h(1, "4. Workload Balance and Continuity"),
        p("แผนนี้รวม owner ตามบุคคล โดย Aphiwit รับ Job 1-10 และ 8b คนเดียว ส่วน BE อื่นแบ่งระหว่าง But และ Vava ตามกลุ่ม contract/read/action กับ command/workflow/support ตามลำดับ ภาระงานของทุกคนมากกว่า 3 work weeks และไม่เกิน 4.5 work weeks เมื่อคิดที่ 5 วันต่อสัปดาห์และ 6 ชั่วโมงต่อวัน"),
        table(["Role", "Owner", "Hours", "Start Date", "End Date", "Work Focus"], owner_rows),
        h(1, "5. FE Summary"),
        table(["FE Topic", "ชั่วโมง", "Start Date", "End Date", "Deliverable"], [[t.title.replace("LLDD FE - ", ""), t.hours, fmt_date(schedule[t.file][0]), fmt_date(schedule[t.file][1]), summary_scope(t, 3)] for t in fe]),
        h(1, "6. Document Detail Role Pack"),
        p("เอกสารลูก 5 ฉบับนี้เป็นรายละเอียดแยกตาม role สำหรับอ่านประกอบ LLDD-FE-Document-Detail ไม่ถูกนับซ้ำใน activity plan/hour รวม"),
        table(["Role document", "Parent", "Hour allocation"], [[Path(t.file).name, "LLDD-FE-Document-Detail", "included in parent hours"] for t in role_docs]),
        h(1, "7. BE Summary"),
        table(["BE Topic", "ชั่วโมง", "Start Date", "End Date", "Deliverable"], [[t.title.replace("LLDD BE - ", ""), t.hours, fmt_date(schedule[t.file][0]), fmt_date(schedule[t.file][1]), ", ".join(t.scope[:4])] for t in be]),
        h(1, "8. BE Batch Job Breakdown"),
        table(
            ["Job", "ชั่วโมง", "Start Date", "End Date", "Owner", "เอกสารรายละเอียด"],
            [
                [
                    t.title.replace("LLDD BE - ", ""),
                    t.hours,
                    fmt_date(schedule[t.file][0]),
                    fmt_date(schedule[t.file][1]),
                    t.owner,
                    Path(t.file).name,
                ]
                for t in be_jobs
            ],
        ),
        h(1, "9. Dependency"),
        table(["Dependency", "Owner", "ใช้โดย"], [
            ["Common API/FE contracts", "BE/FE", "LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts เป็นสัญญากลางของทุกหน้า FE และทุก service BE"],
            ["API contract", "BE/FE", "ทุกหน้า FE และทุก service BE"],
            ["Auth/JWT platform และ menu service", "Platform/SSO/IAM", "FE Foundation เรียก /auth/me + /me/menus; BE validate Authorization: Bearer <JWT>"],
            ["Mock/fixture data", "BE", "FE development และ SIT"],
            ["Screenshots/prototype", "FE", "UI implementation"],
            ["Business rules", "BA/BE", "validation/action/report"],
        ]),
        h(1, "10. Deliverable Checklist"),
        bullets(["Main LLDD Index", "Common contract LLDD สำหรับ API/FE integration", "Detailed FE LLDD per SBP Mall page group", "Detailed BE LLDD per SBP Mall API group and Jobs 1-10 + 8b", "Screenshots embedded only for SBP Mall implementation pages", "Implementation flow diagrams embedded as reference, not Flow page deliverables"]),
    ]


def api_endpoint_groups() -> list[list[Any]]:
    return [
        ["Auth & สิทธิ์ผู้ใช้", "4", "POST /auth/login, POST /auth/refresh, GET /auth/me, GET /me/menus", "platform reference; FE consume token/menu"],
        ["งาน & เอกสารประกันรายได้", "10", "GET /tasks, GET/POST/PUT /documents*, POST /documents/{docNo}/actions, attachments, sales, timeline", "core document workflow API"],
        ["Lookup / Reference", "4", "GET /stores/search, /competitors, /document-statuses, /workflow-sections", "dropdown/search/status dictionary"],
        ["Master Data", "19", "operators, factors, employees, menu-permissions, roles, menus, audit-logs", "admin/master maintenance + audit reason"],
        ["System Config", "5", "GET/POST/PUT/DELETE /configs*", "global config; no secret storage"],
        ["Email Template", "5", "GET/PUT/POST /email-templates*", "notification template content"],
        ["รายงาน", "2", "GET /reports/status-summary, /export", "accounting preview/export CSV to Batch"],
        ["Batch Job Admin", "6", "GET/PUT/POST /jobs*", "monitor/admin/manual run guard"],
        ["Workflow ภายใน", "3", "POST /workflows/instances, GET /workflows/instances/{id}, /workflows/summary", "internal workflow engine for Job 8b"],
        ["Interface & Dashboard", "4", "GET /interfaces/*, POST /interfaces/sta/ack, GET /dashboard/summary", "file tracking, ACK, dashboard KPI"],
    ]


def api_doc_text(text: Any) -> str:
    value = str(text if text is not None else "")
    replacements = {
        "workflow.md": "ตารางเส้นทาง workflow",
        "api.md": "API contract",
        "database.md": "Database contract",
        "plan-api.html": "API catalog",
        "plan-database.html": "Database catalog",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def plan_api_groups() -> list[dict[str, Any]]:
    return read_js_array_from_html("plan-api.html", "GROUPS")


def plan_api_sql_by_path() -> dict[str, str]:
    return read_js_object_from_html("plan-api.html", "SQL_BY_PATH")


def endpoint_method_path(endpoint: dict[str, Any]) -> str:
    return f"{endpoint.get('m', '')} {endpoint.get('p', '')}"


def is_batch_api_group(group: dict[str, Any]) -> bool:
    return api_doc_text(group.get("name", "")) == "Batch Job Admin"


def api_endpoint_detail_blocks(groups: list[dict[str, Any]], sql_by_path: dict[str, str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [h(1, "6. Detailed Endpoint Specification")]
    endpoint_no = 0
    for group_idx, group in enumerate(groups, start=1):
        endpoints = group.get("eps", [])
        batch_reference_only = is_batch_api_group(group)
        blocks.extend([
            h(2, f"6.{group_idx} {api_doc_text(group.get('name', ''))}"),
            table(
                ["Endpoint", "Method", "Path", "Summary"],
                [[idx, api_doc_text(ep.get("m", "")), api_doc_text(ep.get("p", "")), api_doc_text(ep.get("sum", ""))] for idx, ep in enumerate(endpoints, start=1)],
            ),
        ])
        if batch_reference_only:
            blocks.append(p("Batch Job Admin เป็น endpoint reference สำหรับ FE Batch Monitor เฉพาะ 2 tab: แบบฟอร์มพารามิเตอร์ และประวัติการรัน เท่านั้น; ไม่ออกแบบ flowchart การทำงาน, step-by-step batch flow หรือ Database ที่ใช้ใน LLDD API ฉบับรวม"))
        for endpoint_idx, endpoint in enumerate(endpoints, start=1):
            endpoint_no += 1
            key = endpoint_method_path(endpoint)
            blocks.extend([
                h(3, f"6.{group_idx}.{endpoint_idx} {api_doc_text(key)}"),
                p(api_doc_text(endpoint.get("sum", ""))),
                table(
                    ["Item", "Detail"],
                    [
                        ["Global No.", endpoint_no],
                        ["Method", api_doc_text(endpoint.get("m", ""))],
                        ["Path", api_doc_text(endpoint.get("p", ""))],
                        ["Group", api_doc_text(group.get("name", ""))],
                        ["Access / Role", api_doc_text(endpoint.get("roles", ""))],
                        ["Requirement Tag", api_doc_text(endpoint.get("refT", ""))],
                    ],
                ),
            ])
            if batch_reference_only:
                blocks.append(p("Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor"))
            else:
                blocks.extend([
                table(
                    ["Step", "Flow"],
                    [[idx, api_doc_text(step)] for idx, step in enumerate(endpoint.get("flow", []), start=1)],
                ),
                table(
                    ["DB Object", "R/W", "Usage"],
                    [[api_doc_text(row[0]), api_doc_text(row[1]), api_doc_text(row[2])] for row in endpoint.get("db", [])],
                ),
                ])
            blocks.extend([
                payload("Request / Query / Header", api_doc_text(endpoint.get("req", "(ไม่มี body)"))),
                payload("Response", api_doc_text(endpoint.get("res", ""))),
                table(
                    ["Error / Condition"],
                    [[api_doc_text(err)] for err in endpoint.get("err", [])],
                ),
            ])
            sql = sql_by_path.get(key)
            if sql and not batch_reference_only:
                blocks.extend([
                    p("SQL Reference"),
                    code(api_doc_text(sql), "sql"),
                ])
    return blocks


def lldd_api_blocks(all_topics: list[Topic]) -> list[dict[str, Any]]:
    be_api_topics = [t for t in all_topics if t.track == "BE" and t.file.startswith("BE/LLDD-BE-API")]
    groups = plan_api_groups()
    endpoint_total = sum(len(g.get("eps", [])) for g in groups)
    sql_by_path = plan_api_sql_by_path()
    return [
        h(1, "1. Purpose"),
        p("เอกสารนี้เป็น LLDD API ระดับรวมของระบบ SBPGI/SBP Mall ใช้เป็น master reference สำหรับ REST contract, auth, error, endpoint catalog, implementation pattern และ test scope ของ BE API LLDD รายกลุ่ม"),
        h(1, "2. Scope"),
        table(
            ["Item", "Detail"],
            [
                ["API base", "/api/v1"],
                ["Endpoint count", f"{endpoint_total} endpoints, {len(groups)} groups"],
                ["Detailed implementation docs", ", ".join(Path(t.file).name for t in be_api_topics)],
                ["Out of scope", "Login/Auth implementation ของ platform, SAP/SR process ภายนอก, abnormal-stores endpoints ที่ยัง comment รอตัดสินใจ"],
            ],
        ),
        h(1, "2.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], [
            ["Input", "Endpoint catalog, auth mode, role/access rules, request/response payloads, error conditions, and SQL references from the API plan data."],
            ["Progress", "For each endpoint, apply middleware, bind DTO, validate, authorize, execute service transaction, map response, and pass errors through the centralized handler."],
            ["Output", "Normalized REST contract for implementation and testing: method/path, payload, response, errors, DB usage, and checklist coverage."],
        ]),
        h(1, "3. API Design Principles"),
        table(
            ["Rule", "Required behavior", "Developer note"],
            [
                ["Transport", "JSON UTF-8 ทุก endpoint; multipart เฉพาะ attachment upload", "FE shared API client เป็นจุดเดียวที่ตั้ง base URL/header"],
                ["Auth", "User endpoint ใช้ Bearer JWT; internal workflow/interface ใช้ service token/API key", "BE middleware ต้องแยก user token กับ service token ชัดเจน"],
                ["Status convention", "API ส่ง `statusCode`; FE resolve label จาก `/document-statuses`", "ห้ามส่ง label ไทยแทน code ใน field ที่กำหนดเป็น canonical code"],
                ["Role namespace", "`roleCode` = RBAC role, `sectionCode` = workflow section, `roleProfileCode` = P-06/P-08/P-01/P-02/P-03", "ป้องกันการชนความหมายของเลข 01/02/03/06/08"],
                ["Pagination", "GET list ใช้ `page,size` และคืน `{page,size,total,items}`", "size max 100 ตาม common contract"],
                ["Errors", "คืน `{code,message}`; message ภาษาไทยตาม SRS ถ้ามี", "FE แสดง message ตรง ๆ ไม่ paraphrase"],
                ["Mutation audit", "workflow action ลง consideration_logs; master/config/email ลง audit_logs; jobs ลง job_run_histories", "mutation ที่ต้องมี reason ต้อง validate ก่อนเริ่ม transaction"],
            ],
        ),
        h(1, "4. Endpoint Catalog"),
        table(
            ["Group", "Count", "Endpoint pattern", "Implementation focus"],
            [[api_doc_text(g.get("name", "")), len(g.get("eps", [])), ", ".join(api_doc_text(e.get("p", "")) for e in g.get("eps", [])[:4]) + (" ..." if len(g.get("eps", [])) > 4 else ""), api_doc_text(g.get("refT", ""))] for g in groups],
        ),
        h(1, "5. Request Lifecycle"),
        table(
            ["Step", "API behavior", "Failure handling"],
            [
                ["1. Middleware", "ตรวจ correlationId/requestId, auth token, content type, payload size", "401/413/415 ก่อนเข้า service"],
                ["2. Controller", "รวม params/query/body เป็น DTO และเรียก service", "controller ไม่ใส่ business rule"],
                ["3. Validation", "required/format/enum/date/page/size/docNo/storeCode", "400/422 พร้อม code/message จาก catalog"],
                ["4. Authorization", "ตรวจ menu/RBAC/document participant/current task owner/service token", "403 หรือ 409 เมื่อ task เปลี่ยนแล้ว"],
                ["5. Transaction", "mutation เปิด transaction ใน service; read ใช้ read-only query", "rollback เมื่อ persist หรือ audit fail"],
                ["6. Mapper", "map domain object เป็น DTO ตาม API contract", "ไม่ expose objectKey/secret/internal raw row"],
                ["7. Response", "คืน JSON หรือ binary stream สำหรับ download", "error ผ่าน centralized error handler"],
            ],
        ),
        *api_endpoint_detail_blocks(groups, sql_by_path),
        h(1, "7. API Test Checklist"),
        table(
            ["Test group", "Required cases"],
            [
                ["Common contract", "401, 403, 404, 409, 422, pagination envelope, error `{code,message}`"],
                ["Document workflow", "create duplicate, submit no result, invalid result for role profile, current task conflict, threshold >100000 route"],
                ["Attachment", "file >5MB, unsupported type, AV blocked, download not owner, download clean file"],
                ["Report", "year required, result required, CSV export with same filter as preview"],
                ["Job admin", "manual run when disabled, manual run while RUNNING, editable params only, run histories"],
                ["Security", "service token only endpoints, no objectKey/secret leak, audit reason required for mutations"],
            ],
        ),
        h(1, "8. Related LLDD"),
        table(["Document", "Use"], [[Path(t.file).name, t.objective] for t in be_api_topics]),
    ]


def database_table_catalog() -> list[list[Any]]:
    return [
        ["A", "fgi_impact_stores", "id", "impact_process_id, impacted_store_code", "impact pair; sales request and allocation data"],
        ["A", "fgi_impact_processes", "id", "impacted_store_code", "impact process hub and canonical workflow_generation_status"],
        ["A", "fgi_impact_sales_summaries", "id", "impact_process_id", "sales summary/growth rate"],
        ["A", "sales_transactions", "id", "sales_summary_id", "daily sales 4 windows x 15 days"],
        ["A", "fgi_impact_competitors", "id", "impact_process_id", "ALLMAP competitors"],
        ["A", "fcs_qssi_scores", "id", "store_id + category_code + period", "QSSI scores"],
        ["A", "interface_transactions", "id", "impact_process_id/sales_summary_id/doc_no", "interface tracking replacement"],
        ["B", "compensation_documents", "doc_no", "impact_process_id, status_code, current_section_code", "document header/core"],
        ["B", "document_new_stores", "id", "doc_no, new_store_code", "new stores and compensate percent"],
        ["B", "document_competitors", "id", "doc_no, competitor_code", "document competitors"],
        ["B", "document_external_factors", "id", "doc_no, factor_code", "document external factors"],
        ["B", "consideration_logs", "id", "doc_no", "approval/action history"],
        ["B", "document_attachments", "attach_id", "doc_no", "attachment metadata and storage pointer"],
        ["B", "compensation_histories", "id", "store_code, ref_doc_no", "compensation history/accounting export"],
        ["B", "workflow_instances", "instance_id", "doc_no", "internal workflow instance"],
        ["B", "workflow_tasks", "task_id", "instance_id, section_code, assignee_employee_id", "current/past tasks"],
        ["C", "stores", "store_code", "-", "all 7-Eleven stores"],
        ["C", "impacted_stores", "store_code", "stores.store_code", "SP impacted store subset"],
        ["C", "workflow_sections", "section_code", "-", "workflow sections 06/08/01/02/03"],
        ["C", "document_statuses", "status_code", "-", "document status dictionary"],
        ["C", "roles", "role_code", "-", "RBAC roles 00-10"],
        ["C", "menus", "menu_code", "-", "menu registry"],
        ["C", "menu_permissions", "role_code + menu_code", "roles, menus", "RBAC matrix"],
        ["C", "operator_assignments", "id", "section_code, employee_id", "operator by section/zone"],
        ["C", "employees", "employee_id", "-", "HR employee master"],
        ["C", "external_factors", "factor_code", "-", "external factor master"],
        ["C", "competitors", "competitor_code", "-", "competitor master"],
        ["C", "audit_logs", "id", "table_name + ref_key", "master/config/email audit"],
        ["C", "status_email_rules", "status_code", "workflow_sections", "notification recipients"],
        ["C", "email_templates", "template_code", "-", "notification templates"],
        ["C", "user_accounts", "employee_id", "role_code", "user account/JWT role"],
        ["C", "job_configs", "job_no", "-", "schema reference for batch schedule/config; not FE Database tab scope"],
        ["C", "job_run_histories", "run_id", "job_no", "job execution history"],
        ["C", "system_configs", "config_key", "-", "global config key-value"],
    ]


def database_ddl_sections() -> list[tuple[str, str]]:
    return [
        ("5.1 Zone C — Shared Master, RBAC, Config and Operations", """CREATE TABLE stores (
    store_code VARCHAR(5) PRIMARY KEY,
    store_name VARCHAR(200) NOT NULL, juristic_name VARCHAR(200), store_type VARCHAR(30),
    region_code VARCHAR(10), zone_code VARCHAR(10), branch_type VARCHAR(10),
    opened_date DATE, closed_date DATE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE impacted_stores (
    store_code VARCHAR(5) PRIMARY KEY REFERENCES stores(store_code),
    dv_code VARCHAR(20), opt_dv_user_id VARCHAR(30), latitude NUMERIC(10,7), longitude NUMERIC(10,7),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workflow_sections (
    section_code VARCHAR(2) PRIMARY KEY,
    section_name VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE document_statuses (
    status_code VARCHAR(2) PRIMARY KEY,
    status_name VARCHAR(200) NOT NULL,
    section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    sort_order INTEGER NOT NULL UNIQUE,
    terminal_flag BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE roles (
    role_code VARCHAR(10) PRIMARY KEY,
    role_name VARCHAR(200) NOT NULL, role_desc VARCHAR(500),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE menus (
    menu_code VARCHAR(50) PRIMARY KEY,
    menu_name VARCHAR(200) NOT NULL, menu_group VARCHAR(100),
    route_path VARCHAR(255), sort_order INTEGER NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE menu_permissions (
    role_code VARCHAR(10) NOT NULL REFERENCES roles(role_code),
    menu_code VARCHAR(50) NOT NULL REFERENCES menus(menu_code),
    can_access BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (role_code, menu_code)
);

CREATE TABLE employees (
    employee_id VARCHAR(30) PRIMARY KEY,
    emp_name VARCHAR(200) NOT NULL,
    emp_mail VARCHAR(255), department VARCHAR(150), zone_code VARCHAR(10), dv_code VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE impacted_stores
    ADD CONSTRAINT fk_impacted_store_opt_dv FOREIGN KEY (opt_dv_user_id) REFERENCES employees(employee_id);

CREATE TABLE operator_assignments (
    id BIGSERIAL PRIMARY KEY,
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    employee_id VARCHAR(30) NOT NULL REFERENCES employees(employee_id),
    emp_name VARCHAR(200) NOT NULL, emp_mail VARCHAR(255), zone_code VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_operator_scope UNIQUE (section_code, employee_id, zone_code)
);

CREATE TABLE external_factors (
    factor_code VARCHAR(30) PRIMARY KEY,
    factor_name VARCHAR(200) NOT NULL, factor_remark VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competitors (
    competitor_code VARCHAR(30) PRIMARY KEY,
    competitor_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE email_templates (
    template_code VARCHAR(30) PRIMARY KEY,
    name VARCHAR(200) NOT NULL, subject VARCHAR(500) NOT NULL, body TEXT NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_subject VARCHAR(500), default_body TEXT,
    is_customized BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_email_rules (
    status_code VARCHAR(2) NOT NULL REFERENCES document_statuses(status_code),
    template_code VARCHAR(30) NOT NULL REFERENCES email_templates(template_code),
    to_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    cc_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (status_code, template_code)
);

CREATE TABLE user_accounts (
    employee_id VARCHAR(30) PRIMARY KEY REFERENCES employees(employee_id),
    role_code VARCHAR(10) NOT NULL REFERENCES roles(role_code),
    section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    username VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_configs (
    job_no VARCHAR(10) PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    cron_expression VARCHAR(100), enabled BOOLEAN NOT NULL DEFAULT TRUE,
    params_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    secret_ref VARCHAR(255), version_no INTEGER NOT NULL DEFAULT 1,
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_job_config_no_inline_secret CHECK (params_json::text !~* '(password|private_key|client_secret)')
);

CREATE TABLE job_run_histories (
    run_id VARCHAR(50) PRIMARY KEY,
    job_no VARCHAR(10) NOT NULL REFERENCES job_configs(job_no),
    period_key VARCHAR(20), status VARCHAR(20) NOT NULL CHECK (status IN ('QUEUED','RUNNING','WAITING','SUCCESS','FAILED','CANCELLED')),
    trigger_type VARCHAR(20) NOT NULL, triggered_by VARCHAR(30), params_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_count INTEGER NOT NULL DEFAULT 0, success_count INTEGER NOT NULL DEFAULT 0,
    reject_count INTEGER NOT NULL DEFAULT 0, skipped_count INTEGER NOT NULL DEFAULT 0,
    error_code VARCHAR(80), error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, ended_at TIMESTAMP
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL, ref_key VARCHAR(200) NOT NULL,
    action_type VARCHAR(80) NOT NULL, old_value JSONB, new_value JSONB,
    reason VARCHAR(500), request_id VARCHAR(80), updated_by VARCHAR(30) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_configs (
    config_key VARCHAR(150) PRIMARY KEY,
    category VARCHAR(80) NOT NULL, config_value TEXT NOT NULL, value_type VARCHAR(30) NOT NULL,
    unit VARCHAR(30), description VARCHAR(500), is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_system_config_no_secret CHECK (config_key !~* '(password|private_key|client_secret|token)')
);"""),
        ("5.2 Zone A — Impact Pipeline, Sales and Interface", """CREATE TABLE fgi_impact_processes (
    id BIGSERIAL PRIMARY KEY,
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7) NOT NULL,
    process_status VARCHAR(30) NOT NULL, action_status VARCHAR(30),
    last_compensation_amount NUMERIC(14,2),
    workflow_generation_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (workflow_generation_status IN ('W','Y','N')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_process UNIQUE (impacted_store_code, impact_month)
);

CREATE TABLE fgi_impact_stores (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    new_store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
    impact_month CHAR(7) NOT NULL, distance_km NUMERIC(8,3),
    sales_request_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_request_status IN ('W','P','Y','E')),
    forecast_compensate_percent NUMERIC(7,4), adjust_compensate_percent NUMERIC(7,4),
    forecast_compensation_amount NUMERIC(14,2), adjust_compensation_amount NUMERIC(14,2),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_store_pair UNIQUE (impacted_store_code, new_store_code, impact_month)
);

CREATE TABLE fgi_impact_sales_summaries (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    total_working_days INTEGER NOT NULL DEFAULT 0 CHECK (total_working_days >= 0),
    growth_rate_before NUMERIC(9,4), growth_rate_after NUMERIC(9,4), growth_rate_diff NUMERIC(9,4),
    sales_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_status IN ('W','Y','N','E')),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_summary_process UNIQUE (impact_process_id)
);

CREATE TABLE sales_transactions (
    id BIGSERIAL PRIMARY KEY,
    sales_summary_id BIGINT NOT NULL REFERENCES fgi_impact_sales_summaries(id) ON DELETE CASCADE,
    txn_date DATE NOT NULL, window_no SMALLINT NOT NULL CHECK (window_no BETWEEN 1 AND 4),
    sales_amount NUMERIC(14,2) NOT NULL, sales_diff NUMERIC(14,2),
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE, source_checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_day_window UNIQUE (sales_summary_id, txn_date, window_no)
);

CREATE TABLE fgi_impact_competitors (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    competitor_code VARCHAR(30) NOT NULL REFERENCES competitors(competitor_code),
    name_th VARCHAR(200), branch_th VARCHAR(200), opened_date DATE, closed_date DATE,
    period_key CHAR(7) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_competitor UNIQUE (impact_process_id, competitor_code, period_key)
);

CREATE TABLE fcs_qssi_scores (
    id BIGSERIAL PRIMARY KEY,
    store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
    category_code VARCHAR(30) NOT NULL, score_period CHAR(7) NOT NULL,
    score_value NUMERIC(10,4) NOT NULL, source_file_name VARCHAR(255), source_checksum VARCHAR(64),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_qssi_score UNIQUE (store_code, category_code, score_period)
);

CREATE TABLE interface_transactions (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(50) REFERENCES job_run_histories(run_id),
    data_name VARCHAR(80) NOT NULL, direction VARCHAR(10) NOT NULL CHECK (direction IN ('IN','OUT','INTERNAL')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','SENT','ACKED','COMPLETED','FAILED','FAILED_RETRY')),
    impact_process_id BIGINT REFERENCES fgi_impact_processes(id),
    sales_summary_id BIGINT REFERENCES fgi_impact_sales_summaries(id),
    doc_no VARCHAR(10), business_key VARCHAR(200) NOT NULL, period_key VARCHAR(20) NOT NULL,
    correlation_id VARCHAR(100), file_name VARCHAR(255), file_checksum VARCHAR(64),
    outbox_status VARCHAR(20), return_code VARCHAR(50), return_message VARCHAR(500),
    retry_count INTEGER NOT NULL DEFAULT 0, sent_at TIMESTAMP, acked_at TIMESTAMP,
    purge_after TIMESTAMP, legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP,
    CONSTRAINT uq_interface_business UNIQUE (data_name, direction, business_key, period_key),
    CONSTRAINT ck_interface_typed_reference CHECK (num_nonnulls(impact_process_id, sales_summary_id, doc_no) >= 1)
);"""),
        ("5.3 Zone B — Document and Internal Workflow", """CREATE TABLE compensation_documents (
    doc_no VARCHAR(10) PRIMARY KEY,
    be_year INTEGER NOT NULL, running_no INTEGER NOT NULL,
    impact_process_id BIGINT NOT NULL UNIQUE REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7), new_store_code VARCHAR(5) REFERENCES stores(store_code), round_no INTEGER,
    source VARCHAR(20) NOT NULL DEFAULT 'FS' CHECK (source IN ('FS','MANUAL')),
    status_code VARCHAR(2) NOT NULL REFERENCES document_statuses(status_code),
    current_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    total_compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    version_no INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(30) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(30), updated_at TIMESTAMP,
    CONSTRAINT uq_comp_be_year_running UNIQUE (be_year, running_no),
    CONSTRAINT uq_comp_business UNIQUE (source, impacted_store_code, impact_month, new_store_code, round_no)
);

ALTER TABLE interface_transactions
    ADD CONSTRAINT fk_interface_doc_no FOREIGN KEY (doc_no) REFERENCES compensation_documents(doc_no);

CREATE TABLE document_new_stores (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
    distance_km NUMERIC(8,3), compensate_percent NUMERIC(7,4) NOT NULL CHECK (compensate_percent BETWEEN 0 AND 100),
    compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    source_system VARCHAR(30) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_new_store UNIQUE (doc_no, new_store_code)
);

CREATE TABLE document_competitors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    competitor_code VARCHAR(30) NOT NULL REFERENCES competitors(competitor_code),
    name_th VARCHAR(200), branch_th VARCHAR(200), opened_date DATE, closed_date DATE, impact_date DATE,
    detail TEXT, remark TEXT, source_system VARCHAR(30) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_competitor UNIQUE (doc_no, competitor_code)
);

CREATE TABLE document_external_factors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    factor_code VARCHAR(30) NOT NULL REFERENCES external_factors(factor_code),
    date_from DATE, date_to DATE, detail TEXT, remark TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_factor UNIQUE (doc_no, factor_code, date_from),
    CONSTRAINT ck_doc_factor_dates CHECK (date_to IS NULL OR date_from IS NULL OR date_to >= date_from)
);

CREATE TABLE consideration_logs (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    result VARCHAR(100) NOT NULL, result_category VARCHAR(50), detail TEXT,
    consider_by VARCHAR(30) NOT NULL REFERENCES employees(employee_id),
    action_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, request_id VARCHAR(80)
);

CREATE TABLE document_attachments (
    attach_id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    file_name VARCHAR(255) NOT NULL, mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size <= 5242880),
    storage_provider VARCHAR(30) NOT NULL, bucket VARCHAR(120) NOT NULL,
    object_key VARCHAR(500) NOT NULL, sha256 VARCHAR(64) NOT NULL,
    scan_status VARCHAR(20) NOT NULL CHECK (scan_status IN ('PENDING','CLEAN','BLOCKED','FAILED')),
    scanned_at TIMESTAMP, scan_message VARCHAR(500), uploaded_by VARCHAR(30) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, deleted_flag CHAR(1) NOT NULL DEFAULT 'N',
    CONSTRAINT uq_doc_attachment_hash UNIQUE (doc_no, sha256, deleted_flag)
);

CREATE TABLE compensation_histories (
    id BIGSERIAL PRIMARY KEY,
    store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
    ref_doc_no VARCHAR(10) REFERENCES compensation_documents(doc_no),
    submit_account_month CHAR(7) NOT NULL, compensate_amount NUMERIC(14,2) NOT NULL,
    accounting_status VARCHAR(30), external_ref VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_compensation_history UNIQUE (store_code, ref_doc_no, submit_account_month)
);

CREATE TABLE workflow_instances (
    instance_id VARCHAR(40) PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL UNIQUE REFERENCES compensation_documents(doc_no),
    instance_status VARCHAR(20) NOT NULL CHECK (instance_status IN ('ACTIVE','COMPLETED','CANCELLED')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, started_by VARCHAR(30) NOT NULL,
    completed_at TIMESTAMP
);

CREATE TABLE workflow_tasks (
    task_id BIGSERIAL PRIMARY KEY,
    instance_id VARCHAR(40) NOT NULL REFERENCES workflow_instances(instance_id),
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    assignee_employee_id VARCHAR(30) REFERENCES employees(employee_id),
    task_status VARCHAR(20) NOT NULL CHECK (task_status IN ('OPEN','DONE','CANCELLED')),
    action_result TEXT, opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, closed_at TIMESTAMP
);"""),
        ("5.4 Required Indexes, Partial Uniqueness and Purge", """CREATE INDEX idx_document_status_section ON compensation_documents(status_code, current_section_code);
CREATE INDEX idx_document_impact_process ON compensation_documents(impact_process_id);
CREATE INDEX idx_task_doc_status ON workflow_tasks(doc_no, task_status);
CREATE UNIQUE INDEX uq_task_one_open_section ON workflow_tasks(instance_id, section_code) WHERE task_status = 'OPEN';
CREATE INDEX idx_consideration_timeline ON consideration_logs(doc_no, action_datetime DESC);
CREATE INDEX idx_interface_pending ON interface_transactions(data_name, status, sent_at);
CREATE INDEX idx_interface_impact_process ON interface_transactions(impact_process_id);
CREATE INDEX idx_interface_sales_summary ON interface_transactions(sales_summary_id);
CREATE INDEX idx_interface_doc ON interface_transactions(doc_no);
CREATE UNIQUE INDEX uq_job_running ON job_run_histories(job_no, COALESCE(period_key, '')) WHERE status = 'RUNNING';
CREATE INDEX idx_audit_ref ON audit_logs(table_name, ref_key, updated_at DESC);

-- Retention worker: delete only terminal, expired, non-held rows in bounded batches.
WITH purge_candidates AS (
    SELECT id FROM interface_transactions
    WHERE status IN ('ACKED', 'COMPLETED')
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
      AND data_name = ANY(:data_names)
    ORDER BY id
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;"""),
    ]


def validate_schema_sql_contract() -> None:
    ddl = "\n".join(sql for _, sql in database_ddl_sections())
    required_ddl = {
        "menu_permissions": ["can_access BOOLEAN"],
        "user_accounts": ["section_code VARCHAR(2)", "is_active BOOLEAN"],
        "workflow_instances": ["instance_status VARCHAR(20)", "started_by VARCHAR(30) NOT NULL"],
        "system_configs": ["category VARCHAR(80)", "unit VARCHAR(30)", "is_editable BOOLEAN"],
        "sales_transactions": ["txn_date DATE", "window_no SMALLINT", "sales_amount NUMERIC", "sales_diff NUMERIC", "is_outlier BOOLEAN"],
        "consideration_logs": ["result VARCHAR(100)", "detail TEXT", "consider_by VARCHAR(30)", "action_datetime TIMESTAMP"],
        "document_statuses": ["sort_order INTEGER"],
    }
    for table_name, columns in required_ddl.items():
        table_match = re.search(rf"CREATE TABLE {table_name} \((.*?)\n\);", ddl, re.S)
        if not table_match:
            raise ValueError(f"missing DDL table: {table_name}")
        body = table_match.group(1)
        missing = [column for column in columns if column not in body]
        if missing:
            raise ValueError(f"DDL/SQL contract drift in {table_name}: missing {missing}")
    forbidden_ddl = ["can_view BOOLEAN", "password_hash", "secret_flag", "result_code VARCHAR", "considered_at TIMESTAMP"]
    for token in forbidden_ddl:
        if token in ddl:
            raise ValueError(f"obsolete DDL vocabulary remains: {token}")

    api_source = (ROOT / "plan-api.html").read_text(encoding="utf-8")
    required_api = [
        "mp.can_access = TRUE",
        "instance_status, started_at, started_by",
        "version_no = version_no + 1",
        "FROM fgi_impact_processes",
        "id AS tracking_id",
        "acked_at AS receive_date",
    ]
    for token in required_api:
        if token not in api_source:
            raise ValueError(f"API/DDL contract is missing canonical token: {token}")
    forbidden_api = [
        "u.password_hash",
        "INSERT INTO workflow_instances (doc_no, status)",
        "INSERT INTO workflow_instances (instance_id, doc_no, status)",
        "UPDATE fgi_impact_stores SET workflow_generation_status",
        "WHERE tracking_id = :trackingId",
    ]
    for token in forbidden_api:
        if token in api_source:
            raise ValueError(f"obsolete API/DDL vocabulary remains: {token}")


def lldd_database_blocks(all_topics: list[Topic]) -> list[dict[str, Any]]:
    db_ref_topics = [t for t in all_topics if t.db_tables]
    return [
        h(1, "1. Purpose"),
        p("เอกสารนี้เป็น LLDD Database ระดับรวมของ target schema ระบบ SBPGI/SBP Mall ใช้เป็น reference สำหรับ BE API, Batch Job, migration, indexing, transaction และ data dictionary"),
        h(1, "2. Architecture Context"),
        bullets([
            "ระบบใหม่รวม EAI และ K2 เข้าเป็น SBPGI ใช้ฐานข้อมูลเดียวกัน",
            "ไม่มีไฟล์ BPM06001O/BPM06002O/BPM06003O ภายในเพื่อส่งเข้า K2; ใช้ FK จาก compensation_documents ไป impact_process แทน",
            "Workflow engine ภายในใช้ workflow_instances และ workflow_tasks แทน K2 engine ภายนอก",
            "ตัดขั้นบัญชี 04/05 ตาม SDD v7.5; workflow ใช้ section 06/08/01/02/03",
            "มาตรฐานชื่อ table/column เป็น English lower_snake_case",
            "ตาราง job_configs และ job_run_histories เป็น schema reference สำหรับ BE/dev; ไม่ใช่ scope ให้ FE Batch Monitor ทำ tab Database ที่ใช้",
        ]),
        h(1, "2.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], [
            ["Input", "Target table catalog, data zones, primary keys, foreign-key relationships, migration assumptions, index needs, and transaction boundaries."],
            ["Progress", "Use the data spine impact_process_id -> doc_no -> instance_id/task_id to implement APIs/jobs, then validate referential integrity, idempotency keys, and audit writes."],
            ["Output", "Data dictionary and implementation reference for schema creation, migration, indexing, transaction handling, and test data preparation."],
        ]),
        h(1, "3. Data Zones and Spine"),
        table(
            ["Zone", "Scope", "Core tables", "Owner usage"],
            [
                ["A", "FGI/FCS Impact Pipeline and external interfaces", "fgi_impact_processes, fgi_impact_stores, sales, interface_transactions", "Batch Jobs 1-7, IAS/ALLMAP/QSSI/STA tracking"],
                ["B", "K2 Document and internal workflow", "compensation_documents, document_* tables, workflow_instances, workflow_tasks", "Document APIs, workflow actions, FE detail/list/report"],
                ["C", "Shared master/config/RBAC/audit", "stores, roles, menus, configs, jobs, email templates, audit", "Lookup, admin, job monitor, notification"],
            ],
        ),
        table(
            ["Order", "Key", "Meaning", "Used by"],
            [
                [1, "impact_process_id", "หนึ่งร้านถูกกระทบ + หนึ่งงวด", "FGI/FCS pipeline, Job 8/8b"],
                [2, "doc_no", "เอกสาร YYYY/xxxxx ปี พ.ศ.", "Document APIs, reports, attachments"],
                [3, "instance_id", "workflow instance ต่อเอกสาร", "Workflow engine"],
                [4, "task_id", "งานต่อ section/assignee", "Inbox/current task guard"],
                [5, "employee_id / role_code", "identity/RBAC", "menu, audit, assignment"],
            ],
        ),
        h(1, "4. Data Dictionary"),
        table(["Zone", "Table", "PK", "FK / relationship", "Role"], database_table_catalog()),
        h(2, "4.1 Canonical Column Contract"),
        table(
            ["Table", "Canonical columns used by DDL and SQL", "Rejected legacy vocabulary"],
            [
                ["menu_permissions", "role_code, menu_code, can_access", "can_view/can_create/can_update/can_delete"],
                ["user_accounts", "employee_id, role_code, section_code, username, is_active", "password_hash/account_status"],
                ["workflow_instances", "instance_id, doc_no, instance_status, started_at, started_by", "status or auto-generated instance id"],
                ["system_configs", "config_key, category, config_value, value_type, unit, description, is_editable", "secret_flag or inline secrets"],
                ["sales_transactions", "txn_date, window_no, sales_amount, sales_diff, is_outlier", "sale_date/window_code/net_sales"],
                ["consideration_logs", "result, result_category, detail, consider_by, action_datetime", "result_code/comment/considered_by/considered_at"],
                ["interface_transactions", "id, acked_at", "tracking_id/receive_date (API aliases only)"],
                ["fgi_impact_processes", "workflow_generation_status", "duplicate workflow flag on fgi_impact_stores"],
            ],
        ),
        h(1, "5. Executable DDL — 34 Tables"),
        p("ส่วนนี้เป็น PostgreSQL DDL ครบทุกตารางใน Data Dictionary เรียงตาม dependency พร้อม PK, typed FK, unique/check constraint และ index ที่จำเป็น สามารถใช้เป็น migration baseline ได้โดยไม่ต้องเดา column เพิ่มเติม"),
        *[
            block
            for section_title, sql_text in database_ddl_sections()
            for block in (h(2, section_title), code(sql_text, "sql"))
        ],
        h(1, "6. Index and Constraint Plan"),
        table(
            ["Table", "Index / constraint", "Reason"],
            [
                ["compensation_documents", "UNIQUE (be_year, running_no), UNIQUE(source, impacted_store_code, impact_month, new_store_code, round_no), INDEX(status_code,current_section_code), INDEX(impact_process_id)", "docNo uniqueness, duplicate guard, list/inbox/report, pipeline trace"],
                ["workflow_tasks", "INDEX(doc_no, task_status), INDEX(section_code, task_status), UNIQUE(instance_id, section_code, task_status) filtered OPEN", "current task guard and inbox"],
                ["document_new_stores", "INDEX(doc_no), CHECK compensate_percent between 0 and 100", "detail load and allocation validation"],
                ["consideration_logs", "INDEX(doc_no, action_datetime DESC), INDEX(result_category)", "timeline/report result filter"],
                ["document_attachments", "INDEX(doc_no), INDEX(scan_status), UNIQUE(sha256, doc_no, deleted_flag)", "attachment list/download/security"],
                ["job_run_histories", "INDEX(job_no, period, status), UNIQUE(job_no, period) filtered RUNNING", "manual run concurrency guard"],
                ["audit_logs", "INDEX(table_name, ref_key), INDEX(updated_at DESC)", "admin history search"],
                ["interface_transactions", "INDEX(data_name,status), INDEX(impact_process_id), INDEX(doc_no)", "tracking and pending ACK"],
            ],
        ),
        h(1, "7. Transaction Rules"),
        table(
            ["Use case", "Transaction boundary", "Rollback rule"],
            [
                ["Create document", "docNo sequence lock + compensation_documents + workflow instance/task + audit", "any fail rollback all; no partial document"],
                ["Submit action", "lock current OPEN task + insert consideration_logs + close/open task + update document", "duplicate/current task conflict returns 409"],
                ["Attachment upload", "metadata insert only after storage write and AV clean; objectKey never exposed", "storage/scan fail leaves no CLEAN metadata"],
                ["Job 4 IAS request", "durable file (fsync + atomic rename + checksum) ก่อน transaction W→P + outbox READY", "file fail คง W; DB fail rollback W→P/outbox; SFTP fail retry transaction เดิม"],
                ["Interface ACK/purge", "ACK compare-and-set บน transaction เดิม; purge เฉพาะ terminal + purge_after + non-held", "pending/failed/unacked/legal-hold ห้ามลบ"],
                ["Job manual run", "acquire run lock + job_run_histories RUNNING before processing", "fatal fail marks run FAILED and keeps record-level rejects"],
                ["Master/config/email mutation", "validate reason + update entity + insert audit_logs", "audit fail rollback mutation"],
            ],
        ),
        h(1, "8. Seed Data"),
        table(
            ["Domain", "Required seed"],
            [
                ["workflow_sections", "06, 08, 01, 02, 03 only"],
                ["document_statuses", "6 statuses: 5 waiting statuses + completed"],
                ["roles", "00, 01, 02, 03, 04, 05, 06, 10 per RBAC model"],
                ["email_templates", "EM-01..EM-08"],
                ["system_configs", "impact radius 1/2 km, workflow.avp_amount_threshold=100000, sales data threshold=60, growth rate threshold=-10"],
                ["job_configs", "Jobs 1-10 and 8b with enabled/schedule/default params as schema reference"],
            ],
        ),
        h(1, "9. Migration and Verification Checklist"),
        table(
            ["Area", "Check"],
            [
                ["Naming", "all new tables/columns lower_snake_case"],
                ["Leading zero", "store_code/new_store_code stored as VARCHAR(5), never numeric"],
                ["docNo", "be_year/running_no/doc_no generated in DB transaction; concurrency test 20 parallel requests"],
                ["Workflow", "no active 04/05 accounting sections/statuses"],
                ["Security", "no secrets in system_configs/job_configs; storage objectKey not returned to FE"],
                ["External interface", "credential/certificate/private key อยู่ Secret Manager ผ่าน secretRef; TLS verify-full หรือ SFTP strict known_hosts; ทดสอบ rotation และ invalid certificate/host key"],
                ["Tracking retention", "backfill typed FK/purge_after, validate FK, dry-run count แล้ว purge เฉพาะ ACKED/COMPLETED เป็น batch; reconcile count ก่อน/หลัง"],
                ["Data integrity", "FK/check constraints enabled before SIT; reject legacy invalid enum values"],
                ["Performance", "list/report/inbox queries explain plan uses indexes above"],
            ],
        ),
        h(1, "10. Related LLDD"),
        table(["Document", "DB usage"], [[Path(t.file).name, ", ".join(f"{row[0]}({row[1]})" for row in t.db_tables[:4])] for t in db_ref_topics]),
    ]


def reference_doc_links() -> list[dict[str, str]]:
    return [
        {
            "id": "LLDD-API",
            "title": "LLDD API - REST API and Integration Contract",
            "owner": "BE/FE",
            "scope": "REST conventions, endpoint catalog, request lifecycle, SQL/repository pattern",
            "base": "LLDD-API",
        },
        {
            "id": "LLDD-Database",
            "title": "LLDD Database - Target Schema and Data Dictionary",
            "owner": "BE/DB",
            "scope": "34-table target schema, data zones/spine, DDL reference, indexes, transaction rules, seed data",
            "base": "LLDD-Database",
        },
    ]


def render_reference_doc_rows() -> str:
    rows = []
    for doc in reference_doc_links():
        base = doc["base"]
        rows.append(
            "<tr>"
            f"<td><strong>{escape(doc['id'])}</strong><span>{escape(doc['title'])}</span></td>"
            f"<td>{escape(doc['owner'])}</td>"
            f"<td>{escape(doc['scope'])}</td>"
            "<td class=\"links\">"
            f"<a href=\"pdf/{escape(base)}.pdf\">PDF</a>"
            f"<a href=\"word/{escape(base)}.docx\">DOCX</a>"
            "</td>"
            "</tr>"
        )
    return "\n".join(rows)


def topic_links(topic: Topic, prefix: str = "") -> dict[str, str]:
    base = Path(topic.file)
    return {"pdf": f"{prefix}pdf/{base}.pdf", "docx": f"{prefix}word/{base}.docx"}


def doc_id(topic: Topic) -> str:
    return Path(topic.file).name.replace("LLDD-FE-", "FE-").replace("LLDD-BE-", "BE-")


def grouped_topics(all_topics: list[Topic]) -> dict[str, list[Topic]]:
    return {
        "fe_core": [t for t in all_topics if t.track == "FE" and t.file.startswith("FE/") and "Document-Detail-Role" not in t.file],
        "fe_roles": [t for t in all_topics if t.file.startswith("FE/LLDD-FE-Document-Detail-Role")],
        "be_api": [t for t in all_topics if t.track == "BE" and t.file.startswith("BE/LLDD-BE-API")],
        "be_ops": [t for t in all_topics if t.track == "BE" and t.file == "BE/LLDD-BE-Job-Batch-Email-SRM"],
        "be_jobs": [t for t in all_topics if "/Jobs/" in t.file],
    }


def render_doc_rows(topics_list: list[Topic]) -> str:
    rows = []
    for topic in topics_list:
        links = topic_links(topic)
        rows.append(
            "<tr>"
            f"<td><strong>{escape(doc_id(topic))}</strong><span>{escape(topic.title)}</span></td>"
            f"<td>{escape(topic.track)}</td>"
            f"<td>{escape(topic.owner)}</td>"
            f"<td>{estimate_html(topic)}</td>"
            "<td class=\"links\">"
            f"<a href=\"{escape(links['pdf'])}\">PDF</a>"
            f"<a href=\"{escape(links['docx'])}\">DOCX</a>"
            "</td>"
            "</tr>"
        )
    return "\n".join(rows)


def estimate_html(topic: Topic) -> str:
    if is_document_detail_role_doc(topic.file):
        return "included<br><small>in Document Detail</small>"
    return f"{topic.hours}h"


def estimate_md(topic: Topic) -> str:
    if is_document_detail_role_doc(topic.file):
        return "included in Document Detail"
    return f"{topic.hours}h"


def build_document_portal(all_topics: list[Topic]) -> None:
    groups = grouped_topics(all_topics)
    total_hours = sum(t.hours for t in all_topics if not is_document_detail_role_doc(t.file))
    main_pdf = "pdf/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.pdf"
    html = f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LLDD Document Portal - SBP Income Guarantee</title>
  <style>
    :root {{ --ink:#1b2733; --muted:#66717f; --line:#d7e0ea; --head:#eef4fa; --accent:#1e6bb8; --soft:#f7fafc; }}
    body {{ margin:0; font-family: Arial, Tahoma, sans-serif; color:var(--ink); background:#fff; }}
    header {{ padding:28px 36px 22px; border-bottom:1px solid var(--line); background:linear-gradient(180deg,#f8fbff,#fff); }}
    h1 {{ margin:0 0 8px; font-size:28px; color:#0b2545; }}
    h2 {{ margin:28px 0 10px; font-size:20px; color:#174c7f; }}
    p {{ margin:6px 0; color:var(--muted); line-height:1.55; }}
    main {{ padding:22px 36px 42px; max-width:1280px; }}
    .quick {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:12px; margin-top:18px; }}
    .quick a {{ display:block; padding:14px; border:1px solid var(--line); border-radius:8px; text-decoration:none; color:var(--ink); background:#fff; }}
    .quick strong {{ display:block; color:var(--accent); margin-bottom:4px; }}
    .summary {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:10px; margin:18px 0 8px; }}
    .metric {{ border:1px solid var(--line); border-radius:8px; padding:12px; background:var(--soft); }}
    .metric b {{ display:block; font-size:22px; color:#0b2545; }}
    table {{ border-collapse:collapse; width:100%; table-layout:fixed; margin-bottom:18px; }}
    th, td {{ border:1px solid var(--line); padding:9px 10px; vertical-align:top; font-size:14px; }}
    th {{ text-align:left; background:var(--head); color:#24384b; }}
    td strong {{ display:block; color:#0b2545; }}
    td span {{ display:block; color:var(--muted); margin-top:3px; }}
    small {{ color:var(--muted); }}
    .links a {{ display:inline-block; margin:0 6px 6px 0; padding:5px 8px; border:1px solid #b9cbe0; border-radius:6px; text-decoration:none; color:#155c9f; background:#fff; }}
    .note {{ padding:12px 14px; border-left:4px solid var(--accent); background:#f3f8fd; color:#31465a; }}
    @media (max-width: 860px) {{ header, main {{ padding-left:18px; padding-right:18px; }} .quick, .summary {{ grid-template-columns:1fr; }} table {{ table-layout:auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>LLDD Document Portal</h1>
    <p>SBP Mall - ระบบประกันรายได้ | Phase 4.3 Operating Management</p>
    <div class="summary">
      <div class="metric"><b>{len(all_topics) + len(reference_doc_links())}</b><small>LLDD documents</small></div>
      <div class="metric"><b>{len(groups['fe_core']) + len(groups['fe_roles'])}</b><small>FE documents</small></div>
      <div class="metric"><b>{len(groups['be_api']) + len(groups['be_ops']) + len(groups['be_jobs'])}</b><small>BE/API/Job documents</small></div>
      <div class="metric"><b>{total_hours}</b><small>estimated hours</small></div>
    </div>
    <div class="quick">
      <a href="{main_pdf}"><strong>Start here</strong>Main LLDD index PDF</a>
      <a href="pdf/LLDD-API.pdf"><strong>API LLDD</strong>REST contract and endpoint catalog</a>
      <a href="pdf/LLDD-Database.pdf"><strong>Database LLDD</strong>Target schema and data dictionary</a>
      <a href="#document-detail-roles"><strong>Document Detail Roles</strong>5 role-specific FE specs</a>
      <a href="#be-api"><strong>BE API</strong>Common and document APIs</a>
      <a href="#be-jobs"><strong>Batch Jobs</strong>Job 1-10 and 8b specs</a>
    </div>
  </header>
  <main>
    <p class="note">วิธีใช้: เอกสาร PDF อยู่ในโฟลเดอร์ pdf, Markdown อยู่ในโฟลเดอร์ md และเอกสาร Word อยู่ในโฟลเดอร์ word โดยแต่ละโฟลเดอร์คงโครงสร้าง FE/BE/Jobs เหมือนกัน</p>
    <p class="note">Batch Monitor scope: LLDD-FE-Batch-Monitor ทำจริงเฉพาะ 2 tab คือ แบบฟอร์มพารามิเตอร์ และประวัติการรัน; flowchart การทำงานและฐานข้อมูลที่ใช้เป็น reference สำหรับ dev เท่านั้น ไม่ใช่ FE deliverable ของหน้านี้</p>
    <p class="note">แผนทีม 6 คน: {escape(FE_OWNER_KITTISAK)}, {escape(FE_OWNER_PEERAKORN)}, {escape(FE_OWNER)} (FE); {escape(BE_OWNER_BUTSABA)}, {escape(BE_OWNER)}, และ {escape(BANK_BE_OWNER)} (BE) ระหว่าง {fmt_date(LLDD_START_DATE)} - {fmt_date(LLDD_END_DATE)} โดย 1 week = {WORKDAYS_PER_WEEK} วัน, 1 วัน = {HOURS_PER_DAY} ชั่วโมง และภาระงานรายคนมากกว่า 3 แต่ไม่เกิน 4.5 work weeks</p>

    <h2 id="reference-docs">Reference Design Documents</h2>
    <table><thead><tr><th>Document</th><th>Owner</th><th>Scope</th><th>Open</th></tr></thead><tbody>
{render_reference_doc_rows()}
    </tbody></table>

    <h2 id="fe-core">FE Core Documents</h2>
    <table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['fe_core'])}
    </tbody></table>

    <h2 id="document-detail-roles">Document Detail Role Pack</h2>
    <p>เอกสารชุดนี้แยกจาก LLDD-FE-Document-Detail เพื่อให้อ่านง่ายตาม role ที่ login จริง</p>
    <table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['fe_roles'])}
    </tbody></table>

    <h2 id="be-api">BE API Documents</h2>
    <table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['be_api'] + groups['be_ops'])}
    </tbody></table>

    <h2 id="be-jobs">BE Batch Job Documents</h2>
    <table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['be_jobs'])}
    </tbody></table>
  </main>
</body>
</html>
"""
    (OUT / "index.html").write_text(html, encoding="utf-8")

    def md_rows(topics_list: list[Topic]) -> list[str]:
        rows = ["| Document | Owner | Estimate | PDF | DOCX |", "| --- | --- | --- | --- | --- |"]
        for topic in topics_list:
            links = topic_links(topic, "../")
            rows.append(
                f"| {doc_id(topic)} | {topic.owner} | {estimate_md(topic)} | "
                f"[PDF]({links['pdf']}) | [DOCX]({links['docx']}) |"
            )
        return rows

    lines = [
        "# LLDD Document Portal",
        "",
        "เปิดหน้า portal ใน browser หรือใช้รายการลิงก์ด้านล่าง.",
        "",
        f"- Main index: [PDF](../{main_pdf})",
        f"- Documents: {len(all_topics) + len(reference_doc_links())}",
        f"- Total estimate: {total_hours} hours",
        "- Batch Monitor scope: `LLDD-FE-Batch-Monitor` ทำจริงเฉพาะ 2 tab คือ `แบบฟอร์มพารามิเตอร์` และ `ประวัติการรัน`; flowchart/database เป็น reference สำหรับ dev เท่านั้น",
        f"- Reschedule window: {fmt_date(LLDD_START_DATE)} - {fmt_date(LLDD_END_DATE)} with 6-person team `{FE_OWNER_KITTISAK}`, `{FE_OWNER_PEERAKORN}`, `{FE_OWNER}` (FE) and `{BE_OWNER_BUTSABA}`, `{BE_OWNER}`, `{BANK_BE_OWNER}` (BE only)",
        f"- Working-time rule: 1 week = {WORKDAYS_PER_WEEK} days, 1 day = {HOURS_PER_DAY} hours ({HOURS_PER_WEEK} hours/week); every developer is allocated more than 3 and no more than 4.5 work weeks",
        "",
        "## Reference Design Documents",
        "",
        "| Document | Owner | Scope | PDF | DOCX |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {doc['id']} | {doc['owner']} | {doc['scope']} | [PDF](../pdf/{doc['base']}.pdf) | [DOCX](../word/{doc['base']}.docx) |"
            for doc in reference_doc_links()
        ],
        "",
        "## FE Core Documents",
        "",
        *md_rows(groups["fe_core"]),
        "",
        "## Document Detail Role Pack",
        "",
        *md_rows(groups["fe_roles"]),
        "",
        "## BE API Documents",
        "",
        *md_rows(groups["be_api"] + groups["be_ops"]),
        "",
        "## BE Batch Job Documents",
        "",
        *md_rows(groups["be_jobs"]),
        "",
    ]
    md_root = OUT / FORMAT_DIRS["md"]
    md_root.mkdir(parents=True, exist_ok=True)
    (md_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_formats(value: str) -> set[str]:
    formats = {item.strip().lower() for item in value.split(",") if item.strip()}
    allowed = {"md", "docx", "pdf"}
    unknown = formats - allowed
    if not formats or unknown:
        raise argparse.ArgumentTypeError(f"formats must be a comma-separated subset of {sorted(allowed)}")
    return formats


def build_manifest() -> dict[str, list[str]]:
    return {
        "generated": [
            str(p.relative_to(ROOT))
            for p in sorted(OUT.rglob("*"))
            if p.suffix.lower() in {".html", ".md", ".docx", ".pdf", ".png"}
        ]
    }


def write_manifest() -> dict[str, list[str]]:
    manifest = build_manifest()
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LLDD deliverables")
    parser.add_argument("--formats", type=parse_formats, default={"md", "docx", "pdf"}, help="comma-separated: md,docx,pdf")
    args = parser.parse_args()
    formats: set[str] = args.formats
    OUT.mkdir(exist_ok=True)
    manifest_path = OUT / "manifest.json"
    if formats == {"md", "docx", "pdf"} and manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("generated", [])
            for rel in previous:
                target = ROOT / rel
                if target.is_file() and target.is_relative_to(OUT):
                    target.unlink()
        except Exception:
            pass
    validate_schema_sql_contract()
    all_topics = topics()
    render_all("LLDD Main Index - Phase 4.3 SBP Operating Management ประกันรายได้", main_doc_blocks(all_topics), OUT / "LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management", formats)
    render_all("LLDD API - REST API and Integration Contract", lldd_api_blocks(all_topics), OUT / "LLDD-API", formats)
    render_all("LLDD Database - Target Schema and Data Dictionary", lldd_database_blocks(all_topics), OUT / "LLDD-Database", formats)
    for topic in all_topics:
        render_all(topic.title, topic_blocks(topic), OUT / topic.file, formats)
    if formats == {"md", "docx", "pdf"}:
        build_document_portal(all_topics)
    manifest = build_manifest()
    if formats == {"md", "docx", "pdf"}:
        manifest = write_manifest()
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
