import { useState } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { DataState } from '@/components/ui/DataState';
import { AuditHistory } from '@/components/ui/AuditHistory';
import { InfoCard } from '@/components/ui/InfoCard';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { apiPost, apiPut, apiDelete } from '@/lib/api';
import type { Factor } from '@/types/api';

type Editing = { mode: 'add' | 'edit'; factor: Factor } | null;
const EMPTY: Factor = { factorCode: '', factorName: '', factorRemark: '' };

export default function K2Factors() {
  const { toast } = useToast();
  const { data, loading, error, refetch } = useApi<{ items: Factor[] }>(EP.factors);
  const rows = data?.items ?? [];
  const [editing, setEditing] = useState<Editing>(null);
  const [form, setForm] = useState<Factor>(EMPTY);
  const [busy, setBusy] = useState(false);

  function openAdd() {
    setForm({ ...EMPTY, factorCode: `F${String(rows.length + 1).padStart(3, '0')}` });
    setEditing({ mode: 'add', factor: EMPTY });
  }
  function openEdit(f: Factor) {
    setForm(f);
    setEditing({ mode: 'edit', factor: f });
  }
  async function save() {
    setBusy(true);
    try {
      if (editing?.mode === 'add') {
        await apiPost(EP.factors, form);
        toast('เพิ่มปัจจัยภายนอกแล้ว', 'ok');
      } else {
        await apiPut(EP.factor(form.factorCode), { factorName: form.factorName, factorRemark: form.factorRemark, reason: 'แก้ไขจากหน้าจอ' });
        toast('บันทึกการแก้ไขแล้ว', 'ok');
      }
      setEditing(null);
      refetch();
    } catch (e) {
      toast((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove(f: Factor) {
    if (!confirm(`ยืนยันการลบปัจจัย ${f.factorCode} ${f.factorName}?`)) return;
    try {
      await apiDelete(EP.factor(f.factorCode), { reason: 'ลบจากหน้าจอ' });
      toast('ลบรายการแล้ว', 'del');
      refetch();
    } catch (e) {
      toast((e as Error).message);
    }
  }

  return (
    <>
      <PageHead
        title="กำหนดปัจจัยภายนอก"
        sub="external_factors (SRS 3.1.9) · รหัสห้ามซ้ำ · แก้/ลบต้องระบุเหตุผล → audit_logs"
        actions={<Button onClick={openAdd}><Plus size={18} /> เพิ่มปัจจัย</Button>}
      />
      <Card>
        <CardHead title="ข้อมูลปัจจัยภายนอกทั้งหมด" />
        <DataState loading={loading} error={error} empty={rows.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr><th className="w-32">รหัสปัจจัย</th><th>ชื่อปัจจัย</th><th>รายละเอียดเพิ่มเติม</th><th className="w-28">Action</th></tr>
              </thead>
              <tbody>
                {rows.map((f) => (
                  <tr key={f.factorCode}>
                    <td className="num font-medium">{f.factorCode}</td>
                    <td>{f.factorName}</td>
                    <td className="text-muted">{f.factorRemark}</td>
                    <td>
                      <div className="flex gap-1">
                        <button className="rounded p-1 text-primary hover:bg-primary-soft" onClick={() => openEdit(f)}><Pencil size={16} /></button>
                        <button className="rounded p-1 text-danger hover:bg-red-50" onClick={() => remove(f)}><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>

      <AuditHistory table="external_factors" />

      <div className="mt-5">
        <InfoCard title="เงื่อนไขตาม SRS 3.1.9">
          รหัสปัจจัย (factor_code) ห้ามซ้ำ · แก้ไขได้เฉพาะชื่อปัจจัย + รายละเอียด และต้องระบุเหตุผล · ลบได้เมื่อไม่ถูกอ้างในเอกสารใด · ทุกการเปลี่ยนแปลงบันทึกที่ <code>audit_logs</code>
        </InfoCard>
      </div>

      <Modal
        open={!!editing}
        title={editing?.mode === 'add' ? 'เพิ่มปัจจัยภายนอก' : 'แก้ไขปัจจัยภายนอก'}
        sub="external_factors"
        onClose={() => setEditing(null)}
        footer={
          <>
            <Button variant="muted" size="sm" onClick={() => setEditing(null)}>ยกเลิก</Button>
            <Button size="sm" onClick={save} disabled={busy || !form.factorCode || !form.factorName}>บันทึก</Button>
          </>
        }
      >
        <div className="flex flex-col gap-3">
          <div className="field">
            <label>รหัสปัจจัย</label>
            <input value={form.factorCode} disabled={editing?.mode === 'edit'} onChange={(e) => setForm({ ...form, factorCode: e.target.value })} />
          </div>
          <div className="field">
            <label>ชื่อปัจจัย</label>
            <input value={form.factorName} onChange={(e) => setForm({ ...form, factorName: e.target.value })} />
          </div>
          <div className="field">
            <label>รายละเอียดเพิ่มเติม</label>
            <textarea rows={2} value={form.factorRemark} onChange={(e) => setForm({ ...form, factorRemark: e.target.value })} />
          </div>
        </div>
      </Modal>
    </>
  );
}
