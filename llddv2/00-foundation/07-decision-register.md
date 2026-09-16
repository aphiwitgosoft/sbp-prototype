# Foundation 07 — Decision Register

> Document status: `Blocked` · ปรับปรุงล่าสุด 2026-09-15

## ต้องทำอะไร และเสร็จแล้วได้อะไร

รายการนี้เป็นประตูบังคับ: เมื่อหลักฐานขัดกันหรือ code มี default ที่ยังไม่รับรอง ให้ผูก Decision ID และห้าม implement/เปลี่ยน production config โดยเดา ปิดข้อได้เมื่อมี owner, วันที่, คำตอบ, เหตุผล และผลกระทบต่อ doc/code/test/migration

## Open decisions

| ID | เรื่อง | สถานะ/ค่าที่ code ใช้ปัจจุบัน | ผู้ตัดสิน | กระทบ |
|---|---|---|---|---|
| D-001 | ที่เก็บ `SGI_APPROVE_LIMIT` และ precedence | requirement = 100,000; lookup จะคืน `approveLimitAmount` | Business + Workflow + BE | route 02→03, lookup, test |
| D-002 | canonical parameter table/key | ตารางระบบเดิมชื่อ `mas_param`; key/seed/owner บางตัวยังไม่รับรอง | DBA + Platform | migration/config |
| D-003 | `SGI_DATASOURCE`/`data_source` ใช้ `ALM` หรือ `ALLMAP` | Batch source row ใช้ `ALM`; document `source_system` ใช้ `ALLMAP` | Data owner | Jobs 2/7/9, prune safety |
| D-004 | workflow definition, version IDs, status/event mapping | code บังคับ `SGI_WORKFLOW_VERSION_IDS` ใน production | Workflow owner | Job 8b/12, API action |
| D-005 | Job 11 deployment/consume model | TypeScript เป็น Rabbit consumer ที่ออกเมื่อ idle | Infra + STA | scaling, ack, duplicate |
| D-006 | email sender/template/recipient ownership | ใช้ shared email lib;หลาย template/group id เป็น env | Business + Platform | Jobs 10/12/failure/action |
| D-007 | `sgi_fgi_impact_processes.process_status` initial/domain | Job 2 default `IMPORTED` | Business + Data | Jobs 2/8, migration |
| D-008 | IAS exact file contract | Job 4 UTF-8 LF no trailing newline; Job 5 Windows-874 | IAS owner | Jobs 4/5 E2E |
| D-009 | STA unknown new store/closed document policy | Job 11 default DLQ unknown; closed=`update` | Business + STA | money consistency |
| D-010 | reminder day/count tiers | Job 12 `TIERED`, 30/45/60 business days | Business/Operations | escalations |
| D-011 | trusted BFF→BE user headers/signature | names proposed, SGI BE absent | Security + BFF + BE | all user APIs |
| D-012 | AWS Batch dependency/schedule/resource policy | cron defaults are reference only | Infra + Batch | all Jobs |
| D-013 | download attachment while scan `PENDING` | proposed `SGI_ALLOW_PENDING_DOWNLOAD` | Security + Business | attachment API |
| D-014 | migration cleanup/out-of-domain records | known duplicate/legacy anomalies | Business + DBA | cutover |

## Confirmed decisions

| ID | คำตอบ | หลักฐาน |
|---|---|---|
| C-001 | base path `/api/v1/sgi`; 28 endpoints / 6 groups | `plan-api.html`, `api.md` |
| C-002 | 20 new tables + reuse `fcs_qssi_score`; schema `sps_store` | generated DDL/database docs |
| C-003 | FE/BFF/BE SGI ยังไม่มี implementation; ต้องระบุ `TO-BE` | repo scan 2026-09-15 |
| C-004 | Batch Jobs 2–12 + 8b มี TypeScript services และ tests | `src/modules/sgi/README.md` + source |
| C-005 | STA ไม่มี HTTP ACK; `pending-ack` หมายถึง publisher confirm | STA message spec + API decision 2026-09-08 |
| C-006 | Job 11 ไม่มี Java เดิม; เป็น target integration ใหม่ | search `batchjob/fcsJar/src/` |
| C-007 | ALLMAP `PERIOD_YEAR` legacy เป็น ค.ศ. | Java audit + Oracle historical data |
| C-008 | Workflow `referenceId` ใช้ document surrogate id เป็น string | workflow decision DP-1 |

## วิธีปิด Decision

เพิ่มบันทึก `คำตอบ`, `owner`, `approvedAt`, `evidence`, `effective environment`, `migration/backfill`, `tests changed` แล้วย้ายแถวไป Confirmed ห้ามลบประวัติ และปรับทุกเอกสารที่อ้าง ID เดียวกันใน commit/PR เดียว

รายการละเอียดกว่านี้ยังอยู่ใน `DECISIONS-รอตัดสินใจ.md` และ `batchjob/JOB-02-12-ข้อตัดสินใจที่ไม่มีของเดิมให้ลอก.md`; LLDDv2 รวมเฉพาะ decision ที่เป็น release gate ของ contract ชุดนี้

