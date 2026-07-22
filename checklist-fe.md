# checklist-fe.md — Checklist สร้าง Frontend (React + Vite) ฉบับละเอียด

> ทำตามลำดับ Phase — **ห้ามข้าม Phase** เพราะของหลังพึ่งของก่อน · spec เต็มอยู่ `plan-fe.md` · รายละเอียด component/ฟิลด์ต่อหน้าอยู่ `REACT-TODO-CHECKLIST.md` · API 62 เส้นอยู่ `api.md` · flow/สถานะอยู่ `workflow.md` · สัญญากลางอยู่ `LLDD/FE/LLDD-FE-Integration-Contracts.md` + `LLDD/BE/LLDD-BE-API-Common-Contracts.md`
> ทุก Phase มี **✔ เกณฑ์ตรวจรับ** เป็น test case ที่รันได้จริง — ผ่านครบก่อนไป Phase ถัดไป
> ทุกข้อออกแบบให้ทำจบใน ~1–2 ชั่วโมง · path ไฟล์ = ใต้ `src/` ตามโครง feature-based ใน plan-fe.md §3

**กติกาเหล็ก (ใช้ทุก Phase — ผิดข้อใดข้อหนึ่ง = ไม่ผ่าน):**
1. workflow 5 ขั้น `06 → 08 → 01 → 02 → 03` เท่านั้น — **ห้ามอ้าง section 04/05 หรือสถานะบัญชีในทุกที่** (SDD v7.5 ตัดแล้ว)
2. สถานะเอกสาร 6 ค่า verbatim: `รอฝ่าย SBP DSA ดำเนินการ` · `รอเจ้าหน้าที่ SBP DSA ดำเนินการ` · `รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ` · `รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ` · `รอผู้บริหารสำนักบริหาร SBP ดำเนินการ` · `เสร็จสิ้นดำเนินการ`
3. กฎ 100,000: >100k → ผ่าน AVP(03) แล้ว**จบ** · ≤100k → **จบที่ GM(02)** — logic อยู่ BE, FE แค่แสดงผล
4. ข้อความไทย verbatim ห้าม paraphrase เช่น `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`
5. ภาค 8 ค่า: `BE BN BS BW RC RE RN RS` — **มี RC ไม่มี RW**
6. %ชดเชยรวมทุกร้านเปิดใหม่ = **100%** พอดีก่อน submit
7. ไฟล์แนบ ≤ **5MB** + นามสกุลตาม `ATTACH_EXTS`
8. แถวยอดขายไม่ครบ 60 วัน = `tr.flag-red`
9. **ห้าม** UI library / chart library / Tailwind — CSS Modules + SVG เขียนเองเท่านั้น

---

## Phase 0 — Scaffold & Design Tokens

### 0.1 สร้างโปรเจกต์ + dependency
- [ ] `pnpm create vite sbpgi-fe --template react-ts` (Node ≥ 20)
- [ ] ติดตั้ง runtime deps: `react-router-dom` `@tanstack/react-query` `zustand` `axios` `react-hook-form` `zod` `@hookform/resolvers` (ตาม plan-fe.md §2 — ห้ามเพิ่มเกิน)
- [ ] ติดตั้ง dev deps: `vitest` `@testing-library/react` `@testing-library/jest-dom` `jsdom` `msw` `eslint` `prettier`
- [ ] ตั้ง `tsconfig.json` strict mode + `vitest.config` (environment jsdom, setupFiles `src/test/setup.ts`)

### 0.2 คุณภาพโค้ด + CI
- [ ] `husky` + `lint-staged` (pre-commit: eslint+prettier เฉพาะไฟล์ที่แก้)
- [ ] `commitlint` + `@commitlint/config-conventional` (บังคับ `feat:` `fix:` `chore:` …)
- [ ] GitHub Actions CI: `.github/workflows/ci.yml` → `lint → tsc --noEmit → test → build` ทุก PR

### 0.3 path alias + กติกา import
- [ ] alias `@/` = `src/` ใน `tsconfig.json` (paths) + `vite.config.ts` (resolve.alias)
- [ ] eslint rule `import/no-restricted-paths`: `app → features → shared` ทางเดียว — feature ห้าม import ข้าม feature
- [ ] ห้าม barrel `index.ts` re-export ทั้งโฟลเดอร์

### 0.4 โครงโฟลเดอร์ feature-based (สร้างครบตั้งแต่แรก)
- [ ] `app/` — `main.tsx` `App.tsx` `router.tsx` `providers/` (query-client.ts, toast, error-boundary)
- [ ] `features/` — `auth/ dashboard/ documents/ reports/ masters/ admin/ abnormal/` (แต่ละอันมี `api/ components/ hooks/ types/`)
- [ ] `shared/` — `api/ components/ charts/ layout/ lib/ types/`
- [ ] `styles/` — `tokens.css` `global.css` · `test/setup.ts`

### 0.5 พอร์ต CSS จาก prototype
- [ ] `styles/tokens.css` — ตัวแปร `:root` ทั้งหมดจาก `assets/sbp.css`: `--primary` #2f6fed, teal secondary, `--seven-*` (โลโก้ header เท่านั้น), `--header-h` 64px
- [ ] `styles/global.css` — base, `table.data` + `.table-wrap` (scroll แนวนอน), `.pill` ครบ variant `wait/violet/info/orange/navy/teal/muted/ok/fail/del`, `.chip`, `.card`, `.btn*`, `tr.flag-red`, โครง modal (`display:flex` + `.show`), toast stack
- [ ] โหลดฟอนต์ Google Fonts **Prompt + Sarabun** ใน `index.html`

### 0.6 Env
- [ ] `.env.development` → `VITE_API_BASE=http://localhost:3000/api/v1` + `VITE_FEATURE_ABNORMAL=false`
- [ ] `vite.config.ts` proxy `/api` → `http://localhost:3000`
- [ ] `shared/lib/env.ts` — validate env ตอน boot, ขาดค่า = โยน error

### 0.7 Common API/FE contracts
- [ ] `shared/types/api.ts` — ประกาศ `ApiError {code,message}` · `PageResponse<T> {page,size,total,items}` · `ActionResponse {nextSection,statusCode,status}` · `MenuItem`
- [ ] `shared/lib/format.ts` เป็นจุดเดียวสำหรับ date/month พ.ศ., money, docNo; ไม่มี formatter ซ้ำใน feature
- [ ] `features/documents/types/workflow.ts` — `ActionResult` 6-enum ไทย verbatim; `DecisionPanel` ใช้ type นี้เท่านั้น
- [ ] `shared/api/client.ts` เป็น API client เดียวทั้งแอป; eslint/import check หรือ test ยืนยันไม่มี axios instance อื่น
- [ ] MSW base handlers คืน error `{code,message}` และ list `{page,size,total,items}` เพื่อบังคับ shape ตั้งแต่ test แรก

**✔ เกณฑ์ตรวจรับ Phase 0**
- [ ] รัน `pnpm dev` → หน้าเปล่าขึ้น, ฟอนต์ไทย Prompt/Sarabun แสดงถูก
- [ ] รัน `pnpm build` → ผ่าน ไม่มี error
- [ ] หน้า demo ชั่วคราวแสดง `.pill` ทั้ง 10 variant → สีตรงกับ prototype เมื่อเทียบตา
- [ ] commit ด้วย message ไม่ตรง convention → ถูก commitlint ปฏิเสธ
- [ ] import ข้าม feature (`features/reports` → `features/documents`) → eslint ฟ้อง
- [ ] unit test `ApiError` passthrough, `PageResponse` pager mapping, `ActionResponse` หลัง submit, formatter พ.ศ./money/docNo ผ่านทั้งหมด

---

## Phase 1 — Layout + Auth

### 1.1 API client
- [ ] `shared/api/client.ts` — axios instance เดียว, baseURL จาก env
- [ ] request interceptor: แนบ `Authorization: Bearer <accessToken>`
- [ ] response interceptor: 401 → `POST /auth/refresh` แบบ **single-flight promise** (กัน race) → replay request · refresh ตาย → ล้าง store + redirect `/login`
- [ ] error ทุกเส้นรูปแบบ `{code, message}` — helper ดึง `message` แสดงตรง ๆ (BE ส่งไทยตาม SRS แล้ว ห้าม FE แต่งเอง)
- [ ] GET list hook ทุกตัว return `PageResponse<T>` shape เดียว; component ห้าม assume array root

### 1.2 Auth store + guard
- [ ] `features/auth/store.ts` — zustand: `user / accessToken (memory) / refreshToken (localStorage)` + `useAuth()`
- [ ] `features/auth/components/RequireAuth.tsx` — ครอบทุก route ยกเว้น `/login`
- [ ] `features/auth/components/RequireRole.tsx` — ครอบหน้า admin/master ตามตารางสิทธิ์ plan-fe.md §4
- [ ] `features/auth/LoginPage.tsx` — form email/password (react-hook-form+zod) → `POST /auth/login` → เก็บ token → `GET /auth/me` + `GET /me/menus` → redirect `/` · error แสดง `message` จาก API ตรง ๆ

### 1.3 Layout
- [ ] `shared/layout/MODULES.ts` — พอร์ต registry จาก `assets/sbp.js` (~บรรทัด 55): `{key,label,route,icon,group}` + `children[]` (เมนู "เอกสาร" → รอดำเนินการ/ที่เกี่ยวข้อง; ลูก abnormal ใส่ไว้แต่ปิดด้วย `isFeatureEnabled('abnormal')`)
- [ ] `shared/layout/Header.tsx` — โลโก้ 7-Eleven ใช้สี `--seven-*` + ชื่อผู้ใช้ + role
- [ ] `shared/layout/Sidebar.tsx` — group ตามลำดับ first-appearance · active ตาม route (exact → key → same path) · submenu พับได้ · **filter เมนูด้วยผล `GET /me/menus` — ไม่ hardcode role ฝั่ง FE**
- [ ] `shared/layout/Breadcrumb.tsx` (leaf จาก meta ของ route) + `shared/layout/AppLayout.tsx` ครอบ `<Outlet>`
- [ ] `app/router.tsx` — ครบทั้ง 14 route ตามตาราง plan-fe.md §4 (หน้า placeholder ได้) + `lazy()` ต่อ page

### 1.4 Toast
- [ ] `app/providers/toast.tsx` — `ToastProvider` + `useToast()` kind `ok/del/default` หน้าตา/สี/ตำแหน่งเหมือน `#toast-stack` เดิม

**✔ เกณฑ์ตรวจรับ Phase 1**
- [ ] login ถูก → redirect `/` → header แสดงชื่อ+role · sidebar แสดงเฉพาะเมนูจาก `/me/menus`
- [ ] login ผิด → แสดง `message` จาก API ใต้ฟอร์ม ไม่ crash
- [ ] mock access token หมดอายุ (msw ตอบ 401 ครั้งแรก) → refresh อัตโนมัติ 1 ครั้ง → request เดิมสำเร็จ
- [ ] ยิง 2 request พร้อมกันตอน 401 → refresh ถูกเรียก**ครั้งเดียว** (single-flight)
- [ ] logout → store ล้าง, localStorage ไม่มี refreshToken, กลับ `/login`
- [ ] role ไม่มีสิทธิ์เข้า `/admin/system-config` → redirect ออก

---

## Phase 2 — Shared Components (ตาม REACT-TODO-CHECKLIST.md §0)

### 2.1 Primitives (`shared/components/`)
- [ ] `Pill.tsx` — variant `wait/violet/info/orange/navy/teal/muted/ok/fail/del` มีจุดสี · `Chip.tsx` + `RefChip.tsx` (source tag `fgi/k2/new/mix` + suffix เช่น `K2 · 3.1.1`) — **Pill ≠ Chip ห้ามใช้สลับ**
- [ ] `StatCard.tsx` + `StatGrid.tsx` — ไอคอน+ตัวเลข+label, variant สี bg-blue/teal/amber/rose/navy · รองรับ clickable+active (ใช้กรองตารางใน Phase 3)
- [ ] `InfoCard.tsx` / `NoticeCard.tsx` (callout ขอบซ้ายน้ำเงิน+ไอคอน) · `FlowLegend.tsx`

### 2.2 DataTable + Pager
- [ ] `DataTable.tsx` — ห่อ `.table-wrap`, sortable header, row action icons view/edit/del, checkbox column + select-all, empty-state row `ไม่พบรายการตามเงื่อนไขที่กรอง` (verbatim), รองรับ `rowClassName` (สำหรับ `flag-red`)
- [ ] `Pager.tsx` — per-page select `10/20/50/100` + " / หน้า", info `แสดง X–Y จาก N รายการ (กรองจาก M)`, ปุ่ม `‹` เลขหน้า+`…` `›`, "ไปหน้า" + goto input

### 2.3 Modal engine
- [ ] `EntityModal.tsx` — schema-driven view/edit/add (แทน `SCHEMAS`+`data-entity` ของ sbp.js) · โหมด edit บังคับช่อง `เหตุผลการแก้ไข (บันทึกลง audit_logs)`
- [ ] `ConfirmDeleteDialog.tsx` · `Tabs.tsx` (`[data-tabs]` แบบ React)
- [ ] `AuditHistoryTable.tsx` — 6 คอลัมน์มาตรฐาน `วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม → ข้อมูลใหม่ | เหตุผลการแก้ไข` · คำสั่ง = pill (`แก้ไข`=info / `เพิ่ม`=ok / `ลบ`/`รีเซ็ต`=fail) · เรียงล่าสุดก่อน — ใช้ทุกหน้า master/admin

### 2.4 Charts (`shared/charts/` — SVG เขียนเองทั้งหมด)
- [ ] `DonutChart.tsx` (หลายสี+เลขกลาง+legend) · `BarChart.tsx` · `SparkChart.tsx`
- [ ] `HBarChart.tsx` (แนวนอน + dot สถานะ + tooltip) + `ChartTooltip.tsx` (fixed, กันหลุด viewport)
- [ ] `ColumnChart.tsx` (รายเดือน, มุมโค้ง, label เฉพาะแท่งสุดท้าย)

### 2.5 Constants + utils
- [ ] `shared/lib/constants.ts` ตาม plan-fe.md §7 ครบ: `SECTIONS` (5 ขั้น 06/08/01/02/03) · `DOC_STATUSES` (6 ค่า verbatim ข้างบน) · `AVP_THRESHOLD=100_000` · `REGIONS8=['BE','BN','BS','BW','RC','RE','RN','RS']` · `REPORT_REGIONS13` · `SEARCH_STORE_TYPES=['FR Type A','FR Type B','FR Type C','พนักงาน']` · `MAX_FILE_MB=5` · `ATTACH_EXTS` (27 นามสกุล) · `MSG.NO_DECISION='ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ'` + ข้อความอื่นจากหน้า html เดิม
- [ ] `shared/lib/format.ts` — `formatMoney` (คั่นหลักพัน ทศนิยม 2) · `formatDateThai` (ISO ค.ศ. → พ.ศ. จุดเดียว) · `formatDocNo` (`YYYY/xxxxx` พ.ศ.)
- [ ] `shared/api/query-keys.ts` — key factory รวมศูนย์ (`documentKeys.list(params)` / `.detail(docNo)` / `taskKeys` / `masterKeys` …)
- [ ] unit test: format ทั้ง 3 + constants (สถานะ 6 ค่า, ภาคมี RC ไม่มี RW, threshold)

### 2.6 Kitchen sink
- [ ] route `/dev/kitchen-sink` (เฉพาะ `import.meta.env.DEV`) แสดงทุก component + ทุก variant

**✔ เกณฑ์ตรวจรับ Phase 2**
- [ ] เปิด `/dev/kitchen-sink` เทียบตากับ prototype → Pill/Chip/StatCard/ตาราง/Pager/Modal/Chart ทุกตัวหน้าตาตรง
- [ ] `formatDateThai('2026-01-15')` → มี `2569` · `formatMoney(1234567)` → `1,234,567.00`
- [ ] DataTable ไม่มีข้อมูล → แถว `ไม่พบรายการตามเงื่อนไขที่กรอง` ตรง verbatim
- [ ] EntityModal โหมด edit ไม่กรอกเหตุผล → submit ไม่ได้
- [ ] `pnpm test` ผ่านทั้งหมด · ไม่มี dependency chart lib ใน `package.json`

---

## Phase 3 — HomePage + DocList

### 3.1 HomePage (`features/dashboard/` — §index.html)
- [ ] `HomePage.tsx` ผูก `GET /dashboard/summary` (react-query, BE cache 5 นาที)
- [ ] S1 Hero: โลโก้โล่ + `สวัสดี, คุณ<ชื่อจาก /auth/me>` + ปุ่ม `งานรอท่านดำเนินการ` (→`/documents/waiting`) · `เอกสารร้านถูกกระทบ`
- [ ] S2 StatGrid 4 ใบ: เอกสารรอท่านดำเนินการ · สาขาประกันรายได้เดือนนี้ · ยอดชดเชยเดือนนี้ (ล้านบาท) · ยอดขายไม่ครบ 60 วัน (แถวแดง)
- [ ] S3: `<ColumnChart>` "ยอดชดเชยประกันรายได้รายเดือน" + `<HBarChart>` "เอกสารค้างตามขั้นตอน Workflow" (**แถวตาม 5 section + เสร็จสิ้น — ไม่มี 04/05**) — ตัวเลข sync กับ stat cards
- [ ] S4 `ModuleGrid.tsx`/`ModuleCard.tsx` — การ์ดทางลัดทุกโมดูล (card abnormal ปิดด้วย feature flag)
- [ ] S5 `ActivityFeed.tsx` (pill+เวลา) + `QuickLinks.tsx`

### 3.2 DocListPage (`features/documents/DocListPage.tsx` — 1 component 2 mode, §k2-list-waiting/related)
- [ ] ฟอร์มค้นหา `DocumentFilterBar.tsx`: **ปี\*** (dropdown พ.ศ.) · เดือน · สถานะ (6 ค่า — ซ่อนใน waiting) · ภาค (`REGIONS8` multi) · ประเภทร้าน (`SEARCH_STORE_TYPES` 4 ค่า multi) · รหัส/ชื่อร้าน · เลขเอกสาร · ยอดขายลดลง% (min–max) · เงินชดเชย (min–max) · รอ(วัน) (min–max) · ปุ่ม `ล้างตัวกรอง` (`RangeInput.tsx`)
- [ ] mode `waiting` → `GET /tasks` (inbox: เฉพาะสถานะ "รอ<role ตัวเอง>ดำเนินการ") · mode `related` → `GET /documents` — **ไม่เลือกปี = ไม่ยิง API + แสดง error ใต้ช่องปี**
- [ ] Stat cards คลิกกรองตาราง: waiting = 4 ใบ (ทั้งหมด / flag60 / รอเกิน 3 วัน / วงเงิน>100,000 เข้า AVP) · related = ทั้งหมด + ต่อสถานะ
- [ ] `DocumentTable.tsx` คอลัมน์: `ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง(%) | จำนวนเงินที่ชดเชย | สถานะ(pill) | รอ (วัน)` · sortable · แถว <60 วัน = `flag-red` · คลิกแถว → `/documents/:docNo`
- [ ] `<Pager>` ผูก `?page&size` ↔ `{page,size,total,items}` + note card ("แดง = ยอดขายไม่ครบ 60 วัน …")

**✔ เกณฑ์ตรวจรับ Phase 3**
- [ ] เปิด `/` → stat 4 ใบ + 2 กราฟขึ้นจากข้อมูล BE จริง · HBar ไม่มีแถว 04/05
- [ ] เปิด `/documents/waiting` → เห็นเฉพาะเอกสารสถานะของ role ตัวเอง
- [ ] เปิด `/documents/related` ไม่เลือกปีแล้วกดค้นหา → error แสดง, network tab **ไม่มี** request
- [ ] เลือกปี+ภาค BN+ประเภท FR Type A → ผลตรง seed · กด `ล้างตัวกรอง` → ฟอร์มกลับค่าเริ่ม
- [ ] แถวร้านยอดขาย <60 วันเป็นสีแดง · คลิกแถว → ไป `/documents/2569/00123` (route ถูก)
- [ ] เปลี่ยน per-page 10→50, กด goto หน้า → ตาราง+info `แสดง X–Y จาก N` ถูกต้อง
- [ ] คลิก stat card "วงเงิน>100,000" → ตารางเหลือเฉพาะแถวเงินชดเชย >100,000

---

## Phase 4 — k2-document + Create (หัวใจระบบ)

### 4.1 โครง DocumentPage (`features/documents/DocumentPage.tsx` — §k2-document)
- [ ] โหลด `GET /documents/{docNo}` ครั้งเดียว → response มีธง `editableSections` + `myRoleView` — **render ตามธง ไม่เดา role เอง** (แทน `data-editrole`/`data-roleonly`/`.edit-only`)
- [ ] S2 head: `เอกสารข้อมูลร้านถูกกระทบ <docNo>` + pill สถานะ (1 ใน 6 ค่า) + ปุ่ม `พิมพ์`
- [ ] `WorkflowStepper.tsx` — 5 ขั้น `06›08›01›02›03` + pill `ขั้นตอนที่ N/5`

### 4.2 ส่วนข้อมูล + กราฟ
- [ ] S3 `DocMetaGrid.tsx` — รอบ/ครั้งที่/เดือน, สถานะ, เลขที่, วันที่สร้าง (พ.ศ.), รหัส/ชื่อร้าน, ภาค, ประเภท, เจ้าของ, นิติบุคคล, วันที่โอน, ผู้ดำเนินการ, ยอดขายลดลง %, ชดเชยล่าสุด, ไฟล์แนบ + ปุ่ม `ข้อมูลยอดขายเพิ่มเติม`
- [ ] S4 `SalesTrendChart.tsx` (เส้น/พื้นที่ 2 ชุด ก่อน–หลัง + marker วันเปิดสาขา + เส้นเฉลี่ย) + `SalesAvgBarChart.tsx` (2 แท่ง + badge −%) — ข้อมูลจาก `GET /documents/{docNo}/sales` (4 หน้าต่าง × 15 วัน)

### 4.3 ร้านเปิดใหม่ (S5) — validate 100%
- [ ] `NewStoresTable.tsx` คอลัมน์: `ลำดับ | รหัสร้าน | ชื่อร้านเปิดใหม่ | ภาค | ประเภทร้าน | เจ้าของร้าน | นิติบุคคล | วันที่เปิดร้าน | วันที่ปิดร้าน | ระยะห่าง(กม.) | %ชดเชย(input) | เงินชดเชย(ร้านใหม่)` · แก้ %ชดเชย ได้เมื่อ section อยู่ใน `editableSections`
- [ ] สูตรแสดงสด: เงินชดเชยร้านใหม่ = ยอดตั้งต้น × %/100
- [ ] ปุ่ม `รีเฟรช` / `คืนค่าก่อนแก้ไข` / `คำนวณเงินชดเชย` — กด**คำนวณ/บันทึก**แล้ว %รวม ≠ 100 → popup เตือน (ข้อความตามหน้า k2-document.html verbatim) และ**ไม่ยิง** `PUT /documents/{docNo}`
- [ ] %รวม = 100 → `PUT /documents/{docNo}` → invalidate `documentKeys.detail` + toast ok

### 4.4 แผนที่ + คู่แข่ง + ปัจจัย (S6–S8)
- [ ] S6 `AllMapPoi.tsx` — SVG วงรัศมี + pulse ร้านถูกกระทบ + หมุดร้านใหม่ + คู่แข่ง + legend + ปุ่ม `Link To ALLMAP`
- [ ] S7 คู่แข่ง `EditableDataTable` (entity competitor): `☑ | ร้านคู่แข่ง | วันที่เปิดกระทบ | รายละเอียดเพิ่มเติม | Action` — dropdown ร้านคู่แข่งจาก `GET /competitors` · แยกป้ายที่มา ALM/USER · ปุ่ม `เพิ่ม`/`บันทึก` → `PUT /documents/{docNo}`
- [ ] S8 ปัจจัยอื่นๆ (entity factordoc): `☑ | ปัจจัยภายนอก | วันที่เริ่มต้น | วันที่สิ้นสุด | รายละเอียดเพิ่มเติม | Action` — dropdown จาก `GET /factors` · ปุ่ม `เพิ่มข้อมูล`/`บันทึก` → `PUT /documents/{docNo}`

### 4.5 ไฟล์แนบ (S9)
- [ ] `AttachmentsTable.tsx`: `ไฟล์แนบ | ตำแหน่ง | ผู้สร้างแนบไฟล์ | รายละเอียดเพิ่มเติม | วัน/เดือน/ปี`
- [ ] ปุ่ม `แนบไฟล์` → ตรวจฝั่ง FE ก่อนอัปโหลด: นามสกุลอยู่ใน `ATTACH_EXTS` **และ** ขนาด ≤ `MAX_FILE_MB` (5MB) — ผิด = toast error ไม่ยิง API · ผ่าน → `POST /documents/{docNo}/attachments` (multipart)

### 4.6 คำนวณเงินชดเชย + ประวัติ (S10–S12)
- [ ] S10 `CompensationCalcPanel.tsx` — readonly (ยอดตั้งต้น / %รวม / รวมร้านใหม่ / อำนาจอนุมัติ `≤100,000 GM · >100,000 AVP`) — **แสดงเฉพาะ view section 08** (ตามธงจาก API)
- [ ] S11 `CompensationHistoryTable.tsx`: `ครั้ง | เดือน/ปีที่กระทบ | จำนวนเงินที่ชดเชย | เดือน/ปีที่ส่งบัญชี | สถานะเอกสาร | ผลการพิจารณา | เอกสาร` (คลิก → เปิดเอกสารครั้งนั้น)
- [ ] S12 `DecisionHistoryTable.tsx` + `DecisionHistoryModal.tsx`: `ชื่อผู้พิจารณา | ตำแหน่ง | ผลการพิจารณา | รายละเอียดการพิจารณา | วัน/เวลา` — จาก `GET /documents/{docNo}/timeline`

### 4.7 แผงพิจารณา (S13) — validate ทีละกรณี
- [ ] `DecisionPanel.tsx` — radio ตัวเลือกผลพิจารณา**ตาม section ปัจจุบัน** (มาจาก API) + textarea `ความคิดเห็นเพิ่มเติม` + ปุ่ม `แนบรูป` / `บันทึก` / `ส่งดำเนินการ`
- [ ] กรณี 1: กด `ส่งดำเนินการ` โดย**ไม่เลือกผล** → popup `MSG.NO_DECISION` (`ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`) — ไม่ยิง API
- [ ] กรณี 2: เลือก "เห็นควรไม่ชดเชย"/"หยุดชดเชย" แต่ไม่กรอกความคิดเห็น → comment required, popup เตือน — ไม่ยิง API
- [ ] กรณี 3: กด `บันทึก` → **ไม่ validate** บันทึก draft ได้เสมอ
- [ ] ผ่าน validate → `POST /documents/{docNo}/actions` `{result, comment}` → BE คำนวณ routing (กฎ 100k อยู่ BE) → toast ok + refetch เอกสาร → สถานะ/stepper ขยับ

### 4.8 CreateDocPage (`features/documents/CreateDocPage.tsx` — §k2-create)
- [ ] S1 pill `เลขที่เอกสารถัดไป · <จาก API>`
- [ ] Tab 1 `สร้างเอกสารใหม่ (นอกเงื่อนไข)`: `รหัสร้านถูกกระทบ*` (`StoreSearchInput` → popup `GET /stores/search?type=impacted`) · `ชื่อร้านถูกกระทบ` (readonly auto) · `ภาค` (readonly) · `ประเภทร้าน` (select 8 ตัวเลือก FR Type A/B/C/C r/บริษัท/พนักงาน/PTT/BGC) · `วันที่โอนเป็นร้าน SP` (date) · `เดือน/ปีที่ถูกกระทบ*` (month) · `ครั้งที่` · `รหัสร้านเปิดใหม่*` (search `type=new`) · `เหตุผลการสร้างเอกสารนอกเงื่อนไข*` (textarea) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` / `สร้างเอกสาร` → `POST /documents` → toast เลขเอกสาร `YYYY/xxxxx` (พ.ศ.) → navigate ไปเอกสาร
- [ ] Tab 2 `สร้างเอกสารที่ FS`: `รหัสร้านถูกกระทบ*` · `ชื่อร้าน` (readonly) · `เดือน/ปีที่ถูกกระทบ*` · `Period Statement (From–To)` · ปุ่ม `เคลียร์` / `ส่งสร้างที่ FS` → `POST /documents` (mode FS)
- [ ] `PendingStatementTable.tsx` "เอกสารที่รอ SBP Statement ส่งกลับ": `รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ` (pill รอ/ส่งกลับแล้ว)

**✔ เกณฑ์ตรวจรับ Phase 4 (เดิน workflow จริงกับ BE)**
- [ ] สร้างเอกสารนอกเงื่อนไข → ได้เลข `2569/xxxxx` → เอกสารสถานะ `รอฝ่าย SBP DSA ดำเนินการ`
- [ ] เคสหลัก ≤100k: 06 ส่งต่อ → 08 คำนวณ+ส่งต่อ → 01 ส่งต่อ → 02 อนุมัติ (เงิน ≤100,000) → สถานะ = `เสร็จสิ้นดำเนินการ` **ไม่ผ่าน 03**
- [ ] เคสสอง >100k: ตั้งเงิน >100,000 → หลัง 02 สถานะ = `รอผู้บริหารสำนักบริหาร SBP ดำเนินการ` → 03 อนุมัติ → `เสร็จสิ้นดำเนินการ`
- [ ] ส่งดำเนินการโดยไม่เลือกผล → popup ตรง verbatim `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`
- [ ] เลือกไม่ชดเชยไม่กรอก comment → ถูกบล็อก · กด `บันทึก` เฉย ๆ → ผ่านโดยไม่ validate
- [ ] แก้ %ชดเชย 2 ร้านเป็น 60+30 → กดคำนวณ → popup %รวม≠100, ไม่ยิง PUT · แก้เป็น 60+40 → บันทึกสำเร็จ เงินชดเชยรายร้านคำนวณถูก
- [ ] แนบไฟล์ .exe → ปฏิเสธ · ไฟล์ .pdf 6MB → ปฏิเสธ (ไม่ยิง API) · .pdf 2MB → ขึ้นตาราง S9
- [ ] view section 08 เห็นแผง S10 คำนวณเงินชดเชย · section อื่นไม่เห็น
- [ ] วันที่ทุกจุดในหน้าเป็น พ.ศ.

---

## Phase 5 — Report

### 5.1 ReportPage (`features/reports/ReportPage.tsx` — §k2-report, รายงานตรวจสอบประกันรายได้ SBP Mall)
- [ ] `ReportSearchForm.tsx`: `ปี*` · เดือน/ปีเริ่ม–ถึง (month) · รหัสร้านกระทบ (+`StorePickerModal`) · ชื่อร้าน (readonly) · รหัสร้านเปิดใหม่ · สถานะ (select 6 ค่า) · **radio ผลการพิจารณา\*: `ประกันรายได้` / `ไม่ประกันรายได้`** · ภาค (`REPORT_REGIONS13` — checkbox 13 รหัส) · ประเภทร้าน (checkbox A–D) · Period Statement From–To · ปุ่ม `เคลียร์` / **`Preview Report`**
- [ ] ไม่เลือกปี → error + ไม่ยิง API (กฎเดียวกับ related)
- [ ] `Preview Report` → `GET /reports/status-summary` → `SummaryLine` (พบ N รายการ / ยอดชดเชยรวม / วงเงิน>100,000 / แถวแดง) + 2 `<HBarChart>` (ตามสถานะ 6 ค่า / ยอดเงินตามภาค)
- [ ] `ReportResultTable.tsx` 19 คอลัมน์ (scroll ใน `.table-wrap`): `รหัสร้านถูกกระทบ | ชื่อร้านถูกกระทบ | ภาค | ประเภทร้าน | เดือนปีที่ถูกกระทบ | วันที่โอนเป็นร้าน SP | Period Statement | รหัสร้านเปิดใหม่ | ชื่อร้านเปิดใหม่ | ภาค (ร้านใหม่) | ประเภทร้าน (ร้านใหม่) | ยอดเงินชดเชย | สถานะ | ชื่อ-นามสกุลผู้ดำเนินการ | ผลการพิจารณา | รอดำเนินการ (วัน) | ครั้งที่ | วันที่สร้าง | เลขที่เอกสาร` · `flag-red` · pill สถานะ
- [ ] ปุ่ม **`Export CSV to Batch`** → `GET /reports/status-summary/export` (เงื่อนไขเดียวกับ preview) → ดาวน์โหลดไฟล์ CSV

**✔ เกณฑ์ตรวจรับ Phase 5**
- [ ] ไม่เลือกปี กด Preview → error, network ไม่มี request
- [ ] เลือกปี + radio `ประกันรายได้` → ตารางเหลือเฉพาะผลชดเชย ตรง seed · สลับ `ไม่ประกันรายได้` → ผลกลับด้าน
- [ ] ติ๊กภาค 2 รหัส + ประเภท A → ผลถูกกรองตรงกัน · ตาราง 19 คอลัมน์ scroll แนวนอนโดย body ไม่ scroll
- [ ] Export CSV → เปิดใน Excel ภาษาไทยไม่เพี้ยน (UTF-8 BOM) เนื้อหาตรงกับ preview
- [ ] เลขเงินคั่นหลักพัน + วันที่ พ.ศ. ทุกคอลัมน์

---

## Phase 6 — Masters (`features/masters/`)

### 6.1 OperatorsPage (§k2-operators — operator_assignments, SRS 3.1.8)
- [ ] `OperatorsPage.tsx` + `OperatorTable.tsx`: `☑ | ชื่อผู้ปฏิบัติงาน | E-Mail | ชื่อตำแหน่ง | ภาคที่รับผิดชอบ | Action(view/edit/del)` — `GET /operators`
- [ ] `EntityModal` schema operator: ชื่อ / อีเมล / ชื่อตำแหน่ง (select ตาม `SECTIONS` 5 ค่า) / ภาค (select `REGIONS8` + `-`) / เหตุผล — **ช่องภาคแสดงเฉพาะเมื่อตำแหน่ง = ฝ่ายส่งเสริมธุรกิจ SBP** · POST/PUT/DELETE `/operators/{id}` (reason บังคับ)
- [ ] `EmployeeSearchModal.tsx` — ปุ่ม `ค้นหาพนักงาน (Pop Up)` → `GET /employees/search` → เลือก → เติมฟอร์มเพิ่มแถว + toast
- [ ] `AuditHistoryTable` ผูก `GET /audit-logs?table=operator_assignments` + `SrsConditionsCard`

### 6.2 FactorsPage (§k2-factors — external_factors, SRS 3.1.9)
- [ ] `FactorsPage.tsx` + ตาราง `☑ | รหัสปัจจัย | ชื่อปัจจัย | รายละเอียดเพิ่มเติม | Action` + toolbar ค้นหา/`เคลียร์` — CRUD `/factors` · `/factors/{code}`
- [ ] schema factor: factor_code / factor_name / factor_remark / เหตุผล — **แก้ได้เฉพาะชื่อ+รายละเอียด** (รหัสล็อกตอน edit)
- [ ] รหัสซ้ำ → แสดง `message` จาก API ตรง ๆ · reason บังคับทุก edit/delete
- [ ] `AuditHistoryTable` (`?table=external_factors`) + `SrsConditionsCard`

### 6.3 PermissionsPage (§k2-permissions — SRS 3.1.1)
- [ ] `PermissionsPage.tsx` — state roles/menus/dirty + ปุ่ม `เพิ่ม Role` / `เพิ่มเมนู` / `บันทึกสิทธิ์` (+badge จำนวน dirty)
- [ ] `RolesTable.tsx`: `Code | Role | คำอธิบาย | Action` — 8 role (00 Default … 10 UserViewer) `GET /roles` · role `is_system` → ปุ่มลบ/แก้รหัส **disabled** · CRUD `/roles/{roleCode}`
- [ ] `PermissionMatrix.tsx` ×2 (เมนู main / เมนู master — master ตัด role 00, off = `✗`): role เป็นคอลัมน์, เมนูเป็นแถว, `MatrixToggleCell` toggle `✓/–` (dirty = amber, optimistic update ได้) — โหลด `GET /menu-permissions`, บันทึก `PUT /menu-permissions/{menuCode}`
- [ ] CRUD เมนู `POST/PUT/DELETE /menus/{menuCode}` — ลบ = confirm cascade สิทธิ์ทุก role · เพิ่ม/ลบ role → คอลัมน์ matrix sync
- [ ] `AuditLogTable` + `AcceptanceCriteriaCard` (เฉพาะ Role 01/02 จัดการได้)

**✔ เกณฑ์ตรวจรับ Phase 6**
- [ ] เพิ่ม operator ผ่าน popup ค้นพนักงาน → แถวขึ้น + audit ขึ้นแถวใหม่ทันที (invalidate query — ไม่ต้อง refresh หน้า)
- [ ] เลือกตำแหน่ง = ฝ่ายส่งเสริมธุรกิจ SBP → ช่องภาคโผล่ · ตำแหน่งอื่น → ซ่อน
- [ ] แก้ factor โดยไม่กรอกเหตุผล → submit ไม่ได้ · เพิ่ม factor รหัสซ้ำ → error message จาก BE แสดงตรง ๆ
- [ ] toggle matrix 3 ช่อง → badge dirty = 3 → กดบันทึก → PUT ต่อเมนู, badge หาย, refresh แล้วค่าคงอยู่
- [ ] role `is_system` (เช่น 00) → ปุ่มลบ disabled · ลบเมนู → สิทธิ์เมนูนั้นหายทุก role
- [ ] ทุก mutation สำเร็จมี toast ok และลง AuditHistoryTable

---

## Phase 7 — Admin (`features/admin/`)

### 7.1 SystemConfigPage (§system-config — system_configs)
- [ ] `SystemConfigPage.tsx` + `ConfigTable.tsx`: `☑ | Config Key | หมวดหมู่ | ค่า (Value) | ชนิดข้อมูล | หน่วย | คำอธิบาย | แก้ไขได้ | Action` — `GET /configs` + filter หมวดหมู่ + ค้นหา + `DonutChart` สัดส่วนตามหมวด
- [ ] แถว `is_editable=false` → ไอคอน lock, ปุ่ม edit/del ซ่อน/disabled — BE ก็ปฏิเสธ
- [ ] `EntityModal` schema config — **validate ค่า ตาม `value_type`** (number/boolean/string/json) ก่อน `PUT /configs/{key}` · เพิ่ม `POST /configs` · ปุ่ม `Invalidate Cache`
- [ ] `AuditHistoryTable` + `InfoCallout` (dot-notation key, cache 5 นาที)

### 7.2 EmailTemplatesPage (§plan-email — EM-01–08)
- [ ] `EmailTemplatesPage.tsx` — `GET /email-templates` · ตาราง map (`Template | ชื่อ | จุดที่ส่งใน Flow | ผู้รับ (TO) | แหล่งกติกาผู้รับ | ความถี่` — คลิกแถวเลื่อนไป card) + Tabs 3 กลุ่ม (Workflow EM-01–03 / เตือนงานค้าง EM-04–05 / Batch EM-06–08)
- [ ] `EmailTemplateCard.tsx` ×8 — meta grid + `MailPreview` (From/To/Cc/Subject + body) — **From/To/Cc read-only จาก status_email_rules** · EM-01 มี selector 6 สถานะ live-rewrite preview
- [ ] Editor: `RichTextToolbar` (bold/italic/underline/strike, สี, list, table picker) + `MergeVariableChips` ต่อ template (subject แทรก text, body แทรก atom) — **ห้ามใช้ execCommand ตรง ห้ามเพิ่ม lib ใหญ่เกินจำเป็น**
- [ ] ปุ่มบันทึก `PUT /email-templates/{code}` · `รีเซ็ต` `POST /email-templates/{code}/reset` · `รีเซ็ตทั้งหมดเป็น Default` `POST /email-templates/reset-all` (confirm ก่อน)
- [ ] `AuditHistoryTable` (`?table=email_templates`)

### 7.3 BatchJobsPage (§job-batch — 11 entry points Jobs 1–10 + 8b)
- [ ] `BatchJobsPage.tsx` — `GET /jobs` · Stat 4 ใบ + Donut/Bar/Spark + `PhaseStrip` เฟส A–E (chip คลิก→select job)
- [ ] `JobTable.tsx`: `Job | ชื่องาน / Main Class | เฟส | ประเภท | กำหนดการ (Cron) | รอบล่าสุด | ผลล่าสุด | รอบถัดไป | สถานะ | (action)` — คลิก → detail
- [ ] `JobDetailPanel.tsx` + toggle เปิด/ปิด (`PUT /jobs/{jobNo}/enabled`) + Tabs 4: พารามิเตอร์ (แก้เฉพาะ editable → `PUT /jobs/{jobNo}/params`) / Flowchart SVG / Database ที่ใช้ / ประวัติการรัน (`GET /jobs/{jobNo}/runs` — ตาราง `เริ่มรัน | ระยะเวลา | จำนวนแถว | ไฟล์ที่เกี่ยวข้อง | ผลลัพธ์ | หมายเหตุ`)
- [ ] run bar: เลือกเดือน + `สั่งรันทันที` → `POST /jobs/{jobNo}/run` — BE guard รันซ้อน → แสดง error message ตรง ๆ
- [ ] `AuditHistoryTable` (job_configs) + `InfoCard`

**✔ เกณฑ์ตรวจรับ Phase 7**
- [ ] config `is_editable=false` → กดแก้ไม่ได้จาก UI, ยิง PUT ตรง (curl) BE ก็ปฏิเสธและ FE แสดง message
- [ ] แก้ config ชนิด number ใส่ตัวอักษร → validate ก่อน save ไม่ผ่าน
- [ ] แก้ subject EM-01 → preview เปลี่ยนทันที → บันทึก → refresh ค่าคงอยู่ + ลง audit · กดรีเซ็ต → กลับ default
- [ ] EM-01 selector เปลี่ยนสถานะ → To/Cc/เนื้อหา preview เปลี่ยนตาม rules (แก้เองไม่ได้)
- [ ] สั่งรัน job ที่กำลังรัน → error จาก BE แสดงตรง ๆ ไม่ crash · toggle ปิด job → สถานะเปลี่ยน + audit ลง
- [ ] ประวัติรันแสดงเรียงล่าสุดก่อน + ปุ่ม `ดู Log`

---

## Phase 8 — Hardening

### 8.1 Abnormal (สร้างเสร็จแต่ปิด flag)
- [ ] `features/abnormal/AbnormalListPage.tsx` ตาม §k2-list-abnormal: stat 4 ใบ (ทั้งหมด/ยังไม่แจกงาน/แจกงานแล้ว/แก้ไขแล้ว — assignment status แยกจากสถานะเอกสาร) · filter (ภาค 8, สาเหตุ 4, สถานะ 3, ผู้รับผิดชอบ) · ตาราง `☑ | ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ | Action(view+assign)` + `flag-red` + bulk `แจกงานที่เลือก` + `AssignJobModal`
- [ ] route `/documents/abnormal` + เมนู + card หน้าแรก เปิด/ปิดด้วย `VITE_FEATURE_ABNORMAL` จุดเดียว (`isFeatureEnabled('abnormal')`)

### 8.2 Test
- [ ] vitest unit: constants/format + business rule (validate แผงพิจารณา 3 กรณี: ไม่เลือกผล / ไม่ชดเชยไม่มี comment / บันทึกไม่ validate) + validate %รวม 100 + validate ไฟล์ (ext, 5MB)
- [ ] component test ผ่าน **msw** (ห้าม mock axios ตรง): DocListPage (ปี required), DecisionPanel, NewStoresTable, EntityModal
- [ ] smoke render ทุก page (14 route) ไม่ throw
- [ ] Playwright e2e 1 เส้น: login → inbox → เปิดเอกสาร → เลือกผล+comment → ส่งดำเนินการ → toast สำเร็จ + สถานะขยับ

### 8.3 คุณภาพ/ความถูกต้อง
- [ ] ErrorBoundary ต่อ route + fallback ภาษาไทย · query error แสดงใน `<NoticeCard>` ไม่ crash · `lazy()` + `<PageSkeleton>` ครบทุก page
- [ ] script grep ตรวจข้อความไทย verbatim เทียบ prototype: `MSG.NO_DECISION`, `ไม่พบรายการตามเงื่อนไขที่กรอง`, สถานะ 6 ค่า, ป้ายปุ่มหลัก — และ grep ยืนยัน**ไม่มี** "04", "05", "ฝ่ายบัญชี SBP", "บัญชีปฏิบัติการภาค" ในโค้ด FE
- [ ] a11y ขั้นต่ำ: ทุก input มี label · modal focus-trap + Esc ปิด · ปุ่มไอคอนมี `aria-label`
- [ ] README.md: วิธีรัน dev/test/build + ตาราง env + โครงโฟลเดอร์ย่อ
- [ ] `pnpm build` + `pnpm preview` + ตรวจ bundle (ไม่มี chart/UI lib แปลกปลอม, code-split ต่อ route)

**✔ เกณฑ์ตรวจรับ Phase 8 (ปิดงาน)**
- [ ] ตั้ง `VITE_FEATURE_ABNORMAL=true` → เมนู+route+card โผล่ครบ · `false` → หายทุกจุด, เข้า URL ตรง → redirect
- [ ] `pnpm test` เขียว 100% · e2e Playwright ผ่าน
- [ ] ทุกหน้าใช้งานได้กับ BE จริงครบทั้ง 14 route (ไล่ตามตาราง traceability ข้างล่าง)
- [ ] script grep verbatim ผ่าน — ไม่มีข้อความเพี้ยนจาก SRS, ไม่มี section 04/05
- [ ] build ไม่มี warning ผิดปกติ · เปิด preview เดิน happy path ≤100k ครบจบ

---

## ตาราง Traceability — Route ↔ หน้า prototype ↔ Endpoints ↔ Phase

| Route | หน้า prototype | Endpoints หลักที่ใช้ | Phase |
|---|---|---|---|
| `/login` | *(ไม่มี — โทนเดียวกัน)* | `POST /auth/login` · `POST /auth/refresh` · `GET /auth/me` · `GET /me/menus` | 1 |
| `/` | index.html | `GET /dashboard/summary` | 3 |
| `/documents/waiting` | k2-list-waiting.html | `GET /tasks` | 3 |
| `/documents/related` | k2-list-related.html | `GET /documents` (ปี required) | 3 |
| `/documents/create` | k2-create.html | `POST /documents` · `GET /stores/search` | 4 |
| `/documents/:docNo` | k2-document.html | `GET/PUT /documents/{docNo}` · `POST .../actions` · `GET .../timeline` · `POST .../attachments` · `GET .../sales` · `GET /competitors` · `GET /factors` | 4 |
| `/reports/income-audit` | k2-report.html | `GET /reports/status-summary` · `GET .../export` · `GET /stores/search` | 5 |
| `/masters/operators` | k2-operators.html | `GET/POST/PUT/DELETE /operators` · `GET /employees/search` · `GET /workflow-sections` · `GET /audit-logs` | 6 |
| `/masters/factors` | k2-factors.html | `GET/POST/PUT/DELETE /factors` · `GET /audit-logs` | 6 |
| `/masters/permissions` | k2-permissions.html | `GET/PUT /menu-permissions` · `GET/POST/PUT/DELETE /roles` · `POST/PUT/DELETE /menus` · `GET /audit-logs` | 6 |
| `/admin/system-config` | system-config.html | `GET/POST/PUT/DELETE /configs` | 7 |
| `/admin/email-templates` | plan-email.html | `GET/PUT /email-templates` · `POST .../reset` · `POST /email-templates/reset-all` | 7 |
| `/admin/batch-jobs` | job-batch.html | `GET /jobs` · `PUT /jobs/{no}/params` · `PUT /jobs/{no}/enabled` · `POST /jobs/{no}/run` · `GET /jobs/{no}/runs` | 7 |
| `/documents/abnormal` | k2-list-abnormal.html *(feature flag)* | `GET /documents` (filter abnormal) + assign | 8 |

> หน้ากลุ่ม Flow/Database/Plan (`flow-fgi`, `k2-flow`, `plan-flow`, `*-database`, `plan-api`) = เอกสารออกแบบ **ไม่พอร์ต**เข้าแอปจริง (plan-fe.md §4)

---

## ภาคผนวก A — ข้อความไทย verbatim ที่ script grep (Phase 8.3) ต้องเจอตรงตัว

| Key | ข้อความ (ห้ามแก้แม้แต่วรรค) | ใช้ที่ |
|---|---|---|
| `MSG.NO_DECISION` | `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ` | DecisionPanel (Phase 4.7) |
| empty-state | `ไม่พบรายการตามเงื่อนไขที่กรอง` | DataTable ทุกหน้า |
| สถานะ 1 | `รอฝ่าย SBP DSA ดำเนินการ` | Pill สถานะ (section 06) |
| สถานะ 2 | `รอเจ้าหน้าที่ SBP DSA ดำเนินการ` | Pill สถานะ (section 08) |
| สถานะ 3 | `รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ` | Pill สถานะ (section 01) |
| สถานะ 4 | `รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ` | Pill สถานะ (section 02) |
| สถานะ 5 | `รอผู้บริหารสำนักบริหาร SBP ดำเนินการ` | Pill สถานะ (section 03) |
| สถานะ 6 | `เสร็จสิ้นดำเนินการ` | Pill สถานะ (จบ) |
| ปุ่มหลัก | `ส่งดำเนินการ` · `บันทึก` · `ล้างตัวกรอง` · `เคลียร์ค่าเริ่มใหม่` · `สร้างเอกสาร` · `ส่งสร้างที่ FS` · `Preview Report` · `Export CSV to Batch` · `แจกงานที่เลือก` · `สั่งรันทันที` · `รีเซ็ตทั้งหมดเป็น Default` · `Invalidate Cache` | ตามหน้า |
| ช่อง audit | `เหตุผลการแก้ไข (บันทึกลง audit_logs)` | EntityModal edit |
| note ตาราง | `แดง = ยอดขายไม่ครบ 60 วัน` | DocList / Report |

ข้อความที่ grep แล้ว**ต้องไม่เจอ**ในโค้ด FE: `ฝ่ายบัญชี SBP` · `บัญชีปฏิบัติการภาค` · สถานะที่ขึ้นด้วย section 04/05 · ชื่อ lib ต้องห้าม (`tailwind` `@mui` `antd` `recharts` `chart.js` `echarts` `d3`)

## ภาคผนวก B — ค่าคงที่ที่ต้องตรงตัว (สรุปจาก plan-fe.md §7)

- `SECTIONS` (ลำดับตายตัว): `06 ฝ่าย SBP DSA` → `08 เจ้าหน้าที่ SBP DSA` → `01 ฝ่ายส่งเสริมธุรกิจ SBP` → `02 GM ส่งเสริมธุรกิจฯ` → `03 ผู้บริหารสำนักบริหาร SBP (AVP)`
- `AVP_THRESHOLD = 100_000` — ใช้แค่**แสดงป้าย** (เช่น stat card "วงเงิน>100,000 เข้า AVP", แผง S10) — routing จริงอยู่ BE
- `REGIONS8 = ['BE','BN','BS','BW','RC','RE','RN','RS']` (มี RC ไม่มี RW) · `REPORT_REGIONS13` = 13 รหัสตาม k2-report.html
- `SEARCH_STORE_TYPES` (ตัวกรองค้นหา 4 ค่า): `FR Type A` `FR Type B` `FR Type C` `พนักงาน` — **คนละชุด**กับประเภทร้าน 8 ตัวเลือกในฟอร์ม k2-create (FR Type A/B/C/C r/บริษัท/พนักงาน/PTT/BGC)
- `MAX_FILE_MB = 5` · `ATTACH_EXTS` = `vsd dwg afp pdf mda zip wav mp3 gif jpg tif tiff htm html txt xml mpg mov ivs doc docx xls xlsx pps ppt pot csv`
- เลขเอกสาร `YYYY/xxxxx` ปี**พ.ศ.** (เช่น `2569/00123`) — format ผ่าน `formatDocNo()` จุดเดียว
- วันที่แสดงผลทุกจุด = พ.ศ. ผ่าน `formatDateThai()` เท่านั้น (API รับ-ส่ง ISO ค.ศ.)

## ภาคผนวก C — Definition of Done ต่อ checkbox (ใช้ตัดสินว่า "ติ๊กได้")

1. โค้ดอยู่ path ตามที่ระบุในข้อ + ผ่าน `eslint` + `tsc --noEmit`
2. หน้าตา/ป้ายข้อความเทียบหน้า prototype (`*.html` เดิม) แล้วตรง — เปิดคู่กันเช็คด้วยตา
3. เรียก endpoint จริงตามที่ระบุ (dev ผ่าน msw ได้ แต่สัญญา request/response ตรง `api.md`)
4. จุด validate ในข้อนั้นมี test (unit หรือ component) อย่างน้อย 1 เคส
5. mutation สำเร็จ → toast ok + `invalidateQueries` ด้วย key จาก factory (ห้าม key มือเปล่า)
6. ไม่เพิ่ม dependency ใหม่นอกรายการ plan-fe.md §2 — ถ้าจำเป็นให้หยุดถามก่อน
