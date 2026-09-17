#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างรายการตารางที่ต้องขอจากทีมเจ้าของฐาน K2 เพื่อทำ migration — **ครบทั้ง 47 ตาราง**

    python3 tools/build_k2_migration_request.py  →  docs/K2-migration-รายการตารางที่ต้องขอ.md

ทำไมต้อง generate
    "เอาให้ครบ" แปลว่าต้องไม่ตกสักตาราง · เขียนมือแล้วตกแน่นอน
    สคริปต์นี้จึงอ่านรายชื่อตารางจริงจาก DDL ที่ได้มา แล้วบังคับว่า
    **ทุกตารางต้องถูกจัดกลุ่ม** ถ้ามีตัวไหนไม่ได้จัด จะ error ทันที

แหล่งข้อมูล
    docs/script_TB_DB_CPA_FRN_FGI_20260722 1.sql  (UTF-16LE · อยู่ใน .gitignore)
    ถ้าไม่มีไฟล์ จะใช้รายชื่อสำรองที่ฝังไว้ (คัดจากไฟล์เดียวกันตอน 2026-09-16)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DDL = ROOT / "docs" / "script_TB_DB_CPA_FRN_FGI_20260722 1.sql"
OUT = ROOT / "docs" / "K2-migration-รายการตารางที่ต้องขอ.md"

FALLBACK = """ActionProfile ActivityProfile ApplicationMenu ApplicationRoles AttachFileProfile
AuthorizedMenu BranchTypeProfile CommonConfig CompDocAttachment CompTempAttachment
CompenOrganizeProfile CompensateFlow CompensateHistory CompetInCompenProfile CompetitionProfile
DecisionProfile FGIHelp FactorInCompenProfile FactorProfile FormProfile ImpactCostDetail
ImpactProfile Journal JournalDetail ListDocumentsPendingRemoval LogCompensate LogCompensateReturn
MENU MaintainForm MaintainFormAuthorized MaintainHistory MaintainMasterHistory MaintainMessage
MasterUserViewer MonitorAdjust RoleForAuthorizedMenu RunningNumber SectionProfile ServerMaster
ServerType StatusProfile TaskList TaskMaster TransectionDeleteStore URLPath Versions
ZoneProfile""".split()

# ---------------------------------------------------------------- การจัดกลุ่ม
# A = ขอข้อมูลทุกแถว · B = ขอจำนวน/ตัวอย่างเพื่อตัดสิน · C = master ที่ได้แล้ว · D = ไม่ใช้
# 🔴 3 ตารางที่อยู่ในกลุ่ม A ตอนแรก แต่ **เป็นตารางว่าง ไม่มีข้อมูลเลยสักแถว**
#    (ผู้ส่งยืนยัน 2026-09-16 · ไม่ได้ตกหล่น)
EMPTY = [
    ("FactorInCompenProfile", "sgi_document_external_factors",
     "🔴 ไม่เคยมีใครบันทึกปัจจัยภายนอกลงเอกสารเลย ตลอด 18,007 ฉบับ ปี 2019–2026"),
    ("CompDocAttachment", "sgi_document_attachments", "ช่องทาง CM/ECM ไม่เคยถูกใช้"),
    ("CompTempAttachment", "sgi_document_attachments", "ไม่มีไฟล์ชั่วคราวค้าง"),
]

A = [
    ("CompensateFlow", "sgi_compensation_documents",
     "หัวเอกสาร 1 แถว = 1 เอกสาร — ตัวตั้งต้นของทั้ง migration",
     "ทุกคอลัมน์ · 25 คอลัมน์สายอนุมัติ (FC/เขต/ฝ่าย/GM/AVP) ลง `approver_snapshot` JSONB"),
    ("CompensateHistory", "sgi_consideration_logs + sgi_compensation_histories",
     "ประวัติพิจารณาทุกขั้น — ไม่ย้าย = เอกสารเก่าไม่มีที่มา",
     "ทุกคอลัมน์ · ⚠️ 3 คอลัมน์มีคำอธิบายในฐานไม่ตรงชื่อ (`ActionFRCCMail` · `OfficeContentURL` · `ActionFRAssignAD`) ต้องดูข้อมูลจริง"),
    ("ImpactProfile", "sgi_document_new_stores (+ sgi_fgi_impact_stores)",
     "คู่ร้าน ถูกกระทบ ↔ เปิดใหม่ + ระยะทาง/รัศมี",
     "ทุกคอลัมน์ · `_N` = ร้านเปิดใหม่ · `_I` = ร้านถูกกระทบ อยู่ในแถวเดียวกัน"),
    ("ImpactCostDetail", "sgi_document_cost_details",
     "เงินชดเชยและ %ต่อร้านเปิดใหม่",
     "ทุกคอลัมน์ · 🔴 ต้องได้ทั้ง `CostTarget_N`/`Cost_N` (ระบบคำนวณ) และ `_Nc` (คนปรับ) — ขาดคู่ใดคู่หนึ่งแยกไม่ออกว่าใครแก้"),
    ("CompetInCompenProfile", "sgi_document_competitors",
     "คู่แข่งที่ผูกกับเอกสาร",
     "ทุกคอลัมน์ · `CreateType` 0 = จาก FMS · 1 = ผู้ใช้คีย์เอง → `source_system`"),
    ("RunningNumber", "sgi_document_running_numbers",
     "ตัวนับเลขเอกสารต่อปี",
     "ทุกคอลัมน์ (4) · ตั้ง `last_running_no` ต่อปีให้ต่อจากเลขสูงสุดที่ย้ายมา"),
    ("AttachFileProfile", "sgi_document_attachments",
     "ไฟล์แนบหลัก + สถานะ S3",
     "ทุกคอลัมน์ · `FlagUpload` `FlagPurgeData` `FlagDeleteS3` `StatusCodeDeleteS3` — โครงใหม่ยังไม่มีวงจรนี้"),
    ("CompetitionProfile", "sgi_competitors",
     "master ยี่ห้อคู่แข่ง — 🔴 ยังไม่เคยได้ข้อมูล",
     "ทุกแถว (ตารางเล็ก) · `sgi_competitors` ตอนนี้มี 11 แถวที่ลอกจากหน้าจอ **ยังไม่เคยเทียบกับฐานจริง**"),
]

B = [
    ("MaintainMessage", "🔴 ตารางเดียวในฐานที่มีโครง \"หัวเรื่อง + เนื้อความ\" — ต้องดูว่าเป็นข้อความ popup หน้าจออย่างเดียว หรือมีเนื้อความอีเมลปนอยู่ (`MsgType` จะบอก)"),
    ("CompenOrganizeProfile", "ผู้ดำเนินการต่อ Section × Zone — ปลายทางใช้ auth-backend ของ SBP แต่ต้องรู้ว่ามีใครบ้างเพื่อตั้ง prepared approver ของ workflow engine"),
    ("MasterUserViewer", "ข้อมูลพนักงาน 16 คอลัมน์ — ต้องเทียบว่าซ้อนกับ `business_user` ของ SBP แค่ไหน ⚠️ มีข้อมูลส่วนบุคคล"),
    ("CommonConfig", "config กลาง — มีกลุ่ม `PurgeDay` ที่คุมวงจรลบข้อมูลซึ่งโครงใหม่ยังไม่มี"),
    ("ListDocumentsPendingRemoval", "วงจร archive → purge ของเอกสาร — **ไม่มีปลายทางในโครงใหม่เลย** ต้องตัดสินว่าจะยกมาไหม"),
    ("TransectionDeleteStore", "ประวัติการลบร้านออกจากเอกสาร + `SRNumber` — ไม่มีปลายทาง แต่เป็นหลักฐานการแก้ไขย้อนหลัง"),
    ("MonitorAdjust", "ติดตามการปรับยอด/รอผลคำนวณกลับจาก FS (`CompForecast` · `CompActual` · `KeyCallSMO`)"),
    ("LogCompensate", "ล็อกการเรียกข้ามระบบ — อาจไม่ต้องย้าย แต่ต้องรู้ปริมาณก่อนตัด"),
    ("LogCompensateReturn", "ล็อก request/response ขากลับ — เหมือนข้างบน"),
]

C = [
    ("FactorProfile", "sgi_external_factors", "✅ ได้แล้ว 7 แถว · ติดตั้งลง dev แล้ว 2026-09-16"),
    ("StatusProfile", "common_code `SGI_DOC_STATUS`", "✅ ได้แล้ว 10 แถว · ใช้แปลงสถานะเก่า → 6 ค่าใหม่"),
    ("SectionProfile", "common_code `SGI_APPROVE_LIMIT`", "✅ ได้แล้ว 10 แถว · ยืนยันเกณฑ์ 100,000 ที่ section 2 (GM)"),
    ("DecisionProfile", "common_code `SGI_DECISION`", "✅ ได้แล้ว 14 แถว · ใช้แปลงผลพิจารณาเก่า → 7 ค่าใหม่"),
    ("ZoneProfile", "`mas_zone` ของ SBP", "✅ ได้แล้ว 13 แถว · เป็นตารางแปลงรหัสโซนที่ Job 8b/12 ต้องใช้"),
    ("BranchTypeProfile", "common_code ของ SBP", "✅ ได้แล้ว 8 แถว · มี 3 ชื่อต่อ 1 รหัส (MM/FMS/FGI)"),
    ("ApplicationRoles", "auth-backend ของ SBP (ไม่ migrate)", "✅ ได้แล้ว 8 แถว · ใช้อ้างอิงเฉย ๆ"),
]

D = {
    "ActionProfile": "ทะเบียน action ของแพลตฟอร์ม BPM",
    "ActivityProfile": "ทะเบียน activity ของแพลตฟอร์ม BPM",
    "ApplicationMenu": "เมนูของเว็บ K2 — ระบบใหม่ใช้เมนูของ SBP portal",
    "AuthorizedMenu": "สิทธิ์เห็นเมนูรายคน — ตัดตามมติ 2026-08-05 (ใช้ auth-backend)",
    "RoleForAuthorizedMenu": "สิทธิ์เห็นเมนูราย role — ตัดตามมติ 2026-08-05",
    "MENU": "โครงเมนู — ตัดตามมติ 2026-08-05",
    "MaintainForm": "ทะเบียนฟอร์มของ K2",
    "MaintainFormAuthorized": "สิทธิ์ต่อฟอร์มของ K2",
    "MaintainHistory": "ประวัติการแก้ฟอร์ม/หน้าจอ ของ K2",
    "MaintainMasterHistory": "ประวัติการแก้ master ของ K2 — ระบบใหม่ยังไม่มี audit กลาง (ข้อค้าง DP-12)",
    "FormProfile": "โครงฟอร์มของ K2",
    "FGIHelp": "เนื้อหาหน้า Help ของ K2",
    "Versions": "เลขเวอร์ชันของแอป K2",
    "URLPath": "URL ต่อ environment — ระบบใหม่ใช้ env/config ของ NestJS",
    "ServerType": "ทะเบียนประเภท server (D/U/P)",
    "ServerMaster": "ทะเบียน server",
    "TaskMaster": "โครงงานของแพลตฟอร์ม BPM (48 คอลัมน์ · ไม่มีคำอธิบายสักตัว)",
    "TaskList": "โครงฟิลด์ของงาน BPM",
    "Journal": "ล็อกของแพลตฟอร์ม",
    "JournalDetail": "ล็อกของแพลตฟอร์ม (รายละเอียด)",
}


def table_names() -> list[str]:
    if DDL.exists():
        raw = DDL.read_bytes().decode("utf-16-le", errors="replace").replace("\r", "")
        names = re.findall(r"CREATE TABLE \[dbo\]\.\[(\w+)\]\(", raw)
        if names:
            return sorted(names)
    return sorted(FALLBACK)


def build(names: list[str]) -> str:
    covered = {t for t, *_ in A} | {t for t, _ in B} | {t for t, *_ in C} | set(D) | {t for t, *_ in EMPTY}
    missing = sorted(set(names) - covered)
    extra = sorted(covered - set(names))
    if missing or extra:
        raise SystemExit(f"จัดกลุ่มไม่ครบ · ตกหล่น {missing} · เกินมา {extra}")

    L: list[str] = []
    a = L.append
    a("# รายการตารางของฐาน K2 ที่ต้องใช้ทำ migration เข้าระบบ SGI — **ครบทั้ง 47 ตาราง**")
    a("")
    a("> สร้างจาก `tools/build_k2_migration_request.py` — **ห้ามแก้ไฟล์นี้ด้วยมือ**")
    a("> อ่านรายชื่อตารางจาก DDL จริง (`docs/script_TB_DB_CPA_FRN_FGI_20260722 1.sql`) แล้วบังคับว่า")
    a("> **ทุกตารางต้องถูกจัดกลุ่ม** — ถ้ามีตัวไหนไม่ได้จัด สคริปต์จะ error ไม่ยอมสร้างไฟล์")
    a(">")
    a("> ใช้คู่กับ `docs/K2-database-CPA_FRN_FGI.md` (โครงสร้าง) · `docs/K2-master-data.md` (master ที่ได้แล้ว)")
    a("> · `output/sql/k2_migration_profile.sql` (สคริปต์สำรวจ SELECT ล้วน)")
    a("")
    a("## สรุปเป็นตัวเลข")
    a("")
    a("| กลุ่ม | จำนวน | ต้องทำอะไร |")
    a("|---|---:|---|")
    a(f"| **A · ขอข้อมูลทุกแถว** | **{len(A)}** | ✅ **ได้ครบแล้ว 2026-09-16** (`docs/data_bk_all/`) |")
    a(f"| **A′ · อยู่ในกลุ่ม A แต่เป็นตารางว่าง** | **{len(EMPTY)}** | ไม่มีข้อมูลเลยสักแถว — ไม่ต้องขอ |")
    a(f"| **B · ขอจำนวนแถวก่อน แล้วค่อยตัดสิน** | **{len(B)}** | ยังไม่รู้ว่าต้องย้ายไหม |")
    a(f"| **C · master ที่ได้ข้อมูลแล้ว** | **{len(C)}** | เป็นแหล่ง migration แต่**ไม่ต้องขอซ้ำ** |")
    a(f"| **D · ไม่ใช้เลย** | **{len(D)}** | โครงสร้างพื้นฐานของแพลตฟอร์ม K2/BPM |")
    a(f"| **รวม** | **{len(names)}** | = จำนวนตารางทั้งหมดในฐาน |")
    a("")
    a(f"## กลุ่ม A′ · อยู่ในกลุ่ม A ตอนแรก แต่ **เป็นตารางว่าง** — {len(EMPTY)} ตาราง")
    a("")
    a("ผู้ส่งยืนยัน 2026-09-16 ว่าไม่ได้ตกหล่น — **ไม่มีข้อมูลเลยสักแถวจริง ๆ**")
    a("")
    a("| # | ตาราง | → ปลายทาง | ผลที่ตามมา |")
    a("|---:|---|---|---|")
    for i, (t, tgt, why) in enumerate(EMPTY, 1):
        a(f"| {i} | `{t}` | `{tgt}` | {why} |")
    a("")
    a("→ ✅ **ไฟล์แนบเหลือทางเดียวคือ `AttachFileProfile`** (11,696 แถว) — งาน migrate ไฟล์แนบง่ายกว่าที่ประเมินไว้")
    a("→ 🔴 **ฟีเจอร์ปัจจัยภายนอกไม่เคยถูกใช้เลยตลอด 8 ปี** — ต้องถามธุรกิจว่ายังต้องมีใน SGI ไหม (ข้อค้าง 2.41)")
    a("")
    a("⚠️ **สิ่งที่ต้องขอก่อนข้อมูลเต็ม** — รัน `output/sql/k2_migration_profile.sql` (SELECT ล้วน)")
    a("แล้วส่งผลกลับมาก่อน เพราะฐาน K2 **ไม่มี FOREIGN KEY และไม่มี CHECK constraint สักตัว**")
    a("ข้อมูลจริงจึงอาจละเมิดทุกกติกาที่ DDL ของ SGI บังคับ (27 CHECK · 28 FK · 19 UNIQUE)")
    a("")
    a("---")
    a("")
    a(f"## กลุ่ม A · ขอข้อมูลทุกแถว — {len(A)} ตาราง")
    a("")
    a("| # | ตาราง | → ปลายทางใน SGI | ทำไมต้องมี | คอลัมน์ที่ต้องการ |")
    a("|---:|---|---|---|---|")
    for i, (t, tgt, why, cols) in enumerate(A, 1):
        a(f"| {i} | **`{t}`** | `{tgt}` | {why} | {cols} |")
    a("")
    a("**ไฟล์แนบมี 3 ตาราง ไม่ใช่ตารางเดียว** (`AttachFileProfile` · `CompDocAttachment` · `CompTempAttachment`)")
    a("— ต้องรู้ว่าไฟล์จริงของแต่ละตัวอยู่ที่ไหน (S3 ของ K2 / ระบบ CM / ในฐานเอง) เพราะปลายทางเก็บแค่ metadata")
    a("")
    a(f"## กลุ่ม B · ขอจำนวนแถวก่อน แล้วค่อยตัดสิน — {len(B)} ตาราง")
    a("")
    a("| # | ตาราง | ทำไมต้องตัดสิน |")
    a("|---:|---|---|")
    for i, (t, why) in enumerate(B, 1):
        a(f"| {i} | **`{t}`** | {why} |")
    a("")
    a(f"## กลุ่ม C · master ที่ได้ข้อมูลแล้ว — {len(C)} ตาราง (ไม่ต้องขอซ้ำ)")
    a("")
    a("ได้จาก `docs/ข้อมูล Master K2.xlsx` เมื่อ 2026-09-16 → ถอดไว้ใน `docs/K2-master-data.md`")
    a("")
    a("| # | ตาราง | → ปลายทาง | สถานะ |")
    a("|---:|---|---|---|")
    for i, (t, tgt, st) in enumerate(C, 1):
        a(f"| {i} | `{t}` | {tgt} | {st} |")
    a("")
    a("🔴 **`CompetitionProfile` ไม่ได้อยู่ในกลุ่มนี้** เพราะชีตที่ได้มาไม่มีตารางนั้น — อยู่กลุ่ม A ข้อ 11")
    a("")
    a(f"## กลุ่ม D · ไม่ใช้เลย — {len(D)} ตาราง")
    a("")
    a("| # | ตาราง | เป็นอะไร |")
    a("|---:|---|---|")
    for i, t in enumerate(sorted(D), 1):
        a(f"| {i} | `{t}` | {D[t]} |")
    a("")
    a("---")
    a("")
    a("## สิ่งที่ต้องขอเพิ่ม — ไม่ได้อยู่ในฐาน K2")
    a("")
    a("| # | ขออะไร | ทำไม |")
    a("|---:|---|---|")
    a("| 1 | **source ของ stored procedure `GetRunningNumberSp`** | เป็นคนออกเลขเอกสารจริง แต่**ไม่อยู่ในสคริปต์ DDL ที่ได้มา** · ยังไม่รู้ว่ากันเลขซ้ำอย่างไร (lock / sequence / read-modify-write) |")
    a("| 2 | **ไฟล์แนบจริง** — bucket/path + สิทธิ์อ่าน | ฐานเก็บแค่ metadata · ไฟล์ต้องย้ายขึ้น S3 ของ SBP |")
    a("| 3 | 🔴 **mapping: transition ไหน → ส่ง email template ไหน** | ตัวที่ตัดสินอยู่ใน workflow engine ของ K2 **ไม่ได้อยู่ในฐาน** · ถ้าไม่ได้อันนี้ ระบบใหม่จะเดาเองว่าสถานะไหนส่งฉบับไหน |")
    a("| 4 | กติกาผู้รับ **TO/CC ต่อ transition** | ของเดิมมีช่องผู้รับ 8 ช่องใน `CompensateFlow` + CC 2 ช่องใน `CompensateHistory` |")
    a("| 5 | **mapping โดเมนอีเมล → ชื่อโดเมน AD** | trigger เดิมอ่านจาก `BPMCentralMaster.dbo.bpmParameterProfile` ซึ่งไม่มีในระบบใหม่ |")
    a("")
    a("### ✅ เนื้อความอีเมลไม่ต้องขอ — อยู่ในฐาน PostgreSQL ของ SBP แล้ว")
    a("")
    a("`sps_store.email_template` **id 1501010–1501044 = 33 แถว** คือชุด template ของระบบประกันรายได้เดิม")
    a("ยืนยันด้วยตัวแปรในเนื้อความที่เป็นชื่อคอลัมน์ของ K2 ตรง ๆ (`${compCurrentUser}` = `CompensateFlow.CompCurrentUser` ฯลฯ)")
    a("ในฐาน K2 **ไม่มีตาราง email template สักตัว** — คอลัมน์ที่มีคำว่า mail ทั้งหมดเป็น *ที่อยู่ผู้รับ* ไม่ใช่เนื้อความ")
    a("")
    a("## แหล่งข้อมูล migration มี **สองฐาน** ไม่ใช่ฐานเดียว")
    a("")
    a("| ฐาน | ให้อะไร | สถานะ |")
    a("|---|---|---|")
    a("| **SQL Server `CPA_FRN_FGI`** (K2) | ฝั่งเอกสาร/อนุมัติ — เอกสารนี้ทั้งฉบับ | 🔴 ยังไม่มีข้อมูล ต้องขอ |")
    a("| **Oracle `FCS_FRN`** (FGI/FCS) | ฝั่งคำนวณ — `FGI_IMPACT_*` · `FGI_NEW_STORE_*` · `FGI_CONFIRM_RECEIVE_DATA` | ✅ ได้แล้ว ผ่าน `tools/introspect_legacy_oracle.py` → `output/legacy-oracle/` |")
    a("")
    a("บางตารางปลายทางรับจาก**ทั้งสองฝั่ง** เช่น `sgi_compensation_histories` = ")
    a("`FGI_IMPACT_STORE_COMPENSATE` (Oracle) + `CompensateFlow` (K2)")
    a("")
    a("## รูปแบบไฟล์ที่ขอ")
    a("")
    a("- **encoding** — UTF-8 หรือ UTF-16 ก็ได้ แต่**ต้องบอกมาว่าอันไหน** (สคริปต์ DDL ที่ได้มาก่อนหน้านี้เป็น UTF-16LE + CRLF)")
    a("- **`NULL` ต้องแยกจากค่าว่าง** — ฐานเดิมมีทั้งสองแบบและความหมายต่างกัน")
    a("- **ห้ามตัดศูนย์นำหน้าของรหัสร้าน** (`00788` ไม่ใช่ `788`) — ปลายทางเป็น `VARCHAR(5)`")
    a("- คอลัมน์ `datetime` ขอเป็น ISO (`YYYY-MM-DD HH:MM:SS`) และบอกด้วยว่าเป็น **ค.ศ. หรือ พ.ศ.**")
    a("")
    a("⚠️ ข้อมูลกลุ่ม A เป็น **ข้อมูลธุรกิจจริง** (ชื่อร้าน · ชื่อเจ้าของร้าน · อีเมล · ยอดเงิน)")
    a("และ `MasterUserViewer` ในกลุ่ม B เป็น **ข้อมูลส่วนบุคคล** — ต้องตกลงช่องทางส่งและที่เก็บให้ชัดก่อน")
    a("ถ้าวางในโปรเจกต์นี้ต้องเข้า `.gitignore` เหมือน `docs/file_IAS_STA/` และ `docs/ข้อมูล Master K2.xlsx`")
    return "\n".join(L) + "\n"


def main() -> int:
    names = table_names()
    OUT.write_text(build(names), encoding="utf-8")
    src = "DDL จริง" if DDL.exists() else "รายชื่อสำรองที่ฝังไว้"
    print(f"เขียนแล้ว: {OUT.relative_to(ROOT)}")
    print(f"  รายชื่อตารางจาก: {src} · {len(names)} ตาราง")
    tot = len(A) + len(EMPTY) + len(B) + len(C) + len(D)
    print(f"  A {len(A)} · A′(ว่าง) {len(EMPTY)} · B {len(B)} · C {len(C)} · D {len(D)} = {tot} "
          + ("✅ ครบ" if tot == len(names) else f"❌ ไม่ครบ (ฐานมี {len(names)})"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
