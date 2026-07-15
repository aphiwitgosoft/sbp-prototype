import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';
import type { PillKind } from '@/types';

/** สถานะ (มีจุดนำ) — ใช้ class .pill จาก globals.css */
export function Pill({ kind, children }: { kind: PillKind; children: ReactNode }) {
  return <span className={cn('pill', kind)}>{children}</span>;
}

/** ป้ายข้อมูล (ไม่มีจุด) */
export function Chip({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={cn('chip', className)}>{children}</span>;
}
