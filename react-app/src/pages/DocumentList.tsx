import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Trash2, ChevronUp, ChevronDown } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card } from '@/components/ui/Card';
import { Pill } from '@/components/ui/Pill';
import { DataState } from '@/components/ui/DataState';
import { InfoCard } from '@/components/ui/InfoCard';
import { Pager } from '@/components/ui/Pager';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { ROUTES } from '@/constants/routes';
import { WORKFLOW_ROLES, DOC_STATUSES } from '@/constants/domain';
import { statusPill } from '@/lib/status';
import { fmt } from '@/lib/format';
import { cn } from '@/lib/cn';
import type { Paged, TaskRow } from '@/types/api';
import type { PillKind } from '@/types';

const REGIONS = ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS'];
const TYPES = ['FR Type A', 'FR Type B', 'FR Type C', 'FR Type พนักงาน'];
const BADGE: Record<PillKind, string> = {
  wait: 'bg-amber-100 text-amber-700', violet: 'bg-violet-100 text-violet-700', info: 'bg-blue-100 text-blue-700',
  orange: 'bg-orange-100 text-orange-700', navy: 'bg-indigo-100 text-indigo-800', teal: 'bg-teal-100 text-teal-700',
  muted: 'bg-slate-100 text-slate-600', ok: 'bg-green-100 text-green-700', fail: 'bg-red-100 text-red-700',
};

/** "12/06/2569" (พ.ศ.) → Date */
function parseThai(d: string): number {
  const [dd, mm, yy] = d.split('/').map(Number);
  return new Date(yy - 543, mm - 1, dd).getTime();
}

type Special = '' | 'flag60' | 'over3' | 'over100k';
const SPECIAL_FN: Record<Exclude<Special, ''>, (r: TaskRow) => boolean> = {
  flag60: (r) => r.red,
  over3: (r) => r.waitingDays > 3,
  over100k: (r) => r.compensateAmount > 100000,
};

const COLS: { key: keyof TaskRow; label: string; num?: boolean }[] = [
  { key: 'round', label: 'ครั้งที่', num: true }, { key: 'docNo', label: 'เลขที่เอกสาร', num: true },
  { key: 'storeCode', label: 'รหัสร้าน', num: true }, { key: 'storeName', label: 'ชื่อร้านถูกกระทบ' },
  { key: 'region', label: 'ภาค' }, { key: 'salesDropPercent', label: 'ยอดขายที่ลดลง', num: true },
  { key: 'compensateAmount', label: 'จำนวนเงินที่ชดเชย', num: true }, { key: 'status', label: 'สถานะ' },
  { key: 'waitingDays', label: 'รอ (วัน)', num: true },
];

export default function DocumentList({ mode }: { mode: 'waiting' | 'related' }) {
  const { data, loading, error } = useApi<Paged<TaskRow>>(EP.documents, { size: 100 });
  const all = useMemo(() => data?.items ?? [], [data]);

  const [roleCode, setRoleCode] = useState('06');
  const [statusKey, setStatusKey] = useState('');
  const [special, setSpecial] = useState<Special>('');
  const [q, setQ] = useState('');
  const [region, setRegion] = useState('');
  const [type, setType] = useState('');
  const [dFrom, setDFrom] = useState('');
  const [dTo, setDTo] = useState('');
  const [dropMin, setDropMin] = useState('');
  const [dropMax, setDropMax] = useState('');
  const [compMin, setCompMin] = useState('');
  const [compMax, setCompMax] = useState('');
  const [dayMin, setDayMin] = useState('');
  const [dayMax, setDayMax] = useState('');
  const [sort, setSort] = useState<{ key: keyof TaskRow; dir: 1 | -1 } | null>(null);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);

  const role = WORKFLOW_ROLES.find((r) => r.code === roleCode)!;
  const base = mode === 'waiting' ? all.filter((r) => r.status === role.wait) : all;

  const filtered = useMemo(() => {
    let rows = base;
    if (mode === 'related' && statusKey) rows = rows.filter((r) => r.status === statusKey);
    if (special) rows = rows.filter(SPECIAL_FN[special]);
    if (q) { const s = q.toLowerCase(); rows = rows.filter((r) => [r.docNo, r.storeCode, r.storeName].some((v) => v.toLowerCase().includes(s))); }
    if (region) rows = rows.filter((r) => r.region === region);
    if (type) rows = rows.filter((r) => r.type === type);
    if (dFrom) rows = rows.filter((r) => parseThai(r.created) >= new Date(dFrom).getTime());
    if (dTo) rows = rows.filter((r) => parseThai(r.created) <= new Date(dTo).getTime());
    if (dropMin) rows = rows.filter((r) => r.salesDropPercent >= +dropMin);
    if (dropMax) rows = rows.filter((r) => r.salesDropPercent <= +dropMax);
    if (compMin) rows = rows.filter((r) => r.compensateAmount >= +compMin);
    if (compMax) rows = rows.filter((r) => r.compensateAmount <= +compMax);
    if (dayMin) rows = rows.filter((r) => r.waitingDays >= +dayMin);
    if (dayMax) rows = rows.filter((r) => r.waitingDays <= +dayMax);
    if (sort) rows = [...rows].sort((a, b) => { const x = a[sort.key], y = b[sort.key]; return (x < y ? -1 : x > y ? 1 : 0) * sort.dir; });
    return rows;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base, mode, statusKey, special, q, region, type, dFrom, dTo, dropMin, dropMax, compMin, compMax, dayMin, dayMax, sort]);

  useEffect(() => setPage(1), [filtered.length]);
  const rows = filtered.slice((page - 1) * size, page * size);
  const count = (fn: (r: TaskRow) => boolean) => base.filter(fn).length;

  function clearFilters() {
    setQ(''); setRegion(''); setType(''); setDFrom(''); setDTo(''); setDropMin(''); setDropMax(''); setCompMin(''); setCompMax(''); setDayMin(''); setDayMax('');
  }
  function toggleSort(key: keyof TaskRow) {
    setSort((s) => (s?.key === key ? { key, dir: s.dir === 1 ? -1 : 1 } : { key, dir: 1 }));
  }

  // stat cards
  const statCards: { key: string; label: string; value: number; tone: PillKind; onClick: () => void; active: boolean }[] =
    mode === 'waiting'
      ? [
          { key: '', label: `งานรอดำเนินการ · ${role.short}`, value: base.length, tone: 'info', onClick: () => setSpecial(''), active: !special },
          { key: 'flag60', label: 'ยอดขายไม่ครบ 60 วัน (แถวแดง)', value: count(SPECIAL_FN.flag60), tone: 'fail', onClick: () => setSpecial('flag60'), active: special === 'flag60' },
          { key: 'over3', label: 'รอเกิน 3 วัน', value: count(SPECIAL_FN.over3), tone: 'wait', onClick: () => setSpecial('over3'), active: special === 'over3' },
          { key: 'over100k', label: 'วงเงิน > 100,000 (เข้าเส้น AVP)', value: count(SPECIAL_FN.over100k), tone: 'navy', onClick: () => setSpecial('over100k'), active: special === 'over100k' },
        ]
      : [
          { key: 'all', label: 'เอกสารที่เกี่ยวข้องทั้งหมด', value: all.length, tone: 'info', onClick: () => { setStatusKey(''); setSpecial(''); }, active: !statusKey && !special },
          ...DOC_STATUSES.map((s) => ({ key: s.code, label: s.label, value: all.filter((r) => r.status === s.label).length, tone: s.pill, onClick: () => { setStatusKey(s.label); setSpecial(''); }, active: statusKey === s.label })),
          { key: 'flag60', label: 'ยอดขายไม่ครบ 60 วัน (แถวแดง)', value: all.filter(SPECIAL_FN.flag60).length, tone: 'fail' as PillKind, onClick: () => { setSpecial('flag60'); setStatusKey(''); }, active: special === 'flag60' },
          { key: 'over3', label: 'รอเกิน 3 วัน', value: all.filter(SPECIAL_FN.over3).length, tone: 'wait' as PillKind, onClick: () => { setSpecial('over3'); setStatusKey(''); }, active: special === 'over3' },
          { key: 'over100k', label: 'วงเงิน > 100,000', value: all.filter(SPECIAL_FN.over100k).length, tone: 'navy' as PillKind, onClick: () => { setSpecial('over100k'); setStatusKey(''); }, active: special === 'over100k' },
        ];

  const rangeCls = 'flex items-center gap-1.5';
  const rangeInput = 'w-full rounded-lg border border-line px-2 py-1.5 text-[13px]';

  return (
    <>
      {mode === 'waiting' && (
        <Card accent className="mb-5">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-[14px] font-semibold text-ink">ขั้นตอน Workflow ตามบทบาท</span>
            <select value={roleCode} onChange={(e) => setRoleCode(e.target.value)} className="min-w-[320px] rounded-lg border border-line px-3 py-2 text-[13.5px]">
              {WORKFLOW_ROLES.map((r) => <option key={r.code} value={r.code}>{r.code} · {r.name}</option>)}
            </select>
            <span className="flex-1 text-[12.5px] text-muted">งานรอดำเนินการและการ์ดสถานะด้านล่างจะแสดงเฉพาะที่อยู่ในสิทธิ์ของบทบาทนี้</span>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-1">
            {WORKFLOW_ROLES.map((r, i) => (
              <span key={r.code} className="flex items-center gap-1">
                {i > 0 && <span className="text-slate-300">›</span>}
                <button onClick={() => setRoleCode(r.code)} className={cn('whitespace-nowrap rounded-full px-2.5 py-1 text-[12px]', roleCode === r.code ? 'bg-primary font-medium text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}>{r.code} {r.short}</button>
              </span>
            ))}
          </div>
        </Card>
      )}

      <PageHead
        title={mode === 'waiting' ? 'เอกสารประกันรายได้ — รอดำเนินการ' : 'เอกสารประกันรายได้ — ที่เกี่ยวข้องกับท่าน'}
        sub={mode === 'waiting'
          ? 'ระบบประกันรายได้ · คลิกรายการเพื่อเปิดเอกสารร้านถูกกระทบ · คลิกการ์ดสถานะด้านล่างเพื่อกรองตาราง'
          : 'ระบบประกันรายได้ · เอกสารที่ท่านเคยดำเนินการหรือมีส่วนเกี่ยวข้อง · คลิกการ์ดสถานะเพื่อกรองตาราง'}
      />

      <div className={cn('mb-5 grid gap-3', mode === 'waiting' ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2 md:grid-cols-4 xl:grid-cols-6')}>
        {statCards.map((c) => (
          <button key={c.key} onClick={c.onClick} className={cn('flex items-center gap-2.5 rounded-card border bg-card p-3 text-left shadow-card transition-shadow hover:shadow-md', c.active ? 'border-primary ring-1 ring-primary/40' : 'border-line')}>
            <span className={cn('flex h-8 w-8 flex-none items-center justify-center rounded-lg text-[13px] font-bold', BADGE[c.tone])}>{c.value}</span>
            <span className="text-[11.5px] leading-tight text-slate-600">{c.label.replace(' ดำเนินการ', '')}</span>
          </button>
        ))}
      </div>

      <Card>
        {/* filter panel */}
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2">
            <div className="mb-1 text-[12px] text-muted">ค้นหา</div>
            <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-1.5">
              <Search size={16} className="text-slate-400" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="ค้นหาเลขที่เอกสาร / รหัสร้าน / ชื่อร้าน" className="flex-1 text-[13px] outline-none" />
            </div>
          </div>
          <div><div className="mb-1 text-[12px] text-muted">ภาค</div><select value={region} onChange={(e) => setRegion(e.target.value)} className={rangeInput}><option value="">ทุกภาค</option>{REGIONS.map((r) => <option key={r}>{r}</option>)}</select></div>
          <div><div className="mb-1 text-[12px] text-muted">ประเภทร้าน</div><select value={type} onChange={(e) => setType(e.target.value)} className={rangeInput}><option value="">ทุกประเภท</option>{TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
          <div><div className="mb-1 text-[12px] text-muted">วันที่สร้าง</div><div className={rangeCls}><input type="date" value={dFrom} onChange={(e) => setDFrom(e.target.value)} className={rangeInput} /><span className="text-slate-300">–</span><input type="date" value={dTo} onChange={(e) => setDTo(e.target.value)} className={rangeInput} /></div></div>
          <div><div className="mb-1 text-[12px] text-muted">ยอดขายที่ลดลง (%)</div><div className={rangeCls}><input type="number" value={dropMin} onChange={(e) => setDropMin(e.target.value)} placeholder="ต่ำสุด" className={rangeInput} /><span className="text-slate-300">–</span><input type="number" value={dropMax} onChange={(e) => setDropMax(e.target.value)} placeholder="สูงสุด" className={rangeInput} /></div></div>
          <div><div className="mb-1 text-[12px] text-muted">เงินชดเชย (บาท)</div><div className={rangeCls}><input type="number" value={compMin} onChange={(e) => setCompMin(e.target.value)} placeholder="ต่ำสุด" className={rangeInput} /><span className="text-slate-300">–</span><input type="number" value={compMax} onChange={(e) => setCompMax(e.target.value)} placeholder="สูงสุด" className={rangeInput} /></div></div>
          <div><div className="mb-1 text-[12px] text-muted">รอ (วัน)</div><div className={rangeCls}><input type="number" value={dayMin} onChange={(e) => setDayMin(e.target.value)} placeholder="ต่ำสุด" className={rangeInput} /><span className="text-slate-300">–</span><input type="number" value={dayMax} onChange={(e) => setDayMax(e.target.value)} placeholder="สูงสุด" className={rangeInput} /></div></div>
        </div>
        <div className="mb-3 flex justify-end">
          <button onClick={clearFilters} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-[13px] text-slate-600 hover:bg-slate-50"><Trash2 size={15} /> ล้างตัวกรอง</button>
        </div>

        <DataState loading={loading} error={error} empty={filtered.length === 0}>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  {COLS.map((c) => (
                    <th key={c.key} onClick={() => toggleSort(c.key)} className="cursor-pointer select-none">
                      <span className="inline-flex items-center gap-1">{c.label}{sort?.key === c.key && (sort.dir === 1 ? <ChevronUp size={13} /> : <ChevronDown size={13} />)}</span>
                    </th>
                  ))}
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.docNo} className={r.red ? 'flag-red' : undefined}>
                    <td className="num">{r.round}</td>
                    <td className="num font-medium">{r.docNo}</td>
                    <td className="num">{r.storeCode}</td>
                    <td>{r.storeName}</td>
                    <td>{r.region}</td>
                    <td className="num text-danger">{r.salesDropPercent}%</td>
                    <td className="num">{fmt(r.compensateAmount)}</td>
                    <td><Pill kind={statusPill(r.status)}>{r.status}</Pill></td>
                    <td className="num">{r.waitingDays}</td>
                    <td><Link to={ROUTES.document(r.docNo)} className="text-primary hover:underline">เปิด</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} size={size} total={filtered.length} filteredFrom={base.length} onPage={setPage} onSize={setSize} />
        </DataState>
      </Card>

      <div className="mt-5">
        <InfoCard title="หมายเหตุการทำงาน">
          <span className="pill fail align-middle font-semibold">แดง = ยอดขายไม่ครบ 60 วัน</span> · ระบบรับข้อมูลจากทีม Store Chain Unit เป็น text file รอบ <b>17:00 ของทุกวัน</b> ผ่าน Batch job · คลิกรายการในตารางเพื่อเปิดหน้า<b>เอกสารร้านที่ถูกกระทบ</b> (ดูรายละเอียด ผลการพิจารณา และสถานะเอกสาร) · หลังตัดสินใจ Approve (A) ระบบบันทึกบัญชีส่งไปยัง SAP และยืนยันด้วย <code>confirmDataFromBPM</code>
        </InfoCard>
      </div>
    </>
  );
}
