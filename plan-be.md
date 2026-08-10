# plan-be.md — Spec สร้าง Backend ระบบ SBPGI (Node.js) ฉบับละเอียด

> ## ⚠️ ตัดสินใจ 2026-08-06 — ยึดตาราง/บริการของระบบ SBP เดิม
>
> spec นี้เขียนไว้ตอนโครงยังเป็น 34 ตาราง **ตอนนี้เหลือ 21 ตาราง / 30 endpoint 6 กลุ่ม** (Lookup 3 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3 — ลบกลุ่ม System Config + Email Template 10 เส้น พร้อมหน้าจอ และกลุ่ม Batch Job Admin 6 เส้น + ตาราง `job_configs`/`job_run_histories` เมื่อตัด 2 tab ควบคุมของหน้า Batch Job · 2026-08-06 · แล้วตัด `audit_logs` + `GET /audit-logs` 2026-08-07) · ส่วนที่บอกให้สร้างของด้านล่างนี้ **ให้ใช้ของระบบ SBP ปัจจุบันแทน**:
> `workflow_instances`/`workflow_tasks`/`workflow_sections`/`document_statuses` → **`@srm/glb-workflow`** (**13 ตาราง · schema `sps_store`** · ชื่อ function `initializeWorkflow`/`addPreparedApprover`/`triggerEvent`/`getPendingFlow` **ยังไม่ยืนยัน — เอกสาร 3 ชุดขัดกัน** ดู §Alignment · `referenceId = doc_no` **ยังไม่ตัดสิน** DP-1) ·
> `stores`→`store`/`mas_store` · `zones`→`mas_zone` · `branch_types`→`common_code` · `employees`→`business_user` ·
> `email_templates`→`email_template` + `@gosoft-sbp/email-lib` · `system_configs`→`mas_param` ·
> วงเงินอนุมัติ → `common_code` (`SBPGI_APPROVE_LIMIT` · **GM 50,000 / AVP 300,000** ตาม SDD GI)
> · envelope ต้องเป็น `{success, data}` / `{success:false, data:null, error:{code,message}}` ตาม store-backend
> · รายละเอียด: `database.md` §ตารางที่ตัดออกรอบ 2 · `api.md` §เส้นที่เปลี่ยนไปใช้ของระบบ SBP เดิม


> **spec สำหรับ AI/นักพัฒนา สร้าง Backend จริงโดยไม่ต้องถามเพิ่ม** อ่านคู่กับ: `checklist-be.md` (ลำดับงาน + เกณฑ์ตรวจรับต่อ Phase) · `api.md` + `plan-api.html` (สัญญา API **30 เส้น 6 กลุ่ม** — **สัญญาผูกมัด** รวม SQL ตัวอย่างต่อเส้นใน `SQL_BY_PATH`) · `database.md` (schema **21 ตาราง**) · `workflow.md` (flow 12 ขั้น + ตาราง transition) · **SDD GI 24/02/2026** (`SDD-GI-Compensation/SDD-ปรับปรุงการชดเชยรายได้-SBP-GI.md` — วงเงิน GM/AVP ใหม่ · เปิดเรื่องซ้ำ · งานค้าง) · เอกสารวิเคราะห์ระบบเดิม `SBP/srm-sps-spsap-store-backend.md` + `SBP/srm-sps-spsap-sbp-bff.md` · `plan-fe.md`
>
> หลักการใหญ่: **รวม EAI + K2 เข้า SBPGI** — Document Service เขียน DB ตรง + Workflow Engine ภายใน (ไม่มีไฟล์ `BPM06001O_/2O_/3O_` และไม่มี K2 REST StartInstance) · interface ภายนอก (QSSI/ALLMAP/IAS/STA/SMTP) คงกลไกไฟล์/SFTP เดิม
>
> **กติกาเหล็ก (ห้ามเปลี่ยน):**
> - workflow **5 ขั้น 06→08→01→02→03** (ตัดขั้นบัญชี 04/05 ตาม SDD v7.5) · สถานะเอกสาร **6 ค่า** (เปลี่ยนคำเรียก "ฝ่ายส่งเสริม" → **"หน่วยงานส่งเสริมธุรกิจ"** ทุกจุดตาม SDD GI — ทั้งค่า enum **"ส่งหน่วยงานส่งเสริมธุรกิจ SBP"** และชื่อสถานะ **"รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ"** · ตัดสินใจ 2026-08-06)
> - กฎวงเงิน (SDD GI 24/02/2026 — แทนเกณฑ์เดียว 100,000 เดิม): เห็นควรชดเชย **≤ 50,000 จบที่ GM (02)** · **50,001–300,000 → AVP (03) แล้วจบ** · **เกิน 300,000 ยังไม่กำหนดเส้นทาง (รอ confirm)**
> - เห็นควรไม่ชดเชยที่ขั้น **01/02 → เสร็จสิ้นทันที** (ไม่ตีกลับเป็นทอด ๆ · SDD GI) · ขั้น 03 คงเดิม (รอ confirm)
> - Error ทุกเส้นรูปเดียว `{code,message}` — ข้อความไทย **verbatim ตาม SRS**
> - เลขเอกสาร `พ.ศ./xxxxx` running ต่อปี จองด้วย `SELECT ... FOR UPDATE`
> - Gen Flow Gate **6 เกณฑ์** ครบทุกข้อ · Job 4 ครอบ transaction/outbox (**P0**)
> - **ห้ามเก็บ secret ใน DB/`mas_param`** — credential อยู่ `.env` (prod = Secret Manager)
> - **Auth/RBAC/ผู้ปฏิบัติงาน ไม่ทำใน SBPGI** (ตัดสินใจ 2026-08-05) — ใช้ระบบ SBP เดิม (Cognito + BFF + auth-backend) · SBPGI รับ user context จาก header เท่านั้น
> - กลุ่ม abnormal-stores **ยกเลิกและลบทิ้งถาวร 2026-08-06** พร้อมหน้าจอ — ไม่มี route นี้
> - **ยึดของระบบ SBP เดิมก่อนเสมอ (2026-08-06):** workflow = `@srm/glb-workflow` · ร้าน/ภาค/lookup = `/store/*` + `/common/common-code` · อีเมล = `email_template` + `@gosoft-sbp/email-lib` · config = `mas_param` · ไฟล์ = service S3 เดิม

---

## Alignment กับระบบ SBP เดิม (สรุปจาก SBP/srm-sps-spsap-store-backend.md + -sbp-bff.md)

SBPGI ไม่ใช่ระบบโดดเดี่ยว — จะเสียบเข้าสถาปัตยกรรม SBP ปัจจุบัน (FE → BFF → backend ต่อโดเมน) สรุปข้อเท็จจริงของระบบเดิมที่ spec นี้ต้อง align ด้วย:

- **Stack backend เดิม**: **NestJS 11 + TypeORM 0.3 + PostgreSQL** (AWS RDS · 1 database แบ่ง **schema ต่อโดเมน** เช่น `sps_store`) + **read-replica routing** เขียนเอง (SELECT/WITH สุ่มไป slave pool, write ไป master, fallback master เมื่อ slave fail) · Node 20 alpine · deploy ECS ผ่าน Bitbucket pipeline template กลาง + Dynatrace
- **Workflow engine ภายในมีอยู่แล้ว**: **`@srm/glb-workflow`** (private CodeArtifact · state machine) — **definition ของ flow (states/routes/events) เก็บใน DB 13 ตาราง บน schema `sps_store`** (ยืนยันจาก `SBP/db-schema-sps_store.md` 2026-08-10): `workflow` · `workflow_version` · `workflow_state` · `workflow_status` · `workflow_event` · `workflow_route` · `workflow_group` · `workflow_group_map` · `workflow_transaction` · `workflow_history` · `workflow_approver` · `workflow_part` · `workflow_part_display` · ใช้งานจริงเต็มรูปแบบกับหนังสือขอความร่วมมือ (versionId 6) · inbox รวมที่ `/api/workflow/pending`
  - **schema ต้องระบุให้ชัดเสมอว่า `sps_store`** — `sps_auth` มีตารางชื่อเดียวกันครบ 13 ตัวแต่เป็นชุดของ auth-backend คนละชุดและคนละเวอร์ชัน (`workflow_state` 3 คอลัมน์ vs 4 คอลัมน์) · ปริมาณจริงฝั่ง `sps_store`: `workflow_transaction` 19,283 · `workflow_history` 38,010 · `workflow_approver` 96,542 · ฝั่ง `sps_auth`: transaction 55 · route 41 · state 10
  - ⚠️ **ความเสี่ยงที่ต้องคุยกับทีมเจ้าของ library:** `sps_store.workflow_transaction` **ไม่มี PK และไม่มี index ใด ๆ** ทั้งที่มี 19,283 แถว (ตัวเดียวกันใน `sps_auth` มี PK) → seq-scan ทุก action และไม่มีอะไรกัน initialize ซ้ำระดับ DB · **ยังไม่ตัดสิน** ว่าจะขอ sign-off เพิ่ม index หรือกันซ้ำฝั่ง SBPGI — ดู **DP-2** ใน `SBP/SBPGI-vs-existing-system.md`
  - ⚠️ **ชื่อ use case / function ยังไม่ยืนยัน — เอกสาร 3 ชุดขัดกัน ห้ามเลือกเอง:** ชุด A `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` (ชีต Detail) = `eventWorkflow` / `addPreApprover` / `getPendingFlowByUser` · ชุด B ชีต Mermaid seq ของไฟล์เดียวกัน = `triggerEvent` · ชุด C `SBP/srm-sps-spsap-store-backend.md` §1.5 = `TriggerEventUseCase` / `AddPreparedApproverUseCase` / `GetPendingFlowUseCase` (+ `GetPermissionUseCase`) — ชื่อทุกจุดในไฟล์นี้เป็น **placeholder** ต้อง confirm กับทีมเจ้าของ `@srm/glb-workflow` ก่อน implement
  - **`workflow_part` / `workflow_part_display`** คุม READ/WRITE รายส่วนของหน้าจอต่อ state — ทับซ้อนกับกลไก `data-editrole`/`.edit-only` ที่ prototype ทำเอง · **เป็นข้อค้างตัดสินใจ ยังไม่เปลี่ยนดีไซน์** (ดู `SBP/SBPGI-vs-existing-system.md`)
- **BFF (NestJS)**: ผู้ใช้ login ผ่าน **AWS Cognito** (OIDC · token เก็บใน httpOnly cookie ฝั่ง BFF) · BFF proxy ไป backend ภายในด้วย **`x-api-key`** ต่อ backend + **user-context headers** (`x-user-id` / `x-user-group-id` / `x-user-full-name` / `x-user-permissions`) — backend เดิม**ไม่ทำ authentication เอง**
- **Infra ที่ backend เดิมใช้**: **RabbitMQ** (publish event topic exchange) + **S3** (เก็บไฟล์) + **SMTP** (nodemailer/email-lib · template ในตาราง `email_template` + log `email_sent`)

**ข้อสรุปข้อ (ก) Stack (ตัดสินใจ 2026-08-05): ยึดตามงานเดิม — ใช้ NestJS + TypeORM + PostgreSQL ตาม convention ของ store-backend** (spec ฉบับก่อนหน้าเขียนเป็น Express + Prisma — แก้เป็น NestJS ทั้งไฟล์แล้ว):
- **NestJS modules/controllers/services** ต่อโดเมน · **TypeORM entities** บน **schema แยกของ SBPGI** (เช่น `sps_sbpgi`) ใน PostgreSQL RDS เดียวกัน — แนว schema-per-domain ของระบบเดิม
- **repository provider pattern** ตามระบบเดิม (`{provide: '<TOKEN>_REPOSITORY', useFactory: (ds) => ds.getRepository(Entity), inject: ['DATA_SOURCE']}`)
- **guards / interceptors / filters** ตามแบบระบบเดิม: ApiKey/UserContext guard · `HttpContext` (AsyncLocalStorage + request id) · exception filters กลาง — โดย **shape ของ response/error ยังต้องตรงสัญญา `api.md`** (`{page,size,total,items}` · error `{code,message}`) — ถ้าจะห่อ `{success,data}` ตาม `ResponseInterceptor` ของระบบเดิม ต้องอัปเดต `api.md`/`plan-api.html` คู่กันก่อน (ประเด็นเปิดเล็ก แจ้งทีม FE)
- รองรับ **read-replica routing** แบบระบบเดิม (SELECT → slave pool, write → master) ถ้าจำเป็น · **Dockerfile/CI ตามแนว bitbucket-pipelines template กลาง `srm-sps-spsap-pipeline-template`**
- ชื่อ service เสนอ (ไม่ผูกมัด): **`srm-sps-spsap-sbpgi-backend`**

> ✅ **ประเด็นตัดสินใจข้อ (ข) — Workflow Engine: เคาะแล้ว 2026-08-06 → ใช้ `@srm/glb-workflow` ของระบบเดิม (ทางเลือก 2)**
> เพิ่ม **workflow version ใหม่ 1 ตัว** ของประกันรายได้ (state = 5 ขั้น 06/08/01/02/03 · route = การส่งต่อ/ตีกลับ · status = 6 ค่า) แล้วเรียก `initializeWorkflow({versionId, referenceId, userId})` → `addPreparedApprover()` → `triggerEvent()` · inbox ใช้ `getPendingFlow()` (มี endpoint รวมทุกระบบอยู่แล้วที่ `GET /api/workflow/pending`) — **ชื่อ function ทั้ง 4 ตัวนี้ยังไม่ยืนยัน (เอกสาร 3 ชุดขัดกัน ดู §Alignment) และค่า `referenceId` ยังไม่ตัดสิน (DP-1 — ระบบเดิมส่ง surrogate id จริงทั้ง cooperation-request และ inform-evaluate)**
> **ผลที่ตามมา (แก้ในเอกสารแล้ว):** ตาราง `workflow_instances`/`workflow_tasks`/`workflow_sections`/`document_statuses` **ถูกตัดออกจาก schema** (34 → 24 → 22 → 21 ตาราง) · `database.md`/`plan-database.html` และ `api.md`/`plan-api.html` อัปเดตตรงกันแล้ว
> **§6–7 (engine ตัวอย่างที่เขียนเอง) คงไว้เป็น reference design เท่านั้น — ห้าม implement ตามนั้น**

## 0. สัญญากลาง BE/API Common Contracts

> LLDD อ้างอิง: `LLDD/BE/LLDD-BE-API-Common-Contracts.md` + `LLDD/FE/LLDD-FE-Integration-Contracts.md` · ทุก route/controller/service ต้องยึดสัญญานี้ก่อนอ่านรายละเอียด endpoint รายตัวใน `api.md`/`plan-api.html`

| หมวด | Contract ที่ BE ต้อง enforce |
|---|---|
| Transport | Base URL `/api/v1`; JSON `application/json; charset=utf-8`; multipart เฉพาะ attachments; logging ต้องมี request id (`X-Request-Id` ถ้าส่งมา ไม่ส่งให้ generate) |
| Auth | **SBPGI ไม่ทำ JWT login เอง (ตัดสินใจ 2026-08-05)** — user endpoint ทุกเส้นตรวจ `x-api-key` จาก BFF ระบบเดิม + อ่าน user context จาก header `x-user-id`/`x-user-group-id`/`x-user-permissions` (แบบเดียวกับ backend อื่นของ SBP); `POST /workflows/instances` ใช้ service token; `POST /interfaces/sta/ack` ใช้ API key แยกของ STA |
| Error | error handler คืน `{code,message}` เท่านั้น; ห้าม endpoint คืน shape อื่น; SRS popup text ต้องอยู่ใน `lib/messages.ts` เพื่อเทียบ verbatim จุดเดียว |
| HTTP status | 400 validation · 401 auth · 403 forbidden/RBAC · 404 not found · 409 duplicate/current-task/job-running conflict · 422 business rule · 413 file too large · 415 unsupported file |
| Pagination | GET list ทุกเส้นใช้ `page,size` และคืน `{page,size,total,items}`; default size 20, max 100 |
| Format | `docNo` = พ.ศ. `YYYY/xxxxx`; `storeCode/newStoreCode` เป็น string 5 หลัก; date/month payload เป็น ISO ค.ศ.; amount/percent validate เป็น number 2 decimals |
| Workflow transition | `/documents/{docNo}/actions` รับ `{result,comment}` เท่านั้น; `result` เป็น 6-enum ไทย verbatim (ค่า "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" ตาม SDD GI); service lookup transition จาก `section+result+amountFlag` (วงเงิน GM 50,000 / AVP 300,000); response `{nextSection,statusCode,status}` — positive path `06→08→01→02→03→99` โดย `99` = เสร็จสิ้นและ `nextSection=null` |
| RBAC/Menu | เมนู/สิทธิ์เข้าหน้าใช้ระบบเดิม (BFF `GET /menus` + `GET /groups/current-user/permissions` — `canView/canManage/canExport/canOther` ต่อ URL); SBPGI คำนวณเฉพาะธงเชิง workflow: current task owner + `permissions.canEditSections`/`canAction` ใน detail API |
| Audit/Reason | master/config/email mutation ต้อง validate `reason` และเขียน `audit_logs` ใน transaction เดียว (การแก้สิทธิ์/กลุ่มลง audit ของระบบเดิม); workflow action เขียน `consideration_logs`; batch เขียน `job_run_histories` |
| Idempotency | endpoint จาก job/service ใช้ `requestId` หรือ business key; duplicate ต้องคืน existing result หรือ 409 ตามกฎ endpoint |

## 1. Stack และเวอร์ชัน

> **ตัดสินใจ 2026-08-05: ยึด stack ตามระบบ SBP เดิม (store-backend)** — NestJS + TypeORM + PostgreSQL · ตารางนี้อัปเดตแล้วทั้งหมด

| ส่วน | เลือกใช้ | เหตุผล / ข้อกำหนด |
|---|---|---|
| Runtime | **Node.js >= 20** + **TypeScript** (`strict: true`) | ตามโจทย์ |
| Framework | **NestJS 11** (module-per-domain · controller → service → repository) + `ResponseInterceptor` ห่อ `{success,data}` · `HttpContext` ด้วย AsyncLocalStorage | ตรงกับ `srm-sps-spsap-store-backend` เดิม |
| DB | **PostgreSQL** (AWS RDS · schema แยกของ SBPGI เช่น `sps_sbpgi` บน database เดียวกับระบบเดิม) รองรับ **read-replica routing** แบบ store-backend | 21 ตาราง ใช้ transaction/constraint หนัก |
| Query | **TypeORM 0.3** — entity ใน `src/entitys/` (= source of truth ของ 21 ตาราง) · repository provider pattern (`{provide:'X_REPOSITORY', useFactory: ds => ds.getRepository(X), inject:['DATA_SOURCE']}`) · `query()` ดิบเฉพาะรายงาน/dashboard (ตัวอย่างใน `SQL_BY_PATH`) | ตรงกับ convention ระบบเดิม · `synchronize:false` เสมอ |
| Validation | **class-validator + class-transformer** ผ่าน `ValidationPipe` (DTO ต่อ endpoint ใน `dto/`) | ตรงกับระบบเดิม · error message ไทยตาม SRS |
| Auth | **ตัดออก — ใช้ระบบเดิม** (ตัดสินใจ 2026-08-05): ไม่มี jsonwebtoken/bcrypt login ใน SBPGI — ตรวจ `x-api-key` จาก BFF + อ่าน user-context headers เท่านั้น | Cognito + BFF + auth-backend ของ SBP เดิม |
| Scheduler | **node-cron** (in-process) — cron ต่อ job อ่านจาก `job_configs` | Jobs 1–10 |
| ไฟล์/SFTP | **ssh2-sftp-client** (QSSI/STA) · **mssql** (ALLMAP read-only) · **iconv-lite** (WINDOWS-874/TIS-620) | interface เดิม |
| Email | **nodemailer** (SMTP, UTF-8) — template จาก `email_templates` (EM-01–08) | Notification Service |
| Upload | **multer** (memory) → disk `storage/attachments/` + แถว `document_attachments` | ≤ 5MB + ext whitelist |
| Log | **pino** (JSON) + request id + redact | |
| Test | **vitest** + **supertest** (+ postgres จริงสำหรับ integration) | coverage `workflow/` ≥ 90% |
| Doc | `@nestjs/swagger` generate จาก DTO/decorator — ต้องตรงกับ api.md **30 เส้น 6 กลุ่ม** | |

เครื่องมือคุณภาพ (Phase 0): **husky + lint-staged + commitlint** (Conventional Commits) · **Bitbucket Pipelines** (import template กลางของกลุ่ม `srm-sps-spsap` — SonarQube/Trivy → deploy ECS): `lint → tsc --noEmit → test → build` (postgres service container) · path alias `@/` = `src/`

## 2. โครงสร้างโฟลเดอร์ (บังคับ — module-per-domain + layered)

หลักการชั้น (dependency ทางเดียว): `module → controller → service → repository → TypeORM DataSource`
- **controller**: แปลง HTTP ↔ DTO เท่านั้น — **ห้ามมี business logic**
- **service**: business logic + transaction ทั้งหมด — **ห้ามแตะ req/res**
- **repository**: TypeORM repository / QueryBuilder / raw SQL เท่านั้น — คืน entity ไม่คืน DTO
- ข้าม module ได้เฉพาะชั้น **service** (documents.service → notification.service ได้ · ห้ามข้ามไป repo ของ module อื่น)
- DTO + class-validator decorator = source of truth ของสัญญา request/response

```
sbpgi-be/
  src/entitys/                  # 21 ตาราง 3 โซน + enum ทุกตัว — แปลงตรงจาก database.md (§5)
  src/migrations/               # TypeORM migration (ห้ามใช้ synchronize)
  src/database/seed.ts          # §10 — idempotent (upsert)
  storage/                      # attachments/ exports/ (volume แยก — stateless app)
  src/
    main.ts  app.module.ts      # bootstrap · helmet+cors+ValidationPipe+ResponseInterceptor+exception filters · enableShutdownHooks
    config/                     # ConfigModule + validate .env — fail fast (§7.1) · data-source.ts (DataSource + read replica)
    common/
      filters/                  # HttpExceptionFilter + OtherExceptionsFilter → {code,message} (§7.2)
      interceptors/             # ResponseInterceptor ห่อ {success,data} · LogControllerErrorInterceptor
      guards/                   # ApiKeyGuard (x-api-key จาก BFF) + PermissionGuard
    middlewares/
      userContext.ts            # ตรวจ x-api-key จาก BFF + อ่าน x-user-id/x-user-group-id/x-user-permissions → req.user (§7.3) — แทน auth.ts/JWT เดิม (ตัดออก — ใช้ระบบเดิม)
      requirePermission.ts      # 403 ถ้าสิทธิ์จาก x-user-permissions/x-user-group-id ไม่พอ (แทน requireRole เดิม)
      http-context.ts           # AsyncLocalStorage (request id + user context) แบบ store-backend เดิม
      serviceToken.ts           # header Authorization: Bearer <SERVICE_TOKEN> (Job 8b → /workflows/instances)
      apiKey.ts                 # header X-Api-Key (STA callback)
    modules/                    # ไม่มี module auth/ (ตัดออก — ใช้ระบบเดิม) · masters/ เหลือ factors + audit-logs
      tasks/  documents/  lookup/  masters/  configs/
      emailTemplates/  reports/  jobs/  workflows/  interfaces/  dashboard/
        *.routes.ts *.controller.ts *.service.ts *.repo.ts *.schema.ts *.test.ts
    workflow/
      engine.ts                 # applyAction(): transaction เต็ม (§7.5)
      transitions.ts            # ตาราง transition เป็น data — ลอกครบจาก workflow.md (§6)
      genFlowGate.ts            # 6 เกณฑ์ (§7.6)
    notification/
      mailer.ts  renderer.ts  queue.ts   # คิว in-memory + retry 3 ครั้ง — นอก transaction เสมอ
      rules.ts                  # event → EM-xx → ผู้รับ (§9)
    batch/
      scheduler.ts  runner.ts   # lock กันรันซ้อน (§7.7)
      jobs/job01.ts job02.ts job03.ts job04.ts job05.ts job06.ts job08b.ts job10.ts
    interfaces/
      sftp.ts  allmap.ts  fileCodec.ts   # fixed-width + iconv-lite + golden-file tests
    lib/
      errors.ts                 # AppError (§7.2)
      docNo.ts                  # เลขเอกสาร FOR UPDATE (§7.4)
      date.ts                   # พ.ศ.↔ค.ศ. (payload = ISO ค.ศ. · เลขเอกสาร/ไฟล์ interface = พ.ศ.)
      audit.ts                  # writeAudit (§7.8)
      cache.ts                  # in-memory TTL 5 นาที (configs / dashboard)
```

## 3. มาตรฐาน API + Error Catalog

- Base `/api/v1` · JSON UTF-8 · **ไม่มี endpoint `/auth/*` ใน SBPGI** — user endpoint ทุกเส้นตรวจ `x-api-key` จาก BFF + user-context headers (`x-user-id`/`x-user-group-id`/`x-user-permissions`) **ยกเว้น**: `POST /workflows/instances` (service token) · `POST /interfaces/sta/ack` (API key ของ STA)
- Pagination: `?page=1&size=20` → `{page,size,total,items}` (default size 20 · max 100)
- วันที่ใน payload = ISO-8601 ค.ศ. (FE แปลง พ.ศ.) — ยกเว้นเลขเอกสารและไฟล์ interface ที่เป็น พ.ศ.
- ทุกเส้นที่แก้ข้อมูลบันทึกผู้ทำจาก `x-user-id` (user context ที่ BFF แนบมา) ลง audit ตามโดเมน (consideration_logs / audit_logs / job_run_histories)

**Error รูปเดียวทั้งระบบ** `{"code":"...","message":"<ไทย verbatim ตาม SRS>"}` — โยน `AppError` (extends `HttpException`) แล้ว `HttpExceptionFilter` แปลง:

| HTTP | code | ใช้เมื่อ | ตัวอย่าง message (verbatim ที่ SRS กำหนด) |
|---|---|---|---|
| 400 | `VALIDATION` | ValidationPipe fail / กติกาธุรกิจ input | `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ` |
| 400 | `DOC_PERCENT_400` | %ชดเชยรวม ≠ 100% | `เปอร์เซ็นต์ชดเชยรวมทุกร้านต้องเท่ากับ 100%` |
| 400 | `REPORT_YEAR_400` | ไม่ส่งปี (พ.ศ.) ใน /documents, /reports | `กรุณาระบุปีที่ต้องการค้นหา` |
| 401 | `AUTH_401` | `x-api-key` ผิด/ไม่ส่ง · user-context header ขาด · service token/API key ผิด | |
| 403 | `FORBIDDEN` | สิทธิ์จาก x-user-permissions ไม่พอ / section ≠ current / is_editable=false | |
| 404 | `NOT_FOUND` | ไม่พบ resource | |
| 409 | `CONFLICT` | factor_code ซ้ำ · ร้าน+งวดซ้ำ · action บนเอกสารจบแล้ว · job รันซ้อน | |
| 422 | `BUSINESS_RULE` | ข้อมูลครบเชิง schema แต่ไม่ผ่าน business rule เช่น Gen Flow Gate ยังไม่พร้อม / transition ใช้ไม่ได้ | |
| 413 | `FILE_TOO_LARGE` | ไฟล์แนบเกิน 5MB | |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | นามสกุล/ชนิดไฟล์แนบไม่อยู่ใน whitelist | |
| 429 | `RATE_LIMIT` | ~~login เกิน limit~~ **ตัดออก — ไม่มี login ใน SBPGI** (rate limit ฝั่ง login อยู่ที่ Cognito/BFF ระบบเดิม) | |
| 500 | `INTERNAL` | error ไม่คาดคิด (log เต็ม · ไม่ leak stack) | |

> ข้อความไทยทุกตัวรวมศูนย์ที่ `lib/messages.ts` (const object) — ห้าม hardcode กระจายตามไฟล์ เพื่อให้เทียบ verbatim กับ SRS ได้จุดเดียว

## 4. ตาราง endpoint (สัญญาผูกมัด — path/method ห้ามเปลี่ยน)

> **ตัวเลขปัจจุบัน: 30 เส้น 6 กลุ่ม** (Lookup 3 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3) — ตารางด้านล่างเป็นรายการรุ่น 44 เส้น 9 กลุ่ม แถวที่ทำเครื่องหมาย "ตัดออก" หรืออยู่ในกลุ่ม Auth/System Config/Email Template/Batch Job Admin/`audit_logs`/`dashboard` **ไม่ต้อง implement** · ยึด `api.md` / `plan-api.html` เป็นสัญญาจริง

สิทธิ์: `ทุก role` = ผ่าน user context จาก BFF (x-api-key + headers) · `admin` = สิทธิ์จัดการจาก `x-user-permissions` (group ผู้ดูแล — role 01 Admin / 03 User Admin ของ SRS map เป็น group ใน auth-backend) · `section` = ผู้เรียกต้องเป็น section ปัจจุบันของเอกสาร · `svc` = SERVICE_TOKEN · `key` = API key ของ STA
ตาราง R = อ่าน · W = เขียน · SQL แนวทางต่อเส้น = `SQL_BY_PATH['METHOD path']` ใน `plan-api.html`

### กลุ่ม 1 · Auth — **ตัดออก ใช้ระบบ SBP เดิม** (ตัดสินใจ 2026-08-05)

เดิม 4 เส้น (`POST /auth/login` · `POST /auth/refresh` · `GET /auth/me` · `GET /me/menus`) — FE ใช้ของระบบเดิมผ่าน BFF แทน: login redirect (Cognito · cookie httpOnly) · `/auth/refresh` · `/auth/profile` + `/users/current` · `/menus` + `/groups/current-user/permissions` (ดู "เส้นที่ตัดออก" ใน `api.md`)

### กลุ่ม 2 · งาน & เอกสาร (10 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 1 | GET `/tasks` | ทุก role | R: workflow_tasks, compensation_documents | inbox = task เปิดของ section ที่ map กับ group ผู้เรียก · paginate · **SDD GI:** filter + เลือกหลายเอกสาร (bulk action) · เจ้าหน้าที่/ฝ่าย SBP DSA เห็นเอกสารได้**ทุกสาขา** (query scope ไม่จำกัดงานตน) · ทีมส่งเสริม/บัญชีตามสิทธิ์เดิม |
| 2 | GET `/documents` | ทุก role | R: compensation_documents | **ไม่ส่งปี พ.ศ. → 400 REPORT_YEAR_400** · filter สถานะ/ร้าน/งวด · scope DSA เห็นทุกสาขา (SDD GI) |
| 3 | GET `/documents/{docNo}` | ทุก role | R: compensation_documents + ลูกทั้งชุด | ไม่พบ → 404 · คืนธง `editableSections`/`myRoleView` ต่อ role-section |
| 4 | POST `/documents` | 00,01,06(section 06) | W: compensation_documents, document_new_stores, workflow_instances, workflow_tasks, doc_no_counters | MANUAL/FS · **SDD GI: 409 เฉพาะมีเอกสาร active (ยังไม่จบ) ของร้าน+เดือนนั้น** — เอกสารเดิมที่จบด้วยหยุดชดเชย/เห็นควรไม่ชดเชย เปิดเรื่องใหม่ได้ (เดือนเดียวกัน/ถัดไป · ยกเลิกการเปิด SR) · transaction เดียว (ออกเลข+instance+task 06) |
| 5 | PUT `/documents/{docNo}` | section | W: document_new_stores, document_competitors, document_external_factors | section ≠ current → 403 · **%ชดเชยรวม ≠ 100% → 400 DOC_PERCENT_400** |
| 6 | POST `/documents/{docNo}/actions` | section | W: compensation_documents, workflow_tasks, consideration_logs | ไม่ส่ง result → 400 verbatim · result ไม่ชดเชยไม่มี comment → 400 · เอกสารจบแล้ว → 409 · section ≠ current → 403 · routing ตามวงเงิน GM 50,000 / AVP 300,000 (§6) |
| 7 | GET `/documents/{docNo}/timeline` | ทุก role | R: consideration_logs | เรียงเวลา |
| 8 | POST `/documents/{docNo}/attachments` | section | W: document_attachments | > 5MB / ext นอก whitelist → 400 |
| 9 | GET `/documents/{docNo}/sales` | ทุก role | R: sales_transactions, fgi_impact_sales_summaries | 4 หน้าต่าง × 15 วัน ผ่าน impact_process_id |
| 10 | GET `/documents/{docNo}/attachments/{attachId}/download` | ทุก role ที่อ่านเอกสารได้ | R: document_attachments | attachment ต้องเป็นของ docNo และ scan_status=CLEAN |

### กลุ่ม 3 · Lookup (4 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 11 | GET `/store/search` (ระบบ SBP เดิม) | ทุก role | R: stores / impacted_stores | `type=impacted\|new` บังคับ — อื่น/ไม่ส่ง → 400 |
| 12 | GET `/competitors` | ทุก role | R: competitors | master 11 ราย (01–11 · ชื่อไทย+อังกฤษ) |
| 13 | GET `/document-statuses` | ทุก role | R: document_statuses | **6 ค่า** (เฉพาะ active) |
| 14 | GET `/workflow-sections` | ทุก role | R: workflow_sections | **5 ขั้น** (ไม่รวม 04/05 is_active=false) |

### กลุ่ม 4 · Masters (5 เส้น — เดิม 19)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 15 | GET `/factors` | ทุก role | R: external_factors | |
| 16 | POST `/factors` | admin | W: external_factors | **factor_code ซ้ำ → 409** message ไทยตาม SRS |
| 17 | PUT `/factors/{code}` | admin | W: external_factors, audit_logs | reason บังคับ |
| 18 | DELETE `/factors/{code}` | admin | W: external_factors, audit_logs | มี document_external_factors อ้าง → 409 |
| 19 | GET `/audit-logs` | admin | R: audit_logs | filter table/refKey · paginate |

> **ตัดออก — ใช้ระบบเดิม (ตัดสินใจ 2026-08-05 · 14 เส้น):** ผู้ปฏิบัติงาน `GET/POST/PUT/DELETE /operators` · `/operators/{id}` · `GET /employees/search` (แทนด้วย group+scope ของ auth-backend — จัดการหน้า `/setting/manage-user-rights` · ค้นพนักงานผ่าน employee backend เดิม) และสิทธิ์เมนู `/menu-permissions*` · `/roles*` · `/menus*` (แทนด้วย auth-backend: `/groups` · `/groups/{id}/permissions` · `/menus`) — ห้ามสร้าง route เหล่านี้ใน SBPGI

### กลุ่ม 5 · System Config (5 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 20 | GET `/configs` | admin | R: system_configs | filter category |
| 21 | GET `/configs/{key}` | ทุก role | R: system_configs | cache 5 นาที |
| 22 | POST `/configs` | admin | W: system_configs, audit_logs | validate ตาม value_type → 400 · **key หน้าตา secret (password/secret/token) → 400** |
| 23 | PUT `/configs/{key}` | admin | W: system_configs, audit_logs | `is_editable=false` → 403 · reason บังคับ · invalidate cache ทันที |
| 24 | DELETE `/configs/{key}` | admin | W: system_configs, audit_logs | is_editable=false → 403 |

### กลุ่ม 6 · Email Templates (5 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 25 | GET `/email-templates` | admin | R: email_templates | 8 template EM-01–08 |
| 26 | GET `/email-templates/{code}` | admin | R: email_templates, status_email_rules | |
| 27 | PUT `/email-templates/{code}` | admin | W: email_templates, audit_logs | แก้ได้เฉพาะ subject/body (From/To/Cc ล็อกตาม rules) · reason บังคับ |
| 28 | POST `/email-templates/{code}/reset` | admin | W: email_templates, audit_logs | คืน default_subject/default_body |
| 29 | POST `/email-templates/reset-all` | admin | W: email_templates, audit_logs | |

### กลุ่ม 7 · รายงาน (2 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 30 | GET `/reports/status-summary` | group รายงาน (map จาก role 01,04,06) | R: compensation_documents, consideration_logs, document_new_stores | **ปี พ.ศ. required → 400** · filter: status(6 · บังคับ) · **`periodStatement` บังคับเมื่อ status = เสร็จสิ้นดำเนินการ (SDD GI) — ไม่ส่ง → 400** · result(ประกันรายได้/ไม่ประกันรายได้ จาก result_category ล่าสุด) · region(**13 รหัส + ภาคใหม่เพิ่มอัตโนมัติ** — อ่านจาก master ไม่ hardcode) · storeType(A–D multi) · impactedStoreCode · newStoreCode · เฉพาะรายการมีเลขเอกสาร |
| 31 | GET `/reports/status-summary/export` | group รายงาน (map จาก role 01,04,06) | R: เดียวกับข้อ 30 + W ไฟล์ `storage/exports/` | เงื่อนไข/validation เดียวกับข้อ 30 · CSV UTF-8 **มี BOM** + Content-Disposition |

### กลุ่ม 8 · Batch Job Admin (6 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 32 | GET `/jobs` | admin | R: job_configs, job_run_histories | 11 entry points + สถานะล่าสุด |
| 33 | GET `/jobs/{jobNo}` | admin | R: job_configs | |
| 34 | PUT `/jobs/{jobNo}/params` | admin | W: job_configs, audit_logs | แก้ตัว non-editable → 400 |
| 35 | PUT `/jobs/{jobNo}/enabled` | admin | W: job_configs, audit_logs | |
| 36 | POST `/jobs/{jobNo}/run` | admin | W: job_run_histories + ตารางตาม job | **รันซ้อน (มีแถว RUNNING) → 409** |
| 37 | GET `/jobs/{jobNo}/runs` | admin | R: job_run_histories | paginate |

### กลุ่ม 9 · Workflow ภายใน (3 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 38 | POST `/workflows/instances` | svc | R/W: fgi_impact_processes, impacted_stores, stores, fgi_impact_stores, fgi_impact_sales_summaries; W: workflow_instances, workflow_tasks | **Gen Flow Gate W/Y/N** — status source of truth อยู่ fgi_impact_processes; ผ่านตอบ Y; branch type นอกเซ็ตตั้ง N; ข้อมูลยังไม่พร้อมคง W + 422/reason · token ผิด → 401 |
| 39 | GET `/workflows/instances/{id}` | ทุก role | R: workflow_instances, workflow_tasks | 404 ถ้าไม่พบ |
| 40 | GET `/workflows/summary` | admin | R: fgi_impact_processes, workflow_tasks | ตัวเลข W/Y/N + งานค้างต่อ section |

### กลุ่ม 10 · Interface & Dashboard (4 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 41 | GET `/interfaces/tracking` | admin | R: interface_transactions | filter data_name/ช่วงวัน |
| 42 | GET `/interfaces/pending-ack` | admin | R: interface_transactions | ACK ค้าง ≥ 1 วัน (ฐานเดียวกับ Job 10) |
| 43 | POST `/interfaces/sta/ack` | key | W: interface_transactions | key ผิด/ไม่ส่ง → 401 · อัปเดต sta_status |
| 44 | GET `/dashboard/summary` | ทุก role | R: aggregate หลายตาราง | cache in-memory TTL 5 นาที |

> **ไม่มี:** `GET /abnormal-stores` · `POST /abnormal-stores/assign` — **ยกเลิกและลบทิ้งถาวร 2026-08-06** พร้อมหน้าจอ (script Phase 7 ต้องยืนยันว่า**ไม่มี**)

## 5. TypeORM entities — enum ทุกตัว + ตัวอย่าง entity หลัก 6 ตัว

**21 ตาราง** ตาม `database.md` §Data Dictionary ฉบับปัจจุบัน (รายการด้านล่างเขียนไว้ตอน 34 ตาราง — ตารางที่ถูกตัด 13 ตัวห้ามสร้าง entity · checklist ต่อตารางใน `checklist-be.md` §0.2–0.4)
**ตารางที่ตัดออก (ตัดสินใจ 2026-08-05 — ใช้ระบบ SBP เดิม):** `roles` / `menus` / `menu_permissions` (→ auth-backend groups/menus/permissions ต่อ URL) · `user_accounts` (→ Cognito + auth-backend — SBPGI รับตัวตนจาก header) · `operator_assignments` (→ group+scope ของ auth-backend + prepared approvers ของ workflow engine เดิม) — **ห้ามสร้าง entity เหล่านี้**
**ตารางที่เพิ่มจากการเทียบ DB เดิมของ K2 (2026-08-06 · `script_TB_DB_CPA_FRN_FGI_20260722.sql`):** `zones` (ZoneProfile) · `branch_types` (BranchTypeProfile — เก็บชื่อฝั่ง FMS/FGI แยกกัน) · `decisions` (DecisionProfile — 3 ชื่อต่อรายการ) · `document_running_numbers` (RunningNumber) · `document_cost_details` (ImpactCostDetail) — พร้อมคอลัมน์เติม `workflow_sections.approve_limit_amount`, `compensation_documents.round_no/loop_no/allmap_url/statement_id/approver_snapshot`

Convention ตาม `store-backend` เดิม: entity อยู่ `src/entitys/` · `@Entity({ schema: 'sps_sbpgi', name: 'lower_snake_case' })` · identity ต่อตาราง (ไม่ใช้ sequence รวม — Errata E18) · `synchronize: false` เสมอ · เปลี่ยน schema ผ่าน migration เท่านั้น

### 5.1 Enum ทุกตัว (บังคับระดับ DB ด้วย `type: 'enum'` — insert นอกเซ็ตต้องถูก reject)

```ts
// src/common/enums.ts — ใช้ร่วมกับ @Column({ type: 'enum', enum: X })
export enum VerifyStatus       { W = 'W', P = 'P', Y = 'Y', N = 'N' }        // fgi_impact_stores.verify_status
export enum WorkflowGenStatus  { W = 'W', Y = 'Y', N = 'N' }                 // fgi_impact_processes.workflow_generation_status (source of truth)
export enum ActionStatus       { Y = 'Y', W = 'W', N = 'N' }                 // fgi_impact_processes.action_status
export enum StaStatus          { I='I', C='C', A='A', N='N', S='S', Z='Z' }  // interface_transactions.sta_status
export enum InterfaceDataName  { AMS06001O='AMS06001O', AMS06001I='AMS06001I', FRBC0001='FRBC0001', QSSI_MRS='QSSI_MRS', RT040035='RT040035', RT040078='RT040078' }
export enum SourceSystem       { ALM = 'ALM', USER = 'USER' }                // document_competitors.source_system
export enum ResultCategory     { APPROVE='APPROVE', REJECT='REJECT', PENDING='PENDING' }  // consideration_logs
export enum DocumentOrigin     { AUTO='AUTO', FS='FS' }                      // compensation_documents.origin — ตัด MANUAL (2026-08-06: ไม่มีฟอร์มสร้างเอกสารใน FE)
export enum InstanceStatus     { ACTIVE='ACTIVE', COMPLETED='COMPLETED', CANCELLED='CANCELLED' }
export enum TaskStatus         { OPEN = 'OPEN', CLOSED = 'CLOSED' }
export enum ConfigCategory     { IMPACT='IMPACT', WORKFLOW='WORKFLOW', DOCUMENT='DOCUMENT', AUTH='AUTH', NOTIFICATION='NOTIFICATION', BATCH='BATCH' }
export enum ConfigValueType    { NUMBER='NUMBER', STRING='STRING', BOOLEAN='BOOLEAN', JSON='JSON', CRON='CRON' }
export enum AuditActionType    { CREATE='CREATE', UPDATE='UPDATE', DELETE='DELETE', RESET='RESET' }
export enum JobRunStatus       { RUNNING='RUNNING', SUCCESS='SUCCESS', ERROR='ERROR' }
// enum MenuGroup — ตัดออก (ตารางเมนู/สิทธิ์ใช้ระบบ SBP เดิม · ตัดสินใจ 2026-08-05)
```

### 5.2 ตัวอย่าง entity 6 ตัวหลัก

```ts
@Entity({ schema: 'sps_sbpgi', name: 'compensation_documents' })
@Index(['impactedStoreCode', 'periodMonth'])
@Index(['statusCode', 'currentSectionCode'])
export class CompensationDocument {
  @PrimaryColumn({ name: 'doc_no', length: 10 })            docNo: string;            // "2026/00185" (พ.ศ.)
  @Column({ name: 'status_code', length: 2 })               statusCode: string;
  @Column({ name: 'current_section_code', length: 2, nullable: true }) currentSectionCode: string | null;  // NULL เมื่อเสร็จสิ้น
  @Column({ name: 'impacted_store_code', length: 5 })       impactedStoreCode: string;
  @Column({ name: 'impact_process_id', type: 'bigint', nullable: true, unique: true }) impactProcessId: string | null;  // FK 1 รอบ : 1 เอกสาร
  @Column({ name: 'origin', type: 'enum', enum: DocumentOrigin, default: DocumentOrigin.AUTO }) origin: DocumentOrigin;
  @Column({ name: 'period_month', length: 7 })              periodMonth: string;      // งวด YYYY-MM (ค.ศ.)
  @Column({ name: 'compensation_amount', type: 'numeric', precision: 14, scale: 2, nullable: true }) compensationAmount: string | null;

  // --- เติมจาก CompensateFlow ของ K2 เดิม (2026-08-06) ---
  @Column({ name: 'round_no', type: 'int', default: 1 })     roundNo: number;          // = CompMainLoopNo — "รอบ 1"
  @Column({ name: 'loop_no', type: 'int', default: 1 })      loopNo: number;           // = CompLoopNo — "ครั้งที่ 3"
  @Column({ name: 'allmap_url', type: 'text', nullable: true }) allmapUrl: string | null;   // = CompUrlMap — ปุ่ม Link To ALLMAP
  @Column({ name: 'statement_id', length: 50, nullable: true }) statementId: string | null; // = CompStatementID — ต้นทางจาก FS/SBP Statement
  @Column({ name: 'account_year', length: 4, nullable: true }) accountYear: string | null;
  @Column({ name: 'account_month', length: 2, nullable: true }) accountMonth: string | null;
  @Column({ name: 'approver_snapshot', type: 'jsonb', nullable: true }) approverSnapshot: ApproverSnapshot | null;
  // ↑ FC/Section/Manager/GM/AVP + ชื่อ/อีเมล ณ เวลาเปิดเอกสาร — จำเป็นเพราะตำแหน่งมาจาก HR Connect ของระบบเดิมและเปลี่ยนได้
  //   (SDD GI: ผู้รักษาการเป็นผู้อนุมัติไม่ได้ → ต้อง freeze สายอนุมัติไว้กับเอกสาร)

  @Column({ name: 'created_by' })                            createdBy: string;
  @CreateDateColumn({ name: 'created_at' })                  createdAt: Date;
  @UpdateDateColumn({ name: 'updated_at' })                  updatedAt: Date;

  @ManyToOne(() => DocumentStatus)  @JoinColumn({ name: 'status_code' })          status: DocumentStatus;
  @ManyToOne(() => WorkflowSection) @JoinColumn({ name: 'current_section_code' }) section: WorkflowSection | null;
  @OneToMany(() => DocumentNewStore, r => r.document)        newStores: DocumentNewStore[];
  @OneToMany(() => ConsiderationLog, r => r.document)        logs: ConsiderationLog[];
  @OneToOne(() => WorkflowInstance, r => r.document)         instance: WorkflowInstance;

  // SDD GI: กันซ้ำเฉพาะเอกสาร active — ห้ามใส่ unique เต็มคู่ (เอกสารที่จบด้วยหยุด/ไม่เห็นควรชดเชย เปิดใหม่ทับได้)
  // → partial unique index ผ่าน migration SQL:
  //   CREATE UNIQUE INDEX ux_doc_active ON sps_sbpgi.compensation_documents (impacted_store_code, period_month) WHERE status_code <> '99';
  //   + service ตรวจซ้ำใน transaction เดียวกับ POST /documents (คืน 409 เฉพาะพบเอกสาร active)
}

@Entity({ schema: 'sps_sbpgi', name: 'workflow_instances' })
export class WorkflowInstance {
  @PrimaryColumn({ name: 'instance_id', length: 36 })        instanceId: string;
  @Column({ name: 'doc_no', length: 10, unique: true })      docNo: string;            // 1 เอกสาร : 1 instance
  @Column({ name: 'instance_status', type: 'enum', enum: InstanceStatus, default: InstanceStatus.ACTIVE }) status: InstanceStatus;
  @CreateDateColumn({ name: 'started_at' })                  startedAt: Date;
  @Column({ name: 'started_by' })                            startedBy: string;
  @Column({ name: 'completed_at', type: 'timestamptz', nullable: true }) completedAt: Date | null;

  @OneToOne(() => CompensationDocument, d => d.instance) @JoinColumn({ name: 'doc_no' }) document: CompensationDocument;
  @OneToMany(() => WorkflowTask, t => t.instance)            tasks: WorkflowTask[];
}

@Entity({ schema: 'sps_sbpgi', name: 'workflow_tasks' })
@Index(['sectionCode', 'status'])
export class WorkflowTask {
  @PrimaryGeneratedColumn({ name: 'task_id', type: 'bigint' }) taskId: string;
  @Column({ name: 'instance_id', length: 36 })               instanceId: string;
  @Column({ name: 'doc_no', length: 10 })                    docNo: string;
  @Column({ name: 'section_code', length: 2 })               sectionCode: string;
  @Column({ name: 'assignee_employee_id', nullable: true })  assigneeEmployeeId: string | null;
  // ↑ NULL = ทั้ง section · resolve จาก group+scope ของ auth-backend + prepared approvers (ไม่มี operator_assignments ใน SBPGI)
  //   SDD GI: เคสต่อเนื่อง/เห็นควรไม่ชดเชย → auto-assign เจ้าของงานคนเดิม
  @Column({ name: 'task_status', type: 'enum', enum: TaskStatus, default: TaskStatus.OPEN }) status: TaskStatus;
  @Column({ name: 'action_result', nullable: true })         actionResult: string | null;
  @CreateDateColumn({ name: 'opened_at' })                   openedAt: Date;
  @Column({ name: 'closed_at', type: 'timestamptz', nullable: true }) closedAt: Date | null;
  // waiting_days = now - opened_at (ใช้กับ EM-04/05 + stat card "รอเกิน 3 วัน")

  @ManyToOne(() => WorkflowInstance, i => i.tasks) @JoinColumn({ name: 'instance_id' }) instance: WorkflowInstance;
}

@Entity({ schema: 'sps_sbpgi', name: 'consideration_logs' })
@Index(['docNo', 'actionDatetime'])
export class ConsiderationLog {
  @PrimaryGeneratedColumn({ type: 'bigint' })                id: string;
  @Column({ name: 'doc_no', length: 10 })                    docNo: string;
  @Column({ name: 'section_code', length: 2 })               sectionCode: string;
  @Column({ name: 'decision_code', length: 2, nullable: true }) decisionCode: string | null;  // → decisions (master · 2026-08-06)
  @Column()                                                  result: string;           // ข้อความไทย verbatim ณ เวลากด (snapshot)
  @Column({ type: 'text', nullable: true })                  detail: string | null;    // required ที่ service เมื่อไม่ชดเชย
  @Column({ name: 'result_category', type: 'enum', enum: ResultCategory }) resultCategory: ResultCategory;  // ฐาน filter ประกันรายได้/ไม่ประกันรายได้
  @Column({ name: 'consider_by' })                           considerBy: string;
  @CreateDateColumn({ name: 'action_datetime' })             actionDatetime: Date;

  @ManyToOne(() => CompensationDocument, d => d.logs) @JoinColumn({ name: 'doc_no' }) document: CompensationDocument;
}

@Entity({ schema: 'sps_sbpgi', name: 'interface_transactions' })
@Index(['dataName', 'sentAt'])
export class InterfaceTransaction {
  @PrimaryGeneratedColumn({ type: 'bigint' })                id: string;
  @Column({ name: 'data_name', type: 'enum', enum: InterfaceDataName }) dataName: InterfaceDataName;
  // typed FK 3 คอลัมน์ — ห้าม polymorphic key (แก้ P1 + บั๊ก parseInt เลขศูนย์นำหน้า)
  @Column({ name: 'impact_process_id', type: 'bigint', nullable: true }) impactProcessId: string | null;
  @Column({ name: 'sales_summary_id', type: 'bigint', nullable: true })  salesSummaryId: string | null;
  @Column({ name: 'doc_no', length: 10, nullable: true })    docNo: string | null;
  @Column({ name: 'file_name', nullable: true })             fileName: string | null;
  @Column({ name: 'sta_status', type: 'enum', enum: StaStatus, nullable: true }) staStatus: StaStatus | null;
  @Column({ name: 'acked_at', type: 'timestamptz', nullable: true }) ackedAt: Date | null;  // NULL + ส่งไป ≥ 1 วัน = pending-ack (Job 10)
  @CreateDateColumn({ name: 'sent_at' })                     sentAt: Date;
}

@Entity({ schema: 'sps_sbpgi', name: 'system_configs' })
export class SystemConfig {
  @PrimaryColumn({ name: 'config_key' })                     configKey: string;        // dot notation: workflow.gm_amount_limit / workflow.avp_amount_limit
  @Column({ type: 'enum', enum: ConfigCategory })            category: ConfigCategory;
  @Column({ name: 'value_type', type: 'enum', enum: ConfigValueType }) valueType: ConfigValueType;  // validate ก่อนบันทึก
  @Column({ name: 'config_value', type: 'text' })            configValue: string;      // เก็บ string เดียว แปลงตาม valueType
  @Column({ type: 'text', nullable: true })                  description: string | null;
  @Column({ name: 'is_editable', default: true })            isEditable: boolean;      // false = ค่าคงที่ธุรกิจ แก้ผ่าน API ไม่ได้
  @Column({ name: 'updated_by', nullable: true })            updatedBy: string | null;
  @UpdateDateColumn({ name: 'updated_at' })                  updatedAt: Date;
  // ห้ามมี secret — POST/PUT ปฏิเสธ key ที่มี password/secret/token (400)
}

@Entity({ schema: 'sps_sbpgi', name: 'document_running_numbers' })
export class DocumentRunningNumber {     // = RunningNumber ของ K2 เดิม (2026-08-06) — แทนชื่อ doc_no_counters ในร่างก่อนหน้า
  @PrimaryColumn({ name: 'year', type: 'int' })           year: number;           // ปี พ.ศ. เช่น 2569
  @Column({ name: 'last_running_no', type: 'int', default: 0 }) lastRunningNo: number;
}
```

## 6. Workflow Engine — ตาราง transition เต็ม + transitions.ts

**5 ขั้น 06→08→01→02→03 · สถานะ 6 ค่า** · วงเงินอ่านจาก `system_configs['workflow.gm_amount_limit']` (50,000) + `system_configs['workflow.avp_amount_limit']` (300,000) — **ห้าม hardcode** (SDD GI 24/02/2026 · แทน `workflow.avp_amount_threshold` = 100,000 เดิม)

### 6.1 สถานะเอกสาร 6 ค่า (seed `document_statuses` — status_code = section คู่ · END = `99` ตาม canonical `database.md`/`api.md`)

| status_code | สถานะ | Section คู่ |
|---|---|---|
| 06 | รอฝ่าย SBP DSA ดำเนินการ | 06 |
| 08 | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | 08 |
| 01 | รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ | 01 |
| 02 | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | 02 |
| 03 | รอผู้บริหารสำนักบริหาร SBP ดำเนินการ | 03 |
| 99 | เสร็จสิ้นดำเนินการ | — (END) |

> **ชื่อสถานะของขั้น 01 เปลี่ยนเป็น "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ"** พร้อมค่า `result` "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" — ตัดสินใจ 2026-08-06: เปลี่ยนคำเรียก "ฝ่ายส่งเสริม" → "หน่วยงานส่งเสริมธุรกิจ" **ทุกจุดของระบบ รวมชื่อสถานะเอกสาร** (SDD GI สั่งเปลี่ยนคำเรียกทั้งระบบ · ภาพหน้าจอในสไลด์ SDD ยังเป็นของเดิม — ถือว่าข้อความสั่งชนะภาพ) · seed `document_statuses` และ `decisions` ต้องใช้ข้อความใหม่

### 6.2 ตาราง transition เต็มทุกแถว (ลอกจาก `workflow.md` §สถานะเอกสารและเส้นทางพิจารณา · อัปเดตตาม SDD GI 24/02/2026)

| # | Section | ตัวเลือกพิจารณา (`result` — ไทย verbatim 6-enum) | เงื่อนไข | ไปที่ | result_category |
|---|---|---|---|---|---|
| 1 | 06 ฝ่าย SBP DSA | เห็นควรไม่ชดเชย | — | **เสร็จสิ้นดำเนินการ** (END) · SDD GI: รอบเดือนถัดไปสร้างงานอัตโนมัติ assignee คนเดิม (ดูหมายเหตุ) | REJECT |
| 2 | 06 | หยุดชดเชยประกันรายได้ | — | **เสร็จสิ้นดำเนินการ** (END) · เปิดเรื่องใหม่ได้เอง (SDD GI) | REJECT |
| 3 | 06 | **ส่งหน่วยงานส่งเสริมธุรกิจ SBP** (SDD GI: เปลี่ยนชื่อจาก "ส่งฝ่ายส่งเสริมธุรกิจ SBP") | — | รอ 01 | PENDING |
| 4 | 06 | ส่งเจ้าหน้าที่ SBP DSA | — | รอ 08 | PENDING |
| 5 | 08 เจ้าหน้าที่ SBP DSA | คำนวณเงินชดเชยเรียบร้อย | — | รอ 01 | PENDING |
| 6 | 08 | ส่งกลับ | — | รอ 06 (back-flow) | PENDING |
| 7 | 01 หน่วยงานส่งเสริมธุรกิจ SBP | เห็นควรชดเชย | — | รอ 02 | PENDING |
| 8 | 01 | เห็นควรไม่ชดเชย | — | **เสร็จสิ้นดำเนินการ** (END — ไม่อนุมัติในเดือนนั้น · SDD GI — เดิมตีกลับให้ 06 รับทราบ) | REJECT |
| 9 | 01 | ส่งกลับ | — | รอ 06 (back-flow) | PENDING |
| 10 | 02 GM ส่งเสริมธุรกิจ SBP | เห็นควรชดเชย | ยอด **≤ 50,000** | **เสร็จสิ้นดำเนินการ** (จบที่ GM — วงเงิน GM ตาม SDD GI) | APPROVE |
| 11 | 02 | เห็นควรชดเชย | ยอด **50,001–300,000** | รอ 03 (AVP สำนัก SBPM) | PENDING |
| 12 | 02 | เห็นควรชดเชย | ยอด **> 300,000** | **ยังไม่กำหนด — SDD ไม่ระบุเส้นทาง (รอ confirm)** · ไม่มีแถวใน TRANSITIONS → `findTransition` throw | — |
| 13 | 02 | เห็นควรไม่ชดเชย | — (ทุกวงเงิน) | **เสร็จสิ้นดำเนินการ** (END — ไม่อนุมัติในเดือนนั้น · SDD GI — เดิมตีกลับเป็นทอด ๆ) | REJECT |
| 14 | 02 | ส่งกลับ | — | รอ 01 (back-flow) | PENDING |
| 15 | 03 AVP | เห็นควรชดเชย | — | **เสร็จสิ้นดำเนินการ** (จบที่ AVP · วงเงิน 300,000/รายการ) | APPROVE |
| 16 | 03 | เห็นควรไม่ชดเชย | — | รอ 06 (back-flow) — **คงเดิม · SDD GI ไม่ได้ระบุขั้น AVP (รอ confirm)** | PENDING |
| 17 | 03 | ส่งกลับ | — | รอ 02 (back-flow) | PENDING |

> ขั้นบัญชี 04/05 ถูกตัดตาม SDD v7.5 — ทางเลือกเดิม "06 → ส่งฝ่ายบัญชี SBP" ยกเลิกด้วย · `result` ที่ไม่อยู่ใน 6-enum หรือไม่ถูกต้องสำหรับ section ปัจจุบัน → throw (400)
>
> **กติกาเปิดเรื่องซ้ำ/งานค้างที่ engine + service ต้อง implement (SDD GI 24/02/2026):**
> - เอกสารที่จบด้วย "หยุดชดเชย/เห็นควรไม่ชดเชย" **เปิดเรื่องใหม่ได้** (เดือนเดียวกัน/ถัดไป) — `POST /documents` ตอบ 409 เฉพาะมีเอกสาร active ของร้าน+เดือน (ดู §4 ข้อ 4 + partial unique index §5.2)
> - "เห็นควรไม่ชดเชย" ที่ 06 → รอบเดือนถัดไป job/logic ภายในดึงร้านเข้าหน้างานค้างอัตโนมัติ พร้อม **assignee คนเดิม** (ดู §8)
> - **ยอดชดเชยเป็น 0**: เดือนที่ 1–3 ผู้ใช้กด "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" (เดินต่อ) · เดือนที่ 4 กด "หยุดชดเชยประกันรายได้" — เป็นกติกาการใช้งาน (ไม่ enforce ใน engine)
> - ผู้รักษาการ (acting) ตั้งเป็นผู้อนุมัติไม่ได้ — ระบบยึดตำแหน่งจริงจาก HR Connect

### 6.3 `workflow/transitions.ts` (ประกาศเป็น data — unit test ครบทุก branch)

```ts
// วงเงิน SDD GI 24/02/2026: gm_amount_limit=50000 · avp_amount_limit=300000
export type Amount = 'LTE_GM' | 'GM_TO_AVP' | 'OVER_AVP';   // ≤50,000 · 50,001–300,000 · >300,000
export interface Transition {
  section: string;                                // section ปัจจุบัน
  result: string;                                 // payload result ไทย verbatim 6-enum
  amount?: Amount;                                // เฉพาะ section 02 + result เห็นควรชดเชย
  next: string | 'END';                           // section ถัดไป หรือจบ (END → status_code 99)
  resultCategory: 'APPROVE' | 'REJECT' | 'PENDING';
  backFlow?: boolean;                             // true → ส่ง EM-03 แทน EM-01
  commentRequired?: boolean;                      // ไม่ชดเชย/หยุด → comment บังคับ
}

export const TRANSITIONS: Transition[] = [
  { section: '06', result: 'เห็นควรไม่ชดเชย',              next: 'END', resultCategory: 'REJECT',  commentRequired: true },  // SDD GI: เดือนถัดไปตั้งงาน assignee เดิม (§8)
  { section: '06', result: 'หยุดชดเชยประกันรายได้',         next: 'END', resultCategory: 'REJECT',  commentRequired: true },
  { section: '06', result: 'ส่งหน่วยงานส่งเสริมธุรกิจ SBP',  next: '01',  resultCategory: 'PENDING' },  // SDD GI: เปลี่ยนชื่อ enum
  { section: '06', result: 'ส่งเจ้าหน้าที่ SBP DSA',        next: '08',  resultCategory: 'PENDING' },
  { section: '08', result: 'คำนวณเงินชดเชยเรียบร้อย',       next: '01',  resultCategory: 'PENDING' },
  { section: '08', result: 'ส่งกลับ',                       next: '06',  resultCategory: 'PENDING', backFlow: true },
  { section: '01', result: 'เห็นควรชดเชย',                 next: '02',  resultCategory: 'PENDING' },
  { section: '01', result: 'เห็นควรไม่ชดเชย',              next: 'END', resultCategory: 'REJECT',  commentRequired: true },  // SDD GI: จบทันที (เดิมตีกลับ 06)
  { section: '01', result: 'ส่งกลับ',                       next: '06',  resultCategory: 'PENDING', backFlow: true },
  { section: '02', result: 'เห็นควรชดเชย',   amount: 'LTE_GM',    next: 'END', resultCategory: 'APPROVE' },  // ≤50,000 จบที่ GM
  { section: '02', result: 'เห็นควรชดเชย',   amount: 'GM_TO_AVP', next: '03',  resultCategory: 'PENDING' },  // 50,001–300,000 → AVP
  // OVER_AVP (>300,000): ไม่มีแถว — SDD ไม่ระบุเส้นทาง (รอ confirm) → findTransition throw
  { section: '02', result: 'เห็นควรไม่ชดเชย',              next: 'END', resultCategory: 'REJECT',  commentRequired: true },  // SDD GI: จบทันทีทุกวงเงิน (เดิมตีกลับ/ผ่าน AVP)
  { section: '02', result: 'ส่งกลับ',                       next: '01',  resultCategory: 'PENDING', backFlow: true },
  { section: '03', result: 'เห็นควรชดเชย',                 next: 'END', resultCategory: 'APPROVE' },  // วงเงิน AVP 300,000/รายการ
  { section: '03', result: 'เห็นควรไม่ชดเชย',              next: '06',  resultCategory: 'PENDING', backFlow: true, commentRequired: true },  // คงเดิม — SDD GI ไม่ระบุ (รอ confirm)
  { section: '03', result: 'ส่งกลับ',                       next: '02',  resultCategory: 'PENDING', backFlow: true },
];

export function findTransition(section: string, result: string, amountFlag?: Amount): Transition {
  const t = TRANSITIONS.find(x => x.section === section && x.result === result
    && (x.amount === undefined || x.amount === amountFlag));
  if (!t) throw new AppError('VALIDATION', MSG.UNKNOWN_RESULT, 400);   // รวมเคส OVER_AVP รอ confirm
  return t;
}
```

## 7. โค้ดตัวอย่าง core (implement ตามนี้ — ปรับได้เฉพาะรายละเอียดไม่ใช่พฤติกรรม)

### 7.1 `config/env.validation.ts` — validate ทุกตัวแปร fail fast (ConfigModule + class-validator หรือ zod ก็ได้)

```ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  BFF_API_KEY: z.string().min(32),                // x-api-key ที่ BFF ระบบเดิมใช้เรียก SBPGI (ไม่มี JWT_* — auth ใช้ระบบเดิม)
  SERVICE_TOKEN: z.string().min(32),
  API_KEY_STA: z.string().min(32),
  CORS_ORIGINS: z.string(),                       // comma-separated
  SMTP_HOST: z.string(), SMTP_PORT: z.coerce.number(),
  SMTP_USER: z.string().optional(), SMTP_PASS: z.string().optional(),
  SMTP_FROM: z.string().email(),
  SFTP_QSSI_HOST: z.string(), SFTP_QSSI_USER: z.string(), SFTP_QSSI_KEY: z.string(),
  SFTP_STA_HOST: z.string(),  SFTP_STA_USER: z.string(),  SFTP_STA_KEY: z.string(),
  ALLMAP_MSSQL_URL: z.string(),
  MIS_IN_DIR: z.string(), MIS_OUT_DIR: z.string(),
  STORAGE_DIR: z.string().default('./storage'),
  LOG_LEVEL: z.string().default('info'),
});

const parsed = envSchema.safeParse(process.env);
if (!parsed.success) {                            // fail fast — บอกตัวแปรที่ขาดแล้วตายทันที
  console.error('ENV validation failed:', parsed.error.flatten().fieldErrors);
  process.exit(1);
}
export const env = parsed.data;
```

### 7.2 `common/errors.ts` + `common/filters/http-exception.filter.ts`

```ts
export class AppError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  catch(err: unknown, host: ArgumentsHost) {
  if (err instanceof AppError)
    return res.status(err.status).json({ code: err.code, message: err.message });
  if (err instanceof ZodError)
    return res.status(400).json({ code: 'VALIDATION', message: err.issues[0]?.message ?? MSG.VALIDATION });
  req.log.error({ err }, 'unhandled');            // log เต็ม — ไม่ leak stack ออก response
  return res.status(500).json({ code: 'INTERNAL', message: MSG.INTERNAL });
}
```

### 7.3 `common/guards/api-key.guard.ts` + `permission.guard.ts` — **ไม่มี JWT login ใน SBPGI** (ตัดสินใจ 2026-08-05)

SBPGI รับ user context จาก BFF ระบบเดิมผ่าน header แบบเดียวกับ backend อื่นของ SBP (store-backend guard: เทียบ `x-api-key` ตรง ๆ · user อ่านจาก header ที่ BFF แนบ):

```ts
export function userContext(req: Request, _res: Response, next: NextFunction) {
  // 1) BFF ยืนยันตัวเองด้วย x-api-key — เทียบ constant-time กับ env.BFF_API_KEY
  const key = req.headers['x-api-key'];
  if (!key || !timingSafeEqualStr(String(key), env.BFF_API_KEY))
    throw new AppError('AUTH_401', MSG.AUTH_REQUIRED, 401);
  // 2) user context ที่ BFF แนบมา (login จริงอยู่ Cognito ฝั่ง BFF)
  const userId = req.headers['x-user-id'];
  if (!userId) throw new AppError('AUTH_401', MSG.AUTH_REQUIRED, 401);
  req.user = {
    employeeId: String(userId),
    groupId: String(req.headers['x-user-group-id'] ?? ''),
    permissions: parsePermissions(req.headers['x-user-permissions']),  // สิทธิ์ต่อ URL จาก auth-backend (canView/canManage/canExport/canOther)
    fullName: decodeURIComponent(String(req.headers['x-user-full-name'] ?? '')),
  };
  next();
}

export const requirePermission = (check: (u: UserContext) => boolean) =>
  (req: Request, _res: Response, next: NextFunction) => {
    if (!check(req.user!)) throw new AppError('FORBIDDEN', MSG.FORBIDDEN, 403);
    next();
  };
// serviceToken.ts / apiKey.ts: เทียบ constant-time (crypto.timingSafeEqual) กับ env.SERVICE_TOKEN / env.API_KEY_STA → ผิด 401
// การ resolve section/ผู้ปฏิบัติงานของ user: จาก group+scope ของ auth-backend (ผ่าน x-user-group-id/x-user-permissions)
// + prepared approvers ที่ผูกไว้รายเอกสาร — ไม่มีตาราง roles/operator_assignments ใน SBPGI
```

### 7.4 `lib/docNo.ts` — เลขเอกสาร พ.ศ./xxxxx จองด้วย FOR UPDATE

```ts
/** เรียกภายใน dataSource.transaction เท่านั้น — race-safe ด้วย row lock
 *  ตาราง document_running_numbers = RunningNumber ของ K2 เดิม (เทียบ DB 2026-08-06) */
export async function nextDocNo(manager: EntityManager, date = new Date()): Promise<string> {
  const yearBe = date.getFullYear() + 543;
  await manager.query(
    `INSERT INTO sps_sbpgi.document_running_numbers (year, last_running_no) VALUES ($1, 0)
     ON CONFLICT (year) DO NOTHING`, [yearBe]);
  const [row] = await manager.query(
    `SELECT last_running_no FROM sps_sbpgi.document_running_numbers WHERE year = $1 FOR UPDATE`, [yearBe]);
  const next = Number(row.last_running_no) + 1;
  await manager.query(
    `UPDATE sps_sbpgi.document_running_numbers SET last_running_no = $1 WHERE year = $2`, [next, yearBe]);
  return `${yearBe}/${String(next).padStart(5, '0')}`;   // เช่น "2026/00185"
}
// test: Promise.all ยิง 20 ครั้งพร้อมกัน → 20 เลขไม่ซ้ำ ต่อเนื่อง
```

### 7.5 `workflow/engine.ts` — applyAction (transaction เต็มของ POST /documents/{docNo}/actions)

```ts
export async function applyAction(docNo: string, user: UserContext,
    input: { result?: string; comment?: string }) {
  // 1) validate ก่อนเข้า transaction
  if (!input.result)
    throw new BadRequestException(
      'ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ');      // verbatim SRS

  const result = await this.dataSource.transaction(async manager => {
    const doc = await manager.getRepository(CompensationDocument).findOne({ where: { docNo } });
    if (!doc) throw new NotFoundException(MSG.DOC_NOT_FOUND);
    if (doc.statusCode === '99') throw new ConflictException(MSG.DOC_ALREADY_DONE);

    const mySection = await sectionOfUser(manager, user);      // map group/scope (auth-backend) + prepared approver → section
    if (mySection !== doc.currentSectionCode)
      throw new AppError('FORBIDDEN', MSG.NOT_YOUR_SECTION, 403);

    // 2) lookup transition (วงเงินจาก system_configs — ห้าม hardcode · SDD GI 24/02/2026)
    const gmLimit  = await getConfigNumber(tx, 'workflow.gm_amount_limit');   // 50000
    const avpLimit = await getConfigNumber(tx, 'workflow.avp_amount_limit');  // 300000
    const amt = Number(doc.compensationAmount ?? 0);
    const amountFlag: Amount = amt <= gmLimit ? 'LTE_GM' : amt <= avpLimit ? 'GM_TO_AVP' : 'OVER_AVP';
    const t = findTransition(doc.currentSectionCode!, input.result, amountFlag);
    // OVER_AVP + เห็นควรชดเชยที่ 02 → ไม่มี transition (SDD รอ confirm) → findTransition throw
    if (t.commentRequired && !input.comment?.trim())
      throw new AppError('VALIDATION', MSG.COMMENT_REQUIRED, 400);

    // 3) update เอกสาร + ปิด/เปิด task + log — atomic (status_code = section คู่ · END = '99')
    const done = t.next === 'END';
    await tx.compensationDocument.update({ where: { docNo }, data: {
      statusCode: done ? '99' : t.next,
      currentSectionCode: done ? null : t.next,
    }});
    await tx.workflowTask.updateMany({
      where: { instance: { docNo }, status: 'OPEN' },
      data: { status: 'CLOSED', closedAt: new Date() },
    });
    if (done) {
      await tx.workflowInstance.update({ where: { docNo },
        data: { status: 'COMPLETED', completedAt: new Date() } });
    } else {
      const inst = await tx.workflowInstance.findUniqueOrThrow({ where: { docNo } });
      await tx.workflowTask.create({ data: { instanceId: inst.instanceId, sectionCode: t.next } });
    }
    await tx.considerationLog.create({ data: {
      docNo, sectionCode: doc.currentSectionCode!, result: input.result!,
      detail: input.comment, resultCategory: t.resultCategory, considerBy: user.employeeId,
    }});
    return { doc, transition: t, done };
  });

  // 4) อีเมล — นอก transaction เสมอ (คิว in-memory + retry 3 ครั้ง)
  const em = result.done ? 'EM-02' : result.transition.backFlow ? 'EM-03' : 'EM-01';
  notificationQueue.enqueue({ template: em, docNo, statusCode: result.doc.statusCode });
  return result;
}
```

### 7.6 `workflow/genFlowGate.ts` — 6 เกณฑ์ (POST /workflows/instances)

```ts
const BRANCH_TYPES = ['FAM', 'FB1', 'FC1', 'FB2', 'FVB', 'FVC'];

export function checkGenFlowGate(row: FgiImpactStoreView):
    { pass: boolean; status: 'W' | 'Y' | 'N'; reason?: string } {
  if (row.workflowGenerationStatus === 'Y') return { pass: true, status: 'Y', reason: 'opened already' };
  if (row.workflowGenerationStatus !== 'W') return { pass: false, status: 'W', reason: 'เกณฑ์ 1: workflow_generation_status ≠ W' };
  if (!BRANCH_TYPES.includes(row.branchType)) return { pass: false, status: 'N', reason: 'เกณฑ์ 2: branch type ไม่อยู่ใน FAM/FB1/FC1/FB2/FVB/FVC' };
  if (!row.dvCode)                             return { pass: false, status: 'W', reason: 'เกณฑ์ 3: DV ว่าง' };
  if (row.impactedJuristic === row.newJuristic) return { pass: false, status: 'W', reason: 'เกณฑ์ 4: juristic เดียวกัน' };
  if (row.growthRateDiff === null || row.growthRateDiff > -10)
                                               return { pass: false, status: 'W', reason: 'เกณฑ์ 5: growth_rate_diff > −10 หรือ NULL' };
  if (!['Y', 'N'].includes(row.salesStatus))   return { pass: false, status: 'W', reason: 'เกณฑ์ 6: sales_status ∉ {Y,N}' };
  return { pass: true, status: 'Y' };
}
// POST /workflows/instances request = {impactProcessId, sourceJobNo:'8b', requestId}
// ผ่านครบ → transaction เดียว: ใช้ document ที่ Job 8 สร้างแล้ว + instance + task 06
//            + ตั้ง fgi_impact_processes.workflow_generation_status = 'Y'
// branch type นอกเซ็ต → ตั้ง 'N' ถาวรแล้วตอบ workflowGenerationStatus='N'
// ข้อมูลยังไม่พร้อม → คง 'W' และตอบ 422/reason เพื่อให้ Job 8b rerun ได้
```

### 7.7 `batch/runner.ts` — lock กันรันซ้อน

```ts
export async function runJob(jobNo: string, trigger: 'CRON' | 'MANUAL', by?: string) {
  const run = await this.dataSource.transaction(async manager => {
    const repo = manager.getRepository(JobRunHistory);
    const running = await repo.findOne({ where: { jobNo, status: JobRunStatus.RUNNING } });
    if (running) throw new ConflictException(MSG.JOB_ALREADY_RUNNING);          // กันรันซ้อน
    return repo.save(repo.create({ jobNo, status: JobRunStatus.RUNNING, trigger, startedBy: by }));
  });
  const runs = this.dataSource.getRepository(JobRunHistory);
  try {
    const stats = await JOB_IMPLS[jobNo]();       // { rows, files, note }
    await runs.update({ runId: run.runId },
      { status: JobRunStatus.SUCCESS, finishedAt: new Date(), ...stats });
  } catch (err) {
    await runs.update({ runId: run.runId },
      { status: JobRunStatus.ERROR, finishedAt: new Date(), errorMessage: String(err) });
    notificationQueue.enqueue({ template: 'EM-07', jobNo, error: String(err) });
    throw err;
  }
}
// boot recovery: แถว RUNNING ค้างจาก process ตาย → mark ERROR ตอน start (ไม่งั้น lock ค้างถาวร)
```

### 7.8 `lib/audit.ts` — writeAudit (ใช้ร่วมทุก master mutation ใน transaction เดียวกัน)

```ts
export async function writeAudit(manager: EntityManager, p: {
  tableName: string; refKey: string;
  actionType: 'CREATE' | 'UPDATE' | 'DELETE' | 'RESET';
  oldValue?: unknown; newValue?: unknown;
  reason: string;                                  // บังคับ — controller ตรวจ 400 ก่อนถึงตรงนี้
  updatedBy: string;                               // จาก user-context header ที่ BFF ส่งมา
}) {
  await manager.getRepository(AuditLog).save({
    tableName: p.tableName, refKey: p.refKey, actionType: p.actionType,
    oldValue: p.oldValue ? JSON.stringify(p.oldValue) : null,
    newValue: p.newValue ? JSON.stringify(p.newValue) : null,
    reason: p.reason, updatedBy: p.updatedBy,
  }});
}
```

## 8. Batch Jobs — spec ต่อ job (Jobs 7/8/9 ตัดทิ้ง — ไม่ต้องสร้าง)

ทุก job รันผ่าน `runner.ts` (lock + `job_run_histories` + EM-07 เมื่อ error) · cron อ่านจาก `job_configs` (แก้ได้ผ่าน `PUT /jobs/{jobNo}/params`) · เวลาอ้างอิงเอกสาร Batch v4.0

| Job | ชื่อ/หน้าที่ | Cron เดิม | Input → Output | ตารางที่แตะ | Error handling |
|---|---|---|---|---|---|
| 1 | นำเข้าคะแนน QSSI | รายเดือน | SFTP 4 ไฟล์ `mrs*` → upsert คะแนน 6 หมวด (8,9,12,1,10,16) | W: **`fcs_qssi_score`** (เอกพจน์ · **มีอยู่จริงแล้วใน `sps_store` 23,958,780 แถว — ห้ามสร้างใหม่ ให้ reuse**) · UK กันซ้ำ **ยังไม่มีในตารางเดิม** | ไฟล์ขาดหมวด → fail ทั้งรอบ + EM-07 · งวด DB = เดือนก่อนหน้า (off-by-one ตั้งใจ) |
| 2 | นำเข้าร้านกระทบจาก ALLMAP | รายวัน | SELECT จาก SQL Server (read-only) → แถวร้านกระทบ | W: `fgi_impact_stores`, `fgi_impact_processes` | connection fail → retry 3 → EM-07 |
| 3 | นำเข้าคู่แข่งจาก ALLMAP | รายวัน | SELECT คู่แข่งรัศมี → แถว `data_source='ALM'` งวดล่าสุดต่อร้าน | W: `fgi_impact_competitors` | เหมือน Job 2 |
| 4 | export ยอดขายไป MIS | 16:00 วันที่ 7–16 | รอบที่ `action_status='W'` → ไฟล์ `AMS06001O_YYYYMMDD` | R: sales pipeline · W: `interface_transactions`, สถานะ W→P | **P0: transaction/outbox — เขียนไฟล์สำเร็จก่อนค่อย commit W→P** · fail = rollback ทั้งก้อน |
| 5 | import ยอดขายจาก MIS | 16:30 วันที่ 7–16 | ไฟล์ `AMS06001I_` → ยอดขายรายวัน 4×15 | W: `sales_transactions`, `fgi_impact_sales_summaries` | ค่า NULL → ตั้งสถานะ "รอตรวจสอบ" (**ห้าม auto-accept** — flag `batch.job5_null_policy` ใน system_configs รอ business sign-off) |
| 6 | export ผลชดเชยไป STA | 17:00 ทุกวัน | `compensation_histories` งวดพร้อมส่ง → ไฟล์ `FRBC0001_` | R: histories · W: `interface_transactions` (sta_status I/C/A/N/S/Z) | เขียนไฟล์ fail → ไม่อัปเดตสถานะ + EM-07 |
| 8b (แทน) | เปิด workflow อัตโนมัติ | 17:30 วันที่ 7–31 | รอบผ่าน Gen Flow Gate → เรียก `workflows.service.openInstance()` **ภายใน process** (ไม่ผ่าน HTTP) | W: documents/instances/tasks | สรุปผลราย DV → EM-06 · รายการไม่ผ่าน gate = log เหตุผล ไม่ fail รอบ |
| 10 | watchdog ACK จาก STA | 07:00 ทุกวัน | หา `interface_transactions` ที่ส่งแล้วไม่มี ACK ≥ 1 วัน | R: interface_transactions | พบ → EM-08 ถึงผู้ดูแล (ไม่ใช่ error ของ job) |

> **งานต่อเนื่องตาม SDD GI (24/02/2026):** เอกสารที่จบด้วย "เห็นควรไม่ชดเชย" ที่ขั้น 06 — รอบเดือนถัดไประบบต้องดึงร้านนั้นเข้าหน้างานค้างอัตโนมัติพร้อม **assignee คนเดิม** (เจ้าหน้าที่ SBP DSA): implement เป็น logic ในรอบ Job 8b (หรือ job ภายในของ Workflow Engine) ที่สร้างเอกสาร/task เดือนถัดไปโดย copy `assignee_employee_id` จาก task เดิม · กรณีพนักงานลาออกยังต้องเปิด SR แก้ชื่อผู้ดำเนินการ (นอกระบบ)

## 9. Notification — mapping event → template → ผู้รับ

Renderer แทนตัวแปร `{{var}}` จาก context · ผู้รับ EM-01–03 มาจาก `status_email_rules` (rules = ผู้รับ · templates = เนื้อหา) · ส่งผ่านคิว in-memory + retry 3 ครั้ง · fail สุดท้าย = log ERROR (ไม่ block ธุรกรรม)

| Event (จุด hook ใน service) | Template | TO / CC | ตัวแปร merge หลัก |
|---|---|---|---|
| applyAction → สถานะเปลี่ยน (ไป section ถัดไป) | EM-01 | ผู้ดำเนินการ step ถัดไป (to_section_code) | docNo, storeName, statusName, actorName, dueInfo |
| applyAction → จบ workflow (ไม่ชดเชย/หยุด/อนุมัติจบ) | EM-02 | ผู้เกี่ยวข้องทุก section ที่เคยรับเอกสาร | docNo, finalResult, totalAmount |
| applyAction → ส่งกลับ (back-flow) | EM-03 | ผู้ถูกส่งกลับหา · CC ผู้ส่งกลับ | docNo, fromSection, toSection, comment |
| cron จันทร์ 10:00 (แก้ cron ได้) | EM-04 | ผู้มีงานค้าง (workflow_tasks เปิดค้าง) | taskCount, oldestDocNo, daysPending |
| cron รายวัน — task ค้าง 30/45/60 วัน | EM-05 | หัวหน้า section (30/45) · GM OPT (60) | docNo, daysPending, assigneeName |
| Job 8b จบรอบ | EM-06 | DV/GM user | dvCode, openedCount, skippedCount |
| job รอบใด error | EM-07 | ผู้ดูแลระบบ (config ต่อ job ใน job_configs) | jobNo, jobName, errorSummary, runId |
| Job 10 พบ ACK ค้าง | EM-08 | ผู้ดูแลระบบ | fileName, sentDate, daysWaiting |

## 10. Seed data (`src/database/seed.ts` — idempotent ด้วย upsert ทั้งหมด)

| ตาราง | แถว | รายละเอียด |
|---|---|---|
| ~~roles / menus / menu_permissions~~ | — | **ตัดออก — ใช้ระบบเดิม** (auth-backend groups/menus · ตัดสินใจ 2026-08-05) — ไม่ seed |
| workflow_sections | 7 (5 active + 04/05 `is_active=false`) | 04/05 เก็บไว้อ้างอิงประวัติเท่านั้น |
| document_statuses | 6 | string ตรง workflow.md ทุกตัวอักษร · status_code 06/08/01/02/03/99 |
| system_configs | ~15 | radius 1/2 กม. · `workflow.gm_amount_limit`=50000 + `workflow.avp_amount_limit`=300000 (SDD GI — แทน threshold 100000 เดิม) · เกณฑ์ 60 วัน · −10 (ทั้งหมด is_editable=false) + cache TTL, cron ต่าง ๆ |
| email_templates + status_email_rules | 8 + 6 | EM-01–08 (subject/body default ตาม email-template.html) |
| competitors / external_factors | 24 / ~10 | ตาม master ใน prototype |
| employees | ~15 | master พนักงาน (dev) — ~~user_accounts~~ ตัดออก: ตัวตนมาจาก BFF/Cognito · dev จำลองด้วย header `x-user-id` ฯลฯ |
| ~~operator_assignments~~ | — | **ตัดออก — ใช้ระบบเดิม** (group+scope ของ auth-backend + prepared approvers) — ไม่ seed |
| stores / impacted_stores | ~30 / ~15 | รหัส 5 หลัก มีเลขศูนย์นำหน้า (ทดสอบ typed FK) |
| job_configs | 11 | cron ตาม Batch v4.0 · Jobs 7/8/9 `enabled=false` + note "ตัดทิ้ง — คงแถวเพื่อ traceability" |
| เอกสาร demo | ~10 | ครบ 6 สถานะ · มีเคส ≤50,000 (จบที่ 02) · 50,001–300,000 (ผ่าน 03) · เคสจบด้วยหยุด/ไม่เห็นควรชดเชยแล้วเปิดเรื่องใหม่ (ทดสอบ partial unique — SDD GI) · แถว <60 วัน · เลขเริ่ม 2026/00181 ให้เลขถัดไปตรง prototype (2026/00187) |

## 11. Environment variables + docker-compose

| ตัวแปร | ตัวอย่าง (dev) | ใช้ทำอะไร |
|---|---|---|
| `DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA` | localhost / 5432 / sbpgi / sbpgi / sbpgi / sps_sbpgi | TypeORM DataSource (ชื่อตัวแปรตาม store-backend เดิม) |
| `DB_SLAVE_HOSTS/PORTS/USERS/PASSWORDS` | — | read-replica routing (optional · แบบระบบเดิม) |
| `PORT` / `NODE_ENV` | 3000 / development | server |
| `BFF_API_KEY` (≥32 ตัว) | random 64 hex | ตรวจ `x-api-key` จาก BFF ระบบเดิม (แทน `JWT_*` เดิม — ตัดออก ใช้ auth ระบบเดิม) |
| `SERVICE_TOKEN` | random 64 hex | Job 8b → workflows |
| `STA_API_KEY` | random 64 hex | POST /interfaces/sta/ack |
| `SMTP_HOST/PORT/USER/PASS/FROM` | localhost/1025 (mailpit) | notification |
| `SFTP_QSSI_*` / `SFTP_STA_*` (HOST/PORT/USER/KEY_PATH/DIR) | — | Jobs 1/6/10 |
| `ALLMAP_MSSQL_URL` | — | Jobs 2–3 (read-only) |
| `STORAGE_DIR` | ./storage | attachments/exports |
| `CORS_ORIGINS` | http://localhost:5173 | cors whitelist |

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment: { POSTGRES_USER: sbpgi, POSTGRES_PASSWORD: sbpgi, POSTGRES_DB: sbpgi }
    ports: ["5432:5432"]
    volumes: [dbdata:/var/lib/postgresql/data]
  mail:
    image: axllent/mailpit          # ทดสอบอีเมล dev
    ports: ["1025:1025", "8025:8025"]
  api:
    build: .
    env_file: .env.docker
    depends_on: [db, mail]
    ports: ["3000:3000"]
    volumes: [./storage:/app/storage]
volumes: { dbdata: {} }
```

Dockerfile: multi-stage `node:20-alpine` (deps → `nest build` → runtime คัดเฉพาะ dist+node_modules production · รันเป็น user `node` · HEALTHCHECK `GET /api/health`) · CMD `node dist/main.js` · migrate ตอน deploy ด้วย `typeorm migration:run` (ไม่ auto ใน CMD)

## 12. Best practices สากลที่บังคับใช้

- **12-factor**: config ผ่าน env (ConfigModule validate fail fast) · log stdout JSON (pino + request id + redact token/password) · stateless (storage เป็น volume)
- **Security**: helmet · cors whitelist · ตรวจ `x-api-key`/service token แบบ constant-time (ไม่มี login/bcrypt ใน SBPGI — auth อยู่ Cognito/BFF ระบบเดิม) · TypeORM parameterized เท่านั้น ห้ามต่อ string SQL · ไม่ leak stack ใน 500 (ใช้ exception filter แบบ store-backend)
- **Graceful shutdown**: `enableShutdownHooks()` — SIGTERM/SIGINT → หยุดรับ request → รอ job ที่กำลังรัน → `dataSource.destroy()` · `GET /api/health` (liveness) + `GET /readyz` (เช็ค DB)
- **Transaction boundary ที่ service** — `dataSource.transaction(async manager => …)` ส่ง `manager` ลง repo · side-effect ภายนอก (อีเมล/ไฟล์) นอก transaction เสมอ
- **Testing pyramid**: unit service (mock repo — เน้น `workflow/transitions` ครบทุก branch) → integration supertest + postgres จริง → golden-file ต่อ interface (encoding, วันที่ พ.ศ., ชื่อ first+last) · coverage `workflow/` ≥ 90%
- **Migration ผ่าน TypeORM migration เท่านั้น** (ห้าม `synchronize: true`) · seed idempotent
- **API versioning**: ทุกอย่างใต้ `/api/v1` — breaking change = `/api/v2`

## 13. Definition of Done (ทั้งโปรเจกต์ BE)

1. endpoint ครบ **44/44** ตรง `api.md` (script เทียบ route tableรายงาน matched) — abnormal-stores ยกเลิกถาวรแล้ว · เส้น Auth/RBAC/operators 18 เส้นต้อง**ไม่มี** (ตัดออก — ใช้ระบบเดิม)
2. integration test เดิน workflow จริงผ่านทุก scenario ใน checklist-be.md Phase 3 (≤50,000 จบ 02 · 50,001–300,000 ผ่าน 03 · >300,000 → reject รอ confirm · ไม่ชดเชยที่ 01/02 จบทันที · back-flow · เอกสารจบแล้ว action ซ้ำ → 409 · เปิดเรื่องใหม่หลังหยุด/ไม่เห็นควรชดเชย ต้องไม่ 409)
3. ข้อความ error ไทยทุกตัวรวมศูนย์ `lib/messages.ts` และตรง verbatim SRS
4. batch ทุก job รันผ่าน `POST /jobs/{no}/run` สำเร็จบน fixture · Job 4 fail กลางทาง = rollback สถานะไม่ค้าง P
5. seed แล้ว FE (plan-fe.md) ใช้งานได้ครบทุกหน้า end-to-end ผ่าน `docker compose up`
6. CI เขียว: lint / tsc / test / build · ไม่มี secret ใน repo/DB/log
