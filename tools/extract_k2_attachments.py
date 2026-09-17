#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""แกะไฟล์แนบที่ K2 ฝัง base64 ไว้ในฐาน ออกมาเป็นไฟล์จริง

    PGPASSWORD=... python3 tools/extract_k2_attachments.py [--confirm]

🔴 สิ่งที่ค้นพบ 2026-09-17 — ไฟล์แนบของ K2 **ไม่ได้อยู่บน S3**
    คอลัมน์ `AttachFileProfile.AttachFileLink` เก็บ **ตัวไฟล์เอง** เป็น base64 ในห่อ XML
        <file><name>ชื่อไฟล์.xlsx</name><content>UEsDBBQ…</content></file>
    (ชื่อคอลัมน์ว่า "link" ทำให้เข้าใจผิดมาตลอดว่าเป็น URL)

🔴 แต่ dump ที่ได้มา **ถูกตัดที่ 65,535 ตัวอักษร**
    มีเนื้อไฟล์ 3,932 แถว · ตันเพดาน (ถูกตัด) 3,253 · ปิด </content> ครบ 679
    แกะสำเร็จจริง **678 ไฟล์ · 21.3 MB** (xlsx 471 · xls 207)
    → **ต้องขอ K2 re-export คอลัมน์นี้แบบไม่ตัดความยาว** ถึงจะได้ไฟล์แนบครบ 11,696 รายการ

🔒 SELECT ล้วน · ⚠️ ผลลัพธ์เป็น**ไฟล์ Excel ของจริง** (ชื่อร้าน ยอดเงิน ข้อมูลผู้ประกอบการ)
   → เขียนลง `output/legacy-k2-attachments/` ซึ่ง **เพิ่มเข้า .gitignore ไว้เฉพาะเจาะจงแล้ว**
   ⚠️ `output/` **ไม่ได้ถูก ignore ทั้งก้อน** — มีแค่บาง subfolder ที่ระบุไว้
      ถ้าเพิ่มโฟลเดอร์ผลลัพธ์ใหม่ใต้ output/ ต้องเติม .gitignore เองทุกครั้ง
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
import sys
from collections import Counter
from pathlib import Path

import pg8000.native

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "legacy-k2-attachments"
DEFAULT_HOST = ("srm-sps-spsap-postgres-instance-dev-new"
                ".cluster-cxsegsg200gm.ap-southeast-1.rds.amazonaws.com")
CONTENT = re.compile(r"<content>(.*?)</content>", re.S)
NAME = re.compile(r"<name>(.*?)</name>", re.S)
SIGS = {b"PK\x03\x04": "xlsx/docx/zip", b"\xd0\xcf\x11\xe0": "xls/doc (OLE2)", b"%PDF": "pdf"}


def safe_name(s: str) -> str:
    """กันชื่อไฟล์ที่มี / หรือ .. ไม่ให้เขียนออกนอกโฟลเดอร์ปลายทาง"""
    s = s.replace("\x00", "").strip() or "unnamed"
    return re.sub(r"[/\\\x00-\x1f]", "_", s)[:120]


def main() -> int:
    confirm = "--confirm" in sys.argv
    if not os.environ.get("PGPASSWORD"):
        print("ขาด PGPASSWORD — ส่งผ่าน env เท่านั้น", file=sys.stderr)
        return 2
    host = os.environ.get("PGHOST") or DEFAULT_HOST
    c = pg8000.native.Connection(user=os.environ.get("PGUSER", "sps_store"),
        password=os.environ["PGPASSWORD"], host=host,
        port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "postgres"), ssl_context=True, timeout=1800)
    c.run("SET search_path TO sps_store")

    total = c.run("SELECT count(*) FROM sgi_mig_k2_attach_file_profile")[0][0]
    withlink = c.run("""SELECT count(*) FROM sgi_mig_k2_attach_file_profile
                         WHERE nullif(btrim(attach_file_link), '') IS NOT NULL""")[0][0]
    cut = c.run("""SELECT count(*) FROM sgi_mig_k2_attach_file_profile
                    WHERE length(attach_file_link) = 65535""")[0][0]
    rows = c.run("""SELECT attach_file_id, attach_file_comp_document_id, file_name, attach_file_link
                      FROM sgi_mig_k2_attach_file_profile
                     WHERE attach_file_link LIKE '%</content>%'""")

    print(f"ฐาน      : {host}")
    print(f"โหมด     : {'🔴 เขียนไฟล์จริง (--confirm)' if confirm else '🟢 dry-run'}")
    print(f"ปลายทาง  : {OUT.relative_to(ROOT)}/\n")
    print(f"  ไฟล์แนบทั้งหมดในฐาน K2        {total:>7,}")
    print(f"  มีเนื้อไฟล์ฝังมา               {withlink:>7,}")
    print(f"  🔴 ถูกตัดที่ 65,535 ตัวอักษร   {cut:>7,}  ← ต้องขอ K2 re-export")
    print(f"  ปิด </content> ครบ             {len(rows):>7,}\n")

    ok = bad = 0
    kinds: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    seen: dict[str, str] = {}
    written = 0
    if confirm:
        OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = ["attach_file_id\tdoc_no\tfile_name\tbytes\tsha256\tkind\tsaved_as"]

    for aid, doc, fname, link in rows:
        m = CONTENT.search(link or "")
        if not m:
            bad += 1; reasons["ไม่มี <content> ครบคู่"] += 1; continue
        b64 = "".join(m.group(1).split())
        try:
            data = base64.b64decode(b64, validate=True)
        except Exception as e:
            bad += 1; reasons[str(e)[:44]] += 1; continue
        ok += 1
        kinds[SIGS.get(data[:4], "ไม่รู้จัก")] += 1
        sha = hashlib.sha256(data).hexdigest()
        nm = NAME.search(link)
        disp = safe_name((nm.group(1) if nm else None) or fname or f"{aid}.bin")
        saved = ""
        if confirm:
            # ตั้งชื่อด้วย sha256 กันไฟล์ซ้ำเขียนทับกัน (ของจริงซ้ำ 239 จาก 678)
            if sha in seen:
                saved = seen[sha]
            else:
                saved = f"{sha[:16]}_{disp}"
                (OUT / saved).write_bytes(data)
                seen[sha] = saved
                written += 1
        manifest.append(f"{aid}\t{doc or ''}\t{disp}\t{len(data)}\t{sha}\t"
                        f"{SIGS.get(data[:4], '?')}\t{saved}")

    print(f"  แกะสำเร็จ {ok:,} · ล้มเหลว {bad:,}")
    for r, n in reasons.most_common(3):
        print(f"    - {r}: {n:,}")
    for k, n in kinds.most_common():
        print(f"    {k:<18}{n:>6,}")

    if not confirm:
        print(f"\n🟢 dry-run จบ — ยังไม่เขียนไฟล์ · ใส่ --confirm เพื่อแกะจริง")
        return 0

    (OUT / "manifest.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    size = sum(f.stat().st_size for f in OUT.glob("*") if f.is_file())
    print(f"\n✅ เขียน {written:,} ไฟล์ (ไม่ซ้ำ) · {size/1048576:.1f} MB")
    print(f"   {OUT.relative_to(ROOT)}/manifest.tsv — เทียบ sha256 กับ sgi_document_attachments ได้")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
