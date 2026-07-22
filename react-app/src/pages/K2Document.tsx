import { useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { Printer } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Pill, Chip } from '@/components/ui/Pill';
import { Button } from '@/components/ui/Button';
import { DataState } from '@/components/ui/DataState';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { WORKFLOW_ROLES } from '@/constants/domain';
import { statusPill } from '@/lib/status';
import { fmt } from '@/lib/format';
import type { DocumentDetail } from '@/types/api';

function Meta({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-line py-2">
      <span className="text-[12px] text-muted">{k}</span>
      <span className="text-[13.5px] text-ink">{v}</span>
    </div>
  );
}

function SalesCompare({ dropPct }: { dropPct: number }) {
  const before = 42450;
  const after = Math.round(before * (1 - dropPct / 100));
  const barH = (v: number) => ((v - 30000) / 14000) * 118;
  return (
    <svg viewBox="0 0 320 196" width="100%" style={{ maxWidth: 380 }} fontFamily="Prompt,Sarabun,sans-serif">
      <line x1="34" y1="166" x2="304" y2="166" stroke="#dde5ef" strokeWidth={1.2} />
      {[{ x: 104, v: before, c: '#2f6fed', label: 'ก่อนเปิด' }, { x: 216, v: after, c: '#dc2626', label: 'หลังเปิด' }].map((b) => {
        const h = barH(b.v);
        return (
          <g key={b.label}>
            <rect x={b.x - 42} y={166 - h} width={84} height={h} rx={6} fill={b.c} />
            <text x={b.x} y={166 - h - 8} textAnchor="middle" fontSize={14} fontWeight={800} fill="#2b3440">{fmt(b.v)}</text>
            <text x={b.x} y={184} textAnchor="middle" fontSize={11.5} fill="#55677d">{b.label}</text>
          </g>
        );
      })}
      <g transform="translate(118,6)"><rect width={84} height={26} rx={8} fill="#fdecec" stroke="#e2a3a3" /><text x={42} y={17} textAnchor="middle" fontSize={13.5} fontWeight={800} fill="#c0392b">−{dropPct.toFixed(2)}%</text></g>
    </svg>
  );
}

/** แผนที่ POI (AllMap) — ร้านถูกกระทบตรงกลาง + รัศมี 1 กม. + ร้านเปิดใหม่ + คู่แข่ง */
function AllMap({ data }: { data: DocumentDetail }) {
  const cx = 230, cy = 150;
  const newPos = data.newStores.map((_, i) => ({ a: -0.6 + i * 1.2 }));
  const compPos = data.competitors.map((_, i) => ({ a: 2.2 + i * 1.1 }));
  const at = (a: number, r: number) => ({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r });
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-[#f5f9ff] p-2">
      <svg viewBox="0 0 460 300" width="100%" style={{ minWidth: 380 }} fontFamily="Prompt,Sarabun,sans-serif">
        <circle cx={cx} cy={cy} r={110} fill="#2f6fed0d" stroke="#2f6fed" strokeWidth={1.2} strokeDasharray="5 4" />
        <text x={cx} y={cy - 116} textAnchor="middle" fontSize={10} fill="#2f6fed">รัศมี 1 กม.</text>
        {/* ร้านถูกกระทบ (center) */}
        <circle cx={cx} cy={cy} r={9} fill="#16a34a" />
        <text x={cx} y={cy + 24} textAnchor="middle" fontSize={10.5} fontWeight={700} fill="#15803d">{data.impactedStore.storeCode} (SP)</text>
        {/* ร้านเปิดใหม่ */}
        {data.newStores.map((n, i) => {
          const p = at(newPos[i].a, 78);
          return (
            <g key={n.storeCode}>
              <line x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="#c8d6ec" strokeWidth={1} />
              <circle cx={p.x} cy={p.y} r={7} fill="#2f6fed" />
              <text x={p.x} y={p.y - 11} textAnchor="middle" fontSize={9.5} fill="#1d4ed8">{n.storeCode}</text>
            </g>
          );
        })}
        {/* คู่แข่ง */}
        {data.competitors.map((c, i) => {
          const p = at(compPos[i].a, 62);
          return (
            <g key={c.competitorCode}>
              <circle cx={p.x} cy={p.y} r={6} fill="#f59e0b" />
              <text x={p.x} y={p.y - 10} textAnchor="middle" fontSize={9} fill="#92670b">{c.competitorName}</text>
            </g>
          );
        })}
      </svg>
      <div className="flex flex-wrap gap-4 px-2 pb-1 text-[11.5px] text-slate-600">
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full bg-success" /> ร้านถูกกระทบ (SP)</span>
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full bg-primary" /> ร้านเปิดใหม่</span>
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full bg-warn" /> ร้านคู่แข่ง (ALLMAP)</span>
      </div>
    </div>
  );
}

export default function K2Document() {
  const { docNo = '' } = useParams();
  const { toast } = useToast();
  const [role, setRole] = useState('06');
  const [decision, setDecision] = useState('');
  const [comment, setComment] = useState('');
  const { data, loading, error } = useApi<DocumentDetail>(docNo ? EP.document(docNo) : null);
  const currentRole = WORKFLOW_ROLES.find((r) => r.code === role)!;

  // ตัวเลือกผลพิจารณาตามขั้น (verbatim จาก SRS)
  const OPTIONS: Record<string, string[]> = {
    '06': ['เห็นควรไม่ชดเชย', 'หยุดชดเชยประกันรายได้', 'ส่งฝ่ายส่งเสริมธุรกิจ SBP', 'ส่งเจ้าหน้าที่ SBP DSA'],
    '08': ['คำนวณเงินชดเชยเรียบร้อย', 'ส่งกลับฝ่าย SBP DSA'],
    '01': ['เห็นควรชดเชย', 'เห็นควรไม่ชดเชย / ส่งกลับ'],
    '02': ['เห็นควรชดเชย', 'เห็นควรไม่ชดเชย', 'ส่งกลับฝ่ายส่งเสริมธุรกิจ SBP'],
    '03': ['เห็นควรชดเชย', 'เห็นควรไม่ชดเชย', 'ส่งกลับ GM ส่งเสริมฯ'],
  };

  function submit() {
    if (!decision) { toast('ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ'); return; }
    toast(`ส่งผล: ${decision} (POST /documents/{docNo}/actions)`, 'ok');
    setDecision(''); setComment('');
  }

  return (
    <>
      <PageHead
        title={`เอกสารประกันรายได้ ${docNo}`}
        sub="รายละเอียดเอกสาร · GET /documents/{docNo}"
        actions={
          <>
            <select value={role} onChange={(e) => setRole(e.target.value)} className="rounded-lg border border-line px-3 py-2 text-[13px]">
              {WORKFLOW_ROLES.map((r) => <option key={r.code} value={r.code}>มุมมอง: {r.code} {r.short}</option>)}
            </select>
            <Button variant="ghost" onClick={() => toast('พิมพ์เอกสาร')}><Printer size={16} /> พิมพ์</Button>
          </>
        }
      />
      <DataState loading={loading} error={error}>
        {data && (
          <div className="flex flex-col gap-5">
            <div className="rounded-lg bg-primary-soft px-4 py-2 text-[13px] text-primary">
              กำลังดูในมุมมอง <b>{currentRole.name}</b> — {role === data.currentSection ? 'เป็นเจ้าของงานขั้นนี้ (แก้ไข/ส่งดำเนินการได้)' : 'อ่านอย่างเดียว (ไม่ใช่ขั้นปัจจุบัน)'}
            </div>

            <Card>
              <CardHead title="ข้อมูลร้านถูกกระทบ" right={<Pill kind={statusPill(data.status)}>{data.status}</Pill>} />
              <div className="grid grid-cols-2 gap-x-6 md:grid-cols-4">
                <Meta k="เลขที่เอกสาร" v={<span className="num">{data.docNo}</span>} />
                <Meta k="รหัสร้านถูกกระทบ" v={<span className="num">{data.impactedStore.storeCode}</span>} />
                <Meta k="ชื่อร้าน" v={data.impactedStore.storeName} />
                <Meta k="ภาค / ประเภท" v={`${data.impactedStore.region} · ${data.impactedStore.storeType}`} />
                <Meta k="ยอดขายที่ลดลง" v={<span className="text-danger num">{data.salesDropPercent}%</span>} />
                <Meta k="จำนวนเงินที่ชดเชย" v={<span className="text-success num">{fmt(data.compensateAmount)} ฿</span>} />
                <Meta k="Section ปัจจุบัน" v={<span className="num">{data.currentSection}</span>} />
              </div>
            </Card>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <Card>
                <CardHead title="แผนที่ (POI จากระบบ AllMap)" />
                <AllMap data={data} />
              </Card>
              <Card>
                <CardHead title="แนวโน้มยอดขาย ก่อน–หลัง" right={<Pill kind="fail">ลดลง {data.salesDropPercent}%</Pill>} />
                <SalesCompare dropPct={data.salesDropPercent} />
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <Card>
                <CardHead title="ร้านเปิดใหม่ (ที่ทำให้กระทบ)" right={role === '01' ? <Chip>แก้ไขได้ในขั้นนี้</Chip> : undefined} />
                <table className="data">
                  <thead><tr><th>รหัส</th><th>ชื่อร้าน</th><th>ระยะ (กม.)</th><th>%ชดเชย</th></tr></thead>
                  <tbody>
                    {data.newStores.map((n) => (
                      <tr key={n.storeCode}><td className="num">{n.storeCode}</td><td>{n.storeName}</td><td className="num">{n.distanceKm}</td><td className="num">{n.compensatePercent}%</td></tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-[12px] text-muted">%ชดเชยรวมต้องเท่ากับ 100%</p>
              </Card>
              <Card>
                <CardHead title="ร้านคู่แข่ง / ปัจจัยภายนอก" />
                <table className="data mb-3">
                  <tbody>
                    {data.competitors.map((c) => (
                      <tr key={c.competitorCode}><td className="num w-24">{c.competitorCode}</td><td>{c.competitorName}</td><td className="num">{c.impactDate}</td></tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex flex-wrap gap-2">
                  {data.factors.map((f) => <span key={f.factorCode} className="chip">{f.factorCode} · {f.factorName}</span>)}
                </div>
              </Card>
            </div>

            <Card>
              <CardHead title="คำนวณเงินชดเชย" right={<Chip>ผ่านระบบ Finance &amp; Account (FS)</Chip>} />
              <table className="data">
                <thead><tr><th>รายการ</th><th>สูตร / เกณฑ์</th><th>จำนวน</th></tr></thead>
                <tbody>
                  <tr><td>ยอดขายเฉลี่ยก่อนกระทบ</td><td className="text-muted">4 หน้าต่าง × 15 วัน</td><td className="num">42,450.00</td></tr>
                  <tr><td>ยอดขายเฉลี่ยหลังกระทบ</td><td className="text-muted">4 หน้าต่าง × 15 วัน</td><td className="num">{fmt(Math.round(42450 * (1 - data.salesDropPercent / 100)))}.00</td></tr>
                  <tr><td>อัตราชดเชย</td><td className="text-muted">ตามหลักเกณฑ์ SP</td><td className="num">ตามสูตร</td></tr>
                  <tr className="font-semibold"><td>รวมเงินชดเชย (งวดล่าสุด)</td><td className="text-muted">%ชดเชย × ผลต่าง</td><td className="num text-success">{fmt(data.compensateAmount)}.00</td></tr>
                </tbody>
              </table>
            </Card>

            <Card>
              <CardHead title="เอกสารแนบทั้งหมด" />
              <table className="data">
                <thead><tr><th>ไฟล์</th><th>หน่วยงาน</th><th>ผู้แนบ</th><th>รายละเอียด</th><th>วันที่</th></tr></thead>
                <tbody>
                  <tr><td className="num">impact_report.pdf</td><td>ฝ่าย บธฟ</td><td>Chantaporn B.</td><td>รายงานยอดขายย้อนหลัง</td><td className="num">12/06/2569</td></tr>
                  <tr><td className="num">SBP_Statement.pdf</td><td>Finance &amp; Account</td><td>ระบบ FS</td><td>SBP Statement</td><td className="num">13/06/2569</td></tr>
                </tbody>
              </table>
            </Card>

            <Card>
              <CardHead title="ประวัติการชดเชย" />
              <table className="data">
                <thead><tr><th>ครั้ง</th><th>เดือน/ปีที่กระทบ</th><th>จำนวนเงินที่ชดเชย</th><th>เดือน/ปีที่ส่งบัญชี</th><th>สถานะเอกสาร</th><th>ผลการพิจารณา</th></tr></thead>
                <tbody>
                  <tr><td className="num">1</td><td className="num">04/2569</td><td className="num">{fmt(25650)}</td><td className="num">05/2569</td><td><Pill kind="ok">เสร็จสิ้น</Pill></td><td>เห็นควรชดเชย</td></tr>
                  <tr><td className="num">2</td><td className="num">{data.impactedStore.region ? '05/2569' : '-'}</td><td className="num">{fmt(data.compensateAmount)}</td><td>-</td><td><Pill kind={statusPill(data.status)}>{data.status}</Pill></td><td>อยู่ระหว่างพิจารณา</td></tr>
                </tbody>
              </table>
            </Card>

            <Card>
              <CardHead title="ประวัติการพิจารณา (Timeline)" />
              <ol className="relative ml-2 border-l-2 border-line pl-5">
                {data.timeline.map((t, i) => (
                  <li key={i} className="mb-3">
                    <span className="absolute -left-[7px] mt-1 h-3 w-3 rounded-full bg-primary" />
                    <div className="text-[13px]"><b>Section {t.section}</b> · {t.considerName} — {t.result}</div>
                    <div className="num text-[12px] text-muted">{t.actionDateTime.replace('T', ' ')}</div>
                  </li>
                ))}
              </ol>
            </Card>

            {role === data.currentSection && (
              <Card accent>
                <CardHead title="พิจารณา (ส่งดำเนินการ)" right={<Chip>ขั้น {role}</Chip>} />
                <div className="mb-3 flex flex-col gap-2">
                  {(OPTIONS[role] ?? ['เห็นควรชดเชย', 'เห็นควรไม่ชดเชย']).map((o) => (
                    <label key={o} className="flex cursor-pointer items-center gap-2 text-[13.5px] text-slate-700">
                      <input type="radio" name="decision" checked={decision === o} onChange={() => setDecision(o)} className="accent-primary" /> {o}
                    </label>
                  ))}
                </div>
                <div className="field mb-3">
                  <label>ความคิดเห็นเพิ่มเติม</label>
                  <textarea rows={2} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="ระบุความคิดเห็น..." />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => toast('แนบรูปประกอบการพิจารณา')}>แนบรูป</Button>
                  <Button variant="muted" onClick={() => toast('บันทึกฉบับร่างแล้ว', 'ok')}>บันทึก</Button>
                  <Button onClick={submit}>ส่งดำเนินการ</Button>
                </div>
              </Card>
            )}
          </div>
        )}
      </DataState>
    </>
  );
}
