# LLDD Document Portal

เปิดหน้า portal ใน browser หรือใช้รายการลิงก์ด้านล่าง.

- Main index: [PDF](../pdf/LLDD-Main-Index-Phase4-4-3-SBP-Operating-Management.pdf)
- Documents: 43
- Total estimate: 829 hours  (implementation 675 + unit test 154)
- Unit test: BE/Job 30% · FE 25% ของชั่วโมง implementation · เอกสารสัญญา/ออกแบบไม่คิดแยก (ดู NO_UNIT_TEST_DOCS)
- ขอบเขต 2026-08-07: ตัด `LLDD-FE-Overview` และ `LLDD-BE-API-Dashboard-Summary` · เพิ่ม `LLDD-BE-Database-Structure`, `LLDD-BE-Data-Migration-Cutover`, `LLDD-BE-Integration-SBP-Platform`, `LLDD-BE-Workflow-Engine-Definition` · เปลี่ยนชื่อ `FE-Master-Config` -> `FE-Master-Data`, `BE-API-Lookup-RBAC-Email` -> `BE-API-Lookup`, `BE-API-Report-Master-Config` -> `BE-API-Report-and-Master-Data`
- ขอบเขต 2026-08-06: ตัด `LLDD-FE-Batch-Monitor` และ `LLDD-FE-Email-Template` ออกจากชุดส่งมอบ — หน้า Global Config/Email Template ลบทั้งฟีเจอร์ (ใช้ `mas_param`/`email_template` ของระบบ SBP เดิม) และหน้า Batch Job ย้ายไปกลุ่มเมนู Flow เหลือเฉพาะ Flowchart + Database ที่ใช้ (พารามิเตอร์อยู่ใน backend config)
- Plan: hours + dependency step only (no calendar dates) with 6-person team `Kittisak &lt;New&gt; Kaeowika`, `Chidchanok &lt;lin&gt; Saengamnat` (FE) and `Butsaba &lt;But&gt; Podamrong`, `Tunyatorn &lt;Vava&gt; Kiatkongphongsa`, `Peerakorn &lt;Pete&gt; Sakunkaewphithak`, `Aphiwit &lt;Bank&gt; Khammoon` (BE) — Peerakorn moved FE -> BE on 2026-08-07
- Working-time rule: 1 week = 5 days, 1 day = 8.5 hours (42.5 hours/week)
- Delivery target (2026-08-25): finish in **4 weeks** = 170 hours per person; team capacity 6 x 170 = 1020 hours vs 829 hours of work (81% utilisation)
- Track ownership (latest 2026-09-02): `Aphiwit &lt;Bank&gt; Khammoon` owns **all 12 batch jobs** (Job 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 8b) and nothing else - Database Structure, Data Migration/Cutover and Workflow Engine Definition sit with their own track owners - 211 hours
- ⚠️ **Capacity warning:** `Aphiwit &lt;Bank&gt; Khammoon` carries **211 hours**, 1.24x the 4-week ceiling of 170 hours - that is **5.0 weeks** at 42.5 hours/week (25 working days at 8.5 h/day). Everyone else ranges 103-145 hours (2.4-3.4 weeks), so 5 of 5 finish inside 4 weeks. The plan does not fit until the batch jobs are shared out or the deadline moves - see DECISIONS-รอตัดสินใจ.md

## Reference Design Documents

| Document | Owner | Scope | PDF | DOCX |
| --- | --- | --- | --- | --- |
| LLDD-API | BE/FE | REST conventions, endpoint catalog, request lifecycle, SQL/repository pattern | [PDF](../pdf/LLDD-API.pdf) | [DOCX](../word/LLDD-API.docx) |
| LLDD-Database | BE/DB | 20-table target schema (CREATE 19 + reuse fcs_qssi_score), data zones/spine, DDL reference, indexes, transaction rules, seed data — **คำอธิบายรายคอลัมน์อยู่ที่ LLDD-Database-Dictionary** | [PDF](../pdf/LLDD-Database.pdf) | [DOCX](../word/LLDD-Database.docx) |
| LLDD-Database-Dictionary | BE/DB | 19 ตารางใหม่ (โซน A/B/C) — มาจากไหน · ใช้ทำอะไร · ทำไมต้องมี · ทุกคอลัมน์เก็บอะไรไว้ใช้ทำอะไร | [PDF](../pdf/LLDD-Database-Dictionary.pdf) | — (PDF อย่างเดียว) |
| LLDD-To-Be | PM/BA | สอบทานย้อนกลับ SDD GI หัวข้อ 1.9 To-Be -> เอกสาร FE/BE ที่ใช้ + ชั่วโมงต่อข้อ (implementation + unit test) | [PDF](../pdf/LLDD-To-Be.pdf) | [DOCX](../word/LLDD-To-Be.docx) |

## FE Core Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| FE-Integration-Contracts | Chidchanok &lt;lin&gt; Saengamnat | 16h | [PDF](../pdf/FE/LLDD-FE-Integration-Contracts.pdf) | [DOCX](../word/FE/LLDD-FE-Integration-Contracts.docx) |
| FE-Foundation | Chidchanok &lt;lin&gt; Saengamnat | 35h (impl 28 + test 7) | [PDF](../pdf/FE/LLDD-FE-Foundation.pdf) | [DOCX](../word/FE/LLDD-FE-Foundation.docx) |
| FE-Document-Lists | Chidchanok &lt;lin&gt; Saengamnat | 35h (impl 28 + test 7) | [PDF](../pdf/FE/LLDD-FE-Document-Lists.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Lists.docx) |
| FE-Create-Document | Kittisak &lt;New&gt; Kaeowika | 8h (impl 6 + test 2) | [PDF](../pdf/FE/LLDD-FE-Create-Document.pdf) | [DOCX](../word/FE/LLDD-FE-Create-Document.docx) |
| FE-Document-Detail | Kittisak &lt;New&gt; Kaeowika | 75h (impl 60 + test 15) | [PDF](../pdf/FE/LLDD-FE-Document-Detail.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail.docx) |
| FE-Testing-Delivery | Chidchanok &lt;lin&gt; Saengamnat | 12h | [PDF](../pdf/FE/LLDD-FE-Testing-Delivery.pdf) | [DOCX](../word/FE/LLDD-FE-Testing-Delivery.docx) |
| FE-Report | Chidchanok &lt;lin&gt; Saengamnat | 25h (impl 20 + test 5) | [PDF](../pdf/FE/LLDD-FE-Report.pdf) | [DOCX](../word/FE/LLDD-FE-Report.docx) |
| FE-Master-Data | Kittisak &lt;New&gt; Kaeowika | 20h (impl 16 + test 4) | [PDF](../pdf/FE/LLDD-FE-Master-Data.pdf) | [DOCX](../word/FE/LLDD-FE-Master-Data.docx) |

## Document Detail Role Pack

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| FE-Document-Detail-Role-06-SBP-DSA | Kittisak &lt;New&gt; Kaeowika | 13h (impl 10 + test 3) — รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-06-SBP-DSA.docx) |
| FE-Document-Detail-Role-08-SBP-DSA-Officer | Kittisak &lt;New&gt; Kaeowika | 13h (impl 10 + test 3) — รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-08-SBP-DSA-Officer.docx) |
| FE-Document-Detail-Role-01-Business-Promotion | Kittisak &lt;New&gt; Kaeowika | 13h (impl 10 + test 3) — รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-01-Business-Promotion.docx) |
| FE-Document-Detail-Role-02-GM-Business-Promotion | Kittisak &lt;New&gt; Kaeowika | 13h (impl 10 + test 3) — รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-02-GM-Business-Promotion.docx) |
| FE-Document-Detail-Role-03-AVP-SBP | Kittisak &lt;New&gt; Kaeowika | 13h (impl 10 + test 3) — รวมอยู่ใน Document Detail ไม่บวกซ้ำในยอดรวม | [PDF](../pdf/FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP.pdf) | [DOCX](../word/FE/LLDD-FE-Document-Detail-Role-03-AVP-SBP.docx) |

## BE API Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| BE-API-Common-Contracts | Butsaba &lt;But&gt; Podamrong | 18h | [PDF](../pdf/BE/LLDD-BE-API-Common-Contracts.pdf) | [DOCX](../word/BE/LLDD-BE-API-Common-Contracts.docx) |
| BE-API-Document-List-Search | Butsaba &lt;But&gt; Podamrong | 26h (impl 20 + test 6) | [PDF](../pdf/BE/LLDD-BE-API-Document-List-Search.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-List-Search.docx) |
| BE-API-Document-Create-Update | Butsaba &lt;But&gt; Podamrong | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Document-Create-Update.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Create-Update.docx) |
| BE-API-Document-Detail-Aggregate | Butsaba &lt;But&gt; Podamrong | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Document-Detail-Aggregate.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Detail-Aggregate.docx) |
| BE-API-Document-Workflow-Actions | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | 37h (impl 28 + test 9) | [PDF](../pdf/BE/LLDD-BE-API-Document-Workflow-Actions.pdf) | [DOCX](../word/BE/LLDD-BE-API-Document-Workflow-Actions.docx) |
| BE-API-Workflow-Instances | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | 32h (impl 24 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Workflow-Instances.pdf) | [DOCX](../word/BE/LLDD-BE-API-Workflow-Instances.docx) |
| BE-API-Attachment-Sales-Timeline | Peerakorn &lt;Pete&gt; Sakunkaewphithak | 34h (impl 26 + test 8) | [PDF](../pdf/BE/LLDD-BE-API-Attachment-Sales-Timeline.pdf) | [DOCX](../word/BE/LLDD-BE-API-Attachment-Sales-Timeline.docx) |
| BE-API-Lookup | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | 13h (impl 10 + test 3) | [PDF](../pdf/BE/LLDD-BE-API-Lookup.pdf) | [DOCX](../word/BE/LLDD-BE-API-Lookup.docx) |
| BE-API-Report-and-Master-Data | Peerakorn &lt;Pete&gt; Sakunkaewphithak | 39h (impl 30 + test 9) | [PDF](../pdf/BE/LLDD-BE-API-Report-and-Master-Data.pdf) | [DOCX](../word/BE/LLDD-BE-API-Report-and-Master-Data.docx) |
| BE-Job-Batch-Email-SRM | Peerakorn &lt;Pete&gt; Sakunkaewphithak | 11h (impl 8 + test 3) | [PDF](../pdf/BE/LLDD-BE-Job-Batch-Email-SRM.pdf) | [DOCX](../word/BE/LLDD-BE-Job-Batch-Email-SRM.docx) |
| BE-Database-Structure | Peerakorn &lt;Pete&gt; Sakunkaewphithak | 31h | [PDF](../pdf/BE/LLDD-BE-Database-Structure.pdf) | [DOCX](../word/BE/LLDD-BE-Database-Structure.docx) |
| BE-Data-Migration-Cutover | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | 43h | [PDF](../pdf/BE/LLDD-BE-Data-Migration-Cutover.pdf) | [DOCX](../word/BE/LLDD-BE-Data-Migration-Cutover.docx) |
| BE-Integration-SBP-Platform | Tunyatorn &lt;Vava&gt; Kiatkongphongsa | 20h | [PDF](../pdf/BE/LLDD-BE-Integration-SBP-Platform.pdf) | [DOCX](../word/BE/LLDD-BE-Integration-SBP-Platform.docx) |
| BE-Workflow-Engine-Definition | Peerakorn &lt;Pete&gt; Sakunkaewphithak | 24h | [PDF](../pdf/BE/LLDD-BE-Workflow-Engine-Definition.pdf) | [DOCX](../word/BE/LLDD-BE-Workflow-Engine-Definition.docx) |

## BE Batch Job Documents

| Document | Owner | Estimate | PDF | DOCX |
| --- | --- | --- | --- | --- |
| BE-Job-2-ImportImpactStore | Aphiwit &lt;Bank&gt; Khammoon | 20h (impl 15 + test 5) | [PDF](../pdf/Jobs/LLDD-BE-Job-2-ImportImpactStore.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-2-ImportImpactStore.docx) |
| BE-Job-3-ImportImpactCompetitor | Aphiwit &lt;Bank&gt; Khammoon | 12h (impl 9 + test 3) | [PDF](../pdf/Jobs/LLDD-BE-Job-3-ImportImpactCompetitor.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-3-ImportImpactCompetitor.docx) |
| BE-Job-4-PrepareImpactStoreToIAS | Aphiwit &lt;Bank&gt; Khammoon | 17h (impl 13 + test 4) | [PDF](../pdf/Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS.docx) |
| BE-Job-5-ImportImpactSaleFromIAS | Aphiwit &lt;Bank&gt; Khammoon | 17h (impl 13 + test 4) | [PDF](../pdf/Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS.docx) |
| BE-Job-6-ExportImpactStoreToFS | Aphiwit &lt;Bank&gt; Khammoon | 32h (impl 24 + test 8) | [PDF](../pdf/Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS.docx) |
| BE-Job-7-SyncCompetitorToDocument | Aphiwit &lt;Bank&gt; Khammoon | 12h (impl 9 + test 3) | [PDF](../pdf/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.docx) |
| BE-Job-8-CreateCompensationDocument | Aphiwit &lt;Bank&gt; Khammoon | 23h (impl 17 + test 6) | [PDF](../pdf/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.docx) |
| BE-Job-8b-StartInternalWorkflow | Aphiwit &lt;Bank&gt; Khammoon | 28h (impl 21 + test 7) | [PDF](../pdf/Jobs/LLDD-BE-Job-8b-StartInternalWorkflow.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-8b-StartInternalWorkflow.docx) |
| BE-Job-9-SyncNewStoreToDocument | Aphiwit &lt;Bank&gt; Khammoon | 13h (impl 10 + test 3) | [PDF](../pdf/Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument.docx) |
| BE-Job-10-NotifyNoReceiveData | Aphiwit &lt;Bank&gt; Khammoon | 8h (impl 6 + test 2) | [PDF](../pdf/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.docx) |
| BE-Job-11-ConsumeStaCompensate | Aphiwit &lt;Bank&gt; Khammoon | 16h (impl 12 + test 4) | [PDF](../pdf/Jobs/LLDD-BE-Job-11-ConsumeStaCompensate.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-11-ConsumeStaCompensate.docx) |
| BE-Job-12-NotifyPendingWork | Aphiwit &lt;Bank&gt; Khammoon | 13h (impl 10 + test 3) | [PDF](../pdf/Jobs/LLDD-BE-Job-12-NotifyPendingWork.pdf) | [DOCX](../word/Jobs/LLDD-BE-Job-12-NotifyPendingWork.docx) |
