# LLDD BE - API Common Contracts

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | BE |
| Estimate | 18 ชั่วโมง (ไม่มี unit test แยก — ดูเหตุผลใน NO_UNIT_TEST_DOCS) |
| Owner | Butsaba <But> Podamrong |
| Target repository | `SBP/srm-sps-spsap-store-backend` (NestJS + TypeORM · schema `sps_store`) + `SBP/srm-sps-spsap-sbp-bff` (forward ผ่าน client service · ไม่มี DB) สำหรับเส้นที่ FE เรียก |
| Objective | กำหนดสัญญากลางของ REST API ทุกเส้นเพื่อไม่ให้ endpoint รายตัวตีความต่างกัน: transport/auth/error/format/pagination/action/RBAC/audit/idempotency |

Common contract reference: ทุกหัวข้อ API/FE ต้องยึด LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts สำหรับ error/auth/format/pagination/action/RBAC ก่อนลงรายละเอียดเฉพาะหน้าหรือเฉพาะ endpoint

### 1.1 เอกสาร LLDD ที่เกี่ยวข้อง

ตารางนี้สร้างจาก endpoint และตารางที่เอกสารฉบับนี้ประกาศไว้จริง — อ่านฉบับที่อยู่ในตารางก่อนลงมือ เพื่อไม่ให้สัญญา request/response หรือชื่อคอลัมน์หลุดจากกัน

| ความสัมพันธ์ | เอกสาร LLDD | เกี่ยวข้องตรงไหน |
| --- | --- | --- |
| ใช้ endpoint ของ | **LLDD-BE-API-Document-Workflow-Actions** | `POST /api/v1/sgi/document/{docNo}/actions` |
| workflow engine | **LLDD-BE-Workflow-Engine-Definition** | นิยาม state/route/event ที่หัวข้อ Workflow Trigger Event Contract เรียกใช้ |
| แพลตฟอร์มระบบเดิม | **LLDD-BE-Integration-SBP-Platform** | header จาก BFF (`x-api-key` / `x-user-*`) · การ reuse ตารางและ service ของระบบ SBP เดิม |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-BE-Database-Structure** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-BE-Integration-SBP-Platform** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |

## 2. Screen / Functional Scope

- Base URL, content type, charset and request tracing
- Auth/JWT platform validation and service-token exception
- Standard success envelopes for list/detail/mutation
- Standard error envelope and HTTP status mapping
- Field format for date/month/docNo/storeCode/amount/percent
- Document action input/output contract
- RBAC/menu permission and editable section guard
- Audit/reason and idempotency rules

## 3. Screenshot Reference

ไม่มีภาพหน้าจอสำหรับหัวข้อนี้ — เป็นเอกสารฝั่ง Backend/Batch ที่ไม่มี UI (ภาพหน้าจอทั้งหมดอยู่ในเอกสารชุด FE)

## 4. Implementation Flow & Sequence Diagram (Reference)

### 4.1 Implementation Flow (ลำดับขั้นการทำงาน)

![รูปที่ 1: Implementation flow reference: LLDD BE - API Common Contracts](../../assets/flows/BE-LLDD-BE-API-Common-Contracts.png)

_รูปที่ 1: Implementation flow reference: LLDD BE - API Common Contracts_

### 4.2 Sequence Diagram (ใครคุยกับใคร ลำดับไหน)

ผู้แสดงและลำดับข้อความในภาพนี้สร้างจาก endpoint ในหัวข้อ 7 และตารางในหัวข้อ Reference DB Mapping ของเอกสารฉบับนี้เอง จึงตรงกับสัญญาเสมอ

![รูปที่ 2: Sequence diagram: LLDD BE - API Common Contracts](../../assets/flows/BE-LLDD-BE-API-Common-Contracts-sequence.png)

_รูปที่ 2: Sequence diagram: LLDD BE - API Common Contracts_

## 5. Field, Format, and Validation

| Field / UI | Format | Validation | Behavior |
| --- | --- | --- | --- |
| Base URL | /api/v1 | required | ทุก endpoint ใช้ prefix นี้ |
| Content-Type | application/json; charset=utf-8 | required for JSON | multipart เฉพาะ attachments |
| Authorization | Bearer <JWT> | required for user endpoints | validate signature/expiry/role; platform provides token |
| X-Service-Token | opaque service token | required for internal workflow/batch callbacks | ใช้กับ /sgi/workflow/instances และ external callback ที่ไม่ใช่ user JWT |
| X-Request-Id | uuid/string | optional but logged | ถ้าไม่ส่ง BE generate แล้วคืนใน log/trace |
| ErrorEnvelope | {code,message} | message Thai verbatim | ห้ามเพิ่ม error shape อื่นใน endpoint รายตัว |
| PageResponse<T> | {page,size,total,items} | page>=1 size<=100 | ใช้กับทุก GET list |
| MutationResponse | {message} | message optional for simple save | ถ้า workflow action ใช้ ActionResponse แทน |
| docNo | YYYY/xxxxx ค.ศ. | path/query | URL encode slash ตาม client/router; service ประกอบกลับเป็น docNo |
| storeCode/newStoreCode | string 5 digits | preserve leading zero | ห้ามใช้ numeric id แทนรหัสร้านใน payload |
| date/month | ISO-8601 ค.ศ. | YYYY-MM-DD / YYYY-MM | FE แสดง ค.ศ. เป็นค่าเริ่มต้น (buddhistEra=false) · แปลง พ.ศ. เฉพาะ component ที่เปิด flag |
| amount/percent | number | 2 decimal | format display อยู่ FE; BE validate precision/range |
| result | verbatim from actionOptions | required for /actions | ต้องเป็นค่าที่ BE ส่งมาใน role profile ของเอกสารนั้น |
| ActionResponse | {statusCode,nextSection,message} | required for /actions | FE resolve label จาก /sgi/lookup/document-statuses; mutation response ไม่คืน label ไทยซ้ำ |
| reason | text | ไม่บังคับแล้ว (ยกเลิกระบบ audit ของ master 2026-08-07) | ไม่มีปลายทางเก็บ — ถ้าส่งมาให้ละเว้น |

### 5.80 Namespace + กลุ่ม path ของงานประกันรายได้ (มติ 2026-08-25)

SGI ไม่ได้แยก backend/พอร์ทัลใหม่ (มติ **DP-10** ให้อยู่ใน `srm-sps-spsap-store-backend` และโมดูลใน `srm-sps-spsap-web-frontend` เดิม) ทุกอย่างของงานประกันรายได้จึงอยู่ใต้ **ชื่อเดียวกันทั้ง 3 ชั้น** แล้วแตกเป็น **6 กลุ่มย่อยตามกลุ่มงาน** — ตรงกับ 6 กลุ่มใน `api.md` แบบ 1:1

| ชั้น | รูปแบบ | ตัวอย่าง |
| --- | --- | --- |
| URL ของ API | `/api/v1/sgi/<กลุ่ม>/<resource>` | `/api/v1/sgi/document/{docNo}/actions` |
| route ของหน้าจอ | `/sgi/<กลุ่ม>/<หน้า>` | `/sgi/document/waiting` · `/sgi/report/status-summary` |
| โฟลเดอร์ไฟล์ | `**/sgi/*` | `src/app/(main)/sgi/*` · `src/services/sgi/*` · `src/types/sgi/*` |

#### 6 กลุ่มย่อยใต้ `sgi`

| กลุ่ม | prefix | เส้น | ครอบคลุมอะไร |
| --- | --- | --- | --- |
| งาน & เอกสารประกันรายได้ | `/sgi/document/*` | 11 | `/tasks` (กล่องงาน) · ค้นหา/สร้าง/แก้เอกสาร · `/{docNo}/actions` · `/timeline` · `/attachments` · `/sales` |
| ข้อมูลอ้างอิง (Lookup) | `/sgi/lookup/*` | 2 | `/document-statuses` · `/workflow-sections` — อ่านอย่างเดียว ไม่มีหน้าจอดูแล |
| Master Data | `/sgi/master/*` | 8 | `/factors` (CRUD 4) · `/competitors` (CRUD 4) — master ที่มีหน้าจอดูแลของตัวเอง |
| รายงาน | `/sgi/report/*` | 2 | `/status-summary` · `/status-summary/export` |
| Workflow ภายใน | `/sgi/workflow/*` | 3 | `/instances` · `/instances/{id}` · `/summary` |
| Interface (tracking / ACK) | `/sgi/interface/*` | 3 | `/tracking` · `/pending-ack` · `/sta/ack` |

**Batch job ไม่มีกลุ่ม path ของตัวเอง** — Jobs 2-10 + 8b รันด้วย cron/CLI ไม่ได้เปิด endpoint (กลุ่ม Batch Job Admin 6 เส้นถูกตัดทิ้ง 2026-08-06) · หน้าต่างที่มองเห็นผลของ job คือ **`/sgi/interface/*`** (tracking + ACK ของ `sgi_interface_transactions`) กับ application log เท่านั้น

#### ทำไมต้องมี prefix (ไม่ใช่แค่ความสวยงาม)

| ระบบเดิมมีอยู่แล้ว | ของ SGI ถ้าไม่ใส่ prefix | ผล |
| --- | --- | --- |
| `/document` · `/statement/...` | `/documents` | ชนเชิงความหมาย อ่าน routing แล้วสับสน |
| `/report` · `/performance-report` · `/statement/report/ej` | `/reports/status-summary` | ชนเชิงความหมาย |
| **`/interface/sta/upload-cmadd`** · `/interface/add` | **`/interfaces/sta/ack`** | 🔴 เกือบเหมือนกัน — เสี่ยงยิงผิดเส้นจริง |
| `/common` · `/master` · `/store` | `/factors` `/competitors` `/document-statuses` | ปนกับ master ของโมดูลอื่น |

- ฝั่ง NestJS: **`SgiModule` เดียว** ผูก prefix ที่ระดับโมดูล (`RouterModule.register([{ path: 'sgi', module: SgiModule }])`) แล้วแตกเป็น 6 controller ตามกลุ่ม (`DocumentController` `LookupController` `MasterController` `ReportController` `WorkflowController` `InterfaceController`) — **ห้ามเติม `sgi/` ในแต่ละ `@Controller()`**
- ในกลุ่ม `document` ต้องประกาศ route คงที่ (`/tasks`) **ก่อน** route ที่มีพารามิเตอร์ (`/{docNo}`) และ `docNo` เป็น `YYYY/xxxxx` จึงต้อง `encodeURIComponent` ทุกครั้งที่ประกอบ URL
- เส้นที่ **ไม่ใช่ของ SGI ห้ามใส่ prefix และห้ามแตะ** — `GET /store/search` · `GET /store/all-regions` · `GET /common/common-code` · `GET /menus` · `GET /groups/current-user/permissions` · `POST /statement/upload-file-aws` · `GET /api/workflow/pending` เป็นของระบบ SBP เดิม
- BFF ส่งต่อทั้ง prefix (`/api/v1/sgi/*`) โดยไม่ตัดคำ · สิทธิ์เมนูผูกกับ URL ของ **หน้าจอ** (`/sgi/<กลุ่ม>/...`) ไม่ใช่ URL ของ API

### 5.1 Error and Popup Catalog

ทุก endpoint ต้องใช้ code และ message จาก catalog เดียวกันเมื่อเข้าเงื่อนไขเดียวกัน

| code | HTTP / Scope | Trigger | message |
| --- | --- | --- | --- |
| ACTION_RESULT_REQUIRED | 422 | submit action โดยไม่เลือกผลการพิจารณา | ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ |
| ACTION_COMMENT_REQUIRED | 422 | result ที่ต้องมี comment แต่ comment ว่าง | กรุณากรอกความคิดเห็นเพิ่มเติม (บังคับกรอกสำหรับผลการพิจารณานี้) ก่อนส่งดำเนินการ |
| COMPENSATE_PERCENT_INVALID | 422 | ผลรวม % ชดเชยร้านเปิดใหม่ไม่เท่ากับ 100 | โปรดตรวจสอบ %ชดเชย ของท่าน รวมกันแล้วไม่เท่ากับ 100% |
| COMPETITOR_REQUIRED | 422 | บันทึกร้านคู่แข่งโดยไม่เลือก competitorCode | กรุณาเลือกร้านคู่แข่งก่อนบันทึก |
| EXTERNAL_FACTOR_REQUIRED | 422 | บันทึกปัจจัยอื่นโดยไม่เลือก factorCode | กรุณาเลือกปัจจัยอื่นก่อนบันทึก |
| REPORT_DATE_RANGE_INVALID | 422 | impactMonthFrom มากกว่า impactMonthTo | เดือนเริ่มต้นต้องไม่มากกว่าเดือนสิ้นสุด |
| FILE_TOO_LARGE | 413 | attachment > 5 MB | ไฟล์แนบมีขนาดเกิน 5 MB |
| FILE_TYPE_UNSUPPORTED | 415 | extension/content type ไม่อยู่ใน allowlist | ชนิดไฟล์ไม่อนุญาตให้อัปโหลด |
| FILE_SCAN_BLOCKED | 422 | AV scan พบไวรัสหรือ scan failed | ไฟล์แนบไม่ผ่านการตรวจสอบความปลอดภัย |
| FORBIDDEN | 403 | ไม่มีสิทธิ์เมนู/เอกสาร/task | กรุณาติดต่อผู้ดูแลระบบ |
| DUPLICATE_DOCUMENT | 409 | business key ซ้ำตอนสร้างเอกสาร | ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว |
| CONFLICT | 409 | resource/task ถูกเปลี่ยนหรือเงื่อนไขปัจจุบันไม่ตรงกับคำขอ | ข้อมูลมีการเปลี่ยนแปลง กรุณาโหลดข้อมูลล่าสุดแล้วดำเนินการใหม่ |
| STALE_VERSION | 409 | versionNo ที่ส่งมาไม่ตรงกับ sgi_compensation_documents.version_no | ข้อมูลถูกแก้ไขโดยผู้ใช้อื่น กรุณาโหลดข้อมูลล่าสุดแล้วลองอีกครั้ง |
| FS_BRIDGE_UNAVAILABLE | FE | hidden iframe ไม่ตอบ FS_FORM_READY ภายในเวลาที่กำหนด | ไม่สามารถเชื่อมต่อแบบฟอร์ม FS ได้ กรุณาลองอีกครั้ง |
| FS_BRIDGE_ORIGIN_INVALID | FE | event.origin ไม่ตรง allowlist | ไม่สามารถยืนยันแหล่งที่มาของแบบฟอร์ม FS ได้ |
| FS_BRIDGE_SCHEMA_INVALID | FE | FS_FIELD_SCHEMA ไม่ตรง message schema หรือมี field type ที่ไม่รองรับ | ข้อมูลแบบฟอร์ม FS ไม่ถูกต้อง กรุณาติดต่อผู้ดูแลระบบ |
| FS_BRIDGE_SUBMIT_FAILED | FE | FS_SUBMIT_RESULT ไม่สำเร็จหรือ FS_ERROR ตอน submit | ส่งแบบฟอร์ม FS ไม่สำเร็จ กรุณาตรวจสอบข้อมูลแล้วลองอีกครั้ง |

### 5.2 Endpoint Role Matrix

Matrix นี้เป็น baseline สำหรับ BE authorization guard; menu-level visibility มาจาก permissions ต่อ URL ของ auth-backend (header `x-user-permissions`)

| Endpoint group | Endpoint pattern | Allowed roles / identity |
| --- | --- | --- |
| Current user/menu | ไม่ใช่ endpoint ของ SGI — FE เรียกของระบบเดิมผ่าน BFF: GET /auth/profile, GET /users/current, GET /menus, GET /groups/current-user/permissions | authenticated user |
| Task inbox | GET /sgi/document/tasks | authenticated user with assigned task access |
| Document read/list/timeline/sales | GET /sgi/document*, GET /sgi/document/{docNo}/timeline, GET /sgi/document/{docNo}/sales | document participant or report/admin role explicitly granted |
| Document create | POST /sgi/document | 🔴 **service token / pipeline เท่านั้น** — มติ 2026-08-06 ตัดฟอร์มสร้างเอกสารใน FE ออกแล้ว (ต้นทางสร้างที่ระบบ FS แล้ว SBP Statement ส่งข้อมูลกลับ) · ห้ามระบุเป็นรหัสกลุ่มสิทธิ์ เพราะเลข 01/02/03 ชนกับ section_code ของ workflow |
| Document update/action/attachment upload | PUT /sgi/document/{docNo}, POST /sgi/document/{docNo}/actions, POST /sgi/document/{docNo}/attachments | current action owner; admin override only with policy and audit reason |
| Attachment download | GET /sgi/document/{docNo}/attachments/{attachId}/download | สิทธิ์เท่ากับอ่านเอกสาร + attachment ต้องเป็นของ docNo นั้น · ⚠️ เงื่อนไข `scan_status` ขึ้นกับนโยบาย AV ที่ยังไม่เคาะ (ดู `LLDD-BE-API-Attachment-Sales-Timeline` 5.1) — บังคับ CLEAN อย่างเดียวตอนนี้จะดาวน์โหลดไม่ได้เลย |
| Lookup | /sgi/lookup/document-statuses, /sgi/lookup/workflow-sections (ร้าน/ภาค/ประเภทสาขา ใช้ /store/* + /common/common-code ของระบบ SBP เดิม · 2026-08-06) | authenticated user with related menu access |
| Master (SGI) | /sgi/master/factors*, /sgi/master/competitors* | admin/HQ ตามสิทธิ์เมนูที่มากับ header x-user-permissions |
| RBAC/ผู้ปฏิบัติงาน | ไม่ใช่ endpoint ของ SGI — ตัด /operators* /roles* /menus* /menu-permissions* /employees/search รวม 14 เส้น (2026-08-05) ใช้ auth-backend เดิม จัดการที่หน้า /setting/manage-user-rights | - |
| Reports | /sgi/report/status-summary* | admin/HQ/report roles and accounting service user |
| Internal workflow/interface | /sgi/workflow/instances · /sgi/interface/* (tracking · pending-ack · sta/ack callback) | service token หรือ API key เท่านั้น — ไม่ผ่านสิทธิ์เมนูของผู้ใช้ |

### 5.9 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | ALL /api/v1/sgi/*; GET /api/v1/sgi/*; POST /api/v1/sgi/document/{docNo}/actions |
| Progress | Request enters logging middleware and request id is attached; BffUserGuard ตรวจ x-api-key แล้ว map BFF header เป็น user context — 🔴 SGI ไม่ออก/ไม่ตรวจ JWT เอง (login อยู่ที่ Cognito ฝั่ง BFF) · เส้น service-token ใช้ API key แยก; RBAC guard checks role/menu/current workflow task owner; Validate params/query/body with shared schema conventions |
| Output | ไม่มีตารางที่เอกสารนี้เขียนเอง — output คือ response ตาม envelope กลาง `{success, data}` และร่องรอยที่ตรวจย้อนได้ (log / sgi_consideration_logs / workflow_history ของ engine) |

### 5.90 Endpoint Implementation Contract

| Endpoint | Use-case owner | Service/repository behavior | Definition of done |
| --- | --- | --- | --- |
| ALL /api/v1/sgi/* | Standard error envelope | Request enters logging middleware and request id is attached | ทุก endpoint ต้องใช้ common contract นี้ |
| GET /api/v1/sgi/* | Standard list envelope เมื่อ endpoint เป็นรายการ | BffUserGuard ตรวจ x-api-key แล้ว map BFF header เป็น user context — 🔴 SGI ไม่ออก/ไม่ตรวจ JWT เอง (login อยู่ที่ Cognito ฝั่ง BFF) · เส้น service-token ใช้ API key แยก | ไม่มี endpoint คืน error shape อื่นนอกจาก `{code,message}` |
| POST /api/v1/sgi/document/{docNo}/actions | **อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Document-Workflow-Actions (Tunyatorn)** · ยกมาเป็นตัวอย่างสัญญา action กลางที่ทุกเส้นต้องยึด (ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02) | RBAC guard checks role/menu/current workflow task owner | 401/403/404/409/422/413/415 mapping คงที่และ test ได้ |

### 5.91 Backend Execution Sequence

| Step | Behavior specific to this LLDD | Failure/test evidence |
| --- | --- | --- |
| 1 | Request enters logging middleware and request id is attached | missing JWT 401 |
| 2 | BffUserGuard ตรวจ x-api-key แล้ว map BFF header เป็น user context — 🔴 SGI ไม่ออก/ไม่ตรวจ JWT เอง (login อยู่ที่ Cognito ฝั่ง BFF) · เส้น service-token ใช้ API key แยก | role forbidden 403 |
| 3 | RBAC guard checks role/menu/current workflow task owner | validation error 400 |
| 4 | Validate params/query/body with shared schema conventions | not found 404 |
| 5 | Service executes business rule and document action if relevant | duplicate conflict 409 |
| 6 | Mutation writes domain row and audit/reason in the same transaction | list envelope |
| 7 | Controller maps result to standard envelope or throws AppError | action transition envelope |
| 8 | Error handler maps all failures to `{code,message}` only | audit reason required |

### 5.92 Workflow Trigger Event Contract

งานชิ้นนี้ **ต้องเรียก workflow engine** ตามตารางด้านล่าง · ชื่อ function ยึด API 8 ตัวของ `@srm/glb-workflow` ตามชีต `Detail` ของ `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` — รายละเอียด signature และตารางที่ engine เขียน ดู **LLDD-BE-Workflow-Engine-Definition** หัวข้อ 5.3

| จุดที่เรียก (call site) | Engine function | พารามิเตอร์หลัก | กติกา / transaction boundary |
| --- | --- | --- | --- |
| ตัวห่อกลาง (WorkflowGateway) | ทั้ง 8 ตัวของ `@srm/glb-workflow` | userData มาจาก BFF header (`x-user-id`, `x-user-group-id`) | 🔴 งานของเอกสารนี้คือ **ทำตัวห่อกลางให้ทุกคนเรียก** — map error ของ engine เข้า envelope `{success:false, error:{code,message}}` และบังคับ timeout/retry ที่เดียว |

- 🔴 กติกาเหล็ก: ตาราง `sps_store.workflow_*` (13 ตาราง) เป็นของ lib — SGI **R เท่านั้น** ห้าม INSERT/UPDATE/DELETE ตรงในทุกกรณี
- ทุกการเรียก engine ต้องผ่านตัวห่อกลาง `WorkflowGateway` ที่นิยามใน **LLDD-BE-API-Common-Contracts** (timeout · retry · map error เข้า envelope) ห้าม import lib ตรงจาก service
- unit test ต้อง mock engine และครอบอย่างน้อย: เรียกสำเร็จ · engine โยน error แล้ว rollback ฝั่ง SGI ครบ · เรียกซ้ำด้วย referenceId เดิมไม่เกิดผลซ้ำ

## 6. Button / User Action Mapping

| Action | Trigger | API / Service | Expected Result |
| --- | --- | --- | --- |
| Authenticate user endpoint | middleware | auth.verifyJwt | req.user = employeeId/roleCode/sectionCode |
| Authorize menu/role | middleware/service | rbac.requireMenu/requireRole | 403 FORBIDDEN เมื่อไม่มีสิทธิ์ |
| Validate request | controller | zod schema | 400 VALIDATION envelope |
| Return list | repository/service | PageResponse<T> | pagination shape เดียวกัน |
| Submit document action | service | documentAction.service.submit | return ActionResponse |
| Write audit | transaction | audit.service.write | reason/updated_by/old_value/new_value |
| Handle idempotency | service | requestId/business key | duplicate returns existing result or 409 per endpoint rule |

## 7. API Contract

### ALL /api/v1/sgi/*

Standard error envelope

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| - | none | No | Endpoint has no JSON body/query object |

#### Response

```json
{
  "code": "VALIDATION",
  "message": "ข้อความภาษาไทยตรงตาม SRS"
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| code | string | Yes | UTF-8; use value domain described by endpoint purpose |
| message | string | Yes | UTF-8; use value domain described by endpoint purpose |

### GET /api/v1/sgi/*

Standard list envelope เมื่อ endpoint เป็นรายการ

#### Query Params

```json
{
  "page": 1,
  "size": 20
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| page | integer | No | >= 1; default 1 |
| size | integer | No | 1..100; default 20 |

#### Response

```json
{
  "page": 1,
  "size": 20,
  "total": 0,
  "items": []
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| page | integer | Yes | >= 1; default 1 |
| size | integer | Yes | 1..100; default 20 |
| total | integer | Yes | UTF-8; use value domain described by endpoint purpose |
| items | array<object> | Yes | JSON array; element type shown in Type column |

### POST /api/v1/sgi/document/{docNo}/actions

**อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Document-Workflow-Actions (Tunyatorn)** · ยกมาเป็นตัวอย่างสัญญา action กลางที่ทุกเส้นต้องยึด (ตัวอย่าง currentSection=01 จึงเปลี่ยนไป 02)

#### Request

```json
{
  "result": "เห็นควรชดเชย",
  "comment": "เห็นควรชดเชยตามหลักเกณฑ์"
}
```

#### Request Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| result | string | Yes | UTF-8; use value domain described by endpoint purpose |
| comment | string | Yes | trimmed UTF-8 Thai text; required by operation/business rule |

#### Response

```json
{
  "statusCode": "02",
  "nextSection": "02",
  "message": "submitted"
}
```

#### Response Field Schema

| Field | Type | Required | Constraint / Meaning |
| --- | --- | --- | --- |
| statusCode | string | Yes | canonical code; do not replace with display label |
| nextSection | string | Yes | canonical code; do not replace with display label |
| message | string | Yes | UTF-8; use value domain described by endpoint purpose |

## 8. Skeleton Code (store-backend + BFF)

โครงโค้ดตั้งต้นของเอกสารฉบับนี้ ยึด convention จริงของ `srm-sps-spsap-store-backend` (NestJS 11 + TypeORM, schema `sps_store`, custom provider `DATA_SOURCE` ที่ route SELECT ไป slave pool) และ `srm-sps-spsap-sbp-bff` (ไม่มี DB, forward ผ่าน client service). ทุกจุดที่ต้องเติมกำกับด้วย `// TODO:` และ response ทุกเส้นถูกห่อเป็น `{success, data}` โดย ResponseInterceptor อยู่แล้ว จึงห้าม service ห่อซ้ำ

#### 8.1 ผังไฟล์ที่ต้องสร้าง

**เอกสารฉบับนี้ไม่ต้องสร้างไฟล์ใหม่** — ทุก endpoint ที่อยู่ในตาราง API เป็น contract กลาง หรือถูก implement ที่เอกสารอื่น/ระบบ SBP เดิมแล้ว (ดูตารางด้านล่าง) การสร้าง controller ซ้ำจะทำให้ NestJS มี 2 controller จอง route เดียวกันแล้ว register ตัวแรกชนะเงียบ ๆ

| Endpoint | จุดประสงค์ | implement ที่ไหน |
| --- | --- | --- |
| ALL /api/v1/sgi/* | Standard error envelope | contract กลาง/wildcard — ไม่ผูกกับ controller ใดเส้นเดียว |
| GET /api/v1/sgi/* | Standard list envelope เมื่อ endpoint เป็นรายการ | contract กลาง/wildcard — ไม่ผูกกับ controller ใดเส้นเดียว |
| POST /api/v1/sgi/document/{docNo}/actions | **อ้างอิงเท่านั้น — เจ้าของ endpoint นี้คือ LLDD-BE-API-Doc… | **reference — implement ที่เอกสาร `LLDD-BE-API-Document-Workflow-Actions`** (1 เส้น = 1 เจ้าของ ไม่ประกาศ controller ซ้ำ ไม่งั้น NestJS จะ register ทับกันเงียบ ๆ) |

#### 8.2 สัญญากลางที่ต้องยึด

```ts
// src/common/interceptors/response.interceptor.ts (มีอยู่แล้ว — ห้ามห่อซ้ำใน service)
// success : { success: true, data }
// error   : { success: false, data: null, error: { code, message } }
// TODO: endpoint ของ SGI ทุกเส้นต้องคืน error message ภาษาไทย verbatim ตาม SRS ผ่าน HttpException เท่านั้น
```

## 9. Database SQL

ไม่มี SQL เฉพาะของเอกสารนี้ — SQL ของแต่ละเส้นอยู่ในเอกสารเจ้าของ endpoint ตามตารางด้านบน

## 10. Processing Flow

| Step | Description |
| --- | --- |
| 1 | Request enters logging middleware and request id is attached |
| 2 | BffUserGuard ตรวจ x-api-key แล้ว map BFF header เป็น user context — 🔴 SGI ไม่ออก/ไม่ตรวจ JWT เอง (login อยู่ที่ Cognito ฝั่ง BFF) · เส้น service-token ใช้ API key แยก |
| 3 | RBAC guard checks role/menu/current workflow task owner |
| 4 | Validate params/query/body with shared schema conventions |
| 5 | Service executes business rule and document action if relevant |
| 6 | Mutation writes domain row and audit/reason in the same transaction |
| 7 | Controller maps result to standard envelope or throws AppError |
| 8 | Error handler maps all failures to `{code,message}` only |

## 11. Acceptance Criteria

- ทุก endpoint ต้องใช้ common contract นี้
- ไม่มี endpoint คืน error shape อื่นนอกจาก `{code,message}`
- 401/403/404/409/422/413/415 mapping คงที่และ test ได้
- GET list ทุกเส้นคืน `{page,size,total,items}`
- /actions รับ `{result,comment}` เท่านั้นและคืน `{statusCode,nextSection,message}`
- RBAC ใช้ role/menu/current task owner ฝั่ง BE เป็น source of truth
- workflow action ต้องเขียน sgi_consideration_logs · master mutation ไม่มี audit แล้ว (ยกเลิกระบบ audit ของ master 2026-08-07)

## 12. Developer Test Checklist

| No | Test |
| --- | --- |
| 1 | missing JWT 401 |
| 2 | role forbidden 403 |
| 3 | validation error 400 |
| 4 | not found 404 |
| 5 | duplicate conflict 409 |
| 6 | list envelope |
| 7 | action transition envelope |
| 8 | audit reason required |
| 9 | service token endpoint |
