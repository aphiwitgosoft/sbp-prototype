# ข้อมูลจากฐาน K2 ที่ต้องใช้ทำ migration เข้าระบบ SGI

> ตอบคำถาม *"จะ migrate จากฐาน K2 มา SGI ต้องการข้อมูลตารางไหนบ้าง"* (2026-09-16)
> ตั้งบน `docs/K2-database-CPA_FRN_FGI.md` (โครงสร้าง 47 ตาราง) · `docs/K2-master-data.md` (master ที่ได้แล้ว)
> และตาราง Source-to-Target ที่มีอยู่แล้วใน `LLDD-BE-Data-Migration-Cutover` §5.1

## สรุปสั้น

ฐาน K2 มี 47 ตาราง — **ต้องการข้อมูลจริง 10 ตาราง** (+ master `CompetitionProfile` อีก 1) ·
อีก 9 ตารางขอแค่จำนวนแถวเพื่อตัดสินใจ · ที่เหลือ 19 ตารางเป็นโครงสร้างพื้นฐานของ K2/BPM **ไม่ต้องการเลย**

⚠️ **แต่สิ่งที่ต้องการ *ตอนนี้* ไม่ใช่ข้อมูลเต็ม** — ตอนนี้ต้องการ **ผลสำรวจ (profile)** ก่อน
เพราะฐาน K2 **ไม่มี FOREIGN KEY และไม่มี CHECK constraint สักตัว** ข้อมูลจริงจึงอาจละเมิด
ทุกกติกาที่ DDL ของ SGI บังคับ (26 CHECK · 28 FK · 19 UNIQUE) — ถ้าไม่วัดก่อน full load จะล้มทั้ง batch

สคริปต์สำรวจพร้อมใช้: **`output/sql/k2_migration_profile.sql`**
(สร้างจาก `tools/build_k2_migration_profile_sql.py` · **SELECT ล้วน** · ไม่คืนข้อมูลธุรกิจเป็นแถว ๆ)

---

## 1. ต้องการข้อมูลจริง — 10 ตาราง

| # | ตาราง K2 | คอลัมน์ | → ปลายทางใน SGI | ทำไมต้องมี |
|---|---|---:|---|---|
| 1 | **`CompensateFlow`** | 84 | `sgi_compensation_documents` | หัวเอกสาร 1 แถว = 1 เอกสาร · **ตัวตั้งต้นของทุกอย่าง** |
| 2 | **`CompensateHistory`** | 18 | `sgi_consideration_logs` + `sgi_compensation_histories` | ประวัติพิจารณาทุกขั้น — ถ้าไม่ย้าย เอกสารเก่าจะไม่มีที่มา |
| 3 | **`ImpactProfile`** | 35 | `sgi_document_new_stores` | คู่ร้าน ถูกกระทบ ↔ เปิดใหม่ + ระยะทาง/รัศมี |
| 4 | **`ImpactCostDetail`** | 19 | `sgi_document_cost_details` | เงินชดเชยและ **%ต่อร้านเปิดใหม่** (ทั้งฉบับระบบคำนวณและฉบับคนปรับ) |
| 5 | **`CompetInCompenProfile`** | 21 | `sgi_document_competitors` | คู่แข่งที่ผูกกับเอกสาร |
| 6 | **`FactorInCompenProfile`** | 8 | `sgi_document_external_factors` | ปัจจัยภายนอกที่ผูกกับเอกสาร |
| 7 | **`RunningNumber`** | 4 | `sgi_document_running_numbers` | ตั้งตัวนับต่อปีให้ต่อจากเลขสูงสุดที่ย้ายมา |
| 8 | **`AttachFileProfile`** | 19 | `sgi_document_attachments` | ไฟล์แนบ + สถานะ S3 |
| 9 | **`CompDocAttachment`** | 15 | `sgi_document_attachments` | ไฟล์แนบฝั่ง CM/ECM (`SEQCMID` · `CM_URL`) |
| 10 | **`CompTempAttachment`** | 6 | `sgi_document_attachments` | ไฟล์แนบชั่วคราว (`FileContent` เก็บตัวไฟล์) |

**ไฟล์แนบมี 3 ตาราง ไม่ใช่ตารางเดียว** — ต้องรู้ว่าไฟล์จริงอยู่ที่ไหนของแต่ละตัว
(S3 ของ K2 / CM / ในฐานเอง) เพราะปลายทางเก็บแค่ metadata ส่วนไฟล์ต้องขึ้น S3 ของ SBP

### 1.1 master 8 ตัวก็เป็นแหล่ง migration ด้วย — แต่ส่วนใหญ่ได้ข้อมูลแล้ว

**แก้ 2026-09-16** — ฉบับแรกจัด `FactorProfile` ไว้ใน "ไม่ต้องการ" ซึ่งกำกวม ที่ถูกคือ
**ต้องใช้ แต่ได้ข้อมูลมาแล้ว** จาก `docs/ข้อมูล Master K2.xlsx`

| master ใน K2 | → ปลายทาง | สถานะ |
|---|---|---|
| `FactorProfile` | **`sgi_external_factors`** (ตารางของ SGI เอง) | ✅ **ได้แล้ว 7 แถว · ติดตั้งลง dev แล้ว 2026-09-16** — และเป็นตัวที่จับได้ว่าของเดิมที่เราใช้ 4 รายการเป็นค่าที่คิดขึ้นเอง |
| **`CompetitionProfile`** | **`sgi_competitors`** (ตารางของ SGI เอง) | 🔴 **ยังไม่มีข้อมูล — ต้องขอ** · ชีต xlsx ที่ได้มา **ไม่มีตารางนี้** · ตอนนี้ `sgi_competitors` มี 11 แถวที่ลอกจากหน้าจอ K2 (`k2-competitors.html`) **ยังไม่เคยเทียบกับฐานจริงเลย** |
| `StatusProfile` · `SectionProfile` · `DecisionProfile` | `common_code` (`SGI_DOC_STATUS` · `SGI_APPROVE_LIMIT` · `SGI_DECISION`) | ✅ ได้แล้ว — ใช้เทียบ/แปลงค่าเก่าตอน migrate |
| `ZoneProfile` · `BranchTypeProfile` | `mas_zone` · `common_code` ของ SBP เดิม | ✅ ได้แล้ว — `ZoneProfile` ยังเป็นตารางแปลงรหัสโซนที่ Job 8b/12 ต้องใช้ |
| `ApplicationRoles` | auth-backend ของ SBP (ไม่ migrate) | ✅ ได้แล้ว — ใช้อ้างอิงเฉย ๆ |

🔴 **`CompetitionProfile` จึงเป็นตารางเดียวในกลุ่ม master ที่ยังต้องขอ** — และเป็นความเสี่ยงแบบเดียวกับ
`FactorProfile` เป๊ะ (ข้อมูลที่เราใช้อยู่ลอกมาจากหน้าจอ ไม่ได้มาจากฐาน) · ถ้ารหัส/ชื่อไม่ตรง
`sgi_document_competitors.brand_code` ที่ migrate มาจะอ้าง master ที่ไม่มีอยู่จริง

---

## 2. ขอแค่จำนวนแถว เพื่อตัดสินว่าจะย้ายไหม — 9 ตาราง

| ตาราง | ทำไมต้องตัดสิน |
|---|---|
| `TransectionDeleteStore` | ประวัติการลบร้านออกจากเอกสาร + `SRNumber` · **ไม่มีปลายทางในโครงใหม่** |
| `ListDocumentsPendingRemoval` | วงจร archive → purge ที่โครงใหม่ยังไม่มีเลย (ดู `docs/K2-database-CPA_FRN_FGI.md` §5.1) |
| `MonitorAdjust` | ติดตามการปรับยอด/รอผลคำนวณกลับจาก FS |
| `LogCompensate` · `LogCompensateReturn` | ล็อกการเรียกข้ามระบบ — อาจไม่ต้องย้าย แต่ต้องรู้ปริมาณก่อนตัด |
| `CompenOrganizeProfile` | ผู้ดำเนินการต่อ Section × Zone — ปลายทางใช้ auth-backend ของ SBP แต่ต้องรู้ว่ามีใครบ้างเพื่อตั้ง prepared approver |
| `MasterUserViewer` | ข้อมูลพนักงาน — ต้องเทียบว่าซ้อนกับ `business_user` ของ SBP แค่ไหน |
| `CommonConfig` | config กลาง · มีกลุ่ม **`PurgeDay`** ที่คุมวงจรลบข้อมูล |
| **`MaintainMessage`** | `MsgType` · `MsgTitle` · `MsgBody` · `MsgFormCode` — **ตารางเดียวในฐาน K2 ที่มีโครงแบบ "หัวเรื่อง + เนื้อความ"** · ต้องดูข้อมูลจริงว่าเป็นข้อความ popup หน้าจออย่างเดียว หรือมีเนื้อความอีเมลปนอยู่ด้วย — **ดูข้อ 5.1** |

## 3. ไม่ต้องการเลย — 19 ตาราง

โครงสร้างพื้นฐานของแพลตฟอร์ม K2/BPM และส่วนที่ระบบใหม่ใช้ของ SBP เดิมแทน:

`ActionProfile` · `ActivityProfile` · `ApplicationMenu` · `ApplicationRoles` · `AuthorizedMenu` ·
`MENU` · `RoleForAuthorizedMenu` · `MaintainForm` · `MaintainFormAuthorized` · `MaintainHistory` ·
`MaintainMasterHistory` · `FormProfile` · `FGIHelp` · `Versions` · `URLPath` ·
`ServerType` · `ServerMaster` · `TaskMaster` · `TaskList` · `Journal` · `JournalDetail`

> ⚠️ **master 8 ตัวไม่ได้อยู่ในรายการนี้แล้ว** — ย้ายไปข้อ 1.1 เพราะเป็นแหล่ง migration จริง
> เพียงแต่ได้ข้อมูลมาแล้ว 7 ใน 8 ตัว · RBAC 6 ตารางถูกตัดตามมติ 2026-08-05 (ใช้ auth-backend ของ SBP)

---

## 4. 🔴 สิ่งที่ต้องการ **ก่อน** ข้อมูลเต็ม — ผลสำรวจ 7 ส่วน

รัน `output/sql/k2_migration_profile.sql` แล้วส่งผลกลับมา · **SELECT ล้วน ไม่แตะข้อมูล**

| ส่วน | ถามอะไร | ทำไมต้องรู้ก่อน |
|---|---|---|
| 1–2 | จำนวนแถวของทุกตารางที่เกี่ยว | ประเมินขนาด batch · ตัดสินตารางกลุ่มที่ 2 |
| **3** | **โดเมนของค่าจริง 19 คอลัมน์** (`CompStatusCode` · `CompSectionCode` · `CompDecisionCode` · `CompFlagStatus` · `CompType` · `FactorCode` …) | 🔴 **สำคัญที่สุด** — ปลายทางมี CHECK 26 จุด · ค่าที่โผล่นอกรายการที่เราคาดไว้ = load ล้มทั้ง batch · ฐานเดิมไม่มี CHECK จึงมีค่าแปลก ๆ ได้ทุกแบบ |
| 4 | ความยาวจริงสูงสุดของ `nvarchar(max)` 13 คอลัมน์ | ของเดิมไม่มีเพดาน · ปลายทางเป็น `VARCHAR(n)` — ยาวเกินแม้แถวเดียวก็ load ไม่เข้า (`CompensateFlow` มี `nvarchar(max)` **13 คอลัมน์** รวมชื่อร้าน/ชื่อนิติบุคคล) |
| 5 | คีย์และความสัมพันธ์ | ฐานเดิม **ไม่มี FK สักเส้น** — ต้องวัดเองว่ามีลูกกำพร้าไหม · เลขเอกสารซ้ำไหม · ปีเป็น ค.ศ. หรือ พ.ศ. · รหัสร้านเสียศูนย์นำหน้าไหม · **%ชดเชยรวมได้ 100% จริงไหม** |
| 6 | ช่วงเวลา · เอกสารต่อปี · สถานะปัจจุบัน | ตั้ง `sgi_document_running_numbers` ต่อปี · รู้ว่ามีเอกสารค้าง workflow กี่ฉบับที่ต้องเดินต่อในระบบใหม่ |
| 7 | ไฟล์แนบ — จำนวน · ขนาดรวม · ชนิด · สถานะ | วางแผนย้ายไฟล์ขึ้น S3 ของ SBP |

### คำถามในส่วนที่ 5 ที่คาดว่าจะเจอปัญหา

- **เลขเอกสารซ้ำ** — ปลายทาง `doc_no` เป็น UNIQUE · ของเดิมออกเลขด้วย trigger ที่**รองรับแถวเดียว**
  (`SELECT @ID = D.CompID FROM inserted D`) → insert หลายแถวพร้อมกันเคยได้เลขไม่ครบ
- **ปีในเลขเอกสาร** — ของเดิมรันจาก `year(getdate())` = **ปีที่แทรกแถว ไม่ใช่ปีของงวด**
  เอกสารงวด ธ.ค. ที่สร้างเดือน ม.ค. จะได้เลขปีถัดไป
- **`%ชดเชยรวม = 100%`** — เป็นกติกาธุรกิจแต่ฐานเดิมไม่มีอะไรบังคับ · ปลายทางจะบังคับ
- **`_Nc` กับ `_N`** — trigger ตั้งให้เท่ากันตอน insert จึง**แยกไม่ออกว่าใครเคยปรับจริง**
  ส่วนที่ 5.7 นับให้ว่ามีกี่แถวที่ค่าต่างกันจริง

---

## 5. สิ่งที่ต้องขอเพิ่ม — ไม่ได้อยู่ในฐาน K2

| สิ่งที่ขอ | จากใคร | ทำไม |
|---|---|---|
| **source ของ stored procedure `GetRunningNumberSp`** | ทีมเจ้าของ K2 | เป็นคนออกเลขเอกสารจริง · **ไม่ได้อยู่ในสคริปต์ที่ได้มา** · ยังไม่รู้ว่ากันเลขซ้ำอย่างไร (lock? sequence? read-modify-write?) — ระบบใหม่ต้องรับประกันเรื่องเดียวกัน |
| **ไฟล์แนบจริง** (S3 ของ K2 / CM) | ทีมเจ้าของ K2 + ทีม storage | ฐานเก็บแค่ metadata · ต้องรู้ bucket/path และสิทธิ์อ่าน |
| **mapping โดเมนอีเมล → ชื่อโดเมน AD** | ทีมเจ้าของ K2 | trigger เดิมอ่านจาก `BPMCentralMaster.dbo.bpmParameterProfile` ซึ่ง**ไม่มีในระบบใหม่** |
| ข้อมูลฝั่ง **Oracle FCS_FRN** | — | **ได้แล้ว** ผ่าน `tools/introspect_legacy_oracle.py` → `output/legacy-oracle/` (โซน A ทั้งหมด: `FGI_IMPACT_*` · `FGI_NEW_STORE_*` · `FGI_CONFIRM_RECEIVE_DATA`) |

⚠️ **แหล่งข้อมูล migration มีสองฐาน ไม่ใช่ฐานเดียว** — K2 (SQL Server) ให้ฝั่ง **เอกสาร/อนุมัติ** ·
Oracle FCS_FRN ให้ฝั่ง **คำนวณ FGI/FCS** · บางตารางปลายทางรับจากทั้งสองฝั่ง
(เช่น `sgi_compensation_histories` = `FGI_IMPACT_STORE_COMPENSATE` + `CompensateFlow`)

---

### 5.1 🔴 email template — **ไม่มีตารางไหนในฐาน K2 เก็บไว้เลย**

ไล่ทั้ง 47 ตาราง 575 คอลัมน์แล้ว **ไม่มีตารางชื่อหรือหน้าที่แบบ email template สักตัว** ·
คอลัมน์ที่มีคำว่า mail ทั้งหมดเป็น **ที่อยู่ผู้รับ** ไม่ใช่เนื้อความ:

| ตาราง | คอลัมน์อีเมลที่มี | คืออะไร |
|---|---|---|
| `CompensateFlow` | `CompCurrentMail` · `CompStoreOwnerMail` · `CompAllUserMail` · `CompStoreFCMail` · `CompStoreSectionMail` · `CompStoreManagerMail` · `CompStoreGMMail` · `CompStoreAVPMail` | **ผู้รับ 8 ช่อง** — แช่แข็งไว้ในเอกสารตอน start flow |
| `CompensateHistory` | `ActionAccountCCMail` · `ActionFRCCMail` | ผู้รับสำเนาต่อการดำเนินการ |
| `CompenOrganizeProfile` · `MasterUserViewer` · `AuthorizedMenu` | `CompenOrgEmpMail` · `EmpEmail` · `EMAIL` | อีเมลของคนในทะเบียน |
| **`MaintainMessage`** | `MsgType` · `MsgTitle` · `MsgBody` | **ตัวเดียวที่มีโครง "หัวเรื่อง + เนื้อความ"** — ต้องดูข้อมูลจริง |

### ✅ แต่เนื้อความอีเมลของ K2 **เจอแล้ว — อยู่ในฐาน PostgreSQL ของ SBP ไม่ใช่ใน K2**

`sps_store.email_template` **id 1501010–1501044 = 33 แถว** คือชุด template ของระบบประกันรายได้เดิม
(ดู `docs/IAS-STA-interface-files.md` §4) · ชื่อ template เป็นชื่อ transition ของ K2 ตรง ๆ เช่น
`ManagerFranchiseSendToOfficerFranchise` · `GMOPTIncompensatedAVPOPT` · `AlertWaitingManagerOPT30Days`

**หลักฐานที่ผูกสองฝั่งเข้าด้วยกัน — ตัวแปรในเนื้อความคือชื่อคอลัมน์ของ K2:**

| ตัวแปรใน template | คอลัมน์ในฐาน K2 |
|---|---|
| `${compCurrentUser}` | `CompensateFlow.CompCurrentUser` ✅ |
| `${compStoreCode}` | `CompensateFlow.CompStoreCode` ✅ |
| `${compStoreName}` | `CompensateFlow.CompStoreName` ✅ |
| `${compLoopNo}` | `CompensateFlow.CompLoopNo` ✅ |
| `${branchTypeFGIName}` | `BranchTypeProfile.BranchTypeFGIName` ✅ |
| `${branchTypeI}` | ไม่มีคอลัมน์ชื่อตรง — น่าจะได้จากประเภทร้านฝั่ง `_I` ⚠️ |
| `${link}` | URL ที่ประกอบขึ้นเอง |

→ **ไม่ต้องขอเนื้อความอีเมลจากทีม K2** เพราะอ่านได้จากฐาน dev ที่เราต่ออยู่แล้ว

### สิ่งที่ยัง **ต้องขอ** เรื่องอีเมล

| # | ขออะไร | ทำไม |
|---|---|---|
| 1 | **ข้อมูลจริงของ `MaintainMessage`** | ยืนยันว่าเป็นข้อความ popup หน้าจออย่างเดียว หรือมีเนื้อความอีเมลปนอยู่ด้วย (`MsgType` จะบอก) |
| 2 | 🔴 **mapping: transition ไหน → ส่ง template ไหน** | 33 template มีชื่อบอกใบ้ แต่ **ตัวที่ตัดสินว่าจะส่งอันไหนอยู่ในตัว workflow engine ของ K2 ไม่ได้อยู่ในฐาน** — ถ้าไม่ได้ mapping นี้ ระบบใหม่จะเดาเองว่าสถานะไหนส่งอีเมลฉบับไหน |
| 3 | กติกาผู้รับ TO/CC ต่อ transition | ของเดิมมีช่องผู้รับ 8 ช่องใน `CompensateFlow` + CC อีก 2 ช่องใน `CompensateHistory` — ต้องรู้ว่าแต่ละ transition ใช้ช่องไหนเป็น TO ช่องไหนเป็น CC |

⚠️ **ช่องว่างเชิงออกแบบที่ต้องตัดสิน** — ของเดิมมี **33 template (หนึ่งฉบับต่อหนึ่ง transition)**
แต่ระบบใหม่ออกแบบไว้ **8 ฉบับแบบรวม (EM-01…EM-08)** · ต้องเคาะว่า

- **(ก)** map 33 → 8 (ข้อความจะกลางขึ้น เสียรายละเอียดต่อ transition) หรือ
- **(ข)** ทำ template ต่อ transition เหมือนเดิม (ตรงของเดิมกว่า แต่ต้องดูแล 33 ฉบับ)

ปัจจุบัน seed ลง 8 ฉบับไปแล้ว (id 1501045–1501052) โดย**ยังไม่ได้ตัดสินข้อนี้** และ
`workflow_route.email_id` ของ engine ก็ยังไม่ได้ผูกกับ template ไหนเลย (ทีมเจ้าของ lib เป็นคนตั้ง)

---

## 6. ลำดับที่แนะนำ

1. รัน `k2_migration_profile.sql` ส่งผลกลับมา → เราปรับ DDL/กติกาแปลงให้รับของจริงได้ก่อน
2. ตัดสิน 9 ตารางในกลุ่มที่ 2 (ย้าย / ไม่ย้าย / ย้ายบางส่วน)
3. ขอ dump เต็มของ 10 ตารางในกลุ่มที่ 1 — **UTF-8 หรือ UTF-16 ก็ได้ แต่ต้องบอกมาว่าอันไหน**
   (สคริปต์ DDL ที่ได้มาก่อนหน้านี้เป็น UTF-16LE + CRLF) · คงค่า `NULL` แยกจากค่าว่างไว้
4. ทดลอง load เข้า dev แล้ว reconcile ตาม `LLDD-BE-Data-Migration-Cutover` §5.3

⚠️ ข้อมูลใน 10 ตารางกลุ่มแรกเป็น **ข้อมูลธุรกิจจริง** (ชื่อร้าน · ชื่อเจ้าของร้าน · อีเมล · ยอดเงิน)
ต้องตกลงช่องทางส่งและที่เก็บให้ชัดก่อน · ถ้าวางในโปรเจกต์นี้จะต้องเข้า `.gitignore` เหมือน
`docs/file_IAS_STA/` และ `docs/ข้อมูล Master K2.xlsx`
