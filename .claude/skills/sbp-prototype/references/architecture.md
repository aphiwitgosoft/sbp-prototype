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
- ใช้ `k2-document.html` เป็น template หน้าใหม่ (`index.html` โครงต่างออกไป — อย่า copy)
- Public API มีแค่ `window.SBP.toast(msg, kind)` — kind: `'ok'` / `'del'` / ว่าง

**เพิ่มหน้า = 2 ขั้น**: สร้างไฟล์ตาม contract + เพิ่ม entry ใน `MODULES` (sbp.js ~บรรทัด 55): `{key, label, href, icon, group}`
กลุ่ม sidebar render ตามลำดับที่พบครั้งแรก ปัจจุบัน: `ระบบประกันรายได้` → `Flow` → `Database` → `Plan`
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
| หลัก | `index.html` | Overview + shortcuts |
| | `k2-create.html` | สร้างเอกสาร manual (จาก Approve Flow เดิมขั้น 15) |
| | `k2-list-waiting.html` / `k2-list-related.html` | รอดำเนินการ / ที่เกี่ยวข้อง — **ฝาแฝด ต่างแค่ `MODE` const, title, body attrs — แก้ทั้งคู่เสมอ** |
| | `k2-list-abnormal.html` | ข้อมูลผิดปกติ/แจกงาน — **ปิดชั่วคราว** (comment ใน MODULES/index/plan-api) ไฟล์ยังใช้ได้ |
| | `k2-document.html` | หน้าเอกสารร้านถูกกระทบ (SRS 3.1.6 — ซับซ้อนสุด) มี dropdown สลับ role demo 7 มุมมองผ่าน `data-editrole`/`data-roleonly`/`.edit-only` · **ไม่อยู่ใน sidebar** เข้าจากคลิกแถวตาราง |
| | `k2-report.html` | รายงานสรุปสถานะ 19 คอลัมน์ (SRS 3.1.7) |
| | `k2-operators.html` / `k2-factors.html` | master ผู้ปฏิบัติงาน (3.1.8) / ปัจจัยภายนอก (3.1.9) |
| | `k2-permissions.html` | สิทธิ์เมนู 8 role (SRS 3.1.1) |
| | `system-config.html` | Global config key–value (ตาราง `system_configs`) |
| | `job-batch.html` | Batch console Jobs 1–10 + 8b (จากเอกสาร Batch v4.0) |
| | `plan-email.html` | Email templates EM-01–08 + WYSIWYG editor (ดูหัวข้อถัดไป) |
| Flow | `flow-fgi.html` / `k2-flow.html` / `plan-flow.html` | FGI/FCS pipeline / K2 approval BPMN / flow รวมระบบใหม่ (คู่ของ workflow.md) |
| Database | `fgi-database.html` / `k2-database.html` / `plan-database.html` | schema FGI/FCS / schema K2 16 ตาราง + ER / schema รวม 34 ตาราง (คู่ของ database.md) |
| Plan | `plan-api.html` | REST API spec 61 เส้น 10 กลุ่ม (กลุ่มข้อมูลผิดปกติ 2 เส้น comment รอตัดสินใจ) |

หมายเหตุ: `k2-database.html` (ER + 16 ตาราง) และ BPMN ใน `k2-flow.html` เป็นของ**เพิ่มเกิน SRS** — ชื่อตาราง/FK ที่เพิ่มไม่ใช่ SRS-mandated

## plan-email.html — internals ของ editor

- 8 การ์ด template แต่ละใบมี `data-tpl="EM-0x"` · Subject = `.mail-row .v.subj` · เนื้อหา = `.mail-body`
- กด "แก้ไข" → contenteditable + แถบ `.tpl-editor` (สร้างโดย JS) โผล่เหนือ `.mail` แบบ **sticky** ใต้ header
- Toolbar ใช้ `document.execCommand`: undo/redo, bold/italic/underline/strike, สีอักษร 4 ค่า + hilite, list 2 แบบ, **ตาราง** (grid picker 6×6 แทรก `table.det` + ปุ่ม +แถว/+คอลัมน์/−แถว/−คอลัมน์ ทำงานกับตารางที่เคอร์เซอร์อยู่), removeFormat
- ปุ่ม **บันทึก/รีเซ็ต sticky** อยู่ขวาสุดของ toolbar (`data-act`) — delegate ไปที่ปุ่มเดิมบน card-head
- ตัวแปร merge ต่อ template อยู่ใน object `VARS` (inline script) — ชิป `.rt-var` คลิกแทรก ณ เคอร์เซอร์ (body = ชิป `.mf contenteditable=false` · subject = ข้อความเปล่า)
- ระหว่างแก้ไข `.mf` เป็น atom (คลิกครั้งเดียวเลือกทั้งก้อน) — attribute contenteditable ถูก**ถอดออกก่อนบันทึก**
- เก็บใน localStorage key `sbpEmailTpl:EM-0x` เป็น JSON `{subj, body}` · From/To/Cc ล็อกตาม `status_email_rules`
- EM-01 มี dropdown `#em01Select` สลับตัวอย่างตาม section ถัดไป — object `RULES` ในหน้า ต้องตรงกับตาราง State/Email ใน k2-flow
- CSS ระวัง: ปุ่มใน toolbar ใช้ selector `.rt-toolbar button:not(.btn)` เพื่อไม่ทับสไตล์ปุ่ม `.btn` ของ save/reset

## plan-api.html — internals ของ modal + SQL + Flowchart

- catalog `GROUPS` (61 เส้น 10 กลุ่ม · inline script) → คลิกแถว → `selectEp()` เปิด modal
- โครง modal: ชิป (ที่มา/สิทธิ์/กลุ่ม) → **Flow (ลำดับการทำงาน) อยู่นอกแท็บ** → แท็บ 1 Request/Response → แท็บ 2 Database + SQL → แท็บ 3 Flowchart (โผล่เฉพาะเส้นที่มี spec)
- **`SQL_BY_PATH`** — ตัวอย่าง SQL ต่อ endpoint keyed `'METHOD path'` (เช่น `'GET /api/v1/tasks'`) ครบทั้ง 61 เส้น · bind params ขึ้นต้น `:` · illustrative
- **`FLOWCHART_BY_PATH`** — spec flowchart (nodes/edges) เฉพาะ 4 เส้นซับซ้อน: `POST /documents/{docNo}/actions` · `POST /workflows/instances` · `POST /documents` · `POST /jobs/{jobNo}/run` · เรนเดอร์ด้วย `renderFlow()` เป็น inline SVG (node type: term/termOk/proc/dec/err)
- เพิ่ม endpoint = เพิ่ม object ใน `GROUPS` (+ entry ใน `SQL_BY_PATH`) · ถ้าซับซ้อนพอค่อยเพิ่ม `FLOWCHART_BY_PATH` · อัปเดตตัวเลขสรุป (page-sub + stat cards + comment) และ `api.md`
- รายการ endpoint เต็ม + กฎธุรกิจต่อเส้น ดู `api.md`

## กราฟ / charts ในหน้าต่าง ๆ

- engine กลาง `data-chart="bar|donut|spark"` ใน `sbp.js` (`renderCharts()` รันตอนโหลด · bar=สีเดียว+label · donut=หลายสี+เลขกลาง ต้องใส่ legend เอง · spark=เส้นพื้นที่)
- หน้าที่มีกราฟ: `index` + `k2-report` (กราฟ JS ของตัวเอง — hbarChart) · `job-batch` (donut สถานะ + bar ต่อเฟส + spark ACK) · `system-config` (donut ตาม category) · `k2-document` (ยอดขาย ก่อน–หลัง 2 คอลัมน์ — เส้น + แท่งเทียบเฉลี่ย · hand-authored SVG, baseline ซูมให้เห็นส่วนต่าง)
- กราฟที่ผูกข้อมูล dynamic ต้องคำนวณจากชุดเดียวกับตัวเลขในหน้า (อย่า hardcode เลขที่หลุดจาก stat cards) · กราฟที่ไม่มีข้อมูลจริงให้กำกับ "ตัวอย่าง" ชัดเจน · เคยลองใส่กราฟใน k2-list(คู่แฝด)/k2-operators/k2-factors แล้ว **เอาออก** ตามที่ตกลง
