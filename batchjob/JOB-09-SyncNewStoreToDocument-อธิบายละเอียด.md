# Job 9 — SyncNewStoreToDocument : ยกร้านเปิดใหม่และ %ชดเชยขึ้นเอกสาร

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 10 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.19 · 2.30 · 2.31 · 2.33 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-09-SyncNewStoreToDocument-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/ExportOpenStore.java` · `controller/ExportController.java` (`exportOpenNewStore` · `manageOpenNewStoreToBPM` · `appendContentOpenNewStore` · `checkProcesssError`) · `dao/jdbc/ExportJdbc.java` (`queryOpenNewStore` · `getErrorProcess`) · `Constant/FgiConstant.java` · `config.xml` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-sync-new-store-to-document` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-9-SyncNewStoreToDocument` · **Job 7 (คู่แฝดที่ยกคู่แข่งขึ้นเอกสาร)** ดู `batchjob/JOB-07-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

ยก **รายชื่อร้าน 7-Eleven ที่เปิดใหม่** พร้อม **%ชดเชยและจำนวนเงินของแต่ละร้าน** ขึ้นไปติดกับเอกสารชดเชย

```
Job 6 สร้างค่าชดเชยรายร้านใหม่           Job 9 ยกขึ้นเอกสาร              คนพิจารณาเห็นบนหน้าจอ
fgi_new_store_compensate      ──▶  sgi_document_new_stores  ──▶  ตาราง "ร้านที่เปิดใหม่"
```

**นี่คือคู่แฝดของ Job 7** — โครงเหมือนกันเกือบทั้งหมด ต่างกันที่ **ข้อมูลที่ยก** และ **กติกาการตรวจ**

| | Job 7 | **Job 9 (ฉบับนี้)** |
|---|---|---|
| ยกอะไรขึ้นเอกสาร | ร้านคู่แข่ง | **ร้าน 7-Eleven ที่เปิดใหม่** |
| ปลายทาง | `sgi_document_competitors` | `sgi_document_new_stores` |
| ไฟล์เดิม | `BPM06003O` (14 ฟิลด์) | **`BPM06002O` (24 ฟิลด์)** |
| ปลายทาง SFTP เดิม | `BPM/FGI/Inbound/competition/` | `BPM/FGI/Inbound/impactprofile/` |
| มีตัวเลขที่กระทบเงินไหม | ❌ ข้อมูลประกอบเท่านั้น | ✅ **มี — %ชดเชยและจำนวนเงิน** |
| ต้อง validate อะไรพิเศษ | — | 🔴 **%ชดเชยรวมต่อเอกสารต้องได้ 100** |

> 🔴 **ความต่างที่สำคัญที่สุด** — Job 7 ยกข้อมูลประกอบ ผิดแล้วแค่ดูไม่ครบ
> **Job 9 ยกตัวเลขที่กลายเป็นเงินจริง** ผิดแล้วจ่ายผิด

---

## 2. ทำไมต้องมี job นี้

ร้าน SP หนึ่งร้านอาจถูกกระทบจาก **ร้าน 7-Eleven ใหม่หลายร้านพร้อมกัน**
เงินชดเชยก้อนเดียวจึงต้อง **แบ่งสัดส่วนว่าร้านใหม่ร้านไหนรับผิดชอบกี่เปอร์เซ็นต์**

Job 9 คือตัวที่ยกสัดส่วนนั้นขึ้นเอกสารให้คนพิจารณาเห็นและปรับแก้ได้

**สายข้อมูลเต็ม:** `Job 2` (คู่ร้าน) → `Job 6` (สร้างค่าชดเชยรายร้านใหม่) → `Job 8` (สร้างเอกสาร) → **`Job 9` (ยกร้านใหม่ + %ชดเชยขึ้นเอกสาร)** → หน้าจอ `k2-document.html`

> ⚠️ **ลำดับเลข job ไม่ใช่ลำดับการทำงาน** — เหมือน Job 7 · Job 9 ต้องรันหลัง Job 8 ถึงจะมี `doc_no` ให้ผูก

---

## 3. ภาพรวมการทำงาน

```
① query ร้านเปิดใหม่ที่ควรส่ง — เงื่อนไข 4 ชั้น
      ▼
② คัดออกอีกชั้น: รอบที่ข้อมูลผู้อนุมัติไม่ครบ (getErrorProcess)
      │  ไม่เหลือแถว ──▶ จบ (ถือว่าสำเร็จ)
      ▼
③ transaction เดียว:
     เขียนไฟล์ BPM06002O ทีละบรรทัด (24 ฟิลด์)  +  สะสม ConfirmReceiveData
     insert FGI_CONFIRM_RECEIVE_DATA
     SFTP ไป BPM
      ▼
④ ส่งเมลแจ้งผล (เพิ่มผู้รับฝั่ง BPM)
```

**โครงเหมือน Job 7 ทุกประการ** — รวมถึงกับดักเดียวกันเกือบทั้งหมด (ดูหัวข้อ 11)

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — ระบบเดิม **ไม่เคยตรวจว่า %ชดเชยรวมได้ 100**

ค้นทั้ง `ExportController` และ `ExportJdbc` แล้ว **ไม่มีการตรวจผลรวม `compensate_forecast_percent_n` เลย**
แต่ละแถวถูกเขียนลงไฟล์ตามที่ query มาได้ **โดยไม่มีใครดูภาพรวมต่อเอกสาร**

| | ระบบเดิม | ระบบใหม่ (ผังระบุไว้แล้ว) |
|---|---|---|
| ตรวจว่า % อยู่ในช่วง 0–100 | ❌ ไม่มี | ✅ `CHECK (compensate_percent BETWEEN 0 AND 100)` ใน DDL |
| ตรวจว่า % ไม่เป็น NULL | ❌ ไม่มี | ✅ `NOT NULL` + `COMPENSATE_PERCENT_INVALID` ก่อน upsert |
| **ตรวจว่ารวมกันได้ 100** | ❌ **ไม่มี** | ✅ **`validate allocation percent รวมต่อ doc_no`** |

> 🔴 **นี่คือกติกาธุรกิจที่มีอยู่แล้ว** (`%ชดเชยจัดสรรข้ามร้านใหม่ต้องรวมได้ 100% พอดี`)
> แต่ **ระบบเดิมบังคับที่หน้าจอ K2 เท่านั้น ไม่ได้บังคับที่ pipeline**
> ระบบใหม่ต้องบังคับตั้งแต่ตอน sync — ดูหัวข้อ 7

---

## 4. ขั้นที่ ① — เงื่อนไข 4 ชั้น

```sql
  from fgi_new_store_info si
  inner join fgi_impact_store_on_process op on op.impact_process_id = si.impact_process_id
  inner join fgi_new_store_compensate fnsc
          on fnsc.impact_process_id = si.impact_process_id
         and fnsc.storecode_n       = si.storecode_n
         and fnsc.compensate_month  = si.compensate_month
         and fnsc.compensate_year   = si.compensate_year
  inner join fgi_impact_store_compensate fisc
          on fisc.impact_process_id = si.impact_process_id
         and fisc.compensate_month  = si.compensate_month
         and fisc.compensate_year   = si.compensate_year
         and fisc.compensate_status = 'I'                     -- ชั้น 2
         and fisc.compensate_forecast is not null             -- ชั้น 3
  inner join fgi_impact_store fis on fis.impact_store_id = si.impact_store_id
 where op.flag_action in ('Y','W')                            -- ชั้น 1
   and not exists ( ... rd.data_name = 'NEW_STORE' ... )      -- ชั้น 4
```

| ชั้น | เงื่อนไข | ทำไม |
|---|---|---|
| **1** | รอบชดเชย `flag_action IN ('Y','W')` | เฉพาะรอบที่ยัง active |
| **2** | ค่าชดเชย **ฝั่งร้านถูกกระทบ** `compensate_status = 'I'` | ยังไม่ถูกอนุมัติ |
| **3** | `compensate_forecast is not null` (ฝั่ง I) | คำนวณค่าชดเชยแล้ว |
| **4** | ยังไม่เคยส่งงวดนี้ | กันส่งซ้ำ |

> 📌 **เงื่อนไขชั้น 2/3 ดูที่ฝั่งร้านถูกกระทบ (`fisc`) ไม่ใช่ฝั่งร้านใหม่ (`fnsc`)**
> แปลว่า **ถ้าฝั่ง I พร้อม ฝั่ง N ก็ถูกส่งไปด้วยทั้งหมด** โดยไม่ตรวจว่าฝั่ง N มีค่าครบไหม
> → **นี่คือช่องที่ทำให้ % ที่ไม่ครบหลุดเข้าไฟล์ได้** (ดูหัวข้อ 3)

> ⚠️ **ไม่มีเงื่อนไข `datasource = 'ALM'` แบบ Job 7** — Job 9 ส่งทุกช่องทาง
> **ต่างจาก Job 4 · Job 7 · Job 8 ที่กันช่องทาง `STA` ออก** (ดูหัวข้อ 10)

### 🔴 `adjust` ชนะ `forecast` แล้วสลับชื่อ — เหมือน Job 8

```sql
nvl(fnsc.compensate_adjust_n,         fnsc.compensate_forecast_n)         as compensate_forecast_n,
nvl(fnsc.compensate_adjust_percent_n, fnsc.compensate_forecast_percent_n) as compensate_forecast_percent_n,
null as compensate_adjust_n,
null as compensate_adjust_percent_n
```

**ค่าที่คนปรับแก้ถูกส่งออกในชื่อ `forecast`** และคอลัมน์ `adjust` ที่ส่งออก **บังคับเป็น `null` เสมอ**

→ ไฟล์ `BPM06002O` **ฟิลด์ที่ 19 และ 20 (`COMPENSATE_ADJUST_N` · `COMPENSATE_ADJUST_PERCENT_N`) เป็นค่าว่างตลอดกาล**

> 🔴 **ปัญหาเดียวกับ Job 8** (`DECISIONS` ข้อ **2.31** ข้อย่อย 4) — ปลายทางแยกไม่ออกว่าตัวเลขมาจากระบบหรือคนปรับ
> **แต่ที่นี่หนักกว่า** เพราะเป็น **%ชดเชย** ที่กลายเป็นเงินโดยตรง

---

## 5. ขั้นที่ ② — gate ข้อมูลผู้อนุมัติ

ใช้ `getErrorProcess()` **ตัวเดียวกับ Job 7 และ Job 8** — คัดรอบที่ `dv_*` / `gm_*` / `avp_*`
มีคอลัมน์ใดเป็น NULL ออกทั้งรอบ ด้วยเทคนิค `'NuLL' in (nvl(col,'NuLL'), ...)`

> ⚠️ **Job 9 ไม่มีการรายงานรายร้านที่ถูกคัดออก** ต่างจาก Job 8 ที่สร้าง `errorProcessListMap`
> พร้อมโซนและประเภทร้านใส่ในโน้ตอีเมล · **Job 9 คัดออกเงียบ ๆ**

---

## 6. ขั้นที่ ③ — ไฟล์ 24 ฟิลด์

### รูปแบบไฟล์ `BPM06002O_yyyyMMddHHmm.txt`

| # | ฟิลด์ | รูปแบบ / หมายเหตุ |
|---|---|---|
| 1 | `NEW_STORE_INFO_ID` | 🔴 PK ของแถวต้นทาง — ระบบใหม่ไม่มีที่เก็บ |
| 2 | `STORECODE_I` | รหัสร้าน SP ที่ถูกกระทบ |
| 3 | `RADIUS` | รัศมีกระทบ |
| 4 | `RADIUS_UNIT` | **หน่วยของรัศมี** |
| 5 | `DISTANCE` | ระยะห่างจริง |
| — | ~~`DISTANCE_UNIT`~~ | 🔴 **คิวรี select มา แต่ไม่ได้เขียนลงไฟล์** (ดูด้านล่าง) |
| 6 | `STORECODE_N` | รหัสร้านเปิดใหม่ |
| 7 | `NAME_N` | ชื่อร้านเปิดใหม่ |
| 8 | `OPENDATE_N` | **`dd/MM/yyyy` ค.ศ.** (ว่างได้) |
| 9 | `CLOSEDATE_N` | **`dd/MM/yyyy` ค.ศ.** (ว่างได้) |
| 10 | `ZONE_N` | โซน |
| 11 | `BRANCHTYPE_N` | ประเภทร้าน |
| 12 | `JURISTIC_ID_N` · 13 `JURISTIC_NAME_N` | นิติบุคคล |
| 14 | ชื่อ-นามสกุลแฟรนไชซี | 🔴 **`FNAME + " " + LNAME` รวมเป็นฟิลด์เดียว** |
| 15 | `YEAR` · 16 `MONTH` | **เติมศูนย์หน้าเป็น 2 หลัก** |
| 17 | `COMPENSATE_FORECAST_N` | **จำนวนเงินชดเชยของร้านใหม่นี้** |
| 18 | `COMPENSATE_FORECAST_PERCENT_N` | **%ชดเชย** |
| 19 | `COMPENSATE_ADJUST_N` | 🔴 **ว่างเสมอ** |
| 20 | `COMPENSATE_ADJUST_PERCENT_N` | 🔴 **ว่างเสมอ** |
| 21–22 | `CREATE_BY` · `CREATE_DATE` | `dd/MM/yyyy HH:mm:ss` |
| 23–24 | `UPDATE_BY` · `UPDATE_DATE` | ↑ |

- คั่นด้วย **`|`** · **encoding `UTF-8`** (`FILE_ENCODING_BPM`) · วันที่ **ค.ศ.** ทั้งหมด (`Locale.US` ทั้งสองฝั่ง)

### 🔴 `DISTANCE_UNIT` ถูก select มาแล้วทิ้ง

```sql
sql.append("     fis.radius, fis.radius_unit, fis.distance, fis.distance_unit,   ");
```

แต่ใน `appendContentOpenNewStore` มีแค่:

```java
content.append(... newStore.get("RADIUS")      + delimiter);
content.append(... newStore.get("RADIUS_UNIT") + delimiter);
content.append(... newStore.get("DISTANCE")    + delimiter);   // ← ไม่มี DISTANCE_UNIT ต่อท้าย
content.append(... newStore.get("STORECODE_N") + delimiter);
```

**รัศมีมีหน่วยกำกับ แต่ระยะทางไม่มี** — ปลายทางต้องเดาเอาว่า `DISTANCE` เป็นหน่วยอะไร

> 🔴 **ผูกกับกติกาแปลงหน่วยของ Job 2 โดยตรง** — เอกสาร Job 2 ระบุว่า ALLMAP ส่ง `DISTANCE_UNIT` มาแยกคอลัมน์
> และตารางใหม่ `distance_km` **มีหน่วยเดียว** จึงต้องแปลงตั้งแต่ Job 2
> **ถ้าแปลงถูกตั้งแต่ต้นทาง ปัญหานี้หายไปเอง** แต่ถ้ายังไม่แปลง ตัวเลขในเอกสารจะผิดหน่วย

### 🔴 ชื่อแฟรนไชซีถูกรวมเป็นฟิลด์เดียว

```java
content.append(TextUtils.nullReturnEmpty(newStore.get("FRANCHISEE_FNAME_N")));
content.append(" ");
content.append(TextUtils.nullReturnEmpty(newStore.get("FRANCHISEE_LNAME_N")) + delimiter);
```

ต้นทางเก็บแยกชื่อ/นามสกุล แต่ไฟล์รวมด้วยช่องว่าง → **ปลายทางแยกกลับไม่ได้** ถ้าชื่อหรือนามสกุลมีช่องว่างในตัว

> ⚠️ **ถ้าฝั่งใดฝั่งหนึ่งว่าง จะได้ช่องว่างนำหน้าหรือต่อท้าย** ที่ปลายทางต้อง trim เอง

### ⚠️ ผลของ SFTP ถูกทิ้ง — เหมือน Job 7

```java
FtpUtils.uploadSFTPFile(ftpEaiServerIpBpm, ..., ftpFileNameArray);//////////
```

**ไม่มี `if` ครอบ** — อัปโหลดล้มแต่ `FGI_CONFIRM_RECEIVE_DATA` commit ว่า "ส่งแล้ว" → ชั้นกันซ้ำปิดประตูไม่ให้ส่งอีก
→ **ร้านเปิดใหม่และ %ชดเชยหายถาวรจากเอกสาร**

---

## 7. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| ไฟล์ `BPM06002O` + SFTP ไป `BPM/FGI/Inbound/impactprofile/` | **upsert ลง `sgi_document_new_stores`** |
| `FGI_CONFIRM_RECEIVE_DATA` | `sgi_interface_transactions` (`direction = 'INTERNAL'`) |
| `FGI_NEW_STORE_INFO` + `FGI_NEW_STORE_COMPENSATE` | `sgi_fgi_impact_compensations` + `sgi_fgi_impact_stores` |
| ผูกด้วย `STORECODE_I` + งวด | ผูกด้วย **`doc_no`** ที่หาจาก `impact_process_id` |

### ตารางปลายทาง

```sql
CREATE TABLE sgi_document_new_stores (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    new_store_code VARCHAR(5) NOT NULL,
    distance_km NUMERIC(8,3),
    compensate_percent NUMERIC(7,4) NOT NULL CHECK (compensate_percent BETWEEN 0 AND 100),
    compensation_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    source_system VARCHAR(30) NOT NULL, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_new_store UNIQUE (doc_no, new_store_code)
);
```

### การแปลงคอลัมน์

| ระบบเดิม | ระบบใหม่ | หมายเหตุ |
|---|---|---|
| `NEW_STORE_INFO_ID` (ฟิลด์ 1) | 🔴 **ไม่มีที่เก็บ** | เหมือน Job 7 · ตามรอยกลับไม่ได้ |
| `STORECODE_I` (2) | ผ่าน `doc_no` → เอกสาร | |
| `RADIUS` · `RADIUS_UNIT` (3–4) | 🔴 **ไม่มีที่เก็บ** | รัศมีกระทบ (1/2 กม.) เป็นค่าคงที่ทางธุรกิจอยู่แล้ว |
| `DISTANCE` (5) | **`distance_km`** | 🔴 ต้องแปลงหน่วยตั้งแต่ Job 2 |
| `STORECODE_N` (6) | `new_store_code` | |
| `NAME_N` · `ZONE_N` · `BRANCHTYPE_N` (7 · 10 · 11) | 🔴 **ไม่มีที่เก็บ** | อ่านจาก `mas_store` ของระบบเดิมแทน |
| `OPENDATE_N` · `CLOSEDATE_N` (8–9) | 🔴 **ไม่มีที่เก็บ** | ↑ |
| `JURISTIC_*_N` (12–13) | 🔴 **ไม่มีที่เก็บ** | อ่านจาก `fr_store` → `juristic` แทน |
| ชื่อแฟรนไชซี (14) | 🔴 **ไม่มีที่เก็บ** | ↑ |
| `YEAR` · `MONTH` (15–16) | ไม่เก็บ — งวดอยู่ที่เอกสาร | |
| `COMPENSATE_FORECAST_N` (17) | **`compensation_amount`** | `COALESCE(adjust_amount, forecast_amount)` |
| `COMPENSATE_FORECAST_PERCENT_N` (18) | **`compensate_percent`** | `COALESCE(adjust_compensate_percent, forecast_compensate_percent)` |
| `COMPENSATE_ADJUST_*` (19–20) | 🔴 **ไม่มีที่เก็บ** | ค่าว่างเสมออยู่แล้ว |
| `CREATE_BY` … `UPDATE_DATE` (21–24) | `source_system` · `updated_at` | |

> 🔴 **ตารางใหม่แคบกว่ามาก** — เก็บแค่ 4 ค่าที่จำเป็น (`new_store_code` · `distance_km` · `compensate_percent` · `compensation_amount`)
> ที่เหลืออ่านจาก master ของระบบเดิม · **เป็นไปตามหลักการ "ห้ามเก็บ master ซ้ำ"**
> แต่แปลว่า **ตรวจย้อนหลังไม่ได้** ว่าตอนนั้นร้านชื่ออะไร ประเภทอะไร (ปัญหาชนิดเดียวกับ `branchtype` ข้อ **2.15**)

### 🔴 A — `compensate_percent` เป็น `NOT NULL` + `CHECK` แต่ต้นทางไม่มีข้อบังคับ

```sql
compensate_percent NUMERIC(7,4) NOT NULL CHECK (compensate_percent BETWEEN 0 AND 100)
```

| | ระบบเดิม | ระบบใหม่ |
|---|---|---|
| % เป็น NULL | ✅ เขียนลงไฟล์เป็นค่าว่าง | ❌ **insert ไม่ผ่าน** |
| % = 150 | ✅ เขียนลงไฟล์ | ❌ **insert ไม่ผ่าน** |
| % รวมได้ 87 | ✅ ไม่มีใครตรวจ | 🔴 **ต้องตรวจ** (ผังระบุ) |

ผังระบุทางออกไว้แล้ว: **decision node `compensate_percent ครบและอยู่ในช่วง 0..100 ทุกแถว?`**
ถ้าไม่ผ่าน → `COMPENSATE_PERCENT_INVALID` + **rollback ก่อน upsert/prune** (`noKind: 'err'` = ล้มทั้ง job)

> ✅ **เป็นการเลือกที่ถูกต้อง** — ต่างจาก `brand_code` ของ Job 7 ที่ map ไม่ได้ก็ยังเก็บแถวไว้
> เพราะ **%ชดเชยผิด = จ่ายเงินผิด** จึงต้องหยุดทั้งรอบ ไม่ใช่ปล่อยผ่านบางแถว

### 🔴 B — "รวมได้ 100" ตรวจที่ไหน และเมื่อไร

ผังมีขั้น **`validate allocation percent รวมต่อ doc_no`** อยู่หลัง upsert

**แต่ยังไม่ระบุว่า:**

| คำถาม | ทางเลือก |
|---|---|
| ตรวจก่อนหรือหลัง upsert | ก่อน (ปลอดภัยกว่า) · หลัง (ต้อง rollback) |
| ไม่ครบ 100 แล้วทำอย่างไร | ล้มทั้ง job · ล้มเฉพาะ `doc_no` นั้น · เตือนแล้วปล่อยผ่าน |
| ยอมให้คลาดเคลื่อนไหม | `= 100` เป๊ะ · `BETWEEN 99.99 AND 100.01` (ปัดเศษ `NUMERIC(7,4)`) |
| ร้านใหม่ร้านเดียว | ต้องเป็น 100 พอดี |
| แถวที่ผู้ใช้เพิ่มเองทีหลัง | นับรวมด้วยไหม |

> 🔴 **ต้องเคาะก่อนเขียนโค้ด** — `NUMERIC(7,4)` มีทศนิยม 4 ตำแหน่ง การแบ่ง 3 ร้านเท่ากันจะได้
> `33.3333 × 3 = 99.9999` **ไม่เท่ากับ 100** · ถ้าบังคับ `= 100` เป๊ะจะ **ล้มทุกครั้งที่แบ่งไม่ลงตัว**

### 🔴 C — การ prune และ `source_system` — เหมือน Job 7

สเปกให้ upsert แล้ว prune เฉพาะแถวที่มาจาก pipeline โดยไม่ลบแถวที่ผู้ใช้เพิ่มเอง
**ปัญหาเดียวกับ Job 7 ทุกข้อ** — `source_system` ใช้ค่าอะไร · สถานะ "รอ sync" เก็บที่ไหน (`DECISIONS` ข้อ **2.30**)

> 🔴 **แต่ที่นี่อันตรายกว่า** — ถ้า prune ลบแถวร้านใหม่ออกไปหนึ่งร้าน **%รวมจะไม่ครบ 100 ทันที**
> การ prune กับ validate 100% จึงต้องอยู่ใน transaction เดียวกันและตรวจ**หลัง** prune

### `sgi_interface_transactions` — ค่าที่ Job 9 ต้องใส่

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | **`'NEW_STORE'`** |
| `direction` | `'INTERNAL'` |
| `status` | `'COMPLETED'` ทันที |
| `doc_no` · `impact_process_id` | typed FK |

---

## 8. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `candidateCount` | แถวที่ผ่านเงื่อนไข 4 ชั้น | |
| `filteredByApproverCount` | แถวที่ถูกคัดออกเพราะข้อมูลผู้อนุมัติไม่ครบ | 🔴 **> 0 ต้อง alert พร้อมรายชื่อร้าน** (ระบบเดิมเงียบ) |
| `pendingNoDocumentCount` | แถวที่ยังไม่มีเอกสาร | 🔴 **> 0 ข้ามวันต้อง alert** |
| `percentInvalidCount` | แถวที่ % เป็น NULL หรือนอกช่วง 0–100 | 🔴 **> 0 = ล้มทั้ง job** |
| **`allocationNot100Count`** | เอกสารที่ %รวมไม่ได้ 100 | 🔴 **> 0 ต้อง alert** — เงินจะจ่ายไม่ครบหรือเกิน |
| `insertedCount` · `updatedCount` | แถวที่ upsert | |
| `prunedCount` | แถวที่ถูกลบเพราะต้นทางไม่มีแล้ว | 🔴 **ต้อง re-validate 100% หลัง prune** |
| `userRowsPreserved` | แถวที่ผู้ใช้เพิ่มเอง | **ต้องไม่ลดลง** |
| `totalAmountSynced` | ผลรวม `compensation_amount` | 🔴 **ต้องเท่ากับยอดชดเชยบนหัวเอกสาร** |
| `durationMs` | เวลาที่ใช้ | |

**สมการที่ต้องเป็นจริงเสมอ:**

```
candidateCount − filteredByApproverCount − pendingNoDocumentCount  =  insertedCount + updatedCount
ต่อ doc_no:  SUM(compensate_percent) = 100
ต่อ doc_no:  SUM(compensation_amount) = sgi_compensation_documents.total_compensation_amount
```

- 🔴 **สมการที่สามคือด่านสุดท้ายก่อนเงินออก** — ยอดรายร้านรวมต้องเท่ากับยอดบนหัวเอกสาร
  ระบบเดิม **ไม่เคยตรวจ** จุดนี้เลย

---

## 9. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — การคัดเลือก

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | รอบ active · `compensate_status = 'I'` · มี forecast ฝั่ง I | **ยกร้านใหม่ทุกร้านของรอบนั้นขึ้นเอกสาร** |
| 1.2 | `flag_action = 'N'` | ไม่ยก |
| 1.3 | `compensate_status = 'A'` | ไม่ยก |
| 1.4 | forecast **ฝั่ง I** เป็น NULL | ไม่ยก |
| 1.5 | 🔴 forecast **ฝั่ง N** เป็น NULL แต่ฝั่ง I ครบ | ระบบเดิม **ยกไปทั้งที่ % ว่าง** · **ระบบใหม่ต้อง reject** |
| 1.6 | เคยยกงวดนี้ไปแล้ว | ไม่ยกซ้ำ |
| 1.7 | รอบจาก `datasource = 'STA'` | 🔴 Job 9 **ไม่กันออก** (ต่างจาก Job 7/8) — ต้องยืนยันว่าตั้งใจ |
| 1.8 | ไม่มีแถวผ่านเลย | job **สำเร็จ** |

### กลุ่มที่ 2 — %ชดเชยและจำนวนเงิน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | ร้านใหม่ร้านเดียว % = 100 | ผ่าน |
| 2.2 | 2 ร้าน 60 + 40 | ผ่าน |
| 2.3 | 🔴 **3 ร้านเท่ากัน 33.3333 × 3 = 99.9999** | 🔴 **ต้องเคาะว่ายอมรับหรือไม่** (ดูหัวข้อ 10 · B) |
| 2.4 | 2 ร้าน 60 + 30 = 90 | ❌ **ไม่ผ่าน** · `allocationNot100Count` + alert |
| 2.5 | 2 ร้าน 60 + 50 = 110 | ❌ ไม่ผ่าน |
| 2.6 | % เป็น NULL | ❌ **`COMPENSATE_PERCENT_INVALID` + rollback** |
| 2.7 | % = 150 (นอกช่วง) | ❌ ไม่ผ่าน `CHECK` |
| 2.8 | % = 0 | ✅ ผ่าน `CHECK` (`BETWEEN 0 AND 100`) — แต่รวมต้องได้ 100 |
| 2.9 | มีทั้ง `adjust` และ `forecast` | ใช้ **`adjust`** ทั้งจำนวนเงินและ % |
| 2.10 | `adjust` เป็น NULL | ใช้ `forecast` |
| 2.11 | ผลรวม `compensation_amount` ≠ ยอดบนหัวเอกสาร | ✅ **ทำแล้ว 2026-09-14** — `checkAmountAgainstHeader()` เทียบทุกเอกสารที่แตะในรอบนั้น · เกินเกณฑ์ `SGI_JOB9_AMOUNT_TOLERANCE` (0.05 บาท) → `amountMismatchDocuments` + `log.error` ⚠️ **ไม่แก้ตัวเลขให้และไม่ทำให้ job ล้ม** — เลือกว่าจะเชื่อฝั่งไหนเป็นการตัดสินใจเชิงธุรกิจ |

### กลุ่มที่ 3 — การเขียนลงเอกสาร

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | เอกสารยังไม่มีร้านใหม่เลย | insert ครบทุกร้าน · `source_system` = ค่าที่ตกลง |
| 3.2 | เอกสารมีร้านนั้นแล้ว | **update ไม่ใช่ insert ซ้ำ** (`UNIQUE (doc_no, new_store_code)`) |
| 3.3 | ต้นทางไม่มีร้านนั้นแล้ว | prune ออก · 🔴 **แล้ว re-validate %รวม 100 ทันที** |
| 3.4 | เอกสารมีแถวที่ผู้ใช้เพิ่มเอง | 🔴 **ห้ามถูก prune** · แต่ **ต้องนับรวมใน %** — 🔴 **ขยายความ 2026-09-14**: ตรวจ %รวม **สองชั้น** · ① ก่อนเขียนตรวจ**ต้นทาง** ② หลัง prune ตรวจ**สภาพจริงบนเอกสาร** (นับแถว USER ด้วย) · ดังนั้นถ้าต้นทางรวม 100 อยู่แล้ว การ**เพิ่ม**แถว USER จะทำให้เกิน 100 แล้วตกที่ชั้น ② ซึ่งถูกต้อง — วิธีที่ถูกคือ**แก้แถวที่มีอยู่** ไม่ใช่เพิ่มแถวใหม่ |
| 3.5 | ยังไม่มีเอกสาร | นับ `pendingNoDocumentCount` · **ห้ามล้มทั้ง job** |
| 3.6 | รันซ้ำทันที | ไม่มีอะไรเปลี่ยน |

### กลุ่มที่ 4 — ความคงทน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | % ไม่ผ่าน validate | ❌ **rollback ก่อน upsert/prune** · เอกสารยังเป็นแบบเดิมทั้งหมด |
| 4.2 | ล้มกลาง upsert | rollback ทั้ง `doc_no` นั้น · **ห้ามเหลือร้านใหม่ครึ่ง ๆ กลาง ๆ** (%รวมจะเพี้ยน) |
| 4.3 | ล้มระหว่าง prune | rollback · แถวเดิมยังอยู่ครบ |
| 4.4 | รัน 2 instance พร้อมกัน | **ห้าม prune ทับกัน** — advisory lock ต่อ `doc_no` |
| 4.5 | Job 9 รันก่อน Job 8 | ทุกแถวเข้า `pendingNoDocumentCount` · job สำเร็จ |
| 4.6 | ส่งเมลไม่สำเร็จ แต่งานสำเร็จ | exit **0** + log ระดับ ERROR |
| 4.7 | งานไม่สำเร็จ แต่ส่งเมลสำเร็จ | exit **ไม่ใช่ 0** |

---

## 10. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **กติกา "%รวมต้องได้ 100"** | ตรวจเมื่อไร · ยอมคลาดเคลื่อนเท่าไร · แถวผู้ใช้นับไหม · prune แล้ว re-validate ไหม | ✅ **ตอบครบแล้ว 2026-09-13** — ดูด้านล่าง · 🔴 **ยังต้อง business sign-off** เรื่องค่าคลาดเคลื่อน |

### กติกา "%ชดเชยรวมต้องได้ 100" ที่ลงมือทำจริง (2026-09-13)

| คำถาม | คำตอบ | เหตุผล |
|---|---|---|
| ตรวจก่อนหรือหลัง upsert | **ก่อน** | ไม่ต้องแตะข้อมูลเลยถ้าผิด · ไม่ต้อง rollback |
| ไม่ครบแล้วทำอย่างไร | **ข้ามเฉพาะ `doc_no` นั้น** แล้ว job จบเป็น `FAILED` | ใบเดียวตั้งค่าผิดไม่ควรกันเงินของอีกหลายร้อยร้าน · แต่ต้องไม่ผ่านเงียบ ๆ |
| แถวเดียวผิด | **ทั้งเอกสารผิด** | upsert แค่แถวที่ถูกจะทำให้ %รวมเพี้ยนยิ่งกว่าเดิม |
| แถวที่ผู้ใช้เพิ่มเอง | **นับรวม** ในการตรวจหลัง prune | เป็นสภาพจริงบนเอกสารที่จะจ่ายเงินตาม |
| prune แล้ว re-validate | **ต้อง** และอยู่ใน transaction เดียวกัน | ลบร้านออกหนึ่งร้าน %รวมไม่ครบทันที → rollback ทั้งรอบ |

#### 🔴 ค่าคลาดเคลื่อนต้อง **ขยายตามจำนวนร้าน** ไม่ใช่ค่าคงที่

เอกสารฉบับนี้เคยระบุว่าคอลัมน์เป็น `NUMERIC(7,4)` — **รันกับ PostgreSQL จริงแล้วพบว่าไม่ใช่**
คอลัมน์ต้นทาง `sgi_fgi_new_store_compensations.forecast_percent` เป็น **`NUMERIC(5,2)`**
(ตาม ORA `NUMBER(5,2)` เดิม) ส่วน `sgi_document_new_stores.compensate_percent` เป็น `NUMERIC(7,4)`

| แบ่ง | ค่าต่อร้าน | ผลรวม | ต่างจาก 100 | tolerance คงที่ 0.01 |
|---|---|---|---|---|
| 2 ร้าน | 50.00 | 100.00 | 0.00 | ✅ |
| 3 ร้าน | 33.33 | 99.99 | 0.01 | ❌ **ตก** |
| 6 ร้าน | 16.67 | 100.02 | **0.02** | ❌ ตก |
| 7 ร้าน | 14.29 | 100.03 | **0.03** | ❌ ตก |

→ สูตรที่ใช้: **`0.01 + จำนวนร้าน × 0.005`** (0.005 = ครึ่งหนึ่งของหน่วยย่อยสุดของ `NUMERIC(5,2)`)
ยืนยันกับ PostgreSQL 16 จริงแล้ว: 7 ร้าน × 14.29 = 100.03 **ผ่าน** · ลบร้านออก 1 เหลือ 85.74 **จับได้**
| 🔴 **ยอดรายร้านรวม ต้องเท่ากับยอดบนหัวเอกสาร** | ระบบเดิม **ไม่เคยตรวจ** ว่า `SUM(compensation_amount)` เท่ากับ `total_compensation_amount` ของเอกสารไหม | 🔴 **ต้องเคาะว่าใครเป็นเจ้าของตัวเลข** — หัวเอกสาร หรือรายร้าน · ผูกกับข้อ **2.31** |
| 🔴 **forecast กับ adjust ถูกยุบเป็นค่าเดียว** | ระบบเดิมส่ง `nvl(adjust, forecast)` ในชื่อ `forecast` แล้วบังคับ `adjust = null` | ✅ **ปิดแล้ว 2026-09-13 — หมดปัญหาโดยโครงสร้าง** (เหมือน Job 8) · ระบบเดิมเสียข้อมูลเพราะ**ไฟล์มีช่องเดียว** · ของใหม่ `sgi_fgi_new_store_compensations` เก็บ `forecast_amount`/`forecast_percent`/`adjust_amount`/`adjust_percent` **แยกกันครบ 4 ค่า** และเอกสารเก็บ `source_row_id` ชี้กลับไปได้ |
| 🔴 **`DISTANCE_UNIT` หายจากไฟล์** | คิวรี select มาแต่ไม่ได้เขียนลงไฟล์ · รัศมีมีหน่วยกำกับแต่ระยะทางไม่มี · ตารางใหม่ `distance_km` มีหน่วยเดียว **จึงต้องแปลงตั้งแต่ Job 2** | 🔴 ผูกกับกติกาแปลงหน่วยในเอกสาร **Job 2 หัวข้อ 4** — ถ้าแปลงถูกที่ต้นทาง ปัญหานี้หายไปเอง |
| 🔴 **Job 9 ไม่กันช่องทาง `STA` ออก** | Job 4/7/8 กัน แต่ Job 9 ส่งทุกช่องทาง | ⚙️ **ทำเป็น config `SGI_JOB9_DATASOURCE`** ค่าตั้งต้น `''` (ไม่กรอง · คงพฤติกรรมเดิม) · ตั้ง `'ALM'` ได้เมื่อธุรกิจเคาะ · **ควรเคาะพร้อม Job 7** (ข้อ 2.24) |
| **ข้อมูลร้านใหม่ที่ไม่มีที่เก็บ** | `NAME_N` · `ZONE_N` · `BRANCHTYPE_N` · `OPENDATE_N` · นิติบุคคล · ชื่อแฟรนไชซี — ตารางใหม่ไม่เก็บ ต้อง join master | ⏳ ตรงกับหลักการ "ห้ามเก็บ master ซ้ำ" **แต่ตรวจย้อนหลังไม่ได้** (ปัญหาชนิดเดียวกับ **2.15**) |
| **`source_system` · สถานะรอ sync · `source_row_id`** | ปัญหาเดียวกับ Job 7 ทุกข้อ | ✅ **ปิดแล้ว 2026-09-13 พร้อม Job 7** — `source_system = 'ALLMAP'` · สถานะรอ sync เก็บเป็น `sgi_interface_transactions` `status='PENDING'` · เพิ่มคอลัมน์ `sgi_document_new_stores.source_row_id` ชี้ไป `sgi_fgi_new_store_compensations(id)` |
| **ลำดับการรัน Job 9 กับ Job 8** | Job 9 ต้องรันหลัง Job 8 | ⏳ ระบุ dependency ใน AWS Batch |
| **รันย้อนหลัง** | ไม่รับ argument เลย | ✅ **ทำแล้ว** — รับ `docNo` · `impactedStoreCode` · `compensateMonth` · `datasource` · `dryRun` เป็น optional · ไม่ส่งอะไรเลยทำงานเหมือนเดิมทุกประการ |

---

### 🔴 ช่องว่างที่พบตอนตรวจข้ามทั้ง 12 job (2026-09-13)

**Job 11 อัปเดตยอดที่ STA จ่ายจริงได้ทุกสถานะ แต่ Job 9 เดิมคัดเฉพาะ `compensate_status = 'I'`**

| รอบชดเชย | Job 11 เขียนยอดจริง | Job 9 ยกขึ้นเอกสาร (เดิม) |
|---|---|---|
| `I` (ยังไม่อนุมัติ) | ✅ | ✅ |
| **`A` / `S` (อนุมัติ/ส่งแล้ว)** | ✅ | 🔴 **ไม่ยก** |

→ ยอดจริงค้างอยู่ชั้น pipeline **เอกสารแสดงตัวเลขก่อนจ่าย**
ซึ่งเป็นปัญหาเดียวกับที่ Job 11 มีไว้แก้ (*"คนเปิดเอกสารดูย้อนหลังจะเห็นตัวเลขผิด"*)

✅ **แก้แล้ว** — เพิ่มสาขา `OR n.updated_by = 'SGI-JOB11'` (`SGI_JOB9_SYNC_STA_UPDATED`)
ยกเฉพาะแถวที่ Job 11 แตะจริง **ไม่กวาดทุกแถวที่อนุมัติแล้ว** · ยืนยันกับ PostgreSQL 16:
ร้านสถานะ `A` ที่ Job 11 แตะ → ยก · ร้านสถานะ `A` ที่ไม่มีใครแตะ → ไม่ยก

> 🔴 อยู่ภายใต้คำถามธุรกิจเดียวกับ `SGI_JOB11_CLOSED_POLICY` — **ต้อง sign-off พร้อมกัน**

---

## 11. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | 🔴 **ไม่เคยตรวจว่า %รวมได้ 100** | ค้นทั้ง `ExportController`/`ExportJdbc` แล้วไม่มีการตรวจผลรวมเลย · กติกาถูกบังคับที่หน้าจอ K2 เท่านั้น | **บังคับที่ pipeline** — validate ต่อ `doc_no` ก่อน commit |
| **L2** | 🔴 **ไม่ตรวจว่า % เป็น NULL หรือนอกช่วง** | เขียนลงไฟล์ตามที่ query ได้ | `NOT NULL` + `CHECK (0..100)` + reject ก่อน upsert (DDL ใหม่ทำแล้ว) |
| **L3** | 🔴 **เงื่อนไขดูฝั่ง I แต่ส่งข้อมูลฝั่ง N** | `fisc.compensate_status = 'I'` · `fisc.compensate_forecast is not null` ตรวจ**ฝั่งร้านถูกกระทบ** แล้วส่งฝั่งร้านใหม่ไปทั้งหมดโดยไม่ตรวจ | ตรวจความครบของฝั่งที่จะส่งจริง |
| **L4** | 🔴 **ผลของ SFTP ถูกทิ้ง** | `FtpUtils.uploadSFTPFile(...);` ไม่มี `if` ครอบ (เหมือน Job 7 · L1) | ระบบใหม่เขียน DB ตรง — แต่หลักการคือ **ห้ามทิ้งผลของ I/O** |
| **L5** | **`DISTANCE_UNIT` select มาแล้วทิ้ง** | `queryOpenNewStore` select แต่ `appendContentOpenNewStore` ไม่เขียน | แปลงหน่วยตั้งแต่ Job 2 แล้วเก็บเป็น `distance_km` หน่วยเดียว |
| **L6** | **ชื่อ-นามสกุลรวมเป็นฟิลด์เดียว** | `FNAME + " " + LNAME` — แยกกลับไม่ได้ | เก็บ/ส่งแยกฟิลด์ |
| **L7** | **`forecast`/`adjust` ยุบและสลับชื่อ** | `nvl(adjust, forecast) as forecast` + `null as adjust` (เหมือน Job 8 · L7) | ส่งทั้งสองค่าแยกกัน |
| **L8** | **คัดออกเงียบ ๆ ไม่รายงานรายร้าน** | `checkProcesssError` คัดออกโดยไม่สร้าง `errorProcessListMap` แบบ Job 8 | รายงานรายร้าน + โซน + ประเภทร้าน ให้ตามแก้ได้ |
| **L9** | **SFTP อยู่ใน DB transaction** | `manageOpenNewStoreToBPM` เหมือน Job 6/7/8 | เขียน DB อย่างเดียว |
| **L10** | **transaction ซ้อนสองชั้น** | `TransactionTemplate.execute()` + `createSavepoint()` เอง | transaction ชั้นเดียว (เหมือน Job 2 · L5) |
| **L11** | **`args` ถูกทิ้งทั้งหมด** | `main()` เรียก `exportOpenNewStore()` โดยไม่ส่ง `args` | รับ input JSON · รองรับรันซ่อมย้อนหลัง |
| **L12** | **`getErrorProcess` ใช้ `'NuLL' in (nvl(...))`** | เทคนิคเทียบสตริงหา NULL | `IS NULL` / `num_nonnulls(...)` (เหมือน Job 7 · L8) |

> ⚠️ **L1 + L2 + L3 รวมกันคือความเสี่ยงที่ร้ายที่สุดของ job นี้**
> ระบบเดิมส่ง %ชดเชยขึ้นเอกสาร **โดยไม่ตรวจอะไรเลย** — ไม่ตรวจว่ามีค่า ไม่ตรวจว่าอยู่ในช่วง ไม่ตรวจว่ารวมได้ 100
> ความถูกต้องพึ่งหน้าจอ K2 ล้วน ๆ · **ถ้าคนกดผ่านโดยไม่ดู เงินจะจ่ายผิดสัดส่วนทันที**
>
> ✅ **DDL ใหม่ปิดสองข้อแรกไปแล้ว** (`NOT NULL` + `CHECK`) เหลือข้อ "รวมได้ 100" ที่ต้องเคาะกติกา

---

## 12. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 7 (คู่แฝด — ยกคู่แข่งขึ้นเอกสาร) | `batchjob/JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md` |
| Job 8 (สร้างเอกสาร · ต้องรันก่อน Job 9) | `batchjob/JOB-08-CreateCompensationDocument-อธิบายละเอียด.md` |
| Job 6 (สร้างค่าชดเชยรายร้านใหม่) | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` |
| Job 2 (กติกาแปลงหน่วยระยะทาง) | `batchjob/JOB-02-ImportImpactStore-อธิบายละเอียด.md` หัวข้อ 4 |
| สเปกรูปแบบมาตรฐานของ Job 9 | `LLDD/md/Jobs/LLDD-BE-Job-9-SyncNewStoreToDocument.md` |
| ตาราง "ร้านที่เปิดใหม่" บนหน้าจอ | `k2-document.html` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
