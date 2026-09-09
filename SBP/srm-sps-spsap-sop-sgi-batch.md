# srm-sps-spsap-sop-sgi-batch — เอกสารวิเคราะห์ Codebase

> สรุปจากการอ่าน source code จริงใน `/Users/bank_mac/gosoft/java/SBP/sbp-prototype/SBP/srm-sps-spsap-sop-sgi-batch`
> (branch `dev` · commit ล่าสุด `efef272` "fix bug" · 2026-08-31 · git remote `git@bitbucket.org:gosoft-thailand/srm-sps-spsap-sop-sgi-batch.git`)
> ข้อความใดที่เป็นการตีความจากชื่อ/บริบทจะระบุกำกับว่า "ตีความ"
> โฟลเดอร์โค้ดถูก **gitignore** เหมือน repo อื่นใน `SBP/` — clone ไว้อ่านอ้างอิงเท่านั้น ห้ามแก้

---

## 0. สรุปสำหรับคนรีบ — ทำไมไฟล์นี้สำคัญกับงานประกันรายได้

repo นี้ชื่อ **`sop-sgi-batch`** และเป็น **batch runner ของฝั่ง SBP ที่มีอยู่จริงและรันอยู่แล้ว** (42 job) — ไม่ใช่โปรเจกต์ใหม่ · สิ่งที่มันมีอยู่แล้วครบทั้ง 5 อย่างที่ชุด LLDD Job ของ SGI ต้องใช้:

| สิ่งที่ LLDD Job ของเราต้องใช้ | มีอยู่แล้วใน repo นี้ |
|---|---|
| batch runner + job dispatch | `src/main.ts` — `switch (jobName)` 42 เคส · เรียกด้วย `--job=<name>` / env `JOB_NAME` / AWS Batch argv |
| RabbitMQ publish | `src/modules/rabbitMQ/rabbitmq.service.ts` + `amqplib` · envelope `dataType/dataName/dataMessage/sender/sentAt` |
| S3 (EAI) | `src/shared/services/s3.service.ts` + `@aws-sdk/client-s3` (read/upload/copy/move/list) |
| ไฟล์ WINDOWS-874 / TIS-620 | `iconv-lite` + `StatementService.decodeThaiFileContent()` (auto-detect UTF-8 → fallback win874) |
| อีเมลกลาง | `@gosoft-sbp/email-lib` ^0.1.7 (+ entity `email_sent` / `email_template` ที่ lib เป็นเจ้าของ) |
| log การรัน interface | `integration_log` ผ่าน `StatementService.logInterfest()` — เรียกอัตโนมัติทุก job ที่ `main.ts` |

**ยังไม่มีอะไรของ SGI ในนี้เลย** — `grep` หา `sgi_` / `compensate` / "ประกันรายได้" ใน `src/` ได้ 0 ผลลัพธ์ · ชื่อ repo มี `sgi` แต่โค้ดปัจจุบันคือ FES / Statement / Reward / Master sync

✅ **มติ 2026-09-02 — Jobs 2–10 + 8b มา dev บน repo นี้** (เดิมชุด LLDD ชี้ไป `store-backend` + สร้าง `src/batch/sgi/*` ใหม่ทั้งชุด) · เอกสาร LLDD ทั้ง 10 ฉบับถูก regenerate ตามนี้แล้ว:

- job ชื่อ **`sgi-<kebab>`** ลงทะเบียนใน `src/main.ts` (เช่น `sgi-import-impact-store`) · โค้ดวางใต้ **`src/modules/sgi/`**
- argument เป็น **JSON ผ่าน `INPUT`** — local ใช้ env `JOB_NAME`/`INPUT` · AWS Batch ใช้ `argv[3]`/`argv[2]`
- **ตารางเวลา = AWS Batch scheduled event** ไม่ใช่ `@Cron`
- ทุกฉบับมีหัวข้อใหม่ **5.95 การลงทะเบียน job และ Arguments** และ **5.96 เงื่อนไขตัดสิน (Decision Rules)**

---

## 1. ภาพรวม

| รายการ | ค่า |
|---|---|
| ชื่อ package | `export-grade-to-ias` v1.0.0 (**ชื่อไม่ตรงกับ repo** — ตั้งจาก job แรกที่เขียน) |
| description | "FES modules - Export Grade, FES Reminder, Import Bank Account, Reward Division, Reward The Best (NestJS)" |
| Framework | NestJS 11 (`createApplicationContext` — **ไม่เปิด HTTP server**) · TypeScript ES2023 |
| ORM / DB | TypeORM 11 + PostgreSQL · schema เริ่มต้น `sps_store` (`DB_SCHEMA`) |
| Runtime | Docker `node:20-alpine` · TZ `Asia/Bangkok` · non-root `appuser` · `dumb-init` · `CMD node dist/main.js` |
| Deploy | **AWS Batch** (อ่าน `AWS_BATCH_JOB_ID`, argv) — CI/CD Bitbucket Pipelines template ของทีม SCM (`*-batch-pipeline`) |
| ขนาด | 179 ไฟล์ (ไม่นับ node_modules) · 14 module · 37 service · 28 spec · 30 entity · ~14,300 บรรทัดในไฟล์ service |

`index.js` ที่ root เป็น **stub ตัวอย่าง AWS Batch** (sleep + log) ไม่ได้ถูกใช้จริง — entry point จริงคือ `dist/main.js`

---

## 2. Tech Stack (จาก `package.json`)

**ที่เกี่ยวกับงาน SGI โดยตรง**

| lib | เวอร์ชัน | ใช้ทำอะไร |
|---|---|---|
| `@srm/glb-workflow` | ^1.1.26 | **ประกาศเป็น dependency แต่ยังไม่ถูก import ที่ไหนใน `src/`** — เตรียมไว้ (ตีความ) |
| `@srm/glb-log` | ^2.0.2 | logger กลาง — `src/common/logger.ts` (`createLogger`, `logger.child({module})`) |
| `@gosoft-sbp/email-lib` | ^0.1.7 | ส่งอีเมล + entity `email_sent` / `email_template` |
| `amqplib` | ^0.10.9 | RabbitMQ publisher |
| `@aws-sdk/client-s3` | ^3.1009.0 | EAI S3 |
| `iconv-lite` | ^0.7.2 | WINDOWS-874 / TIS-620 |
| `@nestjs/schedule` | ^6.0.0 | ประกาศไว้ แต่ **ไม่มี `@Cron` ที่ไหนในโค้ด** — ตารางเวลามาจาก AWS Batch ข้างนอก |

**อื่น ๆ**: `exceljs`, `pdf-lib` + `@pdf-lib/fontkit`, `decimal.js`, `dayjs`, `lodash`, `axios`, `class-validator`/`class-transformer`, `dotenv`
**Test**: Jest + `jest-junit` (`npm run test:ci` มี coverage + SonarQube)

---

## 3. รูปแบบการรัน job (สำคัญที่สุด)

`src/main.ts` — bootstrap เดียวรองรับทั้ง local และ AWS Batch:

```
isLocal = !process.argv[3]
jobName = isLocal ? process.env.JOB_NAME : process.argv[3]
rawInput = isLocal ? process.env.INPUT  : process.argv[2]   // JSON string
runId  = process.env.AWS_BATCH_JOB_ID ?? randomUUID()
```

ลำดับการทำงาน:

1. `NestFactory.createApplicationContext(AppModule)` (ไม่เปิดพอร์ต)
2. log `BATCH_START` (`event`, `runId`, `jobname`, `batchStatus`)
3. **บันทึกทุก job ลง `integration_log`** ผ่าน `StatementService.logInterfest(jobName, input)` — ล้มเหลวแล้ว log warn ไม่ล้ม job
4. `switch (jobName)` → **dynamic `import()` service ของ job นั้นตัวเดียว** แล้ว `app.get(Service).execute(...)`
5. log `BATCH_END` (`SUCCESS` / `FAILED` + `durationMs`) → `app.close()` → `process.exit(0|1)`
6. `default:` = `Unknown job` → `exit(1)` · ไม่ระบุ `jobName` = "API mode" (ไม่ทำอะไร)

> **ข้อสังเกต:** ไม่มี distributed lock (`pg_try_advisory_lock`) ที่ไหนใน repo — การกันรันซ้ำเป็นหน้าที่ของ AWS Batch queue ไม่ใช่โค้ด · ต่างจากที่ LLDD Job ของ SGI ระบุไว้ว่าจะล็อกด้วย `pg_try_advisory_lock`

**42 job ที่มีอยู่** (ตามลำดับใน `switch`):

| กลุ่ม | job |
|---|---|
| FES / เกรดร้าน | `fes-reminder` · `export-grade` · `autoconfirm-grade` |
| Reward | `reward-division` · `reward-division-recalculate` · `reward-the-best` |
| Statement / SAP | `sap-statement-expsub` (+`-summary`) · `sap-statement-pl-sbp` (+`-count`) · `sap-statement-pl-subarea` (+`-summary`) · `sta-statement-summary` · `delete-franchise-statement` · `export-statement-ptt` · `import-statement-ej` · `export-subarea-ej` |
| อีเมล statement | `email-sbp-statement` · `email-subarea-sta-statement` · `email-subarea-statement` · `email-sap-statement` · `email-etax-statement` |
| นำเข้า | `import-bank` · `import-add-expense` · `import-sub-area` · `import-monthly-avg-sales` · **`import-qssi`** |
| Master sync | `sta-taxpayer` · `sta-contact-acc` · `sta-skip-store` · `mms-store-main` · `mms-store-merge` · `oas-store-amphur` · `oas-store-province` · `oas-store-org-bellinee` · `oas-store-org-subarea` · `manage-business-user-group` |
| Cooperation | `update-cooperation-approver` · `auto-complete-cooperation` · `alert-mail-cooperation-on-process-daily` · `send-mail-cooperation-on-process-weekly` |

### ⚠️ `import-qssi` มีอยู่แล้วในนี้

`src/modules/performance/import-qssi.service.ts` (~530 บรรทัด) — อ่านไฟล์ QSSI, decode ไทย, insert `tmp` แล้ว transaction ลง `fcs_qssi_score`, ส่งเมลสำเร็จ/ล้มเหลว
**ยืนยันมติ 2026-08-24 ที่ตัด Job 1 ImportQSSI ออกจากขอบเขต SGI** — ระบบเดิมนำเข้าให้แล้วจริง และนี่คือโค้ดที่ทำ

---

## 4. RabbitMQ — รูปแบบบ้านนี้ (สำคัญกับสัญญา STA)

### 4.1 ตัว publisher

`src/modules/rabbitMQ/rabbitmq.service.ts` — ฟังก์ชันเดียว ไม่ใช่ NestJS provider:

```ts
publishMessage(urls, exchange, routingKey, payload, exchangeType = 'topic')
```

- `assertExchange(exchange, 'topic', { durable: true })`
- `publish(..., { persistent: true, contentType: 'application/json', contentEncoding: 'utf-8' })`
- **เปิด connection + channel ใหม่ทุกครั้ง แล้วปิดใน `finally`** (ไม่มี connection pool / publisher confirm)
- error ถูก `throw` ต่อ แต่ผู้เรียกทุกรายห่อด้วย `try/catch` แล้ว log อย่างเดียว → **ส่งไม่สำเร็จไม่ทำให้ job fail**

### 4.2 Envelope มาตรฐาน (`docs/rabbitmq-master-payload-spec.md`)

```json
{
  "dataType": "message",
  "dataName": "<ชื่อชุดข้อมูล>",
  "dataMessage": [ ...records... ],
  "sender": "sop-sgi-batch",
  "sentAt": "2026-03-29T10:00:00.000Z"
}
```

**ตรงกับ envelope ในสเปกของทีม STA** (`STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md`) ทุกฟิลด์ — ยืนยันว่าเป็นมาตรฐานเดียวกันทั้งบ้าน

### 4.3 การตั้งค่า — แยก "ช่อง" ต่อปลายทาง

`src/config/config.ts` มี 2 ชั้น:

```ts
export const rabbitMQConfig = {                       // ช่อง default
  url:        process.env.RABBITMQ_URL          ?? 'amqp://localhost:5672',
  exchange:   process.env.RABBITMQ_EXCHANGE     ?? 'sbp.master.exchange',
  routingKey: process.env.RABBITMQ_ROUTING_KEY  ?? 'sbp.master.sync',
};

export const rabbitMQPublisherChannels = {            // ช่องเฉพาะปลายทาง
  storeBellinee: { url, exchange: 'sps.store.master', exchangeType: 'topic',
                   routingKey: 'sps.store.master.store-bellinee',
                   queueName:  'srm.sps.store-bellinee.queue',
                   dataName:   'sps_store_bellinee' },
  orgSubarea:    { ... exchange: 'oas.store.master', routingKey: 'oas.store.master.org.subarea',
                   queueName: 'srm.sps.org.subarea.queue', dataName: 'oas_store_org_subarea' },
};
```

env pattern: `RABBITMQ_<CHANNEL>_URL / _EXCHANGE / _EXCHANGE_TYPE / _ROUTING_KEY / _QUEUE / _DATA_NAME`

> **นี่คือคำตอบของข้อค้างเรื่อง routing key ของ SGI**: บ้านนี้แยก **routing key** (คีย์ที่ queue bind) ออกจาก **`dataName`** (ชื่อชุดข้อมูลใน payload) เป็นคนละ config key
> ⇒ `sta.compensation.result` (routing key ที่เราตั้งไว้) กับ `sgi_impact_store` (`dataName` ตามสเปก STA) **อยู่ร่วมกันได้ ไม่ได้ขัดกัน** — แต่ต้องประกาศเป็นช่องใหม่ (เช่น `RABBITMQ_STA_SGI_*`) และยืนยัน routing key/queue กับทีม STA เพราะเขาเป็นเจ้าของ queue ที่ bind
> ยังไม่มีตัวอย่าง **consumer** ใน repo นี้ — ทุกช่องเป็น publisher อย่างเดียว (ตรงกับที่ชุด LLDD ยังไม่มีฉบับรับ `sta_update_compensate`)

### 4.4 ตัวอย่างการเรียกจริง (`src/modules/master/tax-payer.service.ts`)

```ts
await publishMessage(rabbitMQConfig.url, rabbitMQConfig.exchange, rabbitMQConfig.routingKey, {
  dataType: 'message', dataName: 'sta_taxpayer',
  dataMessage: result.entities || [],
  sender: 'sop-sgi-batch', sentAt: new Date().toISOString(),
});
```

ผู้เรียก `publishMessage` ทั้งหมดอยู่ใน `src/modules/master/` (province, amphur, tax-payer, contact-acc, store-type-bellinee, store-info-bellinee, store-organize-bellinee, …) — ปลายทางคือ `store-backend` ให้ sync master data

---

## 5. Database

`src/database/typeorm.config.ts`:

- `type: 'postgres'` · `synchronize: false` · `logging` เฉพาะ `NODE_ENV=dev`
- **entities โหลด 2 แหล่ง**: `src/**/*.entity.ts` + `node_modules/@gosoft-sbp/email-lib/dist/**/*.entity.js` และ **register class `EmailSent`/`EmailTemplate` ของ lib ตรง ๆ** (คอมเมนต์ในไฟล์เตือนว่าประกาศ entity ท้องถิ่นชื่อตารางเดียวกันจะไม่ทำงาน)
- รองรับทั้ง single DB และ **replication (master/slaves)** เลือกจาก `config.db.replication`
- SSL เปิดเมื่อ `APP_ENV ∈ {production, uat, dev}`
- pool: `max`/`min`/`idleTimeoutMillis`/`connectionTimeoutMillis`/`statement_timeout`/`idleInTransactionSessionTimeout` ตั้งได้จาก env
- migrations: `src/database/migrations/*`

**30 entity** — กลุ่มหลัก: statement (`fml_sbp_stmt`, `fml_stmt_trans`, `fml_stmt_end`, `statement`, `statement_summary`, `temp_*`), master (`store`, `mas_zone`, `province`, `amphur`, `mas_taxpayer`, `mas_contact`, `common_code`, `system_param`), FCS (`fcs_monthly_sales`, `fcs_audit_costs`), MMS (`mms_store_trans`, `mms_store_merge_trans`), infra (`integration_log`, `import_job_status`, `email_sent`, `email_template`)

**ไม่มี entity ของ `sgi_*` เลย** — ถ้า Jobs ของ SGI มาอยู่ที่นี่ ต้องเพิ่มทั้ง 19 ตาราง (หรือเฉพาะที่ job แต่ละตัวใช้)

---

## 6. โครงสร้าง `src/`

```
src/
├── main.ts                 job dispatcher (switch 42 เคส) + BATCH_START/END log
├── app.module.ts
├── common/logger.ts        @srm/glb-log — logger.child({ module })
├── config/config.ts        ~250 บรรทัด · export const แยกเป็นกลุ่ม ๆ (ไม่ใช้ registerAs)
├── database/typeorm.config.ts
├── entities/               30 entity
├── shared/services/s3.service.ts
├── types/index.ts
├── __tests__/
└── modules/                14 module
    ├── rabbitMQ/           publishMessage()
    ├── statement/          ใหญ่สุด — export-ptt 969, exp-sub 963, email-statement 888, pre-statement 887 บรรทัด + logInterfest() + decodeThaiFileContent()
    ├── master/             import/sync master + publish RabbitMQ (import-seven-shop 821 บรรทัด)
    ├── performance/        import-qssi · import-monthly-avg-sales
    ├── reward-division/    1,567 บรรทัด (ใหญ่สุดในไฟล์เดียว)
    ├── reward-the-best/ · export-grade/ · fes-reminder/ · import-bank/ · autoconfirm-grade/
    ├── cooperation-approver/ · auto-complete-cooperation/
    └── alert-mail-cooperation-on-process-daily/ · send-mail-cooperation-on-process-weekly/
```

`src/config/config.ts` แตกเป็น `export const` ต่อโดเมน: `appConfig`, `mail*Config` (~10 ตัว), `importBankConfig`, `exportGradeConfig`, `s3Bank`, `s3Grade`, `rewardConfig`, `awsConfig`, `cmConfig`, `rabbitMQConfig`, `rabbitMQPublisherChannels`, `importMonthlyAvgSalesConfig` — **ไม่ใช้ `registerAs` ของ `@nestjs/config`** (แบบเดียวกับ store-backend)

---

## 7. S3 (`src/shared/services/s3.service.ts`)

`@Injectable() S3Service` — `readFile` · `uploadFile` · `copyFile` · `deleteFile` · `moveFile` · `listFiles(bucket, prefix)`
โมเดลการใช้งานที่มีอยู่ (`import-bank`): เลือกได้ระหว่าง local filesystem กับ S3 ผ่าน `BANK_STORAGE_TYPE=local|s3` + `BANK_S3_BUCKET` / `BANK_S3_PREFIX` / `BANK_S3_BACKUP_PREFIX`

**ตรงกับที่ Job 4/5 ของ SGI ต้องการ** (อัปโหลด `AMS06001O_` → prefix ขาออก · ดึง `AMS06001I_` จาก prefix ขาเข้า → ย้ายไป prefix backup)

---

## 8. Environment Variables (`.env.example`)

กลุ่มที่ใช้ซ้ำได้กับ SGI:

| กลุ่ม | ตัวอย่าง key |
|---|---|
| DB | `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` `DB_NAME` (+ `DB_SCHEMA` ในโค้ด, default `sps_store`) |
| ไฟล์ interface | `OUTPUT_PATH` `BACKUP_PATH` `FILE_NAME_PATTERN` `FILE_EXTENSION` `FILE_ENCODING=TIS-620` |
| S3 | `BANK_STORAGE_TYPE` `BANK_S3_BUCKET` `BANK_S3_PREFIX` `BANK_S3_BACKUP_PREFIX` `AWS_REGION` |
| RabbitMQ | `RABBITMQ_URL` `RABBITMQ_EXCHANGE` `RABBITMQ_ROUTING_KEY` + ชุดต่อช่อง `RABBITMQ_<CH>_*` |
| อีเมล | `SMTP_HOST=tarmg.cpall.co.th` `SMTP_PORT=25` `MAIL_FROM=noreply@cpall.co.th` + `*_MAIL_TEMPLATE` (เลข template ของ `email_template`) |
| Runtime | `NODE_ENV` `APP_ENV` (`dev`/`uat`/`prod` เปลี่ยนผู้รับเมล) `LOG_LEVEL` |
| **Test mode** | `TEST_MODE=true` `TEST_OVERRIDE_EMAIL` `TEST_MAIL_LIMIT` — กันส่งเมลหาลูกค้าจริงบน dev/uat |

> ⚠️ `.env.example` มี **อีเมลพนักงานจริงหลายรายและ SMTP host จริง** — ไม่ควรคัดลอกเข้าเอกสารส่งมอบ · ไฟล์ `.env` จริงไม่มีใน clone

`TEST_MODE` เป็นแพตเทิร์นที่ชุด LLDD ของเรายังไม่ได้ระบุ — ควรหยิบมาใช้กับ job ที่ส่งเมล/ส่ง MQ

---

## 9. ผลกระทบต่องานประกันรายได้ (SGI) — สิ่งที่ต้องตัดสิน

| # | ประเด็น | สถานะปัจจุบันในเอกสารของเรา | ข้อเท็จจริงจาก repo นี้ |
|---|---|---|---|
| 1 | **Jobs 2–10 + 8b จะไปอยู่ repo ไหน** | ✅ **ปิดแล้ว (มติ 2026-09-02)** — LLDD ทั้ง 10 ฉบับชี้มาที่ repo นี้แล้ว · job ชื่อ `sgi-<kebab>` ใน `src/main.ts` · โค้ดใต้ `src/modules/sgi/` · argument เป็น JSON ผ่าน `INPUT` | โครง runner/MQ/S3/encoding/email/`integration_log` reuse ได้ทันที |
| 2 | **ตารางเวลา** | ✅ ปิดแล้ว — LLDD ระบุชัดว่า cron เป็น **นิยามของ AWS Batch scheduled event** และ `SGI_JOB*_CRON` เก็บไว้เป็นเอกสารประกอบเท่านั้น | repo นี้ไม่มี `@Cron` เลย |
| 3 | **กันรันซ้ำ** | ⚠️ ยังค้าง — LLDD ยังระบุ `pg_try_advisory_lock` (ทำเครื่องหมาย **ของใหม่** แล้ว) | repo ไม่มี lock ใด ๆ · ต้องตัดสินว่าจะสร้างจริงหรือพึ่ง AWS Batch queue อย่างเดียว |
| 4 | **routing key ของ STA** | เราตั้ง `sta.compensation.result` · สเปก STA ระบุแค่ exchange `sgi.interface` + `dataName` | บ้านนี้แยก routing key กับ `dataName` เป็นคนละ config → ใช้ทั้งคู่ได้ แต่ต้อง confirm queue binding กับ STA |
| 5 | **consumer `sta_update_compensate`** | ไม่มี LLDD ฉบับไหนรองรับ (ช่องว่างที่รายงานไว้) | repo นี้มีแต่ publisher — ไม่มีตัวอย่าง consumer ให้ลอก ต้องออกแบบใหม่จริง |
| 6 | **Job 1 ImportQSSI** | ตัดออกจากขอบเขต (มติ 2026-08-24) | ✅ ยืนยันถูกต้อง — `import-qssi` ทำงานอยู่แล้วใน repo นี้ |
| 7 | **`@srm/glb-workflow`** | Job 8b เรียก `initializeWorkflow` / `addPreApprover` | ประกาศเป็น dependency แล้ว (^1.1.26) แต่ยังไม่มีโค้ดเรียก — ถ้ามาอยู่ที่นี่ Job 8b จะเป็นตัวแรกที่ใช้ |
| 8 | **ชั่วโมงประเมิน** | **182 ชม.** สำหรับ Jobs 2–10 + 8b (10 ฉบับ) · **211 ชม.** เมื่อรวม Job 11 + 12 ที่เพิ่ม 2026-09-02 (12 ฉบับ · รวม unit test) — *ตัวเลข 224 ที่เคยเขียนไว้ตกยุคแล้ว แก้ 2026-09-08* | reuse runner/MQ/S3/encoding/email/log ได้แล้ว งาน infra ต่อ job ลดลง แต่เพิ่มงานปิดช่องว่าง schema G1-G5 · ควรทบทวนตัวเลขพร้อมกันทีเดียว |

---

## 10. ข้อสังเกต / ความเสี่ยงของ codebase นี้

1. **ชื่อ package ไม่ตรง repo** (`export-grade-to-ias` vs `sop-sgi-batch`) และ description ยังพูดถึงแค่ 5 job แรก ทั้งที่มี 42 job
2. `main.ts` เป็น **god switch** ยาว ~600 บรรทัด — เพิ่ม job = แก้ไฟล์กลางทุกครั้ง (merge conflict ง่าย)
3. **RabbitMQ publish ล้มเหลวไม่ทำให้ job fail** (ทุกผู้เรียก `try/catch` + log) และ **ไม่มี publisher confirm / outbox** → ข้อความหายเงียบได้
   ⇒ ขัดกับที่ LLDD Job 6 ของเราระบุว่าใช้ **transactional outbox + publisher confirm + ACK** — ถ้ามาอยู่ repo นี้ต้องเพิ่มกลไกใหม่ ไม่ใช่ reuse ตรง ๆ
4. เปิด/ปิด connection RabbitMQ ทุกครั้งที่ publish — ไม่เหมาะกับการ publish จำนวนมาก (Job 6 ส่ง ~1,200 msg/วัน)
5. `tsconfig.json` ปิด `strictNullChecks` และ `strictBindCallApply`
6. `export-ptt-query-old-new.txt` และ `payload.json` วางอยู่ที่ root — ไฟล์งานชั่วคราวที่หลุดเข้า repo (ตีความ)
7. `index.js` stub ที่ไม่ได้ใช้ยังอยู่ ทำให้เข้าใจผิดว่าเป็น entry point
8. `.env.example` มีอีเมลพนักงานจริง + SMTP host จริง (ดูข้อ 8)
9. **ไม่มี README ที่อธิบายตัวระบบ** — `README.md` ทั้งไฟล์เป็นคู่มือตั้งค่า CI/CD variables ของทีม SCM เท่านั้น
10. มี `ai-behavior-bullet-mode.md` ที่ root (คู่มือสไตล์การตอบของ AI ไม่เกี่ยวกับระบบ)

---

## 11. ไฟล์อ้างอิงในโปรเจกต์นี้

- `SBP/srm-sps-spsap-store-backend.md` — BE หลัก (NestJS + TypeORM) ที่ LLDD ปัจจุบันชี้เป็น target ของ Jobs
- `SBP/srm-sps-spsap-sbp-bff.md` · `SBP/srm-sps-spsap-web-frontend.md`
- `SBP/SBPGI-vs-existing-system.md` — การเทียบตาราง/endpoint ของ SGI กับระบบเดิม
- `STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md` — สัญญาข้อความ 3 ชุดกับ STA (envelope ตรงกับ `docs/rabbitmq-master-payload-spec.md` ของ repo นี้)
- `LLDD/md/Jobs/*.md` — LLDD 10 ฉบับที่ต้องทบทวน target repository ตามข้อ 9
