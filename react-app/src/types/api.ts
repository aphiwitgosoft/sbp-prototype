/** DTO ของ response — อิงรูปแบบใน api.md / plan-api.html */

export interface Paged<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}

export interface DashboardSummary {
  waitingTasks: number;
  storesThisMonth: number;
  compensationThisMonth: number;
  abnormalStores: number;
  monthly: { label: string; value: number }[];
  byStatus: { label: string; value: number; color: string }[];
}

export interface TaskRow {
  docNo: string;
  storeCode: string;
  storeName: string;
  region: string;
  impactMonth: string;
  status: string;
  currentSection: string;
  waitingDays: number;
  compensateAmount: number;
  salesDropPercent: number;
  round: number;
  type: string;
  created: string;
  red: boolean;
}

/** แถวรายงานสรุปสถานะ 19 คอลัมน์ (SRS 3.1.7) */
export interface ReportRow {
  store: string; storeName: string; region: string; type: string; month: string;
  transfer: string; period: string; newStore: string; newName: string; newRegion: string;
  newType: string; amount: number; status: string; officer: string; result: string;
  waitDays: number; round: number; created: string; docNo: string; red: boolean;
}

export interface DocumentDetail {
  docNo: string;
  status: string;
  currentSection: string;
  impactedStore: { storeCode: string; storeName: string; region: string; storeType: string };
  salesDropPercent: number;
  compensateAmount: number;
  newStores: { storeCode: string; storeName: string; compensatePercent: number; distanceKm: number }[];
  competitors: { competitorCode: string; competitorName: string; impactDate: string }[];
  factors: { factorCode: string; factorName: string }[];
  timeline: { section: string; considerName: string; result: string; actionDateTime: string }[];
}

export interface Operator {
  operatorAssignmentId: number;
  empName: string;
  empMail: string;
  sectionName: string;
  zoneCode: string;
}

export interface Factor {
  factorCode: string;
  factorName: string;
  factorRemark: string;
}

export interface ConfigItem {
  configKey: string;
  category: string;
  value: string;
  valueType: string;
  unit: string;
  description: string;
  isEditable: boolean;
}

export interface Job {
  jobNo: string;
  name: string;
  phase: string;
  cron: string;
  enabled: boolean;
  lastStatus: 'SUCCESS' | 'RUNNING' | 'FAILED' | 'WARN';
  lastRows: number;
  lastRunAt: string;
}

export interface JobDetail {
  jobNo: string;
  name: string;
  phase: string;
  cron: string;
  mainClass: string;
  desc: string;
  params: { key: string; value: string; editable: boolean }[];
  flow: string[];
  db: [string, 'R' | 'W' | 'R/W', string][];
  runs: { runId: number; status: string; rows: number; file: string; startedAt: string; durationSec: number }[];
}

export interface RoleRow {
  roleCode: string;
  roleName: string;
  roleDesc: string;
  isSystem: boolean;
}

export interface MenuPermissionRow {
  menuCode: string;
  menuName: string;
  group: string;
  access: Record<string, boolean>;
}

export interface EmailTemplate {
  templateCode: string;
  name: string;
  subject: string;
  body: string;
  variables: string[];
  to: string;
  cc: string;
  isCustomized: boolean;
}

export interface StoreLookup {
  storeCode: string;
  storeName: string;
  storeType: string;
}

export interface Competitor {
  competitorCode: string;
  competitorName: string;
}

export interface Lookup {
  code: string;
  name: string;
}

export interface AuditLog {
  tableName: string;
  actionType: 'ADD' | 'EDIT' | 'DELETE' | 'RESET';
  refKey: string;
  change: string;
  reason: string;
  updatedBy: string;
  updatedAt: string;
}
