# LLDD API - REST API and Integration Contract

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารนี้เป็น LLDD API ระดับรวมของระบบ SBPGI/SBP Mall ใช้เป็น master reference สำหรับ REST contract, auth, error, endpoint catalog, implementation pattern และ test scope ของ BE API LLDD รายกลุ่ม

## 2. Scope

| Item | Detail |
| --- | --- |
| API base | /api/v1 |
| Endpoint count | 29 endpoints, 6 groups |
| Detailed implementation docs | LLDD-BE-API-Common-Contracts, LLDD-BE-API-Document-List-Search, LLDD-BE-API-Document-Create-Update, LLDD-BE-API-Document-Detail-Aggregate, LLDD-BE-API-Document-Workflow-Actions, LLDD-BE-API-Workflow-Instances, LLDD-BE-API-Attachment-Sales-Timeline, LLDD-BE-API-Lookup, LLDD-BE-API-Report-and-Master-Data |
| Out of scope | Login/Auth implementation ของ platform, SAP/SR process ภายนอก, abnormal-stores endpoints ที่ยัง comment รอตัดสินใจ |

### 2.1 Input / Progress / Output Contract

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
| Mutation audit | workflow action ลง consideration_logs เท่านั้น (ยกเลิกระบบ audit ของ master 2026-08-07 · jobs เขียน application log) | mutation ที่ต้องมี reason ต้อง validate ก่อนเริ่ม transaction |

## 4. Endpoint Catalog

| Group | Count | Endpoint pattern | Implementation focus |
| --- | --- | --- | --- |
| งาน & เอกสารประกันรายได้ | 11 | /api/v1/tasks, /api/v1/documents, /api/v1/documents/{docNo}, /api/v1/documents ... | K2 · SRS 3.1.2 / 3.1.3 / 3.1.6 |
| ข้อมูลอ้างอิง (Lookup / Reference) | 2 | /api/v1/document-statuses, /api/v1/workflow-sections | K2 + FGI/FCS · master สำหรับ dropdown |
| Master Data | 8 | /api/v1/competitors, /api/v1/competitors, /api/v1/competitors/{code}, /api/v1/competitors/{code} ... | K2 · SRS 3.1.9 |
| รายงาน | 2 | /api/v1/reports/status-summary, /api/v1/reports/status-summary/export | K2 · SRS 3.1.7 |
| Workflow ภายใน | 3 | /api/v1/workflows/instances, /api/v1/workflows/instances/{id}, /api/v1/workflows/summary | K2 3.1.4 + FGI/FCS Job 8b |
| Interface & Dashboard | 3 | /api/v1/interfaces/tracking, /api/v1/interfaces/sta/ack, /api/v1/interfaces/pending-ack | FGI/FCS · tracking / watchdog |

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
| 6 | POST | /api/v1/documents/{docNo}/actions | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · วงเงิน เกณฑ์เดียว 100,000 (SDD GI 24/02/2026) |
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
| 2 | อ่านงานค้างจาก engine เดิม (schema sps_store): getPendingFlowByUser({userData}) ของ @srm/glb-workflow  — ไม่มีตาราง workflow_tasks ของ SBPGI แล้ว |
| 3 | join compensation_documents + stores + fgi_impact_sales_summaries คืน 9 คอลัมน์ตามหน้าจอและ salesDataDays สำหรับ red flag |

| DB Object | R/W | Usage |
| --- | --- | --- |
| sps_store.workflow_transaction / workflow_approver | R | งานค้างจาก @srm/glb-workflow (engine 13 ตาราง · schema sps_store · workflow_transaction 19,283 แถว ไม่มี PK/index — ดูการ์ดด้านบน) |
| compensation_documents | R | ข้อมูลเอกสาร |
| store (SBP เดิม) | R | ชื่อและภาคของร้าน — ตาราง stores ของ SBPGI ถูกตัด 2026-08-06 · คีย์ store_id · ภาค zone_cd |
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
-- ⚠️ ไม่มีตาราง workflow_tasks ของ SBPGI แล้ว — กล่องงานอ่านจาก engine กลาง (schema sps_store)
--    getPendingFlowByUser({userData}) 
-- ✅ DP-1 ปิดแล้ว: reference_id = compensation_documents.id (surrogate · varchar(255)) · ⚠️ DP-2 workflow_transaction ไม่มี PK/index (19,283 แถว → seq-scan) ยังไม่ตัดสิน
--    ยังไม่ตัดสิน — ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
WITH wh AS (
  -- workflow_transaction ไม่มี created_date — ใช้เวลา event แรกจาก workflow_history แทน
  SELECT transaction_id, MIN(create_date) AS first_event_date
  FROM sps_store.workflow_history GROUP BY transaction_id
)
SELECT d.round_no AS "roundNo",
       d.doc_no AS "docNo",
       d.impacted_store_code AS "impactedStoreCode",
       s.store_name AS "impactedStoreName",
       s.zone_cd AS "regionCode",
       GREATEST(COALESCE(-ss.growth_rate_diff, 0), 0) AS "salesDeclinePercent",
       d.total_compensation_amount AS "totalCompensationAmount",
       d.status_code AS "statusCode",
       d.current_section_code AS "currentSection",
       GREATEST(CURRENT_DATE - wh.first_event_date::date, 0) AS "daysPending",
       ss.total_working_days AS "salesDataDays"
FROM sps_store.workflow_approver a
JOIN sps_store.workflow_transaction w ON w.transaction_id = a.transaction_id
JOIN compensation_documents d ON d.id::text = w.reference_id   -- DP-1 = surrogate id   -- DP-1
JOIN store s ON s.store_id = d.impacted_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = d.impact_process_id
WHERE a.state_id = :sectionFromJwt AND a.state_id = w.current_state_id AND w.version_id = :sbpgiVersionId
ORDER BY w.update_date
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
Query: ?year=2026&impactedStoreCode=00788&status=06&result=APPROVE&page=1
(status = section ที่รออยู่ 06/08/01/02/03 หรือ END)
(result = APPROVE | REJECT | CANCELLED | NONE — ประกันรายได้ / ไม่ประกันรายได้ / ยกเลิกโดยระบบ / ยังไม่มีผล · CANCELLED เพิ่ม 2026-08-10 ตาม master DecisionProfile)
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
       s.zone_cd AS "regionCode",
       GREATEST(COALESCE(-ss.growth_rate_diff, 0), 0) AS "salesDeclinePercent",
       d.total_compensation_amount AS "totalCompensationAmount",
       d.status_code AS "statusCode",
       d.current_section_code AS "currentSection",
       -- workflow_transaction ไม่มี created_date (มีแค่ update_date) — วันที่เริ่มงานเอาจาก workflow_history
       CASE WHEN w.current_status_id <> :statusDone THEN GREATEST(CURRENT_DATE - wh.first_event_date::date, 0) ELSE 0 END AS "daysPending",
       ss.total_working_days AS "salesDataDays"
FROM compensation_documents d
JOIN store s ON s.store_id = d.impacted_store_code
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = d.impact_process_id
LEFT JOIN sps_store.workflow_transaction w ON w.reference_id = d.id::text   -- DP-1 = surrogate id (reference_id เป็น varchar(255)) AND w.version_id = :sbpgiVersionId   -- DP-1 · DP-2 (ไม่มี index → seq-scan)
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
  // newStores[] = แหล่งข้อมูลของตารางร้านเปิดใหม่ (กราฟสัดส่วนเงินชดเชยถอดออกแล้ว 2026-08-06)
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
| 3 | insert compensation_documents สถานะเริ่มต้น + เรียก initializeWorkflow({versionId, referenceId, userId}) [referenceId ยังไม่ตัดสินว่าใช้ docNo หรือ surrogate id — DP-1 ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4] ของ @srm/glb-workflow แล้ว addPreApprover ขั้น 06 |
| 4 | SBPGI เรียก sendEmail() แจ้งเปิดเรื่อง ด้วยเลข template จาก workflow_route.email_id (นอก transaction) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | W | เอกสารใหม่ |
| sps_store.workflow_transaction / workflow_approver | W (โดย lib) | เปิด instance + ผู้รับผิดชอบขั้นแรกผ่าน initializeWorkflow() + addPreApprover() ของ @srm/glb-workflow (schema sps_store) — ห้ามเขียนตรง |
| email_template (SBP เดิม) | R | template — อ่านอย่างเดียว |
| email_sent (SBP เดิม) | W (โดย email-lib) | SBPGI เรียก sendEmail() ด้วยเลข template จาก workflow_route.email_id แล้ว lib เขียนแถวให้เอง |

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
-- ⚠️ ไม่ INSERT ตาราง workflow เอง — เรียก @srm/glb-workflow (schema sps_store) ให้ library เขียนให้
--    initialize(versionId=:sbpgiVersionId, referenceId=:referenceId, userId=:empId)
--    addPreApprover(versionId, referenceId, stateId=:section06, approver, seq=1)
--    library เขียน sps_store.workflow_transaction / workflow_approver / workflow_history ให้เอง
-- referenceId = compensation_documents.id (surrogate · DP-1 ปิดแล้ว 2026-08-17)
-- ⚠️ sps_store.workflow_transaction ไม่มี PK/index → กันซ้ำต้องทำที่ application (DP-2)
--    ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
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
| 3 | validate require field ของแถวที่ผู้ใช้เพิ่มเอง: คู่แข่ง = รหัสแบรนด์จาก master /competitors (01–11) + วันที่เปิดกระทบ · ปัจจัย = รหัสจาก master /factors + วันที่เริ่มต้น (วันที่สิ้นสุดถ้ามีต้อง ≥ วันที่เริ่มต้น) |
| 4 | ส่งอาร์เรย์มา = ชุดข้อมูลเต็มของส่วนนั้น — รายการที่หายไปจากอาร์เรย์ถือว่าถูกลบ (รองรับปุ่ม "ลบที่เลือก") · ฝั่ง FE เรียกเส้นนี้ทันทีเมื่อกดบันทึกใน modal หรือยืนยันลบ ไม่มีปุ่มบันทึกระดับการ์ดแล้ว |
| 5 | บันทึกและคืนเอกสารล่าสุด |

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
  "competitors": [ { "id": 12, "impactDate": "2023-10-10" } ]   // id 13 หายไป = ลบ
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
| 400 — "กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ" (verbatim จาก SRS §10) |
| 400 — "กรุณาเลือกปัจจัยอื่นๆ ที่ท่านต้องการ" (ไม่ได้อยู่ใน SRS — เราตั้งเองให้ล้อกับข้อความคู่แข่ง · รอ BA ยืนยัน) |
| 400 — "วันที่สิ้นสุดต้องมีค่าเท่ากับหรือมากกว่าวันที่เริ่มต้น" (SRS §11 ระบุกฎ แต่ไม่ได้ให้ข้อความ · รอ BA ยืนยัน) |

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

ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน — หัวใจ workflow 5 ขั้น · วงเงิน เกณฑ์เดียว 100,000 (SDD GI 24/02/2026)

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
| 1 | ตรวจว่าผู้ใช้เป็น approver ของ state ปัจจุบันใน @srm/glb-workflow schema sps_store (getTransaction / getPermissionEvents ) |
| 2 | validate เลือกผลแล้ว — ไม่งั้น 422 ข้อความ SRS ตรงตัว |
| 3 | คำนวณขั้นถัดไปตามตารางเส้นทาง (ตารางเส้นทาง workflow · SDD GI): 06 ไม่ชดเชย/หยุดชดเชย → เสร็จสิ้น · 01/02 เห็นควรไม่ชดเชย → เสร็จสิ้นทันที (ไม่อนุมัติในเดือนนั้น) · 02 ชดเชย < 100,000 → เสร็จสิ้น (จบที่ GM) · ≥ 100,000 → 03 → จบ  · ตัดขั้นบัญชี 04/05 (SDD v7.5) · ทุกขั้นมีเส้นส่งกลับ |
| 4 | insert consideration_logs + ปิด task เดิม เปิด task ใหม่ · กรณี 06 เห็นควรไม่ชดเชย ระบบตั้งงานเดือนถัดไปให้เจ้าของงานคนเดิม (SDD GI) |
| 5 | SBPGI เรียก sendEmail() แจ้งผู้อนุมัติถัดไป ด้วยเลข template จาก workflow_route.email_id (นอก transaction) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| sps_store.workflow_transaction / workflow_history / workflow_approver | R (เขียนผ่าน lib) | 🔴 ห้าม INSERT/UPDATE ตรง — eventWorkflow() + addPreApprover() ของ engine เดิม (schema sps_store) — เดิน state + บันทึก history + ตั้ง approver ขั้นถัดไป · API 8 ตัวตามชีต Detail ของ LLDD lib (ปิด 2026-08-14) |
| compensation_documents | W | อัปเดต Status + CurSection |
| consideration_logs | W | บันทึกผลพิจารณา |
| email_template (SBP เดิม) | R | template — อ่านอย่างเดียว ไม่แก้ของระบบเดิม |
| email_sent (SBP เดิม) | W (โดย email-lib) | ปิด DP-5 · 2026-08-14 — SBPGI เรียก sendEmail() ด้วยเลข template จาก workflow_route.email_id แล้ว lib เขียนแถวให้เอง (คอลัมน์ผู้ส่ง = send_by) |

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
-- ⚠️ ไม่ UPDATE ตาราง workflow เอง — เดิน state ผ่าน @srm/glb-workflow (schema sps_store)
--    eventWorkflow({versionId, referenceId, event, eventParam:{amount}, remark, userId})
--    library ปิดงานขั้นเดิม เขียน sps_store.workflow_history และเปิด approver ขั้นถัดไปให้เอง
-- referenceId = compensation_documents.id (surrogate · DP-1 ปิดแล้ว 2026-08-17)

INSERT INTO consideration_logs (doc_no, section_code, consider_by, result, detail, action_datetime)
VALUES (:docNo, :curSection, :empId, :result, :comment, :now);

-- คำนวณขั้นถัดไป (วงเงิน เกณฑ์เดียว 100,000 · SDD GI) → เปิดงานใหม่ + อัปเดตสถานะเอกสารแบบ optimistic lock
UPDATE compensation_documents SET status_code = :nextStatus, current_section_code = :nextSection, version_no = version_no + 1, updated_at = :now, updated_by = :empId
WHERE doc_no = :docNo AND version_no = :versionNo;
-- งานขั้นถัดไปเปิดโดย engine (addPreApprover) ไม่ใช่ INSERT ของ SBPGI

-- ✅ ปิด DP-5 (แก้มติ 2026-08-14): workflow ให้ "เลข template" · SBPGI เรียก lib ส่งเอง (ไม่มีตาราง status_email_rules)
-- 1) เอาเลข template ของ route ที่เพิ่งเดิน (ถ้า NULL = ไม่ต้องส่งเมล)
-- ⚠️ ต้องระบุ to_state_id ด้วย! state 02 มี 2 route ตามวงเงิน (< 100,000 จบ · ≥ 100,000 ไป 03)
--    ถ้าใช้แค่ (from_state_id, event) แล้ว ORDER BY seq LIMIT 1 จะได้ template ผิดเสมอเมื่อเข้าเงื่อนไขที่สอง
--    :prevStateId เก็บจาก getTransaction() "ก่อน" เรียก eventWorkflow · :nextStateId อ่านจาก getTransaction() "หลัง" สำเร็จ
SELECT r.email_id
FROM sps_store.workflow_route r
WHERE r.version_id = :versionId
  AND r.from_state_id = :prevStateId
  AND r.event = :event
  AND r.to_state_id = :nextStateId;

-- 2) หาอีเมลผู้อนุมัติลำดับถัดไปที่ engine resolve ให้แล้ว
SELECT string_agg(DISTINCT u.email, ',') AS mail_to
FROM sps_store.workflow_approver a
JOIN sps_store.business_user u ON u.user_id = a.current_approver
WHERE a.transaction_id = :transactionId AND a.state_id = :nextStateId AND u.email IS NOT NULL;

-- 2b) ผู้รับ CC — ระบบเดิมมีกลไกอยู่แล้ว (fml_email_account.template_id)
SELECT string_agg(email, ',') AS mail_cc
FROM fml_email_account
WHERE template_id = :emailId;

-- 3) เรียก lib "นอก transaction" (อีเมลล้มต้องไม่ rollback การอนุมัติ · lib ไม่ retry ให้)
--    emailService.sendEmail({ emailId, mailTo, mailCc, param:{docNo, storeName, amount}, userId })
--    lib อ่าน email_template แล้ว INSERT email_sent (is_sent 'Y'/'N' + error) ให้เอง — return แค่ Success/Fail

-- 4) รายงานตามเก็บเมลที่ส่งไม่สำเร็จ (⚠️ คอลัมน์จริงคือ send_by ไม่ใช่ sent_by)
SELECT email_sent_id, email_id, mail_to, mail_cc, is_sent, error, sent_date, send_by
FROM email_sent
WHERE is_sent = 'N' AND sent_date >= :since
ORDER BY sent_date DESC;
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
| 2 | [ยังไม่ตัดสิน — DP-7] consideration_logs จะเป็น timeline เต็มของ SBPGI หรือเป็นตารางส่วนขยายบน sps_store.workflow_history ของ engine (engine เก็บ state transition แต่ไม่มี decision code / ไฟล์แนบ / ความเห็น) — กระทบทั้ง DDL และรูปแบบ response ของเส้นนี้ · ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4 |

| DB Object | R/W | Usage |
| --- | --- | --- |
| consideration_logs | R | ประวัติครบทุกขั้น — [DP-7 ยังไม่ตัดสิน] |
| sps_store.workflow_history | R | timeline การเดิน state ของ engine (ทางเลือก B ของ DP-7) — คีย์ที่ใช้ค้น = compensation_documents.id (DP-1 ปิดแล้ว) |

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
-- ⚠️ DP-7 ยังไม่ตัดสิน: consideration_logs เป็น timeline เต็ม หรือเป็นตารางส่วนขยายบน sps_store.workflow_history
--    ถ้าเลือกทางเลือก B ต้อง join getHistory() ของ engine เข้ามาด้วย (DP-1 กำหนดคีย์ที่ใช้ค้น)
--    ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
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
| (object storage S3 — ไม่ใช่ตาราง) | R | binary file ผ่าน service ของระบบ SBP เดิม |

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

SQL Reference

```sql
-- รวมไฟล์แนบทั้งหมดเป็น .zip — ตรวจสิทธิ์อ่านเอกสารก่อน แล้วรวมเฉพาะไฟล์ที่ scan ผ่าน
-- ไม่มีไฟล์ที่ดาวน์โหลดได้เลย -> 404 (ไม่คืน zip เปล่า)
SELECT attach_id, bucket, object_key, file_name, mime_type, file_size
FROM document_attachments
WHERE doc_no = :docNo AND scan_status = 'CLEAN'
ORDER BY section_code, attach_id;
```

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
| 1 | GET | /api/v1/document-statuses | รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report) |
| 2 | GET | /api/v1/workflow-sections | รายการ Section 5 ขั้น + วงเงินอนุมัติต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE แสดงวงเงินจากข้อมูล ไม่ hardcode |

#### 6.2.1 GET /api/v1/document-statuses

รายการสถานะเอกสารทั้งหมด — เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report)

| Item | Detail |
| --- | --- |
| Global No. | 12 |
| Method | GET |
| Path | /api/v1/document-statuses |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · 3.1.3 / 3.1.7 |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sps_store.workflow_status ของ @srm/glb-workflow เรียงตามลำดับ workflow (ตาราง document_statuses ของ SBPGI ถูกตัดไปแล้ว 2026-08-06) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| sps_store.workflow_status | R | สถานะเอกสาร (06/08/01/02/03/99; 99=เสร็จสิ้น) — ของ engine กลาง ไม่ใช่ตารางของ SBPGI |

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
-- ตาราง document_statuses ของ SBPGI ถูกตัดแล้ว — อ่านจาก workflow_status ของ engine กลาง
SELECT status_id AS status_code, status_name, seq AS sort_order
FROM sps_store.workflow_status
WHERE version_id = :sbpgiVersionId
ORDER BY seq;
```

#### 6.2.2 GET /api/v1/workflow-sections

รายการ Section 5 ขั้น + วงเงินอนุมัติต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE แสดงวงเงินจากข้อมูล ไม่ hardcode

| Item | Detail |
| --- | --- |
| Global No. | 13 |
| Method | GET |
| Path | /api/v1/workflow-sections |
| Group | ข้อมูลอ้างอิง (Lookup / Reference) |
| Access / Role | ทุก role |
| Requirement Tag | K2 · master section |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sps_store.workflow_state ของ engine เรียงตามลำดับ 06→08→01→02→03 (ตาราง workflow_sections ของ SBPGI ถูกตัดแล้ว) |
| 2 | คืน approve_limit_amount ต่อขั้น (= SectionLimitCost ของ K2 เดิม · ขั้น 02 = 100,000 · ขั้น 03 = null ไม่มีเพดาน · มติ 2026-08-18) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| workflow_state (@srm/glb-workflow · sps_store) | R | ขั้นตอน 06/08/01/02/03 — ตาราง workflow_sections ของ SBPGI ถูกตัดแล้ว |
| workflow_route (@srm/glb-workflow · sps_store) | R | ลำดับขั้น (seq) — workflow_state ไม่มีคอลัมน์ลำดับ |
| common_code (SBP เดิม) | R | approve_limit_amount ต่อขั้น (code_type = SBPGI_APPROVE_LIMIT) |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
{
  "items": [
    { "sectionCode": "06", "sectionName": "ฝ่าย SBP DSA", "approveLimitAmount": null },
    { "sectionCode": "02", "sectionName": "GM ส่งเสริมธุรกิจ SBP", "approveLimitAmount": 100000.00 },
    { "sectionCode": "03", "sectionName": "ผู้บริหารสำนักบริหาร SBP", "approveLimitAmount": null }
  ]
}
```

| Error / Condition |
| --- |
| 401 |

SQL Reference

```sql
-- ตาราง workflow_sections ของ SBPGI ถูกตัดแล้ว — อ่าน state จาก engine กลาง และวงเงินจาก common_code ของระบบเดิม
-- (approve_limit_amount = SectionLimitCost ของ K2 เดิม · เกณฑ์เดียว 100,000 ตามมติ 2026-08-18 — เป็น data ไม่ hardcode · ขั้น 03 เป็น null = ไม่มีเพดาน)
-- ⚠️ sps_store.workflow_state ไม่มีคอลัมน์ลำดับ (มีแค่ version_id · state_id · state_name · create_date)
--    ลำดับขั้นต้องเอาจาก workflow_route.seq · วงเงินจับคู่ด้วย common_code.code_value (ไม่มี code_id)
SELECT s.state_id AS section_code, s.state_name AS section_name,
       MIN(r.seq) AS sort_order,
       CAST(c.other_value AS NUMERIC) AS approve_limit_amount
FROM sps_store.workflow_state s
LEFT JOIN sps_store.workflow_route r ON r.version_id = s.version_id AND r.from_state_id = s.state_id
LEFT JOIN common_code c ON c.code_type = 'SBPGI_APPROVE_LIMIT' AND c.code_value = s.state_id
WHERE s.version_id = :sbpgiVersionId
GROUP BY s.state_id, s.state_name, c.other_value
ORDER BY sort_order;
```

### 6.3 Master Data

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/competitors | master แบรนด์ร้านคู่แข่ง 11 รายการ (รหัส 01–11 · ชื่อไทย+อังกฤษ) — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html) · จัดการที่หน้า k2-competitors.html |
| 2 | POST | /api/v1/competitors | เพิ่มแบรนด์ร้านคู่แข่งใน master (หน้า k2-competitors.html) — เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม |
| 3 | PUT | /api/v1/competitors/{code} | แก้ไขชื่อไทย/อังกฤษ/รายละเอียดของแบรนด์คู่แข่ง — แก้รหัสไม่ได้ |
| 4 | DELETE | /api/v1/competitors/{code} | ลบแบรนด์คู่แข่งออกจาก master — ห้ามลบถ้ายังถูกอ้างในเอกสาร |
| 5 | GET | /api/v1/factors | รายการปัจจัยภายนอก (external_factors) |
| 6 | POST | /api/v1/factors | เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS) |
| 7 | PUT | /api/v1/factors/{code} | แก้ไขปัจจัยภายนอก |
| 8 | DELETE | /api/v1/factors/{code} | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) |

#### 6.3.1 GET /api/v1/competitors

master แบรนด์ร้านคู่แข่ง 11 รายการ (รหัส 01–11 · ชื่อไทย+อังกฤษ) — dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (k2-document.html) · จัดการที่หน้า k2-competitors.html

| Item | Detail |
| --- | --- |
| Global No. | 14 |
| Method | GET |
| Path | /api/v1/competitors |
| Group | Master Data |
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
-- master แบรนด์คู่แข่ง 11 รายการ (รหัส 01-11) · ระบบเดิมเก็บชื่อไทยและอังกฤษ
SELECT competitor_code, name_th, name_en, remark, is_active
FROM competitors
WHERE (:q IS NULL OR name_th LIKE :q OR name_en LIKE :q)
ORDER BY competitor_code;
```

#### 6.3.2 POST /api/v1/competitors

เพิ่มแบรนด์ร้านคู่แข่งใน master (หน้า k2-competitors.html) — เพิ่ม 2026-08-06 ตามหน้าจอ K2 เดิม

| Item | Detail |
| --- | --- |
| Global No. | 15 |
| Method | POST |
| Path | /api/v1/competitors |
| Group | Master Data |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | validate code / nameTh / nameEn ครบทั้งสามช่อง |
| 2 | ตรวจรหัสซ้ำ → 409 |
| 3 | insert competitors |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | แถวใหม่ (code · name_th · name_en · remark) |

#### Request / Query / Header

```json
{
  "code": "12",
  "nameTh": "ร้านคู่แข่งรายใหม่",
  "nameEn": "New Competitor",
  "remark": ""
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

SQL Reference

```sql
-- competitor_code ห้ามซ้ำ (ไม่งั้น 409) · ชื่อไทยและอังกฤษบังคับทั้งคู่
INSERT INTO competitors (competitor_code, name_th, name_en, remark, is_active)
VALUES (:code, :nameTh, :nameEn, :remark, TRUE);
```

#### 6.3.3 PUT /api/v1/competitors/{code}

แก้ไขชื่อไทย/อังกฤษ/รายละเอียดของแบรนด์คู่แข่ง — แก้รหัสไม่ได้

| Item | Detail |
| --- | --- |
| Global No. | 16 |
| Method | PUT |
| Path | /api/v1/competitors/{code} |
| Group | Master Data |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | แก้ได้เฉพาะ nameTh / nameEn / remark |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | ค่าใหม่ |

#### Request / Query / Header

```json
{
  "nameEn": "Lawson 108"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบรหัส |
| 422 — ข้อมูลบังคับไม่ครบ |

SQL Reference

```sql
-- ห้ามแก้ competitor_code (เป็น PK และถูกอ้างจาก document_competitors)
UPDATE competitors
   SET name_th = :nameTh, name_en = :nameEn, remark = :remark, is_active = :isActive,
       updated_at = CURRENT_TIMESTAMP
 WHERE competitor_code = :code;
```

#### 6.3.4 DELETE /api/v1/competitors/{code}

ลบแบรนด์คู่แข่งออกจาก master — ห้ามลบถ้ายังถูกอ้างในเอกสาร

| Item | Detail |
| --- | --- |
| Global No. | 17 |
| Method | DELETE |
| Path | /api/v1/competitors/{code} |
| Group | Master Data |
| Access / Role | Admin / ผู้ดูแล master |
| Requirement Tag | K2 · master |

| Step | Flow |
| --- | --- |
| 1 | ตรวจว่าไม่มี document_competitors อ้างรหัสนี้ → ไม่งั้น 409 |
| 2 | ลบแถว |

| DB Object | R/W | Usage |
| --- | --- | --- |
| competitors | W | ลบแถว |
| document_competitors | R | ตรวจการอ้างอิง |

#### Request / Query / Header

```json
(ไม่มี body)
```

#### Response

```json
204 No Content
```

| Error / Condition |
| --- |
| 409 — ยังถูกอ้างในเอกสาร |
| 404 |

SQL Reference

```sql
-- ตรวจไม่ถูกอ้างในเอกสารก่อนลบ (ไม่งั้น 409)
SELECT 1 FROM document_competitors WHERE competitor_code = :code;

DELETE FROM competitors WHERE competitor_code = :code;
```

#### 6.3.5 GET /api/v1/factors

รายการปัจจัยภายนอก (external_factors)

| Item | Detail |
| --- | --- |
| Global No. | 18 |
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

#### 6.3.6 POST /api/v1/factors

เพิ่มปัจจัยภายนอก — รหัสห้ามซ้ำ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 19 |
| Method | POST |
| Path | /api/v1/factors |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจ factor_code ไม่ซ้ำ |
| 2 | insert external_factors |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | แถวใหม่ |

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
```

#### 6.3.7 PUT /api/v1/factors/{code}

แก้ไขปัจจัยภายนอก

| Item | Detail |
| --- | --- |
| Global No. | 20 |
| Method | PUT |
| Path | /api/v1/factors/{code} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | แก้ได้เฉพาะชื่อปัจจัยและรายละเอียด |
| 2 | update external_factors |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | แก้ไข |

#### Request / Query / Header

```json
{
  "factorName": "คู่แข่งจัดโปรโมชันใหญ่"
}
```

#### Response

```json
200 OK
```

| Error / Condition |
| --- |
| 404 — ไม่พบรหัสปัจจัย |

SQL Reference

```sql
-- ไม่มี audit/เหตุผลแล้ว (ยกเลิก audit_logs 2026-08-07)
UPDATE external_factors SET factor_name = :factorName, factor_remark = :factorRemark
WHERE factor_code = :code;
```

#### 6.3.8 DELETE /api/v1/factors/{code}

ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด)

| Item | Detail |
| --- | --- |
| Global No. | 21 |
| Method | DELETE |
| Path | /api/v1/factors/{code} |
| Group | Master Data |
| Access / Role | 03 User Admin |
| Requirement Tag | K2 · 3.1.9 |

| Step | Flow |
| --- | --- |
| 1 | ตรวจไม่ถูกอ้างใน document_external_factors |
| 2 | ลบแถว |

| DB Object | R/W | Usage |
| --- | --- | --- |
| external_factors | W | ลบแถว |
| document_external_factors | R | ตรวจการใช้งาน |

#### Request / Query / Header

```json
(ไม่มี body)
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
```

### 6.4 รายงาน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/reports/status-summary | รายงานตรวจสอบประกันรายได้ (SBP Mall) — ค้นหาข้อมูล · filter 7 ตัวและผลลัพธ์ 14 คอลัมน์ ตาม SDD สไลด์ 60 · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) |
| 2 | GET | /api/v1/reports/status-summary/export | Export Excel — ส่งออกผลการค้นหา 14 คอลัมน์เป็น Excel ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา |

#### 6.4.1 GET /api/v1/reports/status-summary

รายงานตรวจสอบประกันรายได้ (SBP Mall) — ค้นหาข้อมูล · filter 7 ตัวและผลลัพธ์ 14 คอลัมน์ ตาม SDD สไลด์ 60 · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS)

| Item | Detail |
| --- | --- |
| Global No. | 22 |
| Method | GET |
| Path | /api/v1/reports/status-summary |
| Group | รายงาน |
| Access / Role | บัญชี / 06 Report Admin |
| Requirement Tag | K2 · 3.1.7 + SDD v7.5 |

| Step | Flow |
| --- | --- |
| 1 | validate ปี (ไม่ระบุ → 400) และ status (ไม่ระบุ → 400 · Required Field ตาม SDD) |
| 2 | validate คู่รหัสร้าน: ระบุ impactedStoreCode แล้วต้องระบุ newStoreCode ด้วย (และกลับกัน) ไม่งั้น 400 |
| 3 | ถ้า status = เสร็จสิ้นดำเนินการ ต้องมี periodStatementFrom/To (ค.ศ.) ไม่งั้น 400 |
| 4 | query compensation_documents + compensation_histories ตามเงื่อนไข (status 6 ค่า · region 13 รหัส + ภาคใหม่อัตโนมัติ · storeType 7 ค่า `A B C D E PTT บริษัท` (BranchTypeProfile.BranchTypeFGIName · ห้าม hardcode) · รหัสถูกกระทบ/เปิดกระทบ · ช่วง Period Statement) |
| 5 | กรอง result (APPROVE/REJECT) จากผลพิจารณาล่าสุดใน consideration_logs — Radio "ประกันรายได้/ไม่ประกันรายได้" (ไม่บังคับ) |
| 6 | คืน 14 คอลัมน์ตาม SDD แบบแบ่งหน้า (ร้านถูกกระทบ 4 · เดือน/ปีที่ถูกกระทบ · Period Statement · ร้านเปิดกระทบ 4 · ยอดเงินชดเชย · ครั้งที่ · วันที่สร้าง · เลขที่เอกสาร) |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents | R | สถานะเอกสาร |
| compensation_histories | R | ยอด/งวดชดเชย |
| impacted_stores | R | ข้อมูลร้าน |
| consideration_logs | R | ผลพิจารณาล่าสุด (กรองประกัน/ไม่ประกัน) |

#### Request / Query / Header

```json
Query: ?year=2026&status=เสร็จสิ้นดำเนินการ&periodStatementFrom=2026-06-01&periodStatementTo=2026-06-30
       &storeType=A&storeType=B&region=RSU&region=BW&impactedStoreCode=00788&newStoreCode=00990&result=APPROVE&page=1
(status บังคับ · result = APPROVE | REJECT — ประกันรายได้ / ไม่ประกันรายได้ · ไม่บังคับ)
```

#### Response

```json
{
  "page": 1, "total": 212,
  "items": [{
    "impactedStoreCode": "00788", "impactedStoreName": "รัตนอุทิศ ซ.13", "impactedRegion": "RSU", "impactedStoreType": "B",
    "impactMonth": "05/2026", "periodStatement": "07/06/2026",
    "newStoreCode": "00990", "newStoreName": "เซเว่นฯ รัตนาธิเบศร์ 12", "newRegion": "RSU", "newStoreType": "A",
    "compensateAmount": 48200.00, "round": 1, "createdDate": "12/06/2026", "docNo": "2026/00123"
  }]
}
```

| Error / Condition |
| --- |
| 400 — กรุณาระบุปีที่ต้องการค้นหา |
| 400 — กรุณาเลือกสถานะก่อนค้นหาข้อมูล |
| 400 — กรณีระบุรหัสร้านถูกกระทบ ต้องระบุรหัสร้านเปิดกระทบด้วย |

SQL Reference

```sql
-- 14 คอลัมน์ตาม SDD สไลด์ 60 ; ต้องระบุ :year และ :status เสมอ ; เอาเฉพาะเอกสารที่มีเลขที่แล้ว
-- ⚠️ ตาราง stores ของ SBPGI ถูกตัด 2026-08-06 — ใช้ store ของระบบ SBP เดิม (sps_store 19,402 แถว): คีย์ store_id · ภาค zone_cd
SELECT si.store_id   AS impacted_store_code, si.store_name   AS impacted_store_name,
       si.zone_cd  AS impacted_region,     si.store_type   AS impacted_store_type,
       pr.impact_month, pr.impact_year, d.statement_date,   -- statement_date = ค.ศ. (คอลัมน์ใหม่คู่กับ statement_id)
       ns.store_id   AS new_store_code,      ns.store_name  AS new_store_name,
       ns.zone_cd  AS new_region,          ns.store_type  AS new_store_type,
       h.compensate_amount, d.loop_no AS round_no, d.created_at AS created_date, d.doc_no
FROM compensation_documents d
JOIN fgi_impact_processes pr ON pr.id = d.impact_process_id
JOIN store si                ON si.store_id = d.impacted_store_code
LEFT JOIN compensation_histories h ON h.ref_doc_no = d.doc_no
LEFT JOIN document_new_stores dns  ON dns.doc_no = d.doc_no
LEFT JOIN store ns                 ON ns.store_id = dns.new_store_code
LEFT JOIN LATERAL (
  SELECT result_category FROM consideration_logs
  WHERE doc_no = d.doc_no ORDER BY action_datetime DESC LIMIT 1
) cl ON TRUE
WHERE d.year = :year
  AND d.status_code = :status                                   -- Drop-down บังคับ (SDD สไลด์ 60)
  AND (:impactedStoreCode IS NULL OR d.impacted_store_code = :impactedStoreCode)
  AND (:newStoreCode      IS NULL OR dns.new_store_code    = :newStoreCode)
  AND (:psFrom IS NULL OR d.statement_date BETWEEN :psFrom AND :psTo)  -- ค.ศ. ; บังคับเมื่อ status = เสร็จสิ้นดำเนินการ
  AND (:storeTypes IS NULL OR si.store_type  = ANY(:storeTypes))       -- 7 ค่า `A B C D E PTT บริษัท` (BranchTypeProfile.BranchTypeFGIName · ห้าม hardcode)
  AND (:regions    IS NULL OR si.zone_cd = ANY(:regions))          -- 13 ภาค + ภาคใหม่อัตโนมัติ
  AND (:result     IS NULL OR cl.result_category = :result)            -- APPROVE / REJECT (ไม่บังคับ)
ORDER BY d.doc_no
LIMIT :size OFFSET :offset;
```

#### 6.4.2 GET /api/v1/reports/status-summary/export

Export Excel — ส่งออกผลการค้นหา 14 คอลัมน์เป็น Excel ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา

| Item | Detail |
| --- | --- |
| Global No. | 23 |
| Method | GET |
| Path | /api/v1/reports/status-summary/export |
| Group | รายงาน |
| Access / Role | 04 / 06 Report Admin |
| Requirement Tag | K2 · 3.1.7 |

| Step | Flow |
| --- | --- |
| 1 | เงื่อนไขเดียวกับ status-summary (รวม validate status และคู่รหัสร้าน) |
| 2 | สร้างไฟล์ Excel 14 คอลัมน์ตาม SDD สไลด์ 60 ให้ทีมบัญชีนำไปกระทบ SAP |

| DB Object | R/W | Usage |
| --- | --- | --- |
| compensation_documents / compensation_histories | R | ข้อมูลชุดเดียวกับรายงาน |

#### Request / Query / Header

```json
Query: ?year=2026&status=เสร็จสิ้นดำเนินการ&region=RSU&storeType=A&result=APPROVE
(เงื่อนไขชุดเดียวกับเส้นค้นหา รวม result ประกันรายได้/ไม่ประกันรายได้)
```

#### Response

```json
200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="insurance-verification-2026.xlsx"
```

| Error / Condition |
| --- |
| 400 — ไม่ระบุปี |

SQL Reference

```sql
-- เงื่อนไขเดียวกับ status-summary ทุกตัว แล้ว stream 14 คอลัมน์เดิมออกเป็นไฟล์ .xlsx (Export Excel)
-- ใช้ SELECT ชุดเดียวกับ GET /reports/status-summary แต่ไม่ตัดหน้า (ไม่มี LIMIT/OFFSET)
ORDER BY d.doc_no;
```

### 6.5 Workflow ภายใน

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | POST | /api/v1/workflows/instances | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม |
| 2 | GET | /api/v1/workflows/instances/{id} | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) |
| 3 | GET | /api/v1/workflows/summary | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น |

#### 6.5.1 POST /api/v1/workflows/instances

เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate — เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม

| Item | Detail |
| --- | --- |
| Global No. | 24 |
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
| 5 | ผ่าน: ใช้ compensation_documents ที่ Job 8 สร้างแล้ว + initializeWorkflow/addPreApprover ขั้น 06 ผ่าน @srm/glb-workflow แล้วตั้ง workflow_generation_status=Y |
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
  "instanceId": "WF-2026-00124",
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
       -- ⚠️ store ของระบบเดิมไม่มี juristic_name — นิติบุคคลอยู่คนละตาราง (fr_store / franchisee / juristic)
       --    ชื่อตาราง/คีย์ยังไม่ยืนยัน ต้องถามทีมเจ้าของก่อนเขียนโค้ด
       ij.juristic_name AS impacted_store_juristic_name, nj.juristic_name AS new_store_juristic_name,
       ss.growth_rate_diff, ss.sales_status, ns.store_type, pair.distance_km, impacted.zone_cd
FROM fgi_impact_processes p
JOIN impacted_stores ist ON ist.store_code = p.impacted_store_code
JOIN store impacted ON impacted.store_id = p.impacted_store_code
JOIN fgi_impact_stores pair ON pair.impact_process_id = p.id
JOIN store ns ON ns.store_id = pair.new_store_code
-- นิติบุคคลต้องผ่าน fr_store: store.store_id -> fr_store.juristic_id -> juristic.juristic_name
LEFT JOIN fr_store ifs ON ifs.store_id = impacted.store_id
LEFT JOIN juristic ij  ON ij.juristic_id = ifs.juristic_id
LEFT JOIN fr_store nfs ON nfs.store_id = ns.store_id
LEFT JOIN juristic nj  ON nj.juristic_id = nfs.juristic_id
LEFT JOIN fgi_impact_sales_summaries ss ON ss.impact_process_id = p.id
WHERE p.id = :impactProcessId FOR UPDATE OF p;

-- fail ถาวร (branch/distance over/missing DV/same juristic/growth > -10) → N; เฉพาะ distance/juristic/growth NULL หรือ sales_status ยังไม่พร้อมจึงคง W
UPDATE fgi_impact_processes SET workflow_generation_status = :flagN
WHERE id = :impactProcessId AND workflow_generation_status = :flagW AND :gateDecision = :flagN;

-- ผ่าน gate → ใช้เอกสารที่ Job 8 สร้างแล้ว เปิด instance + งานแรกผ่าน @srm/glb-workflow แล้วตั้ง Y ใน transaction เดียว
-- ⚠️ ไม่ INSERT ตาราง workflow เอง (workflow_instances / workflow_tasks ถูกตัดออกจากโครง 19 ตารางแล้ว)
--    initialize(versionId=:sbpgiVersionId, referenceId=:referenceId, userId=:serviceActor)
--    addPreApprover(versionId, referenceId, stateId=:section06, approver, seq=1)
-- referenceId = compensation_documents.id (DP-1 ปิดแล้ว) · ไม่มี UNIQUE กันซ้ำจริงบน
--    sps_store.workflow_transaction (ไม่มี PK/index · 19,283 แถว) → กันซ้ำที่ application (DP-2)
--    ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
SELECT d.doc_no FROM compensation_documents d
WHERE d.impact_process_id = :impactProcessId AND :gateDecision = :flagY;
UPDATE fgi_impact_processes SET workflow_generation_status = :flagY
WHERE id = :impactProcessId AND workflow_generation_status = :flagW AND :gateDecision = :flagY;
```

#### 6.5.2 GET /api/v1/workflows/instances/{id}

สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม)

| Item | Detail |
| --- | --- |
| Global No. | 25 |
| Method | GET |
| Path | /api/v1/workflows/instances/{id} |
| Group | Workflow ภายใน |
| Access / Role | 01 Admin / เจ้าของงาน |
| Requirement Tag | ใหม่ |

| Step | Flow |
| --- | --- |
| 1 | อ่าน sps_store.workflow_transaction (instance ปัจจุบัน) + workflow_approver (ผู้รับผิดชอบขั้นปัจจุบัน) ของ @srm/glb-workflow แล้ว join เอกสารของ SBPGI |
| 2 | คีย์ที่ใช้ค้น = compensation_documents.id (DP-1 ปิดแล้ว) · [ยังไม่ตัดสิน] DP-2 ตารางนี้ไม่มี PK/index (19,283 แถว) จึงเป็น seq-scan — ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4 |

| DB Object | R/W | Usage |
| --- | --- | --- |
| sps_store.workflow_transaction | R | สถานะ instance ปัจจุบัน (@srm/glb-workflow) — ⚠️ ไม่มี PK/index · DP-2 |
| sps_store.workflow_approver | R | ผู้รับผิดชอบ/งานขั้นปัจจุบัน |
| sps_store.workflow_history | R | timeline การเดิน state |
| compensation_documents | R | เอกสารที่ผูกกับ instance |

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
-- ✅ DP-1 ปิดแล้ว: referenceId = compensation_documents.id (surrogate) · ⚠️ DP-2 (sps_store.workflow_transaction ไม่มี PK/index · 19,283 แถว → seq-scan) ยังไม่ตัดสิน
--    ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
SELECT w.transaction_id, w.reference_id, w.current_state_id, w.current_status_id, w.current_approver,
       a.state_id AS pending_state_id, a.approver_id, a.approve_seq
FROM sps_store.workflow_transaction w
LEFT JOIN sps_store.workflow_approver a ON a.transaction_id = w.transaction_id AND a.state_id = w.current_state_id
WHERE w.transaction_id = :id AND w.version_id = :sbpgiVersionId;

-- เอกสารที่ผูกกับ instance (join ด้วยcompensation_documents.id (DP-1 ปิดแล้ว))
SELECT doc_no, status_code, current_section_code FROM compensation_documents WHERE doc_no = :referenceId;
```

#### 6.5.3 GET /api/v1/workflows/summary

ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น

| Item | Detail |
| --- | --- |
| Global No. | 26 |
| Method | GET |
| Path | /api/v1/workflows/summary |
| Group | Workflow ภายใน |
| Access / Role | 01 Admin |
| Requirement Tag | FGI/FCS · Monitoring 7.4 |

| Step | Flow |
| --- | --- |
| 1 | aggregate จาก fgi_impact_processes + sps_store.workflow_transaction / workflow_approver ของ @srm/glb-workflow |
| 2 | [ยังไม่ตัดสิน] DP-2 — ไม่มี index บน workflow_transaction จึงต้องประเมินต้นทุน aggregate ก่อนเปิดใช้จริง |

| DB Object | R/W | Usage |
| --- | --- | --- |
| fgi_impact_processes | R | นับ W/Y/N |
| sps_store.workflow_approver | R | งานค้างต่อ section (@srm/glb-workflow) |
| sps_store.workflow_transaction | R | นับ instance ที่ยังไม่จบ — ⚠️ ไม่มี PK/index · DP-2 |

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

-- ✅ DP-1 ปิดแล้ว: referenceId = compensation_documents.id (surrogate) · ⚠️ DP-2 (sps_store.workflow_transaction ไม่มี PK/index · 19,283 แถว → seq-scan) ยังไม่ตัดสิน
--    ดู SBP/SBPGI-vs-existing-system.md หัวข้อ 4
SELECT w.current_state_id AS section_code, COUNT(*) AS open_tasks
FROM sps_store.workflow_transaction w
WHERE w.version_id = :sbpgiVersionId AND w.current_status_id <> :statusDone
GROUP BY w.current_state_id;
```

### 6.6 Interface & Dashboard

| Endpoint | Method | Path | Summary |
| --- | --- | --- | --- |
| 1 | GET | /api/v1/interfaces/tracking | สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) |
| 2 | POST | /api/v1/interfaces/sta/ack | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว |
| 3 | GET | /api/v1/interfaces/pending-ack | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน |

#### 6.6.1 GET /api/v1/interfaces/tracking

สถานะการรับ–ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA)

| Item | Detail |
| --- | --- |
| Global No. | 27 |
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

#### 6.6.2 POST /api/v1/interfaces/sta/ack

Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง — แทนการรออัปเดต return_code ฝั่งเดียว

| Item | Detail |
| --- | --- |
| Global No. | 28 |
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

#### 6.6.3 GET /api/v1/interfaces/pending-ack

รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) — ใช้ทั้งหน้า dashboard และอีเมลเตือน

| Item | Detail |
| --- | --- |
| Global No. | 29 |
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

## 7. API Test Checklist

| Test group | Required cases |
| --- | --- |
| Common contract | 401, 403, 404, 409, 422, pagination envelope, error `{code,message}` |
| Document workflow | create duplicate, submit no result, invalid result for role profile, current task conflict, threshold ≥ 100,000 -> AVP route (SDD GI) |
| Attachment | file >5MB, unsupported type, AV blocked, download not owner, download clean file |
| Report | year required, result required, CSV export with same filter as preview |
| Job admin | manual run when disabled, manual run while RUNNING, editable params only, run histories |
| Security | service token only endpoints, no objectKey/secret leak, audit reason required for mutations |

## 8. Related LLDD

| Document | Use |
| --- | --- |
| LLDD-BE-API-Common-Contracts | กำหนดสัญญากลางของ REST API ทุกเส้นเพื่อไม่ให้ endpoint รายตัวตีความต่างกัน: transport/auth/error/format/pagination/action/RBAC/audit/idempotency |
| LLDD-BE-API-Document-List-Search | ออกแบบ APIs สำหรับงานรอดำเนินการและค้นหาเอกสารที่เกี่ยวข้อง |
| LLDD-BE-API-Document-Create-Update | ออกแบบ APIs สำหรับสร้างเอกสารใหม่และบันทึกส่วนย่อยของเอกสาร |
| LLDD-BE-API-Document-Detail-Aggregate | ออกแบบ aggregate API สำหรับโหลดรายละเอียดเอกสารครบทุก section ให้หน้า FE detail |
| LLDD-BE-API-Document-Workflow-Actions | ออกแบบ APIs สำหรับรับผลพิจารณา ตรวจสิทธิ์ action และบันทึก audit/consideration log |
| LLDD-BE-API-Workflow-Instances | ออกแบบ Workflow Engine ภายในและ POST /api/v1/workflows/instances สำหรับเปิด workflow จาก Job 8b แทน K2 REST StartInstance โดยเป็นเจ้าของ Gen Flow Gate W/Y/N |
| LLDD-BE-API-Attachment-Sales-Timeline | ออกแบบ APIs สำหรับไฟล์แนบ ข้อมูลยอดขายเพิ่มเติม และ timeline/history |
| LLDD-BE-API-Lookup | ออกแบบ APIs กลุ่ม lookup ที่ใช้ร่วมทุกหน้าจอของ SBP Mall |
| LLDD-BE-API-Report-and-Master-Data | ออกแบบ APIs สำหรับรายงานตรวจสอบประกันรายได้ และ Master Data ที่ SBPGI ดูแลเอง (ปัจจัยภายนอก + รายชื่อคู่แข่ง) |
