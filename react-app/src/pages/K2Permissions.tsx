import { useState } from 'react';
import { Check, X, Plus, Pencil, Trash2 } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { DataState } from '@/components/ui/DataState';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { apiPost, apiPut, apiDelete } from '@/lib/api';
import { cn } from '@/lib/cn';
import type { MenuPermissionRow, RoleRow } from '@/types/api';

const EMPTY: RoleRow = { roleCode: '', roleName: '', roleDesc: '', isSystem: false };

export default function K2Permissions() {
  const { toast } = useToast();
  const roles = useApi<{ items: RoleRow[] }>(EP.roles);
  const perms = useApi<{ menus: MenuPermissionRow[] }>(EP.menuPermissions);
  const roleList = roles.data?.items ?? [];
  const menus = perms.data?.menus ?? [];
  const [edit, setEdit] = useState<{ mode: 'add' | 'edit'; role: RoleRow } | null>(null);
  const [form, setForm] = useState<RoleRow>(EMPTY);
  const [busy, setBusy] = useState(false);

  async function toggle(m: MenuPermissionRow, roleCode: string) {
    try {
      await apiPut(EP.menuPermission(m.menuCode), { access: { [roleCode]: !m.access[roleCode] } });
      perms.refetch();
    } catch (e) { toast((e as Error).message); }
  }
  async function saveRole() {
    setBusy(true);
    try {
      if (edit?.mode === 'add') { await apiPost(EP.roles, form); toast('เพิ่ม Role แล้ว', 'ok'); }
      else { await apiPut(EP.role(form.roleCode), { roleName: form.roleName, roleDesc: form.roleDesc, reason: 'แก้ไข' }); toast('บันทึกแล้ว', 'ok'); }
      setEdit(null); roles.refetch(); perms.refetch();
    } catch (e) { toast((e as Error).message); } finally { setBusy(false); }
  }
  async function removeRole(r: RoleRow) {
    if (!confirm(`ลบ Role ${r.roleCode} ${r.roleName}?`)) return;
    try { await apiDelete(EP.role(r.roleCode), { reason: 'ลบ' }); toast('ลบแล้ว', 'del'); roles.refetch(); perms.refetch(); }
    catch (e) { toast((e as Error).message); }
  }

  return (
    <>
      <PageHead
        title="สิทธิ์การเข้าถึงเมนู"
        sub="matrix สิทธิ์เมนู × Role (00–10) · roles / menus / menu_permissions (SRS 3.1.1) · คลิกช่องเพื่อสลับสิทธิ์"
        actions={<Button onClick={() => { setForm({ ...EMPTY, roleCode: '11' }); setEdit({ mode: 'add', role: EMPTY }); }}><Plus size={18} /> เพิ่ม Role</Button>}
      />

      <Card className="mb-5">
        <CardHead title="ตารางสิทธิ์การเข้าถึง" right={<Chip>{roleList.length} Role × {menus.length} เมนู</Chip>} />
        <DataState loading={roles.loading || perms.loading} error={roles.error || perms.error} empty={menus.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th className="sticky left-0 z-10 bg-thbg">เมนู</th>
                  {roleList.map((r) => <th key={r.roleCode} className="text-center"><div className="num">{r.roleCode}</div><div className="text-[11px] font-normal">{r.roleName}</div></th>)}
                </tr>
              </thead>
              <tbody>
                {menus.map((m) => (
                  <tr key={m.menuCode}>
                    <td className="sticky left-0 z-10 bg-white"><div className="font-medium">{m.menuName}</div><div className="num text-[11px] text-muted">{m.menuCode}</div></td>
                    {roleList.map((r) => (
                      <td key={r.roleCode} className="text-center">
                        <button onClick={() => toggle(m, r.roleCode)} className={cn('mx-auto flex h-6 w-6 items-center justify-center rounded transition-colors', m.access[r.roleCode] ? 'text-success hover:bg-green-50' : 'text-slate-300 hover:bg-slate-100')}>
                          {m.access[r.roleCode] ? <Check size={16} /> : <X size={15} />}
                        </button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[12px] text-muted">ทุกการเปลี่ยนสิทธิ์บันทึก <code>audit_logs</code></p>
        </DataState>
      </Card>

      <Card>
        <CardHead title="กลุ่มผู้ใช้งาน (Roles)" />
        <DataState loading={roles.loading} error={roles.error} empty={roleList.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th className="w-20">Code</th><th>ชื่อ Role</th><th>คำอธิบาย</th><th>ชนิด</th><th className="w-28">Action</th></tr></thead>
              <tbody>
                {roleList.map((r) => (
                  <tr key={r.roleCode}>
                    <td className="num font-medium">{r.roleCode}</td>
                    <td>{r.roleName}</td>
                    <td className="text-muted">{r.roleDesc}</td>
                    <td>{r.isSystem ? <Chip>ระบบ</Chip> : <Chip className="bg-green-100 text-green-700">กำหนดเอง</Chip>}</td>
                    <td>
                      <div className="flex gap-1">
                        <button className="rounded p-1 text-primary hover:bg-primary-soft" onClick={() => { setForm(r); setEdit({ mode: 'edit', role: r }); }}><Pencil size={16} /></button>
                        <button className={cn('rounded p-1', r.isSystem ? 'text-slate-300' : 'text-danger hover:bg-red-50')} disabled={r.isSystem} onClick={() => removeRole(r)}><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>

      <Modal
        open={!!edit}
        title={edit?.mode === 'add' ? 'เพิ่ม Role' : 'แก้ไข Role'}
        sub="roles · สิทธิ์เมนูเริ่มต้นเป็น false ทุกเมนู"
        onClose={() => setEdit(null)}
        footer={<><Button variant="muted" size="sm" onClick={() => setEdit(null)}>ยกเลิก</Button><Button size="sm" disabled={busy || !form.roleCode || !form.roleName} onClick={saveRole}>บันทึก</Button></>}
      >
        <div className="flex flex-col gap-3">
          <div className="field"><label>รหัส Role</label><input value={form.roleCode} disabled={edit?.mode === 'edit'} onChange={(e) => setForm({ ...form, roleCode: e.target.value })} /></div>
          <div className="field"><label>ชื่อ Role</label><input value={form.roleName} onChange={(e) => setForm({ ...form, roleName: e.target.value })} /></div>
          <div className="field"><label>คำอธิบาย</label><input value={form.roleDesc} onChange={(e) => setForm({ ...form, roleDesc: e.target.value })} /></div>
        </div>
      </Modal>
    </>
  );
}
