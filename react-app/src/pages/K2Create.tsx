import { useState } from 'react';
import { Search, FilePlus2, Send } from 'lucide-react';
import { PageHead } from '@/components/ui/PageHead';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Tabs } from '@/components/ui/Tabs';
import { Pill } from '@/components/ui/Pill';
import { InfoCard } from '@/components/ui/InfoCard';
import { apiGet } from '@/lib/api';
import { EP } from '@/constants/api';
import { useToast } from '@/hooks/useToast';
import type { StoreLookup } from '@/types/api';

const STORE_TYPES = ['FR Type A', 'FR Type B', 'FR Type C', 'FR Type C r', 'บริษัท', 'FR Type พนักงาน', 'FR Type PTT', 'FR Type BGC'];
const FS_ROWS = [
  { store: '01045', name: 'บางบัวทอง ก.ม.8', period: '06/2569', sentAt: '25/06/2569', status: 'รอ SBP Statement', done: false },
  { store: '00256', name: 'ปากเกร็ด สถานี', period: '05/2569', sentAt: '24/06/2569', status: 'ส่งกลับแล้ว · สร้างเอกสาร', done: true },
];

function SearchInput({ value, onChange, placeholder, onSearch }: { value: string; onChange: (v: string) => void; placeholder: string; onSearch: () => void }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-1.5">
      <button onClick={onSearch} className="text-slate-400 hover:text-primary"><Search size={17} /></button>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="num flex-1 text-[13.5px] outline-none" />
    </div>
  );
}

function ManualTab() {
  const { toast } = useToast();
  const [impacted, setImpacted] = useState('00788');
  const [impactedName, setImpactedName] = useState('รัตนอุทิศ ซ.13');
  const [region, setRegion] = useState('RS');
  const [newStore, setNewStore] = useState('00990');

  async function lookup(type: 'impacted' | 'new') {
    try {
      const res = await apiGet<{ items: StoreLookup[] }>(EP.storesSearch, { type });
      const s = res.items[0];
      if (s) {
        if (type === 'impacted') { setImpacted(s.storeCode); setImpactedName(s.storeName); setRegion('RS'); }
        else setNewStore(s.storeCode);
        toast(`เลือกร้าน: ${s.storeCode} ${s.storeName}`, 'ok');
      }
    } catch { toast('ค้นหาร้านไม่ได้ — รัน dev:mock'); }
  }

  return (
    <>
      <div className="mb-4">
        <InfoCard>
          ใช้สำหรับร้าน Store Partner ที่อยู่<b>นอกเหนือเงื่อนไขการสร้างเอกสารอัตโนมัติ</b>ของระบบ · เลขที่เอกสารรูปแบบ <code>YYYY/Running 5 หลัก</code> (เริ่มต้น 00001) ระบบจะออกให้อัตโนมัติเมื่อกดสร้างเอกสาร
        </InfoCard>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="field"><label>รหัสร้านถูกกระทบ <span className="text-danger">*</span></label><SearchInput value={impacted} onChange={setImpacted} placeholder="กดแว่นขยายเพื่อค้นหา" onSearch={() => lookup('impacted')} /></div>
        <div className="field"><label>ชื่อร้านถูกกระทบ (อัตโนมัติ)</label><input value={impactedName} readOnly /></div>
        <div className="field"><label>ภาค (อัตโนมัติ)</label><input value={region} readOnly /></div>
        <div className="field"><label>ประเภทร้าน</label><select defaultValue="FR Type B">{STORE_TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
        <div className="field"><label>วันที่โอนเป็นร้าน SP</label><input type="date" /></div>
        <div className="field"><label>เดือน/ปีที่ถูกกระทบ <span className="text-danger">*</span></label><input type="month" defaultValue="2026-06" className="num" /></div>
        <div className="field"><label>ครั้งที่</label><input className="num" defaultValue="3" /></div>
        <div className="field"><label>รหัสร้านเปิดใหม่ (ที่ทำให้กระทบ) <span className="text-danger">*</span></label><SearchInput value={newStore} onChange={setNewStore} placeholder="ค้นหารหัสร้านเปิดใหม่" onSearch={() => lookup('new')} /></div>
        <div className="field md:col-span-2"><label>เหตุผลการสร้างเอกสารนอกเงื่อนไข <span className="text-danger">*</span></label><textarea rows={3} placeholder="ระบุเหตุผล/หมายเหตุการสร้างเอกสารนอกเงื่อนไข..." /></div>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="muted" size="sm" onClick={() => toast('เคลียร์ค่าเริ่มใหม่')}>เคลียร์ค่าเริ่มใหม่</Button>
        <Button size="sm" onClick={() => toast('สร้างเอกสารใหม่เรียบร้อย · ออกเลขที่ 2569/00187', 'ok')}><FilePlus2 size={16} /> สร้างเอกสาร</Button>
      </div>
    </>
  );
}

function FsTab() {
  const { toast } = useToast();
  return (
    <>
      <div className="mb-4">
        <InfoCard>
          สร้างข้อมูลต้นทางผ่านระบบ <b>Finance &amp; Account Unit (FS)</b> จากนั้น<b>รอกระบวนการ SBP Statement</b> ประมวลผลและส่งข้อมูลกลับมายังระบบประกันรายได้ (ใช้เวลาประมาณ <b>1 วัน</b>) · เฉพาะผู้มีสิทธิ์เข้าถึงเท่านั้น
        </InfoCard>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="field"><label>รหัสร้านถูกกระทบ <span className="text-danger">*</span></label>
          <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-1.5"><Search size={17} className="text-slate-400" /><input className="num flex-1 text-[13.5px] outline-none" defaultValue="01045" placeholder="ค้นหารหัสร้าน" /></div>
        </div>
        <div className="field"><label>ชื่อร้านถูกกระทบ (อัตโนมัติ)</label><input value="บางบัวทอง ก.ม.8" readOnly /></div>
        <div className="field"><label>เดือน/ปีที่ถูกกระทบ <span className="text-danger">*</span></label><input type="month" defaultValue="2026-06" className="num" /></div>
        <div className="field"><label>Period Statement (From – To)</label><input className="num" placeholder="01/05/2569 - 31/05/2569" /></div>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="muted" size="sm" onClick={() => toast('เคลียร์ค่าเริ่มใหม่')}>เคลียร์ค่าเริ่มใหม่</Button>
        <Button size="sm" onClick={() => toast('ส่งสร้างข้อมูลที่ FS · รอ SBP Statement ส่งกลับ ~1 วัน', 'ok')}><Send size={16} /> ส่งสร้างที่ FS</Button>
      </div>

      <h3 className="mb-3 mt-6 text-[14px] font-semibold text-ink">เอกสารที่รอ SBP Statement ส่งกลับ</h3>
      <div className="table-wrap">
        <table className="data">
          <thead><tr><th>รหัสร้าน</th><th>ชื่อร้านถูกกระทบ</th><th>เดือน/ปี</th><th>ส่งเข้า FS เมื่อ</th><th>สถานะ</th></tr></thead>
          <tbody>
            {FS_ROWS.map((r) => (
              <tr key={r.store}>
                <td className="num">{r.store}</td>
                <td>{r.name}</td>
                <td className="num">{r.period}</td>
                <td className="num">{r.sentAt}</td>
                <td><Pill kind={r.done ? 'ok' : 'wait'}>{r.status}</Pill></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function K2Create() {
  return (
    <>
      <PageHead
        title="สร้างเอกสารประกันรายได้"
        sub="สร้างเอกสารร้านถูกกระทบ — กรณีนอกเงื่อนไขของระบบ (Create New Document) และผ่านระบบ Finance & Account Unit (FS)"
        actions={<span className="pill info self-center">เลขที่เอกสารถัดไป · <b className="num">2569/00187</b></span>}
      />
      <Card>
        <Tabs
          tabs={[
            { key: 'manual', label: 'สร้างเอกสารใหม่ (นอกเงื่อนไข)', content: <ManualTab /> },
            { key: 'fs', label: 'สร้างเอกสารที่ FS', content: <FsTab /> },
          ]}
        />
      </Card>
    </>
  );
}
