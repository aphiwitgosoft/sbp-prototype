# SBPGI เทียบระบบ SBP เดิม — เอกสารตัดสินใจว่าจะตัดอะไรออกจากแผน

> **สถานะ:** ร่างเพื่อการตัดสินใจ · ตรวจ 07/08/2026
> **ผู้อ่านเป้าหมาย:** เจ้าของโครงการ (ตัดสินใจ) · Tech Lead FE/BE (ลงมือ)
> **แหล่งหลักฐาน (อ่านจากไฟล์จริงทุกข้อ):**
> - `SBP/db-schema-sps_store.md` — schema `sps_store` · 198 ตาราง · 3,061 คอลัมน์ (ดึงสดจาก DB dev 07/08/2026 · PostgreSQL 17.7)
> - `SBP/db-schema-sps_auth.md` — schema `sps_auth` · 78 ตาราง · 1,335 คอลัมน์
> - ซอร์สจริง `SBP/srm-sps-spsap-store-backend/` และ `SBP/srm-sps-spsap-sbp-bff/`
> - แผนของเรา: `database.md` (21 ตารางเป้าหมาย) · `api.md` (30 เส้น 6 กลุ่ม) · `workflow.md` (12 ขั้น)
> - `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` (workflow engine กลาง)
>
> **เอกสารนี้ไม่แก้ `database.md` / `api.md` / `workflow.md`** — เป็นข้อเสนอเพื่อขอมติ เมื่อได้มติแล้วค่อยไปแก้ (ดูหัวข้อสุดท้าย)

---

## 1. สรุปผู้บริหาร

### ตัวเลขเดียวที่ต้องจำ

ขอบเขตที่ตรวจ = **21 ตารางเป้าหมาย + 8 ความสามารถระดับแพลตฟอร์ม** โดย "การออกเลขเอกสารรันนิ่ง" นับซ้ำกันระหว่างสองชุด (เป็นทั้งตารางและความสามารถ) → **รวมของจริง 28 รายการ**

| กลุ่มคำตัดสิน | จำนวน | ความหมาย |
|---|---:|---|
| 🟢 **ตัดออกจากแผนได้เลย** | **4** | ระบบเดิมมีของที่ใช้ได้จริง ทำงานอยู่แล้ว ไม่ต้องสร้างและไม่ต้องแก้ของเดิม |
| 🟡 **ใช้ของเดิมร่วมได้ แต่ต้องเพิ่ม/ครอบ** | **11** | ลดงานได้จริง แต่มีเงื่อนไข — ต้องเพิ่มคอลัมน์ · เพิ่ม index · หรือเขียนชั้นครอบ และหลายข้อ**ต้องขอ sign-off จากทีมเจ้าของตาราง** |
| 🔴 **ไม่มีของเดิม ต้องทำเองเต็ม** | **13** | แกนธุรกิจประกันรายได้ — ยืนยันแล้วว่าไม่มีอยู่ในระบบเดิมเลย |

### สิ่งที่ยืนยันหนักแน่นที่สุด

**แกน pipeline ประกันรายได้ไม่มีในระบบเดิมแม้แต่นิดเดียว** — ค้นทั้ง 276 ตาราง / 4,396 คอลัมน์ ด้วยคำว่า `impact` · `compensat` · `guarantee` · `income` · `competitor` · `growth` · `outlier` · `distance` · `radius` · `latitude` · `longitude` · `window_no` ได้ **0 hit ทุกคำ** ทั้งชื่อตารางและชื่อคอลัมน์ (คำว่า `factor` เจอ 4 ครั้ง เป็น `fillfactor='90'` ของ index ล้วน)

แปลว่า: **โซน A (7 ตาราง) และแกนเอกสารในโซน B ต้องสร้างใหม่ทั้งหมด — ไม่มีทางลัด** สิ่งที่ตัดได้อยู่ในชั้นแพลตฟอร์ม (workflow · อีเมล · config · storage) ไม่ใช่ชั้นธุรกิจ

### ประหยัดงานได้เท่าไร

| สิ่งที่ตัด/ยืม | ประหยัดโดยประมาณ |
|---|---:|
| Workflow engine 5 ขั้น (ไม่ต้องเขียน state machine + 4 ตาราง) | 15–20 วัน-คน |
| ระบบ template อีเมล + ตัวส่ง + หน้าจอดูแล | 5–7 วัน-คน |
| หน้าจอ + API + ตาราง config กลาง | 3–4 วัน-คน |
| ไม่ต้อง migrate `fcs_qssi_score` 23.9 ล้านแถว + ได้ import pipeline ที่ทำงานอยู่แล้ว | 3–5 วัน-คน |
| S3 storage layer / credential / presign | 2–3 วัน-คน |
| Excel export lib + จัดการชื่อไฟล์ภาษาไทย (`ResponseHelper.contentDispositionThaiFileName` มีอยู่แล้ว) | 1–2 วัน-คน |
| Master 3 ตัว (ถ้าเลือกใช้ `common_code`) | 1–2 วัน-คน |
| เสียบกล่องงานรวมข้ามระบบ (`GET /api/workflow/pending` คืนทุก version อยู่แล้ว) | 1 วัน-คน |
| **รวมประหยัด** | **~31–44 วัน-คน** |
| **หัก** งานเชื่อม/ปรับ/ทดสอบที่เกิดจากการใช้ของเดิม (migration `fcs_qssi_score` · PoC อีเมล · register workflow version · ขอ sign-off) | −8 ถึง −12 วัน-คน |
| **สุทธิ** | **~20–35 วัน-คน** |

> ⚠️ ตัวเลขนี้จะเป็นจริงก็ต่อเมื่อผ่าน **Decision Points ข้อ DP-1 ถึง DP-4** ด้านล่าง ถ้าเลือกทางที่ปลอดภัยกว่าในบางข้อ ตัวเลขจะลดลงประมาณ 5–8 วัน-คน — ซึ่งอาจคุ้มกับความเสี่ยงที่ตัดออกไป

### 3 เรื่องที่ต้องตัดสินใจก่อนล็อกดีไซน์ (เรียงตามผลกระทบ)

1. **DP-1 · `reference_id` ของ workflow = `doc_no` หรือ surrogate id** — แผนปัจจุบัน (`database.md` Cross-System Key ข้อ 4) อ้างว่าลอกแพตเทิร์นจาก `cooperation-request` แต่ **แพตเทิร์นนั้นไม่มีอยู่จริง** โค้ดจริงส่ง `referenceId: trnId` (PK ตัวเลข) ทุกจุด
2. **DP-2 · `workflow_transaction` ใน `sps_store` ไม่มี PK และไม่มี index เลย** ทั้งที่มี 19,283 แถว — ต้องคุยกับทีมเจ้าของ `@srm/glb-workflow` ก่อน ไม่ใช่ "เพิ่ม index เอง"
3. **DP-3 · `impacted_stores` เป็น view หรือตาราง** — `store_sbp` คีย์ด้วย `order_id` (สัญญา) ไม่ใช่ `store_code` และ `v_fr_store_active` ตัดร้านที่ยกเลิกเกิน 1 เดือนออก ทำให้เอกสารย้อนหลังหาร้านไม่เจอ

---

## 2. ตารางตัดสินใจ

### 🟢 กลุ่ม A — ตัดออกจากแผนได้เลย (4 รายการ)

| สิ่งที่จะสร้าง | ของเดิมที่มี (จำนวนแถวจริง) | คำตัดสิน | ต้องทำอะไรถ้าใช้ของเดิม |
|---|---|---|---|
| **Workflow engine 5 ขั้น** (เดิมวางไว้ 4 ตาราง: `workflow_instances` · `workflow_tasks` · `workflow_sections` · `document_statuses` — ตัดไปแล้ว 2026-08-06) | `sps_store.workflow_transaction` 19,283 · `workflow_approver` 96,542 · `workflow_history` 38,010 · `workflow_route` 43 · `workflow_state` 18 · `workflow_status` 22 + wrapper `src/modules/workflow/workflow.service.ts` | ✅ **ตัด** — engine ทำงานจริงแล้ว | ขอ **workflow version ใหม่ 1 ตัว** (1 ระบบ = 1 version) · ลง 5 state (06/08/01/02/03) + route ที่ใส่ `condition_json` วงเงิน · กรอก `url_main`/`url_param_mapping` ตอน register · ⚠️ ดู **DP-2** (ไม่มี PK/index) และ **DP-1** (reference_id) |
| **ระบบอีเมล 8 template EM-01–08** (`email_templates` + หน้าจอ + mail sender) | `sps_store.email_template` 85 · `email_sent` 5,214 (มี `mail_cc` text) · `MailService` + `EmailLibService` (`@gosoft-sbp/email-lib`) ใช้จริงใน 6 โมดูล | ✅ **ตัด** | insert 8 แถวใน `email_template` เดิม · ⚠️ ต้องทำ PoC เคลียร์ว่า engine ส่งเมลเองผ่าน `workflow_route.email_id` หรือไม่ (ดู **DP-5**) ไม่งั้นผู้อนุมัติได้เมลซ้ำ 2 ฉบับ · **ห้ามสับสนกับ `sps_store.wf_email_template` (118 แถว)** ซึ่งเป็นของ WF utility เดิมฝั่ง FCS คนละชุด |
| **ค่ากำหนดกลาง** (`system_configs` + หน้าจอ + 5 endpoint) | `sps_store.mas_param` 93,752 · `common_code` 2,609 · `common_code_type` 376 + `CommonService.getCommonCode()` + `GET /common/common-code` | ✅ **ตัด** (ตามมติ 2026-08-06) | ตั้ง prefix `SBPGI_*` · คัดด้วย `is_config='Y' AND active_flag='Y'` เสมอ · ลงทะเบียน `code_type` ที่ `common_code_type` ก่อน · เขียน getter + cache ของ SBPGI เอง (ของเดิมไม่มี ConfigService กลางและไม่มี cache — อ่านกระจายเป็น raw SQL ต่อโมดูล) |
| **`decisions`** — master ผลพิจารณา 6 แถว | `sps_store.common_code` 2,609 (`code_type` · `seq_no` · `code_value` · `code_name` 1000 · `code_mapping` 100 · `other_value` 50) | ✅ **ตัด** (เงื่อนไขเบา) | seed 6 แถว `code_type='SBPGI_DECISION'` + ลงทะเบียนที่ `common_code_type` · ลบ endpoint `GET /decisions` ใช้ `GET /common/common-code?codeType=SBPGI_DECISION` · ⚠️ `decision_code` ที่จะ map 1:1 กับ `workflow_event.event` ต้อง **ยาวไม่เกิน 10 ตัวอักษร** (`event` เป็น `varchar(10)` ทั้ง 2 schema) |

---

### 🟡 กลุ่ม B — ใช้ของเดิมร่วมได้ แต่ต้องเพิ่ม/ครอบ (11 รายการ)

| สิ่งที่จะสร้าง | ของเดิมที่มี | คำตัดสิน | ต้องทำอะไรถ้าใช้ของเดิม |
|---|---|---|---|
| **`fcs_qssi_score`** | `sps_store.fcs_qssi_score` **23,958,780 แถว** + staging `fcs_tmp_qssi_score` + `POST /performance/import-qssi` ที่ทำงานอยู่ | 🟡 reuse ได้ แต่ migration **หนักกว่าที่ประเมินไว้เดิม** | เพิ่ม 3 คอลัมน์ (`source_file_name`, `source_checksum`, `updated_at`) · **backfill + `SET NOT NULL` บน `store_id`/`category`/`month`/`year` ก่อน** (ทั้ง 4 คอลัมน์ nullable → UNIQUE index กันซ้ำไม่ได้ใน Postgres และ `ON CONFLICT` ไม่ทำงาน) · dedup แล้วสร้าง `UNIQUE INDEX CONCURRENTLY (store_id,category,month,year)` · เพิ่ม index lookup (ตอนนี้มีแค่ `fcs_qssi_score_pkey` บน `id` → Job 6 จะ seq-scan 23.9M ทุกครั้ง) · ดู **DP-4** |
| **`interface_transactions`** | `integration_log` 518 (6 คอลัมน์ · index มีแค่ PK) · `statement_summary` 199 + `sap_statement_expected` (UNIQUE `year,month,report_type,store_id`) · `sps_auth.import_jobs` 317 + `import_errors` 572 (UNIQUE `job_id,row_number`) · `import_job_status` + `temp_control_file` (ว่างทั้งคู่) | 🟡 ต้องสร้างตารางเอง แต่**ลอกแพตเทิร์นได้** | ดู **DP-6** — `statement_summary` มี `sum_record` vs `received_record` + `last_progress_email_at` + `progress_email_flag`/`complete_email_flag` = **แพตเทิร์น expected-vs-received + กันเมลเตือนซ้ำ ตัวเดียวกับที่เรากำลังจะประดิษฐ์ใหม่** (`last_ack_notified_on`) |
| **`consideration_logs`** | `sps_store.workflow_history` 38,010 (`event` varchar(30) · `event_data_json` jsonb · `old/new_state_id` · `create_by_name`) + `workflow_approver` 96,542 (`remark` varchar(2000) · `approve_event` · `approve_date`) | 🟡 ลดรูปเป็นตารางส่วนขยายได้ | ดู **DP-7** — engine ไม่มี `decision_code` แยกคอลัมน์ · ไม่มี `result_category` ที่ index ได้ (หน้ารายงานต้อง filter ประกัน/ไม่ประกันรายได้) · ไม่มีที่ผูกไฟล์แนบต่อการพิจารณา · และเป็นตารางของ library **ห้ามเพิ่มคอลัมน์เอง** |
| **`document_attachments`** | `upload_general` 235 (`doc_id` varchar(20) · `entity_name` · `key` text = S3 key · `job_id`/`audit_log_id` **nullable ทั้งคู่**) + `AwsService` (`POST /statement/upload-file-aws` · `download-file-aws`) | 🟡 metadata ทำเอง · storage ยืม | ดู **DP-8** · **หมายเหตุแก้ความเข้าใจผิด:** ที่เคยบอกว่า "ใช้ `upload_general` แล้วจะพัง FK `job_id`" **ไม่จริง** — FK เป็น nullable ทั้งคู่ เหตุผลจริงที่ต้องมีตารางเองคือขาด `file_size`/`content_type`/`section_code`/`upload_status`/`purge_flag`/`storage_delete_status` (`file_size` ของเดิมอยู่ระดับ job ไม่ใช่ระดับไฟล์) |
| **`impacted_stores`** | `store_sbp` 11,583 (**PK = `order_id`** · `store_id` varchar(10) **nullable ไม่มี index**) · view `v_fr_store_active` · `mas_store` 19,647 · `store` 19,402 · `sevenshop` 15,308 | 🟡 ไม่ต้องสร้าง master ใหม่ แต่ **ทำ view ตรง ๆ ไม่ได้** | ดู **DP-3** — เป็นข้อที่คำแนะนำเดิมพลาดชัดที่สุด |
| **`external_factors`** (master ปัจจัยภายนอก) | `common_code` (`code_name` 1000 · `other_value` **50** · `code_mapping` 100) หรือ `sps_auth.lookup_values` (มี `description` text ไม่จำกัด) | 🟡 ตัดได้ถ้ายอมแก้ตาราง lookup กลาง | ดู **DP-9** — ต้องเพิ่มคอลัมน์ `remark` ที่ `common_code` (remark จริงในหน้าจอยาว 43 ตัวอักษรแล้ว เกิน `other_value(50)` ได้ง่าย) + partial unique index (`WHERE code_type='SBPGI_FACTOR'`) + เขียน CRUD เอง (ระบบเดิมมีแต่ GET) |
| **`competitors`** (master แบรนด์คู่แข่ง 11 แถว) | `common_code` — เจอ `compet` 0 hit ทั้ง 2 schema | 🟡 เหมือนข้างบน | ต้องการ 4 ช่องข้อความ (`code`/`name_th`/`name_en`/`remark`) แต่ `common_code` มีช่องว่างให้ใช้แค่ 3 → ต้องเพิ่ม `remark` (ใช้คอลัมน์เดียวกับ `external_factors`) · **ห้ามใช้กลไก `language` แยกแถว** (1 แถวหน้าจอจะกลายเป็น 2 record) · ดู **DP-9** |
| **`status_email_rules`** | `workflow_route.email_id` + `group_id` (43 แถว) · `fml_email_account` 1,646 (PK `user_id,template_id,email` + `remark`) · `fcs_reminder_log` 695,653 (`reminder_to` · **`reminder_cc`** · `reminder_type` · `reminder_status`) · `email_sent.mail_cc` | 🟡 ตัดได้**บางส่วน** ไม่ใช่ทั้งหมด | ดู **DP-5** — `workflow_route` แขวนได้แค่ **1 เมลต่อ 1 transition** แต่ **reminder รายสัปดาห์ไม่ใช่ transition** จึงไม่มี route ให้แขวนเลย · และที่เคยสรุปว่า "ไม่มีที่เก็บ CC" **ไม่จริง** — มี 3 ที่ |
| **อัปโหลดไฟล์แนบ ≤5MB ขึ้น S3** | `AwsService` (`uploadFile`/`downloadFile`/`moveFile`/`checkFileExist`) · body limit 100mb ที่ `main.ts:33` | 🟡 ยืม storage · ครอบ validate เอง | **ไม่มีการตรวจขนาด/นามสกุล/ไวรัสเลย** ในทั้ง 2 เส้น (pass-through) → SBPGI ต้องครอบ validate เอง (≤5MB · 413/415 ตาม `api.md`) · ⚠️ `AwsService` **hardcode URL bucket dev** `https://srm-sps-data-s3-dev.s3...` ต้องแจ้งทีมเดิมแก้ก่อนขึ้น UAT/PRD · `DeleteObjectCommand` import ไว้แต่ไม่ได้ใช้ → ไม่มี `deleteFile` (กระทบ lifecycle purge) |
| **Export Excel 14 คอลัมน์** | `exceljs ^4.4` ครบทั้ง 3 ชั้น (store-backend 12 ไฟล์ · BFF · FE) · `ResponseHelper.contentDispositionThaiFileName()` · `export-styles.ts` | 🟡 ยืม lib + helper · รายงานยังต้องเขียนเอง | generate ที่ BE ของ SBPGI คืน Buffer + header ชุดเดียวกับ `grade-evaluation-summary.controller.ts` · **ห้ามนับ 14 คอลัมน์เป็นงานที่ตัดออกได้** — ไม่มี Excel helper กลางให้ import |
| **หน้างานรอดำเนินการ + กล่องงานรวมข้ามระบบ** | `GET /api/workflow/pending` (store-backend `backlog.controller.ts`) · BFF `GET /bff/backlog/pending` รวมจาก 5 backend | 🟡 เสียบกล่องรวมได้เกือบฟรี · หน้า `GET /tasks` ยังต้องทำ | `BacklogService.getPending()` เรียกโดย**ไม่ส่ง `versionId`** → คืนงานทุก version → ถ้า SBPGI อยู่ใน store-backend เดียวกัน งานโผล่ทันทีไม่ต้องแก้โค้ด (ดู **DP-10**) · แต่ `PendingTaskItemDto` **ตัด `referenceId` ทิ้ง** และไม่มี filter/paging/bulk → **ห้ามตัดงานทำ `GET /tasks`** |

---

### 🔴 กลุ่ม C — ไม่มีของเดิม ต้องทำเองเต็ม (13 รายการ)

| สิ่งที่จะสร้าง | ของเดิมที่ใกล้ที่สุด | ทำไมใช้แทนไม่ได้ |
|---|---|---|
| **`fgi_impact_processes`** ★ (hub รอบชดเชย) | — | ค้น `impact`/`fgi`/`compensat`/`guarantee`/`income` ในชื่อตารางทั้ง 276 ตาราง = **0 hit** · ค้น `impact_month`/`distance`/`radius`/`latitude`/`longitude` ใน 4,396 คอลัมน์ = **0 hit** · เป็นตัวที่ต้องสร้าง**ก่อน**ทุกตารางในโซน A |
| **`fgi_impact_stores`** (คู่ร้านกระทบ↔เปิดใหม่) | รายงาน `POST /performance/report-open-store` | รายงานนั้นแค่**นับจำนวนร้านเปิดใหม่จาก master** ไม่มีการจับคู่ร้าน 2 ร้านและไม่มีระยะทาง — และ DB เดิม**ไม่มีพิกัด lat/long ให้คำนวณรัศมีเองด้วย** |
| **`fgi_impact_sales_summaries`** | `fcs_monthly_sales.total_day` | `total_day` = จำนวนวันขาย**ต่อร้านต่อเดือน** ไม่ใช่ต่อ**รอบชดเชย** (4 หน้าต่างคร่อมหลายเดือน) · ค้น `growth`/`growth_rate`/`working_day`/`sales_status` = 0 hit |
| **`sales_transactions`** (ยอดขายรายวัน) | `fcs_monthly_sales` 711,384 (index `store_id,year,month`) | **1 แถว = 1 ร้าน/1 เดือน** ย้อนกลับเป็นรายวันไม่ได้ · ค้น `sale_date`/`txn_date`/`daily_sales`/`window_no`/`outlier` ทั้ง 2 schema = 0 hit · เราต้องการ ~60 แถว/รอบ (4 หน้าต่าง × 15 วัน) พร้อม flag outlier รายวัน |
| **`fgi_impact_competitors`** | — | ค้น `compet` = 0 hit · **ALLMAP เป็น SQL Server ภายนอกที่ระบบ SBP ปัจจุบันไม่ได้ต่ออยู่เลย** ต้องทำ integration ใหม่ทั้งเส้น (Jobs 2/3) |
| **`compensation_documents`** | `fml_cooperation_trn` 19,236 | เป็นหนังสือขอความร่วมมือ — ไม่มีคอลัมน์เงิน/งวด/สาขาที่กระทบเลย · **แต่ลอกโครง controller/service ได้** และเชื่อมกลับ SBP Statement ผ่าน `fml_sbp_stmt.document_id` varchar(20) ที่มีรออยู่แล้ว |
| **`document_new_stores`** | — | ไม่มีตารางใดจับคู่ร้าน 2 ร้าน · ไม่มี `distance_km` · ไม่มีที่เก็บ %ชดเชยที่ต้องรวมได้ 100% |
| **`document_competitors`** | — | `grep -ci "competitor"` = **0** ทั้ง 2 ไฟล์ schema |
| **`document_external_factors`** | — | `grep "factor"` เจอ 4 ครั้งเป็น `fillfactor` ของ index ทั้งหมด |
| **`compensation_histories`** | `fr_store_insure` 708 (`store_id` · `year` · `month` · `money_support`) | มีมิติ ร้าน×ปี×เดือน×ยอด ตรงกันจริง **แต่คีย์หลักคือ `order_id` (สัญญา) ไม่ใช่ `doc_no`** · ไม่มี `ref_doc_no` · ไม่มี `submit_account_month` · ไม่มีสถานะ I/C/A/N/S/Z · 708 แถว = ระดับสัญญา ไม่ใช่ระดับรอบชดเชยทั้งระบบ · ⚠️ ดู **DP-11** (ความเสี่ยงตัวเลขเงิน 2 ชุด) |
| **`document_cost_details`** ★ | `fr_store_insure` · `fcs_audit_costs` | ไม่มีตารางใดมีครบทั้ง 3 มิติ (เอกสาร × เดือน × ร้านเปิดใหม่) และไม่มี `cost_target` · ถ้าไม่มีตารางนี้ **จะทวนยอดรายเดือนกับ Statement/SAP ไม่ได้** |
| **`document_running_numbers`** ★ | `fml_cooperation_trn.doc_number` + `cooperation-request.service.ts:1988` | **ไม่มีตารางตัวนับใด ๆ ในทั้ง 276 ตาราง** · ของเดิมออกเลขด้วย `SELECT COUNT(1) + 1 AS seq FROM fml_cooperation_trn WHERE store_id=$1 AND year=$2::text` — **ไม่มี lock** และเป็นคนละรูปแบบ (ผูกรหัสร้าน) · **ห้ามลอก** |
| **รูปแบบแบ่งหน้ากลาง `{page,size,total,items}`** | `src/common/helpers/` มีแค่ common/date/response/string/read-query | ไม่มี pagination helper กลาง · ของเดิมมี **3 รูปแบบขัดกันเอง** (`{page,pageSize,total,totalPage,listData}` / `firstRow`+`lastRow` / `rows.slice()` ใน controller) และมีบั๊ก `Math.ceil(totalRecords)` **โดยไม่หาร `pageSize` อยู่ 6 จุด** (`report-division.controller.ts:340,401` · `evaluate-summary.service.ts:256` · `inform-evaluate.service.ts:463,469` · `cooperation-request.service.ts:936`) |

---

## 3. รายละเอียดรายรายการ (เฉพาะที่ verdict ไม่ใช่ "ไม่มีเลย")

### 3.1 Workflow engine — `sps_store` ไม่ใช่ `sps_auth`

**หลักฐานว่า engine ตัวจริงอยู่ที่ `sps_store`:**
- `workflow.service.ts` ตั้ง DataSource ชื่อ `workflow-connection` ด้วย `schema = WORKFLOW_SCHEMA || DB_SCHEMA` และ `.env-dev` มี `DB_SCHEMA=sps_store`
- `sps_store.workflow_transaction` 19,283 แถว ≈ `fml_cooperation_trn` 19,236 แถว (โมดูล cooperation-request เรียก engine จริง)
- `sps_auth.workflow_*` เป็น DDL ชุดเดียวกันแต่ `transaction` 55 / `route` 41 / `state` 10 — เป็นของ auth-backend คนละชุด
- ชุด `wf_*` (`wf_step_history` 161,813 · `wf_approve` 155,740 · `wf_email_template` 118 — ชนิด `numeric(38,0)` แบบ Oracle เดิม) คือ engine **เก่า** คนละเรื่อง **ห้ามเขียนลง**

**Gap ที่ต้องปิด:**

| # | Gap | หลักฐาน |
|---|---|---|
| 1 | ต้องขอ **version ใหม่ 1 ตัว** ใช้ของเดิม (6/9) ไม่ได้ | LLDD: 1 ระบบ = 1 version |
| 2 | wrapper register entity แค่ **10 ตัว** — ไม่มี `WorkflowPart`/`WorkflowPartDisplay`/`WorkflowEvent` → กลไก READ/WRITE รายส่วนหน้าจอ (`workflow_part_display` 12 ส่วน) **ยังใช้ไม่ได้ทันที** | `src/modules/workflow/workflow.service.ts` |
| 3 | `sps_store.workflow_transaction` **ไม่มี PK และไม่มี index ใด ๆ** (ยืนยันจาก schema dump — ต่างจาก `sps_auth` ที่มี PK `transaction_id`) | ดู **DP-2** |
| 4 | `sps_store.workflow_state` · `workflow_event` · `workflow_part_display` ก็**ไม่มี PK/index** เช่นกัน | schema dump |
| 5 | ชื่อ method ให้ยึด wrapper (`triggerEvent`/`addPreparedApprover`/`getPendingFlow`/`getPermissionEvents`) **ไม่ใช่ชื่อใน LLDD** (`eventWorkflow`/`addPreApprover`) | `workflow.service.ts` |

**ข่าวดีที่แผนเดิมยังไม่ได้ใช้:** wrapper มี **`getPermissionEvents()`** (เรียก `GetPermissionUseCase`) ซึ่งคืน event ที่ผู้ใช้คนนั้นกดได้กับเอกสารนั้น → **ปุ่มผลพิจารณา 6 ตัวเรนเดอร์จากผลลัพธ์นี้ได้เลย ไม่ต้องรอ `workflow_part_display` และไม่ต้อง hardcode role เหมือน prototype** · และ `workflow_transaction.data_json` (jsonb) รับ payload เอกสารให้ `workflow_route.condition_json` ตัดสินเส้นทางตามวงเงินได้ (ตัวอย่างใน LLDD: `{"field":"amount","operator":"<","value":1000}`) → ตรงกับกติกา GM 50,000 / AVP 300,000 พอดี

### 3.2 `fcs_qssi_score` — ตารางเดียวที่ชื่อตรงเป๊ะ

โครงเดิม 7 คอลัมน์: `id` · `store_id` varchar(5) · `category` varchar(2) · `month` varchar(2) · `year` varchar(4) · `score` numeric(38,2) · `create_date` — **business key ครบตามที่ LLDD ต้องการเป๊ะ** (แค่แยก `month`/`year` แทน `score_period CHAR(7)`) และ `category` varchar(2) รองรับหมวด 1,8,9,10,12,16 ได้พอดี

**Gap ที่ต้องปิด (เรียงตามความหนัก):**
1. 🔴 **`store_id`, `category`, `month`, `year` เป็น nullable ทั้ง 4 ตัว** — UNIQUE index บนคอลัมน์ที่มี NULL **ไม่กันซ้ำใน Postgres** (NULL ≠ NULL) และ `ON CONFLICT` จะไม่ทำงานกับแถวที่มี NULL → migration ต้องเพิ่มขั้น **backfill + `SET NOT NULL` บน 23.9 ล้านแถว** ซึ่งล็อกตารางที่ทีมอื่นเขียนอยู่
2. 🔴 ไม่มี UNIQUE(`store_id`,`category`,`month`,`year`) — index มีแค่ `fcs_qssi_score_pkey` บน `id` → ต้อง dedup ก่อน ไม่งั้น index สร้างไม่ผ่าน
3. 🟠 ไม่มี index บน lookup key → Job 6 จะ seq-scan 23.9M ทุกครั้ง
4. 🟡 ขาด `source_file_name`/`source_checksum` (Job 1 ใช้ SHA-256 ตัดสิน SKIP ไฟล์ซ้ำ — staging `fcs_tmp_qssi_score` มี `file_name` แต่ตารางปลายทางไม่มี)
5. 🟡 ขาด `updated_at` · `score numeric(38,2)` vs เป้า `NUMERIC(10,4)` (ทศนิยมหาย 2 ตำแหน่ง — ต้องยืนยันว่า 2 ตำแหน่งพอ)

**หมายเหตุ:** `fcs_qssi_score_bak_20260710` (18,577,924 แถว) = snapshot ก่อน rework 10/07/2026 ไม่มี PK/index **ห้ามอ่าน ห้าม join**

### 3.3 `interface_transactions` — แพตเทิร์นที่มีอยู่แล้วแต่ถูกมองข้าม

ระบบเดิมมี tracking หลายชั้นที่ไม่ครบชั้นเดียวกับเรา แต่ **มี 2 คู่ที่ใกล้กว่าที่เคยรายงาน**:

| ของเดิม | ทำอะไร | ใกล้ตรงไหน |
|---|---|---|
| `sap_statement_expected` (UNIQUE `year,month,report_type,store_id` + `source_file_name`) × `statement_summary` (`sum_record` vs `received_record` · `last_progress_email_at` · `progress_email_flag` · `complete_email_flag` · `complete_date` · partial UNIQUE แยก STA/SAP) | **expected-vs-received ระดับ record + marker กันส่งเมลเตือนซ้ำ** | นี่คือแพตเทิร์นเดียวกับ Job 10 watchdog + คอลัมน์ `last_ack_notified_on` ที่เรากำลังจะประดิษฐ์ใหม่ · **และเป็นเส้น interface เดียวกับที่ Job 6 ส่ง FRBC0001 เข้าไป** · มี entity/migration พร้อมใช้ที่ `src/entitys/statement-summary.entity.ts` และ `src/migrations/202607200001-CreateSapStatementExpected.ts` |
| `sps_auth.import_jobs` 317 × `import_errors` 572 (`row_number` · `error_code` · `error_message` · UNIQUE `job_id,row_number`) | ผลนำเข้า**รายแถว**พร้อมรหัสข้อผิดพลาด กันซ้ำที่ระดับ DB | ไม่ใช่ ACK แต่เป็นโครงระดับ record ที่ใกล้ที่สุดและมีข้อมูลจริงเดินอยู่ — ใช้เป็นต้นแบบ Jobs 1/4/5 ได้ดีกว่าออกแบบใหม่จากศูนย์ |

**ที่ต้องแก้ความเข้าใจ:** ข้อเสนอเดิมบอกว่า "ใช้ `integration_log` แทน `FGI_WS_LOG` (ข้อ F6) ได้เลย ไม่ต้องเพิ่มตาราง" — **ใช้ได้แค่บางส่วน** `integration_log` มี 6 คอลัมน์ (`id`/`module`/`service`/`create_date`/`update_date`/`payload`) และ **index มีแค่ PK** แต่ F6 ต้องการ `DATA_INPUT`/`DATA_OUTPUT` แยกกัน · `ERROR_CODE`/`ERROR_MSG` · เวลา start/end (ไว้วัด timeout ของ QSSI/ALLMAP/IAS) → ต้องยัดทุกอย่างลง `payload` เป็น JSON แล้วทำรายงาน error ไม่ได้ และถ้ายิงทุก call ลงตารางที่ไม่มี index จะโตเร็วมาก (ตอนนี้ 518 แถวเพราะแทบไม่มีใครใช้)

**ห้ามลอก:** `fcs_file_mapping` (22,314 แถว) เป็น polymorphic pointer แบบเดียวกับ `FGI_CONFIRM_RECEIVE_DATA` — **คือบั๊ก E20 ที่เรากำลังจะแก้**

### 3.4 `consideration_logs` — engine เก็บได้แค่ครึ่งเดียว

`workflow_history` เก็บ: `event` varchar(30) · `event_data_json` jsonb · `old/new_state_id` · `old/new_status_id` · `create_by` + `create_by_name` · `create_date` (มี index `idx_ca_wh_latest` บน `transaction_id, version_id, create_date DESC`)
`workflow_approver` เก็บ: `remark` varchar(2000) · `approve_event` · `approve_date` · `approve_seq`

**ขาด:** `decision_code` แยกคอลัมน์ · `result_category` ที่ index ได้ (หน้ารายงาน `k2-report` ต้อง filter ประกัน/ไม่ประกันรายได้) · ไฟล์แนบต่อการพิจารณา · `section_code` ตรง ๆ (ต้องแปลจาก `state_id`)

### 3.5 `document_attachments` และ S3

`upload_general` มีของที่ใช้ได้มากกว่าที่เคยรายงาน: `doc_id` varchar(20) (พอสำหรับ `2026/00123`) · `entity_name` · `key` text (S3 key) · `code_type`/`code_value` · และ **`job_id`/`audit_log_id` เป็น nullable ทั้งคู่** (FK ไม่บังคับ)
**สิ่งที่ขาดจริง:** `file_size` · `content_type` · `section_code` · `upload_status`/`upload_message` · `purge_flag` · `storage_delete_status` (`file_size` ของเดิมอยู่ที่ `general_upload_data_page_job.file_size` varchar(10) = ระดับ job)
**ห้ามลอก:** `fml_bellinee_statement_file` 59,822 / `fml_franchise_statement_file` 5,730 เก็บ **content เป็น bytea ในฐานข้อมูล** — ขัดกับแนวทาง S3

### 3.6 Master 3 ตัว บน `common_code` — ข้อจำกัดที่ต้องรู้ก่อนตัดสินใจ

| ข้อจำกัดจริง | ตัวเลข | ผลกระทบ |
|---|---|---|
| `common_code.code_type` เป็น **`varchar(20)`** ขณะที่ `common_code_type.code_type` เป็น `varchar(50)` | `SBPGI_APPROVE_LIMIT` = 19 ตัว | ชื่อ `code_type` ที่ยาวเกิน 20 จะลงทะเบียนที่ `common_code_type` ได้แต่**เขียน `common_code` ไม่ได้** — ตอนนี้เหลือที่ว่างแค่ 1 ตัวอักษร |
| **ไม่มี unique บน (`code_type`,`code_value`)** | มีแค่ `common_code_idx` btree (`code_type`,`code_value`,`code_name`) | SRS สั่ง "รหัสปัจจัยห้ามซ้ำ" → ต้องเพิ่ม partial unique index เอง |
| ช่องข้อความว่างมีแค่ 3 | `code_name`(1000) · `other_value`(**50**) · `code_mapping`(100) | `competitors` ต้องการ 4 ช่อง (`code`/`name_th`/`name_en`/`remark`) → ไม่พอ |
| `code_mapping` **ถูกใช้เป็นคีย์ join จริงแล้ว** | endpoint `GET /commonCodeWithCond` | ไม่ควรเอามาใส่ข้อความอิสระ |
| ระบบเดิม**ไม่มี POST/PUT/DELETE** ของ `common_code` | module `common` มีแต่ GET | SBPGI ต้องเขียน CRUD ที่เขียนลง lookup กลางที่ทั้งระบบพึ่ง |
| `workflow_event.event` = **`varchar(10)`** ทั้ง 2 schema | | `decision_code` ที่ map 1:1 กับ event ต้องยาวไม่เกิน 10 ตัวอักษร |

**ทางเลือกที่ยังไม่เคยพิจารณา:** `sps_auth.lookup_values` มี `description` text ไม่จำกัด + `parent_id` + `created_by`/`updated_by` — ใช้ได้โดย**ไม่ต้อง ALTER ตาราง lookup กลางของ store-backend**

### 3.7 `impacted_stores` — ทำไม view ตรง ๆ ไม่ได้

| ข้อเท็จจริงจาก schema | ผลกระทบ |
|---|---|
| `store_sbp` **PK = `order_id` (สัญญา)** ไม่ใช่ `store_id` · `store_id` เป็น `varchar(10)` **nullable** และ **ไม่มี index ใด ๆ** (มีแค่ `store_sbp_pkey`) · มี `reference_order_id`/`new_order_id`/`old_order_id`/`transfer_to_store_id` | **1 ร้านมีได้หลายแถวตามรอบสัญญา** → เป็น master keyed by `store_code` ตรง ๆ ไม่ได้ ต้อง dedup เลือกสัญญาปัจจุบันก่อน · join ด้วย `store_id` จะ seq-scan ทุกครั้ง |
| `v_fr_store_active` มี `WHERE (cancel_date IS NULL OR to_char(cancel_date,'YYYYMM') = เดือนที่แล้ว)` | **ร้านที่ยกเลิกเกิน 1 เดือนหายจาก view** แต่เอกสารชดเชยย้อนหลังยังต้องอ้างร้านเหล่านั้น → เอกสารเก่ากลายเป็น "ร้านไม่พบ" |
| รูปแบบรหัสร้านไม่ตรงกัน — `v_fr_store_active` ต้อง `lpad(store_id,5,'0')` · `store.store_id`/`mas_store.branch_id` varchar(10) · `fs_sevenshop.branch_id` varchar(7) | ต้อง normalize เป็น 5 หลักทุกจุดที่ join ข้ามโซน · **ห้าม `parseInt(store_code)`** (เลขศูนย์นำหน้าหาย) |
| ชื่อ `transfer_sbp_date` ไม่มีตรงตัว — มีผู้สมัคร 2 ตัว: `store_sbp.start_sbp_date` และ `store_sbp.transfer_date` | ถ้าเลือกผิด เงื่อนไข 1/10/2014 จะพาเอกสารเข้าสาย approve ผิด |

**สิ่งที่ระบบเดิมมีครบและใช้ได้จริง:** `sevenshop` มีบล็อกผู้อนุมัติ 18 คอลัมน์ (`dv_name`/`dv_email`/`dv_employee_id` · `gm_*` · `avp_*`) + index บน `dv_email` · และ **คอลัมน์ 52–53 `start_renovate_date`/`end_renovate_date`** ซึ่ง**ตอบข้อ F5 ของ `database.md` ได้ทันทีโดยไม่ต้องเพิ่มคอลัมน์ใด ๆ** (`database.md` บรรทัด 162 เขียนว่า "เพิ่มคอลัมน์ renovate ใน `stores`" — ไม่ต้องแล้ว) · รวมถึง `open_date`/`close_date`/`sales_area`/`store_type_code`/`ptt_code` ที่ pipeline ใช้หาร้านเปิดใหม่

**สำหรับ resolve ผู้อนุมัติต่อร้าน** มีของที่เหมาะกว่า `sevenshop` (ที่เก็บชื่อแบบ denormalize): `sps_auth.store_organize` **PK (`store_id`,`employee_id`)** 116,790 แถว และ `sps_store.store_organize` 79,722 แถว (`store_id` + `employee_id` + `group_id` + `email` + `active_flag`) — รองรับหลายคนต่อร้าน/หลายบทบาท เหมาะกับ `addPreparedApprover` มากกว่า
**สำหรับกติกา "ผู้รักษาการเป็นผู้อนุมัติไม่ได้" (SDD GI):** ไม่ต้อง infer จาก `position_level` — **มีธงตรง ๆ 2 ที่** คือ `mas_sbp_ad.position_acting` (102,125 แถว · มี `store_id`/`store_type`/`emp_id`/`active_date`/`inactive_date` · index บน `store_id`) และ `business_user.cpall_acting_supervisor_lvl`

### 3.8 อีเมลและ `status_email_rules`

`workflow_route` (43 แถว ใน `sps_store` · 41 ใน `sps_auth`) มี `email_id` **เดียว** + `group_id` **เดียว** ต่อ route → แขวนได้แค่เมล 1 ฉบับต่อ 1 transition ส่งหาผู้อนุมัติถัดไป

**สิ่งที่ผูกกับ route ไม่ได้:**
- **reminder รายสัปดาห์ — ไม่ใช่ transition** จึงไม่มี route ให้แขวนเลย
- เมลแจ้งผู้เปิดเรื่อง / เมลแจ้งจบ flow ที่ไม่ตรงกับ 1 transition เดียว

**ที่เก็บ CC มีอยู่แล้ว 3 ที่** (ตรงข้ามกับที่เคยสรุปว่า "ไม่มีที่ไหนเก็บ CC"): `email_sent.mail_cc` (text) · `fcs_reminder_log.reminder_cc` varchar(4000) (695,653 แถว) · และ `fml_email_account` (PK `user_id`,`template_id`,`email` · 1,646 แถว · มี `remark`) = **ทะเบียนผู้รับต่อ template** ที่ระบบเดิมใช้อยู่จริง

**ประเด็นที่ยังไม่ปิด:** LLDD §7 ข้อ 5 เขียนเองว่า *"ไม่มีรายละเอียดการ config email — `email_id` ชี้ไป table email…… (ยังไม่ระบุชื่อตาราง)"* และ `cooperation-request.module.ts` **ไม่ import MailModule/EmailLib เลย** ทั้งที่ใช้ engine เต็มรูปแบบ → น่าจะแปลว่า engine ส่งเมลเอง **แต่ยังไม่ได้พิสูจน์**

### 3.9 Export Excel · กล่องงานรวม · helper ที่มีอยู่แล้ว

- **`ResponseHelper.contentDispositionThaiFileName()`** ใน `src/common/helpers/response.helper.ts` — ทำ `filename` + `filename*=UTF-8''` ให้แล้ว (ไม่ต้องลอกจาก `grade-evaluation-summary.controller.ts`)
- **`DateHelper.convertADToBE()` · `getBEShortYear()` · `formatThaiBEDate()` · `formatDateBE()`** ใน `date.helper.ts` — ใช้กับเลขเอกสาร `YYYY/xxxxx` (พ.ศ.) ได้ทันที
- **`readQuery()`** ใน `read-query.helper.ts` วิ่ง replica — ⚠️ ระวัง replication lag เมื่ออ่านทันทีหลังสร้างเอกสาร
- **`@nestjs/schedule ^6.0.1`** เป็น dependency ของ store-backend อยู่แล้ว (ยังไม่ register ใน `app.module`) + `rabbitmq.service.ts` (`publishMessage`, topic exchange, persistent) → **batch 11 entry point ไม่ต้องเพิ่ม infra ใหม่** หลังตัด `job_configs`/`job_run_histories` ไปแล้ว
- **`import_type` (23 แถว: `file_header` · `file_type` · `endpoint_url` · `s3_backup_path` · `s3_template_path` · `payload_json` · `is_background`) + `import_group` + `import_type_permission` (UNIQUE `import_type_id,group_id`) + `master_template_columns` (`template` · `download_template_report` · `import_path` · `dynamic_config`) + `view_column` (816 แถว: `col_name`/`dbcol_name` · `color_code` · `hf_col_start/end` · `body_json_attribute`)** → ระบบเดิมเก็บ **ชนิดไฟล์นำเข้า + ผังคอลัมน์ + template ดาวน์โหลด เป็น data อยู่แล้ว** ตอบข้อ P1 `TaskMaster`/`TaskList` ของ `database.md` ได้โดยไม่ต้องยัดลง config file และใช้เก็บผัง 14 คอลัมน์ของรายงานได้
- **กล่องงานรวม:** `BacklogService.getPending()` เรียก `getPendingFlow({userData})` **โดยไม่ส่ง `versionId`** → คืนงานทุก version · ฝั่ง BFF `BACKLOG_SOURCES` เป็นอาร์เรย์ตายตัว 5 ตัว (Auth/Store/StorePartner/Contract/Investor) prefix `transactionId` แล้ว `Promise.allSettled` · ⚠️ helper `daysSinceDate()` คำนวณด้วย `Date.UTC(ty, tm, td)` **โดยไม่ลบ 1 จากเดือน** (คลาดเคลื่อนที่รอยต่อเดือน) — ควรแจ้งทีม BFF

---

## 4. ข้อที่ต้องตัดสินใจ (Decision Points) — 12 ข้อ

> ทุกข้อในหัวข้อนี้มีทางเลือกจริง 2 ทาง · ข้อเสนอแนะเป็นความเห็นเชิงเทคนิค **การตัดสินใจขั้นสุดท้ายเป็นของเจ้าของโครงการ**

---

### DP-1 · `reference_id` ของ workflow = `doc_no` หรือ surrogate id? 🔴 สำคัญที่สุด

**ปัญหา:** `database.md` Cross-System Key ข้อ 4 กำหนดให้ `referenceId = doc_no` โดยอ้างว่าเป็นแพตเทิร์นของ `cooperation-request` — **แต่แพตเทิร์นนั้นไม่มีอยู่จริง**

**หลักฐาน:** `cooperation-request.service.ts` ส่ง `referenceId: trnId` (PK ตัวเลข) ที่บรรทัด **1724, 1749, 1810, 1910 (`initializeWorkflow`), 2005, 2089, 2194** ทุกจุด · `doc_number` ถูก generate **ทีหลัง ตอน `sendApprove`** (~บรรทัด 1978–2000) · `inform-evaluate.service.ts:741` ก็ใช้ `String(evaluateId)` → **ทั้งสองโมดูลจงใจใช้ surrogate id เพราะเลขเอกสารยังไม่เกิดตอน initialize**

| | ทางเลือก A — `referenceId = doc_no` (ตามแผนปัจจุบัน) | ทางเลือก B — `referenceId = surrogate id` (ตามระบบเดิมจริง) |
|---|---|---|
| **ข้อดี** | join กับ `compensation_documents` ตรง ๆ อ่านง่าย · debug ง่าย (เห็นเลขเอกสารใน engine) · `PendingTaskItemDto` ตัด `referenceId` ทิ้งอยู่แล้วจึงไม่กระทบกล่องรวม | ตรงกับที่ระบบเดิมทำจริงทั้ง 2 โมดูล · ออกเลขเอกสารเมื่อไรก็ได้ (ไม่บังคับตอนสร้าง) · แก้/ออกเลขใหม่ภายหลังได้ · ลดแรงกดดันบนกลไก running number |
| **ข้อเสีย** | **บังคับให้ต้องออกเลขตั้งแต่ตอน initialize** ซึ่งเป็นจุดที่ Job 8b (batch) และผู้ใช้ทำพร้อมกัน · **แก้เลขเอกสารภายหลังไม่ได้เลย** เพราะเป็นคีย์ที่ engine ใช้ · เสี่ยงชนกับกลไก reopening ของ SDD GI | ต้อง join 1 ชั้นทุกครั้งที่แปลง transaction ↔ เอกสาร · ต้องเก็บ mapping `transaction_id ↔ doc_no` เอง · debug ยากขึ้นเล็กน้อย |
| **ต้นทุน** | 0 (แต่รับความเสี่ยง) | +0.5–1 วัน (คอลัมน์ + query mapping) |

**ข้อเสนอแนะ:** ไปทาง **B** — ให้ `compensation_documents` มี surrogate PK แล้วส่ง `referenceId = surrogate` ส่วน `doc_no` เป็นคอลัมน์ธรรมดา (index unique) เพราะเป็นทางที่ระบบเดิมพิสูจน์แล้ว 19,283 ครั้ง และปลดล็อกทางเลือกเรื่องจังหวะการออกเลข
**คำถามที่ต้องตอบเพื่อเลือก:** เลขเอกสารต้องเกิดพร้อมกับการสร้างเอกสารเสมอหรือไม่ (ธุรกิจ) และมีเคสที่ต้องออกเลขใหม่/แก้เลขหรือไม่

---

### DP-2 · `workflow_transaction` ไม่มี PK/index — ขอ sign-off เพิ่ม หรือยอมรับสภาพ? 🔴

**ข้อเท็จจริง:** `sps_store.workflow_transaction` มี **19,283 แถว** แต่ schema dump แสดงว่า **ไม่มี PK และไม่มี index ใด ๆ เลย** (ต่างจาก `sps_auth.workflow_transaction` ที่มี PK `transaction_id`) · `workflow_state`/`workflow_event`/`workflow_part_display` ใน `sps_store` ก็ไม่มี PK เช่นกัน

**ผล:** ทุกครั้งที่เปิดเอกสารหรือกด action ต้อง **seq-scan 19,283 แถว** เพื่อหา `reference_id` · และไม่มีอะไรกัน `initialize` ซ้ำแม้แต่ระดับ application

| | ทางเลือก A — ขอ sign-off จากทีม `@srm/glb-workflow` เพิ่ม PK + UNIQUE(`version_id`,`reference_id`) + index | ทางเลือก B — ไม่แตะตารางของ library · กันซ้ำ + index ที่ฝั่ง SBPGI |
|---|---|---|
| **ข้อดี** | แก้ที่ต้นเหตุ · ทุกโมดูลที่ใช้ engine ได้ประโยชน์ร่วม (cooperation ก็เร็วขึ้น) · idempotent ที่ระดับ DB | ไม่ต้องรอใคร · ไม่เสี่ยงกระทบ cooperation-request ที่ใช้งานจริง 19,236 เอกสาร |
| **ข้อเสีย** | ต้องรอ sign-off จากทีมอื่น (อาจเป็น blocker ตาราง critical path) · ถ้ามีข้อมูลซ้ำอยู่แล้ว UNIQUE สร้างไม่ผ่านต้อง dedup ก่อน · ต้องทดสอบ regression ของ cooperation | ยังคง seq-scan ทุกครั้ง (จะแย่ลงเมื่อ SBPGI เพิ่มอีก ~หมื่นแถว/ปี) · กันซ้ำได้แค่ระดับ application (race ยังเกิดได้) · เก็บ mapping `doc ↔ transaction_id` เองเพิ่ม 1 ตาราง/คอลัมน์ |
| **ต้นทุน** | 1–2 วัน + เวลารอ sign-off | 1 วัน |

**ข้อเสนอแนะ:** ทำ **ทั้งสอง** — เดินหน้าด้วย B ทันทีเพื่อไม่ให้เป็น blocker แล้ว**ยื่นเรื่อง A ขนานไป** เพราะ index บนตารางที่ทุกโมดูลใช้เป็นประโยชน์ร่วมที่มีต้นทุนต่ำ
**คำถามที่ต้องตอบ:** ใครเป็นเจ้าของ `@srm/glb-workflow` และมีช่องทาง/รอบการขอแก้ schema หรือไม่

---

### DP-3 · `impacted_stores` เป็น view จากระบบเดิม หรือตาราง snapshot ของ SBPGI? 🔴

| | ทางเลือก A — view `v_sbpgi_sp_store` (ไม่มีตาราง) | ทางเลือก B — ตาราง `impacted_stores` ของ SBPGI (sync จาก master) |
|---|---|---|
| **ข้อดี** | ไม่ต้อง ETL/sync 11,583 แถว · ข้อมูลตรงกับ master เสมอ · ตัดตารางได้ 1 ตัว | เอกสารย้อนหลังหาร้านเจอเสมอ (แม้ร้านยกเลิกไปแล้ว) · คุม `store_code` 5 หลักได้เอง · join เร็ว (มี index ของเราเอง) · เก็บ `transfer_sbp_date` ที่ตกลงกันแล้วได้ชัด |
| **ข้อเสีย** | 🔴 `v_fr_store_active` **ตัดร้านที่ยกเลิกเกิน 1 เดือนออก** → เอกสารชดเชยย้อนหลังกลายเป็น "ร้านไม่พบ" · 🔴 `store_sbp` คีย์ด้วย `order_id` (สัญญา) → 1 ร้านหลายแถว ต้อง dedup ทุก query · 🔴 `store_id` nullable + **ไม่มี index** → seq-scan 11,583 แถวทุก join · ต้อง `lpad(...,5,'0')` ทุกจุด | ต้อง sync + มีโอกาสข้อมูลค้างไม่ตรง master · เพิ่ม 1 ตาราง + 1 job |
| **ต้นทุน** | 1–2 วัน (เขียน view + จูน) แต่มีหนี้ทางเทคนิค | 2–3 วัน (ตาราง + sync job) |

**ทางเลือกที่ 3 (ผสม):** ตาราง snapshot **เฉพาะร้านที่เคยเข้ารอบชดเชย** (ไม่ใช่ทั้ง 11,583 แถว) เติมทีละแถวตอน pipeline สร้าง `fgi_impact_processes` → ได้ความคงทนของ B โดยไม่ต้อง sync ทั้ง master

**ข้อเสนอแนะ:** **ทางเลือกที่ 3** — ราคาเท่า A แต่ไม่มีปัญหาเอกสารย้อนหลัง
**คำถามที่ต้องตอบ:** เอกสารชดเชยย้อนหลังต้องเปิดดูได้นานแค่ไหนหลังร้านยกเลิกสัญญา (ธุรกิจ) — ถ้าคำตอบคือ "ไม่ต้องเปิดดูเลย" ทางเลือก A ก็ใช้ได้ · **และ `transfer_sbp_date` คือ `start_sbp_date` หรือ `transfer_date`?** (ต้อง confirm กับเจ้าของระบบก่อนลงมือทุกทาง)

---

### DP-4 · `fcs_qssi_score` — reuse ตารางเดิม 23.9M แถว หรือสร้างตารางของ SBPGI? 🟠

| | ทางเลือก A — reuse (ตามมติเดิมใน `database.md` บรรทัด 56) | ทางเลือก B — สร้าง `sbpgi_qssi_scores` ของเราเอง |
|---|---|---|
| **ข้อดี** | ไม่ต้อง migrate 23.9M แถว · ได้ import pipeline (`POST /performance/import-qssi` + staging) ฟรี · ไม่มีข้อมูล QSSI 2 ชุด | ไม่แตะตารางที่ทีมอื่นเขียนอยู่ · ออกแบบคอลัมน์/index/constraint ได้อิสระ · ไม่ต้อง backfill + `SET NOT NULL` บน 23.9M แถว |
| **ข้อเสีย** | 🔴 ต้อง backfill + `SET NOT NULL` บน 4 คอลัมน์ × 23.9M แถว (**ล็อกตารางที่ `performance.service.ts` เขียนอยู่**) · ต้อง dedup ก่อนสร้าง UNIQUE · ถ้าเพิ่ม UNIQUE แล้ว `import-qssi` เดิมอาจพัง → **ต้องคุยกับเจ้าของ `performance.service.ts` ก่อน** | ข้อมูล QSSI 2 ชุดในระบบเดียว (เสี่ยงไม่ตรงกัน) · ต้องเขียน import เอง · เสีย 23.9M แถวที่มีอยู่แล้ว (หรือต้อง copy) |
| **ต้นทุน** | 3–5 วัน (migration + dedup + ทดสอบ regression) | 4–6 วัน (ตาราง + import + backfill ข้อมูลเก่าถ้าต้องการ) |

**ข้อเสนอแนะ:** ก่อนตัดสินใจ ให้รัน **query เดียว** ก่อน: นับแถวที่ `store_id IS NULL OR category IS NULL OR month IS NULL OR year IS NULL` และนับ duplicate ของ business key — ถ้าตัวเลขทั้งสองเป็น 0 หรือใกล้ 0 ให้ไป A · ถ้าเยอะ ให้ไป B แล้วค่อยตัดสินใจว่าจะรวมทีหลังหรือไม่
**คำถามที่ต้องตอบ:** เจ้าของ `performance.service.ts` ยอมให้เพิ่ม constraint บนตารางนี้หรือไม่

---

### DP-5 · อีเมล — ผูกที่ `workflow_route.email_id` หรือ SBPGI ส่งเอง? 🟠

**ประเด็นที่ยังไม่ปิด:** ไม่มีใครพิสูจน์ว่า engine ส่งเมลเองหรือไม่ · `cooperation-request.module.ts` ไม่ import MailModule/EmailLib แต่ใช้ engine เต็มรูปแบบ · LLDD §7 ข้อ 5 ยอมรับเองว่ายังไม่ระบุตาราง template ที่ `email_id` ชี้ไป

| | ทางเลือก A — ผูก `email_id` + `group_id` ที่ `workflow_route` (ไม่เขียนโค้ดส่งเมล) | ทางเลือก B — ปล่อย `email_id` ว่าง · SBPGI เรียก `MailService.sendMail()` เองหลัง action สำเร็จ |
|---|---|---|
| **ข้อดี** | flow กับกฎอีเมลอยู่ที่เดียว แก้ที่เดียว ไม่มีทางไม่ตรงกัน · ไม่ต้องเขียนโค้ดเลย | ควบคุมได้เต็ม (ตัวแปร · ผู้รับ · CC · เงื่อนไข) · รู้แน่ว่าเมลออกเมื่อไร · เดียวกันทั้ง transition และ non-transition |
| **ข้อเสีย** | 🔴 **แขวนได้แค่ 1 เมลต่อ 1 transition** → เมลแจ้งผู้เปิดเรื่อง/แจ้งจบ flow อาจไม่พอ · 🔴 **reminder รายสัปดาห์แขวนไม่ได้เลย** (ไม่ใช่ transition) · ยังไม่ยืนยันว่า engine ส่งจริง — ถ้าไม่ส่ง = ไม่มีอีเมลทั้ง flow · ไม่มีที่เก็บ CC ที่ route | ถ้า engine ส่งเมลเองด้วย → **ผู้อนุมัติได้เมลซ้ำ 2 ฉบับต่อ 1 การเปลี่ยนสถานะ** · ต้องเขียน mapping สถานะ → template เอง |
| **ต้นทุน** | 0.5 วัน (config) | 2–3 วัน |

**ทางเลือกที่ 3 (ที่ผมแนะนำ):** **ผสม** — ใช้ A สำหรับเมล transition (EM ที่ตรงกับ 1 route) และใช้ B + ทะเบียนผู้รับแบบ `fml_email_account` สำหรับ **reminder รายสัปดาห์และเมลที่ไม่ผูกกับ route** → ยังตัด `status_email_rules` เป็นตารางเต็มออกได้ แต่ยอมรับว่าต้องมีที่เก็บกฎผู้รับของเมลนอก route

**ก่อนตัดสินใจต้องทำ PoC 1 route:** trigger event แล้วดูว่ามีแถวใหม่ใน `email_sent` (5,214 แถว) หรือไม่ — **ใช้เวลาไม่เกินครึ่งวันและเป็นตัวชี้ขาดของทั้ง DP นี้**
**คำถามที่ต้องตอบ:** ทีม `@srm/glb-workflow` ยืนยันว่า `email_id` ส่งเมลเองหรือไม่ และอ่าน template จากตารางไหน

---

### DP-6 · `interface_transactions` — ออกแบบใหม่ หรือลอกแพตเทิร์น `statement_summary`? 🟡

| | ทางเลือก A — ตารางใหม่ ~24 คอลัมน์ ตามที่ออกแบบไว้ | ทางเลือก B — ลอกโครง `sap_statement_expected` × `statement_summary` |
|---|---|---|
| **ข้อดี** | ครบตามความต้องการทุกข้อ (direction · status 6 ค่า · typed FK · retry · purge/legal hold) · เป็นของเราคนเดียว | เป็นแพตเทิร์นที่ทีมนี้ใช้จริงและ maintain อยู่ (expected-vs-received + `last_progress_email_at` = marker กันเมลซ้ำ ตรงกับ `last_ack_notified_on` ของเรา) · มี entity/migration ให้ลอก · **เป็นเส้น interface เดียวกับที่ Job 6 ส่ง FRBC0001 อยู่แล้ว** |
| **ข้อเสีย** | ประดิษฐ์ใหม่ทั้งที่ทีมมีแพตเทิร์นเดียวกันอยู่แล้ว · โค้ด watchdog เขียนจากศูนย์ | ต้องปรับให้รองรับ IN/OUT/INTERNAL และ typed FK ซึ่งของเดิมไม่มี · อาจจบด้วย 2 ตาราง (expected + summary) แทน 1 |
| **ต้นทุน** | 3–4 วัน | 2–3 วัน |

**ข้อเสนอแนะ:** ทาง **B** โดยยังเป็นตารางของ SBPGI เอง (ไม่ใช้ตารางของเขา) แค่**ลอกโครงคอลัมน์และ index** — ได้ทั้งความเร็วและความคุ้นเคยของทีม
**ไม่ว่าเลือกทางไหน:** ตัด `run_id REFERENCES job_run_histories` ออกจาก DDL (ตารางนั้นถูกลบจาก target schema 2026-08-06) · ใช้ `integration_log` เก็บ payload ราย call ได้ แต่**อย่านับว่าครอบ F6 ครบ** (ไม่มี error code/เวลา start-end/index)

---

### DP-7 · `consideration_logs` — ตาราง timeline เต็ม หรือตารางส่วนขยายบน engine? 🟡

| | ทางเลือก A — ตารางเต็ม (เก็บ timeline เองทั้งหมด) | ทางเลือก B — ตารางส่วนขยาย (เก็บเฉพาะที่ engine ไม่มี) |
|---|---|---|
| **ข้อดี** | อ่านง่าย query เดียวจบ · ไม่ผูกกับ engine · รายงานเร็ว (มี index ของเราเอง) | ไม่มีข้อมูลซ้ำ 2 ที่ · ตัดคอลัมน์ซ้ำได้ ~6 ตัว · ไม่ต้องเขียน timeline เอง · ใช้ index `idx_ca_wh_latest` ของ engine ได้ |
| **ข้อเสีย** | เวลา/ผู้ทำ/สถานะซ้ำกับ `workflow_history` 38,010 แถว → เสี่ยงไม่ตรงกัน | ต้อง join ข้าม DataSource (engine ใช้ `workflow-connection` แยก) ทุกครั้งที่แสดงประวัติ · รายงานที่ filter `result_category` ต้อง join 2 ตาราง |
| **ต้นทุน** | 2 วัน | 1.5 วัน + ความซับซ้อนตอน query |

**ข้อเสนอแนะ:** ทาง **B** พร้อม map `route.event` → `decision_code` แบบ 1:1 ตั้งแต่ตอน register workflow version (จำได้ว่า `workflow_event.event` = `varchar(10)`) แล้วดึงเวลา/ผู้ทำผ่าน `GetHistoryUseCase`
**คำถามที่ต้องตอบ:** หน้ารายงานต้อง filter/นับตาม `result_category` บ่อยแค่ไหน — ถ้าเป็น query หลักของรายงานรายเดือนที่ต้องเร็ว ทาง A คุ้มกว่า

---

### DP-8 · `document_attachments` — ตารางของเราเอง หรือต่อยอด `upload_general`? 🟡

| | ทางเลือก A — ตาราง `document_attachments` ของ SBPGI (metadata อย่างเดียว) | ทางเลือก B — ต่อยอด `upload_general` (เพิ่มคอลัมน์) |
|---|---|---|
| **ข้อดี** | คุมคอลัมน์/lifecycle เองเต็ม · ไม่กระทบฟีเจอร์ general upload · ใช้ `AwsService` ของเดิมเป็นชั้น storage ได้อยู่ดี | ไม่เพิ่มตาราง · `doc_id`(20) / `entity_name` / `key`(S3 key) มีอยู่แล้ว และ `job_id`/`audit_log_id` เป็น nullable (ไม่บังคับ) |
| **ข้อเสีย** | +1 ตาราง | ต้องเพิ่ม 6 คอลัมน์ (`file_size`, `content_type`, `section_code`, `upload_status`, `purge_flag`, `storage_delete_status`) ลงตารางของฟีเจอร์อื่น · ข้อมูลไฟล์แนบเอกสารปนกับไฟล์งาน general upload (235 แถว) · ต้องขอ sign-off |
| **ต้นทุน** | 1 วัน | 1 วัน + เวลารอ sign-off + ความเสี่ยง |

**ข้อเสนอแนะ:** ทาง **A** — ต้นทุนเท่ากันแต่ไม่ต้องขอใคร · **ไม่ว่าทางไหนก็ใช้ `AwsService` เป็นชั้น storage** (ห้ามเขียน S3 layer เอง) และต้องครอบ validate ≤5MB เพราะของเดิมเป็น pass-through ที่รับไฟล์ได้ถึง 100MB
**เรื่องที่ต้องแจ้งทีมเดิมไม่ว่าเลือกทางไหน:** `AwsService` hardcode URL bucket dev และไม่มี `deleteFile` (กระทบ lifecycle purge ของเรา)

---

### DP-9 · master 3 ตัว — ยัดลง `common_code` หรือตารางเล็กของ SBPGI? 🟡

(`decisions` 6 แถว · `external_factors` ~สิบแถว · `competitors` 11 แถว — รวมกันไม่ถึง 30 แถว)

| | ทางเลือก A — `common_code` (`code_type = SBPGI_*`) | ทางเลือก B — 3 ตารางเล็กของ SBPGI เอง |
|---|---|---|
| **ข้อดี** | ตัดได้ 3 ตาราง + งาน migration · `decisions` เข้าได้พอดีโดยไม่ต้องแก้อะไร · หน้าจอ admin เดิมดูแลได้ | ไม่แตะ lookup กลางที่ทุกโมดูลอ่าน · ใส่ `remark` ยาวเท่าไรก็ได้ · มี unique constraint ของตัวเอง · CRUD เขียนได้อิสระ |
| **ข้อเสีย** | 🔴 `external_factors`/`competitors` **ต้องเพิ่มคอลัมน์ `remark` ที่ `common_code`** (ตารางที่ทั้งระบบพึ่ง 2,609 แถว) เพราะ `other_value` จำกัด 50 ตัวอักษร · ต้องเพิ่ม partial unique index เอง (ของเดิมไม่มี) · ต้องเขียน CRUD ที่**เขียนลง lookup กลาง** (ของเดิมมีแต่ GET) · ถ้า `seq_no`/`active_flag` พลาดอาจกระทบ dropdown ของโมดูลอื่น | +3 ตารางเล็ก (แต่รวมกันไม่ถึง 30 แถว) · ต้องทำ endpoint เอง |
| **ต้นทุน** | 1–2 วัน + เวลารอ sign-off | 2–3 วัน |

**ทางเลือกที่ 3:** ใช้ `sps_auth.lookup_values` (มี `description` text ไม่จำกัด + `parent_id` + `created_by`/`updated_by`) → ได้ประโยชน์ของ A โดย**ไม่ต้อง ALTER ตารางของ store-backend**

**ข้อเสนอแนะ:** **แยกตัดสินคนละแบบ** — `decisions` ไป A (เข้าพอดี ไม่ต้องแก้อะไร ตัดได้เลย) · `external_factors` + `competitors` ไป B หรือทางเลือกที่ 3 (มีหน้าจอ CRUD ของตัวเอง การเขียนลง lookup กลางไม่คุ้มความเสี่ยง)
**คำถามที่ต้องตอบ:** ทีม store-backend ยอมให้ระบบอื่นเขียน `common_code` หรือไม่

---

### DP-10 · SBPGI อยู่ใน store-backend เดิม หรือแยกเป็น backend ใหม่? 🟠

**ข้อนี้ยังไม่เคยตัดสินใจอย่างเป็นทางการ แต่มีผลต่ออีกหลายข้อ**

| | ทางเลือก A — โมดูลใน `srm-sps-spsap-store-backend` | ทางเลือก B — backend ใหม่ `srm-sps-spsap-sbpgi-backend` |
|---|---|---|
| **ข้อดี** | งานโผล่ในกล่องรวมข้ามระบบ **ทันทีโดยไม่ต้องแก้โค้ด** (`getPendingFlow` ไม่กรอง version) · ใช้ helper/entity/DataSource เดิมทั้งชุด (`readQuery`, `DateHelper`, `ResponseHelper`, `AwsService`, `MailService`, `WorkflowService`) · อยู่ schema `sps_store` เดียวกับ engine | ขอบเขต deploy/release แยก ไม่กระทบระบบเดิม · ตาราง 21 ตัวไม่ปนกับ 198 ตาราง · ทีมเป็นเจ้าของ codebase เต็ม |
| **ข้อเสีย** | เพิ่ม 21 ตารางเข้า schema ที่มี 198 ตารางแล้ว · deploy ผูกกับ release cycle ของ store-backend · โค้ดปนกับ 25 controller เดิม | ต้อง copy helper ทั้งชุดหรือทำ shared lib · ต้องเพิ่ม client + env + แถวใน `BACKLOG_SOURCES` ของ BFF (5 ตัวปัจจุบันเป็นอาร์เรย์ตายตัว) · ต้องตั้ง DataSource ข้าม schema ไปหา engine |
| **ต้นทุน** | ต่ำ | +3–5 วัน setup + งานเชื่อมต่อเนื่อง |

**ข้อเสนอแนะ:** ข้อนี้เป็นการตัดสินใจเชิงองค์กร (ใครดูแล · release cycle · ทีม) มากกว่าเชิงเทคนิค — ผมไม่ฟันธง แต่ขอบันทึกไว้ว่า **ทางเลือก A ทำให้ตัวเลขประหยัด 20–35 วันในหัวข้อ 1 เป็นจริงได้ง่ายกว่ามาก**
**คำถามที่ต้องตอบ:** ทีมไหนดูแล SBPGI หลัง go-live และยอมรับ release cycle ร่วมกับ store-backend ได้หรือไม่

---

### DP-11 · ตัวเลข "เงินประกันรายได้" — SBPGI เป็นต้นทาง หรือ `fr_store_insure` ยังคีย์มือ? 🔴 (ธุรกิจล้วน)

**ข้อเท็จจริง:** `sps_store.fr_store_insure` (708 แถว) เก็บ `store_id` · `year` · `month` · `money_support(10,2)` · `split(10,2)` ต่อ `order_id` (สัญญา) — เป็น "เงินช่วยเหลือ/ประกันรายได้ต่อสัญญา" ที่โมดูล inquiry เขียนอยู่แล้ว **มิติซ้ำกับ `compensation_histories` ของเราบางส่วน**

| | ทางเลือก A — SBPGI เป็นต้นทางเดียว (feed เข้า `fr_store_insure`) | ทางเลือก B — แยกกันเด็ดขาด (SBPGI ไม่ยุ่งกับ `fr_store_insure`) |
|---|---|---|
| **ข้อดี** | ตัวเลขเงินชุดเดียวทั้งระบบ · หน้า inquiry เดิมเห็นยอดที่ผ่าน workflow แล้ว | ไม่กระทบโมดูลเดิมเลย · ขอบเขตชัด |
| **ข้อเสีย** | ต้องเขียนเข้าตารางของโมดูลอื่น · grain ต่างกัน (สัญญา vs รอบชดเชย) ต้อง map · ต้องขอ sign-off | 🔴 **ระบบจะมีตัวเลข "ประกันรายได้" 2 ที่ที่อาจไม่ตรงกัน** — เป็นความเสี่ยงที่แพงที่สุดในเอกสารนี้เพราะเป็นตัวเลขเงินที่ส่งต่อบัญชี/SAP |

**ข้อเสนอแนะ:** **ผมไม่ฟันธง — เป็นการตัดสินใจเชิงธุรกิจ/บัญชีล้วน** แต่ขอเน้นว่าต้องตัดสินใจ **ก่อน** เขียน `compensation_histories` ไม่ใช่หลัง
**คำถามที่ต้องตอบ:** `fr_store_insure` วันนี้ใครกรอก · กรอกจากอะไร · และตัวเลขนั้นคือตัวเดียวกับเงินชดเชยที่ผ่าน workflow ของเราหรือไม่

---

### DP-12 · audit ของ master — เอากลับมาโดยใช้ของเดิม หรือไม่มีเลยตามมติ 2026-08-07? 🟡

**เหตุผลที่บันทึกไว้ตอนตัด `audit_logs` (`database.md` บรรทัด 180) ว่า "ระบบ SBP เดิมไม่มี audit กลางของ master (มีเฉพาะ `general_upload_data_page_audit_log`)" — ไม่ตรงกับ schema จริง**

ของที่มีจริง:
- `sps_auth.user_log` — `action` · `table_name` · `key_field_name1-4` + `key_field_value1-4` · `detail` varchar(4000) · `user_id` FK → `users` · `log_date` → **row-level audit แบบ generic ที่ SBPGI เขียนลงได้เลยโดยไม่ต้องสร้างตาราง**
- `sps_auth.user_audit_events` — `action` · `meta` jsonb · `ip` inet · index บน `action` และ `created_at DESC`
- `sps_store.common_log` — `system` · `module` · `detail` text · `create_user_id` · `ip_address`

| | ทางเลือก A — คงมติเดิม (ไม่มี audit ของ master) | ทางเลือก B — เอากลับมาโดยเขียนลง `user_log`/`common_log` ของเดิม |
|---|---|---|
| **ข้อดี** | ไม่มีงานเพิ่ม · หน้าจอ/API/ฟิลด์ "เหตุผลการแก้ไข" ถูกตัดไปแล้วเรียบร้อย | ได้ร่องรอยว่าใครแก้ปัจจัยภายนอก/รายชื่อคู่แข่ง เมื่อไร · **ไม่ต้องสร้างตารางใหม่และไม่ต้องรื้อมติเดิม** (มติคือ "ไม่สร้างตาราง" ไม่ใช่ "ห้ามมี audit") |
| **ข้อเสีย** | ไม่มีร่องรอยการแก้ master เลย — ถ้า audit/compliance ถามภายหลังตอบไม่ได้ | +0.5–1 วัน · ต้องกลับมาเพิ่มการเรียก log ในเส้น CRUD ของ master |
| **ต้นทุน** | 0 | 0.5–1 วัน |

**ข้อเสนอแนะ:** ทาง **B** — ต้นทุนต่ำมากและไม่ขัดกับมติเดิม (ยังไม่มีตาราง `audit_logs`) · แต่ถ้าธุรกิจยืนยันว่าไม่ต้องการ audit ของ master จริง ๆ ทาง A ก็ถูกต้อง
**คำถามที่ต้องตอบ:** มีข้อกำหนด compliance/ตรวจสอบภายในที่ต้องการร่องรอยการแก้ master หรือไม่

---

## 5. สิ่งที่ยืนยันแล้วว่าต้องทำเอง

| รายการ | เหตุผลสั้น ๆ (หลักฐาน) |
|---|---|
| `fgi_impact_processes` ★ · `fgi_impact_stores` · `fgi_impact_sales_summaries` · `sales_transactions` · `fgi_impact_competitors` | ค้น `impact`/`fgi`/`compensat`/`guarantee`/`income`/`compet`/`growth`/`outlier`/`distance`/`radius`/`latitude`/`longitude`/`window_no` ในชื่อตาราง 276 ตัว และชื่อคอลัมน์ 4,396 ตัว = **0 hit ทุกคำ** |
| `compensation_documents` · `document_new_stores` · `document_competitors` · `document_external_factors` · `document_cost_details` | ไม่มีตารางเอกสารชดเชยในระบบเดิม · ไม่มีที่เก็บระยะทาง/%ชดเชย/ปัจจัยภายนอก · ไม่มีตารางใดมีครบ 3 มิติ (เอกสาร × เดือน × ร้านเปิดใหม่) |
| `compensation_histories` | `fr_store_insure` คีย์ด้วย `order_id` (สัญญา) ไม่ใช่ `doc_no` · ไม่มี `ref_doc_no`/`submit_account_month`/สถานะ I/C/A/N/S/Z · 708 แถว = ระดับสัญญา |
| `document_running_numbers` ★ | **ไม่มีตารางตัวนับใด ๆ ในทั้ง 276 ตาราง** · sequence ที่มีทั้งหมดเป็น identity ต่อตาราง รันต่อเนื่องไม่รีเซ็ตรายปี · ของเดิมใช้ `COUNT(1)+1` ไม่มี lock (`cooperation-request.service.ts:1988`) → batch (Job 8b) + ผู้ใช้พร้อมกันได้เลขชนกัน |
| helper แบ่งหน้า `{page,size,total,items}` | ไม่มี pagination helper กลาง · ของเดิมมี 3 รูปแบบขัดกันเอง + บั๊ก `Math.ceil(total)` ไม่หาร `pageSize` **6 จุด** |
| ตัวรายงาน Export Excel 14 คอลัมน์ (ตัว lib ยืมได้ แต่รายงานทำเอง) | ไม่มี Excel helper กลางให้ import — `export-styles.ts` เป็น local ของโมดูล evaluation-process |
| หน้า `GET /tasks` (filter · paging · bulk · แถวแดง) | `PendingTaskItemDto` ตัด `referenceId` ทิ้ง และไม่มี filter/paging/bulk เลย |
| ชั้น validate ไฟล์แนบ (≤5MB · นามสกุล · 413/415) | `AwsService` และทั้ง 2 endpoint เป็น pass-through ไม่ตรวจอะไรเลย · body limit = 100mb |
| integration กับ ALLMAP (Jobs 2/3) | ALLMAP เป็น SQL Server ภายนอกที่ระบบ SBP ปัจจุบัน**ไม่ได้ต่ออยู่เลย** — `ftp_interface` 145 แถวเก็บแต่ path SFTP ตาม report_type ไม่มีรายการคู่แข่ง |

---

## 6. ความเสี่ยง / ข้อควรระวัง

### 6.1 ตารางที่มีข้อมูลจริงเยอะแล้ว — การไปใช้ร่วมกระทบใคร

| ตาราง | แถวจริง | ใครใช้อยู่ | ถ้าเราไปแก้จะกระทบอะไร |
|---|---:|---|---|
| `fcs_qssi_score` | **23,958,780** | `performance.service.ts` (`POST /performance/import-qssi` + `report-qssi`) | เพิ่ม UNIQUE/`NOT NULL` = **ล็อกตาราง 23.9M แถวและอาจทำ import เดิมพัง** → ต้องคุยกับเจ้าของก่อน (DP-4) |
| `workflow_transaction` | 19,283 | `cooperation-request` (19,236 เอกสาร) · `inform-evaluate` · `@srm/glb-workflow` | เพิ่ม PK/index = แก้ตารางของ library ที่ทีมอื่นเป็นเจ้าของ ต้อง sign-off + regression test (DP-2) |
| `common_code` | 2,609 | **ทุกโมดูล** (store-backend เรียกว่า "lookup กลางที่ทั้งระบบพึ่ง") | เพิ่มคอลัมน์ `remark` หรือ seed ผิด `code_type`/`seq_no`/`active_flag` = **dropdown ของโมดูลอื่นเพี้ยน** (DP-9) |
| `mas_param` | 93,752 | ทุกโมดูล (อ่านกระจายเป็น raw SQL) | **ไม่มี PK/UNIQUE บน `param_name`** (มีแค่ index `mas_param_idx`) → `findOne` อาจได้แถวใดก็ได้ถ้าชื่อซ้ำ · ตารางถูกใช้เก็บข้อมูลรายร้านด้วย ไม่ใช่ config ล้วน → **ต้องใช้ prefix `SBPGI_` เสมอ** |
| `email_template` / `email_sent` | 85 / 5,214 | 6 โมดูล + `@gosoft-sbp/email-lib` | seed 8 แถวใหม่ปลอดภัย แต่ถ้าไม่เคลียร์ DP-5 จะเกิดเมลซ้ำ 2 ฉบับ |
| `store_sbp` | 11,583 | โมดูล store/contract | `store_id` **nullable และไม่มี index** → ทุก join จาก SBPGI = seq-scan (DP-3) |
| `integration_log` | 518 | แทบไม่มีใครใช้ | ถ้ายิงทุก call ของ QSSI/ALLMAP/IAS ลงตารางที่ **index มีแค่ PK** จะโตเร็วมากและ query ช้า |

### 6.2 กับดักที่ทำให้เลือกผิดได้ง่าย (ตารางชื่อคล้ายกันแต่คนละเรื่อง)

| อย่าสับสน | ✅ ตัวที่ถูก | ❌ ตัวที่ผิด |
|---|---|---|
| Workflow engine | `sps_store.workflow_*` (transaction 19,283 · history 38,010 · approver 96,542) | `sps_auth.workflow_*` (transaction 55 — ของ auth-backend) · `sps_store.wf_*` (`wf_step_history` 161,813 · `wf_approve` 155,740 — engine **เก่า** ชนิด `numeric(38,0)` แบบ Oracle) |
| Template อีเมล | `sps_store.email_template` (85) ตัวที่ `@gosoft-sbp/email-lib` ใช้ | `sps_store.wf_email_template` (118 — WF utility เดิมฝั่ง FCS · `WF_EMAIL_TEMPLATE_ID`/`DB_VIEW_NAME`/`CONTENT_FORMAT`) |
| Tracking ไฟล์แนบ | `document_attachments` ของเรา + `AwsService` | `fcs_file_mapping` (22,314 — **polymorphic pointer แบบเดียวกับบั๊ก E20 ที่เรากำลังแก้**) · `fml_*_statement_file` (เก็บ bytea ในฐานข้อมูล) |
| รหัสคู่แข่ง | `competitors` = แบรนด์ 01–11 (หน้า `k2-competitors.html`) | `document_competitors.competitor_code` = รหัส ALLMAP รายสาขา (`4832`, `TD58_08`, `LS3550`) — **คนละ domain ห้ามยัดรวม `code_type` เดียวกัน** |
| ข้อมูล QSSI | `fcs_qssi_score` | `fcs_qssi_score_bak_20260710` (18,577,924 — snapshot ก่อน rework ไม่มี PK/index **ห้ามอ่าน ห้าม join**) |

### 6.3 ความเสี่ยงเชิงกระบวนการ

1. **บั๊กที่จะติดมาถ้าลอกโค้ดเดิมโดยไม่ระวัง** — `Math.ceil(totalRecords)` ไม่หาร `pageSize` (6 จุด) · `LIMIT ${pageSize}` แบบ interpolate ไม่ใช่ bind param · `daysSinceDate()` ของ BFF ไม่ลบ 1 จากเดือน · `COUNT(1)+1` ออกเลขเอกสาร · `parseInt(store_code)` ทำเลขศูนย์นำหน้าหาย
2. **`readQuery()` วิ่ง replica** — ระวัง replication lag เมื่ออ่านทันทีหลังสร้างเอกสาร
3. **`AwsService` hardcode URL bucket dev** (`srm-sps-data-s3-dev...`) และไม่มี `deleteFile` — ต้องแจ้งทีมเดิมก่อน UAT/PRD
4. **`workflow_part_display` ยังใช้ไม่ได้** (wrapper register แค่ 10 entity) — แต่ **มีทางออกที่ดีกว่ารอ:** ใช้ `getPermissionEvents()` ที่พร้อมใช้อยู่แล้ว
5. **การพึ่งพาทีมอื่น 4 จุด** ที่อาจเป็น blocker: เจ้าของ `performance.service.ts` (DP-4) · ทีม `@srm/glb-workflow` (DP-2, DP-5) · ทีม store-backend เรื่อง `common_code` (DP-9) · ฝ่ายบัญชี/ธุรกิจเรื่อง `fr_store_insure` (DP-11) — **ควรยื่นเรื่องทั้ง 4 พร้อมกันตั้งแต่สัปดาห์แรก**

---

## 7. ขั้นตอนถัดไปหลังตัดสินใจ

### 7.1 ทำทันทีไม่ว่าจะตัดสินใจอย่างไร (ปลดล็อกหลาย DP พร้อมกัน · รวม ~1.5 วัน)

| # | งาน | ปลดล็อก | เวลา |
|---|---|---|---|
| 1 | **PoC อีเมล 1 route** — register route ทดสอบ ใส่ `email_id` แล้ว `triggerEvent` ดูว่ามีแถวใหม่ใน `email_sent` หรือไม่ | DP-5 (ทั้งข้อ) | 0.5 วัน |
| 2 | **นับ NULL + duplicate ใน `fcs_qssi_score`** (`store_id`/`category`/`month`/`year`) | DP-4 (ทั้งข้อ) | 0.5 ชม. |
| 3 | **ถามเจ้าของระบบ:** `transfer_sbp_date` = `start_sbp_date` หรือ `transfer_date` | DP-3 (ต้องรู้ทุกทาง) | — |
| 4 | **ยื่นขอ sign-off 3 เรื่องพร้อมกัน:** index บน `workflow_transaction` · constraint บน `fcs_qssi_score` · สิทธิ์เขียน `common_code` | DP-2, DP-4, DP-9 | — |
| 5 | ทดสอบ `getPermissionEvents()` กับ transaction ตัวอย่าง | ยืนยันว่าไม่ต้องรอ `workflow_part_display` | 0.5 วัน |

### 7.2 ถ้าเลือกแบบไหน ต้องไปแก้ไฟล์อะไร

| ตัดสินใจ | ไฟล์ที่ต้องแก้ |
|---|---|
| **DP-1** ไป B (surrogate id) | `database.md` — Cross-System Keys ข้อ 4 + Canonical Column Contract · `workflow.md` — Stage B/C (จุด initialize) · `api.md` — `POST /workflows/instances` + `POST /documents/{docNo}/actions` · `plan-database.html` · `plan-flow.html` · `plan-api.html` (รวม `SQL_BY_PATH` + `FLOWCHART_BY_PATH`) |
| **DP-1** ไป A (คงเดิม) | ไม่ต้องแก้ แต่**เพิ่มหมายเหตุใน `database.md`** ว่าแพตเทิร์นนี้ไม่มีในระบบเดิม และบันทึกความเสี่ยงเรื่องจังหวะออกเลข |
| **DP-2** ได้ sign-off | `database.md` — เพิ่มหมายเหตุ index ที่ขอเพิ่ม + เจ้าของ · เขียน migration script แยก (ไม่ใช่ของ SBPGI) |
| **DP-3** ไปทางเลือกที่ 3 (snapshot เฉพาะร้านที่เข้ารอบ) | `database.md` — เปลี่ยนคำอธิบาย `impacted_stores` จาก "master ร้าน SP" เป็น "snapshot ร้านที่เคยเข้ารอบชดเชย" + แก้ Cross-System Key ข้อ 1 · `plan-database.html` โซน C · `workflow.md` Stage B (เพิ่มขั้น upsert snapshot) |
| **DP-3** ไป A (view) | `database.md` — ย้าย `impacted_stores` ออกจาก 21 ตาราง (เหลือ 20) + เพิ่มนิยาม view · `plan-database.html` |
| **DP-4** ไป B (ตารางใหม่) | `database.md` — เปลี่ยนบรรทัด 56 (ที่ระบุว่าห้ามสร้างใหม่) · `plan-database.html` โซน A |
| **DP-5** ไปทางเลือกที่ 3 (ผสม) | `database.md` — เก็บ `status_email_rules` ไว้แต่เปลี่ยนขอบเขตเป็น "กฎผู้รับของเมลนอก route (reminder)" · `workflow.md` — ตารางสถานะ×อีเมล · `api.md` — endpoint reminder |
| **DP-5** ไป A ล้วน | ตัด `status_email_rules` ออกจาก `database.md` (21 → 20 ตาราง) + `plan-database.html` · **และต้องตอบให้ได้ว่า reminder รายสัปดาห์จะแขวนที่ไหน** |
| **DP-6** ไป B | `database.md` — ปรับคอลัมน์ `interface_transactions` ให้ตรงแพตเทิร์น expected/received · `plan-database.html` · `workflow.md` Stage D (Job 10) |
| **DP-7** ไป B | `database.md` — เปลี่ยนคำอธิบาย `consideration_logs` เป็นตารางส่วนขยาย + ตัดคอลัมน์ซ้ำ · `api.md` — `GET /documents/{docNo}/history` (ระบุว่า join engine) · `plan-api.html` `SQL_BY_PATH` |
| **DP-8** ไป A | ไม่ต้องแก้ (ตรงกับแผนปัจจุบัน) — แค่เพิ่มหมายเหตุว่าใช้ `AwsService` + ต้องครอบ validate เอง |
| **DP-9** แยกตัดสิน (`decisions`→A · อีก 2 ตัว→B) | `database.md` — ตัด `decisions` ออกจากโซน C (21 → 20 ตาราง) + คง `external_factors`/`competitors` · `api.md` — ลบ `GET /decisions` · `plan-database.html` · `plan-api.html` |
| **DP-10** ไป B (backend แยก) | `database.md` — ระบุ schema/DataSource · `api.md` — base URL + BFF routing · `SBP/srm-sps-spsap-sbp-bff` `BACKLOG_SOURCES` (แก้โค้ดจริง) · `plan-fe.md`/`plan-be.md` · `LLDD/md/BE/LLDD-BE-API-Common-Contracts.md` |
| **DP-11** ไป A (SBPGI เป็นต้นทาง) | `database.md` — เพิ่มความสัมพันธ์ `compensation_histories` → `fr_store_insure` · `workflow.md` Stage D · `api.md` — endpoint/job ที่เขียนกลับ |
| **DP-12** ไป B (audit ผ่านของเดิม) | `database.md` — แก้หัวข้อ "ยกเลิกระบบ audit ของ master" (บรรทัด 174–183) ให้ระบุว่าเขียนลง `user_log`/`common_log` · `api.md` — แถว Audit ในตารางสัญญากลาง · `assets/sbp.js` `SCHEMAS` (ถ้าเอาฟิลด์เหตุผลกลับมา) |

### 7.3 ไฟล์ที่ต้องแก้แน่นอนไม่ว่าตัดสินใจอย่างไร

| ไฟล์ | สิ่งที่ต้องแก้ |
|---|---|
| `database.md` ข้อ **F5** (บรรทัด 162) | ลบข้อเสนอ "เพิ่มคอลัมน์ renovate ใน `stores`" — **`sevenshop.start_renovate_date`/`end_renovate_date` มีอยู่แล้ว** |
| `database.md` ข้อ **F6** (บรรทัด 163) + หัวข้อ "ตารางที่คล้ายแต่ไม่ใช่" (บรรทัด 206) | ปรับข้อความ "ใช้ `integration_log` แทน `FGI_WS_LOG` ได้เลย" → ระบุว่าครอบได้เฉพาะ payload · ไม่มี error code/เวลา start-end/index |
| `database.md` บรรทัด **180** | แก้ข้อความ "ระบบ SBP เดิมไม่มี audit กลางของ master" — **ไม่จริง** (`user_log` · `user_audit_events` · `common_log`) |
| `database.md` หัวข้อ **P1 `TaskMaster`/`TaskList`** (บรรทัด 128) | ระบุว่ามีของเดิมรองรับ: `import_type` · `master_template_columns` · `view_column` |
| `database.md` ข้อ **F3** (`approver_snapshot`) | เพิ่มว่าธง "รักษาการ" มีคอลัมน์ตรง ๆ อยู่แล้ว: `mas_sbp_ad.position_acting` · `business_user.cpall_acting_supervisor_lvl` (ไม่ต้อง infer จาก `position_level`) และ resolve ผู้อนุมัติควรใช้ `store_organize` (PK `store_id,employee_id`) ไม่ใช่ `sevenshop` |
| `LLDD/md/BE/LLDD-BE-API-Common-Contracts.md` | เพิ่ม `PageRequestDto`/`PageResponse<T>` ของ SBPGI + ข้อห้ามลอกสูตร `totalPage` เดิม + ระบุว่าต้อง bind param |
| `LLDD/md/FE/LLDD-FE-Integration-Contracts.md` | ระบุว่าปุ่มผลพิจารณาเรนเดอร์จาก `getPermissionEvents()` ไม่ใช่ hardcode role |

---

**สรุปสิ่งที่ขอจากเจ้าของโครงการ:** ตอบ **DP-1 · DP-3 · DP-11** ก่อน (3 ข้อนี้เป็น blocker ของ schema) · อนุมัติให้ทำ **PoC 2 ตัวในหัวข้อ 7.1** (รวม 1.5 วัน) · และอนุมัติให้**ยื่นขอ sign-off 3 เรื่องกับทีมอื่นพร้อมกันตั้งแต่สัปดาห์แรก** ที่เหลือ (DP-2, DP-4 ถึง DP-10, DP-12) ตัดสินได้หลังผล PoC และคำตอบจากทีมอื่นกลับมา
