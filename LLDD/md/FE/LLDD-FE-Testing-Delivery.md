# LLDD FE - Testing and Delivery

SBP Mall - ระบบประกันรายได้ | Low Level Design Document

## 1. Overview

| รายการ | รายละเอียด |
| --- | --- |
| Track | FE |
| Estimate | 24 ชั่วโมง |
| Owner | Peerakorn <Pete> Sakunkaewphithak |
| Document type | FE verification and release handover specification; not an application screen |
| Objective | กำหนด regression, responsive pass, API payload adjustment และ delivery note สำหรับ FE |

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
| FE-REPORT | required filters, 19 columns, totals, CSV parity | known report fixture and expected aggregate | query snapshot, row count, totals and exported checksum |
| FE-ADMIN | SCR-08/09/10/11 plus email template | admin role and reversible test data | before/after values and audit reference |
| FE-BATCH | job selection, editable params, locked params, run history | job metadata/run fixtures | request/response capture and UI state |
| FE-RESP | desktop 1440, tablet 768, mobile 390 | latest supported browsers | page checklist with overflow/modal/navigation result |

## 4. Environment and Fixture Contract

| Item | Required content | Control |
| --- | --- | --- |
| Build identity | commit SHA, build number, deploy timestamp | freeze before regression |
| API identity | base URL and contract version | no production credentials in evidence |
| Role users | one account per tested RBAC role/profile | masked identifiers in shared evidence |
| Document fixtures | docNo per current section plus <=100,000 and >100,000 cases | resettable or uniquely generated |
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
| 6 | action transition 06→08→01→02→03→99 |
| 7 | delivery evidence ไม่มี token/secret |
