# plan-be.md — Spec สร้าง Backend ระบบ SBPGI (Node.js) ฉบับละเอียด

> **spec สำหรับ AI/นักพัฒนา สร้าง Backend จริงโดยไม่ต้องถามเพิ่ม** อ่านคู่กับ: `checklist-be.md` (ลำดับงาน + เกณฑ์ตรวจรับต่อ Phase) · `api.md` + `plan-api.html` (สัญญา API 62 เส้น — **สัญญาผูกมัด** รวม SQL ตัวอย่างต่อเส้นใน `SQL_BY_PATH`) · `database.md` (schema 34 ตาราง) · `workflow.md` (flow 12 ขั้น + ตาราง transition) · `plan-fe.md`
>
> หลักการใหญ่: **รวม EAI + K2 เข้า SBPGI** — Document Service เขียน DB ตรง + Workflow Engine ภายใน (ไม่มีไฟล์ `BPM06001O_/2O_/3O_` และไม่มี K2 REST StartInstance) · interface ภายนอก (QSSI/ALLMAP/IAS/STA/SMTP) คงกลไกไฟล์/SFTP เดิม
>
> **กติกาเหล็ก (ห้ามเปลี่ยน):**
> - workflow **5 ขั้น 06→08→01→02→03** (ตัดขั้นบัญชี 04/05 ตาม SDD v7.5) · สถานะเอกสาร **6 ค่า**
> - กฎวงเงิน: ชดเชย/ไม่ชดเชย **> 100,000 → AVP (03) แล้วจบ** · ชดเชย **≤ 100,000 จบที่ GM (02)**
> - Error ทุกเส้นรูปเดียว `{code,message}` — ข้อความไทย **verbatim ตาม SRS**
> - เลขเอกสาร `พ.ศ./xxxxx` running ต่อปี จองด้วย `SELECT ... FOR UPDATE`
> - Gen Flow Gate **6 เกณฑ์** ครบทุกข้อ · Job 4 ครอบ transaction/outbox (**P0**)
> - **ห้ามเก็บ secret ใน DB/`system_configs`** — credential อยู่ `.env` (prod = Secret Manager)
> - กลุ่ม abnormal-stores 2 เส้น **skip** (comment รอตัดสินใจ — ทำแล้วจะเป็น 63 เส้น)

---

## 0. สัญญากลาง BE/API Common Contracts

> LLDD อ้างอิง: `LLDD/BE/LLDD-BE-API-Common-Contracts.md` + `LLDD/FE/LLDD-FE-Integration-Contracts.md` · ทุก route/controller/service ต้องยึดสัญญานี้ก่อนอ่านรายละเอียด endpoint รายตัวใน `api.md`/`plan-api.html`

| หมวด | Contract ที่ BE ต้อง enforce |
|---|---|
| Transport | Base URL `/api/v1`; JSON `application/json; charset=utf-8`; multipart เฉพาะ attachments; logging ต้องมี request id (`X-Request-Id` ถ้าส่งมา ไม่ส่งให้ generate) |
| Auth | User endpoint ใช้ `Authorization: Bearer <JWT>` จาก platform reference; `POST /workflows/instances` ใช้ service token; `POST /interfaces/sta/ack` ใช้ `X-Api-Key` |
| Error | error handler คืน `{code,message}` เท่านั้น; ห้าม endpoint คืน shape อื่น; SRS popup text ต้องอยู่ใน `lib/messages.ts` เพื่อเทียบ verbatim จุดเดียว |
| HTTP status | 400 validation · 401 auth · 403 forbidden/RBAC · 404 not found · 409 duplicate/current-task/job-running conflict · 422 business rule · 413 file too large · 415 unsupported file |
| Pagination | GET list ทุกเส้นใช้ `page,size` และคืน `{page,size,total,items}`; default size 20, max 100 |
| Format | `docNo` = พ.ศ. `YYYY/xxxxx`; `storeCode/newStoreCode` เป็น string 5 หลัก; date/month payload เป็น ISO ค.ศ.; amount/percent validate เป็น number 2 decimals |
| Workflow transition | `/documents/{docNo}/actions` รับ `{result,comment}` เท่านั้น; `result` เป็น 6-enum ไทย verbatim; service lookup transition จาก `section+result+amountFlag`; response `{nextSection,statusCode,status}` |
| RBAC/Menu | BE เป็น source of truth ของ role/menu/current task owner; `/me/menus` คืนสิทธิ์ sidebar; detail API คืน `permissions.canEditSections`/`canAction` |
| Audit/Reason | master/config/email/RBAC mutation ต้อง validate `reason` และเขียน `audit_logs` ใน transaction เดียว; workflow action เขียน `consideration_logs`; batch เขียน `job_run_histories` |
| Idempotency | endpoint จาก job/service ใช้ `requestId` หรือ business key; duplicate ต้องคืน existing result หรือ 409 ตามกฎ endpoint |

## 1. Stack และเวอร์ชัน (ตัดสินใจแล้ว — คงเดิม ห้ามสลับ)

| ส่วน | เลือกใช้ | เหตุผล / ข้อกำหนด |
|---|---|---|
| Runtime | **Node.js >= 20** + **TypeScript** (`strict: true`) | ตามโจทย์ |
| Framework | **Express 4** + โครง layered (route → controller → service → repository) | ตรงไปตรงมา ทีมคุ้นเคย |
| DB | **PostgreSQL 16** | 34 ตาราง ใช้ transaction/constraint หนัก |
| Query | **Prisma ORM** (`schema.prisma` = source of truth ของ 34 ตาราง) + `$queryRaw` เฉพาะรายงาน/dashboard (ตัวอย่างใน `SQL_BY_PATH`) | migration + type-safety |
| Validation | **zod** ต่อ endpoint (body/query/params) — schema อยู่ `*.schema.ts` | error message ไทยตาม SRS |
| Auth | **jsonwebtoken** — access 30 นาที / refresh 8 ชม. · **bcrypt** cost ≥ 10 | ตาม api.md |
| Scheduler | **node-cron** (in-process) — cron ต่อ job อ่านจาก `job_configs` | Jobs 1–10 |
| ไฟล์/SFTP | **ssh2-sftp-client** (QSSI/STA) · **mssql** (ALLMAP read-only) · **iconv-lite** (WINDOWS-874/TIS-620) | interface เดิม |
| Email | **nodemailer** (SMTP, UTF-8) — template จาก `email_templates` (EM-01–08) | Notification Service |
| Upload | **multer** (memory) → disk `storage/attachments/` + แถว `document_attachments` | ≤ 5MB + ext whitelist |
| Log | **pino** (JSON) + request id + redact | |
| Test | **vitest** + **supertest** (+ postgres จริงสำหรับ integration) | coverage `workflow/` ≥ 90% |
| Doc | `openapi.yaml` เขียนมือจาก api.md — ต้อง sync 62 เส้น | |

เครื่องมือคุณภาพ (Phase 0): **husky + lint-staged + commitlint** (Conventional Commits) · **GitHub Actions CI**: `lint → tsc --noEmit → prisma validate → test → build` (postgres service container) · path alias `@/` = `src/`

## 2. โครงสร้างโฟลเดอร์ (บังคับ — module-per-domain + layered)

หลักการชั้น (dependency ทางเดียว): `routes → controller → service → repository → prisma`
- **controller**: แปลง HTTP ↔ DTO เท่านั้น — **ห้ามมี business logic**
- **service**: business logic + transaction ทั้งหมด — **ห้ามแตะ req/res**
- **repository**: query Prisma/raw SQL เท่านั้น — คืน entity ไม่คืน DTO
- ข้าม module ได้เฉพาะชั้น **service** (documents.service → notification.service ได้ · ห้ามข้ามไป repo ของ module อื่น)
- zod schema = source of truth ของ DTO (`export type X = z.infer<typeof xSchema>`)

```
sbpgi-be/
  prisma/schema.prisma          # 34 ตาราง 3 โซน + enum ทุกตัว — แปลงตรงจาก database.md
  prisma/seed.ts                # §10 — idempotent (upsert)
  storage/                      # attachments/ exports/ (volume แยก — stateless app)
  src/
    server.ts  app.ts           # bootstrap · helmet+cors+pino-http+errorHandler · graceful shutdown
    config/env.ts               # zod-validate .env — fail fast (§7.1)
    middlewares/
      auth.ts                   # Bearer JWT → req.user (§7.3)
      requireRole.ts            # 403 ถ้า role ไม่อยู่ใน whitelist
      validate.ts               # zod → 400 {code:"VALIDATION", message}
      errorHandler.ts           # AppError → {code,message} (§7.2)
      serviceToken.ts           # header Authorization: Bearer <SERVICE_TOKEN> (Job 8b → /workflows/instances)
      apiKey.ts                 # header X-Api-Key (STA callback)
    modules/
      auth/  tasks/  documents/  lookup/  masters/  configs/
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

- Base `/api/v1` · JSON UTF-8 · Bearer JWT ทุกเส้น **ยกเว้น**: `POST /auth/login`, `POST /auth/refresh` (public) · `POST /workflows/instances` (service token) · `POST /interfaces/sta/ack` (`X-Api-Key`)
- Pagination: `?page=1&size=20` → `{page,size,total,items}` (default size 20 · max 100)
- วันที่ใน payload = ISO-8601 ค.ศ. (FE แปลง พ.ศ.) — ยกเว้นเลขเอกสารและไฟล์ interface ที่เป็น พ.ศ.
- ทุกเส้นที่แก้ข้อมูลบันทึกผู้ทำจาก JWT ลง audit ตามโดเมน (consideration_logs / audit_logs / job_run_histories)

**Error รูปเดียวทั้งระบบ** `{"code":"...","message":"<ไทย verbatim ตาม SRS>"}` — โยน `AppError` แล้ว errorHandler แปลง:

| HTTP | code | ใช้เมื่อ | ตัวอย่าง message (verbatim ที่ SRS กำหนด) |
|---|---|---|---|
| 400 | `VALIDATION` | zod fail / กติกาธุรกิจ input | `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ` |
| 400 | `DOC_PERCENT_400` | %ชดเชยรวม ≠ 100% | `เปอร์เซ็นต์ชดเชยรวมทุกร้านต้องเท่ากับ 100%` |
| 400 | `REPORT_YEAR_400` | ไม่ส่งปี (พ.ศ.) ใน /documents, /reports | `กรุณาระบุปีที่ต้องการค้นหา` |
| 401 | `AUTH_401` | login ผิด / token หมดอายุ/ปลอม / API key ผิด | `ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง` |
| 403 | `FORBIDDEN` | role ไม่มีสิทธิ์ / section ≠ current / is_system / is_editable=false | |
| 404 | `NOT_FOUND` | ไม่พบ resource | |
| 409 | `CONFLICT` | factor_code ซ้ำ · ร้าน+งวดซ้ำ · action บนเอกสารจบแล้ว · job รันซ้อน | |
| 422 | `BUSINESS_RULE` | ข้อมูลครบเชิง schema แต่ไม่ผ่าน business rule เช่น Gen Flow Gate ยังไม่พร้อม / transition ใช้ไม่ได้ | |
| 413 | `FILE_TOO_LARGE` | ไฟล์แนบเกิน 5MB | |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | นามสกุล/ชนิดไฟล์แนบไม่อยู่ใน whitelist | |
| 429 | `RATE_LIMIT` | login เกิน limit | |
| 500 | `INTERNAL` | error ไม่คาดคิด (log เต็ม · ไม่ leak stack) | |

> ข้อความไทยทุกตัวรวมศูนย์ที่ `lib/messages.ts` (const object) — ห้าม hardcode กระจายตามไฟล์ เพื่อให้เทียบ verbatim กับ SRS ได้จุดเดียว

## 4. ตาราง endpoint ครบ 62 เส้น (สัญญาผูกมัด — path/method ห้ามเปลี่ยน)

สิทธิ์: `ทุก role` = JWT ใดก็ได้ · `01,03` = Admin/User Admin · `section` = ผู้เรียกต้องเป็น section ปัจจุบันของเอกสาร · `svc` = SERVICE_TOKEN · `key` = X-Api-Key
ตาราง R = อ่าน · W = เขียน · SQL แนวทางต่อเส้น = `SQL_BY_PATH['METHOD path']` ใน `plan-api.html`

### กลุ่ม 1 · Auth (4 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 1 | POST `/auth/login` | public/platform callback | R: user_accounts, employees, roles | credential ตรวจโดย platform SSO/AD/LDAP; รับ employee identity ที่ยืนยันแล้ว · local account inactive → 403 |
| 2 | POST `/auth/refresh` | public | — (JWT) | refresh หมดอายุ/ปลอม → 401 |
| 3 | GET `/auth/me` | ทุก role | R: user_accounts, employees, roles | ไม่มี token → 401 |
| 4 | GET `/me/menus` | ทุก role | R: menu_permissions, menus | คืนเฉพาะ `can_access=true` ของ role ผู้เรียก |

### กลุ่ม 2 · งาน & เอกสาร (10 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 5 | GET `/tasks` | ทุก role | R: workflow_tasks, compensation_documents | inbox = task เปิดของ section ที่ map กับ role · paginate |
| 6 | GET `/documents` | ทุก role | R: compensation_documents | **ไม่ส่งปี พ.ศ. → 400 REPORT_YEAR_400** · filter สถานะ/ร้าน/งวด |
| 7 | GET `/documents/{docNo}` | ทุก role | R: compensation_documents + ลูกทั้งชุด | ไม่พบ → 404 · คืนธง `editableSections`/`myRoleView` ต่อ role-section |
| 8 | POST `/documents` | 00,01,06(section 06) | W: compensation_documents, document_new_stores, workflow_instances, workflow_tasks, doc_no_counters | MANUAL/FS · ร้าน+งวดซ้ำ → 409 · transaction เดียว (ออกเลข+instance+task 06) |
| 9 | PUT `/documents/{docNo}` | section | W: document_new_stores, document_competitors, document_external_factors | section ≠ current → 403 · **%ชดเชยรวม ≠ 100% → 400 DOC_PERCENT_400** |
| 10 | POST `/documents/{docNo}/actions` | section | W: compensation_documents, workflow_tasks, consideration_logs | ไม่ส่ง result → 400 verbatim · result ไม่ชดเชยไม่มี comment → 400 · เอกสารจบแล้ว → 409 · section ≠ current → 403 |
| 11 | GET `/documents/{docNo}/timeline` | ทุก role | R: consideration_logs | เรียงเวลา |
| 12 | POST `/documents/{docNo}/attachments` | section | W: document_attachments | > 5MB / ext นอก whitelist → 400 |
| 13 | GET `/documents/{docNo}/sales` | ทุก role | R: sales_transactions, fgi_impact_sales_summaries | 4 หน้าต่าง × 15 วัน ผ่าน impact_process_id |
| 62 | GET `/documents/{docNo}/attachments/{attachId}/download` | ทุก roleที่อ่านเอกสารได้ | R: document_attachments | attachment ต้องเป็นของ docNo และ scan_status=CLEAN |

### กลุ่ม 3 · Lookup (4 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 14 | GET `/stores/search` | ทุก role | R: stores / impacted_stores | `type=impacted\|new` บังคับ — อื่น/ไม่ส่ง → 400 |
| 15 | GET `/competitors` | ทุก role | R: competitors | master 24 ราย |
| 16 | GET `/document-statuses` | ทุก role | R: document_statuses | **6 ค่า** (เฉพาะ active) |
| 17 | GET `/workflow-sections` | ทุก role | R: workflow_sections | **5 ขั้น** (ไม่รวม 04/05 is_active=false) |

### กลุ่ม 4 · Masters (19 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 18 | GET `/operators` | 01,03 | R: operator_assignments, employees | filter section/zone · paginate |
| 19 | POST `/operators` | 01,03 | W: operator_assignments | employee_id ไม่มีจริง → 400 |
| 20 | PUT `/operators/{id}` | 01,03 | W: operator_assignments, audit_logs | **ไม่ส่ง reason → 400** |
| 21 | DELETE `/operators/{id}` | 01,03 | W: operator_assignments, audit_logs | reason บังคับ |
| 22 | GET `/employees/search` | 01,03 | R: employees | popup 3.1.8 · `q` บังคับ |
| 23 | GET `/factors` | ทุก role | R: external_factors | |
| 24 | POST `/factors` | 01,03 | W: external_factors | **factor_code ซ้ำ → 409** message ไทยตาม SRS |
| 25 | PUT `/factors/{code}` | 01,03 | W: external_factors, audit_logs | reason บังคับ |
| 26 | DELETE `/factors/{code}` | 01,03 | W: external_factors, audit_logs | มี document_external_factors อ้าง → 409 |
| 27 | GET `/menu-permissions` | 01,03 | R: menu_permissions, menus, roles | matrix 8 role × เมนู |
| 28 | PUT `/menu-permissions/{menuCode}` | 01,03 | W: menu_permissions, audit_logs | reason บังคับ |
| 29 | GET `/roles` | 01,03 | R: roles | |
| 30 | POST `/roles` | 01,03 | W: roles, menu_permissions | สร้างแถวสิทธิ์ `can_access=false` ทุกเมนูอัตโนมัติ |
| 31 | PUT `/roles/{roleCode}` | 01,03 | W: roles, audit_logs | `is_system=true` แก้รหัส → 403 · reason บังคับ |
| 32 | DELETE `/roles/{roleCode}` | 01,03 | W: roles, menu_permissions (cascade), audit_logs | is_system → 403 |
| 33 | POST `/menus` | 01,03 | W: menus, menu_permissions | สร้างสิทธิ์ false ทุก role |
| 34 | PUT `/menus/{menuCode}` | 01,03 | W: menus, audit_logs | is_system กันแก้รหัส · reason บังคับ |
| 35 | DELETE `/menus/{menuCode}` | 01,03 | W: menus, menu_permissions (cascade), audit_logs | |
| 36 | GET `/audit-logs` | 01,03 | R: audit_logs | filter table/refKey · paginate |

### กลุ่ม 5 · System Config (5 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 37 | GET `/configs` | 01,03 | R: system_configs | filter category |
| 38 | GET `/configs/{key}` | ทุก role | R: system_configs | cache 5 นาที |
| 39 | POST `/configs` | 01,03 | W: system_configs, audit_logs | validate ตาม value_type → 400 · **key หน้าตา secret (password/secret/token) → 400** |
| 40 | PUT `/configs/{key}` | 01,03 | W: system_configs, audit_logs | `is_editable=false` → 403 · reason บังคับ · invalidate cache ทันที |
| 41 | DELETE `/configs/{key}` | 01,03 | W: system_configs, audit_logs | is_editable=false → 403 |

### กลุ่ม 6 · Email Templates (5 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 42 | GET `/email-templates` | 01,03 | R: email_templates | 8 template EM-01–08 |
| 43 | GET `/email-templates/{code}` | 01,03 | R: email_templates, status_email_rules | |
| 44 | PUT `/email-templates/{code}` | 01,03 | W: email_templates, audit_logs | แก้ได้เฉพาะ subject/body (From/To/Cc ล็อกตาม rules) · reason บังคับ |
| 45 | POST `/email-templates/{code}/reset` | 01,03 | W: email_templates, audit_logs | คืน default_subject/default_body |
| 46 | POST `/email-templates/reset-all` | 01,03 | W: email_templates, audit_logs | |

### กลุ่ม 7 · รายงาน (2 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 47 | GET `/reports/status-summary` | 01,04,06 | R: compensation_documents, consideration_logs, document_new_stores | **ปี พ.ศ. required → 400** · filter: status(6) · result(ประกันรายได้/ไม่ประกันรายได้ จาก result_category ล่าสุด) · region(13 รหัส) · storeType(A–D multi) · impactedStoreCode · newStoreCode · เฉพาะรายการมีเลขเอกสาร |
| 48 | GET `/reports/status-summary/export` | 01,04,06 | R: เดียวกับ 47 + W ไฟล์ `storage/exports/` | CSV UTF-8 **มี BOM** + Content-Disposition |

### กลุ่ม 8 · Batch Job Admin (6 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 49 | GET `/jobs` | 01,03 | R: job_configs, job_run_histories | 11 entry points + สถานะล่าสุด |
| 50 | GET `/jobs/{jobNo}` | 01,03 | R: job_configs | |
| 51 | PUT `/jobs/{jobNo}/params` | 01,03 | W: job_configs, audit_logs | แก้ตัว non-editable → 400 |
| 52 | PUT `/jobs/{jobNo}/enabled` | 01,03 | W: job_configs, audit_logs | |
| 53 | POST `/jobs/{jobNo}/run` | 01,03 | W: job_run_histories + ตารางตาม job | **รันซ้อน (มีแถว RUNNING) → 409** |
| 54 | GET `/jobs/{jobNo}/runs` | 01,03 | R: job_run_histories | paginate |

### กลุ่ม 9 · Workflow ภายใน (3 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 55 | POST `/workflows/instances` | svc | R/W: fgi_impact_processes, impacted_stores, stores, fgi_impact_stores, fgi_impact_sales_summaries; W: workflow_instances, workflow_tasks | **Gen Flow Gate W/Y/N** — status source of truth อยู่ fgi_impact_processes; ผ่านตอบ Y; branch type นอกเซ็ตตั้ง N; ข้อมูลยังไม่พร้อมคง W + 422/reason · token ผิด → 401 |
| 56 | GET `/workflows/instances/{id}` | ทุก role | R: workflow_instances, workflow_tasks | 404 ถ้าไม่พบ |
| 57 | GET `/workflows/summary` | 01,03 | R: fgi_impact_processes, workflow_tasks | ตัวเลข W/Y/N + งานค้างต่อ section |

### กลุ่ม 10 · Interface & Dashboard (4 เส้น)
| # | Method Path | สิทธิ์ | ตาราง (R/W) | Validation / Error |
|---|---|---|---|---|
| 58 | GET `/interfaces/tracking` | 01,03 | R: interface_transactions | filter data_name/ช่วงวัน |
| 59 | GET `/interfaces/pending-ack` | 01,03 | R: interface_transactions | ACK ค้าง ≥ 1 วัน (ฐานเดียวกับ Job 10) |
| 60 | POST `/interfaces/sta/ack` | key | W: interface_transactions | key ผิด/ไม่ส่ง → 401 · อัปเดต sta_status |
| 61 | GET `/dashboard/summary` | ทุก role | R: aggregate หลายตาราง | cache in-memory TTL 5 นาที |

> **Skip:** `GET /abnormal-stores` · `POST /abnormal-stores/assign` — comment รอตัดสินใจ ไม่สร้าง route (script Phase 7 ต้องยืนยันว่า**ไม่มี**)

## 5. Prisma schema — enum ทุกตัว + ตัวอย่างตารางหลัก 6 ตัว

34 ตารางเต็มแปลงจาก `database.md` §Data Dictionary (Zone A 7 · Zone B 9 · Zone C 18 — checklist ต่อตารางใน `checklist-be.md` §0.2–0.4) + ตาราง counter `doc_no_counters` (ไม่นับใน 34)
ทุกตารางใช้ `@@map` เป็น `lower_snake_case` · identity ต่อตาราง (ไม่ใช้ sequence รวม — Errata E18)

### 5.1 Enum ทุกตัว (บังคับระดับ DB — insert นอก enum ต้องถูก reject)

```prisma
enum VerifyStatus            { W P Y N }          // fgi_impact_stores.verify_status
enum WorkflowGenStatus       { W Y N }            // fgi_impact_processes.workflow_generation_status (source of truth)
enum ActionStatus            { Y W N }            // fgi_impact_processes.action_status
enum StaStatus               { I C A N S Z }      // interface_transactions.sta_status
enum InterfaceDataName       { AMS06001O AMS06001I FRBC0001 QSSI_MRS RT040035 RT040078 }
enum SourceSystem            { ALM USER }         // document_competitors.source_system
enum ResultCategory          { APPROVE REJECT PENDING }   // consideration_logs
enum DocumentOrigin          { AUTO MANUAL FS }   // compensation_documents.origin
enum InstanceStatus          { ACTIVE COMPLETED CANCELLED }   // workflow_instances.instance_status
enum TaskStatus              { OPEN CLOSED }      // workflow_tasks
enum ConfigCategory          { IMPACT WORKFLOW DOCUMENT AUTH NOTIFICATION BATCH }
enum ConfigValueType         { NUMBER STRING BOOLEAN JSON CRON }
enum AuditActionType         { CREATE UPDATE DELETE RESET }
enum JobRunStatus            { RUNNING SUCCESS ERROR }
enum MenuGroup               { MAIN MASTER }
```

### 5.2 ตัวอย่าง model 6 ตัวหลัก

```prisma
model CompensationDocument {
  docNo              String    @id @map("doc_no")            // "2569/00185" (พ.ศ.)
  statusCode         String    @map("status_code")
  currentSectionCode String?   @map("current_section_code")  // NULL เมื่อเสร็จสิ้น
  impactedStoreCode  String    @map("impacted_store_code")
  impactProcessId    BigInt?   @unique @map("impact_process_id") // FK ใหม่ 1 รอบ : 1 เอกสาร (MANUAL อาจ NULL)
  origin             DocumentOrigin @default(AUTO)
  periodMonth        String    @map("period_month")          // งวด YYYY-MM (ค.ศ.)
  compensationAmount Decimal?  @map("compensation_amount") @db.Decimal(14, 2)
  createdBy          String    @map("created_by")
  createdAt          DateTime  @default(now()) @map("created_at")
  updatedAt          DateTime  @updatedAt @map("updated_at")

  status        DocumentStatus     @relation(fields: [statusCode], references: [statusCode])
  section       WorkflowSection?   @relation(fields: [currentSectionCode], references: [sectionCode])
  impactProcess FgiImpactProcess?  @relation(fields: [impactProcessId], references: [id])
  newStores     DocumentNewStore[]
  competitors   DocumentCompetitor[]
  factors       DocumentExternalFactor[]
  logs          ConsiderationLog[]
  attachments   DocumentAttachment[]
  instance      WorkflowInstance?

  @@unique([impactedStoreCode, periodMonth])   // ร้าน+งวดซ้ำ → 409
  @@index([statusCode, currentSectionCode])
  @@map("compensation_documents")
}

model WorkflowInstance {
  instanceId  String         @id @map("instance_id")
  docNo       String         @unique @map("doc_no")        // 1 เอกสาร : 1 instance
  status      InstanceStatus @default(ACTIVE) @map("instance_status")
  startedAt   DateTime       @default(now()) @map("started_at")
  startedBy   String         @map("started_by")
  completedAt DateTime?      @map("completed_at")

  document CompensationDocument @relation(fields: [docNo], references: [docNo])
  tasks    WorkflowTask[]
  @@map("workflow_instances")
}

model WorkflowTask {
  taskId             BigInt     @id @default(autoincrement()) @map("task_id")
  instanceId         String     @map("instance_id")
  docNo              String     @map("doc_no")
  sectionCode        String     @map("section_code")
  assigneeEmployeeId String?    @map("assignee_employee_id")  // NULL = ทั้ง section (จาก operator_assignments)
  status             TaskStatus @default(OPEN) @map("task_status")
  actionResult       String?    @map("action_result")
  openedAt           DateTime   @default(now()) @map("opened_at")
  closedAt           DateTime?  @map("closed_at")             // waiting_days = now - opened_at (EM-04/05)

  instance WorkflowInstance @relation(fields: [instanceId], references: [instanceId])
  @@index([sectionCode, status])
  @@map("workflow_tasks")
}

model ConsiderationLog {
  id             BigInt         @id @default(autoincrement())
  docNo          String         @map("doc_no")
  sectionCode    String         @map("section_code")
  result         String                                  // payload result ไทย verbatim 6-enum
  detail         String?                                 // required ที่ service เมื่อไม่ชดเชย
  resultCategory ResultCategory @map("result_category")  // ฐาน filter ประกันรายได้/ไม่ประกันรายได้
  considerBy     String         @map("consider_by")
  actionDatetime DateTime       @default(now()) @map("action_datetime")

  document CompensationDocument @relation(fields: [docNo], references: [docNo])
  @@index([docNo, actionDatetime])
  @@map("consideration_logs")
}

model InterfaceTransaction {
  id              BigInt            @id @default(autoincrement())
  dataName        InterfaceDataName @map("data_name")
  // typed FK 3 คอลัมน์ — ห้าม polymorphic key (แก้ P1 + บั๊ก parseInt เลขศูนย์นำหน้า)
  impactProcessId BigInt?           @map("impact_process_id")
  salesSummaryId  BigInt?           @map("sales_summary_id")
  docNo           String?           @map("doc_no")
  fileName        String?           @map("file_name")
  staStatus       StaStatus?        @map("sta_status")
  ackAt           DateTime?         @map("ack_at")            // NULL + ส่งไป ≥ 1 วัน = pending-ack (Job 10)
  sentAt          DateTime          @default(now()) @map("sent_at")

  impactProcess FgiImpactProcess?      @relation(fields: [impactProcessId], references: [id])
  salesSummary  FgiImpactSalesSummary? @relation(fields: [salesSummaryId], references: [id])
  document      CompensationDocument?  @relation(fields: [docNo], references: [docNo])
  @@index([dataName, sentAt])
  @@map("interface_transactions")
}

model SystemConfig {
  configKey   String          @id @map("config_key")     // dot notation: workflow.avp_amount_threshold
  category    ConfigCategory
  valueType   ConfigValueType @map("value_type")         // validate ก่อนบันทึก
  value       String                                      // เก็บ string เดียว แปลงตาม valueType
  description String?
  isEditable  Boolean         @default(true) @map("is_editable")  // false = ค่าคงที่ธุรกิจ แก้ผ่าน API ไม่ได้
  updatedBy   String?         @map("updated_by")
  updatedAt   DateTime        @updatedAt @map("updated_at")
  // ห้ามมี secret — POST/PUT ปฏิเสธ key ที่มี password/secret/token (400)
  @@map("system_configs")
}

model DocNoCounter {
  yearBe Int @id @map("year_be")   // ปี พ.ศ. เช่น 2569
  lastNo Int @default(0) @map("last_no")
  @@map("doc_no_counters")
}
```

## 6. Workflow Engine — ตาราง transition เต็ม + transitions.ts

**5 ขั้น 06→08→01→02→03 · สถานะ 6 ค่า** · threshold 100,000 อ่านจาก `system_configs['workflow.avp_amount_threshold']` — **ห้าม hardcode**

### 6.1 สถานะเอกสาร 6 ค่า (seed `document_statuses` — status_code = section คู่ · END = `DONE`)

| status_code | สถานะ | Section คู่ |
|---|---|---|
| S06 | รอฝ่าย SBP DSA ดำเนินการ | 06 |
| S08 | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | 08 |
| S01 | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | 01 |
| S02 | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | 02 |
| S03 | รอผู้บริหารสำนักบริหาร SBP ดำเนินการ | 03 |
| DONE | เสร็จสิ้นดำเนินการ | — (END) |

### 6.2 ตาราง transition เต็มทุกแถว (ลอกจาก `workflow.md` §สถานะเอกสารและเส้นทางพิจารณา)

| # | Section | ตัวเลือกพิจารณา (`result` — ไทย verbatim 6-enum) | เงื่อนไข | ไปที่ | result_category |
|---|---|---|---|---|---|
| 1 | 06 ฝ่าย SBP DSA | เห็นควรไม่ชดเชย | — | **เสร็จสิ้นดำเนินการ** (END) | REJECT |
| 2 | 06 | หยุดชดเชยประกันรายได้ | — | **เสร็จสิ้นดำเนินการ** (END) | REJECT |
| 3 | 06 | ส่งฝ่ายส่งเสริมธุรกิจ SBP | — | รอ 01 | PENDING |
| 4 | 06 | ส่งเจ้าหน้าที่ SBP DSA | — | รอ 08 | PENDING |
| 5 | 08 เจ้าหน้าที่ SBP DSA | คำนวณเงินชดเชยเรียบร้อย | — | รอ 01 | PENDING |
| 6 | 08 | ส่งกลับ | — | รอ 06 (back-flow) | PENDING |
| 7 | 01 ฝ่ายส่งเสริมธุรกิจ SBP | เห็นควรชดเชย | — | รอ 02 | PENDING |
| 8 | 01 | เห็นควรไม่ชดเชย | — | รอ 06 (back-flow) | PENDING |
| 9 | 02 GM ส่งเสริมธุรกิจ SBP | เห็นควรชดเชย | ยอด **> 100,000** | รอ 03 (AVP) | PENDING |
| 10 | 02 | เห็นควรชดเชย | ยอด **≤ 100,000** | **เสร็จสิ้นดำเนินการ** (จบที่ GM) | APPROVE |
| 11 | 02 | เห็นควรไม่ชดเชย | ยอด **> 100,000** | รอ 03 — ไม่ชดเชยก็ต้องผ่าน AVP ตามวงเงิน | PENDING |
| 12 | 02 | เห็นควรไม่ชดเชย | ยอด **≤ 100,000** | รอ 06 (back-flow) | PENDING |
| 13 | 02 | ส่งกลับ | — | รอ 01 (back-flow) | PENDING |
| 14 | 03 AVP | เห็นควรชดเชย | — | **เสร็จสิ้นดำเนินการ** (จบที่ AVP) | APPROVE |
| 15 | 03 | เห็นควรไม่ชดเชย | — | รอ 06 (back-flow) | REJECT |
| 16 | 03 | ส่งกลับ | — | รอ 02 (back-flow) | PENDING |

> ขั้นบัญชี 04/05 ถูกตัดตาม SDD v7.5 — ทางเลือกเดิม "06 → ส่งฝ่ายบัญชี SBP" ยกเลิกด้วย · `result` ที่ไม่อยู่ใน 6-enum หรือไม่ถูกต้องสำหรับ section ปัจจุบัน → throw (400)

### 6.3 `workflow/transitions.ts` (ประกาศเป็น data — unit test ครบทุก branch)

```ts
export type Amount = 'GT' | 'LTE';               // เทียบ avp_amount_threshold
export interface Transition {
  section: string;                                // section ปัจจุบัน
  result: string;                                 // payload result ไทย verbatim 6-enum
  amount?: Amount;                                // เฉพาะ section 02
  next: string | 'END';                           // section ถัดไป หรือจบ
  resultCategory: 'APPROVE' | 'REJECT' | 'PENDING';
  backFlow?: boolean;                             // true → ส่ง EM-03 แทน EM-01
  commentRequired?: boolean;                      // ไม่ชดเชย/หยุด → comment บังคับ
}

export const TRANSITIONS: Transition[] = [
  { section: '06', result: 'เห็นควรไม่ชดเชย',              next: 'END', resultCategory: 'REJECT',  commentRequired: true },
  { section: '06', result: 'หยุดชดเชยประกันรายได้',         next: 'END', resultCategory: 'REJECT',  commentRequired: true },
  { section: '06', result: 'ส่งฝ่ายส่งเสริมธุรกิจ SBP',      next: '01',  resultCategory: 'PENDING' },
  { section: '06', result: 'ส่งเจ้าหน้าที่ SBP DSA',        next: '08',  resultCategory: 'PENDING' },
  { section: '08', result: 'คำนวณเงินชดเชยเรียบร้อย',       next: '01',  resultCategory: 'PENDING' },
  { section: '08', result: 'ส่งกลับ',                       next: '06',  resultCategory: 'PENDING', backFlow: true },
  { section: '01', result: 'เห็นควรชดเชย',                 next: '02',  resultCategory: 'PENDING' },
  { section: '01', result: 'เห็นควรไม่ชดเชย',              next: '06',  resultCategory: 'PENDING', backFlow: true, commentRequired: true },
  { section: '02', result: 'เห็นควรชดเชย',   amount: 'GT',  next: '03',  resultCategory: 'PENDING' },
  { section: '02', result: 'เห็นควรชดเชย',   amount: 'LTE', next: 'END', resultCategory: 'APPROVE' },
  { section: '02', result: 'เห็นควรไม่ชดเชย', amount: 'GT',  next: '03',  resultCategory: 'PENDING', commentRequired: true },
  { section: '02', result: 'เห็นควรไม่ชดเชย', amount: 'LTE', next: '06',  resultCategory: 'PENDING', backFlow: true, commentRequired: true },
  { section: '02', result: 'ส่งกลับ',                       next: '01',  resultCategory: 'PENDING', backFlow: true },
  { section: '03', result: 'เห็นควรชดเชย',                 next: 'END', resultCategory: 'APPROVE' },
  { section: '03', result: 'เห็นควรไม่ชดเชย',              next: '06',  resultCategory: 'PENDING', backFlow: true, commentRequired: true },
  { section: '03', result: 'ส่งกลับ',                       next: '02',  resultCategory: 'PENDING', backFlow: true },
];

export function findTransition(section: string, result: string, amountFlag?: Amount): Transition {
  const t = TRANSITIONS.find(x => x.section === section && x.result === result
    && (x.amount === undefined || x.amount === amountFlag));
  if (!t) throw new AppError('VALIDATION', MSG.UNKNOWN_RESULT, 400);
  return t;
}
```

## 7. โค้ดตัวอย่าง core (implement ตามนี้ — ปรับได้เฉพาะรายละเอียดไม่ใช่พฤติกรรม)

### 7.1 `config/env.ts` — zod validate ทุกตัวแปร fail fast

```ts
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  JWT_ACCESS_TTL: z.string().default('30m'),
  JWT_REFRESH_TTL: z.string().default('8h'),
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

### 7.2 `lib/errors.ts` + `middlewares/errorHandler.ts`

```ts
export class AppError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

export function errorHandler(err: unknown, req: Request, res: Response, _next: NextFunction) {
  if (err instanceof AppError)
    return res.status(err.status).json({ code: err.code, message: err.message });
  if (err instanceof ZodError)
    return res.status(400).json({ code: 'VALIDATION', message: err.issues[0]?.message ?? MSG.VALIDATION });
  req.log.error({ err }, 'unhandled');            // log เต็ม — ไม่ leak stack ออก response
  return res.status(500).json({ code: 'INTERNAL', message: MSG.INTERNAL });
}
```

### 7.3 `middlewares/auth.ts` + `requireRole.ts`

```ts
export function auth(req: Request, _res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace(/^Bearer /, '');
  if (!token) throw new AppError('AUTH_401', MSG.AUTH_REQUIRED, 401);
  try {
    const p = jwt.verify(token, env.JWT_SECRET) as { employeeId: string; roleCode: string };
    req.user = p;
    next();
  } catch { throw new AppError('AUTH_401', MSG.TOKEN_INVALID, 401); }
}

export const requireRole = (...roles: string[]) =>
  (req: Request, _res: Response, next: NextFunction) => {
    if (!roles.includes(req.user!.roleCode))
      throw new AppError('FORBIDDEN', MSG.FORBIDDEN, 403);
    next();
  };
// serviceToken.ts / apiKey.ts: เทียบ constant-time (crypto.timingSafeEqual) กับ env.SERVICE_TOKEN / env.API_KEY_STA → ผิด 401
```

### 7.4 `lib/docNo.ts` — เลขเอกสาร พ.ศ./xxxxx จองด้วย FOR UPDATE

```ts
/** เรียกภายใน prisma.$transaction เท่านั้น — race-safe ด้วย row lock */
export async function nextDocNo(tx: Prisma.TransactionClient, date = new Date()): Promise<string> {
  const yearBe = date.getFullYear() + 543;
  await tx.$executeRaw`INSERT INTO doc_no_counters (year_be, last_no) VALUES (${yearBe}, 0)
                       ON CONFLICT (year_be) DO NOTHING`;
  const [row] = await tx.$queryRaw<{ last_no: number }[]>`
    SELECT last_no FROM doc_no_counters WHERE year_be = ${yearBe} FOR UPDATE`;
  const next = row.last_no + 1;
  await tx.$executeRaw`UPDATE doc_no_counters SET last_no = ${next} WHERE year_be = ${yearBe}`;
  return `${yearBe}/${String(next).padStart(5, '0')}`;   // เช่น "2569/00185"
}
// test: Promise.all ยิง 20 ครั้งพร้อมกัน → 20 เลขไม่ซ้ำ ต่อเนื่อง
```

### 7.5 `workflow/engine.ts` — applyAction (transaction เต็มของ POST /documents/{docNo}/actions)

```ts
export async function applyAction(docNo: string, user: JwtUser,
    input: { result?: string; comment?: string }) {
  // 1) validate ก่อนเข้า transaction
  if (!input.result)
    throw new AppError('VALIDATION',
      'ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ', 400); // verbatim SRS

  const result = await prisma.$transaction(async tx => {
    const doc = await tx.compensationDocument.findUnique({ where: { docNo } });
    if (!doc) throw new AppError('NOT_FOUND', MSG.DOC_NOT_FOUND, 404);
    if (doc.statusCode === 'DONE') throw new AppError('CONFLICT', MSG.DOC_ALREADY_DONE, 409);

    const mySection = await sectionOfRole(tx, user);           // map role/operator → section
    if (mySection !== doc.currentSectionCode)
      throw new AppError('FORBIDDEN', MSG.NOT_YOUR_SECTION, 403);

    // 2) lookup transition (threshold จาก system_configs — ห้าม hardcode)
    const threshold = await getConfigNumber(tx, 'workflow.avp_amount_threshold'); // 100000
    const amountFlag = Number(doc.compensationAmount ?? 0) > threshold ? 'GT' : 'LTE';
    const t = findTransition(doc.currentSectionCode!, input.result, amountFlag);
    if (t.commentRequired && !input.comment?.trim())
      throw new AppError('VALIDATION', MSG.COMMENT_REQUIRED, 400);

    // 3) update เอกสาร + ปิด/เปิด task + log — atomic
    const done = t.next === 'END';
    await tx.compensationDocument.update({ where: { docNo }, data: {
      statusCode: done ? 'DONE' : `S${t.next}`,
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
  const run = await prisma.$transaction(async tx => {
    const running = await tx.jobRunHistory.findFirst({ where: { jobNo, status: 'RUNNING' } });
    if (running) throw new AppError('CONFLICT', MSG.JOB_ALREADY_RUNNING, 409);   // กันรันซ้อน
    return tx.jobRunHistory.create({ data: { jobNo, status: 'RUNNING', trigger, startedBy: by } });
  });
  try {
    const stats = await JOB_IMPLS[jobNo]();       // { rows, files, note }
    await prisma.jobRunHistory.update({ where: { runId: run.runId },
      data: { status: 'SUCCESS', finishedAt: new Date(), ...stats } });
  } catch (err) {
    await prisma.jobRunHistory.update({ where: { runId: run.runId },
      data: { status: 'ERROR', finishedAt: new Date(), errorMessage: String(err) } });
    notificationQueue.enqueue({ template: 'EM-07', jobNo, error: String(err) });
    throw err;
  }
}
// boot recovery: แถว RUNNING ค้างจาก process ตาย → mark ERROR ตอน start (ไม่งั้น lock ค้างถาวร)
```

### 7.8 `lib/audit.ts` — writeAudit (ใช้ร่วมทุก master mutation ใน transaction เดียวกัน)

```ts
export async function writeAudit(tx: Prisma.TransactionClient, p: {
  tableName: string; refKey: string;
  actionType: 'CREATE' | 'UPDATE' | 'DELETE' | 'RESET';
  oldValue?: unknown; newValue?: unknown;
  reason: string;                                  // บังคับ — controller ตรวจ 400 ก่อนถึงตรงนี้
  updatedBy: string;                               // จาก JWT
}) {
  await tx.auditLog.create({ data: {
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
| 1 | นำเข้าคะแนน QSSI | รายเดือน | SFTP 4 ไฟล์ `mrs*` → upsert คะแนน 6 หมวด (8,9,12,1,10,16) | W: `fcs_qssi_scores` · UK กันซ้ำ | ไฟล์ขาดหมวด → fail ทั้งรอบ + EM-07 · งวด DB = เดือนก่อนหน้า (off-by-one ตั้งใจ) |
| 2 | นำเข้าร้านกระทบจาก ALLMAP | รายวัน | SELECT จาก SQL Server (read-only) → แถวร้านกระทบ | W: `fgi_impact_stores`, `fgi_impact_processes` | connection fail → retry 3 → EM-07 |
| 3 | นำเข้าคู่แข่งจาก ALLMAP | รายวัน | SELECT คู่แข่งรัศมี → แถว `data_source='ALM'` งวดล่าสุดต่อร้าน | W: `fgi_impact_competitors` | เหมือน Job 2 |
| 4 | export ยอดขายไป MIS | 16:00 วันที่ 7–16 | รอบที่ `action_status='W'` → ไฟล์ `AMS06001O_YYYYMMDD` | R: sales pipeline · W: `interface_transactions`, สถานะ W→P | **P0: transaction/outbox — เขียนไฟล์สำเร็จก่อนค่อย commit W→P** · fail = rollback ทั้งก้อน |
| 5 | import ยอดขายจาก MIS | 16:30 วันที่ 7–16 | ไฟล์ `AMS06001I_` → ยอดขายรายวัน 4×15 | W: `sales_transactions`, `fgi_impact_sales_summaries` | ค่า NULL → ตั้งสถานะ "รอตรวจสอบ" (**ห้าม auto-accept** — flag `batch.job5_null_policy` ใน system_configs รอ business sign-off) |
| 6 | export ผลชดเชยไป STA | 17:00 ทุกวัน | `compensation_histories` งวดพร้อมส่ง → ไฟล์ `FRBC0001_` | R: histories · W: `interface_transactions` (sta_status I/C/A/N/S/Z) | เขียนไฟล์ fail → ไม่อัปเดตสถานะ + EM-07 |
| 8b (แทน) | เปิด workflow อัตโนมัติ | 17:30 วันที่ 7–31 | รอบผ่าน Gen Flow Gate → เรียก `workflows.service.openInstance()` **ภายใน process** (ไม่ผ่าน HTTP) | W: documents/instances/tasks | สรุปผลราย DV → EM-06 · รายการไม่ผ่าน gate = log เหตุผล ไม่ fail รอบ |
| 10 | watchdog ACK จาก STA | 07:00 ทุกวัน | หา `interface_transactions` ที่ส่งแล้วไม่มี ACK ≥ 1 วัน | R: interface_transactions | พบ → EM-08 ถึงผู้ดูแล (ไม่ใช่ error ของ job) |

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

## 10. Seed data (`prisma/seed.ts` — idempotent ด้วย upsert ทั้งหมด)

| ตาราง | แถว | รายละเอียด |
|---|---|---|
| roles / menus / menu_permissions | 8 / ~12 / 8×เมนู | ตาม k2-permissions.html — matrix สิทธิ์ตรง prototype |
| workflow_sections | 7 (5 active + 04/05 `is_active=false`) | 04/05 เก็บไว้อ้างอิงประวัติเท่านั้น |
| document_statuses | 6 | string ตรง workflow.md ทุกตัวอักษร |
| system_configs | ~15 | radius 1/2 กม. · threshold 100000 · เกณฑ์ 60 วัน · −10 (ทั้งหมด is_editable=false) + cache TTL, cron ต่าง ๆ |
| email_templates + status_email_rules | 8 + 6 | EM-01–08 (subject/body default ตาม plan-email.html) |
| competitors / external_factors | 24 / ~10 | ตาม master ใน prototype |
| employees / user_accounts | ~15 / 8 | 1 บัญชีต่อ role · รหัสผ่าน `Passw0rd!` (bcrypt) — dev เท่านั้น |
| operator_assignments | ~10 | กระจาย 5 section · ภาคใช้ REGIONS8 |
| stores / impacted_stores | ~30 / ~15 | รหัส 5 หลัก มีเลขศูนย์นำหน้า (ทดสอบ typed FK) |
| job_configs | 11 | cron ตาม Batch v4.0 · Jobs 7/8/9 `enabled=false` + note "ตัดทิ้ง — คงแถวเพื่อ traceability" |
| เอกสาร demo | ~10 | ครบ 6 สถานะ · มีเคส >100k (ผ่าน 03) และ ≤100k (จบที่ 02) · แถว <60 วัน · เลขเริ่ม 2569/00181 ให้เลขถัดไปตรง prototype (2569/00187) |

## 11. Environment variables + docker-compose

| ตัวแปร | ตัวอย่าง (dev) | ใช้ทำอะไร |
|---|---|---|
| `DATABASE_URL` | postgres://sbpgi:sbpgi@localhost:5432/sbpgi | Prisma |
| `PORT` / `NODE_ENV` | 3000 / development | server |
| `JWT_SECRET` (≥32 ตัว) / `JWT_ACCESS_TTL` / `JWT_REFRESH_TTL` | … / 30m / 8h | auth |
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

Dockerfile: multi-stage `node:20-alpine` (deps → build tsc+prisma generate → runtime คัดเฉพาะ dist+node_modules production) · CMD `node dist/server.js` · migrate ตอน deploy ด้วย `prisma migrate deploy` (ไม่ auto ใน CMD)

## 12. Best practices สากลที่บังคับใช้

- **12-factor**: config ผ่าน env (zod fail fast) · log stdout JSON (pino + request id + redact token/password) · stateless (storage เป็น volume)
- **Security**: helmet · cors whitelist · rate limit `POST /auth/login` · bcrypt ≥ 10 · Prisma/parameterized เท่านั้น ห้ามต่อ string SQL · ไม่ leak stack ใน 500
- **Graceful shutdown**: SIGTERM/SIGINT → หยุดรับ request → รอ job ที่กำลังรัน → `prisma.$disconnect()` · `GET /healthz` (liveness) + `GET /readyz` (เช็ค DB)
- **Transaction boundary ที่ service** — `prisma.$transaction(async tx => …)` ส่ง `tx` ลง repo · side-effect ภายนอก (อีเมล/ไฟล์) นอก transaction เสมอ
- **Testing pyramid**: unit service (mock repo — เน้น `workflow/transitions` ครบทุก branch) → integration supertest + postgres จริง → golden-file ต่อ interface (encoding, วันที่ พ.ศ., ชื่อ first+last) · coverage `workflow/` ≥ 90%
- **Migration ผ่าน `prisma migrate` เท่านั้น** (ห้าม `db push`) · seed idempotent
- **API versioning**: ทุกอย่างใต้ `/api/v1` — breaking change = `/api/v2`

## 13. Definition of Done (ทั้งโปรเจกต์ BE)

1. endpoint ครบ **62/62** ตรง `api.md` (script เทียบ route tableรายงาน matched) — abnormal-stores 2 เส้น skip ตามแผน
2. integration test เดิน workflow จริงผ่านทุก scenario ใน checklist-be.md Phase 3 (≤100k จบ 02 · >100k ผ่าน 03 · back-flow · เอกสารจบแล้ว action ซ้ำ → 409)
3. ข้อความ error ไทยทุกตัวรวมศูนย์ `lib/messages.ts` และตรง verbatim SRS
4. batch ทุก job รันผ่าน `POST /jobs/{no}/run` สำเร็จบน fixture · Job 4 fail กลางทาง = rollback สถานะไม่ค้าง P
5. seed แล้ว FE (plan-fe.md) ใช้งานได้ครบทุกหน้า end-to-end ผ่าน `docker compose up`
6. CI เขียว: lint / tsc / prisma validate / test / build · ไม่มี secret ใน repo/DB/log
