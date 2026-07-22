import { Link } from 'react-router-dom';
import type { LucideIcon } from 'lucide-react';
import {
  ShieldCheck, ClipboardCheck, Store, Wallet, AlertTriangle,
  FilePlus2, Package, FileText, Users, Database, Lock, ChevronRight,
} from 'lucide-react';
import { Card, CardHead } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Pill } from '@/components/ui/Pill';
import { ColumnChart } from '@/components/charts/ColumnChart';
import { HBarChart } from '@/components/charts/HBarChart';
import { ROUTES } from '@/constants/routes';
import type { PillKind } from '@/types';

const MONTHLY = [
  { label: 'พ.ย.', value: 5.2 }, { label: 'ธ.ค.', value: 6.1 }, { label: 'ม.ค.', value: 5.8 },
  { label: 'ก.พ.', value: 7.4 }, { label: 'มี.ค.', value: 6.9 }, { label: 'เม.ย.', value: 8.0 },
  { label: 'พ.ค.', value: 7.6 }, { label: 'มิ.ย.', value: 8.42 },
];
const PIPELINE = [
  { label: '06 · รอฝ่าย SBP DSA', dot: '#f59e0b', value: 24 },
  { label: '08 · รอเจ้าหน้าที่ SBP DSA', dot: '#7c3aed', value: 12 },
  { label: '01 · รอฝ่ายส่งเสริมธุรกิจ SBP', dot: '#2563eb', value: 18 },
  { label: '02 · รอ GM ส่งเสริมธุรกิจ SBP', dot: '#ea580c', value: 9 },
  { label: '03 · รอผู้บริหารสำนักบริหาร SBP', dot: '#4f46e5', value: 4 },
  { label: 'เสร็จสิ้นดำเนินการ (เดือนนี้)', dot: '#16a34a', value: 73 },
];

const DOC = ROUTES.document('2569/00123');
const MODULES_CARDS: { to: string; icon: LucideIcon; bg: string; title: string; code: string; desc: string; cta: string }[] = [
  { to: ROUTES.docsWaiting, icon: ShieldCheck, bg: 'bg-success', title: 'เอกสาร — รอดำเนินการ / ที่เกี่ยวข้อง', code: 'Workflow Inbox', desc: 'inbox ต่อบทบาท: เห็นเฉพาะเอกสารสถานะ "รอ<บทบาทของท่าน>ดำเนินการ" พร้อมสลับมุมมอง 5 ขั้นตอน ค้นหา กรอง และเปิดเอกสารเพื่อพิจารณา/ส่งดำเนินการ', cta: 'เข้าสู่งาน' },
  { to: ROUTES.create, icon: FilePlus2, bg: 'bg-primary', title: 'สร้างเอกสาร', code: 'Create New / FS', desc: 'สร้างเอกสารร้านถูกกระทบกรณีนอกเงื่อนไขของระบบ (เลขที่ YYYY/Running 5 หลัก) และสร้างผ่านระบบ Finance & Account Unit (FS) รอ SBP Statement ส่งกลับ ~1 วัน', cta: 'สร้างเอกสาร' },
  { to: DOC, icon: Package, bg: 'bg-brandteal', title: 'เอกสารข้อมูลร้านถูกกระทบ', code: 'Workflow Document', desc: 'หน้าจอหลักของกระบวนการ — ข้อมูลร้านถูกกระทบ ร้านเปิดใหม่ แผนที่ ALLMAP ร้านคู่แข่ง ปัจจัยอื่น ๆ ประวัติการชดเชย ผลการพิจารณา เอกสารแนบ คำนวณเงิน และส่งดำเนินการตาม Role', cta: 'เปิดเอกสาร' },
  { to: ROUTES.report, icon: FileText, bg: 'bg-violet-500', title: 'รายงานสรุปสถานะ', code: 'Report · Export Excel', desc: 'ค้นหา ติดตาม และ Export รายงานเอกสารประกันรายได้ ตามรหัสร้าน ภาค ประเภทร้าน สถานะ และ Period Statement (ผลลัพธ์ 19 คอลัมน์)', cta: 'ออกรายงาน' },
  { to: ROUTES.operators, icon: Users, bg: 'bg-warn', title: 'กำหนดชื่อผู้ปฏิบัติงาน', code: 'Master · operator_assignments', desc: 'กำหนดว่าพนักงานคนใดรับผิดชอบตำแหน่งหรือขั้นตอนใดใน Workflow บันทึกประวัติการเพิ่ม/แก้ไขใน audit_logs', cta: 'จัดการข้อมูล' },
  { to: ROUTES.factors, icon: Database, bg: 'bg-primary', title: 'กำหนดปัจจัยภายนอก', code: 'Master · external_factors', desc: 'จัดการ Master ข้อมูลปัจจัยภายนอกที่อาจกระทบยอดขาย รหัสปัจจัยห้ามซ้ำ บันทึกใน external_factors และ audit_logs', cta: 'จัดการข้อมูล' },
  { to: ROUTES.permissions, icon: Lock, bg: 'bg-danger', title: 'สิทธิ์การเข้าถึงเมนู', code: 'RBAC · SRS 3.1.1', desc: 'ตารางสิทธิ์ 8 กลุ่มบทบาท (00 Default – 10 UserViewer) ต่อเมนูของระบบ ใช้เป็นแหล่งข้อมูล RBAC ของ Auth ในระบบใหม่', cta: 'ดูสิทธิ์' },
];

const ACTIVITY: { kind: PillKind; label: string; text: string; time: string }[] = [
  { kind: 'ok', label: 'เสร็จสิ้น', text: 'อนุมัติเอกสาร 2569/00152 แคราย พลาซ่า → เสร็จสิ้นดำเนินการ', time: '09:24' },
  { kind: 'violet', label: 'คำนวณเงิน', text: 'คำนวณเงินชดเชยเรียบร้อย เอกสาร 2569/00140 → รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ', time: '08:50' },
  { kind: 'navy', label: 'AVP', text: 'เอกสาร 2569/00194 วงเงิน 104,500 บาท → รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', time: '08:12' },
  { kind: 'fail', label: 'แถวแดง', text: 'ร้านยอดขายไม่ครบ 60 วัน 5 รายการ ในคิวรอฝ่าย SBP DSA ดำเนินการ', time: '07:40' },
];

export default function Overview() {
  return (
    <>
      {/* Hero */}
      <section className="relative mb-6 overflow-hidden rounded-card bg-gradient-to-br from-primary to-primary-dark p-8 text-white shadow-card">
        <ShieldCheck className="pointer-events-none absolute -right-3 -top-4 h-48 w-48 text-white/10" strokeWidth={1} />
        <h1 className="relative text-[26px] font-semibold">สวัสดี, คุณภัชริดา</h1>
        <p className="relative mt-2 max-w-3xl text-[13.5px] leading-relaxed text-white/85">
          ระบบประกันรายได้ — ชดเชยรายได้ร้าน 7-11 Franchise ที่ได้รับผลกระทบจากร้านเปิดใหม่ในรัศมีใกล้เคียง เอกสารเดินตาม Workflow 5 ขั้นตอน (06 → 08 → 01 → 02 → 03) จนเสร็จสิ้นดำเนินการ · วงเงิน &gt; 100,000 ผ่าน AVP
        </p>
        <div className="relative mt-5 flex flex-wrap gap-3">
          <Link to={ROUTES.docsWaiting} className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-[13.5px] font-medium text-primary hover:bg-white/90">
            <ClipboardCheck size={18} /> งานรอท่านดำเนินการ
          </Link>
          <Link to={DOC} className="inline-flex items-center gap-2 rounded-lg border border-white/50 px-4 py-2 text-[13.5px] font-medium text-white hover:bg-white/10">
            <FileText size={18} /> เอกสารร้านถูกกระทบ
          </Link>
        </div>
      </section>

      {/* Stat grid */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={ClipboardCheck} tone="blue" value={24} label="เอกสารรอท่านดำเนินการ" />
        <StatCard icon={Store} tone="teal" value={342} label="สาขาประกันรายได้เดือนนี้" />
        <StatCard icon={Wallet} tone="amber" value="8.42" label="ยอดชดเชยเดือนนี้ (ล้านบาท)" />
        <StatCard icon={AlertTriangle} tone="rose" value={5} label="ยอดขายไม่ครบ 60 วัน (แถวแดง)" />
      </div>

      {/* Charts */}
      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="text-[15px] font-semibold text-ink">ยอดชดเชยประกันรายได้รายเดือน</h3>
          <div className="mb-2 text-[12px] text-muted">หน่วย: ล้านบาท · 8 เดือนล่าสุด</div>
          <ColumnChart rows={MONTHLY} />
        </Card>
        <Card className="lg:col-span-2">
          <h3 className="text-[15px] font-semibold text-ink">เอกสารค้างตามขั้นตอน Workflow</h3>
          <div className="mb-2 text-[12px] text-muted">สถานะ "รอ&lt;ผู้ดำเนินการ&gt;ดำเนินการ" ต่อ Section + เสร็จสิ้นเดือนนี้ · จุดสี = สีสถานะทั้งระบบ</div>
          <HBarChart rows={PIPELINE} />
        </Card>
      </div>

      {/* Module grid */}
      <h2 className="mb-3 text-[17px] font-semibold text-ink">หน้าจอระบบประกันรายได้</h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {MODULES_CARDS.map((m) => (
          <Link key={m.title} to={m.to} className="group flex flex-col rounded-card border border-line bg-card p-5 shadow-card transition-shadow hover:shadow-md">
            <div className="mb-2.5 flex items-center gap-3">
              <span className={`flex h-12 w-12 flex-none items-center justify-center rounded-xl text-white ${m.bg}`}><m.icon size={26} strokeWidth={1.8} /></span>
              <div>
                <div className="font-semibold text-ink">{m.title}</div>
                <div className="text-[12px] text-muted">{m.code}</div>
              </div>
            </div>
            <div className="flex-1 text-[13px] leading-relaxed text-slate-600">{m.desc}</div>
            <span className="mt-3 inline-flex items-center gap-1 text-[13px] font-medium text-primary">{m.cta}<ChevronRight size={16} className="transition-transform group-hover:translate-x-0.5" /></span>
          </Link>
        ))}
      </div>

      {/* Bottom: activity + quick links */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHead title="กิจกรรมล่าสุด" />
          <div className="flex flex-col divide-y divide-slate-100">
            {ACTIVITY.map((a, i) => (
              <div key={i} className="flex items-center gap-3 py-2.5">
                <Pill kind={a.kind}>{a.label}</Pill>
                <span className="flex-1 text-[13px] text-slate-600">{a.text}</span>
                <span className="num text-[12.5px] text-slate-400">{a.time}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <CardHead title="ทางลัด" />
          <div className="flex flex-col gap-2.5">
            <Link to={ROUTES.docsWaiting} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-[13.5px] font-medium text-white hover:bg-primary-dark"><ClipboardCheck size={18} /> งานรอท่านดำเนินการ</Link>
            <Link to={DOC} className="inline-flex items-center gap-2 rounded-lg bg-primary-soft px-4 py-2 text-[13.5px] font-medium text-primary hover:bg-blue-100"><FileText size={18} /> เปิดเอกสารร้านถูกกระทบ</Link>
            <Link to={ROUTES.report} className="inline-flex items-center gap-2 rounded-lg border border-line px-4 py-2 text-[13.5px] font-medium text-slate-600 hover:bg-slate-50"><FileText size={18} /> ออกรายงานสรุปสถานะ</Link>
          </div>
        </Card>
      </div>
    </>
  );
}
