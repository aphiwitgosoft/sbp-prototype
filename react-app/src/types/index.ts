import type { LucideIcon } from 'lucide-react';

/** กลุ่มใน sidebar — เรียงตามลำดับที่ปรากฏครั้งแรกใน MODULES */
export type ModuleGroup = 'ระบบประกันรายได้' | 'Flow' | 'Database' | 'Plan';

export interface ModuleChild {
  key: string;
  label: string;
  path: string;
}

/** entry ใน MODULES registry (พอร์ตจาก sbp.js) */
export interface ModuleItem {
  key: string;
  label: string;
  /** path ของ route — เว้นว่างได้ถ้ามี children */
  path?: string;
  icon: LucideIcon;
  group: ModuleGroup;
  children?: ModuleChild[];
}

export type PillKind =
  | 'wait'
  | 'violet'
  | 'info'
  | 'orange'
  | 'navy'
  | 'teal'
  | 'muted'
  | 'ok'
  | 'fail';

export type ToastKind = '' | 'ok' | 'del';
