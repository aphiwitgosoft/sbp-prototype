export type ApiRef = 'fgi' | 'k2' | 'new' | 'mix';

export interface ApiEndpoint {
  m: 'GET' | 'POST' | 'PUT' | 'DELETE';
  p: string;
  ref: ApiRef;
  refT: string;
  roles?: string;
  sum: string;
  flow?: string[];
  db?: [string, 'R' | 'W' | 'R/W', string][];
  req?: string;
  res?: string;
  err?: string[];
  sql?: string;
}

export interface ApiGroup {
  name: string;
  eps: ApiEndpoint[];
}

import { API_BASE } from '@/constants/api';

const B = API_BASE;

/** catalog ย่อจาก plan-api.html (รายละเอียดเต็มดู api.md) — เน้น endpoint สำคัญ + 4 เส้นที่มี Flowchart */
export const API_GROUPS: ApiGroup[] = [
  {
    name: '1 · Auth & สิทธิ์ผู้ใช้',
    eps: [
      { m: 'POST', p: `${B}/auth/login`, ref: 'k2', refT: 'K2 · 3.1.1', roles: 'public', sum: 'login แลก JWT + role/section',
        db: [['user_accounts', 'R', 'บัญชีผู้ใช้ + role'], ['roles', 'R', 'ชื่อ role 00–10']],
        req: '{ "username": "phatcharida.p", "password": "********" }',
        res: '{ "accessToken": "...", "user": { "roles": ["03"], "sectionCode": "06" } }',
        err: ['401 — ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', '423 — บัญชีถูกล็อก'],
        sql: '-- credential ตรวจโดย platform SSO/AD/LDAP; SBPGI ไม่เก็บ password_hash\nSELECT u.employee_id, u.role_code, u.section_code\nFROM user_accounts u JOIN roles r ON r.role_code = u.role_code\nWHERE u.employee_id = :employeeIdFromPlatform AND u.is_active = TRUE;' },
      { m: 'POST', p: `${B}/auth/refresh`, ref: 'new', refT: 'ใหม่', sum: 'ต่ออายุ accessToken' },
      { m: 'GET', p: `${B}/auth/me`, ref: 'k2', refT: 'K2', sum: 'ข้อมูลผู้ใช้ปัจจุบันจาก JWT' },
      { m: 'GET', p: `${B}/me/menus`, ref: 'k2', refT: 'K2 · 3.1.1', sum: 'เมนูที่ role เข้าถึงได้ (สร้าง sidebar)' },
    ],
  },
  {
    name: '2 · งาน & เอกสารประกันรายได้',
    eps: [
      { m: 'GET', p: `${B}/tasks`, ref: 'k2', refT: 'K2 · 3.1.2', sum: 'inbox งานค้างที่ section ของผู้ใช้',
        db: [['workflow_tasks', 'R', 'งานค้างต่อ section'], ['compensation_documents', 'R', 'ข้อมูลเอกสาร']],
        req: 'Query: ?q=00788&page=1&size=20',
        sql: 'SELECT t.doc_no, d.status_code, s.store_name\nFROM workflow_tasks t\nJOIN compensation_documents d ON d.doc_no = t.doc_no\nJOIN stores s ON s.store_code = d.impacted_store_code\nWHERE t.section_code = :section AND t.task_status = :open;' },
      { m: 'GET', p: `${B}/documents`, ref: 'k2', refT: 'K2 · 3.1.3', sum: 'ค้นหาเอกสาร — บังคับระบุปี',
        err: ['400 — กรุณาระบุปีที่ต้องการค้นหา'] },
      { m: 'GET', p: `${B}/documents/{docNo}`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'เอกสารฉบับเต็ม 12 ส่วน + ธงสิทธิ์แก้' },
      { m: 'POST', p: `${B}/documents`, ref: 'k2', refT: 'K2 · 3.1.6', roles: '02/03', sum: 'สร้างเอกสาร + เปิด workflow (มี Flowchart)',
        db: [['compensation_documents', 'W', 'เอกสารใหม่'], ['workflow_instances / workflow_tasks', 'W', 'เปิด workflow']],
        req: '{ "impactedStoreCode": "00788", "impactMonth": "2026-06", "source": "MANUAL" }',
        res: '201 { "docNo": "2569/00124" }',
        err: ['409 — ร้าน/เดือนนี้มีเอกสารแล้ว', '422 — ข้อมูลบังคับไม่ครบ'],
        sql: 'INSERT INTO compensation_documents (doc_no, impacted_store_code, impact_month, status_code, current_section_code)\nVALUES (:docNo, :store, :month, :init, :s06);' },
      { m: 'PUT', p: `${B}/documents/{docNo}`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'บันทึกส่วนย่อย · %ชดเชยรวม = 100%',
        err: ['422 — "%ชดเชย … รวมกันแล้วไม่เท่ากับ 100%"'] },
      { m: 'POST', p: `${B}/documents/{docNo}/actions`, ref: 'k2', refT: 'K2 · 3.1.4', roles: 'เจ้าของ task', sum: 'ส่งผลพิจารณา — workflow 5 ขั้น · กฎ 100,000 (มี Flowchart)',
        db: [['workflow_tasks', 'R/W', 'ปิดงานเดิม เปิดงานถัดไป'], ['consideration_logs', 'W', 'บันทึกผล'], ['compensation_documents', 'W', 'อัปเดตสถานะ']],
        req: '{ "action": "COMPENSATE", "comment": "เห็นควรชดเชย" }',
        res: '{ "nextSection": "02", "status": "รอ GM ..." }',
        err: ['422 — "ท่านยังไม่เลือกผลการพิจารณา…"', '403 — ไม่ใช่เจ้าของงาน', '409 — ถูกดำเนินการไปแล้ว'],
        sql: 'UPDATE workflow_tasks SET task_status = :closed WHERE doc_no = :docNo AND task_status = :open;\nINSERT INTO consideration_logs (doc_no, section_code, result, consider_by, action_datetime) VALUES (:docNo, :cur, :result, :empId, :now);\nUPDATE compensation_documents SET status_code = :next, version_no = version_no + 1 WHERE doc_no = :docNo AND version_no = :versionNo;' },
      { m: 'GET', p: `${B}/documents/{docNo}/timeline`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'ประวัติพิจารณาทุกขั้น' },
      { m: 'POST', p: `${B}/documents/{docNo}/attachments`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'แนบไฟล์ ≤ 5MB', err: ['413 — ไฟล์เกิน 5MB'] },
      { m: 'GET', p: `${B}/documents/{docNo}/attachments/{attachId}/download`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'ดาวน์โหลดไฟล์แนบที่ scan_status=CLEAN และเป็นของเอกสาร' },
      { m: 'GET', p: `${B}/documents/{docNo}/sales`, ref: 'k2', refT: 'K2 · 3.1.6', sum: 'ยอดขาย 4 หน้าต่าง × 15 วัน (กราฟ ก่อน/หลัง)',
        db: [['fgi_impact_sales_summaries', 'R', 'หัวยอดขาย'], ['sales_transactions', 'R', 'ยอดขายรายวัน']] },
    ],
  },
  {
    name: '3 · ข้อมูลอ้างอิง (Lookup)',
    eps: [
      { m: 'GET', p: `${B}/stores/search`, ref: 'mix', refT: 'FGI/FCS + K2', sum: 'ค้นหาร้าน (impacted/new) — แว่นขยายใน k2-create',
        req: 'Query: ?q=00788&type=impacted' },
      { m: 'GET', p: `${B}/competitors`, ref: 'k2', refT: 'K2', sum: 'master คู่แข่ง — dropdown เพิ่มคู่แข่ง' },
      { m: 'GET', p: `${B}/document-statuses`, ref: 'k2', refT: 'K2', sum: 'รายการสถานะ — dropdown ตัวกรอง' },
      { m: 'GET', p: `${B}/workflow-sections`, ref: 'k2', refT: 'K2', sum: 'รายการ Section 5 ขั้น' },
    ],
  },
  {
    name: '4 · Master Data',
    eps: [
      { m: 'GET', p: `${B}/operators`, ref: 'k2', refT: 'K2 · 3.1.8', sum: 'ผู้ปฏิบัติงาน (CRUD)' },
      { m: 'POST', p: `${B}/operators`, ref: 'k2', refT: 'K2 · 3.1.8', sum: 'เพิ่มผู้ปฏิบัติงาน → audit_logs' },
      { m: 'PUT', p: `${B}/operators/{id}`, ref: 'k2', refT: 'K2 · 3.1.8', sum: 'แก้ไข (ต้องระบุ reason)' },
      { m: 'DELETE', p: `${B}/operators/{id}`, ref: 'k2', refT: 'K2 · 3.1.8', sum: 'ลบ (ต้องระบุ reason)' },
      { m: 'GET', p: `${B}/factors`, ref: 'k2', refT: 'K2 · 3.1.9', sum: 'ปัจจัยภายนอก (list)' },
      { m: 'POST', p: `${B}/factors`, ref: 'k2', refT: 'K2 · 3.1.9', sum: 'เพิ่มปัจจัย — รหัสห้ามซ้ำ', err: ['409 — รหัสปัจจัยนี้มีอยู่แล้ว'] },
      { m: 'PUT', p: `${B}/factors/{code}`, ref: 'k2', refT: 'K2 · 3.1.9', sum: 'แก้ไขปัจจัย (ต้องระบุ reason)' },
      { m: 'DELETE', p: `${B}/factors/{code}`, ref: 'k2', refT: 'K2 · 3.1.9', sum: 'ลบปัจจัย (ต้องไม่ถูกใช้ในเอกสาร)' },
      { m: 'GET', p: `${B}/employees/search`, ref: 'mix', refT: 'K2 3.1.8 + master', sum: 'ค้นหาพนักงานจาก HR (popup)' },
      { m: 'GET', p: `${B}/menu-permissions`, ref: 'k2', refT: 'K2 · 3.1.1', sum: 'matrix สิทธิ์เมนู 8 role' },
      { m: 'PUT', p: `${B}/menu-permissions/{menuCode}`, ref: 'k2', refT: 'K2 · 3.1.1', sum: 'แก้สิทธิ์เมนูต่อ role → audit_logs' },
      { m: 'GET', p: `${B}/roles`, ref: 'k2', refT: 'K2 · 3.1.1', sum: 'รายการ Role' },
      { m: 'POST', p: `${B}/roles`, ref: 'new', refT: 'ใหม่', sum: 'เพิ่ม Role — สิทธิ์เริ่มต้น false ทุกเมนู' },
      { m: 'PUT', p: `${B}/roles/{roleCode}`, ref: 'new', refT: 'ใหม่', sum: 'แก้ชื่อ/คำอธิบาย Role' },
      { m: 'DELETE', p: `${B}/roles/{roleCode}`, ref: 'new', refT: 'ใหม่', sum: 'ลบ Role — role ระบบลบไม่ได้' },
      { m: 'POST', p: `${B}/menus`, ref: 'new', refT: 'ใหม่', sum: 'เพิ่มเมนู — สิทธิ์เริ่มต้น false ทุก role' },
      { m: 'PUT', p: `${B}/menus/{menuCode}`, ref: 'new', refT: 'ใหม่', sum: 'แก้ชื่อ/กลุ่ม/ลำดับเมนู' },
      { m: 'DELETE', p: `${B}/menus/{menuCode}`, ref: 'new', refT: 'ใหม่', sum: 'ลบเมนู (cascade สิทธิ์)' },
      { m: 'GET', p: `${B}/audit-logs`, ref: 'k2', refT: 'K2', sum: 'ประวัติแก้ master (MaintainMasterHistory)' },
    ],
  },
  {
    name: '5 · System Config',
    eps: [
      { m: 'GET', p: `${B}/configs`, ref: 'new', refT: 'ใหม่', sum: 'ค่ากำหนดกลาง (list · cache 5 นาที)' },
      { m: 'GET', p: `${B}/configs/{key}`, ref: 'new', refT: 'ใหม่', sum: 'อ่านค่ารายตัว (typed value + cache TTL)' },
      { m: 'POST', p: `${B}/configs`, ref: 'new', refT: 'ใหม่', sum: 'เพิ่มค่า — key ห้ามซ้ำ · ห้ามเก็บ secret' },
      { m: 'PUT', p: `${B}/configs/{key}`, ref: 'new', refT: 'ใหม่', sum: 'แก้ค่า — is_editable=false แก้ไม่ได้ (ข้อ 8.2)',
        err: ['422 — ค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้'] },
      { m: 'DELETE', p: `${B}/configs/{key}`, ref: 'new', refT: 'ใหม่', sum: 'ลบค่า — ค่าระบบลบไม่ได้' },
    ],
  },
  {
    name: '6 · Email Template',
    eps: [
      { m: 'GET', p: `${B}/email-templates`, ref: 'new', refT: 'ใหม่', sum: '8 template (EM-01–08)' },
      { m: 'GET', p: `${B}/email-templates/{code}`, ref: 'new', refT: 'ใหม่', sum: 'อ่าน template รายตัว + ตัวแปร merge' },
      { m: 'PUT', p: `${B}/email-templates/{code}`, ref: 'new', refT: 'ใหม่', sum: 'แก้ subject/body — From/To/Cc ล็อก' },
      { m: 'POST', p: `${B}/email-templates/{code}/reset`, ref: 'new', refT: 'ใหม่', sum: 'รีเซ็ต template รายตัวเป็น Default' },
      { m: 'POST', p: `${B}/email-templates/reset-all`, ref: 'new', refT: 'ใหม่', sum: 'รีเซ็ตทั้งหมดเป็น Default' },
    ],
  },
  {
    name: '7 · รายงาน',
    eps: [
      { m: 'GET', p: `${B}/reports/status-summary`, ref: 'k2', refT: 'K2 · 3.1.7', sum: 'รายงาน 19 คอลัมน์ · filter result อนุมัติ/ไม่อนุมัติ',
        db: [['compensation_documents', 'R', 'สถานะ'], ['consideration_logs', 'R', 'ผลพิจารณาล่าสุด']],
        req: 'Query: ?year=2569&result=APPROVE',
        sql: 'SELECT d.doc_no, d.status_code, cl.result_category\nFROM compensation_documents d\nLEFT JOIN LATERAL (SELECT result_category FROM consideration_logs WHERE doc_no = d.doc_no ORDER BY action_datetime DESC LIMIT 1) cl ON TRUE\nWHERE d.doc_year = :year AND (:result IS NULL OR cl.result_category = :result);' },
      { m: 'GET', p: `${B}/reports/status-summary/export`, ref: 'k2', refT: 'K2 · 3.1.7', sum: 'Export .xlsx' },
    ],
  },
  {
    name: '8 · Batch Job Admin',
    eps: [
      { m: 'GET', p: `${B}/jobs`, ref: 'fgi', refT: 'FGI/FCS', sum: 'รายการ 11 entry points + สถานะรอบล่าสุด' },
      { m: 'GET', p: `${B}/jobs/{jobNo}`, ref: 'fgi', refT: 'FGI/FCS', sum: 'รายละเอียด job + พารามิเตอร์ (แก้ได้/คงที่)' },
      { m: 'PUT', p: `${B}/jobs/{jobNo}/params`, ref: 'fgi', refT: 'FGI/FCS + ข้อ 8.2', sum: 'แก้พารามิเตอร์ (editable เท่านั้น)' },
      { m: 'POST', p: `${B}/jobs/{jobNo}/run`, ref: 'fgi', refT: 'FGI/FCS · Runbook 7.1', roles: '01 Admin', sum: 'สั่งรันนอกรอบ — guard กันรันซ้อน (มี Flowchart)',
        db: [['job_run_histories', 'W', 'รอบใหม่ RUNNING'], ['job_configs', 'R', 'ตรวจ enabled']],
        req: '{ "period": "2026-07" }',
        res: '202 { "runId": 4451 }',
        err: ['409 — Job กำลังรันอยู่ ห้ามรันซ้อน', '422 — job ถูกปิดใช้งาน'] },
      { m: 'PUT', p: `${B}/jobs/{jobNo}/enabled`, ref: 'fgi', refT: 'FGI/FCS', sum: 'เปิด/ปิด job' },
      { m: 'GET', p: `${B}/jobs/{jobNo}/runs`, ref: 'fgi', refT: 'FGI/FCS', sum: 'ประวัติการรัน' },
    ],
  },
  {
    name: '9 · Workflow ภายใน',
    eps: [
      { m: 'POST', p: `${B}/workflows/instances`, ref: 'mix', refT: 'แทน K2 StartInstance (Job 8b)', roles: 'service token', sum: 'เปิด workflow — Gen Flow Gate (มี Flowchart)',
        db: [['fgi_impact_stores', 'R/W', 'ตรวจ gate + อัปเดตสถานะ W→Y/N'], ['workflow_instances / workflow_tasks', 'W', 'เปิด instance + งานแรก']],
        req: '{ "impactProcessId": 88123 }',
        res: '201 { "instanceId": 501, "flagGenFlow": "Y" }',
        err: ['422 — ไม่ผ่าน Gen Flow Gate', '401 — service token ไม่ถูกต้อง'] },
      { m: 'GET', p: `${B}/workflows/instances/{id}`, ref: 'new', refT: 'ใหม่', sum: 'สถานะ instance + งานขั้นปัจจุบัน (debug)' },
      { m: 'GET', p: `${B}/workflows/summary`, ref: 'fgi', refT: 'FGI/FCS · 7.4', sum: 'นับ W/Y/N + งานค้างต่อ section' },
    ],
  },
  {
    name: '10 · Interface & Dashboard',
    eps: [
      { m: 'GET', p: `${B}/interfaces/tracking`, ref: 'fgi', refT: 'FGI/FCS', sum: 'สถานะรับ–ส่งไฟล์ (interface_transactions)' },
      { m: 'GET', p: `${B}/interfaces/pending-ack`, ref: 'fgi', refT: 'FGI/FCS · Job 10', sum: 'ACK ค้าง ≥ 1 วัน' },
      { m: 'POST', p: `${B}/interfaces/sta/ack`, ref: 'new', refT: 'ใหม่', sum: 'callback ให้ STA ยิง ACK (API key)' },
      { m: 'GET', p: `${B}/dashboard/summary`, ref: 'k2', refT: 'K2', sum: 'ตัวเลขหน้า Dashboard (cache 5 นาที)' },
    ],
  },
];

export const REF_STYLE: Record<ApiRef, { bg: string; text: string }> = {
  fgi: { bg: '#e8f0fe', text: '#1d4ed8' },
  k2: { bg: '#f1ecfe', text: '#6d28d9' },
  new: { bg: '#e7f7ee', text: '#15803d' },
  mix: { bg: '#fff4d6', text: '#92670b' },
};
