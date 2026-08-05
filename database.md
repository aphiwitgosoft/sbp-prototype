# Database — FGI/FCS + K2 (Target Schema ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุปโครงสร้างฐานข้อมูลเป้าหมายของระบบใหม่
> **แหล่งอ้างอิงหลัก:** `plan-database.html` (หน้า DB FGI/FCS + K2)
> **อ้างอิงประกอบ:** `fgi-database.html`, `k2-database.html`, เอกสาร Batch v4.0 (Data Dictionary หน้า 6–10), SRS ประกันรายได้-K2 v3.1
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง database ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-database.html` ให้ตรงกัน

## บริบทระบบใหม่

ระบบใหม่ **รวม EAI และ K2 เข้าเป็นส่วนหนึ่งของ SBPGI** — งาน FGI/FCS batch และงานเอกสาร/workflow K2 ทำงานบน **ฐานข้อมูลเดียวกัน** ไม่มีการส่งไฟล์ผ่าน EAI อีกต่อไป (ดูรายละเอียด flow ที่ [workflow.md](workflow.md))

ผลต่อ schema:
- ไฟล์ภายใน `BPM06001O_` (48 ฟิลด์) / `BPM06002O_` / `BPM06003O_` ที่เคยส่งผ่าน EAI ไป K2 → แทนด้วย FK `compensation_documents.impact_process_id` เชื่อมตรงในฐานข้อมูลเดียวกัน
- K2 engine ภายนอก → แทนด้วยตาราง `workflow_instances` + `workflow_tasks` ภายใน
- ตาราง tracking เดิม `FGI_CONFIRM_RECEIVE_DATA` → แทนด้วย `interface_transactions` (typed FK)
- **SDD v7.5:** ตัดขั้นบัญชี 04/05 ออกจาก workflow — `workflow_sections` เหลือ 5 แถวใช้งาน (06/08/01/02/03) · `document_statuses` เหลือ 6 ค่า (ตัด "รอฝ่ายบัญชี SBP" / "รอบัญชีปฏิบัติการภาค") · บัญชีตรวจสอบผ่านรายงาน SBP Mall + กระทบ SAP นอกระบบ

## ภาพรวม

- **29 ตาราง** ใน Target Schema เดียว (1 schema ใช้ร่วมกัน)
- **3 Data Zones**: A = FGI/FCS Impact Pipeline · B = K2 เอกสาร & Workflow · C = Master/Config ใช้ร่วม
- **4 Core IDs** ใช้ trace งาน (Data Spine)
- มาตรฐานชื่อ: อังกฤษ `lower_snake_case` ทั้ง schema · ป้ายที่มา (FGI/FCS), (K2), (ใหม่) ต้องคงไว้เสมอ
- **ตัดสินใจ 2026-08-05:** RBAC (`roles`/`menus`/`menu_permissions`/`user_accounts`) และผู้ปฏิบัติงาน (`operator_assignments`) **ไม่สร้างใน SBPGI** — ใช้ระบบสิทธิ์/ผู้ใช้ของระบบ SBP เดิม (ดูหัวข้อ "ตารางที่ตัดออก" ท้าย Zone C) · เดิมนับเป็น 34 ตาราง

## Data Spine — เส้นทางข้อมูลหลัก

หนึ่งรายการผลกระทบเดินผ่าน ID หลักตามลำดับ ตารางอื่นเป็นรายละเอียด/master ที่เกาะกับ spine นี้:

| ลำดับ | Zone | Key | ความหมาย |
|---|---|---|---|
| 1 | A | `impact_process_id` | หนึ่งร้านถูกกระทบ + หนึ่งงวด — hub ของยอดขาย ร้านใหม่ และคู่แข่ง |
| 2 | B | `doc_no` | เอกสารประกันรายได้รูปแบบ `YYYY/xxxxx` (ปี พ.ศ.) เชื่อมกลับ impact process |
| 3 | B | `instance_id` | Workflow instance หนึ่งชุดต่อเอกสาร ติดตามตั้งแต่เริ่มถึงจบ |
| 4 | B | `task_id` | งานของแต่ละ Section และผู้รับผิดชอบ — แหล่งข้อมูลหน้า inbox |
| 5 | C | `employee_id` | ผู้ปฏิบัติงานที่อ้างร่วมกันทุกขั้น — ตัวตน/สิทธิ์เมนูมาจากระบบ SBP เดิม (auth-backend) ผ่าน user-context header ไม่ใช่ตารางใน SBPGI |

## Data Dictionary (29 ตาราง)

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
| `compensation_documents` | K2 | `doc_no` (YYYY/xxxxx) | `status_code` · `current_section_code` · `impacted_store_code` · **`impact_process_id` (ใหม่)** | เอกสารประกันรายได้ — หัวใจโซน B · FK ใหม่เชื่อม hub โซน A แทนไฟล์ 48 ฟิลด์ |
| `document_new_stores` | K2 | id | `doc_no` → compensation_documents | ร้านเปิดใหม่ · `distance_km` · %ชดเชย (**ผลรวมต้อง = 100%**) |
| `document_competitors` | K2 | id | `doc_no` · `competitor_code` → competitors | คู่แข่งในเอกสาร · `source_system` = ALLMAP (จาก pipeline) / USER (ผู้ใช้เพิ่มเอง) |
| `document_external_factors` | K2 | id | `doc_no` · `factor_code` → external_factors | ปัจจัยภายนอกที่ใช้ในเอกสาร + ช่วงวันที่ |
| `consideration_logs` | K2 | id | `doc_no` → compensation_documents | ประวัติพิจารณาทุกขั้น (ผู้พิจารณา · Section · ผล · เวลา) · `result_category` (APPROVE/REJECT/PENDING) สำหรับ filter **ประกันรายได้/ไม่ประกันรายได้** หน้ารายงานตรวจสอบประกันรายได้ (k2-report · SDD v7.5) |
| `document_attachments` | K2 | id | `doc_no` → compensation_documents | ไฟล์แนบ ≤ 5MB ต่อไฟล์ · แยกตาม Section ที่แนบ |
| `compensation_histories` | K2 | id | `store_code` · `ref_doc_no` | ประวัติชดเชยต่อร้าน/รอบ · `submit_account_month` เดือนส่งบัญชี (→ ไฟล์ FRBC0001 ของ Job 6) |
| `workflow_instances` | ใหม่ | `instance_id` | `doc_no` → compensation_documents | instance ของ workflow ภายใน (แทน K2 engine) · สถานะ instance แทน workflow_generation_status=Y |
| `workflow_tasks` | ใหม่ | `task_id` | `instance_id` · `section_code` · `assignee_employee_id` | งานค้างต่อ Section — แหล่งข้อมูลหน้างานรอดำเนินการ (inbox) · ฐานของ reminder รายสัปดาห์ (จันทร์ 10:00) และ escalation 30/45/60 วัน (จาก Approve Flow เดิม — ดู workflow.md) |

### Zone C · Shared — Master, RBAC, Configuration และ Audit

| ตาราง | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท |
|---|---|---|---|---|
| `stores` | FGI/FCS | `store_code` | ← impacted_stores (subset SP) · ← `document_new_stores.new_store_code` | master สาขา 7-Eleven ทุกประเภท (SP / เปิดใหม่ / ปิด renovate) — แหล่งค้นหาร้านของหน้า `k2-create.html` (API `/stores/search`) |
| `impacted_stores` | K2 | `store_code` | = `impacted_store_code` ของโซน A (สะพานหลักสองระบบ) · subset SP ของ `stores` | ข้อมูลร้าน SP master |
| `workflow_sections` / `document_statuses` | K2 | `section_code` / `status_code` | อ้างโดย compensation_documents · workflow_tasks · status_email_rules | ขั้นตอน **06/08/01/02/03 (5 ขั้น · ตัดบัญชี 04/05 ตาม SDD v7.5)** · สถานะเอกสาร **6 ค่า: 06/08/01/02/03/99** โดย 99 = เสร็จสิ้นดำเนินการ — แถวบัญชี (04/05) และสถานะ "รอฝ่ายบัญชี/รอบัญชีปฏิบัติการภาค" ยกเลิกใช้งาน |
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
- API ที่อ่าน/เขียนตาราง: [api.md](api.md) · `plan-api.html` (44 endpoints 9 กลุ่ม — กลุ่ม Auth/RBAC และ Master ผู้ปฏิบัติงาน/สิทธิ์ถูกตัดไปใช้ระบบเดิม · รวม System Config 5 เส้น, กลุ่ม Lookup 4 เส้น และ `GET /documents/{docNo}/sales`)
- Schema ต้นทางแยกระบบ: `fgi-database.html` (FGI/FCS) · `k2-database.html` (K2, 16 ตาราง + ER diagram)
