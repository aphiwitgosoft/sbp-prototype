# LLDDv2 — ระบบประกันรายได้ SGI

> ชุดเอกสารนี้ยังไม่แทนที่ `LLDD/` จนกว่าทุกรายการที่จำเป็นจะเป็น Ready

## ต้องทำอะไร และเสร็จแล้วได้อะไร

เริ่มอ่านจาก Foundation แล้วเลือก Job หรือ Feature ที่จะพัฒนา เอกสารแต่ละฉบับบอก input, contract, DB, failure และ test จนครบเส้นทาง เมื่อปิด Decision ที่เกี่ยวข้องและผ่าน checklist แล้วจึงเลื่อนสถานะเป็น Ready

## ลำดับที่แนะนำให้ dev อ่าน

1. [แผนและกติกา](PLAN-LLDDV2.md)
2. [ภาพรวมระบบ](00-foundation/01-system-overview.md), [ศัพท์/กฎธุรกิจ](00-foundation/02-glossary-and-business-rules.md), [API security/error](00-foundation/03-api-security-and-error-contract.md)
3. [Database/migration](00-foundation/04-database-and-migration.md) และ [Workflow engine](00-foundation/05-workflow-engine.md)
4. Job ตาม [pipeline overview](jobs/00-job-pipeline-overview.md) หรือ Feature ที่รับผิดชอบ
5. Catalog ใน `references/` และ [Test/Delivery checklist](references/TEST-AND-DELIVERY.md)
6. เปิด [Decision Register](00-foundation/07-decision-register.md) ก่อน implement ทุกครั้ง

## สถานะ Foundation

| เอกสาร | สถานะ | หมายเหตุ |
|---|---|---|
| [01 System overview](00-foundation/01-system-overview.md) | Verified | ตรวจขอบเขตระบบและ journey แล้ว |
| [02 Glossary/business rules](00-foundation/02-glossary-and-business-rules.md) | Verified | canonical term และกฎหลัก |
| [03 API/security/error](00-foundation/03-api-security-and-error-contract.md) | Blocked | รอ D-011 header trust contract |
| [04 Database/migration](00-foundation/04-database-and-migration.md) | Blocked | DDL ผ่าน PostgreSQL test แต่ยังไม่ลองฐาน dev จริง |
| [05 Workflow engine](00-foundation/05-workflow-engine.md) | Blocked | D-004 workflow definition/version |
| [06 Integrations/operations](00-foundation/06-integrations-and-operations.md) | Blocked | external contract/template/schedule ยังมีข้อค้าง |
| [07 Decision register](00-foundation/07-decision-register.md) | Blocked | มี open decision |

## สถานะ Feature

ทุก Feature เป็น `TO-BE`: ตรวจ repo FE/BFF/BE เมื่อ 2026-09-15 แล้วไม่พบ module/route `/sgi`; ไฟล์ prototype เป็นเพียงหลักฐานหน้าจอ

| เอกสาร | สถานะ | API หลัก |
|---|---|---|
| [01 Worklist/search](features/01-worklist-and-document-search.md) | Draft | 1–2, 12–13 |
| [02 Creation pipeline](features/02-document-creation-pipeline.md) | Blocked | 4, 24–26 |
| [03 Detail/editing](features/03-document-detail-and-editing.md) | Draft | 3, 5 |
| [04 Actions/timeline](features/04-workflow-actions-and-timeline.md) | Blocked | 6–7, 24–26 |
| [05 Attachments/sales](features/05-attachments-and-sales-data.md) | Draft | 8–11 |
| [06 Master data](features/06-master-data.md) | Draft | 14–21 |
| [07 Report/export](features/07-status-report-and-export.md) | Draft | 22–23 |
| [08 Interface tracking](features/08-interface-tracking.md) | Draft | 27–28 |

## สถานะ Job

ทั้ง 12 ฉบับเป็น `AS-BUILT` จาก TypeScript ปัจจุบัน แต่มีค่า config/contract ที่ยัง `BLOCKED` จึงยังไม่มีฉบับใดเป็น Ready

| Job | เอกสาร | สถานะ | หลักฐาน code |
|---|---|---|---|
| 2 | [ImportImpactStore](jobs/JOB-02-ImportImpactStore.md) | Blocked | `job-2-import-impact-store.service.ts` |
| 3 | [ImportImpactCompetitor](jobs/JOB-03-ImportImpactCompetitor.md) | Blocked | `job-3-import-impact-competitor.service.ts` |
| 4 | [PrepareImpactStoreToIAS](jobs/JOB-04-PrepareImpactStoreToIAS.md) | Blocked | `job-4-prepare-impact-store-to-ias.service.ts` |
| 5 | [ImportImpactSaleFromIAS](jobs/JOB-05-ImportImpactSaleFromIAS.md) | Blocked | `job-5-import-impact-sale-from-ias.service.ts` |
| 6 | [ExportImpactStoreToSTA](jobs/JOB-06-ExportImpactStoreToSTA.md) | Blocked | `job-6-export-impact-store-to-sta.service.ts` |
| 7 | [SyncCompetitorToDocument](jobs/JOB-07-SyncCompetitorToDocument.md) | Blocked | `job-7-sync-competitor-to-document.service.ts` |
| 8 | [CreateCompensationDocument](jobs/JOB-08-CreateCompensationDocument.md) | Blocked | `job-8-create-compensation-document.service.ts` |
| 8b | [StartInternalWorkflow](jobs/JOB-08b-StartInternalWorkflow.md) | Blocked | `job-8b-start-internal-workflow.service.ts` |
| 9 | [SyncNewStoreToDocument](jobs/JOB-09-SyncNewStoreToDocument.md) | Blocked | `job-9-sync-new-store-to-document.service.ts` |
| 10 | [NotifyNoReceiveData](jobs/JOB-10-NotifyNoReceiveData.md) | Blocked | `job-10-notify-no-receive-data.service.ts` |
| 11 | [ConsumeStaCompensate](jobs/JOB-11-ConsumeStaCompensate.md) | Blocked | `job-11-consume-sta-compensate.service.ts` |
| 12 | [NotifyPendingWork](jobs/JOB-12-NotifyPendingWork.md) | Blocked | `job-12-notify-pending-work.service.ts` |

## Reference

| เอกสาร | สถานะ | จำนวน canonical |
|---|---|---|
| [API Catalog](references/API-CATALOG.md) | Verified | 28 endpoints / 6 groups |
| [Database Dictionary](references/DATABASE-DICTIONARY.md) | Verified | 20 new + 1 reuse |
| [Config/Env Catalog](references/CONFIG-AND-ENV-CATALOG.md) | Blocked | มีค่าที่รอ sign-off |
| [Error Catalog](references/ERROR-CATALOG.md) | Draft | API/FE/Batch mapping |
| [Test and Delivery](references/TEST-AND-DELIVERY.md) | Draft | automated + review gates |

## กติกาเปลี่ยนสถานะ

- Draft → Verified: owner ของเอกสารตรวจชื่อ identifier, link, contract และ test แล้ว
- Verified → Ready: ไม่มี `BLOCKED`, implementation owner ยืนยัน path และผู้ตรวจรับ FE/BFF/BE/Batch-DB/Business ลงชื่อส่วนที่เกี่ยวข้อง
- ถ้าพบข้อขัดแย้งใหม่ ให้ลดเป็น Blocked และเพิ่ม Decision ID ก่อนแก้เนื้อหา

