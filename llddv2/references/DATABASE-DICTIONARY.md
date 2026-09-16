# Database Dictionary — 20 ตารางใหม่ + 1 reuse

> Contract status: `CONFIRMED` target · Catalog status: `Verified`

## ต้องทำอะไร และเสร็จแล้วได้อะไร

ตารางนี้กำหนดชื่อ/owner/ผู้อ่าน/ผู้เขียนระดับตาราง คอลัมน์และ constraint ที่ใช้ deploy ต้องยึด generated DDL จาก `tools/build_sgi_schema_sql.py`; catalog นี้ใช้ traceability ไม่ใช้แทน DDL

| # | Table | Zone/owner | Key สำคัญ | Reader | Writer |
|---:|---|---|---|---|---|
| 01 | `sgi_impacted_stores` | C / SGI | `store_code` | Jobs 2/4/8, BE | Job 2/migration |
| 02 | `sgi_external_factors` | C / SGI Master | `code` | BE, Job 8 | BE master |
| 03 | `sgi_competitors` | C / SGI Master | `code` | BE, Jobs 3/7 | BE master/migration |
| 04 | `sgi_fgi_impact_processes` | A / Batch | `id`, store+period | Jobs 2–11 | Jobs 2/5/6/8/8b/11 |
| 05 | `sgi_fgi_impact_compensations` | A / Batch | process+month | Jobs 6/8/8b/11 | Jobs 6/11/migration |
| 06 | `sgi_fgi_impact_stores` | A / Batch | process+new store | Jobs 2/4/6/9 | Jobs 2/4/5/6/11 |
| 07 | `sgi_fgi_new_store_compensations` | A / Batch | impact store+period | Jobs 6/9/11 | Jobs 6/11 |
| 08 | `sgi_fgi_impact_sales_summaries` | A / Batch | process/period | Jobs 4–8b, BE | Jobs 4/5 |
| 09 | `sgi_sales_transactions` | A / Batch | summary+window+seq | Job 5, BE sales | Job 5 |
| 10 | `sgi_fgi_impact_competitors` | A / Batch | process+branch identity | Jobs 3/7 | Job 3 |
| 11 | `sgi_interface_transactions` | A / Integration | message/business key | Jobs 4–11, BE tracking | Jobs/BE outbox+consumer |
| 12 | `sgi_compensation_documents` | B / SGI BE | `id`, `doc_no`, active business key | BE, Jobs 7–12 | BE, Job 8/11 |
| 13 | `sgi_document_new_stores` | B / SGI BE | doc+new store | BE/report | BE, Jobs 9/11 |
| 14 | `sgi_document_competitors` | B / SGI BE | doc+source identity | BE/report | BE, Job 7 |
| 15 | `sgi_document_external_factors` | B / SGI BE | doc+factor | BE/report | BE |
| 16 | `sgi_consideration_logs` | B / SGI BE | doc+transaction/time | BE/report/timeline | BE action |
| 17 | `sgi_document_attachments` | B / SGI BE | id+doc | BE | BE attachment/scan |
| 18 | `sgi_compensation_histories` | B / SGI BE | doc+period/version | BE/report | BE/Job 11 |
| 19 | `sgi_document_cost_details` | B / SGI BE | doc+cost period/type | BE/report | BE/pipeline |
| 20 | `sgi_document_running_numbers` | B / SGI BE | year | Job 8/BE | Job 8/BE under lock |
| 21 | `fcs_qssi_score` | reuse / SBP existing | store/category/month/year | Job 6 | owner เดิมเท่านั้น |

## Canonical columns

รายการนี้ต้องตรงกับ DDL ปัจจุบันทุกชื่อ; ชนิดข้อมูล, nullability, default, CHECK, FK และ index ให้เปิด generated DDL ก่อนเขียน migration

| Table | Columns |
|---|---|
| `sgi_impacted_stores` | `store_code`, `dv_code`, `opt_dv_user_id`, `latitude`, `longitude`, `transfer_sbp_date`, `is_active`, `updated_at` |
| `sgi_external_factors` | `factor_code`, `factor_name`, `factor_remark`, `is_active`, `updated_at` |
| `sgi_competitors` | `competitor_code`, `name_th`, `name_en`, `remark`, `is_active`, `updated_at` |
| `sgi_fgi_impact_processes` | `id`, `impacted_store_code`, `impact_month`, `impact_year`, `process_status`, `action_status`, `last_compensation_amount`, `workflow_generation_status`, `last_compensate_seq`, `last_compensate_seq_no`, `start_compensate_month`, `start_compensate_year`, `end_compensate_month`, `end_compensate_year`, `flag_action`, `datasource`, `created_at`, `updated_by`, `updated_at` |
| `sgi_fgi_impact_compensations` | `id`, `impact_process_id`, `impacted_store_code`, `compensate_seq`, `compensate_seq_no`, `compensate_month`, `compensate_year`, `forecast_amount`, `adjust_amount`, `compensate_status`, `compensate_comment`, `stmt_month`, `stmt_year`, `approve_date`, `created_by`, `created_at`, `updated_by`, `updated_at` |
| `sgi_fgi_impact_stores` | `id`, `impact_process_id`, `impacted_store_code`, `new_store_code`, `impact_month`, `distance_km`, `verify_status`, `created_by`, `updated_by`, `created_at`, `sales_request_status`, `forecast_compensate_percent`, `adjust_compensate_percent`, `forecast_compensation_amount`, `adjust_compensation_amount`, `updated_at` |
| `sgi_fgi_new_store_compensations` | `id`, `impact_compensation_id`, `impact_store_id`, `new_store_code`, `forecast_amount`, `forecast_percent`, `adjust_amount`, `adjust_percent`, `created_by`, `created_at`, `updated_by`, `updated_at` |
| `sgi_fgi_impact_sales_summaries` | `id`, `impact_process_id`, `total_working_days`, `growth_rate_before`, `growth_rate_after`, `growth_rate_diff`, `sales_status`, `updated_by`, `updated_at` |
| `sgi_sales_transactions` | `id`, `sales_summary_id`, `txn_date`, `window_no`, `seq`, `sales_amount`, `sales_diff`, `is_outlier`, `source_checksum`, `created_at` |
| `sgi_fgi_impact_competitors` | `id`, `impact_process_id`, `competitor_store_code`, `brand_code`, `name_th`, `name_en`, `branch_th`, `zone_code`, `subzone_code`, `opened_date`, `closed_date`, `period_key`, `updated_at`, `competitor_key` |
| `sgi_interface_transactions` | `id`, `run_id`, `data_name`, `direction`, `status`, `impact_process_id`, `sales_summary_id`, `doc_no`, `business_key`, `period_key`, `correlation_id`, `file_name`, `file_checksum`, `outbox_status`, `return_code`, `return_message`, `payload`, `payload_version`, `retry_count`, `sent_at`, `acked_at`, `last_ack_notified_on`, `purge_after`, `legal_hold`, `created_at`, `completed_at` |
| `sgi_compensation_documents` | `id`, `doc_no`, `year`, `running_no`, `impact_process_id`, `impact_compensation_id`, `impacted_store_code`, `impact_month`, `new_store_code`, `round_no`, `loop_no`, `source`, `status_code`, `current_section_code`, `total_compensation_amount`, `allmap_url`, `statement_id`, `statement_date`, `account_year`, `account_month`, `approver_snapshot`, `version_no`, `created_by`, `created_at`, `updated_by`, `updated_at` |
| `sgi_document_new_stores` | `id`, `doc_no`, `new_store_code`, `distance_km`, `compensate_percent`, `compensation_amount`, `source_system`, `source_row_id`, `updated_at` |
| `sgi_document_competitors` | `id`, `doc_no`, `competitor_store_code`, `brand_code`, `name_th`, `name_en`, `branch_th`, `zone_code`, `subzone_code`, `opened_date`, `closed_date`, `impact_date`, `detail`, `remark`, `source_system`, `source_row_id`, `updated_at`, `competitor_key` |
| `sgi_document_external_factors` | `id`, `doc_no`, `factor_code`, `date_from`, `date_to`, `detail`, `remark`, `updated_at` |
| `sgi_consideration_logs` | `id`, `doc_no`, `section_code`, `result`, `result_category`, `detail`, `consider_by`, `action_datetime`, `request_id` |
| `sgi_document_attachments` | `attach_id`, `doc_no`, `section_code`, `file_name`, `mime_type`, `file_size`, `storage_provider`, `bucket`, `object_key`, `sha256`, `scan_status`, `scanned_at`, `scan_message`, `uploaded_by`, `uploaded_at`, `deleted_flag` |
| `sgi_compensation_histories` | `id`, `store_code`, `ref_doc_no`, `submit_account_month`, `compensate_amount`, `accounting_status`, `external_ref`, `created_at` |
| `sgi_document_cost_details` | `id`, `doc_no`, `new_store_code`, `cost_year`, `cost_month`, `cost_target_n`, `cost_amount_n`, `cost_target_nc`, `cost_amount_nc`, `created_at` |
| `sgi_document_running_numbers` | `year`, `last_running_no`, `updated_by`, `updated_at` |
| `fcs_qssi_score` | `id`, `store_id`, `category`, `month`, `year`, `score`, `create_date` — existing table, read-only for SGI |

## Shared existing objects (ไม่นับใน 21)

`mas_store`, `fr_store`, `juristic`, `mas_zone`, `seven_shop`/store views, `common_code`, `common_code_type`, `mas_param`, `email_template`, `email_sent`, `business_user`, `business_user_group` และ workflow 13 ตาราง SGI ต้องใช้ชื่อ/column จาก schema dump จริงและสิทธิ์เท่าที่จำเป็น

## Ownership rules

- Batch/BE ห้ามสร้าง shadow master ของ auth/menu/store/workflow/email
- SGI ห้าม DML `workflow_*` และ `fcs_qssi_score`
- source snapshot กับ live master ต้องระบุชัดใน field mapping; ห้าม join live master แล้วอ้างว่าเป็น historical snapshot
- ทุกตารางที่เก็บบุคคล/ที่อยู่/ความคิดเห็นต้องมี access, masking และ retention review

## Count invariant

Canonical = `20 CREATE TABLE` ใน DDL + `fcs_qssi_score` reuse = 21 ตาราง หากเปลี่ยนจำนวนต้องแก้ database source, migration generator, API/Job mapping, checklist และ Decision Register พร้อมกัน
