# ฐานข้อมูลจริง — schema `sps_auth` (SBP Mall Dev)

> ดึงจากฐานข้อมูลจริงเมื่อ **07/08/2026** ด้วยบัญชี read-only ของ schema `sps_auth`
> Host `srm-sps-spsap-postgres-instance-dev-new-instance-{writer|reader}.cxsegsg200gm.ap-southeast-1.rds.amazonaws.com` · port `5432` · database `postgres` · **PostgreSQL 17.7**
> **เอกสารนี้ไม่มี credential** — username/password อยู่กับผู้ดูแลระบบเท่านั้น

schema ของ **auth-backend** — เก็บ user, group, permission, menu
ระบบประกันรายได้ (SBPGI) **ไม่สร้าง RBAC ของตัวเอง** แต่รับสิทธิ์จาก schema นี้ผ่าน BFF ตามมติ 2026-08-05

**สรุป:** 78 ตาราง · 1335 คอลัมน์ · 122 foreign key · 130 index · 1 view

## ตารางที่ระบบประกันรายได้ (SBPGI) ตัดสินใจใช้ร่วม

| ตาราง | บทบาทใน SBPGI | คอลัมน์ | แถว (ประมาณ) |
|---|---|---|---|
| [`business_user`](#business-user) | ผู้ใช้/ผู้อนุมัติ | 36 | 22,057 |
| [`common_code`](#common-code) | lookup ทั่วไป (+ วงเงินอนุมัติ SBPGI_APPROVE_LIMIT) | 13 | 2,594 |
| [`email_sent`](#email-sent) | log การส่งอีเมล | 12 | 51 |
| [`email_template`](#email-template) | template อีเมล (แทน email_templates) | 13 | -1 |
| [`mas_store`](#mas-store) | master ร้าน | 31 | 18,790 |
| [`mas_zone`](#mas-zone) | ภาค/โซน | 5 | 28 |

## ดัชนีตารางทั้งหมด

| ตาราง | คอลัมน์ | PK | FK | แถว (ประมาณ) | หมายเหตุ |
|---|---|---|---|---|---|
| `app_menus` | 13 | id | 3 | 79 |  |
| `bellinee_area_assignments` | 4 | id | 1 | 27 |  |
| `bellinee_authorizations` | 40 | id | 14 | 19 |  |
| `bellinee_authorizations_process` | 7 | id | 4 | 37 |  |
| `bellinee_secure_links` | 11 | id | 3 | 13 |  |
| `bellinee_store_assignments` | 5 | id | 1 | 28 |  |
| `bellinee_store_organize` | 49 | — | 0 | 246 |  |
| `business_user` | 36 | — | 0 | 22,057 | **ใช้ใน SBPGI** |
| `common_code` | 13 | — | 0 | 2,594 | **ใช้ใน SBPGI** |
| `consent` | 11 | id | 0 | 12 | ตารางเก็บข้อมูลเงื่อนไข/ความยินยอม/แจ้งการประมวลผลข้อมูลส่วนบุคคล |
| `consent_history` | 9 | id | 3 | 52 | ตารางเก็บข้อมูลประวัติการทำรายการ consent |
| `consent_option` | 8 | id | 1 | 25 | ตารางเก็บข้อมูลตัวเลือก consent (consent_option) |
| `consent_records` | 10 | id | 3 | 34 | ตารางเก็บข้อมูลการ consent สำหรับผู้ถือบัตรประชาชน (card_id) |
| `consent_subject` | 9 | id | 1 | 14 | ตารางเก็บข้อมูลหัวข้อเรื่อง consent (consent_subject) |
| `consent_translations` | 5 | id | 0 | 51 | ตารางข้อความ consent แบบหลายภาษา |
| `consent_user` | 6 | id | 0 | 26 |  |
| `districts` | 9 | id | 3 | 928 |  |
| `email_sent` | 12 | email_sent_id | 0 | 51 | **ใช้ใน SBPGI** |
| `email_template` | 13 | email_template_id | 0 | -1 | **ใช้ใน SBPGI** |
| `employee_store` | 70 | id | 0 | -1 |  |
| `fml_franchisee_register` | 44 | id | 0 | 4,269 |  |
| `fml_responsible_sbp` | 11 | responsible_sbp_id | 0 | 99 |  |
| `fml_sub_organize` | 41 | — | 0 | 890 |  |
| `fr_store` | 85 | — | 0 | 10,914 |  |
| `franchisee` | 86 | — | 0 | 15,504 |  |
| `fs_sevenshop` | 56 | branch_id | 0 | 18,432 |  |
| `group_permissions` | 11 | id | 4 | 2,300 |  |
| `import_errors` | 6 | id | 1 | 572 |  |
| `import_jobs` | 13 | id | 3 | 317 |  |
| `local_credentials` | 8 | — | 1 | -1 |  |
| `lookup_values` | 12 | id | 3 | 134 |  |
| `manager_store_transection` | 8 | mst_id | 0 | 137 |  |
| `mas_area` | 2 | area_id | 0 | 13 |  |
| `mas_sbp_ad` | 48 | — | 0 | 102,131 |  |
| `mas_store` | 31 | — | 0 | 18,790 | **ใช้ใน SBPGI** |
| `mas_store_organize` | 19 | — | 0 | 126,708 |  |
| `mas_tmp_sbp_ad` | 44 | — | 0 | 1 |  |
| `mas_zone` | 5 | — | 0 | 28 | **ใช้ใน SBPGI** |
| `postal_codes` | 8 | id | 3 | 7,437 |  |
| `provinces` | 8 | id | 2 | 77 |  |
| `regional_coordinators` | 10 | id | 3 | -1 |  |
| `responsible_owners` | 12 | id | 3 | -1 |  |
| `secure_links` | 11 | id | 3 | 13 |  |
| `store_organize` | 18 | store_id,employee_id | 0 | 116,790 | ข้อมูลโครงสร้างร้านและข้อมูลพนักงานที่เกี่ยวข้องกับร้าน |
| `store_partner_contacts` | 11 | id | 3 | 3 |  |
| `sub_area_area_assignments` | 4 | id | 1 | 30 |  |
| `sub_area_authorizations` | 42 | id | 15 | 22 |  |
| `sub_area_authorizations_process` | 7 | id | 4 | 53 |  |
| `sub_area_secure_links` | 11 | id | 3 | 12 |  |
| `sub_area_store_assignments` | 5 | id | 1 | 33 |  |
| `sub_districts` | 8 | id | 3 | 7,437 |  |
| `test_bellinee_authorizations` | 17 | id | 5 | 2 |  |
| `tmp_import` | 28 | — | 0 | 435 |  |
| `tmp_import_1` | 28 | — | 0 | 24,410 |  |
| `user_addresses` | 11 | user_id | 5 | 22 |  |
| `user_area_assignments` | 4 | id | 1 | 42 |  |
| `user_audit_events` | 6 | id | 1 | -1 |  |
| `user_employment_details` | 11 | user_id | 3 | 81 |  |
| `user_group_members` | 2 | user_id | 2 | 184 |  |
| `user_groups` | 12 | id | 2 | 122 |  |
| `user_groups_old` | 12 | id | 2 | 28 |  |
| `user_log` | 16 | — | 1 | -1 |  |
| `user_store_assignments` | 5 | id | 1 | 46 |  |
| `user_sub_group` | 4 | — | 0 | 6,656 | ตารางเก็บข้อมูลกลุ่มย่อยของผู้ใช้งาน |
| `users` | 22 | id | 6 | 210 |  |
| `workflow` | 2 | workflow_id | 0 | 2 |  |
| `workflow_approver` | 10 | approver_id | 0 | -1 |  |
| `workflow_event` | 2 | event | 0 | 6 |  |
| `workflow_group` | 3 | group_id | 0 | 3 |  |
| `workflow_group_map` | 5 | group_map_id | 0 | 9 |  |
| `workflow_history` | 12 | history_id | 0 | -1 |  |
| `workflow_part` | 4 | part_id | 0 | 5 |  |
| `workflow_part_display` | 5 | — | 0 | -1 |  |
| `workflow_route` | 11 | route_id | 0 | 41 |  |
| `workflow_state` | 3 | state_id | 0 | 10 |  |
| `workflow_status` | 3 | status_id | 0 | 10 |  |
| `workflow_transaction` | 9 | transaction_id | 0 | 55 |  |
| `workflow_version` | 10 | version_id | 0 | 2 |  |

---

## โครงสร้างรายตาราง

### app_menus

ประมาณ 79 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `language_code` | character varying(10) | N | 'th-TH'::character varying |
| 2 | `name` | character varying(50) | N |  |
| 3 | `description` | text | Y |  |
| 4 | `target_url` | text | Y |  |
| 5 | `picture_url` | text | Y |  |
| 6 | `sort_order` | integer | N | 0 |
| 7 | `is_active` | boolean | N | true |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `updated_at` | timestamp with time zone | N | now() |
| 10 | `created_by` | bigint | Y |  |
| 11 | `updated_by` | bigint | Y |  |
| 12 | `id` 🔑 | bigint | N |  |
| 13 | `parent_id` | bigint | Y |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `parent_id` → `app_menus`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `app_menus_pkey` — `btree (id)`

</details>

### bellinee_area_assignments

ประมาณ 27 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `bellinee_auth_id` | bigint | N |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `area_name` | character varying(100) | N |  |

- **PK:** `id`
- **FK:** `bellinee_auth_id` → `bellinee_authorizations`.`id`

<details><summary>Index</summary>

- `bellinee_area_assignments_pkey` — `btree (id)`

</details>

### bellinee_authorizations

ประมาณ 19 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `approved_at` | timestamp with time zone | Y |  |
| 4 | `confirmed_at` | timestamp with time zone | Y |  |
| 5 | `remarks` | text | Y |  |
| 6 | `consent_personal_data` | boolean | N | false |
| 7 | `deleted_at` | timestamp with time zone | Y |  |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `updated_at` | timestamp with time zone | N | now() |
| 10 | `approved_by` | bigint | Y |  |
| 11 | `created_by` | bigint | Y |  |
| 12 | `updated_by` | bigint | Y |  |
| 13 | `title_id` | bigint | N |  |
| 14 | `first_name` | text | N |  |
| 15 | `last_name` | text | N |  |
| 16 | `first_name_en` | text | N |  |
| 17 | `last_name_en` | text | N |  |
| 18 | `national_id_enc` | bytea | N |  |
| 19 | `national_id_digest` | bytea | N |  |
| 20 | `date_of_birth` | date | N |  |
| 21 | `phone_number` | character varying(10) | N |  |
| 22 | `email` | text | N |  |
| 23 | `employee_id` | character varying(20) | Y |  |
| 24 | `employee_type_id` | bigint | N |  |
| 25 | `position_id` | bigint | N |  |
| 26 | `start_date` | date | N |  |
| 27 | `user_status_id` | bigint | N |  |
| 28 | `group_id` | bigint | Y |  |
| 29 | `address_no` | character varying(20) | Y |  |
| 30 | `moo` | character varying(10) | Y |  |
| 31 | `building` | character varying(100) | Y |  |
| 32 | `floor` | character varying(10) | Y |  |
| 33 | `soi` | character varying(100) | Y |  |
| 34 | `road` | character varying(100) | N |  |
| 35 | `province_id` | bigint | N |  |
| 36 | `district_id` | bigint | N |  |
| 37 | `sub_district_id` | bigint | N |  |
| 38 | `postal_code_id` | bigint | Y |  |
| 39 | `status_id` | bigint | N |  |
| 40 | `delivery_id` | character varying(20) | Y |  |

- **PK:** `id`
- **FK:** `approved_by` → `users`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `district_id` → `districts`.`id`
- **FK:** `employee_type_id` → `lookup_values`.`id`
- **FK:** `group_id` → `user_groups`.`id`
- **FK:** `position_id` → `lookup_values`.`id`
- **FK:** `postal_code_id` → `postal_codes`.`id`
- **FK:** `province_id` → `provinces`.`id`
- **FK:** `status_id` → `lookup_values`.`id`
- **FK:** `sub_district_id` → `sub_districts`.`id`
- **FK:** `title_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`
- **FK:** `user_id` → `users`.`id`
- **FK:** `user_status_id` → `lookup_values`.`id`

<details><summary>Index</summary>

- `bellinee_authorizations_pkey` — `btree (id)`
- `idx_bellinee_auth_created_at` — `btree (created_at)`

</details>

### bellinee_authorizations_process

ประมาณ 37 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `bellinee_auth_id` | bigint | N |  |
| 3 | `process_type_id` | bigint | N |  |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `created_by` | bigint | Y |  |
| 6 | `updated_at` | timestamp with time zone | N | now() |
| 7 | `updated_by` | bigint | Y |  |

- **PK:** `id`
- **FK:** `bellinee_auth_id` → `bellinee_authorizations`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `process_type_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `bellinee_authorizations_process_pkey` — `btree (id)`

</details>

### bellinee_secure_links

ประมาณ 13 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('bellinee_secure_links_id_seq'::regclass) |
| 2 | `bellinee_auth_id` | bigint | N |  |
| 3 | `token_hash` | bytea | N |  |
| 4 | `expires_at` | timestamp with time zone | Y |  |
| 5 | `used_at` | timestamp with time zone | Y |  |
| 6 | `created_ip` | inet | Y |  |
| 7 | `user_agent` | text | Y |  |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `created_by` | bigint | Y |  |
| 10 | `updated_at` | timestamp with time zone | N | now() |
| 11 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `bellinee_auth_id` → `bellinee_authorizations`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `bellinee_secure_links_pkey` — `btree (id)`

</details>

### bellinee_store_assignments

ประมาณ 28 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `bellinee_auth_id` | bigint | N |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `store_id` | character varying(10) | N |  |
| 5 | `store_name` | character varying(100) | Y |  |

- **PK:** `id`
- **FK:** `bellinee_auth_id` → `bellinee_authorizations`.`id`

<details><summary>Index</summary>

- `bellinee_store_assignments_pkey` — `btree (id)`

</details>

### bellinee_store_organize

ประมาณ 246 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` | character varying(10) | Y |  |
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
| 47 | `ks_sub_type` | character varying(10) | Y |  |
| 48 | `rnv_start` | timestamp without time zone | Y |  |
| 49 | `rnv_end` | timestamp without time zone | Y |  |

### business_user

**ใช้ใน SBPGI:** ผู้ใช้/ผู้อนุมัติ · ประมาณ 22,057 แถว

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

- `idx_business_user` — `btree (user_id, franchisee_id, active_flag)`
- `idx_business_user_group_active` — `btree (group_id, active_flag)`

</details>

### common_code

**ใช้ใน SBPGI:** lookup ทั่วไป (+ วงเงินอนุมัติ SBPGI_APPROVE_LIMIT) · ประมาณ 2,594 แถว

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

<details><summary>Index</summary>

- `idx_common_code_type_value_active` — `btree (code_type, code_value, active_flag)`

</details>

### consent

ตารางเก็บข้อมูลเงื่อนไข/ความยินยอม/แจ้งการประมวลผลข้อมูลส่วนบุคคล · ประมาณ 12 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `consent_name` | character varying(200) | N |  |
| 3 | `consent_version` | character varying(50) | N | '1'::character varying |
| 4 | `consent_type` | character varying(50) | N |  |
| 5 | `system_id` | character varying(50) | Y |  |
| 6 | `active_flag` | character varying(50) | N | 'Y'::character varying |
| 7 | `create_by` | bigint | Y |  |
| 8 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 9 | `update_by` | bigint | Y |  |
| 10 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 11 | `user_table` | character varying(100) | Y |  |

- **PK:** `id`
- **UNIQUE:** `consent_name,consent_version,system_id`

<details><summary>Index</summary>

- `consent_master_pkey` — `btree (id)`
- `consent_master_unique_def` — `btree (consent_name, consent_version, system_id)`
- `idx_consent_master_system` — `btree (system_id)`
- `idx_consent_master_type_active` — `btree (consent_type, active_flag)`

</details>

### consent_history

ตารางเก็บข้อมูลประวัติการทำรายการ consent · ประมาณ 52 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `consents_id` | bigint | N |  |
| 3 | `consent_subject_id` | bigint | N |  |
| 4 | `consent_option_id` | bigint | N |  |
| 5 | `consent_transaction_pk` | bigint | N |  |
| 6 | `create_by` | integer | Y |  |
| 7 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 8 | `national_id_enc` | bytea | Y |  |
| 9 | `national_id_digest` | bytea | Y |  |

- **PK:** `id`
- **FK:** `consents_id` → `consent`.`id`
- **FK:** `consent_option_id` → `consent_option`.`id`
- **FK:** `consent_subject_id` → `consent_subject`.`id`

<details><summary>Index</summary>

- `consent_history_pkey` — `btree (id)`
- `idx_consent_history_consent` — `btree (consents_id)`
- `idx_consent_history_option` — `btree (consent_option_id)`
- `idx_consent_history_subject` — `btree (consent_subject_id)`
- `idx_consent_history_transaction` — `btree (consent_transaction_pk)`

</details>

### consent_option

ตารางเก็บข้อมูลตัวเลือก consent (consent_option) · ประมาณ 25 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `consent_subject_id` | bigint | N |  |
| 3 | `ccm_status_id` | integer | Y |  |
| 4 | `active_flag` | character varying(50) | N | 'Y'::character varying |
| 5 | `create_by` | bigint | Y |  |
| 6 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 7 | `update_by` | bigint | Y |  |
| 8 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`
- **FK:** `consent_subject_id` → `consent_subject`.`id`

<details><summary>Index</summary>

- `consent_option_pkey` — `btree (id)`
- `idx_consent_option_active` — `btree (active_flag)`
- `idx_consent_option_status` — `btree (ccm_status_id)`
- `idx_consent_option_subject` — `btree (consent_subject_id)`

</details>

### consent_records

ตารางเก็บข้อมูลการ consent สำหรับผู้ถือบัตรประชาชน (card_id) · ประมาณ 34 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `consents_id` | bigint | N |  |
| 3 | `consent_subject_id` | bigint | N |  |
| 4 | `consent_option_id` | bigint | N |  |
| 5 | `create_by` | bigint | Y |  |
| 6 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 7 | `update_by` | bigint | Y |  |
| 8 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 9 | `national_id_enc` | bytea | Y |  |
| 10 | `national_id_digest` | bytea | Y |  |

- **PK:** `id`
- **FK:** `consents_id` → `consent`.`id`
- **FK:** `consent_option_id` → `consent_option`.`id`
- **FK:** `consent_subject_id` → `consent_subject`.`id`

<details><summary>Index</summary>

- `consent_records_pkey` — `btree (id)`
- `idx_consent_records_consent` — `btree (consents_id)`
- `idx_consent_records_option` — `btree (consent_option_id)`
- `idx_consent_records_subject` — `btree (consent_subject_id)`

</details>

### consent_subject

ตารางเก็บข้อมูลหัวข้อเรื่อง consent (consent_subject) · ประมาณ 14 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `consents_id` | bigint | N |  |
| 3 | `action_id` | character varying(50) | Y |  |
| 4 | `consent_subject_version` | character varying(50) | N |  |
| 5 | `active_flag` | character varying(50) | N | 'Y'::character varying |
| 6 | `create_by` | bigint | Y |  |
| 7 | `create_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |
| 8 | `update_by` | bigint | Y |  |
| 9 | `update_date` | timestamp with time zone | Y | CURRENT_TIMESTAMP |

- **PK:** `id`
- **FK:** `consents_id` → `consent`.`id`

<details><summary>Index</summary>

- `consent_subject_pkey` — `btree (id)`
- `idx_consent_subject_action` — `btree (action_id)`
- `idx_consent_subject_active` — `btree (active_flag)`
- `idx_consent_subject_fk` — `btree (consents_id)`

</details>

### consent_translations

ตารางข้อความ consent แบบหลายภาษา · ประมาณ 51 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `ref_type` | character varying(50) | N |  |
| 3 | `ref_id` | bigint | N |  |
| 4 | `value` | text | N |  |
| 5 | `language` | character varying(50) | N | 'TH'::character varying |

- **PK:** `id`
- **UNIQUE:** `ref_type,ref_id,language`

<details><summary>Index</summary>

- `consent_translations_pkey` — `btree (id)`
- `consent_translations_unique_ref_lang` — `btree (ref_type, ref_id, language)`
- `idx_consent_translations_ref` — `btree (ref_type, ref_id)`

</details>

### consent_user

ประมาณ 26 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `card_id` | character varying(20) | Y |  |
| 4 | `system_id` | character varying(50) | N |  |
| 5 | `card_id_enc` | bytea | Y |  |
| 6 | `card_id_digest` | bytea | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `consent_user_pkey` — `btree (id)`
- `idx_consent_user_card_digest` — `btree (card_id_digest)`

</details>

### districts

ประมาณ 928 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `code` | character varying(10) | N |  |
| 2 | `name` | character varying(100) | N |  |
| 3 | `postcode` | character varying(10) | Y |  |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `updated_at` | timestamp with time zone | N | now() |
| 6 | `created_by` | bigint | Y |  |
| 7 | `updated_by` | bigint | Y |  |
| 8 | `province_id` | bigint | Y |  |
| 9 | `id` 🔑 | bigint | N |  |

- **PK:** `id`
- **UNIQUE:** `code`
- **FK:** `created_by` → `users`.`id`
- **FK:** `province_id` → `provinces`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `districts_code_key` — `btree (code)`
- `districts_pkey` — `btree (id)`

</details>

### email_sent

**ใช้ใน SBPGI:** log การส่งอีเมล · ประมาณ 51 แถว

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

**ใช้ใน SBPGI:** template อีเมล (แทน email_templates) · ประมาณ -1 แถว

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
| 13 | `email_template_id","email_template_name","email_template_desc",` | character varying(4096) | Y |  |

- **PK:** `email_template_id`

<details><summary>Index</summary>

- `email_template_pkey` — `btree (email_template_id)`

</details>

### employee_store

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `store_id` | character varying(5) | N |  |
| 3 | `delivery_id` | character varying(50) | N |  |
| 4 | `first_name` | character varying(100) | Y |  |
| 5 | `last_name` | character varying(100) | Y |  |
| 6 | `position_id` | character varying(50) | Y |  |
| 7 | `job_code` | character varying(50) | Y |  |
| 8 | `position_name` | character varying(200) | Y |  |
| 9 | `employee_type_id` | character varying(50) | Y |  |
| 10 | `employee_type_name` | character varying(200) | Y |  |
| 11 | `department_id` | character varying(50) | Y |  |
| 12 | `department_name` | character varying(200) | Y |  |
| 13 | `employee_id` | character varying(50) | N |  |
| 14 | `start_date` | timestamp with time zone | Y |  |
| 15 | `end_date` | timestamp with time zone | Y |  |
| 16 | `create_date` | timestamp with time zone | Y |  |
| 17 | `update_date` | timestamp with time zone | Y | now() |
| 18 | `username` | character varying(70) | Y |  |
| 19 | `national_id` | character varying(20) | Y |  |
| 20 | `title_name` | character varying(20) | Y |  |
| 21 | `domain` | character varying(50) | Y |  |
| 22 | `first_name_en` | character varying(100) | Y |  |
| 23 | `last_name_en` | character varying(100) | Y |  |
| 24 | `authoriztion_id` | character varying(100) | Y |  |
| 25 | `role_id` | character varying(50) | Y |  |
| 26 | `end_status` | character varying(1) | Y |  |
| 27 | `checkin_status` | character varying(1) | Y |  |
| 28 | `employee_barcode` | character varying(13) | Y |  |
| 29 | `shift_status` | character varying(1) | Y |  |
| 30 | `store_id_from` | character varying(5) | Y |  |
| 31 | `store_id_to` | character varying(5) | Y |  |
| 32 | `flag_change_status` | character varying(1) | Y |  |
| 33 | `date_change_status` | timestamp with time zone | Y |  |
| 34 | `flag_sbp` | character varying(1) | Y |  |
| 35 | `flag_fc_change` | numeric | Y |  |
| 36 | `job_code_acting` | character varying(20) | Y |  |
| 37 | `sex` | character varying(1) | Y |  |
| 38 | `nationality` | character varying(30) | Y |  |
| 39 | `street` | character varying(50) | Y |  |
| 40 | `village` | character varying(25) | Y |  |
| 41 | `tumbon` | character varying(25) | Y |  |
| 42 | `amphur` | character varying(25) | Y |  |
| 43 | `province` | character varying(25) | Y |  |
| 44 | `post_code` | character varying(5) | Y |  |
| 45 | `tel` | character varying(40) | Y |  |
| 46 | `education` | character varying(25) | Y |  |
| 47 | `salary_type` | character varying(1) | Y |  |
| 48 | `salary` | numeric | Y |  |
| 49 | `birthdate` | timestamp with time zone | Y |  |
| 50 | `benefit` | numeric | Y |  |
| 51 | `salary_perunit` | numeric(13,2) | Y |  |
| 52 | `work_hr_perday` | numeric | Y |  |
| 53 | `work_day_permonth` | numeric | Y |  |
| 54 | `bu_code` | character varying(2) | Y |  |
| 55 | `title_name_en` | character varying(20) | Y |  |
| 56 | `resign_id` | numeric(38,0) | Y |  |
| 57 | `resign_detail` | character varying(2000) | Y |  |
| 58 | `store_type` | character varying(100) | Y |  |
| 59 | `store_group` | character varying(20) | Y |  |
| 60 | `store_name` | character varying(200) | Y |  |
| 61 | `manager_id` | character varying(15) | Y |  |
| 62 | `approver_id` | character varying(15) | Y |  |
| 63 | `company_id` | character varying(3) | Y |  |
| 64 | `email_notify` | character varying(70) | Y |  |
| 65 | `emp_rcd` | character varying(5) | Y |  |
| 66 | `position_nbr_acting` | character varying(8) | Y |  |
| 67 | `supv_lvl_id_acting` | character varying(8) | Y |  |
| 68 | `jobcode_acting` | character varying(100) | Y |  |
| 69 | `deptid_acting` | character varying(10) | Y |  |
| 70 | `remark` | character varying(255) | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `employee_store_pkey` — `btree (id)`

</details>

### fml_franchisee_register

ประมาณ 4,269 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `first_name` | character varying(50) | Y |  |
| 3 | `last_name` | character varying(50) | Y |  |
| 4 | `first_name_eng` | character varying(50) | N |  |
| 5 | `last_name_eng` | character varying(50) | N |  |
| 6 | `username` | character varying(25) | Y |  |
| 7 | `password` | character varying(100) | N |  |
| 8 | `id_card` | character varying(15) | N |  |
| 9 | `current_franchisee_id` | bigint | N |  |
| 10 | `f_tower` | character varying(100) | Y |  |
| 11 | `f_floor` | character varying(20) | Y |  |
| 12 | `f_address_no` | character varying(100) | Y |  |
| 13 | `f_moo` | character varying(20) | Y |  |
| 14 | `f_soi` | character varying(100) | Y |  |
| 15 | `f_street` | character varying(100) | Y |  |
| 16 | `f_district` | character varying(100) | Y |  |
| 17 | `f_city` | character varying(20) | Y |  |
| 18 | `f_province` | character varying(20) | Y |  |
| 19 | `f_zip` | character varying(10) | Y |  |
| 20 | `f_mobile` | character varying(50) | Y |  |
| 21 | `f_tel` | character varying(50) | Y |  |
| 22 | `f_email` | character varying(100) | Y |  |
| 23 | `f_status_code` | character varying(20) | Y |  |
| 24 | `f_number_child` | character varying(20) | Y |  |
| 25 | `current_juristic_id` | bigint | Y |  |
| 26 | `juristic_name` | character varying(50) | Y |  |
| 27 | `j_tower` | character varying(100) | Y |  |
| 28 | `j_floor` | character varying(20) | Y |  |
| 29 | `j_address_no` | character varying(100) | Y |  |
| 30 | `j_moo` | character varying(20) | Y |  |
| 31 | `j_soi` | character varying(100) | Y |  |
| 32 | `j_street` | character varying(100) | Y |  |
| 33 | `j_district` | character varying(100) | Y |  |
| 34 | `j_city` | character varying(20) | Y |  |
| 35 | `j_province` | character varying(20) | Y |  |
| 36 | `j_zip` | character varying(10) | Y |  |
| 37 | `j_tel` | character varying(50) | Y |  |
| 38 | `j_fax` | character varying(50) | Y |  |
| 39 | `juristic_type_id` | character varying(20) | Y |  |
| 40 | `create_date` | timestamp without time zone | N | CURRENT_TIMESTAMP |
| 41 | `verify_flag` | character varying(1) | Y | 'N'::character varying |
| 42 | `approve_change_flag` | character varying(1) | Y | 'N'::character varying |
| 43 | `f_fax` | character varying(20) | Y |  |
| 44 | `update_date` | timestamp without time zone | Y |  |

- **PK:** `id`

<details><summary>Index</summary>

- `fml_franchisee_register_pk` — `btree (id)`

</details>

### fml_responsible_sbp

ประมาณ 99 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `responsible_sbp_id` 🔑 | integer | N |  |
| 2 | `store_ptt` | character varying(2) | N |  |
| 3 | `region` | character varying(100) | N |  |
| 4 | `name` | character varying(200) | Y |  |
| 5 | `position` | character varying(100) | Y |  |
| 6 | `email` | character varying(100) | N |  |
| 7 | `tel` | character varying(100) | Y |  |
| 8 | `create_date` | date | Y | CURRENT_DATE |
| 9 | `create_by` | character varying(20) | Y | 'system'::character varying |
| 10 | `update_date` | date | Y | CURRENT_DATE |
| 11 | `update_by` | character varying(20) | Y | 'system'::character varying |

- **PK:** `responsible_sbp_id`

<details><summary>Index</summary>

- `fml_responsible_sbp_pkey` — `btree (responsible_sbp_id)`

</details>

### fml_sub_organize

ประมาณ 890 แถว

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

### fr_store

ประมาณ 10,914 แถว

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
| 67 | `update_date` | date | Y |  |
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
- `fr_store_index2` — `btree (start_date)`
- `fr_store_index3` — `btree (owner_id1)`
- `fr_store_index4` — `btree (cancel_date)`
- `fr_store_index5` — `btree (fr_type)`
- `fr_store_index6` — `btree (status)`
- `fr_store_index7` — `btree (cancel_type)`
- `fr_store_index8` — `btree (owner_id2)`
- `fr_store_index9` — `btree (owner_id3)`
- `idx_fr_store_owner_status_cancel` — `btree (owner_id1, status, cancel_type, cancel_date)`

</details>

### franchisee

ประมาณ 15,504 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `cust_id` | numeric(38,0) | Y |  |
| 2 | `franchisee_id` | numeric(38,0) | Y |  |
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
| 56 | `create_date` | timestamp without time zone | Y |  |
| 57 | `create_user` | character varying(200) | Y |  |
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
| 81 | `main_nationality` | numeric | Y |  |
| 82 | `married_birthday` | timestamp without time zone | Y |  |
| 83 | `docattach_id` | numeric | Y |  |
| 84 | `religion_accept` | character varying(1) | Y |  |
| 85 | `marketing_accept` | character varying(1) | Y |  |
| 86 | `profile_accept` | character varying(1) | Y |  |

<details><summary>Index</summary>

- `idx_franchisee_status` — `btree (franchisee_id, status)`

</details>

### fs_sevenshop

ประมาณ 18,432 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `branch_id` 🔑 | character varying(7) | N |  |
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

- **PK:** `branch_id`

<details><summary>Index</summary>

- `fs_sevenshop_index2` — `btree (shop_type)`
- `fs_sevenshop_index3` — `btree (dv_email)`
- `pk_fs_sevenshop` — `btree (branch_id)`

</details>

### group_permissions

ประมาณ 2,300 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `can_view` | boolean | N | false |
| 2 | `can_manage` | boolean | N | false |
| 3 | `can_export` | boolean | N | false |
| 4 | `can_other` | boolean | N | false |
| 5 | `created_at` | timestamp with time zone | N | now() |
| 6 | `updated_at` | timestamp with time zone | N | now() |
| 7 | `created_by` | bigint | Y |  |
| 8 | `updated_by` | bigint | Y |  |
| 9 | `menu_id` | bigint | Y |  |
| 10 | `group_id` | bigint | Y |  |
| 11 | `id` 🔑 | bigint | N |  |

- **PK:** `id`
- **UNIQUE:** `group_id,menu_id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `menu_id` → `app_menus`.`id`
- **FK:** `updated_by` → `users`.`id`
- **FK:** `group_id` → `user_groups`.`id`

<details><summary>Index</summary>

- `group_permissions_group_id_menu_id_key` — `btree (group_id, menu_id)`
- `group_permissions_pkey` — `btree (id)`

</details>

### import_errors

ประมาณ 572 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('import_errors_id_seq'::regclass) |
| 2 | `job_id` | bigint | N |  |
| 3 | `row_number` | integer | N |  |
| 4 | `error_code` | text | N |  |
| 5 | `error_message` | text | N |  |
| 6 | `created_at` | timestamp with time zone | N | CURRENT_TIMESTAMP |

- **PK:** `id`
- **FK:** `job_id` → `import_jobs`.`id`

<details><summary>Index</summary>

- `import_errors_job_id_key` — `btree (job_id, row_number)`
- `import_errors_pkey` — `btree (id)`

</details>

### import_jobs

ประมาณ 317 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('import_jobs_id_seq'::regclass) |
| 2 | `type` | character varying(50) | N |  |
| 3 | `file_name` | character varying(255) | N |  |
| 4 | `file_size_bytes` | integer | N | 0 |
| 5 | `status_id` | bigint | N |  |
| 6 | `total_rows` | integer | Y |  |
| 7 | `valid_rows` | integer | Y |  |
| 8 | `error_rows` | integer | Y |  |
| 9 | `comment` | text | Y |  |
| 10 | `created_at` | timestamp with time zone | N | now() |
| 11 | `updated_at` | timestamp with time zone | N | now() |
| 12 | `created_by` | bigint | N |  |
| 13 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `status_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `import_jobs_pkey` — `btree (id)`

</details>

### local_credentials

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `password_hash` | text | N |  |
| 2 | `password_updated_at` | timestamp with time zone | N | now() |
| 3 | `password_must_change` | boolean | N | false |
| 4 | `password_version` | smallint | N | 1 |
| 5 | `last_login_at` | timestamp with time zone | Y |  |
| 6 | `failed_attempts` | integer | N | 0 |
| 7 | `locked_until` | timestamp with time zone | Y |  |
| 8 | `user_id` | bigint | Y |  |

- **FK:** `user_id` → `users`.`id`

### lookup_values

ประมาณ 134 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `language_code` | character varying(10) | N | 'th-TH'::character varying |
| 3 | `name` | character varying(50) | N |  |
| 4 | `description` | text | Y |  |
| 5 | `sort_order` | integer | N | 0 |
| 6 | `is_active` | boolean | N | true |
| 7 | `created_at` | timestamp with time zone | N | now() |
| 8 | `updated_at` | timestamp with time zone | N | now() |
| 9 | `created_by` | bigint | Y |  |
| 10 | `updated_by` | bigint | Y |  |
| 11 | `parent_id` | bigint | Y |  |
| 12 | `code_value` | character varying(100) | Y |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `parent_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `lookup_values_pkey` — `btree (id)`

</details>

### manager_store_transection

ประมาณ 137 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `mst_id` 🔑 | bigint | N | nextval('manager_store_transection_seq'::regclass) |
| 2 | `store_id` | character varying(10) | Y |  |
| 3 | `principal_name` | character varying(70) | Y |  |
| 4 | `active_flag` | character varying(5) | Y |  |
| 5 | `owner_id3` | bigint | Y |  |
| 6 | `create_date` | timestamp without time zone | Y | CURRENT_TIMESTAMP |
| 7 | `send_flag` | character varying(5) | Y | 'N'::character varying |
| 8 | `send_date` | timestamp without time zone | Y |  |

- **PK:** `mst_id`

<details><summary>Index</summary>

- `manager_store_transection_pkey` — `btree (mst_id)`

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

### mas_sbp_ad

ประมาณ 102,131 แถว

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
| 27 | `emp_rcd` | character varying(5) | Y |  |
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
| 38 | `create_date` | timestamp without time zone | Y |  |
| 39 | `update_date` | timestamp without time zone | Y |  |
| 40 | `is_manager` | character(1) | Y |  |
| 41 | `trans_cate` | character varying(5) | Y |  |
| 42 | `return_status` | character varying(15) | Y |  |
| 43 | `return_msg_desc` | character varying(4000) | Y |  |
| 44 | `return_code` | character varying(15) | Y |  |
| 45 | `temp_col_1` | character varying(20) | Y |  |
| 46 | `company_id` | character varying(20) | Y |  |
| 47 | `job_code` | character varying(10) | Y |  |
| 48 | `remark` | character varying(255) | Y |  |

<details><summary>Index</summary>

- `idx_ad_idcard` — `btree (id_card)`
- `idx_ad_trans_date` — `btree (trans_date)`

</details>

### mas_store

**ใช้ใน SBPGI:** master ร้าน · ประมาณ 18,790 แถว

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
| 21 | `open_date` | date | Y |  |
| 22 | `close_date` | date | Y |  |
| 23 | `branch_other` | character varying(100) | Y |  |
| 24 | `fr_sub_type` | character varying(25) | Y |  |
| 25 | `status` | character varying(20) | Y |  |
| 26 | `src_update_date` | timestamp without time zone | Y |  |
| 27 | `src_update_user` | character varying(200) | Y |  |
| 28 | `data_type` | character varying(5) | Y |  |
| 29 | `active_flag` | character(1) | Y |  |
| 30 | `start_renovate_date` | date | Y |  |
| 31 | `end_renovate_date` | date | Y |  |

<details><summary>Index</summary>

- `idx_mas_store_branch_active` — `btree (branch_id, active_flag)`

</details>

### mas_store_organize

ประมาณ 126,708 แถว

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

- `idx_mas_store_organize_branch_group_active` — `btree (branch_id, group_id, active_flag)`

</details>

### mas_tmp_sbp_ad

ประมาณ 1 แถว

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
| 11 | `hire_start_date` | date | Y |  |
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
| 29 | `trans_date` | date | Y |  |
| 30 | `flag_action` | character varying(5) | Y |  |
| 31 | `active_date` | date | Y |  |
| 32 | `inactive_date` | date | Y |  |
| 33 | `flag_send_ad` | character varying(5) | Y | 'N'::character varying |
| 34 | `last_send_ad_date` | date | Y |  |
| 35 | `return_msg` | character varying(4000) | Y |  |
| 36 | `franchisee_id` | numeric | Y |  |
| 37 | `principal_name` | character varying(70) | Y |  |
| 38 | `create_date` | date | Y | CURRENT_DATE |
| 39 | `update_date` | date | Y |  |
| 40 | `is_manager` | character(1) | Y | 'N'::bpchar |
| 41 | `trans_cate` | character varying(5) | Y |  |
| 42 | `return_status` | character varying(15) | Y |  |
| 43 | `return_msg_desc` | character varying(4000) | Y |  |
| 44 | `return_code` | character varying(15) | Y |  |

- **UNIQUE:** `id_card`
- **UNIQUE:** `sbp_ad_id`
- **UNIQUE:** `username`

<details><summary>Index</summary>

- `idx_tmp_idcard_cate` — `btree (id_card, trans_cate)`
- `idx_tmp_trans_date` — `btree (trans_date)`
- `mas_tmp_sbp_ad_u01` — `btree (id_card)`
- `mas_tmp_sbp_ad_u02` — `btree (sbp_ad_id)`
- `mas_tmp_sbp_ad_u03` — `btree (username)`

</details>

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

### postal_codes

ประมาณ 7,437 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `postcode` | character varying(10) | N |  |
| 2 | `note` | character varying(255) | Y |  |
| 3 | `created_at` | timestamp with time zone | N | now() |
| 4 | `updated_at` | timestamp with time zone | N | now() |
| 5 | `created_by` | bigint | Y |  |
| 6 | `updated_by` | bigint | Y |  |
| 7 | `sub_district_id` | bigint | Y |  |
| 8 | `id` 🔑 | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `sub_district_id` → `sub_districts`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `postal_codes_pkey` — `btree (id)`

</details>

### provinces

ประมาณ 77 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `language_code` | character varying(10) | N | 'th-TH'::character varying |
| 2 | `code` | character varying(10) | N |  |
| 3 | `name` | character varying(100) | N |  |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `updated_at` | timestamp with time zone | N | now() |
| 6 | `created_by` | bigint | Y |  |
| 7 | `updated_by` | bigint | Y |  |
| 8 | `id` 🔑 | bigint | N |  |

- **PK:** `id`
- **UNIQUE:** `language_code,code`
- **FK:** `created_by` → `users`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `provinces_language_code_code_key` — `btree (language_code, code)`
- `provinces_pkey` — `btree (id)`

</details>

### regional_coordinators

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('regional_coordinators_id_seq'::regclass) |
| 2 | `region` | character varying(100) | N |  |
| 3 | `employee_code` | character varying(50) | N |  |
| 4 | `first_name_th` | character varying(100) | N |  |
| 5 | `last_name_th` | character varying(100) | N |  |
| 6 | `job_id` | bigint | N |  |
| 7 | `created_at` | timestamp with time zone | N | now() |
| 8 | `updated_at` | timestamp with time zone | N | now() |
| 9 | `created_by` | bigint | N |  |
| 10 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `job_id` → `import_jobs`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `regional_coordinators_pkey` — `btree (id)`
- `regional_coordinators_region_key` — `btree (region)`

</details>

### responsible_owners

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('responsible_owners_id_seq'::regclass) |
| 2 | `store` | character(2) | N |  |
| 3 | `region` | character varying(100) | N |  |
| 4 | `name` | character varying(150) | Y |  |
| 5 | `position` | character varying(150) | Y |  |
| 6 | `email` | character varying(150) | N |  |
| 7 | `telephone` | character varying(50) | Y |  |
| 8 | `job_id` | bigint | N |  |
| 9 | `created_at` | timestamp with time zone | N | now() |
| 10 | `updated_at` | timestamp with time zone | N | now() |
| 11 | `created_by` | bigint | N |  |
| 12 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `job_id` → `import_jobs`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `responsible_owners_pkey` — `btree (id)`
- `responsible_owners_region_key` — `btree (region)`

</details>

### secure_links

ประมาณ 13 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('secure_links_id_seq'::regclass) |
| 2 | `user_id` | bigint | N |  |
| 3 | `token_hash` | bytea | N |  |
| 4 | `expires_at` | timestamp with time zone | N |  |
| 5 | `used_at` | timestamp with time zone | Y |  |
| 6 | `created_ip` | inet | Y |  |
| 7 | `user_agent` | text | Y |  |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `created_by` | bigint | Y |  |
| 10 | `updated_at` | timestamp with time zone | N | now() |
| 11 | `updated_by` | bigint | Y |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `updated_by` → `users`.`id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `idx_secure_links_token_hash` — `btree (token_hash)`
- `secure_links_pkey` — `btree (id)`

</details>

### store_organize

ข้อมูลโครงสร้างร้านและข้อมูลพนักงานที่เกี่ยวข้องกับร้าน · ประมาณ 116,790 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `store_id` | character varying(10) | N |  |
| 2 | `employee_id` | character varying(50) | N |  |
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

- **PK:** `store_id,employee_id`

<details><summary>Index</summary>

- `pk_store_organize` — `btree (store_id, employee_id)`

</details>

### store_partner_contacts

ประมาณ 3 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('store_partner_contacts_id_seq'::regclass) |
| 2 | `region` | character varying(100) | N |  |
| 3 | `store_id` | character varying(50) | Y |  |
| 4 | `department` | character varying(100) | N |  |
| 5 | `name` | character varying(150) | N |  |
| 6 | `telephone` | character varying(50) | N |  |
| 7 | `job_id` | bigint | N |  |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `updated_at` | timestamp with time zone | N | now() |
| 10 | `created_by` | bigint | N |  |
| 11 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `job_id` → `import_jobs`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `store_partner_contacts_pkey` — `btree (id)`
- `store_partner_contacts_region_key` — `btree (region)`

</details>

### sub_area_area_assignments

ประมาณ 30 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `sub_area_auth_id` | bigint | N |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `area_name` | character varying(100) | N |  |

- **PK:** `id`
- **FK:** `sub_area_auth_id` → `sub_area_authorizations`.`id`

<details><summary>Index</summary>

- `idx_sub_area_area_assignments_auth_id` — `btree (sub_area_auth_id)`
- `sub_area_area_assignments_pkey` — `btree (id)`

</details>

### sub_area_authorizations

ประมาณ 22 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `status_id` | bigint | Y |  |
| 4 | `approved_by` | bigint | Y |  |
| 5 | `approved_at` | timestamp with time zone | Y |  |
| 6 | `confirmed_at` | timestamp with time zone | Y |  |
| 7 | `remarks` | text | Y |  |
| 8 | `consent_personal_data` | boolean | N | false |
| 9 | `deleted_at` | timestamp with time zone | Y |  |
| 10 | `created_at` | timestamp with time zone | N | now() |
| 11 | `updated_at` | timestamp with time zone | N | now() |
| 12 | `created_by` | bigint | Y |  |
| 13 | `updated_by` | bigint | Y |  |
| 14 | `title_id` | bigint | Y |  |
| 15 | `first_name` | text | Y |  |
| 16 | `last_name` | text | Y |  |
| 17 | `first_name_en` | text | Y |  |
| 18 | `last_name_en` | text | Y |  |
| 19 | `national_id_enc` | bytea | Y |  |
| 20 | `national_id_digest` | bytea | Y |  |
| 21 | `date_of_birth` | date | Y |  |
| 22 | `phone_number` | character varying(10) | Y |  |
| 23 | `email` | text | Y |  |
| 24 | `employee_id` | character varying(20) | Y |  |
| 25 | `employee_type_id` | bigint | Y |  |
| 26 | `position_id` | bigint | Y |  |
| 27 | `start_date` | date | Y |  |
| 28 | `area_id` | bigint | Y |  |
| 29 | `user_status_id` | bigint | Y |  |
| 30 | `user_type_id` | bigint | Y |  |
| 31 | `group_id` | bigint | Y |  |
| 32 | `address_no` | character varying(20) | Y |  |
| 33 | `moo` | character varying(10) | Y |  |
| 34 | `building` | character varying(100) | Y |  |
| 35 | `floor` | character varying(10) | Y |  |
| 36 | `soi` | character varying(100) | Y |  |
| 37 | `road` | character varying(100) | Y |  |
| 38 | `province_id` | bigint | Y |  |
| 39 | `district_id` | bigint | Y |  |
| 40 | `sub_district_id` | bigint | Y |  |
| 41 | `postal_code_id` | bigint | Y |  |
| 42 | `delivery_id` | character varying(20) | Y |  |

- **PK:** `id`
- **FK:** `approved_by` → `users`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `district_id` → `districts`.`id`
- **FK:** `employee_type_id` → `lookup_values`.`id`
- **FK:** `group_id` → `user_groups`.`id`
- **FK:** `position_id` → `lookup_values`.`id`
- **FK:** `postal_code_id` → `postal_codes`.`id`
- **FK:** `province_id` → `provinces`.`id`
- **FK:** `status_id` → `lookup_values`.`id`
- **FK:** `sub_district_id` → `sub_districts`.`id`
- **FK:** `title_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`
- **FK:** `user_id` → `users`.`id`
- **FK:** `user_status_id` → `lookup_values`.`id`
- **FK:** `user_type_id` → `lookup_values`.`id`

<details><summary>Index</summary>

- `idx_sub_area_auth_created_at` — `btree (created_at)`
- `idx_sub_area_auth_status` — `btree (status_id)`
- `sub_area_authorizations_pkey` — `btree (id)`

</details>

### sub_area_authorizations_process

ประมาณ 53 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `sub_area_auth_id` | bigint | N |  |
| 3 | `process_type_id` | bigint | N |  |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `created_by` | bigint | N |  |
| 6 | `updated_at` | timestamp with time zone | N | now() |
| 7 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `process_type_id` → `lookup_values`.`id`
- **FK:** `sub_area_auth_id` → `sub_area_authorizations`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `idx_sub_area_authorizations_process_auth_id` — `btree (sub_area_auth_id)`
- `sub_area_authorizations_process_pkey` — `btree (id)`

</details>

### sub_area_secure_links

ประมาณ 12 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N | nextval('sub_area_secure_links_id_seq'::regclass) |
| 2 | `sub_area_auth_id` | bigint | N |  |
| 3 | `token_hash` | bytea | N |  |
| 4 | `expires_at` | timestamp with time zone | Y |  |
| 5 | `used_at` | timestamp with time zone | Y |  |
| 6 | `created_ip` | inet | Y |  |
| 7 | `user_agent` | text | Y |  |
| 8 | `created_at` | timestamp with time zone | N | now() |
| 9 | `created_by` | bigint | Y |  |
| 10 | `updated_at` | timestamp with time zone | N | now() |
| 11 | `updated_by` | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `sub_area_auth_id` → `sub_area_authorizations`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `sub_area_secure_links_pkey` — `btree (id)`

</details>

### sub_area_store_assignments

ประมาณ 33 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `sub_area_auth_id` | bigint | N |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `store_id` | character varying(10) | N |  |
| 5 | `store_name` | character varying(100) | Y |  |

- **PK:** `id`
- **FK:** `sub_area_auth_id` → `sub_area_authorizations`.`id`

<details><summary>Index</summary>

- `idx_sub_area_store_assignments_auth_id` — `btree (sub_area_auth_id)`
- `sub_area_store_assignments_pkey` — `btree (id)`

</details>

### sub_districts

ประมาณ 7,437 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `code` | character varying(10) | N |  |
| 2 | `name` | character varying(100) | N |  |
| 3 | `created_at` | timestamp with time zone | N | now() |
| 4 | `updated_at` | timestamp with time zone | N | now() |
| 5 | `created_by` | bigint | Y |  |
| 6 | `updated_by` | bigint | Y |  |
| 7 | `district_id` | bigint | Y |  |
| 8 | `id` 🔑 | bigint | N |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `district_id` → `districts`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `sub_districts_pkey` — `btree (id)`

</details>

### test_bellinee_authorizations

ประมาณ 2 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `status_id` | bigint | Y |  |
| 4 | `approved_by` | bigint | Y |  |
| 5 | `approved_at` | timestamp with time zone | Y |  |
| 6 | `confirmed_at` | timestamp with time zone | Y |  |
| 7 | `remarks` | text | Y |  |
| 8 | `consent_personal_data` | boolean | N | false |
| 9 | `deleted_at` | timestamp with time zone | Y |  |
| 10 | `created_at` | timestamp with time zone | N | now() |
| 11 | `updated_at` | timestamp with time zone | N | now() |
| 12 | `created_by` | bigint | Y |  |
| 13 | `updated_by` | bigint | Y |  |
| 14 | `first_name` | text | Y |  |
| 15 | `last_name` | text | Y |  |
| 16 | `national_id_enc` | bytea | Y |  |
| 17 | `phone_number` | character varying(10) | Y |  |

- **PK:** `id`
- **FK:** `approved_by` → `users`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `status_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `test_bellinee_authorizations_pkey` — `btree (id)`

</details>

### tmp_import

ประมาณ 435 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `temp1` | character varying(1000) | Y |  |
| 2 | `temp2` | character varying(1000) | Y |  |
| 3 | `temp3` | character varying(1000) | Y |  |
| 4 | `temp4` | character varying(1000) | Y |  |
| 5 | `temp5` | character varying(1000) | Y |  |
| 6 | `temp6` | character varying(3000) | Y |  |
| 7 | `temp7` | character varying(1000) | Y |  |
| 8 | `temp8` | character varying(1000) | Y |  |
| 9 | `temp9` | character varying(1000) | Y |  |
| 10 | `temp10` | character varying(1000) | Y |  |
| 11 | `temp11` | character varying(1000) | Y |  |
| 12 | `temp12` | character varying(1000) | Y |  |
| 13 | `temp13` | character varying(1000) | Y |  |
| 14 | `temp14` | character varying(1000) | Y |  |
| 15 | `temp15` | character varying(1000) | Y |  |
| 16 | `temp16` | character varying(1000) | Y |  |
| 17 | `temp17` | character varying(1000) | Y |  |
| 18 | `temp18` | character varying(1000) | Y |  |
| 19 | `temp19` | character varying(1000) | Y |  |
| 20 | `temp20` | character varying(1000) | Y |  |
| 21 | `temp21` | timestamp without time zone | Y |  |
| 22 | `temp22` | timestamp without time zone | Y |  |
| 23 | `temp23` | timestamp without time zone | Y |  |
| 24 | `temp24` | timestamp without time zone | Y |  |
| 25 | `temp25` | timestamp without time zone | Y |  |
| 26 | `temp26` | bytea | Y |  |
| 27 | `temp27` | bytea | Y |  |
| 28 | `temp28` | bytea | Y |  |

### tmp_import_1

ประมาณ 24,410 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `temp1` | character varying(1000) | Y |  |
| 2 | `temp2` | character varying(1000) | Y |  |
| 3 | `temp3` | character varying(1000) | Y |  |
| 4 | `temp4` | character varying(1000) | Y |  |
| 5 | `temp5` | character varying(1000) | Y |  |
| 6 | `temp6` | character varying(3000) | Y |  |
| 7 | `temp7` | character varying(1000) | Y |  |
| 8 | `temp8` | character varying(1000) | Y |  |
| 9 | `temp9` | character varying(1000) | Y |  |
| 10 | `temp10` | character varying(1000) | Y |  |
| 11 | `temp11` | character varying(1000) | Y |  |
| 12 | `temp12` | character varying(1000) | Y |  |
| 13 | `temp13` | character varying(1000) | Y |  |
| 14 | `temp14` | character varying(1000) | Y |  |
| 15 | `temp15` | character varying(1000) | Y |  |
| 16 | `temp16` | character varying(1000) | Y |  |
| 17 | `temp17` | character varying(1000) | Y |  |
| 18 | `temp18` | character varying(1000) | Y |  |
| 19 | `temp19` | character varying(1000) | Y |  |
| 20 | `temp20` | character varying(1000) | Y |  |
| 21 | `temp21` | timestamp without time zone | Y |  |
| 22 | `temp22` | timestamp without time zone | Y |  |
| 23 | `temp23` | timestamp without time zone | Y |  |
| 24 | `temp24` | timestamp without time zone | Y |  |
| 25 | `temp25` | timestamp without time zone | Y |  |
| 26 | `temp26` | bytea | Y |  |
| 27 | `temp27` | bytea | Y |  |
| 28 | `temp28` | bytea | Y |  |

### user_addresses

ประมาณ 22 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `address_no` | character varying(20) | Y |  |
| 2 | `moo` | character varying(10) | Y |  |
| 3 | `building` | character varying(100) | Y |  |
| 4 | `floor` | character varying(10) | Y |  |
| 5 | `soi` | character varying(100) | Y |  |
| 6 | `road` | character varying(100) | Y |  |
| 7 | `user_id` 🔑 | bigint | N |  |
| 8 | `province_id` | bigint | Y |  |
| 9 | `district_id` | bigint | Y |  |
| 10 | `sub_district_id` | bigint | Y |  |
| 11 | `postal_code_id` | bigint | Y |  |

- **PK:** `user_id`
- **FK:** `district_id` → `districts`.`id`
- **FK:** `postal_code_id` → `postal_codes`.`id`
- **FK:** `province_id` → `provinces`.`id`
- **FK:** `sub_district_id` → `sub_districts`.`id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `user_addresses_pkey` — `btree (user_id)`

</details>

### user_area_assignments

ประมาณ 42 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | N |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `area_name` | character varying(100) | N |  |

- **PK:** `id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `idx_user_sub_area_id` — `btree (area_id)`
- `user_area_assignments_pkey` — `btree (id)`

</details>

### user_audit_events

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `action` | text | N |  |
| 4 | `meta` | jsonb | Y |  |
| 5 | `ip` | inet | Y |  |
| 6 | `created_at` | timestamp with time zone | N | now() |

- **PK:** `id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `idx_user_audit_action` — `btree (action)`
- `idx_user_audit_created_at` — `btree (created_at DESC)`
- `user_audit_events_pkey` — `btree (id)`

</details>

### user_employment_details

ประมาณ 81 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `employee_id` | character varying(20) | N |  |
| 2 | `start_date` | date | Y |  |
| 3 | `user_id` 🔑 | bigint | N |  |
| 4 | `employee_type_id` | bigint | Y |  |
| 5 | `position_id` | bigint | Y |  |
| 6 | `area_id` | bigint | Y |  |
| 7 | `position` | character varying(100) | Y |  |
| 8 | `dept` | character varying(100) | Y |  |
| 9 | `department` | character varying(100) | Y |  |
| 10 | `division` | character varying(100) | Y |  |
| 11 | `company_name` | character varying(100) | Y |  |

- **PK:** `user_id`
- **UNIQUE:** `employee_id`
- **FK:** `employee_type_id` → `lookup_values`.`id`
- **FK:** `position_id` → `lookup_values`.`id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `idx_emp_details_employee_id` — `btree (employee_id)`
- `user_employment_details_employee_id_key` — `btree (employee_id)`
- `user_employment_details_pkey` — `btree (user_id)`

</details>

### user_group_members

ประมาณ 184 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` 🔑 | bigint | N |  |
| 2 | `group_id` | bigint | N |  |

- **PK:** `user_id`
- **FK:** `group_id` → `user_groups`.`id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `user_group_members_pkey` — `btree (user_id)`

</details>

### user_groups

ประมาณ 122 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `language_code` | character varying(5) | N | 'th-TH'::character varying |
| 2 | `name` | character varying(100) | Y |  |
| 3 | `is_active` | boolean | N | true |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `updated_at` | timestamp with time zone | N | now() |
| 6 | `created_by` | bigint | Y |  |
| 7 | `updated_by` | bigint | Y |  |
| 8 | `id` 🔑 | bigint | N |  |
| 9 | `parent_id` | bigint | Y |  |
| 10 | `sml_landing_page` | text | Y |  |
| 11 | `siv_landing_page` | text | Y |  |
| 12 | `sbpm_landing_page` | text | Y |  |

- **PK:** `id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `user_groups_new_pkey` — `btree (id)`

</details>

### user_groups_old

ประมาณ 28 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `language_code` | character varying(5) | N | 'th-TH'::character varying |
| 2 | `name` | character varying(50) | Y |  |
| 3 | `is_active` | boolean | N | true |
| 4 | `created_at` | timestamp with time zone | N | now() |
| 5 | `updated_at` | timestamp with time zone | N | now() |
| 6 | `created_by` | bigint | Y |  |
| 7 | `updated_by` | bigint | Y |  |
| 8 | `id` 🔑 | bigint | N |  |
| 9 | `parent_id` | bigint | Y |  |
| 10 | `sml_landing_page` | text | Y |  |
| 11 | `siv_landing_page` | text | Y |  |
| 12 | `sbpm_landing_page` | text | Y |  |

- **PK:** `id`
- **UNIQUE:** `language_code,parent_id,name`
- **FK:** `created_by` → `users`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `uq_user_groups_language_parent_name` — `btree (language_code, parent_id, name)`
- `user_groups_pkey` — `btree (id)`

</details>

### user_log

ประมาณ -1 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | N |  |
| 2 | `log_date` | timestamp with time zone | N | now() |
| 3 | `bu_id` | character varying(6) | Y |  |
| 4 | `action` | character varying(200) | Y |  |
| 5 | `table_name` | character varying(25) | Y |  |
| 6 | `key_field_name1` | character varying(50) | Y |  |
| 7 | `key_field_value1` | character varying(100) | Y |  |
| 8 | `key_field_name2` | character varying(50) | Y |  |
| 9 | `key_field_value2` | character varying(100) | Y |  |
| 10 | `key_field_name3` | character varying(50) | Y |  |
| 11 | `key_field_value3` | character varying(100) | Y |  |
| 12 | `key_field_name4` | character varying(50) | Y |  |
| 13 | `key_field_value4` | character varying(100) | Y |  |
| 14 | `detail` | character varying(4000) | Y |  |
| 15 | `update_date` | timestamp with time zone | Y | now() |
| 16 | `update_user` | character varying(100) | Y |  |

- **FK:** `user_id` → `users`.`id`

### user_store_assignments

ประมาณ 46 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `user_id` | bigint | Y |  |
| 3 | `area_id` | bigint | N |  |
| 4 | `store_id` | character varying(10) | N |  |
| 5 | `store_name` | character varying(100) | Y |  |

- **PK:** `id`
- **FK:** `user_id` → `users`.`id`

<details><summary>Index</summary>

- `idx_user_store_id` — `btree (store_id)`
- `idx_user_store_sub_area` — `btree (area_id)`
- `user_store_assignments_pkey` — `btree (id)`

</details>

### user_sub_group

ตารางเก็บข้อมูลกลุ่มย่อยของผู้ใช้งาน · ประมาณ 6,656 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `user_id` | bigint | Y |  |
| 2 | `group_id` | bigint | Y |  |
| 3 | `store_type` | character varying(5) | Y |  |
| 4 | `store_area` | character varying(5) | Y |  |

### users

ประมาณ 210 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `id` 🔑 | bigint | N |  |
| 2 | `username` | character varying(50) | Y |  |
| 3 | `email` | text | N |  |
| 4 | `phone_number` | character varying(10) | Y |  |
| 5 | `first_name` | text | N |  |
| 6 | `last_name` | text | N |  |
| 7 | `first_name_en` | text | Y |  |
| 8 | `last_name_en` | text | Y |  |
| 9 | `national_id_enc` | bytea | Y |  |
| 10 | `national_id_digest` | bytea | Y |  |
| 11 | `date_of_birth` | date | Y |  |
| 12 | `deleted_at` | timestamp with time zone | Y |  |
| 13 | `created_at` | timestamp with time zone | N | now() |
| 14 | `updated_at` | timestamp with time zone | N | now() |
| 15 | `created_by` | bigint | Y |  |
| 16 | `updated_by` | bigint | Y |  |
| 17 | `auth_source_id` | bigint | Y |  |
| 18 | `role_id` | bigint | Y |  |
| 19 | `status_id` | bigint | Y |  |
| 20 | `title_id` | bigint | Y |  |
| 21 | `franchisee_id` | bigint | Y |  |
| 22 | `email_notification` | text | Y |  |

- **PK:** `id`
- **UNIQUE:** `email`
- **FK:** `auth_source_id` → `lookup_values`.`id`
- **FK:** `created_by` → `users`.`id`
- **FK:** `role_id` → `lookup_values`.`id`
- **FK:** `status_id` → `lookup_values`.`id`
- **FK:** `title_id` → `lookup_values`.`id`
- **FK:** `updated_by` → `users`.`id`

<details><summary>Index</summary>

- `users_email_key` — `btree (email)`
- `users_pkey` — `btree (id)`

</details>

### workflow

ประมาณ 2 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `workflow_id` 🔑 | integer | N | nextval('workflow_workflow_id_seq'::regclass) |
| 2 | `workflow_name` | character varying(100) | Y |  |

- **PK:** `workflow_id`

<details><summary>Index</summary>

- `workflow_pkey` — `btree (workflow_id)`

</details>

### workflow_approver

ประมาณ -1 แถว

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
| 10 | `remark` | character varying(1000) | Y |  |

- **PK:** `approver_id`

<details><summary>Index</summary>

- `workflow_approver_pkey` — `btree (approver_id)`

</details>

### workflow_event

ประมาณ 6 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `event` 🔑 | character varying(10) | N |  |
| 2 | `event_name` | character varying(100) | Y |  |

- **PK:** `event`

<details><summary>Index</summary>

- `workflow_event_pkey` — `btree (event)`

</details>

### workflow_group

ประมาณ 3 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_id` 🔑 | integer | N | nextval('workflow_group_group_id_seq'::regclass) |
| 2 | `group_name` | character varying(100) | Y |  |
| 3 | `approver_type` | character varying(10) | Y |  |

- **PK:** `group_id`

<details><summary>Index</summary>

- `workflow_group_pkey` — `btree (group_id)`

</details>

### workflow_group_map

ประมาณ 9 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `group_map_id` 🔑 | integer | N | nextval('workflow_group_map_group_map_id_seq'::regclass) |
| 2 | `group_id` | integer | Y |  |
| 3 | `map_table` | character varying(50) | Y |  |
| 4 | `map_column` | character varying(10) | Y |  |
| 5 | `map_key` | character varying(50) | Y |  |

- **PK:** `group_map_id`

<details><summary>Index</summary>

- `workflow_group_map_pkey` — `btree (group_map_id)`

</details>

### workflow_history

ประมาณ -1 แถว

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
| 9 | `event` | character varying(10) | Y |  |
| 10 | `create_by` | integer | Y |  |
| 11 | `create_date` | timestamp with time zone | Y |  |
| 12 | `create_by_name` | character varying(100) | Y |  |

- **PK:** `history_id`

<details><summary>Index</summary>

- `workflow_history_pkey` — `btree (history_id)`

</details>

### workflow_part

ประมาณ 5 แถว

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

ประมาณ 41 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `route_id` 🔑 | integer | N | nextval('workflow_route_route_id_seq'::regclass) |
| 2 | `version_id` | integer | Y |  |
| 3 | `from_state_id` | integer | Y |  |
| 4 | `event` | character varying(10) | Y |  |
| 5 | `to_state_id` | integer | Y |  |
| 6 | `seq` | integer | Y |  |
| 7 | `to_status_id` | integer | Y |  |
| 8 | `condition_json` | jsonb | Y |  |
| 9 | `approver_type` | character varying(10) | Y |  |
| 10 | `group_id` | integer | Y |  |
| 11 | `email_id` | integer | Y |  |

- **PK:** `route_id`

<details><summary>Index</summary>

- `workflow_route_pkey` — `btree (route_id)`

</details>

### workflow_state

ประมาณ 10 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `state_id` 🔑 | integer | N |  |
| 2 | `state_name` | character varying(100) | Y |  |
| 3 | `version_id` | bigint | Y |  |

- **PK:** `state_id`

<details><summary>Index</summary>

- `workflow_state_pkey` — `btree (state_id)`

</details>

### workflow_status

ประมาณ 10 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `status_id` 🔑 | integer | N |  |
| 2 | `status_name` | character varying(100) | Y |  |
| 3 | `version_id` | bigint | Y |  |

- **PK:** `status_id`

<details><summary>Index</summary>

- `workflow_status_pkey` — `btree (status_id)`

</details>

### workflow_transaction

ประมาณ 55 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `transaction_id` 🔑 | integer | N | nextval('workflow_transaction_transaction_id_seq'::regclass) |
| 2 | `version_id` | integer | Y |  |
| 3 | `reference_id` | character varying(10) | Y |  |
| 4 | `current_state_id` | integer | Y |  |
| 5 | `current_approver` | integer | Y |  |
| 6 | `approver_type` | character varying(10) | Y |  |
| 7 | `current_status_id` | integer | Y |  |
| 8 | `data_json` | jsonb | Y |  |
| 9 | `update_date` | timestamp with time zone | Y |  |

- **PK:** `transaction_id`

<details><summary>Index</summary>

- `workflow_transaction_pkey` — `btree (transaction_id)`

</details>

### workflow_version

ประมาณ 2 แถว

| # | คอลัมน์ | ชนิด | Null | ค่า default |
|---|---|---|---|---|
| 1 | `version_id` 🔑 | integer | N | nextval('workflow_version_version_id_seq'::regclass) |
| 2 | `workflow_id` | integer | Y |  |
| 3 | `initial_state_id` | integer | Y |  |
| 4 | `initial_status_id` | integer | Y |  |
| 5 | `end_state_id` | integer | Y |  |
| 6 | `end_status_id` | integer | Y |  |
| 7 | `description` | character varying(1000) | Y |  |
| 8 | `update_date` | timestamp with time zone | Y |  |
| 9 | `url_main` | character varying(1000) | Y |  |
| 10 | `url_param_mapping` | jsonb | Y |  |

- **PK:** `version_id`

<details><summary>Index</summary>

- `workflow_version_pkey` — `btree (version_id)`

</details>

---

## View

### v_fz_store_active

```sql
WITH user_list AS (
         SELECT u.id AS user_id,
            u.first_name,
            u.last_name,
            u.username,
            u.email,
            emp.employee_id,
            g.id AS group_id
           FROM ((((users u
             JOIN user_group_members gm_1 ON ((gm_1.user_id = u.id)))
             JOIN user_groups g ON ((g.id = gm_1.group_id)))
             JOIN user_employment_details emp ON ((emp.user_id = u.id)))
             JOIN lookup_values lv ON (((lv.id = u.status_id) AND (lv.parent_id = 1) AND ((lv.name)::text = 'ACTIVE'::text))))
        )
 SELECT fs.order_id,
    ms.branch_id,
    ms.branch_name,
    ms.status_type AS branch_type,
    fs.fr_type,
    fs.fr_subtype,
    cc_st.code_name AS fr_subtype_name,
    cc_ad.code_name AS ad_store_type,
    ms.region,
    fs.start_date,
    fs.cancel_date,
    fz.franchisee_id,
    fz.id_card AS fz_id_card,
    cc1.code_name AS fz_title_name,
    fz.first_name AS fz_first_name,
    fz.last_name AS fz_last_name,
    fz.first_name_en AS fz_first_name_en,
    fz.last_name_en AS fz_last_name_en,
    fz.sex AS fz_sex,
    cc5.code_name AS fz_sex_name,
    fz.email AS fz_email,
    fz.mobile AS fz_mobile,
    fz.create_date AS fz_register_date,
    fc.employee_id AS fc_emp_id,
    mso1.fullname AS fc_fullname,
    fc.first_name AS fc_first_name,
    fc.last_name AS fc_last_name,
    fc.username AS fc_username,
    fc.email AS fc_email,
    mn.employee_id AS mn_emp_id,
    mso2.fullname AS mn_fullname,
    mn.first_name AS mn_first_name,
    mn.last_name AS mn_last_name,
    mn.username AS mn_username,
    mn.email AS mn_email,
    dv.employee_id AS dv_emp_id,
    mso3.fullname AS dv_fullname,
    dv.first_name AS dv_first_name,
    dv.last_name AS dv_last_name,
    dv.username AS dv_username,
    dv.email AS dv_email,
    gm.employee_id AS gm_emp_id,
    mso4.fullname AS gm_fullname,
    gm.first_name AS gm_first_name,
    gm.last_name AS gm_last_name,
    gm.username AS gm_username,
    gm.email AS gm_email,
    vp.employee_id AS vp_emp_id,
    mso5.fullname AS vp_fullname,
    vp.first_name AS vp_first_name,
    vp.last_name AS vp_last_name,
    vp.username AS vp_username,
    vp.email AS vp_email
   FROM ((((((((((((((((franchisee fz
     JOIN fr_store fs ON (((fz.franchisee_id = (fs.owner_id1)::numeric) AND ((COALESCE(fz.status, '-'::character varying))::text <> 'D'::text) AND ((COALESCE(fs.status, '-'::character varying))::text <> 'D'::text) AND ((fs.cancel_type)::text = '00'::text) AND ((fs.cancel_date IS NULL) OR (fs.cancel_date >= CURRENT_DATE)) AND ((fs.owner_id1)::numeric = fz.franchisee_id))))
     JOIN mas_store ms ON ((((ms.branch_id)::text = (fs.store_id)::text) AND (ms.active_flag = 'Y'::bpchar))))
     JOIN store_organize mso1 ON ((((mso1.store_id)::text = (ms.branch_id)::text) AND ((mso1.active_flag)::bpchar = 'Y'::bpchar) AND ((mso1.group_id)::integer = 2000))))
     LEFT JOIN user_list fc ON ((((fc.group_id)::text = (mso1.group_id)::text) AND (((fc.employee_id)::te
```
