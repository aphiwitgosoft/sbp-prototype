# Database — FGI/FCS + K2 (Target Schema ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุปโครงสร้างฐานข้อมูลเป้าหมายของระบบใหม่
> **แหล่งอ้างอิงหลัก:** `plan-database.html` (หน้า DB FGI/FCS + K2)
> **อ้างอิงประกอบ:** `fgi-database.html`, `k2-database.html`, เอกสาร Batch v4.0 (Data Dictionary หน้า 6–10), SRS ประกันรายได้-K2 v3.1, **`script_TB_DB_CPA_FRN_FGI_20260722.sql`** (schema จริงของ K2 เดิม — SQL Server 47 ตาราง · ดูหัวข้อ "ช่องว่างเทียบ DB เดิมของ K2")
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง database ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-database.html` ให้ตรงกัน

## บริบทระบบใหม่

ระบบใหม่ **รวม EAI และ K2 เข้าเป็นส่วนหนึ่งของ SBPGI** — งาน FGI/FCS batch และงานเอกสาร/workflow K2 ทำงานบน **ฐานข้อมูลเดียวกัน** ไม่มีการส่งไฟล์ผ่าน EAI อีกต่อไป (ดูรายละเอียด flow ที่ [workflow.md](workflow.md))

ผลต่อ schema:
- ไฟล์ภายใน `BPM06001O_` (48 ฟิลด์) / `BPM06002O_` / `BPM06003O_` ที่เคยส่งผ่าน EAI ไป K2 → แทนด้วย FK `compensation_documents.impact_process_id` เชื่อมตรงในฐานข้อมูลเดียวกัน
- K2 engine ภายนอก → แทนด้วย **workflow engine กลาง `@srm/glb-workflow` (13 ตาราง ใน schema `sps_store`)** ไม่สร้าง `workflow_instances`/`workflow_tasks` เอง (ตัดออก 2026-08-06)
- ตาราง tracking เดิม `FGI_CONFIRM_RECEIVE_DATA` → แทนด้วย `interface_transactions` (typed FK)
- **SDD v7.5:** ตัดขั้นบัญชี 04/05 ออกจาก workflow — `workflow_sections` เหลือ 5 แถวใช้งาน (06/08/01/02/03) · `document_statuses` เหลือ 6 ค่า (ตัด "รอฝ่ายบัญชี SBP" / "รอบัญชีปฏิบัติการภาค") · บัญชีตรวจสอบผ่านรายงาน SBP Mall + กระทบ SAP นอกระบบ

## ภาพรวม

- **19 ตาราง** ใน Target Schema เดียว (1 schema ใช้ร่วมกัน) — 34 ตารางเดิม **ตัดออก 10 ตารางที่ระบบ SBP ปัจจุบันมีอยู่แล้ว** เมื่อ 2026-08-06 (workflow engine · store/zone/employee master · email template · config — ดูหัวข้อ "ตารางที่ตัดออกรอบ 2" ท้ายไฟล์) แล้ว **ตัดอีก 2 ตาราง** (`job_configs` · `job_run_histories`) เมื่อ 2026-08-06 เพราะตัด 2 tab ควบคุมของหน้า Batch Job (ดูหมายเหตุในโซน C) และ **ตัด `audit_logs`** เมื่อ 2026-08-07 เพราะยกเลิกระบบ audit ของ master
- **3 Data Zones**: A = FGI/FCS Impact Pipeline · B = K2 เอกสาร & Workflow · C = Master/Config ใช้ร่วม
- **4 Core IDs** ใช้ trace งาน (Data Spine)
- มาตรฐานชื่อ: อังกฤษ `lower_snake_case` ทั้ง schema · ป้ายที่มา (FGI/FCS), (K2), (ใหม่) ต้องคงไว้เสมอ
- **ตัดสินใจ 2026-08-05:** RBAC (`roles`/`menus`/`menu_permissions`/`user_accounts`) และผู้ปฏิบัติงาน (`operator_assignments`) **ไม่สร้างใน SBPGI** — ใช้ระบบสิทธิ์/ผู้ใช้ของระบบ SBP เดิม (ดูหัวข้อ "ตารางที่ตัดออก" ท้าย Zone C) · การตัดนี้ทำให้เหลือ 29 ตาราง ก่อนเพิ่มอีก 5 ตารางจากการเทียบ DB เดิมของ K2 (2026-08-06) → รวมเป็น 34
- **ตรวจกับฐานข้อมูลจริงแล้ว 07/08/2026** — ยืนยันว่าโซน A และแกนเอกสารโซน B ไม่มีของเดิมให้ reuse · ดูหัวข้อ [ผลการเทียบกับฐานข้อมูลจริง (07/08/2026)](#ผลการเทียบกับฐานข้อมูลจริง-07082026) และ **ข้อค้างตัดสินใจ 12 ข้อ (DP-1 … DP-12) ที่ยังไม่ตัดสิน** ใน [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4

## Data Spine — เส้นทางข้อมูลหลัก

หนึ่งรายการผลกระทบเดินผ่าน ID หลักตามลำดับ ตารางอื่นเป็นรายละเอียด/master ที่เกาะกับ spine นี้:

| ลำดับ | Zone | Key | ความหมาย |
|---|---|---|---|
| 1 | A | `impact_process_id` | หนึ่งร้านถูกกระทบ + หนึ่งงวด — hub ของยอดขาย ร้านใหม่ และคู่แข่ง |
> **⚠️ Invariant ของ `doc_no` (บันทึก 2026-08-17):** `compensation_documents.doc_no` เป็น **nullable UNIQUE** (มติ DP-1 ให้ PK เป็น `id`) แต่ **ตารางลูก 6 ตัว FK ไป `doc_no` แบบ `NOT NULL`** (`document_new_stores` · `document_external_factors` · `document_competitors` · `document_cost_details` · `document_attachments` · `consideration_logs`)
>
> ⇒ **ต้องออกเลขเอกสารใน INSERT เดียวกับที่สร้างแถวเสมอ** — Job 8 ทำแบบนี้อยู่แล้ว (`INSERT … (doc_no, year, running_no, impact_process_id, …)`) · ถ้าปล่อย `doc_no` ว่างไว้ เอกสารจะเปิด workflow ได้แต่**บันทึกรายละเอียดอะไรไม่ได้เลย** · ถ้าภายหลังธุรกิจต้องการ "เปิดเรื่องก่อนออกเลข" จริง ต้องเปลี่ยน FK ของลูกทั้ง 6 ไปที่ `compensation_documents(id)` ก่อน

| 2 | B | `compensation_documents.id` | **surrogate PK ของเอกสาร (มติ DP-1 = B)** — ค่าที่ส่งเป็น `reference_id` ให้ workflow engine · `doc_no` (`YYYY/xxxxx` ค.ศ.) เป็น **business key แบบ UNIQUE** ที่ผู้ใช้เห็น ไม่ใช่คีย์ที่ engine ยึด |
| 3 | B | `transaction_id` | Workflow instance หนึ่งชุดต่อเอกสาร — **อยู่ที่ `sps_store.workflow_transaction` ของ engine กลาง ไม่ใช่ตารางของ SBPGI** (เดิมเรียก `instance_id`) |
| 4 | B | `approver_id` | งานของแต่ละ Section และผู้รับผิดชอบ — มาจาก `sps_store.workflow_approver` + `GET /api/workflow/pending` (เดิมเรียก `task_id`) |
| 5 | C | `employee_id` | ผู้ปฏิบัติงานที่อ้างร่วมกันทุกขั้น — ตัวตน/สิทธิ์เมนูมาจากระบบ SBP เดิม (auth-backend) ผ่าน user-context header ไม่ใช่ตารางใน SBPGI |

## Data Dictionary (19 ตาราง)

คอลัมน์ **ตารางต้นทาง (Migration)** = ตารางใน DB เดิมที่ต้องดึงข้อมูลมาลงตารางใหม่ ใช้เขียนสคริปต์ import ได้ตรง ๆ · ป้ายกำกับต้นทาง:

- **ORA** = Oracle `FCS_FRN` — `fcs_frn_stqa_schema_20260806.sql` (ฝั่ง FGI/FCS · 707 ตาราง)
- **MSSQL** = SQL Server `CPA_FRN_FGI` — `script_TB_DB_CPA_FRN_FGI_20260722.sql` (ฝั่ง K2 · 47 ตาราง)
- ตารางที่เขียนว่า *ไม่มีต้นทางตรง* ต้อง **derive ระหว่าง migrate** ไม่ใช่ copy · ตารางที่เขียนว่า *sync ต่อเนื่อง* คือ master ของระบบเดิม ห้าม migrate แล้วแยกดูแลเอง
- ลำดับ import ที่ปลอดภัย: master โซน C → โซน A (`fgi_impact_processes` ก่อน แล้วลูกทั้งหมด) → โซน B (`compensation_documents` ก่อน แล้ว `document_*`) → **ท้ายสุดคือการ initialize workflow ผ่าน engine กลาง** (`sps_store.workflow_*` — ไม่ใช่ตารางของ SBPGI แล้ว)

### Zone A · FGI/FCS — Impact Pipeline และ External Interfaces

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `fgi_impact_stores` | FGI/FCS | **ORA** `FGI_IMPACT_STORE` (PK `IMPACT_STORE_ID` · business key `STORECODE_I`+`MONTH`+`YEAR`) | id | `impact_process_id` → fgi_impact_processes · `impacted_store_code` → impacted_stores | คู่ร้านกระทบ–เปิดใหม่ · `verify_status` (W/P/Y/N) · ข้อมูล %/ยอดชดเชยต่อคู่ร้าน |
| `fgi_impact_processes` ★ | FGI/FCS | **ORA** `FGI_IMPACT_STORE_ON_PROCESS` (PK `IMPACT_PROCESS_ID` — seq `SEQ_FGI_IMPACT_PROCESS`) | id | `impacted_store_code` · แม่ของตารางรายรอบทั้งหมด | **hub รอบชดเชย** · `action_status` (Y/W/N) · `last_compensation_amount` · source of truth ของ `workflow_generation_status` (W/Y/N) |
| `fgi_impact_sales_summaries` | FGI/FCS | **ORA** `FGI_IMPACT_STORE_SALES` (key `STORECODE_I`+`MONTH`+`YEAR`) | id | `impact_process_id` → fgi_impact_processes · → sales_transactions (1:N) | หัวยอดขาย · `growth_rate_diff` · `total_working_days` (เกณฑ์ 60 วัน) |
| `sales_transactions` | FGI/FCS | **ORA** `FGI_IMPACT_STORE_SALES_TRN` (key เดียวกับหัว + `SEQ`) | id | `sales_summary_id` → fgi_impact_sales_summaries | ยอดขายรายวันจาก IAS · 4 หน้าต่าง × 15 วัน · sales_diff/outlier ≥ 50 แบบจับคู่ |
| `fgi_impact_competitors` | FGI/FCS | **ORA** `FGI_IMPACT_COMPETITOR` (PK `IMPACT_COMPETITOR_ID`) | id | `impact_process_id` → fgi_impact_processes · → document_competitors (นำเข้า) | คู่แข่งจาก ALLMAP (data_source=ALM) · งวดล่าสุดต่อร้าน |
| `fcs_qssi_score` | FGI/FCS | **ORA** `FCS_QSSI_SCORE` (`STORE_ID`+`CATEGORY`+`MONTH`+`YEAR`) — ⚠ **ไม่ต้อง migrate ใหม่ ของเดิมมีข้อมูลครบแล้ว** | id | UK: store_id + category_code + งวด (**ยังไม่มีจริงในของเดิม** — ดู DP-4) | คะแนน QSSI 6 หมวด (8,9,12,1,10,16) จาก Job 1 — **มีอยู่จริงใน `sps_store.fcs_qssi_score` (ชื่อ *เอกพจน์*) 23,958,780 แถว · 7 คอลัมน์** (`SBP/db-schema-sps_store.md`) และมี **import pipeline ที่ทำงานอยู่แล้ว**: `POST /performance/import-qssi` + staging `fcs_tmp_qssi_score` + `performance.service.ts` → **ห้ามสร้างตาราง/entity ใหม่ ให้ reuse ของเดิม** · ชื่อพหูพจน์ `fcs_qssi_scores` **ผิด ห้ามใช้** · ข้อจำกัดที่ต้องปิด: 4 คอลัมน์คีย์ (`store_id`/`category`/`month`/`year`) เป็น **nullable** · index มีแค่ `fcs_qssi_score_pkey` บน `id` → **จะแก้ตารางเดิมอย่างไรยังไม่ตัดสิน (DP-4 · ต้อง sign-off เจ้าของ `performance.service.ts`)** · `fcs_qssi_score_bak_20260710` (18,577,924 แถว) เป็น snapshot **ห้ามอ่าน/ห้าม join** |
| `interface_transactions` | ใหม่ | **ORA** `FGI_CONFIRM_RECEIVE_DATA` — ⚠ `TRANSACTION_PK` เป็น polymorphic ต้องแตกตาม `DATA_NAME` เป็น typed FK ตอน migrate | id | typed FK: `impact_process_id` / `sales_summary_id` / `doc_no` | แทน FGI_CONFIRM_RECEIVE_DATA — เลิก polymorphic PK + purge ทำงานจริง · **คอลัมน์ `last_ack_notified_on` (DATE · ใหม่ 2026-08-07)** — marker กันงาน watchdog ส่งอีเมลเตือนซ้ำในวันเดียวกัน (ย้ายมาจาก `audit_logs` ที่ถูกยกเลิก) (แก้ E20) · **ยังไม่ตัดสิน (DP-6)** ว่าจะออกแบบใหม่ หรือลอกแพตเทิร์น `statement_summary` ของระบบเดิม — [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4 |

### Zone B · K2 — เอกสารประกันรายได้และ Workflow ภายใน

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `compensation_documents` | K2 | **MSSQL** `CompensateFlow` (PK `CompDocumentID` → `doc_no`) + join **ORA** `FGI_IMPACT_STORE_INFO` เพื่อเติม `impact_process_id` | **`id` (surrogate · มติ DP-1 = ทางเลือก B 2026-08-10)** · `doc_no` เป็น **UNIQUE** ไม่ใช่ PK | `status_code` · `current_section_code` · `impacted_store_code` · **`impact_process_id` (ใหม่)** | เอกสารประกันรายได้ — หัวใจโซน B · FK ใหม่เชื่อม hub โซน A แทนไฟล์ 48 ฟิลด์ · **คอลัมน์ที่เติมจาก CompensateFlow เดิม (2026-08-06):** `round_no`/`loop_no` (= CompMainLoopNo/CompLoopNo — หน้าจอแสดง "รอบ 1 · ครั้งที่ 3") · `allmap_url` (= CompUrlMap — ปุ่ม Link To ALLMAP) · **`statement_id`** (= CompStatementID — โยงกลับ SBP Statement ที่เป็นต้นทางการสร้างเอกสารตามกระบวนการ FS ใหม่) · **`statement_date` (ใหม่ 2026-08-06)** — วันที่ของ SBP Statement เก็บเป็น **ค.ศ.** เพราะรายงานตรวจสอบประกันรายได้ตาม **SDD สไลด์ 60** ใช้ตัวกรอง Period Statement เป็นช่วง **วัน/เดือน/ปี (ค.ศ.)** และแสดงเป็นคอลัมน์ "Period Statement" ในผลลัพธ์ 14 คอลัมน์ · `account_year`/`account_month` (งวดบัญชี) · `approver_snapshot` (JSONB — FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร ตามที่ CompensateFlow เก็บไว้ 25 คอลัมน์: **จำเป็นเป็นพิเศษเมื่อ RBAC ย้ายไปใช้ระบบเดิม เพราะตำแหน่งจาก HR Connect เปลี่ยนได้ และผู้รักษาการเป็นผู้อนุมัติไม่ได้**) |
| `document_new_stores` | K2 | **MSSQL** `ImpactProfile` (ฝั่ง `_N`) + **ORA** `FGI_NEW_STORE_INFO` / `FGI_NEW_STORE_COMPENSATE` (%ชดเชย + ยอดต่อร้าน) | id | `doc_no` → compensation_documents | ร้านเปิดใหม่ · `distance_km` · `compensate_percent` (**ผลรวมต้อง = 100%**) · `compensate_amount` (ใหม่ — ยอดชดเชยร้านถูกกระทบ × %ชดเชย คำนวณ/ปัดเศษที่ BE · ผลรวมทุกแถวต้องเท่ากับยอดชดเชยของเอกสารพอดี · แสดงในคอลัมน์ "เงินชดเชย (ร้านใหม่)" ของตารางร้านเปิดใหม่ — **กราฟสัดส่วนเงินชดเชยถูกถอดออก 2026-08-06**) |
| `document_competitors` | K2 | **MSSQL** `CompetInCompenProfile` (+ ไฟล์ `BPM06003O_` 14 ฟิลด์) | id | `doc_no` · `competitor_code` → competitors | คู่แข่งในเอกสาร **ระดับสาขา** · `source_system` = ALLMAP (จาก pipeline) / USER (ผู้ใช้เพิ่มเอง) · **คอลัมน์ที่ยืนยันจากไฟล์จริง (2026-08-06):** `competitor_code` เป็นรหัสจาก **ALLMAP** แบบตัวเลข/ตัวอักษรผสม (`4832`, `TD58_08`, `LS3550`) — **ไม่ใช่** รหัสแบรนด์ 01–11 · `branch_name` (ชื่อสาขาคู่แข่ง เช่น "ตลาดศรีวานิช") · `zone_code` + `subzone_code` (01–07) · `open_date`/`close_date` ของคู่แข่ง (ดู `docs/K2-interface-files.md`) |
| `document_external_factors` | K2 | **MSSQL** `FactorInCompenProfile` | id | `doc_no` · `factor_code` → external_factors | ปัจจัยภายนอกที่ใช้ในเอกสาร + ช่วงวันที่ |
| `consideration_logs` | K2 | **MSSQL** `CompensateHistory` (PK `ActionID`) | id | `doc_no` → compensation_documents | ประวัติพิจารณาทุกขั้น (ผู้พิจารณา · Section · ผล · เวลา) · `result_category` (APPROVE/REJECT/**CANCELLED**/PENDING) สำหรับ filter **ประกันรายได้ / ไม่ประกันรายได้ / ยกเลิกโดยระบบ / ยังไม่มีผล** หน้ารายงานตรวจสอบประกันรายได้ (k2-report · SDD v7.5) · **ยังไม่ตัดสิน (DP-7)** ว่าตารางนี้เป็น timeline เต็ม หรือเป็นตารางส่วนขยายบน `sps_store.workflow_history` ของ engine (engine เก็บ timeline แต่ไม่มีรหัสผลพิจารณา/ไฟล์แนบ) — กระทบ `GET /documents/{docNo}/timeline` โดยตรง · [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4 |
| `document_attachments` | K2 | **MSSQL** `CompDocAttachment` + `CompTempAttachment` (+ `AttachFileProfile` สำหรับสถานะอัปโหลด/purge) | id | `doc_no` → compensation_documents | ไฟล์แนบ ≤ 5MB ต่อไฟล์ · แยกตาม Section ที่แนบ · **เติมจาก AttachFileProfile เดิม (2026-08-06):** `file_size` · `upload_status` + `upload_message` (ผลอัปโหลดขึ้น object storage) · `purge_flag`/`storage_delete_status` (lifecycle ลบไฟล์บน S3 — ของเดิมมี FlagPurgeData/FlagDeleteS3/StatusCodeDeleteS3 ครบ) |
| `compensation_histories` | K2 | **ORA** `FGI_IMPACT_STORE_COMPENSATE` + **MSSQL** `CompensateFlow` (แถวรอบก่อนหน้าของร้านเดียวกัน) | id | `store_code` · `ref_doc_no` | ประวัติชดเชยต่อร้าน/รอบ · `submit_account_month` เดือนส่งบัญชี (→ ไฟล์ FRBC0001 ของ Job 6) · ⚠ **ต้องตัดสิน DP-11 ก่อนสร้างตารางนี้** — SBPGI เป็นต้นทางตัวเลขเงินประกันรายได้ หรือ `fr_store_insure` ยังคีย์มือ (ข้อธุรกิจล้วน) · [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4 |
| `document_cost_details` ★ | K2 (ImpactCostDetail) | **MSSQL** `ImpactCostDetail` (PK `ImpCostID`) | id | `doc_no` → compensation_documents · `new_store_code` | **(เพิ่ม 2026-08-06)** ยอดชดเชย**แยกรายเดือน/รายร้านเปิดใหม่** — `cost_year`/`cost_month` · `cost_target` (เป้ายอดขาย) · `cost_amount` · แยกค่าของร้านใหม่ (`_n`) และร้านใหม่สะสม (`_nc`) ตาม ImpactCostDetail เดิม · ของเดิมในโครงเรามีแค่ยอดรวมต่อเอกสาร + %ต่อร้าน ทำให้ทวนยอดรายเดือนกับ Statement/SAP ไม่ได้ |
| `document_running_numbers` ★ | K2 (RunningNumber) | **MSSQL** `RunningNumber` | `year` | ออกเลขให้ compensation_documents | **(เพิ่ม 2026-08-06)** ตัวนับเลขเอกสารต่อปี **ค.ศ.** (`last_running_no`) — ปีเป็น ค.ศ. ตามมติ 2026-08-06 (ดู `api.md`) **ห้ามเก็บ พ.ศ.** — ออกเลข `YYYY/xxxxx` แบบ atomic (`UPDATE … RETURNING` / row lock) กันเลขชนกันเมื่อ batch และผู้ใช้สร้างพร้อมกัน · เดิมโครงเราไม่ระบุที่เก็บตัวนับ |

### Zone C · Shared — Master ที่ SBPGI เป็นเจ้าของ

(RBAC/ผู้ใช้/config/email template/workflow → ใช้ของระบบ SBP เดิม · audit ยกเลิก 2026-08-07)

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `impacted_stores` | K2 | **ORA** `FGI_IMPACT_STORE` (ฝั่ง `_I` · distinct) + **MSSQL** `CompensateFlow.CompTransferSBPDate` | `store_code` | = `impacted_store_code` ของโซน A (สะพานหลักสองระบบ) · subset SP ของ `stores` | ข้อมูลร้าน SP master · **`transfer_sbp_date` (เพิ่ม 2026-08-06 = CompTransferSBPDate เดิม)** — วันที่โอนเป็นร้าน SP ใช้กับเงื่อนไขร้านก่อน/หลัง 1/10/2014 ของ Approve Flow เดิม · **มติ DP-3 (2026-08-10) = ตาราง snapshot บางส่วน** — เก็บ**เฉพาะร้านที่เคยเข้ารอบชดเชยจริง** (ไม่ sync ทั้ง master 11,583 แถว) เติมทีละแถวแบบ upsert ตอน pipeline สร้าง `fgi_impact_processes` · เหตุผล: `v_fr_store_active` ตัดร้านที่ยกเลิกเกิน 1 เดือนออก → ถ้าใช้ view เอกสารย้อนหลังจะกลายเป็น "ไม่พบร้าน" · snapshot ของ SBPGI — กระทบทั้ง DDL และขอบเขต migration · [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4 |
| `external_factors` | K2 · SRS 3.1.9 | **MSSQL** `FactorProfile` | `factor_code` | ← document_external_factors | ปัจจัยภายนอก master · รหัสห้ามซ้ำ |
| `competitors` | K2 | **MSSQL** `CompetitionProfile` (+ **ORA** `MAS_STORE_COMPETITOR`) | `competitor_code` | ← document_competitors | **master แบรนด์ร้านคู่แข่ง 11 รายการ** (รหัส `01`–`11`) · `name_th` + `name_en` (ระบบเดิมเก็บทั้งไทยและอังกฤษ) — จัดการที่หน้าจอ `k2-competitors.html` (เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม) · **คนละระดับกับ `document_competitors`** ที่เก็บ *รายสาขา* ของคู่แข่งพร้อมรหัสจาก ALLMAP (เช่น `4832`, `TD58_08`) + ชื่อสาขา + zone/subzone (ดู `docs/K2-interface-files.md`) |

> **Batch Job — ตัด 2 tab ควบคุมออก (2026-08-06):** ตาราง `job_configs` และ `job_run_histories` **ถูกลบจาก target schema** พร้อมกับลบ API กลุ่ม Batch Job Admin 6 เส้น · หน้า `job-batch.html` **ย้ายไปกลุ่มเมนู `Flow` ชื่อ "Flow Batch Job" และเหลือเฉพาะ 2 แท็บ `Flowchart การทำงาน` + `Database ที่ใช้`** (ตัดแบบฟอร์มพารามิเตอร์ · ประวัติการรัน · ปุ่มสั่งรัน/เปิด-ปิด job · stat cards · กราฟ · การ์ด audit ออกทั้งหมด) — เป็นเอกสารอ้างอิงสำหรับผู้พัฒนา ไม่ใช่หน้าจอควบคุม · **batch job ทั้ง 11 entry point ยังทำงานตามปกติ** แต่พารามิเตอร์/ตารางเวลากำหนดใน **backend config** (config file/env ฝั่ง BE) และผลการรันเก็บที่ application log + `interface_transactions` แทน · ถ้าทำ 2 tab ควบคุมใน phase ถัดไป ให้กลับมาเพิ่ม 2 ตารางนี้พร้อม endpoint กลุ่มเดิม

> **✅ ปิด DP-5 (แก้มติ 2026-08-14) — workflow ให้ "เลข template" · SBPGI เป็นคนเรียก lib ส่งเอง**
>
> **ไม่มีตารางใหม่** — `status_email_rules` ยังถูกตัดตามเดิม (19 ตารางไม่เปลี่ยน) เปลี่ยนเฉพาะ **ใครเป็นคนเรียก**
>
> **แหล่งความจริง:** `SBP/TSM-SRM-LLDD SBP EMAIL1.0.xlsx` (v1.0 · 15/09/2025 · Sukol K.) — lib ส่งอีเมลกลาง **ทำเสร็จและใช้งานจริงแล้ว** ให้ module อื่น import
>
> **สัญญาที่ต้อง code ตาม** (ชีต Detail + MermaidSeq):
>
> ```ts
> emailService.sendEmail({
>   emailId,     // เลข template — SBPGI อ่านจาก sps_store.workflow_route.email_id ของ route ที่เพิ่งเดิน
>   mailTo,      // 'a@x.co.th,b@y.co.th'  หลายเมลคั่นด้วย ,
>   mailCc,      // เดียวกัน (ว่างได้)
>   param,       // { docNo:'2026/00123', storeName:'...', amount:'12,500' } → lib แทนค่า {{key}} ใน subject/body
>   fileAttach,  // ไฟล์แนบ (ไม่ถูก log — ดูข้อจำกัด)
>   userId,      // ผู้ดำเนินการ → ลง email_sent.send_by
> })
> ```
>
> ลำดับใน lib: `findById(emailId)` → แทนค่า `{{key}}` ใน subject/body → ส่งผ่าน SMTP/AWS SES → `INSERT email_sent` (`is_sent='Y'` หรือ `'N'` + `error`) → return `Success` / `Fail`
>
> **ทำไมไม่ใช่ engine ส่ง:** input ของ `eventWorkflow` มีแค่ `versionId · referenceId · event · eventParam · remark · userData · userFullname · nextApproverId` — **ไม่มี `mailTo`/`mailCc`/`param`/`fileAttach`** engine จึงเติมอาร์กิวเมนต์ที่ `sendEmail` บังคับไม่ได้ · และบรรทัด *"เรียก function ส่งเมล์จาก lib ....."* ในชีต 2 ของ LLDD workflow ยังเป็น **placeholder `.....` ที่ยังไม่เติมชื่อ function**
>
> **ผู้รับมาจากไหน (ไม่ต้องมีตารางกฎ):** `mailTo` = ผู้อนุมัติลำดับถัดไปที่ engine resolve แล้ว (`workflow_transaction.current_approver` / `workflow_approver.current_approver` → ขยายกลุ่มด้วย `workflow_group_map`) → อีเมลจาก **`business_user.email`** · `mailCc` = **`fml_email_account`** (1,646 แถว · มีคอลัมน์ `template_id` → เป็นกลไก "ใครรับ template ไหน" ของระบบเดิมอยู่แล้ว ไม่ต้องสร้างตารางกฎใหม่)
>
> **สิ่งที่ปลดล็อกได้จากมติใหม่:** อีเมลเตือนงานค้างรายสัปดาห์ + escalation 30/45/60 วัน **ไม่ใช่ transition** จึงไม่มี route ให้แขวน `email_id` — เดิมเป็นรูโหว่ของ DP-5 · ตอนนี้ SBPGI ส่งเองได้ โดยเก็บเลข template ของเมลกลุ่มนี้ไว้ที่ **`mas_param`** (ไม่ hardcode)
>
> ⚠️ **ข้อจำกัด/กับดักที่ dev ต้องรู้** (รายละเอียดเต็มใน [`api.md`](api.md) §อีเมล):
> 1. ชื่อคอลัมน์จริงคือ **`email_sent.send_by`** ไม่ใช่ `sent_by` ตามที่เขียนในชีต Detail — เขียนตามเอกสารแล้ว query พัง
> 2. `email_template` จริงใน `sps_store` มี **12 คอลัมน์** (`email_template_id` · `email_template_name` · `email_template_desc` · `subject_format` · `body_format` · `sender` · `email_from` · `active_flag` · `create_by/date` · `update_by/date`) — **ชื่อในชีต Database ของเอกสาร lib (`email_id`/`email_name`/`subject_mail`/`body_mail`/`mail_from`/`mail_from_name`) เป็นชื่อที่เสนอไว้ ไม่ตรง production** · seed template ของ SBPGI ต้องใช้ชื่อจริง
> 3. `sendEmail` คืนแค่ `Success`/`Fail` **ไม่คืน `email_sent_id`** และ **lib ไม่ retry ให้** — ส่งอีเมล**นอก transaction** ของ action เสมอ (อีเมลล้มต้องไม่ rollback การอนุมัติ) แล้วตามเก็บด้วยรายงาน `email_sent WHERE is_sent='N'`
> 4. `fileAttach` เป็น input แต่ `email_sent` **ไม่มีคอลัมน์เก็บไฟล์แนบ** — ห้ามใช้ `email_sent` เป็นหลักฐานว่าแนบไฟล์ไปแล้ว
> 5. 🔴 **ต้องยืนยันกับทีมเจ้าของ `@srm/glb-workflow`:** ถ้า engine ส่งเมลเองด้วยบน route ที่มี `email_id` ผู้อนุมัติจะได้ **เมลซ้ำ 2 ฉบับ** — ทางแก้คือใช้ `workflow_route.email_id` เป็น *ค่าอ่านอย่างเดียว* ให้ SBPGI ไปเรียก lib เอง และให้ฝั่ง engine ปิดการส่ง

### Seed data ที่ต้องใส่ลงตารางของระบบ SBP เดิม (มติ 2026-08-17)

SBPGI **ไม่สร้างตารางใหม่** สำหรับ 3 ชุดนี้ แต่ต้อง **INSERT แถวของตัวเอง** ลงตารางของระบบเดิม — **ทีม SBPGI เป็นผู้ทำเอง**

| ชุด | ตารางปลายทาง (`sps_store`) | ผู้รับผิดชอบ | ขอบเขตที่อนุญาต |
|---|---|---|---|
| **Email template 8 ฉบับ** (EM-01…EM-08) | `email_template` (เดิม 85 แถว) | **Butsaba \<But\> Podamrong** | `INSERT` แถวใหม่ + `active_flag='Y'` เท่านั้น · ห้าม `UPDATE`/`DELETE` 85 แถวเดิม · ต้องใช้ชื่อคอลัมน์จริง (`email_template_name` · `subject_format` · `body_format` · `sender` · `email_from`) |
| **Workflow version เริ่มต้น 1 ชุด** | **10 ตารางนิยาม** ของ engine (จาก 13 ตาราง — อีก 3 ตัว `workflow_transaction`/`workflow_history`/`workflow_approver` เป็น runtime ที่ lib เขียนเอง ห้ามแตะ): (`workflow` · `workflow_version` · `workflow_state` · `workflow_status` · `workflow_event` · `workflow_route` · `workflow_group` · `workflow_group_map` · `workflow_part` · `workflow_part_display`) | **Aphiwit \<Bank\> Khammoon** | `INSERT` **version ใหม่หมายเลขเดียว** ของ SBPGI · 🔴 ห้ามแตะ version ของระบบอื่นเด็ดขาด (`workflow_transaction` 19,283 แถวใช้ร่วมกันทั้งองค์กร) · `workflow_route.email_id` ผูกเลข template จากชุดบน |
| **`SBPGI_APPROVE_LIMIT` + `SBPGI_DECISION`** | `common_code` (+ `common_code_type`) | **Aphiwit \<Bank\> Khammoon** | `INSERT` เฉพาะ `code_type` ที่ขึ้นต้นด้วย `SBPGI_` · ห้ามแตะ code_type ของโมดูลอื่น |

**กติกาที่ทั้ง 3 ชุดต้องทำตาม:**
- ทำผ่าน **migration script ของ SBPGI** (versioned · rerun ได้ · มี rollback) ไม่ใช่คีย์มือบน production
- ทุก statement เป็น `INSERT` เท่านั้น — ไม่มี `UPDATE`/`DELETE`/`ALTER` บนข้อมูลเดิม ตามกติกา **"ไม่แก้ระบบเดิม"**
- แจ้งทีมเจ้าของ (`email-lib` · `@srm/glb-workflow` · store-backend) ให้ review script ก่อนรัน แม้จะรันเอง
- ⚠️ ยังต้องได้คำยืนยันจากทีม `@srm/glb-workflow` ว่า **engine ไม่ส่งอีเมลเอง** บน route ที่มี `email_id` ไม่งั้นผู้อนุมัติได้เมลซ้ำ 2 ฉบับ (ดู [`api.md`](api.md) §อีเมล ข้อ 5)

### ตารางที่ตัดออก — ใช้ระบบ SBP เดิมแทน (ตัดสินใจ 2026-08-05)

SBPGI เป็น backend ใหม่ที่จะเสียบเข้าสถาปัตยกรรม SBP ปัจจุบัน (FE → BFF → backend ต่อโดเมน) ซึ่งมีระบบผู้ใช้/สิทธิ์อยู่แล้ว จึง**ไม่สร้างตาราง RBAC/ผู้ปฏิบัติงานของตัวเอง** — หน้าจอ `k2-permissions.html` (SRS 3.1.1) และ `k2-operators.html` (SRS 3.1.8) ถูกถอดออกจาก sidebar ของ prototype (ไฟล์ยังเก็บไว้อ้างอิง):

| ตารางที่ตัด (5) | แทนด้วยของระบบเดิม |
|---|---|
| `roles` / `menus` / `menu_permissions` | auth-backend (ABS): `groups` / `menus` / permissions ต่อ URL (`canView/canManage/canExport/canOther`) — จัดการผ่านหน้า `/setting/manage-user-rights` ของ FE เดิม · BFF ส่งสิทธิ์มากับ header `x-user-permissions` |
| `user_accounts` | AWS Cognito + auth-backend `users`/`user_group_memberships` — SBPGI รับตัวตนจาก BFF ผ่าน header `x-user-id`/`x-user-group-id` ไม่เก็บบัญชีเอง |
| `operator_assignments` | จับกลุ่มผู้ปฏิบัติงานต่อ section/พื้นที่ด้วย group + scope ของ auth-backend (แบบเดียวกับ `business_user_group` ของ store-backend) · การผูกผู้อนุมัติรายเอกสารใช้ pattern prepared approvers ของ workflow engine เดิม (`@srm/glb-workflow` — `AddPreparedApproverUseCase`) |

ผลที่ตาม: 8 role (00–10) ของ SRS ถูก map เป็น group ใน auth-backend · `workflow_tasks.assignee_employee_id` ยังอยู่ (เก็บผลการ resolve แล้ว) แต่แหล่งข้อมูลการ resolve คือระบบเดิม · การแก้สิทธิ์/กลุ่มลง audit ของระบบเดิม ไม่ใช่ `audit_logs` ของ SBPGI

## ช่องว่างเทียบ DB เดิมของ K2 (`script_TB_DB_CPA_FRN_FGI_20260722.sql` · ตรวจ 2026-08-06)

สคริปต์ต้นฉบับ = **SQL Server `CPA_FRN_FGI` · 47 ตาราง** (UTF-16, CREATE TABLE ล้วน ไม่มีข้อมูล/ไม่มี index) — ตรวจแล้วนำเข้าเฉพาะสิ่งที่ยังขาดในโครงเป้าหมาย:

### รับเข้าแล้ว (5 ตาราง ★ + คอลัมน์เติมข้างต้น)

| ตารางเดิม (K2) | เข้าเป็น | เหตุผลที่ต้องมี |
|---|---|---|
| `ZoneProfile` | `zones` | SDD GI บังคับให้เพิ่มภาคแล้ว checkbox ขึ้นอัตโนมัติ — ต้องเป็น master |
| `BranchTypeProfile` | `branch_types` | ชื่อประเภทสาขาต่างกันระหว่าง FMS/FGI ต้อง map · Gen Flow Gate อ่านเซ็ตประเภทจากที่นี่ |
| `DecisionProfile` | **`common_code`** (`code_type = SBPGI_DECISION` · มติ DP-9) | ผลพิจารณามีชื่อ 3 ชุด (ปุ่ม/flow/ผลลัพธ์) → `code_name` / `code_mapping` / `other_value` · เปลี่ยนชื่อปุ่มตาม SDD GI ได้โดยไม่ deploy |
| `RunningNumber` | `document_running_numbers` | ออกเลข `YYYY/xxxxx` แบบ atomic ต่อปี — กันเลขชนเมื่อ batch + ผู้ใช้สร้างพร้อมกัน |
| `ImpactCostDetail` | `document_cost_details` | ยอดชดเชยแยกรายเดือน/รายร้านใหม่ — จำเป็นต่อการทวนยอดกับ Statement/SAP |
| `SectionProfile.SectionLimitCost` | `common_code` (`code_type = SBPGI_APPROVE_LIMIT`) — ตาราง `workflow_sections` ถูกตัดแล้ว | ทำให้วงเงิน เกณฑ์เดียว 100,000 (SDD GI) เป็น data |
| `CompensateFlow` (84 คอลัมน์) | คอลัมน์เติมใน `compensation_documents` | `round_no`/`loop_no` · `allmap_url` · `statement_id` · งวดบัญชี · `approver_snapshot` |
| `AttachFileProfile` | คอลัมน์เติมใน `document_attachments` | สถานะอัปโหลด + lifecycle ลบไฟล์บน object storage |
| `CompTransferSBPDate` | `impacted_stores.transfer_sbp_date` | เงื่อนไขร้านก่อน/หลัง 1/10/2014 |

### ตรวจแล้ว — มีของเทียบเท่าอยู่แล้ว ไม่ต้องเพิ่ม

`CompensateHistory` → `consideration_logs` · `CompetInCompenProfile`/`CompetitionProfile` → `document_competitors`/`competitors` · `FactorInCompenProfile`/`FactorProfile` → `document_external_factors`/`external_factors` · `ImpactProfile` → `fgi_impact_stores` + `document_new_stores` · `StatusProfile` → `document_statuses` · `CommonConfig` → `mas_param` ของระบบ SBP เดิม (ไม่มีตาราง/หน้าจอ config ใน SBPGI) · `MaintainHistory`/`MaintainMasterHistory` → **ไม่ migrate** (ยกเลิกระบบ audit ของ master 2026-08-07) · `Journal`/`JournalDetail` → application log ของ BE (ไม่มีตาราง `job_run_histories` ใน target schema แล้ว) · `CompDocAttachment`/`CompTempAttachment` → `document_attachments` · `CompensateHistory.ActionWaitingDays` → `workflow_tasks.waiting_days`

### ตัดทิ้งตามการตัดสินใจเดิม (ไม่นำเข้า)

กลุ่ม RBAC/เมนูของ K2 — `ApplicationMenu` · `ApplicationRoles` · `AuthorizedMenu` · `MENU` · `RoleForAuthorizedMenu` · `MasterUserViewer` · `MaintainForm` · `MaintainFormAuthorized` · `FormProfile` · `URLPath` · `CompenOrganizeProfile` (ผู้ปฏิบัติงาน) → **ใช้ระบบ SBP เดิม (auth-backend)** ตามการตัดสินใจ 2026-08-05

### ค้างพิจารณา (P1 — ยังไม่เพิ่มในโครง)

| ตารางเดิม | ประเด็น |
|---|---|
| `ListDocumentsPendingRemoval` | นโยบาย **archive/purge เอกสาร** (ArchiveDay → ArchiveDate → PurgeDate → DeleteDate) — โครงใหม่ยังไม่มี data retention plan |
| `TaskMaster` / `TaskList` | นิยาม **layout ไฟล์ interface แบบ fixed-width** (posstart/fieldlength/formatdate ต่อฟิลด์) — ปัจจุบัน hardcode ในโค้ด job · ระบบใหม่กำหนดใน **backend config** (ไม่มีตาราง `job_configs` แล้ว) |
| `MaintainMessage` | master **ข้อความ popup/validation ต่อฟอร์ม** (title/body/type) — ถ้ามี จะแก้ข้อความ SRS verbatim ได้โดยไม่ deploy |
| `MonitorAdjust` | log **ปรับยอด forecast/actual** ต่อเอกสาร (KeyCallSMO) |
| `TransectionDeleteStore` | log ลบร้าน/เอกสารพร้อม **SRNumber** — เป็นหลักฐานของปัญหา "ต้องเปิด SR" ที่ SDD GI ยกเลิก · ควรมี log การยกเลิก/ลบเอกสารแบบใหม่แทน |
| `LogCompensate` / `LogCompensateReturn` | log request/response ข้ามระบบ (FMS) — `interface_transactions` ครอบเฉพาะไฟล์/ACK |
| `ServerMaster` | เก็บ `username`/`password` เป็น plaintext — **ยืนยันข้อ P0 เดิม**: ย้าย credential ไป Secret Manager |
| `Versions` / `FGIHelp` | ข้อมูลเวอร์ชันระบบ + เนื้อหาหน้า Help |

## ช่องว่างเทียบ DB เดิมของ FGI — Oracle `FCS_FRN` (ตรวจ 2026-08-06)

แหล่ง: `fcs_frn_stqa_schema_20260806.sql` — DDL ของ schema **FCS_FRN ทั้งระบบ FCS** (Oracle 19c · 707 ตาราง · 87 view · 295 sequence)
ส่วนที่เกี่ยวกับ FGI = **19 ตาราง** (ไม่นับ `*_BK_20250515` 8 ตัวที่เป็น backup) + 22 sequence + view `V_FGI_SBP_APPROVER`
ต่างจาก `script_TB_DB_CPA_FRN_FGI_20260722.sql` ที่เป็น **ฝั่ง K2 (SQL Server)** — ไฟล์นี้คือ **ฝั่ง FGI/FCS (Oracle)** จึงเทียบกับ **zone A** เป็นหลัก

### ตรงกับโครงเป้าหมายแล้ว (zone A ครบ 7 ตาราง)

| ตารางเดิม (FGI) | ในโครงใหม่ |
|---|---|
| `FGI_IMPACT_STORE` | `fgi_impact_stores` |
| `FGI_IMPACT_STORE_ON_PROCESS` | `fgi_impact_processes` (hub · ออก `impact_process_id`) |
| `FGI_IMPACT_STORE_SALES` | `fgi_impact_sales_summaries` |
| `FGI_IMPACT_STORE_SALES_TRN` | `sales_transactions` |
| `FGI_IMPACT_COMPETITOR` | `fgi_impact_competitors` |
| `FGI_CONFIRM_RECEIVE_DATA` | `interface_transactions` (typed FK แทน polymorphic — แก้ E20) |
| `FCS_QSSI_SCORE` | `fcs_qssi_score` |

### ต้องพิจารณาเพิ่ม — **ยังไม่รับเข้าโครง 19 ตาราง รอตัดสินใจ**

| # | ตารางเดิม (FGI) | ช่องว่างที่พบ | ข้อเสนอ |
|---|---|---|---|
| F1 | `FGI_IMPACT_STORE_COMPENSATE` (20 คอลัมน์) | **ยอดชดเชยรายงวดฝั่ง pipeline** ที่เกิด*ก่อน*มีเอกสาร — แยก `COMPENSATE_FORECAST` (ระบบคำนวณ) กับ `COMPENSATE_ADJUST` (คนปรับ) · `COMPENSATE_STATUS` · `COMPENSATE_COMMENT` · `STMT_MONTH`/`STMT_YEAR` (งวด statement) · `APPROVE_DATE` · `COMPENSATE_SEQ`/`SEQ_NO` (รอบ/ครั้งที่) — โครงเรามีแต่ยอดสุดท้ายบน `compensation_documents` | เพิ่ม `fgi_impact_compensations` (zone A) · `FLAG_SEND_BPM` ตัดทิ้งได้ (ไม่ export ไฟล์เข้า K2 แล้ว) แต่ **forecast vs adjust ต้องเก็บคู่กัน** เพราะ SDD GI ให้คีย์ปรับยอดได้ |
| F2 | `FGI_NEW_STORE_COMPENSATE` (19) | ของเดิมเก็บ **ยอด + % ทั้งฝั่ง forecast และ adjust** ต่อร้านเปิดใหม่ (`COMPENSATE_FORECAST_N` / `_PERCENT_N` / `COMPENSATE_ADJUST_N` / `_PERCENT_N`) — โครงเรามีชุดเดียว | ขยาย `document_new_stores` เป็น 2 ชุด (forecast/adjust) หรือแยกตาราง zone A · **ยืนยันการเพิ่ม `compensate_amount` ที่ทำไปแล้ววันนี้ว่าถูกทาง** |
| F3 | `FGI_IMPACT_STORE_INFO` (63) + `FGI_NEW_STORE_INFO` (24) | **snapshot ร้าน + ผู้อนุมัติต่องวด** — ชื่อร้าน/ภาค/ประเภท/นิติบุคคล/ชื่อผู้รับสิทธิ์/วันเริ่ม-ยกเลิก SBP · `URL_ALL_MAP` · `IMPACT_TYPE` · บล็อก **DV/GM/AVP** + **SBP_DV/GM/VP** (18 คอลัมน์จาก `V_FGI_SBP_APPROVER`) — โครงเรา join `stores` สด ๆ และเก็บ `approver_snapshot` เฉพาะบนเอกสาร (ไม่มี **DV/ผู้จัดการเขต**) | ตัดสินใจ snapshot-vs-join: หน้าเอกสารแสดงชื่อร้าน/เจ้าของ/นิติบุคคล ถ้า master เปลี่ยนย้อนหลัง เอกสารเก่าจะเพี้ยน · อย่างน้อยต้องเพิ่ม **DV** เข้า `approver_snapshot` |
| F4 | `FGI_ROS_IMPORT` (14) | **ตัวตั้งของการคำนวณ** ที่ import รายเดือน — `ROS_SALES` · `GP_SALES` · `PHONE_CARD_SALES`/`_PROFIT` · `CASH_CARD_SALES`/`_COMMISSION` · `CUSTOMER_AVG` — โครงเราไม่มีเลย | ตรงกับ **ข้อค้าง P2 ของ gap-analysis** (รายละเอียดการคำนวณตามประเภทร้าน / GP before Split) — ตัดสินใจว่าจะรับเข้า SBPGI หรือปล่อยให้เป็นของ FS/Statement |
| F5 | `MAS_STORE_IMPACT` + `MAS_STORE_IMPACT_PREDICT` (19 + 19) | master คู่ร้านกระทบที่มี **`RENOVATE_START_DATE`/`RENOVATE_END_DATE`** และตาราง **คาดการณ์ร้านที่จะกระทบล่วงหน้า** — โครงเราพูดถึง "ปิด renovate" แต่ไม่มีช่วงวันที่และไม่มี predict | **ไม่ต้องเพิ่มคอลัมน์ใด** — ตรวจฐานจริงแล้ว `sevenshop` ของระบบเดิมมี `start_renovate_date` / `end_renovate_date` อยู่แล้ว (คอลัมน์ 52-53 · [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §3.7) และ `stores` เองก็ถูกตัดไปใช้ `store`/`mas_store`/`sevenshop` ตั้งแต่ 2026-08-06 แล้ว → อ่านจาก `sevenshop` · ส่วน predict ยังเป็นข้อค้างถามธุรกิจว่ายังใช้งานอยู่หรือไม่ก่อนรับเข้า |
| F6 | `FGI_WS_LOG` (7) | log **request/response ของ web service** (`DATA_INPUT`/`DATA_OUTPUT` CLOB · `ERROR_CODE`/`MSG` · start/end) — application log เก็บผลการรัน job และ `interface_transactions` เก็บไฟล์/ACK แต่ไม่มีที่เก็บ payload ราย call | เพิ่ม `integration_call_logs` — ยังจำเป็นแม้ตัด K2 REST เพราะ QSSI/ALLMAP/IAS ยังเป็น service call · ซ้ำประเด็นกับ `LogCompensate` ในรายการ P1 ฝั่ง K2 |
| F7 | `FGI_CANCEL_PROCESS` · `FGI_CANCEL_APPROVE` · `FGI_CANCEL_HISTORY` · `FGI_CANCEL_MAIL` · `FGI_COMPETITOR_DEL` (5 ตาราง + sequence รายภาค `SEQ_FGI_CANCEL_PROCESS_00`–`09`) | **สายอนุมัติ "ขอยกเลิก" อีกชุดหนึ่งที่แยกจาก workflow หลัก** — มี `CANCEL_TYPE`/`CANCEL_SUBTYPE` · ช่วงวันที่ยกเลิก · `APPROVE_SEQ` หลายชั้น · ผู้เปิดเรื่อง (ชื่อ/หน่วยงาน/เบอร์/อีเมล) · mail TO/CC/BCC ต่อชั้น · `STATUS_ID` — **ไม่ถูกอ้างถึงเลยใน `fcsJar` และใน repo `SBP/` ทั้ง 3 ตัว** แปลว่าเป็นของ **เว็บ FCS เดิม** ที่อยู่นอกทั้งสองงาน | **ต้องถามธุรกิจ**: SBPGI รับงานนี้มาด้วยหรือไม่ · ไม่ใช่ตัวเดียวกับผลพิจารณา "หยุดชดเชยประกันรายได้" ในขั้น 06 ของ workflow เรา |
| F8 | `FGI_IMPACT_STORE_ON_PROCESS` (คอลัมน์ที่ยังไม่ครอบ) | `START_COMPENSATE_MONTH/YEAR` + `END_COMPENSATE_MONTH/YEAR` (กรอบงวดที่ชดเชยได้) · `LAST_COMPENSATE_SEQ_NO` · `FLAG_ACTION` · `DATASOURCE` | เติมคอลัมน์เข้า `fgi_impact_processes` — กรอบเริ่ม/จบงวดคือกติกา "เดือนที่ 4 หยุดชดเชย" และการเปิดเรื่องซ้ำตาม SDD GI |

### ขอบเขต — ของที่ **ไม่ใช่** ของ SBPGI (ห้ามทำซ้ำ)

- `MAS_STORE` · `MAS_STORE_TYPE` · `MAS_EMPLOYEE` · `MAS_STORE_COMPETITOR` · `FCS_MONTHLY_SALES` · `FML_SBP_STMT` → **master/ข้อมูลของระบบ FCS/SBP เดิม** (ดู `SBP/README.md` — store-backend เป็นเจ้าของฝั่ง PostgreSQL) · `stores`/`employees`/`branch_types`/`competitors` ในโครงเราคือ **read model ที่ sync มา ไม่ใช่ master**
  - `FML_SBP_STMT` มี `DOCUMENT_ID` + `CHANNEL_TRAN_ID` + `REPORT_LINK` — คือปลายทางของ `compensation_documents.statement_id` ที่เราตั้งไว้ ตรงกันแล้ว
- `V_FGI_SBP_APPROVER` → **auth-backend ของระบบ SBP เดิม** ตามการตัดสินใจ 2026-08-05 · สิ่งที่ต้องบันทึกไว้: view นี้ resolve ผู้อนุมัติจาก `business_user` + `business_user_group` (group_id = 21) โดย key คือ **(store_type, store_area)** แล้วจัดอันดับด้วย `position_level` — SBPGI ต้องส่ง 2 คีย์นี้ไปถามระบบเดิม และ `position_level` คือจุดที่แยก **ผู้รักษาการ** ออกจากผู้อนุมัติจริงตาม SDD GI
- `FGI_*_BK_20250515` (8 ตาราง) → backup ของการ migrate เดิม ไม่นำเข้า

### ยกเลิกระบบ audit ของ master (ตัดสินใจ 2026-08-07 · ตัด 1 ตาราง)

`audit_logs` **ถูกลบจาก target schema** (22 → 21 ตาราง) พร้อมกับ endpoint `GET /audit-logs` · การ์ด "ประวัติการแก้ไขข้อมูล" ในหน้า `k2-factors.html` / `k2-competitors.html` · และฟิลด์ "เหตุผลการแก้ไขข้อมูล" ใน `SCHEMAS` ของ `assets/sbp.js`

| ผลกระทบ | รายละเอียด |
|---|---|
| **สิ่งที่หายไป** | ไม่มีร่องรอยว่าใครแก้ master (ปัจจัยภายนอก / รายชื่อคู่แข่ง) เมื่อไร จากค่าอะไรเป็นอะไร ด้วยเหตุผลใด — เดิมเก็บตารางนี้ไว้เพราะ**ระบบ SBP เดิมไม่มี audit กลางของ master** (มีเฉพาะ `general_upload_data_page_audit_log` ของงาน upload) |
| **สิ่งที่ยังอยู่** | `consideration_logs` (ประวัติผลพิจารณารายเอกสาร — คนละเรื่อง) · `interface_transactions` (tracking รับ–ส่งไฟล์) · audit ของ RBAC/config/email template ที่อยู่ฝั่งระบบ SBP เดิม |
| **ของที่ต้องย้ายที่เก็บ** | Job 10 (watchdog ACK) เคยใช้ `audit_logs` เป็น marker กันส่งอีเมลซ้ำต่อวัน → ย้ายไปใช้คอลัมน์ใหม่ **`interface_transactions.last_ack_notified_on`** แทน |
| **ถ้าต้องการ audit กลับมา** | ให้พิจารณาใช้กลไก audit ของระบบ SBP เดิม แทนการสร้างตารางใหม่ |

### ตารางที่ตัดออกรอบ 2 — มีอยู่แล้วในระบบ SBP ปัจจุบัน (ตัดสินใจ 2026-08-06)

ตรวจ `SBP/README.md` + repo `srm-sps-spsap-store-backend` (79 entity / PostgreSQL) แล้วพบว่า **10 ตารางในโครงเป้าหมายซ้ำกับของที่ระบบ SBP มีและใช้งานจริงอยู่แล้ว** → **ยึดของ SBP เป็นหลัก ไม่สร้างซ้ำ** (34 → 24 ตาราง · ต่อมาเหลือ 22 เมื่อตัดตารางกลุ่ม batch และ 21 เมื่อยกเลิกระบบ audit)

| ตารางที่ตัด (10) | ของระบบ SBP ที่ใช้แทน | หมายเหตุการต่อยอด |
|---|---|---|
| `workflow_instances` · `workflow_tasks` | **`@srm/glb-workflow`** ใน schema **`sps_store`** — `workflow_transaction` (instance · 19,283 แถว) · `workflow_approver` (prepared approvers · 96,542 แถว) · `workflow_history` (timeline · 38,010 แถว) | SBPGI ขอ **workflow version ใหม่** 1 ตัว แล้วเรียก initialize → เพิ่ม prepared approver → ยิง event · **ชื่อ method ยังไม่ยืนยัน** (ดูข้อค้างในหัวข้อผลการเทียบ DB จริง) · `referenceId` จะใช้ `doc_no` หรือ surrogate id **ยังไม่ตัดสิน (DP-1)** |
| `workflow_sections` · `document_statuses` | **`workflow_state` / `workflow_route` / `workflow_status`** ของ engine ใน **`sps_store`** (definition เก็บใน DB ไม่ใช่โค้ด · ของจริงมี state 18 · route 43 · status 22 แถว) | 5 ขั้น 06/08/01/02/03 = state · การส่งต่อ/ตีกลับ = route · สถานะ 6 ค่า = status · **วงเงินอนุมัติ (เกณฑ์เดียว 100,000) เก็บใน `common_code`** (`code_type = SBPGI_APPROVE_LIMIT`) หรือ `workflow_route.condition_json` — ยังคงเป็น data ตาม SDD GI |
| `stores` | **`store` / `mas_store` / `sevenshop`** + `fr_store` · `franchisee` · `juristic` | มี API พร้อมใช้: `GET /store/search`, `/store/list`, `/store/detail`, `/store/opt-name` |
| `zones` | **`mas_zone`** (`zone_id` · `zone_cd` · `zone_name` · `sub_area_flag/name`) | มี API พร้อมใช้: `GET /store/all-regions`, `/store/regions-by-email`, `/store/province-by-region` — ตอบโจทย์ SDD GI ที่ให้ภาคเพิ่มเองโดยไม่แก้หน้าจอ |
| `branch_types` | **`common_code`** (`code_type` + `seq_no` → `code_value`/`code_name`) | มี API พร้อมใช้: `GET /common/common-code`, `/master/common` · ชื่อ FMS/FGI ที่ต่างกันเก็บเป็นคนละ `code_type` |
| `employees` | **`business_user`** + `business_user_group` + `business_group` (auth-backend) | ต่อจากการตัดสินใจ 2026-08-05 · ผู้อนุมัติ resolve ด้วย (store_type, store_area) + `position_level` แบบเดียวกับ view `V_FGI_SBP_APPROVER` |
| `email_templates` | **`email_template`** (`email_template_id` · `subject_format` · `body_format`) + **`email_sent`** (log ทุกฉบับ) + lib `@gosoft-sbp/email-lib` (`emailId`) | 8 template EM-01–08 = **8 แถวใน `email_template` เดิม** · **ลบหน้าจอ `email-template.html` และ endpoint `/email-templates/*` ทั้งกลุ่ม 2026-08-06** — SBPGI แค่**อ่าน**ไปประกอบอีเมลแล้วส่งผ่าน lib การแก้ template ทำที่ระบบ SBP เดิม · ไม่ต้องทำ mail sender เอง |
| `system_configs` | **`mas_param`** (`param_name` · `param_value` · `ref_name` · `description` · `is_config` · `active_flag`) | ถ้าต้องการ `category`/`value_type`/`is_editable` ให้**เพิ่มคอลัมน์ใน `mas_param`** ไม่สร้างตารางใหม่ · **ลบหน้าจอ `system-config.html` และ endpoint `/configs*` ทั้งกลุ่ม 2026-08-06** — SBPGI แค่**อ่าน**ค่าไปใช้ การแก้ค่าทำที่ระบบ SBP เดิม |

### มติจากการเทียบฐานข้อมูลจริง (ตัดสินใจ 2026-08-10 · DP-1 · DP-3 · DP-9)

| มติ | ผลต่อ schema |
|---|---|
| **DP-9 = แยกตัดสิน** | `decisions` **ตัดออก** → ใช้ `common_code` ของระบบเดิม (`code_type = 'SBPGI_DECISION'`) · `external_factors` + `competitors` **ยังเป็นตารางของ SBPGI** เพราะมีหน้าจอ CRUD ของตัวเอง และการเขียนลง lookup กลางไม่คุ้มความเสี่ยง (ตอนนั้น 20 ตาราง · ปัจจุบัน 19) |
| **DP-3 = ทางเลือกที่ 3 (ผสม)** | `impacted_stores` **ยังเป็นตาราง** แต่เป็น **snapshot บางส่วน** — เก็บเฉพาะร้านที่เคยเข้ารอบชดเชย เติมแบบ upsert ตอนสร้าง `fgi_impact_processes` ไม่ sync ทั้ง master |
| **DP-1 = ทางเลือก B** | `compensation_documents` เปลี่ยนเป็น **surrogate PK `id`** · `doc_no` เป็น **UNIQUE NOT NULL** (business key) · `reference_id` ที่ส่งให้ engine = `id` |

**การ map `decisions` → `common_code`** (ตรวจจากโครงจริงของ `sps_store.common_code` แล้วว่าใส่ได้พอดี ไม่ต้อง ALTER):

| ฟิลด์เดิมของ `decisions` | คอลัมน์ใน `common_code` | ข้อจำกัดจริง |
|---|---|---|
| `decision_code` | `code_value` varchar(100) | ⚠ ถ้า map 1:1 กับ `workflow_event.event` ต้อง **ยาวไม่เกิน 10 ตัวอักษร** (`event` เป็น varchar(10)) |
| `decision_name` (ข้อความบนปุ่ม · ไทย verbatim) | `code_name` varchar(1000) | พอ |
| `flow_name` (ชื่อในผัง flow) | `code_mapping` varchar(100) | พอ |
| `result_name` (ชื่อในรายงาน/ประวัติ) | `other_value` varchar(50) | พอ (ค่าจริงคือ "ประกันรายได้" / "ไม่ประกันรายได้") |
| ลำดับแสดงผล | `seq_no` integer | ต้องกำหนดเอง |
| เปิด/ปิดใช้งาน | `active_flag` varchar(1) default `'Y'` | ต้องกรอง `active_flag='Y'` ทุก query |

> ⚠️ **ข้อควรระวังที่ต้องรับทราบ:** `common_code` **ไม่มี PK และไม่มี unique constraint** — มีแค่ index ธรรมดา `btree (code_type, code_value, code_name)` แปลว่า**ฐานข้อมูลไม่กันรหัสซ้ำให้** ต้องกันที่ระดับแอปพลิเคชัน หรือขอเพิ่ม partial unique index (`WHERE code_type='SBPGI_DECISION'`) ซึ่งต้อง sign-off จากทีมเจ้าของตาราง เพราะเป็นตารางที่ทุกโมดูลอ่าน (2,609 แถว)
> และต้องลงทะเบียน `code_type` ที่ `common_code_type` (376 แถว) ก่อนใช้งาน

### ตารางที่ "คล้ายแต่ไม่ใช่" — ตรวจแล้วต้องเก็บของเราไว้

| ตารางของเรา | ของ SBP ที่ใกล้เคียง | เหตุผลที่ยังต้องมี |
|---|---|---|
| `consideration_logs` | `workflow_history` (from_state → to_state · remark · user) | engine ไม่มี `decision_code` · `result_category` (APPROVE/REJECT — ใช้ filter รายงาน) · ไฟล์แนบต่อการพิจารณา → เก็บตารางเราไว้และผูก `transaction_id` ของ engine |
| `document_attachments` | `upload_general` (ไฟล์ของงาน general upload) + service `POST /statement/upload-file-aws` · `download-file-aws` | คนละบริบทไฟล์ · **แต่ให้ใช้ service อัปโหลด/ดาวน์โหลด S3 ของระบบเดิม ไม่เขียน storage layer เอง** · **เหตุผลจริงที่ต้องมีตารางเอง = `upload_general` ขาด `file_size` / `content_type` / `section_code` / `upload_status` / `purge_flag`** (ไม่ใช่เพราะติด FK `job_id` — ดูข้อแก้ความเข้าใจผิดในหัวข้อผลการเทียบ DB จริง) · จะทำตารางเองหรือต่อยอด `upload_general` **ยังไม่ตัดสิน (DP-8)** |
| `interface_transactions` | `integration_log` (`module` · `service` · `payload`) | ของเราติดตาม ACK ระดับ record/ไฟล์ · `integration_log` เป็น payload log ราย call → **ใช้ `integration_log` แทนตาราง `FGI_WS_LOG` ในข้อ F6 ได้เลย ไม่ต้องเพิ่มตารางใหม่** |

## ผลการเทียบกับฐานข้อมูลจริง (07/08/2026)

ดึง schema สดจาก DB dev (PostgreSQL 17.7) แล้วเทียบกับโครงตารางนี้ทีละรายการ · หลักฐานอยู่ที่ **[`SBP/db-schema-sps_store.md`](SBP/db-schema-sps_store.md)** (schema `sps_store` · 198 ตาราง · 3,061 คอลัมน์) และ **[`SBP/db-schema-sps_auth.md`](SBP/db-schema-sps_auth.md)** (schema `sps_auth` · 78 ตาราง · 1,335 คอลัมน์) · บทวิเคราะห์เต็มและ **ข้อค้างตัดสินใจ 12 ข้อ** อยู่ที่ **[`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md)**

### 1. โซน A + แกนเอกสารโซน B — ยืนยันว่าไม่มีของเดิม ต้องสร้างเองทั้งหมด

ค้นทั้ง **276 ตาราง / 4,396 คอลัมน์** ของทั้งสอง schema ด้วยคำว่า `impact` · `compensat` · `guarantee` · `income` · `competitor` · `growth` · `outlier` · `distance` · `radius` · `latitude` · `longitude` · `window_no` → **0 hit ทุกคำ** ทั้งชื่อตารางและชื่อคอลัมน์ (`factor` เจอ 4 ครั้ง เป็น `fillfactor='90'` ของ index ล้วน)

⇒ **โซน A ทั้ง 7 ตาราง และแกนเอกสารโซน B ต้องสร้างใหม่ ไม่มีทางลัด** · สิ่งที่ reuse ได้อยู่ในชั้นแพลตฟอร์ม (workflow · อีเมล · config · storage · master) ไม่ใช่ชั้นธุรกิจ

### 2. Workflow engine — **13 ตาราง** และอยู่ schema **`sps_store`** (ไม่ใช่ `sps_auth`)

เอกสารเดิมของเราเขียนว่า "10 ตารางของ engine" — **ผิด** ของจริงมี **13 ตาราง**:

`workflow` · `workflow_version` · `workflow_state` · `workflow_status` · `workflow_event` · `workflow_route` · `workflow_group` · `workflow_group_map` · `workflow_transaction` · `workflow_history` · `workflow_approver` · `workflow_part` · `workflow_part_display`

**4 ตารางที่โครงเรายังไม่เคยระบุชื่อไว้เลย** = `workflow_group` · `workflow_group_map` · `workflow_part` · `workflow_part_display` (บวก `workflow_event` และ `workflow` ที่เอกสารเดิมก็ไม่ได้ระบุ)

ทั้งสอง schema มีครบ 13 ตารางเหมือนกัน (DDL ชุดเดียวกัน) แต่ **engine ตัวจริงที่ SBPGI ต้องเสียบคือ `sps_store`** — ดูจากปริมาณข้อมูล:

| ตาราง | `sps_store` (ตัวจริง) | `sps_auth` (ของ auth-backend คนละชุด) |
|---|---:|---:|
| `workflow_transaction` | **19,283** | 55 |
| `workflow_history` | **38,010** | — |
| `workflow_approver` | **96,542** | — |
| `workflow_route` | 43 | 41 |
| `workflow_state` | 18 (**4 คอลัมน์**) | 10 (**3 คอลัมน์**) |
| `workflow_status` | 22 | 10 |

`workflow_state` คนละจำนวนคอลัมน์ ⇒ **สอง schema เป็นคนละเวอร์ชันของ engine** ห้ามอ้างอิงสลับกัน · ชุด `wf_*` (`wf_step_history` · `wf_approve` · `wf_email_template`) เป็น engine **เก่า** คนละเรื่อง **ห้ามเขียนลง**

### 3. ⚠ ความเสี่ยง — `sps_store.workflow_transaction` ไม่มี PK และไม่มี index เลย

ตารางนี้มี **19,283 แถว** แต่ใน schema dump **ไม่มี PRIMARY KEY และไม่มี index ใด ๆ** (ตัวเดียวกันใน `sps_auth` มี PK `transaction_id` ปกติ) · `workflow_state` · `workflow_event` · `workflow_part_display` ใน `sps_store` ก็ไม่มี PK/index เช่นกัน

| หัวข้อ | รายละเอียด |
|---|---|
| **ผลกระทบ** | ทุก query ที่ SBPGI ยิงหาเอกสารด้วย `reference_id` จะเป็น seq-scan บนตารางที่โตขึ้นเรื่อย ๆ · ไม่มีอะไรกันแถว duplicate ระดับฐานข้อมูล |
| **สถานะ** | **ยังไม่ตัดสิน** — ตารางนี้เป็นของ library กลาง `@srm/glb-workflow` ที่ทีมอื่นเป็นเจ้าของ · **ห้าม "เพิ่ม index เอง"** ต้องขอ sign-off จากทีมเจ้าของ library ก่อน |
| **อ้างอิง** | `SBP/SBPGI-vs-existing-system.md` §4 **DP-2** |

### 4. `fcs_qssi_score` — มีอยู่จริง 23,958,780 แถว ห้ามสร้างใหม่

ดูรายละเอียดในแถว `fcs_qssi_score` ของ Data Dictionary โซน A ด้านบน · สรุป: ชื่อ **เอกพจน์** · reuse ของเดิม · มี `POST /performance/import-qssi` + staging `fcs_tmp_qssi_score` ทำงานอยู่แล้ว · **จะแก้ตารางเดิมอย่างไร (NOT NULL / UNIQUE / index) ยังไม่ตัดสิน — DP-4**

### 5. `fcs_monthly_sales` ใช้แทน `sales_transactions` **ไม่ได้**

| | `fcs_monthly_sales` (ของเดิม) | `sales_transactions` (ของเรา) |
|---|---|---|
| ระดับข้อมูล | **รายเดือน** | **รายวัน** (4 หน้าต่าง × 15 วัน) |
| คีย์ | `store_id` + `year` + `month` | `sales_summary_id` + `txn_date` + `window_no` |
| ปริมาณจริง | 711,384 แถว | — (ยังไม่มี) |

ยอดรายเดือน **ย้อนกลับเป็นรายวันไม่ได้** และการหา outlier ≥ 50 แบบจับคู่ต้องใช้รายวัน ⇒ ยังต้องสร้าง `sales_transactions` เอง · `fcs_monthly_sales` **ใช้เป็นข้อมูล cross-check ยอดรวมรายเดือนได้**

### 6. ปริมาณจริงของตารางที่ตกลง reuse

| ตารางของระบบเดิม (`sps_store`) | แถว | ใช้แทนอะไรในโครงเรา |
|---|---:|---|
| `mas_param` | 93,752 | `system_configs` |
| `common_code` | 2,609 | `branch_types` · **`decisions`** (มติ DP-9 2026-08-10 · `code_type = SBPGI_DECISION`) · วงเงินอนุมัติ `SBPGI_APPROVE_LIMIT` — **`external_factors`/`competitors` ไม่ย้ายมา** |
| `common_code_type` | 376 | นิยาม `code_type` ของข้างบน |
| `email_template` | 85 | `email_templates` |
| `email_sent` | 5,214 | log อีเมลทุกฉบับ |
| `business_user` | 12,752 | `employees` |
| `mas_store` | 19,647 | `stores` |
| `store` | 19,402 | `stores` |

ตารางเหล่านี้ทีมอื่นเขียนอยู่จริง ⇒ **การเพิ่มคอลัมน์/constraint ต้องขอ sign-off เจ้าของก่อน** ไม่ใช่งานที่ SBPGI ทำเองได้

### 7. แก้ความเข้าใจผิดในเอกสารเก่าของเรา (2 จุด)

| จุด | ที่เคยเขียนไว้ (**ผิด**) | ข้อเท็จจริงจาก schema จริง |
|---|---|---|
| `document_attachments` | "ถ้าใช้ `upload_general` จะติด FK `job_id`" | **ไม่จริง** — `upload_general.job_id` และ `audit_log_id` เป็น **nullable ทั้งคู่** (FK ไป `general_upload_data_page_job` / `..._audit_log`) · **เหตุผลจริงที่ต้องมีตารางเอง คือขาด `file_size` · `content_type` · `section_code` · `upload_status` · `purge_flag`** |
| อีเมล CC | "ระบบเดิมไม่มีที่เก็บ CC ของอีเมล" | **ไม่จริง** — มีอย่างน้อย **3 ที่**: `email_sent.mail_cc` (text) · `fcs_reminder_log.reminder_cc` (varchar 4000) · `fml_email_account` (1,646 แถว · PK `user_id`+`template_id`+`email`) |

### 8. ข้อค้างที่ยังไม่ตัดสิน (บันทึกไว้ ห้ามเลือกเอง)

| # | เรื่อง | สถานะ |
|---|---|---|
| DP-1 … DP-12 | **12 ข้อ · ตัดสินแล้ว 3 (DP-1 · DP-3 · DP-9 เมื่อ 2026-08-10) เหลือค้าง 9** — ที่ยังค้างเช่น DP-2 (index บน `workflow_transaction`) · DP-4 (`fcs_qssi_score`) · DP-11 (ตัวเลขเงิน) · SBPGI อยู่ใน store-backend เดิมหรือแยก backend ใหม่ · audit ของ master เอากลับมาหรือไม่ | **ยังไม่ตัดสิน** — รายละเอียดครบทุกข้อพร้อมข้อดี/ข้อเสียอยู่ที่ [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) §4 · **เอกสารนี้บันทึกไว้เฉย ๆ ไม่เปลี่ยนดีไซน์ตามข้อเสนอ** |
| ✅ ปิด 2026-08-14 | **ชื่อ function ของ workflow engine** — ยึดชีต `Detail` ของ `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` (เอกสารของ lib เอง) เป็น API จริง 8 ตัว: `initializeWorkflow` · `eventWorkflow` · `getPermissionEvents` · `getHistory` · `getTransaction` · `getPendingFlowByUser` · `getWorkflowsByUser` · `addPreApprover` | **ปิดแล้ว** — *Trigger Event* เป็นชื่อหัวข้อขั้นตอนภายใน `eventWorkflow` ไม่ใช่ชื่อ API · `*UseCase` เป็น class ที่ store-backend ห่อไว้เอง |
| — | `workflow_part` + `workflow_part_display` ของ engine คุมการแสดงผล **รายส่วนของหน้าจอ (READ/WRITE ต่อ state)** ซึ่ง**ทับซ้อน**กับกลไก `data-editrole` / `.edit-only` ที่ prototype ทำเอง | **ข้อสังเกต ยังไม่ตัดสิน** ว่าจะย้ายไปใช้ของ engine หรือคงกลไกฝั่ง FE |

## ไฟล์ interface ของ K2 เดิม — ใช้ตรวจ field coverage (2026-08-06)

ถอดโครงสร้างจากไฟล์ตัวอย่างจริงใน `docs/ตัวอย่างไฟล์ที่วางให้ K2 เอาเข้าระบบ/` แล้วสรุปไว้ที่ **[`docs/K2-interface-files.md`](docs/K2-interface-files.md)** — ระบบใหม่ตัดไฟล์ทั้ง 3 ตัวออก (Jobs 7/8/9 → เขียน DB ตรง) แต่ต้องใช้ layout นี้ตรวจว่า **เขียนลง DB ครบทุกฟิลด์ที่ K2 เคยได้รับ**

| ไฟล์ | ฟิลด์ | สาระที่กระทบ schema |
|---|---|---|
| `BPM06001O_` | 48 | หัวเอกสาร + งวด + growth + ยอดชดเชย · **24 ฟิลด์ (ครึ่งไฟล์) เป็นบล็อกผู้อนุมัติ DV/GM/AVP** (emp id · ชื่อ-สกุล ไทย/อังกฤษ · อีเมล) → ยืนยันว่า `compensation_documents.approver_snapshot` ต้องมี **DV** ด้วย (ข้อ F3) · ฟิลด์ 9 = `allmap_url` และฟิลด์ 10 = ลิงก์ SBP Statement (`statement_id`) มาจากไฟล์นี้ตรง ๆ |
| `BPM06002O_` | 24 | ร้านเปิดใหม่ต่อร้านถูกกระทบ — `radius` + `radius_unit` · `distance_km` · **`compensate_amount` (ฟิลด์ 16) + `compensate_percent` (ฟิลด์ 17)** → ยืนยันสูตร ยอด × % และผลรวม = ยอดของเอกสาร · ประเภทร้านเป็น **ตัวอักษรเดียว (`B`)** ยืนยันชุด 7 ค่า `A B C D E PTT บริษัท` (BranchTypeProfile.BranchTypeFGIName · ห้าม hardcode) |
| `BPM06003O_` | 14 | คู่แข่งระดับสาขา — รหัส ALLMAP · **ชื่อไทย + ชื่ออังกฤษ** (→ `competitors.name_th`/`name_en`) · ชื่อสาขา · zone + subzone |

**ข้อเท็จจริงของไฟล์ที่ต้องแก้ในเอกสารเก่า:** ไฟล์กลุ่ม BPM เป็น **UTF-8** (ไม่ใช่ windows-874 — ตัวที่เป็น windows-874 คือ `FRBC0001` ที่ส่งไป STA) · ตัวคั่น `|` · ไม่มีบรรทัดหัวคอลัมน์ · วันที่/ปีเป็น **ค.ศ.** · ชุดตัวอย่างมี `BPM06002O_` ซ้ำ 2 ไฟล์เนื้อหาเหมือนกันทุกไบต์ → **การนำเข้าต้อง idempotent ด้วย business key ไม่ใช่ชื่อไฟล์**

## Master data ที่ยืนยันจากไฟล์จริง (`ข้อมูล Master K2.xlsx` · 2026-08-10)

ไฟล์นี้เป็น dump ของ master ในฐานข้อมูล K2 เดิม **`CPA_FRN_FGI`** (SQL Server) พร้อม DDL — ใช้เป็นแหล่งชี้ขาดค่าคงที่ที่เอกสารก่อนหน้าขัดกัน

### ประเภทร้าน — `BranchTypeProfile` (ชี้ขาดข้อค้าง)

หน้าจอ FGI/รายงานใช้คอลัมน์ **`BranchTypeFGIName`** ไม่ใช่ `BranchTypeCode`

| BranchTypeCode | BranchTypeName | BranchTypeFMSName | **BranchTypeFGIName** |
|---|---|---|---|
| 4 | A-Mo | FAM | **A** |
| 1 | B(1) | FB1 | **B** |
| 3 | C | FC1 | **C** |
| 9 | C(Retire CPALL) | NULL | **C** |
| 6 | BGC | FBGC | **D** |
| 2 | B(2) | FB2 | **E** |
| 5 | PTT | FPT1 | **PTT** |
| 0 | Corporate | B | **บริษัท** |

> **⚠️ master นี้มี 2 ระบบชื่อ — อย่าสลับกัน**
> - `BranchTypeName` (ชื่อแสดงผล): `A-Mo` · `B(1)` · `B(2)` · `C` · `C(Retire CPALL)` · `Corporate` · `PTT` · `BGC` — 8 ค่า
> - `BranchTypeFGIName` (รหัสที่ pipeline/รายงาน FGI ใช้): `A` · `B` · `E` · `C` · `C` · `บริษัท` · `PTT` · `D` — 7 ค่าไม่ซ้ำ
>
> หน้ารายงาน (`k2-report`) กรองด้วย **FGIName**  · หน้าเอกสาร (`k2-document`) ใช้ **BranchTypeName** (ชื่อแสดงผล) — **ต้องเลือกใช้ระบบชื่อเดียวต่อหน้าจอ** และ **`พนักงาน` ไม่ปรากฏใน master เลย** (SRS เขียนไว้แต่ไม่มีแถวรองรับ) → ข้อค้าง: ยืนยันกับ BA ว่า `พนักงาน` คือ `B(2)`/`E` หรือเป็นค่าที่เลิกใช้แล้ว
>
> ⚠️ **`D` และ `E` มีจริงทั้งคู่และเป็นคนละประเภท** (D = BGC · E = B(2)) → ค่าไม่ซ้ำมี **7 ค่า**: `A B C D E PTT บริษัท`
> เอกสาร/หน้าจอรุ่นก่อนแสดงเพียง 4 ตัวเลือกจึง**ผิดทั้งหมด** — SDD สไลด์ 60 แสดงบางส่วน · SRS เขียน “พนักงาน” ซึ่ง **ไม่มีอยู่ใน master**
> แก้แล้วที่ `k2-report.html` (4 → 7 ตัวเลือก) และ `LLDD-FE-Report` · ยังคง**ห้าม hardcode** ให้โหลดจาก `GET /common/common-code` แล้วใช้ 7 ค่านี้เป็น expected set ตอนทดสอบ

### ภาค — `ZoneProfile` (ยืนยันว่าของเราถูกอยู่แล้ว)

**13 ภาค**: BN(10) · BW(20) · BE(30) · BG(40) · BS(70) · REU(81) · NEU(82) · RSU(83) · RSL(84) · RN(85) · RC(86) · REL(90) · NEL(92)
ตรงกับที่ prototype/LLDD ใช้ครบทุกค่า — รายการ 8 ค่าใน SRS (BE/BN/BS/BW/RC/RE/RN/RS) เป็นของเก่า **ไม่ต้องใช้**

### กับดักตอน migrate (ต้องรู้ก่อนเขียนสคริปต์)

| เรื่อง | ข้อเท็จจริงจากไฟล์ | สิ่งที่ต้องทำ |
|---|---|---|
| วงเงินอนุมัติ | `SectionProfile.SectionLimitCost` มีค่าเดียวคือ section 2 (GM) = **100,000** · AVP เป็น NULL | เป็นเกณฑ์**เก่า** — SDD GI เปลี่ยนเป็น เกณฑ์เดียว 100,000 · ห้าม migrate ค่าเดิมมาตรง ๆ ให้ seed ใหม่ที่ `common_code` (`SBPGI_APPROVE_LIMIT`) |
| `DecisionProfile.DecisionCode` | Excel แปลงรหัส **3, 6, 9, 11, 13** เป็นวันที่ (`1900-01-03` ฯลฯ) | เป็น artifact ของไฟล์ Excel ไม่ใช่ข้อมูลจริง — อ่านรหัสจาก DB ต้นทางโดยตรง ห้าม import จากไฟล์นี้ |
| ผลการพิจารณา | `DecisionResultName` มี **4 แบบ**: ประกันรายได้ · ไม่ประกันรายได้ · **ยกเลิกโดยระบบ** · NULL | ✅ **ตัดสินแล้ว 2026-08-10 — แยกเป็นตัวเลือกที่ 4**: `result_category` = APPROVE / REJECT / **CANCELLED** / PENDING · ตัวกรองรายงานเป็น 4 ปุ่ม (ประกันรายได้ · ไม่ประกันรายได้ · ยกเลิกโดยระบบ · ยังไม่มีผล) |
| สถานะเอกสาร | `StatusProfile` เดิมมี **10 สถานะ** (รวมบัญชี 4/5 · GM Promotion 7 · บัญชีภาค 9 · **ยกเลิกเอกสาร 10**) | ระบบใหม่เหลือ 6 หลัง SDD v7.5 ตัดขั้นบัญชี — ต้อง map สถานะเก่าที่ถูกตัดตอน migrate ให้ครบ |
| `SectionCode` | เดิมเป็นเลขหลักเดียว 1–10 (`nvarchar(2)`) | ระบบใหม่ใช้ 2 หลัก `01/02/03/06/08` — เติมศูนย์นำหน้าตอน migrate |

## Canonical Column Contract

DDL, SQL ใน API และ SQL ของ Job ต้องใช้ชื่อด้านล่างตรงกัน; ชื่อในคอลัมน์ “ยกเลิกใช้” ห้ามปรากฏใน implementation ใหม่

| ตาราง | ชื่อ canonical | ยกเลิกใช้ |
|---|---|---|
| `workflow_instances` | `instance_id`, `doc_no`, `instance_status`, `started_at`, `started_by` | `status`; `instance_id` ต้องส่งเข้าตอน insert |
| `sales_transactions` | `txn_date`, `window_no`, `sales_amount`, `sales_diff`, `is_outlier` | `sale_date`, `window_code`, `net_sales` |
| `consideration_logs` | `result`, `result_category`, `detail`, `consider_by`, `action_datetime` | `result_code`, `comment`, `considered_by`, `considered_at` |
| `interface_transactions` | PK `id`, เวลา ACK `acked_at` | API อาจ alias เป็น `trackingId`/`receiveDate` แต่ SQL ต้องอ้าง `id`/`acked_at` |
| `fgi_impact_processes` | `workflow_generation_status` | ห้าม duplicate สถานะเดียวกันใน `fgi_impact_stores` |
| `workflow_sections` | `approve_limit_amount` (numeric) | ห้าม hardcode วงเงินใน service — อ่านจากคอลัมน์นี้ |
| `zones` / `branch_types` / **`decisions` (อยู่ที่ `common_code`)** | `zone_code` · `branch_type_code` · `decision_code` | ห้าม hardcode รายการภาค / ประเภทสาขา / ปุ่มผลพิจารณาใน FE |
| `document_running_numbers` | `year`, `last_running_no` | ห้ามใช้ `MAX(running_no)+1` — ต้อง lock แถวปีนั้น |

> **หมายเหตุ (07/08/2026):** แถว `workflow_instances` และ `workflow_sections` ข้างบนเป็น **สัญญาที่ตกค้างจากก่อนตัดตาราง** — ทั้งสองไม่อยู่ในโครง 19 ตารางแล้ว ของจริงคือ `sps_store.workflow_transaction` / `workflow_state` ของ engine กลาง และวงเงินอนุมัติย้ายไป `common_code` (`SBPGI_APPROVE_LIMIT`) · **ชื่อคอลัมน์ฝั่ง engine เป็นของ library กลาง แก้เองไม่ได้**

## กุญแจเชื่อมข้ามระบบ (Cross-System Keys)

1. **`impacted_stores.store_code = fgi_impact_stores.impacted_store_code`** — สะพานหลักโซน C (K2) ↔ โซน A (FGI/FCS) · รหัสร้าน 5 หลักเดียวกันทั้งระบบ
   - **`stores`** = master สาขา 7-Eleven ทุกประเภท · `impacted_stores` เป็น subset ร้าน SP · ร้านเปิดใหม่ (`document_new_stores.new_store_code`) อ้าง `stores` ตัวเดียวกัน — เป็นแหล่งของ popup ค้นหาร้านในหน้าสร้างเอกสาร
2. **`*.impact_process_id → fgi_impact_processes.id`** — hub กลางของคู่ร้าน ยอดขาย และคู่แข่งในหนึ่งรอบชดเชย (ใหม่)
3. **`compensation_documents.impact_process_id → fgi_impact_processes`** — FK ใหม่ **1 รอบชดเชย : 1 เอกสาร** แทนการส่งไฟล์ BPM06001O (48 ฟิลด์) ข้ามระบบ (ใหม่)
4. **`sps_store.workflow_transaction.reference_id → compensation_documents`** — เปิด instance ของ engine กลางเมื่อผ่าน Gen Flow Gate · สถานะ instance แทน `workflow_generation_status = Y` ของเดิม (ใหม่) · ✅ **มติ DP-1 (2026-08-10) = ทางเลือก B** — `reference_id` ใช้ **surrogate id** (`compensation_documents.id`) **ไม่ใช่ `doc_no`** ตามที่ระบบเดิมทำจริงทั้ง `cooperation-request` (7 จุด) และ `inform-evaluate` · การแปลง transaction ↔ เอกสาร join ผ่าน `compensation_documents.id` · **ผลพลอยได้:** ปลดล็อกให้ออกเลข `doc_no` ทีหลังได้และแก้เลขภายหลังได้ (จังหวะการออกเลขจริงยังเป็นคำถามธุรกิจที่ยังไม่ตอบ)
5. **`document_competitors.source_system = 'ALLMAP'`** — แถวจาก fgi_impact_competitors (Jobs 3/7 เดิม) แยกจากที่ผู้ใช้เพิ่มเอง (USER)
6. **`compensation_histories.submit_account_month`** — งวดที่ส่งเข้าไฟล์ FRBC0001 ไป STA (Job 6) · สถานะ I/C/A/N/S/Z ตามเดิม
7. **`interface_transactions`** — FK แยกประเภทเป็นคอลัมน์ (impact_process_id / sales_summary_id / doc_no) + `data_name` เป็น enum — เลิก `parseInt(impacted_store_code)` ที่ทำเลขศูนย์นำหน้าหาย (ใหม่)

## ข้อปรับปรุงจากระบบเดิม (P0 × 3 · P1 × 4)

1. **เลิก polymorphic FK** — `transaction_key` ของ tracking เดิมชี้คนละตารางตาม data_name (P1) → `interface_transactions` ใช้ typed FK แยกคอลัมน์
2. **บังคับ status domain ด้วย enum / check constraint** — W/P/Y/N · I/C/A/N/S/Z · action_status (Y/W/N) · workflow_generation_status (W/Y/N)
3. **ครอบ Job 4 ด้วย transaction (outbox pattern)** — เดิม commit W→P ก่อนเขียนไฟล์ rollback ไม่ได้ (**P0 อันดับหนึ่ง**)
4. **แก้บั๊ก purge tracking (E20)** — SQL เดิมต่อ data_name สองค่าเป็น string เดียวทำให้ไม่เคยลบ — ต้องทำพร้อม data migration และ test
5. **ทบทวน NULL → auto-accept ของ Job 5** (P1) — ระบบใหม่ตั้งสถานะ "รอตรวจสอบ" แทน accept อัตโนมัติ · **ต้องขอ business sign-off ก่อนเปลี่ยน**
6. **ย้าย credential ทั้งหมดไป Secret Manager + บังคับ TLS** — เดิม SFTP/K2 Basic Auth เป็น plaintext/hardcoded (P0)
7. **ใช้ identity ต่อตารางแทน sequence รวม 7 ตัว** — คงชื่อ sequence เดิมเฉพาะช่วง migrate (Errata E18)
8. **golden-file tests ต่อ interface ภายนอก** — encoding WINDOWS-874 / UTF-8 / TIS-620, วันที่ พ.ศ., ชื่อประกอบ first + last

## เอกสารที่เกี่ยวข้อง

- Flow ที่ใช้ตารางเหล่านี้: [workflow.md](workflow.md) · `plan-flow.html`
- API ที่อ่าน/เขียนตาราง: [api.md](api.md) · `plan-api.html` (**29 เส้น 6 กลุ่ม** — Lookup 2 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3 · กลุ่ม Auth/RBAC · System Config · Email Template · Batch Job Admin ถูกตัดไปใช้ระบบเดิม)
- Schema ต้นทางแยกระบบ: `fgi-database.html` (FGI/FCS) · `k2-database.html` (K2, 16 ตาราง + ER diagram)
- ผลตรวจกับ DB จริง + ข้อค้างตัดสินใจ 12 ข้อ: [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) · หลักฐาน schema: [`SBP/db-schema-sps_store.md`](SBP/db-schema-sps_store.md) · [`SBP/db-schema-sps_auth.md`](SBP/db-schema-sps_auth.md)
