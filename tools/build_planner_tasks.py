#!/usr/bin/env python3
"""สร้างข้อมูลการ์ด Microsoft Planner จากชุดข้อมูลเดียวกับ LLDD / worklist

ผลลัพธ์ -> output/planner-tasks.csv  (นำเข้า/คีย์ตามได้)
           output/planner-tasks.txt  (อ่านง่ายตอนคีย์มือในหน้าเว็บ Planner)

กติกา label (มติ 2026-08-25):
  * `Step 1` .. `Step 6`            ลำดับการทำตาม dependency
  * `BE` `FE` `JOBS`                สาย/ทีมที่ลงมือ
  * `API` `DATABASE` `WORKFLOW` `BFF` ประเภทงานที่อยู่ในการ์ด
  * `8-15 hrs.` `16-30 hrs.` `31+ hrs.` ขนาดงาน
Planner รองรับ label ได้ 25 ป้ายต่อแผน — ชุดนี้ใช้ 16 ป้าย

checklist ของการ์ดมาจาก track และจะ **เพิ่มข้อ trigger event ให้อัตโนมัติ**
เมื่อเอกสาร LLDD ของงานนั้นระบุว่าต้องเรียก @srm/glb-workflow
(อ่านจาก WORKFLOW_TRIGGER_CONTRACTS ใน build_lldd_documents.py — แหล่งเดียวกัน)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_lldd_documents as B  # noqa: E402

# path จริงบน SharePoint (ยืนยันแล้วจากการเปิดไฟล์ 2026-08-24) — ส่วนภาษาไทย percent-encode ไว้
SHAREPOINT_BASE = (
    "https://cpallgroup.sharepoint.com/sites/"
    "MST-GO0666ITHW2025ReplaceSBPManagementSystem/Shared%20Documents/General/"
    "04-Analysis%20%26%20Design/LLDD/Non-Baseline/"
    "Phase%204%20%5BSBP%20Operating%20Management%20"
    "%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B8%A3%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%94%E0%B9%89"
    "%2C%20Contract%20Management%20%28"
    "%E0%B8%A3%E0%B9%89%E0%B8%B2%E0%B8%99%E0%B8%9E%E0%B8%A3%E0%B9%89%E0%B8%AD%E0%B8%A1%E0%B9%82%E0%B8%AD%E0%B8%99"
    "%29%5D/SBP%20Operating%20Management%20"
    "%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B8%A3%E0%B8%B2%E0%B8%A2%E0%B9%84%E0%B8%94%E0%B9%89"
)

BFF_DOCS = {"LLDD-FE-Integration-Contracts", "LLDD-BE-Integration-SBP-Platform"}
DATABASE_DOCS = {"LLDD-BE-Database-Structure", "LLDD-BE-Data-Migration-Cutover"}

CHECKLISTS = {
    "BE": [
        "controller + DTO/validation",
        "service + SQL ตาม DB Mapping",
        "error/response envelope",
        "unit test ตามขอบเขตใน LLDD",
    ],
    "FE": [
        "ทำ form/UI ตาม LLDD",
        "ต่อ API + state",
        "validate + error state",
        "unit test ตามขอบเขตใน LLDD",
    ],
    "DB": [
        "เขียน DDL / migration script",
        "ตรวจ constraint + index + FK",
        "rollback / rerun script",
        "unit test ตามขอบเขตใน LLDD",
    ],
    "Job": [
        "อ่านสเปก LLDD + ตั้ง config/env",
        "เขียน runner + SQL ตามลำดับขั้น",
        "idempotency + rerun/rollback",
        "unit test ตามขอบเขตใน LLDD",
    ],
}

# ข้อ checklist เพิ่มเมื่อเอกสารระบุว่าต้องเรียก workflow engine
WORKFLOW_CHECK_ITEM = "trigger event: เรียก engine ตามหัวข้อ Workflow Trigger Event Contract + mock ใน unit test"


def card_title(title: str) -> str:
    """'LLDD BE - Database Structure and Deployment' -> 'Database Structure and Deployment'"""
    for prefix in ("LLDD BE - ", "LLDD FE - ", "LLDD - "):
        if title.startswith(prefix):
            return title[len(prefix):]
    return title


def short_owner(owner: str) -> str:
    """'Aphiwit <Bank> Khammoon' -> 'Bank'"""
    if "<" in owner and ">" in owner:
        return owner.split("<", 1)[1].split(">", 1)[0]
    return owner.split()[0]


# ป้ายชั่วโมงต้องอ่านเป็นตัวเลขเสมอ — role pack ก็มีชั่วโมงจริงของตัวเอง (13 ชม.)
# เพียงแต่ยอดรวมไปนับที่ [FE] Document Detail and Action จึงไม่บวกซ้ำในคอลัมน์ Hours
def size_label(hours: int) -> str:
    if hours <= 15:
        return "8-15 hrs."
    if hours <= 30:
        return "16-30 hrs."
    return "31+ hrs."


def calls_workflow(doc_key: str) -> bool:
    rows = B.WORKFLOW_TRIGGER_CONTRACTS.get(doc_key)
    if not rows:
        return False
    return any(not row[1].lstrip("`").startswith("ไม่เรียก") for row in rows)


def track_labels(topic: "B.Topic", doc_key: str) -> list[str]:
    labels: list[str] = []
    if topic.track == "FE":
        labels.append("FE")
    elif B.is_job_doc(topic.file):
        labels.append("JOBS")
    else:
        labels.append("BE")
    if "-API-" in doc_key:
        labels.append("API")
    if doc_key in DATABASE_DOCS:
        labels.append("DATABASE")
    if calls_workflow(doc_key) or "Workflow" in doc_key:
        labels.append("WORKFLOW")
    if doc_key in BFF_DOCS:
        labels.append("BFF")
    return labels


def main() -> None:
    all_topics = B.topics()
    steps = B.dependency_steps(all_topics)
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    rows = []
    for topic in all_topics:
        doc_key = topic.file.rsplit("/", 1)[-1]
        # role pack 5 ฉบับนับชั่วโมงรวมไว้ใน [FE] Document Detail and Action แล้ว
        # (ตรงกับ billable ใน build_lldd_documents.py) — การ์ดยังต้องมี แต่ไม่นับชั่วโมงซ้ำ
        included = B.is_document_detail_role_doc(topic.file)
        hours = 0 if included else B.total_hours(topic)
        step = steps.get(topic.file, 1)
        track = "Job" if B.is_job_doc(topic.file) else topic.track
        labels = [f"Step {step}"] + track_labels(topic, doc_key)
        # ป้ายใช้ชั่วโมงจริงของเอกสารเสมอ (ไม่ใช่ 0 ของ role pack) จะได้เป็นตัวเลขที่ถูกต้อง
        labels.append(size_label(B.total_hours(topic)))
        checklist = list(CHECKLISTS["DB" if doc_key in DATABASE_DOCS else track])
        if calls_workflow(doc_key):
            checklist.insert(-1, WORKFLOW_CHECK_ITEM)
        rows.append({
            "Bucket": "To do",
            "Task name": f"[{track}] {card_title(topic.title)}",
            "Assigned to": short_owner(topic.owner),
            "Hours": f"{B.total_hours(topic)} (incl.)" if included else hours,
            "Step": step,
            "Track": track,
            "Labels": " | ".join(labels),
            "Checklist": " | ".join(checklist),
            "LLDD link": f"{SHAREPOINT_BASE}/{topic.file}.pdf",
        })

    rows.sort(key=lambda r: (r["Step"], r["Track"], r["Task name"]))

    csv_path = out_dir / "planner-tasks.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    txt_path = out_dir / "planner-tasks.txt"
    used_labels: list[str] = []
    for row in rows:
        for label in row["Labels"].split(" | "):
            if label not in used_labels:
                used_labels.append(label)
    with txt_path.open("w", encoding="utf-8") as fh:
        fh.write(f"Planner · SBP Mall · {len(rows)} การ์ด\n")
        fh.write(f"ป้ายที่ใช้ทั้งหมด {len(used_labels)} ป้าย (Planner จำกัด 25): "
                 + ", ".join(used_labels) + "\n\n")
        for index, row in enumerate(rows, start=1):
            fh.write(f"{index:>2}. {row['Task name']}\n")
            hrs = row["Hours"]
            hrs_txt = (
                f"{hrs.split()[0]} \u0e0a\u0e21. (\u0e23\u0e27\u0e21\u0e43\u0e19 [FE] Document Detail and Action)"
                if isinstance(hrs, str) and hrs.endswith("(incl.)")
                else f"{hrs} \u0e0a\u0e21."
            )
            fh.write(f"    ผู้รับผิดชอบ : {row['Assigned to']} · {hrs_txt}\n")
            fh.write(f"    Labels      : {row['Labels']}\n")
            fh.write("    Checklist   :\n")
            for item in row["Checklist"].split(" | "):
                fh.write(f"       - {item}\n")
            fh.write(f"    LLDD        : {row['LLDD link']}\n\n")

    wf = sum(1 for r in rows if "WORKFLOW" in r["Labels"])
    total = sum(r["Hours"] for r in rows if isinstance(r["Hours"], int))
    print(f"{csv_path.relative_to(ROOT)} · {len(rows)} การ์ด · รวม {total} ชม. · "
          f"{len(used_labels)} ป้าย · {wf} การ์ดติดป้าย WORKFLOW (มี checklist trigger event)")


if __name__ == "__main__":
    main()
