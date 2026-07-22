# checklist-be.md — Checklist สร้าง Backend (Node.js + Express + Prisma + PostgreSQL)

> **วิธีใช้:** ทำตามลำดับ Phase 0 → 7 ติ๊กทีละข้อ — ทุก Phase มี **✔ เกณฑ์ตรวจรับ** เป็น test case รันได้จริง ต้องผ่านครบก่อนไปต่อ
> spec เต็มอยู่ `plan-be.md` · สัญญา API = `api.md` + `SQL_BY_PATH` ใน `plan-api.html` · สัญญากลาง = `LLDD/BE/LLDD-BE-API-Common-Contracts.md` + `LLDD/FE/LLDD-FE-Integration-Contracts.md` · schema = `database.md` · transition = `workflow.md`
>
> **กติกาเหล็ก (ห้ามเปลี่ยน):**
> - workflow **5 ขั้น 06→08→01→02→03** (ตัดขั้นบัญชี 04/05 ตาม SDD v7.5)
> - สถานะเอกสาร **6 ค่า** · เลขเอกสาร `พ.ศ./xxxxx` running ต่อปี จองด้วย `FOR UPDATE`
> - กฎวงเงิน: ชดเชย/ไม่ชดเชย **> 100,000 → AVP (03) แล้วจบ** · ชดเชย **≤ 100,000 จบที่ GM (02)**
> - Error ทุกเส้นรูปเดียว `{code,message}` — ข้อความไทย **verbatim ตาม SRS**
> - Gen Flow Gate **6 เกณฑ์** ครบทุกข้อ · Job 4 ครอบ transaction/outbox (**P0**)
> - **ห้ามเก็บ secret ใน DB/system_configs** — credential อยู่ .env / Secret Manager
> - กลุ่ม abnormal-stores 2 เส้น (`GET /abnormal-stores`, `POST /abnormal-stores/assign`) **ยังไม่ทำ — skip** (comment รอตัดสินใจ · ทำแล้วจะเป็น 63 เส้น)

---

## Phase 0 — Scaffold + Schema (34 ตาราง)

### 0.1 โครงโปรเจกต์
- [ ] init โปรเจกต์ TypeScript strict + Express 4 + pino + helmet/cors — โครงโฟลเดอร์ **module-per-domain + layered** ตาม plan-be.md §2 (`routes → controller → service → repository → prisma` · controller ห้ามมี business logic · service ห้ามแตะ req/res · ข้าม module ได้เฉพาะชั้น service)
- [ ] husky + lint-staged + commitlint (Conventional Commits) + path alias `@/` = `src/`
- [ ] GitHub Actions CI: `lint → tsc --noEmit → prisma validate → test → build` + postgres service container
- [ ] `config/env.ts` — zod validate ทุกตัวแปร env (ดูตาราง ENV ท้ายไฟล์) — ขาดตัวไหน **fail fast ตอน boot**
- [ ] `lib/errors.ts` — `AppError{code,message,status}` + `errorHandler` middleware แปลงเป็น `{code,message}` · 400 VALIDATION / 401 AUTH / 403 FORBIDDEN / 404 NOT_FOUND / 409 CONFLICT
- [ ] `lib/date.ts` — แปลง พ.ศ.↔ค.ศ. (payload = ISO ค.ศ. · เลขเอกสาร/ไฟล์ interface = พ.ศ.)
- [ ] `GET /healthz` (liveness — ไม่แตะ DB)

### 0.1b Common API contracts
- [ ] `lib/http-contract.ts` — constants: base `/api/v1`, JSON UTF-8, page default/max, allowed public/service-token/API-key endpoint lists
- [ ] `lib/messages.ts` — รวมข้อความไทย verbatim จาก SRS ที่ BE ต้องคืน; endpoint ห้าม hardcode message กระจาย
- [ ] `lib/pagination.ts` — parse/validate `page,size` และ build `{page,size,total,items}` shape กลาง
- [ ] `middlewares/requestId.ts` — รับ `X-Request-Id` หรือ generate ใหม่ แล้ว bind เข้า pino context
- [ ] `middlewares/auth.ts` + `serviceToken.ts` + `apiKey.ts` — แยก JWT user endpoint, service token `/workflows/instances`, API key `/interfaces/sta/ack`
- [ ] `middlewares/rbac.ts` — `requireRole`, `requireMenu`, `requireCurrentTaskOwner`; BE เป็น source of truth ของ sidebar/edit/action permission
- [ ] `modules/common/contracts.test.ts` — supertest ยืนยัน error `{code,message}`, list envelope, auth 401, forbidden 403, validation 400, conflict 409, attachment 413/415

### 0.2 Prisma schema — Zone A · FGI/FCS (7 ตาราง)
- [ ] `fgi_impact_processes` ★ hub รอบชดเชย — PK `id` · `impacted_store_code` → impacted_stores · enum `action_status` (Y/W/N) · `last_compensation_amount`
- [ ] `fgi_impact_stores` — PK `id` · FK `impact_process_id` → fgi_impact_processes · `impacted_store_code` → impacted_stores · enum `verify_status` (W/P/Y/N) · enum `workflow_generation_status` (W/Y/N)
- [ ] `fgi_impact_sales_summaries` — PK `id` · FK `impact_process_id` · `growth_rate_diff` (nullable — เคส NULL = รอตรวจสอบ) · `total_working_days` (เกณฑ์ 60 วัน)
- [ ] `sales_transactions` — PK `id` · FK `sales_summary_id` → fgi_impact_sales_summaries · ยอดขายรายวัน 4 หน้าต่าง × 15 วัน · `sales_diff` / outlier ≥ 50
- [ ] `fgi_impact_competitors` — PK `id` · FK `impact_process_id` · `data_source = 'ALM'` · งวดล่าสุดต่อร้าน
- [ ] `fcs_qssi_scores` — PK `id` · **UK: store_id + category_code + งวด** · 6 หมวด (8,9,12,1,10,16)
- [ ] `interface_transactions` — PK `id` · **typed FK 3 คอลัมน์: `impact_process_id` / `sales_summary_id` / `doc_no` — ห้าม polymorphic key** · `data_name` เป็น enum · enum `sta_status` (I/C/A/N/S/Z)

### 0.3 Prisma schema — Zone B · K2 เอกสาร & Workflow (9 ตาราง)
- [ ] `compensation_documents` — PK `doc_no` (`YYYY/xxxxx` พ.ศ.) · FK `status_code` → document_statuses · `current_section_code` → workflow_sections · `impacted_store_code` · **`impact_process_id` → fgi_impact_processes (FK ใหม่ 1 รอบ : 1 เอกสาร)**
- [ ] `document_new_stores` — PK `id` · FK `doc_no` · `distance_km` · `%ชดเชย` (**ผลรวมต่อเอกสาร = 100%** — enforce ชั้น service)
- [ ] `document_competitors` — PK `id` · FK `doc_no` · `competitor_code` → competitors · enum `source_system` (ALM/USER)
- [ ] `document_external_factors` — PK `id` · FK `doc_no` · `factor_code` → external_factors · ช่วงวันที่
- [ ] `consideration_logs` — PK `id` · FK `doc_no` · ผู้พิจารณา/section/ผล/เวลา · enum `result_category` (APPROVE/REJECT/PENDING)
- [ ] `document_attachments` — PK `id` · FK `doc_no` · ≤ 5MB ต่อไฟล์ · section ที่แนบ
- [ ] `compensation_histories` — PK `id` · `store_code` · `ref_doc_no` · `submit_account_month` (→ ไฟล์ FRBC0001 Job 6)
- [ ] `workflow_instances` — PK `instance_id` · FK `doc_no` (unique — 1 เอกสาร : 1 instance) · สถานะ instance
- [ ] `workflow_tasks` — PK `task_id` · FK `instance_id` · `section_code` · `assignee_employee_id` · สถานะ open/closed (ฐาน inbox + reminder + escalation)

### 0.4 Prisma schema — Zone C · Shared Master/Config (18 ตาราง)
- [ ] `stores` — PK `store_code` — master สาขาทุกประเภท (แหล่ง `/stores/search?type=new`)
- [ ] `impacted_stores` — PK `store_code` — subset SP · สะพาน Zone C ↔ A (`= fgi_impact_stores.impacted_store_code`)
- [ ] `workflow_sections` — PK `section_code` — **5 แถวใช้งาน (06/08/01/02/03)** + 04/05 `is_active=false` (อ้างอิงประวัติ)
- [ ] `document_statuses` — PK `status_code` — **6 ค่า** (ตัด "รอฝ่ายบัญชี SBP" / "รอบัญชีปฏิบัติการภาค")
- [ ] `roles` — PK `role_code` (8 role: 00,01,02,03,04,05,06,10) · `is_system` กันลบ/แก้รหัส
- [ ] `menus` — PK `menu_code` · `menu_group` (MAIN/MASTER) · `sort_order` · `is_system`
- [ ] `menu_permissions` — **composite PK (role_code, menu_code)** · `can_access`
- [ ] `operator_assignments` — PK `id` · `section_code` · `zone_code` · FK `employee_id` → employees
- [ ] `employees` — PK `employee_id` — master HR (แหล่ง `/employees/search`)
- [ ] `external_factors` — PK `factor_code` — **รหัสห้ามซ้ำ**
- [ ] `competitors` — PK `competitor_code` — 24 ราย
- [ ] `audit_logs` — PK `id` · generic `table_name` + `ref_key` · `action_type` · `old_value` → `new_value` · `reason` · `updated_by` · `updated_at`
- [ ] `status_email_rules` — PK `status_code` · `to_section_code` / `cc_section_code` → workflow_sections
- [ ] `email_templates` — PK `template_code` (EM-01–08) · subject/body + ตัวแปร merge + default สำหรับ reset
- [ ] `user_accounts` — PK `employee_id` · FK `role_code` → roles · password bcrypt
- [ ] `job_configs` — PK `job_no` · cron + พารามิเตอร์ editable · `enabled` (11 jobs)
- [ ] `job_run_histories` — PK `run_id` · FK `job_no` · เวลา/แถว/ไฟล์/ผล · สถานะ RUNNING ใช้เป็น lock
- [ ] `system_configs` — PK `config_key` (dot notation) · `category` (IMPACT/WORKFLOW/DOCUMENT/AUTH/NOTIFICATION/BATCH) · `value_type` (NUMBER/STRING/BOOLEAN/JSON/CRON) · `is_editable` · **ห้ามมี secret**
- [ ] ตาราง counter เลขเอกสาร (เช่น `doc_no_counters` PK ปี พ.ศ. + `last_no`) สำหรับ `FOR UPDATE`

### 0.5 Migration แรก
- [ ] `prisma migrate dev` สร้าง migration แรก — enum/check constraint ครบทุก status domain ตามข้อ 0.2–0.4

### ✔ เกณฑ์ตรวจรับ Phase 0
- [ ] `npx prisma migrate dev` ผ่านไม่มี error · `psql -c "\dt"` นับตารางได้ **34** (+ตาราง counter/_prisma_migrations ไม่นับ)
- [ ] `curl -s localhost:3000/healthz` → **200** `{"status":"ok"}`
- [ ] `curl -s localhost:3000/api/v1/ไม่มีอยู่` → **404** body รูป `{"code":"NOT_FOUND","message":"..."}`
- [ ] `GET` list fixture ใดก็ได้ → body มี `{page,size,total,items}` และ `items` เป็น array root เดียว
- [ ] endpoint ที่ไม่มี JWT → 401 `{code:"AUTH_401",message}`; role ผิด → 403 `{code:"FORBIDDEN",message}`
- [ ] insert ค่า status นอก enum เช่น `verify_status='X'` ผ่าน SQL ตรง → ถูก DB reject
- [ ] ลบตัวแปร env สำคัญ (เช่น DATABASE_URL) แล้ว boot → process ตายทันทีพร้อม log บอกตัวแปรที่ขาด

---

## Phase 1 — Auth & RBAC (4 เส้น)

### 1.1 Seed ขั้นต่ำ
- [ ] `roles` 8 แถว (00 Default … 10 UserViewer) · `menus` + `menu_permissions` ตาม k2-permissions.html · `employees` + `user_accounts` 1 บัญชีต่อ role (bcrypt cost ≥ 10)

### 1.2 Endpoint (4 เส้น)
- [ ] `POST /auth/login` — body `{username,password}` · ตรวจ bcrypt → sign accessToken (30 นาที) + refreshToken (8 ชม.) · payload `{employeeId, roleCode}` · รหัสผิด → **401** message ไทย
- [ ] `POST /auth/refresh` — body `{refreshToken}` → accessToken ใหม่ · refresh หมดอายุ/ปลอม → **401**
- [ ] `GET /auth/me` — joined `user_accounts + employees + roles` · ไม่มี/หมดอายุ token → **401**
- [ ] `GET /me/menus` — join `menu_permissions` ที่ `can_access=true` ของ role ผู้เรียก (FE สร้าง sidebar)

### 1.3 Middleware
- [ ] `auth.ts` — Bearer → verify → `req.user` · `requireRole('01','03',...)` → ไม่มีสิทธิ์ **403** · `validate.ts` (zod body/query/params → 400)
- [ ] rate limit `POST /auth/login` (express-rate-limit)

### ✔ เกณฑ์ตรวจรับ Phase 1 (supertest)
- [ ] login ถูก → 200 + ได้ 2 token · login รหัสผิด → 401 `{code:"AUTH_401",...}`
- [ ] เรียก `GET /auth/me` ด้วย token หมดอายุ (mock เวลา/sign อายุ 1 วิ) → 401
- [ ] `POST /auth/refresh` ด้วย refresh ที่ยัง valid → ได้ access ใหม่ ใช้เรียก `/auth/me` ได้ 200
- [ ] `GET /me/menus` ด้วยบัญชี role 03 vs role 10 → รายการเมนูต่างกันตรงตาม k2-permissions
- [ ] เส้นที่ requireRole('03') เรียกด้วย role 10 → 403
- [ ] ยิง login ผิดรัว ๆ เกิน limit → 429

---

## Phase 2 — Lookup + Masters + Audit (4 + 19 เส้น)

### 2.1 Lookup (4 เส้น)
- [ ] `GET /stores/search?type=impacted|new&q=` — impacted → `impacted_stores` · new → `stores` · type อื่น/ไม่ส่ง → 400
- [ ] `GET /competitors` — master 24 ราย
- [ ] `GET /document-statuses` — **6 ค่า** (เฉพาะ active)
- [ ] `GET /workflow-sections` — **5 ขั้น** (06/08/01/02/03 · ไม่รวม 04/05 ที่ is_active=false)

### 2.2 Audit helper
- [ ] `writeAudit(tx, {table_name, ref_key, action_type, old_value, new_value, reason, updated_by})` — updated_by จาก JWT · ใช้ร่วมทุก master mutation ใน transaction เดียวกับการแก้

### 2.3 Masters (19 เส้น)
- [ ] `GET /operators` (paginate + filter section/zone)
- [ ] `POST /operators` — validate employee_id มีจริง
- [ ] `PUT /operators/{id}` — **ไม่ส่ง `reason` → 400** · ลง audit_logs
- [ ] `DELETE /operators/{id}` — reason บังคับ → audit
- [ ] `GET /employees/search?q=` — popup 3.1.8
- [ ] `GET /factors`
- [ ] `POST /factors` — **`factor_code` ซ้ำ → 409** message ไทยตาม SRS
- [ ] `PUT /factors/{code}` — reason บังคับ → audit
- [ ] `DELETE /factors/{code}` — reason บังคับ · มี document_external_factors อ้างอยู่ → 409
- [ ] `GET /menu-permissions` — matrix 8 role × เมนู
- [ ] `PUT /menu-permissions/{menuCode}` — อัปเดต can_access ต่อ role · reason → audit
- [ ] `GET /roles`
- [ ] `POST /roles` — สร้าง role ใหม่ = **สร้างแถว menu_permissions `can_access=false` ทุกเมนู** อัตโนมัติ
- [ ] `PUT /roles/{roleCode}` — `is_system=true` แก้รหัส/ลบ → **403** · reason → audit
- [ ] `DELETE /roles/{roleCode}` — is_system → 403 · ลบ = cascade menu_permissions
- [ ] `POST /menus` — เมนูใหม่ = สร้างสิทธิ์ false ทุก role
- [ ] `PUT /menus/{menuCode}` — is_system กันแก้รหัส · reason → audit
- [ ] `DELETE /menus/{menuCode}` — cascade สิทธิ์ทุก role
- [ ] `GET /audit-logs?table=&refKey=&page=&size=` — paginate

### ✔ เกณฑ์ตรวจรับ Phase 2
- [ ] `PUT /operators/{id}` ไม่ส่ง reason → 400 · ส่งครบ → 200 แล้ว `GET /audit-logs?table=operator_assignments` เห็นแถว old_value→new_value + reason + updated_by ถูกต้อง
- [ ] `POST /factors` ด้วยรหัสที่มีอยู่ → **409** message ไทยตรง SRS ตัวอักษรต่อตัวอักษร
- [ ] `DELETE /roles/00` (is_system) → 403 · `POST /roles` role ใหม่ → นับแถว menu_permissions เพิ่ม = จำนวนเมนูทั้งหมด (can_access=false ทุกแถว)
- [ ] `DELETE /menus/{code}` → menu_permissions ของเมนูนั้นหายทั้ง 8 role
- [ ] ทุกเส้น list ตอบ `{page,size,total,items}` — เช็คด้วย `GET /operators?page=2&size=5`
- [ ] `GET /workflow-sections` ตอบ 5 แถวเท่านั้น (ไม่มี 04/05)

---

## Phase 3 — Documents + Workflow Engine (9 + 3 เส้น — หัวใจระบบ)

### 3.1 Seed เพิ่ม
- [ ] `workflow_sections` 5 (+04/05 inactive) · `document_statuses` 6 · `system_configs`: `workflow.avp_amount_threshold=100000`, รัศมี 1/2 กม., เกณฑ์ 60 วัน, เกณฑ์ −10 (ทั้งหมด `is_editable=false`)
- [ ] เอกสารตัวอย่าง ~10 ฉบับครบทุกสถานะ 6 ค่า + เคส >100k / ≤100k + แถว <60 วัน (เลขตรง prototype เช่น 2569/00185)

### 3.2 Transition table (`workflow/transitions.ts` — ประกาศเป็น data)
ลอกครบทุกแถวจาก `workflow.md` §ตารางเส้นทางพิจารณา — checkbox ต่อแถว:
- [ ] **06 ฝ่าย SBP DSA** · "เห็นควรไม่ชดเชย" → **เสร็จสิ้นดำเนินการ** (END · result REJECT)
- [ ] 06 · "หยุดชดเชยประกันรายได้" → **เสร็จสิ้นดำเนินการ** (END)
- [ ] 06 · "ส่งฝ่ายส่งเสริมธุรกิจ SBP" → รอ 01
- [ ] 06 · "ส่งเจ้าหน้าที่ SBP DSA" → รอ 08
- [ ] **08 เจ้าหน้าที่ SBP DSA** · "คำนวณเงินชดเชยเรียบร้อย" → รอ 01
- [ ] 08 · result "ส่งกลับ" → รอ 06 (back-flow)
- [ ] **01 ฝ่ายส่งเสริมธุรกิจ SBP** · "เห็นควรชดเชย" → รอ 02
- [ ] 01 · "เห็นควรไม่ชดเชย / ส่งกลับ" → รอ 06 (back-flow)
- [ ] **02 GM** · "เห็นควรชดเชย" + ยอด **> 100,000** → รอ 03 (AVP)
- [ ] 02 · "เห็นควรชดเชย" + ยอด **≤ 100,000** → **เสร็จสิ้นดำเนินการ** (จบที่ GM · APPROVE)
- [ ] 02 · "เห็นควรไม่ชดเชย" + ยอด **> 100,000** → รอ 03 (ไม่ชดเชยก็ต้องผ่าน AVP ตามวงเงิน)
- [ ] 02 · "เห็นควรไม่ชดเชย" + ยอด **≤ 100,000** → รอ 06 (back-flow)
- [ ] 02 · result "ส่งกลับ" → รอ 01 (back-flow)
- [ ] **03 AVP** · "เห็นควรชดเชย" → **เสร็จสิ้นดำเนินการ** (APPROVE)
- [ ] 03 · "เห็นควรไม่ชดเชย" → รอ 06 (back-flow)
- [ ] 03 · result "ส่งกลับ" → รอ 02 (back-flow)
- [ ] threshold 100,000 อ่านจาก `system_configs['workflow.avp_amount_threshold']` — **ห้าม hardcode**
- [ ] unit test transitions ครอบ**ทุก branch ข้างบน** + เคส result ไม่รู้จัก → throw

### 3.3 เลขเอกสาร (`lib/docNo.ts`)
- [ ] ออกเลข `YYYY(พ.ศ.)/xxxxx` running ต่อปีเริ่ม 00001 — จองด้วย `SELECT ... FOR UPDATE` บนตาราง counter ใน transaction
- [ ] test: ยิงขอเลขพร้อมกัน 20 ครั้ง (Promise.all) → 20 เลขไม่ซ้ำ ต่อเนื่อง

### 3.4 Endpoint เอกสาร (9 เส้น)
- [ ] `GET /tasks` — inbox: workflow_tasks เปิดของ section ที่ map กับ role ผู้เรียก · paginate
- [ ] `GET /documents` — **ไม่ส่งปี (พ.ศ.) → 400** · filter สถานะ/ร้าน/งวด · paginate
- [ ] `GET /documents/{docNo}` — เอกสารเต็ม 12 ส่วน + ธง `editableSections` / `myRoleView` ต่อ role-section ผู้เรียก · ไม่พบ → 404
- [ ] `POST /documents` — MANUAL/FS: ออกเลข (3.3) + สร้าง instance + task แรก (06) ใน transaction เดียว · **ร้าน+งวดซ้ำ → 409**
- [ ] `PUT /documents/{docNo}` — ตรวจสิทธิ์ section ผู้เรียก = current_section (403 ถ้าไม่ใช่) · **%ชดเชยรวม ≠ 100% → 400** message ตาม SRS
- [ ] `POST /documents/{docNo}/actions` — request `{result, comment}` เท่านั้น; transaction เดียว: validate → lookup transition → update status/section → ปิด task เดิม + เปิด task ใหม่ → insert consideration_logs (result_category) → enqueue อีเมล (นอก transaction)
  - [ ] ไม่ส่ง result → **400** `"ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ"` (**verbatim**)
  - [ ] result ไม่ชดเชย + ไม่มี comment → **400**
  - [ ] เอกสารสถานะ "เสร็จสิ้นดำเนินการ" ยิง action → **409**
  - [ ] ผู้เรียก section ≠ current_section_code → 403
- [ ] `GET /documents/{docNo}/timeline` — consideration_logs ทุกขั้นเรียงเวลา
- [ ] `POST /documents/{docNo}/attachments` — multer memory ≤ 5MB + ext whitelist (vsd,dwg,…,csv ตาม workflow.md) → เกิน/ผิด ext → 400 · เก็บ `storage/attachments/` + แถว document_attachments
- [ ] `GET /documents/{docNo}/sales` — ยอดขาย 4 หน้าต่าง × 15 วัน จาก sales_transactions ผ่าน impact_process_id

### 3.5 Workflow endpoints (3 เส้น)
- [ ] `POST /workflows/instances` — **service token เท่านั้น** · **Gen Flow Gate W/Y/N** ครบทุกข้อก่อนเปิด:
  1. `workflow_generation_status = W`
  2. branch type ∈ {FAM, FB1, FC1, FB2, FVB, FVC}
  3. DV ไม่ว่าง
  4. juristic ต่างกัน
  5. `growth_rate_diff ≤ −10`
  6. `sales_status ∈ {Y, N}`
  - เกณฑ์ไหนไม่ผ่าน → ตอบ reason ระบุเกณฑ์นั้น · ผ่านครบ → สร้าง instance + task 06 + ออกเลขเอกสาร + ตั้ง workflow_generation_status=Y
- [ ] `GET /workflows/instances/{id}` — สถานะ instance + tasks
- [ ] `GET /workflows/summary` — ตัวเลขเฝ้าระวัง W/Y/N + งานค้างต่อ section

### ✔ เกณฑ์ตรวจรับ Phase 3 — integration test เดินเรื่องจริง (supertest + postgres)

**Scenario 1 — เส้นทางปกติ ≤ 100,000 (จบที่ GM):**
1. login role 06 → `POST /documents` (ยอด 80,000) → 201 ได้ `docNo` รูป `2569/xxxxx` · เช็ค DB: status "รอฝ่าย SBP DSA ดำเนินการ" + task 06 เปิด
2. `POST .../actions` result "ส่งเจ้าหน้าที่ SBP DSA" → 200 · status → รอ 08 · task 06 ปิด, task 08 เปิด
3. login role 08 → actions "คำนวณเงินชดเชยเรียบร้อย" → รอ 01
4. login role 01 → `PUT /documents/{docNo}` %ชดเชยรวม 100 → 200 · actions "เห็นควรชดเชย" → รอ 02
5. login role 02 → actions "เห็นควรชดเชย" (80,000 ≤ 100k) → **สถานะ "เสร็จสิ้นดำเนินการ"** · ไม่มี task เปิดเหลือ · consideration_logs แถวสุดท้าย result_category=APPROVE

**Scenario 2 — เส้นทาง > 100,000 (ผ่าน AVP):**
1. สร้างเอกสารยอด 150,000 เดิน 06→08→01→02 เหมือน Scenario 1
2. ขั้น 02 "เห็นควรชดเชย" → status **รอ 03** (ไม่จบ) · task 03 เปิด
3. login role 03 → actions "เห็นควรชดเชย" → เสร็จสิ้นดำเนินการ

**Scenario 3 — back-flow:**
1. เอกสารอยู่ขั้น 02 · actions result "ส่งกลับ" → status รอ 01 · task 02 ปิด task 01 เปิดใหม่ · timeline มีแถวส่งกลับ

**Scenario 4 — จบทันทีที่ 06:** actions "เห็นควรไม่ชดเชย" + comment → เสร็จสิ้นดำเนินการ · result REJECT

**Error cases:**
- [ ] `GET /documents` ไม่ส่งปี → 400 · `POST /documents` ร้าน+งวดซ้ำ → 409
- [ ] actions ไม่ส่ง result → 400 message verbatim ตรงตัวอักษร
- [ ] `PUT` %รวม = 90 → 400 · เอกสารจบแล้วยิง action ซ้ำ → 409
- [ ] `POST /workflows/instances` ด้วยแถว growth_rate_diff = −5 → ไม่เปิด, คง workflow_generation_status=W + 422/reason ระบุเกณฑ์ 5
- [ ] docNo concurrent test (3.3) ผ่าน

---

## Phase 4 — Reports + Dashboard (2 + 1 เส้น)

- [ ] `GET /reports/status-summary` — **ปี (พ.ศ.) required → 400** · filter ครบ 6 ตัว:
  - `status` (6 ค่า) · `result` (**ประกันรายได้/ไม่ประกันรายได้** — จาก `consideration_logs.result_category` **ล่าสุด** APPROVE/REJECT) · `region` (13 รหัส: BE BS NEU REU RSU BG BW RC RN BN NEL REL RSL + ภาคใหม่อัตโนมัติ) · `storeType` (A/B/C/D เลือกได้หลายค่า) · `impactedStoreCode` · `newStoreCode`
  - ออกเฉพาะรายการ**มีเลขเอกสาร** · SQL ตาม `SQL_BY_PATH` ($queryRaw parameterized)
- [ ] `GET /reports/status-summary/export` — เงื่อนไขเดียวกัน → **CSV UTF-8 มี BOM** (`﻿`) · เก็บสำเนา `storage/exports/` + ส่งไฟล์กลับ (Content-Disposition)
- [ ] `GET /dashboard/summary` — ตัวเลข 4 ก้อน + chart data (SQL ตาม SQL_BY_PATH) · **cache in-memory TTL 5 นาที**

### ✔ เกณฑ์ตรวจรับ Phase 4
- [ ] `GET /reports/status-summary` ไม่ส่งปี → 400 · ส่งปี+filter → จำนวนแถวตรงกับ seed ที่คำนวณมือ (ทดสอบอย่างน้อย filter status, result, region อย่างละเคส)
- [ ] filter `result=ประกันรายได้` → ได้เฉพาะเอกสารที่ log ล่าสุด APPROVE (เอกสาร back-flow แล้ว REJECT ทีหลังต้องไม่ติดมา)
- [ ] export → header `text/csv` · ไบต์แรก = EF BB BF (BOM) · เปิด Excel ภาษาไทยไม่เพี้ยน · มีไฟล์สำเนาใน `storage/exports/`
- [ ] `GET /dashboard/summary` ยิง 2 ครั้งใน 5 นาที → query log ครั้งเดียว (ดู pino) · ครั้งที่ 3 หลัง TTL → query ใหม่

---

## Phase 5 — Config + Email Templates + Notification (5 + 5 เส้น)

### 5.1 System Config (5 เส้น)
- [ ] `GET /configs` (filter category) · `GET /configs/{key}` (cache 5 นาที)
- [ ] `POST /configs` — validate ค่าตาม `value_type` (NUMBER/STRING/BOOLEAN/JSON/CRON) ก่อนบันทึก → ผิด type → 400
- [ ] `PUT /configs/{key}` — `is_editable=false` → **403** · **key หน้าตาเป็น secret (มี password/secret/token/key คู่ credential) → 400 ปฏิเสธ** · reason → audit · แก้แล้ว **invalidate cache** ทันที
- [ ] `DELETE /configs/{key}` — is_editable=false → 403 · reason → audit

### 5.2 Email Templates (5 เส้น)
- [ ] seed `email_templates` EM-01–08 + `status_email_rules` (TO/CC ต่อสถานะตาม SRS 3.1.5)
- [ ] `GET /email-templates` · `GET /email-templates/{code}` — subject/body + ตัวแปร merge
- [ ] `PUT /email-templates/{code}` — แก้ subject/body เท่านั้น (From/To/Cc ล็อกตาม status_email_rules) · reason → audit
- [ ] `POST /email-templates/{code}/reset` · `POST /email-templates/reset-all` — คืน default · audit

### 5.3 Notification Service
- [ ] `notification/` — nodemailer (SMTP UTF-8) + render ตัวแปร merge จาก template + **คิว in-memory + retry 3 ครั้ง** (ส่งเมลอยู่นอก transaction เสมอ)
- [ ] hook เข้ากับ Workflow Engine: เปลี่ยนสถานะ → **EM-01** · เสร็จสิ้น → **EM-02** · ส่งกลับ (back-flow) → **EM-03** — TO/CC จาก status_email_rules
- [ ] cron **EM-04** เตือนงานค้างรายสัปดาห์ จันทร์ 10:00 (อ่าน workflow_tasks เปิด · รอบเวลาแก้ได้ใน config)
- [ ] cron **EM-05** escalation งานค้าง 30/45/60 วัน (waiting_days ของ workflow_tasks → แจ้งหัวหน้า section)

### ✔ เกณฑ์ตรวจรับ Phase 5 (mailpit/mailhog)
- [ ] `docker run mailpit` → เดิน Scenario 1 ของ Phase 3 ใหม่ → กล่อง mailpit มี EM-01 ทุกครั้งที่เปลี่ยนสถานะ · EM-02 ตอนจบ · ผู้รับ TO/CC ตรง status_email_rules · ตัวแปร (docNo, ร้าน, สถานะ) ถูกแทนครบไม่มี `{{...}}` หลงเหลือ
- [ ] back-flow (Scenario 3) → EM-03 ออก
- [ ] `PUT /configs/workflow.avp_amount_threshold` → 403 · `PUT /configs/x` value_type=NUMBER ส่ง "abc" → 400 · `POST /configs` key `smtp.password` → 400
- [ ] แก้ config editable แล้ว `GET /configs/{key}` ทันที → ได้ค่าใหม่ (cache invalidated)
- [ ] ดับ SMTP ชั่วคราวแล้วเดิน workflow → เมล retry 3 ครั้ง (ดู log) · workflow ไม่ fail

---

## Phase 6 — Batch Jobs + Interfaces (6 + 4 เส้น)

> **Jobs 7/8/9 ตัดทิ้ง** — ไฟล์ BPM06001O_/2O_/3O_ ผ่าน EAI ไม่มีในระบบใหม่ (แทนด้วย Document Service เขียน DB ตรง + Job 8b เรียก workflow ภายใน) — **ไม่ต้องสร้าง** แต่ให้คง job_no ไว้ในเอกสาร/seed เป็นแถว `enabled=false` + หมายเหตุ "removed — replaced by direct DB write" เพื่อ traceability

### 6.1 Runner กลาง
- [ ] seed `job_configs` 11 แถว (cron ตามเอกสาร Batch v4.0) · `batch/runner.ts` — lock กันรันซ้อน (แถว RUNNING ใน job_run_histories) → รันซ้อน **409** · ทุก run บันทึก job_run_histories (เวลา/แถว/ไฟล์/ผล) · จบ Error → **EM-07**
- [ ] `batch/scheduler.ts` — node-cron อ่าน cron จาก job_configs · `POST /jobs/{jobNo}/run` ใช้ runner ตัวเดียวกับ cron

### 6.2 Job Admin API (6 เส้น)
- [ ] `GET /jobs` — 11 entry points + สถานะล่าสุด
- [ ] `GET /jobs/{jobNo}` — รายละเอียด + พารามิเตอร์
- [ ] `PUT /jobs/{jobNo}/params` — แก้เฉพาะพารามิเตอร์ editable → แก้ตัว non-editable → 400
- [ ] `PUT /jobs/{jobNo}/enabled` — เปิด/ปิด
- [ ] `POST /jobs/{jobNo}/run` — สั่งรันนอกรอบ (guard 6.1)
- [ ] `GET /jobs/{jobNo}/runs` — ประวัติรัน paginate

### 6.3 File codec
- [ ] `interfaces/fileCodec.ts` — fixed-width + iconv-lite (WINDOWS-874/TIS-620/UTF-8) + **golden-file tests**: วันที่ พ.ศ. · ชื่อประกอบ first+last · เลขศูนย์นำหน้า store_code ไม่หาย

### 6.4 Jobs รายตัว (checkbox ต่อ job — input / output / เกณฑ์ผ่าน)
- [ ] **Job 1 — นำเข้า QSSI** · Input: SFTP QSSI 4 ไฟล์ `mrs*` (รายเดือน) · Output: แถว `fcs_qssi_scores` (UK กัน dup) · เกณฑ์ผ่าน: dedup ทำงาน (รันซ้ำไฟล์เดิมแถวไม่เพิ่ม) · งวดใน DB = **เดือนก่อนหน้า** (off-by-one ตั้งใจ) · ครบ 6 หมวด (8,9,12,1,10,16)
- [ ] **Job 2 — นำเข้าคู่ร้านกระทบ** · Input: ALLMAP SQL Server (**read-only** · mssql) ทุกวันที่ 7 07:00 · Output: `fgi_impact_stores` (กฎ DENY/ON_PROCESS → W/N/P) · เกณฑ์ผ่าน: mapping สถานะถูกตาม fixture
- [ ] **Job 3 — นำเข้าคู่แข่ง** · Input: ALLMAP read-only · Output: `fgi_impact_competitors` (`data_source=ALM` · งวดล่าสุดต่อร้าน) · เกณฑ์ผ่าน: แถวซ้ำงวดเดิมถูกแทนที่ไม่งอก
- [ ] **Job 4 — export ยอดขายไป MIS** (**P0**) · Input: fgi_impact_stores เข้าเกณฑ์ (อายุร้าน 12 เดือน 15 วัน / +16 วัน) วันที่ 7–16 16:00 · Output: ไฟล์ `AMS06001O_` + สถานะ W→P · เกณฑ์ผ่าน: **ครอบ transaction/outbox — ห้าม commit W→P ก่อนเขียนไฟล์สำเร็จ** · จำลอง fail กลางทาง (mock fs โยน error) → rollback สถานะไม่ค้าง P
- [ ] **Job 5 — import ยอดขายจาก MIS** · Input: ไฟล์ `AMS06001I_` 16:30 · Output: `sales_transactions` + คำนวณ sales_diff 4×15 วัน (outlier ≥ 50) → verify_status Y/N · เกณฑ์ผ่าน: **growth_rate_diff = NULL → ตั้ง "รอตรวจสอบ" ไม่ auto-accept** (flag config รอ business sign-off) · ตัวเลขคำนวณตรง fixture
- [ ] **Job 6 — export FRBC0001 ไป STA** · Input: compensation_histories (submit_account_month) ทุกวัน 17:00 · เช็ค QSSI ครบ 6 หมวดก่อนส่ง · Output: ไฟล์ `FRBC0001_` (windows-874 · วันที่ พ.ศ.) SFTP ไป STA + interface_transactions (sta_status I/C/A/N/S/Z) · เกณฑ์ผ่าน: golden file byte-ตรง · **purge tracking ทำงานจริง (แก้บั๊ก E20)**
- [ ] **Job 8b (แทน) — เปิด workflow** · Input: fgi_impact_stores ที่ workflow_generation_status=W · Output: เรียก `POST /workflows/instances` ภายใน (service token) ต่อแถว + **EM-06** สรุปราย DV · เกณฑ์ผ่าน: แถวผ่าน Gate → status Y + เอกสาร+instance เกิด · branch type นอกเซ็ต → N · ข้อมูลยังไม่พร้อม → คง W + reason ใน log · **ไม่มี K2 REST อีกแล้ว**
- [ ] **Job 10 — watchdog ACK จาก STA** · Input: interface_transactions ที่ ACK ค้าง ≥ 1 วัน (ตรวจ 07:00) · Output: **EM-08** · เกณฑ์ผ่าน: fixture แถวค้าง 2 วัน → เมลออก · แถวค้าง 0 วัน → เงียบ

### 6.5 Interface endpoints (4 เส้น)
- [ ] `GET /interfaces/tracking` — สถานะรับ–ส่งไฟล์ (filter data_name/ช่วงวัน · paginate)
- [ ] `GET /interfaces/pending-ack` — รายการ ACK ค้าง ≥ 1 วัน (ฐานเดียวกับ Job 10)
- [ ] `POST /interfaces/sta/ack` — callback STA · auth ด้วย header `X-Api-Key` — **key ผิด/ไม่ส่ง → 401** · อัปเดต sta_status
- [ ] `GET /dashboard/summary` — (ทำแล้ว Phase 4 — เช็คว่า route อยู่ครบในกลุ่ม 10)

### ✔ เกณฑ์ตรวจรับ Phase 6
- [ ] `POST /jobs/{n}/run` ทุก job (1,2,3,4,5,6,8b,10) รันสำเร็จบน fixture (SFTP/ALLMAP mock) · job_run_histories มีแถวผลถูกต้อง
- [ ] ยิง `POST /jobs/1/run` ซ้อนขณะ RUNNING → **409**
- [ ] Job 4 fail กลางทาง → สถานะใน DB ไม่ค้าง P (rollback) · รันใหม่ได้
- [ ] golden-file tests ผ่านทุกไฟล์ (AMS06001O, FRBC0001) — เทียบ byte รวม encoding
- [ ] `POST /interfaces/sta/ack` key ถูก → 200 + sta_status เปลี่ยน · key ผิด → 401
- [ ] job จงใจ throw → EM-07 ออกใน mailpit

---

## Phase 7 — Hardening & Delivery

- [ ] script เทียบ route table กับ `api.md` — รายงาน **"62/62 matched"** path/method ตรงทุกตัว (+ ยืนยัน abnormal-stores 2 เส้น**ไม่มี** route)
- [ ] `openapi.yaml` ครบ 62 เส้น + ตัวอย่าง request/response ตรง plan-api.html
- [ ] security: rate limit login (มีแล้ว P1 — ทวน) · pino redact token/รหัสผ่าน/Authorization header · สแกนยืนยัน**ไม่มี secret ใน DB** (`SELECT * FROM system_configs WHERE config_key ~* 'password|secret|token'` → 0 แถว) และไม่มีใน log
- [ ] index DB จุด query หนัก: `compensation_documents(status_code, current_section_code)` · `(impact_process_id)` · `compensation_histories(submit_account_month)` · `workflow_tasks(section_code, status)`
- [ ] graceful shutdown: SIGTERM/SIGINT → หยุดรับ request → รอ job ที่กำลังรัน → `prisma.$disconnect()` · `GET /readyz` เช็ค DB
- [ ] `prisma/seed.ts` เต็มรูปตาม plan-be.md §6 — **idempotent (upsert)** รันซ้ำได้
- [ ] Dockerfile multi-stage (node:20-alpine) + docker-compose (postgres + api + mailpit) + README (วิธีรัน dev · ตาราง env · แผนผังโมดูล)
- [ ] vitest ทั้งหมด green · coverage โมดูล `workflow/` ≥ **90%**

### ✔ เกณฑ์ตรวจรับ Phase 7
- [ ] `docker compose up -d && npx prisma migrate deploy && npx prisma db seed` → `curl /readyz` 200 → FE (checklist-fe) ใช้งานครบทุกหน้า end-to-end
- [ ] script เทียบ api.md พิมพ์ "62/62 matched"
- [ ] `kill -TERM <pid>` ระหว่างมี request ค้าง → request จบก่อน process ออก · ระหว่าง job รัน → job จบก่อน
- [ ] รัน seed 2 รอบ → จำนวนแถวเท่าเดิม (idempotent)
- [ ] `npx vitest run --coverage` → workflow ≥ 90%

---

## ภาคผนวก A — Traceability: 62 endpoint ↔ ตาราง DB ↔ Phase

| # | Method | Path | ตารางหลัก (R/W) | Phase |
|---|---|---|---|---|
| 1 | POST | /auth/login | user_accounts, employees, roles (R) | 1 |
| 2 | POST | /auth/refresh | — (JWT) | 1 |
| 3 | GET | /auth/me | user_accounts, employees, roles (R) | 1 |
| 4 | GET | /me/menus | menu_permissions, menus (R) | 1 |
| 5 | GET | /tasks | workflow_tasks, compensation_documents (R) | 3 |
| 6 | GET | /documents | compensation_documents (R) | 3 |
| 7 | GET | /documents/{docNo} | compensation_documents + ลูกทั้งชุด (R) | 3 |
| 8 | POST | /documents | compensation_documents, document_new_stores, workflow_instances, workflow_tasks, doc_no_counters (W) | 3 |
| 9 | PUT | /documents/{docNo} | document_new_stores, document_competitors, document_external_factors (W) | 3 |
| 10 | POST | /documents/{docNo}/actions | compensation_documents, workflow_tasks, consideration_logs (W) | 3 |
| 11 | GET | /documents/{docNo}/timeline | consideration_logs (R) | 3 |
| 12 | POST | /documents/{docNo}/attachments | document_attachments (W) | 3 |
| 13 | GET | /documents/{docNo}/sales | sales_transactions, fgi_impact_sales_summaries (R) | 3 |
| 14 | GET | /stores/search | stores / impacted_stores (R) | 2 |
| 15 | GET | /competitors | competitors (R) | 2 |
| 16 | GET | /document-statuses | document_statuses (R) | 2 |
| 17 | GET | /workflow-sections | workflow_sections (R) | 2 |
| 18 | GET | /operators | operator_assignments, employees (R) | 2 |
| 19 | POST | /operators | operator_assignments (W) | 2 |
| 20 | PUT | /operators/{id} | operator_assignments, audit_logs (W) | 2 |
| 21 | DELETE | /operators/{id} | operator_assignments, audit_logs (W) | 2 |
| 22 | GET | /employees/search | employees (R) | 2 |
| 23 | GET | /factors | external_factors (R) | 2 |
| 24 | POST | /factors | external_factors (W) | 2 |
| 25 | PUT | /factors/{code} | external_factors, audit_logs (W) | 2 |
| 26 | DELETE | /factors/{code} | external_factors, audit_logs (W) | 2 |
| 27 | GET | /menu-permissions | menu_permissions, menus, roles (R) | 2 |
| 28 | PUT | /menu-permissions/{menuCode} | menu_permissions, audit_logs (W) | 2 |
| 29 | GET | /roles | roles (R) | 2 |
| 30 | POST | /roles | roles, menu_permissions (W) | 2 |
| 31 | PUT | /roles/{roleCode} | roles, audit_logs (W) | 2 |
| 32 | DELETE | /roles/{roleCode} | roles, menu_permissions (cascade), audit_logs (W) | 2 |
| 33 | POST | /menus | menus, menu_permissions (W) | 2 |
| 34 | PUT | /menus/{menuCode} | menus, audit_logs (W) | 2 |
| 35 | DELETE | /menus/{menuCode} | menus, menu_permissions (cascade), audit_logs (W) | 2 |
| 36 | GET | /audit-logs | audit_logs (R) | 2 |
| 37 | GET | /configs | system_configs (R) | 5 |
| 38 | GET | /configs/{key} | system_configs (R · cache 5 นาที) | 5 |
| 39 | POST | /configs | system_configs, audit_logs (W) | 5 |
| 40 | PUT | /configs/{key} | system_configs, audit_logs (W) | 5 |
| 41 | DELETE | /configs/{key} | system_configs, audit_logs (W) | 5 |
| 42 | GET | /email-templates | email_templates (R) | 5 |
| 43 | GET | /email-templates/{code} | email_templates, status_email_rules (R) | 5 |
| 44 | PUT | /email-templates/{code} | email_templates, audit_logs (W) | 5 |
| 45 | POST | /email-templates/{code}/reset | email_templates, audit_logs (W) | 5 |
| 46 | POST | /email-templates/reset-all | email_templates, audit_logs (W) | 5 |
| 47 | GET | /reports/status-summary | compensation_documents, consideration_logs, document_new_stores (R) | 4 |
| 48 | GET | /reports/status-summary/export | เดียวกับ 47 (R) + ไฟล์ storage/exports | 4 |
| 49 | GET | /jobs | job_configs, job_run_histories (R) | 6 |
| 50 | GET | /jobs/{jobNo} | job_configs (R) | 6 |
| 51 | PUT | /jobs/{jobNo}/params | job_configs, audit_logs (W) | 6 |
| 52 | PUT | /jobs/{jobNo}/enabled | job_configs, audit_logs (W) | 6 |
| 53 | POST | /jobs/{jobNo}/run | job_run_histories (W) + ตารางตาม job | 6 |
| 54 | GET | /jobs/{jobNo}/runs | job_run_histories (R) | 6 |
| 55 | POST | /workflows/instances | fgi_impact_stores, compensation_documents, workflow_instances, workflow_tasks (W) | 3 |
| 56 | GET | /workflows/instances/{id} | workflow_instances, workflow_tasks (R) | 3 |
| 57 | GET | /workflows/summary | fgi_impact_stores, workflow_tasks (R) | 3 |
| 58 | GET | /interfaces/tracking | interface_transactions (R) | 6 |
| 59 | GET | /interfaces/pending-ack | interface_transactions (R) | 6 |
| 60 | POST | /interfaces/sta/ack | interface_transactions (W) | 6 |
| 61 | GET | /dashboard/summary | หลายตาราง aggregate (R · cache 5 นาที) | 4 |

> **Skip (comment รอตัดสินใจ):** `GET /abnormal-stores` · `POST /abnormal-stores/assign` — ไม่ implement ใน scope นี้

## ภาคผนวก B — Environment Variables (validate ด้วย zod ที่ `config/env.ts`)

| ตัวแปร | ใช้ทำอะไร | ตัวอย่าง / ข้อกำหนด |
|---|---|---|
| `NODE_ENV` | โหมดรัน | development / production |
| `PORT` | พอร์ต API | 3000 |
| `DATABASE_URL` | PostgreSQL 16 | postgresql://... |
| `JWT_SECRET` | sign JWT | **ความยาว ≥ 32 ตัวอักษร** |
| `JWT_ACCESS_TTL` / `JWT_REFRESH_TTL` | อายุ token | 30m / 8h |
| `SERVICE_TOKEN` | เรียก `POST /workflows/instances` (Job 8b) | ≥ 32 ตัว |
| `API_KEY_STA` | header X-Api-Key ของ `/interfaces/sta/ack` | ≥ 32 ตัว |
| `CORS_ORIGINS` | whitelist origin FE | comma-separated |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | Notification Service | dev = mailpit:1025 |
| `SFTP_QSSI_HOST` / `SFTP_QSSI_USER` / `SFTP_QSSI_KEY` | Job 1 | key-based · known_hosts บังคับ |
| `SFTP_STA_HOST` / `SFTP_STA_USER` / `SFTP_STA_KEY` | Job 6 ส่ง FRBC0001 | เดียวกัน |
| `ALLMAP_MSSQL_URL` | Jobs 2–3 (read-only) | mssql://... |
| `MIS_IN_DIR` / `MIS_OUT_DIR` | ไฟล์ AMS06001I/O (Jobs 4–5) | path volume |
| `STORAGE_DIR` | attachments + exports | ./storage |
| `LOG_LEVEL` | pino | info |

> **prod:** ทุก secret มาจาก Secret Manager — ห้ามอยู่ใน repo/DB/log · pino redact `SMTP_PASS`, `Authorization`, password ทุกจุด

## ภาคผนวก C — อ้างอิงเร็ว: สถานะ 6 ค่า และ Email Templates

**สถานะเอกสาร 6 ค่า** (seed `document_statuses` — เรียงตาม flow):

| # | สถานะ | Section คู่ |
|---|---|---|
| 1 | รอฝ่าย SBP DSA ดำเนินการ | 06 |
| 2 | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | 08 |
| 3 | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | 01 |
| 4 | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | 02 |
| 5 | รอผู้บริหารสำนักบริหาร SBP ดำเนินการ | 03 |
| 6 | เสร็จสิ้นดำเนินการ | — (END) |

**Email templates EM-01–08** (seed `email_templates` · ผู้รับตาม `status_email_rules`):

| Code | จังหวะส่ง | Phase ที่ hook |
|---|---|---|
| EM-01 | เปลี่ยนสถานะเอกสาร (ทุก transition) | 5 |
| EM-02 | เอกสารเสร็จสิ้นดำเนินการ | 5 |
| EM-03 | ส่งกลับ (back-flow) | 5 |
| EM-04 | เตือนงานค้างรายสัปดาห์ (จันทร์ 10:00) | 5 |
| EM-05 | escalation งานค้าง 30/45/60 วัน | 5 |
| EM-06 | สรุปเปิด workflow ราย DV (Job 8b) | 6 |
| EM-07 | batch job จบด้วย Error | 6 |
| EM-08 | watchdog ACK จาก STA ค้าง ≥ 1 วัน (Job 10) | 6 |

**Definition of Done รวม:** ติ๊กครบทุกข้อ + เกณฑ์ตรวจรับทุก Phase ผ่าน + script traceability รายงาน 62/62 + FE end-to-end ใช้งานได้ผ่าน docker compose
