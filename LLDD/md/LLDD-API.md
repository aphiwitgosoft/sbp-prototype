# LLDD API - REST API and Integration Contract

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารนี้เป็น LLDD API ระดับรวมของระบบ SBPGI/SBP Mall ใช้เป็น master reference สำหรับ REST contract, auth, error, endpoint catalog, implementation pattern และ test scope ของ BE API LLDD รายกลุ่ม

## 2. Scope

| Item | Detail |
| --- | --- |
| API base | /api/v1 |
| Endpoint count | 48 endpoints, 9 groups |
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
| งาน & เอกสารประกันรายได้ | 11 | /api/v1/tasks, /api/v1/documents, /api/v1/documents/{docNo}, /api/v1/documents ... | K2 · SRS 3.1.2 / 3.1.3 / 3.1.6 |
| ข้อมูลอ้างอิง (Lookup / Reference) | 7 | /api/v1/competitors, /api/v1/competitors, /api/v1/competitors/{code}, /api/v1/competitors/{code} ... | K2 + FGI/FCS · master สำหรับ dropdown |
| Master Data | 5 | /api/v1/factors, /api/v1/factors, /api/v1/factors/{code}, /api/v1/factors/{code} ... | K2 · SRS 3.1.9 |
| System Config (Global) | 5 | /api/v1/configs, /api/v1/configs/{key}, /api/v1/configs, /api/v1/configs/{key} ... | ระบบ SBP เดิม · mas_param |
| Email Template (Notification) | 5 | /api/v1/email-templates, /api/v1/email-templates/{code}, /api/v1/email-templates/{code}, /api/v1/email-templates/{code}/reset ... | ระบบ SBP เดิม · email_template |
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

### 6.1 งาน & เอกสารประกันรายได้

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/tasks | งานรอท่านดำเนินการ — เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า k2-list-waiting.html) |
| 2 | GET | /api/v1/documents | ค้นหาเอกสารที่เกี่ยวข้อง — บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS) |
| 3 | GET | /api/v1/documents/{docNo} | เอกสารฉบับเต็ม 12 ส่วนย่อย (k2-document.html) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน |
| 4 | POST | /api/v1/documents | สร้างเอกสารจากข้อมูลที่ FS/SBP Statement ส่งกลับ — ตัดสินใจ 2026-08-06: ไม่มีฟอร์มสร้างเอกสารใน FE แล้ว (k2-create.html เหลือเป็นหน้าอธิบายกระบวนการ) เส้นนี้เรียกโดย pipeline/service token |
| 5 | PUT | /api/v1/documents/{docNo} | บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่ |
| 6 | POST | /api/v1/documents/{docNo}/actions | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · วงเงิน GM 50,000 / AVP 300,000 (SDD GI 24/02/2026) |
| 7 | GET | /api/v1/documents/{docNo}/timeline | ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร) |
| 8 | POST | /api/v1/documents/{docNo}/attachments | แนบไฟล์เข้าเอกสาร — จำกัด 5MB ต่อไฟล์ตาม SRS |
| 9 | GET | /api/v1/documents/{docNo}/attachments/{attachId}/download | ดาวน์โหลดไฟล์แนบผ่าน BE stream โดยตรวจสิทธิ์เอกสารและ scanStatus=CLEAN ก่อนส่ง binary |
| 10 | GET | /api/v1/documents/{docNo}/attachments/download-all | ดาวน์โหลดไฟล์แนบทั้งหมดของเอกสารเป็นไฟล์ .zip — ปุ่ม "ดาวน์โหลดทั้งหมด" ระดับการ์ด (เทียบเท่าปุ่ม Download ของ K2 เดิม) |
| 11 | GET | /api/v1/documents/{docNo}/sales | ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง × 15 วัน) — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร k2-document.html |

#### 6.1.1 GET /api/v1/tasks

งานรอท่านดำเนินการ — เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า k2-list-waiting.html)

| Item | Detail |
| --- | --- |
| Global No. | 1 |
| Method | GET |
| Path | /api/v1/tasks |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | role ที่มีสิทธิ์เมนูเอกสาร |
| Requirement Tag | K2 · 3.1.2 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sectionCode ของผู้ใช้จาก JWT |
| 2 | อ่านงานค้างจาก engine เดิม: getPendingFlow({userData:{userId,groupId}, versionId}) ของ @srm/glb-workflow (ไม่มีตาราง workflow_tasks ของ SBPGI แล้ว) |
| 3 | join compensation_documents + stores + fgi_impact_sales_summaries คืน 9 คอลัมน์ตามหน้าจอและ salesDataDays สำหรับ red flag |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_transaction / workflow_approver | R | งานค้างจาก @srm/glb-workflow (ระบบ SBP เดิม) |
| compensation_documents | R | ข้อมูลเอกสาร |
| stores | R | ชื่อและภาคของร้าน |
| fgi_impact_sales_summaries | R | อัตรายอดขายลดลงและจำนวนวันข้อมูลยอดขาย |

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
    "roundNo": 1,
    "docNo": "2026/00123",
    "impactedStoreCode": "00788",
    "impactedStoreName": "รัตนอุทิศ ซ.13",
    "regionCode": "BE",
    "salesDeclinePercent": 12.5,
    "totalCompensationAmount": 48200.00,
    "statusCode": "06",
    "currentSection": "06",
    "daysPending": 3,
    "salesDataDays": 58
  }]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
SELECT d.round_no AS "roundNo",
       d.doc_no AS "docNo",
       d.impacted_store_code AS "impactedStoreCode",
       s.store_name AS "impactedStoreName",
       s.region_code AS "regionCode",
       GREATEST(COALESCE(-ss.growth_rate_diff, 0), 0) AS "salesDeclinePercent",
       d.total_compensation_amount AS "totalCompensationAmount",
       d.status_code AS "statusCode",
       d.current_section_code AS "currentSection",
       GREATEST(CURRENT_DATE - t.opened_at::date, 0) AS "daysPending",
       ss.total_working_days AS "salesDataDays"
FROM workflow_tasks t
JOIN compensation_documents d ON d.doc_no = t.doc_no
JOIN stores s ON s.store_code = d.impacted_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = d.impact_process_id
WHERE t.section_code = :sectionFromJwt AND t.task_status = :statusOpen
ORDER BY t.opened_at
LIMIT :size OFFSET :offset;
```

#### 6.1.2 GET /api/v1/documents

ค้นหาเอกสารที่เกี่ยวข้อง — บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 2 |
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
Query: ?year=2569&impactedStoreCode=00788&status=06&page=1
(status = section ที่รออยู่ 06/08/01/02/03 หรือ END)
```

#### Response

```json
{
  "page": 1, "total": 6,
  "items": [{ "docNo": "2026/00123", "statusCode": "06", ... }]
}
```

items[] ใช้ field ชุดเดียวกับ §6.2.1 GET /api/v1/tasks สำหรับ list response ของ SCR-03/04

| Error / Condition |
| --- |
| 400 — กรุณาระบุปีที่ต้องการค้นหา (กติกา SRS) |
| 401 |

SQL Reference

```sql
-- ต้องระบุ :year เสมอ ไม่งั้นตอบ 400 (กติกา SRS)
SELECT d.round_no AS "roundNo",
       d.doc_no AS "docNo",
       d.impacted_store_code AS "impactedStoreCode",
       s.store_name AS "impactedStoreName",
       s.region_code AS "regionCode",
       GREATEST(COALESCE(-ss.growth_rate_diff, 0), 0) AS "salesDeclinePercent",
       d.total_compensation_amount AS "totalCompensationAmount",
       d.status_code AS "statusCode",
       d.current_section_code AS "currentSection",
       CASE WHEN t.task_status = :statusOpen THEN GREATEST(CURRENT_DATE - t.opened_at::date, 0) ELSE 0 END AS "daysPending",
       ss.total_working_days AS "salesDataDays"
FROM compensation_documents d
JOIN stores s ON s.store_code = d.impacted_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = d.impact_process_id
LEFT JOIN workflow_tasks t ON t.doc_no = d.doc_no AND t.task_status = :statusOpen
WHERE d.year = :year
  AND (:impactedStoreCode IS NULL OR d.impacted_store_code = :impactedStoreCode)
  AND (:status            IS NULL OR d.status_code = :status)
ORDER BY d.doc_no DESC
LIMIT :size OFFSET :offset;
```

#### 6.1.3 GET /api/v1/documents/{docNo}

เอกสารฉบับเต็ม 12 ส่วนย่อย (k2-document.html) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน

| Item | Detail |
| --- | --- |
| Global No. | 3 |
| Method | GET |
| Path | /api/v1/documents/{docNo} |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์เมนู |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | โหลดเอกสาร + ร้านใหม่ + คู่แข่ง + ปัจจัย + ไฟล์แนบ + สรุปชดเชย ในคำขอเดียว |
| 2 | คำนวณ compensateAmount ต่อร้านเปิดใหม่ = ยอดชดเชยร้านถูกกระทบ × %ชดเชย (ปัดเศษที่ BE · ผลรวมต้องเท่ากับยอดชดเชยพอดี) |
| 3 | คำนวณ permissions: ส่วนไหนแก้ได้ตาม role + current_section_code (data-editrole เดิม) |
| 4 | FE ใช้ธงนี้แสดงป้าย "อ่านอย่างเดียว" ต่อส่วน + ซ่อนคอลัมน์ checkbox/Action ของตารางที่แก้ไม่ได้ |

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
  "docNo": "2026/00123",
  "statusCode": "06",
  "currentSection": "06",
  "impactedStore": { "storeCode": "00788", ... },
  // newStores[] = แหล่งข้อมูลของทั้งตารางร้านเปิดใหม่และกราฟ "สัดส่วนเงินชดเชยรายร้านเปิดใหม่"
  // compensateAmount คำนวณที่ BE (= compensation.amount x compensatePercent) — FE ไม่คูณเอง
  "newStores": [
    { "newStoreCode": "00990", "storeName": "สาขารัตนาธิเบศร์ 2", "distanceKm": 0.85,
      "compensatePercent": 60.0, "compensateAmount": 28920.00 },
    { "newStoreCode": "01180", "storeName": "สาขาซอยวัดกู้", "distanceKm": 1.40,
      "compensatePercent": 40.0, "compensateAmount": 19280.00 }
  ],
  "competitors": [ ... ],
  "factors": [ ... ],
  "compensation": { "amount": 48200.00, "salesDropPercent": 12.45 },
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

#### 6.1.4 POST /api/v1/documents

สร้างเอกสารจากข้อมูลที่ FS/SBP Statement ส่งกลับ — ตัดสินใจ 2026-08-06: ไม่มีฟอร์มสร้างเอกสารใน FE แล้ว (k2-create.html เหลือเป็นหน้าอธิบายกระบวนการ) เส้นนี้เรียกโดย pipeline/service token

| Item | Detail |
| --- | --- |
| Global No. | 4 |
| Method | POST |
| Path | /api/v1/documents |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | 02 HQ, 03 User Admin |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจซ้ำ: ร้าน + เดือนที่ถูกกระทบ ต้องยังไม่มีเอกสาร |
| 2 | ออกเลขที่ YYYY/xxxxx (running ต่อปี เริ่ม 00001 — กติกา SRS) |
| 3 | insert compensation_documents สถานะเริ่มต้น + เรียก initializeWorkflow({versionId, referenceId: docNo, userId}) ของ @srm/glb-workflow แล้ว addPreparedApprover ขั้น 06 |
| 4 | ส่งอีเมลตาม status_email_rules |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | W | เอกสารใหม่ |
| workflow_transaction / workflow_approver | W | เปิด instance + ผู้รับผิดชอบขั้นแรกผ่าน @srm/glb-workflow |
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
  "docNo": "2026/00124"
}
```

| Error / Condition |
| --- |
| 409 — ร้านนี้ในเดือนนี้มีเอกสารที่ยังดำเนินการอยู่ (active) — เอกสารเดิมที่จบด้วยหยุดชดเชย/เห็นควรไม่ชดเชย เปิดเรื่องใหม่ได้ · SDD GI |
| 422 — ข้อมูลบังคับไม่ครบ |

SQL Reference

```sql
-- กันซ้ำเฉพาะเอกสาร active (SDD GI): เอกสารเดิมที่จบด้วยหยุดชดเชย/เห็นควรไม่ชดเชย เปิดเรื่องใหม่ได้
SELECT 1 FROM compensation_documents
WHERE impact_process_id = :impactProcessId AND status_code <> :statusDone;

-- ออกเลขที่ YYYY/xxxxx (running ต่อปี) แล้วสร้างเอกสาร + เปิด workflow งานแรก (Section 06)
INSERT INTO compensation_documents (doc_no, year, running_no, impact_process_id, impacted_store_code, impact_month, status_code, current_section_code, created_by)
VALUES (:docNo, :year, :runningNo, :impactProcessId, :storeCode, :month, :statusInit, :section06, :empId);
INSERT INTO workflow_instances (instance_id, doc_no, instance_status, started_at, started_by)
VALUES (:instanceId, :docNo, :active, :now, :empId);
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status)
VALUES (:instanceId, :docNo, :section06, :statusOpen);
```

#### 6.1.5 PUT /api/v1/documents/{docNo}

บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่

| Item | Detail |
| --- | --- |
| Global No. | 5 |
| Method | PUT |
| Path | /api/v1/documents/{docNo} |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตาม section ปัจจุบัน |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่า role + section ปัจจุบันมีสิทธิ์แก้ส่วนที่ส่งมา (เช่น Section 01 แก้คู่แข่ง/ปัจจัยได้) |
| 2 | validate %ชดเชยของร้านใหม่รวมกันต้องเท่ากับ 100% แล้วคำนวณ compensateAmount ใหม่ทุกแถว |
| 3 | ส่งอาร์เรย์มา = ชุดข้อมูลเต็มของส่วนนั้น — รายการที่หายไปจากอาร์เรย์ถือว่าถูกลบ (รองรับปุ่ม "ลบที่เลือก" ในหน้าเอกสาร) |
| 4 | บันทึกและคืนเอกสารล่าสุด |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_new_stores | R/W | %ชดเชย · ระยะห่าง · เงินชดเชยต่อร้าน |
| document_competitors | R/W/D | คู่แข่ง — ลบรายการที่ไม่ได้ส่งมา |
| document_external_factors | R/W/D | ปัจจัยภายนอก — ลบรายการที่ไม่ได้ส่งมา |

#### Request / Query / Header

```json
{
  "newStores": [ { "newStoreCode": "00990", "compensatePercent": 60.0 },
                 { "newStoreCode": "01180", "compensatePercent": 40.0 } ],
  // ส่งเฉพาะส่วนที่แก้ · อาร์เรย์ที่ส่งมาคือชุดเต็มของส่วนนั้น
  "competitors": [ { "id": 12, "impactDate": "2566-10-10" } ]   // id 13 หายไป = ลบ
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
UPDATE document_new_stores       SET compensate_percent = :pct, compensate_amount = :amount
WHERE new_store_code = :newStoreCode AND doc_no = :docNo;
UPDATE document_competitors      SET impact_date = :date         WHERE id = :competitorId AND doc_no = :docNo;
UPDATE document_external_factors SET date_from = :from, date_to = :to WHERE id = :factorId AND doc_no = :docNo;

-- ลบรายการที่ผู้ใช้เอาออก (ปุ่ม "ลบที่เลือก" ส่งอาร์เรย์ชุดใหม่มาแทนทั้งชุด)
DELETE FROM document_competitors      WHERE doc_no = :docNo AND id NOT IN (:keepCompetitorIds);
DELETE FROM document_external_factors WHERE doc_no = :docNo AND id NOT IN (:keepFactorIds);
```

#### 6.1.6 POST /api/v1/documents/{docNo}/actions

ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · วงเงิน GM 50,000 / AVP 300,000 (SDD GI 24/02/2026)

| Item | Detail |
| --- | --- |
| Global No. | 6 |
| Method | POST |
| Path | /api/v1/documents/{docNo}/actions |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | เจ้าของ task ปัจจุบัน |
| Requirement Tag | K2 · 3.1.4 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่าผู้ใช้เป็น approver ของ state ปัจจุบันใน @srm/glb-workflow (getTransaction / getPermissionEvents) |
| 2 | validate เลือกผลแล้ว — ไม่งั้น 422 ข้อความ SRS ตรงตัว |
| 3 | คำนวณขั้นถัดไปตามตารางเส้นทาง (ตารางเส้นทาง workflow · SDD GI): 06 ไม่ชดเชย/หยุดชดเชย → เสร็จสิ้น · 01/02 เห็นควรไม่ชดเชย → เสร็จสิ้นทันที (ไม่อนุมัติในเดือนนั้น) · 02 ชดเชย ≤ 50,000 → เสร็จสิ้น (จบที่ GM) · 50,001–300,000 → 03 → จบ (เกิน 300,000 รอ confirm) · ตัดขั้นบัญชี 04/05 (SDD v7.5) · ทุกขั้นมีเส้นส่งกลับ |
| 4 | insert consideration_logs + ปิด task เดิม เปิด task ใหม่ · กรณี 06 เห็นควรไม่ชดเชย ระบบตั้งงานเดือนถัดไปให้เจ้าของงานคนเดิม (SDD GI) |
| 5 | ส่งอีเมล TO/CC ตาม status_email_rules |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_transaction / workflow_history / workflow_approver | R/W | triggerEvent() ของ engine เดิม — เดิน state + บันทึก history + ตั้ง approver ขั้นถัดไป |
| compensation_documents | W | อัปเดต Status + CurSection |
| consideration_logs | W | บันทึกผลพิจารณา |
| status_email_rules | R | ผู้รับอีเมล |

#### Request / Query / Header

```json
{
  "result": "เห็นควรชดเชย",
  // 6-enum verbatim: เห็นควรชดเชย / เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้
  // / ส่งหน่วยงานส่งเสริมธุรกิจ SBP (SDD GI — เดิม "ส่งฝ่ายส่งเสริมธุรกิจ SBP") / ส่งเจ้าหน้าที่ SBP DSA / ส่งกลับ
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
-- result รับ 6-enum verbatim เท่านั้น: เห็นควรชดเชย / เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้ / ส่งหน่วยงานส่งเสริมธุรกิจ SBP (SDD GI) / ส่งเจ้าหน้าที่ SBP DSA / ส่งกลับ
UPDATE workflow_tasks SET task_status = :statusClosed, action_result = :result, closed_at = :now
WHERE doc_no = :docNo AND section_code = :curSection AND task_status = :statusOpen;

INSERT INTO consideration_logs (doc_no, section_code, consider_by, result, detail, action_datetime)
VALUES (:docNo, :curSection, :empId, :result, :comment, :now);

-- คำนวณขั้นถัดไป (วงเงิน GM 50,000 / AVP 300,000 · SDD GI) → เปิดงานใหม่ + อัปเดตสถานะเอกสารแบบ optimistic lock
UPDATE compensation_documents SET status_code = :nextStatus, current_section_code = :nextSection, version_no = version_no + 1, updated_at = :now, updated_by = :empId
WHERE doc_no = :docNo AND version_no = :versionNo;
INSERT INTO workflow_tasks (instance_id, doc_no, section_code, task_status)
VALUES (:instanceId, :docNo, :nextSection, :statusOpen);

SELECT r.status_code, d.status_name, r.to_section_code, r.cc_section_code
FROM status_email_rules r JOIN document_statuses d ON d.status_code = r.status_code
WHERE r.status_code = :nextStatus;
```

#### 6.1.7 GET /api/v1/documents/{docNo}/timeline

ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร)

| Item | Detail |
| --- | --- |
| Global No. | 7 |
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

#### 6.1.8 POST /api/v1/documents/{docNo}/attachments

แนบไฟล์เข้าเอกสาร — จำกัด 5MB ต่อไฟล์ตาม SRS

| Item | Detail |
| --- | --- |
| Global No. | 8 |
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

#### 6.1.9 GET /api/v1/documents/{docNo}/attachments/{attachId}/download

ดาวน์โหลดไฟล์แนบผ่าน BE stream โดยตรวจสิทธิ์เอกสารและ scanStatus=CLEAN ก่อนส่ง binary

| Item | Detail |
| --- | --- |
| Global No. | 9 |
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

#### 6.1.10 GET /api/v1/documents/{docNo}/attachments/download-all

ดาวน์โหลดไฟล์แนบทั้งหมดของเอกสารเป็นไฟล์ .zip — ปุ่ม "ดาวน์โหลดทั้งหมด" ระดับการ์ด (เทียบเท่าปุ่ม Download ของ K2 เดิม)

| Item | Detail |
| --- | --- |
| Global No. | 10 |
| Method | GET |
| Path | /api/v1/documents/{docNo}/attachments/download-all |
| Group | งาน & เอกสารประกันรายได้ |
| Access / Role | ตามสิทธิ์อ่านเอกสาร |
| Requirement Tag | K2 · 3.1.6 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจสิทธิ์อ่านเอกสารเหมือนเส้นดาวน์โหลดรายไฟล์ |
| 2 | รวมเฉพาะไฟล์ที่ผ่าน AV clean guard |
| 3 | stream .zip ชื่อ {docNo}-attachments.zip |

| DB Object | R/W | Usage |
| --- | --- | --- |
| document_attachments | R | รายการไฟล์แนบของเอกสาร |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
200 OK · application/zip (Content-Disposition: attachment; filename="2026-00123-attachments.zip")
```

| Error / Condition |
| --- |
| 404 — ไม่มีไฟล์แนบในเอกสารนี้ |
| 403 |

#### 6.1.11 GET /api/v1/documents/{docNo}/sales

ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง × 15 วัน) — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร k2-document.html

| Item | Detail |
| --- | --- |
| Global No. | 11 |
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

### 6.2 ข้อมูลอ้างอิง (Lookup / Reference)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/competitors | master แบรนด์ร้านคู่แข่ง 11 รายการ (รหัส 01–11 · ชื่อไทย+อังกฤษ) — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html) · จัดการที่หน้า k2-competitors.html |
| 2 | POST | /api/v1/competitors | เพิ่มแบรนด์ร้านคู่แข่งใน master (หน้า k2-competitors.html) — เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม |
| 3 | PUT | /api/v1/competitors/{code} | แก้ไขชื่อไทย/อังกฤษ/รายละเอียดของแบรนด์คู่แข่ง — แก้รหัสไม่ได้ · ต้องระบุเหตุผล |
| 4 | DELETE | /api/v1/competitors/{code} | ลบแบรนด์คู่แข่งออกจาก master — ต้องระบุเหตุผล และห้ามลบถ้ายังถูกอ้างในเอกสาร |
| 5 | GET | /api/v1/document-statuses | รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report) |
| 6 | GET | /api/v1/workflow-sections | รายการ Section 5 ขั้น + วงเงินอนุมัติต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE แสดงวงเงินจากข้อมูล ไม่ hardcode |
| 7 | GET | /api/v1/decisions | ผลพิจารณาจาก master decisions — FE เรนเดอร์ปุ่มพิจารณาจากเส้นนี้ ไม่ hardcode 6-enum (เปลี่ยนชื่อปุ่มตาม SDD GI ได้ที่ data) |

#### 6.2.1 GET /api/v1/competitors

master แบรนด์ร้านคู่แข่ง 11 รายการ (รหัส 01–11 · ชื่อไทย+อังกฤษ) — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html) · จัดการที่หน้า k2-competitors.html

| Item | Detail |
| --- | --- |
| Global No. | 12 |
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
| competitors | R | master แบรนด์คู่แข่ง 11 ราย (Lotus Express, Mini Big C, Tops Daily, Family Mart, Jiffy, CJ Express, Max Valu, Super Cheap, Lawson 108, Joy, Other) |

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

#### 6.2.2 POST /api/v1/competitors

เพิ่มแบรนด์ร้านคู่แข่งใน master (หน้า k2-competitors.html) — เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม

| Item | Detail |
| --- | --- |
| Global No. | 13 |
| Method | POST |
| Path | /api/v1/competitors |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | validate code / nameTh / nameEn ครบทั้งสามช่อง |
| 2 | ตรวจรหัสซ้ำ → 409 |
| 3 | insert competitors + บันทึก audit_logs พร้อมเหตุผล |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | แถวใหม่ (code · name_th · name_en · remark) |
| audit_logs | W | audit + เหตุผล |

#### Request / Query / Header

```json
{
  "code": "12",
  "nameTh": "ร้านคู่แข่งรายใหม่",
  "nameEn": "New Competitor",
  "remark": "",
  "reason": "พบคู่แข่งรายใหม่ในพื้นที่ RN"
}
```

#### Response

```json
201 Created
```

| Error / Condition |
| --- |
| 409 — รหัสคู่แข่งซ้ำ |
| 422 — ข้อมูลบังคับไม่ครบ |

#### 6.2.3 PUT /api/v1/competitors/{code}

แก้ไขชื่อไทย/อังกฤษ/รายละเอียดของแบรนด์คู่แข่ง — แก้รหัสไม่ได้ · ต้องระบุเหตุผล

| Item | Detail |
| --- | --- |
| Global No. | 14 |
| Method | PUT |
| Path | /api/v1/competitors/{code} |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | แก้ได้เฉพาะ nameTh / nameEn / remark |
| 2 | บันทึก audit_logs (old → new + เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | ค่าใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ + เหตุผล |

#### Request / Query / Header

```json
{
  "nameEn": "Lawson 108",
  "reason": "ปรับให้ตรงกับชื่อทางการค้า"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบรหัส |
| 422 — ไม่ได้ระบุเหตุผล |

#### 6.2.4 DELETE /api/v1/competitors/{code}

ลบแบรนด์คู่แข่งออกจาก master — ต้องระบุเหตุผล และห้ามลบถ้ายังถูกอ้างในเอกสาร

| Item | Detail |
| --- | --- |
| Global No. | 15 |
| Method | DELETE |
| Path | /api/v1/competitors/{code} |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่าไม่มี document_competitors อ้างรหัสนี้ → ไม่งั้น 409 |
| 2 | ลบ + บันทึก audit_logs |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | ลบแถว |
| document_competitors | R | ตรวจการอ้างอิง |
| audit_logs | W | audit + เหตุผล |

#### Request / Query / Header

```json
{
  "reason": "ไม่ใช่ร้านสะดวกซื้อเชนที่ต้องติดตาม"
}
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — ยังถูกอ้างในเอกสาร |
| 404 |

#### 6.2.5 GET /api/v1/document-statuses

รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report)

| Item | Detail |
| --- | --- |
| Global No. | 16 |
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

#### 6.2.6 GET /api/v1/workflow-sections

รายการ Section 5 ขั้น + วงเงินอนุมัติต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE แสดงวงเงินจากข้อมูล ไม่ hardcode

| Item | Detail |
| --- | --- |
| Global No. | 17 |
| Method | GET |
| Path | /api/v1/workflow-sections |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · master section |

| Step | Flow |
| --- | --- |
| 1 | อ่าน workflow_sections ทั้งหมดเรียงตามลำดับ 06→08→01→02→03 |
| 2 | คืน approve_limit_amount ต่อขั้น (= SectionLimitCost ของ K2 เดิม · GM 50,000 / AVP 300,000 ตาม SDD GI) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_sections | R | ขั้นตอน 06/08/01/02/03 + approve_limit_amount |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [
    { "sectionCode": "06", "sectionName": "ฝ่าย SBP DSA", "approveLimitAmount": null },
    { "sectionCode": "02", "sectionName": "GM ส่งเสริมธุรกิจ SBP", "approveLimitAmount": 50000.00 },
    { "sectionCode": "03", "sectionName": "ผู้บริหารสำนักบริหาร SBP", "approveLimitAmount": 300000.00 }
  ]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- approve_limit_amount = SectionLimitCost ของ K2 เดิม (GM 50,000 / AVP 300,000 · SDD GI) — วงเงินเป็น data ไม่ hardcode
SELECT section_code, section_name, sort_order, approve_limit_amount
FROM workflow_sections
ORDER BY sort_order;
```

#### 6.2.7 GET /api/v1/decisions

ผลพิจารณาจาก master decisions — FE เรนเดอร์ปุ่มพิจารณาจากเส้นนี้ ไม่ hardcode 6-enum (เปลี่ยนชื่อปุ่มตาม SDD GI ได้ที่ data)

| Item | Detail |
| --- | --- |
| Global No. | 18 |
| Method | GET |
| Path | /api/v1/decisions |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · DecisionProfile (DB เดิม) |

| Step | Flow |
| --- | --- |
| 1 | อ่าน decisions ที่ใช้งานอยู่ กรองตาม sectionCode ที่ส่งมา (ปุ่มต่างกันตามขั้น) |
| 2 | คืน decisionName (ข้อความปุ่มไทย verbatim) · flowName (ชื่อในผัง flow) · resultName (ชื่อที่แสดงในรายงาน/ประวัติ) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| decisions | R | master ผลพิจารณา 3 ชื่อต่อรายการ |

#### Request / Query / Header

```json
Query: ?sectionCode=06
```

#### Response

```json
{
  "items": [
    { "decisionCode": "01", "decisionName": "ส่งหน่วยงานส่งเสริมธุรกิจ SBP", "flowName": "ส่งต่อ 01", "resultName": "ประกันรายได้" }
  ]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- master ผลพิจารณา (= DecisionProfile) · 3 ชื่อต่อรายการ: ปุ่ม / ผัง flow / ผลลัพธ์ในรายงาน
SELECT decision_code, decision_name, flow_name, result_name, result_category
FROM decisions
WHERE is_active = true
  AND (:sectionCode IS NULL OR section_code = :sectionCode)
ORDER BY sort_order;
```

### 6.3 Master Data

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/factors | รายการปัจจัยภายนอก (external_factors) |
| 2 | POST | /api/v1/factors | เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS) |
| 3 | PUT | /api/v1/factors/{code} | แก้ไขปัจจัยภายนอก |
| 4 | DELETE | /api/v1/factors/{code} | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) |
| 5 | GET | /api/v1/audit-logs | ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม→ใหม่ · เหตุผล · เมื่อไร) — แผงประวัติท้ายหน้าจอ 3.1.9 |

#### 6.3.1 GET /api/v1/factors

รายการปัจจัยภายนอก (external_factors)

| Item | Detail |
| --- | --- |
| Global No. | 19 |
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

#### 6.3.2 POST /api/v1/factors

เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 20 |
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

#### 6.3.3 PUT /api/v1/factors/{code}

แก้ไขปัจจัยภายนอก

| Item | Detail |
| --- | --- |
| Global No. | 21 |
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

#### 6.3.4 DELETE /api/v1/factors/{code}

ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด)

| Item | Detail |
| --- | --- |
| Global No. | 22 |
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

#### 6.3.5 GET /api/v1/audit-logs

ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม→ใหม่ · เหตุผล · เมื่อไร) — แผงประวัติท้ายหน้าจอ 3.1.9

| Item | Detail |
| --- | --- |
| Global No. | 23 |
| Method | GET |
| Path | /api/v1/audit-logs |
| Group | Master Data |
| Access / Role | 01 Admin, 02 HQ, 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

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

### 6.4 System Config (Global)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/configs | รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ system-config.html) |
| 2 | GET | /api/v1/configs/{key} | อ่านค่ากำหนดรายตัว — เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที |
| 3 | POST | /api/v1/configs | เพิ่มค่ากำหนดใหม่ — key ห้ามซ้ำ และ validate ค่าตาม value_type |
| 4 | PUT | /api/v1/configs/{key} | แก้ค่ากำหนด — ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้ |
| 5 | DELETE | /api/v1/configs/{key} | ลบค่ากำหนด — ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล |

#### 6.4.1 GET /api/v1/configs

รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ system-config.html)

| Item | Detail |
| --- | --- |
| Global No. | 24 |
| Method | GET |
| Path | /api/v1/configs |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | query mas_param (ตารางของระบบ SBP เดิม) ตาม category / คำค้น |
| 2 | คืนครบทุก field รวม value_type · unit · is_editable |

| DB Object | R/W | Usage |
| --- | --- | --- |
| mas_param (ระบบ SBP เดิม) | R | ค่ากำหนดกลางทั้งหมด — ไม่สร้างตาราง system_configs ใหม่ |

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
FROM mas_param
WHERE (:category IS NULL OR category = :category)
  AND (:q IS NULL OR config_key LIKE :q)
ORDER BY category, config_key;
```

#### 6.4.2 GET /api/v1/configs/{key}

อ่านค่ากำหนดรายตัว — เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที

| Item | Detail |
| --- | --- |
| Global No. | 25 |
| Method | GET |
| Path | /api/v1/configs/{key} |
| Group | System Config (Global) |
| Access / Role | ทุก role (อ่าน) / service token |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | อ่าน mas_param ด้วย config_key (param_name) |
| 2 | ตอบพร้อม header Cache-Control (TTL 5 นาที) — service ฝั่งเรียก cache ตาม |
| 3 | ค่า BOOLEAN/NUMBER/JSON ตอบเป็น typed value ตาม value_type ไม่ใช่ string ล้วน |

| DB Object | R/W | Usage |
| --- | --- | --- |
| mas_param (ระบบ SBP เดิม) | R | ค่ารายตัว |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "configKey": "workflow.gm_amount_limit",
  "value": 50000,
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
FROM mas_param
WHERE config_key = :key;
-- ตอบพร้อม Cache-Control TTL 5 นาที · แปลงเป็น typed value ตาม value_type
```

#### 6.4.3 POST /api/v1/configs

เพิ่มค่ากำหนดใหม่ — key ห้ามซ้ำ และ validate ค่าตาม value_type

| Item | Detail |
| --- | --- |
| Global No. | 26 |
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
| mas_param (ระบบ SBP เดิม) | W | แถวใหม่ |
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
INSERT INTO mas_param (config_key, category, config_value, value_type, unit, description, is_editable)
VALUES (:key, :category, :value, :valueType, :unit, :description, TRUE);

INSERT INTO audit_logs (table_name, ref_key, action_type, new_value, updated_by, updated_at)
VALUES (:tableName, :key, :actionAdd, :newValue, :actor, :now);
```

#### 6.4.4 PUT /api/v1/configs/{key}

แก้ค่ากำหนด — ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 27 |
| Method | PUT |
| Path | /api/v1/configs/{key} |
| Group | System Config (Global) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Global Config |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ is_editable — ค่าคงที่ทางธุรกิจ (รัศมี · วงเงิน GM 50,000/AVP 300,000 · เกณฑ์ 60 วัน · เกณฑ์ −10 ตามข้อ 8.2) ตอบ 422 |
| 2 | validate ค่าใหม่ตาม value_type + ต้องระบุ reason เสมอ |
| 3 | update + บันทึก audit_logs (EDIT · old_value → new_value · เหตุผล) |
| 4 | broadcast invalidate cache ให้ทุก service อ่านค่าใหม่ทันที |

| DB Object | R/W | Usage |
| --- | --- | --- |
| mas_param (ระบบ SBP เดิม) | W | ค่าใหม่ |
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
UPDATE mas_param SET config_value = :value
WHERE config_key = :key AND is_editable = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :key, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
-- broadcast invalidate cache ให้ทุก service
```

#### 6.4.5 DELETE /api/v1/configs/{key}

ลบค่ากำหนด — ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล

| Item | Detail |
| --- | --- |
| Global No. | 28 |
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
| mas_param (ระบบ SBP เดิม) | W | ลบแถว |
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
DELETE FROM mas_param WHERE config_key = :key AND is_editable = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, reason, updated_by, updated_at)
VALUES (:tableName, :key, :actionDelete, :oldValue, :reason, :actor, :now);
```

### 6.5 Email Template (Notification)

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/email-templates | รายการ 8 email template (EM-01–08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ email-template.html) |
| 2 | GET | /api/v1/email-templates/{code} | อ่าน template รายตัว (EM-01–08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น |
| 3 | PUT | /api/v1/email-templates/{code} | บันทึกเนื้อหา template — แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules) |
| 4 | POST | /api/v1/email-templates/{code}/reset | รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ) |
| 5 | POST | /api/v1/email-templates/reset-all | รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default") |

#### 6.5.1 GET /api/v1/email-templates

รายการ 8 email template (EM-01–08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ email-template.html)

| Item | Detail |
| --- | --- |
| Global No. | 29 |
| Method | GET |
| Path | /api/v1/email-templates |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | query email_template (ตารางของระบบ SBP เดิม) ทั้ง 8 รหัส EM-01–08 |
| 2 | join จุดส่งใน flow (status_email_rules) เพื่อแสดงผู้รับ TO/CC ที่ล็อกไว้ |
| 3 | คืน subject/body ปัจจุบัน + is_customized |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_template (ระบบ SBP เดิม) | R | เนื้อหา template ทั้งหมด (ตารางใหม่) |
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
FROM email_template
ORDER BY template_code;
-- FE ประกอบผู้รับ TO/CC จาก status_email_rules มาแสดง (อ่านอย่างเดียว)
```

#### 6.5.2 GET /api/v1/email-templates/{code}

อ่าน template รายตัว (EM-01–08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น

| Item | Detail |
| --- | --- |
| Global No. | 30 |
| Method | GET |
| Path | /api/v1/email-templates/{code} |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | อ่าน email_template (ระบบ SBP เดิม) ด้วย template_code (EM-01–08) |
| 2 | คืน subject/body + รายการตัวแปร merge ที่รองรับ + ผู้รับ TO/CC (อ่านอย่างเดียว) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_template (ระบบ SBP เดิม) | R | เนื้อหารายตัว |
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
FROM email_template
WHERE template_code = :code;

SELECT to_section_code, cc_section_code FROM status_email_rules WHERE template_code = :code;
```

#### 6.5.3 PUT /api/v1/email-templates/{code}

บันทึกเนื้อหา template — แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules)

| Item | Detail |
| --- | --- |
| Global No. | 31 |
| Method | PUT |
| Path | /api/v1/email-templates/{code} |
| Group | Email Template (Notification) |
| Access / Role | 01 Admin |
| Requirement Tag | ใหม่ · Notification |

| Step | Flow |
| --- | --- |
| 1 | validate ใช้เฉพาะตัวแปร merge ที่รองรับของ template นั้น |
| 2 | ปฏิเสธการแก้ From/To/Cc — ผู้รับกำหนดที่ status_email_rules เท่านั้น |
| 3 | update email_template (ระบบ SBP เดิม) + set is_customized = true |
| 4 | บันทึก audit_logs (EDIT · old → new · เหตุผล) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| email_template (ระบบ SBP เดิม) | W | subject/body ใหม่ |
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
UPDATE email_template SET subject = :subject, body = :body, is_customized = TRUE
WHERE template_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, old_value, new_value, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionEdit, :oldValue, :newValue, :reason, :actor, :now);
```

#### 6.5.4 POST /api/v1/email-templates/{code}/reset

รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ)

| Item | Detail |
| --- | --- |
| Global No. | 32 |
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
| email_template (ระบบ SBP เดิม) | W | คืนค่า Default |
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
UPDATE email_template SET subject = :defaultSubject, body = :defaultBody, is_customized = FALSE
WHERE template_code = :code;

INSERT INTO audit_logs (table_name, ref_key, action_type, reason, updated_by, updated_at)
VALUES (:tableName, :code, :actionReset, :reason, :actor, :now);
```

#### 6.5.5 POST /api/v1/email-templates/reset-all

รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default")

| Item | Detail |
| --- | --- |
| Global No. | 33 |
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
| email_template (ระบบ SBP เดิม) | W | คืนค่า Default ทั้ง 8 |
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
UPDATE email_template SET subject = default_subject, body = default_body, is_customized = FALSE
WHERE is_customized = TRUE;

INSERT INTO audit_logs (table_name, ref_key, action_type, reason, updated_by, updated_at)
SELECT :tableName, template_code, :actionReset, :reason, :actor, :now
FROM email_template WHERE is_customized = FALSE;
```

### 6.6 รายงาน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/reports/status-summary | รายงานตรวจสอบประกันรายได้ (SBP Mall) — Preview Report · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) |
| 2 | GET | /api/v1/reports/status-summary/export | Export CSV to Batch — ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา |

#### 6.6.1 GET /api/v1/reports/status-summary

รายงานตรวจสอบประกันรายได้ (SBP Mall) — Preview Report · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 34 |
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
  "items": [{ "docNo": "2026/00098", "storeCode": "00788", "status": "เสร็จสิ้นดำเนินการ", "compensateAmount": 85000.00, ... }]
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
WHERE d.year = :year
  AND (:month  IS NULL OR h.submit_account_month = :month)
  AND (:zone   IS NULL OR s.zone_code = :zone)
  AND (:statusCode IS NULL OR d.status_code = :statusCode)
  AND (:result IS NULL OR cl.result_category = :result)   -- APPROVE / REJECT (filter ประกันรายได้/ไม่ประกันรายได้)
ORDER BY d.doc_no
LIMIT :size OFFSET :offset;
```

#### 6.6.2 GET /api/v1/reports/status-summary/export

Export CSV to Batch — ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา

| Item | Detail |
| --- | --- |
| Global No. | 35 |
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
WHERE d.year = :year
  AND (:month  IS NULL OR h.submit_account_month = :month)
  AND (:result IS NULL OR cl.result_category = :result)
ORDER BY d.doc_no;
```

### 6.7 Batch Job Admin

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/jobs | รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด — reference contract สำหรับแบบฟอร์มพารามิเตอร์และประวัติการรันเท่านั้น |
| 2 | GET | /api/v1/jobs/{jobNo} | รายละเอียด job หนึ่งตัวสำหรับ tab แบบฟอร์มพารามิเตอร์: schedule, input/configurable parameters, output และ current status |
| 3 | PUT | /api/v1/jobs/{jobNo}/params | แก้พารามิเตอร์ที่ editable ของ job — ค่าคงที่ทางธุรกิจแก้ผ่าน UI/API ไม่ได้ |
| 4 | POST | /api/v1/jobs/{jobNo}/run | สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล — รายละเอียด flow การทำงานอยู่ในเอกสาร BE/Runbook ไม่ใช่ tab ที่ต้องทำใน FE Batch Monitor |
| 5 | PUT | /api/v1/jobs/{jobNo}/enabled | เปิด/ปิดการทำงานของ job ตามรอบเวลา |
| 6 | GET | /api/v1/jobs/{jobNo}/runs | ประวัติการรันของ job สำหรับ tab ประวัติการรันในหน้า Batch Monitor |

Batch Job Admin เป็น endpoint reference สำหรับ FE Batch Monitor เฉพาะ 2 tab: แบบฟอร์มพารามิเตอร์ และประวัติการรัน เท่านั้น; ไม่ออกแบบ flowchart การทำงาน, step-by-step batch flow หรือ Database ที่ใช้ใน LLDD API ฉบับรวม

#### 6.7.1 GET /api/v1/jobs

รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด — reference contract สำหรับแบบฟอร์มพารามิเตอร์และประวัติการรันเท่านั้น

| Item | Detail |
| --- | --- |
| Global No. | 36 |
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

#### 6.7.2 GET /api/v1/jobs/{jobNo}

รายละเอียด job หนึ่งตัวสำหรับ tab แบบฟอร์มพารามิเตอร์: schedule, input/configurable parameters, output และ current status

| Item | Detail |
| --- | --- |
| Global No. | 37 |
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

#### 6.7.3 PUT /api/v1/jobs/{jobNo}/params

แก้พารามิเตอร์ที่ editable ของ job — ค่าคงที่ทางธุรกิจแก้ผ่าน UI/API ไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 38 |
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

#### 6.7.4 POST /api/v1/jobs/{jobNo}/run

สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล — รายละเอียด flow การทำงานอยู่ในเอกสาร BE/Runbook ไม่ใช่ tab ที่ต้องทำใน FE Batch Monitor

| Item | Detail |
| --- | --- |
| Global No. | 39 |
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

#### 6.7.5 PUT /api/v1/jobs/{jobNo}/enabled

เปิด/ปิดการทำงานของ job ตามรอบเวลา

| Item | Detail |
| --- | --- |
| Global No. | 40 |
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

#### 6.7.6 GET /api/v1/jobs/{jobNo}/runs

ประวัติการรันของ job สำหรับ tab ประวัติการรันในหน้า Batch Monitor

| Item | Detail |
| --- | --- |
| Global No. | 41 |
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

### 6.8 Workflow ภายใน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | POST | /api/v1/workflows/instances | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม |
| 2 | GET | /api/v1/workflows/instances/{id} | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) |
| 3 | GET | /api/v1/workflows/summary | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น |

#### 6.8.1 POST /api/v1/workflows/instances

เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม

| Item | Detail |
| --- | --- |
| Global No. | 42 |
| Method | POST |
| Path | /api/v1/workflows/instances |
| Group | Workflow ภายใน |
| Access / Role | service token (ภายใน) |
| Requirement Tag | แทน K2 StartInstance (Job 8b) |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ service token (ไม่ใช่ JWT ผู้ใช้) |
| 2 | lock fgi_impact_processes แล้วตรวจ Gen Flow Gate ทุกข้อ: workflow_generation_status=W · branch type FAM/FB1/FC1/FB2/FVB/FVC · ระยะทางตามเกณฑ์ · opt_dv_user_id ไม่ว่าง · juristic ร้านใหม่ต่างจากร้านถูกกระทบ · growth_rate_diff ≤ −10 · sales_status ∈ {Y,N} |
| 3 | fail ถาวร: branch type นอกเซ็ต, ระยะทางเกิน, DV หาย, นิติบุคคลเดียวกัน หรือ growth > −10 → workflow_generation_status=N |
| 4 | ข้อมูลต้นทางยังไม่พร้อม: distance/juristic/growth เป็น NULL หรือ sales_status ไม่ใช่ Y/N → คง W (ตอบ 422 พร้อมเหตุผล) |
| 5 | ผ่าน: ใช้ compensation_documents ที่ Job 8 สร้างแล้ว + initializeWorkflow/addPreparedApprover ขั้น 06 ผ่าน @srm/glb-workflow แล้วตั้ง workflow_generation_status=Y |
| 6 | ส่งอีเมลสรุปราย DV หลัง commit |

| DB Object | R/W | Usage |
| --- | --- | --- |
| fgi_impact_processes | R/W | source of truth ของ workflow_generation_status W→Y/N |
| impacted_stores / stores / fgi_impact_stores / fgi_impact_sales_summaries | R | คอลัมน์ gate จากตารางจริง |
| compensation_documents | R | เอกสารอัตโนมัติจาก Job 8 |
| workflow_transaction / workflow_approver | W | เปิด instance + ผู้รับผิดชอบขั้นแรก (@srm/glb-workflow) |

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
  "docNo": "2026/00124",
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
       ss.growth_rate_diff, ss.sales_status, ns.branch_type, pair.distance_km, impacted.region_code
FROM fgi_impact_processes p
JOIN impacted_stores ist ON ist.store_code = p.impacted_store_code
JOIN stores impacted ON impacted.store_code = p.impacted_store_code
JOIN fgi_impact_stores pair ON pair.impact_process_id = p.id
JOIN stores ns ON ns.store_code = pair.new_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = p.id
WHERE p.id = :impactProcessId FOR UPDATE OF p;

-- fail ถาวร (branch/distance over/missing DV/same juristic/growth > -10) → N; เฉพาะ distance/juristic/growth NULL หรือ sales_status ยังไม่พร้อมจึงคง W
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

#### 6.8.2 GET /api/v1/workflows/instances/{id}

สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม)

| Item | Detail |
| --- | --- |
| Global No. | 43 |
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
  "docNo": "2026/00124",
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

#### 6.8.3 GET /api/v1/workflows/summary

ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น

| Item | Detail |
| --- | --- |
| Global No. | 44 |
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

### 6.9 Interface & Dashboard

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/interfaces/tracking | สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) |
| 2 | POST | /api/v1/interfaces/sta/ack | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว |
| 3 | GET | /api/v1/interfaces/pending-ack | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน |
| 4 | GET | /api/v1/dashboard/summary | ตัวเลข stat cards ของหน้าแรก (งานรอดำเนินการ) — ยกเลิกหน้า Overview/Dashboard แล้ว (ตัดสินใจ 2026-08-06) |

#### 6.9.1 GET /api/v1/interfaces/tracking

สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA)

| Item | Detail |
| --- | --- |
| Global No. | 45 |
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
    "docNo": "2026/00098",
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

#### 6.9.2 POST /api/v1/interfaces/sta/ack

Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว

| Item | Detail |
| --- | --- |
| Global No. | 46 |
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

#### 6.9.3 GET /api/v1/interfaces/pending-ack

รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน

| Item | Detail |
| --- | --- |
| Global No. | 47 |
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
  "items": [{ "dataName": "COMPENSATE_INIT_I", "docNo": "2026/00098", "ageDays": 2 }]
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

#### 6.9.4 GET /api/v1/dashboard/summary

ตัวเลข stat cards ของหน้าแรก (งานรอดำเนินการ) — ยกเลิกหน้า Overview/Dashboard แล้ว (ตัดสินใจ 2026-08-06)

| Item | Detail |
| --- | --- |
| Global No. | 48 |
| Method | GET |
| Path | /api/v1/dashboard/summary |
| Group | Interface & Dashboard |
| Access / Role | ทุก role |
| Requirement Tag | K2 (หน้าแรก = งานรอดำเนินการ) |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sectionCode ของผู้ใช้จาก user context ที่ BFF ส่งมา |
| 2 | นับงานค้างของ section นั้น + แยกกลุ่ม: ยอดขายไม่ครบ 60 วัน · รอเกิน 3 วัน · วงเงินเข้าเส้น AVP (> 50,000 · SDD GI) |
| 3 | cache 5 นาที |
| 4 | ตัด field abnormalStores/chart.monthly ของหน้า Overview เดิมออก |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_tasks | R | งานค้างของ section + จำนวนวันที่รอ |
| compensation_documents | R | ยอดชดเชยต่อเอกสาร (เกณฑ์วงเงิน AVP) |
| fgi_impact_sales_summaries | R | total_working_days < 60 = แถวแดง |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "waitingTasks": 24,
  "flagUnder60Days": 5,
  "pendingOver3Days": 7,
  "overGmLimit": 3
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- stat cards หน้าแรก = งานรอดำเนินการ (cache 5 นาที) · ยกเลิกหน้า Overview แล้ว (2026-08-06)
SELECT COUNT(*) AS waiting_tasks
FROM workflow_tasks WHERE section_code = :mySection AND task_status = :statusOpen;

SELECT COUNT(*) AS flag_under_60_days
FROM workflow_tasks t
JOIN compensation_documents d ON d.doc_no = t.doc_no
JOIN fgi_impact_sales_summaries s ON s.impact_process_id = d.impact_process_id
WHERE t.section_code = :mySection AND t.task_status = :statusOpen AND s.total_working_days < 60;

SELECT COUNT(*) AS pending_over_3_days
FROM workflow_tasks WHERE section_code = :mySection AND task_status = :statusOpen
  AND opened_at < :threeDaysAgo;

-- วงเงินเข้าเส้น AVP (> workflow.gm_amount_limit = 50,000 · SDD GI)
SELECT COUNT(*) AS over_gm_limit
FROM workflow_tasks t JOIN compensation_documents d ON d.doc_no = t.doc_no
WHERE t.section_code = :mySection AND t.task_status = :statusOpen AND d.total_compensation_amount > :gmLimit;
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
