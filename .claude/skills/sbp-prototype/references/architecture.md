# Architecture — โครงสร้าง prototype และวิธีแก้ไข

3 ส่วนเคลื่อนไหว: หน้า HTML ~18 หน้า · stylesheet เดียว `assets/sbp.css` · script เดียว `assets/sbp.js` (ES5 IIFE ไม่มี dependency)
Header และ sidebar **ไม่อยู่ใน HTML** — `sbp.js` inject ตอน runtime ทุกหน้า

## Page contract (ทุกหน้าต้องเป็นแบบนี้)

```html
<body data-page="k2-report" data-nav="modules" data-module="k2-report" data-crumb="รายงานสรุปสถานะ">
<div class="layout">
  <aside id="sidebar"></aside>          <!-- ต้องว่างเสมอ sbp.js เติมเอง -->
  <main class="content">…เนื้อหา…</main>
</div>
<div id="toast-stack"></div>
<script src="assets/sbp.js"></script>
<!-- JS เฉพาะหน้าใส่ inline <script> หลัง sbp.js เพื่อให้ window.SBP.toast มีแล้ว -->
```

- `data-page`/`data-module` = ชื่อไฟล์ไม่มีนามสกุล · `data-crumb` = breadcrumb ใบสุดท้าย
- CSS เฉพาะหน้า → inline `<style>` ใน head ของหน้านั้น · **ไม่มีไฟล์ asset ต่อหน้า**
- ใช้ `k2-document.html` เป็น template หน้าใหม่ (`index.html` เป็น redirect stub ไป `k2-list-waiting.html` แล้ว — ไม่ตาม page contract อย่า copy)
- Public API มีแค่ `window.SBP.toast(msg, kind)` — kind: `'ok'` / `'del'` / ว่าง

**เพิ่มหน้า = 2 ขั้น**: สร้างไฟล์ตาม contract + เพิ่ม entry ใน `MODULES` (sbp.js ~บรรทัด 55): `{key, label, href, icon, group}`
กลุ่ม sidebar render ตามลำดับที่พบครั้งแรก ปัจจุบัน: `ระบบประกันรายได้ (SBP Mall)` → `ผู้ดูแลระบบ (Admin)` → `Flow` → `Database` → `Plan`
Entry แบบมี `children: [{key,label,href}]` (ไม่มี href บนแม่) = submenu พับได้ — ใช้กับเมนู เอกสาร
**อย่าใช้** โหมด `data-nav="application"` / `switchStep()` / `APP_SECTIONS` — legacy ของหน้าที่ถูกลบไปแล้ว

## Behavior hooks (declarative ผ่าน attribute — delegated click handler เดียวใน sbp.js)

| Hook | ผล |
|---|---|
| `data-href` | นำทางเมื่อคลิก |
| `data-toast` / `data-ack` (+ `data-kind="ok\|del"`) | ยิง toast แทน action จริง |
| `table.data` + ปุ่ม `.icon-view/.icon-edit/.icon-del` | modal view/edit อัตโนมัติ + confirm ลบ |
| `[data-add-row="tableId"]` | modal เพิ่มแถว |
| `data-entity` บนตาราง | เลือก schema จาก `SCHEMAS` (sbp.js ~บรรทัด 424) — **field map กับคอลัมน์ด้วยข้อความ `<th>` แบบตรงตัว** เปลี่ยนชื่อ th = modal พังเงียบ |
| `data-entity="k2doc"` | ข้าม modal — เติมข้อมูลลง panel `#openedDoc` แทน |
| `[data-tabs]` + `.tab[data-tab=key]` | toggle ทุก `[data-tabpane]` **ทั้ง document** ที่ key ไม่ตรง |
| `<div data-chart="bar\|donut\|spark" data-values data-labels...>` | SVG chart inline — diagram อื่น (BPMN, ER, แผนที่) เป็น SVG เขียนมือทั้งหมด |

## Styling

- Design tokens ใน `:root` ของ sbp.css — `--primary` #2f6fed (accent หลัก) · `--seven-*` ใช้กับโลโก้ header **เท่านั้น**
- `.pill` = สถานะ (มีจุด) · `.chip` = ป้ายข้อมูล — **ห้ามสลับกัน**
- `table.data` ต้องห่อด้วย `.table-wrap` (horizontal scroll)
- `.reveal` มองไม่เห็นจนกว่า JS เติม `.in` · modal ต้องมีทั้ง `display:flex` และ `.show`
- header สูง `--header-h` (64px) — ของ sticky ใต้ header ใช้ `top:calc(var(--header-h) + 10px)`

## รายการหน้า

| กลุ่ม | ไฟล์ | คือ |
|---|---|---|
| หลัก | ~~`index.html`~~ | **ตัดออก 2026-08-06** — Overview ไม่ใช้แล้ว เหลือเป็น redirect stub ไปหน้าแรกจริง (`k2-list-waiting.html`) |
| | `k2-create.html` | **หน้าอธิบายกระบวนการ (ไม่มีฟอร์ม/แท็บ · 2026-08-06)** — สร้างข้อมูลต้นทางที่ FS แล้วรอ SBP Statement ส่งกลับ ~1 วัน |
| | `k2-list-waiting.html` / `k2-list-related.html` | รอดำเนินการ / ที่เกี่ยวข้อง — **ฝาแฝด ต่างแค่ `MODE` const, title, body attrs — แก้ทั้งคู่เสมอ** |
| | ~~`k2-list-abnormal.html`~~ | ข้อมูลผิดปกติ/แจกงาน — **ลบไฟล์ทิ้งแล้ว 2026-08-06** พร้อมเมนู/กลุ่ม API · เหลือเป็นธงแถวแดง + ตัวกรองในหน้ารอดำเนินการ |
| | `k2-document.html` | หน้าเอกสารร้านถูกกระทบ (SRS 3.1.6 — ซับซ้อนสุด) มี dropdown สลับ role demo 7 มุมมองผ่าน `data-editrole`/`data-roleonly`/`.edit-only` · **ไม่อยู่ใน sidebar** เข้าจากคลิกแถวตาราง |
| | `k2-report.html` | รายงานสรุปสถานะ — **ตัวกรอง 7 ตัว / ผลลัพธ์ 14 คอลัมน์ ตาม SDD สไลด์ 60** (SRS 3.1.7 · ปรับ 2026-08-06) |
| | `k2-factors.html` | master ปัจจัยภายนอก (3.1.9) |
| | ~~`k2-operators.html`~~ / ~~`k2-permissions.html`~~ | **ถอดจาก sidebar 2026-08-05** — ผู้ปฏิบัติงาน (3.1.8) + สิทธิ์เมนู (3.1.1) ใช้ระบบ SBP เดิม (auth-backend) · ไฟล์เก็บไว้อ้างอิง |
| ~~Admin~~ | ~~`system-config.html`~~ / ~~`email-template.html`~~ | **ลบไฟล์ทิ้งทั้งฟีเจอร์ 2026-08-06** พร้อม endpoint 10 เส้น (`/configs*` · `/email-templates*`) และ `SCHEMAS.config` — ค่ากำหนดกลาง/template อีเมลอยู่ที่ระบบ SBP เดิม (`mas_param` / `email_template`) SBPGI แค่อ่าน · อีเมลยังส่งผ่าน `@gosoft-sbp/email-lib` |
| | | **กลุ่ม ผู้ดูแลระบบ (Admin) ไม่มีเมนูเหลือแล้ว** |
| Flow | `flow-fgi.html` / `k2-flow.html` / `plan-flow.html` | FGI/FCS pipeline / K2 approval BPMN / flow รวมระบบใหม่ (คู่ของ workflow.md) |
| | `job-batch.html` — **Flow Batch Job** | **ย้ายจากกลุ่ม Admin มากลุ่ม Flow 2026-08-06 และเหลือ 2 แท็บ: `Flowchart การทำงาน` + `Database ที่ใช้`** (ตัดแบบฟอร์มพารามิเตอร์ · ประวัติการรัน · ปุ่มสั่งรัน/เปิด-ปิด · stat cards · กราฟ · การ์ด audit ออก) — เอกสารอ้างอิงผู้พัฒนา ไม่ใช่หน้าจอควบคุม · endpoint 6 เส้น (`/jobs*`) + ตาราง `job_configs`/`job_run_histories` ถูกลบจากแบบ · batch job ยังรันปกติ พารามิเตอร์อยู่ใน backend config |
| Database | `fgi-database.html` / `k2-database.html` / `plan-database.html` | schema FGI/FCS / schema K2 16 ตาราง + ER / schema รวม **20 ตาราง** (19 CREATE + `fcs_qssi_score` ที่ reuse · คู่ของ database.md · RBAC/ผู้ปฏิบัติงาน + workflow engine + store/zone/employee master + email template + config ตัดไปใช้ของระบบ SBP เดิม · 2026-08-05/06) |
| Plan | `plan-api.html` | REST API spec **29 เส้น 6 กลุ่ม** (Lookup 2 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3 · กลุ่ม Auth + เส้นสิทธิ์/ผู้ปฏิบัติงาน 18 เส้น comment ตัดถาวร — ใช้ระบบเดิม · กลุ่มข้อมูลผิดปกติ 2 เส้น · กลุ่ม System Config + Email Template 10 เส้น · กลุ่ม Batch Job Admin 6 เส้น — ลบทิ้งทั้งหมด 2026-08-06) |

หมายเหตุ: `k2-database.html` (ER + 16 ตาราง) และ BPMN ใน `k2-flow.html` เป็นของ**เพิ่มเกิน SRS** — ชื่อตาราง/FK ที่เพิ่มไม่ใช่ SRS-mandated

## ~~email-template.html~~ — ลบทั้งฟีเจอร์แล้ว (2026-08-06)

หน้าจอ Email Template (8 การ์ด EM-01–08 + WYSIWYG editor ในตัว) และหน้า ตั้งค่าระบบ (Global Config) **ถูกลบออกจากโปรเจกต์** พร้อม endpoint 10 เส้น, `SCHEMAS.config` ใน `sbp.js` และเอกสาร LLDD-FE-Email-Template

- ค่ากำหนดกลางอยู่ในตาราง **`mas_param`** และ template อีเมลอยู่ในตาราง **`email_template`** ของระบบ SBP เดิม ซึ่งมีหน้าจอบริหารจัดการของตัวเองอยู่แล้ว — SBPGI **อ่านอย่างเดียว**
- อีเมลตามสถานะยังส่งเหมือนเดิมผ่าน `@gosoft-sbp/email-lib` (log ลง `email_sent`) · ตารางสถานะ × action × ผู้รับ × อีเมล ดู `workflow_status_document.md`
- ถ้าต้องกลับมาดูของเดิม: กู้จาก git history (commit ก่อน 2026-08-06)

## plan-api.html — internals ของ modal + SQL + Flowchart

- catalog `GROUPS` (**29 เส้น 6 กลุ่ม** · inline script) → คลิกแถว → `selectEp()` เปิด modal
- โครง modal: ชิป (ที่มา/สิทธิ์/กลุ่ม) → **Flow (ลำดับการทำงาน) อยู่นอกแท็บ** → แท็บ 1 Request/Response → แท็บ 2 Database + SQL → แท็บ 3 Flowchart (โผล่เฉพาะเส้นที่มี spec)
- **`SQL_BY_PATH`** — ตัวอย่าง SQL ต่อ endpoint keyed `'METHOD path'` (เช่น `'GET /api/v1/tasks'`) ครบทุกเส้น active · bind params ขึ้นต้น `:` · illustrative (key ของเส้นที่ตัดออกยังอยู่แต่ไม่ถูกใช้)
- **`FLOWCHART_BY_PATH`** — spec flowchart (nodes/edges) เฉพาะเส้นซับซ้อน: `POST /documents/{docNo}/actions` · `POST /workflows/instances` · `POST /documents` (spec ของ `POST /jobs/{jobNo}/run` **ถูกลบออกแล้ว** พร้อมกลุ่ม Batch Job Admin — เหลือ 3 เส้น · ตรวจยืนยัน 2026-08-24) · เรนเดอร์ด้วย `renderFlow()` เป็น inline SVG (node type: term/termOk/proc/dec/err)
- เพิ่ม endpoint = เพิ่ม object ใน `GROUPS` (+ entry ใน `SQL_BY_PATH`) · ถ้าซับซ้อนพอค่อยเพิ่ม `FLOWCHART_BY_PATH` · อัปเดตตัวเลขสรุป (page-sub + stat cards + comment) และ `api.md`
- รายการ endpoint เต็ม + กฎธุรกิจต่อเส้น ดู `api.md`

## กราฟ / charts ในหน้าต่าง ๆ

- engine กลาง `data-chart="bar|donut|spark"` ใน `sbp.js` (`renderCharts()` รันตอนโหลด · bar=สีเดียว+label · donut=หลายสี+เลขกลาง ต้องใส่ legend เอง · spark=เส้นพื้นที่)
- **หน้าทำงานจริงไม่มีกราฟแล้วทั้งหมด (2026-08-06)** — `k2-report` (ถอด hbarChart 2 ตัว + โค้ด/CSS ที่เหลือ) · `k2-document` (ถอดแนวโน้มยอดขายรายวัน + donut สัดส่วนเงินชดเชย · แผนที่ AllMap ยังอยู่) · `k2-list-*` (ถอด stat cards ทั้งแถว) · `index` (ตัดทั้งหน้า) · `system-config` (ลบหน้าไปแล้ว) · `job-batch` (ถอด stat cards + 3 กราฟ เหลือ Flowchart + DB) · กราฟเหลืออยู่เฉพาะหน้าออกแบบ (`plan-*`, `*-database`, `*-flow`)
- กราฟที่ผูกข้อมูล dynamic ต้องคำนวณจากชุดเดียวกับตัวเลขในหน้า (อย่า hardcode เลขที่หลุดจาก stat cards) · กราฟที่ไม่มีข้อมูลจริงให้กำกับ "ตัวอย่าง" ชัดเจน · เคยลองใส่กราฟใน k2-list(คู่แฝด)/k2-operators/k2-factors แล้ว **เอาออก** ตามที่ตกลง
