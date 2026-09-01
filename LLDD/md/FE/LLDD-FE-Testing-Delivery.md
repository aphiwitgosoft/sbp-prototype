# LLDD FE - Testing and Delivery

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | FE |
| Estimate | 12 ชั่วโมง (ไม่มี unit test แยก — ดูเหตุผลใน NO_UNIT_TEST_DOCS) |
| Owner | Chidchanok <lin> Saengamnat |
| Target repository | `SBP/srm-sps-spsap-web-frontend` (sbp-portal · Next.js · `NEXT_PUBLIC_APP_TARGET=sbpm`) — เรียก API ผ่าน `SBP/srm-sps-spsap-sbp-bff` เท่านั้น ห้ามยิง store-backend ตรง |
| Document type | FE verification and release handover specification; not an application screen |
| Objective | กำหนด regression, responsive pass, API payload adjustment และ delivery note สำหรับ FE |

### 1.1 เอกสาร LLDD ที่เกี่ยวข้อง

ตารางนี้สร้างจาก endpoint และตารางที่เอกสารฉบับนี้ประกาศไว้จริง — อ่านฉบับที่อยู่ในตารางก่อนลงมือ เพื่อไม่ให้สัญญา request/response หรือชื่อคอลัมน์หลุดจากกัน

| ความสัมพันธ์ | เอกสาร LLDD | เกี่ยวข้องตรงไหน |
| --- | --- | --- |
| สัญญากลาง | **LLDD-BE-API-Common-Contracts** | envelope `{success,data}` · error code · pagination · รูปแบบวันที่/เลขเอกสาร |
| สัญญากลาง | **LLDD-FE-Integration-Contracts** | API client · auth header · error mapping · RBAC/menu gating ฝั่ง FE |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Create-Document** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail-Role-01-Business-Promotion** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail-Role-03-AVP-SBP** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail-Role-06-SBP-DSA** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Document-Lists** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Foundation** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Integration-Contracts** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Master-Data** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |
| ต้องจบก่อน (ลำดับงาน) | **LLDD-FE-Report** | เป็นฉบับต้นทางของสัญญา/โครงที่ฉบับนี้อ้าง |

## 2. Delivery Scope

- Regression suites for Dashboard, document lists/create/detail/actions, report, master/config, batch monitor and email template
- Contract verification against the endpoint schemas embedded in each feature LLDD
- Responsive and browser checks for supported viewports
- UAT defect triage, retest evidence and release handover
- No screen route, UI field table or synthetic API endpoint is created by this work item

## 3. Test Suite Matrix

| Suite | Coverage | Entry condition | Required evidence |
| --- | --- | --- | --- |
| FE-SMOKE | app bootstrap, menus, dashboard, open list/detail | deploy reachable and test user available | timestamped run result and failed-step detail |
| FE-DOC | create, edit section, attachment, action, timeline and role views | fixture documents for sections 06/08/01/02/03 | case ID, docNo, requestId and screenshots for failures |
| FE-REPORT | required status filter, 14 columns (SDD slide 60), totals, Excel parity | known report fixture and expected aggregate | query snapshot, row count, totals and exported checksum |
| FE-MASTER | SCR-09 ปัจจัยภายนอก + รายชื่อคู่แข่ง (SCR-08/10/11 และ email template ตัดออกแล้ว) | admin role and reversible test data | before/after values |
| FE-BATCH | job selection, editable params, locked params, run history | job metadata/run fixtures | request/response capture and UI state |
| FE-RESP | desktop 1440, tablet 768, mobile 390 | latest supported browsers | page checklist with overflow/modal/navigation result |

## 4. Environment and Fixture Contract

| Item | Required content | Control |
| --- | --- | --- |
| Build identity | commit SHA, build number, deploy timestamp | freeze before regression |
| API identity | base URL and contract version | no production credentials in evidence |
| Role users | one account per tested RBAC role/profile | masked identifiers in shared evidence |
| Document fixtures | docNo per current section plus <100,000 (GM) and >=100,000 (AVP) cases per มติ 2026-08-18 | resettable or uniquely generated |
| File fixtures | valid type, >5MB, unsupported type, AV-blocked stub | checksum recorded |
| Job fixtures | SUCCESS/FAILED/RUNNING/QUEUED histories | read-only unless manual-run case |

## 5. Execution and Defect Flow

| Step | Action | Exit rule |
| --- | --- | --- |
| 1 | Record build/environment and run FE-SMOKE | all smoke cases pass before broad regression |
| 2 | Execute feature suites using fixed fixtures | each case has pass/fail and evidence reference |
| 3 | Log defects with severity, route, role, data key, steps and expected/actual | defect is reproducible or explicitly closed as non-reproducible |
| 4 | Retest fixes and run impacted regression | no Critical/High open; Medium has accepted disposition |
| 5 | Run responsive/browser matrix and release checklist | all mandatory cells pass |
| 6 | Produce handover summary | build identity, known limitations, evidence index and rollback note complete |

## 6. Release Gate

| Gate | Pass condition |
| --- | --- |
| Functional | All Critical/High feature and workflow cases pass |
| Contract | No request/response field mismatch against feature LLDD schema tables |
| Visual | No blocked action, clipped modal/table or unusable navigation at required viewports |
| Security | Unauthorized routes/actions fail closed; evidence contains no token/secret |
| Data | Report totals/export parity and action transitions reconcile with persisted result |
| Handover | Known limitations, rollback steps and test evidence index are complete |

## 7. Developer / QA Checklist

| No | Check |
| --- | --- |
| 1 | desktop regression ครบทุก route หลัก |
| 2 | tablet/mobile regression |
| 3 | request/response schema mismatch ต้องเป็นศูนย์ |
| 4 | Critical/High defects ต้องปิด |
| 5 | report preview/export parity |
| 6 | action transition 06→08→06→01→02→03→99 |
| 7 | delivery evidence ไม่มี token/secret |
