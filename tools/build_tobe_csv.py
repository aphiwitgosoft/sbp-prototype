#!/usr/bin/env python3
"""ตาราง CSV ของงาน To-Be — "SDD สไลด์ไหน · ข้อไหน · ทำอะไร · ใครทำกี่ชั่วโมง · รวมกี่ชั่วโมง"

ผลลัพธ์ -> output/tobe-work.csv   (1 แถว = 1 ข้อที่ SDD สั่ง)

กติกา (มติ 2026-08-25)
  * นับ **เฉพาะงานที่ To-Be เพิ่มเข้ามาใหม่** — งานฐานราก (TB-0) ไม่อยู่ในไฟล์นี้
  * นับ **เฉพาะสาย FE และ BE** — งาน batch job ไม่ใช่งานหน้าจอ/API ที่ To-Be สั่งใหม่
    (ชั่วโมง job ที่กันออกสรุปไว้ท้ายไฟล์ ไม่ตัดทิ้งเงียบ ๆ)

วิธีคิดชั่วโมงต่อข้อ
  ชั่วโมงจริงประกาศไว้ที่ระดับ **เอกสาร LLDD** (implementation + unit test) ไม่ได้แตกเป็นรายข้อ
  ไฟล์นี้จึงกระจายชั่วโมงของเอกสารลงข้อที่เอกสารนั้นรับผิดชอบ **แบ่งเท่ากัน**
  ผลรวมทุกข้อของแต่ละ TB จึงเท่ากับชั่วโมงจริงของ TB นั้นเสมอ (ข้อสุดท้ายรับเศษ)
  -> ตัวเลขรายข้อเป็น "ค่าประมาณเพื่อวางแผน" ส่วนตัวเลขที่ผูกสัญญาคือยอดรวมของ TB
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_lldd_documents as B  # noqa: E402

# ---------------------------------------------------------------------------
# ข้อที่ SDD สั่ง -> เอกสาร LLDD ที่ลงมือทำข้อนั้น
# (ดุลพินิจของผู้ออกแบบ · แก้ที่นี่ที่เดียวแล้วตัวเลขรายข้อขยับตาม)
# key = (รหัส To-Be, ลำดับข้อ)
# ---------------------------------------------------------------------------
BULLET_DOCS: dict[tuple[str, int], list[str]] = {
    # ---- TB-1 · สไลด์ 43 · 46-51 ----
    ("TB-1", 1): ["LLDD-FE-Document-Lists", "LLDD-BE-API-Document-List-Search"],
    ("TB-1", 2): ["LLDD-FE-Document-Detail", "LLDD-BE-API-Document-Create-Update",
                  "LLDD-BE-API-Attachment-Sales-Timeline"],
    ("TB-1", 3): ["LLDD-FE-Document-Detail", "LLDD-BE-API-Document-Workflow-Actions"],
    ("TB-1", 4): ["LLDD-BE-API-Document-Create-Update", "LLDD-BE-API-Workflow-Instances",
                  "LLDD-FE-Document-Lists"],
    ("TB-1", 5): ["LLDD-BE-API-Workflow-Instances", "LLDD-BE-API-Document-List-Search"],
    ("TB-1", 6): ["LLDD-FE-Document-Lists", "LLDD-BE-API-Document-List-Search",
                  "LLDD-FE-Document-Detail"],
    ("TB-1", 7): ["LLDD-BE-API-Document-Create-Update"],
    ("TB-1", 8): ["LLDD-FE-Document-Detail", "LLDD-BE-API-Document-Detail-Aggregate"],
    ("TB-1", 9): ["LLDD-BE-API-Document-Workflow-Actions", "LLDD-FE-Create-Document"],
    ("TB-1", 10): ["LLDD-BE-API-Document-Detail-Aggregate",
                   "LLDD-BE-API-Attachment-Sales-Timeline"],
    # ---- TB-2 · สไลด์ 52-58 ----
    ("TB-2", 1): ["LLDD-BE-Workflow-Engine-Definition", "LLDD-BE-API-Workflow-Instances"],
    ("TB-2", 2): ["LLDD-FE-Document-Detail", "LLDD-BE-API-Lookup"],
    ("TB-2", 3): ["LLDD-BE-Workflow-Engine-Definition", "LLDD-BE-Integration-SBP-Platform"],
    ("TB-2", 4): ["LLDD-BE-Integration-SBP-Platform", "LLDD-BE-API-Lookup"],
    ("TB-2", 5): ["LLDD-BE-API-Document-Workflow-Actions", "LLDD-BE-API-Workflow-Instances"],
    ("TB-2", 6): ["LLDD-BE-API-Document-Workflow-Actions", "LLDD-FE-Document-Detail"],
    # ---- TB-3 · สไลด์ 59-62 ----
    ("TB-3", 1): ["LLDD-BE-API-Report-and-Master-Data"],
    ("TB-3", 2): ["LLDD-FE-Report", "LLDD-BE-API-Report-and-Master-Data"],
    ("TB-3", 3): ["LLDD-FE-Report", "LLDD-BE-API-Report-and-Master-Data"],
    ("TB-3", 4): ["LLDD-FE-Report", "LLDD-BE-API-Report-and-Master-Data"],
}


FIELDS = ["SDD สไลด์", "ข้อ", "ทำอะไร", "ใครทำ / กี่ชั่วโมง", "รวม (ชม.)", "เอกสาร LLDD"]


def short_owner(owner: str) -> str:
    if "<" in owner and ">" in owner:
        return owner.split("<", 1)[1].split(">", 1)[0]
    return owner.split()[0]


def plain(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    topics = {t.file.rsplit("/", 1)[-1]: t for t in B.topics()}
    meta = {c: (title, slides, bullets) for c, title, slides, bullets in B.TOBE_ITEMS}
    codes = [c for c, *_ in B.TOBE_ITEMS if c != "TB-0"]

    # ---- ชั่วโมงของแต่ละเอกสารในแต่ละ TB (เฉพาะ FE/BE) ----
    doc_hours: dict[tuple[str, str], int] = {}
    job_hours = 0
    job_docs: set[str] = set()
    for key, topic in topics.items():
        if B.is_document_detail_role_doc(topic.file):
            continue
        for code, (imp, ut) in B.tobe_split(topic).items():
            if code not in codes or imp + ut == 0:
                continue
            if B.is_job_doc(topic.file):
                job_hours += imp + ut
                job_docs.add(key)
            else:
                doc_hours[(code, key)] = imp + ut

    # ---- ตรวจว่า mapping ครอบคลุมทุกเอกสาร/ทุกข้อ ----
    for code in codes:
        n = len(meta[code][2])
        for i in range(1, n + 1):
            if (code, i) not in BULLET_DOCS:
                raise SystemExit(f"BULLET_DOCS ขาด {code} ข้อ {i}")
        mapped = {d for (c, _), docs in BULLET_DOCS.items() if c == code for d in docs}
        have = {k for (c, k) in doc_hours if c == code}
        if mapped - have:
            raise SystemExit(f"{code}: mapping อ้างเอกสารที่ไม่มีชั่วโมงใน TB นี้ {sorted(mapped - have)}")
        if have - mapped:
            raise SystemExit(f"{code}: เอกสารที่ยังไม่ถูก map เข้าข้อไหนเลย {sorted(have - mapped)}")

    rows: list[dict[str, object]] = []
    for code in codes:
        title, slides, bullets = meta[code]
        # จำนวนข้อที่เอกสารแต่ละฉบับรับผิดชอบใน TB นี้
        span: dict[str, int] = defaultdict(int)
        for (c, i), docs in BULLET_DOCS.items():
            if c == code:
                for d in docs:
                    span[d] += 1
        # กระจายชั่วโมงแบบแบ่งเท่า · เอกสารละข้อสุดท้ายรับเศษ
        left = {d: doc_hours[(code, d)] for d in span}
        done: dict[str, int] = defaultdict(int)
        per_bullet: list[dict[str, int]] = []
        for i in range(1, len(bullets) + 1):
            alloc: dict[str, int] = {}
            for d in BULLET_DOCS[(code, i)]:
                done[d] += 1
                if done[d] == span[d]:          # ข้อสุดท้ายของเอกสารนี้ -> รับเศษ
                    alloc[d] = left[d]
                    left[d] = 0
                else:
                    h = round(doc_hours[(code, d)] / span[d])
                    h = min(h, left[d])
                    alloc[d] = h
                    left[d] -= h
            per_bullet.append(alloc)

        for i, (bullet, alloc) in enumerate(zip(bullets, per_bullet), start=1):
            by_owner: dict[tuple[str, str], int] = defaultdict(int)
            for d, h in alloc.items():
                if not h:
                    continue
                t = topics[d]
                by_owner[("FE" if t.track == "FE" else "BE", short_owner(t.owner))] += h
            parts = [f"{tr}({ow}) {h} ชม."
                     for (tr, ow), h in sorted(by_owner.items(), key=lambda kv: (kv[0][0], -kv[1]))]
            total = sum(by_owner.values())
            rows.append({
                "SDD สไลด์": slides,
                "ข้อ": f"{code}.{i}",
                "ทำอะไร": plain(bullet),
                "ใครทำ / กี่ชั่วโมง": "  ".join(parts),
                "รวม (ชม.)": total,
                "เอกสาร LLDD": " · ".join(sorted(d for d, h in alloc.items() if h)),
            })

        fe = sum(h for d, h in doc_hours.items() if d[0] == code and topics[d[1]].track == "FE")
        be = sum(doc_hours[(code, d)] for d in span if topics[d].track != "FE")
        rows.append({
            "SDD สไลด์": slides, "ข้อ": f"{code} รวม", "ทำอะไร": title,
            "ใครทำ / กี่ชั่วโมง": f"FE {fe} ชม.  BE {be} ชม.",
            "รวม (ชม.)": fe + be, "เอกสาร LLDD": "",
        })

    fe_all = sum(h for (c, d), h in doc_hours.items() if topics[d].track == "FE")
    be_all = sum(h for (c, d), h in doc_hours.items() if topics[d].track != "FE")
    rows.append({
        "SDD สไลด์": "", "ข้อ": "รวมทั้งหมด", "ทำอะไร": "งานที่ To-Be เพิ่ม (เฉพาะ FE + BE)",
        "ใครทำ / กี่ชั่วโมง": f"FE {fe_all} ชม.  BE {be_all} ชม.",
        "รวม (ชม.)": fe_all + be_all, "เอกสาร LLDD": "",
    })

    # ---- ตารางที่ 2 (แยกจากตารางบน) · รวมแล้วใครทำกี่ชั่วโมง ----
    per_owner: dict[tuple[str, str], int] = defaultdict(int)
    for (code, doc), h in doc_hours.items():
        t = topics[doc]
        per_owner[("FE" if t.track == "FE" else "BE", short_owner(t.owner))] += h

    rows.append({f: "" for f in FIELDS})
    rows.append({"SDD สไลด์": "ตารางที่ 2", "ข้อ": "รวมแล้วใครทำ",
                 "ทำอะไร": "ภาระงาน To-Be ต่อคน (เฉพาะงานที่ To-Be เพิ่ม · FE + BE)",
                 "ใครทำ / กี่ชั่วโมง": "", "รวม (ชม.)": "", "เอกสาร LLDD": ""})
    for (track, owner), hrs in sorted(per_owner.items(), key=lambda kv: (-kv[1], kv[0][0])):
        docs = sorted({d for (c, d) in doc_hours
                       if short_owner(topics[d].owner) == owner
                       and ("FE" if topics[d].track == "FE" else "BE") == track})
        rows.append({
            "SDD สไลด์": "", "ข้อ": owner, "ทำอะไร": f"สาย {track}",
            "ใครทำ / กี่ชั่วโมง": f"{track}({owner}) {hrs} ชม.",
            "รวม (ชม.)": hrs, "เอกสาร LLDD": " · ".join(docs),
        })
    rows.append({
        "SDD สไลด์": "", "ข้อ": "รวม", "ทำอะไร": "ทุกคนรวมกัน",
        "ใครทำ / กี่ชั่วโมง": f"FE {fe_all} ชม.  BE {be_all} ชม.",
        "รวม (ชม.)": fe_all + be_all, "เอกสาร LLDD": "",
    })

    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    path = out / "tobe-work.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    n_items = sum(len(meta[c][2]) for c in codes)
    print(f"{path.relative_to(ROOT)} · {n_items} ข้อที่ SDD สั่ง + แถวสรุป · "
          f"FE {fe_all} + BE {be_all} = {fe_all + be_all} ชม. (กัน job ออก {job_hours} ชม.)")


if __name__ == "__main__":
    main()
