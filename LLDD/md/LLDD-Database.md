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
- ตาราง job_configs และ job_run_histories เป็น schema reference สำหรับ BE/dev; ไม่ใช่ scope ให้ FE Batch Monitor ทำ tab Database ที่ใช้

## 2.1 Input / Progress / Output Contract

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
| C | Master ที่ SBPGI เป็นเจ้าของ (RBAC/config/master ร้าน ใช้ของระบบ SBP เดิม) | impacted_stores, decisions, external_factors, competitors, status_email_rules | Lookup, master maintenance, notification |

| Order | Key | Meaning | Used by |
| --- | --- | --- | --- |
| 1 | impact_process_id | หนึ่งร้านถูกกระทบ + หนึ่งงวด | FGI/FCS pipeline, Job 8/8b |
| 2 | doc_no | เอกสาร YYYY/xxxxx ปี พ.ศ. | Document APIs, reports, attachments |
| 3 | transaction_id (@srm/glb-workflow) | workflow transaction ต่อเอกสาร — reference_id ยังไม่ตัดสินว่าเป็น doc_no หรือ surrogate id (DP-1) | Workflow engine ใน schema sps_store |
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
| A | fcs_qssi_score | id | store_id + category_code + period | QSSI scores — ⚠️ REUSE ตารางเดิมของ sps_store (เอกพจน์ · 23,958,780 แถว · มี import pipeline POST /performance/import-qssi ใช้งานอยู่) ห้ามสร้างใหม่ และห้ามใช้ชื่อพหูพจน์ fcs_qssi_scores |
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
| C | impacted_stores | store_code | store.store_code (SBP) | SP impacted store subset |
| C | decisions | decision_code | - | decision master (button/flow/result names) |
| C | external_factors | factor_code | - | external factor master |
| C | competitors | competitor_code | - | competitor master |
| C | status_email_rules | status_code | workflow state (SBP) | notification recipients |
| REF | job_configs | job_no | - | schema reference สำหรับ batch schedule/config เท่านั้น — ไม่นับใน 21 ตาราง (ตัดพร้อม 2 tab ควบคุมของหน้า Batch Job 2026-08-06) |
| REF | job_run_histories | run_id | job_no | schema reference สำหรับประวัติการรัน — ไม่นับใน 21 ตาราง; ผลการรันจริงเขียน application log |
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

## 5. Executable DDL — 21 Tables (+ schema reference)

หัวข้อ 5.1-5.4 เป็น PostgreSQL DDL ของ **21 ตารางในโครง SBPGI** เรียงตาม dependency พร้อม PK, typed FK, unique/check constraint และ index ที่จำเป็น ใช้เป็น migration baseline ได้โดยไม่ต้องเดา column เพิ่มเติม · ในจำนวนนี้ `fcs_qssi_score` **ไม่มี CREATE TABLE เพราะ reuse ตารางเดิมของ `sps_store`** (สร้างจริง 20 ตาราง) · หัวข้อ **5.5 เป็น schema reference ที่ไม่นับใน 21 ตาราง** (`job_configs` / `job_run_histories` ที่ถูกตัดออกเมื่อ 2026-08-06) ห้ามนำไป deploy

### 5.1 Zone C — Shared Master, RBAC, Config and Operations

```sql
-- ❌ ไม่สร้างตาราง stores ใน SBPGI — ใช้ store / mas_store / sevenshop ของระบบ SBP เดิม (API: GET /store/search · /store/list · /store/detail)

CREATE TABLE impacted_stores (
    store_code VARCHAR(5) PRIMARY KEY REFERENCES stores(store_code),
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
    ADD CONSTRAINT fk_impacted_store_opt_dv FOREIGN KEY (opt_dv_user_id) REFERENCES employees(employee_id);

-- ❌ ไม่สร้างตาราง operator_assignments ใน SBPGI — ใช้ group + scope ของ auth-backend + prepared approvers ของ @srm/glb-workflow (ตัดสินใจ 2026-08-05)

CREATE TABLE decisions (
    decision_code VARCHAR(30) PRIMARY KEY,
    decision_name VARCHAR(200) NOT NULL,
    flow_name VARCHAR(200), result_name VARCHAR(200),
    section_code VARCHAR(2) NOT NULL,
    result_category VARCHAR(20) NOT NULL CHECK (result_category IN ('APPROVE','REJECT','PENDING')),
    engine_event VARCHAR(20) NOT NULL CHECK (engine_event IN ('save','submit','approve','reject','cancel','sendback')),
    seq SMALLINT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_decision_section_seq UNIQUE (section_code, seq)
);

CREATE TABLE external_factors (
    factor_code VARCHAR(30) PRIMARY KEY,
    factor_name VARCHAR(200) NOT NULL, factor_remark VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competitors (
    competitor_code VARCHAR(30) PRIMARY KEY,
    competitor_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ❌ ไม่สร้างตาราง email_templates ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง email_template ของระบบ SBP เดิม (email_template_id · subject_format · body_format) + email_sent

CREATE TABLE status_email_rules (
    status_code VARCHAR(2) NOT NULL REFERENCES document_statuses(status_code),
    template_code VARCHAR(30) NOT NULL REFERENCES email_templates(template_code),
    to_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    cc_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (status_code, template_code)
);

-- ❌ ไม่สร้างตาราง user_accounts ใน SBPGI — ใช้ AWS Cognito + auth-backend — SBPGI รับตัวตนจาก header ของ BFF (ตัดสินใจ 2026-08-05)

-- ❌ ไม่สร้างตาราง system_configs ใน SBPGI (ตัดสินใจ 2026-08-06) — ใช้ตาราง mas_param ของระบบ SBP เดิม (param_name · param_value · ref_name · description · is_config · active_flag)
```

### 5.2 Zone A — Impact Pipeline, Sales and Interface

```sql
CREATE TABLE fgi_impact_processes (
    id BIGSERIAL PRIMARY KEY,
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7) NOT NULL,
    process_status VARCHAR(30) NOT NULL, action_status VARCHAR(30),
    last_compensation_amount NUMERIC(14,2),
    workflow_generation_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (workflow_generation_status IN ('W','Y','N')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_impact_process UNIQUE (impacted_store_code, impact_month)
);

CREATE TABLE fgi_impact_stores (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    new_store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
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
    run_id VARCHAR(50) REFERENCES job_run_histories(run_id),
    data_name VARCHAR(80) NOT NULL, direction VARCHAR(10) NOT NULL CHECK (direction IN ('IN','OUT','INTERNAL')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','SENT','ACKED','COMPLETED','FAILED','FAILED_RETRY')),
    impact_process_id BIGINT REFERENCES fgi_impact_processes(id),
    sales_summary_id BIGINT REFERENCES fgi_impact_sales_summaries(id),
    doc_no VARCHAR(10), business_key VARCHAR(200) NOT NULL, period_key VARCHAR(20) NOT NULL,
    correlation_id VARCHAR(100), file_name VARCHAR(255), file_checksum VARCHAR(64),
    outbox_status VARCHAR(20), return_code VARCHAR(50), return_message VARCHAR(500),
    retry_count INTEGER NOT NULL DEFAULT 0, sent_at TIMESTAMP, acked_at TIMESTAMP,
    purge_after TIMESTAMP, legal_hold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP,
    CONSTRAINT uq_interface_business UNIQUE (data_name, direction, business_key, period_key),
    CONSTRAINT ck_interface_typed_reference CHECK (num_nonnulls(impact_process_id, sales_summary_id, doc_no) >= 1)
);
```

### 5.3 Zone B — Document and Internal Workflow

```sql
CREATE TABLE compensation_documents (
    doc_no VARCHAR(10) PRIMARY KEY,
    year INTEGER NOT NULL, running_no INTEGER NOT NULL,
    impact_process_id BIGINT NOT NULL UNIQUE REFERENCES fgi_impact_processes(id),
    impacted_store_code VARCHAR(5) NOT NULL REFERENCES impacted_stores(store_code),
    impact_month CHAR(7), new_store_code VARCHAR(5) REFERENCES stores(store_code), round_no INTEGER,
    source VARCHAR(20) NOT NULL DEFAULT 'FS' CHECK (source IN ('FS','MANUAL')),
    status_code VARCHAR(2) NOT NULL REFERENCES document_statuses(status_code),
    current_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    total_compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
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
    new_store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
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
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    result VARCHAR(100) NOT NULL, result_category VARCHAR(50), detail TEXT,
    consider_by VARCHAR(30) NOT NULL REFERENCES employees(employee_id),
    action_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, request_id VARCHAR(80)
);

CREATE TABLE document_attachments (
    attach_id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
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
    store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
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
    year SMALLINT PRIMARY KEY,
    last_running_no INTEGER NOT NULL DEFAULT 0 CHECK (last_running_no >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- ออกเลขแบบ atomic: UPDATE document_running_numbers SET last_running_no = last_running_no + 1
--                   WHERE year = :be_year RETURNING last_running_no;   (row lock กันเลขชน)

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

### 5.5 Schema Reference — ตารางที่ **ไม่นับใน 21 ตาราง**

```sql
-- ⚠️ ส่วนนี้ไม่ใช่ขอบเขต migration baseline ของ 21 ตาราง
-- job_configs / job_run_histories ถูกตัดออกจาก target schema เมื่อ 2026-08-06 พร้อมกับ 2 แท็บควบคุมของหน้า Batch Job
-- (cron/พารามิเตอร์อยู่ใน backend config · ผลการรันเขียน application log + interface_transactions)
-- DDL ด้านล่างคงไว้เป็น **schema reference** สำหรับกรณีที่แท็บควบคุมกลับมาในเฟสถัดไป — ห้าม deploy ใน 01_schema.sql

CREATE TABLE job_configs (
    job_no VARCHAR(10) PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    cron_expression VARCHAR(100), enabled BOOLEAN NOT NULL DEFAULT TRUE,
    params_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    secret_ref VARCHAR(255), version_no INTEGER NOT NULL DEFAULT 1,
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_job_config_no_inline_secret CHECK (params_json::text !~* '(password|private_key|client_secret)')
);

CREATE TABLE job_run_histories (
    run_id VARCHAR(50) PRIMARY KEY,
    job_no VARCHAR(10) NOT NULL REFERENCES job_configs(job_no),
    period_key VARCHAR(20), status VARCHAR(20) NOT NULL CHECK (status IN ('QUEUED','RUNNING','WAITING','SUCCESS','FAILED','CANCELLED')),
    trigger_type VARCHAR(20) NOT NULL, triggered_by VARCHAR(30), params_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_count INTEGER NOT NULL DEFAULT 0, success_count INTEGER NOT NULL DEFAULT 0,
    reject_count INTEGER NOT NULL DEFAULT 0, skipped_count INTEGER NOT NULL DEFAULT 0,
    error_code VARCHAR(80), error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, ended_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_job_running ON job_run_histories(job_no, COALESCE(period_key, '')) WHERE status = 'RUNNING';
```

## 6. Index and Constraint Plan

| Table | Index / constraint | Reason |
| --- | --- | --- |
| compensation_documents | UNIQUE (year, running_no), UNIQUE(source, impacted_store_code, impact_month, new_store_code, round_no), INDEX(status_code,current_section_code), INDEX(impact_process_id) | docNo uniqueness, duplicate guard, list/inbox/report, pipeline trace |
| workflow_transaction (@srm/glb-workflow · sps_store) | ปัจจุบัน **ไม่มี PK และไม่มี index เลย** ทั้งที่มี 19,283 แถว (ตรวจ 2026-08-07) — ที่ต้องการคือ PK(transaction_id) + UNIQUE(version_id, reference_id) + INDEX(current_approver) | current approver guard และ inbox · เป็นตารางของ library ไม่ใช่ของ SBPGI จึงต้องขอ sign-off (DP-2 · ยังไม่ตัดสิน) |
| document_new_stores | INDEX(doc_no), CHECK compensate_percent between 0 and 100 | detail load and allocation validation |
| consideration_logs | INDEX(doc_no, action_datetime DESC), INDEX(result_category) | timeline/report result filter |
| document_attachments | INDEX(doc_no), INDEX(scan_status), UNIQUE(sha256, doc_no, deleted_flag) | attachment list/download/security |
| job_run_histories | INDEX(job_no, period, status), UNIQUE(job_no, period) filtered RUNNING | manual run concurrency guard |
| interface_transactions | INDEX(data_name,status), INDEX(impact_process_id), INDEX(doc_no) | tracking and pending ACK |

## 7. Transaction Rules

| Use case | Transaction boundary | Rollback rule |
| --- | --- | --- |
| Create document | docNo sequence lock (document_running_numbers) + compensation_documents + initializeWorkflow/addPreApprover ของ @srm/glb-workflow | any fail rollback all; no partial document · engine อยู่คนละ DataSource จึงต้องมี compensating action เมื่อ commit ฝั่งใดฝั่งหนึ่งไม่ผ่าน |
| Submit action | ตรวจ current_approver จาก workflow_transaction + insert consideration_logs + eventWorkflow (เดิน state) + update compensation_documents | duplicate/current approver conflict returns 409 |
| Attachment upload | metadata insert only after storage write and AV clean; objectKey never exposed | storage/scan fail leaves no CLEAN metadata |
| Job 4 IAS request | durable file (fsync + atomic rename + checksum) ก่อน transaction W→P + outbox READY | file fail คง W; DB fail rollback W→P/outbox; SFTP fail retry transaction เดิม |
| Interface ACK/purge | ACK compare-and-set บน transaction เดิม; purge เฉพาะ terminal + purge_after + non-held | pending/failed/unacked/legal-hold ห้ามลบ |
| Job manual run | acquire run lock + job_run_histories RUNNING before processing | fatal fail marks run FAILED and keeps record-level rejects |
| Master mutation | update entity ใน transaction เดียว | mutation fail ต้อง rollback ครบ |

## 8. Seed Data

| Domain | Required seed |
| --- | --- |
| workflow_state / workflow_status (@srm/glb-workflow) | 5 ขั้น 06, 08, 01, 02, 03 + state จบ flow · 6 สถานะเอกสาร (5 waiting + เสร็จสิ้น) — ลงทะเบียนที่ engine ไม่ใช่ตารางของ SBPGI |
| decisions | ผลพิจารณาทุกปุ่ม (decision_name / flow_name / result_name) |
| competitors | แบรนด์คู่แข่ง 11 รายการ รหัส 01-11 (ไทย + อังกฤษ) |
| external_factors | ปัจจัยภายนอกที่ใช้อยู่ |
| status_email_rules | ผู้รับ TO/CC ต่อสถานะ |
| email_template (ระบบ SBP เดิม) | EM-01..EM-08 |
| common_code / mas_param (ระบบ SBP เดิม) | SBPGI_APPROVE_LIMIT: GM=50000 / AVP=300000 (SDD GI), impact radius 1/2 km, sales data threshold=60, growth rate threshold=-10 |

## 9. Migration and Verification Checklist

| Area | Check |
| --- | --- |
| Naming | all new tables/columns lower_snake_case |
| Leading zero | store_code/new_store_code stored as VARCHAR(5), never numeric |
| docNo | year/running_no/doc_no generated in DB transaction; concurrency test 20 parallel requests |
| Workflow | no active 04/05 accounting sections/statuses; ไม่มีตาราง workflow ของ SBPGI — ตรวจว่า state/route ถูกลงทะเบียนที่ engine ครบ |
| Security | no secrets in mas_param/backend config; storage objectKey not returned to FE |
| External interface | credential/certificate/private key อยู่ Secret Manager ผ่าน secretRef; TLS verify-full หรือ SFTP strict known_hosts; ทดสอบ rotation และ invalid certificate/host key |
| Tracking retention | backfill typed FK/purge_after, validate FK, dry-run count แล้ว purge เฉพาะ ACKED/COMPLETED เป็น batch; reconcile count ก่อน/หลัง |
| Data integrity | FK/check constraints enabled before SIT; reject legacy invalid enum values |
| Performance | list/report/inbox queries explain plan uses indexes above |

## 10. Related LLDD

| Document | DB usage |
| --- | --- |
| LLDD-BE-API-Document-List-Search | workflow_transaction / workflow_approver (@srm/glb-workflow)(R), compensation_documents(R), impacted_stores(R), fgi_impact_sales_summaries(R) |
| LLDD-BE-API-Document-Create-Update | compensation_documents(R/W), workflow_transaction / workflow_approver (@srm/glb-workflow)(W), document_new_stores(R/W), document_competitors(R/W) |
| LLDD-BE-API-Document-Detail-Aggregate | compensation_documents(R), impacted_stores(R), document_new_stores(R), document_competitors(R) |
| LLDD-BE-API-Document-Workflow-Actions | workflow_transaction / workflow_history / workflow_approver (@srm/glb-workflow)(R/W), compensation_documents(W), consideration_logs(W), status_email_rules(R) |
| LLDD-BE-API-Workflow-Instances | fgi_impact_processes / fgi_impact_stores(R/W), compensation_documents(R/W), workflow_transaction (@srm/glb-workflow)(R/W), workflow_approver (@srm/glb-workflow)(W) |
| LLDD-BE-API-Attachment-Sales-Timeline | document_attachments(R/W), compensation_documents(R), fgi_impact_sales_summaries(R), sales_transactions(R) |
| LLDD-BE-API-Lookup | stores / impacted_stores(R), document_statuses / workflow_sections(R), employees(R), roles / menus / menu_permissions(R/W) |
| LLDD-BE-API-Report-and-Master-Data | compensation_documents(R), compensation_histories(R), consideration_logs(R), operator_assignments(R/W) |
| LLDD-BE-Job-Batch-Email-SRM | job_configs(R/W), job_run_histories(R/W), interface_transactions(R/W), email_template (SBP)(R/W) |
| LLDD-BE-Database-Structure | 21 target tables (โซน A/B/C)(W), workflow engine 13 ตาราง (sps_store)(R), fcs_qssi_score (sps_store)(R), mas_param / common_code / business_user / email_template (sps_store)(R) |
| LLDD-BE-Data-Migration-Cutover | ORA FCS_FRN (FGI_IMPACT_* · FCS_QSSI_SCORE · FGI_CONFIRM_RECEIVE_DATA)(R), MSSQL CPA_FRN_FGI (CompensateFlow · CompensateHistory · ImpactProfile · ImpactCostDetail · RunningNumber)(R), 21 target tables (โซน A/B/C)(W), workflow_transaction / workflow_approver / workflow_history (sps_store)(W) |
| LLDD-BE-Integration-SBP-Platform | mas_param (sps_store)(R), common_code / common_code_type (sps_store)(R), email_template / email_sent (sps_store)(R/W), business_user (sps_store)(R) |
| LLDD-BE-Workflow-Engine-Definition | workflow / workflow_version / workflow_state / workflow_status / workflow_event / workflow_route (sps_store)(R/W), workflow_group / workflow_group_map (sps_store)(R/W), workflow_transaction / workflow_history / workflow_approver (sps_store)(R/W), workflow_part / workflow_part_display (sps_store)(R/W) |
| LLDD-BE-Job-1-ImportQSSI | fcs_qssi_score(W) |
| LLDD-BE-Job-2-ImportImpactStore | fgi_impact_stores(W) |
| LLDD-BE-Job-3-ImportImpactCompetitor | fgi_impact_competitors(W) |
| LLDD-BE-Job-4-PrepareImpactStoreToIAS | fgi_impact_stores(R/W), fgi_impact_sales_summaries(R/W), interface_transactions(W), job_run_histories(W) |
| LLDD-BE-Job-5-ImportImpactSaleFromIAS | sales_transactions(W), fgi_impact_sales_summaries(R/W), interface_transactions(W) |
| LLDD-BE-Job-6-ExportImpactStoreToFS | fgi_impact_processes(R/W), fgi_impact_stores(R/W), fcs_qssi_score(R), interface_transactions(W) |
| LLDD-BE-Job-7-SyncCompetitorToDocument | fgi_impact_competitors(R), compensation_documents(R), document_competitors(W), interface_transactions(W) |
| LLDD-BE-Job-8-CreateCompensationDocument | fgi_impact_stores(R/W), fgi_impact_processes(R), compensation_documents(W), interface_transactions(W) |
| LLDD-BE-Job-8b-StartInternalWorkflow | fgi_impact_stores(R/W), compensation_documents(R/W), workflow_instances(W), workflow_tasks(W) |
| LLDD-BE-Job-9-SyncNewStoreToDocument | fgi_impact_stores(R), compensation_documents(R), document_new_stores(W), interface_transactions(W) |
| LLDD-BE-Job-10-NotifyNoReceiveData | interface_transactions(R), email_templates(R), status_email_rules(R) |
