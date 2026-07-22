# LLDD Phase #4 - 4.3 SBP Operating Management ประกันรายได้

วันที่จัดทำ: 2026-07-20  
เอกสารต้นทาง: `LLDD Check List.xlsx`  
Sheet: `LLDD`  
Module: `4.3 SBP Operating Management ประกันรายได้`  
Release: `Phase #4`  

## 1. Document Control

| รายการ | รายละเอียด |
|---|---|
| Document Type | Low Level Design Document (LLDD) |
| System | SBP Mall - ระบบประกันรายได้ |
| Phase | Phase #4 |
| Module | 4.3 SBP Operating Management ประกันรายได้ |
| Team จาก Checklist | SRM |
| Assignee จาก Checklist | TBC |
| Target Date จาก Checklist | 2026-04-30 |
| Status จาก Checklist | Not Start / Overdue |
| Scope หลัก | Integration (SRM) และ LLDD สำหรับระบบประกันรายได้ |

## 2. Checklist Traceability

| Excel Row | No | Release | Module | Function | Team | Create LLDD | Flag | Target Date |
|---:|---:|---|---|---|---|---|---|---|
| 76 | - | Phase #4 | 4.3 SBP Operating Management ประกันรายได้ | Header | - | - | - | - |
| 77 | 31 | Phase #4 | 4.3 SBP Operating Management ประกันรายได้ | Integration (SRM) | SRM | Not Start | Overdue | 2026-04-30 |
| 78 | 32 | Phase #4 | 4.3 SBP Operating Management ประกันรายได้ | LLDD | SRM | Not Start | Overdue | 2026-04-30 |

## 3. Objective

เอกสารนี้กำหนดรายละเอียด Low Level Design สำหรับส่วน `4.3 SBP Operating Management ประกันรายได้` ใน SBP Mall โดยเน้นการออกแบบเชิง implementation สำหรับ:

- การรับ/เชื่อมข้อมูลจาก SRM สำหรับงานประกันรายได้
- หน้าจอและ API ที่ใช้แสดง สร้าง ดำเนินการ และติดตามเอกสารประกันรายได้
- การจัดการรายงาน Master/Config Batch Monitor และ Email Template ที่เกี่ยวข้องกับ SBP Mall
- Validation, error handling, audit และ test cases ที่ต้องรองรับ

## 4. Scope

### 4.1 In Scope

| กลุ่มงาน | รายละเอียด |
|---|---|
| Integration (SRM) | รับหรือเชื่อมข้อมูลตั้งต้นจาก SRM เพื่อสร้าง/อัปเดตข้อมูลที่ใช้ในเอกสารประกันรายได้ |
| Dashboard | KPI, งานรอดำเนินการ, สรุปยอดชดเชย, กราฟสถานะ |
| Document List | รายการรอดำเนินการ, รายการที่เกี่ยวข้อง, รายการข้อมูลผิดปกติ/placeholder |
| Create Document | สร้างเอกสารประกันรายได้แบบ Manual/FS ตามสิทธิ์ที่ระบบหลักส่งมา |
| Document Detail | แสดงรายละเอียดร้านถูกกระทบ ร้านเปิดใหม่ แผนที่ ประวัติ ผลพิจารณา คู่แข่ง ปัจจัยอื่น เอกสารแนบ และ Action Panel |
| Document Action | บันทึกร่าง ส่งดำเนินการ อนุมัติ ไม่อนุมัติ ส่งกลับ และบันทึก comment/history |
| Report | รายงานตรวจสอบประกันรายได้, Preview, Export CSV สำหรับ Batch/บัญชี |
| Master/Config | ผู้ปฏิบัติงาน, ปัจจัยภายนอก, สิทธิ์เมนู, ตั้งค่าระบบ |
| Batch/Email | Batch Job Monitor, Job History, Retry/Re-run, Log Detail, Email Template/Preview |

### 4.2 Out of Scope

| ไม่รวม | หมายเหตุ |
|---|---|
| Login/Auth ใหม่ | ใช้ identity/permission จาก platform หรือ module กลาง |
| Flow page / Diagram page | ไม่ทำหน้าจอเอกสาร Flow เพิ่มใน Phase นี้ |
| Database design ใหม่ | LLDD นี้อธิบาย logical data และ contract เท่านั้น ไม่ออกแบบ ER/DDL ใหม่ |
| Plan pages/documents | ไม่รวม plan-api, plan-database, plan-flow หรือเอกสาร plan |
| Data migration | ไม่ย้ายข้อมูล production เดิม |
| HA infrastructure / Security pentest ภายนอก | อยู่นอกขอบเขต application LLDD |

## 5. Assumptions

- SRM เป็นเจ้าของข้อมูลต้นทางบางส่วนของร้าน/ผู้เกี่ยวข้อง/ข้อมูลที่ใช้เริ่มกระบวนการประกันรายได้
- รายละเอียด protocol ของ SRM ยังต้อง confirm เช่น REST API, file, MQ หรือ batch interface
- ระบบ SBP Mall มีข้อมูล user/role จากระบบกลางแล้ว จึงไม่ออกแบบ login ใหม่
- เลขที่เอกสารใช้รูปแบบ `YYYY/xxxxx` โดย `YYYY` เป็นปี พ.ศ. และ running 5 หลักต่อปี
- ร้านที่ข้อมูลยอดขายไม่ครบ 60 วันต้องแสดงเป็นรายการผิดปกติด้วยสีแดง
- รายงานบัญชีใช้ Preview และ Export CSV เพื่อส่งต่อ Batch/กระทบ SAP ภายนอกระบบ

## 6. Logical Architecture

```text
SRM
  |
  | Integration Contract
  v
SBP Mall API / Backend
  |-- SRM Integration Adapter
  |-- Income Guarantee Document Service
  |-- Workflow Action Service
  |-- Report Service
  |-- Master/Config Service
  |-- Batch Monitor Service
  |-- Email Template Service
  |
  v
Existing Data Store / Mock Repository / Shared Services
  |
  v
React-Vite Frontend (SBP Mall)
  |-- Dashboard
  |-- Document Lists
  |-- Create Document
  |-- Document Detail
  |-- Report
  |-- Master/Config
  |-- Batch/Email
```

## 7. Integration (SRM) Design

### 7.1 Purpose

Integration (SRM) ใช้รับข้อมูลตั้งต้นหรือข้อมูลอ้างอิงที่เกี่ยวข้องกับประกันรายได้ เพื่อให้ SBP Mall สามารถสร้างเอกสาร ติดตามสถานะ และแสดงข้อมูลร้านถูกกระทบได้ครบถ้วน

### 7.2 Integration Pattern

| หัวข้อ | Design |
|---|---|
| Integration Name | `SRM Income Guarantee Integration` |
| Direction | Inbound to SBP Mall |
| Owner | SRM |
| Consumer | SBP Mall Backend |
| Trigger | ตาม schedule หรือ event จาก SRM, ต้อง confirm กับ SRM |
| Transport | To be confirmed: REST API / File / MQ |
| Data Format | JSON หรือ delimited file, ต้อง confirm กับ SRM |
| Encoding | UTF-8 เป็น default, ถ้าเป็นไฟล์ legacy ต้องระบุ encoding แยก |
| Idempotency Key | `sourceSystem + sourceRefNo + impactedStoreCode + period` |
| Retry | Retry เฉพาะ transient error, ไม่ retry validation error |
| Audit | บันทึก inbound request/file, result, error, processed count |

### 7.3 Provisional Interface Contract

> ตารางนี้เป็น contract ระดับ LLDD สำหรับเริ่ม alignment กับ SRM ข้อมูลจริงต้อง confirm จาก SRM ก่อน build

| Field | Type | Required | Mapping / Usage |
|---|---|---|---|
| `sourceSystem` | string | Y | ค่าคงที่ `SRM` |
| `sourceRefNo` | string | Y | เลขอ้างอิงจาก SRM ใช้กันข้อมูลซ้ำ |
| `periodMonth` | string | Y | เดือนที่ชดเชย รูปแบบ `YYYY-MM` |
| `statementPeriodFrom` | date | Y | วันที่เริ่ม period statement |
| `statementPeriodTo` | date | Y | วันที่สิ้นสุด period statement |
| `impactedStoreCode` | string | Y | รหัสร้านถูกกระทบ 5 หลัก |
| `impactedStoreName` | string | Y | ชื่อร้านถูกกระทบ |
| `regionCode` | string | Y | ภาค/เขต |
| `franchiseType` | string | Y | ประเภทร้าน |
| `transferDate` | date | N | วันที่โอนเป็นร้าน SP |
| `newStoreCode` | string | Y | รหัสร้านเปิดใหม่ |
| `newStoreName` | string | Y | ชื่อร้านเปิดใหม่ |
| `openDate` | date | N | วันที่ร้านเปิดใหม่เปิด |
| `distanceKm` | number | N | ระยะห่างจากร้านถูกกระทบ |
| `salesDropAmount` | number | N | ยอดขายที่ลดลง |
| `compensationAmount` | number | N | จำนวนเงินชดเชยเบื้องต้น |
| `salesDataDays` | number | N | จำนวนวันข้อมูลยอดขาย ใช้ flag ข้อมูลผิดปกติ |
| `allMapUrl` | string | N | Link ไป ALLMAP |

### 7.4 Processing Logic

| Step | Logic | Success | Error |
|---|---|---|---|
| 1 | รับ request/file จาก SRM | สร้าง transaction log | Reject หาก format อ่านไม่ได้ |
| 2 | ตรวจ required fields | ผ่าน validation | แจ้งรายการ field error |
| 3 | ตรวจ duplicate ด้วย idempotency key | ไม่ซ้ำ | ถ้าซ้ำให้ mark duplicate และไม่สร้างซ้ำ |
| 4 | Normalize code/date/amount | ได้ canonical payload | Reject เฉพาะ record ที่ผิด |
| 5 | สร้างหรืออัปเดต impact candidate | พร้อมให้สร้างเอกสาร | บันทึก partial failure |
| 6 | Flag sales data < 60 days | แสดงเป็นข้อมูลผิดปกติ | ไม่ block ingestion |
| 7 | ส่งผล processing | return summary หรือสร้าง result file | log error detail |

### 7.5 Processing Result

| Field | Type | Description |
|---|---|---|
| `transactionId` | string | เลขอ้างอิงการรับข้อมูล |
| `receivedAt` | datetime | วันที่เวลารับข้อมูล |
| `totalRecords` | number | จำนวน record ทั้งหมด |
| `successRecords` | number | จำนวนที่ผ่าน |
| `failedRecords` | number | จำนวนที่ไม่ผ่าน |
| `duplicateRecords` | number | จำนวนข้อมูลซ้ำ |
| `errors[]` | array | รายการ error ต่อ record |

## 8. Frontend Low Level Design

### 8.1 Technology

| Layer | Design |
|---|---|
| Framework | React + Vite + TypeScript |
| Routing | React Router |
| API State | React Query |
| Local UI State | Component state / lightweight store |
| Styling | CSS Modules หรือ shared CSS ตาม prototype |
| Chart | Inline SVG / lightweight custom component |

### 8.2 Routes

| Route | Page | Purpose |
|---|---|---|
| `/` | Overview | Dashboard ระบบประกันรายได้ |
| `/documents/waiting` | DocumentListWaiting | เอกสารรอดำเนินการ |
| `/documents/related` | DocumentListRelated | เอกสารที่เกี่ยวข้อง |
| `/documents/abnormal` | DocumentListAbnormal | ข้อมูลผิดปกติหรือ placeholder |
| `/documents/create` | CreateDocument | สร้างเอกสารประกันรายได้ |
| `/documents/:docNo` | DocumentDetail | รายละเอียดเอกสารและ action |
| `/reports/status-summary` | StatusSummaryReport | รายงานตรวจสอบประกันรายได้ |
| `/masters/operators` | OperatorMaster | กำหนดผู้ปฏิบัติงาน |
| `/masters/factors` | ExternalFactorMaster | กำหนดปัจจัยภายนอก |
| `/permissions` | MenuPermission | สิทธิ์การเข้าถึงเมนู |
| `/configs` | SystemConfig | ตั้งค่าระบบ |
| `/jobs` | BatchJobMonitor | Batch Job Monitor |
| `/email-templates` | EmailTemplate | Email Template |

### 8.3 Shared Components

| Component | Responsibility |
|---|---|
| `DataTable` | sort/filter/pagination/action column |
| `StatusBadge` | แสดงสถานะเอกสารและสีตาม status |
| `AmountText` | format จำนวนเงิน 2 decimal |
| `DateText` | format date เป็น `DD/MM/YYYY` |
| `DocumentActionPanel` | ปุ่มบันทึก/ส่งดำเนินการ/comment/attachment |
| `AttachmentList` | แสดงไฟล์แนบทั้งหมดและเปิดไฟล์ |
| `ConfirmDialog` | confirm ก่อน action สำคัญ |
| `Toast` | แสดงผลสำเร็จ/ผิดพลาด |
| `AuditTimeline` | แสดงประวัติการพิจารณา |

### 8.4 Page Detail

| Page | UI Sections | API |
|---|---|---|
| Overview | KPI, pending queue, monthly chart, status chart | `GET /dashboard/summary` |
| Document List | Search/filter, table, status flag, row click | `GET /tasks`, `GET /documents` |
| Create Document | Store selector, period, source, save/submit | `POST /documents` |
| Document Detail | Header, store, new stores, map, history, competitors, factors, attachments, action | `GET /documents/{docNo}`, `PUT /documents/{docNo}`, `POST /documents/{docNo}/actions` |
| Report | Filter, preview, export | `GET /reports/status-summary`, `GET /reports/status-summary/export` |
| Master/Config | CRUD table, modal, reason, audit | `/operators`, `/factors`, `/menu-permissions`, `/configs` |
| Batch/Email | job list/history/log/retry, template preview | `/jobs`, `/email-templates` |

## 9. Backend Low Level Design

### 9.1 Module Structure

```text
src/modules/incomeGuarantee/
  controllers/
    dashboard.controller.ts
    document.controller.ts
    report.controller.ts
    master.controller.ts
    batch.controller.ts
    emailTemplate.controller.ts
    srmIntegration.controller.ts
  services/
    dashboard.service.ts
    document.service.ts
    documentAction.service.ts
    report.service.ts
    master.service.ts
    batchMonitor.service.ts
    emailTemplate.service.ts
    srmIntegration.service.ts
  validators/
    document.validator.ts
    action.validator.ts
    report.validator.ts
    master.validator.ts
    srmIntegration.validator.ts
  repositories/
    document.repository.ts
    report.repository.ts
    master.repository.ts
    integration.repository.ts
  types/
    document.types.ts
    report.types.ts
    integration.types.ts
```

### 9.2 API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Dashboard KPI และกราฟ |
| `GET` | `/api/v1/tasks` | เอกสารรอดำเนินการ |
| `GET` | `/api/v1/documents` | ค้นหาเอกสารที่เกี่ยวข้อง |
| `GET` | `/api/v1/documents/{docNo}` | รายละเอียดเอกสาร 12 ส่วน |
| `POST` | `/api/v1/documents` | สร้างเอกสาร |
| `PUT` | `/api/v1/documents/{docNo}` | บันทึกส่วนย่อย |
| `POST` | `/api/v1/documents/{docNo}/actions` | ส่งผลพิจารณา |
| `GET` | `/api/v1/documents/{docNo}/timeline` | ประวัติการพิจารณา |
| `POST` | `/api/v1/documents/{docNo}/attachments` | แนบไฟล์ |
| `GET` | `/api/v1/reports/status-summary` | Preview รายงาน |
| `GET` | `/api/v1/reports/status-summary/export` | Export CSV |
| `GET/POST/PUT/DELETE` | `/api/v1/operators` | ผู้ปฏิบัติงาน |
| `GET/POST/PUT/DELETE` | `/api/v1/factors` | ปัจจัยภายนอก |
| `GET/PUT` | `/api/v1/menu-permissions` | สิทธิ์เมนู |
| `GET/POST/PUT/DELETE` | `/api/v1/configs` | ตั้งค่าระบบ |
| `GET/POST/PUT` | `/api/v1/jobs` | Batch monitor/run history/retry |
| `GET/PUT/POST` | `/api/v1/email-templates` | Email template/preview/reset |
| `POST` | `/api/v1/integrations/srm/income-guarantee` | Inbound SRM integration, provisional |

### 9.3 Service Responsibilities

| Service | Responsibility |
|---|---|
| `SrmIntegrationService` | รับข้อมูลจาก SRM, validate, normalize, idempotency, transaction log |
| `DocumentService` | สร้าง/อ่าน/แก้ไขเอกสาร และ compose detail aggregate |
| `DocumentActionService` | ตรวจ action, route สถานะ, บันทึก consideration/audit |
| `ReportService` | Query รายงาน, preview, export CSV |
| `MasterService` | CRUD ผู้ปฏิบัติงาน/ปัจจัยภายนอก/permission/config |
| `BatchMonitorService` | job list/history/retry/log detail |
| `EmailTemplateService` | template CRUD, preview/render, reset |

## 10. Logical Data Objects

> ส่วนนี้เป็น logical object สำหรับ LLDD ไม่ใช่ database design หรือ DDL

| Object | Key Fields | Usage |
|---|---|---|
| `IncomeGuaranteeDocument` | `docNo`, `statusCode`, `currentSectionCode`, `periodMonth` | Header เอกสาร |
| `ImpactedStore` | `storeCode`, `storeName`, `regionCode`, `franchiseType` | ร้านถูกกระทบ |
| `NewStoreImpact` | `newStoreCode`, `distanceKm`, `allocationPercent`, `compensationAmount` | ร้านเปิดใหม่ที่กระทบ |
| `ConsiderationLog` | `docNo`, `sectionCode`, `result`, `comment`, `actedBy`, `actedAt` | ประวัติพิจารณา |
| `ExternalFactorEntry` | `factorCode`, `startDate`, `endDate`, `description` | ปัจจัยอื่น |
| `CompetitorEntry` | `competitorName`, `openDate`, `description` | ร้านคู่แข่ง |
| `Attachment` | `fileName`, `fileSize`, `contentType`, `uploadedBy`, `uploadedAt` | ไฟล์แนบ |
| `ReportStatusSummaryRow` | `docNo`, `storeCode`, `status`, `result`, `compensationAmount` | รายงาน |
| `SrmImpactCandidate` | `sourceRefNo`, `impactedStoreCode`, `periodMonth`, `newStoreCode` | ข้อมูลตั้งต้นจาก SRM |

## 11. Business Rules

| Rule ID | Rule | Handling |
|---|---|---|
| BR-01 | ค้นหาเอกสาร/รายงานต้องระบุปี | Return validation error |
| BR-02 | เลขเอกสารรูปแบบ `YYYY/xxxxx` | Generate running ต่อปี |
| BR-03 | ยอดขายไม่ครบ 60 วัน | แสดงสีแดง/flag ผิดปกติ ไม่ block การแสดงผล |
| BR-04 | `%ชดเชย` ของร้านเปิดใหม่รวมต้องเท่ากับ 100% | Validate ก่อน save |
| BR-05 | ไฟล์แนบไม่เกิน 5 MB | Reject file |
| BR-06 | ส่งดำเนินการต้องเลือกผลพิจารณา | แสดง popup ตาม SRS |
| BR-07 | บาง action ต้องกรอก comment | Validate ก่อน submit |
| BR-08 | เงินชดเชยมากกว่า 100,000 บาท | ส่งต่อ AVP OPT ตาม rule ปัจจุบัน |
| BR-09 | แก้ Master/Config ต้องบันทึก reason | Create audit log |
| BR-10 | SRM duplicate sourceRefNo | Skip duplicate และ log result |

## 12. Validation & Error Message

| Scenario | Validation | Message |
|---|---|---|
| ไม่เลือกผลพิจารณาก่อนส่ง | `result` required | `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ` |
| เลือกร้านคู่แข่งไม่ครบ | competitor required | `กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ` |
| วันที่สิ้นสุดน้อยกว่าวันเริ่มต้น | `endDate >= startDate` | แสดง popup แจ้งวันที่ไม่ถูกต้อง |
| ผลรวม % ชดเชยไม่เท่ากับ 100 | sum allocation != 100 | แจ้งให้ปรับ % ชดเชยรวมให้เท่ากับ 100 |
| ไฟล์แนบเกิน 5 MB | file size > 5 MB | แจ้งขนาดไฟล์เกินกำหนด |
| SRM payload ขาด required field | schema validation fail | return field-level errors |

## 13. Audit, Logging, and Monitoring

| Event | Audit / Log |
|---|---|
| รับข้อมูล SRM | integration transaction log พร้อม transactionId |
| สร้างเอกสาร | audit document created |
| แก้ไขเอกสาร | audit changed fields |
| ส่งผลพิจารณา | consideration log |
| แนบไฟล์ | attachment audit |
| แก้ master/config | audit พร้อม reason |
| Export report | report export log |
| Retry batch job | job run history |
| Error จาก integration | error log พร้อม sourceRefNo/record index |

## 14. Security

| Area | Design |
|---|---|
| User access | ใช้ role/permission จาก platform กลาง |
| API authorization | ทุก API ตรวจ permission ตาม menu/action |
| SRM integration auth | ใช้ service token หรือ API key, ต้อง confirm กับ SRM |
| Attachment | ตรวจ file size, extension, content type |
| Audit | ทุก action สำคัญต้องระบุ actor และ timestamp |
| Sensitive data | ไม่ log token, secret, หรือข้อมูลส่วนบุคคลเกินจำเป็น |

## 15. Test Cases

### 15.1 Integration (SRM)

| TC | Case | Expected Result |
|---|---|---|
| TC-SRM-01 | รับ payload ถูกต้อง 1 record | successRecords = 1 |
| TC-SRM-02 | payload ขาด impactedStoreCode | failedRecords = 1 พร้อม field error |
| TC-SRM-03 | ส่ง sourceRefNo ซ้ำ | duplicateRecords = 1 และไม่สร้างซ้ำ |
| TC-SRM-04 | salesDataDays < 60 | record ผ่าน แต่ flag เป็นผิดปกติ |
| TC-SRM-05 | date/amount format ผิด | reject record พร้อม error detail |

### 15.2 Document

| TC | Case | Expected Result |
|---|---|---|
| TC-DOC-01 | สร้างเอกสารใหม่ | ได้ docNo รูปแบบ `YYYY/xxxxx` |
| TC-DOC-02 | เปิดรายการรอดำเนินการ | แสดงเฉพาะงานของผู้ใช้/section |
| TC-DOC-03 | แก้ % ชดเชยรวม 100% | save สำเร็จ |
| TC-DOC-04 | แก้ % ชดเชยรวมไม่ครบ 100% | validate error |
| TC-DOC-05 | ส่งดำเนินการโดยไม่เลือกผล | แสดง popup ตาม SRS |
| TC-DOC-06 | แนบไฟล์เกิน 5 MB | upload ไม่สำเร็จ |

### 15.3 Report / Master / Batch / Email

| TC | Case | Expected Result |
|---|---|---|
| TC-RPT-01 | ค้นหารายงานโดยไม่ระบุปี | validation error |
| TC-RPT-02 | Export CSV | ได้ไฟล์ตาม filter |
| TC-MST-01 | เพิ่มปัจจัยภายนอก code ซ้ำ | validation error |
| TC-MST-02 | แก้ master โดยไม่ระบุ reason | validation error |
| TC-BAT-01 | Retry job จากหน้าจอ | create job run history |
| TC-EML-01 | Preview email template | render variable ถูกต้อง |

## 16. Deployment Checklist

| Item | Check |
|---|---|
| SRM contract confirmed | Pending |
| API paths reviewed with FE | Pending |
| Test fixtures prepared | Pending |
| Integration auth configured | Pending |
| Error code/message reviewed | Pending |
| Audit log reviewed | Pending |
| SIT scenario approved | Pending |
| UAT owner confirmed | Pending |

## 17. Open Issues

| ID | Issue | Owner | Required Decision |
|---|---|---|---|
| OI-01 | SRM transport ยังไม่ชัดเจน | SRM/SBP | REST, File, MQ หรือ Batch |
| OI-02 | SRM field mapping จริงยังไม่ชัดเจน | SRM/SBP | ยืนยัน sample payload/file |
| OI-03 | Integration auth ยังไม่ชัดเจน | SRM/Security | service token/API key/cert |
| OI-04 | Schedule/SLA ยังไม่ชัดเจน | SRM/SBP | realtime, daily, หรือ manual retry |
| OI-05 | Assignee ใน checklist เป็น TBC | PM | ระบุผู้รับผิดชอบ |
| OI-06 | ขอบเขตข้อมูลผิดปกติ | Business/SBP | placeholder หรือเปิดฟังก์ชัน assign งาน |

## 18. Sign-off Checklist

| Role | Name | Status | Date |
|---|---|---|---|
| Business Owner | TBC | Pending | - |
| SRM Owner | TBC | Pending | - |
| Backend Lead | TBC | Pending | - |
| Frontend Lead | TBC | Pending | - |
| QA Lead | TBC | Pending | - |
| PM | TBC | Pending | - |

