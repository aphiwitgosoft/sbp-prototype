from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
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

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_integrated_srs import target_job  # noqa: E402
from lldd_skeleton_be import be_skeleton_blocks  # noqa: E402
from lldd_skeleton_fe import fe_skeleton_blocks  # noqa: E402
from lldd_skeleton_job import job_skeleton_blocks  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "LLDD"
LEGACY_JAVA_ROOT = ROOT.parent / "fcsJar"
FORMAT_DIRS = {"md": "md", "docx": "word", "pdf": "pdf"}
IMG = ROOT / "output/srs/screenshots/full"
SLICE = ROOT / "output/srs/screenshots/slices"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
# 2026-08-07: re-baseline วันเริ่มเป็นจันทร์ 10/08/2026 (วันเริ่มเดิม 29/07/2026 ผ่านมาแล้ว
# ทำให้แผนมี End Date เป็นอดีตตั้งแต่วันส่งมอบ) · เส้นวิกฤตคือ Aphiwit 130 ชม. = 22 วันทำงาน -> 08/09/2026
LLDD_START_DATE = date(2026, 8, 10)
# 2026-08-10: เลิกใช้เป็น "กรอบบังคับ" — วันจบมาจาก planned_finish_date() ที่คำนวณจาก dependency จริง
LLDD_END_DATE = date(2026, 9, 8)  # คงไว้เป็นวันเป้าหมายเดิมเพื่อเทียบเท่านั้น
WORKDAYS_PER_WEEK = 5
# 2026-08-25: กรอบส่งมอบ "จบใน 4 สัปดาห์ · 5 วัน/สัปดาห์ · 8.5 ชม./วัน"
#             = 170 ชม./คน · ทีม 6 คน = 1,020 ชม. · ยอดงานคำนวณสดจาก _grand_total_hours() (ห้าม hardcode)
#             ชั่วโมงงานรวมไม่เปลี่ยน — เปลี่ยนแค่ตัวหารที่แปลงชั่วโมงเป็นวัน
HOURS_PER_DAY = 8.5
HOURS_PER_WEEK = WORKDAYS_PER_WEEK * HOURS_PER_DAY
# 2026-08-11: ถอดกรอบ work-week ออก — เดิมบังคับให้ทุกคนอยู่ระหว่าง >3 ถึง <=4.5 สัปดาห์
#             ซึ่งทำให้ต้องปรับชั่วโมงให้ "พอดีกรอบ" แทนที่จะประเมินตามเนื้องานจริง
MIN_WORK_WEEKS_EXCLUSIVE = 0.0   # ไม่บังคับแล้ว
MAX_WORK_WEEKS = 0.0             # ไม่บังคับแล้ว
FE_OWNER_KITTISAK = "Kittisak <New> Kaeowika"
# 2026-08-07: Peerakorn ย้ายจากสาย FE ไปสาย BE (รับ Attachment / Report-and-Master-Data /
# Job-Batch-SRM / Job 5,7,9,10) เพื่อเปิดที่ให้ Aphiwit รับ Database-Structure + Data-Migration
BE_OWNER_PEERAKORN = "Peerakorn <Pete> Sakunkaewphithak"
FE_OWNER = "Chidchanok <lin> Saengamnat"
BANK_BE_OWNER = "Aphiwit <Bank> Khammoon"
BE_OWNER = "Tunyatorn <Vava> Kiatkongphongsa"
BE_OWNER_BUTSABA = "Butsaba <But> Podamrong"
ATTACHMENT_ALLOWED_EXTENSIONS = "vsd, dwg, afp, pdf, mda, zip, wav, mp3, gif, jpg, tif, tiff, htm, html, txt, xml, mpg, mov, ivs, doc, docx, xls, xlsx, pps, ppt, pot, csv"
# 2026-08-07: ปรับชั่วโมง/เจ้าของใหม่ · 2026-08-11: รวม 703 ชม. (ถอด buffer ออก)
# Job 8b -> Tunyatorn (job เดียวที่เรียก workflow engine · ถือ Workflow-Engine-Definition อยู่แล้ว)
# Job 5/7/9/10 -> Peerakorn (งาน interface ที่พึ่งพา job อื่นน้อยที่สุด)
# 2026-09-02 — ปรับตามของที่ reuse ได้จริงบน SBP/srm-sps-spsap-sop-sgi-batch (เดิมตั้งบน store-backend
#   ที่ต้องสร้าง runner/scheduler/cli/notifier เองทั้งชุด) · หักลบทั้ง "สิ่งที่ไม่ต้องทำแล้ว" และ
#   "งานใหม่ที่เพิ่งรู้ว่าต้องทำ" (join ข้าม schema · INPUT DTO + validation · outbox บน publisher ที่ไม่มี confirm)
#   ที่มาของ delta: SBP/srm-sps-spsap-sop-sgi-batch.md ข้อ 0 และ 9
JOB_ESTIMATES: dict[str, int] = {
    "2": 15,    # +1 : reuse dispatcher/log/integration_log (-1) · แต่ต้อง join ข้าม schema (mas_store/fr_store/juristic)
                #      และคุม lifecycle 2 สถานะแยกกัน verify_status + sales_request_status (+2)
    "3": 9,     # -1 : reuse dispatcher/log — งานเป็น import ตรง ๆ ไม่มี infra เฉพาะ
    "4": 13,    # -1 : reuse S3Service + dispatcher (-3) · เพิ่ม join mas_store 2 ด้าน + INPUT args ที่ legacy ไม่มี (+2)
    "5": 13,    # -3 : reuse S3Service + decodeThaiFileContent (WINDOWS-874) + dispatcher (-4) · เพิ่ม INPUT args (+1)
    "6": 24,    # -2 : reuse publishMessage + envelope dataType/dataName + dispatcher (-4)
                #      · แต่ publishMessage เป็น fire-and-forget ไม่มี confirm — outbox ยังต้องเขียนเพิ่ม (+2)
    "7": 9,     # -1 : reuse dispatcher/log
    "8": 17,    # -1 : reuse dispatcher/log
    "8b": 21,   # -1 : reuse dispatcher/log · @srm/glb-workflow ติดตั้งไว้แล้วใน repo (ยังไม่มี call site)
    "9": 10,    # -1 : reuse dispatcher/log
    "10": 6,    # -2 : reuse email-lib + dispatcher — งานนี้เกือบทั้งหมดคือ query + ส่งเมล
    # ── 2 job ใหม่ (2026-09-02) — ปิดช่องว่างที่ตรวจเจอตอนเทียบ LLDD กับ Java/สเปก STA ──
    "11": 12,   # ConsumeStaCompensate — ของใหม่ทั้งหมด ไม่มีคลาสเดิม · repo มีแต่ publisher ไม่มี consumer ให้ลอก
                #   งาน: envelope validation + ดาวน์โหลดไฟล์เมื่อ dataType=S3 + กันซ้ำด้วย uq_interface_business
                #   (มติ 2026-09-12: job consume คิวเองใน sop-sgi-batch — ตัด repo store-consumer ออกจากขอบเขต)
    "12": 10,   # NotifyPendingWork — มีคลาสเดิม (SendMailReport/MailReportService) ให้ยึดกติกา
                #   งาน: อ่านงานค้างจาก engine แทน K2 SmartObject + bucket 3 ช่วง + จัดกลุ่มตามโซน + email-lib
}

# 2026-08-25 (รอบ 3): Bank รับผิดชอบ migration DB + **batch job ทั้งหมด** + สร้าง workflow (นิยาม)
#   จึงไม่มี override ใด ๆ — ทุก job ตกเป็นของ BANK_BE_OWNER ตาม default
#   ⚠️ ผลรวมของ Bank = 296 ชม. เกินเพดาน 4 สัปดาห์ (170 ชม.) อยู่ 126 ชม. — ดูหมายเหตุใน README
JOB_OWNER_OVERRIDES: dict[str, str] = {}

HIGH_LEVEL_ESTIMATES: dict[str, int] = {
    "FE/LLDD-FE-Integration-Contracts": 16,
    "FE/LLDD-FE-Foundation": 28,
    "FE/LLDD-FE-Document-Lists": 28,
    "FE/LLDD-FE-Create-Document": 6,
    "FE/LLDD-FE-Document-Detail": 60,
    "FE/LLDD-FE-Report": 20,
    "FE/LLDD-FE-Master-Data": 16,
    "FE/LLDD-FE-Testing-Delivery": 12,
    "BE/LLDD-BE-API-Common-Contracts": 18,
    "BE/LLDD-BE-Integration-SBP-Platform": 20,
    "BE/LLDD-BE-API-Document-List-Search": 20,
    "BE/LLDD-BE-API-Document-Create-Update": 24,
    "BE/LLDD-BE-API-Document-Detail-Aggregate": 24,
    "BE/LLDD-BE-API-Document-Workflow-Actions": 28,
    "BE/LLDD-BE-API-Workflow-Instances": 24,
    "BE/LLDD-BE-Workflow-Engine-Definition": 24,   # +8 (2026-08-11): ปิดชื่อ function ที่ขัดกัน 3 ชุด · DP-2 ไม่มี PK/index · ออกแบบลำดับขั้นใหม่เพราะ workflow_state ไม่มี seq · ตัดสิน workflow_part_display ที่ทับซ้อน data-editrole
    "BE/LLDD-BE-API-Attachment-Sales-Timeline": 26,
    "BE/LLDD-BE-API-Lookup": 10,
    "BE/LLDD-BE-API-Report-and-Master-Data": 30,   # +3 (2026-08-11): ต้อง join store -> fr_store -> juristic ของระบบเดิม และดึงประเภทร้าน/ภาคจาก common_code + store/all-regions
    # 2026-09-02: -6 — ตัดงานสร้าง runner/scheduler/cli/job-failure notifier ทั้งชุดออก (มีใน sop-sgi-batch แล้ว)
    #   เหลือเฉพาะต่อ email-lib ของ SGI + endpoint interface tracking/pending-ack (ตัด sta/ack 2026-09-08)
    "BE/LLDD-BE-Job-Batch-Email-SRM": 8,
    "BE/LLDD-BE-Database-Structure": 31,   # +3 (2026-08-21): DDL ตาราง sgi_fgi_impact_compensations + 5 คอลัมน์รอบชดเชย + index/UK (F8+F1)
    "BE/LLDD-BE-Data-Migration-Cutover": 43,   # +3 (2026-08-21): map/migrate FGI_IMPACT_STORE_COMPENSATE และคอลัมน์รอบชดเชยจาก FGI_IMPACT_STORE_ON_PROCESS · +6 (2026-08-11): งานเพิ่มจาก master จริง — SectionLimitCost 100,000 ต้อง seed ใหม่ · DecisionCode ที่ Excel แปลงเป็นวันที่ · สถานะเดิม 10 ค่า map เหลือ 6 · SectionCode เติมศูนย์ · doc_no เป็น UNIQUE ตาม DP-1
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
    base_hours: int = 0     # = hours (คงไว้เพื่อความเข้ากันได้ — ระบบ buffer ถอดออก 2026-08-11)
    buffer: float = 0.0     # ไม่ใช้แล้ว


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


_NAMED_PARAM = re.compile(r"(?<![:\w]):([a-zA-Z_]\w*)")


def to_positional_sql(sql: str) -> str:
    """แปลง named parameter `:name` เป็น positional `$n` ที่ store-backend รันได้จริง

    ⚠️ เหตุผล (ยืนยันจากโค้ดจริง 2026-09-04): `dataSource.query(sql, params)` ของ store-backend
    รับเฉพาะ `$1..$n` · `:name` ใช้ได้เฉพาะใน QueryBuilder (`.andWhere("x = :id", {id})`) เท่านั้น
    เอกสารเดิมพิมพ์ `:name` ในบล็อก SQL ดิบ แล้วเตือนให้ผู้อ่านไปแปลงเอง — คัดลอกไปรันตรง ๆ ไม่ได้
    ตอนนี้เอกสารพิมพ์ `$n /* ชื่อ */` ให้เลย พร้อมบรรทัดลำดับ bind ที่หัวบล็อก

    ชื่อเดิมที่ซ้ำจะได้เลขเดิม (bind ครั้งเดียว) · ข้ามข้อความในคอมเมนต์ `--` และใน string literal
    """
    order: list[str] = []
    out: list[str] = []
    for line in sql.split("\n"):
        head, sep, tail = line.partition("--")          # ไม่แตะข้อความหลัง --
        pieces = head.split("'")                        # index คู่ = นอก string literal
        for i, piece in enumerate(pieces):
            if i % 2:
                continue

            def repl(m: "re.Match[str]") -> str:
                name = m.group(1)
                if name not in order:
                    order.append(name)
                return f"${order.index(name) + 1} /* {name} */"

            pieces[i] = _NAMED_PARAM.sub(repl, piece)
        out.append("'".join(pieces) + sep + tail)
    body = "\n".join(out)
    if not order:
        return sql
    binding = "-- bind ตามลำดับ: " + " · ".join(f"${i + 1}={n}" for i, n in enumerate(order))
    return binding + "\n" + body


def code(text: str, lang: str = "") -> dict[str, Any]:
    if lang == "sql":
        text = to_positional_sql(text)
    return {"type": "code", "text": text, "lang": lang}


def payload(title: str, text: str) -> dict[str, Any]:
    return {"type": "payload", "title": title, "text": text}


def pagebreak() -> dict[str, Any]:
    return {"type": "pagebreak"}


LEGACY_JOB_SOURCES: dict[str, dict[str, Any]] = {
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
            ["fcsJar/src/th/co/gosoft/fgi/controller/ImportController.java", "483-598", "Validate params, skip duplicates, query source, chunk insert sgi_competitors."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportJdbc.java", "200-241", "Count existing period, query COMPETITOR_IMPACT_VIEW, insert FGI_IMPACT_COMPETITOR."],
        ],
    },
    "4": {
        "input": "FGI_IMPACT_STORE_SALES rows waiting for IAS sales data and EAI S3 bucket/prefix parameters.",
        "progress": "query eligible stores, write outbound IAS request file, upload to EAI S3 outbound prefix, keep local backup, record success/failure and notification.",
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
        "input": "New-store compensation rows linked to active impact-process records (writes to sgi_document_new_stores directly; no export file).",
        "progress": "query eligible new-store rows, filter process errors, write outbound new-store payload, insert confirm-receive rows, upload/export, backup, notify.",
        "output": "New-store sync payload/output and confirm-receive rows keyed by NEW_STORE_INFO_ID/month/year.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/ExportOpenStore.java", "1-22", "Legacy main entrypoint; constant job name is ExportNewStoreToBPM."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ExportController.java", "404-516, 893-961", "Query new stores, create payload content, upload, backup, notification."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1558-1594", "Query new-store rows eligible for export."],
        ],
    },
    "11": {
        "input": "envelope ของข้อความ `sta_update_compensate` ที่ **job consume เองจากคิว** (มติ 2026-09-12 · job เป็นผู้ bind คิวบน exchange `sgi.interface` · มติ 2026-09-08) — ยอดเงินประกันรายได้รายงวดจากระบบ STA",
        "progress": "อ่าน `INPUT`, ตรวจ envelope (`dataName` ต้องเป็น sta_update_compensate), ถ้า `dataType = S3` ให้ดาวน์โหลดไฟล์จาก `urls` เอง, กันซ้ำด้วย `uq_interface_business`, อัปเดตยอดชดเชยของงวดใน transaction เดียว — **ไม่ต่อ RabbitMQ เอง ไม่ ack เอง** (consumer จัดการให้)",
        "output": "sgi_fgi_impact_compensations มี forecast_amount / adjust_amount ของงวดที่ STA แจ้ง + แถว direction=IN ใน sgi_interface_transactions",
        "sources": [
            ["(ไม่มีคลาสเดิมใน fcsJar)", "-", "งานใหม่ทั้งหมด — ระบบเดิมรับยอดจาก STA ผ่านไฟล์/WS ไม่ใช่ RabbitMQ · สัญญาข้อความมาจาก STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md ข้อ 3 (2026-09-01)"],
        ],
    },
    "12": {
        "input": "งานค้างในขั้นรอดำเนินการของ workflow engine + อายุงานเป็นวัน",
        "progress": "อ่านงานค้างจาก engine, คำนวณอายุงาน, คัดเฉพาะช่วง 30-36 / 45-51 / 60-66 วัน, จัดกลุ่มตามโซน, ส่งอีเมลถึง GM และ OPT ต่อโซน",
        "output": "อีเมลเตือนงานค้าง 1 ฉบับต่อโซนต่อช่วงอายุ พร้อมแถวใน email_sent",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/SendMailReport.java", "23-60", "Legacy main entrypoint — เรียก 3 ช่วง 30/45/60 ตามลำดับ"],
            ["fcsJar/src/th/co/gosoft/fgi/service/MailReportService.java", "168-240", "seperateDay() คัดช่วงอายุงาน + sendEmail() จัดกลุ่มตามโซนและ resolve ผู้รับ GM/OPT"],
        ],
    },
    "10": {
        "input": "FGI_CONFIRM_RECEIVE_DATA rows without return_code after the waiting threshold.",
        "progress": "query missing receive data, group by data_name/direction (To-Be — เดิม Oracle ใช้ interface_type), build notification message, send admin mail, close run.",
        "output": "Notification sent for overdue receive confirmations; run status records grouped counts or no-data success.",
        "sources": [
            ["fcsJar/src/th/co/gosoft/fgi/main/NotifyNoReceiveData.java", "16-37", "Legacy main entrypoint for missing-receive notification."],
            ["fcsJar/src/th/co/gosoft/fgi/controller/ManageCompensateController.java", "748-775", "Build and send notification content for missing receive data."],
            ["fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ExportJdbc.java", "1894-1917", "Query confirm-receive rows without return_code."],
        ],
    },
}


# ---------------------------------------------------------------------------
# สัญญาการลงทะเบียน job + arguments บน srm-sps-spsap-sop-sgi-batch
# (มติ 2026-09-02 — ย้าย batch ทั้งชุดจาก store-backend มา repo นี้)
# แหล่งของ legacy args: main() ของแต่ละคลาสใน fcsJar/src/th/co/gosoft/fgi/main
# ---------------------------------------------------------------------------

JOB_RUN_CONTRACT: dict[str, dict[str, Any]] = {
    "11": {
        "job": "sgi-consume-sta-compensate",
        "legacy": "**ไม่มีของเดิม** — ระบบเดิมรับยอดจาก STA ผ่านไฟล์/WS ไม่ใช่ RabbitMQ · งานนี้เกิดจากสเปกข้อความชุดใหม่ของทีม STA (2026-09-01)",
        "fields": [
            ["`dataType`", "string", "—", "`message` \\| `S3` \\| `file` — envelope ที่ job อ่านจากคิวเอง", "**ของใหม่**"],
            ["`dataName`", "string", "—", "ต้องเป็น `sta_update_compensate` เท่านั้น · ไม่ตรง = จบงานแบบสำเร็จพร้อม log warn (ห้าม fail job เพราะ consumer ack ไปแล้ว)", "**ของใหม่**"],
            ["`dataMessage`", "object[]", "—", "รายการยอดชดเชยรายงวด (ใช้เมื่อ `dataType = message`)", "**ของใหม่**"],
            ["`urls`", "string", "—", "S3 URI ของไฟล์ (ใช้เมื่อ `dataType = S3`) — **job ต้องดาวน์โหลดเอง**", "**ของใหม่**"],
            ["`sender` / `sentAt`", "string", "—", "ผู้ส่งและเวลาส่ง — เก็บลง `sgi_interface_transactions` เพื่อตามรอย", "**ของใหม่**"],
        ],
        "example": '{"dataType":"message","dataName":"sta_update_compensate","dataMessage":[{"storeCode":"01234","compensateMonth":"2026-06","amount":15000}],"sender":"sta","sentAt":"2026-09-08T03:00:00.000Z"}',
        "notes": [
            "🔴 **มติ 2026-09-12 — job นี้ consume คิวเอง** · bind คิวใน `srm-sps-spsap-sop-sgi-batch` แล้วคุม ack/nack/DLQ เอง "
            "มาที่ job นี้พร้อม `INPUT` = envelope ทั้งก้อน · **1 ข้อความ = 1 การรัน** ไม่ใช่ drain-then-exit ตามที่เคยออกแบบไว้",
            "ผลที่ตามมา: `maxMessages` / `stopWhenEmpty` / `queue` **ไม่ใช้แล้ว** — prefetch, ack/nack และ DLQ เป็นหน้าที่ของ consumer "
            "🔴 **repo ปลายทางมีแต่ `publishMessage` ยังไม่มี consumer · DLQ · retry policy — ต้องสร้างใหม่ทั้งชุด** (ดู `SBP/srm-sps-spsap-sop-sgi-batch.md` ข้อ 4)",
            "job ต้องเป็น **idempotent** เพราะ consumer ไม่มีกลไกกันส่งซ้ำ — ใช้ `uq_interface_business` "
            "(`data_name` + `direction` + `business_key` + `period_key`) เป็นตัวกันบันทึกซ้ำ",
        ],
    },
    "12": {
        "job": "sgi-notify-pending-work",
        "legacy": "`SendMailReport.main` **ไม่รับ args** — เรียก `sendEmail(...)` 3 ครั้งตายตัวด้วย period `\"30\"`, `\"45\"`, `\"60\"`",
        "fields": [
            ["`asOfDate`", "string", "วันนี้", "`YYYY-MM-DD` · ใช้คำนวณอายุงาน", "**ของใหม่** — เดิมใช้วันปัจจุบันเสมอ ทดสอบย้อนหลังไม่ได้"],
            ["`windows`", "number[][]", "`[[30,36],[45,51],[60,66]]`", "คู่ `[เริ่ม,จบ]` · ต้องไม่ทับกัน · จบ ≥ เริ่ม", "**ของใหม่** — เดิม hardcode ใน `FgiConstant`"],
            ["`zones`", "string[]", "`null` = ทุกโซน", "รหัสโซนต้องมีจริง", "**ของใหม่**"],
        ],
        "example": '{"asOfDate":"2026-06-15","windows":[[30,36],[45,51],[60,66]]}',
        "notes": [
            "`dryRun=true` ให้ประกอบเนื้อหาอีเมลครบแต่ **ไม่ส่งจริงและไม่เขียน `email_sent`** — ใช้ตรวจว่าคัดงานได้ตรงก่อนเปิดใช้",
        ],
    },
    "2": {
        "job": "sgi-import-impact-store",
        "legacy": "`args[0]` = `ZONES|YYYY|MM` (`ZONES` = `BN,BS,BW` หรือ `ALL`) · ไม่ส่ง = **งวดเดือนก่อนหน้า** (`modifyDateToString(now, -1)`)",
        "fields": [
            ["`year`", "number", "งวดเดือนก่อนหน้า", "ค.ศ. 4 หลัก · 2000-2999", "`params[1]`"],
            ["`month`", "number", "งวดเดือนก่อนหน้า", "1-12", "`params[2]`"],
            ["`zones`", "string[]", "`null` = ทุกโซน", "รหัสโซนต้องมีใน `mas_zone` · `[]`/`null`/`\"ALL\"` = ไม่กรอง", "`params[0]` แยกด้วย `,`"],
        ],
        "example": '{"year":2026,"month":6,"zones":["BN","BS"]}',
        "notes": [
            "✅ **ปิดแล้ว 2026-09-12 — `PERIOD_YEAR` เป็น ค.ศ.** ตรวจฐานเดิมจริง (`FGI_IMPACT_STORE_BK_20250515` 26,264 แถว) พบปี **2016-2025 เท่านั้น ไม่มีค่า 25xx เลย** และคอลัมน์นี้คัดลอกตรงจาก `PERIOD_YEAR` ของวิว (`ImportStoreMapper.java:39`) · โค้ดเดิมก็ส่ง ค.ศ. (`Locale.US` = Gregorian ที่ `DateUtils.java:356`) ไม่มีการแปลง 543 ที่ใดเลย · ตัวอย่าง `ALL|2569|06` ในเอกสารเก่า**เป็นตัวอย่างที่เขียนผิด** ไม่ใช่พฤติกรรมจริง · `INPUT` ของ job ใหม่รับ ค.ศ. และยิง ค.ศ. ตรง ๆ (env `SGI_JOB2_ALLMAP_YEAR_ERA=AD`)",
        ],
    },
    "3": {
        "job": "sgi-import-impact-competitor",
        "legacy": "`args[0]` = `YYYY|MM` — **ต้องมี 2 ส่วนพอดี** (ว่าง/เกิน = `NullPointerException`) · validate ด้วย `isDateValid(yyyy/MM)` · ไม่ส่ง = **งวดเดือนก่อนหน้า**",
        "fields": [
            ["`year`", "number", "งวดเดือนก่อนหน้า", "ค.ศ. 4 หลัก · ต้องส่งคู่กับ `month` เสมอ", "`paramsArr[0]`"],
            ["`month`", "number", "งวดเดือนก่อนหน้า", "1-12 · ส่งมาตัวเดียวโดยไม่มีอีกตัว = `INVALID_JOB_INPUT`", "`paramsArr[1]`"],
        ],
        "example": '{"year":2026,"month":6}',
        "notes": ["legacy โยน exception ทันทีเมื่อ argument ผิดรูป — job ใหม่ต้องคง**พฤติกรรม fail-fast** ไม่ใช่ fallback เงียบ ๆ ไปงวดก่อนหน้า"],
    },
    "4": {
        "job": "sgi-prepare-impact-store-to-ias",
        "legacy": "**ไม่รับ args** — ใช้ปี/เดือน**ปัจจุบัน** จาก `Calendar` ไปประกอบชื่อไฟล์ (`ftpFileTimePattern`) และแปลง พ.ศ.→ค.ศ. เมื่อ `year > 2100`",
        "fields": [
            ["`year`", "number", "ปีปัจจุบัน", "ค.ศ. 4 หลัก", "**ของใหม่** — legacy ไม่มี ทำให้ rerun งวดย้อนหลังไม่ได้"],
            ["`month`", "number", "เดือนปัจจุบัน", "1-12", "**ของใหม่**"],
        ],
        "example": '{"year":2026,"month":6}',
        "notes": ["ชื่อไฟล์ยังเป็น `AMS06001O_yyyyMMddHHmm.txt` ที่สร้างจากเวลา ณ ตอนรัน — `year`/`month` ใช้คัดงวดของ candidate ไม่ใช่เปลี่ยนชื่อไฟล์"],
    },
    "5": {
        "job": "sgi-import-impact-sale-from-ias",
        "legacy": "รับ `args` แต่ **ไม่ได้ใช้เลย** — สแกนทุกไฟล์ในโฟลเดอร์ต้นทางที่ตรง regex `AMS06001I_YYYYMMDDHHMM.txt` (case-insensitive)",
        "fields": [
            ["`dataType`", "string", "—", "`S3` เมื่อมาจากข้อความในคิว (กรณีปกติ) · ไม่มีค่านี้ = โหมด safety-net สแกนเอง", "**ของใหม่**"],
            ["`urls`", "string", "—", "S3 URI ของไฟล์ `AMS06001I` ที่ EAI วางไว้ — **job ดาวน์โหลดเอง** (consumer ส่งแค่ที่อยู่)", "**ของใหม่**"],
            ["`dataName`", "string", "—", "ต้องเป็น `ams_impact_sale_result` · ไม่ตรง = จบแบบสำเร็จพร้อม log warn", "**ของใหม่**"],
            ["`fileName`", "string", "`null` = ประมวลผลทุกไฟล์ที่ตรง pattern", "ใช้เฉพาะโหมด safety-net · ต้องตรง regex เดิม ไม่ตรง = `INVALID_JOB_INPUT`", "**ของใหม่** — เจาะไฟล์เดียวเวลา rerun"],
            ["`reprocess`", "boolean", "`false`", "`true` = ยอมอ่านไฟล์ที่ย้ายไป prefix backup แล้ว", "**ของใหม่**"],
        ],
        "example": '{"dataType":"S3","dataName":"ams_impact_sale_result","urls":"s3://eai-inbound/sgi/AMS06001I_202606161630.txt","sender":"eai","sentAt":"2026-06-16T09:30:00.000Z"}',
        "notes": [
            "🔴 **มติ 2026-09-12 — job นี้ consume คิวของ EAI เอง** · EAI ส่งข้อความเข้า RabbitMQ ว่าไฟล์พร้อมแล้ว "
            "consumer อ่าน config จาก S3 แล้ว `SubmitJob` มาที่ job นี้พร้อม `INPUT` = envelope · **job ดาวน์โหลดไฟล์จาก `urls` เอง** "
            "เพราะข้อความบอกแค่ที่อยู่ไฟล์ ไม่ได้แนบไฟล์มาด้วย",
            "**cron เดิม `30 16 7-16 * *` ยังอยู่ในฐานะ safety net** — รันแล้วไม่เจอไฟล์ใหม่ให้จบแบบสำเร็จ ไม่ใช่ error · "
            "เผื่อกรณีข้อความหายจาก consumer ที่ยังไม่มี DLQ (ข้อ C1 ของเอกสาร consumer)",
            "`reprocess=true` ไม่ยกเว้นกฎกันซ้ำระดับข้อมูล — `checksum` + `UNIQUE(sales_summary_id, txn_date, window_no)` ยังทำงานตามเดิม",
        ],
    },
    "6": {
        "job": "sgi-export-impact-store-to-fs",
        "legacy": "`args[0]` = `yyyyMMdd` (วันประมวลผล) · ไม่ส่ง = **วันปัจจุบัน** · parse ไม่ได้ = log `Error PARAMETER is not format` แล้วจบแบบ FAIL",
        "fields": [
            ["`processDate`", "string", "วันนี้", "`YYYY-MM-DD` (ค.ศ.) · parse ไม่ได้ = `INVALID_JOB_INPUT`", "`args[0]` (`yyyyMMdd`)"],
        ],
        "example": '{"processDate":"2026-06-16"}',
        "notes": [
            "`processDate` ไม่ได้เป็นแค่ label — มัน**เปลี่ยนผลลัพธ์** 2 ทาง: (1) `dd` ของมันตัดสินว่าจะสร้างชุด `I` (Initial) ให้ STA หรือไม่ (2) เดือนก่อนหน้าของมันคืองวดที่ใช้ตรวจ QSSI · ดูหัวข้อเงื่อนไขตัดสิน",
        ],
    },
    "7": {
        "job": "sgi-sync-competitor-to-document",
        "legacy": "**ไม่รับ args** — sync ทุกเอกสารที่เข้าเงื่อนไข",
        "fields": [
            ["`docNo`", "string", "`null` = ทุกเอกสารที่เข้าเงื่อนไข", "`YYYY/xxxxx` · ไม่พบเอกสาร = `INVALID_JOB_INPUT`", "**ของใหม่**"],
            ["`impactMonth`", "string", "`null`", "`YYYY-MM`", "**ของใหม่**"],
        ],
        "example": '{"docNo":"2026/00123"}',
        "notes": ["ระบุ `docNo` แล้ว prune ต้องจำกัดขอบเขตเฉพาะเอกสารนั้น — ห้ามลบแถวของเอกสารอื่น"],
    },
    "8": {
        "job": "sgi-create-compensation-document",
        "legacy": "**ไม่รับ args**",
        "fields": [
            ["`impactMonth`", "string", "งวดล่าสุดที่พร้อม", "`YYYY-MM`", "**ของใหม่**"],
            ["`impactProcessIds`", "number[]", "`null` = ทุกรอบที่เข้าเงื่อนไข", "ต้องมีอยู่จริงใน `sgi_fgi_impact_processes`", "**ของใหม่**"],
        ],
        "example": '{"impactMonth":"2026-06"}',
        "notes": ["ระบุ `impactProcessIds` ไม่ข้ามกฎ `UNIQUE(impact_process_id)` — รอบที่มีเอกสารแล้วต้อง skip พร้อมคืน `doc_no` เดิม"],
    },
    "8b": {
        "job": "sgi-start-internal-workflow",
        "legacy": "**ไม่รับ args** (`StartK2WorkFlow.main`)",
        "fields": [
            ["`docNos`", "string[]", "`null` = ทุกเอกสารที่ยังไม่มี workflow", "`YYYY/xxxxx`", "**ของใหม่**"],
            ["`impactMonth`", "string", "`null`", "`YYYY-MM`", "**ของใหม่**"],
        ],
        "example": '{"docNos":["2026/00123"]}',
        "notes": ["รันซ้ำบนเอกสารเดิมต้องไม่เปิด workflow ซ้ำ — ตรวจ `sps_store.workflow_transaction` ด้วย `reference_id` + `version_id` ก่อนเสมอ"],
    },
    "9": {
        "job": "sgi-sync-new-store-to-document",
        "legacy": "**ไม่รับ args**",
        "fields": [
            ["`docNo`", "string", "`null` = ทุกเอกสารที่เข้าเงื่อนไข", "`YYYY/xxxxx`", "**ของใหม่**"],
            ["`impactMonth`", "string", "`null`", "`YYYY-MM`", "**ของใหม่**"],
        ],
        "example": '{"docNo":"2026/00123"}',
        "notes": ["prune เฉพาะแถว `source_system = 'FGI'` — แถวที่คนเพิ่มเอง (`USER`) ห้ามลบไม่ว่าจะส่ง arg แบบไหน"],
    },
    "10": {
        "job": "sgi-notify-no-receive-data",
        "legacy": "**ไม่รับ args**",
        "fields": [
            ["`asOfDate`", "string", "วันนี้", "`YYYY-MM-DD`", "**ของใหม่** — ใช้ทดสอบ/ย้อนหลัง"],
            ["`ageDays`", "number", "`1`", "จำนวนเต็ม ≥ 1", "**ของใหม่** — เดิม hardcode 1 วัน"],
        ],
        "example": '{"asOfDate":"2026-06-16","ageDays":1}',
        "notes": ["เปลี่ยน `ageDays` ไม่ล้าง marker `last_ack_notified_on` — รันซ้ำวันเดียวกันยังไม่ส่งเมลซ้ำ"],
    },
}


def _job_is_event_driven(job_no: str) -> bool:
    """job ที่ถูกกระตุ้นด้วยข้อความจากคิว (job consume เอง) — ไม่มีและห้ามมีตารางเวลา"""
    job = batch_job_by_no(job_no)
    return str((job or {}).get("cron", "")).strip().lower() == "event-driven"


def job_run_contract_blocks(job_no: str, section: str) -> list[dict[str, Any]]:
    """5.9x — job นี้ลงทะเบียนใน sop-sgi-batch อย่างไร และรับ argument อะไรได้บ้าง"""
    spec = JOB_RUN_CONTRACT.get(job_no)
    if not spec:
        return []
    name = spec["job"]
    rows = [[f, t, d, v, src] for f, t, d, v, src in spec["fields"]]
    rows.append(["`dryRun`", "boolean", "`false`", "`true` = อ่าน/คำนวณครบแต่ไม่ commit และไม่ publish/ไม่ส่งไฟล์", "**ของกลาง** ทุก job"])
    rows.append(["`limit`", "number", "`null`", "จำกัดจำนวนรายการที่ประมวลผลรอบนี้ (ใช้ตอน smoke test)", "**ของกลาง** ทุก job"])
    return [
        h(2, f"{section} การลงทะเบียน job และ Arguments (sop-sgi-batch)"),
        p(
            f"งานนี้ลงทะเบียนเป็น job ชื่อ **`{name}`** ใน `src/main.ts` ของ `SBP/srm-sps-spsap-sop-sgi-batch` "
            "โดยใช้ dispatcher เดิมของ repo (ไม่สร้าง runner ใหม่) — `main.ts` อ่านชื่อ job และ input มา 2 ทาง "
            "แล้วเลือกอัตโนมัติจากการมี `argv[3]` หรือไม่"
        ),
        table(["ช่องทางรัน", "ชื่อ job มาจาก", "input มาจาก", "ตัวอย่าง"], [
            ["Local / CLI / runbook", "env `JOB_NAME`", "env `INPUT` (JSON string)",
             f"`JOB_NAME={name} INPUT='{spec['example']}' npm run start`"],
            ["AWS Batch (ตารางเวลาจริง)", "`process.argv[3]`", "`process.argv[2]` (JSON string)",
             f"`node dist/main.js '{spec['example']}' {name}`"],
        ]),
        p(
            "**ตารางเวลาไม่ได้อยู่ในโค้ด** — repo นี้ไม่มี `@Cron`/`@Interval` แม้แต่จุดเดียว (แม้ติดตั้ง `@nestjs/schedule` ไว้) "
            "cron ในหัวข้อ 5 เป็น **นิยามของ AWS Batch scheduled event** ที่ต้องตั้งตอน deploy ไม่ใช่ค่าที่อ่านจาก config file"
            + (
                " · 🔴 **ยกเว้น job นี้** ซึ่งเป็น **event-driven ไม่มีตารางเวลา** — "
                "job bind คิวเองแล้วทำงานทุกครั้งที่มีข้อความเข้า "
                "**ห้ามตั้ง AWS Batch scheduled event ให้ job นี้** เพราะจะรันซ้อนกับ consumer"
                if _job_is_event_driven(job_no) else ""
            )
        ),
        h(3, "Argument ที่รับได้ (`INPUT` เป็น JSON object · ไม่ส่ง = `{}`)"),
        p(
            f"**ระบบเดิมรับ argument แบบนี้:** {spec['legacy']}  \n"
            "ของใหม่เปลี่ยนจาก positional string เป็น JSON เพื่อให้เพิ่มฟิลด์ได้โดยไม่พังของเดิม "
            "แต่ **ต้องรองรับทุกอย่างที่ระบบเดิมรับได้เป็นอย่างน้อย** — ห้ามลดความสามารถลง"
        ),
        table(["Field", "ชนิด", "ไม่ส่งแล้วได้อะไร (default)", "Validation", "ตรงกับ argument เดิม"], rows),
        p(
            "**กติกาการ validate ที่ทุก job ต้องทำเหมือนกัน** — parse `INPUT` ไม่สำเร็จ หรือฟิลด์ไม่ผ่าน validation "
            "ให้ log `BATCH_END` ด้วย `batchStatus: 'FAILED'` แล้ว `exit(1)` **ก่อนแตะฐานข้อมูล** "
            "(ห้าม fallback ไปค่า default เงียบ ๆ เมื่อผู้ใช้ตั้งใจส่งค่ามาแล้วผิด) · "
            "ฟิลด์ที่ไม่รู้จักให้ log warn แล้วข้าม ไม่ทำให้ job ล้ม"
        ),
    ] + ([bullets(spec["notes"])] if spec.get("notes") else [])


# ---------------------------------------------------------------------------
# เงื่อนไขตัดสินของแต่ละ job — "ตัดสินจากอะไร" ระดับตาราง.คอลัมน์
# ทุกแถวต้องสืบกลับไป legacy ได้ (ระบุไฟล์/บรรทัดใน 5.92) ห้ามเดา
# ---------------------------------------------------------------------------

JOB_DECISION_RULES: dict[str, dict[str, Any]] = {
    "11": {
        "intro": "Job 11 ตัดสิน 3 เรื่องต่อข้อความ 1 ใบ: **ข้อความนี้ของเราหรือเปล่า · เคยประมวลผลไปแล้วหรือยัง · จะเอายอดไปลงงวดไหน** — ผิดข้อกลางแล้วยอดชดเชยจะถูกทับซ้ำเงียบ ๆ",
        "rules": [
            ["ข้อความนี้เป็นของ job นี้หรือไม่",
             "envelope ของข้อความ — `dataType` · `dataName` · `sender`",
             "`dataType = 'message'` **และ** `dataName = 'sta_update_compensate'` · `sender` ที่ได้รับจริงคือ `\"STA\"` (⚠️ ไฟล์ต้นฉบับของ STA เขียนสลับเป็น `\"SGI\"` — ยึดทิศทางไม่ยึดค่าในไฟล์)",
             "`dataName` ไม่ตรง = **ack ทิ้งพร้อม log warn** (ไม่ใช่ nack — ไม่งั้นจะวนไม่รู้จบ) · envelope ผิดรูป = เข้า DLQ"],
            ["ข้อความนี้เคยประมวลผลไปแล้วหรือยัง",
             "`sgi_interface_transactions` — `data_name = 'STA_UPDATE_COMPENSATE'` · `direction = 'IN'` · `business_key` · `period_key`",
             "`business_key` = `storecode_i:storecode_n` · `period_key` = `compensate_year_month` แปลงจาก `yyMM` **พ.ศ.** เป็น `'YYYY-MM'` **ค.ศ.** แล้ว · พบแถวเดิม = เคยทำแล้ว",
             "เคยทำแล้ว = **ack ทิ้ง ไม่แก้ยอดซ้ำ** (นับเป็น `skipped`) — RabbitMQ redeliver ได้เสมอเมื่อ ack หาย"],
            ["ยอดนี้ลงงวดไหน ของรอบไหน",
             "`sgi_fgi_impact_processes` (`impacted_store_code` + งวด) → `sgi_fgi_impact_compensations` (`impact_process_id` + `compensate_month`)",
             "หา `impact_process_id` จาก `impacted_store_code` + งวดก่อน แล้วอัปเดตแถว `compensate_month` ที่ตรงกัน · `impactStatus` `Z` = ยอดเป็นศูนย์ · `W` = ยอดไม่เป็นศูนย์",
             "หารอบไม่เจอ = **เข้า DLQ พร้อม reason** ห้ามสร้างรอบใหม่เอง (รอบเป็นของ Job 6)"],
        ],
        "domains": [
            ["`dataName` ที่รับ", "`sta_update_compensate` เท่านั้น", "สเปก STA §3"],
            ["`impactStatus`", "`Z` = ยอดเป็นศูนย์ · `W` = ยอดไม่เป็นศูนย์", "สเปก STA §3"],
            ["ปีในข้อความ", "`compensate_year_month` / `stmt_year_month` เป็น `yyMM` **พ.ศ.**", "แปลงเป็น ค.ศ. ตอนอ่าน ห้ามให้ พ.ศ. หลุดเข้า DB"],
            ["จำนวนครั้ง retry ก่อนเข้า DLQ", "3", "ค่าตั้งต้นของ job นี้ (ของใหม่)"],
        ],
    },
    "12": {
        "intro": "Job 12 ตัดสินเรื่องเดียวแต่พลาดง่ายที่สุดในชุด: **งานค้างกี่วันถึงจะเตือน** — ระบบเดิมใช้ \"ช่วง 7 วัน\" ไม่ใช่ \"ครบ n วันขึ้นไป\" ซึ่งเอกสารรุ่นก่อนเขียนผิดมาตลอด",
        "rules": [
            ["งานค้างชิ้นนี้ต้องเตือนหรือไม่",
             "อายุงาน (วัน) นับจากเวลาที่เอกสารเข้าขั้นปัจจุบัน — `sps_store.workflow_transaction`",
             "อายุต้องอยู่ใน **ช่วงใดช่วงหนึ่งของ 3 ช่วงนี้: `30-36` · `45-51` · `60-66` วัน** · **นอกช่วงไม่ส่งเลย**",
             "⚠️ ค้าง 37-44 · 52-59 · หรือ **67 วันขึ้นไป จะเงียบสนิท** — เป็นพฤติกรรมเดิม (`MailReportService.seperateDay` บรรทัด 177-183) ที่ผูกกับการรัน**สัปดาห์ละครั้ง** พอดี · เปลี่ยนความถี่การรันเมื่อไร **ต้องทบทวนช่วงพร้อมกัน** ไม่งั้นงานจะหลุดการเตือน"],
            ["งานแบบไหนถึงนับ",
             "`sps_store.workflow_transaction.current_state_id` เทียบกับชุด state ที่รอคนกด",
             "เฉพาะเอกสารที่อยู่ใน **ขั้นรอดำเนินการ** (ระบบเดิมคือ `stepID = 501001`) — ระบบใหม่ต้อง map เป็นชุด state ของ engine กลางแล้วเก็บใน config",
             "เอกสารที่จบแล้ว (`99`) หรืออยู่ระหว่างระบบทำงานเอง ไม่นับ"],
            ["ส่งหาใคร",
             "โซนของร้านที่ถูกกระทบ (`mas_store.region`) + `business_user` ของระบบ SBP เดิม",
             "จัดกลุ่มตามโซนก่อน แล้วส่ง **1 ฉบับต่อโซนต่อช่วงอายุ** ถึง **GM group `38`** และ **OPT group `15`**",
             "โซนที่ไม่มีผู้รับ = log warn แล้วข้ามโซนนั้น **ห้ามล้มทั้ง job**"],
        ],
        "gaps": [
            ["**G7** ⏳ ต้องยืนยัน", "ระบบเดิมใส่ **วันที่ พ.ศ.** ในอีเมล (`getCurrentBuddhistDate()`) ซึ่งขัดกับกติกา ค.ศ. ทั้งระบบ (มติ 2026-08-06)", "ตัดสินว่าอีเมลจะคง พ.ศ. ตามของเดิม หรือเปลี่ยนเป็น ค.ศ. ให้ตรงทั้งระบบ — กระทบ template ที่ต้องเตรียม"],
            ["**G8** ⏳ ต้องยืนยัน", "ไม่มี marker กันส่งซ้ำเมื่อ rerun วันเดียวกัน (ต่างจาก Job 10 ที่มี `last_ack_notified_on`)", "ถ้าต้องกันซ้ำ ต้องเพิ่มคอลัมน์/ตาราง marker · ถ้ายอมให้ส่งซ้ำได้ตอน rerun ให้ระบุไว้ใน runbook"],
        ],
        "domains": [
            ["ช่วงอายุงาน", "`30-36` · `45-51` · `60-66` วัน (ช่วงละ 7 วัน)", "`FgiConstant.THIRTYDAY/THIRTYSIX/FOURTYFIVEDAY/FIFTYONE/SIXTYDAY/SIXTYSIX`"],
            ["กลุ่มผู้รับ", "GM = `38` · OPT = `15`", "`FgiConstant.GM_GROUP_ID` / `OPT_GROUP_ID`"],
            ["ขั้นที่นับว่าค้าง", "ระบบเดิม `stepID = 501001`", "`FgiConstant.STEPIDWAIT` — ระบบใหม่ map เป็น state ของ `@srm/glb-workflow`"],
            ["จังหวะรัน", "ทุกวันจันทร์ 10:00 น.", "`workflow.md` · ต้องสอดคล้องกับช่วง 7 วันข้างบน"],
        ],
    },
    "2": {
        "intro": "Job 2 ตัดสิน 3 เรื่องต่อกันเป็นทอด และ **ผิดข้อใดข้อหนึ่งก็ทำให้ร้านหายไปเงียบ ๆ โดยไม่มี error**: (ก) แถวไหนจาก ALLMAP นับเป็น candidate (ข) candidate นั้น **เป็นคู่ร้านใหม่หรือมีอยู่แล้ว** (ค) คู่ที่ insert แล้วจะ **เข้ากระบวนการ** หรือ **ถูกตัดทิ้ง**",
        "rules": [
            ["ก. แถวนี้เป็น candidate ของงวดหรือไม่",
             "วิว `allmapssa.SEVEN_IMPACT_VIEW` (SQL Server GSMALLMAP · ระบบภายนอก อ่านอย่างเดียว)",
             "`PERIOD_YEAR` = ปีที่ขอ **และ** `PERIOD_MONTH` = เดือนที่ขอ · ส่ง `zones` มาก็เพิ่ม `ZONE_I IN (...)` · เก็บเฉพาะแถวแรกของแต่ละ `(STORECODE_I, STORECODE_N, PERIOD_YEAR, PERIOD_MONTH)` ด้วย `ROW_NUMBER() OVER(PARTITION BY ... ORDER BY PERIOD_YEAR, PERIOD_MONTH) = 1`",
             "ไม่เข้าเกณฑ์ = ไม่อ่านเข้ามา · **วิวไม่คืนแถวเลย = จบงานแบบ SUCCESS** พร้อม note (ระบบเดิม `return true` ไม่ใช่ FAIL)"],
            ["ข. **เป็นคู่ร้านใหม่หรือมีอยู่แล้ว**",
             "`sgi_fgi_impact_stores` (`impacted_store_code` · `new_store_code` · `impact_month` · `verify_status`) LEFT JOIN `sgi_fgi_impact_processes` (`impacted_store_code` · `flag_action` · `start_compensate_year/_month` · `end_compensate_year/_month`)",
             "สร้าง **ชุด \"มีอยู่แล้ว\"** ของงวดก่อน (SQL ด้านล่าง) แล้วเทียบ candidate ด้วยคีย์ `(impacted_store_code, new_store_code)` · **ไม่พบในชุด = คู่ใหม่ → INSERT** · **พบ = ข้าม**",
             "⚠️ **พบแล้วระบบเดิมไม่อัปเดตอะไรเลย** — `updateList` ถูกสร้างขึ้นแต่ `manageImpactStore()` เรียกเฉพาะ `insertList` (`ImpactStoreService` บรรทัด 45-51, 148-155) · ระบบใหม่ต้องคงพฤติกรรมนี้และนับเป็น `skipped`"],
            ["ค1. คู่นี้ต้อง **ถูกตัดทิ้ง** หรือไม่ (`verify_status = 'N'`)",
             "**ตารางของระบบ SBP เดิม (อ่านอย่างเดียว)**: `mas_store` (`branch_id` · `status_type` · `open_date` · `region`) · `fr_store` (`store_id` · `juristic_id` · `start_date` · `cancel_date` · `cancel_type` · `status` · `order_id`) · `juristic` (`juristic_id` · `juristic_name`)",
             "ตัดทิ้งเมื่อ **ข้อใดข้อหนึ่ง** จริง: ประเภทสาขาฝั่ง I ไม่อยู่ในรายการที่รับได้ · ฝั่ง N เป็น `F` · **นิติบุคคลสองฝั่งเป็นรายเดียวกัน** · สัญญา SBP ของร้าน I ไม่คลุมงวด · หรือแถวเก่ากว่า 12 เดือน (SQL ด้านล่าง)",
             "ตั้ง **`verify_status = 'N'`** + `updated_at` และ **ไม่ลบแถว** (เก็บไว้ตรวจย้อนหลัง)"],
            ["ค2. คู่นี้ **เข้ากระบวนการ** หรือไม่ (`verify_status = 'P'`)",
             "ชุดคอลัมน์เดียวกับ ค1 + **`sgi_fgi_impact_stores.created_by` / `.updated_by`**",
             "เข้ากระบวนการเมื่อ มาจาก ALLMAP **และ** ผ่านเกณฑ์ประเภทสาขาทั้งสองฝั่ง **และ** นิติบุคคลคนละราย **และ** สัญญา SBP คลุมงวด — **หรือ** มาจาก STA (เคสที่ระบบ Statement ส่งเข้ามาเอง ผ่านทันทีโดยไม่ตรวจเกณฑ์)",
             "ตั้ง **`verify_status = 'P'`** + `updated_at` · แถวที่ไม่เข้าทั้ง ค1 และ ค2 ค้างเป็น `'W'` ให้รอบถัดไปหยิบ"],
        ],
        "gaps": [
            ["**G1** ✅ ปิดแล้ว 2026-09-02", "เดิม `sales_request_status` (`W/P/Y/E`) ไม่มีที่เก็บผล DENY", "เพิ่มคอลัมน์ **`verify_status CHAR(1) CHECK IN ('W','P','N')`** แยกจาก `sales_request_status` — legacy มีสองสถานะคนละเรื่อง (ตรวจคู่ร้าน vs ขอยอดขาย) ที่โครงเดิมยุบเหลือคอลัมน์เดียว"],
            ["**G2** ✅ ปิดแล้ว 2026-09-02", "เดิมไม่มี `created_by` / `updated_by`", "เพิ่ม **`created_by` / `updated_by VARCHAR(10) CHECK IN ('ALM','STA','USER')`** และ **`created_at`** (กฎ \"เก่ากว่า 12 เดือน\" อ้างคอลัมน์นี้)"],
            ["**G3** ✅ ปิดแล้ว 2026-09-12", "ไม่มีคอลัมน์วันเปิดร้าน / ประเภทสาขา / นิติบุคคล / วันสัญญา SBP ใน `sgi_*` เลย — **และจะไม่เพิ่ม**", "ทุกเงื่อนไขของ ค1/ค2 **join ออกไปที่ `mas_store` · `fr_store` · `juristic` ของ schema `sps_store`** (อ่านอย่างเดียว) · **วัดผลกระทบจากข้อมูลจริงแล้ว**: แถว ALM 23,120 แถวที่หาร้านใน master เจอ เปลี่ยนจาก snapshot มาใช้ `mas_store.status_type` ปัจจุบันแล้ว**ผลตัดสินพลิกแค่ 19 แถว (0.08%)** และฝั่งร้านใหม่ (`branchtype_n = F`) **พลิก 0 แถว** — จึงไม่คุ้มที่จะเพิ่มคอลัมน์ snapshot · สิ่งที่เหลือคือ **ยืนยันสิทธิ์อ่านข้าม schema + index บน `mas_store.branch_id` / `fr_store.store_id`** (ข้อมูลจริง: ร้าน 1,056 ร้านมีสัญญา `fr_store` มากกว่า 1 ฉบับ — ชั้น `dense_rank() = 1` จำเป็นจริง ไม่ใช่ทฤษฎี)"],
        ],
        "domains": [
            ["`verify_status` (เดิม `FLAG_VERIFY`)", "`W` = รอตรวจ (ค่าตั้งต้นตอน insert) · `P` = เข้ากระบวนการ · `N` = ถูกตัดทิ้ง<br>**ข้อมูลจริง (26,264 แถว):** `N` 14,424 · `Y` 8,556 · `W` 3,064 · `P` 220 — `Y` ของเดิมคือ \"ยอดขายผ่านแล้ว\" ซึ่งโครงใหม่แยกไป `sales_request_status` **migration ต้องแมป ไม่ใช่คัดลอกตรง**", "`FgiConstant.FLAG_VERIFY_WAIT` / `_ON_PROCESS` / `_DENY` · ตรวจฐาน stqa 2026-09-12"],
            ["`created_by` / `updated_by` (เดิม `CREATE_BY`/`UPDATE_BY`)", "`ALM` = ALLMAP · `STA` = ระบบ Statement ส่งเข้ามา · `USER` = คนคีย์เอง<br>**ข้อมูลจริง:** `CREATE_BY` = ALM 23,126 · STA 3,138 (**ไม่มี `USER` เลย**) · `UPDATE_BY` = **NULL ทั้ง 26,264 แถว** → เงื่อนไข `'ALM' IN (created_by, updated_by)` ของกฎตัดทิ้ง ในทางปฏิบัติเท่ากับ `created_by = 'ALM'`", "`FgiConstant.ALLMAP` / `FRANCHISE_STATEMENT` · ตรวจฐาน stqa 2026-09-12"],
            ["ประเภทสาขาฝั่ง I ที่รับได้", "`B` · `FAM` · `FB1` · `FB2` · `FC1` · `FVB` · `FVC` — และ `FPT1` **เฉพาะเมื่อ** ประเภทการยกเลิก SBP = `'06'`", "SQL ของ `updateImpactStoreByJuristicMeetCondition()`"],
            ["ประเภทสาขาฝั่ง N ที่ห้าม", "`F`", "เงื่อนไข `a.branchtype_n in ('F')` ในกฎตัดทิ้ง"],
            ["หน่วยของ `DISTANCE_UNIT` ที่ ALLMAP ส่งมาจริง", "**`กิโลเมตร` (ภาษาไทย) ค่าเดียวเท่านั้น** — 23,127 แถวของ `CREATE_BY = 'ALM'` ทั้งหมด · ไม่เคยส่ง `KM`/`M` ภาษาอังกฤษเลย · แถว `STA` ส่ง `DISTANCE = 0` และหน่วยเป็น NULL<br>ระยะทางจริงอยู่ในช่วง **0.03–1.52 กม.** และคอลัมน์เดิมเป็น `NUMBER(3,2)` = เก็บเป็นกิโลเมตรอยู่แล้ว", "ตรวจฐาน stqa 2026-09-12 — whitelist การแปลงหน่วยต้องมี `กิโลเมตร` เป็นอย่างน้อย"],
            ["อายุแถวสูงสุดก่อนถูกตัดทิ้ง", "12 เดือนนับจากวันที่สร้างแถว", "`FgiConstant.INTERVAL_MONTH = 12`"],
            ["ค่าแทน \"ไม่มีวันยกเลิก\"", "`4000-01-01` (`to_date('01/4000','mm/yyyy')`)", "ใช้กับ `COALESCE(cancel_date, ...)` ทั้ง ค1 และ ค2"],
        ],
        "sql_title": "ข. ชุด \"คู่ร้านที่มีอยู่แล้ว\" — ตัวตัดสินว่าเป็นคู่ใหม่หรือไม่",
        "sql_note": "ชุดนี้ **ไม่ใช่แค่ \"แถวของงวดนี้\"** — ร้าน I ที่ยังมีรอบชดเชย active (`flag_action IN ('Y','W')`) ครอบคลุมงวดที่ขอ ก็นับว่า \"มีอยู่แล้ว\" ทั้งที่คู่ (I,N) นั้นอาจมาจากงวดอื่น · **จุดนี้คือสาเหตุที่คู่ร้านบางคู่หายไปเงียบ ๆ ถ้า implement เป็นแค่ `WHERE impact_month = :m`**",
        "sql": """-- ชุด "มีอยู่แล้ว" ของงวด :impact_month ('YYYY-MM')
-- แปลงตรงจาก ImportStoreJdbc.getImpactStoreFranchise (บรรทัด 170-219)
SELECT DISTINCT fis.impacted_store_code, fis.new_store_code
FROM sgi_fgi_impact_stores fis
LEFT JOIN sgi_fgi_impact_processes op
       ON op.flag_action IN ('Y', 'W')                       -- นับเฉพาะรอบที่ยัง active
      AND op.impacted_store_code = fis.impacted_store_code
      AND to_date(:impact_month, 'YYYY-MM') BETWEEN
              to_date(op.start_compensate_month, 'YYYY-MM')
          AND CASE
                -- ถ้า "เดือนก่อนหน้าเดือนปัจจุบัน" = งวดปิดล่าสุด หรือ งวดปิดล่าสุด + 1 เดือน
                -- ให้ยืดขอบบนออกไปถึงเดือนก่อนหน้า (รองรับรอบที่ยังชดเชยต่อเนื่องอยู่)
                WHEN (date_trunc('month', CURRENT_DATE) - INTERVAL '1 month') IN (
                       to_date(op.end_compensate_month, 'YYYY-MM'),
                       to_date(op.end_compensate_month, 'YYYY-MM') + INTERVAL '1 month')
                THEN date_trunc('month', CURRENT_DATE) - INTERVAL '1 month'
                ELSE to_date(op.end_compensate_month, 'YYYY-MM')
              END
WHERE fis.verify_status <> 'N'               -- แถวที่ถูกตัดทิ้งไม่นับว่ามีอยู่
  AND ( fis.impact_month = :impact_month     -- แถวของงวดนี้
        OR op.id IS NOT NULL );              -- หรือร้าน I อยู่ในรอบ active ที่คลุมงวดนี้

-- candidate จาก ALLMAP ที่ (impacted_store_code, new_store_code) ไม่อยู่ในผลลัพธ์นี้ = คู่ใหม่ -> INSERT
-- ที่อยู่ในผลลัพธ์ = ข้าม (นับเป็น skipped) ห้าม UPDATE ทับ""",
        "sql2_title": "ค. กฎตัดทิ้ง และกฎเข้ากระบวนการ — **ต้องรันตามลำดับนี้เท่านั้น** (ตัดทิ้งก่อนเสมอ)",
        "sql2": """-- 🔴 อ่านสองข้อนี้ก่อนใช้ SQL ด้านล่าง — ทั้งคู่ยังไม่ตรงกับระบบเดิม 100%
--
-- (1) แหล่งของ branchtype — SQL นี้ใช้ ms_i.status_type / ms_n.status_type จาก mas_store
--     แต่ระบบเดิมใช้ decode(fis.create_by,'STA', ms_i.status_type, fis.branchtype_i)
--     (ImportStoreJdbc.java:229) => แถว 'ALM' ซึ่งเป็นแถวที่ Job 2 สร้าง **ใช้ค่าจาก ALLMAP ไม่ใช่ master**
--     การเปลี่ยนมา join master เป็นการ **เปลี่ยนพฤติกรรมทางธุรกิจ** (ผล P/N อาจต่างจากเดิม)
--     ไม่ใช่แค่ปรับโครงสร้าง — ช่องว่าง G3 จึงยังไม่ปิด ต้องเคาะก่อน (DECISIONS ข้อ 2.15)
--
-- (2) การเลือกสัญญา fr_store — LEFT JOIN ตรง ๆ ข้างล่างยัง **ไม่รักษากติกาเดิม**
--     ร้านหนึ่งร้านมีหลายสัญญาในงวดเดียวได้ ระบบเดิมจึงคัดเหลือฉบับเดียวก่อนเสมอ:
--
--       dense_rank() OVER (PARTITION BY store_id, งวด
--                          ORDER BY start_date DESC, cancel_type, order_id DESC) = 1
--       WHERE COALESCE(status,'-') <> 'D'
--         AND store_id <> '00000'
--         AND cancel_type IS NOT NULL
--         AND TRUNC(start_date)  <= วันสุดท้ายของงวด
--         AND COALESCE(cancel_date, DATE '4000-01-01') >= วันแรกของงวด
--
--     ถ้าไม่ใส่ชั้นนี้ JOIN จะได้หลายแถวต่อร้าน => นิติบุคคล/วันสัญญาที่เอามาตัดสินอาจเป็นคนละฉบับ
--     กับที่ระบบเดิมใช้ และ UPDATE จะได้ผล P/N ไม่คงที่ **ต้องทำเป็น CTE คัดให้เหลือ rank 1 ก่อน join**

-- ค1. ตัดทิ้ง : รันก่อน (updateImpactStoreByJuristicNotMeetCondition · บรรทัด 344-380)
UPDATE sgi_fgi_impact_stores a
   SET verify_status = 'N', updated_by = 'ALM', updated_at = CURRENT_TIMESTAMP
  FROM mas_store   ms_i  -- ร้านที่ถูกกระทบ
  LEFT JOIN fr_store s_i ON s_i.store_id = ms_i.branch_id AND COALESCE(s_i.status,'-') <> 'D'
  LEFT JOIN juristic j_i ON j_i.juristic_id = s_i.juristic_id
     , mas_store   ms_n  -- ร้านเปิดใหม่
  LEFT JOIN fr_store s_n ON s_n.store_id = ms_n.branch_id AND COALESCE(s_n.status,'-') <> 'D'
  LEFT JOIN juristic j_n ON j_n.juristic_id = s_n.juristic_id
 WHERE a.verify_status = 'W'
   AND ms_i.branch_id = a.impacted_store_code
   AND ms_n.branch_id = a.new_store_code
   AND 'ALM' IN (a.created_by, a.updated_by)
   AND (
         ms_i.status_type NOT IN ('B','FAM','FB1','FB2','FC1','FVB','FVC','FPT1')
      OR ms_n.status_type IN ('F')
      OR TRIM(COALESCE(j_n.juristic_name,'juristic_n')) = TRIM(COALESCE(j_i.juristic_name,'juristic_i'))
      OR ( (    ms_i.status_type IN ('B','FAM','FB1','FB2','FC1','FVB','FVC')
             OR (ms_i.status_type = 'FPT1' AND s_i.cancel_type = '06') )
           AND ( date_trunc('day', s_i.start_date)
                     >= (to_date(a.impact_month,'YYYY-MM') + INTERVAL '1 month - 1 day')
              OR to_date(a.impact_month,'YYYY-MM')
                     >= date_trunc('day', COALESCE(s_i.cancel_date, DATE '4000-01-01')) ) )
      OR CURRENT_TIMESTAMP > (date_trunc('day', a.created_at) + INTERVAL '12 months')
   );

-- ค2. เข้ากระบวนการ : รันหลัง ค1 เสมอ (updateImpactStoreByJuristicMeetCondition · บรรทัด 381-420)
UPDATE sgi_fgi_impact_stores a
   SET verify_status = 'P', updated_by = 'ALM', updated_at = CURRENT_TIMESTAMP
 WHERE a.verify_status = 'W'
   AND (
        (    a.created_by = 'ALM'
         AND <ผ่านเกณฑ์ประเภทสาขาฝั่ง I>          -- เงื่อนไขชุดเดียวกับ ค1 แต่กลับด้าน
         AND <ประเภทสาขาฝั่ง N ไม่ใช่ 'F'>
         AND <นิติบุคคลสองฝั่งคนละราย>
         AND <สัญญา SBP ของร้าน I คลุมงวด>  )
     OR a.created_by = 'STA'      -- STA ส่งเข้ามาเอง: ผ่านทันที ไม่ตรวจเกณฑ์ด้านบน
   );""",
    },
    "3": {
        "intro": "Job 3 ตัดสินเรื่องเดียวแต่พลาดง่าย: **งวดนี้เคยนำเข้าคู่แข่งไปแล้วหรือยัง** — ⚠️ ระบบเดิม **ข้ามทั้งงวดแล้วรายงานว่าสำเร็จ** ไม่ได้ล้างแล้วนำเข้าใหม่ และไม่ได้ merge ทีละแถว (ยืนยันแล้วว่า `fcsJar/` ไม่มีคำสั่ง `DELETE FROM FGI_IMPACT_COMPETITOR` เลยแม้แต่จุดเดียว)",
        "rules": [
            ["งวดนี้มีข้อมูลคู่แข่งอยู่แล้วหรือไม่",
             "`sgi_fgi_impact_competitors` — `impact_process_id` · `period_key` (CHAR(7) `'YYYY-MM'`)",
             "มีแถวของ `period_key` = งวดที่ขอ อยู่แล้ว → ถือว่า \"งวดนี้นำเข้าแล้ว\"",
             "**ข้ามทั้งงวดทันที ไม่ insert อะไรเลย แล้วจบด้วยสถานะสำเร็จ** (`ImportController.importImpactCompetitor` บรรทัด 521-527) — ไม่ใช่ล้างแล้วนำเข้าใหม่ และไม่ใช่ upsert · 🔴 **จุดเสี่ยง:** ถ้ารอบก่อนล้มกลางคันจนมีข้อมูลค้างไม่ครบ การรันซ้ำจะไม่ช่วยอะไร ข้อมูลขาดถาวรโดยไม่มีใครรู้ — ระบบใหม่ต้องเทียบจำนวนกับต้นทางแล้ว **alert เมื่อไม่ตรง** (ดู `batchjob/JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md` หัวข้อ 3 และ 10)"],
            ["ร้านคู่แข่งรายนี้อ้างอิงได้หรือไม่",
             "`sgi_competitors.competitor_code` (master 11 รหัส `01`-`11`)",
             "⚠️ **`COMPET_ID` ที่วิวส่งมาคือ *รหัสสาขา* ไม่ใช่รหัสแบรนด์** (ไฟล์จริง BPM06003O มี 222 รหัสจาก 7 แบรนด์) จึงเก็บลง `competitor_store_code` ที่**ไม่มี FK** · ส่วน `brand_code` ได้จากการ map ชื่อแบรนด์เข้า master 11 รายการ",
             "ต้อง **reject รายแถวพร้อมเก็บ reason** ไม่ใช่ล้มทั้งงวด (นับเข้า `rejected` ใน metrics)"],
            ["แถวซ้ำในวิวต้นทาง",
             "วิว `COMPETITOR_IMPACT_VIEW` (ALLMAP · SQL Server GSMALLMAP)",
             "อ่านทีละ 10,000 แถว · deduplicate ด้วยคีย์ `(impact_process_id, competitor_store_code, period_key)` **ก่อน** ยิงเข้า DB · แถวที่ `competitor_store_code` ว่างต้องแปลงเป็น NULL แล้ว dedup ด้วย `branch_th` แทน",
             "ไม่ dedup ก่อน จะชน `uq_impact_competitor` แล้วทั้ง chunk fail"],
        ],
        "domains": [
            ["ขนาด chunk", "10,000 แถว", "พฤติกรรมเดิมของ `ImportImpactCompetitor`"],
            ["คีย์กันซ้ำ", "`UNIQUE (impact_process_id, competitor_store_code, period_key)` — **คีย์เป็นสาขา ไม่ใช่แบรนด์**", "`uq_impact_competitor` ใน DDL (แก้ 2026-09-09)"],
        ],
    },
    "4": {
        "intro": "Job 4 ตัดสินว่า **ร้านไหนพร้อมขอยอดขายจาก IAS/MIS แล้ว** — ไม่ใช่ทุกแถวที่สถานะ `'W'` จะถูกส่ง เพราะมีเงื่อนไข **อายุร้าน** และ **ระยะเวลารอหลังร้านใหม่เปิด** คุมอยู่ และทั้งสองข้อนี้หายไปจากเอกสารเดิม",
        "rules": [
            ["ร้านนี้พร้อมส่งขอยอดขายหรือยัง",
             "`sgi_fgi_impact_stores.verify_status` · `.sales_request_status` + **วันเปิดร้านจาก `mas_store.open_date`** ของทั้งร้าน I (`impacted_store_code`) และร้าน N (`new_store_code`)",
             "ต้องจริงครบ 4 ข้อ: (0) **`verify_status = 'P'`** (ผ่านกฎของ Job 2 มาแล้ว) (1) `sales_request_status = 'W'` (2) **ร้านเก่าเปิดก่อนร้านใหม่อย่างน้อย 12 เดือน 15 วัน** → `open_date(I) <= (open_date(N) - 12 เดือน) - 15 วัน` (3) **วันนี้ต้องเลย `open_date(N) + 15 + 1` วันไปแล้ว**",
             "ไม่ครบ = ไม่ส่งรอบนี้ ค้างเป็น `'W'` ให้รอบถัดไปหยิบ — **ไม่ใช่ error และไม่นับเป็น rejected**"],
            ["ส่งอะไรลงไฟล์",
             "คอลัมน์เดียวกับข้างบน",
             "1 บรรทัด = `impacted_store_code + '|' + to_char(open_date(N),'YYYYMMDD')` · เรียงด้วย `open_date(N)`, `impacted_store_code`",
             "จำนวนบรรทัดต้องเท่ากับจำนวน candidate ที่ล็อกไว้ ไม่เท่า = ยกเลิกทั้งรอบ"],
            ["เปลี่ยนสถานะเมื่อไร",
             "`sgi_fgi_impact_stores.sales_request_status`",
             "`'W' → 'P'` **หลังเขียนไฟล์ลงดิสก์สำเร็จ (fsync + atomic rename) แล้วเท่านั้น** และอยู่ transaction เดียวกับ insert outbox",
             "อัปโหลด S3 ล้มเหลว **ห้ามย้อน `'P' → 'W'`** (จะสร้างไฟล์ซ้ำ) — ให้ outbox retry แทน"],
        ],
        "gaps": [
            ["**G4** ⏳ ยังค้าง", "ไม่มีคอลัมน์วันเปิดร้านใน `sgi_*` เลย (`open_date` ไม่ปรากฏใน DDL ทั้ง 20 ตาราง) — **และจะไม่เพิ่ม** (วันเปิดร้านเป็น master ของระบบเดิม คัดลอกมาเก็บจะ stale)", "เงื่อนไข 12 เดือน 15 วัน และ 16 วัน ต้อง join ออกไปที่ `mas_store.open_date` (schema `sps_store`) ทุกครั้ง — ต้องยืนยัน **สิทธิ์อ่าน + index บน `mas_store.branch_id`** ก่อน implement"],
        ],
        "domains": [
            ["ระยะห่างอายุร้าน", "12 เดือน 15 วัน", "`FgiConstant.INTERVAL_MONTH = 12` · `INTERVAL_DAY = 15`"],
            ["ระยะรอหลังร้านใหม่เปิด", "15 + 1 = 16 วัน", "`TRUNC(SYSDATE) > (TRUNC(OPENDATE_N + 15) + 1)`"],
            ["สถานะของ `sales_request_status`", "`W` = รอส่งขอ · `P` = ส่งขอแล้วรอไฟล์ตอบกลับ · `Y` = ได้ยอดแล้ว · `E` = ผิดพลาด", "`CHECK` ใน DDL"],
        ],
        "sql_title": "SQL คัด candidate (แปลงจาก `ImportStoreJdbc.getPrepareImpactStoreToIASList` บรรทัด 99-115)",
        "sql_note": "ค่า 12 / 15 ต้องอ่านจาก config ไม่ hardcode ในคิวรี แต่ **ค่าตั้งต้นต้องเท่าระบบเดิม** ไม่งั้นจำนวนร้านที่ส่งขอจะไม่ตรงกับของเดิมตอนเทียบ UAT",
        "sql": """SELECT fis.id,
       fis.impact_process_id,
       fis.impacted_store_code,
       fis.new_store_code,
       fis.impact_month,
       fis.impacted_store_code || '|' || to_char(ms_n.open_date, 'YYYYMMDD') AS line
FROM sgi_fgi_impact_stores fis
JOIN mas_store ms_i ON ms_i.branch_id = fis.impacted_store_code   -- schema sps_store (อ่านอย่างเดียว)
JOIN mas_store ms_n ON ms_n.branch_id = fis.new_store_code
WHERE fis.verify_status = 'P'          -- ผ่านกฎ DENY/ON_PROCESS ของ Job 2 มาแล้วเท่านั้น
  AND fis.sales_request_status = 'W'
  AND ms_i.open_date <= date_trunc('day', ms_n.open_date - INTERVAL '12 months' - INTERVAL '15 days')
  AND date_trunc('day', CURRENT_DATE) > date_trunc('day', ms_n.open_date + INTERVAL '15 days') + INTERVAL '1 day'
ORDER BY ms_n.open_date, fis.impacted_store_code
FOR UPDATE OF fis SKIP LOCKED;""",
    },
    "5": {
        "intro": "Job 5 ตัดสิน 3 เรื่อง: ไฟล์ไหนควรอ่าน · บรรทัดไหนจับคู่กับร้านได้ · และ **ยอดขายครบพอจะคำนวณ Growth หรือยัง**",
        "rules": [
            ["ไฟล์นี้ควรอ่านหรือไม่",
             "ชื่ออ็อบเจกต์บน EAI S3 (prefix ขาเข้าของ IAS)",
             "ต้องตรงรูปแบบ `AMS06001I_YYYYMMDDHHMM.txt` (ตรวจด้วย regex เดิม · case-insensitive) — ไม่ตรง = ข้ามไฟล์นั้น",
             "ระบบเดิม **สแกนทุกไฟล์ในโฟลเดอร์** ไม่ได้ใช้ argument เลย · ของใหม่เพิ่ม `fileName` เพื่อเจาะไฟล์เดียวได้ (ดู 5.95)"],
            ["ไฟล์นี้เคยประมวลผลไปแล้วหรือยัง",
             "`sgi_interface_transactions` — `data_name = 'IMPACT_STORE_SALES'` · `direction = 'IN'` · `file_name` · `file_checksum`",
             "มี transaction ของ `file_name` เดิมและ checksum ตรงกัน = เคยอ่านแล้ว → ข้าม",
             "อ่านสำเร็จจึงย้ายอ็อบเจกต์ไป prefix backup — **ย้ายไฟล์ต้องเป็นขั้นสุดท้าย** ไม่ใช่ก่อน commit"],
            ["บรรทัดนี้จับคู่กับร้านไหน",
             "`sgi_fgi_impact_stores` (`impacted_store_code` + วันเปิดร้านใหม่) — ไฟล์มี 4 ฟิลด์: `impacted_store_code | วันเปิดร้านใหม่ | วันที่ขาย | ยอดขาย`",
             "จับคู่ด้วย `impacted_store_code` + วันเปิดร้านใหม่ (ตรงกับคีย์ที่ Job 4 ส่งออกไป) · จับคู่ไม่ได้ = reject รายแถวพร้อม reason",
             "reject รายแถวต้องไม่ทำให้ทั้งไฟล์ fail — สรุปจำนวนใน metrics และแนบไปในอีเมลแจ้งผล"],
            ["ยอดขายครบพอคำนวณ Growth หรือยัง",
             "`sgi_sales_transactions` (ยอดรายวัน) → สรุปลง `sgi_fgi_impact_sales_summaries` (`total_working_days` · `growth_rate_before/after/diff` · `sales_status`)",
             "🔴 **แก้ 2026-09-13 — เดิมเอกสารเขียนกลับด้านกับโค้ดจริง** · ระบบเดิม **คำนวณ Growth ให้ทุกแถวเสมอ** "
             "ไม่ว่าวันจะครบ 60 หรือไม่ (`ImportJdbc.calculateGrowthRateAndTotalDiffRateImpactStoreSalesTrn` "
             "กรองด้วย `FLAG_VERIFY` อย่างเดียว ไม่มีเงื่อนไขจำนวนวัน) · และวันไม่ครบมักทำให้ "
             "`growth_rate_diff` เป็น **NULL** ซึ่ง `NVL(GROWTH_RATE_DIFF,-1) < 0` ตีเป็น **`'Y'`** — "
             "**ตรงข้ามกับที่เอกสารเดิมเขียนว่า \"ไม่ครบ = ยังไม่เป็น Y\"**",
             "`pre-accept` **ไม่ใช่คอลัมน์ที่เก็บ** — ปลายทางคำนวณเองจาก `total_working_day != 60 OR growth_rate_diff IS NULL` "
             "(`ExportJdbc.java:968`) · Job 5 มีหน้าที่บันทึก `total_working_days` ให้ตรงความจริงเท่านั้น · "
             "⚠️ ระบบเดิมใช้ `!=` ไม่ใช่ `<` — ข้อมูล**เกิน** 60 วันก็เข้า pre-accept ด้วย "
             "ขณะที่หน้าจอรายการใช้ `< 60` ตีแถวแดง (สองกติกานี้ไม่ตรงกันมาแต่เดิม)"],
        ],
        "domains": [
            ["รูปแบบชื่อไฟล์", "`AMS06001I_YYYYMMDDHHMM.txt`", "regex ใน `ImportController.importImpactSaleFromIAS`"],
            ["encoding ของไฟล์",
             "ประกาศเป็น WINDOWS-874 แต่ไฟล์จริง **เป็น ASCII ล้วน ไม่มีไบต์ภาษาไทยเลย** · "
             "วันที่ในไฟล์เป็น **ค.ศ.** (`20260824`) **ไม่ใช่ พ.ศ.**",
             "🔴 แก้ 2026-09-16 จากไฟล์ตัวอย่างจริง `docs/file_IAS_STA/` — เอกสารเดิมเขียนว่าเป็น พ.ศ. ซึ่งผิด · "
             "ที่เป็น พ.ศ. + windows-874 จริงคือ `FRBC0001` ของ STA (Job 6) เท่านั้น · "
             "รายละเอียด `docs/IAS-STA-interface-files.md`"],
            ["จำนวนวันทำการขั้นต่ำ", "60 วัน", "`FgiConstant.TOTAL_INTERVAL_DAY = 60`"],
            ["`sales_status`",
             "`W` = รอ · `P` = ส่งคำขอแล้วรอผล (Job 4 ตั้ง) · `Y` = เข้าเกณฑ์ชดเชย · `N` = ไม่เข้าเกณฑ์ · `E` = ผิดพลาด",
             "`CHECK` ใน DDL · Job 5 แตะเฉพาะแถวที่เป็น `'P'` เท่านั้น (กันทับผลที่คนแก้ไปแล้ว)"],
            ["`sales_diff` ของแถวรายวัน",
             "**เปอร์เซ็นต์** = `ROUND((ยอดวันนั้น − ค่าเฉลี่ยของหน้าต่าง) / **ยอดวันนั้น** × 100)`",
             "`ImportJdbc.java:544` · ⚠️ หารด้วยยอดของวันนั้นเอง ไม่ใช่หารด้วยค่าเฉลี่ย — **หน่วยเป็น % ไม่ใช่บาท**"],
            ["`is_outlier`", "`|sales_diff| >= 50` (เปอร์เซ็นต์)",
             "`ImportJdbc.java` — `CASE WHEN ABS(T.DIFF_*) >= 50 THEN 1 ELSE 0 END`"],
            ["ตัวกรองจับคู่วันตอนเฉลี่ย",
             "ถ้าหน้าต่างปีก่อนกับปีนี้ **มี outlier ไม่เหมือนกัน** วันที่ธง outlier ไม่ตรงกันจะถูกแทนด้วย **0** "
             "แต่ **ยังนับอยู่ในตัวหาร** (ตัวหารคงเป็น 15)",
             "`ELSE 0` ในสูตร AVG ของเดิม — **ไม่ใช่การตัดวันนั้นทิ้ง** · เขียนเป็น `WHERE` แล้วผลจะต่างทันที · "
             "จับคู่ด้วย `seq` (ตารางเดิมเป็นตารางกว้างจึงจับคู่ได้ในแถวเดียว ตารางใหม่แคบจึงต้องมีคอลัมน์ `seq`)"],
        ],
    },
    "6": {
        "intro": "Job 6 มี **2 สวิตช์ที่เปลี่ยนผลลัพธ์ของทั้งรอบ** และทั้งคู่ถูกตัดสิน **ก่อน** เปิด transaction — implement ผิดจะส่งข้อมูลผิดชุดให้ STA โดยไม่มี error ให้เห็น",
        "rules": [
            ["รอบนี้จะสร้างชุด `I` (Initial) ให้ STA หรือไม่",
             "`processDate` (argument · ดู 5.95) เทียบกับค่าคงที่ `dateStartInitToSTA`",
             "`dd` ของ `processDate` **≥ 7** → สร้างชุด Initial ของงวด (log `Create Data`) · `< 7` → ไม่สร้าง (log `No Create Data`) แต่ยังส่งชุด `A`/`N`/`S` ตามปกติ",
             "ค่านี้อยู่ใน `ApplicationResources.properties` ของระบบเดิม → ระบบใหม่ต้องเป็น env ไม่ใช่ค่าฝังในโค้ด"],
            ["ข้อมูล QSSI ของงวดครบหรือยัง",
             "`fcs_qssi_score` (ตารางของระบบ SBP เดิม · SGI **อ่านอย่างเดียว**) — `year` · `month` · `category`",
             "งวดที่ตรวจ = **เดือนก่อนหน้า `processDate`** · ต้องมีข้อมูล **ครบทุกหมวดใน 6 หมวด `8, 9, 12, 1, 10, 16`** · **หมวดใดหมวดหนึ่ง count = 0 → ไม่ครบทันที** (ระบบเดิม `break` แล้วตั้ง `countRow = 0`)",
             "ไม่ครบ → ชุดที่ส่งออกเปลี่ยนไป (**ไม่ใช่ job fail**) · ⚠️ ระบบเดิม **กลืน exception ของคิวรีนี้เป็น 0 ด้วย** — ระบบใหม่ต้องแยก \"ไม่ครบ\" ออกจาก \"คิวรีพัง\" และ log ต่างกัน"],
            ["แถวไหนถูกส่งออก และส่งด้วยสถานะอะไร",
             "`sgi_fgi_impact_compensations.compensate_status`",
             "ส่ง `A` (อนุมัติชดเชย) · `N` (เห็นควรไม่ชดเชย) · `S` (หยุดชดเชย) เสมอ · เพิ่ม `I` เมื่อสวิตช์ข้อ 1 และ 2 จริงพร้อมกัน · **`Z` (ยอดเป็นศูนย์) แปลงเป็น `S` เฉพาะใน payload — ใน DB ยังเป็น `Z`**",
             "`R` (Reflow) **ไม่ได้มาจาก job นี้** — เกิดจากปุ่มเปิดพิจารณาใหม่ที่ `POST /sgi/document/{docNo}/actions` (ดู `LLDD-BE-API-Document-Workflow-Actions` §5.1c)"],
            ["ปิดรอบชดเชยหรือพักไว้",
             "`sgi_fgi_impact_processes.flag_action`",
             "ส่งผลชดเชยของงวดครบแล้ว → `Y → N` (ปิดรอบ) · ยังรอจ่ายอีก → `Y → W` (พัก)",
             "`flag_action` เป็น input ของ **จุดเข้า flow ชั้นที่ 1 ใน Job 8b** — เขียนผิดที่นี่ทำให้เอกสารรอบหน้าเข้าผิดขั้น"],
        ],
        "gaps": [
            ["**G5** ✅ ปิดแล้ว 2026-09-02", "`compensate_status VARCHAR(5)` เดิม **ไม่มีทั้ง CHECK และคำอธิบายโดเมนใน DDL** และค่า `'C'` ไม่มีนิยาม", "อ่าน `ExportJdbc.insertFgiImpactStoreCompensate()` (บรรทัด 395-460) แล้วพบนิยามของ `'C'` — ดูตาราง \"โดเมนของ `compensate_status`\" ด้านล่าง · เติมโดเมนครบ + กฎ map ลง DDL แล้ว (`CHECK IN ('I','C','A','N','S','Z')`)"],
        ],
        "domains": [
            ["`dateStartInitToSTA`", "`7`", "`ApplicationResources.properties` ของระบบเดิม"],
            ["`categoryQssi`",
             "`8,9,12,1,10,16` (6 หมวด) → **8 = Result · 9 = Process · 12 = สินค้าขาด · "
             "1 = บริการ · 10 = Follow up · 16 = สินค้าหมดอายุ** (ลำดับนี้คือลำดับฟิลด์ 9–14 ของ `FRBC0001`)",
             "`ApplicationResources.properties` · **ชื่อหมวดถอดได้ 2026-09-16** จากรายงาน `RT040035` ของ STA "
             "เทียบกับไฟล์ `FRBC0001` จริงร้านเดียวกันงวดเดียวกัน (ตรงทุกค่า ยืนยัน 3 ร้าน) — "
             "ดู `docs/IAS-STA-interface-files.md` · ⚠️ **เปอร์เซ็นต์หักคำนวณที่ STA ไม่ใช่ที่ SGI** "
             "SGI ส่งแค่คะแนนดิบ · หมวด Follow up **ติดลบได้**"],
            ["`numWaitPay`", "`3` งวด", "`ApplicationResources.properties`"],
            ["`compensate_status` ที่ STA รับได้", "`I` · `A` · `N` · `S` · `R`", "`STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md` §2.2"],
            ["ค่าที่มีใน DB แต่ไม่ส่งดิบ ๆ", "`Z` และ **`C`** → แปลงเป็น **`S`** เฉพาะใน payload (ใน DB คงค่าเดิม)", "ขั้นที่ 4 ของ Job 6 · `ExportJdbc` จัด `C`/`S`/`Z` เป็นกลุ่มเดียวกันในทุก filter ปลายน้ำ (บรรทัด 366 · 1440)"],
        ],
        "status_table": ("โดเมนของ `compensate_status` ครบทุกค่า (สืบจาก `FgiConstant` + `ExportJdbc`)", [
            ["`I`", "**Initial** — ข้อมูลตั้งต้นของงวด (ร้านยังเปิดและสัญญายังไม่จบ)", "ส่ง `I`", "`FGI_COMPESATE_STATUS_I`"],
            ["`C`", "**Closed/Cancelled** — ตอน insert แถวงวดนั้นพบว่า **ร้านปิดไปแล้ว** (`mas_store.close_date <= งวด`) **หรือ สัญญา SBP ถูกยกเลิกก่อน/ในงวดนั้นด้วยเหตุ `cancel_type IN ('01','02','03','04','08')`** — ตั้งแทน `I` ตั้งแต่แรก", "**ส่ง `S`** (STA ไม่รับค่า `C`) — กลุ่มเดียวกับ `S`/`Z` ในทุก filter ปลายน้ำ", "`ExportJdbc` บรรทัด 404 · 414 · 452 (CASE ตอน insert) · 366 · 1440 (filter)"],
            ["`A`", "**Approve** — อนุมัติชดเชย", "ส่ง `A`", "`FGI_COMPESATE_STATUS_A`"],
            ["`N`", "**Not Approve** — เห็นควรไม่ชดเชย", "ส่ง `N`", "`FGI_COMPESATE_STATUS_N`"],
            ["`S`", "**Stop** — หยุดชดเชยประกันรายได้", "ส่ง `S`", "`FGI_COMPESATE_STATUS_S`"],
            ["`Z`", "**Zero** — ยอดชดเชยของงวดเป็นศูนย์", "**ส่ง `S`** (แปลงเฉพาะใน payload · ใน DB ยังเป็น `Z`)", "`FgiConstant.FLAG_VERIFY_Z`"],
            ["`R`", "**Reflow** — เปิดพิจารณาใหม่", "เป็นค่าของ **message เท่านั้น ไม่เคยลง DB** — สร้างโดย `POST /sgi/document/{docNo}/actions`", "สเปก STA §2.2 + `LLDD-BE-API-Document-Workflow-Actions` §5.1c"],
        ]),
        "sql_title": "SQL ตรวจความครบของ QSSI — **ต้องแยกทีละหมวด ห้าม `IN (...)` รวบเดียว**",
        "sql_note": "ระบบเดิมวนตรวจ **ทีละหมวด** แล้ว break ทันทีที่เจอหมวดว่าง · เขียนเป็น `category IN (8,9,12,1,10,16)` แล้วนับรวมจะได้ผลต่างกัน (มีข้อมูลหมวดเดียวก็ผ่าน) ซึ่ง **ผิด** และจะส่งชุด Initial ผิดให้ STA",
        "sql": """-- ตรวจทีละหมวด · หมวดใดได้ 0 ให้หยุดทันทีและถือว่า "ไม่ครบ"
SELECT q.category, COUNT(1) AS count_rec
FROM fcs_qssi_score q                      -- schema sps_store · SGI อ่านอย่างเดียว
WHERE q.year  = :qssi_year                 -- ปีของ "เดือนก่อนหน้า processDate"
  AND q.month = :qssi_month                -- เดือนก่อนหน้า processDate
  AND q.category = ANY(:qssi_categories)   -- {8, 9, 12, 1, 10, 16}
GROUP BY q.category;
-- ครบ ก็ต่อเมื่อ จำนวนหมวดที่คืนมา = 6 และทุกหมวด count_rec > 0
-- คิวรี throw = ต้อง log error แล้วหยุดรอบ ห้ามกลืนเป็น "ไม่ครบ" แบบระบบเดิม""",
    },
    "7": {
        "intro": "Job 7 คัดลอกคู่แข่งจากโซน A เข้าเอกสาร — เรื่องที่ต้องชัดคือ **แถวไหนลบได้ แถวไหนห้ามแตะ** เพราะเอกสารเดียวกันมีทั้งแถวที่ระบบใส่และแถวที่คนคีย์เอง",
        "rules": [
            ["เอกสารนี้ต้อง sync หรือไม่",
             "`sgi_compensation_documents` (`doc_no` · สถานะเอกสาร) + `sgi_fgi_impact_competitors` ของรอบเดียวกัน",
             "เอกสารที่ยังไม่จบและมีข้อมูลคู่แข่งของรอบนั้นอยู่ · ส่ง `docNo` มาก็จำกัดเฉพาะเอกสารนั้น (ดู 5.95)",
             "ไม่มีข้อมูลต้นทาง = ข้ามเอกสารนั้น ไม่ลบของเดิมทิ้ง"],
            ["แถวนี้ลบได้หรือไม่ (prune)",
             "`sgi_document_competitors.source_system`",
             "ลบได้เฉพาะแถวที่ `source_system = 'ALLMAP'` และไม่มีอยู่ในชุดต้นทางปัจจุบันแล้ว",
             "⛔ **แถว `source_system = 'USER'` (คนคีย์เอง) ห้ามลบทุกกรณี** — รวมถึงตอนส่ง `docNo` มาเจาะจง"],
            ["แถวซ้ำ",
             "`UNIQUE (doc_no, competitor_store_code)`",
             "upsert ด้วยคีย์นี้ — ค่าจากต้นทางชนะค่าที่ระบบเคยใส่ไว้",
             "ชน unique = อัปเดตแถวเดิม ไม่ใช่ error"],
        ],
        "domains": [
            ["`source_system`", "`ALLMAP` = ระบบนำเข้าให้ (ลบ/อัปเดตได้) · `USER` = คนคี่ย์เอง (**ห้ามแตะ**)", "คอลัมน์ `source_system` ของ `sgi_document_competitors`"],
        ],
    },
    "8": {
        "intro": "Job 8 สร้างเอกสารประกันรายได้ — 2 เรื่องที่ต้องชัดคือ **รอบไหนได้เอกสาร** และ **เลขเอกสารจองอย่างไรไม่ให้ชนกัน**",
        "rules": [
            ["รอบชดเชยนี้ได้เอกสารหรือยัง",
             "`sgi_fgi_impact_processes.id` เทียบกับ `sgi_compensation_documents.impact_process_id` (`UNIQUE`)",
             "มีเอกสารของ `impact_process_id` นั้นอยู่แล้ว = **skip** และคืน `doc_no` เดิม",
             "ห้ามสร้างเอกสารใบที่ 2 ให้รอบเดียวกัน — นี่คือกลไกกัน rerun ซ้ำหลักของ job นี้"],
            ["รอบนี้พร้อมสร้างเอกสารหรือยัง",
             "`sgi_fgi_impact_processes.flag_action` · `sgi_fgi_impact_sales_summaries.sales_status` ของรอบเดียวกัน",
             "รอบต้อง active (`flag_action IN ('Y','W')`) และมียอดขาย/Growth ที่คำนวณแล้ว (`sales_status = 'Y'`)",
             "ยังไม่พร้อม = ข้ามรอบนี้ ให้รอบถัดไปหยิบ (ไม่ใช่ error)"],
            ["เลขเอกสารเป็นอะไร",
             "`sgi_document_running_numbers` (`year` · `running_no`) · `UNIQUE(year, running_no)`",
             "รูปแบบ `YYYY/xxxxx` ด้วย **ปี ค.ศ.** · lock running number ต่อปีภายใน transaction เดียวกับการ insert เอกสาร",
             "**ช่องว่างของเลขเป็นเรื่องปกติ** (rerun/conflict) — เลขรับประกันแค่ไม่ซ้ำ ไม่รับประกันความต่อเนื่อง และ **ห้าม reuse เลขที่จองไปแล้ว**"],
        ],
        "domains": [
            ["รูปแบบเลขเอกสาร", "`YYYY/xxxxx` · ปี **ค.ศ.**", "มติ 2026-08-06 (ทั้งระบบเป็น ค.ศ. ยกเว้นไฟล์ interface)"],
            ["`flag_action` ที่ถือว่า active", "`Y` · `W`", "โดเมนเดิมของ `FGI_IMPACT_STORE_ON_PROCESS`"],
        ],
    },
    "8b": {
        "intro": "เงื่อนไขตัดสินของ Job 8b คือ **จุดเข้า flow 2 ชั้น** ในหัวข้อ 4a ของเอกสารฉบับนี้ — ตารางนี้สรุปเฉพาะ \"ตัดสินจากคอลัมน์ไหน\" เพื่อให้เขียนโค้ดได้โดยไม่ต้องเลื่อนกลับไปอ่าน",
        "rules": [
            ["ชั้นที่ 1 — เปิดเรื่องใหม่ หรือ ต่อเนื่อง",
             "`sgi_fgi_impact_processes.last_compensate_seq_no` · `.flag_action`",
             "`last_compensate_seq_no = 1` → **① เปิดเรื่องใหม่** · `> 1` **และ** `flag_action = 'Y'` → **② ต่อเนื่อง**",
             "① เปิด workflow ที่ state `06` · ② ไปตัดสินชั้นที่ 2 ต่อ"],
            ["ชั้นที่ 2 — (เฉพาะเคส ②) ยอดชดเชยผ่านเกณฑ์หรือไม่",
             "`sgi_fgi_impact_compensations.adjust_amount` · `.forecast_amount` · `.compensate_seq` · `.compensate_seq_no`",
             "ยอดที่ใช้ = `COALESCE(adjust_amount, forecast_amount)` · **ผ่าน** เมื่อ ยอด > 0 **หรือ** ยอด = 0 ติดกันงวดที่ 1-3 · **ไม่ผ่าน** เมื่อ ยอด = 0 ติดกันงวดที่ 4 ขึ้นไป",
             "ผ่าน → Auto Approve เปิด workflow ที่ state `08` (ข้ามขั้น 06) · ไม่ผ่าน → **ไม่เปิด workflow** ปิดเอกสารเป็น `99` ผลการพิจารณา \"หยุดชดเชยประกันรายได้\""],
            ["เอกสารนี้เปิด workflow ไปแล้วหรือยัง",
             "`sps_store.workflow_transaction.reference_id` · `.version_id`",
             "มีแถวที่ `reference_id = sgi_compensation_documents.id::text` **และ** `version_id = :sgi_version_id` = เปิดไปแล้ว",
             "เปิดแล้ว = **skip** ไม่เรียก `initializeWorkflow` ซ้ำ (นับเป็น `skipped`) — กลไกกัน rerun ซ้ำหลักของ job นี้"],
            ["ใครเป็นผู้รับผิดชอบขั้นแรกของเคสต่อเนื่อง",
             "`sgi_consideration_logs.consider_by` ของเอกสารรอบก่อนหน้าของร้านเดียวกัน",
             "หาแถวล่าสุดที่ `section_code` = ขั้นที่จะมอบหมาย ของเอกสารรอบก่อน → `consider_by`",
             "หาไม่เจอ → ปล่อยให้ engine ใช้ group ปกติ (**ห้ามล้ม job**) · เจอ → ผูกด้วย `addPreApprover(...)`"],
            ["ทุกเส้นทางอัตโนมัติต้องทิ้งร่องรอย",
             "`sgi_consideration_logs`",
             "ทั้งเส้นทาง ① ② และเส้นทางหยุดชดเชย ต้อง insert แถวด้วยผู้ดำเนินการ `SYSTEM`",
             "ไม่บันทึก = timeline ของเอกสารขาดช่วง และ resolve เจ้าของงานรอบถัดไปไม่ได้"],
        ],
        "domains": [
            ["`flag_action`", "`Y` = รอบเปิดอยู่ · `W` = พักรอตรวจ · `N` = ปิดรอบแล้ว", "`CHECK` ใน DDL (`IN ('Y','W','N')`)"],
            ["`requestId` ที่ job ส่งให้ BE", "`job8b-{impactProcessId}-{YYYYMM}` (ค.ศ.)", "🔴 มติ 2026-09-09 — job **ไม่รู้จัก `referenceId`** แล้ว เพราะไม่ได้คุยกับ engine เอง · สิ่งที่ job ส่งคือ `impactProcessId` + `requestId` ให้ `POST /sgi/workflow/instances` · การแปลงเป็น `referenceId = sgi_compensation_documents.id` เป็นหน้าที่ของฝั่ง BE"],
            ["state เริ่มต้นที่เป็นไปได้", "`06` หรือ `08` เท่านั้น — **ไม่มี `01`** อีกแล้ว", "มติ 2026-09-01"],
        ],
    },
    "9": {
        "intro": "Job 9 คัดลอกร้านเปิดใหม่เข้าเอกสาร — กติกาเดียวกับ Job 7 เรื่องแถวที่คนคีย์เอง บวกกฎ **%ชดเชยรวมต้องเท่ากับ 100%**",
        "rules": [
            ["แถวนี้ลบได้หรือไม่ (prune)",
             "`sgi_document_new_stores.source_system`",
             "ลบได้เฉพาะ `source_system = 'FGI'` ที่ไม่มีอยู่ในชุด impact ปัจจุบันแล้ว",
             "⛔ **แถว `source_system = 'USER'` ห้ามลบทุกกรณี** ไม่ว่าจะส่ง argument แบบไหน"],
            ["%ชดเชยของเอกสารถูกต้องหรือไม่",
             "`sgi_document_new_stores.compensate_percent` (`CHECK BETWEEN 0 AND 100`)",
             "ผลรวมของทุกร้านเปิดใหม่ในเอกสารเดียวกันต้อง **= 100%** พอดี",
             "ไม่เท่า 100% = **ยกเลิกทั้งเอกสารนั้น** พร้อม reason ห้าม commit ครึ่งทาง (เอกสารจะคำนวณยอดผิด)"],
            ["ยอดชดเชยต่อร้านมาจากไหน",
             "`sgi_document_new_stores.compensation_amount` ← `sgi_fgi_impact_stores.forecast_compensation_amount` / `.adjust_compensation_amount`",
             "ใช้ `COALESCE(adjust_compensation_amount, forecast_compensation_amount)` — ค่าที่คนปรับชนะค่าที่ระบบคำนวณเสมอ",
             "ไม่มีทั้งคู่ = 0 (คอลัมน์ `NOT NULL DEFAULT 0`) ไม่ใช่ error"],
        ],
        "domains": [
            ["`source_system`", "`FGI` = ระบบนำเข้าให้ (ลบ/อัปเดตได้) · `USER` = คนคีย์เอง (**ห้ามแตะ**)", "คอลัมน์ `source_system`"],
            ["ผลรวม %ชดเชย", "ต้อง = 100% พอดีต่อ 1 เอกสาร", "กติกาธุรกิจ (SDD GI)"],
        ],
    },
    "10": {
        "intro": "Job 10 เป็น watchdog ของ **ข้อความขาออกที่ยังไม่ถึงปลายทาง** — 🔴 **มติ 2026-09-08 (ข้อ 2.13) เปลี่ยนนิยามจาก \"ACK ระดับธุรกิจ\" เป็น \"publisher confirm ของ RabbitMQ\"** เพราะสเปกของทีม STA มีแค่ 3 ข้อความบน RabbitMQ **ไม่มี ACK แบบ HTTP** — เส้น `POST /sgi/interface/sta/ack` จึงถูกตัดทิ้ง · เงื่อนไขที่ต้องชัดมี 2 ข้อ: \"แถวไหนเรียกว่าค้าง\" และ \"อะไรกันไม่ให้ส่งอีเมลซ้ำ\" · ⚠️ **อย่าสับสนกับงานเตือน/escalation ของเอกสารค้างพิจารณา** ซึ่งเป็นคนละงาน และมีเอกสารของตัวเองแล้วคือ **LLDD-BE-Job-12-NotifyPendingWork** (สร้าง 2026-09-02 · ปิดช่องว่าง G6) — Job 10 ดู **ข้อความ interface ที่ยังไม่ออกจากระบบเรา** ส่วน Job 12 ดู **เอกสารที่ค้างรอคนกดใน workflow**",
        "rules": [
            ["แถวนี้นับว่า **ค้างส่ง** หรือไม่",
             "`sgi_interface_transactions` — `direction` · `outbox_status` · `data_name` · `created_at`",
             "`direction = 'OUT'` **และ** `outbox_status` ยังไม่เป็น `CONFIRMED` **และ** สร้างมาแล้วเก่ากว่า `asOfDate - ageDays` (ค่าตั้งต้น 1 วัน)",
             "ขาเข้า (`IN`) และการส่งต่อภายใน (`INTERNAL`) **ไม่นับ** · 🔴 **มติ 2026-09-08:** เกณฑ์คือ "
             "**publisher confirm ของ broker** (RabbitMQ ตอบว่ารับข้อความแล้ว) ไม่ใช่การรอ ACK จากระบบ STA — "
             "เพราะสเปก STA ไม่มีช่องทาง ACK กลับมา · Job 6 ต้องตั้ง `outbox_status = 'CONFIRMED'` **เฉพาะเมื่อได้ confirm จาก broker เท่านั้น**"],
            ["ส่งอีเมลซ้ำหรือยัง (วันนี้)",
             "`sgi_interface_transactions.last_ack_notified_on` (ชื่อคอลัมน์คงเดิม — ความหมายคือ \"วันที่แจ้งเตือนล่าสุด\")",
             "`last_ack_notified_on` = วันที่ของ `asOfDate` แล้ว → เคยแจ้งไปแล้ววันนี้ → ข้าม",
             "อัปเดต marker **หลังส่งอีเมลสำเร็จเท่านั้น** — marker นี้ย้ายมาจาก `audit_logs` ที่ถูกยกเลิก 2026-08-07"],
        ],
        "domains": [
            ["ค่าตั้งต้น `ageDays`", "1 วัน", "ระบบเดิมคัดรายการที่ยังไม่มี `return_code`"],
            ["สัญญาณที่ถือว่า \"ส่งถึงแล้ว\"", "**publisher confirm ของ RabbitMQ** (`channel.waitForConfirms()` / `amqp-connection-manager` callback)", "🔴 มติ 2026-09-08 — สเปก STA มีแค่ 3 ข้อความบน MQ **ไม่มี ACK แบบ HTTP** เส้น `POST /sgi/interface/sta/ack` จึงถูกตัด · ไม่มีการรอ ACK ระดับธุรกิจอีกต่อไป"],
            ["`direction`", "`OUT` = ส่งออกไประบบภายนอก · `IN` = รับกลับ · `INTERNAL` = ส่งต่อภายในระบบ (Jobs 7/8/9)", "คอมเมนต์ใน DDL"],
        ],
        "gaps": [
            ["**G6** ✅ ปิดแล้ว 2026-09-02", "**งานเตือนงานค้าง + escalation 30/45/60 วัน** เดิมไม่มีเอกสารและไม่มีชั่วโมง — ตอนนี้แยกเป็นเอกสารของตัวเองแล้ว: **`LLDD-BE-Job-12-NotifyPendingWork`** (13 ชั่วโมง · เจ้าของ Aphiwit <Bank> Khammoon) ครอบคลุม `SendMailReport.java` / `MailReportService.java` ของระบบเดิมครบ · ข้อค้างที่เหลือย้ายไปอยู่ในเอกสารฉบับนั้นแล้ว (G7 = วันที่ พ.ศ. ในอีเมล · G8 = ไม่มี marker กันส่งซ้ำ)", "ดู **LLDD-BE-Job-12-NotifyPendingWork** หัวข้อ 5.96"],
        ],
    },
}


def _has_open_gap(gaps: list[list[str]]) -> bool:
    """ยังมีข้อค้างจริงไหม — แถวที่ขึ้นต้นด้วย ✅ ถือว่าปิดแล้ว"""
    return any("✅" not in str(row[0]) for row in gaps)


def job_decision_rule_blocks(job_no: str, section: str) -> list[dict[str, Any]]:
    """5.9x — เงื่อนไขตัดสินระดับตาราง.คอลัมน์ ให้ dev อ่านแล้วเขียนโค้ดได้เลย"""
    spec = JOB_DECISION_RULES.get(job_no)
    if not spec:
        return []
    out: list[dict[str, Any]] = [
        h(2, f"{section} เงื่อนไขตัดสิน (Decision Rules) — ตัดสินจากอะไร"),
        p(spec["intro"]),
        table(["คำถามที่โค้ดต้องตอบ", "ตัดสินจาก (ตาราง · คอลัมน์)", "เงื่อนไขที่ต้องเป็นจริง", "ไม่เข้าเงื่อนไขแล้วทำอะไร"], spec["rules"]),
    ]
    if spec.get("gaps"):
        out.extend([
            # หัวข้อเปลี่ยนตามสถานะจริง — ถ้าทุกข้อปิดหมดแล้วห้ามยังพาดหัวว่า "ต้องปิดก่อน implement"
            h(3, ("⚠️ ช่องว่างของ schema ที่ต้องปิดก่อน implement เงื่อนไขข้างบนได้จริง"
                  if _has_open_gap(spec["gaps"]) else
                  "ช่องว่างที่เคยค้างของหัวข้อนี้ — ปิดครบแล้ว (เก็บไว้เป็นประวัติ)")),
            p("แถวในตารางนี้ไม่ใช่ \"ข้อควรระวัง\" แต่เป็น **ของที่ยังไม่มีในโครง 21 ตาราง** — เขียนโค้ดตามเงื่อนไขด้านบนแล้วจะ compile ไม่ผ่าน/คิวรีพังทันที"
              if _has_open_gap(spec["gaps"]) else
              "ทุกข้อปิดแล้ว — เก็บตารางไว้เพื่อให้ตามรอยได้ว่าเคยค้างอะไรและปิดด้วยอะไร"),
            table(["#", "สิ่งที่ขาด", "ต้องทำอะไรก่อน"], spec["gaps"]),
        ])
    if spec.get("domains"):
        out.extend([
            h(3, "ค่าคงที่และโดเมนที่ใช้ในเงื่อนไขข้างบน"),
            p("ทุกค่าในตารางนี้ต้องอ่านจาก config/env ไม่ hardcode ในคิวรี — แต่ **ค่าตั้งต้นต้องเท่าระบบเดิมทุกตัว** ไม่งั้นผลลัพธ์จะไม่ตรงกันตอนเทียบ UAT"),
            table(["ค่า", "โดเมน / ค่าที่ระบบเดิมใช้", "ที่มา"], spec["domains"]),
        ])
    if spec.get("extra_table"):
        title, rows = spec["extra_table"]
        out.extend([h(3, title), table(["รายการ", "กติกาที่ระบบเดิมใช้จริง", "ที่มา / ข้อควรระวัง"], rows)])
    if spec.get("status_table"):
        title, rows = spec["status_table"]
        out.extend([
            h(3, title),
            p("ค่าเหล่านี้ไม่ได้อยู่ใน DDL เดิมเลย · สืบจากโค้ดจริงของระบบเดิมทั้งหมด — **`C` เป็นค่าที่ระบบเดิมตั้งตอน insert ไม่ใช่ค่าที่คนเลือก** จึงต้องรองรับตั้งแต่ migration รอบแรก"),
            table(["ค่าใน DB", "หมายความว่าอะไร", "ส่งอะไรให้ STA", "ที่มาในโค้ดเดิม"], rows),
        ])
    if spec.get("sql"):
        out.append(h(3, spec.get("sql_title", "SQL อ้างอิง")))
        if spec.get("sql_note"):
            out.append(p(spec["sql_note"]))
        out.append(code(spec["sql"], "sql"))
    if spec.get("sql2"):
        out.append(h(3, spec.get("sql2_title", "SQL อ้างอิง (ต่อ)")))
        out.append(code(spec["sql2"], "sql"))
    return out


JOB_IMPLEMENTATION_SPECS: dict[str, dict[str, str]] = {
    "11": {
        "repository": "staCompensateRepository",
        "read": """-- กันซ้ำ: ข้อความเดิมเคยประมวลผลไปแล้วหรือยัง
SELECT 1
FROM sgi_interface_transactions
WHERE data_name = 'STA_UPDATE_COMPENSATE'
  AND direction = 'IN'
  AND business_key = :business_key      -- storecode_i:storecode_n
  AND period_key   = :compensate_month  -- 'YYYY-MM' (แปลงจาก yyMM พ.ศ. ในข้อความแล้ว)
LIMIT 1;""",
        "write": """INSERT INTO sgi_interface_transactions
    (run_id, data_name, direction, status, impact_process_id, business_key, period_key, purge_after)
VALUES (:run_id, 'STA_UPDATE_COMPENSATE', 'IN', 'COMPLETED', :impact_process_id,
        :business_key, :compensate_month, CURRENT_TIMESTAMP + INTERVAL '180 days')
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;

UPDATE sgi_fgi_impact_compensations
SET forecast_amount = COALESCE(:forecast_amount, forecast_amount),
    adjust_amount   = COALESCE(:adjust_amount, adjust_amount),
    updated_by = 'STA', updated_at = CURRENT_TIMESTAMP
WHERE impact_process_id = :impact_process_id
  AND compensate_month  = :compensate_month;""",
        "idempotency": "UNIQUE(data_name,direction,business_key,period_key) ของ sgi_interface_transactions — ข้อความเดิมที่ redeliver ต้อง ack ทิ้งโดยไม่แก้ยอดซ้ำ",
        "transaction": "insert outbox ขาเข้า + update ยอด อยู่ transaction เดียวกัน แล้วจึง ack ข้อความ; commit ไม่ผ่าน = nack + requeue (ครบ 3 ครั้งเข้า DLQ)",
        "security": "RabbitMQ ใช้ secretRef=secret/sgi/mq/sta ผ่าน AMQPS (TLS 1.2+ verify-full); ชื่อ queue/exchange มาจาก config ไม่ใช่ค่าที่ผู้ใช้แก้ได้",
        "steps": "connectAndDrainQueue|validateEnvelope|skipDuplicateMessage|applyCompensateAmount",
    },
    "12": {
        "repository": "pendingWorkRepository",
        "read": """SELECT d.doc_no, d.impact_process_id, d.current_section_code,
       ist.store_code AS impacted_store_code, ms.region AS zone_code,
       (CURRENT_DATE - date_trunc('day', w.update_date)::date) AS waiting_days
FROM sps_store.workflow_transaction w                 -- ⚠️ ไม่มี PK/index — ประเมินต้นทุน query ก่อนใช้
JOIN sgi_compensation_documents d ON d.id::text = w.reference_id
JOIN sgi_impacted_stores ist ON ist.store_code = d.impacted_store_code
JOIN mas_store ms ON ms.branch_id = ist.store_code
WHERE w.version_id = :sgi_version_id
  AND w.current_state_id = ANY(:waiting_state_ids)     -- เฉพาะ state ที่รอคนกด (แทน stepID 501001 เดิม)
  -- ช่วงวันค้าง 3 ช่วงตาม FgiConstant (30-36 · 45-51 · 60-66)
  -- ⚠️ `BETWEEN ANY (...)` **ไม่ใช่ syntax ของ PostgreSQL** (แก้ 2026-09-04) — `ANY` ใช้ได้กับตัวเปรียบเทียบ
  --    เดี่ยว ๆ อย่าง `= ANY(...)` เท่านั้น · ช่วงหลายช่วงต้องกาง 2 อาร์เรย์แล้ว unnest คู่กัน
  AND EXISTS (
        SELECT 1
        FROM unnest(:win_lo::int[], :win_hi::int[]) AS win(lo, hi)
        WHERE (CURRENT_DATE - date_trunc('day', w.update_date)::date) BETWEEN win.lo AND win.hi)
ORDER BY ms.region, waiting_days DESC;""",
        "write": """-- job นี้ไม่เขียนตารางของ SGI เลย — email-lib เขียน email_sent ให้เอง
-- บันทึกผลการรันไปที่ integration_log ผ่าน main.ts (อัตโนมัติ) + structured log BATCH_END""",
        "idempotency": "ส่งสัปดาห์ละครั้งตาม cron; รันซ้ำวันเดียวกันจะส่งซ้ำ — ถ้าต้องกันซ้ำให้ใช้ marker เดียวกับ Job 10 (last_notified_on) ซึ่งยังไม่มีในโครง (ดูช่องว่าง)",
        "transaction": "อ่านอย่างเดียว ไม่มี DB transaction; ส่งเมลล้มเหลวรายโซนต้องไม่ทำให้โซนอื่นไม่ได้รับ (รวบ error แล้วรายงานท้ายรอบ)",
        "security": "อ่าน business_user ของระบบเดิมได้เฉพาะคอลัมน์อีเมล/กลุ่ม; ห้าม log อีเมลผู้รับแบบเต็มใน application log",
        "steps": "loadPendingWorkFromEngine|bucketByAgeWindow|groupByZone|sendZoneEmails",
    },
    "2": {
        "repository": "impactStoreRepository",
        "read": """-- ⚠️ วิวต้นทางอยู่บน **SQL Server** (GSMALLMAP) ไม่ใช่ PostgreSQL
--    ชื่อคอลัมน์เป็นของวิวจริง (ตัวพิมพ์ใหญ่) · placeholder เป็น ? ของ JDBC/mssql ไม่ใช่ $n/:name
--    และ **ห้ามใช้ ANY()/CASE แบบ PostgreSQL** ที่นี่ — ต้องรันได้บน SQL Server
SELECT STORECODE_I, NAME_I, OPENDATE_I, ZONE_I, SUBZONE_I, BRANCHTYPE_I,
       STORECODE_N, NAME_N, OPENDATE_N, ZONE_N, SUBZONE_N, BRANCHTYPE_N,
       RADIUS, RADIUS_UNIT, DISTANCE, DISTANCE_UNIT, URL_EMBEDDED,
       PERIOD_YEAR, PERIOD_MONTH
  FROM (
    SELECT *,
           ROW_NUMBER() OVER (
             PARTITION BY STORECODE_I, STORECODE_N, PERIOD_YEAR, PERIOD_MONTH
             -- 🔴 ORDER BY ของระบบเดิมใช้คอลัมน์ที่อยู่ใน PARTITION BY อยู่แล้ว จึงเลือกแถวแบบ
             --    non-deterministic · ต้องกำหนด tie-breaker จริง (เช่น DISTANCE ASC) ก่อนใช้งาน
             ORDER BY DISTANCE ASC, STORECODE_N ASC
           ) AS ROW_NUM
      FROM allmapssa.SEVEN_IMPACT_VIEW
     WHERE PERIOD_MONTH = ? AND PERIOD_YEAR = ?      -- ✅ ปีเป็น **ค.ศ.** (ยืนยันจากข้อมูลจริง 2026-09-12 · ข้อ 4.4 ปิดแล้ว)
       -- โซน: ระบบเดิมต่อสตริงเข้า IN (...) ตรง ๆ = ช่อง SQL injection
       --      ระบบใหม่ต้อง bind ทีละค่า + whitelist โซนจาก master
       AND (? IS NULL OR ZONE_I IN (/* bind ทีละค่า */))
  ) A
 WHERE ROW_NUM = 1;

-- 🔴 ระบบเดิม **ไม่ได้กรองรัศมี 1/2 กม. ซ้ำในคิวรีนี้** — ถือว่า ALLMAP คัดมาให้แล้ว
--    ถ้าจะเพิ่มการกรองในระบบใหม่ = requirement ใหม่ ต้องขอ business sign-off ก่อน
--    (และต้องแปลง DISTANCE ตาม DISTANCE_UNIT ก่อนเทียบ — วิวส่งหน่วยมาแยกคอลัมน์)""",
        "write": """-- ⚠️ ต้องเป็น DO NOTHING ไม่ใช่ DO UPDATE — ระบบเดิมไม่อัปเดตคู่ร้านที่มีอยู่แล้วเลย
--    (ImpactStoreService บรรทัด 45-51 สร้าง updateList ขึ้นมาแต่ manageImpactStore() เรียกเฉพาะ insertList)
--    เขียนเป็น DO UPDATE จะทับค่าที่คนแก้ไว้ในเอกสารรอบก่อน — ดูหัวข้อเงื่อนไขตัดสินข้อ ข.
-- FK บังคับลำดับ 3 ขั้น — ข้ามขั้นไหนก็ insert ไม่ผ่าน
--   sgi_impacted_stores -> sgi_fgi_impact_processes -> sgi_fgi_impact_stores

-- ขั้นที่ 1: ร้านที่ถูกกระทบต้องมีก่อน (FK ของอีกสองตาราง)
--   Job 2 มีแค่ store_code · คอลัมน์อื่น (dv_code · opt_dv_user_id · latitude/longitude ·
--   transfer_sbp_date) ไม่มีข้อมูล จึง **ห้ามเขียนทับของเดิมด้วยค่าว่าง** -> DO NOTHING
INSERT INTO sgi_impacted_stores (store_code, is_active, updated_at)
VALUES (:impacted_store_code, TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (store_code) DO NOTHING;   -- ตารางนี้ไม่มี created_at (มีแค่ updated_at)

-- ขั้นที่ 2: แถวแม่ของ (ร้าน + งวด) แล้วเอา id กลับมาใช้เป็น FK
--   impact_year · process_status เป็น NOT NULL และไม่มี DEFAULT -> ต้องใส่ค่าเองทั้งคู่
--   ✅ process_status เคาะแล้ว (มติ 2026-09-12) — Job 2 ใส่ 'IMPORTED' เสมอ
INSERT INTO sgi_fgi_impact_processes
    (impacted_store_code, impact_month, impact_year, process_status, flag_action, datasource,
     created_at, updated_at)
VALUES (:impacted_store_code, :impact_month, :impact_year,
        :process_status,  -- 'IMPORTED' — สถานะเริ่มต้นของวงจร (DDL มี DEFAULT ให้แล้วแต่ใส่ชัดเจนดีกว่า)
        'N',              -- ยังไม่มีรอบชดเชย (มติ 2026-09-13) · Job 6 เปลี่ยนเป็น 'Y' เมื่อรอบเริ่มจริง
        'ALM',            -- ช่องทางต้นทาง · โดเมนจริง ALM/STA/PRO/REA
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
-- ⚠️ ต้องเป็น DO UPDATE ไม่ใช่ DO NOTHING — DO NOTHING ไม่คืนแถวเมื่อคีย์ชน
--    ทำให้ RETURNING id ได้ NULL แล้วขั้นที่ 3 ไม่มี FK จะใส่ (FK violation)
--    DO UPDATE ที่แตะเฉพาะ updated_at จึงได้ id กลับมาเสมอโดยไม่ทับข้อมูลธุรกิจ
ON CONFLICT (impacted_store_code, impact_month) DO UPDATE
   SET updated_at = CURRENT_TIMESTAMP
RETURNING id;   -- ใช้เป็น impact_process_id ของขั้นที่ 3

-- ขั้นที่ 3: คู่ร้าน (ใช้ id จากขั้นที่ 2 เป็น impact_process_id)
INSERT INTO sgi_fgi_impact_stores
    (impact_process_id, impacted_store_code, new_store_code, impact_month, distance_km,
     verify_status, created_by, created_at, updated_at)
VALUES (:impact_process_id, :impacted_store_code, :new_store_code, :impact_month,
        :distance_km,     -- แปลงเป็นกิโลเมตรแล้วเท่านั้น (DDL ไม่มีคอลัมน์หน่วย)
        'W',              -- รอตรวจ · กฎ DENY/ON_PROCESS จะเปลี่ยนเป็น N/P ในขั้นถัดไป
        :created_by,      -- 'ALM' เมื่อมาจากวิว ALLMAP · 'STA' เมื่อระบบ Statement ส่งเข้ามา (ห้ามพึ่ง DEFAULT)
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (impacted_store_code, new_store_code, impact_month) DO NOTHING;
-- sales_request_status ไม่ต้องใส่ — DEFAULT 'W' ของ DDL ให้ค่าอยู่แล้ว และ Job 2 ไม่แตะคอลัมน์นี้""",
        "idempotency": "UNIQUE(impacted_store_code, new_store_code, impact_month) + `ON CONFLICT DO NOTHING`; คู่ร้านที่มีอยู่แล้วต้อง **ข้ามเงียบและนับเป็น `skipped`** ห้ามอัปเดตทับ (พฤติกรรมเดิมของระบบ)",
        "transaction": "**ทั้ง 3 ขั้น (impacted_stores -> impact_processes -> impact_stores) ของ candidate หนึ่งราย ต้องอยู่ใน transaction เดียวกัน** — ห้าม commit แถวแม่แยกจากคู่ร้าน ไม่งั้นจะเหลือแถวแม่ที่ไม่มีลูก; chunk fail rollback เฉพาะ chunk แล้วนับเข้า failedCount; **ห้ามซ้อน transaction สองชั้นแบบระบบเดิม**",
        "security": "ALLMAP connection ใช้ datasource secretRef และ TLS verify-full; job parameter เก็บได้เฉพาะ datasource alias ไม่เก็บ username/password",
        "steps": "loadAllmapCandidates|resolveImpactProcesses|upsertImpactPairs|reconcileImportedPairs",
    },
    "3": {
        "repository": "impactCompetitorRepository",
        "read": """-- ⚠️ วิวต้นทางอยู่บน **SQL Server** (GSMALLMAP) · ชื่อคอลัมน์เป็นของวิวจริง (ตัวพิมพ์ใหญ่)
--    placeholder เป็น ? ของ JDBC/mssql ไม่ใช่ $n/:name · **ห้ามใช้ไวยากรณ์ PostgreSQL ที่นี่**
--    ⚠️ `NAMT` และ `BRANCHT` เป็นชื่อคอลัมน์จริงของวิว ไม่ใช่พิมพ์ผิด (ImpactCompetitorMapper.java:18,20)
--    ระบุคอลัมน์ใน DISTINCT เสมอ — ระบบเดิมใช้ `SELECT distinct *` ซึ่ง dedup ด้วยทุกคอลัมน์ของวิว
--    รวมคอลัมน์ที่ไม่ได้เอาไปใช้ ทำให้แถวซ้ำหลุดเข้ามาได้
SELECT DISTINCT
       STORECODE_I, COMPET_ID, NAMT, NAME, BRANCHT,
       ZONE_CODE, SUBZONE_CODE, OPEN_DATE, CLOSE_DATE,
       PERIOD_YEAR, PERIOD_MONTH
  FROM allmapssa.COMPETITOR_IMPACT_VIEW
 WHERE PERIOD_YEAR = ? AND PERIOD_MONTH = ?;

-- ขั้น resolve (รันบน PostgreSQL หลังอ่านข้อมูลมาแล้ว — คนละฐาน ห้าม join ข้าม)
--   1) STORECODE_I + งวด -> impact_process_id
--      ✅ หาไม่พบ = **ข้ามแถวนั้น** แล้วนับ skippedNoParentCount + alert (มติ 2026-09-13 · ข้อ 2.20)
--      หลักฐาน: ผู้อ่าน FGI_IMPACT_COMPETITOR รายเดียวของระบบเดิมคือคิวรีส่งออกที่
--      ExportJdbc.java:1605-1628 ซึ่ง INNER JOIN ไปแถวแม่ -> คู่แข่งของร้านที่ไม่มีแถวแม่
--      ระบบเดิมก็ไม่เคยใช้เลย · ข้อมูลจริง 228,116 แถว: ไม่มีแถวคู่ร้าน 16,796 แถว
--      ผูกกับรอบชดเชยได้แค่ 14 แถว (0.08%) = 99.92% เป็นข้อมูลตายอยู่แล้ว
--   2) COMPET_ID          -> competitor_store_code (ใช้ตรง ๆ · '' -> NULL)
--   3) NAMT/NAME          -> brand_code ผ่าน master 11 แบรนด์ (map ไม่ได้ = NULL + นับ unmapped)""",
        "write": """INSERT INTO sgi_fgi_impact_competitors
    (impact_process_id, competitor_store_code, brand_code, name_th, name_en, branch_th,
     zone_code, subzone_code, opened_date, closed_date, period_key, updated_at)
VALUES (:impact_process_id, :competitor_store_code, :brand_code, :name_th, :name_en, :branch_th,
        :zone_code, :subzone_code, :opened_date, :closed_date, :period_key, CURRENT_TIMESTAMP)
ON CONFLICT (impact_process_id, competitor_store_code, period_key)
DO UPDATE SET name_th = EXCLUDED.name_th,
              branch_th = EXCLUDED.branch_th,
              opened_date = EXCLUDED.opened_date,
              closed_date = EXCLUDED.closed_date,
              updated_at = CURRENT_TIMESTAMP;""",
        "idempotency": "UNIQUE(impact_process_id, competitor_store_code, period_key) — **คีย์เป็นสาขา ไม่ใช่แบรนด์** (แก้ 2026-09-09); source row ซ้ำในวิวต้อง deduplicate ก่อน upsert · **สัญญาระดับ job คือ period-level skip** — ✅ ปิดแล้ว 2026-09-13 (ข้อ 2.23): คงพฤติกรรมเดิม (งวดมีข้อมูลแล้ว = ข้ามทั้งงวด) **แต่ต้องเทียบ `existingRowCount` กับ `sourceCount` ทุกรอบแล้ว alert เมื่อของเดิมน้อยกว่าต้นทาง** · หลักฐาน: ข้อมูลจริง 88 งวด (2017-2025) **insert จบภายในวันเดียวทั้ง 88 งวด · งวดที่ insert หลายวัน = 0** จึงไม่เคยมีการนำเข้าไม่ครบแล้วเติมทีหลัง และไม่มีคำสั่ง `DELETE FROM FGI_IMPACT_COMPETITOR` ที่ใดเลยทั้ง repo",
        "transaction": "validate งวดก่อนอ่าน; upsert ทีละ chunk และ commit หลัง reconcile จำนวน input/success/reject ของ chunk ตรงกัน",
        "security": "ALLMAP datasource ใช้ secretRef และ TLS verify-full; จำกัด DB user เป็น SELECT เฉพาะ source view",
        "steps": "loadCompetitorPeriod|deduplicateCompetitors|upsertCompetitors|reconcileCompetitorCount",
    },
    "4": {
        "repository": "iasRequestRepository",
        "read": """SELECT s.id, s.impact_process_id, s.impacted_store_code, s.new_store_code, s.impact_month
FROM sgi_fgi_impact_stores s
WHERE s.sales_request_status = 'W'
ORDER BY s.id
FOR UPDATE SKIP LOCKED;""",
        "write": """UPDATE sgi_fgi_impact_stores
SET sales_request_status = 'P', updated_at = CURRENT_TIMESTAMP
WHERE id = ANY(:impact_store_ids) AND sales_request_status = 'W';

INSERT INTO sgi_interface_transactions
    (run_id, data_name, direction, status, impact_process_id, business_key, period_key,
     file_name, file_checksum, outbox_status, purge_after)
SELECT :run_id, 'IAS_SALES_REQUEST', 'OUT', 'READY', impact_process_id,
       impacted_store_code || ':' || new_store_code, impact_month,
       :file_name, :file_checksum, 'READY', CURRENT_TIMESTAMP + INTERVAL '180 days'
FROM sgi_fgi_impact_stores
WHERE id = ANY(:impact_store_ids)
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;""",
        "idempotency": "ชื่อไฟล์ deterministic จาก period+runId และ UNIQUE(data_name,direction,business_key,period_key); outbox retry ใช้ transaction เดิม ไม่สร้าง request ซ้ำ",
        "transaction": "สร้างไฟล์ temp, fsync, atomic rename และคำนวณ checksum ให้สำเร็จก่อน; จากนั้น transaction เดียว lock W, update W→P และ insert outbox READY; ห้าม commit W→P ก่อนมี durable file",
        "security": "สิทธิ์เขียน EAI S3 ใช้ IAM role ของ pod หรือ secretRef=secret/sgi/interfaces/eai-s3; จำกัดสิทธิ์เฉพาะ prefix ขาออกของ IAS (PutObject เท่านั้น) และห้าม editable access key ในหน้าจอ/ไฟล์ config",
        "steps": "lockWaitingSalesRequests|writeDurableIasFile|markPendingAndCreateOutbox|dispatchIasOutbox",
    },
    "5": {
        "repository": "iasSalesRepository",
        "read": """SELECT t.sales_summary_id, t.txn_date, t.sales_amount, t.window_no, t.source_checksum
FROM sgi_sales_transactions t
JOIN sgi_fgi_impact_sales_summaries s ON s.id = t.sales_summary_id
WHERE s.impact_process_id = :impact_process_id
ORDER BY t.sales_summary_id, t.txn_date, t.window_no;""",
        "write": """INSERT INTO sgi_sales_transactions
    (sales_summary_id, txn_date, window_no, seq, sales_amount, sales_diff, is_outlier, source_checksum)
VALUES (:sales_summary_id, :txn_date, :window_no, :seq, :sales_amount, :sales_diff, :is_outlier, :source_checksum)
ON CONFLICT (sales_summary_id, txn_date, window_no)
DO UPDATE SET sales_amount = EXCLUDED.sales_amount,
              sales_diff = EXCLUDED.sales_diff,
              is_outlier = EXCLUDED.is_outlier,
              source_checksum = EXCLUDED.source_checksum;

UPDATE sgi_fgi_impact_sales_summaries
SET total_working_days = :total_working_days,
    growth_rate_before = :growth_rate_before,
    growth_rate_after = :growth_rate_after,
    growth_rate_diff = :growth_rate_diff,
    sales_status = :sales_status,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :sales_summary_id;""",
        "idempotency": "checksum กันไฟล์ซ้ำ + UNIQUE(sales_summary_id,txn_date,window_no); คำนวณ summary ใหม่จาก transaction rows ทุก rerun",
        "transaction": "upsert รายวันและ update summary ของ sales_summary_id เดียวกันใน transaction; checksum/file tracking commit พร้อมกัน",
        "security": "สิทธิ์อ่าน EAI S3 ใช้ IAM role ของ pod หรือ secretRef=secret/sgi/interfaces/eai-s3 จำกัดเฉพาะ prefix ขาเข้า/backup ของ IAS (GetObject + PutObject เฉพาะ backup); quarantine อ็อบเจกต์ที่ checksum/รูปแบบไม่ผ่าน แทนการลบทิ้ง",
        "steps": "downloadAndStageIasSales|validateSalesWindows|upsertDailySales|recalculateSalesSummaries",
    },
    "6": {
        "repository": "statementExportRepository",
        "read": """SELECT d.doc_no, d.impact_process_id, s.id AS sales_summary_id,
       d.total_compensation_amount, q.score
FROM sgi_compensation_documents d
JOIN sgi_fgi_impact_sales_summaries s ON s.impact_process_id = d.impact_process_id
LEFT JOIN fcs_qssi_score q ON q.store_id = d.impacted_store_code AND q.month = d.impact_month
JOIN LATERAL (
    SELECT c.result_category
    FROM sgi_consideration_logs c
    WHERE c.doc_no = d.doc_no
    ORDER BY c.action_datetime DESC
    LIMIT 1
) latest_decision ON latest_decision.result_category = 'APPROVE'
WHERE d.status_code = '99'
  AND NOT EXISTS (
      SELECT 1 FROM sgi_interface_transactions i
      WHERE i.data_name = 'COMPENSATE_APPROVE_I' AND i.direction = 'OUT'
        AND i.doc_no = d.doc_no AND i.status IN ('READY','SENT'));""",
        "write": """INSERT INTO sgi_interface_transactions
    (run_id, data_name, direction, status, doc_no, impact_process_id, sales_summary_id,
     business_key, period_key, file_name, file_checksum, outbox_status, purge_after)
VALUES (:run_id, 'COMPENSATE_APPROVE_I', 'OUT', 'READY', :doc_no, :impact_process_id,
        :sales_summary_id, :doc_no, :period_key, :file_name, :file_checksum, 'READY',
        CURRENT_TIMESTAMP + INTERVAL '365 days')
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;

WITH purge_candidates AS (
    SELECT id
    FROM sgi_interface_transactions
    WHERE data_name = ANY(:purge_data_names)
      AND status = 'COMPLETED'
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
    ORDER BY id
    LIMIT :purge_batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM sgi_interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;""",
        "idempotency": "UNIQUE(data_name,direction,business_key,period_key); publisher confirm เปลี่ยน outbox_status ของ transaction เดิมเป็น CONFIRMED ไม่ insert แถวใหม่",
        "transaction": "สร้าง payload/checksum ก่อน แล้ว insert outbox READY; dispatcher publish และเปลี่ยน SENT + outbox_status = PUBLISHED แยก transaction; เมื่อได้ publisher confirm จาก broker จึงเปลี่ยน outbox_status = CONFIRMED + status = COMPLETED แบบ compare-and-set บนแถวเดิม (มติ 2026-09-08 ข้อ 2.13 — ไม่มี ACK ระดับธุรกิจจาก STA)",
        "security": "RabbitMQ broker ใช้ secretRef=secret/sgi/mq/sta, เชื่อมด้วย AMQPS (TLS 1.2+ verify-full); exchange/routing key มาจาก config ไม่ใช่ค่าที่ผู้ใช้แก้ได้ (dataName = sgi_impact_store ตามสัญญาใน STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md); credential rotation ไม่ต้องแก้เอกสารหรือ job param",
        "steps": "loadApprovedCompensations|buildStatementPayload|enqueueStatementOutbox|purgeAcknowledgedTracking",
    },
    "7": {
        "repository": "documentCompetitorRepository",
        "read": """-- คัดลอกทั้ง "รหัสสาขา" และ "รหัสแบรนด์" — คัดลอกอย่างใดอย่างหนึ่งข้อมูลจะหาย
SELECT d.doc_no, c.competitor_store_code, c.brand_code, c.name_th, c.name_en, c.branch_th,
       c.zone_code, c.subzone_code, c.opened_date, c.closed_date
FROM sgi_fgi_impact_competitors c
JOIN sgi_compensation_documents d ON d.impact_process_id = c.impact_process_id
WHERE c.period_key = :period_key;""",
        "write": """INSERT INTO sgi_document_competitors
    (doc_no, competitor_store_code, brand_code, name_th, name_en, branch_th,
     zone_code, subzone_code, opened_date, closed_date, source_system, updated_at)
VALUES (:doc_no, :competitor_store_code, :brand_code, :name_th, :name_en, :branch_th,
        :zone_code, :subzone_code, :opened_date, :closed_date, 'ALLMAP', CURRENT_TIMESTAMP)
ON CONFLICT (doc_no, competitor_store_code)
DO UPDATE SET brand_code = EXCLUDED.brand_code, name_th = EXCLUDED.name_th,
              name_en = EXCLUDED.name_en, branch_th = EXCLUDED.branch_th,
              zone_code = EXCLUDED.zone_code, subzone_code = EXCLUDED.subzone_code,
              opened_date = EXCLUDED.opened_date, closed_date = EXCLUDED.closed_date,
              updated_at = CURRENT_TIMESTAMP;

DELETE FROM sgi_document_competitors dc
WHERE dc.doc_no = :doc_no
  AND dc.source_system = 'ALLMAP'
  AND NOT EXISTS (
      SELECT 1
      FROM sgi_fgi_impact_competitors src
      JOIN sgi_compensation_documents d ON d.impact_process_id = src.impact_process_id
      WHERE d.doc_no = dc.doc_no
        AND src.period_key = :period_key
        AND src.competitor_store_code IS NOT DISTINCT FROM dc.competitor_store_code
  );""",
        "idempotency": "UNIQUE(doc_no,competitor_store_code) — **คีย์เป็นสาขา ไม่ใช่แบรนด์** (แก้ 2026-09-09); upsert และ prune เฉพาะ source_system=ALLMAP ให้ target ตรง source ปัจจุบันโดยไม่ลบแถว USER",
        "transaction": "upsert + prune sgi_document_competitors และ tracking (direction=INTERNAL) ใน transaction เดียวต่อ doc_no",
        "security": "service account ภายในมีสิทธิ์ SELECT source และ INSERT/UPDATE target เท่านั้น; ไม่มี external credential",
        "steps": "loadLatestDocumentCompetitors|upsertDocumentCompetitors|recordInternalCompetitorSync|reconcileDocumentCompetitors",
    },
    "8": {
        "repository": "compensationDocumentRepository",
        "read": """SELECT p.id AS impact_process_id, p.impacted_store_code, p.impact_month,
       SUM(COALESCE(s.adjust_compensation_amount, s.forecast_compensation_amount, 0)) AS total_compensation_amount
FROM sgi_fgi_impact_processes p
JOIN sgi_fgi_impact_stores s ON s.impact_process_id = p.id
WHERE p.process_status = 'READY_DOCUMENT'
GROUP BY p.id, p.impacted_store_code, p.impact_month;""",
        "write": """INSERT INTO sgi_compensation_documents
    (doc_no, year, running_no, impact_process_id, impact_compensation_id,
     impacted_store_code, impact_month,
     source, status_code, current_section_code, total_compensation_amount, created_by)
VALUES (:doc_no, :year, :running_no, :impact_process_id, :impact_compensation_id,
        :impacted_store_code, :impact_month,
        'FS', '06', '06', :total_compensation_amount, 'JOB-8')
-- ⚠️ กันซ้ำที่ **งวด** ไม่ใช่ที่รอบ — รอบหนึ่งมีเอกสารได้หลายใบ (งวดละใบ · มติ 2026-09-13)
ON CONFLICT (impact_compensation_id) DO NOTHING;

INSERT INTO sgi_interface_transactions
    (run_id, data_name, direction, status, impact_process_id, doc_no,
     business_key, period_key, outbox_status, purge_after, completed_at)
SELECT :run_id, 'DOCUMENT_CREATE', 'INTERNAL', 'COMPLETED', d.impact_process_id, d.doc_no,
       CAST(d.impact_process_id AS VARCHAR), d.impact_month, 'COMPLETED',
       CURRENT_TIMESTAMP + INTERVAL '365 days', CURRENT_TIMESTAMP
FROM sgi_compensation_documents d
WHERE d.impact_process_id = :impact_process_id
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;""",
        "idempotency": "UNIQUE(impact_process_id) และ UNIQUE(year,running_no); lock running number ต่อปีใน transaction; conflict ต้องคืน/อ้าง doc_no เดิม และยอมให้เลขที่จองกระโดดโดยห้าม reuse",
        "transaction": "lock เลขรัน + insert document + update process + tracking (direction=INTERNAL) ใน transaction เดียว",
        "security": "internal service account เท่านั้น; ห้ามสร้างไฟล์ BPM06001O, ห้าม SFTP และห้ามเก็บ K2 credential",
        "steps": "loadDocumentCandidates|allocateDocumentNumbers|createCompensationDocuments|recordDocumentCreation",
    },
    "8b": {
        "repository": "workflowRepository",
        "read": """WITH locked_process AS (
    SELECT p.id
    FROM sgi_fgi_impact_processes p
    JOIN sgi_compensation_documents d ON d.impact_process_id = p.id
    WHERE p.workflow_generation_status = 'W'
      -- ⚠️ sps_store.workflow_transaction ไม่มี PK/index (19,327 แถว) → เงื่อนไขนี้เป็น seq-scan · ประเมินต้นทุน query ก่อนใช้ และห้ามแก้ schema ของ library
      -- ✅ DP-1 ปิดแล้ว: reference_id = sgi_compensation_documents.id (surrogate) แปลงเป็น text
      AND NOT EXISTS (SELECT 1 FROM sps_store.workflow_transaction w WHERE w.reference_id = d.id::text   -- DP-1 = surrogate id (reference_id เป็น varchar(255)) AND w.version_id = :sgi_version_id)   -- @srm/glb-workflow
    ORDER BY p.id
    FOR UPDATE OF p SKIP LOCKED
), gate AS (
    SELECT p.id AS impact_process_id, d.doc_no, d.current_section_code,
           CASE
             WHEN BOOL_OR(ns.store_type IS NULL OR ns.store_type NOT IN ('FAM','FB1','FC1','FB2','FVB','FVC')) THEN 'N'
             WHEN BOOL_OR(pair.distance_km > CASE
                    WHEN impacted.zone_cd = ANY(:bangkok_metro_region_codes) THEN 1.000
                    ELSE 2.000
                  END) THEN 'N'
             WHEN BOOL_OR(pair.distance_km IS NULL) THEN 'W'
             WHEN ist.opt_dv_user_id IS NULL OR BTRIM(ist.opt_dv_user_id) = '' THEN 'N'
             WHEN ij.juristic_name IS NULL OR BOOL_OR(nj.juristic_name IS NULL) THEN 'W'
             WHEN BOOL_OR(ij.juristic_name = nj.juristic_name) THEN 'N'
             WHEN ss.growth_rate_diff IS NULL THEN 'W'
             WHEN ss.growth_rate_diff > -10 THEN 'N'
             WHEN ss.sales_status IS NULL OR ss.sales_status NOT IN ('Y','N') THEN 'W'
             ELSE 'Y'
           END AS gate_decision
    FROM locked_process lp
    JOIN sgi_fgi_impact_processes p ON p.id = lp.id
    JOIN sgi_compensation_documents d ON d.impact_process_id = p.id
    JOIN sgi_impacted_stores ist ON ist.store_code = p.impacted_store_code
    JOIN store impacted ON impacted.store_id = p.impacted_store_code
    JOIN sgi_fgi_impact_stores pair ON pair.impact_process_id = p.id
    JOIN store ns ON ns.store_id = pair.new_store_code
    -- นิติบุคคลไม่ได้อยู่บน store — ต้องผ่าน fr_store.juristic_id -> juristic.juristic_name
    LEFT JOIN fr_store ifs ON ifs.store_id = impacted.store_id
    LEFT JOIN juristic ij  ON ij.juristic_id = ifs.juristic_id
    LEFT JOIN fr_store nfs ON nfs.store_id = ns.store_id
    LEFT JOIN juristic nj  ON nj.juristic_id = nfs.juristic_id
    LEFT JOIN sgi_fgi_impact_sales_summaries ss ON ss.impact_process_id = p.id
    GROUP BY p.id, d.doc_no, d.current_section_code, ist.opt_dv_user_id,
             ij.juristic_name, ss.growth_rate_diff, ss.sales_status
)
SELECT * FROM gate;""",
        "write": """UPDATE sgi_fgi_impact_processes
SET workflow_generation_status = 'N', updated_at = CURRENT_TIMESTAMP
WHERE id = :impact_process_id
  AND workflow_generation_status = 'W'
  AND :gate_decision = 'N';

-- gate_decision='Y': เปิด workflow
-- 🔴 มติ 2026-09-09 — **job ไม่เรียก @srm/glb-workflow เอง**
--    workflow lib ใช้กับ flow K2 (เอกสาร/การอนุมัติ) เท่านั้น
--    Job 8b เรียก REST ของ BE ด้วย service token แทน:
--        POST /api/v1/sgi/workflow/instances
--        body: { impactProcessId, sourceJobNo: '8b', requestId: 'job8b-<id>-<YYYYMM>' }
--    ฝั่ง BE (LLDD-BE-API-Workflow-Instances) เป็นผู้เรียก engine ที่เดียวในระบบ
--    → job ไม่ต้องรู้จัก versionId / referenceId / stateId / ชื่อ function ของ lib เลย
--    → requestId เป็น idempotency key: ยิงซ้ำด้วยค่าเดิมต้องไม่เปิด workflow ที่สอง
-- ✅ DP-1 (2026-08-17): referenceId = sgi_compensation_documents.id — **BE เป็นผู้ส่งให้ engine**
UPDATE sgi_fgi_impact_processes
SET workflow_generation_status = 'Y', updated_at = CURRENT_TIMESTAMP
WHERE id = :impact_process_id
  AND workflow_generation_status = 'W'
  AND :gate_decision = 'Y';

-- gate_decision='W' ไม่เปลี่ยนสถานะ; บันทึก reason ลง application log (structured) เพื่อ rerun — ไม่มีตาราง job_run_histories แล้ว (2026-08-06).""",
        "idempotency": ("กันซ้ำระดับ application — ตรวจว่ามี transaction เดิมของ reference นี้อยู่แล้วหรือไม่ ก่อนเรียก initialize แล้ว skip "
                        "· ⚠️ **ไม่มี UNIQUE(version_id, reference_id) จริงใน `sps_store.workflow_transaction`** (ตารางนี้ไม่มีทั้ง PK และ index "
                        "ทั้งที่มี 19,327 แถว — ตรวจแล้วที่ `SBP/db-schema-sps_store.md`) จึงพึ่ง constraint ฝั่ง DB ไม่ได้ และ query ตาม reference_id เป็น seq-scan "
                        "· **ห้ามแก้ schema ของ library** — กันซ้ำที่ระดับ application และประเมินต้นทุน query ทุกครั้งที่อ้างตารางนี้"),
        "transaction": "lock process + evaluate gate + branch N/W/Y; เฉพาะ Y จึงเรียก `POST /sgi/workflow/instances` ของ BE (job ไม่เรียก lib เอง · มติ 2026-09-09) (ชื่อ function ตามชีต Detail ของ LLDD lib) และ W→Y ใน transaction เดียว, N ต้อง persist ถาวร, W คงเดิมเพื่อ rerun",
        "security": "internal service token จาก workload identity/secretRef; ห้าม Basic Auth หรือ K2 REST credential เดิม",
        "steps": "lockWorkflowCandidates|evaluateGenerationGate|startInternalWorkflows|notifyWorkflowOwners",
    },
    "9": {
        "repository": "documentNewStoreRepository",
        "read": """SELECT d.doc_no, s.new_store_code,
       COALESCE(s.adjust_compensate_percent, s.forecast_compensate_percent) AS compensate_percent,
       COALESCE(s.adjust_compensation_amount, s.forecast_compensation_amount) AS compensation_amount
FROM sgi_fgi_impact_stores s
JOIN sgi_compensation_documents d ON d.impact_process_id = s.impact_process_id
WHERE s.impact_month = :impact_month
  AND COALESCE(s.adjust_compensate_percent, s.forecast_compensate_percent) IS NOT NULL
  AND COALESCE(s.adjust_compensate_percent, s.forecast_compensate_percent) BETWEEN 0 AND 100;""",
        "write": """-- validateAllocationValues ต้องยืนยัน source_row_count = valid_row_count ก่อนคำสั่งนี้;
-- ถ้าค่า percent เป็น NULL/นอกช่วง ให้ throw COMPENSATE_PERCENT_INVALID และ rollback ก่อน upsert/prune.
INSERT INTO sgi_document_new_stores
    (doc_no, new_store_code, compensate_percent, compensation_amount, source_system, updated_at)
SELECT :doc_no, :new_store_code, :compensate_percent, :compensation_amount, 'FGI', CURRENT_TIMESTAMP
WHERE :compensate_percent IS NOT NULL
  AND :compensate_percent BETWEEN 0 AND 100
ON CONFLICT (doc_no, new_store_code)
DO UPDATE SET compensate_percent = EXCLUDED.compensate_percent,
              compensation_amount = EXCLUDED.compensation_amount,
              updated_at = CURRENT_TIMESTAMP
RETURNING doc_no, new_store_code;

-- Service ต้องได้ RETURNING 1 แถวต่อ source row; ไม่ครบให้ rollback และห้าม prune.

DELETE FROM sgi_document_new_stores dns
WHERE dns.doc_no = :doc_no
  AND dns.source_system = 'FGI'
  AND NOT EXISTS (
      SELECT 1
      FROM sgi_fgi_impact_stores src
      JOIN sgi_compensation_documents d ON d.impact_process_id = src.impact_process_id
      WHERE d.doc_no = dns.doc_no
        AND src.impact_month = :impact_month
        AND src.new_store_code = dns.new_store_code
  );

SELECT CASE WHEN ABS(SUM(compensate_percent) - 100) <= 0.0001 THEN TRUE ELSE FALSE END AS allocation_valid
FROM sgi_document_new_stores
WHERE doc_no = :doc_no;""",
        "idempotency": "UNIQUE(doc_no,new_store_code); upsert + prune เฉพาะ source_system=FGI ให้ target ตรง impact set ปัจจุบัน โดยไม่ลบแถว USER",
        "transaction": "validate source percent ต้องไม่เป็น NULL และอยู่ 0..100 ก่อน upsert; จากนั้น upsert + prune ร้านของ doc_no, validate ผลรวม 100% และ tracking (direction=INTERNAL) ใน transaction เดียว; invalid/ไม่ครบให้ rollback ก่อน prune",
        "security": "internal service account least privilege; ไม่มี SFTP/BPM credential หรือ editable external endpoint",
        "steps": "loadNewStoreAllocations|validateAllocationValues|upsertDocumentNewStores|reconcileAllocationTotals",
    },
    "10": {
        "repository": "pendingAckRepository",
        "read": """-- มติ 2026-09-08 (ข้อ 2.13): "ค้าง" = broker ยังไม่ publisher confirm ไม่ใช่ "STA ยังไม่ ACK"
-- สเปก STA มีแค่ 3 ข้อความบน RabbitMQ ไม่มีช่องทาง ACK กลับมา จึงไม่รอ ACK ระดับธุรกิจ
SELECT id, data_name, business_key, file_name, sent_at
FROM sgi_interface_transactions
WHERE direction = 'OUT'
  AND (outbox_status IS NULL OR outbox_status <> 'CONFIRMED')
  AND created_at < CURRENT_TIMESTAMP - (:threshold_hours * INTERVAL '1 hour')
  AND (last_ack_notified_on IS NULL OR last_ack_notified_on < CURRENT_DATE)
ORDER BY created_at;""",
        "write": """-- ยกเลิกตาราง audit_logs แล้ว (2026-08-07) — marker กันส่งซ้ำย้ายมาไว้บน sgi_interface_transactions เอง
-- คอลัมน์ last_ack_notified_on DATE มีอยู่ใน DDL ของ sgi_interface_transactions แล้ว (ดู LLDD-Database 5.x)
UPDATE sgi_interface_transactions
   SET last_ack_notified_on = CURRENT_DATE
 WHERE id = ANY(:transaction_ids)
   AND (last_ack_notified_on IS NULL OR last_ack_notified_on < CURRENT_DATE)
RETURNING id;""",
        "idempotency": "คอลัมน์ last_ack_notified_on บน sgi_interface_transactions เป็น marker ต่อรายการต่อวัน; rerun วันเดียวกันไม่ส่งอีเมลซ้ำ (ย้ายมาจาก audit_logs ที่ถูกยกเลิก 2026-08-07)",
        "transaction": "อ่าน pending แบบ read-only (ไม่แตะ outbox_status — Job 6 เป็นผู้เขียน `outbox_status = 'CONFIRMED'` + `status = 'COMPLETED'` เมื่อได้ publisher confirm); reserve notification marker ก่อนส่ง; ส่งอีเมลล้มเหลวจึง mark FAILED และ retry ด้วย marker เดิม",
        "security": "SGI เรียก sendEmail() ของ email-lib เอง (ปิด DP-5 · 2026-08-14) — เลข template มาจาก workflow_route.email_id · credential SMTP/SES และตาราง email_template/email_sent เป็นของระบบ SBP เดิม",
        "steps": "loadOverdueAcknowledgements|reserveNotificationMarkers|sendPendingAckDigest|closeNotificationMarkers",
    },
}


def api_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


API_REQUIRED_QUERY_FIELDS: dict[str, set[str]] = {
    "/api/v1/sgi/document": {"year"},
    "/api/v1/sgi/report/status-summary": {"year", "status"},
    "/api/v1/sgi/report/status-summary/export": {"year", "status"},
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


# ตัวกรองของหน้ารายการเอกสาร — ทุกตัวตรงกับช่องกรองบนหน้าจอ 1:1
# ⚠️ ต้องกรองที่ฝั่ง server เพราะ endpoint มี page/size · ถ้ากรองฝั่ง client
#    ตัวกรองจะทำงานแค่แถวในหน้านั้น (เพิ่มครบ 2026-09-09 หลังผู้ใช้ชี้ว่า Query Params ไม่ครบ)
_LIST_FILTER_NOTES = {
    "keyword": "ช่อง **ค้นหา** — ค้นแบบ contains ใน เลขที่เอกสาร / ชื่อร้าน / รหัสร้าน (ไม่สนตัวพิมพ์)",
    "regioncode": "ช่อง **ภาค** — รหัสภาคของร้าน (`store.zone_cd`) · ค่าเดียวกับ `items[].regionCode` ใน response",
    "storetype": "ช่อง **ประเภทร้าน** — 7 ค่า `A B C D E PTT บริษัท` (`store.store_type`) ชุดเดียวกับตัวกรองในรายงาน",
    "createdfrom": "ช่อง **วันที่สร้าง (ตั้งแต่)** — ISO ค.ศ. · รวมวันที่ระบุ",
    "createdto": "ช่อง **วันที่สร้าง (ถึง)** — ISO ค.ศ. · **รวมทั้งวัน** (SQL ใช้ `< :createdTo + 1`)",
    "salesdeclinemin": "ช่อง **ยอดขายที่ลดลง (ต่ำสุด)** — % เทียบกับ `items[].salesDeclinePercent`",
    "salesdeclinemax": "ช่อง **ยอดขายที่ลดลง (สูงสุด)** — % เทียบกับ `items[].salesDeclinePercent`",
    "compensationmin": "ช่อง **เงินชดเชย (ต่ำสุด)** — บาท เทียบกับ `items[].totalCompensationAmount`",
    "compensationmax": "ช่อง **เงินชดเชย (สูงสุด)** — บาท เทียบกับ `items[].totalCompensationAmount`",
    "dayspendingmin": "ช่อง **รอ (วัน) ต่ำสุด** — เทียบกับ `items[].daysPending` · มีเฉพาะกล่องงาน `/tasks`",
    "dayspendingmax": "ช่อง **รอ (วัน) สูงสุด** — เทียบกับ `items[].daysPending` · มีเฉพาะกล่องงาน `/tasks`",
    "result": "ช่อง **ผลการพิจารณา** (มีเฉพาะหน้า *ที่เกี่ยวข้อง*) — `APPROVE` / `REJECT` / `CANCELLED` / `NONE` · "
              "ดูจากผลพิจารณา **ล่าสุด** ของเอกสารใน `sgi_consideration_logs` ไม่ได้อยู่ที่หัวเอกสาร",
}


def api_field_constraint(field_path: str, value: Any) -> str:
    name = field_path.split(".")[-1].replace("[]", "").lower()
    if not field_path.startswith("items") and name in _LIST_FILTER_NOTES:
        return _LIST_FILTER_NOTES[name]
    if name in {"page"}:
        return ">= 1; default 1"
    if name in {"size"}:
        return "1..100; default 20"
    if name.endswith("storecode"):
        return "exactly 5 digits; preserve leading zero"
    if name in {"docno"}:
        return "ค.ศ. YYYY/xxxxx"
    if name.endswith("datetime") or name.endswith("at") or name.endswith("date") or name.endswith("month"):
        return "ISO-8601 ค.ศ.; nullable only when type includes null"
    if name.endswith("percent"):
        return "number 0..100 with 2 decimals"
    if name == "compensationamount":
        return ("number >= 0 with 2 decimals · ⚠️ มาจากคนละคอลัมน์ตามที่อยู่: "
                "ใน `newStores[]` = `sgi_document_new_stores.compensation_amount` · "
                "ใน `compensationHistories[]` = `sgi_compensation_histories.compensate_amount`")
    if "amount" in name:
        return "number >= 0 with 2 decimals"
    if name in {"statuscode", "nextsection", "sectioncode", "rolecode"}:
        return "canonical code; do not replace with display label"
    if name in {"reason", "comment"}:
        return "trimmed UTF-8 Thai text; required by operation/business rule"
    if name == "versionno":
        return "optimistic concurrency: ต้องส่งค่าล่าสุดที่โหลดมา · ไม่ตรงคืน 409 STALE_VERSION"
    if name == "competitorcode":
        return "รหัสแบรนด์คู่แข่งจาก master 01–11 เท่านั้น (ห้าม free text)"
    if name == "factorcode":
        return "รหัสปัจจัยภายนอกจาก master (sgi_external_factors.factor_code)"
    if name == "sourcesystem":
        return "ALLMAP = ระบบดึงมาเอง · USER = ผู้ใช้คีย์เพิ่ม"
    if name == "id":
        return "id ของแถวเดิม — **ไม่ส่ง = แถวที่ผู้ใช้เพิ่มใหม่ (INSERT)** · แถวเดิมที่ไม่ถูกส่งมาถือว่าถูกลบ"
    if isinstance(value, list):
        return "JSON array; element type shown in Type column"
    if isinstance(value, dict):
        return "JSON object; nested fields listed below"
    return "UTF-8; use value domain described by endpoint purpose"


# ฟิลด์ที่ "ไม่บังคับ" โดยกติกาธุรกิจ — ประกาศตรง ๆ ไม่ให้ไปเดาจากการมี/ไม่มีในตัวอย่าง
#   (ตัวอย่าง payload ถูก merge คีย์ข้ามเอกสารแล้ว การเดาจาก "ขาดใน element ไหน" จึงไม่น่าเชื่อถือ)
API_OPTIONAL_FIELDS: set[str] = {
    "competitors[].id",          # ไม่ส่ง = แถวที่ผู้ใช้เพิ่มใหม่ (INSERT)
    "externalFactors[].id",      # ไม่ส่ง = แถวที่ผู้ใช้เพิ่มใหม่ (INSERT)
    "externalFactors[].dateTo",  # SRS ข้อ 11: วันที่สิ้นสุดไม่บังคับ แต่ถ้ามีต้อง >= วันที่เริ่มต้น
}


def api_schema_rows(spec: ApiSpec, body: Any, direction: str) -> list[list[str]]:
    if body is None:
        return [["-", "none", "No", "Endpoint has no JSON body/query object"]]

    rows: list[list[str]] = []
    required_query = API_REQUIRED_QUERY_FIELDS.get(spec.path, set())

    def walk(value: Any, path: str = "", force_optional: bool = False) -> None:
        if force_optional:
            # key ที่ไม่ได้มีครบทุก element ของอาร์เรย์ → optional เสมอ ไม่ว่าทิศทางไหน
            rows.append([path, api_value_type(value), "No", api_field_constraint(path, value)])
            if isinstance(value, dict):
                for key, child in value.items():
                    walk(child, f"{path}.{key}", True)
            return
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
            items = [v for v in value if isinstance(v, dict)]
            if items:
                # รวม key จาก **ทุก element** ไม่ใช่แค่ตัวแรก — key ที่ไม่ได้อยู่ครบทุกตัวคือ optional
                # (เช่น competitors[].id: แถวเดิมมี id · แถวที่ผู้ใช้เพิ่มใหม่ไม่มี)
                seen: dict[str, Any] = {}
                for it in items:
                    for key, child in it.items():
                        seen.setdefault(key, child)
                for key, child in seen.items():
                    optional_in_array = any(key not in it for it in items)
                    walk(child, f"{path}[].{key}", optional_in_array)
            return
        if direction == "response":
            required = "No" if value is None else "Yes"
        elif spec.method.upper() == "GET":
            required = "Yes" if path in required_query else "No"
        else:
            required = "No" if value is None else "Yes"
        if (path or "") in API_OPTIONAL_FIELDS:
            required = "No"
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


# --------------------------------------------------------------------------------------
# ลำดับงานจริงระหว่างเอกสาร (finish-to-start) — ผู้ผลิตต้องจบก่อนผู้บริโภคเริ่ม
#
# 2026-08-10: เดิม build_topic_schedule คิดแค่ "ชั่วโมงสะสมรายคน" จึงไม่รู้จัก dependency เลย
# ผลคือตารางเดิมละเมิดลำดับงาน 14 เส้น ที่หนักที่สุดคือ Job 8 (ผู้สร้าง sgi_compensation_documents)
# ถูกจัดไว้ท้ายสุด แต่ Job 7 / 9 / 8b ที่อ่านผลของมันเสร็จไปก่อนแล้ว
#
# แหล่งอ้างอิงของแต่ละเส้น: field `rels` ของแต่ละ job ใน job-batch.html (ดู load_batch_jobs)
# --------------------------------------------------------------------------------------
# Job 1 (ImportQSSI) ถูกตัดออก 2026-08-24 — ระบบ SBP เดิมนำเข้า fcs_qssi_score ให้แล้ว SGI แค่อ่าน
JOB_PIPELINE_ORDER: list[str] = ["2", "3", "4", "5", "6", "7", "8", "8b", "9", "10"]

# 2026-08-11: ถอดระบบ buffer ออกทั้งหมด — ชั่วโมงในเอกสารคือค่าประเมินตรง ๆ ไม่มีส่วนเผื่อ

# ป้ายปุ่มบนหน้าจอ -> ค่า `result` ที่ยิงเข้า API (7-enum verbatim)
#   BE ตรวจ result แบบตรงตัว — ป้ายที่คนเห็นกับค่าที่ส่งจึงเป็นคนละอย่างได้ แต่ต้อง map ให้ถูก
#   เจอจริง 2026-09-02: role 01/02/03/06 ส่งป้ายไปตรง ๆ ทำให้ 4 ใน 5 บทบาทจะได้ 422 ตอน submit
# ══ นโยบายเดียวของการดาวน์โหลดไฟล์แนบ (ตั้งเป็นแหล่งเดียว 2026-09-07) ══════════════
# ก่อนหน้านี้ 4 เอกสารเขียนกันคนละอย่าง — BE §5 บอก "เฉพาะ CLEAN" · BE flow บอก "PENDING ก็ได้"
# · FE C06 ปิด PENDING ตายตัว · LLDD-API ระบุ CLEAN อย่างเดียว — รวมแล้วขัดกันเอง 4 ทาง
# เรื่องนี้กระทบ security + BE + FE + test case พร้อมกัน จึงต้องมีข้อความชุดเดียวที่ทุกฉบับอ้าง
#
# ข้อเท็จจริงที่ตรวจแล้ว (2026-09-07): **ไม่มีตัวสแกนไวรัสอยู่จริงในระบบใดเลย** —
#   ค้น clamav/virus/antivirus/malware/GuardDuty ใน store-backend · bff · sop-sgi-batch = ไม่พบ
#   `POST /statement/upload-file-aws` แค่รับ base64 แล้ววางลง S3 ไม่มีขั้นสแกน
#   ผลคือถ้าบังคับ CLEAN อย่างเดียว `scan_status` จะค้างที่ PENDING ตลอด → **ดาวน์โหลดไม่ได้เลยทั้งระบบ**
ATTACHMENT_DOWNLOAD_POLICY_SHORT = (
    "`CLEAN` ดาวน์โหลดได้เสมอ · `BLOCKED`/`FAILED` คืน 422 `FILE_SCAN_BLOCKED` เสมอ · "
    "`PENDING` ขึ้นกับสวิตช์ `SGI_ALLOW_PENDING_DOWNLOAD` (`mas_param`)"
)

ATTACHMENT_DOWNLOAD_POLICY_FULL = (
    "**นโยบายเดียวของทั้งระบบ (ปิดข้อขัดแย้ง 2026-09-07 · ยังรอ security sign-off — ดู `DECISIONS-รอตัดสินใจ.md` ข้อ 2.10):**\n\n"
    "| `scan_status` | ดาวน์โหลดได้ไหม | ทำอะไร |\n"
    "| --- | --- | --- |\n"
    "| `CLEAN` | ✅ ได้เสมอ | stream ไฟล์ตามปกติ |\n"
    "| `BLOCKED` · `FAILED` | ❌ ไม่ได้เสมอ | คืน **422 `FILE_SCAN_BLOCKED`** — ห้ามมีทางลัดใด ๆ |\n"
    "| `PENDING` | ⚠️ ขึ้นกับสวิตช์ | อ่าน `SGI_ALLOW_PENDING_DOWNLOAD` จาก `mas_param` · "
    "`Y` = ให้ดาวน์โหลดได้ แต่ต้องแนบ header `X-SGI-Scan-Status: PENDING` และ FE ต้องขึ้นคำเตือนว่ายังไม่ผ่านการสแกน · "
    "`N` = คืน 422 `FILE_SCAN_BLOCKED` เหมือน BLOCKED |\n\n"
    "**ทำไมต้องมีสวิตช์แทนที่จะบังคับ `CLEAN` ตรง ๆ:** ตรวจแล้วว่า**ยังไม่มีตัวสแกนไวรัสในระบบใดเลย** "
    "(ไม่พบ clamav/antivirus/GuardDuty ใน `store-backend` · `sbp-bff` · `sop-sgi-batch` · "
    "`POST /statement/upload-file-aws` แค่วางไฟล์ลง S3) ถ้าบังคับ `CLEAN` วันนี้ `scan_status` จะค้างที่ `PENDING` ตลอด "
    "**แล้วไฟล์แนบทั้งระบบจะดาวน์โหลดไม่ได้เลย** · การมีสวิตช์ทำให้เลือกได้โดยไม่ต้องแก้โค้ด และ**พลิกกลับเป็นเข้มได้ทันที**\n\n"
    "**ค่าตั้งต้นและเงื่อนไขปิด:** ตั้ง `SGI_ALLOW_PENDING_DOWNLOAD = 'Y'` เฉพาะช่วงที่ยังไม่มีตัวสแกน · "
    "**วันที่ตัวสแกนขึ้น production ต้องเปลี่ยนเป็น `'N'` ทันทีในรอบ deploy เดียวกัน** และตัดสวิตช์ทิ้งในเฟสถัดไป · "
    "🔴 ค่านี้เป็นการตัดสินใจด้าน security — **ต้องให้ทีม security/infra เซ็นรับก่อน UAT** ห้ามทีมพัฒนาตั้งเอง"
)

RESULT_ENUM_VALUE: dict[str, str] = {
    "เห็นควรชดเชย": "เห็นควรชดเชย",
    "เห็นควรไม่ชดเชย": "เห็นควรไม่ชดเชย",
    "หยุดชดเชยประกันรายได้": "หยุดชดเชยประกันรายได้",
    "ส่งหน่วยงานส่งเสริมธุรกิจ SBP": "ส่งหน่วยงานส่งเสริมธุรกิจ SBP",
    "ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ": "ส่งเจ้าหน้าที่ SBP DSA",
    "คำนวณเงินชดเชยเรียบร้อย": "คำนวณเงินชดเชยเรียบร้อย",
    "ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)": "ส่งกลับ",
    "ส่งกลับฝ่าย SBP DSA": "ส่งกลับ",
}

JOB_DEPENDENCIES: dict[str, list[str]] = {
    "3": ["2"],       # sgi_fgi_impact_stores เป็นแม่ของ sgi_fgi_impact_competitors
    "4": ["2"],       # sgi_fgi_impact_sales_summaries ต่อจาก sgi_fgi_impact_stores
    "5": ["4"],       # Job 5 เติม sgi_sales_transactions ใต้หัวตารางที่ Job 4 สร้าง
    "6": ["2"],       # อ่าน fcs_qssi_score (ระบบ SBP เดิมเติมให้) ครบ 6 หมวด + mutate sgi_fgi_impact_stores
    "7": ["3", "8"],  # อ่าน sgi_fgi_impact_competitors เขียนลง sgi_document_competitors.doc_no
    "8": ["6"],       # query impact profile สถานะ COMPENSATE I ที่ Job 6 ปล่อย
    "8b": ["5", "8"], # growth_rate_diff -> Gen Flow Gate · ต้องมี sgi_compensation_documents ก่อน
    "9": ["8"],       # sgi_document_new_stores.doc_no -> sgi_compensation_documents
    "10": ["6"],      # เฝ้าแถว sgi_interface_transactions ที่ Job 6 สร้าง
    # 2026-09-02 — job ใหม่ 2 ตัว (เดิมตกหล่นจากกราฟ ทำให้แผนงานจัดคิวให้เริ่มเร็วเกินจริง)
    "11": ["6"],      # ขากลับของสัญญาเดียวกับ Job 6 — ต้องมี exchange/queue + outbox ของ Job 6 ก่อน
    "12": ["8b"],     # อ่านงานค้างจาก @srm/glb-workflow — ต้องมีงานอยู่ใน engine ก่อนถึงทดสอบได้
}

DOC_DEPENDENCIES: dict[str, list[str]] = {
    "BE/LLDD-BE-Data-Migration-Cutover": ["BE/LLDD-BE-Database-Structure"],
    "BE/LLDD-BE-API-Common-Contracts": [
        "BE/LLDD-BE-Database-Structure",
        "BE/LLDD-BE-Integration-SBP-Platform",
    ],
    # กันงานซ้ำระหว่าง Vava (BE) กับ lin (FE): ตัวตน/สิทธิ์/เมนู ถูกนิยามฝั่ง BE ก่อนหนึ่งครั้ง
    # แล้ว FE จึงเขียนสัญญาฝั่งบริโภค — ไม่ให้สองคนนิยาม header/permission ซ้ำกันคนละแบบ
    "FE/LLDD-FE-Integration-Contracts": ["BE/LLDD-BE-Integration-SBP-Platform"],
    "FE/LLDD-FE-Foundation": ["FE/LLDD-FE-Integration-Contracts"],
    "FE/LLDD-FE-Create-Document": ["FE/LLDD-FE-Foundation"],
    "FE/LLDD-FE-Document-Lists": ["FE/LLDD-FE-Foundation"],
    "FE/LLDD-FE-Document-Detail": ["FE/LLDD-FE-Foundation", "BE/LLDD-BE-Workflow-Engine-Definition"],
    "FE/LLDD-FE-Report": ["FE/LLDD-FE-Foundation"],
    "FE/LLDD-FE-Master-Data": ["FE/LLDD-FE-Foundation"],
    # role pack 5 ฉบับเป็นมุมมองต่อบทบาทของหน้าเดียวกัน — ต้องรอโครงหน้า Document Detail นิ่งก่อน
    # (เดิมไม่ได้ประกาศไว้ ทำให้กระดาน Kanban แสดงว่าเริ่มได้ทันทีทั้งที่เริ่มไม่ได้จริง)
    "FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA": ["FE/LLDD-FE-Document-Detail"],
    "FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer": ["FE/LLDD-FE-Document-Detail"],
    "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion": ["FE/LLDD-FE-Document-Detail"],
    "FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion": ["FE/LLDD-FE-Document-Detail"],
    "FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP": ["FE/LLDD-FE-Document-Detail"],
}


def document_dependencies(topics_list: list[Topic]) -> dict[str, set[str]]:
    """แผนที่ เอกสาร -> เอกสารที่ต้องจบก่อน (เฉพาะที่มีอยู่จริงใน topics_list)"""
    files = {t.file for t in topics_list}
    job_file = {
        t.file.split("Job-")[1].split("-")[0]: t.file
        for t in topics_list
        if t.file.startswith("Jobs/")
    }
    preds: dict[str, set[str]] = {t.file: set() for t in topics_list}
    for consumer, producers in DOC_DEPENDENCIES.items():
        if consumer in files:
            preds[consumer] |= {p for p in producers if p in files}
    for consumer, producers in JOB_DEPENDENCIES.items():
        if consumer in job_file:
            preds[job_file[consumer]] |= {job_file[p] for p in producers if p in job_file}
    # สองฉบับนี้อธิบายการต่อกับ "ระบบเดิม" (BFF/auth/mas_param และ @srm/glb-workflow)
    # ไม่ได้อ้าง DDL ของ SGI จึงเขียนขนานกับ Database-Structure ได้ตั้งแต่สัปดาห์แรก
    platform_docs = {"BE/LLDD-BE-Integration-SBP-Platform", "BE/LLDD-BE-Workflow-Engine-Definition"}
    fe_leaf = "FE/LLDD-FE-Testing-Delivery"
    if fe_leaf in files:
        preds[fe_leaf] |= {f for f in files if f.startswith("FE/") and f != fe_leaf}
    for topic in topics_list:
        # เอกสารฐานราก: DDL ต้องนิ่งก่อนเขียนเอกสาร BE อื่น · envelope กลางต้องนิ่งก่อนเขียน BE-API
        if (
            topic.file.startswith("BE/")
            and topic.file != "BE/LLDD-BE-Database-Structure"
            and topic.file not in platform_docs
        ):
            preds[topic.file] |= {"BE/LLDD-BE-Database-Structure"} & files
        if topic.file.startswith("BE/LLDD-BE-API") and topic.file != "BE/LLDD-BE-API-Common-Contracts":
            preds[topic.file] |= {"BE/LLDD-BE-API-Common-Contracts"} & files
        if topic.file.startswith("Jobs/"):
            preds[topic.file] |= {"BE/LLDD-BE-API-Common-Contracts"} & files
    for topic in topics_list:
        preds[topic.file].discard(topic.file)
    return preds


# ═══════════════════════ เอกสารที่เกี่ยวข้อง (cross-reference อัตโนมัติ) ═══════════════════════
# ผูกจาก endpoint จริงที่แต่ละฉบับประกาศไว้ใน topic.apis — ฉบับ FE ที่เรียกเส้นไหน
# จะโยงไปยังฉบับ BE ที่เป็นเจ้าของเส้นนั้นเสมอ ไม่ต้องมีใครมาไล่ใส่มือ

_TOPIC_INDEX: dict[str, "Topic"] | None = None


def topic_index() -> dict[str, "Topic"]:
    global _TOPIC_INDEX
    if _TOPIC_INDEX is None:
        _TOPIC_INDEX = {t.file: t for t in topics()}
    return _TOPIC_INDEX


def doc_short_name(file_key: str) -> str:
    return file_key.rsplit("/", 1)[-1]


def endpoint_key(spec: "ApiSpec") -> str:
    return f"{spec.method} {spec.path}"


def _is_be_api_doc(file_key: str) -> bool:
    return file_key.startswith("BE/LLDD-BE-API") or file_key.startswith("Jobs/")


def related_documents(topic: "Topic") -> list[list[str]]:
    """ตารางเอกสาร LLDD ที่เกี่ยวข้องกับฉบับนี้ พร้อมเหตุผลว่าเกี่ยวยังไง"""
    index = topic_index()
    rows: list[tuple[str, str, str]] = []          # (ความสัมพันธ์, เอกสาร, รายละเอียด)
    seen: set[tuple[str, str]] = set()

    def add(relation: str, file_key: str, detail: str) -> None:
        if file_key == topic.file or file_key not in index:
            return
        key = (relation, file_key)
        if key in seen:
            return
        seen.add(key)
        rows.append((relation, doc_short_name(file_key), detail))

    my_paths = {endpoint_key(a) for a in topic.apis}

    # 1) เส้นที่ฉบับนี้ "เรียกใช้" -> ฉบับ BE ที่เป็นเจ้าของสัญญาเส้นนั้น
    #    Common-Contracts ยกเว้น เพราะมันเป็นสัญญากลาง ไม่ใช่เจ้าของ endpoint (ยกเส้นมาเป็นตัวอย่าง)
    owned_by: dict[str, list[str]] = {}
    for other_key, other in index.items():
        if other_key == topic.file or not _is_be_api_doc(other_key):
            continue
        if other_key == "BE/LLDD-BE-API-Common-Contracts":
            continue
        shared = sorted(my_paths & {endpoint_key(a) for a in other.apis})
        if shared:
            owned_by[other_key] = shared
    for other_key in sorted(owned_by):
        add("ใช้ endpoint ของ", other_key, " · ".join(f"`{s}`" for s in owned_by[other_key]))

    # 2) ฉบับอื่นที่เรียกเส้นของฉบับนี้ (เฉพาะเมื่อฉบับนี้เป็นเจ้าของสัญญา)
    if _is_be_api_doc(topic.file) and topic.file != "BE/LLDD-BE-API-Common-Contracts":
        for other_key in sorted(index):
            other = index[other_key]
            if other_key == topic.file or other_key == "BE/LLDD-BE-API-Common-Contracts":
                continue
            shared = sorted(my_paths & {endpoint_key(a) for a in other.apis})
            if shared:
                add("ถูกเรียกจาก", other_key, " · ".join(f"`{s}`" for s in shared))

    # 3) สัญญากลางที่ทุกฉบับต้องยึด
    if topic.file != "BE/LLDD-BE-API-Common-Contracts":
        add("สัญญากลาง", "BE/LLDD-BE-API-Common-Contracts",
            "envelope `{success,data}` · error code · pagination · รูปแบบวันที่/เลขเอกสาร")
    if topic.track == "FE" and topic.file != "FE/LLDD-FE-Integration-Contracts":
        add("สัญญากลาง", "FE/LLDD-FE-Integration-Contracts",
            "API client · auth header · error mapping · RBAC/menu gating ฝั่ง FE")

    # 4) โครงสร้างข้อมูล / engine / แพลตฟอร์ม
    if topic.db_tables:
        add("โครงสร้างข้อมูล", "BE/LLDD-BE-Database-Structure",
            "DDL ของตารางที่หัวข้อ Reference DB Mapping อ้างถึง")
    if doc_short_name(topic.file) in WORKFLOW_TRIGGER_CONTRACTS:
        add("workflow engine", "BE/LLDD-BE-Workflow-Engine-Definition",
            "นิยาม state/route/event ที่หัวข้อ Workflow Trigger Event Contract เรียกใช้")
    if topic.track in {"BE", "Job"} and topic.file != "BE/LLDD-BE-Integration-SBP-Platform":
        add("แพลตฟอร์มระบบเดิม", "BE/LLDD-BE-Integration-SBP-Platform",
            "header จาก BFF (`x-api-key` / `x-user-*`) · การ reuse ตารางและ service ของระบบ SBP เดิม")

    # 5) ลำดับงาน — ต้องจบก่อนถึงเริ่มฉบับนี้ได้
    for dep in sorted(document_dependencies(list(index.values())).get(topic.file, set())):
        add("ต้องจบก่อน (ลำดับงาน)", dep, "เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง")

    order = {"ใช้ endpoint ของ": 0, "ถูกเรียกจาก": 1, "สัญญากลาง": 2, "โครงสร้างข้อมูล": 3,
             "workflow engine": 4, "แพลตฟอร์มระบบเดิม": 5, "ต้องจบก่อน (ลำดับงาน)": 6}
    rows.sort(key=lambda r: (order.get(r[0], 9), r[1]))
    return [[r[0], f"**{r[1]}**", r[2]] for r in rows]


def related_documents_blocks(topic: "Topic") -> list[dict[str, Any]]:
    rows = related_documents(topic)
    if not rows:
        return []
    return [
        h(2, "1.1 เอกสาร LLDD ที่เกี่ยวข้อง"),
        p("ตารางนี้สร้างจาก endpoint และตารางที่เอกสารฉบับนี้ประกาศไว้จริง — อ่านฉบับที่อยู่ในตารางก่อนลงมือ "
          "เพื่อไม่ให้สัญญา request/response หรือชื่อคอลัมน์หลุดจากกัน"),
        table(["ความสัมพันธ์", "เอกสาร LLDD", "เกี่ยวข้องตรงไหน"], rows),
    ]


# ═══════════════════════ Sequence Diagram (สร้างจากข้อมูลของแต่ละฉบับ) ═══════════════════════
# ผู้แสดง (lifeline) และลำดับข้อความมาจาก topic.apis / topic.db_tables / WORKFLOW_TRIGGER_CONTRACTS
# ของเอกสารฉบับนั้นเอง จึงไม่ต้องเขียนมือทีละฉบับและไม่มีทางหลุดจากสัญญาในหัวข้อ 7

EXTERNAL_LANE_HINTS: list[tuple[tuple[str, ...], str, str]] = [
    (("RabbitMQ", "sta.compensation.result"), "RabbitMQ", "message ถึงระบบ STA"),
    (("EAI S3", "S3", "upload-file-aws"), "EAI S3", "พื้นที่แลกไฟล์กับ IAS/MIS"),
    (("ALLMAP",), "ALLMAP", "SQL Server view ร้าน/คู่แข่ง"),
    (("IAS", "MIS", "AMS06001"), "IAS / MIS", "ระบบปลายทางยอดขาย"),
    (("email-lib", "sendEmail", "อีเมล"), "email-lib", "ตัวส่งอีเมลกลางของ SBP"),
]


def _db_ops(topic: "Topic") -> tuple[list[str], list[str]]:
    """ตารางที่อ่าน/เขียน — แตกแถวที่รวมหลายตารางไว้ด้วย " / " แล้วตัดชื่อซ้ำออก"""
    reads: list[str] = []
    writes: list[str] = []
    for row in topic.db_tables:
        rw = str(row[1]).upper()
        for name in str(row[0]).split("(")[0].split("/"):
            name = name.strip()
            if not name:
                continue
            # ตาราง workflow_* เป็นของ engine — เดินผ่าน lib เท่านั้น จึงไปอยู่บนเส้น @srm/glb-workflow
            # ไม่ใช่เส้น SGI Database (กันภาพสื่อว่า SGI เขียนตารางของ lib ตรง ๆ)
            if name.startswith("workflow_"):
                continue
            if "R" in rw and name not in reads:
                reads.append(name)
            if "W" in rw and name not in writes:
                writes.append(name)
    return reads[:3], writes[:3]


def _external_lanes(topic: "Topic") -> list[tuple[str, str]]:
    haystack = " ".join([topic.objective] + topic.scope + topic.flow + [str(r[0]) + str(r[2]) for r in topic.db_tables])
    found: list[tuple[str, str]] = []
    for keys, title, subtitle in EXTERNAL_LANE_HINTS:
        if any(k in haystack for k in keys) and (title, subtitle) not in found:
            found.append((title, subtitle))
    return found[:2]


def _endpoint_label(topic: "Topic", limit: int = 2) -> str:
    if not topic.apis:
        return "เรียกผ่านสัญญากลาง (ไม่มี endpoint ของตัวเอง)"
    shown = [f"{a.method} {a.path}" for a in topic.apis[:limit]]
    more = len(topic.apis) - len(shown)
    return " · ".join(shown) + (f" (+ อีก {more} เส้น · ดูหัวข้อ 7)" if more > 0 else "")


def _prune_unused_lanes(lanes: list[tuple[str, str]],
                        msgs: list[tuple[int, int, str, str]]) -> tuple[list[tuple[str, str]], list[tuple[int, int, str, str]]]:
    """ตัด lifeline ที่ไม่มีข้อความวิ่งเข้า/ออกเลย แล้ว remap index — กันเส้นเปล่าในภาพ"""
    used = {i for m in msgs for i in (m[0], m[1])}
    if len(used) == len(lanes):
        return lanes, msgs
    keep = [i for i in range(len(lanes)) if i in used]
    remap = {old: new for new, old in enumerate(keep)}
    return [lanes[i] for i in keep], [(remap[s], remap[d], lab, k) for s, d, lab, k in msgs]


def sequence_spec(topic: "Topic") -> tuple[list[tuple[str, str]], list[tuple[int, int, str, str]]]:
    """คืน (lifelines, messages) — message = (จาก, ถึง, ข้อความ, ชนิด: call/return/self)"""
    reads, writes = _db_ops(topic)
    has_engine = doc_short_name(topic.file) in WORKFLOW_TRIGGER_CONTRACTS
    externals = _external_lanes(topic)
    read_txt = ", ".join(reads) if reads else "ตารางที่หัวข้อ Reference DB Mapping ระบุ"
    write_txt = ", ".join(writes) if writes else None
    msgs: list[tuple[int, int, str, str]] = []

    if is_job_doc(topic.file):
        lanes = [("Scheduler", "cron / CLI · backend config"),
                 (topic.title.split(" - ")[-1][:34], "Job (NestJS)"),
                 ("SGI Database", "PostgreSQL · schema sps_store")]
        ext_base = len(lanes)
        lanes += externals
        eng = -1
        if has_engine:
            eng = len(lanes)
            lanes.append(("@srm/glb-workflow", "workflow engine (lib)"))
        msgs.append((0, 1, "ทริกตามรอบที่ตั้งไว้ (cron) หรือสั่งรันมือผ่าน CLI/runbook", "call"))
        msgs.append((1, 2, f"อ่านข้อมูลตั้งต้น — {read_txt}", "call"))
        msgs.append((2, 1, "ชุดข้อมูลที่เข้าเงื่อนไขของรอบนี้", "return"))
        for i, (name, _) in enumerate(externals):
            msgs.append((1, ext_base + i, f"รับ/ส่งข้อมูลกับ {name} ตามสัญญาในหัวข้อ 5", "call"))
            msgs.append((ext_base + i, 1, "ผลลัพธ์ / ACK", "return"))
        if has_engine:
            msgs.append((1, eng, "initializeWorkflow() + addPreApprover() — ห้าม INSERT ตาราง workflow_* ตรง", "call"))
            msgs.append((eng, 1, "transactionId ของ instance ที่เปิดให้", "return"))
        msgs.append((1, 2, f"เขียนผลการรัน — {write_txt or 'ตารางผลลัพธ์ของ job นี้'} + sgi_interface_transactions", "call"))
        msgs.append((1, 0, "สรุปผล/สถานะการรันลง application log (สำเร็จ · ข้าม · ล้มเหลว)", "return"))
        return _prune_unused_lanes(lanes, msgs)

    if topic.track == "FE":
        lanes = [("ผู้ใช้", "ตามสิทธิ์ของ section_code"),
                 ("หน้าจอ FE", "sbp-portal (Next.js) · route /sgi/*"),
                 ("BFF", "srm-sps-spsap-sbp-bff"),
                 ("SGI Backend", "store-backend · /api/v1/sgi"),
                 ("SGI Database", "PostgreSQL")]
        first_action = topic.actions[0][0] if topic.actions else "เปิดหน้าจอ"
        msgs.append((0, 1, f"{first_action} (ดูรายการปุ่มทั้งหมดในหัวข้อ 6)", "call"))
        msgs.append((1, 2, _endpoint_label(topic), "call"))
        msgs.append((2, 3, "ส่งต่อพร้อม x-api-key + x-user-id / x-user-group-id / x-user-full-name", "call"))
        msgs.append((3, 4, f"query / persist — {read_txt}", "call"))
        msgs.append((4, 3, "ผลลัพธ์ระดับแถว", "return"))
        msgs.append((3, 2, "{ success: true, data } — envelope กลางตาม Common Contracts", "return"))
        msgs.append((2, 1, "ส่งกลับหน้าจอ (error map เป็นข้อความไทยตาม Integration Contracts)", "return"))
        msgs.append((1, 0, "แสดงผล / toast / เปลี่ยนสถานะปุ่มตามสิทธิ์", "return"))
        return _prune_unused_lanes(lanes, msgs)

    # เอกสาร BE ที่ไม่มี endpoint ของตัวเอง (โครงสร้างข้อมูล · migration · นิยาม engine · การต่อแพลตฟอร์ม)
    # เป็นงานตั้งค่า/ย้ายข้อมูล ไม่ใช่ request-response — ลำดับจึงมาจากขั้นตอนในหัวข้อ Processing Flow
    if not topic.apis:
        lanes = [("ผู้ดำเนินการ", "dev / ops ตาม runbook"),
                 ("สคริปต์ของ SGI", "store-backend · migration / setup"),
                 ("SGI Database", "PostgreSQL")]
        ext_base = len(lanes)
        lanes += externals
        eng = -1
        if has_engine or "workflow" in topic.file.lower():
            eng = len(lanes)
            lanes.append(("@srm/glb-workflow", "workflow engine (lib)"))
        msgs.append((0, 1, "เริ่มงานตามลำดับใน runbook (ดูหัวข้อ Processing Flow)", "call"))
        used_ext = 0
        for step in topic.flow[:6]:
            low = step.lower()
            if eng >= 0 and ("workflow" in low or "engine" in low or "approver" in low):
                msgs.append((1, eng, step[:96], "call"))
            elif externals and used_ext < len(externals) and any(k.lower() in low for k in ("s3", "rabbit", "allmap", "ias", "mail", "อีเมล")):
                msgs.append((1, ext_base + used_ext, step[:96], "call"))
                used_ext += 1
            elif any(k in low for k in ("table", "ตาราง", "ddl", "insert", "select", "migrate", "index", "seed", "sgi_")):
                msgs.append((1, 2, step[:96], "call"))
            else:
                msgs.append((1, 1, step[:96], "self"))
        msgs.append((2, 1, "ผลการรัน / จำนวนแถวที่ได้", "return"))
        msgs.append((1, 0, "สรุปผลลง runbook + application log (ผ่าน / ต้องย้อนกลับ)", "return"))
        return _prune_unused_lanes(lanes, msgs)

    lanes = [("ผู้เรียก", "หน้าจอ FE (sbp-portal) หรือ service ภายใน"),
             ("BFF", "srm-sps-spsap-sbp-bff"),
             ("SGI Backend", "store-backend · /api/v1/sgi"),
             ("SGI Database", "PostgreSQL")]
    ext_base = len(lanes)
    lanes += externals
    eng = -1
    if has_engine:
        eng = len(lanes)
        lanes.append(("@srm/glb-workflow", "workflow engine (lib)"))
    msgs.append((0, 1, _endpoint_label(topic), "call"))
    msgs.append((1, 2, "ส่งต่อพร้อม x-api-key + x-user-* (ตรวจที่ HttpHeaderGuard)", "call"))
    msgs.append((2, 2, "validate payload + ตรวจสิทธิ์เขียนจาก group + สถานะเอกสาร", "self"))
    msgs.append((2, 3, f"อ่านข้อมูล — {read_txt}", "call"))
    msgs.append((3, 2, "ผลลัพธ์ระดับแถว", "return"))
    if has_engine:
        msgs.append((2, eng, "eventWorkflow() / getTransaction() — ภายใน transaction เดียวกับการเขียนของ SGI", "call"))
        msgs.append((eng, 2, "state ถัดไป + transactionId", "return"))
    if write_txt:
        msgs.append((2, 3, f"เขียนผล — {write_txt}", "call"))
    for i, (name, _) in enumerate(externals):
        msgs.append((2, ext_base + i, f"ส่งต่อ/รับข้อมูลกับ {name}", "call"))
        msgs.append((ext_base + i, 2, "ผลลัพธ์ / ACK", "return"))
    msgs.append((2, 1, "{ success: true, data } หรือ { success: false, error: { code, message } }", "return"))
    msgs.append((1, 0, "ส่งกลับผู้เรียก", "return"))
    return _prune_unused_lanes(lanes, msgs)


def draw_sequence_diagram(title: str, lanes: list[tuple[str, str]],
                          messages: list[tuple[int, int, str, str]], out_rel: str) -> str:
    out_path = ROOT / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font_path = FONT if os.path.exists(FONT) else "/System/Library/Fonts/Supplemental/Arial.ttf"
    f_title = ImageFont.truetype(font_path, 24)
    f_lane = ImageFont.truetype(font_path, 16)
    f_sub = ImageFont.truetype(font_path, 12)
    f_msg = ImageFont.truetype(font_path, 13)

    n = len(lanes)
    lane_w, margin, head_h, head_top = 300, 60, 76, 84
    width = margin * 2 + lane_w * n
    row_h = 62
    body_top = head_top + head_h + 46
    height = body_top + len(messages) * row_h + 70
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    d.text((margin, 34), title, fill="#0B2545", font=f_title)

    cx = [margin + lane_w * i + lane_w // 2 for i in range(n)]
    palette = ["#2F6FED", "#7C3AED", "#0F7B6C", "#B45309", "#BE185D", "#475569"]
    for i, (name, sub) in enumerate(lanes):
        colour = palette[i % len(palette)]
        x0, x1 = cx[i] - lane_w // 2 + 16, cx[i] + lane_w // 2 - 16
        d.rounded_rectangle([x0, head_top, x1, head_top + head_h], radius=12,
                            fill="#F6F8FE", outline=colour, width=3)
        d.text((cx[i], head_top + 26), name, fill=colour, font=f_lane, anchor="mm")
        d.text((cx[i], head_top + 52), sub, fill="#67707C", font=f_sub, anchor="mm")
        y = head_top + head_h
        while y < height - 40:                      # lifeline แบบเส้นประ
            d.line([cx[i], y, cx[i], min(y + 8, height - 40)], fill="#C4CDD8", width=2)
            y += 15

    for idx, (src, dst, label, kind) in enumerate(messages):
        y = body_top + idx * row_h
        colour = "#2B3440" if kind == "call" else "#0F7B6C"
        if kind == "self":
            x = cx[src]
            d.line([x, y, x + 46, y], fill="#8A97A5", width=2)
            d.line([x + 46, y, x + 46, y + 22], fill="#8A97A5", width=2)
            d.line([x + 46, y + 22, x + 8, y + 22], fill="#8A97A5", width=2)
            d.polygon([(x + 8, y + 22), (x + 20, y + 17), (x + 20, y + 27)], fill="#8A97A5")
            tw = d.textlength(label, font=f_msg)
            d.rectangle([x + 52, y + 1, x + 60 + tw, y + 21], fill="white")
            d.text((x + 56, y + 11), label, fill="#5D6B7A", font=f_msg, anchor="lm")
            continue
        x0, x1 = cx[src], cx[dst]
        dash = kind == "return"
        if dash:
            step, pos = 12, min(x0, x1)
            while pos < max(x0, x1):
                d.line([pos, y, min(pos + 7, max(x0, x1)), y], fill=colour, width=2)
                pos += step
        else:
            d.line([x0, y, x1, y], fill=colour, width=2)
        head = 11 if x1 > x0 else -11
        d.polygon([(x1, y), (x1 - head, y - 6), (x1 - head, y + 6)], fill=colour)
        mid = (x0 + x1) // 2
        avail = abs(x1 - x0) + lane_w - 40
        text = label
        while d.textlength(text, font=f_msg) > avail and len(text) > 12:
            text = text[:-2]
        if text != label:
            text = text[:-1] + "…"
        # กล่องพื้นขาวหลังข้อความ — ไม่ให้ตัวหนังสือทับเส้น lifeline ที่วิ่งผ่าน
        tw = d.textlength(text, font=f_msg)
        d.rectangle([mid - tw / 2 - 5, y - 22, mid + tw / 2 + 5, y - 3], fill="white")
        d.text((mid, y - 12), text, fill=colour, font=f_msg, anchor="mm")

    d.text((margin, height - 34),
           "เส้นทึบ = การเรียก · เส้นประ = การตอบกลับ · ลูปในตัว = งานที่ทำภายใน service เอง",
           fill="#8A97A5", font=f_sub)
    img.save(out_path)
    return out_rel


def build_topic_schedule(topics_list: list[Topic], start_date: date = LLDD_START_DATE) -> dict[str, tuple[date, date]]:
    """จัดตารางแบบรู้จัก dependency — เจ้าของหนึ่งคนทำได้ทีละฉบับ และผู้บริโภคเริ่มหลังผู้ผลิตจบ

    ยังคงการอัดชั่วโมงต่อคนแบบเดิม (เอกสาร 9 ชม. กินวันครึ่ง ฉบับถัดไปเริ่มกลางวันได้)
    แต่เมื่อ dependency บังคับให้เริ่มช้ากว่านั้น จะดันชั่วโมงสะสมของเจ้าของไปที่ต้นวันนั้นเลย
    """
    preds = document_dependencies(topics_list)
    priority = {topic.file: index for index, topic in enumerate(topics_list)}
    by_file = {topic.file: topic for topic in topics_list}
    used_hours_by_owner: dict[str, int] = {}
    start_day: dict[str, int] = {}
    end_day: dict[str, int] = {}
    pending = set(by_file)
    while pending:
        # sorted() ไม่ใช่แค่ความสวย — pending เป็น set ลำดับจึงไม่คงที่ข้ามรัน
        # ถึง min() ข้างล่างจะมี priority เป็นตัวตัดสินสุดท้ายอยู่แล้ว ก็ตรึงลำดับตั้งแต่ต้นทางไว้
        ready = [f for f in sorted(pending) if not (preds[f] & pending)]
        if not ready:
            raise ValueError(f"Cyclic document dependency among: {sorted(pending)}")

        def earliest_start(file_key: str) -> int:
            owner_free = int(used_hours_by_owner.get(by_file[file_key].owner, 0) // HOURS_PER_DAY)
            blocked = max((end_day[p] + 1 for p in preds[file_key]), default=0)
            return max(owner_free, blocked)

        # เลือกงานที่ "เริ่มได้เร็วที่สุดจริง" ก่อน แล้วจึงใช้ลำดับใน MAIN_INDEX_ORDER ตัดสินเสมอ
        # (ถ้าเรียงตามลำดับประกาศอย่างเดียว งานที่ติด dependency จะถูกดันไปท้ายแถวโดยไม่จำเป็น)
        file_key = min(ready, key=lambda f: (earliest_start(f), priority[f]))
        topic = by_file[file_key]
        used_hours = used_hours_by_owner.get(topic.owner, 0)
        start_offset = earliest_start(file_key)
        used_hours = max(used_hours, start_offset * HOURS_PER_DAY)
        start_day[file_key] = start_offset
        # ใช้ชั่วโมงรวม (implementation + unit test) — unit test เป็นงานที่ต้องทำจริง
        # ถ้าคิดแค่ implementation แผนจะสั้นกว่าความจริง 154 ชั่วโมงทั้งโครงการ
        end_day[file_key] = int((used_hours + total_hours(topic) - 1) // HOURS_PER_DAY)
        used_hours_by_owner[topic.owner] = used_hours + total_hours(topic)
        pending.discard(file_key)
    schedule: dict[str, tuple[date, date]] = {}
    for file_key in by_file:
        start = add_workdays(start_date, start_day[file_key] + 1)
        end = add_workdays(start_date, end_day[file_key] + 1)
        if start < start_date or end < start:
            raise ValueError(f"Invalid schedule window for {file_key}: {start} - {end}")
        schedule[file_key] = (start, end)
    return schedule


def schedule_finish_date(topics_list: list[Topic], start_date: date = LLDD_START_DATE) -> date:
    """วันจบจริงของแผน — คำนวณจากตาราง ไม่ใช่ค่าคงที่ที่ตั้งไว้ล่วงหน้า"""
    return max(end for _, end in build_topic_schedule(topics_list, start_date).values())


def dependency_steps(topics_list: list[Topic]) -> dict[str, int]:
    """ลำดับขั้นของงาน = ความลึกที่ยาวที่สุดใน dependency graph + 1

    เอกสารที่อยู่ "ขั้น" เดียวกันไม่มีใครรอใคร จึงลงมือพร้อมกันได้
    ใช้แทนวันที่ในเอกสารส่งมอบ — สื่อลำดับงานโดยไม่ผูกกับปฏิทิน
    """
    preds = document_dependencies(topics_list)
    steps: dict[str, int] = {}

    def depth(file_key: str, seen: frozenset[str] = frozenset()) -> int:
        if file_key in steps:
            return steps[file_key]
        if file_key in seen:
            raise ValueError(f"Cyclic document dependency at {file_key}")
        parents = preds.get(file_key, set())
        steps[file_key] = 1 + max((depth(p, seen | {file_key}) for p in parents), default=0)
        return steps[file_key]

    for topic in topics_list:
        depth(topic.file)
    return steps


_PLANNED_FINISH: date | None = None


def planned_finish_date() -> date:
    """วันจบของแผนทั้งชุด (cache ไว้ เพราะถูกเรียกจากหลายที่ตอนเรนเดอร์)"""
    global _PLANNED_FINISH
    if _PLANNED_FINISH is None:
        counted = [t for t in main_index_ordered(topics()) if not is_document_detail_role_doc(t.file)]
        _PLANNED_FINISH = schedule_finish_date(counted)
    return _PLANNED_FINISH


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
    if bold:
        runs = [para.add_run(str(text) if text is not None else "")]
        runs[0].bold = True
    else:
        # แปลง markdown inline ในเซลล์ตารางด้วย (หมายเหตุของ skeleton ใช้ **bold** / `code` เยอะ)
        add_md_runs(para, text)
        runs = list(para.runs) or [para.add_run("")]
    for run in runs:
        set_run_fonts(run, "Courier New" if run.font.name == "Courier New" else "Arial")
        run.font.size = Pt(9)
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
    set_run_fonts(run, "Courier New")
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


_MD_INLINE_RE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`", re.S)


def add_md_runs(paragraph, text: Any) -> None:
    """เขียน text ลง paragraph โดยแปลง markdown inline (**bold** / `code`) เป็น run จริง

    ใช้เฉพาะ block ชนิด paragraph/bullet — block ชนิด code ต้องคงข้อความดิบไว้
    """
    raw = str(text if text is not None else "")
    pos = 0
    for m in _MD_INLINE_RE.finditer(raw):
        if m.start() > pos:
            paragraph.add_run(raw[pos:m.start()])
        if m.group(1) is not None:
            paragraph.add_run(m.group(1)).bold = True
        else:
            body = m.group(2)
            run = paragraph.add_run(body)
            # Courier New ไม่การันตี glyph ไทย — ใช้เฉพาะ ASCII ล้วน (เหตุผลเดียวกับฝั่ง PDF)
            try:
                body.encode("ascii")
                set_run_fonts(run, "Courier New")
            except UnicodeEncodeError:
                run.font.color.rgb = RGBColor.from_string("8A3324")
        pos = m.end()
    if pos < len(raw):
        paragraph.add_run(raw[pos:])


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
    set_style_fonts(styles["Normal"], "Arial")
    styles["Normal"].font.size = Pt(10)
    for style_name, size, color in [
        ("Heading 1", 16, "1F4D78"),
        ("Heading 2", 13, "2E74B5"),
        ("Heading 3", 11, "1F4D78"),
        ("Heading 4", 10, "2E74B5"),
    ]:
        st = styles[style_name]
        st.font.name = "Arial"
        set_style_fonts(st, "Arial")
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.keep_together = True

    title_p = doc.add_paragraph()
    title_run = title_p.add_run(title)
    set_run_fonts(title_run, "Arial")
    title_run.font.size = Pt(20)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor.from_string("0B2545")
    doc.add_paragraph("SBP Mall - ระบบประกันรายได้ | Low Level Design Document")

    header = section.header.paragraphs[0]
    header.text = title
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        set_run_fonts(run, "Arial")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor.from_string("66717F")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("หน้า ")
    set_run_fonts(footer_run, "Arial")
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
        elif btype in ("h3", "h4"):
            para = doc.add_heading(block["text"], level=3 if btype == "h3" else 4)
            para.paragraph_format.page_break_before = page_break_pending
            page_break_pending = False
            para.paragraph_format.keep_with_next = True
            para.paragraph_format.keep_together = True
            heading_pending = True
        elif btype == "p":
            para = doc.add_paragraph()
            add_md_runs(para, block["text"])
            if heading_pending:
                para.paragraph_format.keep_with_next = False
            heading_pending = False
        elif btype == "bullets":
            for item in block["items"]:
                para = doc.add_paragraph(style="List Bullet")
                add_md_runs(para, item)
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
            set_run_fonts(run, "Courier New")
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
        "h4": ParagraphStyle("H4TH", parent=ss["Heading4"], fontName=base, fontSize=9.5, leading=13, textColor=colors.HexColor("#2E74B5"), spaceBefore=5, spaceAfter=2),
        "body": ParagraphStyle("BodyTH", parent=ss["BodyText"], fontName=base, fontSize=9.2, leading=13, spaceAfter=5),
        "small": ParagraphStyle("SmallTH", parent=ss["BodyText"], fontName=base, fontSize=8, leading=10, spaceAfter=3),
        "code": ParagraphStyle("CodeTH", parent=ss["Code"], fontName=base, fontSize=7.4, leading=9, backColor=colors.HexColor("#F4F6F9"), borderPadding=4),
        "java": ParagraphStyle("JavaTH", parent=ss["Code"], fontName=base, fontSize=6.4, leading=7.8, backColor=colors.HexColor("#F4F6F9"), borderPadding=4),
    }


_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
_MD_CODE_RE = re.compile(r"`([^`]+)`")


# ---------------------------------------------------------------------------
# PDF: แปลง emoji เป็นสัญลักษณ์ที่ฟอนต์มี glyph จริง
# ---------------------------------------------------------------------------
# เจอจริง 2026-09-09 (ผู้ใช้ชี้): PDF แสดง ⚠️ 🔴 ✅ เป็นกล่อง □ เพราะฟอนต์ที่ใช้สร้าง PDF
# (Arial Unicode) **ไม่มี glyph emoji เลยสักตัว** — ตรวจแล้วมีอักขระแบบนี้ 964 จุดในชุดเอกสาร
# แก้เฉพาะ "ตอนเรนเดอร์ PDF" เท่านั้น — md/html/docx ยังแสดง emoji ตามเดิมเพราะที่นั่นแสดงได้ปกติ
#
# ตัวแทนเลือกจากอักขระที่ยืนยันแล้วว่าฟอนต์มี และสื่อความหมายเดิมได้ในงานพิมพ์ขาวดำ
_PDF_GLYPH_FALLBACK = {
    "\uFE0F": "",          # variation selector — ตัดทิ้ง ไม่งั้นกลายเป็นกล่องตัวที่สอง
    "\uFEFF": "",          # zero-width no-break space
    "\u26A0": "▲",         # ⚠ คำเตือน
    "\U0001F534": "●",     # 🔴 สำคัญมาก
    "\U0001F7E0": "●",     # 🟠
    "\u2705": "✓",         # ✅ ผ่าน/ปิดแล้ว
    "\u274C": "✗",         # ❌ ไม่ทำ/ตัดออก
    "\u23ED": "»",         # ⏭ ข้าม/ยังไม่ทำ (เพิ่ม 2026-09-16)
    "\U0001F7E2": "○",     # 🟢 dry-run / ปลอดภัย (เพิ่ม 2026-09-16)
    "\U0001F7E1": "◐",     # 🟡 trial / กึ่งกลาง (เพิ่ม 2026-09-16)
    "\U0001F6D1": "✗",     # 🛑 หยุด/ROLLBACK (เพิ่ม 2026-09-17)
    "\u26D4": "✗",         # ⛔ ห้าม
    "\u23F3": "⌛",         # ⏳ ยังค้าง
    "\u23F1": "⌛",         # ⏱
    "\u23F0": "⌛",         # ⏰
    "\u2B07": "↓",         # ⬇
    "\U0001F449": "→",     # 👉
    "\u2139": "※",         # ℹ
    "\u2699": "◆",         # ⚙
    "\U0001F517": "◇",     # 🔗
    "\U0001F464": "○",     # 👤
    "\U0001F4F6": "▪",     # 📶
    "\U0001F5C4": "▣",     # 🗄
    "\U0001F5C2": "▣",     # 🗂
    "\U0001F4C2": "▣",     # 📂
    "\U0001F4C4": "▫",     # 📄
    "\U0001F511": "◆",     # 🔑
    "\U0001F512": "◆",     # 🔒
    "\U0001F50C": "◆",     # 🔌
    "\U0001F4BE": "▣",     # 💾
    "\U0001F4C5": "▫",     # 📅
    "\U0001F4E6": "▣",     # 📦
    "\U0001F3E0": "▫",     # 🏠
    "\U0001F3A8": "◇",     # 🎨
    "\U0001F7E9": "▪",     # 🟩
    "\U0001F7E6": "▪",     # 🟦
    "\U0001F7EA": "▪",     # 🟪
}
_PDF_GLYPH_RE = re.compile("|".join(map(re.escape, _PDF_GLYPH_FALLBACK)))


def pdf_safe_text(text: Any) -> str:
    """แทน emoji ด้วยสัญลักษณ์ที่ฟอนต์ PDF มี glyph จริง (ใช้เฉพาะทาง PDF)"""
    return _PDF_GLYPH_RE.sub(lambda m: _PDF_GLYPH_FALLBACK[m.group(0)], str(text))


def para(text: Any, style: ParagraphStyle) -> Paragraph:
    esc = pdf_safe_text(text if text is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    esc = esc.replace("\n", "<br/>")
    # แปลง markdown inline ที่ generator ใช้อยู่ (ไม่งั้น PDF จะโชว์ดอกจันดิบ)
    esc = _MD_BOLD_RE.sub(r"<b>\1</b>", esc)
    # inline code: Courier ไม่มี glyph ภาษาไทย ถ้าสลับ face จะได้ ■■■ ทั้งก้อน
    # จึงใช้ Courier เฉพาะเนื้อหาที่เป็น ASCII ล้วน · ที่เหลือคงฟอนต์ไทยไว้แล้วใช้สีแทนเพื่อยังเห็นว่าเป็น code
    def _inline_code(m: "re.Match[str]") -> str:
        body = m.group(1)
        try:
            body.encode("ascii")
        except UnicodeEncodeError:
            return f"<font color='#8A3324'>{body}</font>"
        return f"<font face='Courier'>{body}</font>"

    esc = _MD_CODE_RE.sub(_inline_code, esc)
    return Paragraph(esc, style)


def code_para(text: Any, style: ParagraphStyle) -> Paragraph:
    escaped_lines = []
    for line in pdf_safe_text(text if text is not None else "").splitlines():
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
    """กล่องตัวอย่าง payload

    ⚠️ payload ยาว ๆ ต้อง **แบ่งข้ามหน้าได้** — reportlab โยน LayoutError ทันทีถ้า
    flowable สูงเกินหนึ่งหน้าแล้วแบ่งไม่ได้ (เจอจริง 2026-09-09 ตอนขยาย response
    ของ GET /sgi/document/{docNo} ให้ครบ 10 การ์ด แล้ว build ทั้งชุดพังทันที)
    จึงหั่นเนื้อ payload เป็นก้อนละไม่เกิน ~46 บรรทัด แล้วปล่อยให้ตารางแบ่งแถวได้เอง
    """
    lines = text.split("\n")
    chunk = 46
    body_rows = [[code_para("\n".join(lines[i:i + chunk]), styles["code"])]
                 for i in range(0, max(1, len(lines)), chunk)]
    data = [[para(title, styles["small"])]] + body_rows
    t = Table(data, colWidths=[7.0 * inch], splitByRow=1, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BFD0E6")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBFF")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFE")),
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
    story: list[Any] = [Paragraph(pdf_safe_text(title), styles["title"]), para("SBP Mall - ระบบประกันรายได้ | Low Level Design Document", styles["body"]), Spacer(1, 8)]
    figure_no = 0
    for block in blocks:
        btype = block["type"]
        if btype in ("h1", "h2", "h3", "h4"):
            min_space = {"h1": 1.6 * inch, "h2": 1.15 * inch, "h3": 0.9 * inch, "h4": 0.8 * inch}[btype]
            story.append(CondPageBreak(min_space))
            story.append(Paragraph(pdf_safe_text(block["text"]), styles[btype]))
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
            # KeepTogether เฉพาะ payload สั้น — ก้อนยาวต้องปล่อยให้แบ่งข้ามหน้า
            # ไม่งั้น reportlab โยน LayoutError (เจอจริง 2026-09-09)
            if block["text"].count("\n") < 40:
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
    if not document_key.startswith("Jobs/"):
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
    is_job = document_key.startswith("Jobs/")
    combined = [*delivery_intro_blocks(is_job), *blocks, *legacy_java_appendix_blocks(document_key)]
    return scrub_lldd_text(title), scrub_lldd_blocks(combined, preserve_java=is_job)


# tag HTML ที่ตั้งใจใช้จริงในเอกสาร — นอกรายการนี้ถือว่าเป็น "ข้อความที่หน้าตาเหมือน tag"
_REAL_HTML_TAGS = {
    "a", "b", "br", "code", "details", "div", "em", "hr", "i", "iframe", "img", "li",
    "ol", "p", "small", "span", "strong", "sub", "summary", "sup", "table", "td", "th",
    "tr", "u", "ul",
}
_TAG_LIKE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)(\s*/?)>")


def md_escape_pseudo_tags(text: str) -> str:
    """escape `<...>` ที่ไม่ใช่ tag จริง ไม่ให้ renderer กลืนหายไป

    ⚠️ เจอจริง 2026-09-07: ชื่อเล่นในรูป `Aphiwit <Bank> Khammoon` ตรงรูปแบบ HTML open tag พอดี
    renderer จึงปล่อยผ่านเป็น raw HTML แล้ว browser ทิ้ง element ที่ไม่รู้จัก — **ชื่อเล่นหายทั้งหมด**
    เรื่องเดียวกันกินคอลัมน์ Type ของตารางสัญญา API ด้วย (`array<object>` เหลือแค่ `array`)
    และตัวยึดอย่าง `<YYYYMM>` · `<AccessDenied>` · `<JWT>` ก็หายเหมือนกัน
    """
    if "<" not in text:
        return text

    def repl(m: "re.Match[str]") -> str:
        if m.group(2).lower() in _REAL_HTML_TAGS:
            return m.group(0)
        # ใช้ HTML entity ไม่ใช่ backslash escape — ในเซลล์ตาราง ตัว `\<` จะโผล่เป็นแบ็กสแลชจริง
        return "&lt;" + m.group(1) + m.group(2) + m.group(3) + "&gt;"

    return _TAG_LIKE.sub(repl, text)


def build_md(title: str, blocks: list[dict[str, Any]], out_path: Path) -> None:
    lines = [f"# {md_escape_pseudo_tags(title)}", "",
             "SBP Mall - ระบบประกันรายได้ | Low Level Design Document", ""]
    figure_no = 0
    for raw_block in blocks:
        # escape เฉพาะ block ที่ renderer ตีความเป็น HTML — code/payload อยู่ใน fence ปลอดภัยอยู่แล้ว
        block = raw_block
        if raw_block["type"] not in ("code", "payload"):
            block = map_block_text(dict(raw_block), md_escape_pseudo_tags)
        btype = block["type"]
        if btype == "h1":
            lines.extend([f"## {block['text']}", ""])
        elif btype == "h2":
            lines.extend([f"### {block['text']}", ""])
        elif btype == "h3":
            lines.extend([f"#### {block['text']}", ""])
        elif btype == "h4":
            lines.extend([f"##### {block['text']}", ""])
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


# เอกสารที่ไม่ผ่าน skeleton generator: ไม่มี REST endpoint ของตัวเอง (skeleton จะได้แต่โครงว่าง)
SKELETON_SKIP_FILES = {
    "FE/LLDD-FE-Testing-Delivery",
    "BE/LLDD-BE-Database-Structure",
    "BE/LLDD-BE-Data-Migration-Cutover",
    "BE/LLDD-BE-Integration-SBP-Platform",
    "BE/LLDD-BE-Workflow-Engine-Definition",
}
_SKELETON_SQL_CACHE: dict[str, str] | None = None
_BATCH_JOBS_BY_NO: dict[str, dict[str, Any]] | None = None


def api_sql_map() -> dict[str, str]:
    """SQL_BY_PATH จาก plan-api.html (อ่านครั้งเดียวแล้ว cache — การอ่านต้องเรียก node)"""
    global _SKELETON_SQL_CACHE
    if _SKELETON_SQL_CACHE is None:
        try:
            _SKELETON_SQL_CACHE = plan_api_sql_by_path()
        except Exception:
            _SKELETON_SQL_CACHE = {}
    return _SKELETON_SQL_CACHE


def batch_job_by_no(job_no: str) -> dict[str, Any] | None:
    """dict ของ job ตัวนั้นจาก JOBS ใน job-batch.html (cache ทั้ง array ไว้ครั้งเดียว)"""
    global _BATCH_JOBS_BY_NO
    if _BATCH_JOBS_BY_NO is None:
        try:
            _BATCH_JOBS_BY_NO = {str(job.get("no")): job for job in load_batch_jobs()}
        except Exception:
            _BATCH_JOBS_BY_NO = {}
    return _BATCH_JOBS_BY_NO.get(str(job_no))


def job_no_from_file(file_key: str) -> str:
    match = re.search(r"LLDD-BE-Job-([0-9]+[A-Za-z]?)-", file_key)
    return match.group(1) if match else ""


def is_job_doc(file_key: str) -> bool:
    return file_key.startswith("Jobs/")


def map_block_text(block: dict[str, Any], fn) -> dict[str, Any]:
    """apply fn กับทุก string ที่แสดงผลใน block เดียว (ใช้ renumber หัวข้อของ skeleton module)"""
    for key in ("text", "title", "caption"):
        if isinstance(block.get(key), str):
            block[key] = fn(block[key])
    for key in ("headers", "items"):
        if isinstance(block.get(key), list):
            block[key] = [fn(item) if isinstance(item, str) else item for item in block[key]]
    if isinstance(block.get("rows"), list):
        # แถวบางตารางเป็น tuple ไม่ใช่ list — ของเดิมข้ามไปเงียบ ๆ ทำให้ escape ไม่ทั่ว
        block["rows"] = [
            [fn(cell) if isinstance(cell, str) else cell for cell in row]
            if isinstance(row, (list, tuple)) else row
            for row in block["rows"]
        ]
    return block


_HEAD_ORDER = ["h1", "h2", "h3", "h4"]


def shift_heading(block: dict[str, Any], delta: int) -> dict[str, Any]:
    """เลื่อนระดับหัวข้อของ block เดียว (ค่าลบ = เลื่อนขึ้น)"""
    btype = block.get("type")
    if btype in _HEAD_ORDER:
        idx = max(0, min(len(_HEAD_ORDER) - 1, _HEAD_ORDER.index(btype) + delta))
        block["type"] = _HEAD_ORDER[idx]
    return block


def level_skeleton_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """จัดระดับหัวข้อของ skeleton ให้ต่อเนื่องกับหัวข้อหลักของเอกสาร

    กติกาเดียวกันทั้ง 3 track: หัวข้อ section = h1 (`##`) · ลูกโดยตรง = h2 (`###`) · หลาน = h3 (`####`)

    ⚠️ แก้ 2026-09-07: เดิมแต่ละ track จัดระดับคนละแบบ ผลคือหัวข้อ section เป็น `##` แต่ลูกเป็น `####`
    ข้ามระดับ H2 → H4 รวม 43 จุดใน 34 ไฟล์ ทำให้สารบัญและ accessibility ผิดโครง
    """
    out = [dict(b) for b in blocks]
    if out and out[0].get("type") in _HEAD_ORDER:
        out[0]["type"] = "h1"             # หัวข้อ section = ระดับเดียวกับหัวข้อหลักของเอกสาร
    child_levels = [_HEAD_ORDER.index(b["type"]) for b in out[1:] if b.get("type") in _HEAD_ORDER]
    if not child_levels:
        return out
    # เลื่อนทั้งชุดให้หัวข้อลูกที่ตื้นที่สุดมาอยู่ที่ h2 พอดี — ลำดับสัมพัทธ์ระหว่างลูกยังเท่าเดิม
    delta = 1 - min(child_levels)
    for block in out[1:]:
        shift_heading(block, delta)
    return out


def promote_skeleton_heading(block: dict[str, Any], numbers: set[str]) -> dict[str, Any]:
    """หัวข้อหลักของ module (h2 ขึ้นต้นด้วยเลข section) -> h1 พร้อมจุดให้ตรงกับหัวข้ออื่นในเอกสาร"""
    if block.get("type") != "h2":
        return block
    match = re.match(r"^(\d+)\s+(.*)$", str(block.get("text", "")))
    if match and match.group(1) in numbers:
        block["type"] = "h1"
        block["text"] = f"{match.group(1)}. {match.group(2)}"
    return block


def skeleton_code_blocks(topic: Topic, section_no: int) -> list[dict[str, Any]]:
    """Skeleton Code section ของเอกสารหนึ่งฉบับ โดยหัวข้อหลักเริ่มที่ `section_no`

    - เอกสาร Job (`Jobs/...`) -> lldd_skeleton_job (ctx: job dict จาก JOBS ใน job-batch.html)
    - เอกสาร BE อื่น            -> lldd_skeleton_be  (ctx: sql_by_path จาก SQL_BY_PATH ใน plan-api.html)
    - เอกสาร FE (ยกเว้น testing/delivery) -> lldd_skeleton_fe
    ใช้ h1 เป็นหัวข้อหลักเสมอ เพื่อให้นับต่อกับหัวข้ออื่นของ topic_blocks ได้
    """
    file_key = topic.file
    if file_key in SKELETON_SKIP_FILES:
        return []
    try:
        if is_job_doc(file_key):
            job_no = job_no_from_file(file_key)
            raw = job_skeleton_blocks(topic, {"job": batch_job_by_no(job_no)})
            if not raw:
                return []

            def renumber(text: str) -> str:
                return re.sub(
                    r"\b5\.(9[4-9])(\.\d+)?\b",
                    lambda m: f"{section_no}.{int(m.group(1)) - 93}{m.group(2) or ''}",
                    text,
                )

            raw = [map_block_text(dict(block), renumber) for block in raw]

            def normalize(block: dict[str, Any]) -> dict[str, Any]:
                if isinstance(block.get("text"), str):
                    block["text"] = block["text"].replace("Skeleton Code — ", "")
                return block

            raw = [normalize(dict(block)) for block in raw]
            title = f"{section_no}. Skeleton Code (Batch Job {job_no})" if job_no else f"{section_no}. Skeleton Code"
            return level_skeleton_blocks([h(1, title)] + raw)
        if topic.track == "BE":
            raw = be_skeleton_blocks(topic, {
                "sql_by_path": api_sql_map(),
                "skeleton_section": str(section_no),
                "sql_section": str(section_no + 1),
            })
            numbers = {str(section_no), str(section_no + 1)}
            # เอกสาร BE มี 2 section ในชุดเดียว (Skeleton Code + Database SQL) — จัดระดับทีละ section
            out: list[dict[str, Any]] = []
            group: list[dict[str, Any]] = []
            for block in raw:
                promoted = promote_skeleton_heading(dict(block), numbers)
                if promoted.get("type") == "h1" and group:
                    out.extend(level_skeleton_blocks(group))
                    group = []
                group.append(promoted)
            out.extend(level_skeleton_blocks(group))
            return out
        if topic.track == "FE":
            raw = fe_skeleton_blocks(topic, {"section_prefix": str(section_no), "heading_level": 1})
            blocks = [dict(block) for block in raw]
            for block in blocks:
                if block.get("type") == "h1":
                    block["text"] = re.sub(r"^(\d+)\s+", r"\1. ", str(block.get("text", "")))
                    break
            return level_skeleton_blocks(blocks)
    except Exception as error:  # generator ต้องไม่ล้มทั้งชุดเพราะ skeleton ฉบับเดียว
        return [
            h(1, f"{section_no}. Skeleton Code"),
            p(f"ไม่สามารถสร้าง skeleton code อัตโนมัติสำหรับเอกสารนี้ได้ ({type(error).__name__}: {error})"),
        ]
    return []


def count_top_sections(blocks: list[dict[str, Any]]) -> int:
    return sum(1 for block in blocks if block.get("type") == "h1")


# ---------------------------------------------------------------------------
# ชั่วโมง Unit Test (เพิ่ม 2026-08-18 ตามข้อกำหนด: LLDD ต้องประเมิน unit test ของงานนั้นด้วย)
# ---------------------------------------------------------------------------
# อัตราคิดจากลักษณะงาน ไม่ใช่ตัวเลขลอย:
#   BE / Job  30%  — business rule + SQL + transaction/rollback ต้องมี test คลุม
#                    (jest + repository mock; job ต้องมี fixture ของไฟล์ interface)
#   FE        25%  — component/hook test ด้วย React Testing Library + mock API layer
#   เอกสารสัญญา/ออกแบบ  0%  — ไม่มีโค้ดของตัวเอง หรือเป็นเอกสารที่กำกับการทดสอบอยู่แล้ว
NO_UNIT_TEST_DOCS = {
    "BE/LLDD-BE-API-Common-Contracts",      # สัญญากลาง — ทดสอบผ่าน endpoint ที่ใช้สัญญานี้
    "BE/LLDD-BE-Database-Structure",        # DDL/index — ตรวจด้วย migration verification ไม่ใช่ unit test
    "BE/LLDD-BE-Data-Migration-Cutover",    # reconcile script — มีเกณฑ์ตรวจรับของตัวเอง
    "BE/LLDD-BE-Workflow-Engine-Definition",# config ของ engine ระบบเดิม — ไม่ได้เขียนโค้ดเอง
    "BE/LLDD-BE-Integration-SBP-Platform",  # สัญญาต่อระบบเดิม — ทดสอบผ่าน integration ของเส้นที่ใช้
    "FE/LLDD-FE-Integration-Contracts",     # สัญญากลางฝั่ง FE
    "FE/LLDD-FE-Testing-Delivery",          # เอกสารกำกับการทดสอบเอง
}


def unit_test_hours(topic: "Topic") -> int:
    """ชั่วโมงเขียน unit test ของเอกสารนั้น (ปัดขึ้นเป็นจำนวนเต็มชั่วโมง)"""
    if topic.file in NO_UNIT_TEST_DOCS:
        return 0
    ratio = 0.25 if topic.track == "FE" else 0.30
    return math.ceil(topic.hours * ratio)


def total_hours(topic: "Topic") -> int:
    return topic.hours + unit_test_hours(topic)



def estimate_cell(topic: "Topic") -> str:
    ut = unit_test_hours(topic)
    if not ut:
        return f"{topic.hours} ชั่วโมง (ไม่มี unit test แยก — ดูเหตุผลใน NO_UNIT_TEST_DOCS)"
    return (f"**{total_hours(topic)} ชั่วโมง** = implementation {topic.hours} + "
            f"unit test {ut} ({int((0.25 if topic.track == 'FE' else 0.30) * 100)}%)")


def unit_test_scope_blocks(topic: "Topic", section_no: int) -> list[dict[str, Any]]:
    """ขอบเขต unit test ของเอกสารนั้น — ผูกกับชั่วโมงที่ประเมินไว้ใน Overview

    รายการทดสอบ derive จากข้อมูลของเอกสารเอง (field/validation · acceptance ·
    endpoint · ตารางที่เขียน) ไม่ใช่ checklist สำเร็จรูป จึงต่างกันจริงทุกฉบับ
    ต่างจาก "Developer Test Checklist" ที่เป็น scenario ระดับ end-to-end/manual
    """
    ut = unit_test_hours(topic)
    if not ut:
        return []
    is_fe = topic.track == "FE"
    is_job = topic.file.startswith("Jobs/")

    rows: list[list[str]] = []

    # 1) validation ของแต่ละ field ที่มี "กฎ" จริง
    #    ตาราง field ของเอกสาร Job ใช้คอลัมน์นี้เป็นธง แก้ไขได้/แก้ไม่ได้ ไม่ใช่กฎ validation
    #    จึงต้องคัดออก ไม่งั้นจะได้เคสไร้สาระแบบ "ผ่านเมื่อถูกกฎ — กฎ: แก้ไขได้"
    EDITABILITY = {"แก้ไขได้", "ค่าคงที่/แก้ผ่านหน้าจอไม่ได้", "-", "response only",
                   "optional", "read-only", "response only"}
    RULE_HINT = ("กฎ", "เงื่อนไข", "เกณฑ์", "rule", "format", "pattern")
    import re as _re
    # ค่าที่ไม่ใช่กฎ: ตำแหน่งคอลัมน์ (column 3) · ธงไม่บังคับล้วน (optional …) ที่ไม่มีเงื่อนไขต่อท้าย
    NOT_A_RULE = _re.compile(r"^(column\s*\d+|row\s*key|display\s*only|optional(\s+\w+){0,3})$", _re.I)
    for name, fmt, validation, behavior in topic.fields:
        v = (validation or "").strip()
        if NOT_A_RULE.match(v):
            continue
        if v in EDITABILITY or "แก้ผ่านหน้าจอไม่ได้" in v or not v:
            # ไม่มีกฎ validation — แต่ถ้าชื่อ field บอกว่าเป็นกฎ/เงื่อนไข ให้ทดสอบตัวกฎจาก format แทน
            if any(k in name.lower() or k in name for k in RULE_HINT) and fmt:
                rows.append([f"`{name}`", "rule", f"ใช้กฎกับข้อมูลตัวอย่างแล้วได้ผลตามที่ระบุ — {fmt}"])
            continue
        rows.append([
            f"`{name}`",
            "validation",
            f"ผ่านเมื่อถูกกฎ / โยน error เมื่อผิด — กฎ: {v}" + (f" · รูปแบบ: {fmt}" if fmt else ""),
        ])

    # 2) กฎธุรกิจจาก Acceptance Criteria
    for rule in topic.acceptance:
        rows.append(["business rule", "logic", rule])

    # 3) endpoint: success + error envelope
    for spec in topic.apis:
        if is_fe:
            rows.append([
                f"`{spec.method} {spec.path}`",
                "api client",
                "hook/service เรียกเส้นนี้ด้วยพารามิเตอร์ถูกต้อง · map {success:true,data} เป็น state ที่หน้าจอใช้ "
                "· เจอ {success:false,error} แล้วแสดงข้อความไทย verbatim (mock ด้วย msw)",
            ])
        else:
            rows.append([
                f"`{spec.method} {spec.path}`",
                "handler",
                "คืน {success:true,data} ตามรูปแบบที่ระบุ และคืน {success:false,error:{code,message}} "
                "เมื่อ input ผิด — mock repository/lib ไม่แตะ DB จริง",
            ])

    # 4) เฉพาะฝั่งที่เขียนข้อมูล: transaction / rollback
    writes = [r[0] for r in topic.db_tables if str(r[1]).upper().startswith(("W", "R/W"))]
    if writes:
        rows.append([
            ", ".join(f"`{w}`" for w in writes[:3]),
            "transaction",
            "จำลอง error กลางทาง แล้วยืนยันว่า rollback ครบ ไม่เหลือแถวค้าง (mock DataSource/QueryRunner)",
        ])

    # 5) รายการเฉพาะ track
    if is_job:
        rows.append(["runner", "idempotency", "รันซ้ำด้วย fixture เดิมต้องไม่เกิดแถวซ้ำ (ON CONFLICT / business unique key ทำงาน)"])
        rows.append(["runner", "lock", "เรียกซ้อนขณะกำลังรัน ต้องถูกปฏิเสธด้วย advisory lock"])
    elif is_fe:
        rows.append(["component", "render", "render ด้วย React Testing Library แล้วเห็น element ตาม field/action contract ของเอกสารนี้"])
        rows.append(["hook/state", "interaction", "ยิง action แล้ว state เปลี่ยนตามที่ระบุ และเรียก API layer ที่ mock ไว้ด้วยพารามิเตอร์ถูกต้อง"])
        rows.append(["error path", "ui", "API ตอบ error envelope แล้วหน้าจอต้องแสดงข้อความไทย verbatim ไม่ crash"])
    else:
        rows.append(["service", "error mapping", "แปลง error ของ repository/lib เป็น error code ตามสัญญากลาง (LLDD-BE-API-Common-Contracts)"])

    ratio = 25 if is_fe else 30
    tool = ("Jest + React Testing Library + msw (mock API layer)" if is_fe
            else "Jest + mock repository/DataSource (ไม่ต่อ DB จริง)")

    return [
        h(1, f"{section_no}. Unit Test Scope"),
        p(f"**{ut} ชั่วโมง** ({ratio}% ของ implementation {topic.hours} ชั่วโมง) · เครื่องมือ: {tool}"),
        p("หัวข้อนี้คือ **unit test** ที่ต้องเขียนคู่กับโค้ด — ต่างจาก *Developer Test Checklist* "
          "ซึ่งเป็น scenario ระดับ end-to-end/manual ที่ใช้ตอนตรวจรับ · "
          "รายการด้านล่าง derive จาก field/validation, acceptance criteria, endpoint และตารางที่เอกสารนี้เขียน"),
        table(["สิ่งที่ทดสอบ", "ประเภท", "เกณฑ์ผ่าน"], rows),
        bullets([
            "ทุกเคสต้องรันได้โดยไม่ต่อ DB/บริการภายนอกจริง — mock ที่ขอบ repository/client เสมอ",
            "ข้อความไทยที่ยืนยันในเทสต้องเป็น verbatim ตาม SRS ห้ามพิมพ์ใหม่",
            "เกณฑ์ผ่านของ CI: ทุกเคสในตารางนี้มี test จริงและผ่านทั้งหมด",
        ]),
    ]


# DOCX: ภาษาไทยเป็น "complex script" ใน Word — ถ้าไม่ตั้ง w:cs Word จะใช้ฟอนต์ default
# ของ theme ซึ่งมักไม่มี glyph ไทย แล้วแสดงเป็น ■■■ · Arial เองก็ไม่มีอักษรไทย
# Tahoma มีทั้งบน Windows และ macOS และครอบคลุมไทย จึงใช้เป็นฟอนต์ complex script
DOCX_THAI_FONT = "Tahoma"


def set_run_fonts(run: Any, latin: str = "Arial") -> None:
    """ตั้งฟอนต์ให้ครบทั้ง latin / eastAsia / complex-script (ไทย)"""
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), latin)
    rfonts.set(qn("w:cs"), DOCX_THAI_FONT)


def set_style_fonts(style: Any, latin: str = "Arial") -> None:
    style.font.name = latin
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), latin)
    rfonts.set(qn("w:cs"), DOCX_THAI_FONT)


def target_repo_row(topic: "Topic") -> list[str]:
    """repo ปลายทางของโค้ดตามเอกสารฉบับนั้น — ทุกฉบับต้องบอกให้ชัดว่าโค้ดไปวางที่ไหน

    FE  -> SBP/srm-sps-spsap-web-frontend (sbp-portal · Next.js · portal target sbpm)
    BE  -> SBP/srm-sps-spsap-store-backend (NestJS + TypeORM · schema sps_store)
           + SBP/srm-sps-spsap-sbp-bff (proxy/forward · ไม่มี DB) สำหรับเส้นที่ FE เรียก
    Job -> SBP/srm-sps-spsap-sop-sgi-batch (batch runner เดิมของ SBP บน AWS Batch · มติ 2026-09-02)
    """
    if topic.track == "FE":
        return ["Target repository", "`SBP/srm-sps-spsap-web-frontend` (sbp-portal · Next.js · `NEXT_PUBLIC_APP_TARGET=sbpm`) — "
                "เรียก API ผ่าน `SBP/srm-sps-spsap-sbp-bff` เท่านั้น ห้ามยิง store-backend ตรง"]
    if topic.file.startswith("Jobs/"):
        return ["Target repository", "**`SBP/srm-sps-spsap-sop-sgi-batch`** (NestJS 11 + TypeORM · schema `sps_store` · **มติ 2026-09-02 — ย้ายมาจาก store-backend**) — "
                "batch runner ของ SBP ที่รันอยู่แล้ว 42 job บน **AWS Batch** · ลงทะเบียน job ใน `src/main.ts` แล้วรับ argument ผ่าน `JOB_NAME`/`INPUT` (local) หรือ `argv[3]`/`argv[2]` (AWS Batch) · "
                "**ไม่ผ่าน BFF และไม่เปิด HTTP** · ตารางเวลาเป็น AWS Batch scheduled event ไม่ใช่ `@Cron` · ดู `SBP/srm-sps-spsap-sop-sgi-batch.md`"]
    return ["Target repository", "`SBP/srm-sps-spsap-store-backend` (NestJS + TypeORM · schema `sps_store`) "
            "+ `SBP/srm-sps-spsap-sbp-bff` (forward ผ่าน client service · ไม่มี DB) สำหรับเส้นที่ FE เรียก"]


def topic_blocks(topic: Topic) -> list[dict[str, Any]]:
    if topic.file == "FE/LLDD-FE-Testing-Delivery":
        return testing_delivery_blocks(topic)
    is_batch_monitor = is_batch_monitor_doc(topic.file)
    blocks: list[dict[str, Any]] = [
        h(1, "1. Overview"),
        table(["รายการ", "รายละเอียด"], [
            ["Track", topic.track],
            ["Estimate", estimate_cell(topic)],
            ["Owner", topic.owner],
            target_repo_row(topic),
            ["Objective", topic.objective],
        ]),
        h(1, "2. Screen / Functional Scope"),
        bullets(topic.scope),
    ]
    # 1.1 แทรกท้ายหัวข้อ 1 (ก่อน "2. Screen / Functional Scope") — เลขหัวข้อระดับบนไม่ขยับ
    rel = related_documents_blocks(topic)
    if rel:
        blocks[2:2] = rel
    if not is_batch_monitor:
        blocks.insert(2, p("Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint"))
    # หัวข้อ 3 ต้องปรากฏทุกฉบับ ไม่งั้นเลขหัวข้อกระโดด 2 → 4 (ผู้ตรวจรับจะถามหา)
    blocks.append(h(1, "3. Screenshot Reference"))
    if topic.screenshots:
        for shot in topic.screenshots:
            blocks.append(image(str(image_path(shot).relative_to(ROOT)), f"Screenshot: {shot}"))
    else:
        blocks.append(p("ไม่มีภาพหน้าจอสำหรับหัวข้อนี้ — เป็นเอกสารฝั่ง Backend/Batch ที่ไม่มี UI "
                        "(ภาพหน้าจอทั้งหมดอยู่ในเอกสารชุด FE)"))
    if topic.flow_diagram and not is_batch_monitor:
        draw_flow_diagram(topic.title, topic.flow, topic.flow_diagram)
        seq_rel = topic.flow_diagram.replace(".png", "-sequence.png")
        seq_lanes, seq_msgs = sequence_spec(topic)
        draw_sequence_diagram(f"Sequence — {topic.title}", seq_lanes, seq_msgs, seq_rel)
        blocks.extend([
            h(1, "4. Implementation Flow & Sequence Diagram (Reference)"),
            h(2, "4.1 Implementation Flow (ลำดับขั้นการทำงาน)"),
            image(topic.flow_diagram, f"Implementation flow reference: {topic.title}"),
            h(2, "4.2 Sequence Diagram (ใครคุยกับใคร ลำดับไหน)"),
            p("ผู้แสดงและลำดับข้อความในภาพนี้สร้างจาก endpoint ในหัวข้อ 7 และตารางในหัวข้อ Reference DB Mapping "
              "ของเอกสารฉบับนี้เอง จึงตรงกับสัญญาเสมอ"),
            image(seq_rel, f"Sequence diagram: {topic.title}"),
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
    if not topic.apis:
        blocks.append(p(
            "**เอกสารฉบับนี้ไม่มี endpoint ของตัวเอง** — เป็นสัญญา/งานภายในที่เอกสารอื่นเรียกใช้ "
            "(ดูขอบเขตใน 5.90 Endpoint Implementation Contract) · "
            f"รายการ endpoint ทั้ง {sgi_endpoint_count()} เส้นของ SGI อยู่ที่ **LLDD-API** และ `api.md`"
        ))
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
        next_no = 7
        skeleton = skeleton_code_blocks(topic, next_no)
        blocks.extend(skeleton)
        next_no += count_top_sections(skeleton)
        blocks.extend([
            h(1, f"{next_no}. Tab Interaction Flow"),
            table(["Step", "Description"], [[i + 1, s] for i, s in enumerate(topic.flow)]),
            h(1, f"{next_no + 1}. Acceptance Criteria"),
            bullets(topic.acceptance),
            h(1, f"{next_no + 2}. Developer Test Checklist"),
            table(["No", "Test"], [[i + 1, t] for i, t in enumerate(topic.tests)]),
        ])
        blocks.extend(unit_test_scope_blocks(topic, next_no + 3))
        return blocks
    next_no = 8
    if topic.db_tables:
        blocks.extend([
            h(1, f"{next_no}. Reference DB Mapping (No Database Page Work)"),
            p("ส่วนนี้เป็นข้อมูลอ้างอิงสำหรับการ implement API/Job เท่านั้น ไม่ใช่งานสร้างหน้า Database, ไม่ใช่งานออกแบบ DB page และไม่ถูกนับเป็น deliverable แยกของ FE/BE"),
            table(["Table / Object", "R/W", "Usage"], topic.db_tables),
        ])
        next_no += 1
    skeleton = skeleton_code_blocks(topic, next_no)
    blocks.extend(skeleton)
    next_no += count_top_sections(skeleton)
    blocks.extend([
        h(1, f"{next_no}. Processing Flow"),
        table(["Step", "Description"], [[i + 1, s] for i, s in enumerate(topic.flow)]),
        h(1, f"{next_no + 1}. Acceptance Criteria"),
        bullets(topic.acceptance),
        h(1, f"{next_no + 2}. Developer Test Checklist"),
        table(["No", "Test"], [[i + 1, t] for i, t in enumerate(topic.tests)]),
    ])
    blocks.extend(unit_test_scope_blocks(topic, next_no + 3))
    return blocks


def common_doc_fields() -> list[tuple[str, str, str, str]]:
    return [
        ("docNo", "YYYY/xxxxx", "required when opening existing document", "ใช้ปี **ค.ศ.** และ running 5 หลัก (มติ 2026-08-06)"),
        ("storeCode", "string 5 digits", "numeric length = 5", "แสดง leading zero"),
        ("amount", "number, 2 decimals", ">= 0", "format `#,##0.00` บาท"),
        ("percent", "number, 2 decimals", "0-100", "ใช้ `%` และรวม allocation ต้องเท่ากับ 100 — **B5: เพิ่ม/ลบร้านที่กระทบเพิ่มเมื่อไร ต้องเกลี่ยใหม่ทั้งชุดแล้วคำนวณ `compensateAmount` ของทุกแถวใหม่ ไม่ใช่เฉพาะแถวที่เพิ่ม**"),
        ("sourceSystem", "enum", "ALLMAP / USER", "**B5** ที่มาของแถวร้านเปิดใหม่ — `ALLMAP` ระบบ default ให้อัตโนมัติ (Job 9) · `USER` เจ้าหน้าที่ SBP DSA คีย์เองจากเอกสารแจ้งของหน่วยงานส่งเสริม (ผัง To-Be · SDD สไลด์ 7) · ซ้ำ `(doc_no, new_store_code)` ให้คืน `409`"),
        ("date", "DD/MM/YYYY", "valid date", "payload เป็น ISO ค.ศ. · FE แสดง ค.ศ. เป็นค่าเริ่มต้น (DatePicker buddhistEra=false) แสดง พ.ศ. เฉพาะจุดที่เปิด flag"),
        ("attachment", "file", "<= 5 MB", f"รองรับ {ATTACHMENT_ALLOWED_EXTENSIONS}"),
    ]


def sgi_namespace_blocks() -> list[dict[str, Any]]:
    """5.80 — namespace + การจัดกลุ่ม path ของงานประกันรายได้ (มติ 2026-08-25)"""
    return [
        h(2, "5.80 Namespace + กลุ่ม path ของงานประกันรายได้ (มติ 2026-08-25)"),
        p(
            "SGI ไม่ได้แยก backend/พอร์ทัลใหม่ (มติ **DP-10** ให้อยู่ใน `srm-sps-spsap-store-backend` "
            "และโมดูลใน `srm-sps-spsap-web-frontend` เดิม) ทุกอย่างของงานประกันรายได้จึงอยู่ใต้ "
            "**ชื่อเดียวกันทั้ง 3 ชั้น** แล้วแตกเป็น **6 กลุ่มย่อยตามกลุ่มงาน** — ตรงกับ 6 กลุ่มใน `api.md` แบบ 1:1"
        ),
        table(["ชั้น", "รูปแบบ", "ตัวอย่าง"], [
            ["URL ของ API", "`/api/v1/sgi/<กลุ่ม>/<resource>`", "`/api/v1/sgi/document/{docNo}/actions`"],
            ["route ของหน้าจอ", "`/sgi/<กลุ่ม>/<หน้า>`", "`/sgi/document/waiting` · `/sgi/report/status-summary`"],
            ["โฟลเดอร์ไฟล์", "`**/sgi/*`", "`src/app/(main)/sgi/*` · `src/services/sgi/*` · `src/types/sgi/*`"],
        ]),
        h(3, "6 กลุ่มย่อยใต้ `sgi`"),
        table(["กลุ่ม", "prefix", "เส้น", "ครอบคลุมอะไร"], [
            ["งาน & เอกสารประกันรายได้", "`/sgi/document/*`", "11",
             "`/tasks` (กล่องงาน) · ค้นหา/สร้าง/แก้เอกสาร · `/{docNo}/actions` · `/timeline` · `/attachments` · `/sales`"],
            ["ข้อมูลอ้างอิง (Lookup)", "`/sgi/lookup/*`", "2",
             "`/document-statuses` · `/workflow-sections` — อ่านอย่างเดียว ไม่มีหน้าจอดูแล"],
            ["Master Data", "`/sgi/master/*`", "8",
             "`/factors` (CRUD 4) · `/competitors` (CRUD 4) — master ที่มีหน้าจอดูแลของตัวเอง"],
            ["รายงาน", "`/sgi/report/*`", "2", "`/status-summary` · `/status-summary/export`"],
            ["Workflow ภายใน", "`/sgi/workflow/*`", "3", "`/instances` · `/instances/{id}` · `/summary`"],
            ["Interface (tracking)", "`/sgi/interface/*`", "2", "`/tracking` · `/pending-ack` — **ตัด `/sta/ack` 2026-09-08** (ข้อ 2.13 · สเปก STA ไม่มี ACK แบบ HTTP)"],
        ]),
        p(
            f"**Batch job ไม่มีกลุ่ม path ของตัวเอง** — {job_list_label()} รันด้วย AWS Batch/CLI ไม่ได้เปิด endpoint "
            "(กลุ่ม Batch Job Admin 6 เส้นถูกตัดทิ้ง 2026-08-06) · หน้าต่างที่มองเห็นผลของ job คือ "
            "**`/sgi/interface/*`** (tracking + ACK ของ `sgi_interface_transactions`) กับ application log เท่านั้น"
            "\n\n**repo ปลายทางของ batch job ทุกตัวคือ `SBP/srm-sps-spsap-sop-sgi-batch`** — วิธีลงทะเบียน job, "
            "รูปแบบ `INPUT`, publisher ของ RabbitMQ, `S3Service` และ `integration_log` อ่านได้ที่ "
            "**`SBP/srm-sps-spsap-sop-sgi-batch.md`** · ห้ามออกแบบ batch ของ SGI โดยไม่อ่านไฟล์นั้นก่อน "
            "· ส่วน job ที่ถูก **สั่งจากข้อความ** (Job 5 · Job 11 · มติ 2026-09-08) ตัวรับข้อความคือ "
            "**`SBP/srm-sps-spsap-sop-sgi-batch`** — ดู `SBP/srm-sps-spsap-sop-sgi-batch.md` (job consume คิวเอง · มติ 2026-09-12)"
        ),
        h(3, "ทำไมต้องมี prefix (ไม่ใช่แค่ความสวยงาม)"),
        table(["ระบบเดิมมีอยู่แล้ว", "ของ SGI ถ้าไม่ใส่ prefix", "ผล"], [
            ["`/document` · `/statement/...`", "`/documents`", "ชนเชิงความหมาย อ่าน routing แล้วสับสน"],
            ["`/report` · `/performance-report` · `/statement/report/ej`", "`/reports/status-summary`", "ชนเชิงความหมาย"],
            ["**`/interface/sta/upload-cmadd`** · `/interface/add`", "~~`/interfaces/sta/ack`~~", "✅ **หมดความเสี่ยงแล้ว** — เส้นของเราถูกตัดเมื่อ 2026-09-08"],
            ["`/common` · `/master` · `/store`", "`/factors` `/competitors` `/document-statuses`", "ปนกับ master ของโมดูลอื่น"],
        ]),
        bullets([
            "ฝั่ง NestJS: **`SgiModule` เดียว** ผูก prefix ที่ระดับโมดูล "
            "(`RouterModule.register([{ path: 'sgi', module: SgiModule }])`) แล้วแตกเป็น 6 controller ตามกลุ่ม "
            "(`DocumentController` `LookupController` `MasterController` `ReportController` `WorkflowController` `InterfaceController`) — "
            "**ห้ามเติม `sgi/` ในแต่ละ `@Controller()`**",
            "ในกลุ่ม `document` ต้องประกาศ route คงที่ (`/tasks`) **ก่อน** route ที่มีพารามิเตอร์ (`/{docNo}`) "
            "และ `docNo` เป็น `YYYY/xxxxx` จึงต้อง `encodeURIComponent` ทุกครั้งที่ประกอบ URL",
            "เส้นที่ **ไม่ใช่ของ SGI ห้ามใส่ prefix และห้ามแตะ** — `GET /store/search` · `GET /store/all-regions` · "
            "`GET /common/common-code` · `GET /menus` · `GET /groups/current-user/permissions` · "
            "`POST /statement/upload-file-aws` · `GET /api/workflow/pending` เป็นของระบบ SBP เดิม",
            "BFF ส่งต่อทั้ง prefix (`/api/v1/sgi/*`) โดยไม่ตัดคำ · สิทธิ์เมนูผูกกับ URL ของ **หน้าจอ** (`/sgi/<กลุ่ม>/...`) ไม่ใช่ URL ของ API",
        ]),
    ]


def topic_extra_blocks(file_key: str) -> list[dict[str, Any]]:
    if file_key == "FE/LLDD-FE-Create-Document":
        return create_document_fs_iframe_blocks()
    if file_key == "FE/LLDD-FE-Master-Data":
        return master_config_screen_blocks()
    if file_key == "FE/LLDD-FE-Document-Detail":
        return document_detail_role_blocks()
    role_profile = document_detail_role_profile(file_key)
    if role_profile:
        return document_detail_single_role_blocks(role_profile)
    if file_key == "FE/LLDD-FE-Integration-Contracts":
        return sgi_namespace_blocks()
    if file_key == "BE/LLDD-BE-API-Common-Contracts":
        return sgi_namespace_blocks() + common_contract_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Create-Update":
        return document_create_update_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Workflow-Actions":
        return workflow_action_transition_blocks()
    if file_key == "BE/LLDD-BE-API-Document-Detail-Aggregate":
        return document_detail_aggregate_extra_blocks()
    if file_key == "BE/LLDD-BE-API-Attachment-Sales-Timeline":
        return attachment_storage_extra_blocks()
    if file_key == "BE/LLDD-BE-Database-Structure":
        return database_structure_extra_blocks()
    if file_key == "BE/LLDD-BE-Data-Migration-Cutover":
        return data_migration_extra_blocks()
    if file_key == "BE/LLDD-BE-Integration-SBP-Platform":
        return integration_sbp_platform_extra_blocks()
    if file_key == "BE/LLDD-BE-Workflow-Engine-Definition":
        return workflow_engine_definition_extra_blocks()
    if file_key == "Jobs/LLDD-BE-Job-8b-StartInternalWorkflow":
        return workflow_engine_unconfirmed_warning_blocks()
    return []


def workflow_engine_unconfirmed_warning_blocks() -> list[dict[str, Any]]:
    """คำเตือน F9 + F1/F2/F3 สำหรับ Job 8b — job เดียวที่เรียก workflow engine โดยตรง

    เอกสารฉบับนี้เคยระบุชื่อ function ตายตัว (ปนสองชุด) และอ้าง UNIQUE constraint
    ที่ไม่มีอยู่จริง โดยไม่มีคำเตือนเหมือนที่เอกสาร BE-API มี
    """
    return [
        h(1, "4a. จุดเข้า flow ตามประเภทเคส — Job 8b เป็นคนตัดสินว่าเปิด workflow ที่ state ไหน"),
        p("ผัง To-Be 12/02/2026 กำหนดว่า **เอกสารไม่ได้เริ่มที่ state 06 เสมอไป** · Job 8b ต้องอ่านข้อมูลรอบชดเชย (คอลัมน์ที่รับเข้าโครง 2026-08-21 · gap F8) แล้วเลือก state เริ่มต้นก่อนส่งให้ `POST /sgi/workflow/instances` (job ไม่เรียก lib เอง · มติ 2026-09-09)"),
        p("**การตัดสินมี 2 ชั้น (มติ 2026-09-02)** — ชั้นที่ 1 คือ *ประเภทเคส* ซึ่งมีแค่ 2 ทาง (① เปิดเรื่องใหม่ / ② ต่อเนื่อง) · ชั้นที่ 2 ตัดสินเฉพาะเคส ② ด้วยเงื่อนไขเดียวคือ `ยอดชดเชย > 0 OR ยอด 0 ติดกัน <= 3 เดือน`"),
        table(["ชั้นที่ 1 · ประเภทเคส", "ชั้นที่ 2 · ยอดชดเชย", "เงื่อนไขที่ Job 8b ต้องอ่าน", "เปิด workflow ที่ state", "ผู้รับผิดชอบขั้นแรก"], [
            ["① เปิดเรื่องใหม่", "- ไม่ต้องตัดสินต่อ", "sgi_fgi_impact_processes.last_compensate_seq_no = 1", "**06**", "group ฝ่าย SBP DSA (ปกติ)"],
            ["② ต่อเนื่อง (last_compensate_seq_no > 1 และ flag_action = 'Y')", "**ใช่** — ยอด > 0 หรือ ยอด 0 ติดกัน <= 3 เดือน", "COALESCE(adjust_amount, forecast_amount) > 0 หรือ = 0 ใน sgi_fgi_impact_compensations งวดที่ 1-3", "**08** (Auto Approve — ข้ามขั้น 06 · มติ 2026-09-01 เคสยอด 0 เดิม 01)", "**เจ้าหน้าที่ SBP DSA คนเดิม** — job ส่งรหัสผู้รับผิดชอบไปกับ request แล้ว BE เป็นผู้ผูกให้ engine"],
            ["② ต่อเนื่อง (ต่อ)", "**ไม่ใช่** — ยอด 0 ติดกัน > 3 เดือน (เดือนที่ 4)", "COALESCE(adjust_amount, forecast_amount) = 0 งวดที่ 4 ขึ้นไป", "**ไม่เปิด workflow** — ปิดเอกสารเป็นเสร็จสิ้น (หยุดชดเชยประกันรายได้)", "-"],
        ]),
        p("**ที่มาของค่าที่ใช้ตัดสิน** — ทุกค่าอยู่ในโซน A (FGI/FCS) ที่ batch เขียนไว้ก่อนเปิดเอกสาร ไม่ใช่ค่าที่ Job 8b คำนวณเอง"),
        table(["ค่าที่ใช้ในเงื่อนไข", "ระบบเดิม (Oracle FCS_FRN)", "ตาราง SGI", "คอลัมน์ · ชนิด", "เขียนโดย"], [
            ["`LAST_COMPENSATE_SEQ_NO`", "`FGI_IMPACT_STORE_ON_PROCESS.LAST_COMPENSATE_SEQ_NO`", "`sgi_fgi_impact_processes`", "`last_compensate_seq_no` · INTEGER", "Job 2 — `ImportJdbc` (`SEQ_NO + 1` เมื่อเป็นรอบต่อเนื่อง)"],
            ["`FLAG_ACTION`", "`FGI_IMPACT_STORE_ON_PROCESS.FLAG_ACTION` (โดเมน Y/W/N)", "`sgi_fgi_impact_processes`", "`flag_action` · CHAR(1)", "Job 2 เขียน `'Y'` · Job 6 ปิดรอบ `Y->N` / พัก `Y->W`"],
            ["`DATASOURCE`", "`FGI_IMPACT_STORE_ON_PROCESS.DATASOURCE` (ข้อมูลจริงมีแค่ ALM/STA)", "`sgi_fgi_impact_processes`", "`datasource` · VARCHAR(5)", "Job 2/3 = `ALM` · Job 5 = `STA` · **`PRO` เชิงรุก / `REA` เชิงรับ = คนคีย์** (รหัสใหม่ 2026-08-24)"],
            ["`forecast`", "`FGI_IMPACT_STORE_COMPENSATE.COMPENSATE_FORECAST`", "`sgi_fgi_impact_compensations`", "`forecast_amount` · NUMERIC(14,2)", "Job 5 — นำเข้ายอดจาก IAS/MIS"],
            ["`adjust`", "`FGI_IMPACT_STORE_COMPENSATE.COMPENSATE_ADJUST`", "`sgi_fgi_impact_compensations`", "`adjust_amount` · NUMERIC(14,2)", "เจ้าหน้าที่ SBP DSA ปรับยอดในเอกสาร"],
        ]),
        p("> ยอดที่ใช้จริงทุกที่คือ `COALESCE(adjust_amount, forecast_amount)` — ค่าที่คนปรับชนะค่าที่ระบบคำนวณเสมอ  \n"
          "> `datasource` ไม่ได้เปลี่ยน state เริ่มต้นของ workflow — มันบอกแค่ว่า **ใครคีย์ข้อมูล** (`ALM`/`STA` = ระบบส่งงานมาให้เลือก · `PRO`/`REA` = เจ้าของงานคีย์เอง · SDD GI สไลด์ 17 · 47 · 49)  \n"
          "> ⚠️ ทั้งสองตารางเป็น gap **F8/F1** ที่เพิ่งรับเข้าโครงเมื่อ 2026-08-21 — ต้อง migrate ครบก่อน Job 8b จึงทำงานตามผัง To-Be ได้"),
        code("""-- ตัดสินประเภทเคสก่อนเปิด workflow (Job 8b)
SELECT p.last_compensate_seq_no,
       p.flag_action,
       (SELECT COUNT(*) FROM sgi_fgi_impact_compensations c
         WHERE c.impact_process_id = p.id
           AND COALESCE(c.adjust_amount, c.forecast_amount) = 0
           AND c.compensate_seq = p.last_compensate_seq) AS zero_months
FROM sgi_fgi_impact_processes p
WHERE p.id = :impactProcessId;
-- มติ 2026-09-01 — เคสต่อเนื่องเข้า state 08 ทั้งยอด > 0 และยอด 0 (<= 3 เดือน) · ไม่มีป้ายกำกับบนหน้าจอ
-- zero_months >= 4            -> ไม่เปิด workflow · ปิดเอกสารเป็น 99 พร้อม result = หยุดชดเชยประกันรายได้
-- zero_months BETWEEN 1 AND 3 -> state 08 + approver = เจ้าหน้าที่คนเดิม (เดิมเข้า state 01)
-- seq_no > 1 AND flag_action='Y' AND ยอด > 0 -> state 08 + approver = เจ้าหน้าที่คนเดิม
-- นอกนั้น                      -> state 06 ตามปกติ""", "sql"),
        p("**ทุกเส้นทางอัตโนมัติต้องบันทึกลง `sgi_consideration_logs` ด้วยผู้ดำเนินการ `SYSTEM`** เพื่อไม่ให้ timeline ของเอกสารขาดช่วง · รายละเอียดกติกาเต็มดู `workflow.md` หัวข้อจุดเข้า flow ตามประเภทเคส"),
        h(1, "4b. ข้อกำหนดการต่อกับ workflow ที่ Job 8b ต้องทำตาม"),
        p(
            "🔴 **มติ 2026-09-09 — job ไม่เรียก `@srm/glb-workflow` เอง** · workflow lib ใช้กับ "
            "**flow K2 (เอกสาร/การอนุมัติ) เท่านั้น** · Job 8b จึงเรียก REST ของ BE ด้วย service token:\n"
            "`POST /api/v1/sgi/workflow/instances` body `{impactProcessId, sourceJobNo: '8b', requestId}` · "
            "ฝั่ง BE (`LLDD-BE-API-Workflow-Instances`) เป็น**ผู้เรียก engine ที่เดียวในระบบ** และเป็นผู้แปลง "
            "`impactProcessId` เป็น `referenceId = sgi_compensation_documents.id` ให้เอง"
        ),
        p(
            "**สิ่งที่ job ยังต้องรู้:** เกณฑ์ Gen Flow Gate (W/Y/N) และ **state เริ่มต้นที่ต้องการ** "
            "(`06` เปิดเรื่องใหม่ / `08` ต่อเนื่อง) เพราะเป็นกติกาธุรกิจของ job — ส่งไปกับ request "
            "แล้วให้ BE เป็นผู้แปลงเป็นการเรียก engine · "
            "**สิ่งที่ job ไม่ต้องรู้แล้ว:** ชื่อ function ของ lib · `versionId` · `referenceId` · ลำดับการเรียก engine ทั้งหมด"
        ),
        table(
            ["เรื่อง", "ข้อเท็จจริงที่ตรวจจากฐานจริง", "ผลต่อ Job 8b", "ข้อกำหนดที่ต้องทำตาม"],
            [
                [
                    "`referenceId` ที่ส่งเข้า workflow",
                    "ระบบเดิม (cooperation-request · inform-evaluate) ใช้ surrogate id ทุกจุด",
                    "ค่าที่ส่งเข้า initialize และคีย์ที่ใช้เช็คซ้ำเปลี่ยนตามข้อนี้",
                    "ส่ง `sgi_compensation_documents.id` (surrogate) เป็น string ทุกครั้ง — ห้ามส่ง `doc_no` (ยืนยัน 2026-08-17)",
                ],
                [
                    "`sps_store.workflow_transaction` ไม่มี PK/index",
                    "19,327 แถว · ไม่มีทั้ง PK และ index (`SBP/db-schema-sps_store.md`) ต่างจาก `sps_auth` ที่มี PK ปกติ",
                    "กันซ้ำด้วย DB constraint ไม่ได้ ต้องกันที่ application · query ตาม reference_id เป็น seq-scan",
                    "**ห้ามแก้ schema ของ library** — กันซ้ำระดับ application ก่อนเรียก initialize และประเมินต้นทุน query ที่อ้างตารางนี้ทุกครั้ง",
                ],
                [
                    "schema ของ engine",
                    "engine ตัวจริงมี **13 ตาราง** อยู่ใน schema **`sps_store`** — `sps_auth` มีชื่อตารางชุดเดียวกันแต่เป็นสำเนาของ auth-backend คนละเวอร์ชัน",
                    "ทุก SQL ในเอกสารนี้ต้อง prefix `sps_store.`",
                    "ทุก SQL ต้องเขียน `sps_store.` นำหน้าเสมอ ห้ามชี้ `sps_auth`",
                ],
            ],
        ),
    ]


# --------------------------------------------------------------------------------------
# เนื้อหาเฉพาะของเอกสาร BE ที่เพิ่มใหม่ 4 ฉบับ (2026-08-07)
#
# ข้อเท็จจริงเชิงตัวเลขทุกตัวในหัวข้อนี้มาจากการตรวจฐานข้อมูลจริง 2026-08-07 และบันทึกไว้ที่
# `SBP/db-schema-sps_store.md` · `SBP/db-schema-sps_auth.md` · `SBP/SBPGI-vs-existing-system.md`
# ส่วนนิยาม engine มาจาก `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md`
# ข้อกำหนด implement ทุกข้อในเอกสารชุดนี้อ้าง living docs (database.md / workflow.md / api.md)
# --------------------------------------------------------------------------------------
DECISION_DOC = "SBP/SBPGI-vs-existing-system.md หัวข้อ 4"


def implementation_rule_blocks(heading: str, rows: list[list[str]]) -> list[dict[str, Any]]:
    """ข้อกำหนดที่ต้องยึดตอน implement — ระบุสิ่งที่ต้องทำ ไม่ใช่ทางเลือกให้เลือก"""
    return [
        h(2, heading),
        p(
            "ตารางนี้คือ**ข้อกำหนดที่ต้องทำตาม** ไม่ใช่ทางเลือก — ทุกข้อสอดคล้องกับ "
            "`database.md` / `workflow.md` / `api.md` ซึ่งเป็นแหล่งความจริงของระบบ"
        ),
        table(["เรื่อง", "ข้อกำหนดที่ต้องทำตาม", "ที่มา / เหตุผล"], rows),
    ]


def database_structure_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 ขอบเขตตารางในโครง SGI (21 ตาราง — CREATE จริง 20 + reuse 1)"),
        p(
            "DDL เต็มอยู่ที่เอกสาร `LLDD-Database` หัวข้อ Executable DDL · เอกสารฉบับนี้เป็นเจ้าของ "
            "**สคริปต์ deploy จริง** และกติกาว่าอะไรสร้างได้/สร้างไม่ได้"
        ),
        p(
            "⚠️ **20 = จำนวนตารางในโครง ไม่ใช่จำนวนที่ต้อง CREATE** — `fcs_qssi_score` นับอยู่ในโครงโซน A "
            "แต่ใช้ตารางเดิมของ `sps_store` (24,284,545 แถว) จึง **ห้าม CREATE TABLE** ดูหัวข้อ 5.1.1 · "
            "จำนวนที่ต้อง CREATE จริงคือ **20 ตาราง** (21 ตารางในโครง ลบ fcs_qssi_score ที่ reuse) · "
            f"**DP-4 ✅ ปิดแล้ว 2026-08-24** — reuse ตารางเดิมแบบ **อ่านอย่างเดียว** ไม่มีการเขียนจากฝั่ง SGI จึงไม่ต้องแก้ constraint/index ของตารางเดิมและไม่ต้องขอ sign-off (`{DECISION_DOC}`)"
        ),
        table(
            ["โซน", "จำนวน", "ตาราง"],
            [
                ["A — FGI/FCS pipeline", "8 (CREATE 7 + reuse 1)", "sgi_fgi_impact_processes, **sgi_fgi_impact_compensations**, sgi_fgi_impact_stores, sgi_fgi_impact_sales_summaries, sgi_sales_transactions, sgi_fgi_impact_competitors, sgi_interface_transactions · **+ fcs_qssi_score = reuse ห้าม CREATE (ดู 5.1.1 · DP-4)**"],
                ["B — เอกสาร/ประวัติ", "9", "sgi_compensation_documents, sgi_document_new_stores, sgi_document_competitors, sgi_document_external_factors, sgi_consideration_logs, sgi_document_attachments, sgi_compensation_histories, sgi_document_cost_details, sgi_document_running_numbers"],
                ["C — master ที่ SGI เป็นเจ้าของ", "3", "sgi_impacted_stores, sgi_external_factors, sgi_competitors (decisions ย้ายไป common_code · DP-9 · status_email_rules ตัดตาม DP-5 — SGI เรียก email-lib เองโดยใช้เลข template จาก workflow_route.email_id)"],
                ["รวม", "**20 (CREATE 19 + reuse 1)**", "ตรงกับ `database.md` และผลรวมของโซน A 8 + B 9 + C 3 · ประวัติ: 34 → 24 (2026-08-06 reuse ของระบบเดิม) → 22 (ตัดกลุ่ม batch) → 21 (ยกเลิก `audit_logs` 2026-08-07) → **20 (มติ DP-9 2026-08-10 ย้าย `decisions` ไป `common_code`)** → คงที่หลังรับ F8+F1 เข้าโครง 2026-08-21 (เพิ่ม `sgi_fgi_impact_compensations` แทน `status_email_rules` ที่ตัดตาม DP-5)"],
            ],
        ),
        h(3, "5.1.1 ตารางที่ระบบ SBP เดิมมีอยู่แล้ว — ห้าม CREATE TABLE"),
        p(
            "ตรวจฐานข้อมูลจริง 2026-08-07 (`SBP/db-schema-sps_store.md`) ทุกตารางในตารางนี้อยู่ใน schema "
            "**`sps_store`** และมีข้อมูลจริงใช้งานอยู่ การสร้างซ้ำใน SGI = ข้อมูลสองชุดที่ไม่มีวันตรงกัน"
        ),
        p(
            "⚠️ **จำนวนแถวเป็นค่า ณ 2026-09-16** วัดสดจากฐาน dev ด้วย `tools/introspect_dev_sgi.py` · "
            "ฐานนี้ยังมีระบบเดิมใช้งานอยู่จริง ตัวเลขจึงเปลี่ยนทุกวัน — ใช้เพื่อดู**ขนาดของปัญหา** "
            "ไม่ใช่ตัวเลขที่ต้องตรงเป๊ะ · ตรวจว่ายังใกล้เคียงอยู่ไหมด้วย `tools/check_docs_vs_db.py`"
        ),
        table(
            ["ตาราง/กลุ่มตาราง", "schema", "จำนวนแถวจริง", "หมายเหตุ"],
            [
                ["workflow engine 13 ตาราง", "sps_store", "workflow_transaction 19,327 · workflow_history 38,136 · workflow_approver 96,542", "ดู LLDD-BE-Workflow-Engine-Definition"],
                ["fcs_qssi_score (เอกพจน์)", "sps_store", "24,284,545", "มี import pipeline ใช้งานอยู่ (POST /performance/import-qssi · staging fcs_tmp_qssi_score) — ห้ามสร้างใหม่"],
                ["mas_param", "sps_store", "93,763", "ค่ากำหนดกลาง"],
                ["common_code / common_code_type", "sps_store", "2,641 / 380", "วงเงินอนุมัติ code_type = SGI_APPROVE_LIMIT"],
                ["email_template / email_sent", "sps_store", "126 / 5,392", "เทมเพลตอีเมลและ log การส่ง"],
                ["business_user", "sps_store", "12,759", "ตัวตนผู้ใช้/ผู้อนุมัติ"],
                ["store / mas_store", "sps_store", "19,402 / 19,647", "master ร้าน"],
                ["fcs_monthly_sales", "sps_store", "711,384", "ยอดขาย**รายเดือน** (key store_id+year+month) — ใช้แทน sgi_sales_transactions รายวันไม่ได้ ย้อนกลับเป็นรายวันไม่ได้ · ใช้ cross-check ได้"],
            ],
        ),
        h(3, "5.1.2 แกนธุรกิจที่ยืนยันแล้วว่าต้องสร้างเอง"),
        p(
            "ค้นทั้งฐาน 276 ตาราง / 4,396 คอลัมน์ ด้วยคำ `impact` · `compensat` · `guarantee` · `income` · "
            "`competitor` · `growth` · `outlier` · `distance` · `radius` · `latitude` · `longitude` · `window_no` "
            "ได้ **0 hit ทุกคำ** → ตารางโซน A และแกนเอกสารโซน B ไม่มีของเดิมให้ reuse ต้องสร้างเองทั้งหมด"
        ),
        h(2, "5.2 ลำดับไฟล์ deploy"),
        table(
            ["ไฟล์", "เนื้อหา", "รันเมื่อไร"],
            [
                ["01_schema.sql", "CREATE TABLE 20 ตาราง เรียงตาม dependency (C master -> A pipeline -> B document) — ไม่รวม fcs_qssi_score ที่ reuse ของเดิม", "ครั้งเดียวต่อ environment"],
                ["02_index.sql", "index, unique/partial index, check constraint", "หลัง 01 · rerun ได้เมื่อเพิ่ม index"],
                ["03_seed.sql", "sgi_external_factors, sgi_competitors (01-11) — ไม่มี decisions แล้ว (DP-9 ย้ายไป common_code · seed ที่ระบบเดิม)", "หลัง 02"],
                ["04_grant.sql", "GRANT ให้ role ของ application (แยก read/write)", "หลัง 03"],
                ["99_rollback.sql", "DROP TABLE ย้อนลำดับ เฉพาะตารางของ SGI", "เฉพาะกรณี rollback"],
            ],
        ),
        code(
            """-- 01_schema.sql (ตัวอย่างส่วนหัว — DDL เต็มอยู่ที่ LLDD-Database)
-- ห้ามมี CREATE TABLE ของตาราง reuse: ตรวจด้วยคำสั่งนี้ก่อน commit
--   grep -nE 'CREATE TABLE (workflow_|fcs_qssi_score|mas_param|common_code|business_user|store|mas_store|email_template|decisions)' 01_schema.sql
BEGIN;
SET search_path TO sps_store;

-- โซน C: master ที่ SGI เป็นเจ้าของ (ต้องมาก่อนเพราะโซน A/B อ้างถึง)
-- ❌ ไม่มี CREATE TABLE decisions — มติ DP-9 (2026-08-10) ย้ายไป common_code ของระบบเดิม
--    (code_type = 'SGI_DECISION') · FE อ่านผ่าน GET /common/common-code?codeType=SGI_DECISION
CREATE TABLE sgi_external_factors (...);
CREATE TABLE sgi_competitors (...);
CREATE TABLE sgi_impacted_stores (...);
-- ❌ ไม่สร้างตาราง status_email_rules ใน SGI (ปิด DP-5 · แก้มติ 2026-08-14)
--    workflow ให้ 'เลข template' ผ่าน workflow_route.email_id → SGI เรียก sendEmail() ของ email-lib เอง
--    ผู้รับ resolve จาก workflow_approver → business_user.email · ⚠️ คอลัมน์จริงคือ email_sent.send_by ไม่ใช่ sent_by
--    SGI อ่าน workflow_route.email_id แล้วเรียก sendEmail() ของ email-lib · template อยู่ที่ email_template ของระบบ SBP เดิม (85 แถว)
--    lib เขียน log ให้เองที่ email_sent (5,392 แถว · mail_to/mail_cc/is_sent/error · ⚠️ คอลัมน์ผู้ส่งคือ send_by)


-- โซน A: pipeline
CREATE TABLE sgi_fgi_impact_processes (...);
-- ...

-- โซน B: เอกสาร
CREATE TABLE sgi_compensation_documents (...);
-- ...
COMMIT;""",
            "sql",
        ),
        h(2, "5.3 Seed ที่ต้องมีตั้งแต่วันแรก"),
        table(
            ["ตาราง", "ข้อมูล seed", "ที่มา"],
            [
                ["(ไม่สร้าง) decisions", "ย้ายไป common_code ของระบบเดิม (code_type = SGI_DECISION) — มติ DP-9 2026-08-10", "MSSQL DecisionProfile"],
                ["sgi_competitors", "แบรนด์คู่แข่ง 11 รายการ รหัส 01-11 (ไทย+อังกฤษ)", "หน้าจอ K2 เดิม (k2-competitors.html)"],
                ["sgi_external_factors", "ปัจจัยภายนอกที่ใช้อยู่", "MSSQL FactorProfile"],
                
                ["common_code (ระบบเดิม)", "SGI_APPROVE_LIMIT: code_value=100000 · code_name=100000 (เกณฑ์เดียว)", "มติประชุม 2026-08-18 — เขียนที่ common_code ของระบบเดิม ไม่ใช่ตารางของ SGI"],
                ["common_code (ระบบเดิม)", "SGI_DATASOURCE: ALM=ระบบ (ALLMAP) · STA=ระบบ (Statement) · PRO=เชิงรุก · REA=เชิงรับ", "SDD GI สไลด์ 17 — 3 แหล่งข้อมูลร้านที่ต้องชดเชย · รหัส PRO/REA ตั้งใหม่ 2026-08-24 ตามแพตเทิร์น 3 ตัวอักษรของ DATASOURCE เดิม (ข้อมูลจริงมีแค่ ALM/STA) เพราะ SDD และระบบเดิมไม่ได้กำหนดไว้"],
            ],
        ),
        *implementation_rule_blocks(
            "5.4 ข้อกำหนดด้านโครงสร้างข้อมูลที่ต้องยึด",
            [
                ["ร้าน SP ที่ใช้อ้างในเอกสาร", "เก็บเป็น **snapshot เฉพาะร้านที่เคยเข้ารอบชดเชย** ใน `sgi_impacted_stores` — เติมตอนสร้าง `sgi_fgi_impact_processes` ห้ามอ่านผ่าน view ของระบบเดิม", "ร้านที่ยกเลิกเกิน 1 เดือนหายจาก view ของระบบเดิม ทำให้เอกสารย้อนหลังอ่านไม่ได้ (ตัดสิน 2026-08-10)"],
                ["`fcs_qssi_score`", "**ห้าม CREATE TABLE** — reuse ตารางเดิมของ `sps_store` (24,284,545 แถว) แบบอ่านอย่างเดียว", "ระบบ SBP เดิมนำเข้าให้แล้วผ่าน `POST /performance/import-qssi` (ปิด 2026-08-24 · ตัด Job 1 ออก)"],
                ["ผลพิจารณา / ปัจจัย / คู่แข่ง", "`decisions` ใช้ `common_code` ของระบบเดิม (`code_type = SGI_DECISION`) · `sgi_external_factors` และ `sgi_competitors` **เป็นตารางของ SGI**", "สองตารางหลังมีหน้าจอ CRUD ของตัวเอง และ remark ของ `common_code` จำกัด 50 ตัวอักษร (ตัดสิน 2026-08-10)"],
                ["`reference_id` ที่ส่งเข้า workflow engine", "ส่ง **`sgi_compensation_documents.id`** (surrogate) เป็น string — ห้ามส่ง `doc_no`", "`reference_id` ของ engine เป็น varchar(255) และระบบเดิม (cooperation-request / inform-evaluate) ส่ง surrogate id ทุกจุด (ปิด 2026-08-17)"],
                ["ประวัติการพิจารณา", "ใช้ **`sgi_consideration_logs` ของ SGI เอง** ผูก `transaction_id` ของ engine — ไม่ต่อยอดบน `sps_store.workflow_history`", "engine เก็บ timeline แต่ไม่มีรหัสผลพิจารณาและไฟล์แนบ (ปิด 2026-08-24)"],
                ["audit การแก้ master data", "โครง SGI **ไม่มีตาราง audit ของตัวเอง** — การตรวจสอบการแก้ master ใช้กลไกของระบบ SBP เดิม", "`audit_logs` ถูกตัดออกจากโครงเมื่อ 2026-08-07 · DDL ปัจจุบันไม่มีตารางนี้"],
            ],
        ),
    ]


def data_migration_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Source-to-Target Mapping ระดับตาราง"),
        table(
            ["ต้นทาง", "ระบบ", "ปลายทาง (SGI)", "กฎแปลงที่ต้องระวัง"],
            [
                ["FGI_IMPACT_STORE_ON_PROCESS", "ORA FCS_FRN", "sgi_fgi_impact_processes", "PK IMPACT_PROCESS_ID (seq SEQ_FGI_IMPACT_PROCESS) เป็น hub ของทั้งโซน A · **ต้อง migrate คอลัมน์รอบชดเชยด้วย (gap F8 · รับเข้าโครง 2026-08-21)**: `LAST_COMPENSATE_SEQ/_SEQ_NO -> last_compensate_seq/_seq_no` · `START/END_COMPENSATE_MONTH-YEAR -> start/end_compensate_month/year` · `FLAG_ACTION -> flag_action` · `DATASOURCE -> datasource` · ⚠️ `FLAG_ACTION` โดเมนจริงคือ **Y/W/N** (active = `IN ('Y','W')`) ไม่ใช่ Y/N — Job 6 เขียน `Y->W` ตอนพัก/รอจ่าย ถ้า CHECK ปลายทางรับแค่ Y/N แถวกลุ่มนี้จะ migrate ไม่ผ่าน · ทั้ง 4 กลุ่มนี้คือค่าที่ Job 8b ใช้ตัดสินจุดเข้า flow"],
                ["FGI_IMPACT_STORE", "ORA FCS_FRN", "sgi_fgi_impact_stores + sgi_impacted_stores", "แถวฝั่ง `_I` ทำ distinct เข้า sgi_impacted_stores · ที่เหลือเป็นคู่ร้าน · **คอลัมน์ที่รับเข้าโครง 2026-09-02**: `FLAG_VERIFY -> verify_status` (W/P/N ตรงตัว) · `CREATE_BY -> created_by` / `UPDATE_BY -> updated_by` (โดเมน `ALM`/`STA`/`USER` — ค่าอื่นในข้อมูลเดิมต้อง map เป็น `USER` และรายงานจำนวน) · `CREATE_DATE -> created_at` (กฎ \"ตัดทิ้งเมื่อเก่ากว่า 12 เดือน\" ของ Job 2 อ้างคอลัมน์นี้ — ห้ามใส่ค่า sysdate ตอน migrate ไม่งั้นแถวเก่าจะไม่ถูกตัดทิ้ง)"],
                ["FGI_IMPACT_STORE_COMPENSATE", "ORA FCS_FRN", "**sgi_fgi_impact_compensations** (รับเข้าโครง 2026-08-21 · gap F1)", "`COMPENSATE_FORECAST -> forecast_amount` · `COMPENSATE_ADJUST -> adjust_amount` · `COMPENSATE_SEQ/_SEQ_NO -> compensate_seq/_seq_no` · UK (impact_process_id, compensate_month) · ใช้นับยอด 0 ติดกันกี่งวดด้วย `COALESCE(adjust_amount, forecast_amount) = 0` — เป็น input ของ Job 8b ชั้นที่ 2 ของเคส ② ต่อเนื่อง"],
                ["FGI_IMPACT_STORE_INFO", "ORA FCS_FRN", "sgi_compensation_documents (+ `approver_snapshot` JSONB)", "**ตกหล่นจากตารางนี้จนถึง 2026-09-13** — ตรวจฐานจริงแล้วมี **429 แถว** · เก็บ snapshot ร้านที่ถูกกระทบ + ผู้อนุมัติ ณ เวลาเปิดเอกสาร · เอกสาร `batchjob/JOB-08` ระบุปลายทางไว้แล้วแต่ไม่เคยถูกยกมาที่แผน migration"],
                ["FGI_NEW_STORE_INFO", "ORA FCS_FRN", "sgi_document_new_stores", "**ตกหล่นจากตารางนี้จนถึง 2026-09-13** — ตรวจฐานจริงแล้วมี **492 แถว** · ร้านเปิดใหม่ที่ผูกกับเอกสาร (ดู `batchjob/JOB-09`)"],
                ["FGI_NEW_STORE_COMPENSATE", "ORA FCS_FRN", "sgi_document_new_stores (`%ชดเชย` ต่อร้านใหม่)", "**ตกหล่นจากตารางนี้จนถึง 2026-09-13** — ตรวจฐานจริงแล้วมี **473 แถว** · สัดส่วน %ชดเชยต่อร้านใหม่ ซึ่งกติกาบังคับว่ารวมกันต้องได้ 100% พอดี — **ต้อง reconcile หลัง load**"],
                ["FGI_WS_LOG", "ORA FCS_FRN", "— **ไม่ migrate** (ตัดทิ้งโดยตั้งใจ)", "⚠️ **ตรวจฐานจริง 2026-09-13 พบ 20,704 แถว และถูกใช้ในโค้ด Java เดิม 4 ไฟล์** — ไม่ใช่ \"ตารางที่เสนอไว้\" อย่างที่เคยเขียนไว้ · ระบบใหม่ใช้ `integration_log` ของ SBP เดิม ทำหน้าที่นี้แทน (log payload ราย call) ส่วน ACK ระดับแถวอยู่ที่ `sgi_interface_transactions` · **log เดิมไม่ถูกยกมา** — ถ้าต้องสืบย้อนต้องเปิดฐานเดิมอ่านเอง ต้องยืนยันว่ารับได้"],
                ["FGI_IMPACT_STORE_SALES", "ORA FCS_FRN", "sgi_fgi_impact_sales_summaries", "key STORECODE_I + MONTH + YEAR"],
                ["FGI_IMPACT_STORE_SALES_TRN", "ORA FCS_FRN", "sgi_sales_transactions", "4 หน้าต่าง × 15 วัน — ห้ามใช้ fcs_monthly_sales แทน (รายเดือน ย้อนกลับเป็นรายวันไม่ได้)"],
                ["FGI_IMPACT_COMPETITOR", "ORA FCS_FRN", "sgi_fgi_impact_competitors", "data_source = ALM"],
                ["FGI_CONFIRM_RECEIVE_DATA", "ORA FCS_FRN", "sgi_interface_transactions", "TRANSACTION_PK เป็น polymorphic — ต้องแตกตาม DATA_NAME เป็น typed FK"],
                ["FCS_QSSI_SCORE", "ORA FCS_FRN", "fcs_qssi_score (sps_store)", "ปลายทางมีข้อมูลอยู่แล้ว 24,284,545 แถว — **ไม่ต้อง migrate** เพราะ SGI อ่านอย่างเดียว ห้ามโหลดทับ"],
                ["CompensateFlow", "MSSQL CPA_FRN_FGI", "sgi_compensation_documents", "CompDocumentID -> doc_no · เก็บ round_no/loop_no/allmap_url/statement_id/approver_snapshot"],
                ["CompensateHistory", "MSSQL CPA_FRN_FGI", "sgi_consideration_logs", "PK ActionID · เติม result_category (APPROVE/REJECT/CANCELLED/PENDING)"],
                ["ImpactProfile", "MSSQL CPA_FRN_FGI", "sgi_document_new_stores", "ฝั่ง `_N` + %ชดเชย/ยอดต่อร้าน"],
                ["CompetInCompenProfile", "MSSQL CPA_FRN_FGI", "sgi_document_competitors", "คู่แข่งที่ผูกกับเอกสาร · **competitor_store_code = รหัสสาขาจาก ALLMAP (ไม่มี FK)** · **brand_code อ้าง master sgi_competitors (11 รหัส 01-11)** · แถวที่มาจาก ALLMAP ตั้ง data_source = ALM"],
                ["FactorInCompenProfile", "MSSQL CPA_FRN_FGI", "sgi_document_external_factors", "ปัจจัยภายนอกที่ผูกกับเอกสาร · factor_code อ้าง master sgi_external_factors + ช่วงวันที่มีผล"],
                ["FGI_IMPACT_STORE_COMPENSATE + CompensateFlow", "ORA + MSSQL", "sgi_compensation_histories", "ประวัติชดเชยต่อร้าน/รอบ · submit_account_month (งวดที่ Job 6 ส่งไป STA ผ่าน RabbitMQ) · migrate เป็นข้อมูลอ้างอิงของ SGI — ไม่เขียนกลับ `fr_store_insure` ของระบบเดิม"],
                ["ImpactCostDetail", "MSSQL CPA_FRN_FGI", "sgi_document_cost_details", "ยอดชดเชยแยกรายเดือน/รายร้านใหม่"],
                ["RunningNumber", "MSSQL CPA_FRN_FGI", "sgi_document_running_numbers", "ตั้ง last_running_no ต่อปีให้ตรงกับเลขสูงสุดที่ย้ายมา"],
                ["CompDocAttachment / CompTempAttachment / AttachFileProfile", "MSSQL CPA_FRN_FGI", "sgi_document_attachments", "metadata เท่านั้น · ไฟล์จริงต้องย้ายขึ้น S3 ของระบบเดิม"],
                ["FactorProfile / CompetitionProfile", "MSSQL CPA_FRN_FGI", "sgi_external_factors / sgi_competitors", "เป็น master ที่ SGI เป็นเจ้าของ · **DecisionProfile ไม่ย้ายมาแล้ว** — มติ DP-9 (2026-08-10) ให้ seed ลง common_code ของระบบเดิม (code_type = SGI_DECISION) ไม่สร้างตาราง decisions"],
            ],
        ),
        h(2, "5.2 กฎแปลงข้อมูลที่ผิดบ่อย"),
        table(
            ["เรื่อง", "อาการถ้าไม่ทำ", "กฎที่ต้องใช้"],
            [
                ["**ค่าที่ติด CHECK constraint**", f"**load ล้มทั้ง batch** — DDL มี `CHECK` {ddl_check_count()} จุด ถ้าข้อมูลเดิมมีค่านอกโดเมนแม้แถวเดียว INSERT จะถูกปฏิเสธ",
                 "**profile ค่าจริงของทุกคอลัมน์ที่มี CHECK ก่อน full load** (`SELECT DISTINCT col, COUNT(*) ... GROUP BY col`) แล้วเทียบกับโดเมนใน DDL · "
                 "จุดที่เสี่ยงที่สุด: `compensate_status` · `verify_status` จาก `FLAG_VERIFY` · `sales_request_status` — **ทั้งสามยืนยันจากข้อมูลจริงแล้ว ดูตารางแมปในข้อ 5.2.1** · "
                 "`created_by`/`updated_by` จาก `CREATE_BY`/`UPDATE_BY` (`ALM/STA/USER` — ค่าอื่นให้ map เป็น `USER` แล้วรายงานจำนวน) · `flag_action` (`Y/W/N`) · `data_name` (12 ค่า) · "
                 "**ห้ามแก้ด้วยการถอด CHECK ออก** — ให้แก้ค่าหรือขยายโดเมนอย่างตั้งใจพร้อมอัปเดต `database.md`"],
                ["leading zero ของรหัสร้าน", "ร้าน 00788 กลายเป็น 788 แล้ว join ไม่ติด", "lpad(store_code, 5, '0') ทุกจุด · ปลายทางเป็น VARCHAR(5)"],
                ["ปี พ.ศ./ค.ศ.", "วันที่เพี้ยน 543 ปี", "เก็บ ค.ศ. ใน DB และ `doc_no` เป็นปี **ค.ศ.** ด้วย (มติ 2026-08-06) · ถ้าของเดิมเป็น พ.ศ. ต้องแปลงตอน migrate ด้วย toAD()"],
                ["polymorphic key", "FK ชี้ผิดตาราง", "แตก TRANSACTION_PK ตาม DATA_NAME เป็น impact_process_id / sales_summary_id / doc_no"],
                ["เลขเอกสารซ้ำ", "ออกเลขใหม่ทับของเก่า", "หลังโหลด ตั้ง sgi_document_running_numbers.last_running_no = MAX(running) ต่อปี"],
                ["ยอดขายรายวัน", "ข้อมูล 60 วันไม่ครบ ทำให้ธงผิดปกติเพี้ยน", "ต้องมาจาก FGI_IMPACT_STORE_SALES_TRN เท่านั้น · fcs_monthly_sales (711,384 แถว) ใช้ cross-check ได้อย่างเดียว"],
            ],
        ),
        h(2, "5.2.1 ตารางแมปค่าสถานะตอน migrate (ยืนยันจากฐานเดิมจริง)"),
        p("ตัวเลขทั้งหมดมาจากการ profile ฐาน Oracle ของระบบเดิมเมื่อ **2026-09-12** "
          "(`tools/introspect_legacy_oracle.py` · ตาราง `FGI_IMPACT_STORE_BK_20250515` 26,264 แถว "
          "และ `FGI_IMPACT_STORE_SALES_BK_20250515` 8,730 แถว — ตาราง live ถูกรีเซ็ตเมื่อ 2025-05-15 "
          "จึงมีแค่ 728 แถว ใช้เป็นภาพแทนไม่ได้) · "
          "**แถวที่ยังไม่เคาะทำให้ load ล้มทั้ง batch** เพราะทั้งไฟล์อยู่ใน transaction เดียว"),
        table(
            ["ค่าเดิม", "จำนวนแถวจริง", "แมปเป็นอะไรในโครงใหม่", "สถานะ"],
            [
                ["`FGI_IMPACT_STORE.FLAG_VERIFY` = `N`", "14,424", "`verify_status = 'N'`", "✅ ตรงตัว"],
                ["`FGI_IMPACT_STORE.FLAG_VERIFY` = `Y`", "**8,556**",
                 "`verify_status = 'P'` **+** `sales_request_status = 'Y'` — ค่าเดียวของเดิมถือสองความหมาย "
                 "(ผ่านการตรวจคู่ร้าน **และ** ยอดขายผ่านแล้ว) โครงใหม่แยกเป็นสองคอลัมน์",
                 "🔴 **ต้องเคาะ** — แมปตรงตัวจะติด CHECK ทันที 8,556 แถว"],
                ["`FGI_IMPACT_STORE.FLAG_VERIFY` = `W`", "3,064", "`verify_status = 'W'`", "✅ ตรงตัว"],
                ["`FGI_IMPACT_STORE.FLAG_VERIFY` = `P`", "220", "`verify_status = 'P'`", "✅ ตรงตัว"],
                ["`FGI_IMPACT_STORE_SALES.FLAG_VERIFY` = `Y`", "6,029", "`sgi_fgi_impact_sales_summaries.sales_status = 'Y'`", "✅ ตรงตัว"],
                ["`FGI_IMPACT_STORE_SALES.FLAG_VERIFY` = `N`", "2,549",
                 "`sgi_fgi_impact_sales_summaries.sales_status = 'N'` — `N` = ประเมินแล้วยอดไม่ตก "
                 "(`growth_rate_diff >= 0`) **ไม่ใช่ความผิดพลาด** จึงแมปเป็น `E` ไม่ได้",
                 "✅ **เคาะแล้ว** (ข้อ 2.37) — โดเมนเดิมมี `N` อยู่แล้ว"],
                ["`FGI_IMPACT_STORE_SALES.FLAG_VERIFY` = `P`", "**151**",
                 "`sgi_fgi_impact_sales_summaries.sales_status = 'P'` (ขอแล้วรอผล) — "
                 "**โดเมนเดิมไม่มี `P` จึงเพิ่มเข้าไป** เป็น `W/P/Y/N/E`",
                 "✅ **เคาะแล้ว** (ข้อ 2.37)"],
                ["`FGI_IMPACT_STORE_SALES.FLAG_VERIFY` = `W`", "1", "`sales_status = 'W'`", "✅ ตรงตัว"],
                ["`sgi_fgi_impact_stores.sales_request_status`", "—",
                 "**ไม่มีต้นทางในระบบเดิม** — เป็นคอลัมน์ใหม่ที่ติดตาม *การขอ* ยอดขายระดับคู่ร้าน "
                 "(W ยังไม่ขอ · P ขอแล้ว · Y ได้ข้อมูล · E ขอไม่สำเร็จ) คนละเรื่องกับ `sales_status` "
                 "ที่เป็น *ผลทางธุรกิจ* จึงไม่มี `N`",
                 "ℹ️ ไม่เกี่ยวกับ migration"],
                ["`sales_status` = `E`", "0", "ไม่เคยถูกใช้เลยในระบบเดิม — สงวนไว้สำหรับกรณีที่ Job 5 คำนวณไม่ได้จริง ๆ", "ℹ️ ค่าใหม่ของโครงนี้"],
                ["`CREATE_BY` = `USER`", "**0**", "ไม่เคยถูกใช้เลย — ALM 23,126 · STA 3,138", "ℹ️ ค่าใหม่ของโครงนี้"],
                ["`UPDATE_BY`", "NULL ทั้ง 26,264 แถว", "`updated_by` เป็น NULL ได้อยู่แล้ว", "✅ ไม่มีปัญหา"],
                ["`DATASOURCE`", "ALM 4,670 · STA 2,877", "`datasource` ตรงตัว — **ไม่มี `HRS` จริง**", "✅ ไม่มีปัญหา"],
                ["`FLAG_ACTION`", "N 7,545 · Y 2 · W 1", "`flag_action` ตรงตัว (`Y/W/N`)", "✅ ไม่มีปัญหา"],
            ],
        ),
        h(2, "5.2.2 คีย์กันซ้ำที่ทำให้ load ล้ม (ยืนยันจากฐานเดิมจริง)"),
        table(
            ["คีย์ของโครงใหม่", "ข้อมูลเดิมละเมิดกี่กลุ่ม", "ต้องทำอะไรก่อน load"],
            [
                ["`uq_impact_store_pair (impacted_store_code, new_store_code, impact_month)`",
                 "**67 กลุ่ม** ในข้อมูลประวัติ · **93 กลุ่ม** ในตาราง live",
                 "แถวซ้ำส่วนใหญ่เหมือนกันทุกค่า (`COUNT(DISTINCT distance) = 1`) ต่างแค่ `IMPACT_STORE_ID` → "
                 "เลือกแถวเดียวด้วยกติกาเดียวกับ tie-breaker ของ Job 2 (`DISTANCE` น้อยสุด) แล้วรายงานจำนวนที่ตัดทิ้ง"],
                ["`uq_impact_process (impacted_store_code, impact_month)`",
                 "**9 กลุ่ม** (ข้อมูลประวัติ) · **8 กลุ่ม** (live)",
                 "✅ **เคาะครบแล้ว (ข้อ 2.38-2 · 2026-09-13)** — `impact_month` = `START_COMPENSATE_YEAR`+`MONTH` "
                 "· กติกาเลือกแถวอยู่ในหัวข้อ 5.2.4 ด้านล่าง (ตัดสินครบ 9/9 กลุ่ม) · "
                 "การเติม `datasource` เข้าคีย์ **ไม่ช่วยเลย** (ยังซ้ำ 9 กลุ่มเท่าเดิม)"],
                ["`storecode_i` / `storecode_n` → `VARCHAR(5)`",
                 "0 (ความยาวจริงสูงสุด = 5 ทั้งที่คอลัมน์เดิมเป็น `VARCHAR2(10)`)",
                 "ไม่ต้องทำอะไร — แต่ต้องคง `lpad(..., 5, '0')` ไว้"],
                ["`distance_km` → `NUMERIC(8,3)`",
                 "0 (ของเดิมเป็น `NUMBER(3,2)` ค่าจริง 0.03–1.52 กม.)",
                 "ไม่ต้องแปลงหน่วย — ของเดิมเก็บเป็นกิโลเมตรอยู่แล้ว · "
                 "⚠️ แถว `CREATE_BY = 'STA'` 3,137 แถวมี `DISTANCE = 0` และหน่วยเป็น NULL"],
            ],
        ),
        h(2, "5.2.3 การสร้างแถวแม่ `sgi_fgi_impact_processes` ตอน migrate"),
        p("โครงใหม่บังคับให้**คู่ร้านทุกแถวต้องมีแถวแม่** (`impact_process_id BIGINT NOT NULL` + FK) "
          "แต่ระบบเดิมสร้าง `FGI_IMPACT_STORE_ON_PROCESS` **เฉพาะตอนที่รอบชดเชยเริ่มจริง** "
          "(`ExportJdbc` · หลังคู่ร้านผ่านเป็น `P` และยอดขายผ่านแล้ว) — **ไม่ใช่ตอนนำเข้า** "
          "ผลคือคู่ร้านส่วนใหญ่ไม่มีแถวแม่ในระบบเดิม และ migration ต้อง **สร้างขึ้นใหม่**"),
        table(
            ["ตัวเลขจากข้อมูลจริง", "ค่า"],
            [
                ["คู่ร้านในระบบเดิม", "26,264 แถว"],
                ["แถวแม่ที่โครงใหม่ต้องมี = `DISTINCT (storecode_i, year, month)` ของคู่ร้าน", "**24,783 แถว**"],
                ["แถวแม่ที่ระบบเดิมมีจริง", "7,548 แถว (3,143 ร้าน)"],
                ["**แถวแม่ที่ต้องสร้างขึ้นใหม่ตอน migrate**", "🔴 **17,247 แถว (69.6%)**"],
                ["แถวแม่ที่ไม่มีคู่ร้านรองรับเลย", "**0** — สร้างจากคู่ร้านได้ครบ ไม่มีของตกหล่น"],
            ],
        ),
        p("**กติกาการสร้าง** — สองขั้น ห้ามสลับลำดับ"),
        table(
            ["ขั้น", "ทำอะไร"],
            [
                ["1", "สร้างแถวแม่จาก `SELECT DISTINCT storecode_i, year, month FROM FGI_IMPACT_STORE` "
                      "→ `impacted_store_code` · `impact_month = to_char(year)||'-'||lpad(month,2,'0')` · `impact_year = year`"],
                ["2", "`LEFT JOIN FGI_IMPACT_STORE_ON_PROCESS` ด้วย "
                      "`(storecode_i, start_compensate_year, start_compensate_month)` แล้วขนคุณสมบัติของรอบมา: "
                      "`flag_action` · `datasource` · `last_compensate_seq` · `last_compensate_seq_no` · "
                      "`start/end_compensate_month|year`"],
            ],
        ),
        p("🔴 **สองข้อที่ยังต้องเคาะและผูกกับข้อนี้โดยตรง** — 17,247 แถวที่สร้างใหม่จะได้ค่าอะไร:"),
        table(
            ["คอลัมน์", "ปัญหา", "ผลถ้าตั้งผิด"],
            [
                ["`flag_action`", "✅ เคาะแล้ว 2026-09-13 (ข้อ 2.38) — **17,247 แถวที่สร้างใหม่ใส่ `'N'`** "
                 "(ยังไม่มีรอบชดเชย) · แถวที่มีต้นทางให้ขน `flag_action` เดิมมาตรง ๆ",
                 "ใช้กติกาเดียวกับ Job 2 ที่รันจริง (ใส่ `'N'` ชัดเจน ไม่พึ่ง `DEFAULT 'Y'`) — "
                 "ตั้ง `Y` ผิด ๆ จะทำให้คิวรี \"คู่ที่มีอยู่แล้ว\" กันคู่ร้านใหม่ออกเงียบ ๆ"],
                ["`process_status`", "✅ เคาะแล้ว (ข้อ 2.17) — `IMPORTED` / `SALES_READY` / `READY_DOCUMENT` / "
                 "`DOCUMENT_CREATED` / `CLOSED` · DDL มี `DEFAULT 'IMPORTED'` แล้ว",
                 "ใช้กติกาอนุมานในตารางถัดไป — ห้ามใส่ `IMPORTED` ให้ทุกแถว เพราะ 8,114 แถวมีความคืบหน้าไปแล้วจริง"],
            ],
        ),
        p("**กติกาอนุมาน `process_status` ตอน migrate** — ไล่จากบนลงล่าง เจอข้อแรกที่จริงแล้วหยุด "
          "(ตัวเลขจากข้อมูลจริง 2026-09-12)"),
        table(
            ["ลำดับ", "เงื่อนไข", "process_status", "แถว"],
            [
                ["1", "แถวแม่เดิมมี `FLAG_ACTION = 'N'` (รอบปิดแล้ว)", "`CLOSED`", "**7,542**"],
                ["2", "มีแถวใน `FGI_IMPACT_STORE_COMPENSATE` ของงวดนั้น (เคยสร้างเอกสารแล้ว)", "`DOCUMENT_CREATED`", "**572**"],
                ["3", "มีแถวแม่เดิมอยู่ แต่ยังไม่เข้าข้อ 1-2", "`READY_DOCUMENT`", "0"],
                ["4", "มี `FGI_IMPACT_STORE_SALES` ของงวดนั้นที่ `FLAG_VERIFY IN ('Y','N')`", "`SALES_READY`", "**2,498**"],
                ["5", "นอกนั้นทั้งหมด (ส่วนใหญ่คือคู่ร้านที่ถูกตัดทิ้งหรือค้าง `W`)", "`IMPORTED`", "**14,180**"],
            ],
        ),
        p("⚠️ ผลรวมของตารางนี้คือ **24,792** แต่แถวแม่ที่ต้องมีคือ **24,783** — ต่างกัน **9 แถว** พอดีกับ "
          "จำนวนกลุ่มแถวแม่ที่ซ้ำ การ `LEFT JOIN` จึงคืนแถวเกิน · "
          "✅ **แก้ด้วยการตัดแถวซ้ำตามกติกาในข้อ 5.2.4 ก่อน แล้วจึงอนุมาน `process_status`** "
          "(ตัดแล้วได้ 24,783 พอดี)"),
        h(2, "5.2.4 กติกาตัดแถวแม่ที่ซ้ำ (`uq_impact_process`)"),
        p("**มติ 2026-09-13 (DECISIONS ข้อ 2.38-2): เก็บแถวที่ `LAST_COMPENSATE` ใหม่สุด** "
          "แต่ข้อมูลจริงบอกว่าเกณฑ์เดียวไม่พอ — **ตัดสินได้แค่ 2 จาก 9 กลุ่ม** เพราะอีก 7 กลุ่ม "
          "เหมือนกันทุกคอลัมน์ จึงต้องมี tie-breaker ต่ออีก 2 ชั้น"),
        table(
            ["ชั้น", "เกณฑ์", "เหตุผล"],
            [
                ["1", "`last_compensate_year DESC, last_compensate_month DESC`",
                 "**มติหลัก** — แถวที่ก้าวหน้ากว่าสะท้อนสถานะล่าสุดจริง · ตัดสินได้ 2 กลุ่ม"],
                ["2", "`create_date ASC`",
                 "ข้อมูลจริงจับคู่กันเป็น `00:00:00` (แถว backfill ที่ใส่ด้วยมือ/สคริปต์) กับ `17:00:xx` "
                 "(แถวที่ job สร้างตามตาราง) · ทั้ง 2 กลุ่มที่ชั้น 1 ตัดสินได้ **แถว backfill เป็นผู้ชนะ** "
                 "การเรียง `ASC` จึงสอดคล้องกัน · ตัดสินอีก 7 กลุ่ม"],
                ["3", "`impact_process_id ASC`",
                 "กันเสมอเด็ดขาด — ผลต้อง deterministic รันกี่ครั้งก็ได้แถวเดิม"],
            ],
        ),
        p("ยืนยันกับข้อมูลจริง: กติกา 3 ชั้นนี้ **ตัดสินครบทั้ง 9 กลุ่ม (9/9)** เหลือผู้ชนะกลุ่มละ 1 แถว "
          "และตัดทิ้ง **9 แถว** — ทำให้จำนวนแถวแม่ลงตัวที่ **24,783** พอดี "
          "(ก่อนหน้านี้ตารางอนุมาน `process_status` ในข้อ 5.2.3 รวมได้ 24,792 เพราะ `LEFT JOIN` คืนแถวเกิน 9)"),
        p("**แถวลูกของแถวที่ถูกตัด — ลบทิ้งได้ ไม่ต้อง repoint**"),
        table(
            ["ตรวจ", "ผล"],
            [
                ["แถวแม่ที่ถูกตัด", "9 แถว"],
                ["แถวลูกใน `FGI_IMPACT_STORE_COMPENSATE` ของแถวที่ถูกตัด", "20 แถว"],
                ["แถวลูกของแถวที่เก็บไว้ (เฉพาะกลุ่มที่ซ้ำ)", "20 แถว"],
                ["ลูกของแถวที่ถูกตัด ที่**ไม่มี**คู่งวดเดียวกันฝั่งผู้ชนะ", "**0 แถว**"],
                ["คู่ที่ชนกัน 20 คู่ · `compensate_status` ตรงกัน", "**20 จาก 20 คู่**"],
            ],
        ),
        p("→ ลูกของแถวที่ถูกตัดเป็น **สำเนาซ้ำของลูกฝั่งผู้ชนะทั้งหมด** (งวดตรงกัน สถานะตรงกัน) "
          "จึง **ลบทิ้งพร้อมแถวแม่ได้เลย ไม่เสียข้อมูล และไม่ต้องย้าย FK**"),
        p("⚠️ **ผลข้างเคียงที่ต้องยอมรับ:** `last_compensate_seq_no` ของแถวที่เก็บไว้จะกระโดด "
          "(เช่น กลุ่ม `02985` งวด 2024-03 เก็บแถว `seq_no = 13` แล้วทิ้งแถว `seq_no = 4`) "
          "เลขลำดับในระบบใหม่จึงไม่ต่อเนื่อง — **ห้าม renumber** เพราะจะทำให้อ้างอิงย้อนหลังกับระบบเดิมไม่ตรง"),
        h(2, "5.3 แผน Cutover"),
        table(
            ["รอบ", "กิจกรรม", "เกณฑ์ผ่าน"],
            [
                ["T-14 วัน", "Profiling ต้นทาง + dry-run รอบที่ 1", "อธิบายแถวที่ reject ได้ทุก reason code"],
                ["T-7 วัน", "Full load บน staging + reconcile", "จำนวนแถว/ยอดเงินตรง หรืออธิบายส่วนต่างได้"],
                ["T-2 วัน", "ซ้อม cutover เต็มรูปแบบรวม rollback", "rollback สำเร็จอย่างน้อย 1 ครั้ง"],
                ["T-0 (freeze)", "หยุดใช้ระบบเดิม -> delta load -> reconcile รอบสุดท้าย -> ย้าย workflow ที่ยังวิ่ง", "ทุกเอกสารที่ยังไม่จบ flow เปิดในระบบใหม่ได้ที่ state เดิม"],
                ["T+1..T+7", "เฝ้าระวัง · เก็บ snapshot ก่อน cutover ไว้", "ไม่มีเอกสารที่หาไม่เจอ/สถานะเพี้ยน"],
            ],
        ),
        h(2, "5.4 การย้าย workflow ที่ยังวิ่งอยู่"),
        p(
            "เอกสารที่ยังไม่จบ flow ต้องถูกเปิด transaction ใหม่ใน `@srm/glb-workflow` ให้อยู่ state ปัจจุบัน — "
            "ไม่ใช่เริ่มต้นที่ state แรก ขั้นตอนที่ต้องทำต่อเอกสาร: `initializeWorkflow` -> เดิน event จนถึง state ปัจจุบัน "
            "หรือ set `current_state_id`/`current_status_id`/`current_approver` โดยตรง แล้วเติม `workflow_history` "
            "ย้อนหลังจาก `CompensateHistory` เพื่อให้ timeline ไม่ขาด · เขียนผ่าน API ของ library เท่านั้น ห้าม INSERT ตารางของ engine ตรง "
            "เพราะ engine ไม่มี API สำหรับ set state ตรง ๆ"
        ),
        *implementation_rule_blocks(
            "5.5 ข้อกำหนดด้าน migration ที่ต้องยึด",
            [
                ["`fcs_qssi_score`", "**ไม่มีอะไรต้อง migrate** — SGI อ่านตารางเดิมอย่างเดียว ไม่ต้อง dedup/backfill", "ระบบ SBP เดิมนำเข้าให้แล้ว (ปิด 2026-08-24 · ตัด Job 1)"],
                ["ร้าน SP", "migrate เฉพาะร้านที่เคยเข้ารอบชดเชยเข้ามาเป็น snapshot ใน `sgi_impacted_stores`", "กันเอกสารย้อนหลังอ่านไม่ได้เมื่อร้านถูกยกเลิก (ตัดสิน 2026-08-10)"],
                ["`reference_id` ของ workflow", "ตอน backfill ให้ผูกด้วย **`sgi_compensation_documents.id`** (ส่งเป็น string)", "ตรงกับสัญญาของ engine (varchar(255)) และแพตเทิร์นของระบบเดิม (ปิด 2026-08-17)"],
                ["ลำดับการ import", "master โซน C → โซน A (`sgi_fgi_impact_processes` ก่อนลูกทั้งหมด) → โซน B (`sgi_compensation_documents` ก่อน `sgi_document_*`) → เปิด workflow ผ่าน engine เป็นขั้นสุดท้าย", "FK ของโซน B ชี้กลับโซน A และตารางลูกทั้ง 6 FK ไป `doc_no` แบบ NOT NULL"],
            ],
        ),
    ]


def integration_sbp_platform_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 User Context จาก BFF"),
        p(
            "SGI **ไม่มีระบบ login ของตัวเอง** — login จริงอยู่ที่ **AWS Cognito ฝั่ง BFF** · FE ไม่แตะ token · "
            "BFF ยืนยันตัวเองกับ backend ด้วย `x-api-key` แล้วส่งบริบทผู้ใช้ต่อเป็น header · "
            "guard ของ store-backend แปลง header เป็น user context แล้วส่งต่อให้ service ทุกชั้น "
            "(รูปแบบเดียวกับที่ `export-data.service.ts` / `relation.service.ts` / `backlog.service.ts` ของ BFF ใช้อยู่แล้ว)"
        ),
        h(3, "5.1.1 ตัวอย่าง request จริงที่ SGI ได้รับ"),
        p("**HTTP request จาก BFF → store-backend (SGI)**"),
        code(
            """POST /api/v1/sgi/document/2026%2F00123/actions HTTP/1.1
Host: store-backend:3004
Content-Type: application/json
accept-language: th

x-api-key: 8f2b1c94-6d5e-4a70-b1c3-9ee27a4f0d51
x-user-id: 0000123456
x-user-group-id: 08
x-user-full-name: %E0%B8%AA%E0%B8%A1%E0%B8%8A%E0%B8%B2%E0%B8%A2%20%E0%B9%83%E0%B8%88%E0%B8%94%E0%B8%B5
x-user-permissions: [{"url":"/sgi/document/waiting","canView":true,"canManage":true,"canExport":false,"canOther":false},{"url":"/sgi/report/status-summary","canView":true,"canManage":false,"canExport":true,"canOther":false}]

{"result":"ส่งหน่วยงานส่งเสริมธุรกิจ SBP","comment":"ตรวจยอดชดเชยแล้ว"}""",
            "http",
        ),
        h(3, "5.1.2 แต่ละ header คืออะไร ใช้ทำอะไร"),
        table(
            ["Header", "ตัวอย่างค่า", "มาจากไหน", "SGI ใช้ทำอะไร", "ถ้าไม่มี/ผิด"],
            [
                ["`x-api-key`", "`8f2b1c94-6d5e-4a70-b1c3-9ee27a4f0d51`",
                 "env ของ BFF ต่อ backend (`API_STORE_BACKEND_KEY_VALUE`) เทียบกับ `X_API_KEY` ของ store-backend",
                 "พิสูจน์ว่า request มาจาก BFF จริง ไม่ใช่ใครยิงตรง — **ไม่ใช่ตัวตนผู้ใช้**",
                 "**401** `ไม่พบสิทธิ์การเข้าใช้งาน` · `HttpHeaderGuard` ของระบบเดิมเทียบแบบ `===` ตรง ๆ"],
                ["`x-user-id`", "`0000123456`",
                 "`sub`/employee id จาก JWT ของ Cognito (BFF ถอดจาก cookie)",
                 "🔴 **ตัวตนผู้ใช้** — ใส่ใน `created_by`/`updated_by`, `sgi_consideration_logs.consider_by`, "
                 "และส่งเป็น `userId` เข้า `eventWorkflow` / `initializeWorkflow` ของ engine",
                 "**401** — ห้ามให้ผ่านโดยไม่มี userId เพราะ audit trail จะขาด"],
                ["`x-user-group-id`", "`08`",
                 "auth-backend (ABS) — กลุ่มสิทธิ์ของผู้ใช้",
                 "map เป็น **section_code** ของ workflow (06/08/01/02/03) เพื่อกรองกล่องงานและตัดสินว่ากดปุ่มไหนได้",
                 "**403** เมื่อ endpoint ต้องรู้ section · endpoint อ่านอย่างเดียวยอมให้ผ่านได้"],
                ["`x-user-full-name`", "`%E0%B8%AA%E0%B8%A1%E0%B8%8A%E0%B8%B2%E0%B8%A2%20%E0%B9%83%E0%B8%88%E0%B8%94%E0%B8%B5`  → `สมชาย ใจดี`",
                 "employee backend (`/employees/{empId}/profile`)",
                 "แสดงชื่อผู้ทำรายการใน timeline/อีเมล · **ต้อง `decodeURIComponent` ก่อนใช้เสมอ** (BFF encode มา)",
                 "ไม่บล็อก — fallback เป็น `x-user-id` แล้วเติมชื่อทีหลังจาก `business_user`"],
                ["`x-user-permissions`", "`[{\"url\":\"/sgi/document/waiting\",\"canView\":true,\"canManage\":true,\"canExport\":false,\"canOther\":false}]`",
                 "auth-backend `GET /groups/current-user/permissions` (ชุดเดียวกับที่ FE ใช้)",
                 "กันเรียก API ตรงโดยข้ามหน้าจอ — เทียบ `url` ของหน้าที่เป็นเจ้าของ endpoint นั้น + `canManage` ก่อนยอมให้เขียน",
                 "**403** สำหรับ endpoint ที่เขียนข้อมูล · ⚠️ ดูข้อควรระวังด้านล่าง"],
                ["`accept-language`", "`th`", "BFF ส่งต่อจาก browser",
                 "เลือกภาษาข้อความ error — SGI ใช้ **ไทย verbatim ตาม SRS** เป็นค่าตั้งต้นเสมอ", "ไม่บล็อก — default `th`"],
            ],
        ),
        p(
            "⚠️ **ข้อควรระวัง `x-user-permissions` — ใช้เป็นด่านเสริมเท่านั้น:** "
            "เอกสารวิเคราะห์ระบบเดิมยืนยันแค่ว่า *มี* header ตัวนี้และเนื้อหาคือชุดสิทธิ์ต่อ URL "
            "(`canView` / `canManage` / `canExport` / `canOther`) แต่**รูปแบบ serialize ไม่ผูกเป็นสัญญา** จึงต้องเขียนโค้ดเผื่อไว้ 2 เรื่อง — "
            "(1) รูปแบบที่ serialize มา (JSON ตรง ๆ · base64 · หรือย่อเป็น CSV) และ "
            "(2) พฤติกรรมเมื่อสิทธิ์เยอะจน header ยาวเกินลิมิตของ proxy (ปกติ ~8 KB) · "
            "**จนกว่าจะยืนยัน ห้ามใช้ header นี้เป็นด่านเดียว** — ให้ตัดสินสิทธิ์เขียนจาก "
            "`x-user-group-id` + สถานะเอกสาร + ผู้ถืองานจาก `getTransaction()` ของ engine เป็นหลัก "
            "แล้วใช้ `x-user-permissions` เป็นด่านเสริม"
        ),
        h(3, "5.1.3 Guard ที่ต้องเขียน"),
        code(
            """// src/common/guards/bff-user.guard.ts (ยึด convention ของ store-backend)
export interface SgiUser {
  userId: string;          // x-user-id            เช่น '0000123456'
  groupId: string;         // x-user-group-id      เช่น '08'
  fullName: string;        // x-user-full-name     decode แล้ว เช่น 'สมชาย ใจดี'
  permissions: UrlPermission[];   // x-user-permissions  (ดูข้อควรระวัง 5.1.2)
}

@Injectable()
export class BffUserGuard implements CanActivate {
  constructor(private readonly config: ConfigService) {}

  canActivate(ctx: ExecutionContext): boolean {
    const req = ctx.switchToHttp().getRequest();

    // 1) ยืนยันว่ามาจาก BFF จริง — เทียบกับ X_API_KEY (มาจาก Secret Manager ห้าม hardcode/commit)
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== this.config.get('X_API_KEY')) {
      throw new UnauthorizedException('ไม่พบสิทธิ์การเข้าใช้งาน');
    }

    // 2) ตัวตนผู้ใช้ — ไม่มี userId = ไม่ให้ผ่าน เพราะ audit trail จะขาด
    const userId = req.headers['x-user-id'];
    if (!userId) throw new UnauthorizedException('ไม่พบสิทธิ์การเข้าใช้งาน');

    req.user = {
      userId,
      groupId: req.headers['x-user-group-id'] ?? '',
      // BFF encodeURIComponent มา -> ต้อง decode ก่อนใช้ ไม่งั้นชื่อไทยกลายเป็น %E0%B8...
      fullName: safeDecode(req.headers['x-user-full-name']),
      permissions: parsePermissions(req.headers['x-user-permissions']),
    } satisfies SgiUser;
    return true;
  }
}

/** header อาจว่าง/พัง — ห้ามให้ทั้ง request ล้มเพราะ decode ไม่ผ่าน */
function safeDecode(v?: string): string {
  if (!v) return '';
  try { return decodeURIComponent(v); } catch { return v; }
}

/** parse แบบป้องกันไว้ก่อน — ถ้ารูปแบบไม่ตรงให้คืน [] แล้วตกไปใช้ด่าน group/สถานะเป็นหลัก (ดู 5.1.2) */
function parsePermissions(v?: string): UrlPermission[] {
  if (!v) return [];
  try { const j = JSON.parse(v); return Array.isArray(j) ? j : []; } catch { return []; }
}""",
            "ts",
        ),
        h(3, "5.1.4 ใช้ใน controller / ทดสอบเอง"),
        code(
            """// controller — อ่าน user ที่ guard แปะไว้ ห้ามอ่าน header ตรงในทุก service
// ⚠️ ไม่มี 'sgi/' ใน @Controller() เพราะ prefix ผูกที่ระดับโมดูล:
//    RouterModule.register([{ path: 'sgi', module: SgiModule }])
//    -> URL จริงคือ /api/v1/sgi/document/... (ดู LLDD-BE-API-Common-Contracts 5.80)
@UseGuards(BffUserGuard)
@Controller('document')
export class SgiDocumentController {
  @Post(':docNo/actions')
  submit(@Param('docNo') docNo: string, @Body() dto: ActionDto, @Req() req: { user: SgiUser }) {
    // docNo มาเป็น '2026%2F00123' -> Nest decode ให้แล้วเป็น '2026/00123'
    return this.service.submit(docNo, dto, req.user);
  }
}""",
            "ts",
        ),
        code(
            """# ยิงทดสอบเองตอน dev (ไม่ผ่าน BFF) — ใส่ header ให้ครบเหมือนที่ BFF ส่งจริง
curl -X POST 'http://localhost:3004/api/v1/sgi/document/2026%2F00123/actions' \\
  -H 'x-api-key: '"$X_API_KEY" \\
  -H 'x-user-id: 0000123456' \\
  -H 'x-user-group-id: 08' \\
  -H 'x-user-full-name: %E0%B8%AA%E0%B8%A1%E0%B8%8A%E0%B8%B2%E0%B8%A2%20%E0%B9%83%E0%B8%88%E0%B8%94%E0%B8%B5' \\
  -H 'accept-language: th' \\
  -H 'Content-Type: application/json' \\
  -d '{"result":"ส่งหน่วยงานส่งเสริมธุรกิจ SBP","comment":"ตรวจยอดชดเชยแล้ว"}'""",
            "bash",
        ),
        bullets([
            "🔴 **ห้ามให้ FE ส่ง header เหล่านี้เอง** — ต้องมาจาก BFF เท่านั้น · store-backend ต้องอยู่หลัง network layer ที่เปิดให้เฉพาะ BFF เข้าถึง",
            "🔴 **ห้าม log ค่า `x-api-key`** ลง application log / error message ทุกกรณี",
            "`x-user-id` ที่ส่งเข้า engine ต้องเป็นตัวเดียวกับที่บันทึกใน `sgi_consideration_logs` — ไม่งั้น timeline ของ SGI กับ `workflow_history` ของ engine จะชี้คนละคน",
            "unit test ต้องครอบ: ไม่มี `x-api-key` → 401 · `x-api-key` ผิด → 401 · ไม่มี `x-user-id` → 401 · "
            "`x-user-full-name` เป็น %-encoded → decode ถูก · `x-user-permissions` พัง/ว่าง → ไม่ throw แต่ตกไปใช้ด่าน group",
        ]),
        h(2, "5.2 Response Envelope"),
        code(
            """// ResponseInterceptor ของ store-backend ห่อให้แล้ว — service ห้ามห่อซ้ำ
// success : { success: true,  data: <payload> }
// error   : { success: false, data: null, error: { code, message } }
// message ต้องเป็นภาษาไทย verbatim ตาม SRS และโยนผ่าน HttpException เท่านั้น""",
            "ts",
        ),
        h(2, "5.3 ไฟล์แนบผ่าน S3 ของระบบเดิม"),
        table(
            ["ขั้นตอน", "ปลายทาง", "สิ่งที่ SGI เก็บเอง"],
            [
                ["อัปโหลด", "POST /statement/upload-file-aws (ระบบ SBP เดิม)", "objectKey + ชื่อไฟล์ + ขนาด + content type + section_code"],
                ["ดาวน์โหลด", "POST /statement/download-file-aws (ระบบ SBP เดิม)", "SGI แปลงเป็น **binary stream** ก่อนคืนให้ FE · ห้ามคืน objectKey ให้ FE"],
                ["ลบ/purge", "lifecycle ของ S3 + flag ใน sgi_document_attachments", "purge_flag / storage_delete_status"],
            ],
        ),
        p(
            "🔴 **ข้อจำกัดที่ต้องรู้ก่อนเขียนโค้ด (ตรวจ `store-backend` 2026-08-26):** `AwsService` ของระบบเดิมเป็น "
            "**wrapper แบบ base64** ไม่ใช่ stream — `upload-file-aws` รับไฟล์เป็น base64 และ `download-file-aws` "
            "**คืนไฟล์เป็น base64 ใน JSON** สายส่งจริงจึงเป็น "
            "`FE ← binary stream ← SGI BE ← base64 JSON ← /statement/download-file-aws ← S3`"
        ),
        table(["ผลกระทบ", "ตัวเลข", "ต้องทำอย่างไร"], [
            ["base64 ทำให้ payload โตขึ้น ~33%", "ไฟล์ 5 MB → **~6.7 MB** ใน JSON",
             "ยังไม่ชน body limit ของ store-backend (**100 MB** ที่ `main.ts:33`) แต่กิน memory ต่อ request จริง"],
            ["ปุ่ม **ดาวน์โหลดทั้งหมด (.zip)** ต้องดึงหลายไฟล์", "n ไฟล์ × 1.33 พร้อมกัน",
             "🔴 ห้ามโหลดทุกไฟล์เข้า memory พร้อมกัน — ดึงทีละไฟล์แล้ว **stream เข้า zip ทันที** (archiver แบบ streaming)"],
            ["FE ไม่ควรรู้ว่าใต้ท้องเป็น base64", "—",
             "สัญญาฝั่ง FE ยังเป็น **binary stream + Content-Type / Content-Disposition** ตาม `LLDD-BE-API-Attachment-Sales-Timeline` — SGI เป็นคนแปลง"],
        ]),
        p(
            "⚠️ **ข้อจำกัดที่ต้องออกแบบเผื่อ:** wrapper ของระบบเดิมอาจไม่รองรับ **range request / partial download** · "
            "ถ้าไม่รองรับ ไฟล์ใหญ่จะ resume ไม่ได้ และปุ่มดาวน์โหลดทั้งหมดต้องกำหนดเพดานจำนวน/ขนาดรวม"
        ),
        p(
            "**แก้ความเข้าใจผิดเดิม (ตรวจ schema จริง 2026-08-07):** เอกสารรุ่นก่อนเคยเขียนว่าถ้าใช้ตาราง "
            "`upload_general` ของระบบเดิมจะติด FK `job_id` — **ไม่จริง** `job_id` และ `audit_log_id` เป็น "
            "**nullable ทั้งคู่** · เหตุผลจริงที่ SGI ต้องมี `sgi_document_attachments` ของตัวเองคือ `upload_general` "
            "**ไม่มีคอลัมน์** `file_size` · `content_type` · `section_code` · `upload_status` · `purge_flag`"
        ),
        h(2, "5.4 อีเมล"),
        p(
            "ส่งผ่าน `@gosoft-sbp/email-lib` โดยอ่านเนื้อหาจาก `email_template` (85 แถว) และบันทึกผลที่ "
            "`email_sent` (5,392 แถว)"
        ),
        p(
            "**แก้ความเข้าใจผิดเดิม (ตรวจ schema จริง 2026-08-07):** เอกสารรุ่นก่อนเคยเขียนว่าระบบเดิม "
            "**ไม่มีที่เก็บ CC ของอีเมล** — **ไม่จริง** มีอยู่ 3 ที่: `email_sent.mail_cc` · "
            "`fcs_reminder_log.reminder_cc` · `fml_email_account`"
        ),
        h(2, "5.5 ค่ากำหนดกลาง — `mas_param` กับ `common_code` คืออะไร"),
        p(
            "🔴 **สองตารางนี้เป็นของระบบ SBP เดิม อยู่ใน schema `sps_store` เท่านั้น** และ "
            "**ค่าของ SGI ยังไม่มีอยู่จริง — เป็นแถวที่เราต้อง seed เองตอน setup** "
            "(เอกสารรอบก่อนเขียนกำกวมจนอ่านเหมือนมีข้อมูลอยู่แล้ว · แก้ 2026-08-25)"
        ),
        table(
            ["ตาราง", "คืออะไร", "โครงคีย์", "ของจริงตอนนี้ (ตรวจ 07/08/2026)"],
            [
                ["`sps_store.mas_param`",
                 "**ตาราง config กลางของ store-backend** — คู่ชื่อ/ค่าแบบอิสระ ที่ทั้งระบบเดิมใช้ร่วมกัน "
                 "(เช่น `GROUP_ID_VIEW_ALL_STMT` คุมว่ากลุ่มไหนเห็นใบแจ้งยอดทั้งหมด · ช่วงวันที่ของไฟล์อากรแสตมป์)",
                 "`param_name` · `param_value`(4000) · `ref_name` · `description` · `is_config` · `active_flag`",
                 "**93,763 แถว** · ⚠️ **ไม่มี PK ไม่มี unique** มีแค่ btree `(param_name, param_value)` → "
                 "ชื่อพารามิเตอร์ซ้ำได้ ต้องกันเองที่ระดับแอปและ `WHERE active_flag = 'Y'` เสมอ"],
                ["`sps_store.common_code`",
                 "**lookup กลาง** ของทั้งระบบเดิม — ชุดรหัส/ชื่อที่ใช้ทำ dropdown",
                 "`code_type`(**20**) · `seq_no` · `code_value`(100) · `code_name`(1000) · `other_value`(50) · `code_mapping`(100) · `active_flag`",
                 "**2,641 แถว** · ⚠️ **ไม่มี PK ไม่มี unique** บน (`code_type`,`code_value`) · "
                 "`code_type` ต้องลงทะเบียนที่ **`common_code_type`** (378 แถว) ก่อน"],
            ],
        ),
        h(3, "5.5.1 ทำไมค้นแล้วไม่เจอข้อมูล (2 กับดักที่เจอจริง)"),
        table(["กับดัก", "ข้อเท็จจริง", "ต้องทำอย่างไร"], [
            ["ค้นผิด schema",
             "`mas_param` มี **เฉพาะ `sps_store`** — ใน `sps_auth` **ไม่มีตารางนี้เลย** · "
             "ส่วน `common_code` มี **ทั้งสอง schema แต่เป็นคนละตาราง**: `sps_store` 14 คอลัมน์ 2,641 แถว vs "
             "`sps_auth` **13 คอลัมน์ 2,594 แถว** (ชุดเก่าของ auth-backend)",
             "🔴 SGI ใช้ **`sps_store` เท่านั้น** · เขียน schema นำหน้าทุกครั้งใน SQL "
             "(กับดักเดียวกับตาราง `workflow_*` ที่มีสองชุด — ดู 5.4)"],
            ["คิดว่าค่าของ SGI มีอยู่แล้ว",
             "`SGI_APPROVE_LIMIT` · `SGI_DECISION` · `SGI_DATASOURCE` **ยังไม่มีสักแถวในระบบจริง** — "
             "เป็นค่าที่การออกแบบ *วางแผนจะเพิ่ม* ไม่ใช่ของเดิมที่ reuse ได้ทันที",
             "ต้อง **seed เองตอน setup** (ดู 5.5.2) และนับเป็นงานของ `LLDD-BE-Data-Migration-Cutover`"],
        ]),
        h(3, "5.5.2 ค่าที่ SGI ต้อง seed เอง"),
        table(["ค่า", "ลงที่ไหน", "คีย์ที่ใช้", "สถานะ"], [
            ["วงเงินอนุมัติ เกณฑ์เดียว **100,000**", "`sps_store.common_code`",
             "`code_type = 'SGI_APPROVE_LIMIT'` · `code_value = '100000'` · `code_name = '100000'` ""— 🔴 **ยึดของที่ติดตั้งในฐาน dev จริง** (ตรวจ 2026-09-16) · เดิมเอกสารเขียน `'THRESHOLD'` ""ซึ่งไม่ตรงกับแถวที่ถูก seed ไปเมื่อ 2026-08-27 → seed ใหม่จะได้แถวที่สอง",
             "🔴 **ยังไม่มี — ต้อง seed**"],
            ["ผลการพิจารณา 7 ค่า (มติ DP-9)", "`sps_store.common_code`",
             "`code_type = 'SGI_DECISION'`", "🔴 **ยังไม่มี — ต้อง seed**"],
            ["ต้นทาง `PRO` (เชิงรุก) · `REA` (เชิงรับ)", "`sps_store.common_code`",
             "`code_type = 'SGI_DATASOURCE'`", "🔴 **ยังไม่มี — ต้อง seed** (เพิ่มจากของเดิมที่มี `ALM`/`STA`)"],
            ["รัศมีผลกระทบ 1 กม. (กทม./ปริมณฑล) · 2 กม. (ต่างจังหวัด)", "`sps_store.mas_param`",
             "`param_name = 'SGI_IMPACT_RADIUS_BKK' / 'SGI_IMPACT_RADIUS_UPC'`", "🔴 **ยังไม่มี — ต้อง seed** · อ่านตอนคำนวณ ห้าม hardcode"],
            ["เกณฑ์ยอดขายไม่ครบ **60 วัน** · growth rate **-10%**", "`sps_store.mas_param`",
             "`param_name = 'SGI_SALES_DAYS_MIN' / 'SGI_GROWTH_RATE_MAX'`",
             "🔴 **ยังไม่มี — ต้อง seed** · ใช้กับธงข้อมูลผิดปกติและ Gen Flow Gate"],
        ]),
        code(
            """-- seed ตอน setup (idempotent) — ⚠️ ทั้งสองตารางไม่มี unique จึงต้อง guard ด้วย NOT EXISTS เอง
-- 1) ลงทะเบียน code_type ก่อนเสมอ ไม่งั้น dropdown ของระบบเดิมจะไม่รู้จัก
INSERT INTO sps_store.common_code_type (code_type, code_type_name, active_flag, create_date, create_user)
SELECT 'SGI_APPROVE_LIMIT', 'วงเงินอนุมัติ ประกันรายได้', 'Y', CURRENT_TIMESTAMP, 'SGI-SETUP'
WHERE NOT EXISTS (SELECT 1 FROM sps_store.common_code_type WHERE code_type = 'SGI_APPROVE_LIMIT');

-- 2) ค่าจริง · code_type เป็น varchar(20) -> 'SGI_APPROVE_LIMIT' = 19 ตัว เหลือที่ว่าง 1 ตัวเท่านั้น
INSERT INTO sps_store.common_code (code_type, seq_no, code_value, code_name, active_flag, create_date, create_user)
SELECT 'SGI_APPROVE_LIMIT', 1, '100000', '100000', 'Y', CURRENT_TIMESTAMP, 'SGI-SETUP'
WHERE NOT EXISTS (SELECT 1 FROM sps_store.common_code
                  WHERE code_type = 'SGI_APPROVE_LIMIT' AND code_value = '100000');

-- 3) ค่ากำหนดกลางที่ไม่ใช่ lookup -> mas_param
INSERT INTO sps_store.mas_param (param_name, param_value, description, is_config, active_flag, create_by, create_date)
SELECT 'SGI_SALES_DAYS_MIN', '60', 'จำนวนวันยอดขายขั้นต่ำก่อนถือว่าข้อมูลครบ', 'Y', 'Y', 'SGI-SETUP', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM sps_store.mas_param
                  WHERE param_name = 'SGI_SALES_DAYS_MIN' AND active_flag = 'Y');

-- อ่านค่ากลับมาใช้ — ต้องกรอง active_flag เสมอ และ LIMIT 1 เพราะไม่มี unique กันซ้ำ
SELECT param_value FROM sps_store.mas_param
WHERE param_name = :name AND active_flag = 'Y'
ORDER BY update_date DESC NULLS LAST, create_date DESC LIMIT 1;""",
            "sql",
        ),
        h(3, "5.5.3 ของเดิมอยู่ที่ไหน — ทำไมค้นใน `mas_param`/`common_code` แล้วไม่เจอ"),
        p(
            "🔴 **ข้อมูลของงานประกันรายได้เดิม ไม่เคยอยู่ใน `mas_param` หรือ `common_code` เลย** — สองตารางนั้นเป็นของ "
            "**store-backend (SBP Mall)** ส่วนของเดิมอยู่คนละฐานข้อมูล คือ **SQL Server `CPA_FRN_FGI`** (ฝั่ง K2 · 47 ตาราง) "
            "กับ **Oracle** (ฝั่ง FGI/FCS) · ที่เอกสารเขียนว่า *\"ใช้ `common_code` แทน\"* หมายถึง **ปลายทางที่จะย้ายไป** "
            "ไม่ใช่ที่ที่ข้อมูลอยู่ตอนนี้"
        ),
        table(["ค่า", "ของเดิมอยู่ที่ (ฐานข้อมูลเดิม)", "ปลายทางใหม่", "ต้องทำอะไร"], [
            ["วงเงินอนุมัติ", "**MSSQL** `SectionProfile.SectionLimitCost` — มีค่าเดียวคือ section 02 (GM) = 100,000 · AVP เป็น NULL",
             "`sps_store.common_code` `SGI_APPROVE_LIMIT`",
             "🔴 **ห้าม migrate ค่าเดิมมาตรง ๆ** — เกณฑ์เก่าไม่ตรง SDD GI · **seed ใหม่** เป็นเกณฑ์เดียว 100,000"],
            ["ผลการพิจารณา", "**MSSQL** `DecisionProfile`", "`sps_store.common_code` `SGI_DECISION`",
             "แปลงชื่อ 3 ชุด (ปุ่ม/flow/ผลลัพธ์) ลง `code_name` / `code_mapping` / `other_value` แล้ว seed"],
            ["ปัจจัยภายนอก", "**MSSQL** `FactorProfile`", "**ตาราง `sgi_external_factors` ของ SGI** (ไม่ได้ไป `common_code` · มติ DP-9)",
             "migrate เข้าตารางของเราเอง เพราะมีหน้าจอ CRUD และช่องข้อความของ `common_code` ไม่พอ"],
            ["ร้านคู่แข่ง 11 แบรนด์", "**MSSQL** `CompetitionProfile` + **ORA** `MAS_STORE_COMPETITOR`",
             "**ตาราง `sgi_competitors` ของ SGI** (มติ DP-9)", "migrate เข้าตารางของเราเอง"],
            ["รัศมี/เกณฑ์คำนวณ (1-2 กม. · 60 วัน · -10%)", "**hardcode อยู่ในโค้ด Java เดิม** ไม่ได้อยู่ในตารางไหน",
             "`sps_store.mas_param`", "🔴 **ไม่มีของเดิมให้ migrate** — ยกค่าจากโค้ดมา seed เป็น data"],
        ]),
        p(
            "**สรุปสั้น ๆ:** ค้นใน `mas_param`/`common_code` แล้วไม่เจอเป็นเรื่อง**ปกติและถูกต้อง** — "
            "(1) ของเดิมอยู่คนละฐานข้อมูล (MSSQL/Oracle) · (2) ค่าของ SGI ยังไม่ถูก seed · "
            "(3) ถ้าเปิดผิด schema (`sps_auth`) จะยิ่งไม่เจอเพราะ `mas_param` ไม่มีในนั้นเลย"
        ),
        bullets([
            "🔴 **`code_type` เป็น `varchar(20)`** (ขณะที่ `common_code_type.code_type` เป็น `varchar(50)`) — "
            "`SGI_APPROVE_LIMIT` ยาว 19 ตัว **เหลือที่ว่างแค่ 1 ตัวอักษร** · ตั้งชื่อ `code_type` ใหม่ห้ามเกิน 20",
            "ระบบเดิม**ไม่มี POST/PUT/DELETE ของ `common_code`** (module `common` มีแต่ GET) — "
            "SGI จะเขียนลง lookup กลางที่ทุกโมดูลใช้ร่วม ต้องทำผ่าน migration script ที่ review ได้ ไม่ใช่หน้าจอ",
            "SGI **อ่านอย่างเดียวในเวลาปกติ** — แก้ค่าทำที่ระบบ SBP เดิม (หน้าจอ Global Config ของ SGI ถูกลบไปแล้ว 2026-08-06) · "
            "การเขียนเกิดเฉพาะตอน **seed/cutover** เท่านั้น",
        ]),
        *implementation_rule_blocks(
            "5.6 ข้อกำหนดด้าน integration ที่ต้องยึด",
            [
                ["อีเมลแจ้งสถานะ", "workflow ให้ **เลข template** ผ่าน `workflow_route.email_id` แล้ว **SGI เรียก `sendEmail()` ของ `@gosoft-sbp/email-lib` เอง** พร้อม `mailTo` / `mailCc` / `param`", "`triggerEvent` ของ engine ไม่มีฟิลด์ `mailTo`/`mailCc`/`param` ที่ `sendEmail` บังคับ (ปิด 2026-08-14)"],
                ["ไฟล์แนบ", "`sgi_document_attachments` เก็บ **metadata ฝั่ง SGI** แล้วฝากไฟล์กับ service S3 ของระบบเดิม (`upload-file-aws` / `download-file-aws`) — ไม่เขียน storage layer เอง", "`upload_general` ของระบบเดิมไม่มีคอลัมน์ที่เอกสารต้องใช้ (ปิด 2026-08-24)"],
                ["ที่อยู่ของโค้ด SGI", "เป็น **โมดูลใน `srm-sps-spsap-store-backend` เดิม** ไม่แยก backend ใหม่", "ได้ guard / interceptor / response envelope ของ store-backend มาใช้ทันที (ปิด 2026-08-21)"],
                ["`sgi_interface_transactions`", "ใช้ DDL ตามที่ประกาศไว้ในเอกสาร `LLDD-Database` — 1 แถวต่อ 1 record ที่รับส่งกับระบบภายนอก พร้อมสถานะ สถานะการรับส่ง (ขาออกจบที่ outbox_status = CONFIRMED)", "เป็นตารางของ SGI เอง (`integration_log` ของระบบเดิมเก็บ payload ต่อ call ไม่ใช่ระดับ record)"],
            ],
        ),
    ]


def workflow_engine_definition_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.0 ทำไมเอกสารฉบับนี้ต้องปิดเป็นฉบับแรก"),
        p(
            "เอกสารฉบับนี้ **ไม่มี endpoint ของตัวเอง** — ผลลัพธ์คือชุดนิยาม state/status/route/part ที่เอกสารอื่น "
            "เอาไปใช้ต่อ จึงต้องจบก่อนผู้บริโภคทั้งหมดเริ่ม (ปรับลำดับ 2026-08-10: เดิมถูกจัดไว้ท้ายกลุ่ม API "
            "ทำให้ `BE-API-Document-Workflow-Actions` และ `BE-API-Workflow-Instances` เริ่มก่อนเอกสารที่นิยาม "
            "สิ่งที่มันต้องใช้)"
        ),
        table(
            ["เอกสารที่รอ", "รออะไรจากฉบับนี้"],
            [
                ["BE-API-Document-Workflow-Actions", "รหัส event ต่อปุ่ม · route ของแต่ละ state · เงื่อนไขแตกสายตามวงเงิน"],
                ["BE-API-Workflow-Instances", "โครง version/state/status ที่จะ query และรูปแบบ payload ของ engine"],
                ["BE-Job-8b-StartInternalWorkflow", "**เรียก `POST /sgi/workflow/instances` ด้วย service token** — ไม่เรียก engine เอง (มติ 2026-09-09)"],
                ["FE-Document-Detail (5 ฉบับ role)", "`workflow_part_display` READ/WRITE ต่อ state ที่คุมการแสดงผลรายส่วน"],
            ],
        ),
        h(2, "5.1 Engine คือของกลาง 13 ตาราง ใน schema `sps_store`"),
        p(
            "`@srm/glb-workflow` เป็น library กลางที่ทุกระบบใน SBP platform import ไปใช้ "
            "(ต้นฉบับ: `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` v1.2 ลงวันที่ 29/04/2026) · "
            "SGI ใช้ engine ตัวนี้ตามมติ 2026-08-06 ที่ตัดตาราง workflow ของตัวเองทิ้งทั้งหมด"
        ),
        p(
            "**ตัวเลขที่เอกสารรุ่นก่อนเขียนผิด 2 จุด (แก้แล้ว 2026-08-07):** (1) engine มี **13 ตาราง ไม่ใช่ 10** · "
            "(2) engine ตัวที่ใช้งานจริงอยู่ schema **`sps_store` ไม่ใช่ `sps_auth`** — ทั้งสอง schema มีครบ 13 ตาราง"
            "เหมือนกันแต่เป็นคนละชุดและคนละเวอร์ชัน (`workflow_state` ของ `sps_auth` มี 3 คอลัมน์ · ของ `sps_store` "
            "มี 4 คอลัมน์) · `sps_auth.workflow_transaction` มีแค่ 55 แถว (route 41 · state 10) ซึ่งเป็นชุดของ "
            "auth-backend คนละเรื่องกัน"
        ),
        table(
            ["กลุ่ม", "ตาราง", "หน้าที่"],
            [
                ["นิยาม flow (config)", "workflow · workflow_version · workflow_state · workflow_status · workflow_event · workflow_route", "ตั้งครั้งเดียวต่อระบบ · `workflow_version.url_main` / `url_param_mapping` ทำให้ inbox กลางลิงก์กลับหน้าเอกสารของ SGI ได้"],
                ["กลุ่มผู้อนุมัติ", "workflow_group · workflow_group_map", "`map_table` ว่าง = เทียบกับ field ของ user ตรง ๆ · ระบุ map_table = ต้องเป็น view ที่ where ด้วย user_id/group_id ได้"],
                ["ข้อมูลรันไทม์", "workflow_transaction · workflow_history · workflow_approver", "19,327 / 38,010 / 96,542 แถวใน sps_store (ตรวจ 2026-08-07)"],
                ["คุมการแสดงผล", "workflow_part · workflow_part_display", "`part_display_type` = READ / WRITE ต่อ state — คืนมากับ getPermissionEvents"],
            ],
        ),
        h(2, "5.2 ความเสี่ยงที่ต้องคุยกับทีมเจ้าของ library"),
        table(
            ["ความเสี่ยง", "ข้อเท็จจริงที่ตรวจแล้ว", "ผลกระทบต่อ SGI", "สิ่งที่ต้องทำ"],
            [
                [
                    "`sps_store.workflow_transaction` ไม่มี PK และไม่มี index เลย",
                    "มี 19,327 แถวแต่ schema dump ไม่พบ PK/index ใด ๆ (ตารางชื่อเดียวกันใน `sps_auth` มี PK `transaction_id` ปกติ) · `workflow_state` / `workflow_event` / `workflow_part_display` ของ `sps_store` ก็ไม่มี PK เช่นกัน",
                    "ทุกครั้งที่เปิดเอกสารหรือกด action ต้อง seq-scan 19,327 แถวเพื่อหา `reference_id` · ไม่มีอะไรกัน initialize ซ้ำแม้ระดับ application · จะแย่ลงเมื่อ SGI เพิ่มอีกราวหมื่นแถวต่อปี",
                    "**ห้ามแก้ schema ของ `@srm/glb-workflow`** — กันซ้ำและเก็บ mapping ที่ฝั่ง SGI เอง แล้วประเมินต้นทุน query ทุกเส้นที่อ้างตารางนี้",
                ],
                [
                    "`part_display_type` สะกดว่า `WRTIE` ในไฟล์ต้นฉบับ",
                    "สะกดผิดทุกแถวของชีต `sample data`",
                    "ถ้า SGI เขียนค่า `WRITE` แล้ว engine เทียบกับ `WRTIE` การแสดงผลจะเพี้ยนทั้งหน้า",
                    "ยืนยันค่าจริงในระบบกับทีม library ก่อนลงทะเบียน part",
                ],
                [
                    "`workflow_route` มี 2 นิยามในไฟล์เดียวกัน",
                    "ชีต `sample data` มีคอลัมน์ `group_id` แต่ entity ที่แนบมาใช้ `approver` และตั้งชื่อ property ว่า `approverRoleId`",
                    "เขียนโค้ดผูกผู้อนุมัติผิดคอลัมน์",
                    "ยืนยัน schema จริงของ route กับทีม library",
                ],
                [
                    "ไม่มี API ถอน/แก้ผู้อนุมัติล่วงหน้า",
                    "มีแต่ `addPreApprover`",
                    "เคสเปลี่ยนตัวผู้อนุมัติ (ลาออก/รักษาการ) ทำไม่ได้ผ่าน library",
                    "ถามทีม library ว่าจะเพิ่มให้หรือให้ SGI แก้ตารางตรง",
                ],
            ],
        ),
        h(2, "5.3 API ของ engine — 8 function (ยึด LLDD ของ lib · ยืนยันแล้ว 2026-08-14)"),
        p(
            "แหล่งความจริงคือชีต `Detail` ของ `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` "
            "ซึ่งเป็น **เอกสารของ lib เอง** · ชื่อที่เคยนับว่าขัดกันไม่ใช่ชื่อ API: "
            "*Trigger Event* เป็น**ชื่อหัวข้อของขั้นตอนภายใน** `eventWorkflow` ในชีต 2 "
            "ส่วน `TriggerEventUseCase` / `AddPreparedApproverUseCase` / `GetPendingFlowUseCase` "
            "เป็น **UseCase class ที่ store-backend ห่อไว้ใช้เอง** ไม่ใช่ API ของ lib"
        ),
        table(
            ["#", "function", "พารามิเตอร์ (ชีต Detail)", "SGI ใช้ที่ไหน"],
            [
                ["1", "`initializeWorkflow`", "version, userId, referenceId",
                 "เปิด flow ให้เอกสารใหม่ (Job 8b · `POST /sgi/workflow/instances`)"],
                ["2", "`eventWorkflow`",
                 "version, referenceId, event, eventParam, remark, userId **+ userData · userFullname · nextApproverId** "
                 "(ส่วนขยาย 29/04 · 20/05 · 16/06/2026 — ยึดชุดนี้เวลาเขียนโค้ด)",
                 "`POST /sgi/document/{docNo}/actions`"],
                ["3", "`getPermissionEvents`", "version, referenceId, userData",
                 "ปุ่ม/ผลพิจารณาที่ user กดได้ในหน้าเอกสาร"],
                ["4", "`getHistory`", "version, referenceId", "`GET /sgi/document/{docNo}/timeline`"],
                ["5", "`getTransaction`", "version, referenceId", "สถานะ + ผู้ถืองานปัจจุบันของเอกสาร"],
                ["6", "`getPendingFlowByUser`", "userData",
                 "**หน้า เอกสาร → รอดำเนินการ** + reminder รายสัปดาห์"],
                ["7", "`getWorkflowsByUser`", "userData",
                 "**หน้า เอกสาร → ที่เกี่ยวข้อง** (รวมที่ยังไม่ถึงคิวและที่อนุมัติไปแล้ว)"],
                ["8", "`addPreApprover`", "version, userId, referenceId, state_id, approver, seq",
                 "ตั้งผู้อนุมัติล่วงหน้าของขั้นถัดไป"],
            ],
        ),
        h(2, "5.4 นิยาม flow ของ SGI ที่ต้อง register"),
        table(
            ["state", "ชื่อสถานะเอกสาร", "event ที่ทำได้", "ปลายทาง"],
            [
                ["06", "รอฝ่าย SBP DSA ดำเนินการ", "submit (ส่งเจ้าหน้าที่ SBP DSA) · reject (เห็นควรไม่ชดเชย) · cancel (หยุดชดเชย) · submit (ส่งหน่วยงานส่งเสริมธุรกิจ SBP)", "08 หรือ 01 หรือจบ flow"],
                ["08", "รอเจ้าหน้าที่ SBP DSA ดำเนินการ", "submit (คำนวณเงินชดเชยเรียบร้อย) — **ปุ่มเดียวของขั้นนี้ (มติ 2026-09-01)**", "**06** (ส่งยอดกลับฝ่าย SBP DSA · เดิม 01)"],
                ["01", "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ", "approve (เห็นควรชดเชย) · reject (เห็นควรไม่ชดเชย → จบ flow ทันที) · sendback (ฝ่าย SBP DSA ดำเนินการ)", "02 · จบ flow · 06"],
                ["02", "รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ", "approve (เห็นควรชดเชย) · reject (เห็นควรไม่ชดเชย → จบ flow ทันที) · sendback (ส่งกลับฝ่าย SBP DSA)", "จบ flow เมื่อยอด < 100,000 · ไป 03 เมื่อ ≥ 100,000 · **06** (มติ 2026-09-01 · เดิม 01)"],
                ["03", "รอผู้บริหารสำนักบริหาร SBP ดำเนินการ", "approve (เห็นควรชดเชย) · reject (เห็นควรไม่ชดเชย → จบ flow ทันที · มติ 2026-09-02) · sendback (ส่งกลับฝ่าย SBP DSA)", "จบ flow · **06** (มติ 2026-09-01 · เดิม 02)"],
            ],
        ),
        code(
            """-- ⚠️ ตัวอย่างนี้แสดง "รูปแบบ" ของ condition_json เท่านั้น — วงเงินอนุมัติของจริงเก็บที่ common_code
-- วงเงินเก็บที่ `common_code` (code_type = SGI_APPROVE_LIMIT) ที่เดียว แล้ว "อ่านทุกครั้ง ห้าม hardcode"
-- ตามที่ LLDD-BE-Integration-SBP-Platform / LLDD-Database ระบุไว้ · **ห้ามเก็บสองที่**
-- วิธีที่ใช้: SGI เทียบยอดกับ common_code เอง แล้วส่งผลลัพธ์ให้ engine เลือก route
--   เช่น eventParam = {"limitTier":"GM"|"AVP"} โดยไม่ฝังตัวเลขวงเงินลง condition_json
--
-- ด้านล่างเป็นรูปแบบ condition_json ที่ engine รองรับ (แสดงไว้เพื่อความครบถ้วนของนิยาม route):
-- seq = ลำดับที่ engine ใช้ไล่ตรวจ condition_json (ตัวแรกที่ตรงชนะ)
-- ตัวเลข 100000 ด้านล่างเป็นค่า **ตัวอย่าง** ของเกณฑ์เดียว (มติ 2026-08-18) ไม่ใช่ค่าที่ตกลงให้ hardcode
INSERT INTO sps_store.workflow_route
  (version_id, from_state_id, event, to_state_id, to_status_id, seq, condition_json, approver_type, group_id)
VALUES
  (:v, :state_02, 'approve', :state_end, :status_done, 1,
   '{"field":"amount","operator":"<","value":100000}', 'group', :group_none),
  (:v, :state_02, 'approve', :state_03,  :status_wait_avp, 2,
   '{"field":"amount","operator":">=","value":100000}', 'group', :group_avp);
-- ✅ เกณฑ์เดียวจึงไม่มีช่องโหว่ปลายบน: ทุกยอดตั้งแต่ 100,000 ขึ้นไปวิ่งเข้า AVP เส้นเดียว""",
            "sql",
        ),
        h(2, "5.5 `workflow_part_display` ทับซ้อนกับกลไกของ prototype"),
        p(
            "หน้า `k2-document.html` ของ prototype คุมสิทธิ์แก้ไขรายส่วนด้วย `data-editrole` / `data-roleonly` / "
            "`.edit-only` ฝั่ง client เอง · engine มีกลไกเดียวกันให้อยู่แล้วผ่าน `workflow_part` + "
            "`workflow_part_display` ที่คืนมาใน `display[]` ของ `getPermissionEvents` "
            "(รูปแบบ `{partId, partName, stateId, partDisplayType, partSeq}`)"
        ),
        p(
            "**SGI ไม่ใช้กลไกนี้** — บันทึกไว้เป็นข้อสังเกตว่า engine รองรับการลงทะเบียน part แล้วให้ FE อ่าน "
            "`display[]` แทนการ hardcode สิทธิ์ต่อ role หรือไม่ · ถ้าเลือกทางนี้จะกระทบ "
            "`LLDD-FE-Document-Detail` + role pack 5 ฉบับ ที่ปัจจุบันอ่าน `visibleSections`/`editableSections` "
            f"จาก API ของ SGI เอง · ทางเลือกเต็มอยู่ที่ `{DECISION_DOC}`"
        ),
        *implementation_rule_blocks(
            "5.6 ข้อกำหนดที่ต้องยึดตอนต่อกับ engine",
            [
                ["`reference_id`", "ส่ง **`sgi_compensation_documents.id`** (surrogate) เป็น string ทุกครั้งที่เรียก engine", "`reference_id` เป็น varchar(255) และระบบเดิมส่ง surrogate id ทุกจุด (ปิด 2026-08-17)"],
                ["ตารางของ engine", "**ห้ามแก้ schema และห้าม INSERT/UPDATE `sps_store.workflow_*` ตรง** — SGI ต้องกันซ้ำระดับ application ก่อนเรียก `initializeWorkflow()` และประเมินต้นทุน query ที่อ้าง `workflow_transaction` เอง", "ตารางเป็นของ `@srm/glb-workflow` · `workflow_transaction` มี 19,327 แถวโดยไม่มี PK/index (ตรวจฐานจริง 2026-08-07) ทุกเงื่อนไขจึงเป็น seq-scan"],
                ["วงเงินอนุมัติ", "เก็บที่ **`common_code` (`code_type = SGI_APPROVE_LIMIT`) ที่เดียว** — ห้ามเก็บซ้ำใน `workflow_route.condition_json`", "เป็น data ไม่ hardcode · เก็บสองที่แล้วแก้ไม่ครบคือความเสี่ยงหลัก (`database.md` §วงเงินอนุมัติ)"],
                ["อีเมล", "SGI เรียก `sendEmail()` เอง โดยใช้เลข template จาก `workflow_route.email_id`", "`triggerEvent` ไม่มี `mailTo`/`param` (ปิด 2026-08-14)"],
                ["ผู้อนุมัติของแต่ละขั้น", "ผูกด้วย **`addPreApprover()` รายคน** ตอนเปิด/เดิน flow — ไม่ใช้ `workflow_group_map`", "ตรงกับที่ Job 8b และทุก endpoint ของ SGI ทำจริง และรองรับกติกา auto-assign เจ้าของงานคนเดิม"],
                ["การคุมสิทธิ์แสดง/แก้รายส่วนของหน้าเอกสาร", "ใช้ **`visibleSections` / `editableSections`** ที่ API ของ SGI คืนมา — ไม่ใช้ `workflow_part_display` ของ engine", "role pack 5 ฉบับและ `data-editrole` ของ prototype ยึดกลไกนี้ทั้งหมด"],
            ],
        ),
    ]


def workflow_action_transition_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Canonical Workflow Transition Matrix"),
        p("BE ต้องคำนวณ transition จาก currentSection, result และ totalCompensationAmount ภายใน transaction; FE ส่งเพียง result/comment และห้ามส่ง nextSection เอง"),
        table(["Current", "Result / condition", "statusCode", "nextSection", "Task effect"], [
            ["06", "ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ (เส้นทางปกติ — ให้คำนวณยอดก่อน)", "08", "08", "close 06; open 08"],
            ["06", "ส่งหน่วยงานส่งเสริมธุรกิจ SBP (SDD GI · **เส้นทางข้ามขั้น 08**)", "01", "01", "close 06; open 01"],
            ["06", "เห็นควรไม่ชดเชย หรือ หยุดชดเชยประกันรายได้", "99", "null", "close 06; complete instance"],
            ["08", "คำนวณเงินชดเชยเรียบร้อย (**ปุ่มเดียวของขั้น 08** · มติ 2026-09-01 — ส่งยอดกลับให้ 06 ตัดสินใจส่งต่อ)", "06", "06", "close 08; reopen 06"],
            ["01", "เห็นควรชดเชย", "02", "02", "close 01; open 02"],
            ["01", "เห็นควรไม่ชดเชย (SDD GI — **จบ flow ทันที** ไม่ตีกลับให้ 06)", "99", "null", "close 01; complete instance"],
            ["02", "เห็นควรชดเชย และ totalCompensationAmount >= 100,000 (มติ 2026-08-18)", "03", "03", "close 02; open 03"],
            ["02", "เห็นควรชดเชย และ totalCompensationAmount < 100,000 (มติ 2026-08-18)", "99", "null", "close 02; complete instance"],
            ["02", "เห็นควรไม่ชดเชย (SDD GI — **จบ flow ทันที** ไม่ตีกลับเป็นทอด ๆ)", "99", "null", "close 02; complete instance"],
            ["03", "เห็นควรชดเชย", "99", "null", "close 03; complete instance"],
            ["03", "เห็นควรไม่ชดเชย (มติ 2026-09-02 — **จบ flow ทันที** เหมือน 01/02 · เดิมตีกลับ 06)", "99", "null", "close 03; complete instance"],
            ["ทุก section ที่รองรับ", "ส่งกลับฝ่าย SBP DSA", "**06 เสมอ** (มติ 2026-09-01 — เดิม 02→01 · 03→02 · ขั้น 08 ตัดปุ่มส่งกลับทิ้งเพราะปุ่มเดียวที่เหลือก็กลับ 06 อยู่แล้ว)", "06", "close current; reopen 06 with new task id"],
        ]),
        h(2, "5.1c แจ้ง STA เมื่อเปิดพิจารณาใหม่ (reflow) — มติ 2026-09-01"),
        p("เมื่อ **ฝ่าย SBP DSA (section 06)** กด action บนเอกสารที่**จบไปแล้ว** (statusCode 99) ด้วยผล **เห็นควรไม่ชดเชย** หรือ "
          "**หยุดชดเชยประกันรายได้** เพื่อเปิดรอบพิจารณาใหม่ endpoint นี้ต้อง **publish message `sgi_reflow`** ให้ระบบ STA ด้วย — "
          "ถ้าไม่แจ้ง STA จะปิดงวดนั้นค้างไว้และยอดชดเชยรอบใหม่จะไม่ถูกคำนวณ · "
          "สัญญาข้อความเต็มดู `STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md`"),
        table(["รายการ", "ข้อกำหนดที่ต้องทำตาม"], [
            ["ช่องทาง", "RabbitMQ exchange `sgi.interface` (topic · durable) — ชื่อ exchange อ่านจาก backend config `SGI_MQ_EXCHANGE`"],
            ["ชื่อชุดข้อมูล", "`dataName = \"sgi_reflow\"` · `sender = \"SGI\"` · โครงสร้างฟิลด์ชุดเดียวกับ `sgi_impact_store`"],
            ["ค่าที่บังคับ", "`compensate_status = \"R\"` ทุกรายการ · `stmt_year_month` ว่างเสมอ (ยังไม่ทราบงวด statement ใหม่)"],
            ["จำนวนรายการ", "**1 รายการต่อ 1 งวด** (`compensate_year_month`) ที่ต้อง reflow — ส่งครบทุกงวดที่เอกสารเดิมครอบคลุม"],
            ["Transaction boundary", "insert แถว outbox `sgi_interface_transactions` (**`data_name = 'SGI_REFLOW'`** · `direction = 'OUT'` · `status = 'READY'`) **ใน transaction เดียวกับการเปิดรอบพิจารณาใหม่** แล้ว publish นอก transaction · publish สำเร็จตั้ง `status = 'SENT'` + `outbox_status = 'PUBLISHED'` · **ได้ publisher confirm จาก broker จึงตั้ง `outbox_status = 'CONFIRMED'` + `status = 'COMPLETED'`** (ตรงกับโดเมนใน `LLDD-Database` · มติ 2026-09-08 ข้อ 2.13 — ค้างที่ `SENT` แปลว่ายังไม่ confirm และ Job 10 จะเตือน) <br>⚠️ `SGI_REFLOW` เพิ่งถูกเพิ่มเข้า `CHECK` ของ `data_name` เมื่อ 2026-09-02 — ก่อนหน้านั้น INSERT นี้จะถูก constraint ปฏิเสธ"],
            ["Idempotency", "`message_id` = `sgi_interface_transactions.id` · กดเปิดพิจารณาใหม่ซ้ำบนเอกสารเดิมต้องไม่เกิดแถว outbox ที่สอง"],
        ]),
        h(2, "5.1b Auto-assign เจ้าของงานคนเดิม (SDD สไลด์ 46 · 48 · 64)"),
        p("สองปุ่มที่จบเอกสารเหมือนกันแต่พฤติกรรมหน้ารายการตรงข้ามกัน — BE ต้อง implement แยกกันให้ชัด ห้ามรวมเป็นเส้นเดียว"),
        table(["ปุ่มที่กดที่ขั้น 06", "เดือนที่กด", "เดือนถัดไป", "ผู้ดำเนินการ (เจ้าของงาน)"], [
            ["เห็นควรไม่ชดเชยรายได้", "ปิดเอกสาร (99) และ GET /sgi/document/tasks ของ 06 ต้อง **ไม่คืน** เอกสารนี้ในเดือนนั้น", "ระบบตั้งงานรอบเดือนถัดไปของร้านเดิมอัตโนมัติ", "**คนเดิม** ที่พิจารณาเอกสารรอบก่อนในขั้นเดียวกัน"],
            ["หยุดชดเชยประกันรายได้", "ปิดเอกสาร (99) แต่ GET /sgi/document/tasks ของ 06 **ต้องคืนทันที** พร้อม stoppedReopenable=true", "ไม่มีการตั้งงานอัตโนมัติ", "ฝ่าย SBP DSA (06)"],
            ["เคสต่อเนื่อง (ไม่ใช่ปุ่ม — เงื่อนไขของงานรอบถัดไป)", "ระบบสร้างงานให้เอง ไม่ต้องแจกงานด้วยมือ", "เหมือนกันทุกเดือนที่ยังต่อเนื่อง", "**คนเดิม** — เจ้าหน้าที่ SBP DSA รอบก่อนหน้า"],
        ]),
        p("**วิธี resolve เจ้าของงานคนเดิม** — ไม่มีคอลัมน์ assignee ในตารางของ SGI (ตาราง workflow_tasks ถูกตัดออกจากโครง 21 ตารางแล้ว) ผู้รับผิดชอบเป็นข้อมูลของ engine"),
        table(["ขั้น", "การทำงาน"], [
            ["1", "หาเอกสารรอบก่อนหน้าของร้านเดียวกัน (impacted_store_code เดิม · round_no/loop_no ก่อนหน้า)"],
            ["2", "อ่าน sgi_consideration_logs แถวล่าสุดของเอกสารนั้นที่ section_code = ขั้นที่จะมอบหมาย -> consider_by (คอลัมน์ผู้ดำเนินการ · อ้าง business_user ของระบบเดิม)"],
            ["3", "ผูกเป็นผู้รับผิดชอบผ่าน addPreApprover(versionId, referenceId, stateId, approver, seq) ของ @srm/glb-workflow"],
            ["4", "Fallback: รอบก่อนไม่เคยผ่านขั้นนั้น หรือพนักงานไม่อยู่ในกลุ่มแล้ว -> มอบหมายตาม group ของ auth-backend ตามปกติ"],
            ["5", "พนักงานลาออกยังต้องเปิด SR เพื่อแก้ชื่อผู้ดำเนินการ (ข้อจำกัดที่ SDD สไลด์ 48 ระบุ ไม่แก้ในเฟสนี้)"],
        ]),
        code("""-- resolve เจ้าของงานคนเดิมของขั้น :sectionCode จากเอกสารรอบก่อนของร้านเดียวกัน
SELECT cl.consider_by
FROM sgi_compensation_documents d
JOIN sgi_consideration_logs cl ON cl.doc_no = d.doc_no
WHERE d.impacted_store_code = :impactedStoreCode
  AND d.doc_no <> :currentDocNo
  AND cl.section_code = :sectionCode
ORDER BY d.round_no DESC, d.loop_no DESC, cl.action_datetime DESC
LIMIT 1;
-- ได้ค่าแล้วส่งเข้า addPreApprover(...) ตอนเปิดงานรอบใหม่ ห้าม INSERT sps_store.workflow_approver เอง
-- NULL -> fallback group ของ auth-backend""", "sql"),
        h(2, "5.2 Action Response Type"),
        table(["Field", "Type", "Required", "Rule"], [
            ["statusCode", "enum 06|08|01|02|03|99", "Yes", "ค่าหลัง commit; 99 = เสร็จสิ้น"],
            ["nextSection", "enum 06|08|01|02|03 | null", "Yes", "null เมื่อ workflow จบ"],
            ["message", "string", "Yes", "ข้อความผล mutation สำหรับแสดงผู้ใช้"],
        ]),
        *implementation_rule_blocks(
            "5.3 ข้อกำหนดที่ต้องยึดสำหรับ endpoint ของเอกสารนี้",
            [
                ["แหล่งข้อมูลของ `GET /sgi/document/{docNo}/timeline`", "อ่าน **`sgi_consideration_logs` ของ SGI** เป็น timeline เต็ม (ผูก `transaction_id` ของ engine) — ไม่เรียก `getHistory()` ของ engine", "engine ไม่มีรหัสผลพิจารณาและไฟล์แนบใน history (ปิด 2026-08-24)"],
                ["`referenceId` ที่ส่งเข้า engine", "ส่ง **`sgi_compensation_documents.id`** (surrogate) เป็น string", "`reference_id` เป็น varchar(255) · ระบบเดิมส่ง surrogate id ทุกจุด (ปิด 2026-08-17)"],
                ["ตาราง `sps_store.workflow_transaction`", "**ห้ามแก้ schema ของ library** — กันซ้ำระดับ application และประเมินต้นทุน query ก่อนเปิดใช้ทุกเส้นที่อ้างตารางนี้", "19,327 แถวโดยไม่มี PK/index (ตรวจฐานจริง 2026-08-07) ทุก action จึงเป็น seq-scan"],
                ["อีเมลหลังเปลี่ยนสถานะ", "SGI เรียก `sendEmail()` ของ email-lib เอง โดยใช้ `emailId` จาก `workflow_route.email_id` ของ route ที่เพิ่งเดิน", "`triggerEvent` ของ engine ไม่มี `mailTo`/`mailCc`/`param` (ปิด 2026-08-14)"],
            ],
        ),
    ]


def master_config_screen_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Screen Boundary and Route Matrix"),
        p("หัวข้อนี้ประกอบด้วย **2 หน้าจออิสระ** แต่ละหน้ามี route, state, validation และ endpoint ของตนเอง "
          "ห้าม implement เป็น form/table เดียวที่สลับชนิดข้อมูลด้วยเงื่อนไขใน component · "
          "SCR-08 ผู้ปฏิบัติงาน และ SCR-10 สิทธิ์เมนู **ถูกตัดออก 2026-08-05** (ใช้ของระบบ SBP เดิม)"),
        table(["Screen", "Route / Component", "Primary model", "Main operations"], [
            ["SCR-09 ปัจจัยภายนอก", "/admin/external-factors / ExternalFactorPage", "ExternalFactor",
             "list, add, edit, delete, duplicate-code guard"],
            ["รายชื่อร้านคู่แข่ง (master แบรนด์)", "/admin/competitors / CompetitorPage", "Competitor",
             "list, add, edit, delete, duplicate-code guard, active toggle"],
            ["~~SCR-08 ผู้ปฏิบัติงาน~~ **ตัด 2026-08-05**", "ไม่มีหน้าจอใน SGI", "-",
             "ใช้ group + scope ของ auth-backend และ prepared approver ของ @srm/glb-workflow · "
             "จัดการที่หน้า /setting/manage-user-rights ของระบบเดิม — **ไม่มี field/endpoint ให้ implement**"],
            ["~~SCR-10 สิทธิ์เมนู~~ **ตัด 2026-08-05**", "ไม่มีหน้าจอใน SGI", "-",
             "สิทธิ์เมนูจัดการที่หน้า /setting/manage-user-rights ของระบบเดิม · "
             "SGI อ่านผ่าน header x-user-permissions จาก BFF — **ไม่มี field/endpoint ให้ implement**"],
        ]),
        h(2, "5.2 SCR-09 External Factor"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["factorCode", "string", "required; unique; immutable after create", "uppercase and trim before submit"],
            ["factorName", "string", "required; 1..200 chars", "Thai UTF-8 supported"],
            ["description", "string | null", "optional; max 1000 chars", "multiline editor"],
            ["active", "boolean", "required", "inactive rows remain visible under filter แต่ไม่ขึ้นใน dropdown ของหน้าเอกสาร"],
        ]),
        p("⚠️ **ไม่มีฟิลด์ `reason`** — ยกเลิกระบบ audit ของ master ทั้งหมด 2026-08-07 · "
          "mutation ไม่ต้องส่ง `reason` และไม่มี audit dialog ก่อน submit"),
        h(2, "5.3 Competitor Brand Master"),
        table(["Field", "Type", "Required / Rule", "UI behavior"], [
            ["competitorCode", "string(30)", "required; unique; immutable after create", "รหัส 01-11 ของ master เดิม · trim ก่อน submit"],
            ["nameTh", "string(200)", "required", "ชื่อแบรนด์ภาษาไทย — แสดงใน dropdown ร้านคู่แข่งของหน้าเอกสาร"],
            ["nameEn", "string(200)", "required", "ชื่อแบรนด์ภาษาอังกฤษ (ระบบเดิมเก็บทั้งสองภาษา)"],
            ["remark", "string(500) | null", "optional", "คอลัมน์ รายละเอียดเพิ่มเติม ของหน้า k2-competitors.html"],
            ["active", "boolean", "required", "ปิด active แทนการลบเมื่อถูกอ้างใน sgi_document_competitors แล้ว"],
        ]),
        p("**คนละระดับกับ `sgi_document_competitors`** ซึ่งเก็บคู่แข่ง *รายสาขา* ที่ import จาก ALLMAP "
          "พร้อมรหัสของตัวเอง (เช่น `4832`, `TD58_08`) — หน้านี้ดูแลเฉพาะ **แบรนด์**"),
        h(2, "5.6 Screen-level Acceptance"),
        bullets([
            "แต่ละหน้ามี route/component/state แยกและสามารถ test/release แยกกันได้",
            "mutation refresh เฉพาะ resource ที่เปลี่ยน — **ไม่ส่ง reason และไม่มี audit dialog** (ยกเลิก audit ของ master 2026-08-07)",
            "SCR-09 กัน factorCode ซ้ำทั้ง client response handling และ BE error (409 CODE_DUPLICATE)",
            "หน้าคู่แข่งกัน competitorCode ซ้ำ และบังคับ nameTh + nameEn ครบทั้งคู่",
            "ลบรายการที่ถูกอ้างในเอกสารแล้วต้องได้ 409 และ UI ต้องเสนอให้ปิด active แทน",
            "(SCR-08 และ SCR-10 ตัดออก 2026-08-05 — ไม่มีเกณฑ์ตรวจรับสำหรับสองหน้านี้)",
        ]),
    ]


def testing_delivery_blocks(topic: Topic) -> list[dict[str, Any]]:
    return [
        h(1, "1. Overview"),
        table(["รายการ", "รายละเอียด"], [
            ["Track", topic.track], ["Estimate", estimate_cell(topic)], ["Owner", topic.owner],
            target_repo_row(topic),
            ["Document type", "FE verification and release handover specification; not an application screen"],
            ["Objective", topic.objective],
        ]),
        *related_documents_blocks(topic),
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
            ["FE-REPORT", "required status filter, 14 columns (SDD slide 60), totals, Excel parity", "known report fixture and expected aggregate", "query snapshot, row count, totals and exported checksum"],
            ["FE-MASTER", "SCR-09 ปัจจัยภายนอก + รายชื่อคู่แข่ง (SCR-08/10/11 และ email template ตัดออกแล้ว)", "admin role and reversible test data", "before/after values"],
            ["FE-BATCH", "job selection, editable params, locked params, run history", "job metadata/run fixtures", "request/response capture and UI state"],
            ["FE-RESP", "desktop 1440, tablet 768, mobile 390", "latest supported browsers", "page checklist with overflow/modal/navigation result"],
        ]),
        h(1, "4. Environment and Fixture Contract"),
        table(["Item", "Required content", "Control"], [
            ["Build identity", "commit SHA, build number, deploy timestamp", "freeze before regression"],
            ["API identity", "base URL and contract version", "no production credentials in evidence"],
            ["Role users", "one account per tested RBAC role/profile", "masked identifiers in shared evidence"],
            ["Document fixtures", "docNo per current section plus <100,000 (GM) and >=100,000 (AVP) cases per มติ 2026-08-18", "resettable or uniquely generated"],
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
        p(
            "🔴 **หัวข้อ 5.1-5.6 ต่อจากนี้เป็นดีไซน์ *ก่อน* มติ 2026-08-06 — ยังไม่อยู่ในขอบเขตที่ประเมินไว้ 8 ชั่วโมง** · "
            "ของจริงที่ต้องทำคือ **iframe ของหน้าสร้างเอกสารระบบ FS ตรง ๆ + หมายเหตุ 4 ขั้นตอนใต้ iframe** (ดูโครงไฟล์ในหัวข้อ 8) · "
            "เก็บ SBP mirror form + FS bridge ไว้เป็น **ทางเลือกสำรอง** เผื่อ FS ไม่ยอมให้ฝัง iframe หรือ origin ไม่ผ่าน — "
            "ถ้าจะทำจริงต้องตั้งงบใหม่ ไม่ใช่ 6 ชม. · error code `FS_BRIDGE_*` ใน `LLDD-BE-API-Common-Contracts` ผูกกับทางเลือกสำรองนี้เท่านั้น"
        ),
        h(2, "5.1 Tab Structure *(ทางเลือกสำรอง — ไม่อยู่ในขอบเขตปัจจุบัน)*"),
        p("หน้า Create Document ต้องมี tab แยกสำหรับสร้างเอกสารจาก FS โดย UI หลักยังเป็น form ของ SBP Mall แต่มี hidden iframe ของ FS เป็น source/submit target จริง"),
        table(
            ["Tab", "Purpose", "Render behavior"],
            [
                ["สร้างเอกสารทั่วไป", "สร้างเอกสาร MANUAL/out-of-condition ผ่าน API ของ SGI", "ใช้ form ปกติและ submit POST /api/v1/sgi/document"],
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
                ["impactMonth", "month/date field ของ FS", "SBP ใช้ ค.ศ. · sync เป็น format ที่ FS field ต้องการ"],
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
            ["Origin setup", "allowlist มาจาก config และ targetOrigin ต้องเป็น origin เฉพาะ ห้ามใช้ `*`", "origin ไม่ตรง → **`FS_BRIDGE_ORIGIN_INVALID`** (catalog กลาง) · ignore ข้อความนั้นและ security log โดยไม่ log payload"],
            ["Ready", "รอ FS_FORM_READY จาก iframe window เดียวกัน", "10s -> FS_BRIDGE_TIMEOUT; retry reload iframe ได้ 1 ครั้ง"],
            ["Schema", "ส่ง discovery และ validate FS_FIELD_SCHEMA", "5s หรือ schema invalid -> **FS_BRIDGE_SCHEMA_INVALID** (ต้องใช้ชื่อ code จาก catalog กลางเท่านั้น — เอกสารรุ่นก่อนตั้งชื่อเองซึ่งไม่มีใน catalog)"],
            ["Value sync", "ส่ง SBP_SET_VALUES พร้อม requestId ใหม่และ debounce 150ms", "FS_ERROR ผูก correlationId กลับ field"],
            ["Submit", "ส่ง SBP_SUBMIT หนึ่งครั้งและ disable submit", "30s -> FS_SUBMIT_TIMEOUT; user retry สร้าง requestId ใหม่"],
            ["Result", "ยอมรับเฉพาะ correlationId ที่ pending และ source/origin ถูกต้อง", "`FS_SUBMIT_RESULT` ไม่สำเร็จ หรือได้ `FS_ERROR` → **`FS_BRIDGE_SUBMIT_FAILED`** (catalog กลาง) · late/duplicate result ถูก ignore แบบ idempotent"],
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
    return False  # ตัดเอกสาร Batch Monitor ออกจากชุดส่งมอบ 2026-08-06


def role_profile_code(profile: dict[str, Any]) -> str:
    return f"P-{profile['code']}"


def implementation_detail_blocks(topic: Topic) -> list[dict[str, Any]]:
    if is_document_detail_role_doc(topic.file):
        return role_doc_implementation_blocks(topic)
    if is_batch_monitor_doc(topic.file):
        return batch_monitor_implementation_blocks()
    if topic.file.startswith("Jobs/"):
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
    if topic.file.startswith("Jobs/"):
        job_no = topic.file.split("LLDD-BE-Job-", 1)[1].split("-", 1)[0]
        legacy = LEGACY_JOB_SOURCES.get(job_no, {})
        rows = [
            ["Input", legacy.get("input", "Job parameters, source files/tables, schedule period, and service-token context defined by this job.")],
            ["Progress", legacy.get("progress", "Create run record, load input, process in chunks, update checkpoint/summary, and expose current state through run history.")],
            ["Output", legacy.get("output", "Target rows/files/interfaces updated according to DB mapping; run history stores status, counts, output reference, and error detail.")],
        ]
        return [
            h(2, "5.9 Input / Progress / Output Contract"),
            table(["Stage", "Contract for implementation"], rows),
        ]

    request_sources = [f"{api.method} {api.path}" for api in topic.apis[:3]]
    db_outputs = [row[0] for row in topic.db_tables if str(row[1]).upper() in {"W", "R/W"}][:3]
    flow_summary = "; ".join(topic.flow[:4]) if topic.flow else "Validate request, apply business rule, persist or render result, and return normalized status."
    rows = [
        # เอกสารที่ไม่มี endpoint ของตัวเอง (สัญญา/งานภายใน) ต้องไม่ได้ประโยคกลาง ๆ ภาษาอังกฤษของหน้าจอ
        ["Input", "; ".join(request_sources) if request_sources
         else "ไม่มี endpoint ของตัวเอง — input คือ request ที่เอกสารอื่นส่งเข้ามา พร้อม user context จาก BFF header (ดู 5.1) และค่ากำหนดกลางที่อ่านจากระบบเดิม"],
        ["Progress", flow_summary],
        ["Output", "; ".join(db_outputs) if db_outputs
         else "ไม่มีตารางที่เอกสารนี้เขียนเอง — output คือ response ตาม envelope กลาง `{success, data}` และร่องรอยที่ตรวจย้อนได้ (log / sgi_consideration_logs / workflow_history ของ engine)"],
    ]
    return [
        h(2, "5.9 Input / Progress / Output Contract"),
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
        p("Line ranges refer to the legacy Java implementation under `batchjob/fcsJar/` (path นับจากราก `sbp-prototype/`). Use these ranges to preserve business behavior while implementing the target Node job."),
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
        ("ให้ formatter กลางสำหรับวันที่ (ค.ศ.), เดือน, เงิน, percent และ docNo โดยไม่เปลี่ยนค่าที่ส่ง API", "payload และ UI ใช้ ค.ศ. เป็นค่าเริ่มต้น (buddhistEra=false); รูปแบบเงิน/docNo ตรงกันทุกหน้า"),
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
    "FE/LLDD-FE-Document-Lists": [
        ("โหลดงานของผู้ใช้จาก /sgi/document/tasks และ map 9 คอลัมน์หลักพร้อม task owner/status", "waiting list แสดง 9 คอลัมน์ตรง type และรักษา leading zero ของรหัสร้าน"),
        ("ค้นหาเอกสารจาก /sgi/document โดยบังคับปีและแสดงเอกสารที่เกี่ยวข้องตาม permission", "ไม่ call API เมื่อไม่มีปี และ empty result ไม่แสดงข้อมูลจาก query ก่อนหน้า"),
        ("serialize docNo/year/status/store filters ลง query state และ restore เมื่อย้อนกลับจาก detail", "Search/Clear/refresh ให้ผลซ้ำได้และ pagination ใช้ filter ชุดเดียวกัน"),
        ("ควบคุม page/size/sort และ row navigation โดยใช้ docNo เป็น stable key · เพิ่มคอลัมน์ checkbox แรกสุดสำหรับเลือกหลายเอกสาร (SDD GI สไลด์ 48) — checkbox ต้อง stopPropagation ไม่ให้ทริกเกอร์ row navigation และ \"เลือกทั้งหมด\" ครอบเฉพาะแถวที่แสดงในหน้านั้น ไม่ใช่ทั้งชุดผลลัพธ์", "เปลี่ยนหน้าไม่ reset filter และเปิด detail ของ row ที่เลือกถูกเลขเอกสาร · เลือกหลายรายการแล้วกด \"ดำเนินการที่เลือก\" ต้องเปิด popup ยืนยันพร้อมรายการเลขที่เอกสารก่อนส่ง และเคลียร์การเลือกหลังส่งสำเร็จ"),
        ("คำนวณ presentation flag จาก salesDataDays < 60 โดยไม่ใช้ waitingDays แทน และ render เอกสารที่จบด้วยผลปฏิเสธทั้ง 2 แบบ — หยุดชดเชยประกันรายได้ (stoppedReopenable=true) และ เห็นควรไม่ชดเชยรายได้ (notCompensated=true) — เฉพาะบทบาท section 06", "แถวผิดปกติเป็นสีแดงพร้อม accessible label เฉพาะเมื่อยอดขายไม่ครบ 60 วัน · บทบาท 06 เห็น 3 กลุ่มในหน้าเดียว (มติ 2026-08-24): (1) รอฝ่าย SBP DSA ดำเนินการ (2) เสร็จสิ้นดำเนินการ + ชิป หยุดชดเชยฯ (3) เสร็จสิ้นดำเนินการ + ชิป เห็นควรไม่ชดเชยฯ · บทบาท 08/01/02/03 ต้องไม่เห็นกลุ่ม (2) และ (3) · ชิปทั้งสองเป็นผลการพิจารณาสุดท้าย ไม่ใช่สถานะที่ 7/8 — สถานะจริงยังเป็น เสร็จสิ้นดำเนินการ ตามชุด 6 ค่า และมีตัวกรองแยก 2 ตัวจาก dropdown สถานะ · กลุ่ม (2) คลิกแล้วเปิดเอกสารในโหมดเปิดพิจารณาใหม่ · หมายเหตุที่มา: กลุ่ม (3) กว้างกว่าตัวอักษรของ SDD สไลด์ 46/64 ที่ให้แสดงเฉพาะรอบเดือนถัดไปในหน้างานค้างของ เจ้าหน้าที่ SBP DSA"),
    ],
    "FE/LLDD-FE-Create-Document": [
        ("หน้าเดียว ไม่มี state ของฟอร์ม — ถือแค่ config URL ของ FS และสถานะโหลด iframe", "ไม่มี draft/unsaved-change guard เพราะไม่มีฟอร์มฝั่ง SBP"),
        ("render กรอบ iframe ของหน้าสร้างเอกสารระบบ FS (สไตล์ `.fs-frame` เดียวกับ k2-document)", "iframe load/error/timeout มี state ชัดเจนและมีข้อความบอกผู้ใช้เมื่อโหลดไม่ขึ้น"),
        ("render การ์ดหมายเหตุ 4 ขั้นตอน **verbatim จากหน้าจอ K2 เดิม** ใต้ iframe (นอกกรอบ)", "ข้อความตรงต้นฉบับทุกตัวอักษร ห้าม paraphrase"),
        ("ลิงก์กลับไปหน้ารายการเอกสารและหน้าเอกสารเมื่อ SBP Statement ส่งข้อมูลกลับแล้ว (~1 วัน)", "ผู้ใช้เข้าใจว่าเอกสารจะมาเองไม่ต้องกดสร้างซ้ำ"),
        ("route guard/เมนูของหน้านี้มาจาก `GET /menus` ของระบบเดิม ไม่ hardcode", "ผู้ใช้ที่ไม่มีสิทธิ์เมนูเข้าหน้านี้ไม่ได้"),
        ("⚠️ *(ทางเลือกสำรอง — ไม่อยู่ในขอบเขต 8 ชม.)* SBP mirror form + FS bridge ตามหัวข้อ 5.1-5.6", "ใช้เมื่อ FS ไม่ยอมให้ฝัง iframe หรือ origin ไม่ผ่าน — ต้องตั้งงบใหม่ก่อนทำ"),
    ],
    "FE/LLDD-FE-Document-Detail": [
        ("โหลดและแสดง docNo, status, impacted store, impact month และ current operator จาก aggregate response", "header refresh หลัง mutation และ status badge resolve จาก statusCode"),
        ("render new-store, competitor และ factor collections ด้วย row key และ typed value mapping", "ข้อมูลอ่าน/แก้/ลบตรง editableSections และ percent รวมตรวจได้ 100"),
        ("ใช้ visibleSections/editableSections/canAction เป็น source of truth สำหรับ DOM และ focusable controls", "section ที่ซ่อนไม่อยู่ใน DOM และ read-only section ไม่มี mutation control"),
        ("สร้าง action radio/comment/confirm จาก actionOptions และ requireComment ที่ API ส่งมา", "ไม่ hardcode route/nextSection และ block submit เมื่อ result/comment ไม่ครบ"),
        ("รวม consideration history, workflow timeline และ invalidate หลัง save/upload/action", "ลำดับเวลาใหม่สุดถูกต้องและข้อมูลหลัง submit ไม่ค้างจาก cache เดิม"),
        ("upload ด้วย allowlist/5MB/scan state และ download ผ่าน authorized BE stream", "BLOCKED/FAILED ดาวน์โหลดไม่ได้ (422 FILE_SCAN_BLOCKED) · PENDING ขึ้นกับสวิตช์ SGI_ALLOW_PENDING_DOWNLOAD ที่ BE ส่งผลมาให้ — FE **ห้ามตัดสินเอง** ให้ดูจาก header X-SGI-Scan-Status แล้วขึ้นคำเตือนเมื่อเป็น PENDING · success แสดงชื่อ/ขนาดไฟล์จาก metadata"),
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
        ("จัดการ filter 7 ตัวตาม SDD สไลด์ 60 (status, impacted/new store code, store type, period statement, region, result) พร้อม dependency validation", "status required, คู่รหัสร้านต้องมาด้วยกัน, period statement บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ และช่วง from-to ตรวจผ่านก่อนค้นหา/Export"),
        ("map response เป็น summary line และตาราง 14 คอลัมน์ (SDD สไลด์ 60) ด้วย formatter กลาง", "คอลัมน์/ยอดรวม/วันที่ (ค.ศ.)/leading zero ตรง response และข้อมูลยอดขายผิดปกติใช้ salesDataDays"),
        ("ส่ง filter snapshot ล่าสุดไป export endpoint และจัดการ download/error state · SDD GI สไลด์ 62 กำหนดปุ่มออกผล 3 ตัว — Preview Report (ดูตัวอย่างก่อนออกไฟล์) · Export Excel (ทีมบัญชีเทียบ SAP) · Export CSV to Batch (ส่งเข้าคิว batch ประมวลผลต่อ)", "ทั้งสามปุ่มใช้เงื่อนไขค้นหาชุดเดียวกับตารางผลลัพธ์ และชื่อไฟล์/content type ตรง response (.xlsx สำหรับ Excel · .csv สำหรับ CSV to Batch)"),
        ("รองรับ fixture สำหรับ 0 แถว, หลาย region/type, เกิน threshold และยอดขายไม่ครบ 60 วัน", "sample verification ครอบคลุม table/export parity 14 คอลัมน์ โดยไม่ฝังข้อมูลทดสอบใน production"),
    ],
    "FE/LLDD-FE-Master-Data": [
        ("จัดการปัจจัยภายนอก (SCR-09) CRUD ครบ — DELETE เฉพาะรายการที่ยังไม่ถูกอ้างในเอกสาร",
         "factorCode ซ้ำไม่ได้ (409 CODE_DUPLICATE) · ลบรายการที่ถูกอ้างแล้วต้องได้ 409 · deleted row หายหลัง refresh"),
        ("จัดการ master แบรนด์คู่แข่ง (รหัส 01-11) พร้อม nameTh/nameEn/remark",
         "nameTh และ nameEn บังคับทั้งคู่ · competitorCode ซ้ำไม่ได้ · แถวใหม่ขึ้นใน dropdown ร้านคู่แข่งของหน้าเอกสาร"),
        ("ใช้ modal mode ADD/EDIT/DELETE แยก initial values, validation และ confirm copy",
         "เปลี่ยน mode ไม่ทิ้ง stale field และปุ่ม submit กัน double request"),
        ("toggle active แทนการลบเมื่อรายการถูกอ้างในเอกสารแล้ว",
         "แถวที่ปิด active ต้องไม่ขึ้นใน dropdown ของหน้าเอกสาร แต่เอกสารเก่ายังแสดงชื่อเดิมได้"),
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


# ---------------------------------------------------------------------------
# Workflow trigger-event contract (มติ 2026-08-25)
# ทุกเอกสาร BE / Job ต้องบอกให้ชัดว่า "ต้องเรียก engine ตัวไหน ที่จุดไหน" หรือ
# "ไม่เรียก" เพื่อให้คน BE ที่ไม่ได้ทำ workflow เองรู้ภาระของตัวเองตั้งแต่อ่านเอกสาร
# ชื่อ function ยึดชีต Detail ของ SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md (8 ตัว)
# ---------------------------------------------------------------------------

WORKFLOW_TRIGGER_CONTRACTS: dict[str, list[list[str]]] = {
    # ---- ฝั่ง BE API: มีเฉพาะบางเส้นที่แตะ engine ----
    "LLDD-BE-API-Document-Workflow-Actions": [
        ["ก่อนแสดงปุ่ม / ก่อนรับ action", "`getPermissionEvents`", "versionId, referenceId, userData", "ถ้า event ที่ส่งมาไม่อยู่ใน event[] ที่คืนมา ต้องตอบ 403 ห้ามเรียก eventWorkflow ต่อ"],
        ["กันกดซ้ำ / กันงานถูกคนอื่นเดินไปแล้ว", "`getTransaction`", "versionId, referenceId", "เทียบ state ปัจจุบันกับ state ที่ FE ส่งมา ไม่ตรงตอบ 409 (optimistic guard)"],
        ["กดผลพิจารณา (trigger event)", "`eventWorkflow`", "versionId, referenceId, userId, event, eventParam (amount สำหรับ route 100,000)", "🔴 หัวใจของเอกสารนี้ — เขียน sgi_consideration_logs + แนบไฟล์ + เรียก eventWorkflow ใน transaction เดียว; engine fail ต้อง rollback ฝั่ง SGI ทั้งหมด"],
        ["ผูกผู้รับผิดชอบขั้นถัดไป", "`addPreApprover`", "versionId, referenceId, stateId, approver, seq", "ใช้เมื่อ route ระบุตัวบุคคล (เช่น ตีกลับหาเจ้าของงานคนเดิม) — เรียกหลัง eventWorkflow สำเร็จ ใน transaction เดียวกัน"],
    ],
    "LLDD-BE-API-Workflow-Instances": [
        ["เปิด instance ให้เอกสาร", "`initializeWorkflow`", "versionId, userId, referenceId = `sgi_compensation_documents.id` (DP-1 ปิดแล้ว)", "idempotent — referenceId เดิมต้องไม่เกิด workflow_transaction ที่สอง"],
        ["ระบุผู้อนุมัติล่วงหน้า", "`addPreApprover`", "versionId, referenceId, stateId, approver, seq, userId", "เรียกต่อทันทีหลัง initialize ภายใน transaction เดียว"],
        ["อ่านสถานะ instance", "`getTransaction`", "versionId, referenceId", "ใช้ยืนยันว่า initialize สำเร็จจริงก่อนคืน 201"],
    ],
    "LLDD-BE-API-Document-Create-Update": [
        ["หลัง insert เอกสารสำเร็จ (Open first task)", "`initializeWorkflow` แล้วต่อด้วย `addPreApprover`", "versionId, userId, referenceId, stateId = `06`", "อยู่ใน transaction boundary เดียวกับการสร้างเอกสาร — engine fail ต้อง rollback เอกสาร"],
    ],
    "LLDD-BE-API-Document-Detail-Aggregate": [
        ["ประกอบหน้าเอกสาร", "`getPermissionEvents`", "versionId, referenceId, userData", "คืน event[] เป็นปุ่ม และ display[] เป็น READ/WRITE ต่อ part — FE ห้ามคำนวณสิทธิ์เอง"],
        ["สถานะ + ผู้ถืองานปัจจุบัน", "`getTransaction`", "versionId, referenceId", "ใช้เป็นค่าอ้างอิงให้ FE ส่งกลับมาตอนกดปุ่ม (optimistic guard)"],
    ],
    "LLDD-BE-API-Document-List-Search": [
        ["กล่องงานรอดำเนินการ", "`getPendingFlowByUser`", "userData, versionId", "เป็นแหล่งความจริงของรายการรอดำเนินการ · section 06 ต้อง union เอกสารที่จบด้วย หยุดชดเชยฯ (stoppedReopenable) เพิ่มเอง"],
    ],
    "LLDD-BE-API-Attachment-Sales-Timeline": [
        ["แท็บประวัติ (timeline)", "`getHistory`", "versionId, referenceId", "อ่าน `sgi_consideration_logs` ของ SGI เป็น timeline เต็ม — ไม่เรียก getHistory() เพราะ engine ไม่มี"],
    ],
    "LLDD-BE-API-Common-Contracts": [
        ["ตัวห่อกลาง (WorkflowGateway)", "ทั้ง 8 ตัวของ `@srm/glb-workflow`", "userData มาจาก BFF header (`x-user-id`, `x-user-group-id`)", "🔴 งานของเอกสารนี้คือ **ทำตัวห่อกลางให้ทุกคนเรียก** — map error ของ engine เข้า envelope `{success:false, error:{code,message}}` และบังคับ timeout/retry ที่เดียว"],
    ],
    "LLDD-BE-Data-Migration-Cutover": [
        ["ย้ายเอกสารที่ค้างกลางทาง", "`initializeWorkflow` แล้ว `eventWorkflow` ซ้ำจนถึง state ปัจจุบัน", "versionId, referenceId, ลำดับ event ตามสถานะเดิมใน K2", "🔴 ห้าม INSERT `workflow_transaction` ตรงเพื่อ 'ตั้ง state ให้ตรง' — ต้องเดิน event จริงเพื่อให้ history ครบ · ต้อง rerun ได้ (referenceId เดิมไม่สร้าง instance ซ้ำ)"],
    ],
    "LLDD-BE-Integration-SBP-Platform": [
        ["ส่ง identity ให้ engine", "ทุก function ที่รับ `userData`", "แปลง BFF header → userData ที่ lib ต้องการ", "ถ้า mapping ผิด `getPermissionEvents` จะคืนปุ่มว่างทั้งหน้า — ต้องมี contract test ครอบ"],
    ],
    # ---- ฝั่ง Job: มีแค่ Job 8b ตัวเดียวที่แตะ workflow engine ----
    # Job อื่น (2/3/4/5/6/7/8/9/10) ไม่เรียก engine จึง **ไม่มีหัวข้อนี้ในเอกสาร**
    # (มติผู้ใช้ 2026-08-25: "job อันไหนต้อง trigger event ก็ใส่ อันไหนไม่มีก็ไม่ต้องใส่")
    # 🔴 มติผู้ใช้ 2026-09-09 — **ฝั่ง job ไม่เรียก @srm/glb-workflow เอง**
    #    workflow lib ใช้กับ **flow K2 (เอกสาร/การอนุมัติ) เท่านั้น**
    #    Job 8b จึงเรียก `POST /api/v1/sgi/workflow/instances` ด้วย service token แทน
    #    แล้วให้ฝั่ง BE (LLDD-BE-API-Workflow-Instances) เป็นผู้เรียก engine ที่เดียว
    #    → เอกสารฝั่ง Job ไม่มีหัวข้อ Workflow Trigger Event Contract อีกต่อไป
}


def workflow_trigger_contract_blocks(topic: "Topic", section_no: str) -> list[dict[str, Any]]:
    """5.92 — บอกให้ชัดต่อเอกสารว่าต้องเรียก @srm/glb-workflow ตัวไหน ที่จุดไหน หรือไม่เรียก"""
    doc_key = topic.file.rsplit("/", 1)[-1]
    rows = WORKFLOW_TRIGGER_CONTRACTS.get(doc_key)
    if not rows:
        # เอกสารที่ไม่ได้แตะ workflow engine — ไม่ต้องมีหัวข้อนี้เลย (มติ 2026-08-25)
        return []
    return [
        h(2, f"{section_no} Workflow Trigger Event Contract"),
        p(
            "งานชิ้นนี้ **ต้องเรียก workflow engine** ตามตารางด้านล่าง · "
            "ชื่อ function ยึด API 8 ตัวของ `@srm/glb-workflow` ตามชีต `Detail` ของ "
            "`SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` — รายละเอียด signature และตารางที่ engine เขียน "
            "ดู **LLDD-BE-Workflow-Engine-Definition** หัวข้อ 5.3"
        ),
        table(["จุดที่เรียก (call site)", "Engine function", "พารามิเตอร์หลัก", "กติกา / transaction boundary"], rows),
        bullets([
            "🔴 กติกาเหล็ก: ตาราง `sps_store.workflow_*` (13 ตาราง) เป็นของ lib — SGI **R เท่านั้น** ห้าม INSERT/UPDATE/DELETE ตรงในทุกกรณี",
            "ทุกการเรียก engine ต้องผ่านตัวห่อกลาง `WorkflowGateway` ที่นิยามใน **LLDD-BE-API-Common-Contracts** (timeout · retry · map error เข้า envelope) ห้าม import lib ตรงจาก service",
            "unit test ต้อง mock engine และครอบอย่างน้อย: เรียกสำเร็จ · engine โยน error แล้ว rollback ฝั่ง SGI ครบ · เรียกซ้ำด้วย referenceId เดิมไม่เกิดผลซ้ำ",
        ]),
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
        # ห้ามวน tests ซ้ำ — step ที่ไม่มี test ตรงตัวให้เขียนว่ายังไม่มี ไม่ใช่ยืมหลักฐานของ step อื่น
        if index - 1 < len(topic.tests):
            failure = topic.tests[index - 1]
        else:
            failure = "— (ยังไม่มี test เฉพาะขั้นนี้ · ครอบด้วย test รวมของเอกสารในหัวข้อ 11)"
        sequence_rows.append([index, step, failure])
    if not sequence_rows:
        sequence_rows = [[1, "อ่านข้อมูลตาม DB Mapping และคืนผลตาม contract", "ไม่พบข้อมูลคืน typed error"]]
    return [
        h(2, "5.90 Endpoint Implementation Contract"),
        table(["Endpoint", "Use-case owner", "Service/repository behavior", "Definition of done"], endpoint_rows),
        h(2, "5.91 Backend Execution Sequence"),
        table(["Step", "Behavior specific to this LLDD", "Failure/test evidence"], sequence_rows),
    ] + workflow_trigger_contract_blocks(topic, "5.92")


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
    blocks.extend(job_run_contract_blocks(job_no, "5.95"))
    blocks.extend(job_decision_rule_blocks(job_no, "5.96"))
    if job_no == "4":
        blocks.extend([
            h(2, "5.97 Job 4 Atomic File / Outbox Sequence"),
            table(
                ["Order", "Required action", "Failure behavior"],
                [
                    [1, "lock candidate W ด้วย FOR UPDATE SKIP LOCKED และสร้าง payload ใน memory", "validation fail: rollback lock; สถานะยัง W"],
                    [2, "เขียน temporary file, fsync, atomic rename และคำนวณ SHA-256", "write/rename/checksum fail: ลบ temp; สถานะยัง W; ไม่สร้าง outbox"],
                    [3, "transaction เดียว update W→P และ insert sgi_interface_transactions/outbox READY", "DB fail: rollback W→P และ outbox; durable file คงไว้ให้ cleanup/reconcile โดย checksum"],
                    [4, "dispatcher อ่าน READY แล้วอัปโหลดขึ้น EAI S3 (prefix ขาออก); compare checksum ก่อนส่ง", "อัปโหลด fail: outbox ยัง READY/FAILED_RETRY; ห้ามเปลี่ยน candidate กลับ W เพื่อไม่ให้สร้างไฟล์ซ้ำ"],
                    [5, "publish สำเร็จ mark SENT + outbox_status = PUBLISHED; ได้ publisher confirm จึง CONFIRMED + status = COMPLETED", "ใช้ transaction id เดิมตลอด lifecycle"],
                ],
            ),
        ])
    if job_no == "6":
        blocks.extend([
            h(2, "5.97 เขียนข้อมูลรอบชดเชย (รับเข้าโครง 2026-08-21 · gap F8 + F1)"),
            p("Job 6 คือ job เดียวที่เขียนตารางรอบชดเชยในระบบเดิม — `ExportService.manageDBToFs()` เรียก 5 คำสั่งต่อกันเป็นชุด ระบบใหม่ต้องทำครบเหมือนเดิม แต่เขียนลงตารางของ SGI"),
            table(["ลำดับใน manageDBToFs()", "ระบบเดิม (Oracle)", "ระบบใหม่ (SGI)", "ใช้ทำอะไรต่อ"], [
                ["updateFgiImpactStoreOnProcess(INITDATE)", "FGI_IMPACT_STORE_ON_PROCESS · LAST_COMPENSATE_SEQ_NO + 1 เมื่อ FLAG_ACTION='Y' และเพิ่งชดเชยเดือนที่แล้ว", "sgi_fgi_impact_processes.last_compensate_seq_no += 1", "**เคสต่อเนื่อง** (SEQ_NO > 1)"],
                ["insertFgiImpactStoreOnProcess()", "แถวใหม่ · LAST_COMPENSATE_SEQ = MAX+1 · SEQ_NO = 1 · FLAG_ACTION='Y' · DATASOURCE", "🔴 **ในโครงใหม่เป็น UPDATE ไม่ใช่ INSERT** — `sgi_fgi_impact_processes` ถูก **Job 2 สร้างไว้แล้ว** ตอนนำเข้า (`UNIQUE (impacted_store_code, impact_month)`) Job 6 จึงต้อง `UPDATE ... SET flag_action = 'Y'` (จาก `'N'` ที่ Job 2 ใส่) · `last_compensate_seq = MAX+1` · `last_compensate_seq_no = 1` · `start/end_compensate_*` · และเลื่อน `process_status` เป็น `READY_DOCUMENT` — **insert ซ้ำจะชนคีย์** (มติ 2026-09-13 · DECISIONS 2.38)", "**เปิดเรื่องใหม่** (SEQ_NO = 1)"],
                ["insertFgiImpactStoreCompensate(...)", "FGI_IMPACT_STORE_COMPENSATE · COMPENSATE_FORECAST / COMPENSATE_ADJUST ต่องวด", "**sgi_fgi_impact_compensations** (forecast_amount / adjust_amount)", "**นับยอด 0 ติดกันกี่เดือน** (กติกาเดือน 1-3 / เดือนที่ 4)"],
                ["insertFgiNewStoreCompensate(...)", "FGI_NEW_STORE_COMPENSATE", "sgi_document_new_stores.compensation_amount / compensate_percent", "ยอดต่อร้านเปิดใหม่"],
                ["updateCompleteImpactStoreOnProcess / FlagYToW", "FLAG_ACTION Y→N / Y→W", "sgi_fgi_impact_processes.flag_action", "ปิดรอบ / ส่งกลับรอตรวจ"],
            ]),
            p("⚠️ `ImportJdbc.insertImpactStoreOnProcess()` / `updateImpactStoreOnProcess()` มี SQL ชุดเดียวกันอยู่ในไฟล์ Import แต่ตรวจทั้ง src แล้ว **ไม่มี call site จริง** — เป็นโค้ดตาย ให้ยึด `ExportJdbc` เป็นต้นแบบเท่านั้น"),
            h(2, "5.98 Tracking Retention / Purge SQL"),
            p("Purge ทำได้เฉพาะแถว COMPLETED ที่ครบ purge_after และไม่อยู่ใน legal hold; ต้องรันเป็น batch จำกัดจำนวนเพื่อไม่ lock ตารางยาว"),
            code("""WITH purge_candidates AS (
    SELECT id
    FROM sgi_interface_transactions
    WHERE status = 'COMPLETED'
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
      AND data_name = ANY(:sta_data_names)
    ORDER BY id
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM sgi_interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;""", "sql"),
        ])
    if job_no == "8":
        blocks.extend([
            h(2, "5.97 Job 8 Document Number Gap and Rerun Policy"),
            p("Job 8 ใช้ running number แบบ monotonic ต่อปี ค.ศ. ช่องว่างของเลขเอกสารจาก concurrent rerun หรือ ON CONFLICT เป็นพฤติกรรมที่ยอมรับได้ เพราะเลขที่มีหน้าที่รับประกัน uniqueness ไม่ได้รับประกันความต่อเนื่อง"),
            table(
                ["Case", "Required behavior", "Evidence / metric"],
                [
                    ["Rerun พบ impact_process_id เดิมก่อนจองเลข", "คืน/ข้ามด้วย doc_no เดิมโดยไม่จอง running_no เพิ่มเมื่อ fast lookup พบข้อมูลแล้ว", "duplicateExistingCount + existingDocNo"],
                    ["Concurrent worker ชน ON CONFLICT หลังจองเลข", "ยอมให้ running_no ที่จองแล้วกลายเป็น gap; ห้ามลด sequence และห้ามนำเลขกลับมาใช้", "numberGapCount + conflictedImpactProcessId"],
                    ["Conflict path", "อ่าน sgi_compensation_documents ด้วย impact_process_id แล้วใช้ d.doc_no เดิมสำหรับ tracking/reconcile", "tracking.doc_no ตรงกับเอกสารที่ commit อยู่จริง"],
                    ["New document path", "insert document และ tracking (direction=INTERNAL) ใน transaction เดียว", "createdCount และ trackingCount เพิ่มเท่ากัน"],
                    ["Audit/runbook", "อธิบายว่าเลขอาจไม่ต่อเนื่องแต่ต้องไม่ซ้ำและตรวจสอบย้อนกลับได้", "ไม่มีขั้นตอน manual reuse หรือ renumber"],
                ],
            ),
        ])
    # เลือกเลขหัวข้อถัดไปที่ยังว่าง (job บางตัวใช้ 5.95/5.96 ไปแล้ว) เพื่อไม่ให้เลขกระโดด
    used = {b["text"].split()[0] for b in blocks if str(b.get("type","")).startswith("h") and str(b.get("text","")).startswith("5.9")}
    next_no = next(f"5.{n}" for n in range(95, 100) if f"5.{n}" not in used)
    blocks.extend(workflow_trigger_contract_blocks(topic, next_no))
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
                ["Load exact profile", f"เรียก GET /api/v1/sgi/document/{{docNo}} และยืนยัน roleProfileCode={profile_code}, statusCode={profile['code']} ก่อน render action state", f"profile mismatch ต้อง fail closed; ไม่ใช้ role switcher เพื่อจำลอง {profile_code}"],
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
                ["ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "comment optional"],
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
                ["คำนวณเงินชดเชย", "baseCompensationAmount, totalCompensatePercent, totalCompensationAmount, approvalLimitIndicator", "read-only; แสดงเกณฑ์วงเงินอนุมัติจาก API (< 100,000 จบที่ GM · ≥ 100,000 ส่ง AVP · มติ 2026-08-18)"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment ตาม actionOptions.requireComment"],
            ],
            "actions": [
                ["คำนวณเงินชดเชยเรียบร้อย", "comment optional — **ปุ่มเดียวของขั้นนี้ (มติ 2026-09-01)** ส่งยอดกลับ section 06"],
            ],
            "tests": [
                "เปิดด้วย roleProfileCode=P-08 แล้ว sec-calc ต้องแสดง",
                "sec-calc ต้องไม่มี input/button บันทึก",
                "section ร้านเปิดใหม่/คู่แข่ง/ปัจจัยต้อง read-only",
                "action radio แสดงเฉพาะ 1 รายการของ role 08 (มติ 2026-09-01)",
                "หลัง submit ต้อง reload detail/timeline/status",
            ],
        },
        {
            "file": "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion",
            "code": "01",
            "name": "หน่วยงานส่งเสริมธุรกิจ SBP",
            "short": "Business Promotion",
            "status": "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ",
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
                ["ข้อมูลประกอบอนุมัติ", "totalCompensationAmount, approvalLimitIndicator", "read-only จาก API; ใช้แสดงเกณฑ์วงเงินอนุมัติ (< 100,000 จบที่ GM · ≥ 100,000 ส่ง AVP ตาม SDD GI)"],
                ["เอกสารแนบ", "file, fileName, attachmentType, remark", "เพิ่มไฟล์ได้; ขนาด <= 5 MB; extension ต้องอยู่ใน allowlist"],
                ["แผงพิจารณา", "result, comment", "result required; comment ตาม actionOptions.requireComment"],
            ],
            "actions": [
                ["เห็นควรชดเชย", "comment optional"],
                ["เห็นควรไม่ชดเชย", "comment ตาม actionOptions.requireComment"],
                ["ส่งกลับฝ่าย SBP DSA", "comment ตาม actionOptions.requireComment — มติ 2026-09-01 (เดิมส่งกลับหน่วยงานส่งเสริมธุรกิจ SBP)"],
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
                ["ส่งกลับฝ่าย SBP DSA", "comment ตาม actionOptions.requireComment — มติ 2026-09-01 (เดิมส่งกลับ GM ส่งเสริมธุรกิจฯ)"],
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
            ["Section", "06 ฝ่าย SBP DSA", "08 จนท. SBP DSA", "01 หน่วยงานส่งเสริมธุรกิจ SBP", "02 GM ส่งเสริมฯ", "03 AVP สำนักบริหาร SBP"],
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
                ["06 ฝ่าย SBP DSA", "เห็นควรไม่ชดเชย; หยุดชดเชยประกันรายได้; ส่งหน่วยงานส่งเสริมธุรกิจ SBP; ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "บังคับเมื่อเลือก เห็นควรไม่ชดเชย"],
                ["08 เจ้าหน้าที่ SBP DSA", "คำนวณเงินชดเชยเรียบร้อย (**ปุ่มเดียว** · มติ 2026-09-01)", "บังคับเมื่อ actionOptions.requireComment=true"],
                ["01 หน่วยงานส่งเสริมธุรกิจ SBP", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; ฝ่าย SBP DSA ดำเนินการ (ส่งกลับ)", "บังคับเมื่อเลือก เห็นควรไม่ชดเชย"],
                ["02 GM ส่งเสริมธุรกิจฯ", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; **ส่งกลับฝ่าย SBP DSA** (มติ 2026-09-01)", "บังคับเมื่อ actionOptions.requireComment=true"],
                ["03 AVP สำนักบริหาร SBP", "เห็นควรชดเชย; เห็นควรไม่ชดเชย; **ส่งกลับฝ่าย SBP DSA** (มติ 2026-09-01)", "บังคับเมื่อ actionOptions.requireComment=true"],
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
        "docNo": "2026/00123",
        "statusCode": profile["code"],
        "viewerRbacRoleCode": "R-XX",
        "roleProfileCode": role_profile_code(profile),
        "visibleSections": profile["visible"],
        "editableSections": profile["editable"],
        "canUploadAttachment": profile["upload"],
        "canAction": True,
        "actionOptions": [{"value": RESULT_ENUM_VALUE[row[0]], "label": row[0], "requireComment": "ต้องกรอก" in row[1]} for row in profile["actions"]],
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
        payload("GET /api/v1/sgi/document/{docNo} response", api_json(response)),
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
        "08": ("คำนวณเงินชดเชยเรียบร้อย", "06", "06"),
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
            ("Load detail", "เปิดเอกสาร", "GET /api/v1/sgi/document/{docNo}", "render role profile"),
            ("Save editable section", "ปุ่มบันทึก", "PUT /api/v1/sgi/document/{docNo}", "ใช้เฉพาะ role ที่มี editableSections"),
            ("Upload attachment", "เลือกไฟล์", "POST /api/v1/sgi/document/{docNo}/attachments", "append attachment when allowed"),
            ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/sgi/document/{docNo}/actions", "submit selected result"),
        ],
        [
            ApiSpec("GET", "/api/v1/sgi/document/{docNo}", f"โหลด role profile {role_profile_code(profile)} สำหรับหน้า detail", {"docNo": "2026/00123"}, {"docNo": "2026/00123", "statusCode": profile["code"], "viewerRbacRoleCode": "R-XX", "roleProfileCode": role_profile_code(profile), "visibleSections": profile["visible"], "editableSections": profile["editable"], "actionOptions": [{"value": row[0], "label": row[0], "requireComment": "ต้องกรอก" in row[1]} for row in profile["actions"]]}),
            ApiSpec("POST", "/api/v1/sgi/document/{docNo}/actions", f"ตัวอย่าง positive-path จาก section {profile['code']}; Section 02 ส่งต่อ AVP (03) เมื่อยอดรวม ≥ 100,000 บาท และจบที่ GM เมื่อ < 100,000 บาท (มติ 2026-08-18)", {"result": forward_action[0], "comment": "ส่งดำเนินการตามลำดับ"}, {"statusCode": forward_action[2], "nextSection": forward_action[1], "message": "submitted"}),
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
                ["REPORT_STATUS_REQUIRED", "400", "กดค้นหาในหน้ารายงานโดยไม่เลือกสถานะ (สถานะเป็น filter บังคับเพียงตัวเดียว · SDD สไลด์ 60)", "กรุณาเลือกสถานะก่อนค้นหาข้อมูล"],
                ["ATTACHMENT_FILE_REQUIRED", "422", "กดปุ่มแนบเอกสารโดยยังไม่ได้เลือกไฟล์", "กรุณาเลือกไฟล์ที่ต้องการแนบ ก่อนกดแนบเอกสาร"],
                ["FILE_TOO_LARGE", "413", "attachment > 5 MB", "ไฟล์แนบมีขนาดเกิน 5 MB"],
                ["FILE_TYPE_UNSUPPORTED", "415", "extension/content type ไม่อยู่ใน allowlist", "ชนิดไฟล์ไม่อนุญาตให้อัปโหลด"],
                ["FILE_SCAN_BLOCKED", "422", "AV scan พบไวรัสหรือ scan failed", "ไฟล์แนบไม่ผ่านการตรวจสอบความปลอดภัย"],
                ["FORBIDDEN", "403", "ไม่มีสิทธิ์เมนู/เอกสาร/task", "กรุณาติดต่อผู้ดูแลระบบ"],
                ["DUPLICATE_DOCUMENT", "409", "business key ซ้ำตอนสร้างเอกสาร", "ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว"],
                ["CONFLICT", "409", "resource/task ถูกเปลี่ยนหรือเงื่อนไขปัจจุบันไม่ตรงกับคำขอ", "ข้อมูลมีการเปลี่ยนแปลง กรุณาโหลดข้อมูลล่าสุดแล้วดำเนินการใหม่"],
                ["STALE_VERSION", "409", "versionNo ที่ส่งมาไม่ตรงกับ sgi_compensation_documents.version_no", "ข้อมูลถูกแก้ไขโดยผู้ใช้อื่น กรุณาโหลดข้อมูลล่าสุดแล้วลองอีกครั้ง"],
                ["FS_BRIDGE_UNAVAILABLE", "FE", "hidden iframe ไม่ตอบ FS_FORM_READY ภายในเวลาที่กำหนด", "ไม่สามารถเชื่อมต่อแบบฟอร์ม FS ได้ กรุณาลองอีกครั้ง"],
                ["FS_BRIDGE_ORIGIN_INVALID", "FE", "event.origin ไม่ตรง allowlist", "ไม่สามารถยืนยันแหล่งที่มาของแบบฟอร์ม FS ได้"],
                ["CODE_DUPLICATE", "409", "บันทึก master ด้วยรหัสที่มีอยู่แล้ว (`factorCode` / `competitorCode`)", "รหัสนี้ถูกใช้แล้ว กรุณาระบุรหัสอื่น"],
                ["FS_PROTOCOL_VERSION_UNSUPPORTED", "FE", "ข้อความจาก FS iframe ส่ง `protocolVersion` ที่ไม่ใช่ `1.0`", "เวอร์ชันของแบบฟอร์ม FS ไม่รองรับ กรุณาติดต่อผู้ดูแลระบบ"],
                ["FS_BRIDGE_SCHEMA_INVALID", "FE", "FS_FIELD_SCHEMA ไม่ตรง message schema หรือมี field type ที่ไม่รองรับ", "ข้อมูลแบบฟอร์ม FS ไม่ถูกต้อง กรุณาติดต่อผู้ดูแลระบบ"],
                ["FS_BRIDGE_SUBMIT_FAILED", "FE", "FS_SUBMIT_RESULT ไม่สำเร็จหรือ FS_ERROR ตอน submit", "ส่งแบบฟอร์ม FS ไม่สำเร็จ กรุณาตรวจสอบข้อมูลแล้วลองอีกครั้ง"],
            ],
        ),
        h(2, "5.2 Endpoint Role Matrix"),
        p("Matrix นี้เป็น baseline สำหรับ BE authorization guard; menu-level visibility มาจาก permissions ต่อ URL ของ auth-backend (header `x-user-permissions`)"),
        table(
            ["Endpoint group", "Endpoint pattern", "Allowed roles / identity"],
            [
                ["Current user/menu", "ไม่ใช่ endpoint ของ SGI — FE เรียกของระบบเดิมผ่าน BFF: GET /auth/profile, GET /users/current, GET /menus, GET /groups/current-user/permissions", "authenticated user"],
                ["Task inbox", "GET /sgi/document/tasks", "authenticated user with assigned task access"],
                ["Document read/list/timeline/sales", "GET /sgi/document*, GET /sgi/document/{docNo}/timeline, GET /sgi/document/{docNo}/sales", "document participant or report/admin role explicitly granted"],
                ["Document create", "POST /sgi/document", "🔴 **service token / pipeline เท่านั้น** — มติ 2026-08-06 ตัดฟอร์มสร้างเอกสารใน FE ออกแล้ว (ต้นทางสร้างที่ระบบ FS แล้ว SBP Statement ส่งข้อมูลกลับ) · ห้ามระบุเป็นรหัสกลุ่มสิทธิ์ เพราะเลข 01/02/03 ชนกับ section_code ของ workflow"],
                ["Document update/action/attachment upload", "PUT /sgi/document/{docNo}, POST /sgi/document/{docNo}/actions, POST /sgi/document/{docNo}/attachments", "current action owner; admin override only with policy and audit reason"],
                ["Attachment download", "GET /sgi/document/{docNo}/attachments/{attachId}/download", "สิทธิ์เท่ากับอ่านเอกสาร + attachment ต้องเป็นของ docNo นั้น · เงื่อนไข `scan_status` ใช้**นโยบายเดียวของทั้งระบบ** — " + ATTACHMENT_DOWNLOAD_POLICY_SHORT + " · รายละเอียดเต็มที่ `LLDD-BE-Integration-SBP-Platform` หัวข้อ 5"],
                ["Lookup", "/sgi/lookup/document-statuses, /sgi/lookup/workflow-sections (ร้าน/ภาค/ประเภทสาขา ใช้ /store/* + /common/common-code ของระบบ SBP เดิม · 2026-08-06)", "authenticated user with related menu access"],
                ["Master (SGI)", "/sgi/master/factors*, /sgi/master/competitors*", "admin/HQ ตามสิทธิ์เมนูที่มากับ header x-user-permissions"],
                ["RBAC/ผู้ปฏิบัติงาน", "ไม่ใช่ endpoint ของ SGI — ตัด /operators* /roles* /menus* /menu-permissions* /employees/search รวม 14 เส้น (2026-08-05) ใช้ auth-backend เดิม จัดการที่หน้า /setting/manage-user-rights", "-"],
                ["Reports", "/sgi/report/status-summary*", "admin/HQ/report roles and accounting service user"],
                ["Internal workflow/interface", "/sgi/workflow/instances · /sgi/interface/* (tracking · pending-ack)", "service token หรือ API key เท่านั้น — ไม่ผ่านสิทธิ์เมนูของผู้ใช้"],
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
                ["Format", "YYYY/xxxxx โดย YYYY เป็นปี **ค.ศ.** และ running 5 หลัก (มติ 2026-08-06 · หน้าจอ K2 จริงใช้ ค.ศ. เช่น 2026/01870)", "ตัวอย่าง 2026/00124; เก็บ doc_no เป็น string และเก็บ year/running_no แยกเพื่อ index"],
                ["Sequence scope", "running reset ตามปี ค.ศ.", "unique key `(year, running_no)` และ unique `doc_no`"],
                ["Lock strategy", "lock row sequence ด้วย `SELECT ... FOR UPDATE` หรือ database sequence ต่อปี", "ห้ามอ่าน max(running_no)+1 แบบไม่มี lock"],
                ["Transaction boundary", "generate docNo, insert sgi_compensation_documents, insert first workflow task และ audit ใน transaction เดียว", "ถ้าสร้าง task ไม่สำเร็จต้อง rollback ทั้งชุด"],
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
                ["2. Check duplicate", "query business key บน sgi_compensation_documents", "พบเอกสารเดิมคืน 409 DUPLICATE_DOCUMENT พร้อม docNo เดิมถ้าอนุญาตให้แสดง"],
                ["3. Start transaction", "เปิด transaction และ lock sequence row ของปี ค.ศ.", "lock timeout คืน 409/503 ตามมาตรฐาน platform"],
                ["4. Generate docNo", "เพิ่ม running_no และประกอบ doc_no", "ยังไม่ส่ง response จนกว่า commit สำเร็จ"],
                ["5. Insert document", "insert sgi_compensation_documents และ child rows เริ่มต้น", "fail ต้อง rollback sequence/document"],
                ["6. Open first task", "เรียก initializeWorkflow + addPreApprover (state 06) ของ @srm/glb-workflow ภายใน transaction boundary ที่กำหนด — ชื่อ function ตามชีต Detail ของ LLDD lib — ดู LLDD-BE-Workflow-Engine-Definition 5.3", "fail ต้อง rollback document"],
                ["7. Commit", "commit transaction (ไม่มีการเขียน audit ของ master แล้ว · ยกเลิกระบบ audit ของ master 2026-08-07)", "หลัง commit จึง return docNo/statusCode"],
            ],
        ),
        h(2, "5.3 Required Developer Tests for docNo"),
        table(
            ["Test", "Expected result"],
            [
                ["ยิง POST /sgi/document พร้อมกัน 20 request ในปีเดียวกัน", "ได้ docNo ไม่ซ้ำ running เรียงตาม commit และไม่มี duplicate key error ที่หลุดเป็น 500"],
                ["สร้าง duplicate business key", "คืน 409 DUPLICATE_DOCUMENT และไม่ consume docNo ใหม่ถ้า duplicate ถูกพบก่อน lock sequence"],
                ["จำลอง error หลัง insert document ก่อนเปิด workflow", "rollback แล้วไม่เหลือ sgi_compensation_documents/workflow_transaction/audit partial"],
                ["เปลี่ยนปี ค.ศ.", "running เริ่มที่ 00001 ของปีใหม่"],
            ],
        ),
        h(2, "5.4 docNo Generator SQL Reference"),
        code("""-- ออกเลขเอกสาร YYYY/xxxxx แบบ atomic ต่อ "ปี ค.ศ." (ห้ามใช้ พ.ศ. — ดู api.md มติ 2026-08-06)
-- ตารางจริงคือ sgi_document_running_numbers (year · last_running_no · updated_at) ไม่มีคอลัมน์ created_at

-- 1) สร้างแถวของปีนี้ถ้ายังไม่มี (idempotent)
INSERT INTO sgi_document_running_numbers (year, last_running_no)
VALUES (:year, 0)
ON CONFLICT (year) DO NOTHING;

-- 2) กินเลขถัดไปในทรานแซกชันเดียวกับการสร้างเอกสาร — UPDATE ... RETURNING ล็อกแถวให้เอง
--    กัน batch (Job 8) กับผู้ใช้สร้างพร้อมกันแล้วได้เลขชนกัน
UPDATE sgi_document_running_numbers
SET last_running_no = last_running_no + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE year = :year
RETURNING last_running_no;          -- → :runningNo

-- 3) docNo = :year || \'/\' || lpad(:runningNo::text, 5, \'0\')   เช่น 2026/00123
--    ⚠️ ต้องใส่ impact_process_id ทุกครั้ง — เป็น NOT NULL UNIQUE (หนึ่ง impact process = หนึ่งเอกสาร)
INSERT INTO sgi_compensation_documents (
    doc_no, year, running_no,
    impact_process_id, impact_compensation_id, impacted_store_code, impact_month, new_store_code,
    round_no, source, status_code, current_section_code, created_by
) VALUES (
    :docNo, :year, :runningNo,
    :impactProcessId, :impactCompensationId, :impactedStoreCode, :impactMonth, :newStoreCode,
    :roundNo, :source, :statusInit, \'06\', :userId
);
-- created_at / total_compensation_amount / version_no มี DEFAULT อยู่แล้ว ไม่ต้องส่ง""", "sql"),
    ]


def attachment_storage_extra_blocks() -> list[dict[str, Any]]:
    return [
        h(2, "5.1 Attachment Storage and Security Design"),
        p(
            "Attachment API จัดการ binary file จริง ไม่ใช่บันทึกแต่ metadata — แต่ **SGI ไม่ได้เป็นเจ้าของ storage layer** · "
            "ตามมติ **DP-8 (ปิด 2026-08-24)** SGI เก็บแค่ metadata ใน `sgi_document_attachments` ของตัวเอง แล้ว "
            "**ยืม service S3 ของระบบ SBP เดิม** (`POST /statement/upload-file-aws` · `download-file-aws`) — "
            "สิ่งที่ SGI เป็นเจ้าของจริงคือ **validation · authorization · metadata · การแปลงเป็น stream ให้ FE**"
        ),
        p(
            "🔴 **wrapper ของระบบเดิมเป็น base64 ไม่ใช่ stream** (ตรวจ `store-backend` 2026-08-26) — สายส่งจริงคือ "
            "`FE ← binary stream ← SGI BE ← base64 JSON ← /statement/{upload,download}-file-aws ← S3` · "
            "ไฟล์ 5 MB จะกลายเป็น ~6.7 MB ใน JSON (body limit ของ store-backend คือ 100 MB) · "
            "ปุ่ม **ดาวน์โหลดทั้งหมด (.zip)** ห้ามโหลดทุกไฟล์เข้า memory พร้อมกัน ให้ดึงทีละไฟล์แล้ว stream เข้า zip "
            "— รายละเอียดเต็มอยู่ที่ **LLDD-BE-Integration-SBP-Platform** 5.3"
        ),
        table(
            ["Item", "Required value / convention", "Developer note"],
            [
                ["Storage provider", "**service S3 ของระบบ SBP เดิม** (`AwsService` ผ่าน `/statement/{upload,download}-file-aws`)",
                 "🔴 มติ DP-8 — SGI **ห้ามสร้าง storage adapter/ไม่ต่อ S3 SDK เอง** และไม่ต้องเลือก vendor · เก็บ `storage_provider` ไว้เป็น metadata เผื่ออนาคตเท่านั้น"],
                ["Bucket/container", "**bucket ของระบบเดิม** (ทีม SBP เป็นผู้กำหนด)",
                 "ไฟล์ของ SGI ใช้ prefix ของตัวเองใต้ bucket เดียวกับระบบเดิม — lifecycle/backup เป็นของ infra ฝั่งนั้น ไม่ใช่ของ SGI"],
                ["Object key", "`documents/{year}/{docNoSafe}/{attachId}/{sha256Prefix}-{safeFileName}`", "`docNoSafe` แทน `/` ด้วย `-`; sanitize filename ก่อนใช้ใน key"],
                ["Quarantine / AV", "**แยกสถานะสแกนออกจากสถานะไฟล์**", 
                 "🔴 ไม่พบ AV scanner ในเอกสารวิเคราะห์ระบบเดิมเลย · จนกว่าจะยืนยัน ให้ `scan_status` เริ่มที่ `PENDING` และ **ตัดสินร่วมกับทีม infra** ว่าจะสแกนที่ไหน (ฝั่ง S3 event · ฝั่ง SGI · หรือยอมรับความเสี่ยง) — ห้ามสมมติว่ามีของให้ใช้แล้ว"],
                ["Allowed extension", ATTACHMENT_ALLOWED_EXTENSIONS, "ตรวจทั้ง extension และ content type/magic bytes เท่าที่ platform รองรับ · ไม่อยู่ใน allowlist → **415 `FILE_TYPE_UNSUPPORTED`**"],
                ["AV scan status", "PENDING -> CLEAN หรือ BLOCKED/FAILED", ATTACHMENT_DOWNLOAD_POLICY_SHORT + " — รายละเอียดเต็มที่หัวข้อ Download Flow"],
                ["Max size", "5 MB ต่อไฟล์", "เกินให้คืน **413 `FILE_TOO_LARGE`** ก่อน upload เข้า storage"],
                ["ต้องเลือกไฟล์ก่อน", "กดปุ่มแนบเอกสารโดยยังไม่เลือกไฟล์", "คืน **422 `ATTACHMENT_FILE_REQUIRED`** พร้อมข้อความ verbatim \"กรุณาเลือกไฟล์ที่ต้องการแนบ ก่อนกดแนบเอกสาร\" — FE ต้องกันไว้ก่อนยิง API ด้วย"],
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
                ["scanStatus/scannedAt/scanMessage", "ผล AV scan · เริ่มที่ `PENDING` เสมอตอนอัปโหลด", ATTACHMENT_DOWNLOAD_POLICY_SHORT],
                ["uploadedBy/uploadedAt/deletedFlag", "audit metadata", "soft delete เท่านั้นเมื่อมีการลบภายหลัง"],
            ],
        ),
        h(2, "5.3 Upload Flow"),
        table(
            ["Step", "Backend behavior", "Error / response"],
            [
                ["1. Authorize", "ตรวจผู้ใช้มีสิทธิ์อ่านเอกสารและ canUploadAttachment/current task owner", "ไม่มีสิทธิ์คืน 403"],
                ["2. Validate multipart", "ตรวจ file present, size, extension, content type, sectionCode", "คืน 400/413/415 ตาม catalog"],
                ["3. Hash + ส่งขึ้น storage", "คำนวณ sha256 จาก buffer แล้วเรียก `POST /statement/upload-file-aws` (**ส่งเป็น base64**) เก็บ objectKey ที่ได้กลับมา", "service ของระบบเดิม fail คืน 503 และ **ไม่ insert metadata**"],
                ["4. Scan", "ตั้ง `scan_status = PENDING` ตอนอัปโหลด แล้วให้ตัวสแกนของแพลตฟอร์มอัปเดตเป็น CLEAN/BLOCKED ภายหลัง", "พบไวรัสให้ตั้ง BLOCKED และคืน FILE_SCAN_BLOCKED"],
                ["5. Insert metadata", "insert `sgi_document_attachments` พร้อม objectKey · sha256 · scan_status", "🔴 ไม่มีขั้น move/promote — wrapper ของระบบเดิมไม่มี API ย้าย object ให้ SGI เรียก"],
                ["6. Respond", "คืน attachId, fileName, fileSizeBytes, scanStatus, uploadedAt", "ไม่คืน bucket/objectKey ให้ FE"],
            ],
        ),
        h(2, "5.4 Download Flow and Authorization"),
        p(ATTACHMENT_DOWNLOAD_POLICY_FULL),
        table(
            ["Step", "Backend behavior", "Error / response"],
            [
                ["1. Validate path", "ตรวจ docNo/attachId และ attachment belongs to docNo", "ไม่พบคืน 404"],
                ["2. Authorize read", "สิทธิ์เท่ากับ document read หรือ report/admin ที่ได้รับสิทธิ์", "ไม่มีสิทธิ์คืน 403"],
                ["3. Check scan", "ตัดสินตามนโยบายเดียวด้านล่าง และ `deleted_flag = 'N'` (คอลัมน์เป็น CHAR(1) ไม่ใช่ boolean)",
                 ATTACHMENT_DOWNLOAD_POLICY_SHORT + " — **ห้าม hardcode รายการสถานะในโค้ด** ให้อ่านสวิตช์จาก `mas_param` ทุกครั้ง"],
                ["4. Stream", "เรียก `POST /statement/download-file-aws` ได้ **base64** แล้ว decode เป็น buffer ก่อน stream ออกไป",
                 "🔴 **ไม่มี signed URL ให้ใช้** — wrapper ของระบบเดิมไม่คืน presigned url · ตั้ง Content-Type และ Content-Disposition จาก metadata"],
                ["5. Audit", "บันทึกร่องรอยการดาวน์โหลดที่ **application log** (structured)",
                 "🔴 ตาราง `audit_logs` ถูกตัดไปแล้ว 2026-08-07 — ห้ามอ้างตารางนี้ · ต้อง trace userId/docNo/attachId/requestId ได้จาก log"],
            ],
        ),
        h(2, "5.5 Download Endpoint Contract"),
        table(
            ["Method", "Path", "Response"],
            [
                ["GET", "/api/v1/sgi/document/{docNo}/attachments/{attachId}/download", "binary stream; headers Content-Type, Content-Length, Content-Disposition"],
            ],
        ),
        h(2, "5.6 Attachment Repository SQL Reference"),
        code("""-- Insert metadata after storage write and AV scan pass.
INSERT INTO sgi_document_attachments (
    doc_no, section_code, file_name, mime_type, file_size,
    storage_provider, bucket, object_key, sha256,
    scan_status, scanned_at, uploaded_by, uploaded_at, deleted_flag
) VALUES (
    :docNo, :sectionCode, :fileName, :mimeType, :fileSize,
    :storageProvider, :bucket, :objectKey, :sha256,
    'PENDING', NULL, :userId, CURRENT_TIMESTAMP, 'N'
    -- ⚠️ scan_status เริ่มที่ PENDING เสมอ · scanned_at เป็น NULL จนกว่าตัวสแกนจะอัปเดต
    --    (เขียน CLEAN ตอน insert = ประกาศว่าสแกนผ่านทั้งที่ยังไม่มีตัวสแกนในระบบ)
)
RETURNING attach_id;

-- Load attachment for download. Authorization is checked in service before streaming.
SELECT
    attach_id, doc_no, file_name, mime_type, file_size,
    storage_provider, bucket, object_key, sha256, scan_status
FROM sgi_document_attachments
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
    for no in ["2", "3", "4", "5", "6", "7", "8", "8b", "9", "10", "11", "12"]:
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
    owner = JOB_OWNER_OVERRIDES.get(no, BANK_BE_OWNER)
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
        "Argument รับผ่าน `INPUT` (JSON) — local ใช้ env `JOB_NAME`/`INPUT` · AWS Batch ใช้ `argv[3]`/`argv[2]` · ดูหัวข้อ 5.95 · ไม่มีตาราง job_configs และไม่มีหน้าจอควบคุม (หน้า Flow Batch Job ในกลุ่มเมนู Flow เหลือแค่ Flowchart + Database ที่ใช้ · 2026-08-06)",
        "ตารางเวลาตั้งที่ **AWS Batch scheduled event** (repo ไม่มี `@Cron`) — **ยกเว้น job ที่เป็น event-driven (ดูหัวข้อ Config Schema ของ job นั้น) ซึ่งห้ามตั้ง schedule** · ทุก job ถูกบันทึกลง `integration_log` โดย `main.ts` อัตโนมัติ + structured log `BATCH_START`/`BATCH_END` พร้อม `runId`",
    ]
    if no == "8b":
        scope.append("Depends on LLDD-BE-API-Workflow-Instances; Job 8b เรียก Workflow Engine ภายในและไม่ duplicate Gen Flow Gate logic")
    return Topic(
        f"Jobs/LLDD-BE-Job-{no}-{sanitize_filename(job['name'])}",
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
            ("รันตามตารางเวลา", "CRON", f"scheduler → runner (job {no})", "อ่าน cron/พารามิเตอร์จาก backend config"),
            ("รันนอกรอบ (manual/rerun)", "CLI", f"CLI/ops runbook → runner (job {no})", "guard ไม่ให้รันซ้อนด้วย distributed lock"),
            ("แก้พารามิเตอร์/เปิด-ปิด job", "CONFIG", "แก้ backend config แล้ว deploy", "ไม่มี endpoint และไม่มีหน้าจอควบคุม — หน้า Flow Batch Job เป็น reference อย่างเดียว (2026-08-06)"),
            ("ตรวจผลการรัน", "LOG", "application log (structured)", "ไม่มีตาราง job_run_histories แล้ว · ผลการรับส่งไฟล์/ข้อความดูที่ sgi_interface_transactions"),
        ],
        [],
        flow,
        [
            "พารามิเตอร์รับผ่าน `INPUT` (JSON) และ config ของ repo — เปลี่ยนค่าโดย deploy ไม่ใช่ผ่าน API/หน้าจอ · **ตารางเวลาตั้งที่ AWS Batch scheduled event ไม่ใช่ `@Cron` ในโค้ด**",
            "การรันต้องตรวจ enabled flag ใน config · **การกันรันซ้อนพึ่ง AWS Batch queue เป็นหลัก** — advisory lock เป็นของใหม่ที่ต้องสร้างเองถ้างานนั้นรับความเสี่ยงรันซ้อนไม่ได้",
            "ทุกรอบต้องเขียน application log แบบ structured (`BATCH_START`/`BATCH_END` + `runId` — `src/main.ts` ทำให้แล้ว) และบันทึกลง `integration_log` อัตโนมัติ · error ต้องส่ง EM-07",
            "DB/table mapping ใช้เป็น reference สำหรับ implement Job เท่านั้น ไม่ใช่งานสร้างหน้า Database",
            "รองรับ rerun rule และ risk note ตาม runbook",
        ],
        [
            "รันตามตารางเวลาแล้วผลถูกต้องบน fixture",
            "รันนอกรอบผ่าน CLI ได้ผลเดียวกับ cron",
            "สั่งรันซ้อนขณะกำลังรัน → runner ปฏิเสธ (lock ทำงาน)",
            "แก้ config แล้ว deploy → รอบถัดไปใช้ค่าใหม่",
            "job throw error → EM-07 ออก และ log มีบรรทัด error",
            "ตรวจผลกระทบตารางตาม R/W mapping reference",
        ],
        db_tables=db_tables,
        flow_diagram=flow_file,
    )


def be_job_topics() -> list[Topic]:
    return [job_topic(job) for job in load_batch_jobs()]


# --------------------------------------------------------------------------------------
# 2026-08-07: เอกสาร BE ที่เพิ่มใหม่ 4 ฉบับ (Database-Structure · Data-Migration-Cutover ·
# Integration-SBP-Platform · Workflow-Engine-Definition) — ทั้ง 4 ฉบับไม่มี REST endpoint
# ของตัวเอง จึงไม่ผ่าน skeleton generator (ดู SKELETON_SKIP_FILES) และใช้เนื้อหาจาก
# topic_extra_blocks() แทน
# --------------------------------------------------------------------------------------
def new_be_design_topics() -> list[Topic]:
    return [
        Topic(
            "BE/LLDD-BE-Database-Structure",
            "LLDD BE - Database Structure and Deployment",
            "BE",
            4.0,
            24,
            BE_OWNER_PEERAKORN,
            "กำหนด DDL ของ target schema 21 ตาราง พร้อม index/constraint/seed และสคริปต์ deploy ให้ทุกเอกสาร BE อ้างอิงโครงเดียวกัน — เป็น blocker ที่ต้องปิดในสัปดาห์แรก",
            [],
            [
                "DDL ครบ 21 ตารางของ target schema (โซน A 8 · โซน B 9 · โซน C 3)",
                "Index, unique/partial index, check constraint และ FK ที่ต้องมีก่อน SIT",
                "Seed data ที่ต้องมีก่อนเปิดระบบ (sgi_external_factors · sgi_competitors) — decisions ไป seed ที่ common_code ของระบบเดิม (DP-9)",
                "สคริปต์ deploy/rollback ต่อ environment และลำดับการรันตาม dependency",
                "ตารางที่ห้ามสร้างซ้ำเพราะระบบ SBP เดิมมีอยู่แล้ว (workflow engine 13 ตาราง · store/mas_store · common_code · mas_param · business_user · email_template · fcs_qssi_score)",
                "ระบุข้อกำหนดด้านโครงสร้างข้อมูลที่ต้องยึดตอน implement",
            ],
            [
                ("naming", "lower_snake_case", "บังคับทุกตาราง/คอลัมน์ใหม่", "ห้ามใช้ชื่อไทย/CamelCase หรือชื่อ legacy แบบ FGI_/Comp*"),
                ("store_code / new_store_code", "VARCHAR(5)", "ห้ามเก็บเป็น numeric", "ต้องคง leading zero (00788) ทุกตาราง"),
                ("doc_no", "VARCHAR(12) รูปแบบ YYYY/xxxxx", "unique ต่อปี", "ออกเลขผ่าน sgi_document_running_numbers แบบ atomic"),
                ("amount / percent", "NUMERIC(15,2) / NUMERIC(5,2)", "amount >= 0 · percent 0-100", "ผลรวม compensate_percent ต่อเอกสารต้อง = 100"),
                ("period key", "CHAR(7) 'YYYY-MM' (ค.ศ.)", "ค่าคงรูปแบบเดียวทั้ง schema", "แสดงผลเป็น ค.ศ. เช่นกัน"),
                ("fcs_qssi_score", "ตารางเดิมของ sps_store", "ห้าม CREATE TABLE ใหม่", "มีอยู่จริง 24,284,545 แถว + import pipeline ใช้งานอยู่ (POST /performance/import-qssi · staging fcs_tmp_qssi_score)"),
            ],
            [
                ("รัน DDL baseline", "deploy script", "psql -f 01_schema.sql", "สร้าง 20 ตารางตามลำดับ dependency"),
                ("รัน index/constraint", "deploy script", "psql -f 02_index.sql", "index/unique/check ครบก่อนเปิด SIT"),
                ("รัน seed", "deploy script", "psql -f 03_seed.sql", "master ที่ระบบต้องมีตั้งแต่วันแรก"),
                ("Rollback", "deploy script", "psql -f 99_rollback.sql", "DROP ย้อนลำดับ · ห้ามแตะตารางของระบบ SBP เดิม"),
            ],
            [],
            [
                "ยืนยันรายการ 21 ตารางกับ database.md และ LLDD-Database ให้ตรงกันก่อนเขียน DDL",
                "เขียน 01_schema.sql เรียงตาม dependency: โซน C master -> โซน A pipeline -> โซน B document",
                "เขียน 02_index.sql แยกไฟล์ เพื่อให้ rerun/เพิ่ม index ภายหลังได้โดยไม่แตะ schema",
                "เขียน 03_seed.sql เฉพาะ master ที่ระบบต้องมีตั้งแต่วันแรก",
                "ตรวจว่าไม่มี CREATE TABLE ของตารางที่ระบบ SBP เดิมมีอยู่แล้ว",
                "รันบน environment ว่างแล้ว dump schema กลับมาเทียบกับ DDL ต้นฉบับ",
                "ส่งมอบ DDL ให้ Data-Migration-Cutover ใช้เป็นปลายทาง",
            ],
            [
                "DDL รันบนฐานว่างได้ครบในครั้งเดียวโดยไม่มี error ลำดับ FK",
                "จำนวนตารางที่สร้างจริง = 20 ตาราง (21 ในโครง ลบ fcs_qssi_score ที่ reuse) ตรงกับ database.md",
                "ไม่มี CREATE TABLE ของ workflow engine, store master, common_code, mas_param, business_user, email_template หรือ fcs_qssi_score",
                "ทุกตารางมี PK และทุก FK ชี้ไปตารางที่มีอยู่จริงในสคริปต์เดียวกัน",
                "rollback script ลบเฉพาะตารางของ SGI",
                "ข้อกำหนดด้านโครงสร้างข้อมูลทุกข้อในหัวข้อ 5.4 ระบุเป็นสิ่งที่ต้องทำ ไม่มีทางเลือกค้าง",
            ],
            [
                "รัน 01+02+03 บนฐานว่าง แล้ว dump schema เทียบกับต้นฉบับ",
                "รัน 01 ซ้ำครั้งที่สอง ต้อง fail แบบชัดเจน ไม่สร้างของซ้ำเงียบ ๆ",
                "ทดสอบ insert เอกสารที่ compensate_percent รวมไม่ครบ 100 ต้องถูก block",
                "ทดสอบ insert store_code '00788' แล้วอ่านกลับได้ leading zero ครบ",
                "ทดสอบออกเลข doc_no พร้อมกัน 20 request ต้องไม่ซ้ำ",
                "grep หา CREATE TABLE ของตาราง reuse ต้องได้ 0 บรรทัด",
            ],
            db_tables=[
                ("20 target tables (โซน A/B/C)", "W", "สร้างจาก DDL baseline ของเอกสารนี้"),
                ("workflow engine 13 ตาราง (sps_store)", "R", "ห้ามสร้างซ้ำ — ใช้ของ @srm/glb-workflow"),
                ("fcs_qssi_score (sps_store)", "R", "ห้ามสร้างซ้ำ — 24,284,545 แถว + import pipeline ใช้งานอยู่"),
                ("mas_param / common_code / business_user / email_template (sps_store)", "R", "ค่ากำหนดกลาง/master/ตัวตน/เทมเพลตอีเมลของระบบ SBP เดิม"),
            ],
        ),
        Topic(
            "BE/LLDD-BE-Data-Migration-Cutover",
            "LLDD BE - Data Migration and Cutover",
            "BE",
            5.0,
            30,
            BE_OWNER,
            "ออกแบบการย้ายข้อมูลจากระบบเดิม (Oracle FCS_FRN ฝั่ง FGI/FCS + SQL Server CPA_FRN_FGI ฝั่ง K2) เข้าสู่ target schema ของ SGI พร้อมแผน cutover, reconcile และ rollback",
            [],
            [
                "Source-to-target mapping ระดับตาราง/คอลัมน์ (ORA FCS_FRN · MSSQL CPA_FRN_FGI -> 21 ตาราง)",
                "การแปลงคีย์: polymorphic TRANSACTION_PK -> typed FK · CompDocumentID -> doc_no · IMPACT_PROCESS_ID -> impact_process_id",
                "แผน cutover เป็นรอบ (dry-run -> delta -> freeze -> final) และ rollback",
                "Reconcile: นับแถว ยอดเงิน และ checksum ต่อโซน",
                "การย้าย workflow ที่ยังวิ่งอยู่เข้าสู่ @srm/glb-workflow",
                "ระบุข้อกำหนดด้าน migration ที่ต้องยึดตอนย้ายข้อมูลจริง",
            ],
            [
                ("source ORA", "Oracle FCS_FRN", "read-only ตอน migrate", "ฝั่ง FGI/FCS pipeline (FGI_IMPACT_* · FCS_QSSI_SCORE · FGI_CONFIRM_RECEIVE_DATA)"),
                ("source MSSQL", "SQL Server CPA_FRN_FGI", "read-only ตอน migrate", "ฝั่ง K2 document (CompensateFlow · CompensateHistory · ImpactProfile · ImpactCostDetail · RunningNumber)"),
                ("business key", "impacted_store_code + month + year", "ต้อง unique หลังแปลง", "ใช้เป็นคีย์ dedup ตอน load โซน A"),
                ("doc_no", "YYYY/xxxxx (**ค.ศ.** · มติ 2026-08-06)", "ต้อง unique", "แปลงจาก CompDocumentID — ถ้าของเดิมเป็น พ.ศ. ต้องแปลงเป็น ค.ศ. ตอน migrate · ตั้งค่า sgi_document_running_numbers.last_running_no ต่อปี (ค.ศ.) ให้ตรงกับเลขสูงสุดที่ย้ายมา"),
                ("date", "เก็บเป็น ค.ศ. ใน DB", "แปลงจาก พ.ศ. ของระบบเดิมด้วย toAD()", "FE แสดง ค.ศ. เป็นค่าเริ่มต้น"),
                ("store_code", "VARCHAR(5)", "lpad 5 หลัก", "ระบบเดิมบางตารางเก็บเป็นตัวเลข ทำให้ leading zero หาย"),
            ],
            [
                ("Dry-run migrate", "runbook", "สคริปต์ ETL โหมด --dry-run", "ได้รายงานจำนวนแถว/แถวที่ reject โดยไม่เขียนปลายทาง"),
                ("Full load", "runbook", "สคริปต์ ETL โหมด --full", "โหลดข้อมูลย้อนหลังทั้งหมดเข้า target schema"),
                ("Delta load", "runbook", "สคริปต์ ETL โหมด --delta --since", "โหลดเฉพาะรายการที่เปลี่ยนหลัง full load"),
                ("Reconcile", "runbook", "สคริปต์ reconcile", "เทียบจำนวนแถว/ยอดเงินต้นทาง-ปลายทางต่อโซน"),
                ("Rollback", "runbook", "restore snapshot ก่อน cutover", "กลับไปใช้ระบบเดิมได้ภายในหน้าต่างที่ตกลง"),
            ],
            [],
            [
                "ยืนยันปลายทางกับ LLDD-BE-Database-Structure (DDL ต้องนิ่งก่อน)",
                "ทำ profiling ต้นทาง: นับแถว/ค่า null/ค่าซ้ำของทุกตารางที่จะย้าย",
                "เขียน mapping ต่อคอลัมน์ พร้อมกฎแปลง (พ.ศ.->ค.ศ. · lpad store_code · polymorphic key -> typed FK)",
                "Dry-run บน environment ทดสอบ แล้วแก้ reject rule จนแถวที่ reject อธิบายได้ทุกแถว",
                "Full load + reconcile ครั้งที่ 1",
                "Freeze ระบบเดิม -> delta load -> reconcile ครั้งสุดท้าย",
                "ย้าย workflow ที่ยังวิ่งอยู่: initialize transaction ใน @srm/glb-workflow ให้ตรง state ปัจจุบันของเอกสาร",
                "เปิดระบบใหม่ · เก็บ snapshot ก่อน cutover ไว้สำหรับ rollback ตามหน้าต่างที่ตกลง",
            ],
            [
                "จำนวนแถวปลายทางเท่าต้นทางทุกตาราง หรืออธิบายส่วนต่างได้ทุกแถว",
                "ยอดเงินชดเชยรวมต้นทาง = ปลายทาง (เทียบต่อปีและต่อร้าน)",
                "ไม่มี store_code ที่ leading zero หาย",
                "ไม่มี doc_no ซ้ำ และ sgi_document_running_numbers ต่อปีตรงกับเลขสูงสุดที่ย้ายมา",
                "เอกสารที่ยังไม่จบ flow เปิดในระบบใหม่แล้วอยู่ state เดิมและมีผู้อนุมัติปัจจุบันถูกคน",
                "มี rollback plan ที่ทดสอบแล้วอย่างน้อย 1 ครั้ง",
            ],
            [
                "dry-run แล้วรายงาน reject อธิบายได้ครบทุก reason code",
                "full load + reconcile ผ่านบน dataset จริงชุด staging",
                "delta load ซ้ำ 2 รอบต้อง idempotent (ไม่เกิดแถวซ้ำ)",
                "ทดสอบร้านที่ store_code ขึ้นต้นด้วย 0",
                "ทดสอบเอกสารที่มีหลายรอบ (round_no/loop_no) ว่าลำดับไม่สลับ",
                "ทดสอบ rollback: restore snapshot แล้วระบบเดิมกลับมาใช้งานได้",
            ],
            db_tables=[
                ("ORA FCS_FRN (FGI_IMPACT_* · FCS_QSSI_SCORE · FGI_CONFIRM_RECEIVE_DATA)", "R", "ต้นทางฝั่ง FGI/FCS"),
                ("MSSQL CPA_FRN_FGI (CompensateFlow · CompensateHistory · ImpactProfile · ImpactCostDetail · RunningNumber)", "R", "ต้นทางฝั่ง K2 document"),
                ("20 target tables (โซน A/B/C)", "W", "ปลายทางตาม DDL ของ LLDD-BE-Database-Structure"),
                ("workflow_transaction / workflow_approver / workflow_history (sps_store)", "W (ผ่าน lib)", "เปิด transaction ให้เอกสารที่ยังไม่จบ flow ด้วย initializeWorkflow() + addPreApprover() — **ห้าม INSERT ตรง** แม้เป็นสคริปต์ย้ายข้อมูล"),
                ("fcs_monthly_sales (sps_store)", "R", "ใช้ cross-check ยอดขายรายเดือนเท่านั้น — แทนยอดขายรายวันไม่ได้"),
            ],
        ),
        Topic(
            "BE/LLDD-BE-Integration-SBP-Platform",
            "LLDD BE - Integration with SBP Platform",
            "BE",
            3.0,
            18,
            BE_OWNER,
            "กำหนดวิธีที่ SGI ต่อกับแพลตฟอร์ม SBP เดิม: BFF header/ตัวตน, response envelope, ไฟล์บน S3, อีเมลผ่าน @gosoft-sbp/email-lib และค่ากำหนดกลางใน mas_param/common_code — เป็น blocker ที่ต้องปิดในสัปดาห์แรก",
            [],
            [
                "ตัวตนผู้ใช้จาก BFF header 6 ตัว (x-api-key · x-user-id · x-user-group-id · x-user-full-name · x-user-permissions · accept-language) — ดูค่าตัวอย่างจริงใน 5.1",
                "Response envelope ของ store-backend: {success, data} / {success:false, data:null, error:{code,message}}",
                "ไฟล์แนบผ่าน service S3 เดิม (POST /statement/upload-file-aws · download-file-aws)",
                "อีเมลผ่าน @gosoft-sbp/email-lib + ตาราง email_template / email_sent",
                "ค่ากำหนดกลางที่ sps_store.mas_param และ sps_store.common_code — 🔴 ค่าของ SGI (SGI_APPROVE_LIMIT ฯลฯ) ยังไม่มีในระบบจริง ต้อง seed เองตอน setup (ดู 5.5)",
                "การใช้ตาราง master ของระบบเดิม (store/mas_store · business_user · common_code) และปริมาณข้อมูลจริง",
            ],
            [
                ("x-api-key", "string", "required ทุก request จาก BFF", "ตรวจที่ guard ของ store-backend ก่อนเข้า controller"),
                ("x-user-id", "string เช่น `0000123456`", "required ทุก endpoint ของผู้ใช้ — ไม่มี = 401", "created_by/updated_by ของ SGI + sgi_consideration_logs.consider_by + ส่งเป็น userId เข้า engine · 🔴 ห้ามเขียน current_approver เอง (engine เป็นคนเขียน)"),
                ("x-user-group-id", "string เช่น `08`", "required เมื่อ endpoint ต้องรู้ section", "map เป็น section_code ของ workflow (06/08/01/02/03) — เป็นด่านหลักในการตัดสินสิทธิ์เขียน"),
                ("x-user-full-name", "string · **%-encoded**", "ไม่บังคับ", "ชื่อผู้ทำรายการใน timeline/อีเมล · 🔴 ต้อง decodeURIComponent ก่อนใช้เสมอ · ไม่มีให้ fallback เป็น x-user-id"),
                ("x-user-permissions", "string (serialized) · รูปแบบไม่ผูกเป็นสัญญา", "**ด่านเสริม ไม่ใช่ด่านเดียว**", "สิทธิ์ต่อ URL จาก auth-backend — SGI ไม่คำนวณสิทธิ์เมนูเอง · parse ไม่ผ่านให้ตกไปใช้ x-user-group-id + สถานะเอกสาร (ดู 5.1.2)"),
                ("accept-language", "string เช่น `th`", "ไม่บังคับ", "ภาษาข้อความ error — default th (ไทย verbatim ตาม SRS)"),
                ("envelope", "{success, data}", "บังคับทุก endpoint", "ResponseInterceptor ห่อให้แล้ว — service ห้ามห่อซ้ำ"),
                ("envelope ที่ผ่าน BFF", "{success, data, requestId}", "**BFF ต้อง unwrap ของ store-backend 1 ชั้นก่อนคืน**",
                 "🔴 ยืนยันจากโค้ดจริง 2026-09-04: BFF มี `ResponseInterceptor` ระดับ global "
                 "(`src/common/interceptors/response.interceptor.ts`) ที่ห่อผลของ controller เป็น `{success, data, requestId}` เสมอ · "
                 "แต่ `client-service.abstract.ts` คืน `response.data` ซึ่งเป็น envelope ของ store-backend อยู่แล้ว "
                 "→ ถ้าส่งต่อดิบ ๆ interceptor จะเห็นคีย์ `success` แล้วห่อซ้ำ FE ได้ `data.data.data` · "
                 "**สัญญา: `SgiClientService` คืน `response.data.data`** แล้ว FE อ่าน `data.data` ชั้นเดียว · "
                 "`requestId` เป็นของ BFF ใช้อ้างอิงตอนแจ้งปัญหา store-backend ไม่ต้องสร้างเอง"),
                ("error", "{success:false, data:null, error:{code,message}}", "message ภาษาไทย verbatim ตาม SRS", "โยนผ่าน HttpException เท่านั้น"),
                ("sps_store.mas_param", "key-value ของระบบเดิม", "**runtime = read-only · เขียนเฉพาะตอน seed/cutover**", "93,763 แถว · ไม่มี PK/unique → อ่านต้อง WHERE active_flag='Y' + LIMIT 1 เสมอ · ✅ ค่า SGI_* seed ลงฐาน dev แล้ว 2026-09-16 · uat/prod ยังต้อง seed (5.5.2)"),
                ("sps_store.common_code / common_code_type", "code master ของระบบเดิม", "**runtime = read-only · เขียนเฉพาะตอน seed/cutover**", "2,641 / 380 แถว · code_type เป็น varchar(20) · ต้อง INSERT common_code_type ก่อน · ✅ SGI_APPROVE_LIMIT seed ลง dev แล้ว 2026-09-16 · uat/prod ยังต้อง seed (5.5.2)"),
            ],
            [
                ("อ่านตัวตนผู้ใช้", "ทุก request", "BffUserGuard อ่าน BFF header (5.1.3)", "req.user = {userId, groupId, fullName, permissions} — fullName decode แล้ว"),
                ("อัปโหลดไฟล์แนบ", "ปุ่มแนบไฟล์", "POST /statement/upload-file-aws (ระบบ SBP เดิม)", "ได้ objectKey กลับมาเก็บใน sgi_document_attachments"),
                ("ดาวน์โหลดไฟล์แนบ", "ปุ่มดาวน์โหลด", "POST /statement/download-file-aws (ระบบ SBP เดิม)", "stream ไฟล์ผ่าน BE · ห้ามคืน objectKey ให้ FE"),
                ("ส่งอีเมล", "หลัง action สำเร็จ", "@gosoft-sbp/email-lib + email_template", "บันทึกผลที่ email_sent"),
                ("อ่านค่ากำหนดกลาง", "ตอน bootstrap/ตอนใช้งาน", "mas_param / common_code", "ห้าม hardcode วงเงินอนุมัติในโค้ด"),
            ],
            [],
            [
                "BFF forward request พร้อม header ตัวตนมาที่ store-backend",
                "Guard ตรวจ x-api-key แล้ว map header เป็น user context",
                "Controller/Service ทำงานโดยใช้ user context (ไม่มี JWT ของ SGI เอง)",
                "ผลลัพธ์ถูกห่อด้วย ResponseInterceptor เป็น {success, data}",
                "ไฟล์แนบวิ่งผ่าน service S3 เดิม · เก็บเฉพาะ metadata ใน SGI",
                "อีเมลส่งผ่าน email-lib โดยอ่าน template จาก email_template และบันทึกผลที่ email_sent",
                "ค่ากำหนด/วงเงินอ่านจาก mas_param และ common_code ทุกครั้ง ไม่ cache ข้ามรอบโดยไม่มี TTL",
            ],
            [
                "ไม่มี endpoint ใดของ SGI ออก/ตรวจ JWT เอง",
                "ทุก response ผ่าน envelope เดียวกับ store-backend",
                "ไม่มี credential ของ S3/SMTP อยู่ในโค้ดหรือ config ของ SGI",
                "วงเงินอนุมัติ เกณฑ์เดียว 100,000 อ่านจาก common_code (SGI_APPROVE_LIMIT) ไม่ hardcode",
                "objectKey ไม่ถูกส่งออกไปที่ FE",
                "x-user-full-name ถูก decodeURIComponent ก่อนใช้ทุกจุด — ไม่มี %E0%B8 หลุดไปที่ timeline/อีเมล",
                "สิทธิ์เขียนตัดสินจาก x-user-group-id + สถานะเอกสาร + getTransaction() ของ engine — ไม่ใช้ x-user-permissions เป็นด่านเดียว",
                "ค่า SGI_* ใน common_code/mas_param ถูก seed ด้วย script ที่ rerun ได้ (NOT EXISTS guard) ไม่ใช่ INSERT มือ",
                "ข้อกำหนดด้าน integration ทุกข้อในหัวข้อ 5.6 ถูกระบุเป็นสิ่งที่ต้องทำ ไม่มีทางเลือกค้างให้ dev เลือกเอง",
            ],
            [
                "ไม่ส่ง x-api-key ต้องได้ 401 ตาม envelope มาตรฐาน",
                "ส่ง x-api-key ผิดค่า ต้องได้ 401 (เทียบ X_API_KEY ตรง ๆ) และ **ห้ามมีค่า key โผล่ใน log/error**",
                "ไม่ส่ง x-user-id ต้องได้ 401 · ส่ง x-user-group-id ที่ไม่ตรง section ของเอกสาร ต้องได้ 403",
                "error ที่โยนออกมาต้องเป็น {success:false, data:null, error:{code,message}} และ message เป็นไทย verbatim",
                "upload ไฟล์ 6MB ต้องถูก block ก่อนขึ้น S3 · download ไฟล์ของเอกสารที่ผู้ใช้ไม่เกี่ยวข้องต้องถูก block",
                "ส่งอีเมลสำเร็จแล้วมีแถวใน email_sent (คอลัมน์ผู้ส่งคือ send_by)",
                "เปลี่ยนค่า SGI_APPROVE_LIMIT ใน common_code แล้ว route อนุมัติเปลี่ยนตามโดยไม่ deploy",
                "x-user-full-name เป็น %-encoded ต้อง decode ถูก · ส่งค่าพัง decode ไม่ผ่านต้องไม่ throw",
                "x-user-permissions ว่าง/parse ไม่ผ่าน ต้องไม่ throw แต่ตกไปใช้ด่าน group + สถานะเอกสาร",
                "objectKey ต้องไม่โผล่ใน response ของทุก endpoint ที่ FE เรียก",
                "รัน seed script ซ้ำ 2 ครั้ง ต้องไม่เกิดแถวซ้ำใน common_code/mas_param (ไม่มี unique กันให้)",
            ],
            db_tables=[
                ("mas_param (sps_store)", "R (+ W ครั้งเดียวตอน seed)", "ค่ากำหนดกลาง 93,763 แถว · runtime อ่านอย่างเดียว · ✅ ค่า SGI_* seed ลงฐาน dev แล้ว 2026-09-16 · uat/prod ยังต้อง seed (5.5.2)"),
                ("common_code / common_code_type (sps_store)", "R (+ W ครั้งเดียวตอน seed)", "2,641 / 380 แถว · 🔴 `SGI_APPROVE_LIMIT` / `SGI_DECISION` / `SGI_DATASOURCE` **ยังไม่มีในระบบจริง** ต้อง seed ตอน setup (5.5.2) · code_type เป็น varchar(20)"),
                ("email_template (sps_store)", "R", "85 แถว · SGI/lib อ่านอย่างเดียว — seed 8 แถวของ SGI ทำครั้งเดียวตอน migration ไม่ใช่ runtime"),
                ("email_sent (sps_store)", "W (โดย email-lib)", "5,392 แถว · lib เขียน log ให้เอง SGI ไม่ INSERT เอง (⚠️ คอลัมน์ผู้ส่งคือ send_by)"),
                ("business_user (sps_store)", "R", "12,759 แถว · ข้อมูลผู้ใช้/ผู้อนุมัติ"),
                ("store / mas_store (sps_store)", "R", "19,402 / 19,647 แถว · master ร้าน"),
                ("sgi_document_attachments (SGI)", "R/W", "metadata ไฟล์แนบ · ไฟล์จริงอยู่บน S3 ของระบบเดิม"),
            ],
        ),
        Topic(
            "BE/LLDD-BE-Workflow-Engine-Definition",
            "LLDD BE - Workflow Engine Definition",
            "BE",
            2.0,
            12,
            BE_OWNER_PEERAKORN,
            "**สร้างข้อมูลนิยาม workflow ลงฐานข้อมูลของ engine** — ระบุว่า flow ของ SGI มีกี่ step แต่ละ step ทำอะไร ใครทำได้ กดปุ่มไหนแล้วไป state ใด "
            "โดย register version/state/status/event/route/group/part ของ `@srm/glb-workflow` ตามสัญญาในเอกสารของ lib เอง "
            "(`docs/TSM-SRM-LLDD-SBP-workflow-1.2-full.md` — แปลงจาก `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx`) · "
            "**เป็นงานตั้งต้นที่ต้องเสร็จก่อน** ฝั่ง BE คนอื่นจึงจะเรียก `initializeWorkflow` และ `eventWorkflow` (trigger event) ได้ — blocker ของสัปดาห์แรก",
            [],
            [
                "ลงทะเบียน workflow version ของ SGI 1 version (url_main + url_param_mapping)",
                "**ผลลัพธ์ที่ส่งมอบคือ seed script/มัยเกรชันของข้อมูลนิยาม** ไม่ใช่โค้ดเรียก engine — ทีมอื่นเรียก engine ต่อจากนิยามชุดนี้",
                "**จำนวน step ที่ต้องสร้าง = 6 state** — 5 ขั้นทำงาน (`06` รอฝ่าย SBP DSA → `08` รอเจ้าหน้าที่ SBP DSA → `01` รอหน่วยงานส่งเสริมธุรกิจ SBP → `02` รอ GM → `03` รอ AVP) + **1 state จบ** (`99` เสร็จสิ้นดำเนินการ) · `state_id` เป็น running ตาม version ตามกติกาของ engine (v1 → 10001+)",
                "**จำนวน route ที่ต้องสร้าง = 12 เส้น** ตาม Canonical Workflow Transition Matrix ใน `LLDD-BE-API-Document-Workflow-Actions` §5.1 (รวมเส้นข้ามขั้น 06→01 · เส้นจบทันทีเมื่อ เห็นควรไม่ชดเชย ที่ 01/02 · เส้นแตกตามวงเงิน 100,000 ที่ 02 และเส้นส่งกลับ)",
                "**ตารางที่ต้อง seed = 10 ตาราง** จาก 13 ตารางของ engine (`sps_store`) ตาม `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` §4 — อีก 3 ตารางเป็นรันไทม์ที่ engine เขียนเอง",
                "ขอบเขตหยุดที่ข้อมูลนิยาม: **ไม่รวม** `initializeWorkflow` (เปิด instance · อยู่ใน LLDD-BE-API-Workflow-Instances) และ **ไม่รวม** `eventWorkflow`/trigger event (อยู่ใน LLDD-BE-API-Document-Workflow-Actions)",
                "นิยาม state/status 5 ขั้น 06 -> 08 -> 01 -> 02 -> 03 และปลายทางจบ flow",
                "นิยาม route ของทุกปุ่ม · วงเงินอนุมัติ เกณฑ์เดียว 100,000 **อ่านจาก `common_code` (`SGI_APPROVE_LIMIT`) ที่เดียว** — ตัวอย่าง `condition_json` ในเอกสารนี้แสดงรูปแบบเท่านั้น",
                "ผู้อนุมัติของแต่ละขั้นผูกด้วย **`addPreApprover()` รายคน** — ไม่ใช้ workflow_group / workflow_group_map (ดูหัวข้อ 5.6)",
                "การคุมการแสดงผล/แก้ไขรายส่วนใช้ **`visibleSections` / `editableSections` ของ SGI** — ไม่ใช้ workflow_part / workflow_part_display ของ engine (ดูหัวข้อ 5.6)",
                "ความเสี่ยงของ engine ที่ต้องออกแบบเผื่อ — ยึด 8 API ตามชีต Detail ของ LLDD ฝั่ง lib · `workflow_transaction` ไม่มี PK/index จึงต้องกันซ้ำที่ฝั่ง SGI",
            ],
            [
                ("versionId", "integer", "1 ระบบ = 1 version", "SGI ขอ version ใหม่จากทีมเจ้าของ library"),
                ("referenceId", "string unique", "required ตอน initializeWorkflow", "✅ DP-1 ปิดแล้ว 2026-08-17 = `sgi_compensation_documents.id` (surrogate) แปลงเป็น string — `reference_id` ของ engine เป็น varchar(255)"),
                ("state_id", "integer running ตาม version", "1 state มีได้หลาย status", "map 5 ขั้นของ SGI: 06/08/01/02/03 + state จบ"),
                ("event", "save|submit|approve|reject|cancel|sendback", "ค่าเริ่มต้นของ engine", "ปุ่มไทยของ SGI map ลง event เหล่านี้ผ่าน common_code (code_type=SGI_DECISION) — ตาราง decisions ถูกตัดตามมติ DP-9 (2026-08-10)"),
                ("condition_json", '{"field","operator","value"}', "operator: == != > < >= <=", 'ใช้ {"field":"amount","operator":"<","value":100000} แยก route GM/AVP'),
                ("eventParam", "object", "ส่งมาพร้อม event", "SGI ส่ง {\"amount\": ยอดชดเชยรวม} ให้ engine เลือก route เอง"),
                ("part_display_type", "READ | WRITE", "SGI ไม่ใช้ตารางนี้ — บันทึกไว้เพื่อความครบถ้วนของนิยาม engine", "ไฟล์ต้นฉบับสะกดว่า WRTIE ทุกแถวของชีต sample data"),
                ("url_main / url_param_mapping", "string", "required ตอน register version", "ทำให้ inbox กลาง (GET /api/workflow/pending) ลิงก์กลับหน้าเอกสารของ SGI ได้"),
            ],
            [
                ("เปิด workflow", "BE `POST /sgi/workflow/instances` (Job 8b เป็นผู้เรียก REST)", "initializeWorkflow(versionId, userId, referenceId)", "สร้าง workflow_transaction ที่ initial state/status"),
                ("ระบุผู้อนุมัติล่วงหน้า", "หลังเปิด workflow", "addPreApprover(versionId, referenceId, stateId, approver, seq, userId)", "insert workflow_approver (approver_type = user เสมอ)"),
                ("กดผลพิจารณา", "ปุ่มบนหน้าเอกสาร", "eventWorkflow(... event, eventParam ...)", "เดิน state ตาม route ที่ตรง condition_json แล้วบันทึก workflow_history"),
                ("อ่านปุ่ม/สิทธิ์แสดงผล", "เปิดหน้าเอกสาร", "getPermissionEvents(versionId, referenceId, userData)", "คืน event[] + display[] (partId/partDisplayType ต่อ state)"),
                ("อ่านกล่องงาน", "หน้ารายการรอดำเนินการ", "getPendingFlowByUser(userData, versionId)", "คืนงานที่รอ user คนนั้น + url_main"),
                ("อ่านประวัติ", "แท็บประวัติ", "getHistory(versionId, referenceId)", "คืน timeline ต่อแถว"),
            ],
            [],
            [
                "ขอ workflow version ใหม่จากทีมเจ้าของ @srm/glb-workflow (1 ระบบ = 1 version)",
                "ลงทะเบียน state/status 5 ขั้นของ SGI + state จบ flow",
                "ลงทะเบียน route ทุกเส้น พร้อม seq · route ที่แตกตามวงเงินให้แยกด้วยค่าที่ SGI ส่งมา โดย**อ่านวงเงินจาก `common_code` (`SGI_APPROVE_LIMIT`)** ไม่ hardcode ลง condition_json",
                "ผูกผู้อนุมัติของแต่ละขั้นด้วย `addPreApprover()` ระบุรายคน — **ไม่ต้อง seed `workflow_group` / `workflow_group_map`**",
                "คงกลไก `visibleSections` / `editableSections` ของ SGI สำหรับคุมการแสดงผลรายส่วน — **ไม่ต้อง seed `workflow_part` / `workflow_part_display`**",
                "กรอก url_main / url_param_mapping ให้ inbox กลางลิงก์กลับหน้าเอกสารได้",
                "ทดสอบเดิน flow ครบทุก route บน environment ทดสอบ",
                "ส่งรายการความเสี่ยงของ engine (ตาราง 5.2) ให้ทีมเจ้าของ library รับทราบพร้อมสรุปการกันความเสี่ยงที่ฝั่ง SGI",
            ],
            [
                "SGI ไม่สร้างตาราง workflow ของตัวเองเลย — ใช้ engine 13 ตารางใน schema sps_store",
                "route ครอบคลุมทุกปุ่มบนหน้าเอกสาร และทุก route มี seq ที่ไม่ชนกัน",
                "วงเงินอนุมัติอยู่ที่ `common_code` (`SGI_APPROVE_LIMIT`) ที่เดียว — ห้ามเก็บซ้ำใน condition_json",
                "การแสดงผล/แก้ไขรายส่วนของหน้าเอกสารมาจาก visibleSections / editableSections ที่ API ของ SGI คืนมา ไม่ใช่จาก engine",
                "ทุก query ที่อ้าง workflow_transaction มีการกันซ้ำระดับ application และผ่านการประเมินต้นทุนแล้ว",
                "โค้ดเรียกเฉพาะ 8 function ตามชีต Detail ของ LLDD ฝั่ง lib ไม่มีชื่อ function นอกรายการ",
            ],
            [
                "initializeWorkflow ซ้ำด้วย referenceId เดิมต้องไม่เกิด transaction ที่สอง",
                "ยอดชดเชย 99,999 ต้องจบที่ GM · 100,000 ต้องวิ่งต่อ AVP (เกณฑ์เดียว · มติ 2026-08-18)",
                "ผู้ใช้ที่ไม่ใช่ current_approver ต้องไม่ได้ปุ่มใด ๆ จาก getPermissionEvents",
                "editableSections ที่ API คืนตอน state 01 ต้องมีเฉพาะส่วนที่ section 01 แก้ได้ (ร้านเปิดใหม่ · คู่แข่ง · ปัจจัย)",
                "getPendingFlowByUser ต้องคืน url_main ที่เปิดกลับหน้าเอกสารได้จริง",
                "เดิน flow จนจบแล้ว workflow_history มีครบทุกขั้น",
            ],
            db_tables=[
                # --- 4.1 ตารางนิยาม flow (config · seed ครั้งเดียวต่อระบบ) — SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md §4.1
                ("workflow (sps_store)", "W ครั้งเดียวตอน setup", "**1 แถว** — `workflow_name` = ระบบประกันรายได้ (SGI)"),
                ("workflow_version (sps_store)", "W ครั้งเดียวตอน setup", "**1 แถว** — 1 ระบบ = 1 version · ต้องมี `initial_state_id` (= ขั้น 06), `end_state_id` (= 99), `url_main`, `url_param_mapping` เพื่อให้ inbox กลางลิงก์กลับหน้าเอกสารได้ · **ขอเลข version จากทีมเจ้าของ library**"),
                ("workflow_state (sps_store)", "W ครั้งเดียวตอน setup", "**6 แถว = จำนวน step ของ flow** — 5 ขั้นทำงาน (06 · 08 · 01 · 02 · 03) + 1 ขั้นจบ (99) · `state_id` running ตาม version (v1 → 10001+)"),
                ("workflow_status (sps_store)", "W ครั้งเดียวตอน **setup** (งาน config ไม่ใช่โค้ดแอป)", "**6 แถว** — ชื่อสถานะเอกสารที่ผู้ใช้เห็น 1:1 กับ state (รอฝ่าย SBP DSA ดำเนินการ / รอเจ้าหน้าที่ SBP DSA ดำเนินการ / รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ / รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ / รอผู้บริหารสำนักบริหาร SBP ดำเนินการ / เสร็จสิ้นดำเนินการ) · engine รองรับ 1 state หลาย status<br>**ใช้ทำอะไร:** `workflow_route.to_status_id` ชี้มาที่ตารางนี้ และ `workflow_transaction.current_status_id` เก็บสถานะ**ปัจจุบันจริง**ของแต่ละเอกสาร · inbox กลาง (`getPendingFlowByUser`) แสดงชื่อจากตารางนี้ — **engine เป็นเจ้าของสถานะตอนรันไทม์** ส่วน `sgi_compensation_documents.status_code` เป็น**สำเนาที่ SGI ถือไว้เอง**เพื่อค้นหา/กรอง/ทำรายงาน โดยไม่ต้อง join ข้ามไปตาราง engine<br>🔴 **batch job ไม่แตะตารางนี้เลยแม้แต่ตัวเดียว** (มติ 2026-09-09 — workflow lib ใช้กับ flow K2 ฝั่ง BE/FE เท่านั้น · Job 8b เรียก REST `POST /api/v1/sgi/workflow/instances` แทน) · ไม่อยู่ใน `sgi_seed_data.sql` ด้วย เพราะไฟล์นั้นแตะเฉพาะ `sgi_*` + `common_code`/`mas_param`/`email_template`<br>⚠️ **ชื่อไทย 6 ค่านี้ต้องตรงกับ `common_code` (`code_type = SGI_DOC_STATUS`) เป๊ะ** — engine ถือ `status_id` (integer) ส่วนรหัส 2 ตัวอักษร (`06/08/01/02/03/99`) เป็นของ SGI ทั้งสองที่ต้อง seed จาก**รายการเดียวกัน** ห้ามพิมพ์ซ้ำด้วยมือ (`check_docs.py` กฎ #111 ดักไว้)"),
                ("workflow_event (sps_store)", "R (ใช้ค่า default ของ engine)", "`save` `submit` `approve` `reject` `cancel` `sendback` — ปุ่มไทยของ SGI map ลง 6 event นี้ผ่าน `common_code` (`code_type = SGI_DECISION`) · **ไม่ต้องเพิ่ม event ใหม่**"),
                ("workflow_route (sps_store)", "W ครั้งเดียวตอน setup", "**12 แถว = ทุกเส้นทางของ flow** ตาม Canonical Workflow Transition Matrix (`LLDD-BE-API-Document-Workflow-Actions` §5.1) — รวมเส้นข้ามขั้น 06→01 · เส้นจบทันทีเมื่อ *เห็นควรไม่ชดเชย* ที่ 01/02 · เส้นแตกตามวงเงิน 100,000 ที่ 02 (`condition_json`) และเส้นส่งกลับทุกขั้น · `seq` ห้ามชนกันภายใน from_state เดียวกัน"),
                # --- 4.2 ตารางกลุ่มผู้อนุมัติ — §4.2
                ("workflow_group (sps_store)", "— ไม่ใช้", "กลุ่มผู้อนุมัติต่อขั้น — **SGI ไม่ seed ตารางนี้** เพราะผูกผู้อนุมัติรายคนด้วย `addPreApprover` (หัวข้อ 5.6)"),
                ("workflow_group_map (sps_store)", "— ไม่ใช้", "map กลุ่ม → ผู้ใช้ · **SGI ไม่ seed ตารางนี้** (บันทึกไว้เพื่อความครบถ้วนของนิยาม engine)"),
                # --- 4.4 ตารางคุมการแสดงผล — §4.4
                ("workflow_part (sps_store)", "— ไม่ใช้", "ชื่อ component ของหน้าเอกสาร + `part_seq` — **SGI ไม่ seed ตารางนี้** เพราะคุมการแสดงผลด้วย visibleSections/editableSections"),
                ("workflow_part_display (sps_store)", "— ไม่ใช้", "`part_display_type` = READ / WRITE ต่อ (state, part) — **SGI ไม่ seed ตารางนี้**"),
                # --- 4.3 ตารางรันไทม์ (ไม่ seed) — §4.3
                ("workflow_transaction / workflow_history / workflow_approver (sps_store)", "R เท่านั้น (engine เขียนเอง)", "ข้อมูลรันไทม์ 19,327 / 38,010 / 96,542 แถว (ตรวจ 2026-08-07) — 🔴 **ห้าม INSERT/UPDATE ตรง** ต้องผ่าน `initializeWorkflow` / `eventWorkflow` / `addPreApprover` ของ lib เท่านั้น · DP-2: `workflow_transaction` ไม่มี PK และไม่มี index"),
            ],
        ),
    ]


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
                ("date/month", "ISO ค.ศ. YYYY-MM-DD / YYYY-MM", "payload uses CE", "แสดงผ่าน formatDateThai/formatMonthThai จุดเดียว — ค่าเริ่มต้นเป็น ค.ศ."),
                ("docNo", "YYYY/xxxxx ค.ศ.", "do not split except route params", "route ใช้ /documents/:year/:running แล้วประกอบ docNo"),
                ("result", "actionOptions[].**value** (ไม่ใช่ label)", "required before submit action", "ส่งเป็น payload `{result, comment}` เท่านั้น · **`result` = `actionOptions[].value`** — `label` เป็นข้อความบนปุ่มที่ยาวกว่า (เช่น label `ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ` → value `ส่งเจ้าหน้าที่ SBP DSA`) ส่ง label ไปจะไม่ตรง 7 ค่าของ enum"),
                ("ActionResponse", "{statusCode,nextSection,message}", "required after action", "invalidate detail/timeline/tasks แล้ว resolve label จาก /sgi/lookup/document-statuses"),
                ("envelope", "{success, data, requestId}", "BFF unwrap ของ store-backend แล้ว 1 ชั้น", "FE อ่าน `data.data` ชั้นเดียว (ยืนยันจากโค้ด BFF จริง 2026-09-04 · รายละเอียดเต็มอยู่ใน **LLDD-BE-Integration-SBP-Platform** หัวข้อ 5)"),
                ("MenuItem", "{menuCode,label,route,group}", "จาก GET /menus + GET /groups/current-user/permissions ของระบบเดิม (ผ่าน BFF)", "sidebar filter ด้วย menuCode จาก API; ไม่ hardcode role"),
                ("canEditSections", "string[]", "from document detail", "ใช้เปิด/ปิด section editor; FE ไม่คำนวณสิทธิ์เอง"),
            ],
            [
                ("Attach token", "ทุก API call", "shared/api/client.ts", "Authorization header จาก auth store"),
                ("Refresh token", "401 non-auth endpoint", "POST /api/v1/auth/refresh", "single-flight แล้ว replay request เดิม"),
                ("Show API error", "catch AxiosError", "apiErrorMessage()", "แสดงข้อความไทยจาก BE ตรง ๆ"),
                ("Render list", "GET list endpoint", "PageResponse<T>", "DataTable/Pager ใช้ shape เดียวกัน"),
                ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/sgi/document/{docNo}/actions", "ส่ง `{result, comment}` และ consume `{statusCode,nextSection,message}`"),
                ("Gate route/menu", "login/bootstrap", "GET /menus + GET /groups/current-user/permissions (ระบบเดิม ผ่าน BFF)", "สร้าง sidebar และ route guard จาก menuCode"),
            ],
            [
                ApiSpec("ALL", "/api/v1/sgi/*", "Error contract กลางสำหรับ FE ทุกหน้า", None, {"code": "VALIDATION", "message": "ข้อความภาษาไทยตรงตาม SRS"}),
                ApiSpec("GET", "/api/v1/sgi/*?page=1&size=20", "List/pagination contract กลาง", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/actions", "Document action contract ตัวอย่างเมื่อ currentSection=01 จึงเปลี่ยนไป 02; FE ห้ามส่งหรือคำนวณปลายทางเอง", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
            ],
            [
                "Bootstrap env and API client",
                "Login or restore session with refresh token",
                "Load GET /auth/profile + GET /users/current + GET /menus + GET /groups/current-user/permissions (ทั้งหมดเป็นของระบบเดิมผ่าน BFF)",
                "Render routes/sidebar from menu contract",
                "All feature hooks use shared API client and PageResponse/Error types",
                "Document action sends `{result, comment}` only and consumes `{statusCode,nextSection,message}`",
                "All display formatting goes through shared/lib/format.ts",
            ],
            [
                "ไม่มี feature ใดสร้าง axios instance เอง",
                "ทุก API error แสดง message จาก BE โดยไม่ paraphrase",
                "ทุก list endpoint ใช้ PageResponse shape เดียวกัน",
                "วันที่ใน payload และหน้าจอเป็น ค.ศ. จาก formatter กลาง (แสดง พ.ศ. เฉพาะจุดที่เปิด flag)",
                "Sidebar และ route access มาจาก GET /menus ของระบบเดิม ไม่ hardcode role",
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
                ApiSpec("GET", "/api/v1/sgi/lookup/document-statuses", "โหลดสถานะเอกสารสำหรับ dropdown/badge", {}, {"items": [{"code": "06", "label": "รอฝ่าย SBP DSA ดำเนินการ"}]}),
            ],
            ["Initialize app config", "Register SBP Mall routes", "Create shared API client", "Prepare constants/formatters", "Wire shared UI primitives"],
            ["ไม่มี screenshot หรือ dashboard behavior ในเอกสารนี้", "ทุก route ถูก register ผ่าน module registry", "API error shape ใช้ร่วมกัน", "ไม่มี dependency กับ Login/Auth ใหม่", "CSS responsive base พร้อม"],
            ["route registration", "API base missing", "status unknown", "mock response compatible", "shared formatter output"],
        ),
        Topic(
            "FE/LLDD-FE-Document-Lists",
            "LLDD FE - Document Lists",
            "FE",
            8.2,
            70,
            FE_OWNER,
            "สร้างหน้ารายการเอกสารรอดำเนินการและเอกสารที่เกี่ยวข้อง",
            ["k2-list-waiting-01.png", "k2-list-waiting-02.png", "k2-list-related-01.png"],
            ["Waiting list", "Related document list", "Search/filter/status filter", "Pagination/row action + เลือกหลายเอกสาร (bulk)", "Red flag (sales < 60 days) + rejected-ending rows ที่บทบาท 06 ต้องเห็น"],
            [
                ("docNo", "YYYY/xxxxx", "optional search", "ถ้าคลิก row ส่งไป detail"),
                ("year", "ค.ศ. YYYY", "required สำหรับ /sgi/document และ /sgi/report/status-summary",
                 "**ไม่มีช่องบนหน้าจอทั้งสองหน้า — FE เป็นผู้ใส่ให้**: หน้ารายการใช้ปีปัจจุบัน (ค.ศ.) · "
                 "หน้ารายงานใช้ปีของ `periodStatementFrom` ถ้าผู้ใช้ระบุ ไม่งั้นใช้ปีปัจจุบัน"),
                ("status", "status code/string", "optional single select",
                 "**เงื่อนไขต่อบทบาท (มติ 2026-09-01 · ทำในโปรโตไทป์แล้ว):** หน้า **รอดำเนินการ** แสดงตัวกรองนี้ "
                 "**เฉพาะบทบาท 06** เพราะ inbox ของ 08/01/02/03 มีสถานะเดียว (`รอ<บทบาท>ดำเนินการ`) ตัวกรองจึงไม่มีประโยชน์ — ซ่อนไปเลย · "
                 "ของบทบาท 06 ใส่ **เฉพาะ 3 ตัวเลือกที่บทบาทนี้เห็นจริง** เท่านั้น: `รอฝ่าย SBP DSA ดำเนินการ` · "
                 "`เสร็จสิ้นดำเนินการ + หยุดชดเชย (เปิดพิจารณาใหม่ได้)` · `เสร็จสิ้นดำเนินการ + ไม่ชดเชย` — "
                 "**ห้ามยกสถานะของบทบาทอื่นมาให้เลือกลอย ๆ** · หน้า **ที่เกี่ยวข้อง** ไม่ถูกกระทบ ยังแสดงตัวกรองครบทุกค่า · "
                 "สลับบทบาทแล้วต้อง rebuild ตัวเลือกใหม่และคงค่าที่เลือกไว้ถ้ายังมีอยู่ ไม่งั้น reset เป็น 'ทุกสถานะ'"),
                ("table.roundNo", "integer", "column 1", "ครั้งที่ (รอบชดเชยของร้าน)"),
                ("table.docNo", "YYYY/xxxxx", "column 2", "เลขที่เอกสารและลิงก์เปิด detail"),
                ("table.impactedStoreCode", "string 5 digits", "column 3", "รหัสร้านถูกกระทบ; คง leading zero"),
                ("table.impactedStoreName", "string", "column 4", "ชื่อร้านถูกกระทบ"),
                ("table.regionCode", "string", "column 5", "ภาค"),
                ("table.salesDeclinePercent", "decimal", "column 6", "ยอดขายที่ลดลง (%)"),
                ("table.totalCompensationAmount", "decimal", "column 7; >=0", "จำนวนเงินที่ชดเชย; format #,##0.00"),
                ("table.statusCode/statusName", "code + label", "column 8", "สถานะ; เก็บ code และ resolve label จาก dictionary"),
                ("table.daysPending", "integer", "column 9; >=0", "รอ (วัน)"),
                ("table.salesDataDays", "integer", "internal (ไม่ใช่คอลัมน์แสดง)", "<60 = แถวผิดปกติสีแดง (red-flag)"),
            ],
            [
                ("Search", "ปุ่มค้นหา", "GET /api/v1/sgi/document/tasks หรือ /sgi/document", "reload table"),
                ("Clear", "ปุ่มเคลียร์", "client state", "reset filters"),
                ("Open detail", "click row", "navigate /sgi/document/:docNo", "เปิดเอกสาร"),
            ],
            [
                ApiSpec("GET", "/api/v1/sgi/document/tasks", "รายการเอกสารรอดำเนินการ", {"status": "06", "keyword": "โลตัส", "regionCode": "BE", "storeType": "A", "createdFrom": "2026-06-01", "createdTo": "2026-06-30", "salesDeclineMin": 10, "salesDeclineMax": 80, "compensationMin": 0, "compensationMax": 500000, "daysPendingMin": 0, "daysPendingMax": 30, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 24, "items": [{"roundNo": 1, "docNo": "2026/00123", "impactedStoreCode": "01234", "impactedStoreName": "สาขาตัวอย่าง", "regionCode": "BE", "salesDeclinePercent": 12.5, "statusCode": "06", "currentOwner": "somchai.k", "statusName": "รอฝ่าย SBP DSA ดำเนินการ", "totalCompensationAmount": 48200.0, "daysPending": 3, "salesDataDays": 58}]}),
                ApiSpec("GET", "/api/v1/sgi/document", "ค้นหาเอกสารที่เกี่ยวข้อง ต้องระบุปี", {"year": 2026, "impactedStoreCode": "00788", "status": "06", "result": "APPROVE", "keyword": "โลตัส", "regionCode": "BE", "storeType": "A", "createdFrom": "2026-06-01", "createdTo": "2026-06-30", "salesDeclineMin": 10, "salesDeclineMax": 80, "compensationMin": 0, "compensationMax": 500000, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 342, "items": [{"roundNo": 2, "docNo": "2026/00124", "impactedStoreCode": "01235", "impactedStoreName": "สาขาตัวอย่าง 2", "regionCode": "BS", "salesDeclinePercent": 18.0, "statusCode": "99", "statusName": "เสร็จสิ้น", "totalCompensationAmount": 72500.0, "daysPending": 0, "salesDataDays": 60}]}),
            ],
            ["Read route mode", "Bind filter values", "Call list API", "Render table", "Apply abnormal row style", "Navigate to detail on row click"],
            ["ตาราง 9 คอลัมน์หลักครบ", "ปีเป็น required เมื่อใช้ /sgi/document", "ยอดขายไม่ครบ 60 วันแสดงแดง", "pagination คง filter เดิม"],
            ["ค้นหาด้วย docNo", "filter status", "เปิด detail", "empty result", "abnormal row"],
        ),
        Topic(
            "FE/LLDD-FE-Create-Document",
            "LLDD FE - Create Document",
            "FE",
            4.9,
            42,
            FE_OWNER_KITTISAK,
            "หน้าสร้างเอกสารประกันรายได้ — **มติ 2026-08-06: ไม่มีฟอร์มฝั่ง SBP** main card เป็น iframe ของหน้าสร้างเอกสารระบบ FS ตรง ๆ + หมายเหตุ 4 ขั้นตอนใต้ iframe · `POST /sgi/document` เรียกโดย pipeline/service token",
            ["k2-create-01.png"],
            ["🔴 **มติ 2026-08-06 — หน้านี้ไม่มีฟอร์มและไม่มีแท็บฝั่ง SBP**", "main card = iframe ของหน้าสร้างเอกสารระบบ FS ตรง ๆ (เหมือน `k2-create.html`)", "หมายเหตุ 4 ขั้นตอน (verbatim จากหน้าจอ K2 เดิม) อยู่ใต้ iframe นอกกรอบ", "`POST /sgi/document` เป็น pipeline/service-token ไม่ใช่ฟอร์ม FE — ต้นทางสร้างที่ FS แล้วรอ SBP Statement ส่งกลับ (~1 วัน)", "การคีย์/ปรับข้อมูลร้านตาม SDD GI ทำที่หน้าเอกสาร (`PUT /sgi/document/{docNo}`) ไม่ใช่หน้านี้", "⚠️ หัวข้อ 5.1-5.6 (SBP mirror form + FS bridge) เป็นดีไซน์ก่อนมติ — เก็บไว้เป็นทางเลือกสำรอง **ไม่อยู่ในขอบเขต 8 ชม.**"],
            [
                ("source", "MANUAL|FS", "required", "แสดง section ตาม source; payload ใช้ชื่อ field `source`"),
                ("activeTab", "MANUAL|FS_IFRAME", "required UI state", "เลือก tab สร้างเอกสารทั่วไปหรือเอกสารจาก FS"),
                ("fsIframeUrl", "URL", "required for FS tab", "อ่านจาก config; ใช้โหลด hidden iframe ของ FS"),
                ("fsFieldMap", "array", "required after iframe load", "metadata ของ input/select/textarea ที่อ่านจาก iframe เพื่อ render SBP mirror form"),
                ("fsMirrorValues", "object", "required for FS tab", "state ของ form ฝั่ง SBP ที่ sync เข้า hidden iframe เมื่อ change/submit"),
                ("impactedStoreCode", "string 5 digits", "required", "ค้นหาด้วย popup ร้านถูกกระทบ; คง leading zero"),
                ("impactedStoreName", "string", "readonly after select", "เติมอัตโนมัติหลังเลือกร้าน"),
                ("newStoreCode", "string 5 digits", "required", "เลือกร้านเปิดใหม่จาก popup; ส่งรหัสร้านและคง leading zero"),
                ("impactMonth", "YYYY-MM", "required", "month picker; ทั้งแสดงและส่งเป็น ค.ศ."),
                ("statementPeriod", "YYYY-MM", "required for FS", "Period Statement จาก SRS SCR-02"),
                ("roundNo", "integer >= 1", "required/default 1", "ครั้งที่ของเอกสาร/งวดชดเชย"),
                ("reason", "text", "required for MANUAL/out-of-condition", "เหตุผลการสร้างเอกสารนอกเงื่อนไข; trim ก่อนส่ง"),
            ],
            [
                ("Search store", "แว่นขยาย", "GET /store/search (ระบบ SBP เดิม)", "เลือก impacted/new store"),
                ("Open FS tab", "tab เอกสารจาก FS", "Load hidden iframe from fsIframeUrl", "discover FS fields and render SBP mirror form"),
                ("Change FS mirror value", "input/select ใน SBP mirror form", "iframe value sync service", "ส่งค่าเข้า field ใน hidden iframe และ dispatch input/change"),
                ("Save draft", "ปุ่มบันทึก", "POST /api/v1/sgi/document", "สร้าง draft"),
                ("Submit", "ปุ่มส่งดำเนินการ", "POST /api/v1/sgi/document", "สร้างเอกสารและเริ่ม workflow"),
                ("Submit FS iframe", "ปุ่มส่งใน tab เอกสารจาก FS", "sync all mirror values + submit iframe form", "submit form ของ FS ใน hidden iframe"),
            ],
            [
                ApiSpec("GET", "/store/search (ระบบ SBP เดิม)", "ค้นหาร้านสำหรับ popup", {"q": "012", "type": "impacted"}, {"items": [{"storeCode": "01234", "storeName": "สาขาตัวอย่าง", "regionCode": "BN"}]}),
                # URL ของ FS iframe อ่านจาก backend config (env `FS_CREATE_DOCUMENT_URL`) — ไม่มี endpoint /configs แล้ว (2026-08-06)
                ApiSpec("POST", "/api/v1/sgi/document", "สร้างเอกสาร", {"source": "MANUAL", "impactMonth": "2026-07", "statementPeriod": "2026-07", "impactedStoreCode": "01234", "newStoreCode": "22864", "roundNo": 1, "reason": "สร้างเอกสารนอกเงื่อนไข"}, {"docNo": "2026/00001", "statusCode": "06", "message": "created"}),
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
                ("result", "actionOptions[].**value** (ไม่ใช่ label)", "required on submit action", "FE แสดง radio ตาม `actionOptions` จาก API เท่านั้น · ไม่เลือกแล้วกดส่ง → popup **verbatim SRS**: `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`"),
                ("comment", "text", "required บาง result", "trim before submit · SRS บังคับ required เมื่อเลือกไม่ชดเชย แต่ไม่ได้ระบุข้อความ popup"),
                ("compensatePercent", "number", "sum = 100", "validate before save · ไม่ครบ 100% → popup `โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100%`"),
                ("competitorCode", "select จาก master sgi_competitors", "required เมื่อเพิ่ม/แก้แถวคู่แข่ง", "ไม่เลือก → popup **verbatim SRS §10**: `กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ`"),
                ("factor.startDate / factor.endDate", "date", "endDate >= startDate", "**กติกา SRS §11**: วันที่สิ้นสุดต้องเท่ากับหรือมากกว่าวันที่เริ่มต้น — ถ้าน้อยกว่าต้องแสดง Pop-up แจ้งเตือน (SRS ไม่ได้ระบุข้อความ ให้ยืนยันกับ BA ก่อน UAT)"),
            ],
            [
                ("Save section", "ปุ่มบันทึก", "PUT /api/v1/sgi/document/{docNo}", "save partial"),
                ("Submit action", "ปุ่มส่งดำเนินการ", "POST /api/v1/sgi/document/{docNo}/actions", "submit selected result and reload status"),
                ("Upload file", "เลือกไฟล์", "POST /api/v1/sgi/document/{docNo}/attachments", "append attachment"),
                ("Open sales", "ข้อมูลยอดขายเพิ่มเติม", "GET /api/v1/sgi/document/{docNo}/sales", "show chart/detail"),
            ],
            [
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}", "โหลดรายละเอียดเอกสารพร้อม role profile สำหรับหน้า detail", {"docNo": "2026/00123"}, {"docNo": "2026/00123", "statusCode": "06", "viewerRbacRoleCode": "R-XX", "roleProfileCode": "P-06", "visibleSections": ["doc-header", "sec-sales", "sec-map", "sec-newstore", "sec-competitor", "sec-factor", "sec-attach", "sec-comp-history", "sec-decision-history", "sec-action"], "editableSections": [], "canUploadAttachment": True, "canAction": True, "actionOptions": [{"value": RESULT_ENUM_VALUE["เห็นควรไม่ชดเชย"], "label": "เห็นควรไม่ชดเชย", "requireComment": True}, {"value": RESULT_ENUM_VALUE["หยุดชดเชยประกันรายได้"], "label": "หยุดชดเชยประกันรายได้", "requireComment": False}, {"value": RESULT_ENUM_VALUE["ส่งหน่วยงานส่งเสริมธุรกิจ SBP"], "label": "ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "requireComment": False}, {"value": RESULT_ENUM_VALUE["ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ"], "label": "ส่งเจ้าหน้าที่ SBP DSA ดำเนินการ", "requireComment": False}], "impactedStore": {"storeCode": "01234"}, "newStores": [], "competitors": [{"competitorCode": "01", "nameTh": "โลตัสเอ็กซ์เพรส", "branchTh": "สาขารัตนอุทิศ", "openedDate": "2023-10-10", "impactDate": "2026-06-01", "detail": "", "sourceSystem": "ALLMAP"}], "externalFactors": [{"factorCode": "F003", "factorName": "การก่อสร้าง / ปิดถนน", "dateFrom": "2026-05-01", "dateTo": None, "detail": ""}], "attachments": [{"attachId": 4471, "fileName": "impact_report.pdf", "fileSize": 1887436, "mimeType": "application/pdf", "sectionCode": "06", "scanStatus": "CLEAN", "uploadedBy": "somchai.k", "uploadedAt": "2026-06-12T09:31:00"}], "costDetails": [{"newStoreCode": "00990", "costYear": 2026, "costMonth": 6, "costTargetN": 250000.00, "costAmountN": 232000.00, "costTargetNc": 0, "costAmountNc": 0}], "compensationHistories": [{"submitAccountMonth": "2026-05", "compensationAmount": 18000.00, "refDocNo": "2026/00098", "accountingStatus": "POSTED"}], "considerationLogs": [{"sectionCode": "06", "result": "ส่งเจ้าหน้าที่ SBP DSA", "resultCategory": "PENDING", "detail": "", "considerBy": "somchai.k", "actionDatetime": "2026-06-12T10:02:00"}], "allmapUrl": "https://allmap.example/store/01234"}),
                ApiSpec("PUT", "/api/v1/sgi/document/{docNo}", "บันทึกส่วนย่อย เช่น ร้านเปิดใหม่/คู่แข่ง/ปัจจัย", {"versionNo": 3, "newStores": [{"newStoreCode": "00990", "compensatePercent": 60, "compensationAmount": 18000.00, "sourceSystem": "ALLMAP"}, {"newStoreCode": "01180", "compensatePercent": 40, "compensationAmount": 12000.00, "sourceSystem": "USER"}], "competitors": [{"id": 8801, "competitorCode": "01", "impactDate": "2026-07-15"}, {"competitorCode": "07", "impactDate": "2026-07-20"}], "externalFactors": [{"id": 4402, "factorCode": "F03", "dateFrom": "2026-07-01", "dateTo": "2026-07-31"}, {"factorCode": "F09", "dateFrom": "2026-07-10", "dateTo": None}]}, {"message": "saved", "versionNo": 4}),
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/actions", "ส่งผลพิจารณาที่เลือกจาก actionOptions; ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/attachments", "แนบไฟล์", {"file": "multipart/form-data <= 5MB"}, {"attachId": 771, "fileName": "evidence.pdf"}),
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
            FE_OWNER,
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
            ["desktop regression ครบทุก route หลัก", "tablet/mobile regression", "request/response schema mismatch ต้องเป็นศูนย์", "Critical/High defects ต้องปิด", "report preview/export parity", "action transition 06→08→06→01→02→03→99", "delivery evidence ไม่มี token/secret"],
        ),
        Topic(
            "FE/LLDD-FE-Report",
            "LLDD FE - Status Summary Report",
            "FE",
            5.9,
            50,
            FE_OWNER,
            "สร้างรายงานตรวจสอบประกันรายได้ตาม SDD สไลด์ 60 (7 ตัวกรอง / 14 คอลัมน์) พร้อมค้นหาข้อมูลและ Export Excel",
            ["k2-report-01.png", "k2-report-02.png"],
            ["Report filters (SDD slide 60 · 2026-08-06: สถานะ*|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ|ประเภทร้าน (รหัสจาก common_code · ห้าม hardcode) · Period Statement From-To (date, ค.ศ.) เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว)", "Summary table (sortable 14 columns)", "ปุ่มออกผล 3 ตัว (Preview Report · Export Excel · Export CSV to Batch)", "Sample data verification"],
            [
                ("impactedStoreCode", "string 5 digits", "optional; numeric only when input", "คง leading zero; ปุ่มแว่นขยายเรียก popup เลือกร้านที่ถูกกระทบ"),
                ("impactedStoreName", "string", "readonly", "แสดงอัตโนมัติหลังเลือกรหัสร้าน; ไม่ส่งเป็น filter หลักถ้ามี storeCode"),
                ("newStoreCode", "string 5 digits", "optional; numeric only when input", "รหัสร้านเปิดกระทบ/ร้านเปิดใหม่; คง leading zero"),
                ("impactMonthFrom", "YYYY-MM", "optional; month picker", "ส่งและแสดงเป็น ค.ศ. เช่น 2026-05"),
                ("impactMonthTo", "YYYY-MM", "optional; month picker; must be >= from", "ถ้า from > to ให้แสดง validation ก่อน call API"),
                ("storeTypes", "array ของ BranchTypeFGIName", "optional multi select", "**ยืนยันจาก master จริงแล้ว (`ข้อมูล Master K2.xlsx` · ชีต `BranchTypeProfile` จาก `CPA_FRN_FGI`)**: ค่าที่ใช้คือคอลัมน์ `BranchTypeFGIName` มี **7 ค่าไม่ซ้ำ** — `A` (A-Mo) · `B` (B(1)) · `C` (C และ C(Retire CPALL)) · `D` (Type D — เดิมเรียก BGC) · `E` (B(2)) · `PTT` · `บริษัท` (Corporate) · ⚠️ **D กับ E เป็นคนละประเภทและมีจริงทั้งคู่** — เอกสารรุ่นก่อนที่แสดงเพียง 4 ตัวเลือก (A/B/C/E หรือ A/B/C/D) **ผิด** ทั้ง SDD สไลด์ 60 (แสดงบางส่วน) และ SRS (เขียน “พนักงาน” ซึ่ง**ไม่มีใน master**) · ยังคง**ห้าม hardcode** — โหลดจาก `GET /common/common-code` ของระบบ SBP เดิม แล้วใช้ 7 ค่านี้เป็น expected set ตอนทดสอบ"),
                ("status", "statusCode string", "required single select", "บังคับเลือก 1 สถานะก่อน Preview/Export; options มาจาก sps_store.workflow_status ของ @srm/glb-workflow (ตาราง document_statuses ของ SGI ถูกตัดแล้ว)"),
                ("resultCategory", "APPROVE|REJECT|CANCELLED|PENDING", "optional radio (status เท่านั้นที่บังคับ)", "**4 ค่า** — APPROVE=ประกันรายได้ · REJECT=ไม่ประกันรายได้ · **CANCELLED=ยกเลิกโดยระบบ (เพิ่ม 2026-08-10)** · PENDING/ไม่มีค่า=ยังไม่มีผล · CANCELLED มาจาก master จริง `DecisionProfile` decision 14 `CancelBySystem` (`DecisionResultName` = ยกเลิกโดยระบบ) ซึ่ง SDD สไลด์ 60 ไม่ได้แสดงไว้"),
                ("regions", "array ของ ZoneName", "optional multi select", "**ยืนยันจาก master จริงแล้ว (`ข้อมูล Master K2.xlsx` · ชีต `ZoneProfile`)**: **13 ภาค** — BN(10) · BW(20) · BE(30) · BG(40) · BS(70) · REU(81) · NEU(82) · RSU(83) · RSL(84) · RN(85) · RC(86) · REL(90) · NEL(92) (ตัวเลขในวงเล็บคือ `ZoneCode`) — ตรงกับรายการที่ prototype ใช้ **ครบทั้ง 13 ค่า** · รายการ 8 ค่าใน SRS (BE/BN/BS/BW/RC/RE/RN/RS) เป็นของเก่า **ไม่ต้องใช้** · ยังคง**ห้าม hardcode** — โหลดจาก `GET /store/all-regions` ของระบบ SBP เดิม"),
                ("statementPeriodFrom", "YYYY-MM", "optional month picker", "Period Statement From; ส่ง ค.ศ. format YYYY-MM"),
                ("statementPeriodTo", "YYYY-MM", "optional month picker; must be >= from", "Period Statement To; validate range ก่อน call API"),
                ("page", "integer", "default 1; >=1", "pagination ของ preview table"),
                ("size", "integer", "default 20; max 100", "BE จำกัด page size เพื่อกัน query หนัก"),
                ("resultTable.storeCode", "string 5 digits", "display only", "คอลัมน์ 1 รหัสร้านถูกกระทบ"),
                ("resultTable.storeName", "string", "display only", "คอลัมน์ 2 ชื่อร้านถูกกระทบ"),
                ("resultTable.region", "string", "display only", "คอลัมน์ 3 ภาค"),
                ("resultTable.storeType", "string", "display only", "คอลัมน์ 4 ประเภทร้าน"),
                ("resultTable.impactMonth", "MM/YYYY ค.ศ.", "display only", "คอลัมน์ 5 เดือน/ปีที่ถูกกระทบ"),
                ("resultTable.statementPeriod", "MM/YYYY ค.ศ.", "nullable", "คอลัมน์ 6 Period Statement"),
                ("resultTable.newStoreCode", "string 5 digits or '-'", "display only", "คอลัมน์ 7 รหัสร้านเปิดกระทบ"),
                ("resultTable.newStoreName", "string or '-'", "display only", "คอลัมน์ 8 ชื่อร้านเปิดกระทบ"),
                ("resultTable.newStoreRegion", "string or '-'", "display only", "คอลัมน์ 9 ภาค (ร้านเปิดกระทบ)"),
                ("resultTable.newStoreType", "string or '-'", "display only", "คอลัมน์ 10 ประเภทร้าน (ร้านเปิดกระทบ)"),
                ("resultTable.compensationAmount", "number #,##0.00", ">=0", "คอลัมน์ 11 ยอดเงินชดเชย; align right"),
                ("derived.salesDataDays", "integer", "<60 = abnormal", "ข้อมูลประกอบสำหรับ class flag-red; ไม่ใช่ waitingDays"),
                ("resultTable.roundNo", "integer", ">=1", "คอลัมน์ 12 ครั้งที่"),
                ("resultTable.createdDate", "DD/MM/YYYY ค.ศ.", "required", "คอลัมน์ 13 วันที่สร้าง"),
                ("resultTable.docNo", "YYYY/xxxxx", "required", "คอลัมน์ 14 เลขที่เอกสาร; ใช้เปิด detail/preview"),
            ],
            [
                ("เปิด popup ร้าน", "ปุ่มแว่นขยายข้างรหัสร้านที่ถูกกระทบ", "GET /store/search (ระบบ SBP เดิม)", "เลือก store แล้วเติม storeCode/storeName"),
                ("ค้นหาข้อมูล", "ปุ่ม ค้นหาข้อมูล", "GET /api/v1/sgi/report/status-summary", "validate status (required) และคู่รหัสร้าน แล้ว render summary line + table 14 columns"),
                ("เคลียร์ค่าเริ่มใหม่", "ปุ่มเคลียร์ค่าเริ่มใหม่", "client state", "reset filter, summary, table และ error message"),
                ("Export Excel", "ปุ่ม Export Excel ท้าย filter", "GET /api/v1/sgi/report/status-summary/export", "ส่ง filter ชุดเดียวกับการค้นหา แล้วดาวน์โหลดไฟล์ .xlsx 14 คอลัมน์"),
                ("Open detail", "คลิกเลขที่เอกสารหรือ row", "navigate /sgi/document/{docNo} หรือ preview modal", "เปิดเอกสารที่เกี่ยวข้อง"),
            ],
            [
                ApiSpec("GET", "/store/search (ระบบ SBP เดิม)", "Popup เลือกร้านที่ถูกกระทบ", {"q": "00788", "type": "impacted"}, {"items": [{"storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13", "region": "BN", "storeType": "SBP Type B"}]}),
                ApiSpec("GET", "/api/v1/sgi/report/status-summary", "ค้นหาข้อมูลรายงานตรวจสอบประกันรายได้ (14 คอลัมน์ · SDD สไลด์ 60)", {"status": "06", "impactedStoreCode": "00788", "newStoreCode": "00990", "periodStatementFrom": "2026-06-01", "periodStatementTo": "2026-06-30", "storeTypes": ["A", "B"], "regions": ["RSU", "BN"], "result": "APPROVE", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 10, "summary": {"totalItems": 10, "totalCompensationAmount": 439100.0, "overThresholdItems": 3, "abnormalSalesItems": 2}, "items": [{"impactedStoreCode": "00788", "impactedStoreName": "รัตนอุทิศ ซ.13", "impactedRegion": "RSU", "impactedStoreType": "B", "impactMonth": "2026-05", "periodStatement": "2026-06-07", "newStoreCode": "00990", "newStoreName": "เซเว่นฯ รัตนาธิเบศร์ 12", "newRegion": "RSU", "newStoreType": "A", "compensationAmount": 48200.0, "roundNo": 1, "createdDate": "2026-06-12", "docNo": "2026/00123"}]}),
                ApiSpec("GET", "/api/v1/sgi/report/status-summary/export", "Export Excel ด้วย filter เดียวกับการค้นหา", {"sameAsSearch": True, "format": "xlsx"}, {"contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "fileName": "insurance-verification-2026.xlsx"}),
            ],
            ["เปิดหน้า Report", "โหลด reference status/region/store type ถ้ามี API (ภาคใหม่แสดง checkbox อัตโนมัติ)", "ผู้ใช้ระบุ filter 7 ตัวตาม SDD สไลด์ 60", "Validate status (required) · คู่รหัสร้านถูกกระทบ-เปิดกระทบ · Period Statement บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ", "กด ค้นหาข้อมูล แล้ว call report API", "แสดงวันที่เป็น ค.ศ. ตามระบบ SBP เดิม (ไม่แปลงเป็น พ.ศ. — ตัดสินใจ 2026-08-06)", "render summary line และ table 14 คอลัมน์", "กด Export Excel แล้วส่ง filter เดียวกันไป export API"],
            ["status เป็น required ตัวเดียวก่อนค้นหา/export (resultCategory เป็นตัวเลือก · SDD สไลด์ 60)", "ระบุ impactedStoreCode แล้วต้องระบุ newStoreCode ด้วย", "Period Statement เป็นช่วงวันที่ ค.ศ. และ from <= to", "ตารางแสดง 14 คอลัมน์ครบและ export ออกครบ 14 คอลัมน์", "ยอดเงิน format #,##0.00 และ total summary ตรงกับผลรวม API", "แถวข้อมูลยอดขายไม่ครบ 60 วันใช้ class flag-red โดยอิง derived.salesDataDays < 60", "export ใช้ filter เดียวกับการค้นหาล่าสุด"],
            ["ไม่เลือก status แล้วค้นหาต้อง block", "ระบุร้านถูกกระทบแต่ไม่ระบุร้านเปิดกระทบ ต้อง block", "periodStatementFrom > periodStatementTo ต้อง error REPORT_DATE_RANGE_INVALID", "สถานะ = เสร็จสิ้นดำเนินการ แต่ไม่ระบุ Period Statement ต้อง block", "ค้นหาด้วยร้านถูกกระทบ", "เลือกหลาย region/storeType", "render table 14 columns", "export xlsx", "empty result แสดง summary เป็น 0"],
        ),
        Topic(
            "FE/LLDD-FE-Master-Data",
            "LLDD FE - Master Data",
            "FE",
            6.5,
            55,
            FE_OWNER_KITTISAK,
            "สร้างหน้าจอ master ที่ SGI ดูแลเอง 2 หน้า: ปัจจัยภายนอก (SCR-09 · k2-factors.html) "
            "และรายชื่อแบรนด์ร้านคู่แข่ง (k2-competitors.html · รหัส 01-11 ไทย+อังกฤษ) — "
            "หน้าผู้ปฏิบัติงาน/สิทธิ์เมนู/ตั้งค่าระบบ ไม่อยู่ในขอบเขตแล้ว (ใช้ของระบบ SBP เดิม)",
            ["k2-factors-01.png", "k2-competitors-01.png"],
            ["External factor master (SCR-09)", "Competitor brand master", "CRUD modal", "Active/inactive toggle"],
            [
                ("factorCode", "string", "required · unique · ห้ามซ้ำ", "คีย์ของปัจจัยภายนอก — แก้ไม่ได้หลังสร้าง"),
                ("factorName", "string", "required", "ชื่อปัจจัยภายนอกที่แสดงในหน้าเอกสาร"),
                ("description", "text", "optional", "คำอธิบายเพิ่มเติม"),
                ("competitorCode", "string(30)", "required · unique · รหัส 01-11", "คีย์ของแบรนด์คู่แข่ง — feed dropdown ร้านคู่แข่งในหน้าเอกสาร"),
                ("nameTh", "string(200)", "required", "ชื่อแบรนด์ภาษาไทย"),
                ("nameEn", "string(200)", "required", "ชื่อแบรนด์ภาษาอังกฤษ (ระบบเดิมเก็บทั้งสองภาษา)"),
                ("remark", "string(500)", "optional", "คอลัมน์ รายละเอียดเพิ่มเติม ของหน้า k2-competitors.html"),
                ("active", "boolean", "default true", "ปิดใช้งานแทนการลบเมื่อถูกอ้างในเอกสารแล้ว"),
            ],
            [
                ("Add/Edit", "modal action", "POST/PUT ของ master ที่กำลังเปิดอยู่", "ปิด modal + reload table"),
                ("Delete", "ปุ่มถังขยะ + confirm", "DELETE master API", "409 ถ้าถูกอ้างในเอกสารแล้ว → ให้ปิด active แทน"),
                ("Toggle active", "switch ในตาราง", "PUT พร้อม active", "แถวที่ปิดใช้งานไม่ขึ้นใน dropdown ของหน้าเอกสาร"),
            ],
            [
                ApiSpec("GET", "/api/v1/sgi/master/factors", "SCR-09 list/filter ปัจจัยภายนอก",
                        {"q": "ถนน", "active": True, "page": 1, "size": 20},
                        {"page": 1, "size": 20, "total": 1,
                         "items": [{"factorCode": "F001", "factorName": "ก่อสร้างถนน", "description": "ผลกระทบจากการก่อสร้าง", "active": True}]}),
                ApiSpec("POST", "/api/v1/sgi/master/factors", "SCR-09 เพิ่มปัจจัยภายนอก",
                        {"factorCode": "F001", "factorName": "ก่อสร้างถนน", "description": "ผลกระทบจากการก่อสร้าง", "active": True},
                        {"factorCode": "F001", "created": True}),
                ApiSpec("PUT", "/api/v1/sgi/master/factors/{code}", "SCR-09 แก้ไขปัจจัยภายนอก",
                        {"factorName": "ก่อสร้างถนนระยะยาว", "description": "กระทบการเข้าร้าน", "active": True},
                        {"factorCode": "F001", "updated": True}),
                ApiSpec("DELETE", "/api/v1/sgi/master/factors/{code}", "SCR-09 ลบปัจจัยภายนอกที่ยังไม่ถูกอ้างในเอกสาร",
                        {}, {"factorCode": "F001", "deleted": True}),
                ApiSpec("GET", "/api/v1/sgi/master/competitors", "list แบรนด์คู่แข่ง (master 11 รายการ)",
                        {"active": True},
                        {"total": 11, "items": [{"competitorCode": "01", "nameTh": "แฟมิลี่มาร์ท", "nameEn": "FamilyMart", "remark": "", "active": True}]}),
                ApiSpec("POST", "/api/v1/sgi/master/competitors", "เพิ่มแบรนด์คู่แข่ง",
                        {"competitorCode": "12", "nameTh": "ร้านตัวอย่าง", "nameEn": "Sample Shop", "remark": "", "active": True},
                        {"competitorCode": "12", "created": True}),
                ApiSpec("PUT", "/api/v1/sgi/master/competitors/{code}", "แก้ไขแบรนด์คู่แข่ง",
                        {"nameTh": "แฟมิลี่มาร์ท", "nameEn": "FamilyMart", "remark": "ปรับชื่อ", "active": True},
                        {"competitorCode": "01", "updated": True}),
                ApiSpec("DELETE", "/api/v1/sgi/master/competitors/{code}", "ลบแบรนด์คู่แข่งที่ยังไม่ถูกอ้างใน sgi_document_competitors",
                        {}, {"competitorCode": "12", "deleted": True}),
            ],
            ["Open master page", "Load table", "Open modal", "Validate required/unique", "Call API", "Reload table"],
            [
                "factorCode และ competitorCode ห้ามซ้ำ (409 CODE_DUPLICATE)",
                "nameTh และ nameEn ของคู่แข่งบังคับทั้งคู่",
                "ลบไม่ได้ถ้าถูกอ้างใน sgi_document_external_factors / sgi_document_competitors → 409 ให้ปิด active แทน",
                "ไม่มี reason และไม่มี audit log (ยกเลิกระบบ audit ของ master 2026-08-07)",
            ],
            [
                "duplicate factorCode",
                "duplicate competitorCode",
                "competitor ไม่ใส่ nameEn ต้อง block",
                "ลบ factor ที่ถูกอ้างในเอกสารแล้ว ต้องได้ 409",
                "toggle active แล้ว dropdown ในหน้าเอกสารต้องไม่แสดงแถวนั้น",
            ],
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
                ("X-Service-Token", "opaque service token", "required for internal workflow/batch callbacks", "ใช้กับ /sgi/workflow/instances และ external callback ที่ไม่ใช่ user JWT"),
                ("X-Request-Id", "uuid/string", "optional but logged", "ถ้าไม่ส่ง BE generate แล้วคืนใน log/trace"),
                ("ErrorEnvelope", "{code,message}", "message Thai verbatim", "ห้ามเพิ่ม error shape อื่นใน endpoint รายตัว"),
                ("PageResponse<T>", "{page,size,total,items}", "page>=1 size<=100", "ใช้กับทุก GET list"),
                ("MutationResponse", "{message}", "message optional for simple save", "ถ้า workflow action ใช้ ActionResponse แทน"),
                ("docNo", "YYYY/xxxxx ค.ศ.", "path/query", "URL encode slash ตาม client/router; service ประกอบกลับเป็น docNo"),
                ("storeCode/newStoreCode", "string 5 digits", "preserve leading zero", "ห้ามใช้ numeric id แทนรหัสร้านใน payload"),
                ("date/month", "ISO-8601 ค.ศ.", "YYYY-MM-DD / YYYY-MM", "FE แสดง ค.ศ. เป็นค่าเริ่มต้น (buddhistEra=false) · แปลง พ.ศ. เฉพาะ component ที่เปิด flag"),
                ("amount/percent", "number", "2 decimal", "format display อยู่ FE; BE validate precision/range"),
                ("result", "actionOptions[].**value** (ไม่ใช่ label)", "required for /actions", "ต้องเป็นค่า `value` ที่ BE ส่งมาใน `actionOptions` ของ role profile เอกสารนั้น — ไม่ใช่ `label` ที่ใช้แสดงผล"),
                ("ActionResponse", "{statusCode,nextSection,message}", "required for /actions", "FE resolve label จาก /sgi/lookup/document-statuses; mutation response ไม่คืน label ไทยซ้ำ"),
                ("reason", "text", "ไม่บังคับแล้ว (ยกเลิกระบบ audit ของ master 2026-08-07)", "ไม่มีปลายทางเก็บ — ถ้าส่งมาให้ละเว้น"),
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
                ApiSpec("ALL", "/api/v1/sgi/*", "Standard error envelope", None, {"code": "VALIDATION", "message": "ข้อความภาษาไทยตรงตาม SRS"}),
                ApiSpec("GET", "/api/v1/sgi/*", "Standard list envelope เมื่อ endpoint เป็นรายการ", {"page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/actions", "**อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Document-Workflow-Actions (Tunyatorn)** · ยกมาเป็นตัวอย่างสัญญา action กลางที่ทุกเส้นต้องยึด (ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02)", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
            ],
            [
                "Request enters logging middleware and request id is attached",
                "BffUserGuard ตรวจ x-api-key แล้ว map BFF header เป็น user context — 🔴 SGI ไม่ออก/ไม่ตรวจ JWT เอง (login อยู่ที่ Cognito ฝั่ง BFF) · เส้น service-token ใช้ API key แยก",
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
                "workflow action ต้องเขียน sgi_consideration_logs · master mutation ไม่มี audit แล้ว (ยกเลิกระบบ audit ของ master 2026-08-07)",
            ],
            ["missing JWT 401", "role forbidden 403", "validation error 400", "not found 404", "duplicate conflict 409", "list envelope", "action transition envelope", "audit reason required", "service token endpoint"],
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
                ("year", "ค.ศ. YYYY", "required for /sgi/document", "ไม่ระบุคืน 400 ตาม SRS · BE ผ่าน toAD() เผื่อ client ส่ง พ.ศ."),
                ("page/size", "integer", "page>=1 size<=100", "pagination"),
            ],
            [
                ("Inbox tasks", "GET", "task.service.searchOpenTasks", "return waiting list"),
                ("Document search", "GET", "document.service.search", "return related list"),
            ],
            [
                ApiSpec("GET", "/api/v1/sgi/document/tasks", "Inbox tasks API", {"status": "06", "keyword": "โลตัส", "regionCode": "BE", "storeType": "A", "createdFrom": "2026-06-01", "createdTo": "2026-06-30", "salesDeclineMin": 10, "salesDeclineMax": 80, "compensationMin": 0, "compensationMax": 500000, "daysPendingMin": 0, "daysPendingMax": 30, "page": 1, "size": 20}, {"items": [{"docNo": "2026/00123", "currentOwner": "somchai.k", "daysPending": 3}]}),
                ApiSpec("GET", "/api/v1/sgi/document", "Document search API", {"year": 2026, "impactedStoreCode": "00788", "status": "06", "result": "APPROVE", "keyword": "โลตัส", "regionCode": "BE", "storeType": "A", "createdFrom": "2026-06-01", "createdTo": "2026-06-30", "salesDeclineMin": 10, "salesDeclineMax": 80, "compensationMin": 0, "compensationMax": 500000, "page": 1, "size": 20}, {"items": [{"docNo": "2026/00123", "statusCode": "06"}]}),
            ],
            ["Read JWT section/role", "Validate year for documents", "Build filter query", "Join sgi_impacted_stores", "Return page result"],
            ["year missing fails for /sgi/document", "leading zero storeCode preserved", "pagination returns total", "status filter works"],
            ["tasks by section", "documents missing year", "store search", "empty result"],
        ),
        Topic(
            "BE/LLDD-BE-API-Document-Create-Update",
            "LLDD BE - API Document Create and Update",
            "BE",
            4.2,
            36,
            BE_OWNER_BUTSABA,
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
                ApiSpec("POST", "/api/v1/sgi/document", "Create document API", {"impactedStoreCode": "00788", "impactMonth": "2026-06", "source": "MANUAL", "newStoreCode": "00990", "roundNo": 1, "reason": "manual create", "requestId": "uuid"}, {"docNo": "2026/00124", "statusCode": "06"}),
                ApiSpec("PUT", "/api/v1/sgi/document/{docNo}", "Update document partial sections", {"versionNo": 3, "newStores": [{"newStoreCode": "00990", "compensatePercent": 60, "compensationAmount": 18000.00, "sourceSystem": "ALLMAP"}, {"newStoreCode": "01180", "compensatePercent": 40, "compensationAmount": 12000.00, "sourceSystem": "USER"}], "competitors": [{"id": 8801, "competitorCode": "01", "impactDate": "2026-07-15"}, {"competitorCode": "07", "impactDate": "2026-07-20"}], "externalFactors": [{"id": 4402, "factorCode": "F03", "dateFrom": "2026-07-01", "dateTo": "2026-07-31"}, {"factorCode": "F09", "dateFrom": "2026-07-10", "dateTo": None}]}, {"message": "saved", "versionNo": 4}),
            ],
            ["Validate required fields", "Check duplicate store/month", "Generate docNo", "Insert sgi_compensation_documents", "Open workflow task", "Save section updates in transaction"],
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
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}", "Document aggregate API", {"docNo": "2026/00123"}, {"docNo": "2026/00123", "statusCode": "06", "viewerRbacRoleCode": "R-XX", "roleProfileCode": "P-06", "visibleSections": ["doc-header", "sec-sales", "sec-map", "sec-newstore", "sec-competitor", "sec-factor", "sec-attach", "sec-comp-history", "sec-decision-history", "sec-action"], "editableSections": [], "canUploadAttachment": True, "canAction": True, "actionOptions": [{"value": RESULT_ENUM_VALUE["เห็นควรไม่ชดเชย"], "label": "เห็นควรไม่ชดเชย", "requireComment": True}], "impactedStore": {"storeCode": "00788"}, "newStores": []}),
                ApiSpec("GET", "/api/v1/sgi/master/competitors", "**อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Report-and-Master-Data (Peerakorn)** · เอกสารนี้เป็นผู้ใช้: อ่าน master คู่แข่งมาทำ dropdown ในหน้าเอกสาร", {"q": "lotus"}, {"items": [{"competitorCode": "C007", "competitorName": "Lotus Express"}]}),
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
            BE_OWNER,
            "ออกแบบ APIs สำหรับรับผลพิจารณา ตรวจสิทธิ์ action และบันทึก audit/consideration log",
            [],
            ["Submit action", "Action owner guard", "Amount threshold reference", "Send back result", "Audit and email rule"],
            [
                ("docNo", "YYYY/xxxxx", "required", "path param"),
                ("result", "actionOptions[].**value** (ไม่ใช่ label)", "required", "ต้องเป็นค่า `value` จาก `actionOptions` ที่ API detail ส่งมา — validate ซ้ำฝั่ง BE ว่าอยู่ใน 7 ค่าของ enum"),
                ("comment", "text", "required for return/reject", "trim ก่อนบันทึก"),
            ],
            [
                ("Submit action", "POST", "documentAction.service.submit", "submit result and update status"),
                ("Write audit", "transaction", "considerationLog.repository.insert", "record action history"),
                ("Send email", "async", "notification.service.sendByStatusRule", "notify next owner"),
            ],
            [
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/actions", "Document action API ตัวอย่างเมื่อ currentSection=01 จึงเปลี่ยนไป 02", {"result": "เห็นควรชดเชย", "comment": "เห็นควรชดเชยตามหลักเกณฑ์"}, {"statusCode": "02", "nextSection": "02", "message": "submitted"}),
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}/timeline", "**อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Attachment-Sales-Timeline (Peerakorn)** · เอกสารนี้อ้างเพราะ action ที่ส่งผลพิจารณาเป็นตัวเขียน sgi_consideration_logs ที่ timeline อ่าน", {"docNo": "2026/00123"}, {"items": [{"section": "06", "result": "ชดเชย"}]}),
            ],
            ["Lock current action task", "Validate owner and selected result against actionOptions", "Apply server-side business rule", "Update document/task", "Insert sgi_consideration_logs", "Trigger email"],
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
            "ออกแบบ Workflow Engine ภายในและ POST /api/v1/sgi/workflow/instances สำหรับเปิด workflow จาก Job 8b แทน K2 REST StartInstance โดยเป็นเจ้าของ Gen Flow Gate W/Y/N",
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
                ("impactProcessId", "integer/string", "required", "อ้าง sgi_fgi_impact_processes และ sgi_compensation_documents ที่ Job 8 สร้างแล้ว"),
                ("sourceJobNo", "string", "required fixed 8b", "ใช้ trace รอบรันใน application log (structured) — ไม่มีตาราง job_run_histories แล้ว"),
                ("requestId", "string `job8b-{impactProcessId}-{YYYYMM}` (ค.ศ.)", "required", "idempotency key ต่อ impactProcessId + sourceJobNo — **ต้องเป็นค่าที่คำนวณซ้ำได้ ไม่ใช่ UUID สุ่ม** เพราะถ้าสุ่มใหม่ทุกครั้งที่ retry จะกันซ้ำไม่ได้เลย (แก้ชนิดจาก `uuid` เมื่อ 2026-09-08 — ตัวอย่างในเอกสารไม่เคยเป็น UUID)"),
                ("workflow_generation_status", "W|Y|N", "computed", "W=ข้อมูลยังไม่พร้อมเพื่อ rerun, Y=เปิด workflow สำเร็จ, N=ไม่เข้าเกณฑ์ถาวร"),
                ("branchType/distanceKm", "enum/number|null", "required by gate", "branch นอกเซ็ตหรือระยะเกินตั้ง N; ระยะยังไม่มีค่าคง W"),
                ("growthRateDiff", "number|null", "<= -10 required by gate", "NULL คง W; ค่ามากกว่า -10 ตั้ง N แบบถาวร"),
                ("dvUserId/juristic", "string|null", "DV required; juristic must differ", "DV ว่างหรือ juristic เดียวกันตั้ง N; juristic ยังไม่พร้อมคง W"),
                ("salesStatus", "Y|N", "required by gate", "ค่าอื่นคง W และคืน 422"),
            ],
            [
                ("Open workflow", "POST", "workflowInstance.service.openFromImpact", "ผ่าน gate แล้วสร้าง/คืน instance"),
                ("Check status", "GET", "/api/v1/sgi/workflow/instances/{id}", "อ่าน instance status"),
                ("Summary", "GET", "/api/v1/sgi/workflow/summary", "ตัวเลข W/Y/N และงานค้างต่อ section"),
            ],
            [
                ApiSpec("POST", "/api/v1/sgi/workflow/instances", "เปิด workflow ภายในจาก impact process; เรียกโดย Job 8b ผ่าน service token ไม่ใช่ FE", {"impactProcessId": 901234, "sourceJobNo": "8b", "requestId": "job8b-901234-202607"}, {"docNo": "2026/00123", "instanceId": "WF-2026-00123", "workflowGenerationStatus": "Y", "firstSection": "06", "statusCode": "06", "status": "รอฝ่าย SBP DSA ดำเนินการ"}),
                ApiSpec("GET", "/api/v1/sgi/workflow/instances/{id}", "อ่านสถานะ workflow instance", {"id": "WF-2026-00123"}, {"instanceId": "WF-2026-00123", "docNo": "2026/00123", "status": "ACTIVE", "currentSection": "06"}),
                ApiSpec("GET", "/api/v1/sgi/workflow/summary", "สรุป W/Y/N และงานค้างต่อ section สำหรับ monitor", {"period": "2026-07"}, {"workflowGeneration": {"W": 12, "Y": 342, "N": 8}, "openTasksBySection": [{"sectionCode": "06", "count": 24}]}),
            ],
            [
                "Validate service token and idempotency key",
                "Load impact process and current workflow_generation_status",
                "Reject if status is already Y and return existing doc/instance idempotently",
                "Evaluate Gen Flow Gate in one service: status W, branch type allowlist, DV present, juristic different, growth_rate_diff <= -10, sales_status in Y/N",
                "If branch type is outside allowlist, distance exceeds threshold, DV is missing, juristic is the same, or growth_rate_diff > -10, update workflow_generation_status=N and return 200 with permanent-skip reason",
                "If distance/juristic/growth data is NULL or sales_status is not ready, keep workflow_generation_status=W and return 422 reason so Job 8b can rerun",
                "If gate passes, require sgi_compensation_documents from Job 8, open workflow via @srm/glb-workflow (initializeWorkflow + addPreApprover at state 06 — function names confirmed 2026-08-14 from the library's own LLDD, sheet Detail), then update sgi_fgi_impact_processes.workflow_generation_status=Y in one transaction",
                "Enqueue notification summary outside transaction after commit",
            ],
            [
                "ไม่มี FE screen หรือ Flow page deliverable เพิ่มจาก LLDD นี้",
                "Job 8b ต้องเรียก API/service นี้และไม่ duplicate Gen Flow Gate",
                "ไม่เรียก K2 REST StartInstance และไม่สร้างไฟล์ BPM06001O/2O/3O",
                "ผ่าน gate แล้ว transaction ต้องมี document + instance + first task + Y ครบ หรือ rollback ทั้งหมด",
                "fail ถาวร (branch type, distance over threshold, missing DV, same juristic, growth not met) ต้องตั้ง N; เฉพาะข้อมูล distance/juristic/growth/sales status ยังไม่พร้อมจึงคง W",
                "idempotent rerun ไม่สร้าง docNo/instance/task ซ้ำ",
            ],
            ["gate pass creates workflow", "branch type/distance over threshold sets N", "distance NULL keeps W", "missing DV sets N", "same juristic sets N", "growth NULL keeps W but growth > -10 sets N", "sales status NULL keeps W", "duplicate request returns existing instance", "transaction rollback on task insert failure", "service token missing returns 401"],
        ),
        Topic(
            "BE/LLDD-BE-API-Attachment-Sales-Timeline",
            "LLDD BE - API Attachment Sales and Timeline",
            "BE",
            3.5,
            30,
            BE_OWNER_PEERAKORN,
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
                ApiSpec("POST", "/api/v1/sgi/document/{docNo}/attachments", "Upload attachment API", {"file": "multipart <= 5MB", "sectionCode": "06"}, {"attachId": 771, "fileName": "evidence.pdf"}),
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}/attachments/{attachId}/download", "ดาวน์โหลดไฟล์แนบรายไฟล์ผ่าน BE — ตรวจสิทธิ์เอกสาร + attachment ต้องเป็นของ docNo แล้วตัดสิน scan_status ตามนโยบายเดียว ("
                        + ATTACHMENT_DOWNLOAD_POLICY_SHORT + ")", {}, {"contentType": "application/pdf", "note": "binary stream · ไฟล์จริงอยู่บน S3 ผ่าน service ของระบบ SBP เดิม"}),
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}/attachments/download-all", "ดาวน์โหลดไฟล์แนบทั้งหมดเป็น .zip — ไม่มีไฟล์ที่ผ่าน scan เลยตอบ 404 (ไม่คืน zip เปล่า)", {}, {"contentType": "application/zip", "fileName": "2026-00123-attachments.zip"}),
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}/sales", "Sales detail API", {"docNo": "2026/00123"}, {"growthRateDiff": -12.45, "totalWorkingDays": 60, "windows": [{"label": "ก่อนเปิด 15 วัน", "rows": []}]}),
                ApiSpec("GET", "/api/v1/sgi/document/{docNo}/timeline", "Timeline/history API", {"docNo": "2026/00123"}, {"items": []}),
            ],
            ["Validate docNo/permission", "Validate file size/type", "Store file metadata", "Load sales summary and transactions", "Return timeline ordered by action time"],
            ["file >5MB returns 413", "unsupported file type returns 415", "sales windows are ordered", "timeline newest/oldest order matches FE expectation"],
            ["upload success", "upload too large", "download missing file", "sales not found", "timeline empty"],
        ),
        Topic(
            "BE/LLDD-BE-API-Lookup",
            "LLDD BE - API Lookup",
            "BE",
            4.7,
            40,
            BE_OWNER,
            "ออกแบบ APIs กลุ่ม lookup ที่ใช้ร่วมทุกหน้าจอของ SBP Mall",
            [],
            ["Lookup APIs", "Auth endpoints are platform reference only"],
            [
                ("q", "string", "optional", "ใช้ค้นหา ร้าน (store/mas_store ระบบเดิม) · พนักงาน (business_user ระบบเดิม) · คู่แข่ง (sgi_competitors ของ SGI)"),
                ("type", "impacted|new", "required for /store/search (ระบบ SBP เดิม)", "เลือกแหล่งร้านถูกกระทบ/ร้านเปิดใหม่"),
                ("roleCode", "00-10", "required for permission", "group ของ auth-backend (ระบบเดิม) — SGI ไม่มีตาราง roles"),
                ("menuCode", "string", "required for permission", "menu ของ auth-backend (ระบบเดิม) — SGI ไม่มีตาราง menus"),
                ("templateCode", "EM-01..EM-08", "required", "email template key"),
                ("reason", "text", "ไม่บังคับแล้ว", "ไม่มีปลายทางเก็บ (ยกเลิกระบบ audit ของ master 2026-08-07)"),
            ],
            [
                ("Store lookup", "GET", "lookup.service.searchStores", "return impacted/new stores"),
                ("Employee lookup", "GET", "employee backend เดิมของระบบ SBP (ไม่ใช่ endpoint ของ SGI)", "return business_user for operator popup"),
                ("Permission save", "PUT", "rbac.service.saveMenuPermission", "update can_access and audit"),
                ("Email template save/reset", "PUT/POST", "notificationTemplate.service", "update/reset template and audit"),
            ],
            [
                ApiSpec("GET", "/store/search (ระบบ SBP เดิม)", "ค้นหาร้านสำหรับ popup", {"q": "00788", "type": "impacted"}, {"items": [{"storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13"}]}),
                ApiSpec("GET", "/api/v1/sgi/lookup/document-statuses", "รายการสถานะเอกสาร verbatim", {}, {"items": [{"statusCode": "06", "currentOwner": "somchai.k", "statusName": "รอฝ่าย SBP DSA ดำเนินการ"}]}),
                ApiSpec("GET", "/api/v1/sgi/lookup/workflow-sections", "รายการ section 5 ขั้น", {}, {"items": [{"sectionCode": "06", "sectionName": "ฝ่าย SBP DSA"}]}),
            ],
            ["Validate query", "Read/write table by domain", "Return standard envelope for list endpoints"],
            ["status label ต้องเป็น verbatim", "permission mutation ต้อง audit", "SGI เรียก email-lib ส่งอีเมลเอง โดยใช้เลข template จาก workflow_route.email_id (ปิด DP-5 · 2026-08-14)", "Auth Group 1 เป็น platform/external reference ไม่ใช่งาน implement ใน LLDD นี้"],
            ["store lookup", "status lookup", "permission save without reason", "email template reset", "(ตัดออก) audit log search"],
        ),
        Topic(
            "BE/LLDD-BE-API-Report-and-Master-Data",
            "LLDD BE - API Report and Master Data",
            "BE",
            5.6,
            48,
            BE_OWNER_PEERAKORN,
            "ออกแบบ APIs สำหรับรายงานตรวจสอบประกันรายได้ และ Master Data ที่ SGI ดูแลเอง (ปัจจัยภายนอก + รายชื่อคู่แข่ง)",
            [],
            ["Report query service", "Excel export (14 columns, SDD slide 60)", "Operator/factor CRUD", "Report filters"],
            [
                ("year", "ค.ศ. YYYY", "required for report",
                 "⚠️ **หน้าจอรายงานไม่มีช่อง \"ปี\"** (SDD สไลด์ 60 มี 7 ตัวกรอง ไม่รวมปี) — "
                 "**FE เป็นผู้ใส่ให้เสมอ: ปีของ `periodStatementFrom` ถ้าระบุ · ไม่ระบุใช้ปีปัจจุบัน (ค.ศ.)** · "
                 "BE ยังคง return 400 ถ้าไม่มี (กติกา SRS) และผ่าน toAD() เผื่อ client ส่ง พ.ศ."),
                ("status", "statusCode string", "required", "6 สถานะเอกสาร; verbatim จาก sps_store.workflow_status ของ @srm/glb-workflow"),
                ("result", "APPROVE|REJECT|CANCELLED|PENDING", "optional for report (บังคับเฉพาะ status)", "maps to sgi_consideration_logs.result_category ล่าสุด · CANCELLED = ยกเลิกโดยระบบ (เพิ่ม 2026-08-10)"),
                ("region", "array/string", "optional", "13 region codes; multi-select"),
                ("storeType", "array ของ BranchTypeFGIName", "optional", "**7 ค่า** `A B C D E PTT บริษัท` (ยืนยันจาก master `BranchTypeProfile` ของ `CPA_FRN_FGI` 2026-08-10) · multi-select · **ห้าม hardcode** ให้โหลดจาก `GET /common/common-code` ของระบบ SBP เดิม"),
                ("impactedStoreCode", "string 5 digits", "optional", "คง leading zero"),
                ("newStoreCode", "string 5 digits", "optional", "คง leading zero"),
                ("reason", "text", "required mutation", "audit reason"),
                ("page/size", "integer", "page>=1 size<=100", "pagination"),
            ],
            [
                ("Report preview", "GET", "report.service.search", "paginated rows"),
                ("Report export", "GET", "report.service.exportCsv", "csv stream"),
                ("Master mutation", "POST/PUT/DELETE", "master.service.save", "อัปเดต row ของ master"),
            ],
            [
                ApiSpec("GET", "/api/v1/sgi/report/status-summary", "รายงานตรวจสอบประกันรายได้", {"year": 2026, "status": "06", "result": "APPROVE", "regions": ["RSU"], "storeTypes": ["A"], "periodStatementFrom": "2026-06-01", "periodStatementTo": "2026-06-30", "impactedStoreCode": "00788", "newStoreCode": "00990", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 0, "items": []}),
                ApiSpec("GET", "/api/v1/sgi/report/status-summary/export", "Export Excel", {"year": 2026, "status": "06", "result": "APPROVE", "region": ["RSU"], "storeType": ["A"], "impactedStoreCode": "00788", "newStoreCode": "00990"}, {"fileName": "insurance-verification-2026.xlsx"}),
                ApiSpec("GET", "/api/v1/sgi/master/factors", "อ่านปัจจัยภายนอก", {"q": "ก่อสร้าง", "active": True, "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "description": "ปิดช่องทางจราจร", "active": True}]}),
                ApiSpec("POST", "/api/v1/sgi/master/factors", "สร้างปัจจัยภายนอก", {"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "description": "ปิดช่องทางจราจร", "active": True, "reason": "เพิ่มปัจจัยใหม่"}, {"factorCode": "ROAD", "factorName": "ก่อสร้างถนน", "active": True}),
                ApiSpec("PUT", "/api/v1/sgi/master/factors/{code}", "แก้ปัจจัยภายนอก", {"factorName": "ก่อสร้างและปิดถนน", "description": "ปิดช่องทางจราจรบางส่วน", "active": True, "reason": "ปรับคำอธิบาย"}, {"factorCode": "ROAD", "factorName": "ก่อสร้างและปิดถนน", "active": True}),
                ApiSpec("GET", "/api/v1/sgi/master/competitors", "master แบรนด์คู่แข่ง 11 รายการ (รหัส 01-11) — เป็นแหล่งของ dropdown ร้านคู่แข่งในหน้าเอกสารด้วย", {"q": "108"}, {"items": [{"code": "01", "nameTh": "108 Shop", "nameEn": "108 Shop", "remark": "", "isActive": True}]}),
                ApiSpec("POST", "/api/v1/sgi/master/competitors", "เพิ่มแบรนด์คู่แข่ง — code/nameTh/nameEn บังคับ · รหัสซ้ำตอบ 409", {"code": "12", "nameTh": "ร้านคู่แข่งรายใหม่", "nameEn": "New Competitor", "remark": ""}, {"code": "12", "message": "saved"}),
                ApiSpec("PUT", "/api/v1/sgi/master/competitors/{code}", "แก้ชื่อ/สถานะ — ห้ามแก้ code เพราะถูกอ้างจาก sgi_document_competitors", {"nameTh": "ลอว์สัน 108", "nameEn": "Lawson 108", "remark": "", "isActive": True}, {"message": "saved"}),
                ApiSpec("DELETE", "/api/v1/sgi/master/competitors/{code}", "ลบแบรนด์คู่แข่ง — ถูกอ้างในเอกสารแล้วตอบ 409", {}, {"message": "deleted"}),
                ApiSpec("DELETE", "/api/v1/sgi/master/factors/{code}", "ลบปัจจัยภายนอกที่ไม่ถูกใช้งาน", {"reason": "ยกเลิกค่าทดสอบ"}, {"factorCode": "ROAD", "deleted": True}),
            ],
            ["Validate filter", "Build query", "Apply pagination/export mode", "Return rows or CSV", "For mutations validate reason and write audit"],
            ["missing year/status/result fails", "export uses same filters as preview", "master edit requires reason", "config locked value cannot edit"],
            ["report missing year", "report export", "factor duplicate", "operator audit", "config locked"],
        ),
        Topic(
            "BE/LLDD-BE-Job-Batch-Email-SRM",
            "LLDD BE - Job Batch and Email Integration",
            "BE",
            6.4,
            54,
            BE_OWNER_PEERAKORN,
            "ออกแบบ Backend contracts ฝั่ง **store-backend** สำหรับ interface tracking / รายการข้อความขาออกที่ยังไม่ได้ publisher confirm (2 เส้น · `POST /sgi/interface/sta/ack` ถูกตัด 2026-09-08 ตามมติข้อ 2.13) และ Notification Service (ส่งผ่าน @gosoft-sbp/email-lib) — ไม่มี Job Admin API, Email Template API (2026-08-06) และไม่มี SRM inbound adapter แล้ว (2026-08-07) · **⚠️ มติ 2026-09-02: งานสร้าง batch runner / scheduler / cli / job-failure notifier ถูกตัดออกจากเอกสารฉบับนี้** — batch job ทั้ง 12 ตัวย้ายไปรันบน `SBP/srm-sps-spsap-sop-sgi-batch` ที่มี dispatcher + `integration_log` + structured log พร้อมแล้ว เอกสารฉบับนี้เหลือเฉพาะ **ฝั่ง API ที่ยังอยู่ใน store-backend**",
            [],
            ["Interface tracking และรายการค้างส่ง APIs (2 เส้น · `/tracking` · `/pending-ack`)", "Notification adapter ผ่าน @gosoft-sbp/email-lib", "**ไม่มี STA ACK callback** — ตัดเมื่อ 2026-09-08 (ข้อ 2.13) เพราะสเปก STA ไม่มี ACK แบบ HTTP", "ไม่มี Batch Job Admin API และไม่มี inbound endpoint ของ SRM", "**ไม่รวม batch runner/scheduler** — อยู่ที่ sop-sgi-batch (มติ 2026-09-02)"],
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
                ApiSpec("GET", "/api/v1/sgi/interface/tracking", "ค้นสถานะ interface ตาม dataset/business key/status/ช่วงเวลา", {"dataName": "COMPENSATE_INIT_I", "status": "SENT", "pending": True, "sentFrom": "2026-07-01T00:00:00+07:00", "sentTo": "2026-07-22T23:59:59+07:00", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "items": [{"trackingId": 9912, "dataName": "COMPENSATE_INIT_I", "direction": "OUT", "businessKey": "2026/00098", "docNo": "2026/00098", "fileName": "COMPENSATE_INIT_I_25690722.dat", "status": "SENT", "sentAt": "2026-07-20T17:02:00+07:00", "ackedAt": None, "returnCode": None, "ageHours": 41}]}),
                ApiSpec("GET", "/api/v1/sgi/interface/pending-ack", "รายการข้อความขาออกที่ยังไม่ได้ publisher confirm ตาม watchdog rule อายุอย่างน้อย 1 วัน (path คงชื่อเดิม)", {"thresholdHours": 24, "dataName": "COMPENSATE_INIT_I", "page": 1, "size": 20}, {"page": 1, "size": 20, "total": 1, "count": 1, "items": [{"trackingId": 9912, "dataName": "COMPENSATE_INIT_I", "businessKey": "2026/00098", "docNo": "2026/00098", "fileName": "COMPENSATE_INIT_I_25690722.dat", "sentAt": "2026-07-20T17:02:00+07:00", "ageHours": 41, "returnCode": None}]}),
                # 2026-08-07: ตัด ApiSpec `POST /api/v1/integrations/srm/income-guarantee` ออก —
                # "SRM" ไม่ใช่ระบบต้นทาง เป็นเพียง prefix ของชื่อ resource (srm-sps-spsap-*) ·
                # SDD GI สไลด์ 75-77 ว่างเปล่า · ไม่มีเส้นนี้ใน 29 เส้นของ api.md ·
                # และหน้าที่ซ้ำกับ POST /sgi/document ที่ pipeline ใช้สร้างเอกสารอยู่แล้ว
            ],
            ["Receive request", "Validate schema", "Check idempotency", "Process records", "Log success/failure", "Return summary"],
            ["job run guard prevents duplicate running job", "email preview renders variables", "failed records include detail", "ไม่มี inbound endpoint ของ SRM แล้ว (ตัด 2026-08-07) — เอกสารต้องไม่อ้างถึงอีก"],
            ["run job", "run duplicate", "interface tracking filter", "watchdog ข้อความค้างส่ง (ยังไม่ publisher confirm)", "email preview"],
        ),
        *new_be_design_topics(),
    ]
    base.extend(document_detail_role_topics())
    db_map = {
        "BE/LLDD-BE-API-Document-List-Search": [
            ("workflow_transaction / workflow_approver (@srm/glb-workflow)", "R", "อ่าน inbox ผ่าน getPendingFlowByUser() · เฉพาะ section 06 ต้อง union เอกสารที่จบด้วย หยุดชดเชยประกันรายได้ เข้ามาด้วย (stoppedReopenable)"),
            ("sgi_compensation_documents", "R", "ค้นเอกสารตาม year/status/store"),
            ("sgi_impacted_stores", "R", "ชื่อร้าน ภาค และข้อมูลร้าน"),
            ("sgi_fgi_impact_sales_summaries", "R", "flag ข้อมูลผิดปกติ/ยอดขายไม่ครบ 60 วัน"),
            ("workflow_history (@srm/glb-workflow · sps_store)", "R", "ประวัติการเดิน state ของ engine (อ้างอิงเสริม ห้ามเขียน) (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("sgi_consideration_logs", "R", "ผลการพิจารณาสุดท้าย — คัดเอกสารที่จบด้วย หยุดชดเชยประกันรายได้ เข้าคิวของ section 06 (SDD สไลด์ 46 ข้อ 1.9)"),
        ],
        "BE/LLDD-BE-API-Document-Create-Update": [
            ("sgi_compensation_documents", "R/W", "สร้างหัวเอกสารและแก้ไข section หลัก"),
            ("workflow_transaction / workflow_approver (@srm/glb-workflow)", "W (ผ่าน lib)", "เปิด workflow งานแรกตอนสร้างเอกสารด้วย initializeWorkflow() + addPreApprover() — **ห้าม INSERT ตรง**"),
            ("sgi_document_new_stores", "R/W", "ร้านเปิดใหม่และ % ชดเชย"),
            ("sgi_document_competitors", "R/W", "ร้านคู่แข่งในเอกสาร"),
            ("sgi_document_running_numbers", "R/W", "ตัวนับเลขเอกสารต่อปี ค.ศ. — ออกเลข YYYY/xxxxx แบบ atomic (INSERT … ON CONFLICT DO UPDATE … RETURNING)"),
            ("sgi_document_cost_details", "R/W", "ยอดชดเชยแยกรายเดือน/รายร้านเปิดใหม่ (cost_year/cost_month · cost_target · cost_amount · _n / _nc)"),
            ("sgi_document_external_factors", "R/W", "ปัจจัยภายนอกในเอกสาร"),
            ("sgi_compensation_documents unique guard", "R", "กัน duplicate ด้วย business key: impact_process_id หรือ source + impacted_store_code + impact_month + new_store_code + round_no"),
        ],
        "BE/LLDD-BE-API-Document-Detail-Aggregate": [
            ("sgi_compensation_documents", "R", "หัวเอกสาร สถานะ และ section ปัจจุบัน"),
            ("sgi_impacted_stores", "R", "ข้อมูลร้านถูกกระทบ"),
            ("sgi_document_new_stores", "R", "ร้านเปิดใหม่และ compensate_percent"),
            ("sgi_document_competitors", "R", "คู่แข่ง"),
            ("sgi_document_external_factors", "R", "ปัจจัยภายนอก"),
            ("sgi_document_attachments", "R", "metadata ไฟล์แนบ"),
            ("sgi_consideration_logs", "R", "timeline/history"),
            ("sgi_document_cost_details", "R", "การ์ด \"คำนวณเงินชดเชย\" — ยอดแยกรายเดือน × รายร้านเปิดใหม่ (เพิ่ม 2026-09-09)"),
            ("sgi_compensation_histories", "R", "การ์ด \"ประวัติการชดเชย\" — ประวัติรายร้านข้ามเอกสาร (เพิ่ม 2026-09-09)"),
            ("sgi_competitors", "R", "ชื่อแบรนด์คู่แข่ง (join จาก sgi_document_competitors.brand_code) (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
        ],
        "BE/LLDD-BE-API-Document-Workflow-Actions": [
            ("workflow_transaction / workflow_history / workflow_approver (@srm/glb-workflow)", "R (เขียนผ่าน lib)", "eventWorkflow() เดิน state + บันทึก history"),
            ("sgi_compensation_documents", "W", "อัปเดต status/current_section/result"),
            ("sgi_consideration_logs", "W", "บันทึกผลพิจารณาและ comment"),
            ("workflow_route (@srm/glb-workflow · sps_store)", "R", "อ่าน `email_id` ของ route ที่เพิ่งเดิน เพื่อเลือก template อีเมล (ปิด DP-5) (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("business_user (ระบบ SBP เดิม)", "R", "resolve อีเมล/ชื่อของผู้ดำเนินการถัดไปที่ engine คืนมา (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("workflow_transaction (@srm/glb-workflow)", "R (เขียนผ่าน lib)", "กัน action ซ้ำด้วย getTransaction/getPermissionEvents ก่อน eventWorkflow — ห้าม UPDATE ตรง"),
        ],
        "BE/LLDD-BE-API-Workflow-Instances": [
            ("sgi_fgi_impact_processes / sgi_fgi_impact_stores", "R/W", "อ่านข้อมูล impact และอัปเดต workflow_generation_status W/Y/N"),
            ("sgi_fgi_impact_sales_summaries", "R", "growth_rate_diff / sales_status ที่ Gen Flow Gate ใช้ตัดสิน (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศ)"),
            ("sgi_impacted_stores", "R", "opt_dv_user_id ที่ Gen Flow Gate ใช้ตรวจว่ามี DV เจ้าของร้าน (เพิ่ม 2026-09-02)"),
            ("sgi_compensation_documents", "R/W", "create-if-missing จาก impact process และผูก docNo"),
            ("workflow_transaction (@srm/glb-workflow)", "W (โดย lib)", "initializeWorkflow() แทน K2 StartInstance — ห้าม INSERT ตรง"),
            ("workflow_approver (@srm/glb-workflow)", "W (ผ่าน lib)", "addPreApprover() ปักผู้รับงาน state 06 — **ห้าม INSERT ตรง**"),
            ("workflow_status / workflow_state (@srm/glb-workflow · sps_store)", "R", "lookup statusCode/status และ state แรก — ตาราง document_statuses/workflow_sections ของ SGI ถูกตัดแล้ว"),
            ("sgi_interface_transactions", "W", "บันทึกผลเรียกจาก Job 8b · ตาราง job_run_histories ถูกตัด 2026-08-06 — ผลการรันไปที่ application log"),
        ],
        "BE/LLDD-BE-API-Attachment-Sales-Timeline": [
            ("sgi_document_attachments", "R/W", "metadata ไฟล์แนบและ section ที่แนบ"),
            ("sgi_compensation_documents", "R", "ตรวจเอกสารและ impact_process_id"),
            ("sgi_fgi_impact_sales_summaries", "R", "หัวข้อมูลยอดขาย growth_rate_diff/total_working_days"),
            ("sgi_sales_transactions", "R", "ยอดขายรายวัน 4 windows"),
            ("sgi_consideration_logs", "R", "timeline/history"),
        ],
        "BE/LLDD-BE-API-Lookup": [
            ("sgi_impacted_stores (SGI) / store · mas_store · sevenshop (SBP เดิม)", "R", "store picker — SGI ไม่มีตาราง stores ของตัวเอง"),
            ("common_code (SBP เดิม · SGI_DOC_STATUS / SGI_APPROVE_LIMIT)", "R", "🔴 แก้ 2026-09-16 — lookup สถานะ 6 ค่าและขั้น 5 ค่าอ่านจาก common_code **ไม่ใช่ sps_store.workflow_status** เพราะตารางนั้นไม่มีคอลัมน์ลำดับ และ status_id เป็น integer surrogate ต่างกันตาม environment · วงเงินอนุมัติอยู่ที่ code_name ของ SGI_APPROVE_LIMIT"),
            ("workflow_status / workflow_state (@srm/glb-workflow · sps_store)", "R", "ชื่อสถานะฝั่ง engine — engine เป็นเจ้าของสถานะตอนรันไทม์ · lookup API ไม่ได้อ่านตารางนี้แล้ว"),
            ("business_user (SBP เดิม)", "R", "popup ค้นหาพนักงาน — SGI ไม่มีตาราง employees"),
            ("auth-backend groups / menus / permissions (ระบบเดิม)", "R", "RBAC/menu matrix — จัดการที่หน้า /setting/manage-user-rights เดิม · SGI อ่านผ่าน header x-user-permissions เท่านั้น ไม่มีตารางของตัวเอง"),
            ("email_template (SBP เดิม)", "R", "template — SGI อ่านผ่าน lib เท่านั้น ไม่แก้ของระบบเดิม"),
            ("email_sent (SBP เดิม)", "W (โดย email-lib)", "log การส่ง — SGI เรียก sendEmail() ด้วยเลข template จาก workflow_route.email_id แล้ว lib เขียนแถวให้เอง (DP-5 · 2026-08-14) · ⚠️ คอลัมน์ผู้ส่งคือ send_by ไม่ใช่ sent_by"),
        ],
        "BE/LLDD-BE-API-Report-and-Master-Data": [
            ("sgi_compensation_documents", "R", "แหล่งข้อมูลรายงานและ filter status/year"),
            ("sgi_compensation_histories", "R", "ยอดเงินชดเชยและงวด statement"),
            ("sgi_consideration_logs", "R", "ผลพิจารณาล่าสุด APPROVE/REJECT"),
            ("auth-backend group + scope (business_user_group) / prepared approver ของ @srm/glb-workflow", "R", "ผู้ปฏิบัติงาน — ตาราง operator_assignments ถูกตัด 2026-08-05"),
            ("sgi_external_factors", "R/W", "master ปัจจัยภายนอก"),
            ("sgi_competitors", "R/W", "master แบรนด์คู่แข่ง 11 รายการ (code 01-11 · name_th · name_en · remark) — feed dropdown ร้านคู่แข่งของหน้าเอกสาร"),
            ("sgi_document_competitors", "R", "ตรวจว่าแบรนด์ถูกอ้างในเอกสารก่อนลบ (409)"),
            ("sgi_document_external_factors", "R", "ตรวจว่าปัจจัยภายนอกถูกอ้างในเอกสารก่อนลบ (409) (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("sgi_document_new_stores", "R", "ยอด/%ชดเชยต่อร้านเปิดใหม่ในรายงาน (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("sgi_fgi_impact_processes", "R", "รอบชดเชย (roundNo) และงวดในรายงาน (เพิ่ม 2026-09-02 — SQL แตะอยู่แล้วแต่ไม่ได้ประกาศไว้)"),
            ("mas_param (SBP)", "R", "ค่ากำหนดกลางของระบบ SBP เดิม — **อ่านอย่างเดียว** (หน้า Global Config ของ SGI ถูกลบ 2026-08-06 · ระบบเดิมเป็นผู้แก้)"),
        ],
        "BE/LLDD-BE-Job-Batch-Email-SRM": [
            ("(backend config: config file/env)", "R", "enabled, cron, params ของ batch — ตาราง job_configs ถูกตัด 2026-08-06 ไม่มีหน้าจอควบคุม · **cron จริงตั้งที่ AWS Batch scheduled event ของ sop-sgi-batch ไม่ใช่ที่ store-backend**"),
            ("(application log แบบ structured)", "W", "ประวัติการรันและสถานะล่าสุด — ตาราง job_run_histories ถูกตัด 2026-08-06"),
            ("sgi_interface_transactions", "R/W", "tracking การรับส่งไฟล์/ข้อความ + outbox (สถานะจบที่ outbox_status = CONFIRMED)"),
            ("email_template (SBP)", "R", "subject_format/body_format ของระบบ SBP เดิม — อ่านอย่างเดียว"),
            ("email_sent (SBP)", "W (โดย email-lib)", "log การส่งของ batch — lib เขียนให้เอง"),
        ],
    }
    for topic in base:
        # FE-Testing-Delivery ใช้โครงเอกสารของตัวเอง (Test Suite Matrix / Release Gate)
        # ไม่ผ่าน renderer กลาง จึงไม่มีการวาด flow PNG — อย่าตั้ง flow_diagram ให้ชี้ไฟล์ที่ไม่มีจริง
        if (not topic.flow_diagram and not is_batch_monitor_doc(topic.file)
                and topic.file != "FE/LLDD-FE-Testing-Delivery"):
            topic.flow_diagram = f"LLDD/assets/flows/{sanitize_filename(topic.file)}.png"
        if not topic.db_tables and topic.file in db_map:
            topic.db_tables = db_map[topic.file]
    base.extend(be_job_topics())
    for topic in base:
        if topic.file in HIGH_LEVEL_ESTIMATES:
            topic.hours = HIGH_LEVEL_ESTIMATES[topic.file]
        # 2026-08-11: ถอด buffer ออก — ชั่วโมงที่แสดงคือค่าประเมินตรง ๆ ไม่บวกส่วนเผื่อ
        topic.base_hours = topic.hours
        topic.buffer = 0.0
        topic.days = round(topic.hours / HOURS_PER_DAY, 1)
    _unify_api_payloads(base)
    return base


def _payload_size(value: Any) -> int:
    """นับจำนวน key ทั้งหมดแบบ recursive — ใช้ตัดสินว่า payload ไหน 'ครบกว่า'"""
    if isinstance(value, dict):
        return len(value) + sum(_payload_size(v) for v in value.values())
    if isinstance(value, list):
        return sum(_payload_size(v) for v in value)
    return 0


def _merge_payload_keys(base: Any, other: Any) -> Any:
    """รวม **คีย์** ของสอง payload เข้าด้วยกัน โดยยึดค่าของ base เป็นหลัก

    ใช้กับ `_unify_api_payloads` เท่านั้น — จุดประสงค์คือ "ไม่ให้คีย์หายไป" ไม่ใช่รวมค่า
    ถ้า base ไม่มีคีย์ที่ other มี ให้ยกค่าจาก other มาเป็นตัวอย่าง
    """
    if isinstance(base, dict) and isinstance(other, dict):
        out = dict(base)
        for key, value in other.items():
            out[key] = _merge_payload_keys(out[key], value) if key in out else value
        return out
    if isinstance(base, list) and isinstance(other, list):
        donors = [x for x in other if isinstance(x, dict)]
        if not donors:
            return base
        # รวม schema ของทุก element ฝั่ง other แล้วเติมคีย์ที่ขาดให้ทุก element ของ base
        donor: dict[str, Any] = {}
        for item in donors:
            for key, value in item.items():
                donor.setdefault(key, value)
        return [_merge_payload_keys(x, donor) if isinstance(x, dict) else x for x in base] or other
    return base


def _unify_api_payloads(topic_list: list[Topic]) -> None:
    """1 endpoint = 1 สัญญา — ให้ทุกเอกสารที่ประกาศเส้นเดียวกันใช้ request/response ชุดเดียว

    เจอจริง 2026-09-02 ตอนไล่เอกสาร FE: เอกสารฝั่ง BE หลายฉบับใส่ตัวอย่าง response
    แบบย่อ (เช่น `GET /sgi/document/tasks` เหลือ 2 ฟิลด์) ขณะที่เอกสาร FE ของเส้นเดียวกัน
    ใส่ครบ 9 คอลัมน์ — dev ที่สร้าง BE จากเอกสารของตัวเองจะ implement ไม่ครบและ FE พัง
    ทั้งที่ไม่มีใครเขียนผิดสักคน · แก้ที่ต้นเหตุ: เลือกชุดที่ครบที่สุดของแต่ละเส้นแล้วใช้ร่วมกัน
    """
    richest: dict[tuple[str, str], dict[str, Any]] = {}
    for topic in topic_list:
        for api in topic.apis:
            if not api.path.startswith("/api/v1/sgi") or "*" in api.path:
                continue
            key = (api.method, api.path)
            slot = richest.setdefault(key, {"request": None, "response": None})
            for field_name in ("request", "response"):
                candidate = getattr(api, field_name)
                if candidate is None:
                    continue
                current = slot[field_name]
                if current is None or _payload_size(candidate) > _payload_size(current):
                    slot[field_name] = candidate
    # ⚠️ เลือก "ชุดที่ใหญ่ที่สุด" อย่างเดียวไม่พอ — ชุดที่ใหญ่กว่าอาจ **ขาดคีย์** ที่ชุดเล็กมี
    #    เจอจริง 2026-09-04: response ของ GET /sgi/document/{docNo} ที่ถูกเลือกมี actionOptions
    #    เป็น {label, requireComment} ขณะที่ชุดของเอกสาร role มี {value, label, requireComment}
    #    → FE จะส่ง label แทน value แล้ว 7-enum ไม่ตรง · จึงต้อง "รวมคีย์" ไม่ใช่แค่เลือกชุด
    for topic in topic_list:
        for api in topic.apis:
            key = (api.method, api.path)
            if key not in richest:
                continue
            for field_name in ("request", "response"):
                candidate = getattr(api, field_name)
                if candidate is None or richest[key][field_name] is None:
                    continue
                richest[key][field_name] = _merge_payload_keys(richest[key][field_name], candidate)
    for topic in topic_list:
        for api in topic.apis:
            slot = richest.get((api.method, api.path))
            if not slot:
                continue
            for field_name in ("request", "response"):
                if slot[field_name] is not None and getattr(api, field_name) is not None:
                    setattr(api, field_name, slot[field_name])


MAIN_INDEX_ORDER: dict[str, int] = {
        "FE/LLDD-FE-Integration-Contracts": 5,
        "FE/LLDD-FE-Foundation": 10,
        "FE/LLDD-FE-Document-Lists": 30,
        "FE/LLDD-FE-Create-Document": 40,
        "FE/LLDD-FE-Document-Detail": 50,
        "FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA": 51,
        "FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer": 52,
        "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion": 53,
        "FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion": 54,
        "FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP": 55,
        "FE/LLDD-FE-Report": 60,
        "FE/LLDD-FE-Master-Data": 70,
        "FE/LLDD-FE-Testing-Delivery": 90,
        "BE/LLDD-BE-Database-Structure": 100,
        "BE/LLDD-BE-Data-Migration-Cutover": 101,
        "BE/LLDD-BE-Integration-SBP-Platform": 102,
        # 2026-08-10: ย้ายมาจากลำดับ 156 (เดิมอยู่ท้ายกลุ่ม API) — เอกสารนี้นิยาม
        # state/status/route/part ของ @srm/glb-workflow ที่ BE-API-Document-Workflow-Actions
        # และ BE-API-Workflow-Instances ต้องใช้ ตารางเดิมจึงให้ผู้บริโภคเริ่มก่อนผู้นิยาม
        # (Workflow-Actions 21–27/08 · Workflow-Instances 24–27/08 vs Definition 27–31/08)
        # ลำดับนี้ทำให้เป็น blocker สัปดาห์แรกพร้อมอีก 3 ฉบับ ตรงกับ objective ของเอกสารเอง
        "BE/LLDD-BE-Workflow-Engine-Definition": 103,
        "BE/LLDD-BE-API-Common-Contracts": 105,
        "BE/LLDD-BE-API-Document-List-Search": 120,
        "BE/LLDD-BE-API-Document-Create-Update": 130,
        "BE/LLDD-BE-API-Document-Detail-Aggregate": 140,
        "BE/LLDD-BE-API-Document-Workflow-Actions": 150,
        "BE/LLDD-BE-API-Workflow-Instances": 155,
        "BE/LLDD-BE-API-Attachment-Sales-Timeline": 160,
        "BE/LLDD-BE-API-Lookup": 170,
        "BE/LLDD-BE-API-Report-and-Master-Data": 180,
        "BE/LLDD-BE-Job-Batch-Email-SRM": 190,
}


def _counted_topics() -> list["Topic"]:
    """เอกสารที่นับในยอดรวม — ตัด role pack ของ Document Detail ที่ชั่วโมงถูกนับไปแล้ว"""
    return [t for t in topics() if not is_document_detail_role_doc(t.file)]


def _grand_total_hours() -> int:
    """ยอดชั่วโมงรวมของชุดส่งมอบ (คำนวณสด ห้าม hardcode)"""
    return sum(total_hours(t) for t in _counted_topics())


def owner_workload() -> list[tuple[str, int, int, list[str]]]:
    """(owner, ชั่วโมงที่นับในยอดรวม, ชั่วโมงดิบ, เลข job ที่ถือ) — คำนวณจาก topics() เสมอ

    ⚠️ เพิ่ม 2026-09-07: ประโยคเรื่อง owner/ชั่วโมงเคยเขียนมือไว้ 4 ที่แล้วหลุดกันหมด
    (README บอก Bank ถือ migration+workflow definition · Main Index บอกถือแค่ batch job ·
     prose ในไฟล์เดียวกันยังเป็นการแบ่งงานรุ่น 2026-08-07) — ทุกประโยคต้องมาจากฟังก์ชันนี้
    """
    counted: dict[str, int] = {}
    raw: dict[str, int] = {}
    jobs: dict[str, list[str]] = {}
    for topic in topics():
        hours = total_hours(topic)
        raw[topic.owner] = raw.get(topic.owner, 0) + hours
        if not is_document_detail_role_doc(topic.file):
            counted[topic.owner] = counted.get(topic.owner, 0) + hours
        if topic.file.startswith("Jobs/"):
            jobs.setdefault(topic.owner, []).append(job_no_from_file(topic.file))
    out = [(o, counted.get(o, 0), raw.get(o, 0), sorted(jobs.get(o, []), key=lambda x: (len(x), x)))
           for o in raw]
    out.sort(key=lambda r: -r[1])
    return out


def owner_hours_map() -> dict[str, int]:
    return {o: c for o, c, _r, _j in owner_workload()}


def job_numbers() -> list[str]:
    """เลข job ทั้งหมดที่มีเอกสารจริง เรียงตามลำดับ (2,3,...,8b,...) — แหล่งเดียว"""
    nos = [job_no_from_file(t.file) for t in topics() if t.file.startswith("Jobs/")]
    def key(n: str) -> tuple[int, str]:
        m = re.match(r"(\d+)", n)
        return (int(m.group(1)) if m else 999, n)
    return sorted(nos, key=key)


def job_list_label() -> str:
    """ข้อความมาตรฐานสำหรับอ้างชุด batch job — ห้ามพิมพ์ช่วงเลขเอง

    ⚠️ เพิ่ม 2026-09-07: หลายที่ยังค้าง "Jobs 2-10 + 8b" ตั้งแต่ก่อนเพิ่ม Job 11/12 (2026-09-02)
    เขียนช่วงเลขด้วยมือแล้วชุดงานโตขึ้นเมื่อไร ข้อความก็ตกยุคทันที
    """
    nos = job_numbers()
    return f"Jobs {', '.join(nos)} (รวม {len(nos)} job)"


def _short_name(owner: str) -> str:
    """ชื่อเล่นในวงเล็บมุม เช่น `Aphiwit <Bank> Khammoon` -> `Bank`"""
    m = re.search(r"<([^>]+)>", owner)
    return m.group(1) if m else owner.split()[0]


def _owner_split_sentence() -> str:
    """ประโยคสรุปการแบ่งงาน — สร้างจาก owner จริงของทุกฉบับ ไม่เขียนมือ"""
    rows = owner_workload()
    job_owner = [r for r in rows if r[3]]
    parts = []
    for owner, counted, _raw, jobs in rows:
        who = _short_name(owner)
        if jobs:
            parts.append(f"**{who}** ถือ **batch job ทั้ง {len(jobs)} ฉบับ** (Job {', '.join(jobs)}) {counted} ชม.")
        else:
            parts.append(f"{who} {counted} ชม.")
    lead = ("แผนนี้รวม owner ตามบุคคล (ล่าสุด 2026-09-02 — **batch job ทั้งหมดรวมที่คนเดียว**): "
            "ทีม 6 คน แบ่งเป็น FE 2 คน BE 4 คน · Peerakorn ย้ายจากสาย FE ไปสาย BE ตั้งแต่ 2026-08-07 · ")
    tail = ""
    if len(job_owner) == 1:
        others = [r for r in rows if not r[3]]
        tail = (f" · เอกสารฝั่ง Database Structure / Data Migration / Workflow Engine Definition "
                f"**ไม่ได้อยู่กับ {_short_name(job_owner[0][0])} แล้ว** — ย้ายไปกับเจ้าของสายนั้น ๆ")
    return lead + " · ".join(parts) + tail


def _bank_move_effect() -> str:
    """ผลจริงของการย้าย 3 เอกสารออกจากเจ้าของ batch job — บอกตัวเลข ไม่ใช่บอกเจตนา

    ⚠️ แก้ 2026-09-07: ข้อความเดิมอ้างเจตนาว่าย้ายออกแล้วสายงาน job จะลงกรอบพอดี
    ซึ่งอ่านแล้วเข้าใจว่าทำสำเร็จแล้ว — แต่บรรทัดกติกาเวลาในไฟล์เดียวกันบอกว่ายังเกินกรอบ
    ประโยคนี้จึงต้องรายงาน "ผลที่ได้จริง" จากตัวเลข ไม่ใช่ "เจตนาตอนย้าย"
    """
    moved = [t for t in _counted_topics()
             if t.file in ("BE/LLDD-BE-Database-Structure",
                           "BE/LLDD-BE-Data-Migration-Cutover",
                           "BE/LLDD-BE-Workflow-Engine-Definition")]
    moved_hours = sum(total_hours(t) for t in moved)
    now = _bank_total_hours()
    ceiling = 4 * HOURS_PER_WEEK
    before = now + moved_hours
    head = (f"ย้ายออกเมื่อ 2026-09-02 · ลดภาระจาก {before} เหลือ {now} ชม. (−{moved_hours} ชม.)")
    if now <= ceiling:
        return f"({head} — ลงกรอบ 4 สัปดาห์ {ceiling:g} ชม. แล้ว)"
    return (f"({head} · **แต่ยังเกินกรอบ 4 สัปดาห์อยู่ {now - ceiling:g} ชม.** "
            f"= {now / HOURS_PER_WEEK:.1f} สัปดาห์ — ยังต้องกระจาย job ออกไปอีกหรือเลื่อนกำหนดส่ง "
            f"ดูข้อค้างใน `DECISIONS-รอตัดสินใจ.md`)")


def _workload_rule_sentence() -> str:
    """กติกาเวลาทำงาน + สถานะว่าใครเกินกรอบ — ตัวเลขเดียวกับ README ทุกตัว"""
    ceiling = 4 * HOURS_PER_WEEK
    rows = owner_workload()
    over = [r for r in rows if r[1] > ceiling]
    base = (f"**กติกาเวลาทำงาน:** 1 สัปดาห์ = {WORKDAYS_PER_WEEK} วัน · 1 วัน = {HOURS_PER_DAY} ชม. "
            f"(**{HOURS_PER_WEEK:g} ชม./สัปดาห์**) · กรอบส่งมอบ 4 สัปดาห์ = **{ceiling:g} ชม./คน** "
            f"(ทีม 6 คน = {6 * ceiling:g} ชม. เทียบงานจริง {_grand_total_hours()} ชม.)")
    if not over:
        return base + " · ทุกคนอยู่ในกรอบ"
    who = " · ".join(f"**{_short_name(o)} {c} ชม. = {c / HOURS_PER_WEEK:.1f} สัปดาห์** "
                     f"(เกินกรอบ {c - ceiling:g} ชม.)" for o, c, _r, _j in over)
    return (base + f" · 🔴 **ยังไม่ลงกรอบ:** {who} — "
            "ต้องกระจาย batch job ออกไปหรือเลื่อนกำหนดส่ง (ข้อค้างใน `DECISIONS-รอตัดสินใจ.md`) "
            "· ประโยคที่บอกว่า \"ย้ายงานแล้วจบใน 4 สัปดาห์\" ยังไม่เป็นจริงตามตัวเลขนี้")


def _readme_owner_line() -> str:
    rows = owner_workload()
    job_rows = [r for r in rows if r[3]]
    if not job_rows:
        return "- Track ownership: (no batch-job owner assigned)"
    owner, counted, _raw, jobs = job_rows[0]
    other_docs = sorted({t.file.split("/")[-1] for t in _counted_topics()
                         if t.owner == owner and not t.file.startswith("Jobs/")})
    extra = (" plus " + ", ".join(other_docs)) if other_docs else \
            " and nothing else - Database Structure, Data Migration/Cutover and Workflow Engine Definition sit with their own track owners"
    return (f"- Track ownership (latest 2026-09-02): `{owner}` owns **all {len(jobs)} batch jobs** "
            f"(Job {', '.join(jobs)}){extra} - {counted} hours")


def _readme_capacity_line() -> str:
    """คำเตือนกำลังคน — ทุกตัวเลขคำนวณสด รวมทั้งจำนวนสัปดาห์และช่วงชั่วโมงของคนอื่น

    ⚠️ ของเดิมเขียนมือแล้วผิด 2 จุด: "25 working days = about 7 weeks" (จริงคือ 5 สัปดาห์)
    และ "everyone else 92-123 hours" (จริง Vava 145 · Pete 139)
    """
    ceiling = 4 * HOURS_PER_WEEK
    rows = owner_workload()
    over = [r for r in rows if r[1] > ceiling]
    if not over:
        top = rows[0]
        return (f"- Capacity: heaviest load is `{top[0]}` at {top[1]} hours "
                f"({top[1] / HOURS_PER_WEEK:.1f} weeks) - inside the {ceiling:g}-hour 4-week ceiling")
    owner, counted, _raw, _jobs = over[0]
    rest = [r[1] for r in rows if r[0] != owner]
    return (f"- \u26a0\ufe0f **Capacity warning:** `{owner}` carries **{counted} hours**, "
            f"{counted / ceiling:.2f}x the 4-week ceiling of {ceiling:g} hours - that is "
            f"**{counted / HOURS_PER_WEEK:.1f} weeks** at {HOURS_PER_WEEK:g} hours/week "
            f"({counted / HOURS_PER_DAY:.0f} working days at {HOURS_PER_DAY} h/day). "
            f"Everyone else ranges {min(rest)}-{max(rest)} hours "
            f"({min(rest) / HOURS_PER_WEEK:.1f}-{max(rest) / HOURS_PER_WEEK:.1f} weeks), so "
            f"{sum(1 for r in rest if r <= ceiling)} of {len(rest)} finish inside 4 weeks. "
            f"The plan does not fit until the batch jobs are shared out or the deadline moves - "
            f"see DECISIONS-\u0e23\u0e2d\u0e15\u0e31\u0e14\u0e2a\u0e34\u0e19\u0e43\u0e08.md")


def _bank_total_hours() -> int:
    """ยอดชั่วโมงของเจ้าของงานที่รับ migration + batch job ทั้งหมด"""
    return sum(total_hours(t) for t in _counted_topics() if t.owner == BANK_BE_OWNER)


def main_index_ordered(all_topics: list[Topic]) -> list[Topic]:
    """ลำดับที่ใช้คำนวณตารางเวลา — ต้องเป็นลำดับเดียวกันทุกที่ ไม่งั้นวันที่จะเพี้ยน"""
    return sorted(all_topics, key=lambda t: MAIN_INDEX_ORDER.get(t.file, 999))


def main_doc_blocks(all_topics: list[Topic]) -> list[dict[str, Any]]:
    ordered = main_index_ordered(all_topics)
    counted_topics = [t for t in ordered if not is_document_detail_role_doc(t.file)]
    be_jobs = [t for t in counted_topics if t.file.startswith("Jobs/")]
    high_level = [t for t in counted_topics if not t.file.startswith("Jobs/")]
    role_docs = [t for t in ordered if is_document_detail_role_doc(t.file)]
    fe = [t for t in high_level if t.track == "FE"]
    be = [t for t in high_level if t.track == "BE"]
    schedule = build_topic_schedule(counted_topics)   # ตรวจว่า dependency ไม่ขัดกัน
    steps = dependency_steps(counted_topics)
    rows = [
        [
            t.track,
            t.title.replace("LLDD ", ""),
            (f"{total_hours(t)}" if not unit_test_hours(t)
             else f"**{total_hours(t)}** (impl {t.hours} + test {unit_test_hours(t)})"),
            f"{steps[t.file]}",
            t.owner,
            Path(t.file).name,
        ]
        for t in high_level
    ]
    owner_stats: dict[str, dict[str, Any]] = {}
    for topic in counted_topics:
        key = topic.owner
        owner_stats.setdefault(key, {"hours": 0, "base": 0, "tracks": set(), "topics": []})
        owner_stats[key]["hours"] += topic.hours
        owner_stats[key]["test"] = owner_stats[key].get("test", 0) + unit_test_hours(topic)
        owner_stats[key]["base"] += topic.base_hours
        owner_stats[key]["tracks"].add(topic.track)
        owner_stats[key]["topics"].append(topic.title.replace("LLDD FE - ", "").replace("LLDD BE - ", ""))
    owner_order = [
        FE_OWNER_KITTISAK,
        FE_OWNER,
        BE_OWNER_BUTSABA,
        BE_OWNER,
        BE_OWNER_PEERAKORN,
        BANK_BE_OWNER,
    ]
    continuity = {
        FE_OWNER_KITTISAK: "FE หน้าจอเอกสาร (สายลึกที่สุดของ FE): Document Detail/Action (+ role pack 5 ฉบับ) -> Master Data -> Create Document",
        FE_OWNER: "FE ที่ต่อกับระบบเดิม: Integration Contracts (auth/session/permission จาก BFF) -> Foundation (sidebar/header/menu gating ของ portal เดิม) -> Document Lists -> Report -> Testing/Delivery",
        BE_OWNER_BUTSABA: "BE เอกสาร/สัญญากลางของ SGI เอง: Common Contracts -> List/Search -> Create/Update -> Detail Aggregate (ทุก job ย้ายไป Aphiwit แล้วตามมติ 2026-09-02)",
        BE_OWNER: "BE ที่ต่อกับระบบเดิม + **เรียกใช้ engine**: Integration with SBP Platform -> Workflow Instances (initializeWorkflow) -> Workflow Actions (eventWorkflow = trigger event) -> Lookup",
        BE_OWNER_PEERAKORN: "BE support/interface (ย้ายจากสาย FE 2026-08-07): Batch/Email -> Attachment/Sales/Timeline -> Report and Master Data",
        BANK_BE_OWNER: "**batch job ทั้งหมด 12 ฉบับ** (Jobs 2-12 + 8b · มติ 2026-09-02): Job 2, 3 (นำเข้า ALLMAP) -> Job 4, 5 (IAS/MIS ผ่าน EAI S3) -> Job 6 (ส่ง STA) + Job 11 (รับกลับจาก STA) -> Job 8, 8b (สร้างเอกสาร + เปิด workflow) -> Job 7, 9 (sync เข้าเอกสาร) -> Job 10, 12 (watchdog + เตือนงานค้าง) · **ไม่ถือ Database Structure / Data Migration / Workflow Engine Definition แล้ว** " + _bank_move_effect() + "",
    }
    owner_rows = []
    for key in owner_order:
        if key not in owner_stats:
            continue
        hours = owner_stats[key]["hours"]
        tests = owner_stats[key].get("test", 0)
        # tracks เป็น set — ถึงสาขานี้จะเหลือสมาชิกเดียวเสมอ (len > 1 แยกไปทางซ้ายแล้ว)
        # ก็ใช้ sorted() ให้ผลคงที่โดยไม่ต้องพึ่งเงื่อนไขข้างหน้า
        role = "FE & BE" if len(owner_stats[key]["tracks"]) > 1 else sorted(owner_stats[key]["tracks"])[0]
        owner_rows.append([role, key, f"**{hours + tests}** (impl {hours} + test {tests})", continuity[key]])

    if set(owner_stats) != set(owner_order):
        raise ValueError("LLDD schedule must include all six developers")
    for owner, stats in owner_stats.items():
        work_weeks = (stats["hours"] + stats.get("test", 0)) / HOURS_PER_WEEK

    def summary_scope(topic: Topic, count: int) -> str:
        items = topic.scope[:count]
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
        h(2, "2.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], [
            ["Input", "Topic inventory, owner assignment, estimates, screenshots, API/job/database scope, and schedule assumptions for the SBP Mall income-guarantee work package."],
            ["Progress", "Use this index to sequence FE/BE work, confirm owner workload, locate detailed topic documents, and track dependency readiness before development starts."],
            ["Output", "A single implementation index with activity plan, owner workload, FE/BE summaries, job breakdown, dependencies, and deliverable checklist."],
        ]),
        h(1, "3. High Level Activity Plan"),
        table(["Track", "หัวข้อ", "ชั่วโมง (impl + unit test)", "ลำดับขั้น", "Owner", "เอกสารรายละเอียด"], rows),
        h(1, "4. Workload Balance and Continuity"),
        p(_owner_split_sentence()),
        # เอกสารฉบับนี้เคยไม่บอกกติกาเวลาทำงานเลย ผู้อ่านจึงตัดสินไม่ได้ว่า 211 ชม. พอดีกรอบไหม (เพิ่ม 2026-09-07)
        p(_workload_rule_sentence()),
        table(["Role", "Owner", "ชั่วโมง (impl + unit test)", "Work Focus"], owner_rows),
        h(1, "5. FE Summary"),
        table(["FE Topic", "ชั่วโมง", "ลำดับขั้น", "Deliverable"], [[t.title.replace("LLDD FE - ", ""), t.hours, steps[t.file], summary_scope(t, 3)] for t in fe]),
        h(1, "6. Document Detail Role Pack"),
        p("เอกสารลูก 5 ฉบับนี้เป็นรายละเอียดแยกตาม role สำหรับอ่านประกอบ LLDD-FE-Document-Detail ไม่ถูกนับซ้ำใน activity plan/hour รวม"),
        table(["Role document", "Parent", "Hour allocation"], [[Path(t.file).name, "LLDD-FE-Document-Detail", "included in parent hours"] for t in role_docs]),
        h(1, "7. BE Summary"),
        table(["BE Topic", "ชั่วโมง", "ลำดับขั้น", "Deliverable"], [[t.title.replace("LLDD BE - ", ""), t.hours, steps[t.file], ", ".join(t.scope[:4])] for t in be]),
        h(1, "8. BE Batch Job Breakdown"),
        table(
            ["Job", "ชั่วโมง", "ลำดับขั้น", "Owner", "เอกสารรายละเอียด"],
            [
                [
                    t.title.replace("LLDD BE - ", ""),
                    t.hours,
                    steps[t.file],
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
            ["Master Data contract", "FE/BE", "LLDD-FE-Master-Data ใช้ LLDD-BE-API-Report-and-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง (ไม่มี Operator/Menu Permission/System Config/Audit แล้ว — ใช้ระบบ SBP เดิม)"],
            ["Blocker ลำดับขั้นที่ 1", "BE", "LLDD-BE-Integration-SBP-Platform, LLDD-BE-Workflow-Engine-Definition, LLDD-BE-Database-Structure และสัญญากลางของ LLDD-API ต้องปิดก่อน เพราะเอกสาร BE ทุกฉบับอ้างอิง 4 ชิ้นนี้"],
            ["Auth/JWT platform และ menu service", "Platform/SSO/IAM", "FE Foundation เรียก /auth/profile + /users/current + /menus + /groups/current-user/permissions ของระบบเดิม; SGI รับตัวตนจาก BFF ผ่าน header x-api-key/x-user-id/x-user-group-id/x-user-permissions"],
            ["Mock/fixture data", "BE", "FE development และ SIT"],
            ["Screenshots/prototype", "FE", "UI implementation"],
            ["Business rules", "BA/BE", "validation/action/report"],
        ]),
        h(1, "10. Deliverable Checklist"),
        bullets(["Main LLDD Index", "Common contract LLDD สำหรับ API/FE integration", "LLDD-FE-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง", "Detailed FE LLDD per SBP Mall page group", f"Detailed BE LLDD per SBP Mall API group and {job_list_label()}", "Database Structure, Data Migration/Cutover, Integration with SBP Platform และ Workflow Engine Definition (เพิ่ม 2026-08-07)", "Screenshots embedded only for SBP Mall implementation pages", "Implementation flow diagrams embedded as reference, not Flow page deliverables"]),
    ]


def db_dictionary_blocks() -> list[dict[str, Any]]:
    """พจนานุกรมข้อมูลรายตาราง/รายคอลัมน์ของ 20 ตารางใหม่ (โซน A/B/C)

    เนื้อหาอยู่ที่ ``tools/lldd_db_dictionary.py`` — แยกไฟล์เพราะยาวมาก
    และรายชื่อคอลัมน์ถูกดึงสดจาก DDL ในไฟล์นี้เอง จึง drift ไม่ได้
    """
    from lldd_db_dictionary import dictionary_blocks

    return dictionary_blocks()


def sgi_endpoint_count() -> int:
    """จำนวน endpoint ของ SGI — คำนวณสดจาก api_endpoint_groups() ห้าม hardcode ที่อื่น

    2026-09-08: เลข 29 ถูกพิมพ์ตายไว้ในประโยค "ไม่มี endpoint ของตัวเอง" ที่เดียว
    แล้วกระจายไปค้างอยู่ในเอกสาร 16 ฉบับ (job 12 + BE 4) หลังตัดเหลือ 28 เส้น
    """
    return sum(int(row[1]) for row in api_endpoint_groups())


def api_endpoint_groups() -> list[list[Any]]:
    return [
        # 6 กลุ่ม (ตรงกับ api.md และ plan-api.html) — Auth ถูกตัดทั้งกลุ่ม 2026-08-05 (ใช้ระบบ SBP เดิม)
        # ยอดรวมอ่านด้วย sgi_endpoint_count() เสมอ — ห้ามพิมพ์เลขรวมไว้ในคอมเมนต์นี้อีก (เคยค้างที่ 29)
        ["งาน & เอกสารประกันรายได้", "11", "GET /sgi/document/tasks, GET/POST/PUT /sgi/document*, POST /sgi/document/{docNo}/actions, attachments, sales, timeline", "core document workflow API"],
        ["Lookup / Reference", "2", "GET /sgi/lookup/document-statuses, /sgi/lookup/workflow-sections", "read-only reference ที่ไม่มีหน้าจอดูแล (ร้าน/ภาค/ประเภทสาขา ใช้ของระบบ SBP เดิม)"],
        ["Master Data", "8", "factors CRUD, competitors CRUD", "master ที่มีหน้าจอดูแลของตัวเอง (ไม่มี audit · ยกเลิกระบบ audit ของ master 2026-08-07)"],
        ["รายงาน", "2", "GET /sgi/report/status-summary, /export", "accounting search/export Excel (14 columns, SDD slide 60)"],
        ["Workflow ภายใน", "3", "POST /sgi/workflow/instances, GET /sgi/workflow/instances/{id}, /sgi/workflow/summary", "internal workflow engine for Job 8b"],
        ["Interface Tracking", "2", "GET /sgi/interface/tracking, GET /sgi/interface/pending-ack", "tracking การรับส่งไฟล์/ข้อความ + รายการขาออกที่ยังไม่ publisher confirm (ตัด GET /dashboard/summary ออก 2026-08-06 · ตัด POST /integrations/srm/income-guarantee 2026-08-07)"],
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
            ])
            if endpoint.get("resNote"):
                blocks.append(p(api_doc_text(endpoint["resNote"])))
            blocks.extend([
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
        p("เอกสารนี้เป็น LLDD API ระดับรวมของระบบ SGI/SBP Mall ใช้เป็น master reference สำหรับ REST contract, auth, error, endpoint catalog, implementation pattern และ test scope ของ BE API LLDD รายกลุ่ม"),
        h(1, "2. Scope"),
        table(
            ["Item", "Detail"],
            [
                ["API base", "/api/v1"],
                ["Endpoint count", f"{endpoint_total} endpoints, {len(groups)} groups"],
                ["Detailed implementation docs", ", ".join(Path(t.file).name for t in be_api_topics)],
                ["Out of scope", "Login/Auth implementation ของ platform, SAP/SR process ภายนอก, หน้าจอข้อมูลผิดปกติที่ถูกตัดออกจากขอบเขตแล้ว"],
            ],
        ),
        h(2, "2.1 Input / Progress / Output Contract"),
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
                ["Status convention", "API ส่ง `statusCode`; FE resolve label จาก `/sgi/lookup/document-statuses`", "ห้ามส่ง label ไทยแทน code ใน field ที่กำหนดเป็น canonical code"],
                ["Role namespace", "`roleCode` = RBAC role, `sectionCode` = workflow section, `roleProfileCode` = P-06/P-08/P-01/P-02/P-03", "ป้องกันการชนความหมายของเลข 01/02/03/06/08"],
                ["Pagination", "GET list ใช้ `page,size` และคืน `{page,size,total,items}`", "size max 100 ตาม common contract"],
                ["Errors", "คืน `{code,message}`; message ภาษาไทยตาม SRS ถ้ามี", "FE แสดง message ตรง ๆ ไม่ paraphrase"],
                ["Mutation audit", "workflow action ลง sgi_consideration_logs เท่านั้น (ยกเลิกระบบ audit ของ master 2026-08-07 · jobs เขียน application log)", "mutation ที่ต้องมี reason ต้อง validate ก่อนเริ่ม transaction"],
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
                ["Document workflow", "create duplicate, submit no result, invalid result for role profile, current task conflict, threshold ≥ 100,000 -> AVP route (SDD GI)"],
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
    """20 target tables: 34 -> 24 (ตัด 10 ตารางที่ระบบ SBP เดิมมีอยู่แล้ว 2026-08-06)
    -> 22 (ตัด job_configs/job_run_histories พร้อม 2 tab ควบคุมของหน้า Batch Job)
    -> 21 (ตัด audit_logs 2026-08-07) -> 20 (ตัด decisions ไป common_code · มติ DP-9 2026-08-10).
    แถวที่ zone = "REF" เป็น schema reference สำหรับ dev เท่านั้น ไม่นับใน 21 ตาราง.
    """
    return [
        ["A", "sgi_fgi_impact_stores", "id", "impact_process_id, impacted_store_code", "impact pair; sales request and allocation data"],
        ["A", "sgi_fgi_impact_processes", "id", "impacted_store_code", "impact process hub and canonical workflow_generation_status"],
        ["A", "sgi_fgi_impact_sales_summaries", "id", "impact_process_id", "sales summary/growth rate"],
        ["A", "sgi_sales_transactions", "id", "sales_summary_id", "daily sales 4 windows x 15 days"],
        ["A", "sgi_fgi_impact_competitors", "id", "impact_process_id", "ALLMAP competitors"],
        ["A", "fcs_qssi_score", "id", "store_id + category + month + year", "QSSI scores — ⚠️ REUSE ตารางเดิมของ sps_store (เอกพจน์ · 24,284,545 แถว · มี import pipeline POST /performance/import-qssi ใช้งานอยู่) ห้ามสร้างใหม่ และห้ามใช้ชื่อพหูพจน์ fcs_qssi_scores"],
        ["A", "sgi_interface_transactions", "id", "impact_process_id/sales_summary_id/doc_no", "interface tracking replacement"],
        ["B", "sgi_compensation_documents", "doc_no", "impact_process_id, status_code, current_section_code", "document header/core"],
        ["B", "sgi_document_new_stores", "id", "doc_no, new_store_code", "new stores, compensate percent and amount"],
        ["B", "sgi_document_competitors", "id", "doc_no, competitor_store_code", "document competitors"],
        ["B", "sgi_document_external_factors", "id", "doc_no, factor_code", "document external factors"],
        ["B", "sgi_consideration_logs", "id", "doc_no", "approval/action history (decision code, result category, attachments)"],
        ["B", "sgi_document_attachments", "attach_id", "doc_no", "attachment metadata; file storage uses existing SBP S3 service"],
        ["B", "sgi_compensation_histories", "id", "store_code, ref_doc_no", "compensation history/accounting export"],
        ["B", "sgi_document_cost_details", "id", "doc_no, new_store_code", "monthly cost detail per new store (ImpactCostDetail)"],
        ["B", "sgi_document_running_numbers", "year", "-", "atomic YYYY/xxxxx running number"],
        ["C", "sgi_impacted_stores", "store_code", "store.store_id (SBP · varchar(10))", "SP impacted store subset"],
        
        ["C", "sgi_external_factors", "factor_code", "-", "external factor master"],
        ["C", "sgi_competitors", "competitor_code", "-", "competitor master"],
        ["-", "USE EXISTING SBP TABLES", "-", "-",
         "workflow engine 13 ตาราง ใน schema sps_store (workflow · workflow_version · workflow_state · workflow_status · workflow_event · workflow_route · "
         "workflow_group · workflow_group_map · workflow_transaction · workflow_history · workflow_approver · workflow_part · workflow_part_display) "
         "· store/mas_store/sevenshop · mas_zone · common_code · business_user · email_template + email_sent · mas_param · fcs_qssi_score "
         "— decided 2026-08-05/2026-08-06: do NOT recreate these in SGI"],
    ]


def ddl_check_count() -> int:
    """นับ CHECK constraint จาก DDL จริง — ห้าม hardcode เลขนี้ที่อื่น
    (2026-09-08: เคยเขียนตายไว้ 22 แล้วค้างทันทีที่เพิ่ม CHECK ของ outbox_status)"""
    return sum(body.count("CHECK (") for _, body in database_ddl_sections())


def database_ddl_sections() -> list[tuple[str, str]]:
    return [
        ("5.1 Zone C — Shared Master, RBAC, Config and Operations", """-- ❌ ไม่สร้างตาราง stores ใน SGI — ใช้ store / mas_store / sevenshop ของระบบ SBP เดิม (API: GET /store/search · /store/list · /store/detail)

CREATE TABLE sgi_impacted_stores (
    store_code VARCHAR(5) PRIMARY KEY,   -- ร้าน SP · master อยู่ที่ store/mas_store/sevenshop ของระบบเดิม
    dv_code VARCHAR(20), opt_dv_user_id VARCHAR(30), latitude NUMERIC(10,7), longitude NUMERIC(10,7),
    -- CompTransferSBPDate ของ CompensateFlow เดิม — ใช้แยกร้านที่โอนเป็นแฟรนไชส์ก่อน/หลัง 1/10/2014
    -- entity ใน LLDD-BE-API-Lookup / Document-List-Search / Document-Detail-Aggregate map คอลัมน์นี้อยู่แล้ว
    transfer_sbp_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ❌ ไม่สร้างตาราง workflow_sections ใน SGI — ใช้ workflow_state / workflow_route ของ @srm/glb-workflow · วงเงินอนุมัติเก็บใน common_code (SGI_APPROVE_LIMIT)

-- ❌ ไม่สร้างตาราง document_statuses ใน SGI — ใช้ workflow_status ของ @srm/glb-workflow

-- ❌ ไม่สร้างตาราง roles ใน SGI — ใช้ auth-backend/ABS groups ของระบบ SBP เดิม (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง menus ใน SGI — ใช้ menus/permissions ของ auth-backend (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง menu_permissions ใน SGI — ใช้ permissions ต่อ URL ของ auth-backend (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง employees ใน SGI — ใช้ business_user / business_user_group ของระบบ SBP เดิม

-- หมายเหตุ sgi_impacted_stores: opt_dv_user_id ไม่มี FK — ผู้ใช้อยู่ที่ business_user
--   ของระบบ SBP เดิม (ตัดตาราง employees ออกเมื่อ 2026-08-05)
--   ⚠️ แก้ 2026-09-09: เดิมบรรทัดนี้เขียนเป็น "ALTER TABLE sgi_impacted_stores" ค้างไว้
--      โดยไม่มีเนื้อคำสั่งและไม่มี ; — ถ้าก๊อป DDL ไปรันจริงจะ syntax error

-- ❌ ไม่สร้างตาราง operator_assignments ใน SGI — ใช้ group + scope ของ auth-backend + prepared approvers ของ @srm/glb-workflow (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง decisions ใน SGI — มติ DP-9 (2026-08-10) ย้ายไป common_code ของระบบ SBP เดิม
--    code_type='SGI_DECISION' · code_value=decision_code · code_name=decision_name
--    code_mapping=flow_name · other_value=result_name · remark=result_category+engine_event (จำกัด 50 ตัวอักษร)
--    FE อ่านผ่าน GET /common/common-code?codeType=SGI_DECISION (ตัดเส้น GET /decisions ออกแล้ว)
-- ⚠️ common_code ไม่มี PK และไม่มี unique constraint → กันรหัสซ้ำที่ระดับแอป
--    และต้องลงทะเบียน code_type ที่ common_code_type ก่อนใช้งาน

CREATE TABLE sgi_external_factors (
    factor_code VARCHAR(30) PRIMARY KEY,
    factor_name VARCHAR(200) NOT NULL, factor_remark VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- master แบรนด์คู่แข่ง 11 รายการ (รหัส 01-11) — ระบบเดิมเก็บชื่อทั้งไทยและอังกฤษ
-- คนละระดับกับ sgi_document_competitors ที่เก็บ "รายสาขา" พร้อมรหัสจาก ALLMAP (เช่น 4832, TD58_08)
CREATE TABLE sgi_competitors (
    competitor_code VARCHAR(30) PRIMARY KEY,
    name_th VARCHAR(200) NOT NULL,
    name_en VARCHAR(200) NOT NULL,
    remark VARCHAR(500),                 -- คอลัมน์ "รายละเอียดเพิ่มเติม" ของหน้า k2-competitors.html
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ❌ ไม่สร้างตาราง email_templates ใน SGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง email_template ของระบบ SBP เดิม (email_template_id · subject_format · body_format) + email_sent

-- ❌ ไม่สร้างตาราง status_email_rules (ปิด DP-5 · แก้มติ 2026-08-14) — workflow ให้เลข template ผ่าน workflow_route.email_id แล้ว SGI เรียก email-lib ส่งเอง
--    อีเมลของ batch job (EM-07 error · EM-08 watchdog) ไม่ใช่ workflow event → ส่งผ่าน @gosoft-sbp/email-lib ของระบบเดิม
--    ผู้รับของ batch job อยู่ใน backend config (config file/env) ไม่ใช่ตารางของ SGI


-- ❌ ไม่สร้างตาราง user_accounts ใน SGI — ใช้ AWS Cognito + auth-backend — SGI รับตัวตนจาก header ของ BFF (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง system_configs ใน SGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง mas_param ของระบบ SBP เดิม (param_name · param_value · ref_name · description · is_config · active_flag)"""),
        ("5.2 Zone A — Impact Pipeline, Sales and Interface", """CREATE TABLE sgi_fgi_impact_processes (
    id BIGSERIAL PRIMARY KEY,
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES sgi_impacted_stores(store_code),
    -- 'YYYY-MM' (ค.ศ.) = **งวดที่ร้านถูกกระทบ** (ไม่ใช่งวดที่จ่ายชดเชย)
    -- ✅ มติ 2026-09-12 (DECISIONS 2.38 ข้อ 3) — ต้นทางตอน migrate คือ
    --    `FGI_IMPACT_STORE.YEAR` + `MONTH` ของคู่ร้าน  ==  `FGI_IMPACT_STORE_ON_PROCESS.START_COMPENSATE_*`
    --    หลักฐาน: ExportJdbc บรรทัด 684-699 ตอน insert ตั้ง start_compensate = last_compensate = fis.month/fis.year
    --      และข้อมูลจริงยืนยัน start_compensate ตรงกับงวดของคู่ร้าน **7,545 จาก 7,548 แถว (99.96%)**
    --    🔴 **ห้ามใช้ `LAST_COMPENSATE_*`** — ถูกเลื่อนไปเรื่อย ๆ ตามงวดที่จ่าย ข้อมูลจริง**เลื่อนไปแล้ว 3,747
    --       จาก 7,548 แถว (49.6%)** ใช้แล้วจะได้งวดผิดครึ่งหนึ่งของข้อมูล
    --    กรอบงวดที่ชดเชยได้อยู่ที่ start_compensate_* / end_compensate_* ด้านล่าง เป็นคนละเรื่องกับคอลัมน์นี้
    impact_month CHAR(7) NOT NULL,
    impact_year INTEGER NOT NULL,    -- แตกจาก impact_month เพื่อ filter รายปีโดยไม่ต้อง substring
    -- วงจรชีวิตของ "รอบชดเชย" — ✅ มติ 2026-09-12 (DECISIONS ข้อ 2.17)
    --   IMPORTED         Job 2  สร้างแถวแม่ตอนนำเข้าคู่ร้านจาก ALLMAP (สถานะเริ่มต้น)
    --   SALES_READY      Job 5  ได้ยอดขายจาก IAS/MIS และคำนวณ growth_rate_diff เสร็จแล้ว
    --   READY_DOCUMENT   Job 6  ตั้งรอบชดเชยของงวดเรียบร้อย พร้อมให้ Job 8 สร้างเอกสาร
    --   DOCUMENT_CREATED Job 8  สร้าง sgi_compensation_documents สำเร็จ
    --   CLOSED           Job 6  ปิดรอบ (flag_action Y -> N)
    -- ⚠️ Job 4 ไม่เลื่อนสถานะนี้ — การขอยอดขายติดตามที่ sgi_fgi_impact_stores.sales_request_status
    -- ⚠️ Job 8b ไม่เลื่อนสถานะนี้ — ผลการเปิด workflow อยู่ที่ workflow_generation_status
    -- ⚠️ ถ้ารอบเดียวเข้าเงื่อนไขทั้ง READY_DOCUMENT และ CLOSED ในการรันครั้งเดียว **CLOSED ชนะ** (terminal)
    -- ⚠️ แถวที่คู่ร้านถูกตัดทิ้ง (verify_status = 'N') หรือค้าง 'W' จะ **คงเป็น IMPORTED ตลอดไป**
    --    IMPORTED จึงแปลว่า "ยังไม่มีอะไรเกิดขึ้น" ไม่ใช่ "กำลังดำเนินการ"
    process_status VARCHAR(30) NOT NULL DEFAULT 'IMPORTED'
        CHECK (process_status IN ('IMPORTED','SALES_READY','READY_DOCUMENT','DOCUMENT_CREATED','CLOSED')),
    action_status VARCHAR(30),
    last_compensation_amount NUMERIC(14,2),
    workflow_generation_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (workflow_generation_status IN ('W','Y','N')),
    -- ⬇ รับเข้าโครงตามมติ 2026-08-21 (gap F8) — ขนจาก ORA FGI_IMPACT_STORE_ON_PROCESS
    --   ใช้ตัดสิน "ประเภทเคส" ที่จุดเข้า flow และ auto-assign เจ้าของงานคนเดิม
    last_compensate_seq INTEGER NOT NULL DEFAULT 1,        -- รอบชดเชย (ขึ้นใหม่เมื่อเปิดเรื่องใหม่)
    last_compensate_seq_no INTEGER NOT NULL DEFAULT 1,     -- ครั้งที่ในรอบ · > 1 = เคสต่อเนื่อง
    start_compensate_month CHAR(7), start_compensate_year INTEGER,   -- กรอบงวดที่ชดเชยได้ (เริ่ม)
    end_compensate_month CHAR(7),   end_compensate_year INTEGER,     -- กรอบงวดที่ชดเชยได้ (จบ)
    -- ORA FGI_IMPACT_STORE_ON_PROCESS.FLAG_ACTION — โดเมนจริง Y/W/N (active = IN ('Y','W'))
    --   N = ยังไม่มีรอบชดเชย / ปิดรอบแล้ว · Y = รอบ active · W = พัก รอจ่าย
    -- ✅ มติ 2026-09-13 (DECISIONS ข้อ 2.38): **Job 2 ใส่ 'N' ชัดเจน ห้ามพึ่ง DEFAULT 'Y'**
    --    เพราะตอนนำเข้ายังไม่มีรอบชดเชย · **Job 6 เป็นผู้เปลี่ยน 'N' -> 'Y'** เมื่อรอบเริ่มจริง
    --    แล้ว 'Y' -> 'W' (พัก) / 'Y' -> 'N' (ปิดรอบ) ตามเดิม
    --    🔴 ถ้าปล่อยเป็น 'Y' ตั้งแต่นำเข้า คิวรี "คู่ที่มีอยู่แล้ว" ของ Job 2 (นับ flag_action IN ('Y','W')
    --       เป็นรอบ active) จะกันคู่ร้านใหม่ออกเงียบ ๆ ไม่มี error ไม่มี log
    --    ⚠️ DEFAULT ยังเป็น 'Y' เพื่อไม่ให้กระทบ job อื่นที่พึ่งค่านี้ — ผู้เขียนแถวต้องระบุเอง
    -- CHECK เดิมที่รับแค่ ('Y','N') จะทำ migration ล้มทันทีที่เจอแถว 'W'
    flag_action CHAR(1) NOT NULL DEFAULT 'Y' CHECK (flag_action IN ('Y','W','N')),
    -- ช่องทางต้นทางของเคส (SDD GI สไลด์ 17 · 3 แหล่ง) — ORA FGI_IMPACT_STORE_ON_PROCESS.DATASOURCE
    --   ALM = ระบบดึงจาก ALLMAP (Job 2/3)   · STA = ระบบดึงจาก Franchise Statement (Job 5)   [ทั้งคู่มีในระบบเดิม]
    --   PRO = เชิงรุก  — OPT ประชุมพิจารณาแล้วเปิดเรื่อง (ต้นทางเอกสารอยู่ที่ All Memo)      [ใหม่ 2026-08-24]
    --   REA = เชิงรับ  — หน่วยงานอื่นแจ้งเข้ามาว่าร้านถูกกระทบ                                [ใหม่ 2026-08-24]
    -- ผลต่อ flow (SDD สไลด์ 47 · 49): ALM/STA = งานเข้ามาให้ จนท. SBP DSA เลือก · PRO/REA = เจ้าของงานต้องคีย์เอง
    -- ไม่ใส่ CHECK constraint เพื่อกันค่าใหม่ในอนาคต
    -- ✅ ตรวจฐานเดิมจริงแล้ว 2026-09-12: DATASOURCE มีแค่ **ALM (4,670) · STA (2,877)** เท่านั้น
    --    ไม่มี HRS เลยทั้งตาราง live และ FGI_IMPACT_STORE_ON_PROCESS_BK_20250515
    --    (ข้อความเดิมที่ว่า "ระบบเดิมมี HRS ปนอยู่" พิสูจน์แล้วว่าไม่จริง)
    datasource VARCHAR(5),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- ชื่อ job/ผู้ใช้ที่แตะแถวล่าสุด (JOB2 · JOB6 · x-user-id) — เพิ่ม 2026-09-02 ตาม SQL ที่ Job 6 เขียนจริง
    updated_by VARCHAR(30),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_process UNIQUE (impacted_store_code, impact_month)
);

-- รับเข้าโครงตามมติ 2026-08-21 (gap F1) — ขนจาก ORA FGI_IMPACT_STORE_COMPENSATE
-- ยอดชดเชย "รายงวด" ที่เกิดก่อนมีเอกสาร · จำเป็นเพื่อนับ "ยอด 0 ติดกันกี่เดือน" (กติกาเดือน 1-3 / เดือนที่ 4)
CREATE TABLE sgi_fgi_impact_compensations (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES sgi_impacted_stores(store_code),
    compensate_seq INTEGER NOT NULL,        -- รอบ (คู่กับ sgi_fgi_impact_processes.last_compensate_seq)
    compensate_seq_no INTEGER NOT NULL,     -- ครั้งที่ในรอบ
    compensate_month CHAR(7) NOT NULL,      -- งวดที่ชดเชย 'YYYY-MM' (ค.ศ.)
    compensate_year INTEGER NOT NULL,
    forecast_amount NUMERIC(14,2),          -- ระบบคำนวณ
    adjust_amount NUMERIC(14,2),            -- คนปรับ · ยอดที่ใช้จริง = COALESCE(adjust_amount, forecast_amount)
    -- โดเมนครบ 6 ค่า (สืบจาก FgiConstant + ExportJdbc · ปิด DP-14 เมื่อ 2026-09-02):
    --   I = ข้อมูลตั้งต้นของงวด · A = อนุมัติชดเชย · N = เห็นควรไม่ชดเชย · S = หยุดชดเชย · Z = ยอดเป็นศูนย์
    --   C = ร้านปิดแล้ว (mas_store.close_date <= งวด) หรือสัญญา SBP ถูกยกเลิกด้วย cancel_type IN ('01','02','03','04','08')
    --       ก่อน/ในงวดนั้น — ระบบเดิมตั้งค่านี้แทน 'I' ตั้งแต่ตอน insert (ExportJdbc บรรทัด 404/414/452)
    --   ส่ง STA: I/A/N ส่งตรง · S ส่งตรง · **C และ Z แปลงเป็น S เฉพาะใน payload** (ใน DB คงค่าเดิม)
    --   R (Reflow) เป็นค่าของ message เท่านั้น ไม่เคยลง DB — สร้างที่ POST /sgi/document/{docNo}/actions
    compensate_status VARCHAR(5) CHECK (compensate_status IN ('I','C','A','N','S','Z')),
    compensate_comment VARCHAR(4000),
    stmt_month INTEGER, stmt_year INTEGER,  -- งวด statement
    approve_date DATE,
    created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_compensation UNIQUE (impact_process_id, compensate_month)
);

CREATE TABLE sgi_fgi_impact_stores (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES sgi_impacted_stores(store_code),
    new_store_code VARCHAR(5) NOT NULL,   -- ร้านเปิดใหม่ · master ของระบบเดิม
    impact_month CHAR(7) NOT NULL, distance_km NUMERIC(8,3),
    -- ⬇ ปิดช่องว่าง G1/G2 (2026-09-02) — legacy มี "สองสถานะคนละเรื่อง" ที่โครงเดิมยุบเหลือคอลัมน์เดียว
    --   ORA FGI_IMPACT_STORE.FLAG_VERIFY = ผลตรวจ "คู่ร้านนี้เข้าเกณฑ์ชดเชยไหม" (Job 2 · กฎ DENY/ON_PROCESS)
    --   W = รอตรวจ (ค่าตั้งต้นตอน insert) · P = เข้ากระบวนการ · N = ถูกตัดทิ้ง (เก็บแถวไว้ ไม่ลบ)
    -- ⚠️ โดเมนจริงของ FLAG_VERIFY เดิมมี **4 ค่า** (ตรวจ 2026-09-12 · FGI_IMPACT_STORE_BK_20250515 26,264 แถว):
    --    N 14,424 · Y 8,556 · W 3,064 · P 220 — ค่า **Y ไม่มีใน CHECK นี้โดยตั้งใจ**
    --    เพราะ Y ของเดิม = "ยอดขายผ่านการตรวจแล้ว" ซึ่งโครงใหม่แยกไปที่ sales_request_status
    --    migration ต้องแมป: FLAG_VERIFY 'Y' -> verify_status 'P' + sales_request_status 'Y'
    --    (ถ้าแมปตรงตัวจะติด CHECK ทันที 8,556 แถว — ดู LLDD-BE-Data-Migration-Cutover)
    verify_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (verify_status IN ('W','P','N')),
    -- ORA FGI_IMPACT_STORE.CREATE_BY / UPDATE_BY — กฎ DENY/ON_PROCESS ของ Job 2 ใช้เป็นเงื่อนไขหลัก
    --   ALM = ALLMAP (ตรวจตามเกณฑ์) · STA = ระบบ Statement ส่งเข้ามาเอง (ผ่านทันที) · USER = คนคีย์เอง
    created_by VARCHAR(10) NOT NULL DEFAULT 'ALM' CHECK (created_by IN ('ALM','STA','USER')),
    updated_by VARCHAR(10) CHECK (updated_by IN ('ALM','STA','USER')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,   -- กฎ "ตัดทิ้งเมื่อเก่ากว่า 12 เดือน" อ้างคอลัมน์นี้
    -- สถานะ **การขอ** ยอดขายจาก IAS/MIS ระดับคู่ร้าน (คนละเรื่องกับ verify_status)
    --   W = ยังไม่ได้ขอ (ค่าตั้งต้น · Job 2 ไม่แตะคอลัมน์นี้เลย) · P = ขอแล้วรอผล (Job 4)
    --   Y = ได้ข้อมูลกลับมาแล้ว · E = ขอแล้วได้ข้อมูลไม่ได้ / คำนวณไม่ได้
    -- ⚠️ ติดตาม "การขอ" ไม่ใช่ "ผลทางธุรกิจ" จึง **ไม่มี 'N'** โดยตั้งใจ —
    --    ผลว่ายอดตกหรือไม่ตกอยู่ที่ sgi_fgi_impact_sales_summaries.sales_status (W/P/Y/N/E)
    --    และคอลัมน์นี้ **ไม่มีต้นทางในระบบเดิม** (เป็นของใหม่) จึงไม่มีข้อจำกัดจาก migration
    sales_request_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_request_status IN ('W','P','Y','E')),
    forecast_compensate_percent NUMERIC(7,4), adjust_compensate_percent NUMERIC(7,4),
    forecast_compensation_amount NUMERIC(14,2), adjust_compensation_amount NUMERIC(14,2),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_store_pair UNIQUE (impacted_store_code, new_store_code, impact_month)
);

-- ⬇ เพิ่ม 2026-09-13 (มติผู้ใช้) — ค่าชดเชย **ฝั่งร้านเปิดใหม่ (N) รายงวด**
--   ORA `FGI_NEW_STORE_COMPENSATE` (23,628 แถวจริง) · คู่กับ `sgi_fgi_impact_compensations` ที่เป็นฝั่ง I
--
--   🔴 ทำไมใส่ใน `sgi_fgi_impact_stores` ไม่ได้: ตารางนั้นเป็น **1 แถวต่อคู่ร้าน ไม่มีมิติงวด**
--      แต่ `ExportJdbc.insertFgiNewStoreCompensate` ใส่ `op.last_compensate_month/year` ทุกรอบ
--      → คู่ร้านเดิมได้แถวใหม่ **ทุกงวดที่ยังชดเชยต่อเนื่อง** · ข้อมูลจริงยืนยัน:
--        23,628 แถว N ต่อ 7,548 รอบ = 3.13 แถว/รอบ (ฝั่ง I 2.74) → มากกว่า 1 ร้านใหม่ต่องวด
--      ถ้าเขียนทับบนแถวคู่ร้าน งวด ก.ค. จะทับ มิ.ย. แล้วตรวจย้อนหลังไม่ได้ว่างวดไหนจ่ายเท่าไร
--
--   ⚠️ กติกาธุรกิจ "%ชดเชยของร้านใหม่ทุกแถวรวมกันต้องได้ 100%" ตรวจต่อ `impact_compensation_id`
--      (คือต่อ 1 งวด) — ไม่ใช่ต่อคู่ร้าน
CREATE TABLE sgi_fgi_new_store_compensations (
    id BIGSERIAL PRIMARY KEY,
    -- แถวแม่ = ค่าชดเชยฝั่ง I ของงวดนั้น · CASCADE เพราะลูกไม่มีความหมายถ้าไม่มีงวด
    impact_compensation_id BIGINT NOT NULL
        REFERENCES sgi_fgi_impact_compensations(id) ON DELETE CASCADE,
    -- ORA FGI_NEW_STORE_COMPENSATE.IMPACT_STORE_ID — ชี้กลับไปแถวคู่ร้าน (I↔N) ที่เป็นต้นเรื่อง
    impact_store_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_stores(id),
    new_store_code VARCHAR(5) NOT NULL,
    -- 🔴 แก้ 2026-09-15 — เดิมเป็น NUMERIC(5,2) ตาม ORA NUMBER(5,2) เป๊ะ
    --    แต่ Job 6 คัดค่ามาจาก `sgi_fgi_impact_stores.forecast_compensate_percent`
    --    ซึ่ง SGI ขยายเป็น NUMERIC(7,4) ไปแล้ว → PostgreSQL **ปัดเงียบ ๆ ไม่มี error**
    --    (33.3333 → 33.33 · 14.2857 → 14.29) พิสูจน์กับ PostgreSQL 16 จริงแล้ว
    --    ผลคือตารางสองตัวเก็บ "ปริมาณเดียวกัน" ไม่ตรงกัน กระทบยอด %ชดเชยรวม 100
    --    ปลายทางต้องกว้างอย่างน้อยเท่าต้นทางเสมอ · ค่าเดิมของ ORA (5,2) ใส่ (7,4) ได้ทั้งหมด
    forecast_amount NUMERIC(14,2), forecast_percent NUMERIC(7,4),
    adjust_amount NUMERIC(14,2), adjust_percent NUMERIC(7,4),
    created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_new_store_compensation UNIQUE (impact_compensation_id, new_store_code)
);

CREATE TABLE sgi_fgi_impact_sales_summaries (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    total_working_days INTEGER NOT NULL DEFAULT 0 CHECK (total_working_days >= 0),
    growth_rate_before NUMERIC(9,4), growth_rate_after NUMERIC(9,4), growth_rate_diff NUMERIC(9,4),
    -- ปลายทางจริงของ ORA FGI_IMPACT_STORE_SALES.FLAG_VERIFY (ดู Source-to-Target ข้อ 5.1)
    --   W = ยังไม่ได้ประเมิน · P = ขอยอดไปแล้ว รอข้อมูลจาก IAS/MIS
    --   Y = ประเมินแล้ว **ยอดตกจริง** เข้าเกณฑ์ชดเชย  (growth_rate_diff < 0 หรือ NULL)
    --   N = ประเมินแล้ว **ยอดไม่ตก** ไม่เข้าเกณฑ์ชดเชย (growth_rate_diff >= 0)
    --   E = ประเมินผิดพลาด (ของใหม่ ระบบเดิมไม่มี)
    -- ✅ มติ 2026-09-12 (DECISIONS ข้อ 2.37): **รับ 'N' ตามระบบเดิม ไม่แมป N -> E** และ **เพิ่ม 'P'**
    --    หลักฐานความหมายของ N: ImportJdbc.updateStatusImpactStoreSaleByDiff() บรรทัด 155-180
    --      FLAG_VERIFY = CASE WHEN NVL(GROWTH_RATE_DIFF, -1) < 0 THEN 'Y' ELSE 'N' END
    --    ข้อมูลจริง (FGI_IMPACT_STORE_SALES_BK_20250515 · 8,730 แถว): Y 6,029 · N 2,549 · P 151 · W 1
    --      แถว 'N' มี growth_rate_diff 0..90.61 และ **ไม่มี NULL เลย** = ประเมินสำเร็จ ไม่ใช่ error
    --      แถว 'P' 151 แถว = ขอแล้วยังไม่ได้ผล — เดิมโดเมนไม่มี 'P' ทำให้ migration ล้ม
    sales_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_status IN ('W','P','Y','N','E')),
    -- ชื่อ job/ผู้ใช้ที่แตะแถวล่าสุด (JOB4 · JOB5) — เพิ่ม 2026-09-02 ตาม SQL ที่ Job 4/5 เขียนจริง
    updated_by VARCHAR(30),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_summary_process UNIQUE (impact_process_id)
);

CREATE TABLE sgi_sales_transactions (
    id BIGSERIAL PRIMARY KEY,
    sales_summary_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_sales_summaries(id) ON DELETE CASCADE,
    txn_date DATE NOT NULL, window_no SMALLINT NOT NULL CHECK (window_no BETWEEN 1 AND 4),
    -- ⬇ เพิ่ม 2026-09-13 — ตำแหน่งวันในหน้าต่าง 1..15 (คอลัมน์ SEQ ของ FGI_IMPACT_STORE_SALES_TRN เดิม)
    --   จำเป็น **ต่อความถูกต้องของเงิน** ไม่ใช่ของประดับ: สูตร AVG ของระบบเดิมจับคู่
    --   "วันเดียวกันของปีก่อน ↔ ปีนี้" เพื่อตัดสินว่าจะนับยอดวันนั้นหรือแทนด้วย 0
    --   ตารางเดิมเป็นตารางกว้าง (1 แถว = 1 SEQ มี 4 ชุดยอดขาย) จึงจับคู่ได้ฟรีในแถวเดียว
    --   ตารางใหม่เป็นตารางแคบ (1 แถว = 1 วัน) ถ้าไม่มี seq จะ join คู่ปีไม่ได้เลย
    --   (คำนวณย้อนจาก txn_date + วันเปิดร้านก็ได้ แต่ต้องเขียนกฎ leap year ซ้ำใน SQL)
    seq SMALLINT NOT NULL CHECK (seq BETWEEN 1 AND 15),
    sales_amount NUMERIC(14,2) NOT NULL, sales_diff NUMERIC(14,2),
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE, source_checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_day_window UNIQUE (sales_summary_id, txn_date, window_no),
    -- คู่ (หน้าต่าง, ลำดับ) ต้องไม่ซ้ำ — กันแถวหลุดจากการรันซ้ำที่ txn_date เพี้ยน
    CONSTRAINT uq_sales_window_seq UNIQUE (sales_summary_id, window_no, seq)
);

-- ⬇ แก้ 2026-09-09 — เดิมใช้คอลัมน์เดียว `competitor_code` แล้ว FK ไป master แบรนด์
--   ซึ่งผิดระดับ: ALLMAP ส่ง **รหัสสาขาของคู่แข่ง** มา (`4832` · `789` · `TD58_08` · `LS3550`)
--   ไม่ใช่รหัสแบรนด์ `01`-`11` · พิสูจน์จากไฟล์จริง BPM06003O (1,312 แถว):
--   COMPET_ID ไม่ซ้ำ 222 ค่า แต่มีแค่ 7 แบรนด์ · ร้าน 07109 มีแฟมิลี่มาร์ท 80 สาขาใกล้ร้าน
--   ถ้าคง UNIQUE เดิมไว้จะ **เหลือแค่ 165 จาก 1,312 แถว (หายไป 87%)**
CREATE TABLE sgi_fgi_impact_competitors (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    -- รหัส "สาขา" ของคู่แข่งตามที่ ALLMAP ส่งมา — ไม่มี FK เพราะเป็นรหัสของระบบภายนอก
    -- nullable เพราะ ALLMAP ส่งค่าว่างมาได้จริง (56/1,312 แถวในไฟล์ตัวอย่าง) · job ต้องแปลง '' -> NULL
    competitor_store_code VARCHAR(50),
    -- รหัส "แบรนด์" — FK ไป master 11 รายการของหน้า k2-competitors.html
    -- nullable เพราะ map ไม่ได้ต้องยังเก็บแถวไว้ (ห้ามทิ้งข้อมูล) แล้วรายงานเป็น rejected/unmapped
    brand_code VARCHAR(30) REFERENCES sgi_competitors(competitor_code),
    name_th VARCHAR(200),        -- ชื่อแบรนด์ภาษาไทยตามที่ ALLMAP ส่งมา (snapshot)
    name_en VARCHAR(200),        -- ชื่อแบรนด์ภาษาอังกฤษ (ฟิลด์ 4 ของ BPM06003O)
    branch_th VARCHAR(200),      -- ชื่อสาขาของคู่แข่ง เช่น 'ตลาดศรีวานิช' (ฟิลด์ 5)
    zone_code VARCHAR(10), subzone_code VARCHAR(10),   -- ฟิลด์ 6-7 · ส่งต่อ K2 ในไฟล์ BPM06003O
    opened_date DATE, closed_date DATE,
    period_key CHAR(7) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- คีย์เป็น "สาขา" ไม่ใช่ "แบรนด์" — ALLMAP ส่ง `COMPET_ID` ว่างมาได้
    -- ⚠️ **ห้ามพึ่งพฤติกรรม NULL ของ UNIQUE** (ทั้ง NULLS DISTINCT และ NOT DISTINCT ผิดทั้งคู่
    --    ดูเหตุผลด้านล่าง) — คีย์จริงคือคอลัมน์ generated `competitor_key` ที่ไม่เป็น NULL เลย
    -- ⬇ business key ที่ทนทั้งสองกรณี — แก้ 2026-09-14
    --   `competitor_store_code` เป็น NULL ได้ (ORA `COMPET_ID VARCHAR2(50)` ไม่มี NOT NULL)
    --
    --   🔴 ทางเลือกสองทางแรกผิดทั้งคู่:
    --     NULLS DISTINCT (ค่าปริยาย) → แถวไร้รหัส **พอกขึ้นทุกรอบ** เพราะ upsert ไม่เคยชน
    --     NULLS NOT DISTINCT        → ร้านคู่แข่ง**หลายสาขา**ที่ไม่มีรหัสถูกยุบเหลือแถวเดียว
    --                                 = **ข้อมูลหาย** (ร้าน 07109 มีแฟมิลี่มาร์ท 80 สาขา)
    --
    --   ✅ ใช้คอลัมน์ generated ที่ fallback เป็น **ชื่อสาขา** เมื่อไม่มีรหัส
    --      จึงแยกสาขาออกจากกันได้จริง และยัง upsert ทับตัวเองได้เมื่อรันซ้ำ
    --   ⚠️ แก้ 2026-09-14 — fallback แบบ 'name:<ชื่อสาขา>' อย่างเดียว **ยังยุบผิด** 2 เคส:
    --     1. สาขาคนละแบรนด์/คนละโซนที่ชื่อเหมือนกัน → ถูกยุบเป็นแถวเดียว
    --     2. ทั้งรหัสและชื่อว่าง → ทุกแถวได้คีย์ 'name:' เหมือนกันหมด
    --   จึงรวม brand/zone/subzone เข้าไปด้วย และ **แถวที่ไม่มีทั้งรหัสและชื่อถูกปฏิเสธที่ Job 3**
    --   (ระบุตัวตนไม่ได้เลย เก็บไว้ก็ไม่มีใครใช้ได้ · คีย์จึงไม่มีทางเป็น NULL)
    competitor_key VARCHAR(300) GENERATED ALWAYS AS (
        COALESCE(
            NULLIF(btrim(competitor_store_code), ''),
            'name:' || lower(btrim(COALESCE(brand_code, '') || '|' ||
                                   COALESCE(zone_code, '') || '|' ||
                                   COALESCE(subzone_code, '') || '|' ||
                                   -- 🔴 NULLIF กันช่องว่าง: ALLMAP ส่ง '' (ไม่ใช่ NULL) ได้
                                   --    COALESCE เปล่า ๆ จะไม่ตกไป name_th แล้วคู่แข่งคนละร้าน
                                   --    ได้คีย์เดียวกัน → ชน UNIQUE แล้วหายไปหนึ่งแถว
                                   COALESCE(NULLIF(btrim(branch_th), ''), name_th, '')))
        )
    ) STORED,
    CONSTRAINT uq_impact_competitor UNIQUE (impact_process_id, competitor_key, period_key)
);

-- ⚠️ fcs_qssi_score — ห้าม CREATE TABLE ใหม่ (ตรวจฐานจริง 2026-08-07)
--   ตารางนี้มีอยู่แล้วใน schema `sps_store` ชื่อ **เอกพจน์** `fcs_qssi_score`
--   มีข้อมูลจริง 24,284,545 แถว และมี import pipeline ทำงานอยู่
--   (`POST /performance/import-qssi` · staging `fcs_tmp_qssi_score` · `performance.service.ts`)
--   โครงคอลัมน์อ้างอิงด้านล่างเป็น target shape ที่ SGI ต้องการ — ต้องเทียบกับคอลัมน์จริงก่อน
--   ✅ DP-4 ปิดแล้ว 2026-08-24: อ่านอย่างเดียว ไม่แก้ constraint/index ของตารางเดิม
--   ห้ามใช้ชื่อพหูพจน์ `fcs_qssi_scores` ทุกกรณี
-- target shape (reference only — ห้ามรันเป็น DDL):
--   id BIGSERIAL PK · store_code VARCHAR(5) · category_code VARCHAR(30) · score_period CHAR(7)
--   · score_value NUMERIC(10,4) · source_file_name · source_checksum · updated_at
--   · UNIQUE (store_code, category_code, score_period)

CREATE TABLE sgi_interface_transactions (
    id BIGSERIAL PRIMARY KEY,
    -- run_id เป็น correlation id ของรอบรัน (มาจาก application log) — ไม่มี FK เพราะ job_run_histories ถูกตัด 2026-08-06
    run_id VARCHAR(50),
    -- direction: OUT = ส่งออกไประบบภายนอก (Job 4 → IAS · Job 6 → STA) · IN = รับเข้าจากภายนอก (Job 5 ไฟล์จาก IAS · Job 11 ข้อความจาก STA)
    --            ⚠️ ไม่มี "ACK กลับ" จาก STA แล้ว (มติ 2026-09-08 ข้อ 2.13) — ความสำเร็จของขาออกวัดที่ outbox_status = CONFIRMED
    --            INTERNAL = การส่งต่อ*ภายในระบบเดียวกัน* ที่มาแทนไฟล์ EAI เดิม (Jobs 7/8/9 เขียน DB ตรง — ไม่มี ACK ให้รอ จึงจบที่ status = COMPLETED)
    -- ชุดค่าปิด 12 ค่า เขียนโดย batch เท่านั้น (ไม่ใช่ input ของผู้ใช้) — ต้องล็อกเพราะ data_name เป็นส่วนหนึ่งของ
    -- UNIQUE ที่กันส่งซ้ำ และเป็นตัวกรองของ watchdog Job 10 · พิมพ์ผิดหนึ่งตัว = กันซ้ำไม่ทำงาน + watchdog เงียบ
    -- เพิ่ม interface ใหม่ = ALTER CONSTRAINT + อัปเดตตารางใน database.md พร้อมกัน
    data_name VARCHAR(80) NOT NULL CHECK (data_name IN (
        'IAS_SALES_REQUEST',                                    -- Job 4 -> IAS/MIS (OUT)
        'IMPACT_STORE_SALES',                                   -- Job 5 <- IAS/MIS (IN)
        'COMPENSATE_INIT_I','COMPENSATE_INIT_N',                -- Job 6 -> STA (OUT)
        'COMPENSATE_APPROVE_I','COMPENSATE_APPROVE_N',          -- Job 6 -> STA (OUT)
        'IMPACT_COMPETITOR','IMPACT_STORE','NEW_STORE',         -- Jobs 7/8/9 เขียน DB ตรง (INTERNAL)
        -- ⬇ เพิ่ม 2026-09-02 หลังไล่ค่าที่เอกสารใช้จริงเทียบกับ CHECK นี้ (พบว่า 3 ค่าถูก INSERT แต่ CHECK ไม่รับ)
        'DOCUMENT_CREATE',                                      -- Job 8 บันทึกการสร้างเอกสาร (INTERNAL) — ใช้อยู่แล้วแต่ตกหล่นจาก CHECK
        'STA_UPDATE_COMPENSATE',                                -- Job 11 <- STA แจ้งยอดชดเชย (IN · message sta_update_compensate)
        'SGI_REFLOW'                                            -- POST /sgi/document/{docNo}/actions -> STA (OUT · message sgi_reflow)
    )),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('IN','OUT','INTERNAL')),
    -- status = lifecycle ของ "แถว" · outbox_status (ข้างล่าง) = สถานะการ publish ของฝั่งขาออก
    -- ⚠️ ตัดค่า 'ACKED' ออกเมื่อ 2026-09-08 (มติข้อ 2.13) — ไม่มี ACK ระดับธุรกิจจาก STA ให้รออีกแล้ว
    --    ขาออกจบที่ COMPLETED เมื่อ outbox_status = 'CONFIRMED' (ได้ publisher confirm จาก broker)
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','SENT','COMPLETED','FAILED','FAILED_RETRY')),
    impact_process_id BIGINT REFERENCES sgi_fgi_impact_processes(id),
    sales_summary_id BIGINT REFERENCES sgi_fgi_impact_sales_summaries(id),
    doc_no VARCHAR(10), business_key VARCHAR(200) NOT NULL, period_key VARCHAR(20) NOT NULL,
    correlation_id VARCHAR(100), file_name VARCHAR(255), file_checksum VARCHAR(64),
    -- outbox_status — โดเมนชัดเจนตั้งแต่ 2026-09-08 (มติข้อ 2.13)
    --   READY      = เขียนลง outbox แล้ว รอ publish
    --   PUBLISHED  = ยิงเข้า broker แล้วแต่ **ยังไม่ได้ publisher confirm**
    --   CONFIRMED  = broker ยืนยันรับแล้ว = ถือว่าส่งสำเร็จ (Job 10 เลิกเฝ้าแถวนี้)
    --   FAILED     = publish ไม่สำเร็จ / ถูก broker ปฏิเสธ
    -- ⚠️ ไม่มีสถานะ "ACKED" ทั้งที่นี่และที่ status — สเปก STA ไม่มี ACK กลับมา (เส้น POST /sgi/interface/sta/ack ถูกตัด)
    outbox_status VARCHAR(20) CHECK (outbox_status IN ('READY','PUBLISHED','CONFIRMED','FAILED')),
    return_code VARCHAR(50), return_message VARCHAR(500),
    -- 🔴 payload — **ข้อความที่ส่งออกไปจริง** (เพิ่ม 2026-09-14)
    --    transactional outbox ที่ไม่เก็บ payload ไม่ใช่ outbox จริง: ตอนส่งซ้ำต้อง "ประกอบใหม่"
    --    จากข้อมูลในฐานซึ่ง**อาจเปลี่ยนไปแล้ว** → ปลายทางได้ข้อความคนละฉบับกับที่เคยตกลงไว้
    --    โดยไม่มีใครรู้ · เก็บไว้จึงส่งซ้ำได้ตรงตัวและใช้เทียบตอนสอบสวนย้อนหลังได้ด้วย
    --    ⚠️ เก็บเฉพาะขาออก (`direction = 'OUT'`) — ขาเข้าเก็บไฟล์/checksum แทน
    payload JSONB,
    -- เวอร์ชันของรูปแบบ payload — ขึ้นเมื่อ contract กับปลายทางเปลี่ยน ไม่ใช่เมื่อข้อมูลเปลี่ยน
    payload_version SMALLINT NOT NULL DEFAULT 1,
    retry_count INTEGER NOT NULL DEFAULT 0, sent_at TIMESTAMP, acked_at TIMESTAMP,
    -- marker กัน watchdog (Job 10) ส่งอีเมลเตือนซ้ำในวันเดียวกัน — ย้ายมาจาก audit_logs ที่ยกเลิก 2026-08-07
    last_ack_notified_on DATE,
    purge_after TIMESTAMP, legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP,
    CONSTRAINT uq_interface_business UNIQUE (data_name, direction, business_key, period_key),
    CONSTRAINT ck_interface_typed_reference CHECK (num_nonnulls(impact_process_id, sales_summary_id, doc_no) >= 1)
);"""),
        ("5.3 Zone B — Document and Internal Workflow", """-- ✅ มติ DP-1 (2026-08-10): PK เป็น surrogate `id` · `doc_no` เป็น UNIQUE ไม่ใช่ PK
-- ⚠️ ผลที่ตามมา: มี 8 ตาราง FK ไป doc_no แต่ **แบ่งเป็น 2 กลุ่ม ไม่เหมือนกัน**
--    [NOT NULL 6 ตัว] sgi_document_new_stores · sgi_document_competitors · sgi_document_external_factors ·
--                     sgi_consideration_logs · sgi_document_attachments · sgi_document_cost_details
--                     → แปลว่า "ต้องออก doc_no ให้เสร็จก่อนจึงบันทึกส่วนย่อยได้"
--    [nullable 2 ตัว] sgi_compensation_histories.ref_doc_no · sgi_interface_transactions.doc_no
--                     → 2 ตัวนี้บันทึกได้ก่อนมี doc_no (interface ผูกด้วย typed FK ตัวอื่นแทนได้ ดู ck_interface_typed_reference)
--    ⚠️ อย่าเขียนรวบว่า "ลูกทั้ง 8 เป็น NOT NULL" — เคยเขียนผิดแบบนั้นและขัดกับ database.md ที่นับ 6 (แก้ 2026-09-08)
--    จึงต้องออกเลขเอกสารใน INSERT เดียวกับที่สร้างแถวเสมอ (Job 8 ทำแบบนี้อยู่แล้ว)
--    referenceId ที่ส่งให้ @srm/glb-workflow = id (ตรงกับที่ระบบเดิมทำจริงใน cooperation-request/inform-evaluate)
--    doc_no อาจยังว่างตอนสร้างแถว แล้วออกเลขทีหลัง จึงเป็น NULL ได้
CREATE TABLE sgi_compensation_documents (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) UNIQUE,          -- YYYY/xxxxx (ปี ค.ศ.) · ออกจาก sgi_document_running_numbers
    year INTEGER, running_no INTEGER,   -- แตกจาก doc_no เพื่อ index/ค้นหา (NULL จนกว่าจะออกเลข)
    -- ⬇ แก้ 2026-09-13 (มติผู้ใช้) — **ตัด UNIQUE ออก** · เดิมล็อกไว้ 1 เอกสารต่อ 1 รอบ
    --   ซึ่งขัดกับข้อมูลจริง: ORA `FGI_IMPACT_STORE_INFO` (= เอกสาร) 20,676 แถว ต่อรอบชดเชย
    --   7,548 รอบ = **2.74 เอกสารต่อรอบ** · และเทียบกับค่าชดเชยรายงวด 20,674 แถว = **1.0001**
    --   ตารางเดิมมี COMPENSATE_MONTH/YEAR ชัดเจน → **เอกสาร 1 ใบ = 1 งวดชดเชย ไม่ใช่ 1 รอบ**
    --   ถ้าคง UNIQUE ไว้ เอกสารของเดือนที่ 2 จะ insert ไม่ได้เลย (รอบชดเชยกินหลายเดือน)
    --   คงคอลัมน์ไว้เพื่อค้นหา/รายงานระดับรอบ แต่ **ตัวตนของเอกสารอยู่ที่ impact_compensation_id**
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    -- แถวค่าชดเชยของงวดนั้น = ตัวตนจริงของเอกสาร (1:1) · ORA `IMPACT_STORE_INFO_ID` คู่กับ
    --   (IMPACT_PROCESS_ID, COMPENSATE_MONTH, COMPENSATE_YEAR) ของระบบเดิม
    impact_compensation_id BIGINT NOT NULL UNIQUE
        REFERENCES sgi_fgi_impact_compensations(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES sgi_impacted_stores(store_code),
    impact_month CHAR(7), new_store_code VARCHAR(5),   -- master ของระบบเดิม
    round_no INTEGER, loop_no INTEGER,  -- CompMainLoopNo / CompLoopNo — หน้าจอแสดง "รอบ 1 · ครั้งที่ 3"
    source VARCHAR(20) NOT NULL DEFAULT 'FS' CHECK (source IN ('FS','MANUAL')),
    -- สถานะเอกสารที่ผู้ใช้เห็น — ✅ มติ 2026-09-13 (DECISIONS ข้อ 2.31)
    --   06 = รอฝ่าย SBP DSA ดำเนินการ             (สถานะแรกหลังสร้างเอกสาร)
    --   08 = รอเจ้าหน้าที่ SBP DSA ดำเนินการ
    --   01 = รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ
    --   02 = รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ
    --   03 = รอผู้บริหารสำนักบริหาร SBP ดำเนินการ (AVP)
    --   99 = เสร็จสิ้นดำเนินการ (terminal)
    -- ใครตั้ง: **Job 8** ใส่ '06' ตอนสร้างเอกสาร (workflow_status_document.md บรรทัดแรก
    --   "สร้างเอกสาร -> รอฝ่าย SBP DSA ดำเนินการ") · หลังจากนั้น
    --   **POST /sgi/document/{docNo}/actions เป็นผู้เขียนที่เดียวในระบบ** (เขียนคอลัมน์นี้
    --   พร้อมกับ current_section_code เสมอ) · Job 8b ไม่แตะคอลัมน์นี้ — ผลการเปิด workflow อยู่ที่
    --   sgi_fgi_impact_processes.workflow_generation_status
    -- 🔴 **รหัสชุดนี้เป็นของ SGI เอง ไม่ใช่ของ engine** — sps_store.workflow_status มีแค่
    --    status_id (integer surrogate ที่ engine ออกให้ตอน setup จึงไม่เท่ากันข้าม dev/uat/prod)
    --    และ status_name (ชื่อไทย) **ไม่มีคอลัมน์รหัส 2 ตัวอักษรเลย** คำอธิบายเดิมจึงคลาดเคลื่อน
    --    แหล่ง lookup ที่ใช้ได้จริงคือ common_code (code_type = 'SGI_DOC_STATUS') แบบเดียวกับ SGI_DECISION
    -- ⚠️ ค่าเดียวกับ current_section_code สำหรับสถานะ "รอ..." ทั้ง 5 ตัว ต่างกันแค่ 99 ที่ไม่มี section
    status_code VARCHAR(2) NOT NULL DEFAULT '06'
        CHECK (status_code IN ('01','02','03','06','08','99')),
    current_section_code VARCHAR(2),   -- ค่าจาก sps_store.workflow_state ของ engine
    total_compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    allmap_url VARCHAR(500),                   -- CompUrlMap — ปุ่ม Link To ALLMAP
    statement_id VARCHAR(500),                 -- CompStatementID — โยงกลับ SBP Statement ต้นทาง
    --   🔴 ขยายจาก VARCHAR(50) เป็น 500 เมื่อ 2026-09-17 — ของเดิม**เก็บ URL เต็ม** ไม่ใช่รหัส
    --   วัดจากข้อมูลจริง 18,007 เอกสาร: ยาวสุด 97 ตัวอักษร · **18,006 แถวเกิน 50**
    --   (`https://franchisemall.cpall.co.th/franchise/frFMLWeb/…`) · ขนาดเดียวกับ allmap_url
    statement_date DATE,                       -- Period Statement (ค.ศ.) — ตัวกรอง/คอลัมน์ของรายงาน SDD สไลด์ 60
    account_year INTEGER,                      -- งวดบัญชี
    -- CHECK เพิ่ม 2026-09-17 — ต้นทาง K2 เก็บเป็นข้อความ '01'–'12' (+ ว่าง 6,484 แถว)
    --   ถ้าแปลงพลาดเป็น 0 หรือ 13 จะหลุดเข้าฐานเงียบ ๆ แล้วรายงานงวดบัญชีเพี้ยน
    account_month INTEGER CHECK (account_month BETWEEN 1 AND 12),
    approver_snapshot JSONB,                   -- FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร
    version_no INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(30) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(30), updated_at TIMESTAMP,
    CONSTRAINT uq_comp_year_running UNIQUE (year, running_no),
    CONSTRAINT uq_comp_business UNIQUE (source, impacted_store_code, impact_month, new_store_code, round_no)
);

ALTER TABLE sgi_interface_transactions
    ADD CONSTRAINT fk_interface_doc_no FOREIGN KEY (doc_no) REFERENCES sgi_compensation_documents(doc_no);

-- ══ นโยบาย ON DELETE ของลูก sgi_compensation_documents (ระบุชัด 2026-09-02) ══
--   CASCADE = แถวรายละเอียดที่มีความหมายเฉพาะกับเอกสารใบนั้น ลบเอกสารแล้วต้องหายตาม
--     sgi_document_new_stores · sgi_document_competitors · sgi_document_external_factors · sgi_document_cost_details
--   ไม่ CASCADE (NO ACTION) = หลักฐาน/ประวัติ ที่ต้องอยู่ต่อแม้เอกสารถูกลบ — **ห้ามเติม CASCADE ให้กลุ่มนี้**
--     sgi_consideration_logs (ผลพิจารณา) · sgi_document_attachments (ไฟล์แนบ · ใช้ soft delete)
--     sgi_compensation_histories (ยอดที่ส่ง STA ไปแล้ว) · sgi_interface_transactions.doc_no (หลักฐานรับ-ส่ง interface)
--   หมายเหตุ: ตามมติ "ไม่มีการเปิด SR เพื่อลบข้อมูล" (ข้อค้าง N1) เอกสารไม่ถูกลบจริงอยู่แล้ว
--   นโยบายนี้จึงเป็นแนวกันพลาด ไม่ใช่ flow ปกติ
CREATE TABLE sgi_document_new_stores (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL,   -- ร้านเปิดใหม่ · master ของระบบเดิม
    distance_km NUMERIC(8,3), compensate_percent NUMERIC(7,4) NOT NULL CHECK (compensate_percent BETWEEN 0 AND 100),
    compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    source_system VARCHAR(30) NOT NULL,
    -- ⬇ เพิ่ม 2026-09-13 — แถวต้นทางใน sgi_fgi_new_store_compensations ที่ Job 9 คัดลอกมา
    --   เหตุผลเดียวกับ sgi_document_competitors.source_row_id: **%ชดเชยผิด = จ่ายเงินผิด**
    --   ต้องตามรอยกลับไปได้ว่าตัวเลขบนเอกสารมาจากแถวไหนของงวดไหน
    --   NULL = แถวที่ผู้ใช้เพิ่มเอง (source_system = 'USER') ซึ่งไม่มีต้นทาง
    source_row_id BIGINT REFERENCES sgi_fgi_new_store_compensations(id) ON DELETE SET NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_new_store UNIQUE (doc_no, new_store_code)
);

-- ⬇ แก้ 2026-09-09 พร้อมกับ sgi_fgi_impact_competitors — Job 7 คัดลอกมาจากตารางนั้นตรง ๆ
--   ถ้าปลายทางยังคีย์ด้วยแบรนด์ ข้อมูลจะหายตอนคัดลอก (เอกสารใบเดียวเก็บได้แค่ 1 สาขาต่อแบรนด์)
CREATE TABLE sgi_document_competitors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    competitor_store_code VARCHAR(50),                                  -- รหัสสาขาจาก ALLMAP (ไม่มี FK)
    brand_code VARCHAR(30) REFERENCES sgi_competitors(competitor_code), -- รหัสแบรนด์ master 01-11
    name_th VARCHAR(200), name_en VARCHAR(200), branch_th VARCHAR(200),
    zone_code VARCHAR(10), subzone_code VARCHAR(10),
    opened_date DATE, closed_date DATE, impact_date DATE,
    detail TEXT, remark TEXT, source_system VARCHAR(30) NOT NULL,
    -- ⬇ เพิ่ม 2026-09-13 — แถวต้นทางใน sgi_fgi_impact_competitors ที่ Job 7 คัดลอกมา
    --   ระบบเดิมส่ง PK ของแถวต้นทางเป็นฟิลด์ที่ 1 ของไฟล์ BPM06003O แล้วใช้กันส่งซ้ำ
    --   ของใหม่กันซ้ำด้วย uq_doc_competitor แล้ว แต่ยัง **ตามรอยกลับไม่ได้** ว่าข้อมูล
    --   บนเอกสารมาจากแถวไหน — จำเป็นตอน audit เมื่อผู้พิจารณาทักว่าข้อมูลคู่แข่งผิด
    --   NULL = แถวที่ผู้ใช้คีย์เอง (source_system = 'USER') ซึ่งไม่มีต้นทาง
    source_row_id BIGINT REFERENCES sgi_fgi_impact_competitors(id) ON DELETE SET NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- แถวที่ผู้ใช้คีย์เอง (source_system = 'USER') อาจไม่มีรหัสสาขา จึงต้อง nullable เช่นกัน
    -- ⬇ business key เดียวกับ sgi_fgi_impact_competitors — แก้ 2026-09-14
    --   NULLS NOT DISTINCT ยุบหลายสาขาที่ไม่มีรหัสเหลือแถวเดียว = ข้อมูลหาย
    --   ⚠️ แก้ 2026-09-14 — fallback แบบ 'name:<ชื่อสาขา>' อย่างเดียว **ยังยุบผิด** 2 เคส:
    --     1. สาขาคนละแบรนด์/คนละโซนที่ชื่อเหมือนกัน → ถูกยุบเป็นแถวเดียว
    --     2. ทั้งรหัสและชื่อว่าง → ทุกแถวได้คีย์ 'name:' เหมือนกันหมด
    --   จึงรวม brand/zone/subzone เข้าไปด้วย และ **แถวที่ไม่มีทั้งรหัสและชื่อถูกปฏิเสธที่ Job 3**
    --   (ระบุตัวตนไม่ได้เลย เก็บไว้ก็ไม่มีใครใช้ได้ · คีย์จึงไม่มีทางเป็น NULL)
    competitor_key VARCHAR(300) GENERATED ALWAYS AS (
        COALESCE(
            NULLIF(btrim(competitor_store_code), ''),
            'name:' || lower(btrim(COALESCE(brand_code, '') || '|' ||
                                   COALESCE(zone_code, '') || '|' ||
                                   COALESCE(subzone_code, '') || '|' ||
                                   -- 🔴 NULLIF กันช่องว่าง: ALLMAP ส่ง '' (ไม่ใช่ NULL) ได้
                                   --    COALESCE เปล่า ๆ จะไม่ตกไป name_th แล้วคู่แข่งคนละร้าน
                                   --    ได้คีย์เดียวกัน → ชน UNIQUE แล้วหายไปหนึ่งแถว
                                   COALESCE(NULLIF(btrim(branch_th), ''), name_th, '')))
        )
    ) STORED,
    CONSTRAINT uq_doc_competitor UNIQUE (doc_no, competitor_key)
);

CREATE TABLE sgi_document_external_factors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    factor_code VARCHAR(30) NOT NULL REFERENCES sgi_external_factors(factor_code),
    date_from DATE, date_to DATE, detail TEXT, remark TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_factor UNIQUE (doc_no, factor_code, date_from),
    CONSTRAINT ck_doc_factor_dates CHECK (date_to IS NULL OR date_from IS NULL OR date_to >= date_from)
);

CREATE TABLE sgi_consideration_logs (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL,   -- ค่าจาก sps_store.workflow_state ของ engine
    result VARCHAR(100) NOT NULL,
    -- APPROVE=ประกันรายได้ · REJECT=ไม่ประกันรายได้ · CANCELLED=ยกเลิกโดยระบบ (decision 14 CancelBySystem) · PENDING=ยังไม่มีผล
    result_category VARCHAR(50) CHECK (result_category IN ('APPROVE','REJECT','CANCELLED','PENDING')),
    detail TEXT,
    consider_by VARCHAR(30) NOT NULL,   -- ผู้ใช้จาก business_user ของระบบเดิม
    action_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, request_id VARCHAR(80)
);

CREATE TABLE sgi_document_attachments (
    attach_id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL,   -- ค่าจาก sps_store.workflow_state ของ engine
    file_name VARCHAR(255) NOT NULL, mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size <= 5242880),
    storage_provider VARCHAR(30) NOT NULL, bucket VARCHAR(120) NOT NULL,
    object_key VARCHAR(500) NOT NULL, sha256 VARCHAR(64) NOT NULL,
    scan_status VARCHAR(20) NOT NULL CHECK (scan_status IN ('PENDING','CLEAN','BLOCKED','FAILED')),
    scanned_at TIMESTAMP, scan_message VARCHAR(500), uploaded_by VARCHAR(30) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, deleted_flag CHAR(1) NOT NULL DEFAULT 'N',
    CONSTRAINT uq_doc_attachment_hash UNIQUE (doc_no, sha256, deleted_flag)
);

CREATE TABLE sgi_compensation_histories (
    id BIGSERIAL PRIMARY KEY,
    store_code VARCHAR(5) NOT NULL,   -- master ของระบบเดิม
    ref_doc_no VARCHAR(10) REFERENCES sgi_compensation_documents(doc_no),
    submit_account_month CHAR(7) NOT NULL, compensate_amount NUMERIC(14,2) NOT NULL,
    accounting_status VARCHAR(30), external_ref VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_compensation_history UNIQUE (store_code, ref_doc_no, submit_account_month)
);

CREATE TABLE sgi_document_cost_details (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL,
    cost_year SMALLINT NOT NULL, cost_month SMALLINT NOT NULL CHECK (cost_month BETWEEN 1 AND 12),
    cost_target_n NUMERIC(14,2), cost_amount_n NUMERIC(14,2),
    cost_target_nc NUMERIC(14,2), cost_amount_nc NUMERIC(14,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_document_cost_detail UNIQUE (doc_no, new_store_code, cost_year, cost_month)
);

CREATE TABLE sgi_document_running_numbers (
    year SMALLINT PRIMARY KEY,   -- ปี ค.ศ. เท่านั้น (เช่น 2026) ห้ามเก็บ พ.ศ.
    last_running_no INTEGER NOT NULL DEFAULT 0 CHECK (last_running_no >= 0),
    -- ใครแตะแถวล่าสุด — เก็บ "ชื่อ job" (JOB8) หรือ x-user-id · ไม่ใส่ CHECK เพราะโดเมนเปิด
    -- (เพิ่ม 2026-09-02 · SQL ของ Job 8 เขียนคอลัมน์นี้อยู่แล้วแต่ DDL ไม่เคยประกาศ)
    updated_by VARCHAR(30),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ⚠️ year เป็น "ค.ศ." (มติ 2026-08-06 · ทั้งระบบเป็น ค.ศ. — หน้าจอ K2 จริงก็ ค.ศ. เช่น 2026/01870)
--    ห้ามใช้ พ.ศ. · ถ้า client ส่ง พ.ศ. มา ให้ BE แปลงด้วย toAD(y) = y >= 2500 ? y - 543 : y ก่อนเสมอ
-- ออกเลขแบบ atomic (upsert กันกรณีปีใหม่ยังไม่มีแถว):
--   INSERT INTO sgi_document_running_numbers (year, last_running_no) VALUES (:ad_year, 1)
--   ON CONFLICT (year) DO UPDATE SET last_running_no = sgi_document_running_numbers.last_running_no + 1,
--                                    updated_at = CURRENT_TIMESTAMP
--   RETURNING last_running_no;   (row lock กันเลขชนเมื่อ batch และผู้ใช้สร้างพร้อมกัน)
--   doc_no = :ad_year || '/' || LPAD(last_running_no::text, 5, '0')

-- ❌ ไม่สร้างตาราง workflow_instances ใน SGI (ตัดสินใจ 2026-08-06) — ใช้ workflow_transaction ของ @srm/glb-workflow

-- ❌ ไม่สร้างตาราง workflow_tasks ใน SGI (ตัดสินใจ 2026-08-06) — ใช้ workflow_approver/workflow_transaction ของ @srm/glb-workflow"""),
        ("5.4 Required Indexes, Partial Uniqueness and Purge", """CREATE INDEX idx_document_status_section ON sgi_compensation_documents(status_code, current_section_code);
CREATE INDEX idx_document_impact_process ON sgi_compensation_documents(impact_process_id);
-- ❌ ไม่มี index ของ workflow_tasks/workflow_instances ใน SGI — ตารางทั้งสองถูกตัดไปแล้ว (2026-08-06)
--    งานค้าง/ผู้อนุมัติปัจจุบันอ่านจาก workflow_transaction + workflow_approver ของ @srm/glb-workflow (schema sps_store)
--    ⚠️ sps_store.workflow_transaction ไม่มี PK และไม่มี index เลย ทั้งที่มี 19,327 แถว (ตรวจ 2026-08-07)
--       -> ห้ามแก้ schema ของ library · กันซ้ำที่ระดับ application ของ SGI แทน
--          หรือจะกันซ้ำ + ทำ index ที่ฝั่ง SGI เอง · ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
CREATE INDEX idx_consideration_timeline ON sgi_consideration_logs(doc_no, action_datetime DESC);
CREATE INDEX idx_interface_pending ON sgi_interface_transactions(data_name, status, sent_at);
CREATE INDEX idx_interface_impact_process ON sgi_interface_transactions(impact_process_id);
CREATE INDEX idx_interface_sales_summary ON sgi_interface_transactions(sales_summary_id);
CREATE INDEX idx_interface_doc ON sgi_interface_transactions(doc_no);

-- index รองรับ FK ที่ PostgreSQL ไม่สร้างให้เอง (เพิ่ม 2026-08-24 หลังตรวจ FK coverage)
CREATE INDEX idx_impact_store_process ON sgi_fgi_impact_stores(impact_process_id);
CREATE INDEX idx_document_impacted_store ON sgi_compensation_documents(impacted_store_code);
CREATE INDEX idx_compensation_history_doc ON sgi_compensation_histories(ref_doc_no);
CREATE INDEX idx_impact_compensation_store ON sgi_fgi_impact_compensations(impacted_store_code);
CREATE INDEX idx_impact_competitor_store ON sgi_fgi_impact_competitors(competitor_store_code);  -- รหัสสาขาคู่แข่งจาก ALLMAP
CREATE INDEX idx_impact_competitor_brand ON sgi_fgi_impact_competitors(brand_code);             -- สรุปรายงานรายแบรนด์
CREATE INDEX idx_document_competitor_code ON sgi_document_competitors(brand_code);   -- สรุปรายงานรายแบรนด์
CREATE INDEX idx_document_factor_code ON sgi_document_external_factors(factor_code);

-- FK 3 เส้นที่ยังขาด leading index (เพิ่ม 2026-09-17 หลัง review ชุด migration)
--   ไม่มี index ฝั่งลูก = ทุก DELETE/UPDATE ฝั่งแม่ต้อง seq scan ตารางลูกทั้งตาราง
--   ORA FGI_NEW_STORE_COMPENSATE ของจริง 23,628 แถว · ลบรอบชดเชยทีเดียวจะกินเวลาผิดปกติ
CREATE INDEX idx_new_store_compensate_impact_store ON sgi_fgi_new_store_compensations(impact_store_id);
CREATE INDEX idx_document_new_store_source_row ON sgi_document_new_stores(source_row_id);
CREATE INDEX idx_document_competitor_source_row ON sgi_document_competitors(source_row_id);

-- index ที่หัวข้อ 6 (Index & Constraint) ระบุไว้ — เดิมมีแต่ในตารางสรุป ยังไม่ถูกสร้างจริง (เพิ่ม 2026-08-25)
CREATE INDEX idx_attachment_scan_status ON sgi_document_attachments(scan_status);
CREATE INDEX idx_consideration_result ON sgi_consideration_logs(result_category);

-- ── index ที่ batch job ต้องใช้จริง (เพิ่ม 2026-09-02 หลังไล่เงื่อนไขตัดสินของ Jobs 2/4/8b) ──
-- ทุกตัวเป็น partial index เพราะแถวที่ job หยิบคือแถว "ยังไม่ถูกดำเนินการ" ซึ่งเป็นส่วนน้อยของตาราง
-- และจะเล็กลงเรื่อย ๆ เมื่อข้อมูลสะสม — index เต็มตารางจะโตโดยไม่จำเป็น
--   Job 2 ค1/ค2: UPDATE ... WHERE verify_status = 'W'
CREATE INDEX idx_impact_store_verify_wait ON sgi_fgi_impact_stores(impact_month)
    WHERE verify_status = 'W';
--   Job 2 ข: ชุด "คู่ร้านที่มีอยู่แล้ว" ของงวด (คัดแถวที่ไม่ถูกตัดทิ้งออกก่อน)
CREATE INDEX idx_impact_store_month_active ON sgi_fgi_impact_stores(impact_month, impacted_store_code)
    WHERE verify_status <> 'N';
--   Job 4: candidate ขอยอดขาย = ผ่านการตรวจแล้ว (P) และยังไม่ได้ส่งขอ (W)
CREATE INDEX idx_impact_store_sales_request ON sgi_fgi_impact_stores(id)
    WHERE verify_status = 'P' AND sales_request_status = 'W';
--   Job 2 ข / Job 6 / Job 8: หารอบชดเชยที่ยัง active ของร้าน
CREATE INDEX idx_impact_process_active ON sgi_fgi_impact_processes(impacted_store_code, impact_month)
    WHERE flag_action IN ('Y', 'W');
--   Job 8b: รอบที่ยังไม่ได้เปิด workflow
CREATE INDEX idx_impact_process_wf_wait ON sgi_fgi_impact_processes(id)
    WHERE workflow_generation_status = 'W';
--   Job 11: กันซ้ำข้อความขาเข้าจาก STA (คู่กับ UNIQUE เดิมที่ครอบ 4 คอลัมน์)
CREATE INDEX idx_interface_in_business_key ON sgi_interface_transactions(business_key, period_key)
    WHERE direction = 'IN';
--   Job 10: watchdog หาข้อความขาออกที่ broker ยังไม่ confirm (มติ 2026-09-08 ข้อ 2.13)
--   ⚠️ ต้องตรงกับ WHERE ของ Job 10 เป๊ะ ๆ ไม่งั้น partial index ไม่ถูกใช้
CREATE INDEX idx_interface_out_pending ON sgi_interface_transactions(created_at)
    WHERE direction = 'OUT' AND (outbox_status IS NULL OR outbox_status <> 'CONFIRMED');

-- Retention worker: delete only terminal, expired, non-held rows in bounded batches.
WITH purge_candidates AS (
    SELECT id FROM sgi_interface_transactions
    WHERE status = 'COMPLETED'
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
      AND data_name = ANY(:data_names)
    ORDER BY id
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM sgi_interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;"""),

    ]


def validate_schema_sql_contract() -> None:
    ddl = "\n".join(sql for _, sql in database_ddl_sections())
    # 2026-08-05/06: ตาราง RBAC, workflow, master ร้าน/ภาค/พนักงาน, email template และ config
    # ใช้ของระบบ SBP เดิม จึงไม่มี DDL ในเอกสารนี้ (เหลือเป็นบรรทัดหมายเหตุ "ไม่สร้างตาราง ... ใน SGI")
    required_ddl = {
        "sgi_sales_transactions": ["txn_date DATE", "window_no SMALLINT", "seq SMALLINT", "sales_amount NUMERIC", "sales_diff NUMERIC", "is_outlier BOOLEAN"],
        "sgi_consideration_logs": ["result VARCHAR(100)", "detail TEXT", "consider_by VARCHAR(30)", "action_datetime TIMESTAMP"],
    }
    reused_tables = [
        "stores", "zones", "branch_types", "employees", "workflow_sections", "document_statuses",
        "workflow_instances", "workflow_tasks", "email_templates", "system_configs",
        "roles", "menus", "menu_permissions", "user_accounts", "operator_assignments",
        # 2026-08-07: ล็อกเพิ่มตามข้อเท็จจริงที่ตรวจฐานจริง
        # engine 13 ตารางอยู่ใน schema sps_store (ไม่ใช่ 10 ตาราง และไม่ใช่ sps_auth)
        "workflow", "workflow_version", "workflow_state", "workflow_status", "workflow_event",
        "workflow_route", "workflow_group", "workflow_group_map", "workflow_transaction",
        "workflow_history", "workflow_approver", "workflow_part", "workflow_part_display",
        # fcs_qssi_score (เอกพจน์) มีอยู่จริงใน sps_store 24,284,545 แถว + import pipeline ใช้งานอยู่
        # (POST /performance/import-qssi + staging fcs_tmp_qssi_score) → ข้อเท็จจริง F4
        # ⚠️ การ์ดนี้เป็นการ "ล็อกชั่วคราวตามข้อเท็จจริง" ไม่ใช่การตัดสิน DP-4:
        #    ถ้าเจ้าของโครงการเลือกทางเลือก B ของ DP-4 (SGI สร้างตารางของตัวเอง)
        #    ต้องถอด "fcs_qssi_score" ออกจากลิสต์นี้ก่อน จึงจะเขียน DDL ลงเอกสารได้
        #    ชื่อพหูพจน์ fcs_qssi_scores ผิดเสมอ ไม่ผูกกับ DP-4
        "fcs_qssi_score", "fcs_qssi_scores",
        "mas_param", "common_code", "business_user", "email_template", "email_sent",
    ]
    # ตัดออกตามมติ 2026-08-07 — ไม่ได้ไป reuse ของระบบเดิม จึงแยกลิสต์และแยกข้อความ error
    # (audit การแก้ master ใช้กลไกของระบบ SBP เดิม — โครง SGI ไม่มีตาราง audit ของตัวเอง)
    removed_tables = ["audit_logs"]
    for table_name in reused_tables:
        if re.search(rf"CREATE TABLE {table_name} \(", ddl):
            raise ValueError(f"table must reuse the existing SBP system, DDL must not exist: {table_name}")
    for table_name in removed_tables:
        if re.search(rf"CREATE TABLE {table_name} \(", ddl):
            raise ValueError(
                f"table was removed from the target schema on 2026-08-07 (not reused), DDL must not exist: {table_name}"
                " — master-data audit uses the existing SBP system mechanism; SGI has no audit table of its own"
            )
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
        # 2026-08-07: ตัด token "mp.can_access = TRUE" ออก — endpoint /menu-permissions ถูกลบจาก
        # plan-api.html แล้ว (RBAC/เมนูใช้ auth-backend ของระบบ SBP เดิม · ตัดสินใจ 2026-08-05)
        # 2026-08-07: ตัด token "instance_status, started_at, started_by" ออก — SQL ที่ INSERT ลง
        # workflow_instances/workflow_tasks ถูกแทนด้วยการเรียก @srm/glb-workflow (schema sps_store) แล้ว
        "sps_store.workflow_transaction",
        "version_no = version_no + 1",
        "FROM sgi_fgi_impact_processes",
        "id AS tracking_id",
        # 2026-09-08 (ข้อ 2.13): alias เปลี่ยนเป็น confirmed_date — ค่าที่บันทึกคือเวลาที่ได้
        # publisher confirm จาก broker ไม่ใช่เวลาที่ STA ตอบรับ (สเปก STA ไม่มี ACK)
        "acked_at AS confirmed_date",
    ]
    for token in required_api:
        if token not in api_source:
            raise ValueError(f"API/DDL contract is missing canonical token: {token}")
    forbidden_api = [
        "u.password_hash",
        # ตารางที่ถูกตัดออกจากโครง 21 ตาราง — ห้ามกลับมาเป็น SQL/DDL ที่ execute ได้ใน plan-api.html
        "FROM workflow_tasks",
        "INTO workflow_tasks",
        "FROM workflow_instances",
        "INTO workflow_instances",
        "FROM document_statuses",
        "INSERT INTO workflow_instances (doc_no, status)",
        "INSERT INTO workflow_instances (instance_id, doc_no, status)",
        "UPDATE sgi_fgi_impact_stores SET workflow_generation_status",
        "WHERE tracking_id = :trackingId",
    ]
    for token in forbidden_api:
        if token in api_source:
            raise ValueError(f"obsolete API/DDL vocabulary remains: {token}")


def lldd_database_blocks(all_topics: list[Topic]) -> list[dict[str, Any]]:
    db_ref_topics = [t for t in all_topics if t.db_tables]
    return [
        h(1, "1. Purpose"),
        p("เอกสารนี้เป็น LLDD Database ระดับรวมของ target schema ระบบ SGI/SBP Mall ใช้เป็น reference สำหรับ BE API, Batch Job, migration, indexing และ transaction"),
        p("**แบ่งงานกับเอกสารพี่น้องให้ชัด:** ฉบับนี้ = **DDL ที่รันได้จริง + index + constraint + transaction + seed** · "
          "`LLDD-Database-Dictionary` = **คำอธิบายรายตาราง/รายคอลัมน์** (มาจากไหน · ใช้ทำอะไร · ทำไมต้องมี · แต่ละคอลัมน์เก็บอะไร) · "
          "`database.md` = ตารางต้นทางตอน migrate และเหตุผลที่ตัดตารางบางตัวทิ้ง"),
        h(1, "2. Architecture Context"),
        bullets([
            "ระบบใหม่รวม EAI และ K2 เข้าเป็น SGI ใช้ฐานข้อมูลเดียวกัน",
            "ไม่มีไฟล์ BPM06001O/BPM06002O/BPM06003O ภายในเพื่อส่งเข้า K2; ใช้ FK จาก sgi_compensation_documents ไป impact_process แทน",
            "Workflow ใช้ engine กลาง `@srm/glb-workflow` **13 ตาราง ใน schema `sps_store`** (workflow · workflow_version · workflow_state · workflow_status · workflow_event · workflow_route · workflow_group · workflow_group_map · workflow_transaction · workflow_history · workflow_approver · workflow_part · workflow_part_display) แทน K2 engine ภายนอก — SGI ไม่สร้างตาราง workflow ของตัวเอง (ตัดสินใจ 2026-08-06 · แก้จำนวนตารางจาก 10 เป็น 13 และแก้ schema จาก sps_auth เป็น sps_store เมื่อ 2026-08-07)",
            "ตัดขั้นบัญชี 04/05 (SDD v7.5 — รวมเข้าการออกแบบแล้ว ไฟล์ต้นฉบับถูกลบจาก repo 2026-08-06); workflow ใช้ section 06/08/01/02/03; SDD ที่ยึดเป็นหลักคือ SDD GI 24/02/2026",
            "มาตรฐานชื่อ table/column เป็น English lower_snake_case",
            "ตาราง job_configs / job_run_histories ถูกตัดออกจาก target schema เมื่อ 2026-08-06 พร้อม 2 แท็บควบคุมของหน้า Batch Job — cron/พารามิเตอร์อยู่ใน backend config · ผลการรันเขียน application log + sgi_interface_transactions",
        ]),
        h(2, "2.1 Input / Progress / Output Contract"),
        table(["Stage", "Contract for implementation"], [
            ["Input", "Target table catalog, data zones, primary keys, foreign-key relationships, migration assumptions, index needs, and transaction boundaries."],
            ["Progress", "Use the data spine impact_process_id -> doc_no -> transaction_id -> approver_id (the last two live in sps_store.workflow_transaction / workflow_approver of @srm/glb-workflow, not in SGI tables) to implement APIs/jobs, then validate referential integrity and idempotency keys."],
            ["Output", "Data dictionary and implementation reference for schema creation, migration, indexing, transaction handling, and test data preparation."],
        ]),
        h(1, "3. Data Zones and Spine"),
        table(
            ["Zone", "Scope", "Core tables", "Owner usage"],
            [
                ["A", "FGI/FCS Impact Pipeline and external interfaces", "sgi_fgi_impact_processes, sgi_fgi_impact_stores, sales, sgi_interface_transactions", "Batch Jobs 1-7, IAS/ALLMAP/QSSI/STA tracking"],
                ["B", "K2 Document (workflow อยู่ที่ engine กลาง)", "sgi_compensation_documents, document_* tables, sgi_consideration_logs, sgi_compensation_histories", "Document APIs, workflow actions, FE detail/list/report"],
                ["C", "Master ที่ SGI เป็นเจ้าของ (RBAC/config/master ร้าน/ผลพิจารณา ใช้ของระบบ SBP เดิม)", "sgi_impacted_stores, sgi_external_factors, sgi_competitors", "Lookup, master maintenance, notification"],
            ],
        ),
        table(
            ["Order", "Key", "Meaning", "Used by"],
            [
                [1, "impact_process_id", "หนึ่งร้านถูกกระทบ + หนึ่งงวด", "FGI/FCS pipeline, Job 8/8b"],
                [2, "doc_no", "เอกสาร YYYY/xxxxx ปี ค.ศ.", "Document APIs, reports, attachments"],
                [3, "transaction_id (@srm/glb-workflow)", "workflow transaction ต่อเอกสาร — `reference_id` = `sgi_compensation_documents.id` (surrogate · DP-1 ปิดแล้ว 2026-08-17)", "Workflow engine ใน schema sps_store"],
                [4, "approver_id (@srm/glb-workflow)", "ผู้อนุมัติต่อ state — แทน task_id เดิม", "Inbox/current approver guard"],
                [5, "employee_id / user_id", "identity — มาจาก BFF header ไม่ใช่ตารางของ SGI", "lookup, assignment"],
            ],
        ),
        h(1, "4. Data Dictionary ระดับตาราง (ภาพรวม)"),
        p("ตารางด้านล่างเป็น **สารบัญระดับตาราง** — โซน · PK · FK · บทบาทย่อ · "
          "👉 **คำอธิบายรายคอลัมน์ (แต่ละคอลัมน์เก็บอะไร ใช้ทำอะไร มาจากไหน ทำไมต้องมี) อยู่ที่เอกสาร `LLDD-Database-Dictionary` คนละฉบับ** — ฉบับนี้ไม่ลงลึกระดับคอลัมน์"),
        table(["Zone", "Table", "PK", "FK / relationship", "Role"], database_table_catalog()),
        h(2, "4.1 Canonical Column Contract"),
        table(
            ["Table", "Canonical columns used by DDL and SQL", "Rejected legacy vocabulary"],
            [
                ["workflow_transaction (@srm/glb-workflow)", "transaction_id, version_id, reference_id, current_state_id, current_status_id, current_approver", "instance_id/doc_no/instance_status ของตาราง workflow_instances ที่ถูกตัดไปแล้ว"],
                ["common_code (ระบบ SBP เดิม)", "code_type = SGI_APPROVE_LIMIT, code, code_value", "system_configs/approve_limit_amount ที่ถูกตัดไปแล้ว"],
                ["fcs_qssi_score (ระบบ SBP เดิม · เอกพจน์)", "store_id, category_code, period, score", "fcs_qssi_scores (พหูพจน์) — ห้ามใช้"],
                ["sgi_sales_transactions", "txn_date, window_no, sales_amount, sales_diff, is_outlier", "sale_date/window_code/net_sales"],
                ["sgi_consideration_logs", "result, result_category, detail, consider_by, action_datetime", "result_code/comment/considered_by/considered_at"],
                ["sgi_interface_transactions", "id, acked_at", "tracking_id/receive_date (API aliases only)"],
                ["sgi_fgi_impact_processes", "workflow_generation_status", "duplicate workflow flag on sgi_fgi_impact_stores"],
            ],
        ),
        h(1, "5. Executable DDL — 20 ตาราง (+ fcs_qssi_score ที่ reuse ของระบบ SBP เดิม = 21 ในโครง · + schema reference)"),
        p("หัวข้อ 5.1-5.4 เป็น PostgreSQL DDL ของ **21 ตารางในโครง SGI** เรียงตาม dependency พร้อม PK, typed FK, unique/check constraint และ index ที่จำเป็น ใช้เป็น migration baseline ได้โดยไม่ต้องเดา column เพิ่มเติม"),
        *[
            block
            for section_title, sql_text in database_ddl_sections()
            for block in (h(2, section_title), code(sql_text, "sql"))
        ],
        h(1, "6. Index and Constraint Plan"),
        table(
            ["Table", "Index / constraint", "Reason"],
            [
                ["sgi_compensation_documents", "UNIQUE (year, running_no), UNIQUE(source, impacted_store_code, impact_month, new_store_code, round_no), INDEX(status_code,current_section_code), INDEX(impact_process_id)", "docNo uniqueness, duplicate guard, list/inbox/report, pipeline trace"],
                ["workflow_transaction (@srm/glb-workflow · sps_store)", "ปัจจุบัน **ไม่มี PK และไม่มี index เลย** ทั้งที่มี 19,327 แถว (ตรวจ 2026-08-07) — query ทุกเส้นที่อ้างตารางนี้จึงเป็น seq-scan ต้องจำกัดเงื่อนไขด้วย version_id + reference_id เสมอ", "current approver guard และ inbox · เป็นตารางของ library ไม่ใช่ของ SGI — **ห้ามแก้ schema** จึงต้องกันซ้ำและประเมินต้นทุน query ที่ฝั่ง SGI"],
                ["sgi_document_new_stores", "INDEX(doc_no) *(ได้จาก UNIQUE (doc_no, new_store_code))*, CHECK compensate_percent between 0 and 100", "detail load and allocation validation"],
                ["sgi_consideration_logs", "INDEX(doc_no, action_datetime DESC), INDEX(result_category)", "timeline/report result filter"],
                ["sgi_document_attachments", "INDEX(doc_no) *(ได้จาก UNIQUE ที่ขึ้นต้นด้วย doc_no)*, INDEX(scan_status), UNIQUE(doc_no, sha256, deleted_flag)", "attachment list/download/security"],
                ["sgi_interface_transactions", "INDEX(data_name,status), INDEX(impact_process_id), INDEX(doc_no)", "tracking และรายการขาออกที่ยังไม่ publisher confirm"],
            ],
        ),
        h(1, "7. Transaction Rules"),
        table(
            ["Use case", "Transaction boundary", "Rollback rule"],
            [
                ["Create document", "docNo sequence lock (sgi_document_running_numbers) + sgi_compensation_documents + initializeWorkflow/addPreApprover ของ @srm/glb-workflow", "any fail rollback all; no partial document · engine อยู่คนละ DataSource จึงต้องมี compensating action เมื่อ commit ฝั่งใดฝั่งหนึ่งไม่ผ่าน"],
                ["Submit action", "ตรวจ current_approver จาก workflow_transaction + insert sgi_consideration_logs + eventWorkflow (เดิน state) + update sgi_compensation_documents", "duplicate/current approver conflict returns 409"],
                ["Auto-assign (SDD 46/48)", "06 เห็นควรไม่ชดเชย -> ปิดเอกสารและตั้งงานเดือนถัดไปให้เจ้าของงานคนเดิม ผ่าน addPreApprover · 06 หยุดชดเชยฯ -> เอกสารกลับเข้า GET /sgi/document/tasks ของ 06 ทันที (stoppedReopenable)", "เดือนที่กดเห็นควรไม่ชดเชย ต้องไม่พบเอกสารใน GET /sgi/document/tasks ของ 06 · เดือนถัดไปต้องพบพร้อม assignee คนเดิม"],
                ["Attachment upload", "metadata insert after storage write with scan_status = PENDING; objectKey never exposed", "storage fail leaves no CLEAN metadata"],
                ["Job 4 IAS request", "durable file (fsync + atomic rename + checksum) ก่อน transaction W→P + outbox READY", "file fail คง W; DB fail rollback W→P/outbox; S3 upload fail retry transaction เดิม"],
                ["Interface confirm/purge", "publisher confirm ตั้ง outbox_status = CONFIRMED + status = COMPLETED แบบ compare-and-set บน transaction เดิม; purge เฉพาะ terminal + purge_after + non-held", "pending/failed/unacked/legal-hold ห้ามลบ"],
                ["Master mutation", "update entity ใน transaction เดียว", "mutation fail ต้อง rollback ครบ"],
            ],
        ),
        h(1, "8. Seed Data"),
        table(
            ["Domain", "Required seed"],
            [
                ["workflow_state / workflow_status (@srm/glb-workflow)", "5 ขั้น 06, 08, 01, 02, 03 + state จบ flow · 6 สถานะเอกสาร (5 waiting + เสร็จสิ้น) — ลงทะเบียนที่ engine ไม่ใช่ตารางของ SGI"],
                ["(ไม่สร้าง) decisions", "ย้ายไป common_code ของระบบเดิม — มติ DP-9 2026-08-10"],
                ["sgi_competitors", "แบรนด์คู่แข่ง 11 รายการ รหัส 01-11 (ไทย + อังกฤษ)"],
                ["sgi_external_factors", "ปัจจัยภายนอกที่ใช้อยู่"],
                ["email_template (ระบบ SBP เดิม)", "EM-01..EM-08"],
                ["common_code / mas_param (ระบบ SBP เดิม)", "SGI_APPROVE_LIMIT: THRESHOLD=100000 (เกณฑ์เดียว · มติ 2026-08-18), impact radius 1/2 km, sales data threshold=60, growth rate threshold=-10"],
            ],
        ),
        h(1, "9. Migration and Verification Checklist"),
        table(
            ["Area", "Check"],
            [
                ["Naming", "all new tables/columns lower_snake_case"],
                ["Leading zero", "store_code/new_store_code stored as VARCHAR(5), never numeric"],
                ["docNo", "year/running_no/doc_no generated in DB transaction; concurrency test 20 parallel requests"],
                ["Workflow", "no active 04/05 accounting sections/statuses; ไม่มีตาราง workflow ของ SGI — ตรวจว่า state/route ถูกลงทะเบียนที่ engine ครบ"],
                ["Security", "no secrets in mas_param/backend config; storage objectKey not returned to FE"],
                ["External interface", "credential/certificate/private key อยู่ Secret Manager ผ่าน secretRef; TLS verify-full (HTTPS สำหรับ EAI S3 · AMQPS สำหรับ RabbitMQ ของ STA); ทดสอบ rotation และ invalid certificate/host key"],
                ["Tracking retention", "backfill typed FK/purge_after, validate FK, dry-run count แล้ว purge เฉพาะ COMPLETED เป็น batch; reconcile count ก่อน/หลัง"],
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
            "scope": "20-table target schema (CREATE 19 + reuse fcs_qssi_score), data zones/spine, DDL reference, indexes, transaction rules, seed data — **คำอธิบายรายคอลัมน์อยู่ที่ LLDD-Database-Dictionary**",
            "base": "LLDD-Database",
        },
        {
            "id": "LLDD-Database-Dictionary",
            "title": "LLDD Database Dictionary - พจนานุกรมข้อมูลรายตาราง/รายคอลัมน์",
            "owner": "BE/DB",
            "scope": "20 ตารางใหม่ (โซน A/B/C) — มาจากไหน · ใช้ทำอะไร · ทำไมต้องมี · ทุกคอลัมน์เก็บอะไรไว้ใช้ทำอะไร",
            "base": "LLDD-Database-Dictionary",
            "pdf_only": True,
        },
        {
            "id": "LLDD-To-Be",
            "title": "LLDD To-Be - SDD Traceability and Effort Allocation",
            "owner": "PM/BA",
            "scope": "สอบทานย้อนกลับ SDD GI หัวข้อ 1.9 To-Be -> เอกสาร FE/BE ที่ใช้ + ชั่วโมงต่อข้อ (implementation + unit test)",
            "base": "LLDD-To-Be",
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
            # LLDD-Database-Dictionary ส่งมอบเป็น PDF อย่างเดียว (มติผู้ใช้ 2026-09-09)
            + (f"<a href=\"word/{escape(base)}.docx\">DOCX</a>" if not doc.get("pdf_only") else "")
            + "</td>"
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
        # BE ที่ไม่ใช่กลุ่ม API และไม่ใช่ Job — รวมเอกสารพื้นฐาน 4 ฉบับที่เพิ่ม 2026-08-07
        # (Database-Structure · Data-Migration-Cutover · Integration-SBP-Platform · Workflow-Engine-Definition)
        "be_ops": [
            t for t in all_topics
            if t.track == "BE" and t.file.startswith("BE/") and not t.file.startswith("Jobs/")
            and not t.file.startswith("BE/LLDD-BE-API")
        ],
        "be_jobs": [t for t in all_topics if t.file.startswith("Jobs/")],
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
        ut = unit_test_hours(topic)
        return (f"{total_hours(topic)}h<br><small>impl {topic.hours} + test {ut}"
                "<br>รวมอยู่ใน Document Detail</small>")
    ut = unit_test_hours(topic)
    if not ut:
        return f"{topic.hours}h"
    return f"{total_hours(topic)}h<br><small>impl {topic.hours} + test {ut}</small>"


def estimate_md(topic: Topic) -> str:
    if is_document_detail_role_doc(topic.file):
        return (f"{total_hours(topic)}h (impl {topic.hours} + test {unit_test_hours(topic)}) "
                "— รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม")
    ut = unit_test_hours(topic)
    if not ut:
        return f"{topic.hours}h"
    return f"{total_hours(topic)}h (impl {topic.hours} + test {ut})"


def build_main_index_csv(all_topics: list[Topic]) -> None:
    """Generate LLDD/Main-Index-FE-BE-Job.csv from the same data as
    main index §3 High Level Activity Plan + §8 BE Batch Job Breakdown.

    The CSV used to be maintained by hand and drifted badly (deleted documents,
    old names, pre-2026-08-07 owners, pre-reschedule dates). It is generated now
    so it can never drift from HIGH_LEVEL_ESTIMATES / JOB_ESTIMATES again.
    """
    counted = [t for t in main_index_ordered(all_topics) if not is_document_detail_role_doc(t.file)]
    schedule = build_topic_schedule(counted)
    high_level = [t for t in counted if not t.file.startswith("Jobs/")]
    be_jobs = [t for t in counted if t.file.startswith("Jobs/")]
    steps = dependency_steps(counted)
    all_steps = dependency_steps(all_topics)
    role_docs = [t for t in all_topics if is_document_detail_role_doc(t.file)]
    # เอกสาร role pack 5 ฉบับมีชั่วโมงจริงของตัวเอง (13 ชม. = impl 10 + test 3) แต่ยอดรวมไปนับที่
    # [FE] Document Detail and Action แล้ว จึงต้องอยู่ใน CSV ให้ครบ 37 ฉบับ (ไม่งั้นคนเปิด CSV จะไม่เห็น)
    # และต้องมีคอลัมน์บอกว่า "ไม่นับซ้ำ" ไม่งั้นบวกคอลัมน์ชั่วโมงแล้วยอดจะเกินยอดจริง
    lines = ["หัวข้อ,owner,ชั่วโมงรวม,implementation,unit test,ลำดับขั้น,นับในยอดรวม"]

    def row(topic: Topic, step: int, counted_flag: str) -> str:
        title = topic.title.replace("LLDD ", "")
        return (f"{title},{topic.owner},{total_hours(topic)},{topic.hours},"
                f"{unit_test_hours(topic)},{step},{counted_flag}")

    for topic in high_level:
        lines.append(row(topic, steps[topic.file], "Y"))
        # แทรก role pack ต่อท้ายเอกสารแม่ทันที เพื่อให้อ่านเป็นเอกสารลูกของหน้าเดียวกัน
        if topic.file == "FE/LLDD-FE-Document-Detail":
            for r in role_docs:
                lines.append(row(r, all_steps[r.file], "N"))
    for topic in be_jobs:
        lines.append(row(topic, steps[topic.file], "Y"))
    (OUT / "Main-Index-FE-BE-Job.csv").write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")


def build_document_portal(all_topics: list[Topic]) -> None:
    groups = grouped_topics(all_topics)
    _billable = [t for t in all_topics if not is_document_detail_role_doc(t.file)]
    impl_hours = sum(t.hours for t in _billable)
    ut_hours = sum(unit_test_hours(t) for t in _billable)
    grand_hours = impl_hours + ut_hours
    main_pdf = "pdf/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.pdf"
    html = f"""<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
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
    /* มือถือ: ตารางกว้าง ~420px ต้องเลื่อนในกล่องของตัวเอง ไม่ดันทั้งหน้า (แก้ 2026-09-07) */
    .table-scroll {{ overflow-x:auto; -webkit-overflow-scrolling:touch; max-width:100%; }}
    @media (max-width: 860px) {{ header, main {{ padding-left:18px; padding-right:18px; }} .quick, .summary {{ grid-template-columns:1fr; }} table {{ table-layout:auto; }} }}
    @media (max-width: 640px) {{ header, main {{ padding-left:12px; padding-right:12px; }} code, td, th {{ overflow-wrap:anywhere; }} }}
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
      <div class="metric"><b>{grand_hours}</b><small>estimated hours</small></div>
    </div>
    <div class="quick">
      <a href="{main_pdf}"><strong>Start here</strong>Main LLDD index PDF</a>
      <a href="pdf/LLDD-API.pdf"><strong>API LLDD</strong>REST contract and endpoint catalog</a>
      <a href="pdf/LLDD-Database.pdf"><strong>Database LLDD</strong>DDL, index, constraint, transaction</a>
      <a href="#document-detail-roles"><strong>Document Detail Roles</strong>5 role-specific FE specs</a>
      <a href="#be-api"><strong>BE API</strong>Common and document APIs</a>
      <a href="#be-jobs"><strong>Batch Jobs</strong>{len(job_numbers())} job specs (Job {", ".join(job_numbers())})</a>
    </div>
  </header>
  <main>
    <p class="note">วิธีใช้: เอกสาร PDF อยู่ในโฟลเดอร์ pdf, Markdown อยู่ในโฟลเดอร์ md และเอกสาร Word อยู่ในโฟลเดอร์ word โดยแต่ละโฟลเดอร์คงโครงสร้าง FE/Jobs เหมือนกัน</p>
    <p class="note">ขอบเขต 2026-08-07: ตัด <code>LLDD-FE-Overview</code> (หน้า Dashboard ยกเลิก) และ <code>LLDD-BE-API-Dashboard-Summary</code> (endpoint <code>/dashboard/summary</code> ตัดถาวร) · เพิ่ม 4 ฉบับ: <code>LLDD-BE-Database-Structure</code>, <code>LLDD-BE-Data-Migration-Cutover</code>, <code>LLDD-BE-Integration-SBP-Platform</code>, <code>LLDD-BE-Workflow-Engine-Definition</code> · เปลี่ยนชื่อ <code>FE-Master-Config</code> → <code>FE-Master-Data</code>, <code>BE-API-Lookup-RBAC-Email</code> → <code>BE-API-Lookup</code>, <code>BE-API-Report-Master-Config</code> → <code>BE-API-Report-and-Master-Data</code></p>
    <p class="note">ขอบเขต 2026-08-06: ตัดเอกสาร LLDD-FE-Batch-Monitor และ LLDD-FE-Email-Template ออกจากชุดส่งมอบ — หน้า Global Config และ Email Template ลบทั้งฟีเจอร์ (บริหารจัดการที่ระบบ SBP เดิม) ส่วนหน้า Batch Job Monitor พักไว้ก่อน ไม่ทำใน phase นี้ (batch job ยังรันปกติ แต่กำหนดพารามิเตอร์ใน backend config)</p>
    <p class="note">แผนทีม 6 คน (ปรับ 2026-08-07): {escape(FE_OWNER_KITTISAK)}, {escape(FE_OWNER)} (FE); {escape(BE_OWNER_BUTSABA)}, {escape(BE_OWNER)}, {escape(BE_OWNER_PEERAKORN)}, และ {escape(BANK_BE_OWNER)} (BE) โดย 1 week = {WORKDAYS_PER_WEEK} วัน, 1 วัน = {HOURS_PER_DAY} ชั่วโมง · เอกสารระบุเฉพาะชั่วโมงและลำดับขั้น ไม่ระบุวันที่</p>

    <h2 id="reference-docs">Reference Design Documents</h2>
    <div class="table-scroll"><table><thead><tr><th>Document</th><th>Owner</th><th>Scope</th><th>Open</th></tr></thead><tbody>
{render_reference_doc_rows()}
    </tbody></table></div>

    <h2 id="fe-core">FE Core Documents</h2>
    <div class="table-scroll"><table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['fe_core'])}
    </tbody></table></div>

    <h2 id="document-detail-roles">Document Detail Role Pack</h2>
    <p>เอกสารชุดนี้แยกจาก LLDD-FE-Document-Detail เพื่อให้อ่านง่ายตาม role ที่ login จริง</p>
    <div class="table-scroll"><table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['fe_roles'])}
    </tbody></table></div>

    <h2 id="be-api">BE API Documents</h2>
    <div class="table-scroll"><table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['be_api'] + groups['be_ops'])}
    </tbody></table></div>

    <h2 id="be-jobs">BE Batch Job Documents</h2>
    <div class="table-scroll"><table><thead><tr><th>Document</th><th>Track</th><th>Owner</th><th>Estimate</th><th>Open</th></tr></thead><tbody>
{render_doc_rows(groups['be_jobs'])}
    </tbody></table></div>
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
        f"- Total estimate: {grand_hours} hours  (implementation {impl_hours} + unit test {ut_hours})",
        "- Unit test: BE/Job 30% · FE 25% ของชั่วโมง implementation · เอกสารสัญญา/ออกแบบไม่คิดแยก (ดู NO_UNIT_TEST_DOCS)",
        "- ขอบเขต 2026-08-07: ตัด `LLDD-FE-Overview` และ `LLDD-BE-API-Dashboard-Summary` · เพิ่ม `LLDD-BE-Database-Structure`, `LLDD-BE-Data-Migration-Cutover`, `LLDD-BE-Integration-SBP-Platform`, `LLDD-BE-Workflow-Engine-Definition` · เปลี่ยนชื่อ `FE-Master-Config` -> `FE-Master-Data`, `BE-API-Lookup-RBAC-Email` -> `BE-API-Lookup`, `BE-API-Report-Master-Config` -> `BE-API-Report-and-Master-Data`",
        "- ขอบเขต 2026-08-06: ตัด `LLDD-FE-Batch-Monitor` และ `LLDD-FE-Email-Template` ออกจากชุดส่งมอบ — หน้า Global Config/Email Template ลบทั้งฟีเจอร์ (ใช้ `mas_param`/`email_template` ของระบบ SBP เดิม) และหน้า Batch Job ย้ายไปกลุ่มเมนู Flow เหลือเฉพาะ Flowchart + Database ที่ใช้ (พารามิเตอร์อยู่ใน backend config)",
        f"- Plan: hours + dependency step only (no calendar dates) with 6-person team `{FE_OWNER_KITTISAK}`, `{FE_OWNER}` (FE) and `{BE_OWNER_BUTSABA}`, `{BE_OWNER}`, `{BE_OWNER_PEERAKORN}`, `{BANK_BE_OWNER}` (BE) — Peerakorn moved FE -> BE on 2026-08-07",
        f"- Working-time rule: 1 week = {WORKDAYS_PER_WEEK} days, 1 day = {HOURS_PER_DAY} hours ({HOURS_PER_WEEK:g} hours/week)",
        f"- Delivery target (2026-08-25): finish in **4 weeks** = {4 * HOURS_PER_WEEK:g} hours per person; team capacity 6 x {4 * HOURS_PER_WEEK:g} = {6 * 4 * HOURS_PER_WEEK:g} hours vs {_grand_total_hours()} hours of work ({_grand_total_hours() / (6 * 4 * HOURS_PER_WEEK) * 100:.0f}% utilisation)",
        _readme_owner_line(),
        _readme_capacity_line(),
        "",
        "## Reference Design Documents",
        "",
        "| Document | Owner | Scope | PDF | DOCX |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {doc['id']} | {doc['owner']} | {doc['scope']} | [PDF](../pdf/{doc['base']}.pdf) | "
            + ("— (PDF อย่างเดียว)" if doc.get("pdf_only")
               else f"[DOCX](../word/{doc['base']}.docx)") + " |"
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
    # README เขียนตรงไม่ผ่าน build_md — ต้อง escape เองไม่งั้นชื่อเล่นในทีมหายเหมือนกัน
    (md_root / "README.md").write_text(
        "\n".join(md_escape_pseudo_tags(line) for line in lines), encoding="utf-8")


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



# ---------------------------------------------------------------------------
# LLDD To-Be — สอบทานย้อนกลับจาก SDD GI หัวข้อ 1.9 To-Be Business Process
# ที่มา: SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI (24/02/2026) สไลด์ 43-62
# ---------------------------------------------------------------------------
TOBE_ITEMS: list[tuple[str, str, str, list[str]]] = [
    ("TB-1", "แก้ไขระบบการสร้างเอกสารชดเชยรายได้", "สไลด์ 43 · 46-51", [
        "Step 1.0 — เพิ่ม**หน้าจองานค้าง** แสดงร้านที่เข้าเงื่อนไขการเปิดกระทบ · เลือกงานของตนเอง · filter · checkbox เลือกหลายเอกสาร · popup ยืนยัน",
        "Step 1.0 — เจ้าหน้าที่ SBP DSA **คีย์ข้อมูลร้านเปิดกระทบเอง** เพื่อให้ระบบคำนวณและ Adjust ยอดชดเชย",
        "Step 1.1 — ฝ่าย SBP DSA ตรวจสอบตัวเลข + ปุ่มพิจารณา 4 ปุ่ม (เห็นควรไม่ชดเชย · หยุดชดเชย · หน่วยงานส่งเสริมฯ SBP · เจ้าหน้าที่ SBP DSA)",
        "**เปิดเรื่องซ้ำได้เองโดยไม่ต้องเปิด SR** — สาขาที่เคยถูกปฏิเสธ/หยุดชดเชย เปิดใหม่ได้ในเดือนเดียวกันหรือเดือนถัดไป",
        "**auto-assign เจ้าของงานคนเดิม (สไลด์ 48)** — (ก) เคสต่อเนื่อง ระบบส่งงานให้เจ้าหน้าที่ SBP DSA **คนเดิม** อัตโนมัติ · (ข) ฝ่าย SBP DSA คลิก **เห็นควรไม่ชดเชย** เอกสารจบและ**ไม่แสดง**ในหน้ารอดำเนินการของ 06 ในเดือนนั้น แล้ว**เดือนถัดไป**ระบบดึงเข้ามาใหม่พร้อมเจ้าของงานคนเดิม",
        "**หยุดชดเชยประกันรายได้ (สไลด์ 46 ข้อ 1.9)** — เอกสารกลับมาแสดงใน**หน้ารอดำเนินการของ ฝ่าย SBP DSA (06) ทันทีในเดือนนั้น** ให้พิจารณาคำขอชดเชยอีกครั้งได้เอง · เปิดเอกสารแล้วเห็นข้อมูลเดิมครบ + แผงพิจารณาชุดเดียวกับสถานะ รอฝ่าย SBP DSA ดำเนินการ · บทบาทอื่นไม่เห็น",
        "**หลังพัฒนาไม่ต้องเปิด SR เพื่อลบข้อมูล (สไลด์ 46 · Note)** — กระบวนการลบ/แก้ข้อมูลเอกสารที่เดิมต้องเปิด SR (มี log ที่ TransectionDeleteStore พร้อม SRNumber) ต้องทำได้ในระบบ · ขอบเขตที่ระบบรองรับคือ **ฝ่าย SBP DSA (06) เปิดพิจารณาเอกสารที่จบแล้วใหม่ได้เอง** โดยไม่ต้องเปิด SR — ไม่มีการลบเอกสารถาวรจากหน้าจอ",
        "**แก้ไขครอบคลุมเอกสารทุก Type (สไลด์ 46 · Note)** — การเปลี่ยนแปลงข้อ TB-1 มีผลกับเอกสารทุกประเภทร้าน ไม่จำกัดเฉพาะ Type ใด Type หนึ่ง",
        "ยอดชดเชย 0: เดือน 1-3 คลิก **ส่งเจ้าหน้าที่ SBP DSA** (มติ 2026-09-01 · เดิม หน่วยงานส่งเสริมธุรกิจ SBP) · เดือน 4 คลิก หยุดชดเชยรายได้",
        "สิทธิ์การมองเห็น — เจ้าหน้าที่/ฝ่าย SBP DSA ดูรายละเอียดได้ทุกสาขา ไม่จำกัดเฉพาะงานที่รับผิดชอบ",
    ]),
    ("TB-2", "ปรับสิทธิ์การตรวจสอบยอดชดเชยรายได้และกระบวนการทำงานของทีมส่งเสริม", "สไลด์ 52-58", [
        "Step 2.1 — ลำดับตรวจสอบใหม่: หน่วยงานส่งเสริม (ผู้จัดการฝ่าย/ผู้เชี่ยวชาญ, เจ้าหน้าที่อาวุโส) → GM ส่งเสริม",
        "เปลี่ยนชื่อปุ่ม **ฝ่ายส่งเสริมธุรกิจ SBP → หน่วยงานส่งเสริมธุรกิจ SBP** (มีผลถึงชื่อสถานะเอกสารด้วย)",
        "เพิ่มสิทธิ์ **เจ้าหน้าที่อาวุโส** ให้ส่งต่อ Flow ให้ GM ส่งเสริมได้ (ระดับตำแหน่งอ้างจาก HR Connect)",
        "map ตำแหน่ง HR → กล่องอนุมัติ: AVP = ผู้ช่วยกรรมการผู้จัดการ · GM = ผู้จัดการทั่วไป/รอง/ผู้ช่วย · หน่วยงานส่งเสริม = ผู้จัดการฝ่าย/ผู้เชี่ยวชาญ, เจ้าหน้าที่อาวุโส",
        "**วงเงินอนุมัติ เกณฑ์เดียว 100,000 ต่อรายการ** — < 100,000 จบที่ GM · ≥ 100,000 ผ่าน GM แล้ว AVP อนุมัติ",
        "**เห็นควรไม่ชดเชยจบทันที** ทั้งระดับหน่วยงานส่งเสริมและ GM (เลิกตีกลับให้ SBP DSA รับทราบก่อน)",
    ]),
    ("TB-3", "ยกเลิก Process บัญชี SBP ในการ Approve ค่าใช้จ่าย + เมนูรายงานใน SBP Mall", "สไลด์ 59-62", [
        "ยกเลิกขั้นบัญชี Approve ยอดชดเชยรายได้ออกจาก workflow",
        "Step 3 — สร้าง **เมนูใหม่ใน SBP Mall: รายงานตรวจสอบประกันรายได้** ให้ทีมบัญชีดึงข้อมูลไปใช้ต่อเอง",
        "ตัวกรอง 7 ตัว — สถานะ (บังคับ · ไม่เลือกแล้วกดค้นหา → 400 **REPORT_STATUS_REQUIRED**) · รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ · Period Statement (ค.ศ.) · ประเภทร้าน (checkbox) · ภาค (checkbox เพิ่มอัตโนมัติเมื่อมีภาคใหม่) · ผลการพิจารณา (radio)",
        "ปุ่ม ค้นหาข้อมูล · Export Excel · เคลียร์ค่าเริ่มต้น · Preview Report · Export CSV to Batch",
    ]),
    ("TB-0", "งานฐานรากที่ To-Be ทุกข้อใช้ร่วมกัน (ไม่ได้ระบุเป็นข้อใน SDD)", "—", [
        "โครงฐานข้อมูลเป้าหมาย 21 ตาราง + migration/cutover จากระบบเดิม",
        f"pipeline FGI/FCS ที่ป้อนข้อมูลให้ทุก To-Be — **batch job ทั้งหมด** {job_list_label()} และงาน interface/อีเมล",
        "สัญญากลาง API/FE (envelope · error · auth · pagination) และ shell ของ portal",
        "master ที่ SGI ดูแลเอง (ปัจจัยภายนอก · แบรนด์คู่แข่ง) และงานทดสอบ/ส่งมอบ",
    ]),
]

# เอกสาร -> {รหัส To-Be: สัดส่วน %}  (แต่ละเอกสารต้องรวมได้ 100)
TOBE_ALLOCATION: dict[str, dict[str, int]] = {
    # ---- FE ----
    "FE/LLDD-FE-Foundation": {"TB-0": 100},
    "FE/LLDD-FE-Integration-Contracts": {"TB-0": 100},
    "FE/LLDD-FE-Testing-Delivery": {"TB-0": 100},
    "FE/LLDD-FE-Master-Data": {"TB-0": 100},
    "FE/LLDD-FE-Document-Lists": {"TB-1": 100},
    "FE/LLDD-FE-Create-Document": {"TB-1": 100},
    "FE/LLDD-FE-Document-Detail": {"TB-1": 60, "TB-2": 40},
    "FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA": {"TB-1": 100},
    "FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer": {"TB-1": 100},
    "FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion": {"TB-2": 100},
    "FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion": {"TB-2": 100},
    "FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP": {"TB-2": 100},
    "FE/LLDD-FE-Report": {"TB-3": 100},
    # ---- BE ----
    "BE/LLDD-BE-Database-Structure": {"TB-0": 100},
    "BE/LLDD-BE-Data-Migration-Cutover": {"TB-0": 100},
    "BE/LLDD-BE-API-Common-Contracts": {"TB-0": 100},
    "BE/LLDD-BE-Job-Batch-Email-SRM": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-2-ImportImpactStore": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-3-ImportImpactCompetitor": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-10-NotifyNoReceiveData": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-11-ConsumeStaCompensate": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-12-NotifyPendingWork": {"TB-0": 100},
    "Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument": {"TB-1": 100},
    "Jobs/LLDD-BE-Job-8-CreateCompensationDocument": {"TB-1": 100},
    "Jobs/LLDD-BE-Job-8b-StartInternalWorkflow": {"TB-1": 100},
    "Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument": {"TB-1": 100},
    "BE/LLDD-BE-API-Document-List-Search": {"TB-1": 100},
    "BE/LLDD-BE-API-Document-Create-Update": {"TB-1": 100},
    "BE/LLDD-BE-API-Document-Detail-Aggregate": {"TB-1": 100},
    "BE/LLDD-BE-API-Attachment-Sales-Timeline": {"TB-1": 100},
    "BE/LLDD-BE-API-Document-Workflow-Actions": {"TB-1": 40, "TB-2": 60},
    "BE/LLDD-BE-API-Workflow-Instances": {"TB-1": 50, "TB-2": 50},
    "BE/LLDD-BE-Workflow-Engine-Definition": {"TB-2": 100},
    "BE/LLDD-BE-API-Lookup": {"TB-2": 100},
    "BE/LLDD-BE-Integration-SBP-Platform": {"TB-2": 100},
    "BE/LLDD-BE-API-Report-and-Master-Data": {"TB-3": 70, "TB-0": 30},
}


def tobe_split(topic: "Topic") -> dict[str, tuple[int, int]]:
    """คืน {รหัส To-Be: (ชม. implementation, ชม. unit test)} ของเอกสารนั้น

    ปัดให้ผลรวมของทุกข้อเท่ากับชั่วโมงจริงของเอกสารเสมอ (ข้อสุดท้ายรับเศษ)
    """
    alloc = TOBE_ALLOCATION.get(topic.file)
    if not alloc:
        raise SystemExit(f"TOBE_ALLOCATION ขาดเอกสาร {topic.file}")
    if sum(alloc.values()) != 100:
        raise SystemExit(f"TOBE_ALLOCATION ของ {topic.file} รวมได้ {sum(alloc.values())}% ไม่ใช่ 100%")
    ut = unit_test_hours(topic)
    keys = list(alloc)
    out: dict[str, tuple[int, int]] = {}
    imp_left, ut_left = topic.hours, ut
    for i, k in enumerate(keys):
        if i == len(keys) - 1:
            out[k] = (imp_left, ut_left)
        else:
            hi = round(topic.hours * alloc[k] / 100)
            hu = round(ut * alloc[k] / 100)
            out[k] = (hi, hu)
            imp_left -= hi
            ut_left -= hu
    return out


def tobe_blocks(all_topics: list["Topic"]) -> list[dict[str, Any]]:
    """LLDD To-Be — เขียนแบบ 'SDD สั่งอะไร · กี่ชั่วโมง · ใครทำ · ไปดูที่ LLDD ฉบับไหน'

    กติกาเวลา (มติ 2026-08-25): **นับเฉพาะงานที่ To-Be เพิ่มเข้ามาใหม่**
    งานฐานราก (TB-0) ที่ต้องทำอยู่แล้วไม่ว่าจะมี To-Be หรือไม่ ไม่นับเป็นเวลาของ To-Be
    """
    by_file = {t.file: t for t in all_topics}
    for t in all_topics:
        tobe_split(t)  # validate ทุกฉบับตั้งแต่ต้น
    billable = [t for t in all_topics if not is_document_detail_role_doc(t.file)]

    def short(owner: str) -> str:
        return owner.split("<")[1].split(">")[0] if "<" in owner else owner

    # code -> {"fe": ชม., "be": ชม., "owners": {ชื่อ: ชม.}, "rows": [...]}
    agg: dict[str, dict[str, Any]] = {
        code: {"fe": 0, "be": 0, "owners": {}, "rows": []} for code, *_ in TOBE_ITEMS
    }
    for t in billable:
        for code, (hi, hu) in tobe_split(t).items():
            hours = hi + hu
            if hours == 0:
                continue
            a = agg[code]
            a["fe" if t.track == "FE" else "be"] += hours
            a["owners"][short(t.owner)] = a["owners"].get(short(t.owner), 0) + hours
            a["rows"].append((t.track, t.file, short(t.owner), hours,
                              TOBE_ALLOCATION[t.file].get(code, 0)))

    tobe_codes = [c for c, *_ in TOBE_ITEMS if c != "TB-0"]
    add_fe = sum(agg[c]["fe"] for c in tobe_codes)
    add_be = sum(agg[c]["be"] for c in tobe_codes)
    base_fe, base_be = agg["TB-0"]["fe"], agg["TB-0"]["be"]

    def owner_line(code: str) -> str:
        fe = [(o, h) for o, h in agg[code]["owners"].items()
              if any(r[0] == "FE" and r[2] == o for r in agg[code]["rows"])]
        be = [(o, h) for o, h in agg[code]["owners"].items()
              if any(r[0] != "FE" and r[2] == o for r in agg[code]["rows"])]
        fmt = lambda xs: " · ".join(f"**{o}** {h} ชม." for o, h in sorted(xs, key=lambda x: -x[1])) or "—"
        return f"FE: {fmt(fe)}   |  BE: {fmt(be)}"

    blocks: list[dict[str, Any]] = [
        h(1, "1. เอกสารนี้ตอบอะไร"),
        p("ตอบคำถามเดียว: **SDD สั่งให้ทำอะไรเพิ่ม · ใช้เวลากี่ชั่วโมง · ใครทำฝั่ง FE ใครทำฝั่ง BE · "
          "รายละเอียดอยู่ใน LLDD ฉบับไหน** — ใช้คู่กับ SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI (24/02/2026) หัวข้อ 1.9 To-Be Business Process"),
        p(f"⚠️ **กติกาการนับเวลา (มติ 2026-08-25):** นับ**เฉพาะงานที่ To-Be เพิ่มเข้ามาใหม่ = {add_fe + add_be} ชั่วโมง** เท่านั้น · "
          f"งานฐานรากที่ต้องทำอยู่แล้วไม่ว่าจะมี To-Be หรือไม่ ({base_fe + base_be} ชั่วโมง — โครงฐานข้อมูล, pipeline FGI/FCS, สัญญากลาง API/FE, shell ของ portal, งานทดสอบ/ส่งมอบ) "
          "แยกไว้ท้ายเอกสารและ**ไม่นับรวมเป็นเวลาของ To-Be**"),
        p("ชั่วโมงที่แสดงคือชั่วโมงเดียวกับที่ประกาศในแต่ละฉบับ (implementation + unit test) · "
          "เอกสารที่รับใช้ To-Be หลายข้อจะถูกแบ่งตามสัดส่วนในคอลัมน์ *สัดส่วนของฉบับ* จึงไม่มีการนับซ้ำ"),
        h(1, "2. สรุปงานที่ To-Be เพิ่มเข้ามา"),
        table(
            ["ข้อ", "SDD สไลด์", "ทำอะไร", "FE (ชม.)", "BE (ชม.)", "รวม (ชม.)"],
            [[code, src, title, str(agg[code]["fe"]), str(agg[code]["be"]),
              f"**{agg[code]['fe'] + agg[code]['be']}**"]
             for code, title, src, _ in TOBE_ITEMS if code != "TB-0"]
            + [["", "", "**รวมงานที่ To-Be เพิ่ม**", f"**{add_fe}**", f"**{add_be}**", f"**{add_fe + add_be}**"],
               ["TB-0", "—", "*(ฐานราก — ไม่นับเป็นเวลาของ To-Be)*",
                f"*{base_fe}*", f"*{base_be}*", f"*{base_fe + base_be}*"]],
        ),
    ]

    idx = 2
    for code, title, src, sdd_points in TOBE_ITEMS:
        if code == "TB-0":
            continue
        idx += 1
        a = agg[code]
        blocks += [
            h(1, f"{idx}. {code} · SDD {src} — {title}"),
            p(f"**ใช้เวลา {a['fe'] + a['be']} ชั่วโมง** (FE {a['fe']} + BE {a['be']})  ·  {owner_line(code)}"),
            h(2, f"{idx}.1 SDD สั่งให้ทำอะไร"),
        ]
        blocks += [bullets(list(sdd_points))]
        blocks += [
            h(2, f"{idx}.2 ทำที่เอกสาร LLDD ฉบับไหน"),
            table(
                ["เอกสาร LLDD", "สาย", "ผู้รับผิดชอบ", "ชม.", "สัดส่วนของฉบับ"],
                [[f"`{f.split('/')[-1]}`", tr, o, f"**{hh}**",
                  "เต็มฉบับ" if pct == 100 else f"{pct}% ของฉบับ"]
                 for tr, f, o, hh, pct in sorted(a["rows"], key=lambda r: (-r[3], r[1]))],
            ),
        ]

    idx += 1
    a0 = agg["TB-0"]
    blocks += [
        h(1, f"{idx}. TB-0 · งานฐานราก — **ไม่นับเป็นเวลาของ To-Be**"),
        p(f"งานชุดนี้ ({a0['fe'] + a0['be']} ชั่วโมง · FE {a0['fe']} + BE {a0['be']}) ต้องทำอยู่แล้วไม่ว่าจะมี To-Be หรือไม่ "
          "— SDD ไม่ได้ระบุเป็นข้อ และไม่ควรนับเป็นต้นทุนของการเปลี่ยนแปลงตาม To-Be · "
          "แสดงไว้เพื่อให้เห็นภาพรวมของชุดส่งมอบทั้งหมดเท่านั้น"),
    ]
    blocks += [bullets(list(next(pts for c, _, _, pts in TOBE_ITEMS if c == "TB-0")))]
    blocks += [
        table(
            ["เอกสาร LLDD", "สาย", "ผู้รับผิดชอบ", "ชม.", "สัดส่วนของฉบับ"],
            [[f"`{f.split('/')[-1]}`", tr, o, str(hh),
              "เต็มฉบับ" if pct == 100 else f"{pct}% ของฉบับ"]
             for tr, f, o, hh, pct in sorted(a0["rows"], key=lambda r: (-r[3], r[1]))],
        ),
        h(1, f"{idx + 1}. เอกสารที่รับใช้ To-Be มากกว่าหนึ่งข้อ"),
        p("เอกสารเหล่านี้ถูกแบ่งชั่วโมง จึงต้องอ่านคู่กันเมื่อวางแผนคน — ถ้าเลื่อนข้อใดข้อหนึ่ง เอกสารที่แชร์กันจะกระทบทั้งสองข้อ"),
        table(
            ["เอกสาร LLDD", "แบ่งให้ข้อไหนบ้าง", "เหตุผลที่ต้องแบ่ง"],
            [
                ["`LLDD-FE-Document-Detail`", "TB-1 60% · TB-2 40%",
                 "หน้าเดียวกันแต่คนละบทบาท — ฝั่ง DSA (คีย์งาน/ปรับยอด) เป็น TB-1 · ฝั่งส่งเสริม/GM/AVP (ปุ่มพิจารณา วงเงิน) เป็น TB-2"],
                ["`LLDD-BE-API-Document-Workflow-Actions`", "TB-1 40% · TB-2 60%",
                 "endpoint เดียวรับ 7-enum — เส้นทางของ DSA เป็น TB-1 · กติกาวงเงิน/ลำดับใหม่/เห็นควรไม่ชดเชยจบทันที เป็น TB-2"],
                ["`LLDD-BE-API-Workflow-Instances`", "TB-1 50% · TB-2 50%",
                 "เปิด instance ให้เอกสารใหม่ (TB-1) และลงทะเบียน version ที่ฝัง state/วงเงินใหม่ (TB-2)"],
                ["`LLDD-BE-API-Report-and-Master-Data`", "TB-3 70% · TB-0 30%",
                 "เส้นรายงาน (TB-3) กับเส้น master ปัจจัยภายนอก/คู่แข่ง (TB-0 ฐานราก) อยู่เอกสารเดียวกัน"],
            ],
        ),
        h(1, f"{idx + 2}. Related LLDD"),
        p("รายละเอียดการทำงานจริงอยู่ในเอกสารที่อ้างถึงข้างบน · ภาพรวมชุดส่งมอบดูที่ `LLDD/md/README.md` · "
          "สัญญา API ดูที่ `LLDD-API` · โครงฐานข้อมูลดูที่ `LLDD-Database`"),
    ]
    return blocks

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
    # พจนานุกรมข้อมูล: **ส่งมอบเป็น PDF อย่างเดียว** (มติผู้ใช้ 2026-09-09)
    # ใช้ตัวเรนเดอร์เฉพาะของตัวเอง — แนวนอน + ปก + สารบัญ + สีแยกโซน + หัวตารางซ้ำทุกหน้า
    # ตัวเรนเดอร์กลางแบ่งคอลัมน์เท่ากันหมด ซึ่งอ่านไม่ได้กับตาราง 223 แถวของเอกสารนี้
    if "pdf" in formats:
        from lldd_db_dictionary import build_dictionary_pdf
        dict_pdf = OUT / FORMAT_DIRS["pdf"] / "LLDD-Database-Dictionary.pdf"
        dict_pdf.parent.mkdir(parents=True, exist_ok=True)
        build_dictionary_pdf(dict_pdf)
    render_all("LLDD To-Be - SDD Traceability and Effort Allocation", tobe_blocks(all_topics), OUT / "LLDD-To-Be", formats)
    for topic in all_topics:
        render_all(topic.title, topic_blocks(topic), OUT / topic.file, formats)
    if formats == {"md", "docx", "pdf"}:
        build_document_portal(all_topics)
        build_main_index_csv(all_topics)
    manifest = build_manifest()
    if formats == {"md", "docx", "pdf"}:
        manifest = write_manifest()
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
