import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

export function Card({
  children,
  className,
  accent,
}: {
  children: ReactNode;
  className?: string;
  /** แถบซ้ายสีน้ำเงิน (border-left) แบบ prototype */
  accent?: boolean;
}) {
  return (
    <div className={cn('card', accent && 'border-l-4 border-l-primary', className)}>{children}</div>
  );
}

export function CardHead({
  title,
  right,
}: {
  title: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="card-head">
      <h2>{title}</h2>
      {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
    </div>
  );
}
