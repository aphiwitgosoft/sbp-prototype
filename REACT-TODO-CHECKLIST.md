# React Rebuild — TODO Checklist (per หน้า)

> ℹ️ **อัปเดต 2026-08-06:** โฟลเดอร์ `react-app/` ถูกลบแล้ว — เอกสารนี้ใช้เป็น **รายการ component/ฟิลด์ต่อหน้าจอ** สำหรับสร้างโมดูล SBPGI ใน Next.js portal เดิม (`SBP/srm-sps-spsap-web-frontend` · portal `sbpm`) ไม่ใช่ TODO ของ React+Vite app แล้ว · หน้า Overview และหน้าข้อมูลผิดปกติถูกยกเลิก · หน้าสร้างเอกสารไม่มีฟอร์ม


เอกสารนี้แตกโครงสร้างของ **prototype HTML 20 หน้า** ให้เป็นรายการงานสำหรับ implement เป็น React
แต่ละหน้าระบุ: sections, ปุ่ม, กราฟ, ตาราง (คอลัมน์ครบ), ฟอร์ม/ฟิลด์, modal, และ component ที่ต้องสร้าง

> ป้ายกำกับ UI ภาษาไทยคัดลอกจากหน้าจริงแบบ verbatim — ข้อความ popup/validation ต้องตรงตาม SRS ห้าม paraphrase
> อ้างอิงกติกาธุรกิจ (workflow 5 ขั้น 06→08→01→02→03 — ตัดขั้นบัญชี 04/05, **วงเงินตาม SDD GI 24/02/2026: ≤ 50,000 จบที่ GM · 50,001–300,000 ผ่าน AVP แล้วจบ** — แทนเกณฑ์เดียว 100,000 เดิม, %ชดเชยรวม 100%, 60 วัน = แถวแดง) — ดู `CLAUDE.md` / skill `sbp-prototype`

---

## 0. รากฐานร่วม (สร้างก่อน — ทุกหน้าใช้ซ้ำ)

Header + sidebar **ไม่อยู่ใน HTML** — `sbp.js` inject ตอน runtime จาก registry `MODULES`. ใน React ให้เป็น `<AppLayout>` ครอบทุก route

### Shared layout & infra
- [ ] `<AppLayout>` — header (โลโก้ 7-Eleven + user) + sidebar + breadcrumb + `<main>`; อ่านเมนูจาก `MODULES` registry (key/label/href/icon/group; groups: `ระบบประกันรายได้` → `Flow` → `Database` → `Plan`; รองรับ `children[]` = submenu พับได้ เช่นเมนู "เอกสาร")
- [ ] `MODULES` config (พอร์ตจาก sbp.js) + logic active-item / breadcrumb leaf (`data-crumb`)
- [ ] `ToastProvider` + `useToast()` — แทน `window.SBP.toast(msg, kind)`; kind = `ok` / `del` / ว่าง; แทน hook `data-toast`/`data-ack`/`data-kind`
- [ ] Router — route ต่อหน้า (ดู "Suggested route" ในแต่ละหน้า)

### Shared UI primitives (ใช้ข้ามหน้า)
- [ ] `<Pill>` — สถานะ (มีจุด) หลาย variant: `wait/violet/info/orange/navy/teal/muted/ok/fail/del` **ห้ามสลับกับ** `<Chip>` (ป้ายข้อมูล)
- [ ] `<Chip>` / `<RefChip>` (source tag: `fgi/k2/new/mix` + suffix เช่น `K2 · 3.1.1`)
- [x] ~~`<StatCard>` + `<StatGrid>`~~ **ไม่ต้องสร้าง** — ถอด stat cards ออกจากทุกหน้าแล้ว (2026-08-06)
- [ ] `<DataTable>` — `table.data` ห่อ `.table-wrap` (scroll แนวนอน); รองรับ sortable header (`data-stype`), row action icons `.icon-view/.icon-edit/.icon-del`, checkbox column, empty-state row "ไม่พบรายการตามเงื่อนไขที่กรอง"
- [ ] `<EntityModal>` — engine view/edit/add ขับเคลื่อนด้วย schema (แทน `SCHEMAS` + `data-entity`); field map กับ header ตาราง; **ไม่มีช่อง "เหตุผลการแก้ไข" แล้ว** — ตัดพร้อมตาราง `audit_logs` 2026-08-07 (22 → **21 ตาราง**) · จะเอา audit กลับมาโดยใช้ของระบบเดิมหรือไม่ **ยังไม่ตัดสิน** (DP-12 ใน `SBP/SBPGI-vs-existing-system.md`)
- [ ] `<ConfirmDeleteDialog>`
- [ ] `<Tabs>` — `[data-tabs]` + `.tab` toggle pane
- [ ] `<Pager>` — per-page select (10/20/50/100 " / หน้า"), info "แสดง X–Y จาก N รายการ (กรองจาก M)", prev `‹` / เลขหน้า + `…` / next `›`, "ไปหน้า" + goto input (ใช้ใน k2-list-waiting/related/abnormal)
- [ ] Chart components (แทน engine `data-chart` และ hand-SVG):
  - `<DonutChart>` (หลายสี + เลขกลาง + legend), `<BarChart>`, `<SparkChart>`
  - `<HBarChart>` (แนวนอน + dot สถานะ + tooltip; ใช้ index, k2-report) + `<ChartTooltip>` (`#chartTip` fixed, กันหลุด viewport)
  - `<ColumnChart>` (index รายเดือน, มุมโค้ง, label เฉพาะแท่งสุดท้าย)
- [ ] `<InfoCard>` / `<NoticeCard>` — การ์ด callout ขอบซ้ายสีน้ำเงิน + ไอคอน (ใช้แทบทุกหน้า)
- [ ] `<FlowLegend>` — swatch + label
- [ ] `<AuditHistoryTable>` — ตาราง "ประวัติการแก้ไขข้อมูล" **โครงเดียวกันทุกหน้า**: `วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม → ข้อมูลใหม่ | เหตุผลการแก้ไข`; คำสั่ง = pill (`แก้ไข`=info / `เพิ่ม`=ok / `ลบ`/`รีเซ็ต`=fail); เรียงล่าสุดก่อน
- [ ] Design tokens (`:root`): `--primary` #2f6fed, teal secondary, `--seven-*` (โลโก้ header เท่านั้น), `--header-h` 64px

---

# กลุ่ม: ระบบประกันรายได้

## index.html — **redirect stub (ยกเลิกหน้า Overview 2026-08-06)**
- **Route:** `/` — ไม่มีเนื้อหา ไม่ตาม page contract · ทำหน้าที่เด้งไป **`k2-list-waiting.html` (เอกสาร → รอดำเนินการ) ซึ่งเป็นหน้าแรกของโมดูล**
- Hero / Stat grid / Charts / Module grid / ActivityFeed / QuickLinks **ถูกถอดออกทั้งหมด** พร้อม endpoint `GET /dashboard/summary`
- **TODO:** ฝั่ง Next.js ให้ `redirect('/sbpgi/documents/waiting')` ที่ route `/` เท่านั้น — ไม่มี `<HomePage>` component

## k2-create.html
> **โครงหน้า (2026-08-06):** การ์ด `สร้างเอกสารที่ FS` = กรอบจำลอง iframe ของระบบ FS (คลาส `.fs-frame` ใน `sbp.css` ใช้ร่วมกับส่วนคำนวณเงินชดเชยของหน้าเอกสาร) · ใต้กรอบเป็นการ์ด **หมายเหตุ · ขั้นตอนการสร้างเอกสาร** (หัวข้อ + 4 ขั้นตอน verbatim + บรรทัด “ใช้กรณี…”) — ไม่มีฟอร์ม/แท็บในหน้านี้ — สร้างเอกสาร
- **Route:** `/k2-create` · **crumb:** `สร้างเอกสาร`
- **S1 head:** info pill `เลขที่เอกสารถัดไป · 2026/00187`
- **S2 Tabs:** `สร้างเอกสารใหม่ (นอกเงื่อนไข)` | `สร้างเอกสารที่ FS`
  - **Tab manual:** InfoCallout + ฟอร์ม: `รหัสร้านถูกกระทบ*`(search), `ชื่อร้านถูกกระทบ`(readonly), `ภาค`(readonly), `ประเภทร้าน`(select 8 ตัวเลือก FR Type A/B/C/C r/บริษัท/พนักงาน/PTT/BGC), `วันที่โอนเป็นร้าน SP`(date), `เดือน/ปีที่ถูกกระทบ*`(month), `ครั้งที่`, `รหัสร้านเปิดใหม่*`(search), `เหตุผลการสร้างเอกสารนอกเงื่อนไข*`(textarea) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` · `สร้างเอกสาร`(toast ออกเลข 2026/00187)
  - **Tab fs:** InfoCallout + ฟอร์ม: `รหัสร้านถูกกระทบ*`(search), `ชื่อร้านถูกกระทบ`(readonly), `เดือน/ปีที่ถูกกระทบ*`(month), `Period Statement (From–To)` · ปุ่ม `เคลียร์` · `ส่งสร้างที่ FS` · ตาราง "เอกสารที่รอ SBP Statement ส่งกลับ": `รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ` (pill รอ/ส่งกลับแล้ว)
- **TODO:** `<K2CreatePage>`, `<Tabs>`, `<InfoCallout>`, `<StoreSearchInput>`(×3, ปุ่มแว่นขยาย→lookup), `<FormGrid>`/`<Field>`, `<PendingStatementTable>`

## k2-list-waiting.html — เอกสาร · รอดำเนินการ  ⟷  k2-list-related.html — เอกสาร · ที่เกี่ยวข้อง
> **ฝาแฝด** — ต่างแค่ `<title>`, body attrs, และ const `MODE` (`waiting`/`related`) → พอร์ตเป็น `<DocumentListPage mode>` ตัวเดียว
- **Route:** `/k2/documents/waiting` · `/k2/documents/related`
- **S1 RoleWorkflowBar** (sticky, เฉพาะ mode=waiting): dropdown role profile 5 ขั้น (`code · name`) + stepper คลิกได้ `06›08›01›02›03` + hint
- **S2 head:** title/sub สลับตาม mode
- **S2.1 ตัวกรองหน้า “ที่เกี่ยวข้อง”** (2026-08-06): เพิ่ม select **ผลการพิจารณา** เป็น**ช่องสุดท้ายของฟอร์ม** (ต่อจาก “รอ (วัน)”) — `ทุกผลการพิจารณา` / `ประกันรายได้` / `ไม่ประกันรายได้` / `ยังไม่มีผล (อยู่ระหว่างดำเนินการ)` · อิง `data-result` ของแถว (มีค่าเฉพาะเอกสารที่เสร็จสิ้น) · ใช้เฉพาะหน้านี้ หน้า “รอดำเนินการ” ไม่มีเพราะยังไม่มีผลพิจารณาสุดท้าย
- ~~**S3 Stat cards**~~ **ถอดออกทั้ง 2 หน้า 2026-08-06** — เหลือฟอร์มตัวกรอง + ตารางเท่านั้น · เส้น `GET /dashboard/summary` ถูกตัดตามไปด้วย · หน้า “ที่เกี่ยวข้อง” เปิดช่องตัวกรอง **สถานะ** กลับมาแทนการคลิกกราฟวงกลม
- **S4 Filter bar:** ค้นหา, สถานะ(ซ่อนใน waiting), ภาค(8), ประเภทร้าน, ช่วงวันที่สร้าง, ยอดขายลดลง% (min–max), เงินชดเชย (min–max), รอ(วัน) (min–max), `ล้างตัวกรอง`
- **ตาราง `#tblK2`/`#tblRelated`** (คลิกแถว→k2-document, sortable): `ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง(%) | จำนวนเงินที่ชดเชย | สถานะ(pill) | รอ (วัน)` · `tr.flag-red` = ยอดขายไม่ครบ 60 วัน
- **Pager** + note card ("แดง = ยอดขายไม่ครบ 60 วัน · text file 17:00/วัน · Approve A → SAP")
- **TODO:** `<DocumentListPage mode>`, `<RoleWorkflowBar>` (render เฉพาะ waiting), `<WorkflowStepper>`, `<DocumentFilterBar>`, `<RangeInput>`, `<DocumentTable>`, `<StatusPill>` (map 6 สถานะ), `<Pager>`, hook mock data (เปลี่ยนเป็น API)

## k2-list-abnormal.html — ข้อมูลผิดปกติ / แจกงาน  *(ปิดชั่วคราวใน MODULES — ไฟล์ยังใช้ได้)*
- **Route:** `/k2/documents/abnormal` · **crumb:** `ข้อมูลผิดปกติ / แจกงาน`
- **S1 head:** ปุ่ม `แจกงานที่เลือก` (bulk assign, toast)
- **S2 Stat cards (4, ค่าคำนวณจาก data):** ทั้งหมด / ยังไม่แจกงาน / แจกงานแล้ว / แก้ไขแล้ว
- **S3 Filter:** ค้นหา, ภาค(8), สาเหตุผิดปกติ(4), สถานะ(3), ผู้รับผิดชอบ, `ล้างตัวกรอง` + legend "แดง = ยอดขายไม่ครบ 60 วัน"
- **ตาราง `#tblAbnormal`** (`data-entity=abnormal`): `☑(select-all) | ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ(pill fail/wait/ok) | Action(view+assign)` · `tr.flag-red` · Pager
- **TODO:** `<AbnormalDocumentsPage>`, `<StatCardGrid>`(static), `<AbnormalFilterBar>`, `<AbnormalTable>`(select-all + row checkbox), `<AssignJobModal>`, `<ViewDocumentModal>`, `<Pager>`, bulk-assign state

## k2-document.html — เอกสารข้อมูลร้านถูกกระทบ  ⭐ (ซับซ้อนสุด, SRS 3.1.6)
- **Route:** `/documents/:docNo` · **crumb:** `เอกสารร้านถูกกระทบ` · *ไม่อยู่ใน sidebar (เข้าจากคลิกแถว)*
> ⚠️ **ข้อสังเกต — กลไกสิทธิ์แก้ไขรายส่วนซ้ำซ้อนกับ workflow engine (ยืนยัน 2026-08-10 · ยังไม่ตัดสิน):**
> workflow engine `@srm/glb-workflow` มีตาราง **`workflow_part` + `workflow_part_display`** (schema `sps_store` · `workflow_part_display` คุม 12 ส่วน) ที่กำหนด **READ/WRITE รายส่วนของหน้าจอต่อ state ได้อยู่แล้ว** ซึ่ง**ทับซ้อน**กับกลไก `data-editrole` / `data-roleonly` / `.edit-only` ที่ prototype ทำเอง (ดู S5/S7/S8/S10 ด้านล่าง) และกับธง `permissions.canEditSections` ที่ SBPGI จะคำนวณเอง
> **ยังไม่ตัดสิน**ว่าจะย้ายไปใช้ของ engine หรือคงกลไกของ SBPGI — **ยังไม่เปลี่ยนดีไซน์ ให้ทำตามรายการด้านล่างไปก่อน** · ข้อมูลประกอบ: wrapper ของระบบเดิม register entity แค่ 10 ตัว ยังไม่รวม `WorkflowPart`/`WorkflowPartDisplay` จึงใช้ทันทีไม่ได้ · ดู `SBP/SBPGI-vs-existing-system.md` §3.1 + หัวข้อ 4 (Decision Points 12 ข้อ)
- **S1 RoleSwitcherBar** (sticky): `#roleSwitch` (**5 role** — ตัดขั้นบัญชี 04/05) + pill `ขั้นตอนที่ N/5` + stepper คลิกได้ → เปลี่ยน role re-render ทั้งหน้า + toast
- **S2 head:** `เอกสารข้อมูลร้านถูกกระทบ 2026/00123` + sub + pill สถานะ(สลับตาม role) + ปุ่ม `พิมพ์`
- **S3 ข้อมูลร้านถูกกระทบ:** doc-meta grid (รอบ/ครั้งที่/เดือน, สถานะ, เลขที่, วันที่สร้าง, รหัส/ชื่อร้าน, ภาค, ประเภท, เจ้าของ, นิติบุคคล, วันที่โอน, ผู้ดำเนินการ, ยอดขายลดลง 12.45%, ชดเชยล่าสุด 48,200฿, ไฟล์แนบ) + ปุ่ม `ข้อมูลยอดขายเพิ่มเติม`
- ~~**S4 Charts**~~ **ถอดกราฟ “แนวโน้มยอดขายรายวัน” และ “สัดส่วนเงินชดเชยรายร้านเปิดใหม่” ออก 2026-08-06** — ข้อมูลยอดขายดูผ่านปุ่ม `ข้อมูลยอดขายเพิ่มเติม` (ลิงก์ QlikView BI) และยอดชดเชยรายร้านดูจากคอลัมน์ในตารางร้านเปิดใหม่แทน
- **S5 ร้านเปิดใหม่** (`data-editrole=opt-mgr`): ปุ่ม `รีเฟรช`/`คืนค่าก่อนแก้ไข`/`คำนวณเงินชดเชย` (validate %รวม=100 ไม่งั้น popup) · ตาราง `#tbldocument_new_stores`: `ลำดับ | รหัสร้าน | ชื่อร้านเปิดใหม่ | ภาค | ประเภทร้าน | เจ้าของร้าน | นิติบุคคล | วันที่เปิดร้าน | วันที่ปิดร้าน | ระยะห่าง(กม.) | %ชดเชย(input) | เงินชดเชย(ร้านใหม่)` · สูตร comp = base × %/100
- **S6 แผนที่ AllMap:** `<AllMapPoi>` hand-SVG (วงรัศมี 1กม., pulse ร้านถูกกระทบ, หมุดร้านใหม่ 1/2, คู่แข่ง C) + legend + ปุ่ม `Link To ALLMAP`
- **S7 ร้านคู่แข่ง** (`data-editrole`, `data-entity=competitor`): ปุ่ม `เพิ่ม`(add-row) เท่านั้น — **ไม่มีปุ่ม `บันทึก` ระดับการ์ด** (บันทึกใน modal · 2026-08-06) · ตาราง `☑ | ร้านคู่แข่ง | วันที่เปิดกระทบ | รายละเอียดเพิ่มเติม | Action`
- **S8 ปัจจัยอื่นๆ** (`data-entity=factordoc`): ปุ่ม `เพิ่มข้อมูล` เท่านั้น — **ไม่มีปุ่ม `บันทึก` ระดับการ์ด** · ตาราง `☑ | ปัจจัยภายนอก | วันที่เริ่มต้น | วันที่สิ้นสุด | รายละเอียดเพิ่มเติม | Action`
- **S7–S8 สิทธิ์ + bulk action** (2026-08-06): คอลัมน์ `☑` และคอลัมน์ `Action` **แสดงเฉพาะ role ที่แก้ส่วนนั้นได้** (`permissions.canEditSections` — ปัจจุบันคือ section 01) · role อ่านอย่างเดียวต้องไม่เห็นทั้งสองคอลัมน์ · เมื่อติ๊ก ≥ 1 แถวให้ขึ้นแถบ `เลือกไว้ N รายการ` + ปุ่ม `ล้างการเลือก` / `ลบที่เลือก` (confirm ก่อนลบ · **บันทึกทันที** → `PUT /documents/{docNo}` ไม่ค้างเป็น draft)
- **S9 เอกสารแนบทั้งหมด:** ปุ่ม `แนบไฟล์` (≤5MB) · ตาราง `ไฟล์แนบ | ตำแหน่ง | ผู้สร้างแนบไฟล์ | รายละเอียดเพิ่มเติม | วัน/เดือน/ปี`
- **S9 modal รายละเอียดไฟล์แนบ** (2026-08-06): คลิกแถวในตารางเปิด modal — ไอคอนนามสกุลไฟล์ + ชื่อไฟล์ + ขนาด + วันที่แนบ · ตำแหน่ง/ผู้แนบ/ขั้นตอนที่แนบ/รายละเอียด (readonly) · ปุ่ม **ดาวน์โหลดเอกสาร** → `GET /documents/{docNo}/attachments/{attachId}/download` (ไฟล์จริงใช้ service S3 ของระบบ SBP เดิม `POST /statement/download-file-aws`) · ปุ่ม ปิด
- **S10 คำนวณเงินชดเชย** (`data-roleonly=sbpdsa-officer`): ฟอร์ม readonly (ตั้งต้น 48,200 / %รวม 100 / รวมร้านใหม่ 48,200 / อำนาจอนุมัติ ≤50k GM · 50,001–300k AVP · SDD GI)
- **S11 ประวัติการชดเชย:** ตาราง `ครั้ง | เดือน/ปีที่กระทบ | จำนวนเงินที่ชดเชย | เดือน/ปีที่ส่งบัญชี | สถานะเอกสาร | ผลการพิจารณา | เอกสาร` (คลิก→doc)
- **S12 ผลการพิจารณา (ประวัติ):** ตาราง `ชื่อผู้พิจารณา | ตำแหน่ง | ผลการพิจารณา | รายละเอียดการพิจารณา | วัน/เวลา` (คลิกแถว→modal)
- **S13 พิจารณา (ส่งดำเนินการ):** radio ตัวเลือกตาม role + textarea `ความคิดเห็นเพิ่มเติม` + ปุ่ม `แนบรูป`/`บันทึก`/`ส่งดำเนินการ` (validate เลือกผล + comment ถ้าบังคับ → popup "ท่านยังไม่เลือกผลการพิจารณา…")
- **Role-based views:** **5 role** (sbpdsa-mgr, sbpdsa-officer, opt-mgr, opt-gm, avp — role บัญชี acct-mgr/acct-op ถูกตัดออกแล้ว) กำหนด status/pill/edit sections/decision options + กฎวงเงิน SDD GI (≤50,000 จบที่ GM · 50,001–300,000 → AVP)
- **Modals:** `#k2pop` (warning SRS), `#decHistPop` (รายละเอียดผลพิจารณา), auto view/edit/add/del (competitor/factordoc)
- **TODO:** `<DocumentPage>` + workflow state provider, `<RoleSwitcherBar>`, `<WorkflowStepper>`, `<DocMetaGrid>`, `<AllMapPoi>`, `<NewStoresTable>`(edit+validate 100%), `<EditableDataTable>`(competitor/factors), `<AttachmentsTable>`, `<CompensationCalcPanel>`, `<CompensationHistoryTable>`, `<DecisionHistoryTable>`+`<DecisionHistoryModal>`, `<DecisionPanel>`, `<WarningPopup>`, `useWorkflowRole()`

## k2-report.html — รายงานสรุปสถานะ (SRS 3.1.7 · ปรับตาม **SDD สไลด์ 60** 2026-08-06: ตัวกรอง 7 ตัว / ผลลัพธ์ 14 คอลัมน์)
- **Route:** `/k2/report` · **crumb:** `รายงานสรุปสถานะ`
- **S1 head:** ไม่มีปุ่มด้านบน — `ค้นหาข้อมูล` และ `Export Excel` อยู่ในฟอร์มค้นหาเท่านั้น (2026-08-06)
- **S2 ฟอร์มค้นหา (7 ตัวกรอง · ลำดับตาม SDD สไลด์ 60):** สถานะ\* (select ทีละ 1 · **Required Field ตัวเดียวของหน้านี้**) | รหัสร้านถูกกระทบ (numeric) · รหัสร้านเปิดกระทบ (numeric) | **ประเภทร้าน (checkbox `A/B/C/E`)** · **Period Statement From–To** (`col-2` · `input[type=date]` ปฏิทิน **วัน/เดือน/ปี ค.ศ.** · บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ) · ภาค (checkbox 13 รหัส · `col-2` · ภาคใหม่แสดงอัตโนมัติ) · ผลการพิจารณา (radio ประกันรายได้/ไม่ประกันรายได้ · `col-2` · **ไม่บังคับ**) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` · `ค้นหาข้อมูล` · `Export Excel` · **validate คู่รหัสร้าน:** ระบุรหัสร้านถูกกระทบแล้วต้องระบุรหัสร้านเปิดกระทบด้วย (ตัดฟิลด์ ชื่อร้านที่ถูกกระทบ และ เดือน/ปีที่ถูกกระทบ From–To ออก 2026-08-06 — ไม่มีใน SDD)
- **S2.1 ความสูงคอนโทรล:** input / select / กล่อง checkbox-radio (`.ckgrid`) สูง **46px เท่ากันทุกช่อง** — `sbp.css` คุมด้วย `min-height:46px` (ยกเว้น `[type=checkbox]`/`[type=radio]` ที่ยังเป็น 15px) · กล่องหลายแถว (ภาค) ยืดตามเนื้อหา
- **S3 Summary line:** พบ N รายการ / ยอดชดเชยรวม / วงเงินเข้า AVP / แถวแดง
- ~~**S4 Charts**~~ **ถอดกราฟ “เอกสารตามสถานะ” และ “ยอดเงินชดเชยตามภาค” ออก 2026-08-06** — หน้ารายงานเหลือ ฟอร์มค้นหา → แถบสรุป → ตาราง 14 คอลัมน์
- **S5 ตารางผล 14 คอลัมน์ (ตาม SDD สไลด์ 60):** `รหัสร้านถูกกระทบ | ชื่อร้านถูกกระทบ | ภาค | ประเภทร้าน | เดือน/ปีที่ถูกกระทบ | Period Statement | รหัสร้านเปิดกระทบ | ชื่อร้านเปิดกระทบ | ภาค | ประเภทร้าน | ยอดเงินชดเชย | ครั้งที่ | วันที่สร้าง | เลขที่เอกสาร` · **ทุกคอลัมน์ sort ได้** (`th[data-sort="text|num|date"]` → sorter กลางใน `sbp.js` คลิกสลับ asc/desc) · `tr.flag-red` · ค่า ประเภทร้าน/ภาค ใช้รหัสสั้น (`A/B/C/E`, 13 ภาค) ตามตัวอย่างใน SDD (ตัดคอลัมน์ วันที่โอนเป็นร้าน SP · สถานะ · ชื่อ-นามสกุลผู้ดำเนินการ · ผลการพิจารณา · รอดำเนินการ (วัน) ออก 2026-08-06)
- **TODO:** `<K2ReportPage>`, `<ReportSearchForm>`, `<CheckboxGroup>`(×2), `<MonthRangeInput>`(From–To ใช้ซ้ำทั้งเดือน/ปีที่ถูกกระทบและ Period Statement), `<StorePickerModal>`, `<SummaryLine>`, `<HBarChart>`+`<ChartTooltip>`, `<ReportResultTable>`(19-col scroll + sort ทุกคอลัมน์), number formatter (คั่นหลักพันไทย)
- **ไม่มีในหน้านี้:** กล่องอธิบายขั้นตอนบัญชี/SAP (FBL3H · SAPPOST · SR/BSR) **ถูกลบออก 2026-08-06** — ปลายทางของปุ่ม Export อธิบายไว้ที่ `workflow.md` ขั้น 10 แทน

## k2-operators.html — กำหนดชื่อผู้ปฏิบัติงาน (3.1.8, operator_assignments)
- **Route:** `/k2-operators` · **crumb:** `กำหนดชื่อผู้ปฏิบัติงาน`
- **S1 head:** ปุ่ม `ค้นหาพนักงาน (Pop Up)` (เปิด overlay) · `เพิ่มผู้ปฏิบัติงาน`(add-row)
- **S2 ตาราง `#tblOperators`** (`data-entity=operator`): `☑ | ชื่อผู้ปฏิบัติงาน | E-Mail | ชื่อตำแหน่ง | ภาคที่รับผิดชอบ | Action` (view/edit/del)
- **S3 AuditHistoryTable** + **S4 SrsConditionsCard**
- **S5 EmployeeSearchModal `#empPop`:** search + list พนักงาน (8 คน) → เลือก→เพิ่มแถว + toast
- **Modal schema operator:** ชื่อ/อีเมล/ชื่อตำแหน่ง(select 7)/ภาค(select BE..RS,-)/เหตุผล (ภาคแสดงเมื่อตำแหน่ง=ส่งเสริมธุรกิจฯ)
- **TODO:** `<K2OperatorsPage>`, `<DataTableCard>`, `<OperatorTable>`, `<EmployeeSearchModal>` (แทน DOM-clone ด้วย state), `<EntityModal>` schema operator, `<AuditHistoryTable>`, `<SrsConditionsCard>`

## k2-factors.html — กำหนดปัจจัยภายนอก (3.1.9, external_factors)
- **Route:** `/k2-factors` · **crumb:** `กำหนดปัจจัยภายนอก`
- **S1 head:** ปุ่ม `เพิ่มปัจจัยภายนอก`(add-row)
- **S2 ตาราง `#tblFactors`** (`data-entity=factor`): `☑ | รหัสปัจจัย | ชื่อปัจจัย | รายละเอียดเพิ่มเติม | Action` (view/edit/del) + toolbar ค้นหา/`เคลียร์`
- **S3 AuditHistoryTable** + **S4 SrsConditionsCard** (รหัสห้ามซ้ำ, แก้ได้เฉพาะชื่อ+รายละเอียด+เหตุผล)
- **Modal schema factor:** factor_code/factor_name/factor_remark/เหตุผล
- **TODO:** `<K2FactorsPage>`, `<DataTableCard>`, `<FactorTable>`, `<EntityModal>` schema factor, `<AuditHistoryTable>`, `<SrsConditionsCard>`

## k2-permissions.html — สิทธิ์การเข้าถึงเมนู (SRS 3.1.1)
- **Route:** `/k2/permissions` · **crumb:** `สิทธิ์การเข้าถึงเมนู`
- **S1 head:** ปุ่ม `เพิ่ม Role`(add-row) · `เพิ่มเมนู`(modal) · `บันทึกสิทธิ์`(+badge dirty count)
- **S2 ตาราง Role `#tblRoles`** (`data-entity=role`): `Code | Role | คำอธิบาย | Action` — 8 role (00 Default…10 UserViewer), is_system
- **S3 Matrix `#mtxMain`** (6 เมนู main): role เป็นคอลัมน์บน, เมนูเป็นแถวซ้าย, cell toggle `✓/–` (dirty=amber) + คอลัมน์ `จัดการ` (edit/del)
- **S4 Matrix `#mtxMaster`** (14 เมนู master, ตัด role 00, off-mark `✗`) + legend
- **S5 AuditLogTable** (prepend, pill) + **S6 AcceptanceCriteriaCard** (เฉพาะ Role 01/02 จัดการได้)
- **Modal `#pmPop`:** add/edit menu + confirm delete (cascade menu_permissions)
- **TODO:** `<K2PermissionsPage>`(state roles/menus/dirty), `<RolesTable>`, `<PermissionMatrix>`(group main/master), `<MatrixToggleCell>`, `<MenuManageButtons>`, `<AuditLogTable>`, `<PageModal>`, `<DirtyBadge>`; sync คอลัมน์ matrix เมื่อ add/remove role → บันทึก `PUT /api/v1/menu-permissions/{menuCode}`

## ~~system-config.html~~ · ~~email-template.html~~ — **ลบทั้งฟีเจอร์ (2026-08-06)**
- ไฟล์ HTML ทั้งสองถูกลบออกจากโปรเจกต์ พร้อม entry ใน `MODULES`, `SCHEMAS.config` ของ `assets/sbp.js`, endpoint 10 เส้น (`/configs*` · `/email-templates*`) และตาราง `system_configs`/`email_templates`
- **ไม่ต้องพอร์ตเป็น React** — ค่ากำหนดกลางอยู่ในตาราง `mas_param` และ template อีเมลอยู่ในตาราง `email_template` ของ**ระบบ SBP เดิม** ซึ่งมีหน้าจอบริหารจัดการของตัวเองอยู่แล้ว
- **อีเมลตามสถานะยังส่งเหมือนเดิม** — service ฝั่ง BE อ่าน `email_template` แล้วส่งผ่าน `@gosoft-sbp/email-lib` (log ลง `email_sent`) โดยไม่ต้องมีหน้าจอใน SBPGI · ตารางสถานะ × ผู้รับ ดู `workflow_status_document.md`

---

# กลุ่ม: Flow  (หน้า read-only เอกสาร)

## flow-fgi.html — Flow FGI/FCS (Batch Pipeline, As-Is)
- **Route:** `/flows/fgi` · **crumb:** `Flow FGI/FCS (Batch)`
- **S1 head** (pill `ระบบปัจจุบัน (As-Is)`) · **S2 IntroCard** (ลิงก์ k2-flow/plan-flow)
- **S3 PipelineDiagram** hand-SVG 3 คอลัมน์ (ต้นทาง QSSI/ALLMAP/IAS → เฟส A–E → ปลายทาง BPM/K2/STA/SMTP), เฟส A นำเข้า Master / B แลกเปลี่ยนยอดขาย / C ส่งออก BPM 3 ไฟล์ / D K2·Statement / E Watchdog
- **S4 ตาราง Cron:** `เวลา | Cron | Job | งาน` (8 แถว) · **S5 ตาราง Interface:** `Interface | ทิศทาง | Encoding | ฟิลด์ | เนื้อหา` (9 แถว)
- **TODO:** `<FgiFlowPage>`, `<PipelineDiagram>` (พิจารณา data-drive `phases[]`), `<DataTable>` mono cells, `<RefBadge>`

## k2-flow.html — Flow K2 (Workflow อนุมัติ, SRS 3.1.4)
- **Route:** `/flows/k2` · **crumb:** `Flow K2`
- **S1 head** (pill `5 ขั้นตอน · 6 สถานะ`) · **S2 IntroCard**
- **S3 HappyPathStepper:** `S › 06 › 08 › 01 › 02 › 03(เฉพาะ 50,001–300,000) › ✓`
- **S4 K2Flowchart:** BPMN hand-SVG (task/decision D1–D3/end; solid=ส่งต่อ/ข้ามขั้น, dashed amber=ส่งกลับ/ไม่ชดเชย; กล่องแจ้งเตือนอัตโนมัติ + escalation 30/45/60) + legend
- **S5 Swimlane:** 6 lane (ระบบ→06→08→01→02→03) แต่ละ lane มี task + branch chips (b-go/b-back/b-end)
- **S6 ตาราง Transitions:** `ลำดับ | ผู้ดำเนินการ | section_code | ตัวเลือกส่งงาน / หมายเหตุ` (7 แถว)
- **S7 ตาราง State/Email:** `State | สถานะเอกสาร | ผู้ดำเนินการ | อีเมลถึง (TO) | สำเนา (CC)` (9 แถว) · **S8 note วงเงิน**
- **TODO:** `<FlowPage>`, `<HappyPathStepper>`, `<K2Flowchart>` (static SVG), `<Swimlane>`/`<BranchChip>`, `<DataTable>`(×2), `<InfoCard>`

## job-batch.html — Flow Batch Job (FGI/FCS Jobs 1–10 + 8b) — **ย้ายมากลุ่ม Flow + ลดขอบเขต 2026-08-06**
- **Route:** `/flows/batch-job` · **crumb:** `Flow Batch Job` · **กลุ่มเมนู `Flow`** (ย้ายจากกลุ่ม Admin)
- **ขอบเขตใหม่:** เหลือเฉพาะ **`Flowchart การทำงาน`** + **`Database ที่ใช้`** — เป็นเอกสารอ้างอิงผู้พัฒนา ไม่ใช่หน้าจอควบคุม
- **ตัดออกแล้ว (ไม่ต้องพอร์ต):** แท็บ `แบบฟอร์มพารามิเตอร์` · แท็บ `ประวัติการรัน` · run bar `สั่งรันทันที` · toggle เปิด/ปิด job · ปุ่ม `รีเฟรชสถานะ`/`Export ตาราง Job` · stat cards 4 ใบ · กราฟ 3 ตัว · การ์ด `audit_logs (job_configs)` · endpoint `/jobs*` 6 เส้น · ตาราง `job_configs`/`job_run_histories`
- **S1 head:** ชื่อหน้า + คำอธิบายขอบเขต (ไม่มีปุ่ม)
- **S2 PhaseStrip:** 5 คอลัมน์เฟส A–E, chip ต่อ job (คลิก→select)
- **S3 ตาราง `#tblJobs`:** `Job | ชื่องาน / Main Class | เฟส | ประเภท | กำหนดการ (Cron) | ผลลัพธ์หลัก | (ดู Flow / DB)` — คลิก→detail
- **S4 JobDetailPanel:** header + chips + **Tabs 2:**
  - `Flowchart การทำงาน` — hand-SVG flowchart (`renderFlow`) + timeline คำอธิบายทีละขั้น
  - `Database ที่ใช้` — hand-SVG DB diagram (R/W/RW) + ตาราง `ตาราง/วิว | สิทธิ์ | บทบาทใน Job นี้` + relations + link ไป fgi-database
- **ข้อมูล:** 2 array `PHASES` + `JOBS` (11 job — ใช้เฉพาะ field `flow` / `tables` / `rels` / meta หัวเรื่อง; field `params`/`run`/`hist` ไม่ถูกใช้แล้ว)
- **TODO:** `<BatchFlowPage>`, `<PhaseStrip>`/`<JobChip>`, `<JobTable>`, `<JobDetailPanel>`, `<Tabs>`, `<FlowchartSvg>`(port renderFlow), `<JobDbDiagramSvg>`(port renderDb)

## plan-flow.html — Flow FGI/FCS + K2 (ระบบใหม่, คู่ของ workflow.md)
- **Route:** `/plan/flow` · **crumb:** `Flow FGI/FCS + K2`
- **S1 head** (pill `Target Architecture`) · **S2 RefLegendCard** (chip fgi/k2/new/mix + cross-links)
- **S3 Stat cards (4):** 11 Batch Entry Points / 5 Approval Sections / 21 tables / 30 endpoints (6 กลุ่ม)
- **S4 JourneyStrip (5 ขั้น):** รับข้อมูล → วิเคราะห์ → สร้างเอกสาร → อนุมัติ 5 ขั้น → ส่งผล+ติดตาม + rule grid
- **S5 ArchitectureDiagram** hand-SVG (FE SPA → REST → 6 Backend services → DB รวม → External 5 ระบบ)
- **S6 Timeline 12 ขั้น** (Stage A–D) พร้อม ref chips
- **S7 MigrationTable:** `จุดเชื่อมต่อ | กลไกเดิม | กลไกใหม่ | ที่มา` (7) · **S8 ตารางพฤติกรรม flow เดิม** (4) · **S9 NoticeCard**
- **TODO:** `<PlanFlowPage>`, `<RefLegendCard>`, `<JourneyStrip>`/`<JourneyStep>`, `<ArchitectureDiagram>`, `<Timeline>`/`<TimelineItem>`(done/active), `<MigrationTable>`, `<NoticeCard>`
- ⚠️ ถ้าแก้ flow ต้อง sync `workflow.md` + `plan-flow.html` คู่กัน (living docs)

---

# กลุ่ม: Database  (หน้า read-only เอกสาร)

## fgi-database.html — ฐานข้อมูล FGI/FCS (7 ตาราง, Zone A)
- **Route:** `/database/fgi` · **crumb:** `DB FGI/FCS`
- **S2 DbSwitcherNav** (FGI/FCS·K2·FGI/FCS+K2) · **S3 Stat (4):** 7/11/4/3 · **S4 ScopeCard**
- **S5 ER Diagram** hand-SVG hub-and-spoke รอบ `fgi_impact_processes`
- **S6 SchemaTableCards** (7: fgi_impact_processes/stores/sales_summaries, sales_transactions, competitors, **fcs_qssi_score** (เอกพจน์ — **ตารางนี้มีอยู่จริงแล้วใน `sps_store` 23,958,780 แถว ห้ามสร้างใหม่ ให้ reuse**), interface_transactions) — spec `Column | Type | Key/Rule` + tag
- **S7 StatusDomainGrid** (verify_status/workflow_generation_status/action_status) · **S8 ตาราง SourceSystem:** `ระบบ | Interface | Landing/Domain Table | กติกาสำคัญ` (4)
- **TODO:** `<DbSwitcherNav>`, `<DbStatGrid>`, `<ERDiagram>`(hub variant), `<SchemaTableCard>`, `<DbTag>`, `<StatusDomainGrid>`, `<SourceSystemTable>`

## k2-database.html — ฐานข้อมูล K2 (21 ตาราง, Zone B/C, +ER)
- **Route:** `/database/k2` · **crumb:** `DB K2`
- **S2 DbSwitcherNav** · **S3 Stat (4):** 21/7/8/5MB · **S4 NamingCard**
- **S5 ER Diagram** hand-SVG 11 entity (Transaction=น้ำเงิน/Master=เขียว/Reference=เหลือง, PK/FK, เส้น 1:N)
- **S6–S9 SchemaTableCards** จัดกลุ่ม Master(6) / Transaction(9) / Workflow ภายใน(3) / Config(2) — spec `Column | Type | Key` + source chip (SRS/ออกแบบ/ระบบใหม่)
- **TODO:** `<DbSwitcherNav>`, `<DbStatGrid>`, `<ERDiagram>`(K2 variant), `<SchemaTableCard>`(Key รองรับ PK/FK/enum), `<SourceTag>`, `<SchemaSection>`

## plan-database.html — ฐานข้อมูลรวม 21 ตาราง (Zone A/B/C, คู่ของ database.md)
- **Route:** `/database/plan` · **crumb:** `DB FGI/FCS + K2`
- **S2 DbSwitcherNav** · **S3 SourceLegendCard** · **S4 Stat (4):** 21 ตารางใน Target Schema / 3 Data Zones / 10 ตารางที่ใช้ของระบบ SBP เดิม / 4 Core IDs
- **S5 DataSpine** (5 node: impact_process_id → doc_no → transaction_id → approver_id → employee_id — สอง node กลางอยู่ที่ `sps_store.workflow_transaction`/`workflow_approver` ของ engine กลาง) + 3 zone summary cards
- **S6 ZoneMapDiagram** hand-SVG A/B/C (กล่องตาราง, ตารางใหม่=เขียวประ, ลูกศร A→B)
- **S7 GroupedSchemaTable (21 แถว):** `ตาราง | โซน | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท` — group header สี Zone A/B/C (จำนวนต่อโซนยึดตาม `database.md` ฉบับปัจจุบัน)
- **S8 CrossKeyList** (8 bullet) · **S9 ImprovementList** (8, pill P0×3 · P1×4)
- **TODO:** `<DbSwitcherNav>`, `<DataSpine>`, `<ZoneSummaryCards>`, `<ZoneMapDiagram>`, `<GroupedSchemaTable>`(group-header rows), `<RefChip>`, `<CrossKeyList>`, `<ImprovementList>`
- ⚠️ ถ้าแก้ schema ต้อง sync `database.md` + `plan-database.html` คู่กัน (living docs)

---

# กลุ่ม: Plan

## plan-api.html — API Specification (30 เส้น 6 กลุ่ม, คู่ของ api.md)
- **Route:** `/plan-api` · **crumb:** `API`
- **S1 head:** ปุ่ม `Export OpenAPI`(toast) · **S2 Stat (4):** 30/6/JWT/JSON
- **S3 ConventionsCard** (base `/api/v1`, JWT, pagination, error shape, ISO-8601) · **S5 RecommendationsCard**
- **S4 ApiCatalog:** **6 กลุ่ม / 30 เส้น** (Lookup 3 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3 — กลุ่ม Auth/ผิดปกติ/Config/Email/Batch ถูกตัดออกหมดแล้ว), ตารางต่อกลุ่ม `Method | Path | ทำอะไร | ที่มา` — คลิกแถว→modal
- **EndpointDetailModal:** chips (ที่มา/สิทธิ์/กลุ่ม) → Flow (นอกแท็บ) → **Tabs:** `1 Request/Response` (2 คอลัมน์ + Error list) · `2 Database + SQL` (ตาราง R/W + `<pre>` SQL จาก `SQL_BY_PATH`) · `3 Flowchart` (เฉพาะเส้นซับซ้อน: actions/instances/documents — `renderFlow` SVG · spec ของ jobs run ยังอยู่แต่ไม่ถูกใช้)
- **TODO:** `<PlanApiPage>`, `<ApiCatalog>`/`<ApiGroup>`/`<EndpointTable>`, `<MethodChip>`/`<SourceRefChip>`, `<EndpointDetailModal>`(Tabs+Flow), `<CodeBlock>`, `<DbTable>`, `<FlowchartSVG>`(port renderFlow); พอร์ต `GROUPS`/`SQL_BY_PATH`/`FLOWCHART_BY_PATH` (อุดมคติ = generate จาก OpenAPI)
- ⚠️ ถ้าแก้ API ต้อง sync `api.md` + `plan-api.html` (+ database/workflow ถ้ากระทบ)

---

## หมายเหตุ implement รวม
- **Charts:** prototype ใช้ทั้ง engine `data-chart` (bar/donut/spark) และ hand-SVG (index cols, ทุก diagram/flowchart/ER/map) — React แนะนำ data-drive component; diagram ใหญ่ (BPMN, architecture, ER, zone map) อาจเก็บเป็น SVG asset ก่อนแล้วค่อย data-drive
- **หน้า static (ไม่มี state):** flow-fgi, k2-flow, plan-flow, fgi-database, k2-database, plan-database → layout + data เท่านั้น
- **หน้ามี state จริง:** k2-document (workflow role), k2-permissions (matrix dirty), k2-list-* (filter/sort/page), master pages (CRUD modal)
- **Mock data → API:** k2-list-* และ master pages ใช้ mock deterministic — เปลี่ยนเป็น REST ตาม plan-api.html
- **Living docs:** แก้เรื่อง database/flow/API ต้องอัปเดต `.md` + HTML คู่ของมันพร้อมกันเสมอ
