#!/usr/bin/env python3
"""แบบจำลอง ER ฉบับสมบูรณ์ของ SBPGI — กลุ่ม / ตารางที่แสดง / ความสัมพันธ์ข้ามระบบ

ที่มาของข้อมูลแต่ละส่วน
  - โครงสร้างตาราง            : tools/er_sources.py (อ่านจาก LLDD-Database.md + SBP/db-schema-*.md)
  - FK ภายในโซน A/B/C         : REFERENCES ใน DDL — ดึงอัตโนมัติ ไม่ hardcode
  - FK จริงของ sps_store/auth : บรรทัด "- **FK:**" ในไฟล์ dump — ดึงอัตโนมัติ
  - ความสัมพันธ์ที่เหลือ       : CROSS ด้านล่าง (logical/api/snapshot) — มี evidence กำกับทุกเส้น

ค่า kind ของความสัมพันธ์
  fk       = foreign key จริงในฐานข้อมูล
  logical  = join key ที่ใช้จริงแต่ไม่มี FK ในฐานข้อมูล (ทั้งสอง schema แทบไม่มี FK)
  api      = ข้ามขอบเขต service — เชื่อมผ่าน HTTP/library ไม่ใช่ SQL join
  snapshot = คัดลอกค่ามาเก็บ ณ เวลาหนึ่ง (ไม่ใช่ join สด)
"""

from __future__ import annotations

# ----------------------------------------------------------------- กลุ่ม (โซน)

GROUPS = [
    {
        "key": "A",
        "schema": "sbpgi",
        "title": "โซน A · FGI/FCS Impact Pipeline",
        "subtitle": "ตารางใหม่ของ SBPGI — ค้นฐานจริง 276 ตารางแล้วไม่มีของเดิมให้ reuse",
        "color": "#0e7c6b",
        "tint": "#e6f6f2",
        "cell": (0, 0),
        "columns": [
            ["fgi_impact_processes", "fgi_impact_compensations", "fgi_impact_stores", "fgi_impact_sales_summaries", "sales_transactions"],
            ["fgi_impact_competitors", "fcs_qssi_score", "interface_transactions"],
        ],
    },
    {
        "key": "B",
        "schema": "sbpgi",
        "title": "โซน B · K2 เอกสารประกันรายได้",
        "subtitle": "แกนเอกสาร + ประวัติ — workflow ใช้ engine กลาง ไม่สร้างตารางเอง",
        "color": "#2f6fed",
        "tint": "#e8effd",
        "cell": (0, 1),
        "columns": [
            ["compensation_documents", "document_running_numbers", "document_new_stores"],
            ["document_cost_details", "document_competitors", "document_external_factors"],
            ["consideration_logs", "document_attachments", "compensation_histories"],
        ],
    },
    {
        "key": "C",
        "schema": "sbpgi",
        "title": "โซน C · Master ที่ SBPGI เป็นเจ้าของ",
        "subtitle": "3 ตาราง — ที่เหลือใช้ master ของระบบ SBP เดิม",
        "color": "#7c3aed",
        "tint": "#f1ebfe",
        "cell": (1, 0),
        "columns": [
            ["impacted_stores", "competitors", "external_factors"],
        ],
    },
    {
        "key": "E",
        "schema": "sps_store",
        "title": "Workflow Engine · @srm/glb-workflow",
        "subtitle": "13 ตารางใน schema sps_store · library กลาง — SBPGI ขอ version ใหม่ 1 ตัว ห้ามสร้างตารางเอง/ห้ามแก้ DDL",
        "color": "#b45309",
        "tint": "#fdf1e0",
        "cell": (1, 1),
        "columns": [
            ["workflow", "workflow_version", "workflow_state", "workflow_status"],
            ["workflow_event", "workflow_route", "workflow_group", "workflow_group_map"],
            ["workflow_transaction", "workflow_approver", "workflow_history"],
            ["workflow_part", "workflow_part_display"],
        ],
    },
    {
        "key": "P",
        "schema": "sps_store",
        "title": "SBP Platform · schema sps_store",
        "subtitle": "198 ตาราง — แสดง 24 ตารางที่ SBPGI ใช้ · ระบบเดิมเป็นเจ้าของ SBPGI อ่าน/เรียก API เท่านั้น เพิ่มคอลัมน์ต้อง sign-off",
        "color": "#166534",
        "tint": "#e7f4ec",
        "cell": (2, 0),
        "columns": [
            ["store", "mas_store", "sevenshop"],
            ["fr_store", "fr_store_insure", "juristic"],
            ["franchisee", "store_organize", "fml_responsible_sbp"],
            ["business_user", "business_user_group", "business_group"],
            ["common_code", "common_code_type", "mas_zone"],
            ["mas_param", "integration_log", "upload_general"],
            ["email_template", "email_sent", "general_upload_data_page_job",
             "general_upload_data_page_audit_log"],
            ["fcs_monthly_sales", "fml_sbp_stmt", "statement", "fml_cooperation_trn"],
        ],
    },
    {
        "key": "I",
        "schema": "sps_auth",
        "title": "Auth Backend · schema sps_auth",
        "subtitle": "78 ตาราง — แสดง 10 ตาราง · ตัวตน/สิทธิ์เมนู\nSBPGI รับผ่าน header ของ BFF ไม่ query ตรง",
        "color": "#9f1239",
        "tint": "#fdeaef",
        "cell": (1, 2),
        "columns": [
            ["users", "user_groups", "user_group_members", "group_permissions", "app_menus",
             "lookup_values"],
            ["business_user", "employee_store", "mas_store", "fr_store", "franchisee"],
        ],
    },
]

# ------------------------------------------------- คอลัมน์ที่แสดงของตารางระบบเดิม
# ตาราง SBPGI + engine แสดง "ทุกคอลัมน์" · ตารางแพลตฟอร์มที่กว้างมาก (สูงสุด 86 คอลัมน์)
# แสดงเฉพาะคอลัมน์คีย์/คอลัมน์ที่ SBPGI ใช้จริง แล้วบอกจำนวนที่ซ่อนไว้ท้ายกล่อง

KEY_COLS: dict[str, list[str]] = {
    "sps_store.store": [
        "store_id", "store_name", "business_type", "store_type", "area_id", "zone_cd",
        "store_open_date", "store_close_date", "store_status_type", "data_type",
    ],
    "sps_store.mas_store": [
        "branch_id", "branch_name", "branch_type", "status_type", "area_id", "region",
        "zone_cd", "open_date", "close_date", "fr_sub_type",
    ],
    "sps_store.sevenshop": [
        "branch_id", "shop_type", "branch_name", "branch_type", "area_id", "region",
        "zone_cd", "open_date", "close_date", "fc_name", "mn_name",
        "start_renovate_date", "end_renovate_date",
    ],
    "sps_store.fr_store": [
        "order_id", "store_id", "store_name", "region", "juristic_id", "juristic_group_id",
        "start_date", "transfer_date", "open_date", "contract_start_date", "contract_end_date",
        "store_type", "fr_type", "cur_owner_id", "status",
    ],
    "sps_store.fr_store_insure": [
        "order_id", "store_id", "seq_no", "year", "month", "money_support", "split",
    ],
    "sps_store.franchisee": ["cust_id", "franchisee_id", "first_name", "last_name", "id_card", "status_code"],
    "sps_store.juristic": ["juristic_id", "juristic_name", "franchisee_id", "juristic_group_id", "juristic_no"],
    "sps_store.business_user": [
        "user_id", "user_name", "group_id", "first_name", "last_name", "email",
        "emp_id", "position_level", "zone_cd", "active_flag", "franchisee_id",
    ],
    "sps_store.business_user_group": [
        "user_id", "group_id", "store_type", "store_area", "group_name", "parent_group_id",
    ],
    "sps_store.business_group": ["group_id", "group_name", "parent_group_id", "system_code"],
    "sps_store.store_organize": [
        "store_id", "employee_id", "first_name", "last_name", "email", "group_id", "active_flag",
    ],
    "sps_store.mas_store_organize": ["store_id", "employee_id", "group_id"],
    "sps_store.statement": ["id", "store_id", "report_type", "year", "month", "day", "file_name", "zone_cd"],
    "sps_store.fml_sbp_stmt": [
        "sbp_stmt_id", "process_id", "report_type", "store_id", "year", "month", "day",
        "report_link", "document_id", "channel_tran_id",
    ],
    "sps_store.fcs_monthly_sales": ["id", "store_id", "year", "month", "total_sales", "total_day"],
    "sps_store.fml_responsible_sbp": ["responsible_sbp_id", "store_ptt", "region", "name", "email"],
    "sps_auth.business_user": [
        "user_id", "user_name", "group_id", "first_name", "last_name", "email",
        "emp_id", "position_level", "active_flag",
    ],
    "sps_auth.mas_store": ["branch_id", "branch_name", "branch_type", "area_id", "region", "zone_cd"],
    "sps_auth.fr_store": ["order_id", "store_id", "store_name", "juristic_id", "region", "status"],
    "sps_auth.franchisee": ["cust_id", "franchisee_id", "first_name", "last_name", "id_card"],
    "sps_auth.employee_store": [
        "id", "store_id", "employee_id", "first_name", "last_name", "position_id",
        "department_id", "username", "role_id",
    ],
    "sps_auth.users": [
        "id", "username", "email", "first_name", "last_name", "auth_source_id",
        "role_id", "status_id", "franchisee_id",
    ],
    "sps_auth.user_groups": ["id", "name", "parent_id", "is_active", "sbpm_landing_page"],
    "sps_auth.group_permissions": [
        "id", "menu_id", "group_id", "can_view", "can_manage", "can_export", "can_other",
    ],
    "sps_auth.app_menus": ["id", "name", "target_url", "parent_id", "sort_order", "is_active"],
    "sps_auth.lookup_values": ["id", "name", "code_value", "parent_id", "sort_order", "is_active"],
    "sps_store.fml_cooperation_trn": [
        "trn_id", "doc_number", "store_id", "doc_type", "create_by", "operate_by", "year",
    ],
    "sps_store.general_upload_data_page_job": ["id", "code_type", "code_value", "file_name", "status"],
    "sps_store.general_upload_data_page_audit_log": ["id", "status", "create_date", "create_by"],
}

# ----------------------------------------------------- ความสัมพันธ์ที่ไม่ได้มาจาก DDL
# (from_table, from_col, to_table, to_col, kind, cardinality, label, evidence, status)

CROSS: list[tuple] = [
    # ---------- workflow engine ภายใน (schema sps_store · ไม่มี FK ในฐานจริง) ----------
    ("sps_store.workflow_version", "workflow_id", "sps_store.workflow", "workflow_id", "logical", "N:1",
     "version ของ workflow", "db-schema-sps_store.md §workflow_version", "confirmed"),
    ("sps_store.workflow_version", "initial_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state เริ่มต้น", "db-schema-sps_store.md §workflow_version", "confirmed"),
    ("sps_store.workflow_version", "end_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state สิ้นสุด", "db-schema-sps_store.md §workflow_version", "confirmed"),
    ("sps_store.workflow_version", "initial_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status เริ่มต้น", "db-schema-sps_store.md §workflow_version", "confirmed"),
    ("sps_store.workflow_version", "end_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status สิ้นสุด", "db-schema-sps_store.md §workflow_version", "confirmed"),
    ("sps_store.workflow_state", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "18 state ต่อ version", "db-schema-sps_store.md §workflow_state", "confirmed"),
    ("sps_store.workflow_status", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "22 status ต่อ version", "db-schema-sps_store.md §workflow_status", "confirmed"),
    ("sps_store.workflow_route", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "43 route ต่อ version", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "from_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state ต้นทาง", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "to_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state ปลายทาง", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "to_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status ปลายทาง", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "event", "sps_store.workflow_event", "event", "logical", "N:1",
     "เหตุการณ์ที่กระตุ้น route", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "group_id", "sps_store.workflow_group", "group_id", "logical", "N:1",
     "กลุ่มผู้อนุมัติของ route", "db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_route", "email_id", "sps_store.email_template", "email_template_id", "logical", "N:1",
     "เลข template ของ workflow — SBPGI อ่านค่านี้ไปเรียก sendEmail() ของ email-lib เอง (ปิด DP-5 · 14/08/2026)",
     "database.md §ปิด DP-5 · db-schema-sps_store.md §workflow_route", "confirmed"),
    ("sps_store.workflow_group_map", "group_id", "sps_store.workflow_group", "group_id", "logical", "N:1",
     "map กลุ่ม → ตาราง/คอลัมน์จริง", "db-schema-sps_store.md §workflow_group_map", "confirmed"),
    ("sps_store.workflow_transaction", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "instance ของ version", "db-schema-sps_store.md §workflow_transaction", "confirmed"),
    ("sps_store.workflow_transaction", "current_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state ปัจจุบัน", "db-schema-sps_store.md §workflow_transaction", "confirmed"),
    ("sps_store.workflow_transaction", "current_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status ปัจจุบัน", "db-schema-sps_store.md §workflow_transaction", "confirmed"),
    ("sps_store.workflow_transaction", "current_approver", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้อนุมัติปัจจุบัน", "db-schema-sps_store.md §workflow_transaction", "confirmed"),
    ("sps_store.workflow_history", "transaction_id", "sps_store.workflow_transaction", "transaction_id", "logical", "1:N",
     "timeline 38,010 แถว", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "event", "sps_store.workflow_event", "event", "logical", "N:1",
     "เหตุการณ์ที่บันทึก", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_approver", "transaction_id", "sps_store.workflow_transaction", "transaction_id", "logical", "1:N",
     "prepared approver 96,542 แถว", "db-schema-sps_store.md §workflow_approver", "confirmed"),
    ("sps_store.workflow_approver", "state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "ผู้อนุมัติต่อ state", "db-schema-sps_store.md §workflow_approver", "confirmed"),
    ("sps_store.workflow_approver", "current_approver", "sps_store.business_user", "user_id", "logical", "N:1",
     "ตัวผู้อนุมัติ", "db-schema-sps_store.md §workflow_approver", "confirmed"),
    ("sps_store.workflow_part", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "ส่วนของหน้าจอต่อ version", "db-schema-sps_store.md §workflow_part", "confirmed"),
    ("sps_store.workflow_part_display", "part_id", "sps_store.workflow_part", "part_id", "logical", "N:1",
     "สิทธิ์ READ/WRITE ต่อส่วน", "db-schema-sps_store.md §workflow_part_display", "confirmed"),
    ("sps_store.workflow_part_display", "state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "แสดงผลต่อ state", "db-schema-sps_store.md §workflow_part_display", "confirmed"),
    ("sps_store.workflow_part_display", "group_id", "sps_store.workflow_group", "group_id", "logical", "N:1",
     "แสดงผลต่อกลุ่ม", "db-schema-sps_store.md §workflow_part_display", "confirmed"),

    # ---------- SBPGI ↔ workflow engine ----------
    ("sbpgi.compensation_documents", "id", "sps_store.workflow_transaction", "reference_id", "api", "1:1",
     "referenceId = surrogate id (มติ DP-1 = B)", "database.md §กุญแจเชื่อมข้ามระบบ ข้อ 4", "confirmed"),
    ("sbpgi.compensation_documents", "status_code", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "สถานะเอกสาร 6 ค่า = status ของ engine", "LLDD-Database.md §5.3 · database.md", "confirmed"),
    ("sbpgi.compensation_documents", "current_section_code", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "ขั้น 06/08/01/02/03 = state ของ engine", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.consideration_logs", "section_code", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "ขั้นที่พิจารณา", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.consideration_logs", "id", "sps_store.workflow_history", "history_id", "logical", "1:1",
     "ส่วนขยาย timeline (engine ไม่มีรหัสผลพิจารณา/ไฟล์แนบ)", "database.md §ตารางที่คล้ายแต่ไม่ใช่", "undecided · DP-7"),
    ("sbpgi.document_attachments", "section_code", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "ไฟล์แนบแยกตามขั้น", "LLDD-Database.md §5.3", "confirmed"),

    # ---------- SBPGI ↔ master ร้าน ----------
    ("sbpgi.impacted_stores", "store_code", "sps_store.store", "store_id", "logical", "1:1",
     "ร้าน SP · snapshot บางส่วน (มติ DP-3)", "database.md §โซน C · DP-3", "confirmed"),
    ("sbpgi.impacted_stores", "store_code", "sps_store.mas_store", "branch_id", "logical", "1:1",
     "master สาขา", "database.md §ตารางที่ตัดออกรอบ 2", "confirmed"),
    ("sbpgi.impacted_stores", "store_code", "sps_store.sevenshop", "branch_id", "logical", "1:1",
     "renovate start/end date อ่านจากที่นี่ (ข้อ F5)", "database.md §F5", "confirmed"),
    ("sbpgi.impacted_stores", "store_code", "sps_store.fr_store", "store_id", "logical", "1:N",
     "สัญญา/นิติบุคคลของร้าน SP", "SBPGI-vs-existing-system.md §3", "confirmed"),
    ("sbpgi.impacted_stores", "opt_dv_user_id", "sps_store.business_user", "user_id", "logical", "N:1",
     "DV/ผู้ดูแลร้าน", "LLDD-Database.md §5.1 (คอมเมนต์ไม่ใส่ FK)", "confirmed"),
    ("sbpgi.fgi_impact_stores", "new_store_code", "sps_store.store", "store_id", "logical", "N:1",
     "ร้านเปิดใหม่ · master ของระบบเดิม", "LLDD-Database.md §5.2", "confirmed"),
    ("sbpgi.document_new_stores", "new_store_code", "sps_store.store", "store_id", "logical", "N:1",
     "ร้านเปิดใหม่ในเอกสาร", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.document_cost_details", "new_store_code", "sps_store.store", "store_id", "logical", "N:1",
     "ยอดชดเชยรายเดือนต่อร้านใหม่", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.compensation_histories", "store_code", "sps_store.store", "store_id", "logical", "N:1",
     "ประวัติชดเชยรายร้าน", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.compensation_histories", "compensate_amount", "sps_store.fr_store_insure", "money_support", "logical", "N:1",
     "ตัวเลขเงินประกันรายได้ — SBPGI เป็นต้นทางหรือคีย์มือ", "database.md §โซน B · DP-11", "undecided · DP-11"),

    # ---------- SBPGI ↔ ผู้ใช้ / lookup / config ----------
    ("sbpgi.compensation_documents", "created_by", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้สร้างเอกสาร", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.compensation_documents", "approver_snapshot", "sps_store.business_user", "user_id", "snapshot", "N:1",
     "FC/Section/GM/AVP ณ เวลาเปิดเอกสาร (ตำแหน่งเปลี่ยนได้)", "database.md §โซน B", "confirmed"),
    ("sbpgi.consideration_logs", "consider_by", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้พิจารณา", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.document_attachments", "uploaded_by", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้แนบไฟล์", "LLDD-Database.md §5.3", "confirmed"),
    ("sbpgi.compensation_documents", "statement_id", "sps_store.fml_sbp_stmt", "document_id", "logical", "N:1",
     "โยงกลับ SBP Statement ต้นทาง (CompStatementID)", "database.md §โซน B · §ขอบเขต", "confirmed"),
    ("sbpgi.compensation_documents", "impacted_store_code", "sps_store.statement", "store_id", "logical", "N:1",
     "ใบแจ้งยอดของร้าน/งวด — Period Statement ของรายงาน (SDD สไลด์ 60)", "database.md §โซน B", "proposed"),
    ("sbpgi.fcs_qssi_score", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "คะแนน QSSI ต่อร้าน 23.9 ล้านแถว", "db-schema-sps_store.md §fcs_qssi_score", "confirmed"),
    ("sbpgi.fgi_impact_processes", "impacted_store_code", "sps_store.fcs_monthly_sales", "store_id", "logical", "N:1",
     "cross-check ยอดรวมรายเดือน (แทน sales_transactions รายวันไม่ได้)", "database.md §ผลการเทียบ ข้อ 5", "confirmed"),
    ("sbpgi.document_attachments", "object_key", "sps_store.upload_general", "key", "api", "N:1",
     "ใช้ service S3 ของระบบเดิม (upload/download-file-aws)", "database.md §ตารางที่คล้ายแต่ไม่ใช่ · DP-8", "undecided · DP-8"),
    ("sbpgi.interface_transactions", "correlation_id", "sps_store.integration_log", "service", "api", "1:N",
     "payload ราย call แทนตาราง FGI_WS_LOG (ข้อ F6) — ยังไม่มีคอลัมน์คีย์เชื่อมกลับ", "database.md §F6", "proposed"),

    # ---------- lookup กลาง (common_code / mas_param / mas_zone) ----------
    ("sbpgi.consideration_logs", "result", "sps_store.common_code", "code_value", "logical", "N:1",
     "ผลพิจารณา — code_type=SBPGI_DECISION (มติ DP-9)", "database.md §มติ DP-9 · การ map decisions", "confirmed"),
    ("sbpgi.compensation_documents", "total_compensation_amount", "sps_store.common_code", "code_value", "logical", "N:1",
     "วงเงินอนุมัติ SBPGI_APPROVE_LIMIT (เกณฑ์เดียว 100,000)", "database.md §ตารางที่ตัดออกรอบ 2 · SDD GI", "confirmed"),
    ("sbpgi.compensation_documents", "(BE service)", "sps_store.mas_param", "param_name", "api", "N:1",
     "ค่ากำหนดกลาง — SBPGI อ่านอย่างเดียว ไม่มีหน้าจอแก้", "database.md §ตารางที่ตัดออกรอบ 2", "confirmed"),

    ("sbpgi.document_running_numbers", "year", "sbpgi.compensation_documents", "year", "logical", "1:N",
     "ออกเลข YYYY/xxxxx แบบ atomic ต่อปี ค.ศ.", "LLDD-Database.md §5.3 · database.md §Canonical", "confirmed"),
    ("sbpgi.fgi_impact_competitors", "competitor_code", "sbpgi.document_competitors", "source_system", "logical", "1:N",
     "นำเข้าเป็นแถว source_system=ALLMAP (แยกจาก USER ที่ผู้ใช้เพิ่มเอง)", "database.md §กุญแจเชื่อมข้ามระบบ ข้อ 5", "confirmed"),
    ("sbpgi.fgi_impact_stores", "new_store_code", "sbpgi.document_new_stores", "new_store_code", "logical", "1:1",
     "คู่ร้านจาก pipeline → ร้านใหม่ในเอกสาร", "database.md §Data Dictionary", "confirmed"),

    # ---------- ภายในระบบเดิม (sps_store) ----------
    ("sps_store.common_code", "code_type", "sps_store.common_code_type", "code_type", "logical", "N:1",
     "ต้องลงทะเบียน code_type ก่อนใช้", "database.md §มติ DP-9", "confirmed"),
    ("sps_store.email_sent", "email_id", "sps_store.email_template", "email_template_id", "logical", "N:1",
     "log อีเมลทุกฉบับ 5,214 แถว", "db-schema-sps_store.md §email_sent", "confirmed"),
    ("sps_store.business_user", "group_id", "sps_store.business_group", "group_id", "logical", "N:1",
     "กลุ่มหลักของผู้ใช้", "db-schema-sps_store.md §business_user", "confirmed"),
    ("sps_store.business_user_group", "user_id", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้ใช้อยู่ได้หลายกลุ่ม", "db-schema-sps_store.md §business_user_group", "confirmed"),
    ("sps_store.business_user_group", "group_id", "sps_store.business_group", "group_id", "logical", "N:1",
     "(store_type, store_area) = คีย์ resolve ผู้อนุมัติ", "database.md §ขอบเขต V_FGI_SBP_APPROVER", "confirmed"),
    ("sps_store.business_user", "franchisee_id", "sps_store.franchisee", "franchisee_id", "logical", "N:1",
     "ผู้ใช้ฝั่งผู้รับสิทธิ์", "db-schema-sps_store.md §business_user", "proposed"),
    ("sps_store.mas_store", "branch_id", "sps_store.store", "store_id", "logical", "1:1",
     "รหัสสาขา 5 หลักเดียวกันทั้งระบบ", "db-schema-sps_store.md", "confirmed"),
    ("sps_store.sevenshop", "branch_id", "sps_store.mas_store", "branch_id", "logical", "1:1",
     "ข้อมูลสาขาเชิงปฏิบัติการ (FC/MN/renovate)", "db-schema-sps_store.md §sevenshop", "confirmed"),
    ("sps_store.fr_store", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "สัญญาร้าน SP ต่อรอบ", "db-schema-sps_store.md §fr_store", "confirmed"),
    ("sps_store.fr_store", "juristic_id", "sps_store.juristic", "juristic_id", "logical", "N:1",
     "นิติบุคคลคู่สัญญา", "db-schema-sps_store.md §fr_store", "confirmed"),
    ("sps_store.fr_store_insure", "order_id", "sps_store.fr_store", "order_id", "logical", "N:1",
     "เงินประกันรายได้ต่อสัญญา 708 แถว", "db-schema-sps_store.md §fr_store_insure", "confirmed"),
    ("sps_store.juristic", "franchisee_id", "sps_store.franchisee", "franchisee_id", "logical", "N:1",
     "ผู้รับสิทธิ์ของนิติบุคคล", "db-schema-sps_store.md §juristic", "confirmed"),
    ("sps_store.store_organize", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "ผู้ดูแลร้านรายคน 79,722 แถว", "db-schema-sps_store.md §store_organize", "confirmed"),
    ("sps_store.store_organize", "employee_id", "sps_store.business_user", "emp_id", "logical", "N:1",
     "โยงพนักงานกับร้าน", "db-schema-sps_store.md §store_organize", "proposed"),
    ("sps_store.fcs_monthly_sales", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "ยอดขายรายเดือน 711,384 แถว", "db-schema-sps_store.md §fcs_monthly_sales", "confirmed"),
    ("sps_store.fml_sbp_stmt", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "SBP Statement ต่อร้าน/งวด", "db-schema-sps_store.md §fml_sbp_stmt", "confirmed"),
    ("sps_store.statement", "store_id", "sps_store.store", "store_id", "logical", "N:1",
     "ใบแจ้งยอด 174,084 แถว", "db-schema-sps_store.md §statement", "confirmed"),
    ("sps_store.fml_responsible_sbp", "region", "sps_store.mas_zone", "zone_cd", "logical", "N:1",
     "ผู้รับผิดชอบ SBP รายภาค", "db-schema-sps_store.md §fml_responsible_sbp", "proposed"),
    ("sps_store.store", "zone_cd", "sps_store.mas_zone", "zone_cd", "logical", "N:1",
     "ภาคของร้าน", "db-schema-sps_store.md §store", "confirmed"),

    # ---------- ภายใน sps_auth + ข้าม schema ----------
    ("sps_auth.user_group_members", "user_id", "sps_auth.users", "id", "logical", "N:1",
     "สมาชิกกลุ่ม", "db-schema-sps_auth.md §user_group_members", "confirmed"),
    ("sps_auth.user_group_members", "group_id", "sps_auth.user_groups", "id", "logical", "N:1",
     "กลุ่มสิทธิ์ (ABS group)", "db-schema-sps_auth.md §user_group_members", "confirmed"),
    ("sps_auth.group_permissions", "group_id", "sps_auth.user_groups", "id", "logical", "N:1",
     "สิทธิ์ต่อกลุ่ม 2,300 แถว", "db-schema-sps_auth.md §group_permissions", "confirmed"),
    ("sps_auth.group_permissions", "menu_id", "sps_auth.app_menus", "id", "logical", "N:1",
     "canView/canManage/canExport/canOther ต่อ URL", "db-schema-sps_auth.md §group_permissions", "confirmed"),
    ("sps_auth.app_menus", "parent_id", "sps_auth.app_menus", "id", "logical", "N:1",
     "เมนูซ้อนชั้น", "db-schema-sps_auth.md §app_menus", "confirmed"),
    ("sps_auth.users", "franchisee_id", "sps_auth.franchisee", "franchisee_id", "logical", "N:1",
     "ผู้ใช้ฝั่งผู้รับสิทธิ์", "db-schema-sps_auth.md §users", "confirmed"),
    ("sps_auth.employee_store", "store_id", "sps_auth.mas_store", "branch_id", "logical", "N:1",
     "พนักงานประจำร้าน", "db-schema-sps_auth.md §employee_store", "proposed"),
    ("sps_auth.fr_store", "store_id", "sps_auth.mas_store", "branch_id", "logical", "N:1",
     "สัญญาร้าน (สำเนาฝั่ง auth)", "db-schema-sps_auth.md §fr_store", "proposed"),
    ("sps_auth.business_user", "user_id", "sps_store.business_user", "user_id", "logical", "1:1",
     "ตารางชื่อเดียวกันคนละ schema (22,057 vs 12,752 แถว)", "db-schema ทั้งสองไฟล์", "confirmed"),
    ("sbpgi.compensation_documents", "created_by", "sps_auth.users", "username", "api", "N:1",
     "ตัวตนมาทาง header x-user-id ของ BFF ไม่ query ตรง", "database.md §ตารางที่ตัดออก 2026-08-05", "confirmed"),
    ("sps_auth.users", "username", "sps_store.business_user", "user_name", "logical", "1:1",
     "บัญชี Cognito ↔ ผู้ใช้ระบบเดิม", "SBPGI-vs-existing-system.md", "proposed"),

    # ---------- engine: history/approver ผูกกับ state · status · version · ผู้ทำรายการ ----------
    ("sps_store.workflow_history", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "denormalize version ไว้ที่ประวัติ", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "old_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state ก่อนเปลี่ยน", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "new_state_id", "sps_store.workflow_state", "state_id", "logical", "N:1",
     "state หลังเปลี่ยน", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "old_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status ก่อนเปลี่ยน", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "new_status_id", "sps_store.workflow_status", "status_id", "logical", "N:1",
     "status หลังเปลี่ยน", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_history", "create_by", "sps_store.business_user", "user_id", "logical", "N:1",
     "ผู้ทำ action (มี create_by_name เก็บชื่อ snapshot)", "db-schema-sps_store.md §workflow_history", "confirmed"),
    ("sps_store.workflow_approver", "version_id", "sps_store.workflow_version", "version_id", "logical", "N:1",
     "denormalize version ไว้ที่แถวผู้อนุมัติ", "db-schema-sps_store.md §workflow_approver", "confirmed"),
    ("sps_store.workflow_approver", "approve_event", "sps_store.workflow_event", "event", "logical", "N:1",
     "ผลที่ผู้อนุมัติกด (ชนิดไม่ตรง varchar(100) vs varchar(10))", "db-schema-sps_store.md §workflow_approver", "confirmed"),

    # ---------- master ของระบบเดิมที่ผูกกันเอง (เพิ่มรอบตรวจ 11/08/2026) ----------
    ("sps_store.fr_store", "fr_type", "sps_store.common_code", "code_value", "logical", "N:1",
     "ประเภทร้าน (code_type='00019')", "db-schema-sps_store.md §fr_store", "proposed"),
    ("sps_store.fr_store", "cur_owner_id", "sps_store.franchisee", "franchisee_id", "logical", "N:1",
     "เจ้าของร้านปัจจุบัน", "db-schema-sps_store.md §fr_store", "proposed"),
    ("sps_store.business_group", "parent_group_id", "sps_store.business_group", "group_id", "logical", "N:1",
     "กลุ่มลูก → กลุ่มแม่", "db-schema-sps_store.md §business_group", "confirmed"),
    ("sps_store.store_organize", "group_id", "sps_store.business_group", "group_id", "logical", "N:1",
     "บทบาทของพนักงานในร้าน", "db-schema-sps_store.md §store_organize", "proposed"),
    ("sps_store.mas_store", "zone_cd", "sps_store.mas_zone", "zone_cd", "logical", "N:1",
     "สาขา → ภาค", "db-schema-sps_store.md §mas_store", "confirmed"),
    ("sps_store.sevenshop", "zone_cd", "sps_store.mas_zone", "zone_cd", "logical", "N:1",
     "สาขา 7-Eleven → ภาค", "db-schema-sps_store.md §sevenshop", "confirmed"),
    ("sps_store.business_user", "zone_cd", "sps_store.mas_zone", "zone_cd", "logical", "N:1",
     "ผู้ใช้ → ภาคที่รับผิดชอบ", "db-schema-sps_store.md §business_user", "confirmed"),
    ("sps_store.upload_general", "code_type", "sps_store.common_code", "code_type", "logical", "N:1",
     "ประเภทเอกสารแนบ", "db-schema-sps_store.md §upload_general", "proposed"),
    ("sps_store.fml_sbp_stmt", "report_type", "sps_store.statement", "report_type", "logical", "N:1",
     "ทะเบียน SBP ↔ ไฟล์ statement รอบเดียวกัน (store_id+year+month+day)", "db-schema-sps_store.md", "proposed"),

    # ---------- ภายใน sps_auth (เพิ่ม) ----------
    ("sps_auth.user_groups", "parent_id", "sps_auth.user_groups", "id", "logical", "N:1",
     "กลุ่มแม่-ลูก", "db-schema-sps_auth.md §user_groups", "confirmed"),
    ("sps_auth.business_user", "group_id", "sps_auth.user_groups", "id", "logical", "N:1",
     "กลุ่มของผู้ใช้ระดับ business — ยังไม่ยืนยันว่าชี้ user_groups", "db-schema-sps_auth.md §business_user", "proposed"),
    ("sps_auth.business_user", "franchisee_id", "sps_auth.franchisee", "franchisee_id", "logical", "N:1",
     "ผู้ใช้ที่เป็น Store Partner", "db-schema-sps_auth.md §business_user", "proposed"),

    # ---------- ข้ามสกีมา sps_auth ↔ sps_store ----------
    ("sps_auth.mas_store", "branch_id", "sps_store.store", "store_id", "logical", "1:1",
     "รหัสร้านเดียวกันทั้งสองสกีมา — SBPGI ใช้ฝั่ง sps_store", "db-schema ทั้งสองไฟล์", "confirmed"),
    ("sps_auth.mas_store", "branch_id", "sps_store.mas_store", "branch_id", "logical", "1:1",
     "mas_store สองสำเนา 31 คอลัมน์เท่ากัน (18,790 vs 19,647 แถว)", "db-schema ทั้งสองไฟล์", "confirmed"),

    # ---------- SBPGI → master ร้าน (หน้าเอกสารดึงชื่อร้าน/ภาค/ประเภทสาขา) ----------
    ("sbpgi.compensation_documents", "impacted_store_code", "sps_store.store", "store_id", "logical", "N:1",
     "ชื่อร้าน · ภาค (zone_cd) · ประเภทสาขา บนหน้าเอกสาร/รายงาน", "LLDD-BE-API-Document-Detail-Aggregate.md", "confirmed"),
]

# ------------------------------------------------------------- หมายเหตุบนรูป

WARNINGS = [
    ("sps_store.workflow_transaction", "ไม่มี PK และไม่มี index เลย ทั้งที่มี 19,283 แถว — DP-2 ยังไม่ตัดสิน"),
    ("sps_store.fcs_qssi_score", "23.9 ล้านแถว · ห้าม CREATE ใหม่ · ห้ามใช้ชื่อพหูพจน์ · DP-4"),
    ("sps_store.common_code", "ไม่มี PK/unique — กันรหัสซ้ำที่ระดับแอป"),
    ("sbpgi.compensation_documents", "PK = id (surrogate) · doc_no เป็น UNIQUE · referenceId = id (DP-1 = B)"),
]

FORBIDDEN = [
    "sps_auth.workflow_* — engine คนละเวอร์ชันกับ sps_store (workflow_state คนละจำนวนคอลัมน์) ห้าม SBPGI เขียนลง",
    "sps_store.wf_* — engine เก่าอีกชุดใน schema เดียวกับตัวจริง (wf_transaction 53,186 · wf_approve 155,740 · wf_email_template 118) ห้ามใช้",
    "store_old · store_organize_old · juristic_backup · fml_cooperation_topic_backup · mas_tmp_store · fes_*_bak_20260710 · sps_auth.user_groups_old — ห้าม join",
    "fcs_qssi_score_bak_20260710 (18,577,924 แถว) — snapshot ก่อน rework · fcs_tmp_qssi_score โครงคนละชุด",
    "fcs_qssi_scores (พหูพจน์) — ชื่อผิด ของจริงคือ fcs_qssi_score",
]


# ------------------------------------- การ์ดหมายเหตุ (วางในพื้นที่ว่างขวาบนของรูป)

NOTES = [
    ("มติที่ตรึงโครงนี้ไว้แล้ว", [
        "DP-1 (10/08/2026) = ทางเลือก B — compensation_documents ใช้ surrogate PK `id`",
        "   · `doc_no` เป็น UNIQUE (business key) · referenceId ที่ส่งให้ engine = `id`",
        "DP-3 = ผสม — impacted_stores เป็น snapshot เฉพาะร้านที่เคยเข้ารอบชดเชย",
        "   ไม่ sync ทั้ง master 11,583 แถว (v_fr_store_active ตัดร้านที่ยกเลิกออก)",
        "DP-9 = แยกตัดสิน — `decisions` ตัดทิ้ง ใช้ common_code (SBPGI_DECISION)",
        "   · external_factors + competitors ยังเป็นตารางของ SBPGI เพราะมีหน้าจอ CRUD",
        "05/08/2026 — RBAC/ผู้ปฏิบัติงานใช้ของระบบเดิม (ตัด 5 ตาราง)",
        "06/08/2026 — ตัด 10 ตารางที่ระบบ SBP เดิมมีอยู่แล้ว + ตัดกลุ่ม batch 2 ตาราง",
        "07/08/2026 — ยกเลิก audit_logs → ย้าย marker ไป interface_transactions",
        "DP-5 (แก้มติ 14/08/2026) ปิดแล้ว — workflow ให้เลข template · SBPGI เรียก lib ส่งเอง · ตัด status_email_rules",
        "   อ่าน workflow_route.email_id → sendEmail() ของ email-lib → lib เขียน email_sent ของระบบเดิมให้เอง",
        "   → โครงเหลือ 20 ตาราง (โซน A 8 · B 9 · C 3)",
    ]),
    ("ข้อค้างที่ยังไม่ตัดสิน — กระทบรูปนี้โดยตรง", [
        "DP-2  workflow_transaction ไม่มี PK/index ทั้งที่มี 19,283 แถว (ตารางของ library)",
        "DP-4  fcs_qssi_score — 4 คอลัมน์คีย์เป็น nullable · จะแก้ตารางเดิมอย่างไร",
        "DP-6  interface_transactions — ออกแบบใหม่ หรือลอกแพตเทิร์น statement_summary",
        "DP-7  consideration_logs — timeline เต็ม หรือส่วนขยายบน workflow_history",
        "DP-8  document_attachments — ตารางของเราเอง หรือต่อยอด upload_general",
        "DP-11 ตัวเลขเงินประกันรายได้ — SBPGI เป็นต้นทาง หรือ fr_store_insure คีย์มือ",
        "DP-12 audit ของ master จะเอากลับมาด้วยกลไกของระบบเดิมหรือไม่",
        "(ปิดแล้ว 14/08/2026) ชื่อ function ของ engine ยึดชีต Detail ของ LLDD lib — 8 ตัว initializeWorkflow/eventWorkflow/",
        "   getPermissionEvents/getHistory/getTransaction/getPendingFlowByUser/getWorkflowsByUser/addPreApprover",
    ]),
    ("อ่านรูปนี้อย่างไร", [
        "กล่องสีเข้ม = ตารางในโครง SBPGI (20 ตาราง) · กล่องเขียว/แดง = ตารางของระบบเดิม",
        "ตาราง SBPGI และ workflow engine แสดง 'ทุกคอลัมน์' ตาม DDL/ฐานจริง",
        "ตารางแพลตฟอร์มที่กว้างมาก (สูงสุด 86 คอลัมน์) แสดงเฉพาะคอลัมน์ที่ SBPGI ใช้",
        "   แล้วบอกจำนวนที่เหลือไว้ท้ายกล่อง — ดูครบทุกคอลัมน์ได้ในไฟล์ .html",
        "ที่มา: LLDD/md/LLDD-Database.md §5 (DDL) · SBP/db-schema-sps_store.md",
        "   · SBP/db-schema-sps_auth.md (ดึงฐานจริง 07/08/2026) · database.md",
        "สร้างใหม่ด้วย: python3 tools/build_er_diagram.py",
    ]),
    ("กุญแจเชื่อมข้ามระบบ (Cross-System Keys)", [
        "1  impacted_stores.store_code = fgi_impact_stores.impacted_store_code (รหัส 5 หลัก)",
        "2  *.impact_process_id → fgi_impact_processes.id (hub ของหนึ่งรอบชดเชย)",
        "3  compensation_documents.impact_process_id → 1 รอบ : 1 เอกสาร (UNIQUE)",
        "4  workflow_transaction.reference_id → compensation_documents.id",
        "5  document_competitors.source_system = ALLMAP แยกจากที่ผู้ใช้เพิ่มเอง (USER)",
        "6  compensation_histories.submit_account_month → งวดที่ Job 6 ส่งไป STA (RabbitMQ)",
        "7  interface_transactions ใช้ typed FK 3 คอลัมน์แทน polymorphic key เดิม",
    ]),
]
