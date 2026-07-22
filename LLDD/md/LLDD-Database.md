# LLDD Database - Target Schema and Data Dictionary

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารนี้เป็น LLDD Database ระดับรวมของ target schema ระบบ SBPGI/SBP Mall ใช้เป็น reference สำหรับ BE API, Batch Job, migration, indexing, transaction และ data dictionary

## 2. Architecture Context

- ระบบใหม่รวม EAI และ K2 เข้าเป็น SBPGI ใช้ฐานข้อมูลเดียวกัน
- ไม่มีไฟล์ BPM06001O/BPM06002O/BPM06003O ภายในเพื่อส่งเข้า K2; ใช้ FK จาก compensation_documents ไป impact_process แทน
- Workflow engine ภายในใช้ workflow_instances และ workflow_tasks แทน K2 engine ภายนอก
- ตัดขั้นบัญชี 04/05 ตาม SDD v7.5; workflow ใช้ section 06/08/01/02/03
- มาตรฐานชื่อ table/column เป็น English lower_snake_case
- ตาราง job_configs และ job_run_histories เป็น schema reference สำหรับ BE/dev; ไม่ใช่ scope ให้ FE Batch Monitor ทำ tab Database ที่ใช้

## 2.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | Target table catalog, data zones, primary keys, foreign-key relationships, migration assumptions, index needs, and transaction boundaries. |
| Progress | Use the data spine impact_process_id -> doc_no -> instance_id/task_id to implement APIs/jobs, then validate referential integrity, idempotency keys, and audit writes. |
| Output | Data dictionary and implementation reference for schema creation, migration, indexing, transaction handling, and test data preparation. |

## 3. Data Zones and Spine

| Zone | Scope | Core tables | Owner usage |
| --- | --- | --- | --- |
| A | FGI/FCS Impact Pipeline and external interfaces | fgi_impact_processes, fgi_impact_stores, sales, interface_transactions | Batch Jobs 1-7, IAS/ALLMAP/QSSI/STA tracking |
| B | K2 Document and internal workflow | compensation_documents, document_* tables, workflow_instances, workflow_tasks | Document APIs, workflow actions, FE detail/list/report |
| C | Shared master/config/RBAC/audit | stores, roles, menus, configs, jobs, email templates, audit | Lookup, admin, job monitor, notification |

| Order | Key | Meaning | Used by |
| --- | --- | --- | --- |
| 1 | impact_process_id | หนึ่งร้านถูกกระทบ + หนึ่งงวด | FGI/FCS pipeline, Job 8/8b |
| 2 | doc_no | เอกสาร YYYY/xxxxx ปี พ.ศ. | Document APIs, reports, attachments |
| 3 | instance_id | workflow instance ต่อเอกสาร | Workflow engine |
| 4 | task_id | งานต่อ section/assignee | Inbox/current task guard |
| 5 | employee_id / role_code | identity/RBAC | menu, audit, assignment |

## 4. Data Dictionary

| Zone | Table | PK | FK / relationship | Role |
| --- | --- | --- | --- | --- |
| A | fgi_impact_stores | id | impact_process_id, impacted_store_code | impact pair; sales request and allocation data |
| A | fgi_impact_processes | id | impacted_store_code | impact process hub and canonical workflow_generation_status |
| A | fgi_impact_sales_summaries | id | impact_process_id | sales summary/growth rate |
| A | sales_transactions | id | sales_summary_id | daily sales 4 windows x 15 days |
| A | fgi_impact_competitors | id | impact_process_id | ALLMAP competitors |
| A | fcs_qssi_scores | id | store_id + category_code + period | QSSI scores |
| A | interface_transactions | id | impact_process_id/sales_summary_id/doc_no | interface tracking replacement |
| B | compensation_documents | doc_no | impact_process_id, status_code, current_section_code | document header/core |
| B | document_new_stores | id | doc_no, new_store_code | new stores and compensate percent |
| B | document_competitors | id | doc_no, competitor_code | document competitors |
| B | document_external_factors | id | doc_no, factor_code | document external factors |
| B | consideration_logs | id | doc_no | approval/action history |
| B | document_attachments | attach_id | doc_no | attachment metadata and storage pointer |
| B | compensation_histories | id | store_code, ref_doc_no | compensation history/accounting export |
| B | workflow_instances | instance_id | doc_no | internal workflow instance |
| B | workflow_tasks | task_id | instance_id, section_code, assignee_employee_id | current/past tasks |
| C | stores | store_code | - | all 7-Eleven stores |
| C | impacted_stores | store_code | stores.store_code | SP impacted store subset |
| C | workflow_sections | section_code | - | workflow sections 06/08/01/02/03 |
| C | document_statuses | status_code | - | document status dictionary |
| C | roles | role_code | - | RBAC roles 00-10 |
| C | menus | menu_code | - | menu registry |
| C | menu_permissions | role_code + menu_code | roles, menus | RBAC matrix |
| C | operator_assignments | id | section_code, employee_id | operator by section/zone |
| C | employees | employee_id | - | HR employee master |
| C | external_factors | factor_code | - | external factor master |
| C | competitors | competitor_code | - | competitor master |
| C | audit_logs | id | table_name + ref_key | master/config/email audit |
| C | status_email_rules | status_code | workflow_sections | notification recipients |
| C | email_templates | template_code | - | notification templates |
| C | user_accounts | employee_id | role_code | user account/JWT role |
| C | job_configs | job_no | - | schema reference for batch schedule/config; not FE Database tab scope |
| C | job_run_histories | run_id | job_no | job execution history |
| C | system_configs | config_key | - | global config key-value |

### 4.1 Canonical Column Contract

| Table | Canonical columns used by DDL and SQL | Rejected legacy vocabulary |
| --- | --- | --- |
| menu_permissions | role_code, menu_code, can_access | can_view/can_create/can_update/can_delete |
| user_accounts | employee_id, role_code, section_code, username, is_active | password_hash/account_status |
| workflow_instances | instance_id, doc_no, instance_status, started_at, started_by | status or auto-generated instance id |
| system_configs | config_key, category, config_value, value_type, unit, description, is_editable | secret_flag or inline secrets |
| sales_transactions | txn_date, window_no, sales_amount, sales_diff, is_outlier | sale_date/window_code/net_sales |
| consideration_logs | result, result_category, detail, consider_by, action_datetime | result_code/comment/considered_by/considered_at |
| interface_transactions | id, acked_at | tracking_id/receive_date (API aliases only) |
| fgi_impact_processes | workflow_generation_status | duplicate workflow flag on fgi_impact_stores |

## 5. Executable DDL — 34 Tables

ส่วนนี้เป็น PostgreSQL DDL ครบทุกตารางใน Data Dictionary เรียงตาม dependency พร้อม PK, typed FK, unique/check constraint และ index ที่จำเป็น สามารถใช้เป็น migration baseline ได้โดยไม่ต้องเดา column เพิ่มเติม

### 5.1 Zone C — Shared Master, RBAC, Config and Operations

```sql
CREATE TABLE stores (
    store_code VARCHAR(5) PRIMARY KEY,
    store_name VARCHAR(200) NOT NULL, juristic_name VARCHAR(200), store_type VARCHAR(30),
    region_code VARCHAR(10), zone_code VARCHAR(10), branch_type VARCHAR(10),
    opened_date DATE, closed_date DATE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE impacted_stores (
    store_code VARCHAR(5) PRIMARY KEY REFERENCES stores(store_code),
    dv_code VARCHAR(20), opt_dv_user_id VARCHAR(30), latitude NUMERIC(10,7), longitude NUMERIC(10,7),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workflow_sections (
    section_code VARCHAR(2) PRIMARY KEY,
    section_name VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE document_statuses (
    status_code VARCHAR(2) PRIMARY KEY,
    status_name VARCHAR(200) NOT NULL,
    section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    sort_order INTEGER NOT NULL UNIQUE,
    terminal_flag BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE roles (
    role_code VARCHAR(10) PRIMARY KEY,
    role_name VARCHAR(200) NOT NULL, role_desc VARCHAR(500),
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE menus (
    menu_code VARCHAR(50) PRIMARY KEY,
    menu_name VARCHAR(200) NOT NULL, menu_group VARCHAR(100),
    route_path VARCHAR(255), sort_order INTEGER NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE menu_permissions (
    role_code VARCHAR(10) NOT NULL REFERENCES roles(role_code),
    menu_code VARCHAR(50) NOT NULL REFERENCES menus(menu_code),
    can_access BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (role_code, menu_code)
);

CREATE TABLE employees (
    employee_id VARCHAR(30) PRIMARY KEY,
    emp_name VARCHAR(200) NOT NULL,
    emp_mail VARCHAR(255), department VARCHAR(150), zone_code VARCHAR(10), dv_code VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE impacted_stores
    ADD CONSTRAINT fk_impacted_store_opt_dv FOREIGN KEY (opt_dv_user_id) REFERENCES employees(employee_id);

CREATE TABLE operator_assignments (
    id BIGSERIAL PRIMARY KEY,
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    employee_id VARCHAR(30) NOT NULL REFERENCES employees(employee_id),
    emp_name VARCHAR(200) NOT NULL, emp_mail VARCHAR(255), zone_code VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_operator_scope UNIQUE (section_code, employee_id, zone_code)
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

CREATE TABLE email_templates (
    template_code VARCHAR(30) PRIMARY KEY,
    name VARCHAR(200) NOT NULL, subject VARCHAR(500) NOT NULL, body TEXT NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_subject VARCHAR(500), default_body TEXT,
    is_customized BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_email_rules (
    status_code VARCHAR(2) NOT NULL REFERENCES document_statuses(status_code),
    template_code VARCHAR(30) NOT NULL REFERENCES email_templates(template_code),
    to_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    cc_section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (status_code, template_code)
);

CREATE TABLE user_accounts (
    employee_id VARCHAR(30) PRIMARY KEY REFERENCES employees(employee_id),
    role_code VARCHAR(10) NOT NULL REFERENCES roles(role_code),
    section_code VARCHAR(2) REFERENCES workflow_sections(section_code),
    username VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL, ref_key VARCHAR(200) NOT NULL,
    action_type VARCHAR(80) NOT NULL, old_value JSONB, new_value JSONB,
    reason VARCHAR(500), request_id VARCHAR(80), updated_by VARCHAR(30) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_configs (
    config_key VARCHAR(150) PRIMARY KEY,
    category VARCHAR(80) NOT NULL, config_value TEXT NOT NULL, value_type VARCHAR(30) NOT NULL,
    unit VARCHAR(30), description VARCHAR(500), is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_system_config_no_secret CHECK (config_key !~* '(password|private_key|client_secret|token)')
);
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
    verify_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (verify_status IN ('W','P','Y','N')),
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

CREATE TABLE fcs_qssi_scores (
    id BIGSERIAL PRIMARY KEY,
    store_code VARCHAR(5) NOT NULL REFERENCES stores(store_code),
    category_code VARCHAR(30) NOT NULL, score_period CHAR(7) NOT NULL,
    score_value NUMERIC(10,4) NOT NULL, source_file_name VARCHAR(255), source_checksum VARCHAR(64),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_qssi_score UNIQUE (store_code, category_code, score_period)
);

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
    be_year INTEGER NOT NULL, running_no INTEGER NOT NULL,
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
    CONSTRAINT uq_comp_be_year_running UNIQUE (be_year, running_no),
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

CREATE TABLE workflow_instances (
    instance_id VARCHAR(40) PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL UNIQUE REFERENCES compensation_documents(doc_no),
    instance_status VARCHAR(20) NOT NULL CHECK (instance_status IN ('ACTIVE','COMPLETED','CANCELLED')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, started_by VARCHAR(30) NOT NULL,
    completed_at TIMESTAMP
);

CREATE TABLE workflow_tasks (
    task_id BIGSERIAL PRIMARY KEY,
    instance_id VARCHAR(40) NOT NULL REFERENCES workflow_instances(instance_id),
    doc_no VARCHAR(10) NOT NULL REFERENCES compensation_documents(doc_no),
    section_code VARCHAR(2) NOT NULL REFERENCES workflow_sections(section_code),
    assignee_employee_id VARCHAR(30) REFERENCES employees(employee_id),
    task_status VARCHAR(20) NOT NULL CHECK (task_status IN ('OPEN','DONE','CANCELLED')),
    action_result TEXT, opened_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, closed_at TIMESTAMP
);
```

### 5.4 Required Indexes, Partial Uniqueness and Purge

```sql
CREATE INDEX idx_document_status_section ON compensation_documents(status_code, current_section_code);
CREATE INDEX idx_document_impact_process ON compensation_documents(impact_process_id);
CREATE INDEX idx_task_doc_status ON workflow_tasks(doc_no, task_status);
CREATE UNIQUE INDEX uq_task_one_open_section ON workflow_tasks(instance_id, section_code) WHERE task_status = 'OPEN';
CREATE INDEX idx_consideration_timeline ON consideration_logs(doc_no, action_datetime DESC);
CREATE INDEX idx_interface_pending ON interface_transactions(data_name, status, sent_at);
CREATE INDEX idx_interface_impact_process ON interface_transactions(impact_process_id);
CREATE INDEX idx_interface_sales_summary ON interface_transactions(sales_summary_id);
CREATE INDEX idx_interface_doc ON interface_transactions(doc_no);
CREATE UNIQUE INDEX uq_job_running ON job_run_histories(job_no, COALESCE(period_key, '')) WHERE status = 'RUNNING';
CREATE INDEX idx_audit_ref ON audit_logs(table_name, ref_key, updated_at DESC);

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
| compensation_documents | UNIQUE (be_year, running_no), UNIQUE(source, impacted_store_code, impact_month, new_store_code, round_no), INDEX(status_code,current_section_code), INDEX(impact_process_id) | docNo uniqueness, duplicate guard, list/inbox/report, pipeline trace |
| workflow_tasks | INDEX(doc_no, task_status), INDEX(section_code, task_status), UNIQUE(instance_id, section_code, task_status) filtered OPEN | current task guard and inbox |
| document_new_stores | INDEX(doc_no), CHECK compensate_percent between 0 and 100 | detail load and allocation validation |
| consideration_logs | INDEX(doc_no, action_datetime DESC), INDEX(result_category) | timeline/report result filter |
| document_attachments | INDEX(doc_no), INDEX(scan_status), UNIQUE(sha256, doc_no, deleted_flag) | attachment list/download/security |
| job_run_histories | INDEX(job_no, period, status), UNIQUE(job_no, period) filtered RUNNING | manual run concurrency guard |
| audit_logs | INDEX(table_name, ref_key), INDEX(updated_at DESC) | admin history search |
| interface_transactions | INDEX(data_name,status), INDEX(impact_process_id), INDEX(doc_no) | tracking and pending ACK |

## 7. Transaction Rules

| Use case | Transaction boundary | Rollback rule |
| --- | --- | --- |
| Create document | docNo sequence lock + compensation_documents + workflow instance/task + audit | any fail rollback all; no partial document |
| Submit action | lock current OPEN task + insert consideration_logs + close/open task + update document | duplicate/current task conflict returns 409 |
| Attachment upload | metadata insert only after storage write and AV clean; objectKey never exposed | storage/scan fail leaves no CLEAN metadata |
| Job 4 IAS request | durable file (fsync + atomic rename + checksum) ก่อน transaction W→P + outbox READY | file fail คง W; DB fail rollback W→P/outbox; SFTP fail retry transaction เดิม |
| Interface ACK/purge | ACK compare-and-set บน transaction เดิม; purge เฉพาะ terminal + purge_after + non-held | pending/failed/unacked/legal-hold ห้ามลบ |
| Job manual run | acquire run lock + job_run_histories RUNNING before processing | fatal fail marks run FAILED and keeps record-level rejects |
| Master/config/email mutation | validate reason + update entity + insert audit_logs | audit fail rollback mutation |

## 8. Seed Data

| Domain | Required seed |
| --- | --- |
| workflow_sections | 06, 08, 01, 02, 03 only |
| document_statuses | 6 statuses: 5 waiting statuses + completed |
| roles | 00, 01, 02, 03, 04, 05, 06, 10 per RBAC model |
| email_templates | EM-01..EM-08 |
| system_configs | impact radius 1/2 km, workflow.avp_amount_threshold=100000, sales data threshold=60, growth rate threshold=-10 |
| job_configs | Jobs 1-10 and 8b with enabled/schedule/default params as schema reference |

## 9. Migration and Verification Checklist

| Area | Check |
| --- | --- |
| Naming | all new tables/columns lower_snake_case |
| Leading zero | store_code/new_store_code stored as VARCHAR(5), never numeric |
| docNo | be_year/running_no/doc_no generated in DB transaction; concurrency test 20 parallel requests |
| Workflow | no active 04/05 accounting sections/statuses |
| Security | no secrets in system_configs/job_configs; storage objectKey not returned to FE |
| External interface | credential/certificate/private key อยู่ Secret Manager ผ่าน secretRef; TLS verify-full หรือ SFTP strict known_hosts; ทดสอบ rotation และ invalid certificate/host key |
| Tracking retention | backfill typed FK/purge_after, validate FK, dry-run count แล้ว purge เฉพาะ ACKED/COMPLETED เป็น batch; reconcile count ก่อน/หลัง |
| Data integrity | FK/check constraints enabled before SIT; reject legacy invalid enum values |
| Performance | list/report/inbox queries explain plan uses indexes above |

## 10. Related LLDD

| Document | DB usage |
| --- | --- |
| LLDD-BE-API-Dashboard-Summary | workflow_tasks(R), compensation_documents(R), compensation_histories(R), fgi_impact_sales_summaries(R) |
| LLDD-BE-API-Document-List-Search | workflow_tasks(R), compensation_documents(R), impacted_stores(R), fgi_impact_sales_summaries(R) |
| LLDD-BE-API-Document-Create-Update | compensation_documents(R/W), workflow_instances / workflow_tasks(W), document_new_stores(R/W), document_competitors(R/W) |
| LLDD-BE-API-Document-Detail-Aggregate | compensation_documents(R), impacted_stores(R), document_new_stores(R), document_competitors(R) |
| LLDD-BE-API-Document-Workflow-Actions | workflow_tasks(R/W), compensation_documents(W), consideration_logs(W), status_email_rules(R) |
| LLDD-BE-API-Workflow-Instances | fgi_impact_processes / fgi_impact_stores(R/W), compensation_documents(R/W), workflow_instances(R/W), workflow_tasks(W) |
| LLDD-BE-API-Attachment-Sales-Timeline | document_attachments(R/W), compensation_documents(R), fgi_impact_sales_summaries(R), sales_transactions(R) |
| LLDD-BE-API-Lookup-RBAC-Email | stores / impacted_stores(R), document_statuses / workflow_sections(R), employees(R), roles / menus / menu_permissions(R/W) |
| LLDD-BE-API-Report-Master-Config | compensation_documents(R), compensation_histories(R), consideration_logs(R), operator_assignments(R/W) |
| LLDD-BE-Job-Batch-Email-SRM | job_configs(R/W), job_run_histories(R/W), interface_transactions(R/W), email_templates(R/W) |
| LLDD-BE-Job-1-ImportQSSI | fcs_qssi_scores(W) |
| LLDD-BE-Job-2-ImportImpactStore | fgi_impact_stores(W) |
| LLDD-BE-Job-3-ImportImpactCompetitor | fgi_impact_competitors(W) |
| LLDD-BE-Job-4-PrepareImpactStoreToIAS | fgi_impact_stores(R/W), fgi_impact_sales_summaries(R/W), interface_transactions(W), job_run_histories(W) |
| LLDD-BE-Job-5-ImportImpactSaleFromIAS | sales_transactions(W), fgi_impact_sales_summaries(R/W), interface_transactions(W) |
| LLDD-BE-Job-6-ExportImpactStoreToFS | fgi_impact_processes(R/W), fgi_impact_stores(R/W), fcs_qssi_scores(R), interface_transactions(W) |
| LLDD-BE-Job-7-SyncCompetitorToDocument | fgi_impact_competitors(R), compensation_documents(R), document_competitors(W), interface_transactions(W) |
| LLDD-BE-Job-8-CreateCompensationDocument | fgi_impact_stores(R/W), fgi_impact_processes(R), compensation_documents(W), interface_transactions(W) |
| LLDD-BE-Job-8b-StartInternalWorkflow | fgi_impact_stores(R/W), compensation_documents(R/W), workflow_instances(W), workflow_tasks(W) |
| LLDD-BE-Job-9-SyncNewStoreToDocument | fgi_impact_stores(R), compensation_documents(R), document_new_stores(W), interface_transactions(W) |
| LLDD-BE-Job-10-NotifyNoReceiveData | interface_transactions(R), email_templates(R), status_email_rules(R) |
