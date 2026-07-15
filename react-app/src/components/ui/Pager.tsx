import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/cn';

const SIZES = [10, 20, 50, 100];

/** แถบแบ่งหน้า — per-page select + info + prev/page/next (พอร์ตจาก Pager ใน k2-list) */
export function Pager({
  page,
  size,
  total,
  filteredFrom,
  onPage,
  onSize,
}: {
  page: number;
  size: number;
  total: number;
  /** จำนวนก่อนกรอง (แสดง "กรองจาก M") */
  filteredFrom?: number;
  onPage: (p: number) => void;
  onSize: (s: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / size));
  const from = total === 0 ? 0 : (page - 1) * size + 1;
  const to = Math.min(page * size, total);
  const nums = Array.from({ length: pages }, (_, i) => i + 1).filter((n) => n === 1 || n === pages || Math.abs(n - page) <= 1);

  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-[13px] text-slate-600">
      <div className="flex items-center gap-2">
        <select value={size} onChange={(e) => { onSize(Number(e.target.value)); onPage(1); }} className="rounded-lg border border-line px-2 py-1">
          {SIZES.map((s) => <option key={s} value={s}>{s} / หน้า</option>)}
        </select>
        <span className="text-muted">
          แสดง {from}–{to} จาก {total} รายการ{filteredFrom !== undefined && filteredFrom !== total ? ` (กรองจาก ${filteredFrom})` : ''}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button disabled={page <= 1} onClick={() => onPage(page - 1)} className="flex h-8 w-8 items-center justify-center rounded-lg border border-line disabled:opacity-40 hover:bg-slate-50"><ChevronLeft size={16} /></button>
        {nums.map((n, i) => (
          <span key={n} className="flex items-center">
            {i > 0 && nums[i - 1] !== n - 1 && <span className="px-1 text-slate-300">…</span>}
            <button onClick={() => onPage(n)} className={cn('h-8 min-w-8 rounded-lg border px-2 text-[13px]', n === page ? 'border-primary bg-primary text-white' : 'border-line hover:bg-slate-50')}>{n}</button>
          </span>
        ))}
        <button disabled={page >= pages} onClick={() => onPage(page + 1)} className="flex h-8 w-8 items-center justify-center rounded-lg border border-line disabled:opacity-40 hover:bg-slate-50"><ChevronRight size={16} /></button>
      </div>
    </div>
  );
}
