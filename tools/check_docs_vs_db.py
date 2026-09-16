#!/usr/bin/env python3
"""
ตรวจเอกสารของโครงการกับ **ข้อมูลจริงจากฐานสองฝั่ง**

    output/legacy-oracle/data.json   ฝั่ง As-Is (Oracle ของระบบ Java เดิม)
    output/legacy-sgi/data.json      ฝั่งปลายทาง (PostgreSQL dev ของระบบ SBP)

ต่างจาก `check_docs.py` ตรงที่ตัวนั้นตรวจ**ความสอดคล้องภายในเอกสารเอง**
ส่วนตัวนี้ตรวจว่า **สิ่งที่เอกสารอ้างว่าเป็นจริงในฐาน ยังจริงอยู่ไหม**

    python3 tools/check_docs_vs_db.py            # ต้องรัน introspect ทั้งสองตัวก่อน

exit 1 เมื่อพบข้อที่เอกสารอ้างไม่ตรงของจริง · ข้ามเงียบ ๆ เมื่อยังไม่มีไฟล์ข้อมูล
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORA = ROOT / "output" / "legacy-oracle" / "data.json"
SGI = ROOT / "output" / "legacy-sgi" / "data.json"

# เอกสารที่ตรวจ — ไม่รวมผลลัพธ์ที่ generate จากฐานเอง และไม่รวม /SBP (อ่านอย่างเดียว)
DOC_GLOBS = ("*.md", "*.html", "LLDD/md/**/*.md", "batchjob/*.md",
             "SBP/srm-sps-spsap-sop-sgi-batch/*.md")
SKIP_PARTS = ("node_modules", "output/legacy-oracle", "output/legacy-sgi",
              "LLDD/pdf", "LLDD/word", "output/srs", "output/diagrams")


def load(p: Path):
    if not p.exists():
        return None
    return json.loads(io.open(p, encoding="utf-8").read())


def docs() -> list[Path]:
    seen, out = set(), []
    for g in DOC_GLOBS:
        for f in ROOT.glob(g):
            rel = str(f.relative_to(ROOT))
            if any(s in rel for s in SKIP_PARTS) or rel in seen:
                continue
            seen.add(rel)
            out.append(f)
    return out


def _num(s: str) -> int:
    return int(s.replace(",", ""))


# --------------------------------------------------------------- ตรวจข้อ 1
def check_row_counts(sgi: dict, files: list[Path]) -> list[str]:
    """ตัวเลขจำนวนแถวของตารางระบบเดิมที่เอกสารอ้าง ต้องตรงกับฐาน dev จริง"""
    live = {t: i["row_count"] for t, i in sgi["tables"].items() if i.get("exists")}
    names = sorted(live, key=len, reverse=True)
    bad = []
    for f in files:
        text = io.open(f, encoding="utf-8", errors="ignore").read()
        for t, real in live.items():
            # จับรูปแบบ  `table` ... 12,345 แถว  /  12,345 rows — **ในบรรทัดเดียวเท่านั้น**
            # `(?!\.)` = ข้ามกรณี `mas_store.status_type` — ประโยคนั้นพูดถึงคอลัมน์ ไม่ใช่จำนวนแถวของตาราง
            # 🔴 เดิมใช้ re.S ทำให้จับข้ามบรรทัดแล้วโยงตัวเลขของตารางอื่นมาใส่ผิดตัว
            for m in re.finditer(r"`?\b" + re.escape(t) + r"\b(?!\.)`?([^\n|]{0,60}?)([\d,]{4,})\s*(?:แถว|rows?)", text):
                try:
                    claimed = _num(m.group(2))
                except ValueError:
                    continue
                gap = m.group(1)
                # 🔴 ถ้ามีชื่อตารางอื่นคั่นอยู่ แปลว่าเลขนั้นเป็นของตารางนั้น ไม่ใช่ของ t
                #    (แถวตารางใน markdown/html มีหลายคอลัมน์บนบรรทัดเดียว)
                if any(o != t and re.search(r"\b" + re.escape(o) + r"\b", gap) for o in names):
                    continue
                if claimed != real and abs(claimed - real) < max(real * 0.5, 5000):
                    bad.append(f"{f.relative_to(ROOT)} :: `{t}` เอกสารว่า {claimed:,} แถว · ฐาน dev จริง {real:,}")
    return sorted(set(bad))


# --------------------------------------------------------------- ตรวจข้อ 2
def check_pk_claims(sgi: dict, files: list[Path]) -> list[str]:
    """ข้ออ้างว่า 'ไม่มี PK' / 'ไม่มี index' ต้องตรงกับของจริง"""
    bad = []
    for t, i in sgi["tables"].items():
        if not i.get("exists"):
            continue
        has_pk = any(c["type"] == "p" for c in i["constraints"])
        n_idx = len(i["indexes"])
        for f in files:
            text = io.open(f, encoding="utf-8", errors="ignore").read()
            # 🔴 ห้ามใช้ re.S — ข้ออ้าง "ไม่มี PK" ของตารางหนึ่งจะถูกโยงไปอีกตารางที่อยู่บรรทัดถัดไป
            for m in re.finditer(r"`?\b" + re.escape(t) + r"\b`?([^\n]{0,90}?)(ไม่มี\s*(?:ทั้ง\s*)?PK[^\n]{0,40})", text):
                if has_pk:
                    bad.append(f"{f.relative_to(ROOT)} :: อ้างว่า `{t}` ไม่มี PK แต่ของจริงมี "
                               f"({[c['columns'] for c in i['constraints'] if c['type']=='p'][0]})")
                elif "index" in m.group(2) and n_idx:
                    bad.append(f"{f.relative_to(ROOT)} :: อ้างว่า `{t}` ไม่มี index แต่ของจริงมี {n_idx} ตัว")
    return sorted(set(bad))


# --------------------------------------------------------------- ตรวจข้อ 3
def check_columns(sgi: dict, files: list[Path]) -> list[str]:
    """คอลัมน์ของตารางระบบเดิมที่ SQL ในเอกสารอ้าง ต้องมีอยู่จริงในฐาน dev"""
    cols = {t: {c["name"] for c in i["columns"]}
            for t, i in sgi["tables"].items() if i.get("exists")}
    bad = []
    for f in files:
        text = io.open(f, encoding="utf-8", errors="ignore").read()
        for block in re.findall(r"```sql\n(.*?)```", text, re.S):
            block = re.sub(r"--[^\n]*", "", block)
            for t, known in cols.items():
                if not re.search(r"\b" + re.escape(t) + r"\b", block):
                    continue
                # alias ของตารางนี้ เช่น  FROM sps_store.mas_store ms
                aliases = set(re.findall(
                    r"(?:FROM|JOIN)\s+(?:sps_store\.)?" + re.escape(t) + r"\s+(?:AS\s+)?([a-z][a-z0-9_]{0,3})\b",
                    block, re.I))
                aliases.add(t)
                for a in aliases:
                    for m in re.finditer(r"\b" + re.escape(a) + r"\.([a-z_][a-z0-9_]*)", block):
                        c = m.group(1)
                        if c not in known and c not in ("*",):
                            bad.append(f"{f.relative_to(ROOT)} :: SQL อ้าง `{t}.{c}` แต่ฐาน dev ไม่มีคอลัมน์นี้")
    return sorted(set(bad))


# --------------------------------------------------------------- ตรวจข้อ 4
def check_seeded_names(sgi: dict, files: list[Path]) -> list[str]:
    """ชื่อ/ค่า SGI ที่เอกสารอ้าง ต้องตรงกับที่ถูกติดตั้งลงฐาน dev แล้วจริง"""
    seeded = sgi["questions"]["sgi_seeded"]
    installed_params = {r["param_name"] for r in seeded["mas_param"]}
    installed_codes = {(r["code_type"], r["code_value"]) for r in seeded["common_code"]}
    if not installed_params and not installed_codes:
        return []
    bad = []
    # ชื่อ param ที่เอกสารอ้างแต่ฐานใช้ชื่ออื่น (เทียบเฉพาะกลุ่มที่รู้ว่าเป็นเรื่องเดียวกัน)
    ALIASES = {
        "SGI_SALES_DATA_MIN_DAYS": "SGI_SALES_DAYS_MIN",
        "SGI_GROWTH_RATE_THRESHOLD": "SGI_GROWTH_RATE_MAX",
        "SGI_IMPACT_RADIUS_BKK_KM": "SGI_IMPACT_RADIUS_BKK",
        "SGI_IMPACT_RADIUS_UPC_KM": "SGI_IMPACT_RADIUS_UPC",
    }
    for f in files:
        text = io.open(f, encoding="utf-8", errors="ignore").read()
        for wrong, right in ALIASES.items():
            if right in installed_params and wrong in text:
                bad.append(f"{f.relative_to(ROOT)} :: ใช้ชื่อ `{wrong}` แต่ฐาน dev ติดตั้งเป็น `{right}`")
        if ("SGI_APPROVE_LIMIT", "100000") in installed_codes:
            for line in text.split("\n"):
                if "'THRESHOLD'" not in line:
                    continue
                # บรรทัดที่เอ่ยทั้งค่าเก่าและค่าใหม่ = คำอธิบายประวัติ ไม่ใช่ข้ออ้างที่ยังใช้อยู่
                if "'100000'" in line or any(w in line for w in ("เดิม", "ยกเลิก", "ไม่ตรง", "แก้ 2026")):
                    continue
                bad.append(f"{f.relative_to(ROOT)} :: อ้าง code_value `'THRESHOLD'` "
                           f"แต่ฐาน dev ติดตั้งเป็น `'100000'`")
                break
    return sorted(set(bad))


# --------------------------------------------------------------- ตรวจข้อ 5
def check_oracle_widths(ora: dict, files: list[Path]) -> list[str]:
    """ความยาวจริงของรหัสร้านในฐาน Oracle เทียบกับที่เอกสารสรุป"""
    cw = ora.get("data", {}).get("questions", {}).get("column_widths")
    if not cw:
        return []
    mx = cw.get("MAX_LEN_I")
    if mx is None:
        return []
    bad = []
    for f in files:
        text = io.open(f, encoding="utf-8", errors="ignore").read()
        if "ความยาวจริงสูงสุด" in text:
            for m in re.finditer(r"ความยาวจริงสูงสุด\s*=\s*(\d+)", text):
                if int(m.group(1)) != mx:
                    bad.append(f"{f.relative_to(ROOT)} :: อ้างความยาวรหัสร้านสูงสุด {m.group(1)} "
                               f"· ฐาน Oracle (ตารางสด) วัดได้ {mx}")
    return sorted(set(bad))


def main() -> int:
    ora, sgi = load(ORA), load(SGI)
    if sgi is None:
        print("⏭️  ยังไม่มี output/legacy-sgi/data.json — รัน tools/introspect_dev_sgi.py ก่อน", file=sys.stderr)
        return 0
    files = docs()
    print(f"ตรวจเอกสาร {len(files)} ไฟล์ กับข้อมูลจริงจากฐาน\n")

    # ⚠️ จำนวนแถวเป็น **คำเตือน ไม่ใช่ความล้มเหลว** — ฐาน dev ยังมีระบบเดิมใช้งานอยู่
    #    ตัวเลขจึงขยับทุกวันโดยไม่มีใครทำอะไรผิด · ส่วนข้ออ้างเชิงโครงสร้าง (คอลัมน์ · PK · ชื่อค่า)
    #    ถือเป็นความล้มเหลวจริง เพราะมันไม่ควรเปลี่ยนเองโดยไม่มีคนตัดสินใจ
    warn_checks = [("จำนวนแถวของตารางระบบเดิมที่เอกสารอ้าง", check_row_counts(sgi, files))]
    fail_checks = [
        ("ข้ออ้างเรื่อง PK / index", check_pk_claims(sgi, files)),
        ("คอลัมน์ที่ SQL ในเอกสารอ้าง", check_columns(sgi, files)),
        ("ชื่อ/ค่า SGI ที่ติดตั้งลงฐานแล้ว", check_seeded_names(sgi, files)),
    ]
    if ora:
        fail_checks.append(("ความยาวรหัสร้านในฐาน Oracle", check_oracle_widths(ora, files)))
    else:
        print("⚠️  ไม่มี output/legacy-oracle/data.json — ข้ามการตรวจฝั่ง As-Is\n")

    def show(pairs, warn_only: bool) -> int:
        n = 0
        for name, bad in pairs:
            mark = "✅" if not bad else ("⚠️ " if warn_only else "❌")
            print(f"  {name:<46}{len(bad):>4}  {mark}")
            for b in bad[:12]:
                print(f"       • {b}")
            if len(bad) > 12:
                print(f"       … อีก {len(bad)-12} รายการ")
            n += len(bad)
        return n

    warns = show(warn_checks, True)
    fails = show(fail_checks, False)
    print("─" * 74)
    if warns:
        print(f"  ⚠️  จำนวนแถว drift {warns} จุด — ปกติสำหรับฐานที่ยังใช้งานอยู่")
        print("      รีเฟรชด้วย tools/introspect_dev_sgi.py แล้วอัปเดตตัวเลขที่ generator เมื่อเห็นสมควร")
    print(f"  สรุป: {'ผ่านทุกข้อ ✅' if fails == 0 else f'พบ {fails} จุดที่ต้องแก้ ❌'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
