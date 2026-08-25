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

### 2.1 Input / Progress / Output Contract

| Stage | Contract for implementation |
| --- | --- |
| Input | Topic inventory, owner assignment, estimates, screenshots, API/job/database scope, and schedule assumptions for the SBP Mall income-guarantee work package. |
| Progress | Use this index to sequence FE/BE work, confirm owner workload, locate detailed topic documents, and track dependency readiness before development starts. |
| Output | A single implementation index with activity plan, owner workload, FE/BE summaries, job breakdown, dependencies, and deliverable checklist. |

## 3. High Level Activity Plan

| Track | หัวข้อ | ชั่วโมง (impl + unit test) | ลำดับขั้น | Owner | เอกสารรายละเอียด |
| --- | --- | --- | --- | --- | --- |
| FE | FE - Integration Contracts | 16 | 2 | Chidchanok <lin> Saengamnat | LLDD-FE-Integration-Contracts |
| FE | FE - Application Foundation and Shared UI | **35** (impl 28 + test 7) | 3 | Chidchanok <lin> Saengamnat | LLDD-FE-Foundation |
| FE | FE - Document Lists | **35** (impl 28 + test 7) | 4 | Chidchanok <lin> Saengamnat | LLDD-FE-Document-Lists |
| FE | FE - Create Document | **8** (impl 6 + test 2) | 4 | Kittisak <New> Kaeowika | LLDD-FE-Create-Document |
| FE | FE - Document Detail and Action | **75** (impl 60 + test 15) | 4 | Kittisak <New> Kaeowika | LLDD-FE-Document-Detail |
| FE | FE - Status Summary Report | **25** (impl 20 + test 5) | 4 | Kittisak <New> Kaeowika | LLDD-FE-Report |
| FE | FE - Master Data | **20** (impl 16 + test 4) | 4 | Kittisak <New> Kaeowika | LLDD-FE-Master-Data |
| FE | FE - Testing and Delivery | 12 | 5 | Chidchanok <lin> Saengamnat | LLDD-FE-Testing-Delivery |
| BE | BE - Database Structure and Deployment | 31 | 1 | Aphiwit <Bank> Khammoon | LLDD-BE-Database-Structure |
| BE | BE - Data Migration and Cutover | 43 | 2 | Aphiwit <Bank> Khammoon | LLDD-BE-Data-Migration-Cutover |
| BE | BE - Integration with SBP Platform | 20 | 1 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-Integration-SBP-Platform |
| BE | BE - Workflow Engine Definition | 24 | 1 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-Workflow-Engine-Definition |
| BE | BE - API Common Contracts | 18 | 2 | Butsaba <But> Podamrong | LLDD-BE-API-Common-Contracts |
| BE | BE - API Document List and Search | **26** (impl 20 + test 6) | 3 | Butsaba <But> Podamrong | LLDD-BE-API-Document-List-Search |
| BE | BE - API Document Create and Update | **32** (impl 24 + test 8) | 3 | Butsaba <But> Podamrong | LLDD-BE-API-Document-Create-Update |
| BE | BE - API Document Detail Aggregate | **32** (impl 24 + test 8) | 3 | Butsaba <But> Podamrong | LLDD-BE-API-Document-Detail-Aggregate |
| BE | BE - API Document Workflow Actions | **37** (impl 28 + test 9) | 3 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Document-Workflow-Actions |
| BE | BE - Workflow Engine and API Workflow Instances | **32** (impl 24 + test 8) | 3 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Workflow-Instances |
| BE | BE - API Attachment Sales and Timeline | **34** (impl 26 + test 8) | 3 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-API-Attachment-Sales-Timeline |
| BE | BE - API Lookup | **13** (impl 10 + test 3) | 3 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-API-Lookup |
| BE | BE - API Report and Master Data | **39** (impl 30 + test 9) | 3 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-API-Report-and-Master-Data |
| BE | BE - Job Batch and Email Integration | **19** (impl 14 + test 5) | 2 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-Job-Batch-Email-SRM |

## 4. Workload Balance and Continuity

แผนนี้รวม owner ตามบุคคล (ปรับ 2026-08-07): ทีม 6 คนเหลือ FE 2 คนและ BE 4 คน โดย Peerakorn ย้ายจากสาย FE ไปสาย BE · Aphiwit เป็นเจ้าของ Database Structure + Data Migration/Cutover และ Job 2, 3, 4, 6, 8 · Peerakorn รับ Job 5, 7, 9, 10 · Tunyatorn รับ Job 8b เพราะเป็น job เดียวที่เรียก workflow engine และถือ Workflow Engine Definition อยู่แล้ว ชั่วโมงคิดที่ 5 วันต่อสัปดาห์และ 6 ชั่วโมงต่อวัน (30 ชั่วโมงต่อสัปดาห์) · ตัวเลขในตารางเป็นค่าประเมินตรง ๆ **ไม่มีส่วนเผื่อ (buffer)**

| Role | Owner | ชั่วโมง (impl + unit test) | Work Focus |
| --- | --- | --- | --- |
| FE | Kittisak <New> Kaeowika | **128** (impl 102 + test 26) | FE หน้าจอธุรกิจ (ไม่ทับกับงานระบบเดิมของ lin): Create Document -> Document Detail/Action (+ role pack 5 ฉบับ) -> Report -> Master Data |
| FE | Chidchanok <lin> Saengamnat | **98** (impl 84 + test 14) | FE ที่ต่อกับระบบเดิม: Integration Contracts (auth/session/permission จาก BFF) -> Foundation (sidebar/header/menu gating ของ portal เดิม) -> Document Lists -> Testing/Delivery |
| BE | Butsaba <But> Podamrong | **108** (impl 86 + test 22) | BE เอกสาร/สัญญากลางของ SBPGI เอง: Common Contracts -> List/Search -> Create/Update -> Detail Aggregate |
| BE | Tunyatorn <Vava> Kiatkongphongsa | **155** (impl 128 + test 27) | BE ที่ต่อกับระบบเดิม (นิยามสัญญาให้ฝั่ง FE ใช้ต่อ): Integration with SBP Platform -> Workflow Engine Definition -> Workflow Actions -> Workflow Instances -> Lookup -> Job 8b |
| BE | Peerakorn <Pete> Sakunkaewphithak | **152** (impl 115 + test 37) | BE support/interface (ย้ายจากสาย FE 2026-08-07): Attachment/Sales/Timeline -> Report and Master Data -> Batch/Email -> Job 5, 7, 9, 10 |
| BE | Aphiwit <Bank> Khammoon | **183** (impl 156 + test 27) | BE data ownership: Database Structure -> Data Migration/Cutover -> Job 2, 3, 4, 6, 8 |

## 5. FE Summary

| FE Topic | ชั่วโมง | ลำดับขั้น | Deliverable |
| --- | --- | --- | --- |
| Integration Contracts | 16 | 2 | Shared API client contract, Auth/JWT consumption from platform reference, Error display and validation message mapping |
| Application Foundation and Shared UI | 28 | 3 | Non-screen technical foundation, Route/module registry เฉพาะ SBP Mall, API client และ response typing |
| Document Lists | 28 | 4 | Waiting list, Related document list, Search/filter/status filter |
| Create Document | 6 | 4 | Create form shell, Tab: สร้างเอกสารทั่วไป, Tab: เอกสารจาก FS ผ่าน hidden iframe |
| Document Detail and Action | 60 | 4 | Document header, Store impact/new-store/factor sections, Role-based visible/editable sections |
| Status Summary Report | 20 | 4 | Report filters (SDD slide 60 · 2026-08-06: สถานะ*\|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ\|ประเภทร้าน (รหัสจาก common_code · รหัสที่ 4 รอยืนยัน) · Period Statement From-To (date, ค.ศ.) เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว), Summary table (sortable 14 columns), ปุ่มออกผล 3 ตัว (Preview Report · Export Excel · Export CSV to Batch) |
| Master Data | 16 | 4 | External factor master (SCR-09), Competitor brand master, CRUD modal |
| Testing and Delivery | 12 | 5 | Manual regression, Responsive pass, API contract verification |

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

| BE Topic | ชั่วโมง | ลำดับขั้น | Deliverable |
| --- | --- | --- | --- |
| Database Structure and Deployment | 31 | 1 | DDL ครบ 20 ตารางของ target schema (โซน A 8 · โซน B 9 · โซน C 3), Index, unique/partial index, check constraint และ FK ที่ต้องมีก่อน SIT, Seed data ที่ต้องมีก่อนเปิดระบบ (external_factors · competitors) — decisions ไป seed ที่ common_code ของระบบเดิม (DP-9), สคริปต์ deploy/rollback ต่อ environment และลำดับการรันตาม dependency |
| Data Migration and Cutover | 43 | 2 | Source-to-target mapping ระดับตาราง/คอลัมน์ (ORA FCS_FRN · MSSQL CPA_FRN_FGI -> 20 ตาราง), การแปลงคีย์: polymorphic TRANSACTION_PK -> typed FK · CompDocumentID -> doc_no · IMPACT_PROCESS_ID -> impact_process_id, แผน cutover เป็นรอบ (dry-run -> delta -> freeze -> final) และ rollback, Reconcile: นับแถว ยอดเงิน และ checksum ต่อโซน |
| Integration with SBP Platform | 20 | 1 | ตัวตนผู้ใช้จาก BFF header (x-api-key, x-user-id, x-user-group-id, x-user-permissions), Response envelope ของ store-backend: {success, data} / {success:false, data:null, error:{code,message}}, ไฟล์แนบผ่าน service S3 เดิม (POST /statement/upload-file-aws · download-file-aws), อีเมลผ่าน @gosoft-sbp/email-lib + ตาราง email_template / email_sent |
| Workflow Engine Definition | 24 | 1 | ลงทะเบียน workflow version ของ SBPGI 1 version (url_main + url_param_mapping), นิยาม state/status 5 ขั้น 06 -> 08 -> 01 -> 02 -> 03 และปลายทางจบ flow, นิยาม route ของทุกปุ่ม · การแตก route ตามวงเงินอนุมัติ เกณฑ์เดียว 100,000 เขียนเป็น**ตัวอย่างทางเลือก B เท่านั้น** — แหล่งเก็บวงเงินยังไม่ตัดสิน (มติเดิมคือ common_code · ดูข้อค้าง 5.6), สำรวจทางเลือกผู้อนุมัติ: workflow_group / workflow_group_map เทียบกับ addPreApprover รายคน — **ยังไม่ตัดสิน** (ดูข้อค้าง 5.6) |
| API Common Contracts | 18 | 2 | Base URL, content type, charset and request tracing, Auth/JWT platform validation and service-token exception, Standard success envelopes for list/detail/mutation, Standard error envelope and HTTP status mapping |
| API Document List and Search | 20 | 3 | Inbox tasks API, Document search API, Pagination, Status/year filter |
| API Document Create and Update | 24 | 3 | Create document, Duplicate guard, Running doc number, Partial update |
| API Document Detail Aggregate | 24 | 3 | Document aggregate query, Role profile output, Store impact/new-store/factor mapping, Compensation summary |
| API Document Workflow Actions | 28 | 3 | Submit action, Action owner guard, Amount threshold reference, Send back result |
| Workflow Engine and API Workflow Instances | 24 | 3 | Internal Workflow Engine API only, No FE screen and no Flow page work, Gen Flow Gate W/Y/N owner, Require compensation document created by Job 8 |
| API Attachment Sales and Timeline | 26 | 3 | Attachment metadata, Upload/download adapter, Sales 4 windows, Timeline query |
| API Lookup | 10 | 3 | Lookup APIs, Auth endpoints are platform reference only |
| API Report and Master Data | 30 | 3 | Report query service, Excel export (14 columns, SDD slide 60), Operator/factor CRUD, Report filters |
| Job Batch and Email Integration | 14 | 2 | Interface tracking และ pending ACK APIs (3 เส้น), Job runner guard และ application log, Notification adapter ผ่าน @gosoft-sbp/email-lib, STA ACK callback |

## 8. BE Batch Job Breakdown

| Job | ชั่วโมง | ลำดับขั้น | Owner | เอกสารรายละเอียด |
| --- | --- | --- | --- | --- |
| Job 2 ImportImpactStore | 14 | 3 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-2-ImportImpactStore |
| Job 3 ImportImpactCompetitor | 10 | 4 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-3-ImportImpactCompetitor |
| Job 4 PrepareImpactStoreToIAS | 14 | 4 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-4-PrepareImpactStoreToIAS |
| Job 5 ImportImpactSaleFromIAS | 16 | 5 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-Job-5-ImportImpactSaleFromIAS |
| Job 6 ExportImpactStoreToFS | 26 | 4 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-6-ExportImpactStoreToFS |
| Job 7 SyncCompetitorToDocument | 10 | 6 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-Job-7-SyncCompetitorToDocument |
| Job 8 CreateCompensationDocument | 18 | 5 | Aphiwit <Bank> Khammoon | LLDD-BE-Job-8-CreateCompensationDocument |
| Job 8b StartInternalWorkflow | 22 | 6 | Tunyatorn <Vava> Kiatkongphongsa | LLDD-BE-Job-8b-StartInternalWorkflow |
| Job 9 SyncNewStoreToDocument | 11 | 6 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-Job-9-SyncNewStoreToDocument |
| Job 10 NotifyNoReceiveData | 8 | 5 | Peerakorn <Pete> Sakunkaewphithak | LLDD-BE-Job-10-NotifyNoReceiveData |

## 9. Dependency

| Dependency | Owner | ใช้โดย |
| --- | --- | --- |
| Common API/FE contracts | BE/FE | LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts เป็นสัญญากลางของทุกหน้า FE และทุก service BE |
| API contract | BE/FE | ทุกหน้า FE และทุก service BE |
| Master Data contract | FE/BE | LLDD-FE-Master-Data ใช้ LLDD-BE-API-Report-and-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง (ไม่มี Operator/Menu Permission/System Config/Audit แล้ว — ใช้ระบบ SBP เดิม) |
| Blocker ลำดับขั้นที่ 1 | BE | LLDD-BE-Integration-SBP-Platform, LLDD-BE-Workflow-Engine-Definition, LLDD-BE-Database-Structure และสัญญากลางของ LLDD-API ต้องปิดก่อน เพราะเอกสาร BE ทุกฉบับอ้างอิง 4 ชิ้นนี้ |
| Auth/JWT platform และ menu service | Platform/SSO/IAM | FE Foundation เรียก /auth/profile + /users/current + /menus + /groups/current-user/permissions ของระบบเดิม; SBPGI รับตัวตนจาก BFF ผ่าน header x-api-key/x-user-id/x-user-group-id/x-user-permissions |
| Mock/fixture data | BE | FE development และ SIT |
| Screenshots/prototype | FE | UI implementation |
| Business rules | BA/BE | validation/action/report |

## 10. Deliverable Checklist

- Main LLDD Index
- Common contract LLDD สำหรับ API/FE integration
- LLDD-FE-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง
- Detailed FE LLDD per SBP Mall page group
- Detailed BE LLDD per SBP Mall API group and Jobs 2-10 + 8b
- Database Structure, Data Migration/Cutover, Integration with SBP Platform และ Workflow Engine Definition (เพิ่ม 2026-08-07)
- Screenshots embedded only for SBP Mall implementation pages
- Implementation flow diagrams embedded as reference, not Flow page deliverables
