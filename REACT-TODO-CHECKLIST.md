# React Rebuild — TODO Checklist (per หน้า)

เอกสารนี้แตกโครงสร้างของ **prototype HTML 20 หน้า** ให้เป็นรายการงานสำหรับ implement เป็น React
แต่ละหน้าระบุ: sections, ปุ่ม, กราฟ, ตาราง (คอลัมน์ครบ), ฟอร์ม/ฟิลด์, modal, และ component ที่ต้องสร้าง

> ป้ายกำกับ UI ภาษาไทยคัดลอกจากหน้าจริงแบบ verbatim — ข้อความ popup/validation ต้องตรงตาม SRS ห้าม paraphrase
> อ้างอิงกติกาธุรกิจ (workflow 7 ขั้น, วงเงิน 100,000, %ชดเชยรวม 100%, 60 วัน = แถวแดง) — ดู `CLAUDE.md` / skill `sbp-prototype`

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
- [ ] `<StatCard>` + `<StatGrid>` — ไอคอน + ตัวเลข + label (variant สี bg-blue/teal/amber/rose/navy/…)
- [ ] `<DataTable>` — `table.data` ห่อ `.table-wrap` (scroll แนวนอน); รองรับ sortable header (`data-stype`), row action icons `.icon-view/.icon-edit/.icon-del`, checkbox column, empty-state row "ไม่พบรายการตามเงื่อนไขที่กรอง"
- [ ] `<EntityModal>` — engine view/edit/add ขับเคลื่อนด้วย schema (แทน `SCHEMAS` + `data-entity`); field map กับ header ตาราง; edit ต้องมีช่อง "เหตุผลการแก้ไข (บันทึกลง audit_logs)"
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

## index.html — หน้าแรก / Overview
- **Route:** `/`  · **body:** `data-page=home` `data-nav=modules` `data-module=home` (ไม่มี data-crumb — เบี่ยงจาก template)
- **S1 Hero:** โลโก้โล่ + `<h1>สวัสดี, คุณภัชริดา` + ย่อหน้าอธิบาย workflow · ปุ่ม `งานรอท่านดำเนินการ`(→k2-list-waiting) · `เอกสารร้านถูกกระทบ`(→k2-document)
- **S2 Stat grid (4):** `24` เอกสารรอท่านดำเนินการ · `342` สาขาประกันรายได้เดือนนี้ · `8.42` ยอดชดเชยเดือนนี้ (ล้านบาท) · `5` ยอดขายไม่ครบ 60 วัน (แถวแดง)
- **S3 Charts:** `<ColumnChart>` "ยอดชดเชยประกันรายได้รายเดือน" (8 เดือน, ล้านบาท, label เฉพาะแท่งสุดท้าย) · `<HBarChart>` "เอกสารค้างตามขั้นตอน Workflow" (8 แถว 06–05 + เสร็จสิ้น, dot สีสถานะ, tooltip) — เลข 24/8.42 ต้อง sync กับ stat cards
- **S4 Module grid:** การ์ดทางลัด (`<a>`): k2-list-waiting, k2-create, *(k2-list-abnormal — comment ไว้)*, k2-document, k2-report, k2-operators, k2-factors, k2-permissions (แต่ละอันมี title/code/desc/cta)
- **S5:** การ์ด "กิจกรรมล่าสุด" (4 แถว pill+เวลา) · การ์ด "ทางลัด" (ปุ่ม data-href)
- **TODO:** `<HomePage>`, `<Hero>`, `<ColumnChart>`, `<HBarChart>`, `<ModuleCard>`/`<ModuleGrid>` (รองรับ card ปิดแบบ feature-flag), `<ActivityFeed>`, `<QuickLinks>`

## k2-create.html — สร้างเอกสาร
- **Route:** `/k2-create` · **crumb:** `สร้างเอกสาร`
- **S1 head:** info pill `เลขที่เอกสารถัดไป · 2569/00187`
- **S2 Tabs:** `สร้างเอกสารใหม่ (นอกเงื่อนไข)` | `สร้างเอกสารที่ FS`
  - **Tab manual:** InfoCallout + ฟอร์ม: `รหัสร้านถูกกระทบ*`(search), `ชื่อร้านถูกกระทบ`(readonly), `ภาค`(readonly), `ประเภทร้าน`(select 8 ตัวเลือก FR Type A/B/C/C r/บริษัท/พนักงาน/PTT/BGC), `วันที่โอนเป็นร้าน SP`(date), `เดือน/ปีที่ถูกกระทบ*`(month), `ครั้งที่`, `รหัสร้านเปิดใหม่*`(search), `เหตุผลการสร้างเอกสารนอกเงื่อนไข*`(textarea) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` · `สร้างเอกสาร`(toast ออกเลข 2569/00187)
  - **Tab fs:** InfoCallout + ฟอร์ม: `รหัสร้านถูกกระทบ*`(search), `ชื่อร้านถูกกระทบ`(readonly), `เดือน/ปีที่ถูกกระทบ*`(month), `Period Statement (From–To)` · ปุ่ม `เคลียร์` · `ส่งสร้างที่ FS` · ตาราง "เอกสารที่รอ SBP Statement ส่งกลับ": `รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ` (pill รอ/ส่งกลับแล้ว)
- **TODO:** `<K2CreatePage>`, `<Tabs>`, `<InfoCallout>`, `<StoreSearchInput>`(×3, ปุ่มแว่นขยาย→lookup), `<FormGrid>`/`<Field>`, `<PendingStatementTable>`

## k2-list-waiting.html — เอกสาร · รอดำเนินการ  ⟷  k2-list-related.html — เอกสาร · ที่เกี่ยวข้อง
> **ฝาแฝด** — ต่างแค่ `<title>`, body attrs, และ const `MODE` (`waiting`/`related`) → พอร์ตเป็น `<DocumentListPage mode>` ตัวเดียว
- **Route:** `/k2/documents/waiting` · `/k2/documents/related`
- **S1 RoleWorkflowBar** (sticky, เฉพาะ mode=waiting): dropdown `#roleSwitch` (7 role `code · name`) + stepper คลิกได้ `06›08›01›02›03›04›05` + hint
- **S2 head:** title/sub สลับตาม mode
- **S3 Stat cards (คลิกกรองตาราง):** waiting = 4 การ์ด (ทั้งหมด / flag60 แถวแดง / รอเกิน 3 วัน / วงเงิน>100,000 เข้า AVP); related = 12 การ์ด (ทั้งหมด + 8 สถานะ + 3 special)
- **S4 Filter bar:** ค้นหา, สถานะ(ซ่อนใน waiting), ภาค(8), ประเภทร้าน, ช่วงวันที่สร้าง, ยอดขายลดลง% (min–max), เงินชดเชย (min–max), รอ(วัน) (min–max), `ล้างตัวกรอง`
- **ตาราง `#tblK2`/`#tblRelated`** (คลิกแถว→k2-document, sortable): `ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง(%) | จำนวนเงินที่ชดเชย | สถานะ(pill) | รอ (วัน)` · `tr.flag-red` = ยอดขายไม่ครบ 60 วัน
- **Pager** + note card ("แดง = ยอดขายไม่ครบ 60 วัน · text file 17:00/วัน · Approve A → SAP")
- **TODO:** `<DocumentListPage mode>`, `<RoleWorkflowBar>` (render เฉพาะ waiting), `<WorkflowStepper>`, `<StatCardGrid>`(clickable, active), `<DocumentFilterBar>`, `<RangeInput>`, `<DocumentTable>`, `<StatusPill>` (map 8 สถานะ), `<Pager>`, hook mock data (เปลี่ยนเป็น API)

## k2-list-abnormal.html — ข้อมูลผิดปกติ / แจกงาน  *(ปิดชั่วคราวใน MODULES — ไฟล์ยังใช้ได้)*
- **Route:** `/k2/documents/abnormal` · **crumb:** `ข้อมูลผิดปกติ / แจกงาน`
- **S1 head:** ปุ่ม `แจกงานที่เลือก` (bulk assign, toast)
- **S2 Stat cards (4, ค่าคำนวณจาก data):** ทั้งหมด / ยังไม่แจกงาน / แจกงานแล้ว / แก้ไขแล้ว
- **S3 Filter:** ค้นหา, ภาค(8), สาเหตุผิดปกติ(4), สถานะ(3), ผู้รับผิดชอบ, `ล้างตัวกรอง` + legend "แดง = ยอดขายไม่ครบ 60 วัน"
- **ตาราง `#tblAbnormal`** (`data-entity=abnormal`): `☑(select-all) | ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ(pill fail/wait/ok) | Action(view+assign)` · `tr.flag-red` · Pager
- **TODO:** `<AbnormalDocumentsPage>`, `<StatCardGrid>`(static), `<AbnormalFilterBar>`, `<AbnormalTable>`(select-all + row checkbox), `<AssignJobModal>`, `<ViewDocumentModal>`, `<Pager>`, bulk-assign state

## k2-document.html — เอกสารข้อมูลร้านถูกกระทบ  ⭐ (ซับซ้อนสุด, SRS 3.1.6)
- **Route:** `/documents/:docNo` · **crumb:** `เอกสารร้านถูกกระทบ` · *ไม่อยู่ใน sidebar (เข้าจากคลิกแถว)*
- **S1 RoleSwitcherBar** (sticky): `#roleSwitch` (7 role) + pill `ขั้นตอนที่ N/7` + stepper คลิกได้ → เปลี่ยน role re-render ทั้งหน้า + toast
- **S2 head:** `เอกสารข้อมูลร้านถูกกระทบ 2569/00123` + sub + pill สถานะ(สลับตาม role) + ปุ่ม `พิมพ์`
- **S3 ข้อมูลร้านถูกกระทบ:** doc-meta grid (รอบ/ครั้งที่/เดือน, สถานะ, เลขที่, วันที่สร้าง, รหัส/ชื่อร้าน, ภาค, ประเภท, เจ้าของ, นิติบุคคล, วันที่โอน, ผู้ดำเนินการ, ยอดขายลดลง 12.45%, ชดเชยล่าสุด 48,200฿, ไฟล์แนบ) + ปุ่ม `ข้อมูลยอดขายเพิ่มเติม`
- **S4 Charts:** `<SalesTrendChart>` (hand-SVG เส้น/พื้นที่ 2 ชุด ก่อน–หลัง + marker สาขาเปิด + เส้นเฉลี่ย) · `<SalesAvgBarChart>` (2 แท่ง 42,450 vs 37,163 + badge −12.45%)
- **S5 ร้านเปิดใหม่** (`data-editrole=opt-mgr`): ปุ่ม `รีเฟรช`/`คืนค่าก่อนแก้ไข`/`คำนวณเงินชดเชย` (validate %รวม=100 ไม่งั้น popup) · ตาราง `#tbldocument_new_stores`: `ลำดับ | รหัสร้าน | ชื่อร้านเปิดใหม่ | ภาค | ประเภทร้าน | เจ้าของร้าน | นิติบุคคล | วันที่เปิดร้าน | วันที่ปิดร้าน | ระยะห่าง(กม.) | %ชดเชย(input) | เงินชดเชย(ร้านใหม่)` · สูตร comp = base × %/100
- **S6 แผนที่ AllMap:** `<AllMapPoi>` hand-SVG (วงรัศมี 1กม., pulse ร้านถูกกระทบ, หมุดร้านใหม่ 1/2, คู่แข่ง C) + legend + ปุ่ม `Link To ALLMAP`
- **S7 ร้านคู่แข่ง** (`data-editrole`, `data-entity=competitor`): ปุ่ม `เพิ่ม`(add-row)/`บันทึก` · ตาราง `☑ | ร้านคู่แข่ง | วันที่เปิดกระทบ | รายละเอียดเพิ่มเติม | Action`
- **S8 ปัจจัยอื่นๆ** (`data-entity=factordoc`): ปุ่ม `เพิ่มข้อมูล`/`บันทึก` · ตาราง `☑ | ปัจจัยภายนอก | วันที่เริ่มต้น | วันที่สิ้นสุด | รายละเอียดเพิ่มเติม | Action`
- **S9 เอกสารแนบทั้งหมด:** ปุ่ม `แนบไฟล์` (≤5MB) · ตาราง `ไฟล์แนบ | ตำแหน่ง | ผู้สร้างแนบไฟล์ | รายละเอียดเพิ่มเติม | วัน/เดือน/ปี`
- **S10 คำนวณเงินชดเชย** (`data-roleonly=sbpdsa-officer`): ฟอร์ม readonly (ตั้งต้น 48,200 / %รวม 150 / รวมร้านใหม่ 72,300 / อำนาจอนุมัติ ≤100k GM · >100k AVP)
- **S11 ประวัติการชดเชย:** ตาราง `ครั้ง | เดือน/ปีที่กระทบ | จำนวนเงินที่ชดเชย | เดือน/ปีที่ส่งบัญชี | สถานะเอกสาร | ผลการพิจารณา | เอกสาร` (คลิก→doc)
- **S12 ผลการพิจารณา (ประวัติ):** ตาราง `ชื่อผู้พิจารณา | ตำแหน่ง | ผลการพิจารณา | รายละเอียดการพิจารณา | วัน/เวลา` (คลิกแถว→modal)
- **S13 พิจารณา (ส่งดำเนินการ):** radio ตัวเลือกตาม role + textarea `ความคิดเห็นเพิ่มเติม` + ปุ่ม `แนบรูป`/`บันทึก`/`ส่งดำเนินการ` (validate เลือกผล + comment ถ้าบังคับ → popup "ท่านยังไม่เลือกผลการพิจารณา…")
- **Role-based views:** 7 role (sbpdsa-mgr/officer, opt-mgr/gm, avp, acct-mgr/op) กำหนด status/pill/edit sections/decision options + กฎวงเงิน >100,000→AVP
- **Modals:** `#k2pop` (warning SRS), `#decHistPop` (รายละเอียดผลพิจารณา), auto view/edit/add/del (competitor/factordoc)
- **TODO:** `<DocumentPage>` + workflow state provider, `<RoleSwitcherBar>`, `<WorkflowStepper>`, `<DocMetaGrid>`, `<SalesTrendChart>`, `<SalesAvgBarChart>`, `<AllMapPoi>`, `<NewStoresTable>`(edit+validate 100%), `<EditableDataTable>`(competitor/factors), `<AttachmentsTable>`, `<CompensationCalcPanel>`, `<CompensationHistoryTable>`, `<DecisionHistoryTable>`+`<DecisionHistoryModal>`, `<DecisionPanel>`, `<WarningPopup>`, `useWorkflowRole()`

## k2-report.html — รายงานสรุปสถานะ (SRS 3.1.7, 19 คอลัมน์)
- **Route:** `/k2/report` · **crumb:** `รายงานสรุปสถานะ`
- **S1 head:** ปุ่ม `Export Excel`(toast)
- **S2 ฟอร์มค้นหา:** รหัสร้าน(+ปุ่ม picker), ชื่อร้าน(readonly), เดือน/ปีเริ่ม(month), ถึง(month), ประเภทร้าน(checkbox 4), ภาค(checkbox 8), สถานะ(select ทีละ 1), ผลการพิจารณา(select), Period Statement From–To · ปุ่ม `เคลียร์` · `ค้นหาข้อมูล`
- **S3 Summary line:** พบ N รายการ / ยอดชดเชยรวม / วงเงิน>100,000 / แถวแดง
- **S4 Charts:** `<HBarChart>` "เอกสารตามสถานะ" (8 แถว, dot สี) · `<HBarChart>` "ยอดเงินชดเชยตามภาค" (8 ภาค, teal)
- **S5 ตารางผล 19 คอลัมน์:** `รหัสร้านถูกกระทบ | ชื่อร้านถูกกระทบ | ภาค | ประเภทร้าน | เดือนปีที่ถูกกระทบ | วันที่โอนเป็นร้าน SP | Period Statement | รหัสร้านเปิดใหม่ | ชื่อร้านเปิดใหม่ | ภาค (ร้านใหม่) | ประเภทร้าน (ร้านใหม่) | ยอดเงินชดเชย | สถานะ | ชื่อ-นามสกุลผู้ดำเนินการ | ผลการพิจารณา | รอดำเนินการ (วัน) | ครั้งที่ | วันที่สร้าง | เลขที่เอกสาร` · `tr.flag-red` · pill สถานะ (wait/violet/info/orange/navy/teal/muted/ok)
- **TODO:** `<K2ReportPage>`, `<ReportSearchForm>`, `<CheckboxGroup>`(×2), `<StorePickerModal>`, `<SummaryLine>`, `<HBarChart>`+`<ChartTooltip>`, `<ReportResultTable>`(19-col scroll), number formatter (คั่นหลักพันไทย)

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

## system-config.html — ตั้งค่าระบบ (Global Config, system_configs)
- **Route:** `/system-config` · **crumb:** `ตั้งค่าระบบ (Global Config)`
- **S1 head:** ปุ่ม `เพิ่ม Config`(add-row)
- **S2 `<DonutChart>`** "สัดส่วนค่ากำหนดตามหมวดหมู่" (IMPACT4/WORKFLOW3/DOCUMENT3/AUTH2/NOTIFICATION1/BATCH1) + legend
- **S3 ตาราง `#tblConfigs`** (`data-entity=config`): `☑ | Config Key | หมวดหมู่ | ค่า (Value) | ชนิดข้อมูล | หน่วย | คำอธิบาย | แก้ไขได้ | Action` — 14 config; edit/del เฉพาะแถว "แก้ได้"; ปุ่ม `Invalidate Cache` + filter หมวดหมู่ + ค้นหา
- **S4 AuditHistoryTable** + **S5 InfoCallout** (dot-notation key, cache 5 นาที, is_editable=false=ค่าคงที่)
- **TODO:** `<SystemConfigPage>`, `<ConfigCategoryDonut>`, `<ConfigTable>`(filter+cache), `<EntityModal>` schema config (edit/del conditional), `<CategoryChip>`, `<AuditHistoryTable>`

## job-batch.html — Batch Job (FGI/FCS Jobs 1–10 + 8b)
- **Route:** `/job-batch` · **crumb:** `Batch Job`
- **S1 head:** ปุ่ม `รีเฟรชสถานะ` · `Export ตาราง Job` (toast)
- **S2 Stat cards (4):** 11 entry point / 8 interface / 2 ACK ค้าง / 3 ความเสี่ยง P0
- **S3 Charts (3):** `<DonutChart>` สถานะรอบล่าสุด (9,2) · `<BarChart>` Job ต่อเฟส A–E (3,2,3,2,1) · `<SparkChart>` ACK ค้าง 7 วัน
- **S4 PhaseStrip:** 5 คอลัมน์เฟส A–E, แต่ละอันมี chip ต่อ job (คลิก→select)
- **S5 ตาราง `#tblJobs`:** `Job | ชื่องาน / Main Class | เฟส | ประเภท | กำหนดการ (Cron) | รอบล่าสุด | ผลล่าสุด | รอบถัดไป | สถานะ | (action)` — คลิก→detail
- **S6 JobDetailPanel:** header + chips + toggle เปิด/ปิด + **Tabs 4:**
  - `แบบฟอร์มพารามิเตอร์` — ฟอร์ม param (แก้ได้/ค่าคงที่) + `บันทึกพารามิเตอร์` + run bar (month + `สั่งรันทันที`) + Runbook meta
  - `Flowchart การทำงาน` — hand-SVG flowchart (`renderFlow`) + timeline คำอธิบายทีละขั้น
  - `Database ที่ใช้` — hand-SVG DB diagram (R/W/RW) + ตาราง `ตาราง/วิว | สิทธิ์ | บทบาทใน Job นี้` + relations + link fgi-database
  - `ประวัติการรัน` — pills สำเร็จ/ล้มเหลว + `ดู Log` + ตาราง `เริ่มรัน | ระยะเวลา | จำนวนแถว | ไฟล์ที่เกี่ยวข้อง | ผลลัพธ์ | หมายเหตุ`
- **S7 AuditHistoryTable** (job_configs) + **S8 InfoCard**
- **ข้อมูล:** 2 array `PHASES` + `JOBS` (11 job, แต่ละ job: params/flow/tables/rels/meta/run/hist)
- **TODO:** `<JobBatchPage>`, `<PhaseStrip>`/`<JobChip>`, `<JobTable>`, `<JobDetailPanel>`+`<EnableToggle>`, `<Tabs>`, `<ParamForm>`, `<ManualRunBar>`, `<FlowchartSvg>`(port renderFlow), `<JobDbDiagramSvg>`(port renderDb), `<RunHistoryTab>`, `<AuditHistoryTable>`

## plan-email.html — Email Template (EM-01–08 + WYSIWYG editor)
- **Route:** `/plan/email-templates` · **crumb:** `Email Template`
- **S1 head:** pill `8 Templates` + ปุ่ม `รีเซ็ตทั้งหมดเป็น Default`
- **S2 ตาราง map:** `Template | ชื่อ | จุดที่ส่งใน Flow | ผู้รับ (TO) | แหล่งกติกาผู้รับ | ความถี่` — คลิกแถว→เลื่อนไป template card (สลับ tab + flash)
- **S3 InfoCallout** + **S4 Tabs:** `Workflow (EM-01–03)` | `เตือนงานค้าง/Escalation (EM-04–05)` | `Batch FGI/FCS (EM-06–08)`
- **S5–S12 การ์ด template EM-01..08:** แต่ละใบ = head + flowpoint chip + meta grid + mail mockup (From/To/Cc/Subject + body + ตาราง `.det` + `.mail-btn`) + state pill + ปุ่ม แก้ไข/รีเซ็ต; EM-01 มี `#em01Select` (7 สถานะ) live-rewrite; variant สี ok/warn
- **Editor (inject ต่อ card):** toolbar (undo/redo, bold/italic/underline/strike, สีอักษร 4 + hilite, list 2, table grid picker 6×6 + +/−แถว/คอลัมน์, removeFormat, บันทึก/รีเซ็ต) + ชิปตัวแปร merge (per-template จาก `VARS`) — subject แทรกเป็น text, body แทรกเป็น atom `.mf`
- **S13 AuditHistoryTable** (email_templates); persist localStorage `sbpEmailTpl:EM-0x`
- **TODO:** `<EmailTemplatesPage>`, `<TemplateFlowMap>`, `<Tabs>`, `<EmailTemplateCard>`, `<RichTextToolbar>` (แนะนำใช้ rich-text lib จริงแทน execCommand), `<TableGridPicker>`, `<MergeVariableChips>`, `<MailPreview>`, `<EM01StatusSelector>`, `<AuditHistoryTable>`, localStorage hook

---

# กลุ่ม: Flow  (หน้า read-only เอกสาร)

## flow-fgi.html — Flow FGI/FCS (Batch Pipeline, As-Is)
- **Route:** `/flows/fgi` · **crumb:** `Flow FGI/FCS (Batch)`
- **S1 head** (pill `ระบบปัจจุบัน (As-Is)`) · **S2 IntroCard** (ลิงก์ job-batch/k2-flow/plan-flow)
- **S3 PipelineDiagram** hand-SVG 3 คอลัมน์ (ต้นทาง QSSI/ALLMAP/IAS → เฟส A–E → ปลายทาง BPM/K2/STA/SMTP), เฟส A นำเข้า Master / B แลกเปลี่ยนยอดขาย / C ส่งออก BPM 3 ไฟล์ / D K2·Statement / E Watchdog
- **S4 ตาราง Cron:** `เวลา | Cron | Job | งาน` (8 แถว) · **S5 ตาราง Interface:** `Interface | ทิศทาง | Encoding | ฟิลด์ | เนื้อหา` (9 แถว)
- **TODO:** `<FgiFlowPage>`, `<PipelineDiagram>` (พิจารณา data-drive `phases[]`), `<DataTable>` mono cells, `<RefBadge>`

## k2-flow.html — Flow K2 (Workflow อนุมัติ, SRS 3.1.4)
- **Route:** `/flows/k2` · **crumb:** `Flow K2`
- **S1 head** (pill `7 ขั้นตอน · 8 สถานะ`) · **S2 IntroCard**
- **S3 HappyPathStepper:** `S › 06 › 08 › 01 › 02 › 03(>100,000) › 04 › 05 › ✓`
- **S4 K2Flowchart:** BPMN hand-SVG (task/decision D1–D3/end; solid=ส่งต่อ/ข้ามขั้น, dashed amber=ส่งกลับ/ไม่ชดเชย; กล่องแจ้งเตือนอัตโนมัติ + escalation 30/45/60) + legend
- **S5 Swimlane:** 8 lane (ระบบ→06→08→01→02→03→04→05) แต่ละ lane มี task + branch chips (b-go/b-back/b-end)
- **S6 ตาราง Transitions:** `ลำดับ | ผู้ดำเนินการ | section_code | ตัวเลือกส่งงาน / หมายเหตุ` (7 แถว)
- **S7 ตาราง State/Email:** `State | สถานะเอกสาร | ผู้ดำเนินการ | อีเมลถึง (TO) | สำเนา (CC)` (9 แถว) · **S8 note วงเงิน**
- **TODO:** `<FlowPage>`, `<HappyPathStepper>`, `<K2Flowchart>` (static SVG), `<Swimlane>`/`<BranchChip>`, `<DataTable>`(×2), `<InfoCard>`

## plan-flow.html — Flow FGI/FCS + K2 (ระบบใหม่, คู่ของ workflow.md)
- **Route:** `/plan/flow` · **crumb:** `Flow FGI/FCS + K2`
- **S1 head** (pill `Target Architecture`) · **S2 RefLegendCard** (chip fgi/k2/new/mix + cross-links)
- **S3 Stat cards (4):** 11 / 7 / 30 tables / 46 endpoints  *(หมายเหตุ: SVG เขียน 61 — ตัวเลขไม่ตรงกัน ควรตรวจกับ api.md)*
- **S4 JourneyStrip (5 ขั้น):** รับข้อมูล → วิเคราะห์ → สร้างเอกสาร → อนุมัติ 7 ขั้น → ส่งผล+ติดตาม + rule grid
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
- **S6 SchemaTableCards** (7: fgi_impact_processes/stores/sales_summaries, sales_transactions, competitors, fcs_qssi_scores, interface_transactions) — spec `Column | Type | Key/Rule` + tag
- **S7 StatusDomainGrid** (verify_status/workflow_generation_status/action_status) · **S8 ตาราง SourceSystem:** `ระบบ | Interface | Landing/Domain Table | กติกาสำคัญ` (4)
- **TODO:** `<DbSwitcherNav>`, `<DbStatGrid>`, `<ERDiagram>`(hub variant), `<SchemaTableCard>`, `<DbTag>`, `<StatusDomainGrid>`, `<SourceSystemTable>`

## k2-database.html — ฐานข้อมูล K2 (21 ตาราง, Zone B/C, +ER)
- **Route:** `/database/k2` · **crumb:** `DB K2`
- **S2 DbSwitcherNav** · **S3 Stat (4):** 21/7/8/5MB · **S4 NamingCard**
- **S5 ER Diagram** hand-SVG 11 entity (Transaction=น้ำเงิน/Master=เขียว/Reference=เหลือง, PK/FK, เส้น 1:N)
- **S6–S9 SchemaTableCards** จัดกลุ่ม Master(6) / Transaction(9) / Workflow ภายใน(3) / Config(2) — spec `Column | Type | Key` + source chip (SRS/ออกแบบ/ระบบใหม่)
- **TODO:** `<DbSwitcherNav>`, `<DbStatGrid>`, `<ERDiagram>`(K2 variant), `<SchemaTableCard>`(Key รองรับ PK/FK/enum), `<SourceTag>`, `<SchemaSection>`

## plan-database.html — ฐานข้อมูลรวม 34 ตาราง (Zone A/B/C, คู่ของ database.md)
- **Route:** `/database/plan` · **crumb:** `DB FGI/FCS + K2`
- **S2 DbSwitcherNav** · **S3 SourceLegendCard** · **S4 Stat (4):** 34/3/1/4
- **S5 DataSpine** (5 node: impact_process_id → doc_no → instance_id → task_id → employee_id/role_code) + 3 zone summary cards
- **S6 ZoneMapDiagram** hand-SVG A/B/C (กล่องตาราง, ตารางใหม่=เขียวประ, ลูกศร A→B)
- **S7 GroupedSchemaTable (34 แถว):** `ตาราง | โซน | ที่มา | PK | FK / ความสัมพันธ์หลัก | บทบาท` — group header สี Zone A(7)/B(9)/C(15)
- **S8 CrossKeyList** (8 bullet) · **S9 ImprovementList** (8, pill P0×3 · P1×4)
- **TODO:** `<DbSwitcherNav>`, `<DataSpine>`, `<ZoneSummaryCards>`, `<ZoneMapDiagram>`, `<GroupedSchemaTable>`(group-header rows), `<RefChip>`, `<CrossKeyList>`, `<ImprovementList>`
- ⚠️ ถ้าแก้ schema ต้อง sync `database.md` + `plan-database.html` คู่กัน (living docs)

---

# กลุ่ม: Plan

## plan-api.html — API Specification (61 เส้น 10 กลุ่ม, คู่ของ api.md)
- **Route:** `/plan-api` · **crumb:** `API`
- **S1 head:** ปุ่ม `Export OpenAPI`(toast) · **S2 Stat (4):** 61/10/JWT/JSON
- **S3 ConventionsCard** (base `/api/v1`, JWT, pagination, error shape, ISO-8601) · **S5 RecommendationsCard**
- **S4 ApiCatalog:** 10 กลุ่ม (Auth 4 / เอกสาร 9 / Lookup 4 / *[ผิดปกติ 2 comment]* / Master 20 / Config 5 / Email 5 / รายงาน 2 / Batch 6 / Workflow 3 / Interface 4), ตารางต่อกลุ่ม `Method | Path | ทำอะไร | ที่มา` — คลิกแถว→modal
- **EndpointDetailModal:** chips (ที่มา/สิทธิ์/กลุ่ม) → Flow (นอกแท็บ) → **Tabs:** `1 Request/Response` (2 คอลัมน์ + Error list) · `2 Database + SQL` (ตาราง R/W + `<pre>` SQL จาก `SQL_BY_PATH`) · `3 Flowchart` (เฉพาะ 4 เส้น: actions/instances/documents/jobs run — `renderFlow` SVG)
- **TODO:** `<PlanApiPage>`, `<ApiCatalog>`/`<ApiGroup>`/`<EndpointTable>`, `<MethodChip>`/`<SourceRefChip>`, `<EndpointDetailModal>`(Tabs+Flow), `<CodeBlock>`, `<DbTable>`, `<FlowchartSVG>`(port renderFlow); พอร์ต `GROUPS`/`SQL_BY_PATH`/`FLOWCHART_BY_PATH` (อุดมคติ = generate จาก OpenAPI)
- ⚠️ ถ้าแก้ API ต้อง sync `api.md` + `plan-api.html` (+ database/workflow ถ้ากระทบ)

---

## หมายเหตุ implement รวม
- **Charts:** prototype ใช้ทั้ง engine `data-chart` (bar/donut/spark) และ hand-SVG (index cols, k2-report hbar, k2-document sales, ทุก diagram/flowchart/ER/map) — React แนะนำ data-drive component; diagram ใหญ่ (BPMN, architecture, ER, zone map) อาจเก็บเป็น SVG asset ก่อนแล้วค่อย data-drive
- **หน้า static (ไม่มี state):** flow-fgi, k2-flow, plan-flow, fgi-database, k2-database, plan-database → layout + data เท่านั้น
- **หน้ามี state จริง:** k2-document (workflow role), k2-permissions (matrix dirty), plan-email (editor), job-batch (job select), k2-list-* (filter/sort/page), master pages (CRUD modal)
- **Mock data → API:** k2-list-* และ master pages ใช้ mock deterministic — เปลี่ยนเป็น REST ตาม plan-api.html
- **Living docs:** แก้เรื่อง database/flow/API ต้องอัปเดต `.md` + HTML คู่ของมันพร้อมกันเสมอ
