# Job 8b — StartInternalWorkflow : เปิด Workflow ให้เอกสารที่ผ่านเกณฑ์

> **สถานะ: เอกสารวิเคราะห์ + รายการที่ต้องตัดสินใจ** (ปรับปรุง 2026-09-10)
> อธิบายเป็นภาษาคนว่า job นี้ทำอะไร มีเคสอะไรบ้าง แต่ละเคสตัดสินจากอะไร และเขียนลงตารางไหนของ **ฐานข้อมูลใหม่**
>
> ⚠️ **ยังไม่ใช่ implementation-ready** — ข้อ 🔴 ในหัวข้อ 10 ต้องถูกเคาะก่อน
> (`DECISIONS-รอตัดสินใจ.md` ข้อ **2.15 · 2.26 · 2.31 · 2.32 · 4.6**)
>
> | | |
> |---|---|
> | **ที่อยู่ของไฟล์นี้** | `batchjob/JOB-08b-StartInternalWorkflow-อธิบายละเอียด.md` — **path ทุกอันเขียนจากรากโปรเจกต์ `sbp-prototype/`** |
> | **อ่านมาจากโค้ดจริง** | `batchjob/fcsJar/src/th/co/gosoft/fgi/` — `main/StartK2WorkFlow.java` · `service/StartFlowProcessService.java` (`selectImpactStore` · `startFlow` · `startFlowProcess` · `sendMailToOpt`) · `dao/jdbc/StartFlowJdbc.java` (`selectImpactStore` · `updateBeforeSelect` · `udateFlagNo` · `updateFlagGenFlow`) · `Constant/FgiConstant.java` |
> | **เขียนลงฐานข้อมูล** | **ตารางใหม่ `sgi_*`** + เรียก engine ผ่าน **BE API** (ไม่เขียน `sps_store.workflow_*` เอง) |
> | **repo ปลายทาง** | `SBP/srm-sps-spsap-sop-sgi-batch` (NestJS 11 · AWS Batch) ชื่อ job `sgi-start-internal-workflow` |
> | **เอกสารคู่กัน** | `LLDD-BE-Job-8b-GenerateFlowToK2` · **Job 8 (สร้างเอกสาร)** ดู `batchjob/JOB-08-*.md` · **Job 5 (ที่มาของ `growth_rate_diff`)** ดู `batchjob/JOB-05-*.md` |

---

## 1. Job นี้ทำอะไร (อธิบายสั้นที่สุด)

**เป็นประตูด่านสุดท้าย** — ตรวจว่าเรื่องนี้ "ควรเข้าสู่กระบวนการพิจารณาจริงไหม"
ถ้าผ่านก็ **เปิด workflow** ให้เอกสารนั้น แล้วส่งอีเมลแจ้งผู้จัดการเขต (DV)

```
เอกสารที่ Job 8 สร้างไว้ (workflow_generation_status = W)
        │
        │  Gen Flow Gate — 6 เงื่อนไข
        ├── ไม่ผ่านถาวร ──▶ N (จบ ไม่เข้า workflow)
        ├── ข้อมูลยังไม่พร้อม ──▶ คง W (รอบหน้าลองใหม่)
        ▼ ผ่าน
   เปิด workflow → Y → ส่งอีเมลราย DV
```

### 🔴 ข้อห้ามที่สำคัญที่สุด — batch job ห้ามเรียก workflow lib เอง

**มติ 2026-09-09:** `@srm/glb-workflow` ใช้กับ **flow K2 (เอกสาร/การอนุมัติ) เท่านั้น**

| | ระบบเดิม | ระบบใหม่ |
|---|---|---|
| วิธีเปิด workflow | **K2 REST `StartInstance`** ด้วย XML + HTTP Basic Auth | **`POST /api/v1/sgi/workflow/instances`** ด้วย service token |
| ใครเรียก engine | job เรียกตรง | **BE เป็นผู้เรียก engine ที่เดียวในระบบ** |
| ใครเขียน `workflow_transaction` | K2 | **BE** — SGI/job **ห้าม insert ตรง** |
| แปลง `impactProcessId` → `referenceId` | — | **BE เป็นผู้แปลง** (`referenceId` = `sgi_compensation_documents.id`) |

> 🔴 **นี่คือเหตุผลที่ Job 8b เป็น job เดียวที่ "ไม่มีหัวข้อ Workflow Trigger Event Contract"**
> เดิมมีที่ `5.97` แต่ถูกตัดออกเมื่อ 2026-09-09 · **ถ้าเห็น skeleton เรียก `initializeWorkflow` หรือ `addPreApprover` ตรง ๆ คือผิด**

---

## 2. ทำไมต้องแยกจาก Job 8

Job 8 สร้างเอกสารให้ **ทุกรอบที่คำนวณค่าชดเชยแล้ว** — แต่ไม่ใช่ทุกใบที่ควรเข้ากระบวนการพิจารณา

| | Job 8 | **Job 8b (ฉบับนี้)** |
|---|---|---|
| Gate | ข้อมูลผู้อนุมัติ/ร้าน/ยอดชดเชยครบไหม | **เข้าเกณฑ์ทางธุรกิจไหม** (growth rate · ประเภทร้าน · นิติบุคคล) |
| ล้มแล้วเป็นอย่างไร | ไม่สร้างเอกสาร | เอกสารมีอยู่ แต่ **ไม่เปิด workflow** |
| rerun | สร้างเอกสารใหม่ไม่ได้ (มีแล้ว) | **rerun ได้อิสระ** — นี่คือเหตุผลที่แยก job |

> 📌 **แยกเพื่อให้ rerun ได้** — ถ้าข้อมูลที่ Gate ต้องใช้ยังมาไม่ครบ (เช่นยอดขายยังไม่เข้า)
> เอกสารจะคง `W` ไว้แล้วรอบหน้าลองใหม่ **โดยไม่ต้องสร้างเอกสารซ้ำ**

---

## 3. ภาพรวมการทำงาน

```
① updateBeforeSelect()  — ปิดธงรายการที่มี process อยู่แล้ว (W → Y)
      ▼
② selectImpactStore()   — Gen Flow Gate 6 เงื่อนไข
      │ ไม่มีรายการ ──▶ ส่งเมล "Success: 0 / Fail: 0" แล้วจบ
      ▼
③ startFlow()           — เรียก K2 REST ทีละรายการ
      ▼
④ updateFlagGenFlow()   — ตั้ง Y เฉพาะรายการที่สำเร็จ
      ▼
⑤ udateFlagNo()         — ตั้ง N ให้รายการที่ประเภทร้านไม่เข้าเกณฑ์
      ▼
⑥ sendMailToOpt()       — ส่งอีเมลจัดกลุ่มราย DV
```

### 🔴 เรื่องที่ต้องรู้ก่อนอย่างอื่น — ขั้นที่ ① ตั้ง `Y` โดยไม่เปิด workflow

```sql
update fgi_impact_store s
   set flag_gen_flow = 'Y'
 where flag_gen_flow = 'W'
   and exists (select p.impact_store_id from fgi_impact_process p
                where p.impact_store_id = s.impact_store_id)
```

คอมเมนต์ในโค้ดเขียนว่า **`//เพื่อลดการ StartFlow ซ้ำ`**

แปลว่า: **ถ้าเจอว่ามี process อยู่แล้วในตาราง `fgi_impact_process` ให้ถือว่า "เปิดไปแล้ว"**
แล้วตั้ง `Y` ทันที **โดยไม่ต้องเรียก K2 อีก**

> ⚠️ **เป็นกลไกซ่อมสถานะ ไม่ใช่การเปิด workflow** — ใช้กรณีที่รอบก่อนเปิด workflow สำเร็จแล้ว
> แต่ `updateFlagGenFlow` ยังไม่ทันทำงาน (job ตายกลางทาง) · ถ้าไม่มีขั้นนี้จะเปิด workflow ซ้ำ
>
> 🔴 **แต่ถ้า `fgi_impact_process` มีแถวค้างจากสาเหตุอื่น จะตั้ง `Y` ให้ทั้งที่ไม่เคยเปิด workflow เลย**
> แล้วเอกสารนั้น **จะไม่มีวันถูกเปิด workflow อีก** เพราะ Gate คัดเฉพาะ `W`

---

## 4. ขั้นที่ ② — Gen Flow Gate 6 เงื่อนไข

```sql
where s.flag_gen_flow = 'W'                                           -- G1
  and s.branchtype_i in ('FAM','FB1','FC1','FB2','FVB','FVC')          -- G2
  and ms.opt_dv_user_id is not null                                    -- G3
  and exists ( ... nvl(j_n.juristic_name,'n') != nvl(j_i.juristic_name,'i') ... )  -- G4
  and s.growth_rate_diff <= -10                                        -- G5
  and s.sales_status in ('Y','N')                                      -- G6
```

| # | เงื่อนไข | ความหมาย |
|---|---|---|
| **G1** | `flag_gen_flow = 'W'` | ยังไม่เคยเปิด workflow |
| **G2** | ประเภทร้านอยู่ในชุด 6 ค่า | **`FAM · FB1 · FC1 · FB2 · FVB · FVC`** — ไม่รวม `B` และ `FPT1` |
| **G3** | **`opt_dv_user_id` ไม่ว่าง** | ต้องรู้ว่าใครคือผู้จัดการเขตที่จะรับเรื่อง |
| **G4** | นิติบุคคลสองฝั่ง **ต่างกัน** | เจ้าของเดียวกันไม่ถือว่ากระทบ |
| **G5** | **`growth_rate_diff <= -10`** | ยอดโตแย่ลงอย่างน้อย 10% |
| **G6** | `sales_status IN ('Y','N')` | **ผ่านการประเมินจาก Job 5 มาแล้ว** (ค่าใดก็ได้) |

### 🔴 G5 กับ Job 5 ใช้เกณฑ์คนละตัวบนตัวเลขเดียวกัน

| | เกณฑ์ | ผล |
|---|---|---|
| **Job 5** ตัดสิน `sales_status` | `growth_rate_diff < 0` → `Y` | ยอดตกแม้นิดเดียวก็ `Y` |
| **Job 8b** Gate G5 | `growth_rate_diff <= -10` | ต้องตกอย่างน้อย 10% |

**แถวที่ `-10 < diff < 0`** → Job 5 ให้ `sales_status = 'Y'` แต่ **ไม่ผ่าน G5**

แล้วเกิดอะไรขึ้นกับแถวเหล่านั้น?

| ขั้น | ทำอะไรกับแถวนี้ |
|---|---|
| Gate (`selectImpactStore`) | ไม่ถูกเลือก |
| `udateFlagNo()` | ตั้ง `N` **เฉพาะแถวที่ประเภทร้านไม่เข้าเกณฑ์** — แถวนี้ประเภทร้านผ่าน จึงไม่โดน |

→ 🔴 **แถวค้างเป็น `W` ตลอดไป** ไม่มีอะไรมาทำให้จบ

> ⚠️ **เป็นปัญหาชนิดเดียวกับ "แถวตกร่อง" ของ Job 2** — ไม่เข้าทั้งกฎผ่านและกฎตัดทิ้ง
> และไม่มี metric ไหนนับ · **ระบบใหม่ต้องมีนโยบายชัดเจนว่าแถวเหล่านี้จบอย่างไร** (ดูหัวข้อ 10)

> 📌 **ตัวเลข `-10` เป็น literal ในโค้ด** — ถ้าธุรกิจขอเปลี่ยนเกณฑ์ต้อง deploy ใหม่
> ระบบใหม่ตกลงว่าค่าธุรกิจอยู่ที่ `mas_param`/`common_code`

### 🔴 G6 รับทั้ง `Y` และ `N` — `sales_status` ไม่ได้เป็นตัวตัดสิน

`sales_status IN ('Y','N')` แปลว่า **ร้านที่ Job 5 ตัดสินว่า "ไม่เข้าเกณฑ์" (`N`) ก็ผ่าน Gate ได้**

ตัวตัดสินจริงคือ **G5 (`growth_rate_diff <= -10`)** ส่วน G6 ทำหน้าที่แค่เช็คว่า **"ประเมินเสร็จแล้ว"**
(ยังไม่ประเมินจะเป็น `W`; ผิดพลาดจะเป็น `E`)

> ⚠️ **อ่านผิดง่ายมาก** — คนอ่านเผิน ๆ จะคิดว่า `sales_status = 'Y'` คือเกณฑ์ผ่าน
> **ระบบใหม่ควรตั้งชื่อให้ชัด** เช่นแยกเป็น `salesEvaluated` (boolean) กับ `salesResult`

### 🔴 G3 — `opt_dv_user_id` มาจากการเดาชื่อ

```sql
select bu.user_id from ( ... business_user ... ) bu
 where bu.group_id = mso.group_id and mso.group_id = 15          -- 15 = DV
   and ( bu.emp_id = mso.emp_id
      or ( instr(mso.fullname, bu.first_name) > 0
       and instr(mso.fullname, bu.last_name)  > 0 ) )
   and rownum = 1
```

หา `user_id` ของผู้จัดการเขตด้วย **สองวิธี**:
1. จับคู่ด้วย `emp_id` — ถูกต้อง
2. **จับคู่ด้วยการหาชื่อ-นามสกุลเป็นสตริงย่อยใน `fullname`** — เปราะมาก

แล้วเอา `rownum = 1` (แถวไหนก็ได้) และชั้นนอกใช้ `max(...)` พร้อมคอมเมนต์
`--max for opt_dv_user_id or opt_gm_user_id is null (cannot distinct)`

| ปัญหา | ผล |
|---|---|
| ชื่อซ้ำกันในองค์กร | ได้ `user_id` ผิดคน → **เรื่องไปหาคนผิด** |
| ชื่อสะกดต่างกันเล็กน้อย | หาไม่เจอ → `opt_dv_user_id` ว่าง → **G3 ไม่ผ่าน → ค้าง W** |
| `rownum = 1` ก่อน order | ผลไม่ deterministic |

> 🔴 **ระบบใหม่ต้องผูกด้วย `emp_id` หรือ `user_id` เท่านั้น ห้ามจับคู่ด้วยชื่อ**
> `sgi_impacted_stores.opt_dv_user_id` ยังไม่มีใครเติม (`DECISIONS` ข้อ **2.15** กลุ่มเดียวกัน)

---

## 5. ขั้นที่ ③ — เปิด workflow (ระบบเดิม)

```java
String urlSes = FgiConstant.STARTFLOW;         // K2 REST StartInstance
String userCredentials = FgiConstant.K2USER;   // "7ELEVEN\bpmk2_fcs:SupportGSSF2"
String basicAuth = "Basic " + new String(new Base64().encode(userCredentials.getBytes()));
```

payload เป็น **XML** ตามสัญญาของ K2:

```xml
<w:ProcessInstance ExpectedDuration="20"
    FullName="FranchiseImpactAssessment\CPA_Franchise_FIA_WF_ImpactAssessment"
    Folio="FIA{storeID}" Priority="3">
  <p:DataField Name="KeyImpactStoreID">{storeID}</p:DataField>
  <p:DataField Name="KeyProcessStatus">W</p:DataField>
  <p:DataField Name="KeyImpactStatus">W</p:DataField>
</w:ProcessInstance>
```

### 🔴 ตรวจว่าสำเร็จด้วยการหาคำในข้อความตอบกลับ

```java
if (responseString.contains("Failure")) { LogUtils.info(getClass(), responseString); }
if (responseString.contains("Running")) { status = true; }
```

| กรณี | ผล |
|---|---|
| ตอบกลับมีคำว่า `Running` | ✅ ถือว่าสำเร็จ |
| ตอบกลับมีคำว่า `Failure` | **แค่ log** — ไม่ตั้ง fail |
| ตอบกลับไม่มีทั้งสองคำ | ❌ `status = false` เงียบ ๆ |
| HTTP ไม่ใช่ 200 | log แล้ว `status = false` |

> 🔴 **เปราะสองชั้น** — (1) ถ้า K2 เปลี่ยนข้อความตอบกลับ ระบบจะคิดว่าล้มเหลวทั้งหมด
> (2) ถ้าคำว่า `Running` ปรากฏในบริบทอื่น (เช่นข้อความ error) จะคิดว่าสำเร็จ
>
> ✅ **ระบบใหม่ใช้ HTTP status + response body ที่มีโครงสร้าง** จาก `POST /api/v1/sgi/workflow/instances`

> 🔴 **credential ฝังในโค้ด** — `K2USER` มีทั้ง domain user และรหัสผ่านใน `FgiConstant.java:23`
> `DECISIONS` ข้อ **4.6** — ต้อง rotate ไม่ใช่แค่ย้ายที่เก็บ

### ⚠️ ไม่มี timeout · ไม่มี retry

`HttpURLConnection` ถูกใช้โดยไม่ตั้ง `setConnectTimeout` / `setReadTimeout`
**ถ้า K2 ค้าง job จะค้างตามไม่มีกำหนด** และเปิด workflow ทีละรายการแบบ sequential

---

## 6. ขั้นที่ ④ ⑤ ⑥ — ปิดธงและแจ้งผล

### ธงสามค่า

| ค่า | ตั้งโดย | ความหมาย |
|---|---|---|
| `W` | Job 8 ตอนสร้าง | รอเปิด workflow |
| `Y` | `updateFlagGenFlow()` (เฉพาะที่สำเร็จ) + `updateBeforeSelect()` | เปิดแล้ว |
| `N` | `udateFlagNo()` | **เฉพาะประเภทร้านไม่เข้าเกณฑ์** |

```sql
update fgi_impact_store set flag_gen_flow = 'N'
 where flag_gen_flow = 'W'
   and nvl(branchtype_i,'-') not in ('FAM','FB1','FC1','FB2','FVB','FVC')
```

> 🔴 **`N` ถูกตั้งจากเงื่อนไขเดียวเท่านั้น** — G2 (ประเภทร้าน)
> เงื่อนไข G4 (นิติบุคคลเดียวกัน) และ G5 (growth ไม่ถึงเกณฑ์) **ไม่เคยทำให้เป็น `N`**
> ทั้งที่ทั้งสองเป็นเงื่อนไขที่ **ไม่มีวันเปลี่ยน** (นิติบุคคลเดียวกันก็คือเดียวกัน · growth ที่คำนวณแล้วก็นิ่งแล้ว)
>
> ✅ **ผังของระบบใหม่แก้เรื่องนี้แล้ว** — ระบุว่า *"branch type, distance, missing DV, same juristic หรือ growth > -10 → N"*
> และ *"distance/juristic/growth/sales status ที่ยังไม่มีค่าเท่านั้นจึงคง W"*
> **คือแยก "ไม่ผ่านถาวร" ออกจาก "ข้อมูลยังไม่พร้อม" ให้ชัด**

### อีเมลราย DV

`sendMailToOpt()` จัดกลุ่มสองชั้น: **DV → ร้านเปิดใหม่** แล้วส่งอีเมลหนึ่งฉบับต่อ DV หนึ่งคน

> ⚠️ **`email = sendList.get(0).getOptDvUserEmail()`** — เอาอีเมลจาก**แถวแรก**ของกลุ่ม
> ถ้าข้อมูลไม่สอดคล้องกัน (DV เดียวกันแต่อีเมลต่างกัน) จะส่งไปที่อีเมลของแถวแรกเท่านั้น

### ⚠️ ผู้รับอีเมลสรุปถูก hardcode และ **ไม่เคยถูกส่ง**

```java
List<String> mailto = new ArrayList<String>();
mailto.add("go-sbp@gosoft.co.th");
...
// SendMailUtil.sendEmail(mailto, null, null, "FIA Start WorkFlow Report", mailBody.toString());
```

**บรรทัดที่ส่งเมลสรุปจำนวนสำเร็จ/ล้มเหลว ถูก comment ทิ้ง** — โค้ดที่สร้าง `mailBody` ยังอยู่ แต่ไม่มีใครส่ง

→ **ไม่มีใครรู้ว่ารอบนั้นเปิด workflow สำเร็จกี่รายการ ล้มกี่รายการ**
(ยกเว้นกรณี "ไม่มีรายการเลย" ที่ยังส่งอยู่ — ส่งเฉพาะตอนที่ไม่มีอะไรให้รายงาน)

---

## 7. เขียนลงฐานข้อมูลใหม่ตรงไหน

### การแปลง

| ระบบเดิม | ระบบใหม่ |
|---|---|
| `fgi_impact_store.flag_gen_flow` | **`sgi_fgi_impact_processes.workflow_generation_status`** |
| K2 REST `StartInstance` + XML | **`POST /api/v1/sgi/workflow/instances`** (service token) |
| K2 สร้าง process instance | **BE เรียก `@srm/glb-workflow`** แล้วเขียน `sps_store.workflow_*` เอง |
| `KeyImpactStoreID` (data field) | **`referenceId` = `sgi_compensation_documents.id`** (DP-1 · ปิดแล้ว 2026-08-17) |
| `opt_dv_user_id` จากการเดาชื่อ | **`sgi_impacted_stores.opt_dv_user_id`** (ยังไม่มีใครเติม) |

```sql
workflow_generation_status CHAR(1) NOT NULL DEFAULT 'W'
    CHECK (workflow_generation_status IN ('W','Y','N'))
```

**โดเมนตรงกับระบบเดิมพอดี** ✅ และอยู่ที่ **`sgi_fgi_impact_processes` (hub)** ไม่ใช่ที่คู่ร้าน

### ตารางที่ Job 8b อ่าน (ทั้งหมดเป็น R ไม่ใช่ W)

| ตาราง | อ่านอะไร |
|---|---|
| `sgi_fgi_impact_processes` | `last_compensate_seq_no` + `flag_action` — **ตัดสินจุดเข้า flow** |
| `sgi_fgi_impact_compensations` | `COALESCE(adjust_amount, forecast_amount) = 0` กี่งวดติดกัน |
| `sgi_impacted_stores` | `opt_dv_user_id` (G3 + จัดกลุ่มอีเมล) |
| `sgi_fgi_impact_sales_summaries` | `growth_rate_diff` (G5) · `sales_status` (G6) |
| `sgi_compensation_documents` | ต้องมีเอกสารแล้ว |

> ✅ **Job 8b ไม่เขียน `sps_store.workflow_*` เลย** — BE เป็นผู้เขียนหลังเรียก engine

### 🔴 จุดเข้า flow — ของใหม่ที่ระบบเดิมไม่มี

ระบบเดิมเปิด workflow ที่จุดเดียวเสมอ (`KeyProcessStatus = 'W'`)
**ระบบใหม่ต้องตัดสินจุดเข้าจากประเภทเคส:**

| เคส | จุดเข้า |
|---|---|
| เปิดเรื่องใหม่ | **state 06** (ฝ่าย SBP DSA) |
| ชดเชยต่อเนื่อง — ยอด > 0 | **state 08** |
| ชดเชยต่อเนื่อง — **ยอด 0 ไม่เกิน 3 เดือน** | **state 08** (มติ 2026-09-01 · เดิมเข้า 01) |
| ยอด 0 **เดือนที่ 4** | **ปิดเอกสารเป็นหยุดชดเชย** — ไม่เปิด workflow |

> 🔴 **การนับ "ยอด 0 กี่งวดติดกัน" ต้องนิยามให้ชัด** — นับจากงวดไหนถึงงวดไหน · งวดที่ข้ามไปนับไหม
> เป็นตรรกะที่ **ไม่มีในระบบเดิมเลย** จึงไม่มีโค้ดให้เทียบ (ดูหัวข้อ 10)

---

## 8. ตัวเลขที่ job ต้องรายงานทุกรอบ

| ชื่อ | นับอะไร | ตรวจอะไรได้ |
|---|---|---|
| `repairedToYCount` | แถวที่ถูกตั้ง `Y` เพราะมี process อยู่แล้ว (ขั้น ①) | 🔴 **> 0 บ่อยต้อง alert** — แปลว่า job ตายกลางทางบ่อย |
| `candidateCount` | แถวที่ผ่าน Gate ครบ 6 ข้อ | |
| `rejectedPermanentCount` | ตั้ง `N` — แยกตามเหตุผล (branch type · juristic · growth · DV หาย) | 🔴 **ต้องแยกเหตุผล** ไม่ใช่ตัวเลขรวม |
| **`stuckWaitingCount`** | แถวที่คง `W` เพราะข้อมูลยังไม่พร้อม | 🔴 **> 0 ข้ามสัปดาห์ต้อง alert** — ข้อมูลต้นทางไม่มาสักที |
| `workflowStartedCount` | เปิด workflow สำเร็จ | |
| `workflowFailedCount` | เรียก API แล้วล้ม | 🔴 **> 0 ต้อง alert** — ระบบเดิมไม่เคยรายงานเลข้นี้ (เมลถูก comment ทิ้ง) |
| `closedAsStoppedCount` | ปิดเป็นหยุดชดเชย (ยอด 0 เดือนที่ 4) | |
| `mailSentDvCount` · `mailFailedDvCount` | อีเมลราย DV | |
| `durationMs` | เวลาที่ใช้ | 🔴 จับกรณี API ค้าง (ระบบเดิมไม่มี timeout) |

**สมการที่ต้องเป็นจริงเสมอ:**

```
candidateCount = workflowStartedCount + workflowFailedCount + closedAsStoppedCount
แถว W ทั้งหมด = candidateCount + rejectedPermanentCount + stuckWaitingCount
```

- 🔴 **alert เมื่อ `stuckWaitingCount` ไม่ลดลงข้ามสัปดาห์** — นี่คือกลุ่มที่ระบบเดิมปล่อยค้างตลอดไป
- 🔴 **alert เมื่อ `workflowFailedCount > 0`** — เอกสารมีแต่ไม่มีใครเห็นเพราะ workflow ไม่เปิด

---

## 9. เคสทดสอบที่ต้องมี

### กลุ่มที่ 1 — Gen Flow Gate

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 1.1 | ผ่านครบ 6 เงื่อนไข | **เปิด workflow** · `workflow_generation_status = 'Y'` |
| 1.2 | `branchtype_i = 'B'` (นอกชุด 6 ค่า) | **`N`** — ไม่ผ่านถาวร |
| 1.3 | `branchtype_i = 'FPT1'` | **`N`** — ไม่อยู่ในชุดของ Job 8b (ต่างจากกฎ Job 2 ที่รับ FPT1 แบบมีเงื่อนไข) |
| 1.4 | `opt_dv_user_id` ว่าง | ✅ **ปิดแล้ว 2026-09-13 — เลือก `W` (WAIT) ไม่ใช่ `N`** · ถ้าเป็น `N` แล้ว DV ถูกเติมทีหลัง เรื่องจะไม่มีวันกลับมา · หลักการของผังใหม่คือ "ข้อมูลยังไม่พร้อม → `W`" ซึ่ง DV ที่ยังไม่ถูกเติมเข้านิยามตรง ๆ (Job 8 เติมให้ได้รอบถัดไป) · Job 8 ส่ง alert ตั้งแต่วันแรก และ Job 8b เตือนตามอายุที่ค้าง |
| 1.5 | นิติบุคคลสองฝั่งเหมือนกัน | **`N`** (ระบบเดิมคง `W` — เปลี่ยนพฤติกรรม) |
| 1.6 | `growth_rate_diff = -10` พอดี | **ผ่าน** (`<=` ไม่ใช่ `<`) |
| 1.7 | `growth_rate_diff = -9.99` | **`N`** — ไม่ถึงเกณฑ์ |
| 1.8 | 🔴 **`growth_rate_diff = -5`** (อยู่ระหว่าง −10 กับ 0) | ระบบเดิม **ค้าง `W` ตลอดไป** · **ระบบใหม่ต้องเป็น `N`** |
| 1.9 | `growth_rate_diff` เป็น **NULL** | **คง `W`** — ข้อมูลยังไม่พร้อม (ไม่ใช่ `N`) |
| 1.10 | `sales_status = 'N'` | **ผ่าน G6** — `N` ไม่ได้แปลว่าไม่ผ่าน Gate |
| 1.11 | `sales_status = 'W'` (ยังไม่ประเมิน) | **คง `W`** |
| 1.12 | `sales_status = 'E'` (ประเมินผิดพลาด) | ✅ **ตัดสินแล้ว — คง `W` แต่แยกเหตุผลเป็น `SALES_ERROR`** (รัน Job 5 ซ้ำแล้วแก้ได้ · ระบบเดิมปล่อยค้างเงียบ) |

### กลุ่มที่ 2 — จุดเข้า flow

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 2.1 | เปิดเรื่องใหม่ (`last_compensate_seq_no = 1`) | เข้า **state 06** |
| 2.2 | ชดเชยต่อเนื่อง ยอด > 0 | เข้า **state 08** |
| 2.3 | ชดเชยต่อเนื่อง **ยอด 0 เดือนที่ 1** | เข้า **state 08** |
| 2.4 | ยอด 0 **เดือนที่ 3** | เข้า **state 08** |
| 2.5 | ยอด 0 **เดือนที่ 4** | **ปิดเอกสารเป็นหยุดชดเชย** · ไม่เปิด workflow |
| 2.6 | ยอด 0 สลับกับยอด > 0 | 🔴 **ต้องนิยามว่านับติดกันอย่างไร** |
| 2.7 | `adjust_amount` = 0 แต่ `forecast_amount` > 0 | ใช้ `COALESCE(adjust, forecast)` = **0** → นับเป็นงวดยอด 0 |

### กลุ่มที่ 3 — การเปิด workflow

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 3.1 | API ตอบ 201 | `Y` · บันทึก `referenceId` ที่ใช้ |
| 3.2 | API ตอบ 4xx (ข้อมูลผิด) | ❌ **ไม่ตั้ง `Y`** · นับ `workflowFailedCount` · **alert** |
| 3.3 | API ตอบ 5xx | ↑ เหมือนกัน · **retry ได้รอบหน้าเพราะยังเป็น `W`** |
| 3.4 | **API ค้างไม่ตอบ** | 🔴 **ต้องมี timeout** — ระบบเดิมค้างไม่มีกำหนด |
| 3.5 | เปิด workflow สำเร็จแต่ update ธงล้ม | 🔴 รอบหน้าขั้น ① ต้องซ่อมได้ (ตั้ง `Y` โดยไม่เปิดซ้ำ) |
| 3.6 | รัน 2 instance พร้อมกัน | **ห้ามเปิด workflow ซ้ำ** — advisory lock หรือ `FOR UPDATE SKIP LOCKED` |
| 3.7 | rerun หลังสำเร็จทั้งหมด | `candidateCount = 0` · ไม่เรียก API เลย |
| 3.8 | ⚠️ job เรียก `@srm/glb-workflow` เอง | ❌ **ต้องไม่มีในโค้ด** — เรียกผ่าน BE API เท่านั้น (มติ 2026-09-09) |

### กลุ่มที่ 4 — อีเมลและการรายงาน

| # | สถานการณ์ | ผลที่ต้องได้ |
|---|---|---|
| 4.1 | 3 ร้านของ DV คนเดียวกัน | **อีเมลฉบับเดียว** รวม 3 ร้าน |
| 4.2 | ร้านของ DV 2 คน | **2 ฉบับ** |
| 4.3 | DV ไม่มีอีเมล | ✅ **ทำแล้ว 2026-09-14** — นับแยกสองเหตุ `dvNoEmailCount` (ไม่มีอีเมลในระบบ) / `dvMailFailedCount` (ส่งไม่ผ่าน) + **alert พร้อมรายชื่อ** · job ยังสำเร็จเพราะ workflow เปิดจริงแล้ว |
| 4.4 | ไม่มีรายการให้เปิดเลย | job **สำเร็จ** · รายงาน `candidateCount = 0` |
| 4.5 | **มีรายการและเปิดสำเร็จบางส่วน** | 🔴 **ต้องรายงานตัวเลขสำเร็จ/ล้ม** — ระบบเดิม comment ทิ้ง |
| 4.6 | ส่งเมลไม่สำเร็จ แต่เปิด workflow ครบ | exit **0** + log ระดับ ERROR |
| 4.7 | เปิด workflow ไม่ครบ | exit **ไม่ใช่ 0** |

---

## 10. สิ่งที่ต้องตัดสินใจก่อนเริ่มเขียนโค้ด

| เรื่อง | คำถาม | สถานะ |
|---|---|---|
| 🔴 **แถวที่ `-10 < diff < 0` ค้าง `W` ตลอดไป** | Job 5 ให้ `sales_status = 'Y'` (เกณฑ์ `< 0`) แต่ Gate G5 ใช้ `<= -10` | ⚙️ **ทำตามผังใหม่แล้ว — ตั้ง `N` พร้อมเหตุผลที่อ่านออก** (`GROWTH_ABOVE_THRESHOLD` · ข้อความแยก "ยอดตกแต่ยังไม่ถึงเกณฑ์" ออกจาก "ยอดไม่ตก") · job นับแยกใน `rejectedByReason` ทุกรอบ · 🔴 **ยังต้อง business sign-off** ว่าสองเกณฑ์บนตัวเลขเดียวกัน (0 กับ −10) ควรรวมเป็นเกณฑ์เดียวหรือไม่ |
| 🔴 **นิยาม "ยอด 0 กี่งวดติดกัน"** | ตรรกะ **ไม่มีในระบบเดิมเลย** | ✅ **นิยามแล้ว 2026-09-13** — ดูด้านล่าง · 🔴 **ยังต้อง business sign-off** เพราะกระทบเงินโดยตรง |

### นิยาม "ยอดชดเชยเป็น 0 ติดกันกี่งวด" (2026-09-13)

ตรรกะนี้ **ไม่มีในระบบเดิมเลย** จึงไม่มีโค้ดให้เทียบ — นิยามที่เลือกใช้:

1. นับ **ถอยหลังจากงวดล่าสุดของรอบนั้น** เรียงตาม `compensate_month DESC`
2. งวดนับเป็น "ศูนย์" เมื่อ `COALESCE(adjust_amount, forecast_amount) = 0`
3. **`NULL` (ยังไม่คำนวณ) ตัดสายการนับ** — ไม่ใช่ศูนย์ เพราะยังไม่รู้ว่าเท่าไร
4. **งวดที่ไม่มีแถวก็ตัดสายการนับ** — ช่องว่างแปลว่าไม่ได้ชดเชยต่อเนื่อง

> 📌 **เหตุผลของข้อ 3 และ 4** — เลือกให้ "ไม่หยุดชดเชย" เมื่อข้อมูลไม่ชัด
> ผิดทางนี้คือจ่ายเกิน ซึ่งเรียกคืนได้ · ผิดอีกทางคือ**หยุดจ่ายคนที่ควรได้** ซึ่งกู้ยากกว่ามาก

ยืนยันกับ PostgreSQL 16 จริงแล้ว 3 เคส:

| ลำดับงวด (เก่า→ใหม่) | นับได้ | ผล |
|---|---|---|
| `0, 0, 0, 0` | **4** | เกินเพดาน 3 → **หยุดชดเชย** |
| `0, 0, 1000, 0` | **1** | ยอดที่ไม่ใช่ 0 ตัดสาย → เข้า state 08 ตามปกติ |
| `0, NULL, 0, 0` | **2** | **`NULL` ตัดสาย** → ยังไม่หยุด |
| 🔴 **`sales_status = 'E'` ทำอย่างไร** | Gate รับ `IN ('Y','N')` — `'E'` ไม่ผ่านและไม่ถูกตั้ง `N` | ✅ **ปิดแล้ว 2026-09-13 — คง `W` แต่แยกเหตุผลเป็น `SALES_ERROR`** · `'E'` แก้ได้ด้วยการรัน Job 5 ซ้ำ จึงเข้านิยาม "ข้อมูลยังไม่พร้อม" ไม่ใช่ "ไม่ผ่านถาวร" · ต่างจากเดิมตรงที่**นับแยกและขึ้น log ทุกรอบ** ไม่ค้างเงียบ ๆ |
| 🔴 **`opt_dv_user_id` ใครเติม และเติมอย่างไร** | ระบบเดิมเดาจากการจับคู่ชื่อเป็นสตริงย่อย + `rownum = 1` + `max()` | ✅ **ปิดแล้ว 2026-09-13 — Job 8 เป็นคนเติม** ผ่าน `fillMissingApprovers()` ที่ join `mas_store.dv_code` → `business_user.dv_code` ด้วย **`DISTINCT ON`** · **ไม่จับคู่ด้วยชื่อเลย** |
| 🔴 **`opt_dv_user_id` ว่าง → `N` หรือ `W`** | ระบบเดิมคง `W` · ผังใหม่ระบุให้เป็น `N` | ✅ **ปิดแล้ว 2026-09-13 — เลือก `W`** ตามหลักการที่ผังใหม่วางเอง (*"ข้อมูลยังไม่พร้อม → W"*) · DV ที่ยังไม่ถูกเติมเข้านิยามนั้นตรง ๆ และ Job 8 เติมให้ได้ในรอบถัดไป · ถ้าตั้ง `N` แล้ว DV ถูกเติมทีหลัง **เรื่องจะไม่มีวันกลับมา** ซึ่งเอกสารฉบับนี้เตือนไว้เอง · นับเป็น `waitingByReason.NO_DV_USER` + log warn ทุกรอบ |
| **เกณฑ์ `-10` เป็น literal** | ตัวเลขอยู่ในโค้ด SQL | ✅ **ปิดแล้ว** — `mas_param.SGI_GROWTH_RATE_MAX` (seed = `-10`) และ `SGI_ZERO_AMOUNT_MAX_MONTHS` (= `3`) มีอยู่แล้ว · ชุดประเภทร้าน 6 ค่าอยู่ที่ `SGI_JOB8B_BRANCH_TYPES` |
| **ชุดประเภทร้าน 6 ค่าของ Job 8b** | ไม่ตรงกับชุดของ Job 2 ที่มี `B` และ `FPT1` ด้วย | ✅ **ยืนยันจากข้อมูลจริงแล้ว — ตั้งใจให้ต่างกัน** · แถวค้าง `W` ในประวัติ **3,064 แถว** เป็น `B` 2,680 + `FPT1` 382 = **3,062 (99.9%)** คือร้านที่ Job 2 รับเข้ามาแต่ Job 8b ไม่รับ · ของใหม่ตั้ง `N` ให้ทันทีแทนที่จะปล่อยค้าง |
| **timeout ของการเรียก API** | ระบบเดิมไม่ตั้งเลย | ⏳ ต้องกำหนด connect/read timeout + retry policy |
| **ตัวกระตุ้น** | ผังระบุ `after-job-8` — ต้องเป็น AWS Batch dependency ไม่ใช่เวลาห่างกัน | ⏳ ระบุใน deployment |

---

## 11. กับดักในโค้ดเดิม — สิ่งที่ **ห้ามลอกไป** ระบบใหม่

| # | กับดัก | ที่มาในโค้ดเดิม | ระบบใหม่ต้องทำอย่างไร |
|---|---|---|---|
| **L1** | 🔴 **ตรวจสำเร็จด้วยการหาคำในข้อความ** | `startFlowProcess` — `responseString.contains("Running")` · `contains("Failure")` แค่ log | ใช้ **HTTP status + response body ที่มีโครงสร้าง** จาก `POST /sgi/workflow/instances` |
| **L2** | 🔴 **เมลรายงานผลถูก comment ทิ้ง** | `startFlow()` สร้าง `mailBody` ที่มีจำนวนสำเร็จ/ล้ม แล้ว `// SendMailUtil.sendEmail(...)` — **ไม่มีใครรู้ผลรายรอบ** | รายงานทุกรอบผ่าน structured log + metrics |
| **L3** | 🔴 **จับคู่ผู้จัดการเขตด้วยชื่อ** | `instr(mso.fullname, bu.first_name) > 0 and instr(mso.fullname, bu.last_name) > 0` + `rownum = 1` + `max()` | ผูกด้วย `emp_id`/`user_id` เท่านั้น |
| **L4** | **ไม่มี timeout / retry** | `HttpURLConnection` ไม่ตั้ง `setConnectTimeout`/`setReadTimeout` · เรียกทีละรายการ sequential | ตั้ง timeout + retry policy + พิจารณาเรียกแบบขนานมีขอบเขต |
| **L5** | **`N` ถูกตั้งจากเงื่อนไขเดียว** | `udateFlagNo()` ตั้ง `N` เฉพาะประเภทร้านไม่เข้าเกณฑ์ · G4/G5 ไม่เคยทำให้เป็น `N` → **ค้าง `W` ตลอดไป** | แยก **"ไม่ผ่านถาวร" → `N`** ออกจาก **"ข้อมูลยังไม่พร้อม" → `W`** ให้ชัด (ผังใหม่ทำแล้ว) |
| **L6** | **`updateBeforeSelect` ตั้ง `Y` โดยไม่เปิด workflow** | ถ้ามีแถวใน `fgi_impact_process` ถือว่าเปิดแล้ว · **ถ้ามีแถวค้างจากสาเหตุอื่นจะตั้ง `Y` ทั้งที่ไม่เคยเปิด** | ซ่อมสถานะได้ **แต่ต้องยืนยันกับ engine ว่ามี instance จริง** ไม่ใช่เดาจากตารางอื่น |
| **L7** | **credential ฝังในโค้ด** | `K2USER = "7ELEVEN\bpmk2_fcs:SupportGSSF2"` (`FgiConstant.java:23`) + HTTP Basic Auth | **service token จาก Secret Manager** · `DECISIONS` ข้อ **4.6** — credential เดิมต้อง rotate |
| **L8** | **ผู้รับอีเมลสรุป hardcode** | `mailto.add("go-sbp@gosoft.co.th")` 2 จุด | ผู้รับจาก config (`mas_param`/`email_template`) |
| **L9** | **อีเมล DV เอาจากแถวแรกของกลุ่ม** | `sendList.get(0).getOptDvUserEmail()` | ดึงอีเมลจาก master ด้วย `user_id` ไม่ใช่จากข้อมูลที่ join มา |
| **L10** | **`catch` แล้วแค่ log ใน `main`** | `catch (Exception e) { LogUtils.error(...); }` — ไม่มี exit code | exit non-zero เมื่อล้มเหลว (เหมือน Job 2 · L3) |

> ⚠️ **L1 + L2 รวมกันทำให้ job นี้ "เงียบสองชั้น"**
> ตรวจสำเร็จด้วยการหาคำ → ถ้า K2 เปลี่ยนข้อความ ระบบจะคิดว่าล้มทั้งหมด
> และเมลรายงานผลถูก comment ทิ้ง → **ไม่มีใครรู้ว่าไม่มีเอกสารใบไหนเข้า workflow เลย**
> เรื่องจะเงียบจนกว่าผู้จัดการเขตจะทักว่าไม่ได้รับงาน

---

## 12. อ่านต่อที่ไหน

| อยากรู้เรื่อง | อ่านที่ |
|---|---|
| Job 8 (สร้างเอกสาร · ต้องรันก่อน) | `batchjob/JOB-08-CreateCompensationDocument-อธิบายละเอียด.md` |
| Job 5 (ที่มาของ `growth_rate_diff` และ `sales_status`) | `batchjob/JOB-05-ImportImpactSaleFromIAS-อธิบายละเอียด.md` |
| Job 7 (gate ข้อมูลผู้อนุมัติรุ่นแรก) | `batchjob/JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md` |
| สเปกรูปแบบมาตรฐานของ Job 8b | `LLDD/md/Jobs/LLDD-BE-Job-8b-GenerateFlowToK2.md` |
| สัญญาการเรียก engine (8 functions) | `LLDD/md/BE/LLDD-BE-Workflow-Engine-Definition.md` · `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md` |
| endpoint ที่ job เรียก | `api.md` · `plan-api.html` → `POST /sgi/workflow/instances` |
| flow การอนุมัติ 5 ขั้น | `workflow.md` · `k2-flow.html` |
| โครงตารางเต็ม + DDL | `LLDD/md/LLDD-Database.md` · `output/sql/sgi_schema.sql` |
| ข้อค้างที่ยังไม่ตัดสิน | `DECISIONS-รอตัดสินใจ.md` |
