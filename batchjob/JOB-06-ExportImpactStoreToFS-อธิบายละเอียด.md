# Job 6 — ExportImpactStoreToFS : ซิงก์สถานะรอบชดเชย แล้วส่งค่าชดเชยไป STA

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-09)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 12 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.4 · 2.7 · 2.28 · 2.29 · 4.4 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/ExportImpactStoreToFS.java` · `controller/ExportController.java` (`getImpactStoreToFS` · `manageDBAndQueryDataToFS` · `manageDataToFS` · `mapDataImpactStoreDataToFS` · `checkDateToCrateInitToSTA`) · `service/ExportService.java` (`manageDBToFs`) · `dao/jdbc/ExportJdbc.java` · `Constant/FgiConstant.java` · `config.xml` · `ApplicationResources.properties` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-export-impact-store-to-fs` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-6-ExportImpactStoreToFS` · **Job 4/5** ดู `batchjob/JOB-04-*.md` และ `batchjob/JOB-05-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

job นี้ทำ **สองเรื่องที่ไม่เกี่ยวกันโดยตรง** ในการรันครั้งเดียว:

```
เรื่องที่ 1 — ซิงก์สถานะ (ทำทุกวัน)
   เลื่อนสถานะรอบชดเชยให้ตรงกับความจริง: รอบไหนจบแล้ว · รอบไหนต้องกลับมารอ

เรื่องที่ 2 — ส่งค่าชดเชยไป STA (ทำเฉพาะวันที่ ≥ 7 และคะแนน QSSI ครบ)
   ประกอบข้อมูล 14 ฟิลด์ ส่งให้ระบบ Franchise Statement เอาไปตัดจ่ายจริง
```

**STA (Franchise Statement) คือระบบที่จ่ายเงินจริง** — Job 6 คือสะพานเส้นสุดท้ายก่อนเงินออก

**ระบบใหม่เปลี่ยนช่องทางส่ง** — จากเขียนไฟล์ `FRBC0001` + SFTP เป็น **RabbitMQ message** (มติ 2026-08-24)
แต่ **เนื้อข้อมูล 14 ฟิลด์ยังเป็นสัญญาเดิม**

### เทียบกับ job อื่นในกลุ่ม

| | Job 4 | Job 5 | **Job 6 (ฉบับนี้)** |
|---|---|---|---|
| ทิศทาง | ส่งออกไป IAS | รับกลับจาก IAS | **ส่งออกไป STA** |
| argument | ไม่มี | ไม่มี | **`yyyyMMdd` = วันที่อ้างอิงการรัน** |
| ความถี่ | วันที่ 7–16 | ตามข้อความจาก EAI | **ทุกวัน 17:00** |
| ผลลัพธ์ | ไฟล์คำขอ | สถานะ `Y`/`N` | **ข้อมูลที่ทำให้เงินออกจริง** |
| ความซับซ้อน | ต่ำ | สูง | **สูงที่สุด — 10 mutation + gate 2 ชั้น** |

---

## 2. ทำไมต้องมี job นี้

ระบบ SGI ตัดสินว่า *ควรชดเชยเท่าไร* แต่ **ไม่ได้จ่ายเงินเอง** — เงินออกจากระบบ Franchise Statement (STA)
ซึ่งเป็นระบบที่ออกใบแจ้งยอดให้ร้าน SP ทุกเดือน

Job 6 จึงเป็นตัว **ส่งผลการพิจารณาไปให้ STA ตัดจ่าย** และ **รับสถานะการจ่ายกลับมาซิงก์**

**สายข้อมูลเต็ม:** `Job 5` (ตัดสิน Y/N) → `Job 8b` (เปิด workflow) → คนอนุมัติ → **`Job 6` (ส่งไป STA)** → STA จ่ายเงิน → `Job 11` (รับสถานะจ่ายกลับ)

---

## 3. ภาพรวมการทำงาน

```
① อ่าน argument → ได้ "วันที่อ้างอิง" (ไม่ส่ง = วันนี้)
      │  แปลงเป็น: งวด = เดือนก่อนหน้า · วันของเดือน = ตัวตัดสิน gate
      ▼
② Gate 1 — วันของเดือน ≥ 7 ?          (dateStartInitToSTA)
      │  ไม่ถึง ──▶ ไม่สร้างข้อมูลใหม่ แต่ยังซิงก์สถานะ
      ▼
③ Gate 2 — คะแนน QSSI ครบ 6 หมวด ?
      │  ไม่ครบ ──▶ ข้ามเส้นทาง INIT (สาย APPROVE ยังไปต่อ)
      ▼
④ รัน 9 คำสั่งซิงก์/สร้างข้อมูล ใน transaction เดียว
      ▼
⑤ query ชุดที่ส่งออกได้ → ประกอบไฟล์ 14 ฟิลด์
      │  ไม่มีแถว ──▶ จบ (ถือว่าสำเร็จ)
      ▼
⑥ เขียนไฟล์ FRBC0001_yyyyMMddHHmmss.txt (windows-874)
      + insert FGI_CONFIRM_RECEIVE_DATA 2 แถวต่อบรรทัด (ฝั่ง I และ N)
      ▼
⑦ ส่ง SFTP ไป EAI → สำเร็จ = move ไป backup · ล้ม = rollback ทั้ง transaction
```

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — argument ไม่ใช่ "งวด" แต่เป็น "วันที่อ้างอิง"

```java
parameter = isParameter ? แปลง args[0] เป็น yyyyMMdd
                        : วันนี้ในรูปแบบ yyyyMMdd;
```

จากวันที่นั้นโค้ดแตกออกเป็น **3 ค่า** ที่ใช้คนละหน้าที่:

| ค่า | ได้จาก | ใช้ทำอะไร |
|---|---|---|
| `INITDATE` (`yyyyMM`) | เดือนของวันที่อ้างอิง | งวดที่ใช้เทียบใน SQL ซิงก์สถานะ |
| `month` / `year` | **เดือนก่อนหน้า** | งวดที่ใช้ตรวจคะแนน QSSI |
| `curDate` (`dd`) | วันของเดือน | **ตัวตัดสิน Gate 1** |

> ⚠️ **ส่ง argument = เปลี่ยนพฤติกรรมทั้ง 3 อย่างพร้อมกัน** — ไม่ใช่แค่ "รันย้อนหลังงวดนั้น"
> การส่ง `20260615` จะทำให้ Gate 1 ผ่าน (15 ≥ 7) และตรวจ QSSI ของงวด **พฤษภาคม**
> **ระบบใหม่ต้องแยกสามเรื่องนี้ออกจากกันให้ชัด** ไม่ให้ค่าเดียวคุมสามอย่าง

> 🔴 **การแปลง argument ที่ล้มเหลวถูกกลืน** — `catch` แค่ตั้ง `errorMsg` แล้วปล่อยให้ `isCompleted` เป็น `false`
> ไม่มี exit code · ไม่มี exception หลุดออกมา · **job ที่ได้ argument ผิดจะ "ล้มเหลวเงียบ"** แล้วส่งเมลว่า FAIL

---

## 4. Gate 1 — วันของเดือนต้องถึงเกณฑ์

```java
final int DATE_START_INIT_TO_STA = Integer.parseInt(PROPS.getProperty("dateStartInitToSTA"));  // = 7
if (Integer.parseInt(curDate) >= DATE_START_INIT_TO_STA) {
    isCreateDateToSTA = true;     // "Create Data"
} else {
    // "No Create Data"
}
```

| ค่า | ที่มา | ค่าจริง |
|---|---|---|
| `dateStartInitToSTA` | `ApplicationResources.properties` | **7** |
| `numWaitPay` | เดียวกัน | **3** (จำนวนงวดรอจ่าย) |
| `categoryQssi` | เดียวกัน | **8, 9, 12, 1, 10, 16** |

**ความหมาย** — วันที่ 1–6 ของเดือน job ยัง **ซิงก์สถานะ** แต่ **ไม่สร้างรอบชดเชยใหม่**
เพราะต้องรอให้ข้อมูลของงวดที่แล้ว (ยอดขาย · คะแนน QSSI) ลงระบบครบก่อน

> 📌 `checkDateToCrateInitToSTA()` ตรวจซ้ำอีกชั้นว่า `7 ≤ วันที่ ≤ วันสุดท้ายของเดือน`
> ซึ่ง**ให้ผลเหมือนกับ Gate 1 เสมอ** (วันที่ในเดือนย่อมไม่เกินวันสุดท้ายอยู่แล้ว) — เป็นโค้ดซ้ำซ้อน

---

## 5. Gate 2 — คะแนน QSSI ต้องครบ 6 หมวด

```java
if (exportService.countRowQssi(year, month, QSSI_CATEGORY) > 0) { isQssi = true; }
```

**QSSI** = คะแนนประเมินคุณภาพร้าน 6 หมวด (`8 · 9 · 12 · 1 · 10 · 16`) ที่ระบบ SBP เดิมนำเข้าให้แล้ว
(นี่คือเหตุผลที่ **Job 1 ImportQSSI ถูกตัดออกจากขอบเขต** เมื่อ 2026-08-24)

### ตรรกะกลับด้านที่ต้องอ่านให้ดี

```java
if ((IS_QSSI == false) && IS_CREATE_DATE_TO_STA) {
    LogUtils.info(getClass(), "No qssi score");
    if (impactStoreList.isEmpty()) {
        deletetComfirmRecieveDataAndWsLog(informBean);
        return true;                      // ถือว่าสำเร็จ
    }
}
```

**ไม่มีคะแนน QSSI ไม่ได้แปลว่าหยุดทั้ง job** — แปลว่า:

| สาย | ไม่มี QSSI | มี QSSI |
|---|---|---|
| **INIT** (`I`, `C`) — เปิดรอบชดเชยใหม่ | ❌ ข้าม | ✅ สร้าง |
| **APPROVE** (`A`, `N`, `S`, `Z`) — ผลอนุมัติของรอบที่มีอยู่ | ✅ **ยังส่งต่อไป** | ✅ ส่ง |

> 📌 **สมเหตุสมผล** — คะแนน QSSI จำเป็นตอน *เปิดรอบใหม่* เท่านั้น
> รอบที่เปิดไปแล้วและคนอนุมัติแล้ว ไม่ต้องรอคะแนนอีก

---

## 6. ขั้นที่ ④ — 9 คำสั่งซิงก์สถานะ

`ExportService.manageDBToFs()` รันเรียงกันใน transaction เดียว:

| # | คำสั่ง | เงื่อนไข | ทำอะไร |
|---|---|---|---|
| 1 | `updateCompleteImpactStoreOnProcess` | **ทุกครั้ง** | ปิดรอบที่ STA ตอบกลับครบแล้ว (`W` → `N`) |
| 2 | `updateImpactStoreOnProcessFlagYToW` | **ทุกครั้ง** | รอบที่ส่งไปแล้วแต่ยังไม่ถึงกำหนด → `Y` กลับเป็น `W` |
| 3 | `updateFgiImpactStoreOnProcess` | เฉพาะเมื่อ Gate 1 ผ่าน | เลื่อนงวดของรอบที่ยังชดเชยต่อเนื่อง |
| 4 | `insertFgiImpactStoreOnProcess` | ↑ | **เปิดรอบชดเชยใหม่** |
| 5 | `insertFgiImpactStoreCompensate` | ↑ | สร้างแถวค่าชดเชย**ฝั่งร้านถูกกระทบ (I)** |
| 6 | `insertFgiNewStoreCompensate` | ↑ | สร้างแถวค่าชดเชย**ฝั่งร้านเปิดใหม่ (N)** |
| 7 | `insertImpactStoreInfo` | ↑ | snapshot ข้อมูลร้านถูกกระทบ |
| 8 | `insertNewStoreInfo` | ↑ | snapshot ข้อมูลร้านเปิดใหม่ |
| 9 | `updateFgiImpactStoreFlagAccept` / `...FlagDeny` | ↑ | ปิดธงคู่ร้านที่ถูกใช้ไปแล้ว |

> 📌 **คำสั่งที่ 1 กับ 2 ทำทุกวันแม้ Gate 1 ไม่ผ่าน** — นี่คือเหตุผลที่ job รันทุกวัน
> การซิงก์สถานะกับการสร้างข้อมูลใหม่เป็นคนละเรื่องกัน

### 🔴 `compensate_status` — โดเมน 6 ค่าที่ต้องเข้าใจ

| ค่า | ความหมาย | ตั้งตอนไหน |
|---|---|---|
| **`I`** | Initial — เปิดรอบชดเชย รอผลอนุมัติ | ขั้นที่ 5 (ค่าปกติ) |
| **`C`** | **ร้านปิดแล้ว หรือสัญญา SBP ถูกยกเลิก** | ขั้นที่ 5 (แทน `I`) |
| **`A`** | Approve — อนุมัติจ่าย | หลังคนอนุมัติ |
| **`N`** | ไม่อนุมัติ | ↑ |
| **`S`** | ส่ง STA แล้ว | ↑ |
| **`Z`** | ค้างในระบบ | ↑ |

**เงื่อนไขที่ตั้งเป็น `C` แทน `I`** (`ExportJdbc.insertFgiImpactStoreCompensate`):

```sql
case when ms.close_date <= to_date(งวด,'YYYYMM')                              -- ร้านปิดแล้ว
       or ( to_date(งวด,'YYYYMM') >= trunc(nvl(s_i.cancel_date, '4000-01-01'))
            and s_i.cancel_type in ('01','02','03','04','08') )               -- สัญญายกเลิก
     then 'C' else 'I' end
```

> ✅ เรื่องนี้**ปิดแล้ว** เป็น `DECISIONS` ข้อ **2.7** — `C` = ร้านปิด/สัญญายกเลิก และ **ส่ง STA เป็น `S`**

### การจับคู่สถานะ → ชื่อข้อความที่ส่ง

| `compensate_status` | ส่งเป็น |
|---|---|
| `I` · `C` | **`COMPENSATE_INIT_I`** / `COMPENSATE_INIT_N` |
| `A` · `N` · `S` · `Z` | **`COMPENSATE_APPROVE_I`** / `COMPENSATE_APPROVE_N` |

**ทุกแถวส่งเป็นคู่ — ฝั่ง `I` (ร้านถูกกระทบ) และฝั่ง `N` (ร้านเปิดใหม่)**

### 🔴 `Z` ถูกแปลงเป็น `S` เฉพาะตอนส่ง

ผังระบุว่า **`Z` จะถูกแปลงเป็น `S` เฉพาะใน payload ที่ส่งออก — ใน DB ยังเป็น `Z`**
เป็นความแตกต่างที่ **มองไม่เห็นจาก DB** ต้องเขียนไว้ในสเปกให้ชัด ไม่งั้นคนพอร์ตจะพลาด

---

## 7. ขั้นที่ ⑤ ⑥ — ประกอบไฟล์ 14 ฟิลด์

### รูปแบบไฟล์ `FRBC0001_yyyyMMddHHmmss.txt`

| # | ฟิลด์ | ที่มา | รูปแบบ |
|---|---|---|---|
| 1 | `STORECODE_I` | รหัสร้านถูกกระทบ | ข้อความ |
| 2 | `STORECODE_N` | รหัสร้านเปิดใหม่ | ข้อความ |
| 3 | `OPENDATE_N` | วันเปิดร้านใหม่ | **`dd/MM/yyyy` พ.ศ.** 🔴 มีสแลช |
| 4 | `COUNT_STORECODE_N` | จำนวนร้านใหม่ที่กระทบ | ตัวเลข |
| 5 | งวดชดเชย | `COMPENSATE_YEAR` + `MONTH` | **`yyMM` พ.ศ.** |
| 6 | งวด Statement | `STMT_YEAR` + `MONTH` | **`yyMM` พ.ศ.** (ว่างได้) |
| 7 | `COMPENSATE_COMMENT` | หมายเหตุ | ข้อความ |
| 8 | `COMPENSATE_STATUS` | สถานะ | 1 ตัวอักษร |
| 9–14 | `QSSI1_SCORE` … `QSSI6_SCORE` | คะแนน 6 หมวด | ตัวเลข |

- คั่นด้วย **`|`** · ขึ้นบรรทัดด้วย `System.getProperty("line.separator")`
- **encoding `windows-874`** (`FgiConstant.FILE_ENCODING_STA`)

### 🔴 ตรวจกับไฟล์จริงแล้ว 2026-09-16 — เอกสารเดิมผิด 1 จุด และได้ความรู้ใหม่ 2 เรื่อง

ไฟล์ตัวอย่างจริงอยู่ที่ `docs/file_IAS_STA/FRBC0001_*.txt` (3 ไฟล์ 56 แถว) · คำอธิบายเต็มที่
`docs/IAS-STA-interface-files.md`

**ผิด:** ฟิลด์ 3 เป็น **`dd/MM/yyyy` มีสแลช** (`29/08/2569`) ไม่ใช่ `ddMMyyyy` ตามที่สเปกเดิมเขียน

**ใหม่ 1 — ชื่อของหมวด QSSI ทั้ง 6** ถอดได้จากรายงาน `RT040035` ของ STA ร้านเดียวกันงวดเดียวกัน
(ค่าใน `FRBC0001` ตรงกับคอลัมน์ "เกิดจริง" ในรายงานทุกตัว ยืนยัน 3 ร้าน):

| ฟิลด์ | หมวด | ชื่อ | มาตรฐาน | กติกาหักที่ STA ใช้ |
|---|---|---|---|---|
| 9 | 8 | **Result** | 90 | `max(0, 90 − เกิดจริง)` |
| 10 | 9 | **Process** | 90 | `max(0, 90 − เกิดจริง)` |
| 11 | 12 | **สินค้าขาด** | 4 | `max(0, เกิดจริง − 4)` ← ยิ่งมากยิ่งแย่ |
| 12 | 1 | **บริการ** | 90 | `min(5, max(0, 90 − เกิดจริง))` ← เพดาน 5% |
| 13 | 10 | **Follow up** | 0 | ทุก 10 คะแนน หัก 1% · **ติดลบได้** (พบ `-30` จริง) |
| 14 | 16 | **สินค้าหมดอายุ** | 100 | ไม่ถึง 100 หัก 10% |

`จำนวนเงินชดเชย = ยอดหลังปรับปรุง × (100% − รวมหัก%)` — **คำนวณที่ STA ไม่ใช่ที่เรา**

**ใหม่ 2 — แถวเดิมถูกส่งซ้ำด้วยสถานะใหม่** ร้านเดียวงวดเดียวปรากฏสองครั้งห่างกันสองวัน
เปลี่ยนแค่ฟิลด์ 6 (งวด statement ว่าง → `6909`) กับฟิลด์ 8 (`I` → `S`) · ในตัวอย่างพบ 7 ร้าน
→ **outbox/dedup ของระบบใหม่ต้องยอมให้ส่งซ้ำต่อ business key ได้** ไม่งั้นข้อความ `S` จะหาย

### 🔴 วันที่ในไฟล์เป็น พ.ศ.

```java
DateUtils.changeformatString(..., Locale.US, new Locale("th","TH"))
```

**`new Locale("th","TH")` ทำให้ Java ใช้ปฏิทินพุทธ** → ฟิลด์ 3 · 5 · 6 ออกมาเป็น **พ.ศ.**

> ✅ **นี่คือสัญญาของ STA ที่ต้องรักษาไว้** — เป็นข้อยกเว้นที่ระบบตกลงกันไว้แล้ว
> (ไฟล์ `FRBC0001` ของ STA คงเป็น พ.ศ. + windows-874 · **แปลงเฉพาะตอนประกอบ payload ห้ามให้ปนเข้า DB/API**
> 🔴 แก้ 2026-09-16 — ไฟล์ของ **IAS** เป็น **ค.ศ.** ไม่ใช่ พ.ศ. ดู `docs/IAS-STA-interface-files.md`)

### 🔴 แถวเดียวพัง = ยกเลิกทั้งรอบ

```java
String data = mapDataImpactStoreDataToFS(impactStore);
if (data != null) { ... } else { return compelted; }   // compelted = false
```

ถ้า `mapData...` คืน `null` (แปลงวันที่ไม่ได้ · ฟิลด์หาย) → **ออกจากลูปทันที คืน `false` → rollback ทั้ง transaction**

> ⚠️ **แต่ไฟล์ที่เขียนไปแล้วบางส่วนไม่ถูกลบ** — `writer` ยังเปิดค้าง และโค้ดลบไฟล์
> อยู่ใน `if (!fileName.isEmpty())` ที่ **fileName ถูกตั้งเป็น `""` ไปก่อนหน้าแล้ว** (ดูหัวข้อ 12 · L2)

### บันทึกการส่ง 2 แถวต่อบรรทัด

```java
insertComfirmReceiveDataStoreI(DATA_NAME_I, fileName, STORECODE_I, งวด, null)
insertComfirmReceiveDataStoreN(DATA_NAME_N, fileName, STORECODE_N, STORECODE_I, งวด, null)
```

**ยิงทีละแถว ในลูปเดียวกับการเขียนไฟล์** — ไฟล์ 5,000 บรรทัด = **10,000 INSERT ทีละคำสั่ง**

---

## 8. ขั้นที่ ⑦ — ส่ง SFTP (และสิ่งที่ระบบใหม่เปลี่ยน)

```java
if (FtpUtils.uploadSFTPFile(ftpEaiServerIpSta, ftpEaiUserIdSta, ftpEaiPasswordSta, 22, ...)) {
    FileUtils.moveBackupFile(out, backupOut);      // move ไป backup
} else {
    paramTransactionStatus.rollbackToSavepoint(savepoint);
    return false;
}
```

| | ค่าใน `config.xml` |
|---|---|
| path ชั่วคราว | `/appshare/SPS/FGI/interface_data/out/` |
| **ปลายทาง SFTP** | `/staha/staapp/source/SS/FRBC0001/src/` |
| backup | `/appshare/SPS/FGI/interface_data/backup_out/STA/` |

### 🔴 SFTP อยู่ **ใน** DB transaction — dual-write ที่อันตราย

การส่ง SFTP ถูกเรียก **ภายใน** `doInTransaction()` แล้วถ้าล้มก็ `rollbackToSavepoint`

**ปัญหาคือ:**

| เหตุการณ์ | ผล |
|---|---|
| SFTP สำเร็จ แต่ commit ล้ม | ❌ **STA ได้ไฟล์แล้ว แต่ DB บอกว่ายังไม่ส่ง** → รอบหน้าส่งซ้ำ |
| SFTP ล้ม แต่ rollback ไม่สมบูรณ์ | ❌ DB บอกว่าส่งแล้ว แต่ STA ไม่ได้อะไร |
| SFTP ช้า | ❌ **transaction เปิดค้างตลอดเวลาที่อัปโหลด** — ล็อกแถวไว้นาน |

> ✅ **ระบบใหม่แยกสองอย่างนี้ออกจากกันแล้ว** (transactional outbox)
> ```
> ── transaction ──                          ── นอก transaction ──
>    9 mutation ซิงก์สถานะ                       publish ไป RabbitMQ
>    insert outbox (status=READY)                รอ publisher confirm
> ── commit ──                                   update outbox → CONFIRMED
> ```
> **commit แล้วข้อมูลจะไม่หายแม้ broker ล่ม** · ส่งซ้ำได้เพราะ STA กันซ้ำด้วย `message_id`

### สิ่งที่เปลี่ยนในระบบใหม่

| | ระบบเดิม | ระบบใหม่ (มติ 2026-08-24 · 2026-09-08) |
|---|---|---|
| ช่องทาง | ไฟล์ `FRBC0001` + **SFTP** | **RabbitMQ** exchange `sgi.interface` · routing `sta.compensation.result` |
| รูปแบบ | text `windows-874` · `\|` คั่น | **JSON UTF-8** · `dataName = sgi_impact_store` |
| เนื้อข้อมูล | 14 ฟิลด์ | **14 ฟิลด์เท่าเดิม** (ฟิลด์ 3/5/6 ยังเป็น พ.ศ.) |
| ยืนยันการส่ง | ไม่มี | **publisher confirm** → `outbox_status = 'CONFIRMED'` |
| ACK จาก STA | ไม่มี | **ยังไม่มี** — มติข้อ 2.13 ตัดเส้น `POST /sgi/interface/sta/ack` ออก |
| กันซ้ำ | ไม่มี | `message_id` = `sgi_interface_transactions.id` |

---

## 9. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลงตาราง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| `FGI_IMPACT_STORE_ON_PROCESS` | **`sgi_fgi_impact_processes`** |
| `FGI_IMPACT_STORE_COMPENSATE` | **`sgi_fgi_impact_compensations`** |
| `FGI_IMPACT_STORE_INFO` · `FGI_NEW_STORE_INFO` | **`sgi_document_new_stores`** + snapshot ในเอกสาร |
| `FGI_CONFIRM_RECEIVE_DATA` | **`sgi_interface_transactions`** (transactional outbox) |
| ไฟล์ `FRBC0001` + SFTP | **RabbitMQ message** |

### `sgi_interface_transactions` — ค่าที่ Job 6 ต้องใส่

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | `'COMPENSATE_INIT_I'` · `'COMPENSATE_INIT_N'` · `'COMPENSATE_APPROVE_I'` · `'COMPENSATE_APPROVE_N'` |
| `direction` | `'OUT'` |
| `status` | `'READY'` → `'SENT'` → **`'COMPLETED'`** |
| `outbox_status` | `'READY'` → `'PUBLISHED'` → **`'CONFIRMED'`** |
| `impact_process_id` | typed FK ไปรอบชดเชย |
| `business_key` · `period_key` | รหัสร้าน · งวด |
| `correlation_id` | `message_id` ที่ส่งให้ broker |
| `sent_at` | เวลาที่ publish |

> 🔴 **ปลายทางของขาออกคือ `outbox_status = 'CONFIRMED'` + `status = 'COMPLETED'`**
> **ไม่ใช่ `SENT`** — `SENT` แปลว่ายิงแล้วแต่ยังไม่ได้ confirm
> ถ้าหยุดที่ `SENT` แถวจะค้าง แล้ว **Job 10 (watchdog) จะเตือนไม่หยุด**

### ✅ A — ปิดแล้ว 2026-09-13 · เพิ่มตาราง `sgi_fgi_new_store_compensations`

> 🔴 **เอกสารฉบับนี้เคยเขียนผิด** ว่า "ระบบเดิมมี `compensate_i_id` เป็นตัวเชื่อม"
> ตาราง `FGI_NEW_STORE_COMPENSATE` **ไม่มีคอลัมน์นั้น** (ดู `output/legacy-oracle/schema.sql:488`)
> ของจริงผูกด้วย **`IMPACT_STORE_ID`** (ชี้กลับไปแถวคู่ร้าน) + `(IMPACT_PROCESS_ID, COMPENSATE_SEQ, COMPENSATE_SEQ_NO)`

**สิ่งที่พบเพิ่มตอนลงมือทำ** — ฝั่ง `N` ต้องเก็บ **รายงวด** ไม่ใช่รายคู่ร้าน:

```sql
-- ExportJdbc.insertFgiNewStoreCompensate — ใส่งวดปัจจุบันของรอบทุกครั้งที่รัน
select ..., op.last_compensate_month, op.last_compensate_year, fis.impact_store_id, ...
  from fgi_impact_store_on_process op
 inner join fgi_impact_store fis on fis.storecode_i = op.storecode_i
```

| หลักฐาน | ตัวเลขจริง |
|---|---|
| `FGI_NEW_STORE_COMPENSATE_BK_20250515` | **23,628 แถว** |
| รอบชดเชย (`FGI_IMPACT_STORE_ON_PROCESS_BK`) | 7,548 รอบ → **3.13 แถว N ต่อรอบ** |
| ค่าชดเชยฝั่ง I (`FGI_IMPACT_STORE_COMPENSATE_BK`) | 20,674 → 2.74 งวดต่อรอบ · **N/I = 1.14** |

`sgi_fgi_impact_stores` เป็น **1 แถวต่อคู่ร้าน ไม่มีมิติงวด** จึงเก็บแทนไม่ได้ —
งวด ต.ค. จะทับ ก.ย. แล้วตรวจย้อนหลังไม่ได้ว่างวดไหนจ่ายเท่าไร
และกติกา **"%ชดเชยของร้านใหม่ทุกแถวรวมกันต้องได้ 100%"** ต้องตรวจต่อ **1 งวด** ไม่ใช่ต่อคู่ร้าน

> ✅ **มติผู้ใช้ 2026-09-13** — เพิ่มตาราง `sgi_fgi_new_store_compensations`
> เป็นลูกของ `sgi_fgi_impact_compensations` (`ON DELETE CASCADE`) · ยอดตารางในโครง **20 → 21**
> พิสูจน์กับ PostgreSQL 16 จริงแล้ว: คู่ร้านเดิมได้ 2 แถวคนละงวดโดยไม่ทับกัน · %รวมต่องวด = 100 · CASCADE ทำงาน

### 🔴 A (เดิม) — `sgi_fgi_impact_compensations` ยังไม่ได้ออกแบบให้ครบ

ตารางนี้ต้องรองรับ **9 mutation** ของหัวข้อ 6 ซึ่งเป็นตรรกะที่ซับซ้อนที่สุดในระบบเดิม
แต่ `DECISIONS` ข้อ **2.4 (DP-6)** ยังไม่ได้เคาะว่าจะออกแบบใหม่ หรือลอกแพตเทิร์น `statement_summary`

| สิ่งที่ต้องมี | สถานะ |
|---|---|
| `compensate_status` โดเมน 6 ค่า (`I C A N S Z`) | ✅ มี `CHECK` แล้ว (ข้อ 2.7 ปิดแล้ว) |
| `compensate_seq` / `compensate_seq_no` (รอบ / ครั้งที่ในรอบ) | ✅ อยู่บน `sgi_fgi_impact_processes` (gap F8 · รับเข้าโครง 2026-08-21) |
| การผูกฝั่ง `I` กับฝั่ง `N` เป็นคู่ | ✅ **ปิดแล้ว 2026-09-13** — ดูด้านล่าง |
| `STMT_MONTH` / `STMT_YEAR` (งวด Statement · ฟิลด์ 6) | ✅ **ปิดแล้ว 2026-09-13** — คอลัมน์ `stmt_month`/`stmt_year` มีอยู่แล้วใน DDL และ **ฝั่งอนุมัติเป็นคนเติม** |

### ✅ B — ปิดแล้ว 2026-09-13 · ค่าคงที่ 3 ตัวย้ายไป `mas_param`

| `param_name` | ค่า | เดิมอยู่ที่ |
|---|---|---|
| `SGI_STA_INIT_START_DAY` | `7` | `dateStartInitToSTA` |
| `SGI_STA_NUM_WAIT_PAY` | `3` | `numWaitPay` |
| `SGI_QSSI_CATEGORIES` | `8,9,12,1,10,16` | `categoryQssi` |

seed ไว้ใน `output/sql/sgi_seed_data.sql` แล้ว · โค้ดอ่านจาก `mas_param` เป็นหลัก
มี fallback จาก env เฉพาะตอนแถวยังไม่มี (dev/CI) และ **ขึ้น log warn ทุกครั้งที่ต้อง fallback**

### 🔴 B (เดิม) — `numWaitPay = 3` ไม่มีที่เก็บเป็น config

ค่านี้อ่านจาก `ApplicationResources.properties` และถูกต่อเข้า SQL ตรง ๆ
ระบบใหม่ตกลงว่าค่าคงที่ทางธุรกิจอยู่ที่ **`mas_param` / `common_code` ของระบบเดิม**

> 🔴 **ต้องระบุว่า `dateStartInitToSTA` (7) · `numWaitPay` (3) · `categoryQssi` (6 หมวด) เก็บที่ไหน**
> ทั้งสามเป็นค่าที่ธุรกิจอาจขอเปลี่ยน — **ห้าม hardcode ในโค้ด**

---

## 10. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `runDate` · `periodKey` | วันที่อ้างอิง + งวดที่คำนวณได้ | ตามรอยว่ารอบนั้นตีความงวดเป็นอะไร |
| `gateCreateData` | Gate 1 ผ่านไหม (`true`/`false`) | วันที่ 1–6 ต้องเป็น `false` เสมอ |
| `gateQssiComplete` | Gate 2 ผ่านไหม | 🔴 **`false` ติดต่อกันหลังวันที่ 7 ต้อง alert** — คะแนน QSSI ไม่มา |
| `mutation1Count` … `mutation9Count` | จำนวนแถวที่แต่ละคำสั่งแตะ | 🔴 **ทั้ง 9 ตัวต้องบันทึกแยกกัน** — ขั้นไหนได้ 0 ผิดปกติจะเห็นทันที |
| `exportRowCount` | แถวที่ส่งออก | ต้องเท่ากับจำนวนบรรทัดใน payload |
| `outboxInitCount` · `outboxApproveCount` | แถว outbox แยกตามสาย | สัดส่วนผิดปกติเทียบงวดก่อนไหม |
| `publishedCount` · `confirmedCount` | ยิงไป broker · ได้ confirm | 🔴 **`published − confirmed > 0` ต้อง alert** |
| `retryPendingCount` | outbox ที่ยัง `READY`/`FAILED_RETRY` | 🔴 **> 0 ข้ามวันต้อง alert** |
| `durationMs` | เวลาที่ใช้ | จับ transaction ที่เปิดค้างนาน |

**สมการที่ต้องเป็นจริงเสมอ:**

```
exportRowCount × 2  =  outboxInitCount + outboxApproveCount     (ทุกแถวส่งเป็นคู่ I + N)
publishedCount      =  confirmedCount + retryPendingCount
```

- 🔴 **alert เมื่อ `confirmedCount < publishedCount` ข้ามรอบ** — ข้อความค้างที่ broker
- 🔴 **alert เมื่อ Gate 2 ไม่ผ่านติดกัน 3 วันหลังวันที่ 7** — คะแนน QSSI ไม่เข้าระบบ รอบชดเชยจะไม่ถูกเปิด

---

## 11. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — argument และ gate

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | ไม่ส่ง argument | ใช้วันนี้ตามเวลา **`Asia/Bangkok`** |
| 1.2 | ส่ง `20260615` | งวด = `2026-06` · QSSI ตรวจงวด **พฤษภาคม** · Gate 1 ผ่าน |
| 1.3 | ส่ง `20260603` (วันที่ 3) | **Gate 1 ไม่ผ่าน** — ซิงก์สถานะอย่างเดียว ไม่สร้างข้อมูลใหม่ |
| 1.4 | ส่ง `20260607` (วันที่ 7 พอดี) | **Gate 1 ผ่าน** (`>=` ไม่ใช่ `>`) |
| 1.5 | argument รูปแบบผิด (`2026-06-15`) | ❌ **job ล้มเหลว · exit ≠ 0** — ห้ามล้มเงียบแบบเดิม |
| 1.6 | argument เป็นวันที่ไม่มีจริง (`20260231`) | ปฏิเสธ |
| 1.7 | argument เป็นปี **พ.ศ.** (`25690615`) | ปฏิเสธพร้อมบอกว่าน่าจะเป็น พ.ศ. |
| 1.8 | ไม่มีคะแนน QSSI งวดนั้น | **สาย INIT ถูกข้าม · สาย APPROVE ยังส่ง** · job สำเร็จ |
| 1.9 | ไม่มี QSSI **และ** ไม่มีแถวส่งออกเลย | job **สำเร็จ** · ไม่สร้างข้อความ |

### กลุ่มที่ 2 — การซิงก์สถานะ (9 mutation)

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | Gate 1 ไม่ผ่าน | **รันเฉพาะ mutation 1–2** · 3–9 ต้องไม่ทำงาน |
| 2.2 | Gate 1 ผ่าน | รันครบทั้ง 9 · **บันทึกจำนวนแถวแยกทุกขั้น** |
| 2.3 | รอบที่ STA ตอบกลับครบ | mutation 1 ปิดรอบเป็น `N` |
| 2.4 | รอบที่ส่งแล้วแต่ยังไม่ถึงกำหนดจ่าย | mutation 2 เปลี่ยน `Y` → `W` |
| 2.5 | ร้านปิดแล้ว (`close_date <= งวด`) | `compensate_status = 'C'` ไม่ใช่ `'I'` |
| 2.6 | สัญญายกเลิกด้วย `cancel_type` ใน `01,02,03,04,08` | `'C'` |
| 2.7 | สัญญายกเลิกด้วย `cancel_type` อื่น | `'I'` (ไม่เข้าเงื่อนไข) |
| 2.8 | ลำดับการรัน 9 คำสั่งสลับกัน | ❌ **ต้องล้มเหลว** — ลำดับมีความหมาย (ปิดรอบเก่าก่อนเปิดใหม่) |
| 2.9 | mutation ใดล้มกลางทาง | **rollback ทั้ง 9** · สถานะกลับเป็นก่อนรัน |

### กลุ่มที่ 3 — payload และการส่ง

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | ไม่มีแถวส่งออก | job **สำเร็จ** · ไม่สร้าง outbox · ไม่ publish |
| 3.2 | มี 3 คู่ร้านส่งออก | **6 แถว outbox** (คู่ละ 2: ฝั่ง I + ฝั่ง N) |
| 3.3 | ฟิลด์ 3/5/6 (วันที่) | **เป็น พ.ศ.** ตามสัญญา STA |
| 3.4 | ฟิลด์ 5 งวดชดเชย รูปแบบ | `yyMM` **พ.ศ.** เช่น งวด 2026-06 → `6906` |
| 3.5 | `STMT_MONTH`/`STMT_YEAR` เป็น NULL | ฟิลด์ 6 **ว่าง** ไม่ใช่ `null` เป็นตัวอักษร |
| 3.6 | แถวใดแถวหนึ่งประกอบ payload ไม่ได้ | ❌ **ยกเลิกทั้งรอบ · rollback** (คงพฤติกรรมเดิม) · **ต้องไม่เหลือไฟล์/ข้อความค้าง** |
| 3.7 | `compensate_status = 'Z'` | ใน DB คงเป็น `'Z'` · **ใน payload ส่งเป็น `'S'`** |
| 3.8 | สถานะ `I`/`C` | `data_name = COMPENSATE_INIT_I` / `_N` |
| 3.9 | สถานะ `A`/`N`/`S`/`Z` | `data_name = COMPENSATE_APPROVE_I` / `_N` |

### กลุ่มที่ 4 — outbox และ publisher confirm

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | publish สำเร็จ + ได้ confirm | `outbox_status = 'CONFIRMED'` · `status = 'COMPLETED'` |
| 4.2 | publish สำเร็จ แต่**ไม่ได้ confirm** | `outbox_status = 'PUBLISHED'` · **ห้ามเป็น `CONFIRMED`** · ไม่ rollback การซิงก์ |
| 4.3 | broker ล่มตอน publish | `outbox_status` คง `READY`/`FAILED` · **การซิงก์สถานะยัง commit** |
| 4.4 | dispatcher ส่งซ้ำ | **ไม่สร้างแถว outbox ใหม่** (`UNIQUE(data_name, direction, business_key, period_key)`) |
| 4.5 | STA ได้ข้อความซ้ำ | `message_id` เดิม → STA กันซ้ำได้ |
| 4.6 | DB transaction ล้มหลัง publish | 🔴 **ต้องออกแบบไม่ให้เกิด** — publish อยู่นอก transaction เสมอ |
| 4.7 | รัน 2 instance พร้อมกัน | advisory lock → ตัวเดียวทำงาน · **ห้ามส่งข้อความซ้ำ** |
| 4.8 | ส่งเมลไม่สำเร็จ แต่งานสำเร็จ | exit **0** + log ระดับ ERROR |
| 4.9 | งานไม่สำเร็จ แต่ส่งเมลสำเร็จ | exit **ไม่ใช่ 0** |

---

## 12. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **argument คุมสามเรื่องพร้อมกัน** | `yyyyMMdd` ตัวเดียวกำหนด **(1)** งวดที่ซิงก์ **(2)** งวดที่ตรวจ QSSI (เดือนก่อนหน้า) **(3)** Gate 1 (วันของเดือน) · การรันย้อนหลังจึงเปลี่ยนพฤติกรรมทั้งสามอย่าง · เลือก **(ก) แยกเป็น 3 พารามิเตอร์** · **(ข) คงตัวเดียวแต่เขียนสัญญาให้ชัด** | 🔴 **ต้องเคาะ** — กระทบการรันซ่อมย้อนหลังซึ่งเป็นงาน ops ที่ต้องทำจริง |
| 🔴 **ค่าคงที่ธุรกิจ 3 ตัวเก็บที่ไหน** | `dateStartInitToSTA` (7) · `numWaitPay` (3) · `categoryQssi` (8,9,12,1,10,16) อยู่ใน `.properties` ของระบบเดิม · ระบบใหม่ตกลงว่าค่าธุรกิจอยู่ที่ **`mas_param`/`common_code`** | 🔴 **ต้องเคาะ** — ทั้งสามเป็นค่าที่ธุรกิจอาจขอเปลี่ยน **ห้าม hardcode** |
| 🔴 **การผูกคู่ `I` ↔ `N`** | ระบบเดิมใช้ `compensate_i_id` เป็นตัวเชื่อมแถวฝั่งร้านถูกกระทบกับฝั่งร้านเปิดใหม่ · **ตารางใหม่ยังไม่ระบุว่าผูกอย่างไร** | 🔴 **ต้องเคาะ** — ผูกกับ `DECISIONS` ข้อ **2.4 (DP-6)** ที่ยังไม่ปิด |
| 🔴 **`STMT_MONTH` / `STMT_YEAR` (ฟิลด์ 6)** | งวด Statement ที่ STA ใช้ตัดจ่าย — **ยังไม่ระบุว่าเก็บที่คอลัมน์ไหน และใครเป็นคนเติม** | 🔴 **ต้องเคาะ** — ฟิลด์นี้ว่างได้ แต่ต้องรู้ว่าเมื่อไรควรมีค่า |
| 🔴 **`Z` → `S` ตอนส่ง** | เป็นการแปลงที่ **มองไม่เห็นจาก DB** · ต้องเขียนไว้ในสเปกให้ชัดและมีเคสทดสอบ | 🔴 **ยืนยันแล้วในผัง** แต่ต้องบันทึกเหตุผลว่าทำไม |
| **ลำดับ 9 mutation** | ลำดับมีความหมาย (ปิดรอบเก่า → เปิดใหม่ → สร้างค่าชดเชย → snapshot → ปิดธง) | ⏳ **ต้องเขียนเป็นสัญญาที่ทดสอบได้** ไม่ใช่ปล่อยให้คนพอร์ตเดา |
| **ปี พ.ศ. ในฟิลด์ 3/5/6** | เป็นสัญญาของ STA ที่ตกลงไว้แล้ว | ✅ **ยืนยันแล้ว** — แปลงเฉพาะตอนประกอบ payload ห้ามปนเข้า DB/API |
| **โดเมน `compensate_status`** | 6 ค่า `I C A N S Z` | ✅ **ปิดแล้ว** `DECISIONS` ข้อ **2.7** |

---

## 13. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | **ส่ง SFTP อยู่ใน DB transaction** | `getImpactStoreToFS` — `uploadSFTPFile()` ถูกเรียกใน `doInTransaction()` | **transactional outbox** — commit การซิงก์ก่อน แล้ว publish นอก transaction (ผังระบุไว้แล้ว) |
| **L2** | **โค้ดลบไฟล์ที่ทำงานไม่ได้** | 4 จุดเขียน `fileName = ""` แล้วตามด้วย `if (!fileName.isEmpty()) { fileDelete(...) }` — **เงื่อนไขเป็นเท็จเสมอ** ไฟล์ที่เขียนค้างจึงไม่เคยถูกลบ | ใช้ temp file + atomic rename · ล้มแล้วลบ temp ได้จริง |
| **L3** | **argument ผิดรูปแบบล้มเงียบ** | `main()` — `catch` ตั้งแค่ `errorMsg` ไม่ rethrow ไม่กำหนด exit code | validate ก่อนแตะฐาน · **exit ≠ 0 เมื่อ input ผิด** |
| **L4** | **transaction ซ้อนสองชั้น** | `TransactionTemplate.execute()` แล้วข้างในใช้ `createSavepoint()` + `rollbackToSavepoint()` เอง | transaction ชั้นเดียว ปล่อยให้ framework จัดการ (เหมือน Job 2 · L5) |
| **L5** | **insert ทีละแถวในลูปเขียนไฟล์** | `manageDataToFS` — ไฟล์ 5,000 บรรทัด = **10,000 INSERT** | สะสมแล้ว **batch insert** ครั้งเดียว |
| **L6** | **`checkDateToCrateInitToSTA` ซ้ำซ้อน** | ตรวจ `7 ≤ วันที่ ≤ วันสุดท้ายของเดือน` ซึ่งให้ผลเหมือน Gate 1 เสมอ | ตรวจครั้งเดียว |
| **L7** | **`line.separator` ตาม OS** | `FgiConstant.NEW_LINE = System.getProperty("line.separator")` | กำหนดตายตัว (เหมือน Job 4 · L10) |
| **L8** | **credential ของ SFTP ปลายทาง** | `ftpEaiServerIpSta` · `ftpEaiUserIdSta` · `ftpEaiPasswordSta` อ่านจาก config เดิม | ระบบใหม่ใช้ **AMQPS + Secret Manager** (`secret/sgi/mq/sta`) · `DECISIONS` ข้อ 4.6 |
| **L9** | **`return isCompleted && informBean.getErrorMsg().isEmpty()`** | ผลของ job ขึ้นกับว่า **ข้อความ error ว่างหรือไม่** — เปราะมาก ถ้ามีใครไปตั้ง `errorMsg` ด้วยข้อความที่ไม่ใช่ error ก็จะกลายเป็นล้มเหลว | ใช้ **exception + exit code** ไม่ใช่สถานะจากสตริง |
| **L10** | **`finally { return ... }`** | บล็อก `finally` มี `return` — **กลืน exception ทุกตัวที่โยนออกมาก่อนหน้า** | ห้ามใช้ `return` ใน `finally` |

> ⚠️ **L1 + L9 + L10 รวมกันคือความเสี่ยงที่ร้ายที่สุดของ job นี้**
> `finally { return }` กลืน exception → `isCompleted` ตัดสินจากสตริง → SFTP อยู่ใน transaction
> ผลคือ **STA อาจได้ไฟล์ไปแล้วแต่ DB ยัง rollback** หรือกลับกัน
> และเนื่องจากนี่คือ job ที่ทำให้ **เงินออกจริง** ความไม่ตรงกันตรงนี้แปลว่า **จ่ายซ้ำหรือไม่จ่าย**

---

## 14. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 4 (ขอยอดขาย) · Job 5 (รับยอดขาย + ตัดสิน Y/N) | `batchjob/JOB-04-*.md` · `batchjob/JOB-05-*.md` |
| Job 11 (รับสถานะการจ่ายกลับจาก STA) | `LLDD/md/Jobs/LLDD-BE-Job-11-ConsumeStaCompensate.md` |
| Job 10 (watchdog เฝ้า outbox ที่ค้าง) | `LLDD/md/Jobs/LLDD-BE-Job-10-NotifyNoReceiveData.md` |
| สเปกรูปแบบมาตรฐานของ Job 6 | `LLDD/md/Jobs/LLDD-BE-Job-6-ExportImpactStoreToFS.md` |
| สัญญาข้อความ RabbitMQ กับ STA | `STA/ประกันรายได้-ตัวอย่าง-Message-RabbitMQ.md` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| พจนานุกรมข้อมูลรายคอลัมน์ | `LLDD/pdf/LLDD-Database-Dictionary.pdf` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
