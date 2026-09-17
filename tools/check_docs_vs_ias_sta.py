#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตรวจข้ออ้างในเอกสาร (md · html · LLDD) กับ **ไฟล์ interface จริง** ของทีม IAS และ STA

    python3 tools/check_docs_vs_ias_sta.py

ต่างจาก `check_docs.py` ตรงที่ **ความจริงมาจากไบต์ในไฟล์จริง ไม่ใช่จากสเปก**
คู่กับ `check_docs_vs_db.py` ที่ตรวจกับฐานข้อมูลจริง

⚠️ ไฟล์ตัวอย่างอยู่ใน `docs/file_IAS_STA/` ซึ่ง **อยู่ใน .gitignore** (มีข้อมูลธุรกิจจริง)
   ถ้าไม่มีโฟลเดอร์ สคริปต์จะข้ามทุกข้อแล้วจบด้วย exit 0 — ไม่ถือว่าเอกสารผิด

สิ่งที่ตรวจ
  1. จำนวนฟิลด์ของแต่ละไฟล์ ตรงกับที่เอกสารประกาศไหม
  2. ปฏิทินของไฟล์ IAS — เอกสารห้ามบอกว่าเป็น พ.ศ. (ของจริงเป็น ค.ศ.)
  3. รูปแบบวันที่ฟิลด์ 3 ของ FRBC0001 — ห้ามเขียน `ddMMyyyy` (ของจริงมีสแลช)
  4. ลำดับหมวด QSSI 6 ค่า ต้องเป็น 8,9,12,1,10,16 ทุกที่ที่อ้าง
  5. สัญญา JSON ของ STA (`sgi_impact_store`) ต้องมีคีย์ครบและเรียงตรงกับฟิลด์ในไฟล์จริง
  6. โครงหน้าต่างยอดขาย — 4 หน้าต่าง × 15 วัน = 60 วัน และ **ไม่รวมวันที่ร้านใหม่เปิด**
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "docs" / "file_IAS_STA"
KNOWLEDGE = "docs/IAS-STA-interface-files.md"

# หมวด QSSI ตามลำดับฟิลด์ 9–14 ของ FRBC0001 (ชื่อถอดจากรายงาน RT040035 ของ STA 2026-09-16)
QSSI_ORDER = ["8", "9", "12", "1", "10", "16"]

# คีย์ของข้อความ sgi_impact_store ตามลำดับฟิลด์ในไฟล์ FRBC0001
STA_KEYS = ["storecode_i", "storecode_n", "opendate_n", "count_storecode_n",
            "compensate_year_month", "stmt_year_month", "compensate_comment",
            "compensate_status", "qssi1_score", "qssi2_score", "qssi3_score",
            "qssi4_score", "qssi5_score", "qssi6_score"]

# `SBP/` เป็นไฟล์วิเคราะห์ระบบเดิม อ่านอย่างเดียว และพูดคนละบริบท (เช่น ไล่ค่า category ในฐาน
# แบบเรียงเลข ไม่ใช่ลำดับฟิลด์ของ FRBC0001) — สแกนแล้วได้แต่ false positive
SKIP_DIRS = ("output/legacy-oracle", "output/legacy-sgi", "batchjob/fcsJar",
             "SBP/", "node_modules", ".git", "LLDD/word", "LLDD/pdf")

# บรรทัดที่กำลัง *อธิบายความไม่ตรงกัน* ไม่ใช่กำลังอ้างผิด — ข้ามไป
EXPLAINING = ("ไฟล์จริง", "2.39", "แต่ไฟล์", "ของจริง")


def doc_files() -> list[Path]:
    out = []
    for ext in ("*.md", "*.html"):
        for p in ROOT.rglob(ext):
            rel = str(p.relative_to(ROOT))
            if any(rel.startswith(d) or f"/{d}" in rel for d in SKIP_DIRS):
                continue
            out.append(p)
    return sorted(out)


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


# --------------------------------------------------------------- ความจริงจากไฟล์
def load_truth() -> dict | None:
    if not SAMPLES.is_dir():
        return None
    o = sorted(SAMPLES.glob("AMS06001O_*.txt"))
    i = sorted(SAMPLES.glob("AMS06001I_*.txt"))
    f = sorted(SAMPLES.glob("FRBC0001_*.txt"))
    if not (o and i and f):
        return None

    def rows(paths, enc):
        out = []
        for p in paths:
            for line in p.read_text(encoding=enc).split("\n"):
                if line.strip():
                    out.append(line.split("|"))
        return out

    ro, ri, rf = rows(o, "utf-8"), rows(i, "cp874"), rows(f, "cp874")
    t = {
        "AMS06001O": {"fields": Counter(len(r) for r in ro), "rows": len(ro), "files": len(o)},
        "AMS06001I": {"fields": Counter(len(r) for r in ri), "rows": len(ri), "files": len(i)},
        "FRBC0001": {"fields": Counter(len(r) for r in rf), "rows": len(rf), "files": len(f)},
    }
    # ปฏิทิน: ไฟล์ IAS ใช้ปีอะไร (ดูจากฟิลด์วันที่ 8 หลัก)
    t["ias_years"] = sorted({r[1][:4] for r in ro} | {r[2][:4] for r in ri})
    # ไฟล์ IAS มีไบต์ไทยไหม
    t["ias_non_ascii"] = sum(
        sum(1 for b in p.read_bytes() if b > 0x7F) for p in list(o) + list(i))
    # รูปแบบวันที่ฟิลด์ 3 ของ FRBC0001
    t["frbc_date_samples"] = sorted({r[2] for r in rf})[:3]
    t["frbc_has_slash"] = all("/" in r[2] for r in rf)
    # โครงหน้าต่างยอดขาย: นับแถวต่อ (ร้าน, วันเปิด) และช่วงวันที่
    per: dict[tuple[str, str], list[str]] = {}
    for r in ri:
        per.setdefault((r[0], r[1]), []).append(r[2])
    t["window_groups"] = per
    return t


def window_shape(dates: list[str], open_ymd: str) -> tuple[int, list[int], bool]:
    """คืน (จำนวนวัน, ขนาดของแต่ละช่วงต่อเนื่อง, วันเปิดอยู่ในชุดหรือไม่)"""
    d = sorted(dt.date(int(x[:4]), int(x[4:6]), int(x[6:8])) for x in dates)
    od = dt.date(int(open_ymd[:4]), int(open_ymd[4:6]), int(open_ymd[6:8]))
    groups, cur = [], [d[0]]
    for x in d[1:]:
        if (x - cur[-1]).days == 1:
            cur.append(x)
        else:
            groups.append(cur); cur = [x]
    groups.append(cur)
    contains_open = od in d or od.replace(year=od.year - 1) in d
    return len(d), [len(g) for g in groups], contains_open


# --------------------------------------------------------------- รายงานผล
FINDINGS: dict[str, list[str]] = {}
WARNINGS: dict[str, list[str]] = {}


def check(name: str, problems: list[str]) -> None:
    FINDINGS[name] = sorted(set(problems))


def warn(name: str, problems: list[str]) -> None:
    """เรื่องที่รู้แล้วแต่แก้เองไม่ได้ (เอกสารต้นฉบับของทีมอื่น) — รายงานแต่ไม่ทำให้ exit 1"""
    WARNINGS[name] = sorted(set(problems))


def main() -> int:
    truth = load_truth()
    if truth is None:
        print(f"ℹ️  ไม่พบไฟล์ตัวอย่างใน {SAMPLES.relative_to(ROOT)} — ข้ามการตรวจทั้งหมด")
        print("   (โฟลเดอร์นี้อยู่ใน .gitignore เพราะมีข้อมูลธุรกิจจริง · ขอจากทีมที่ถือไฟล์)")
        return 0

    docs = [(str(p.relative_to(ROOT)), read(p)) for p in doc_files()]
    print(f"ไฟล์ตัวอย่าง: AMS06001O {truth['AMS06001O']['files']} ไฟล์ · "
          f"AMS06001I {truth['AMS06001I']['files']} ไฟล์ · FRBC0001 {truth['FRBC0001']['files']} ไฟล์")
    print(f"ตรวจเอกสาร {len(docs)} ไฟล์\n")

    # ---- 1. จำนวนฟิลด์
    bad = []
    for fname in ("AMS06001O", "AMS06001I", "FRBC0001"):
        counts = truth[fname]["fields"]
        if len(counts) != 1:
            bad.append(f"{fname} :: ไฟล์จริงมีจำนวนฟิลด์ไม่คงที่ {dict(counts)} — ตรวจไฟล์ก่อน")
            continue
        real = next(iter(counts))
        for rel, txt in docs:
            if rel == KNOWLEDGE:
                continue
            for line in txt.split("\n"):
                if fname not in line or any(w in line for w in EXPLAINING):
                    continue
                # ดูเฉพาะ 90 ตัวอักษรถัดจากชื่อไฟล์ — ไกลกว่านั้นมักเป็นเลขของเรื่องอื่นในบรรทัดเดียวกัน
                seg = line[line.index(fname) + len(fname):][:90]
                for m in re.finditer(r"(\d+)\s*(?:ฟิลด์|field|record)", seg):
                    n = int(m.group(1))
                    if n != real:
                        bad.append(f"{rel} :: อ้างว่า {fname} มี {n} ฟิลด์ แต่ไฟล์จริงมี {real}"
                                   f"  ← \"…{seg.strip()[:60]}\"")
    check("จำนวนฟิลด์ของไฟล์ interface", bad)

    # ---- 2. ปฏิทินของไฟล์ IAS
    bad = []
    ias_ce = all(y.startswith("20") for y in truth["ias_years"])
    if not ias_ce:
        bad.append(f"ไฟล์ IAS จริงมีปี {truth['ias_years']} — สมมติฐาน ค.ศ. ของตัวตรวจนี้ใช้ไม่ได้แล้ว")
    else:
        for rel, txt in docs:
            if rel == KNOWLEDGE:
                continue
            for line in txt.split("\n"):
                if "AMS06001" not in line or "พ.ศ." not in line:
                    continue
                # ประโยคที่แก้ให้ถูกแล้วจะพูดถึง ค.ศ. ในบรรทัดเดียวกันด้วย
                if "ค.ศ." in line:
                    continue
                bad.append(f"{rel} :: บรรทัดที่เอ่ย AMS06001 พร้อม พ.ศ. โดยไม่มี ค.ศ. กำกับ — "
                           f"ไฟล์ IAS จริงเป็น ค.ศ. (ปีที่พบ {', '.join(truth['ias_years'])})")
    check("ปฏิทินของไฟล์ IAS (ของจริง = ค.ศ.)", bad)

    # ---- 3. รูปแบบวันที่ฟิลด์ 3 ของ FRBC0001
    bad = []
    if truth["frbc_has_slash"]:
        for rel, txt in docs:
            if rel == KNOWLEDGE:
                continue
            for line in txt.split("\n"):
                if "ddMMyyyy" in line and "dd/MM/yyyy" not in line:
                    bad.append(f"{rel} :: เขียน `ddMMyyyy` — ไฟล์ FRBC0001 จริงเป็น "
                               f"`dd/MM/yyyy` (เช่น {truth['frbc_date_samples'][0]})")
    check("รูปแบบวันที่ FRBC0001 ฟิลด์ 3", bad)

    # ---- 4. ลำดับหมวด QSSI
    bad = []
    pat = re.compile(r"\b8\s*,\s*9\s*,\s*12\s*,\s*1\s*,\s*10\s*,\s*16\b")
    wrong = re.compile(r"\b(?:1|8|9|10|12|16)(?:\s*,\s*(?:1|8|9|10|12|16)){5}\b")
    for rel, txt in docs:
        for line in txt.split("\n"):
            for m in wrong.finditer(line):
                seq = [x.strip() for x in m.group(0).split(",")]
                if sorted(seq, key=int) == sorted(QSSI_ORDER, key=int) and seq != QSSI_ORDER:
                    bad.append(f"{rel} :: ลำดับหมวด QSSI เป็น {','.join(seq)} — "
                               f"ต้องเป็น {','.join(QSSI_ORDER)} (ลำดับฟิลด์ 9–14 ของ FRBC0001)")
    check("ลำดับหมวด QSSI", bad)

    # ---- 5. สัญญา JSON ของ STA เทียบฟิลด์ในไฟล์จริง
    bad = []
    sta = ROOT / "STA" / "ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md"
    real_n = next(iter(truth["FRBC0001"]["fields"]))
    if sta.exists():
        txt = read(sta)
        found = [k for k in STA_KEYS if f'"{k}"' in txt]
        missing = [k for k in STA_KEYS if k not in found]
        if missing:
            bad.append(f"STA/…Message-RabbitMQ.md :: ตัวอย่าง JSON ขาดคีย์ {missing}")
        if len(STA_KEYS) != real_n:
            bad.append(f"ตัวตรวจเอง :: รายการคีย์ STA_KEYS มี {len(STA_KEYS)} "
                       f"แต่ไฟล์จริงมี {real_n} ฟิลด์ — อัปเดตตัวตรวจ")
        # บล็อกตัวอย่าง pipe ในสัญญา ต้องมีจำนวนฟิลด์เท่าไฟล์จริง
        for line in txt.split("\n"):
            if line.count("|") >= 8 and re.match(r"^\d{5}\|", line.strip()):
                n = len(line.strip().split("|"))
                if n != real_n:
                    bad.append(f"STA/…Message-RabbitMQ.md :: ตัวอย่างรูปแบบเดิม `{line.strip()[:40]}…` "
                               f"มี {n} ฟิลด์ แต่ไฟล์จริงมี {real_n} — "
                               f"ดูข้อ 2.39 ใน DECISIONS")
    warn("สัญญา sgi_impact_store เทียบไฟล์จริง (เอกสารต้นฉบับ — แก้เองไม่ได้)", bad)

    # ---- 6. โครงหน้าต่างยอดขาย
    bad = []
    full, partial = 0, []
    for (store, opend), dates in truth["window_groups"].items():
        n, sizes, has_open = window_shape(dates, opend)
        if has_open:
            bad.append(f"ไฟล์จริง :: ร้าน {store} มีวันที่ร้านใหม่เปิดอยู่ในชุดข้อมูล — "
                       f"ขัดกับที่เอกสารเขียนว่าหน้าต่างกันวันเปิดออก")
        if n == 60 and sizes == [15, 15, 15, 15]:
            full += 1
        else:
            partial.append((store, n, sizes))
    for rel, txt in docs:
        if re.search(r"4\s*(?:หน้าต่าง|windows?)\s*[x×]\s*15", txt) and "60" not in txt:
            bad.append(f"{rel} :: เอ่ย 4 หน้าต่าง × 15 วัน แต่ไม่ได้ระบุยอดรวม 60 วันไว้ที่ใดในไฟล์")
    check("โครงหน้าต่างยอดขาย 4 × 15 = 60 วัน", bad)

    # ---- สรุป
    width = max(len(k) for k in list(FINDINGS) + list(WARNINGS)) + 2
    print(f"{'ตรวจ':<{width}} ผิด")
    print("─" * 74)
    total = 0
    for name, probs in FINDINGS.items():
        total += len(probs)
        print(f"  {name:<{width}} {len(probs):>3}  {'✅' if not probs else '❌'}")
        for p in probs[:6]:
            print(f"       • {p}")
        if len(probs) > 6:
            print(f"       • … อีก {len(probs) - 6} จุด")
    for name, probs in WARNINGS.items():
        print(f"  {name:<{width}} {len(probs):>3}  {'✅' if not probs else '⚠️ '}")
        for p in probs[:6]:
            print(f"       • {p}")
    print("─" * 74)
    if any(WARNINGS.values()):
        print("  ⚠️  คำเตือนข้างบนอยู่ในเอกสารต้นฉบับของทีมอื่น (`STA/`) ซึ่งห้ามแก้ —")
        print("      บันทึกไว้เป็นข้อ 2.39 ใน DECISIONS-รอตัดสินใจ.md แล้ว รอยืนยันกับทีม STA")
    print(f"  ร้านที่ได้ข้อมูลครบ 60 วัน {full} ร้าน · ไม่ครบ {len(partial)} ร้าน"
          + (f" → {partial}" if partial else ""))
    print("  " + ("สรุป: ผ่านทุกข้อ ✅" if total == 0 else f"พบปัญหา {total} จุด ❌"))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
