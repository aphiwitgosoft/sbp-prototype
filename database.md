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

- **34 ตาราง** ใน Target Schema เดียว (1 schema ใช้ร่วมกัน) — เพิ่ม 5 ตารางจากการเทียบ DB เดิมของ K2 เมื่อ 2026-08-06 (ดูหัวข้อ "ช่องว่างเทียบ DB เดิมของ K2" ท้ายไฟล์)
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

## Data Dictionary (34 ตาราง)

### Zone A · FGI/FCS — Impact Pipeline และ External Interfaces

| ตาราง | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|
| `fgi_impact_stores` | FGI/FCS | id | `impact_process_id` → fgi_impact_processes · `impacted_store_code` → impacted_stores | คู่ร้านกระทบ–เปิดใหม่ · `verify_status` (W/P/Y/N) · ข้อมูล %/ยอดชดเชยต่อคู่ร้าน |
| `fgi_impact_processes` ★ | FGI/FCS | id | `impacted_store_code` · แม่ของตารางรายรอบทั้งหมด | **hub รอบชดเชย** · `action_status` (Y/W/N) · `last_compensation_amount` · source of truth ของ `workflow_generation_status` (W/Y/N) |
| `fgi_impact_sales_summaries` | FGI/FCS | id | `impact_process_id` → fgi_impact_processes · → sales_transactions (1:N) | หัวยอดขาย · `growth_rate_diff` · `total_working_days` (เกณฑ์ 60 วัน) |
| `sales_transactions` | FGI/FCS | id | `sales_summary_id` → fgi_impact_sales_summaries | ยอดขายรายวันจาก IAS · 4 หน้าต่าง × 15 วัน · sales_diff/outlier ≥ 50 แบบจับคู่ |
| `fgi_impact_competitors` | FGI/FCS | id | `impact_process_id` → fgi_impact_processes · → document_competitors (นำเข้า) | คู่แข่งจาก ALLMAP (data_source=ALM) · งวดล่าสุดต่อร้าน |
| `fcs_qssi_scores` | FGI/FCS | id | UK: store_id + category_code + งวด | คะแนน QSSI 6 หมวด (8,9,12,1,10,16) จาก Job 1 |
| `interface_transactions` | ใหม่ | id | typed FK: `impact_process_id` / `sales_summary_id` / `doc_no` | แทน FGI_CONFIRM_RECEIVE_DATA — เลิก polymorphic PK + purge ทำงานจริง (แก้ E20) |

### Zone B · K2 — เอกสารประกันรายได้และ Workflow ภายใน

| ตาราง | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|
| `compensation_documents` | K2 | `doc_no` (YYYY/xxxxx) | `status_code` · `current_section_code` · `impacted_store_code` · **`impact_process_id` (ใหม่)** | เอกสารประกันรายได้ — หัวใจโซน B · FK ใหม่เชื่อม hub โซน A แทนไฟล์ 48 ฟิลด์ · **คอลัมน์ที่เติมจาก CompensateFlow เดิม (2026-08-06):** `round_no`/`loop_no` (= CompMainLoopNo/CompLoopNo — หน้าจอแสดง "รอบ 1 · ครั้งที่ 3") · `allmap_url` (= CompUrlMap — ปุ่ม Link To ALLMAP) · **`statement_id`** (= CompStatementID — โยงกลับ SBP Statement ที่เป็นต้นทางการสร้างเอกสารตามกระบวนการ FS ใหม่) · `account_year`/`account_month` (งวดบัญชี) · `approver_snapshot` (JSONB — FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร ตามที่ CompensateFlow เก็บไว้ 25 คอลัมน์: **จำเป็นเป็นพิเศษเมื่อ RBAC ย้ายไปใช้ระบบเดิม เพราะตำแหน่งจาก HR Connect เปลี่ยนได้ และผู้รักษาการเป็นผู้อนุมัติไม่ได้**) |
| `document_new_stores` | K2 | id | `doc_no` → compensation_documents | ร้านเปิดใหม่ · `distance_km` · %ชดเชย (**ผลรวมต้อง = 100%**) |
| `document_competitors` | K2 | id | `doc_no` · `competitor_code` → competitors | คู่แข่งในเอกสาร · `source_system` = ALLMAP (จาก pipeline) / USER (ผู้ใช้เพิ่มเอง) |
| `document_external_factors` | K2 | id | `doc_no` · `factor_code` → external_factors | ปัจจัยภายนอกที่ใช้ในเอกสาร + ช่วงวันที่ |
| `consideration_logs` | K2 | id | `doc_no` → compensation_documents | ประวัติพิจารณาทุกขั้น (ผู้พิจารณา · Section · ผล · เวลา) · `result_category` (APPROVE/REJECT/PENDING) สำหรับ filter **ประกันรายได้/ไม่ประกันรายได้** หน้ารายงานตรวจสอบประกันรายได้ (k2-report · SDD v7.5) |
| `document_attachments` | K2 | id | `doc_no` → compensation_documents | ไฟล์แนบ ≤ 5MB ต่อไฟล์ · แยกตาม Section ที่แนบ · **เติมจาก AttachFileProfile เดิม (2026-08-06):** `file_size` · `upload_status` + `upload_message` (ผลอัปโหลดขึ้น object storage) · `purge_flag`/`storage_delete_status` (lifecycle ลบไฟล์บน S3 — ของเดิมมี FlagPurgeData/FlagDeleteS3/StatusCodeDeleteS3 ครบ) |
| `compensation_histories` | K2 | id | `store_code` · `ref_doc_no` | ประวัติชดเชยต่อร้าน/รอบ · `submit_account_month` เดือนส่งบัญชี (→ ไฟล์ FRBC0001 ของ Job 6) |
| `workflow_instances` | ใหม่ | `instance_id` | `doc_no` → compensation_documents | instance ของ workflow ภายใน (แทน K2 engine) · สถานะ instance แทน workflow_generation_status=Y |
| `workflow_tasks` | ใหม่ | `task_id` | `instance_id` · `section_code` · `assignee_employee_id` | งานค้างต่อ Section — แหล่งข้อมูลหน้างานรอดำเนินการ (inbox) · `waiting_days` (= CompWaitingDays เดิม) · ฐานของ reminder รายสัปดาห์ (จันทร์ 10:00) และ escalation 30/45/60 วัน (จาก Approve Flow เดิม — ดู workflow.md) |
| `document_cost_details` ★ | K2 (ImpactCostDetail) | id | `doc_no` → compensation_documents · `new_store_code` | **(เพิ่ม 2026-08-06)** ยอดชดเชย**แยกรายเดือน/รายร้านเปิดใหม่** — `cost_year`/`cost_month` · `cost_target` (เป้ายอดขาย) · `cost_amount` · แยกค่าของร้านใหม่ (`_n`) และร้านใหม่สะสม (`_nc`) ตาม ImpactCostDetail เดิม · ของเดิมในโครงเรามีแค่ยอดรวมต่อเอกสาร + %ต่อร้าน ทำให้ทวนยอดรายเดือนกับ Statement/SAP ไม่ได้ |
| `document_running_numbers` ★ | K2 (RunningNumber) | `be_year` | ออกเลขให้ compensation_documents | **(เพิ่ม 2026-08-06)** ตัวนับเลขเอกสารต่อปี พ.ศ. (`last_running_no`) — ออกเลข `YYYY/xxxxx` แบบ atomic (`UPDATE … RETURNING` / row lock) กันเลขชนกันเมื่อ batch และผู้ใช้สร้างพร้อมกัน · เดิมโครงเราไม่ระบุที่เก็บตัวนับ |

### Zone C · Shared — Master, RBAC, Configuration และ Audit

| ตาราง | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|
| `stores` | FGI/FCS | `store_code` | ← impacted_stores (subset SP) · ← `document_new_stores.new_store_code` | master สาขา 7-Eleven ทุกประเภท (SP / เปิดใหม่ / ปิด renovate) — แหล่งค้นหาร้านของ popup ร้านเปิดใหม่ในหน้าเอกสาร (API `/stores/search`) |
| `impacted_stores` | K2 | `store_code` | = `impacted_store_code` ของโซน A (สะพานหลักสองระบบ) · subset SP ของ `stores` | ข้อมูลร้าน SP master · **`transfer_sbp_date` (เพิ่ม 2026-08-06 = CompTransferSBPDate เดิม)** — วันที่โอนเป็นร้าน SP ใช้กับเงื่อนไขร้านก่อน/หลัง 1/10/2557 ของ Approve Flow เดิม |
| `workflow_sections` / `document_statuses` | K2 | `section_code` / `status_code` | อ้างโดย compensation_documents · workflow_tasks · status_email_rules | ขั้นตอน **06/08/01/02/03 (5 ขั้น · ตัดบัญชี 04/05 ตาม SDD v7.5)** · สถานะเอกสาร **6 ค่า: 06/08/01/02/03/99** โดย 99 = เสร็จสิ้นดำเนินการ — แถวบัญชี (04/05) และสถานะ "รอฝ่ายบัญชี/รอบัญชีปฏิบัติการภาค" ยกเลิกใช้งาน · **`workflow_sections.approve_limit_amount` (เพิ่ม 2026-08-06 = SectionProfile.SectionLimitCost เดิม)** — วงเงินอนุมัติต่อขั้นเป็น **data ไม่ใช่ค่า hardcode**: 02 = 50,000 · 03 = 300,000 ตาม SDD GI (คู่กับ `system_configs.workflow.gm_amount_limit` / `avp_amount_limit` — ตารางนี้เป็นค่าจริงที่ Workflow Engine อ่าน) |
| `zones` ★ | K2 (ZoneProfile) | `zone_code` | ← stores/impacted_stores · ใช้ในตัวกรองรายงาน | **(เพิ่ม 2026-08-06)** master **ภาค/โซน** — ชุดปัจจุบัน **13 รหัส**: `BE BS NEU REU RSU BG BW RC RN BN NEL REL RSL` (`zone_code` 2–3 หลัก + `zone_name`) — **SDD GI บังคับ**: "กรณีมีการเพิ่มภาคในระบบ ให้แสดง Checkbox เพิ่มแบบ Auto โดยไม่ต้องแก้หน้าจอ" → รายชื่อภาค 13 ค่าต้องมาจากตารางนี้ ห้าม hardcode ใน FE |
| `branch_types` ★ | K2 (BranchTypeProfile) | `branch_type_code` | ← stores.branch_type_code · ใช้ใน Gen Flow Gate | **(เพิ่ม 2026-08-06)** master **ประเภทสาขา** — เก็บชื่อ 3 ชุดตามของเดิม: `branch_type_name` · **`fms_name`** · **`fgi_name`** (ระบบ FMS กับ FGI เรียกประเภทเดียวกันคนละชื่อ — ต้อง map ไม่ใช่เทียบ string ตรง) · เซ็ตที่ผ่าน Gen Flow Gate (FAM/FB1/FC1/FB2/FVB/FVC) และประเภทร้าน 8 ชนิด/4 ค่าในรายงาน อ่านจากตารางนี้ |
| `decisions` ★ | K2 (DecisionProfile) | `decision_code` | ← consideration_logs.decision_code · workflow transition | **(เพิ่ม 2026-08-06)** master **ผลพิจารณา** — `decision_name` (ข้อความบนปุ่ม · ไทย verbatim) · **`flow_name`** (ชื่อที่ใช้ในผังflow) · **`result_name`** (ชื่อที่ใช้แสดงผลในรายงาน/ประวัติ) ซึ่งของเดิมแยกกัน 3 ชุด · ทำให้การเปลี่ยนชื่อปุ่มตาม SDD GI ("ส่งฝ่ายส่งเสริมฯ" → "ส่งหน่วยงานส่งเสริมฯ") แก้ที่ data ไม่ต้อง deploy · `consideration_logs.result` ยังเก็บข้อความ ณ เวลากดไว้เป็น snapshot |
| `employees` | FGI/FCS | `employee_id` | ← `workflow_tasks.assignee_employee_id` | master พนักงานองค์กร (HR) — batch join อยู่แล้ว · การ resolve ผู้รับผิดชอบต่อ section/พื้นที่ใช้ user–group ของระบบเดิม (auth-backend) ไม่ใช่ตารางใน SBPGI |
| `external_factors` | K2 · SRS 3.1.9 | `factor_code` | ← document_external_factors | ปัจจัยภายนอก master · รหัสห้ามซ้ำ |
| `competitors` | K2 | `competitor_code` | ← document_competitors | ร้านคู่แข่ง 24 ราย (108 Shop, Lotus Express, CJ …) |
| `audit_logs` | K2 | id | `table_name` + `ref_key` (generic) | ประวัติแก้ไข master แบบหลายรายการ: `action_type` · `old_value` → `new_value` · `reason` · `updated_by` · `updated_at` (= MaintainMasterHistory เดิม — แผงประวัติท้ายหน้าจอ 3.1.9) |
| `status_email_rules` | K2 · SRS 3.1.5 | `status_code` | `to_section_code` · `cc_section_code` → workflow_sections | ผู้รับอีเมล TO/CC เมื่อเปลี่ยนสถานะ — ใช้โดย Notification Service |
| `email_templates` | ใหม่ | `template_code` (EM-01–08) | อ่านคู่กับ status_email_rules โดย Notification Service | **เนื้อหา 8 email template** (subject/body + ตัวแปร merge) แก้ได้จากหน้า `plan-email.html` — ยกจากเดิมที่เก็บ localStorage มา persist จริงฝั่ง server · From/To/Cc ล็อกตาม `status_email_rules` (rules = ผู้รับ, templates = เนื้อหา) · ประวัติแก้ไข/รีเซ็ต → `audit_logs` · ถ้อยคำ template เป็น beyond SRS (SRS กำหนดเฉพาะผู้รับ/จังหวะส่ง) |
| `job_configs` | ใหม่ | `job_no` | ← job_run_histories | schema reference สำหรับ cron + พารามิเตอร์ที่แก้ได้ของ 11 jobs; ไม่ใช่ scope ให้ FE ทำ tab Database ที่ใช้ |
| `job_run_histories` | ใหม่ | `run_id` | `job_no` → job_configs | ประวัติรันต่อรอบ (เวลา · แถว · ไฟล์ · ผล) — เดิมอยู่ใน log ไฟล์ |
| `system_configs` | ใหม่ | `config_key` | อ่านโดยทุก service · ประวัติแก้ไข → audit_logs | **Global config แบบ key–value** (หน้าจอ `system-config.html`) — `config_key` เป็น dot notation (`impact.radius_bkk_km`, `workflow.gm_amount_limit`, `workflow.avp_amount_limit`) · `category` (IMPACT/WORKFLOW/DOCUMENT/AUTH/NOTIFICATION/BATCH) · `value_type` (NUMBER/STRING/BOOLEAN/JSON/CRON) ใช้ validate ก่อนบันทึก · `is_editable=false` = ค่าคงที่ทางธุรกิจ (รัศมี 1/2 กม. · วงเงิน GM 50,000 / AVP 300,000 ตาม SDD GI 24/02/2026 — แทน `workflow.avp_amount_threshold` 100,000 เดิม · เกณฑ์ 60 วัน · เกณฑ์ −10 ตามข้อ 8.2) แก้ผ่าน UI/API ไม่ได้ · **ห้ามเก็บ secret** (อยู่ Secret Manager — P0) · service cache 5 นาที + invalidate เมื่อแก้ไข · พารามิเตอร์เฉพาะราย job ยังอยู่ `job_configs` |

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
| `CompTransferSBPDate` | `impacted_stores.transfer_sbp_date` | เงื่อนไขร้านก่อน/หลัง 1/10/2557 |

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
| `document_running_numbers` | `be_year`, `last_running_no` | ห้ามใช้ `MAX(running_no)+1` — ต้อง lock แถวปีนั้น |

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
