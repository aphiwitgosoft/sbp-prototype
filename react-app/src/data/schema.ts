export type Zone = 'A' | 'B' | 'C';
export type Source = 'FGI/FCS' | 'K2' | 'ใหม่';

export interface TableDef {
  name: string;
  zone: Zone;
  source: Source;
  pk: string;
  fk: string;
  role: string;
}

/** Data Dictionary 34 ตาราง (พอร์ตจาก database.md / plan-database.html) */
export const TABLES: TableDef[] = [
  // Zone A · FGI/FCS
  { name: 'fgi_impact_stores', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'impact_process_id · impacted_store_code', role: 'คู่ร้านกระทบ–เปิดใหม่ · sales_request_status · allocation' },
  { name: 'fgi_impact_processes ★', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'impacted_store_code', role: 'hub รอบชดเชย · source of truth ของ workflow_generation_status' },
  { name: 'fgi_impact_sales_summaries', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'impact_process_id → sales_transactions', role: 'หัวยอดขาย · growth_rate_diff · total_working_days (60 วัน)' },
  { name: 'sales_transactions', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'sales_summary_id', role: 'ยอดขายรายวัน 4 หน้าต่าง × 15 วัน · sales_diff/outlier' },
  { name: 'fgi_impact_competitors', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'impact_process_id', role: 'คู่แข่งจาก ALLMAP (ALM) → document_competitors' },
  { name: 'fcs_qssi_scores', zone: 'A', source: 'FGI/FCS', pk: 'id', fk: 'UK: store+category+งวด', role: 'คะแนน QSSI 6 หมวด (8,9,12,1,10,16)' },
  { name: 'interface_transactions', zone: 'A', source: 'ใหม่', pk: 'id', fk: 'typed FK (impact_process/sales_summary/doc_no)', role: 'แทน FGI_CONFIRM_RECEIVE_DATA · purge ทำงานจริง' },
  // Zone B · K2
  { name: 'compensation_documents', zone: 'B', source: 'K2', pk: 'doc_no (YYYY/xxxxx)', fk: 'status_code · current_section_code · impact_process_id', role: 'เอกสารประกันรายได้ — หัวใจโซน B' },
  { name: 'document_new_stores', zone: 'B', source: 'K2', pk: 'id', fk: 'doc_no', role: 'ร้านเปิดใหม่ · distance_km · %ชดเชย (รวม 100%)' },
  { name: 'document_competitors', zone: 'B', source: 'K2', pk: 'id', fk: 'doc_no · competitor_code', role: 'คู่แข่งในเอกสาร · source_system ALLMAP/USER' },
  { name: 'document_external_factors', zone: 'B', source: 'K2', pk: 'id', fk: 'doc_no · factor_code', role: 'ปัจจัยภายนอกที่อ้างในเอกสาร' },
  { name: 'consideration_logs', zone: 'B', source: 'K2', pk: 'id', fk: 'doc_no', role: 'ประวัติพิจารณา + result_category (APPROVE/REJECT/PENDING)' },
  { name: 'document_attachments', zone: 'B', source: 'K2', pk: 'id', fk: 'doc_no', role: 'ไฟล์แนบ ≤ 5MB · แยกตาม Section' },
  { name: 'compensation_histories', zone: 'B', source: 'K2', pk: 'id', fk: 'store_code · ref_doc_no', role: 'ประวัติชดเชย · submit_account_month (→ FRBC0001)' },
  { name: 'workflow_instances', zone: 'B', source: 'ใหม่', pk: 'instance_id', fk: 'doc_no', role: 'instance workflow ภายใน (แทน K2 engine)' },
  { name: 'workflow_tasks', zone: 'B', source: 'ใหม่', pk: 'task_id', fk: 'instance_id · section_code · assignee', role: 'งานค้างต่อ Section (inbox)' },
  // Zone C · Shared
  { name: 'stores', zone: 'C', source: 'FGI/FCS', pk: 'store_code', fk: '← impacted_stores / new_store_code', role: 'master สาขา 7-Eleven ทุกประเภท' },
  { name: 'impacted_stores', zone: 'C', source: 'K2', pk: 'store_code', fk: '= impacted_store_code โซน A', role: 'ร้าน SP master (subset ของ stores)' },
  { name: 'employees', zone: 'C', source: 'FGI/FCS', pk: 'employee_id', fk: '← user_accounts / operator_assignments', role: 'master พนักงาน (HR)' },
  { name: 'workflow_sections / document_statuses', zone: 'C', source: 'K2', pk: 'section_code / status_code', fk: '← compensation_documents', role: 'ขั้นตอน 06/08/01/02/03 · สถานะ 06/08/01/02/03/99' },
  { name: 'roles / menus / menu_permissions', zone: 'C', source: 'K2', pk: 'composite', fk: 'menu_permissions = composite PK', role: 'สิทธิ์เมนู 8 role (00–10)' },
  { name: 'operator_assignments', zone: 'C', source: 'K2', pk: 'id', fk: 'section_code · zone_code · employee_id', role: 'ผู้ปฏิบัติงานต่อ section/zone' },
  { name: 'external_factors', zone: 'C', source: 'K2', pk: 'factor_code', fk: '← document_external_factors', role: 'ปัจจัยภายนอก master · รหัสห้ามซ้ำ' },
  { name: 'competitors', zone: 'C', source: 'K2', pk: 'competitor_code', fk: '← document_competitors', role: 'ร้านคู่แข่ง 24 ราย' },
  { name: 'audit_logs', zone: 'C', source: 'K2', pk: 'id', fk: 'table_name + ref_key', role: 'ประวัติแก้ master (MaintainMasterHistory)' },
  { name: 'status_email_rules', zone: 'C', source: 'K2', pk: 'status_code', fk: 'to/cc_section_code', role: 'ผู้รับอีเมล TO/CC ต่อสถานะ' },
  { name: 'email_templates', zone: 'C', source: 'ใหม่', pk: 'template_code (EM-01–08)', fk: 'คู่กับ status_email_rules', role: 'เนื้อหา 8 template (subject/body + ตัวแปร)' },
  { name: 'user_accounts', zone: 'C', source: 'ใหม่', pk: 'employee_id', fk: 'role_code', role: 'บัญชีผู้ใช้ + role สำหรับ JWT' },
  { name: 'job_configs / job_run_histories', zone: 'C', source: 'ใหม่', pk: 'job_no / run_id', fk: 'job_no', role: 'พารามิเตอร์ 11 jobs + ประวัติรัน' },
  { name: 'system_configs', zone: 'C', source: 'ใหม่', pk: 'config_key', fk: 'อ่านโดยทุก service', role: 'Global config key–value · is_editable' },
];

export const CROSS_KEYS: string[] = [
  'impacted_stores.store_code = fgi_impact_stores.impacted_store_code — สะพานโซน C ↔ A (รหัสร้าน 5 หลัก)',
  '*.impact_process_id → fgi_impact_processes.id — hub กลางของคู่ร้าน/ยอดขาย/คู่แข่ง (ใหม่)',
  'compensation_documents.impact_process_id → fgi_impact_processes — FK ใหม่ 1 รอบ : 1 เอกสาร (แทนไฟล์ BPM06001O)',
  'workflow_instances.doc_no → compensation_documents — เปิด instance เมื่อผ่าน Gen Flow Gate',
  'stores.store_code ← impacted_stores / document_new_stores.new_store_code — master สาขา 7-Eleven',
];
