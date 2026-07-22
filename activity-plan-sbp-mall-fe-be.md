# Activity Plan เฉพาะระบบประกันรายได้ (SBP Mall) - FE และ BE

วันที่จัดทำ: 2026-07-19  
อ้างอิง: `estimate-sbpgi-project-hours.md`  
Scope: เฉพาะระบบประกันรายได้ (SBP Mall)  
ไม่รวม: Login/Auth, Flow pages, Database design/pages, Plan pages/documents, data migration, production HA infrastructure, security pentest ภายนอก

## หลักการวางแผน

- 1 วันทำงาน = 8.5 ชั่วโมง
- ปรับเวลาให้อยู่ในช่วง 5 weeks / 25 working days
- FE รวม 510 ชั่วโมง หรือ 60 วัน (effort baseline)
- BE รวม 595 ชั่วโมง หรือ 70 วัน (effort baseline)
- Shared QA/UAT/Coordination รวม 102 ชั่วโมง หรือ 12 วัน
- Activity ย่อยทุกแถวไม่เกิน 16 ชั่วโมง ยกเว้นแถว Total
- FE และ BE ทำงาน parallel ได้ โดยต้อง sync API contract ตั้งแต่ต้น และ target ปิดงานภายใน 29/07/2026 - 01/09/2026

## Phase Summary

| Phase | ช่วงงาน | FE ชั่วโมง | BE ชั่วโมง | Output หลัก |
|---|---|---:|---:|---|
| P1 | Foundation | 60 | 70 | Scope lock, module foundation, API contract, mock data |
| P2 | Dashboard | 55 | 50 | Dashboard UI + APIs |
| P3 | Document Lists | 70 | 0 | Waiting/related/abnormal lists |
| P4 | Document Core | 140 | 175 | Create/detail/actions/history/attachment |
| P5 | Report | 50 | 65 | Report filter, summary, preview, export |
| P6 | Master/Config | 60 | 80 | Operator, factor, permission, system config |
| P7 | Batch/Email | 40 | 85 | Batch monitor, job adapter/mock, email template |
| P8 | Testing & Delivery | 35 | 70 | Regression, SIT/UAT fixes, handover |
| **รวม** |  | **510** | **595** |  |

## FE Activity Plan

| ID | Activity | Deliverable | Dependency | ชั่วโมง |
|---|---|---|---|---:|
| FE-01 | Confirm SBP Mall screen scope และ exclusions | Confirmed FE scope | Kickoff | 8 |
| FE-02 | Review prototype layout และ reusable UI pattern | UI pattern checklist | FE-01 | 8 |
| FE-03 | Setup routes/modules เฉพาะ SBP Mall | Route map | FE-01 | 8 |
| FE-04 | Setup API client reuse และ response typing | API client/types baseline | API draft | 10 |
| FE-05 | Prepare shared constants, menu mapping, mock data mapping | Constants/mock mapping | FE-03 | 12 |
| FE-06 | Prepare CSS/tokens สำหรับ table/form/modal/responsive | Shared CSS/tokens | FE-02 | 14 |
| FE-07 | Build KPI cards | Dashboard KPI cards | Dashboard contract | 12 |
| FE-08 | Build task summary และ pending queue block | Task summary UI | FE-07 | 10 |
| FE-09 | Build monthly compensation chart | Monthly chart | FE-07 | 10 |
| FE-10 | Build pending status chart | Status chart | FE-07 | 8 |
| FE-11 | Add loading/empty/error states | Dashboard states | FE-07 to FE-10 | 8 |
| FE-12 | Responsive verification และ data sync check | Dashboard verified | FE-07 to FE-11 | 7 |
| FE-13 | Build waiting document list page | Waiting list UI | List contract | 14 |
| FE-14 | Build related document list page | Related list UI | FE-13 | 12 |
| FE-15 | Build abnormal document list placeholder | Abnormal placeholder | FE-13 | 10 |
| FE-16 | Implement search/filter/status filter | Filter behavior | FE-13 to FE-15 | 10 |
| FE-17 | Implement pagination และ export action | List pagination/export | FE-16 | 8 |
| FE-18 | Implement row action และ link to detail | Detail navigation | FE-17 | 8 |
| FE-19 | Manual verification สำหรับ list scenarios | List verification notes | FE-13 to FE-18 | 8 |
| FE-20 | Build create document form shell | Create form shell | Document contract | 14 |
| FE-21 | Build create form main sections | Create form sections | FE-20 | 14 |
| FE-22 | Add validation, draft, save, submit UI | Create actions | FE-21 | 14 |
| FE-23 | Build document detail header และ summary | Detail header | Detail contract | 12 |
| FE-24 | Build store/vendor/contract detail sections | Detail sections | FE-23 | 12 |
| FE-25 | Build compensation/calculation display | Compensation block | FE-23 | 14 |
| FE-26 | Build action panel: approve/reject/return/comment | Action panel | Action contract | 12 |
| FE-27 | Add confirm dialog, toast, action result state | Action UX states | FE-26 | 12 |
| FE-28 | Build history/timeline/audit display | History UI | FE-23 | 10 |
| FE-29 | Build attachment upload/download UI | Attachment UI | FE-23 | 10 |
| FE-30 | Add attachment error/retry state | Attachment states | FE-29 | 10 |
| FE-31 | Scenario verification สำหรับ create/detail/action | Scenario notes | FE-20 to FE-30 | 6 |
| FE-32 | Build report filters และ search/reset | Report filter UI | Report contract | 10 |
| FE-33 | Build report summary table | Report table | FE-32 | 10 |
| FE-34 | Build preview/detail modal | Report modal | FE-33 | 8 |
| FE-35 | Implement export action | Export action | FE-33 | 8 |
| FE-36 | API integration และ sample data verification | Report verified | FE-32 to FE-35 | 8 |
| FE-37 | Responsive/manual test | Report QA notes | FE-32 to FE-36 | 6 |
| FE-38 | Build operator master page | Operator master UI | Master contract | 12 |
| FE-39 | Build external factor master page | Factor master UI | FE-38 pattern | 10 |
| FE-40 | Build menu permission page | Permission UI | FE-38 pattern | 10 |
| FE-41 | Build system config page | Config UI | FE-38 pattern | 10 |
| FE-42 | Add validation และ modal add/edit/delete | CRUD behavior | FE-38 to FE-41 | 8 |
| FE-43 | Add audit display และ API integration | Master integration | FE-42 | 6 |
| FE-44 | Manual verification master/config | Master QA notes | FE-38 to FE-43 | 4 |
| FE-45 | Build Batch Job monitor list | Batch monitor UI | Batch contract | 10 |
| FE-46 | Build job history และ log/detail modal | Job detail UI | FE-45 | 8 |
| FE-47 | Add retry/re-run state และ confirmation | Batch action UI | FE-46 | 8 |
| FE-48 | Build Email Template list/edit/preview | Email template UI | Email contract | 8 |
| FE-49 | Build notification config | Notification UI | FE-48 | 6 |
| FE-50 | Manual regression รอบหลัก | Regression notes | All FE pages | 8 |
| FE-51 | Responsive pass หน้าหลักทั้งหมด | Responsive fixes | All FE pages | 8 |
| FE-52 | API payload adjustment reserve | Payload fixes | API changes | 8 |
| FE-53 | UAT fixes reserve | UAT fixes | UAT feedback | 6 |
| FE-54 | Build check และ delivery note | FE delivery note | FE-50 to FE-53 | 5 |
| **FE Total** |  |  |  | **510** |

## BE Activity Plan

| ID | Activity | Deliverable | Dependency | ชั่วโมง |
|---|---|---|---|---:|
| BE-01 | Confirm SBP Mall API scope และ exclusions | Confirmed BE scope | Kickoff | 10 |
| BE-02 | Draft API contract สำหรับ FE alignment | API contract draft | BE-01 | 10 |
| BE-03 | Setup module/controller/service structure | BE module skeleton | BE-01 | 8 |
| BE-04 | Setup validation pattern | Validation baseline | BE-03 | 8 |
| BE-05 | Setup error response และ logging | Error/logging baseline | BE-03 | 8 |
| BE-06 | Connect existing schema หรือ mock repository | Repository baseline | BE-03 | 8 |
| BE-07 | Prepare fixture/seed data | Test fixtures | BE-06 | 8 |
| BE-08 | Prepare health check และ OpenAPI skeleton | Health/OpenAPI baseline | BE-02 | 10 |
| BE-09 | Build KPI summary API | KPI API | BE-06 | 10 |
| BE-10 | Build pending task/status summary API | Pending API | BE-09 | 10 |
| BE-11 | Build monthly compensation chart API | Monthly chart API | BE-09 | 8 |
| BE-12 | Build status chart data API | Status chart API | BE-09 | 8 |
| BE-13 | Add query/service tests | Dashboard tests | BE-09 to BE-12 | 8 |
| BE-14 | Prepare contract examples for FE | Dashboard examples | BE-09 to BE-12 | 6 |
| BE-15 | Build document search/list endpoints | Document list APIs | BE-06 | 14 |
| BE-16 | Build create/update document endpoints | Create/update APIs | BE-15 | 14 |
| BE-17 | Build document detail aggregate endpoint | Detail API | BE-15 | 14 |
| BE-18 | Implement store/vendor/contract mapping | Detail mapping | BE-17 | 12 |
| BE-19 | Implement compensation data mapping | Compensation mapping | BE-17 | 12 |
| BE-20 | Build submit action endpoint | Submit API | BE-16 | 12 |
| BE-21 | Build approve/reject action endpoints | Approve/reject APIs | BE-20 | 12 |
| BE-22 | Build return/comment action endpoints | Return/comment APIs | BE-20 | 12 |
| BE-23 | Implement status transition guard | Transition guard | BE-20 to BE-22 | 10 |
| BE-24 | Implement history/audit record | Audit/history data | BE-21 to BE-22 | 10 |
| BE-25 | Build attachment metadata endpoints | Attachment metadata APIs | BE-17 | 10 |
| BE-26 | Build file upload/download adapter | File adapter | BE-25 | 12 |
| BE-27 | Implement validation และ business rules | Business rule layer | BE-16 to BE-26 | 12 |
| BE-28 | Implement duplicate/idempotency guard | Idempotency handling | BE-27 | 10 |
| BE-29 | Add integration/negative/regression tests | Document tests | BE-15 to BE-28 | 9 |
| BE-30 | Build report filter/search API | Report search API | BE-06 | 12 |
| BE-31 | Build report summary data API | Report summary API | BE-30 | 10 |
| BE-32 | Build preview/detail data API | Report detail API | BE-31 | 10 |
| BE-33 | Build export CSV data preparation | Export service | BE-31 | 8 |
| BE-34 | Query optimization | Optimized queries | BE-30 to BE-33 | 8 |
| BE-35 | Add report regression tests | Report tests | BE-30 to BE-34 | 8 |
| BE-36 | Prepare report contract examples | Report examples | BE-30 to BE-33 | 9 |
| BE-37 | Build operator master APIs | Operator APIs | BE-06 | 12 |
| BE-38 | Build external factor APIs | Factor APIs | BE-37 pattern | 10 |
| BE-39 | Build menu permission APIs | Permission APIs | BE-37 pattern | 10 |
| BE-40 | Build system config APIs | Config APIs | BE-37 pattern | 10 |
| BE-41 | Add validation | Master validation | BE-37 to BE-40 | 8 |
| BE-42 | Add pagination/search | Master search behavior | BE-37 to BE-40 | 8 |
| BE-43 | Add audit trail | Master audit | BE-37 to BE-40 | 8 |
| BE-44 | Add unit/integration tests | Master tests | BE-37 to BE-43 | 8 |
| BE-45 | Prepare examples for FE | Master examples | BE-37 to BE-40 | 6 |
| BE-46 | Build Batch monitor APIs | Batch monitor API | BE-06 | 12 |
| BE-47 | Build job history APIs | Job history API | BE-46 | 10 |
| BE-48 | Build log/detail APIs | Job log API | BE-47 | 10 |
| BE-49 | Build retry/re-run trigger APIs | Batch action API | BE-48 | 10 |
| BE-50 | Build job runner adapter/mock | Job adapter/mock | BE-46 | 8 |
| BE-51 | Implement file/status/failure handling | Batch state handling | BE-50 | 8 |
| BE-52 | Build Email Template CRUD APIs | Email template APIs | BE-06 | 8 |
| BE-53 | Build email preview/render service | Email preview service | BE-52 | 8 |
| BE-54 | Build notification send adapter/mock | Notification adapter | BE-53 | 6 |
| BE-55 | Add batch/email tests | Batch/email tests | BE-46 to BE-54 | 5 |
| BE-56 | API contract check | Contract review notes | All BE APIs | 12 |
| BE-57 | Security/input validation review | Validation review notes | All BE APIs | 12 |
| BE-58 | Log/error code review | Logging review notes | All BE APIs | 10 |
| BE-59 | SIT support และ bug fixing | SIT fixes | SIT feedback | 10 |
| BE-60 | Business rule/payload change reserve | Change reserve | Change request | 8 |
| BE-61 | Batch/email edge case reserve | Edge case reserve | SIT/UAT feedback | 8 |
| BE-62 | UAT feedback reserve | UAT fixes | UAT feedback | 6 |
| BE-63 | Deployment note และ handover note | BE handover note | BE-56 to BE-62 | 4 |
| **BE Total** |  |  |  | **595** |

## Shared Activity Plan

| ID | Activity | Deliverable | Dependency | ชั่วโมง |
|---|---|---|---|---:|
| SH-01 | Scope confirmation เฉพาะ SBP Mall และตัดรายการที่ไม่รวม | Confirmed scope | Kickoff | 10 |
| SH-02 | FE/BE API contract alignment สำหรับ dashboard/document | API agreement part 1 | SH-01 | 12 |
| SH-03 | FE/BE API contract alignment สำหรับ report/master/batch/email | API agreement part 2 | SH-02 | 12 |
| SH-04 | Test scenario preparation สำหรับ dashboard/document | Test scenarios part 1 | SH-02 | 10 |
| SH-05 | Test scenario preparation สำหรับ report/master/batch/email | Test scenarios part 2 | SH-03 | 12 |
| SH-06 | SIT execution support รอบแรก | SIT result round 1 | FE/BE ready | 12 |
| SH-07 | Defect triage และ retest coordination | Defect log/retest status | SH-06 | 10 |
| SH-08 | UAT support | UAT issue log | SIT pass | 8 |
| SH-09 | Release checklist | Release checklist | UAT pass | 8 |
| SH-10 | UAT/coordination reserve | Reserve usage log | As needed | 8 |
| **Shared Total** |  |  |  | **102** |

## Dependency Plan

| Dependency | Owner | ต้องเสร็จก่อน | ใช้โดย |
|---|---|---|---|
| Scope เฉพาะ SBP Mall | BA/Lead | FE-03, BE-03 | ทุก activity |
| API contract draft | BE/FE | FE-04, BE-09 | Dashboard/List/Document/Report/Master/Batch/Email |
| Mock/fixture data | BE | FE-07, FE-13, FE-20, FE-32 | FE development และ SIT |
| Reusable FE table/form/modal pattern | FE | FE-13, FE-20, FE-32, FE-38, FE-45 | หน้าจอหลักทั้งหมด |
| Document APIs | BE | FE-13, FE-20, FE-23 | Document list/create/detail/action |
| Report APIs | BE | FE-32 | Report |
| Master/Config APIs | BE | FE-38 | Master/Config |
| Batch/Email APIs | BE | FE-45, FE-48 | Batch/Email |

## Suggested Timeline แบบ Parallel

| ช่วงเวลา | FE Focus | BE Focus | Shared Focus |
|---|---|---|---|
| Week 1 | Kickoff, integration contracts, foundation | API contract, common contracts, workflow baseline | Scope/API alignment |
| Week 2 | Overview, document lists, create document | Dashboard, list/search, workflow instances | Test scenario draft |
| Week 3 | Document detail and action, report | Create/update, detail aggregate, attachment | API issue sync |
| Week 4 | Master/config, batch monitor | Workflow actions, lookup/RBAC/email, report master | SIT preparation |
| Week 5 | Email template, testing, delivery | Job batch/email/SRM, jobs 1-10/8b, final fix | SIT/UAT/release checklist |

## Acceptance Criteria

- FE pages เฉพาะ SBP Mall เปิดใช้งานได้ครบตาม scope
- FE ไม่มีการทำหน้า Login/Auth, Flow, Database, Plan
- BE APIs รองรับ dashboard, document, report, master/config, batch/email ตาม contract
- BE ไม่ทำ database design ใหม่ แต่ใช้ schema ที่มีอยู่หรือ mock repository ตาม scope
- Export, attachment, batch retry/log, email preview ทำงานได้ระดับ prototype-to-implementation ตาม contract
- SIT happy path ผ่านครบ dashboard/document/report/master/batch/email
- งานย่อยทุก activity ไม่เกิน 16 ชั่วโมง ยกเว้นแถว Total
