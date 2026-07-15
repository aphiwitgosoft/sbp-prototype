/**
 * ค่าคงที่ของเส้นทาง (route / link path) — แหล่งเดียวที่ประกาศ path ของหน้า
 * ใช้ร่วมกันโดย router (App.tsx), sidebar (modules.ts) และลิงก์ทุกจุด
 */
export const ROUTES = {
  home: '/',
  create: '/create',
  docsWaiting: '/documents/waiting',
  docsRelated: '/documents/related',
  /** รายละเอียดเอกสาร — docNo อาจมี '/' จึง encode */
  document: (docNo: string) => `/documents/${encodeURIComponent(docNo)}`,
  documentPattern: '/documents/:docNo',
  report: '/report',
  operators: '/operators',
  factors: '/factors',
  permissions: '/permissions',
  config: '/config',
  jobs: '/jobs',
  emailTemplates: '/email-templates',
  flowFgi: '/flow/fgi',
  flowK2: '/flow/k2',
  flowCombined: '/flow/combined',
  dbFgi: '/db/fgi',
  dbK2: '/db/k2',
  dbCombined: '/db/combined',
  api: '/api',
  notFound: '*',
} as const;
