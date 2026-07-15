import { http, HttpResponse, delay } from 'msw';
import { API_BASE } from '@/constants/api';
import {
  AUDIT, COMPETITORS, CONFIGS, DASHBOARD, DOCUMENT_DETAIL, EMAIL_TEMPLATES, FACTORS, JOBS,
  MENU_PERMISSIONS, OPERATORS, REPORT, ROLES, SECTIONS, STATUSES, STORES, TASKS,
} from './db';

const API = API_BASE;

/** ห่อเป็น { page, size, total, items } + รองรับ q/page/size อย่างง่าย */
function paged<T>(items: T[], url: URL, match?: (it: T, q: string) => boolean) {
  const q = (url.searchParams.get('q') || '').trim().toLowerCase();
  const page = Number(url.searchParams.get('page') || 1);
  const size = Number(url.searchParams.get('size') || 20);
  const filtered = q && match ? items.filter((it) => match(it, q)) : items;
  const start = (page - 1) * size;
  return { page, size, total: filtered.length, items: filtered.slice(start, start + size) };
}

export const handlers = [
  http.get(`${API}/dashboard/summary`, async () => {
    await delay(150);
    return HttpResponse.json(DASHBOARD);
  }),

  http.get(`${API}/tasks`, async ({ request }) => {
    await delay(200);
    return HttpResponse.json(
      paged(TASKS.filter((t) => t.currentSection !== 'END'), new URL(request.url), (t, q) =>
        [t.docNo, t.storeCode, t.storeName].some((v) => v.toLowerCase().includes(q)),
      ),
    );
  }),

  http.get(`${API}/documents`, async ({ request }) => {
    await delay(200);
    return HttpResponse.json(
      paged(TASKS, new URL(request.url), (t, q) =>
        [t.docNo, t.storeCode, t.storeName].some((v) => v.toLowerCase().includes(q)),
      ),
    );
  }),

  http.get(`${API}/documents/:docNo`, async ({ params }) => {
    await delay(180);
    const docNo = String(params.docNo);
    if (DOCUMENT_DETAIL[docNo]) return HttpResponse.json(DOCUMENT_DETAIL[docNo]);
    // สังเคราะห์รายละเอียดจาก TASKS ให้ทุกเอกสารเปิดได้
    const t = TASKS.find((x) => x.docNo === docNo);
    if (!t) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json({
      docNo: t.docNo,
      status: t.status,
      currentSection: t.currentSection,
      impactedStore: { storeCode: t.storeCode, storeName: t.storeName, region: t.region, storeType: 'FR Type B' },
      salesDropPercent: 12.45,
      compensateAmount: t.compensateAmount,
      newStores: [{ storeCode: '—', storeName: '(mock) ร้านเปิดใหม่', compensatePercent: 100, distanceKm: 0.8 }],
      competitors: [{ competitorCode: 'C007', competitorName: 'Lotus Express', impactDate: t.impactMonth }],
      factors: [{ factorCode: 'F001', factorName: 'ร้านคู่แข่งเปิดใหม่' }],
      timeline: [{ section: t.currentSection, considerName: 'ผู้ดำเนินการปัจจุบัน', result: 'อยู่ระหว่างพิจารณา', actionDateTime: '2026-06-15T10:00:00' }],
    });
  }),

  http.get(`${API}/reports/status-summary`, async ({ request }) => {
    await delay(220);
    return HttpResponse.json(paged(REPORT, new URL(request.url)));
  }),

  http.get(`${API}/operators`, async ({ request }) => {
    await delay(160);
    return HttpResponse.json(
      paged(OPERATORS, new URL(request.url), (o, q) =>
        [o.empName, o.empMail, o.sectionName].some((v) => v.toLowerCase().includes(q)),
      ),
    );
  }),

  http.get(`${API}/factors`, async () => {
    await delay(140);
    return HttpResponse.json({ items: FACTORS });
  }),

  http.get(`${API}/configs`, async ({ request }) => {
    await delay(140);
    const cat = new URL(request.url).searchParams.get('category');
    const items = cat ? CONFIGS.filter((c) => c.category === cat) : CONFIGS;
    return HttpResponse.json({ items });
  }),

  http.get(`${API}/jobs`, async () => {
    await delay(160);
    return HttpResponse.json({ items: JOBS });
  }),
  http.get(`${API}/jobs/:jobNo`, async ({ params }) => {
    await delay(160);
    const j = JOBS.find((x) => x.jobNo === String(params.jobNo));
    if (!j) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json({
      jobNo: j.jobNo,
      name: j.name,
      phase: j.phase,
      cron: j.cron,
      mainClass: `fcs.main.${j.name}`,
      desc: `งาน batch "${j.name}" (เฟส ${j.phase}) — รายละเอียดตามเอกสาร FGI/FCS Batch v4.0`,
      params: [
        { key: 'กำหนดการรัน (Cron)', value: j.cron, editable: true },
        { key: 'งวดข้อมูล', value: '07/2569', editable: true },
        { key: 'Batch Insert Size', value: '10000', editable: true },
        { key: 'SFTP Port', value: '218', editable: true },
        { key: 'Encoding', value: 'WINDOWS-874', editable: false },
      ],
      flow: [
        'เริ่ม — กำหนดงวดข้อมูล',
        'เชื่อมต่อแหล่งข้อมูล / SFTP ดาวน์โหลด/อ่านไฟล์',
        'ประมวลผลตามเงื่อนไข (dedup / validate / คำนวณ)',
        'ตรวจ reconcile จำนวนแถวก่อน commit',
        'เขียนผลลัพธ์ + บันทึก job_run_histories',
        'จบการทำงาน',
      ],
      db: [
        ['(target table ของ job)', 'W', 'เขียนผลลัพธ์'],
        ['job_configs', 'R', 'พารามิเตอร์ + cron'],
        ['job_run_histories', 'W', 'บันทึกรอบรัน'],
      ],
      runs: [
        { runId: 4451, status: j.lastStatus, rows: j.lastRows, file: 'ล่าสุด', startedAt: j.lastRunAt, durationSec: 252 },
        { runId: 4450, status: 'SUCCESS', rows: Math.round(j.lastRows * 0.98), file: '-', startedAt: '2026-06-30T06:00:00', durationSec: 240 },
        { runId: 4449, status: 'SUCCESS', rows: Math.round(j.lastRows * 1.02), file: '-', startedAt: '2026-06-29T06:00:00', durationSec: 261 },
      ],
    });
  }),

  http.get(`${API}/roles`, async () => {
    await delay(120);
    return HttpResponse.json({ items: ROLES });
  }),

  http.get(`${API}/menu-permissions`, async () => {
    await delay(150);
    return HttpResponse.json({ menus: MENU_PERMISSIONS });
  }),

  http.get(`${API}/email-templates`, async () => {
    await delay(130);
    return HttpResponse.json({ items: EMAIL_TEMPLATES });
  }),

  http.get(`${API}/competitors`, async () => {
    await delay(100);
    return HttpResponse.json({ items: COMPETITORS });
  }),

  http.get(`${API}/stores/search`, async ({ request }) => {
    await delay(120);
    const type = new URL(request.url).searchParams.get('type');
    const items =
      type === 'impacted'
        ? STORES.filter((s) => s.storeType === 'SP')
        : type === 'new'
          ? STORES.filter((s) => s.storeType === 'NEW')
          : STORES;
    return HttpResponse.json({ items });
  }),

  http.get(`${API}/document-statuses`, async () => HttpResponse.json({ items: STATUSES })),
  http.get(`${API}/workflow-sections`, async () => HttpResponse.json({ items: SECTIONS })),

  http.get(`${API}/audit-logs`, async ({ request }) => {
    const table = new URL(request.url).searchParams.get('table');
    const items = table ? AUDIT.filter((a) => a.tableName === table) : AUDIT;
    return HttpResponse.json({ items });
  }),

  /* ---------- Mutations (CRUD จริง — mutate in-memory แล้วสะท้อนเมื่อ refetch) ---------- */
  http.post(`${API}/factors`, async ({ request }) => {
    const b = (await request.json()) as { factorCode: string; factorName: string; factorRemark?: string };
    if (FACTORS.some((f) => f.factorCode === b.factorCode))
      return HttpResponse.json({ code: 'DUP_409', message: 'รหัสปัจจัยนี้มีอยู่แล้ว' }, { status: 409 });
    FACTORS.push({ factorCode: b.factorCode, factorName: b.factorName, factorRemark: b.factorRemark ?? '' });
    return HttpResponse.json({ factorCode: b.factorCode }, { status: 201 });
  }),
  http.put(`${API}/factors/:code`, async ({ params, request }) => {
    const b = (await request.json()) as { factorName: string; factorRemark?: string };
    const f = FACTORS.find((x) => x.factorCode === String(params.code));
    if (!f) return new HttpResponse(null, { status: 404 });
    f.factorName = b.factorName;
    f.factorRemark = b.factorRemark ?? f.factorRemark;
    return HttpResponse.json(f);
  }),
  http.delete(`${API}/factors/:code`, async ({ params }) => {
    const i = FACTORS.findIndex((x) => x.factorCode === String(params.code));
    if (i < 0) return new HttpResponse(null, { status: 404 });
    FACTORS.splice(i, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${API}/operators`, async ({ request }) => {
    const b = (await request.json()) as Omit<(typeof OPERATORS)[number], 'operatorAssignmentId'>;
    const id = Math.max(0, ...OPERATORS.map((o) => o.operatorAssignmentId)) + 1;
    OPERATORS.push({ ...b, operatorAssignmentId: id });
    return HttpResponse.json({ operatorAssignmentId: id }, { status: 201 });
  }),
  http.put(`${API}/operators/:id`, async ({ params, request }) => {
    const b = (await request.json()) as Partial<(typeof OPERATORS)[number]>;
    const o = OPERATORS.find((x) => x.operatorAssignmentId === Number(params.id));
    if (!o) return new HttpResponse(null, { status: 404 });
    Object.assign(o, b);
    return HttpResponse.json(o);
  }),
  http.delete(`${API}/operators/:id`, async ({ params }) => {
    const i = OPERATORS.findIndex((x) => x.operatorAssignmentId === Number(params.id));
    if (i < 0) return new HttpResponse(null, { status: 404 });
    OPERATORS.splice(i, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  http.put(`${API}/menu-permissions/:menuCode`, async ({ params, request }) => {
    const b = (await request.json()) as { access: Record<string, boolean> };
    const m = MENU_PERMISSIONS.find((x) => x.menuCode === String(params.menuCode));
    if (!m) return new HttpResponse(null, { status: 404 });
    Object.assign(m.access, b.access);
    return HttpResponse.json(m);
  }),
  http.post(`${API}/roles`, async ({ request }) => {
    const b = (await request.json()) as { roleCode: string; roleName: string; roleDesc: string };
    if (ROLES.some((r) => r.roleCode === b.roleCode))
      return HttpResponse.json({ code: 'DUP_409', message: 'รหัส Role ซ้ำ' }, { status: 409 });
    ROLES.push({ roleCode: b.roleCode, roleName: b.roleName, roleDesc: b.roleDesc, isSystem: false });
    MENU_PERMISSIONS.forEach((m) => (m.access[b.roleCode] = false));
    return HttpResponse.json({ roleCode: b.roleCode }, { status: 201 });
  }),
  http.put(`${API}/roles/:code`, async ({ params, request }) => {
    const b = (await request.json()) as { roleName: string; roleDesc: string };
    const r = ROLES.find((x) => x.roleCode === String(params.code));
    if (!r) return new HttpResponse(null, { status: 404 });
    r.roleName = b.roleName;
    r.roleDesc = b.roleDesc;
    return HttpResponse.json(r);
  }),
  http.delete(`${API}/roles/:code`, async ({ params }) => {
    const code = String(params.code);
    const r = ROLES.find((x) => x.roleCode === code);
    if (!r) return new HttpResponse(null, { status: 404 });
    if (r.isSystem) return HttpResponse.json({ code: 'SYS_409', message: 'Role หลักของระบบ ลบไม่ได้' }, { status: 409 });
    ROLES.splice(ROLES.indexOf(r), 1);
    MENU_PERMISSIONS.forEach((m) => delete m.access[code]);
    return new HttpResponse(null, { status: 204 });
  }),

  http.put(`${API}/configs/:key`, async ({ params, request }) => {
    const b = (await request.json()) as { value: string; reason?: string };
    const c = CONFIGS.find((x) => x.configKey === String(params.key));
    if (!c) return new HttpResponse(null, { status: 404 });
    if (!c.isEditable)
      return HttpResponse.json({ code: 'RO_422', message: 'ค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้' }, { status: 422 });
    c.value = b.value;
    return HttpResponse.json(c);
  }),

  http.put(`${API}/email-templates/:code`, async ({ params, request }) => {
    const b = (await request.json()) as { subject?: string; body?: string };
    const t = EMAIL_TEMPLATES.find((x) => x.templateCode === String(params.code));
    if (!t) return new HttpResponse(null, { status: 404 });
    if (b.subject !== undefined) t.subject = b.subject;
    if (b.body !== undefined) t.body = b.body;
    t.isCustomized = true;
    return HttpResponse.json(t);
  }),
  http.post(`${API}/email-templates/:code/reset`, async ({ params }) => {
    const t = EMAIL_TEMPLATES.find((x) => x.templateCode === String(params.code));
    if (!t) return new HttpResponse(null, { status: 404 });
    t.isCustomized = false;
    return HttpResponse.json(t);
  }),
];
