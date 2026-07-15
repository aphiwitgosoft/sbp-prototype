import {
  LayoutDashboard,
  FilePlus2,
  FileCheck2,
  ClipboardList,
  UserCog,
  ListTree,
  Lock,
  Settings,
  Timer,
  Mail,
  Workflow,
  Route,
  Database,
  Table2,
  Braces,
} from 'lucide-react';
import type { ModuleItem } from '@/types';
import { ROUTES } from '@/constants/routes';

/**
 * MODULES — registry เดียวที่ขับ sidebar + breadcrumb (พอร์ตจาก assets/sbp.js ~บรรทัด 52)
 * sidebar groups เรียงตามลำดับที่กลุ่มปรากฏครั้งแรก
 * child ที่ commented ไว้ (ข้อมูลผิดปกติ) คงสถานะเดิม — ไม่ใส่
 */
export const MODULES: ModuleItem[] = [
  { key: 'home', label: 'Overview', path: ROUTES.home, icon: LayoutDashboard, group: 'ระบบประกันรายได้' },
  { key: 'k2-create', label: 'สร้างเอกสาร', path: ROUTES.create, icon: FilePlus2, group: 'ระบบประกันรายได้' },
  {
    key: 'k2-docs',
    label: 'เอกสาร',
    icon: FileCheck2,
    group: 'ระบบประกันรายได้',
    children: [
      { key: 'k2-list-waiting', label: 'รอดำเนินการ', path: ROUTES.docsWaiting },
      { key: 'k2-list-related', label: 'ที่เกี่ยวข้อง', path: ROUTES.docsRelated },
      // { key: 'k2-list-abnormal', label: 'ข้อมูลผิดปกติ', path: '/documents/abnormal' }, // ปิดชั่วคราวรอตัดสินใจ
    ],
  },
  { key: 'k2-report', label: 'รายงานสรุปสถานะ', path: ROUTES.report, icon: ClipboardList, group: 'ระบบประกันรายได้' },
  { key: 'k2-operators', label: 'กำหนดผู้ปฏิบัติงาน', path: ROUTES.operators, icon: UserCog, group: 'ระบบประกันรายได้' },
  { key: 'k2-factors', label: 'กำหนดปัจจัยภายนอก', path: ROUTES.factors, icon: ListTree, group: 'ระบบประกันรายได้' },
  { key: 'k2-permissions', label: 'สิทธิ์การเข้าถึงเมนู', path: ROUTES.permissions, icon: Lock, group: 'ระบบประกันรายได้' },
  { key: 'system-config', label: 'ตั้งค่าระบบ (Config)', path: ROUTES.config, icon: Settings, group: 'ระบบประกันรายได้' },
  { key: 'job-batch', label: 'Batch Job', path: ROUTES.jobs, icon: Timer, group: 'ระบบประกันรายได้' },
  { key: 'plan-email', label: 'Email Template', path: ROUTES.emailTemplates, icon: Mail, group: 'ระบบประกันรายได้' },

  { key: 'flow-fgi', label: 'Flow FGI/FCS', path: ROUTES.flowFgi, icon: Workflow, group: 'Flow' },
  { key: 'k2-flow', label: 'Flow K2', path: ROUTES.flowK2, icon: Route, group: 'Flow' },
  { key: 'plan-flow', label: 'Flow FGI/FCS + K2', path: ROUTES.flowCombined, icon: Workflow, group: 'Flow' },

  { key: 'fgi-database', label: 'DB FGI/FCS', path: ROUTES.dbFgi, icon: Database, group: 'Database' },
  { key: 'k2-database', label: 'DB K2', path: ROUTES.dbK2, icon: Table2, group: 'Database' },
  { key: 'plan-database', label: 'DB FGI/FCS + K2', path: ROUTES.dbCombined, icon: Database, group: 'Database' },

  { key: 'plan-api', label: 'API', path: ROUTES.api, icon: Braces, group: 'Plan' },
];

/** หา module จาก path (รองรับ children) */
export function findModuleByPath(pathname: string): {
  parent?: ModuleItem;
  self?: ModuleItem;
  crumb: string;
} {
  for (const m of MODULES) {
    if (m.path === pathname) return { self: m, crumb: m.label };
    if (m.children) {
      const c = m.children.find((ch) => ch.path === pathname);
      if (c) return { parent: m, crumb: c.label };
    }
  }
  return { crumb: '' };
}
