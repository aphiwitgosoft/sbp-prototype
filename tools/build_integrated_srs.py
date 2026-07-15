#!/usr/bin/env python3
"""Build the integrated SBPGI SRS as DOCX and PDF from repository sources."""

from __future__ import annotations

import html as html_lib
import json
import os
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from lxml import html
from PIL import Image as PILImage

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "srs"
TMP = ROOT / "tmp"
DATA_FILE = TMP / "prototype_data.json"
HEADER_LOGO = TMP / "pdfs" / "extracted-images" / "img-002.png"
COVER_BADGE = TMP / "pdfs" / "extracted-images" / "img-000.png"

DOCX_OUT = OUT / "SRS-ระบบประกันรายได้-SBPGI-Integrated-v3.2-Draft.docx"
PDF_OUT = OUT / "pdf" / "SRS-ระบบประกันรายได้-SBPGI-Integrated-v3.2-Draft.pdf"
MD_OUT = OUT / "SRS-ระบบประกันรายได้-SBPGI-Integrated-v3.2-Draft.md"
SCREENSHOT_FULL_DIR = OUT / "screenshots" / "full"
SCREENSHOT_SLICE_DIR = OUT / "screenshots" / "slices"

TEMPLATE_CODE = "RDM-TEM-SRS Template-3.1"
DOC_VERSION = "3.2 Draft"
RELEASE_DATE = "07/07/2026"
TARGET_TABLE_COUNT = 34

SCREEN_LABELS = {
    "index.html": "Overview / Dashboard",
    "flow-fgi.html": "Flow FGI/FCS",
    "k2-flow.html": "Flow K2",
    "plan-flow.html": "Integrated Target Flow",
    "fgi-database.html": "Database FGI/FCS",
    "k2-database.html": "Database K2",
    "plan-database.html": "Target Database Schema",
    "job-batch.html": "Batch Job Console",
    "k2-create.html": "Create Document",
    "k2-list-waiting.html": "Task Inbox",
    "k2-list-related.html": "Related Documents",
    "k2-list-abnormal.html": "Abnormal Assignment",
    "k2-document.html": "Document Detail",
    "k2-report.html": "Status Report",
    "k2-operators.html": "Operator Master",
    "k2-factors.html": "External Factor Master",
    "k2-permissions.html": "RBAC Matrix",
    "system-config.html": "Global Config",
    "plan-email.html": "Email Template",
    "plan-api.html": "API Specification",
}


def clean(value: Any) -> str:
    text = "" if value is None else str(value)
    text = html_lib.unescape(text)
    for filename, label in SCREEN_LABELS.items():
        text = re.sub(rf"\(\s*{re.escape(filename)}\s*\)", f"({label})", text)
        text = text.replace(filename, label)
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2192": "->",
        "\u2190": "<-",
        "\u2265": ">=",
        "\u2264": "<=",
        "\u2260": "!=",
        "\u00d7": "x",
        "\u2026": "...",
        "\u2605": "",
        "\u25c4": "<-",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def element_text(node) -> str:
    return clean(" ".join(node.xpath(".//text()")))


def read_html(name: str):
    return html.fromstring((ROOT / name).read_text(encoding="utf-8"))


def parse_db_entities(name: str, classes: tuple[str, ...]) -> list[dict[str, Any]]:
    root = read_html(name)
    entities: list[dict[str, Any]] = []
    class_expr = " or ".join(
        f'contains(concat(" ", normalize-space(@class), " "), " {cls} ")' for cls in classes
    )
    for box in root.xpath(f"//div[{class_expr}]"):
        heading = box.xpath("./h3[1]")
        table = box.xpath(".//table[1]")
        if not heading or not table:
            continue
        names = [clean(x) for x in heading[0].xpath(".//code/text()") if clean(x)]
        title = " / ".join(names) or element_text(heading[0])
        source_tags = [
            clean(x)
            for x in heading[0].xpath('.//span[contains(@class,"src") or contains(@class,"db-tag")]/text()')
            if clean(x)
        ]
        headers = [element_text(x) for x in table[0].xpath(".//thead/tr[1]/th")]
        rows = []
        for tr in table[0].xpath(".//tbody/tr"):
            cells = [element_text(td) for td in tr.xpath("./th|./td")]
            if cells:
                rows.append(cells)
        notes = [
            element_text(p)
            for p in box.xpath("./p|.//p[contains(@class,'db-note')]")
            if element_text(p)
        ]
        entities.append(
            {"name": title, "source": " · ".join(source_tags), "headers": headers, "rows": rows, "notes": notes}
        )
    return entities


def parse_plan_database() -> list[list[str]]:
    root = read_html("plan-database.html")
    tables = root.xpath(
        '//h2[contains(.,"Data Dictionary")]/ancestor::div['
        'contains(concat(" ", normalize-space(@class), " "), " card ")][1]//table'
    )
    if not tables:
        raise RuntimeError("Plan database table not found")
    rows: list[list[str]] = []
    for tr in tables[0].xpath(".//tbody/tr"):
        cells = [element_text(td) for td in tr.xpath("./td")]
        if not cells:
            continue
        if len(cells) == 1:
            rows.append([cells[0], "", "", "", "", ""])
        else:
            rows.append(cells)
    return rows


def parse_plan_flow_migration() -> list[list[str]]:
    root = read_html("plan-flow.html")
    tables = root.xpath(
        '//h2[contains(.,"จุดเชื่อมต่อที่เปลี่ยน")]/ancestor::div['
        'contains(concat(" ", normalize-space(@class), " "), " card ")][1]//table'
    )
    if not tables:
        return []
    return [[element_text(td) for td in tr.xpath("./td")] for tr in tables[0].xpath(".//tbody/tr")]


def parse_markdown_table(path: Path, header_starts: str) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip().startswith(header_starts)), -1)
    if start < 0:
        return []
    rows: list[list[str]] = []
    for line in lines[start + 2 :]:
        if not line.strip().startswith("|"):
            break
        rows.append([clean(cell) for cell in line.strip().strip("|").split("|")])
    return rows


def unique_texts(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def page_inventory(name: str) -> dict[str, Any]:
    root = read_html(name)
    title = element_text(root.xpath("//h1[1]")[0]) if root.xpath("//h1[1]") else name
    labels = unique_texts(
        [element_text(x) for x in root.xpath("//label")]
        + [element_text(x) for x in root.xpath('//span[contains(@class,"flabel")]')]
    )
    actions = unique_texts([element_text(x) for x in root.xpath("//button")])
    tables: list[dict[str, Any]] = []
    for table in root.xpath("//table"):
        headers = unique_texts([element_text(x) for x in table.xpath(".//thead/tr[1]/th")])
        if headers:
            tables.append({"id": table.get("id", ""), "headers": headers})
    return {"file": name, "title": title, "labels": labels, "actions": actions, "tables": tables}


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 0
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    widths: list[float] | None = None
    path: Path | None = None
    caption: str = ""


class Model:
    def __init__(self):
        self.blocks: list[Block] = []
        self.figure_counter = 0

    def heading(self, text: str, level: int = 1):
        self.blocks.append(Block("heading", clean(text), level=level))

    def para(self, text: str):
        self.blocks.append(Block("paragraph", clean(text)))

    def bullet(self, text: str, level: int = 0):
        self.blocks.append(Block("bullet", clean(text), level=level))

    def number(self, text: str, level: int = 0):
        self.blocks.append(Block("number", clean(text), level=level))

    def table(self, headers: list[str], rows: list[list[Any]], widths: list[float] | None = None):
        clean_rows = [[clean(cell) for cell in row] for row in rows]
        self.blocks.append(Block("table", headers=[clean(h) for h in headers], rows=clean_rows, widths=widths))

    def code(self, text: str):
        normalized = text
        for source, target in {
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "\u2013": "-",
            "\u2014": "-",
            "\u2192": "->",
            "\u2190": "<-",
            "\u2265": ">=",
            "\u2264": "<=",
            "\u2260": "!=",
            "\u00d7": "x",
            "\u2026": "...",
        }.items():
            normalized = normalized.replace(source, target)
        self.blocks.append(Block("code", normalized.strip()))

    def note(self, text: str):
        self.blocks.append(Block("note", clean(text)))

    def pagebreak(self):
        self.blocks.append(Block("pagebreak"))

    def image(self, path: Path, caption: str = ""):
        self.blocks.append(Block("image", path=path, caption=caption))

    def figure(self, path: Path, title: str):
        self.figure_counter += 1
        self.image(path, f"รูปที่ {self.figure_counter}: {clean(title)}")


def screenshot_slices(html_file: str, max_height: int = 1500) -> list[Path]:
    source = SCREENSHOT_FULL_DIR / html_file.replace(".html", ".png")
    if not source.exists():
        raise RuntimeError(f"Missing captured image: {source}")
    SCREENSHOT_SLICE_DIR.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    with PILImage.open(source) as image:
        width, height = image.size
        parts = max(1, (height + max_height - 1) // max_height)
        part_height = (height + parts - 1) // parts
        paths: list[Path] = []
        for index in range(parts):
            top = index * part_height
            bottom = min(height, (index + 1) * part_height)
            output = SCREENSHOT_SLICE_DIR / f"{stem}-{index + 1:02d}.png"
            image.crop((0, top, width, bottom)).save(output, "PNG", optimize=True)
            paths.append(output)
    return paths


def add_screen_capture(model: Model, html_file: str, title: str):
    slices = screenshot_slices(html_file)
    for index, image_path in enumerate(slices, 1):
        suffix = f" - ส่วนที่ {index}/{len(slices)}" if len(slices) > 1 else ""
        model.figure(
            image_path,
            f"{title}{suffix}",
        )


def build_model() -> Model:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    api_groups = data["apiGroups"]
    endpoint_total = sum(len(group["eps"]) for group in api_groups)
    api_group_total = len(api_groups)
    db_rows = parse_plan_database()
    fgi_entities = parse_db_entities("fgi-database.html", ("db-entity",))
    k2_entities = parse_db_entities("k2-database.html", ("ent",))
    migration_rows = parse_plan_flow_migration()
    status_rows = parse_markdown_table(ROOT / "workflow_status_document.md", "| State No")

    model = Model()
    model.heading("1. SRS Overview", 1)
    model.heading("1.1 Purpose", 2)
    model.para(
        "เอกสารนี้กำหนดความต้องการของระบบประกันรายได้ SBPGI แบบรวม โดยสกัดจากต้นแบบหน้าจอ "
        "เอกสาร SRS K2 Version 3.1 เอกสาร Batch Job Technical Document Version 4.0 "
        "และเอกสารออกแบบ Flow/Database ที่อยู่ใน Repository เดียวกัน"
    )
    model.para(
        "ขอบเขตเนื้อหาจัดเรียงตามที่ร้องขอ: Flow, Database, Batch Job, หน้าจอ K2 ที่เหลือ และ API "
        "เพื่อใช้เป็นฐานร่วมสำหรับ Business, Developer, Tester, Operations และผู้อนุมัติการออกแบบ"
    )
    model.heading("1.2 Requirement classification", 2)
    model.table(
        ["Tag", "ความหมาย", "การใช้งาน"],
        [
            ["REQ", "ข้อกำหนดที่มีแหล่งอ้างอิงจาก SRS หรือเอกสาร Batch", "ต้องพัฒนาและทดสอบตามข้อความที่กำหนด"],
            ["DES", "Target design ที่เพิ่มในหน้าจอ plan-flow / plan-database / plan-api / system-config / plan-email", "ต้องผ่าน Architecture และ Business sign-off"],
            ["PROTO", "พฤติกรรมหรือข้อมูลตัวอย่างใน prototype", "ใช้ยืนยัน UX ไม่ใช่ข้อมูล Production"],
            ["OPEN", "ประเด็นขัดแย้งหรือยังไม่ตัดสินใจ", "ห้ามถือเป็นข้อยุติจนกว่าจะมีผู้อนุมัติ"],
        ],
        [0.12, 0.38, 0.5],
    )
    model.heading("1.3 Source of truth", 2)
    for text in [
        "REQ: RDM-SRS ประกันรายได้-K2 Version 3.1 เป็นแหล่งอ้างอิงหลักของหน้าจอและ workflow ฝั่ง K2",
        "REQ: FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0 เป็นแหล่งอ้างอิงหลักของ Jobs 1-10 และ Job 8b",
        "DES: เอกสาร workflow และหน้าจอ Flow เป็น Target flow ของระบบใหม่ที่รวม EAI และ K2 เข้า SBPGI",
        f"DES: เอกสาร database และหน้าจอ Database เป็น Target schema {TARGET_TABLE_COUNT} ตาราง",
        f"DES: หน้าจอ API Specification เป็น REST API target {endpoint_total} endpoints / {api_group_total} กลุ่ม",
        "DES: หน้าจอ Global Config และ Email Template เป็นหน้าจอเสริมสำหรับค่ากำหนดกลางและ Notification Service",
        "PROTO: Prototype ทุกหน้าจอและ shared shell ใช้ยืนยัน fields, actions, modal schema, labels และ navigation",
    ]:
        model.bullet(text)

    model.heading("2. Overall of System", 1)
    model.heading("2.1 Product perspective", 2)
    model.para(
        "ระบบประกันรายได้ใช้บริหารการชดเชยรายได้ของร้าน Store Partner ที่ได้รับผลกระทบจากร้านเปิดใหม่ "
        "โดยรับข้อมูลผลกระทบ ยอดขาย และคะแนน QSSI ประมวลผลเงื่อนไข สร้างเอกสาร "
        "เดิน workflow อนุมัติ และส่งผลชดเชยไปยังระบบบัญชี/Statement"
    )
    model.heading("2.2 Target architecture", 2)
    model.table(
        ["Layer", "องค์ประกอบ", "หน้าที่"],
        [
            ["Frontend", "Web SPA จากต้นแบบหน้าจอ", "Dashboard, K2 forms, report, batch monitor และ administration"],
            ["Backend", "Auth/RBAC, Document, Workflow, Batch Scheduler, Interface, Report/Notification", "ให้บริการ REST API /api/v1 และ orchestration ภายใน"],
            ["Database", "Schema รวม Zone A/B/C", "เก็บ pipeline, เอกสาร/workflow, master/config และ audit"],
            ["External", "QSSI, ALLMAP, IAS/MIS, STA, SAP, SMTP", "คง file/SFTP/API ตามขอบเขตระบบภายนอก"],
        ],
        [0.15, 0.35, 0.5],
    )
    model.note(
        "DES: ระบบใหม่รวม EAI และ K2 engine เข้าเป็นส่วนหนึ่งของ SBPGI "
        "ไฟล์ BPM06001O/BPM06002O/BPM06003O และ K2 StartInstance เดิมถูกแทนด้วย DB write และ Workflow Engine ภายใน"
    )
    model.heading("2.3 User roles", 2)
    model.table(
        ["Code", "Role", "ขอบเขต"],
        [
            ["00", "Default", "ผู้ดำเนินการในแบบฟอร์ม"],
            ["01", "Admin", "เห็นทุกเมนูและจัดการข้อมูลทั้งหมด"],
            ["02", "HQ", "HQ Support และงานบริหารข้อมูล"],
            ["03", "User Admin", "ผู้ดูแลระบบระดับผู้ใช้งาน"],
            ["04", "Report Admin", "รายงานและรายงานสรุป"],
            ["05", "Assign Job", "แจกงานข้อมูลผิดปกติ"],
            ["06", "Report Admin Special", "เรียกดูเอกสารทั้งหมด"],
            ["10", "UserViewer", "อ่านเอกสารตามรายการที่ได้รับสิทธิ์"],
        ],
        [0.12, 0.28, 0.6],
    )
    model.heading("2.4 External interfaces", 2)
    model.table(
        ["System", "Direction", "Mechanism", "Requirement"],
        [
            ["QSSI", "Inbound", "SFTP, mrs* 4 files", "WINDOWS-874; คะแนน 6 หมวด 8,9,12,1,10,16"],
            ["ALLMAP", "Inbound", "SQL Server views / link", "คู่ร้านถูกกระทบ ร้านคู่แข่ง และ POI map"],
            ["IAS/MIS", "Outbound/Inbound", "AMS06001O / AMS06001I", "ยอดขาย 4 windows x 15 days"],
            ["STA", "Outbound/Inbound", "FRBC0001 + ACK/API callback", "ส่งผลชดเชยและเฝ้าระวัง ACK"],
            ["SAP", "Downstream via STA", "Accounting posting", "รับรายการเมื่อ STA approve"],
            ["SMTP", "Outbound", "E-mail", "แจ้งผู้ดำเนินการ เตือนงานค้าง และ batch errors"],
        ],
        [0.14, 0.16, 0.28, 0.42],
    )

    model.pagebreak()
    model.heading("3. Specific Requirements", 1)
    model.heading("3.1 Flow Requirements", 2)
    add_screen_capture(model, "flow-fgi.html", "Flow FGI/FCS (Batch Pipeline)")
    add_screen_capture(model, "k2-flow.html", "Flow K2 - Workflow อนุมัติ")
    add_screen_capture(model, "plan-flow.html", "Flow FGI/FCS + K2 - Target System")
    model.heading("3.1.1 End-to-end flow", 3)
    stages = [
        ("A1", "นำเข้าคะแนน QSSI รายเดือน", "Job 1 รับ 4 ไฟล์ผ่าน SFTP, dedup และบันทึก fcs_qssi_scores"),
        ("A2", "นำเข้าคู่ร้านและคู่แข่ง", "Jobs 2-3 อ่าน ALLMAP ทุกวันที่ 7 และตั้ง verify_status ตามกฎ DENY/ON_PROCESS"),
        ("A3", "ขอยอดขายรายวัน", "Job 4 สร้าง AMS06001O วันที่ 7-16 เวลา 16:00"),
        ("A4", "รับยอดขายและคำนวณ", "Job 5 รับ AMS06001I, คำนวณ 4x15 วัน, outlier |sales_diff| >= 50"),
        ("B1", "สร้างเอกสารอัตโนมัติ", "Document Service สร้าง compensation_documents และรายการลูกโดยตรงใน DB"),
        ("B2", "เปิด workflow", "Workflow Engine เปิด instance เมื่อผ่าน Gen Flow Gate และเริ่ม Section 06"),
        ("C1", "SBP DSA ตรวจสอบ", "Section 06 และ 08 ตรวจข้อมูลและคำนวณเงินชดเชย"),
        ("C2", "ฝ่ายส่งเสริมธุรกิจปรับข้อมูล", "Section 01 แก้ร้านเปิดใหม่ คู่แข่ง ปัจจัย และตรวจ % ชดเชยรวม 100%"),
        ("C3", "GM/AVP อนุมัติ", "Section 02; ยอด > 100,000 ผ่าน Section 03, ยอด <= 100,000 ข้ามไปบัญชี"),
        ("C4", "บัญชีอนุมัติ", "Section 04 และ 05 ตรวจและปิดเอกสาร"),
        ("D1", "ส่ง Statement", "Job 6 ส่ง FRBC0001 ไป STA เวลา 17:00 ทุกวัน"),
        ("D2", "ติดตาม ACK", "STA callback อัปเดต ACK และ Job 10 เป็น safety net เมื่อค้าง >= 1 วัน"),
    ]
    model.table(["Step", "Process", "Requirement"], stages, [0.1, 0.28, 0.62])
    model.heading("3.1.2 Gen Flow Gate", 3)
    for rule in [
        "workflow_generation_status ต้องเป็น W",
        "branch_type อยู่ใน FAM, FB1, FC1, FB2, FVB, FVC",
        "opt_dv_user_id ต้องไม่ว่าง",
        "นิติบุคคลของร้านเปิดใหม่ต้องต่างจากร้านถูกกระทบ",
        "growth_rate_diff ต้องน้อยกว่าหรือเท่ากับ -10",
        "sales_status ต้องเป็น Y หรือ N",
        "กรณี branch type ไม่เข้าเกณฑ์ให้สถานะ N; กรณีอื่นที่ยังไม่พร้อมให้คง W เพื่อแก้ไขและรันซ้ำ",
    ]:
        model.bullet(rule)
    model.heading("3.1.3 Approval workflow", 3)
    model.table(
        ["Order", "Section", "Operator", "Primary transition"],
        [
            ["1", "06", "ฝ่าย SBP DSA", "ยุติ/หยุด หรือส่ง 08/01/04"],
            ["2", "08", "เจ้าหน้าที่ SBP DSA", "คำนวณเสร็จส่ง 01 หรือส่งกลับ 06"],
            ["3", "01", "ฝ่ายส่งเสริมธุรกิจฯ", "เห็นควรชดเชยส่ง 02; ไม่ชดเชยส่ง 06"],
            ["4", "02", "GM ส่งเสริมธุรกิจฯ", ">100,000 ส่ง 03; <=100,000 ส่ง 04"],
            ["5", "03", "ผู้บริหารสำนักบริหาร SBP", "เห็นควรชดเชยส่ง 04 หรือส่งกลับตามสิทธิ์"],
            ["6", "04", "ฝ่ายบัญชี SBP", "ส่ง 05 หรือส่งกลับ 06"],
            ["7", "05", "บัญชีปฏิบัติการภาค", "อนุมัติและปิด workflow"],
        ],
        [0.1, 0.12, 0.3, 0.48],
    )
    model.heading("3.1.4 Status and e-mail transition matrix", 3)
    if status_rows:
        model.table(
            ["State", "Status/Operator", "Before", "Action", "After", "Next operator", "TO"],
            status_rows,
            [0.07, 0.15, 0.17, 0.18, 0.18, 0.15, 0.1],
        )
    model.heading("3.1.5 Migration map", 3)
    if migration_rows:
        model.table(["Connection", "Legacy", "Target", "Source"], migration_rows, [0.22, 0.28, 0.35, 0.15])
    else:
        model.para("รายละเอียดอ้างอิงเอกสาร workflow และหน้าจอ Flow")
    model.heading("3.1.6 Flow controls", 3)
    for rule in [
        "รายการที่ข้อมูลยอดขายไม่ครบ 60 วันต้องแสดงเป็นข้อมูลผิดปกติและแถวสีแดง",
        "ระบบต้องกันเปิด workflow ซ้ำต่อ impact process/document",
        "งานเตือนรายสัปดาห์ทำงานวันจันทร์ 10:00 และ escalation งานค้าง 30/45/60 วันต้องอ่านค่าจาก config",
        "การเปลี่ยนกฎธุรกิจ เช่น -10, 50, 60 วัน และ 100,000 บาท ต้องผ่าน Business sign-off",
        "ทุก transition ต้องบันทึก consideration_logs, ผู้กระทำ, เวลา, สถานะก่อน/หลัง และ correlation id",
    ]:
        model.bullet(rule)
    if (ROOT / "Flow ประกันรายได้.png").exists():
        model.figure(ROOT / "Flow ประกันรายได้.png", "Approve Flow เดิม ใช้ประกอบการเทียบพฤติกรรม")

    model.pagebreak()
    model.heading("3.2 Database Requirements", 2)
    add_screen_capture(model, "fgi-database.html", "Database FGI/FCS")
    add_screen_capture(model, "k2-database.html", "Database K2")
    add_screen_capture(model, "plan-database.html", "Database FGI/FCS + K2 - Target Schema")
    model.heading("3.2.1 Data architecture", 3)
    model.para(
        f"Target database เป็น schema รวม {TARGET_TABLE_COUNT} ตาราง แบ่งเป็น Zone A: FGI/FCS impact pipeline, "
        "Zone B: K2 documents/workflow และ Zone C: shared master/config/audit "
        "โดยใช้ชื่อ table/column แบบ English lower_snake_case"
    )
    model.table(
        ["Order", "Core key", "Purpose"],
        [
            ["1", "impact_process_id", "Hub ของหนึ่งร้านถูกกระทบและหนึ่งงวด"],
            ["2", "doc_no", "เลขเอกสาร YYYY/xxxxx"],
            ["3", "instance_id", "Workflow instance ต่อเอกสาร"],
            ["4", "task_id", "งานต่อ Section/assignee"],
            ["5", "employee_id / role_code", "ผู้ใช้ สิทธิ์ และผู้ปฏิบัติงาน"],
        ],
        [0.1, 0.28, 0.62],
    )
    model.heading("3.2.2 Data dictionary overview", 3)
    model.table(["Table", "Zone", "Source", "PK", "FK / Relation", "Purpose"], db_rows, [0.2, 0.07, 0.12, 0.13, 0.23, 0.25])
    model.heading("3.2.3 Detailed entities - FGI/FCS", 3)
    for entity in fgi_entities:
        model.heading(entity["name"] + (f" ({entity['source']})" if entity["source"] else ""), 4)
        model.table(entity["headers"], entity["rows"], [0.34, 0.24, 0.42])
        for note in entity["notes"]:
            model.note(note)
    model.heading("3.2.4 Detailed entities - K2 / Workflow", 3)
    for entity in k2_entities:
        model.heading(entity["name"] + (f" ({entity['source']})" if entity["source"] else ""), 4)
        widths = [0.38, 0.27, 0.35] if len(entity["headers"]) == 3 else None
        model.table(entity["headers"], entity["rows"], widths)
        for note in entity["notes"]:
            model.note(note)
    model.heading("3.2.5 Constraints and controls", 3)
    for rule in [
        "Store code ต้องเก็บเป็น varchar(5) เพื่อรักษา leading zero",
        "doc_no ต้อง unique และรูปแบบ YYYY/xxxxx; running แยกต่อปี",
        "document_new_stores.compensation_percent รวมต่อเอกสารต้องเท่ากับ 100%",
        "ใช้ foreign key จริงระหว่าง compensation_documents.impact_process_id และ fgi_impact_processes.id",
        "system_configs เป็นแหล่งค่ากำหนดกลางแบบ key-value; ค่าธุรกิจที่ is_editable=false แก้ผ่าน UI/API ไม่ได้",
        "email_templates เก็บเฉพาะ subject/body และตัวแปร merge; ผู้รับ From/To/Cc ต้องอ้าง status_email_rules",
        "ใช้ enum/check constraint สำหรับ W/P/Y/N, Y/W/N, I/C/A/N/S/Z และ task status",
        "ใช้ optimistic locking กับเอกสาร/workflow ที่มีการแก้พร้อมกัน",
        "ทุก master mutation ต้องบันทึก audit_logs ค่าเดิม ค่าใหม่ เหตุผล ผู้แก้ และเวลา",
        "Timestamp ภายใน DB ใช้ UTC; UI แสดง Asia/Bangkok และปี พ.ศ. ตามข้อยุติด้าน format",
    ]:
        model.bullet(rule)
    model.heading("3.2.6 Required remediation", 3)
    remediation = [
        ["P0", "Job 4 transaction", "ใช้ transaction/outbox ไม่ให้ W->P commit ก่อนสร้างไฟล์สำเร็จ"],
        ["P0", "Secrets/TLS", "ย้าย credential ไป Secret Manager และบังคับ TLS"],
        ["P0", "Tracking purge", "แก้ SQL purge data_name และทำ migration/test"],
        ["P1", "Polymorphic FK", "ใช้ typed FK ใน interface_transactions"],
        ["P1", "NULL growth rate", "ส่งรอตรวจสอบแทน auto-accept; ต้องมี Business sign-off"],
        ["P1", "Master joins", "รายงาน reject/reconcile แทนการทำแถวหายเงียบ"],
        ["P1", "Golden files", "ทดสอบ encoding วันที่ พ.ศ. delimiter และ field count ทุก interface"],
    ]
    model.table(["Priority", "Issue", "Target requirement"], remediation, [0.12, 0.28, 0.6])

    model.pagebreak()
    model.heading("3.3 Batch Job Requirements", 2)
    add_screen_capture(model, "job-batch.html", "Batch Job Console - Job 1 Detail")
    model.heading("3.3.1 Batch console", 3)
    model.para(
        "หน้า Batch Job Console สำหรับ Admin แสดง pipeline A-E, รายการ 11 entry points, "
        "สถานะรอบล่าสุด/ถัดไป, เปิดปิดงาน, พารามิเตอร์, manual run, flow, database และ run history"
    )
    model.table(
        ["Job", "Name", "Thai name", "Phase", "Schedule", "Output"],
        [[j["no"], j["name"], j["th"], j["phase"], f"{j['cron']} ({j['cronTh']})", j.get("out", "")] for j in jobs],
        [0.07, 0.18, 0.24, 0.07, 0.22, 0.22],
    )
    model.heading("3.3.2 Common controls", 3)
    for rule in [
        "สิทธิ์จัดการ Batch Job เป็น Admin 01 เท่านั้น",
        "Manual run ต้องระบุงวดข้อมูลและสร้าง run_id; API ตอบ 202 Accepted",
        "ห้ามรัน job เดียวกันซ้อน และต้องป้องกัน shared temp resource ของ Job 1",
        "แก้ไขได้เฉพาะ parameter ที่ระบุ editable; business constants ต้องถูก lock",
        "ทุกการเปิด/ปิด แก้ parameter และ manual run ต้องบันทึก audit",
        "run history ต้องเก็บ start/end, status, row count, file, error, correlation id และผู้สั่งรัน",
        "การ re-run ต้องปฏิบัติตาม runbook ของแต่ละ job โดยตรวจ DB, tracking, backup และปลายทางก่อน",
    ]:
        model.bullet(rule)
    for job in jobs:
        model.heading(f"3.3.J{job['no']} Job {job['no']} - {job['th']}", 3)
        model.table(
            ["Item", "Detail"],
            [
                ["Main class", job.get("cls", "")],
                ["Script", job.get("script", "")],
                ["Schedule", f"{job.get('cron', '')} - {job.get('cronTh', '')}"],
                ["Phase / Type", f"{job.get('phase', '')} / {job.get('tag', '')}"],
                ["Output", job.get("out", "")],
                ["Purpose", job.get("desc", "")],
            ],
            [0.22, 0.78],
        )
        model.heading("Parameters", 4)
        model.table(
            ["Parameter", "Value / Example", "Mode", "Note"],
            [[p[0], p[1], "Editable" if p[3] else "Fixed", p[4]] for p in job.get("params", [])],
            [0.25, 0.28, 0.12, 0.35],
        )
        model.heading("Processing flow", 4)
        for step in job.get("flow", []):
            suffix = ""
            if step.get("d"):
                suffix += f" - {step['d']}"
            if step.get("no"):
                suffix += f" | No: {step['no']}"
            model.number(f"{step.get('t', '')}{suffix}")
        model.heading("Database access", 4)
        model.table(["Table/View", "Access", "Role"], job.get("tables", []), [0.32, 0.1, 0.58])
        meta = job.get("meta", {})
        model.table(
            ["Operational control", "Requirement"],
            [
                ["Transaction", meta.get("trans", "")],
                ["Re-run", meta.get("rerun", "")],
                ["Mail routing", meta.get("mail", "")],
                ["Known risk", meta.get("risk", "")],
            ],
            [0.22, 0.78],
        )

    model.pagebreak()
    model.heading("3.4 K2 Screen Requirements", 2)
    screens = [
        {
            "id": "SCR-01",
            "file": "index.html",
            "name": "Overview / Dashboard",
            "purpose": "แสดงงานค้าง ร้านที่เข้าเกณฑ์ ยอดชดเชย ข้อมูลผิดปกติ กราฟ และทางลัดตามสิทธิ์",
            "actors": "ทุก role ที่ login",
            "rules": [
                "ตัวเลขต้อง aggregate จากข้อมูลจริงและรองรับ cache ไม่เกิน 5 นาที",
                "ทางลัดและ sidebar ต้องสร้างตาม menu_permissions",
                "ค่าชื่อผู้ใช้/role ต้องมาจาก JWT ไม่ใช้ข้อมูล mock",
            ],
        },
        {
            "id": "SCR-02",
            "file": "k2-create.html",
            "name": "สร้างเอกสาร",
            "purpose": "สร้างเอกสารนอกเงื่อนไขอัตโนมัติ หรือส่งสร้างผ่าน FS",
            "actors": "HQ 02, User Admin 03 และผู้ที่ได้รับสิทธิ์",
            "rules": [
                "Manual tab ต้องระบุรหัสร้าน เดือน/ปี ร้านเปิดใหม่ และเหตุผล",
                "FS tab ต้องระบุรหัสร้าน เดือน/ปี และ Period Statement",
                "ตรวจ duplicate ร้าน+งวดก่อนสร้าง",
                "ออกเลขเอกสารอัตโนมัติและเปิด workflow Section 06",
            ],
        },
        {
            "id": "SCR-03",
            "file": "k2-list-waiting.html",
            "name": "เอกสารรอดำเนินการ",
            "purpose": "Task inbox แสดงเฉพาะ OPEN task ที่ผู้ใช้/section ปัจจุบันต้องดำเนินการ",
            "actors": "ผู้ดำเนินการ workflow",
            "rules": [
                "filter ด้วยข้อความ สถานะ ภาค ประเภทร้าน วันที่ ยอดขายลด เงินชดเชย และวันค้าง",
                "คลิกแถวเปิดเอกสาร; งานข้อมูลยอดขายไม่ครบ 60 วันเป็นแถวแดง",
                "Role switcher เป็น prototype aid เท่านั้น Production ใช้ JWT/assignment จริง",
            ],
        },
        {
            "id": "SCR-04",
            "file": "k2-list-related.html",
            "name": "เอกสารที่เกี่ยวข้อง",
            "purpose": "แสดงเอกสารทั้งหมดที่ผู้ใช้เคยมีส่วนร่วม โดยแก้ไขได้เฉพาะงานที่อยู่ในสิทธิ์ปัจจุบัน",
            "actors": "ผู้ใช้งานทั่วไปตามสิทธิ์",
            "rules": [
                "filter และ columns เหมือนหน้ารอดำเนินการ",
                "เอกสารนอก task ปัจจุบันต้องเป็น read-only",
                "ผลการค้นหาต้องจำกัดตาม role และ record-level access",
            ],
        },
        {
            "id": "SCR-05",
            "file": "k2-list-abnormal.html",
            "name": "ข้อมูลผิดปกติ / แจกงาน",
            "purpose": "ค้นหาและมอบหมายรายการผิดปกติให้ผู้รับผิดชอบ",
            "actors": "Assign Job 05 และ Admin",
            "rules": [
                "รองรับ multi-select และแจกงานเฉพาะรายการที่เลือก",
                "แสดงสาเหตุ ผู้รับผิดชอบ และสถานะ assignment",
                "OPEN: เมนูนี้และ API 2 เส้นถูก comment ไว้ รอคำตัดสิน keep/drop",
            ],
        },
        {
            "id": "SCR-06",
            "file": "k2-document.html",
            "name": "เอกสารข้อมูลร้านถูกกระทบ",
            "purpose": "หน้าหลักสำหรับดู แก้ คำนวณ พิจารณา แนบไฟล์ และเดิน workflow",
            "actors": "ผู้ดำเนินการตาม Section และผู้มีสิทธิ์อ่าน",
            "rules": [
                "แสดงหัวเอกสาร ร้านถูกกระทบ ร้านเปิดใหม่ แผนที่ คู่แข่ง ปัจจัย เอกสารแนบ ชดเชย ประวัติ และผลพิจารณา",
                "สิทธิ์แก้ไขต้องประเมินต่อ section/role; ส่วนอื่นเป็น read-only",
                "% ชดเชยร้านเปิดใหม่รวมต้องเท่ากับ 100%",
                "วันที่สิ้นสุดปัจจัยต้องไม่ก่อนวันที่เริ่มต้น",
                "ไฟล์แนบไม่เกิน 5 MB และต้องบันทึก section/uploader/time",
                "ส่งดำเนินการต้องเลือกผล; ข้อความ popup ต้องตรงตาม SRS",
            ],
        },
        {
            "id": "SCR-07",
            "file": "k2-report.html",
            "name": "รายงานสรุปสถานะ",
            "purpose": "ค้นหา แสดงกราฟ/ผล 19 คอลัมน์ และ Export Excel",
            "actors": "Admin 01, HQ 02, Report Admin 04, Report Admin Special 06",
            "rules": [
                "บังคับระบุปีและคืนเฉพาะรายการที่มีเลขเอกสาร",
                "ประเภทร้านและภาคเลือกหลายค่า; สถานะเลือกหนึ่งค่า",
                "ผลและ Excel ต้องใช้ dataset/เงื่อนไขเดียวกัน",
                "แถวข้อมูลยอดขายไม่ครบ 60 วันต้องเป็นสีแดง",
            ],
        },
        {
            "id": "SCR-08",
            "file": "k2-operators.html",
            "name": "กำหนดผู้ปฏิบัติงาน",
            "purpose": "จัดการผู้ปฏิบัติงานต่อ section และ zone",
            "actors": "Admin 01, HQ 02, User Admin 03",
            "rules": [
                "ชื่อพนักงานและตำแหน่งเป็น required; เลือกพนักงานจาก popup",
                "แสดงภาคเมื่อเป็นตำแหน่งส่งเสริมธุรกิจพันธมิตรฯ",
                "เพิ่ม/แก้/ลบต้องบันทึก audit และเหตุผลเมื่อแก้ไข",
            ],
        },
        {
            "id": "SCR-09",
            "file": "k2-factors.html",
            "name": "กำหนดปัจจัยภายนอก",
            "purpose": "จัดการ external factor master และประวัติแก้ไข",
            "actors": "Admin 01, HQ 02, User Admin 03",
            "rules": [
                "factor_code และ factor_name เป็น required; factor_code ห้ามซ้ำ",
                "แก้ได้เฉพาะชื่อและรายละเอียด; ต้องระบุเหตุผล",
                "ทุก mutation ต้องบันทึก audit_logs",
            ],
        },
        {
            "id": "SCR-10",
            "file": "k2-permissions.html",
            "name": "สิทธิ์การเข้าถึงเมนู",
            "purpose": "แสดงและบริหาร RBAC 8 role ต่อ main menu และ master forms",
            "actors": "Admin และผู้ดูแลสิทธิ์ที่ได้รับมอบหมาย",
            "rules": [
                "sidebar ต้องอิงสิทธิ์จาก backend ไม่ใช่ซ่อนเฉพาะฝั่ง FE",
                "API ต้องตรวจ role/record access ซ้ำทุก request",
                "การเปลี่ยนสิทธิ์ต้อง audit และมีผลกับ token/session ตามนโยบาย",
            ],
        },
        {
            "id": "SCR-11",
            "file": "system-config.html",
            "name": "ตั้งค่าระบบ (Global Config)",
            "purpose": "จัดการค่ากำหนดกลางที่ใช้ร่วมทั้งระบบ เช่น รัศมีผลกระทบ เกณฑ์ข้อมูล วงเงินอนุมัติ token และ notification switch",
            "actors": "Admin และผู้ดูแลระบบที่ได้รับมอบหมาย",
            "rules": [
                "config_key ต้องเป็น dot notation และห้ามซ้ำ",
                "value_type ต้อง validate ค่า NUMBER, STRING, BOOLEAN, JSON หรือ CRON ก่อนบันทึก",
                "ค่าที่ is_editable=false เป็นค่าคงที่ทางธุรกิจ แก้หรือลบผ่าน UI/API ไม่ได้",
                "ห้ามเก็บ secret เช่น password, API key หรือ connection string ใน system_configs",
                "ทุกการเพิ่ม แก้ ลบ และ invalidate cache ต้องบันทึก audit_logs พร้อมเหตุผล",
            ],
        },
        {
            "id": "SCR-12",
            "file": "plan-email.html",
            "name": "Email Template",
            "purpose": "กำหนดเนื้อหาอีเมล 8 template ของ Notification Service และผูกจุดส่งกับ workflow/batch",
            "actors": "Admin และผู้ดูแล notification",
            "rules": [
                "รองรับ template EM-01 ถึง EM-08 ครอบคลุม workflow transition, reminder, escalation, batch error และ STA ACK watchdog",
                "แก้ไขได้เฉพาะ subject/body และตัวแปร merge ที่รองรับของ template นั้น",
                "From/To/Cc ต้องล็อกตาม status_email_rules หรือ config ต่อ job ไม่ให้แก้ใน template",
                "ต้องรีเซ็ตกลับ Default ได้ทั้งราย template และทั้งหมด",
                "ทุกการแก้ไขหรือรีเซ็ตต้องบันทึก audit_logs พร้อมเหตุผล",
            ],
        },
    ]
    for screen in screens:
        inv = page_inventory(screen["file"])
        model.heading(f"{screen['id']} {screen['name']}", 3)
        add_screen_capture(model, screen["file"], screen["name"])
        model.table(
            ["Item", "Requirement"],
            [["Purpose", screen["purpose"]], ["Actor", screen["actors"]], ["Pre-condition", "ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล"]],
            [0.2, 0.8],
        )
        if inv["labels"]:
            model.heading("Input / filter fields", 4)
            model.para(" · ".join(inv["labels"]))
        if inv["tables"]:
            model.heading("Displayed tables", 4)
            for table_info in inv["tables"]:
                label = table_info["id"] or "Table"
                model.bullet(f"{label}: " + " | ".join(table_info["headers"]))
        if inv["actions"]:
            model.heading("Actions", 4)
            model.para(" · ".join(inv["actions"]))
        model.heading("Business rules / acceptance", 4)
        for rule in screen["rules"]:
            model.bullet(rule)
    model.heading("3.4.13 Shared UI contract", 3)
    for rule in [
        "ทุกหน้าจอต้องมี metadata สำหรับ page, nav, module, breadcrumb, sidebar mount และ main content",
        "Header/sidebar ถูกสร้างโดย shared shell; ห้ามทำซ้ำในแต่ละหน้า",
        "Schema modal อ้างชื่อ table header แบบ exact match; การเปลี่ยน label ต้องแก้ mapping และทดสอบ add/view/edit/delete",
        "รองรับ desktop และ responsive layout; ตารางกว้างต้องเลื่อนแนวนอนโดยไม่ตัดข้อมูล",
        "ข้อความ popup/validation ภาษาไทยและ source tag (FGI/FCS), (K2), (ใหม่) ต้องคงตามข้อกำหนด",
    ]:
        model.bullet(rule)

    model.pagebreak()
    model.heading("3.5 API Requirements", 2)
    add_screen_capture(model, "plan-api.html", "API Specification")
    model.heading("3.5.1 Common conventions", 3)
    model.table(
        ["Topic", "Requirement"],
        [
            ["Base URL", "/api/v1"],
            ["Authentication", "Authorization: Bearer <JWT>; login/refresh public; callbacks ใช้ API key; internal workflow ใช้ service token"],
            ["Format", "JSON UTF-8; วันที่ ISO-8601 ปี ค.ศ.; FE แปลงปีแสดงผลตามข้อยุติ"],
            ["Pagination", "?page=1&size=20 -> {page,size,total,items:[]}"],
            ["Error", '{"code":"DOC_409","message":"ข้อความภาษาไทยตรงตาม SRS"}'],
            ["Audit", "ทุก mutation บันทึก actor จาก JWT/service identity, correlation id และ before/after ที่เหมาะสม"],
            ["Idempotency", "create/action/callback/manual run ต้องรองรับ idempotency key หรือ business duplicate guard"],
        ],
        [0.2, 0.8],
    )
    model.heading("3.5.2 Endpoint catalog", 3)
    catalog_rows = []
    for group in api_groups:
        for ep in group["eps"]:
            catalog_rows.append([group["name"], ep["m"], ep["p"], ep["roles"], ep["sum"], ep["refT"]])
    model.table(
        ["Group", "Method", "Path", "Roles", "Purpose", "Source"],
        catalog_rows,
        [0.14, 0.07, 0.2, 0.13, 0.34, 0.12],
    )
    model.heading("3.5.3 Endpoint details", 3)
    endpoint_counter = 0
    for group_idx, group in enumerate(api_groups, 1):
        model.heading(f"API Group {group_idx}: {group['name']} ({group['refT']})", 3)
        for ep in group["eps"]:
            endpoint_counter += 1
            model.heading(f"API-{endpoint_counter:02d} {ep['m']} {ep['p']}", 4)
            model.table(
                ["Item", "Requirement"],
                [
                    ["Purpose", ep["sum"]],
                    ["Roles", ep["roles"]],
                    ["Source", ep["refT"]],
                ],
                [0.18, 0.82],
            )
            model.para("Flow:")
            for step in ep.get("flow", []):
                model.number(step)
            model.table(["Table", "Access", "Role"], ep.get("db", []), [0.32, 0.1, 0.58])
            model.para("Request")
            model.code(ep.get("req", ""))
            model.para("Response")
            model.code(ep.get("res", ""))
            if ep.get("err"):
                model.para("Errors")
                for err in ep["err"]:
                    model.bullet(err)

    model.pagebreak()
    model.heading("4. Non-Functional Requirements", 1)
    model.table(
        ["Category", "Requirement"],
        [
            ["Performance", "รองรับผู้ใช้พร้อมกันเฉลี่ย 80 คน สูงสุด 100 คน; interaction ปกติตอบภายใน 30 วินาทีตาม SRS เดิม; API list/report ต้องกำหนด SLA แยกก่อน production"],
            ["Availability", "บริการ 7x24 ยกเว้น maintenance window; Batch Scheduler ต้อง resume/reconcile หลัง restart"],
            ["Reliability", "Transaction ที่สำเร็จต้อง durable; error ต้องไม่เขียนข้อมูลบางส่วน; file interface ต้อง reconcile row/file/tracking"],
            ["Security", "SSO/AD หรือ LDAP, JWT อายุจำกัด, refresh token revoke, least privilege, secrets vault, TLS, API key rotation และ server-side RBAC"],
            ["Auditability", "บันทึก login, document mutation, workflow action, master change, job action และ external callback พร้อม actor/time/correlation id"],
            ["Usability", "รองรับ Chrome รุ่นองค์กร, ภาษาไทย, keyboard focus, responsive table/modal และข้อความ validation ตรงตาม SRS"],
            ["Maintainability", "แยก FE/BE, OpenAPI 3.0 contract, configuration versioning, migration scripts และ automated tests สำหรับ business rules"],
            ["Portability", "Deployment ต้องไม่ผูก credential/path กับเครื่อง; ใช้ environment/config/secret manager"],
            ["Backup/Recovery", "กำหนด RPO/RTO, backup DB/config/object files และทดสอบ restore อย่างน้อยตามรอบองค์กร"],
            ["Observability", "Metrics/log/trace สำหรับ API, batch, workflow, interface ACK, queue lag และ e-mail failure พร้อม alert threshold"],
        ],
        [0.2, 0.8],
    )

    model.heading("5. Acceptance and Traceability", 1)
    model.heading("5.1 High-priority acceptance criteria", 2)
    for rule in [
        "เอกสารหนึ่งรายการ trace ได้ครบ impact_process_id -> doc_no -> instance_id -> task_id",
        "กฎ route 100,000 บาททำงานถูกต้องทั้งค่าต่ำกว่า เท่ากับ และสูงกว่า",
        "ผลรวม % ชดเชย 100% ถูกตรวจทั้ง FE และ BE",
        "ร้านยอดขายไม่ครบ 60 วันถูก flag ใน inbox/report และมีเหตุผลตรวจสอบย้อนกลับ",
        "Jobs 1-10/8b รันซ้ำตาม runbook โดยไม่สร้างข้อมูลซ้ำหรือสูญหาย",
        f"API {endpoint_total} เส้นผ่าน authentication/authorization, validation, audit, idempotency และ error contract",
        "ข้อมูล export/import ทุก interface ผ่าน golden-file test เรื่อง encoding/date/delimiter/field count",
        "หน้าจอและ Excel report ให้ผลตรงกันภายใต้ filter เดียวกัน",
    ]:
        model.bullet(rule)
    model.heading("5.2 Traceability matrix", 2)
    trace_rows = [
        ["FLOW-01", "Flow FGI/FCS", "FGI/FCS batch pipeline A-E", "3.1, 3.3"],
        ["FLOW-02", "Flow K2", "K2 approval workflow", "3.1.3-3.1.4"],
        ["FLOW-03", "Integrated Target Flow", "Integrated target architecture/flow", "2.2, 3.1"],
        ["DB-01", "Database FGI/FCS", "FGI/FCS detailed entities", "3.2.3"],
        ["DB-02", "Database K2", "K2 detailed entities", "3.2.4"],
        ["DB-03", "Target Database Schema", f"{TARGET_TABLE_COUNT}-table target schema", "3.2.1-3.2.2"],
        ["JOB-01", "Batch Job Console", "11 entry points and console", "3.3"],
        ["K2-01", "Overview / Dashboard", "Dashboard", "SCR-01"],
        ["K2-02", "Create Document", "Create document", "SCR-02"],
        ["K2-03", "Task Inbox", "Task inbox", "SCR-03"],
        ["K2-04", "Related Documents", "Related documents", "SCR-04"],
        ["K2-05", "Abnormal Assignment", "Abnormal assignment", "SCR-05 / OPEN"],
        ["K2-06", "Document Detail", "Document detail/action", "SCR-06"],
        ["K2-07", "Status Report", "Status report", "SCR-07"],
        ["K2-08", "Operator Master", "Operator master", "SCR-08"],
        ["K2-09", "External Factor Master", "External factor master", "SCR-09"],
        ["K2-10", "RBAC Matrix", "RBAC matrix", "SCR-10"],
        ["K2-11", "Global Config", "Global system configuration", "SCR-11"],
        ["K2-12", "Email Template", "Notification email templates", "SCR-12"],
        ["API-01", "API Specification", f"{endpoint_total} REST endpoints", "3.5"],
    ]
    model.table(["ID", "Screen / Artifact", "Scope", "SRS section"], trace_rows, [0.12, 0.28, 0.42, 0.18])

    model.heading("6. Open Items and Decisions Required", 1)
    open_items = [
        ["OPEN-01", "Document year", "Prototype/CLAUDE use พ.ศ. 2569/xxxxx แต่เอกสาร inventory บางส่วนระบุ ค.ศ.; ต้องยืนยัน canonical storage/display"],
        ["OPEN-02", "Abnormal screen", "หน้าจอข้อมูลผิดปกติและ 2 API endpoints ถูก comment; ต้องตัดสินใจ keep/drop และปรับ role 05"],
        ["OPEN-03", "Job 8b schedule", "เวลา scheduler จริงต้องยืนยันกับ Operations"],
        ["OPEN-04", "NULL growth_rate", "Target เสนอรอตรวจสอบแทน auto-accept; ต้องมี Business sign-off"],
        ["OPEN-05", "Legacy date routing", "เงื่อนไขร้านก่อน/หลัง 1/10/2557 จาก flow เดิมยังต้อง verify กับ SRS v3.1"],
        ["OPEN-06", "NFR SLA/RPO/RTO", "SRS เดิมให้ค่ารวมระดับสูง; ต้องกำหนด SLA API/report/batch และ RPO/RTO production"],
        ["OPEN-07", "File retention", "กำหนด retention, encryption และ purge สำหรับ attachment/interface/archive"],
        ["OPEN-08", "Exact permission matrix", "ยืนยัน menu/master permission ต่อ role ก่อน implementation backend"],
    ]
    model.table(["ID", "Topic", "Decision required"], open_items, [0.12, 0.22, 0.66])

    model.heading("7. Appendices", 1)
    model.heading("7.1 Definitions and abbreviations", 2)
    model.table(
        ["Term", "Definition"],
        [
            ["SBPGI", "Target integrated system for FGI/FCS processing and K2-style documents/workflow"],
            ["SP / Store Partner", "ร้าน Franchise ที่อยู่ในขอบเขตประกันรายได้"],
            ["FGI/FCS", "Legacy batch domains for impact and QSSI data"],
            ["K2", "Legacy BPM/workflow platform and original K2 SRS scope"],
            ["STA", "Statement/accounting interface system"],
            ["IAS/MIS", "Sales data interface"],
            ["QSSI", "Monthly score source"],
            ["ALLMAP", "Store/competitor/map source"],
            ["Gen Flow Gate", "ชุดเงื่อนไขก่อนสร้าง/เปิด workflow"],
        ],
        [0.24, 0.76],
    )
    model.heading("7.2 References", 2)
    refs = [
        "RDM-SRS ประกันรายได้-K2.pdf - Version 3.1",
        "FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf",
        "RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md",
        "ประกันรายได้-K2-รายการหน้าจอ.md",
        "Workflow design documents and Flow screens",
        "Database design documents and Database screens",
        "Batch Job, API Specification, Global Config, Email Template, K2 screens and shared shell",
    ]
    for ref in refs:
        model.bullet(ref)
    return model


def make_md(model: Model):
    lines = [
        "# SOFTWARE REQUIREMENT SPECIFICATION",
        "",
        "## ระบบประกันรายได้ SBPGI",
        "",
        f"Version {DOC_VERSION}",
        "",
        "> Generated from repository requirements and prototype screens. See source-of-truth and open-item sections.",
        "",
    ]
    for block in model.blocks:
        if block.kind == "heading":
            lines.extend(["", f"{'#' * min(6, block.level)} {block.text}", ""])
        elif block.kind == "paragraph":
            lines.extend([block.text, ""])
        elif block.kind == "bullet":
            lines.append(f"- {block.text}")
        elif block.kind == "number":
            lines.append(f"1. {block.text}")
        elif block.kind == "note":
            lines.extend([f"> {block.text}", ""])
        elif block.kind == "code":
            lines.extend(["```text", block.text, "```", ""])
        elif block.kind == "table":
            lines.append("| " + " | ".join(block.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
            for row in block.rows:
                cells = [cell.replace("|", "\\|").replace("\n", "<br>") for cell in row]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
        elif block.kind == "image" and block.path:
            lines.extend([f"![{block.caption}]({block.path.name})", ""])
        elif block.kind == "pagebreak":
            lines.extend(["", "---", ""])
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def docx_set_font(run, name="Cordia New", size: float | None = None, bold: bool | None = None, color: RGBColor | None = None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in [("top", top), ("start", start), ("bottom", bottom), ("end", end)]:
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_table_widths(table, total_twips: int, proportions: list[float] | None):
    cols = len(table.columns)
    if proportions is None or len(proportions) != cols:
        proportions = [1 / cols] * cols
    norm = sum(proportions)
    widths = [round(total_twips * x / norm) for x in proportions]
    widths[-1] += total_twips - sum(widths)
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total_twips))
    tbl_w.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        grid_col = OxmlElement("w:gridCol")
        grid_col.set(qn("w:w"), str(width))
        grid.append(grid_col)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[idx]))
            tc_w.set(qn("w:type"), "dxa")


def set_paragraph_border(paragraph, side: str, color: str, size: int = 8, space: int = 1):
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    edge = OxmlElement(f"w:{side}")
    edge.set(qn("w:val"), "single")
    edge.set(qn("w:sz"), str(size))
    edge.set(qn("w:space"), str(space))
    edge.set(qn("w:color"), color)
    p_bdr.append(edge)


def add_field(paragraph, instruction: str):
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = instruction
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def new_docx_numbering_id(doc: Document) -> int:
    numbering = doc.part.numbering_part.element
    existing_abs = [int(node.get(qn("w:abstractNumId"))) for node in numbering.findall(qn("w:abstractNum"))]
    existing_num = [int(node.get(qn("w:numId"))) for node in numbering.findall(qn("w:num"))]
    abstract_id = max(existing_abs, default=0) + 1
    num_id = max(existing_num, default=0) + 1

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "singleLevel")
    abstract.append(multi)
    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")
    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), "decimal")
    lvl_text = OxmlElement("w:lvlText")
    lvl_text.set(qn("w:val"), "%1.")
    lvl_jc = OxmlElement("w:lvlJc")
    lvl_jc.set(qn("w:val"), "left")
    p_pr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), "540")
    tabs.append(tab)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "540")
    ind.set(qn("w:hanging"), "300")
    p_pr.append(tabs)
    p_pr.append(ind)
    lvl.extend([start, num_fmt, lvl_text, lvl_jc, p_pr])
    abstract.append(lvl)
    numbering.append(abstract)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(abstract_id))
    num.append(abstract_ref)
    numbering.append(num)
    return num_id


def apply_docx_numbering(paragraph, num_id: int):
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), "0")
    num_id_node = OxmlElement("w:numId")
    num_id_node.set(qn("w:val"), str(num_id))
    num_pr.extend([ilvl, num_id_node])
    p_pr.append(num_pr)


def configure_docx_styles(doc: Document):
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.8)
    sec.bottom_margin = Cm(2.8)
    sec.left_margin = Cm(1.75)
    sec.right_margin = Cm(1.75)
    sec.header_distance = Cm(0.8)
    sec.footer_distance = Cm(0.75)
    sec.different_first_page_header_footer = True

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Cordia New"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Cordia New")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Cordia New")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Cordia New")
    normal.font.size = Pt(14)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.05

    for name, size, before, after in [
        ("Heading 1", 18, 12, 6),
        ("Heading 2", 16, 10, 5),
        ("Heading 3", 15, 8, 4),
        ("Heading 4", 14, 6, 3),
    ]:
        style = styles[name]
        style.font.name = "Cordia New"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Cordia New")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Cordia New")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Cordia New")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ["List Bullet", "List Bullet 2", "List Number", "List Number 2"]:
        style = styles[name]
        style.font.name = "Cordia New"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Cordia New")
        style.font.size = Pt(14)
        style.paragraph_format.space_after = Pt(2)

    settings = doc.settings._element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)


def build_docx(model: Model):
    doc = Document()
    configure_docx_styles(doc)
    section = doc.sections[0]

    header = section.header
    header_table = header.add_table(rows=1, cols=2, width=Cm(17.5))
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False
    set_table_widths(header_table, 9920, [0.5, 0.5])
    if HEADER_LOGO.exists():
        p = header_table.cell(0, 0).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run().add_picture(str(HEADER_LOGO), width=Cm(3.95))
    p = header_table.cell(0, 1).paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(TEMPLATE_CODE)
    docx_set_font(r, size=10)
    for cell in header_table.rows[0].cells:
        set_cell_margins(cell, 0, 0, 0, 0)
    hp = header.add_paragraph()
    hp.paragraph_format.space_after = Pt(0)
    set_paragraph_border(hp, "bottom", "FF0000", 8, 0)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.paragraph_format.space_before = Pt(0)
    fp.paragraph_format.space_after = Pt(2)
    set_paragraph_border(fp, "top", "FF0000", 8, 0)
    ft = footer.add_table(rows=3, cols=2, width=Cm(17.5))
    ft.alignment = WD_TABLE_ALIGNMENT.CENTER
    ft.autofit = False
    set_table_widths(ft, 9920, [0.68, 0.32])
    left = [
        "Confidential - Restricted Circulation Only",
        "© 2023 Gosoft (Thailand) Co., Ltd prepared for internal use only",
        "Printed copies of this Document are not controlled and will not be updated.",
    ]
    for idx, text in enumerate(left):
        p = ft.cell(idx, 0).paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        docx_set_font(r, size=8.5, color=RGBColor(255, 0, 0) if idx == 0 else RGBColor(50, 50, 50))
        p = ft.cell(idx, 1).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(0)
        if idx == 0:
            r = p.add_run(TEMPLATE_CODE)
            docx_set_font(r, size=8.5, color=RGBColor(30, 70, 255))
        elif idx == 2:
            r = p.add_run("Page ")
            docx_set_font(r, size=8.5)
            add_field(p, "PAGE")
            r = p.add_run(" of ")
            docx_set_font(r, size=8.5)
            add_field(p, "NUMPAGES")
    for row in ft.rows:
        for cell in row.cells:
            set_cell_margins(cell, 0, 0, 0, 0)

    # Cover
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("SOFTWARE REQUIREMENT SPECIFICATION")
    docx_set_font(r, size=22)
    p.paragraph_format.space_after = Pt(26)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ระบบประกันรายได้ SBPGI")
    docx_set_font(r, size=20, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"VERSION {DOC_VERSION.upper()}")
    docx_set_font(r, size=17)
    p.paragraph_format.space_after = Pt(42)
    if COVER_BADGE.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(COVER_BADGE), width=Cm(5.2))
    for _ in range(4):
        doc.add_paragraph()
    for line in [
        "Gosoft (Thailand) CO.,LTD.",
        "313 CP Tower, 24th Fl., Silom Road",
        "Bangrak, Bangkok 10500.",
        "Website: www.gosoft.co.th",
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(line)
        docx_set_font(r, size=12)
    doc.add_page_break()

    # Version history
    doc.add_heading("Document Version History", level=1)
    table = doc.add_table(rows=2, cols=6)
    table.style = "Table Grid"
    headers = ["Version Number", "Release Date", "Created By", "Detail", "Reviewed by", "Authorized by"]
    values = [
        "3.2 Draft",
        RELEASE_DATE,
        "SBPGI Project Team",
        "Consolidate Flow, Database, Batch Job, K2 screens and API with full figures",
        "",
        "",
    ]
    for i, value in enumerate(headers):
        table.cell(0, i).text = value
    for i, value in enumerate(values):
        table.cell(1, i).text = value
    set_table_widths(table, 9920, [0.11, 0.12, 0.15, 0.34, 0.14, 0.14])
    set_repeat_table_header(table.rows[0])
    for ridx, row in enumerate(table.rows):
        for cell in row.cells:
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx == 0:
                set_cell_shading(cell, "E7E7E7")
            for p in cell.paragraphs:
                for r in p.runs:
                    docx_set_font(r, size=11, bold=(ridx == 0))
    doc.add_page_break()

    doc.add_heading("Sign Off", level=1)
    sign = doc.add_table(rows=6, cols=4)
    sign.style = "Table Grid"
    sign_rows = [
        ["Organization", "Role", "Name / Signature", "Date"],
        ["Gosoft", "Reviewed By - Service Manager", "", ""],
        ["Gosoft", "Approved By - Project Manager", "", ""],
        ["Client", "Reviewed By", "", ""],
        ["Client", "Approved By", "", ""],
        ["Architecture/Operations", "Reviewed By", "", ""],
    ]
    for i, row in enumerate(sign_rows):
        for j, value in enumerate(row):
            sign.cell(i, j).text = value
    set_table_widths(sign, 9920, [0.22, 0.32, 0.28, 0.18])
    set_repeat_table_header(sign.rows[0])
    for ridx, row in enumerate(sign.rows):
        for cell in row.cells:
            set_cell_margins(cell, 120, 100, 240 if ridx else 100, 100)
            if ridx == 0:
                set_cell_shading(cell, "E7E7E7")
            for p in cell.paragraphs:
                for r in p.runs:
                    docx_set_font(r, size=11, bold=(ridx == 0))
    doc.add_page_break()

    doc.add_heading("Table of Contents", level=1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-4" \\h \\z \\u')
    doc.add_page_break()

    current_docx_num_id: int | None = None
    for block in model.blocks:
        if block.kind != "number":
            current_docx_num_id = None
        if block.kind == "heading":
            doc.add_heading(block.text, level=min(4, block.level))
        elif block.kind == "paragraph":
            p = doc.add_paragraph()
            if block.text in {"Request", "Response", "Errors", "Flow:"}:
                p.paragraph_format.keep_with_next = True
            r = p.add_run(block.text)
            docx_set_font(r, size=14)
        elif block.kind == "bullet":
            style = "List Bullet 2" if block.level else "List Bullet"
            p = doc.add_paragraph(style=style)
            r = p.add_run(block.text)
            docx_set_font(r, size=14)
        elif block.kind == "number":
            if current_docx_num_id is None:
                current_docx_num_id = new_docx_numbering_id(doc)
            p = doc.add_paragraph()
            apply_docx_numbering(p, current_docx_num_id)
            r = p.add_run(block.text)
            docx_set_font(r, size=14)
        elif block.kind == "note":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.45)
            p.paragraph_format.right_indent = Cm(0.15)
            set_paragraph_border(p, "left", "FF0000", 18, 4)
            r = p.add_run(block.text)
            docx_set_font(r, size=13.5)
            set_cell_shading  # keep linter quiet about helper locality
        elif block.kind == "code":
            table = doc.add_table(rows=1, cols=1)
            table.style = "Table Grid"
            set_table_widths(table, 9920, [1.0])
            cell = table.cell(0, 0)
            set_cell_shading(cell, "F2F2F2")
            set_cell_margins(cell, 100, 120, 100, 120)
            p = cell.paragraphs[0]
            for idx, line in enumerate(block.text.splitlines() or [""]):
                if idx:
                    p.add_run().add_break()
                r = p.add_run(line)
                docx_set_font(r, name="Arial", size=8.5)
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
        elif block.kind == "table":
            if not block.headers:
                continue
            cols = len(block.headers)
            table = doc.add_table(rows=1, cols=cols)
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for idx, header in enumerate(block.headers):
                table.cell(0, idx).text = header
            for row_data in block.rows:
                row = table.add_row()
                for idx in range(cols):
                    row.cells[idx].text = row_data[idx] if idx < len(row_data) else ""
            set_table_widths(table, 9920, block.widths)
            set_repeat_table_header(table.rows[0])
            for ridx, row in enumerate(table.rows):
                for cidx, cell in enumerate(row.cells):
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    set_cell_margins(cell)
                    if ridx == 0:
                        set_cell_shading(cell, "E7E7E7")
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(0)
                        for r in p.runs:
                            docx_set_font(r, size=10.5, bold=(ridx == 0))
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(1)
        elif block.kind == "image" and block.path and block.path.exists():
            with PILImage.open(block.path) as img:
                ratio = img.height / img.width
            width = Cm(17.0)
            height = min(Cm(19.5), width * ratio)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(block.path), width=width, height=height)
            if block.caption:
                cp = doc.add_paragraph()
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cp.add_run(block.caption)
                docx_set_font(r, size=11)
        elif block.kind == "pagebreak":
            doc.add_page_break()

    DOCX_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = "Software Requirement Specification - ระบบประกันรายได้ SBPGI"
    doc.core_properties.subject = "Integrated Flow, Database, Batch Job, K2 screens and API"
    doc.core_properties.author = "SBPGI Project Team"
    doc.core_properties.comments = "Generated from repository sources; open items require review."
    doc.save(DOCX_OUT)


PDF_FONT = "Tahoma"
PDF_FONT_BOLD = "Tahoma-Bold"
PDF_BODY = 9.0
PAGE_W, PAGE_H = A4
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 26 * mm
BOTTOM = 28 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT


def register_pdf_fonts():
    regular = Path("/System/Library/Fonts/Supplemental/Tahoma.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Tahoma Bold.ttf")
    fallback = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont(PDF_FONT, str(regular)))
        pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(bold)))
    elif fallback.exists():
        pdfmetrics.registerFont(TTFont(PDF_FONT, str(fallback)))
        pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(fallback)))
    else:
        raise RuntimeError("Thai-capable TrueType font not found")


def ptext(text: str) -> str:
    return html_lib.escape(clean(text)).replace("\n", "<br/>")


class SrsDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = self._make_frame()
        self.addPageTemplates([PageTemplate(id="SRS", frames=[frame], onPage=draw_pdf_furniture)])

    def _make_frame(self):
        from reportlab.platypus import Frame

        return Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="normal")

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            if style_name.startswith("Heading"):
                level = int(style_name.replace("Heading", "")) - 1
                text = flowable.getPlainText()
                key = f"h{self.seq.nextf('heading')}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=level, closed=False)
                self.notify("TOCEntry", (level, text, self.page, key))


def draw_pdf_furniture(canv: canvas.Canvas, doc):
    if doc.page == 1:
        return
    canv.saveState()
    if HEADER_LOGO.exists():
        canv.drawImage(str(HEADER_LOGO), LEFT, PAGE_H - 18 * mm, width=39 * mm, height=7.3 * mm, preserveAspectRatio=True, mask="auto")
    canv.setFont(PDF_FONT, 7.3)
    canv.setFillColor(colors.HexColor("#333333"))
    canv.drawRightString(PAGE_W - RIGHT, PAGE_H - 13.5 * mm, TEMPLATE_CODE)
    canv.setStrokeColor(colors.red)
    canv.setLineWidth(0.6)
    canv.line(LEFT, PAGE_H - 20.2 * mm, PAGE_W - RIGHT, PAGE_H - 20.2 * mm)

    y = 18.2 * mm
    canv.line(LEFT, y + 3.2 * mm, PAGE_W - RIGHT, y + 3.2 * mm)
    canv.setFont(PDF_FONT, 6.6)
    canv.setFillColor(colors.red)
    canv.drawString(LEFT, y, "Confidential - Restricted Circulation Only")
    canv.setFillColor(colors.HexColor("#2346FF"))
    canv.drawRightString(PAGE_W - RIGHT, y, TEMPLATE_CODE)
    canv.setFillColor(colors.HexColor("#444444"))
    canv.setFont(PDF_FONT, 6.3)
    canv.drawString(LEFT, y - 5.0 * mm, "© 2023 Gosoft (Thailand) Co., Ltd prepared for internal use only")
    canv.drawString(LEFT, y - 9.2 * mm, "Printed copies of this Document are not controlled and will not be updated.")
    canv.restoreState()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for page_num, state in enumerate(self._saved_page_states, 1):
            self.__dict__.update(state)
            if page_num > 1:
                self.setFont(PDF_FONT, 6.5)
                self.setFillColor(colors.HexColor("#444444"))
                self.drawRightString(PAGE_W - RIGHT, 9.0 * mm, f"Page {page_num} of {page_count}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def pdf_styles():
    styles = getSampleStyleSheet()
    common = dict(fontName=PDF_FONT, textColor=colors.black, wordWrap="CJK")
    out = {
        "Body": ParagraphStyle("Body", parent=styles["Normal"], fontSize=PDF_BODY, leading=12, spaceAfter=4, **common),
        "Bullet": ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=PDF_BODY, leading=12, leftIndent=12, firstLineIndent=-7, bulletIndent=0, spaceAfter=2.5, **common),
        "Number": ParagraphStyle("Number", parent=styles["Normal"], fontSize=PDF_BODY, leading=12, leftIndent=12, firstLineIndent=-7, spaceAfter=2.5, **common),
        "Note": ParagraphStyle("Note", parent=styles["Normal"], fontSize=8.6, leading=11.5, leftIndent=8, rightIndent=4, spaceBefore=4, spaceAfter=6, borderColor=colors.red, borderWidth=0.7, borderPadding=5, backColor=colors.HexColor("#FAFAFA"), **common),
        "Code": ParagraphStyle("Code", parent=styles["Code"], fontName=PDF_FONT, fontSize=6.7, leading=8.5, wordWrap="CJK", textColor=colors.HexColor("#222222")),
        "Heading1": ParagraphStyle("Heading1", parent=styles["Heading1"], fontName=PDF_FONT_BOLD, fontSize=13, leading=16, spaceBefore=9, spaceAfter=5, keepWithNext=True, wordWrap="CJK"),
        "Heading2": ParagraphStyle("Heading2", parent=styles["Heading2"], fontName=PDF_FONT_BOLD, fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=4, keepWithNext=True, wordWrap="CJK"),
        "Heading3": ParagraphStyle("Heading3", parent=styles["Heading3"], fontName=PDF_FONT_BOLD, fontSize=10.2, leading=13, spaceBefore=7, spaceAfter=3, keepWithNext=True, wordWrap="CJK"),
        "Heading4": ParagraphStyle("Heading4", parent=styles["Heading4"], fontName=PDF_FONT_BOLD, fontSize=9.4, leading=12, spaceBefore=5, spaceAfter=2.5, keepWithNext=True, wordWrap="CJK"),
        "Table": ParagraphStyle("Table", parent=styles["Normal"], fontName=PDF_FONT, fontSize=6.8, leading=8.6, wordWrap="CJK", textColor=colors.HexColor("#222222")),
        "TableHead": ParagraphStyle("TableHead", parent=styles["Normal"], fontName=PDF_FONT_BOLD, fontSize=7, leading=8.8, alignment=TA_CENTER, wordWrap="CJK"),
        "Small": ParagraphStyle("Small", parent=styles["Normal"], fontName=PDF_FONT, fontSize=7.4, leading=9.5, wordWrap="CJK"),
        "CoverTitle": ParagraphStyle("CoverTitle", parent=styles["Title"], fontName=PDF_FONT, fontSize=17, leading=21, alignment=TA_CENTER, spaceAfter=18),
        "CoverThai": ParagraphStyle("CoverThai", parent=styles["Title"], fontName=PDF_FONT_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=6),
        "CoverVersion": ParagraphStyle("CoverVersion", parent=styles["Title"], fontName=PDF_FONT, fontSize=13, leading=17, alignment=TA_CENTER, spaceAfter=30),
        "Center": ParagraphStyle("Center", parent=styles["Normal"], fontName=PDF_FONT, fontSize=9.5, leading=13, alignment=TA_CENTER, wordWrap="CJK"),
    }
    return out


def pdf_table(block: Block, st) -> LongTable:
    cols = len(block.headers)
    proportions = block.widths if block.widths and len(block.widths) == cols else [1 / cols] * cols
    total = sum(proportions)
    widths = [CONTENT_W * x / total for x in proportions]
    data = [[Paragraph(ptext(h), st["TableHead"]) for h in block.headers]]
    for row in block.rows:
        data.append([Paragraph(ptext(row[i] if i < len(row) else ""), st["Table"]) for i in range(cols)])
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7E7E7")),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
            ]
        )
    )
    return table


def build_pdf(model: Model):
    register_pdf_fonts()
    st = pdf_styles()
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SrsDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Software Requirement Specification - ระบบประกันรายได้ SBPGI",
        author="SBPGI Project Team",
        subject="Integrated Flow, Database, Batch Job, K2 screens and API",
    )
    story: list[Flowable] = []

    # Cover
    story.extend([Spacer(1, 39 * mm), Paragraph("SOFTWARE REQUIREMENT SPECIFICATION", st["CoverTitle"])])
    story.append(Paragraph("ระบบประกันรายได้ SBPGI", st["CoverThai"]))
    story.append(Paragraph(f"VERSION {DOC_VERSION.upper()}", st["CoverVersion"]))
    if COVER_BADGE.exists():
        story.append(Image(str(COVER_BADGE), width=48 * mm, height=49 * mm, hAlign="CENTER"))
    story.append(Spacer(1, 37 * mm))
    for line in [
        "Gosoft (Thailand) CO.,LTD.",
        "313 CP Tower, 24th Fl., Silom Road",
        "Bangrak, Bangkok 10500.",
        "Website: www.gosoft.co.th",
    ]:
        story.append(Paragraph(line, st["Center"]))
    story.append(PageBreak())

    story.append(Paragraph("Document Version History", st["Heading1"]))
    version_block = Block(
        "table",
        headers=["Version Number", "Release Date", "Created By", "Detail", "Reviewed by", "Authorized by"],
        rows=[
            [
                "3.2 Draft",
                RELEASE_DATE,
                "SBPGI Project Team",
                "Consolidate Flow, Database, Batch Job, K2 screens and API with full figures",
                "",
                "",
            ]
        ],
        widths=[0.11, 0.12, 0.15, 0.34, 0.14, 0.14],
    )
    story.append(pdf_table(version_block, st))
    story.append(PageBreak())

    story.append(Paragraph("Sign Off", st["Heading1"]))
    sign_block = Block(
        "table",
        headers=["Organization", "Role", "Name / Signature", "Date"],
        rows=[
            ["Gosoft", "Reviewed By - Service Manager", "", ""],
            ["Gosoft", "Approved By - Project Manager", "", ""],
            ["Client", "Reviewed By", "", ""],
            ["Client", "Approved By", "", ""],
            ["Architecture/Operations", "Reviewed By", "", ""],
        ],
        widths=[0.22, 0.32, 0.28, 0.18],
    )
    story.append(pdf_table(sign_block, st))
    story.append(PageBreak())

    story.append(Paragraph("Table of Contents", st["Heading1"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(name="TOC1", fontName=PDF_FONT, fontSize=9, leading=13, leftIndent=0, firstLineIndent=0),
        ParagraphStyle(name="TOC2", fontName=PDF_FONT, fontSize=8.5, leading=12, leftIndent=12, firstLineIndent=0),
        ParagraphStyle(name="TOC3", fontName=PDF_FONT, fontSize=8, leading=11, leftIndent=24, firstLineIndent=0),
        ParagraphStyle(name="TOC4", fontName=PDF_FONT, fontSize=7.5, leading=10, leftIndent=36, firstLineIndent=0),
    ]
    story.append(toc)
    story.append(PageBreak())

    pending_code_label: str | None = None
    pdf_number_counter = 0
    for block in model.blocks:
        if block.kind != "number":
            pdf_number_counter = 0
        if pending_code_label is not None and block.kind != "code":
            story.append(Paragraph(ptext(pending_code_label), st["Body"]))
            pending_code_label = None
        if block.kind == "heading":
            story.append(Paragraph(ptext(block.text), st[f"Heading{min(4, block.level)}"]))
        elif block.kind == "paragraph":
            if block.text in {"Request", "Response"}:
                pending_code_label = block.text
            else:
                story.append(Paragraph(ptext(block.text), st["Body"]))
        elif block.kind == "bullet":
            story.append(Paragraph(ptext(block.text), st["Bullet"], bulletText="•"))
        elif block.kind == "number":
            pdf_number_counter += 1
            story.append(Paragraph(ptext(f"{pdf_number_counter}. {block.text}"), st["Number"], bulletText=""))
        elif block.kind == "note":
            story.append(Paragraph(ptext(block.text), st["Note"]))
        elif block.kind == "code":
            lines = []
            for line in block.text.splitlines() or [""]:
                wrapped = textwrap.wrap(line, width=100, replace_whitespace=False, drop_whitespace=False) or [""]
                lines.extend(wrapped)
            code_para = Paragraph("<br/>".join(html_lib.escape(line) for line in lines), st["Code"])
            code_table = Table([[code_para]], colWidths=[CONTENT_W])
            code_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
                        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#888888")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            code_items: list[Flowable] = []
            if pending_code_label is not None:
                code_items.append(Paragraph(ptext(pending_code_label), st["Body"]))
                pending_code_label = None
            code_items.extend([code_table, Spacer(1, 4)])
            story.append(KeepTogether(code_items))
        elif block.kind == "table":
            story.extend([pdf_table(block, st), Spacer(1, 5)])
        elif block.kind == "image" and block.path and block.path.exists():
            with PILImage.open(block.path) as img:
                ratio = img.height / img.width
            width = CONTENT_W
            height = min(175 * mm, width * ratio)
            story.append(Image(str(block.path), width=width, height=height, hAlign="CENTER"))
            if block.caption:
                story.append(Paragraph(ptext(block.caption), st["Center"]))
        elif block.kind == "pagebreak":
            story.append(PageBreak())
    if pending_code_label is not None:
        story.append(Paragraph(ptext(pending_code_label), st["Body"]))
    doc.multiBuild(story, canvasmaker=NumberedCanvas)


def main():
    if not DATA_FILE.exists():
        raise SystemExit(f"Missing {DATA_FILE}; run: node tmp/extract_js_data.mjs")
    if not HEADER_LOGO.exists() or not COVER_BADGE.exists():
        raise SystemExit("Missing extracted PDF template images; run pdfimages first")
    OUT.mkdir(parents=True, exist_ok=True)
    model = build_model()
    make_md(model)
    build_docx(model)
    build_pdf(model)
    print(DOCX_OUT)
    print(PDF_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
