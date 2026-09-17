# ฐานข้อมูลของระบบ K2 เดิม — `CPA_FRN_FGI` (SQL Server)

> ถอดจาก `docs/script_TB_DB_CPA_FRN_FGI_20260722 1.sql` — สคริปต์ที่ generate จากฐานจริงเมื่อ
> **22/07/2026 15:46:58** · UTF-16LE + CRLF · 2,460 บรรทัด · **47 ตาราง · 575 คอลัมน์ · 4 trigger**
>
> 🔴 **นี่คือฐานของระบบ K2 (As-Is) ที่ SGI กำลังจะแทน** — คนละตัวกับ
> `fcsJar` ที่เป็นฝั่ง Oracle (FGI/FCS batch) และคนละตัวกับ `sps_store` ที่เป็น PostgreSQL ของระบบ SBP
> ระบบเดิมจึงมี **สามฐานสามยี่ห้อ**: SQL Server (K2 · เอกสาร/อนุมัติ) · Oracle (FGI/FCS · คำนวณ) · SQL Server (ALLMAP)
>
> ใช้เพื่อ (1) ตรวจว่าโครง `sgi_*` ใหม่ **รับของเก่าครบ** (2) เป็นพจนานุกรมข้อมูลตอน migrate
> (3) ตอบคำถามที่เอกสาร SRS/SDD ไม่ได้บอก เพราะเจ้าของระบบเขียนคำอธิบายไว้ในฐานเอง

## สมบัติที่ล้ำค่าที่สุดของไฟล์นี้ — คำอธิบายภาษาไทย 432 รายการ

ทีมเดิมใส่ `MS_Description` ไว้ที่ **431 คอลัมน์** (จาก 575 คอลัมน์ · 75%) เป็นภาษาไทย
หลายอันอธิบายกติกาธุรกิจที่ไม่มีในเอกสารเล่มไหนเลย เช่นความหมายของทุกค่า enum
เอกสารฉบับนี้ยกมาเฉพาะที่มีผลกับการออกแบบระบบใหม่

**9 ตารางที่ไม่มีคำอธิบายเลย** — `Journal` · `JournalDetail` · `LogCompensate` · `MonitorAdjust` ·
`RoleForAuthorizedMenu` · `RunningNumber` · `ServerMaster` · `TaskMaster` · `Versions`
(ส่วนใหญ่เป็นตารางระบบ/ล็อก ไม่ใช่ข้อมูลธุรกิจ)

---

## สิ่งที่ไม่มีในฐานนี้เลย — สำคัญพอ ๆ กับสิ่งที่มี

| สิ่งที่ตรวจ | จำนวนที่พบ |
|---|---|
| **FOREIGN KEY** | **0** — ตารางทั้ง 47 ตัวไม่ผูกกันด้วย FK สักเส้น ความสัมพันธ์อยู่ในโค้ดแอปล้วน ๆ |
| **CHECK constraint** | **0** — ค่า enum ทุกตัว (`CompFlagStatus` · `CompType` · `CompStatusCode` …) ไม่มีอะไรบังคับ |
| **index ที่ไม่ใช่ PK** | **0** |
| **PRIMARY KEY** | มี **40 จาก 47 ตาราง** — ที่ไม่มี: `Journal` · `JournalDetail` · `ListDocumentsPendingRemoval` · `MonitorAdjust` · `ServerMaster` · `TaskList` · `TransectionDeleteStore` |
| VIEW / STORED PROCEDURE / FUNCTION | **0 ในไฟล์นี้** — แต่ trigger เรียก `CPA_FRN_FGI.dbo.GetRunningNumberSp` ซึ่ง**ไม่ได้อยู่ในสคริปต์** (สคริปต์นี้ export เฉพาะ table + trigger) |

🔴 **ผลต่อ migration:** ไม่มี FK และไม่มี CHECK แปลว่า **ข้อมูลเดิมอาจละเมิดกติกาที่เราจะใส่ใน DDL ใหม่ได้ทุกข้อ**
ต้องรัน data profiling ก่อน ไม่ใช่เชื่อโดเมนที่คำอธิบายเขียนไว้ (บทเรียนเดียวกับฝั่ง Oracle ที่
`tools/introspect_legacy_oracle.py` + `check_docs.py` กฎ #110 ดักไว้แล้ว)

**พึ่งฐานอื่นข้ามเครื่อง 1 จุด** — trigger `CompensateFlowSetADTr` อ่าน
`BPMCentralMaster.dbo.bpmParameterProfile` (ฐานกลางของแพลตฟอร์ม K2) เพื่อแปลงโดเมนอีเมลเป็นชื่อโดเมน AD
→ **ระบบใหม่ไม่มี BPMCentralMaster** ต้องหาที่มาของ mapping นี้ใหม่ ถ้ายังต้องใช้รูปแบบ `K2:<DOMAIN>\<user>`

---

## 1. `CompensateFlow` — หัวใจของระบบ · 84 คอลัมน์

ตารางเอกสารชดเชย 1 แถว = 1 เอกสาร (ร้านถูกกระทบ × งวด) · PK `CompID` เป็น `uniqueidentifier` (`newid()`)
เทียบเท่า **`sgi_compensation_documents`** ในโครงใหม่

### ค่า enum ที่คำอธิบายในฐานบอกไว้ครบ — ไม่มีในเอกสารเล่มไหน

**`CompFlagStatus`** — flag บอกสถานะการชดเชยรายได้ (ใช้เทียบการ Start Flow รอบเดือนถัดไป · ส่งให้ FMS)

| ค่า | ความหมายตามคำอธิบายในฐาน |
|---|---|
| `I` | อยู่ระหว่างการชดเชย |
| `S` | **หยุดชดเชย** |
| `N` | ไม่ชดเชย & ยกเลิกเอกสาร |
| `A` | **ชดเชย** (กรณีนี้ต้องส่ง %ที่ร้านเปิดใหม่ต้องจ่าย + จำนวนเงิน จาก `ImpactProfile` ไปด้วย) |

🔴 **ตัวอักษรชุดนี้คือชุดเดียวกับที่สัญญา STA (`sgi_impact_store` §2.2) ใช้** — ข้อ **2.39** ใน
`DECISIONS-รอตัดสินใจ.md` ตั้งคำถามว่า `S` ที่ปรากฏในไฟล์ `FRBC0001` จริง 44/56 แถวหมายถึง "หยุด" จริงไหม
**ฐาน K2 ยืนยันว่านิยาม `S` = หยุดชดเชย · `A` = ชดเชย เป็นของเดิมจริง** → คำถามที่เหลือแคบลงเหลือว่า
ทำไมไฟล์จริงถึง**ไม่มี `A` เลยสักแถว** และ `S` ถึงมาพร้อมงวด statement (ดูข้อ 2.39 ที่ปรับแล้ว)

**`CompType`** — ประเภทของการขอชดเชย (รับจาก FMS และต้องส่งกลับไปให้ FMS ด้วย)

| ค่า | ความหมาย |
|---|---|
| `01` | ปกติ เปิดก่อน 01/10/2557 |
| `02` | ปกติ ตั้งแต่ 01/10/2557 |
| `03` | คำนวณไม่ได้ |
| `04` | สร้างเอง |

**`CompDecisionCode`** — `01` ไม่ชดเชย · `02` ชดเชย ฯลฯ · **ได้จากการ update จาก Section ล่าสุดเท่านั้น**
**`CompStoreTypeCode`** — `B` Corporate · `F` Franchise
**`CompStoreManagerAction`** — `N` ยังไม่เคยดำเนินการ · `Y` ผ่านแล้ว · **default `N`** ·
คำอธิบายบอกกติกาตรง ๆ ว่า *"ก่อนที่ ฝ่าย บธฟ. จะส่งให้ ฝ่ายบัญชี จะต้องผ่าน ฝ่าย Operation เสมอ"*
**`CompFlagCalculation`** — `0` รอผลการคำนวณ · `1` ได้รับผลการคำนวณใหม่เรียบร้อย
(ใช้ตอนเจ้าหน้าที่ บธฟ. ปรับผลการประกันแล้วรอ FS คำนวณกลับ — **คือ round-trip ที่โครงใหม่ต้องมีที่เก็บ**)
**`CompFlagSelect` / `CompFlagRedirect`** — `0` แสดงด้านบน · `1` แสดงด้านล่าง ของ List view (กลไกมอบหมายงาน)

### 25 คอลัมน์ = snapshot สายอนุมัติของร้าน ณ เวลานั้น

`CompStoreFC*` · `CompStoreSection*` · `CompStoreManager*` · `CompStoreGM*` · `CompStoreAVP*`
แต่ละชั้นมี 5 คอลัมน์ — `Code` · `Tname` · `Ename` · `Mail` · `AD`

🔴 **นี่คือเหตุผลที่โครงใหม่ต้องมี `approver_snapshot`** — ระบบเดิมแช่แข็งทั้งสายไว้ในเอกสาร
ไม่ได้ join HR ตอนแสดงผล · ถ้าคนย้ายตำแหน่ง เอกสารเก่ายังแสดงคนเดิม (ตั้งใจ ไม่ใช่บั๊ก)
ชั้นที่ระบบเดิมเก็บคือ **FC → เขต → ฝ่าย → GM → AVP** ซึ่ง**ไม่ตรงกับ 5 ขั้น workflow ใหม่** (06 → 08 → 01 → 02 → 03)

### คอลัมน์อื่นที่มีผลต่อการออกแบบ

| คอลัมน์ | ชนิด | ทำไมสำคัญ |
|---|---|---|
| `CompDocumentID` | `nvarchar(10)` | `2016/00001` — **ยืนยันที่มาของรูปแบบเลขเอกสาร `YYYY/xxxxx`** และความยาว 10 ตัวอักษรพอดี |
| `CompWaitingDays` | `int` | จำนวนวันที่ใช้ดำเนินการ (ตัวอย่างในคำอธิบาย: ส่ง 03/09 → ทำ 15/09 = 12 วัน) — **ต้นทางของเกณฑ์เตือนงานค้างของ Job 12** |
| `CompProcessDate` | `date` | วันที่ดำเนินการล่าสุด · *"นำไปใช้คำนวณหาจำนวนวันที่รอดำเนินการเท่านั้น"* |
| `CompMainLoopNo` / `CompLoopNo` | `int` | **ครั้งที่ถูกกระทบ** กับ **รอบที่พิจารณา** เป็นคนละตัว · คำอธิบายยกตัวอย่างละเอียด: หยุดชดเชยแล้วกลับมาชดเชยใหม่ → `MainLoopNo` เพิ่ม, `LoopNo` เริ่มใหม่ |
| `CompForecast` / `CompActual` | `numeric(18,2)` | ยอดจากระบบคำนวณ vs ยอดที่เกิดจริง · **trigger ตั้ง `CompActual = CompForecast` ตอน insert** |
| `CompUrlMap` | `nvarchar(max)` | ลิงก์แผนที่ AllMap (ร้านถูกกระทบเป็นศูนย์กลาง) |
| `CompStatementID` | `nvarchar(max)` | ลิงก์เอกสารยอดชดเชยใน Franchise Statement |
| `CompAllUser` / `CompAllUserMail` | `nvarchar(max)` | **ผู้เกี่ยวข้องทั้งหมดเก็บเป็นข้อความก้อนเดียว** เริ่มจาก Store Organize แล้วต่อท้ายเมื่อมอบหมายงาน — โครงใหม่แยกเป็นแถวแล้ว |
| `CompProcessInstanceID` · `CompSerialNumber` · `BatchID` | | ของแพลตฟอร์ม BPM/K2 — **ไม่ย้าย** (ระบบใหม่ใช้ `@srm/glb-workflow`) |
| `CompReferenceKeyFMS` | `int` | คีย์รับ–ส่งกับ FMS/Franchise Statement |
| `CompFMSCreateDate/By` · `CompFMSUpdateDate/By` | | **audit คู่ขนาน** — แยก "ใครแก้ใน K2" ออกจาก "ใครแก้ใน FS" |
| `CompTransferSBPDate` | `date` | **ไม่มีคำอธิบาย** — คอลัมน์เดียวใน 84 ตัวที่ไม่มี (น่าจะเติมทีหลัง) ต้องถามเจ้าของระบบ |

---

## 2. ตารางลูกของเอกสาร

### `ImpactProfile` (35 คอลัมน์) — คู่ร้าน ถูกกระทบ ↔ เปิดใหม่
ทุกคอลัมน์มีคำอธิบาย · เก็บ **ทั้งสองฝั่งในแถวเดียว** ด้วย suffix `_N` (ร้านเปิดใหม่) และ `_I` (ร้านถูกกระทบ)
มี `ImpStoreDistance` · `ImpStoreRadian` · `ImpStoreRadianUnit` — **ระยะทางและรัศมีรับมาจาก FMS ไม่ได้คำนวณเอง**
→ โครงใหม่แยกเป็น `sgi_fgi_impact_stores` + `sgi_document_new_stores`

### `ImpactCostDetail` (19 คอลัมน์) — เงินชดเชยรายร้านเปิดใหม่
**คู่คอลัมน์ที่สำคัญมาก** — ทุกค่ามีทั้งฉบับ "ระบบคำนวณ" และฉบับ "คนปรับ":

| ระบบคำนวณ | คนปรับแก้ | ความหมาย |
|---|---|---|
| `CostTarget_N` | `CostTarget_Nc` | **%ที่ร้านเปิดใหม่ต้องชดเชย** |
| `Cost_N` | `Cost_Nc` | **จำนวนเงินที่ร้านเปิดใหม่ต้องชดเชย** |

🔴 trigger `SetCompDocumentIDTr` ตั้ง `CostTarget_Nc = CostTarget_N` และ `Cost_Nc = Cost_N` **ตอน insert**
แปลว่า *"ค่าที่คนปรับ" เริ่มต้นเท่ากับ "ค่าที่ระบบคำนวณ" เสมอ* — ถ้าไม่มีใครแก้ สองค่าจะเท่ากันตลอด
→ **ตอน migrate ห้ามตีความว่า `_Nc == _N` แปลว่าไม่เคยมีการแก้** แยกไม่ออกจากกรณีแก้แล้วได้ค่าเดิม
→ เทียบเท่า `sgi_document_cost_details` ในโครงใหม่ · **กติกา %รวม 100% ไม่มี constraint บังคับในฐานเดิม**

### `CompensateHistory` (18 คอลัมน์) — ประวัติการพิจารณาทุกขั้น
`ActionSectionCode` · `ActionStatusCode` · `ActionDecisionCode` · `ActionWaitingDays` · `ActionComment`
→ เทียบเท่า `sgi_compensation_histories` + `sgi_consideration_logs`

⚠️ **มี 3 คอลัมน์ที่คำอธิบายไม่ตรงกับชื่อ** (คัดลอกคำอธิบายผิดตอนใส่ metadata):
`ActionFRCCMail` เขียนว่า *"ข้อมูล Incentive Guarantee"* · `OfficeContentURL` เขียนว่า *"ยอดขายรายเดือนไม่รวมบัตร"* ·
`ActionFRAssignAD` ไม่มีคำอธิบาย → **อย่าเชื่อคำอธิบายสามอันนี้ ต้องดูข้อมูลจริง**

`ActionSendApprove` (`nchar(1)` default `0`) — *"บันทึกการส่ง Draft ไปแล้วจะเป็น 1 · ถ้าวนกลับมา Section นี้อีก จะขึ้นบรรทัดใหม่ที่เป็น 0"*
→ **นี่คือกลไกตรวจว่าเอกสารเคยวนกลับมาขั้นเดิมกี่ครั้ง** ซึ่งข้อ 2.36(4) ถามอยู่ว่าเอกสารเด้งกลับควรนับอายุใหม่ไหม

### `CompetInCompenProfile` (21) — คู่แข่งในเอกสาร
`CreateType`: `0` รับจาก FMS · `1` ผู้ใช้สร้างเอง — **ตรงกับ `source_system` = `ALLMAP`/`USER` ในโครงใหม่**
`CompetitionCode` มีคำอธิบายชัดว่า *"จะมีเมื่อเลือกเพิ่มจากหน้าจอเท่านั้น เพราะทาง All Map ไม่มีรหัสให้"*
→ **ยืนยันมติ 2.22** ที่สรุปว่า `COMPET_ID` จาก ALLMAP ไม่ตรงกับ master 11 รหัส

### `FactorInCompenProfile` (8) — ปัจจัยภายนอกในเอกสาร
`FactorCode` + ช่วงวันที่ `StartDate`/`EndDate` + หมายเหตุ → `sgi_document_external_factors`

### ไฟล์แนบมี **3 ตาราง** ไม่ใช่ตารางเดียว

| ตาราง | ใช้ทำอะไร |
|---|---|
| `AttachFileProfile` (19) | ไฟล์แนบหลัก + **สถานะ S3**: `FlagUpload` · `FlagPurgeData` · `FlagDeleteS3` · `StatusCodeDeleteS3` · `MessageDeleteS3` |
| `CompDocAttachment` (15) | ผูกกับ CM/ECM ภายนอก (`SEQCMID` · `CM_URL`) · มี `DeleteFlage` (สะกดผิดในฐานจริง) |
| `CompTempAttachment` (6) | ไฟล์ชั่วคราวก่อนบันทึกเอกสาร (`FileContent` เก็บตัวไฟล์) |

🔴 **โครงใหม่ `sgi_document_attachments` มี 10 คอลัมน์** (`attach_id` `doc_no` `section_code` `file_name`
`file_size` `storage_provider` `object_key` `scan_status` `scanned_at` `uploaded_at`) —
**ไม่มีวงจรลบไฟล์ออกจาก S3 เลย** ทั้งที่ระบบเดิมติดตามครบ 5 คอลัมน์ · **เรื่องนี้ยังไม่มีในข้อค้างไหน**

---

## 3. กติกาที่ซ่อนอยู่ใน trigger — 4 ตัว

| Trigger | บนตาราง | ทำอะไร |
|---|---|---|
| `RunningNumberTr` | `CompensateFlow` AFTER INSERT | เรียก `GetRunningNumberSp(@CurYear)` มาตั้ง `CompDocumentID` **และตั้ง `CompActual = CompForecast`** |
| `SetCompDocumentIDTr` | `ImpactCostDetail` AFTER INSERT | ย้อนหา `CompDocumentID` จาก `ImpactProfile ⋈ CompensateFlow` ด้วย (`StoreCode_I`, `Year`, `Month`, `ImpReferenceKeyFMS`) แล้วตั้ง `CostTarget_Nc`/`Cost_Nc` |
| `SetImpCompTypeTr` | `ImpactProfile` AFTER INSERT | คัด `CompType` มาจาก `CompensateFlow` |
| `CompensateFlowSetADTr` | `CompensateFlow` AFTER INSERT, UPDATE | แปลง e-mail ของ ฝ่าย/GM/AVP เป็น AD `K2:<DOMAIN>\<user>` โดยอ่านโดเมนจาก `BPMCentralMaster` |

### 🔴 บั๊กจริงใน trigger ทั้ง 4 ตัว — รองรับแถวเดียว

ทุกตัวเขียนแบบเดียวกัน:

```sql
SELECT @ID = D.CompID FROM inserted D     -- ได้มาแถวเดียวเสมอ
UPDATE CompensateFlow SET … WHERE CompID = @ID
```

`inserted` เป็น**ตาราง** ไม่ใช่แถวเดียว — `INSERT` ที่ใส่หลายแถวพร้อมกันจะ**ประมวลผลแค่แถวเดียวเงียบ ๆ**
แถวที่เหลือไม่ได้เลขเอกสาร / ไม่ได้ `CompType` / ไม่ได้ AD

ระบบเดิมรอดมาได้เพราะแอปแทรกทีละแถว (`CompCreateBy` default = `'System BatchJob'`) —
**โครงใหม่ที่ใช้ bulk insert จะเจอทันที** ถ้าลอกตรรกะนี้ไปใส่ trigger

### เลขเอกสารรันจาก **ปีที่แทรกแถว** ไม่ใช่ปีของงวด

```sql
SET @CYeaar = cast(year(getdate()) AS nvarchar(4));
EXEC GetRunningNumberSp @CurYear = @CYeaar, @Ret = @Ret out;
```

→ เอกสารของงวด **ธ.ค. 2025** ที่สร้างในเดือน **ม.ค. 2026** จะได้เลข `2026/xxxxx`
**ต้องยืนยันว่าโครงใหม่ (`sgi_document_running_numbers`) ใช้กติกาเดียวกัน** ก่อนขึ้น UAT
(ปัจจุบัน seed ตั้งแถวเริ่มด้วย `EXTRACT(YEAR FROM CURRENT_DATE)` ซึ่งตรงกัน แต่ไม่มีที่ไหนเขียนไว้ว่าจงใจ)

---

## 4. ตาราง master และปลายทางในระบบใหม่

| ตาราง K2 เดิม | เนื้อหา | ปลายทาง |
|---|---|---|
| `StatusProfile` | รหัส/ชื่อสถานะเอกสาร | `common_code` `SGI_DOC_STATUS` |
| `SectionProfile` | รหัส/ชื่อ Section + **`SectionLimitCost`** (วงเงินต่อขั้น) | `common_code` `SGI_APPROVE_LIMIT` — ⚠️ ระบบเดิมเก็บวงเงิน **ต่อ Section** ส่วนมติ 2026-08-18 ใช้ **เกณฑ์เดียว 100,000** |
| `DecisionProfile` | ตัวเลือกผลพิจารณา · มี 3 ชื่อต่อ 1 รหัส: `DecisionName` (ในตัวเลือก) · `DecisionFlowName` (ในผัง) · `DecisionResultName` (เมื่อจบ เช่น "ประกันรายได้"/"ไม่ประกันรายได้") | `common_code` `SGI_DECISION` — 🔴 **โครงใหม่เก็บชื่อเดียว** ต้องตัดสินว่าจะยุบสามชื่อเป็นหนึ่งหรือเก็บครบ |
| `CompetitionProfile` | master ยี่ห้อคู่แข่ง | `sgi_competitors` |
| `FactorProfile` | master ปัจจัยภายนอก | `sgi_external_factors` |
| `BranchTypeProfile` | ประเภทร้าน · มี **3 ชื่อจาก 3 ระบบ**: `BranchTypeName` (MM) · `BranchTypeFMSName` (FMS) · `BranchTypeFGIName` (FGI) | `common_code` — ⚠️ `BranchTypeFGIName` คือชื่อที่โผล่ใน subject อีเมลของ template เดิม |
| `ZoneProfile` | ภาค/พื้นที่ร้าน | `mas_zone` |
| `CommonConfig` | config กลาง (`Group` + `Name` + `Value` + `Sequence` + `Flag`) | `mas_param` — มีกลุ่ม `PurgeDay` ที่คุมวงจรลบข้อมูล |
| `MaintainMessage` | ข้อความ/popup ในหน้าจอ (`MsgTitle` · `MsgBody` · `MsgType` ต่อ `MsgFormCode`) | **ไม่มีปลายทาง** — โครงใหม่ hardcode ข้อความไทยไว้ในหน้าจอ (verbatim จาก SRS) |
| `CompenOrganizeProfile` | ผู้ดำเนินการต่อ Section × Zone | auth-backend + prepared approver ของ `@srm/glb-workflow` |
| `MasterUserViewer` (16) | ข้อมูลพนักงานเต็ม (หน่วยงาน · ฝ่าย · office · บริษัท · **`EmpSupervisorLevel`** · **`EmpPCGrade`**) | `business_user` |
| `ApplicationRoles` · `AuthorizedMenu` · `ApplicationMenu` · `MENU` · `RoleForAuthorizedMenu` · `MaintainFormAuthorized` | RBAC/เมนู 6 ตาราง | **ตัดทั้งหมด** ตามมติ 2026-08-05 — ใช้ auth-backend ของระบบ SBP เดิม |
| `URLPath` · `ServerType` · `ServerMaster` | URL ต่อ environment (`D`/`U`/`P`) | env/config ของ NestJS |
| `Versions` · `FGIHelp` · `FormProfile` · `MaintainForm` · `MaintainHistory` · `MaintainMasterHistory` · `ActionProfile` · `ActivityProfile` · `TaskMaster` · `TaskList` | โครงสร้างพื้นฐานของแพลตฟอร์ม BPM/K2 | **ไม่ย้าย** |
| `Journal` · `JournalDetail` · `LogCompensate` · `LogCompensateReturn` · `MonitorAdjust` | ล็อกและ monitor การเรียกข้ามระบบ | `integration_log` + `sgi_interface_transactions` |
| `TransectionDeleteStore` (18) | บันทึกร้านที่ถูกลบออกจากเอกสาร + **`SRNumber`** | **ไม่มีปลายทาง** — SDD GI ตัด SR ออกแล้ว แต่ประวัติการลบยังควรเก็บ |
| `ListDocumentsPendingRemoval` (12) | **วงจร archive → purge ของเอกสาร** | **ไม่มีปลายทาง — ดูหัวข้อถัดไป** |

---

## 5. เรื่องที่ระบบเดิมมี แต่โครงใหม่ยังไม่มี

### 5.1 🔴 วงจรเก็บ–ลบข้อมูล (data retention) หายไปทั้งชุด

`ListDocumentsPendingRemoval` อธิบายกลไกไว้ครบในคำอธิบายคอลัมน์:

| คอลัมน์ | กติกาตามคำอธิบายในฐาน |
|---|---|
| `ArchiveDay` | จำนวนวันที่ลูกค้ากำหนดให้ขอลบข้อมูล |
| `ArchiveDate` | วันที่คำนวณไว้ว่าจะย้ายออก คิดจากวันที่ดำเนินการเสร็จสิ้น |
| `FlagArchiveData` | เมื่อถึง `ArchiveDate` → ตั้ง `1` แล้ว **หน้า Landing ไม่แสดงเอกสารนี้อีก** |
| `PurgeDate` | `ArchiveDate` + จำนวนวันจาก **`CommonConfig.Group = 'PurgeDay'`** |
| `FlagPurgeData` | เมื่อถึง `PurgeDate` → ตั้ง `1` = **เตรียมลบได้เลย** |
| `DeleteDate` | วันที่ลบจริง |

และ `AttachFileProfile` ก็มี `FlagPurgeData` · `FlagDeleteS3` · `StatusCodeDeleteS3` · `MessageDeleteS3`
ต่อกับวงจรเดียวกันเพื่อลบไฟล์ออกจาก S3

**โครงใหม่มี `purge_after` + `legal_hold` เฉพาะที่ `sgi_interface_transactions` เท่านั้น**
เอกสารและไฟล์แนบไม่มีอะไรเลย → **ควรตั้งเป็นข้อค้างใหม่** ว่าจะยกวงจรนี้มาไหม
(ถ้าไม่ยกมา ต้องมีคนรับผิดชอบว่าเอกสารเก่าจะค้างในระบบตลอดไปและไฟล์ใน S3 จะไม่มีวันถูกลบ)

### 5.2 คู่ค่า "ระบบคำนวณ" ↔ "คนปรับ" และวงจรคำนวณกลับ

`CostTarget_N`/`_Nc` · `Cost_N`/`_Nc` · `CompForecast`/`CompActual` · `CompFlagCalculation` (0 รอผล / 1 ได้ผลใหม่)
ประกอบกันเป็นวงจร **คนปรับ → ส่งให้ FS คำนวณใหม่ → รับผลกลับ** ที่ `MonitorAdjust` เฝ้าอยู่
(`CompForecast` · `CompActual` · `CompForecast_N` · `CompActual_N` · `KeyCallSMO` · `ReturnOutput`)

โครงใหม่มี `sgi_document_cost_details` แต่ **ยังไม่มีธงบอกว่า "กำลังรอผลคำนวณใหม่อยู่"**
→ ต่อกับข้อ **2.35(1)** ที่ยังหาที่ลงยอดรายร้านจาก STA ไม่ได้

### 5.3 สายอนุมัติ 5 ชั้นของระบบเดิมไม่ตรงกับ 5 ขั้นใหม่

ระบบเดิม snapshot **FC → เขต → ฝ่าย → GM → AVP** (ผูกกับ *ร้าน*)
ระบบใหม่เดิน **06 → 08 → 01 → 02 → 03** (ผูกกับ *หน่วยงาน*)
→ ตอน migrate เอกสารเก่า **ไม่มี mapping ตรงตัว** ต้องตัดสินว่าจะเก็บ snapshot เดิมไว้เฉย ๆ
เป็นข้อความ หรือพยายามแปลง

---

## 6. ข้อสังเกตเชิงคุณภาพข้อมูล (ไว้ใช้ตอนเขียนสคริปต์ migrate)

| เรื่อง | ตัวเลข | ผลที่ตามมา |
|---|---|---|
| `nvarchar(max)` | **114 จาก 575 คอลัมน์ (20%)** รวมทั้งชื่อร้าน · ชื่อคน · ชื่อนิติบุคคล | ความยาวจริงไม่มีเพดาน — **ต้องวัดความยาวสูงสุดจริงก่อนกำหนด `VARCHAR(n)` ในโครงใหม่** ไม่งั้น migrate ล้มกลางทาง |
| `uniqueidentifier` (GUID) | **21 คอลัมน์** · PK ส่วนใหญ่เป็น GUID `newid()` | โครงใหม่ใช้ `BIGSERIAL` — ต้องมีตารางแปลง GUID → id ระหว่าง migrate และเก็บ GUID เดิมไว้อ้างอิงย้อนหลัง |
| COLLATE | **คอลัมน์ข้อความทั้ง 393 ตัวเป็น `Thai_CI_AS` ไม่มีข้อยกเว้น** | **case-insensitive** — การเทียบรหัสร้าน/รหัสพนักงานในระบบเดิมไม่สนตัวพิมพ์ · PostgreSQL เทียบแบบ case-sensitive → **ต้องทำให้เป็นมาตรฐานตอน migrate** ไม่งั้นข้อมูลที่เคยชนกันจะกลายเป็นคนละค่า |
| `CompCreateBy` default | `'System BatchJob'` (มีช่องว่าง) · `CompetInCompenProfile.CreateBy` default `'System_BatchJob'` (มีขีดล่าง) | **สองแบบในฐานเดียว** — อย่ากรอง batch-created ด้วยสตริงเดียว |
| ชื่อคอลัมน์สะกดผิดในฐานจริง | `ActionProfile.ActiontName` · `CompDocAttachment.DeleteFlage` · `TransectionDeleteStore` (ตาราง) | **ห้ามแก้ตอนอ่านฐานเดิม** — ต้องใช้ชื่อผิดตามจริง ไม่งั้นคิวรีพัง |

---

## 7. สิ่งที่ยังตอบไม่ได้จากไฟล์นี้

- **ไม่มีข้อมูลสักแถว** — สคริปต์นี้เป็น DDL ล้วน ไม่รู้จำนวนแถว ไม่รู้โดเมนจริงของ enum
  (ฝั่ง Oracle เรามี `tools/introspect_legacy_oracle.py` แต่ฝั่ง SQL Server **ยังไม่เคยต่อ**)
- **ไม่มี stored procedure** — `GetRunningNumberSp` ซึ่งเป็นคนออกเลขเอกสารจริง ๆ ไม่ได้อยู่ในไฟล์
  **ยังไม่รู้ว่ากันเลขซ้ำอย่างไร** (lock? sequence? read-modify-write?) ต้องขอเพิ่ม
- `CompTransferSBPDate` ไม่มีคำอธิบายและไม่มีที่ไหนอ้างถึง
- 3 คอลัมน์ใน `CompensateHistory` ที่คำอธิบายไม่ตรงชื่อ
- ความสัมพันธ์ระหว่างตารางต้องเดาจากชื่อคอลัมน์ล้วน ๆ เพราะ **ไม่มี FK สักเส้น**

---

## ไฟล์ต้นทาง

```
docs/script_TB_DB_CPA_FRN_FGI_20260722 1.sql   UTF-16LE · CRLF · 2,460 บรรทัด · 345 KB
```

⚠️ อยู่ใน `.gitignore` ตามกฎ `*.sql` ของโปรเจกต์ — clone ใหม่จะไม่มีไฟล์นี้
เอกสารฉบับนี้ commit ตามปกติ · ไฟล์เป็น DDL ล้วนไม่มีข้อมูลธุรกิจ แต่ยังถือเป็นโครงสร้างภายในของระบบจริง
