# ฐานข้อมูลจริง — schema `sps_store` (SBP Mall Dev)

> ดึงจากฐานข้อมูลจริงเมื่อ **07/08/2026** ด้วยบัญชี read-only ของ schema `sps_store`
> Host `srm-sps-spsap-postgres-instance-dev-new-instance-{writer|reader}.cxsegsg200gm.ap-southeast-1.rds.amazonaws.com` · port `5432` · database `postgres` · **PostgreSQL 17.7**
> **เอกสารนี้ไม่มี credential** — username/password อยู่กับผู้ดูแลระบบเท่านั้น

schema หลักของ **store-backend** (`srm-sps-spsap-store-backend`) — เก็บข้อมูลร้าน ใบแจ้งยอด การประเมินร้าน สัญญา และงาน interface ทั้งหมด
เป็น schema เดียวกับที่ **ระบบประกันรายได้ (SBPGI) จะเข้าไปสร้างตารางของตัวเองและใช้ตารางเดิมร่วม** ตามมติ 2026-08-06

**สรุป:** 198 ตาราง · 3061 คอลัมน์ · 7 foreign key · 223 index · 2 view

## ตารางที่ระบบประกันรายได้ (SBPGI) ตัดสินใจใช้ร่วม

| ตาราง | บทบาทใน SBPGI | คอลัมน์ | แถว (ประมาณ) |
|---|---|---|---|
| [`business_user`](#business-user) | ผู้ใช้/ผู้อนุมัติ | 36 | 12,752 |
| [`common_code`](#common-code) | lookup ทั่วไป (+ วงเงินอนุมัติ SBPGI_APPROVE_LIMIT) | 14 | 2,609 |
| [`email_sent`](#email-sent) | log การส่งอีเมล | 12 | 5,214 |
| [`email_template`](#email-template) | template อีเมล (แทน email_templates) | 12 | 85 |
| [`fcs_audit_costs`](#fcs-audit-costs) | ต้นทุนตรวจนับ | 6 | 711,384 |
| [`fcs_monthly_sales`](#fcs-monthly-sales) | ยอดขายรายเดือน | 12 | 711,384 |
| [`fcs_qssi_score`](#fcs-qssi-score) | คะแนน QSSI 6 หมวด | 7 | 23,958,780 |
| [`integration_log`](#integration-log) | log payload ราย call | 6 | 518 |
| [`mas_param`](#mas-param) | ค่ากำหนดกลาง (แทน system_configs) | 10 | 93,752 |
| [`mas_store`](#mas-store) | master ร้าน | 31 | 19,647 |
| [`mas_zone`](#mas-zone) | ภาค/โซน | 5 | 28 |
| [`sevenshop`](#sevenshop) | สาขา 7-Eleven | 56 | 15,308 |
| [`store`](#store) | ค้นหา/รายละเอียดร้าน | 32 | 19,402 |
| [`upload_general`](#upload-general) | ไฟล์แนบ generic | 11 | 235 |

## ดัชนีตารางทั้งหมด

| ตาราง | คอลัมน์ | PK | FK | แถว (ประมาณ) | หมายเหตุ |
|---|---|---|---|---|---|
| `actions` | 4 | — | 0 | -1 |  |
| `amphur` | 3 | — | 0 | 997 |  |
| `assistant_manager_assignments` | 13 | id | 0 | 14 |  |
| `bck_business_user` | 36 | — | 0 | 24,336 |  |
| `bck_mas_store_organize` | 19 | — | 0 | 120,000 |  |
| `bellinee_store` | 50 | — | 0 | 254 |  |
| `bellinee_store_organize` | 49 | branch_id | 0 | 264 |  |
| `business_group` | 11 | group_id | 0 | 126 |  |
| `business_user` | 36 | — | 0 | 12,752 | **ใช้ใน SBPGI** |
| `business_user_group` | 14 | — | 0 | 11,409 |  |
| `cancel_contract_store_approve` | 10 | order_id | 0 | -1 |  |
| `common_code` | 14 | — | 0 | 2,609 | **ใช้ใน SBPGI** |
| `common_code_type` | 9 | code_type | 0 | 376 |  |
| `common_log` | 8 | id | 0 | 6 |  |
| `email_sent` | 12 | email_sent_id | 0 | 5,214 | **ใช้ใน SBPGI** |
| `email_template` | 12 | email_template_id | 0 | 85 | **ใช้ใน SBPGI** |
| `fcs_audit_costs` | 6 | id | 0 | 711,384 | **ใช้ใน SBPGI** |
| `fcs_content` | 21 | content_id | 0 | 8,571 |  |
| `fcs_file_content` | 10 | file_id | 0 | 3,367 |  |
| `fcs_file_mapping` | 10 | file_mapping_id | 0 | 22,314 |  |
| `fcs_monthly_sales` | 12 | id | 0 | 711,384 | **ใช้ใน SBPGI** |
| `fcs_qssi_score` | 7 | id | 0 | 23,958,780 | **ใช้ใน SBPGI** |
| `fcs_qssi_score_bak_20260710` | 7 | — | 0 | 18,577,924 |  |
| `fcs_reminder_log` | 10 | — | 0 | 695,653 |  |
| `fcs_tmp_qssi_score` | 8 | — | 0 | 0 |  |
| `fes_adjust_grade` | 10 | — | 0 | 128,805 |  |
| `fes_adjust_grade_bak_20260710` | 10 | — | 0 | 1,402 |  |
| `fes_bank_account` | 6 | — | 0 | 14,079 |  |
| `fes_copylvthree` | 5 | copylvthree_id | 0 | 7,227,231 |  |
| `fes_copylvthree_bak_20260710` | 5 | — | 0 | 550 |  |
| `fes_copylvtwo` | 5 | copylvtwo_id | 0 | 685,085 |  |
| `fes_copylvtwo_bak_20260710` | 5 | — | 0 | 587,997 |  |
| `fes_evallevelone` | 6 | — | 0 | 15 |  |
| `fes_evallevelone_bak_20260710` | 6 | — | 0 | -1 |  |
| `fes_evallevelthree` | 11 | evallevelthree_id | 0 | 165 |  |
| `fes_evallevelthree_bak_20260710` | 11 | — | 0 | 104 |  |
| `fes_evalleveltwo` | 10 | evalleveltwo_id | 0 | 39 |  |
| `fes_evalleveltwo_bak_20260710` | 10 | — | 0 | -1 |  |
| `fes_evalperson` | 4 | — | 0 | 44 |  |
| `fes_evalperson_bak_20260710` | 4 | — | 0 | -1 |  |
| `fes_evalpersonthree` | 4 | — | 0 | 16 |  |
| `fes_evalpersonthree_bak_20260710` | 4 | — | 0 | -1 |  |
| `fes_evaltype` | 3 | — | 0 | 184 |  |
| `fes_evaluate` | 25 | evaluate_id | 0 | 203,884 |  |
| `fes_evaluate_bak_20260710` | 25 | — | 0 | 176,368 |  |
| `fes_evaluate_hint_levelone` | 4 | eval_id,eval_level,seq | 0 | 117 |  |
| `fes_evaluate_hint_levelone_bak_20260710` | 4 | — | 0 | 117 |  |
| `fes_evaluate_hint_leveltwo` | 5 | eval_id,seq,sub_seq | 0 | 321 |  |
| `fes_evaluate_hint_leveltwo_bak_20260710` | 5 | — | 0 | 321 |  |
| `fes_evaluate_opt` | 10 | — | 0 | 166,804 |  |
| `fes_evaluate_opt_bak_20260710` | 10 | — | 0 | 146,839 |  |
| `fes_evaluatedform` | 10 | evaluatedform_id | 0 | -1 |  |
| `fes_evaluatedform_bak_20260710` | 10 | — | 0 | -1 |  |
| `fes_evaluatedform_title` | 6 | — | 0 | 41 |  |
| `fes_evaluatedform_title_bak_20260710` | 6 | — | 0 | -1 |  |
| `fes_evaluatedperson` | 16 | — | 0 | 1,660,005 |  |
| `fes_evaluatedperson_bak_20260710` | 16 | — | 0 | 674 |  |
| `fes_grade` | 9 | grade_id | 0 | -1 |  |
| `fes_grade_bak_20260710` | 9 | — | 0 | -1 |  |
| `fes_gradedetail` | 8 | gradedetail_id | 1 | -1 |  |
| `fes_gradedetail_bak_20260710` | 6 | — | 0 | -1 |  |
| `fes_importdata` | 16 | — | 0 | 62,712 |  |
| `fes_importdata_bak_20260710` | 16 | — | 0 | 12,096,393 |  |
| `fes_properties` | 3 | — | 0 | -1 |  |
| `fes_reward` | 35 | — | 0 | 59,325 |  |
| `fes_reward_bak_20260710` | 35 | — | 0 | 51,658 |  |
| `fes_reward_duration` | 12 | year_reward,type | 0 | 42 |  |
| `fes_reward_duration_bak_20260710` | 12 | — | 0 | -1 |  |
| `fes_reward_grade` | 11 | reward_grade_id | 0 | 36,656 |  |
| `fes_reward_grade_all` | 13 | order_id,year,month | 0 | 150,000 |  |
| `fes_reward_grade_all_bak_20260710` | 13 | — | 0 | 923 |  |
| `fes_reward_grade_bak_20260710` | 11 | — | 0 | 34,695 |  |
| `fes_title` | 6 | title_id | 0 | 20 |  |
| `fml_authorize` | 12 | auth_id | 0 | 16,178 |  |
| `fml_bell_group_report` | 5 | — | 0 | 144 |  |
| `fml_bell_user` | 26 | — | 0 | 97 |  |
| `fml_bell_user_group` | 5 | — | 0 | 95 |  |
| `fml_bell_user_store` | 5 | — | 0 | 131 |  |
| `fml_bellinee_statement` | 11 | — | 0 | 59,806 |  |
| `fml_bellinee_statement_file` | 11 | — | 0 | 59,822 |  |
| `fml_cooperation_topic` | 15 | id | 0 | 87 |  |
| `fml_cooperation_topic_backup` | 13 | id | 0 | 63 |  |
| `fml_cooperation_topic_backup_20260703` | 15 | — | 0 | 87 |  |
| `fml_cooperation_trn` | 20 | trn_id | 0 | 19,236 |  |
| `fml_email_account` | 8 | user_id,template_id,email | 0 | 1,646 |  |
| `fml_franchise_statement` | 11 | id | 0 | 1,571,559 | REPORT_TYE = 'RT040079' ACTION_FLAG เพื่อยืนยันรับทราบ ('Y') |
| `fml_franchise_statement_file` | 11 | file_id | 0 | 5,730 |  |
| `fml_franchise_statement_group` | 2 | — | 0 | 963 |  |
| `fml_fs_other` | 14 | id | 0 | -1 |  |
| `fml_pre_statement` | 30 | trn_id | 0 | 185,179 |  |
| `fml_responsible_sbp` | 11 | responsible_sbp_id | 0 | 101 |  |
| `fml_sbp_show_report` | 6 | period,report_type | 0 | 16 |  |
| `fml_sbp_skip_report_store` | 12 | id | 0 | 5 |  |
| `fml_sbp_stmt` | 16 | sbp_stmt_id | 0 | -1 |  |
| `fml_stacc_fr_stmt` | 12 | — | 0 | -1 |  |
| `fml_stacc_fr_stmt_end` | 5 | — | 0 | -1 |  |
| `fml_stmt_end` | 9 | stmt_end_id | 0 | 8 |  |
| `fml_stmt_trans` | 15 | stmt_trans_id | 0 | 85 |  |
| `fml_sub_group_mapping` | 5 | — | 0 | -1 |  |
| `fml_sub_group_report` | 5 | — | 0 | 126 |  |
| `fml_sub_organize` | 41 | — | 0 | 960 |  |
| `fml_sub_pre_statement` | 30 | — | 0 | 61,162 |  |
| `fml_sub_user_group` | 5 | — | 0 | 305 |  |
| `fml_sub_user_store` | 5 | — | 0 | 5,146 |  |
| `fml_sub_user_zone` | 5 | — | 0 | 286 |  |
| `fml_subarea_file` | 13 | — | 0 | -1 |  |
| `fml_subarea_statement` | 11 | — | 0 | 1,224,084 |  |
| `fml_subarea_ws` | 13 | — | 0 | -1 |  |
| `fml_subarea_ws_end` | 4 | — | 0 | -1 |  |
| `fml_tmp_importdata_stmt` | 26 | id | 0 | 4,528 | Converted from FCS_FRN.FML_TMP_IMPORTDATA_STMT |
| `fr_process` | 131 | process_id | 0 | -1 |  |
| `fr_process_trn` | 52 | process_id,step_id | 0 | -1 |  |
| `fr_store` | 85 | — | 0 | 11,583 |  |
| `fr_store_assessment` | 10 | — | 0 | 629 |  |
| `fr_store_contract_history` | 12 | — | 0 | 13,888 |  |
| `fr_store_insure` | 11 | — | 0 | 708 |  |
| `franchisee` | 86 | franchisee_id | 0 | 7,885 |  |
| `fs_sevenshop` | 56 | — | 0 | 18,432 |  |
| `ftp_interface` | 10 | id | 0 | 145 |  |
| `general_upload_data_page_audit_log` | 6 | id | 0 | 377 |  |
| `general_upload_data_page_job` | 8 | id | 0 | 393 |  |
| `import_group` | 8 | id | 0 | 4 |  |
| `import_job_status` | 5 | file_name | 0 | -1 |  |
| `import_type` | 17 | id | 1 | 23 |  |
| `import_type_permission` | 8 | id | 1 | 6 | Permission whitelist for central upload import types. No row means pub |
| `integration_log` | 6 | id | 0 | 518 | **ใช้ใน SBPGI** |
| `juristic` | 24 | — | 0 | 7,603 |  |
| `juristic_backup` | 24 | — | 0 | -1 |  |
| `juristic_group` | 7 | juristic_group_id | 0 | -1 |  |
| `mas_area` | 2 | area_id | 0 | 13 |  |
| `mas_contact` | 12 | — | 0 | 1,137,861 |  |
| `mas_district` | 4 | — | 0 | 959 |  |
| `mas_param` | 10 | — | 0 | 93,752 | **ใช้ใน SBPGI** |
| `mas_province` | 3 | — | 0 | 77 |  |
| `mas_sbp_ad` | 48 | — | 0 | 102,125 |  |
| `mas_store` | 31 | branch_id | 0 | 19,647 | **ใช้ใน SBPGI** |
| `mas_store_cambodia` | 54 | — | 0 | 78 |  |
| `mas_store_laos` | 54 | — | 0 | -1 |  |
| `mas_store_organize` | 19 | — | 0 | 77,376 |  |
| `mas_sub_district` | 4 | — | 0 | 8,807 |  |
| `mas_taxpayer` | 5 | — | 0 | 2,682 |  |
| `mas_tmp_import_data` | 14 | — | 0 | -1 |  |
| `mas_tmp_store` | 31 | — | 0 | 0 |  |
| `mas_zone` | 5 | — | 0 | 28 | **ใช้ใน SBPGI** |
| `master_template_columns` | 20 | code_value | 0 | 18 |  |
| `menus` | 10 | — | 0 | -1 |  |
| `mms_store_merge_trans` | 32 | mms_store_merge_id | 0 | 7 |  |
| `mms_store_trans` | 54 | mms_store_id | 0 | 18 |  |
| `province` | 2 | province_id | 0 | 77 |  |
| `role_permissions` | 4 | — | 0 | -1 |  |
| `roles` | 5 | — | 0 | -1 |  |
| `sap_statement_expected` | 8 | id | 0 | -1 |  |
| `sap_statement_summary_source` | 12 | id | 0 | -1 |  |
| `sevenshop` | 56 | — | 0 | 15,308 | **ใช้ใน SBPGI** |
| `skip_statement` | 19 | id | 0 | -1 | เก็บ statement report ที่ถูกซ่อนชั่วคราว เมื่อร้านถูก skip — structure |
| `statement` | 19 | id | 0 | 174,084 |  |
| `statement_summary` | 16 | id | 0 | 199 |  |
| `store` | 32 | store_id | 0 | 19,402 | **ใช้ใน SBPGI** · ข้อมูลร้านค้า |
| `store_contract_history` | 13 | — | 0 | 59 |  |
| `store_old` | 82 | — | 0 | 5 | ข้อมูลร้าน |
| `store_organize` | 18 | — | 0 | 79,722 |  |
| `store_organize_old` | 19 | — | 1 | 138,802 |  |
| `store_partner` | 6 | partner_id | 0 | 7,600 | ตารางข้อมูลเจ้าของแฟรนไชส์ |
| `store_partner_contacts` | 8 | id | 0 | -1 |  |
| `store_sbp` | 54 | order_id | 0 | 11,583 | ข้อมูลร้าน SBP |
| `store_sbp_20260708` | 23 | order_id | 0 | 10,907 | ตารางหลักข้อมูลร้าน SBP รวบรวมข้อมูลจาก store_master และ store_partner |
| `store_sbp_log` | 4 | log_id | 0 | -1 | ตารางประวัติการย้ายร้านจาก store_id เดิมไป store_id ใหม่ |
| `system_param` | 7 | id | 0 | -1 |  |
| `temp_control_file` | 3 | file_name | 0 | -1 |  |
| `temp_exp_sub` | 10 | id | 0 | -1 |  |
| `temp_pre_statement` | 29 | id | 0 | 1 |  |
| `upload_general` | 11 | id | 2 | 235 | **ใช้ใน SBPGI** |
| `user_group_members` | 2 | — | 0 | -1 |  |
| `user_sub_group` | 4 | — | 0 | -1 | ตารางเก็บข้อมูลกลุ่มย่อยของผู้ใช้งาน |
| `users` | 3 | id | 0 | 1 |  |
| `view_column` | 17 | — | 0 | 816 |  |
| `wf` | 4 | wf_id | 0 | -1 |  |
| `wf_approve` | 18 | wf_approve_id | 0 | 155,740 |  |
| `wf_email_template` | 7 | — | 0 | 118 |  |
| `wf_route` | 12 | — | 0 | 169 |  |
| `wf_status` | 7 | wf_status_id,wf_version_id | 0 | 86 |  |
| `wf_step` | 13 | wf_step_id,wf_version_id | 0 | 86 |  |
| `wf_step_history` | 11 | — | 0 | 161,813 |  |
| `wf_transaction` | 8 | wf_transaction_id | 0 | 53,186 |  |
| `wf_version` | 9 | wf_version_id | 1 | -1 |  |
| `workflow` | 4 | — | 0 | -1 |  |
| `workflow_approver` | 11 | approver_id | 0 | 96,542 |  |
| `workflow_event` | 2 | — | 0 | -1 |  |
| `workflow_group` | 3 | — | 0 | -1 |  |
| `workflow_group_map` | 5 | — | 0 | -1 |  |
| `workflow_history` | 12 | history_id | 0 | 38,010 |  |
| `workflow_part` | 4 | part_id | 0 | -1 |  |
| `workflow_part_display` | 5 | — | 0 | -1 |  |
| `workflow_route` | 11 | route_id | 0 | 43 |  |
| `workflow_state` | 4 | — | 0 | 18 |  |
| `workflow_status` | 4 | — | 0 | 22 |  |
| `workflow_transaction` | 9 | — | 0 | 19,283 |  |
| `workflow_version` | 10 | — | 0 | -1 |  |

---

## โครงสร้างรายตาราง

### actions

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `action_id` | integer | N | nextval('actions_action_id_seq'::regclass) |
| 2 | `action_code` | character varying(50) | Y |  |
| 3 | `action_name` | character varying(255) | Y |  |
| 4 | `created_date` | timestamp without time zone | Y |  |

### amphur

ประมาณ 997 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `amphur_id` | character varying(6) | N |  |
| 2 | `province_id` | character varying(3) | N |  |
| 3 | `amphur_name` | character varying(100) | Y |  |

<details><summary>Index</summary>

- `amphur_idx` — `btree (amphur_id, province_id)`

</details>

### assistant_manager_assignments

ประมาณ 14 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | N |  |
| 3 | `store_code` | character varying(10) | N |  |
| 4 | `store_name` | character varying(200) | N |  |
| 5 | `employee_id` | character varying(10) | N |  |
| 6 | `employee_name` | character varying(100) | N |  |
| 7 | `position_id` | character varying(5) | N |  |
| 8 | `position_name` | character varying(100) | N |  |
| 9 | `remark` | character varying(100) | Y |  |
| 10 | `created_at` | timestamp with time zone | N | now() |
| 11 | `updated_at` | timestamp with time zone | N | now() |
| 12 | `created_by` | bigint | N |  |
| 13 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **UNIQUE:** `user_id,store_code,employee_id`

<details><summary>Index</summary>

- `assistant_manager_assignments_pkey` — `btree (id)`
- `assistant_manager_assignments_user_id_store_code_employee_i_key` — `btree (user_id, store_code, employee_id)`

</details>

### bck_business_user

ประมาณ 24,336 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_name` | character varying(25) | Y |  |
| 2 | `user_id` | bigint | N |  |
| 3 | `group_id` | bigint | Y |  |
| 4 | `password` | character varying(100) | Y |  |
| 5 | `title_code` | character varying(2) | Y |  |
| 6 | `first_name` | character varying(100) | Y |  |
| 7 | `last_name` | character varying(100) | Y |  |
| 8 | `pop3` | character varying(100) | Y |  |
| 9 | `smtp` | character varying(100) | Y |  |
| 10 | `email` | character varying(100) | Y |  |
| 11 | `update_date` | timestamp without time zone | Y |  |
| 12 | `update_user` | character varying(100) | Y |  |
| 13 | `franchisee_id` | bigint | Y |  |
| 14 | `opt_flag` | character(1) | Y |  |
| 15 | `zone_cd` | character varying(5) | Y |  |
| 16 | `id_card` | character varying(20) | Y |  |
| 17 | `birthday` | date | Y |  |
| 18 | `mobile_phone` | character varying(100) | Y |  |
| 19 | `zone_code` | character varying(20) | Y |  |
| 20 | `is_user_lan` | character(1) | Y |  |
| 21 | `first_name_en` | character varying(100) | Y |  |
| 22 | `last_name_en` | character varying(100) | Y |  |
| 23 | `active_flag` | character(1) | Y |  |
| 24 | `create_date` | timestamp without time zone | Y |  |
| 25 | `emp_id` | character varying(20) | Y |  |
| 26 | `position_level` | character varying(20) | Y |  |
| 27 | `domain` | character varying(50) | Y |  |
| 28 | `hire_date` | date | Y |  |
| 29 | `position` | character varying(100) | Y |  |
| 30 | `dept` | character varying(100) | Y |  |
| 31 | `department` | character varying(100) | Y |  |
| 32 | `division` | character varying(100) | Y |  |
| 33 | `jobfield` | character varying(100) | Y |  |
| 34 | `company_name` | character varying(100) | Y |  |
| 35 | `remark1` | character varying(100) | Y |  |
| 36 | `cpall_acting_supervisor_lvl` | character varying(20) | Y |  |

### bck_mas_store_organize

ประมาณ 120,000 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
| 2 | `emp_id` | character varying(20) | Y |  |
| 3 | `fullname` | character varying(100) | Y |  |
| 4 | `id_card` | character varying(20) | Y |  |
| 5 | `firstname_th` | character varying(50) | Y |  |
| 6 | `lastname_th` | character varying(50) | Y |  |
| 7 | `firstname_en` | character varying(50) | Y |  |
| 8 | `lastname_en` | character varying(50) | Y |  |
| 9 | `birthday` | date | Y |  |
| 10 | `tel_no` | character varying(30) | Y |  |
| 11 | `page_no` | character varying(30) | Y |  |
| 12 | `email` | character varying(100) | Y |  |
| 13 | `group_id` | bigint | Y |  |
| 14 | `note_name` | character varying(100) | Y |  |
| 15 | `other` | character varying(100) | Y |  |
| 16 | `data_type` | character varying(5) | Y |  |
| 17 | `mobile` | character varying(30) | Y |  |
| 18 | `active_flag` | character(1) | Y |  |
| 19 | `country` | character varying(50) | Y |  |

### bellinee_store

ประมาณ 254 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(5) | N |  |
| 2 | `store_name` | character varying(50) | Y |  |
| 3 | `store_name_short` | character varying(20) | Y |  |
| 4 | `corporation_id` | character varying(5) | Y |  |
| 5 | `zone_cd` | character varying(2) | Y |  |
| 6 | `location_type` | character varying(1) | Y |  |
| 7 | `open_date` | character varying(8) | Y |  |
| 8 | `close_date` | character varying(8) | Y |  |
| 9 | `renovation_type` | character varying(1) | Y |  |
| 10 | `renovation_start_date` | character varying(8) | Y |  |
| 11 | `renovation_end_date` | character varying(8) | Y |  |
| 12 | `suspend_order_flg` | character varying(1) | Y |  |
| 13 | `store_address_1` | character varying(30) | Y |  |
| 14 | `store_address_2` | character varying(30) | Y |  |
| 15 | `store_address_3` | character varying(30) | Y |  |
| 16 | `store_address_4` | character varying(30) | Y |  |
| 17 | `store_sub_district_cd` | character varying(6) | Y |  |
| 18 | `store_district_cd` | character varying(4) | Y |  |
| 19 | `store_province_cd` | character varying(2) | Y |  |
| 20 | `store_postal_cd` | character varying(5) | Y |  |
| 21 | `store_phone_no` | character varying(20) | Y |  |
| 22 | `store_fax_no` | character varying(20) | Y |  |
| 23 | `store_owner_name` | character varying(50) | Y |  |
| 24 | `up_country_flg` | character varying(1) | Y |  |
| 25 | `maximum_return_ratio` | numeric(3,0) | Y |  |
| 26 | `selling_floor_space` | numeric(5,1) | Y |  |
| 27 | `backroom_area` | numeric(5,1) | Y |  |
| 28 | `store_type` | character varying(1) | Y |  |
| 29 | `license_type` | character varying(1) | Y |  |
| 30 | `license_type_date` | character varying(8) | Y |  |
| 31 | `royal_fee_type` | character varying(1) | Y |  |
| 32 | `store_assortment_flg` | character varying(1) | Y |  |
| 33 | `store_food_order_flg` | character varying(1) | Y |  |
| 34 | `store_credit_limit` | numeric(9,2) | Y |  |
| 35 | `fr_statement_cycle` | character varying(1) | Y |  |
| 36 | `fr_statement_issue_date` | numeric(2,0) | Y |  |
| 37 | `payment_period` | numeric(3,0) | Y |  |
| 38 | `pay_by_day_cd` | character varying(1) | Y |  |
| 39 | `vat_register_no` | character varying(20) | Y |  |
| 40 | `vat_franchise_no` | character varying(20) | Y |  |
| 41 | `sequence_no` | numeric(5,0) | Y |  |
| 42 | `store_home_id` | character varying(20) | Y |  |
| 43 | `store_merge_type` | character varying(1) | N |  |
| 44 | `active_flag` | character varying(1) | N | 'Y'::character varying |
| 45 | `mms_store_id` | bigint | Y |  |
| 46 | `mms_store_merge_id` | bigint | N |  |
| 47 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 48 | `create_by` | character varying(20) | Y | 'SYSTEM'::character varying |
| 49 | `update_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 50 | `update_by` | character varying(20) | Y | 'SYSTEM'::character varying |

### bellinee_store_organize

ประมาณ 264 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` 🔑 | character varying(10) | N |  |
| 2 | `name` | character varying(50) | Y |  |
| 3 | `open_date` | timestamp without time zone | Y |  |
| 4 | `close_date` | timestamp without time zone | Y |  |
| 5 | `tel` | character varying(25) | Y |  |
| 6 | `home_number` | character varying(50) | Y |  |
| 7 | `lane` | character varying(50) | Y |  |
| 8 | `road` | character varying(50) | Y |  |
| 9 | `sub_district` | character varying(50) | Y |  |
| 10 | `district` | character varying(50) | Y |  |
| 11 | `province` | character varying(50) | Y |  |
| 12 | `post_number` | character varying(50) | Y |  |
| 13 | `fc_id` | character varying(10) | Y |  |
| 14 | `fc_name` | character varying(50) | Y |  |
| 15 | `fc_e_mail` | character varying(30) | Y |  |
| 16 | `fc_note_name` | character varying(60) | Y |  |
| 17 | `fc_page_number` | character varying(15) | Y |  |
| 18 | `fc_tel_number` | character varying(15) | Y |  |
| 19 | `mn_id` | character varying(10) | Y |  |
| 20 | `mn_name` | character varying(50) | Y |  |
| 21 | `mn_e_mail` | character varying(30) | Y |  |
| 22 | `mn_note_name` | character varying(60) | Y |  |
| 23 | `mn_page_number` | character varying(15) | Y |  |
| 24 | `mn_tel_number` | character varying(15) | Y |  |
| 25 | `dpt_id` | character varying(10) | Y |  |
| 26 | `dpt_name` | character varying(50) | Y |  |
| 27 | `dpt_e_mail` | character varying(30) | Y |  |
| 28 | `dpt_note_name` | character varying(60) | Y |  |
| 29 | `dpt_page_number` | character varying(15) | Y |  |
| 30 | `dpt_tel_number` | character varying(15) | Y |  |
| 31 | `agm_id` | character varying(10) | Y |  |
| 32 | `agm_name` | character varying(50) | Y |  |
| 33 | `agm_e_mail` | character varying(30) | Y |  |
| 34 | `agm_note_name` | character varying(60) | Y |  |
| 35 | `agm_page_number` | character varying(15) | Y |  |
| 36 | `agm_tel_number` | character varying(15) | Y |  |
| 37 | `gm_id` | character varying(10) | Y |  |
| 38 | `gm_name` | character varying(50) | Y |  |
| 39 | `gm_e_mail` | character varying(30) | Y |  |
| 40 | `gm_note_name` | character varying(60) | Y |  |
| 41 | `gm_page_number` | character varying(15) | Y |  |
| 42 | `gm_tel_number` | character varying(15) | Y |  |
| 43 | `zone` | character varying(3) | Y |  |
| 44 | `ptt_type` | character varying(5) | Y |  |
| 45 | `seven_store_type` | character varying(5) | Y |  |
| 46 | `ks_store_type` | character varying(15) | Y |  |
| 47 | `ks_sub_type` | character varying(15) | Y |  |
| 48 | `rnv_start` | timestamp without time zone | Y |  |
| 49 | `rnv_end` | timestamp without time zone | Y |  |

- **PK:** `branch_id`

<details><summary>Index</summary>

- `bellinee_store_organize_pkey` — `btree (branch_id)`

</details>

### business_group

ประมาณ 126 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` 🔑 | bigint | N |  |
| 2 | `group_name` | character varying(100) | Y |  |
| 3 | `parent_group_id` | bigint | Y |  |
| 4 | `seq_no` | smallint | N |  |
| 5 | `update_date` | timestamp without time zone | Y |  |
| 6 | `update_user` | character varying(100) | Y |  |
| 7 | `system_code` | character varying(5) | Y |  |
| 8 | `is_require_store_type` | boolean | Y | false |
| 9 | `is_require_store_area` | boolean | Y | false |
| 10 | `jforum_group_id` | bigint | Y |  |
| 11 | `is_system_group` | boolean | Y | false |

- **PK:** `group_id`

<details><summary>Index</summary>

- `bu_group_idx` — `btree (group_id, group_name)`
- `business_group_pk` — `btree (group_id)`

</details>

### business_user

**ใช้ใน SBPGI:** ผู้ใช้/ผู้อนุมัติ · ประมาณ 12,752 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_name` | character varying(25) | Y |  |
| 2 | `user_id` | bigint | N |  |
| 3 | `group_id` | bigint | Y |  |
| 4 | `password` | character varying(100) | Y |  |
| 5 | `title_code` | character varying(2) | Y |  |
| 6 | `first_name` | character varying(100) | Y |  |
| 7 | `last_name` | character varying(100) | Y |  |
| 8 | `pop3` | character varying(100) | Y |  |
| 9 | `smtp` | character varying(100) | Y |  |
| 10 | `email` | character varying(100) | Y |  |
| 11 | `update_date` | timestamp without time zone | Y |  |
| 12 | `update_user` | character varying(100) | Y |  |
| 13 | `franchisee_id` | bigint | Y |  |
| 14 | `opt_flag` | character(1) | Y |  |
| 15 | `zone_cd` | character varying(5) | Y |  |
| 16 | `id_card` | character varying(20) | Y |  |
| 17 | `birthday` | date | Y |  |
| 18 | `mobile_phone` | character varying(100) | Y |  |
| 19 | `zone_code` | character varying(20) | Y |  |
| 20 | `is_user_lan` | character(1) | Y |  |
| 21 | `first_name_en` | character varying(100) | Y |  |
| 22 | `last_name_en` | character varying(100) | Y |  |
| 23 | `active_flag` | character(1) | Y |  |
| 24 | `create_date` | timestamp without time zone | Y |  |
| 25 | `emp_id` | character varying(20) | Y |  |
| 26 | `position_level` | character varying(20) | Y |  |
| 27 | `domain` | character varying(50) | Y |  |
| 28 | `hire_date` | date | Y |  |
| 29 | `position` | character varying(100) | Y |  |
| 30 | `dept` | character varying(100) | Y |  |
| 31 | `department` | character varying(100) | Y |  |
| 32 | `division` | character varying(100) | Y |  |
| 33 | `jobfield` | character varying(100) | Y |  |
| 34 | `company_name` | character varying(100) | Y |  |
| 35 | `remark1` | character varying(100) | Y |  |
| 36 | `cpall_acting_supervisor_lvl` | character varying(20) | Y |  |

<details><summary>Index</summary>

- `idx_bu_empid_active` — `btree (emp_id, active_flag)`

</details>

### business_user_group

ประมาณ 11,409 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |
| 3 | `store_type` | character varying(5) | Y |  |
| 4 | `store_area` | character varying(5) | Y |  |
| 5 | `group_name` | character varying(64) | Y |  |
| 6 | `parent_group_id` | integer | Y |  |
| 7 | `seq_no` | integer | Y |  |
| 8 | `update_date` | character varying(50) | Y |  |
| 9 | `update_user` | character varying(50) | Y |  |
| 10 | `system_code` | character varying(50) | Y |  |
| 11 | `is_require_store_type` | character varying(50) | Y |  |
| 12 | `is_require_store_area` | character varying(50) | Y |  |
| 13 | `jforum_group_id` | character varying(50) | Y |  |
| 14 | `is_system_group` | character varying(50) | Y |  |

<details><summary>Index</summary>

- `idx_stmt_perf_bug_user_group` — `btree (user_id, group_id)`

</details>

### cancel_contract_store_approve

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` 🔑 | numeric(38,0) | N |  |
| 2 | `store_id` | character varying(10) | Y |  |
| 3 | `cancel_type` | character varying(2) | Y |  |
| 4 | `cancel_reason` | character varying(2) | Y |  |
| 5 | `cancel_type_move_store` | character varying(2) | Y |  |
| 6 | `cancel_reason_other` | character varying(4000) | Y |  |
| 7 | `cancel_date` | timestamp with time zone | Y |  |
| 8 | `cancel_detail` | character varying(1000) | Y |  |
| 9 | `to_store_id` | character varying(10) | Y |  |
| 10 | `create_date` | timestamp with time zone | Y | now() |

- **PK:** `order_id`

<details><summary>Index</summary>

- `cancel_contract_store_pk` — `btree (order_id)`

</details>

### common_code

**ใช้ใน SBPGI:** lookup ทั่วไป (+ วงเงินอนุมัติ SBPGI_APPROVE_LIMIT) · ประมาณ 2,609 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `code_type` | character varying(20) | N |  |
| 2 | `seq_no` | integer | N |  |
| 3 | `code_value` | character varying(100) | Y |  |
| 4 | `code_name` | character varying(1000) | Y |  |
| 5 | `related_flag` | character varying(1) | Y |  |
| 6 | `other_field` | character varying(1) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y |  |
| 8 | `create_user` | character varying(200) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y |  |
| 10 | `update_user` | character varying(200) | Y |  |
| 11 | `code_mapping` | character varying(100) | Y |  |
| 12 | `active_flag` | character varying(1) | Y | 'Y'::character varying |
| 13 | `other_value` | character varying(50) | Y |  |
| 14 | `language` | character varying(50) | Y |  |

<details><summary>Index</summary>

- `common_code_idx` — `btree (code_type, code_value, code_name)`
- `idx_stmt_perf_common_code_fml_value_type` — `btree (code_value, code_type, seq_no, code_name) WHERE ("substring"((code_type)::text, 1, 3) = 'FML'::text)`
- `idx_stmt_perf_common_code_value` — `btree (code_value) INCLUDE (code_type, code_name, seq_no)`

</details>

### common_code_type

ประมาณ 376 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `code_type` 🔑 | character varying(50) | N |  |
| 2 | `code_type_name` | character varying(200) | N |  |
| 3 | `digit` | character varying(50) | Y |  |
| 4 | `field_type` | character varying(50) | Y |  |
| 5 | `active_flag` | character varying(1) | N | 'Y'::character varying |
| 6 | `create_date` | timestamp without time zone | Y |  |
| 7 | `create_user` | character varying(200) | Y |  |
| 8 | `update_date` | timestamp without time zone | Y |  |
| 9 | `update_user` | character varying(200) | Y |  |

- **PK:** `code_type`

<details><summary>Index</summary>

- `idx_common_code_type_name` — `btree (code_type_name)`
- `pk_common_code_type` — `btree (code_type)`

</details>

### common_log

ประมาณ 6 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('seq_common_log'::regclass) |
| 2 | `system` | character varying(20) | Y |  |
| 3 | `module` | character varying(200) | Y |  |
| 4 | `detail` | text | Y |  |
| 5 | `create_user` | character varying(200) | Y |  |
| 6 | `create_date` | timestamp without time zone | Y |  |
| 7 | `create_user_id` | bigint | Y |  |
| 8 | `ip_address` | character varying(100) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `common_log_pk` — `btree (id)`

</details>

### email_sent

**ใช้ใน SBPGI:** log การส่งอีเมล · ประมาณ 5,214 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `email_sent_id` 🔑 | bigint | N | nextval('email_sent_email_sent_id_seq'::regclass) |
| 2 | `email_id` | bigint | Y |  |
| 3 | `subject` | text | Y |  |
| 4 | `content` | text | Y |  |
| 5 | `mail_from` | character varying(255) | Y |  |
| 6 | `mail_from_name` | character varying(255) | Y |  |
| 7 | `mail_to` | text | Y |  |
| 8 | `mail_cc` | text | Y |  |
| 9 | `sent_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 10 | `send_by` | character varying(100) | Y |  |
| 11 | `is_sent` | text | Y |  |
| 12 | `error` | text | Y |  |

- **PK:** `email_sent_id`

<details><summary>Index</summary>

- `email_sent_pkey` — `btree (email_sent_id)`

</details>

### email_template

**ใช้ใน SBPGI:** template อีเมล (แทน email_templates) · ประมาณ 85 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `email_template_id` 🔑 | integer | N | nextval('email_template_email_template_id_seq'::regclass) |
| 2 | `email_template_name` | character varying(500) | Y |  |
| 3 | `email_template_desc` | character varying(1000) | Y |  |
| 4 | `subject_format` | character varying(500) | Y |  |
| 5 | `body_format` | text | Y |  |
| 6 | `create_by` | character varying(100) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 8 | `sender` | character varying(200) | Y |  |
| 9 | `email_from` | character varying(100) | Y |  |
| 10 | `active_flag` | character(1) | Y | 'Y'::bpchar |
| 11 | `update_by` | character varying(100) | Y |  |
| 12 | `update_date` | timestamp without time zone | Y |  |

- **PK:** `email_template_id`

<details><summary>Index</summary>

- `email_template_pkey` — `btree (email_template_id)`

</details>

### fcs_audit_costs

**ใช้ใน SBPGI:** ต้นทุนตรวจนับ · ประมาณ 711,384 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('fcs_audit_costs_id_seq'::regclass) |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | character varying(4) | Y |  |
| 4 | `month` | character varying(2) | Y |  |
| 5 | `product_exceeded_lack` | numeric(38,2) | Y |  |
| 6 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`

<details><summary>Index</summary>

- `fcs_audit_costs_idx` — `btree (store_id, year, month)`
- `fcs_audit_costs_pkey` — `btree (id)`

</details>

### fcs_content

ประมาณ 8,571 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `content_id` 🔑 | bigint | N |  |
| 2 | `seq` | bigint | Y |  |
| 3 | `subject` | character varying(4000) | Y |  |
| 4 | `parent_content_id` | bigint | Y |  |
| 5 | `content_type` | character varying(100) | Y |  |
| 6 | `is_active` | character(1) | Y |  |
| 7 | `content_flag` | character varying(100) | Y |  |
| 8 | `create_by` | character varying(100) | Y |  |
| 9 | `create_date` | timestamp without time zone | Y | now() |
| 10 | `update_by` | character varying(100) | Y |  |
| 11 | `update_date` | timestamp without time zone | Y |  |
| 12 | `category_id` | bigint | Y |  |
| 13 | `system_code` | character varying(100) | Y |  |
| 14 | `access_flag` | character(1) | Y | 'Y'::bpchar |
| 15 | `end_date` | timestamp without time zone | Y |  |
| 16 | `bg_color` | character varying(10) | Y |  |
| 17 | `description` | text | Y |  |
| 18 | `summary` | text | Y |  |
| 19 | `pin_flag` | character(1) | Y |  |
| 20 | `pin_flag_news` | character(1) | Y | 'N'::bpchar |
| 21 | `update_flag_news` | timestamp without time zone | Y |  |

- **PK:** `content_id`

<details><summary>Index</summary>

- `fcs_content_pkey` — `btree (content_id)`
- `idx_fcs_content_1` — `btree (category_id, content_flag, is_active, access_flag, system_code)`

</details>

### fcs_file_content

ประมาณ 3,367 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_id` 🔑 | bigint | N |  |
| 2 | `file_name` | character varying(250) | Y |  |
| 3 | `content_type` | character varying(100) | Y |  |
| 4 | `content` | bytea | Y |  |
| 5 | `file_flag` | character varying(100) | Y |  |
| 6 | `create_by` | character varying(100) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | now() |
| 8 | `update_by` | character varying(100) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y | now() |
| 10 | `file_link` | character varying(255) | Y |  |

- **PK:** `file_id`

<details><summary>Index</summary>

- `fcs_file_content_pkey` — `btree (file_id)`
- `idx_fcs_file_content_type` — `btree (content_type)`

</details>

### fcs_file_mapping

ประมาณ 22,314 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_mapping_id` 🔑 | bigint | N |  |
| 2 | `transaction_pk` | numeric(38,0) | N |  |
| 3 | `file_id` | numeric(38,0) | N |  |
| 4 | `seq` | bigint | Y |  |
| 5 | `parent_file_mapping_id` | bigint | Y |  |
| 6 | `table_transaction_pk` | character varying(100) | N |  |
| 7 | `table_file_id` | character varying(100) | N |  |
| 8 | `code_value` | character varying(100) | Y |  |
| 9 | `code_type` | character varying(10) | Y |  |
| 10 | `system_code` | character varying(25) | N |  |

- **PK:** `file_mapping_id`

<details><summary>Index</summary>

- `fcs_file_mapping_pkey` — `btree (file_mapping_id)`
- `idx_fcs_file_mapping_file` — `btree (file_id)`
- `idx_fcs_file_mapping_tbl` — `btree (table_transaction_pk, table_file_id)`
- `idx_fcs_file_mapping_tx` — `btree (transaction_pk)`

</details>

### fcs_monthly_sales

**ใช้ใน SBPGI:** ยอดขายรายเดือน · ประมาณ 711,384 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('fcs_monthly_sales_id_seq'::regclass) |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | character varying(4) | Y |  |
| 4 | `month` | character varying(2) | Y |  |
| 5 | `total_sales` | numeric(38,3) | Y |  |
| 6 | `amt_cust_total` | numeric | Y |  |
| 7 | `sales_exclude_card` | numeric(38,3) | Y |  |
| 8 | `amt_cust_exclude_card` | numeric | Y |  |
| 9 | `sales_card` | numeric(38,3) | Y |  |
| 10 | `amt_cust_card` | numeric | Y |  |
| 11 | `total_day` | numeric | Y |  |
| 12 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`

<details><summary>Index</summary>

- `fcs_monthly_sales_idx` — `btree (store_id, year, month)`
- `fcs_monthly_sales_pkey` — `btree (id)`

</details>

### fcs_qssi_score

**ใช้ใน SBPGI:** คะแนน QSSI 6 หมวด · ประมาณ 23,958,780 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('fcs_qssi_score_id_seq'::regclass) |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `category` | character varying(2) | Y |  |
| 4 | `month` | character varying(2) | Y |  |
| 5 | `year` | character varying(4) | Y |  |
| 6 | `score` | numeric(38,2) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`

<details><summary>Index</summary>

- `fcs_qssi_score_pkey` — `btree (id)`

</details>

### fcs_qssi_score_bak_20260710

ประมาณ 18,577,924 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` | bigint | Y |  |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `category` | character varying(2) | Y |  |
| 4 | `month` | character varying(2) | Y |  |
| 5 | `year` | character varying(4) | Y |  |
| 6 | `score` | numeric(38,2) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y |  |

### fcs_reminder_log

ประมาณ 695,653 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | numeric | Y |  |
| 2 | `template_id` | numeric | Y |  |
| 3 | `reminder_to` | character varying(4000) | Y |  |
| 4 | `reminder_type` | character(1) | Y |  |
| 5 | `reminder_status` | character(1) | Y |  |
| 6 | `error_msg` | character varying(4000) | Y |  |
| 7 | `remind_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 8 | `reminder_cc` | character varying(4000) | Y |  |
| 9 | `json_data` | character varying(4000) | Y |  |
| 10 | `create_by` | numeric | Y |  |

### fcs_tmp_qssi_score

ประมาณ 0 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(20) | Y |  |
| 2 | `data_desc` | character varying(200) | Y |  |
| 3 | `score` | numeric(15,4) | Y |  |
| 4 | `max_score` | numeric(15,4) | Y |  |
| 5 | `percent` | numeric(15,4) | Y |  |
| 6 | `file_name` | character varying(100) | Y |  |
| 7 | `check_date` | timestamp without time zone | Y |  |
| 8 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

### fes_adjust_grade

ประมาณ 128,805 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(8) | Y |  |
| 2 | `eval_year` | integer | Y |  |
| 3 | `eval_month` | integer | Y |  |
| 4 | `total_point` | numeric(7,2) | Y |  |
| 5 | `point_percent` | numeric(7,2) | Y |  |
| 6 | `grade` | character varying(2) | Y |  |
| 7 | `create_by` | integer | Y |  |
| 8 | `create_date` | timestamp with time zone | Y |  |
| 9 | `update_by` | integer | Y |  |
| 10 | `update_date` | timestamp with time zone | Y |  |

- **UNIQUE:** `store_id,eval_year,eval_month`

<details><summary>Index</summary>

- `fes_adjust_grade_u01` — `btree (store_id, eval_year, eval_month)`

</details>

### fes_adjust_grade_bak_20260710

ประมาณ 1,402 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(8) | Y |  |
| 2 | `eval_year` | integer | Y |  |
| 3 | `eval_month` | integer | Y |  |
| 4 | `total_point` | numeric(7,2) | Y |  |
| 5 | `point_percent` | numeric(7,2) | Y |  |
| 6 | `grade` | character varying(2) | Y |  |
| 7 | `create_by` | integer | Y |  |
| 8 | `create_date` | timestamp with time zone | Y |  |
| 9 | `update_by` | integer | Y |  |
| 10 | `update_date` | timestamp with time zone | Y |  |

### fes_bank_account

ประมาณ 14,079 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | Y |  |
| 2 | `store_name` | character varying(255) | Y |  |
| 3 | `gl_account` | character varying(50) | Y |  |
| 4 | `bank_account` | character varying(50) | Y |  |
| 5 | `bank_name` | character varying(255) | Y |  |
| 6 | `create_date` | date | Y |  |

### fes_copylvthree

ประมาณ 7,227,231 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `copylvthree_id` 🔑 | numeric(38,0) | N |  |
| 2 | `point` | numeric(6,2) | Y |  |
| 3 | `evallevelthree_id` | numeric(38,0) | N |  |
| 4 | `evaluate_id` | numeric(38,0) | Y |  |
| 5 | `create_date` | date | Y | CURRENT_DATE |

- **PK:** `copylvthree_id`

<details><summary>Index</summary>

- `fes_copylvthree_index1` — `btree (evallevelthree_id)`
- `fes_copylvthree_index2` — `btree (evaluate_id)`
- `fes_copylvthree_pkey` — `btree (copylvthree_id)`

</details>

### fes_copylvthree_bak_20260710

ประมาณ 550 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `copylvthree_id` | numeric(38,0) | Y |  |
| 2 | `point` | numeric(6,2) | Y |  |
| 3 | `evallevelthree_id` | numeric(38,0) | Y |  |
| 4 | `evaluate_id` | numeric(38,0) | Y |  |
| 5 | `create_date` | date | Y |  |

### fes_copylvtwo

ประมาณ 685,085 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `copylvtwo_id` 🔑 | numeric | N |  |
| 2 | `point` | numeric(6,2) | Y |  |
| 3 | `evalleveltwo_id` | numeric | N |  |
| 4 | `evaluate_id` | numeric | Y |  |
| 5 | `create_date` | date | Y | CURRENT_DATE |

- **PK:** `copylvtwo_id`

<details><summary>Index</summary>

- `fes_copylvtwo_pkey` — `btree (copylvtwo_id)`
- `idx_copylvtwo_eval_l2` — `btree (evaluate_id, evalleveltwo_id)`
- `idx_fes_copylvtwo_evaluate` — `btree (evaluate_id)`
- `idx_fes_copylvtwo_l2` — `btree (evalleveltwo_id)`

</details>

### fes_copylvtwo_bak_20260710

ประมาณ 587,997 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `copylvtwo_id` | numeric | Y |  |
| 2 | `point` | numeric(6,2) | Y |  |
| 3 | `evalleveltwo_id` | numeric | Y |  |
| 4 | `evaluate_id` | numeric | Y |  |
| 5 | `create_date` | date | Y |  |

### fes_evallevelone

ประมาณ 15 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evallevelone_id` | numeric | N |  |
| 2 | `levelone_name` | character varying(500) | Y |  |
| 3 | `evaluatedform_id` | numeric | N |  |
| 4 | `temporary_export_flag` | character varying(1) | Y |  |
| 5 | `point` | numeric(6,2) | Y |  |
| 6 | `seq` | numeric | Y |  |

<details><summary>Index</summary>

- `idx_l1_form` — `btree (evaluatedform_id)`

</details>

### fes_evallevelone_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evallevelone_id` | numeric | Y |  |
| 2 | `levelone_name` | character varying(500) | Y |  |
| 3 | `evaluatedform_id` | numeric | Y |  |
| 4 | `temporary_export_flag` | character varying(1) | Y |  |
| 5 | `point` | numeric(6,2) | Y |  |
| 6 | `seq` | numeric | Y |  |

### fes_evallevelthree

ประมาณ 165 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evallevelthree_id` 🔑 | numeric | N |  |
| 2 | `grade_id` | numeric | Y |  |
| 3 | `levelthree_name` | character varying(500) | Y |  |
| 4 | `point` | numeric(6,2) | Y |  |
| 5 | `point_hit` | character varying(200) | Y |  |
| 6 | `hint` | character varying(1000) | Y |  |
| 7 | `evalleveltwo_id` | numeric | N |  |
| 8 | `fixed` | numeric | Y |  |
| 9 | `seq` | numeric | Y |  |
| 10 | `start_month` | numeric | Y |  |
| 11 | `start_year` | numeric | Y |  |

- **PK:** `evallevelthree_id`

<details><summary>Index</summary>

- `fes_evallevelthree_pk` — `btree (evallevelthree_id)`
- `idx_l3_l2` — `btree (evalleveltwo_id)`

</details>

### fes_evallevelthree_bak_20260710

ประมาณ 104 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evallevelthree_id` | numeric | Y |  |
| 2 | `grade_id` | numeric | Y |  |
| 3 | `levelthree_name` | character varying(500) | Y |  |
| 4 | `point` | numeric(6,2) | Y |  |
| 5 | `point_hit` | character varying(200) | Y |  |
| 6 | `hint` | character varying(1000) | Y |  |
| 7 | `evalleveltwo_id` | numeric | Y |  |
| 8 | `fixed` | numeric | Y |  |
| 9 | `seq` | numeric | Y |  |
| 10 | `start_month` | numeric | Y |  |
| 11 | `start_year` | numeric | Y |  |

### fes_evalleveltwo

ประมาณ 39 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalleveltwo_id` 🔑 | numeric | N |  |
| 2 | `leveltwo_name` | character varying(500) | Y |  |
| 3 | `point` | numeric(6,2) | Y |  |
| 4 | `point_hit` | character varying(200) | Y |  |
| 5 | `hint` | character varying(1000) | Y |  |
| 6 | `evallevelone_id` | numeric | N |  |
| 7 | `fixed` | numeric | Y |  |
| 8 | `temporary_export_flag` | character varying(1) | Y |  |
| 9 | `default_point` | numeric(6,2) | Y |  |
| 10 | `seq` | numeric | Y |  |

- **PK:** `evalleveltwo_id`

<details><summary>Index</summary>

- `idx_l2_l1` — `btree (evallevelone_id)`
- `pk_fes_evalleveltwo` — `btree (evalleveltwo_id)`

</details>

### fes_evalleveltwo_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalleveltwo_id` | numeric | Y |  |
| 2 | `leveltwo_name` | character varying(500) | Y |  |
| 3 | `point` | numeric(6,2) | Y |  |
| 4 | `point_hit` | character varying(200) | Y |  |
| 5 | `hint` | character varying(1000) | Y |  |
| 6 | `evallevelone_id` | numeric | Y |  |
| 7 | `fixed` | numeric | Y |  |
| 8 | `temporary_export_flag` | character varying(1) | Y |  |
| 9 | `default_point` | numeric(6,2) | Y |  |
| 10 | `seq` | numeric | Y |  |

### fes_evalperson

ประมาณ 44 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalperson_id` | numeric | N |  |
| 2 | `group_id` | numeric | N |  |
| 3 | `email` | character varying(60) | Y |  |
| 4 | `evalleveltwo_id` | numeric | N |  |

### fes_evalperson_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalperson_id` | numeric | Y |  |
| 2 | `group_id` | numeric | Y |  |
| 3 | `email` | character varying(60) | Y |  |
| 4 | `evalleveltwo_id` | numeric | Y |  |

### fes_evalpersonthree

ประมาณ 16 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalpersonthree_id` | numeric | N |  |
| 2 | `evalpersontwo_id` | numeric | Y |  |
| 3 | `group_id` | numeric | Y |  |
| 4 | `evallevelthree_id` | numeric | Y |  |

### fes_evalpersonthree_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evalpersonthree_id` | numeric | Y |  |
| 2 | `evalpersontwo_id` | numeric | Y |  |
| 3 | `group_id` | numeric | Y |  |
| 4 | `evallevelthree_id` | numeric | Y |  |

### fes_evaltype

ประมาณ 184 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaltype_id` | numeric | N |  |
| 2 | `evaltype` | character varying(7) | Y |  |
| 3 | `evalleveltwo_id` | numeric | N |  |

### fes_evaluate

ประมาณ 203,884 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluate_id` 🔑 | bigint | N |  |
| 2 | `eval_type` | character varying(20) | N |  |
| 3 | `send_date` | date | Y |  |
| 4 | `order_id` | bigint | N |  |
| 5 | `note` | character varying(1000) | Y |  |
| 6 | `eval_month` | numeric | N |  |
| 7 | `eval_year` | numeric | N |  |
| 8 | `evaluatedform_id` | bigint | N |  |
| 9 | `create_id` | bigint | Y |  |
| 10 | `create_date` | date | Y | CURRENT_DATE |
| 11 | `modify_id` | bigint | Y |  |
| 12 | `modify_date` | date | Y |  |
| 13 | `total_point` | numeric(7,2) | Y |  |
| 14 | `grade` | character varying(2) | Y |  |
| 15 | `status` | character varying(2) | Y |  |
| 16 | `description` | character varying(4000) | Y |  |
| 17 | `del_status` | character varying(2) | Y |  |
| 18 | `account_description` | character varying(1000) | Y |  |
| 19 | `account_merge_flag` | character varying(2) | Y |  |
| 20 | `fr_store_order_id` | numeric(38,0) | Y |  |
| 21 | `status_temp` | character varying(2) | Y |  |
| 22 | `conclude_date` | date | Y |  |
| 23 | `modify_conclude_date` | date | Y |  |
| 24 | `confirm_grade_status` | character varying(2) | Y |  |
| 25 | `confirm_grade_date` | date | Y |  |

- **PK:** `evaluate_id`

<details><summary>Index</summary>

- `fes_evaluate_pk` — `btree (evaluate_id)`
- `idx_eval_main` — `btree (fr_store_order_id, eval_type, eval_month, eval_year, evaluate_id DESC)`
- `idx_fes_evaluate_eval_month` — `btree (eval_month)`
- `idx_fes_evaluate_eval_year` — `btree (eval_year)`
- `idx_fes_evaluate_evaluatedform_id` — `btree (evaluatedform_id)`
- `idx_fes_evaluate_form` — `btree (evaluatedform_id)`
- `idx_fes_evaluate_id` — `btree (evaluate_id)`
- `idx_fes_evaluate_order_id` — `btree (order_id)`
- `idx_fes_evaluate_status` — `btree (status)`

</details>

### fes_evaluate_bak_20260710

ประมาณ 176,368 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluate_id` | bigint | Y |  |
| 2 | `eval_type` | character varying(20) | Y |  |
| 3 | `send_date` | date | Y |  |
| 4 | `order_id` | bigint | Y |  |
| 5 | `note` | character varying(1000) | Y |  |
| 6 | `eval_month` | numeric | Y |  |
| 7 | `eval_year` | numeric | Y |  |
| 8 | `evaluatedform_id` | bigint | Y |  |
| 9 | `create_id` | bigint | Y |  |
| 10 | `create_date` | date | Y |  |
| 11 | `modify_id` | bigint | Y |  |
| 12 | `modify_date` | date | Y |  |
| 13 | `total_point` | numeric(7,2) | Y |  |
| 14 | `grade` | character varying(2) | Y |  |
| 15 | `status` | character varying(2) | Y |  |
| 16 | `description` | character varying(4000) | Y |  |
| 17 | `del_status` | character varying(2) | Y |  |
| 18 | `account_description` | character varying(1000) | Y |  |
| 19 | `account_merge_flag` | character varying(2) | Y |  |
| 20 | `fr_store_order_id` | numeric(38,0) | Y |  |
| 21 | `status_temp` | character varying(2) | Y |  |
| 22 | `conclude_date` | date | Y |  |
| 23 | `modify_conclude_date` | date | Y |  |
| 24 | `confirm_grade_status` | character varying(2) | Y |  |
| 25 | `confirm_grade_date` | date | Y |  |

### fes_evaluate_hint_levelone

ประมาณ 117 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `eval_id` | numeric | N |  |
| 2 | `eval_level` | numeric | N |  |
| 3 | `seq` | numeric | N |  |
| 4 | `hint` | character varying(4000) | Y |  |

- **PK:** `eval_id,eval_level,seq`

<details><summary>Index</summary>

- `fes_evaluate_hint_levelone_pk` — `btree (eval_id, eval_level, seq)`
- `idx_hint_levelone_eval` — `btree (eval_id)`

</details>

### fes_evaluate_hint_levelone_bak_20260710

ประมาณ 117 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `eval_id` | numeric | Y |  |
| 2 | `eval_level` | numeric | Y |  |
| 3 | `seq` | numeric | Y |  |
| 4 | `hint` | character varying(4000) | Y |  |

### fes_evaluate_hint_leveltwo

ประมาณ 321 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `eval_id` | numeric | N |  |
| 2 | `seq` | numeric | N |  |
| 3 | `sub_seq` | numeric | N |  |
| 4 | `hint_condition` | character varying(4000) | Y |  |
| 5 | `hint_score` | character varying(4000) | Y |  |

- **PK:** `eval_id,seq,sub_seq`

<details><summary>Index</summary>

- `fes_evaluate_hint_leveltwo_pk` — `btree (eval_id, seq, sub_seq)`

</details>

### fes_evaluate_hint_leveltwo_bak_20260710

ประมาณ 321 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `eval_id` | numeric | Y |  |
| 2 | `seq` | numeric | Y |  |
| 3 | `sub_seq` | numeric | Y |  |
| 4 | `hint_condition` | character varying(4000) | Y |  |
| 5 | `hint_score` | character varying(4000) | Y |  |

### fes_evaluate_opt

ประมาณ 166,804 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluate_id` | numeric | N |  |
| 2 | `first_name` | character varying(100) | Y |  |
| 3 | `last_name` | character varying(100) | Y |  |
| 4 | `active_flag` | character varying(1) | Y |  |
| 5 | `create_id` | numeric | Y |  |
| 6 | `create_date` | date | Y |  |
| 7 | `modify_id` | numeric | Y |  |
| 8 | `modify_date` | date | Y |  |
| 9 | `user_id` | numeric | Y |  |
| 10 | `fullname` | character varying(100) | Y |  |

### fes_evaluate_opt_bak_20260710

ประมาณ 146,839 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluate_id` | numeric | Y |  |
| 2 | `first_name` | character varying(100) | Y |  |
| 3 | `last_name` | character varying(100) | Y |  |
| 4 | `active_flag` | character varying(1) | Y |  |
| 5 | `create_id` | numeric | Y |  |
| 6 | `create_date` | date | Y |  |
| 7 | `modify_id` | numeric | Y |  |
| 8 | `modify_date` | date | Y |  |
| 9 | `user_id` | numeric | Y |  |
| 10 | `fullname` | character varying(100) | Y |  |

### fes_evaluatedform

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedform_id` 🔑 | bigint | N |  |
| 2 | `start_month` | bigint | Y |  |
| 3 | `start_year` | bigint | Y |  |
| 4 | `end_month` | bigint | Y |  |
| 5 | `end_year` | bigint | Y |  |
| 6 | `total_point` | numeric(7,2) | Y |  |
| 7 | `create_id` | bigint | Y |  |
| 8 | `create_date` | timestamp without time zone | Y |  |
| 9 | `modify_id` | bigint | Y |  |
| 10 | `modify_date` | timestamp without time zone | Y |  |

- **PK:** `evaluatedform_id`

<details><summary>Index</summary>

- `fes_evaluatedform_pk` — `btree (evaluatedform_id)`
- `idx_fes_evaluatedform_pk` — `btree (evaluatedform_id)`

</details>

### fes_evaluatedform_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedform_id` | bigint | Y |  |
| 2 | `start_month` | bigint | Y |  |
| 3 | `start_year` | bigint | Y |  |
| 4 | `end_month` | bigint | Y |  |
| 5 | `end_year` | bigint | Y |  |
| 6 | `total_point` | numeric(7,2) | Y |  |
| 7 | `create_id` | bigint | Y |  |
| 8 | `create_date` | timestamp without time zone | Y |  |
| 9 | `modify_id` | bigint | Y |  |
| 10 | `modify_date` | timestamp without time zone | Y |  |

### fes_evaluatedform_title

ประมาณ 41 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedform_id` | numeric | Y |  |
| 2 | `title_id` | numeric | Y |  |
| 3 | `grade_id` | numeric | Y |  |
| 4 | `seq` | numeric | Y |  |
| 5 | `eval_level` | numeric | Y |  |
| 6 | `eval_level_id` | numeric | Y |  |

### fes_evaluatedform_title_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedform_id` | numeric | Y |  |
| 2 | `title_id` | numeric | Y |  |
| 3 | `grade_id` | numeric | Y |  |
| 4 | `seq` | numeric | Y |  |
| 5 | `eval_level` | numeric | Y |  |
| 6 | `eval_level_id` | numeric | Y |  |

### fes_evaluatedperson

ประมาณ 1,660,005 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedperson_id` | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `status` | character varying(2) | Y |  |
| 4 | `eval_date` | timestamp without time zone | Y |  |
| 5 | `eval_user` | bigint | Y |  |
| 6 | `submit_date` | timestamp without time zone | Y |  |
| 7 | `submit_user` | bigint | Y |  |
| 8 | `approve_date` | timestamp without time zone | Y |  |
| 9 | `approve_user` | bigint | Y |  |
| 10 | `verify_date` | timestamp without time zone | Y |  |
| 11 | `verify_user` | bigint | Y |  |
| 12 | `evaluate_id` | bigint | Y |  |
| 13 | `create_id` | bigint | Y |  |
| 14 | `create_date` | timestamp without time zone | Y |  |
| 15 | `modify_id` | bigint | Y |  |
| 16 | `modify_date` | timestamp without time zone | Y |  |

### fes_evaluatedperson_bak_20260710

ประมาณ 674 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `evaluatedperson_id` | bigint | Y |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `status` | character varying(2) | Y |  |
| 4 | `eval_date` | timestamp without time zone | Y |  |
| 5 | `eval_user` | bigint | Y |  |
| 6 | `submit_date` | timestamp without time zone | Y |  |
| 7 | `submit_user` | bigint | Y |  |
| 8 | `approve_date` | timestamp without time zone | Y |  |
| 9 | `approve_user` | bigint | Y |  |
| 10 | `verify_date` | timestamp without time zone | Y |  |
| 11 | `verify_user` | bigint | Y |  |
| 12 | `evaluate_id` | bigint | Y |  |
| 13 | `create_id` | bigint | Y |  |
| 14 | `create_date` | timestamp without time zone | Y |  |
| 15 | `modify_id` | bigint | Y |  |
| 16 | `modify_date` | timestamp without time zone | Y |  |

### fes_grade

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `grade_id` 🔑 | bigint | N |  |
| 2 | `start_month` | integer | N |  |
| 3 | `start_year` | integer | N |  |
| 4 | `end_month` | integer | Y |  |
| 5 | `end_year` | integer | Y |  |
| 6 | `create_id` | bigint | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | now() |
| 8 | `modify_id` | bigint | Y |  |
| 9 | `modify_date` | timestamp without time zone | Y |  |

- **PK:** `grade_id`

<details><summary>Index</summary>

- `fes_grade_pkey` — `btree (grade_id)`
- `idx_fes_grade_period` — `btree (start_year, start_month)`

</details>

### fes_grade_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `grade_id` | bigint | Y |  |
| 2 | `start_month` | integer | Y |  |
| 3 | `start_year` | integer | Y |  |
| 4 | `end_month` | integer | Y |  |
| 5 | `end_year` | integer | Y |  |
| 6 | `create_id` | bigint | Y |  |
| 7 | `create_date` | timestamp without time zone | Y |  |
| 8 | `modify_id` | bigint | Y |  |
| 9 | `modify_date` | timestamp without time zone | Y |  |

### fes_gradedetail

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `gradedetail_id` 🔑 | bigint | N |  |
| 2 | `grade_name` | character varying(2) | N |  |
| 3 | `min_score` | integer | Y |  |
| 4 | `max_score` | integer | Y |  |
| 5 | `fail_grade` | character varying(1) | N |  |
| 6 | `grade_id` | bigint | N |  |
| 7 | `min` | numeric | N |  |
| 8 | `max` | numeric | N |  |

- **PK:** `gradedetail_id`
- **FK:** `grade_id` → `fes_grade`.`grade_id`

<details><summary>Index</summary>

- `fes_gradedetail_pkey` — `btree (gradedetail_id)`
- `idx_fes_gradedetail_grade_id` — `btree (grade_id)`

</details>

### fes_gradedetail_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `gradedetail_id` | bigint | Y |  |
| 2 | `grade_name` | character varying(2) | Y |  |
| 3 | `min_score` | integer | Y |  |
| 4 | `max_score` | integer | Y |  |
| 5 | `fail_grade` | character varying(1) | Y |  |
| 6 | `grade_id` | bigint | Y |  |

### fes_importdata

ประมาณ 62,712 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `import_id` | numeric | N |  |
| 2 | `title_id` | numeric | N |  |
| 3 | `goal_get` | character varying(1) | Y |  |
| 4 | `mm` | character varying(2) | Y |  |
| 5 | `yy` | character varying(2) | Y |  |
| 6 | `branch_id` | numeric | N |  |
| 7 | `top_value` | numeric(14,2) | Y |  |
| 8 | `bottom_value` | numeric(14,2) | Y |  |
| 9 | `status` | character varying(1) | Y |  |
| 10 | `create_id` | numeric | Y |  |
| 11 | `create_date` | date | Y |  |
| 12 | `modify_id` | numeric | Y |  |
| 13 | `modify_date` | date | Y |  |
| 14 | `fr_store_order_id` | numeric | Y |  |
| 15 | `status_temp` | character varying(1) | Y |  |
| 16 | `premium_comment` | character varying | Y |  |

<details><summary>Index</summary>

- `idx_fes_importdata_branch_goal_yymm_title` — `btree (branch_id, goal_get, yy, mm, title_id)`
- `idx_fes_importdata_createdate` — `btree (create_date)`
- `idx_fes_importdata_import_id` — `btree (import_id)`
- `idx_fes_importdata_mm_order` — `btree (mm, fr_store_order_id)`
- `idx_fes_importdata_yy_mm` — `btree (yy, mm)`
- `idx_importdata_main` — `btree (title_id, branch_id, mm, yy) WHERE ((status)::text = 'Y'::text)`

</details>

### fes_importdata_bak_20260710

ประมาณ 12,096,393 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `import_id` | numeric | Y |  |
| 2 | `title_id` | numeric | Y |  |
| 3 | `goal_get` | character varying(1) | Y |  |
| 4 | `mm` | character varying(2) | Y |  |
| 5 | `yy` | character varying(2) | Y |  |
| 6 | `branch_id` | numeric | Y |  |
| 7 | `top_value` | numeric(14,2) | Y |  |
| 8 | `bottom_value` | numeric(14,2) | Y |  |
| 9 | `status` | character varying(1) | Y |  |
| 10 | `create_id` | numeric | Y |  |
| 11 | `create_date` | date | Y |  |
| 12 | `modify_id` | numeric | Y |  |
| 13 | `modify_date` | date | Y |  |
| 14 | `fr_store_order_id` | numeric | Y |  |
| 15 | `status_temp` | character varying(1) | Y |  |
| 16 | `premium_comment` | character varying | Y |  |

### fes_properties

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `properties_id` | numeric | N |  |
| 2 | `name` | character varying(100) | Y |  |
| 3 | `value` | character varying(100) | Y |  |

### fes_reward

ประมาณ 59,325 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `reward_id` | integer | Y |  |
| 2 | `store_id` | integer | Y |  |
| 3 | `year` | integer | Y |  |
| 4 | `point_service` | numeric(5,2) | Y |  |
| 5 | `rank_service` | character varying(255) | Y |  |
| 6 | `reward_bos` | character varying(255) | Y |  |
| 7 | `point_quality` | numeric(5,2) | Y |  |
| 8 | `rank_quality` | integer | Y |  |
| 9 | `reward_boq` | character varying(255) | Y |  |
| 10 | `point_600` | numeric(5,2) | Y |  |
| 11 | `rank_600` | integer | Y |  |
| 12 | `avg_qssi` | numeric(5,2) | Y |  |
| 13 | `point_division` | integer | Y |  |
| 14 | `rank_division` | integer | Y |  |
| 15 | `reward_division` | character varying(255) | Y |  |
| 16 | `count_e` | character varying(255) | Y |  |
| 17 | `remark` | character varying(255) | Y |  |
| 18 | `ref1` | character varying(255) | Y |  |
| 19 | `ref2` | character varying(255) | Y |  |
| 20 | `ref3` | character varying(255) | Y |  |
| 21 | `ref4` | character varying(255) | Y |  |
| 22 | `ref5` | character varying(255) | Y |  |
| 23 | `create_date` | timestamp without time zone | Y |  |
| 24 | `create_user` | character varying(255) | Y |  |
| 25 | `update_date` | timestamp without time zone | Y |  |
| 26 | `update_user` | character varying(255) | Y |  |
| 27 | `grade_summary` | character varying(255) | Y |  |
| 28 | `first_reward_division` | integer | Y |  |
| 29 | `confirm_division` | character(1) | Y |  |
| 30 | `point_cr_service` | integer | Y |  |
| 31 | `point_cr_quality` | integer | Y |  |
| 32 | `store_division_flag` | character(1) | Y |  |
| 33 | `active_flag` | character(1) | Y |  |
| 34 | `order_id` | bigint | Y |  |
| 35 | `store_the_best_flag` | character(1) | Y |  |

### fes_reward_bak_20260710

ประมาณ 51,658 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `reward_id` | integer | Y |  |
| 2 | `store_id` | integer | Y |  |
| 3 | `year` | integer | Y |  |
| 4 | `point_service` | numeric(5,2) | Y |  |
| 5 | `rank_service` | character varying(255) | Y |  |
| 6 | `reward_bos` | character varying(255) | Y |  |
| 7 | `point_quality` | numeric(5,2) | Y |  |
| 8 | `rank_quality` | integer | Y |  |
| 9 | `reward_boq` | character varying(255) | Y |  |
| 10 | `point_600` | numeric(5,2) | Y |  |
| 11 | `rank_600` | integer | Y |  |
| 12 | `avg_qssi` | numeric(5,2) | Y |  |
| 13 | `point_division` | integer | Y |  |
| 14 | `rank_division` | integer | Y |  |
| 15 | `reward_division` | character varying(255) | Y |  |
| 16 | `count_e` | character varying(255) | Y |  |
| 17 | `remark` | character varying(255) | Y |  |
| 18 | `ref1` | character varying(255) | Y |  |
| 19 | `ref2` | character varying(255) | Y |  |
| 20 | `ref3` | character varying(255) | Y |  |
| 21 | `ref4` | character varying(255) | Y |  |
| 22 | `ref5` | character varying(255) | Y |  |
| 23 | `create_date` | timestamp without time zone | Y |  |
| 24 | `create_user` | character varying(255) | Y |  |
| 25 | `update_date` | timestamp without time zone | Y |  |
| 26 | `update_user` | character varying(255) | Y |  |
| 27 | `grade_summary` | character varying(255) | Y |  |
| 28 | `first_reward_division` | integer | Y |  |
| 29 | `confirm_division` | character(1) | Y |  |
| 30 | `point_cr_service` | integer | Y |  |
| 31 | `point_cr_quality` | integer | Y |  |
| 32 | `store_division_flag` | character(1) | Y |  |
| 33 | `active_flag` | character(1) | Y |  |
| 34 | `order_id` | bigint | Y |  |
| 35 | `store_the_best_flag` | character(1) | Y |  |

### fes_reward_duration

ประมาณ 42 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `year_reward` | smallint | N |  |
| 2 | `process_year` | smallint | N |  |
| 3 | `start_month` | smallint | N |  |
| 4 | `start_year` | smallint | N |  |
| 5 | `end_month` | smallint | N |  |
| 6 | `end_year` | smallint | N |  |
| 7 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 10 | `update_by` | character varying(20) | Y |  |
| 11 | `process_flag` | character(1) | Y | 'N'::bpchar |
| 12 | `type` | character varying(20) | N |  |

- **PK:** `year_reward,type`

<details><summary>Index</summary>

- `fes_reward_duration_pk` — `btree (year_reward, type)`

</details>

### fes_reward_duration_bak_20260710

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `year_reward` | smallint | Y |  |
| 2 | `process_year` | smallint | Y |  |
| 3 | `start_month` | smallint | Y |  |
| 4 | `start_year` | smallint | Y |  |
| 5 | `end_month` | smallint | Y |  |
| 6 | `end_year` | smallint | Y |  |
| 7 | `create_date` | timestamp without time zone | Y |  |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y |  |
| 10 | `update_by` | character varying(20) | Y |  |
| 11 | `process_flag` | character(1) | Y |  |
| 12 | `type` | character varying(20) | Y |  |

### fes_reward_grade

ประมาณ 36,656 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `reward_grade_id` 🔑 | bigint | N | nextval('seq_fes_reward_grade'::regclass) |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | integer | Y |  |
| 4 | `month` | integer | Y |  |
| 5 | `grade` | character varying(2) | Y |  |
| 6 | `point_percent` | numeric(7,2) | Y |  |
| 7 | `total_point` | numeric(7,2) | Y |  |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `create_date` | timestamp without time zone | Y |  |
| 10 | `grade_count_e` | integer | Y | 0 |
| 11 | `order_id` | bigint | Y |  |

- **PK:** `reward_grade_id`

<details><summary>Index</summary>

- `fes_reward_grade_idx1` — `btree (store_id, month, year)`
- `fes_reward_grade_pkey` — `btree (reward_grade_id)`

</details>

### fes_reward_grade_all

ประมาณ 150,000 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` | integer | N |  |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | integer | N |  |
| 4 | `month` | integer | N |  |
| 5 | `grade` | character varying(2) | Y |  |
| 6 | `point_percent` | numeric(7,2) | Y |  |
| 7 | `total_point` | numeric(7,2) | Y |  |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `create_date` | timestamp with time zone | Y |  |
| 10 | `update_by` | character varying(20) | Y |  |
| 11 | `update_date` | timestamp with time zone | Y |  |
| 12 | `active_flag` | character(1) | Y | 'Y'::bpchar |
| 13 | `is_adjust` | character varying(1) | Y | 'N'::character varying |

- **PK:** `order_id,year,month`

<details><summary>Index</summary>

- `fes_reward_grade_all_pk` — `btree (order_id, year, month)`

</details>

### fes_reward_grade_all_bak_20260710

ประมาณ 923 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` | integer | Y |  |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | integer | Y |  |
| 4 | `month` | integer | Y |  |
| 5 | `grade` | character varying(2) | Y |  |
| 6 | `point_percent` | numeric(7,2) | Y |  |
| 7 | `total_point` | numeric(7,2) | Y |  |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `create_date` | timestamp with time zone | Y |  |
| 10 | `update_by` | character varying(20) | Y |  |
| 11 | `update_date` | timestamp with time zone | Y |  |
| 12 | `active_flag` | character(1) | Y |  |
| 13 | `is_adjust` | character varying(1) | Y |  |

### fes_reward_grade_bak_20260710

ประมาณ 34,695 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `reward_grade_id` | bigint | Y |  |
| 2 | `store_id` | character varying(5) | Y |  |
| 3 | `year` | integer | Y |  |
| 4 | `month` | integer | Y |  |
| 5 | `grade` | character varying(2) | Y |  |
| 6 | `point_percent` | numeric(7,2) | Y |  |
| 7 | `total_point` | numeric(7,2) | Y |  |
| 8 | `create_by` | character varying(20) | Y |  |
| 9 | `create_date` | timestamp without time zone | Y |  |
| 10 | `grade_count_e` | integer | Y |  |
| 11 | `order_id` | bigint | Y |  |

### fes_title

ประมาณ 20 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `title_id` 🔑 | integer | N | nextval('fes_title_seq'::regclass) |
| 2 | `title` | character varying(255) | N |  |
| 3 | `type` | USER-DEFINED | N | 'score'::title_type_enum |
| 4 | `status` | character(1) | Y | 'Y'::bpchar |
| 5 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 6 | `seq` | bigint | N | 0 |

- **PK:** `title_id`

<details><summary>Index</summary>

- `fes_title_pkey_v` — `btree (title_id)`
- `idx_fes_title_title` — `btree (title)`

</details>

### fml_authorize

ประมาณ 16,178 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `auth_id` 🔑 | bigint | N | nextval('fml_authorize_auth_id_seq'::regclass) |
| 2 | `type` | character varying(20) | Y |  |
| 3 | `group_id` | numeric | N |  |
| 4 | `item_id` | numeric | Y |  |
| 5 | `bu_id` | character varying(20) | Y |  |
| 6 | `news_type_id` | numeric | Y |  |
| 7 | `perm_id` | character varying(20) | Y |  |
| 8 | `auth` | character varying(3) | N | 'yes'::character varying |
| 9 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 10 | `create_user` | character varying(100) | Y |  |
| 11 | `modify_date` | timestamp without time zone | Y |  |
| 12 | `modify_user` | character varying(100) | Y |  |

- **PK:** `auth_id`

<details><summary>Index</summary>

- `fml_authorize_pkey` — `btree (auth_id)`

</details>

### fml_bell_group_report

ประมาณ 144 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` | bigint | Y |  |
| 2 | `zone_name` | character varying(5) | Y |  |
| 3 | `report_type` | character varying(20) | Y |  |
| 4 | `update_user` | character varying(200) | Y |  |
| 5 | `update_date` | timestamp without time zone | Y |  |

### fml_bell_user

ประมาณ 97 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `bell_user_id` | bigint | Y |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `region` | character varying(3) | Y |  |
| 4 | `emp_id` | character varying(20) | Y |  |
| 5 | `title_code` | character varying(2) | Y |  |
| 6 | `first_name` | character varying(100) | Y |  |
| 7 | `last_name` | character varying(100) | Y |  |
| 8 | `first_name_en` | character varying(100) | Y |  |
| 9 | `last_name_en` | character varying(100) | Y |  |
| 10 | `id_card` | character varying(20) | Y |  |
| 11 | `birthday` | date | Y |  |
| 12 | `address` | character varying(500) | Y |  |
| 13 | `email` | character varying(100) | Y |  |
| 14 | `mobile_phone` | character varying(100) | Y |  |
| 15 | `bell_emp_type` | character varying(50) | Y |  |
| 16 | `position` | character varying(100) | Y |  |
| 17 | `hire_date` | date | Y |  |
| 18 | `bell_user_status` | character varying(2) | Y |  |
| 19 | `is_active` | character varying(2) | Y |  |
| 20 | `user_principal_name` | character varying(100) | Y |  |
| 21 | `delivery_id` | character varying(15) | Y |  |
| 22 | `create_user` | character varying(20) | Y | '0'::character varying |
| 23 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 24 | `update_user` | character varying(20) | Y | '0'::character varying |
| 25 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 26 | `bell_user_type` | character varying(2) | Y | '2'::character varying |

### fml_bell_user_group

ประมาณ 95 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `bell_user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |
| 3 | `update_user` | character varying(200) | Y | '0'::character varying |
| 4 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 5 | `user_id` | bigint | Y |  |

### fml_bell_user_store

ประมาณ 131 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `bell_user_id` | bigint | Y |  |
| 3 | `store_id` | character varying(10) | Y |  |
| 4 | `update_user` | character varying(200) | Y | '0'::character varying |
| 5 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

### fml_bellinee_statement

ประมาณ 59,806 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` | bigint | N |  |
| 2 | `report_type` | character varying(20) | N |  |
| 3 | `file_id` | bigint | Y |  |
| 4 | `store_id` | character varying(20) | N |  |
| 5 | `year` | character varying(4) | N |  |
| 6 | `month` | character varying(2) | N |  |
| 7 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 8 | `update_date` | timestamp without time zone | Y |  |
| 9 | `action_date` | timestamp without time zone | Y |  |
| 10 | `action_flag` | character varying(1) | Y |  |
| 11 | `day` | character varying(2) | Y |  |

### fml_bellinee_statement_file

ประมาณ 59,822 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_id` | bigint | N |  |
| 2 | `file_name` | character varying(1000) | Y |  |
| 3 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 4 | `create_user` | character varying(100) | Y |  |
| 5 | `delete_flag` | character varying(1) | Y |  |
| 6 | `content` | bytea | Y |  |
| 7 | `content_type` | character varying(30) | Y |  |
| 8 | `report_type` | character varying(20) | Y |  |
| 9 | `store_id` | character varying(20) | Y |  |
| 10 | `year` | character varying(4) | Y |  |
| 11 | `month` | character varying(2) | Y |  |

### fml_cooperation_topic

ประมาณ 87 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `code_type` | character varying(20) | Y |  |
| 3 | `seq_no` | smallint | Y |  |
| 4 | `sub_seq_no` | smallint | Y |  |
| 5 | `topic` | character varying(1000) | Y |  |
| 6 | `description` | character varying(1000) | Y |  |
| 7 | `count_warning_speech` | smallint | Y |  |
| 8 | `active_flag` | character varying(1) | Y | 'Y'::character varying |
| 9 | `create_user` | character varying(100) | Y |  |
| 10 | `create_date` | date | Y | CURRENT_DATE |
| 11 | `update_user` | character varying(100) | Y |  |
| 12 | `update_date` | date | Y |  |
| 13 | `code_value` | character varying(25) | Y |  |
| 14 | `operated_store_partner` | smallint | Y |  |
| 15 | `operated_not_store_partner` | smallint | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_cooperation_topic_pk` — `btree (id)`

</details>

### fml_cooperation_topic_backup

ประมาณ 63 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `code_type` | character varying(20) | Y |  |
| 3 | `seq_no` | smallint | Y |  |
| 4 | `sub_seq_no` | smallint | Y |  |
| 5 | `topic` | character varying(1000) | Y |  |
| 6 | `description` | character varying(1000) | Y |  |
| 7 | `count_warning_speech` | smallint | Y |  |
| 8 | `active_flag` | character varying(1) | Y | 'Y'::character varying |
| 9 | `create_user` | character varying(100) | Y |  |
| 10 | `create_date` | date | Y | CURRENT_DATE |
| 11 | `update_user` | character varying(100) | Y |  |
| 12 | `update_date` | date | Y |  |
| 13 | `code_value` | character varying(25) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_cooperation_topic_pk_1` — `btree (id)`

</details>

### fml_cooperation_topic_backup_20260703

ประมาณ 87 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` | bigint | Y |  |
| 2 | `code_type` | character varying(20) | Y |  |
| 3 | `seq_no` | smallint | Y |  |
| 4 | `sub_seq_no` | smallint | Y |  |
| 5 | `topic` | character varying(1000) | Y |  |
| 6 | `description` | character varying(1000) | Y |  |
| 7 | `count_warning_speech` | smallint | Y |  |
| 8 | `active_flag` | character varying(1) | Y |  |
| 9 | `create_user` | character varying(100) | Y |  |
| 10 | `create_date` | date | Y |  |
| 11 | `update_user` | character varying(100) | Y |  |
| 12 | `update_date` | date | Y |  |
| 13 | `code_value` | character varying(25) | Y |  |
| 14 | `operated_store_partner` | smallint | Y |  |
| 15 | `operated_not_store_partner` | smallint | Y |  |

### fml_cooperation_trn

ประมาณ 19,236 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `trn_id` 🔑 | bigint | N |  |
| 2 | `doc_number` | character varying(25) | Y |  |
| 3 | `topic_main_id` | smallint | Y |  |
| 4 | `topic_sub_id` | character varying(100) | Y |  |
| 5 | `store_id` | character varying(10) | Y |  |
| 6 | `create_by` | bigint | Y |  |
| 7 | `create_date` | date | Y | CURRENT_DATE |
| 8 | `update_by` | bigint | Y |  |
| 9 | `update_date` | date | Y |  |
| 10 | `doc_type` | smallint | Y |  |
| 11 | `requestor_detail1` | character varying(4000) | Y |  |
| 12 | `requestor_detail2` | character varying(4000) | Y |  |
| 13 | `requestor_detail3` | character varying(4000) | Y |  |
| 14 | `period_start` | character varying(10) | Y |  |
| 15 | `period_end` | character varying(10) | Y |  |
| 16 | `improve_detail` | character varying(4000) | Y |  |
| 17 | `improve_deadline` | date | Y |  |
| 18 | `year` | character varying(4) | Y |  |
| 19 | `create_by_position_lvl` | character varying(20) | Y |  |
| 20 | `operate_by` | smallint | Y |  |

- **PK:** `trn_id`

<details><summary>Index</summary>

- `fml_cooperation_trn_index1` — `btree (doc_number)`
- `fml_cooperation_trn_index2` — `btree (store_id)`
- `fml_cooperation_trn_pk` — `btree (trn_id)`

</details>

### fml_email_account

ประมาณ 1,646 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | numeric | N |  |
| 2 | `template_id` | numeric | N |  |
| 3 | `email` | character varying(4000) | N |  |
| 4 | `create_by` | numeric | Y |  |
| 5 | `create_date` | timestamp without time zone | Y |  |
| 6 | `update_by` | numeric | Y |  |
| 7 | `update_date` | timestamp without time zone | Y |  |
| 8 | `remark` | character varying(4000) | Y |  |

- **PK:** `user_id,template_id,email`

<details><summary>Index</summary>

- `fml_email_account_pk` — `btree (user_id, template_id, email)`

</details>

### fml_franchise_statement

REPORT_TYE = 'RT040079' ACTION_FLAG เพื่อยืนยันรับทราบ ('Y') · ประมาณ 1,571,559 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('fml_franchise_statement_id_seq'::regclass) |
| 2 | `report_type` | character varying(20) | N |  |
| 3 | `file_id` | bigint | N |  |
| 4 | `store_id` | character varying(20) | N |  |
| 5 | `year` | character varying(4) | N |  |
| 6 | `month` | character varying(2) | N |  |
| 7 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 8 | `update_date` | timestamp without time zone | Y |  |
| 9 | `action_flag` | character varying(1) | Y |  |
| 10 | `action_date` | timestamp without time zone | Y |  |
| 11 | `day` | character varying(2) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_franchise_statement_idx` — `btree (report_type, file_id, store_id, year, month, id)`
- `fml_franchise_statement_pkey` — `btree (id)`

</details>

### fml_franchise_statement_file

ประมาณ 5,730 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_id` 🔑 | bigint | N |  |
| 2 | `file_name` | character varying(1000) | Y |  |
| 3 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 4 | `create_user` | character varying(100) | Y |  |
| 5 | `delete_flag` | character varying(1) | Y |  |
| 6 | `content` | bytea | Y |  |
| 7 | `content_type` | character varying(30) | Y |  |
| 8 | `report_type` | character varying(20) | Y |  |
| 9 | `store_id` | character varying(20) | Y |  |
| 10 | `year` | character varying(4) | Y |  |
| 11 | `month` | character varying(2) | Y |  |

- **PK:** `file_id`

<details><summary>Index</summary>

- `fml_franchise_stmt_file_idx` — `btree (report_type, store_id, year, month, file_name)`
- `fml_statement_file_pk` — `btree (file_id)`

</details>

### fml_franchise_statement_group

ประมาณ 963 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` | numeric | Y |  |
| 2 | `report_type` | character varying(100) | Y |  |

<details><summary>Index</summary>

- `idx_stmt_perf_ffsg_report_group` — `btree (report_type, group_id)`

</details>

### fml_fs_other

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('fml_fs_other_id_seq'::regclass) |
| 2 | `branch_id` | character varying(5) | N |  |
| 3 | `branch_name` | text | N |  |
| 4 | `fr_type` | text | N |  |
| 5 | `acc_accountant` | character varying(100) | Y |  |
| 6 | `acc_manager` | character varying(100) | Y |  |
| 7 | `account_code` | character varying(20) | N |  |
| 8 | `dr_desc` | text | N |  |
| 9 | `amount` | numeric | N |  |
| 10 | `cr_desc` | text | Y |  |
| 11 | `period` | date | N |  |
| 12 | `create_date` | timestamp with time zone | N | now() |
| 13 | `create_user` | character varying(100) | Y |  |
| 14 | `file_id` | integer | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_fs_other_pkey` — `btree (id)`

</details>

### fml_pre_statement

ประมาณ 185,179 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `trn_id` 🔑 | bigint | N | nextval('fml_pre_statement_trn_id_seq'::regclass) |
| 2 | `year` | character varying(4) | Y |  |
| 3 | `month` | character varying(2) | Y |  |
| 4 | `day` | character varying(2) | Y |  |
| 5 | `store_id` | character varying(10) | Y |  |
| 6 | `store_name` | character varying(200) | Y |  |
| 7 | `struct` | character varying(200) | Y |  |
| 8 | `budget` | numeric(17,2) | Y |  |
| 9 | `previous_day_6` | numeric(17,2) | Y |  |
| 10 | `previous_day_5` | numeric(17,2) | Y |  |
| 11 | `previous_day_4` | numeric(17,2) | Y |  |
| 12 | `previous_day_3` | numeric(17,2) | Y |  |
| 13 | `previous_day_2` | numeric(17,2) | Y |  |
| 14 | `previous_day_1` | numeric(17,2) | Y |  |
| 15 | `previous_day_0` | numeric(17,2) | Y |  |
| 16 | `collected_week_1_sale` | numeric(17,2) | Y |  |
| 17 | `collected_week_1_percent` | numeric(17,2) | Y |  |
| 18 | `collected_week_2_sale` | numeric(17,2) | Y |  |
| 19 | `collected_week_2_percent` | numeric(17,2) | Y |  |
| 20 | `collected_week_3_sale` | numeric(17,2) | Y |  |
| 21 | `collected_week_3_percent` | numeric(17,2) | Y |  |
| 22 | `collected_week_4_sale` | numeric(17,2) | Y |  |
| 23 | `collected_week_4_percent` | numeric(17,2) | Y |  |
| 24 | `collected_month_sale` | numeric(17,2) | Y |  |
| 25 | `collected_month_percent` | numeric(17,2) | Y |  |
| 26 | `value` | numeric(17,2) | Y |  |
| 27 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 28 | `create_by` | character varying(50) | Y |  |
| 29 | `update_date` | timestamp without time zone | Y |  |
| 30 | `update_by` | character varying(50) | Y |  |

- **PK:** `trn_id`

<details><summary>Index</summary>

- `fml_pre_statement_idx1` — `btree (trn_id, year, month, day) WITH (fillfactor='90')`
- `fml_pre_statement_pkey` — `btree (trn_id)`

</details>

### fml_responsible_sbp

ประมาณ 101 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `responsible_sbp_id` 🔑 | numeric | N | nextval('fml_responsible_sbp_seq'::regclass) |
| 2 | `store_ptt` | character varying(2) | N |  |
| 3 | `region` | character varying(100) | N |  |
| 4 | `name` | character varying(200) | Y |  |
| 5 | `position` | character varying(100) | Y |  |
| 6 | `email` | character varying(100) | N |  |
| 7 | `tel` | character varying(100) | Y |  |
| 8 | `create_date` | timestamp without time zone | Y | now() |
| 9 | `create_by` | character varying(20) | Y | 'system'::character varying |
| 10 | `update_date` | timestamp without time zone | Y | now() |
| 11 | `update_by` | character varying(20) | Y | 'system'::character varying |

- **PK:** `responsible_sbp_id`

<details><summary>Index</summary>

- `fml_responsible_sbp_pkey` — `btree (responsible_sbp_id)`

</details>

### fml_sbp_show_report

ประมาณ 16 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `period` | character varying(6) | N |  |
| 2 | `report_type` | character varying(15) | N |  |
| 3 | `create_by` | character varying(100) | Y |  |
| 4 | `create_date` | timestamp without time zone | Y |  |
| 5 | `active_flag` | character varying(1) | Y |  |
| 6 | `import_date` | timestamp without time zone | N | now() |

- **PK:** `period,report_type`

<details><summary>Index</summary>

- `idx_show_report_period` — `btree (period)`
- `pk_fml_sbp_show_report` — `btree (period, report_type)`

</details>

### fml_sbp_skip_report_store

ประมาณ 5 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_tax_id` | character varying(13) | Y |  |
| 2 | `start_date` | timestamp without time zone | N |  |
| 3 | `end_date` | timestamp without time zone | N |  |
| 4 | `create_date` | timestamp without time zone | Y | now() |
| 5 | `create_user` | character varying(255) | N |  |
| 6 | `update_date` | timestamp without time zone | N | now() |
| 7 | `update_user` | character varying(255) | N |  |
| 8 | `file_name` | character varying(50) | Y |  |
| 9 | `period` | character varying(6) | Y |  |
| 10 | `store_id` | character varying(5) | Y |  |
| 11 | `active_flag` | character varying(1) | Y |  |
| 12 | `id` 🔑 | bigint | N | nextval('fml_sbp_skip_report_store_id_seq'::regclass) |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_sbp_skip_report_store_pkey` — `btree (id)`

</details>

### fml_sbp_stmt

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `sbp_stmt_id` 🔑 | bigint | N | nextval('fml_sbp_stmt_sbp_stmt_id_seq'::regclass) |
| 2 | `process_id` | character varying(15) | Y |  |
| 3 | `report_type` | character varying(20) | Y |  |
| 4 | `store_id` | character varying(20) | Y |  |
| 5 | `year` | character varying(4) | Y |  |
| 6 | `month` | character varying(2) | Y |  |
| 7 | `day` | character varying(2) | Y |  |
| 8 | `report_link` | character varying(4000) | Y |  |
| 9 | `create_user` | character varying(4000) | Y |  |
| 10 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 11 | `update_user` | character varying(4000) | Y |  |
| 12 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 13 | `action_flag` | character varying(1) | Y |  |
| 14 | `action_date` | timestamp without time zone | Y |  |
| 15 | `document_id` | character varying(20) | Y |  |
| 16 | `channel_tran_id` | character varying(100) | Y |  |

- **PK:** `sbp_stmt_id`

<details><summary>Index</summary>

- `UQ_FML_SBP_STMT_KEY` — `btree (process_id, report_type, store_id, year, month, document_id, day)`
- `fml_sbp_stmt_pkey` — `btree (sbp_stmt_id)`
- `idx_fml_sbp_store_report` — `btree (store_id, report_type)`
- `idx_stmt_perf_fml_sbp_daily` — `btree (report_type, ((((year)::text || lpad((month)::text, 2, '0'::text)) || lpad((day)::text, 2, '0'::text))), store_id) INCLUDE (channel_tran_id, year, month, day) WHERE ((day IS NOT NULL) AND ((day)::text <> ''::text))`
- `idx_stmt_perf_fml_sbp_monthly` — `btree (report_type, (((year)::text || lpad((month)::text, 2, '0'::text))), store_id) INCLUDE (channel_tran_id, year, month, day) WHERE ((day IS NULL) OR ((day)::text = ''::text))`

</details>

### fml_stacc_fr_stmt

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` | character varying(15) | Y |  |
| 2 | `report_type` | character varying(15) | Y |  |
| 3 | `branch` | character varying(20) | Y |  |
| 4 | `year` | character varying(4) | Y |  |
| 5 | `month` | character varying(2) | Y |  |
| 6 | `ws_date` | timestamp with time zone | Y |  |
| 7 | `import_flag` | smallint | Y |  |
| 8 | `import_remark` | character varying(4000) | Y |  |
| 9 | `import_date` | timestamp with time zone | Y |  |
| 10 | `send_mail_flag` | smallint | Y |  |
| 11 | `send_mail_remark` | character varying(4000) | Y |  |
| 12 | `send_mail_date` | timestamp with time zone | Y |  |

<details><summary>Index</summary>

- `fml_stacc_fr_stmt_index1` — `btree (report_type, branch, year, month)`

</details>

### fml_stacc_fr_stmt_end

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` | character varying(15) | Y |  |
| 2 | `end_process_date` | timestamp with time zone | Y |  |
| 3 | `sum_process` | integer | Y |  |
| 4 | `report_type` | character varying(15) | Y |  |
| 5 | `remark` | character varying(4000) | Y |  |

- **UNIQUE:** `process_id`

<details><summary>Index</summary>

- `fml_stacc_fr_stmt_end_index1` — `btree (report_type)`
- `fml_stacc_fr_stmt_end_process_id_key` — `btree (process_id)`

</details>

### fml_stmt_end

ประมาณ 8 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `stmt_end_id` 🔑 | bigint | N |  |
| 2 | `process_id` | character varying(15) | Y |  |
| 3 | `sum_process` | integer | Y |  |
| 4 | `report_type` | character varying(20) | Y |  |
| 5 | `remark` | character varying(4000) | Y |  |
| 6 | `create_user` | character varying(4000) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 8 | `update_user` | character varying(4000) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `stmt_end_id`

<details><summary>Index</summary>

- `UQ_FML_STMT_END_KEY` — `btree (process_id, report_type)`
- `fml_stmt_end_pkey` — `btree (stmt_end_id)`

</details>

### fml_stmt_trans

ประมาณ 85 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `stmt_trans_id` 🔑 | bigint | N |  |
| 2 | `process_id` | character varying(15) | Y |  |
| 3 | `report_type` | character varying(20) | Y |  |
| 4 | `branch` | character varying(20) | Y |  |
| 5 | `year` | character varying(4) | Y |  |
| 6 | `month` | character varying(2) | Y |  |
| 7 | `day` | character varying(2) | Y |  |
| 8 | `document_id` | character varying(20) | Y |  |
| 9 | `report_link` | character varying(4000) | Y |  |
| 10 | `channel_tran_id` | character varying(100) | Y |  |
| 11 | `send_email_flag` | integer | Y |  |
| 12 | `send_email_remark` | character varying(4000) | Y |  |
| 13 | `send_email_date` | timestamp without time zone | Y |  |
| 14 | `create_user` | character varying(4000) | Y |  |
| 15 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `stmt_trans_id`

<details><summary>Index</summary>

- `fml_stmt_trans_pkey` — `btree (stmt_trans_id)`

</details>

### fml_sub_group_mapping

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` | bigint | Y |  |
| 2 | `sp` | character varying(1) | Y |  |
| 3 | `mn` | character varying(1) | Y |  |
| 4 | `dv` | character varying(1) | Y |  |
| 5 | `ot` | character varying(1) | Y |  |

### fml_sub_group_report

ประมาณ 126 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` | bigint | Y |  |
| 2 | `zone_name` | character varying(5) | Y |  |
| 3 | `report_type` | character varying(20) | Y |  |
| 4 | `update_user` | character varying(200) | Y |  |
| 5 | `update_date` | timestamp without time zone | Y |  |

### fml_sub_organize

ประมาณ 960 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(20) | Y |  |
| 2 | `name` | character varying(200) | Y |  |
| 3 | `tel` | character varying(100) | Y |  |
| 4 | `other` | character varying(100) | Y |  |
| 5 | `address` | character varying(500) | Y |  |
| 6 | `sup_id` | character varying(20) | Y |  |
| 7 | `sup_name` | character varying(200) | Y |  |
| 8 | `sp_page_no` | character varying(20) | Y |  |
| 9 | `sp_tel_no` | character varying(20) | Y |  |
| 10 | `sp_e_mail` | character varying(100) | Y |  |
| 11 | `sp_note_name` | character varying(100) | Y |  |
| 12 | `sp_other` | character varying(100) | Y |  |
| 13 | `mn_id` | character varying(20) | Y |  |
| 14 | `mn_name` | character varying(200) | Y |  |
| 15 | `mn_page_no` | character varying(20) | Y |  |
| 16 | `mn_tel_no` | character varying(20) | Y |  |
| 17 | `mn_e_mail` | character varying(100) | Y |  |
| 18 | `mn_note_name` | character varying(100) | Y |  |
| 19 | `mn_other` | character varying(100) | Y |  |
| 20 | `dv_id` | character varying(20) | Y |  |
| 21 | `dv_name` | character varying(200) | Y |  |
| 22 | `dv_page_no` | character varying(20) | Y |  |
| 23 | `dv_tel_no` | character varying(20) | Y |  |
| 24 | `dv_e_mail` | character varying(100) | Y |  |
| 25 | `dv_note_name` | character varying(100) | Y |  |
| 26 | `dv_other` | character varying(100) | Y |  |
| 27 | `agm_id` | character varying(20) | Y |  |
| 28 | `agm_name` | character varying(200) | Y |  |
| 29 | `agm_page_no` | character varying(20) | Y |  |
| 30 | `agm_tel_no` | character varying(20) | Y |  |
| 31 | `agm_e_mail` | character varying(100) | Y |  |
| 32 | `agm_note_name` | character varying(100) | Y |  |
| 33 | `agm_other` | character varying(100) | Y |  |
| 34 | `gm_id` | character varying(20) | Y |  |
| 35 | `gm_name` | character varying(200) | Y |  |
| 36 | `gm_page_no` | character varying(20) | Y |  |
| 37 | `gm_tel_no` | character varying(20) | Y |  |
| 38 | `gm_e_mail` | character varying(100) | Y |  |
| 39 | `gm_note_name` | character varying(100) | Y |  |
| 40 | `gm_other` | character varying(100) | Y |  |
| 41 | `area_id` | character varying(5) | Y |  |

### fml_sub_pre_statement

ประมาณ 61,162 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `trn_id` | bigint | N | nextval('fml_sub_pre_statement_trn_id_seq'::regclass) |
| 2 | `year` | character varying(4) | Y |  |
| 3 | `month` | character varying(2) | Y |  |
| 4 | `day` | character varying(2) | Y |  |
| 5 | `store_id` | character varying(10) | Y |  |
| 6 | `store_name` | character varying(200) | Y |  |
| 7 | `struct` | character varying(200) | Y |  |
| 8 | `budget` | numeric(10,2) | Y |  |
| 9 | `previous_day_6` | numeric(10,2) | Y |  |
| 10 | `previous_day_5` | numeric(10,2) | Y |  |
| 11 | `previous_day_4` | numeric(10,2) | Y |  |
| 12 | `previous_day_3` | numeric(10,2) | Y |  |
| 13 | `previous_day_2` | numeric(10,2) | Y |  |
| 14 | `previous_day_1` | numeric(10,2) | Y |  |
| 15 | `previous_day_0` | numeric(10,2) | Y |  |
| 16 | `collected_week_1_sale` | numeric(10,2) | Y |  |
| 17 | `collected_week_1_percent` | numeric(10,2) | Y |  |
| 18 | `collected_week_2_sale` | numeric(10,2) | Y |  |
| 19 | `collected_week_2_percent` | numeric(10,2) | Y |  |
| 20 | `collected_week_3_sale` | numeric(10,2) | Y |  |
| 21 | `collected_week_3_percent` | numeric(10,2) | Y |  |
| 22 | `collected_week_4_sale` | numeric(10,2) | Y |  |
| 23 | `collected_week_4_percent` | numeric(10,2) | Y |  |
| 24 | `collected_month_sale` | numeric(10,2) | Y |  |
| 25 | `collected_month_percent` | numeric(10,2) | Y |  |
| 26 | `value` | numeric(10,2) | Y |  |
| 27 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 28 | `create_by` | character varying(50) | Y |  |
| 29 | `update_date` | timestamp without time zone | Y |  |
| 30 | `update_by` | character varying(50) | Y |  |

<details><summary>Index</summary>

- `fml_sub_pre_statement_idx1` — `btree (trn_id, year, month, day)`

</details>

### fml_sub_user_group

ประมาณ 305 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |
| 3 | `update_user` | character varying(200) | Y |  |
| 4 | `update_date` | timestamp without time zone | Y |  |
| 5 | `sub_user_id` | bigint | Y |  |

### fml_sub_user_store

ประมาณ 5,146 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `store_id` | character varying(10) | Y |  |
| 3 | `update_user` | character varying(200) | Y |  |
| 4 | `update_date` | timestamp without time zone | Y |  |
| 5 | `sub_user_id` | bigint | Y |  |

### fml_sub_user_zone

ประมาณ 286 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `zone_name` | character varying(5) | Y |  |
| 3 | `update_user` | character varying(200) | Y |  |
| 4 | `update_date` | timestamp without time zone | Y |  |
| 5 | `sub_user_id` | bigint | Y |  |

### fml_subarea_file

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_id` | numeric | N |  |
| 2 | `file_name` | character varying(1000) | Y |  |
| 3 | `create_date` | timestamp without time zone | N |  |
| 4 | `create_user` | character varying(100) | Y |  |
| 5 | `delete_flag` | character varying(1) | Y |  |
| 6 | `content` | bytea | Y |  |
| 7 | `content_type` | character varying(30) | Y |  |
| 8 | `report_type` | character varying(20) | N |  |
| 9 | `store_id` | character varying(5) | Y |  |
| 10 | `year` | character varying(4) | Y |  |
| 11 | `month` | character varying(2) | Y |  |
| 12 | `day` | character varying(2) | Y |  |
| 13 | `zone_cd` | character varying(5) | Y |  |

<details><summary>Index</summary>

- `fml_subarea_file_index1` — `btree (file_id)`

</details>

### fml_subarea_statement

ประมาณ 1,224,084 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` | bigint | N |  |
| 2 | `report_type` | character varying(20) | N |  |
| 3 | `file_id` | bigint | Y |  |
| 4 | `store_id` | character varying(20) | Y |  |
| 5 | `year` | character varying(4) | Y |  |
| 6 | `month` | character varying(2) | Y |  |
| 7 | `day` | character varying(2) | Y |  |
| 8 | `create_date` | timestamp without time zone | Y |  |
| 9 | `update_date` | timestamp without time zone | Y |  |
| 10 | `zone_cd` | character varying(5) | Y |  |
| 11 | `file_type` | character varying(100) | Y |  |

<details><summary>Index</summary>

- `fml_subarea_statement_index2` — `btree (report_type) WITH (fillfactor='90')`
- `fml_subarea_statement_index3` — `btree (store_id) WITH (fillfactor='90')`
- `fml_subarea_statement_index4` — `btree (zone_cd) WITH (fillfactor='90')`

</details>

### fml_subarea_ws

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` | character varying(15) | Y |  |
| 2 | `report_type` | character varying(15) | Y |  |
| 3 | `branch` | character varying(20) | Y |  |
| 4 | `year` | character varying(4) | Y |  |
| 5 | `month` | character varying(2) | Y |  |
| 6 | `day` | character varying(2) | Y |  |
| 7 | `ws_date` | timestamp without time zone | Y |  |
| 8 | `import_flag` | character varying(1) | Y |  |
| 9 | `import_remark` | character varying(500) | Y |  |
| 10 | `import_date` | timestamp without time zone | Y |  |
| 11 | `send_mail_flag` | character varying(1) | Y |  |
| 12 | `send_mail_remark` | character varying(500) | Y |  |
| 13 | `send_mail_date` | timestamp without time zone | Y |  |

<details><summary>Index</summary>

- `fml_subarea_ws_idx` — `btree (process_id, report_type, branch, year, month, import_flag, send_mail_flag)`

</details>

### fml_subarea_ws_end

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` | character varying(15) | Y |  |
| 2 | `end_process_date` | timestamp without time zone | Y |  |
| 3 | `sum_process` | numeric | Y |  |
| 4 | `report_type` | character varying(15) | Y |  |

<details><summary>Index</summary>

- `fml_subarea_ws_end_idx` — `btree (process_id, report_type)`

</details>

### fml_tmp_importdata_stmt

Converted from FCS_FRN.FML_TMP_IMPORTDATA_STMT · ประมาณ 4,528 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `col01` | character varying(4000) | Y |  |
| 2 | `col02` | character varying(4000) | Y |  |
| 3 | `col03` | character varying(4000) | Y |  |
| 4 | `col04` | character varying(4000) | Y |  |
| 5 | `col05` | character varying(4000) | Y |  |
| 6 | `col06` | character varying(4000) | Y |  |
| 7 | `col07` | character varying(4000) | Y |  |
| 8 | `col08` | character varying(4000) | Y |  |
| 9 | `col09` | character varying(4000) | Y |  |
| 10 | `col10` | character varying(4000) | Y |  |
| 11 | `col11` | character varying(4000) | Y |  |
| 12 | `col12` | character varying(4000) | Y |  |
| 13 | `col13` | character varying(4000) | Y |  |
| 14 | `col14` | character varying(4000) | Y |  |
| 15 | `col15` | character varying(4000) | Y |  |
| 16 | `col16` | character varying(4000) | Y |  |
| 17 | `col17` | character varying(4000) | Y |  |
| 18 | `col18` | character varying(4000) | Y |  |
| 19 | `col19` | character varying(4000) | Y |  |
| 20 | `col20` | character varying(4000) | Y |  |
| 21 | `flag_gen_file` | character(1) | Y | 'N'::bpchar |
| 22 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 23 | `report_type` | character varying(20) | Y |  |
| 24 | `filename_period` | character varying(25) | Y |  |
| 25 | `store_area` | character varying(20) | Y |  |
| 26 | `id` 🔑 | bigint | N |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_tmp_importdata_stmt_pkey` — `btree (id)`

</details>

### fr_process

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` 🔑 | numeric(38,0) | N |  |
| 2 | `application_id` | character varying(20) | Y |  |
| 3 | `receive_timestamptz` | timestamp with time zone | Y |  |
| 4 | `fr_bu_type` | character varying(100) | Y |  |
| 5 | `fr_place` | character varying(100) | Y |  |
| 6 | `source_info` | character varying(4000) | Y |  |
| 7 | `prospect_mg` | character varying(100) | Y |  |
| 8 | `prospect_mg_edu` | character varying(5) | Y |  |
| 9 | `process_remark` | character varying(1000) | Y |  |
| 10 | `present_type` | character varying(2) | Y |  |
| 11 | `present_timestamptz` | timestamp with time zone | Y |  |
| 12 | `plan_store_tour_timestamptz` | timestamp with time zone | Y |  |
| 13 | `actual_store_tour_timestamptz` | timestamp with time zone | Y |  |
| 14 | `bu_plan` | character varying(1) | Y |  |
| 15 | `dep_meeting_timestamptz` | timestamp with time zone | Y |  |
| 16 | `dep_meeting_team` | character varying(1000) | Y |  |
| 17 | `read_contract_timestamptz` | timestamp with time zone | Y |  |
| 18 | `actual_pay_timestamptz` | timestamp with time zone | Y |  |
| 19 | `plan_pay_timestamptz` | timestamp with time zone | Y |  |
| 20 | `train_staff` | character varying(1) | Y |  |
| 21 | `select_store_id` | character varying(5) | Y |  |
| 22 | `select_store_timestamptz` | timestamp with time zone | Y |  |
| 23 | `memo_personal` | character varying(1) | Y |  |
| 24 | `memo_personal_timestamptz` | timestamp with time zone | Y |  |
| 25 | `memo_personal_no` | character varying(20) | Y |  |
| 26 | `mg_meeting_timestamptz` | timestamp with time zone | Y |  |
| 27 | `mg_meeting_team` | character varying(1000) | Y |  |
| 28 | `full_capital` | character varying(1) | Y |  |
| 29 | `capital` | numeric(16,2) | Y |  |
| 30 | `loan` | numeric(16,2) | Y |  |
| 31 | `bank_name` | character varying(100) | Y |  |
| 32 | `loan_year` | numeric(2,0) | Y |  |
| 33 | `memo_transfer` | character varying(1) | Y |  |
| 34 | `memo_transfer_timestamptz` | timestamp with time zone | Y |  |
| 35 | `memo_transfer_no` | character varying(20) | Y |  |
| 36 | `memo_btf` | character varying(1) | Y |  |
| 37 | `memo_btf_timestamptz` | timestamp with time zone | Y |  |
| 38 | `memo_btf_no` | character varying(20) | Y |  |
| 39 | `memo_fr` | character varying(1) | Y |  |
| 40 | `memo_fr_timestamptz` | timestamp with time zone | Y |  |
| 41 | `memo_fr_no` | character varying(20) | Y |  |
| 42 | `company` | character varying(500) | Y |  |
| 43 | `sign_timestamptz` | timestamp with time zone | Y |  |
| 44 | `contract_start_timestamptz` | timestamp with time zone | Y |  |
| 45 | `contract_end_timestamptz` | timestamp with time zone | Y |  |
| 46 | `send_doc_timestamptz` | timestamp with time zone | Y |  |
| 47 | `receipt_no` | character varying(20) | Y |  |
| 48 | `keep_in_touch` | character varying(1) | Y |  |
| 49 | `keep_in_touch_timestamptz` | timestamp with time zone | Y |  |
| 50 | `keep_in_touch_reason` | character varying(1000) | Y |  |
| 51 | `big_cleaning_timestamptz` | timestamp with time zone | Y |  |
| 52 | `contract_cust_timestamptz` | timestamp with time zone | Y |  |
| 53 | `contract_lawer_timestamptz` | timestamp with time zone | Y |  |
| 54 | `plan_check_timestamptz` | timestamp with time zone | Y |  |
| 55 | `actual_check_timestamptz` | timestamp with time zone | Y |  |
| 56 | `can_check` | character varying(1) | Y |  |
| 57 | `fr_type` | character varying(5) | Y |  |
| 58 | `fr_subtype` | character varying(5) | Y |  |
| 59 | `region` | character varying(5) | Y |  |
| 60 | `open_type` | character varying(2) | Y |  |
| 61 | `open_timestamptz` | timestamp with time zone | Y |  |
| 62 | `juristic_id` | numeric(38,0) | Y |  |
| 63 | `order_id` | numeric(38,0) | Y |  |
| 64 | `create_timestamptz` | timestamp with time zone | Y |  |
| 65 | `create_user` | character varying(200) | Y |  |
| 66 | `uptimestamptz_timestamptz` | timestamp with time zone | Y |  |
| 67 | `uptimestamptz_user` | character varying(200) | Y |  |
| 68 | `assistant_id` | numeric(38,0) | Y |  |
| 69 | `working_timestamptz` | timestamp with time zone | Y |  |
| 70 | `uptimestamptz_func` | character varying(1) | Y |  |
| 71 | `bu_plan_result` | numeric(5,2) | Y |  |
| 72 | `has_keep_in_touch` | character varying(1) | Y |  |
| 73 | `no_keep_in_touch_reason` | character varying(500) | Y |  |
| 74 | `city` | character varying(100) | Y |  |
| 75 | `province` | character varying(100) | Y |  |
| 76 | `interest_place` | character varying(100) | Y |  |
| 77 | `avp_meeting_timestamptz` | timestamp with time zone | Y |  |
| 78 | `capital_owner` | character varying(100) | Y |  |
| 79 | `select_store_name` | character varying(100) | Y |  |
| 80 | `process_remark_file_name` | character varying(300) | Y |  |
| 81 | `interview_timestamptz` | timestamp with time zone | Y |  |
| 82 | `store_tour_text` | character varying(50) | Y |  |
| 83 | `cust_id` | numeric(38,0) | Y |  |
| 84 | `actual_store_tour_class` | character varying(100) | Y |  |
| 85 | `assessment_test_result` | numeric(5,2) | Y |  |
| 86 | `division_interview_timestamptz` | timestamp with time zone | Y |  |
| 87 | `train_mg_activity_id` | numeric | Y |  |
| 88 | `train_mg_activity_course` | character varying(100) | Y |  |
| 89 | `train_mg_activity_timestamptz` | timestamp with time zone | Y |  |
| 90 | `train_mg_activity_end_timestamptz` | timestamp with time zone | Y |  |
| 91 | `open_timestamptz_char` | character varying(100) | Y |  |
| 92 | `open_timestamptz_plan_char` | character varying(100) | Y |  |
| 93 | `register_timestamptz` | timestamp with time zone | Y |  |
| 94 | `home_visiting_timestamptz` | timestamp with time zone | Y |  |
| 95 | `executive_approve_timestamptz` | timestamp with time zone | Y |  |
| 96 | `franchisee_id` | numeric | Y |  |
| 97 | `process_type` | numeric | Y | 1 |
| 98 | `parent_order_id` | numeric | Y |  |
| 99 | `loan_bank_id` | character varying(5) | Y |  |
| 100 | `extend_round` | numeric(8,0) | Y |  |
| 101 | `extend_year` | numeric(8,0) | Y |  |
| 102 | `email_received` | character varying(1) | Y |  |
| 103 | `profit` | numeric(14,2) | Y |  |
| 104 | `interview_point` | numeric(5,2) | Y |  |
| 105 | `interview_result` | character(1) | Y |  |
| 106 | `interview_remark` | character varying(4000) | Y |  |
| 107 | `interview_next_timestamptz` | timestamp with time zone | Y |  |
| 108 | `dv_name` | character varying(200) | Y |  |
| 109 | `send_contact_lawer_timestamptz` | timestamp with time zone | Y |  |
| 110 | `red_flag` | timestamp with time zone | Y |  |
| 111 | `status_flag` | character varying(5) | Y |  |
| 112 | `white_flag` | timestamp with time zone | Y |  |
| 113 | `green_flag` | timestamp with time zone | Y |  |
| 114 | `have_store` | character varying(1) | Y |  |
| 115 | `open_store_year` | character varying(4) | Y |  |
| 116 | `interview2_point` | numeric(7,2) | Y |  |
| 117 | `interview2_timestamptz` | timestamp with time zone | Y |  |
| 118 | `move_store_remark` | character varying(100) | Y |  |
| 119 | `cancel_type` | character varying(100) | Y |  |
| 120 | `cancel_timestamptz` | timestamp with time zone | Y |  |
| 121 | `move_type_id` | numeric | Y |  |
| 122 | `change_fr_type_remark` | character varying(4000) | Y |  |
| 123 | `continue_contract_age_flag` | character(1) | Y |  |
| 124 | `continue_contract_age_other` | character varying(4000) | Y |  |
| 125 | `source_info_category` | character varying(20) | Y |  |
| 126 | `source_info_other` | character varying(200) | Y |  |
| 127 | `gas_station` | character varying(200) | Y |  |
| 128 | `actual_store_tour_emp_class` | character varying(100) | Y |  |
| 129 | `actual_store_tour_emp_timestamptz` | timestamp with time zone | Y |  |
| 130 | `parent_process_id` | numeric | Y |  |
| 131 | `process_version` | numeric | Y | 1 |

- **PK:** `process_id`

<details><summary>Index</summary>

- `fr_process_pkey` — `btree (process_id)`

</details>

### fr_process_trn

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `process_id` | numeric(38,0) | N |  |
| 2 | `step_id` | numeric(4,0) | N |  |
| 3 | `step_date` | timestamp with time zone | Y |  |
| 4 | `cust_id` | numeric(38,0) | Y |  |
| 5 | `title_code` | character varying(2) | Y |  |
| 6 | `first_name` | character varying(100) | Y |  |
| 7 | `last_name` | character varying(100) | Y |  |
| 8 | `nick_name` | character varying(100) | Y |  |
| 9 | `birthday` | timestamp with time zone | Y |  |
| 10 | `age` | character varying(20) | Y |  |
| 11 | `sex` | character varying(2) | Y |  |
| 12 | `status_code` | character varying(2) | Y |  |
| 13 | `edu_code` | character varying(2) | Y |  |
| 14 | `occp_code` | character varying(5) | Y |  |
| 15 | `id_card` | character varying(15) | Y |  |
| 16 | `tower` | character varying(100) | Y |  |
| 17 | `floor` | character varying(10) | Y |  |
| 18 | `address_no` | character varying(20) | Y |  |
| 19 | `moo` | character varying(10) | Y |  |
| 20 | `soi` | character varying(100) | Y |  |
| 21 | `street` | character varying(100) | Y |  |
| 22 | `district` | character varying(100) | Y |  |
| 23 | `city` | character varying(100) | Y |  |
| 24 | `province` | character varying(100) | Y |  |
| 25 | `zip` | character varying(10) | Y |  |
| 26 | `mobile` | character varying(20) | Y |  |
| 27 | `tel` | character varying(20) | Y |  |
| 28 | `fax` | character varying(20) | Y |  |
| 29 | `email` | character varying(100) | Y |  |
| 30 | `fr_type` | character varying(5) | Y |  |
| 31 | `fr_subtype` | character varying(5) | Y |  |
| 32 | `region` | character varying(5) | Y |  |
| 33 | `open_type` | character varying(2) | Y |  |
| 34 | `open_date` | timestamp with time zone | Y |  |
| 35 | `invitation_id` | numeric(38,0) | Y |  |
| 36 | `amount_return` | numeric(16,2) | Y |  |
| 37 | `memo_date` | timestamp with time zone | Y |  |
| 38 | `memo_no` | character varying(20) | Y |  |
| 39 | `crm_user` | numeric(38,0) | Y |  |
| 40 | `fr_user` | numeric(38,0) | Y |  |
| 41 | `status` | character varying(2) | Y |  |
| 42 | `cancel_reason` | character varying(2) | Y |  |
| 43 | `status_remark` | character varying(4000) | Y |  |
| 44 | `create_date` | timestamp with time zone | Y |  |
| 45 | `create_user` | character varying(200) | Y |  |
| 46 | `update_date` | timestamp with time zone | Y |  |
| 47 | `update_user` | character varying(200) | Y |  |
| 48 | `invitation_received` | character varying(1) | Y |  |
| 49 | `update_func` | character varying(1) | Y |  |
| 50 | `status_remark_file_name` | character varying(300) | Y |  |
| 51 | `expected_date` | timestamp with time zone | Y |  |
| 52 | `process_version` | numeric | Y | 1 |

- **PK:** `process_id,step_id`

<details><summary>Index</summary>

- `fr_process_trn_pkey` — `btree (process_id, step_id)`

</details>

### fr_store

ประมาณ 11,583 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` | bigint | Y |  |
| 2 | `trn_id` | bigint | Y |  |
| 3 | `parent_order_id` | bigint | Y |  |
| 4 | `store_id` | character varying(8) | Y |  |
| 5 | `store_name` | character varying(100) | Y |  |
| 6 | `region` | character varying(4) | Y |  |
| 7 | `location` | character varying(4) | Y |  |
| 8 | `start_date` | date | Y |  |
| 9 | `transfer_date` | date | Y |  |
| 10 | `open_date` | date | Y |  |
| 11 | `sign_date` | date | Y |  |
| 12 | `contract_start_date` | date | Y |  |
| 13 | `contract_end_date` | date | Y |  |
| 14 | `contract_no` | integer | Y |  |
| 15 | `juristic_id` | bigint | Y |  |
| 16 | `juristic_group_id` | bigint | Y |  |
| 17 | `tower` | character varying(100) | Y |  |
| 18 | `floor` | character varying(10) | Y |  |
| 19 | `address_no` | character varying(200) | Y |  |
| 20 | `moo` | character varying(10) | Y |  |
| 21 | `soi` | character varying(100) | Y |  |
| 22 | `street` | character varying(100) | Y |  |
| 23 | `district` | character varying(100) | Y |  |
| 24 | `city` | character varying(100) | Y |  |
| 25 | `province` | character varying(100) | Y |  |
| 26 | `zip` | character varying(10) | Y |  |
| 27 | `mobile` | character varying(20) | Y |  |
| 28 | `tel` | character varying(70) | Y |  |
| 29 | `fax` | character varying(20) | Y |  |
| 30 | `owner_id1` | bigint | Y |  |
| 31 | `owner_id2` | bigint | Y |  |
| 32 | `owner_id3` | bigint | Y |  |
| 33 | `cur_owner_id` | bigint | Y |  |
| 34 | `cur_owner_title_code` | character varying(2) | Y |  |
| 35 | `cur_owner_first_name` | character varying(100) | Y |  |
| 36 | `cur_owner_last_name` | character varying(100) | Y |  |
| 37 | `cur_owner_tel` | character varying(50) | Y |  |
| 38 | `cur_owner_relation` | character varying(100) | Y |  |
| 39 | `fr_type` | character varying(3) | Y |  |
| 40 | `fr_subtype` | character varying(2) | Y |  |
| 41 | `fr_share` | numeric(5,2) | Y |  |
| 42 | `print_address` | character varying(1) | Y |  |
| 43 | `store_type` | character varying(2) | Y |  |
| 44 | `op_type` | character varying(2) | Y |  |
| 45 | `operate_type` | character varying(2) | Y |  |
| 46 | `detail_type` | character varying(4) | Y |  |
| 47 | `owner_type` | character varying(2) | Y |  |
| 48 | `cancel_type` | character varying(2) | Y |  |
| 49 | `cancel_reason` | character varying(2) | Y |  |
| 50 | `cancel_reason_other` | character varying(4000) | Y |  |
| 51 | `cancel_date` | date | Y |  |
| 52 | `cancel_detail` | character varying(1000) | Y |  |
| 53 | `audit_type` | character varying(2) | Y |  |
| 54 | `store_source` | character varying(2) | Y |  |
| 55 | `to_store_id` | character varying(5) | Y |  |
| 56 | `assess1` | numeric(5,2) | Y |  |
| 57 | `assess2` | numeric(5,2) | Y |  |
| 58 | `assess3` | numeric(5,2) | Y |  |
| 59 | `assess3_grade` | character varying(1) | Y |  |
| 60 | `incentive` | numeric(16,2) | Y |  |
| 61 | `affect_date` | date | Y |  |
| 62 | `affect_store_id` | character varying(5) | Y |  |
| 63 | `affect_remark` | character varying(1000) | Y |  |
| 64 | `status` | character varying(10) | Y |  |
| 65 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 66 | `create_user` | character varying(200) | Y |  |
| 67 | `update_date` | timestamp without time zone | Y |  |
| 68 | `update_user` | character varying(200) | Y |  |
| 69 | `amphur_id` | character varying(5) | Y |  |
| 70 | `province_id` | character varying(5) | Y |  |
| 71 | `authorization_person1` | character varying(100) | Y |  |
| 72 | `authorization_person2` | character varying(100) | Y |  |
| 73 | `authorization_person3` | character varying(100) | Y |  |
| 74 | `ref_process_id` | character varying(100) | Y |  |
| 75 | `extend_round` | integer | Y |  |
| 76 | `to_open_date` | date | Y |  |
| 77 | `from_order_id` | bigint | Y |  |
| 78 | `cancel_type_move_store` | character varying(2) | Y |  |
| 79 | `change_partner_contact_flag` | character(1) | Y | 'N'::bpchar |
| 80 | `ref_to_order_id` | bigint | Y |  |
| 81 | `ref_from_order_id` | bigint | Y |  |
| 82 | `change_partner_contact_udate` | date | Y |  |
| 83 | `reward_contract_type` | character varying(2) | Y |  |
| 84 | `owner_id4` | bigint | Y |  |
| 85 | `reward_contract_type_show` | character varying(2) | Y |  |

<details><summary>Index</summary>

- `fr_store_id1` — `btree (store_id, cancel_date)`
- `fr_store_index1` — `btree (store_id)`
- `fr_store_index10` — `btree (owner_id4)`
- `fr_store_index2` — `btree (start_date)`
- `fr_store_index3` — `btree (owner_id1)`
- `fr_store_index4` — `btree (cancel_date)`
- `fr_store_index5` — `btree (fr_type)`
- `fr_store_index6` — `btree (status)`
- `fr_store_index7` — `btree (cancel_type)`
- `fr_store_index8` — `btree (owner_id2)`
- `fr_store_index9` — `btree (owner_id3)`
- `idx_fr_store_lookup` — `btree (store_id, start_date, cancel_date)`

</details>

### fr_store_assessment

ประมาณ 629 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` | numeric(38,0) | Y |  |
| 2 | `store_id` | character varying(5) | N |  |
| 3 | `year_no` | numeric(5,0) | Y |  |
| 4 | `seq_no` | numeric(5,0) | Y |  |
| 5 | `score` | numeric(5,2) | Y | 0 |
| 6 | `grade` | character varying(1) | Y |  |
| 7 | `update_date` | timestamp without time zone | Y |  |
| 8 | `update_user` | character varying(200) | Y |  |
| 9 | `create_date` | timestamp without time zone | Y |  |
| 10 | `create_user` | character varying(200) | Y |  |

### fr_store_contract_history

ประมาณ 13,888 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | N |  |
| 2 | `seq_no` | numeric | N |  |
| 3 | `start_date` | timestamp without time zone | N |  |
| 4 | `end_date` | timestamp without time zone | N |  |
| 5 | `signed_date` | timestamp without time zone | N |  |
| 6 | `edit_end_date` | timestamp without time zone | Y |  |
| 7 | `remark` | character varying(400) | Y |  |
| 8 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 9 | `update_user` | character varying(200) | Y |  |
| 10 | `create_date` | timestamp without time zone | Y |  |
| 11 | `create_user` | character varying(200) | Y |  |
| 12 | `update_fr_store` | character varying(1) | Y | 'N'::character varying |

### fr_store_insure

ประมาณ 708 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` | numeric(38,0) | Y |  |
| 2 | `store_id` | character varying(5) | N |  |
| 3 | `seq_no` | numeric(5,0) | N |  |
| 4 | `year` | numeric(4,0) | Y |  |
| 5 | `month` | character varying(2) | Y |  |
| 6 | `money_support` | numeric(10,2) | Y |  |
| 7 | `split` | numeric(10,2) | Y |  |
| 8 | `create_date` | timestamp with time zone | Y |  |
| 9 | `create_user` | character varying(200) | Y |  |
| 10 | `update_date` | timestamp with time zone | Y |  |
| 11 | `update_user` | character varying(200) | Y |  |

### franchisee

ประมาณ 7,885 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `cust_id` | numeric(38,0) | Y |  |
| 2 | `franchisee_id` 🔑 | numeric(38,0) | N |  |
| 3 | `title_code` | character varying(2) | Y |  |
| 4 | `first_name` | character varying(100) | Y |  |
| 5 | `last_name` | character varying(100) | Y |  |
| 6 | `relation` | character varying(50) | Y |  |
| 7 | `nick_name` | character varying(100) | Y |  |
| 8 | `birthday` | timestamp without time zone | Y |  |
| 9 | `sex` | character varying(2) | Y |  |
| 10 | `status_code` | character varying(2) | Y |  |
| 11 | `edu_code` | character varying(2) | Y |  |
| 12 | `edu_other` | character varying(2) | Y |  |
| 13 | `school` | character varying(100) | Y |  |
| 14 | `major` | character varying(500) | Y |  |
| 15 | `occp_code` | character varying(5) | Y |  |
| 16 | `occp_other` | character varying(100) | Y |  |
| 17 | `id_card` | character varying(15) | Y |  |
| 18 | `religion` | character varying(15) | Y |  |
| 19 | `salary` | numeric(16,2) | Y |  |
| 20 | `tower` | character varying(100) | Y |  |
| 21 | `floor` | character varying(10) | Y |  |
| 22 | `address_no` | character varying(20) | Y |  |
| 23 | `moo` | character varying(10) | Y |  |
| 24 | `soi` | character varying(100) | Y |  |
| 25 | `street` | character varying(100) | Y |  |
| 26 | `district` | character varying(100) | Y |  |
| 27 | `city` | character varying(100) | Y |  |
| 28 | `province` | character varying(100) | Y |  |
| 29 | `zip` | character varying(10) | Y |  |
| 30 | `mobile` | character varying(100) | Y |  |
| 31 | `tel` | character varying(100) | Y |  |
| 32 | `fax` | character varying(100) | Y |  |
| 33 | `email` | character varying(100) | Y |  |
| 34 | `office` | character varying(200) | Y |  |
| 35 | `department` | character varying(200) | Y |  |
| 36 | `position` | character varying(200) | Y |  |
| 37 | `cust_img` | character varying(100) | Y |  |
| 38 | `franchisee_source` | character varying(2) | Y |  |
| 39 | `media_source` | character varying(100) | Y |  |
| 40 | `married_title_code` | character varying(2) | Y |  |
| 41 | `married_first_name` | character varying(100) | Y |  |
| 42 | `married_last_name` | character varying(100) | Y |  |
| 43 | `married_occp_code` | character varying(5) | Y |  |
| 44 | `married_occp` | character varying(100) | Y |  |
| 45 | `married_mobile` | character varying(100) | Y |  |
| 46 | `married_off` | character varying(500) | Y |  |
| 47 | `married_tel_off` | character varying(100) | Y |  |
| 48 | `number_child` | numeric(5,0) | Y |  |
| 49 | `expect_salary` | numeric(16,0) | Y |  |
| 50 | `experience` | character varying(1000) | Y |  |
| 51 | `society` | character varying(1000) | Y |  |
| 52 | `sport` | character varying(1000) | Y |  |
| 53 | `future_trend` | character varying(1000) | Y |  |
| 54 | `status` | character varying(10) | Y |  |
| 55 | `age` | numeric(5,0) | Y |  |
| 56 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 57 | `create_user` | character varying(200) | Y | 'system'::character varying |
| 58 | `update_date` | timestamp without time zone | Y |  |
| 59 | `update_user` | character varying(200) | Y |  |
| 60 | `spouse_img_id` | numeric | Y |  |
| 61 | `p_pac_pri` | character varying(2) | Y |  |
| 62 | `p_pac_sec` | character varying(2) | Y |  |
| 63 | `train_result` | character varying(2) | Y |  |
| 64 | `franchisee_img_id` | character varying(200) | Y |  |
| 65 | `franchisee_group_id` | numeric | Y |  |
| 66 | `first_name_en` | character varying(100) | Y |  |
| 67 | `last_name_en` | character varying(100) | Y |  |
| 68 | `religion_other` | character varying(100) | Y |  |
| 69 | `occp_code2` | character varying(5) | Y |  |
| 70 | `occp_code3` | character varying(5) | Y |  |
| 71 | `married_occp_code2` | character varying(5) | Y |  |
| 72 | `married_occp_code3` | character varying(5) | Y |  |
| 73 | `media_source_category` | character varying(5) | Y |  |
| 74 | `media_source_other` | character varying(200) | Y |  |
| 75 | `nationality` | character varying(5) | Y |  |
| 76 | `married_id_card` | character varying(15) | Y |  |
| 77 | `position_type` | character varying(5) | Y |  |
| 78 | `food_allergy` | character varying(200) | Y |  |
| 79 | `food` | numeric | Y |  |
| 80 | `married_nick_name` | character varying(100) | Y |  |
| 81 | `main_nationality` | numeric | Y | 1 |
| 82 | `married_birthday` | timestamp without time zone | Y |  |
| 83 | `docattach_id` | numeric | Y |  |
| 84 | `religion_accept` | character varying(1) | Y |  |
| 85 | `marketing_accept` | character varying(1) | Y |  |
| 86 | `profile_accept` | character varying(1) | Y |  |

- **PK:** `franchisee_id`

<details><summary>Index</summary>

- `franchisee_pk` — `btree (franchisee_id)`

</details>

### fs_sevenshop

ประมาณ 18,432 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(7) | N |  |
| 2 | `shop_type` | character varying(5) | Y |  |
| 3 | `branch_name` | character varying(100) | Y |  |
| 4 | `branch_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(50) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `tel` | character varying(70) | Y |  |
| 9 | `address_no` | character varying(200) | Y |  |
| 10 | `soi` | character varying(100) | Y |  |
| 11 | `street` | character varying(100) | Y |  |
| 12 | `district_id` | character varying(5) | Y |  |
| 13 | `district` | character varying(100) | Y |  |
| 14 | `amphur_id` | character varying(5) | Y |  |
| 15 | `amphur` | character varying(100) | Y |  |
| 16 | `province_id` | character varying(5) | Y |  |
| 17 | `province` | character varying(100) | Y |  |
| 18 | `zip` | character varying(100) | Y |  |
| 19 | `open_date` | date | Y |  |
| 20 | `close_date` | date | Y |  |
| 21 | `mgr_name` | character varying(200) | Y |  |
| 22 | `fc_name` | character varying(200) | Y |  |
| 23 | `fc_tel` | character varying(30) | Y |  |
| 24 | `fc_page` | character varying(30) | Y |  |
| 25 | `mn_name` | character varying(200) | Y |  |
| 26 | `mn_tel` | character varying(30) | Y |  |
| 27 | `mn_page` | character varying(30) | Y |  |
| 28 | `dv_name` | character varying(200) | Y |  |
| 29 | `dv_tel` | character varying(30) | Y |  |
| 30 | `dv_page` | character varying(30) | Y |  |
| 31 | `dv_email` | character varying(100) | Y |  |
| 32 | `avp_name` | character varying(200) | Y |  |
| 33 | `avp_tel` | character varying(30) | Y |  |
| 34 | `avp_page` | character varying(30) | Y |  |
| 35 | `avp_email` | character varying(100) | Y |  |
| 36 | `gm_name` | character varying(200) | Y |  |
| 37 | `gm_tel` | character varying(30) | Y |  |
| 38 | `gm_page` | character varying(30) | Y |  |
| 39 | `gm_email` | character varying(100) | Y |  |
| 40 | `status` | character varying(20) | Y |  |
| 41 | `update_date` | timestamp without time zone | Y |  |
| 42 | `update_user` | character varying(200) | Y |  |
| 43 | `mn_email` | character varying(100) | Y |  |
| 44 | `fc_email` | character varying(100) | Y |  |
| 45 | `zone_cd` | character varying(10) | Y |  |
| 46 | `fc_employee_id` | character varying(20) | Y |  |
| 47 | `mn_employee_id` | character varying(20) | Y |  |
| 48 | `dv_employee_id` | character varying(20) | Y |  |
| 49 | `avp_employee_id` | character varying(20) | Y |  |
| 50 | `gm_employee_id` | character varying(20) | Y |  |
| 51 | `status_type` | character varying(20) | Y |  |
| 52 | `start_renovate_date` | date | Y |  |
| 53 | `end_renovate_date` | date | Y |  |
| 54 | `sales_area` | numeric(8,2) | Y |  |
| 55 | `store_type_code` | character varying(5) | Y |  |
| 56 | `ptt_code` | character varying(5) | Y |  |

<details><summary>Index</summary>

- `fs_sevenshop_index1` — `btree (branch_id)`
- `fs_sevenshop_index2` — `btree (shop_type)`
- `fs_sevenshop_index3` — `btree (dv_email)`

</details>

### ftp_interface

ประมาณ 145 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('ftp_interface_id_seq'::regclass) |
| 2 | `name` | character varying(500) | Y |  |
| 3 | `ftp_path` | character varying(500) | Y |  |
| 4 | `archive` | numeric(5,2) | Y |  |
| 5 | `report_type` | character varying(20) | Y |  |
| 6 | `franchise_type` | character varying(30) | Y |  |
| 7 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 8 | `create_user` | character varying(100) | Y |  |
| 9 | `update_date` | timestamp without time zone | Y |  |
| 10 | `update_user` | character varying(100) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `ftp_interface_pkey` — `btree (id)`
- `idx_ftp_interface_franchise_type` — `btree (franchise_type)`

</details>

### general_upload_data_page_audit_log

ประมาณ 377 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('general_upload_data_page_audit_log_id_seq'::regclas |
| 2 | `request_payload` | text | Y |  |
| 3 | `request_response` | text | Y |  |
| 4 | `status` | character varying(10) | Y |  |
| 5 | `create_date` | timestamp with time zone | N | CURRENT_TIMESTAMP |
| 6 | `create_by` | character varying(250) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `PK_d81b0764458437cf2f4c38f772b` — `btree (id)`

</details>

### general_upload_data_page_job

ประมาณ 393 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('general_upload_data_page_job_id_seq'::regclass) |
| 2 | `code_value` | character varying(100) | Y |  |
| 3 | `file_name` | character varying(250) | Y |  |
| 4 | `file_size` | character varying(10) | Y |  |
| 5 | `status` | character varying(20) | Y |  |
| 6 | `create_date` | timestamp with time zone | N | CURRENT_TIMESTAMP |
| 7 | `create_by` | character varying(250) | Y |  |
| 8 | `code_type` | character varying(100) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `PK_8325033488528416159df90fd6f` — `btree (id)`

</details>

### import_group

ประมาณ 4 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('import_group_id_seq'::regclass) |
| 2 | `import_group_name` | character varying(255) | Y |  |
| 3 | `seq_no` | bigint | Y |  |
| 4 | `active_flag` | character varying(1) | N | 'Y'::character varying |
| 5 | `create_by` | bigint | Y |  |
| 6 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 7 | `update_by` | bigint | Y |  |
| 8 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`

<details><summary>Index</summary>

- `import_group_pkey` — `btree (id)`

</details>

### import_job_status

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_name` 🔑 | character varying(255) | N |  |
| 2 | `is_data_finished` | boolean | N | false |
| 3 | `is_control_finished` | boolean | N | false |
| 4 | `created_at` | timestamp with time zone | N | CURRENT_TIMESTAMP |
| 5 | `updated_at` | timestamp with time zone | N | CURRENT_TIMESTAMP |

- **PK:** `file_name`

<details><summary>Index</summary>

- `import_job_status_pkey` — `btree (file_name)`

</details>

### import_type

ประมาณ 23 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('import_type_id_seq'::regclass) |
| 2 | `import_group_id` | integer | Y |  |
| 3 | `import_type_name` | character varying(255) | Y |  |
| 4 | `seq_no` | bigint | Y |  |
| 5 | `file_header` | text | Y |  |
| 6 | `file_type` | character varying(50) | Y |  |
| 7 | `active_flag` | character varying(1) | N | 'Y'::character varying |
| 8 | `endpoint_url` | text | Y |  |
| 9 | `endpoint_key` | text | Y |  |
| 10 | `cm_entity_name` | character varying(255) | Y |  |
| 11 | `s3_backup_path` | text | Y |  |
| 12 | `input` | text | Y |  |
| 13 | `s3_template_path` | text | Y |  |
| 14 | `payload_json` | text | Y |  |
| 15 | `type_value` | character varying(255) | Y |  |
| 16 | `system_name` | character varying(255) | Y |  |
| 17 | `is_background` | character varying(1) | Y | 'N'::character varying |

- **PK:** `id`
- **FK:** `import_group_id` → `import_group`.`id`

<details><summary>Index</summary>

- `import_type_pkey` — `btree (id)`

</details>

### import_type_permission

Permission whitelist for central upload import types. No row means public/default access. · ประมาณ 6 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('import_type_permission_id_seq'::regclass) |
| 2 | `import_type_id` | integer | N |  |
| 3 | `group_id` | integer | N |  |
| 4 | `active_flag` | character varying(1) | N | 'Y'::character varying |
| 5 | `create_by` | character varying(100) | Y |  |
| 6 | `create_date` | timestamp with time zone | N | now() |
| 7 | `update_by` | character varying(100) | Y |  |
| 8 | `update_date` | timestamp with time zone | Y |  |

- **PK:** `id`
- **UNIQUE:** `import_type_id,group_id`
- **FK:** `import_type_id` → `import_type`.`id`

<details><summary>Index</summary>

- `idx_import_type_permission_group_id` — `btree (group_id)`
- `idx_import_type_permission_import_type_id` — `btree (import_type_id)`
- `import_type_permission_pkey` — `btree (id)`
- `uq_import_type_permission_import_group` — `btree (import_type_id, group_id)`

</details>

### integration_log

**ใช้ใน SBPGI:** log payload ราย call · ประมาณ 518 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('integration_log_id_seq'::regclass) |
| 2 | `module` | character varying(100) | Y |  |
| 3 | `service` | character varying(100) | Y |  |
| 4 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 5 | `update_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 6 | `payload` | text | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `integration_log_pkey` — `btree (id)`

</details>

### juristic

ประมาณ 7,603 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `juristic_id` | numeric(38,0) | Y |  |
| 2 | `juristic_name` | character varying(200) | Y |  |
| 3 | `tower` | character varying(100) | Y |  |
| 4 | `floor` | character varying(10) | Y |  |
| 5 | `address_no` | character varying(20) | Y |  |
| 6 | `moo` | character varying(10) | Y |  |
| 7 | `soi` | character varying(100) | Y |  |
| 8 | `street` | character varying(100) | Y |  |
| 9 | `district` | character varying(100) | Y |  |
| 10 | `city` | character varying(100) | Y |  |
| 11 | `province` | character varying(100) | Y |  |
| 12 | `zip` | character varying(10) | Y |  |
| 13 | `tel` | character varying(100) | Y |  |
| 14 | `fax` | character varying(100) | Y |  |
| 15 | `create_date` | date | Y |  |
| 16 | `create_user` | character varying(200) | Y |  |
| 17 | `update_date` | date | Y |  |
| 18 | `update_user` | character varying(200) | Y |  |
| 19 | `update_func` | character varying(1) | Y |  |
| 20 | `juristic_type_id` | character varying(5) | Y |  |
| 21 | `franchisee_id` | numeric | Y |  |
| 22 | `juristic_group_id` | numeric | Y |  |
| 23 | `juristic_type` | character varying(20) | Y |  |
| 24 | `juristic_no` | character varying(50) | Y |  |

### juristic_backup

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `juristic_id` | numeric(38,0) | Y |  |
| 2 | `juristic_name` | character varying(200) | Y |  |
| 3 | `tower` | character varying(100) | Y |  |
| 4 | `floor` | character varying(10) | Y |  |
| 5 | `address_no` | character varying(20) | Y |  |
| 6 | `moo` | character varying(10) | Y |  |
| 7 | `soi` | character varying(100) | Y |  |
| 8 | `street` | character varying(100) | Y |  |
| 9 | `district` | character varying(100) | Y |  |
| 10 | `city` | character varying(100) | Y |  |
| 11 | `province` | character varying(100) | Y |  |
| 12 | `zip` | character varying(10) | Y |  |
| 13 | `tel` | character varying(100) | Y |  |
| 14 | `fax` | character varying(100) | Y |  |
| 15 | `create_date` | date | Y |  |
| 16 | `create_user` | character varying(200) | Y |  |
| 17 | `update_date` | date | Y |  |
| 18 | `update_user` | character varying(200) | Y |  |
| 19 | `update_func` | character varying(1) | Y |  |
| 20 | `juristic_type_id` | character varying(5) | Y |  |
| 21 | `franchisee_id` | numeric | Y |  |
| 22 | `juristic_group_id` | numeric | Y |  |
| 23 | `juristic_type` | character varying(20) | Y |  |
| 24 | `juristic_no` | character varying(50) | Y |  |

### juristic_group

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `juristic_group_id` 🔑 | numeric(38,0) | N |  |
| 2 | `group_name` | character varying(200) | Y |  |
| 3 | `create_timestamptz` | timestamp with time zone | Y |  |
| 4 | `create_user` | character varying(200) | Y |  |
| 5 | `uptimestamptz_timestamptz` | timestamp with time zone | Y |  |
| 6 | `uptimestamptz_user` | character varying(200) | Y |  |
| 7 | `uptimestamptz_func` | character varying(1) | Y |  |

- **PK:** `juristic_group_id`

<details><summary>Index</summary>

- `juristic_group_pkey` — `btree (juristic_group_id)`

</details>

### mas_area

ประมาณ 13 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `area_id` 🔑 | integer | N | nextval('mas_area_area_id_seq'::regclass) |
| 2 | `area_name` | character varying(4) | Y |  |

- **PK:** `area_id`

<details><summary>Index</summary>

- `mas_area_pkey` — `btree (area_id)`

</details>

### mas_contact

ประมาณ 1,137,861 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `period` | character varying(8) | Y |  |
| 2 | `store_id` | character varying(10) | Y |  |
| 3 | `emp_id` | character varying(15) | Y |  |
| 4 | `fullname` | character varying(60) | Y |  |
| 5 | `tel` | character varying(50) | Y |  |
| 6 | `seq` | integer | Y |  |
| 7 | `position_id` | character varying(10) | Y |  |
| 8 | `position_name` | character varying(100) | Y |  |
| 9 | `department_id` | character varying(10) | Y |  |
| 10 | `department` | character varying(250) | Y |  |
| 11 | `data_source` | character varying(50) | Y |  |
| 12 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

<details><summary>Index</summary>

- `idx_mas_contact` — `btree (store_id, department_id, position_id, period)`

</details>

### mas_district

ประมาณ 959 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `district_id` | character varying(5) | N |  |
| 2 | `district_name` | character varying(100) | N |  |
| 3 | `province_id` | character varying(5) | N |  |
| 4 | `post_code` | character varying(10) | N |  |

### mas_param

**ใช้ใน SBPGI:** ค่ากำหนดกลาง (แทน system_configs) · ประมาณ 93,752 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `param_name` | character varying(255) | Y |  |
| 2 | `param_value` | character varying(4000) | Y |  |
| 3 | `ref_name` | character varying(4000) | Y |  |
| 4 | `description` | character varying(4000) | Y |  |
| 5 | `is_config` | character(1) | Y | 'Y'::bpchar |
| 6 | `active_flag` | character varying(1) | Y | 'Y'::character varying |
| 7 | `create_by` | character varying(100) | Y |  |
| 8 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 9 | `update_by` | character varying(100) | Y |  |
| 10 | `update_date` | timestamp without time zone | Y |  |

<details><summary>Index</summary>

- `mas_param_idx` — `btree (param_name, param_value)`

</details>

### mas_province

ประมาณ 77 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `province_id` | character varying(5) | N |  |
| 2 | `province_name` | character varying(100) | N |  |
| 3 | `region_id` | character varying(5) | Y |  |

### mas_sbp_ad

ประมาณ 102,125 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id_card` | character varying(15) | Y |  |
| 2 | `emp_id` | character varying(15) | Y |  |
| 3 | `title_name_th` | character varying(30) | Y |  |
| 4 | `first_name_th` | character varying(30) | Y |  |
| 5 | `last_name_th` | character varying(30) | Y |  |
| 6 | `first_name_en` | character varying(30) | Y |  |
| 7 | `last_name_en` | character varying(30) | Y |  |
| 8 | `sex` | character varying(10) | Y |  |
| 9 | `nationality` | character varying(30) | Y |  |
| 10 | `race` | character varying(30) | Y |  |
| 11 | `hire_start_date` | timestamp without time zone | Y |  |
| 12 | `emp_type` | character varying(100) | Y |  |
| 13 | `position_id` | character varying(5) | Y |  |
| 14 | `position_name` | character varying(100) | Y |  |
| 15 | `position_acting` | character varying(5) | Y |  |
| 16 | `email` | character varying(70) | Y |  |
| 17 | `store_id` | character varying(10) | Y |  |
| 18 | `store_name` | character varying(200) | Y |  |
| 19 | `store_type` | character varying(100) | Y |  |
| 20 | `store_group` | character varying(20) | Y |  |
| 21 | `tel_office` | character varying(25) | Y |  |
| 22 | `username` | character varying(50) | Y |  |
| 23 | `sbp_ad_id` | character varying(15) | Y |  |
| 24 | `sp_ad_id` | character varying(15) | Y |  |
| 25 | `manager_ad_id` | character varying(15) | Y |  |
| 26 | `email_notify` | character varying(70) | Y |  |
| 27 | `emp_rcd` | character varying(5) | Y | '0'::character varying |
| 28 | `trans_type` | character varying(5) | Y |  |
| 29 | `trans_date` | timestamp without time zone | Y |  |
| 30 | `flag_action` | character varying(5) | Y |  |
| 31 | `active_date` | timestamp without time zone | Y |  |
| 32 | `inactive_date` | timestamp without time zone | Y |  |
| 33 | `flag_send_ad` | character varying(5) | Y |  |
| 34 | `last_send_ad_date` | timestamp without time zone | Y |  |
| 35 | `return_msg` | character varying(4000) | Y |  |
| 36 | `franchisee_id` | numeric | Y |  |
| 37 | `principal_name` | character varying(70) | Y |  |
| 38 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 39 | `update_date` | timestamp without time zone | Y |  |
| 40 | `is_manager` | character(1) | Y | 'N'::bpchar |
| 41 | `trans_cate` | character varying(5) | Y |  |
| 42 | `return_status` | character varying(15) | Y |  |
| 43 | `return_msg_desc` | character varying(4000) | Y |  |
| 44 | `return_code` | character varying(15) | Y |  |
| 45 | `temp_col_1` | character varying(20) | Y |  |
| 46 | `company_id` | character varying(20) | Y |  |
| 47 | `job_code` | character varying(10) | Y |  |
| 48 | `remark` | character varying(255) | Y |  |

- **UNIQUE:** `sbp_ad_id`
- **UNIQUE:** `username`

<details><summary>Index</summary>

- `idx_mas_sbp_ad` — `btree (id_card, position_id, sbp_ad_id, sp_ad_id, manager_ad_id, flag_action, trans_type, flag_send_ad, franchisee_id)`
- `idx_mas_sbp_ad2` — `btree (store_id)`
- `mas_sbp_ad_u02` — `btree (sbp_ad_id)`
- `mas_sbp_ad_u03` — `btree (username)`

</details>

### mas_store

**ใช้ใน SBPGI:** master ร้าน · ประมาณ 19,647 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` 🔑 | character varying(10) | N |  |
| 2 | `branch_name` | character varying(200) | Y |  |
| 3 | `branch_type` | character varying(20) | Y |  |
| 4 | `status_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(5) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `zone_cd` | character varying(10) | Y |  |
| 9 | `branch_tel` | character varying(70) | Y |  |
| 10 | `address` | character varying(500) | Y |  |
| 11 | `address_no` | character varying(200) | Y |  |
| 12 | `soi` | character varying(100) | Y |  |
| 13 | `street` | character varying(100) | Y |  |
| 14 | `district_id` | character varying(5) | Y |  |
| 15 | `district` | character varying(100) | Y |  |
| 16 | `amphur_id` | character varying(5) | Y |  |
| 17 | `amphur` | character varying(100) | Y |  |
| 18 | `province_id` | character varying(5) | Y |  |
| 19 | `province` | character varying(100) | Y |  |
| 20 | `zip` | character varying(100) | Y |  |
| 21 | `open_date` | date | Y |  |
| 22 | `close_date` | date | Y |  |
| 23 | `branch_other` | character varying(100) | Y |  |
| 24 | `fr_sub_type` | character varying(25) | Y |  |
| 25 | `status` | character varying(20) | Y |  |
| 26 | `src_update_date` | timestamp without time zone | Y |  |
| 27 | `src_update_user` | character varying(200) | Y |  |
| 28 | `data_type` | character varying(5) | Y |  |
| 29 | `active_flag` | character(1) | Y | 'Y'::bpchar |
| 30 | `start_renovate_date` | date | Y |  |
| 31 | `end_renovate_date` | date | Y |  |

- **PK:** `branch_id`

<details><summary>Index</summary>

- `mas_store_pkey` — `btree (branch_id)`

</details>

### mas_store_cambodia

ประมาณ 78 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(7) | Y |  |
| 2 | `shop_type` | character varying(20) | Y |  |
| 3 | `branch_name` | character varying(100) | Y |  |
| 4 | `branch_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(50) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `tel` | character varying(70) | Y |  |
| 9 | `address_no` | character varying(200) | Y |  |
| 10 | `soi` | character varying(100) | Y |  |
| 11 | `street` | character varying(100) | Y |  |
| 12 | `district_id` | character varying(5) | Y |  |
| 13 | `district` | character varying(100) | Y |  |
| 14 | `amphur_id` | character varying(5) | Y |  |
| 15 | `amphur` | character varying(100) | Y |  |
| 16 | `province_id` | character varying(5) | Y |  |
| 17 | `province` | character varying(100) | Y |  |
| 18 | `zip` | character varying(100) | Y |  |
| 19 | `open_date` | timestamp without time zone | Y |  |
| 20 | `close_date` | timestamp without time zone | Y |  |
| 21 | `emp_name` | character varying(200) | Y |  |
| 22 | `fc_name` | character varying(200) | Y |  |
| 23 | `fc_tel_number` | character varying(30) | Y |  |
| 24 | `fc_page_number` | character varying(30) | Y |  |
| 25 | `mn_name` | character varying(200) | Y |  |
| 26 | `mn_tel_number` | character varying(30) | Y |  |
| 27 | `mn_page_number` | character varying(30) | Y |  |
| 28 | `dv_name` | character varying(200) | Y |  |
| 29 | `dv_tel_number` | character varying(30) | Y |  |
| 30 | `dv_page_number` | character varying(30) | Y |  |
| 31 | `dv_e_mail` | character varying(100) | Y |  |
| 32 | `agm_name` | character varying(100) | Y |  |
| 33 | `agm_tel_number` | character varying(30) | Y |  |
| 34 | `agm_page_number` | character varying(30) | Y |  |
| 35 | `agm_e_mail` | character varying(100) | Y |  |
| 36 | `gm_name` | character varying(100) | Y |  |
| 37 | `gm_tel_number` | character varying(30) | Y |  |
| 38 | `gm_page_number` | character varying(30) | Y |  |
| 39 | `gm_e_mail` | character varying(100) | Y |  |
| 40 | `fc_employee_id` | character varying(20) | Y |  |
| 41 | `mn_employee_id` | character varying(20) | Y |  |
| 42 | `dv_employee_id` | character varying(20) | Y |  |
| 43 | `agm_employee_id` | character varying(20) | Y |  |
| 44 | `gm_employee_id` | character varying(20) | Y |  |
| 45 | `status_type` | character varying(20) | Y |  |
| 46 | `rnv_start` | timestamp without time zone | Y |  |
| 47 | `rnv_end` | timestamp without time zone | Y |  |
| 48 | `branch_name_en` | character varying(100) | Y |  |
| 49 | `address_no_en` | character varying(200) | Y |  |
| 50 | `soi_en` | character varying(100) | Y |  |
| 51 | `street_en` | character varying(100) | Y |  |
| 52 | `district_en` | character varying(100) | Y |  |
| 53 | `amphur_en` | character varying(100) | Y |  |
| 54 | `province_en` | character varying(100) | Y |  |

### mas_store_laos

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(7) | Y |  |
| 2 | `shop_type` | character varying(20) | Y |  |
| 3 | `branch_name` | character varying(100) | Y |  |
| 4 | `branch_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(50) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `tel` | character varying(70) | Y |  |
| 9 | `address_no` | character varying(200) | Y |  |
| 10 | `soi` | character varying(100) | Y |  |
| 11 | `street` | character varying(100) | Y |  |
| 12 | `district_id` | character varying(5) | Y |  |
| 13 | `district` | character varying(100) | Y |  |
| 14 | `amphur_id` | character varying(5) | Y |  |
| 15 | `amphur` | character varying(100) | Y |  |
| 16 | `province_id` | character varying(5) | Y |  |
| 17 | `province` | character varying(100) | Y |  |
| 18 | `zip` | character varying(100) | Y |  |
| 19 | `open_date` | timestamp without time zone | Y |  |
| 20 | `close_date` | timestamp without time zone | Y |  |
| 21 | `emp_name` | character varying(200) | Y |  |
| 22 | `fc_name` | character varying(200) | Y |  |
| 23 | `fc_tel_number` | character varying(30) | Y |  |
| 24 | `fc_page_number` | character varying(30) | Y |  |
| 25 | `mn_name` | character varying(200) | Y |  |
| 26 | `mn_tel_number` | character varying(30) | Y |  |
| 27 | `mn_page_number` | character varying(30) | Y |  |
| 28 | `dv_name` | character varying(200) | Y |  |
| 29 | `dv_tel_number` | character varying(30) | Y |  |
| 30 | `dv_page_number` | character varying(30) | Y |  |
| 31 | `dv_e_mail` | character varying(100) | Y |  |
| 32 | `agm_name` | character varying(100) | Y |  |
| 33 | `agm_tel_number` | character varying(30) | Y |  |
| 34 | `agm_page_number` | character varying(30) | Y |  |
| 35 | `agm_e_mail` | character varying(100) | Y |  |
| 36 | `gm_name` | character varying(100) | Y |  |
| 37 | `gm_tel_number` | character varying(30) | Y |  |
| 38 | `gm_page_number` | character varying(30) | Y |  |
| 39 | `gm_e_mail` | character varying(100) | Y |  |
| 40 | `fc_employee_id` | character varying(20) | Y |  |
| 41 | `mn_employee_id` | character varying(20) | Y |  |
| 42 | `dv_employee_id` | character varying(20) | Y |  |
| 43 | `agm_employee_id` | character varying(20) | Y |  |
| 44 | `gm_employee_id` | character varying(20) | Y |  |
| 45 | `status_type` | character varying(20) | Y |  |
| 46 | `rnv_start` | timestamp without time zone | Y |  |
| 47 | `rnv_end` | timestamp without time zone | Y |  |
| 48 | `branch_name_en` | character varying(100) | Y |  |
| 49 | `address_no_en` | character varying(200) | Y |  |
| 50 | `soi_en` | character varying(100) | Y |  |
| 51 | `street_en` | character varying(100) | Y |  |
| 52 | `district_en` | character varying(100) | Y |  |
| 53 | `amphur_en` | character varying(100) | Y |  |
| 54 | `province_en` | character varying(100) | Y |  |

### mas_store_organize

ประมาณ 77,376 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
| 2 | `emp_id` | character varying(20) | Y |  |
| 3 | `fullname` | character varying(100) | Y |  |
| 4 | `id_card` | character varying(20) | Y |  |
| 5 | `firstname_th` | character varying(50) | Y |  |
| 6 | `lastname_th` | character varying(50) | Y |  |
| 7 | `firstname_en` | character varying(50) | Y |  |
| 8 | `lastname_en` | character varying(50) | Y |  |
| 9 | `birthday` | date | Y |  |
| 10 | `tel_no` | character varying(30) | Y |  |
| 11 | `page_no` | character varying(30) | Y |  |
| 12 | `email` | character varying(100) | Y |  |
| 13 | `group_id` | bigint | Y |  |
| 14 | `note_name` | character varying(100) | Y |  |
| 15 | `other` | character varying(100) | Y |  |
| 16 | `data_type` | character varying(5) | Y |  |
| 17 | `mobile` | character varying(30) | Y |  |
| 18 | `active_flag` | character(1) | Y |  |
| 19 | `country` | character varying(50) | Y |  |

<details><summary>Index</summary>

- `idx_mso_group_active_emp` — `btree (group_id, active_flag, emp_id, fullname)`

</details>

### mas_sub_district

ประมาณ 8,807 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `sub_district_id` | character varying(5) | N |  |
| 2 | `sub_district_name` | character varying(100) | N |  |
| 3 | `district_id` | character varying(5) | N |  |
| 4 | `province_id` | character varying(5) | N |  |

### mas_taxpayer

ประมาณ 2,682 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
| 2 | `taxpayer_id` | character varying(20) | Y |  |
| 3 | `taxpayer_name` | character varying(255) | Y |  |
| 4 | `period` | character varying(8) | Y |  |
| 5 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |

<details><summary>Index</summary>

- `idx_mas_taxpayer_lookup` — `btree (taxpayer_id, period)`

</details>

### mas_tmp_import_data

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` | numeric(38,0) | Y |  |
| 2 | `column1` | character varying(100) | Y |  |
| 3 | `column2` | character varying(100) | Y |  |
| 4 | `column3` | character varying(100) | Y |  |
| 5 | `column4` | character varying(100) | Y |  |
| 6 | `column5` | character varying(100) | Y |  |
| 7 | `column6` | character varying(100) | Y |  |
| 8 | `column7` | character varying(100) | Y |  |
| 9 | `column8` | character varying(100) | Y |  |
| 10 | `column9` | character varying(100) | Y |  |
| 11 | `column10` | character varying(100) | Y |  |
| 12 | `data_type` | character varying(20) | Y |  |
| 13 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 14 | `create_by` | character varying(100) | Y |  |

<details><summary>Index</summary>

- `mas_tmp_import_data_index1` — `btree (id)`

</details>

### mas_tmp_store

ประมาณ 0 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
| 2 | `branch_name` | character varying(200) | Y |  |
| 3 | `branch_type` | character varying(20) | Y |  |
| 4 | `status_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(5) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `zone_cd` | character varying(10) | Y |  |
| 9 | `branch_tel` | character varying(70) | Y |  |
| 10 | `address` | character varying(500) | Y |  |
| 11 | `address_no` | character varying(200) | Y |  |
| 12 | `soi` | character varying(100) | Y |  |
| 13 | `street` | character varying(100) | Y |  |
| 14 | `district_id` | character varying(5) | Y |  |
| 15 | `district` | character varying(100) | Y |  |
| 16 | `amphur_id` | character varying(5) | Y |  |
| 17 | `amphur` | character varying(100) | Y |  |
| 18 | `province_id` | character varying(5) | Y |  |
| 19 | `province` | character varying(100) | Y |  |
| 20 | `zip` | character varying(100) | Y |  |
| 21 | `open_date` | timestamp without time zone | Y |  |
| 22 | `close_date` | timestamp without time zone | Y |  |
| 23 | `branch_other` | character varying(100) | Y |  |
| 24 | `fr_sub_type` | character varying(25) | Y |  |
| 25 | `status` | character varying(20) | Y |  |
| 26 | `src_update_date` | timestamp without time zone | Y |  |
| 27 | `src_update_user` | character varying(200) | Y |  |
| 28 | `data_type` | character varying(5) | Y |  |
| 29 | `active_flag` | character(1) | Y | 'Y'::bpchar |
| 30 | `start_renovate_date` | timestamp without time zone | Y |  |
| 31 | `end_renovate_date` | timestamp without time zone | Y |  |

### mas_zone

**ใช้ใน SBPGI:** ภาค/โซน · ประมาณ 28 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `zone_id` | smallint | Y |  |
| 2 | `zone_cd` | character varying(5) | Y |  |
| 3 | `zone_name` | character varying(100) | Y |  |
| 4 | `sub_area_flag` | character varying(20) | Y |  |
| 5 | `sub_area_name` | character varying(20) | Y |  |

<details><summary>Index</summary>

- `mas_zone_pk` — `btree (zone_id)`

</details>

### master_template_columns

ประมาณ 18 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `code_value` 🔑 | character varying(100) | N |  |
| 2 | `code_name` | character varying(250) | Y |  |
| 3 | `code_type` | character varying(100) | Y |  |
| 4 | `code_type_name` | character varying(250) | Y |  |
| 5 | `seq_no` | numeric(5,0) | Y |  |
| 6 | `template` | text | Y |  |
| 7 | `type` | character varying(10) | Y |  |
| 8 | `status` | character varying(1) | Y |  |
| 9 | `entity_name` | character varying(250) | Y |  |
| 10 | `downstream` | character varying(250) | Y |  |
| 11 | `create_date` | timestamp with time zone | N | now() |
| 12 | `import_path` | character varying(20) | Y |  |
| 13 | `create_by` | character varying(250) | Y |  |
| 14 | `address_path` | text | Y |  |
| 15 | `dynamic_config` | text | Y |  |
| 16 | `api_key` | text | Y |  |
| 17 | `download_template_report` | text | Y |  |
| 18 | `payload_json` | text | Y |  |
| 19 | `system_name` | character varying(255) | Y |  |
| 20 | `is_background` | character varying(1) | Y | 'N'::character varying |

- **PK:** `code_value`

<details><summary>Index</summary>

- `PK_c38f9ec6dd503818aac756631bf` — `btree (code_value)`

</details>

### menus

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `menu_id` | integer | N |  |
| 2 | `menu_code` | character varying(100) | Y |  |
| 3 | `menu_name_th` | character varying(255) | Y |  |
| 4 | `menu_name_en` | character varying(255) | Y |  |
| 5 | `parent_id` | integer | Y |  |
| 6 | `route_path` | character varying(255) | Y |  |
| 7 | `icon` | character varying(100) | Y |  |
| 8 | `is_active` | boolean | Y |  |
| 9 | `created_date` | timestamp without time zone | Y |  |
| 10 | `updated_date` | timestamp without time zone | Y |  |

### mms_store_merge_trans

ประมาณ 7 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `mms_store_merge_id` 🔑 | bigint | N | nextval('mms_store_merge_trans_mms_store_merge_id_seq'::regc |
| 2 | `store_id` | character varying(5) | N |  |
| 3 | `effective_start_date` | character varying(8) | N |  |
| 4 | `effective_end_date` | character varying(8) | Y |  |
| 5 | `store_type` | character varying(1) | N |  |
| 6 | `book_merge_flg01` | character varying(1) | Y |  |
| 7 | `book_merge_flg02` | character varying(1) | Y |  |
| 8 | `book_merge_flg03` | character varying(1) | Y |  |
| 9 | `book_merge_flg04` | character varying(1) | Y |  |
| 10 | `book_merge_flg05` | character varying(1) | Y |  |
| 11 | `book_merge_flg06` | character varying(1) | Y |  |
| 12 | `kudsan_merge_flg01` | character varying(1) | Y |  |
| 13 | `kudsan_merge_flg02` | character varying(1) | Y |  |
| 14 | `kudsan_merge_flg03` | character varying(1) | Y |  |
| 15 | `kudsan_merge_flg04` | character varying(1) | Y |  |
| 16 | `kudsan_merge_flg05` | character varying(1) | Y |  |
| 17 | `kudsan_merge_flg06` | character varying(1) | Y |  |
| 18 | `exta_merge_flg01` | character varying(1) | Y |  |
| 19 | `exta_merge_flg02` | character varying(1) | Y |  |
| 20 | `exta_merge_flg03` | character varying(1) | Y |  |
| 21 | `exta_merge_flg04` | character varying(1) | Y |  |
| 22 | `exta_merge_flg05` | character varying(1) | Y |  |
| 23 | `exta_merge_flg06` | character varying(1) | Y |  |
| 24 | `created_date` | character varying(8) | Y |  |
| 25 | `created_time` | character varying(6) | Y |  |
| 26 | `create_user_id` | character varying(20) | Y |  |
| 27 | `updated_date` | character varying(8) | Y |  |
| 28 | `updated_time` | character varying(6) | Y |  |
| 29 | `update_user_id` | character varying(20) | Y |  |
| 30 | `function` | character varying(1) | Y |  |
| 31 | `create_date` | timestamp without time zone | N | now() |
| 32 | `create_by` | character varying(20) | Y | 'SYSTEM'::character varying |

- **PK:** `mms_store_merge_id`

<details><summary>Index</summary>

- `mms_store_merge_trans_pkey` — `btree (mms_store_merge_id)`

</details>

### mms_store_trans

ประมาณ 18 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `mms_store_id` 🔑 | bigint | N | nextval('mms_store_trans_mms_store_id_seq'::regclass) |
| 2 | `store_id` | character varying(5) | N |  |
| 3 | `effective_start_date` | character varying(8) | N |  |
| 4 | `effective_end_date` | character varying(8) | Y |  |
| 5 | `store_name` | character varying(50) | Y |  |
| 6 | `store_name_short` | character varying(20) | Y |  |
| 7 | `corporation_id` | character varying(5) | Y |  |
| 8 | `zone_cd` | character varying(2) | Y |  |
| 9 | `location_type` | character varying(1) | Y |  |
| 10 | `open_date` | character varying(8) | Y |  |
| 11 | `close_date` | character varying(8) | Y |  |
| 12 | `renovation_type` | character varying(1) | Y |  |
| 13 | `renovation_start_date` | character varying(8) | Y |  |
| 14 | `renovation_end_date` | character varying(8) | Y |  |
| 15 | `suspend_order_flg` | character varying(1) | Y |  |
| 16 | `store_address_1` | character varying(30) | Y |  |
| 17 | `store_address_2` | character varying(30) | Y |  |
| 18 | `store_address_3` | character varying(30) | Y |  |
| 19 | `store_address_4` | character varying(30) | Y |  |
| 20 | `store_sub_district_cd` | character varying(6) | Y |  |
| 21 | `store_district_cd` | character varying(4) | Y |  |
| 22 | `store_province_cd` | character varying(2) | Y |  |
| 23 | `store_postal_cd` | character varying(5) | Y |  |
| 24 | `store_phone_no` | character varying(20) | Y |  |
| 25 | `store_fax_no` | character varying(20) | Y |  |
| 26 | `store_owner_name` | character varying(50) | Y |  |
| 27 | `up_country_flg` | character varying(1) | Y |  |
| 28 | `maximum_return_ratio` | smallint | Y |  |
| 29 | `selling_floor_space` | numeric(5,1) | Y |  |
| 30 | `backroom_area` | numeric(5,1) | Y |  |
| 31 | `store_type` | character varying(1) | Y |  |
| 32 | `license_type` | character varying(1) | Y |  |
| 33 | `license_type_date` | character varying(8) | Y |  |
| 34 | `royal_fee_type` | character varying(1) | Y |  |
| 35 | `store_assortment_flg` | character varying(1) | Y |  |
| 36 | `store_food_order_flg` | character varying(1) | Y |  |
| 37 | `store_credit_limit` | numeric(9,2) | Y |  |
| 38 | `fr_statement_cycle` | character varying(1) | Y |  |
| 39 | `fr_statement_issue_date` | smallint | Y |  |
| 40 | `payment_period` | smallint | Y |  |
| 41 | `pay_by_day_cd` | character varying(1) | Y |  |
| 42 | `vat_register_no` | character varying(20) | Y |  |
| 43 | `vat_franchise_no` | character varying(20) | Y |  |
| 44 | `sequence_no` | integer | Y |  |
| 45 | `store_home_id` | character varying(20) | Y |  |
| 46 | `created_date` | character varying(8) | Y |  |
| 47 | `created_time` | character varying(6) | Y |  |
| 48 | `create_user_id` | character varying(20) | Y |  |
| 49 | `updated_date` | character varying(8) | Y |  |
| 50 | `updated_time` | character varying(6) | Y |  |
| 51 | `update_user_id` | character varying(20) | Y |  |
| 52 | `function` | character varying(1) | Y |  |
| 53 | `create_date` | timestamp without time zone | Y | now() |
| 54 | `create_by` | character varying(10) | Y | 'SYSTEM'::character varying |

- **PK:** `mms_store_id`

<details><summary>Index</summary>

- `mms_store_trans_pkey` — `btree (mms_store_id)`

</details>

### province

ประมาณ 77 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `province_id` 🔑 | character varying(3) | N |  |
| 2 | `province_name` | character varying(100) | N |  |

- **PK:** `province_id`

<details><summary>Index</summary>

- `province_pkey` — `btree (province_id)`

</details>

### role_permissions

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `role_id` | integer | N |  |
| 2 | `menu_id` | integer | N |  |
| 3 | `action_id` | integer | N |  |
| 4 | `created_date` | timestamp without time zone | Y |  |

### roles

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `role_id` | integer | N | nextval('roles_role_id_seq'::regclass) |
| 2 | `role_code` | character varying(50) | Y |  |
| 3 | `role_name` | character varying(255) | Y |  |
| 4 | `is_active` | boolean | Y |  |
| 5 | `created_date` | timestamp without time zone | Y |  |

### sap_statement_expected

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('sap_statement_expected_id_seq'::regclass) |
| 2 | `year` | character varying(4) | N |  |
| 3 | `month` | character varying(2) | N |  |
| 4 | `report_type` | character varying(20) | N |  |
| 5 | `store_id` | character varying(5) | N |  |
| 6 | `source_file_name` | character varying(255) | N |  |
| 7 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 8 | `update_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |

- **PK:** `id`
- **UNIQUE:** `year,month,report_type,store_id`

<details><summary>Index</summary>

- `sap_statement_expected_period_report_idx` — `btree (year, month, report_type)`
- `sap_statement_expected_period_report_store_uq` — `btree (year, month, report_type, store_id)`
- `sap_statement_expected_pkey` — `btree (id)`

</details>

### sap_statement_summary_source

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('sap_statement_summary_source_id_seq'::regclass) |
| 2 | `cm_id` | character varying(100) | N |  |
| 3 | `cm_entity` | character varying(100) | N |  |
| 4 | `file_name` | character varying(255) | N |  |
| 5 | `year` | character varying(4) | N |  |
| 6 | `month` | character varying(2) | N |  |
| 7 | `report_type` | character varying(20) | N |  |
| 8 | `request_year` | character varying(4) | N |  |
| 9 | `request_month` | character varying(2) | N |  |
| 10 | `request_day` | character varying(2) | Y |  |
| 11 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 12 | `update_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |

- **PK:** `id`
- **UNIQUE:** `cm_id,cm_entity,year,month,report_type`

<details><summary>Index</summary>

- `sap_statement_summary_source_file_period_report_uq` — `btree (cm_id, cm_entity, year, month, report_type)`
- `sap_statement_summary_source_period_report_idx` — `btree (year, month, report_type)`
- `sap_statement_summary_source_pkey` — `btree (id)`

</details>

### sevenshop

**ใช้ใน SBPGI:** สาขา 7-Eleven · ประมาณ 15,308 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(7) | N |  |
| 2 | `shop_type` | character varying(5) | Y |  |
| 3 | `branch_name` | character varying(100) | Y |  |
| 4 | `branch_type` | character varying(20) | Y |  |
| 5 | `area_id` | character varying(50) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `region` | character varying(100) | Y |  |
| 8 | `tel` | character varying(70) | Y |  |
| 9 | `address_no` | character varying(200) | Y |  |
| 10 | `soi` | character varying(100) | Y |  |
| 11 | `street` | character varying(100) | Y |  |
| 12 | `district_id` | character varying(5) | Y |  |
| 13 | `district` | character varying(100) | Y |  |
| 14 | `amphur_id` | character varying(5) | Y |  |
| 15 | `amphur` | character varying(100) | Y |  |
| 16 | `province_id` | character varying(5) | Y |  |
| 17 | `province` | character varying(100) | Y |  |
| 18 | `zip` | character varying(100) | Y |  |
| 19 | `open_date` | timestamp without time zone | Y |  |
| 20 | `close_date` | timestamp without time zone | Y |  |
| 21 | `mgr_name` | character varying(200) | Y |  |
| 22 | `fc_name` | character varying(200) | Y |  |
| 23 | `fc_tel` | character varying(30) | Y |  |
| 24 | `fc_page` | character varying(30) | Y |  |
| 25 | `mn_name` | character varying(200) | Y |  |
| 26 | `mn_tel` | character varying(30) | Y |  |
| 27 | `mn_page` | character varying(30) | Y |  |
| 28 | `dv_name` | character varying(200) | Y |  |
| 29 | `dv_tel` | character varying(30) | Y |  |
| 30 | `dv_page` | character varying(30) | Y |  |
| 31 | `dv_email` | character varying(100) | Y |  |
| 32 | `avp_name` | character varying(200) | Y |  |
| 33 | `avp_tel` | character varying(30) | Y |  |
| 34 | `avp_page` | character varying(30) | Y |  |
| 35 | `avp_email` | character varying(100) | Y |  |
| 36 | `gm_name` | character varying(200) | Y |  |
| 37 | `gm_tel` | character varying(30) | Y |  |
| 38 | `gm_page` | character varying(30) | Y |  |
| 39 | `gm_email` | character varying(100) | Y |  |
| 40 | `status` | character varying(20) | Y |  |
| 41 | `update_date` | timestamp without time zone | Y |  |
| 42 | `update_user` | character varying(200) | Y |  |
| 43 | `mn_email` | character varying(100) | Y |  |
| 44 | `fc_email` | character varying(100) | Y |  |
| 45 | `zone_cd` | character varying(10) | Y |  |
| 46 | `fc_employee_id` | character varying(20) | Y |  |
| 47 | `mn_employee_id` | character varying(20) | Y |  |
| 48 | `dv_employee_id` | character varying(20) | Y |  |
| 49 | `avp_employee_id` | character varying(20) | Y |  |
| 50 | `gm_employee_id` | character varying(20) | Y |  |
| 51 | `status_type` | character varying(20) | Y |  |
| 52 | `start_renovate_date` | timestamp without time zone | Y |  |
| 53 | `end_renovate_date` | timestamp without time zone | Y |  |
| 54 | `sales_area` | numeric(8,2) | Y |  |
| 55 | `store_type_code` | character varying(5) | Y |  |
| 56 | `ptt_code` | character varying(5) | Y |  |

<details><summary>Index</summary>

- `sevenshop_index1` — `btree (branch_id)`
- `sevenshop_index2` — `btree (shop_type)`
- `sevenshop_index3` — `btree (dv_email)`
- `sevenshop_index4` — `btree (shop_type, branch_type)`

</details>

### skip_statement

เก็บ statement report ที่ถูกซ่อนชั่วคราว เมื่อร้านถูก skip — structure เหมือน statement table เพื่อย้าย data ไปมา · ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('skip_statement_id_seq'::regclass) |
| 2 | `store_id` | character varying | N |  |
| 3 | `tax_id` | character varying | N |  |
| 4 | `report_type` | character varying | N |  |
| 5 | `year` | character varying | N |  |
| 6 | `month` | character varying | N |  |
| 7 | `day` | character varying | N |  |
| 8 | `cm_id` | character varying | N |  |
| 9 | `cm_entity` | character varying | N |  |
| 10 | `file_name` | character varying | N |  |
| 11 | `type` | character varying | N |  |
| 12 | `create_date` | timestamp with time zone | N | now() |
| 13 | `update_date` | timestamp with time zone | N | now() |
| 14 | `action_flag` | character varying(1) | Y |  |
| 15 | `verify_flag` | character varying(1) | Y |  |
| 16 | `content_type` | character varying(30) | Y |  |
| 17 | `action_date` | timestamp with time zone | Y |  |
| 18 | `zone_cd` | character varying(5) | Y |  |
| 19 | `create_user` | character varying(255) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `idx_skip_stmt_store_report` — `btree (store_id, report_type)`
- `idx_skip_stmt_ym_concat` — `btree ((((year)::text || lpad((month)::text, 2, '0'::text))))`
- `pk_skip_statement` — `btree (id)`

</details>

### statement

ประมาณ 174,084 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('statement_id_seq'::regclass) |
| 2 | `store_id` | character varying | N |  |
| 3 | `tax_id` | character varying | N |  |
| 4 | `report_type` | character varying | N |  |
| 5 | `year` | character varying | N |  |
| 6 | `month` | character varying | N |  |
| 7 | `day` | character varying | N |  |
| 8 | `cm_id` | character varying | N |  |
| 9 | `cm_entity` | character varying | N |  |
| 10 | `file_name` | character varying | N |  |
| 11 | `type` | character varying | N |  |
| 12 | `create_date` | timestamp with time zone | N | now() |
| 13 | `update_date` | timestamp with time zone | N | now() |
| 14 | `action_flag` | character varying(1) | Y |  |
| 15 | `verify_flag` | character varying(1) | Y |  |
| 16 | `content_type` | character varying(30) | Y |  |
| 17 | `action_date` | timestamp with time zone | Y |  |
| 18 | `zone_cd` | character varying(5) | Y |  |
| 19 | `create_user` | character varying(255) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `idx_stmt_perf_statement_daily` — `btree (report_type, ((((year)::text || lpad((month)::text, 2, '0'::text)) || lpad((day)::text, 2, '0'::text))), store_id) INCLUDE (id, cm_id, year, month, day, create_date, content_type, tax_id) WHERE ((((COALESCE(verify_flag, ''::character varying))::text = ''::text) OR ((verify_flag)::text = 'Y'::text)) AND (day IS NOT NULL) AND ((day)::text <> ''::text))`
- `idx_stmt_perf_statement_monthly` — `btree (report_type, (((year)::text || lpad((month)::text, 2, '0'::text))), store_id) INCLUDE (id, cm_id, year, month, day, create_date, content_type, tax_id) WHERE ((((COALESCE(verify_flag, ''::character varying))::text = ''::text) OR ((verify_flag)::text = 'Y'::text)) AND ((day IS NULL) OR ((day)::text = ''::text)))`
- `idx_stmt_store_report` — `btree (store_id, report_type)`
- `idx_stmt_ym_concat` — `btree ((((year)::text || lpad((month)::text, 2, '0'::text))))`
- `idx_stmt_ymd_concat` — `btree (((((year)::text || lpad((month)::text, 2, '0'::text)) || lpad((day)::text, 2, '0'::text))))`
- `pk_f05684e32986e91bab86bef5d0a` — `btree (id)`

</details>

### statement_summary

ประมาณ 199 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('statement_summary_id_seq'::regclass) |
| 2 | `year` | character varying(4) | N |  |
| 3 | `month` | character varying(2) | N |  |
| 4 | `report_type` | character varying(20) | N |  |
| 5 | `sum_record` | integer | N |  |
| 6 | `received_record` | integer | N | 0 |
| 7 | `file_name` | character varying(100) | Y |  |
| 8 | `file_size` | integer | Y |  |
| 9 | `file_summary` | integer | Y |  |
| 10 | `last_progress_email_at` | timestamp with time zone | Y |  |
| 11 | `progress_email_flag` | character varying(1) | N | 'N'::character varying |
| 12 | `complete_email_flag` | character varying(1) | N | 'N'::character varying |
| 13 | `complete_date` | timestamp with time zone | Y |  |
| 14 | `create_date` | timestamp with time zone | N | now() |
| 15 | `update_date` | timestamp with time zone | N | now() |
| 16 | `statement_from` | character varying(20) | Y | 'STA'::character varying |

- **PK:** `id`

<details><summary>Index</summary>

- `statement_summary_pkey` — `btree (id)`
- `uk_statement_summary_sap` — `btree (year, month, report_type) WHERE ((statement_from)::text = 'SAP'::text)`
- `uk_statement_summary_sta` — `btree (year, month, report_type, file_name) WHERE ((statement_from)::text = 'STA'::text)`

</details>

### store

**ใช้ใน SBPGI:** ค้นหา/รายละเอียดร้าน · ข้อมูลร้านค้า · ประมาณ 19,402 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` 🔑 | character varying(10) | N |  |
| 2 | `store_name` | character varying(200) | Y |  |
| 3 | `business_type` | character varying(10) | Y |  |
| 4 | `store_type` | character varying(10) | Y |  |
| 5 | `area_id` | character varying(10) | Y |  |
| 6 | `area_name` | character varying(100) | Y |  |
| 7 | `zone` | character varying(10) | Y |  |
| 8 | `zone_cd` | character varying(10) | Y |  |
| 9 | `store_phone` | character varying(70) | Y |  |
| 10 | `full_address` | text | Y |  |
| 11 | `address_no` | character varying(50) | Y |  |
| 12 | `address_soi` | character varying(50) | Y |  |
| 13 | `address_street` | character varying(50) | Y |  |
| 14 | `address_province_name` | character varying(100) | Y |  |
| 15 | `address_province_id` | integer | Y |  |
| 16 | `address_district_name` | character varying(100) | Y |  |
| 17 | `address_district_id` | integer | Y |  |
| 18 | `address_sub_district_name` | character varying(100) | Y |  |
| 19 | `address_sub_district_id` | integer | Y |  |
| 20 | `address_postal_code` | character varying(10) | Y |  |
| 21 | `store_open_date` | date | Y |  |
| 22 | `store_close_date` | date | Y |  |
| 23 | `store_status_type` | character varying(10) | Y |  |
| 24 | `src_update_date` | timestamp with time zone | Y |  |
| 25 | `src_update_by` | character varying(100) | Y |  |
| 26 | `data_type` | character varying(10) | Y |  |
| 27 | `active_flag` | character varying(50) | Y |  |
| 28 | `start_renovate_date` | date | Y |  |
| 29 | `finish_renovate_date` | date | Y |  |
| 30 | `address_moo` | character varying(50) | Y |  |
| 31 | `address_building` | character varying(50) | Y |  |
| 32 | `address_floor` | character varying(50) | Y |  |

- **PK:** `store_id`

<details><summary>Index</summary>

- `pk_store` — `btree (store_id)`

</details>

### store_contract_history

ประมาณ 59 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | Y |  |
| 2 | `seq_no` | integer | N |  |
| 3 | `store_partners_id` | bigint | Y |  |
| 4 | `start_date` | date | Y |  |
| 5 | `end_date` | date | Y |  |
| 6 | `signed_date` | date | Y |  |
| 7 | `edit_end_date` | date | Y |  |
| 8 | `remark` | text | Y |  |
| 9 | `create_date` | timestamp with time zone | Y |  |
| 10 | `create_user` | text | Y |  |
| 11 | `update_date` | timestamp with time zone | Y |  |
| 12 | `update_user` | text | Y |  |
| 13 | `update_fr_store` | text | Y |  |

### store_old

ข้อมูลร้าน · ประมาณ 5 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | Y |  |
| 2 | `effective_start_date` | character varying(8) | Y |  |
| 3 | `effective_end_date` | character varying(8) | Y |  |
| 4 | `store_name` | character varying(200) | Y |  |
| 5 | `store_name_short` | character varying(20) | Y |  |
| 6 | `corporation_id` | character varying(5) | Y |  |
| 7 | `zone_cd` | character varying(10) | Y |  |
| 8 | `location_type` | character varying(1) | Y |  |
| 9 | `open_date` | character varying(8) | Y |  |
| 10 | `close_date` | character varying(8) | Y |  |
| 11 | `renovation_start_date` | character varying(8) | Y |  |
| 12 | `renovation_end_date` | character varying(8) | Y |  |
| 13 | `suspend_order_flg` | character varying(1) | Y |  |
| 14 | `store_address_1` | character varying(30) | Y |  |
| 15 | `store_address_2` | character varying(30) | Y |  |
| 16 | `store_address_3` | character varying(30) | Y |  |
| 17 | `store_address_4` | character varying(30) | Y |  |
| 18 | `store_district_cd` | character varying(4) | Y |  |
| 19 | `store_province_cd` | character varying(2) | Y |  |
| 20 | `store_postal_cd` | character varying(5) | Y |  |
| 21 | `store_phone_no` | character varying(20) | Y |  |
| 22 | `store_fax_no` | character varying(20) | Y |  |
| 23 | `store_owner_name` | character varying(50) | Y |  |
| 24 | `teller_cd` | character varying(3) | Y |  |
| 25 | `start_range` | numeric(9,2) | Y |  |
| 26 | `end_range` | numeric(9,2) | Y |  |
| 27 | `fee_amount` | numeric(5,2) | Y |  |
| 28 | `special_fee_amount` | numeric(5,2) | Y |  |
| 29 | `minimum_fee_amount` | numeric(5,2) | Y |  |
| 30 | `up_country_flg` | character varying(1) | Y |  |
| 31 | `standard_change_amt` | numeric(9,2) | Y |  |
| 32 | `maximum_return_ratio` | smallint | Y |  |
| 33 | `selling_floor_space` | numeric(5,1) | Y |  |
| 34 | `backroom_area` | numeric(5,1) | Y |  |
| 35 | `store_type` | character varying(10) | Y |  |
| 36 | `license_type` | character(1) | Y |  |
| 37 | `royal_fee_type` | character(1) | Y |  |
| 38 | `store_credit_limit` | numeric(9,2) | Y |  |
| 39 | `fr_statement_cycle` | character(1) | Y |  |
| 40 | `fr_statement_issue_date` | smallint | Y |  |
| 41 | `payment_period` | smallint | Y |  |
| 42 | `pay_by_day_cd` | character(1) | Y |  |
| 43 | `vat_no` | character varying(15) | Y |  |
| 44 | `bank_id` | character varying(15) | Y |  |
| 45 | `bank_branch_id` | character varying(3) | Y |  |
| 46 | `bank_account_type` | character(1) | Y |  |
| 47 | `bank_account_no` | character varying(11) | Y |  |
| 48 | `sequence_no` | integer | Y |  |
| 49 | `magazine_location` | character(1) | Y |  |
| 50 | `magazine_shelf_width` | smallint | Y |  |
| 51 | `magazine_shelf_height` | smallint | Y |  |
| 52 | `magazine_shelf_qty` | smallint | Y |  |
| 53 | `update_date` | character varying(8) | Y |  |
| 54 | `update_time` | character varying(6) | Y |  |
| 55 | `update_user_id` | character varying(20) | Y |  |
| 56 | `area_id` | character varying(10) | Y |  |
| 57 | `area_name` | character varying(100) | Y |  |
| 58 | `zone` | character varying(10) | Y |  |
| 59 | `store_phone` | character varying(15) | Y |  |
| 60 | `full_address` | text | Y |  |
| 61 | `address_no` | character varying(50) | Y |  |
| 62 | `address_soi` | character varying(50) | Y |  |
| 63 | `address_street` | character varying(50) | Y |  |
| 64 | `address_province_name` | character varying(100) | Y |  |
| 65 | `address_province_id` | integer | Y |  |
| 66 | `address_district_name` | character varying(100) | Y |  |
| 67 | `address_district_id` | integer | Y |  |
| 68 | `address_sub_district_name` | character varying(100) | Y |  |
| 69 | `address_sub_district_id` | integer | Y |  |
| 70 | `address_postal_code` | character varying(10) | Y |  |
| 71 | `store_open_date` | date | Y |  |
| 72 | `store_close_date` | date | Y |  |
| 73 | `store_status_type` | character varying(10) | Y |  |
| 74 | `src_update_date` | timestamp with time zone | Y |  |
| 75 | `src_update_by` | character varying(100) | Y |  |
| 76 | `data_type` | character varying(10) | Y |  |
| 77 | `active_flag` | character varying(50) | Y |  |
| 78 | `start_renovate_date` | date | Y |  |
| 79 | `finish_renovate_date` | date | Y |  |
| 80 | `address_moo` | character varying(100) | Y |  |
| 81 | `address_building` | character varying(100) | Y |  |
| 82 | `address_floor` | character varying(100) | Y |  |

<details><summary>Index</summary>

- `store_index1` — `btree (zone_cd)`
- `store_index2` — `btree (TRIM(BOTH FROM zone_cd))`

</details>

### store_organize

ประมาณ 79,722 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | N |  |
| 2 | `employee_id` | character varying(50) | Y |  |
| 3 | `fullname` | character varying(200) | Y |  |
| 4 | `national_id` | character varying(20) | Y |  |
| 5 | `first_name` | character varying(100) | Y |  |
| 6 | `last_name` | character varying(100) | Y |  |
| 7 | `first_name_en` | character varying(100) | Y |  |
| 8 | `last_name_en` | character varying(100) | Y |  |
| 9 | `birthday` | date | Y |  |
| 10 | `phone` | character varying(15) | Y |  |
| 11 | `office_phone` | character varying(15) | Y |  |
| 12 | `email` | character varying(255) | Y |  |
| 13 | `group_id` | character varying(50) | Y |  |
| 14 | `lotus_note_name` | character varying(200) | Y |  |
| 15 | `other` | character varying(200) | Y |  |
| 16 | `data_type` | character varying(10) | Y |  |
| 17 | `mobile` | character varying(15) | Y |  |
| 18 | `active_flag` | character varying(10) | Y | 'Y'::character varying |

### store_organize_old

ประมาณ 138,802 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
| 2 | `emp_id` | character varying(20) | Y |  |
| 3 | `fullname` | character varying(100) | Y |  |
| 4 | `id_card` | character varying(20) | Y |  |
| 5 | `firstname_th` | character varying(50) | Y |  |
| 6 | `lastname_th` | character varying(50) | Y |  |
| 7 | `firstname_en` | character varying(50) | Y |  |
| 8 | `lastname_en` | character varying(50) | Y |  |
| 9 | `birthday` | date | Y |  |
| 10 | `tel_no` | character varying(30) | Y |  |
| 11 | `page_no` | character varying(30) | Y |  |
| 12 | `email` | character varying(100) | Y |  |
| 13 | `group_id` | bigint | Y |  |
| 14 | `note_name` | character varying(100) | Y |  |
| 15 | `other` | character varying(100) | Y |  |
| 16 | `data_type` | character varying(5) | Y |  |
| 17 | `mobile` | character varying(30) | Y |  |
| 18 | `active_flag` | character(1) | Y | 'Y'::bpchar |
| 19 | `country` | character varying(50) | Y |  |

- **FK:** `group_id` → `business_group`.`group_id`

<details><summary>Index</summary>

- `store_organize_idx` — `btree (branch_id, emp_id, fullname, id_card, firstname_th, lastname_th, firstname_en, lastname_en, group_id, data_type)`

</details>

### store_partner

ตารางข้อมูลเจ้าของแฟรนไชส์ · ประมาณ 7,600 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `partner_id` 🔑 | character varying(50) | N |  |
| 2 | `first_name` | character varying(100) | Y |  |
| 3 | `last_name` | character varying(100) | Y |  |
| 4 | `status` | character varying(10) | Y |  |
| 5 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 6 | `email` | character varying(100) | Y |  |

- **PK:** `partner_id`

<details><summary>Index</summary>

- `idx_store_partner_partner_id` — `btree (partner_id)`
- `idx_store_partner_status` — `btree (status)`
- `store_partner_pkey` — `btree (partner_id)`

</details>

### store_partner_contacts

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('store_partner_contacts_id_seq'::regclass) |
| 2 | `region` | character varying(100) | N |  |
| 3 | `store_id` | character varying(50) | Y |  |
| 4 | `department` | character varying(100) | N |  |
| 5 | `name` | character varying(150) | N |  |
| 6 | `telephone` | character varying(50) | N |  |
| 7 | `created_at` | timestamp with time zone | N | now() |
| 8 | `updated_at` | timestamp with time zone | N | now() |

- **PK:** `id`

<details><summary>Index</summary>

- `store_partner_contacts_pkey` — `btree (id)`
- `store_partner_contacts_region_key` — `btree (region)`

</details>

### store_sbp

ข้อมูลร้าน SBP · ประมาณ 11,583 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `order_id` 🔑 | bigint | N |  |
| 2 | `reference_order_id` | bigint | Y |  |
| 3 | `store_id` | character varying(10) | Y |  |
| 4 | `store_sbp_type` | character varying(10) | Y |  |
| 5 | `store_sbp_sub_type` | character varying(10) | Y |  |
| 6 | `area_type` | character varying(10) | Y |  |
| 7 | `location` | character varying(10) | Y |  |
| 8 | `start_sbp_date` | date | Y |  |
| 9 | `open_date` | date | Y |  |
| 10 | `close_date` | date | Y |  |
| 11 | `contract_start_date` | date | Y |  |
| 12 | `contract_end_date` | date | Y |  |
| 13 | `active_flag` | character varying(1) | Y | 'Y'::character varying |
| 14 | `transfer_date` | date | Y |  |
| 15 | `juristics_id` | bigint | Y |  |
| 16 | `contract_cancel_date` | date | Y |  |
| 17 | `contract_cancel_detail` | text | Y |  |
| 18 | `contract_cancel_type` | character varying(10) | Y |  |
| 19 | `contract_cancel_reason` | character varying(10) | Y |  |
| 20 | `contract_cancel_reason_other` | text | Y |  |
| 21 | `performance_count_type` | character varying(10) | Y |  |
| 22 | `performance_count_type_show` | character varying(10) | Y |  |
| 23 | `transfer_to_store_id` | character varying(10) | Y |  |
| 24 | `new_order_id` | bigint | Y |  |
| 25 | `old_order_id` | bigint | Y |  |
| 26 | `current_contract_date` | date | Y |  |
| 27 | `store_partners_id` | bigint | Y |  |
| 28 | `co_manager_store_partners_id` | bigint | Y |  |
| 29 | `assistant_manager_user_id` | bigint | Y |  |
| 30 | `successor_store_partners_id` | bigint | Y |  |
| 31 | `current_manager_store_partners_id` | bigint | Y |  |
| 32 | `sbp_share` | numeric(18,2) | Y |  |
| 33 | `label_print_address` | character varying(10) | Y |  |
| 34 | `is_partner_contract_changed` | character varying(10) | Y |  |
| 35 | `partner_contract_changed_date` | date | Y |  |
| 36 | `store_format` | character varying(10) | Y |  |
| 37 | `open_type` | character varying(10) | Y |  |
| 38 | `operate_type` | character varying(10) | Y |  |
| 39 | `operate_sub_type` | character varying(10) | Y |  |
| 40 | `owner_type` | character varying(10) | Y |  |
| 41 | `store_source` | character varying(10) | Y |  |
| 42 | `assessment_round1_score` | numeric(18,2) | Y |  |
| 43 | `assessment_round2_score` | numeric(18,2) | Y |  |
| 44 | `assessment_round3_score` | numeric(18,2) | Y |  |
| 45 | `assessment_round3_grade` | character varying(10) | Y |  |
| 46 | `authorized_signatory_1_name` | character varying(200) | Y |  |
| 47 | `authorized_signatory_2_name` | character varying(200) | Y |  |
| 48 | `authorized_signatory_3_name` | character varying(200) | Y |  |
| 49 | `relocation_open_date` | date | Y |  |
| 50 | `contract_usage_type` | character varying(10) | Y |  |
| 51 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 52 | `create_by` | bigint | Y |  |
| 53 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 54 | `update_by` | bigint | Y |  |

- **PK:** `order_id`

<details><summary>Index</summary>

- `store_sbp_pkey` — `btree (order_id)`

</details>

### store_sbp_20260708

ตารางหลักข้อมูลร้าน SBP รวบรวมข้อมูลจาก store_master และ store_partner · ประมาณ 10,907 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(20) | Y |  |
| 2 | `order_id` 🔑 | character varying(50) | N |  |
| 3 | `parent_order_id` | character varying(50) | Y |  |
| 4 | `store_name` | character varying(200) | Y |  |
| 5 | `store_type` | character varying(3) | Y |  |
| 6 | `partner_id1` | character varying(50) | Y |  |
| 7 | `partner_id2` | character varying(50) | Y |  |
| 8 | `partner_id3` | character varying(50) | Y |  |
| 9 | `partner_id4` | character varying(50) | Y |  |
| 10 | `juristic_id` | integer | Y |  |
| 11 | `juristic_group` | integer | Y |  |
| 12 | `region` | character varying(10) | Y |  |
| 13 | `start_date` | date | Y |  |
| 14 | `to_store_id` | character varying(20) | Y |  |
| 15 | `to_store_date` | date | Y |  |
| 16 | `create_date` | date | Y | CURRENT_DATE |
| 17 | `status` | character varying(10) | Y |  |
| 18 | `cancel_date` | date | Y |  |
| 19 | `cancel_type` | character varying(5) | Y |  |
| 20 | `reward_contract_type` | character varying(2) | Y |  |
| 21 | `update_date` | timestamp without time zone | Y |  |
| 22 | `update_user` | character varying(100) | Y |  |
| 23 | `change_partner_contact_flag` | character(1) | Y | 'N'::bpchar |

- **PK:** `order_id`

<details><summary>Index</summary>

- `idx_store_sbp_parent` — `btree (parent_order_id)`
- `idx_store_sbp_parent_order` — `btree (parent_order_id)`
- `pk_store_sbp` — `btree (order_id)`

</details>

### store_sbp_log

ตารางประวัติการย้ายร้านจาก store_id เดิมไป store_id ใหม่ · ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `log_id` 🔑 | bigint | N | nextval('store_sbp_log_log_id_seq'::regclass) |
| 2 | `from_store_id` | character varying(20) | N |  |
| 3 | `to_store_id` | character varying(20) | N |  |
| 4 | `move_start_at` | timestamp without time zone | N | CURRENT_TIMESTAMP |

- **PK:** `log_id`

<details><summary>Index</summary>

- `idx_store_sbp_log_from_store_id` — `btree (from_store_id)`
- `idx_store_sbp_log_move_start_at` — `btree (move_start_at)`
- `idx_store_sbp_log_to_store_id` — `btree (to_store_id)`
- `store_sbp_log_pkey` — `btree (log_id)`

</details>

### system_param

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('system_param_id_seq'::regclass) |
| 2 | `param_name` | character varying(200) | N |  |
| 3 | `param_value` | text | Y |  |
| 4 | `description` | text | Y |  |
| 5 | `active_flag` | character varying(10) | Y |  |
| 6 | `create_by` | character varying(100) | Y |  |
| 7 | `create_date` | timestamp with time zone | Y | now() |

- **PK:** `id`

<details><summary>Index</summary>

- `system_param_pkey` — `btree (id)`

</details>

### temp_control_file

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_name` 🔑 | character varying | N |  |
| 2 | `expected_count` | integer | N |  |
| 3 | `create_date` | timestamp with time zone | N | now() |

- **PK:** `file_name`

<details><summary>Index</summary>

- `PK_temp_control_file` — `btree (file_name)`

</details>

### temp_exp_sub

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `file_name` | text | Y |  |
| 2 | `col0` | text | Y |  |
| 3 | `col1` | text | Y |  |
| 4 | `col2` | text | Y |  |
| 5 | `col3` | text | Y |  |
| 6 | `col4` | text | Y |  |
| 7 | `col5` | text | Y |  |
| 8 | `col6` | text | Y |  |
| 9 | `id` 🔑 | bigint | N | nextval('temp_exp_sub_id_seq'::regclass) |
| 10 | `create_date` | timestamp with time zone | N | CURRENT_TIMESTAMP |

- **PK:** `id`

<details><summary>Index</summary>

- `temp_exp_sub_pkey` — `btree (id)`

</details>

### temp_pre_statement

ประมาณ 1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `file_name` | text | Y |  |
| 3 | `col0` | text | Y |  |
| 4 | `col1` | text | Y |  |
| 5 | `col2` | text | Y |  |
| 6 | `col3` | text | Y |  |
| 7 | `col4` | text | Y |  |
| 8 | `col5` | text | Y |  |
| 9 | `col6` | text | Y |  |
| 10 | `col7` | text | Y |  |
| 11 | `col8` | text | Y |  |
| 12 | `col9` | text | Y |  |
| 13 | `col10` | text | Y |  |
| 14 | `col11` | text | Y |  |
| 15 | `col12` | text | Y |  |
| 16 | `col13` | text | Y |  |
| 17 | `col14` | text | Y |  |
| 18 | `col15` | text | Y |  |
| 19 | `col16` | text | Y |  |
| 20 | `col17` | text | Y |  |
| 21 | `col18` | text | Y |  |
| 22 | `col19` | text | Y |  |
| 23 | `col20` | text | Y |  |
| 24 | `col21` | text | Y |  |
| 25 | `col22` | text | Y |  |
| 26 | `col23` | text | Y |  |
| 27 | `col24` | text | Y |  |
| 28 | `col25` | text | Y |  |
| 29 | `col26` | text | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `idx_temp_pre_stmt_file_name` — `btree (file_name)`
- `idx_temp_pre_stmt_filename_id` — `btree (file_name, id)`
- `temp_pre_statement_pkey` — `btree (id)`

</details>

### upload_general

**ใช้ใน SBPGI:** ไฟล์แนบ generic · ประมาณ 235 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('upload_general_id_seq'::regclass) |
| 2 | `job_id` | integer | Y |  |
| 3 | `audit_log_id` | integer | Y |  |
| 4 | `doc_id` | character varying(20) | Y |  |
| 5 | `entity_name` | character varying(250) | Y |  |
| 6 | `filename` | character varying(200) | Y |  |
| 7 | `code_value` | character varying(200) | Y |  |
| 8 | `code_type` | character varying(100) | Y |  |
| 9 | `key` | text | Y |  |
| 10 | `create_date` | timestamp with time zone | N | now() |
| 11 | `create_by` | character varying(250) | Y |  |

- **PK:** `id`
- **FK:** `job_id` → `general_upload_data_page_job`.`id`
- **FK:** `audit_log_id` → `general_upload_data_page_audit_log`.`id`

<details><summary>Index</summary>

- `PK_838988356740e5954c6a323d0c6` — `btree (id)`

</details>

### user_group_members

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |

### user_sub_group

ตารางเก็บข้อมูลกลุ่มย่อยของผู้ใช้งาน · ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |
| 3 | `store_type` | character varying(5) | Y |  |
| 4 | `store_area` | character varying(5) | Y |  |

### users

ประมาณ 1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | integer | N | nextval('users_id_seq'::regclass) |
| 2 | `firstname` | text | Y |  |
| 3 | `lastname` | text | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `users_pkey` — `btree (id)`

</details>

### view_column

ประมาณ 816 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `view_id` | integer | N |  |
| 2 | `seq_no` | integer | N |  |
| 3 | `col_name` | character varying(500) | Y |  |
| 4 | `dbcol_name` | character varying(500) | Y |  |
| 5 | `create_date` | timestamp without time zone | Y |  |
| 6 | `create_user` | character varying(200) | Y |  |
| 7 | `update_date` | timestamp without time zone | Y |  |
| 8 | `update_user` | character varying(200) | Y |  |
| 9 | `color_code` | character(10) | Y |  |
| 10 | `hf_type` | character varying(10) | Y |  |
| 11 | `hf_json_attribute` | character varying(4000) | Y |  |
| 12 | `hf_col_start` | integer | Y |  |
| 13 | `hf_col_end` | integer | Y |  |
| 14 | `body_json_attribute` | character varying(4000) | Y |  |
| 15 | `row_level` | integer | Y |  |
| 16 | `hf_row_start` | integer | Y |  |
| 17 | `hf_row_end` | integer | Y |  |

### wf

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_id` 🔑 | bigint | N |  |
| 2 | `wf_system` | character varying(300) | N |  |
| 3 | `wf_name` | character varying(3000) | N |  |
| 4 | `wf_name_th` | character varying(400) | Y |  |

- **PK:** `wf_id`

<details><summary>Index</summary>

- `wf_pk` — `btree (wf_id)`

</details>

### wf_approve

ประมาณ 155,740 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_approve_id` 🔑 | numeric(38,0) | N |  |
| 2 | `wf_version_id` | numeric(38,0) | Y |  |
| 3 | `transaction_pk` | character varying(50) | Y |  |
| 4 | `group_id` | numeric(38,0) | Y |  |
| 5 | `user_id` | character varying(20) | Y |  |
| 6 | `wf_step_id` | numeric(38,0) | Y |  |
| 7 | `action_index` | numeric(38,0) | Y |  |
| 8 | `approve_remark` | character varying(4000) | Y |  |
| 9 | `approve_date` | timestamp without time zone | Y |  |
| 10 | `create_by` | character varying(20) | Y |  |
| 11 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 12 | `approve_no` | numeric(38,0) | Y |  |
| 13 | `approve_info1` | character varying(4000) | Y |  |
| 14 | `approve_info2` | character varying(4000) | Y |  |
| 15 | `approve_info3` | character varying(4000) | Y |  |
| 16 | `approve_info4` | character varying(4000) | Y |  |
| 17 | `approve_info5` | character varying(4000) | Y |  |
| 18 | `approve_desc` | character varying(4000) | Y |  |

- **PK:** `wf_approve_id`

<details><summary>Index</summary>

- `idx_wf_approve_trn` — `btree (transaction_pk, wf_version_id, wf_step_id)`
- `wf_approve_pk` — `btree (wf_approve_id)`

</details>

### wf_email_template

ประมาณ 118 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `WF_EMAIL_TEMPLATE_ID` | numeric | N |  |
| 2 | `WF_EMAIL_TEMPLATE_NAME` | character varying(300) | Y |  |
| 3 | `WF_EMAIL_TEMPLATE_DESC` | character varying(3000) | Y |  |
| 4 | `DB_VIEW_NAME` | character varying(300) | Y |  |
| 5 | `DB_PK_COLUMN_NAME` | character varying(300) | Y |  |
| 6 | `SUBJECT_FORMAT` | character varying(500) | Y |  |
| 7 | `CONTENT_FORMAT` | text | Y |  |

### wf_route

ประมาณ 169 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_route_id` | numeric | N |  |
| 2 | `wf_action_type` | character varying(20) | Y |  |
| 3 | `wf_from_step_id` | numeric | N |  |
| 4 | `wf_to_step_id` | numeric | Y |  |
| 5 | `wf_to_status_id` | numeric | N |  |
| 6 | `action_name` | character varying(900) | Y |  |
| 7 | `wf_version_id` | numeric | N |  |
| 8 | `route_constraint_a` | character varying(90) | Y |  |
| 9 | `route_comparator` | character varying(3) | Y |  |
| 10 | `route_constraint_b` | character varying(90) | Y |  |
| 11 | `then_monitor_with_id` | numeric | Y |  |
| 12 | `then_email_with_id` | numeric | Y |  |

### wf_status

ประมาณ 86 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_status_id` | bigint | N |  |
| 2 | `wf_version_id` | bigint | N |  |
| 3 | `wf_status_name` | character varying(200) | N |  |
| 4 | `wf_status_seq` | bigint | N |  |
| 5 | `wf_status_name_kh` | character varying(300) | Y |  |
| 6 | `wf_status_name_la` | character varying(300) | Y |  |
| 7 | `wf_status_name_en` | character varying(300) | Y |  |

- **PK:** `wf_status_id,wf_version_id`

<details><summary>Index</summary>

- `wf_status_pk` — `btree (wf_status_id, wf_version_id)`
- `wf_status_version_idx` — `btree (wf_version_id)`

</details>

### wf_step

ประมาณ 86 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_step_id` | bigint | N |  |
| 2 | `wf_version_id` | bigint | N |  |
| 3 | `step_name` | character varying(200) | N |  |
| 4 | `step_desc` | character varying(3000) | Y |  |
| 5 | `step_owner_type` | character varying(20) | N |  |
| 6 | `step_owner_data` | character varying(4000) | Y |  |
| 7 | `step_seq` | bigint | N |  |
| 8 | `save_allowed_flag` | smallint | N | 0 |
| 9 | `save_action_name` | character varying(900) | Y |  |
| 10 | `remark_allowed_flag` | smallint | N | 0 |
| 11 | `remark_label` | character varying(3000) | Y |  |
| 12 | `wf_reason_topic_id` | bigint | Y |  |
| 13 | `wf_reason_topic_label` | character varying(3000) | Y |  |

- **PK:** `wf_step_id,wf_version_id`

<details><summary>Index</summary>

- `wf_step_pk` — `btree (wf_step_id, wf_version_id)`
- `wf_step_version_idx` — `btree (wf_version_id)`

</details>

### wf_step_history

ประมาณ 161,813 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_step_history_id` | numeric(38,0) | Y |  |
| 2 | `wf_version_id` | numeric(38,0) | Y |  |
| 3 | `transaction_pk` | character varying(300) | Y |  |
| 4 | `action_name` | character varying(900) | Y |  |
| 5 | `created_by` | character varying(2001) | Y |  |
| 6 | `created_date` | timestamp without time zone | Y |  |
| 7 | `wf_remark` | text | Y |  |
| 8 | `wf_reason_id` | numeric(38,0) | Y |  |
| 9 | `wf_reason` | character varying(3000) | Y |  |
| 10 | `from_step_id` | numeric(38,0) | Y |  |
| 11 | `to_step_id` | numeric(38,0) | Y |  |

<details><summary>Index</summary>

- `idx_wf_step_history_trn` — `btree (wf_version_id, transaction_pk, from_step_id, to_step_id)`

</details>

### wf_transaction

ประมาณ 53,186 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_transaction_id` 🔑 | bigint | N |  |
| 2 | `transaction_pk` | character varying(300) | N |  |
| 3 | `wf_version_id` | bigint | N |  |
| 4 | `wf_step_id` | bigint | N |  |
| 5 | `wf_status_id` | bigint | N |  |
| 6 | `wf_user_id` | character varying(20) | Y |  |
| 7 | `wf_group_id` | bigint | Y |  |
| 8 | `update_date` | date | Y |  |

- **PK:** `wf_transaction_id`

<details><summary>Index</summary>

- `wf_transaction_inx` — `btree (transaction_pk, wf_version_id, wf_step_id, wf_status_id, wf_user_id, wf_group_id)`
- `wf_transaction_pk` — `btree (wf_transaction_id)`

</details>

### wf_version

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `wf_version_id` 🔑 | bigint | N |  |
| 2 | `wf_id` | bigint | N |  |
| 3 | `version_no` | character varying(5) | N |  |
| 4 | `active_flag` | smallint | N |  |
| 5 | `version_changed_remark` | character varying(500) | Y |  |
| 6 | `init_step_id` | bigint | Y |  |
| 7 | `init_status_id` | bigint | Y |  |
| 8 | `cancel_step_id` | bigint | Y |  |
| 9 | `cancel_status_id` | bigint | Y |  |

- **PK:** `wf_version_id`
- **FK:** `wf_id` → `wf`.`wf_id`

<details><summary>Index</summary>

- `wf_version_pk` — `btree (wf_version_id)`

</details>

### workflow

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `workflow_id` | integer | N | nextval('workflow_workflow_id_seq'::regclass) |
| 2 | `workflow_name` | character varying(255) | Y |  |
| 3 | `description` | text | Y |  |
| 4 | `create_date` | timestamp with time zone | Y |  |

### workflow_approver

ประมาณ 96,542 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `approver_id` 🔑 | integer | N | nextval('workflow_approver_approver_id_seq'::regclass) |
| 2 | `transaction_id` | integer | Y |  |
| 3 | `current_approver` | integer | Y |  |
| 4 | `approver_type` | character varying(10) | Y |  |
| 5 | `state_id` | integer | Y |  |
| 6 | `approve_seq` | integer | Y |  |
| 7 | `create_date` | timestamp with time zone | Y |  |
| 8 | `approve_date` | timestamp with time zone | Y |  |
| 9 | `approve_event` | character varying(100) | Y |  |
| 10 | `remark` | character varying(2000) | Y |  |
| 11 | `version_id` | integer | Y |  |

- **PK:** `approver_id`

<details><summary>Index</summary>

- `workflow_approver_pkey` — `btree (approver_id)`

</details>

### workflow_event

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `event` | character varying(10) | Y |  |
| 2 | `event_name` | character varying(100) | Y |  |

### workflow_group

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` | integer | N | nextval('workflow_group_group_id_seq'::regclass) |
| 2 | `group_name` | character varying(255) | Y |  |
| 3 | `approver_type` | character varying(50) | Y |  |

### workflow_group_map

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_map_id` | integer | N | nextval('workflow_group_map_group_map_id_seq'::regclass) |
| 2 | `group_id` | integer | N |  |
| 3 | `map_table` | character varying(255) | Y |  |
| 4 | `map_column` | character varying(255) | Y |  |
| 5 | `map_key` | character varying(255) | Y |  |

### workflow_history

ประมาณ 38,010 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `history_id` 🔑 | integer | N | nextval('workflow_history_history_id_seq'::regclass) |
| 2 | `version_id` | integer | Y |  |
| 3 | `transaction_id` | integer | Y |  |
| 4 | `old_state_id` | integer | Y |  |
| 5 | `old_status_id` | integer | Y |  |
| 6 | `new_state_id` | integer | Y |  |
| 7 | `new_status_id` | integer | Y |  |
| 8 | `event_data_json` | jsonb | Y |  |
| 9 | `event` | character varying(30) | Y |  |
| 10 | `create_by` | integer | Y |  |
| 11 | `create_date` | timestamp with time zone | Y |  |
| 12 | `create_by_name` | character varying(255) | Y |  |

- **PK:** `history_id`

<details><summary>Index</summary>

- `idx_ca_wh_latest` — `btree (transaction_id, version_id, create_date DESC, history_id DESC)`
- `workflow_history_pkey` — `btree (history_id)`

</details>

### workflow_part

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `part_id` 🔑 | integer | N | nextval('workflow_part_part_id_seq'::regclass) |
| 2 | `version_id` | integer | Y |  |
| 3 | `part_name` | character varying(100) | Y |  |
| 4 | `part_seq` | integer | Y |  |

- **PK:** `part_id`

<details><summary>Index</summary>

- `workflow_part_pkey` — `btree (part_id)`

</details>

### workflow_part_display

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `state_id` | integer | Y |  |
| 2 | `part_id` | integer | Y |  |
| 3 | `part_display_type` | character varying(10) | Y |  |
| 4 | `owner_type` | character varying(10) | Y |  |
| 5 | `group_id` | integer | Y |  |

### workflow_route

ประมาณ 43 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `route_id` 🔑 | integer | N | nextval('workflow_route_route_id_seq'::regclass) |
| 2 | `version_id` | integer | N |  |
| 3 | `from_state_id` | integer | N |  |
| 4 | `event` | character varying(255) | Y |  |
| 5 | `to_state_id` | integer | N |  |
| 6 | `seq` | integer | N |  |
| 7 | `to_status_id` | integer | N |  |
| 8 | `condition_json` | jsonb | Y |  |
| 9 | `approver_type` | character varying(50) | Y |  |
| 10 | `group_id` | integer | Y |  |
| 11 | `email_id` | integer | Y |  |

- **PK:** `route_id`

<details><summary>Index</summary>

- `workflow_route_pk` — `btree (route_id)`

</details>

### workflow_state

ประมาณ 18 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `state_id` | integer | N | nextval('workflow_state_state_id_seq'::regclass) |
| 2 | `state_name` | character varying(255) | Y |  |
| 3 | `create_date` | timestamp with time zone | Y |  |
| 4 | `version_id` | bigint | Y |  |

### workflow_status

ประมาณ 22 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `status_id` | integer | N | nextval('workflow_status_status_id_seq'::regclass) |
| 2 | `status_name` | character varying(255) | Y |  |
| 3 | `create_date` | timestamp with time zone | Y |  |
| 4 | `version_id` | bigint | Y |  |

### workflow_transaction

ประมาณ 19,283 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `transaction_id` | integer | N | nextval('workflow_transaction_transaction_id_seq'::regclass) |
| 2 | `version_id` | integer | N |  |
| 3 | `reference_id` | character varying(255) | Y |  |
| 4 | `current_state_id` | integer | N |  |
| 5 | `current_approver` | integer | N |  |
| 6 | `approver_type` | character varying(50) | Y |  |
| 7 | `current_status_id` | integer | N |  |
| 8 | `data_json` | jsonb | Y |  |
| 9 | `update_date` | timestamp with time zone | Y |  |

### workflow_version

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `version_id` | integer | N | nextval('workflow_version_version_id_seq'::regclass) |
| 2 | `workflow_id` | integer | Y |  |
| 3 | `initial_state_id` | integer | Y |  |
| 4 | `initial_status_id` | integer | Y |  |
| 5 | `end_state_id` | integer | Y |  |
| 6 | `end_status_id` | integer | Y |  |
| 7 | `description` | character varying(1000) | Y |  |
| 8 | `update_date` | timestamp with time zone | Y |  |
| 9 | `url_main` | character varying(500) | Y |  |
| 10 | `url_param_mapping` | text | Y |  |

---

## View

### v_fr_store_active

```sql
SELECT fr.order_id,
    fr.parent_order_id,
    lpad((fr.store_id)::text, 5, '0'::text) AS store_id,
    fr.store_name,
    fr.region,
    fr.start_date,
    fr.transfer_date,
    fr.open_date,
    fr.sign_date,
    fr.contract_start_date,
    fr.contract_end_date,
    fr.juristic_id,
    fr.juristic_group_id,
    fr.tower,
    fr.floor,
    fr.address_no,
    fr.moo,
    fr.soi,
    fr.street,
    fr.district,
    fr.city,
    fr.province,
    fr.zip,
    fr.mobile,
    fr.tel,
    fr.fax,
    fr.owner_id1,
    fr.owner_id2,
    fr.owner_id3,
    fr.cur_owner_id,
    fr.cur_owner_title_code,
    fr.cur_owner_first_name,
    fr.cur_owner_last_name,
    fr.cur_owner_tel,
    fr.cur_owner_relation,
    fr.fr_type,
    fr.fr_subtype,
    fr.store_type,
    fr.op_type,
    fr.operate_type,
    fr.detail_type,
    fr.owner_type,
    fr.store_source,
    fr.to_store_id,
    fr.assess1,
    fr.assess2,
    fr.assess3,
    fr.assess3_grade,
    fr.status,
    fr.create_date,
    fr.create_user,
    fr.update_date,
    fr.update_user,
    fr.authorization_person1,
    fr.authorization_person2,
    fr.authorization_person3,
    fr.ref_process_id,
    fr.amphur_id,
    fr.province_id,
    fr.extend_round,
    fr.cancel_date,
    cc_fr_type.code_name AS fr_type_name,
    cc_fr_subtype.code_name AS fr_subtype_name
   FROM ((fr_store fr
     LEFT JOIN ( SELECT common_code.code_type,
            common_code.code_name,
            common_code.code_value
           FROM common_code) cc_fr_type ON ((((cc_fr_type.code_type)::text = '00019'::text) AND ((fr.fr_type)::text = (cc_fr_type.code_value)::text))))
     LEFT JOIN ( SELECT common_code.code_type,
            common_code.code_name,
            common_code.code_value
           FROM common_code
          WHERE ((common_code.code_type)::text IN ( SELECT common_code_1.code_value
                   FROM common_code common_code_1
                  WHERE ((common_code_1.code_type)::text = '00019'::text)))) cc_fr_subtype ON ((((cc_fr_subtype.code_type)::text = (fr.fr_type)::text) AND ((cc_fr_subtype.code_value)::text = (fr.fr_subtype)::text))))
  WHERE (((fr.store_id)::numeric <> (0)::numeric) AND (fr.start_date IS NOT NULL) AND ((COALESCE(fr.status, '-'::character varying))::text <> 'D'::text) AND ((fr.cancel_date IS NULL) OR (to_char((fr.cancel_date)::timestamp with time zone, 'YYYYMM'::text) = to_char((CURRENT_DATE - '1 mon'::interval), 'YYYYMM'::text))));
```

### v_fes_evaluate_summary

```sql
SELECT franchisee_id,
    owner_id2,
    owner_id3,
    owner_id4,
    evaluate_id,
    eva_order_id,
    store_id,
    store_name,
    start_date,
    fr_type_name,
    eval_type,
    eval_year,
    eval_month,
    eval_no,
    total_point,
    full_point,
    percent_point,
    grade,
    period,
    confirm_grade_status,
    confirm_grade_date
   FROM ( WITH RECURSIVE store_tree AS (
                 SELECT s.order_id,
                    s.store_id,
                    s.start_date,
                    s.parent_order_id,
                    s.partner_id1,
                    s.partner_id2,
                    s.partner_id3,
                    s.partner_id4,
                    (s.order_id)::text AS root_path
                   FROM store_sbp_20260708 s
                  WHERE ((s.parent_order_id IS NULL) AND ((s.store_id)::text <> '00000'::text) AND ((s.status IS NULL) OR ((s.status)::text <> 'D'::text)) AND (s.cancel_date IS NULL))
                UNION ALL
                 SELECT c.order_id,
                    c.store_id,
                    c.start_date,
                    c.parent_order_id,
                    c.partner_id1,
                    c.partner_id2,
                    c.partner_id3,
                    c.partner_id4,
                    ((st.root_path || ','::text) || (c.order_id)::text) AS root_path
                   FROM (store_sbp_20260708 c
                     JOIN store_tree st ON (((st.order_id)::text = (c.parent_order_id)::text)))
                  WHERE (((c.store_id)::text <> '00000'::text) AND ((c.status IS NULL) OR ((c.status)::text <> 'D'::text)) AND (c.cancel_date IS NULL))
                ), store_ref AS (
                 SELECT st.order_id,
                    st.store_id,
                    st.start_date,
                    st.parent_order_id,
                    st.partner_id1,
                    st.partner_id2,
                    st.partner_id3,
                    st.partner_id4,
                    (ref.ref_order_id)::bigint AS ref_order_id
                   FROM (store_tree st
                     CROSS JOIN LATERAL unnest(string_to_array(st.root_path, ','::text)) ref(ref_order_id))
                ), latest_midyear AS (
                 SELECT x.evaluate_id,
                    x.eval_month,
                    x.eval_year,
                    x.total_point,
                    x.grade,
                    x.eval_type,
                    x.eva_order_id,
                    x.order_id,
                    x.confirm_grade_status,
                    x.confirm_grade_date,
                    x.row_rank
                   FROM ( SELECT eva.evaluate_id,
                            eva.eval_month,
                            eva.eval_year,
                            eva.total_point,
                            eva.grade,
                            eva.eval_type,
                            eva.order_id AS eva_order_id,
                            sr.order_id,
                            eva.confirm
```
