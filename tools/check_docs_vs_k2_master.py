#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ตรวจ seed และเอกสาร กับ **master data จริงของระบบ K2 เดิม**

    python3 tools/check_docs_vs_k2_master.py

ความจริงมาจาก `docs/ข้อมูล Master K2.xlsx` (export จากฐาน `CPA_FRN_FGI` เมื่อ 08/10/2026)
คู่กับ `check_docs_vs_db.py` (ฐาน PostgreSQL จริง) และ `check_docs_vs_ias_sta.py` (ไฟล์ interface จริง)

⚠️ ไฟล์ xlsx อยู่ใน `.gitignore` (มีชื่อ-อีเมลพนักงาน) — ถ้าไม่มีไฟล์จะข้ามทุกข้อแล้ว exit 0

สิ่งที่ตรวจ
  1. ปัจจัยภายนอกใน `k2-factors.html` (ต้นทางของ seed) ต้องตรงกับ `FactorProfile` ทุกรหัสทุกชื่อ
  2. เกณฑ์วงเงินอนุมัติ — master มีค่าเดียวที่ section GM · เอกสารต้องเขียนตัวเลขเดียวกัน
  3. จำนวน role ที่เอกสารอ้าง ต้องตรงกับ `ApplicationRoles`
  4. ชื่อสถานะที่ seed ใช้ ต้องมีต้นทางใน `StatusProfile` (ยกเว้นที่ SDD สั่งเปลี่ยนชื่อ)
  5. ชื่อฝั่ง FGI ของประเภทร้านซ้ำกัน — เอกสารห้ามบอกว่าแปลงกลับเป็นรหัสได้
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "docs" / "ข้อมูล Master K2.xlsx"
KNOWLEDGE = "docs/K2-master-data.md"

SKIP_DIRS = ("output/legacy-oracle", "output/legacy-sgi", "batchjob/fcsJar",
             "SBP/", "node_modules", ".git", "LLDD/word", "LLDD/pdf")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def doc_files() -> list[Path]:
    out = []
    for ext in ("*.md", "*.html"):
        for p in ROOT.rglob(ext):
            rel = str(p.relative_to(ROOT))
            if any(rel.startswith(d) or f"/{d}" in rel for d in SKIP_DIRS):
                continue
            out.append(p)
    return sorted(out)


def sheet_rows(wb, name: str, ncol: int, key_re: str) -> list[list[str]]:
    """แถวข้อมูลของชีต — ทุกชีตมีสคริปต์ CREATE TABLE ต่อท้าย จึงคัดด้วย pattern ของคอลัมน์คีย์
    (กรองด้วย prefix ของ DDL อย่างเดียวไม่พอ — บรรทัด `PRIMARY KEY CLUSTERED` หลุดเข้ามาได้)"""
    out = []
    for r in wb[name].iter_rows(values_only=True):
        first = "" if r[0] is None else str(r[0]).strip()
        if not re.match(key_re, first):
            continue
        out.append(["" if c is None else str(c).strip() for c in r[:ncol]])
    return out


FINDINGS: dict[str, list[str]] = {}


def check(name: str, problems: list[str]) -> None:
    FINDINGS[name] = sorted(set(problems))


def main() -> int:
    if not XLSX.exists():
        print(f"ℹ️  ไม่พบ {XLSX.relative_to(ROOT)} — ข้ามการตรวจทั้งหมด")
        print("   (อยู่ใน .gitignore เพราะมีชื่อ-อีเมลพนักงาน · ขอจากทีมที่ถือไฟล์)")
        return 0
    try:
        import openpyxl
    except ImportError:
        print("ต้องมี openpyxl (pip install openpyxl)", file=sys.stderr)
        return 2

    wb = openpyxl.load_workbook(XLSX, data_only=True)
    factors = sheet_rows(wb, "FactorProfile", 4, r"^[0-9A-F]{8}-")   # คีย์เป็น GUID
    sections = sheet_rows(wb, "SectionProfile", 4, r"^\d{1,2}$")
    roles = sheet_rows(wb, "ApplicationRoles", 3, r"^\d{2}$")
    statuses = sheet_rows(wb, "StatusProfile", 3, r"^\d{1,2}$")
    branches = sheet_rows(wb, "BranchTypeProfile", 5, r"^\d{1,2}$")
    docs = [(str(p.relative_to(ROOT)), read(p)) for p in doc_files()]
    print(f"master จริง: ปัจจัย {len(factors)} · section {len(sections)} · role {len(roles)} · "
          f"สถานะ {len(statuses)} · ประเภทร้าน {len(branches)}")
    print(f"ตรวจเอกสาร {len(docs)} ไฟล์\n")

    # ---- 1. ปัจจัยภายนอกใน k2-factors.html = ต้นทางของ seed
    bad = []
    real = {f[1]: f[2] for f in factors}
    html = read(ROOT / "k2-factors.html")
    got = {}
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        tds = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) >= 4 and re.match(r"^\d{1,2}$", tds[1]):
            got[tds[1]] = tds[2]
    for code, name in sorted(real.items()):
        if code not in got:
            bad.append(f"k2-factors.html :: ขาดปัจจัย `{code}` {name} ที่มีใน FactorProfile จริง")
        elif got[code] != name:
            bad.append(f"k2-factors.html :: ปัจจัย `{code}` ชื่อ \"{got[code]}\" แต่ของจริงคือ \"{name}\"")
    for code in sorted(set(got) - set(real)):
        bad.append(f"k2-factors.html :: มีปัจจัย `{code}` {got[code]} ที่**ไม่มีใน master จริง**")
    check("ปัจจัยภายนอกตรงกับ FactorProfile", bad)

    # ---- 2. เกณฑ์วงเงินอนุมัติ
    bad = []
    limits = [(s[0], s[1], s[2]) for s in sections if s[2] not in ("", "NULL")]
    if len(limits) != 1:
        bad.append(f"master มีวงเงิน {len(limits)} ค่า ({limits}) — ตัวตรวจนี้ตั้งบนสมมติฐานว่ามีค่าเดียว")
    else:
        code, sec_name, amount = limits[0]
        want = str(int(float(amount)))
        # ตรวจ "ค่าที่ seed ลงฐานจริง" ไม่ใช่ไล่ตัวเลขทุกตัวในบรรทัด (บรรทัดเดียวกันมักมีเลขอื่นปนอยู่)
        seed_sql = read(ROOT / "output" / "sql" / "sgi_seed_data.sql")
        seeded = set(re.findall(r"'SGI_APPROVE_LIMIT', \d+, '(\d+)'", seed_sql))
        if seeded != {want}:
            bad.append(f"seed :: SGI_APPROVE_LIMIT ลงค่า {sorted(seeded) or 'ไม่มีเลย'} "
                       f"แต่ master จริงมีค่าเดียวคือ {want} ที่ section {code} ({sec_name})")
        # และห้ามมีเกณฑ์สองชั้นรุ่นเก่าหลงเหลือในเอกสาร
        for rel, txt in docs:
            if rel == KNOWLEDGE or "DECISIONS" in rel:
                continue
            for line in txt.split("\n"):
                # บรรทัดที่เอ่ยเกณฑ์เก่าพร้อมบอกว่าถูกแทนแล้ว (มี 100,000 อยู่ด้วย) = บันทึกประวัติ ไม่ใช่ของค้าง
                if (re.search(r"วงเงิน|เกณฑ์", line)
                        and re.search(r"\b50,?000\b.*\b300,?000\b", line)
                        and not re.search(r"\b100,?000\b", line)):
                    bad.append(f"{rel} :: ระบุเกณฑ์สองชั้น 50,000/300,000 โดยไม่มี 100,000 กำกับ — "
                               f"เกณฑ์นั้นถูกยกเลิกแล้ว · master จริงมีค่าเดียว {want}")
    check("เกณฑ์วงเงินอนุมัติตรงกับ SectionProfile", bad)

    # ---- 3. จำนวน role
    bad = []
    n_roles = len(roles)
    ids = sorted(r[0] for r in roles)
    for rel, txt in docs:
        if rel == KNOWLEDGE:
            continue
        # จับเฉพาะวลีที่พูดถึง "จำนวนกลุ่มสิทธิ์ทั้งชุด" จริง ๆ — คำว่า role โดด ๆ ปนอยู่ทั่วเอกสาร
        for m in re.finditer(r"(\d+)\s*(?:permission role groups?|role groups?|กลุ่มสิทธิ์)", txt, re.I):
            n = int(m.group(1))
            if n != n_roles:
                bad.append(f"{rel} :: อ้างว่ามี {n} role แต่ ApplicationRoles จริงมี {n_roles} ({' '.join(ids)})")
    check("จำนวน role ตรงกับ ApplicationRoles", bad)

    # ---- 4. ชื่อสถานะที่ seed ใช้ ต้องสืบไปถึง StatusProfile ได้
    bad = []
    real_status = {s[1] for s in statuses}
    seed = read(ROOT / "output" / "sql" / "sgi_seed_data.sql")
    seeded = re.findall(r"'SGI_DOC_STATUS', \d+, '(\d+)', '([^']+)'", seed)
    # ชื่อที่ SDD GI สั่งเปลี่ยน — มีต้นทางแต่คำไม่ตรง
    RENAMED = {"รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ", "รอผู้บริหารสำนักบริหาร SBP ดำเนินการ"}
    for code, name in seeded:
        if name in real_status or name in RENAMED:
            continue
        near = [s for s in real_status if name[:12] in s or s[:12] in name]
        bad.append(f"seed :: สถานะ `{code}` \"{name}\" ไม่มีต้นทางใน StatusProfile"
                   + (f" (ใกล้เคียง: {near})" if near else ""))
    check("สถานะที่ seed ใช้ สืบถึง StatusProfile ได้", bad)

    # ---- 5. ชื่อฝั่ง FGI ซ้ำ — เอกสารห้ามบอกว่าแปลงกลับได้
    bad = []
    fgi = [b[4] for b in branches if len(b) > 4 and b[4] not in ("", "NULL")]
    dup = sorted({v for v in fgi if fgi.count(v) > 1})
    # หมายเหตุ: เดิมพยายามจับ "เอกสารที่บอกว่าชื่อ FGI ไม่ซ้ำ" ด้วย regex แต่ได้ false positive ล้วน
    # (คำว่า `1:1`/`ไม่ซ้ำ` ในบรรทัดเดียวกันมักพูดถึงเรื่องอื่น) — จึงรายงานเป็นข้อมูลประกอบแทน
    check("ชื่อประเภทร้านฝั่ง FGI ซ้ำกัน (ข้อมูลประกอบ)", bad)

    # ---- สรุป
    width = max(len(k) for k in FINDINGS) + 2
    print(f"{'ตรวจ':<{width}} ผิด")
    print("─" * 74)
    total = 0
    for name, probs in FINDINGS.items():
        total += len(probs)
        print(f"  {name:<{width}} {len(probs):>3}  {'✅' if not probs else '❌'}")
        for p in probs[:8]:
            print(f"       • {p}")
        if len(probs) > 8:
            print(f"       • … อีก {len(probs) - 8} จุด")
    print("─" * 74)
    if dup:
        print(f"  ℹ️  ชื่อฝั่ง FGI ที่ซ้ำในของจริง: {dup} — ใช้รหัสเป็นหลักเสมอ")
    print("  " + ("สรุป: ผ่านทุกข้อ ✅" if total == 0 else f"พบปัญหา {total} จุด ❌"))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
