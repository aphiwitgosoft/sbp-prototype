import type { PillKind } from '@/types';

/** 5 บทบาท workflow (section_code) — inbox ของแต่ละบทบาท = สถานะ "รอ<role>ดำเนินการ" */
export interface WorkflowRole {
  code: string;
  short: string;
  name: string;
  wait: string;
}

export const WORKFLOW_ROLES: WorkflowRole[] = [
  { code: '06', short: 'ฝ่าย SBP DSA', name: 'ฝ่าย SBP DSA (Manager Franchise · 06)', wait: 'รอฝ่าย SBP DSA ดำเนินการ' },
  { code: '08', short: 'จนท. SBP DSA', name: 'เจ้าหน้าที่ SBP DSA (Officer Franchise · 08)', wait: 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ' },
  { code: '01', short: 'ฝ่ายส่งเสริมธุรกิจฯ', name: 'ฝ่ายส่งเสริมธุรกิจฯ (Manager OPT · 01)', wait: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ' },
  { code: '02', short: 'GM OPT', name: 'GM ส่งเสริมธุรกิจฯ (GM OPT · 02)', wait: 'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ' },
  { code: '03', short: 'AVP OPT', name: 'ผู้บริหารสำนักบริหาร SBP (AVP OPT · 03)', wait: 'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ' },
];

/** 6 สถานะเอกสาร + สีของ pill */
export interface DocStatus {
  code: string;
  label: string;
  pill: PillKind;
}

export const DOC_STATUSES: DocStatus[] = [
  { code: '06', label: 'รอฝ่าย SBP DSA ดำเนินการ', pill: 'wait' },
  { code: '08', label: 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ', pill: 'violet' },
  { code: '01', label: 'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ', pill: 'info' },
  { code: '02', label: 'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ', pill: 'orange' },
  { code: '03', label: 'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', pill: 'navy' },
  { code: '99', label: 'เสร็จสิ้นดำเนินการ', pill: 'ok' },
];
