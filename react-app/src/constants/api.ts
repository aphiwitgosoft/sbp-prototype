/**
 * ค่าคงที่ของ API path — แหล่งเดียวที่ประกาศเส้น REST /api/v1
 * - EP: path แบบ relative (ไม่มี /api/v1) สำหรับฝั่ง client (apiGet/useApi) — ตัวสร้าง dynamic ใช้ encode
 * - EP_PATTERN: path pattern (มี :param) สำหรับลงทะเบียน MSW handler
 * ทั้งสองอิง API_BASE เดียวกัน
 */
export const API_BASE = '/api/v1';

/** client paths (relative to API_BASE) */
export const EP = {
  login: '/auth/login',
  refresh: '/auth/refresh',
  me: '/auth/me',
  meMenus: '/me/menus',

  tasks: '/tasks',
  documents: '/documents',
  document: (docNo: string) => `/documents/${encodeURIComponent(docNo)}`,
  documentActions: (docNo: string) => `/documents/${encodeURIComponent(docNo)}/actions`,
  documentTimeline: (docNo: string) => `/documents/${encodeURIComponent(docNo)}/timeline`,
  documentAttachments: (docNo: string) => `/documents/${encodeURIComponent(docNo)}/attachments`,
  documentSales: (docNo: string) => `/documents/${encodeURIComponent(docNo)}/sales`,

  storesSearch: '/stores/search',
  competitors: '/competitors',
  documentStatuses: '/document-statuses',
  workflowSections: '/workflow-sections',

  operators: '/operators',
  operator: (id: number | string) => `/operators/${id}`,
  factors: '/factors',
  factor: (code: string) => `/factors/${code}`,
  employeesSearch: '/employees/search',
  menuPermissions: '/menu-permissions',
  menuPermission: (menuCode: string) => `/menu-permissions/${menuCode}`,
  roles: '/roles',
  role: (code: string) => `/roles/${code}`,
  menus: '/menus',
  menu: (code: string) => `/menus/${code}`,
  auditLogs: '/audit-logs',

  configs: '/configs',
  config: (key: string) => `/configs/${key}`,

  emailTemplates: '/email-templates',
  emailTemplate: (code: string) => `/email-templates/${code}`,
  emailTemplateReset: (code: string) => `/email-templates/${code}/reset`,
  emailResetAll: '/email-templates/reset-all',

  reportsStatusSummary: '/reports/status-summary',
  reportsExport: '/reports/status-summary/export',

  jobs: '/jobs',
  job: (no: string) => `/jobs/${no}`,
  jobParams: (no: string) => `/jobs/${no}/params`,
  jobRun: (no: string) => `/jobs/${no}/run`,
  jobEnabled: (no: string) => `/jobs/${no}/enabled`,
  jobRuns: (no: string) => `/jobs/${no}/runs`,

  workflowsInstances: '/workflows/instances',
  workflowInstance: (id: number | string) => `/workflows/instances/${id}`,
  workflowsSummary: '/workflows/summary',

  interfacesTracking: '/interfaces/tracking',
  interfacesStaAck: '/interfaces/sta/ack',
  interfacesPendingAck: '/interfaces/pending-ack',
  dashboardSummary: '/dashboard/summary',
} as const;

/** full path (มี API_BASE) — สะดวกใช้ใน apiCatalog แสดงผล */
export const fullPath = (p: string) => `${API_BASE}${p}`;

/** MSW handler patterns (:param) — ลงทะเบียน worker */
export const EP_PATTERN = {
  login: `${API_BASE}/auth/login`,
  refresh: `${API_BASE}/auth/refresh`,
  me: `${API_BASE}/auth/me`,
  meMenus: `${API_BASE}/me/menus`,
  tasks: `${API_BASE}/tasks`,
  documents: `${API_BASE}/documents`,
  document: `${API_BASE}/documents/:docNo`,
  documentSales: `${API_BASE}/documents/:docNo/sales`,
  storesSearch: `${API_BASE}/stores/search`,
  competitors: `${API_BASE}/competitors`,
  documentStatuses: `${API_BASE}/document-statuses`,
  workflowSections: `${API_BASE}/workflow-sections`,
  operators: `${API_BASE}/operators`,
  operator: `${API_BASE}/operators/:id`,
  factors: `${API_BASE}/factors`,
  factor: `${API_BASE}/factors/:code`,
  menuPermissions: `${API_BASE}/menu-permissions`,
  roles: `${API_BASE}/roles`,
  configs: `${API_BASE}/configs`,
  config: `${API_BASE}/configs/:key`,
  emailTemplates: `${API_BASE}/email-templates`,
  emailTemplate: `${API_BASE}/email-templates/:code`,
  emailTemplateReset: `${API_BASE}/email-templates/:code/reset`,
  reportsStatusSummary: `${API_BASE}/reports/status-summary`,
  jobs: `${API_BASE}/jobs`,
  dashboardSummary: `${API_BASE}/dashboard/summary`,
} as const;
