# Job 11 — ConsumeStaCompensate : รับยอดชดเชยที่ STA คำนวณแล้วกลับเข้าเอกสาร

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
>
> ⚠️ **job นี้ไม่มีโค้ดเดิมใน `fcsJar/` เลย** — ต่างจาก Job 2–10 และ Job 12 ที่พอร์ตมาจากคลาส Java
> ระบบเดิมทำงานนี้ผ่าน **web service `/fgiService/updateCompensateFromFS`** ที่ฝั่ง STA เป็นคนเรียกเข้ามา
> (ค้น `batchjob/fcsJar/src/` แล้ว **ไม่พบ `updateCompensateFromFS` · `sta_update_compensate` · `amqp`/`RabbitMQ` เลยแม้แต่บรรทัดเดียว**)
> เอกสารฉบับนี้จึงเป็น **สเปกของงานที่สร้างใหม่** ไม่ใช่การอธิบายโค้ดเดิม
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 9 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.4 · 2.12 · 2.29 · 2.35 · 4.4**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-11-ConsumeStaCompensate-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **แหล่งความจริง** | `STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md` **ข้อ 3** (สัญญาข้อความ) · `job-batch.html` (ผัง) · `SBP/srm-sps-spsap-sop-sgi-batch.md` ข้อ 4 (RabbitMQ ของ repo ปลายทาง) |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-consume-sta-compensate` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-11-ConsumeStaCompensate` · **Job 6 (ขาส่งของสัญญาเดียวกัน)** ดู `batchjob/JOB-06-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

รับข้อความจาก STA ที่บอกว่า **"งวดนี้จ่ายจริงเท่าไร"** แล้วอัปเดตยอดเงินกลับเข้าเอกสารของ SGI

```
Job 6 ส่งไป STA          STA คำนวณ/ปรับยอด          Job 11 รับกลับ
sgi_impact_store  ──▶    (ระบบจ่ายเงินจริง)   ──▶   sta_update_compensate
                                                            │
                                                            ▼
                                              sgi_fgi_impact_compensations
```

**นี่คือ "ขากลับ" ของสัญญาเดียวกันกับ Job 6** — ปิดวงจรระหว่าง SGI กับ STA

### 🔴 ข้อสำคัญที่สุด — job นี้ **consume คิวเอง**

**มติ 2026-09-12** (แทนที่มติ 2026-09-08 ที่เคยให้ repo `store-consumer` เป็นตัวรับ — repo นั้นถูกตัดออกจากขอบเขตแล้ว)
**Job 11 ทำทุกอย่างเองใน `srm-sps-spsap-sop-sgi-batch`**

| หน้าที่ | ใครทำ |
|---|---|
| bind/consume คิว `srm.sgi.sta-update-compensate.queue` | **Job 11** |
| prefetch · ack · nack · requeue | **Job 11** |
| DLQ · retry policy | **Job 11** |
| อัปเดตยอดเงิน | **Job 11** |

> 🔴 **repo ปลายทางยังไม่มี consumer เลย** — `SBP/srm-sps-spsap-sop-sgi-batch.md` ข้อ 4 ระบุว่า
> *"ยังไม่มีตัวอย่าง consumer ใน repo นี้ — ทุกช่องเป็น publisher อย่างเดียว"*
> มีแต่ `publishMessage()` + `amqplib` · **ต้องสร้าง consumer · DLQ · retry ใหม่ทั้งชุด**
> **เป็นงานที่ยังไม่ได้ประเมินชั่วโมง**

> ⚠️ **job นี้เป็น event-driven ไม่มี cron** — `check_docs.py` มี guard ดักไม่ให้ประกาศ cron/schedule
> ถ้าตั้ง schedule จะ **consume ซ้อนกับตัวเองแล้วประมวลผลข้อความซ้ำ**

---

## 2. ทำไมต้องมี job นี้

SGI คำนวณ **ยอดที่ควรชดเชย** (forecast) และให้คนปรับได้ (adjust) แต่ **STA เป็นระบบที่จ่ายเงินจริง**
และอาจปรับยอดอีกชั้นตามกติกาของงบประมาณหรือรอบ statement

**ถ้าไม่รับยอดกลับ ระบบ SGI จะแสดงตัวเลขที่ไม่ตรงกับที่จ่ายจริง** — คนที่เปิดเอกสารดูย้อนหลังจะเห็นตัวเลขผิด

> 📌 **ปิดช่องว่างที่สเปก STA บังคับไว้แต่ยังไม่มีเอกสารรองรับ** (มติ 2026-09-02)
> สเปกข้อความของ STA มี `sta_update_compensate` มาตั้งแต่ต้น แต่ฝั่ง SGI ไม่เคยมี job รับ

**สายข้อมูลเต็ม:** `Job 6` (ส่งไป STA) → STA จ่ายเงิน → **`Job 11` (รับยอดจริงกลับ)** → หน้าจอเอกสาร

---

## 3. สัญญาข้อความ `sta_update_compensate`

```json
{
  "dataType": "message",
  "dataName": "sta_update_compensate",
  "dataMessage": [
    {
      "storeCodeI": "01213",
      "totalStoreCodeN": "1",
      "periodImpact": "6906",
      "impactStatus": "W",
      "forecast": "0.00",
      "adjust": "0.00",
      "compensate": [
        {
          "storeCodeN": "23760",
          "openDateN": "30/03/2026",
          "forecastN": "0.00",
          "forecastPercentN": "100.00",
          "adjustN": "0.00",
          "adjustPercentN": "",
          "createBy": "GBCE000",
          "createDate": "10/08/2026 17:15:09",
          "updateBy": "GBCE000",
          "updateDate": "10/08/2026 17:15:09"
        }
      ]
    }
  ],
  "sender": "SGI",
  "sentAt": "2025-07-11T15:00:00Z"
}
```

### ฟิลด์ระดับร้านถูกกระทบ

| ฟิลด์ | ความหมาย | ข้อควรระวัง |
|---|---|---|
| `storeCodeI` | รหัสร้านที่ถูกกระทบ | ข้อความ — **คงศูนย์นำหน้า** |
| `totalStoreCodeN` | จำนวนร้านเปิดใหม่ที่กระทบร้านนี้ | 🔴 ควรใช้ตรวจว่า `compensate[]` ครบไหม |
| `periodImpact` | งวดที่กระทบ | 🔴 **`yyMM` พ.ศ.** — `6906` = มิ.ย. 2026 |
| `impactStatus` | `W` = ยอดไม่เป็นศูนย์ · `Z` = ยอดเป็นศูนย์ | ตามกติกาเดิมของ `/fgiService/updateCompensateFromFS` |
| `forecast` / `adjust` | **ยอดรวม**ของร้านที่ถูกกระทบ | เป็น **string** ไม่ใช่ number |

### ฟิลด์ระดับร้านเปิดใหม่ (`compensate[]`)

| ฟิลด์ | ความหมาย | ข้อควรระวัง |
|---|---|---|
| `storeCodeN` | รหัสร้านเปิดใหม่ | |
| `openDateN` | วันเปิดร้านใหม่ | 🔴 **`dd/MM/yyyy` ค.ศ.** — ต่างจาก `periodImpact` ที่เป็น พ.ศ. |
| `forecastN` · `adjustN` | ยอดแยกรายร้าน | string |
| `forecastPercentN` · `adjustPercentN` | %ชดเชยแยกรายร้าน | 🔴 **ค่าว่างเป็น `""` ไม่ใช่ `null`** |
| `createBy` · `createDate` · `updateBy` · `updateDate` | audit | `dd/MM/yyyy HH:mm:ss` |

### 🔴 ปัญหาในสัญญาที่ต้องยืนยันกับทีม STA

**A. `"sender": "SGI"` ในข้อความที่ STA ส่งมา**

ตัวอย่างในสเปกระบุ `sender: "SGI"` ทั้งที่ข้อความนี้เป็น **STA → SGI**
ถ้าตรวจ `sender` เพื่อยืนยันต้นทาง จะตรวจไม่ผ่าน (หรือถ้าตรวจว่าต้องเป็น `"SGI"` ก็ผิดความหมาย)

**B. สองปฏิทินในข้อความเดียวกัน**

| ฟิลด์ | ปฏิทิน |
|---|---|
| `periodImpact` = `"6906"` | **พ.ศ.** |
| `openDateN` = `"30/03/2026"` | **ค.ศ.** |
| `createDate` = `"10/08/2026 17:15:09"` | **ค.ศ.** |

> 🔴 **ต้องยืนยันทั้งสองข้อกับทีม STA ก่อนเขียนโค้ด** — เดาผิดแปลว่าอัปเดตผิดงวด

**C. ตัวเลขส่งมาเป็น string**

`"0.00"` · `"100.00"` · `""` — ต้องแปลงเป็นตัวเลขและแยก `""` ออกจาก `"0.00"` ให้ได้
**`""` = ไม่มีค่า** ≠ **`"0.00"` = ศูนย์**

---

## 4. ภาพรวมการทำงาน

```
① consume ข้อความจากคิว แล้วอ่าน envelope
      ▼
② ตรวจ dataName == 'sta_update_compensate'
      │ ไม่ตรง ──▶ log warn แล้วจบแบบสำเร็จ
      ▼
③ ตรวจ envelope + schema ของ dataMessage
      │ ผิดรูป ──▶ ส่งเข้า DLQ เอง
      ▼
④ กันซ้ำด้วย sgi_interface_transactions (direction = IN)
      │ เคยรับแล้ว ──▶ จบแบบสำเร็จ (ไม่อัปเดตซ้ำ)
      ▼
⑤ transaction เดียว: อัปเดตยอดเงินของงวดที่ระบุ
      ▼
⑥ ack เมื่อสำเร็จ · nack/DLQ เมื่อล้มเหลว
```

### ขั้นที่ ② — `dataName` ไม่ตรงแล้วทำอย่างไร

ผังระบุ: **`no: 'จบการทำงาน'` · `noKind: 'end'`** — ข้ามข้อความที่ `dataName` ไม่ตรง (log warn + ack ทิ้ง)

> 🔴 **แต่ `dataName` อาจไม่มีมาให้ตรวจเลย** — `DECISIONS` ข้อ **2.12**:
> ตรวจ 4 แหล่งแล้ว **3 ใน 4 มี `dataName`** (`sop-sgi-batch` ✅ · `store-backend` ✅ · สเปก STA ✅)
> ✅ **ปิดแล้ว 2026-09-12** — เมื่อ job consume คิวเอง **ไม่มีตัวกลางมาตัด `dataName` ทิ้งอีก**
> job อ่าน envelope ดิบจากคิวโดยตรง จึงเห็นทุกฟิลด์ที่ต้นทางส่งมา
> ⏳ เหลือแค่ยืนยันกับทีม STA ว่าส่ง `dataName` มาจริงตามสเปก

### ขั้นที่ ④ — กันซ้ำ

```sql
INSERT INTO sgi_interface_transactions
  (data_name, direction, status, business_key, period_key, impact_process_id, acked_at, created_at)
VALUES ('STA_UPDATE_COMPENSATE', 'IN', 'COMPLETED', :store_code_i, :period_key, :impact_process_id, now(), now())
ON CONFLICT (data_name, direction, business_key, period_key) DO NOTHING;
```

ถ้า `DO NOTHING` (ไม่ได้แถวใหม่) แปลว่า **เคยรับข้อความของ (ร้าน + งวด) นี้แล้ว**

> 🔴 **ต้องเคาะว่า "รับซ้ำ" หมายถึงอะไร** — STA ส่ง **Real Time** และอาจส่งอัปเดตยอดใหม่ของงวดเดิมได้
> ถ้ากันซ้ำด้วย (ร้าน + งวด) เฉย ๆ **ยอดที่ปรับใหม่จะถูกทิ้ง** (ดูหัวข้อ 9)

---

## 5. ขั้นที่ ⑤ — อัปเดตยอดเงิน

### หาแถวปลายทาง

```sql
-- 1. แปลงงวดจาก พ.ศ. yyMM เป็น ค.ศ. YYYY-MM
--    '6906' -> พ.ศ. 2569 เดือน 06 -> ค.ศ. '2026-06'
-- 2. หา impact_process_id
SELECT id FROM sgi_fgi_impact_processes
 WHERE impacted_store_code = :store_code_i
   AND impact_month = :period_key_ce;
```

### อัปเดตยอดรวม

```sql
UPDATE sgi_fgi_impact_compensations
   SET forecast_amount = :forecast,
       adjust_amount   = :adjust,
       updated_by = 'JOB11', updated_at = now()
 WHERE impact_process_id = :impact_process_id
   AND compensate_month  = :period_key_ce;
```

**คีย์ปลายทาง** — `uq_impact_compensation UNIQUE (impact_process_id, compensate_month)` ✅ ตรงกับคีย์ในข้อความ

### 🔴 A — ยอดแยกรายร้านใหม่ (`compensate[]`) ไม่มีที่ลง

ข้อความมี `compensate[]` ที่ให้ **ยอดและ %แยกรายร้านเปิดใหม่** ครบทุกร้าน
แต่ **ตารางที่ผังประกาศไว้ไม่มีตัวไหนเก็บได้:**

| ตารางที่ผังประกาศ | เก็บอะไร |
|---|---|
| `sgi_interface_transactions` (W) | บันทึกการรับข้อความ |
| `sgi_fgi_impact_compensations` (W) | **ยอดรวมของร้านถูกกระทบเท่านั้น** (`forecast_amount` · `adjust_amount`) |
| `sgi_fgi_impact_processes` (R) | หา `impact_process_id` |

**ยอดรายร้านใหม่ควรลงที่ `sgi_document_new_stores`** (`compensate_percent` · `compensation_amount`)
ซึ่งเป็นตารางที่ **Job 9 เป็นคนเขียน** — แต่ Job 11 ไม่ได้ประกาศตารางนี้ไว้

| ทางเลือก | ผล |
|---|---|
| **ก. ให้ Job 11 เขียน `sgi_document_new_stores` ด้วย** | ข้อมูลตรงกับที่ STA จ่ายจริง · ❌ **ชนกับ Job 9 ที่เขียนตารางเดียวกัน** |
| **ข. เก็บแค่ยอดรวม ทิ้ง `compensate[]`** | ง่าย · ❌ **หน้าจอจะแสดง %ชดเชยที่ไม่ตรงกับที่จ่ายจริง** |
| **ค. เพิ่มตารางเก็บยอดที่ STA แจ้งกลับแยกต่างหาก** | ตรวจย้อนหลังได้ว่า SGI คิดเท่าไร STA จ่ายเท่าไร · ต้องเพิ่มตาราง |

> 🔴 **ต้องเคาะก่อนเขียนโค้ด** — ถ้าเลือก ก. ต้องระบุว่าใครชนะเมื่อ Job 9 กับ Job 11 เขียนทับกัน

### 🔴 B — `impactStatus` ใช้ทำอะไร

| ค่า | ความหมาย |
|---|---|
| `W` | ยอดไม่เท่ากับศูนย์ |
| `Z` | ยอดเท่ากับศูนย์ |

**เป็นข้อมูลซ้ำซ้อนกับตัวเลขที่ส่งมาด้วย** (`forecast` / `adjust`) — ถ้า `adjust = "0.00"` ก็รู้อยู่แล้วว่าเป็นศูนย์

| ทางเลือก | เหตุผล |
|---|---|
| **ก. ใช้ตรวจสอบความสอดคล้อง** | `impactStatus = 'Z'` แต่ยอดไม่เป็นศูนย์ = ข้อความผิด → reject |
| **ข. เก็บลง `compensate_status`** | ⚠️ **`Z` มีอยู่ในโดเมนแล้ว** (`CHECK IN ('I','C','A','N','S','Z')`) แต่ `W` **ไม่มี** |
| **ค. ไม่ใช้เลย** | ยึดตัวเลขอย่างเดียว |

> 🔴 **ทางเลือก ข. ทำไม่ได้ตรงๆ** — `impactStatus = 'W'` ไม่อยู่ในโดเมนของ `compensate_status`
> ถ้าจะ map ต้องระบุกติกาแปลง (`W` → อะไร) หรือขยายโดเมน

### 🔴 C — เอกสารที่ปิดไปแล้ว ยังรับยอดอัปเดตได้ไหม

STA ส่ง **Real Time** — อาจส่งยอดกลับมาหลังจากเอกสารเดินผ่าน workflow จบไปแล้ว

| สถานการณ์ | ต้องทำอย่างไร |
|---|---|
| เอกสารยังอยู่ใน workflow | อัปเดตได้ |
| เอกสารจบแล้ว (อนุมัติ/ไม่อนุมัติ) | 🔴 **อัปเดตยอดจะทำให้ตัวเลขบนเอกสารที่ปิดแล้วเปลี่ยน** |
| ร้าน + งวด ที่ไม่มีในระบบเลย | 🔴 reject หรือ log แล้วข้าม? |

> 🔴 **ต้องเคาะ** — เอกสารที่ปิดแล้วควรถูกแก้ตัวเลขย้อนหลังหรือไม่ · ถ้าไม่ควรจะจัดการข้อความนั้นอย่างไร

---

## 6. เขียนลงฐานข้อมูลใหม่ตรงไหน

### ค่าที่ต้องใส่ใน `sgi_interface_transactions`

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | **`'STA_UPDATE_COMPENSATE'`** |
| `direction` | **`'IN'`** |
| `status` | **`'COMPLETED'`** |
| `outbox_status` | **ไม่ต้องใส่** — เป็นขาเข้า ไม่มี broker publish |
| `impact_process_id` | typed FK |
| `business_key` | `storeCodeI` |
| `period_key` | งวดที่แปลงเป็น **ค.ศ.** แล้ว |
| `acked_at` | เวลาที่รับ |

> ⚠️ **`period_key` ต้องเก็บเป็น ค.ศ.** — ข้อความส่งมาเป็น พ.ศ. (`6906`) แต่ **ห้ามให้ พ.ศ. ปนเข้า DB**
> (กติกาทั้งระบบ · `check_docs.py` มี guard ดักปี พ.ศ. ใน payload/doc_no)

### ค่าที่อัปเดตใน `sgi_fgi_impact_compensations`

| คอลัมน์ | ที่มาในข้อความ | ข้อควรระวัง |
|---|---|---|
| `forecast_amount` | `forecast` | string → `NUMERIC(14,2)` |
| `adjust_amount` | `adjust` | 🔴 **`""` ต้องเป็น `NULL` ไม่ใช่ `0`** |
| `updated_by` | `'JOB11'` | |

> 🔴 **`adjust_amount` เป็น NULL vs 0 ต่างกันมาก** — กติกาทั้งระบบใช้ `COALESCE(adjust_amount, forecast_amount)`
> ถ้าแปลง `""` เป็น `0` **ยอดที่ใช้จริงจะกลายเป็นศูนย์ทันที** ทั้งที่ควรใช้ค่า forecast

---

## 7. ตัวเลขที่ job ต้องรายงานทุกรอบ

**job นี้รัน 1 ข้อความต่อ 1 การรัน** — metric จึงเป็นรายข้อความ ไม่ใช่รายรอบแบบ job อื่น

| ชื่อ | บันทึกอะไร |
|---|---|
| `dataName` · `sender` · `sentAt` | จาก envelope — ตามรอยกลับไปหาข้อความต้นทาง |
| `messageItemCount` | จำนวนรายการใน `dataMessage[]` |
| `storeCodeI` · `periodImpact` · `periodKeyCe` | คีย์ที่ประมวลผล + งวดที่แปลงเป็น ค.ศ. แล้ว |
| `duplicateSkipped` | `true` ถ้าเคยรับแล้ว |
| `compensateItemCount` vs `totalStoreCodeN` | 🔴 **ต้องเท่ากัน** — ไม่เท่าแปลว่าข้อความไม่ครบ |
| `processNotFound` | `true` ถ้าหา `impact_process_id` ไม่เจอ · 🔴 **ต้อง alert** |
| `documentClosed` | `true` ถ้าเอกสารจบไปแล้ว · 🔴 **ต้อง alert** |
| `amountBefore` · `amountAfter` | 🔴 **ยอดก่อน/หลังอัปเดต** — จำเป็นสำหรับ audit เรื่องเงิน |
| `durationMs` | เวลาที่ใช้ |

- 🔴 **alert เมื่อ `processNotFound = true`** — STA ส่งยอดของร้าน/งวดที่ SGI ไม่รู้จัก
- 🔴 **alert เมื่อ `amountBefore ≠ amountAfter` อย่างมีนัยสำคัญ** — STA ปรับยอดต่างจากที่ SGI คิดมาก

---

## 8. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — envelope และ schema

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | `dataName = 'sta_update_compensate'` ถูกต้อง | ประมวลผลต่อ |
| 1.2 | `dataName` เป็นค่าอื่น | log warn · **ack ทิ้ง** (ไม่ใช่ข้อความของเรา) |
| 1.3 | 🔴 **ไม่มีฟิลด์ `dataName` เลย** | ✅ **ตัดสินแล้ว — reject → DLQ** (สเปก STA ระบุเป็นฟิลด์บังคับ · ข้อความที่ไม่มีจึงไม่ใช่ข้อความที่สเปกรองรับ) |
| 1.4 | `dataMessage` เป็นอาร์เรย์ว่าง | จบแบบสำเร็จ · ไม่อัปเดตอะไร |
| 1.5 | `dataMessage` ผิด schema (ขาดฟิลด์บังคับ) | ❌ **ส่งเข้า DLQ เอง** — ห้าม requeue วนไม่จบ |
| 1.6 | `sender = 'SGI'` (ตามตัวอย่างในสเปก) | 🔴 **ต้องเคาะว่าตรวจ `sender` ไหม** — ตัวอย่างขัดกับทิศทางข้อความ |
| 1.7 | JSON ไม่ถูกต้อง | ❌ ส่งเข้า DLQ |

### กลุ่มที่ 2 — การแปลงค่า

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | `periodImpact = '6906'` | แปลงเป็น **`'2026-06'` (ค.ศ.)** |
| 2.2 | `periodImpact = '6812'` | **`'2025-12'`** — ข้ามปีถูก |
| 2.3 | `periodImpact` รูปแบบผิด (`'202606'`) | ❌ reject → DLQ |
| 2.4 | `openDateN = '30/03/2026'` | ตีความเป็น **ค.ศ.** (ต่างจาก `periodImpact`) |
| 2.5 | `forecast = '0.00'` | `forecast_amount = 0` |
| 2.6 | 🔴 **`adjust = ''`** | **`adjust_amount = NULL`** ไม่ใช่ `0` |
| 2.7 | `adjustPercentN = ''` | เก็บเป็น NULL |
| 2.8 | `storeCodeI = '01213'` | **คงศูนย์นำหน้า** — ห้าม `parseInt` |
| 2.9 | ตัวเลขมี comma (`'1,234.00'`) | ✅ **ตัดสินแล้ว — reject** · ไม่เดาให้ เพราะการตีความ `1,234` ต่างกันได้ทั้ง 1234 และ 1.234 แล้วแต่ locale — ตัวเลขเงินเดาไม่ได้ |

### กลุ่มที่ 3 — การอัปเดตยอด

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | ร้าน + งวด มีในระบบ · เอกสารยังไม่จบ | อัปเดต `forecast_amount` · `adjust_amount` |
| 3.2 | 🔴 **หา `impact_process_id` ไม่เจอ** | 🔴 **ต้องเคาะ** — reject → DLQ หรือ log แล้วข้าม |
| 3.3 | 🔴 **เอกสารจบไปแล้ว** | 🔴 **ต้องเคาะ** — อัปเดตย้อนหลังหรือปฏิเสธ |
| 3.4 | `compensate[]` มี 3 ร้าน · `totalStoreCodeN = '3'` | ✅ สอดคล้อง |
| 3.5 | 🔴 **`compensate[]` มี 2 ร้าน แต่ `totalStoreCodeN = '3'`** | ❌ **reject** — ข้อความไม่ครบ |
| 3.6 | 🔴 **`impactStatus = 'Z'` แต่ `adjust = '150.00'`** | ❌ **reject** — ข้อความขัดแย้งในตัวเอง |
| 3.7 | ยอดรายร้านใน `compensate[]` | ✅ **ปิดแล้ว 2026-09-13 — ลงที่ `sgi_fgi_new_store_compensations`** (ตรงกับข้อความแบบ 1:1 ทุกฟิลด์) · 🔴 **แต่ยอดที่ปรับไม่ไหลถึง `sgi_compensation_documents.total_compensation_amount`** ซึ่งเขียนครั้งเดียวตอน Job 8 สร้างเอกสาร — Job 9 ตรวจเจอและเตือน แต่**ยังต้องให้ธุรกิจเคาะ**ว่าหัวเอกสารควรตามยอดจริงหรือไม่ |
| 3.8 | `dataMessage` มี 2 รายการ (2 ร้าน) | ประมวลผลทั้งสองใน **transaction เดียว** |

### กลุ่มที่ 4 — กันซ้ำและความคงทน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | ข้อความเดิมถูกส่งซ้ำ (redelivery) | **ไม่อัปเดตซ้ำ** · จบแบบสำเร็จ · `duplicateSkipped = true` |
| 4.2 | 🔴 **STA ส่งยอด*ใหม่*ของงวดเดิม** | 🔴 **ต้องเคาะ** — กันซ้ำด้วย (ร้าน+งวด) จะทิ้งยอดใหม่ทิ้ง |
| 4.3 | ล้มกลาง transaction | rollback · **ไม่มีแถว `sgi_interface_transactions`** ค้าง · nack + requeue |
| 4.4 | commit สำเร็จแต่ตายก่อน ack | ข้อความถูก requeue → รอบหน้ากันซ้ำจับได้ |
| 4.5 | ⚠️ **job มี cron/schedule** | ❌ **ต้องไม่มี** — จะ consume ซ้อนกับตัวเอง |
| 4.6 | 🔴 **poison message วนไม่จบ** | ต้องมี **retry limit → DLQ** · repo ปลายทางยังไม่มีกลไกนี้ |
| 4.7 | ประมวลผลสำเร็จ | **ack** ข้อความ |
| 4.8 | ประมวลผลล้มเหลว | **nack/DLQ** ตาม policy |

---

## 9. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **ยอดแยกรายร้านใหม่ (`compensate[]`) ลงที่ไหน** | เอกสารฉบับนี้เสนอ 3 ทางที่ล้วนมีปัญหา | ✅ **ปิดแล้ว 2026-09-13 — ลง `sgi_fgi_new_store_compensations`** · เอกสารนี้เขียนไว้**ตอนที่ตารางนี้ยังไม่มี** (เพิ่มตอนทำ Job 6 เมื่อ 2026-09-13) · **ไม่ต้องเพิ่มตารางใหม่ และไม่ชนกับ Job 9** — ดูด้านล่าง |

### ✅ `compensate[]` ลงตารางที่มีอยู่แล้วแบบ 1:1

`sgi_fgi_new_store_compensations` ถูกเพิ่มตอนทำ Job 6 (ค่าชดเชยฝั่งร้านเปิดใหม่ **รายงวด**)
และ **ตรงกับ `compensate[]` ทุกฟิลด์**:

| ฟิลด์ในข้อความ STA | คอลัมน์ |
|---|---|
| `storeCodeN` | `new_store_code` |
| `forecastN` | `forecast_amount` |
| `forecastPercentN` | `forecast_percent` |
| `adjustN` | `adjust_amount` |
| `adjustPercentN` | `adjust_percent` |

คีย์ `uq_new_store_compensation (impact_compensation_id, new_store_code)` = **(งวด, ร้านใหม่)**
ตรงกับคีย์ในข้อความพอดี

> ✅ **ไม่ชนกับ Job 9** — คนละชั้นกัน
> **Job 11 เขียนชั้น pipeline** (`sgi_fgi_new_store_compensations`) ·
> **Job 9 อ่านชั้นนั้นไปเขียนชั้นเอกสาร** (`sgi_document_new_stores`)
> รัน Job 9 ซ้ำหลัง Job 11 แล้วเอกสารจะตามยอดจริงที่ STA จ่ายเอง
| 🔴 **"รับซ้ำ" หมายถึงอะไร** | ต้องแยก "redelivery" ออกจาก "ยอดอัปเดตรอบใหม่" | ✅ **ปิดแล้ว 2026-09-13 — เทียบ `sentAt`** · คงคีย์ `UNIQUE (data_name, direction, business_key, period_key)` ไว้ แต่ใช้ `ON CONFLICT ... DO UPDATE ... WHERE sent_at IS NULL OR sent_at < EXCLUDED.sent_at` · `sentAt` เท่าเดิม/เก่ากว่า = **redelivery → ข้าม** · ใหม่กว่า = **ยอดอัปเดตรอบใหม่ → รับ** · ยืนยันกับ PostgreSQL 16 จริงแล้ว |
| 🔴 **เอกสารที่ปิดแล้วรับยอดอัปเดตไหม** | STA อาจส่งยอดกลับหลังเอกสารจบ workflow | ⚙️ **ทำเป็น config `SGI_JOB11_CLOSED_POLICY`** ค่าตั้งต้น **`update`** — ตัวเลขที่แสดงต้องตรงกับเงินที่จ่ายจริง (เหตุผลที่ job นี้มีอยู่) พร้อม log warn ทุกครั้ง · ตั้ง `skip` ได้ถ้าธุรกิจไม่ยอมให้แก้เอกสารที่ปิดแล้ว · 🔴 **ยังต้อง business sign-off** |
| 🔴 **`sender` และปฏิทินในสัญญา** | ตัวอย่างในสเปกระบุ `"sender": "SGI"` ทั้งที่เป็นข้อความ **STA → SGI** · และมี **สองปฏิทินในข้อความเดียว** (`periodImpact` พ.ศ. · `openDateN`/`createDate` ค.ศ.) | 🔴 **ต้องยืนยันกับทีม STA** · ผูกกับ **4.4** (พ.ศ./ค.ศ.) |
| 🔴 **`impactStatus` (`W`/`Z`) ใช้ทำอะไร** | เป็นข้อมูลซ้ำซ้อนกับตัวเลข | ✅ **ปิดแล้ว 2026-09-13 — เลือก (ก) ใช้เป็น checksum ของข้อความ** · `Z` แต่ยอดไม่เป็นศูนย์ หรือ `W` แต่ยอดเป็นศูนย์ = **ข้อความขัดแย้งกับตัวเอง** → log warn + นับใน `consistencyIssueCount` · map ลงคอลัมน์ไม่ได้เพราะ **`W` ไม่มีในโดเมน** `compensate_status` · `totalStoreCodeN` ใช้แบบเดียวกัน (ตรวจว่า `compensate[]` ถูกตัดระหว่างทางไหม) |
| 🔴 **หา `impact_process_id` ไม่เจอ** | STA ส่งยอดของร้าน/งวดที่ SGI ไม่รู้จัก | ✅ **ปิดแล้ว 2026-09-13 — DLQ + alert** · ส่งซ้ำก็ไม่รู้จักเหมือนเดิม จึงเป็นความล้มเหลว**ถาวร** ห้าม requeue (poison message) · เข้า DLQ พร้อม header `x-sgi-dead-letter-reason` และ job จบเป็น `FAILED` เพราะยอดที่จ่ายจริงยังไม่เข้าระบบ |
| **`dataName` อาจไม่มีมาให้ตรวจ** | ~~zod schema ของตัวกลางไม่มีฟิลด์นี้~~ | ✅ **ปิดแล้ว** `DECISIONS` ข้อ **2.12** — ไม่มีตัวกลางแล้ว · เหลือยืนยันกับทีม STA |
| 🔴 **ต้องสร้าง consumer · DLQ · retry ใหม่ทั้งชุด** | repo มีแต่ `publishMessage` | ✅ **สร้างแล้ว 2026-09-13** — `src/modules/sgi/sgi-rabbit.consumer.ts` · prefetch · ack/nack · DLQ พร้อมเหตุผลใน header · แยก **RETRY** (ชั่วคราว · requeue จำกัดครั้ง) ออกจาก **DEAD_LETTER** (ถาวร · ไม่ requeue) · จบเมื่อคิวว่างเพื่อให้เข้ากับโมเดล AWS Batch ที่ job ต้องมีจุดจบ |
| **ชื่อ queue / routing key** | `srm.sgi.sta-update-compensate.queue` | ⏳ **ต้อง confirm กับทีม STA** |
| **โครง `sgi_interface_transactions`** | ยังไม่เคาะว่าออกแบบใหม่หรือลอกแพตเทิร์น | 🔴 `DECISIONS` ข้อ **2.4 (DP-6)** |

---

## 10. ข้อควรระวังเฉพาะของ job ที่ **ไม่มีโค้ดเดิม**

Job 2–10 และ Job 12 พอร์ตมาจากคลาส Java ที่รันจริงมาหลายปี — **มีพฤติกรรมให้เทียบ**
Job 11 ไม่มี จึงต้องระวังคนละแบบ

| # | ข้อควรระวัง | ทำไม |
|---|---|---|
| **N1** | **ไม่มีข้อมูลจริงให้เทียบผลลัพธ์** | ทดสอบได้แค่ตามสเปก · **ต้องขอตัวอย่างข้อความจริงจากทีม STA ก่อน UAT** |
| **N2** | **สเปกมาจากไฟล์ Excel ที่แปลงเป็น markdown** | ตัวอย่าง JSON คัดลอกมา verbatim — **ข้อผิดพลาดในต้นฉบับ (เช่น `sender: "SGI"`) จึงติดมาด้วย** |
| **N3** | **ไม่รู้ว่า STA ส่งบ่อยแค่ไหน** | "Real Time" อาจแปลว่าทุกครั้งที่มีการเปลี่ยนแปลง → ปริมาณข้อความอาจสูงกว่าที่คิด |
| **N4** | **ไม่รู้ว่า STA ส่งย้อนหลังไหม** | ถ้าส่งงวดเก่ามาด้วย ต้องมีกติกาว่ารับถึงงวดไหน |
| **N5** | **repo ปลายทางยังไม่มี consumer เลย** | มีแต่ `publishMessage` · ต้องสร้าง consumer · DLQ · retry ใหม่ทั้งชุด **ก่อนจะทดสอบ end-to-end ได้** |
| **N6** | **ห้ามลอกโครงจาก Job 5** | Job 5 ก็ consume คิวเองเหมือนกัน **แต่ Job 5 มี cron เป็น safety net ส่วน Job 11 ไม่มี** — ถ้าลอกมาจะได้ cron ที่ทำให้ consume ซ้อน |

> ✅ **`check_docs.py` มี guard ดักไว้แล้ว** — *"job ที่ event-driven ยังมี cron/schedule ในเอกสาร"*
> และ *"job ที่ consumer เป็นตัวกระตุ้น แต่ยังประกาศ cron"* (ชื่อกฎยังเป็นของเดิม)

---

## 11. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 6 (ขาส่งของสัญญาเดียวกัน) | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` |
| Job 9 (เขียน `sgi_document_new_stores` ที่อาจชนกัน) | `batchjob/JOB-09-SyncNewStoreToDocument-อธิบายละเอียด.md` |
| Job 10 (watchdog ของขาออก) | `batchjob/JOB-10-NotifyNoReceiveData-อธิบายละเอียด.md` |
| **สัญญาข้อความเต็ม** | `STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md` ข้อ 3 |
| RabbitMQ ของ repo ปลายทาง (ยังมีแต่ publisher) | `SBP/srm-sps-spsap-sop-sgi-batch.md` ข้อ 4 |
| สเปกรูปแบบมาตรฐานของ Job 11 | `LLDD/md/Jobs/LLDD-BE-Job-11-ConsumeStaCompensate.md` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
