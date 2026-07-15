import { Card, CardHead } from './Card';
import { Chip } from './Pill';
import { DataState } from './DataState';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { cn } from '@/lib/cn';
import type { AuditLog } from '@/types/api';

const ACTION_STYLE: Record<AuditLog['actionType'], string> = {
  ADD: 'bg-green-100 text-green-700',
  EDIT: 'bg-blue-100 text-blue-700',
  DELETE: 'bg-red-100 text-red-700',
  RESET: 'bg-amber-100 text-amber-700',
};

/** ประวัติการแก้ไขข้อมูล master (audit_logs) — ตามหน้า prototype 3.1.8/3.1.9 */
export function AuditHistory({ table }: { table: string }) {
  const { data, loading, error } = useApi<{ items: AuditLog[] }>(EP.auditLogs, { table });
  const rows = data?.items ?? [];
  return (
    <Card className="mt-5">
      <CardHead title="ประวัติการแก้ไขข้อมูล" right={<Chip>audit_logs · {table}</Chip>} />
      <DataState loading={loading} error={error} empty={rows.length === 0}>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr><th>วันที่แก้ไข</th><th>ผู้แก้ไข</th><th>คำสั่ง</th><th>รายการ</th><th>ข้อมูลเดิม → ใหม่</th><th>เหตุผล</th></tr>
            </thead>
            <tbody>
              {rows.map((a, i) => (
                <tr key={i}>
                  <td className="num text-muted">{a.updatedAt}</td>
                  <td>{a.updatedBy}</td>
                  <td><span className={cn('rounded px-2 py-0.5 text-[11px] font-semibold', ACTION_STYLE[a.actionType])}>{a.actionType}</span></td>
                  <td className="num">{a.refKey}</td>
                  <td>{a.change}</td>
                  <td className="text-muted">{a.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </Card>
  );
}
