# แผนจัดทำ LLDDv2

> สถานะเอกสาร: `CONFIRMED` · ปรับปรุงล่าสุด 2026-09-15

## ต้องทำอะไร และเสร็จแล้วได้อะไร

สร้าง LLDD ชุดใหม่ที่อ่านตามฟีเจอร์และตาม data pipeline ได้โดยไม่ต้องประกอบคำตอบจากหลายสิบฉบับ ผู้อ่านต้องตามเส้นทาง FE → BFF → BE → DB/API/Workflow ได้ในฉบับเดียว และแยกสิ่งที่มีใน code ออกจากสิ่งที่ยังต้องสร้างหรือรอตัดสินใจได้ทันที

ผลส่งมอบระยะแรกคือ Markdown และ Mermaid ใน `llddv2/` เท่านั้น ไม่มี PDF, DOCX, PNG และไม่มีการแก้ application code, SQL หรือ API

## หลักการและป้ายสถานะ

| ป้าย | ใช้เมื่อ | ใช้ตัดสินใจพัฒนาได้หรือไม่ |
|---|---|---|
| `CONFIRMED` | มีหลักฐานจาก requirement/code/schema หรือมติที่อ้างกลับได้ | ได้ ภายในขอบเขตหลักฐาน |
| `AS-BUILT` | พฤติกรรมตรงกับ TypeScript/Java/test ปัจจุบัน | ได้ แต่ต้องอ่าน `BLOCKED` ของเรื่องเดียวกัน |
| `TO-BE` | ยังไม่มี code และเป็น contract ที่ต้องพัฒนา | ได้เมื่อไม่มี `BLOCKED` ที่เกี่ยวข้อง |
| `BLOCKED` | ต้องมีผู้มีอำนาจตัดสินใจหรือข้อมูลภายนอก | ห้ามเดาและห้ามใช้สถานะ Ready |

สถานะระดับเอกสารใน [README.md](README.md) คือ `Draft`, `Verified`, `Blocked`, `Ready` โดยเอกสารที่มี `BLOCKED` ต้องเป็น `Blocked` เสมอ

## Source of truth

ลำดับความน่าเชื่อถือเมื่อข้อมูลขัดกัน:

1. Application code และ automated test ปัจจุบัน — ยืนยัน `AS-BUILT` เท่านั้น
2. DDL ที่ generate จาก `LLDD/md/LLDD-Database.md`, `api.md`, `workflow.md` และมติที่ปิดแล้ว — ยืนยัน target contract
3. Java ใน `batchjob/fcsJar/` — อธิบาย legacy behavior และกับดัก ห้ามถือเป็น target โดยอัตโนมัติ
4. `batchjob/JOB-*-อธิบายละเอียด.md` — คำอธิบายกฎจาก Java และผลตรวจย้อนหลัง
5. LLDD เดิม — ใช้เป็นหลักฐาน/ดัชนี ไม่ใช่โครงสร้างของ LLDDv2

ถ้าแหล่งข้อมูลชั้นเดียวกันขัดกัน ให้บันทึก Decision ID ใน [00-foundation/07-decision-register.md](00-foundation/07-decision-register.md) แทนการเลือกเอง

## Source inventory

| Source | ใช้ยืนยัน | ข้อจำกัด |
|---|---|---|
| `SBP/srm-sps-spsap-sop-sgi-batch/src/modules/sgi/` | service, DTO, SQL, env, lock, retry และ message `AS-BUILT` ของ Jobs 2–12 + 8b | ยังต้องรันซ้ำใน environment ที่ CodeArtifact token ใช้ได้ |
| `SBP/.../src/modules/sgi/*.spec.ts`, `__svc__/*`, `test/sgi/*` | unit/service/database/lifecycle contract ของ Batch | ผลใน README เป็นผล SGI scope ไม่ใช่ทั้ง repo |
| `batchjob/fcsJar/` | legacy Java behavior 11 Jobs | Job 11 ไม่มี Java เดิม; มี credential legacy ห้ามคัดลอก |
| `batchjob/JOB-*-อธิบายละเอียด.md` | กฎ legacy, edge case และเหตุผล | บางค่าถูก target code เลือกเป็น config แต่ยังไม่ sign-off |
| `api.md`, `plan-api.html` | canonical API 28 เส้น | FE/BFF/BE SGI ยังไม่มี code |
| `database.md`, `LLDD/md/LLDD-Database.md` | 20 ตารางใหม่ + `fcs_qssi_score` reuse | migration ไป dev จริงยังไม่ยืนยัน |
| `workflow.md` | state, section, route และ engine contract | workflow version/definition จริงยัง Blocked |
| HTML prototype root | route, field, label, validation และ user journey | เป็น prototype ไม่ใช่ production FE |
| `STA/`, `SDD-GI-Compensation/` | interface/business requirement | ต้องให้เจ้าของระบบภายนอกรับรองก่อน UAT |

## Traceability matrix ระดับชุดเอกสาร

| Requirement | Design owner | Implementation evidence | Verification |
|---|---|---|---|
| API SGI 28 เส้น | `features/*`, `references/API-CATALOG.md` | `TO-BE` FE/BFF/BE | API contract/e2e ใน `TEST-AND-DELIVERY.md` |
| DB 20+1 ตาราง | `00-foundation/04-*`, `references/DATABASE-DICTIONARY.md` | generated DDL + Batch SQL | schema count, FK/link checks, PostgreSQL test |
| Workflow 5 section | `00-foundation/05-*`, features 03–04 | engine เดิมมีอยู่; SGI adapter `TO-BE` | transition, ownership, rollback tests |
| Batch Jobs 2–12 + 8b | `jobs/*` | TypeScript services/tests `AS-BUILT` | unit + `__svc__` + lifecycle + failure tests |
| External interfaces | `00-foundation/06-*`, Jobs 4–6, 10–11 | S3/RabbitMQ clients `AS-BUILT` | contract test + replay/DLQ/outbox test |
| Prototype journey | `features/*` | production FE `TO-BE` | component/a11y/e2e acceptance |

## ลำดับจัดทำและเกณฑ์ผ่าน

1. Foundation: canonical terminology, API, DB, workflow, integration และ decision register
2. Jobs: จัดตาม data flow 2–3 → 4–5 → 6 → 8 → 7/9 → 8b → 11 → 10/12
3. Features: worklist → creation → detail → action → attachment/sales → master → report → tracking
4. References: endpoint/table/config/error/test catalogs และตรวจ cross-link
5. เมื่อตรวจรับทุกฉบับเป็น Ready จึงทำงานแยกเพื่อเพิ่ม deprecated banner ให้ `LLDD/`; ห้ามลบชุดเดิมในงานนี้

เกณฑ์อัตโนมัติอยู่ใน `python3 tools/check_docs.py`: ต้องพบเอกสารบังคับทั้งหมด, Job 12 ฉบับ, Feature 8 ฉบับ, Mermaid flowchart+sequence, API 28 เส้น, DB 20+1 ตาราง, ลิงก์ Markdown ที่มีไฟล์ปลายทาง และห้าม Ready เมื่อยังมี `BLOCKED`

## รูปแบบเอกสารมาตรฐาน

- Feature ใช้หัวข้อ 1–17 ตาม [templates/FEATURE-TEMPLATE.md](templates/FEATURE-TEMPLATE.md)
- Job ใช้หัวข้อ 1–18 ตาม [templates/JOB-TEMPLATE.md](templates/JOB-TEMPLATE.md)
- ไม่ใส่ skeleton เต็มไฟล์; snippet ใช้เฉพาะจุดที่กัน implement ผิด
- identifier ใน code ใช้ English เดิม; คำอธิบายใช้ภาษาไทย
- เอกสารหลักควรไม่เกินประมาณ 500 บรรทัด; ตารางยาวอยู่ใน `references/`

