import { Download, Search } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Pill } from '@/components/ui/Pill';
import { DataState } from '@/components/ui/DataState';
import { useApi } from '@/hooks/useApi';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import { statusPill } from '@/lib/status';
import { fmt } from '@/lib/format';
import type { Lookup, Paged, ReportRow } from '@/types/api';

const STORE_TYPES = ['FR Type A', 'FR Type B', 'FR Type C', 'FR Type พนักงาน'];
const REGIONS = ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS'];
const RESULTS = ['ทั้งหมด', 'อนุมัติ (เห็นควรชดเชย)', 'ไม่อนุมัติ (เห็นควรไม่ชดเชย / หยุดชดเชย)', 'ยังไม่พิจารณา (-)'];
const COLS = [
  'รหัสร้านถูกกระทบ', 'ชื่อร้านถูกกระทบ', 'ภาค', 'ประเภทร้าน', 'เดือนปีที่ถูกกระทบ', 'วันที่โอนเป็นร้าน SP',
  'Period Statement', 'รหัสร้านเปิดใหม่', 'ชื่อร้านเปิดใหม่', 'ภาค (ร้านใหม่)', 'ประเภทร้าน (ร้านใหม่)',
  'ยอดเงินชดเชย', 'สถานะ', 'ชื่อ-นามสกุลผู้ดำเนินการ', 'ผลการพิจารณา', 'รอดำเนินการ (วัน)', 'ครั้งที่', 'วันที่สร้าง', 'เลขที่เอกสาร',
];

function HBar({ rows, unit }: { rows: { label: string; value: number }[]; unit?: string }) {
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  return (
    <div className="flex flex-col gap-2">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-2 text-[12px]">
          <span className="w-40 flex-none truncate text-slate-500">{r.label}</span>
          <span className="h-3.5 flex-1 rounded-full bg-slate-100">
            <span className="block h-3.5 rounded-full bg-primary" style={{ width: `${Math.max(3, (r.value / max) * 100)}%` }} />
          </span>
          <span className="num w-16 flex-none text-right font-semibold text-ink">{fmt(r.value)}</span>
        </div>
      ))}
      {unit && <div className="mt-1 text-right text-[11px] text-muted">หน่วย: {unit}</div>}
    </div>
  );
}

export default function K2Report() {
  const { toast } = useToast();
  const statuses = useApi<{ items: Lookup[] }>(EP.documentStatuses);
  const report = useApi<Paged<ReportRow>>(EP.reportsStatusSummary, { year: 2569, size: 50 });
  const rows = report.data?.items ?? [];

  const total = rows.reduce((s, r) => s + r.amount, 0);
  const over100k = rows.filter((r) => r.amount > 100000).length;
  const reds = rows.filter((r) => r.red).length;

  const statusRows = Object.entries(rows.reduce<Record<string, number>>((a, r) => { a[r.status] = (a[r.status] ?? 0) + 1; return a; }, {}))
    .map(([label, value]) => ({ label: label.replace(' ดำเนินการ', ''), value }));
  const regionRows = Object.entries(rows.reduce<Record<string, number>>((a, r) => { a[r.region] = (a[r.region] ?? 0) + r.amount; return a; }, {}))
    .map(([label, value]) => ({ label, value }));

  return (
    <>
      <PageHead
        title="รายงานสรุปสถานะ"
        sub="ค้นหาและออกรายงานสรุปสถานะเอกสารประกันรายได้ (SRS 3.1.7 · 19 คอลัมน์) · GET /reports/status-summary"
        actions={<Button onClick={() => toast('กำลังส่งออกรายงานเป็นไฟล์ Excel...', 'ok')}><Download size={18} /> Export Excel</Button>}
      />

      <Card className="mb-5">
        <CardHead title="กรุณาระบุข้อมูลที่ท่านต้องการค้นหา" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="field"><label>รหัสร้านที่ถูกกระทบ</label><input placeholder="เลือกรหัสร้าน" /></div>
          <div className="field"><label>ชื่อร้านที่ถูกกระทบ</label><input placeholder="แสดงอัตโนมัติ" readOnly /></div>
          <div className="field"><label>เดือน/ปี (เริ่มต้น)</label><input type="month" className="num" /></div>
          <div className="field"><label>ถึง (สิ้นสุด)</label><input type="month" className="num" /></div>
          <div className="field"><label>ประเภทร้าน (เลือกได้มากกว่า 1)</label><CheckGrid items={STORE_TYPES} cols={2} /></div>
          <div className="field"><label>ภาค (เลือกได้มากกว่า 1)</label><CheckGrid items={REGIONS} cols={4} /></div>
          <div className="field">
            <label>สถานะ (ค้นหาได้ทีละ 1 สถานะ)</label>
            <select><option>ทั้งหมด</option>{(statuses.data?.items ?? []).map((s) => <option key={s.code}>{s.name}</option>)}</select>
          </div>
          <div className="field"><label>ผลการพิจารณา (อนุมัติ/ไม่อนุมัติ)</label><select>{RESULTS.map((r) => <option key={r}>{r}</option>)}</select></div>
          <div className="field md:col-span-2">
            <label>Period Statement (From – To)</label>
            <div className="flex gap-2"><input type="month" className="num flex-1" aria-label="from" /><input type="month" className="num flex-1" aria-label="to" /></div>
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="muted" size="sm" onClick={() => toast('เคลียร์ค่าเริ่มใหม่')}>เคลียร์ค่าเริ่มใหม่</Button>
          <Button size="sm" onClick={() => report.refetch()}><Search size={16} /> ค้นหาข้อมูล</Button>
        </div>
      </Card>

      <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-[13px] text-slate-500">
        <span>พบ <b className="text-[15px] text-ink">{rows.length}</b> รายการ</span>
        <span className="text-slate-300">·</span>
        <span>ยอดเงินชดเชยรวม <b className="num text-[15px] text-ink">{fmt(total)}</b> บาท</span>
        <span className="text-slate-300">·</span>
        <span>วงเงิน &gt; 100,000 <b className="text-[15px] text-ink">{over100k}</b> รายการ</span>
        <span className="text-slate-300">·</span>
        <span className="text-danger">ยอดขายไม่ครบ 60 วัน (แถวแดง) <b className="text-[15px]">{reds}</b> รายการ</span>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card><CardHead title="เอกสารตามสถานะ" /><HBar rows={statusRows} /></Card>
        <Card><CardHead title="ยอดเงินชดเชยตามภาค" /><HBar rows={regionRows} unit="บาท" /></Card>
      </div>

      <Card>
        <CardHead
          title="ผลการค้นหารายชื่อร้าน"
          right={<><span className="pill fail font-semibold">แถวแดง = ยอดขายไม่ครบ 60 วัน</span><span className="pill info">19 คอลัมน์</span></>}
        />
        <DataState loading={report.loading} error={report.error} empty={rows.length === 0}>
          <div className="table-wrap">
            <table className="data" style={{ minWidth: 1780 }}>
              <thead><tr>{COLS.map((h) => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.docNo} className={r.red ? 'flag-red' : undefined}>
                    <td className="num">{r.store}</td><td>{r.storeName}</td><td>{r.region}</td><td>{r.type}</td>
                    <td className="num">{r.month}</td><td className="num">{r.transfer}</td><td className="num">{r.period}</td>
                    <td className="num">{r.newStore}</td><td>{r.newName}</td><td>{r.newRegion}</td><td>{r.newType}</td>
                    <td className="num">{fmt(r.amount)}</td>
                    <td><Pill kind={statusPill(r.status)}>{r.status}</Pill></td>
                    <td>{r.officer}</td><td>{r.result}</td><td className="num">{r.waitDays}</td>
                    <td className="num">{r.round}</td><td className="num">{r.created}</td><td className="num">{r.docNo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Card>
    </>
  );
}

function CheckGrid({ items, cols }: { items: string[]; cols: number }) {
  return (
    <div className="grid gap-2 rounded-lg border border-line bg-white p-2.5" style={{ gridTemplateColumns: `repeat(${cols},minmax(0,1fr))` }}>
      {items.map((it) => (
        <label key={it} className="flex cursor-pointer items-center gap-1.5 text-[13px] text-slate-700">
          <input type="checkbox" className="h-4 w-4 accent-primary" /> {it}
        </label>
      ))}
    </div>
  );
}
