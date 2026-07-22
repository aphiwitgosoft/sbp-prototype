# Estimate Time เฉพาะระบบประกันรายได้ (SBP Mall)

วันที่จัดทำ: 2026-07-19  
แหล่งข้อมูลอ้างอิง: HTML prototype กลุ่มเมนู `ระบบประกันรายได้ (SBP Mall)`, `RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md`, `ประกันรายได้-K2-รายการหน้าจอ.md`

## เงื่อนไขการประเมิน

- ประเมินเฉพาะระบบประกันรายได้ (SBP Mall) เท่านั้น
- ไม่รวม Login/Auth
- ไม่รวมหน้า Flow และเอกสาร Flow
- ไม่รวมหน้า Database, database design, migration design และ ER diagram
- ไม่รวมหน้า Plan และเอกสาร plan/API/database/FE/BE plan
- 1 วันทำงาน = 8.5 ชั่วโมง
- ปรับเวลาประเมินให้อยู่ในช่วง 60-80 วัน
- เวลาประเมินจริง: FE = 510 ชั่วโมง หรือ 60 วัน, BE = 595 ชั่วโมง หรือ 70 วัน
- ประเมินสำหรับทีมที่มีประสบการณ์ และ reuse prototype, wording, layout, sample data และ business rule ที่มีอยู่แล้ว
- งานย่อยทุกแถวในตาราง FE/BE/Shared ไม่เกิน 16 ชั่วโมง
- แถวที่ขึ้นต้นด้วยคำว่า `รวม`, `Base Total`, `Grand Total` เป็น subtotal ไม่ใช่งานย่อย

## Scope ที่รวมใน SBP Mall

| กลุ่มงาน | หน้าจอ/ฟังก์ชันที่รวม |
|---|---|
| Dashboard | Overview, KPI, งานรอดำเนินการ, กราฟสรุป |
| เอกสารประกันรายได้ | สร้างเอกสาร, รายการรอดำเนินการ, รายการที่เกี่ยวข้อง, รายการผิดปกติ, รายละเอียดเอกสาร |
| การดำเนินการเอกสาร | ปุ่มดำเนินการตามสถานะหลัก, comment, history, attachment |
| รายงาน | รายงานสรุปสถานะ, filter, preview, export |
| Master/Config | กำหนดผู้ปฏิบัติงาน, ปัจจัยภายนอก, สิทธิ์การเข้าถึงเมนู, ตั้งค่าระบบ |
| Batch/Email | Batch Job monitor, job history, retry/log detail, Email Template |

## Scope ที่ไม่รวม

| ไม่รวม | เหตุผล |
|---|---|
| Login/Auth | ผู้ใช้ระบุว่าไม่ต้องทำ login |
| Flow pages | ไม่ทำหน้ากลุ่ม Flow หรือ diagram flow |
| Database pages/design | ไม่ทำ database document, ER diagram, schema design ใหม่ |
| Plan pages/document | ไม่ทำ plan pages เช่น plan-api, plan-database, plan-flow หรือเอกสาร plan |
| External production integration เต็มรูปแบบ | ประเมินเป็น adapter/mock contract ระดับที่พอให้ SBP Mall ทำงานได้ |
| Data migration | ไม่รวมย้ายข้อมูลจริง |
| Security pentest/HA infrastructure | นอก scope งาน application feature |

## สรุปรวม

| ส่วนงาน | Base estimate (ชั่วโมง) | Buffer (ชั่วโมง) | รวม (ชั่วโมง) | รวม (วัน x 8.5 ชม.) |
|---|---:|---:|---:|---:|
| FE React-Vite เฉพาะ SBP Mall | 475 | 35 | 510 | 60.0 |
| BE Node.js เฉพาะ SBP Mall | 525 | 70 | 595 | 70.0 |
| Shared QA / UAT / Coordination | 90 | 12 | 102 | 12.0 |
| **รวมทั้งหมด** | **1,090** | **117** | **1,207** | **142.0** |

หมายเหตุ: `Base estimate` คือเวลางานหลักก่อน reserve ส่วน `Buffer` คือเวลาสำรองสำหรับ regression, SIT/UAT fixes, payload/rule adjustment และ defect ที่พบระหว่างทดสอบ

## FE React-Vite Estimate

| Phase | งานย่อย | ชั่วโมง |
|---|---|---:|
| FE1 Foundation | Confirm SBP Mall screen scope และ exclusions | 8 |
| FE1 Foundation | Review prototype layout และ reusable UI pattern | 8 |
| FE1 Foundation | Setup routes/modules เฉพาะ SBP Mall | 8 |
| FE1 Foundation | Setup API client reuse และ response typing | 10 |
| FE1 Foundation | Prepare shared constants, menu mapping, mock data mapping | 12 |
| FE1 Foundation | Prepare CSS/tokens สำหรับ table/form/modal/responsive | 14 |
| **FE1 รวม** |  | **60** |
| FE2 Dashboard | Build KPI cards | 12 |
| FE2 Dashboard | Build task summary และ pending queue block | 10 |
| FE2 Dashboard | Build monthly compensation chart | 10 |
| FE2 Dashboard | Build pending status chart | 8 |
| FE2 Dashboard | Add loading/empty/error states | 8 |
| FE2 Dashboard | Responsive verification และ data sync check | 7 |
| **FE2 รวม** |  | **55** |
| FE3 Document Lists | Build waiting document list page | 14 |
| FE3 Document Lists | Build related document list page | 12 |
| FE3 Document Lists | Build abnormal document list placeholder | 10 |
| FE3 Document Lists | Implement search/filter/status filter | 10 |
| FE3 Document Lists | Implement pagination และ export action | 8 |
| FE3 Document Lists | Implement row action และ link to detail | 8 |
| FE3 Document Lists | Manual verification สำหรับ list scenarios | 8 |
| **FE3 รวม** |  | **70** |
| FE4 Create & Detail | Build create document form shell | 14 |
| FE4 Create & Detail | Build create form main sections | 14 |
| FE4 Create & Detail | Add validation, draft, save, submit UI | 14 |
| FE4 Create & Detail | Build document detail header และ summary | 12 |
| FE4 Create & Detail | Build store/vendor/contract detail sections | 12 |
| FE4 Create & Detail | Build compensation/calculation display | 14 |
| FE4 Create & Detail | Build action panel: approve/reject/return/comment | 12 |
| FE4 Create & Detail | Add confirm dialog, toast, action result state | 12 |
| FE4 Create & Detail | Build history/timeline/audit display | 10 |
| FE4 Create & Detail | Build attachment upload/download UI | 10 |
| FE4 Create & Detail | Add attachment error/retry state | 10 |
| FE4 Create & Detail | Scenario verification สำหรับ create/detail/action | 6 |
| **FE4 รวม** |  | **140** |
| FE5 Report | Build report filters และ search/reset | 10 |
| FE5 Report | Build report summary table | 10 |
| FE5 Report | Build preview/detail modal | 8 |
| FE5 Report | Implement export action | 8 |
| FE5 Report | API integration และ sample data verification | 8 |
| FE5 Report | Responsive/manual test | 6 |
| **FE5 รวม** |  | **50** |
| FE6 Master/Config | Build operator master page | 12 |
| FE6 Master/Config | Build external factor master page | 10 |
| FE6 Master/Config | Build menu permission page | 10 |
| FE6 Master/Config | Build system config page | 10 |
| FE6 Master/Config | Add validation และ modal add/edit/delete | 8 |
| FE6 Master/Config | Add audit display และ API integration | 6 |
| FE6 Master/Config | Manual verification master/config | 4 |
| **FE6 รวม** |  | **60** |
| FE7 Batch/Email | Build Batch Job monitor list | 10 |
| FE7 Batch/Email | Build job history และ log/detail modal | 8 |
| FE7 Batch/Email | Add retry/re-run state และ confirmation | 8 |
| FE7 Batch/Email | Build Email Template list/edit/preview | 8 |
| FE7 Batch/Email | Build notification config | 6 |
| **FE7 รวม** |  | **40** |
| FE8 Testing & Delivery | Manual regression รอบหลัก | 8 |
| FE8 Testing & Delivery | Responsive pass หน้าหลักทั้งหมด | 8 |
| FE8 Testing & Delivery | API payload adjustment reserve | 8 |
| FE8 Testing & Delivery | UAT fixes reserve | 6 |
| FE8 Testing & Delivery | Build check และ delivery note | 5 |
| **FE8 รวม** |  | **35** |
| **FE Grand Total** | 510 ชั่วโมง = 60 วัน | **510** |

## BE Node.js Estimate

| Phase | งานย่อย | ชั่วโมง |
|---|---|---:|
| BE1 Foundation | Confirm SBP Mall API scope และ exclusions | 10 |
| BE1 Foundation | Draft API contract สำหรับ FE alignment | 10 |
| BE1 Foundation | Setup module/controller/service structure | 8 |
| BE1 Foundation | Setup validation pattern | 8 |
| BE1 Foundation | Setup error response และ logging | 8 |
| BE1 Foundation | Connect existing schema หรือ mock repository | 8 |
| BE1 Foundation | Prepare fixture/seed data | 8 |
| BE1 Foundation | Prepare health check และ OpenAPI skeleton | 10 |
| **BE1 รวม** |  | **70** |
| BE2 Dashboard APIs | Build KPI summary API | 10 |
| BE2 Dashboard APIs | Build pending task/status summary API | 10 |
| BE2 Dashboard APIs | Build monthly compensation chart API | 8 |
| BE2 Dashboard APIs | Build status chart data API | 8 |
| BE2 Dashboard APIs | Add query/service tests | 8 |
| BE2 Dashboard APIs | Prepare contract examples for FE | 6 |
| **BE2 รวม** |  | **50** |
| BE3 Document APIs | Build document search/list endpoints | 14 |
| BE3 Document APIs | Build create/update document endpoints | 14 |
| BE3 Document APIs | Build document detail aggregate endpoint | 14 |
| BE3 Document APIs | Implement store/vendor/contract mapping | 12 |
| BE3 Document APIs | Implement compensation data mapping | 12 |
| BE3 Document APIs | Build submit action endpoint | 12 |
| BE3 Document APIs | Build approve/reject action endpoints | 12 |
| BE3 Document APIs | Build return/comment action endpoints | 12 |
| BE3 Document APIs | Implement status transition guard | 10 |
| BE3 Document APIs | Implement history/audit record | 10 |
| BE3 Document APIs | Build attachment metadata endpoints | 10 |
| BE3 Document APIs | Build file upload/download adapter | 12 |
| BE3 Document APIs | Implement validation และ business rules | 12 |
| BE3 Document APIs | Implement duplicate/idempotency guard | 10 |
| BE3 Document APIs | Add integration/negative/regression tests | 9 |
| **BE3 รวม** |  | **175** |
| BE4 Report APIs | Build report filter/search API | 12 |
| BE4 Report APIs | Build report summary data API | 10 |
| BE4 Report APIs | Build preview/detail data API | 10 |
| BE4 Report APIs | Build export CSV data preparation | 8 |
| BE4 Report APIs | Query optimization | 8 |
| BE4 Report APIs | Add report regression tests | 8 |
| BE4 Report APIs | Prepare report contract examples | 9 |
| **BE4 รวม** |  | **65** |
| BE5 Master/Config APIs | Build operator master APIs | 12 |
| BE5 Master/Config APIs | Build external factor APIs | 10 |
| BE5 Master/Config APIs | Build menu permission APIs | 10 |
| BE5 Master/Config APIs | Build system config APIs | 10 |
| BE5 Master/Config APIs | Add validation | 8 |
| BE5 Master/Config APIs | Add pagination/search | 8 |
| BE5 Master/Config APIs | Add audit trail | 8 |
| BE5 Master/Config APIs | Add unit/integration tests | 8 |
| BE5 Master/Config APIs | Prepare examples for FE | 6 |
| **BE5 รวม** |  | **80** |
| BE6 Batch/Email APIs | Build Batch monitor APIs | 12 |
| BE6 Batch/Email APIs | Build job history APIs | 10 |
| BE6 Batch/Email APIs | Build log/detail APIs | 10 |
| BE6 Batch/Email APIs | Build retry/re-run trigger APIs | 10 |
| BE6 Batch/Email APIs | Build job runner adapter/mock | 8 |
| BE6 Batch/Email APIs | Implement file/status/failure handling | 8 |
| BE6 Batch/Email APIs | Build Email Template CRUD APIs | 8 |
| BE6 Batch/Email APIs | Build email preview/render service | 8 |
| BE6 Batch/Email APIs | Build notification send adapter/mock | 6 |
| BE6 Batch/Email APIs | Add batch/email tests | 5 |
| **BE6 รวม** |  | **85** |
| BE7 Testing & Delivery | API contract check | 12 |
| BE7 Testing & Delivery | Security/input validation review | 12 |
| BE7 Testing & Delivery | Log/error code review | 10 |
| BE7 Testing & Delivery | SIT support และ bug fixing | 10 |
| BE7 Testing & Delivery | Business rule/payload change reserve | 8 |
| BE7 Testing & Delivery | Batch/email edge case reserve | 8 |
| BE7 Testing & Delivery | UAT feedback reserve | 6 |
| BE7 Testing & Delivery | Deployment note และ handover note | 4 |
| **BE7 รวม** |  | **70** |
| **BE Grand Total** | 595 ชั่วโมง = 70 วัน | **595** |

## Shared QA / UAT / Coordination

| งานย่อย | ชั่วโมง |
|---|---:|
| Scope confirmation เฉพาะ SBP Mall และตัดรายการที่ไม่รวม | 10 |
| FE/BE API contract alignment สำหรับ dashboard/document | 12 |
| FE/BE API contract alignment สำหรับ report/master/batch/email | 12 |
| Test scenario preparation สำหรับ dashboard/document | 10 |
| Test scenario preparation สำหรับ report/master/batch/email | 12 |
| SIT execution support รอบแรก | 12 |
| Defect triage และ retest coordination | 10 |
| UAT support | 8 |
| Release checklist | 8 |
| UAT/coordination reserve | 8 |
| **Shared Grand Total** | **102** |

## Calendar Duration ประมาณการ

| ทีม | Capacity สมมติ | ชั่วโมงรวม | ระยะเวลาประมาณ |
|---|---:|---:|---:|
| FE | 1 developer x 8.5 ชม./วัน | 510 | 60.0 working days |
| FE | 2 developers x 8.5 ชม./วัน | 510 | 30.0 working days |
| FE | 3 developers x 8.5 ชม./วัน | 510 | 20.0 working days |
| BE | 1 developer x 8.5 ชม./วัน | 595 | 70.0 working days |
| BE | 2 developers x 8.5 ชม./วัน | 595 | 35.0 working days |
| BE | 3 developers x 8.5 ชม./วัน | 595 | 23.3 working days |
| Shared | 1 QA/BA/PM capacity เฉลี่ย | 102 | 12.0 working days, ทำ overlap กับ FE/BE ได้ |

หมายเหตุ: แผน reschedule ล่าสุดใช้ 3 คนและ target window 29/07/2026 - 01/09/2026; ตารางนี้ยังคงแสดง effort baseline ต่อ track แยกกัน

## Milestone แนะนำ

| Milestone | Output หลัก | ชั่วโมงสะสมโดยประมาณ |
|---|---|---:|
| M1 Foundation | SBP Mall foundation, API contract, reusable UI/service pattern | 130 |
| M2 Dashboard & Lists | Dashboard, document lists, dashboard APIs | 337 |
| M3 Core Document | Create/detail/actions/history/attachment | 652 |
| M4 Report & Master | Report, export, master/config | 907 |
| M5 Batch & Email | Batch monitor, job adapter/mock, email template/notification | 1,032 |
| M6 SIT/UAT/Delivery | Regression, UAT fixes, release checklist | 1,207 |

## หมายเหตุสำคัญ

ตัวเลขนี้ตั้งใจให้เป็นแผนเฉพาะ SBP Mall และตัด login, Flow, Database, Plan ออกแล้ว ถ้าภายหลังต้องรวม authentication, database design, flow diagram pages, หรือ plan/document pages ให้ประเมินเพิ่มแยกต่างหาก
