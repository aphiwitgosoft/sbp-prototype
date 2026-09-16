# Job 4 — PrepareImpactStoreToIAS : ส่งคำขอยอดขายไป IAS/MIS

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-09)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 11 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.17 · 2.24 · 2.25 · 4.4 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-04-PrepareImpactStoreToIAS-อธิบายละเอียด.md` — **path ทุกอันในเอกสารนี้เขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/PrepareImpactStoreToIAS.java` · `service/ImpactStoreService.java` · `service/ExportService.java` · `dao/jdbc/ImportStoreJdbc.java` · `dao/jdbc/ExportJdbc.java` · `dao/batchupdate/UpdateImpactSaleFromIASBatch.java` · `dao/batchupdate/InsertConfirmReceiveDataBatch.java` · `Constant/FgiConstant.java` · `config.xml` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-prepare-impact-store-to-ias` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-4-PrepareImpactStoreToIAS` · **Job 2/3** ดู `batchjob/JOB-02-*.md` และ `batchjob/JOB-03-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

หยิบร้าน SP ที่ **ผ่านการตรวจแล้ว (`P`)** และ **ครบกำหนดเวลาที่จะขอยอดขายได้** แล้ว
**ส่งรายชื่อออกไปให้ระบบ IAS/MIS** เพื่อขอข้อมูลยอดขายรายวันกลับมา

```
sgi_fgi_impact_stores (verify_status = P)
        │  ① คัดร้าน + สร้างหัวสรุปยอดขาย
        ▼
sgi_fgi_impact_sales_summaries (sales_status = W)
        │  ② คัดเฉพาะร้านที่ครบกำหนดเวลา
        ▼
   ไฟล์ AMS06001O_<YYYYMMDDHHMI>.txt  ──▶  IAS/MIS
        │  ③ เปลี่ยนสถานะเป็น P
        ▼
   รอ Job 5 เอายอดขายกลับมา
```

**ระบบใหม่เปลี่ยนช่องทางส่ง** — จากวางไฟล์บน path SFTP เป็น **อัปโหลดขึ้น EAI S3** (มติ 2026-08-24)
แต่ **รูปแบบไฟล์และตรรกะการคัดร้านยังเหมือนเดิม**

### เทียบกับ Job 2/3 ให้เห็นภาพ

| | Job 2 · Job 3 | **Job 4 (ฉบับนี้)** |
|---|---|---|
| ทิศทาง | **นำเข้า** จาก ALLMAP | **ส่งออก** ไป IAS/MIS |
| argument | Job 2 มี `zones\|ปี\|เดือน` · Job 3 มี `ปี\|เดือน` | **ไม่รับ argument เลย** |
| งวดที่ทำ | ระบุได้ | **ไม่มีแนวคิดเรื่องงวด** — ตัดสินจาก "วันเปิดร้าน" เทียบ "วันนี้" |
| ความถี่ | เดือนละครั้ง (วันที่ 7) | **วันที่ 7–16 ทุกวัน = เดือนละ 10 ครั้ง** |
| transaction | มี (`TransactionTemplate`) | ⚠️ **ไม่มีเลย** |

---

## 2. ทำไมต้องมี job นี้

การชดเชยรายได้คำนวณจาก **ยอดขายก่อนและหลังร้านใหม่เปิด** แต่ยอดขายรายวันไม่ได้อยู่ในระบบเรา —
อยู่ที่ระบบ **IAS/MIS** ของอีกทีม

Job 4 จึงทำหน้าที่ **"ตั้งคำถาม"** ว่า *ขอยอดขายของร้านเหล่านี้หน่อย* แล้ว **Job 5 คือตัวรับคำตอบ**

**สายข้อมูลเต็ม:** `Job 2` (คัดคู่ร้าน) → **`Job 4` (ขอยอดขาย)** → `IAS/MIS` → `Job 5` (รับยอดขาย + คำนวณ growth rate) → `Job 8b` (เปิด workflow)

---

## 3. ภาพรวมการทำงาน 7 ขั้น

```
① สร้างชื่อไฟล์จากวันเวลาปัจจุบัน   AMS06001O_YYYYMMDDHHMI.txt
② สร้างหัวสรุปยอดขาย (insertImpactStoreSales)  ← หนึ่งแถวต่อ ร้าน+งวด
③ อ่านรายการที่ถึงกำหนดขอยอดขาย
④ ประกอบเนื้อไฟล์ในหน่วยความจำ
⑤ เปลี่ยนสถานะ W → P            ⚠️ ทำ "ก่อน" เขียนไฟล์
⑥ เขียนไฟล์ลง path IAS + backup
⑦ บันทึก FGI_CONFIRM_RECEIVE_DATA
```

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — ลำดับขั้น ⑤ กับ ⑥ กลับกัน

ระบบเดิม **เปลี่ยนสถานะเป็น `P` ตั้งแต่ขั้น ⑤ ก่อนที่ไฟล์จะถูกเขียนในขั้น ⑥**
และ **ทั้ง job ไม่มี transaction เลยแม้แต่ชั้นเดียว** (ต่างจาก Job 2/3 ที่ยังมี `TransactionTemplate`)

| ถ้าเขียนไฟล์ล้มเหลว | ผล |
|---|---|
| สถานะในฐาน | ✅ เป็น `P` ไปแล้ว (commit ไปแล้ว) |
| ไฟล์ที่ IAS ได้รับ | ❌ ไม่มี |
| รอบถัดไปจะหยิบร้านนี้อีกไหม | ❌ **ไม่** — เพราะคัดเฉพาะ `FLAG_VERIFY = 'W'` |

→ **ร้านนั้นจะไม่มีวันถูกขอยอดขายอีกเลย** และไม่มีใครรู้ จนกว่าจะไปตายที่ Job 8b ที่รอ `growth_rate_diff`

> ✅ **ระบบใหม่กลับลำดับแล้ว** — เขียนไฟล์ให้ durable (fsync + atomic rename + checksum) **ก่อน**
> แล้วค่อย `update W→P` พร้อม `insert outbox` ใน transaction เดียว (ดูหัวข้อ 8)

---

## 4. ขั้นที่ ① — ชื่อไฟล์

```
AMS06001O_ + YYYYMMDDHH24MI + .txt      เช่น  AMS06001O_202606071600.txt
```

| ส่วน | ที่มา | ค่าใน `config.xml` |
|---|---|---|
| ชื่อนำหน้า | `ftpFileNamePattern` | `AMS06001O_` |
| เวลา | `ftpFileTimePattern` | `YYYYMMDDHH24MI` |
| นามสกุล | `ftpFileExtension` | `.txt` |
| path ปลายทาง | `ftpDestinationPath` | `/appshare/SPS/FGI/interface_data/out/IAS/` |
| path สำรอง | `ftpBackUpPath` | `/appshare/SPS/FGI/interface_data/backup_out/IAS/` |

> ⚠️ **ไม่มีวินาทีในชื่อไฟล์** — บรรทัดที่ใส่ `SS` ถูก comment ทิ้ง
> ถ้ารัน 2 รอบภายในนาทีเดียวกัน **ไฟล์จะชื่อซ้ำและถูกเขียนทับ**

### โค้ดแปลงปีที่ต้องอ่านให้ดี

```java
year > 2100 ? String.valueOf(year - 543) : String.valueOf(year)
```

`Calendar.getInstance(Locale.US)` ให้ปฏิทิน Gregorian → `year` = `2026` → เงื่อนไขเป็นเท็จ → **ใช้ ค.ศ.**

> 📌 **บรรทัดนี้เป็น dead code ในทางปฏิบัติ** — จะทำงานก็ต่อเมื่อ JVM ถูกตั้ง locale ไทย
> (ซึ่งจะให้ปฏิทินพุทธ = `2569` > 2100) · เป็นการกันพลาดที่ผู้เขียนใส่ไว้ ไม่ใช่กติกาธุรกิจ
> **ระบบใหม่ต้องกำหนด timezone และปฏิทินให้ชัดตั้งแต่ต้น** แทนการเดาจากค่าปี (ดูหัวข้อ 4 ของ `JOB-02`)

---

## 5. ขั้นที่ ② — สร้างหัวสรุปยอดขาย (สำคัญที่สุดของ job นี้)

```sql
INSERT INTO FGI_IMPACT_STORE_SALES (STORECODE_I, MONTH, YEAR, OPENDATE_I, OPENDATE_N, FLAG_VERIFY)
SELECT FIS.STORECODE_I, FIS.MONTH, FIS.YEAR, FIS.OPENDATE_I, FIS.OPENDATE_N, 'W'
  FROM ( SELECT ..., DENSE_RANK() OVER (
                       PARTITION BY FIS1.STORECODE_I, FIS1.MONTH, FIS1.YEAR
                       ORDER BY FIS1.OPENDATE_N, FIS1.STORECODE_N ) AS ROW_RANK
           FROM FGI_IMPACT_STORE FIS1
          WHERE FIS1.FLAG_VERIFY = 'P'          -- ผ่านกฎของ Job 2 แล้วเท่านั้น
            AND FIS1.CREATE_BY   = 'ALM' ) FIS  -- ⚠️ เฉพาะแถวจาก ALLMAP
 WHERE FIS.ROW_RANK = 1
   AND NOT EXISTS ( ... FGI_IMPACT_STORE_SALES ที่มี ร้าน+เดือน+ปี เดียวกัน ... )
   AND NOT EXISTS ( ... FGI_IMPACT_STORE_ON_PROCESS ที่ FLAG_ACTION = 'Y' ... )
```

### แปลเป็นภาษาคน — 4 เงื่อนไข

| # | เงื่อนไข | ทำไม |
|---|---|---|
| **S1** | คู่ร้านต้อง `verify_status = 'P'` | ผ่านกฎ DENY/ON_PROCESS ของ Job 2 มาแล้ว |
| **S2** | **`created_by = 'ALM'` เท่านั้น** | ⚠️ **แถว `STA` ถูกกันออก** (ดู 🔴 ด้านล่าง) |
| **S3** | ยังไม่มีหัวสรุปของ (ร้าน + เดือน + ปี) นั้น | กันสร้างซ้ำ |
| **S4** | ร้านนั้น**ไม่มีรอบชดเชยที่ยัง active** (`flag_action = 'Y'`) | ร้านที่กำลังชดเชยอยู่แล้วไม่ต้องขอยอดใหม่ |

### หนึ่งร้าน = หนึ่งแถว ต่อหนึ่งงวด — เลือกร้านใหม่ที่เปิด "ก่อนสุด"

`DENSE_RANK() ... ORDER BY OPENDATE_N, STORECODE_N` แล้วเอา `ROW_RANK = 1`

ร้าน SP หนึ่งร้านอาจถูกกระทบจากร้านใหม่หลายร้านในงวดเดียวกัน (Job 2 สร้างหลายคู่)
แต่ **การขอยอดขายทำครั้งเดียวต่อร้าน** จึงต้องเลือกร้านใหม่มาเป็นตัวแทน **1 ร้าน**

> 📌 **เกณฑ์คือ "ร้านใหม่ที่เปิดก่อนสุด"** — สมเหตุสมผลเพราะช่วงยอดขาย "ก่อนกระทบ" ต้องนับจากร้านแรกที่มากระทบ
> ถ้าเสมอกันใช้ `STORECODE_N` น้อยสุดเป็นตัวตัดสิน (deterministic ✅ ต่างจาก Job 2/3 ที่ไม่ deterministic)

### 🔴 แถว `STA` ถูกกันออก — ตั้งใจหรือหลุด?

`AND FIS1.CREATE_BY = 'ALM'` ทำให้แถวที่มาจาก **Franchise Statement (`STA`)** ไม่ถูกสร้างหัวสรุปยอดขายเลย
ทั้งที่ **Job 2 กฎ P2 ปล่อยแถว `STA` ผ่านเป็น `P` โดยไม่ตรวจอะไรเลย**

| | แถว `ALM` | แถว `STA` |
|---|---|---|
| Job 2 ตั้งให้เป็น `P` | ✅ ตามกฎ | ✅ ผ่านทันที (P2) |
| Job 4 สร้างหัวสรุปยอดขาย | ✅ | ❌ **ไม่สร้าง** |
| จะได้ยอดขายจาก IAS ไหม | ✅ | ❌ **ไม่มีวันได้** |
| แล้ว Job 8b ที่ต้องใช้ `growth_rate_diff` | ✅ | ❌ **เปิด workflow ไม่ได้** |

**เป็นไปได้ 2 อย่าง:** (ก) ตั้งใจ — เคส STA มีเส้นทางอื่นที่ไม่ต้องขอยอดขาย · (ข) หลุด — แถว STA ค้างอยู่เฉย ๆ
**เอกสารเดิมไม่ได้ระบุไว้** จึงต้องเคาะ (ดูหัวข้อ 11) · เกี่ยวโยงกับข้อค้าง P2/STA ของ Job 2 โดยตรง

### ⚠️ `catch` แล้ว `return 0` เงียบ ๆ

```java
}catch(Exception e){ LogUtils.error(getClass(), e); }
return result;   // = 0
```

ถ้า `INSERT` ล้ม (เช่น constraint ชน) job จะ **เดินต่อไปขั้น ③ เหมือนไม่มีอะไรเกิดขึ้น**
แล้วได้รายการว่าง → เขียนไฟล์เปล่า → รายงานว่าสำเร็จ

---

## 6. ขั้นที่ ③ — คัดเฉพาะร้านที่ "ถึงเวลา" ขอยอดขาย

```sql
SELECT STORECODE_I, OPENDATE_N, MONTH, YEAR,
       STORECODE_I || '|' || TO_CHAR(OPENDATE_N, 'YYYYMMDD') AS RESULT
  FROM FGI_IMPACT_STORE_SALES
 WHERE FLAG_VERIFY = 'W'
   AND OPENDATE_I  <= TRUNC(ADD_MONTHS(OPENDATE_N, -12) - 15)
   AND TRUNC(SYSDATE) > (TRUNC(OPENDATE_N + 15) + 1)
 ORDER BY OPENDATE_N, STORECODE_I
```

### กติกาเวลา 2 ข้อ (ค่าคงที่จาก `FgiConstant`)

| ค่า | ตัวแปร | ความหมาย |
|---|---|---|
| **12 เดือน** | `INTERVAL_MONTH` | ระยะเทียบยอดขายย้อนหลัง |
| **15 วัน** | `INTERVAL_DAY` | ระยะกันชนหัว/ท้าย |
| 60 วัน | `TOTAL_INTERVAL_DAY` | จำนวนวันที่ต้องมีข้อมูล (ใช้ที่ Job 5) |

**T1 — ร้านเก่าต้องเปิดก่อนร้านใหม่อย่างน้อย 12 เดือน 15 วัน**

```
OPENDATE_I  <=  (OPENDATE_N − 12 เดือน) − 15 วัน
```

เพราะต้องมียอดขาย "ปีที่แล้วช่วงเดียวกัน" มาเทียบ — ร้านที่เพิ่งเปิดไม่มีข้อมูลให้เทียบ

**T2 — ต้องผ่านไปแล้วอย่างน้อย 16 วันนับจากร้านใหม่เปิด**

```
วันนี้  >  OPENDATE_N + 15 + 1
```

รอให้มียอดขาย "หลังกระทบ" สะสมพอที่จะคำนวณได้

> 📌 **นี่คือเหตุผลที่ job รันวันที่ 7–16 ทุกวัน** — ร้านใหม่เปิดคนละวันกัน จึงถึงกำหนดคนละวัน
> การรันทุกวันทำให้ร้านถูกส่งออกทันทีที่ถึงกำหนด ไม่ต้องรอถึงเดือนหน้า

### รูปแบบไฟล์ — 2 ฟิลด์ต่อบรรทัด

```
00044|20260315
00120|20260318
```

| ฟิลด์ | ที่มา | รูปแบบ |
|---|---|---|
| 1 | `STORECODE_I` | รหัสร้าน SP |
| 2 | `OPENDATE_N` | **วันเปิดร้านใหม่** `YYYYMMDD` (**ค.ศ.**) |

คั่นด้วย `|` · ขึ้นบรรทัดใหม่ด้วย `System.getProperty("line.separator")`

> ⚠️ **`line.separator` ขึ้นกับ OS ที่รัน** — Linux ได้ `\n` · Windows ได้ `\r\n`
> **ระบบใหม่ต้องกำหนดตายตัว** ไม่ใช่ปล่อยตาม OS · และต้องตกลง encoding ให้ชัด
> (ผังระบุ **UTF-8** ต่างจากไฟล์ STA ที่เป็น windows-874)

> ⚠️ **บรรทัดสุดท้ายไม่มี newline ปิดท้าย** (`if (i == size-1)` ต่อ content เฉย ๆ) — ต้องยืนยันกับ IAS ว่ารับได้

### ⚠️ `catch` แล้ว `return null`

เหมือน Job 2 ข้อ L2 — `getPrepareImpactStoreToIASList()` คืน `null` เมื่อ query ล้ม
แล้วขั้น ④ เรียก `impactStoreList.size()` ทันที → **`NullPointerException` กลบต้นเหตุจริง**

---

## 7. ขั้นที่ ⑤ ⑥ ⑦ — เปลี่ยนสถานะ · เขียนไฟล์ · บันทึกการส่ง

### ⑤ เปลี่ยนสถานะ (ทำก่อนเขียนไฟล์ — ดูหัวข้อ 3)

```sql
UPDATE FGI_IMPACT_STORE_SALES
   SET FLAG_VERIFY = 'P', UPDATE_DATE = SYSDATE
 WHERE FLAG_VERIFY = 'W' AND STORECODE_I = ? AND MONTH = ? AND YEAR = ?
```

ยิงเป็น `batchUpdate` ทีละแถวตามรายการที่อ่านมา

> 🔴 **กับดักที่ต้องเห็น** — `catch` ของเมธอดนี้ **รัน `batchUpdate` ตัวเดิมซ้ำอีกครั้ง**
> ```java
> }catch(Exception e){
>     LogUtils.error(getClass(), e);
>     return jdbcTemplate.batchUpdate(sql.toString(), new UpdateImpactSaleFromIASBatch(impactStoreList));
> }
> ```
> ถ้ารอบแรกล้มกลางทาง (บางแถว update ไปแล้ว) รอบสองจะยิงซ้ำทั้งชุด
> `WHERE FLAG_VERIFY = 'W'` ช่วยให้แถวที่เปลี่ยนไปแล้วไม่ถูกแตะซ้ำ (idempotent โดยบังเอิญ ✅)
> **แต่ถ้าสาเหตุที่ล้มคือฐานล่ม การยิงซ้ำทันทีก็จะล้มซ้ำ** และคราวนี้ exception หลุดออกไปจริง

### ⑥ เขียนไฟล์ + backup

เขียนลง `ftpDestinationPath` แล้ว **copy** ไปที่ `ftpBackUpPath` (ไม่ใช่ move — ไฟล์อยู่ทั้งสองที่)

### 🔴 ถ้าเขียนไฟล์ล้มเหลว job ยังรายงานว่าสำเร็จ

```java
}else{
    informBean.setStatus(FgiConstant.JOB_STATUS_FAIL);   // ← ตั้ง FAIL ตรงนี้
}
...
int[] confirmReceiveData = exportService.insertConfirmReceiveData(lstComfirmReceiveData);
isComplete = true;
informBean.setStatus(FgiConstant.JOB_STATUS_SUCCESS);    // ← แล้วถูกทับเป็น SUCCESS ตรงนี้
```

**สถานะ FAIL ที่ตั้งไว้ถูกเขียนทับด้วย SUCCESS อย่างไม่มีเงื่อนไข**
รวมกับข้อ "ไม่มี exit code" (เหมือน Job 2 ข้อ L3) แปลว่า **ไฟล์ไม่ถูกสร้าง แต่ทุกฝ่ายเห็นว่าสำเร็จ**

### ⑦ บันทึกการส่ง

```sql
insert into fgi_confirm_receive_data
  (data_name, transaction_pk, month, year, interface_type, RETURN_CODE, RECEIVE_DATE)
values (?, ?, ?, ?, ?, ?, ?)
```

| คอลัมน์ | ค่าที่ Job 4 ใส่ |
|---|---|
| `data_name` | `'IMPACT_STORE_SALES'` (`FgiConstant.DATA_IMPORT_STORE_SALES`) |
| `transaction_pk` | `STORECODE_I` แปลงเป็นตัวเลข |
| `month` · `year` | งวดของหัวสรุป |
| `interface_type` | **ชื่อไฟล์** (ไม่รวมนามสกุล) |
| `RETURN_CODE` · `RECEIVE_DATE` | 🔴 **ไม่เคยถูกเซ็ต = `null` เสมอ** |

> 🔴 **`transaction_pk` เป็น `NUMBER` แต่รหัสร้านเป็นข้อความ** — `Integer.parseInt(hm.get("STORECODE_I"))`
> ร้าน `00044` กลายเป็น `44` (**ศูนย์นำหน้าหาย**) และถ้ารหัสร้านมีตัวอักษรจะ **`NumberFormatException`**
> ทำให้ทั้ง job ล้มที่ขั้น ④ ทั้งที่ข้อมูลอื่นปกติ · **ระบบใหม่ต้องเก็บเป็นข้อความ**

> 🔴 **`RETURN_CODE`/`RECEIVE_DATE` เป็นช่องของ "ขากลับ"** ที่ Job 5 น่าจะเป็นคนเติม
> แต่ไม่มีโค้ดไหน `UPDATE` ตารางนี้เลย — **ต้องยืนยันว่ามีคนเติมจริงไหม** (ดูหัวข้อ 11)

---

## 8. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลงตาราง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| `FGI_IMPACT_STORE_SALES` | **`sgi_fgi_impact_sales_summaries`** |
| `FGI_CONFIRM_RECEIVE_DATA` | **`sgi_interface_transactions`** (transactional outbox) |
| ไฟล์บน path SFTP | **อัปโหลดขึ้น EAI S3** (มติ 2026-08-24) |

### `sgi_fgi_impact_sales_summaries`

```sql
CREATE TABLE sgi_fgi_impact_sales_summaries (
    id BIGSERIAL PRIMARY KEY,
    impact_process_id BIGINT NOT NULL REFERENCES sgi_fgi_impact_processes(id),
    total_working_days INTEGER NOT NULL DEFAULT 0 CHECK (total_working_days >= 0),
    growth_rate_before NUMERIC(9,4), growth_rate_after NUMERIC(9,4), growth_rate_diff NUMERIC(9,4),
    sales_status CHAR(1) NOT NULL DEFAULT 'W' CHECK (sales_status IN ('W','Y','N','E')),
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sales_summary_process UNIQUE (impact_process_id)
);
```

### 🔴 A — คอลัมน์ที่ Job 4 ต้องใช้ แต่ตารางใหม่ไม่มี

ระบบเดิมเก็บ `OPENDATE_I` และ `OPENDATE_N` ไว้บนหัวสรุปเอง เพราะ **ทั้งกติกา T1/T2 และเนื้อไฟล์ใช้ค่าเหล่านี้**

| ค่าที่ต้องใช้ | ระบบเดิม | ตารางใหม่ |
|---|---|---|
| `OPENDATE_N` (ฟิลด์ที่ 2 ของไฟล์ + กติกา T1/T2) | คอลัมน์บนหัวสรุป | ❌ **ไม่มี** |
| `OPENDATE_I` (กติกา T1) | คอลัมน์บนหัวสรุป | ❌ **ไม่มี** |
| `STORECODE_I` | คอลัมน์บนหัวสรุป | ❌ ไม่มี — ต้อง join ผ่าน `impact_process_id` |
| `MONTH` · `YEAR` | คอลัมน์บนหัวสรุป | ❌ ไม่มี — อยู่ที่แถวแม่ |

**ต้อง join กลับไปหา `mas_store.open_date` ของทั้งสองร้านทุกครั้ง** ซึ่งเป็น **master ที่เปลี่ยนได้**
ต่างจากระบบเดิมที่ **ตรึงค่าไว้ตั้งแต่วันสร้างหัวสรุป**

> 🔴 นี่คือปัญหาชนิดเดียวกับ `branchtype` ของ Job 2 (ข้อ 2.15) — **snapshot vs join master**
> ถ้าวันเปิดร้านใน master ถูกแก้ย้อนหลัง **ร้านที่เคยผ่าน T1/T2 อาจกลายเป็นไม่ผ่าน** (หรือกลับกัน)
> และ **ตรวจย้อนหลังไม่ได้** ว่าตอนนั้นส่งออกด้วยค่าอะไร

### 🔴 B — `UNIQUE (impact_process_id)` เปลี่ยนความหมายของ "หนึ่งแถว"

| | ระบบเดิม | ระบบใหม่ |
|---|---|---|
| คีย์ของหัวสรุป | `STORECODE_I` + `MONTH` + `YEAR` (**ร้าน + งวด**) | `impact_process_id` (**รอบชดเชย**) |

แถวแม่ `sgi_fgi_impact_processes` มี `UNIQUE (impacted_store_code, impact_month)` = ร้าน + งวด **เหมือนกัน**
→ **ความหมายตรงกันโดยบังเอิญ** ตราบใดที่ Job 2 สร้างแถวแม่หนึ่งแถวต่อ (ร้าน + งวด)

> ⚠️ **แต่เงื่อนไข S4 ของระบบเดิมกันร้านที่มีรอบ active อยู่แล้วออก** (`FLAG_ACTION = 'Y'`)
> พอย้ายมาผูกกับ `impact_process_id` ตรง ๆ **ความสัมพันธ์กลับด้าน** — เดิมคือ "ถ้ามีรอบ active อยู่ อย่าสร้าง"
> ตอนนี้คือ "หัวสรุปเป็นของรอบนั้นโดยตรง" · **ต้องเคาะว่าเงื่อนไข S4 ยังต้องมีอยู่ไหม** (ดูหัวข้อ 11)

### `sgi_interface_transactions` — ค่าที่ Job 4 ต้องใส่

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | **`'IAS_SALES_REQUEST'`** (ตาม `CHECK` ของ DDL — **ไม่ใช่** `IMPACT_STORE_SALES` ที่เป็นของ Job 5) |
| `direction` | `'OUT'` |
| `status` | `'READY'` → `'SENT'` → `'COMPLETED'` |
| `outbox_status` | `'READY'` → `'PUBLISHED'` → `'CONFIRMED'` |
| `sales_summary_id` | FK ไปหัวสรุป (typed reference · `ck_interface_typed_reference` บังคับให้มีอย่างน้อย 1 ตัว) |
| `business_key` | รหัสร้าน (แทน `transaction_pk` ที่เดิมเป็นตัวเลข) |
| `period_key` | งวด |
| `file_name` · `file_checksum` | ชื่อไฟล์ + **SHA-256** (ของใหม่ — เดิมไม่มี) |

> ⚠️ **`data_name` ของ Job 4 กับ Job 5 เป็นคนละค่า** — ระบบเดิมใช้ `IMPACT_STORE_SALES` ทั้งขาไปและขากลับ
> DDL ใหม่แยกเป็น `IAS_SALES_REQUEST` (OUT · Job 4) และ `IMPACT_STORE_SALES` (IN · Job 5)
> `UNIQUE (data_name, direction, business_key, period_key)` จึงกันซ้ำแยกกันสองทิศทาง ✅

### ลำดับที่ระบบใหม่ต้องทำ

```
1. อ่าน candidate + lock          SELECT ... FOR UPDATE SKIP LOCKED
2. ประกอบเนื้อไฟล์
3. เขียน temp file + fsync + atomic rename + คำนวณ SHA-256     ← ไฟล์ durable แล้ว
4. ── transaction เดียว ──
      UPDATE sales_status  W → P
      INSERT sgi_interface_transactions (status=READY, outbox_status=READY, checksum)
   ── commit ──
5. dispatcher อัปโหลดขึ้น EAI S3 แล้วอัปเดต outbox_status → PUBLISHED → CONFIRMED
```

**ห้าม commit ขั้น 4 ก่อนขั้น 3 สำเร็จ** และ **ห้ามอัปโหลดโดยไม่มีแถว outbox** — เป็นสัญญาที่ผังกำหนดไว้แล้ว

---

## 9. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `summaryCreatedCount` | หัวสรุปที่สร้างใหม่ในขั้น ② | ถ้า 0 ทุกวันแปลว่า Job 2 ไม่ได้ป้อนงานมา |
| `candidateCount` | ร้านที่ผ่านกติกาเวลา T1/T2 | ยอดที่จะเขียนลงไฟล์ |
| `notDueCount` | หัวสรุปที่เป็น `W` แต่ยังไม่ถึงกำหนด | **ควรมีค่าเสมอ** — ถ้าเป็น 0 ตลอดแปลว่ากติกาเวลาผิด |
| `fileLineCount` · `fileBytes` · `fileChecksum` | เนื้อไฟล์จริง | ต้องตรงกับ `candidateCount` |
| `statusChangedCount` | แถวที่ `W → P` สำเร็จ | 🔴 **ต้องเท่ากับ `candidateCount`** ไม่งั้นมีแถวหลุด |
| `outboxCreatedCount` | แถว outbox ที่สร้าง | ต้องเท่ากับ `candidateCount` |
| `uploadedCount` | ไฟล์ที่อัปโหลดขึ้น S3 สำเร็จ | 0 หรือ 1 |
| `durationMs` | เวลาที่ใช้ | จับ performance |

**สมการที่ต้องเป็นจริงเสมอ:**

```
candidateCount = fileLineCount = statusChangedCount = outboxCreatedCount
```

- 🔴 **alert เมื่อสมการไม่เป็นจริง** — แปลว่ามีร้านที่เปลี่ยนสถานะแล้วแต่ไม่ได้อยู่ในไฟล์ (หรือกลับกัน)
- 🔴 **alert เมื่อ `candidateCount = 0` ติดต่อกันเกิน 3 วันในช่วงวันที่ 7–16** — ผิดปกติสำหรับ job ที่รันทุกวัน

### เมลแจ้งผล ≠ ผลของ job

เหมือน Job 2/3 — **ผลของ job อยู่ที่ exit code เท่านั้น**
โดยเฉพาะ job นี้ที่ระบบเดิม **เขียนทับสถานะ FAIL ด้วย SUCCESS** (ดูหัวข้อ 7)

---

## 10. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — การสร้างหัวสรุป (ขั้น ②)

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | คู่ร้าน `P` จาก ALLMAP ที่ยังไม่มีหัวสรุป | สร้างหัวสรุป 1 แถว · `sales_status = 'W'` |
| 1.2 | ร้านเดียวถูกกระทบจาก **ร้านใหม่ 3 ร้าน** ในงวดเดียวกัน | **สร้างแถวเดียว** · ใช้ร้านใหม่ที่ `open_date` **เก่าสุด** |
| 1.3 | ร้านใหม่ 2 ร้านเปิด**วันเดียวกัน** | ตัดสินด้วย `new_store_code` น้อยสุด · **รันซ้ำต้องได้ร้านเดิม** |
| 1.4 | มีหัวสรุปของ (ร้าน + งวด) อยู่แล้ว | **ไม่สร้างซ้ำ** |
| 1.5 | ร้านมีรอบชดเชยที่ยัง active (`flag_action = 'Y'`) | 🔴 **ขึ้นกับข้อ B ในหัวข้อ 11** — ระบบเดิม**ไม่สร้าง** |
| 1.6 | คู่ร้านเป็น `N` หรือ `W` | ไม่สร้างหัวสรุป |
| 1.7 | **คู่ร้าน `P` ที่ `created_by = 'STA'`** | 🔴 ระบบเดิม **ไม่สร้าง** — ต้องเคาะว่าคงพฤติกรรมนี้หรือไม่ |
| 1.8 | insert หัวสรุปล้มเหลว | ❌ **job ต้องล้มเหลว** — ห้ามเดินต่อแล้วเขียนไฟล์เปล่า |

### กลุ่มที่ 2 — กติกาเวลา (ขั้น ③)

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | ร้านเก่าเปิดก่อนร้านใหม่ **12 เดือน 15 วันพอดี** | **ผ่าน T1** (`<=`) |
| 2.2 | ร้านเก่าเปิดก่อน **12 เดือน 14 วัน** | ❌ ไม่ผ่าน T1 |
| 2.3 | วันนี้ = `open_date(N) + 16` พอดี | ❌ **ไม่ผ่าน T2** — ต้อง `>` ไม่ใช่ `>=` |
| 2.4 | วันนี้ = `open_date(N) + 17` | ✅ ผ่าน T2 |
| 2.5 | ร้านใหม่เปิด **29 ก.พ.** ปีอธิกสุรทิน | คำนวณ `−12 เดือน` ได้ 28 ก.พ. ปีก่อน · ห้ามพัง |
| 2.6 | ร้านใหม่เปิดสิ้นเดือน 31 · ย้อน 12 เดือนไปเดือนที่มี 30 วัน | ใช้กติกาเดียวกับ `ADD_MONTHS` ของ Oracle (ตรึงที่วันสุดท้ายของเดือน) — **ต้องยืนยันว่า PostgreSQL ให้ผลเท่ากัน** |
| 2.7 | หัวสรุปเป็น `W` แต่ยังไม่ถึงกำหนด | **ไม่อยู่ในไฟล์** · นับเข้า `notDueCount` · **คงเป็น `W` ไว้รอบหน้า** |
| 2.8 | หัวสรุปเป็น `P` (ส่งไปแล้ว) | ไม่ถูกหยิบซ้ำ |

### กลุ่มที่ 3 — ไฟล์และการส่ง

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | ไม่มีร้านถึงกำหนดเลย | job **สำเร็จ** · **ไม่สร้างไฟล์** · ไม่มีแถว outbox · log ระบุว่าไม่มีข้อมูล |
| 3.2 | มี 5 ร้านถึงกำหนด | ไฟล์มี **5 บรรทัด** · `รหัสร้าน\|YYYYMMDD` · **รหัสร้านคงศูนย์นำหน้า** |
| 3.3 | **เขียนไฟล์ล้มเหลว** | ❌ **job ล้มเหลว · exit ≠ 0 · สถานะยังเป็น `W` ทั้งหมด** (ห้าม commit W→P) |
| 3.4 | เขียนไฟล์สำเร็จแต่ **อัปโหลด S3 ล้มเหลว** | สถานะ `P` + outbox `READY`/`FAILED` · **dispatcher ส่งซ้ำได้โดยไม่สร้างแถวใหม่** |
| 3.5 | รัน 2 รอบภายในนาทีเดียวกัน | ⚠️ ระบบเดิมชื่อไฟล์ซ้ำและเขียนทับ · **ระบบใหม่ต้องกันชื่อชนได้** |
| 3.6 | รันซ้ำหลังสำเร็จ | ไม่มีร้านเหลือเป็น `W` → ไม่สร้างไฟล์ · **ไม่มีแถว outbox ซ้ำ** (`UNIQUE(data_name,direction,business_key,period_key)`) |
| 3.7 | บรรทัดสุดท้ายของไฟล์ | ตกลงให้ชัดว่ามี newline ปิดท้ายหรือไม่ · **ยืนยันกับ IAS** |
| 3.8 | ตัวคั่นบรรทัด | **ตายตัว `\n`** ไม่ใช่ `System.getProperty("line.separator")` |
| 3.9 | encoding | **UTF-8** (ต่างจากไฟล์ STA ที่เป็น windows-874) |

### กลุ่มที่ 4 — ความคงทนและการรันพร้อมกัน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | ล้มระหว่าง transaction ขั้น 4 | rollback ทั้ง `sales_status` และ outbox · **ไฟล์ที่เขียนไปแล้วต้องถูกเก็บกวาดหรือทิ้งได้อย่างปลอดภัย** |
| 4.2 | ล้มหลัง commit แต่ก่อนอัปโหลด | สถานะ `P` + outbox `READY` · dispatcher เก็บงานต่อได้ |
| 4.3 | รัน 2 instance พร้อมกัน | `FOR UPDATE SKIP LOCKED` + advisory lock → **ร้านหนึ่งร้านอยู่ในไฟล์เดียวเท่านั้น** |
| 4.4 | process ถูก kill ระหว่างเขียนไฟล์ | ไฟล์ temp ไม่ถูก rename → **ปลายทางไม่เห็นไฟล์ครึ่ง ๆ กลาง ๆ** |
| 4.5 | `statusChangedCount ≠ candidateCount` | ❌ **job ล้มเหลว + alert** — มีร้านหลุดจากไฟล์หรือหลุดจากสถานะ |
| 4.6 | ส่งเมลไม่สำเร็จ แต่งานสำเร็จ | exit **0** + log ระดับ ERROR |
| 4.7 | งานไม่สำเร็จ แต่ส่งเมลสำเร็จ | exit **ไม่ใช่ 0** — ห้ามถูกกลบ |

---

## 11. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **แถว `STA` ไม่ได้ยอดขาย** | `insertImpactStoreSales` กรอง `CREATE_BY = 'ALM'` ทำให้แถว `STA` **ไม่มีหัวสรุปยอดขายเลย** ทั้งที่ Job 2 กฎ P2 ปล่อยผ่านเป็น `P` → **ไม่มีวันได้ `growth_rate_diff`** → Job 8b เปิด workflow ไม่ได้ · เป็น **(ก) พฤติกรรมที่ตั้งใจ** (STA มีเส้นทางอื่น) หรือ **(ข) ช่องโหว่ที่ค้างมานาน** | 🔴 **ต้องเคาะ** — ผูกกับข้อค้าง P2/STA ของ Job 2 โดยตรง · ถ้าเป็น (ก) ต้องระบุว่าเส้นทางอื่นคืออะไร |
| 🔴 **`open_date` — snapshot หรือ join master** | ตารางใหม่ **ไม่มี** `OPENDATE_I`/`OPENDATE_N` ที่ทั้งกติกา T1/T2 และเนื้อไฟล์ต้องใช้ · ระบบเดิมตรึงค่าไว้ตอนสร้างหัวสรุป · เลือก **(ก) เพิ่ม 2 คอลัมน์เป็น snapshot** · **(ข) join `mas_store.open_date` ทุกครั้ง** | 🔴 **ต้องเคาะ** — ปัญหาชนิดเดียวกับ `branchtype` ของ Job 2 (ข้อ 2.15) · ถ้าเลือก (ข) แล้ว master ถูกแก้ย้อนหลัง ผลการคัดร้านจะเปลี่ยนและตรวจย้อนหลังไม่ได้ |
| 🔴 **เงื่อนไข S4 ยังต้องมีไหม** | ระบบเดิมกันร้านที่มีรอบชดเชย active (`flag_action = 'Y'`) ออกจากการสร้างหัวสรุป · ระบบใหม่ผูกหัวสรุปกับ `impact_process_id` ตรง ๆ ด้วย `UNIQUE` → **ความสัมพันธ์กลับด้าน** | 🔴 **ต้องเคาะ** — ถ้าตัด S4 ทิ้ง ร้านที่กำลังชดเชยอยู่จะถูกขอยอดขายซ้ำ |
| 🔴 **`RETURN_CODE` / `RECEIVE_DATE` ใครเติม** | สองคอลัมน์นี้เป็นช่องของ "ขากลับ" แต่ **ไม่มีโค้ดไหน `UPDATE` `FGI_CONFIRM_RECEIVE_DATA` เลย** — Job 4 ใส่ `null` แล้วไม่มีใครมาเติม | 🔴 **ต้องยืนยัน** — ถ้าไม่มีใครเติมจริง แปลว่าระบบเดิม **ไม่เคยรู้ว่า IAS รับไฟล์ได้ไหม** · ระบบใหม่ใช้ `outbox_status = CONFIRMED` แทน |
| 🔴 **`ADD_MONTHS` ของ Oracle vs PostgreSQL** | Oracle `ADD_MONTHS` มีกติกา "ตรึงวันสุดท้ายของเดือน" ที่ PostgreSQL `+ INTERVAL '12 months'` ไม่เหมือนกัน | 🔴 **ต้องทดสอบเทียบ** — กระทบว่าร้านจะถึงกำหนดวันไหน (เคสทดสอบ 2.5/2.6) |
| **รูปแบบไฟล์** | ตัวคั่นบรรทัด (`\n` ตายตัว) · newline ปิดท้าย · encoding UTF-8 | ⏳ **ต้องยืนยันกับทีม IAS/MIS** |
| **ชื่อไฟล์ชนกัน** | ชื่อไฟล์ละเอียดถึงระดับ**นาที** — รัน 2 รอบในนาทีเดียวกันจะเขียนทับ | ⏳ เพิ่มวินาที หรือ run id ต่อท้าย · ต้องยืนยันว่า IAS รับรูปแบบใหม่ได้ |
| **ปี พ.ศ./ค.ศ.** | ชื่อไฟล์ใช้ ค.ศ. · เนื้อไฟล์ `TO_CHAR(OPENDATE_N,'YYYYMMDD')` ก็ ค.ศ. | 🔴 `DECISIONS` ข้อ **4.4** — ต้องยืนยันกับ IAS ว่าคาดหวัง ค.ศ. |

---

## 12. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | **เปลี่ยนสถานะก่อนเขียนไฟล์ · ไม่มี transaction เลย** | `PrepareImpactStoreToIAS.java` STEP 05 (บรรทัด ~112) มาก่อน STEP 06 (บรรทัด ~120) · ทั้งไฟล์ไม่มี `TransactionTemplate` | **เขียนไฟล์ให้ durable ก่อน** (fsync + atomic rename + checksum) แล้วค่อย `update W→P` + `insert outbox` ใน **transaction เดียว** |
| **L2** | **สถานะ FAIL ถูกทับด้วย SUCCESS** | บรรทัด ~158 ตั้ง `FAIL` ใน `else` แล้วบรรทัด ~172 ตั้ง `SUCCESS` แบบไม่มีเงื่อนไข | **ผลของ job อยู่ที่ exit code** · ห้ามตั้งสถานะทับโดยไม่ดูผลก่อนหน้า |
| **L3** | **จับ exception แล้วไม่กำหนด exit code** | `catch(Exception e)` ตั้ง FAIL ส่งเมล แล้วหลุดออกจาก `main` ตามปกติ | exit non-zero เสมอเมื่อล้มเหลว (เหมือน Job 2 · L3) |
| **L4** | **DAO คืน `null` เมื่อ query ล้ม** | `getPrepareImpactStoreToIASList` บรรทัด 112-115 · แล้ว `impactStoreList.size()` ทำให้เกิด NPE | โยน exception ต่อ · `[]` สงวนไว้สำหรับ "ไม่มีข้อมูล" เท่านั้น |
| **L5** | **`insertImpactStoreSales` กลืน exception แล้วคืน 0** | บรรทัด 455-458 | insert ล้ม = **job ล้มเหลว** ห้ามเดินต่อ |
| **L6** | **`catch` แล้วยิง `batchUpdate` ตัวเดิมซ้ำ** | `updateImpactStoreSalesFlagVerify` บรรทัด 473-476 | ใช้ retry policy ที่ควบคุมได้ (จำนวนครั้ง · backoff) ไม่ใช่ยิงซ้ำทันทีใน `catch` |
| **L7** | **`Integer.parseInt(STORECODE_I)`** | STEP 04 · รหัสร้าน `00044` → `44` (ศูนย์นำหน้าหาย) · รหัสที่มีตัวอักษรจะ `NumberFormatException` ล้มทั้ง job | เก็บรหัสร้านเป็น **ข้อความ** (`business_key VARCHAR`) |
| **L8** | **`exportService` เป็น static field ที่ไม่มีใคร inject โดยตรง** | `main()` ไม่เคย `getBean("prepareImpactStoreToIAS")` — ค่าถูกเซ็ตเพราะ Spring **สร้าง singleton bean ที่ไม่มีใครใช้** ใน `config.xml:1260-1261` แล้ว setter ไปเซ็ต static field | **ใช้ DI ปกติของ NestJS** · ถ้าใครลบ bean ที่ดูเหมือนไม่ถูกใช้ออกจาก config เมื่อไร STEP 07 จะ **NPE ทันที** |
| **L9** | **ชื่อไฟล์ละเอียดแค่ระดับนาที** | บรรทัดที่ใส่ `SS` ถูก comment ทิ้ง | เพิ่มวินาทีหรือ run id · และตรวจว่าไฟล์ปลายทางยังไม่มีอยู่ก่อนเขียน |
| **L10** | **`line.separator` ตาม OS** | `System.getProperty("line.separator")` | กำหนดตายตัว — รูปแบบไฟล์ต้องไม่ขึ้นกับเครื่องที่รัน |

> ⚠️ **L1 + L2 + L3 รวมกันคือความเสี่ยงที่ร้ายที่สุดของ job นี้**
> เขียนไฟล์ล้มเหลว → สถานะเป็น `P` ไปแล้ว → รอบหน้าไม่หยิบซ้ำ → **แต่ทุกฝ่ายเห็นว่า job สำเร็จ**
> ร้านนั้นจะไม่มียอดขาย ไม่มี `growth_rate_diff` และ **ไปตายที่ Job 8b** โดยไม่มีใครรู้ว่าต้นเหตุอยู่ที่นี่

---

## 13. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 2 (คู่ร้าน · กฎ P/N · แถว STA) | `batchjob/JOB-02-ImportImpactStore-อธิบายละเอียด.md` |
| Job 3 (ร้านคู่แข่ง) | `batchjob/JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md` |
| Job 5 (รับยอดขายกลับ + คำนวณ growth rate) | `LLDD/md/Jobs/LLDD-BE-Job-5-ImportImpactSaleFromIAS.md` |
| สเปกรูปแบบมาตรฐานของ Job 4 | `LLDD/md/Jobs/LLDD-BE-Job-4-PrepareImpactStoreToIAS.md` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| พจนานุกรมข้อมูลรายคอลัมน์ | `LLDD/pdf/LLDD-Database-Dictionary.pdf` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
