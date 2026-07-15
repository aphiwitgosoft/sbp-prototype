import type { PillKind } from '@/types';

/** map สถานะเอกสาร → สีของ .pill (ตามสีที่ใช้ทั้งระบบ) */
export const STATUS_PILL: Record<string, PillKind> = {
  'รอฝ่าย SBP DSA ดำเนินการ': 'wait',
  'รอเจ้าหน้าที่ SBP DSA ดำเนินการ': 'violet',
  'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ': 'info',
  'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ': 'orange',
  'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ': 'navy',
  'รอฝ่ายบัญชี SBP ดำเนินการ': 'teal',
  'รอบัญชีปฏิบัติการภาคดำเนินการ': 'muted',
  เสร็จสิ้นดำเนินการ: 'ok',
};

export function statusPill(status: string): PillKind {
  return STATUS_PILL[status] ?? 'muted';
}
