# Foundation 02 — Glossary และกฎธุรกิจกลาง

> Contract status: `CONFIRMED` · Document status: `Verified`

## ต้องทำอะไร และเสร็จแล้วได้อะไร

ใช้คำในตารางนี้เป็น canonical term ทุกฉบับ ชื่อ code/table/status ต้องใช้ identifier เดิม ส่วนคำไทยใช้เพื่ออธิบายความหมาย ไม่สร้าง synonym ใหม่โดยไม่มี Decision ID

## Glossary

| คำ | ความหมายใน LLDDv2 |
|---|---|
| impacted store | ร้าน SP ที่ยอดขายอาจลดจากร้านใหม่; key `impacted_store_code` |
| new store | ร้านเปิดใหม่ที่ส่งผล; key `new_store_code` และต้องเก็บ leading zero |
| compensation period | งวด `period_year` + `period_month`; ปี API/INPUT เป็น ค.ศ. |
| workflow state | สถานะงานใน engine; SGI map เป็น status code `06/08/01/02/03/99` |
| section | หน่วยงาน/ขั้นปัจจุบัน: 06, 08, 01, 02, 03 |
| route | Next.js page path หรือ HTTP path ตามบริบท; ต้องระบุชนิดเสมอ |
| outbox | แถว `sgi_interface_transactions` ที่ commit พร้อมธุรกิจ ก่อน publish ภายนอก |
| idempotency | เรียกซ้ำด้วย business key เดิมแล้วไม่สร้างผลธุรกิจซ้ำ |
| rerun | การรัน Job เดิมซ้ำอย่างตั้งใจ; ต้องแยกจาก broker redelivery |
| advisory lock | PostgreSQL lock ระดับ Job (`SGI_JOB_LOCK_CLASS_ID=861000`) กันรันชนกัน |
| publisher confirm | RabbitMQ broker ยืนยันรับข้อความ; ไม่ใช่ business ACK จาก STA |
| DLQ | คิวกักข้อความที่ retry ครบหรือ schema/business consistency ผิด |
| `AS-BUILT` | พฤติกรรมที่อ่านได้จาก TypeScript/test ปัจจุบัน ไม่ได้แปลว่า Business อนุมัติ |

## Canonical status

| Code | ชื่อเอกสาร | Section |
|---|---|---|
| `06` | รอฝ่าย SBP DSA ดำเนินการ | 06 |
| `08` | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | 08 |
| `01` | รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ | 01 |
| `02` | รอ GM ส่งเสริมธุรกิจดำเนินการ | 02 |
| `03` | รอ AVP SBP ดำเนินการ | 03 |
| `99` | เสร็จสิ้นดำเนินการ | none |

ชื่อไทยต้องตรง seed `common_code` (`SGI_DOC_STATUS`) และ `workflow_status`; ห้ามให้ FE hardcode เป็นอีกชุด

## กฎธุรกิจที่ห้ามเปลี่ยนโดยลำพัง

1. Store code เป็น string 5 หลัก ห้ามแปลงเป็น number
2. ระยะกระทบตาม requirement คือ 1 กม. กรุงเทพฯ/ปริมณฑล และ 2 กม. ต่างจังหวัด; logic import จริงมี branch/cancel/contract gate เพิ่มเติมตาม Job 2
3. `newStores[].compensatePercent` รวมต้องเท่ากับ 100; BE คำนวณ `compensationAmount` และจัดการเศษให้ยอดรวมตรง
4. วงเงินอนุมัติใช้เกณฑ์ 100,000 บาท: route ไป Section 03 เมื่อเข้าเงื่อนไขตาม workflow contract; แหล่ง config ดู D-001
5. Action 7 ค่าเป็นข้อความตาม requirement: เห็นควรชดเชย, เห็นควรไม่ชดเชย, หยุดชดเชยประกันรายได้, ส่งหน่วยงานส่งเสริมธุรกิจ SBP, ส่งเจ้าหน้าที่ SBP DSA, คำนวณเงินชดเชยเรียบร้อย, ส่งกลับ
6. ยอดชดเชย 0 เดือน 1–3 ยังส่ง Section 08; เดือนที่ 4 หยุดชดเชย
7. Section 08 คำนวณเสร็จส่งกลับ Section 06; ไม่ส่ง Section 01 โดยตรง
8. เอกสารปิดด้วย “หยุดชดเชย” ต้องกลับเข้าคิว Section 06 เพื่อเปิดพิจารณาใหม่; “เห็นควรไม่ชดเชย” ให้ตั้งงานเดือนถัดไปแก่ผู้รับผิดชอบคนเดิม
9. สร้างเอกสารซ้ำไม่ได้เฉพาะเมื่อมี active document ของร้าน+งวดเดียวกัน; เอกสารที่จบแล้วเปิดใหม่ได้ตามกฎ reflow
10. Attachment ไม่เกิน 5 MiB และ download ได้เมื่อ scan policy อนุญาต
11. รายงานบังคับ `status`; ถ้า status `99` ต้องมี statement period; impacted/new store filter ต้องส่งเป็นคู่
12. `pending-ack` หมายถึง outbox ขาออกที่ยังไม่ publisher-confirmed เพื่อ compatibility; STA ไม่มี HTTP ACK endpoint

## Source และการเปลี่ยนกฎ

กฎมาจาก `workflow.md`, `api.md`, SDD/SRS และ code/test ที่อ้างใน Job แต่ละฉบับ การเปลี่ยนกฎที่กระทบเงิน, route, status, file/message schema หรือ data retention ต้องสร้าง Decision ID, owner sign-off, migration impact และ regression test ก่อนแก้ contract

