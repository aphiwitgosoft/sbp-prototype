# LLDD Main Index - Phase 4.3 SBP Operating Management ประกันรายได้

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Purpose

เอกสารหลักนี้เป็น LLDD Index สำหรับ Phase #4 - 4.3 SBP Operating Management ประกันรายได้ โดยสรุปหัวข้อใหญ่ของงาน FE/BE เฉพาะระบบประกันรายได้ (SBP Mall) และเชื่อมไปยังเอกสาร LLDD รายละเอียดของแต่ละหัวข้อ

## 2. Scope

- ครอบคลุมเฉพาะระบบประกันรายได้ (SBP Mall)
- งาน FE/BE ในเอกสารนี้นับเฉพาะหน้าจอ module SBP Mall และ API/Job/Service ที่รองรับระบบประกันรายได้เท่านั้น
- งานออกแบบ flow ระดับระบบและ schema ระดับองค์กรไม่ถูกนับซ้ำเป็นงานหน้าจอ FE
- รายละเอียดที่จำเป็นต่อการพัฒนา การตรวจรับ และการส่งมอบถูกรวมไว้ใน LLDD แต่ละฉบับ
- รูปหน้าจอในหัวข้อ FE ใช้อธิบายองค์ประกอบและพฤติกรรมที่ต้องพัฒนา
- ไม่รวมการพัฒนา Login/Auth ของ platform และกระบวนการภายนอกขอบเขต SBP Mall

## 2.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | Topic inventory, owner assignment, estimates, screenshots, API/job/database scope, and schedule assumptions for the SBP Mall income-guarantee work package. |
| Progress | Use this index to sequence FE/BE work, confirm owner workload, locate detailed topic documents, and track dependency readiness before development starts. |
| Output | A single implementation index with activity plan, owner workload, FE/BE summaries, job breakdown, dependencies, and deliverable checklist. |

## 2.2 Schedule Assumption

| Item | Value |
| --- | --- |
| Start date for every owner | 29/07/2026 |
| Target finish | 27/08/2026 |
| Maximum delivery window | ไม่เกิน 4.5 work weeks (22.5 วันทำงาน / 135 ชั่วโมงต่อคน) |
| Allocation per developer | มากกว่า 3 work weeks และไม่เกิน 4.5 work weeks หรือมากกว่า 90 ชั่วโมงและไม่เกิน 135 ชั่วโมงต่อคน |
| Working-time rule | 1 สัปดาห์ = 5 วันทำงาน, 1 วัน = 6 ชั่วโมง, รวม 30 ชั่วโมงต่อสัปดาห์; ทำงานจันทร์-ศุกร์ |
| Task sequencing | หัวข้อเป็น delivery window ที่ทำต่อเนื่องหรือ overlap ได้ตาม dependency ภายใน 29/07/2026 ถึง 27/08/2026; Aphiwit รับเฉพาะ Job 1-10 และ 8b |
| Estimate interpretation | แสดง delivery estimate เป็นชั่วโมงเท่านั้น โดยรวม buffer ตามความยาก ความเสี่ยงด้าน integration และ rerun แล้ว |

## 3. High Level Activity Plan

| Track | หัวข้อ | ชั่วโมง | Start Date | End Date | Owner | เอกสารรายละเอียด |
| --- | --- | --- | --- | --- | --- | --- |
| FE | FE - Integration Contracts | 18 | 29/07/2026 | 31/07/2026 | Chidchanok <lin> Saengamnat | LLDD-FE-Integration-Contracts |
| FE | FE - Application Foundation and Shared UI | 42 | 03/08/2026 | 11/08/2026 | Chidchanok <lin> Saengamnat | LLDD-FE-Foundation |
| FE | FE - Overview Dashboard | 39 | 12/08/2026 | 20/08/2026 | Chidchanok <lin> Saengamnat | LLDD-FE-Overview |
| FE | FE - Document Lists | 42 | 29/07/2026 | 06/08/2026 | Peerakorn <Pete> Sakunkaewphithak | LLDD-FE-Document-Lists |
| FE | FE - Create Document | 30 | 29/07/2026 | 04/08/2026 | Kittisak <New> Kaeowika | LLDD-FE-Create-Document |
| FE | FE - Document Detail and Action | 72 | 05/08/2026 | 20/08/2026 | Kittisak <New> Kaeowika | LLDD-FE-Document-Detail |
| FE | FE - Status Summary Report | 30 | 07/08/2026 | 13/08/2026 | Peerakorn <Pete> Sakunkaewphithak | LLDD-FE-Report |
| FE | FE - Master and Config | 30 | 14/08/2026 | 20/08/2026 | Peerakorn <Pete> Sakunkaewphithak | LLDD-FE-Master-Config |
| FE | FE - Batch Job Monitor | 24 | 21/08/2026 | 26/08/2026 | Kittisak <New> Kaeowika | LLDD-FE-Batch-Monitor |
| FE | FE - Email Template and Notification Config | 21 | 20/08/2026 | 25/08/2026 | Chidchanok <lin> Saengamnat | LLDD-FE-Email-Template |
| FE | FE - Testing and Delivery | 24 | 21/08/2026 | 26/08/2026 | Peerakorn <Pete> Sakunkaewphithak | LLDD-FE-Testing-Delivery |
| BE | BE - API Common Contracts | 15 | 29/07/2026 | 31/07/2026 | Butsaba <But> Podamrong | LLDD-BE-API-Common-Contracts |
| BE | BE - API Dashboard Summary | 18 | 31/07/2026 | 05/08/2026 | Butsaba <But> Podamrong | LLDD-BE-API-Dashboard-Summary |
| BE | BE - API Document List and Search | 21 | 05/08/2026 | 10/08/2026 | Butsaba <But> Podamrong | LLDD-BE-API-Document-List-Search |
| BE | BE - API Document Create and Update | 27 | 29/07/2026 | 04/08/2026 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Document-Create-Update |
| BE | BE - API Document Detail Aggregate | 27 | 11/08/2026 | 17/08/2026 | Butsaba <But> Podamrong | LLDD-BE-API-Document-Detail-Aggregate |
| BE | BE - API Document Workflow Actions | 24 | 17/08/2026 | 21/08/2026 | Butsaba <But> Podamrong | LLDD-BE-API-Document-Workflow-Actions |
| BE | BE - Workflow Engine and API Workflow Instances | 21 | 04/08/2026 | 07/08/2026 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Workflow-Instances |
| BE | BE - API Attachment Sales and Timeline | 21 | 10/08/2026 | 13/08/2026 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Attachment-Sales-Timeline |
| BE | BE - API Lookup RBAC and Email Template | 30 | 13/08/2026 | 20/08/2026 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Lookup-RBAC-Email |
| BE | BE - API Report Master Config | 30 | 20/08/2026 | 27/08/2026 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Report-Master-Config |
| BE | BE - Job Batch Email and SRM Integration | 24 | 21/08/2026 | 27/08/2026 | Butsaba <But> Podamrong | LLDD-BE-Job-Batch-Email-SRM |

## 4. Workload Balance and Continuity

แผนนี้รวม owner ตามบุคคล โดย Aphiwit รับ Job 1-10 และ 8b คนเดียว ส่วน BE อื่นแบ่งระหว่าง But และ Vava ตามกลุ่ม contract/read/action กับ command/workflow/support ตามลำดับ ภาระงานของทุกคนมากกว่า 3 work weeks และไม่เกิน 4.5 work weeks เมื่อคิดที่ 5 วันต่อสัปดาห์และ 6 ชั่วโมงต่อวัน

| Role | Owner | Hours | Start Date | End Date | Work Focus |
| --- | --- | --- | --- | --- | --- |
| FE | Kittisak <New> Kaeowika | 126 | 29/07/2026 | 26/08/2026 | FE document journey: Create Document -> Document Detail/Action -> Batch Monitor |
| FE | Peerakorn <Pete> Sakunkaewphithak | 126 | 29/07/2026 | 26/08/2026 | FE list, reporting and admin journey: Document Lists -> Report -> Master/Config -> Testing/Delivery |
| FE | Chidchanok <lin> Saengamnat | 120 | 29/07/2026 | 25/08/2026 | FE shared contracts and experience: Integration Contracts -> Foundation -> Overview -> Email Template/Notification Config |
| BE | Butsaba <But> Podamrong | 129 | 29/07/2026 | 27/08/2026 | BE common/read/action/operations: Common Contracts -> Dashboard/List -> Detail Aggregate -> Workflow Actions -> Batch/Email/SRM |
| BE | Tunyatorn <Vava> Kiatkongphongsa | 129 | 29/07/2026 | 27/08/2026 | BE command/workflow/support APIs: Create/Update -> Workflow Instances -> Attachment/Sales/Timeline -> Lookup/RBAC/Email -> Report/Master/Config |
| BE | Aphiwit <Bank> Khammoon | 129 | 29/07/2026 | 27/08/2026 | BE batch ownership: Job 1-10 และ 8b ตั้งแต่ source analysis, migration, test, rerun ไปจนถึง handover |

## 5. FE Summary

| FE Topic | ชั่วโมง | Start Date | End Date | Deliverable |
| --- | --- | --- | --- | --- |
| Integration Contracts | 18 | 29/07/2026 | 31/07/2026 | Shared API client contract, Auth/JWT consumption from platform reference, Error display and validation message mapping |
| Application Foundation and Shared UI | 42 | 03/08/2026 | 11/08/2026 | Non-screen technical foundation, Route/module registry เฉพาะ SBP Mall, API client และ response typing |
| Overview Dashboard | 39 | 12/08/2026 | 20/08/2026 | KPI cards 4 กล่อง, Task summary และ pending queue, Monthly compensation chart |
| Document Lists | 42 | 29/07/2026 | 06/08/2026 | Waiting list, Related document list, Search/filter/status filter |
| Create Document | 30 | 29/07/2026 | 04/08/2026 | Create form shell, Tab: สร้างเอกสารทั่วไป, Tab: เอกสารจาก FS ผ่าน hidden iframe |
| Document Detail and Action | 72 | 05/08/2026 | 20/08/2026 | Document header, Store impact/new-store/factor sections, Role-based visible/editable sections |
| Status Summary Report | 30 | 07/08/2026 | 13/08/2026 | Report filters, Summary table, Preview/detail modal |
| Master and Config | 30 | 14/08/2026 | 20/08/2026 | Operator master, External factor master, Menu permission, System/Global Config (SCR-11) |
| Batch Job Monitor | 24 | 21/08/2026 | 26/08/2026 | Job selector/list สำหรับเลือก job ที่ต้องดูรายละเอียด, Tab: แบบฟอร์มพารามิเตอร์, Tab: ประวัติการรัน |
| Email Template and Notification Config | 21 | 20/08/2026 | 25/08/2026 | Email template list, Template edit form, Variable helper |
| Testing and Delivery | 24 | 21/08/2026 | 26/08/2026 | Manual regression, Responsive pass, API contract verification |

## 6. Document Detail Role Pack

เอกสารลูก 5 ฉบับนี้เป็นรายละเอียดแยกตาม role สำหรับอ่านประกอบ LLDD-FE-Document-Detail ไม่ถูกนับซ้ำใน activity plan/hour รวม

| Role document | Parent | Hour allocation |
| --- | --- | --- |
| LLDD-FE-Document-Detail-Role-06-SBP-DSA | LLDD-FE-Document-Detail | included in parent hours |
| LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer | LLDD-FE-Document-Detail | included in parent hours |
| LLDD-FE-Document-Detail-Role-01-Business-Promotion | LLDD-FE-Document-Detail | included in parent hours |
| LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion | LLDD-FE-Document-Detail | included in parent hours |
| LLDD-FE-Document-Detail-Role-03-AVP-SBP | LLDD-FE-Document-Detail | included in parent hours |

## 7. BE Summary

| BE Topic | ชั่วโมง | Start Date | End Date | Deliverable |
| --- | --- | --- | --- | --- |
| API Common Contracts | 15 | 29/07/2026 | 31/07/2026 | Base URL, content type, charset and request tracing, Auth/JWT platform validation and service-token exception, Standard success envelopes for list/detail/mutation, Standard error envelope and HTTP status mapping |
| API Dashboard Summary | 18 | 31/07/2026 | 05/08/2026 | Dashboard summary service, KPI query, Monthly compensation chart, Status chart |
| API Document List and Search | 21 | 05/08/2026 | 10/08/2026 | Inbox tasks API, Document search API, Pagination, Status/year filter |
| API Document Create and Update | 27 | 29/07/2026 | 04/08/2026 | Create document, Duplicate guard, Running doc number, Partial update |
| API Document Detail Aggregate | 27 | 11/08/2026 | 17/08/2026 | Document aggregate query, Role profile output, Store impact/new-store/factor mapping, Compensation summary |
| API Document Workflow Actions | 24 | 17/08/2026 | 21/08/2026 | Submit action, Action owner guard, Amount threshold reference, Send back result |
| Workflow Engine and API Workflow Instances | 21 | 04/08/2026 | 07/08/2026 | Internal Workflow Engine API only, No FE screen and no Flow page work, Gen Flow Gate W/Y/N owner, Require compensation document created by Job 8 |
| API Attachment Sales and Timeline | 21 | 10/08/2026 | 13/08/2026 | Attachment metadata, Upload/download adapter, Sales 4 windows, Timeline query |
| API Lookup RBAC and Email Template | 30 | 13/08/2026 | 20/08/2026 | Lookup APIs, Employee search, Role/menu/menu-permission CRUD, Audit log search |
| API Report Master Config | 30 | 20/08/2026 | 27/08/2026 | Report query service, CSV export, Operator/factor CRUD, System/Global Config (SCR-11) |
| Job Batch Email and SRM Integration | 24 | 21/08/2026 | 27/08/2026 | Batch Job Admin APIs ครบ 6 endpoints, Interface tracking และ pending ACK APIs, Job runner guard/history, Notification adapter |

## 8. BE Batch Job Breakdown

| Job | ชั่วโมง | Start Date | End Date | Owner | เอกสารรายละเอียด |
| --- | --- | --- | --- | --- | --- |
| Job 1 ImportQSSI | 13 | 29/07/2026 | 31/07/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-1-ImportQSSI |
| Job 2 ImportImpactStore | 13 | 31/07/2026 | 04/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-2-ImportImpactStore |
| Job 3 ImportImpactCompetitor | 10 | 04/08/2026 | 05/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-3-ImportImpactCompetitor |
| Job 4 PrepareImpactStoreToIAS | 13 | 06/08/2026 | 10/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-4-PrepareImpactStoreToIAS |
| Job 5 ImportImpactSaleFromIAS | 13 | 10/08/2026 | 12/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-5-ImportImpactSaleFromIAS |
| Job 6 ExportImpactStoreToFS | 15 | 12/08/2026 | 14/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-6-ExportImpactStoreToFS |
| Job 7 SyncCompetitorToDocument | 10 | 14/08/2026 | 18/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-7-SyncCompetitorToDocument |
| Job 8 CreateCompensationDocument | 13 | 18/08/2026 | 20/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-8-CreateCompensationDocument |
| Job 8b StartInternalWorkflow | 10 | 20/08/2026 | 24/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-8b-StartInternalWorkflow |
| Job 9 SyncNewStoreToDocument | 10 | 24/08/2026 | 25/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-9-SyncNewStoreToDocument |
| Job 10 NotifyNoReceiveData | 9 | 26/08/2026 | 27/08/2026 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-10-NotifyNoReceiveData |

## 9. Dependency

| Dependency | Owner | ใช้โดย |
| --- | --- | --- |
| Common API/FE contracts | BE/FE | LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts เป็นสัญญากลางของทุกหน้า FE และทุก service BE |
| API contract | BE/FE | ทุกหน้า FE และทุก service BE |
| Auth/JWT platform และ menu service | Platform/SSO/IAM | FE Foundation เรียก /auth/me + /me/menus; BE validate Authorization: Bearer <JWT> |
| Mock/fixture data | BE | FE development และ SIT |
| Screenshots/prototype | FE | UI implementation |
| Business rules | BA/BE | validation/action/report |

## 10. Deliverable Checklist

- Main LLDD Index
- Common contract LLDD สำหรับ API/FE integration
- Detailed FE LLDD per SBP Mall page group
- Detailed BE LLDD per SBP Mall API group and Jobs 1-10 + 8b
- Screenshots embedded only for SBP Mall implementation pages
- Implementation flow diagrams embedded as reference, not Flow page deliverables
