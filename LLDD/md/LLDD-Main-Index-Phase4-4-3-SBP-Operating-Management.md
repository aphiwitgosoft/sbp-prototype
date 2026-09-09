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
| FE | FE - Integration Contracts | 16 | 2 | Chidchanok &lt;lin&gt; Saengamnat | LLDD-FE-Integration-Contracts |
| FE | FE - Application Foundation and Shared UI | **35** (impl 28 + test 7) | 3 | Chidchanok &lt;lin&gt; Saengamnat | LLDD-FE-Foundation |
| FE | FE - Document Lists | **35** (impl 28 + test 7) | 4 | Chidchanok &lt;lin&gt; Saengamnat | LLDD-FE-Document-Lists |
| FE | FE - Create Document | **8** (impl 6 + test 2) | 4 | Kittisak &lt;New&gt; Kaeowika | LLDD-FE-Create-Document |
| FE | FE - Document Detail and Action | **75** (impl 60 + test 15) | 4 | Kittisak &lt;New&gt; Kaeowika | LLDD-FE-Document-Detail |
| FE | FE - Status Summary Report | **25** (impl 20 + test 5) | 4 | Chidchanok &lt;lin&gt; Saengamnat | LLDD-FE-Report |
| FE | FE - Master Data | **20** (impl 16 + test 4) | 4 | Kittisak &lt;New&gt; Kaeowika | LLDD-FE-Master-Data |
| FE | FE - Testing and Delivery | 12 | 5 | Chidchanok &lt;lin&gt; Saengamnat | LLDD-FE-Testing-Delivery |
| BE | BE - Database Structure and Deployment | 31 | 1 | Peerakorn &lt;Pete&gt; Sakunkaewphithak | LLDD-BE-Database-Structure |
| BE | BE - Data Migration and Cutover | 43 | 2 | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | LLDD-BE-Data-Migration-Cutover |
| BE | BE - Integration with SBP Platform | 20 | 1 | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | LLDD-BE-Integration-SBP-Platform |
| BE | BE - Workflow Engine Definition | 24 | 1 | Peerakorn &lt;Pete&gt; Sakunkaewphithak | LLDD-BE-Workflow-Engine-Definition |
| BE | BE - API Common Contracts | 18 | 2 | Butsaba &lt;But&gt; Podamrong | LLDD-BE-API-Common-Contracts |
| BE | BE - API Document List and Search | **26** (impl 20 + test 6) | 3 | Butsaba &lt;But&gt; Podamrong | LLDD-BE-API-Document-List-Search |
| BE | BE - API Document Create and Update | **32** (impl 24 + test 8) | 3 | Butsaba &lt;But&gt; Podamrong | LLDD-BE-API-Document-Create-Update |
| BE | BE - API Document Detail Aggregate | **32** (impl 24 + test 8) | 3 | Butsaba &lt;But&gt; Podamrong | LLDD-BE-API-Document-Detail-Aggregate |
| BE | BE - API Document Workflow Actions | **37** (impl 28 + test 9) | 3 | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | LLDD-BE-API-Document-Workflow-Actions |
| BE | BE - Workflow Engine and API Workflow Instances | **32** (impl 24 + test 8) | 3 | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | LLDD-BE-API-Workflow-Instances |
| BE | BE - API Attachment Sales and Timeline | **34** (impl 26 + test 8) | 3 | Peerakorn &lt;Pete&gt; Sakunkaewphithak | LLDD-BE-API-Attachment-Sales-Timeline |
| BE | BE - API Lookup | **13** (impl 10 + test 3) | 3 | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | LLDD-BE-API-Lookup |
| BE | BE - API Report and Master Data | **39** (impl 30 + test 9) | 3 | Peerakorn &lt;Pete&gt; Sakunkaewphithak | LLDD-BE-API-Report-and-Master-Data |
| BE | BE - Job Batch and Email Integration | **11** (impl 8 + test 3) | 2 | Peerakorn &lt;Pete&gt; Sakunkaewphithak | LLDD-BE-Job-Batch-Email-SRM |

## 4. Workload Balance and Continuity

แผนนี้รวม owner ตามบุคคล (ล่าสุด 2026-09-02 — **batch job ทั้งหมดรวมที่คนเดียว**): ทีม 6 คน แบ่งเป็น FE 2 คน BE 4 คน · Peerakorn ย้ายจากสาย FE ไปสาย BE ตั้งแต่ 2026-08-07 · **Bank** ถือ **batch job ทั้ง 12 ฉบับ** (Job 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 8b) 211 ชม. · Vava 145 ชม. · Pete 139 ชม. · lin 123 ชม. · But 108 ชม. · New 103 ชม. · เอกสารฝั่ง Database Structure / Data Migration / Workflow Engine Definition **ไม่ได้อยู่กับ Bank แล้ว** — ย้ายไปกับเจ้าของสายนั้น ๆ

**กติกาเวลาทำงาน:** 1 สัปดาห์ = 5 วัน · 1 วัน = 8.5 ชม. (**42.5 ชม./สัปดาห์**) · กรอบส่งมอบ 4 สัปดาห์ = **170 ชม./คน** (ทีม 6 คน = 1020 ชม. เทียบงานจริง 829 ชม.) · 🔴 **ยังไม่ลงกรอบ:** **Bank 211 ชม. = 5.0 สัปดาห์** (เกินกรอบ 41 ชม.) — ต้องกระจาย batch job ออกไปหรือเลื่อนกำหนดส่ง (ข้อค้างใน `DECISIONS-รอตัดสินใจ.md`) · ประโยคที่บอกว่า "ย้ายงานแล้วจบใน 4 สัปดาห์" ยังไม่เป็นจริงตามตัวเลขนี้

| Role | Owner | ชั่วโมง (impl + unit test) | Work Focus |
| --- | --- | --- | --- |
| FE | Kittisak &lt;New&gt; Kaeowika | **103** (impl 82 + test 21) | FE หน้าจอเอกสาร (สายลึกที่สุดของ FE): Document Detail/Action (+ role pack 5 ฉบับ) -> Master Data -> Create Document |
| FE | Chidchanok &lt;lin&gt; Saengamnat | **123** (impl 104 + test 19) | FE ที่ต่อกับระบบเดิม: Integration Contracts (auth/session/permission จาก BFF) -> Foundation (sidebar/header/menu gating ของ portal เดิม) -> Document Lists -> Report -> Testing/Delivery |
| BE | Butsaba &lt;But&gt; Podamrong | **108** (impl 86 + test 22) | BE เอกสาร/สัญญากลางของ SGI เอง: Common Contracts -> List/Search -> Create/Update -> Detail Aggregate (ทุก job ย้ายไป Aphiwit แล้วตามมติ 2026-09-02) |
| BE | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | **145** (impl 125 + test 20) | BE ที่ต่อกับระบบเดิม + **เรียกใช้ engine**: Integration with SBP Platform -> Workflow Instances (initializeWorkflow) -> Workflow Actions (eventWorkflow = trigger event) -> Lookup |
| BE | Peerakorn &lt;Pete&gt; Sakunkaewphithak | **139** (impl 119 + test 20) | BE support/interface (ย้ายจากสาย FE 2026-08-07): Batch/Email -> Attachment/Sales/Timeline -> Report and Master Data |
| BE | Aphiwit &lt;Bank&gt; Khammoon | **211** (impl 159 + test 52) | **batch job ทั้งหมด 12 ฉบับ** (Jobs 2-12 + 8b · มติ 2026-09-02): Job 2, 3 (นำเข้า ALLMAP) -> Job 4, 5 (IAS/MIS ผ่าน EAI S3) -> Job 6 (ส่ง STA) + Job 11 (รับกลับจาก STA) -> Job 8, 8b (สร้างเอกสาร + เปิด workflow) -> Job 7, 9 (sync เข้าเอกสาร) -> Job 10, 12 (watchdog + เตือนงานค้าง) · **ไม่ถือ Database Structure / Data Migration / Workflow Engine Definition แล้ว** (ย้ายออกเมื่อ 2026-09-02 · ลดภาระจาก 309 เหลือ 211 ชม. (−98 ชม.) · **แต่ยังเกินกรอบ 4 สัปดาห์อยู่ 41 ชม.** = 5.0 สัปดาห์ — ยังต้องกระจาย job ออกไปอีกหรือเลื่อนกำหนดส่ง ดูข้อค้างใน `DECISIONS-รอตัดสินใจ.md`) |

## 5. FE Summary

| FE Topic | ชั่วโมง | ลำดับขั้น | Deliverable |
| --- | --- | --- | --- |
| Integration Contracts | 16 | 2 | Shared API client contract, Auth/JWT consumption from platform reference, Error display and validation message mapping |
| Application Foundation and Shared UI | 28 | 3 | Non-screen technical foundation, Route/module registry เฉพาะ SBP Mall, API client และ response typing |
| Document Lists | 28 | 4 | Waiting list, Related document list, Search/filter/status filter |
| Create Document | 6 | 4 | 🔴 **มติ 2026-08-06 — หน้านี้ไม่มีฟอร์มและไม่มีแท็บฝั่ง SBP**, main card = iframe ของหน้าสร้างเอกสารระบบ FS ตรง ๆ (เหมือน `k2-create.html`), หมายเหตุ 4 ขั้นตอน (verbatim จากหน้าจอ K2 เดิม) อยู่ใต้ iframe นอกกรอบ |
| Document Detail and Action | 60 | 4 | Document header, Store impact/new-store/factor sections, Role-based visible/editable sections |
| Status Summary Report | 20 | 4 | Report filters (SDD slide 60 · 2026-08-06: สถานะ*\|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ\|ประเภทร้าน (รหัสจาก common_code · ห้าม hardcode) · Period Statement From-To (date, ค.ศ.) เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว), Summary table (sortable 14 columns), ปุ่มออกผล 3 ตัว (Preview Report · Export Excel · Export CSV to Batch) |
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
| Database Structure and Deployment | 31 | 1 | DDL ครบ 20 ตารางของ target schema (โซน A 8 · โซน B 9 · โซน C 3), Index, unique/partial index, check constraint และ FK ที่ต้องมีก่อน SIT, Seed data ที่ต้องมีก่อนเปิดระบบ (sgi_external_factors · sgi_competitors) — decisions ไป seed ที่ common_code ของระบบเดิม (DP-9), สคริปต์ deploy/rollback ต่อ environment และลำดับการรันตาม dependency |
| Data Migration and Cutover | 43 | 2 | Source-to-target mapping ระดับตาราง/คอลัมน์ (ORA FCS_FRN · MSSQL CPA_FRN_FGI -> 20 ตาราง), การแปลงคีย์: polymorphic TRANSACTION_PK -> typed FK · CompDocumentID -> doc_no · IMPACT_PROCESS_ID -> impact_process_id, แผน cutover เป็นรอบ (dry-run -> delta -> freeze -> final) และ rollback, Reconcile: นับแถว ยอดเงิน และ checksum ต่อโซน |
| Integration with SBP Platform | 20 | 1 | ตัวตนผู้ใช้จาก BFF header 6 ตัว (x-api-key · x-user-id · x-user-group-id · x-user-full-name · x-user-permissions · accept-language) — ดูค่าตัวอย่างจริงใน 5.1, Response envelope ของ store-backend: {success, data} / {success:false, data:null, error:{code,message}}, ไฟล์แนบผ่าน service S3 เดิม (POST /statement/upload-file-aws · download-file-aws), อีเมลผ่าน @gosoft-sbp/email-lib + ตาราง email_template / email_sent |
| Workflow Engine Definition | 24 | 1 | ลงทะเบียน workflow version ของ SGI 1 version (url_main + url_param_mapping), **ผลลัพธ์ที่ส่งมอบคือ seed script/มัยเกรชันของข้อมูลนิยาม** ไม่ใช่โค้ดเรียก engine — ทีมอื่นเรียก engine ต่อจากนิยามชุดนี้, **จำนวน step ที่ต้องสร้าง = 6 state** — 5 ขั้นทำงาน (`06` รอฝ่าย SBP DSA → `08` รอเจ้าหน้าที่ SBP DSA → `01` รอหน่วยงานส่งเสริมธุรกิจ SBP → `02` รอ GM → `03` รอ AVP) + **1 state จบ** (`99` เสร็จสิ้นดำเนินการ) · `state_id` เป็น running ตาม version ตามกติกาของ engine (v1 → 10001+), **จำนวน route ที่ต้องสร้าง = 12 เส้น** ตาม Canonical Workflow Transition Matrix ใน `LLDD-BE-API-Document-Workflow-Actions` §5.1 (รวมเส้นข้ามขั้น 06→01 · เส้นจบทันทีเมื่อ เห็นควรไม่ชดเชย ที่ 01/02 · เส้นแตกตามวงเงิน 100,000 ที่ 02 และเส้นส่งกลับ) |
| API Common Contracts | 18 | 2 | Base URL, content type, charset and request tracing, Auth/JWT platform validation and service-token exception, Standard success envelopes for list/detail/mutation, Standard error envelope and HTTP status mapping |
| API Document List and Search | 20 | 3 | Inbox tasks API, Document search API, Pagination, Status/year filter |
| API Document Create and Update | 24 | 3 | Create document, Duplicate guard, Running doc number, Partial update |
| API Document Detail Aggregate | 24 | 3 | Document aggregate query, Role profile output, Store impact/new-store/factor mapping, Compensation summary |
| API Document Workflow Actions | 28 | 3 | Submit action, Action owner guard, Amount threshold reference, Send back result |
| Workflow Engine and API Workflow Instances | 24 | 3 | Internal Workflow Engine API only, No FE screen and no Flow page work, Gen Flow Gate W/Y/N owner, Require compensation document created by Job 8 |
| API Attachment Sales and Timeline | 26 | 3 | Attachment metadata, Upload/download adapter, Sales 4 windows, Timeline query |
| API Lookup | 10 | 3 | Lookup APIs, Auth endpoints are platform reference only |
| API Report and Master Data | 30 | 3 | Report query service, Excel export (14 columns, SDD slide 60), Operator/factor CRUD, Report filters |
| Job Batch and Email Integration | 8 | 2 | Interface tracking และรายการค้างส่ง APIs (2 เส้น · `/tracking` · `/pending-ack`), Notification adapter ผ่าน @gosoft-sbp/email-lib, **ไม่มี STA ACK callback** — ตัดเมื่อ 2026-09-08 (ข้อ 2.13) เพราะสเปก STA ไม่มี ACK แบบ HTTP, ไม่มี Batch Job Admin API และไม่มี inbound endpoint ของ SRM |

## 8. BE Batch Job Breakdown

| Job | ชั่วโมง | ลำดับขั้น | Owner | เอกสารรายละเอียด |
| --- | --- | --- | --- | --- |
| Job 2 ImportImpactStore | 15 | 3 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-2-ImportImpactStore |
| Job 3 ImportImpactCompetitor | 9 | 4 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-3-ImportImpactCompetitor |
| Job 4 PrepareImpactStoreToIAS | 13 | 4 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-4-PrepareImpactStoreToIAS |
| Job 5 ImportImpactSaleFromIAS | 13 | 5 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-5-ImportImpactSaleFromIAS |
| Job 6 ExportImpactStoreToFS | 24 | 4 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-6-ExportImpactStoreToFS |
| Job 7 SyncCompetitorToDocument | 9 | 6 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-7-SyncCompetitorToDocument |
| Job 8 CreateCompensationDocument | 17 | 5 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-8-CreateCompensationDocument |
| Job 8b StartInternalWorkflow | 21 | 6 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-8b-StartInternalWorkflow |
| Job 9 SyncNewStoreToDocument | 10 | 6 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-9-SyncNewStoreToDocument |
| Job 10 NotifyNoReceiveData | 6 | 5 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-10-NotifyNoReceiveData |
| Job 11 ConsumeStaCompensate | 12 | 5 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-11-ConsumeStaCompensate |
| Job 12 NotifyPendingWork | 10 | 7 | Aphiwit &lt;Bank&gt; Khammoon | LLDD-BE-Job-12-NotifyPendingWork |

## 9. Dependency

| Dependency | Owner | ใช้โดย |
| --- | --- | --- |
| Common API/FE contracts | BE/FE | LLDD-BE-API-Common-Contracts และ LLDD-FE-Integration-Contracts เป็นสัญญากลางของทุกหน้า FE และทุก service BE |
| API contract | BE/FE | ทุกหน้า FE และทุก service BE |
| Master Data contract | FE/BE | LLDD-FE-Master-Data ใช้ LLDD-BE-API-Report-and-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง (ไม่มี Operator/Menu Permission/System Config/Audit แล้ว — ใช้ระบบ SBP เดิม) |
| Blocker ลำดับขั้นที่ 1 | BE | LLDD-BE-Integration-SBP-Platform, LLDD-BE-Workflow-Engine-Definition, LLDD-BE-Database-Structure และสัญญากลางของ LLDD-API ต้องปิดก่อน เพราะเอกสาร BE ทุกฉบับอ้างอิง 4 ชิ้นนี้ |
| Auth/JWT platform และ menu service | Platform/SSO/IAM | FE Foundation เรียก /auth/profile + /users/current + /menus + /groups/current-user/permissions ของระบบเดิม; SGI รับตัวตนจาก BFF ผ่าน header x-api-key/x-user-id/x-user-group-id/x-user-permissions |
| Mock/fixture data | BE | FE development และ SIT |
| Screenshots/prototype | FE | UI implementation |
| Business rules | BA/BE | validation/action/report |

## 10. Deliverable Checklist

- Main LLDD Index
- Common contract LLDD สำหรับ API/FE integration
- LLDD-FE-Master-Data สำหรับปัจจัยภายนอกและรายชื่อคู่แข่ง
- Detailed FE LLDD per SBP Mall page group
- Detailed BE LLDD per SBP Mall API group and Jobs 2, 3, 4, 5, 6, 7, 8, 8b, 9, 10, 11, 12 (รวม 12 job)
- Database Structure, Data Migration/Cutover, Integration with SBP Platform และ Workflow Engine Definition (เพิ่ม 2026-08-07)
- Screenshots embedded only for SBP Mall implementation pages
- Implementation flow diagrams embedded as reference, not Flow page deliverables
