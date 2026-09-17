#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""สร้างสคริปต์ **T-SQL อ่านอย่างเดียว** ให้ทีมเจ้าของฐาน K2 รันแล้วส่งผลกลับมา

    python3 tools/build_k2_migration_profile_sql.py   →  output/sql/k2_migration_profile.sql

ทำไมต้องมี
    ก่อนเขียนสคริปต์ migrate จริง เราต้องรู้ "หน้าตาข้อมูลจริง" ก่อน — ไม่ใช่แค่โครงสร้าง
    ฐาน K2 **ไม่มี FK และไม่มี CHECK สักตัว** (ดู `docs/K2-database-CPA_FRN_FGI.md`)
    แปลว่าข้อมูลจริงอาจละเมิดทุกกติกาที่ DDL ใหม่จะบังคับ · ต้องวัดก่อน ไม่ใช่เดา

สิ่งที่สคริปต์ผลลัพธ์ทำ
    * `SELECT` ล้วน — ไม่มี INSERT/UPDATE/DELETE/DDL แม้แต่คำสั่งเดียว
    * ไม่ดึงข้อมูลธุรกิจออกมาเป็นแถว ๆ — คืนแต่ **จำนวน · โดเมนของค่า · ความยาวสูงสุด · ช่วงวันที่**
      (ยกเว้นคอลัมน์รหัส/สถานะสั้น ๆ ที่ต้องรู้ค่าจริงเพื่อตั้ง CHECK ให้ถูก)
    * แบ่งเป็นส่วน ๆ ตามคำถามที่ต้องตอบก่อน migrate
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "sql" / "k2_migration_profile.sql"

# (ตาราง, ปลายทางใน SGI, เหตุผลสั้น ๆ)
CORE = [
    ("CompensateFlow", "sgi_compensation_documents", "หัวเอกสาร — 1 แถว = 1 เอกสาร"),
    ("CompensateHistory", "sgi_consideration_logs + sgi_compensation_histories", "ประวัติพิจารณาทุกขั้น"),
    ("ImpactProfile", "sgi_document_new_stores", "คู่ร้าน ถูกกระทบ ↔ เปิดใหม่"),
    ("ImpactCostDetail", "sgi_document_cost_details", "เงินชดเชย/%ต่อร้านเปิดใหม่"),
    ("CompetInCompenProfile", "sgi_document_competitors", "คู่แข่งที่ผูกกับเอกสาร"),
    ("FactorInCompenProfile", "sgi_document_external_factors", "ปัจจัยภายนอกที่ผูกกับเอกสาร"),
    ("RunningNumber", "sgi_document_running_numbers", "ตัวนับเลขเอกสารต่อปี"),
    ("AttachFileProfile", "sgi_document_attachments", "ไฟล์แนบ + สถานะ S3"),
    ("CompDocAttachment", "sgi_document_attachments", "ไฟล์แนบฝั่ง CM/ECM"),
    ("CompTempAttachment", "sgi_document_attachments", "ไฟล์แนบชั่วคราว"),
]

DECIDE = [
    ("CompetitionProfile", "master ยี่ห้อคู่แข่ง — ยังไม่มีในชุด xlsx ที่ได้มา"),
    ("TransectionDeleteStore", "ประวัติการลบร้านออกจากเอกสาร + SRNumber"),
    ("ListDocumentsPendingRemoval", "วงจร archive → purge ที่โครงใหม่ยังไม่มี"),
    ("MonitorAdjust", "ติดตามการปรับยอด/รอผลคำนวณกลับ"),
    ("LogCompensate", "ล็อกการเรียกข้ามระบบ"),
    ("LogCompensateReturn", "ล็อก request/response ขากลับ"),
    ("CompenOrganizeProfile", "ผู้ดำเนินการต่อ Section × Zone"),
    ("MasterUserViewer", "ข้อมูลพนักงาน (เทียบกับ business_user ของ SBP)"),
    ("CommonConfig", "config กลาง — มีกลุ่ม PurgeDay ที่คุมวงจรลบข้อมูล"),
]

# คอลัมน์ที่ต้องรู้ "ค่าจริงทั้งหมด" เพราะปลายทางมี CHECK constraint หรือเป็นคีย์แปลง
DOMAINS = [
    ("CompensateFlow", "CompStatusCode", "→ SGI_DOC_STATUS · ปลายทางรับแค่ 6 ค่า"),
    ("CompensateFlow", "CompSectionCode", "→ section_code · ปลายทางเดิน 5 ขั้น (01 02 03 06 08)"),
    ("CompensateFlow", "CompDecisionCode", "→ SGI_DECISION · ปลายทางมี 7 ค่า"),
    ("CompensateFlow", "CompFlagStatus", "I/S/N/A — ต้องรู้ว่ามีค่าอื่นปนไหม"),
    ("CompensateFlow", "CompType", "01–04"),
    ("CompensateFlow", "CompStoreTypeCode", "B/F"),
    ("CompensateFlow", "CompStoreManagerAction", "N/Y"),
    ("CompensateFlow", "CompFlagCalculation", "0/1"),
    ("CompensateHistory", "ActionSectionCode", "เหมือนข้างบน"),
    ("CompensateHistory", "ActionStatusCode", "เหมือนข้างบน"),
    ("CompensateHistory", "ActionDecisionCode", "เหมือนข้างบน"),
    ("CompensateHistory", "ActionSendApprove", "0/1"),
    ("CompetInCompenProfile", "CreateType", "0 = จาก FMS · 1 = ผู้ใช้สร้างเอง"),
    ("CompetInCompenProfile", "CompetitionCode", "ต้อง map กับ master 11 รหัส"),
    ("FactorInCompenProfile", "FactorCode", "ต้องอยู่ใน 1–6, 99 ของ FactorProfile"),
    ("ImpactProfile", "ImpCompType", "01–04"),
    ("ImpactProfile", "ImpStoreTypeCode_N", "B/F"),
    ("ImpactProfile", "ImpStoreTypeCode_I", "B/F"),
    ("ImpactProfile", "ImpStoreRadianUnit", "หน่วยของรัศมี"),
]

# คอลัมน์ nvarchar(max) ที่ปลายทางกำหนดความยาวไว้ — ต้องรู้ความยาวจริงสูงสุด
LENGTHS = [
    ("CompensateFlow", "CompStoreName", "ปลายทาง VARCHAR(200)"),
    ("CompensateFlow", "CompCorporationName", "ปลายทาง VARCHAR(200)"),
    ("CompensateFlow", "CompCurrentUser", "ปลายทางเป็นชื่อผู้ใช้"),
    ("CompensateFlow", "CompAllUser", "เก็บผู้เกี่ยวข้องทั้งหมดเป็นข้อความก้อนเดียว"),
    ("CompensateFlow", "CompAllUserMail", "เหมือนข้างบน"),
    ("CompensateFlow", "CompUrlMap", "ลิงก์ AllMap"),
    ("CompensateFlow", "CompStatementID", "ลิงก์ Statement"),
    ("CompensateHistory", "ActionComment", "หมายเหตุผู้ดำเนินการ"),
    ("ImpactProfile", "ImpStoreName_N", "ปลายทาง VARCHAR(200)"),
    ("ImpactProfile", "ImpStoreName_I", "ปลายทาง VARCHAR(200)"),
    ("CompetInCompenProfile", "CompetitionStoreName", "ชื่อสาขาคู่แข่ง"),
    ("CompetInCompenProfile", "CompetInCompenRemark", "หมายเหตุจากหน้าจอ"),
    ("FactorInCompenProfile", "FactorInCompenRemark", "หมายเหตุ · รหัส 99 ต้องมีค่า"),
]


def build() -> str:
    L: list[str] = []
    a = L.append
    a("-- =====================================================================")
    a("--  K2 (CPA_FRN_FGI) — สคริปต์สำรวจข้อมูลก่อน migrate เข้าระบบ SGI")
    a("--  สร้างจาก tools/build_k2_migration_profile_sql.py — ห้ามแก้ไฟล์นี้ด้วยมือ")
    a("-- ---------------------------------------------------------------------")
    a("--  🔒 SELECT ล้วน — ไม่มี INSERT / UPDATE / DELETE / DDL แม้แต่คำสั่งเดียว")
    a("--  🔒 ไม่ดึงข้อมูลธุรกิจออกเป็นแถว ๆ — คืนแต่จำนวน · โดเมนของค่า · ความยาว · ช่วงวันที่")
    a("--     (ยกเว้นคอลัมน์รหัส/สถานะสั้น ๆ ที่ต้องรู้ค่าจริงเพื่อตั้ง CHECK ให้ถูก)")
    a("--")
    a("--  ทำไมต้องสำรวจก่อน: ฐาน K2 **ไม่มี FOREIGN KEY และไม่มี CHECK constraint สักตัว**")
    a("--  ข้อมูลจริงจึงอาจละเมิดทุกกติกาที่ DDL ของ SGI จะบังคับ — ถ้าไม่วัดก่อน full load จะล้มทั้ง batch")
    a("-- =====================================================================")
    a("USE [CPA_FRN_FGI];")
    a("SET NOCOUNT ON;")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 1 · จำนวนแถวของตารางที่ต้องย้าย")
    a("-- ---------------------------------------------------------------------")
    for i, (t, target, why) in enumerate(CORE):
        a(f"-- {t} → {target} ({why})")
        a(f"SELECT '{t}' AS table_name, COUNT(*) AS row_count FROM dbo.[{t}]"
          + (" UNION ALL" if i < len(CORE) - 1 else ";"))
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 2 · ตารางที่ยังไม่ตัดสินว่าต้องย้ายไหม — ขอจำนวนแถวเพื่อประเมิน")
    a("-- ---------------------------------------------------------------------")
    for i, (t, why) in enumerate(DECIDE):
        a(f"-- {t} — {why}")
        a(f"SELECT '{t}' AS table_name, COUNT(*) AS row_count FROM dbo.[{t}]"
          + (" UNION ALL" if i < len(DECIDE) - 1 else ";"))
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 3 · โดเมนของค่าจริง (คอลัมน์ที่ปลายทางมี CHECK constraint)")
    a("--   🔴 สำคัญที่สุด — ค่าที่โผล่มานอกรายการที่เราคาดไว้ = migrate ล้มแน่นอน")
    a("-- ---------------------------------------------------------------------")
    for t, c, why in DOMAINS:
        a(f"-- {t}.{c} — {why}")
        a(f"SELECT '{t}.{c}' AS col, [{c}] AS value, COUNT(*) AS cnt")
        a(f"  FROM dbo.[{t}] GROUP BY [{c}] ORDER BY cnt DESC;")
        a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 4 · ความยาวจริงของคอลัมน์ nvarchar(max)")
    a("--   ปลายทางเป็น VARCHAR(n) — ถ้าของจริงยาวกว่า n แถวนั้น load ไม่เข้า")
    a("-- ---------------------------------------------------------------------")
    for i, (t, c, why) in enumerate(LENGTHS):
        a(f"-- {t}.{c} — {why}")
        a(f"SELECT '{t}.{c}' AS col, MAX(LEN([{c}])) AS max_len, "
          f"SUM(CASE WHEN [{c}] IS NULL THEN 1 ELSE 0 END) AS null_rows, COUNT(*) AS total_rows "
          f"FROM dbo.[{t}]" + (" UNION ALL" if i < len(LENGTHS) - 1 else ";"))
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 5 · คีย์และความสัมพันธ์ (ฐานเดิมไม่มี FK จึงต้องตรวจเอง)")
    a("-- ---------------------------------------------------------------------")
    a("-- 5.1 เลขเอกสารซ้ำไหม — ปลายทาง sgi_compensation_documents.doc_no เป็น UNIQUE")
    a("SELECT CompDocumentID, COUNT(*) AS cnt FROM dbo.CompensateFlow")
    a("  GROUP BY CompDocumentID HAVING COUNT(*) > 1 ORDER BY cnt DESC;")
    a("")
    a("-- 5.2 เลขเอกสารว่าง/รูปแบบผิด — ปลายทางบังคับ YYYY/xxxxx (10 ตัวอักษร)")
    a("SELECT COUNT(*) AS null_or_blank FROM dbo.CompensateFlow")
    a("  WHERE CompDocumentID IS NULL OR LTRIM(RTRIM(CompDocumentID)) = '';")
    a("SELECT COUNT(*) AS wrong_format FROM dbo.CompensateFlow")
    a("  WHERE CompDocumentID IS NOT NULL AND CompDocumentID NOT LIKE '[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9][0-9]';")
    a("")
    a("-- 5.3 ปีในเลขเอกสารเป็น ค.ศ. หรือ พ.ศ. — ปลายทางบังคับ ค.ศ. เท่านั้น")
    a("SELECT LEFT(CompDocumentID, 4) AS doc_year, COUNT(*) AS cnt FROM dbo.CompensateFlow")
    a("  WHERE CompDocumentID IS NOT NULL GROUP BY LEFT(CompDocumentID, 4) ORDER BY doc_year;")
    a("")
    a("-- 5.4 ลูกกำพร้า — แถวลูกที่ไม่มีหัวเอกสาร (ฐานเดิมไม่มี FK จึงเกิดได้)")
    for child, col in (("ImpactCostDetail", "CompDocumentID"),
                       ("FactorInCompenProfile", "CompDocumentID"),
                       ("CompDocAttachment", "CompDocumentID"),
                       ("CompTempAttachment", "CompDocumentID"),
                       ("AttachFileProfile", "AttachFileCompDocumentID"),
                       ("CompensateHistory", "ActionCompDocumentID")):
        a(f"SELECT '{child}' AS child_table, COUNT(*) AS orphan_rows FROM dbo.[{child}] x")
        a(f"  WHERE x.[{col}] IS NOT NULL AND NOT EXISTS")
        a(f"    (SELECT 1 FROM dbo.CompensateFlow f WHERE f.CompDocumentID = x.[{col}]);")
    a("")
    a("-- 5.5 รหัสร้านที่เสียศูนย์นำหน้า — ปลายทางเป็น VARCHAR(5) zero-pad")
    a("SELECT 'CompensateFlow.CompStoreCode' AS col, COUNT(*) AS not_5_chars")
    a("  FROM dbo.CompensateFlow WHERE CompStoreCode IS NOT NULL AND LEN(CompStoreCode) <> 5;")
    a("SELECT 'ImpactProfile.ImpStoreCode_N' AS col, COUNT(*) AS not_5_chars")
    a("  FROM dbo.ImpactProfile WHERE ImpStoreCode_N IS NOT NULL AND LEN(ImpStoreCode_N) <> 5;")
    a("SELECT 'ImpactProfile.ImpStoreCode_I' AS col, COUNT(*) AS not_5_chars")
    a("  FROM dbo.ImpactProfile WHERE ImpStoreCode_I IS NOT NULL AND LEN(ImpStoreCode_I) <> 5;")
    a("")
    a("-- 5.6 กติกา %ชดเชยรวมของร้านเปิดใหม่ = 100% — ของเดิมไม่มีอะไรบังคับ")
    a("--     คืนจำนวนกลุ่ม (เอกสาร × งวด) ที่รวมแล้วไม่ได้ 100 · ทั้งฝั่งระบบคำนวณและฝั่งคนปรับ")
    a("SELECT SUM(CASE WHEN ABS(sum_n  - 100) > 0.01 THEN 1 ELSE 0 END) AS bad_system_calc,")
    a("       SUM(CASE WHEN ABS(sum_nc - 100) > 0.01 THEN 1 ELSE 0 END) AS bad_user_adjusted,")
    a("       COUNT(*) AS total_groups")
    a("  FROM (SELECT CompDocumentID, CostYear, CostMonth,")
    a("               SUM(CAST(CostTarget_N  AS float)) AS sum_n,")
    a("               SUM(CAST(CostTarget_Nc AS float)) AS sum_nc")
    a("          FROM dbo.ImpactCostDetail GROUP BY CompDocumentID, CostYear, CostMonth) g;")
    a("")
    a("-- 5.7 แถวที่คนเคยปรับค่าจริง ๆ (trigger ตั้ง _Nc = _N ตอน insert จึงแยกไม่ออกด้วยตาเปล่า)")
    a("SELECT SUM(CASE WHEN CostTarget_Nc <> CostTarget_N THEN 1 ELSE 0 END) AS pct_changed,")
    a("       SUM(CASE WHEN Cost_Nc <> Cost_N THEN 1 ELSE 0 END) AS amount_changed,")
    a("       COUNT(*) AS total_rows FROM dbo.ImpactCostDetail;")
    a("")

    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 6 · ช่วงเวลาและปริมาณงานตอน cutover")
    a("-- ---------------------------------------------------------------------")
    a("SELECT MIN(CompCreateDate) AS first_doc, MAX(CompCreateDate) AS last_doc,")
    a("       MIN(CompYear) AS min_comp_year, MAX(CompYear) AS max_comp_year FROM dbo.CompensateFlow;")
    a("")
    a("-- เอกสารต่อปี — ใช้ประเมินขนาด batch และตั้ง sgi_document_running_numbers ต่อปี")
    a("SELECT LEFT(CompDocumentID, 4) AS doc_year, COUNT(*) AS docs,")
    a("       MAX(CAST(RIGHT(CompDocumentID, 5) AS int)) AS max_running")
    a("  FROM dbo.CompensateFlow WHERE CompDocumentID LIKE '[0-9][0-9][0-9][0-9]/[0-9][0-9][0-9][0-9][0-9]'")
    a("  GROUP BY LEFT(CompDocumentID, 4) ORDER BY doc_year;")
    a("")
    a("-- เอกสารที่ยังไม่จบ (ต้องเดิน workflow ต่อในระบบใหม่) เทียบกับที่จบแล้ว")
    a("SELECT CompStatusCode, COUNT(*) AS cnt FROM dbo.CompensateFlow")
    a("  GROUP BY CompStatusCode ORDER BY cnt DESC;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 7 · ไฟล์แนบ — ต้องรู้ปริมาณและที่อยู่จริงก่อนย้ายขึ้น S3 ของ SBP")
    a("-- ---------------------------------------------------------------------")
    a("SELECT COUNT(*) AS rows_total, SUM(CASE WHEN FlagUpload = 1 THEN 1 ELSE 0 END) AS uploaded,")
    a("       SUM(CASE WHEN FlagDeleteS3 = 1 THEN 1 ELSE 0 END) AS deleted_from_s3,")
    a("       SUM(CAST(ISNULL(FileSize, 0) AS float)) AS total_size,")
    a("       MAX(CAST(ISNULL(FileSize, 0) AS float)) AS max_size")
    a("  FROM dbo.AttachFileProfile;")
    a("SELECT FileType, COUNT(*) AS cnt FROM dbo.AttachFileProfile GROUP BY FileType ORDER BY cnt DESC;")
    a("SELECT StatusCode, COUNT(*) AS cnt FROM dbo.AttachFileProfile GROUP BY StatusCode ORDER BY cnt DESC;")
    a("")
    a("-- ---------------------------------------------------------------------")
    a("-- ส่วนที่ 8 · master ที่ยังไม่มีข้อมูล + คำถามเรื่องอีเมล")
    a("-- ---------------------------------------------------------------------")
    a("-- 8.1 CompetitionProfile — master ยี่ห้อคู่แข่ง · ขอ **ทุกแถว** (ตารางเล็ก)")
    a("--     ปลายทาง sgi_competitors ตอนนี้มี 11 แถวที่ลอกมาจากหน้าจอ ยังไม่เคยเทียบกับฐานจริง")
    a("SELECT CompetitionCode, CompetitionTName, CompetitionEName, CompetitionRemark,")
    a("       CreateDate, CreateBy FROM dbo.CompetitionProfile ORDER BY CompetitionCode;")
    a("")
    a("-- 8.2 MaintainMessage — ในฐาน K2 ไม่มีตาราง email template เลย ตัวนี้เป็นตัวเดียวที่มีโครง")
    a("--     \"หัวเรื่อง + เนื้อความ\" · ขอแค่การกระจายของ MsgType/MsgFormCode ก่อน (ยังไม่ขอเนื้อความ)")
    a("SELECT MsgType, COUNT(*) AS cnt FROM dbo.MaintainMessage GROUP BY MsgType ORDER BY cnt DESC;")
    a("SELECT MsgFormCode, COUNT(*) AS cnt, MAX(LEN(MsgBody)) AS max_body_len")
    a("  FROM dbo.MaintainMessage GROUP BY MsgFormCode ORDER BY cnt DESC;")
    a("SELECT SUM(CASE WHEN Flag = 1 THEN 1 ELSE 0 END) AS active_rows, COUNT(*) AS total_rows,")
    a("       SUM(CASE WHEN MsgBody LIKE '%<html%' OR MsgBody LIKE '%<body%' THEN 1 ELSE 0 END) AS looks_like_email_html")
    a("  FROM dbo.MaintainMessage;")
    a("")
    a("-- 8.3 ช่องผู้รับอีเมลในเอกสาร — มีค่าจริงกี่แถว (ใช้ตัดสินกติกา TO/CC ของระบบใหม่)")
    a("SELECT 'CompCurrentMail' AS col, COUNT(*) AS not_blank FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompCurrentMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreOwnerMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreOwnerMail,''))) <> '' UNION ALL")
    a("SELECT 'CompAllUserMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompAllUserMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreFCMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreFCMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreSectionMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreSectionMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreManagerMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreManagerMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreGMMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreGMMail,''))) <> '' UNION ALL")
    a("SELECT 'CompStoreAVPMail', COUNT(*) FROM dbo.CompensateFlow WHERE LTRIM(RTRIM(ISNULL(CompStoreAVPMail,''))) <> '';")
    a("")
    a("-- =====================================================================")
    a("-- จบสคริปต์ · ส่งผลลัพธ์ทุกส่วนกลับมาได้เลย (ไม่มีข้อมูลส่วนบุคคลในผลลัพธ์")
    a("-- ยกเว้นส่วนที่ 3 ที่เป็นรหัส/สถานะสั้น ๆ)")
    a("-- =====================================================================")
    return "\n".join(L) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = build()
    OUT.write_text(text, encoding="utf-8")
    bad = [k for k in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "TRUNCATE", "ALTER ", "CREATE ")
           if any(k in l and not l.strip().startswith("--") for l in text.split("\n"))]
    print(f"เขียนแล้ว: {OUT.relative_to(ROOT)} · {text.count(chr(10))} บรรทัด")
    print(f"ตาราง core {len(CORE)} · รอตัดสิน {len(DECIDE)} · โดเมน {len(DOMAINS)} · ความยาว {len(LENGTHS)}")
    print("🔒 SELECT ล้วน" if not bad else f"❌ พบคำสั่งที่เขียนข้อมูล: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
