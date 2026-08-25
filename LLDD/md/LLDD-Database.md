# LLDD Database - Target Schema and Data Dictionary

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารนี้เป็น LLDD Database ระดับรวมของ target schema ระบบ SBPGI/SBP Mall ใช้เป็น reference สำหรับ BE API, Batch Job, migration, indexing, transaction และ data dictionary

## 2. Architecture Context

- ระบบใหม่รวม EAI และ K2 เข้าเป็น SBPGI ใช้ฐานข้อมูลเดียวกัน
- ไม่มีไฟล์ BPM06001O/BPM06002O/BPM06003O ภายในเพื่อส่งเข้า K2; ใช้ FK จาก compensation_documents ไป impact_process แทน
- Workflow ใช้ engine กลาง `@srm/glb-workflow` **13 ตาราง ใน schema `sps_store`** (workflow · workflow_version · workflow_state · workflow_status · workflow_event · workflow_route · workflow_group · workflow_group_map · workflow_transaction · workflow_history · workflow_approver · workflow_part · workflow_part_display) แทน K2 engine ภายนอก — SBPGI ไม่สร้างตาราง workflow ของตัวเอง (ตัดสินใจ 2026-08-06 · แก้จำนวนตารางจาก 10 เป็น 13 และแก้ schema จาก sps_auth เป็น sps_store เมื่อ 2026-08-07)
- ตัดขั้นบัญชี 04/05 (SDD v7.5 — รวมเข้าการออกแบบแล้ว ไฟล์ต้นฉบับถูกลบจาก repo 2026-08-06); workflow ใช้ section 06/08/01/02/03; SDD ที่ยึดเป็นหลักคือ SDD GI 24/02/2026
- มาตรฐานชื่อ table/column เป็น English lower_snake_case
- ตาราง job_configs / job_run_histories ถูกตัดออกจาก target schema เมื่อ 2026-08-06 พร้อม 2 แท็บควบคุมของหน้า Batch Job — cron/พารามิเตอร์อยู่ใน backend config · ผลการรันเขียน application log + interface_transactions

### 2.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | Target table catalog, data zones, primary keys, foreign-key relationships, migration assumptions, index needs, and transaction boundaries. |
| Progress | Use the data spine impact_process_id -> doc_no -> transaction_id -> approver_id (the last two live in sps_store.workflow_transaction / workflow_approver of @srm/glb-workflow, not in SBPGI tables) to implement APIs/jobs, then validate referential integrity and idempotency keys. |
| Output | Data dictionary and implementation reference for schema creation, migration, indexing, transaction handling, and test data preparation. |

## 3. Data Zones and Spine

| Zone | Scope | Core tables | Owner usage |
| --- | --- | --- | --- |
| A | FGI/FCS Impact Pipeline and external interfaces | fgi_impact_processes, fgi_impact_stores, sales, interface_transactions | Batch Jobs 1-7, IAS/ALLMAP/QSSI/STA tracking |
| B | K2 Document (workflow อยู่ที่ engine กลาง) | compensation_documents, document_* tables, consideration_logs, compensation_histories | Document APIs, workflow actions, FE detail/list/report |
| C | Master ที่ SBPGI เป็นเจ้าของ (RBAC/config/master ร้าน/ผลพิจารณา ใช้ของระบบ SBP เดิม) | impacted_stores, external_factors, competitors | Lookup, master maintenance, notification |

| Order | Key | Meaning | Used by |
| --- | --- | --- | --- |
| 1 | impact_process_id | หนึ่งร้านถูกกระทบ + หนึ่งงวด | FGI/FCS pipeline, Job 8/8b |
| 2 | doc_no | เอกสาร YYYY/xxxxx ปี ค.ศ. | Document APIs, reports, attachments |
| 3 | transaction_id (@srm/glb-workflow) | workflow transaction ต่อเอกสาร — `reference_id` = `compensation_documents.id` (surrogate · DP-1 ปิดแล้ว 2026-08-17) | Workflow engine ใน schema sps_store |
| 4 | approver_id (@srm/glb-workflow) | ผู้อนุมัติต่อ state — แทน task_id เดิม | Inbox/current approver guard |
| 5 | employee_id / user_id | identity — มาจาก BFF header ไม่ใช่ตารางของ SBPGI | lookup, assignment |

## 4. Data Dictionary

| Zone | Table | PK | FK / relationship | Role |
| --- | --- | --- | --- | --- |
| A | fgi_impact_stores | id | impact_process_id, impacted_store_code | impact pair; sales request and allocation data |
| A | fgi_impact_processes | id | impacted_store_code | impact process hub and canonical workflow_generation_status |
| A | fgi_impact_sales_summaries | id | impact_process_id | sales summary/growth rate |
| A | sales_transactions | id | sales_summary_id | daily sales 4 windows x 15 days |
| A | fgi_impact_competitors | id | impact_process_id | ALLMAP competitors |
| A | fcs_qssi_score | id | store_id + category + month + year | QSSI scores — ⚠️ REUSE ตารางเดิมของ sps_store (เอกพจน์ · 23,958,780 แถว · มี import pipeline POST /performance/import-qssi ใช้งานอยู่) ห้ามสร้างใหม่ และห้ามใช้ชื่อพหูพจน์ fcs_qssi_scores |
| A | interface_transactions | id | impact_process_id/sales_summary_id/doc_no | interface tracking replacement |
| B | compensation_documents | doc_no | impact_process_id, status_code, current_section_code | document header/core |
| B | document_new_stores | id | doc_no, new_store_code | new stores, compensate percent and amount |
| B | document_competitors | id | doc_no, competitor_code | document competitors |
| B | document_external_factors | id | doc_no, factor_code | document external factors |
| B | consideration_logs | id | doc_no | approval/action history (decision code, result category, attachments) |
| B | document_attachments | attach_id | doc_no | attachment metadata; file storage uses existing SBP S3 service |
| B | compensation_histories | id | store_code, ref_doc_no | compensation history/accounting export |
| B | document_cost_details | id | doc_no, new_store_code | monthly cost detail per new store (ImpactCostDetail) |
| B | document_running_numbers | year | - | atomic YYYY/xxxxx running number |
| C | impacted_stores | store_code | store.store_id (SBP · varchar(10)) | SP impacted store subset |
| C | external_factors | factor_code | - | external factor master |
| C | competitors | competitor_code | - | competitor master |
| - | USE EXISTING SBP TABLES | - | - | workflow engine 13 ตาราง ใน schema sps_store (workflow · workflow_version · workflow_state · workflow_status · workflow_event · workflow_route · workflow_group · workflow_group_map · workflow_transaction · workflow_history · workflow_approver · workflow_part · workflow_part_display) · store/mas_store/sevenshop · mas_zone · common_code · business_user · email_template + email_sent · mas_param · fcs_qssi_score — decided 2026-08-05/2026-08-06: do NOT recreate these in SBPGI |

### 4.1 Canonical Column Contract

| Table | Canonical columns used by DDL and SQL | Rejected legacy vocabulary |
| --- | --- | --- |
| workflow_transaction (@srm/glb-workflow) | transaction_id, version_id, reference_id, current_state_id, current_status_id, current_approver | instance_id/doc_no/instance_status ของตาราง workflow_instances ที่ถูกตัดไปแล้ว |
| common_code (ระบบ SBP เดิม) | code_type = SBPGI_APPROVE_LIMIT, code, code_value | system_configs/approve_limit_amount ที่ถูกตัดไปแล้ว |
| fcs_qssi_score (ระบบ SBP เดิม · เอกพจน์) | store_id, category_code, period, score | fcs_qssi_scores (พหูพจน์) — ห้ามใช้ |
| sales_transactions | txn_date, window_no, sales_amount, sales_diff, is_outlier | sale_date/window_code/net_sales |
| consideration_logs | result, result_category, detail, consider_by, action_datetime | result_code/comment/considered_by/considered_at |
| interface_transactions | id, acked_at | tracking_id/receive_date (API aliases only) |
| fgi_impact_processes | workflow_generation_status | duplicate workflow flag on fgi_impact_stores |

## 5. Executable DDL — 19 ตาราง (+ fcs_qssi_score ที่ reuse ของระบบ SBP เดิม = 20 ในโครง · + schema reference)

หัวข้อ 5.1-5.4 เป็น PostgreSQL DDL ของ **20 ตารางในโครง SBPGI** เรียงตาม dependency พร้อม PK, typed FK, unique/check constraint และ index ที่จำเป็น ใช้เป็น migration baseline ได้โดยไม่ต้องเดา column เพิ่มเติม

### 5.1 Zone C — Shared Master, RBAC, Config and Operations

```sql
-- ❌ ไม่สร้างตาราง stores ใน SBPGI — ใช้ store / mas_store / sevenshop ของระบบ SBP เดิม (API: GET /store/search · /store/list · /store/detail)

CREATE TABLE impacted_stores (
    store_code VARCHAR(5) PRIMARY KEY,   -- ร้าน SP · master อยู่ที่ store/mas_store/sevenshop ของระบบเดิม
    dv_code VARCHAR(20), opt_dv_user_id VARCHAR(30), latitude NUMERIC(10,7), longitude NUMERIC(10,7),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ❌ ไม่สร้างตาราง workflow_sections ใน SBPGI — ใช้ workflow_state / workflow_route ของ @srm/glb-workflow · วงเงินอนุมัติเก็บใน common_code (SBPGI_APPROVE_LIMIT)

-- ❌ ไม่สร้างตาราง document_statuses ใน SBPGI — ใช้ workflow_status ของ @srm/glb-workflow

-- ❌ ไม่สร้างตาราง roles ใน SBPGI — ใช้ auth-backend/ABS groups ของระบบ SBP เดิม (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง menus ใน SBPGI — ใช้ menus/permissions ของ auth-backend (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง menu_permissions ใน SBPGI — ใช้ permissions ต่อ URL ของ auth-backend (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง employees ใน SBPGI — ใช้ business_user / business_user_group ของระบบ SBP เดิม

ALTER TABLE impacted_stores
    -- opt_dv_user_id ไม่มี FK — ผู้ใช้อยู่ที่ business_user ของระบบ SBP เดิม (ตัด employees 2026-08-05)

-- ❌ ไม่สร้างตาราง operator_assignments ใน SBPGI — ใช้ group + scope ของ auth-backend + prepared approvers ของ @srm/glb-workflow (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง decisions ใน SBPGI — มติ DP-9 (2026-08-10) ย้ายไป common_code ของระบบ SBP เดิม
--    code_type='SBPGI_DECISION' · code_value=decision_code · code_name=decision_name
--    code_mapping=flow_name · other_value=result_name · remark=result_category+engine_event (จำกัด 50 ตัวอักษร)
--    FE อ่านผ่าน GET /common/common-code?codeType=SBPGI_DECISION (ตัดเส้น GET /decisions ออกแล้ว)
-- ⚠️ common_code ไม่มี PK และไม่มี unique constraint → กันรหัสซ้ำที่ระดับแอป
--    และต้องลงทะเบียน code_type ที่ common_code_type ก่อนใช้งาน

CREATE TABLE external_factors (
    factor_code VARCHAR(30) PRIMARY KEY,
    factor_name VARCHAR(200) NOT NULL, factor_remark VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- master แบรนด์คู่แข่ง 11 รายการ (รหัส 01-11) — ระบบเดิมเก็บชื่อทั้งไทยและอังกฤษ
-- คนละระดับกับ document_competitors ที่เก็บ "รายสาขา" พร้อมรหัสจาก ALLMAP (เช่น 4832, TD58_08)
CREATE TABLE competitors (
    competitor_code VARCHAR(30) PRIMARY KEY,
    name_th VARCHAR(200) NOT NULL,
    name_en VARCHAR(200) NOT NULL,
    remark VARCHAR(500),                 -- คอลัมน์ "รายละเอียดเพิ่มเติม" ของหน้า k2-competitors.html
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ❌ ไม่สร้างตาราง email_templates ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง email_template ของระบบ SBP เดิม (email_template_id · subject_format · body_format) + email_sent

-- ❌ ไม่สร้างตาราง status_email_rules (ปิด DP-5 · แก้มติ 2026-08-14) — workflow ให้เลข template ผ่าน workflow_route.email_id แล้ว SBPGI เรียก email-lib ส่งเอง
--    อีเมลของ batch job (EM-07 error · EM-08 watchdog) ไม่ใช่ workflow event → ส่งผ่าน @gosoft-sbp/email-lib ของระบบเดิม
--    ผู้รับของ batch job อยู่ใน backend config (config file/env) ไม่ใช่ตารางของ SBPGI


-- ❌ ไม่สร้างตาราง user_accounts ใน SBPGI — ใช้ AWS Cognito + auth-backend — SBPGI รับตัวตนจาก header ของ BFF (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง system_configs ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง mas_param ของระบบ SBP เดิม (param_name · param_value · ref_name · description · is_config · active_flag)
```

### 5.2 Zone A — Impact Pipeline, Sales and Interface

```sql
CREATE TABLE fgi_impact_processes (
    id BIGSERIAL PRIMARY KEY,
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7) NOT NULL,   -- 'YYYY-MM' (ค.ศ.)
    impact_year INTEGER NOT NULL,    -- แตกจาก impact_month เพื่อ filter รายปีโดยไม่ต้อง substring
    process_status VARCHAR(30) NOT NULL, action_status VARCHAR(30),
    last_compensation_amount NUMERIC(14,2),
    workflow_generation_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (workflow_generation_status IN ('W','Y','N')),
    -- ⬇ รับเข้าโครงตามมติ 2026-08-21 (gap F8) — ขนจาก ORA FGI_IMPACT_STORE_ON_PROCESS
    --   ใช้ตัดสิน "ประเภทเคส" ที่จุดเข้า flow และ auto-assign เจ้าของงานคนเดิม
    last_compensate_seq INTEGER NOT NULL DEFAULT 1,        -- รอบชดเชย (ขึ้นใหม่เมื่อเปิดเรื่องใหม่)
    last_compensate_seq_no INTEGER NOT NULL DEFAULT 1,     -- ครั้งที่ในรอบ · > 1 = เคสต่อเนื่อง
    start_compensate_month CHAR(7), start_compensate_year INTEGER,   -- กรอบงวดที่ชดเชยได้ (เริ่ม)
    end_compensate_month CHAR(7),   end_compensate_year INTEGER,     -- กรอบงวดที่ชดเชยได้ (จบ)
    -- ORA FGI_IMPACT_STORE_ON_PROCESS.FLAG_ACTION — โดเมนจริง Y/W/N (active = IN ('Y','W'))
    -- Job 6 ปิดรอบด้วย Y->N และพัก/รอจ่ายด้วย Y->W · CHECK เดิมที่รับแค่ ('Y','N') จะทำ migration ล้มทันทีที่เจอแถว 'W'
    flag_action CHAR(1) NOT NULL DEFAULT 'Y' CHECK (flag_action IN ('Y','W','N')),
    -- ช่องทางต้นทางของเคส (SDD GI สไลด์ 17 · 3 แหล่ง) — ORA FGI_IMPACT_STORE_ON_PROCESS.DATASOURCE
    --   ALM = ระบบดึงจาก ALLMAP (Job 2/3)   · STA = ระบบดึงจาก Franchise Statement (Job 5)   [ทั้งคู่มีในระบบเดิม]
    --   PRO = เชิงรุก  — OPT ประชุมพิจารณาแล้วเปิดเรื่อง (ต้นทางเอกสารอยู่ที่ All Memo)      [ใหม่ 2026-08-24]
    --   REA = เชิงรับ  — หน่วยงานอื่นแจ้งเข้ามาว่าร้านถูกกระทบ                                [ใหม่ 2026-08-24]
    -- ผลต่อ flow (SDD สไลด์ 47 · 49): ALM/STA = งานเข้ามาให้ จนท. SBP DSA เลือก · PRO/REA = เจ้าของงานต้องคีย์เอง
    -- ไม่ใส่ CHECK constraint — ระบบเดิมยังมีค่า HRS (HR feed) ปนอยู่ ถ้าบังคับโดเมนแคบจะ migrate ไม่ผ่าน
    datasource VARCHAR(5),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_process UNIQUE (impacted_store_code, impact_month)
);

-- รับเข้าโครงตามมติ 2026-08-21 (gap F1) — ขนจาก ORA FGI_IMPACT_STORE_COMPENSATE
-- ยอดชดเชย "รายงวด" ที่เกิดก่อนมีเอกสาร · จำเป็นเพื่อนับ "ยอด 0 ติดกันกี่เดือน" (กติกาเดือน 1-3 / เดือนที่ 4)
CREATE TABLE fgi_impact_compensations (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    compensate_seq INTEGER NOT NULL,        -- รอบ (คู่กับ fgi_impact_processes.last_compensate_seq)
    compensate_seq_no INTEGER NOT NULL,     -- ครั้งที่ในรอบ
    compensate_month CHAR(7) NOT NULL,      -- งวดที่ชดเชย 'YYYY-MM' (ค.ศ.)
    compensate_year INTEGER NOT NULL,
    forecast_amount NUMERIC(14,2),          -- ระบบคำนวณ
    adjust_amount NUMERIC(14,2),            -- คนปรับ · ยอดที่ใช้จริง = COALESCE(adjust_amount, forecast_amount)
    compensate_status VARCHAR(5),
    compensate_comment VARCHAR(4000),
    stmt_month INTEGER, stmt_year INTEGER,  -- งวด statement
    approve_date DATE,
    created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_compensation UNIQUE (impact_process_id, compensate_month)
);

CREATE TABLE fgi_impact_stores (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    new_store_code VARCHAR(5) NOT NULL,   -- ร้านเปิดใหม่ · master ของระบบเดิม
    impact_month CHAR(7) NOT NULL, distance_km NUMERIC(8,3),
    sales_request_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_request_status IN ('W','P','Y','E')),
    forecast_compensate_percent NUMERIC(7,4), adjust_compensate_percent NUMERIC(7,4),
    forecast_compensation_amount NUMERIC(14,2), adjust_compensation_amount NUMERIC(14,2),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_store_pair UNIQUE (impacted_store_code, new_store_code, impact_month)
);

CREATE TABLE fgi_impact_sales_summaries (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    total_working_days INTEGER NOT NULL DEFAULT 0 CHECK (total_working_days >= 0),
    growth_rate_before NUMERIC(9,4), growth_rate_after NUMERIC(9,4), growth_rate_diff NUMERIC(9,4),
    sales_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_status IN ('W','Y','N','E')),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_summary_process UNIQUE (impact_process_id)
);

CREATE TABLE sales_transactions (
    id BIGSERIAL PRIMARY KEY,
    sales_summary_id BIGINT NOT NULL REFERENCES fgi_impact_sales_summaries(id) ON DELETE CASCADE,
    txn_date DATE NOT NULL, window_no SMALLINT NOT NULL CHECK (window_no BETWEEN 1 AND 4),
    sales_amount NUMERIC(14,2) NOT NULL, sales_diff NUMERIC(14,2),
    is_outlier BOOLEAN NOT NULL DEFAULT FALSE, source_checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_day_window UNIQUE (sales_summary_id, txn_date, window_no)
);

CREATE TABLE fgi_impact_competitors (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    competitor_code VARCHAR(30) NOT NULL REFERENCES competitors(competitor_code),
    name_th VARCHAR(200), branch_th VARCHAR(200), opened_date DATE, closed_date DATE,
    period_key CHAR(7) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_competitor UNIQUE (impact_process_id, competitor_code, period_key)
);

-- ⚠️ fcs_qssi_score — ห้าม CREATE TABLE ใหม่ (ตรวจฐานจริง 2026-08-07)
--   ตารางนี้มีอยู่แล้วใน schema `sps_store` ชื่อ **เอกพจน์** `fcs_qssi_score`
--   มีข้อมูลจริง 23,958,780 แถว และมี import pipeline ทำงานอยู่
--   (`POST /performance/import-qssi` · staging `fcs_tmp_qssi_score` · `performance.service.ts`)
--   โครงคอลัมน์อ้างอิงด้านล่างเป็น target shape ที่ SBPGI ต้องการ — ต้องเทียบกับคอลัมน์จริงก่อน
--   ⚠️ ยังไม่ตัดสินว่าจะแก้ตารางเดิมอย่างไร (DP-4 · ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4)
--   ห้ามใช้ชื่อพหูพจน์ `fcs_qssi_scores` ทุกกรณี
-- target shape (reference only — ห้ามรันเป็น DDL):
--   id BIGSERIAL PK · store_code VARCHAR(5) · category_code VARCHAR(30) · score_period CHAR(7)
--   · score_value NUMERIC(10,4) · source_file_name · source_checksum · updated_at
--   · UNIQUE (store_code, category_code, score_period)

CREATE TABLE interface_transactions (
    id BIGSERIAL PRIMARY KEY,
    -- run_id เป็น correlation id ของรอบรัน (มาจาก application log) — ไม่มี FK เพราะ job_run_histories ถูกตัด 2026-08-06
    run_id VARCHAR(50),
    -- direction: OUT = ส่งไฟล์ออกไประบบภายนอก (Job 4 → IAS · Job 6 → STA) · IN = รับไฟล์/ACK กลับ (Job 5 · callback ของ STA)
    --            INTERNAL = การส่งต่อ*ภายในระบบเดียวกัน* ที่มาแทนไฟล์ EAI เดิม (Jobs 7/8/9 เขียน DB ตรง — ไม่มี ACK ให้รอ จึงจบที่ status = COMPLETED)
    -- ชุดค่าปิด 9 ค่า เขียนโดย batch เท่านั้น (ไม่ใช่ input ของผู้ใช้) — ต้องล็อกเพราะ data_name เป็นส่วนหนึ่งของ
    -- UNIQUE ที่กันส่งซ้ำ และเป็นตัวกรองของ watchdog Job 10 · พิมพ์ผิดหนึ่งตัว = กันซ้ำไม่ทำงาน + watchdog เงียบ
    -- เพิ่ม interface ใหม่ = ALTER CONSTRAINT + อัปเดตตารางใน database.md พร้อมกัน
    data_name VARCHAR(80) NOT NULL CHECK (data_name IN (
        'IAS_SALES_REQUEST',                                    -- Job 4 -> IAS/MIS (OUT)
        'IMPACT_STORE_SALES',                                   -- Job 5 <- IAS/MIS (IN)
        'COMPENSATE_INIT_I','COMPENSATE_INIT_N',                -- Job 6 -> STA (OUT)
        'COMPENSATE_APPROVE_I','COMPENSATE_APPROVE_N',          -- Job 6 -> STA (OUT)
        'IMPACT_COMPETITOR','IMPACT_STORE','NEW_STORE'          -- Jobs 7/8/9 เขียน DB ตรง (INTERNAL)
    )),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('IN','OUT','INTERNAL')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','SENT','ACKED','COMPLETED','FAILED','FAILED_RETRY')),
    impact_process_id BIGINT REFERENCES fgi_impact_processes(id),
    sales_summary_id BIGINT REFERENCES fgi_impact_sales_summaries(id),
    doc_no VARCHAR(10), business_key VARCHAR(200) NOT NULL, period_key VARCHAR(20) NOT NULL,
    correlation_id VARCHAR(100), file_name VARCHAR(255), file_checksum VARCHAR(64),
    outbox_status VARCHAR(20), return_code VARCHAR(50), return_message VARCHAR(500),
    retry_count INTEGER NOT NULL DEFAULT 0, sent_at TIMESTAMP, acked_at TIMESTAMP,
    -- marker กัน watchdog (Job 10) ส่งอีเมลเตือนซ้ำในวันเดียวกัน — ย้ายมาจาก audit_logs ที่ยกเลิก 2026-08-07
    last_ack_notified_on DATE,
    purge_after TIMESTAMP, legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP,
    CONSTRAINT uq_interface_business UNIQUE (data_name, direction, business_key, period_key),
    CONSTRAINT ck_interface_typed_reference CHECK (num_nonnulls(impact_process_id, sales_summary_id, doc_no) >= 1)
);
```

### 5.3 Zone B — Document and Internal Workflow

```sql
-- ✅ มติ DP-1 (2026-08-10 · ทางเลือก B): PK เป็น surrogate `id` · `doc_no` เป็น UNIQUE ไม่ใช่ PK
-- ⚠️ ผลที่ตามมาซึ่งยังต้องตัดสิน: ตารางลูก 8 ตัว (document_new_stores · document_competitors ·
--    document_external_factors · consideration_logs · document_attachments · document_cost_details ·
--    compensation_histories · interface_transactions) ยัง FK ด้วย doc_no แบบ NOT NULL
--    → แปลว่า "ต้องออก doc_no ให้เสร็จก่อนจึงบันทึกส่วนย่อยได้"
--    ถ้าธุรกิจต้องการสร้างเอกสารก่อนออกเลข ต้องเปลี่ยนตารางลูกไป FK ที่ id แทน (ยังไม่ตัดสิน)
--    referenceId ที่ส่งให้ @srm/glb-workflow = id (ตรงกับที่ระบบเดิมทำจริงใน cooperation-request/inform-evaluate)
--    doc_no อาจยังว่างตอนสร้างแถว แล้วออกเลขทีหลัง จึงเป็น NULL ได้
CREATE TABLE compensation_documents (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) UNIQUE,          -- YYYY/xxxxx (ปี ค.ศ.) · ออกจาก document_running_numbers
    year INTEGER, running_no INTEGER,   -- แตกจาก doc_no เพื่อ index/ค้นหา (NULL จนกว่าจะออกเลข)
    impact_process_id BIGINT NOT NULL UNIQUE REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7), new_store_code VARCHAR(5),   -- master ของระบบเดิม
    round_no INTEGER, loop_no INTEGER,  -- CompMainLoopNo / CompLoopNo — หน้าจอแสดง "รอบ 1 · ครั้งที่ 3"
    source VARCHAR(20) NOT NULL DEFAULT 'FS' CHECK (source IN ('FS','MANUAL')),
    status_code VARCHAR(2) NOT NULL,   -- ค่าจาก sps_store.workflow_status ของ engine
    current_section_code VARCHAR(2),   -- ค่าจาก sps_store.workflow_state ของ engine
    total_compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    allmap_url VARCHAR(500),                   -- CompUrlMap — ปุ่ม Link To ALLMAP
    statement_id VARCHAR(50),                  -- CompStatementID — โยงกลับ SBP Statement ต้นทาง
    statement_date DATE,                       -- Period Statement (ค.ศ.) — ตัวกรอง/คอลัมน์ของรายงาน SDD สไลด์ 60
    account_year INTEGER, account_month INTEGER,   -- งวดบัญชี
    approver_snapshot JSONB,                   -- FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร
    version_no INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(30) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(30), updated_at TIMESTAMP,
    CONSTRAINT uq_comp_year_running UNIQUE (year, running_no),
    CONSTRAINT uq_comp_business UNIQUE (source, impacted_store_code, impact_month, new_store_code, round_no)
);

ALTER TABLE interface_transactions
    ADD CONSTRAINT fk_interface_doc_no FOREIGN KEY (doc_no) REFERENCES compensation_documents(doc_no);

CREATE TABLE document_new_stores (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL,   -- ร้านเปิดใหม่ · master ของระบบเดิม
    distance_km NUMERIC(8,3), compensate_percent NUMERIC(7,4) NOT NULL CHECK (compensate_percent BETWEEN 0 AND 100),
    compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    source_system VARCHAR(30) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_new_store UNIQUE (doc_no, new_store_code)
);

CREATE TABLE document_competitors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    competitor_code VARCHAR(30) NOT NULL REFERENCES competitors(competitor_code),
    name_th VARCHAR(200), branch_th VARCHAR(200), opened_date DATE, closed_date DATE, impact_date DATE,
    detail TEXT, remark TEXT, source_system VARCHAR(30) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_competitor UNIQUE (doc_no, competitor_code)
);

CREATE TABLE document_external_factors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    factor_code VARCHAR(30) NOT NULL REFERENCES external_factors(factor_code),
    date_from DATE, date_to DATE, detail TEXT, remark TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_factor UNIQUE (doc_no, factor_code, date_from),
    CONSTRAINT ck_doc_factor_dates CHECK (date_to IS NULL OR date_from IS NULL OR date_to >= date_from)
);

CREATE TABLE consideration_logs (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL,   -- ค่าจาก sps_store.workflow_state ของ engine
    result VARCHAR(100) NOT NULL,
    -- APPROVE=ประกันรายได้ · REJECT=ไม่ประกันรายได้ · CANCELLED=ยกเลิกโดยระบบ (decision 14 CancelBySystem) · PENDING=ยังไม่มีผล
    result_category VARCHAR(50) CHECK (result_category IN ('APPROVE','REJECT','CANCELLED','PENDING')),
    detail TEXT,
    consider_by VARCHAR(30) NOT NULL,   -- ผู้ใช้จาก business_user ของระบบเดิม
    action_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, request_id VARCHAR(80)
);

CREATE TABLE document_attachments (
    attach_id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL,   -- ค่าจาก sps_store.workflow_state ของ engine
    file_name VARCHAR(255) NOT NULL, mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size <= 5242880),
    storage_provider VARCHAR(30) NOT NULL, bucket VARCHAR(120) NOT NULL,
    object_key VARCHAR(500) NOT NULL, sha256 VARCHAR(64) NOT NULL,
    scan_status VARCHAR(20) NOT NULL CHECK (scan_status IN ('PENDING','CLEAN','BLOCKED','FAILED')),
    scanned_at TIMESTAMP, scan_message VARCHAR(500), uploaded_by VARCHAR(30) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, deleted_flag CHAR(1) NOT NULL DEFAULT 'N',
    CONSTRAINT uq_doc_attachment_hash UNIQUE (doc_no, sha256, deleted_flag)
);

CREATE TABLE compensation_histories (
    id BIGSERIAL PRIMARY KEY,
    store_code VARCHAR(5) NOT NULL,   -- master ของระบบเดิม
    ref_doc_no VARCHAR(10) REFERENCES compensation_documents(doc_no),
    submit_account_month CHAR(7) NOT NULL, compensate_amount NUMERIC(14,2) NOT NULL,
    accounting_status VARCHAR(30), external_ref VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_compensation_history UNIQUE (store_code, ref_doc_no, submit_account_month)
);

CREATE TABLE document_cost_details (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL,
    cost_year SMALLINT NOT NULL, cost_month SMALLINT NOT NULL CHECK (cost_month BETWEEN 1 AND 12),
    cost_target_n NUMERIC(14,2), cost_amount_n NUMERIC(14,2),
    cost_target_nc NUMERIC(14,2), cost_amount_nc NUMERIC(14,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_document_cost_detail UNIQUE (doc_no, new_store_code, cost_year, cost_month)
);

CREATE TABLE document_running_numbers (
    year SMALLINT PRIMARY KEY,   -- ปี ค.ศ. เท่านั้น (เช่น 2026) ห้ามเก็บ พ.ศ.
    last_running_no INTEGER NOT NULL DEFAULT 0 CHECK (last_running_no >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ⚠️ year เป็น "ค.ศ." (มติ 2026-08-06 · ทั้งระบบเป็น ค.ศ. — หน้าจอ K2 จริงก็ ค.ศ. เช่น 2026/01870)
--    ห้ามใช้ พ.ศ. · ถ้า client ส่ง พ.ศ. มา ให้ BE แปลงด้วย toAD(y) = y >= 2500 ? y - 543 : y ก่อนเสมอ
-- ออกเลขแบบ atomic (upsert กันกรณีปีใหม่ยังไม่มีแถว):
--   INSERT INTO document_running_numbers (year, last_running_no) VALUES (:ad_year, 1)
--   ON CONFLICT (year) DO UPDATE SET last_running_no = document_running_numbers.last_running_no + 1,
--                                    updated_at = CURRENT_TIMESTAMP
--   RETURNING last_running_no;   (row lock กันเลขชนเมื่อ batch และผู้ใช้สร้างพร้อมกัน)
--   doc_no = :ad_year || '/' || LPAD(last_running_no::text, 5, '0')

-- ❌ ไม่สร้างตาราง workflow_instances ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ workflow_transaction ของ @srm/glb-workflow

-- ❌ ไม่สร้างตาราง workflow_tasks ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ workflow_approver/workflow_transaction ของ @srm/glb-workflow
```

### 5.4 Required Indexes, Partial Uniqueness and Purge

```sql
CREATE INDEX idx_document_status_section ON compensation_documents(status_code, current_section_code);
CREATE INDEX idx_document_impact_process ON compensation_documents(impact_process_id);
-- ❌ ไม่มี index ของ workflow_tasks/workflow_instances ใน SBPGI — ตารางทั้งสองถูกตัดไปแล้ว (2026-08-06)
--    งานค้าง/ผู้อนุมัติปัจจุบันอ่านจาก workflow_transaction + workflow_approver ของ @srm/glb-workflow (schema sps_store)
--    ⚠️ sps_store.workflow_transaction ไม่มี PK และไม่มี index เลย ทั้งที่มี 19,283 แถว (ตรวจ 2026-08-07)
--       -> ยังไม่ตัดสิน (DP-2) ว่าจะขอ sign-off ให้ทีมเจ้าของ library เพิ่ม PK/UNIQUE/index
--          หรือจะกันซ้ำ + ทำ index ที่ฝั่ง SBPGI เอง · ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
CREATE INDEX idx_consideration_timeline ON consideration_logs(doc_no, action_datetime DESC);
CREATE INDEX idx_interface_pending ON interface_transactions(data_name, status, sent_at);
CREATE INDEX idx_interface_impact_process ON interface_transactions(impact_process_id);
CREATE INDEX idx_interface_sales_summary ON interface_transactions(sales_summary_id);
CREATE INDEX idx_interface_doc ON interface_transactions(doc_no);

-- index รองรับ FK ที่ PostgreSQL ไม่สร้างให้เอง (เพิ่ม 2026-08-24 หลังตรวจ FK coverage)
CREATE INDEX idx_impact_store_process ON fgi_impact_stores(impact_process_id);
CREATE INDEX idx_document_impacted_store ON compensation_documents(impacted_store_code);
CREATE INDEX idx_compensation_history_doc ON compensation_histories(ref_doc_no);
CREATE INDEX idx_impact_compensation_store ON fgi_impact_compensations(impacted_store_code);
CREATE INDEX idx_impact_competitor_code ON fgi_impact_competitors(competitor_code);
CREATE INDEX idx_document_competitor_code ON document_competitors(competitor_code);
CREATE INDEX idx_document_factor_code ON document_external_factors(factor_code);

-- index ที่หัวข้อ 6 (Index & Constraint) ระบุไว้ — เดิมมีแต่ในตารางสรุป ยังไม่ถูกสร้างจริง (เพิ่ม 2026-08-25)
CREATE INDEX idx_attachment_scan_status ON document_attachments(scan_status);
CREATE INDEX idx_consideration_result ON consideration_logs(result_category);

-- Retention worker: delete only terminal, expired, non-held rows in bounded batches.
WITH purge_candidates AS (
    SELECT id FROM interface_transactions
    WHERE status IN ('ACKED', 'COMPLETED')
      AND purge_after < CURRENT_TIMESTAMP
      AND legal_hold = FALSE
      AND data_name = ANY(:data_names)
    ORDER BY id
    LIMIT :batch_size
    FOR UPDATE SKIP LOCKED
)
DELETE FROM interface_transactions i
USING purge_candidates p
WHERE i.id = p.id
RETURNING i.id, i.data_name, i.business_key;
```

## 6. Index and Constraint Plan

| Table | Index / constraint | Reason |
| --- | --- | --- |
| compensation_documents | UNIQUE (year, running_no), UNIQUE(source, impacted_store_code, impact_month, new_store_code, round_no), INDEX(status_code,current_section_code), INDEX(impact_process_id) | docNo uniqueness, duplicate guard, list/inbox/report, pipeline trace |
| workflow_transaction (@srm/glb-workflow · sps_store) | ปัจจุบัน **ไม่มี PK และไม่มี index เลย** ทั้งที่มี 19,283 แถว (ตรวจ 2026-08-07) — ที่ต้องการคือ PK(transaction_id) + UNIQUE(version_id, reference_id) + INDEX(current_approver) | current approver guard และ inbox · เป็นตารางของ library ไม่ใช่ของ SBPGI จึงต้องขอ sign-off (DP-2 · ยังไม่ตัดสิน) |
| document_new_stores | INDEX(doc_no) *(ได้จาก UNIQUE (doc_no, new_store_code))*, CHECK compensate_percent between 0 and 100 | detail load and allocation validation |
| consideration_logs | INDEX(doc_no, action_datetime DESC), INDEX(result_category) | timeline/report result filter |
| document_attachments | INDEX(doc_no) *(ได้จาก UNIQUE ที่ขึ้นต้นด้วย doc_no)*, INDEX(scan_status), UNIQUE(doc_no, sha256, deleted_flag) | attachment list/download/security |
| interface_transactions | INDEX(data_name,status), INDEX(impact_process_id), INDEX(doc_no) | tracking and pending ACK |

## 7. Transaction Rules

| Use case | Transaction boundary | Rollback rule |
| --- | --- | --- |
| Create document | docNo sequence lock (document_running_numbers) + compensation_documents + initializeWorkflow/addPreApprover ของ @srm/glb-workflow | any fail rollback all; no partial document · engine อยู่คนละ DataSource จึงต้องมี compensating action เมื่อ commit ฝั่งใดฝั่งหนึ่งไม่ผ่าน |
| Submit action | ตรวจ current_approver จาก workflow_transaction + insert consideration_logs + eventWorkflow (เดิน state) + update compensation_documents | duplicate/current approver conflict returns 409 |
| Auto-assign (SDD 46/48) | 06 เห็นควรไม่ชดเชย -> ปิดเอกสารและตั้งงานเดือนถัดไปให้เจ้าของงานคนเดิม ผ่าน addPreApprover · 06 หยุดชดเชยฯ -> เอกสารกลับเข้า GET /tasks ของ 06 ทันที (stoppedReopenable) | เดือนที่กดเห็นควรไม่ชดเชย ต้องไม่พบเอกสารใน GET /tasks ของ 06 · เดือนถัดไปต้องพบพร้อม assignee คนเดิม |
| Attachment upload | metadata insert only after storage write and AV clean; objectKey never exposed | storage/scan fail leaves no CLEAN metadata |
| Job 4 IAS request | durable file (fsync + atomic rename + checksum) ก่อน transaction W→P + outbox READY | file fail คง W; DB fail rollback W→P/outbox; S3 upload fail retry transaction เดิม |
| Interface ACK/purge | ACK compare-and-set บน transaction เดิม; purge เฉพาะ terminal + purge_after + non-held | pending/failed/unacked/legal-hold ห้ามลบ |
| Master mutation | update entity ใน transaction เดียว | mutation fail ต้อง rollback ครบ |

## 8. Seed Data

| Domain | Required seed |
| --- | --- |
| workflow_state / workflow_status (@srm/glb-workflow) | 5 ขั้น 06, 08, 01, 02, 03 + state จบ flow · 6 สถานะเอกสาร (5 waiting + เสร็จสิ้น) — ลงทะเบียนที่ engine ไม่ใช่ตารางของ SBPGI |
| (ไม่สร้าง) decisions | ย้ายไป common_code ของระบบเดิม — มติ DP-9 2026-08-10 |
| competitors | แบรนด์คู่แข่ง 11 รายการ รหัส 01-11 (ไทย + อังกฤษ) |
| external_factors | ปัจจัยภายนอกที่ใช้อยู่ |
| email_template (ระบบ SBP เดิม) | EM-01..EM-08 |
| common_code / mas_param (ระบบ SBP เดิม) | SBPGI_APPROVE_LIMIT: THRESHOLD=100000 (เกณฑ์เดียว · มติ 2026-08-18), impact radius 1/2 km, sales data threshold=60, growth rate threshold=-10 |

## 9. Migration and Verification Checklist

| Area | Check |
| --- | --- |
| Naming | all new tables/columns lower_snake_case |
| Leading zero | store_code/new_store_code stored as VARCHAR(5), never numeric |
| docNo | year/running_no/doc_no generated in DB transaction; concurrency test 20 parallel requests |
| Workflow | no active 04/05 accounting sections/statuses; ไม่มีตาราง workflow ของ SBPGI — ตรวจว่า state/route ถูกลงทะเบียนที่ engine ครบ |
| Security | no secrets in mas_param/backend config; storage objectKey not returned to FE |
| External interface | credential/certificate/private key อยู่ Secret Manager ผ่าน secretRef; TLS verify-full (HTTPS สำหรับ EAI S3 · AMQPS สำหรับ RabbitMQ ของ STA); ทดสอบ rotation และ invalid certificate/host key |
| Tracking retention | backfill typed FK/purge_after, validate FK, dry-run count แล้ว purge เฉพาะ ACKED/COMPLETED เป็น batch; reconcile count ก่อน/หลัง |
| Data integrity | FK/check constraints enabled before SIT; reject legacy invalid enum values |
| Performance | list/report/inbox queries explain plan uses indexes above |

## 10. Related LLDD

| Document | DB usage |
| --- | --- |
| LLDD-BE-API-Document-List-Search | workflow_transaction / workflow_approver (@srm/glb-workflow)(R), compensation_documents(R), impacted_stores(R), fgi_impact_sales_summaries(R) |
| LLDD-BE-API-Document-Create-Update | compensation_documents(R/W), workflow_transaction / workflow_approver (@srm/glb-workflow)(W), document_new_stores(R/W), document_competitors(R/W) |
| LLDD-BE-API-Document-Detail-Aggregate | compensation_documents(R), impacted_stores(R), document_new_stores(R), document_competitors(R) |
| LLDD-BE-API-Document-Workflow-Actions | workflow_transaction / workflow_history / workflow_approver (@srm/glb-workflow)(R (เขียนผ่าน lib)), compensation_documents(W), consideration_logs(W), workflow_transaction (@srm/glb-workflow)(R (เขียนผ่าน lib)) |
| LLDD-BE-API-Workflow-Instances | fgi_impact_processes / fgi_impact_stores(R/W), compensation_documents(R/W), workflow_transaction (@srm/glb-workflow)(W (โดย lib)), workflow_approver (@srm/glb-workflow)(W) |
| LLDD-BE-API-Attachment-Sales-Timeline | document_attachments(R/W), compensation_documents(R), fgi_impact_sales_summaries(R), sales_transactions(R) |
| LLDD-BE-API-Lookup | impacted_stores (SBPGI) / store · mas_store · sevenshop (SBP เดิม)(R), workflow_status / workflow_state (@srm/glb-workflow · sps_store)(R), business_user (SBP เดิม)(R), auth-backend groups / menus / permissions (ระบบเดิม)(R) |
| LLDD-BE-API-Report-and-Master-Data | compensation_documents(R), compensation_histories(R), consideration_logs(R), auth-backend group + scope (business_user_group) / prepared approver ของ @srm/glb-workflow(R) |
| LLDD-BE-Job-Batch-Email-SRM | (backend config: config file/env)(R), (application log แบบ structured)(W), interface_transactions(R/W), email_template (SBP)(R) |
| LLDD-BE-Database-Structure | 20 target tables (โซน A/B/C)(W), workflow engine 13 ตาราง (sps_store)(R), fcs_qssi_score (sps_store)(R), mas_param / common_code / business_user / email_template (sps_store)(R) |
| LLDD-BE-Data-Migration-Cutover | ORA FCS_FRN (FGI_IMPACT_* · FCS_QSSI_SCORE · FGI_CONFIRM_RECEIVE_DATA)(R), MSSQL CPA_FRN_FGI (CompensateFlow · CompensateHistory · ImpactProfile · ImpactCostDetail · RunningNumber)(R), 20 target tables (โซน A/B/C)(W), workflow_transaction / workflow_approver / workflow_history (sps_store)(W) |
| LLDD-BE-Integration-SBP-Platform | mas_param (sps_store)(R), common_code / common_code_type (sps_store)(R), email_template (sps_store)(R), email_sent (sps_store)(W (โดย email-lib)) |
| LLDD-BE-Workflow-Engine-Definition | workflow / workflow_version / workflow_state / workflow_status / workflow_event / workflow_route (sps_store)(R + W ครั้งเดียวตอน setup), workflow_group / workflow_group_map (sps_store)(R + W ครั้งเดียวตอน setup), workflow_transaction / workflow_history / workflow_approver (sps_store)(R (เขียนผ่าน lib เท่านั้น)), workflow_part / workflow_part_display (sps_store)(R + W ครั้งเดียวตอน setup) |
| LLDD-BE-Job-2-ImportImpactStore | fgi_impact_stores(W) |
| LLDD-BE-Job-3-ImportImpactCompetitor | fgi_impact_competitors(W) |
| LLDD-BE-Job-4-PrepareImpactStoreToIAS | fgi_impact_stores(R/W), fgi_impact_sales_summaries(R/W), interface_transactions(W), (application log แบบ structured)(W) |
| LLDD-BE-Job-5-ImportImpactSaleFromIAS | sales_transactions(W), fgi_impact_sales_summaries(R/W), interface_transactions(W) |
| LLDD-BE-Job-6-ExportImpactStoreToFS | fgi_impact_processes(R/W), fgi_impact_stores(R/W), fcs_qssi_score(R), interface_transactions(W) |
| LLDD-BE-Job-7-SyncCompetitorToDocument | fgi_impact_competitors(R), compensation_documents(R), document_competitors(W), interface_transactions(W) |
| LLDD-BE-Job-8-CreateCompensationDocument | document_running_numbers(R/W), fgi_impact_stores(R/W), fgi_impact_processes(R), compensation_documents(W) |
| LLDD-BE-Job-8b-StartInternalWorkflow | fgi_impact_processes(R), fgi_impact_compensations(R), impacted_stores(R), fgi_impact_stores(R/W) |
| LLDD-BE-Job-9-SyncNewStoreToDocument | fgi_impact_compensations(R), fgi_impact_stores(R), compensation_documents(R), document_new_stores(W) |
| LLDD-BE-Job-10-NotifyNoReceiveData | interface_transactions(R), email_template (ระบบ SBP เดิม)(R), email_sent (ระบบ SBP เดิม)(W (โดย @gosoft-sbp/email-lib)), (backend config)(R) |
