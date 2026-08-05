# srm-sps-spsap-store-backend — เอกสารวิเคราะห์ codebase ฉบับละเอียด

> วิเคราะห์จาก source code จริง ณ วันที่ 2026-08-05 (branch `main`, commit ล่าสุด `c0de17b5 "Fix PDF and Modify Date"`)
> ตำแหน่งโปรเจกต์: `/Users/bank_mac/gosoft/java/SBP/sbp-prototype/SBP/srm-sps-spsap-store-backend`
> Repo จริง: `git@bitbucket.org:gosoft-thailand/srm-sps-spsap-store-backend.git`

---

## 1. ภาพรวม

### 1.1 โปรเจกต์นี้คืออะไร

**Store Backend** ของแพลตฟอร์ม SBP (Store Business Partner) ของ CP All / 7-Eleven — เป็น NestJS API service ตัวหลักที่ให้บริการข้อมูล "ร้าน SBP" ทั้งหมด ได้แก่:

- **Statement** — ใบแจ้งยอด/งบการเงิน/เอกสารการเงินของร้าน SBP ทุกสายธุรกิจ (SBP ปกติ, PTT, Sub-Area, Bellinee's, กัมพูชา, ลาว) รวม interface รับไฟล์จาก SAP / STA / OAS
- **FES (Franchise Evaluation System)** — ระบบประเมินผลร้าน SBP ครบวงจร: สร้างรอบประเมิน → แจ้งผู้ประเมิน → ให้คะแนน → ตรวจสอบ (audit) → อนุมัติ → สรุปเกรด → ออกใบแจ้งเกรด PDF → การแข่งขัน Division/รางวัล
- **FCS** — ข้อมูลยอดขายรายเดือน (`fcs_monthly_sales`), ต้นทุนตรวจนับ (`fcs_audit_costs`), คะแนน QSSI (`fcs_qssi_score`) — ชุดข้อมูลเดียวกับที่ระบบประกันรายได้ (FGI/FCS legacy ใน `fcsJar/`) ใช้
- **หนังสือขอความร่วมมือ (Cooperation Request)** — เอกสารขอความร่วมมือถึงร้าน พร้อม approval workflow ภายใน
- **Generic Upload Framework** — ระบบนำเข้าไฟล์กลางที่ config จาก DB
- **Master data** — ร้าน, โครงสร้างองค์กร, จังหวัด/อำเภอ/ตำบล, common code, business user

### 1.2 ตำแหน่งในสถาปัตยกรรม SBP

โฟลเดอร์แม่ (`sbp-prototype/SBP/`) มี 3 repo พี่น้อง ชี้ว่าสถาปัตยกรรมเป็น 3 ชั้น:

```
srm-sps-spsap-web-frontend  (Next.js)  →  srm-sps-spsap-sbp-bff  (NestJS BFF)  →  srm-sps-spsap-store-backend  (โปรเจกต์นี้, port 3004)
                                                                                →  authorization-backend (port 3003 — อ้างใน env, ไม่อยู่ในโฟลเดอร์นี้)
```

- ทุก request จาก BFF เข้ามาด้วย header `x-api-key` (ค่า `X_API_KEY`) หรือ Bearer JWT — โปรเจกต์นี้**ไม่ทำ authentication เอง** (login จริงอยู่ที่ AWS Cognito ฝั่ง BFF/authorization-backend ตาม env `AUTH_*`)
- โปรเจกต์นี้คือ **"ระบบปัจจุบัน" (To-Be ที่กำลังสร้าง) ที่ prototype ระบบประกันรายได้ K2/SBPGI จะเข้าไปเป็นส่วนหนึ่ง** — เห็นได้จากตาราง `fcs_*`, `fr_store_insure` (เงินช่วยเหลือประกันรายได้), workflow engine ภายใน (`@srm/glb-workflow`) ที่ตรงกับ design ใน `plan-database.html` / `workflow.md` ของ prototype

### 1.3 ความหมายคำย่อ SRM / SPS / SPSAP

**ไม่พบคำนิยามตรง ๆ ใน code หรือเอกสารใด ๆ ในโปรเจกต์** — ปรากฏเป็น prefix ของ resource ทั้งหมดเท่านั้น:
- ชื่อ repo/pipeline: `srm-sps-spsap-*` (org `gosoft-thailand` บน Bitbucket)
- AWS: RDS `srm-sps-spsap-postgres-instance-dev`, S3 `srm-sps-data-s3-dev`, CodeArtifact `srm-sps-spsap-ca-dm-…`
- npm scope: `@srm` (glb-workflow), `@gosoft-sbp` (email-lib)
- path legacy ใน config: `D:/appshare/SPS/FML/interface_data/out/`
- exchange RabbitMQ: `sps.store.master`

จากบริบท SBP = Store Business Partner (ยืนยันจากเอกสาร SRS ใน workspace); SPS น่าจะเป็นชื่อกลุ่มระบบ Store Partner System (มี schema DB ชื่อ `sps_store`) — แต่เป็นการอนุมานจากชื่อ ไม่ใช่นิยามใน code

### 1.4 สรุป README.md

`README.md` เป็น template มาตรฐานของ NestJS starter เกือบทั้งไฟล์ ส่วนที่เขียนเพิ่มเองมี 2 จุด:

1. **EJ report integration** — ให้ config ตัวแปร EJ gateway *เฉพาะใน store-backend เท่านั้น* ห้าม expose ไป frontend/BFF:
   `EJ_API_URL`, `EJ_API_KEY_NAME=x-api-key`, `EJ_API_KEY`, `EJ_API_TIMEOUT=120000`
2. **Project Structure (ภาษาไทย)** — อธิบายโครง `src/common (constant/dto/exception/middleware/utils)`, `src/config`, `src/database` (เขียนว่าเป็น Prisma module/service — **ของจริงใช้ TypeORM แล้ว**, Prisma เหลือแค่ script/dependency ค้าง), `src/modules`, `app.module.ts`, `main.ts`

### 1.5 สรุป WORKFLOW_GUIDE.md (สำคัญ — คู่มือ workflow engine)

เป็นคู่มือการใช้ **library `@srm/glb-workflow`** (workflow/approval engine แบบ **State Machine Pattern** ที่ Gosoft เขียนเอง แจกผ่าน AWS CodeArtifact) — ใจความ:

**Flow มาตรฐาน 4 ขั้น**: (1) Initialize Workflow — สร้าง workflow transaction ผูกกับเอกสาร → (2) Trigger Event — ส่ง event (SUBMIT/APPROVE/REJECT) เพื่อเปลี่ยน state → (3) Get Transaction — อ่าน state ปัจจุบัน → (4) Get History — อ่าน timeline การเปลี่ยน state

**Use cases 7 ตัวของ library**:

| Use case | ทำอะไร | ใช้เมื่อ |
|---|---|---|
| `InitializeWorkflow` | สร้าง workflow transaction ใหม่ `{versionId, userId, referenceId}` → คืน transactionId | สร้างเอกสารใหม่ที่ต้องอนุมัติ |
| `TriggerEventUseCase` | เปลี่ยน state `{versionId, referenceId, event, eventParam, remark, userId}` | user กด submit/approve/reject |
| `GetTransactionUseCase` | อ่าน `{currentState, createdBy, ...}` | แสดงสถานะปัจจุบัน |
| `GetHistoryUseCase` | อ่าน `[{fromState, toState, event, userId, remark, timestamp}]` | timeline / audit log |
| `GetPendingFlowUseCase` | รายการเอกสารที่รอ user คนนั้นอนุมัติ | หน้า backlog/inbox |
| `GetPermissionUseCase` | เช็คว่า user ทำ action ได้ไหม | ก่อน render ปุ่ม approve/reject |
| `AddPreparedApproverUseCase` | ผูกผู้อนุมัติล่วงหน้าเป็นลำดับ `[{userId, level}]` | กำหนดสายอนุมัติตอนสร้างเอกสาร |

**Key concepts**: `versionId` = ID ของ workflow definition (เอกสารแต่ละประเภทมี version ต่างกัน) · `referenceId` = เลขเอกสารที่ track (unique ต่อ versionId) · `event` = action (ต้องตรงกับ definition) · `state` = สถานะปัจจุบัน (DRAFT, PENDING_APPROVAL, APPROVED, …)

**Setup ใน NestJS**: import repository implementations จาก `@srm/glb-workflow/typeorm` (`WorkflowTransactionRepositoryImpl`, `WorkflowHistoryRepositoryImpl`, `WorkflowVersionRepositoryImpl`, `TransactionProvider`/UnitOfWork) แล้วห่อ use case ใน service; ตัวอย่างในคู่มือคือระบบขออนุมัติใบลา (SUBMIT → APPROVE level 1 → ดู history)

**หมายเหตุท้ายคู่มือ**: ต้องมีตาราง DB สำหรับ workflow (transaction / history / version), ต้อง config TypeORM entities ให้ถูก, แนะนำใช้ DB transaction

### 1.6 สรุป WORKFLOW_QUICKSTART.md

ฉบับย่อของ GUIDE — code snippet 4 steps (import → initialize → trigger → get status/history) + **ตาราง events มาตรฐาน**:

| Event | คำอธิบาย | ใช้เมื่อ |
|---|---|---|
| `SUBMIT` | ส่งเอกสาร | พนักงานส่งขออนุมัติ |
| `APPROVE` | อนุมัติ | ผู้อนุมัติกดอนุมัติ |
| `REJECT` | ปฏิเสธ | ผู้อนุมัติกดปฏิเสธ |
| `CANCEL` | ยกเลิก | ผู้สร้างยกเลิกเอกสาร |
| `REVISE` | แก้ไข | ส่งกลับให้แก้ไข |

Tips: versionId = ประเภทเอกสาร (เช่น 1=ใบลา 2=ใบเบิก), referenceId ต้อง unique ต่อ versionId, event ต้องตรงกับ workflow definition, remark แสดงใน timeline

---

## 2. Tech Stack

| หมวด | Library (เวอร์ชัน) | ใช้ทำอะไร |
|---|---|---|
| Framework | **NestJS 11** (`@nestjs/common|core|platform-express ^11.0.1`), Express 5, Node 20 (Dockerfile `node:20-alpine3.21`), TypeScript 5.9 target ES2023 | โครง API ทั้งหมด |
| ORM / DB | **TypeORM 0.3.28** + `pg ^8.20` → **PostgreSQL** (AWS RDS, schema `sps_store`) | entity/repository/raw query; มีระบบ read-replica routing เขียนเอง |
| ORM สำรอง (ค้าง) | `@prisma/client ^6.14` + prisma scripts | **ไม่ได้ใช้จริงใน runtime** — เหลือ script `prisma:*` และคำอธิบายใน README |
| Workflow engine | **`@srm/glb-workflow ^1.1.25`** (private CodeArtifact) | State-machine approval workflow (ดูหัวข้อ 8) |
| Email | **`@gosoft-sbp/email-lib ^0.0.9`** (private) + `nodemailer 9.0.1` | ส่งอีเมลตาม template ในตาราง `email_template` + log ลง `email_sent` |
| Message queue | `amqplib ^0.10.9` (**RabbitMQ**) | publish event `sps.store.master` (topic exchange) หลัง import โครงสร้างองค์กร PTT |
| Cloud storage | `@aws-sdk/client-s3 ^3.1071`, `@aws-sdk/credential-providers` | S3 upload/download/move/head (bucket `srm-sps-data-s3-dev`) |
| Excel | **`exceljs ^4.4`** | export รายงานทุกตัว (audit log, sales summary, division ฯลฯ) |
| PDF สร้าง | **`pdfkit ^0.17`** (วาดใบแจ้งเกรดแบบ absolute-coordinate), **`pdf-lib ^1.17` + `@pdf-lib/fontkit`** (merge/watermark/bookmark), **`puppeteer ^24`** (HTML→PDF หนังสือขอความร่วมมือ; ใช้ chromium ของ alpine) | เอกสาร PDF ภาษาไทย (ฟอนต์ Sarabun/TH Sarabun/Angsana ใน `src/assets/fonts`) |
| PDF เข้ารหัส | `@pdfsmaller/pdf-encrypt-lite` | ใส่รหัสผ่าน PDF ส่งผู้ตรวจสอบบัญชี |
| CSV/parsing | `csv-parse`, `csvtojson`, `papaparse`, `chardet`, `iconv-lite` (decode `win874`/`tis-620`) | parse ไฟล์ interface ไทย |
| HTTP client | `axios ^1.15`, `@nestjs/axios`, `https-proxy-agent` | เรียก CM API, EJ API, downstream |
| FTP | `basic-ftp ^5.3.1` | dependency ประกาศไว้ (การใช้งานจริงในโค้ดไม่พบจุดเรียกที่ active) |
| Auth utils | `jsonwebtoken ^9` (decode JWT), `bcryptjs ^3` (เทียบ API key upload) | guards |
| Scheduler | `@nestjs/schedule ^6.0.1` | **ติดตั้งไว้แต่ไม่พบ `@Cron`/`@Interval` ใดในโค้ด** — ไม่มี scheduled job ใน service นี้ |
| อื่น ๆ | `dayjs`, `date-fns`, `lodash`, `effect ^3.20`, `class-validator`/`class-transformer`, `multer 2.2`, `fs-extra`, `fast-xml-builder` | ตามชื่อ |
| Test | Jest 29 + ts-jest, supertest, `fast-check` (property-based), jest-junit | unit (594 ไฟล์ ts ใน src มี spec ~156 ไฟล์) + e2e 2 ไฟล์ (`test/app.e2e-spec.ts`, `test/statement-search.e2e-spec.ts`) |
| Observability | Dynatrace OneAgent (ฝังใน Docker image), custom `MyLogger` | log + APM |

---

## 3. วิธีรัน / สคริปต์ / CI

### 3.1 npm scripts (`package.json` — ชื่อ package ยังเป็น `nest-api-template` v0.0.2)

| Script | ทำอะไร |
|---|---|
| `dev` | `nest start --watch` |
| `build` | `tsc -p tsconfig.build.json` + `node scripts/copy-assets.js` (copy `src/assets` → `dist/assets`) |
| `start` / `start:prod` | `node dist/main.js` (ฟัง `PORT` default 3004) |
| `start:debug` | nest start --debug --watch |
| `lint` / `format` | eslint --fix / prettier |
| `test`, `test:watch`, `test:cov`, `test:debug` | Jest unit tests (rootDir=src, coverage เปิด default) |
| `test:e2e` | Jest ด้วย `test/jest-e2e.json` |
| `test:ci` | โหมด CI: runInBand, jest-junit → `test-reports/`, lcov → `coveragereport/`, `--bail` |
| `typeorm` | ts-node TypeORM CLI |
| `migration:generate` | สร้าง migration อัตโนมัติ → `./src/migrations/AutoMigration` โดยใช้ `./src/data-source.ts` |
| `migration:run` / `migration:revert` | รัน/ย้อน migration ผ่าน data-source.ts |
| `prisma:db:pull`, `prisma:generate`, `prisma:migrate`, `prisma:deploy`, `prisma:studio`, `prisma:seed` | **ชุด Prisma ที่ค้างจาก template** (ไม่มีโฟลเดอร์ `prisma/` ใน repo) |
| `vercel-build` | alias ของ build (ค้างจาก template) |

### 3.2 Dockerfile (multi-stage, ละเอียดน่าสนใจ)

1. **deps** → npm ci ด้วย `.npmrc` (ชี้ CodeArtifact private registry สำหรับ scope `@srm` และ `@gosoft-sbp`) แล้วลบ .npmrc
2. **build** → `npm run build`
3. **runner** (`node:20-alpine3.21`):
   - ฝัง **Dynatrace OneAgent** (`lss67296.live.dynatrace.com/.../oneagent-codemodules-musl:nodejs`) + มี step **patch ws CVE-2026-48779** ใน agent ด้วยการดึง ws 7.5.11 มาทับ
   - `npm ci --omit=dev` แล้ว**ลบ npm/npx ทิ้งทั้งหมด** (ลด attack surface)
   - copy `dist/`, `templates/`, `sql/`, `src/assets/`, `src/modules/uploads/assets/`
   - ติดตั้ง **chromium** + set `PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser`
   - ติดตั้ง**ฟอนต์ไทย**ลง `/usr/share/fonts/thai` + `fc-cache` (ให้ puppeteer render ไทยได้)
   - `HEALTHCHECK` ยิง `GET /api/health`, รันเป็น user `node`, `EXPOSE 3000`

### 3.3 CI — `bitbucket-pipelines.yml`

ทุก pipeline import จาก template repo กลาง `srm-sps-spsap-pipeline-template` ตาม flow 6 ขั้น (comment ไทยในไฟล์):
1. push `feature/*` → security scan
2. PR `feature/*`→`main` → SonarQube scan
3. merge `main` → build container + **sign signature ด้วย AWS profile**
4. PR `main`→`dev` → ตรวจลายเซ็น + deploy **ECS DEV**
5. PR `dev`→`uat` → deploy **UAT** (ให้ tester)
6. PR `uat`→`production` (+ หลักฐาน QC PASS) → deploy **Production**

### 3.4 โฟลเดอร์ `scripts/`

| ไฟล์ | ทำอะไร |
|---|---|
| `copy-assets.js` | copy `src/assets` → `dist/assets` ตอน build (fs-extra) |
| `optimize-audit-search.sql` | ชุด `CREATE INDEX` (partial/composite/expression index) บน `fes_evaluate` + `store_sbp` เพื่อลดเวลา `POST /assessment/audit/search` จาก ~18s เหลือ <800ms (comment ระบุให้รันช่วง low-traffic เพราะไม่ใช้ CONCURRENTLY) |

### 3.5 โฟลเดอร์ `sql/`

| ไฟล์ | ทำอะไร |
|---|---|
| `deploy-sap-statement-expected.sql` | DDL production (idempotent) สร้าง `sap_statement_expected` + `sap_statement_summary_source` — คู่กับ migration ตัวเดียวใน repo |
| `reconcile-sap-statement-summary.sql` | สคริปต์ reconcile หลัง deploy: สร้างแถว `statement_summary` (statement_from='SAP') ที่ขาด + recalculate `sum_record`/`received_record` จากข้อมูล expected ตั้งแต่งวด 202606 |
| `insert-eval-levels.sql` | Template PL/pgSQL insert โครงหัวข้อประเมิน `fes_evallevelone/two/three` ผูกกับ `fes_evaluatedform` ล่าสุด (โครงเดียวกับ `templates/evaluate-template.json`) |
| `evaluate-template.json` | สำเนา template หัวข้อประเมิน (ซ้ำกับใน `templates/`) |
| `Guidelines.html` | เอกสารธุรกิจ **หลักเกณฑ์การแข่งขัน Division** ของร้าน: National Division (0-5 Excellence ต่อเนื่อง) / Division 2 (6-10) / Division 1 (11-15) / Champions Division (16-20) / Premier Division (21+) + วิธีนับคะแนนรายปี (ใช้ 2 เกรดประเมินต่อปีการแข่งขัน) — ใช้กับ module `award-division` / `report-division` |

### 3.6 โฟลเดอร์ `templates/` และ `test_files/`

- `templates/evaluate-template.json` — **โครงแบบฟอร์มประเมินร้านมาตรฐาน 3 ระดับ**: level 1 (4 หมวด: การบริหารงานที่ร้านสาขา 870 คะแนน, การเงินและบัญชี 90, การมีส่วนร่วมนโยบายบริษัท 40, Premium 30), level 2 (8 หมวดย่อย เช่น ผลการดำเนินงาน 540), level 3 (รายข้อ เช่น ยอดขายเฉลี่ย/วัน 120, GP 80, %Audit 40, QSSI รายหมวด, อัตรากำลังคน, หนังสือขอความร่วมมือ -10/ใบ ฯลฯ พร้อม `point_hit` และ `hint` เกณฑ์ให้คะแนนละเอียด) — ถูก `grades.service.insertEvalFromTemplate()` ใช้สร้างหัวข้อประเมินเมื่อสร้างรอบเกรดใหม่
- `templates/import-*.csv` — ไฟล์ตัวอย่าง/template นำเข้า: `import-award-division-sample.csv` (รหัสร้าน,ปี,เดือน,คะแนน,เกรด,คะแนนรวม), `import-evaluation-test.csv` (คะแนนรายหัวข้อ), `import-grade-test.csv` (เกรดใหม่ ปี พ.ศ.), `import-premium-test.csv`, `import-real-score-template.csv` (หัวข้อ,เป้าหมาย/เกิดจริง,เดือนปี,รหัส,ตัวตั้ง,ตัวหาร)
- `test_files/` — ไฟล์ interface จริงไว้ทดสอบ: `daily_pl_backup/` (DAILYPL_*.txt + count file), `pre_stmt_backup/` (PRESTMT_*.txt + count), `sap-expense/backup/` (EXPSUB_202311.txt + summary) — สะท้อน convention "ไฟล์ข้อมูล + ไฟล์ Count คุมจำนวน record" แบบเดียวกับระบบ FGI/FCS legacy

---

## 4. Database

### 4.1 Connection

- **PostgreSQL** (AWS RDS `srm-sps-spsap-postgres-instance-dev...ap-southeast-1.rds.amazonaws.com`), database `postgres`, **schema `sps_store`**
- มี **2 DataSource ขนานกัน**:
  1. `TypeOrmModule.forRootAsync` ใน `app.module.ts` — ลงทะเบียน entity บางตัว + `autoLoadEntities`, รองรับ **replication mode** (master + slaves จาก `DB_SLAVE_HOSTS/PORTS/USERS/PASSWORDS`), pool/timeout ตั้งจาก env, `synchronize: false`
  2. Custom provider **`DATA_SOURCE`** (`src/database/database.providers.ts`) — โหลด entity ทั้งโฟลเดอร์ `src/entitys/*`, ตั้ง `search_path`, `random_page_cost=1.1` และ **override `dataSource.query()` เอง**: ถ้า SQL ขึ้นต้น `SELECT`/`WITH` → สุ่มส่งไป **slave pool** (pg Pool แยก มี pre-warm 15 connections, log สถิติ pool) ถ้า fail fallback master; write ทั้งหมดไป master — module ธุรกิจส่วนใหญ่ inject `DATA_SOURCE` ตัวนี้แล้วยิง raw SQL
- `src/data-source.ts` — DataSource สำหรับ **TypeORM CLI migration** (entities `src/entitys/*`, migrations `src/migrations/*`)
- WorkflowService สร้าง DataSource ตัวที่ 3 ชื่อ `workflow-connection` แยกไว้สำหรับ entity ของ `@srm/glb-workflow` (ดูหัวข้อ 8)

### 4.2 Migrations

มี**ไฟล์เดียว**: `src/migrations/202607200001-CreateSapStatementExpected.ts` — สร้าง `sap_statement_expected` (unique year+month+report_type+store_id) และ `sap_statement_summary_source` (unique cm_id+cm_entity+period+report_type) พร้อม index ตามงวด
`.gitignore` ระบุ `src/migrations/*` ยกเว้นไฟล์นี้ → ทีมนี้**ไม่ใช้ migration เป็นหลัก** — schema ส่วนใหญ่จัดการนอก repo, DDL production ใช้ `sql/deploy-*.sql` แทน

### 4.3 Entities ทั้งหมด (~100 ไฟล์ / ~90 ตาราง ใน `src/entitys` + entity ในบาง module)

ทุกตัวอยู่ใน schema `process.env.DB_SCHEMA` (= `sps_store`) เว้นที่ระบุ; ส่วนใหญ่**ไม่ประกาศ relation** (join ด้วย raw SQL/QueryBuilder — มี relation จริงแค่ ~10 จุด)

#### กลุ่ม A — Master data (`mas_*` + geo)

| ตาราง | PK | คอลัมน์สำคัญ / หมายเหตุ |
|---|---|---|
| `mas_store` | branch_id | branch_name, branch_type, status_type, area_id, region, zone_cd, province, open/close_date, active_flag — master สาขา 7-Eleven |
| `mas_store_organize` | branch_id+emp_id | fullname, id_card, email, group_id, data_type, active_flag — ผังผู้รับผิดชอบต่อสาขา (ManyToOne→business_group) |
| `mas_store_laos` / `mas_store_cambodia` | branch_id | 53 คอลัมน์ (โครงซ้ำกัน 100%) — master สาขาลาว/กัมพูชา + สายบังคับบัญชา fc/mn/dv/agm/gm |
| `mas_contact` | period+store_id+emp_id | ผู้ติดต่อรายสาขารายงวด (position, department, data_source) |
| `mas_sbp_ad` | sbp_ad_id | คิว sync Active Directory พนักงาน SBP (id_card, emp_id, email, flag_send_ad, franchisee_id) |
| `mas_param` | param_name | **ตาราง config กลางของระบบ** (param_value, ref_name, is_config) |
| `mas_taxpayer` | branch_id+taxpayer_id | ผู้เสียภาษีต่อสาขาต่องวด |
| `mas_zone` | zone_id | zone_cd, zone_name, sub_area_flag |
| `mas_area`, `mas_province`, `mas_district`, `mas_sub_district` | ตาม id | master ภูมิศาสตร์ (ใหม่) |
| `amphur`, `province` | — | ตารางภูมิศาสตร์ legacy ซ้ำซ้อนกับ mas_* |

#### กลุ่ม B — FML Statement domain (`fml_*` 23 ตาราง)

| ตาราง | ใช้ทำอะไร |
|---|---|
| `fml_sbp_stmt` | statement SBP รายสาขา/งวด (process_id, report_type, report_link, action_flag, unique key) |
| `fml_stmt_trans` | transaction log การ gen/ส่ง statement ต่อสาขา (+ send_email_flag) |
| `fml_stmt_end` | mark จบรอบ process (unique process_id+report_type, sum_process) |
| `fml_franchise_statement` / `_file` / `_group` | statement franchise + **เก็บไฟล์เป็น bytea ใน DB** + mapping group |
| `fml_bellinee_statement` / `_file` | คู่ขนานสำหรับสาย Bellinee |
| `fml_pre_statement` / `fml_sub_pre_statement` | ยอดขาย pre-statement (ยอด 7 วันย้อนหลัง + สะสมรายสัปดาห์/เดือน) — สองตารางโครงซ้ำ 100% (SBP กับ Sub-Area) |
| `fml_sub_organize` | ผังผู้บริหารสาย Sub (sup/mn/dv/agm/gm ครบ 40 คอลัมน์) |
| `fml_sub_group_mapping`, `fml_sub_group_report`, `fml_sub_user_group/store/zone` | ระบบสิทธิ์การเห็นรายงานสาย Sub (user↔group↔store↔zone) |
| `fml_bell_user`, `fml_bell_user_group/store`, `fml_bell_group_report` | ระบบสิทธิ์คู่ขนานสาย Bellinee |
| `fml_authorize` | permission ทั่วไปของ FML |
| `fml_sbp_skip_report_store` | สาขาที่ยกเว้นการออกรายงานตามช่วงวันที่ |
| `fml_tmp_importdata_stmt` | staging generic col01..col20 ก่อน gen statement |
| `fml_fs_other` (ไฟล์ `fs-other.entity.ts`) | รายการ Dr/Cr เพิ่มเติมประกอบ statement (จาก import `EXPSUB`) |
| `fml_cooperation_topic`, `fml_cooperation_trn`, `fml_email_account` | (ไม่มี entity — ใช้ raw SQL) หัวข้อ/เอกสารหนังสือขอความร่วมมือ, อีเมล auditor ที่จำไว้ |

#### กลุ่ม C — FES Evaluation domain (`fes_*`)

| ตาราง | ใช้ทำอะไร |
|---|---|
| `fes_evaluatedform`, `fes_evaluatedform_title`, `fes_title` | นิยามฟอร์มประเมินต่อช่วงเวลา + หัวข้อ |
| `fes_evallevelone/two/three` | โครงหัวข้อประเมิน 3 ระดับ (point, point_hit, hint, fixed) |
| `fes_grade`, `fes_gradedetail` | เกณฑ์เกรดต่อรอบ + ช่วงคะแนน→เกรด (E/G/P/I/F) |
| `fes_evaluate` | **หัวตารางการประเมินรายร้านรายรอบ** (order_id, eval_type, eval_month/year, status, grade) — หัวใจของ flow |
| `fes_evaluatedperson`, `fes_evaluate_opt`, `fes_evalperson*` | ผู้ประเมิน/ทีม OPT ต่อรอบ (ใช้ raw SQL) |
| `fes_copylvtwo/three` | snapshot หัวข้อ+คะแนน ต่อการประเมิน (ใช้ raw SQL) |
| `fes_import_data` และ `fes_importdata` | **สองตารางคนละตัว** (มี/ไม่มี underscore) — คะแนนดิบนำเข้า (titleId, goal_get, mm/yy, branch) |
| `fes_log` | log การประเมินรายสาขา |
| `fes_adjust_grade`, `fes_reward_grade_all`, `fes_reward`, `fes_reward_grade`, `fes_reward_duration` | (raw SQL) เกรดปรับแก้ + ระบบรางวัล/Division |
| `fes_evaltype`, `fes_properties` | (raw SQL) ประเภทและ config การประเมิน |

#### กลุ่ม D — FCS (เกี่ยวกับประกันรายได้) — คอลัมน์เต็ม

- **`fcs_monthly_sales`** — id(PK), store_id(5), year(4), month(2), `total_sales` numeric(38,3), `amt_cust_total`, `sales_exclude_card`, `amt_cust_exclude_card`, `sales_card`, `amt_cust_card`, `total_day`, create_date — ยอดขาย+ลูกค้ารายเดือน แยกรวม/ไม่รวม/เฉพาะบัตรโทรศัพท์ + จำนวนวันขาย (ข้อมูลตั้งต้นการคำนวณประกันรายได้)
- **`fcs_audit_costs`** — id, store_id, year, month, `product_exceeded_lack` numeric(38,2), create_date — มูลค่าสินค้าเกิน/ขาดจากการตรวจนับรายเดือน
- **`fcs_reminder_log`** — user_id+template_id (**DDL จริงไม่มี PK — entity เดา composite เอง**, comment ในไฟล์เตือนไว้), reminder_to/cc (varchar4000), reminder_type char(1), reminder_status char(1), error_msg, `json_data` varchar(4000), remind_date, create_by — log การส่งอีเมล reminder/ประวัติ export ให้ auditor
- `fcs_qssi_score`, `fcs_tmp_qssi_score`, `fcs_file_content` — (raw SQL ไม่มี entity) คะแนน QSSI + staging

#### กลุ่ม E — Franchise master (`fr_*`, franchisee, juristic)

| ตาราง | ใช้ทำอะไร |
|---|---|
| `fr_store` | **ตารางแกนของสัญญา store partner** (PK order_id, 82 คอลัมน์: store_id, contract_no/start/end, juristics_id, owner_id1..4, fr_type/subtype, cancel_type/date, reward_contract_type) |
| `fr_process` (130 คอลัมน์!), `fr_process_trn` | กระบวนการรับสมัคร/คัดเลือก/สัมภาษณ์ผู้สมัคร franchise + snapshot ต่อ step |
| `franchisee`, `juristic`, `juristic_group` | ทะเบียนผู้รับสิทธิ์ / นิติบุคคล |
| `cancel_contract_store_approve` | คำขออนุมัติยกเลิกสัญญา/ย้ายร้าน (order_id, cancel_type, to_store_id) |
| `store_sbp` (ไฟล์ `modules/performance-report/fr-store.entity.ts`!) | ร้านที่เป็น SBP (store_id, store_sbp_type, start_sbp_date, active_flag) |
| `fr_store_insure`, `fr_store_assessment` | (raw SQL จาก inquiry module) **เงินช่วยเหลือ/ประกันรายได้ต่อ order** (year, month, money_support, split%) + ผลประเมินต่อปีสัญญา (score, grade) |

#### กลุ่ม F — SAP statements

`statement` (ไฟล์เอกสารที่ลง CM: store_id, report_type, year/month/day, cm_id, cm_entity, type STA/SAP, action_flag, **verify_flag**), `statement_summary` (ตัวนับต่อรอบ: sum_record vs received_record + progress/complete_email_flag), `sap_statement_expected`, `sap_statement_summary_source`

#### กลุ่ม G — User & Import framework

`business_user` (user_id, group_id, email, franchisee_id, position_level, active_flag), `business_group` (tree ผ่าน parent_group_id), `business_user_group` (scope store_type/area), `common_code` (code_type+seq_no → code_value/name/mapping — **lookup กลางที่ทั้งระบบพึ่ง**), `import_group` → `import_type` (นิยามชนิดไฟล์ import: file_header, endpoint_url/key, cm_entity_name, s3_backup/template_path, payload_json, is_background) → `import_type_permission`, `master_template_columns` (metadata template คอลัมน์ generic upload), `general_upload_data_page_job` (สถานะ job upload), `general_upload_data_page_audit_log` (request/response), `upload_general` (ไฟล์ที่อัปโหลด ผูก job+audit+doc_id)

#### กลุ่ม H — Email

`email_template` (email_template_id, subject_format, body_format — ตัวแปรรูปแบบ `${var}`, sender, email_from, active_flag), `email_sent` (snapshot อีเมลที่ส่งจริง: subject, content, mail_to/cc, is_sent Y/N, error)

#### กลุ่ม I — อื่น ๆ

`store` + `store_organize` (master ร้านเวอร์ชันใหม่ — คู่ขนาน mas_*), `store_partner_contacts` (unique store_id+department), `sevenshop` / `fs_sevenshop` (master สาขา+สายบังคับบัญชา 55 คอลัมน์ โครงซ้ำกัน), `bellinee_store`, `bellinee_store_organize`, `mms_store_trans` / `mms_store_merge_trans` (feed ร้านจากระบบ MMS แบบ effective-dated + flag รวมหมวด book/kudsan/exta), `temp_pre_statement` / `temp_exp_sub` / `temp_control_file` (staging ไฟล์ interface + control count), `integration_log` (module, service, payload), `assistant_manager_assignments`, `performance` และ `performance_evaluation` (ตารางทดลอง)

#### ⚠️ Entity ซ้ำ/ชนกัน (ความเสี่ยงที่ควรรู้)

| ตาราง | ปัญหา |
|---|---|
| `business_user` | 2 ไฟล์ (`business-user.entity.ts` vs `business_user.entity.ts`) class ชื่อ `BusinessUser` เหมือนกัน คอลัมน์ต่างกันเล็กน้อย |
| `common_code` | 2 ไฟล์ + ชื่อ @Index ซ้ำ (`common_code_idx`) |
| `fes_importdata` | 2 class map ตารางเดียวกันแต่ **PK คนละคอลัมน์** (`import_id` vs `id` auto) — เสี่ยงสุด |
| `fes_grade`/`fes_gradedetail`/`fes_title`/`fes_evaluatedform_title` | ซ้ำระหว่าง `entitys/` กับ `modules/grades|manage-import/entities/` |
| ชื่อไฟล์หลอก | `fs-other.entity.ts`→ตาราง `fml_fs_other`, `modules/performance-report/fr-store.entity.ts`→ตาราง `store_sbp` (คนละตารางกับ `entitys/fr-store.entity.ts`), `store-orgenize.entity.ts` สะกดผิด |
| `fes_import_data` vs `fes_importdata` | **คนละตารางจริง** ต่างแค่ underscore — ชวนสับสนมาก |
| ไม่ระบุ schema | `juristic*`, `franchisee`, `fr_process*`, `cancel_contract_store_approve`, `store_organize`, entity ใน `modules/performance-report|manage-import` → พึ่ง search_path |

---

## 5. Configuration / Environment Variables

จาก `src/config/app.config.ts` + `.env-dev` / `.env.local` (ไฟล์ env dev **มี credentials จริง commit อยู่ใน repo** — ดูข้อสังเกต)

| กลุ่ม | ตัวแปร | ความหมาย |
|---|---|---|
| App | `NODE_ENV` (dev/uat/prd→normalize เป็น production), `APP_ENV`, `PORT` (3004 dev), `CORS_ORIGINS` (comma-sep), `LOG_COLOR`, `HTTP_LOG_BODY_LIMIT` | พื้นฐาน |
| Auth เข้า service | `X_API_KEY` (header x-api-key ที่ BFF ใช้), `JWT_SECRET`, `API_KEY_UPLOAD`/`API_KEY_CLIENT` (bcrypt สำหรับ ApiKeyUploadGuard) | guards |
| Database | `DB_HOST/PORT/NAME/USER/PASSWORD/SCHEMA`, `DB_REJECT_UNAUTHORIZED`, `DB_CONNECTION_TIMEOUT`, `DB_STATEMENT_TIMEOUT`, `DB_MAX_POOL`/`DB_MIN_POOL`, `DB_IDLE_TIMEOUT`, `DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT`, `DB_LOGGING` | master |
| DB replica | `DB_SLAVE_HOSTS/PORTS/USERS/PASSWORDS` (replication mode), หรือ legacy `DB_READ_HOST/PORT/NAME/USER/PASSWORD` | read-routing |
| Workflow | `WORKFLOW_SCHEMA` (default = DB_SCHEMA), `WORKFLOW_VERSION_ID` (ประเมินร้าน), `COOPERATION_WORKFLOW_VERSION_ID` (default 6) | หัวข้อ 8 |
| Content Manager (CTM) | `CM_ADD_URL/API_KEY/TIMEOUT_MS`, `CM_VIEW_FILE_URL/API_KEY/TIMEOUT_MS`, `CM_DELETE_URL/API_KEY/TIMEOUT_MS` | upload/view/delete เอกสาร |
| EJ | `EJ_API_URL`, `EJ_API_KEY_NAME`, `EJ_API_KEY`, `EJ_API_TIMEOUT` | ดาวน์โหลด ZIP Electronic Journal |
| Downstream | `DOWNSTREAM_TIMEOUT_MS` (URL อ่านจากตาราง `import_type`) | generic upload |
| AWS | `AWS_REGION`, `AWS_BUCKET_NAME`, `AWS_CREDENTIALS_PROFILE` (local), `AWS_PATH_TEMPLATE` | S3 |
| Import | `IMPORT_S3_UPLOAD_PREFIX`, `IMPORT_MAX_FILE_SIZE` (MB), `IMPORT_MAX_ROW_COUNT` (⚠️ โค้ดอ่านผิดไปใช้ `IMPORT_MAX_FILE_SIZE`) | contract import |
| Mail | `SMTP_HOST/PORT/USER/PASS`, `MAIL_FROM`, `MAIL_FROM_NAME`, `MAIL_FROM_ADDRESS`, `mailTemplateId` (default 73), `REMINDER_MAIL_TEMPLATE=73`, `REMINDER_SBP_LINK`, `REMINDER_SBP_PHONE` | อีเมล |
| RabbitMQ | `RABBITMQ_URL` หรือ `MQ_URL` (default `amqp://guest:guest@localhost:5672`) | publish master event |
| Evaluation mapping | `EVALUATION_TITLE_ID_MAP_JSON`, `PREMIUM_TITLE_ID_MAP_JSON` | map คอลัมน์ CSV → title_id ตอน import คะแนน/premium |
| Statement | `PARAMETER_FR_ID`, `SESSION_CURRENT_USER`, `ACCOUNT_CONTACT_DEPARTMENT_ID` (=ACC001), `PERMISSION_SEARCH_ID` | หน้า contacts |
| Cognito/BFF (อยู่ใน env แต่ตัว service นี้ไม่ได้ใช้ตรง ๆ) | `AUTH_CLIENT_ID/SECRET/ISSUER/CALLBACK_URL/DOMAIN/LOGOUT_URL/IDP`, `AUTH_DISABLED`, `DEV_USER_*`, `API_AUTHORIZATION_BACKEND_*`, `API_STORE_BACKEND_*`, `ENCRYPTION_SECRET/SALT`, `COOKIE_*`, `DATABASE_URL` (ของ Prisma) | มรดกจาก env ชุดเดียวกับ BFF |

Hardcode ที่ควรรู้ใน `AppConfig`: `stmtPttFilePathFrom = "D:/appshare/SPS/FML/interface_data/out/"` (path Windows legacy), class `FCSmailConfig` (mailTo เป็น gmail ของ dev)

---

## 6. โครงสร้าง `src/` (ทุกโฟลเดอร์ top-level)

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `assets/fonts/` | ฟอนต์ไทย (Sarabun, THSarabunNew, Angsana New) สำหรับ PDF |
| `common/` | ของกลาง: `constant/` (THAI_SHORT_MONTHS, ค่าคงที่ inquiry/cancel-contract, IMPORT_TYPE), `core/` (HttpContext ด้วย AsyncLocalStorage + MyLogger), `decorators/` (`@UserId()` อ่าน request.userId), `dto/` (BaseRequest/BaseResponse), `filters/` (HttpExceptionFilter, OtherExceptionsFilter), `guards/` (**AuthGuard** — Bearer JWT decode หรือ x-api-key), `helpers/` (common/date/read-query/response/string), `interceptors/` (ResponseInterceptor ห่อ `{success,data}`, LogControllerErrorInterceptor), `middleware/` (http-context, logger-context — log HTTP_IN/HTTP_OUT พร้อม mask ค่า sensitive, response, user-context), `utils/` (chunk, csv, date, **score-formula**, **evaluation-fixed-rule**, null-config) |
| `config/` | `AppConfig` class (อ่าน env ทั้งหมด + replication config), `app-config.module.ts` (global), interfaces |
| `database/` | `DatabaseModule` + provider **`DATA_SOURCE`** (TypeORM DataSource พร้อม read-replica routing ที่เขียนเอง — รายละเอียดหัวข้อ 4.1) |
| `entitys/` | TypeORM entities ~95 ไฟล์ (สะกด "entitys" ตามต้นฉบับ) |
| `guards/` | `HttpHeaderGuard` (เทียบ x-api-key === X_API_KEY ตรง ๆ), `ApiKeyUploadGuard` (bcrypt.compare กับ API_KEY_UPLOAD) |
| `migrations/` | migration 1 ไฟล์ (หัวข้อ 4.2) |
| `modules/` | 31 feature modules (หัวข้อ 7) |
| `providers/` | **Repository providers แบบ factory**: แต่ละโฟลเดอร์ (assistant_manager_assignments, business_user, common_code, general_upload_data_page_audit_log, general_upload_data_page_job, import_group, import_type, import_type_permission, master_template_columns, performance, statement, upload_general) export array `{provide: '<TOKEN>_REPOSITORY', useFactory: ds => ds.getRepository(Entity), inject: ['DATA_SOURCE']}` — ให้ module inject repository ผ่าน token string แทน `TypeOrmModule.forFeature` |
| `app.module.ts` / `app.controller.ts` / `app.service.ts` / `main.ts` | root — main.ts: ValidationPipe (whitelist+forbidNonWhitelisted+transform), global ResponseInterceptor + 2 exception filters, body limit 100mb, CORS credentials, MyLogger |
| `data-source.ts`, `register-paths.ts` | CLI DataSource + ลงทะเบียน tsconfig paths ตอน runtime |
| `cov_json/`, `out/`, `src/src/src/cov_temp/` | ขยะ coverage ที่หลุด commit (ไม่ใช่โค้ด) |

---

## 7. Modules ทั้งหมด (31 modules, ~32 controllers, ~243 endpoints)

> Guard ที่ระบุ = guard ระดับ controller; ทุก response ถูกห่อ `{success, data}` โดย ResponseInterceptor

### 7.1 `statement` — ใบแจ้งยอด/เอกสารการเงินร้าน (module ใหญ่สุด — service 7,597 บรรทัด)

รองรับหลายสายธุรกิจในตัวเดียว: `sbp` (ร้าน SBP), `operation` (FC/MN/DV/GM/AVP เห็นตาม email ใน `fs_sevenshop`), `sub_area`/`sub_area_total` (พื้นที่ CM/UB/YL/PK), `bellinee`, `cambodia`, `laos`, และร้านในปั๊ม ปตท. (PTT subtype 01–06)

**`StatementController`** — `/statement`, guard `HttpHeaderGuard`:

| Method Path | ทำอะไร |
|---|---|
| GET `dropdown/subtype` | คืน PTT subtype ตาม role: group 1 (Admin) เห็น 01–06, group 1101–1109 (PTT) เห็น 01,03,04 |
| GET `dropdown/stores` | dropdown ร้าน — switch ตาม type ไป query ของแต่ละสาย (สิทธิ์ตาม user/group/zone) |
| GET `dropdown/report-types` | dropdown ประเภทรายงานตามสิทธิ์ (`GROUP_ID_VIEW_ALL_STMT` ใน mas_param เห็นหมด; union `MBA0001` เสมอ) |
| POST `search-report` | ค้นหา statement แบบ unified ทุกสาย (paging firstRow/lastRow + hasMore; สาย SBP ค้น 2 ชุด ปกติ+taxpayer) |
| GET `report/pre-stmt` | popup Pre-Statement: ยอดขาย 7 วันย้อนหลัง + สะสมสัปดาห์/เดือน จาก `fml_pre_statement` |
| GET `report/daily-pl` | Daily P&L ของ Sub-Area จาก `fml_sub_pre_statement` |
| GET `form1/resolve` | logic popup อากรแสตมป์ขั้น 1: หาไฟล์ `FML20191021` ในช่วงที่ mas_param กำหนด |
| GET `form1/popupCheckStampDuty` | ขั้น 2: เช็คไฟล์ `RT040079` (ใบอากรแสตมป์) — ผู้ช่วยผู้จัดการได้ `isWaitSPConfirm`, ผู้มีสิทธิ์ได้ cmId ไป confirm |
| POST `form1/rt040079/confirm` | ยืนยันรับทราบ RT040079 (set action_flag='Y') |
| GET `/contacts` | รายชื่อผู้ติดต่อฝ่ายบัญชี (mas_contact + business_user, dept `ACC001`) |
| POST `/interface/sta/upload-cmadd` | **interface จาก STA**: ลงทะเบียนไฟล์ที่ขึ้น CM แล้ว → upsert `statement` (type STA) + นับ `statement_summary.received_record` (pessimistic lock) + log `integration_log` |
| POST `/interface/addStatementTrans` | **interface**: insert `fml_stmt_trans` + merge `fml_sbp_stmt` (transaction, respCode มาตรฐาน) |
| POST `/interface/addStatementEnd` | **interface**: batch upsert `fml_stmt_end` (จบรอบ process) |
| POST `/interface/oas/import-seven-shop` | **interface จาก OAS**: ดึงไฟล์ store.txt จาก S3 → sync master ร้านทั้งชุด (ดูด้านล่าง) |
| POST `download-file-aws` / `upload-file-aws` | wrapper S3 download/upload (base64) |
| GET `/export-ptt` | สร้าง PDF statement รวมของ ปตท. รายเดือน + validate + ส่งเมลแจ้ง |
| GET `/zipej-store` | ข้อมูลร้านสำหรับดาวน์โหลด EJ |
| GET `/commonCodeWithCond` | common_code ตามเงื่อนไข code_mapping |
| POST `/getExportStmtFileToExternalAuditLog` | ประวัติส่ง statement ให้ auditor (template 41) แบบ paging |
| POST `/genExportStmtFileToExternalAuditLog` | export ประวัติเดียวกันเป็น Excel (ExcelJS → `audit_log.xlsx`) |
| POST `merge-file` | รวมหลายไฟล์เป็น PDF เดียว (type NORMAL=CM, LINK=HQ e-Tax presign; ไฟล์ CSV แปลงเป็น PDF ก่อน) |
| POST `view-file` / GET `view-file/stream/:id` | ดูไฟล์ผ่าน CM (JSON presigned url / proxy binary stream) |
| GET `preview-csv/:id` | ดึงไฟล์จาก CM → detect encoding → parse PapaParse → คืน preview + downloadUrl |

**`EjDownloadController`** — `/statement/report/ej`, guard HttpHeaderGuard: POST `download` → POST ไป `EJ_API_URL/download-zipej` (`{date:YYYYMMDD, subareaCode}`) → GET ไฟล์จาก downloadURL (บังคับ https) → stream ZIP กลับ

**Logic เด่นใน service**: decode ไทย UTF-8→win874 fallback ทุกไฟล์ interface; Sub-Area zone scoping ด้วย CTE map `fml_sub_organize`→`mas_zone` (mapping กำกวม = fail-closed); `createPttPDF` merge PDF ด้วย pdf-lib+fontkit อัปโหลด `interface/out/PTT/`; `ImportSevenShop.execute()` = transaction 7 ขั้น sync `fs_sevenshop`→`sevenshop`→`mas_store`→`mas_store_organize`→`fr_store.region` (batch 500–2000 กัน limit 65535 params; GROUP_IDS: FC=2000, MN=70, DV=15, GM=38, AVP=28); กติกา active ของ `fr_store` ที่ใช้ซ้ำทั้งระบบ: `status!='D' AND cancel_type='00' AND (cancel_date IS NULL OR cancel_date+45วัน>=วันนี้)`; ท้าย statement.service.ts มี comment สรุป schema ทุกตารางไว้อ้างอิง

### 7.2 `sap` — callback จาก SAP E-TAX

`/sap`, guard HttpHeaderGuard: **POST `upload-cmadd`** (แยกไฟล์ summary `SUMMARY_*` → parse CSV รายบรรทัด `reportType,storeId,year,month` upsert `sap_statement_expected` + `sap_statement_summary_source` ภายใต้ `pg_advisory_xact_lock`; ไฟล์ปกติ → parse ชื่อ `SAP###_{store}_{YYYYMM}` upsert `statement`) · **GET `statement`** (dump ตาราง statement ทั้งหมด — ไม่มี filter)

กฎธุรกิจสำคัญ: store id 6 หลักตัดเหลือ 5 ท้าย (SAP เติม doc-type digit); **งวด SAP = เดือนออกเอกสาร ต้องลบ 1 เดือนให้เป็นเดือนของข้อมูล** (ยกเว้นไฟล์ Sub-Area `SAP\d{3}` นามสกุล xml/xls); ถ้าเลข expected/received เปลี่ยน → reset flag อีเมล progress/complete ใน `statement_summary` (ตัวส่งอีเมลจริงอยู่นอก service นี้)

### 7.3 `external-audit` — ส่ง statement ให้ผู้ตรวจสอบบัญชี

`/external-audit` (**guard ถูก comment ปิดไว้** — รับ userId ทาง query ตรง ๆ): 11 endpoints — ยอมรับเงื่อนไข (`insertAgreeStmtFile` → `fcs_reminder_log` template 40 type 0), นับ/ดูประวัติ (ย้อนหลัง 3 เดือน + auto-purge), รายชื่อร้านของ SP (จาก `fr_store` owner_id1/2/4), ตาราง pivot ความพร้อมของรายงานต่อร้าน (`listReportStmtFile` — dynamic columns S1..Sn, รายงานจาก common_code `FML00015`), จัดการอีเมล auditor ที่จำไว้ (`fml_email_account` สูงสุด 10 รายการ), และตัวจริง **`exportStmtFileToExternalAudit`**: รวม PDF statement 2 เดือนล่าสุดของกลุ่มร้าน → ใส่ **watermark** (ข้อความจาก mas_param, Angsana แดง 45°) + **bookmark ต่อร้าน** (เขียน /Outlines เอง, ไทยเป็น UTF-16BE hex) + **เข้ารหัสรหัสผ่าน** (`@pdfsmaller/pdf-encrypt-lite`) → ส่งอีเมล 2 ฉบับ (ฉบับไฟล์ template 40 → สำเร็จแล้วจึงส่งฉบับรหัสผ่าน template 41, CC หา SP) → log `fcs_reminder_log` type 1 (json_data = storeGroup/ref/auditorEmail)

### 7.4 `confirm-import` — ยืนยันเอกสารนำเข้า

`/confirm-import`, guard HttpHeaderGuard: GET `init` (dropdown report/store/status), POST `search` (join `statement`×`fs_sevenshop` — reportType `01`=FES0001 ใบแจ้งเกรดแบบเก่า, `02`=FES0003 แบบใหม่, `03`=ACC00004 ปรับฐานค่าจ้าง; statusVerify 1=verify แล้ว 2=รอ), POST `confirm` (set `verify_flag='Y'` → เอกสารจึงแสดงให้ร้านเห็น), POST `delete` (**ลบใน CM ก่อน แล้วค่อยลบ DB**), GET `file/view` (ดูไฟล์ผ่าน cmViewFile — ฟังก์ชันนี้ statement module ยืมใช้ด้วย)

### 7.5 `store-partner-contract-import` — นำเข้าผู้ติดต่อ Store Partner

`/store-partner-contract`, guard **ApiKeyUploadGuard** (bcrypt): POST `upload` (202) — CSV **pipe-delimited** header ไทยต้องตรงเป๊ะ (`พื้นที่|StoreId(รหัสร้าน)|Department(หน่วยงาน)|Name(ชื่อผู้ติดต่อ)|Tel(เบอร์ติดต่อ)`) → เก็บ S3 → validate ทุกแถว (error แม้แถวเดียว = ไม่แตะ DB) → **clear ตาราง `store_partner_contacts` แล้ว insert ใหม่ทั้งหมด** batch 1000; มี exception class เฉพาะ 11 ชนิด; ⚠️ พบ bug: validation Tel/Email เช็ค key `'Tel'` แต่ header จริงคือ `'Tel(เบอร์ติดต่อ)'` → ไม่เคยทำงาน; แม้ตอบ 202 แต่ประมวลผลจริงแบบ synchronous

### 7.6 `uploads` — Generic Upload Framework

`/uploads`, guard HttpHeaderGuard — ระบบนำเข้าไฟล์กลาง config จาก DB (`import_group`/`import_type`/`import_type_permission`):

| Endpoint | ทำอะไร |
|---|---|
| GET `master/group-report` | dropdown รายงานที่ user มีสิทธิ์ (report ไม่มี permission row = public) พร้อม config ครบ (template, entity CM, downstream URL, payload spec, isBackground) |
| POST `general/upload` | อัปโหลดไฟล์: ถ้า `is_background='Y'` (FES0001/FES0003) → สร้าง job แล้ว fire-and-forget คืน `jobId`; ไม่งั้นประมวลผล sync — ทุกไฟล์: S3 เสมอ → ถ้ามี entity_name เรียก **CM_ADD** → log job + audit |
| GET `general/job-status?jobId=` | **endpoint ที่ frontend poll** — สถานะจาก DB + สถิติละเอียดจาก **in-memory Map `jobStats`** (⚠️ หายเมื่อ restart / ไม่ share ข้าม pod, cleanup 5 นาที) |
| POST `general-stream` | ประมวลผลรายงานตาม code_value (ตารางด้านล่าง) |
| POST/GET `general/template` | ดาวน์โหลด template จาก S3 (`s3_template_path`) |
| GET `general/latest` / `general/export` | ประวัติอัปโหลดล่าสุด / ดึงไฟล์ (CM url หรือ S3 base64) |
| GET `mas-store-organize/structure` / `individual` | รายงานโครงสร้าง PTT (pivot group 1101–1109) / รายบุคคล (วันเกิดเป็น พ.ศ.) |
| POST `general/upload-callback` | BFF callback เมื่อ downstream จบ → บันทึก `upload_general` + ปิด job |

**Import processors** (`uploads/import_report/`): `SAP004APEXF`→`import_add_expense` (EXPSUB pipe 10 คอลัมน์ → ล้าง+insert `fml_fs_other`), `MBA0001`→`import_manage_store` (เป้าบริหารร้าน→`statement`), `FES0001`/`FES0003`→**`import_grade_report`** (1,296 บรรทัด: CSV 25 คอลัมน์ → upsert `statement`+`fes_adjust_grade`+`fes_reward_grade_all` → **วาดใบแจ้งเกรด PDF ต่อร้านด้วย pdfkit** แปลงพิกัดจาก JasperReports เดิม, เกรด E/G/P/I/F เลือกฟอร์ม 1–9, ส่วนแบ่งกำไรเกรด E ตามอายุ 23–33%/24–34%/25–35% หรือ `{newSplit}%` สำหรับ type A/C/FPTT → อัปโหลด CM แล้วเติม cm_id), `TES00002`→pass-through, `ORGPTT01`→`import_mas_store_organize` (validate เลขบัตร ปชช. checksum, group_id ในไฟล์ +1100 → 1101–1109, sync `store_organize`+`mas_store_organize`+`mas_store.fr_sub_type` แล้ว **publish RabbitMQ** exchange `sps.store.master` routing key `sps.store.master.store-organize.ptt` — ⚠️ ถ้า publish fail หลัง DB commit จะ inconsistent)

### 7.7 กลุ่ม FES — การประเมินร้าน (หัวใจธุรกิจอีกครึ่งหนึ่ง)

**สถานะการประเมิน (`fes_evaluate.status`)**: `S`=รอประเมิน, `SV`=รอประเมิน(ผู้ประเมินสำรอง), `SN`=รอตรวจสอบ, `AP`=ตรวจสอบแล้ว, `VE`=รออนุมัติ, `DO`=ส่งสรุปผล, `N`=ส่งแจ้งแล้ว, `AE`=แก้ไขหลังอนุมัติ, `W`=สร้างจาก reportGrades — flow: **S/SV → (ประเมิน+submit) → SN → (audit) → VE → (approve) → DO → สรุปเกรด/แจ้งผล**
**ประเภทรอบ (`eval_type`)**: `TWO`=ครั้งที่ 2, `MIDYEAR`=ราย 6 เดือน, `YEAR`=รายปี (+ lookback เดือนข้อมูล import: TWO=0, MIDYEAR/SIX=6, YEAR/FOUR=12, THREE=3, FIVE=4/5)

#### 7.7.1 `inform-evaluate` — เปิดรอบประเมิน + แจ้งผู้ประเมิน (`/informEvaluate`, AuthGuard)

GET `types-group` (ประเภทรอบ), GET `pseudonym-group-names`, GET `stores` (2 controllers — suggest ร้าน), POST `searchEvaluation-round` (ค้นรอบ), PUT `note/update`, POST `two` / POST `midyear` = **`sendEvaluation()`**: insert `fes_evaluate` (status S) ต่อร้าน → background: insert `fes_evaluatedperson`/`fes_evaluate_opt` + **`workflowService.initializeWorkflow({versionId: env.WORKFLOW_VERSION_ID, referenceId: evaluateId})`** ต่อรอบ + **ส่งอีเมลแจ้งผู้ประเมิน** ผ่าน `EmailLibService` template id จาก `mailTemplateId` (default **73**) พารามิเตอร์ลิงก์ `REMINDER_SBP_LINK`/เบอร์ `REMINDER_SBP_PHONE`

#### 7.7.2 `evaluation-process` — ทำแบบประเมิน (service 8,965 บรรทัด — ใหญ่สุดฝั่ง FES)

Controller ประกาศ **base path 16 แบบ** (ทุก combination ของ `api/`, `v1/`, `sbp/`, ตัวพิมพ์) guard AuthGuard: POST `checkPermission`, GET `dropdowns`, POST `pseudonym-group/:groupId/users` (รายชื่อผู้ประเมินในกลุ่มนามแฝง), POST `search`, GET `:evaluateId/detail` (ฟอร์ม 3 ระดับ + คะแนน), POST `:evaluateId/save-draft`, POST `recalculate` (เดี่ยว/batch — คำนวณคะแนนใหม่จากข้อมูล import), POST `:evaluateId/submit` (S→SN), POST `export`, ชุด assess (POST `searchAssess`, `assessEvaluate/scoreKey`, `assessEvaluate/:evaluateId`, `assessSave`, `assessSubmit` — ฝั่งผู้ตรวจ), GET `assessCriteriafile` (+`/download` — ไฟล์เกณฑ์จาก S3/`fcs_file_content`), POST `EvaluationformExport` / `assessExport` (Excel แบบฟอร์ม), POST `storeManagementsearch` / `storeManagementexport`
ตารางหลัก: `fes_evaluate`, `fes_evaluatedperson`, `fes_copylvtwo/three` (snapshot คะแนน), `fes_evallevelone/two/three`, `fes_importdata`, `store_sbp`; คะแนนคำนวณด้วย `common/utils/score-formula.util.ts` (linearScore, percentBandScore, ratioPercent) + `evaluation-fixed-rule.util.ts` (map fixed rule ↔ import title ↔ คะแนนเต็มรายข้อ เช่น rule 1=120, 2=80…); ส่งเมลด้วย EmailLib template 73

#### 7.7.3 `assessment-audit` — ตรวจสอบ/อนุมัติผลประเมิน (service 6,220 บรรทัด)

Base paths `['v1/sbp/assessment/audit','/assessment/audit']` (+`/assessment` สำหรับ dvName): POST/GET `dvName` (suggest ฝ่าย — cache in-memory TTL 5 นาที), POST `search` (ค้นตามรอบ/สถานะ/เกรด — มี index เฉพาะจาก `scripts/optimize-audit-search.sql`), GET `:evaluateId/detail`, POST `:evaluateId/assessSave`, POST `:evaluateId/approve` (S→SN, VE→DO, อื่น→VE), POST `approves` (bulk — เฉพาะ VE→DO), POST `:evaluateId/recalculate`, POST `:evaluateId/sendback/confirm` (ตีกลับ→S), POST `sendConclude` (→DO ส่งสรุปผล), POST `export` (Excel 12 คอลัมน์: ประเภท/สาขา/ภาค/ฝ่าย/สถานะ/คะแนนรวม/เกรด/คะแนน-เกรดปรับช่วยเหลือ/ชื่อ SP/Type/วันที่เป็น SBP), POST `:evaluateIds/exportEvaluationform` (แบบฟอร์ม PDF/Excel หลายรายการ)

#### 7.7.4 `evaluate-summary` — สรุปเกรด (`/evaluateSummary`, AuthGuard)

POST `divisionSearchStore`, PUT `:evaluateId/:storeId/confirmGrade` (ยืนยันเกรด), POST `:storeId/reportGrades` (สร้าง `fes_evaluate` status `W` จากรายงาน), GET `:evaluateId/:storeId/viewGrade` (รายละเอียดคะแนน+hint เกณฑ์), POST `viewMonthly` (คะแนนรายเดือน), GET `:userId/store`; + `assessment.controller.ts` GET `/assessment/evaluation/criteriaFile` (ไฟล์เกณฑ์)

#### 7.7.5 `assessment` — dropdown ร้าน (`/assessment`, HttpHeaderGuard): GET `stores` (ร้าน SBP active จาก `store_sbp`×`fs_sevenshop`)

#### 7.7.6 `performance-report` — รายงานผลดำเนินงานร้านประกอบการประเมิน (`/assessment`)

GET `stores`, POST `performance/search-store`, GET `eval-level-two` / `eval-level-three` (หัวข้อ), GET `performance/monthly-6m` (ผล 6 เดือน), POST `performance/store-info`, POST `performance/search` (สรุป target vs actual ต่อหัวข้อ — fallback ไปข้อมูล eval เมื่อไม่มี import), POST `performance/exportExcel`; ตาราง: `store_sbp`, `fes_evaluate`, `fes_evallevel*`, `fes_importdata`, `fes_log`

#### 7.7.7 `grades` — เกณฑ์เกรด (`/grades`)

GET `gradeDatalist`, GET/PUT `gradesedit/:id`, POST `addgrades` (สร้างรอบเกรด: gen id เอง MAX+1 + **สร้างฟอร์มประเมินจาก `templates/evaluate-template.json`** ลง `fes_evaluatedform`+`fes_evallevelone/two/three`), DELETE ``/`score-ranges`/`gradeId` — จัดการ `fes_grade`/`fes_gradedetail` (ช่วงคะแนน→เกรด E/G/P/I/F)

#### 7.7.8 `grade-evaluation-summary` — รายงานสรุปเกรด (AuthGuard): POST `search`, GET `reportPtt/reportFrom`, POST `reportPtt/reportSearchgrade`, POST `reportPtt/reportExport` (Excel; ประกาศซ้ำ 2 ครั้งในโค้ด) — อ่าน `fes_evaluate`/`fes_evaluatedform`/`fes_adjust_grade`

#### 7.7.9 `award-division` — การแข่งขัน Division (`/awardDivision`, AuthGuard)

GET `types-division` (ปี/ภาค), POST `searchDataDivision`, POST `/exportGradeDivision` (Excel), PUT `/confirmDivision` (ยืนยันผล), GET `/download-import-template`, POST `/validate-import-data` + `/importData` (นำเข้าเกรดจาก CSV — ตรวจกับ `fes_reward_grade` เดิม), POST `/exportCollectDivisionReport`, GET `reportType` — ตาราง `fes_reward`, `fes_reward_grade`, `fes_reward_duration`; กติกา Division ตาม `sql/Guidelines.html` (นับจำนวนเกรด Excellence ต่อเนื่อง → National/2/1/Champions/Premier)

#### 7.7.10 `report-division` — รายงาน Division ฝั่ง Admin/SBP (`/reportdivision`, AuthGuard): POST `/loadCurrent`, GET `/loadCommonCode(+OrderByValue)`, POST `loadOptList`, GET `/loadDivision`, POST `/searchDataAdmin` / `/searchDataSbp`, POST `exportDivisionAdmin` / `exportDivisionSbp` (Excel), GET `criteriaDivision` (ดาวน์โหลดไฟล์เกณฑ์)

#### 7.7.11 `manage-import` — จัดการข้อมูลคะแนนที่ import (`/manage-import`, AuthGuard): GET `test`, GET `find-real` (dropdown ฟอร์ม/หัวข้อจาก `fes_evaluatedform`/`fes_title`), POST `searchreal` (ค้น `fes_importdata` + paging), DELETE `deletereal` (ลบตาม import_id)

#### 7.7.12 `sbp-import` — นำเข้าคะแนน/ข้อมูลประเมิน (`['/import','sbp/import']`, AuthGuard)

POST `real-score` (คะแนนจริง เป้าหมาย/เกิดจริง ตัวตั้ง/ตัวหาร), POST `premium` (คะแนน Premium — map `premiumType` 1–6 → title_id ผ่าน `PREMIUM_TITLE_ID_MAP_JSON`), POST `evaluation` (คะแนนรายหัวข้อ — map คอลัมน์ b–f → title_id ผ่าน `EVALUATION_TITLE_ID_MAP_JSON` + โหลด map จาก DB), POST `import-grade` (เกรดใหม่ ปี พ.ศ.), POST `responsible-sbp` (ผู้รับผิดชอบ), POST `import-cooperation-topic` (หัวข้อหนังสือขอความร่วมมือ), GET `premiumType` — ทุกตัว validate งวด/ร้าน/transfer ownership แล้วเขียน `fes_importdata`

### 7.8 `cooperation-request` — หนังสือขอความร่วมมือ (ใช้ workflow engine จริงจังที่สุด)

Base paths `['v1/sbp/docCooperation','sbp/docCooperation','docCooperation']` (ไม่มี guard ระดับ controller — อ่าน user จาก header `x-user-id`/`x-user-group-id` ที่ BFF ส่งมา), 21 endpoints:

- Dropdown/เช็คสิทธิ์: GET `checkCreateDepartment`, `docType`, `docStatus`, `filterOptions`, `cooperationTopic` (จาก `fml_cooperation_topic`), `storeActive`, `storeOrgActive(/:storeId)`, `searchApproverList` (ผู้อนุมัติตาม group/position/store/หน่วยงาน), `checkDocType`, `checkDisplayPart`
- ค้นหา/รายงาน: GET `cooperationSearch` (join `fml_cooperation_trn` × workflow transaction — visibility scope ซับซ้อน: ซ่อนสถานะใน common_code `COOP_STATUS_HIDE`, SP (group ใน mas_param `CPR_HIDDEN_GROUP_ID`) เห็นเฉพาะร้านตัวเองผ่าน `store_sbp`), GET `exportCooperationReport`, GET `exportSummary` (Excel)
- เอกสาร: GET `cooperationDefaultDetails`, `currentStepCooperation` (state ปัจจุบันจาก workflow), `cooperationDetail`, `cooperationApproverList` (จาก prepared approvers)
- Action: POST `cooperationRequestorDoc` — สร้าง/ส่งเอกสาร: upsert `fml_cooperation_trn` + running เลขที่เอกสารต่อร้านต่อปี + `initializeWorkflow(versionId=COOPERATION_WORKFLOW_VERSION_ID default 6)` + `addPreparedApprover` ตามสายที่เลือก + trigger `submit`; POST `cooperationApproveDoc` — trigger `approve` / `sendback` / `cancel` ตาม action; POST `cooperationConfirmDoc` — ร้านยืนยันรับทราบ (trigger `APPROVE` ขั้นสุดท้าย); POST `cooperationExport`
- `cooperation-pdf.service.ts` — สร้าง PDF หนังสือด้วย **puppeteer** (HTML template จาก S3 `AWS_PATH_TEMPLATE`, browser instance เดียว + idle timeout 60s ปิดเอง)

### 7.9 `backlog` — inbox งานรออนุมัติ

`/api/workflow`, guard HttpHeaderGuard: GET `/pending?userId&userGroupId` → `WorkflowService.getPendingFlow()` → รายการ `{transactionId, workflowName, stateName, waitingDate, approver, createBy, urlMain}` — หน้า "งานของฉัน" กลางที่รวมทุก workflow

### 7.10 `performance` — รายงานผลดำเนินงาน/FCS (`/performance`, HttpHeaderGuard — 19 endpoints)

- Dropdown: GET `list-year-sales-summary`, `list-month-sales-summary`, `list-sales-type-summary`, `list-zone-summary`, `list-type-group-summary`, `qssi-type-list`
- รายงาน: POST `sales-summary` (+`/export` Excel — join `fcs_monthly_sales`), POST `report-qssi` (คะแนน QSSI จาก `fcs_qssi_score`), POST `report-audit` (join `fcs_monthly_sales` × `fcs_audit_costs` — %Audit ต่อยอดขาย), POST `report-open-store` + `report-open-store-count` (ร้านเปิดใหม่), POST `report-call-complaint` (อ่านไฟล์ข้อร้องเรียนจาก S3)
- Interface นำเข้า: POST `import-monthly-sales` (ลบข้อมูลงวดเดิมแล้ว insert `fcs_monthly_sales` + `fcs_audit_costs` จากไฟล์; แจ้งผลทางอีเมล EmailLib), POST `import-qssi` (staging `fcs_tmp_qssi_score` → `fcs_qssi_score`)
- อื่น ๆ: POST `send-mail` (ส่งเมล generic), POST `upload-file-aws` / `download-file-aws`, POST `test-integration` (echo ทดสอบ)

### 7.11 `inquiry` — คำขอ/ใบคำสั่งเกี่ยวกับสัญญาร้าน (`/inquiry` — 15 endpoints)

GET `store`, `store/address/:storeId`, `store-partner`, `co-manager`, `successor`, `current-manager`, `store-ref`, `legal-entity`(+`-detail/:id`), `affected-store`, `search` (รวมสถานะยกเลิกสัญญา/ย้ายร้านจาก `cancel_contract_store_approve`), GET `:orderId` (ฟอร์มเต็ม), POST ``/PUT ``/PATCH `:orderId` (สร้าง/แก้/ลบ-ยกเลิก inquiry) — เขียน `fr_process`/`fr_process_trn` และที่สำคัญ: **`fr_store_insure` (order_id, store_id, seq_no, year, month, `money_support`, `split`)** = เงินช่วยเหลือ/ประกันรายได้ต่อสัญญา และ `fr_store_assessment` (score, grade ต่อปีสัญญา); ค่าคงที่ใน `common/constant`: CANCEL_COMMON_CODE `00034`, MOVE_STORE code `00098`, status W/D

### 7.12 `master` — master data + interface sync (`/master`, HttpHeaderGuard)

GET `common`, `province`, `district`, `sub-district`, `area` (lookup) + **3 interface ที่ระบบ HR/สิทธิ์ภายนอกยิงเข้ามา**: POST `users/interface` (sync `business_user` insert/update/soft-delete + กลุ่ม `business_user_group`/`fml_sub_user_group`/`fml_bell_user_group`), POST `statement-area/interface` (sync `fml_sub_user_zone` — พื้นที่ที่ user เห็น statement), POST `statement-store/interface` (sync `fml_sub_user_store`) — ทั้งหมดเป็น transaction ต่อรายการ พร้อม resolve zone จากร้าน

### 7.13 `store` — ข้อมูลร้าน (`/store`, HttpHeaderGuard): GET `list`, `detail`, `search`, `regions-by-email`, `all-regions`, `province-by-region`, `opt-name`, POST `store-transfer` (ร้านตามเงื่อนไขโอนย้าย) — จากตาราง `store`/`mas_store`/`sevenshop`

### 7.14 `common` — lookup กลาง (`/common`): GET `common-code`, `common-code/with-sub`, `master/province`, `master/district/:provinceId`, `master/sub-district/...` (+ variant `store-profile`), `master/area`

### 7.15 `assistant-manager-assignments` (`/assistant-manager`, HttpHeaderGuard): GET `` (ดูตาม storeCode), POST `/assign` (บันทึกผู้ช่วยผู้จัดการต่อสาขา — ตาราง `assistant_manager_assignments` unique user+store+employee)

### 7.16 `auth` (`/auth`): POST `login` (**stub — คืน string `sample`**), GET `test`; ของจริงคือ `AuthService.getUserProfileByUserId()` ที่ module อื่นเรียกใช้อ่าน profile จาก `business_user` (login จริงอยู่ที่ Cognito ฝั่ง BFF)

### 7.17 Service-only modules (ไม่มี controller)

| Module | หน้าที่ |
|---|---|
| `workflow` | `WorkflowService` — wrapper ของ `@srm/glb-workflow` (หัวข้อ 8) |
| `mail` | `MailService` (nodemailer + template จาก DB + log `email_sent`) และ re-export `EmailLibService` |
| `aws` | `AwsService` — S3 upload (base64→PutObject), download (→base64), moveFile (copy+delete, cross-bucket ได้), checkFileExist |
| `rabbitMQ` | ฟังก์ชัน `publishMessage(urls, exchange, routingKey, payload)` — connect→assertExchange(topic,durable)→publish(persistent,JSON)→ปิด connection เสมอ |

### 7.18 `app` controller: GET `/` (hello), GET `/check`, GET `/api/health` (ใช้ใน Docker HEALTHCHECK)

---

## 8. Workflow Engine (`@srm/glb-workflow`)

### 8.1 สถาปัตยกรรม

- เป็น **private npm library** (state machine) — ตัว definition ของ flow (states/routes/events) เก็บใน **ตาราง DB** ไม่ใช่ในโค้ด
- `src/modules/workflow/workflow.service.ts` เป็น wrapper กลาง: lazy-`require('@srm/glb-workflow')` + สร้าง **DataSource แยกชื่อ `workflow-connection`** (schema จาก `WORKFLOW_SCHEMA` หรือ DB_SCHEMA) ลงทะเบียน **entity 10 ตัวของ library**:
  `WorkflowEntity, WorkflowVersionEntity, WorkflowStateEntity, WorkflowStatusEntity, WorkflowRouteEntity, WorkflowTransactionEntity, WorkflowHistoryEntity, WorkflowApproverEntity, WorkflowGroupEntity, WorkflowGroupMapEntity`
  → ตาราง workflow: definition (workflow/version/state/status/route/group/group_map) + runtime (transaction/history/approver)
- ทุก operation ห่อผ่าน `TypeOrmUnitOfWork` + `WorkflowTransactionRepositoryImpl`/`WorkflowHistoryRepositoryImpl`

### 8.2 Methods ที่ expose

`initializeWorkflow({referenceId, userId, versionId})`, `triggerEvent({referenceId, event, eventParam, remark, userId, userFullname, nextApproverId, versionId})`, `getPermissionEvents`, `getHistory`, `getTransaction`, `getPendingFlow({userData:{userId, groupId}, versionId?})`, `addPreparedApprover({referenceId, versionId, stateId, approver, seq, userId})`

### 8.3 การใช้งานจริงในระบบ

| ผู้ใช้ | versionId | events | referenceId |
|---|---|---|---|
| `cooperation-request` (หนังสือขอความร่วมมือ) | `COOPERATION_WORKFLOW_VERSION_ID` (default **6**) | `submit`, `approve`, `sendback`, `cancel`, `APPROVE` (ยืนยันรับทราบ) | `trn_id` ของ `fml_cooperation_trn` |
| `inform-evaluate` (เปิดรอบประเมิน) | `WORKFLOW_VERSION_ID` (env) | initialize อย่างเดียว (trigger ถูก comment ไว้ — ตัวอย่างใช้ versionId 9) | `evaluate_id` ของ `fes_evaluate` |
| `backlog` | ไม่ระบุ (ทุก version) | — | อ่าน pending list |

**ข้อสังเกตสำคัญ**: การประเมิน (FES) เดิน state จริงด้วยคอลัมน์ `fes_evaluate.status` (S→SN→VE→DO) ใน SQL ตรง ๆ — workflow engine ถูก initialize ไว้คู่ขนาน (ยังไม่ trigger event ตาม state) ส่วน**หนังสือขอความร่วมมือใช้ engine เต็มรูปแบบ** (state ปัจจุบันอ่านจาก `workflow_transaction.current_status_id`, ผู้อนุมัติจาก prepared approvers, การมองเห็นเอกสาร join กับ workflow transaction)

### 8.4 Email / Notification

- **2 กลไก**: (1) `MailService` ภายใน — nodemailer + template จากตาราง `email_template` (แทนตัวแปร `${var}` ใน subject/body) + log ทุกฉบับลง `email_sent` (is_sent Y/N + error) (2) **`EmailLibService`** จาก `@gosoft-sbp/email-lib` — ใช้ในโมดูลใหม่ ๆ (inform-evaluate, evaluation-process, performance, external-audit, statement PTT) รูปแบบเรียกเหมือนกัน (`emailId` = template id)
- Template เด่น: **73** = แจ้งผู้ประเมิน (`REMINDER_MAIL_TEMPLATE`), **40** = ส่งไฟล์ statement ให้ auditor, **41** = ส่งรหัสผ่านไฟล์
- log เพิ่มเติม: `fcs_reminder_log` (การส่ง reminder/export ให้ auditor), `fml_stmt_trans.send_email_flag`, `statement_summary.progress/complete_email_flag`
- `templates/` ใช้กับ**ฟอร์มประเมิน** (ไม่ใช่อีเมล — email template อยู่ใน DB); template HTML อีเมล auditor เป็น inline HTML (TIS-620) ในโค้ด external-audit

---

## 9. Cross-cutting

| ชิ้น | ไฟล์ | ทำอะไร |
|---|---|---|
| `HttpContextMiddleware` → `HttpContext` | `common/middleware`, `common/core/http-context.ts` | สร้าง context ต่อ request (AsyncLocalStorage — request id ใช้ใน logger) — apply ทุก route เป็นตัวแรก |
| `LoggerContextMiddleware` | `common/middleware/logger-context.middleware.ts` | log `HTTP_IN`/`HTTP_OUT` (method, url, ip, body ตัดที่ `HTTP_LOG_BODY_LIMIT`=2000) พร้อม **mask** authorization/x-api-key/password/token |
| `MyLogger` | `common/core/logger.ts` | LoggerService เอง (สี ANSI เมื่อ `LOG_COLOR=true`, ผูก request id จาก HttpContext) |
| `ResponseInterceptor` (global) | `common/interceptors/response.interceptor.ts` | ห่อทุก response เป็น `{success:true, data}` (ข้ามถ้า service ห่อเองแล้ว) |
| `LogControllerErrorInterceptor` | `common/interceptors/log-controller-error.interceptor.ts` | log error ราย controller (ใช้ใน award-division, report-division, assessment, grade-evaluation-summary) |
| `HttpExceptionFilter` + `OtherExceptionsFilter` (global) | `common/filters/` | แปลง error เป็น `{success:false, data:null, error:{code,message}}` (รองรับ custom code) |
| **Guards 3 ตัว** | `guards/http-header.guard.ts` — เทียบ `x-api-key === X_API_KEY` (ใช้มากสุด: statement, sap, uploads, master, performance, store, confirm-import, assistant-manager, backlog, assessment) · `common/guards/auth.guard.ts` — **AuthGuard**: รับ `Bearer <jwt>` (แค่ `jwt.decode` **ไม่ verify signature** — set `request.userId` จาก username/sub) หรือ x-api-key (ใช้ใน: evaluation-process, inform-evaluate, evaluate-summary, award-division, report-division, sbp-import, manage-import, grade-evaluation-summary) · `guards/api-key-upload.guard.ts` — bcrypt.compare hashed key (store-partner-contract) |
| `@UserId()` decorator | `common/decorators/user-id.decorator.ts` | ดึง userId ที่ AuthGuard แปะไว้ |
| Providers pattern | `src/providers/*` | repository factory ผูก token string (`XXX_REPOSITORY`) กับ `DATA_SOURCE` — DI แบบ manual แทน forFeature |
| Utils เด่น | `score-formula.util.ts` (สูตรคะแนนกลาง — single source ระหว่าง performance-report กับ assessment-audit), `evaluation-fixed-rule.util.ts` (map fixed rule↔title↔คะแนนเต็ม), `chunk.util`, `csv.util`, `date.util` (พ.ศ./ค.ศ.), `null-config.util` |

---

## 10. การเชื่อมต่อระบบภายนอก

| ระบบ | ทิศทาง | กลไก | ใช้ที่ |
|---|---|---|---|
| **CTM / Content Manager** (`ctm-ctmapi*.cpall.co.th`) | ออก | REST `cmAdd` / `cmViewFile` / `cmDelete` + x-api-key (env `CM_*`) — เก็บ/ดู/ลบไฟล์เอกสาร, entity หลัก `sbp_statement` | uploads, statement, sap, confirm-import, external-audit |
| **HQ e-Tax gateway** (`ctm-etaxapi.cpall.co.th`) | ออก | JSON-RPC presign download (channel `SAP_SBP`, doc FULLFORM) — ⚠️ URL+JWT hardcode ในโค้ด | statement `document.service.ts` (merge-file type LINK) |
| **EJ gateway** | ออก | POST `/download-zipej` + x-api-key (`EJ_*`) → ZIP Electronic Journal | statement `ej-download` |
| **AWS S3** (`srm-sps-data-s3-dev`) | สองทาง | SDK v3 — ไฟล์ interface in/backup-in, template, PDF ที่ gen, upload ทั่วไป | aws.service ใช้ทั่วระบบ |
| **SAP (E-TAX/บัญชี)** | เข้า | callback `POST /sap/upload-cmadd` + ไฟล์ `SAP###_*`, `SUMMARY_SAP*`, `EXPSUB_*` ผ่าน CM/S3 | sap, uploads |
| **STA** | เข้า | `POST /statement/interface/sta/upload-cmadd`, `addStatementTrans`, `addStatementEnd` | statement |
| **OAS / Store Profile** | เข้า | `POST /statement/interface/oas/import-seven-shop` (ไฟล์ store.txt บน S3) | statement |
| **ระบบ HR/สิทธิ์** | เข้า | `POST /master/users/interface`, `statement-area/interface`, `statement-store/interface` | master |
| **RabbitMQ** | ออก | exchange `sps.store.master` (topic) key `sps.store.master.store-organize.ptt` — broadcast โครงสร้างองค์กร PTT (env `RABBITMQ_URL`/`MQ_URL`) | uploads (ORGPTT01) |
| **SMTP** | ออก | nodemailer / email-lib (`SMTP_*`, from `noreply@cpall.co.th`) | mail, inform-evaluate, evaluation-process, external-audit, performance, statement |
| **Downstream API (dynamic)** | ออก | URL+key จากตาราง `import_type` — BFF/บริการปลายทางของแต่ละรายงาน + callback กลับที่ `/uploads/general/upload-callback` | uploads |
| **AWS Cognito** | (อ้อม) | env `AUTH_*` — ใช้จริงที่ BFF; service นี้เพียง decode JWT | auth guard |
| **Dynatrace** | ออก | OneAgent ฝังใน image | ทั้ง service |

---

## 11. ข้อสังเกต

### 11.1 สิ่งที่เกี่ยวกับประกันรายได้ / FCS / K2 (โยงกับ prototype SBPGI)

1. **ตาราง `fcs_monthly_sales` / `fcs_audit_costs`** — ยอดขายรายเดือน (แยกรวม/ไม่รวมบัตรโทรศัพท์ + จำนวนวันขาย) และมูลค่าสินค้าเกิน/ขาดจากตรวจนับ คือ**ข้อมูลตั้งต้นชุดเดียวกับที่ FGI/FCS batch (Jobs ใน `fcsJar/`) ใช้คำนวณเงินชดเชยประกันรายได้** — ที่นี่มี interface import (`/performance/import-monthly-sales`) และรายงาน (%Audit, sales summary) แล้ว แต่**ยังไม่มี logic คำนวณเงินชดเชย**ใน service นี้
2. **`fr_store_insure` (money_support, split, year, month ต่อ order_id)** ที่ inquiry module เขียน — โครงเดียวกับตารางประกันรายได้ฝั่ง legacy → จุดเชื่อมข้อมูลสัญญา-เงินช่วยเหลือที่ K2/SBPGI จะต้องใช้
3. **Workflow engine `@srm/glb-workflow` มีอยู่แล้วและใช้งานจริง** (หนังสือขอความร่วมมือ = versionId 6) — ตรงกับ design ของ prototype ที่ให้ระบบประกันรายได้ใช้ "internal Workflow Engine" แทน K2 REST: เพิ่ม workflow version ใหม่ + ตาราง state/route ก็ต่อยอดได้ทันที (pattern: initialize → addPreparedApprover → triggerEvent, inbox รวมที่ `/api/workflow/pending`)
4. `fcs_reminder_log` + `email_template`/`email_sent` = โครงระบบแจ้งเตือนอีเมลแบบ template ที่ prototype (email templates ของ K2) จะ reuse ได้
5. Convention ไฟล์ interface (ไฟล์ข้อมูล + ไฟล์ `*_Count_*` คุมจำนวน record ใน `test_files/`, ตาราง `temp_control_file.expected_count`) สืบทอดจากระบบ FGI/FCS legacy โดยตรง

### 11.2 จุดแข็ง

- Read-replica routing เขียนเองครบทั้ง TypeORM replication + override raw `query()` (พร้อม pre-warm pool, fallback master, comment อธิบาย consistency ละเอียด)
- โมดูลใหม่ ๆ (store-partner-contract, sap, assessment-audit) มีมาตรฐานดี: DTO validation เข้ม, exception class เฉพาะ, advisory lock กัน race, partial index ทำ performance (18s→<800ms)
- Docker image ใส่ใจ security (ลบ npm, patch CVE ใน Dynatrace agent, non-root) + ฟอนต์ไทยสำหรับ PDF ครบ
- ระบบ Generic Upload ที่ config จาก DB ทำให้เพิ่มรายงานนำเข้าใหม่โดยแทบไม่ต้องแก้โค้ด

### 11.3 จุดเสี่ยง/หนี้ทางเทคนิคที่พบ

1. **Secrets ใน repo**: `.env-dev`/`.env.local` มี DB password, API keys, SMTP password (gmail ส่วนตัว dev) จริง commit อยู่; JWT token PRD ของ HQ e-Tax + fallback CM API key **hardcode ในซอร์ส** (`statement/document.service.ts`, `sap.service.ts`, `external-audit.service.ts`)
2. **AuthGuard ไม่ verify JWT signature** (แค่ decode) และ `external-audit.controller` ปิด guard ไว้ทั้ง controller (รับ userId ทาง query) — ปลอดภัยได้ก็ต่อเมื่อ network layer กันให้ BFF เท่านั้นที่เข้าถึง
3. **SQL injection surface** ใน raw SQL บางจุด (interpolate store ids ตรง ๆ ใน `external-audit.getListReportStmt`, `import-seven-shop.deleteMso`)
4. **Entity ซ้ำ/PK ไม่ตรงตารางจริง** (fes_importdata 2 class คนละ PK, business_user/common_code สองไฟล์, fcs_reminder_log ไม่มี PK จริงใน DB) — เสี่ยง silent bug
5. **สถานะ background job เก็บใน in-memory Map** (`uploads.jobStats`) — ไม่รอดข้าม restart/multi-pod; RabbitMQ publish หลัง DB commit โดยไม่มี outbox
6. เศษ legacy: path Windows (`D:/appshare/...`, `C:/Windows/Fonts/Tahoma.TTF` — จะพังบน Linux), Prisma scripts ค้าง, โฟลเดอร์ขยะ `src/cov_json`, `src/out`, `src/src/src/cov_temp`, `error_log.txt` ใน root, ชื่อ package ยังเป็น `nest-api-template`
7. ความซ้ำซ้อนเชิง schema: master ร้าน 4 ชุด (mas_store / sevenshop / fs_sevenshop / store), ภูมิศาสตร์ 2 ชุด (mas_* กับ amphur/province), pre_statement 2 ตารางโครงเดียวกัน — ภาระ sync ที่ระบบใหม่ (SBPGI) ควรทราบ
8. `evaluation-process` controller ประกาศ base path 16 แบบ / `cooperation-request` 3 แบบ — สะท้อนการไล่ compatibility กับ frontend หลายรุ่น
9. บั๊กย่อยที่ยืนยันจากโค้ด: validation Tel/Email ของ store-partner-contract ใช้ key ไม่ตรง header (ไม่เคยรัน), `AppConfig.import.maxRowCount` อ่านค่าจาก `IMPORT_MAX_FILE_SIZE` ผิดตัวแปร, `confirm-import` dropdown ร้าน hardcode เฉพาะ FES0003

---

*เอกสารนี้สรุปจากการอ่าน source code เท่านั้น — ตัวเลข "~" คือค่านับจากไฟล์จริง ณ commit ปัจจุบัน (594 ไฟล์ .ts ใน src, ~438 ไฟล์ไม่รวม spec, 31 modules, ~100 entity files, ~243 endpoints)*
