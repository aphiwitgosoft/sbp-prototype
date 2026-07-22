import { useState } from 'react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Pill';
import { Modal } from '@/components/ui/Modal';
import { Tabs, type TabDef } from '@/components/ui/Tabs';
import { FlowchartSVG } from '@/components/charts/FlowchartSVG';
import { API_GROUPS, REF_STYLE, type ApiEndpoint } from '@/data/apiCatalog';
import { FLOWCHARTS } from '@/data/flowcharts';
import { cn } from '@/lib/cn';

const MTH: Record<string, string> = {
  GET: 'bg-blue-100 text-blue-700',
  POST: 'bg-green-100 text-green-700',
  PUT: 'bg-amber-100 text-amber-700',
  DELETE: 'bg-red-100 text-red-700',
};

function MethodChip({ m }: { m: string }) {
  return <span className={cn('inline-flex min-w-[52px] justify-center rounded-md px-2 py-0.5 text-[11px] font-extrabold tracking-wide', MTH[m])}>{m}</span>;
}
function RefChip({ ep }: { ep: ApiEndpoint }) {
  const s = REF_STYLE[ep.ref];
  return <span className="rounded-full px-2 py-0.5 text-[10.5px] font-bold" style={{ background: s.bg, color: s.text }}>{ep.refT}</span>;
}
function Code({ children }: { children: string }) {
  return <pre className="overflow-x-auto whitespace-pre rounded-xl bg-slate-900 px-4 py-3.5 font-mono text-[12px] leading-relaxed text-slate-200">{children}</pre>;
}

export default function PlanApi() {
  const [sel, setSel] = useState<ApiEndpoint | null>(null);
  const chart = sel ? FLOWCHARTS[`${sel.m} ${sel.p}`] : undefined;

  const tabs: TabDef[] = sel
    ? [
        {
          key: 'req',
          label: '1. Request / Response',
          content: (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <h4 className="mb-1.5 text-[13px] font-semibold text-slate-500">{sel.m === 'GET' ? 'Request (Query)' : 'Request Body'}</h4>
                  <Code>{sel.req ?? '(ไม่มี body — ใช้ JWT ใน header)'}</Code>
                </div>
                <div>
                  <h4 className="mb-1.5 text-[13px] font-semibold text-slate-500">Response</h4>
                  <Code>{sel.res ?? '200 OK'}</Code>
                </div>
              </div>
              {sel.err && (
                <div>
                  <h4 className="mb-1.5 text-[13px] font-semibold text-slate-500">Error ที่ต้องรองรับ</h4>
                  <ul className="ml-5 list-disc space-y-1 text-[13px] text-slate-600">
                    {sel.err.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ),
        },
        {
          key: 'db',
          label: '2. Database + SQL',
          content: (
            <div className="space-y-4">
              {sel.db ? (
                <table className="data">
                  <thead><tr><th>ตาราง</th><th>สิทธิ์</th><th>บทบาท</th></tr></thead>
                  <tbody>
                    {sel.db.map((d, i) => (
                      <tr key={i}>
                        <td className="num">{d[0]}</td>
                        <td><span className={cn('pill', d[1] === 'R' ? 'info' : d[1] === 'W' ? 'ok' : 'violet')}>{d[1]}</span></td>
                        <td className="text-muted">{d[2]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-[13px] text-muted">รายการตารางเต็มดู <code>api.md</code></p>
              )}
              {sel.sql && (
                <div>
                  <h4 className="mb-1.5 text-[13px] font-semibold text-slate-500">ตัวอย่าง SQL (bind params ขึ้นต้น :)</h4>
                  <Code>{sel.sql}</Code>
                </div>
              )}
            </div>
          ),
        },
        ...(chart
          ? [{
              key: 'chart',
              label: '3. Flowchart',
              content: (
                <div className="overflow-x-auto rounded-xl border border-line bg-slate-50/60 p-3.5">
                  <FlowchartSVG spec={chart} />
                </div>
              ),
            }]
          : []),
      ]
    : [];

  return (
    <>
      <PageHead title="API Specification" sub="REST /api/v1 · 62 เส้น 10 กลุ่ม · คลิกเส้นเพื่อดูรายละเอียด (Flow · SQL · Flowchart)" />

      <div className="mb-5 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[['62', 'เส้น API ทั้งหมด'], ['10', 'กลุ่มตามโดเมน'], ['JWT', 'Bearer Token · Role 00–10'], ['JSON', 'UTF-8 ทุกเส้น']].map(([n, l]) => (
          <div key={l} className="rounded-card border border-line bg-card p-4 text-center shadow-card">
            <div className="text-2xl font-bold text-primary">{n}</div>
            <div className="mt-1 text-[12px] text-muted">{l}</div>
          </div>
        ))}
      </div>

      <Card className="mb-5 border-l-4 border-l-primary">
        <div className="text-[13px] leading-relaxed text-slate-600">
          <b className="text-ink">มาตรฐานกลาง (ทุกเส้น):</b> Base URL <code className="num">/api/v1</code> · Auth <code className="num">Authorization: Bearer &lt;JWT&gt;</code> (ยกเว้น login/refresh + callback ภายนอก) ·
          แบ่งหน้า <code className="num">?page=1&amp;size=20</code> ตอบ <code className="num">{'{page,size,total,items}'}</code> ·
          Error รูปแบบเดียว <code className="num">{'{code,message}'}</code> — ข้อความไทยตรงตาม SRS ·
          วันที่ ISO-8601 + ปี ค.ศ. ใน payload (FE แปลง พ.ศ.)
        </div>
      </Card>

      {API_GROUPS.map((g) => (
        <Card key={g.name} className="mb-4">
          <CardHead title={g.name} right={<Chip>{g.eps.length} เส้น</Chip>} />
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th className="w-20">Method</th><th>Path</th><th>ทำอะไร</th><th className="w-32">ที่มา</th></tr></thead>
              <tbody>
                {g.eps.map((e) => (
                  <tr key={e.m + e.p} className="cursor-pointer" onClick={() => setSel(e)}>
                    <td><MethodChip m={e.m} /></td>
                    <td className="num font-medium text-primary">{e.p}</td>
                    <td className="text-[12.5px]">{e.sum}</td>
                    <td><RefChip ep={e} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}

      <Modal open={!!sel} size="lg" title={sel ? `${sel.m} ${sel.p}` : ''} sub={sel?.sum} onClose={() => setSel(null)}>
        {sel && (
          <div>
            <div className="mb-4 flex flex-wrap gap-2">
              <RefChip ep={sel} />
              {sel.roles && <Chip>สิทธิ์: {sel.roles}</Chip>}
            </div>
            {sel.flow && (
              <div className="mb-5">
                <h4 className="mb-2 text-[13px] font-semibold text-slate-500">
                  ลำดับการทำงาน (Flow){chart && <span className="pill info ml-2 text-[10.5px]">มี Flowchart ในแท็บ 3</span>}
                </h4>
                <ol className="ml-5 list-decimal space-y-1 text-[13.5px] leading-relaxed text-slate-600">
                  {sel.flow.map((f, i) => <li key={i}>{f}</li>)}
                </ol>
              </div>
            )}
            <Tabs tabs={tabs} />
          </div>
        )}
      </Modal>
    </>
  );
}
