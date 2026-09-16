# Job 7 — SyncCompetitorToDocument : ยกข้อมูลคู่แข่งขึ้นเอกสารชดเชย

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 10 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.20 · 2.29 · 2.30 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/ExportCompetitor.java` · `controller/ExportController.java` (`exportCompetitorToBPM` · `manageCompetitorToBPM` · `appendContentCompetitorToBPM` · `checkProcesssError`) · `dao/jdbc/ExportJdbc.java` (`queryCompetitorToBPM` · `getErrorProcess`) · `Constant/FgiConstant.java` · `config.xml` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-sync-competitor-to-document` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-7-SyncCompetitorToDocument` · **Job 3 (ต้นทางข้อมูลคู่แข่ง)** ดู `batchjob/JOB-03-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

ยกข้อมูล **ร้านคู่แข่งงวดล่าสุด** ของแต่ละร้าน SP ขึ้นไปติดกับ **เอกสารชดเชย** ที่กำลังรอพิจารณา
เพื่อให้ผู้พิจารณาเห็นว่ามีคู่แข่งเจ้าไหนอยู่ใกล้บ้าง ตอนตัดสินว่าจะชดเชยเท่าไร

```
Job 3 นำเข้าคู่แข่งรายงวด          Job 7 ยกขึ้นเอกสาร            คนพิจารณาเห็นบนหน้าจอ
sgi_fgi_impact_competitors  ──▶  sgi_document_competitors  ──▶  การ์ด "ร้านคู่แข่ง"
```

**ระบบเดิมทำโดยเขียนไฟล์ `BPM06003O` แล้ว SFTP ไป BPM (K2)**
**ระบบใหม่เขียนลงตารางตรง ๆ** เพราะ SGI กับ K2 รวมเป็นระบบเดียวแล้ว (มติสถาปัตยกรรม)

### เทียบกับ job อื่น

| | Job 3 | Job 6 | **Job 7 (ฉบับนี้)** |
|---|---|---|---|
| ทิศทาง | นำเข้าจาก ALLMAP | ส่งออกไป STA (ระบบภายนอก) | **ภายในระบบเดียวกัน** |
| ปลายทางเดิม | ตาราง | ไฟล์ + SFTP → STA | ไฟล์ + SFTP → **BPM (K2)** |
| ปลายทางใหม่ | ตาราง | **RabbitMQ** | **เขียน DB ตรง** |
| มี ACK ให้รอไหม | — | มี publisher confirm | **ไม่มี** — เขียน DB จบในตัว |

> 📌 **นี่คือเหตุผลที่ `direction = 'INTERNAL'`** ใน `sgi_interface_transactions`
> ไม่ใช่ `OUT` เพราะไม่ได้ออกไปไหน · และจบที่ `status = 'COMPLETED'` ทันทีเพราะไม่มีอะไรให้รอตอบกลับ

---

## 2. ทำไมต้องมี job นี้

ข้อมูลคู่แข่งอยู่ที่ **ระดับร้าน + งวด** (`sgi_fgi_impact_competitors`)
แต่การพิจารณาชดเชยเกิดที่ **ระดับเอกสาร** (`sgi_compensation_documents`)

**สองระดับนี้ผูกกันไม่ได้โดยตรง** เพราะ:
- ร้านหนึ่งร้านมีข้อมูลคู่แข่งหลายงวด แต่เอกสารหนึ่งใบสนใจแค่งวดที่กำลังชดเชย
- ข้อมูลคู่แข่งอาจถูกนำเข้าก่อนที่เอกสารจะถูกสร้าง

Job 7 จึงเป็นตัว **จับคู่และคัดลอก** — เลือกงวดที่ถูกต้องแล้วยกขึ้นเอกสาร

**สายข้อมูลเต็ม:** `Job 3` (นำเข้าคู่แข่ง) → `Job 8` (สร้างเอกสาร) → **`Job 7` (ยกคู่แข่งขึ้นเอกสาร)** → หน้าจอ `k2-document.html`

> ⚠️ **ลำดับเลข job ไม่ใช่ลำดับการทำงาน** — Job 7 ต้องรันหลัง Job 8 (ที่สร้างเอกสาร)
> ถึงจะมี `doc_no` ให้ผูก · ระบบเดิมเลี่ยงปัญหานี้ด้วยการรันทุกวัน แล้วรอบไหนยังไม่มีเอกสารก็ข้ามไป

---

## 3. ภาพรวมการทำงาน

```
① query คู่แข่งที่ควรส่ง — เงื่อนไข 6 ชั้น (ดูหัวข้อ 4)
      ▼
② คัดออกอีกชั้น: รอบที่ข้อมูลผู้อนุมัติไม่ครบ (getErrorProcess)
      │  ไม่เหลือแถว ──▶ จบ (ถือว่าสำเร็จ)
      ▼
③ transaction เดียว:
     เขียนไฟล์ BPM06003O ทีละบรรทัด  +  สะสม ConfirmReceiveData
     insert FGI_CONFIRM_RECEIVE_DATA ทั้งชุด
     SFTP ไป BPM
      ▼
④ ส่งเมลแจ้งผล
```

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — job นี้ไม่มี argument และไม่มีแนวคิดเรื่องงวด

```java
public static void main(String[] args) {
    exportController.exportCompetitorToBPM();     // args ถูกทิ้งทั้งหมด
}
```

งวดที่จะส่งถูกตัดสิน**จากข้อมูลในฐาน** ล้วน ๆ — `dense_rank()` หา "งวดคู่แข่งล่าสุดต่อร้าน"
แล้วเทียบกับกรอบงวดที่รอบชดเชยนั้นครอบคลุม

> ⚠️ **รันย้อนหลังไม่ได้** — ไม่มีทางบอก job ว่า "ขอส่งงวดพฤษภาคม" · ระบบใหม่ควรรองรับ (ดูหัวข้อ 10)

---

## 4. ขั้นที่ ① — เงื่อนไข 6 ชั้นที่คัดว่าแถวไหนควรส่ง

```sql
select * from (
    select fic.impact_competitor_id, fic.storecode_i, fic.compet_id, fic.name_th, fic.name,
           fic.branch_th, fic.zone_code, fic.subzone_code, fic.open_date, fic.close_date,
           op.last_compensate_month as month, op.last_compensate_year as year,
           dense_rank() over (partition by fic.storecode_i
                              order by fic.year desc, fic.month desc) as rank_period,
           'system' as create_by, fic.create_date, op.impact_process_id
      from fgi_impact_competitor fic
      inner join fgi_impact_store_on_process op
              on op.flag_action in ('Y','W')                       -- ชั้น 2
             and op.datasource = 'ALM'                             -- ชั้น 3
             and op.storecode_i = fic.storecode_i
             and to_date(fic.year||fic.month,'YYYYMM')
                 between to_date(op.start_compensate_year||op.start_compensate_month,'YYYYMM')
                     and to_date(op.last_compensate_year||op.last_compensate_month,'YYYYMM')   -- ชั้น 4
      inner join fgi_impact_store_compensate fisc
              on fisc.impact_process_id = op.impact_process_id
             and fisc.compensate_month = op.last_compensate_month
             and fisc.compensate_year  = op.last_compensate_year
             and fisc.compensate_status = 'I'                      -- ชั้น 5
             and fisc.compensate_forecast is not null              -- ชั้น 5
) a
where a.rank_period = 1                                            -- ชั้น 1
  and not exists ( ... fgi_confirm_receive_data ที่ส่งไปแล้ว ... )  -- ชั้น 6
```

| ชั้น | เงื่อนไข | ทำไม |
|---|---|---|
| **1** | `rank_period = 1` — **งวดคู่แข่งล่าสุดต่อร้าน** | ร้านหนึ่งร้านส่งได้งวดเดียว — งวดใหม่สุดที่มี |
| **2** | รอบชดเชย `flag_action IN ('Y','W')` | เฉพาะรอบที่**ยัง active** |
| **3** | `datasource = 'ALM'` | เฉพาะรอบที่มาจาก ALLMAP · **ไม่รวม STA/PRO/REA** |
| **4** | งวดของคู่แข่งอยู่ใน **กรอบ `start_compensate` … `last_compensate`** ของรอบนั้น | คู่แข่งที่เปิดนอกช่วงชดเชยไม่เกี่ยว |
| **5** | ค่าชดเชย `compensate_status = 'I'` **และ** `compensate_forecast is not null` | เฉพาะรอบที่**คำนวณค่าชดเชยเบื้องต้นแล้ว** และยังไม่ถูกอนุมัติ |
| **6** | ยังไม่เคยส่งงวดนี้ (`NOT EXISTS` ใน `FGI_CONFIRM_RECEIVE_DATA`) | กันส่งซ้ำ |

> 🔴 **ชั้น 3 (`datasource = 'ALM'`) เป็นข้อจำกัดเดียวกับที่เจอใน Job 4**
> รอบที่มาจาก `STA` · `PRO` · `REA` **จะไม่ได้ข้อมูลคู่แข่งขึ้นเอกสารเลย**
> ผู้พิจารณาจะเห็นการ์ดคู่แข่งว่างสำหรับเคสเหล่านั้น — ต้องเคาะว่าตั้งใจหรือไม่ (ดูหัวข้อ 10)

### 🔴 `dense_rank` เรียงตามงวด แต่ไม่ตัดสินกรณีเสมอ

```sql
dense_rank() over (partition by fic.storecode_i order by fic.year desc, fic.month desc)
```

`dense_rank` (ไม่ใช่ `row_number`) แปลว่า **ถ้ามีหลายแถวในงวดเดียวกัน จะได้ `rank = 1` ทั้งหมด**

> ✅ **นี่คือสิ่งที่ถูกต้องสำหรับ job นี้** — ร้านหนึ่งร้านมีคู่แข่งหลายสาขาในงวดเดียวกันได้จริง
> (พิสูจน์ในเอกสาร Job 3: ร้าน `07109` มีแฟมิลี่มาร์ท 80 สาขา) · **ต้องส่งครบทุกสาขา**
> ต่างจาก Job 4 ที่ใช้ `dense_rank ... = 1` เพื่อเลือก **แถวเดียว** ต่อร้าน

---

## 5. ขั้นที่ ② — คัดรอบที่ข้อมูลผู้อนุมัติไม่ครบออก

```java
List<Map> competitorList  = exportService.queryCompetitorToBPM();
List<String> errorProcessList = exportService.getErrorProcess();
competitorList = checkProcesssError(competitorList, errorProcessList);
```

`getErrorProcess()` หา `impact_process_id` ที่ **ข้อมูลผู้อนุมัติใน `FGI_IMPACT_STORE_INFO` ไม่ครบ**:

```sql
select op.impact_process_id
  from fgi_impact_store_on_process op
  inner join fgi_impact_store_info fisi on fisi.impact_process_id = op.impact_process_id
 where op.flag_action in ('Y','W')
   and 'NuLL' in ( nvl(dv_emp_id,'NuLL'), nvl(dv_fname_th,'NuLL'), ...,
                   nvl(gm_emp_id,'NuLL'), ..., nvl(avp_emp_id,'NuLL'), ... )
```

**เทคนิค `'NuLL' in (nvl(col,'NuLL'), ...)`** = *"มีคอลัมน์ไหนเป็น NULL บ้างไหม"*
ถ้ามีแม้แต่คอลัมน์เดียว → รอบนั้นถูกคัดออก

| กลุ่มข้อมูลที่ตรวจ | คอลัมน์ |
|---|---|
| **DV** (ผู้จัดการเขต) | `dv_emp_id` · `dv_fname_th` · `dv_lname_th` · `dv_fname_en` · `dv_lname_en` · `dv_email` |
| **GM** | `gm_emp_id` · `gm_fname_th` · `gm_lname_th` · `gm_fname_en` · `gm_lname_en` · `gm_email` |
| **AVP** | `avp_emp_id` · … |

> 📌 **นี่คือ "Gen Flow Gate" รุ่นแรก** — ระบบเดิมกันไม่ให้ข้อมูลไหลไป BPM ถ้าไม่รู้ว่าใครจะอนุมัติ
> ในระบบใหม่ gate แบบเดียวกันย้ายไปอยู่ที่ **Job 8b** (ตอนเปิด workflow) และใช้ `opt_dv_user_id`

> 🔴 **แต่ Job 7 ของระบบใหม่ยังต้องมี gate นี้ไหม?**
> ถ้า Job 8 สร้างเอกสารได้แล้ว แปลว่าผ่าน gate มาแล้วหรือยัง — **ต้องเคาะ** (ดูหัวข้อ 10)

### ไม่มีแถวเหลือ = สำเร็จ

```java
if (competitorList.size() == 0) {
    informBean.setNote("No Data Found");
    informBean.setStatus(JOB_STATUS_SUCCESS);
    return;                                  // finally ยังทำงาน → ส่งเมล
}
```

**เป็นพฤติกรรมที่ตั้งใจ** — วันที่ไม่มีเอกสารใหม่ก็ไม่มีอะไรต้องส่ง

---

## 6. ขั้นที่ ③ — ไฟล์ 14 ฟิลด์และการส่ง

### รูปแบบไฟล์ `BPM06003O_yyyyMMddHHmm.txt`

| # | ฟิลด์ | รูปแบบ |
|---|---|---|
| 1 | `IMPACT_COMPETITOR_ID` | 🔴 **PK ของแถวต้นทาง** — ระบบใหม่ไม่มีที่เก็บ (ดูหัวข้อ 8) |
| 2 | `STORECODE_I` | รหัสร้าน SP |
| 3 | `COMPET_ID` | **รหัสสาขาคู่แข่ง** (ดูเอกสาร Job 3 · ✅ B) |
| 4 | `NAME_TH` | ชื่อแบรนด์ไทย |
| 5 | `NAME` | ชื่อแบรนด์อังกฤษ |
| 6 | `BRANCH_TH` | ชื่อสาขาคู่แข่ง |
| 7 | `ZONE_CODE` | โซน |
| 8 | `SUBZONE_CODE` | โซนย่อย |
| 9 | `OPEN_DATE` | **`dd/MM/yyyy` ค.ศ.** (ว่างได้) |
| 10 | `CLOSE_DATE` | **`dd/MM/yyyy` ค.ศ.** (ว่างได้) |
| 11 | `MONTH` | **เติมศูนย์หน้าเป็น 2 หลัก** (`padLeft(…, 2, "0")`) |
| 12 | `YEAR` | ปี |
| 13 | `CREATE_BY` | ค่าคงที่ **`'system'`** (hardcode ใน SQL) |
| 14 | `CREATE_DATE` | `dd/MM/yyyy HH:mm:ss` |

- คั่นด้วย **`|`** · ขึ้นบรรทัดด้วย `System.getProperty("line.separator")`
- **encoding `UTF-8`** (`FILE_ENCODING_BPM`)

> ✅ **ต่างจากไฟล์ STA อย่างชัดเจน** — ไฟล์นี้เป็น **UTF-8** และ **วันที่เป็น ค.ศ.**
> (`Locale.US` ทั้งต้นทางและปลายทางในการแปลง) · ไม่ใช่ `windows-874` + พ.ศ. แบบ `FRBC0001` ของ Job 6
> **เพราะ BPM เป็นระบบภายในองค์กรเดียวกัน ส่วน STA เป็นระบบภายนอกที่มีสัญญาเก่า**

| | ค่าใน `config.xml` (`fgiExportCompetitor`) |
|---|---|
| path ชั่วคราว | `/appshare/SPS/FGI/interface_data/out/` |
| ปลายทาง SFTP | `BPM/FGI/Inbound/competition/` |
| backup | `/appshare/SPS/FGI/interface_data/backup_out/BPM/` |

### 🔴 ผลของการส่ง SFTP **ถูกทิ้ง**

```java
FtpUtils.uploadSFTPFile(ftpEaiServerIpBpm, ftpEaiUserIdBpm, ftpEaiPasswordBpm, 22, null, 0,
                        ftpSourcePath, ftpDestinationPath, ftpFileNameArray);//////////
```

**ไม่มี `if` ครอบ ไม่มีการรับค่ากลับ** — เทียบกับ Job 6 ที่เขียน `if (FtpUtils.uploadSFTPFile(...)) { ... } else { rollback }`

| ถ้าอัปโหลดล้มเหลว | ผล |
|---|---|
| `FGI_CONFIRM_RECEIVE_DATA` | ✅ commit ไปแล้ว = "ส่งแล้ว" |
| BPM ได้รับไฟล์ | ❌ ไม่ได้รับ |
| รอบหน้าจะส่งซ้ำไหม | ❌ **ไม่** — ชั้นที่ 6 (`NOT EXISTS`) จะกันไว้ |

→ **ข้อมูลคู่แข่งหายถาวรจากเอกสาร** และไม่มีใครรู้ จนกว่าผู้พิจารณาจะเปิดเอกสารแล้วเห็นการ์ดว่าง

> 🔴 **นี่คือความเสี่ยงที่ร้ายที่สุดของ job นี้** และเป็นคนละแบบกับ Job 6
> Job 6 อย่างน้อยยัง rollback เมื่ออัปโหลดล้ม · **Job 7 ไม่รู้ด้วยซ้ำว่าล้ม**

---

## 7. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| ไฟล์ `BPM06003O` + SFTP ไป BPM | **`INSERT`/`UPDATE` ลง `sgi_document_competitors` ตรง ๆ** |
| `FGI_CONFIRM_RECEIVE_DATA` | `sgi_interface_transactions` (`direction = 'INTERNAL'`) |
| `FGI_IMPACT_COMPETITOR` | `sgi_fgi_impact_competitors` |
| ผูกด้วย `STORECODE_I` + งวด | ผูกด้วย **`doc_no`** ที่หาจาก `impact_process_id` |

### ตารางปลายทาง

```sql
CREATE TABLE sgi_document_competitors (
    id BIGSERIAL PRIMARY KEY,
    doc_no VARCHAR(10) NOT NULL REFERENCES sgi_compensation_documents(doc_no) ON DELETE CASCADE,
    competitor_store_code VARCHAR(50),                                  -- รหัสสาขาจาก ALLMAP
    brand_code VARCHAR(30) REFERENCES sgi_competitors(competitor_code), -- รหัสแบรนด์ 01-11
    name_th VARCHAR(200), name_en VARCHAR(200), branch_th VARCHAR(200),
    zone_code VARCHAR(10), subzone_code VARCHAR(10),
    opened_date DATE, closed_date DATE, impact_date DATE,
    detail TEXT, remark TEXT, source_system VARCHAR(30) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doc_competitor UNIQUE (doc_no, competitor_store_code)
);
```

> 🔧 **DDL นี้แก้เมื่อ 2026-09-09 พร้อมกับ `sgi_fgi_impact_competitors`** — เดิมมีคอลัมน์เดียว
> `competitor_code` ที่ FK ไป master แบรนด์ ซึ่งทำให้เอกสารหนึ่งใบเก็บได้แค่ 1 สาขาต่อแบรนด์
> (ดู `DECISIONS` ข้อ 2.21 และเอกสาร Job 3 หัวข้อ 7)

### การแปลงคอลัมน์

| ระบบเดิม (ฟิลด์ในไฟล์) | ระบบใหม่ |
|---|---|
| `IMPACT_COMPETITOR_ID` (ฟิลด์ 1) | 🔴 **ไม่มีที่เก็บ** (ดู 🔴 B) |
| `STORECODE_I` (ฟิลด์ 2) | ผ่าน `doc_no` → เอกสาร → `impact_process_id` |
| `COMPET_ID` (ฟิลด์ 3) | **`competitor_store_code`** |
| — (map จากชื่อ) | **`brand_code`** |
| `NAME_TH` · `NAME` · `BRANCH_TH` (4–6) | `name_th` · `name_en` · `branch_th` |
| `ZONE_CODE` · `SUBZONE_CODE` (7–8) | `zone_code` · `subzone_code` |
| `OPEN_DATE` · `CLOSE_DATE` (9–10) | `opened_date` · `closed_date` |
| `MONTH` · `YEAR` (11–12) | ไม่เก็บ — งวดอยู่ที่เอกสาร |
| `CREATE_BY` = `'system'` (13) | **`source_system = 'ALLMAP'`** (ค่า canonical · เลือกแล้ว 2026-09-12) |
| `CREATE_DATE` (14) | `updated_at` |

### 🔴 A — ต้องมี `doc_no` ก่อน แต่ Job 8 เป็นคนสร้าง

`doc_no` เป็น **`NOT NULL` + FK** → ถ้าเอกสารยังไม่ถูกสร้าง Job 7 ทำอะไรไม่ได้เลย

ผังระบุทางออกไว้แล้ว: **decision node `มี sgi_compensation_documents ของ impact_process_id แล้ว?`**
ถ้าไม่มี → `คงสถานะรอ sync / log pending` แล้วไป record ถัดไป (`noKind: 'mark'`)

> ⚠️ **แต่ยังไม่มีคอลัมน์ไหนเก็บ "สถานะรอ sync"** — ผังบอกว่า "คงสถานะ" แต่ไม่ได้บอกว่าสถานะอยู่ที่ไหน
> ระบบเดิมไม่มีปัญหานี้เพราะผูกด้วย `STORECODE_I` ตรง ๆ ไม่ต้องรอเอกสาร (ดูหัวข้อ 10)

### 🔴 B — `IMPACT_COMPETITOR_ID` (ฟิลด์ 1) หายไป

ระบบเดิมส่ง **PK ของแถวต้นทาง** เป็นฟิลด์แรก และใช้เป็น `transaction_pk` ในตารางกันส่งซ้ำ
ตารางใหม่ไม่มีคอลัมน์ไหนเก็บ "แถวต้นทางคือแถวไหน"

| ใช้ทำอะไรในระบบเดิม | ระบบใหม่ทำอย่างไร |
|---|---|
| กันส่งซ้ำ (`NOT EXISTS` ใน `FGI_CONFIRM_RECEIVE_DATA`) | `UNIQUE (doc_no, competitor_store_code)` ทำหน้าที่แทน ✅ |
| ตามรอยกลับไปหาแถวต้นทาง | ❌ **ทำไม่ได้** — ถ้าข้อมูลบนเอกสารผิด สืบกลับไม่ได้ว่ามาจากแถวไหน |

> 🔴 **ต้องเคาะว่าจะเก็บ `source_row_id` ไว้ไหม** — มีประโยชน์ตอน audit และตอน prune (ดูหัวข้อ 10)

### 🔴 C — การ prune แถวที่ต้นทางไม่มีแล้ว

สเปกระบุให้ **upsert แล้ว prune เฉพาะ `source_system = 'ALLMAP'`** ให้ target ตรงกับ source ปัจจุบัน
โดย**ไม่ลบแถวที่ผู้ใช้คีย์เอง** (`source_system = 'USER'`)

```sql
DELETE FROM sgi_document_competitors dc
 WHERE dc.doc_no = :doc_no
   AND dc.source_system = 'ALLMAP'
   AND NOT EXISTS ( ... แถวต้นทางที่ยังมีอยู่ ... )
```

> ⚠️ **ระบบเดิมไม่มีการ prune เลย** — เขียนไฟล์ทีเดียวจบ ไม่เคยลบอะไรที่ปลายทาง
> **นี่คือพฤติกรรมใหม่** ต้องระบุให้ชัดว่าเมื่อไรถึงควรลบ และมีเคสทดสอบรองรับ

> ✅ **เลือกค่า canonical แล้ว 2026-09-12: `'ALLMAP'`** — แก้ผังใน `job-batch.html` ให้ตรงกับสเปก SQL แล้ว
> `INSERT` · `prune` · skeleton · rerun note · เคสทดสอบ ใช้ค่าเดียวกันทั้งหมด
> ⚠️ **ข้อมูลเก่าที่อาจมีค่า `ALM` ปนอยู่ต้อง migrate ก่อน** ไม่งั้น prune จะไม่แตะแถวเหล่านั้น

#### ✅ ปิดช่องโหว่ 2026-09-14 — เอกสารที่ต้นทางเหลือ **ศูนย์แถว**

`prune` ข้างบนลบได้เฉพาะเอกสารที่รอบนั้นยังมี candidate อย่างน้อย 1 แถว
เอกสารที่คู่แข่งถูกถอดออกจาก ALLMAP **จนหมดทั้งใบ** จะหลุดจาก candidate query
(ซึ่ง join ผ่าน `sgi_fgi_impact_competitors`) แล้ว **ไม่มีใครลบแถวเก่าเลย** —
ผู้พิจารณาเห็นคู่แข่งที่ไม่มีอยู่จริงแล้วค้างบนเอกสารตลอดไป

จึงเพิ่มขั้น `pruneEmptiedDocuments()` ที่ไล่หาเอกสารในขอบเขตเดียวกัน
ซึ่ง **ไม่ปรากฏใน candidate รอบนี้** แต่ยังมีแถว `ALLMAP` ค้างอยู่ แล้วล้างออก

> ⚠️ **เคสนี้อันตรายกว่า prune ปกติ** เพราะ "ไม่มีแถว" แยกไม่ออกระหว่าง
> *คู่แข่งถูกถอดจริง* กับ *ALLMAP ล่ม/ดึงข้อมูลไม่ครบ* จึงกัน 2 ชั้น:
> 1. รอบนั้นต้องมี candidate อย่างน้อย 1 แถว (ถ้า 0 แถวทั้งรอบ job จบไปก่อนถึงขั้นนี้)
> 2. ถ้าจำนวนเอกสารที่จะโดนล้าง **เกิน `SGI_JOB7_EMPTY_PRUNE_MAX_DOCS`** (ค่าเริ่มต้น 50)
>    = ผิดปกติ → log `error` แล้ว **ไม่ลบอะไรเลย**
>
> ✅ พิสูจน์กับ PostgreSQL 16 จริงแล้ว 2026-09-14 — แถว `USER` รอดครบ

### `sgi_interface_transactions` — ค่าที่ Job 7 ต้องใส่

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | **`'IMPACT_COMPETITOR'`** |
| `direction` | **`'INTERNAL'`** — เขียน DB ตรง ไม่ได้ออกไประบบภายนอก |
| `status` | **`'COMPLETED'`** ทันที — ไม่มี ACK ให้รอ |
| `outbox_status` | **ไม่ต้องใส่** (nullable) — ไม่มี broker เกี่ยวข้อง |
| `impact_process_id` · `doc_no` | typed FK |
| `business_key` · `period_key` | รหัสร้าน · งวด |

---

## 8. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `candidateCount` | แถวที่ผ่านเงื่อนไข 6 ชั้น | ถ้า 0 ทุกวันแปลว่า Job 3 หรือ Job 8 ไม่ได้ป้อนงานมา |
| `filteredByApproverCount` | แถวที่ถูกคัดออกเพราะข้อมูลผู้อนุมัติไม่ครบ | 🔴 **> 0 ต่อเนื่องต้อง alert** — เรื่องจะไปตายที่ Job 8b |
| `pendingNoDocumentCount` | แถวที่ยังไม่มีเอกสาร | 🔴 **> 0 ข้ามวันต้อง alert** — ลำดับการรัน job ผิด |
| `insertedCount` · `updatedCount` | แถวที่ upsert | |
| `prunedCount` | แถว `ALLMAP` ที่ถูกลบเพราะต้นทางไม่มีแล้ว | 🔴 **สูงผิดปกติต้อง alert** — อาจลบผิด |
| `prunedEmptyDocCount` · `emptiedDocumentCount` | แถว/เอกสารที่ถูกล้างเพราะต้นทางเหลือศูนย์แถว | 🔴 **สูงผิดปกติ = ALLMAP ล่ม** — มีเพดานกันไว้แล้ว |
| `skippedUserOwnedCount` | แถวที่ไม่ได้เขียนเพราะบนเอกสารเป็นของ `USER` | ไม่ใช่ error แต่ต้องเห็น — เดิมถูกนับรวมเป็น "เขียนสำเร็จ" |
| `userRowsPreserved` | แถว `USER` ที่ยังอยู่ครบ | **ต้องไม่ลดลงเลย** |
| `unmappedBrandCount` | แถวที่ `brand_code` เป็น NULL | ต่อเนื่องจาก Job 3 |
| `durationMs` | เวลาที่ใช้ | |

**สมการที่ต้องเป็นจริงเสมอ:**

```
candidateCount − filteredByApproverCount − pendingNoDocumentCount  =  insertedCount + updatedCount
userRowsPreserved(หลัง) = userRowsPreserved(ก่อน)          -- prune ต้องไม่แตะแถวของผู้ใช้
```

---

## 9. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — การคัดเลือกข้อมูล

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | ร้านมีคู่แข่ง 2 งวด (พ.ค. · มิ.ย.) | ส่งเฉพาะ **มิ.ย.** (งวดล่าสุด) |
| 1.2 | ร้านมีคู่แข่ง **หลายสาขาในงวดเดียวกัน** | **ส่งครบทุกสาขา** (`dense_rank` ให้ rank 1 ทั้งหมด) |
| 1.3 | รอบชดเชย `flag_action = 'N'` (ปิดแล้ว) | **ไม่ส่ง** |
| 1.4 | รอบชดเชย `datasource = 'STA'` | 🔴 ระบบเดิม **ไม่ส่ง** — ต้องเคาะว่าคงพฤติกรรมนี้ไหม |
| 1.5 | งวดคู่แข่ง**นอกกรอบ** `start_compensate` … `last_compensate` | **ไม่ส่ง** |
| 1.6 | `compensate_status ≠ 'I'` (อนุมัติไปแล้ว) | **ไม่ส่ง** |
| 1.7 | `compensate_forecast` เป็น NULL | **ไม่ส่ง** — ยังไม่ได้คำนวณค่าชดเชย |
| 1.8 | เคยส่งงวดนี้ไปแล้ว | **ไม่ส่งซ้ำ** |
| 1.9 | ไม่มีแถวผ่านเงื่อนไขเลย | job **สำเร็จ** · ไม่เขียนอะไร |

### กลุ่มที่ 2 — gate ข้อมูลผู้อนุมัติ

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | ข้อมูล DV/GM/AVP ครบทุกคอลัมน์ | ผ่าน gate |
| 2.2 | `dv_email` เป็น NULL คอลัมน์เดียว | **ถูกคัดออกทั้งรอบ** |
| 2.3 | ข้อมูลผู้อนุมัติไม่ครบต่อเนื่องหลายวัน | 🔴 **ต้อง alert** — ไม่ใช่เงียบแบบเดิม |
| 2.4 | ผ่าน gate แล้วแต่ยัง**ไม่มีเอกสาร** | นับ `pendingNoDocumentCount` · **ห้ามล้มทั้ง job** · รอบหน้าลองใหม่ |

### กลุ่มที่ 3 — การเขียนลงเอกสาร

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | เอกสารยังไม่มีคู่แข่งเลย | insert ครบทุกสาขา · `source_system = 'ALLMAP'` |
| 3.2 | เอกสารมีคู่แข่งสาขานั้นแล้ว | **update ไม่ใช่ insert ซ้ำ** — 🔴 **แก้ 2026-09-14** คีย์จริงคือ `UNIQUE (doc_no, competitor_key)` ไม่ใช่ `competitor_store_code` · `competitor_key` เป็น generated column ที่ fallback เป็น `brand\|zone\|subzone\|ชื่อสาขา` เมื่อไม่มีรหัส จึงรองรับเคส 3.3 ได้ · 🔴 **แก้เพิ่ม 2026-09-14** ชื่อสาขาใช้ `COALESCE(NULLIF(btrim(branch_th),''), name_th, '')` — เดิมเป็น `COALESCE(branch_th, name_th, '')` ซึ่งไม่ตกไป `name_th` เมื่อ `branch_th` เป็น**สตริงว่าง** (ALLMAP ส่ง `''` แทน NULL ได้) ทำให้คู่แข่งคนละร้านได้คีย์เดียวกันแล้วชน UNIQUE · ฝั่ง TS (`competitor-key.ts`) ต้องตรงกันเป๊ะเพราะ Job 7 เอาคีย์ฝั่ง TS ไป prune |
| 3.3 | แถวต้นทางที่ `competitor_store_code` **ว่าง** | แปลงเป็น `NULL` · หลายแถวว่างต้องไม่ชนกันเอง |
| 3.4 | ต้นทางไม่มีสาขานั้นแล้ว | **prune** แถว `ALLMAP` นั้นออก |
| 3.5 | เอกสารมีแถวที่ **ผู้ใช้คีย์เอง** (`USER`) | 🔴 **ห้ามถูก prune เด็ดขาด** |
| 3.6 | `brand_code` map ไม่ได้ | เก็บแถวไว้โดย `brand_code = NULL` · นับ `unmappedBrandCount` |
| 3.7 | รันซ้ำทันที | `insertedCount = 0` · `prunedCount = 0` · ไม่มีอะไรเปลี่ยน |
| 3.8 | ต้นทางของเอกสารเหลือ **ศูนย์แถว** | ล้างแถว `ALLMAP` ของเอกสารนั้นออกทั้งใบ · แถว `USER` อยู่ครบ |
| 3.9 | เอกสารที่ต้นทางว่าง **เกินเพดาน** (ALLMAP ล่ม) | 🔴 **ไม่ลบอะไรเลย** · log `error` ให้คนมาดู |
| 3.10 | upsert ชนแถวที่ผู้ใช้คีย์เอง | ไม่ทับข้อมูล · `upsertedCount` ต้องนับเฉพาะแถวที่เขียนจริง |

### กลุ่มที่ 4 — ความคงทน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | ล้มกลาง upsert | **rollback ทั้ง doc_no นั้น** · ไม่เหลือคู่แข่งครึ่ง ๆ กลาง ๆ |
| 4.2 | ล้มระหว่าง prune | rollback · แถวเดิมยังอยู่ครบ |
| 4.3 | รัน 2 instance พร้อมกัน | advisory lock หรือ `FOR UPDATE` → **ห้าม prune ทับกัน** |
| 4.4 | Job 7 รันก่อน Job 8 ของงวดเดียวกัน | ทุกแถวเข้า `pendingNoDocumentCount` · **job สำเร็จ** · รอบหน้าเก็บงานต่อ |
| 4.5 | ส่งเมลไม่สำเร็จ แต่งานสำเร็จ | exit **0** + log ระดับ ERROR |
| 4.6 | งานไม่สำเร็จ แต่ส่งเมลสำเร็จ | exit **ไม่ใช่ 0** |

---

## 10. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **`datasource = 'ALM'` กันช่องทางอื่นออก** | เงื่อนไขชั้นที่ 3 ทำให้รอบที่มาจาก `STA` · `PRO` · `REA` **ไม่ได้ข้อมูลคู่แข่งขึ้นเอกสารเลย** — ผู้พิจารณาจะเห็นการ์ดว่าง | 🔴 **ยังต้องเคาะ แต่ไม่บล็อกแล้ว** — ทำเป็น config `SGI_JOB7_DATASOURCE` (ค่าตั้งต้น `'ALM'` คงพฤติกรรมเดิม · `''` = ไม่กรอง) และ job **รายงานจำนวนแถวที่ถูกกรองทิ้งทุกรอบ** (`excludedByDatasourceCount`) พร้อม log warn · ผูกกับ `DECISIONS` ข้อ **2.24** |

**📊 ผลกระทบจริงจากฐานข้อมูลเดิม** (ตัวเลขที่ธุรกิจต้องใช้ตัดสิน — ไม่ใช่การคาดเดา)

| ชุดข้อมูล | ALM | STA | สัดส่วน STA |
|---|---|---|---|
| ประวัติ `FGI_IMPACT_STORE_ON_PROCESS_BK_20250515` (7,548 รอบ) | 4,670 | 2,877 | **38.1%** |
| ตารางปัจจุบัน `FGI_IMPACT_STORE_ON_PROCESS` (395 รอบ) | 13 | 382 | **96.7%** |

> 🔴 **สัดส่วน STA โตขึ้นมาก** — ถ้าคงตัวกรองไว้ เอกสารเกือบทั้งหมดในปัจจุบัน
> จะไม่มีข้อมูลคู่แข่งให้ผู้พิจารณาเห็นเลย
| 🔴 **"สถานะรอ sync" เก็บที่ไหน** | ผังบอกว่าถ้ายังไม่มีเอกสารให้ "คงสถานะรอ sync / log pending" แต่ **ไม่มีคอลัมน์ไหนเก็บสถานะนี้** | ✅ **ปิดแล้ว 2026-09-13** — บันทึกเป็นแถว `sgi_interface_transactions` ที่ `direction='INTERNAL'` · `status='PENDING'` · `data_name='IMPACT_COMPETITOR'` (1 แถวต่อรอบ ไม่ใช่ต่อคู่แข่ง) · **ไม่ต้องเพิ่มคอลัมน์ใหม่** · นับได้ · Job 10 watchdog เฝ้าได้ |
| 🔴 **`source_system` ใช้ค่าอะไร** | สเปก SQL ใช้ **`'ALLMAP'`** · ผังใน `job-batch.html` เขียน **`ALM`** · ต้องเลือกค่าเดียว | 🔴 **ต้องเคาะ** — เป็นเงื่อนไขของ `DELETE` ตอน prune · ใช้ผิดค่าจะ **ลบไม่ตรงกลุ่ม** หรือ **ลบแถวของผู้ใช้** |
| 🔴 **เก็บ `source_row_id` ไหม** | ฟิลด์ 1 ของไฟล์เดิมคือ PK ของแถวต้นทาง | ✅ **ปิดแล้ว 2026-09-13** — เพิ่มคอลัมน์ `sgi_document_competitors.source_row_id BIGINT REFERENCES sgi_fgi_impact_competitors(id) ON DELETE SET NULL` · NULL = แถวที่ผู้ใช้คีย์เอง |
| 🔴 **gate ข้อมูลผู้อนุมัติยังต้องมีที่ Job 7 ไหม** | ระบบเดิมคัดรอบที่ `dv_*`/`gm_*`/`avp_*` ไม่ครบออก | ✅ **ปิดแล้ว 2026-09-13 — ตัดออก** · โครงใหม่ **ไม่มีคอลัมน์เหล่านั้นเลย** (ระบบเดิมมี 30 คอลัมน์ใน `FGI_IMPACT_STORE_INFO` · ของใหม่มีแค่ `sgi_impacted_stores.opt_dv_user_id`) ผู้อนุมัติมาจาก `@srm/glb-workflow` แล้ว → **ทำซ้ำที่นี่ไม่ได้และไม่ควร** |
| **ลำดับการรัน Job 7 กับ Job 8** | Job 7 ต้องรันหลัง Job 8 ถึงจะมี `doc_no` · ผังตั้ง cron `30 17 7-31` (Job 7) กับของ Job 8 ต้องไม่ชนกัน | ⏳ **ต้องระบุ dependency ใน AWS Batch** ไม่ใช่พึ่งเวลาห่างกัน |
| **รันย้อนหลัง** | job นี้ไม่รับ argument เลย — บอกไม่ได้ว่า "ขอ sync งวดพฤษภาคม" | ⏳ ระบบใหม่ควรรับ `year`/`month`/`docNo` เป็น optional input |
| **การ prune เป็นพฤติกรรมใหม่** | ระบบเดิมไม่เคยลบอะไรที่ปลายทาง | ⏳ **ต้องระบุกติกาให้ชัด** และมีเคสทดสอบว่าไม่แตะแถว `USER` |

---

## 11. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | 🔴 **ผลของ SFTP ถูกทิ้ง** | `ExportController.java:497` — `FtpUtils.uploadSFTPFile(...);` **ไม่มี `if` ครอบ** (ต่างจาก Job 6 บรรทัด 217 ที่ตรวจผล) · อัปโหลดล้มแต่ DB บันทึกว่า "ส่งแล้ว" แล้วชั้นกันซ้ำจะไม่ให้ส่งอีก | ระบบใหม่**เขียน DB ตรง ไม่มี SFTP** — แต่หลักการเดิมคือ **ห้ามทิ้งผลของ I/O** ทุกกรณี |
| **L2** | **SFTP อยู่ใน DB transaction** | อยู่ใน `doInTransaction()` เหมือน Job 6 · transaction เปิดค้างตลอดเวลาอัปโหลด | เขียน DB อย่างเดียวจึงหมดปัญหา · แต่ห้ามเอา I/O ภายนอกใส่ใน transaction |
| **L3** | **transaction ซ้อนสองชั้น** | `TransactionTemplate.execute()` + `createSavepoint()`/`rollbackToSavepoint()` เอง | transaction ชั้นเดียว (เหมือน Job 2 · L5) |
| **L4** | **insert ทีละแถวปนกับการเขียนไฟล์** | ลูปเดียวทำทั้ง `writeFile` และสะสม `ConfirmReceiveData` | แยกขั้นตอน · batch insert ครั้งเดียว |
| **L5** | **`args` ถูกทิ้งทั้งหมด** | `main()` เรียก `exportCompetitorToBPM()` โดยไม่ส่ง `args` ต่อ | รับ input เป็น JSON ตามสัญญาของ repo ปลายทาง |
| **L6** | **`CREATE_BY = 'system'` hardcode ใน SQL** | `'system' as create_by` ในคิวรี | ใช้ `source_system` ที่มีโดเมนชัดเจน |
| **L7** | **`line.separator` ตาม OS** | `FgiConstant.NEW_LINE` | ไม่เกี่ยวแล้วเพราะไม่เขียนไฟล์ · แต่ถ้ามี export ในอนาคตต้องกำหนดตายตัว |
| **L8** | **`getErrorProcess` ใช้ `'NuLL' in (nvl(...))`** | เทคนิคเทียบสตริงเพื่อหา NULL — อ่านยากและพังทันทีถ้ามีข้อมูลจริงที่มีค่าเป็นข้อความ `'NuLL'` | ใช้ `IS NULL` ตรง ๆ หรือ `num_nonnulls(...)` ของ PostgreSQL |
| **L9** | **credential SFTP ของ BPM ในไฟล์ config** | `ftpEaiServerIpBpm` · `ftpEaiUserIdBpm` · `ftpEaiPasswordBpm` | ไม่ต้องใช้แล้ว · แต่ credential เดิมยังต้อง rotate (`DECISIONS` ข้อ 4.6) |

> ⚠️ **L1 คือความเสี่ยงที่ร้ายที่สุดของ job นี้ในระบบเดิม**
> อัปโหลดล้ม → ไม่มีใครรู้ → ชั้นกันซ้ำปิดประตูไม่ให้ส่งอีก → **ข้อมูลคู่แข่งหายถาวรจากเอกสาร**
> ผู้พิจารณาตัดสินใจชดเชยโดยไม่เห็นว่ามีคู่แข่งเจ้าไหนอยู่ใกล้บ้าง
>
> ✅ **ระบบใหม่หมดความเสี่ยงนี้ไปโดยโครงสร้าง** เพราะเขียน DB ตรง — สำเร็จหรือ rollback เท่านั้น

---

## 12. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 3 (นำเข้าคู่แข่ง · เรื่องรหัสสาขา vs รหัสแบรนด์) | `batchjob/JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md` |
| Job 6 (ส่งออกไป STA · เทียบวิธีจัดการ SFTP) | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` |
| Job 8 (สร้างเอกสาร — ต้องรันก่อน Job 7) | `LLDD/md/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.md` |
| Job 8b (Gen Flow Gate ที่รับ gate ผู้อนุมัติมา) | `LLDD/md/Jobs/LLDD-BE-Job-8b-GenerateFlowToK2.md` |
| สเปกรูปแบบมาตรฐานของ Job 7 | `LLDD/md/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.md` |
| การ์ดคู่แข่งบนหน้าจอ | `k2-document.html` · master ที่ `k2-competitors.html` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
