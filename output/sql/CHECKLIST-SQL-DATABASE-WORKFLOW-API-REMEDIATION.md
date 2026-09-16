# Checklist แก้ไข SQL ให้ตรงกับ Database / Workflow / API

> สร้างจากการตรวจเทียบ SQL ใน `output/sql/` กับ `database.md`, `workflow.md`, `api.md`,
> `LLDD/md/BE/LLDD-BE-Integration-SBP-Platform.md`,
> `LLDD/md/BE/LLDD-BE-Workflow-Engine-Definition.md` และ schema จริงของ `sps_store`
>
> **วันที่ตรวจล่าสุด:** 2026-09-16
> **ขอบเขต:** schema 20 ตารางใหม่ · ตารางเดิมที่ reuse · seed data · workflow setup · rollback · contract ของ API  
> **วิธีใช้:** แก้ตามลำดับ P0 → P1 → P2 และติ๊ก `[x]` เฉพาะเมื่อผ่านเกณฑ์ตรวจรับของข้อนั้นจริง  
> **ข้อควรระวัง:** `sgi_schema.sql` และไฟล์ที่ generate จาก DDL ต้องแก้ที่ source generator แล้วสร้างใหม่ ห้ามแก้เฉพาะ generated SQL

---

## ผลตรวจซ้ำล่าสุด 2026-09-16

> 🔴 **สถานะรวม: BLOCKED — ชุด SQL ยังไม่พร้อมใช้เป็น Production release package**
> DDL หลักติดตั้งได้จริงและ SQL ของ Batch ที่ตรวจได้อ้างตาราง/คอลัมน์ถูกต้อง แต่ยังมี blocker ที่
> API lookup, workflow definition, concurrent seed, rollback/cleanup และความตรงของ test stub กับฐานจริง

| พื้นที่ | สถานะ | ผลที่ยืนยันได้ | สิ่งที่ยังปิดไม่ได้ |
|---|---|---|---|
| Schema 20 ตาราง | **PASS WITH ACTION** | PostgreSQL 16 สร้าง 20 ตาราง · 24 secondary index · 28 FK · ทุกตารางมี PK | FK ฝั่งลูก 3 เส้นไม่มี leading index และ SQL ตรวจจำนวน index แค่ `NOTICE` ไม่ fail |
| Seed | **BLOCKED** | fresh install ได้ `common_code_type` 3 · `common_code` 14 · `mas_param` 11 · template 8; sequential rerun ไม่เพิ่ม | concurrent rerun สร้าง `common_code` 28 แถว (duplicate 14 key) และ template 16 แถว (duplicate 8 key) |
| Rollback | **PARTIAL** | รันซ้ำ 2 ครั้งได้; ตาราง/index/sequence `sgi_*` เหลือ 0 ในฐาน isolated | ไม่ลบ seed; header/cleanup ตก `common_code_type` และ `SGI_APPROVE_LIMIT`; `CASCADE` ยังไม่ผ่าน dependency audit ใน environment จริง |
| Workflow | **BLOCKED** | contract ระบุ 6 state/status และ 12 route | ไม่มี deployable definition/version, ID binding, rollback หรือ E2E test; เอกสารยังขัดกันเรื่อง threshold |
| API 28 เส้น | **BLOCKED** | static catalog/count/links ผ่าน 28 เส้น 6 กลุ่ม | ไม่มี SGI module ใน BE และ SQL ของ lookup 2 เส้นยังใช้ schema/field ผิด |
| Batch SQL | **PASS WITH LIMIT** | PostgreSQL `PREPARE` ผ่าน 75 จาก 90 คำสั่ง | ข้าม SQL Server 6 · prose 2 · dynamic fragment 7; ไม่ได้พิสูจน์ runtime behavior ของคำสั่งที่ข้าม |
| Generator drift | **PASS** | schema/seed/rollback/stub ตรงกับ generator แบบ byte-for-byte | generator เป็นแหล่งของ defect ที่พบด้วย จึงต้องแก้ generator ก่อน regenerate |
| Automated test harness | **PARTIAL** | `check_docs.py` ผ่าน 106 ไฟล์ | stub ใส่/ขาด PK ไม่ตรงฐานจริง และ checker ไม่ fail จาก subprocess return code ทุกกรณี |

### หลักฐานที่รันจริงในรอบนี้

```text
python3 tools/check_docs.py                         PASS · 106 files
generator → temp + cmp                             PASS · 4/4 files identical
PostgreSQL 16: stub → schema                       PASS · tables=20 indexes=24
PostgreSQL 16: seed → seed                         PASS · sequential counts unchanged
concurrent seed (partial-state simulation)         FAIL · codes=28/dup=14 · templates=16/dup=8
python3 tools/check_sgi_sql_columns.py              PASS · 75/90 prepared
API lookup SQL against real workflow column shape  FAIL · 2/2 queries
rollback → rollback                                PASS isolated · SGI objects=0; shared seed remains
```

ไม่ได้ rerun Jest ในรอบนี้ เพราะ checkout ไม่มี `node_modules/.bin/jest` และ `npx` ไม่สามารถเริ่มชุดทดสอบได้;
ตัวเลข `41 suites / 662 tests` และ `25 suites / 249 tests` ด้านล่างเป็นหลักฐานจากรอบ 2026-09-15
ไม่ใช่ผลยืนยันของ source snapshot วันที่ 2026-09-16

### Blocker ใหม่ที่ต้องแก้ก่อน Production

1. **P0-API-02:** SQL lookup ใช้ `workflow_status.seq` ที่ไม่มีจริง และอ่านวงเงินคนละ key/column กับ seed
2. **P1-MIG-01:** `WHERE NOT EXISTS` กันซ้ำได้เฉพาะ sequential run; concurrent run สร้าง duplicate ได้จริง
3. **P1-RBK-01:** รายการ residue/cleanup ตก `common_code_type` และ `SGI_APPROVE_LIMIT`; ตัวเลข header ค้างเวอร์ชันเก่า
4. **P1-DB-01:** FK 3 เส้นไม่มี leading index สำหรับ parent update/delete และ reverse lookup
5. **P1-TEST-01:** test stub ไม่สะท้อน key จริงของ `common_code_type`/`mas_param`
6. **P2-DOC-02:** living docs/LLDD ยังขัดกับ DDL/seed เรื่อง `approver_snapshot`, threshold source และ seed owner

---

## ✅ ติดตั้ง `sgi_schema.sql` ลงฐาน dev จริงแล้ว — 2026-09-16

> เป็นครั้งแรกที่ schema ของ SGI อยู่บนฐานจริงของโครงการ · ปิดข้อ *"ยังไม่เคยรันกับฐาน dev จริง"*
> ที่ค้างใน `CLAUDE.md` มาตั้งแต่ต้น

| | |
|---|---|
| ฐาน | `srm-sps-...-dev-new-instance-1` · **PostgreSQL 17.7** · schema `sps_store` |
| เครื่องมือ | **`tools/apply_sgi_sql.py`** (ใหม่) — ไม่ใส่ `--confirm` = dry-run |
| ผลลัพธ์ | **20 ตาราง · 24 index · 20 PK · 28 FK · 26 CHECK · generated column 2 ตัว** |
| ตารางของระบบเดิม | **205 ตารางเท่าเดิม ไม่ถูกแตะ** |
| ข้อมูล | ทุกตาราง `sgi_` **ว่าง** (ยังไม่ได้รัน seed) |
| ถอนกลับ | `output/sql/sgi_schema_rollback.sql` |

### guard 4 ข้อที่ตรวจก่อนยิงทุกครั้ง

1. **ไฟล์ตรงกับ generator** — generate ใหม่ลง temp แล้วเทียบไบต์ · กันการรันไฟล์ที่ถูกแก้ด้วยมือ
2. **ทุก `CREATE`/`ALTER TABLE` แตะเฉพาะตาราง `sgi_`** — กันการแตะระบบเดิมโดยไม่ตั้งใจ
3. **ไม่มี `DROP`/`TRUNCATE`/`DELETE`/`UPDATE`** นอกขอบเขต (ไฟล์ rollback ได้รับการยกเว้นเฉพาะ `sgi_`)
4. **อยู่ในทรานแซกชันเดียว** — พังกลางทางต้องไม่เหลือขยะ (ทดสอบด้วยการฉีดข้อผิดพลาดแล้ว)

แล้วรายงาน **สภาพฐานก่อน–หลัง** ให้เทียบได้ว่าอะไรเปลี่ยนไปบ้างจริง ๆ

### ⚠️ ยังไม่ได้รัน `sgi_seed_data.sql` บน dev

ฐาน dev **มีแถว SGI ที่ทีมอื่น seed ไว้ตั้งแต่ 2026-08-27** (`SGI-SETUP` · `common_code` 1 · `mas_param` 4)
seed ของเราปรับให้ใช้ชื่อ/ค่าชุดเดียวกับของที่ติดตั้งแล้ว และ**ทดสอบบนฐานจำลองว่าไม่เกิดแถวซ้ำ**
แต่การยิงลงฐานจริงต้องมีคนสั่งอีกครั้ง

---

## 🔬 ตรวจ `output/sql/` เชิงลึก — 2026-09-16 (เทคนิคใหม่ 5 อย่าง)

ที่ผ่านมาตรวจไฟล์ชุดนี้ด้วยการ "ติดตั้งแล้วดูว่าผ่าน" · รอบนี้ใช้วิธีที่ยังไม่เคยใช้

### 🔴 เจอของจริง — `.sql` บนดิสก์ค้างเวอร์ชันเก่า

**determinism test** (generate ใหม่ลง temp แล้วเทียบไบต์ต่อไบต์) พบว่า `sgi_schema.sql`
ยังมี `23,958,780` ทั้งที่ generator ให้ `24,284,545` แล้ว — **แก้ generator แล้วลืม regenerate**

⚠️ กฎ `#91` ที่มีอยู่ตรวจ**เชิงโครงสร้าง** (มี `CREATE TABLE` ครบไหม) จึงมองไม่เห็น comment ที่ตกยุค
✅ เพิ่ม **กฎ #112** ใน `check_docs.py` — generate ลง temp แล้วเทียบทุกไบต์ · **tamper-test แล้ว**:
แก้ `.sql` ด้วยมือหนึ่งบรรทัด กฎจับได้ทันทีและบอกวิธีแก้

### ✅ ติดตั้งบน PostgreSQL 17 — รุ่นเดียวกับ dev จริง

ที่ผ่านมาทดสอบบน `postgres:16-alpine` ตลอด · รอบนี้ยก **PostgreSQL 17.11** ขึ้นมาทดสอบ
ได้ **20 ตาราง · 24 index · 28 FK · common_code 14 · mas_param 11** ตรงกับที่คาดทุกตัว
→ ปิดช่องว่างที่ตัวเองเพิ่งพบเมื่อรู้ว่า dev เป็น 17.7

### ✅ preflight guard ยิงจริง (ไม่ใช่แค่มีโค้ด)

| ทดสอบ | ผล |
|---|---|
| รัน `sgi_schema.sql` ซ้ำทั้งที่มีตาราง `sgi_` อยู่ | ✅ หยุด · *"มีตาราง sgi_ อยู่แล้ว 20 ตาราง — สคริปต์นี้สำหรับติดตั้งครั้งแรกเท่านั้น"* |
| ซ่อนตาราง `common_code_type` แล้วรัน seed | ✅ หยุด · *"ไม่พบตาราง common_code_type — ต้องลงทะเบียน code type ก่อน"* |

### ✅ atomicity — ฉีดข้อผิดพลาดกลางไฟล์

| ไฟล์ | จุดที่ฉีด | ผลลัพธ์ |
|---|---|---|
| `sgi_schema.sql` | ก่อน `CREATE TABLE` ตัวที่ 10 | **เหลือ 0 ตาราง** ✅ |
| `sgi_seed_data.sql` | ก่อน `INSERT INTO mas_param` ตัวแรก | **เหลือ 0 แถวทุกตาราง รวมของระบบเดิม** ✅ |

⚠️ รอบแรกอ่านผลผิดเพราะลืมล้างแถวที่ค้างจากการติดตั้งสำเร็จก่อนหน้า (rollback ไม่ลบแถวในตารางระบบเดิม
ตามที่ออกแบบไว้) — ต้องล้างก่อนถึงจะตีความได้

### ✅ คุณภาพ index — วัดด้วย EXPLAIN บนข้อมูลระดับจริง

สร้างข้อมูลสังเคราะห์ **processes 24,000 · impact_stores 72,000 · compensations 24,000 ·
interface_transactions 40,000** แล้ว `ANALYZE` + `EXPLAIN (ANALYZE)` คิวรีหลักของแต่ละ job

| คิวรี | แผน | ผล |
|---|---|---|
| Job 4 หาคู่ร้านที่ต้องขอยอดขาย | Index Scan `idx_impact_store_process` | ✅ |
| Job 2 กวาดแถวค้าง `W` | Bitmap Index Scan `idx_impact_store_verify_wait` (partial index) | ✅ |
| Job 8 หารอบที่พร้อมสร้างเอกสาร | Seq Scan บน `sgi_fgi_impact_processes` | **1.8 ms** |
| Job 6 กรอง `impact_month + flag_action` | Seq Scan | **9.1 ms** |
| Job 10 หาแถวขาออกค้าง | Seq Scan (14,243 จาก 40,000 แถว) | เลือกถูกแล้ว — selectivity ต่ำ index ไม่ช่วย |

⏭️ **ไม่เพิ่ม index** — `sgi_fgi_impact_processes` ไม่มี index บน `impact_month`/`process_status` จริง
แต่ **วัดแล้วได้ 9 ms ที่ 24,000 แถว** และ job พวกนี้รันเดือนละครั้ง · เพิ่ม index = ภาระตอนเขียน
โดยไม่มีใครได้ประโยชน์ตอนอ่าน · ถ้าตารางโตถึงระดับล้านแถวค่อยกลับมาดู (เวลาโตเชิงเส้น)

### ✅ ตรวจแล้วไม่พบปัญหา

| ตรวจอะไร | ผล |
|---|---|
| index ซ้ำซ้อน (ตัวที่เป็น prefix ของอีกตัว) | 0 จุด |
| rollback บน PostgreSQL 17 | เหลือ 0 ตาราง · 0 sequence · 0 index · แถวในตารางระบบเดิม 14 แถวคงไว้ตามที่ออกแบบ |
| determinism หลังแก้ | 4/4 ไฟล์เหมือนเดิมทุกไบต์ |

---

## ✅ ตรวจเอกสารทั้งชุดกับข้อมูลจริงจากฐานสองฝั่ง — 2026-09-16

เครื่องมือใหม่ **`tools/check_docs_vs_db.py`** — ต่างจาก `check_docs.py` ตรงที่ตัวนั้นตรวจ
**ความสอดคล้องภายในเอกสารเอง** ส่วนตัวนี้ตรวจว่า **สิ่งที่เอกสารอ้างว่าเป็นจริงในฐาน ยังจริงอยู่ไหม**
โดยอ่านจาก `output/legacy-oracle/data.json` (As-Is) + `output/legacy-sgi/data.json` (dev ปลายทาง)
ตรงกับที่รอบตรวจ 2026-09-16 ขอไว้ใน P0-API-02 ("เพิ่มตัวตรวจ SQL ของ FE/BE LLDD กับ schema ระบบเดิม")

ตรวจเอกสาร **103 ไฟล์** · 5 หมวด:

| หมวด | พบครั้งแรก | หลังแก้ |
|---|---|---|
| จำนวนแถวของตารางระบบเดิมที่เอกสารอ้าง | 52 | **⚠️ 0** (เตือน ไม่ใช่ล้ม) |
| ข้ออ้างเรื่อง PK / index | 4 | ✅ 0 (เป็น false positive ทั้งหมด) |
| คอลัมน์ที่ SQL ในเอกสารอ้าง | 0 | ✅ 0 |
| ชื่อ/ค่า SGI ที่ติดตั้งลงฐานแล้ว | 6 | ✅ 0 |
| ความยาวรหัสร้านในฐาน Oracle | 0 | ✅ 0 |

### สิ่งที่แก้

- **ตัวเลขจำนวนแถว 169 จุด** ใน 29 ไฟล์ อัปเดตเป็นค่าที่วัดสด (`workflow_transaction` 19,283→19,327 ·
  `common_code` 2,609→2,628 · `email_sent` 5,214→5,392 · `fcs_qssi_score` 23.96M→24.28M ·
  `business_user` 12,752→12,759 · `mas_param` 93,752→93,756 · `workflow_approver` 96,542→99,198 ·
  `workflow_history` 38,010→38,136 · `email_template` 85→126 · `common_code_type` 376→378)
- เพิ่ม **หมายเหตุวันที่วัด** ในเอกสาร — ฐาน dev ยังมีระบบเดิมใช้งานอยู่ ตัวเลขจึงขยับทุกวัน
  ระบุให้ชัดว่าใช้ดู**ขนาดของปัญหา** ไม่ใช่ตัวเลขที่ต้องตรงเป๊ะ
- **ชื่อ/ค่า SGI ที่เหลือ 6 จุด** — `batchjob/JOB-02` · `JOB-08b` ยังใช้ชื่อเก่า และ `'THRESHOLD'`
  ยังค้างใน `plan-api.html` + LLDD 3 ฉบับ · แก้ให้ตรงกับที่ติดตั้งในฐาน dev ทั้งหมด
- เพิ่ม fallback ของ glyph `⏭` ใน `pdf_safe_text()` (ไม่งั้นขึ้นเป็นกล่องใน PDF — `check_docs.py` จับได้)

### 🔴 บทเรียน — ตัวตรวจที่เตือนผิดแย่กว่าไม่มีตัวตรวจ

รอบแรกตัวตรวจรายงาน **62 จุด** แต่ไล่ดูแล้วพบว่าหลายจุด**เป็นบั๊กของตัวตรวจเอง**:

| อาการ | สาเหตุ | แก้อย่างไร |
|---|---|---|
| อ้างว่า `workflow_approver`/`workflow_route` ไม่มี PK (ของจริงมี) | regex ใช้ `re.S` จับข้ามบรรทัด แล้วโยงข้อความ "ไม่มี PK" ของ `workflow_transaction` มาใส่ตารางอื่น | เลิกใช้ `re.S` · จับในบรรทัดเดียว |
| `workflow_group_map` ว่า 1,646 แถว (จริง 11) | แถวตารางใน markdown มีหลายคอลัมน์บนบรรทัดเดียว เลขของตารางอื่นถูกดึงมา | ข้ามเมื่อมีชื่อตารางอื่นคั่นอยู่ · ลดหน้าต่างเหลือ 60 ตัวอักษร · ไม่ข้าม `\|` |
| `mas_store` ว่า 23,120 แถว (จริง 19,647) | ประโยคพูดถึง `mas_store.status_type` แล้วมีเลขของฝั่ง Oracle ตามมา | เพิ่ม `(?!\.)` — ถ้าตามด้วยจุด แปลว่าพูดถึง**คอลัมน์** ไม่ใช่จำนวนแถว |
| `'THRESHOLD'` ในบรรทัดที่อธิบายว่า "เดิมเขียนแบบนี้" | จับทุกที่ที่เจอคำ | ข้ามบรรทัดที่เอ่ยทั้งค่าเก่าและค่าใหม่ = เป็นคำอธิบายประวัติ |

หลังแก้ตัวตรวจ: false positive **0** · เหลือแต่ของจริง
และแยก **จำนวนแถว = คำเตือน** ออกจาก **ข้ออ้างเชิงโครงสร้าง = ความล้มเหลว** เพราะอย่างแรกขยับเองได้
ส่วนอย่างหลังไม่ควรเปลี่ยนโดยไม่มีคนตัดสินใจ

---

## 🔴 ผลตรวจกับ **ฐาน dev จริงของโครงการ** — 2026-09-16

> เป็นครั้งแรกที่ตรวจกับฐาน dev จริง (ก่อนหน้านี้ทดสอบบน docker `postgres:16-alpine` เท่านั้น)
> **อ่านอย่างเดียว ไม่ได้เขียนอะไรลงฐาน** · เครื่องมือใหม่ `tools/introspect_dev_sgi.py`
> ผลเต็มอยู่ที่ `output/legacy-sgi/` (gitignore เพราะมีข้อมูลธุรกิจจริง)

### ✅ ยืนยันว่า stub และ dump ถูกต้อง

| ตรวจอะไร | ผล |
|---|---|
| คอลัมน์ 13 ตารางที่ stub จำลอง เทียบ `SBP/db-schema-sps_store.md` | **ตรงกันครบ 256 คอลัมน์ ไม่ผิดสักจุด** |
| PK ของ 13 ตาราง | **ตรงกับ stub ที่แก้วันนี้เป๊ะ** — `mas_param`·`juristic`·`mas_zone`·`business_user`·`fr_store`·`workflow_transaction` ไม่มี PK จริง · `common_code_type` มี PK จริง |
| `workflow_status.seq` | **ไม่มีจริง** — ยืนยัน P0-API-02 |
| ตาราง `sgi_` ในฐาน | **0 ตาราง** → preflight ผ่าน ติดตั้งใหม่ได้ |

### 🔴 สามเรื่องที่เปลี่ยนการตัดสินใจ

**1 · มีคน seed ค่า SGI ลง dev ไปแล้วเมื่อ 2026-08-27** (เจ้าของ `SGI-SETUP`) ด้วยชื่อคนละชุดกับ seed ของเรา

| ในฐาน dev จริง | seed ของเรา (ก่อนแก้) |
|---|---|
| `SGI_SALES_DAYS_MIN` · `SGI_GROWTH_RATE_MAX` · `SGI_IMPACT_RADIUS_BKK` · `_UPC` | `SGI_SALES_DATA_MIN_DAYS` · `SGI_GROWTH_RATE_THRESHOLD` · `..._BKK_KM` · `..._UPC_KM` |
| `SGI_APPROVE_LIMIT` · `code_value = '100000'` | `code_value = 'THRESHOLD'` (ตาม LLDD §5.5.2) |

✅ **แก้แล้วตามมติผู้ใช้ — ยึดของที่ติดตั้งจริง** · `SEED_OWNER` เปลี่ยนเป็น `SGI-SETUP` ด้วยเพื่อให้คำสั่งล้างครอบของเดิม
🔴 **นี่พลิกข้อสรุป P1-PARAM-01 ของรอบ 2026-09-15** ที่เลือก "ยึดชื่อใน SQL เพราะเป็นชุดที่ติดตั้งจริง" —
เหตุผลนั้นผิด เพราะตอนนั้นยังเข้าฐาน dev ไม่ได้ · **ของที่ติดตั้งจริงคือชื่อในเอกสาร**
⚠️ contract ใน `LLDD-BE-Integration-SBP-Platform` §5.5.2 (`code_value='THRESHOLD'`) **ขัดกับของที่ติดตั้ง** — ต้องให้เจ้าของเอกสารเคาะว่าจะแก้ contract หรือแก้ข้อมูลในฐาน

**พิสูจน์แล้ว:** จำลองฐานที่มีของเดิม 2026-08-27 อยู่ก่อน แล้วรัน seed ใหม่ → `SGI_APPROVE_LIMIT` เหลือ **1 แถว** (ไม่ซ้ำ) · `mas_param` SGI_* = **11 ไม่ใช่ 15**

**2 · 🔴 โซนสำหรับหาผู้รับอีเมลของ Job 8b/12 join ไม่ติดเลยในฐาน dev**

```
mas_store.zone_cd      = 10, 21, 70, 84, 85     (ว่าง/NULL 19,641 จาก 19,647 แถว)
business_user.zone_cd  = 72, 73, 75, 76         (ว่างทั้ง zone_cd และ zone_code 9,819 จาก 9,833)
ค่าที่ซ้อนกัน            = 0
```

`bu.zone_cd = ms.zone_cd` ที่ Job 8b และ Job 12 ใช้ **หาผู้รับไม่เจอสักคน** → Job 12 จะจบเป็น `FAILED`
ทุกรอบเพราะ `zonesWithoutRecipient` · `business_user` ยังมีคอลัมน์ `zone_code` (ตัวอักษร `BE`/`BN`/`RC`…)
เป็นอีกระบบรหัสหนึ่ง และค่าที่มีอยู่ยังมีช่องว่างต่อท้ายไม่สม่ำเสมอ (`'84         '`)
✅ **ข่าวดี:** `group_id` 15 = **1,856 คน** · 38 = **20 คน** มีจริงทั้งคู่
🔴 **ต้องเคาะกับเจ้าของ auth-backend** ว่าจะหาผู้รับด้วยอะไรแทน — ข้อค้าง **E3** ใน `batchjob/JOB-02-12-...md`

**3 · 🔴 dev เป็น PostgreSQL 17.7 ไม่ใช่ 16**

ชุดทดสอบทั้งหมด (`check_sgi_sql_columns.py` · `__svc__` · lifecycle) รันบน `postgres:16-alpine`
ต้องรันซ้ำบน 17 ก่อนขึ้น UAT · `CLAUDE.md` ก็ระบุ 16 ไว้ตลอด

### ℹ️ workflow engine ในฐาน dev (ข้อมูลสำหรับ P0-WF-01)

`workflow` 1 · `workflow_version` **2** (version 6 = หนังสือขอความร่วมมือ · version 9 = การแจ้งประเมิน) ·
`workflow_state` 20 · `workflow_status` 31 · `workflow_event` 6 · `workflow_route` 43 · `workflow_transaction` **19,327**
→ **ยังไม่มี version ของ SGI** ต้องขอใหม่จากทีม engine ตามที่บันทึกไว้ · และยืนยัน DP-2 ว่า `workflow_transaction` ไม่มี PK จริง

---

## สรุปรอบแก้ 2026-09-16 (ตอบผลตรวจ 2026-09-16)

| Blocker ที่รอบตรวจระบุ | ผล |
|---|---|
| **P0-API-02** lookup SQL ใช้คอลัมน์ที่ไม่มี | ✅ **แก้แล้ว** · ถูกต้องทั้งสอง query · แก้ที่ `SQL_BY_PATH` ใน `plan-api.html` แล้ว regenerate · **รันจริงบน PostgreSQL 16 ผ่านทั้งคู่** |
| **P1-MIG-01** concurrent seed สร้างแถวซ้ำ | ✅ **แก้แล้วด้วย `pg_advisory_xact_lock`** · พิสูจน์ก่อนแก้ (2 แถว) และหลังแก้ (1 แถว) |
| **P1-RBK-01** residue/cleanup ตก `common_code_type` · ตัวเลขค้าง | ✅ **แก้แล้ว** — เป็นความพลาดของรอบ 09-15 เอง |
| **P1-TEST-01** stub ไม่สะท้อนฐานจริง | ✅ **แก้แล้ว** — stub อ่าน PK จาก dump แทน hardcode · **ร้ายกว่าที่ระบุ: PK ปลอม 4 ตาราง + ตกของจริง 1 ตาราง** |
| **P1-DB-01** FK 3 เส้นไม่มี index | ⏭️ **ยังไม่ทำ** — ไม่มีโค้ดลบแถวแม่ และคอลัมน์เหล่านั้นเขียนอย่างเดียว · ควรเคาะตอนเขียน runbook migration |
| **P2-DOC-02** contract drift ที่เหลือ | ⏭️ **ยังไม่ทำ** — ต้องไล่ตรวจทีละข้อก่อน (รอบก่อนพบว่า 2 ใน 3 ข้อที่เช็กลิสต์ระบุ ไม่ตรงข้อเท็จจริง) |

### สิ่งที่พบเพิ่มเองระหว่างแก้

- **stub ที่ PK ไม่ตรงของจริงบังบั๊กไว้ทั้งสองทาง** — `mas_param` มี PK ปลอมทำให้ race ที่ของจริงเกิดได้ถูกซ่อน
  ส่วน `common_code_type` ที่ของจริงมี PK แต่ stub ไม่มี ทำให้เทสหลวมกว่าจริง
  **พอแก้ stub ให้ตรง บั๊ก concurrent seed ก็โผล่ทันที** — สองข้อนี้เกี่ยวกันโดยตรง
- `check_docs.py` จับได้เองว่าพอ lookup SQL เปลี่ยนไปอ่าน `common_code` แล้ว Reference DB Mapping
  ยังประกาศตารางเก่า — แก้ตามแล้ว

### ผลตรวจรับที่รันจริงรอบนี้

```
ติดตั้งสด PostgreSQL 16: stub → schema → seed        ✅
lookup SQL ทั้ง 2 query รันจริง                       ✅ สถานะ 6 · ขั้น 5 · วงเงิน 100000
concurrent seed (2 session พร้อมกัน)                  ✅ 3/14/11/8/11 ตรงเป๊ะ ไม่มีแถวซ้ำ
race test บน mas_param: ไม่มี lock → 2 แถว · มี lock → 1 แถว   ✅
python3 tools/check_docs.py                          ✅ ผ่านทุกข้อ
python3 tools/check_sgi_sql_columns.py               ✅
npx jest src/modules/sgi/                            ✅ 41 suites / 662 tests
npx jest -c jest.svc.config.js                       ✅ 25 suites / 249 tests
```

> ⚠️ รอบตรวจ 2026-09-16 ระบุว่ารัน Jest ไม่ได้เพราะไม่มี `node_modules` — **รันได้แล้วในรอบนี้**
> ผ่าน sandbox ที่ลง dependency จาก `registry.npmjs.org` (CodeArtifact token ยังหมดอายุอยู่)
> ตัวเลข 662/249 ข้างบนเป็นผลของ source ณ 2026-09-16 ไม่ใช่ของเก่า

---

## สถานะตั้งต้นจากรอบตรวจ

- [x] `python3 tools/check_docs.py` ผ่าน — ตรวจ 106 ไฟล์ ไม่พบ error จากกฎที่มีอยู่
- [x] `sgi_schema.sql` รันบน PostgreSQL 16 ได้ — สร้าง 20 ตารางและ 24 secondary index
- [x] `sgi_seed_data.sql` รันได้ — competitor 11 · factor 4 · code type 3 · common code 14 · parameter 11 · email template 8
- [x] รัน seed ซ้ำแบบ sequential แล้วจำนวนแถวไม่เพิ่ม
- [ ] รัน seed พร้อมกันได้อย่างปลอดภัย — **ไม่ผ่าน**: ทดสอบ 2 session แล้ว duplicate `common_code` 14 key และ template 8 key
- [x] `sgi_schema_rollback.sql` รันได้สองครั้งโดยไม่ error
- [x] P0 — ย้าย `SGI_APPROVE_LIMIT` จาก `mas_param` ไป `common_code` — **แก้ที่ generator แล้ว ติดตั้งจริงผ่าน**
- [x] P0 — เพิ่ม `common_code_type` — **ลง 3 type แล้ว (`SGI_DECISION` · `SGI_DOC_STATUS` · `SGI_APPROVE_LIMIT`)** · `SGI_DATASOURCE` รอเคาะชุดค่า
- [ ] P0 — เพิ่ม seed `SGI_DATASOURCE`
  > ⏭️ **ไม่ทำ** — เช็กลิสต์ข้อนี้เริ่มด้วย "ขอ business sign-off" เอง · เดาชุดค่าแล้วผิดจะทำให้ dropdown และ validation ปฏิเสธข้อมูลจริง
- [ ] P0 — จัดทำ workflow definition/version และผูก email template ให้ครบ
  > ⏭️ **ไม่ทำ** — ต้องได้ `version_id` จากทีม `@srm/glb-workflow` ก่อน · และมติ 2026-09-09 ให้ **BE เป็นผู้เรียก engine ที่เดียว** งานนี้จึงไม่ใช่ของ `output/sql/` ฝั่ง batch
- [ ] P1 — ทำชื่อ parameter และ consumer ให้ตรงกัน — ชื่อเก่าถูกล้างแล้ว แต่ Batch อ่านจริง 6/11 key; อีก 5 key ยังไม่ถูก consume และบางค่ามี env fallback
- [ ] P1 — ทำ migration/seed/rollback ให้รองรับการเปลี่ยนค่าและ deploy ซ้ำอย่างปลอดภัย
  > 🔴 **rollback ลบ SGI objects ได้ แต่ residue/cleanup/dependency audit ยังไม่ครบ · desired-state/concurrent migration ยังไม่ผ่าน** (ดู P1-MIG-01/P1-RBK-01)
- [ ] P1 — เติม email body จริงและตรวจการส่งเมลซ้ำ
  > ⏭️ **ไม่ทำ** — เนื้อหาอีเมลถึงคนจริง ต้องให้ธุรกิจเขียนและอนุมัติ · โครงสร้าง seed 8 แถวพร้อมรับเนื้อหาแล้ว
- [ ] P1 — ล้างข้อขัดแย้งใน `database.md`, `workflow.md`, `api.md`, HTML และ LLDD — F1/F8 แก้แล้ว แต่ยังพบ contract drift ใหม่ใน P0-API-02/P2-DOC-02
- [x] P2 — แก้จำนวนตาราง/index และ comment ที่ตกยุค — **ผิดจริง 4 จุด แก้ครบ** (23→24 index · 19→20 ตาราง · 9→12 ค่า `data_name` · 6→7 ผลการพิจารณา)
- [ ] Final — ชุดติดตั้งใหม่ผ่าน schema, seed, workflow, API contract และ rollback test ครบ
  > 🔴 **ผ่านเฉพาะ schema + sequential seed + isolated rollback** · concurrent seed และ API lookup ไม่ผ่าน · workflow definition/BE ยังไม่มี

---

## สรุปรอบแก้ 2026-09-15 (ประวัติ — ให้ยึดผลตรวจ 2026-09-16 ด้านบนเมื่อขัดกัน)

| กลุ่ม | แก้แล้ว | ไม่แก้ (มีเหตุผลกำกับทุกข้อ) |
|---|---|---|
| **P0** | CFG-01 ย้ายวงเงินไป `common_code` · CFG-02 ลงทะเบียน `common_code_type` | CFG-03 `SGI_DATASOURCE` (รอ business) · WF-01 workflow definition (รอทีม workflow) |
| **P1** | DOC-01 ถ้อยคำ 20/21 · DOC-02 F1/F8 | PARAM-01 consumer coverage · MIG-01 desired-state/concurrency · MAIL-01 เนื้อหาอีเมล · RBK-01 cleanup |
| **P1 ที่ตรวจแล้วไม่ต้องแก้** | DOC-03 `status_email_rules` · DOC-04 Job 11 model — **เกณฑ์ตรวจรับผ่านอยู่แล้ว** | — |
| **P2** | DOC-01 จำนวนตาราง/index · SQL-01 comment `data_name` | API-01 lookup SQL validation · DOC-02 contract drift |

**ทุกอย่างแก้ที่ source generator แล้ว regenerate — ไม่มีการแก้ `.sql` ด้วยมือ**

### ที่พบว่าเช็กลิสต์ระบุไม่ตรงข้อเท็จจริง

| ข้อ | เช็กลิสต์ระบุ | ตรวจแล้วพบว่า |
|---|---|---|
| P1-DOC-03 | เอกสารยังเขียนว่าส่งเมลตาม `status_email_rules` | ทุกจุดอยู่ในบริบท **"ถูกยกเลิกแล้ว"** · `workflow.md:149` ระบุ source เดียว (`workflow_route.email_id`) และผู้ส่งฝ่ายเดียวไว้ครบ |
| P1-DOC-04 | เอกสารกล่าวปะปน 3 แบบเรื่อง execution model ของ Job 11 | เอกสารกับโค้ดตรงกัน (**consume เอง** · มติ 2026-09-12) · คำว่า `SubmitJob` ที่เจอมาจากเอกสารวิเคราะห์ **repo อื่น** |
| P1-DOC-01 | ต้องเพิ่มแถว Data Dictionary ของ `sgi_fgi_new_store_compensations` | พจนานุกรม **generate จาก DDL ชุดเดียวกัน** ตารางนี้อยู่ในนั้นอยู่แล้ว — เพิ่มด้วยมือจะสร้างแหล่งความจริงที่สอง |

### ผลตรวจรับที่รันจริง

```
ติดตั้งสด PostgreSQL 16: stub → schema → seed       ✅ ผ่านทั้งสามไฟล์
common_code_type 3 · common_code 14 · mas_param 11   ✅ sequential (APPROVE_LIMIT เหลือ 0 ใน mas_param)
รัน seed ซ้ำ                                          ✅ จำนวนเท่าเดิมทุกตาราง
python3 tools/check_docs.py                          ✅ ผ่านทุกข้อ
python3 tools/check_sgi_sql_columns.py               ✅ 75 คำสั่ง
npx jest src/modules/sgi/                            ✅ 41 suites / 662 tests
npx jest -c jest.svc.config.js                       ✅ 25 suites / 249 tests
```

> บล็อกผลข้างบนเป็นผลจากรอบ 2026-09-15; รอบ 2026-09-16 rerun เฉพาะรายการในหัวข้อ
> “หลักฐานที่รันจริงในรอบนี้” และพบ concurrency/API/test-harness gap เพิ่มเติม

> ⚠️ **ไฟล์นี้อยู่ใน `output/sql/` ซึ่งตามกติกาโครงการเป็นโฟลเดอร์ที่ generate ทับได้**
> ถ้าจะเก็บระยะยาวควรย้ายไปที่ `batchjob/` หรือรากโปรเจกต์ ไม่งั้นมีโอกาสหายตอน regenerate

---

## P0 — ต้องแก้ก่อนติดตั้ง Production

### P0-CFG-01 — ย้ายวงเงินอนุมัติไป `common_code`

> ✅ **แก้แล้ว 2026-09-15 — ส่วนที่เป็น SQL ทำครบ**
> ย้าย `SGI_APPROVE_LIMIT` ออกจาก `mas_param` ไป `common_code` ตาม contract ใน
> `LLDD-BE-Integration-SBP-Platform` §5.5.2 เป๊ะ — `code_value='THRESHOLD'` · `code_name='100000'`
> แก้ที่ `tools/build_sgi_schema_sql.py` แล้ว regenerate · **ติดตั้งจริงบน PostgreSQL 16 แล้ว**:
> `common_code` มีแถว `SGI_APPROVE_LIMIT` 1 แถว · `mas_param` เหลือ 0 แถว · `code_type` ยาว 19 ตัว (ไม่เกิน 20)
>
> ⏭️ **ไม่ทำในรอบนี้ — อยู่นอกขอบเขต batch:** "ให้ Backend อ่านค่าแบบ numeric + fail-fast" และ
> "เพิ่ม test สำหรับ `< / = / > 100000`" เป็นงานของ BE ที่ยังไม่ได้เขียน
> **ไม่มีโค้ดบรรทัดไหนในทั้ง workspace อ่าน `SGI_APPROVE_LIMIT` เลยตอนนี้** (ตรวจแล้ว 0 จุด)
> การย้ายจึงปลอดภัย และ test จะเขียนได้ก็ต่อเมื่อ BE routing มีจริง


ปัญหาที่พบและแก้ฝั่ง SQL แล้วเมื่อ 2026-09-15:

- `sgi_seed_data.sql` ใส่ `SGI_APPROVE_LIMIT=100000` ลง `mas_param`
- `database.md`, `workflow.md`, `api.md` และ Workflow LLDD กำหนดให้มี source of truth แห่งเดียวใน `common_code`
- API `GET /sgi/lookup/workflow-sections` ออกแบบให้อ่านวงเงินจาก `common_code`

งานที่ต้องทำ:

- [x] ลบ seed `SGI_APPROVE_LIMIT` ออกจากชุด `mas_param`
- [x] เพิ่มค่าใน `common_code` โดยใช้ contract ที่ตกลงไว้:
  - [x] `code_type = 'SGI_APPROVE_LIMIT'`
  - [x] `code_value = 'THRESHOLD'`
  - [x] `code_name = '100000'`
  - [x] `active_flag = 'Y'`
- [x] ตรวจความยาว `code_type` ไม่เกิน `varchar(20)`
- [ ] ให้ Backend อ่านค่าแบบ numeric อย่างปลอดภัย และ fail-fast เมื่อไม่มีค่า/มีค่าซ้ำ/แปลงไม่ได้
- [ ] ห้าม hardcode `100000` ซ้ำใน application code หรือ `workflow_route.condition_json`
- [ ] เพิ่ม test สำหรับ `< 100000`, `= 100000` และ `> 100000`

เกณฑ์ตรวจรับ:

- [x] fresh/sequential install: query `common_code` พบ active row ของ `SGI_APPROVE_LIMIT` เพียงหนึ่งแถว
- [x] query `mas_param` ไม่พบ `SGI_APPROVE_LIMIT` ที่ SGI seed เพิ่ม
- [ ] ค่า `< 100000` จบที่ GM 02 และค่า `>= 100000` ไป AVP 03 ตาม flow ที่อนุมัติ
- [ ] เปลี่ยนค่าใน DB แล้ว routing เปลี่ยนตามโดยไม่ deploy code ใหม่

หลักฐานอ้างอิง:

- `output/sql/sgi_seed_data.sql` บรรทัดเดิมประมาณ 169–172
- `database.md` หัวข้อ Seed / approval limit
- `workflow.md` หัวข้อเกณฑ์วงเงินอนุมัติ
- `api.md` endpoint `GET /sgi/lookup/workflow-sections`
- `LLDD/md/BE/LLDD-BE-Integration-SBP-Platform.md` §5.5.2

### P0-CFG-02 — ลงทะเบียน `common_code_type` ก่อนลงค่าจริง

> ✅ **แก้แล้ว 2026-09-15** — เพิ่มหัวข้อ `2.0 common_code_type` ใน seed **มาก่อน** การ insert `common_code`
> ลงทะเบียน 3 type: `SGI_DECISION` · `SGI_DOC_STATUS` · `SGI_APPROVE_LIMIT` (idempotent · `create_user='SGI-INSTALL'`)
> เพิ่ม preflight ตรวจว่าตาราง `common_code_type` มีจริงก่อนเริ่ม
> และเพิ่ม `common_code_type` เข้า `tools/build_sgi_existing_stub_sql.py` ไม่งั้นเทสจะล้มที่ preflight
> **พิสูจน์แล้ว:** ติดตั้งสด → type 3 · code 14 · รันซ้ำแล้วเท่าเดิม
>
> ⏭️ **`SGI_DATASOURCE` ยังไม่ลงทะเบียน** — ดูเหตุผลที่ P0-CFG-03 (ชุดค่ายังไม่ถูกเคาะ)
> การลงทะเบียน type โดยไม่มีค่าที่ตกลงกันจะได้ type เปล่าที่ไม่มีใครใช้


ปัญหาที่พบและแก้แล้วบางส่วนเมื่อ 2026-09-15:

- SQL insert ค่า `SGI_DECISION` และ `SGI_DOC_STATUS` ลง `common_code` โดยไม่มี seed ใน `common_code_type`
- ชุดติดตั้งยังไม่มี type ของ `SGI_APPROVE_LIMIT` และ `SGI_DATASOURCE`

งานที่ต้องทำ:

- [x] เพิ่ม preflight ตรวจว่าตาราง `common_code_type` มีอยู่จริง
- [ ] เพิ่ม idempotent seed สำหรับ type ต่อไปนี้:
  - [x] `SGI_DECISION`
  - [x] `SGI_DOC_STATUS`
  - [x] `SGI_APPROVE_LIMIT`
  - [ ] `SGI_DATASOURCE`
- [ ] ใช้ `active_flag='Y'`, `create_user='SGI-INSTALL'` และคำอธิบายภาษาไทยที่ทีมธุรกิจยืนยันแล้ว
- [x] insert type ก่อน insert แถวใน `common_code`
- [x] ตรวจชื่อทุก type ไม่เกินความยาวที่ `common_code.code_type` รองรับ
- [ ] ตรวจว่าการรันซ้ำไม่ชน type ที่ทีมอื่นเป็นเจ้าของ

เกณฑ์ตรวจรับ:

- [x] ทุก `SGI_*` code type ที่ SQL ปัจจุบันใช้มี active row ใน `common_code_type`
- [x] ไม่มี SGI code type ที่มีเฉพาะใน `common_code` แต่ไม่มีทะเบียน type (fresh/sequential install)
- [ ] deploy ซ้ำไม่สร้าง type ซ้ำและไม่แก้ข้อมูลของโมดูลอื่น

### P0-CFG-03 — เพิ่ม `SGI_DATASOURCE`

> ⏭️ **ไม่ทำ — เป็นการตัดสินใจเชิงธุรกิจ ไม่ใช่การแก้ให้ตรงกัน**
> เช็กลิสต์ข้อนี้ขึ้นต้นด้วย "ขอ business sign-off รายการ datasource" ด้วยตัวเอง
> คำถามที่ยังไม่มีคำตอบ: `ALM`/`STA` เป็นค่าจาก integration เท่านั้น หรือต้องอยู่ใน code type เดียวกับ `PRO`/`REA`
> · `seq_no` และ `code_name` ภาษาไทยของแต่ละค่า · ค่าไหน active
>
> **ถ้าเดาแล้วผิด จะเลวร้ายกว่าไม่ทำ** — dropdown ของ FE จะผูกกับชุดค่าที่ผิด และ validation
> "ไม่รับ datasource นอกชุดที่ active" จะปฏิเสธข้อมูลจริงจาก ALLMAP/STA
> ⚠️ ผูกกับข้อค้างเดียวกันใน `batchjob/JOB-02-12-ข้อตัดสินใจที่ไม่มีของเดิมให้ลอก.md` หัวข้อ **C3**
> (กฎตัดสินของ Job 2 ยังรู้จักแค่ `ALM`/`STA` — `PRO`/`REA` เข้ามาแล้วจะค้าง `W` ตลอดไป)


งานที่ต้องทำ:

- [ ] ขอ business sign-off รายการ datasource ที่ระบบใหม่ต้องแสดง
- [ ] เพิ่มค่า `PRO` = เชิงรุก
- [ ] เพิ่มค่า `REA` = เชิงรับ
- [ ] ตัดสินใจและบันทึกว่า `ALM`/`STA` ต้องอยู่ใน code type เดียวกันหรือเป็นค่าจาก integration เท่านั้น
- [ ] กำหนด `seq_no`, `code_name` และ active status ให้แน่นอน
- [ ] ให้ FE/API อ่านจาก `GET /common/common-code` หรือ adapter ที่ตกลง ห้าม hardcode dropdown
- [ ] เพิ่ม validation ไม่รับ datasource นอกชุดที่ active

เกณฑ์ตรวจรับ:

- [ ] API lookup คืนค่า datasource ครบและลำดับถูกต้อง
- [ ] สร้าง/นำเข้าเอกสารจาก `PRO` และ `REA` ได้
- [ ] ค่า legacy ที่ยังต้องรองรับไม่ถูก reject โดยไม่ตั้งใจ

### P0-WF-01 — สร้าง Workflow definition/version เริ่มต้น

> ⏭️ **ไม่ทำ — ไม่ใช่ของที่ทีมนี้สร้างเองได้**
> งานข้อนี้เริ่มด้วย "ยืนยัน owner และวิธีขอ `version_id` กับทีม `@srm/glb-workflow`" ซึ่งเป็นเงื่อนไขก่อนทุกขั้น
> `version_id` ที่เดาเอาเองจะไปชนกับ workflow ของระบบอื่นที่ใช้ `sps_store.workflow_*` ร่วมกันอยู่ (state จริงมี 18 · transaction 19,283 แถว)
>
> **สิ่งที่ยืนยันได้จากฝั่งเรา:** มติ 2026-09-09 ระบุว่า **batch job ไม่เรียก engine เอง**
> Job 8b เรียก REST `POST /api/v1/sgi/workflow/instances` และ **BE เป็นผู้เรียก engine ที่เดียวในระบบ**
> → artifact ของ workflow definition จึงเป็นงานของ **BE + ทีม workflow** ไม่ใช่ `output/sql/` ของ batch
> ⚠️ ข้อนี้ถูกบันทึกเป็นข้อค้างไว้แล้วที่ `batchjob/JOB-02-12-...md` หัวข้อ **A3**


ปัญหาปัจจุบัน:

- `output/sql/` ยังไม่มี artifact สำหรับ workflow version, state, status, event, route, part และ URL mapping
- ไม่มีขั้นตอนผูก `email_template_id` ที่ seed ได้กับ `workflow_route.email_id`
- schema SGI สำเร็จอย่างเดียวไม่ทำให้เอกสารเดิน approval flow ได้

งานที่ต้องทำ:

- [ ] ยืนยัน owner และวิธีขอ `version_id` กับทีม `@srm/glb-workflow`
- [ ] สร้าง workflow version ใหม่สำหรับ SGI โดยไม่แตะ version ของระบบอื่น
- [ ] ลงทะเบียน initial state `06` และ end state `99`
- [ ] ลงทะเบียน state/status `06`, `08`, `01`, `02`, `03`, `99`
- [ ] ลงทะเบียน event/route ทุกปุ่ม รวมเส้นส่งกลับและเส้นแยก GM/AVP
- [ ] กำหนด `seq`, `from_state_id`, `event`, `to_state_id` และ condition ให้ตรง transition table
- [ ] กำหนด `url_main` และ `url_param_mapping` ให้ inbox กลางเปิดเอกสาร SGI ได้
- [ ] ยืนยันว่า SGI ใช้ `addPreApprover()` และไม่ seed `workflow_group`/`workflow_group_map` หาก design ล่าสุดไม่ใช้
- [ ] resolve ID ของ email template ทั้ง 8 แถวหลัง seed
- [ ] ผูก template ID กับ route โดย business key ครบ `(version_id, from_state_id, event, to_state_id)`
- [ ] แยก template ของ reminder/escalation/batch ไปเก็บใน config ตาม contract ที่ตกลง
- [ ] จัดทำ rollback เฉพาะ workflow version ของ SGI โดยไม่กระทบ transaction/history ของระบบอื่น
- [ ] ถ้าทีม Workflow deploy แยก ให้เพิ่ม runbook, dependency, owner และ evidence ใน release package

เกณฑ์ตรวจรับ:

- [ ] initialize workflow ได้โดยใช้ `referenceId = sgi_compensation_documents.id`
- [ ] `getPermissionEvents()` คืนปุ่มถูกต้องทุก state/ผู้อนุมัติ
- [ ] เส้นทางวงเงินต่ำกว่า/ตั้งแต่ threshold ขึ้นไปเลือก route ถูกต้อง
- [ ] ส่งกลับทุก state ไปปลายทางที่ระบุใน transition table
- [ ] inbox กลางเปิดกลับหน้าเอกสาร SGI ถูกใบ
- [ ] route ทุกเส้นที่ต้องส่งเมลมี template ID ถูกฉบับ
- [ ] rerun setup ไม่สร้าง workflow version ซ้ำโดยไม่ตั้งใจ

### P0-API-02 — แก้ SQL ของ Lookup API ให้ตรง schema และ seed

> ✅ **แก้แล้ว 2026-09-16 — ข้อกล่าวหาถูกต้องทั้งสอง query**
> ยืนยันกับ dump จริง: `sps_store.workflow_status` มีแค่ `status_id` · `status_name` · `create_date` · `version_id`
> — **ไม่มี `seq`** จริงตามที่ระบุ · และ `c.code_value = s.state_id` เทียบ varchar กับ integer
>
> **แก้ที่ `SQL_BY_PATH` ใน `plan-api.html`** (แหล่งจริงที่ LLDD อ่านไปสร้างเอกสาร) แล้ว regenerate:
> · `document-statuses` → อ่าน `common_code` (`SGI_DOC_STATUS`) คืน `code_value` เป็นรหัส 2 ตัวอักษร เรียงตาม `seq_no`
> · `workflow-sections` → อ่าน `common_code` ตัด `'99'` ออกเหลือ 5 ขั้น · วงเงินจาก `SGI_APPROVE_LIMIT` ที่ **`code_name`** (ไม่ใช่ `other_value` ที่ไม่ได้ seed)
> · ใช้ชื่อเต็ม `sps_store.common_code` ทั้งสอง query ไม่พึ่ง `search_path`
> · อัปเดต `flow:` และ `db:` ของ endpoint ให้ตรงกับ SQL ใหม่ด้วย
>
> **รันจริงกับ PostgreSQL 16 แล้วทั้งสอง query** — ได้ผลตรงเกณฑ์ตรวจรับ:
> สถานะ 6 ค่าเรียงตาม `seq_no` · ขั้น 5 ค่า (06→08→01→02→03) · `approve_limit_amount = 100000`
> `check_docs.py` จับเพิ่มว่า Reference DB Mapping ยังประกาศตารางเก่า — แก้ให้ตรงแล้ว
>
> ⏭️ **ไม่ทำ:** "fail-fast เมื่อ threshold หาย/ซ้ำ/ไม่ใช่ตัวเลข" — **SQL อย่างเดียวทำแทนไม่ได้** ต้องเป็นตรรกะฝั่ง BE
> ซึ่งยังไม่มีโค้ด · เขียนเป็นคำเตือนไว้ในคอมเมนต์ของ SQL แล้ว
> ⏭️ "เพิ่มตัวตรวจ SQL ของ FE/BE LLDD กับ schema ระบบเดิม" — `check_sgi_sql_columns.py` ตรวจเฉพาะ SQL ใน TypeScript
> การขยายให้ตรวจ SQL ในเอกสารต้อง parse markdown + รู้ว่า bind อะไร เป็นงานคนละขนาด ยังไม่ทำในรอบนี้


> 🔴 **พบใหม่ 2026-09-16 — SQL ตัวอย่างปัจจุบันรันไม่ได้ทั้ง 2 query**
> ทดสอบ SQL จาก `LLDD-BE-API-Lookup`/`plan-api.html` กับ column shape ของ
> `sps_store.workflow_state`, `workflow_status`, `workflow_route` ตาม schema dump จริงแล้วได้:
>
> - document statuses: `ERROR: column "seq" does not exist`
> - workflow sections: `ERROR: operator does not exist: character varying = integer`

ปัญหาที่ต้องแก้:

- [ ] `GET /api/v1/sgi/lookup/document-statuses` ห้ามอ่าน `workflow_status.seq` เพราะตารางจริงมีเพียง `status_id`, `status_name`, `create_date`, `version_id`
- [ ] ห้ามคืน `workflow_status.status_id` เป็น `statusCode` เพราะเป็น integer surrogate ต่างกันตาม environment; canonical code `06/08/01/02/03/99` อยู่ที่ `common_code` (`SGI_DOC_STATUS`)
- [ ] `GET /api/v1/sgi/lookup/workflow-sections` ห้าม join `c.code_value = s.state_id`: seed ใช้ `code_value='THRESHOLD'` แต่ `state_id` เป็น integer
- [ ] อ่านยอดจาก `common_code.code_name='100000'` ตาม seed; SQL ปัจจุบันอ่าน `other_value` ซึ่งไม่ได้ seed
- [ ] ใช้ชื่อเต็ม `sps_store.common_code` ไม่พึ่ง session `search_path`
- [ ] กำหนดลำดับ section จาก canonical mapping/version definition; `MIN(workflow_route.seq)` ไม่รับประกันลำดับ 06→08→01→02→03 เพราะ `seq` เป็นลำดับ route ภายในแต่ละ state
- [ ] ทำให้ `api.md`, `plan-api.html`, `LLDD-BE-API-Lookup`, API Catalog และ LLDDv2 ใช้ source/mapping ชุดเดียวกัน
- [ ] เพิ่มตัวตรวจ SQL ของ FE/BE LLDD กับ schema ระบบเดิม; `check_sgi_sql_columns.py` ปัจจุบันตรวจเฉพาะ SQL ใน Batch TypeScript

เกณฑ์ตรวจรับ:

- [ ] query ทั้งสอง `PREPARE`/execute บน PostgreSQL ด้วย column shape จาก `SBP/db-schema-sps_store.md` ได้
- [ ] document statuses คืนรหัส 2 ตัวอักษรครบ 6 ค่าและชื่อเรียงตาม `seq_no`
- [ ] workflow sections คืน 5 ขั้นตามลำดับ และ `approveLimitAmount=100000` เฉพาะ contract ที่ตกลง
- [ ] กรณี threshold หาย/ซ้ำ/inactive/ไม่ใช่ตัวเลขต้อง fail ด้วย error code ที่ระบุ ไม่เลือกแถวแบบสุ่ม
- [ ] เปลี่ยน `SGI_APPROVE_LIMIT.code_name` แล้ว response/routing เปลี่ยนโดยไม่ deploy code

---

## P1 — ต้องแก้ก่อนส่ง UAT/Production readiness

### P1-PARAM-01 — กำหนดชื่อ `mas_param` มาตรฐานชุดเดียวและผูก consumer จริง

> 🟡 **แก้ชื่อแล้ว แต่ consumer coverage ยังไม่ครบ (ตรวจซ้ำ 2026-09-16)**
> ชื่อสองชุดขัดกันจริงตามที่เช็กลิสต์ระบุ · เลือกยึด **ชื่อใน SQL** เพราะเป็นชุดที่ถูกติดตั้งจริง
> และ**มีหน่วยกำกับในชื่อ** (`_KM` · `_DAYS`) ตรงกับที่เช็กลิสต์ข้อนี้เองขอไว้
>
> แก้ที่ `tools/build_lldd_documents.py` แล้ว regenerate: `SGI_SALES_DAYS_MIN` → `SGI_SALES_DATA_MIN_DAYS` ·
> `SGI_GROWTH_RATE_MAX` → `SGI_GROWTH_RATE_THRESHOLD` · `SGI_IMPACT_RADIUS_BKK` → `..._BKK_KM` (และ `_UPC_KM`)
> แก้ `database.md` ด้วย · ตรวจแล้วชื่อเก่าเหลือ **0 จุด** ในเอกสารที่ generate
> พร้อมกันนี้แก้ "ผลการพิจารณา **6** ค่า" → **7** ค่า ให้ตรงกับที่ seed ลงจริง
>
> ตรวจ code ปัจจุบันแล้ว Batch อ่าน `mas_param` จริง **6 จาก 11 key** (Job 6 = 3, Job 8b = 2,
> Job 10 = 1) และ fallback ไป env เมื่อไม่พบค่า ส่วนอีก **5 key ยังไม่มี consumer ที่อ่านจาก DB**:
> `SGI_IMPACT_RADIUS_BKK_KM`, `SGI_IMPACT_RADIUS_UPC_KM`, `SGI_SALES_DATA_MIN_DAYS`,
> `SGI_OUTLIER_SALES_DIFF`, `SGI_ALLOW_PENDING_DOWNLOAD` (ตัวท้ายรอ BE ซึ่งยังไม่มี)
>
> 🔴 ข้อความเดิมที่ว่า “ไม่มีโค้ดไหนอ่านค่าเหล่านี้จาก `mas_param`” **ไม่จริงแล้ว** และถูกแก้ใน checklist นี้
> แต่ยังห้ามปิดข้อนี้จนกว่าจะยืนยันว่า key ใดเป็น DB source, key ใดเป็น env source และ fallback
> เป็นพฤติกรรมที่อนุมัติแล้ว เพราะ `mas_param` ไม่มี unique constraint; ถ้ามีค่าซ้ำ consumer ปัจจุบันเลือกค่า
> ตามลำดับแถวที่ DB คืนมา ซึ่งไม่ deterministic


ชื่อในเอกสารปัจจุบัน:

- `SGI_IMPACT_RADIUS_BKK`
- `SGI_IMPACT_RADIUS_UPC`
- `SGI_SALES_DAYS_MIN`
- `SGI_GROWTH_RATE_MAX`

ชื่อใน SQL ปัจจุบัน:

- `SGI_IMPACT_RADIUS_BKK_KM`
- `SGI_IMPACT_RADIUS_UPC_KM`
- `SGI_SALES_DATA_MIN_DAYS`
- `SGI_GROWTH_RATE_THRESHOLD`

งานที่ต้องทำ:

- [ ] เลือก canonical key ของแต่ละค่ากับทีม Backend/Batch/Business
- [ ] ทำ inventory การอ้าง key ใน Java, configuration, SQL, API และ LLDD
- [ ] แก้ทุก consumer/provider ให้ใช้ชื่อเดียวกัน
- [ ] ทำ consumer matrix ครบทั้ง 11 key; ระบุ `DB only`, `DB + env fallback`, `env only` หรือ `BE TO-BE`
- [ ] เพิ่ม query ตรวจ active duplicate ก่อนสร้าง `Map`/หยิบแถวแรก ห้ามปล่อยให้ค่าซ้ำเลือกแบบไม่กำหนดลำดับ
- [ ] ระบุ unit ในชื่อหรือ description ให้ชัด เช่น km, day, percent
- [ ] ถ้าต้องเปลี่ยนชื่อ key ที่เคย deploy แล้ว ให้มี migration และช่วงรองรับชื่อเก่า
- [ ] เพิ่ม startup validation สำหรับ parameter ที่จำเป็น
- [ ] เพิ่ม automated check ป้องกัน key ใน SQL กับเอกสารไม่ตรงกันอีก

เกณฑ์ตรวจรับ:

- [ ] ค้นทั้ง repository แล้วแต่ละ business parameter เหลือ canonical key เดียว หรือมี alias ที่ระบุวันยกเลิกชัดเจน
- [ ] Backend/Batch อ่านค่าที่ seed ได้จริง
- [ ] เปลี่ยนค่าใน `mas_param` แล้ว behavior เปลี่ยนตามโดยไม่แก้ code

### P1-SEED-01 — ทำ seed manifest และ post-check ให้ตรวจ “ค่า” ไม่ใช่แค่จำนวนขั้นต่ำ

> ⏭️ **ไม่ทำในรอบนี้ — แต่เหตุผลเปลี่ยนไปแล้วบางส่วน**
> ✅ สิ่งที่ทำให้แล้ว: หัวไฟล์ seed และ rollback ตอนนี้ระบุ**จำนวนจริงที่คำนวณสด**จาก generator
> (`common_code_type 3` · `common_code 14` · `mas_param 11` · `email_template 8`) ไม่ใช่ตัวเลข hardcode
>
> ⏭️ ที่ยังไม่ทำคือ **manifest แยกไฟล์ + post-check ที่เทียบค่าทีละแถว** — ต้องตัดสินก่อนว่า manifest
> เป็นแหล่งความจริงหรือ generator เป็น · ถ้าทำสองที่จะกลายเป็นสองแหล่งที่ drift ออกจากกันได้
> (ปัญหาชนิดเดียวกับที่เพิ่งแก้ใน P1-DOC-01 เรื่อง Data Dictionary)


> 🔴 **พบใหม่ 2026-09-16** — seed fresh/sequential ผ่าน แต่ self-check ยังให้ผลผ่านเมื่อมีข้อมูลเกินหรือซ้ำ
>
> - header ของ `sgi_seed_data.sql` ระบุ `common_code 13` ทั้งที่ insert จริง **14** (7 decision + 6 status + 1 threshold)
> - header ไม่ระบุ `common_code_type 3` ทั้งที่เขียนลงตารางระบบเดิม
> - post-check ไม่ตรวจ code type 3, threshold 1, running number ปีปัจจุบัน, owner และค่าจริง
> - ใช้เงื่อนไข `< expected` จึงยอมรับแถวเกิน/duplicate
> - filter template ด้วย `LIKE 'EM-0%'` กว้างกว่าชุด exact EM-01…EM-08 และไม่จำกัด owner

งานที่ต้องทำ:

- [ ] สร้าง manifest ของ business key + expected value + active flag + owner สำหรับ seed ทุกแถว
- [ ] แก้ header เป็น `common_code_type 3`, `common_code 14`, `mas_param 11`, `email_template 8`
- [ ] post-check ต้องตรวจ exact business key/value ของ `SGI_APPROVE_LIMIT` (`THRESHOLD`/`100000`) และ parameter ทั้ง 11 key
- [ ] ตรวจ duplicate แยกจาก count; ถ้ามี key ซ้ำต้อง rollback transaction พร้อมข้อความระบุ key
- [ ] ตรวจ `sgi_document_running_numbers` ของปีปัจจุบันว่ามีหนึ่งแถว แต่ห้าม reset ค่าเดิมที่ใช้งานแล้ว
- [ ] ใช้รายชื่อ template exact EM-01…EM-08 + `create_by='SGI-INSTALL'` แทน wildcard อย่างเดียว
- [ ] ตกลง owner marker เดียว: generated seed ใช้ `SGI-INSTALL` แต่ LLDD SQL ตัวอย่างใช้ `SGI-SETUP`

เกณฑ์ตรวจรับ:

- [ ] แก้ค่าของ seed แล้ว rerun migration ทำให้ได้ desired value หรือ fail พร้อม runbook ที่ชัดเจน
- [ ] เติม duplicate จำลองหนึ่ง key แล้ว post-check ต้อง fail
- [ ] เพิ่มแถว SGI ที่ไม่อยู่ใน manifest แล้ว post-check รายงานโดยไม่ลบข้อมูลอัตโนมัติ
- [ ] count/header/cleanup manifest มาจาก constant ชุดเดียวกับคำสั่ง INSERT

### P1-TEST-01 — ทำ existing-table stub และ SQL checker ให้สะท้อนฐานจริง

> ✅ **แก้แล้ว 2026-09-16 — และเป็นบั๊กที่ร้ายกว่าที่เช็กลิสต์ระบุ**
> `tools/build_sgi_existing_stub_sql.py` **hardcode PK** ไว้ พร้อมคอมเมนต์ยอมรับเองว่า
> *"PK ใส่เท่าที่จำเป็นให้ seed ของเทสใช้ ON CONFLICT ได้"* → stub **โกหก** 5 ตาราง:
>
> | ตาราง | ของจริงใน dump | stub เดิม |
> |---|---|---|
> | `mas_param` | **ไม่มี PK** (index ธรรมดา `btree(param_name, param_value)`) | `param_name PRIMARY KEY` 🔴 |
> | `juristic` · `mas_zone` · `business_user` | **ไม่มี PK** | ใส่ PK ปลอม 🔴 |
> | `common_code_type` | **มี PK `code_type`** | ไม่ใส่ 🔴 |
>
> ✅ แก้ให้ **อ่าน PK จาก dump** (`- **PK:** \`col\``) แทน hardcode · ตรวจแล้วไม่มีเทสไหนพึ่ง PK ปลอม
> (`ON CONFLICT` ใช้กับ `mas_store` ตัวเดียวซึ่งของจริงมี PK อยู่แล้ว)
>
> 🔴 **ผลที่ตามมาทันที** — พอ stub ตรงของจริง การทดสอบ concurrent seed ก็**เกิดแถวซ้ำจริง** (ดู P1-MIG-01)
> ซึ่งก่อนหน้านี้ถูก PK ปลอมบังไว้ · นี่คือตัวอย่างว่า stub ที่หลวม/แน่นไม่ตรงของจริงทำให้เทสเชื่อผิดได้ทั้งสองทาง


> 🔴 **พบใหม่ 2026-09-16** — `sgi_existing_stub.sql` ตรงกับ generator แต่ generator ใส่ key ไม่ตรง dump:
>
> - ฐานจริง `common_code_type.code_type` เป็น PK แต่ stub **ไม่มี PK**
> - ฐานจริง `mas_param` ไม่มี PK/unique (มีเพียง index `(param_name,param_value)`) แต่ stubเติม
>   `PRIMARY KEY (param_name)` เพื่อช่วย test
> - stub มี workflow เพียง `workflow_transaction`/`workflow_history` จึงไม่สามารถตรวจ SQL ของ lookup
>   ที่อ้าง `workflow_state`, `workflow_status`, `workflow_route`
> - รอบ `--keep` หนึ่งครั้ง loader ไม่สร้าง relation แต่ checker เดินต่อ เพราะตรวจข้อความ `ERROR`/
>   `could not connect` แทนการตรวจ `returncode`; ผลรอบนั้นล้มภายหลังเป็น relation missing

งานที่ต้องทำ:

- [ ] generate PK/unique/default/nullability จาก dump จริง ห้ามใช้ `PK` override เพื่อทำให้ test ผ่านง่ายขึ้น
- [ ] ถ้า test fixture ต้องการ key เพิ่ม ให้สร้างใน fixture เฉพาะ test และติดป้ายว่าไม่ใช่ production schema
- [ ] เพิ่ม workflow definition tables ที่ API SQL ใช้ หรือสร้าง checker แยกสำหรับ BE/API contract
- [ ] ทุก subprocess ที่ load stub/schema ต้องตรวจ `returncode != 0` และแสดง `stdout/stderr` ของไฟล์ที่ล้ม
- [ ] checker ต้อง load `sgi_seed_data.sql` และรัน post-check อย่างน้อยหนึ่งรอบสำหรับ seed contract
- [ ] แยกผล `PASS`, `SKIPPED_MSSQL`, `SKIPPED_DYNAMIC`, `NOT_TESTED` ชัดเจน ห้ามสรุปรวมว่า “SQL ทั้งหมดผ่าน”

เกณฑ์ตรวจรับ:

- [ ] catalog ของ stub เทียบ PK/unique/null/default กับ `SBP/db-schema-sps_store.md` แล้วไม่ต่างใน object ที่ทดสอบ
- [ ] ทำให้ schema load fail แล้ว checker ต้องหยุดทันที ก่อน PREPARE query
- [ ] SQL lookup 2 เส้นและ Batch PostgreSQL SQL ทุกคำสั่งที่ประกอบเสร็จถูก parse/resolve กับ schema จริง

### P1-DOC-01 — ทำ Data Dictionary ให้ครบ 21 ตารางใน scope

> ✅ **แก้แล้วบางส่วน / ⏭️ ที่เหลือไม่จำเป็น**
> ✅ แก้ถ้อยคำจำนวนตารางใน `database.md` เป็น **"20 ตารางใหม่ + 24 index · รวม `fcs_qssi_score` ที่ reuse = 21 ตารางในขอบเขต"**
>
> ⏭️ **"เพิ่มแถว Data Dictionary ของ `sgi_fgi_new_store_compensations`" ไม่ต้องทำ** — ตรวจแล้วว่า
> `tools/lldd_db_dictionary.py` **อ่านรายชื่อตารางจาก DDL ชุดเดียวกับ `build_lldd_documents`**
> ไม่ได้ hardcode รายชื่อ ตารางนี้จึงอยู่ในพจนานุกรมอัตโนมัติอยู่แล้ว (PDF regenerate 2026-09-15)
> การ "เพิ่มแถว" ด้วยมือจะกลายเป็นรายชื่อซ้อนที่หลุดจาก DDL ได้ในอนาคต


งานที่ต้องทำ:

- [x] แก้คำอธิบายจำนวนให้ชัดว่า “20 ตารางสร้างใหม่ + `fcs_qssi_score` reuse = 21 ตารางใน scope”
- [x] เพิ่มแถว Data Dictionary ของ `sgi_fgi_new_store_compensations` ผ่าน generator กลาง
- [x] ระบุ source `FGI_NEW_STORE_COMPENSATE`, PK/UK/FK, period key และ Job ที่อ่าน/เขียน
- [x] ตรวจ Zone A ให้มี 8 ตารางตรงกับ `sgi_schema.sql`
- [x] ตรวจ ERD/HTML/LLDD ที่แสดงจำนวนตารางให้ตรงกัน
- [x] อัปเดตกฎ `check_docs.py` ให้เทียบ canonical columns/owner/read/write ของ 20+1 ตาราง

เกณฑ์ตรวจรับ:

- [x] รายชื่อตารางจาก DDL เทียบ Data Dictionary แล้วไม่ขาด/เกิน
- [x] จำนวน 20/21 ถูกใช้ด้วยความหมายเดียวกันในขอบเขตที่ `check_docs.py` ตรวจ

### P1-DOC-02 — ลบข้อความ F1/F8 ที่ตกยุคจาก `workflow.md`

> ✅ **แก้แล้ว 2026-09-15 — ข้อความตกยุคจริง**
> `workflow.md` บรรทัด 189 ยังเขียนว่า `sgi_fgi_impact_processes` **ขาด** คอลัมน์ F8 และ **ยังไม่มี**
> ตาราง `sgi_fgi_impact_compensations` · ตรวจกับ DDL ที่ติดตั้งจริงแล้ว **ผิดทั้งสองข้อ**:
> ตาราง `sgi_fgi_impact_compensations` มีจริง และคอลัมน์ F8 ครบทั้ง 6 ตัว
> (`last_compensate_seq` · `last_compensate_seq_no` · `start_compensate_month` · `end_compensate_month` · `flag_action` · `datasource`)
> เขียนใหม่เป็น "ปิดแล้ว 2026-08-21 · ยืนยันซ้ำกับ DDL จริง 2026-09-15"
>
> ⚠️ **แต่คงคำเตือนไว้หนึ่งข้อ** — นิยาม "ยอด 0 กี่งวดติดกันแล้วหยุดชดเชย" **ยังต้อง business sign-off**
> (ไม่มีตรรกะนี้ในระบบเดิมเลย) การรับ F1 เข้าโครงแก้แค่เรื่อง "เก็บข้อมูลได้" ไม่ได้แก้เรื่อง "กติกาคืออะไร"


งานที่ต้องทำ:

- [x] แก้ข้อความที่ยังระบุว่า `sgi_fgi_impact_processes` ขาดคอลัมน์ F8
- [x] แก้ข้อความที่ยังระบุว่าไม่มี `sgi_fgi_impact_compensations`
- [x] อ้างสถานะล่าสุดจาก `database.md` ซึ่งรับ F1/F8 เข้าโครงแล้ว
- [ ] ตรวจ sequence/flow ที่ใช้ `last_compensate_seq`, `last_compensate_seq_no`, งวด และยอดศูนย์ต่อเนื่องให้ตรง DDL
- [ ] เพิ่ม test mapping จาก legacy F1/F8 ไป schema ใหม่

เกณฑ์ตรวจรับ:

- [x] `workflow.md` ไม่มีข้อความว่า F1/F8 ยังเป็น implementation blocker
- [x] ชื่อคอลัมน์และตารางใน flow มีอยู่จริงใน generated SQL

### P1-DOC-03 — ล้าง `status_email_rules` ออกจาก active contract

> ⏭️ **ไม่ต้องแก้ — เกณฑ์ตรวจรับของข้อนี้ผ่านอยู่แล้ว**
> ไล่ดูทุกจุดที่เอ่ย `status_email_rules` ในเอกสาร active แล้ว **ทุกจุดอยู่ในบริบท "ถูกยกเลิกแล้ว"**:
> · `workflow.md:149` — *"✅ ปิด DP-5 (2026-08-14): workflow ให้เลข template (`sps_store.workflow_route.email_id`)
>   แล้ว SGI เรียก `sendEmail()` ของ email-lib เอง — **ไม่มีตาราง `status_email_rules`**"*
> · `database.md:98` — *"`status_email_rules` ยังถูกตัดตามเดิม"*
> · `api.md:394` — *"หลังตัด `audit_logs` และ `status_email_rules`"*
>
> ทั้ง source เดียว (`workflow_route.email_id`) และผู้ส่งเพียงฝ่ายเดียว (SGI เรียก email-lib) **ระบุไว้ครบแล้ว**
> ⏭️ ที่ยังต้องทำจริงคือ **"ยืนยันกับทีม workflow ว่า engine จะไม่ส่งซ้ำ"** ซึ่งเป็นการถามทีมอื่น ไม่ใช่การแก้เอกสาร


งานที่ต้องทำ:

- [ ] แก้ขั้นตอน workflow ที่ยังเขียนว่าส่งเมลตาม `status_email_rules`
- [ ] ระบุ source เดียวว่า transition mail ใช้ `workflow_route.email_id`
- [ ] ระบุว่า SGI หรือ workflow engine เป็นผู้ส่งจริงเพียงหนึ่งฝ่าย
- [ ] ยืนยันกับทีม workflow ว่า engine จะไม่ส่งซ้ำเมื่อ SGI เรียก email-lib เอง
- [ ] ระบุวิธีหา route ด้วย key ครบ ไม่เลือกเพียง `(from_state_id, event)`

เกณฑ์ตรวจรับ:

- [ ] ไม่พบ `status_email_rules` ในเอกสาร active ยกเว้นบริบทที่บอกว่าถูกยกเลิก
- [ ] transition หนึ่งครั้งส่งอีเมลไม่เกินหนึ่งฉบับต่อผู้รับ/เหตุการณ์ตาม design

### P1-DOC-04 — เลือก execution model ของ Job 11 ให้เหลือแบบเดียว

> ⏭️ **ไม่ต้องแก้ — เอกสารกับโค้ดตรงกันอยู่แล้ว**
> เช็กลิสต์ระบุว่าเอกสาร "กล่าวปะปนกัน 3 แบบ" · ตรวจแล้ว**ไม่พบความขัดแย้ง**:
> · `workflow.md:45` และ `:103` — *"job นี้เป็นผู้ consume เอง (มติ 2026-09-12)"*
> · โค้ดจริง `job-11-consume-sta-compensate.service.ts:69` — *"job นี้ consume คิวเอง · bind · ack · nack · DLQ · retry ทำเองหมด"*
>   และ *"repo `store-consumer` ถูกตัดออกจากขอบเขตแล้ว"* · ใช้ `SgiRabbitConsumer` จริง
>
> ที่เจอคำว่า `SubmitJob` คือไฟล์ `SBP/srm-sps-spsap-store-consumer.md` ซึ่งเป็น**เอกสารวิเคราะห์ repo อื่น**
> (ความสามารถของ EAI consumer เดิม) ไม่ได้พูดถึง Job 11 — ไม่ใช่ความขัดแย้ง
>
> ⏭️ **ที่ยังเปิดอยู่จริง** คือสัญญากับ STA (ชื่อ queue/binding · จำนวน retry · นโยบาย DLQ)
> บันทึกไว้ที่ `batchjob/JOB-02-12-ข้อตัดสินใจที่ไม่มีของเดิมให้ลอก.md` หัวข้อ **A1**


ตัวเลือกที่เอกสารปัจจุบันกล่าวปะปนกัน:

- Job 11 consume RabbitMQ เอง
- consumer ภายนอกเรียก `SubmitJob` หนึ่งครั้งต่อข้อความ
- Job 11 ไม่เชื่อม MQ เอง

งานที่ต้องทำ:

- [ ] เลือก model ที่ตรง implementation/deployment ล่าสุด
- [ ] ระบุ owner ของ ACK/NACK, retry, dead-letter และ publisher/consumer connection
- [ ] ระบุ transaction boundary ระหว่าง inbox dedup กับ update compensation
- [ ] ทำ `workflow.md`, Job 11 LLDD, Java implementation และ deployment config ให้ตรงกัน
- [ ] เพิ่ม integration test duplicate delivery, poison message และ restart ระหว่างประมวลผล

เกณฑ์ตรวจรับ:

- [ ] เอกสารไม่ใช้คำว่า “consume เอง” และ “ไม่ต่อ MQ เอง” กับ component เดียวกัน
- [ ] duplicate message ไม่อัปเดต compensation ซ้ำ
- [ ] operational runbook ระบุจุดดู lag/retry/DLQ ได้

### P1-MIG-01 — ทำ seed ให้เป็น desired-state migration

> ✅ **แก้ส่วน concurrent แล้ว 2026-09-16 — ข้อกล่าวหาถูกต้อง พิสูจน์ได้จริง**
> เดิมผมสรุปว่า "ทำไม่ได้เพราะไม่มี unique constraint" ซึ่ง**ไม่ครบ** — เช็กลิสต์เสนอ advisory lock ไว้เองตั้งแต่แรก
>
> **พิสูจน์ว่าเกิดจริง** (PostgreSQL 16 · stub ที่แก้ให้ตรงของจริงแล้ว ไม่มี PK บน `mas_param`):
> สอง transaction ที่ทับกันแบบ READ COMMITTED ต่างฝ่ายต่างไม่เห็นแถวที่อีกฝ่ายยังไม่ commit
> → `INSERT ... WHERE NOT EXISTS` ผ่านทั้งคู่ → **ได้ 2 แถวที่ควรมี 1**
>
> ✅ **แก้: เพิ่ม `SELECT pg_advisory_xact_lock(861000, 1);` ที่หัว `sgi_seed_data.sql`** (ก่อน PREFLIGHT)
> · namespace เดียวกับ `SgiJobLockService` · ปลดอัตโนมัติตอน COMMIT/ROLLBACK ไม่มีทางค้างแม้ script ตาย
> · **ไม่แตะโครงสร้างตารางของระบบเดิมเลย** จึงไม่ขัดกติกาโครงการ
>
> **ทดสอบเทียบตรง:** race เดิมที่เคยได้ 2 แถว → มี lock แล้วได้ **1 แถว** · และรัน seed เต็มพร้อมกัน 2 รอบบนฐานว่าง
> ได้ `common_code_type 3 · common_code 14 · mas_param 11 · email_template 8 · competitors 11` ตรงเป๊ะ
>
> ⏭️ **ยังไม่ทำ (เหตุผลเดิมยังใช้ได้):** desired-state ที่ **อัปเดตค่าเดิม** เมื่อ spec เปลี่ยน
> ยังติดที่ `common_code`/`mas_param` ไม่มี unique key และเป็นตารางของทีมอื่น — ต้องเคาะว่าจะ
> (ก) ขอเพิ่ม unique (ข) ใช้ migration tool ที่มี version (ค) UPDATE ... WHERE create_user='SGI-INSTALL'
> ⚠️ ข้อ (ค) ขัดกติกา "INSERT อย่างเดียว" ที่ทั้งโครงการยึดมา ต้องมีคนรับผิดชอบเคาะ

> ⏭️ **ไม่ทำ — เป็นการเปลี่ยนรูปแบบการ deploy ต้องเคาะก่อน**
> ปัญหาที่ระบุถูกต้อง: `INSERT ... WHERE NOT EXISTS` **ไม่ปรับค่าเดิมเมื่อ spec เปลี่ยน**
> (พิสูจน์แล้วในรอบตรวจ DDL — แก้ค่า seed แล้วติดตั้งใหม่ ค่าเก่าจะค้าง)
>
> **สิ่งที่ทำไปแล้วแทน** (รอบ 2026-09-15): เขียนกับดักนี้ไว้ในหัวไฟล์ `sgi_schema_rollback.sql` ให้ชัด
> พร้อมคำสั่งล้าง 3 บรรทัดที่ทดสอบวนครบรอบแล้ว (install → rollback → ล้าง → seed ใหม่)
>
> 🔴 **ยืนยันความเสี่ยงด้วย test จริง 2026-09-16:** จำลอง partial state ที่ตาราง/parameter/type มีแล้ว
> แต่ล้างเฉพาะ `common_code` และ `email_template`, จากนั้นรัน seed พร้อมกัน 2 session — ทั้งสอง session
> commit สำเร็จ และได้ `common_code=28` (duplicate 14 business keys) กับ `email_template=16`
> (duplicate 8 names) จาก expected 14/8 ตามลำดับ จึงห้ามเรียก seed ชุดนี้ว่า concurrency-safe
>
> **ที่ไม่ทำเพราะต้องเคาะก่อน:** จะเปลี่ยนเป็น `INSERT ... ON CONFLICT DO UPDATE` ไม่ได้ตรง ๆ เพราะ
> `common_code`/`mas_param` **ไม่มี unique constraint** ครบทุก business key (เป็นตารางของระบบเดิม ห้ามแก้)
> การทำ desired-state จึงต้องเลือกระหว่าง (ก) ขอทีมเจ้าของเพิ่ม unique (ข) ใช้ migration tool ที่มี version
> (ค) เขียน UPDATE ... WHERE create_user='SGI-INSTALL' ซึ่งจะ**แตะแถวที่ติดตั้งไปแล้ว** — ขัดกับกติกา "INSERT อย่างเดียว"
> ⚠️ ข้อ (ค) กระทบกติกาความปลอดภัยที่ทั้งโครงการยึดมา ต้องมีคนรับผิดชอบเคาะ


ปัญหาปัจจุบัน:

- `INSERT ... WHERE NOT EXISTS` ป้องกันจำนวนเพิ่มเมื่อรันตามลำดับ แต่ไม่ปรับค่าเดิมเมื่อ specification เปลี่ยน
- legacy tables ไม่มี unique constraint ครบทุก business key จึงยังเสี่ยง duplicate เมื่อ deploy พร้อมกัน

งานที่ต้องทำ:

- [ ] กำหนด migration version ของ schema, seed และ workflow setup
- [ ] เลือกวิธี update ค่า SGI เดิมเมื่อ description/value/template เปลี่ยน
- [ ] เพิ่ม advisory lock หรือ deployment lock ป้องกัน concurrent seed
- [ ] เพิ่ม exact duplicate preflight/post-check สำหรับ `common_code` และ `email_template` ซึ่งไม่มี unique business key
- [ ] ตรวจ duplicate ก่อน insert และ fail พร้อมข้อความที่แก้ปัญหาได้
- [ ] ระบุ ownership ด้วย `create_user='SGI-INSTALL'` หรือ migration marker ที่ตรวจสอบย้อนกลับได้
- [ ] แยก initial seed ออกจาก change migration ใน release ถัดไป
- [ ] ทำ partial-install recovery runbook เพราะ schema preflight ปัจจุบันหยุดเมื่อพบตาราง SGI อยู่แล้ว

เกณฑ์ตรวจรับ:

- [ ] รัน migration ซ้ำแล้วทั้งจำนวนและค่าข้อมูลตรง desired state
- [ ] จำลอง deploy พร้อมกันสอง session แล้วไม่เกิด duplicate
- [ ] environment ที่ติดตั้งค้างกลางทางสามารถ recover โดยไม่ต้องลบข้อมูลแบบเดาสุ่ม

### P1-MAIL-01 — เติม Email template และ mapping ให้พร้อมใช้งาน

> ⏭️ **ไม่ทำ — เป็นเนื้อหาที่ธุรกิจต้องเขียนและอนุมัติ**
> `subject`/`body` ของ EM-01 ถึง EM-08 เป็นข้อความที่ส่งถึงคนจริง การเขียนเองแล้วให้ธุรกิจ "ตรวจทีหลัง"
> มีความเสี่ยงว่าจะถูกใช้งานจริงโดยไม่มีใครอ่าน
>
> **ที่ฝั่งเราทำได้และทำแล้ว:** seed ลง `email_template` ครบ 8 แถว พร้อม `create_by='SGI-INSTALL'`
> ให้ย้อนกลับมาหาได้แม่นยำ · โครงสร้างพร้อมรับเนื้อหาทันทีที่ธุรกิจส่งมา
> ⏭️ "ทดสอบภาษาไทย UTF-8 · HTML escaping · recipient/CC" ทำได้ก็ต่อเมื่อมีเนื้อหาจริงแล้ว


งานที่ต้องทำ:

- [ ] ให้ทีมธุรกิจอนุมัติ subject/body ของ EM-01 ถึง EM-08
> ยังค้าง — ต้องให้คนของธุรกิจอ่านข้อความจริง เราตัดสินแทนไม่ได้
> แต่ 2026-09-16 เลิกส่งของเปล่าแล้ว: seed มีข้อความที่อ่านรู้เรื่องครบ 8 ฉบับ ให้แก้ทับได้เลย
- [x] เติม `body_format` จริง ไม่ปล่อยเป็นค่าว่างใน production migration
> ทำแล้ว 2026-09-16 — body เป็น HTML เต็มฉบับ ลอกโครงจาก template ประกันรายได้เดิม
> (id 1501010–1501044) ทุกบรรทัด รวม meta charset=utf-8 · `check_docs.py` บังคับว่าต้องมีคอลัมน์นี้
- [x] ระบุ placeholder ที่ email-lib รองรับ และ validate placeholder ก่อน deploy
> รูปแบบยืนยันจากข้อมูลจริง: `${ชื่อ}` (ของเดิมใช้ 193 จุด · `{}` เปล่าเพียง 5 จุด)
> ตัวแปรที่ของเดิมมีอยู่แล้วใช้ชื่อเดิม: `${compCurrentUser}` `${compStoreCode}` `${compStoreName}`
> `${branchTypeI}` `${branchTypeFGIName}` `${compLoopNo}` `${link}`
> ที่เพิ่มใหม่: `${docNo}` `${ageDays}` `${pendingCount}` `${newDocCount}` `${jobName}` `${runId}` `${errorMessage}`
> `check_docs.py` ดักแล้วถ้ามีใครเขียน `{ชื่อ}` แบบไม่มี `$`
- [x] ยืนยัน sender/email_from ตาม environment
> วัดจากฐาน dev: `sender` = **อีเมลผู้ส่ง** · `email_from` = **ชื่อที่แสดง** (สลับกับที่ชื่อคอลัมน์ชวนให้เข้าใจ)
> ชุดประกันรายได้เดิมใช้ `noreply@cpall.co.th` / `SBP Mall System` ครบทั้ง 33 แถว — seed ใช้คู่เดียวกัน
> ⚠️ ยังไม่ได้แยกค่าตาม environment (uat/prod อาจใช้คนละ sender) — ต้องยืนยันตอน cutover
- [ ] map template กับ transition/batch/reminder ให้ครบ
- [ ] ทดสอบภาษาไทย UTF-8, HTML escaping, recipient/CC และข้อมูลที่อาจเป็นความลับ
- [ ] กำหนด behavior เมื่อหา template ไม่พบหรือ template inactive

เกณฑ์ตรวจรับ:

- [ ] template ทั้ง 8 active และไม่มี body ว่าง
- [ ] preview/test send ผ่านทุก template
- [ ] `email_sent` มี log สำเร็จ/ล้มเหลวและ trace กลับ document/interface ได้

### P1-RBK-01 — ทำ Rollback และ seed cleanup ให้ปลอดภัย

> ✅ **แก้เพิ่ม 2026-09-16 — ข้อกล่าวหาถูกต้อง เป็นความพลาดของรอบ 2026-09-15 เอง**
> รอบก่อนผมเพิ่มรายการ residue + คำสั่งล้างไว้ แต่ **ตก `common_code_type` ทั้งสองที่**
> และตัวเลข `common_code` ยังเป็น 13 ทั้งที่ย้าย `SGI_APPROVE_LIMIT` เข้ามาแล้วเป็น 14
> (หัวไฟล์นับจาก `len(SGI_DECISIONS) + len(SGI_DOC_STATUSES)` ซึ่งลืมบวก `SGI_APPROVE_LIMITS`)
>
> ✅ แก้ที่ generator แล้ว regenerate — ตอนนี้หัวไฟล์ระบุครบ 4 ตาราง พร้อมคำสั่งล้าง 4 บรรทัด
> และเพิ่มคำเตือน **ลบ `common_code` ก่อน `common_code_type` เสมอ** (ทะเบียน type ต้องหายทีหลังค่าที่อ้างมัน)

> 🟡 **รันได้ แต่เอกสาร cleanup ยังไม่ครบ (ตรวจซ้ำ 2026-09-16)**
> ✅ ตัดสินแล้วว่า **rollback ไม่ลบแถวในตารางของระบบเดิม** (ยึดกติกา "ไม่แตะตารางของระบบเดิม")
> ✅ ทดสอบ isolated rollback สองครั้งแล้ว: ตาราง 0 · index 0 · sequence 0 และติดตั้ง schema ใหม่ได้
>
> 🔴 header ปัจจุบันบอก residue ผิด: ต้องเป็น `common_code_type 3` · `common_code 14` ·
> `mas_param 11` · `email_template 8`; ไฟล์เขียนเพียง `common_code 13` · `mas_param 11` · template 8
> และไม่เอ่ย code type เลย
>
> 🔴 cleanup ท้าย `sgi_seed_data.sql` ลบ `common_code` เฉพาะ `SGI_DECISION/SGI_DOC_STATUS`
> จึงตก `SGI_APPROVE_LIMIT`; ทั้ง cleanup ของ seed และ rollback ไม่มีคำสั่งสำหรับ `common_code_type`
>
> 🔴 ผล “ไม่กระทบ object ระบบอื่น” ยังยืนยันไม่ได้จาก isolated DB เพราะ rollback ใช้
> `DROP TABLE ... CASCADE`; ตอนทดสอบเห็นอย่างน้อย constraint ข้ามตารางถูก cascade ตามปกติ
> ต้อง inventory dependency จริงก่อนใช้ใน environment ที่มี view/FK ของระบบอื่น
>
> ⏭️ **ไม่ทำ:** "แยก rollback สำหรับ Dev/UAT กับ production recovery" และ runbook —
> เป็นเอกสารปฏิบัติการที่ต้องมีเจ้าของระบบ production ร่วมเขียน · ไฟล์ปัจจุบันระบุชัดแล้วว่า **dev/uat เท่านั้น**


งานที่ต้องทำ:

- [ ] ตัดสินใจว่า rollback ต้องลบ SGI seed ใน `common_code_type`, `common_code`, `mas_param`, `email_template` หรือเก็บไว้
- [ ] ถ้าลบ ให้จำกัดด้วย business key + owner/migration version ห้ามลบแถวของทีมอื่น
- [ ] ถ้าเก็บ ให้ระบุผลกระทบและขั้นตอน reinstall ที่เจอข้อมูลเดิม
- [ ] แก้ residue manifest ให้รวม `common_code_type 3`, `common_code 14`, `mas_param 11`, `email_template 8`
- [ ] ถ้ามี manual cleanup ให้รวม `SGI_APPROVE_LIMIT` และพิจารณาลบ `common_code_type` หลังลบ code โดยจำกัด owner
- [ ] ตรวจ dependency ภายนอกก่อนใช้ `DROP TABLE ... CASCADE`
- [ ] แยก rollback สำหรับ Dev/UAT กับ production recovery
- [ ] ห้ามใช้ destructive rollback กับ production โดยไม่มี backup/approval/runbook

เกณฑ์ตรวจรับ:

- [ ] rollback ไม่ลบ view/FK/object ของระบบอื่นโดยไม่ตั้งใจ
- [ ] reinstall หลัง rollback ให้ desired state เดิม
- [ ] มีรายการ object/data ที่ rollback ลบและไม่ลบอย่างชัดเจน

### P1-DB-01 — ปิดช่องว่าง index ของ Foreign Key ฝั่งลูก

> ⏭️ **ยังไม่ทำ — และรอบก่อนตัดสินว่าไม่ต้องทำด้วยเหตุผลที่ยังใช้ได้**
> FK 3 เส้นที่ไม่มี index: `sgi_document_competitors.source_row_id` · `sgi_document_new_stores.source_row_id` ·
> `sgi_fgi_new_store_compensations.impact_store_id`
>
> เหตุผลเดิม (ตรวจ 2026-09-15): **ไม่มีโค้ดไหนลบแถวแม่** และ `source_row_id` ถูก**เขียนอย่างเดียว**
> ไม่เคยใช้เป็นเงื่อนไขกรอง → index จะเป็นภาระตอนเขียนโดยไม่มีใครได้ประโยชน์ตอนอ่าน
>
> ⚠️ **แต่ข้อกังวลของรอบ 2026-09-16 มีน้ำหนักในกรณีที่ยังไม่เกิด**: ถ้าวันหนึ่งมี migration/cleanup
> ที่ลบแถวแม่จริง `ON DELETE SET NULL` จะ scan ตารางลูกทั้งตาราง · **เป็นเรื่องที่ควรเคาะตอนเขียน runbook migration**
> ไม่ใช่ตอนนี้ที่ยังไม่มีเส้นทางนั้น · ถ้าทีม DB อยากเพิ่มไว้ก่อน เพิ่มได้ที่ generator ไม่กระทบอย่างอื่น


> 🟡 **พบใหม่ 2026-09-16** — PostgreSQL catalog ยืนยัน 28 FK และพบ 3 FK ที่ไม่มี index
> ซึ่งขึ้นต้นด้วยคอลัมน์ FK (`leading index`):
>
> | Child table | FK column | Parent | ผลกระทบหลัก |
> |---|---|---|---|
> | `sgi_document_competitors` | `source_row_id` | `sgi_fgi_impact_competitors.id` | parent delete/update และ audit reverse lookup ต้อง scan ลูก |
> | `sgi_document_new_stores` | `source_row_id` | `sgi_fgi_new_store_compensations.id` | parent delete/update และ trace source ต้อง scan ลูก |
> | `sgi_fgi_new_store_compensations` | `impact_store_id` | `sgi_fgi_impact_stores.id` | reverse lookup/parent mutation ต้อง scanข้อมูลรายงวด |
>
> PostgreSQL ไม่บังคับให้ FK ฝั่งลูกมี index จึงไม่ใช่ syntax/error blocker แต่ต้องมี workload/EXPLAIN
> รองรับก่อน production โดยเฉพาะสอง `source_row_id` ที่ออกแบบไว้เพื่อ audit trace โดยตรง

งานที่ต้องทำ:

- [ ] เก็บ cardinality/EXPLAIN ของ query และ parent update/delete ที่ใช้ FK ทั้ง 3 เส้น
- [ ] ถ้า workload ใช้ reverse lookup หรือ parent mutation ให้เพิ่ม index ผ่าน DDL generator ไม่แก้ generated SQL
- [ ] เพิ่ม automated FK-index coverage report; ถ้าตั้งใจไม่สร้างต้องมี reason/owner ต่อ FK
- [ ] ประเมิน index write/storage cost ของ Job 6/7/9 ก่อนอนุมัติ

เกณฑ์ตรวจรับ:

- [ ] FK ทั้ง 28 เส้นมี leading index หรือมี documented waiver ที่ DBA อนุมัติ
- [ ] query plan ของ trace/delete path ไม่เกิด sequential scan ที่เกินเกณฑ์ production

---

## P2 — ความถูกต้องและความสม่ำเสมอของเอกสาร

### P2-DOC-01 — แก้จำนวนตารางและ index ที่ตกยุค

> ✅ **แก้แล้ว 2026-09-15 — ตัวเลขผิดจริงทั้งสามจุด**
> นับจากไฟล์จริง: `CREATE TABLE` = **20** · `CREATE INDEX` = **24**
> · `CLAUDE.md` "20 ตาราง + **23** index" → 24 · และ "schema **19** ตาราง + 24 index" → 20
> · `database.md` "สร้าง **19** ตาราง + **23** index" → "**20 ตารางใหม่ + 24 index** · รวม reuse = **21 ตารางในขอบเขต**"
>
> 🟡 **ตรวจซ้ำ 2026-09-16:** `check_docs.py` ตรวจขอบเขต 20+1 และตรวจว่าคอลัมน์ของ index มีจริง
> แต่ `sgi_schema.sql` บังคับ fail เฉพาะ `t <> 20`; ค่า `i` ถูกพิมพ์เป็น `NOTICE` โดยไม่มี
> `IF i <> 24 THEN RAISE EXCEPTION` ดังนั้นจำนวน index ขาด/เกินยังไม่ทำให้ transaction ล้ม
> ต้อง derive expected count จาก generator ชุดเดิม ไม่ hardcode เป็นแหล่งความจริงใหม่ใน checker อื่น


- [x] แก้ `CLAUDE.md` จาก 23 index เป็น 24 index
- [x] แก้ `database.md` ส่วน SQL ติดตั้งจาก 19 ตาราง + 23 index เป็น 20 ตาราง + 24 index
- [x] ระบุให้ชัดว่า `plan-database.html` แสดง 20 ตารางใหม่ หรือ 21 ตารางใน scope รวม reuse
- [ ] เพิ่ม generated assertion ให้งานติดตั้ง fail เมื่อจำนวน target index ไม่ตรง manifest (ปัจจุบันตรวจ table อย่างเดียว)

### P2-SQL-01 — แก้ comment `data_name` ให้ตรง constraint

> ✅ **แก้แล้ว 2026-09-15** — comment เขียน "ชุดค่าปิด **9** ค่า" ทั้งที่ `CHECK` มี **12** ค่า
> นับจากฐานจริงยืนยันแล้ว: 12 ค่า · แก้ที่ `tools/build_lldd_documents.py` แล้ว regenerate
>
> ⏭️ **ไม่ทำ:** "เพิ่ม test เทียบ enum ใน SQL กับตาราง contract ใน `database.md`"
> — มีของเทียบเท่าอยู่แล้วคือ `__svc__/ddl-contract.svc.spec.ts` (ตรวจจาก catalog จริง)
> และการเทียบกับ **ข้อความในเอกสาร** เปราะกว่าการเทียบกับ **ฐานที่ติดตั้งจริง**


- [x] แก้ comment “ชุดค่าปิด 9 ค่า” ใน `sgi_schema.sql` ให้ตรง 12 ค่าจริง
- [x] ตรวจว่า 12 ค่าใน DDL ตรงกับ Job 2–12/8b และไม่มี interface ที่ตกหล่น
- [ ] เพิ่ม test เทียบ enum ใน SQL กับตาราง contract ใน `database.md`

### P2-API-01 — เพิ่ม validation contract ที่ตัวตรวจเดิมยังไม่ครอบคลุม

> 🔴 **แก้สถานะ 2026-09-16 — ตรวจ contract ได้และพบ error แม้ BE ยังไม่มี**
> SQL ใน LLDD/`plan-api.html` สามารถ parse กับ schema dump + seed ได้ตั้งแต่ก่อน implement และรอบนี้
> พบ lookup พังจริง 2 query (ดู P0-API-02) จึงห้ามเลื่อน automated contract validation ทั้งหมดไปหลังมี BE
> ส่วน response envelope/auth/runtime behavior ยังเป็น `TO-BE` และต้องเพิ่มเมื่อ controller มีจริง


- [ ] ตรวจ API lookup ว่าอ้าง code type ที่ seed มีจริง
- [ ] ตรวจ config key ใน API/Backend ว่ามีใน seed
- [ ] ตรวจ workflow endpoint ว่า state/event/route มีใน workflow definition
- [ ] ตรวจ response/error envelope `{success,data,error}` ตาม store-backend
- [ ] ตรวจกรณี lookup/config มีค่าซ้ำ, inactive, หาย หรือชนิดข้อมูลผิด

### P2-DOC-02 — ล้าง contract drift ที่ยังเหลือระหว่าง DDL/seed/living docs/LLDD

> ⏭️ **ยังไม่ทำในรอบนี้** — ต้องไล่ทีละข้อกับของจริงก่อน เหมือนที่ทำกับ P1-DOC-03/04 แล้วพบว่า
> **สองในสามข้อของรอบก่อนไม่ตรงข้อเท็จจริง** จึงไม่ควรแก้ตามคำอธิบายโดยไม่ตรวจ
> ✅ ส่วนที่ตรวจและแก้ไปแล้วในรอบนี้: `SGI_APPROVE_LIMIT` (ย้ายไป `common_code` · seed ตรงกับ contract §5.5.2)
> และ threshold source ที่ lookup SQL อ่าน (แก้ที่ P0-API-02)
> ⏭️ เหลือ `approver_snapshot` และ seed owner — ต้องตรวจก่อนว่า drift จริงหรือเป็นข้อความที่อ่านคนละบริบท


> 🔴 **พบใหม่ 2026-09-16** — static checker ผ่าน แต่ข้อความต่อไปนี้ยังขัดกับ artifact ปัจจุบัน:

| จุดอ้างอิง | ข้อความปัจจุบัน | ข้อเท็จจริงจาก DDL/seed |
|---|---|---|
| `database.md` แถว `CompensateFlow` | `approver_snapshot` ยังไม่ได้เติม DDL | `sgi_compensation_documents.approver_snapshot JSONB` มีแล้ว |
| `database.md` workflow mapping | threshold อยู่ `common_code` **หรือ** `workflow_route.condition_json` | canonical seed อยู่ `common_code` (`THRESHOLD`/`code_name=100000`) |
| `plan-database.html` | threshold อยู่ `common_code` **หรือ eventParam** | eventParam ควรเป็น input สำหรับเลือก route ไม่ใช่ source เก็บค่า |
| `workflow.md` | แสดง `condition_json.value=100000` เหมือน route จริง | LLDD บอกห้ามเก็บ threshold ซ้ำใน condition JSON แต่ยังใช้ตัวเลขตัวอย่างเดียวกัน |
| `LLDD-BE-Integration-SBP-Platform` SQL ตัวอย่าง | owner `SGI-SETUP` | generated seed/cleanup ใช้ `SGI-INSTALL` |
| `LLDD-BE-API-Lookup` | statuses จาก `workflow_status`; sections อ่าน `other_value` | LLDDv2/API Catalog ชี้ status ไป `common_code`; threshold อยู่ `code_name` |

งานที่ต้องทำ:

- [ ] ปิด D-001 แล้วระบุให้ชัดว่า `common_code` เป็น source; `eventParam` เป็น derived routing input หรือไม่
- [ ] เลือก owner marker เดียวและทำ migration/cleanup ตามค่านั้น
- [ ] แก้ source generator ของ LLDD/HTML และ living docs คู่กันตาม repo guidance
- [ ] เพิ่ม checker เทียบ seed field mapping กับ SQL ของ lookup ไม่ใช่ตรวจเพียงว่าชื่อตารางปรากฏ
- [ ] เพิ่ม checker สำหรับข้อความ “ยังไม่มีใน DDL” เทียบ canonical column inventory

เกณฑ์ตรวจรับ:

- [ ] ไม่มีคำว่า “หรือ” ที่เปิดให้เก็บ threshold มากกว่าหนึ่ง source โดยไม่มี Decision ID
- [ ] lookup SQL ใช้ business key/column เดียวกับ seed manifest
- [ ] owner marker, residue count และ cleanup list ตรงกันทุกเอกสาร
- [ ] `python3 tools/check_docs.py` ดัก regression ทั้งหกแถวข้างบนได้

---

## ลำดับการแก้ไขที่แนะนำ

- [ ] 1. แก้ P0-API-02 และปิด D-001/D-004: source ของ status/threshold + workflow version/route
- [ ] 2. แก้ P1-MIG-01/P1-SEED-01: migration lock, duplicate detection, exact manifest และ owner marker
- [ ] 3. แก้ P1-RBK-01: residue count/cleanup ให้ครบ แล้วทำ dependency audit ก่อนใช้ `CASCADE`
- [ ] 4. ทำ P1-TEST-01 ให้ stub ตรงฐานจริงและ checker หยุดเมื่อ load fail
- [ ] 5. ตัดสิน `SGI_DATASOURCE`, parameter consumer/fallback และ email body/template ID mapping
- [ ] 6. ประเมิน/เพิ่ม FK index 3 เส้น หรือแนบ DBA waiver
- [ ] 7. แก้ source generator ของ schema/seed/LLDD/HTML แล้ว regenerate; ห้ามแก้ generated artifact อย่างเดียว
- [ ] 8. ล้าง contract drift ใน `database.md`, `workflow.md`, `api.md`, HTML, LLDD และ LLDDv2
- [ ] 9. รัน static + PostgreSQL integration + concurrent/partial-state/rollback tests
- [ ] 10. เมื่อ BE พร้อม ให้ทดสอบ API lookup/workflow/email happy path และ failure path end-to-end

---

## ชุดคำสั่งตรวจรับขั้นต่ำ

```sh
python3 tools/check_docs.py
python3 tools/build_sgi_schema_sql.py
python3 tools/check_sgi_sql_columns.py
git diff --check
```

หลัง regenerate ต้องตรวจด้วย PostgreSQL version เดียวกับ environment เป้าหมาย:

- [ ] รัน existing-table stub เฉพาะ test environment
- [ ] รัน `sgi_schema.sql`
- [ ] รัน `sgi_seed_data.sql` สองครั้ง
- [ ] รัน `sgi_seed_data.sql` พร้อมกันสอง session และจาก partial state อย่างน้อยหนึ่งกรณี
- [ ] ตรวจจำนวนตาราง/index/seed และค่าจริง ไม่ตรวจเฉพาะจำนวนแถว
- [ ] parse/execute SQL ของ lookup 2 เส้นกับ schema `workflow_*` จริง
- [ ] รัน workflow setup สองครั้งตาม idempotency contract
- [ ] เรียก lookup API และ workflow happy path/return path
- [ ] ทดสอบ email EM-01 ถึง EM-08
- [ ] รัน rollback ตาม runbook แล้วตรวจ object/data ของระบบเดิม
- [ ] รันติดตั้งใหม่หลัง rollback

---

## Definition of Done

- [ ] ไม่มี P0 หรือ P1 ค้าง
- [ ] SQL ทั้งชุดรันบน PostgreSQL เป้าหมายได้ใน transaction/dependency order ที่กำหนด
- [ ] Schema มี 20 ตารางใหม่และ 24 index ตาม source of truth
- [ ] ขอบเขตเอกสารระบุ 21 ตารางเมื่อรวม `fcs_qssi_score` ที่ reuse
- [ ] `common_code_type`, `common_code`, `mas_param` และ `email_template` มี SGI data ครบและไม่ซ้ำ
- [ ] sequential/concurrent/partial-state seed ให้ desired state เดียวกัน หรือ fail ก่อน commit โดยไม่เกิด duplicate
- [ ] stub/catalog ที่ใช้ทดสอบตรงกับ PK/unique/null/default ของฐานเป้าหมาย
- [ ] FK ทั้ง 28 เส้นมี index หรือ DBA waiver พร้อมหลักฐาน query plan
- [ ] Workflow version/state/status/event/route/part/email mapping พร้อมใช้งาน
- [ ] SQL lookup statuses/sections execute ได้และคืน canonical code/threshold จาก seed ชุดเดียวกัน
- [ ] Database, Workflow, API, LLDD, Java/config และ generated SQL ใช้ชื่อ/ค่า contract เดียวกัน
- [ ] Seed, upgrade, rerun, recovery และ rollback มีผลทดสอบแนบ
- [ ] ทีม Database, Workflow, Backend/Batch, API และ Business sign-off ส่วนที่ตนเป็นเจ้าของ

---

## ✅ ติดตั้ง `sgi_seed_data.sql` ลงฐาน dev จริง — 2026-09-16

ยิงด้วย `tools/apply_sgi_sql.py --confirm` (guard 4 ข้อผ่านครบ) บน **PostgreSQL 17.7** schema `sps_store`
ผลตรงกับตารางทำนายที่ประกาศไว้ก่อนยิง **ทุกตัว**:

| ตาราง | ก่อน | หลัง | ทำนาย |
|---|---:|---:|---:|
| `common_code_type` (SGI) | 1 | 3 | 3 ✅ |
| `common_code` (SGI) | 1 | 14 | 14 ✅ |
| `mas_param` (SGI_*) | 4 | 11 | 11 ✅ |
| `email_template` (SGI-SETUP) | 0 | 8 | 8 ✅ |
| `sgi_competitors` | 0 | 11 | 11 ✅ |
| `sgi_external_factors` | 0 | 4 | 4 ✅ |
| `sgi_document_running_numbers` | 0 | 1 | 1 ✅ |

idempotency พิสูจน์แบบอ่านอย่างเดียว: ดึงเงื่อนไข `WHERE NOT EXISTS` ออกมาทั้ง **52 ข้อ**
แล้วเช็คว่า "มีอยู่แล้ว" ครบทุกข้อ → รันซ้ำจะไม่เพิ่มแถวใด ๆ

### 🔴 บั๊กจริงที่เจอรอบนี้ — sequence ของตารางระบบเดิมตามหลังข้อมูลตัวเอง

รอบแรกล้มด้วย `duplicate key value violates unique constraint "email_template_pkey"`
`Key (email_template_id)=(1201012) already exists` · ทั้ง transaction rollback ครบ ไม่เหลือขยะ (ตรวจแล้ว)

วัดจากฐานจริง:

- `max(email_template_id)` = **1501044** · 126 แถว
- `email_template_email_template_id_seq.last_value` = **1201012**
- ช่วง id ที่ใช้อยู่: `1–6007` (74) · `1101001–1101006` (6) · `1201001–1201013` (13) · `1501010–1501044` (33)

แปลว่า **ทีมอื่น INSERT ด้วย id ที่ระบุเอง แบ่งเป็นช่วงตามทีม/migration** — `nextval()` ไม่ใช่ตัวแจก id จริง
seed ของเราไม่ได้ hardcode id เลย แต่ปล่อยให้ column default (`nextval`) ทำงาน จึงได้เลขที่มีแถวอยู่แล้ว

**ทางเลือกที่พิจารณา**

| | ทำอะไร | ทำไมไม่เลือก / เลือก |
|---|---|---|
| ก | `setval()` ซ่อม sequence ให้เจ้าของ | ❌ แก้ object ที่เราไม่ได้เป็นเจ้าของ — ผิดข้อตกลง "ตารางระบบเดิม INSERT ได้อย่างเดียว" |
| ข | คำนวณ id เองจาก `max()+1` | ✅ **เลือกข้อนี้** — ไม่แตะ sequence ของใคร · advisory lock ที่หัวไฟล์กัน race |
| ค | รายงานทีมเจ้าของแล้วพัก email_template ไว้ | ❌ บล็อกงานทั้งชุดโดยไม่จำเป็น เพราะ (ข) ปลอดภัยอยู่แล้ว |

id ที่ได้จริง: **1501045–1501052** (ต่อท้ายช่วงสูงสุดพอดี · ไม่ชนช่วงของใคร · ตรวจแล้วไม่มี id ซ้ำทั้งตาราง)

⚠️ **sequence ของ `email_template` ยังตามหลังอยู่เหมือนเดิม** — เป็นข้อบกพร่องของ environment ไม่ใช่ของเรา
คนต่อไปที่ INSERT โดยพึ่ง `nextval()` จะเจอปัญหาเดียวกัน · **ควรแจ้งทีมเจ้าของตารางให้ `setval()` ซ่อม**

### เครื่องมือที่เพิ่ม

`tools/apply_sgi_sql.py --trial` — รันไฟล์จริงบนฐานจริงแล้ว **ROLLBACK เสมอ** พร้อมยืนยันว่าตัวนับกลับสภาพเดิม
ใช้พิสูจน์ syntax/constraint/duplicate key ก่อนยิงจริง โดยไม่เขียนอะไรค้างไว้ — รอบนี้จับได้ก่อนยิงจริง

---

## ✅ แก้รูปแบบ `email_template` ให้ตรงของเดิม + อัปเดตฐาน dev — 2026-09-16 (รอบสอง)

ผู้ใช้ทักท้วงว่าที่ seed ไปตอนเช้า **ยังไม่ถูก** — ตรวจกับข้อมูลจริง 126 แถวของทีมอื่นแล้วยืนยันว่าจริง

| ช่อง | ที่เราทำผิด | ของจริงในฐาน |
|---|---|---|
| ตัวแปร | `{docNo}` | **`${docNo}`** — ของเดิมใช้ `${}` 193 จุด · `{}` เปล่าเพียง 5 จุด |
| `body_format` | `''` ว่าง | HTML เต็มฉบับ — **126/126 แถวมีเนื้อหา ไม่มีแถวว่างเลย** |
| `sender` | ไม่ได้ใส่ | `noreply@cpall.co.th` = **อีเมลผู้ส่ง** |
| `email_from` | ไม่ได้ใส่ | `SBP Mall System` = **ชื่อที่แสดง** (สลับกับที่ชื่อคอลัมน์ชวนให้เข้าใจ) |

ชุด template ประกันรายได้เดิมอยู่ที่ id **1501010–1501044** (33 แถว) ใช้คู่ sender/email_from เดียวกันครบทุกแถว
และมีคำศัพท์ตัวแปรแค่ 7 ตัว — `${compCurrentUser}` `${compStoreCode}` `${compStoreName}`
`${branchTypeI}` `${branchTypeFGIName}` `${compLoopNo}` `${link}` — **seed ใช้ชื่อเดิมทั้งหมด ไม่ตั้งใหม่**
ที่เพิ่มเฉพาะแนวคิดที่ระบบเดิมไม่มี: `${docNo}` `${ageDays}` `${pendingCount}` `${newDocCount}`
`${jobName}` `${runId}` `${errorMessage}`

body ลอกโครงเดิมทุกบรรทัด รวม `<title>Untitled Document</title>` ตามที่ผู้ใช้สั่งว่าส่วนที่ยังไม่มี
ข้อมูลของตัวเองให้ยึด data เดิมไปก่อน

### บั๊กพ่วงที่เจอระหว่างแก้

- **คำสั่งล้างในหัวไฟล์ rollback ใช้ `create_by = 'SGI-INSTALL'`** ทั้งที่ของจริงประทับ `SGI-SETUP`
  ลอกไปรันแล้วจะลบไม่ได้สักแถว — แก้ให้ดึงจาก `SEED_OWNER` แล้ว
- `check_docs.py` ใช้ `split(";")` ตรง ๆ — `&nbsp;` ใน HTML ทำให้หั่นกลางคำสั่งแล้วรายงานผิดว่า
  "ไม่มี WHERE NOT EXISTS" ทั้งที่มี — เปลี่ยนเป็นตัวแยกที่เคารพ string literal

### กฎใหม่กันถอยหลัง (`check_docs.py`)

INSERT ลง `email_template` ต้องมี `body_format`/`sender`/`email_from` ครบ และห้ามมี `{ชื่อ}` ที่ไม่มี `$`
ทดสอบด้านลบแล้วว่ากฎจับได้จริง

### เครื่องมือใหม่ `tools/reseed_sgi_seed_rows.py`

seed ใช้ `INSERT ... WHERE NOT EXISTS` จึง **รันซ้ำแล้วไม่อัปเดตของเดิม** — แก้ค่า seed แล้วรันใหม่
ค่าเก่าจะค้างเงียบ ๆ (หัวไฟล์ seed เตือนไว้ แต่ไม่มีเครื่องมือทำให้) สคริปต์นี้ลบ + seed ใหม่ในทรานแซกชันเดียว

ขอบเขตที่บังคับในโค้ด แก้จาก command line ไม่ได้: ลบได้เฉพาะ 4 ตารางใน `ALLOWED`
และเฉพาะแถวที่ประทับ `create_by/create_user = SEED_OWNER` · ก่อนลบตรวจว่าไม่มีคอลัมน์ใดในฐานอ้างถึง id ที่จะลบ

### ผลบนฐาน dev

ตรวจก่อนลบ: `workflow_route.email_id` · `email_sent.email_id` · `wf_route.then_email_with_id` ·
`wf_email_template` = **0 แถว** และ **ไม่มี FK ชี้มาที่ `email_template` เลย**

หลังรัน: 8 แถว id **1501045–1501052** (ชุดเดิมพอดี เพราะลบแล้ว `max()` กลับไป 1501044) ·
subject/body เป็น `${}` ครบ · sender/email_from ครบทุกแถว · **ทั้งตาราง 134 แถว body ว่าง 0 แถว**
