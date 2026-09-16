# Job 8 — CreateCompensationDocument : สร้างเอกสารประกันรายได้อัตโนมัติ

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 10 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.14 · 2.17 · 2.24 · 2.31 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-08-CreateCompensationDocument-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/ExportImpactStoreFlowToBPM.java` · `controller/ExportController.java` (`exportImpactStoreFlowToBPM` · `manageImpactStoreToBPM` · `updateSeqToBpm` · `checkProcesssError` · `addMailToBPM`) · `dao/jdbc/ExportJdbc.java` (`queryImpactStoreToBPM` · `updateImpactStoreInfoNotOPT` · `getErrorProcess`) · `Constant/FgiConstant.java` · `config.xml` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** (ดู `LLDD-Database` และ `output/sql/sgi_schema.sql`) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-create-compensation-document` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-8-CreateCompensationDocument` · **Job 8b (เปิด workflow)** · **Job 7 (ยกคู่แข่งขึ้นเอกสาร)** ดู `batchjob/JOB-07-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

รวบข้อมูลทุกอย่างที่พร้อมแล้ว **สร้างเป็น "เอกสารประกันรายได้" หนึ่งใบ** พร้อมเลขที่เอกสาร
เพื่อให้คนเข้ามาพิจารณาต่อ

```
รอบชดเชยที่คำนวณค่าชดเชยเบื้องต้นแล้ว
        │
        │  ① เติมข้อมูลผู้อนุมัติที่ยังขาด
        │  ② คัดรอบที่ข้อมูลยังไม่ครบออก
        │  ③ ออกเลขที่เอกสาร YYYY/xxxxx
        ▼
sgi_compensation_documents  ──▶  Job 8b เปิด workflow  ──▶  คนพิจารณา
```

**ระบบเดิมทำโดยเขียนไฟล์ `BPM06001O` แล้ว SFTP ไป BPM (K2)** ซึ่งฝั่ง K2 เอาไปสร้างเอกสารเอง
**ระบบใหม่สร้างเอกสารลงตารางตรง ๆ** เพราะ SGI กับ K2 รวมเป็นระบบเดียวแล้ว

### เส้นแบ่งที่ต้องเข้าใจ — Job 8 กับ Job 8b คนละหน้าที่

| | **Job 8 (ฉบับนี้)** | Job 8b |
|---|---|---|
| ทำอะไร | **สร้างเอกสาร** + ออกเลขที่ | **เปิด workflow** ให้เอกสารนั้น |
| ปลายทาง | `sgi_compensation_documents` | `@srm/glb-workflow` ผ่าน `POST /sgi/workflow/instances` |
| Gate | ข้อมูลผู้อนุมัติ/ร้าน/ยอดชดเชยครบ | **Gen Flow Gate** (`growth_rate_diff` · `opt_dv_user_id` ฯลฯ) |
| เรียก workflow เองไหม | ❌ **ห้ามเด็ดขาด** | ❌ ห้ามเรียก lib เอง — เรียกผ่าน **BE API** (มติ 2026-09-09) |

> 🔴 **ข้อห้ามเชิงสถาปัตยกรรมของ Job 8** (ระบุในผัง): **ห้ามสร้างไฟล์ `BPM06001O` · ห้าม SFTP · ห้ามเรียก K2 REST**
> ใช้ Document Service + DB transaction เท่านั้น

---

## 2. ทำไมต้องมี job นี้

ก่อนหน้านี้ข้อมูลกระจายอยู่หลายที่ — รอบชดเชย · ค่าชดเชย · ยอดขาย · คู่แข่ง · ผู้อนุมัติ
**ยังไม่มี "เอกสาร" ที่คนจะเปิดดูและกดอนุมัติได้**

Job 8 คือตัวที่ **ตกผลึกข้อมูลทั้งหมดเป็นเอกสารหนึ่งใบ** พร้อมเลขที่ที่อ้างอิงได้

**สายข้อมูลเต็ม:** `Job 5` (ตัดสิน Y/N) → `Job 6` (สร้างค่าชดเชย) → **`Job 8` (สร้างเอกสาร)** → `Job 7` (ยกคู่แข่งขึ้นเอกสาร) → `Job 8b` (เปิด workflow) → คนพิจารณา → `Job 6` (ส่งผลไป STA)

---

## 3. ภาพรวมการทำงาน

```
① updateSeqToBpm()  — เลื่อนเลขลำดับรอบชดเชย
      │ ล้ม ──▶ return ทันที (ไม่ทำอะไรต่อ)
      ▼
② query candidate ครั้งที่ 1        ⚠️ ผลถูกทิ้งทั้งดุ้น
      ▼
③ updateImpactStoreInfoNotOPT()  — เติมข้อมูลผู้อนุมัติ SBP ที่ยังขาด
      │ ล้ม ──▶ แค่ log แล้วเดินต่อ
      ▼
④ query candidate ครั้งที่ 2        ← ชุดที่ใช้จริง
      ▼
⑤ คัดรอบที่ข้อมูลผู้อนุมัติไม่ครบออก (getErrorProcess)
      │ ไม่เหลือแถว ──▶ จบ (ถือว่าสำเร็จ)
      ▼
⑥ transaction เดียว: เขียนไฟล์ BPM06001O + insert FGI_CONFIRM_RECEIVE_DATA + SFTP ไป BPM
      ▼
⑦ ส่งเมล (เพิ่มผู้รับฝั่ง BPM เข้าไปด้วย)
```

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — query ใหญ่ถูกยิงสองรอบ รอบแรกทิ้ง

```java
List<Map> impactStoreList = exportService.queryImpactStoreToBPM();   // ← รอบที่ 1
try {
    exportService.updateImpactStoreInfoNotOPT();
} catch (Exception e) {
    LogUtils.error(getClass(), "error query updateImpactStoreInfoNotOPT : ", e);
}
impactStoreList.clear();                                             // ← ทิ้งผลรอบที่ 1
impactStoreList = exportService.queryImpactStoreToBPM();             // ← รอบที่ 2
```

**รอบแรกถูก `clear()` ทิ้งทั้งหมด** — เป็นการยิงคิวรีที่ join 5 ตารางและดึงคอลัมน์กว่า 50 คอลัมน์ **ฟรี ๆ**

> ⚠️ เจตนาที่เดาได้คือ *"เติมข้อมูลผู้อนุมัติก่อนแล้วค่อยอ่านใหม่ให้ได้ค่าที่เติมแล้ว"*
> ซึ่งถูกต้อง — **แต่การ query รอบแรกไม่จำเป็นเลย** ควรเติมข้อมูลก่อนแล้วค่อย query ครั้งเดียว

---

## 4. ขั้นที่ ① — เลื่อนเลขลำดับรอบชดเชย

```java
if (!updateSeqToBpm(informBean)) {
    return;                       // ไม่ทำอะไรต่อเลย
}
```

`updateSeqToBpm()` ห่อ `exportService.updateSeqToBpm()` ไว้ใน transaction ของตัวเอง
ทำหน้าที่เลื่อน `bpm_compensate_seq` / `bpm_compensate_seq_no` บน `FGI_IMPACT_STORE_INFO`
ให้ตรงกับรอบ/ครั้งที่ปัจจุบัน — ค่าสองตัวนี้คือ **"รอบที่ 1 · ครั้งที่ 3"** ที่แสดงบนหน้าจอ

> 📌 **ล้มแล้วหยุดทั้ง job ทันที** — ต่างจากขั้นที่ ③ ที่ล้มแล้วเดินต่อ
> เป็นการตัดสินใจที่ถูก เพราะเลขรอบผิดแปลว่าเอกสารจะออกมาผิดรอบ

---

## 5. ขั้นที่ ③ — เติมข้อมูลผู้อนุมัติที่ยังขาด

```sql
update fgi_impact_store_info fi set (
    sbp_dv_emp_id1, sbp_dv_fname_th1, ..., sbp_vp_email1     -- 18 คอลัมน์
) = (
    select v.sbp_dv_emp_id1, ..., v.sbp_vp_email1
      from v_fgi_sbp_approver v
     where fi.zone_i = v.STORE_AREA and fi.branchtype_i = v.STORE_TYPE
)
 where sbp_dv_emp_id1 is null or ... or sbp_vp_email1 is null     -- มีตัวใดตัวหนึ่งว่าง
```

**หาผู้อนุมัติจากวิว `v_fgi_sbp_approver` โดยจับคู่ด้วย `zone_i` + `branchtype_i`**
เติมให้ 3 ระดับ × 6 คอลัมน์ = **18 คอลัมน์**: `SBP_DV` · `SBP_GM` · `SBP_VP`

| ระดับ | คอลัมน์ต่อระดับ |
|---|---|
| `SBP_DV` (ผู้จัดการเขต) | `emp_id` · `fname_th` · `lname_th` · `fname_en` · `lname_en` · `email` |
| `SBP_GM` | ↑ เหมือนกัน |
| `SBP_VP` | ↑ เหมือนกัน |

> 📌 **ผู้อนุมัติถูกกำหนดจาก "โซน + ประเภทร้าน"** ไม่ใช่จากตัวร้าน
> นี่คือกลไก auto-assign รุ่นแรกที่ระบบใหม่แทนด้วย **`approver_snapshot` (JSONB)** และ auth-backend groups

### 🔴 ล้มแล้วเดินต่อเงียบ ๆ

```java
try {
    exportService.updateImpactStoreInfoNotOPT();
} catch (Exception e) {
    LogUtils.error(getClass(), "error query updateImpactStoreInfoNotOPT : ", e);
}
```

ถ้าคำสั่งนี้ล้ม (วิวไม่มีข้อมูล · join ได้หลายแถว · deadlock) → **แค่ log แล้วไปต่อ**
ผลคือข้อมูลผู้อนุมัติยังว่าง → ขั้นที่ ⑤ คัดรอบนั้นออก → **เอกสารไม่ถูกสร้าง โดยไม่มีใครรู้ว่าทำไม**

> ⚠️ **`UPDATE ... SET (cols) = (subquery)` ที่ subquery คืนหลายแถวจะ error ทั้งคำสั่ง**
> วิว `v_fgi_sbp_approver` ต้องมีแถวเดียวต่อ (`STORE_AREA`, `STORE_TYPE`) — **ถ้าซ้ำ job จะเงียบทุกวัน**

---

## 6. ขั้นที่ ④ ⑤ — เงื่อนไขคัดเลือกและ gate

### เงื่อนไข 4 ชั้นในคิวรีหลัก

```sql
  from fgi_impact_store_info si
  inner join fgi_impact_store_on_process op on op.impact_process_id = si.impact_process_id
  inner join fgi_impact_store_compensate fisc
          on fisc.impact_process_id = si.impact_process_id
         and fisc.compensate_month  = si.compensate_month
         and fisc.compensate_year   = si.compensate_year
         and fisc.compensate_status = 'I'                    -- ชั้น 2
         and fisc.compensate_forecast is not null            -- ชั้น 3
  left join fgi_impact_store_sales fiss
         on fiss.storecode_i = si.storecode_i
        and fiss.month = op.start_compensate_month
        and fiss.year  = op.start_compensate_year
 where op.flag_action in ('Y','W')                           -- ชั้น 1
   and not exists ( ... rd.data_name = 'IMPACT_STORE' ... )  -- ชั้น 4
```

| ชั้น | เงื่อนไข | ทำไม |
|---|---|---|
| **1** | รอบชดเชย `flag_action IN ('Y','W')` | เฉพาะรอบที่ยัง active |
| **2** | `compensate_status = 'I'` | เฉพาะรอบที่**ยังไม่ถูกอนุมัติ** — `A`/`N`/`S`/`Z` ผ่านขั้นนี้ไปแล้ว |
| **3** | `compensate_forecast is not null` | ต้องคำนวณค่าชดเชยเบื้องต้นแล้ว (Job 6 ขั้นที่ 5) |
| **4** | ยังไม่เคยสร้างเอกสารของงวดนี้ | กันสร้างซ้ำ — ใช้ `impact_store_info_id` เป็น idempotency key |

### 🔴 ค่าชดเชยที่ส่งออกใช้ `adjust` ก่อน `forecast`

```sql
nvl(fisc.compensate_adjust, fisc.compensate_forecast) as compensate_forecast,
null as compensate_adjust
```

**ค่าที่คนปรับแก้ (`adjust`) ชนะค่าที่ระบบคำนวณ (`forecast`)** และ **ส่งออกไปในชื่อ `compensate_forecast`**
ส่วนคอลัมน์ `compensate_adjust` ที่ส่งออก **บังคับเป็น `null` เสมอ**

> ⚠️ **การสลับชื่อแบบนี้ทำให้ปลายทางแยกไม่ออก**ว่าตัวเลขมาจากระบบหรือคนปรับ
> **ระบบใหม่ควรส่งทั้งสองค่าแยกกัน** ไม่ใช่ยุบเป็นตัวเดียว (ดูหัวข้อ 10)

### 🔴 แถว `STA` ถูกบังคับให้ `growth_rate_diff` เป็น NULL

```sql
decode(op.datasource, 'STA', null, fiss.growth_rate_diff) as growth_rate_diff
```

**รอบที่มาจาก Franchise Statement ถูกลบค่า `growth_rate_diff` ทิ้งโดยตั้งใจ**

| ช่องทาง | `growth_rate_diff` ที่ส่งออก |
|---|---|
| `ALM` (ALLMAP) | ค่าจริงจาก Job 5 |
| **`STA`** | **`null` เสมอ** |

> 📌 **นี่คือหลักฐานว่าเคส `STA` "ตั้งใจไม่ผ่านการคำนวณยอดขาย"** — สอดคล้องกับที่ Job 4 ไม่สร้างหัวสรุปให้แถว `STA`
> (`DECISIONS` ข้อ **2.24**) และ Job 7 ไม่ส่งคู่แข่งให้ (`datasource = 'ALM'`)
> **ทั้งสามที่สอดคล้องกัน → น่าจะเป็นการออกแบบ ไม่ใช่ช่องโหว่** แต่ยังต้องยืนยันว่าเคส STA เดินเส้นทางไหนแทน

### gate ข้อมูลผู้อนุมัติ (`getErrorProcess`)

เหมือน Job 7 — คัดรอบที่ `dv_*` / `gm_*` / `avp_*` มีคอลัมน์ใดเป็น NULL ออกทั้งรอบ

```java
if (errorProcessListMap.size() > 0) {
    String note = "don't write to file, error query data (storecode_I|zone_I|branchtype_I) : ";
    for (Map m : errorProcessListMap) { note += m.get("storeCodeI")+"|"+m.get("zoneI")+"|"+m.get("branchTypeI")+"\r\n"; }
    informBean.setNote(note);
    informBean.setStatus(FgiConstant.JOB_STATUS_FAIL);
}
```

> ✅ **จุดที่ระบบเดิมทำดี** — รายงานรายร้านที่ถูกคัดออก พร้อมโซนและประเภทร้าน
> ซึ่งเป็นข้อมูลที่ใช้ตามแก้ที่วิว `v_fgi_sbp_approver` ได้ทันที · **ระบบใหม่ต้องคงระดับรายละเอียดนี้ไว้**

---

## 7. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| ไฟล์ `BPM06001O` + SFTP ไป `BPM/FGI/Inbound/compensateflow/` | **`INSERT` ลง `sgi_compensation_documents`** |
| `FGI_IMPACT_STORE_INFO` (snapshot ร้าน + ผู้อนุมัติ) | `sgi_compensation_documents` + **`approver_snapshot` (JSONB)** |
| `bpm_compensate_seq` / `_seq_no` | `round_no` / `loop_no` |
| `FGI_CONFIRM_RECEIVE_DATA` | `sgi_interface_transactions` (`direction = 'INTERNAL'`) |
| K2 สร้างเลขเอกสารเอง | **`sgi_document_running_numbers`** ออก `doc_no` |

### เลขที่เอกสาร `YYYY/xxxxx`

```sql
CREATE TABLE sgi_document_running_numbers (
    year SMALLINT PRIMARY KEY,   -- ปี ค.ศ. เท่านั้น ห้ามเก็บ พ.ศ.
    last_running_no INTEGER NOT NULL DEFAULT 0 CHECK (last_running_no >= 0),
    updated_by VARCHAR(30), updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**นี่คือของใหม่ทั้งหมด** — ระบบเดิมไม่เคยออกเลขเอกสารเอง (K2 เป็นคนออก)

> 🔴 **ต้องล็อกแถวปีนั้นตอนออกเลข** ไม่งั้นรันพร้อมกันจะได้เลขซ้ำ
> สเปกระบุ `ON CONFLICT (year) DO UPDATE SET last_running_no = last_running_no + 1 ... RETURNING`
> ซึ่งเป็น atomic แต่ **ต้องอยู่ใน transaction เดียวกับการ insert เอกสาร**

> ⚠️ **เลขที่จองแล้วอาจกระโดดได้** ถ้า transaction rollback — สเปกยอมรับเรื่องนี้แล้ว
> (`idempotency`: *"conflict ต้องคืน/อ้าง doc_no เดิม และยอมให้เลขที่จองกระโดดโดยห้าม reuse"*)

### `sgi_compensation_documents` — คอลัมน์ที่ Job 8 ต้องใส่

| คอลัมน์ | ค่า | หมายเหตุ |
|---|---|---|
| `doc_no` · `year` · `running_no` | จาก running number | `YYYY/xxxxx` **ค.ศ.** |
| `impact_process_id` | **`NOT NULL` + `UNIQUE`** | idempotency key ตัวจริง |
| `impacted_store_code` | `NOT NULL` + FK | |
| `impact_month` · `new_store_code` | จากรอบชดเชย | |
| `round_no` · `loop_no` | จาก `bpm_compensate_seq` / `_seq_no` | หน้าจอแสดง "รอบ 1 · ครั้งที่ 3" |
| `source` | **`'FS'`** | `CHECK IN ('FS','MANUAL')` |
| `status_code` | **`NOT NULL`** | 🔴 ค่าจาก `sps_store.workflow_status` ของ engine — **แต่ Job 8 ยังไม่เปิด workflow** (ดู 🔴 A) |
| `total_compensation_amount` | `nvl(adjust, forecast)` | ดูหัวข้อ 6 |
| `allmap_url` | 🔴 **ไม่มีต้นทาง** | `DECISIONS` ข้อ **2.14** |
| `approver_snapshot` | JSONB จาก 18 คอลัมน์ผู้อนุมัติ | |
| `created_by` | `NOT NULL` | ชื่อ job |

### 🔴 A — `status_code` เป็น `NOT NULL` แต่ workflow ยังไม่เปิด

`status_code` คือ **ค่าจาก `sps_store.workflow_status` ของ engine** แต่ **Job 8b เป็นคนเปิด workflow ไม่ใช่ Job 8**

| ลำดับจริง | สถานะของเอกสาร |
|---|---|
| Job 8 สร้างเอกสาร | 🔴 **ยังไม่มี workflow → ยังไม่มี `status_code` จาก engine** |
| Job 8b เปิด workflow | ได้ `status_code` มา |

**แต่คอลัมน์เป็น `NOT NULL` — insert ไม่ผ่านถ้าไม่ใส่ค่า**

> 🔴 **ต้องเคาะว่า Job 8 ใส่ค่าอะไร** — ค่าตั้งต้นก่อนเข้า workflow (เช่น `'00'` = ร่าง) หรือให้คอลัมน์เป็น nullable
> เป็นปัญหาชนิดเดียวกับ `process_status` (`DECISIONS` ข้อ **2.17**)

### 🔴 B — `uq_comp_business` มี `new_store_code` ในคีย์

```sql
CONSTRAINT uq_comp_business UNIQUE (source, impacted_store_code, impact_month, new_store_code, round_no)
```

แต่ `impact_process_id` ก็เป็น **`UNIQUE`** เช่นกัน — **มีคีย์กันซ้ำสองชั้นที่ความหมายไม่ตรงกัน**

| คีย์ | หมายถึง |
|---|---|
| `UNIQUE (impact_process_id)` | **หนึ่งรอบชดเชย = หนึ่งเอกสาร** |
| `uq_comp_business` | หนึ่ง (ร้าน + งวด + **ร้านใหม่** + รอบ) = หนึ่งเอกสาร |

**ร้านหนึ่งร้านถูกกระทบจากร้านใหม่หลายร้านในงวดเดียวได้** (Job 2 สร้างหลายคู่)
แต่รอบชดเชยมีแถวเดียวต่อ (ร้าน + งวด) → **`new_store_code` บนเอกสารคือร้านไหน?**

> 🔴 **ต้องเคาะ** — ถ้าเลือกร้านใหม่มาเป็นตัวแทน ต้องระบุกติกา (Job 4 ใช้ "เปิดก่อนสุด")
> และถ้าคีย์ทั้งสองให้ผลต่างกันเมื่อไร **จะ insert ไม่ผ่านโดยไม่มีคำอธิบาย**

### `sgi_interface_transactions` — ค่าที่ Job 8 ต้องใส่

| คอลัมน์ | ค่า |
|---|---|
| `data_name` | **`'IMPACT_STORE'`** (การสร้างเอกสาร) หรือ **`'DOCUMENT_CREATE'`** 🔴 **ต้องเลือกค่าเดียว** |
| `direction` | `'INTERNAL'` |
| `status` | `'COMPLETED'` ทันที |
| `doc_no` · `impact_process_id` | typed FK |

> 🔴 **DDL มีทั้ง `IMPACT_STORE` และ `DOCUMENT_CREATE` ในโดเมน** และผังใช้ `IMPACT_STORE`
> ส่วน `DOCUMENT_CREATE` ถูกเพิ่มเข้า `CHECK` เมื่อ 2026-09-02 เพราะ "ใช้อยู่แล้วแต่ตกหล่นจาก CHECK"
> **ต้องระบุว่าเป็นคนละเหตุการณ์ หรือซ้ำซ้อนกัน**

---

## 8. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `seqUpdatedCount` | แถวที่ `updateSeqToBpm` แตะ | 0 ทุกวันแปลว่าไม่มีรอบใหม่ |
| `approverFilledCount` | แถวที่เติมข้อมูลผู้อนุมัติสำเร็จ | 🔴 **ถ้าคำสั่งนี้ล้ม ต้องทำให้ job ล้ม ไม่ใช่ log เฉย ๆ** |
| `candidateCount` | รอบที่ผ่านเงื่อนไข 4 ชั้น | |
| `filteredByApproverCount` | รอบที่ถูกคัดออกเพราะข้อมูลผู้อนุมัติไม่ครบ | 🔴 **> 0 ต้อง alert พร้อมรายชื่อร้าน + โซน + ประเภทร้าน** |
| `documentCreatedCount` | เอกสารที่สร้างสำเร็จ | |
| `runningNoIssued` · `runningNoSkipped` | เลขที่ออก · เลขที่กระโดด | เลขกระโดดเยอะ = rollback บ่อย |
| `duplicateSkippedCount` | รอบที่มีเอกสารอยู่แล้ว | รันซ้ำควรเข้าช่องนี้ทั้งหมด |
| `durationMs` | เวลาที่ใช้ | |

**สมการที่ต้องเป็นจริงเสมอ:**

```
candidateCount − filteredByApproverCount − duplicateSkippedCount  =  documentCreatedCount
documentCreatedCount = runningNoIssued
```

- 🔴 **alert เมื่อ `filteredByApproverCount > 0` ติดต่อกัน** — วิวผู้อนุมัติไม่ครอบคลุมโซน/ประเภทร้านนั้น
- 🔴 **alert เมื่อ `documentCreatedCount = 0` หลายวันติดในช่วงวันที่ 7–31** — สายงานสะดุดที่ไหนสักแห่ง

---

## 9. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — การคัดเลือก

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | รอบ `flag_action = 'Y'` · `status = 'I'` · มี forecast | **สร้างเอกสาร** |
| 1.2 | `flag_action = 'N'` (ปิดแล้ว) | ไม่สร้าง |
| 1.3 | `compensate_status = 'A'` (อนุมัติแล้ว) | ไม่สร้าง |
| 1.4 | `compensate_forecast` เป็น NULL | ไม่สร้าง |
| 1.5 | มีเอกสารของงวดนี้แล้ว | **ไม่สร้างซ้ำ** · นับ `duplicateSkippedCount` |
| 1.6 | มีทั้ง `forecast` และ `adjust` | ใช้ **`adjust`** เป็นยอดชดเชย |
| 1.7 | รอบจาก `datasource = 'STA'` | `growth_rate_diff` ต้องเป็น **NULL** (ไม่ใช่ค่าจาก join) |
| 1.8 | ไม่มี candidate เลย | job **สำเร็จ** · ไม่สร้างอะไร |

### กลุ่มที่ 2 — ข้อมูลผู้อนุมัติ

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | ข้อมูลผู้อนุมัติว่างแต่วิวมีข้อมูล | **เติมได้ครบ 18 คอลัมน์** แล้วสร้างเอกสาร |
| 2.2 | วิวไม่มีแถวของ (โซน + ประเภทร้าน) นั้น | 🔴 **แก้ 2026-09-14 — ระบบใหม่ต่างจากนี้โดยตั้งใจ**: **สร้างเอกสารต่อ** แล้วให้ **Job 8b เป็นด่านกัน** (`WAIT · NO_DV_USER`) เพราะวิว `v_fgi_sbp_approver` ไม่มีตัวแทนในระบบใหม่ · Job 8 ส่ง alert พร้อมรายชื่อโซนที่ไม่มีคนรับเรื่องทันทีที่สร้างเอกสาร |
| 2.3 | **วิวมีหลายแถวของคีย์เดียวกัน** | 🔴 ระบบเดิม **error ทั้งคำสั่ง** แล้วเดินต่อเงียบ ๆ · **ระบบใหม่ต้องล้มให้เห็น** |
| 2.4 | เติมข้อมูลผู้อนุมัติล้มเหลว | ❌ **job ต้องล้มเหลว** — ห้ามเดินต่อแล้วสร้างเอกสารไม่ครบ |
| 2.5 | `dv_email` ว่างคอลัมน์เดียว | 🔴 **แก้ 2026-09-14** — เหตุผลเดียวกับ 2.2 · ไม่คัดออกแล้ว |

### กลุ่มที่ 3 — เลขที่เอกสาร

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | เอกสารใบแรกของปี | `doc_no = '2026/00001'` |
| 3.2 | ปีใหม่ | เริ่มนับ `00001` ใหม่ · แถวปีเก่ายังอยู่ |
| 3.3 | **รัน 2 instance พร้อมกัน** | 🔴 **ห้ามได้เลขซ้ำ** — ต้อง atomic |
| 3.4 | transaction rollback หลังจองเลข | 🔴 **แก้ 2026-09-14 — ข้อความเดิมผิด** · ตัวนับเป็น **แถวในตาราง** ไม่ใช่ sequence → rollback **คืนเลข** ไม่มีเลขกระโดด (พิสูจน์กับ PostgreSQL ใน `__svc__/job8-concurrency.svc.spec.ts`) · **ไม่มีตัวนับชื่อ `runningNoSkipped` อยู่จริง** |
| 3.5 | เลขเกิน 99999 ในปีเดียว | ✅ **ตัดสินแล้ว** — โยน `JOB8_RUNNING_OVERFLOW` พร้อมข้อความว่าต้องขยาย `doc_no` หรือเปลี่ยนรูปแบบก่อน (`doc_no` เป็น `VARCHAR(10)` = `YYYY/xxxxx` พอดี) |
| 3.6 | ปีที่เก็บใน `sgi_document_running_numbers` | **ค.ศ. เท่านั้น** — ปฏิเสธ พ.ศ. |

### กลุ่มที่ 4 — ความคงทนและลำดับ

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | ล้มระหว่าง insert เอกสาร | **rollback ทั้ง running number และเอกสาร** |
| 4.2 | `updateSeqToBpm` ล้ม | **หยุดทั้ง job ทันที** · exit ≠ 0 |
| 4.3 | Job 8 รันก่อน Job 6 (ยังไม่มี `compensate_forecast`) | ไม่มี candidate · job สำเร็จ · รอบหน้าเก็บงานต่อ |
| 4.4 | Job 7 รันก่อน Job 8 | Job 7 นับ `pendingNoDocumentCount` (ดูเอกสาร Job 7) |
| 4.5 | รัน 2 instance พร้อมกัน | advisory lock → ตัวเดียวทำงาน |
| 4.6 | ส่งเมลไม่สำเร็จ แต่งานสำเร็จ | exit **0** + log ระดับ ERROR |
| 4.7 | งานไม่สำเร็จ แต่ส่งเมลสำเร็จ | exit **ไม่ใช่ 0** |
| 4.8 | รันซ้ำหลังสำเร็จ | `documentCreatedCount = 0` · `duplicateSkippedCount` = จำนวนเดิม |

---

## 10. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **`status_code` ตอนสร้างเอกสาร** | Job 8b เป็นคนเปิด workflow ไม่ใช่ Job 8 | ✅ **ปิดแล้ว — ปิดไปตั้งแต่มติข้อ 2.31** · DDL มี `DEFAULT '06'` + `CHECK IN ('01','02','03','06','08','99')` อยู่แล้ว · `'06'` = รอฝ่าย SBP DSA ซึ่งเป็นขั้นแรกของ flow · **lookup ชื่อสถานะอยู่ที่ `common_code SGI_DOC_STATUS` ไม่ใช่ `workflow_status` ของ engine** (engine ไม่มีคอลัมน์ code) |
| 🔴 **คีย์กันซ้ำสองชั้นที่ไม่ตรงกัน** | `UNIQUE (impact_process_id)` = หนึ่งรอบ = หนึ่งเอกสาร | ✅ **ปิดแล้ว 2026-09-13 (มติผู้ใช้)** — ดูด้านล่าง · ร้านใหม่ตัวแทนใช้กติกา **"เปิดก่อนสุด"** เหมือน Job 4/5 |

### 🔴 ข้อผิดพลาดของ DDL ที่พบตอนลงมือทำ — เอกสารเป็นรายงวด ไม่ใช่รายรอบ

`sgi_compensation_documents.impact_process_id` เคยเป็น **`UNIQUE`** = 1 เอกสารต่อ 1 รอบ
**ซึ่งขัดกับข้อมูลจริง:**

| ชุดข้อมูล | แถว | อัตราส่วน |
|---|---|---|
| `FGI_IMPACT_STORE_INFO_BK_20250515` (= เอกสาร) | 20,676 | — |
| `FGI_IMPACT_STORE_ON_PROCESS_BK` (รอบชดเชย) | 7,548 | **2.74 เอกสาร/รอบ** |
| `FGI_IMPACT_STORE_COMPENSATE_BK` (ค่าชดเชยรายงวด) | 20,674 | **1.0001 เอกสาร/งวด** |

ตารางเดิมมี `COMPENSATE_MONTH` / `COMPENSATE_YEAR` อยู่ชัดเจน →
**เอกสาร 1 ใบ = 1 งวดชดเชย** · ถ้าคง `UNIQUE` ไว้ **เอกสารของเดือนที่ 2 จะ insert ไม่ได้เลย**
และ `round_no` / `loop_no` ที่หน้าจอแสดงเป็น "รอบ 1 · ครั้งที่ 3" ก็จะไม่มีความหมาย

> ✅ **มติผู้ใช้ 2026-09-13** — เพิ่ม `impact_compensation_id BIGINT NOT NULL UNIQUE`
> ชี้ไป `sgi_fgi_impact_compensations(id)` เป็นตัวตนของเอกสาร · **ตัด `UNIQUE` ออกจาก `impact_process_id`**
> (คงคอลัมน์ไว้เพื่อค้นหา/รายงานระดับรอบ)
> พิสูจน์กับ PostgreSQL 16 จริงแล้ว: รอบเดียวสร้างเอกสารได้ 3 ใบ (งวดละใบ) `round_no`=1 `loop_no`=1,2,3
>
> ⚠️ **กระทบ Job 7 ที่ทำเสร็จไปแล้ว** — มัน `LEFT JOIN ... ON d.impact_process_id = p.id`
> ซึ่งจะคืนหลายแถวต่อรอบ ทำให้คู่แข่งงวดหนึ่งถูกยกขึ้นเอกสารทุกงวด · **แก้เป็น `d.impact_compensation_id = c.id` แล้ว**
| 🔴 **`data_name` ใช้ `IMPACT_STORE` หรือ `DOCUMENT_CREATE`** | DDL มีทั้งสองค่าในโดเมน | ✅ **ปิดแล้ว 2026-09-13 — ใช้ `DOCUMENT_CREATE`** · คอมเมนต์ใน DDL เองระบุว่า *"Job 8 บันทึกการสร้างเอกสาร (INTERNAL)"* · ส่วน `IMPACT_STORE` เป็นชื่อของ**ไฟล์ `BPM06001O` ที่ถูกยกเลิกไปแล้ว** จึงเป็นคนละเหตุการณ์ ไม่ใช่ค่าซ้ำซ้อน |
| 🔴 **`forecast` กับ `adjust` ถูกยุบเป็นค่าเดียว** | ระบบเดิมส่ง `nvl(adjust, forecast)` ในชื่อ `compensate_forecast` และบังคับ `compensate_adjust = null` | ✅ **ปิดแล้ว 2026-09-13 — หมดปัญหาไปโดยโครงสร้าง** · ระบบเดิมเสียข้อมูลเพราะ**ไฟล์มีช่องเดียว** · ระบบใหม่เขียน DB: `sgi_fgi_impact_compensations` เก็บ `forecast_amount` กับ `adjust_amount` **แยกกันครบ** และเอกสารผูกด้วย `impact_compensation_id` จึงตามกลับไปดูทั้งสองค่าได้เสมอ · ช่อง `total_compensation_amount` บนเอกสารเป็นยอดรวมสำหรับแสดงผลเท่านั้น |
| **`allmap_url` ไม่มีต้นทาง** | คอลัมน์มีอยู่และหน้าจออ่าน แต่ไม่มีใครเขียน | 🔴 `DECISIONS` ข้อ **2.14** (ยังไม่ปิด) |
| **ผู้อนุมัติจาก "โซน + ประเภทร้าน"** | ระบบเดิมใช้วิว `v_fgi_sbp_approver` จับคู่ด้วย `zone_i` + `branchtype_i` · ระบบใหม่ใช้ `approver_snapshot` + auth-backend groups | ⏳ **ต้องระบุว่าที่มาของ snapshot คืออะไร** และวิวเดิมจะถูกแทนด้วยอะไร |
| **เคส `STA` เดินเส้นทางไหน** | Job 4 ไม่สร้างหัวสรุป · Job 7 ไม่ส่งคู่แข่ง · Job 8 บังคับ `growth_rate_diff = null` — **ทั้งสามสอดคล้องกัน** | 🔴 `DECISIONS` ข้อ **2.24** — น่าจะเป็นการออกแบบ แต่ต้องยืนยันว่าเคส STA ได้ข้อมูลจากไหนแทน |
| **เลขเอกสารเกิน 99999** | `doc_no VARCHAR(10)` รูปแบบ `YYYY/xxxxx` | ⏳ ต้องระบุพฤติกรรม |

---

## 11. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | 🔴 **เติมข้อมูลผู้อนุมัติล้มแล้วเดินต่อเงียบ ๆ** | `exportImpactStoreFlowToBPM` — `try { updateImpactStoreInfoNotOPT(); } catch { log เฉย ๆ }` → ข้อมูลไม่ครบ → รอบถูกคัดออก → **เอกสารไม่ถูกสร้างโดยไม่มีใครรู้ว่าทำไม** | เติมล้ม = **job ล้มเหลว** · ห้ามเดินต่อ |
| **L2** | **query ใหญ่ยิงสองรอบ รอบแรกทิ้ง** | `queryImpactStoreToBPM()` → `clear()` → `queryImpactStoreToBPM()` อีกครั้ง | เติมข้อมูลก่อน แล้ว **query ครั้งเดียว** |
| **L3** | **`UPDATE ... SET (cols) = (subquery)` ที่ subquery อาจคืนหลายแถว** | `updateImpactStoreInfoNotOPT` — วิว `v_fgi_sbp_approver` ต้องมีแถวเดียวต่อ (`STORE_AREA`,`STORE_TYPE`) · ถ้าซ้ำ **error ทั้งคำสั่งทุกวัน** | ใช้ join ที่คัดแถวเดียวชัดเจน (`DISTINCT ON` / `row_number = 1`) + ตรวจว่าซ้ำแล้ว alert |
| **L4** | **`getErrorProcess` ใช้ `'NuLL' in (nvl(...))`** | เทคนิคเทียบสตริงหา NULL — พังถ้ามีข้อมูลจริงเป็นข้อความ `'NuLL'` | ใช้ `IS NULL` หรือ `num_nonnulls(...)` (เหมือน Job 7 · L8) |
| **L5** | **SFTP อยู่ใน DB transaction** | `manageImpactStoreToBPM` เหมือน Job 6/7 | ระบบใหม่เขียน DB ตรง ไม่มี SFTP |
| **L6** | **transaction ซ้อนสองชั้น** | `TransactionTemplate.execute()` + `createSavepoint()` เอง | transaction ชั้นเดียว (เหมือน Job 2 · L5) |
| **L7** | **`forecast` / `adjust` ถูกยุบและสลับชื่อ** | `nvl(fisc.compensate_adjust, fisc.compensate_forecast) as compensate_forecast, null as compensate_adjust` | ส่งทั้งสองค่าแยกกัน · ปลายทางต้องรู้ว่าใครเป็นคนกำหนดตัวเลข |
| **L8** | **`args` ถูกทิ้งทั้งหมด** | `main()` เรียก `exportImpactStoreFlowToBPM()` โดยไม่ส่ง `args` | รับ input JSON ตามสัญญาของ repo ปลายทาง · รองรับการรันซ่อมย้อนหลัง |
| **L9** | **สถานะ FAIL ถูกตั้งใน `finally` หลังงานสำเร็จไปแล้ว** | ถ้ามี `errorProcessListMap` จะตั้ง `JOB_STATUS_FAIL` **แม้เอกสารอื่นสร้างสำเร็จหมด** | แยก **"job ล้มเหลว"** ออกจาก **"มีรายการถูกคัดออก"** — อย่างหลังคือ warning ไม่ใช่ failure |

> ⚠️ **L1 + L9 รวมกันทำให้สัญญาณผิดสองทาง**
> เติมข้อมูลผู้อนุมัติล้ม → เอกสารไม่ถูกสร้าง แต่ job **ไม่ล้ม** (L1)
> ขณะที่มีรายการถูกคัดออกเพียงรายการเดียว → job **รายงานว่าล้มเหลว** ทั้งที่เอกสารอื่นสร้างครบ (L9)
> **ทั้งสองอย่างทำให้คนดูแลเชื่อสถานะของ job นี้ไม่ได้**

---

## 12. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 6 (สร้างค่าชดเชย · ต้องรันก่อน Job 8) | `batchjob/JOB-06-ExportImpactStoreToFS-อธิบายละเอียด.md` |
| Job 7 (ยกคู่แข่งขึ้นเอกสาร · ต้องรันหลัง Job 8) | `batchjob/JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md` |
| Job 5 (ที่มาของ `growth_rate_diff`) | `batchjob/JOB-05-ImportImpactSaleFromIAS-อธิบายละเอียด.md` |
| Job 8b (เปิด workflow · Gen Flow Gate) | `LLDD/md/Jobs/LLDD-BE-Job-8b-GenerateFlowToK2.md` |
| สเปกรูปแบบมาตรฐานของ Job 8 | `LLDD/md/Jobs/LLDD-BE-Job-8-CreateCompensationDocument.md` |
| หน้าจอเอกสาร | `k2-document.html` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ผังการทำงานของทุก job | `job-batch.html` (กลุ่ม Flow → Flow Batch Job) |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
