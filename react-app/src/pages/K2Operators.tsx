import { useState } from 'react';
import { Search, UserPlus, Pencil, Trash2 } from 'lucide-react';
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
import type { Operator, Paged } from '@/types/api';

const SECTIONS = ['ฝ่าย SBP DSA', 'เจ้าหน้าที่ SBP DSA', 'ส่งเสริมธุรกิจพันธมิตรฯ', 'GM ส่งเสริมธุรกิจฯ', 'ผู้บริหารสำนักบริหาร SBP (AVP)', 'ฝ่ายบัญชี SBP', 'บัญชีปฏิบัติการภาค'];
const ZONES = ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS', '-'];
const EMPTY: Operator = { operatorAssignmentId: 0, empName: '', empMail: '', sectionName: SECTIONS[0], zoneCode: '-' };

export default function K2Operators() {
  const [q, setQ] = useState('');
  const { toast } = useToast();
  const { data, loading, error, refetch } = useApi<Paged<Operator>>(EP.operators, { q, size: 50 });
  const rows = data?.items ?? [];
  const [editing, setEditing] = useState<'add' | 'edit' | null>(null);
  const [form, setForm] = useState<Operator>(EMPTY);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      if (editing === 'add') {
        await apiPost(EP.operators, form);
        toast('เพิ่มผู้ปฏิบัติงานแล้ว', 'ok');
      } else {
        await apiPut(EP.operator(form.operatorAssignmentId), { ...form, reason: 'แก้ไขจากหน้าจอ' });
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
  async function remove(o: Operator) {
    if (!confirm(`ยืนยันการลบ ${o.empName}?`)) return;
    try {
      await apiDelete(EP.operator(o.operatorAssignmentId), { reason: 'ลบจากหน้าจอ' });
      toast('ลบรายการแล้ว', 'del');
      refetch();
    } catch (e) {
      toast((e as Error).message);
    }
  }

  return (
    <>
      <PageHead
        title="กำหนดชื่อผู้ปฏิบัติงาน"
        sub="operator_assignments (SRS 3.1.8) · แก้/ลบต้องระบุเหตุผล → audit_logs"
        actions={<Button onClick={() => { setForm(EMPTY); setEditing('add'); }}><UserPlus size={18} /> เพิ่มผู้ปฏิบัติงาน</Button>}
      />
      <Card>
        <CardHead
          title="รายชื่อผู้ปฏิบัติงานในแต่ละตำแหน่ง"
          right={
            <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-1.5">
              <Search size={16} className="text-slate-400" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="ค้นหาชื่อ / อีเมล / ตำแหน่ง" className="w-56 text-[13px] outline-none" />
            </div>
          }
        />
        <DataState loading={loading} error={error} empty={rows.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr><th>ชื่อผู้ปฏิบัติงาน</th><th>E-Mail</th><th>ชื่อตำแหน่ง</th><th>ภาค</th><th className="w-28">Action</th></tr>
              </thead>
              <tbody>
                {rows.map((o) => (
                  <tr key={o.operatorAssignmentId}>
                    <td>{o.empName}</td>
                    <td className="num">{o.empMail}</td>
                    <td>{o.sectionName}</td>
                    <td>{o.zoneCode}</td>
                    <td>
                      <div className="flex gap-1">
                        <button className="rounded p-1 text-primary hover:bg-primary-soft" onClick={() => { setForm(o); setEditing('edit'); }}><Pencil size={16} /></button>
                        <button className="rounded p-1 text-danger hover:bg-red-50" onClick={() => remove(o)}><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>

      <AuditHistory table="operator_assignments" />

      <div className="mt-5">
        <InfoCard title="เงื่อนไขตาม SRS 3.1.8">
          ชื่อพนักงานและชื่อตำแหน่งเป็น require field · เลือกชื่อพนักงานผ่าน Pop Up (ปุ่มค้นหา) · ช่อง "ภาค" แสดงเมื่อเลือกตำแหน่ง "ส่งเสริมธุรกิจพันธมิตรฯ" · การแก้ไขต้องระบุเหตุผล → <code>audit_logs</code>
        </InfoCard>
      </div>

      <Modal
        open={!!editing}
        title={editing === 'add' ? 'เพิ่มผู้ปฏิบัติงาน' : 'แก้ไขผู้ปฏิบัติงาน'}
        sub="operator_assignments"
        onClose={() => setEditing(null)}
        footer={
          <>
            <Button variant="muted" size="sm" onClick={() => setEditing(null)}>ยกเลิก</Button>
            <Button size="sm" onClick={save} disabled={busy || !form.empName}>บันทึก</Button>
          </>
        }
      >
        <div className="flex flex-col gap-3">
          <div className="field"><label>ชื่อผู้ปฏิบัติงาน</label><input value={form.empName} onChange={(e) => setForm({ ...form, empName: e.target.value })} /></div>
          <div className="field"><label>E-Mail</label><input value={form.empMail} onChange={(e) => setForm({ ...form, empMail: e.target.value })} /></div>
          <div className="field">
            <label>ชื่อตำแหน่ง</label>
            <select value={form.sectionName} onChange={(e) => setForm({ ...form, sectionName: e.target.value })}>
              {SECTIONS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="field">
            <label>ภาคที่รับผิดชอบ</label>
            <select value={form.zoneCode} onChange={(e) => setForm({ ...form, zoneCode: e.target.value })}>
              {ZONES.map((z) => <option key={z}>{z}</option>)}
            </select>
          </div>
        </div>
      </Modal>
    </>
  );
}
