# Database — FGI/FCS + K2 (Target Schema ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุปโครงสร้างฐานข้อมูลเป้าหมายของระบบใหม่
> **แหล่งอ้างอิงหลัก:** `plan-database.html` (หน้า DB FGI/FCS + K2)
> **อ้างอิงประกอบ:** `fgi-database.html`, `k2-database.html`, เอกสาร Batch v4.0 (Data Dictionary หน้า 6–10), SRS ประกันรายได้-K2 v3.1, **`script_TB_DB_CPA_FRN_FGI_20260722.sql`** (schema จริงของ K2 เดิม — SQL Server 47 ตาราง · ดูหัวข้อ "ช่องว่างเทียบ DB เดิมของ K2")
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง database ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-database.html` ให้ตรงกัน

## บริบทระบบใหม่

ระบบใหม่ **รวม EAI และ K2 เข้าเป็นส่วนหนึ่งของ SBPGI** — งาน FGI/FCS batch และงานเอกสาร/workflow K2 ทำงานบน **ฐานข้อมูลเดียวกัน** ไม่มีการส่งไฟล์ผ่าน EAI อีกต่อไป (ดูรายละเอียด flow ที่ [workflow.md](workflow.md))

ผลต่อ schema:
- ไฟล์ภายใน `BPM06001O_` (48 ฟิลด์) / `BPM06002O_` / `BPM06003O_` ที่เคยส่งผ่าน EAI ไป K2 → แทนด้วย FK `compensation_documents.impact_process_id` เชื่อมตรงในฐานข้อมูลเดียวกัน
- K2 engine ภายนอก → แทนด้วยตาราง `workflow_instances` + `workflow_tasks` ภายใน
- ตาราง tracking เดิม `FGI_CONFIRM_RECEIVE_DATA` → แทนด้วย `interface_transactions` (typed FK)
- **SDD v7.5:** ตัดขั้นบัญชี 04/05 ออกจาก workflow — `workflow_sections` เหลือ 5 แถวใช้งาน (06/08/01/02/03) · `document_statuses` เหลือ 6 ค่า (ตัด "รอฝ่ายบัญชี SBP" / "รอบัญชีปฏิบัติการภาค") · บัญชีตรวจสอบผ่านรายงาน SBP Mall + กระทบ SAP นอกระบบ

## ภาพรวม

- **24 ตาราง** ใน Target Schema เดียว (1 schema ใช้ร่วมกัน) — 34 ตารางเดิม **ตัดออก 10 ตารางที่ระบบ SBP ปัจจุบันมีอยู่แล้ว** เมื่อ 2026-08-06 (workflow engine · store/zone/employee master · email template · config — ดูหัวข้อ "ตารางที่ตัดออกรอบ 2" ท้ายไฟล์)
- **3 Data Zones**: A = FGI/FCS Impact Pipeline · B = K2 เอกสาร & Workflow · C = Master/Config ใช้ร่วม
- **4 Core IDs** ใช้ trace งาน (Data Spine)
- มาตรฐานชื่อ: อังกฤษ `lower_snake_case` ทั้ง schema · ป้ายที่มา (FGI/FCS), (K2), (ใหม่) ต้องคงไว้เสมอ
- **ตัดสินใจ 2026-08-05:** RBAC (`roles`/`menus`/`menu_permissions`/`user_accounts`) และผู้ปฏิบัติงาน (`operator_assignments`) **ไม่สร้างใน SBPGI** — ใช้ระบบสิทธิ์/ผู้ใช้ของระบบ SBP เดิม (ดูหัวข้อ "ตารางที่ตัดออก" ท้าย Zone C) · การตัดนี้ทำให้เหลือ 29 ตาราง ก่อนเพิ่มอีก 5 ตารางจากการเทียบ DB เดิมของ K2 (2026-08-06) → รวมเป็น 34

## Data Spine — เส้นทางข้อมูลหลัก

หนึ่งรายการผลกระทบเดินผ่าน ID หลักตามลำดับ ตารางอื่นเป็นรายละเอียด/master ที่เกาะกับ spine นี้:

| ลำดับ | Zone | Key | ความหมาย |
|---|---|---|---|
| 1 | A | `impact_process_id` | หนึ่งร้านถูกกระทบ + หนึ่งงวด — hub ของยอดขาย ร้านใหม่ และคู่แข่ง |
| 2 | B | `doc_no` | เอกสารประกันรายได้รูปแบบ `YYYY/xxxxx` (ปี พ.ศ.) เชื่อมกลับ impact process |
| 3 | B | `instance_id` | Workflow instance หนึ่งชุดต่อเอกสาร ติดตามตั้งแต่เริ่มถึงจบ |
| 4 | B | `task_id` | งานของแต่ละ Section และผู้รับผิดชอบ — แหล่งข้อมูลหน้า inbox |
| 5 | C | `employee_id` | ผู้ปฏิบัติงานที่อ้างร่วมกันทุกขั้น — ตัวตน/สิทธิ์เมนูมาจากระบบ SBP เดิม (auth-backend) ผ่าน user-context header ไม่ใช่ตารางใน SBPGI |

## Data Dictionary (24 ตาราง)

คอลัมน์ **ตารางต้นทาง (Migration)** = ตารางใน DB เดิมที่ต้องดึงข้อมูลมาลงตารางใหม่ ใช้เขียนสคริปต์ import ได้ตรง ๆ · ป้ายกำกับต้นทาง:

- **ORA** = Oracle `FCS_FRN` — `fcs_frn_stqa_schema_20260806.sql` (ฝั่ง FGI/FCS · 707 ตาราง)
- **MSSQL** = SQL Server `CPA_FRN_FGI` — `script_TB_DB_CPA_FRN_FGI_20260722.sql` (ฝั่ง K2 · 47 ตาราง)
- ตารางที่เขียนว่า *ไม่มีต้นทางตรง* ต้อง **derive ระหว่าง migrate** ไม่ใช่ copy · ตารางที่เขียนว่า *sync ต่อเนื่อง* คือ master ของระบบเดิม ห้าม migrate แล้วแยกดูแลเอง
- ลำดับ import ที่ปลอดภัย: master โซน C → โซน A (`fgi_impact_processes` ก่อน แล้วลูกทั้งหมด) → โซน B (`compensation_documents` ก่อน แล้ว `document_*`) → `workflow_instances`/`workflow_tasks` ท้ายสุด

### Zone A · FGI/FCS — Impact Pipeline และ External Interfaces

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `fgi_impact_stores` | FGI/FCS | **ORA** `FGI_IMPACT_STORE` (PK `IMPACT_STORE_ID` · business key `STORECODE_I`+`MONTH`+`YEAR`) | id | `impact_process_id` → fgi_impact_processes · `impacted_store_code` → impacted_stores | คู่ร้านกระทบ–เปิดใหม่ · `verify_status` (W/P/Y/N) · ข้อมูล %/ยอดชดเชยต่อคู่ร้าน |
| `fgi_impact_processes` ★ | FGI/FCS | **ORA** `FGI_IMPACT_STORE_ON_PROCESS` (PK `IMPACT_PROCESS_ID` — seq `SEQ_FGI_IMPACT_PROCESS`) | id | `impacted_store_code` · แม่ของตารางรายรอบทั้งหมด | **hub รอบชดเชย** · `action_status` (Y/W/N) · `last_compensation_amount` · source of truth ของ `workflow_generation_status` (W/Y/N) |
| `fgi_impact_sales_summaries` | FGI/FCS | **ORA** `FGI_IMPACT_STORE_SALES` (key `STORECODE_I`+`MONTH`+`YEAR`) | id | `impact_process_id` → fgi_impact_processes · → sales_transactions (1:N) | หัวยอดขาย · `growth_rate_diff` · `total_working_days` (เกณฑ์ 60 วัน) |
| `sales_transactions` | FGI/FCS | **ORA** `FGI_IMPACT_STORE_SALES_TRN` (key เดียวกับหัว + `SEQ`) | id | `sales_summary_id` → fgi_impact_sales_summaries | ยอดขายรายวันจาก IAS · 4 หน้าต่าง × 15 วัน · sales_diff/outlier ≥ 50 แบบจับคู่ |
| `fgi_impact_competitors` | FGI/FCS | **ORA** `FGI_IMPACT_COMPETITOR` (PK `IMPACT_COMPETITOR_ID`) | id | `impact_process_id` → fgi_impact_processes · → document_competitors (นำเข้า) | คู่แข่งจาก ALLMAP (data_source=ALM) · งวดล่าสุดต่อร้าน |
| `fcs_qssi_scores` | FGI/FCS | **ORA** `FCS_QSSI_SCORE` (`STORE_ID`+`CATEGORY`+`MONTH`+`YEAR`) | id | UK: store_id + category_code + งวด | คะแนน QSSI 6 หมวด (8,9,12,1,10,16) จาก Job 1 |
| `interface_transactions` | ใหม่ | **ORA** `FGI_CONFIRM_RECEIVE_DATA` — ⚠ `TRANSACTION_PK` เป็น polymorphic ต้องแตกตาม `DATA_NAME` เป็น typed FK ตอน migrate | id | typed FK: `impact_process_id` / `sales_summary_id` / `doc_no` | แทน FGI_CONFIRM_RECEIVE_DATA — เลิก polymorphic PK + purge ทำงานจริง (แก้ E20) |

### Zone B · K2 — เอกสารประกันรายได้และ Workflow ภายใน

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `compensation_documents` | K2 | **MSSQL** `CompensateFlow` (PK `CompDocumentID` → `doc_no`) + join **ORA** `FGI_IMPACT_STORE_INFO` เพื่อเติม `impact_process_id` | `doc_no` (YYYY/xxxxx) | `status_code` · `current_section_code` · `impacted_store_code` · **`impact_process_id` (ใหม่)** | เอกสารประกันรายได้ — หัวใจโซน B · FK ใหม่เชื่อม hub โซน A แทนไฟล์ 48 ฟิลด์ · **คอลัมน์ที่เติมจาก CompensateFlow เดิม (2026-08-06):** `round_no`/`loop_no` (= CompMainLoopNo/CompLoopNo — หน้าจอแสดง "รอบ 1 · ครั้งที่ 3") · `allmap_url` (= CompUrlMap — ปุ่ม Link To ALLMAP) · **`statement_id`** (= CompStatementID — โยงกลับ SBP Statement ที่เป็นต้นทางการสร้างเอกสารตามกระบวนการ FS ใหม่) · `account_year`/`account_month` (งวดบัญชี) · `approver_snapshot` (JSONB — FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร ตามที่ CompensateFlow เก็บไว้ 25 คอลัมน์: **จำเป็นเป็นพิเศษเมื่อ RBAC ย้ายไปใช้ระบบเดิม เพราะตำแหน่งจาก HR Connect เปลี่ยนได้ และผู้รักษาการเป็นผู้อนุมัติไม่ได้**) |
| `document_new_stores` | K2 | **MSSQL** `ImpactProfile` (ฝั่ง `_N`) + **ORA** `FGI_NEW_STORE_INFO` / `FGI_NEW_STORE_COMPENSATE` (%ชดเชย + ยอดต่อร้าน) | id | `doc_no` → compensation_documents | ร้านเปิดใหม่ · `distance_km` · `compensate_percent` (**ผลรวมต้อง = 100%**) · `compensate_amount` (ใหม่ — ยอดชดเชยร้านถูกกระทบ × %ชดเชย คำนวณ/ปัดเศษที่ BE · ผลรวมทุกแถวต้องเท่ากับยอดชดเชยของเอกสารพอดี · แสดงในคอลัมน์ "เงินชดเชย (ร้านใหม่)" ของตารางร้านเปิดใหม่ — **กราฟสัดส่วนเงินชดเชยถูกถอดออก 2026-08-06**) |
| `document_competitors` | K2 | **MSSQL** `CompetInCompenProfile` (+ ไฟล์ `BPM06003O_` 14 ฟิลด์) | id | `doc_no` · `competitor_code` → competitors | คู่แข่งในเอกสาร **ระดับสาขา** · `source_system` = ALLMAP (จาก pipeline) / USER (ผู้ใช้เพิ่มเอง) · **คอลัมน์ที่ยืนยันจากไฟล์จริง (2026-08-06):** `competitor_code` เป็นรหัสจาก **ALLMAP** แบบตัวเลข/ตัวอักษรผสม (`4832`, `TD58_08`, `LS3550`) — **ไม่ใช่** รหัสแบรนด์ 01–11 · `branch_name` (ชื่อสาขาคู่แข่ง เช่น "ตลาดศรีวานิช") · `zone_code` + `subzone_code` (01–07) · `open_date`/`close_date` ของคู่แข่ง (ดู `docs/K2-interface-files.md`) |
| `document_external_factors` | K2 | **MSSQL** `FactorInCompenProfile` | id | `doc_no` · `factor_code` → external_factors | ปัจจัยภายนอกที่ใช้ในเอกสาร + ช่วงวันที่ |
| `consideration_logs` | K2 | **MSSQL** `CompensateHistory` (PK `ActionID`) | id | `doc_no` → compensation_documents | ประวัติพิจารณาทุกขั้น (ผู้พิจารณา · Section · ผล · เวลา) · `result_category` (APPROVE/REJECT/PENDING) สำหรับ filter **ประกันรายได้/ไม่ประกันรายได้** หน้ารายงานตรวจสอบประกันรายได้ (k2-report · SDD v7.5) |
| `document_attachments` | K2 | **MSSQL** `CompDocAttachment` + `CompTempAttachment` (+ `AttachFileProfile` สำหรับสถานะอัปโหลด/purge) | id | `doc_no` → compensation_documents | ไฟล์แนบ ≤ 5MB ต่อไฟล์ · แยกตาม Section ที่แนบ · **เติมจาก AttachFileProfile เดิม (2026-08-06):** `file_size` · `upload_status` + `upload_message` (ผลอัปโหลดขึ้น object storage) · `purge_flag`/`storage_delete_status` (lifecycle ลบไฟล์บน S3 — ของเดิมมี FlagPurgeData/FlagDeleteS3/StatusCodeDeleteS3 ครบ) |
| `compensation_histories` | K2 | **ORA** `FGI_IMPACT_STORE_COMPENSATE` + **MSSQL** `CompensateFlow` (แถวรอบก่อนหน้าของร้านเดียวกัน) | id | `store_code` · `ref_doc_no` | ประวัติชดเชยต่อร้าน/รอบ · `submit_account_month` เดือนส่งบัญชี (→ ไฟล์ FRBC0001 ของ Job 6) |
| `document_cost_details` ★ | K2 (ImpactCostDetail) | **MSSQL** `ImpactCostDetail` (PK `ImpCostID`) | id | `doc_no` → compensation_documents · `new_store_code` | **(เพิ่ม 2026-08-06)** ยอดชดเชย**แยกรายเดือน/รายร้านเปิดใหม่** — `cost_year`/`cost_month` · `cost_target` (เป้ายอดขาย) · `cost_amount` · แยกค่าของร้านใหม่ (`_n`) และร้านใหม่สะสม (`_nc`) ตาม ImpactCostDetail เดิม · ของเดิมในโครงเรามีแค่ยอดรวมต่อเอกสาร + %ต่อร้าน ทำให้ทวนยอดรายเดือนกับ Statement/SAP ไม่ได้ |
| `document_running_numbers` ★ | K2 (RunningNumber) | **MSSQL** `RunningNumber` | `year` | ออกเลขให้ compensation_documents | **(เพิ่ม 2026-08-06)** ตัวนับเลขเอกสารต่อปี พ.ศ. (`last_running_no`) — ออกเลข `YYYY/xxxxx` แบบ atomic (`UPDATE … RETURNING` / row lock) กันเลขชนกันเมื่อ batch และผู้ใช้สร้างพร้อมกัน · เดิมโครงเราไม่ระบุที่เก็บตัวนับ |

### Zone C · Shared — Master, RBAC, Configuration และ Audit

| ตาราง | ที่มา | ตารางต้นทาง (Migration) | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|---|
| `impacted_stores` | K2 | **ORA** `FGI_IMPACT_STORE` (ฝั่ง `_I` · distinct) + **MSSQL** `CompensateFlow.CompTransferSBPDate` | `store_code` | = `impacted_store_code` ของโซน A (สะพานหลักสองระบบ) · subset SP ของ `stores` | ข้อมูลร้าน SP master · **`transfer_sbp_date` (เพิ่ม 2026-08-06 = CompTransferSBPDate เดิม)** — วันที่โอนเป็นร้าน SP ใช้กับเงื่อนไขร้านก่อน/หลัง 1/10/2014 ของ Approve Flow เดิม |
| `decisions` ★ | K2 (DecisionProfile) | **MSSQL** `DecisionProfile` | `decision_code` | ← consideration_logs.decision_code · workflow transition | **(เพิ่ม 2026-08-06)** master **ผลพิจารณา** — `decision_name` (ข้อความบนปุ่ม · ไทย verbatim) · **`flow_name`** (ชื่อที่ใช้ในผังflow) · **`result_name`** (ชื่อที่ใช้แสดงผลในรายงาน/ประวัติ) ซึ่งของเดิมแยกกัน 3 ชุด · ทำให้การเปลี่ยนชื่อปุ่มตาม SDD GI ("ส่งฝ่ายส่งเสริมฯ" → "ส่งหน่วยงานส่งเสริมฯ") แก้ที่ data ไม่ต้อง deploy · `consideration_logs.result` ยังเก็บข้อความ ณ เวลากดไว้เป็น snapshot |
| `external_factors` | K2 · SRS 3.1.9 | **MSSQL** `FactorProfile` | `factor_code` | ← document_external_factors | ปัจจัยภายนอก master · รหัสห้ามซ้ำ |
| `competitors` | K2 | **MSSQL** `CompetitionProfile` (+ **ORA** `MAS_STORE_COMPETITOR`) | `competitor_code` | ← document_competitors | **master แบรนด์ร้านคู่แข่ง 11 รายการ** (รหัส `01`–`11`) · `name_th` + `name_en` (ระบบเดิมเก็บทั้งไทยและอังกฤษ) — จัดการที่หน้าจอ `k2-competitors.html` (เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม) · **คนละระดับกับ `document_competitors`** ที่เก็บ *รายสาขา* ของคู่แข่งพร้อมรหัสจาก ALLMAP (เช่น `4832`, `TD58_08`) + ชื่อสาขา + zone/subzone (ดู `docs/K2-interface-files.md`) |
| `audit_logs` | K2 | **MSSQL** `MaintainHistory` + `MaintainMasterHistory` (`ActionCode` ← `ActionProfile`) | id | `table_name` + `ref_key` (generic) | ประวัติแก้ไข master แบบหลายรายการ: `action_type` · `old_value` → `new_value` · `reason` · `updated_by` · `updated_at` (= MaintainMasterHistory เดิม — แผงประวัติท้ายหน้าจอ 3.1.9) |
| `status_email_rules` | K2 · SRS 3.1.5 | **ORA** `WF_EMAIL_RULE` + `WF_EMAIL_DETAIL` + `WF_EMAIL_CC` (WF = email utility ของ FCS) + **MSSQL** `CompensateHistory.ActionAccountCCMail`/`ActionFRCCMail` | `status_code` | `to_section_code` · `cc_section_code` → workflow_sections | ผู้รับอีเมล TO/CC เมื่อเปลี่ยนสถานะ — ใช้โดย Notification Service |
| `job_configs` | ใหม่ | **MSSQL** `TaskMaster` + `TaskList` (layout fixed-width ต่อฟิลด์) + `ServerMaster`/`ServerType` — ⚠ **ห้าม migrate `ServerMaster.password`** (plaintext → Secret Manager) | `job_no` | ← job_run_histories | schema reference สำหรับ cron + พารามิเตอร์ที่แก้ได้ของ 11 jobs; ไม่ใช่ scope ให้ FE ทำ tab Database ที่ใช้ |
| `job_run_histories` | ใหม่ | **MSSQL** `Journal` + `JournalDetail` (+ **ORA** `FGI_WS_LOG` ถ้ารับข้อ F6) | `run_id` | `job_no` → job_configs | ประวัติรันต่อรอบ (เวลา · แถว · ไฟล์ · ผล) — เดิมอยู่ใน log ไฟล์ |

> Batch Monitor scope note: ตาราง `job_configs` และ `job_run_histories` เป็น schema reference สำหรับ dev/BE เท่านั้น ไม่ใช่ scope ให้ `LLDD/FE/LLDD-FE-Batch-Monitor.*` ต้องทำหน้า database หรือใส่ DB mapping รายละเอียด; เอกสาร FE หน้านั้นทำเฉพาะ tab `แบบฟอร์มพารามิเตอร์` และ `ประวัติการรัน`.

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
| `DecisionProfile` | `decisions` | ผลพิจารณามีชื่อ 3 ชุด (ปุ่ม/flow/ผลลัพธ์) · เปลี่ยนชื่อปุ่มตาม SDD GI ได้โดยไม่ deploy |
| `RunningNumber` | `document_running_numbers` | ออกเลข `YYYY/xxxxx` แบบ atomic ต่อปี — กันเลขชนเมื่อ batch + ผู้ใช้สร้างพร้อมกัน |
| `ImpactCostDetail` | `document_cost_details` | ยอดชดเชยแยกรายเดือน/รายร้านใหม่ — จำเป็นต่อการทวนยอดกับ Statement/SAP |
| `SectionProfile.SectionLimitCost` | `workflow_sections.approve_limit_amount` | ทำให้วงเงิน GM 50,000 / AVP 300,000 (SDD GI) เป็น data |
| `CompensateFlow` (84 คอลัมน์) | คอลัมน์เติมใน `compensation_documents` | `round_no`/`loop_no` · `allmap_url` · `statement_id` · งวดบัญชี · `approver_snapshot` |
| `AttachFileProfile` | คอลัมน์เติมใน `document_attachments` | สถานะอัปโหลด + lifecycle ลบไฟล์บน object storage |
| `CompTransferSBPDate` | `impacted_stores.transfer_sbp_date` | เงื่อนไขร้านก่อน/หลัง 1/10/2014 |

### ตรวจแล้ว — มีของเทียบเท่าอยู่แล้ว ไม่ต้องเพิ่ม

`CompensateHistory` → `consideration_logs` · `CompetInCompenProfile`/`CompetitionProfile` → `document_competitors`/`competitors` · `FactorInCompenProfile`/`FactorProfile` → `document_external_factors`/`external_factors` · `ImpactProfile` → `fgi_impact_stores` + `document_new_stores` · `StatusProfile` → `document_statuses` · `CommonConfig` → `system_configs` · `MaintainHistory`/`MaintainMasterHistory` → `audit_logs` · `Journal`/`JournalDetail` → `job_run_histories` · `CompDocAttachment`/`CompTempAttachment` → `document_attachments` · `CompensateHistory.ActionWaitingDays` → `workflow_tasks.waiting_days`

### ตัดทิ้งตามการตัดสินใจเดิม (ไม่นำเข้า)

กลุ่ม RBAC/เมนูของ K2 — `ApplicationMenu` · `ApplicationRoles` · `AuthorizedMenu` · `MENU` · `RoleForAuthorizedMenu` · `MasterUserViewer` · `MaintainForm` · `MaintainFormAuthorized` · `FormProfile` · `URLPath` · `CompenOrganizeProfile` (ผู้ปฏิบัติงาน) → **ใช้ระบบ SBP เดิม (auth-backend)** ตามการตัดสินใจ 2026-08-05

### ค้างพิจารณา (P1 — ยังไม่เพิ่มในโครง)

| ตารางเดิม | ประเด็น |
|---|---|
| `ListDocumentsPendingRemoval` | นโยบาย **archive/purge เอกสาร** (ArchiveDay → ArchiveDate → PurgeDate → DeleteDate) — โครงใหม่ยังไม่มี data retention plan |
| `TaskMaster` / `TaskList` | นิยาม **layout ไฟล์ interface แบบ fixed-width** (posstart/fieldlength/formatdate ต่อฟิลด์) — ปัจจุบัน hardcode ในโค้ด job · `job_configs` ยังไม่ครอบ |
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
| `FCS_QSSI_SCORE` | `fcs_qssi_scores` |

### ต้องพิจารณาเพิ่ม — **ยังไม่รับเข้าโครง 24 ตาราง รอตัดสินใจ**

| # | ตารางเดิม (FGI) | ช่องว่างที่พบ | ข้อเสนอ |
|---|---|---|---|
| F1 | `FGI_IMPACT_STORE_COMPENSATE` (20 คอลัมน์) | **ยอดชดเชยรายงวดฝั่ง pipeline** ที่เกิด*ก่อน*มีเอกสาร — แยก `COMPENSATE_FORECAST` (ระบบคำนวณ) กับ `COMPENSATE_ADJUST` (คนปรับ) · `COMPENSATE_STATUS` · `COMPENSATE_COMMENT` · `STMT_MONTH`/`STMT_YEAR` (งวด statement) · `APPROVE_DATE` · `COMPENSATE_SEQ`/`SEQ_NO` (รอบ/ครั้งที่) — โครงเรามีแต่ยอดสุดท้ายบน `compensation_documents` | เพิ่ม `fgi_impact_compensations` (zone A) · `FLAG_SEND_BPM` ตัดทิ้งได้ (ไม่ export ไฟล์เข้า K2 แล้ว) แต่ **forecast vs adjust ต้องเก็บคู่กัน** เพราะ SDD GI ให้คีย์ปรับยอดได้ |
| F2 | `FGI_NEW_STORE_COMPENSATE` (19) | ของเดิมเก็บ **ยอด + % ทั้งฝั่ง forecast และ adjust** ต่อร้านเปิดใหม่ (`COMPENSATE_FORECAST_N` / `_PERCENT_N` / `COMPENSATE_ADJUST_N` / `_PERCENT_N`) — โครงเรามีชุดเดียว | ขยาย `document_new_stores` เป็น 2 ชุด (forecast/adjust) หรือแยกตาราง zone A · **ยืนยันการเพิ่ม `compensate_amount` ที่ทำไปแล้ววันนี้ว่าถูกทาง** |
| F3 | `FGI_IMPACT_STORE_INFO` (63) + `FGI_NEW_STORE_INFO` (24) | **snapshot ร้าน + ผู้อนุมัติต่องวด** — ชื่อร้าน/ภาค/ประเภท/นิติบุคคล/ชื่อผู้รับสิทธิ์/วันเริ่ม-ยกเลิก SBP · `URL_ALL_MAP` · `IMPACT_TYPE` · บล็อก **DV/GM/AVP** + **SBP_DV/GM/VP** (18 คอลัมน์จาก `V_FGI_SBP_APPROVER`) — โครงเรา join `stores` สด ๆ และเก็บ `approver_snapshot` เฉพาะบนเอกสาร (ไม่มี **DV/ผู้จัดการเขต**) | ตัดสินใจ snapshot-vs-join: หน้าเอกสารแสดงชื่อร้าน/เจ้าของ/นิติบุคคล ถ้า master เปลี่ยนย้อนหลัง เอกสารเก่าจะเพี้ยน · อย่างน้อยต้องเพิ่ม **DV** เข้า `approver_snapshot` |
| F4 | `FGI_ROS_IMPORT` (14) | **ตัวตั้งของการคำนวณ** ที่ import รายเดือน — `ROS_SALES` · `GP_SALES` · `PHONE_CARD_SALES`/`_PROFIT` · `CASH_CARD_SALES`/`_COMMISSION` · `CUSTOMER_AVG` — โครงเราไม่มีเลย | ตรงกับ **ข้อค้าง P2 ของ gap-analysis** (รายละเอียดการคำนวณตามประเภทร้าน / GP before Split) — ตัดสินใจว่าจะรับเข้า SBPGI หรือปล่อยให้เป็นของ FS/Statement |
| F5 | `MAS_STORE_IMPACT` + `MAS_STORE_IMPACT_PREDICT` (19 + 19) | master คู่ร้านกระทบที่มี **`RENOVATE_START_DATE`/`RENOVATE_END_DATE`** และตาราง **คาดการณ์ร้านที่จะกระทบล่วงหน้า** — โครงเราพูดถึง "ปิด renovate" แต่ไม่มีช่วงวันที่และไม่มี predict | เพิ่มคอลัมน์ renovate ใน `stores` · ส่วน predict ให้ยืนยันว่ายังใช้งานอยู่หรือไม่ก่อนรับเข้า |
| F6 | `FGI_WS_LOG` (7) | log **request/response ของ web service** (`DATA_INPUT`/`DATA_OUTPUT` CLOB · `ERROR_CODE`/`MSG` · start/end) — `job_run_histories` เก็บผลการรัน job และ `interface_transactions` เก็บไฟล์/ACK แต่ไม่มีที่เก็บ payload ราย call | เพิ่ม `integration_call_logs` — ยังจำเป็นแม้ตัด K2 REST เพราะ QSSI/ALLMAP/IAS ยังเป็น service call · ซ้ำประเด็นกับ `LogCompensate` ในรายการ P1 ฝั่ง K2 |
| F7 | `FGI_CANCEL_PROCESS` · `FGI_CANCEL_APPROVE` · `FGI_CANCEL_HISTORY` · `FGI_CANCEL_MAIL` · `FGI_COMPETITOR_DEL` (5 ตาราง + sequence รายภาค `SEQ_FGI_CANCEL_PROCESS_00`–`09`) | **สายอนุมัติ "ขอยกเลิก" อีกชุดหนึ่งที่แยกจาก workflow หลัก** — มี `CANCEL_TYPE`/`CANCEL_SUBTYPE` · ช่วงวันที่ยกเลิก · `APPROVE_SEQ` หลายชั้น · ผู้เปิดเรื่อง (ชื่อ/หน่วยงาน/เบอร์/อีเมล) · mail TO/CC/BCC ต่อชั้น · `STATUS_ID` — **ไม่ถูกอ้างถึงเลยใน `fcsJar` และใน repo `SBP/` ทั้ง 3 ตัว** แปลว่าเป็นของ **เว็บ FCS เดิม** ที่อยู่นอกทั้งสองงาน | **ต้องถามธุรกิจ**: SBPGI รับงานนี้มาด้วยหรือไม่ · ไม่ใช่ตัวเดียวกับผลพิจารณา "หยุดชดเชยประกันรายได้" ในขั้น 06 ของ workflow เรา |
| F8 | `FGI_IMPACT_STORE_ON_PROCESS` (คอลัมน์ที่ยังไม่ครอบ) | `START_COMPENSATE_MONTH/YEAR` + `END_COMPENSATE_MONTH/YEAR` (กรอบงวดที่ชดเชยได้) · `LAST_COMPENSATE_SEQ_NO` · `FLAG_ACTION` · `DATASOURCE` | เติมคอลัมน์เข้า `fgi_impact_processes` — กรอบเริ่ม/จบงวดคือกติกา "เดือนที่ 4 หยุดชดเชย" และการเปิดเรื่องซ้ำตาม SDD GI |

### ขอบเขต — ของที่ **ไม่ใช่** ของ SBPGI (ห้ามทำซ้ำ)

- `MAS_STORE` · `MAS_STORE_TYPE` · `MAS_EMPLOYEE` · `MAS_STORE_COMPETITOR` · `FCS_MONTHLY_SALES` · `FML_SBP_STMT` → **master/ข้อมูลของระบบ FCS/SBP เดิม** (ดู `SBP/README.md` — store-backend เป็นเจ้าของฝั่ง PostgreSQL) · `stores`/`employees`/`branch_types`/`competitors` ในโครงเราคือ **read model ที่ sync มา ไม่ใช่ master**
  - `FML_SBP_STMT` มี `DOCUMENT_ID` + `CHANNEL_TRAN_ID` + `REPORT_LINK` — คือปลายทางของ `compensation_documents.statement_id` ที่เราตั้งไว้ ตรงกันแล้ว
- `V_FGI_SBP_APPROVER` → **auth-backend ของระบบ SBP เดิม** ตามการตัดสินใจ 2026-08-05 · สิ่งที่ต้องบันทึกไว้: view นี้ resolve ผู้อนุมัติจาก `business_user` + `business_user_group` (group_id = 21) โดย key คือ **(store_type, store_area)** แล้วจัดอันดับด้วย `position_level` — SBPGI ต้องส่ง 2 คีย์นี้ไปถามระบบเดิม และ `position_level` คือจุดที่แยก **ผู้รักษาการ** ออกจากผู้อนุมัติจริงตาม SDD GI
- `FGI_*_BK_20250515` (8 ตาราง) → backup ของการ migrate เดิม ไม่นำเข้า

### ตารางที่ตัดออกรอบ 2 — มีอยู่แล้วในระบบ SBP ปัจจุบัน (ตัดสินใจ 2026-08-06)

ตรวจ `SBP/README.md` + repo `srm-sps-spsap-store-backend` (79 entity / PostgreSQL) แล้วพบว่า **10 ตารางในโครงเป้าหมายซ้ำกับของที่ระบบ SBP มีและใช้งานจริงอยู่แล้ว** → **ยึดของ SBP เป็นหลัก ไม่สร้างซ้ำ** (34 → 24 ตาราง)

| ตารางที่ตัด (10) | ของระบบ SBP ที่ใช้แทน | หมายเหตุการต่อยอด |
|---|---|---|
| `workflow_instances` · `workflow_tasks` | **`@srm/glb-workflow`** — `workflow_transaction` (instance) · `workflow_approver` (prepared approvers) · `workflow_history` (timeline) | SBPGI ขอ **workflow version ใหม่** 1 ตัว แล้วใช้ `initializeWorkflow({versionId, referenceId: docNo, userId})` → `addPreparedApprover()` → `triggerEvent()` · `referenceId` = `doc_no` |
| `workflow_sections` · `document_statuses` | **`workflow_state` / `workflow_route` / `workflow_status`** ของ engine (definition เก็บใน DB ไม่ใช่โค้ด) | 5 ขั้น 06/08/01/02/03 = state · การส่งต่อ/ตีกลับ = route · สถานะ 6 ค่า = status · **วงเงินอนุมัติ (GM 50,000 / AVP 300,000) เก็บใน `common_code`** (`code_type = SBPGI_APPROVE_LIMIT`) หรือ eventParam ของ route — ยังคงเป็น data ตาม SDD GI |
| `stores` | **`store` / `mas_store` / `sevenshop`** + `fr_store` · `franchisee` · `juristic` | มี API พร้อมใช้: `GET /store/search`, `/store/list`, `/store/detail`, `/store/opt-name` |
| `zones` | **`mas_zone`** (`zone_id` · `zone_cd` · `zone_name` · `sub_area_flag/name`) | มี API พร้อมใช้: `GET /store/all-regions`, `/store/regions-by-email`, `/store/province-by-region` — ตอบโจทย์ SDD GI ที่ให้ภาคเพิ่มเองโดยไม่แก้หน้าจอ |
| `branch_types` | **`common_code`** (`code_type` + `seq_no` → `code_value`/`code_name`) | มี API พร้อมใช้: `GET /common/common-code`, `/master/common` · ชื่อ FMS/FGI ที่ต่างกันเก็บเป็นคนละ `code_type` |
| `employees` | **`business_user`** + `business_user_group` + `business_group` (auth-backend) | ต่อจากการตัดสินใจ 2026-08-05 · ผู้อนุมัติ resolve ด้วย (store_type, store_area) + `position_level` แบบเดียวกับ view `V_FGI_SBP_APPROVER` |
| `email_templates` | **`email_template`** (`email_template_id` · `subject_format` · `body_format`) + **`email_sent`** (log ทุกฉบับ) + lib `@gosoft-sbp/email-lib` (`emailId`) | 8 template EM-01–08 = **8 แถวใน `email_template` เดิม** · หน้าจอ `email-template.html` แก้ผ่าน endpoint ของ SBPGI แต่เขียนลงตารางเดิม · ไม่ต้องทำ mail sender เอง |
| `system_configs` | **`mas_param`** (`param_name` · `param_value` · `ref_name` · `description` · `is_config` · `active_flag`) | ถ้าต้องการ `category`/`value_type`/`is_editable` ให้**เพิ่มคอลัมน์ใน `mas_param`** ไม่สร้างตารางใหม่ · หน้า `system-config.html` อ่าน/เขียนตารางนี้ |

### ตารางที่ "คล้ายแต่ไม่ใช่" — ตรวจแล้วต้องเก็บของเราไว้

| ตารางของเรา | ของ SBP ที่ใกล้เคียง | เหตุผลที่ยังต้องมี |
|---|---|---|
| `consideration_logs` | `workflow_history` (from_state → to_state · remark · user) | engine ไม่มี `decision_code` · `result_category` (APPROVE/REJECT — ใช้ filter รายงาน) · ไฟล์แนบต่อการพิจารณา → เก็บตารางเราไว้และผูก `transaction_id` ของ engine |
| `document_attachments` | `upload_general` (ไฟล์ของงาน general upload) + service `POST /statement/upload-file-aws` · `download-file-aws` | คนละบริบทไฟล์ · **แต่ให้ใช้ service อัปโหลด/ดาวน์โหลด S3 ของระบบเดิม ไม่เขียน storage layer เอง** |
| `interface_transactions` | `integration_log` (`module` · `service` · `payload`) | ของเราติดตาม ACK ระดับ record/ไฟล์ · `integration_log` เป็น payload log ราย call → **ใช้ `integration_log` แทนตาราง `FGI_WS_LOG` ในข้อ F6 ได้เลย ไม่ต้องเพิ่มตารางใหม่** |
| `audit_logs` | `general_upload_data_page_audit_log` (เฉพาะงาน upload) | ระบบเดิมไม่มี audit กลางของ master → เก็บของเราไว้ |

## ไฟล์ interface ของ K2 เดิม — ใช้ตรวจ field coverage (2026-08-06)

ถอดโครงสร้างจากไฟล์ตัวอย่างจริงใน `docs/ตัวอย่างไฟล์ที่วางให้ K2 เอาเข้าระบบ/` แล้วสรุปไว้ที่ **[`docs/K2-interface-files.md`](docs/K2-interface-files.md)** — ระบบใหม่ตัดไฟล์ทั้ง 3 ตัวออก (Jobs 7/8/9 → เขียน DB ตรง) แต่ต้องใช้ layout นี้ตรวจว่า **เขียนลง DB ครบทุกฟิลด์ที่ K2 เคยได้รับ**

| ไฟล์ | ฟิลด์ | สาระที่กระทบ schema |
|---|---|---|
| `BPM06001O_` | 48 | หัวเอกสาร + งวด + growth + ยอดชดเชย · **24 ฟิลด์ (ครึ่งไฟล์) เป็นบล็อกผู้อนุมัติ DV/GM/AVP** (emp id · ชื่อ-สกุล ไทย/อังกฤษ · อีเมล) → ยืนยันว่า `compensation_documents.approver_snapshot` ต้องมี **DV** ด้วย (ข้อ F3) · ฟิลด์ 9 = `allmap_url` และฟิลด์ 10 = ลิงก์ SBP Statement (`statement_id`) มาจากไฟล์นี้ตรง ๆ |
| `BPM06002O_` | 24 | ร้านเปิดใหม่ต่อร้านถูกกระทบ — `radius` + `radius_unit` · `distance_km` · **`compensate_amount` (ฟิลด์ 16) + `compensate_percent` (ฟิลด์ 17)** → ยืนยันสูตร ยอด × % และผลรวม = ยอดของเอกสาร · ประเภทร้านเป็น **ตัวอักษรเดียว (`B`)** ยืนยันชุด A/B/C/E |
| `BPM06003O_` | 14 | คู่แข่งระดับสาขา — รหัส ALLMAP · **ชื่อไทย + ชื่ออังกฤษ** (→ `competitors.name_th`/`name_en`) · ชื่อสาขา · zone + subzone |

**ข้อเท็จจริงของไฟล์ที่ต้องแก้ในเอกสารเก่า:** ไฟล์กลุ่ม BPM เป็น **UTF-8** (ไม่ใช่ windows-874 — ตัวที่เป็น windows-874 คือ `FRBC0001` ที่ส่งไป STA) · ตัวคั่น `|` · ไม่มีบรรทัดหัวคอลัมน์ · วันที่/ปีเป็น **ค.ศ.** · ชุดตัวอย่างมี `BPM06002O_` ซ้ำ 2 ไฟล์เนื้อหาเหมือนกันทุกไบต์ → **การนำเข้าต้อง idempotent ด้วย business key ไม่ใช่ชื่อไฟล์**

## Canonical Column Contract

DDL, SQL ใน API และ SQL ของ Job ต้องใช้ชื่อด้านล่างตรงกัน; ชื่อในคอลัมน์ “ยกเลิกใช้” ห้ามปรากฏใน implementation ใหม่

| ตาราง | ชื่อ canonical | ยกเลิกใช้ |
|---|---|---|
| `workflow_instances` | `instance_id`, `doc_no`, `instance_status`, `started_at`, `started_by` | `status`; `instance_id` ต้องส่งเข้าตอน insert |
| `system_configs` | `config_key`, `category`, `config_value`, `value_type`, `unit`, `description`, `is_editable` | `secret_flag` และ secret ทุกชนิด |
| `sales_transactions` | `txn_date`, `window_no`, `sales_amount`, `sales_diff`, `is_outlier` | `sale_date`, `window_code`, `net_sales` |
| `consideration_logs` | `result`, `result_category`, `detail`, `consider_by`, `action_datetime` | `result_code`, `comment`, `considered_by`, `considered_at` |
| `interface_transactions` | PK `id`, เวลา ACK `acked_at` | API อาจ alias เป็น `trackingId`/`receiveDate` แต่ SQL ต้องอ้าง `id`/`acked_at` |
| `fgi_impact_processes` | `workflow_generation_status` | ห้าม duplicate สถานะเดียวกันใน `fgi_impact_stores` |
| `workflow_sections` | `approve_limit_amount` (numeric) | ห้าม hardcode วงเงินใน service — อ่านจากคอลัมน์นี้ |
| `zones` / `branch_types` / `decisions` | `zone_code` · `branch_type_code` · `decision_code` | ห้าม hardcode รายการภาค / ประเภทสาขา / ปุ่มผลพิจารณาใน FE |
| `document_running_numbers` | `year`, `last_running_no` | ห้ามใช้ `MAX(running_no)+1` — ต้อง lock แถวปีนั้น |

## กุญแจเชื่อมข้ามระบบ (Cross-System Keys)

1. **`impacted_stores.store_code = fgi_impact_stores.impacted_store_code`** — สะพานหลักโซน C (K2) ↔ โซน A (FGI/FCS) · รหัสร้าน 5 หลักเดียวกันทั้งระบบ
   - **`stores`** = master สาขา 7-Eleven ทุกประเภท · `impacted_stores` เป็น subset ร้าน SP · ร้านเปิดใหม่ (`document_new_stores.new_store_code`) อ้าง `stores` ตัวเดียวกัน — เป็นแหล่งของ popup ค้นหาร้านในหน้าสร้างเอกสาร
2. **`*.impact_process_id → fgi_impact_processes.id`** — hub กลางของคู่ร้าน ยอดขาย และคู่แข่งในหนึ่งรอบชดเชย (ใหม่)
3. **`compensation_documents.impact_process_id → fgi_impact_processes`** — FK ใหม่ **1 รอบชดเชย : 1 เอกสาร** แทนการส่งไฟล์ BPM06001O (48 ฟิลด์) ข้ามระบบ (ใหม่)
4. **`workflow_instances.doc_no → compensation_documents`** — เปิด instance เมื่อผ่าน Gen Flow Gate · สถานะ instance แทน `workflow_generation_status = Y` ของเดิม (ใหม่)
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
- API ที่อ่าน/เขียนตาราง: [api.md](api.md) · `plan-api.html` (47 endpoints 9 กลุ่ม — กลุ่ม Auth/RBAC และ Master ผู้ปฏิบัติงาน/สิทธิ์ถูกตัดไปใช้ระบบเดิม · รวม System Config 5 เส้น, กลุ่ม Lookup 4 เส้น และ `GET /documents/{docNo}/sales`)
- Schema ต้นทางแยกระบบ: `fgi-database.html` (FGI/FCS) · `k2-database.html` (K2, 16 ตาราง + ER diagram)
