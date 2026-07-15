import { useState } from 'react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { DataState } from '@/components/ui/DataState';
import { AuditHistory } from '@/components/ui/AuditHistory';
import { InfoCard } from '@/components/ui/InfoCard';
import { DonutChart } from '@/components/charts/DonutChart';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { apiPut } from '@/lib/api';
import type { ConfigItem } from '@/types/api';

const CAT_COLOR: Record<string, string> = {
  IMPACT: '#2f6fed', WORKFLOW: '#7c3aed', DOCUMENT: '#0f9f90',
  AUTH: '#f59e0b', NOTIFICATION: '#ef4444', BATCH: '#64748b',
};

export default function SystemConfig() {
  const { toast } = useToast();
  const { data, loading, error, refetch } = useApi<{ items: ConfigItem[] }>(EP.configs);
  const rows = data?.items ?? [];
  const [editing, setEditing] = useState<ConfigItem | null>(null);
  const [value, setValue] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [cat, setCat] = useState('');

  const byCat = Object.entries(
    rows.reduce<Record<string, number>>((acc, c) => { acc[c.category] = (acc[c.category] ?? 0) + 1; return acc; }, {}),
  );
  const CATS = ['IMPACT', 'WORKFLOW', 'DOCUMENT', 'AUTH', 'NOTIFICATION', 'BATCH'];
  const shown = cat ? rows.filter((c) => c.category === cat) : rows;

  function open(c: ConfigItem) { setEditing(c); setValue(c.value); setReason(''); }
  async function save() {
    if (!editing) return;
    setBusy(true);
    try {
      await apiPut(EP.config(editing.configKey), { value, reason });
      toast('บันทึกค่ากำหนดแล้ว', 'ok');
      setEditing(null);
      refetch();
    } catch (e) {
      toast((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="ตั้งค่าระบบ (Global Config)" sub="ค่ากำหนดกลาง key–value · system_configs · cache 5 นาที" />

      {rows.length > 0 && (
        <Card className="mb-5">
          <CardHead title="สัดส่วนค่ากำหนดตามหมวดหมู่" right={<Chip>{rows.length} รายการ</Chip>} />
          <div className="flex flex-wrap items-center gap-7">
            <DonutChart values={byCat.map(([, n]) => n)} colors={byCat.map(([c]) => CAT_COLOR[c] ?? '#94a3b8')} center="Configs" />
            <div className="grid grid-cols-2 gap-x-8 gap-y-2.5 text-[12.5px] text-slate-600">
              {byCat.map(([c, n]) => (
                <span key={c} className="flex items-center gap-2">
                  <i className="inline-block h-3 w-3 rounded-[3px]" style={{ background: CAT_COLOR[c] ?? '#94a3b8' }} />
                  {c} <b className="ml-auto text-ink">{n}</b>
                </span>
              ))}
            </div>
          </div>
        </Card>
      )}

      <Card>
        <CardHead
          title="ค่ากำหนดทั้งหมด"
          right={
            <div className="flex items-center gap-2">
              <select value={cat} onChange={(e) => setCat(e.target.value)} className="rounded-lg border border-line px-2.5 py-1.5 text-[13px]">
                <option value="">ทุกหมวดหมู่</option>
                {CATS.map((c) => <option key={c}>{c}</option>)}
              </select>
              <button onClick={() => toast('Invalidate cache ทุก service แล้ว', 'ok')} className="rounded-lg border border-line px-2.5 py-1.5 text-[13px] hover:bg-slate-50">Invalidate Cache</button>
            </div>
          }
        />
        <DataState loading={loading} error={error} empty={shown.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr><th>Config Key</th><th>หมวดหมู่</th><th>ค่า (Value)</th><th>ชนิด</th><th>หน่วย</th><th>คำอธิบาย</th><th>แก้ไขได้</th></tr>
              </thead>
              <tbody>
                {shown.map((c) => (
                  <tr key={c.configKey}>
                    <td className="num">{c.configKey}</td>
                    <td><span className="rounded px-2 py-0.5 text-[11px] font-semibold text-white" style={{ background: CAT_COLOR[c.category] ?? '#94a3b8' }}>{c.category}</span></td>
                    <td className="num">{c.value}</td>
                    <td className="text-muted">{c.valueType}</td>
                    <td className="text-muted">{c.unit || '-'}</td>
                    <td className="text-muted">{c.description}</td>
                    <td>
                      {c.isEditable ? (
                        <button className="text-primary hover:underline" onClick={() => open(c)}>แก้ไข</button>
                      ) : (
                        <span className="text-[12px] text-slate-400">ค่าคงที่ธุรกิจ (ข้อ 8.2)</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>

      <AuditHistory table="system_configs" />

      <div className="mt-5">
        <InfoCard title="ข้อควรทราบ">
          Config Key เป็น dot notation (เช่น <code>impact.radius_bkk_km</code>) · service cache 5 นาที + invalidate เมื่อแก้ไข · <code>is_editable=false</code> = ค่าคงที่ทางธุรกิจ (รัศมี · วงเงิน 100,000 · เกณฑ์ 60 วัน ตามข้อ 8.2) แก้ผ่าน UI/API ไม่ได้ · ห้ามเก็บ secret (อยู่ Secret Manager)
        </InfoCard>
      </div>

      <Modal
        open={!!editing}
        title="แก้ไขค่ากำหนด"
        sub={editing?.configKey}
        onClose={() => setEditing(null)}
        footer={
          <>
            <Button variant="muted" size="sm" onClick={() => setEditing(null)}>ยกเลิก</Button>
            <Button size="sm" onClick={save} disabled={busy || !reason}>บันทึก</Button>
          </>
        }
      >
        {editing && (
          <div className="flex flex-col gap-3">
            <p className="text-[13px] text-muted">{editing.description}</p>
            <div className="field"><label>ค่า ({editing.valueType}{editing.unit ? ` · ${editing.unit}` : ''})</label><input value={value} onChange={(e) => setValue(e.target.value)} className="num" /></div>
            <div className="field"><label>เหตุผลการแก้ไข (บังคับ → audit_logs)</label><input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="ระบุเหตุผล..." /></div>
          </div>
        )}
      </Modal>
    </>
  );
}
