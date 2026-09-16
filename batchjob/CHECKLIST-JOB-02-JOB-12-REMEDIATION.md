# Checklist แก้ไขเอกสารและสเปก Batch Job 2–12

> ## ⚠️ ไฟล์นี้เป็นฉบับเก่า — อย่าใช้ทำงาน
>
> ฉบับที่ใช้งานจริงอยู่ที่
> **`SBP/srm-sps-spsap-sop-sgi-batch/CHECKLIST-JOB-02-JOB-12-REMEDIATION.md`**
> (ยาวกว่าเท่าตัว · มีข้อที่เพิ่มหลังลงมือเขียนโค้ดจริง · มีการติ๊กความคืบหน้า)
>
> ไฟล์นี้เก็บไว้เป็นบันทึกรอบตรวจ **2026-09-12** เท่านั้น — เครื่องหมายติ๊กในนี้ตกยุคแล้ว
> *(ป้ายนี้เพิ่ม 2026-09-14 เพราะมีสองไฟล์ชื่อเดียวกันคนละที่ เสี่ยงหยิบผิดฉบับ)*


> สร้างจากการตรวจเทียบเอกสารอธิบายละเอียดใน `batchjob/`, Java legacy ใน
> `batchjob/fcsJar/`, LLDD ของ Job 2–12 และ DDL ใหม่ใน `output/sql/sgi_schema.sql`
>
> **วันที่ตรวจ:** 2026-09-12  
> **ขอบเขต:** Jobs 2–12 รวม Job 8b · schema ใหม่ · schedule/dependency · ความปลอดภัยของ legacy snapshot  
> **วิธีใช้:** แก้ตามลำดับ P0 → P1 → P2 และติ๊ก `[x]` เมื่อผ่านเกณฑ์ตรวจรับของข้อนั้นจริง
>
> Checklist รายละเอียดเดิมของ Job 2/3 ยังอยู่ที่
> [CHECKLIST-JOB-02-JOB-03-REMEDIATION.md](CHECKLIST-JOB-02-JOB-03-REMEDIATION.md)
> เอกสารฉบับนี้ไม่แทนที่ข้อที่ยังเปิดอยู่ในไฟล์เดิม

---

## สถานะรวม

- [ ] P0 — ถอน/หมุนเวียน credentials ที่อยู่ใน legacy snapshot และกำหนดวิธีเก็บ snapshot ที่ปลอดภัย
- [ ] P0 — ทำ competitor identity ของ Job 3/7 ให้ idempotent แม้ `COMPET_ID` ว่าง
- [ ] P0 — แก้ Job 3 mapping/metrics ให้ตรง DDL ใหม่
- [ ] P0 — แก้ LLDD Job 7 ที่ยังใช้ `competitor_code` และ `source_system=ALM`
- [ ] P0 — กำหนด dependency ของ Jobs 2/3 และ Jobs 7/8/8b/9 ให้ enforce ได้จริง
- [ ] P1 — แก้คำอธิบาย business flow ของ Job 5 ให้ตรงกับ Gate ของ Job 8b
- [ ] P1 — แก้กติกาการเตือน Job 12 ไม่ให้พึ่งสมมติฐาน “7 วันทำการต่อสัปดาห์”
- [ ] P1 — ทำ baseline ของ `fcsJar` ให้ตรวจสอบย้อนกลับได้
- [ ] P2 — เก็บงานเลขหัวข้อ, cross-reference, README และ repo guidance
- [ ] Final — เอกสารอธิบาย, LLDD, DDL, generated skeleton และ deployment ใช้ contract เดียวกัน

---

## P0 — ต้องแก้ก่อนเริ่ม implementation

### P0-SEC-01 — ถอน credentials ออกจาก legacy snapshot

- [x] จัดทำบัญชี credentials ที่พบโดย **ไม่คัดลอกค่าจริงลงเอกสารหรือ ticket**
- [ ] rotate/revoke database, SFTP, K2 Basic Auth และ cloud access keys ที่พบ
- [x] ตรวจว่า credential ใดเป็น production/UAT/STQA และระบุเจ้าของระบบ
- [ ] ย้ายค่า runtime ของระบบใหม่ไป Secret Manager/Vault ตามมาตรฐานองค์กร
- [ ] สร้าง sanitized snapshot ของ `fcsJar` สำหรับใช้เป็นหลักฐานอ้างอิง
- [x] เพิ่ม secret scanning ใน CI/pre-commit ก่อนนำ `batchjob/` เข้า repository หลัก
- [ ] ตรวจ git history ของ nested repository เพราะการลบเฉพาะ working tree ไม่ได้ลบค่าจาก history
- [ ] ห้ามเผยแพร่ไฟล์ PDF/เอกสารเก่าที่อาจคัดลอก credential จริงไว้โดยไม่สแกนก่อน

ไฟล์หลักที่ต้องตรวจ:

- `batchjob/fcsJar/ApplicationResources.properties`
- `batchjob/fcsJar/jdbc.properties`
- `batchjob/fcsJar/config.xml`
- `batchjob/fcsJar/src/th/co/gosoft/fgi/Constant/FgiConstant.java`
- `batchjob/fcsJar/src/th/co/gosoft/fml/constant/CipherKey.java`

เกณฑ์ตรวจรับ:

- [ ] secret scanner ไม่พบ active credential ใน snapshot ที่จะแชร์/commit
- [ ] credential เดิมถูกยกเลิกหรือหมุนเวียนแล้ว ไม่ใช่เพียงลบข้อความออกจากไฟล์
- [ ] ระบบใหม่โหลด secret จาก reference/ARN/environment injection โดยไม่ log ค่าออกมา

### P0-DB-01 — สร้าง stable identity ให้แถวคู่แข่งที่ `COMPET_ID` ว่าง

ปัญหาปัจจุบัน:

- `sgi_fgi_impact_competitors` ใช้ `UNIQUE (impact_process_id, competitor_store_code, period_key)`
- `sgi_document_competitors` ใช้ `UNIQUE (doc_no, competitor_store_code)`
- `competitor_store_code` เป็น nullable และข้อมูลตัวอย่างมีค่าว่าง 56 แถว
- PostgreSQL ให้หลายแถวที่มี `NULL` ผ่าน UNIQUE ได้ และ `ON CONFLICT` จะไม่ match แถว NULL เดิม

งานที่ต้องทำ:

- [ ] เลือก stable source identity สำหรับแถวที่ไม่มี `COMPET_ID`
  - [ ] ทางเลือก A — เก็บ `source_row_id` จากต้นทาง
  - [ ] ทางเลือก B — สร้าง deterministic `source_row_hash` จากฟิลด์ที่ยืนยันแล้วว่าแยกสาขาได้
  - [ ] ทางเลือก C — reject/quarantine แถวที่ไม่มี identity พร้อม business sign-off
- [ ] ห้ามใช้เพียง `NULLS NOT DISTINCT` ถ้าจะทำให้คู่แข่งรหัสว่างหลายสาขาถูกยุบเหลือแถวเดียว
- [ ] ปรับ UNIQUE ของ source table และ document table ให้ใช้ identity เดียวกัน
- [ ] ปรับ Job 3 import, Job 7 upsert และ Job 7 prune ให้ใช้ identity เดียวกัน
- [ ] เพิ่ม traceability จาก `sgi_document_competitors` กลับไป source row
- [ ] อัปเดต DDL source (`tools/build_lldd_documents.py`) แล้ว regenerate SQL/LLDD

เกณฑ์ตรวจรับ:

- [ ] import แถว `COMPET_ID` ว่างหลายแถวได้โดยไม่ทำข้อมูลหาย
- [ ] rerun Job 3/7 ไม่เพิ่มจำนวนแถวซ้ำ
- [ ] prune ลบเฉพาะ source row ที่หายไปจริง ไม่ลบ/คงทุกแถว NULL พร้อมกัน
- [ ] concurrent run สอง instance ไม่สร้าง duplicate business row

หลักฐาน:

- [JOB-03 หัวข้อ competitor identity](JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md#7-เขียนลงฐานข้อมูลใหม่ตรงไหน)
- [JOB-07 หัวข้อ source row](JOB-07-SyncCompetitorToDocument-อธิบายละเอียด.md#-b--impact_competitor_id-ฟิลด์-1-หายไป)
- `output/sql/sgi_schema.sql` ตาราง `sgi_fgi_impact_competitors` และ `sgi_document_competitors`

### P0-J3-01 — แก้ Job 3 mapping และ metrics ที่ยังอ้าง schema เก่า

- [x] แก้ `COMPET_ID` จาก “รหัสแบรนด์ที่ต้อง map master” เป็น `competitor_store_code` ซึ่งไม่มี FK
- [x] ระบุว่า `brand_code` ได้จากการ map ชื่อแบรนด์ `NAMT`/`NAME`
- [x] ลบข้อความว่า `NAME`, `ZONE_CODE`, `SUBZONE_CODE` ไม่มีที่เก็บ เพราะ DDL เพิ่มแล้ว
- [x] แก้ข้อความ UNIQUE เก่าจาก `competitor_code` เป็น identity ที่เลือกใน P0-DB-01
- [x] เปลี่ยน `rejectedCount` ที่หมายถึง COMPET_ID ไม่อยู่ใน master เป็น `unmappedBrandCount`
- [x] ยืนยันว่า map brand ไม่ได้ยังเก็บ row โดย `brand_code = NULL` หรือเปลี่ยนนโยบายพร้อม sign-off
- [x] แก้ reconciliation equation ให้ไม่ลบ `unmappedBrandCount` หากยังเก็บแถวนั้น
- [ ] ทำ mapping table, test cases และ metrics ในเอกสารอธิบายกับ LLDD ให้ตรงกัน

ไฟล์ที่ต้องแก้:

- `batchjob/JOB-03-ImportImpactCompetitor-อธิบายละเอียด.md` บรรทัดเดิมประมาณ 166–177, 239 และ 417–436
- `LLDD/md/Jobs/LLDD-BE-Job-3-ImportImpactCompetitor.md`
- source generator ที่สร้าง LLDD/DDL ส่วน Job 3

### P0-J7-01 — ล้าง contract เก่าจาก LLDD Job 7

- [x] เปลี่ยน `competitor_code` ทุกจุดเป็น `competitor_store_code`/stable identity ที่เลือก
- [x] แก้ `ON CONFLICT (doc_no, competitor_code)` ซึ่งอ้างคอลัมน์ที่ไม่มีจริง
- [x] เลือก `source_system` ค่าเดียวระหว่าง `ALLMAP` กับ `ALM`
- [x] ใช้ค่าที่เลือกให้ตรงกันใน INSERT, prune, skeleton, log, rerun note และ test
- [x] แก้ target table description ที่ยังเขียน `source_system=ALM`
- [ ] ตรวจ generated repository SQL ทุกชุดว่าอ้างคอลัมน์จริงของ DDL
- [x] แก้ที่ source generator แล้ว regenerate; ห้ามแก้เฉพาะ Markdown generated

เกณฑ์ตรวจรับ:

- [ ] SQL Job 7 รัน parse/prepare กับ PostgreSQL ได้
- [x] `tools/check_docs.py` มีกฎจับ `ON CONFLICT` ที่อ้างคอลัมน์/constraint ไม่มีจริง
- [ ] rerun และ prune ใช้ business key และ `source_system` ชุดเดียวกันทุกเอกสาร

หลักฐาน: `LLDD/md/Jobs/LLDD-BE-Job-7-SyncCompetitorToDocument.md` บรรทัดเดิมประมาณ 64, 306, 464, 585, 641, 654 และ 669

### P0-ORCH-01 — กำหนด dependency ที่ระบบบังคับใช้จริง

- [ ] Job 3 ต้องไม่เขียนก่อนที่ parent จาก Job 2 พร้อม หรือเลือกนโยบายอื่นจาก checklist Job 2/3 ให้ชัด
- [x] เลิกใช้ cron เวลาเดียวกันเป็นตัวรับประกันลำดับ Job 2 → Job 3
- [x] กำหนด Job 8 → Jobs 7 และ 9 เพราะทั้งสองต้องใช้ `doc_no`
- [ ] กำหนด Job 8 → Job 8b หรือ chain ที่ตกลง หาก Job 8b ต้องเริ่มหลังสร้างเอกสาร
- [ ] กำหนด retry/backfill เมื่อ upstream สำเร็จแต่ downstream ไม่ได้ถูก trigger
- [ ] กำหนด dependency ใน AWS Batch/EventBridge/Step Functions จริง ไม่ใช่เฉพาะในเอกสาร
- [x] ทำ schedule table กลางหนึ่งชุด แล้วให้ README, LLDD, runbook และ deployment อ้างชุดเดียวกัน

เกณฑ์ตรวจรับ:

- [ ] Job 7/9 ไม่พบ `pendingNoDocumentCount` เพราะ race ตามปกติ
- [ ] downstream retry ได้โดยไม่สร้างข้อมูลซ้ำ
- [ ] มี integration test จำลอง upstream fail, downstream fail และ manual rerun

### P0-J2J3-01 — ปิด design blockers ที่ค้างจาก checklist เดิม

- [ ] เลือกความสัมพันธ์ Job 3 กับ `impact_process_id`
- [ ] กำหนดโดเมนและ state transition ของ `process_status`
- [ ] เลือก idempotency contract ของ Job 3: skip ทั้งงวด / replace / upsert พร้อม completeness marker
- [ ] เลือก scope การกวาดแถว `W` ของ Job 2
- [ ] กำหนด owner ของแถว datasource `STA`, `PRO`, `REA`
- [ ] กำหนด `branchtype` source of truth
- [ ] กำหนด policy re-import คู่ร้านที่เคยเป็น `N`
- [ ] กำหนดผู้เติม `opt_dv_user_id` ก่อน Job 8b
- [ ] ปิด `URL_EMBEDDED/allmap_url` data lineage

อ้างอิงรายละเอียดและหลักฐานใน
[CHECKLIST-JOB-02-JOB-03-REMEDIATION.md](CHECKLIST-JOB-02-JOB-03-REMEDIATION.md)

---

## P1 — ต้องแก้ก่อนส่งให้ทีมพัฒนา

### P1-J5-01 — ทำ flow Job 5 → Job 8b ให้ตรงกับ legacy

- [x] แก้แผนภาพ/ข้อความ Job 5 ที่บอกว่า `growth_rate_diff < 0` แล้วเข้า workflow ทันที
- [x] ระบุว่า Job 5 ให้ `Y` เมื่อ `< 0` แต่ Job 8b Gate ใช้ `<= -10`
- [x] ระบุว่าแถว `-10 < diff < 0` ค้าง `W` ใน legacy
- [x] แก้ข้อความว่า `growth_rate_diff = NULL` “ไหลเข้า workflow” เพราะ Job 8b ไม่เลือกแถวดังกล่าว
- [ ] เลือกเกณฑ์ระบบใหม่เพียงชุดเดียว หรือบันทึกเหตุผลที่ต้องมีสองเกณฑ์
- [ ] กำหนด outcome ของ `NULL`, `sales_status='E'` และช่วง `-10 < diff < 0`
- [ ] ย้าย threshold `-10` ไป config หากยังใช้
- [ ] ขอ business sign-off เพราะมีผลต่อสิทธิชดเชย

หลักฐาน:

- `batchjob/fcsJar/src/th/co/gosoft/fgi/dao/jdbc/ImportJdbc.java` เมธอด `updateStatusImpactStoreSaleByDiff`
- `batchjob/fcsJar/src/th/co/gosoft/fgi/dao/jdbc/StartFlowJdbc.java` เงื่อนไข `growth_rate_diff <= -10`
- [JOB-08b หัวข้อ Gate G5](JOB-08b-StartInternalWorkflow-อธิบายละเอียด.md#-g5-กับ-job-5-ใช้เกณฑ์คนละตัวบนตัวเลขเดียวกัน)

### P1-J5-02 — แยก metrics “ข้อมูลเสีย” ออกจากผลธุรกิจ N

- [x] เพิ่ม `invalidLineCount` หรือ `inputRejectedCount` สำหรับบรรทัดว่าง/ฟิลด์ไม่ครบ/ยอดขายไม่ใช่ตัวเลข
- [x] ใช้ `businessRejectedCount` สำหรับร้านที่ผลการประเมินเป็น `N`
- [ ] ระบุว่า malformed row ทำให้ reject รายแถวหรือ fail ทั้งไฟล์
- [x] แก้ reconciliation equation ให้รวม invalid, skipped, unmatched และ inserted ครบ
- [x] เพิ่ม error reason และ source line number เพื่อ audit/retry
- [ ] เพิ่ม test mixed valid/invalid lines และไฟล์ที่ invalid ทั้งหมด

### P1-J12-01 — ออกแบบการเตือนซ้ำจาก notification state ไม่ใช่ช่วง 7 วัน

- [x] ลบคำรับประกันว่า bucket 7 วันทำให้เตือน “พอดี 1 ครั้ง” จนกว่าจะพิสูจน์ calendar จริง
- [ ] ยืนยันปฏิทิน `Franchise Working Day`, ชั่วโมงต่อวัน และนิยาม `TotalDayOfWorkingHour`
- [x] แก้ตัวอย่างอายุ `33 → 40` ไม่ให้สมมติว่า 1 สัปดาห์ปฏิทินเท่ากับ 7 วันทำการ
- [ ] เพิ่ม notification history/marker ต่อเอกสารและระดับ 30/45/60 วัน
- [ ] กำหนด catch-up เมื่อ job ไม่ได้รันในสัปดาห์ก่อน
- [ ] กำหนด escalation สำหรับงานเกิน 66 วัน
- [ ] ป้องกันการส่งซ้ำเมื่อ rerun วันเดียวกันหรือหลาย instance พร้อมกัน

เกณฑ์ตรวจรับ:

- [ ] วันหยุดยาวไม่ทำให้เอกสารถูกเตือนซ้ำหรือหลุดถาวร
- [ ] job ที่ขาดหนึ่งรอบกลับมา catch up ได้
- [ ] มี audit ว่า doc ใดถูกเตือนระดับใด เมื่อไร และส่งสำเร็จหรือไม่

### P1-J3-01 — ทำข้อความ พ.ศ./ค.ศ. ให้เป็นสถานะเดียวกัน

- [x] ลบคำยืนยันว่า argument ที่ “ใช้จริง” เป็น พ.ศ. หากไม่มีหลักฐาน environment/run log
- [x] แยก “ตัวอย่างในเอกสารเดิม” ออกจาก “ค่าจริงที่ ALLMAP ต้องการ”
- [ ] query `SELECT DISTINCT PERIOD_YEAR` จาก source views ใน environment ที่ถูกต้อง
- [ ] เก็บผล query, วันที่, environment และผู้ยืนยันไว้เป็น evidence
- [x] รับ ค.ศ. ใน input ระบบใหม่และแปลง ณ adapter boundary เพียงจุดเดียว หาก ALLMAP ใช้ พ.ศ.
- [x] ทำ Job 2 และ Job 3 ใช้ calendar contract เดียวกัน

### P1-J7-01 — ปิดค่า `source_system` และกติกา prune

- [x] เลือกค่า canonical ระหว่าง `ALLMAP` กับ `ALM`
- [ ] กำหนด enum/domain กลางแทน string literal กระจายหลายไฟล์
- [ ] prune ได้เฉพาะแถวที่สร้างโดย source canonical เท่านั้น
- [ ] ห้าม prune `source_system='USER'`
- [ ] test migration/ข้อมูลเก่าที่อาจมีทั้ง `ALM` และ `ALLMAP`

### P1-REPO-01 — ทำ legacy baseline ให้ตรวจสอบย้อนกลับได้

สถานะที่พบ ณ วันที่ตรวจ:

- main repository มอง `batchjob/` เป็น untracked ทั้งโฟลเดอร์
- `batchjob/fcsJar/` เป็น nested Git repository ขนาดประมาณ 413 MB
- nested repository รายงานประมาณ 301 modified/deleted entries และ 10 untracked entries
- มี Java 742 ไฟล์, JAR 59 ไฟล์ และ class files 901 ไฟล์

งานที่ต้องทำ:

- [ ] ระบุ commit/tag ที่เป็น legacy baseline สำหรับเอกสารชุดนี้
- [ ] แยก user changes ออกจากความต่างที่เกิดจาก line ending/encoding/import process
- [ ] ตัดสินใจว่าจะเก็บ `fcsJar` เป็น submodule, sanitized archive หรือ external evidence repository
- [ ] ไม่ add nested `.git`, binary build output และ secret-bearing config เข้า main repository โดยไม่ตั้งใจ
- [ ] สร้าง manifest: commit hash, branch, extraction date, checksum และรายการไฟล์ที่ตัดออก
- [ ] ระบุใน README ว่า source snapshot compile ได้หรือใช้เพื่ออ่านอ้างอิงเท่านั้น

### P1-CROSS-01 — ปิด open decisions ของทุก Job ก่อนเปลี่ยนเป็น implementation-ready

- [ ] Job 2 — W sweep, datasource owner, process status, branch type, re-import N, ALLMAP URL, DV owner
- [ ] Job 3 — parent relation, idempotency, reject policy, calendar, optional zone filtering
- [ ] Job 4 — trigger/input, durable file/outbox boundary, retry และ reconciliation
- [ ] Job 5 — checksum/outlier definitions, invalid rows, NULL diff และเกณฑ์ชดเชย
- [ ] Job 6 — input date สามความหมาย, business config, I↔N linkage และ statement period
- [ ] Job 7 — source identity, pending state, source system, prune และ dependency
- [ ] Job 8 — document number/identity, approver snapshot, readiness state และ rerun policy
- [ ] Job 8b — threshold, rows ค้าง W, zero-compensation rule, DV identity และ API retry
- [ ] Job 9 — percentage precision, allocation 100%, amount reconciliation, source owner และ dependency
- [ ] Job 10 — watchdog scope, threshold, dedup notification, NULL outbox status และ legal hold
- [ ] Job 11 — message contract, update ownership/conflict กับ Job 9, idempotency และ poison-message policy
- [ ] Job 12 — work calendar, watched workflow steps, reminder state, catch-up และ >66-day escalation

---

## P2 — ความถูกต้องและความสม่ำเสมอของเอกสาร

### P2-DOC-01 — แก้เลขหัวข้อและ cross-reference

- [x] Job 7 เปลี่ยน “เงื่อนไข 5 ชั้น” เป็น “6 ชั้น” หรือรวมเงื่อนไขให้เหลือ 5 จริง
- [x] Job 6 หัวไฟล์เปลี่ยน reference จากหัวข้อ 11 เป็นหัวข้อ 12
- [x] Job 2 เรียง test case กลุ่ม 4 จาก `4.1 ... 4.9` ตามลำดับ โดยไม่วาง `4.6` หลัง `4.9`
- [x] ตรวจ anchor links หลังแก้ชื่อหัวข้อ

### P2-DOC-02 — แก้ README และ repository guidance

- [x] แก้ `CLAUDE.md` ที่ยังระบุว่า `batchjob/` มี Job 2 เพียงฉบับเดียว
- [x] เปลี่ยนสถานะใน `batchjob/README.md` จาก “✅ เสร็จ” ให้แยกเป็น
  - [x] เอกสารเขียนครบ
  - [x] Open decision ปิดครบ
  - [x] Implementation-ready
- [x] อัปเดตวันที่ตรวจล่าสุดหลังปิด remediation จริง
- [x] เพิ่มลิงก์ checklist ฉบับนี้ใน `batchjob/README.md`

### P2-CHECKER-01 — เพิ่มกฎที่ตัวตรวจปัจจุบันยังจับไม่ได้

- [x] จับ `ON CONFLICT` ที่อ้างคอลัมน์/constraint ไม่มีใน DDL
- [ ] จับ business key nullable ที่ใช้เป็น idempotency key โดยไม่มี fallback identity
- [x] จับ canonical enum/string ที่ใช้หลายค่า เช่น `ALM` กับ `ALLMAP`
- [x] จับ schedule เดียวกันของ jobs ที่ประกาศ dependency กัน
- [ ] จับข้อความ mapping เก่าหลัง rename/split column เช่น `competitor_code`
- [ ] จับ metric equation ที่อ้าง metric ซึ่งมีความหมายขัดกับ test cases
- [x] เพิ่ม secret scanner แยกจาก `tools/check_docs.py`

---

## Test checklist หลัง remediation

### Job 2 / Job 3

- [ ] ใช้ test checklist เต็มจาก `CHECKLIST-JOB-02-JOB-03-REMEDIATION.md`
- [ ] Job 3 รันก่อน Job 2 แล้วได้ผลตาม parent policy โดยไม่เกิด FK failure แบบไม่ควบคุม
- [ ] `COMPET_ID` ว่างหลายแถว import/rerun ได้ตาม stable identity ที่เลือก
- [ ] brand map ไม่ได้ยัง reconcile ถูกต้อง

### Job 4 / Job 5

- [ ] outbox/file write failure ไม่ทิ้งสถานะว่า request สำเร็จทั้งที่ส่งไม่สำเร็จ
- [ ] Job 5 malformed rows เป็นไปตาม reject/fail policy และ metrics รวมลงตัว
- [ ] ค่า diff `NULL`, `-10`, `-9.9999`, `-0.0001`, `0` และค่าบวกได้ outcome ที่ตกลง
- [ ] การตัดสินของ Job 5 กับ Gate Job 8b ไม่ทำให้แถวค้างโดยไม่มี owner

### Job 6

- [ ] mutation ทั้ง 9 ขั้นรันในลำดับที่กำหนดและ rollback ตาม boundary
- [ ] outbox publisher ยืนยันได้โดยไม่ publish ภายใน DB transaction
- [ ] payload ฝั่ง I/N ผูกกันและกันได้ด้วย key ที่ชัดเจน
- [ ] rerun ไม่สร้างข้อความซ้ำ

### Jobs 7 / 8 / 8b / 9

- [ ] Job 8 สร้างเอกสารก่อน Job 7/9 ทุกครั้งในการรันปกติ
- [ ] Job 7 rerun ไม่เพิ่มคู่แข่งที่ source identity ว่างซ้ำ
- [ ] Job 7 prune ไม่แตะแถว USER
- [ ] Job 8b เปิด workflow ผ่าน BE API และไม่เรียก workflow package โดยตรง
- [ ] Job 9 ตรวจ SUM(percent) และ SUM(amount) ก่อน commit
- [ ] chain fail/retry ที่ทุกจุดไม่สร้าง document/workflow/child row ซ้ำ

### Jobs 10 / 11 / 12

- [ ] Job 10 เฝ้า outbox scope ที่ตกลงและเตือนซ้ำไม่เกิน policy
- [ ] Job 11 consume duplicate message แล้วไม่ update เงินซ้ำ
- [ ] Job 11 poison message ถูก retry/DLQ ตาม contract
- [ ] Job 12 วันหยุดยาวและ missed schedule ไม่ทำ reminder หลุดหรือซ้ำ
- [ ] ส่งอีเมลล้มเหลวไม่บันทึกว่าแจ้งสำเร็จ

### Security / repository

- [ ] secret scanner ผ่านทั้ง working tree และ history/snapshot ที่จะส่งมอบ
- [ ] ไม่มี nested repository หรือ binary output ถูก commit โดยไม่ตั้งใจ
- [ ] manifest ของ legacy baseline ตรวจ checksum ได้

---

## Final consistency gate

- [ ] เอกสารอธิบาย Job 2–12 ไม่มีข้อเท็จจริงที่ขัดกับ Java legacy โดยไม่ได้ติดป้าย “พฤติกรรมใหม่”
- [ ] LLDD Job 2–12 ไม่มี SQL/TypeScript skeleton ที่คัดลอกแล้ว compile/prepare ไม่ผ่าน
- [ ] DDL, LLDD-Database, database.md และ Job documents ใช้ table/column/constraint ตรงกัน
- [ ] competitor identity และ `source_system` ใช้ contract เดียวกันตลอด Job 3 → Job 7 → document
- [ ] schedule/dependency ตรงกันใน LLDD, deployment และ runbook
- [ ] metrics และ reconciliation equations ครอบคลุมทุก outcome
- [ ] Open decision ที่กระทบเงิน, eligibility, data loss หรือ workflow มีผู้อนุมัติลงชื่อ
- [x] `python3 tools/check_docs.py` ผ่านทุกกฎเดิม ณ วันที่ 2026-09-12
- [x] ไม่พบ broken local Markdown links ในเอกสารชุดที่ตรวจ
- [x] ไม่พบ merge-conflict marker ใน Markdown/Java/XML/properties ที่ตรวจ
- [ ] เพิ่มกฎ checker ใหม่ตาม P2-CHECKER-01 แล้วผ่าน
- [ ] target repository compile ผ่าน
- [ ] unit/integration tests ตาม checklist ผ่าน
- [ ] security review ผ่านก่อนแชร์หรือ commit legacy snapshot

---

## ลำดับแนะนำในการแก้

1. `P0-SEC-01` — ป้องกัน credential รั่วเพิ่มเติมและ rotate ค่าที่พบ
2. `P0-DB-01` — เลือก competitor source identity ก่อนแก้ DDL/SQL
3. `P0-J3-01` + `P0-J7-01` — แก้ mapping, metrics และ generated LLDD
4. `P0-ORCH-01` + `P0-J2J3-01` — ปิด dependency และ design decisions
5. `P1-J5-01` + `P1-J5-02` — เคาะ eligibility flow ที่กระทบสิทธิชดเชย
6. `P1-J12-01` — ออกแบบ reminder state/catch-up
7. `P1-REPO-01` — ตรึง legacy baseline และ provenance
8. P2 + checker rules → regenerate → compile/test → final review

---

## สรุปรอบแก้ 2026-09-12 — อะไรแก้แล้ว อะไรไม่แก้และทำไม

### 🔄 เปลี่ยนสถาปัตยกรรมตามคำสั่งผู้ใช้ (นอกเหนือจาก checklist)

**ตัด repo `srm-sps-spsap-store-consumer` ออกจากขอบเขต** — ลบทั้งโฟลเดอร์และไฟล์วิเคราะห์
**Job 5 / Job 11 ต้อง consume คิวเองใน `srm-sps-spsap-sop-sgi-batch`**

| ไฟล์ที่แก้ | สิ่งที่เปลี่ยน |
|---|---|
| `job-batch.html` | Job 5/11 · desc · trigger · flow · queue · DLQ |
| `tools/build_lldd_documents.py` · `lldd_skeleton_job.py` · `lldd_db_dictionary.py` | ข้อความ trigger + input contract |
| `tools/check_docs.py` | guard "consumer เป็นตัวกระตุ้น" เปลี่ยนเงื่อนไขจับ |
| `workflow.md` · `CLAUDE.md` · `.claude/skills/**` | ผังระบบ + คู่มือ |
| `DECISIONS` **2.11** | พลิกมติเดิม (2026-09-08) เป็นมติใหม่ (2026-09-12) |
| `DECISIONS` **2.12** | **ปิดเอง** — ไม่มีตัวกลางมาตัด `dataName` ทิ้งอีกแล้ว |
| `batchjob/JOB-11-*.md` | หัวข้อ 1 · 4 · 8 · 9 · 10 |

> 🔴 **ผลที่ตามมาที่ยังไม่ได้ประเมินชั่วโมง** — `SBP/srm-sps-spsap-sop-sgi-batch.md` ข้อ 4 ระบุว่า
> *"ยังไม่มีตัวอย่าง consumer ใน repo นี้ — ทุกช่องเป็น publisher อย่างเดียว"*
> **ต้องสร้าง consumer · DLQ · retry policy ใหม่ทั้งชุด**

### ✅ แก้แล้ว 28 ข้อ (แก้ที่ต้นทาง ไม่ได้แก้ไฟล์ generate)

| กลุ่ม | สรุป |
|---|---|
| **P0-J7-01** | `competitor_code` → `competitor_store_code` ทุกจุด · `ON CONFLICT` อ้างคอลัมน์จริงแล้ว · `source_system` เหลือ **`ALLMAP`** ค่าเดียว — แก้ที่ `BUSINESS_UNIQUE_KEYS` และ `job-batch.html` |
| **P0-J3-01** | ตารางฟิลด์ §5 · UNIQUE §6 · metrics §9 ตรงกับ DDL ใหม่แล้ว · `rejectedCount` → `unmappedBrandCount` + เพิ่ม `noStoreCodeCount` · สมการไม่หัก unmapped ออก (เพราะยังเก็บแถวไว้) |
| **P1-J7-01** | เลือกค่า canonical `ALLMAP` + เตือนว่าข้อมูลเก่าที่มี `ALM` ต้อง migrate ก่อน |
| **P2-DOC-01** | Job 7 "5 ชั้น" → **6 ชั้น** · Job 6 อ้างหัวข้อ 11 → **12** · Job 2 ย้าย test case `4.6` ขึ้นหลัง `4.5` |
| **P2-DOC-02** | `CLAUDE.md` (Job 2 ฉบับเดียว → 12 ฉบับ) · `README.md` แยกสถานะ **3 แกน** (เขียนครบ / ปิด decision / implementation-ready) + ลิงก์ checklist + วันที่ตรวจ |
| **P2-CHECKER-01** (2 จาก 7) | **guard #105** จับ `ON CONFLICT` ที่อ้างคอลัมน์ไม่มีใน DDL · **guard #106** จับ enum ที่เขียนหลายค่า — ทดสอบด้วยการคืนบั๊กแล้วจับได้ทั้งคู่ |

### ✅ รอบที่ 2 (2026-09-12 · ต่อจากรอบแรก) — แก้เพิ่ม 22 ข้อ

| กลุ่ม | สรุป |
|---|---|
| **P0-SEC-01** (3/6) | สร้าง **`tools/scan_secrets.py`** (ไม่พิมพ์ค่าจริง) + **`batchjob/CREDENTIAL-INVENTORY.md`** — พบ **83 จุด ใน 22 ไฟล์** รวม **AWS access key 1 ตัว** ที่ยังไม่เคยบันทึก · ✅ `fcsJar/` อยู่ใน `.gitignore` แล้ว credential จึงไม่หลุดเข้า git |
| **P0-ORCH-01** (3/7) | 🔴 **พบว่า Job 2/3 ใช้ cron เดียวกัน และ Job 7/8/9 ใช้ cron เดียวกัน** ทั้งที่ประกาศ dependency กัน → เหลื่อมเวลาแล้ว (Job 3 `07:30` · Job 7/9 `18:00`) พร้อมระบุชัดว่า **เวลาเหลื่อมไม่ใช่การรับประกัน ต้องตั้ง dependency ที่ AWS Batch** |
| **P1-J5-01** (4/8) | 🔴 **แก้ข้อเท็จจริงผิดในเอกสารผมเอง** — เขียนว่า `Y` แล้วเข้า workflow ทันที และ `NULL` "ไหลเข้า workflow" · ของจริง Gate ใช้ `<= -10` → **`Y` ที่ diff = −5 หรือ NULL จะค้าง `W` ตลอดไป** · เพิ่มตารางเทียบเกณฑ์ทุกช่วงค่า |
| **P1-J5-02** (4/6) | แยก **`invalidLineCount`** (ข้อมูลเสีย) ออกจาก **`businessRejectedCount`** (ผลธุรกิจ `N`) · แก้สมการ reconcile · ระบุให้เก็บเหตุผล + เลขบรรทัดต้นทาง |
| **P1-J12-01** (2/7) | 🔴 **ลบคำรับประกัน "เตือนพอดี 1 ครั้ง"** — เพราะนับ *วันทำการ* ไม่ใช่วันปฏิทิน · 1 สัปดาห์ปฏิทิน = ~5 วันทำการ → **ปกติจะเตือนซ้ำ** พร้อมตารางแสดงผลแต่ละกรณี |
| **P1-J3-01** (4/6) | แยก **"ตัวอย่างในเอกสารเดิม"** ออกจาก **"ค่าจริงที่วิวต้องการ"** พร้อมหลักฐานสวนทาง (ไฟล์ K2 ใช้ ค.ศ. `2017`) · ระบุ query ที่ต้องรันและหลักฐานที่ต้องเก็บ |
| **P2-CHECKER-01** (4/7) | **guard #107** จับ job ที่ขึ้นต่อกันแต่ใช้ cron เดียวกัน (จับได้จริง 3 จุด) · **`tools/scan_secrets.py`** แยกจาก `check_docs.py` |

### ⏸️ ไม่แก้ พร้อมเหตุผล

| ข้อ | เหตุผลที่ไม่แก้ |
|---|---|
| **P0-SEC-01** ที่เหลือ (rotate · sanitized snapshot) | **อยู่นอก repo** — `rotate/revoke` ต้องทำที่ระบบจริงโดยทีม infra/security · การลบข้อความในไฟล์ไม่ทำให้ credential ปลอดภัยขึ้น · ✅ **ส่วนที่ทำได้ในนี้ทำแล้ว** (บัญชีรายการ + scanner) |
| **P0-DB-01** เลือก competitor identity | **เป็นการตัดสินใจออกแบบ** — ทางเลือก A (`source_row_id`) · B (hash) · C (quarantine) ให้ผลต่างกันมาก · บันทึกปัญหา `ON CONFLICT` ไม่ match แถว `NULL` ไว้ในเอกสาร Job 3 แล้ว |
| **P0-ORCH-01** ที่เหลือ (enforce จริง · retry/backfill) | ต้องตั้งที่ **AWS Batch/EventBridge/Step Functions** ไม่ใช่แก้ในเอกสาร · ✅ **เหลื่อม cron + guard #107 ทำแล้ว** เพื่อไม่ให้เอกสารอ้างตารางเวลาที่ race |
| **P0-J2J3-01 · P1-CROSS-01** ปิด open decisions | **36 ข้อใน `DECISIONS-รอตัดสินใจ.md`** — ส่วนใหญ่กระทบเงิน/สิทธิชดเชย ต้องมีเจ้าของงานเคาะ |
| **P1-J5-01 · P1-J5-02 · P1-J12-01 · P1-J3-01** ที่เหลือ | ✅ **ส่วนที่เป็น "ข้อเท็จจริงผิด" แก้แล้วทั้งหมด** · ที่เหลือเป็นการ**เลือกกติกาธุรกิจ** — เกณฑ์ `-10` vs `0` · malformed row reject รายแถวหรือ fail ทั้งไฟล์ · reminder state/catch-up/escalation >66 วัน · ปฏิทินวันทำการ · query `PERIOD_YEAR` จริง — **ต้อง business sign-off หรือเข้าถึงฐาน/ปฏิทินที่ยังไม่มีสิทธิ์** |
| **P2-CHECKER-01** ที่เหลือ 3 กฎ | "business key nullable ที่ไม่มี fallback" ขึ้นกับ **P0-DB-01** ที่ยังไม่เคาะ · "mapping เก่าหลัง rename" กับ "metric equation ขัดกับ test" ต้องนิยาม "อะไรคือผิด" ให้ชัดก่อน ไม่งั้นจะได้ false positive เยอะกว่าของจริง |
| **P1-REPO-01** legacy baseline | ต้องเลือกว่าจะเก็บ `fcsJar` เป็น submodule / sanitized archive / external repo — **เป็นการตัดสินใจของเจ้าของ repo** · ⚠️ ข้อมูลจริง: `batchjob/` ยัง **untracked ทั้งโฟลเดอร์** ลบแล้วกู้ไม่ได้ |
| **compile / unit test / integration test** | **ยังไม่มี implementation ให้ compile** — `SBP/` เป็นอ่านอย่างเดียวตามข้อกำหนดที่ตกลงไว้ |
| **secret scanner แยกจาก check_docs** | เป็นงาน CI/pre-commit ไม่ใช่ตัวตรวจเอกสาร |

---

## บันทึกการปิดงาน

| วันที่ | Checklist ID | ผู้แก้ | ผู้ตรวจ | หลักฐาน/PR/Commit | หมายเหตุ |
|---|---|---|---|---|---|
| 2026-09-12 | สร้าง checklist จากผลตรวจรอบล่าสุด | Codex | — | ตรวจแบบ read-only ก่อนสร้างไฟล์นี้ | ยังไม่มีการแก้เอกสาร/DDL/code ตามรายการ |
| 2026-09-12 | รอบที่ 1 — P0-J7-01 · P0-J3-01 · P1-J7-01 · P2-DOC-01/02 · guard #105/#106 | Claude | — | `check_docs.py` ผ่าน 107 กฎ | + ตัด repo `store-consumer` ตามคำสั่งผู้ใช้ · แก้ 28 ข้อ |
| 2026-09-12 | รอบที่ 2 — P0-SEC-01 (บางส่วน) · P0-ORCH-01 (บางส่วน) · P1-J5-01/02 · P1-J12-01 · P1-J3-01 · guard #107 | Claude | — | `check_docs.py` ผ่าน 108 กฎ · `scan_secrets.py` ใหม่ | แก้เพิ่ม 22 ข้อ · รวม **50 ข้อ** · เหลือ 129 ข้อที่ต้องให้คนเคาะหรือทำนอก repo |

