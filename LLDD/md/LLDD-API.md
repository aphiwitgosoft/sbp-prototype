# LLDD API - REST API and Integration Contract

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารนี้เป็น LLDD API ระดับรวมของระบบ SBPGI/SBP Mall ใช้เป็น master reference สำหรับ REST contract, auth, error, endpoint catalog, implementation pattern และ test scope ของ BE API LLDD รายกลุ่ม

## 2. Scope

| Item | Detail |
| --- | --- |
| API base | /api/v1 |
| Endpoint count | 62 endpoints, 10 groups |
| Detailed implementation docs | LLDD-BE-API-Common-Contracts, LLDD-BE-API-Dashboard-Summary, LLDD-BE-API-Document-List-Search, LLDD-BE-API-Document-Create-Update, LLDD-BE-API-Document-Detail-Aggregate, LLDD-BE-API-Document-Workflow-Actions, LLDD-BE-API-Workflow-Instances, LLDD-BE-API-Attachment-Sales-Timeline, LLDD-BE-API-Lookup-RBAC-Email, LLDD-BE-API-Report-Master-Config |
| Out of scope | Login/Auth implementation ของ platform, SAP/SR process ภายนอก, abnormal-stores endpoints ที่ยัง comment รอตัดสินใจ |

## 2.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | Endpoint catalog, auth mode, role/access rules, request/response payloads, error conditions, and SQL references from the API plan data. |
| Progress | For each endpoint, apply middleware, bind DTO, validate, authorize, execute service transaction, map response, and pass errors through the centralized handler. |
| Output | Normalized REST contract for implementation and testing: method/path, payload, response, errors, DB usage, and checklist coverage. |

## 3. API Design Principles

| Rule | Required behavior | Developer note |
| --- | --- | --- |
| Transport | JSON UTF-8 ทุก endpoint; multipart เฉพาะ attachment upload | FE shared API client เป็นจุดเดียวที่ตั้ง base URL/header |
| Auth | User endpoint ใช้ Bearer JWT; internal workflow/interface ใช้ service token/API key | BE middleware ต้องแยก user token กับ service token ชัดเจน |
| Status convention | API ส่ง `statusCode`; FE resolve label จาก `/document-statuses` | ห้ามส่ง label ไทยแทน code ใน field ที่กำหนดเป็น canonical code |
| Role namespace | `roleCode` = RBAC role, `sectionCode` = workflow section, `roleProfileCode` = P-06/P-08/P-01/P-02/P-03 | ป้องกันการชนความหมายของเลข 01/02/03/06/08 |
| Pagination | GET list ใช้ `page,size` และคืน `{page,size,total,items}` | size max 100 ตาม common contract |
| Errors | คืน `{code,message}`; message ภาษาไทยตาม SRS ถ้ามี | FE แสดง message ตรง ๆ ไม่ paraphrase |
| Mutation audit | workflow action ลง consideration_logs; master/config/email ลง audit_logs; jobs ลง job_run_histories | mutation ที่ต้องมี reason ต้อง validate ก่อนเริ่ม transaction |

## 4. Endpoint Catalog

| Group | Count | Endpoint pattern | Implementation focus |
| --- | --- | --- | --- |
| Auth & สิทธิ์ผู้ใช้ (platform reference) | 4 | /api/v1/auth/login, /api/v1/auth/refresh, /api/v1/auth/me, /api/v1/me/menus | K2 · SRS 3.1.1 |
| งาน & เอกสารประกันรายได้ | 10 | /api/v1/tasks, /api/v1/documents, /api/v1/documents/{docNo}, /api/v1/documents ... | K2 · SRS 3.1.2 / 3.1.3 / 3.1.6 |
| ข้อมูลอ้างอิง (Lookup / Reference) | 4 | /api/v1/stores/search, /api/v1/competitors, /api/v1/document-statuses, /api/v1/workflow-sections | K2 + FGI/FCS · master สำหรับ dropdown |
| Master Data | 19 | /api/v1/operators, /api/v1/operators, /api/v1/operators/{id}, /api/v1/operators/{id} ... | K2 · SRS 3.1.8 / 3.1.9 |
| System Config (Global) | 5 | /api/v1/configs, /api/v1/configs/{key}, /api/v1/configs, /api/v1/configs/{key} ... | ใหม่ · system_configs |
| Email Template (Notification) | 5 | /api/v1/email-templates, /api/v1/email-templates/{code}, /api/v1/email-templates/{code}, /api/v1/email-templates/{code}/reset ... | ใหม่ · email_templates |
| รายงาน | 2 | /api/v1/reports/status-summary, /api/v1/reports/status-summary/export | K2 · SRS 3.1.7 |
| Batch Job Admin | 6 | /api/v1/jobs, /api/v1/jobs/{jobNo}, /api/v1/jobs/{jobNo}/params, /api/v1/jobs/{jobNo}/run ... | FGI/FCS · Jobs 1–10 |
| Workflow ภายใน | 3 | /api/v1/workflows/instances, /api/v1/workflows/instances/{id}, /api/v1/workflows/summary | K2 3.1.4 + FGI/FCS Job 8b |
| Interface & Dashboard | 4 | /api/v1/interfaces/tracking, /api/v1/interfaces/sta/ack, /api/v1/interfaces/pending-ack, /api/v1/dashboard/summary | FGI/FCS · tracking / watchdog |

## 5. Request Lifecycle

| Step | API behavior | Failure handling |
| --- | --- | --- |
| 1. Middleware | ตรวจ correlationId/requestId, auth token, content type, payload size | 401/413/415 ก่อนเข้า service |
| 2. Controller | รวม params/query/body เป็น DTO และเรียก service | controller ไม่ใส่ business rule |
| 3. Validation | required/format/enum/date/page/size/docNo/storeCode | 400/422 พร้อม code/message จาก catalog |
| 4. Authorization | ตรวจ menu/RBAC/document participant/current task owner/service token | 403 หรือ 409 เมื่อ task เปลี่ยนแล้ว |
| 5. Transaction | mutation เปิด transaction ใน service; read ใช้ read-only query | rollback เมื่อ persist หรือ audit fail |
| 6. Mapper | map domain object เป็น DTO ตาม API contract | ไม่ expose objectKey/secret/internal raw row |
| 7. Response | คืน JSON หรือ binary stream สำหรับ download | error ผ่าน centralized error handler |

## 6. Detailed Endpoint Specification

### 6.1 Auth & สิทธิ์ผู้ใช้ (platform reference)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | POST | /api/v1/auth/login | เข้าสู่ระบบด้วยบัญชีพนักงาน แลก JWT พร้อม role และ section สำหรับใช้ทุกเส้นถัดไป |
| 2 | POST | /api/v1/auth/refresh | ต่ออายุ accessToken โดยไม่ต้อง login ใหม่ |
| 3 | GET | /api/v1/auth/me | ข้อมูลผู้ใช้ปัจจุบันจาก JWT — FE ใช้แสดงชื่อ/role มุมขวาบน |
| 4 | GET | /api/v1/me/menus | เมนูที่ role ของผู้ใช้เข้าถึงได้ — FE ใช้สร้าง sidebar (แทนตารางสิทธิ์ 8 role ในหน้าจอ 3.1.1) |

#### 6.1.1 POST /api/v1/auth/login

เข้าสู่ระบบด้วยบัญชีพนักงาน แลก JWT พร้อม role และ section สำหรับใช้ทุกเส้นถัดไป

| Item | Detail |
| --- | --- |
| Global No. | 1 |
| Method | POST |
| Path | /api/v1/auth/login |
| Group | Auth & สิทธิ์ผู้ใช้ (platform reference) |
| Access / Role | ทุกคน (public) |
| Requirement Tag | K2 · 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ username/password กับ AD/LDAP ขององค์กร |
| 2 | โหลด user_accounts + role (00–10) และ section_code ของผู้ใช้ |
| 3 | ออก accessToken (30 นาที) + refreshToken (8 ชั่วโมง) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| user_accounts | R | บัญชีผู้ใช้ + role (ตารางใหม่) |
| roles | R | ชื่อ role 00–10 (K2 3.1.1) |

#### Request / Query / Header

```json
{
  "username": "phatcharida.p",
  "password": "********"
}
```

#### Response

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "d2f8a1...",
  "user": {
    "empId": "57123",
    "name": "ภัชริดา ประเสริฐ",
    "roles": ["03"],
    "sectionCode": "06"
  }
}
```

| Error / Condition |
| --- |
| 401 — ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง |
| 423 — บัญชีถูกล็อกจากการลองผิดเกินกำหนด |

SQL Reference

```sql
-- Platform SSO/AD/LDAP ตรวจ credential และส่ง employeeId ที่ยืนยันแล้วให้ SBPGI; SBPGI ไม่เก็บ password_hash
SELECT u.employee_id, u.role_code, u.section_code, r.role_name, e.emp_name, e.emp_mail, e.zone_code
FROM user_accounts u
JOIN roles r ON r.role_code = u.role_code
JOIN employees e ON e.employee_id = u.employee_id
WHERE u.employee_id = :employeeIdFromPlatform AND u.is_active = TRUE AND e.is_active = TRUE;
-- ออก JWT (access 30 นาที / refresh 8 ชม.) หลัง map local authorization สำเร็จ
```

#### 6.1.2 POST /api/v1/auth/refresh

ต่ออายุ accessToken โดยไม่ต้อง login ใหม่

| Item | Detail |
| --- | --- |
| Global No. | 2 |
| Method | POST |
| Path | /api/v1/auth/refresh |
| Group | Auth & สิทธิ์ผู้ใช้ (platform reference) |
| Access / Role | ผู้ถือ refreshToken |
| Requirement Tag | ใหม่ |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ refreshToken ยังไม่หมดอายุ/ไม่ถูกเพิกถอน |
| 2 | ออก accessToken ใหม่ |

| DB Object | R/W | Usage |
| --- | --- | --- |
| user_accounts | R | ตรวจสถานะบัญชียัง active |

#### Request / Query / Header

```json
{
  "refreshToken": "d2f8a1..."
}
```

#### Response

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

| Error / Condition |
| --- |
| 401 — token หมดอายุหรือถูกเพิกถอน ให้ login ใหม่ |

SQL Reference

```sql
SELECT employee_id, is_active FROM user_accounts
WHERE employee_id = :empId AND is_active = TRUE;
-- refreshToken ยังไม่ถูกเพิกถอน → ออก accessToken ใหม่
```

#### 6.1.3 GET /api/v1/auth/me

ข้อมูลผู้ใช้ปัจจุบันจาก JWT — FE ใช้แสดงชื่อ/role มุมขวาบน

| Item | Detail |
| --- | --- |
| Global No. | 3 |
| Method | GET |
| Path | /api/v1/auth/me |
| Group | Auth & สิทธิ์ผู้ใช้ (platform reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 |

| Step | Flow |
| --- | --- |
| 1 | ถอด JWT → คืนข้อมูลผู้ใช้และ section ปัจจุบัน |

| DB Object | R/W | Usage |
| --- | --- | --- |
| user_accounts | R | ข้อมูลผู้ใช้ล่าสุด |

#### Request / Query / Header

```json
(ไม่มี body — ใช้ JWT ใน header)
```

#### Response

```json
{
  "empId": "57123",
  "name": "ภัชริดา ประเสริฐ",
  "roles": ["03"],
  "sectionCode": "06",
  "zone": "RS"
}
```

| Error / Condition |
| --- |
| 401 — token หมดอายุ |

SQL Reference

```sql
SELECT u.employee_id, e.emp_name, e.emp_mail, u.role_code, u.section_code, e.zone_code
FROM user_accounts u JOIN employees e ON e.employee_id = u.employee_id
WHERE u.employee_id = :empIdFromJwt AND u.is_active = TRUE;
```

#### 6.1.4 GET /api/v1/me/menus

เมนูที่ role ของผู้ใช้เข้าถึงได้ — FE ใช้สร้าง sidebar (แทนตารางสิทธิ์ 8 role ในหน้าจอ 3.1.1)

| Item | Detail |
| --- | --- |
| Global No. | 4 |
| Method | GET |
| Path | /api/v1/me/menus |
| Group | Auth & สิทธิ์ผู้ใช้ (platform reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน role จาก JWT |
| 2 | join menu_permissions × menus เอาเฉพาะ can_access = true |
| 3 | คืนรายการเมนูเรียงตามกลุ่ม |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menu_permissions | R | สิทธิ์ต่อ role (composite PK) |
| menus | R | ชื่อ/กลุ่มเมนู |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "menus": [
    { "code": "M02", "name": "เอกสาร · รอดำเนินการ", "group": "ระบบประกันรายได้" },
    { "code": "M08", "name": "Batch Job", "group": "ระบบประกันรายได้" }
  ]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT m.menu_code, m.menu_name, m.menu_group
FROM menu_permissions mp JOIN menus m ON m.menu_code = mp.menu_code
WHERE mp.role_code = :roleFromJwt AND mp.can_access = TRUE
ORDER BY m.menu_group, m.sort_order;
```

### 6.2 งาน & เอกสารประกันรายได้

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/tasks | งานรอท่านดำเนินการ — เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า k2-list-waiting.html) |
| 2 | GET | /api/v1/documents | ค้นหาเอกสารที่เกี่ยวข้อง — บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS) |
| 3 | GET | /api/v1/documents/{docNo} | เอกสารฉบับเต็ม 12 ส่วนย่อย (k2-document.html) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน |
| 4 | POST | /api/v1/documents | สร้างเอกสารใหม่นอกเงื่อนไข หรือสร้างเอกสารที่ FS (สองแท็บของ k2-create.html) |
| 5 | PUT | /api/v1/documents/{docNo} | บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่ |
| 6 | POST | /api/v1/documents/{docNo}/actions | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · กฎวงเงิน 100,000 ใช้ทั้งกรณีชดเชยและไม่ชดเชย |
| 7 | GET | /api/v1/documents/{docNo}/timeline | ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร) |
| 8 | POST | /api/v1/documents/{docNo}/attachments | แนบไฟล์เข้าเอกสาร — จำกัด 5MB ต่อไฟล์ตาม SRS |
| 9 | GET | /api/v1/documents/{docNo}/attachments/{attachId}/download | ดาวน์โหลดไฟล์แนบผ่าน BE stream โดยตรวจสิทธิ์เอกสารและ scanStatus=CLEAN ก่อนส่ง binary |
| 10 | GET | /api/v1/documents/{docNo}/sales | ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง × 15 วัน) — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร k2-document.html |

#### 6.2.1 GET /api/v1/tasks

งานรอท่านดำเนินการ — เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า k2-list-waiting.html)

| Item | Detail |
| --- | --- |
| Global No. | 5 |
| Method | GET |
| Path | /api/v1/tasks |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | role ที่มีสิทธิ์เมนูเอกสาร |
| Requirement Tag | K2 · 3.1.2 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sectionCode ของผู้ใช้จาก JWT |
| 2 | query workflow_tasks สถานะ OPEN ของ section นั้น |
| 3 | join compensation_documents + impacted_stores คืน 9 คอลัมน์ตามหน้าจอ |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_tasks | R | งานค้างต่อ section (ตารางใหม่ — inbox) |
| compensation_documents | R | ข้อมูลเอกสาร |
| impacted_stores | R | ชื่อ/ภาคของร้าน |

#### Request / Query / Header

```json
Query: ?page=1&size=20&q=00788
(q = เลขที่เอกสาร / รหัสร้าน / ชื่อร้าน)
```

#### Response

```json
{
  "page": 1, "total": 24,
  "items": [{
    "docNo": "2569/00123",
    "storeCode": "00788",
    "storeName": "รัตนอุทิศ ซ.13",
    "impactMonth": "2026-06",
    "statusCode": "06",
    "currentSection": "06",
    "waitingDays": 3
  }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT t.doc_no, d.status_code, t.section_code, s.store_code, s.store_name, d.impact_month, t.opened_at
FROM workflow_tasks t
JOIN compensation_documents d ON d.doc_no = t.doc_no
JOIN stores s ON s.store_code = d.impacted_store_code
WHERE t.section_code = :sectionFromJwt AND t.task_status = :statusOpen
ORDER BY t.opened_at
LIMIT :size OFFSET :offset;
```

#### 6.2.2 GET /api/v1/documents

ค้นหาเอกสารที่เกี่ยวข้อง — บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 6 |
| Method | GET |
| Path | /api/v1/documents |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์เมนู |
| Requirement Tag | K2 · 3.1.3 / 3.1.7 |

| Step | Flow |
| --- | --- |
| 1 | validate: ต้องระบุ year เสมอ ไม่งั้นตอบ 400 |
| 2 | ค้น compensation_documents ตามเงื่อนไข (เลขที่ / ร้าน / สถานะ / เดือน) |
| 3 | คืนแบบแบ่งหน้า |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | R | เอกสารตามเงื่อนไข |
| impacted_stores | R | ข้อมูลร้าน |

#### Request / Query / Header

```json
Query: ?year=2569&storeCode=00788&status=06&page=1
(status = section ที่รออยู่ 06/08/01/02/03 หรือ END)
```

#### Response

```json
{
  "page": 1, "total": 6,
  "items": [{ "docNo": "2569/00123", "statusCode": "06", ... }]
}
```

| Error / Condition |
| --- |
| 400 — กรุณาระบุปีที่ต้องการค้นหา (กติกา SRS) |
| 401 |

SQL Reference

```sql
-- ต้องระบุ :year เสมอ ไม่งั้นตอบ 400 (กติกา SRS)
SELECT d.doc_no, d.status_code, d.impacted_store_code, s.store_name, d.impact_month
FROM compensation_documents d
JOIN stores s ON s.store_code = d.impacted_store_code
WHERE d.be_year = :year
  AND (:storeCode IS NULL OR d.impacted_store_code = :storeCode)
  AND (:status    IS NULL OR d.status_code = :status)
ORDER BY d.doc_no DESC
LIMIT :size OFFSET :offset;
```

#### 6.2.3 GET /api/v1/documents/{docNo}

เอกสารฉบับเต็ม 12 ส่วนย่อย (k2-document.html) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน

| Item | Detail |
| --- | --- |
| Global No. | 7 |
| Method | GET |
| Path | /api/v1/documents/{docNo} |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์เมนู |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | โหลดเอกสาร + ร้านใหม่ + คู่แข่ง + ปัจจัย + ไฟล์แนบ + สรุปชดเชย ในคำขอเดียว |
| 2 | คำนวณ permissions: ส่วนไหนแก้ได้ตาม role + current_section_code (data-editrole เดิม) |
| 3 | FE ใช้ธงนี้แสดงป้าย "อ่านอย่างเดียว" ต่อส่วน |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | R | หัวเอกสาร |
| document_new_stores / document_competitors / document_external_factors | R | ส่วนย่อย |
| document_attachments / consideration_logs | R | ไฟล์แนบ + ประวัติ |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "docNo": "2569/00123",
  "statusCode": "06",
  "currentSection": "06",
  "impactedStore": { "storeCode": "00788", ... },
  "newStores": [ { "storeCode": "15211", "compensatePercent": 60.0 } ],
  "competitors": [ ... ],
  "factors": [ ... ],
  "compensation": { "amount": 95000.00, "salesDropPercent": 12.5 },
  "permissions": { "canEditSections": ["competitor","factor"], "canAction": true }
}
```

| Error / Condition |
| --- |
| 404 — ไม่พบเอกสาร |
| 401 |

SQL Reference

```sql
-- โหลดเอกสารฉบับเต็ม 12 ส่วนในคำขอเดียว
SELECT * FROM compensation_documents      WHERE doc_no = :docNo;
SELECT * FROM document_new_stores          WHERE doc_no = :docNo;
SELECT * FROM document_competitors         WHERE doc_no = :docNo;
SELECT * FROM document_external_factors    WHERE doc_no = :docNo;
SELECT * FROM document_attachments         WHERE doc_no = :docNo;
SELECT * FROM consideration_logs           WHERE doc_no = :docNo ORDER BY action_datetime;
```

#### 6.2.4 POST /api/v1/documents

สร้างเอกสารใหม่นอกเงื่อนไข หรือสร้างเอกสารที่ FS (สองแท็บของ k2-create.html)

| Item | Detail |
| --- | --- |
| Global No. | 8 |
| Method | POST |
| Path | /api/v1/documents |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | 02 HQ, 03 User Admin |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจซ้ำ: ร้าน + เดือนที่ถูกกระทบ ต้องยังไม่มีเอกสาร |
| 2 | ออกเลขที่ YYYY/xxxxx (running ต่อปี เริ่ม 00001 — กติกา SRS) |
| 3 | insert compensation_documents สถานะเริ่มต้น + เปิด workflow_instances / workflow_tasks แรก (Section 06) |
| 4 | ส่งอีเมลตาม status_email_rules |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | W | เอกสารใหม่ |
| workflow_instances / workflow_tasks | W | เปิด workflow + งานแรก |
| status_email_rules | R | ผู้รับอีเมล TO/CC |

#### Request / Query / Header

```json
{
  "impactedStoreCode": "00788",
  "impactMonth": "2026-06",
  "source": "MANUAL"   // MANUAL | FS
}
```

#### Response

```json
201 Created
{
  "docNo": "2569/00124"
}
```

| Error / Condition |
| --- |
| 409 — ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว |
| 422 — ข้อมูลบังคับไม่ครบ |

SQL Reference

```sql
-- กันซ้ำ: เอกสารจาก impact_process เดียวกันต้องมีได้รายการเดียว
SELECT 1 FROM compensation_documents
WHERE impact_process_id = :impactProcessId;

-- ออกเลขที่ YYYY/xxxxx (running ต่อปี) แล้วสร้างเอกสาร + เปิด workflow งานแรก (Section 06)
INSERT INTO compensation_documents (doc_no, be_year, running_no, impact_process_id, impacted_store_code, impact_month, status_code, current_section_code, created_by)
VALUES (:docNo, :year, :runningNo, :impactProcessId, :storeCode, :month, :statusInit, :section06, :empId);
INSERT INTO workflow_instances (instance_id, doc_no, instance_status, started_at, started_by)
VALUES (:instanceId, :docNo, :active, :now, :empId);
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status)
VALUES (:instanceId, :docNo, :section06, :statusOpen);
```

#### 6.2.5 PUT /api/v1/documents/{docNo}

บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่

| Item | Detail |
| --- | --- |
| Global No. | 9 |
| Method | PUT |
| Path | /api/v1/documents/{docNo} |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตาม section ปัจจุบัน |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่า role + section ปัจจุบันมีสิทธิ์แก้ส่วนที่ส่งมา (เช่น Section 01 แก้คู่แข่ง/ปัจจัยได้) |
| 2 | validate %ชดเชยของร้านใหม่รวมกันต้องเท่ากับ 100% |
| 3 | บันทึกและคืนเอกสารล่าสุด |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_new_stores | R/W | %ชดเชย · ระยะห่าง |
| document_competitors | R/W | คู่แข่ง |
| document_external_factors | R/W | ปัจจัยภายนอก |

#### Request / Query / Header

```json
{
  "newStores": [ { "newStoreCode": "00990", "compensatePercent": 60.0 },
                 { "newStoreCode": "00991", "compensatePercent": 40.0 } ]
}
```

#### Response

```json
200 OK — เอกสารฉบับล่าสุด (โครงเดียวกับ GET)
```

| Error / Condition |
| --- |
| 403 — ไม่มีสิทธิ์แก้ส่วนนี้ในขั้นปัจจุบัน |
| 422 — "%ชดเชย ... รวมกันแล้วไม่เท่ากับ 100%" (ข้อความตรงตาม SRS) |

SQL Reference

```sql
-- ตรวจสิทธิ์ตาม role + current_section ก่อน · %ชดเชยร้านใหม่รวมกันต้อง = 100% (ไม่งั้น 422)
-- optimistic concurrency: mutation ทุกชุดต้องส่ง versionNo ล่าสุด; ไม่ตรงคืน 409 STALE_VERSION
UPDATE compensation_documents SET version_no = version_no + 1, updated_at = :now, updated_by = :empId
WHERE doc_no = :docNo AND version_no = :versionNo;
UPDATE document_new_stores       SET compensate_percent = :pct   WHERE new_store_code = :newStoreCode AND doc_no = :docNo;
UPDATE document_competitors      SET impact_date = :date         WHERE id = :competitorId AND doc_no = :docNo;
UPDATE document_external_factors SET date_from = :from, date_to = :to WHERE id = :factorId AND doc_no = :docNo;
```

#### 6.2.6 POST /api/v1/documents/{docNo}/actions

ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · กฎวงเงิน 100,000 ใช้ทั้งกรณีชดเชยและไม่ชดเชย

| Item | Detail |
| --- | --- |
| Global No. | 10 |
| Method | POST |
| Path | /api/v1/documents/{docNo}/actions |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | เจ้าของ task ปัจจุบัน |
| Requirement Tag | K2 · 3.1.4 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่าผู้ใช้เป็นเจ้าของ workflow_tasks ขั้นปัจจุบัน |
| 2 | validate เลือกผลแล้ว — ไม่งั้น 422 ข้อความ SRS ตรงตัว |
| 3 | คำนวณขั้นถัดไปตามตารางเส้นทาง (ตารางเส้นทาง workflow): 06 ไม่ชดเชย/หยุดชดเชย → เสร็จสิ้น · 02 ชดเชย/ไม่ชดเชย > 100,000 → 03 → จบ · ชดเชย ≤ 100,000 → เสร็จสิ้น (จบที่ GM) · ไม่ชดเชย ≤ 100,000 → กลับ 06 · ตัดขั้นบัญชี 04/05 (SDD v7.5) · ทุกขั้นมีเส้นส่งกลับ |
| 4 | insert consideration_logs + ปิด task เดิม เปิด task ใหม่ |
| 5 | ส่งอีเมล TO/CC ตาม status_email_rules |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_tasks | R/W | ปิดงานเดิม เปิดงานขั้นถัดไป |
| compensation_documents | W | อัปเดต Status + CurSection |
| consideration_logs | W | บันทึกผลพิจารณา |
| status_email_rules | R | ผู้รับอีเมล |

#### Request / Query / Header

```json
{
  "result": "เห็นควรชดเชย",
  // 6-enum verbatim: เห็นควรชดเชย / เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้
  // / ส่งฝ่ายส่งเสริมธุรกิจ SBP / ส่งเจ้าหน้าที่ SBP DSA / ส่งกลับ
  "comment": "เห็นควรชดเชยตามหลักเกณฑ์"
}
```

#### Response

```json
{
  "nextSection": "02",
  "statusCode": "02",
  "message": "ส่งดำเนินการสำเร็จ"
}
```

| Error / Condition |
| --- |
| 422 — "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ" |
| 403 — ไม่ใช่เจ้าของงานขั้นนี้ |
| 409 — งานถูกดำเนินการไปแล้วโดยผู้อื่น |

SQL Reference

```sql
-- ตรวจเป็นเจ้าของงานขั้นปัจจุบัน + ต้องเลือก result แล้ว (ไม่งั้น 422)
-- result รับ 6-enum verbatim เท่านั้น: เห็นควรชดเชย / เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้ / ส่งฝ่ายส่งเสริมธุรกิจ SBP / ส่งเจ้าหน้าที่ SBP DSA / ส่งกลับ
UPDATE workflow_tasks SET task_status = :statusClosed, action_result = :result, closed_at = :now
WHERE doc_no = :docNo AND section_code = :curSection AND task_status = :statusOpen;

INSERT INTO consideration_logs (doc_no, section_code, consider_by, result, detail, action_datetime)
VALUES (:docNo, :curSection, :empId, :result, :comment, :now);

-- คำนวณขั้นถัดไป (กฎวงเงิน 100,000) → เปิดงานใหม่ + อัปเดตสถานะเอกสารแบบ optimistic lock
UPDATE compensation_documents SET status_code = :nextStatus, current_section_code = :nextSection, version_no = version_no + 1, updated_at = :now, updated_by = :empId
WHERE doc_no = :docNo AND version_no = :versionNo;
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status)
VALUES (:instanceId, :docNo, :nextSection, :statusOpen);

SELECT r.status_code, d.status_name, r.to_section_code, r.cc_section_code
FROM status_email_rules r JOIN document_statuses d ON d.status_code = r.status_code
WHERE r.status_code = :nextStatus;
```

#### 6.2.7 GET /api/v1/documents/{docNo}/timeline

ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร)

| Item | Detail |
| --- | --- |
| Global No. | 11 |
| Method | GET |
| Path | /api/v1/documents/{docNo}/timeline |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์เมนู |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน consideration_logs เรียงตามเวลา |

| DB Object | R/W | Usage |
| --- | --- | --- |
| consideration_logs | R | ประวัติครบทุกขั้น |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{
    "section": "06",
    "considerName": "สมชาย ใจดี",
    "result": "ชดเชย",
    "detail": "ตรวจสอบแล้วเข้าเกณฑ์",
    "actionDateTime": "2026-06-18T10:42:00"
  }]
}
```

| Error / Condition |
| --- |
| 404 |

SQL Reference

```sql
SELECT section_code, consider_by, result, detail, action_datetime
FROM consideration_logs
WHERE doc_no = :docNo
ORDER BY action_datetime;
```

#### 6.2.8 POST /api/v1/documents/{docNo}/attachments

แนบไฟล์เข้าเอกสาร — จำกัด 5MB ต่อไฟล์ตาม SRS

| Item | Detail |
| --- | --- |
| Global No. | 12 |
| Method | POST |
| Path | /api/v1/documents/{docNo}/attachments |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตาม section ปัจจุบัน |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | รับ multipart/form-data (file + sectionCode) |
| 2 | ตรวจขนาด ≤ 5MB และชนิดไฟล์ที่อนุญาต |
| 3 | sanitize filename + คำนวณ sha256 |
| 4 | run AV scan |
| 5 | เก็บ binary ใน object storage และบันทึก metadata document_attachments |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_attachments | W | เมทาดาต้าไฟล์ + bucket/object_key/sha256/scan_status |

#### Request / Query / Header

```json
multipart/form-data
  file: (binary ≤ 5MB)
  sectionCode: "06"
```

#### Response

```json
201 Created
{ "attachId": 771, "fileName": "หนังสือแจ้งผล.pdf", "scanStatus": "CLEAN" }
```

| Error / Condition |
| --- |
| 413 — ไฟล์เกิน 5MB |
| 415 — ชนิดไฟล์ไม่อนุญาต |
| 422 — ไฟล์แนบไม่ผ่านการตรวจสอบความปลอดภัย |

SQL Reference

```sql
-- ตรวจขนาด ≤ 5MB, sanitize filename, sha256, AV scan=CLEAN ก่อน commit metadata
INSERT INTO document_attachments (doc_no, section_code, file_name, mime_type, file_size, storage_provider, bucket, object_key, sha256, scan_status, uploaded_by, uploaded_at)
VALUES (:docNo, :sectionCode, :fileName, :mimeType, :fileSize, :storageProvider, :bucket, :objectKey, :sha256, :scanClean, :empId, :now);
```

#### 6.2.9 GET /api/v1/documents/{docNo}/attachments/{attachId}/download

ดาวน์โหลดไฟล์แนบผ่าน BE stream โดยตรวจสิทธิ์เอกสารและ scanStatus=CLEAN ก่อนส่ง binary

| Item | Detail |
| --- | --- |
| Global No. | 13 |
| Method | GET |
| Path | /api/v1/documents/{docNo}/attachments/{attachId}/download |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์อ่านเอกสาร |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจสิทธิ์อ่านเอกสารและ attachment ต้องผูกกับ docNo |
| 2 | ตรวจ scan_status = CLEAN |
| 3 | อ่าน object storage ผ่าน bucket/object_key |
| 4 | stream ผ่าน BE พร้อม Content-Disposition; ไม่ expose permanent bucket URL |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_attachments | R | metadata + object key + scan status |
| object storage | R | binary file |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
200 binary stream
Content-Disposition: attachment; filename="หนังสือแจ้งผล.pdf"
```

| Error / Condition |
| --- |
| 403 — ไม่มีสิทธิ์อ่านเอกสาร |
| 404 — ไม่พบไฟล์แนบ |
| 409 — ไฟล์ยังไม่พร้อมให้ดาวน์โหลด |
| 422 — ไฟล์ไม่ผ่านการตรวจสอบความปลอดภัย |

SQL Reference

```sql
-- ตรวจสิทธิ์อ่านเอกสาร + attachment ต้องเป็นของ docNo + scan_status=CLEAN ก่อน stream ผ่าน BE
SELECT attach_id, bucket, object_key, file_name, mime_type, scan_status
FROM document_attachments
WHERE doc_no = :docNo AND attach_id = :attachId;
```

#### 6.2.10 GET /api/v1/documents/{docNo}/sales

ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง × 15 วัน) — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร k2-document.html

| Item | Detail |
| --- | --- |
| Global No. | 14 |
| Method | GET |
| Path | /api/v1/documents/{docNo}/sales |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์เมนู |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | หา impact_process_id ของเอกสารจาก compensation_documents |
| 2 | อ่าน fgi_impact_sales_summaries (หัว) + sales_transactions (รายวัน) ของงวดนั้น (โซน A) |
| 3 | คืน growth_rate_diff · total_working_days + แถวยอดขายรายวันแยก 4 หน้าต่าง |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | R | หา impact_process_id ของเอกสาร |
| fgi_impact_sales_summaries | R | หัวยอดขาย · growth_rate_diff · total_working_days |
| sales_transactions | R | ยอดขายรายวัน 4 หน้าต่าง × 15 วัน |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "growthRateDiff": -12.45,
  "totalWorkingDays": 60,
  "windows": [
    { "label": "ก่อนเปิด 15 วัน",
      "rows": [ { "date": "2026-05-01", "amount": 42500.00 } ] }
  ]
}
```

| Error / Condition |
| --- |
| 404 — ไม่พบเอกสารหรือยอดขายของงวดนี้ |
| 401 |

SQL Reference

```sql
-- หา impact_process_id ของเอกสาร แล้วอ่านยอดขาย 4 หน้าต่าง × 15 วัน
SELECT ss.id AS sales_summary_id, ss.growth_rate_diff, ss.total_working_days
FROM compensation_documents d
JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = d.impact_process_id
WHERE d.doc_no = :docNo;

SELECT window_no, txn_date, sales_amount, sales_diff, is_outlier
FROM sales_transactions
WHERE sales_summary_id = :salesSummaryId
ORDER BY window_no, txn_date;
```

### 6.3 ข้อมูลอ้างอิง (Lookup / Reference)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/stores/search | ค้นหาร้าน (แว่นขยายในหน้า k2-create.html) — ร้านถูกกระทบ (SP) หรือร้านเปิดใหม่ 7-Eleven ตาม type |
| 2 | GET | /api/v1/competitors | รายการร้านคู่แข่ง master 24 ราย — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html) |
| 3 | GET | /api/v1/document-statuses | รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report) |
| 4 | GET | /api/v1/workflow-sections | รายการ Section 5 ขั้น — dropdown เลือกตำแหน่ง/ขั้น (หน้า 3.1.8) และตัวกรองตาม section |

#### 6.3.1 GET /api/v1/stores/search

ค้นหาร้าน (แว่นขยายในหน้า k2-create.html) — ร้านถูกกระทบ (SP) หรือร้านเปิดใหม่ 7-Eleven ตาม type

| Item | Detail |
| --- | --- |
| Global No. | 15 |
| Method | GET |
| Path | /api/v1/stores/search |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ตามสิทธิ์เมนูเอกสาร |
| Requirement Tag | FGI/FCS master + K2 |

| Step | Flow |
| --- | --- |
| 1 | รับ q (รหัส/ชื่อร้าน) + type (impacted \| new) |
| 2 | type=impacted → ค้น impacted_stores (ร้าน SP) |
| 3 | type=new → ค้น stores (master สาขา 7-Eleven ทุกประเภท) |
| 4 | คืนรายการสั้นสำหรับ popup เลือก (คงเลขศูนย์นำหน้ารหัสร้าน) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| stores | R | master สาขา 7-Eleven — ร้านเปิดใหม่ (โซน C) |
| impacted_stores | R | ร้าน SP — ร้านถูกกระทบ |

#### Request / Query / Header

```json
Query: ?q=00788&type=impacted
(type = impacted | new)
```

#### Response

```json
{
  "items": [{ "storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13", "storeType": "SP" }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- type = impacted → ร้าน SP ; type = new → สาขา 7-Eleven ทุกประเภท
-- type = impacted:
SELECT s.store_code, s.store_name, 'SP' AS store_type FROM impacted_stores i
JOIN stores s ON s.store_code = i.store_code
WHERE s.store_code LIKE :q OR s.store_name LIKE :q
LIMIT 20;
-- type = new:
SELECT store_code, store_name, store_type FROM stores
WHERE store_code LIKE :q OR store_name LIKE :q
LIMIT 20;
```

#### 6.3.2 GET /api/v1/competitors

รายการร้านคู่แข่ง master 24 ราย — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html)

| Item | Detail |
| --- | --- |
| Global No. | 16 |
| Method | GET |
| Path | /api/v1/competitors |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ตาม section ปัจจุบัน |
| Requirement Tag | K2 · master คู่แข่ง |

| Step | Flow |
| --- | --- |
| 1 | query competitors ทั้งหมด / ตามคำค้น |
| 2 | คืนรหัส + ชื่อคู่แข่งสำหรับเลือกใส่ document_competitors |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | R | master ร้านคู่แข่ง 24 ราย (108 Shop, Lotus Express, CJ …) |

#### Request / Query / Header

```json
Query: ?q=lotus
```

#### Response

```json
{
  "items": [{ "competitorCode": "C007", "competitorName": "Lotus Express" }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT competitor_code, competitor_name
FROM competitors
WHERE :q IS NULL OR competitor_name LIKE :q
ORDER BY competitor_name;
```

#### 6.3.3 GET /api/v1/document-statuses

รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report)

| Item | Detail |
| --- | --- |
| Global No. | 17 |
| Method | GET |
| Path | /api/v1/document-statuses |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · 3.1.3 / 3.1.7 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน document_statuses ทั้งหมดเรียงตามลำดับ workflow |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_statuses | R | สถานะเอกสาร (06/08/01/02/03/99; 99=เสร็จสิ้น) |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{ "statusCode": "06", "statusName": "รอฝ่าย SBP DSA ดำเนินการ" }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT status_code, status_name, sort_order
FROM document_statuses
ORDER BY sort_order;
```

#### 6.3.4 GET /api/v1/workflow-sections

รายการ Section 5 ขั้น — dropdown เลือกตำแหน่ง/ขั้น (หน้า 3.1.8) และตัวกรองตาม section

| Item | Detail |
| --- | --- |
| Global No. | 18 |
| Method | GET |
| Path | /api/v1/workflow-sections |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · master section |

| Step | Flow |
| --- | --- |
| 1 | อ่าน workflow_sections ทั้งหมดเรียงตามลำดับ 06→08→01→02→03 |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_sections | R | ขั้นตอน 06/08/01/02/03 |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{ "sectionCode": "06", "sectionName": "ฝ่าย SBP DSA" }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT section_code, section_name, sort_order
FROM workflow_sections
ORDER BY sort_order;
```

### 6.4 Master Data

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/operators | รายชื่อผู้ปฏิบัติงาน (operator_assignments) พร้อมค้นหา/แบ่งหน้า |
| 2 | POST | /api/v1/operators | เพิ่มผู้ปฏิบัติงานใหม่ (จากหน้าค้นหาพนักงานด้วยแว่นขยาย) |
| 3 | PUT | /api/v1/operators/{id} | แก้ไขข้อมูลผู้ปฏิบัติงาน |
| 4 | DELETE | /api/v1/operators/{id} | ลบผู้ปฏิบัติงาน พร้อมบันทึกเหตุผล |
| 5 | GET | /api/v1/factors | รายการปัจจัยภายนอก (external_factors) |
| 6 | POST | /api/v1/factors | เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS) |
| 7 | PUT | /api/v1/factors/{code} | แก้ไขปัจจัยภายนอก |
| 8 | DELETE | /api/v1/factors/{code} | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) |
| 9 | GET | /api/v1/employees/search | ค้นหาพนักงานจากระบบ HR (popup แว่นขยายในหน้า 3.1.8) |
| 10 | GET | /api/v1/menu-permissions | ตาราง matrix สิทธิ์เมนูทั้งหมด (8 role × เมนู) — หน้าจอสิทธิ์การเข้าถึงเมนู |
| 11 | PUT | /api/v1/menu-permissions/{menuCode} | แก้สิทธิ์การเข้าถึงเมนูหนึ่งรายการต่อทุก role — บันทึก audit เสมอ |
| 12 | GET | /api/v1/roles | รายการ Role ทั้งหมด (ตารางกลุ่มผู้ใช้งานในหน้าจอ 3.1.1 และ dropdown ที่อื่น) |
| 13 | POST | /api/v1/roles | เพิ่ม Role ใหม่ — ระบบสร้างสิทธิ์เมนูเริ่มต้นเป็น "ไม่มีสิทธิ์" ทุกเมนู |
| 14 | PUT | /api/v1/roles/{roleCode} | แก้ชื่อ/คำอธิบาย Role — ต้องระบุเหตุผล บันทึก audit เสมอ |
| 15 | DELETE | /api/v1/roles/{roleCode} | ลบ Role — ลบไม่ได้ถ้าเป็น Role ระบบ (is_system) หรือยังมีผู้ใช้อ้างอยู่ |
| 16 | POST | /api/v1/menus | เพิ่มเมนูใหม่เข้าระบบ — สิทธิ์เริ่มต้นเป็น "ไม่มีสิทธิ์" ทุก Role |
| 17 | PUT | /api/v1/menus/{menuCode} | แก้ชื่อ/กลุ่ม/ลำดับเมนู — ต้องระบุเหตุผล บันทึก audit เสมอ |
| 18 | DELETE | /api/v1/menus/{menuCode} | ลบเมนูพร้อมสิทธิ์ทุก Role ของเมนูนั้น (cascade) — เมนูระบบลบไม่ได้ |
| 19 | GET | /api/v1/audit-logs | ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม→ใหม่ · เหตุผล · เมื่อไร) — แผงประวัติท้ายหน้าจอ 3.1.8 / 3.1.9 |

#### 6.4.1 GET /api/v1/operators

รายชื่อผู้ปฏิบัติงาน (operator_assignments) พร้อมค้นหา/แบ่งหน้า

| Item | Detail |
| --- | --- |
| Global No. | 19 |
| Method | GET |
| Path | /api/v1/operators |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.8 |

| Step | Flow |
| --- | --- |
| 1 | query ตามเงื่อนไข (ชื่อ / section / zone) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| operator_assignments | R | master ผู้ปฏิบัติงาน (เทียบจาก SRS) |

#### Request / Query / Header

```json
Query: ?q=สมชาย&sectionCode=06&page=1
```

#### Response

```json
{
  "items": [{
    "operatorAssignmentId": 12,
    "empName": "สมชาย ใจดี",
    "empMail": "somchai@cpall.co.th",
    "sectionCode": "06",
    "zoneCode": "RS"
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT id AS operator_assignment_id, emp_name, emp_mail, section_code, zone_code
FROM operator_assignments
WHERE (:q IS NULL OR emp_name LIKE :q)
  AND (:sectionCode IS NULL OR section_code = :sectionCode)
ORDER BY emp_name
LIMIT :size OFFSET :offset;
```

#### 6.4.2 POST /api/v1/operators

เพิ่มผู้ปฏิบัติงานใหม่ (จากหน้าค้นหาพนักงานด้วยแว่นขยาย)

| Item | Detail |
| --- | --- |
| Global No. | 20 |
| Method | POST |
| Path | /api/v1/operators |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.8 |

| Step | Flow |
| --- | --- |
| 1 | validate พนักงานมีจริง (จากเส้น employees/search) |
| 2 | insert + บันทึก audit_logs (ADD) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| operator_assignments | W | แถวใหม่ |
| audit_logs | W | audit การเพิ่ม |

#### Request / Query / Header

```json
{
  "empId": "57123",
  "empName": "สมชาย ใจดี",
  "empMail": "somchai@cpall.co.th",
  "sectionCode": "06",
  "zoneCode": "RS"
}
```

#### Response

```json
201 Created — { "operatorAssignmentId": 31 }
```

| Error / Condition |
| --- |
| 409 — พนักงานคนนี้อยู่ใน section นี้แล้ว |

SQL Reference

```sql
INSERT INTO operator_assignments (employee_id, emp_name, emp_mail, section_code, zone_code)
VALUES (:empId, :empName, :empMail, :sectionCode, :zoneCode);

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :empId, :actionAdd, :newValue, :actor, :now);
```

#### 6.4.3 PUT /api/v1/operators/{id}

แก้ไขข้อมูลผู้ปฏิบัติงาน

| Item | Detail |
| --- | --- |
| Global No. | 21 |
| Method | PUT |
| Path | /api/v1/operators/{id} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.8 |

| Step | Flow |
| --- | --- |
| 1 | validate: ต้องระบุ reason เสมอ (กติกา SRS) |
| 2 | update + บันทึก audit_logs (EDIT · old_value → new_value · เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| operator_assignments | W | แก้ไข |
| audit_logs | W | audit |

#### Request / Query / Header

```json
{
  "empMail": "somchai.j@cpall.co.th",
  "zoneCode": "RN",
  "reason": "ปรับพื้นที่รับผิดชอบตามโครงสร้างใหม่"   // บังคับ (SRS)
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 422 — กรุณาระบุเหตุผลการแก้ไขข้อมูล |
| 404 |

SQL Reference

```sql
-- ต้องระบุ :reason เสมอ (กติกา SRS)
UPDATE operator_assignments SET emp_mail = :empMail, zone_code = :zoneCode WHERE id = :id;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :id, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.4.4 DELETE /api/v1/operators/{id}

ลบผู้ปฏิบัติงาน พร้อมบันทึกเหตุผล

| Item | Detail |
| --- | --- |
| Global No. | 22 |
| Method | DELETE |
| Path | /api/v1/operators/{id} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.8 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่าไม่ถืองานค้างใน workflow_tasks |
| 2 | ลบ + บันทึก audit_logs (DELETE + เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| operator_assignments | W | ลบแถว |
| audit_logs | W | audit + เหตุผล |
| workflow_tasks | R | ตรวจงานค้าง |

#### Request / Query / Header

```json
{ "reason": "ย้ายหน่วยงาน" }
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — ยังถืองานค้างอยู่ ต้องแจกงานใหม่ก่อน |

SQL Reference

```sql
-- ตรวจไม่ถืองานค้างก่อนลบ (ไม่งั้น 409)
SELECT 1 FROM workflow_tasks WHERE assignee_employee_id = :empId AND task_status = :statusOpen;

DELETE FROM operator_assignments WHERE id = :id;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :id, :actionDelete, :oldValue, :reason, :actor, :now);
```

#### 6.4.5 GET /api/v1/factors

รายการปัจจัยภายนอก (external_factors)

| Item | Detail |
| --- | --- |
| Global No. | 23 |
| Method | GET |
| Path | /api/v1/factors |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | query ทั้งหมด / ตามคำค้น |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | R | master ปัจจัย (เทียบจาก SRS) |

#### Request / Query / Header

```json
Query: ?q=ถนน
```

#### Response

```json
{
  "items": [{ "factorCode": "F001", "factorName": "ปิดถนน/ซ่อมถนน", "factorRemark": "..." }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT factor_code, factor_name, factor_remark
FROM external_factors
WHERE :q IS NULL OR factor_name LIKE :q
ORDER BY factor_code;
```

#### 6.4.6 POST /api/v1/factors

เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 24 |
| Method | POST |
| Path | /api/v1/factors |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ factor_code ไม่ซ้ำ |
| 2 | insert + audit_logs |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | แถวใหม่ |
| audit_logs | W | audit |

#### Request / Query / Header

```json
{ "factorCode": "F009", "factorName": "คู่แข่งจัดโปรโมชัน", "factorRemark": "" }
```

#### Response

```json
201 Created
```

| Error / Condition |
| --- |
| 409 — รหัสปัจจัยนี้มีอยู่แล้ว |

SQL Reference

```sql
-- factor_code ห้ามซ้ำ (ไม่งั้น 409)
INSERT INTO external_factors (factor_code, factor_name, factor_remark)
VALUES (:factorCode, :factorName, :factorRemark);

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :factorCode, :actionAdd, :newValue, :actor, :now);
```

#### 6.4.7 PUT /api/v1/factors/{code}

แก้ไขปัจจัยภายนอก

| Item | Detail |
| --- | --- |
| Global No. | 25 |
| Method | PUT |
| Path | /api/v1/factors/{code} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | validate: ต้องระบุ reason เสมอ (กติกา SRS) |
| 2 | update + audit_logs (EDIT · old_value → new_value · เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | แก้ไข |
| audit_logs | W | audit |

#### Request / Query / Header

```json
{
  "factorName": "คู่แข่งจัดโปรโมชันใหญ่",
  "reason": "ขยายนิยามให้ชัดเจนขึ้น"   // บังคับ (SRS)
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 422 — กรุณาระบุเหตุผลการแก้ไขข้อมูล |
| 404 |

SQL Reference

```sql
-- ต้องระบุ :reason เสมอ
UPDATE external_factors SET factor_name = :factorName, factor_remark = :factorRemark
WHERE factor_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.4.8 DELETE /api/v1/factors/{code}

ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด)

| Item | Detail |
| --- | --- |
| Global No. | 26 |
| Method | DELETE |
| Path | /api/v1/factors/{code} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจไม่ถูกอ้างใน document_external_factors |
| 2 | ลบ + audit_logs |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | ลบแถว |
| document_external_factors | R | ตรวจการใช้งาน |
| audit_logs | W | audit |

#### Request / Query / Header

```json
{ "reason": "เลิกใช้" }
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — ปัจจัยถูกใช้ในเอกสารอยู่ ลบไม่ได้ |

SQL Reference

```sql
-- ตรวจไม่ถูกอ้างในเอกสารก่อนลบ (ไม่งั้น 409)
SELECT 1 FROM document_external_factors WHERE factor_code = :code;

DELETE FROM external_factors WHERE factor_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionDelete, :oldValue, :reason, :actor, :now);
```

#### 6.4.9 GET /api/v1/employees/search

ค้นหาพนักงานจากระบบ HR (popup แว่นขยายในหน้า 3.1.8)

| Item | Detail |
| --- | --- |
| Global No. | 27 |
| Method | GET |
| Path | /api/v1/employees/search |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 3.1.8 + master FGI/FCS |

| Step | Flow |
| --- | --- |
| 1 | ค้นจาก employees (ตาราง master ที่ฝั่ง batch ใช้ join อยู่แล้ว) |
| 2 | คืนรายการสั้นสำหรับ popup เลือก |

| DB Object | R/W | Usage |
| --- | --- | --- |
| employees | R | master พนักงาน (โซน master เดิมของ FGI/FCS) |

#### Request / Query / Header

```json
Query: ?q=สมชาย (ชื่อ / รหัสพนักงาน)
```

#### Response

```json
{
  "items": [{ "empId": "57123", "name": "สมชาย ใจดี", "mail": "somchai@cpall.co.th", "dept": "SBP DSA" }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT employee_id, emp_name, emp_mail, department
FROM employees
WHERE emp_name LIKE :q OR employee_id LIKE :q
ORDER BY emp_name
LIMIT 20;
```

#### 6.4.10 GET /api/v1/menu-permissions

ตาราง matrix สิทธิ์เมนูทั้งหมด (8 role × เมนู) — หน้าจอสิทธิ์การเข้าถึงเมนู

| Item | Detail |
| --- | --- |
| Global No. | 28 |
| Method | GET |
| Path | /api/v1/menu-permissions |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | K2 · 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน menu_permissions ทั้งหมด join menus + roles |
| 2 | คืนเป็น matrix ต่อเมนู |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menu_permissions | R | สิทธิ์ต่อ role (composite PK) |
| menus / roles | R | ชื่อเมนูและ role 00–10 |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "menus": [{
    "menuCode": "M07",
    "menuName": "รายงานสรุปสถานะ",
    "access": { "00": false, "01": true, "02": false, "03": false, "04": true, "05": false, "06": true, "10": false }
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT m.menu_code, m.menu_name, mp.role_code, mp.can_access
FROM menus m JOIN menu_permissions mp ON mp.menu_code = m.menu_code
ORDER BY m.sort_order, mp.role_code;
-- service ประกอบเป็น matrix ต่อเมนู (8 role × เมนู)
```

#### 6.4.11 PUT /api/v1/menu-permissions/{menuCode}

แก้สิทธิ์การเข้าถึงเมนูหนึ่งรายการต่อทุก role — บันทึก audit เสมอ

| Item | Detail |
| --- | --- |
| Global No. | 29 |
| Method | PUT |
| Path | /api/v1/menu-permissions/{menuCode} |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | K2 · 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | validate role code อยู่ในเซ็ต 00–10 |
| 2 | update menu_permissions ของเมนูนั้น |
| 3 | บันทึก audit_logs (ผู้แก้ + ค่าเดิม/ใหม่) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menu_permissions | W | สิทธิ์ใหม่ต่อ role |
| audit_logs | W | audit การแก้สิทธิ์ |

#### Request / Query / Header

```json
{
  "access": { "04": true, "06": true }
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบเมนู |
| 403 |

SQL Reference

```sql
-- validate role code อยู่ในเซ็ต 00–10
UPDATE menu_permissions SET can_access = :canAccess
WHERE menu_code = :menuCode AND role_code = :roleCode;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, updated_by, updated_at)
VALUES (:tableName, :menuCode, :actionEdit, :oldValue, :newValue, :actor, :now);
```

#### 6.4.12 GET /api/v1/roles

รายการ Role ทั้งหมด (ตารางกลุ่มผู้ใช้งานในหน้าจอ 3.1.1 และ dropdown ที่อื่น)

| Item | Detail |
| --- | --- |
| Global No. | 30 |
| Method | GET |
| Path | /api/v1/roles |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | K2 · 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน roles ทั้งหมดเรียงตาม role_code |

| DB Object | R/W | Usage |
| --- | --- | --- |
| roles | R | role_code · role_name · role_desc · is_system |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{ "roleCode": "01", "roleName": "Admin", "roleDesc": "ผู้ดูแลระบบ BPM ...", "isSystem": true }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT role_code, role_name, role_desc, is_system
FROM roles
ORDER BY role_code;
```

#### 6.4.13 POST /api/v1/roles

เพิ่ม Role ใหม่ — ระบบสร้างสิทธิ์เมนูเริ่มต้นเป็น "ไม่มีสิทธิ์" ทุกเมนู

| Item | Detail |
| --- | --- |
| Global No. | 31 |
| Method | POST |
| Path | /api/v1/roles |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | validate role_code ไม่ซ้ำ |
| 2 | insert roles (is_system = false) |
| 3 | insert menu_permissions ทุกเมนู can_access = false |
| 4 | บันทึก audit_logs |

| DB Object | R/W | Usage |
| --- | --- | --- |
| roles | W | role ใหม่ |
| menu_permissions | W | สิทธิ์เริ่มต้น false ทุกเมนู |
| audit_logs | W | audit การเพิ่ม |

#### Request / Query / Header

```json
{
  "roleCode": "11",
  "roleName": "Zone Viewer",
  "roleDesc": "ดูเอกสารเฉพาะภาคของตน"
}
```

#### Response

```json
201 Created
```

| Error / Condition |
| --- |
| 409 — รหัส Role ซ้ำกับที่มีอยู่ |
| 403 |

SQL Reference

```sql
-- role_code ห้ามซ้ำ ; สร้างแล้วตั้งสิทธิ์เริ่มต้น false ทุกเมนู
INSERT INTO roles (role_code, role_name, role_desc, is_system)
VALUES (:roleCode, :roleName, :roleDesc, FALSE);

INSERT INTO menu_permissions (role_code, menu_code, can_access)
SELECT :roleCode, menu_code, FALSE FROM menus;

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :roleCode, :actionAdd, :newValue, :actor, :now);
```

#### 6.4.14 PUT /api/v1/roles/{roleCode}

แก้ชื่อ/คำอธิบาย Role — ต้องระบุเหตุผล บันทึก audit เสมอ

| Item | Detail |
| --- | --- |
| Global No. | 32 |
| Method | PUT |
| Path | /api/v1/roles/{roleCode} |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ role มีอยู่ |
| 2 | update roles (role_code ของ role ระบบแก้ไม่ได้) |
| 3 | บันทึก audit_logs (ค่าเดิม/ใหม่ + เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| roles | W | ชื่อ/คำอธิบายใหม่ |
| audit_logs | W | audit การแก้ไข |

#### Request / Query / Header

```json
{
  "roleName": "Report Admin",
  "roleDesc": "สำหรับดูเมนูรายงานทุกภาค",
  "reason": "ขยายขอบเขตการดูรายงาน"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบ Role |
| 403 |

SQL Reference

```sql
-- role ระบบแก้ role_code ไม่ได้ ; ต้องระบุ :reason
UPDATE roles SET role_name = :roleName, role_desc = :roleDesc
WHERE role_code = :roleCode;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :roleCode, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.4.15 DELETE /api/v1/roles/{roleCode}

ลบ Role — ลบไม่ได้ถ้าเป็น Role ระบบ (is_system) หรือยังมีผู้ใช้อ้างอยู่

| Item | Detail |
| --- | --- |
| Global No. | 33 |
| Method | DELETE |
| Path | /api/v1/roles/{roleCode} |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ is_system = false และไม่มี user_accounts อ้างถึง |
| 2 | ลบ menu_permissions ของ role ทั้งหมด แล้วลบ roles |
| 3 | บันทึก audit_logs พร้อมเหตุผล |

| DB Object | R/W | Usage |
| --- | --- | --- |
| roles | W | ลบ role |
| menu_permissions | W | ลบสิทธิ์ของ role (cascade) |
| audit_logs | W | audit การลบ |

#### Request / Query / Header

```json
{ "reason": "ยุบรวมกับ Role 04" }
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — Role หลักของระบบ (00–10) ลบไม่ได้ |
| 409 — ยังมีผู้ใช้อยู่ใน Role นี้ ลบไม่ได้ |
| 403 |

SQL Reference

```sql
-- ลบไม่ได้ถ้า is_system หรือมีผู้ใช้อ้างอยู่ (409)
SELECT is_system FROM roles WHERE role_code = :roleCode;
SELECT 1 FROM user_accounts WHERE role_code = :roleCode;

DELETE FROM menu_permissions WHERE role_code = :roleCode;
DELETE FROM roles WHERE role_code = :roleCode;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :roleCode, :actionDelete, :oldValue, :reason, :actor, :now);
```

#### 6.4.16 POST /api/v1/menus

เพิ่มเมนูใหม่เข้าระบบ — สิทธิ์เริ่มต้นเป็น "ไม่มีสิทธิ์" ทุก Role

| Item | Detail |
| --- | --- |
| Global No. | 34 |
| Method | POST |
| Path | /api/v1/menus |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | validate ชื่อเมนูไม่ว่าง / menu_group อยู่ในเซ็ต MAIN, MASTER |
| 2 | insert menus (running menu_code + sort_order ท้ายกลุ่ม) |
| 3 | insert menu_permissions ทุก role can_access = false |
| 4 | บันทึก audit_logs |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menus | W | เมนูใหม่ (menu_group + sort_order) |
| menu_permissions | W | สิทธิ์เริ่มต้น false ทุก role |
| audit_logs | W | audit การเพิ่ม |

#### Request / Query / Header

```json
{
  "menuName": "รายงานผลชดเชยรายเดือน",
  "menuGroup": "MAIN"
}
```

#### Response

```json
201 Created
{ "menuCode": "M07" }
```

| Error / Condition |
| --- |
| 422 — กรุณาระบุชื่อเมนู |
| 403 |

SQL Reference

```sql
-- running menu_code + sort_order ท้ายกลุ่ม ; สิทธิ์เริ่มต้น false ทุก role
INSERT INTO menus (menu_code, menu_name, menu_group, sort_order, is_system)
VALUES (:menuCode, :menuName, :menuGroup, :sortOrder, FALSE);

INSERT INTO menu_permissions (role_code, menu_code, can_access)
SELECT role_code, :menuCode, FALSE FROM roles;

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :menuCode, :actionAdd, :newValue, :actor, :now);
```

#### 6.4.17 PUT /api/v1/menus/{menuCode}

แก้ชื่อ/กลุ่ม/ลำดับเมนู — ต้องระบุเหตุผล บันทึก audit เสมอ

| Item | Detail |
| --- | --- |
| Global No. | 35 |
| Method | PUT |
| Path | /api/v1/menus/{menuCode} |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจเมนูมีอยู่ |
| 2 | update menus |
| 3 | บันทึก audit_logs (ค่าเดิม/ใหม่ + เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menus | W | ชื่อ/กลุ่ม/ลำดับใหม่ |
| audit_logs | W | audit การแก้ไข |

#### Request / Query / Header

```json
{
  "menuName": "รายงานสรุปสถานะ (ใหม่)",
  "sortOrder": 5,
  "reason": "ปรับชื่อให้ตรงรายงานฉบับปรับปรุง"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบเมนู |
| 403 |

SQL Reference

```sql
-- ต้องระบุ :reason
UPDATE menus SET menu_name = :menuName, menu_group = :menuGroup, sort_order = :sortOrder
WHERE menu_code = :menuCode;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :menuCode, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.4.18 DELETE /api/v1/menus/{menuCode}

ลบเมนูพร้อมสิทธิ์ทุก Role ของเมนูนั้น (cascade) — เมนูระบบลบไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 36 |
| Method | DELETE |
| Path | /api/v1/menus/{menuCode} |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ |
| Requirement Tag | ใหม่ · หน้าจอ 3.1.1 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ is_system = false |
| 2 | ลบ menu_permissions ของเมนู แล้วลบ menus |
| 3 | บันทึก audit_logs พร้อมเหตุผล |

| DB Object | R/W | Usage |
| --- | --- | --- |
| menus | W | ลบเมนู |
| menu_permissions | W | ลบสิทธิ์ทุก role ของเมนู (cascade) |
| audit_logs | W | audit การลบ |

#### Request / Query / Header

```json
{ "reason": "ยุบรวมกับเมนูรายงานสรุปสถานะ" }
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — เมนูหลักของระบบลบไม่ได้ |
| 403 |

SQL Reference

```sql
-- เมนูระบบ (is_system) ลบไม่ได้
SELECT is_system FROM menus WHERE menu_code = :menuCode;

DELETE FROM menu_permissions WHERE menu_code = :menuCode;
DELETE FROM menus WHERE menu_code = :menuCode;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :menuCode, :actionDelete, :oldValue, :reason, :actor, :now);
```

#### 6.4.19 GET /api/v1/audit-logs

ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม→ใหม่ · เหตุผล · เมื่อไร) — แผงประวัติท้ายหน้าจอ 3.1.8 / 3.1.9

| Item | Detail |
| --- | --- |
| Global No. | 37 |
| Method | GET |
| Path | /api/v1/audit-logs |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ, 03 User Admin |
| Requirement Tag | K2 · 3.1.8 / 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | query audit_logs ตาม table_name (+ ref_key ถ้าระบุเฉพาะรายการ) |
| 2 | เรียงล่าสุดก่อน แบ่งหน้า |

| DB Object | R/W | Usage |
| --- | --- | --- |
| audit_logs | R | ประวัติหลายรายการต่อข้อมูล (= MaintainMasterHistory เดิม) |

#### Request / Query / Header

```json
Query: ?table=operator_assignments&refKey=12&page=1
```

#### Response

```json
{
  "items": [{
    "actionType": "EDIT",
    "refKey": "12",
    "oldValue": "zoneCode=RS",
    "newValue": "zoneCode=RN",
    "reason": "ปรับพื้นที่รับผิดชอบตามโครงสร้างใหม่",
    "updatedBy": "ภัชริดา ประดิษฐ์ทองใส",
    "updatedAt": "2026-07-02T14:20:00"
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT action_type, ref_key, old_value, new_value, reason, updated_by, updated_at
FROM audit_logs
WHERE table_name = :table
  AND (:refKey IS NULL OR ref_key = :refKey)
ORDER BY updated_at DESC
LIMIT :size OFFSET :offset;
```

### 6.5 System Config (Global)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/configs | รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ system-config.html) |
| 2 | GET | /api/v1/configs/{key} | อ่านค่ากำหนดรายตัว — เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที |
| 3 | POST | /api/v1/configs | เพิ่มค่ากำหนดใหม่ — key ห้ามซ้ำ และ validate ค่าตาม value_type |
| 4 | PUT | /api/v1/configs/{key} | แก้ค่ากำหนด — ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้ |
| 5 | DELETE | /api/v1/configs/{key} | ลบค่ากำหนด — ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล |

#### 6.5.1 GET /api/v1/configs

รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ system-config.html)

| Item | Detail |
| --- | --- |
| Global No. | 38 |
| Method | GET |
| Path | /api/v1/configs |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | query system_configs ตาม category / คำค้น |
| 2 | คืนครบทุก field รวม value_type · unit · is_editable |

| DB Object | R/W | Usage |
| --- | --- | --- |
| system_configs | R | ค่ากำหนดกลางทั้งหมด (ตารางใหม่) |

#### Request / Query / Header

```json
Query: ?category=WORKFLOW&q=escalation
```

#### Response

```json
{
  "items": [{
    "configKey": "workflow.escalation_days",
    "category": "WORKFLOW",
    "value": "[30, 45, 60]",
    "valueType": "JSON",
    "unit": "วัน",
    "description": "ลำดับวัน escalation งานค้าง",
    "isEditable": true
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT config_key, category, config_value, value_type, unit, description, is_editable
FROM system_configs
WHERE (:category IS NULL OR category = :category)
  AND (:q IS NULL OR config_key LIKE :q)
ORDER BY category, config_key;
```

#### 6.5.2 GET /api/v1/configs/{key}

อ่านค่ากำหนดรายตัว — เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที

| Item | Detail |
| --- | --- |
| Global No. | 39 |
| Method | GET |
| Path | /api/v1/configs/{key} |
| Group | System Config (Global) |
| Access / Role | ทุก role (อ่าน) / service token |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | อ่าน system_configs ด้วย config_key |
| 2 | ตอบพร้อม header Cache-Control (TTL 5 นาที) — service ฝั่งเรียก cache ตาม |
| 3 | ค่า BOOLEAN/NUMBER/JSON ตอบเป็น typed value ตาม value_type ไม่ใช่ string ล้วน |

| DB Object | R/W | Usage |
| --- | --- | --- |
| system_configs | R | ค่ารายตัว |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "configKey": "workflow.avp_amount_threshold",
  "value": 100000,
  "valueType": "NUMBER",
  "unit": "บาท"
}
```

| Error / Condition |
| --- |
| 404 — ไม่พบ config key นี้ |
| 401 |

SQL Reference

```sql
SELECT config_key, config_value, value_type, unit
FROM system_configs
WHERE config_key = :key;
-- ตอบพร้อม Cache-Control TTL 5 นาที · แปลงเป็น typed value ตาม value_type
```

#### 6.5.3 POST /api/v1/configs

เพิ่มค่ากำหนดใหม่ — key ห้ามซ้ำ และ validate ค่าตาม value_type

| Item | Detail |
| --- | --- |
| Global No. | 40 |
| Method | POST |
| Path | /api/v1/configs |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | validate config_key รูปแบบ dot notation และไม่ซ้ำ |
| 2 | validate ค่า parse ได้ตาม value_type (NUMBER/BOOLEAN/JSON/CRON) |
| 3 | ปฏิเสธค่าที่เป็น secret (รหัสผ่าน/API key ต้องอยู่ Secret Manager) |
| 4 | insert + บันทึก audit_logs (ADD) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| system_configs | W | แถวใหม่ |
| audit_logs | W | audit การเพิ่ม |

#### Request / Query / Header

```json
{
  "configKey": "report.export_max_rows",
  "category": "DOCUMENT",
  "value": "50000",
  "valueType": "NUMBER",
  "unit": "แถว",
  "description": "จำนวนแถวสูงสุดต่อไฟล์ export"
}
```

#### Response

```json
201 Created
```

| Error / Condition |
| --- |
| 409 — Config Key นี้มีอยู่แล้ว |
| 422 — ค่าไม่ตรงกับชนิดข้อมูล (value_type) |

SQL Reference

```sql
-- config_key ห้ามซ้ำ + parse ค่าตาม value_type ; ห้ามเก็บ secret
INSERT INTO system_configs (config_key, category, config_value, value_type, unit, description, is_editable)
VALUES (:key, :category, :value, :valueType, :unit, :description, TRUE);

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :key, :actionAdd, :newValue, :actor, :now);
```

#### 6.5.4 PUT /api/v1/configs/{key}

แก้ค่ากำหนด — ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 41 |
| Method | PUT |
| Path | /api/v1/configs/{key} |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ is_editable — ค่าคงที่ทางธุรกิจ (รัศมี · วงเงิน 100,000 · เกณฑ์ 60 วัน · เกณฑ์ −10 ตามข้อ 8.2) ตอบ 422 |
| 2 | validate ค่าใหม่ตาม value_type + ต้องระบุ reason เสมอ |
| 3 | update + บันทึก audit_logs (EDIT · old_value → new_value · เหตุผล) |
| 4 | broadcast invalidate cache ให้ทุก service อ่านค่าใหม่ทันที |

| DB Object | R/W | Usage |
| --- | --- | --- |
| system_configs | W | ค่าใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ + เหตุผล |

#### Request / Query / Header

```json
{
  "value": "[30, 45, 60]",
  "reason": "เพิ่มขั้นเตือน 45 วันตามมติที่ประชุม"   // บังคับ
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 422 — key นี้เป็นค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้ |
| 422 — กรุณาระบุเหตุผลการแก้ไขข้อมูล |
| 404 |

SQL Reference

```sql
-- is_editable = FALSE (ค่าคงที่ทางธุรกิจ ข้อ 8.2) → 422 ; ต้องระบุ :reason
UPDATE system_configs SET config_value = :value
WHERE config_key = :key AND is_editable = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :key, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
-- broadcast invalidate cache ให้ทุก service
```

#### 6.5.5 DELETE /api/v1/configs/{key}

ลบค่ากำหนด — ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล

| Item | Detail |
| --- | --- |
| Global No. | 42 |
| Method | DELETE |
| Path | /api/v1/configs/{key} |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ is_editable = true (ค่าคงที่ทางธุรกิจ/ค่าระบบลบไม่ได้) |
| 2 | ลบ + บันทึก audit_logs (DELETE + เหตุผล) |
| 3 | broadcast invalidate cache |

| DB Object | R/W | Usage |
| --- | --- | --- |
| system_configs | W | ลบแถว |
| audit_logs | W | audit + เหตุผล |

#### Request / Query / Header

```json
{ "reason": "เลิกใช้หลังย้ายไปกำหนดใน job_configs" }
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — ค่าระบบ/ค่าคงที่ทางธุรกิจ ลบไม่ได้ |
| 404 |

SQL Reference

```sql
-- ลบได้เฉพาะ key ที่ is_editable = TRUE
DELETE FROM system_configs WHERE config_key = :key AND is_editable = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :key, :actionDelete, :oldValue, :reason, :actor, :now);
```

### 6.6 Email Template (Notification)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/email-templates | รายการ 8 email template (EM-01–08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ plan-email.html) |
| 2 | GET | /api/v1/email-templates/{code} | อ่าน template รายตัว (EM-01–08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น |
| 3 | PUT | /api/v1/email-templates/{code} | บันทึกเนื้อหา template — แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules) |
| 4 | POST | /api/v1/email-templates/{code}/reset | รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ) |
| 5 | POST | /api/v1/email-templates/reset-all | รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default") |

#### 6.6.1 GET /api/v1/email-templates

รายการ 8 email template (EM-01–08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ plan-email.html)

| Item | Detail |
| --- | --- |
| Global No. | 43 |
| Method | GET |
| Path | /api/v1/email-templates |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | query email_templates ทั้ง 8 รหัส |
| 2 | join จุดส่งใน flow (status_email_rules) เพื่อแสดงผู้รับ TO/CC ที่ล็อกไว้ |
| 3 | คืน subject/body ปัจจุบัน + is_customized |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_templates | R | เนื้อหา template ทั้งหมด (ตารางใหม่) |
| status_email_rules | R | ผู้รับ TO/CC ที่ล็อกต่อสถานะ |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{
    "templateCode": "EM-01",
    "name": "แจ้งผู้ดำเนินการลำดับถัดไป",
    "subject": "[SBPGI] เอกสารประกันรายได้ {{doc_no}} — {{next_status}}",
    "isCustomized": false
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
SELECT template_code, name, subject, is_customized
FROM email_templates
ORDER BY template_code;
-- FE ประกอบผู้รับ TO/CC จาก status_email_rules มาแสดง (อ่านอย่างเดียว)
```

#### 6.6.2 GET /api/v1/email-templates/{code}

อ่าน template รายตัว (EM-01–08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น

| Item | Detail |
| --- | --- |
| Global No. | 44 |
| Method | GET |
| Path | /api/v1/email-templates/{code} |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | อ่าน email_templates ด้วย template_code |
| 2 | คืน subject/body + รายการตัวแปร merge ที่รองรับ + ผู้รับ TO/CC (อ่านอย่างเดียว) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_templates | R | เนื้อหารายตัว |
| status_email_rules | R | ผู้รับ TO/CC (ล็อก) |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "templateCode": "EM-01",
  "subject": "[SBPGI] เอกสารประกันรายได้ {{doc_no}} — {{next_status}}",
  "body": "<p>เรียน {{next_actor}} ...</p>",
  "variables": ["doc_no", "store_code", "next_status", "doc_url"],
  "lockedRecipients": { "to": "ผู้ดำเนินการลำดับถัดไป", "cc": "ตาม status_email_rules" }
}
```

| Error / Condition |
| --- |
| 404 — ไม่พบ template code นี้ |
| 401 |

SQL Reference

```sql
SELECT template_code, subject, body, variables
FROM email_templates
WHERE template_code = :code;

SELECT to_section_code, cc_section_code FROM status_email_rules WHERE template_code = :code;
```

#### 6.6.3 PUT /api/v1/email-templates/{code}

บันทึกเนื้อหา template — แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules)

| Item | Detail |
| --- | --- |
| Global No. | 45 |
| Method | PUT |
| Path | /api/v1/email-templates/{code} |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | validate ใช้เฉพาะตัวแปร merge ที่รองรับของ template นั้น |
| 2 | ปฏิเสธการแก้ From/To/Cc — ผู้รับกำหนดที่ status_email_rules เท่านั้น |
| 3 | update email_templates + set is_customized = true |
| 4 | บันทึก audit_logs (EDIT · old → new · เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_templates | W | subject/body ใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ + เหตุผล |

#### Request / Query / Header

```json
{
  "subject": "[SBPGI] เอกสาร {{doc_no}} — {{next_status}}",
  "body": "<p>เรียน {{next_actor}} ...</p>",
  "reason": "เพิ่มลิงก์เปิดเอกสาร {{doc_url}}"   // บังคับ
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 422 — ใช้ตัวแปร merge ที่ไม่รองรับใน template นี้ |
| 422 — แก้ผู้รับ From/To/Cc ผ่านเส้นนี้ไม่ได้ |
| 422 — กรุณาระบุเหตุผลการแก้ไข |
| 404 |

SQL Reference

```sql
-- แก้ได้เฉพาะ subject/body + ตัวแปรที่รองรับ ; From/To/Cc ล็อกที่ status_email_rules ; ต้องระบุ :reason
UPDATE email_templates SET subject = :subject, body = :body, is_customized = TRUE
WHERE template_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.6.4 POST /api/v1/email-templates/{code}/reset

รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ)

| Item | Detail |
| --- | --- |
| Global No. | 46 |
| Method | POST |
| Path | /api/v1/email-templates/{code}/reset |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | คืน subject/body เป็นชุด Default ของ template นั้น |
| 2 | set is_customized = false |
| 3 | บันทึก audit_logs (RESET + เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_templates | W | คืนค่า Default |
| audit_logs | W | audit การรีเซ็ต |

#### Request / Query / Header

```json
{ "reason": "ยกเลิกถ้อยคำที่ทดลองปรับ" }
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบ template code นี้ |
| 401 |

SQL Reference

```sql
-- คืน subject/body เป็นชุด Default ของ template นั้น
UPDATE email_templates SET subject = :defaultSubject, body = :defaultBody, is_customized = FALSE
WHERE template_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionReset, :reason, :actor, :now);
```

#### 6.6.5 POST /api/v1/email-templates/reset-all

รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default")

| Item | Detail |
| --- | --- |
| Global No. | 47 |
| Method | POST |
| Path | /api/v1/email-templates/reset-all |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | คืน subject/body ของทุก template เป็นชุด Default |
| 2 | set is_customized = false ทุกฉบับ |
| 3 | บันทึก audit_logs หนึ่งรายการต่อ template ที่เปลี่ยนจริง |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_templates | W | คืนค่า Default ทั้ง 8 |
| audit_logs | W | audit ต่อ template ที่เปลี่ยน |

#### Request / Query / Header

```json
{ "reason": "ล้างค่าทดสอบทั้งหมดก่อนส่งมอบ" }
```

#### Response

```json
200 OK
{ "resetCount": 3 }
```

| Error / Condition |
| --- |
| 401 |
| 403 |

SQL Reference

```sql
-- รีเซ็ตทั้ง 8 ฉบับ ; บันทึก audit เฉพาะฉบับที่เปลี่ยนจริง
UPDATE email_templates SET subject = default_subject, body = default_body, is_customized = FALSE
WHERE is_customized = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, reason, updated_by, updated_at)
SELECT :tableName, template_code, :actionReset, :reason, :actor, :now
FROM email_templates WHERE is_customized = FALSE;
```

### 6.7 รายงาน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/reports/status-summary | รายงานตรวจสอบประกันรายได้ (SBP Mall) — Preview Report · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) |
| 2 | GET | /api/v1/reports/status-summary/export | Export CSV to Batch — ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา |

#### 6.7.1 GET /api/v1/reports/status-summary

รายงานตรวจสอบประกันรายได้ (SBP Mall) — Preview Report · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 48 |
| Method | GET |
| Path | /api/v1/reports/status-summary |
| Group | รายงาน |
| Access / Role | บัญชี / 06 Report Admin |
| Requirement Tag | K2 · 3.1.7 + SDD v7.5 |

| Step | Flow |
| --- | --- |
| 1 | validate ปี (ไม่ระบุ → 400) |
| 2 | query compensation_documents + compensation_histories ตามเงื่อนไข (status 6 ค่า · region 13 · storeType A-D · รหัสถูกกระทบ/เปิดกระทบ) |
| 3 | กรอง result (APPROVE/REJECT) จากผลพิจารณาล่าสุดใน consideration_logs — filter "ประกันรายได้/ไม่ประกันรายได้" หน้า k2-report |
| 4 | คืนแบบแบ่งหน้าตามหน้าจอ k2-report.html |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | R | สถานะเอกสาร |
| compensation_histories | R | ยอด/งวดชดเชย |
| impacted_stores | R | ข้อมูลร้าน |
| consideration_logs | R | ผลพิจารณาล่าสุด (กรองประกัน/ไม่ประกัน) |

#### Request / Query / Header

```json
Query: ?year=2569&statusCode=06&result=APPROVE&region=RSU&storeType=A&impactedStoreCode=00233&newStoreCode=22864&page=1
(result = APPROVE | REJECT — ประกันรายได้ / ไม่ประกันรายได้)
```

#### Response

```json
{
  "page": 1, "total": 212,
  "items": [{ "docNo": "2569/00098", "storeCode": "00788", "status": "เสร็จสิ้นดำเนินการ", "compensateAmount": 85000.00, ... }]
}
```

| Error / Condition |
| --- |
| 400 — กรุณาระบุปีที่ต้องการค้นหา |

SQL Reference

```sql
-- ต้องระบุ :year เสมอ ; เอาเฉพาะเอกสารที่มีเลขที่แล้ว
SELECT d.doc_no, d.impacted_store_code, s.store_name, d.status_code,
       h.compensate_amount, h.submit_account_month, cl.result_category
FROM compensation_documents d
JOIN stores s ON s.store_code = d.impacted_store_code
LEFT JOIN compensation_histories h ON h.ref_doc_no = d.doc_no
LEFT JOIN LATERAL (
  SELECT result_category FROM consideration_logs
  WHERE doc_no = d.doc_no ORDER BY action_datetime DESC LIMIT 1
) cl ON TRUE
WHERE d.be_year = :year
  AND (:month  IS NULL OR h.submit_account_month = :month)
  AND (:zone   IS NULL OR s.zone_code = :zone)
  AND (:statusCode IS NULL OR d.status_code = :statusCode)
  AND (:result IS NULL OR cl.result_category = :result)   -- APPROVE / REJECT (filter ประกันรายได้/ไม่ประกันรายได้)
ORDER BY d.doc_no
LIMIT :size OFFSET :offset;
```

#### 6.7.2 GET /api/v1/reports/status-summary/export

Export CSV to Batch — ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา

| Item | Detail |
| --- | --- |
| Global No. | 49 |
| Method | GET |
| Path | /api/v1/reports/status-summary/export |
| Group | รายงาน |
| Access / Role | 04 / 06 Report Admin |
| Requirement Tag | K2 · 3.1.7 |

| Step | Flow |
| --- | --- |
| 1 | เงื่อนไขเดียวกับ status-summary |
| 2 | สร้างไฟล์ CSV แล้วส่งเข้า Batch (ทีมบัญชีนำไปกระทบ SAP) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents / compensation_histories | R | ข้อมูลชุดเดียวกับรายงาน |

#### Request / Query / Header

```json
Query: ?year=2569&result=APPROVE&region=RSU&storeType=A
(เงื่อนไขชุดเดียวกับเส้นค้นหา รวม result ประกันรายได้/ไม่ประกันรายได้)
```

#### Response

```json
200 OK
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="insurance-verification-2569.csv"
X-Batch-Job: queued
```

| Error / Condition |
| --- |
| 400 — ไม่ระบุปี |

SQL Reference

```sql
-- เงื่อนไขเดียวกับ status-summary (รวม :result ประกัน/ไม่ประกัน) แล้ว stream เป็นไฟล์ .csv เข้า Batch
SELECT d.doc_no, d.impacted_store_code, d.status_code, h.compensate_amount, h.submit_account_month
FROM compensation_documents d
LEFT JOIN compensation_histories h ON h.ref_doc_no = d.doc_no
LEFT JOIN LATERAL (
  SELECT result_category FROM consideration_logs
  WHERE doc_no = d.doc_no ORDER BY action_datetime DESC LIMIT 1
) cl ON TRUE
WHERE d.be_year = :year
  AND (:month  IS NULL OR h.submit_account_month = :month)
  AND (:result IS NULL OR cl.result_category = :result)
ORDER BY d.doc_no;
```

### 6.8 Batch Job Admin

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/jobs | รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด — reference contract สำหรับแบบฟอร์มพารามิเตอร์และประวัติการรันเท่านั้น |
| 2 | GET | /api/v1/jobs/{jobNo} | รายละเอียด job หนึ่งตัวสำหรับ tab แบบฟอร์มพารามิเตอร์: schedule, input/configurable parameters, output และ current status |
| 3 | PUT | /api/v1/jobs/{jobNo}/params | แก้พารามิเตอร์ที่ editable ของ job — ค่าคงที่ทางธุรกิจแก้ผ่าน UI/API ไม่ได้ |
| 4 | POST | /api/v1/jobs/{jobNo}/run | สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล — รายละเอียด flow การทำงานอยู่ในเอกสาร BE/Runbook ไม่ใช่ tab ที่ต้องทำใน FE Batch Monitor |
| 5 | PUT | /api/v1/jobs/{jobNo}/enabled | เปิด/ปิดการทำงานของ job ตามรอบเวลา |
| 6 | GET | /api/v1/jobs/{jobNo}/runs | ประวัติการรันของ job สำหรับ tab ประวัติการรันในหน้า Batch Monitor |

Batch Job Admin เป็น endpoint reference สำหรับ FE Batch Monitor เฉพาะ 2 tab: แบบฟอร์มพารามิเตอร์ และประวัติการรัน เท่านั้น; ไม่ออกแบบ flowchart การทำงาน, step-by-step batch flow หรือ Database ที่ใช้ใน LLDD API ฉบับรวม

#### 6.8.1 GET /api/v1/jobs

รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด — reference contract สำหรับแบบฟอร์มพารามิเตอร์และประวัติการรันเท่านั้น

| Item | Detail |
| --- | --- |
| Global No. | 50 |
| Method | GET |
| Path | /api/v1/jobs |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [{
    "jobNo": "6",
    "name": "ExportImpactStoreToFS",
    "cron": "0 17 * * *",
    "enabled": true,
    "lastRun": { "status": "SUCCESS", "rows": 1254, "startedAt": "2026-07-01T17:00:00" }
  }]
}
```

| Error / Condition |
| --- |
| 401 |
| 403 |

#### 6.8.2 GET /api/v1/jobs/{jobNo}

รายละเอียด job หนึ่งตัวสำหรับ tab แบบฟอร์มพารามิเตอร์: schedule, input/configurable parameters, output และ current status

| Item | Detail |
| --- | --- |
| Global No. | 51 |
| Method | GET |
| Path | /api/v1/jobs/{jobNo} |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "jobNo": "1",
  "name": "ImportQSSI",
  "params": [
    { "key": "sftpPort", "value": "218", "editable": true },
    { "key": "encoding", "value": "WINDOWS-874", "editable": false }
  ]
}
```

| Error / Condition |
| --- |
| 404 |

#### 6.8.3 PUT /api/v1/jobs/{jobNo}/params

แก้พารามิเตอร์ที่ editable ของ job — ค่าคงที่ทางธุรกิจแก้ผ่าน UI/API ไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 52 |
| Method | PUT |
| Path | /api/v1/jobs/{jobNo}/params |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS + ข้อ 8.2 |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
{
  "params": { "cron": "0 18 * * *", "batchSize": 20000 }
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 422 — key นี้เป็นค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้ |
| 404 |

#### 6.8.4 POST /api/v1/jobs/{jobNo}/run

สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล — รายละเอียด flow การทำงานอยู่ในเอกสาร BE/Runbook ไม่ใช่ tab ที่ต้องทำใน FE Batch Monitor

| Item | Detail |
| --- | --- |
| Global No. | 53 |
| Method | POST |
| Path | /api/v1/jobs/{jobNo}/run |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS · Runbook 7.1 |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
{
  "period": "2026-07"   // งวดข้อมูล (YYYY-MM)
}
```

#### Response

```json
202 Accepted
{ "runId": 4451 }
```

| Error / Condition |
| --- |
| 409 — Job กำลังรันอยู่ ห้ามรันซ้อน |
| 422 — job ถูกปิดใช้งาน |

#### 6.8.5 PUT /api/v1/jobs/{jobNo}/enabled

เปิด/ปิดการทำงานของ job ตามรอบเวลา

| Item | Detail |
| --- | --- |
| Global No. | 54 |
| Method | PUT |
| Path | /api/v1/jobs/{jobNo}/enabled |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
{ "enabled": false, "reason": "ปิดชั่วคราวช่วงปิดงบ" }
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 |

#### 6.8.6 GET /api/v1/jobs/{jobNo}/runs

ประวัติการรันของ job สำหรับ tab ประวัติการรันในหน้า Batch Monitor

| Item | Detail |
| --- | --- |
| Global No. | 55 |
| Method | GET |
| Path | /api/v1/jobs/{jobNo}/runs |
| Group | Batch Job Admin |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS |

Scope note: รายละเอียด flow และ database ของ batch job ให้ดูเอกสาร BE/Runbook/Database reference แยก ไม่ใช่ tab หรือ deliverable ที่ต้องทำใน FE Batch Monitor

#### Request / Query / Header

```json
Query: ?page=1&size=20
```

#### Response

```json
{
  "items": [{
    "runId": 4451, "status": "SUCCESS", "rows": 48220,
    "file": "mrs1-mrs5 (4 ไฟล์)", "startedAt": "2026-07-01T06:00:00", "durationSec": 252
  }]
}
```

| Error / Condition |
| --- |
| 404 |

### 6.9 Workflow ภายใน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | POST | /api/v1/workflows/instances | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม |
| 2 | GET | /api/v1/workflows/instances/{id} | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) |
| 3 | GET | /api/v1/workflows/summary | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น |

#### 6.9.1 POST /api/v1/workflows/instances

เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม

| Item | Detail |
| --- | --- |
| Global No. | 56 |
| Method | POST |
| Path | /api/v1/workflows/instances |
| Group | Workflow ภายใน |
| Access / Role | service token (ภายใน) |
| Requirement Tag | แทน K2 StartInstance (Job 8b) |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ service token (ไม่ใช่ JWT ผู้ใช้) |
| 2 | lock fgi_impact_processes แล้วตรวจ Gen Flow Gate ทุกข้อ: workflow_generation_status=W · branch type FAM/FB1/FC1/FB2/FVB/FVC · opt_dv_user_id ไม่ว่าง · juristic ร้านใหม่ต่างจากร้านถูกกระทบ · growth_rate_diff ≤ −10 · sales_status ∈ {Y,N} |
| 3 | ไม่ผ่าน: branch type นอกเซ็ต → workflow_generation_status=N · กรณีอื่นคง W (ตอบ 422 พร้อมเหตุผล) |
| 4 | ผ่าน: ใช้ compensation_documents ที่ Job 8 สร้างแล้ว + workflow_instances + workflow_tasks แรก (06) แล้วตั้ง workflow_generation_status=Y |
| 5 | ส่งอีเมลสรุปราย DV หลัง commit |

| DB Object | R/W | Usage |
| --- | --- | --- |
| fgi_impact_processes | R/W | source of truth ของ workflow_generation_status W→Y/N |
| impacted_stores / stores / fgi_impact_stores / fgi_impact_sales_summaries | R | คอลัมน์ gate จากตารางจริง |
| compensation_documents | R | เอกสารอัตโนมัติจาก Job 8 |
| workflow_instances / workflow_tasks | W | เปิด instance + งานแรก |

#### Request / Query / Header

```json
{
  "impactProcessId": 88123,
  "sourceJobNo": "8b",
  "requestId": "job8b-88123-256907"
}
```

#### Response

```json
201 Created
{
  "docNo": "2569/00124",
  "instanceId": "WF-2569-00124",
  "workflowGenerationStatus": "Y",
  "firstSection": "06",
  "statusCode": "06"
}
```

| Error / Condition |
| --- |
| 422 — ไม่ผ่าน Gen Flow Gate (ตอบเหตุผล + สถานะ W/N ที่ตั้งให้) |
| 401 — service token ไม่ถูกต้อง |

SQL Reference

```sql
-- Gen Flow Gate: workflow_generation_status มี source of truth ที่ fgi_impact_processes
SELECT p.id AS impact_process_id, p.workflow_generation_status, ist.opt_dv_user_id,
       impacted.juristic_name AS impacted_store_juristic_name, ns.juristic_name AS new_store_juristic_name,
       ss.growth_rate_diff, ss.sales_status, ns.branch_type
FROM fgi_impact_processes p
JOIN impacted_stores ist ON ist.store_code = p.impacted_store_code
JOIN stores impacted ON impacted.store_code = p.impacted_store_code
JOIN fgi_impact_stores pair ON pair.impact_process_id = p.id
JOIN stores ns ON ns.store_code = pair.new_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = p.id
WHERE p.id = :impactProcessId FOR UPDATE OF p;

-- branch_type นอก allowlist → ตั้ง N ถาวร; gate อื่นไม่พร้อมคง W
UPDATE fgi_impact_processes SET workflow_generation_status = :flagN
WHERE id = :impactProcessId AND workflow_generation_status = :flagW AND :gateDecision = :flagN;

-- ผ่าน gate → ใช้เอกสารที่ Job 8 สร้างแล้ว เปิด instance + งานแรก แล้วตั้ง Y ใน transaction เดียว
INSERT INTO workflow_instances (instance_id, doc_no, instance_status, started_at, started_by)
SELECT :instanceId, d.doc_no, :active, :now, :serviceActor
FROM compensation_documents d WHERE d.impact_process_id = :impactProcessId AND :gateDecision = :flagY
ON CONFLICT (doc_no) DO NOTHING;
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status)
SELECT :instanceId, d.doc_no, :section06, :statusOpen
FROM compensation_documents d WHERE d.impact_process_id = :impactProcessId AND :gateDecision = :flagY
ON CONFLICT DO NOTHING;
UPDATE fgi_impact_processes SET workflow_generation_status = :flagY
WHERE id = :impactProcessId AND workflow_generation_status = :flagW AND :gateDecision = :flagY;
```

#### 6.9.2 GET /api/v1/workflows/instances/{id}

สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม)

| Item | Detail |
| --- | --- |
| Global No. | 57 |
| Method | GET |
| Path | /api/v1/workflows/instances/{id} |
| Group | Workflow ภายใน |
| Access / Role | 01 Admin / เจ้าของงาน |
| Requirement Tag | ใหม่ |

| Step | Flow |
| --- | --- |
| 1 | อ่าน workflow_instances + workflow_tasks ปัจจุบัน + เอกสารที่ผูก |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_instances / workflow_tasks | R | สถานะ + งานปัจจุบัน |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "instanceId": 501,
  "docNo": "2569/00124",
  "status": "ACTIVE",
  "currentTask": { "section": "02", "openedAt": "2026-07-01T09:00:00" }
}
```

| Error / Condition |
| --- |
| 404 |

SQL Reference

```sql
SELECT i.instance_id, i.doc_no, i.instance_status, t.section_code, t.opened_at
FROM workflow_instances i
LEFT JOIN workflow_tasks t ON t.instance_id = i.instance_id AND t.task_status = :statusOpen
WHERE i.instance_id = :id;
```

#### 6.9.3 GET /api/v1/workflows/summary

ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น

| Item | Detail |
| --- | --- |
| Global No. | 58 |
| Method | GET |
| Path | /api/v1/workflows/summary |
| Group | Workflow ภายใน |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS · Monitoring 7.4 |

| Step | Flow |
| --- | --- |
| 1 | aggregate จาก fgi_impact_processes + workflow_instances/workflow_tasks |

| DB Object | R/W | Usage |
| --- | --- | --- |
| fgi_impact_processes | R | นับ W/Y/N |
| workflow_tasks | R | งานค้างต่อ section |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "genFlow": { "W": 12, "Y": 58, "N": 4 },
  "failedStarts": 0,
  "openTasksBySection": { "06": 24, "02": 7 }
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT workflow_generation_status, COUNT(*) AS cnt
FROM fgi_impact_processes
GROUP BY workflow_generation_status;

SELECT section_code, COUNT(*) AS open_tasks
FROM workflow_tasks WHERE task_status = :statusOpen
GROUP BY section_code;
```

### 6.10 Interface & Dashboard

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/interfaces/tracking | สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) |
| 2 | POST | /api/v1/interfaces/sta/ack | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว |
| 3 | GET | /api/v1/interfaces/pending-ack | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน |
| 4 | GET | /api/v1/dashboard/summary | ตัวเลขหน้า Dashboard: งานค้าง, ร้านประกันรายได้เดือนนี้, ยอดชดเชย, ข้อมูลผิดปกติ + ข้อมูลกราฟ |

#### 6.10.1 GET /api/v1/interfaces/tracking

สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA)

| Item | Detail |
| --- | --- |
| Global No. | 59 |
| Method | GET |
| Path | /api/v1/interfaces/tracking |
| Group | Interface & Dashboard |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS |

| Step | Flow |
| --- | --- |
| 1 | query ตาม dataName / สถานะค้าง / ช่วงเวลา แบ่งหน้า |

| DB Object | R/W | Usage |
| --- | --- | --- |
| interface_transactions | R | tracking typed FK (ตารางใหม่) |

#### Request / Query / Header

```json
Query: ?dataName=COMPENSATE_INIT_I&pending=true&page=1
```

#### Response

```json
{
  "items": [{
    "trackingId": 9912,
    "dataName": "COMPENSATE_INIT_I",
    "docNo": "2569/00098",
    "sentAt": "2026-06-30T17:02:00",
    "returnCode": null
  }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT id AS tracking_id, data_name, doc_no, sent_at, return_code, acked_at AS receive_date
FROM interface_transactions
WHERE (:dataName IS NULL OR data_name = :dataName)
  AND (:pending  IS NULL OR return_code IS NULL)
ORDER BY sent_at DESC
LIMIT :size OFFSET :offset;
```

#### 6.10.2 POST /api/v1/interfaces/sta/ack

Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว

| Item | Detail |
| --- | --- |
| Global No. | 60 |
| Method | POST |
| Path | /api/v1/interfaces/sta/ack |
| Group | Interface & Dashboard |
| Access / Role | API key ของระบบ STA |
| Requirement Tag | ใหม่ (เสริม Job 10) |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ API key เฉพาะของ STA |
| 2 | update interface_transactions.returnCode + receiveDate |
| 3 | รายการหายจากจอ pending-ack ทันที (watchdog Job 10 ยังคงเป็น safety net) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| interface_transactions | W | บันทึก ACK |

#### Request / Query / Header

```json
{
  "trackingId": 9912,
  "returnCode": "W",
  "receiveDate": "2026-07-02T08:15:00"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 401 — API key ไม่ถูกต้อง |
| 404 — ไม่พบ tracking |

SQL Reference

```sql
-- callback จากระบบ STA (API key) → บันทึก ACK
UPDATE interface_transactions
SET return_code = :returnCode, acked_at = :receiveDate, status = :statusAcked, completed_at = :receiveDate
WHERE id = :trackingId;
```

#### 6.10.3 GET /api/v1/interfaces/pending-ack

รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน

| Item | Detail |
| --- | --- |
| Global No. | 61 |
| Method | GET |
| Path | /api/v1/interfaces/pending-ack |
| Group | Interface & Dashboard |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS · Job 10 |

| Step | Flow |
| --- | --- |
| 1 | เกณฑ์เดิมของ Job 10: returnCode IS NULL · interface แบบไฟล์ · อายุ ≥ 1 วัน |
| 2 | เฉพาะ dataset ฝั่ง STA (COMPENSATE_INIT_I / COMPENSATE_APPROVE_I) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| interface_transactions | R | รายการค้าง |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "count": 2,
  "items": [{ "dataName": "COMPENSATE_INIT_I", "docNo": "2569/00098", "ageDays": 2 }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- เกณฑ์ watchdog Job 10: return_code NULL · interface แบบไฟล์ · อายุ ≥ 1 วัน
SELECT data_name, doc_no, sent_at, (CURRENT_DATE - sent_at::date) AS age_days
FROM interface_transactions
WHERE return_code IS NULL
  AND data_name IN (:staDatasets)
  AND sent_at < CURRENT_DATE - 1
ORDER BY sent_at;
```

#### 6.10.4 GET /api/v1/dashboard/summary

ตัวเลขหน้า Dashboard: งานค้าง, ร้านประกันรายได้เดือนนี้, ยอดชดเชย, ข้อมูลผิดปกติ + ข้อมูลกราฟ

| Item | Detail |
| --- | --- |
| Global No. | 62 |
| Method | GET |
| Path | /api/v1/dashboard/summary |
| Group | Interface & Dashboard |
| Access / Role | ทุก role |
| Requirement Tag | K2 (หน้าหลัก) |

| Step | Flow |
| --- | --- |
| 1 | aggregate จากเอกสาร + งานค้าง + ผลชดเชยเดือนปัจจุบัน |
| 2 | cache 5 นาที |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents / workflow_tasks | R | งานค้าง + สถานะ |
| compensation_histories | R | ยอดชดเชยรายเดือน |
| fgi_impact_sales_summaries | R | จำนวนข้อมูลผิดปกติ |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "waitingTasks": 24,
  "storesThisMonth": 342,
  "compensationThisMonth": 8420000.00,
  "abnormalStores": 5,
  "chart": { "monthly": [ ... ] }
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- รวมตัวเลขหน้า Dashboard (cache 5 นาที)
SELECT COUNT(*) AS waiting_tasks       FROM workflow_tasks WHERE task_status = :statusOpen;
SELECT COUNT(*) AS stores_this_month   FROM compensation_documents WHERE impact_month = :thisMonth;
SELECT SUM(compensate_amount) AS compensation_this_month FROM compensation_histories WHERE submit_account_month = :thisMonth;
SELECT COUNT(*) AS abnormal_stores     FROM fgi_impact_sales_summaries WHERE total_working_days < 60;
```

## 7. API Test Checklist

| Test group | Required cases |
| --- | --- |
| Common contract | 401, 403, 404, 409, 422, pagination envelope, error `{code,message}` |
| Document workflow | create duplicate, submit no result, invalid result for role profile, current task conflict, threshold >100000 route |
| Attachment | file >5MB, unsupported type, AV blocked, download not owner, download clean file |
| Report | year required, result required, CSV export with same filter as preview |
| Job admin | manual run when disabled, manual run while RUNNING, editable params only, run histories |
| Security | service token only endpoints, no objectKey/secret leak, audit reason required for mutations |

## 8. Related LLDD

| Document | Use |
| --- | --- |
| LLDD-BE-API-Common-Contracts | กำหนดสัญญากลางของ REST API ทุกเส้นเพื่อไม่ให้ endpoint รายตัวตีความต่างกัน: transport/auth/error/format/pagination/action/RBAC/audit/idempotency |
| LLDD-BE-API-Dashboard-Summary | ออกแบบ Backend APIs สำหรับ Dashboard KPI, pending summary, monthly chart และ status chart |
| LLDD-BE-API-Document-List-Search | ออกแบบ APIs สำหรับงานรอดำเนินการและค้นหาเอกสารที่เกี่ยวข้อง |
| LLDD-BE-API-Document-Create-Update | ออกแบบ APIs สำหรับสร้างเอกสารใหม่และบันทึกส่วนย่อยของเอกสาร |
| LLDD-BE-API-Document-Detail-Aggregate | ออกแบบ aggregate API สำหรับโหลดรายละเอียดเอกสารครบทุก section ให้หน้า FE detail |
| LLDD-BE-API-Document-Workflow-Actions | ออกแบบ APIs สำหรับรับผลพิจารณา ตรวจสิทธิ์ action และบันทึก audit/consideration log |
| LLDD-BE-API-Workflow-Instances | ออกแบบ Workflow Engine ภายในและ POST /api/v1/workflows/instances สำหรับเปิด workflow จาก Job 8b แทน K2 REST StartInstance โดยเป็นเจ้าของ Gen Flow Gate W/Y/N |
| LLDD-BE-API-Attachment-Sales-Timeline | ออกแบบ APIs สำหรับไฟล์แนบ ข้อมูลยอดขายเพิ่มเติม และ timeline/history |
| LLDD-BE-API-Lookup-RBAC-Email | ออกแบบ APIs ที่ตกหล่นจาก shared lookup, RBAC/menu permission, audit log และ email template ของ SBP Mall |
| LLDD-BE-API-Report-Master-Config | ออกแบบ APIs สำหรับรายงาน Master Data และ System Config |
