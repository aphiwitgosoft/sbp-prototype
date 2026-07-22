import type { ReactNode } from 'react';
import { PageHead } from '@/components/ui/PageHead';
import { Card, CardHead } from '@/components/ui/Card';
import { Chip } from '@/components/ui/Pill';
import { FlowchartSVG, type FcSpec } from '@/components/charts/FlowchartSVG';
import { TABLES, CROSS_KEYS, type Zone } from '@/data/schema';
import { cn } from '@/lib/cn';

const ZONE_COLOR: Record<Zone, string> = { A: '#2563eb', B: '#7c3aed', C: '#15803d' };
const SRC_STYLE: Record<string, string> = {
  'FGI/FCS': 'bg-blue-100 text-blue-700',
  K2: 'bg-violet-100 text-violet-700',
  'ใหม่': 'bg-green-100 text-green-700',
};

function SchemaTable({ zones }: { zones: Zone[] }) {
  const rows = TABLES.filter((t) => zones.includes(t.zone));
  return (
    <div className="table-wrap">
      <table className="data">
        <thead><tr><th>ตาราง</th><th>โซน</th><th>ที่มา</th><th>PK</th><th>FK / ความสัมพันธ์หลัก</th><th>บทบาท</th></tr></thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.name}>
              <td className="num font-medium">{t.name}</td>
              <td><span className="rounded px-1.5 py-0.5 text-[11px] font-bold text-white" style={{ background: ZONE_COLOR[t.zone] }}>{t.zone}</span></td>
              <td><span className={cn('rounded px-2 py-0.5 text-[11px] font-semibold', SRC_STYLE[t.source])}>{t.source}</span></td>
              <td className="num">{t.pk}</td>
              <td className="text-[12px] text-slate-600">{t.fk}</td>
              <td className="text-[12px] text-muted">{t.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Reference({ title, sub, chips, children }: { title: string; sub: string; chips?: string[]; children: ReactNode }) {
  return (
    <>
      <PageHead title={title} sub={sub} actions={chips && <div className="flex gap-2">{chips.map((c) => <Chip key={c}>{c}</Chip>)}</div>} />
      {children}
    </>
  );
}
function Section({ heading, items }: { heading: string; items: ReactNode[] }) {
  return (
    <Card className="mb-4">
      <CardHead title={heading} />
      <ul className="ml-5 list-disc space-y-1.5 text-[13.5px] leading-relaxed text-slate-600">
        {items.map((it, i) => <li key={i}>{it}</li>)}
      </ul>
    </Card>
  );
}

/* ---------------- Flow ---------------- */
const K2_FLOW: FcSpec = {
  w: 680, h: 440,
  nodes: [
    { id: 's06', type: 'proc', x: 210, y: 32, w: 300, text: '06 · ฝ่าย SBP DSA (ตรวจสอบ)' },
    { id: 's08', type: 'proc', x: 210, y: 110, w: 300, text: '08 · เจ้าหน้าที่ SBP DSA (คำนวณเงินชดเชย)' },
    { id: 's01', type: 'proc', x: 210, y: 188, w: 300, text: '01 · ฝ่ายส่งเสริมธุรกิจฯ (ปรับข้อมูล)' },
    { id: 's02', type: 'dec', x: 210, y: 284, w: 300, h: 76, text: '02 · GM OPT\nชดเชย > 100,000?' },
    { id: 's03', type: 'proc', x: 520, y: 284, w: 240, text: '03 · AVP OPT' },
    { id: 'end', type: 'termOk', x: 210, y: 410, w: 240, text: '99 · เสร็จสิ้นดำเนินการ' },
  ],
  edges: [
    { from: 's06', to: 's08' },
    { from: 's08', to: 's01' },
    { from: 's01', to: 's02' },
    { from: 's02', to: 's03', dir: 'right', label: '> 100,000' },
    { from: 's03', to: 'end', label: 'อนุมัติ' },
    { from: 's02', to: 'end', label: '≤ 100,000' },
  ],
};

const FGI_FLOW: FcSpec = {
  w: 720, h: 646,
  nodes: [
    { id: 't1', type: 'term', x: 220, y: 30, w: 340, text: 'AllMap → ข้อมูลร้านถูกกระทบ + คู่แข่ง' },
    { id: 'p1', type: 'proc', x: 220, y: 108, w: 340, text: 'Job 1 · ImportQSSI (คะแนน QSSI)' },
    { id: 'p2', type: 'proc', x: 220, y: 176, w: 340, text: 'Job 2–3 · Import ร้านถูกกระทบ/คู่แข่ง (ALLMAP)' },
    { id: 'p3', type: 'proc', x: 220, y: 244, w: 340, text: 'Job 4 · ขอยอดขายไป IAS' },
    { id: 'p4', type: 'proc', x: 220, y: 312, w: 340, text: 'Job 5 · รับยอดขาย + คำนวณ Growth Rate' },
    { id: 'd1', type: 'dec', x: 220, y: 402, w: 300, h: 74, text: 'ผ่าน Gen Flow Gate?' },
    { id: 'eN', type: 'err', x: 540, y: 402, w: 240, text: 'workflow_generation_status = N / W' },
    { id: 'p5', type: 'proc', x: 220, y: 500, w: 360, text: 'Job 8b · เปิด Workflow (06) + Job 6 ส่ง STA' },
    { id: 'end', type: 'termOk', x: 220, y: 578, w: 300, text: 'เข้าสู่ Approval Workflow (5 ขั้น)' },
  ],
  edges: [
    { from: 't1', to: 'p1' }, { from: 'p1', to: 'p2' }, { from: 'p2', to: 'p3' }, { from: 'p3', to: 'p4' },
    { from: 'p4', to: 'd1' },
    { from: 'd1', to: 'eN', dir: 'right', label: 'ไม่' },
    { from: 'd1', to: 'p5', label: 'ใช่' },
    { from: 'p5', to: 'end' },
  ],
};

export function FlowFgi() {
  const stages = [
    ['A', 'รับเข้า', 'QSSI · ALLMAP (Jobs 1–3)', '#2f6fed'],
    ['B', 'ยอดขาย', 'IAS + Growth (Jobs 4–5)', '#15b6a6'],
    ['C', 'ส่งออก', 'Document Service (แทน BPM)', '#7c3aed'],
    ['D', 'Workflow', 'เปิด instance + STA (Job 6/8b)', '#f59e0b'],
    ['E', 'เฝ้าระวัง', 'Watchdog ACK (Job 10)', '#ef4444'],
  ] as const;
  return (
    <Reference title="Flow FGI/FCS (Batch Pipeline)" sub="ท่อ batch รับ–วิเคราะห์–ส่งออก · Jobs 1–10 · เฟส A–E" chips={['FGI/FCS']}>
      <Card className="mb-4">
        <CardHead title="ภาพรวม Pipeline (เฟส A–E)" />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          {stages.map(([code, name, desc, color], i) => (
            <div key={code} className="relative rounded-card border border-line bg-white p-3.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg font-bold text-white" style={{ background: color }}>{code}</span>
              <div className="mt-2 font-semibold text-ink">{name}</div>
              <div className="mt-0.5 text-[12px] text-muted">{desc}</div>
              {i < stages.length - 1 && <span className="absolute -right-2 top-8 hidden text-slate-300 md:block">›</span>}
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <CardHead title="แผนภาพลำดับงาน (Flowchart)" right={<Chip>Gen Flow Gate</Chip>} />
        <div className="overflow-x-auto rounded-xl border border-line bg-slate-50/60 p-3.5">
          <FlowchartSVG spec={FGI_FLOW} />
        </div>
      </Card>
      <Card className="mt-4">
        <CardHead title="ตารางเวลา (Cron)" />
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>เวลา</th><th>Cron</th><th>Job</th><th>งาน</th></tr></thead>
            <tbody>
              {[
                ['ต้นเดือน', 'Monthly', 'Job 1', 'ImportQSSI — นำเข้าคะแนน QSSI'],
                ['07:00 (7)', '0 7 7 * *', 'Job 2–3', 'Import ร้านถูกกระทบ/คู่แข่ง (ALLMAP)'],
                ['16:00 (7–16)', '0 16 7-16 * *', 'Job 4', 'ขอยอดขายไป IAS'],
                ['16:30 (7–16)', '30 16 7-16 * *', 'Job 5', 'รับยอดขาย + คำนวณ Growth'],
                ['17:00 ทุกวัน', '0 17 * * *', 'Job 6', 'ส่งค่าชดเชยไป STA (FRBC0001)'],
                ['18:00 (7–31)', '0 18 7-31 * *', 'Job 8b', 'StartK2WorkFlow (เปิด workflow)'],
                ['17:30 (7–31)', '30 17 7-31 * *', 'Job 7/8/9', 'Export BPM (เดิม — ตัดทิ้งในระบบใหม่)'],
                ['07:00 ทุกวัน', '0 7 * * *', 'Job 10', 'Watchdog เฝ้าระวัง ACK ค้าง'],
              ].map((r, i) => (
                <tr key={i}><td className="num">{r[0]}</td><td className="num text-muted">{r[1]}</td><td className="num font-medium">{r[2]}</td><td>{r[3]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <Card className="mt-4">
        <CardHead title="Interface กับระบบภายนอก" />
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Interface</th><th>ทิศทาง</th><th>Encoding</th><th>เนื้อหา</th></tr></thead>
            <tbody>
              {[
                ['mrs1–5 (QSSI)', 'QSSI → SBPGI', 'WINDOWS-874', 'คะแนน QSSI รายเดือน'],
                ['ALLMAP (SQL Server)', 'ALLMAP → SBPGI', '-', 'ร้านถูกกระทบ + คู่แข่ง'],
                ['AMS06001O', 'SBPGI → MIS', 'UTF-8', 'คำขอยอดขาย (Job 4)'],
                ['AMS06001I', 'MIS → SBPGI', 'UTF-8', 'ยอดขายรายวัน (Job 5)'],
                ['FRBC0001', 'SBPGI → STA', 'WINDOWS-874 · พ.ศ.', 'ค่าชดเชย (Job 6)'],
                ['RT040035 / RT040078', 'STA → SBPGI', '-', 'ผลตั้ง Flow (Initial)'],
                ['COMPENSATE_INIT_I', 'STA callback', 'API', 'ACK ยอดตั้งต้น'],
                ['COMPENSATE_APPROVE_I', 'STA callback', 'API', 'ACK ยอดอนุมัติ'],
                ['SMTP', 'SBPGI → Email', 'UTF-8', 'แจ้งเตือนตามสถานะ'],
              ].map((r, i) => (
                <tr key={i}><td className="num font-medium">{r[0]}</td><td>{r[1]}</td><td className="num text-muted">{r[2]}</td><td>{r[3]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Reference>
  );
}

export function K2Flow() {
  return (
    <Reference title="Flow K2 (Approval Workflow)" sub="เส้นทางพิจารณา 5 ขั้น · 06→08→01→02→03" chips={['K2', '5 ขั้น']}>
      <Card className="mb-4">
        <CardHead title="แผนภาพเส้นทางพิจารณา (Flowchart)" right={<Chip>กฎวงเงิน 100,000</Chip>} />
        <div className="overflow-x-auto rounded-xl border border-line bg-slate-50/60 p-3.5">
          <FlowchartSVG spec={K2_FLOW} />
        </div>
      </Card>
      <Section
        heading="กติกา routing"
        items={[
          'ชดเชย > 100,000 ต้องผ่าน AVP (03) แล้วจบงาน · ชดเชย ≤ 100,000 จบที่ GM (02)',
          '06 ไม่ชดเชย/หยุดชดเชย → เสร็จสิ้น · ทุกขั้นมีเส้นส่งกลับ (back-flow)',
          'ผลพิจารณาบันทึก consideration_logs + ส่งอีเมลตาม status_email_rules',
        ]}
      />
      <Card className="mb-4">
        <CardHead title="ตารางเส้นทางพิจารณา (Transitions)" />
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Section</th><th>ผู้ดำเนินการ</th><th>ตัวเลือกส่งงาน / เงื่อนไข</th><th>สถานะถัดไป</th></tr></thead>
            <tbody>
              {[
                ['06', 'ฝ่าย SBP DSA', 'ไม่ชดเชย/หยุดชดเชย · ส่ง 01 · ส่ง 08', '99 / 01 / 08'],
                ['08', 'เจ้าหน้าที่ SBP DSA', 'คำนวณเงินชดเชยเรียบร้อย · ส่งกลับ', '01 / 06'],
                ['01', 'ฝ่ายส่งเสริมธุรกิจฯ', 'เห็นควรชดเชย · ไม่ชดเชย/ส่งกลับ', '02 / 06'],
                ['02', 'GM OPT', 'ชดเชย > 100,000 → 03 · ≤ 100,000 → จบ · ไม่ชดเชย/ส่งกลับ', '03 / 99 / 06'],
                ['03', 'AVP OPT', 'เห็นควรชดเชย → จบ · ไม่ชดเชย · ส่งกลับ', '99 / 06 / 02'],
              ].map((r, i) => (
                <tr key={i}><td className="num font-medium">{r[0]}</td><td>{r[1]}</td><td className="text-[12px]">{r[2]}</td><td className="num">{r[3]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <Card>
        <CardHead title="สถานะเอกสาร → ผู้รับอีเมล (status_email_rules)" />
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>State</th><th>สถานะเอกสาร</th><th>อีเมลถึง (TO)</th><th>สำเนา (CC)</th></tr></thead>
            <tbody>
              {[
                ['06', 'รอฝ่าย SBP DSA ดำเนินการ', 'ฝ่าย SBP DSA', '-'],
                ['08', 'รอเจ้าหน้าที่ SBP DSA ดำเนินการ', 'เจ้าหน้าที่ SBP DSA', 'ฝ่าย SBP DSA'],
                ['01', 'รอฝ่ายส่งเสริมธุรกิจ SBP', 'ฝ่ายส่งเสริมธุรกิจฯ', '-'],
                ['02', 'รอ GM ส่งเสริมธุรกิจ SBP', 'GM OPT', 'ฝ่ายส่งเสริมธุรกิจฯ'],
                ['03', 'รอผู้บริหารสำนักบริหาร SBP', 'AVP OPT', 'GM OPT'],
                ['99', 'เสร็จสิ้นดำเนินการ', 'ฝ่าย SBP DSA', '-'],
                ['BACK', 'ส่งกลับ', 'ผู้ดำเนินการขั้นก่อนหน้า', '-'],
              ].map((r, i) => (
                <tr key={i}><td className="num font-medium">{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td className="text-muted">{r[3]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[12px] text-muted">กฎวงเงิน: ชดเชย/ไม่ชดเชย &gt; 100,000 ต้องผ่าน AVP (03) เสมอ</p>
      </Card>
    </Reference>
  );
}

export function PlanFlow() {
  return (
    <Reference title="Flow FGI/FCS + K2 (รวม)" sub="flow ต้นทางถึงปลายทางของระบบใหม่ SBPGI (รวม EAI + K2)" chips={['12 ขั้น', 'workflow.md']}>
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[['11', 'Batch Jobs (1–10 + 8b)'], ['5', 'ขั้น workflow อนุมัติ'], ['34', 'ตารางใน DB รวม'], ['62', 'REST API endpoints']].map(([n, l]) => (
          <div key={l} className="rounded-card border border-line bg-card p-4 text-center shadow-card">
            <div className="text-2xl font-bold text-primary">{n}</div>
            <div className="mt-1 text-[12px] text-muted">{l}</div>
          </div>
        ))}
      </div>
      <Card className="mb-4">
        <CardHead title="เปรียบเทียบ lane (เดิม → ใหม่)" />
        <LaneCompare />
      </Card>
      <Section
        heading="แนวคิดระบบใหม่"
        items={[
          'รวม EAI และ K2 เข้าเป็นส่วนหนึ่งของ SBPGI — ไม่ส่งไฟล์ข้ามระบบผ่าน EAI อีกต่อไป',
          'ไฟล์ BPM06001O/2O/3O + K2 REST StartInstance → แทนด้วย Document Service เขียน DB ตรง + Workflow Engine ภายใน',
          'interface ภายนอก (QSSI/ALLMAP/IAS/STA/SMTP) คงกลไกไฟล์/SFTP เดิม',
          'รายละเอียดเต็มดู workflow.md',
        ]}
      />
      <Card>
        <CardHead title="Migration Map — จุดเชื่อมต่อที่เปลี่ยน" />
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>จุดเชื่อมต่อ</th><th>กลไกเดิม</th><th>กลไกใหม่</th></tr></thead>
            <tbody>
              {[
                ['ส่งข้อมูลเข้าระบบเอกสาร', 'ไฟล์ BPM06001O/2O/3O ผ่าน EAI (Jobs 7/8/9)', 'Document Service เขียน DB ตรง'],
                ['เปิด Workflow', 'Job 8b ยิง K2 REST StartInstance', 'Workflow Engine ภายใน · POST /workflows/instances'],
                ['รับ ACK จาก STA', 'รอ STA อัปเดต return_code · Job 10 ตรวจเช้า', 'เพิ่ม POST /interfaces/sta/ack · Job 10 เป็น safety net'],
                ['ตาราง tracking', 'FGI_CONFIRM_RECEIVE_DATA (polymorphic + บั๊ก purge)', 'interface_transactions (typed FK)'],
                ['อีเมลแจ้งเตือน', 'แต่ละ job ต่อ SMTP เอง · TIS-620', 'Notification Service กลาง · UTF-8'],
                ['Interface ภายนอก', 'SFTP + encoding เฉพาะ', 'คงเดิม + credential ไป Secret Manager'],
                ['สิทธิ์ผู้ใช้/เมนู', 'ตารางสิทธิ์ใน BPM', 'Auth & RBAC + JWT · menu_permissions'],
              ].map((r, i) => (
                <tr key={i}><td className="font-medium">{r[0]}</td><td className="text-[12px] text-muted">{r[1]}</td><td className="text-[12px]">{r[2]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Reference>
  );
}

/* ---------------- Database (zone map) ---------------- */
function ZoneMap({ zones }: { zones: { name: string; color: string; tables: string[] }[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {zones.map((z) => (
        <div key={z.name} className="rounded-card border p-3" style={{ borderColor: z.color }}>
          <div className="mb-2 text-[13px] font-bold" style={{ color: z.color }}>{z.name}</div>
          <div className="flex flex-col gap-1.5">
            {z.tables.map((t) => (
              <code key={t} className={cn('rounded-md border border-line bg-white px-2.5 py-1.5 font-mono text-[12px] text-slate-700')}>{t}</code>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function DataSpine() {
  const nodes = [
    { z: 'A', code: 'impact_process_id', color: '#2f6fed', desc: 'หนึ่งร้าน + หนึ่งงวด' },
    { z: 'B', code: 'doc_no', color: '#7c3aed', desc: 'เอกสาร YYYY/xxxxx' },
    { z: 'B', code: 'instance_id', color: '#7c3aed', desc: 'workflow instance' },
    { z: 'B', code: 'task_id', color: '#7c3aed', desc: 'งานต่อ Section (inbox)' },
    { z: 'C', code: 'employee_id / role_code', color: '#16a34a', desc: 'ผู้ใช้ + สิทธิ์' },
  ];
  return (
    <div className="flex flex-wrap items-center gap-2">
      {nodes.map((n, i) => (
        <div key={n.code} className="flex items-center gap-2">
          <div className="min-w-[150px] rounded-card border border-line bg-white p-3">
            <span className="rounded px-1.5 py-0.5 text-[11px] font-bold text-white" style={{ background: n.color }}>{n.z}</span>
            <div className="mt-1.5 font-mono text-[12px] font-semibold text-primary">{n.code}</div>
            <div className="text-[11px] text-muted">{n.desc}</div>
          </div>
          {i < nodes.length - 1 && <span className="text-lg text-slate-300">›</span>}
        </div>
      ))}
    </div>
  );
}

function LaneCompare() {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <div className="rounded-card border border-line p-3">
        <div className="mb-1.5 text-[13px] font-semibold text-slate-500">ระบบเดิม (7 lanes)</div>
        <div className="flex flex-wrap gap-1.5">{['AllMap', 'SBPGI', 'MIS', 'EAI', 'STA', 'SAP', 'K2'].map((l) => <span key={l} className={cn('chip', (l === 'EAI' || l === 'K2') && 'bg-red-100 text-red-700')}>{l}</span>)}</div>
        <div className="mt-2 text-[12px] text-muted">EAI + K2 แยกระบบ · ส่งไฟล์ BPM06001O/2O/3O ข้ามระบบ</div>
      </div>
      <div className="rounded-card border border-primary/40 p-3">
        <div className="mb-1.5 text-[13px] font-semibold text-primary">ระบบใหม่ (5 lanes)</div>
        <div className="flex flex-wrap gap-1.5">{['AllMap', 'SBPGI', 'MIS', 'STA', 'SAP'].map((l) => <span key={l} className="chip">{l}</span>)}</div>
        <div className="mt-2 text-[12px] text-muted">รวม EAI + K2 เข้า SBPGI · เขียน DB ตรง + Workflow ภายใน</div>
      </div>
    </div>
  );
}

export function FgiDatabase() {
  return (
    <Reference title="DB FGI/FCS" sub="สคีมาท่อ impact pipeline (Zone A)" chips={['Zone A · 7 ตาราง']}>
      <Card>
        <CardHead title="Zone A · Impact Pipeline" />
        <ZoneMap zones={[{ name: 'Zone A · FGI/FCS', color: '#1d4ed8', tables: ['fgi_impact_processes ★', 'fgi_impact_stores', 'fgi_impact_sales_summaries', 'sales_transactions', 'fgi_impact_competitors', 'fcs_qssi_scores', 'interface_transactions'] }]} />
      </Card>
      <Card className="mt-4">
        <CardHead title="Data Dictionary — Zone A" />
        <SchemaTable zones={['A']} />
      </Card>
    </Reference>
  );
}

export function K2Database() {
  return (
    <Reference title="DB K2" sub="สคีมาเอกสาร + workflow (Zone B)" chips={['Zone B · 9 ตาราง']}>
      <Card>
        <CardHead title="Zone B · เอกสาร & Workflow" />
        <ZoneMap zones={[{ name: 'Zone B · K2', color: '#6d28d9', tables: ['compensation_documents', 'document_new_stores', 'document_competitors', 'document_external_factors', 'consideration_logs', 'document_attachments', 'compensation_histories', 'workflow_instances', 'workflow_tasks'] }]} />
      </Card>
      <Card className="mt-4">
        <CardHead title="Data Dictionary — Zone B" />
        <SchemaTable zones={['B']} />
      </Card>
    </Reference>
  );
}

export function PlanDatabase() {
  return (
    <Reference title="DB FGI/FCS + K2 (รวม)" sub="Target Schema 34 ตาราง · 3 โซน (A/B/C)" chips={['34 ตาราง', 'database.md']}>
      <Card className="mb-4">
        <CardHead title="Data Spine — เส้นทางข้อมูลหลัก" right={<Chip>เริ่มอ่านตรงนี้</Chip>} />
        <div className="overflow-x-auto pb-1"><DataSpine /></div>
      </Card>
      <Card>
        <CardHead title="แผนภาพโซนข้อมูล (Zone Map)" right={<Chip>4 Core IDs</Chip>} />
        <ZoneMap
          zones={[
            { name: 'Zone A · FGI/FCS', color: '#1d4ed8', tables: ['fgi_impact_processes ★', 'fgi_impact_stores', 'fgi_impact_sales_summaries', 'sales_transactions', 'fgi_impact_competitors', 'fcs_qssi_scores', 'interface_transactions'] },
            { name: 'Zone B · K2', color: '#6d28d9', tables: ['compensation_documents', 'document_new_stores', 'document_competitors', 'consideration_logs', 'document_attachments', 'compensation_histories', 'workflow_instances', 'workflow_tasks'] },
            { name: 'Zone C · Shared', color: '#15803d', tables: ['stores', 'impacted_stores', 'employees', 'roles / menus / menu_permissions', 'operator_assignments', 'external_factors', 'competitors', 'audit_logs', 'status_email_rules', 'email_templates', 'user_accounts', 'system_configs', 'job_configs / job_run_histories'] },
          ]}
        />
      </Card>
      <Card className="mt-4">
        <CardHead title="Data Dictionary — 34 ตาราง (A · B · C)" right={<Chip>ทั้ง 3 โซน</Chip>} />
        <SchemaTable zones={['A', 'B', 'C']} />
      </Card>
      <Card className="mt-4">
        <CardHead title="กุญแจเชื่อมข้ามระบบ (Cross-System Keys)" />
        <ul className="ml-5 list-disc space-y-1.5 text-[13px] leading-relaxed text-slate-600">
          {CROSS_KEYS.map((k, i) => <li key={i}>{k}</li>)}
        </ul>
      </Card>
      <Card className="mt-4">
        <CardHead title="ข้อปรับปรุงจากระบบเดิม" right={<span className="pill fail font-semibold">P0 × 3 · P1 × 4</span>} />
        <ol className="ml-5 list-decimal space-y-1.5 text-[13px] leading-relaxed text-slate-600">
          {[
            'เลิก polymorphic FK — interface_transactions ใช้ typed FK แยกคอลัมน์ (P1)',
            'บังคับ status domain ด้วย enum/check constraint (W/P/Y/N · I/C/A/N/S/Z ฯลฯ)',
            'ครอบ Job 4 ด้วย transaction (outbox pattern) — P0 อันดับหนึ่ง',
            'แก้บั๊ก purge tracking (E20) — ต้องทำพร้อม data migration + test',
            'ทบทวน NULL → auto-accept ของ Job 5 (P1) — ตั้ง "รอตรวจสอบ" แทน',
            'ย้าย credential ไป Secret Manager + บังคับ TLS (P0)',
            'ใช้ identity ต่อตารางแทน sequence รวม (Errata E18)',
            'golden-file tests ต่อ interface ภายนอก (encoding/พ.ศ./ชื่อประกอบ)',
          ].map((t, i) => <li key={i}>{t}</li>)}
        </ol>
      </Card>
    </Reference>
  );
}
