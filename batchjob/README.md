# batchjob/ — เอกสารอธิบาย batch job แบบเล่าให้เข้าใจ

โฟลเดอร์นี้เก็บเอกสาร **"อธิบายละเอียด"** ของ batch job แต่ละตัว — เขียนเป็นภาษาคน
เพื่อให้คนที่จะลงมือเขียนโค้ดอ่านแล้วเข้าใจว่า **job ทำอะไร มีเคสอะไร ตัดสินจากอะไร**

## ต่างจากเอกสาร LLDD อย่างไร

| | `batchjob/` (โฟลเดอร์นี้) | `LLDD/` |
|---|---|---|
| รูปแบบ | เล่าเป็นภาษาคน · มีตารางเคส · อธิบาย "ทำไม" | สเปกรูปแบบมาตรฐาน หัวข้อ 1–10 เหมือนกันทุกฉบับ |
| ที่มา | **อ่านจากโค้ดเดิมใน `fcsJar/` โดยตรง** | ออกแบบจาก requirement + ผัง |
| จุดแข็ง | เข้าใจตรรกะจริง · เห็นกับดักที่โค้ดเดิมซ่อนไว้ | ครบถ้วนเป็นระบบ · มีโครงโค้ด NestJS + SQL |
| สร้างอย่างไร | **เขียนมือ** | **generate** จาก `tools/build_lldd_documents.py` |

อ่านคู่กันทั้งสองฝั่ง — ฉบับใน `batchjob/` ตอบว่า *ทำไมถึงเขียนแบบนั้น*
ส่วนฉบับใน `LLDD/` ตอบว่า *ต้องเขียนอะไรบ้าง*

> ✅ **ครบทั้ง 12 job แล้ว** (Jobs 2–12 + 8b · ปรับปรุงล่าสุด 2026-09-10)
>
> ⚠️ **Job 11 ไม่มีโค้ดเดิมใน `fcsJar/`** — ค้น `batchjob/fcsJar/src/` แล้วไม่พบ `updateCompensateFromFS` ·
> `sta_update_compensate` · `amqp`/`RabbitMQ` เลย · ระบบเดิมให้ **STA เป็นฝ่ายเรียก web service เข้ามา**
> ฉบับนั้นจึงเป็น **สเปกของงานใหม่** ไม่ใช่การอธิบายโค้ดเดิม (ระบุไว้ที่หัวเอกสารแล้ว)
> **อีก 11 ฉบับอ่านจากคลาส Java จริงทั้งหมด**

## กติกาของโฟลเดอร์นี้

- **path ทุกอันในเอกสารเขียนจากรากโปรเจกต์ `sbp-prototype/`** ไม่ใช่จากโฟลเดอร์นี้
  (ลิงก์ที่กดได้จะใส่ `../` ไว้ให้แล้ว)
- ทุกข้อเท็จจริงต้อง**อ้างอิงโค้ดจริงได้** — ระบุไฟล์และเมธอดที่อ่านมาไว้หัวเอกสาร
- ตารางและคอลัมน์ที่อ้างถึงต้องเป็น **schema ใหม่ (`sgi_*`)** เท่านั้น
  ตารางของระบบเดิมอ้างได้แต่ต้องระบุชัดว่า **อ่านอย่างเดียว**

## สถานะรวม

| แกน | สถานะ |
|---|---|
| **เอกสารเขียนครบ** | ✅ **12/12** |
| **เขียนโค้ดแล้ว** | ✅ **12/12** — Jobs 2–12 + 8b (`SBP/srm-sps-spsap-sop-sgi-batch/src/modules/sgi/`) · ทดสอบกับ PostgreSQL 16 จริงแล้วทุกตัว |
| **ปิด open decision ครบ** | ❌ — ดู [`DECISIONS-รอตัดสินใจ.md`](../DECISIONS-รอตัดสินใจ.md) (ทั้งโครงการ) และ **[`JOB-02-12-ข้อตัดสินใจที่ไม่มีของเดิมให้ลอก.md`](JOB-02-12-ข้อตัดสินใจที่ไม่มีของเดิมให้ลอก.md)** (เฉพาะ batch job · **ตัดข้อที่ตอบได้จากโค้ด/ฐานเดิมออกแล้ว**) |
| **Implementation-ready** | ❌ — ต้องปิด P0 ใน checklist ก่อน |

🔴 **ความปลอดภัย:** `batchjob/fcsJar/` มี credential ของ prod อยู่ **83 จุด ใน 22 ไฟล์**
บัญชีรายการ (ไม่มีค่าจริง): [CREDENTIAL-INVENTORY.md](CREDENTIAL-INVENTORY.md) ·
ตรวจด้วย `python3 tools/scan_secrets.py batchjob/fcsJar` **ก่อน commit ทุกครั้ง**

**Checklist งานที่ต้องแก้:**
[CHECKLIST-JOB-02-JOB-12-REMEDIATION.md](CHECKLIST-JOB-02-JOB-12-REMEDIATION.md) (ทุก job) ·
[CHECKLIST-JOB-02-JOB-03-REMEDIATION.md](CHECKLIST-JOB-02-JOB-03-REMEDIATION.md) (Job 2/3 รายละเอียด)

**ตรวจล่าสุด:** 2026-09-15 (รอบตรวจที่ 25 · ดู checklist)

## โค้ดที่เขียนแล้ว

**Job 2** (`sgi-import-impact-store`) และ **Job 3** (`sgi-import-impact-competitor`) อยู่ที่
`SBP/srm-sps-spsap-sop-sgi-batch/src/modules/sgi/` · รายละเอียด env / วิธีรัน / ของที่ยังไม่เคาะ อยู่ใน
[`src/modules/sgi/README.md`](../SBP/srm-sps-spsap-sop-sgi-batch/src/modules/sgi/README.md) ของ repo นั้น

ยืนยันแล้ว: **unit test 117 เคสผ่าน** · typecheck 0 error · SQL รันกับ **PostgreSQL 16 จริง**

- **Job 2** — กฎตัดสินครบ 10 เคส (P1 · P1 FPT1+06 · P2 จาก STA · N1–N5 · 2 เคสตกร่องค้าง `W`) ·
  รหัสร้านขยะถูกกัน · รันซ้ำไม่เกิดแถวซ้ำและไม่รีเซ็ตรอบที่ active แล้ว
- **Job 3** — ครบ 11 เคส (dedup ตามรหัสสาขา · รหัสว่างเป็น `NULL` แล้ว dedup ด้วย `branch_th` ·
  แบรนด์ที่ map ไม่ได้ยังถูกเก็บโดย `brand_code = NULL` · ร้านที่ไม่มีแถวแม่ถูกข้าม ·
  รอบสองข้ามทั้งงวดและไม่เพิ่มแถว)

- **Job 4** — ครบ 14 เคส (สร้างหัวสรุปเฉพาะคู่ร้าน `P` · T1/T2 คัดถูก · เลือกร้านใหม่ที่เปิดก่อนสุด ·
  ไฟล์ `10001|20260301` ไม่มี newline ปิดท้าย · outbox `IAS_SALES_REQUEST` + SHA-256 ·
  `business_key` เก็บศูนย์นำหน้า · รันซ้ำไม่ส่งซ้ำ · เลื่อนวันแล้วร้านถึงกำหนดเพิ่ม)

⚠️ **Job 3 ต้องรันหลัง Job 2 ของงวดเดียวกันเสมอ** — `impact_process_id` เป็น `NOT NULL` + FK
ชี้ไปแถวแม่ที่ Job 2 สร้าง · ข้อมูลจริงมีคู่แข่ง **7.4%** ที่ร้านไม่มีแถวแม่ของงวดนั้น
✅ **ปิดแล้ว 2026-09-13 (ข้อ 2.20 · 2.23)** — ข้ามแถวนั้นได้เพราะ **99.92% เป็นข้อมูลที่ระบบเดิม
ก็ไม่เคยใช้** (ผู้อ่านรายเดียวใช้ `INNER JOIN` แถวแม่) · และการนำเข้าไม่ครบ **ไม่เคยเกิดขึ้นจริง**
ใน 88 งวดตลอด 8 ปี

### ✅ ปิดด้วยข้อมูลจริงจากฐาน Oracle เดิม (2026-09-12)

ดึงข้อมูลจริงด้วย `tools/introspect_legacy_oracle.py` (ฐาน `stqa` · ตาราง `*_BK_20250515` 26,264 แถว
— ตาราง live ถูกรีเซ็ตเมื่อ 2025-05-15 เหลือ 728 แถว ใช้เป็นภาพแทนไม่ได้)

| ข้อ | เดิม | ข้อมูลจริงบอกว่า |
|---|---|---|
| **4.4** `PERIOD_YEAR` พ.ศ./ค.ศ. | สรุปไม่ได้ | **ค.ศ.** — ปีที่พบ 2016–2025 ไม่มี 25xx เลยสักแถว |
| **2.15** แหล่ง `branchtype` | ต้องเลือกระหว่าง snapshot กับ master | **ใช้ master ได้** — ผลตัดสินพลิกแค่ **19 จาก 23,120 แถว (0.08%)** ฝั่งร้านใหม่พลิก 0 |
| **2.15** สาเหตุแถวค้าง `W` | เดาว่า W1 (master ไม่ครบ) ร้ายแรงสุด | **W1 = 0 แถว** · สาเหตุจริงคือ **W3 ไม่มีสัญญา SBP 2,684 แถว (87.6%)** + **`FPT1` ที่ `cancel_type` ≠ `06` 382 แถว (12.5%)** |
| หน่วยระยะทาง | ต้องเคาะกติกาแปลง | ALLMAP ส่ง **`กิโลเมตร` (ไทย) ค่าเดียว** 23,127 แถว · ไม่เคยส่ง `KM`/`M` |
| `DATASOURCE` | DDL เขียนว่า "ของเดิมมี HRS ปนอยู่" | **ไม่มี `HRS` เลย** — ALM 4,670 · STA 2,877 |

🔴 **ยังบล็อกอยู่:** `process_status` (ข้อ 2.17 — ตารางเดิม**ไม่มีคอลัมน์นี้เลย**) ·
นโยบายแถวค้าง `W` จากสาเหตุ W3/W5 (ข้อ 2.15 ส่วนที่เหลือ) ·
**ข้อใหม่ 2.37** `sales_request_status` ไม่มีค่าคู่กับ `N` ของเดิม 2,549 แถว ·
**ข้อใหม่ 2.38** ข้อมูลเดิมละเมิดคีย์กันซ้ำ 67+93+8 กลุ่ม ต้อง cleanup ก่อน migrate

## รายการเอกสาร

| Job | เอกสาร | เขียนครบ | ปิด open decision | implementation-ready |
|---|---|---|---|---|
| **Job 2** — ImportImpactStore | [JOB-02-ImportImpactStore-อธิบายละเอียด.md](JOB-02-ImportImpactStore-อธิบายละเอียด.md) | ✅ | ❌ | 🟡 เขียนโค้ดแล้ว |
| **Job 3** — ImportImpactCompetitor | [JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md](JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md) | ✅ | ❌ | 🟡 เขียนโค้ดแล้ว |
| **Job 4** — PrepareImpactStoreToIAS | [JOB-04-PrepareImpactStoreToIAS-อธิบายละเอียด.md](JOB-04-PrepareImpactStoreToIAS-อธิบายละเอียด.md) | ✅ | ❌ | 🟡 เขียนโค้ดแล้ว |
| **Job 5** — ImportImpactSaleFromIAS | [JOB-05-ImportImpactSaleFromIAS-อธิบายละเอียด.md](JOB-05-ImportImpactSaleFromIAS-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 6** — ExportImpactStoreToFS | [JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md](JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 7** — SyncCompetitorToDocument | [JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md](JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 8** — CreateCompensationDocument | [JOB-08-CreateCompensationDocument-อธิบายละเอียด.md](JOB-08-CreateCompensationDocument-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 8b** — StartInternalWorkflow | [JOB-08b-StartInternalWorkflow-อธิบายละเอียด.md](JOB-08b-StartInternalWorkflow-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 9** — SyncNewStoreToDocument | [JOB-09-SyncNewStoreToDocument-อธิบายละเอียด.md](JOB-09-SyncNewStoreToDocument-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 10** — NotifyNoReceiveData | [JOB-10-NotifyNoReceiveData-อธิบายละเอียด.md](JOB-10-NotifyNoReceiveData-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
| **Job 11** — ConsumeStaCompensate | [JOB-11-ConsumeStaCompensate-อธิบายละเอียด.md](JOB-11-ConsumeStaCompensate-อธิบายละเอียด.md) | ✅ | ❌ | ❌ ⚠️ ไม่มีโค้ดเดิม |
| **Job 12** — NotifyPendingWork | [JOB-12-NotifyPendingWork-อธิบายละเอียด.md](JOB-12-NotifyPendingWork-อธิบายละเอียด.md) | ✅ | ❌ | ❌ |
