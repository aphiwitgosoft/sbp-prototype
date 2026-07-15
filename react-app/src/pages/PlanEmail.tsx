import { useRef, useState } from 'react';
import { RotateCcw, Pencil, Save, X, Lock } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';
import { DataState } from '@/components/ui/DataState';
import { RichEditor } from '@/components/ui/RichEditor';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { apiPut, apiPost } from '@/lib/api';
import type { EmailTemplate } from '@/types/api';

export default function PlanEmail() {
  const { toast } = useToast();
  const { data, loading, error, refetch } = useApi<{ items: EmailTemplate[] }>(EP.emailTemplates);
  const items = data?.items ?? [];
  const [editing, setEditing] = useState<string | null>(null);
  const [subject, setSubject] = useState('');
  const bodyRef = useRef('');
  const [busy, setBusy] = useState(false);

  function openEdit(t: EmailTemplate) {
    setEditing(t.templateCode);
    setSubject(t.subject);
    bodyRef.current = t.body;
  }
  async function save(t: EmailTemplate) {
    setBusy(true);
    try {
      await apiPut(EP.emailTemplate(t.templateCode), { subject, body: bodyRef.current, reason: 'แก้ไขจากหน้าจอ' });
      toast(`บันทึก ${t.templateCode} แล้ว`, 'ok');
      setEditing(null);
      refetch();
    } catch (e) { toast((e as Error).message); } finally { setBusy(false); }
  }
  async function reset(t: EmailTemplate) {
    try {
      await apiPost(EP.emailTemplateReset(t.templateCode), { reason: 'รีเซ็ตจากหน้าจอ' });
      toast(`รีเซ็ต ${t.templateCode} เป็น Default`, 'ok');
      refetch();
    } catch (e) { toast((e as Error).message); }
  }

  return (
    <>
      <PageHead
        title="Email Template"
        sub="เนื้อหา 8 template (EM-01–08) · From/To/Cc ล็อกตาม status_email_rules · แก้ได้เฉพาะ Subject/เนื้อหา"
        actions={<Button variant="ghost" onClick={() => toast('รีเซ็ตทั้งหมดเป็น Default (POST /email-templates/reset-all)')}><RotateCcw size={16} /> รีเซ็ตทั้งหมด</Button>}
      />
      <DataState loading={loading} error={error} empty={items.length === 0}>
        <div className="flex flex-col gap-4">
          {items.map((t) => {
            const isEdit = editing === t.templateCode;
            return (
              <Card key={t.templateCode} accent={isEdit}>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="num rounded-md bg-primary-soft px-2 py-0.5 text-[12px] font-semibold text-primary">{t.templateCode}</span>
                  <span className="font-semibold text-ink">{t.name}</span>
                  {t.isCustomized ? <Chip className="bg-amber-100 text-amber-700">แก้ไขจาก Default</Chip> : <Chip>Default</Chip>}
                  <div className="ml-auto flex gap-2">
                    {t.isCustomized && !isEdit && <Button variant="muted" size="sm" onClick={() => reset(t)}><RotateCcw size={14} /> รีเซ็ต</Button>}
                    {!isEdit ? (
                      <Button size="sm" onClick={() => openEdit(t)}><Pencil size={14} /> แก้ไข</Button>
                    ) : (
                      <>
                        <Button variant="muted" size="sm" onClick={() => setEditing(null)}><X size={14} /> ยกเลิก</Button>
                        <Button size="sm" disabled={busy} onClick={() => save(t)}><Save size={14} /> บันทึก</Button>
                      </>
                    )}
                  </div>
                </div>

                {/* ผู้รับ (ล็อก) */}
                <div className="mb-3 flex flex-wrap gap-x-6 gap-y-1 rounded-lg bg-slate-50 px-3 py-2 text-[12px] text-slate-600">
                  <span className="flex items-center gap-1"><Lock size={12} /> To: <b className="text-ink">{t.to}</b></span>
                  <span className="flex items-center gap-1"><Lock size={12} /> Cc: <b className="text-ink">{t.cc}</b></span>
                </div>

                {isEdit ? (
                  <div className="flex flex-col gap-3">
                    <div className="field">
                      <label>Subject</label>
                      <input value={subject} onChange={(e) => setSubject(e.target.value)} />
                    </div>
                    <div>
                      <label className="mb-1.5 block text-[13px] text-slate-600">เนื้อหาอีเมล</label>
                      <RichEditor initialHtml={t.body} variables={t.variables} onChange={(html) => (bodyRef.current = html)} />
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="rounded-lg border border-line bg-white px-3 py-2 text-[13px]">
                      <span className="text-muted">Subject:</span> {t.subject}
                    </div>
                    <div className="mt-2 rounded-lg border border-line bg-white px-3 py-2 text-[13px] text-slate-700 [&_ul]:list-disc [&_ul]:pl-6" dangerouslySetInnerHTML={{ __html: t.body }} />
                  </>
                )}
              </Card>
            );
          })}
        </div>
      </DataState>
    </>
  );
}
