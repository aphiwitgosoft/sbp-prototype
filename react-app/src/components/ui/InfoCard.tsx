import type { ReactNode } from 'react';
import { Info } from 'lucide-react';
import { Card } from './Card';

/** การ์ด callout ขอบซ้ายสีน้ำเงิน + ไอคอน (แทน InfoCallout/SrsConditionsCard ของ prototype) */
export function InfoCard({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <Card className="border-l-4 border-l-primary">
      <div className="flex gap-3">
        <Info size={20} className="mt-0.5 flex-none text-primary" />
        <div className="text-[13px] leading-relaxed text-slate-600">
          {title && <div className="mb-1 font-semibold text-ink">{title}</div>}
          {children}
        </div>
      </div>
    </Card>
  );
}
