# LLDD Document Portal

เปิดหน้า portal ใน browser หรือใช้รายการลิงก์ด้านล่าง.

- Main index: [PDF](../pdf/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.pdf)
- Documents: 41
- Total estimate: 823 hours  (implementation 669 + unit test 154)
- Unit test: BE/Job 30% · FE 25% ของชั่วโมง implementation · เอกสารสัญญา/ออกแบบไม่คิดแยก (ดู NO_UNIT_TEST_DOCS)
- ขอบเขต 2026-08-07: ตัด `LLDD-FE-Overview` และ `LLDD-BE-API-Dashboard-Summary` · เพิ่ม `LLDD-BE-Database-Structure`, `LLDD-BE-Data-Migration-Cutover`, `LLDD-BE-Integration-SBP-Platform`, `LLDD-BE-Workflow-Engine-Definition` · เปลี่ยนชื่อ `FE-Master-Config` -> `FE-Master-Data`, `BE-API-Lookup-RBAC-Email` -> `BE-API-Lookup`, `BE-API-Report-Master-Config` -> `BE-API-Report-and-Master-Data`
- ขอบเขต 2026-08-06: ตัด `LLDD-FE-Batch-Monitor` และ `LLDD-FE-Email-Template` ออกจากชุดส่งมอบ — หน้า Global Config/Email Template ลบทั้งฟีเจอร์ (ใช้ `mas_param`/`email_template` ของระบบ SBP เดิม) และหน้า Batch Job ย้ายไปกลุ่มเมนู Flow เหลือเฉพาะ Flowchart + Database ที่ใช้ (พารามิเตอร์อยู่ใน backend config)
- Plan: hours + dependency step only (no calendar dates) with 6-person team `Kittisak <New> Kaeowika`, `Chidchanok <lin> Saengamnat` (FE) and `Butsaba <But> Podamrong`, `Tunyatorn <Vava> Kiatkongphongsa`, `Peerakorn <Pete> Sakunkaewphithak`, `Aphiwit <Bank> Khammoon` (BE) — Peerakorn moved FE -> BE on 2026-08-07
- Working-time rule: 1 week = 5 days, 1 day = 6 hours (30 hours/week)

## Reference Design Documents

| Document | Owner | Scope | PDF | DOCX |
| --- | --- | --- | --- | --- |
| LLDD-API | BE/FE | REST conventions, endpoint catalog, request lifecycle, SQL/repository pattern | [PDF](../pdf/LLDD-API.pdf) | [DOCX](../word/LLDD-API.docx) |
| LLDD-Database | BE/DB | 19-table target schema, data zones/spine, DDL reference, indexes, transaction rules, seed data | [PDF](../pdf/LLDD-Database.pdf) | [DOCX](../word/LLDD-Database.docx) |
| LLDD-To-Be | PM/BA | สอบทานย้อนกลับ SDD GI หัวข้อ 1.9 To-Be -> เอกสาร FE/BE ที่ใช้ + ชั่วโมงต่อข้อ (implementation + unit test) | [PDF](../pdf/LLDD-To-Be.pdf) | [DOCX](../word/LLDD-To-Be.docx) |

## FE Core Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| FE-Integration-Contracts | Chidchanok <lin> Saengamnat | 16h | [PDF](../pdf/FE/LLDD-FE-Integration-Contracts.pdf) | [DOCX](../word/FE/LLDD-FE-Integration-Contracts.docx) |
| FE-Foundation | Chidchanok <lin> Saengamnat | 35h (impl 28 + test 7) | [PDF](../pdf/FE/LLDD-FE-Foundation.pdf) | [DOCX](../word/FE/LLDD-FE-Foundation.docx) |
| FE-Document-Lists | Chidchanok <lin> Saengamnat | 35h (impl 28 + test 7) | [PDF](../pdf/FE/LLDD-FE-Document-Lists.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Lists.docx) |
| FE-Create-Document | Kittisak <New> Kaeowika | 8h (impl 6 + test 2) | [PDF](../pdf/FE/LLDD-FE-Create-Document.pdf) | [DOCX](../word/FE/LLDD-FE-Create-Document.docx) |
| FE-Document-Detail | Kittisak <New> Kaeowika | 75h (impl 60 + test 15) | [PDF](../pdf/FE/LLDD-FE-Document-Detail.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail.docx) |
| FE-Testing-Delivery | Chidchanok <lin> Saengamnat | 12h | [PDF](../pdf/FE/LLDD-FE-Testing-Delivery.pdf) | [DOCX](../word/FE/LLDD-FE-Testing-Delivery.docx) |
| FE-Report | Kittisak <New> Kaeowika | 25h (impl 20 + test 5) | [PDF](../pdf/FE/LLDD-FE-Report.pdf) | [DOCX](../word/FE/LLDD-FE-Report.docx) |
| FE-Master-Data | Kittisak <New> Kaeowika | 20h (impl 16 + test 4) | [PDF](../pdf/FE/LLDD-FE-Master-Data.pdf) | [DOCX](../word/FE/LLDD-FE-Master-Data.docx) |

## Document Detail Role Pack

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| FE-Document-Detail-Role-06-SBP-DSA | Kittisak <New> Kaeowika | included in Document Detail | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA.docx) |
| FE-Document-Detail-Role-08-SBP-DSA-Officer | Kittisak <New> Kaeowika | included in Document Detail | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer.docx) |
| FE-Document-Detail-Role-01-Business-Promotion | Kittisak <New> Kaeowika | included in Document Detail | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion.docx) |
| FE-Document-Detail-Role-02-GM-Business-Promotion | Kittisak <New> Kaeowika | included in Document Detail | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion.docx) |
| FE-Document-Detail-Role-03-AVP-SBP | Kittisak <New> Kaeowika | included in Document Detail | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP.docx) |

## BE API Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| BE-API-Common-Contracts | Butsaba <But> Podamrong | 18h | [PDF](../pdf/BE/LLDD-BE-API-Common-Contracts.pdf) | [DOCX](../word/BE/LLDD-BE-API-Common-Contracts.docx) |
| BE-API-Document-List-Search | Butsaba <But> Podamrong | 26h (impl 20 + test 6) | [PDF](../pdf/BE/LLDD-BE-API-Document-List-Search.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-List-Search.docx) |
| BE-API-Document-Create-Update | Butsaba <But> Podamrong | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Document-Create-Update.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Create-Update.docx) |
| BE-API-Document-Detail-Aggregate | Butsaba <But> Podamrong | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Document-Detail-Aggregate.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Detail-Aggregate.docx) |
| BE-API-Document-Workflow-Actions | Tunyatorn <Vava> Kiatkongphongsa | 37h (impl 28 + test 9) | [PDF](../pdf/BE/LLDD-BE-API-Document-Workflow-Actions.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Workflow-Actions.docx) |
| BE-API-Workflow-Instances | Tunyatorn <Vava> Kiatkongphongsa | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Workflow-Instances.pdf) | [DOCX](../word/BE/LLDD-BE-API-Workflow-Instances.docx) |
| BE-API-Attachment-Sales-Timeline | Peerakorn <Pete> Sakunkaewphithak | 34h (impl 26 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Attachment-Sales-Timeline.pdf) | [DOCX](../word/BE/LLDD-BE-API-Attachment-Sales-Timeline.docx) |
| BE-API-Lookup | Tunyatorn <Vava> Kiatkongphongsa | 13h (impl 10 + test 3) | [PDF](../pdf/BE/LLDD-BE-API-Lookup.pdf) | [DOCX](../word/BE/LLDD-BE-API-Lookup.docx) |
| BE-API-Report-and-Master-Data | Peerakorn <Pete> Sakunkaewphithak | 39h (impl 30 + test 9) | [PDF](../pdf/BE/LLDD-BE-API-Report-and-Master-Data.pdf) | [DOCX](../word/BE/LLDD-BE-API-Report-and-Master-Data.docx) |
| BE-Job-Batch-Email-SRM | Peerakorn <Pete> Sakunkaewphithak | 19h (impl 14 + test 5) | [PDF](../pdf/BE/LLDD-BE-Job-Batch-Email-SRM.pdf) | [DOCX](../word/BE/LLDD-BE-Job-Batch-Email-SRM.docx) |
| BE-Database-Structure | Aphiwit <Bank> Khammoon | 28h | [PDF](../pdf/BE/LLDD-BE-Database-Structure.pdf) | [DOCX](../word/BE/LLDD-BE-Database-Structure.docx) |
| BE-Data-Migration-Cutover | Aphiwit <Bank> Khammoon | 40h | [PDF](../pdf/BE/LLDD-BE-Data-Migration-Cutover.pdf) | [DOCX](../word/BE/LLDD-BE-Data-Migration-Cutover.docx) |
| BE-Integration-SBP-Platform | Tunyatorn <Vava> Kiatkongphongsa | 20h | [PDF](../pdf/BE/LLDD-BE-Integration-SBP-Platform.pdf) | [DOCX](../word/BE/LLDD-BE-Integration-SBP-Platform.docx) |
| BE-Workflow-Engine-Definition | Tunyatorn <Vava> Kiatkongphongsa | 24h | [PDF](../pdf/BE/LLDD-BE-Workflow-Engine-Definition.pdf) | [DOCX](../word/BE/LLDD-BE-Workflow-Engine-Definition.docx) |

## BE Batch Job Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| BE-Job-1-ImportQSSI | Aphiwit <Bank> Khammoon | 21h (impl 16 + test 5) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-1-ImportQSSI.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-1-ImportQSSI.docx) |
| BE-Job-2-ImportImpactStore | Aphiwit <Bank> Khammoon | 19h (impl 14 + test 5) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-2-ImportImpactStore.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-2-ImportImpactStore.docx) |
| BE-Job-3-ImportImpactCompetitor | Aphiwit <Bank> Khammoon | 13h (impl 10 + test 3) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-3-ImportImpactCompetitor.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-3-ImportImpactCompetitor.docx) |
| BE-Job-4-PrepareImpactStoreToIAS | Aphiwit <Bank> Khammoon | 19h (impl 14 + test 5) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS.docx) |
| BE-Job-5-ImportImpactSaleFromIAS | Peerakorn <Pete> Sakunkaewphithak | 21h (impl 16 + test 5) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS.docx) |
| BE-Job-6-ExportImpactStoreToFS | Aphiwit <Bank> Khammoon | 26h (impl 20 + test 6) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS.docx) |
| BE-Job-7-SyncCompetitorToDocument | Peerakorn <Pete> Sakunkaewphithak | 13h (impl 10 + test 3) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.docx) |
| BE-Job-8-CreateCompensationDocument | Aphiwit <Bank> Khammoon | 24h (impl 18 + test 6) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.docx) |
| BE-Job-8b-StartInternalWorkflow | Tunyatorn <Vava> Kiatkongphongsa | 21h (impl 16 + test 5) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-8b-StartInternalWorkflow.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-8b-StartInternalWorkflow.docx) |
| BE-Job-9-SyncNewStoreToDocument | Peerakorn <Pete> Sakunkaewphithak | 15h (impl 11 + test 4) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument.docx) |
| BE-Job-10-NotifyNoReceiveData | Peerakorn <Pete> Sakunkaewphithak | 11h (impl 8 + test 3) | [PDF](../pdf/BE/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.pdf) | [DOCX](../word/BE/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.docx) |
