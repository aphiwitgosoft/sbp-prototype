# Job 10 — NotifyNoReceiveData : Watchdog เฝ้าข้อความขาออกที่ค้างส่ง

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 9 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.4 · 2.34 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-10-NotifyNoReceiveData-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/NotifyNoReceiveData.java` · `controller/ManageCompensateController.java` (`genMessageMailNotifyNoReceiveData`) · `dao/jdbc/ExportJdbc.java` (`queryNotifyNoReceiveData`) · `utils/SendMailUtil.java` · `Constant/FgiConstant.java` |
> | **เขียนลงฐานข้อมูล** | **อ่านอย่างเดียว** — ยกเว้น marker กันเตือนซ้ำ (ดูหัวข้อ 6) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-notify-no-receive-data` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-10-NotifyNoReceiveData` · **Job 6 (ต้นทางข้อความที่เฝ้าอยู่)** ดู `batchjob/JOB-06-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

**เป็นยามเฝ้า** — ตรวจทุกเช้าว่ามีข้อความที่ส่งออกไปแล้วแต่ **ปลายทางยังไม่ยืนยันรับ** ค้างอยู่หรือไม่
ถ้ามีก็ส่งอีเมลเตือนให้คนมาตาม

```
sgi_interface_transactions (direction = OUT)
        │
        │  หาแถวที่ยังไม่ CONFIRMED และค้างเกิน 1 วัน
        ▼
   อีเมลเตือน + หน้า /sgi/interface/pending-ack
```

**job นี้ไม่แก้อะไรเลย** — ไม่ส่งซ้ำ ไม่เปลี่ยนสถานะ **แค่บอกว่ามีอะไรค้าง**
คนที่ได้รับเมลต้องไปสั่ง republish จากหน้า pending-ack เอง

### 🔴 เกณฑ์เปลี่ยนไปแล้ว — จาก "ACK" เป็น "publisher confirm"

| | ระบบเดิม | ระบบใหม่ (มติ 2026-09-08 · ข้อ 2.13) |
|---|---|---|
| เฝ้าอะไร | `return_code IS NULL` ใน `FGI_CONFIRM_RECEIVE_DATA` | **`outbox_status != 'CONFIRMED'`** |
| ความหมาย | STA ยังไม่ตอบกลับ (ACK ระดับธุรกิจ) | **broker ยังไม่ยืนยันรับข้อความ** (publisher confirm) |
| ทำไมเปลี่ยน | — | **สเปก STA ไม่มี ACK แบบ HTTP** — เส้น `POST /sgi/interface/sta/ack` ถูกตัดทิ้ง |

> 📌 **ชื่อ endpoint `/sgi/interface/pending-ack` คงไว้เพื่อ compatibility** แต่ความหมายเปลี่ยนแล้ว
> **ห้ามเขียนในเอกสารว่า "รอ ACK จาก STA"** — `check_docs.py` มี guard ดักคำนี้อยู่

---

## 2. ทำไมต้องมี job นี้

Job 6 ส่งข้อมูลค่าชดเชยไป STA ผ่าน RabbitMQ ด้วย **transactional outbox**
ถ้า broker ล่มหรือ publish ล้ม แถวจะค้างอยู่ที่ `outbox_status = 'READY'` แล้ว dispatcher จะส่งซ้ำให้

**แต่ถ้า dispatcher เองก็ล้มหรือค้าง จะไม่มีใครรู้เลย** — ข้อมูลไม่ได้หาย แต่ก็ไม่ได้ไปถึงปลายทาง
และเนื่องจาก Job 6 คือ **สะพานเส้นสุดท้ายก่อนเงินออก** การค้างเงียบ ๆ แปลว่า **ร้านไม่ได้เงิน**

Job 10 จึงเป็น **safety net ชั้นสุดท้าย** — ไม่ซ่อมอะไร แต่ทำให้ความเงียบนั้นดังขึ้น

**สายข้อมูลเต็ม:** `Job 6` (ส่งไป STA) → RabbitMQ → STA · **`Job 10` เฝ้าดูว่าขั้นตอนนี้ติดขัดไหม**

---

## 3. ภาพรวมการทำงาน

```
① query หาแถวขาออกที่ค้าง
      │  ไม่มี ──▶ จบ (ไม่ส่งอีเมล)
      ▼
② ประกอบข้อความเตือน
      ▼
③ ส่งอีเมล
```

**สั้นที่สุดในบรรดา 12 job** — ไม่มี transaction ไม่มีการเขียนข้อมูล

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — job นี้ **รายงานสำเร็จเสมอ**

```java
if (!"".equals(message)) {
    informBean.setNote(message);            // ← ใส่รายการค้างเป็น "โน้ต"
}
informBean.setStatus(FgiConstant.JOB_STATUS_SUCCESS);   // ← SUCCESS ไม่ว่าจะมีค้างหรือไม่
```

**การพบรายการค้างไม่ได้ทำให้ job มีสถานะผิดปกติ** — รายการค้างถูกใส่เป็น **โน้ตในอีเมลสถานะปกติ**
ซึ่งเป็นอีเมลฉบับเดียวกับที่ job อื่น ๆ ส่งทุกวัน

> ⚠️ **แปลว่าคำเตือนไปปนอยู่กับเมลสถานะประจำวัน** — ถ้าคนดูแลชินกับการเห็นเมล "job สำเร็จ" ทุกเช้า
> **คำเตือนจะถูกอ่านข้าม** · job ที่มีหน้าที่เดียวคือ "ทำให้ความเงียบดังขึ้น" กลับเงียบเสียเอง

> ✅ **ระบบใหม่ต้องแยกให้ชัด** — พบรายการค้าง = **alert** ไม่ใช่โน้ตท้ายเมลสถานะ

---

## 4. ขั้นที่ ① — query หาแถวที่ค้าง

```sql
select rd1.data_name, rd1.interface_type,
       count(rd1.interface_type) as count_data,
       count(rd1.return_code)    as count_return_code
  from fgi_confirm_receive_data rd1
 where exists (
         select rd2.data_name, rd2.transaction_pk
           from fgi_confirm_receive_data rd2
          where rd2.data_name in ('COMPENSATE_INIT_I', 'COMPENSATE_APPROVE_I')
            and return_code is null
            and interface_type != 'WS'
            and trunc(create_date) <= trunc(sysdate-1)
            and rd2.data_name      = rd1.data_name
            and rd2.interface_type = rd1.interface_type
       )
 group by rd1.data_name, rd1.interface_type
 order by rd1.data_name, rd1.interface_type
```

### แปลเป็นภาษาคน

**ชั้นใน (`EXISTS`)** — หาว่ามีแถวที่เข้าเงื่อนไข "ค้าง" อยู่ในกลุ่มนี้ไหม:

| เงื่อนไข | ความหมาย |
|---|---|
| `data_name IN ('COMPENSATE_INIT_I','COMPENSATE_APPROVE_I')` | 🔴 **เฉพาะฝั่ง `I` เท่านั้น** (ดูด้านล่าง) |
| `return_code is null` | ปลายทางยังไม่ตอบกลับ |
| `interface_type != 'WS'` | ไม่นับรายการที่ส่งผ่าน web service |
| `trunc(create_date) <= trunc(sysdate-1)` | **ค้างมาแล้วอย่างน้อย 1 วัน** |

**ชั้นนอก** — จัดกลุ่มตาม (`data_name`, `interface_type`) แล้วนับสองตัว

### 🔴 A — ตัวเลขที่รายงานไม่ใช่ "จำนวนที่ค้าง"

```
count(rd1.interface_type) as count_data          -- นับ "ทุกแถว" ในกลุ่มนี้
count(rd1.return_code)    as count_return_code   -- นับเฉพาะแถวที่ "มี" return_code
```

**ชั้นนอกไม่ได้กรองเงื่อนไข "ค้าง" เลย** — `EXISTS` แค่บอกว่ากลุ่มนี้ **มีแถวค้างอย่างน้อย 1 แถว**
แล้วชั้นนอกนับ **ทุกแถวของกลุ่ม** ไม่ว่าจะค้างหรือไม่

| ตัวเลขในอีเมล | หมายถึง |
|---|---|
| `COUNT_DATA` | จำนวนแถวทั้งหมดของไฟล์นั้น |
| `COUNT_RETURN_CODE` | จำนวนแถวที่ปลายทางตอบกลับแล้ว |
| **จำนวนที่ค้างจริง** | 🔴 **ต้องเอาสองตัวมาลบกันเอง** — ไม่มีในอีเมล |

> ⚠️ **คนอ่านต้องคำนวณเองทุกครั้ง** และถ้าอ่านเผิน ๆ จะเข้าใจว่า `COUNT_DATA` คือจำนวนที่ค้าง
> **ระบบใหม่ต้องรายงาน "จำนวนที่ค้าง" ตรง ๆ**

### 🔴 B — เฝ้าเฉพาะฝั่ง `I` ไม่เฝ้าฝั่ง `N`

Job 6 ส่งข้อมูล **เป็นคู่เสมอ** — ฝั่งร้านถูกกระทบ (`_I`) และฝั่งร้านเปิดใหม่ (`_N`)

| `data_name` | Job 6 ส่ง | Job 10 เฝ้า |
|---|---|---|
| `COMPENSATE_INIT_I` | ✅ | ✅ |
| **`COMPENSATE_INIT_N`** | ✅ | ❌ **ไม่เฝ้า** |
| `COMPENSATE_APPROVE_I` | ✅ | ✅ |
| **`COMPENSATE_APPROVE_N`** | ✅ | ❌ **ไม่เฝ้า** |

> 🔴 **ถ้าฝั่ง `N` ค้างแต่ฝั่ง `I` ไปถึง จะไม่มีใครรู้เลย**
> เจตนาที่เดาได้คือ *"ทั้งคู่ส่งพร้อมกัน ถ้าฝั่งหนึ่งไปถึงอีกฝั่งก็ควรไปถึง"*
> **แต่ในระบบใหม่ที่ใช้ RabbitMQ แต่ละข้อความมี publisher confirm แยกกัน** — สมมติฐานนี้ใช้ไม่ได้แล้ว

### 🔴 C — ขอบเขตที่เฝ้ายังแคบเกินไปสำหรับระบบใหม่

DDL ใหม่มี `data_name` ที่เป็นขาออก (`direction = 'OUT'`) **4 ค่า**:

| `data_name` | job ที่ส่ง | Job 10 เฝ้าไหม |
|---|---|---|
| `COMPENSATE_INIT_I` · `COMPENSATE_APPROVE_I` | Job 6 | ✅ |
| `COMPENSATE_INIT_N` · `COMPENSATE_APPROVE_N` | Job 6 | ❌ (ข้อ B) |
| **`IAS_SALES_REQUEST`** | **Job 4** | ❌ **ไม่เฝ้า** |
| **`SGI_REFLOW`** | **`POST /sgi/document/{docNo}/actions`** | ❌ **ไม่เฝ้า** |

> 🔴 **Job 4 ส่งคำขอยอดขายไป IAS ผ่าน EAI S3 พร้อม outbox เหมือนกัน**
> ถ้าอัปโหลดค้าง **ไม่มี watchdog ตัวไหนเฝ้าเลย** — เรื่องจะไปตายที่ Job 5 ที่รอไฟล์ตอบกลับไม่มา
> เช่นเดียวกับ `SGI_REFLOW` ที่ BE ส่งเมื่อผู้ใช้กดปุ่มบนหน้าจอ
>
> **ต้องเคาะว่าจะขยายขอบเขตหรือไม่** (ดูหัวข้อ 9)

### 🔴 D — `interface_type != 'WS'` แปลเป็นระบบใหม่อย่างไร

ระบบเดิมใช้ `interface_type` เก็บ **ชื่อไฟล์** ที่ส่ง และใช้ค่า `'WS'` เป็นเครื่องหมายว่า
"รายการนี้ส่งผ่าน web service ไม่ใช่ไฟล์" แล้วกันออกจากการเฝ้า

**ระบบใหม่ไม่มีคอลัมน์ `interface_type`** — เจตนาเดิมถูกแทนด้วย **`direction = 'OUT'`**

| ระบบเดิม | ระบบใหม่ | เหตุผล |
|---|---|---|
| `interface_type != 'WS'` | **`direction = 'OUT'`** | แถว `INTERNAL` ของ Jobs 7/8/9 จบที่ `COMPLETED` ทันที ไม่มีอะไรให้รอ |

> ✅ **`api.md` บันทึกการแปลนี้ไว้แล้ว** — *"นับเฉพาะ `direction = 'OUT'` … ตรงเจตนาเดิมของ Java ที่กรอง `interface_type != 'WS'`"*

---

## 5. ขั้นที่ ② ③ — ข้อความและการส่ง

### รูปแบบข้อความ

```
Warning - no received data
COMPENSATE_INIT_I | FRBC0001_20260607170000 | 152 | 148
COMPENSATE_APPROVE_I | FRBC0001_20260606170000 | 87 | 87
```

คั่นด้วย `|` · ขึ้นบรรทัดด้วย `System.getProperty("line.separator")`

> ⚠️ **บรรทัดที่สองในตัวอย่างคือกลุ่มที่ `COUNT_DATA = COUNT_RETURN_CODE`** — ดูเหมือนไม่มีอะไรค้าง
> แต่ยังโผล่มาเพราะ `EXISTS` เป็นจริงจากแถวอื่นในกลุ่มเดียวกัน (ข้อ A)

### การส่งอีเมล

```java
manageCompensateController.genMessageMailNotifyNoReceiveData(informBean);
...
SendMailUtil.sendMailToAdmin(informBean, config, true);
```

ใช้ **`sendMailToAdmin` ตัวเดียวกับทุก job** — ผู้รับมาจาก `config.getMailTo()`
รายการค้างอยู่ใน field `note` ของอีเมลสถานะปกติ (ดูหัวข้อ 3)

### ⚠️ ข้อความ log ผิด — copy จาก Job 8

```java
LogUtils.info(ExportImpactStoreFlowToBPM.class, "Start => export IMPACT_STORE_INFO to BPM	");
...
LogUtils.info(ExportImpactStoreFlowToBPM.class, "End => export IMPACT_STORE_INFO to BPM");
```

**ทั้งข้อความและ logger class เป็นของ Job 8** — คนที่ค้น log หา `NotifyNoReceiveData` จะหาไม่เจอ

> ⚠️ และ `informBean.setJobName(NotifyNoReceiveData.class.getSimpleName())` ใช้ชื่อคลาส
> ต่างจาก job อื่นที่ใช้ค่าคงที่ `FgiConstant.JOB_NAME_*` — **ชื่อ job ในเมลจึงไม่สอดคล้องกับ job อื่น**

### 🔴 ไม่มี marker กันเตือนซ้ำ — เตือนเรื่องเดิมทุกวันตลอดไป

ระบบเดิม**ไม่มีอะไรจำว่าเคยเตือนเรื่องนี้ไปแล้ว** — ถ้าแถวหนึ่งค้างอยู่ 30 วัน
จะได้อีเมลเตือนเรื่องเดิม **30 ฉบับ**

> 🔴 **นี่คือสาเหตุคลาสสิกของ alert fatigue** — คนดูแลจะเริ่มกรองเมลนี้ทิ้งอัตโนมัติ
> แล้วรายการค้าง**ใหม่** ก็จะถูกกรองทิ้งไปด้วย
>
> ✅ **DDL ใหม่เตรียมทางไว้แล้ว** — `sgi_interface_transactions.last_ack_notified_on DATE`
> คอมเมนต์ใน DDL ระบุว่า *"marker กัน watchdog (Job 10) ส่งอีเมลเตือนซ้ำในวันเดียวกัน"*

---

## 6. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| `FGI_CONFIRM_RECEIVE_DATA` | **`sgi_interface_transactions`** |
| `return_code IS NULL` | **`outbox_status != 'CONFIRMED'`** |
| `interface_type != 'WS'` | **`direction = 'OUT'`** |
| `trunc(create_date) <= trunc(sysdate-1)` | `created_at <= now() - interval '1 day'` |
| ข้อความในโน้ตอีเมล | **อีเมล EM-08 + หน้า `/sgi/interface/pending-ack`** |
| — | **`last_ack_notified_on`** (marker กันเตือนซ้ำ · ของใหม่) |

### คิวรีของระบบใหม่ควรเป็น

```sql
SELECT data_name, business_key, period_key, outbox_status, retry_count,
       created_at, sent_at, doc_no
  FROM sgi_interface_transactions
 WHERE direction = 'OUT'
   AND outbox_status IS DISTINCT FROM 'CONFIRMED'
   AND created_at <= now() - :pending_threshold
   AND (last_ack_notified_on IS NULL OR last_ack_notified_on < CURRENT_DATE)   -- กันเตือนซ้ำวันเดียวกัน
   AND legal_hold = FALSE
 ORDER BY created_at;
```

> 🔴 **ใช้ `IS DISTINCT FROM` ไม่ใช่ `!=`** — `outbox_status` เป็น **nullable**
> แถว `INTERNAL` ของ Jobs 7/8/9 ไม่ตั้งค่านี้เลย · ถ้าใช้ `!=` แถวที่ `outbox_status IS NULL` จะไม่เข้าเงื่อนไข
> (`NULL != 'CONFIRMED'` ได้ `NULL` ไม่ใช่ `TRUE`) — แต่ที่นี่กรอง `direction = 'OUT'` อยู่แล้วจึงไม่กระทบมาก
> **ยังต้องระวังถ้ามีแถว `OUT` ที่ยังไม่ทันตั้ง `outbox_status`**

### สิ่งเดียวที่ job นี้เขียน

```sql
UPDATE sgi_interface_transactions
   SET last_ack_notified_on = CURRENT_DATE
 WHERE id = ANY(:notified_ids);
```

> ⚠️ **ต้องอัปเดต marker หลังส่งอีเมลสำเร็จเท่านั้น** — ถ้าอัปเดตก่อนแล้วส่งเมลล้ม
> จะไม่มีการเตือนเลยทั้งวัน

### ตารางของระบบเดิมที่ **อ่านอย่างเดียว** (ห้ามเขียนเด็ดขาด)

| ตาราง | ใช้ทำอะไร |
|---|---|
| `email_template` | template **EM-08** (watchdog ค้างส่ง) |
| `email_sent` | 🔴 **`@gosoft-sbp/email-lib` เขียน log ให้เอง — SGI ห้าม INSERT เอง** |

---

## 7. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `pendingCount` | 🔴 **จำนวนแถวที่ค้างจริง** | ระบบเดิมไม่มีตัวเลขนี้ (ต้องลบเอง) |
| `pendingByDataName` | แยกตาม `data_name` | เห็นว่าติดที่ interface ไหน |
| `oldestPendingAgeDays` | อายุของแถวที่ค้างนานที่สุด | 🔴 **> 3 วันต้องยกระดับการแจ้ง** |
| `pendingReadyCount` | ค้างที่ `READY` (ยังไม่ยิง) | dispatcher ไม่ทำงาน |
| `pendingPublishedCount` | ค้างที่ `PUBLISHED` (ยิงแล้วไม่ confirm) | broker มีปัญหา |
| `pendingFailedCount` | `FAILED` | ต้องแก้ที่ payload หรือ config |
| `notifiedCount` | แถวที่ตั้ง marker แล้วในรอบนี้ | ต้องเท่ากับ `pendingCount` |
| `suppressedCount` | แถวที่ค้างแต่เตือนไปแล้ววันนี้ | 🔴 **สูงต่อเนื่อง = ปัญหาเรื้อรัง** |
| `mailSent` | ส่งเมลสำเร็จไหม | 🔴 **ล้มแล้วต้อง alert ทางอื่น** |
| `durationMs` | เวลาที่ใช้ | |

**สมการที่ต้องเป็นจริงเสมอ:**

```
pendingReadyCount + pendingPublishedCount + pendingFailedCount = pendingCount
notifiedCount = pendingCount            (เมื่อส่งเมลสำเร็จ)
```

- 🔴 **alert เมื่อ `oldestPendingAgeDays` เพิ่มขึ้นทุกวัน** — แปลว่าไม่มีใครแก้
- 🔴 **alert เมื่อ `mailSent = false`** — **ยามที่ส่งสัญญาณไม่ได้คือยามที่ไม่มีอยู่จริง**

---

## 8. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — การคัดเลือก

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | ไม่มีแถวค้างเลย | job **สำเร็จ** · **ไม่ส่งอีเมล** |
| 1.2 | มีแถว `OUT` ค้าง 2 วัน `outbox_status = 'READY'` | เข้ารายการ · นับ `pendingReadyCount` |
| 1.3 | แถวค้าง `outbox_status = 'PUBLISHED'` | เข้ารายการ — **ยิงแล้วแต่ยังไม่ได้ confirm ก็ถือว่าค้าง** |
| 1.4 | แถว `outbox_status = 'CONFIRMED'` | **ไม่เข้ารายการ** |
| 1.5 | แถวค้าง **ไม่ถึง 1 วัน** | ไม่เข้ารายการ |
| 1.6 | แถวค้าง **1 วันพอดี** | ✅ **ตัดสินแล้ว — `>=` (เข้ารายการ)** · SQL ใช้ `created_at <= now() - (N * INTERVAL '1 day')` · มีเทสตรึงไว้ใน `__svc__/job10-matrix.svc.spec.ts` |
| 1.7 | แถว `direction = 'INTERNAL'` (Jobs 7/8/9) | 🔴 **แก้ 2026-09-14 — ข้อความเดิมตกยุค** · สมมติฐาน "จบที่ `COMPLETED` ทันที" ไม่จริง: ถ้า Job 8 ไม่เคยสร้างเอกสาร แถวของ Job 7/9 จะค้าง `READY` **ตลอดไป** · ระบบใหม่จึง **เฝ้าด้วย** โดยใช้เกณฑ์อายุแยก (`SGI_JOB10_INTERNAL_AGE_DAYS`) · ปิดได้ด้วย `SGI_JOB10_WATCH_INTERNAL_READY=false` |
| 1.8 | แถว `direction = 'IN'` (Job 5 · Job 11) | **ไม่เข้ารายการ** |
| 1.9 | แถว `OUT` ที่ `outbox_status` เป็น **NULL** | 🔴 **ต้องเข้ารายการ** — ใช้ `IS DISTINCT FROM` ไม่ใช่ `!=` |
| 1.10 | แถว `legal_hold = TRUE` | ✅ **ตัดสินแล้ว — ไม่เตือน** (แช่ไว้ตั้งใจ) · เปลี่ยนได้ด้วย `SGI_JOB10_SKIP_LEGAL_HOLD=false` |

### กลุ่มที่ 2 — ขอบเขตที่เฝ้า

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | `COMPENSATE_INIT_I` ค้าง | เข้ารายการ (ระบบเดิมก็เฝ้า) |
| 2.2 | 🔴 **`COMPENSATE_INIT_N` ค้าง** | ระบบเดิม **ไม่เฝ้า** · **ระบบใหม่ต้องเฝ้า** (แต่ละข้อความมี confirm แยกกัน) |
| 2.3 | 🔴 **`IAS_SALES_REQUEST` ค้าง** (Job 4) | ✅ **ตัดสินแล้ว — เฝ้า** · ค่าเริ่มต้น `SGI_JOB10_DATA_NAMES=''` แปลว่าเฝ้าทุก `data_name` ที่เป็นขาออก · ถ้าไม่เฝ้า Job 4 ที่ค้างจะไม่มีใครเห็นแล้วไปตายที่ Job 5 |
| 2.4 | 🔴 **`SGI_REFLOW` ค้าง** (BE ส่งจากหน้าจอ) | ↑ เหมือนกัน |
| 2.5 | ฝั่ง `I` ไปถึงแต่ฝั่ง `N` ค้าง | **ต้องเตือน** — ระบบเดิมเงียบสนิท |

### กลุ่มที่ 3 — การเตือนซ้ำและอีเมล

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | แถวเดิมค้างมา 5 วัน | 🔴 **เตือนวันละครั้งเท่านั้น** ไม่ใช่ทุกครั้งที่รัน |
| 3.2 | รัน job 2 รอบในวันเดียวกัน | รอบที่สอง **ไม่ส่งซ้ำ** · นับ `suppressedCount` |
| 3.3 | วันใหม่ แถวเดิมยังค้าง | เตือนอีกครั้ง |
| 3.4 | มีแถวค้างใหม่ปนกับแถวเก่าที่เตือนแล้ว | เตือนเฉพาะแถวใหม่ · 🔴 **ต้องเคาะว่ารายงานรวมหรือแยก** |
| 3.5 | **ส่งอีเมลล้มเหลว** | 🔴 **ห้ามตั้ง `last_ack_notified_on`** · exit ≠ 0 · alert ทางอื่น |
| 3.6 | ตั้ง marker แล้ว process ตาย | รอบหน้าจะไม่เตือนซ้ำในวันเดียวกัน — **ยอมรับได้ถ้าเมลส่งไปแล้ว** |
| 3.7 | อีเมลใช้ template EM-08 | ✅ อ่านจาก `email_template` ของระบบเดิม |
| 3.8 | log ของ `email_sent` | 🔴 **`email-lib` เขียนเอง — SGI ห้าม INSERT** |

### กลุ่มที่ 4 — การรายงาน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | รายงานจำนวนที่ค้าง | 🔴 **ตัวเลข "จำนวนที่ค้าง" ตรง ๆ** ไม่ใช่ให้คนลบเอง |
| 4.2 | แยกตาม `data_name` และ `outbox_status` | เห็นว่าติดที่ไหน (dispatcher / broker / payload) |
| 4.3 | มีรายการค้าง | 🔴 **เป็น alert ไม่ใช่โน้ตในเมลสถานะ** |
| 4.4 | ไม่มีรายการค้าง | job สำเร็จ · **ไม่รบกวนใคร** |
| 4.5 | query ล้มเหลว | ❌ **job ล้มเหลว · exit ≠ 0** — ระบบเดิมตั้ง FAIL แต่ไม่มี exit code |

---

## 9. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **ขอบเขตที่เฝ้า** | ระบบเดิมเฝ้าแค่ `COMPENSATE_*_I` | ✅ **ปิดแล้ว 2026-09-13 — เลือก (ก) เฝ้าทุก `direction = 'OUT'`** · เหตุผลจากเอกสารฉบับนี้เอง: คงขอบเขตเดิมแล้ว **Job 4 ที่ค้างจะไม่มีใครเฝ้าเลย** · และ RabbitMQ ให้ publisher confirm **แยกรายข้อความ** สมมติฐาน "I ไปถึงแล้ว N ก็ควรไปถึง" จึงใช้ไม่ได้ · จำกัดขอบเขตได้ผ่าน `SGI_JOB10_DATA_NAMES` ถ้าจำเป็น |
| 🔴 **รายงาน "จำนวนที่ค้าง" ตรง ๆ** | คิวรีเดิมนับทุกแถวในกลุ่ม ไม่ใช่แถวที่ค้าง | ✅ **แก้แล้ว 2026-09-13** — คิวรีกรองเงื่อนไข "ค้าง" ที่ตัวแถวเลย · อีเมลบอก **จำนวนที่ค้างจริง** พร้อมแยกตาม `data_name` · `outbox_status` · **ช่วงอายุ** และบอกอายุรายแถวเป็นวัน |
| 🔴 **การเตือนซ้ำ** | ระบบเดิมไม่มี marker → alert fatigue | ✅ **ปิดแล้ว 2026-09-13** — **วันละครั้งต่อแถว** ผ่าน `last_ack_notified_on` · **ยกระดับด้วยการจัดกลุ่มอายุในอีเมล** (1 วัน / 2-3 / 4-7 / 8-30 / เกิน 30) จึงไม่ต้องเก็บ state เพิ่ม · ค้างเกิน `SGI_JOB10_ESCALATE_DAYS` (3 วัน) → **job จบเป็น FAILED** ให้ระบบ monitoring จับ ไม่ใช่พึ่งคนอ่านอีเมล |
| 🔴 **พบรายการค้าง = alert ไม่ใช่ note** | ระบบเดิมใส่รายการค้างใน `note` ของเมลสถานะปกติ แล้วรายงาน SUCCESS เสมอ | ✅ **แยกแล้ว 2026-09-13** — ส่ง **EM-08 เป็นอีเมลของตัวเอง** (คนละฉบับกับ EM-07 ที่ job อื่นใช้แจ้ง fail) · ไม่มีของค้าง = **ไม่ส่งอีเมลเลย** เพื่อไม่ให้คนชินกับเมลรายวัน · และค้างเกินเกณฑ์ยกระดับ → สถานะ job เป็น FAILED |
| **threshold 1 วัน** | เป็น literal ในโค้ด | ✅ **ปิดแล้ว** — `mas_param.SGI_PENDING_ACK_AGE_DAYS` (seed = `1`) มีอยู่แล้ว · นิยามคือ **`created_at <= now() - N วัน`** (`<=` คือรวมแถวที่ครบพอดี) |
| **`legal_hold = TRUE`** | แถวที่ถูก legal hold ยังต้องเฝ้าไหม | ✅ **ปิดแล้ว 2026-09-13 — ไม่เฝ้า** · แถวที่ถูก legal hold ถูกแช่ไว้**โดยตั้งใจ** การเตือนทุกวันจึงเป็น noise ล้วน ๆ · เปิดกลับได้ด้วย `SGI_JOB10_SKIP_LEGAL_HOLD=false` |
| **`outbox_status` เป็น NULL** | ใช้ `IS DISTINCT FROM` ไม่ใช่ `!=` | ✅ **ทำแล้วและพิสูจน์กับ PostgreSQL 16 จริง** — ข้อมูลทดสอบชุดเดียวกัน: `IS DISTINCT FROM` ได้ **3 แถว** · `!=` ได้แค่ **2 แถว** (แถว `IAS_SALES_REQUEST` ที่ `outbox_status IS NULL` หลุดไป) ซึ่งเป็นแถวที่ **น่าเป็นห่วงที่สุด** เพราะ publish ยังไม่เริ่มด้วยซ้ำ |
| **โครง `sgi_interface_transactions`** | ยังไม่เคาะว่าออกแบบใหม่หรือลอกแพตเทิร์น `statement_summary` | 🔴 `DECISIONS` ข้อ **2.4 (DP-6)** |

---

## 10. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | 🔴 **พบของค้างแล้วยังรายงาน `SUCCESS`** | `genMessageMailNotifyNoReceiveData` — ใส่รายการใน `note` แล้ว `setStatus(JOB_STATUS_SUCCESS)` เสมอ | **พบของค้าง = alert** แยกจากสถานะการรัน job |
| **L2** | 🔴 **ตัวเลขที่รายงานไม่ใช่จำนวนที่ค้าง** | ชั้นนอกนับทุกแถวในกลุ่ม · `EXISTS` แค่ยืนยันว่ามีของค้าง | นับแถวที่ค้างจริง แยกตาม `data_name` และ `outbox_status` |
| **L3** | 🔴 **ไม่มี marker กันเตือนซ้ำ** | เตือนเรื่องเดิมทุกวันจนกว่าจะมีคนแก้ | ใช้ `last_ack_notified_on` · ตั้ง **หลังส่งเมลสำเร็จเท่านั้น** |
| **L4** | 🔴 **เฝ้าเฉพาะฝั่ง `I`** | `data_name in ('COMPENSATE_INIT_I','COMPENSATE_APPROVE_I')` | เฝ้าทุกแถว `direction = 'OUT'` (หรือระบุขอบเขตให้ชัดพร้อมเหตุผล) |
| **L5** | **ข้อความ log และ logger class เป็นของ Job 8** | `LogUtils.info(ExportImpactStoreFlowToBPM.class, "Start => export IMPACT_STORE_INFO to BPM")` | log ด้วยชื่อ job ที่ถูกต้อง — ไม่งั้นค้นหาใน log ไม่เจอ |
| **L6** | **ชื่อ job ไม่สอดคล้องกับ job อื่น** | `setJobName(NotifyNoReceiveData.class.getSimpleName())` แทนค่าคงที่ `FgiConstant.JOB_NAME_*` | ใช้ชื่อ job เดียวกับที่ลงทะเบียนใน `main.ts` |
| **L7** | **threshold เป็น literal ใน SQL** | `trunc(sysdate-1)` | อ่านจาก config · นิยาม `>=` หรือ `>` ให้ชัด |
| **L8** | **ไม่มี exit code** | `catch` ตั้ง FAIL แล้วจบตามปกติ | exit non-zero เมื่อ query ล้มหรือส่งเมลล้ม |
| **L9** | **ส่งเมลผ่าน `sendMailToAdmin` ตัวเดียวกับทุก job** | ผู้รับเหมือน job อื่นทั้งหมด | ใช้ template **EM-08** เฉพาะของ watchdog · ผู้รับแยกตาม config |

> ⚠️ **L1 + L3 รวมกันทำลายจุดประสงค์ของ job นี้ทั้งหมด**
> job ที่มีหน้าที่เดียวคือ **"ทำให้ความเงียบดังขึ้น"** กลับ
> (1) รายงานว่าสำเร็จเสมอ ทำให้คำเตือนปนกับเมลประจำวัน และ
> (2) เตือนเรื่องเดิมซ้ำทุกวันจนคนกรองเมลนี้ทิ้ง
>
> **ผลคือรายการค้างใหม่จะถูกมองข้ามไปด้วย** — และเนื่องจากสิ่งที่ค้างคือข้อความที่ทำให้ **เงินออก**
> ความเงียบตรงนี้แปลว่า **ร้านไม่ได้รับเงินโดยไม่มีใครรู้**

---

## 11. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 6 (ต้นทางของข้อความที่เฝ้าอยู่) | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` |
| Job 4 (outbox ที่ยังไม่มีใครเฝ้า) | `batchjob/JOB-04-PrepareImpactStoreToIAS-อธิบายละเอียด.md` |
| Job 11 (รับสถานะจ่ายกลับจาก STA) | `LLDD/md/Jobs/LLDD-BE-Job-11-ConsumeStaCompensate.md` |
| สเปกรูปแบบมาตรฐานของ Job 10 | `LLDD/md/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.md` |
| endpoint หน้ารายการค้าง | `api.md` → `GET /sgi/interface/pending-ack` |
| มติเรื่องเกณฑ์ publisher confirm | `DECISIONS-รอตัดสินใจ.md` ข้อ 2.13 (ปิดแล้ว 2026-09-08) |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
