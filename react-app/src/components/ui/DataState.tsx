import type { ReactNode } from 'react';
import { Loader2, AlertTriangle, Inbox } from 'lucide-react';

export function DataState({
  loading,
  error,
  empty,
  children,
}: {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  children: ReactNode;
}) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 py-10 text-muted">
        <Loader2 className="animate-spin" size={20} /> กำลังโหลดข้อมูล…
      </div>
    );
  }
  if (error) {
    return (
      <div className="flex items-start gap-3 rounded-card border border-red-200 bg-red-50 p-4 text-[13px] text-red-700">
        <AlertTriangle size={20} className="flex-none" />
        <div>
          <div className="font-medium">โหลดข้อมูลไม่ได้ ({error})</div>
          <div className="mt-0.5 text-red-600/80">
            ต้องรันด้วย <code className="rounded bg-red-100 px-1">npm run dev:mock</code> เพื่อเปิด mock API (MSW)
          </div>
        </div>
      </div>
    );
  }
  if (empty) {
    return (
      <div className="flex items-center gap-2 py-10 text-muted">
        <Inbox size={20} /> ไม่พบข้อมูล
      </div>
    );
  }
  return <>{children}</>;
}
