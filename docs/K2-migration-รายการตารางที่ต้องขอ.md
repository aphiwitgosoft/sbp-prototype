# รายการตารางของฐาน K2 ที่ต้องใช้ทำ migration เข้าระบบ SGI — **ครบทั้ง 47 ตาราง**

> สร้างจาก `tools/build_k2_migration_request.py` — **ห้ามแก้ไฟล์นี้ด้วยมือ**
> อ่านรายชื่อตารางจาก DDL จริง (`docs/script_TB_DB_CPA_FRN_FGI_20260722 1.sql`) แล้วบังคับว่า
> **ทุกตารางต้องถูกจัดกลุ่ม** — ถ้ามีตัวไหนไม่ได้จัด สคริปต์จะ error ไม่ยอมสร้างไฟล์
>
> ใช้คู่กับ `docs/K2-database-CPA_FRN_FGI.md` (โครงสร้าง) · `docs/K2-master-data.md` (master ที่ได้แล้ว)
> · `output/sql/k2_migration_profile.sql` (สคริปต์สำรวจ SELECT ล้วน)

## สรุปเป็นตัวเลข

| กลุ่ม | จำนวน | ต้องทำอะไร |
|---|---:|---|
| **A · ขอข้อมูลทุกแถว** | **8** | ✅ **ได้ครบแล้ว 2026-09-16** (`docs/data_bk_all/`) |
| **A′ · อยู่ในกลุ่ม A แต่เป็นตารางว่าง** | **3** | ไม่มีข้อมูลเลยสักแถว — ไม่ต้องขอ |
| **B · ขอจำนวนแถวก่อน แล้วค่อยตัดสิน** | **9** | ยังไม่รู้ว่าต้องย้ายไหม |
| **C · master ที่ได้ข้อมูลแล้ว** | **7** | เป็นแหล่ง migration แต่**ไม่ต้องขอซ้ำ** |
| **D · ไม่ใช้เลย** | **20** | โครงสร้างพื้นฐานของแพลตฟอร์ม K2/BPM |
| **รวม** | **47** | = จำนวนตารางทั้งหมดในฐาน |

## กลุ่ม A′ · อยู่ในกลุ่ม A ตอนแรก แต่ **เป็นตารางว่าง** — 3 ตาราง

ผู้ส่งยืนยัน 2026-09-16 ว่าไม่ได้ตกหล่น — **ไม่มีข้อมูลเลยสักแถวจริง ๆ**

| # | ตาราง | → ปลายทาง | ผลที่ตามมา |
|---:|---|---|---|
| 1 | `FactorInCompenProfile` | `sgi_document_external_factors` | 🔴 ไม่เคยมีใครบันทึกปัจจัยภายนอกลงเอกสารเลย ตลอด 18,007 ฉบับ ปี 2019–2026 |
| 2 | `CompDocAttachment` | `sgi_document_attachments` | ช่องทาง CM/ECM ไม่เคยถูกใช้ |
| 3 | `CompTempAttachment` | `sgi_document_attachments` | ไม่มีไฟล์ชั่วคราวค้าง |

→ ✅ **ไฟล์แนบเหลือทางเดียวคือ `AttachFileProfile`** (11,696 แถว) — งาน migrate ไฟล์แนบง่ายกว่าที่ประเมินไว้
→ 🔴 **ฟีเจอร์ปัจจัยภายนอกไม่เคยถูกใช้เลยตลอด 8 ปี** — ต้องถามธุรกิจว่ายังต้องมีใน SGI ไหม (ข้อค้าง 2.41)

⚠️ **สิ่งที่ต้องขอก่อนข้อมูลเต็ม** — รัน `output/sql/k2_migration_profile.sql` (SELECT ล้วน)
แล้วส่งผลกลับมาก่อน เพราะฐาน K2 **ไม่มี FOREIGN KEY และไม่มี CHECK constraint สักตัว**
ข้อมูลจริงจึงอาจละเมิดทุกกติกาที่ DDL ของ SGI บังคับ (27 CHECK · 28 FK · 19 UNIQUE)

---

## กลุ่ม A · ขอข้อมูลทุกแถว — 8 ตาราง

| # | ตาราง | → ปลายทางใน SGI | ทำไมต้องมี | คอลัมน์ที่ต้องการ |
|---:|---|---|---|---|
| 1 | **`CompensateFlow`** | `sgi_compensation_documents` | หัวเอกสาร 1 แถว = 1 เอกสาร — ตัวตั้งต้นของทั้ง migration | ทุกคอลัมน์ · 25 คอลัมน์สายอนุมัติ (FC/เขต/ฝ่าย/GM/AVP) ลง `approver_snapshot` JSONB |
| 2 | **`CompensateHistory`** | `sgi_consideration_logs + sgi_compensation_histories` | ประวัติพิจารณาทุกขั้น — ไม่ย้าย = เอกสารเก่าไม่มีที่มา | ทุกคอลัมน์ · ⚠️ 3 คอลัมน์มีคำอธิบายในฐานไม่ตรงชื่อ (`ActionFRCCMail` · `OfficeContentURL` · `ActionFRAssignAD`) ต้องดูข้อมูลจริง |
| 3 | **`ImpactProfile`** | `sgi_document_new_stores (+ sgi_fgi_impact_stores)` | คู่ร้าน ถูกกระทบ ↔ เปิดใหม่ + ระยะทาง/รัศมี | ทุกคอลัมน์ · `_N` = ร้านเปิดใหม่ · `_I` = ร้านถูกกระทบ อยู่ในแถวเดียวกัน |
| 4 | **`ImpactCostDetail`** | `sgi_document_cost_details` | เงินชดเชยและ %ต่อร้านเปิดใหม่ | ทุกคอลัมน์ · 🔴 ต้องได้ทั้ง `CostTarget_N`/`Cost_N` (ระบบคำนวณ) และ `_Nc` (คนปรับ) — ขาดคู่ใดคู่หนึ่งแยกไม่ออกว่าใครแก้ |
| 5 | **`CompetInCompenProfile`** | `sgi_document_competitors` | คู่แข่งที่ผูกกับเอกสาร | ทุกคอลัมน์ · `CreateType` 0 = จาก FMS · 1 = ผู้ใช้คีย์เอง → `source_system` |
| 6 | **`RunningNumber`** | `sgi_document_running_numbers` | ตัวนับเลขเอกสารต่อปี | ทุกคอลัมน์ (4) · ตั้ง `last_running_no` ต่อปีให้ต่อจากเลขสูงสุดที่ย้ายมา |
| 7 | **`AttachFileProfile`** | `sgi_document_attachments` | ไฟล์แนบหลัก + สถานะ S3 | ทุกคอลัมน์ · `FlagUpload` `FlagPurgeData` `FlagDeleteS3` `StatusCodeDeleteS3` — โครงใหม่ยังไม่มีวงจรนี้ |
| 8 | **`CompetitionProfile`** | `sgi_competitors` | master ยี่ห้อคู่แข่ง — 🔴 ยังไม่เคยได้ข้อมูล | ทุกแถว (ตารางเล็ก) · `sgi_competitors` ตอนนี้มี 11 แถวที่ลอกจากหน้าจอ **ยังไม่เคยเทียบกับฐานจริง** |

**ไฟล์แนบมี 3 ตาราง ไม่ใช่ตารางเดียว** (`AttachFileProfile` · `CompDocAttachment` · `CompTempAttachment`)
— ต้องรู้ว่าไฟล์จริงของแต่ละตัวอยู่ที่ไหน (S3 ของ K2 / ระบบ CM / ในฐานเอง) เพราะปลายทางเก็บแค่ metadata

## กลุ่ม B · ขอจำนวนแถวก่อน แล้วค่อยตัดสิน — 9 ตาราง

| # | ตาราง | ทำไมต้องตัดสิน |
|---:|---|---|
| 1 | **`MaintainMessage`** | 🔴 ตารางเดียวในฐานที่มีโครง "หัวเรื่อง + เนื้อความ" — ต้องดูว่าเป็นข้อความ popup หน้าจออย่างเดียว หรือมีเนื้อความอีเมลปนอยู่ (`MsgType` จะบอก) |
| 2 | **`CompenOrganizeProfile`** | ผู้ดำเนินการต่อ Section × Zone — ปลายทางใช้ auth-backend ของ SBP แต่ต้องรู้ว่ามีใครบ้างเพื่อตั้ง prepared approver ของ workflow engine |
| 3 | **`MasterUserViewer`** | ข้อมูลพนักงาน 16 คอลัมน์ — ต้องเทียบว่าซ้อนกับ `business_user` ของ SBP แค่ไหน ⚠️ มีข้อมูลส่วนบุคคล |
| 4 | **`CommonConfig`** | config กลาง — มีกลุ่ม `PurgeDay` ที่คุมวงจรลบข้อมูลซึ่งโครงใหม่ยังไม่มี |
| 5 | **`ListDocumentsPendingRemoval`** | วงจร archive → purge ของเอกสาร — **ไม่มีปลายทางในโครงใหม่เลย** ต้องตัดสินว่าจะยกมาไหม |
| 6 | **`TransectionDeleteStore`** | ประวัติการลบร้านออกจากเอกสาร + `SRNumber` — ไม่มีปลายทาง แต่เป็นหลักฐานการแก้ไขย้อนหลัง |
| 7 | **`MonitorAdjust`** | ติดตามการปรับยอด/รอผลคำนวณกลับจาก FS (`CompForecast` · `CompActual` · `KeyCallSMO`) |
| 8 | **`LogCompensate`** | ล็อกการเรียกข้ามระบบ — อาจไม่ต้องย้าย แต่ต้องรู้ปริมาณก่อนตัด |
| 9 | **`LogCompensateReturn`** | ล็อก request/response ขากลับ — เหมือนข้างบน |

## กลุ่ม C · master ที่ได้ข้อมูลแล้ว — 7 ตาราง (ไม่ต้องขอซ้ำ)

ได้จาก `docs/ข้อมูล Master K2.xlsx` เมื่อ 2026-09-16 → ถอดไว้ใน `docs/K2-master-data.md`

| # | ตาราง | → ปลายทาง | สถานะ |
|---:|---|---|---|
| 1 | `FactorProfile` | sgi_external_factors | ✅ ได้แล้ว 7 แถว · ติดตั้งลง dev แล้ว 2026-09-16 |
| 2 | `StatusProfile` | common_code `SGI_DOC_STATUS` | ✅ ได้แล้ว 10 แถว · ใช้แปลงสถานะเก่า → 6 ค่าใหม่ |
| 3 | `SectionProfile` | common_code `SGI_APPROVE_LIMIT` | ✅ ได้แล้ว 10 แถว · ยืนยันเกณฑ์ 100,000 ที่ section 2 (GM) |
| 4 | `DecisionProfile` | common_code `SGI_DECISION` | ✅ ได้แล้ว 14 แถว · ใช้แปลงผลพิจารณาเก่า → 7 ค่าใหม่ |
| 5 | `ZoneProfile` | `mas_zone` ของ SBP | ✅ ได้แล้ว 13 แถว · เป็นตารางแปลงรหัสโซนที่ Job 8b/12 ต้องใช้ |
| 6 | `BranchTypeProfile` | common_code ของ SBP | ✅ ได้แล้ว 8 แถว · มี 3 ชื่อต่อ 1 รหัส (MM/FMS/FGI) |
| 7 | `ApplicationRoles` | auth-backend ของ SBP (ไม่ migrate) | ✅ ได้แล้ว 8 แถว · ใช้อ้างอิงเฉย ๆ |

🔴 **`CompetitionProfile` ไม่ได้อยู่ในกลุ่มนี้** เพราะชีตที่ได้มาไม่มีตารางนั้น — อยู่กลุ่ม A ข้อ 11

## กลุ่ม D · ไม่ใช้เลย — 20 ตาราง

| # | ตาราง | เป็นอะไร |
|---:|---|---|
| 1 | `ActionProfile` | ทะเบียน action ของแพลตฟอร์ม BPM |
| 2 | `ActivityProfile` | ทะเบียน activity ของแพลตฟอร์ม BPM |
| 3 | `ApplicationMenu` | เมนูของเว็บ K2 — ระบบใหม่ใช้เมนูของ SBP portal |
| 4 | `AuthorizedMenu` | สิทธิ์เห็นเมนูรายคน — ตัดตามมติ 2026-08-05 (ใช้ auth-backend) |
| 5 | `FGIHelp` | เนื้อหาหน้า Help ของ K2 |
| 6 | `FormProfile` | โครงฟอร์มของ K2 |
| 7 | `Journal` | ล็อกของแพลตฟอร์ม |
| 8 | `JournalDetail` | ล็อกของแพลตฟอร์ม (รายละเอียด) |
| 9 | `MENU` | โครงเมนู — ตัดตามมติ 2026-08-05 |
| 10 | `MaintainForm` | ทะเบียนฟอร์มของ K2 |
| 11 | `MaintainFormAuthorized` | สิทธิ์ต่อฟอร์มของ K2 |
| 12 | `MaintainHistory` | ประวัติการแก้ฟอร์ม/หน้าจอ ของ K2 |
| 13 | `MaintainMasterHistory` | ประวัติการแก้ master ของ K2 — ระบบใหม่ยังไม่มี audit กลาง (ข้อค้าง DP-12) |
| 14 | `RoleForAuthorizedMenu` | สิทธิ์เห็นเมนูราย role — ตัดตามมติ 2026-08-05 |
| 15 | `ServerMaster` | ทะเบียน server |
| 16 | `ServerType` | ทะเบียนประเภท server (D/U/P) |
| 17 | `TaskList` | โครงฟิลด์ของงาน BPM |
| 18 | `TaskMaster` | โครงงานของแพลตฟอร์ม BPM (48 คอลัมน์ · ไม่มีคำอธิบายสักตัว) |
| 19 | `URLPath` | URL ต่อ environment — ระบบใหม่ใช้ env/config ของ NestJS |
| 20 | `Versions` | เลขเวอร์ชันของแอป K2 |

---

## สิ่งที่ต้องขอเพิ่ม — ไม่ได้อยู่ในฐาน K2

| # | ขออะไร | ทำไม |
|---:|---|---|
| 1 | **source ของ stored procedure `GetRunningNumberSp`** | เป็นคนออกเลขเอกสารจริง แต่**ไม่อยู่ในสคริปต์ DDL ที่ได้มา** · ยังไม่รู้ว่ากันเลขซ้ำอย่างไร (lock / sequence / read-modify-write) |
| 2 | **ไฟล์แนบจริง** — bucket/path + สิทธิ์อ่าน | ฐานเก็บแค่ metadata · ไฟล์ต้องย้ายขึ้น S3 ของ SBP |
| 3 | 🔴 **mapping: transition ไหน → ส่ง email template ไหน** | ตัวที่ตัดสินอยู่ใน workflow engine ของ K2 **ไม่ได้อยู่ในฐาน** · ถ้าไม่ได้อันนี้ ระบบใหม่จะเดาเองว่าสถานะไหนส่งฉบับไหน |
| 4 | กติกาผู้รับ **TO/CC ต่อ transition** | ของเดิมมีช่องผู้รับ 8 ช่องใน `CompensateFlow` + CC 2 ช่องใน `CompensateHistory` |
| 5 | **mapping โดเมนอีเมล → ชื่อโดเมน AD** | trigger เดิมอ่านจาก `BPMCentralMaster.dbo.bpmParameterProfile` ซึ่งไม่มีในระบบใหม่ |

### ✅ เนื้อความอีเมลไม่ต้องขอ — อยู่ในฐาน PostgreSQL ของ SBP แล้ว

`sps_store.email_template` **id 1501010–1501044 = 33 แถว** คือชุด template ของระบบประกันรายได้เดิม
ยืนยันด้วยตัวแปรในเนื้อความที่เป็นชื่อคอลัมน์ของ K2 ตรง ๆ (`${compCurrentUser}` = `CompensateFlow.CompCurrentUser` ฯลฯ)
ในฐาน K2 **ไม่มีตาราง email template สักตัว** — คอลัมน์ที่มีคำว่า mail ทั้งหมดเป็น *ที่อยู่ผู้รับ* ไม่ใช่เนื้อความ

## แหล่งข้อมูล migration มี **สองฐาน** ไม่ใช่ฐานเดียว

| ฐาน | ให้อะไร | สถานะ |
|---|---|---|
| **SQL Server `CPA_FRN_FGI`** (K2) | ฝั่งเอกสาร/อนุมัติ — เอกสารนี้ทั้งฉบับ | 🔴 ยังไม่มีข้อมูล ต้องขอ |
| **Oracle `FCS_FRN`** (FGI/FCS) | ฝั่งคำนวณ — `FGI_IMPACT_*` · `FGI_NEW_STORE_*` · `FGI_CONFIRM_RECEIVE_DATA` | ✅ ได้แล้ว ผ่าน `tools/introspect_legacy_oracle.py` → `output/legacy-oracle/` |

บางตารางปลายทางรับจาก**ทั้งสองฝั่ง** เช่น `sgi_compensation_histories` = 
`FGI_IMPACT_STORE_COMPENSATE` (Oracle) + `CompensateFlow` (K2)

## รูปแบบไฟล์ที่ขอ

- **encoding** — UTF-8 หรือ UTF-16 ก็ได้ แต่**ต้องบอกมาว่าอันไหน** (สคริปต์ DDL ที่ได้มาก่อนหน้านี้เป็น UTF-16LE + CRLF)
- **`NULL` ต้องแยกจากค่าว่าง** — ฐานเดิมมีทั้งสองแบบและความหมายต่างกัน
- **ห้ามตัดศูนย์นำหน้าของรหัสร้าน** (`00788` ไม่ใช่ `788`) — ปลายทางเป็น `VARCHAR(5)`
- คอลัมน์ `datetime` ขอเป็น ISO (`YYYY-MM-DD HH:MM:SS`) และบอกด้วยว่าเป็น **ค.ศ. หรือ พ.ศ.**

⚠️ ข้อมูลกลุ่ม A เป็น **ข้อมูลธุรกิจจริง** (ชื่อร้าน · ชื่อเจ้าของร้าน · อีเมล · ยอดเงิน)
และ `MasterUserViewer` ในกลุ่ม B เป็น **ข้อมูลส่วนบุคคล** — ต้องตกลงช่องทางส่งและที่เก็บให้ชัดก่อน
ถ้าวางในโปรเจกต์นี้ต้องเข้า `.gitignore` เหมือน `docs/file_IAS_STA/` และ `docs/ข้อมูล Master K2.xlsx`
