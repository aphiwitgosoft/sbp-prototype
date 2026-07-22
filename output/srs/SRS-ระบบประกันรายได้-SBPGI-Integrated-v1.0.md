# SOFTWARE REQUIREMENT SPECIFICATION

## ระบบประกันรายได้ SBPGI

Version 1.0

> เอกสารฉบับนี้เป็น baseline แบบ self-contained สำหรับการพัฒนา ทดสอบ และตรวจรับระบบ


# 1. SRS Overview and Scope


## 1.1 Purpose

เอกสารนี้กำหนดความต้องการของระบบประกันรายได้ SBPGI แบบรวม ครอบคลุมกระบวนการนำเข้าข้อมูลผลกระทบและยอดขาย การคำนวณ การสร้างเอกสาร การพิจารณาอนุมัติ การรายงาน การส่ง Statement และการติดตามผลการทำงานของระบบ

ขอบเขตงานพัฒนาของ FE/BE อยู่ที่ระบบประกันรายได้ (SBP Mall) และบริการภายในที่ระบุในเอกสารนี้เท่านั้น รูป Flow ตารางข้อมูล และภาพหน้าจอที่อยู่ใน SRS ถือเป็นส่วนหนึ่งของคำอธิบายระบบ แต่ไม่เพิ่มขอบเขตนอกเหนือจาก requirement ที่ระบุ

> หมายเหตุเวอร์ชัน: เอกสาร v1.0 เป็น baseline เริ่มต้นสำหรับการพัฒนาและตรวจรับระบบประกันรายได้ SBPGI


## 1.2 Requirement classification

| Tag | ความหมาย | การใช้งาน |
| --- | --- | --- |
| REQ | ข้อกำหนดของระบบที่ได้รับอนุมัติใน SRS ฉบับนี้ | ต้องพัฒนาและทดสอบตามข้อความที่กำหนด |
| SYS | ข้อกำหนดร่วมด้านสถาปัตยกรรม ข้อมูล ความปลอดภัย และการปฏิบัติการ | ใช้กับองค์ประกอบที่เกี่ยวข้องทั้งหมด |
| PROTO | พฤติกรรมหรือข้อมูลตัวอย่างใน prototype | ใช้ยืนยัน UX ไม่ใช่ข้อมูล Production |
| OPEN | ประเด็นขัดแย้งหรือยังไม่ตัดสินใจ | ห้ามถือเป็นข้อยุติจนกว่าจะมีผู้อนุมัติ |


## 1.3 Baseline and change control

- SRS v1.0 ฉบับนี้เป็น baseline เดียวสำหรับกำหนดขอบเขต พัฒนา ทดสอบ และตรวจรับระบบ
- ข้อความ ตาราง รูป และ acceptance criteria ภายใน SRS มีผลร่วมกัน หากมีความขัดแย้งให้เปิดประเด็นตัดสินใจก่อนพัฒนา
- รายละเอียดเชิงออกแบบต้องไม่เพิ่ม ลด หรือเปลี่ยน requirement โดยไม่มีการอนุมัติ change request
- รายการที่ระบุ OPEN ยังไม่ถือเป็นขอบเขตที่อนุมัติจนกว่าจะมีข้อยุติและปรับ baseline
- ข้อมูลตัวอย่างและพฤติกรรม prototype ใช้ยืนยัน UX เท่านั้น ต้องไม่ถูกนำไปใช้เป็นข้อมูล Production
- ขอบเขต API ใน SRS ประกอบด้วย 62 endpoints / 10 กลุ่ม โดยบริการยืนยันตัวตนเป็นบริการ platform กลาง

## 1.4 How to read this document

เอกสารจัดลำดับจากภาพรวมธุรกิจไปสู่ข้อกำหนดที่ใช้พัฒนาและตรวจรับ เพื่อให้ Business, FE, BE, QA และ Operations ใช้ baseline เดียวกันได้โดยไม่ต้องตีความรายละเอียดเชิงออกแบบเป็น requirement เพิ่มเติม

| ผู้อ่าน | หัวข้อที่ควรเริ่ม | สิ่งที่ต้องใช้จากเอกสาร |
| --- | --- | --- |
| Business / Product Owner | 1, 2, 3.1, 5 และ 6 | ยืนยันขอบเขต กฎธุรกิจ เกณฑ์ตรวจรับ และประเด็นที่ต้องตัดสินใจ |
| Frontend / UX | 3.4, 3.5 และ 4 | หน้าจอ ข้อมูลที่แสดง การกระทำ ข้อความตอบกลับ สิทธิ์ และพฤติกรรม responsive |
| Backend / Integration | 3.1, 3.2, 3.3, 3.5 และ 4 | workflow, data controls, batch, interface capability, audit และ reliability |
| QA / UAT | 3, 4 และ 5 | เงื่อนไขก่อนทดสอบ ผลลัพธ์ที่คาดหวัง กฎยอมรับ และ traceability |
| Operations | 2.4, 3.3, 4 และ 6 | schedule, monitoring, rerun/reconcile, availability และ open decision |

> หลักการตีความ: ข้อความที่ระบุว่า ‘ระบบต้อง’ หรืออยู่ภายใต้ REQ/SYS/acceptance ถือเป็นข้อกำหนดที่ต้องทดสอบได้ ส่วน OPEN ต้องได้รับอนุมัติก่อนนำไปพัฒนา


## 1.5 Assumptions, Constraints and Sign-off

| ID | Type | Statement | Validation / approval gate |
| --- | --- | --- | --- |
| ASM-001 | Assumption | Platform SSO/AD/LDAP ยืนยัน credential และส่ง employee identity ที่เชื่อถือได้ให้ SBPGI; SBPGI ไม่เก็บ password hash | ผ่าน integration/security test กับ platform identity |
| ASM-002 | Assumption | QSSI, ALLMAP, IAS/MIS, STA, SAP และ SMTP ให้บริการตาม interface window และ data contract ที่อนุมัติ | ผ่าน connectivity และ golden-file test ก่อน UAT |
| ASM-003 | Assumption | ข้อมูลสาขามี region/branch type/nิติบุคคล/DV ที่เพียงพอสำหรับ candidate selection และ Gen Flow Gate | รายงาน reject/missing master ต้องเป็นศูนย์หรือได้รับ waiver |
| CON-001 | Constraint | Store code เป็นข้อความ 5 หลักและต้องรักษาเลขศูนย์นำหน้าใน DB, API, file และ UI | contract/golden-file test |
| CON-002 | Constraint | ระบบใช้ workflow 5 ขั้น 06/08/01/02/03 และสถานะเอกสาร 6 ค่า 06/08/01/02/03/99 | lookup/transition test |
| CON-003 | Constraint | Secret, password, private key, token และ connection credential ต้องอยู่นอก source/config ธรรมดาและส่งผ่าน TLS | secret scan และ deployment evidence |
| CON-004 | Constraint | ข้อความ error ภาษาไทยและผลพิจารณาที่กำหนดเป็น verbatim ต้องไม่ถูกเปลี่ยนโดย FE | contract/UI test |

| Sign-off role | Approval scope | Required before |
| --- | --- | --- |
| Business Owner / Product Owner | ขอบเขต กฎรัศมี กฎยอดขาย/เงินชดเชย และ OPEN decisions | Development baseline / UAT |
| Solution / Data Architect | API, data ownership, migration, transaction และ integration | Schema/API freeze |
| Security | Identity, RBAC, secret management, TLS, attachment และ audit | Production readiness |
| QA / UAT | Requirement coverage, acceptance evidence และ regression | Release approval |
| Operations | Batch schedule, monitoring, rerun/reconcile, backup/restore และ runbook | Go-live |


---


# 2. System Overview


## 2.1 Product perspective

ระบบประกันรายได้ใช้บริหารการชดเชยรายได้ของร้าน Store Partner ที่ได้รับผลกระทบจากร้านเปิดใหม่ โดยรับข้อมูลผลกระทบ ยอดขาย และคะแนน QSSI ประมวลผลเงื่อนไข สร้างเอกสาร เดิน workflow อนุมัติ และส่งผลชดเชยไปยังระบบบัญชี/Statement


## 2.2 Target architecture

| Layer | องค์ประกอบ | หน้าที่ |
| --- | --- | --- |
| Frontend | Web SPA จากต้นแบบหน้าจอ | Dashboard, K2 forms, report, batch monitor และ administration |
| Backend | RBAC, Document, Workflow, Batch Scheduler, Interface, Report/Notification | ให้บริการ REST API /api/v1 และ orchestration ภายใน; Auth token/menu มาจาก platform กลาง |
| Database | Schema รวม Zone A/B/C | เก็บ pipeline, เอกสาร/workflow, master/config และ audit |
| External | QSSI, ALLMAP, IAS/MIS, STA, SAP, SMTP | คง file/SFTP/API ตามขอบเขตระบบภายนอก |

> SYS: ระบบต้องรวมการสร้างเอกสารและ workflow ไว้ภายใน SBPGI โดยใช้ DB transaction และ Workflow Engine ภายใน ห้ามสร้างไฟล์ BPM06001O/BPM06002O/BPM06003O หรือเรียก K2 StartInstance ใน runtime ใหม่


## 2.3 User roles

| Role code | Role | ขอบเขต |
| --- | --- | --- |
| 00 | Default | ผู้ดำเนินการในแบบฟอร์ม |
| 01 | Admin | เห็นทุกเมนูและจัดการข้อมูลทั้งหมด |
| 02 | HQ | HQ Support และงานบริหารข้อมูล |
| 03 | User Admin | ผู้ดูแลระบบระดับผู้ใช้งาน |
| 04 | Report Admin | รายงานและรายงานสรุป |
| 05 | Assign Job | แจกงานข้อมูลผิดปกติ |
| 06 | Report Admin Special | เรียกดูเอกสารทั้งหมด |
| 10 | UserViewer | อ่านเอกสารตามรายการที่ได้รับสิทธิ์ |

> Role code ในหัวข้อนี้เป็นรหัสกลุ่มสิทธิ์การใช้งานของ RBAC เท่านั้น; ห้ามนำไปตีความเป็นรหัสหน่วยงาน/ขั้นตอนการพิจารณา หน้า Document Detail ต้องประเมินสิทธิ์การมองเห็น แก้ไข และดำเนินการจาก role, section และ task owner ปัจจุบัน


## 2.4 External interfaces

| System | Direction | Mechanism | Requirement |
| --- | --- | --- | --- |
| QSSI | Inbound | SFTP, mrs* 4 files | WINDOWS-874; คะแนน 6 หมวด 8,9,12,1,10,16 |
| ALLMAP | Inbound | SQL Server views / link | คู่ร้านถูกกระทบ ร้านคู่แข่ง และ POI map |
| IAS/MIS | Outbound/Inbound | AMS06001O / AMS06001I | ยอดขาย 4 windows x 15 days |
| STA | Outbound/Inbound | FRBC0001 + ACK/API callback | ส่งผลชดเชยและเฝ้าระวัง ACK |
| SAP | Downstream via STA | Accounting posting | รับรายการเมื่อ STA approve |
| SMTP | Outbound | E-mail | แจ้งผู้ดำเนินการ เตือนงานค้าง และ batch errors |


## 2.5 Business outcomes and scope boundary

ผลลัพธ์ปลายทางของระบบคือการเปลี่ยนข้อมูลผลกระทบและยอดขายให้เป็นเอกสารชดเชยที่อนุมัติ ตรวจสอบย้อนหลัง และส่งต่อบัญชีได้ครบถ้วน โดยไม่เพิ่มหน้าจอหรือระบบย่อยนอกขอบเขตที่ระบุใน SRS

| ประเภท | อยู่ในขอบเขต | อยู่นอกขอบเขต |
| --- | --- | --- |
| Business process | นำเข้าข้อมูล คำนวณ สร้างเอกสาร พิจารณา อนุมัติ รายงาน และส่ง Statement | การเปลี่ยนกฎของ QSSI, ALLMAP, IAS/MIS, STA หรือ SAP ภายนอกระบบ |
| Application | หน้าจอ SBP Mall, API, Document/Workflow Service, Batch Scheduler, Notification และ audit | การพัฒนาระบบ workflow/integration เดิม, Login/SSO platform กลาง และเครื่องมือออกแบบระบบ |
| Data | ข้อมูลประมวลผล เอกสาร workflow master/config interface tracking และไฟล์แนบ | การเปลี่ยน ownership หรือโครงสร้างข้อมูลต้นทางของระบบภายนอก |
| Delivery evidence | ผลทดสอบตาม acceptance, interface golden file, audit trail และ run/reconcile evidence | prototype data และภาพหน้าจอเป็นข้อมูล production |


---


# 3. Specific Requirements

หัวข้อนี้เป็นข้อกำหนดที่ใช้ส่งต่อให้ทีมพัฒนาและ QA โดยเรียงตามลำดับการทำงานจริง: flow, data, batch, screen และ API ทุกส่วนต้องอ่านร่วมกับ Non-Functional Requirements และ Acceptance/Traceability ไม่ควรตรวจรับจากภาพหน้าจอเพียงอย่างเดียว


## 3.0 Atomic Requirement Register

| Requirement ID | Atomic shall statement | Verification |
| --- | --- | --- |
| REQ-BUS-001 | ระบบต้องคัดร้านเปิดใหม่ในกรุงเทพฯ/ปริมณฑลที่อยู่ห่างร้านถูกกระทบไม่เกิน 1 กิโลเมตร | candidate selection boundary test ที่ 0.999/1.000/1.001 กม. |
| REQ-BUS-002 | ระบบต้องคัดร้านเปิดใหม่ในต่างจังหวัดที่อยู่ห่างร้านถูกกระทบไม่เกิน 2 กิโลเมตร | candidate selection boundary test ที่ 1.999/2.000/2.001 กม. |
| REQ-BUS-003 | ระบบต้องเปิด workflow เฉพาะรายการที่ Gen Flow Gate ทุกเงื่อนไขผ่าน | Job 8b/API gate test ครบ Y/W/N |
| REQ-BUS-004 | ระบบต้อง flag รายการที่ยอดขายมีวันทำการน้อยกว่า 60 วันและแสดงเป็นแถวผิดปกติ | list/report test ที่ 59/60 วัน |
| REQ-BUS-005 | ระบบต้องปฏิเสธการบันทึกเมื่อผลรวมเปอร์เซ็นต์ชดเชยของร้านเปิดใหม่ไม่เท่ากับ 100% | validation test ต่ำกว่า/เท่ากับ/มากกว่า 100 |
| REQ-BUS-006 | ยอดชดเชยไม่เกิน 100,000 บาทต้องสิ้นสุดที่ Section 02; ยอดเกิน 100,000 บาทต้องผ่าน Section 03 ก่อนสิ้นสุด | routing boundary test 99,999.99/100,000/100,000.01 |
| REQ-DOC-001 | ระบบต้องสร้างเลขเอกสารรูป YYYY/xxxxx โดยใช้ปี พ.ศ. และ running แยกต่อปี | uniqueness/format/concurrency test |
| REQ-DOC-002 | ระบบต้องป้องกันเอกสารซ้ำต่อ business key และ impact process | duplicate/idempotency test |
| REQ-DOC-003 | ระบบต้องเก็บความสัมพันธ์ impact_process_id -> doc_no -> instance_id -> task_id ให้ trace ได้ | referential-integrity trace |
| REQ-WFL-001 | ระบบต้องอนุญาต action เฉพาะ current task owner ที่ผ่าน RBAC และ record access | authorization test 401/403/409 |
| REQ-WFL-002 | ระบบต้องบันทึกผลพิจารณา เหตุผล ผู้กระทำ เวลา สถานะก่อน/หลัง และ correlation id ของทุก transition | audit trace sample |
| REQ-WFL-003 | ระบบต้องใช้ optimistic concurrency และคืน STALE_VERSION เมื่อ version เอกสารถูกเปลี่ยนแล้ว | parallel update test |
| REQ-INT-001 | Job 4 ต้องสร้าง durable file สำเร็จก่อน commit W เป็น P และ outbox READY | failure injection ก่อน/หลัง fsync |
| REQ-INT-002 | Interface callback ต้องอัปเดต tracking เดิมแบบ compare-and-set และงาน purge ต้องลบเฉพาะ terminal/expired/non-held | ACK race และ retention test |
| REQ-INT-003 | ระบบต้องใช้ typed FK สำหรับ interface transaction และรักษา business key/idempotency key | schema constraint/rerun test |
| REQ-SEC-001 | ระบบต้องไม่เก็บ password hash หรือ credential ของ platform identity ภายใน user account ของ SBPGI | schema/secret scan |
| REQ-SEC-002 | การเชื่อมต่อภายนอกต้องอ่าน secret จาก Secret Manager และบังคับ TLS/host verification | deployment/security evidence |
| REQ-FIL-001 | ไฟล์แนบต้องไม่เกิน 5 MB ผ่าน type/AV scan และดาวน์โหลดได้เฉพาะผู้มีสิทธิ์เมื่อสถานะ CLEAN | upload/download security test |
| REQ-RPT-001 | รายงานหน้าจอและ CSV ต้องใช้ filter/dataset เดียวกันและมีข้อมูลครบ 19 คอลัมน์ | preview/export reconciliation |
| REQ-OPS-001 | Jobs 1-10 และ 8b ต้องรองรับ rerun โดยไม่สร้างข้อมูลซ้ำและต้องรายงาน input/success/reject/skipped | rerun/reconcile evidence |
| REQ-SCR-001 | ระบบต้องมีหน้าจอ committed SCR-01 ถึง SCR-04 และ SCR-06 ถึง SCR-11 ตาม requirement รายหน้าจอ | screen/UAT traceability |
| SYS-API-001 | ระบบต้องมี API capability 62 endpoints ใน 10 กลุ่มตาม catalog | OpenAPI/contract coverage |
| SYS-DAT-001 | ระบบต้องมี logical data model 34 ตารางพร้อม PK/FK/constraint ที่บังคับกฎสำคัญ | migration/schema test |
| SYS-NFR-001 | ระบบต้องมี correlation log, metrics, alert และ audit ที่เชื่อม request/job/interface กับผลธุรกิจได้ | observability trace |


## 3.1 Business Flow and System Diagrams

> รูป Flow ในหัวข้อนี้เป็นส่วนหนึ่งของ SRS ใช้อธิบายลำดับการทำงานและเงื่อนไขทางธุรกิจ แต่ไม่ใช่หน้าจอผู้ใช้งานที่ต้องพัฒนา

![รูปที่ 1: Flow FGI/FCS - Batch Pipeline - ส่วนที่ 1/2](flow-fgi-01.png)

![รูปที่ 2: Flow FGI/FCS - Batch Pipeline - ส่วนที่ 2/2](flow-fgi-02.png)

![รูปที่ 3: Flow การพิจารณาและอนุมัติ - ส่วนที่ 1/3](k2-flow-01.png)

![รูปที่ 4: Flow การพิจารณาและอนุมัติ - ส่วนที่ 2/3](k2-flow-02.png)

![รูปที่ 5: Flow การพิจารณาและอนุมัติ - ส่วนที่ 3/3](k2-flow-03.png)

![รูปที่ 6: Flow ระบบเป้าหมายแบบรวม - ส่วนที่ 1/3](plan-flow-01.png)

![รูปที่ 7: Flow ระบบเป้าหมายแบบรวม - ส่วนที่ 2/3](plan-flow-02.png)

![รูปที่ 8: Flow ระบบเป้าหมายแบบรวม - ส่วนที่ 3/3](plan-flow-03.png)


---


### 3.1.1 End-to-end flow

| Step | Process | Requirement |
| --- | --- | --- |
| A1 | นำเข้าคะแนน QSSI รายเดือน | Job 1 รับ 4 ไฟล์ผ่าน SFTP, dedup และบันทึก fcs_qssi_scores |
| A2 | นำเข้าคู่ร้านและคู่แข่ง | Jobs 2-3 อ่าน ALLMAP ทุกวันที่ 7 และตั้ง verify_status ตามกฎ DENY/ON_PROCESS |
| A3 | ขอยอดขายรายวัน | Job 4 สร้าง AMS06001O วันที่ 7-16 เวลา 16:00 |
| A4 | รับยอดขายและคำนวณ | Job 5 รับ AMS06001I, คำนวณ 4x15 วัน, outlier \|sales_diff\| >= 50 |
| B1 | สร้างเอกสารอัตโนมัติ | Document Service สร้าง compensation_documents และรายการลูกโดยตรงใน DB |
| B2 | เปิด workflow | Workflow Engine เปิด instance เมื่อผ่าน Gen Flow Gate และเริ่ม Section 06 |
| C1 | SBP DSA ตรวจสอบ | Section 06 และ 08 ตรวจข้อมูลและคำนวณเงินชดเชย |
| C2 | ฝ่ายส่งเสริมธุรกิจปรับข้อมูล | Section 01 แก้ร้านเปิดใหม่ คู่แข่ง ปัจจัย และตรวจ % ชดเชยรวม 100% |
| C3 | GM/AVP อนุมัติ | Section 02; ยอด > 100,000 ผ่าน Section 03 แล้วจบ, ยอด <= 100,000 จบที่ GM |
| C4 | บัญชีตรวจสอบนอก workflow | เมื่อเอกสารเสร็จสิ้น ทีมบัญชีใช้รายงาน SBP Mall และ Export CSV to Batch เพื่อกระทบ SAP |
| D1 | ส่ง Statement | Job 6 ส่ง FRBC0001 ไป STA เวลา 17:00 ทุกวัน |
| D2 | ติดตาม ACK | STA callback อัปเดต ACK และ Job 10 เป็น safety net เมื่อค้าง >= 1 วัน |


### 3.1.2 Gen Flow Gate

- คู่ร้านต้องผ่านกฎรัศมี: กรุงเทพฯ/ปริมณฑลไม่เกิน 1 กิโลเมตร และต่างจังหวัดไม่เกิน 2 กิโลเมตร
- workflow_generation_status ต้องเป็น W
- branch_type อยู่ใน FAM, FB1, FC1, FB2, FVB, FVC
- opt_dv_user_id ต้องไม่ว่าง
- นิติบุคคลของร้านเปิดใหม่ต้องต่างจากร้านถูกกระทบ
- growth_rate_diff ต้องน้อยกว่าหรือเท่ากับ -10
- sales_status ต้องเป็น Y หรือ N
- กรณี branch type ไม่เข้าเกณฑ์ให้สถานะ N; กรณีอื่นที่ยังไม่พร้อมให้คง W เพื่อแก้ไขและรันซ้ำ

### 3.1.3 Document action requirements

| Requirement | รายละเอียด |
| --- | --- |
| Action ownership | ผู้ใช้ส่งผลพิจารณาได้เฉพาะเอกสาร/งานที่ตนมีสิทธิ์ดำเนินการตาม RBAC และ task ownership |
| Result options | ระบบต้องแสดงชุดผลพิจารณาที่อนุญาตสำหรับผู้ใช้จาก API/role profile ไม่ให้ FE คำนวณสิทธิ์เอง |
| Status convention | API mutation/action ต้องคืน statusCode เป็นค่ากลาง และ FE resolve label ไทยจาก document_statuses |
| Amount approval rule | ยอดเงินชดเชยรวม 100,000 บาทเป็น threshold ทางธุรกิจสำหรับชั้นอนุมัติตามลำดับที่กำหนดใน 3.1.3 |
| Audit | ทุก action ต้องบันทึกผลพิจารณา ความคิดเห็น สถานะก่อน/หลัง ผู้กระทำ เวลา และ correlation id |
| Notification | เมื่อ action สำเร็จ ระบบต้องแจ้งผู้เกี่ยวข้องตาม e-mail rule/template ที่กำหนด |

> ลำดับ workflow ที่ต้องรองรับคือ Section 06 -> 08 -> 01 -> 02; ยอดรวมไม่เกิน 100,000 บาทสิ้นสุดที่ Section 02 ส่วนยอดเกิน 100,000 บาทต้องส่งต่อ Section 03 ก่อนสิ้นสุด ระบบต้องคืน action ที่อนุญาตตาม role, section และ task owner ปัจจุบัน


---


### 3.1.4 Migration map

| Connection | Legacy | Target |
| --- | --- | --- |
| ส่งข้อมูลชดเชย/ร้านใหม่/คู่แข่ง เข้าระบบเอกสาร | ไฟล์ BPM06001O (48 ฟิลด์) / BPM06002O / BPM06003O ผ่าน SFTP ไป BPM (Jobs 7, 8, 9) | Document Service เขียน DB ตรง (compensation_documents / document_new_stores / document_competitors) - ตัดไฟล์และ SFTP ภายในทิ้ง |
| เปิด Workflow | Job 8b ยิง K2 REST StartInstance (HTTP + Basic Auth hardcoded - ความเสี่ยง P0) | Workflow Engine ภายใน · POST /workflows/instances · Gen Flow Gate W/Y/N คงเกณฑ์เดิมทุกข้อ |
| รับ ACK ผลประมวลจาก STA | รอ STA อัปเดต return_code ใน tracking · Job 10 ตรวจทุกเช้า | เพิ่ม POST /interfaces/sta/ack (API key) · Job 10 คงไว้เป็น safety net |
| ตาราง tracking interface | FGI_CONFIRM_RECEIVE_DATA - transaction_key เป็น polymorphic FK + บั๊ก purge (E20) | interface_transactions - typed FK ต่อประเภทข้อมูล + งาน purge ทำงานจริง |
| อีเมลแจ้งเตือน | แต่ละ job ต่อ SMTP เอง · encoding TIS-620 · ผู้รับ hardcoded บางจุด (template 34) | Notification Service กลาง · UTF-8 · ผู้รับตาม status_email_rules + config ต่อ job |
| Interface ภายนอก QSSI / ALLMAP / IAS / STA | SFTP + ไฟล์ตาม encoding เฉพาะ (WINDOWS-874 / UTF-8 / พ.ศ.) | คงเดิม (ระบบของทีมอื่น) - ย้าย credential ไป Secret Manager + บังคับ known_hosts |
| สิทธิ์ผู้ใช้และเมนู | ตารางสิทธิ์ 8 role ในระบบ BPM เดิม | Auth & RBAC + JWT · menu_permissions ต่อ role · จัดการผ่านหน้าสิทธิ์การเข้าถึงเมนู |


### 3.1.5 Flow controls

- กฎ candidate selection ต้องใช้รัศมีไม่เกิน 1 กิโลเมตรสำหรับกรุงเทพฯ/ปริมณฑล และไม่เกิน 2 กิโลเมตรสำหรับต่างจังหวัด โดยรวมค่าขอบเขตเท่ากับเกณฑ์
- รายการที่ข้อมูลยอดขายไม่ครบ 60 วันต้องแสดงเป็นข้อมูลผิดปกติและแถวสีแดง
- ระบบต้องกันเปิดงาน/เอกสารซ้ำต่อ impact process/document
- บัญชีตรวจสอบยอดผ่านรายงาน SBP Mall และ Export CSV to Batch นอก workflow
- งานเตือนรายสัปดาห์ทำงานวันจันทร์ 10:00 และ escalation งานค้าง 30/45/60 วันต้องอ่านค่าจาก config
- การเปลี่ยนกฎธุรกิจ เช่น -10, 50, 60 วัน และ 100,000 บาท ต้องผ่าน Business sign-off
- ทุก action ต้องบันทึก consideration_logs, ผู้กระทำ, เวลา, สถานะก่อน/หลัง และ correlation id
![รูปที่ 9: Approve Flow เดิม ใช้ประกอบการเทียบพฤติกรรม](Flow ประกันรายได้.png)


---


## 3.2 Data Requirements and Logical Data Model

> หัวข้อนี้กำหนดข้อมูลที่ระบบต้องเก็บ ตรวจสอบ และเชื่อมโยงเพื่อรองรับธุรกรรมและการตรวจสอบย้อนหลัง ชื่อทางกายภาพของตาราง/คอลัมน์สามารถกำหนดในขั้นตอนออกแบบได้ แต่ต้องรักษาความสัมพันธ์และข้อควบคุมใน SRS


### 3.2.1 Data subjects

| Data subject | Requirement |
| --- | --- |
| Impact processing | ระบบต้องเก็บคู่ร้านถูกกระทบ/ร้านเปิดใหม่ งวดผลกระทบ ผล QSSI ยอดขาย และสถานะการสร้าง workflow ให้ตรวจสอบย้อนกลับได้ |
| Compensation document | ระบบต้องเก็บหัวเอกสาร เลขเอกสาร ร้านเปิดใหม่ คู่แข่ง ปัจจัยภายนอก เงินชดเชย ไฟล์แนบ และประวัติการพิจารณา |
| Workflow | ระบบต้องเก็บ instance/task/current section/status/assignee เพื่อควบคุมงานค้างและ audit ทุก transition |
| Master/config | ระบบต้องเก็บ role/menu/permission, ผู้ปฏิบัติงาน, external factors, email rules/templates และ system config ที่ใช้ร่วมกัน |
| Interface tracking | ระบบต้องเก็บสถานะไฟล์/callback/batch run เพื่อ reconcile งานภายนอกและ rerun ได้โดยไม่สร้างข้อมูลซ้ำ |


### 3.2.2 Data controls

- Store code ต้องเก็บเป็น varchar(5) เพื่อรักษา leading zero
- doc_no ต้อง unique และรูปแบบ YYYY/xxxxx; running แยกต่อปี
- ข้อมูลหนึ่งเอกสารต้อง trace ได้ครบจาก impact process ไปยัง document, workflow instance และ task ปัจจุบัน
- % ชดเชยของร้านเปิดใหม่ต่อเอกสารต้องรวมเท่ากับ 100%
- สถานะเอกสาร, section, role และ workflow task ต้องอ้าง lookup กลางเพื่อไม่ให้ label/code ปนกัน
- ค่าธุรกิจที่ถูก lock ต้องแก้ผ่าน UI/API ไม่ได้หากไม่มี Business sign-off
- ระบบต้องรองรับ concurrency control เมื่อมีการแก้เอกสาร/workflow พร้อมกัน
- ทุก master mutation ต้องบันทึก audit_logs ค่าเดิม ค่าใหม่ เหตุผล ผู้แก้ และเวลา
- Timestamp ภายใน DB ใช้ UTC; UI แสดง Asia/Bangkok และปี พ.ศ. ตามข้อยุติด้าน format

### 3.2.3 Logical data relationships

| Data area | Key relationship | Requirement |
| --- | --- | --- |
| Impact processing | impact_process_id เชื่อมร้านถูกกระทบ ร้านเปิดใหม่ คะแนน และยอดขาย | หนึ่งรอบประมวลผลต้องตรวจสอบข้อมูลนำเข้า สถานะ และผลการคำนวณย้อนหลังได้ |
| Compensation document | doc_no เชื่อมหัวเอกสาร ร้านเปิดใหม่ คู่แข่ง ปัจจัย ไฟล์แนบ และยอดชดเชย | doc_no ต้อง unique และข้อมูลลูกทุกประเภทต้องไม่หลุดจากหัวเอกสาร |
| Workflow | instance_id และ task_id เชื่อมเอกสาร ขั้นตอน ผู้รับผิดชอบ และประวัติ action | ต้องทราบ current task และทุก transition ของเอกสารได้ตลอดเวลา |
| Master/config | role, menu, section, operator, factor, template และ config key | ค่ากลางต้องมี version/status และ audit เมื่อเปลี่ยนแปลง |
| Interface tracking | run_id, transaction id และ correlation id | ต้องเชื่อมไฟล์ callback batch run และผลลัพธ์ธุรกิจเพื่อ reconcile/rerun ได้ |


### 3.2.4 Required remediation

| Priority | Issue | Target requirement |
| --- | --- | --- |
| P0 | Job 4 transaction | ใช้ transaction/outbox ไม่ให้ W->P commit ก่อนสร้างไฟล์สำเร็จ |
| P0 | Secrets/TLS | ย้าย credential ไป Secret Manager และบังคับ TLS |
| P0 | Tracking purge | แก้ SQL purge data_name และทำ migration/test |
| P1 | Polymorphic FK | ใช้ typed FK ใน interface_transactions |
| P1 | NULL growth rate | ส่งรอตรวจสอบแทน auto-accept; ต้องมี Business sign-off |
| P1 | Master joins | รายงาน reject/reconcile แทนการทำแถวหายเงียบ |
| P1 | Golden files | ทดสอบ encoding วันที่ พ.ศ. delimiter และ field count ทุก interface |


## 3.3 Batch Job Requirements

> SRS ส่วนนี้อธิบายงาน Batch Job ในระดับที่ผู้ใช้ธุรกิจและผู้ดูแลระบบต้องเข้าใจ: แต่ละ job ทำเพื่ออะไร รับข้อมูลหรือเงื่อนไขอะไร ระบบทำอะไรโดยสรุป และผลลัพธ์ที่ต้องเห็นคืออะไร ไม่ลงรายละเอียด coding, SQL, class/script หรือ transaction ภายใน


### 3.3.1 Batch console

![รูปที่ 10: Batch Job Console - 11 jobs - ส่วนที่ 1/3](job-batch-01.png)

![รูปที่ 11: Batch Job Console - 11 jobs - ส่วนที่ 2/3](job-batch-02.png)

![รูปที่ 12: Batch Job Console - 11 jobs - ส่วนที่ 3/3](job-batch-03.png)

หน้า Batch Job Console สำหรับ Admin แสดง pipeline A-E, รายการ 11 entry points, สถานะรอบล่าสุด/ถัดไป, เปิดปิดงาน, พารามิเตอร์ที่อนุญาตให้แก้, manual run, ลำดับงาน และ run history

| Job | Name | Thai name | Phase | Schedule | Output |
| --- | --- | --- | --- | --- | --- |
| 1 | ImportQSSI | นำเข้าคะแนน QSSI รายเดือน | A | Monthly (รายเดือน (ต้นเดือน)) | fcs_qssi_scores |
| 2 | ImportImpactStore | นำเข้าคู่ร้านถูกกระทบจาก ALLMAP | A | 0 07 7 * * (ทุกวันที่ 7 เวลา 07:00) | fgi_impact_stores |
| 3 | ImportImpactCompetitor | นำเข้าร้านคู่แข่งจาก ALLMAP | A | 0 07 7 * * (ทุกวันที่ 7 เวลา 07:00) | fgi_impact_competitors |
| 4 | PrepareImpactStoreToIAS | เตรียมและส่งคำขอยอดขายไป IAS | B | 0 16 7-16 * * (วันที่ 7-16 เวลา 16:00) | AMS06001O (UTF-8) |
| 5 | ImportImpactSaleFromIAS | รับยอดขายจาก IAS + คำนวณ Growth | B | 30 16 7-16 * * (วันที่ 7-16 เวลา 16:30) | AMS06001I (รับเข้า) |
| 6 | ExportImpactStoreToFS | ซิงก์สถานะ + ส่งค่าชดเชยไป STA | D | 0 17 * * * (ทุกวัน 17:00) | FRBC0001 (windows-874) |
| 7 | SyncCompetitorToDocument | บันทึกข้อมูลคู่แข่งเข้าเอกสาร | B | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | document_competitors (DB) |
| 8 | CreateCompensationDocument | สร้างเอกสารประกันรายได้อัตโนมัติ | B | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | compensation_documents (DB) |
| 8b | StartInternalWorkflow | เปิด Workflow ภายใน | B | after-job-8 (trigger หลัง Job 8 สร้างเอกสารสำเร็จ; manual rerun ได้ตาม period) | workflow_instances / workflow_tasks (DB) |
| 9 | SyncNewStoreToDocument | บันทึกร้านเปิดใหม่เข้าเอกสาร | B | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | document_new_stores (DB) |
| 10 | NotifyNoReceiveData | Watchdog เฝ้าระวัง ACK ค้าง | E | 0 07 * * * (ทุกวัน 07:00) | อีเมลเตือน UTF-8 + pending ACK dashboard |


### 3.3.2 Common controls

- สิทธิ์จัดการ Batch Job เป็น Admin 01 เท่านั้น
- Manual run ต้องระบุงวดข้อมูลและสร้าง run_id; API ตอบ 202 Accepted
- ห้ามรัน job เดียวกันซ้อน และต้องป้องกัน shared temp resource ของ Job 1
- แก้ไขได้เฉพาะ parameter ที่ระบุ editable; business constants ต้องถูก lock
- ทุกการเปิด/ปิด แก้ parameter และ manual run ต้องบันทึก audit
- run history ต้องเก็บ start/end, status, row count, file, error, correlation id และผู้สั่งรัน
- การ re-run ต้องปฏิบัติตาม runbook ของแต่ละ job โดยตรวจ DB, tracking, backup และปลายทางก่อน

### 3.3.3 Job business requirement catalog


#### 3.3.3.1 Job 1 - นำเข้าคะแนน QSSI รายเดือน

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | นำเข้าคะแนน QSSI รายเดือนเพื่อใช้ประกอบการคำนวณและตรวจเงื่อนไขการชดเชย |
| รับข้อมูล/เงื่อนไข | ไฟล์คะแนน QSSI รายเดือน 4 ชุดจาก SFTP, งวดเดือนที่ต้องประมวลผล, และหมวดคะแนนที่ระบบกำหนด |
| ระบบทำอะไรโดยสรุป | ระบบอ่านไฟล์ ตรวจรูปแบบและงวดข้อมูล คัดรายการล่าสุดต่อร้าน/หมวดคะแนน แล้วปรับปรุงคะแนน QSSI ของงวดนั้นให้เป็นชุดล่าสุด |
| ผลลัพธ์ที่ต้องได้ | คะแนน QSSI ของร้านถูกบันทึกพร้อมใช้งานสำหรับงานส่ง Statement และรายงานผลการประมวลผลแสดงจำนวนไฟล์/จำนวนรายการ/สถานะสำเร็จหรือผิดพลาด |
| ผู้ใช้ติดตามได้จาก | Admin ติดตามได้จาก Batch Job Console และประวัติการรัน; ผู้ใช้ธุรกิจเห็นผลผ่านข้อมูลประกอบเอกสาร/รายงาน |


#### 3.3.3.2 Job 2 - นำเข้าคู่ร้านถูกกระทบจาก ALLMAP

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | นำเข้าคู่ร้านที่ได้รับผลกระทบจากร้านเปิดใหม่ เพื่อสร้างฐานข้อมูลการพิจารณาชดเชย |
| รับข้อมูล/เงื่อนไข | ข้อมูลงวดเดือนและข้อมูลร้านจาก ALLMAP ที่ระบุร้านเปิดใหม่ ร้านถูกกระทบ ระยะทาง รัศมี โซน และประเภทสาขา |
| ระบบทำอะไรโดยสรุป | ระบบคัดเลือกร้านที่เข้าเกณฑ์ ตรวจซ้ำตามงวดและคู่ร้าน แล้วบันทึกเป็นรายการผลกระทบตั้งต้นสำหรับ pipeline ประกันรายได้ |
| ผลลัพธ์ที่ต้องได้ | รายการร้านถูกกระทบและร้านเปิดใหม่ถูกสร้าง/ปรับสถานะให้พร้อมสำหรับการขอยอดขายและการคำนวณต่อไป |
| ผู้ใช้ติดตามได้จาก | Admin เห็นจำนวนรายการที่นำเข้าและสถานะรอบล่าสุด; ทีมงานเห็นข้อมูลเป็น candidate ของเอกสารในขั้นต่อไป |


#### 3.3.3.3 Job 3 - นำเข้าร้านคู่แข่งจาก ALLMAP

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | นำเข้าข้อมูลคู่แข่งรอบล่าสุดของร้านที่ได้รับผลกระทบ |
| รับข้อมูล/เงื่อนไข | งวดปี/เดือนและข้อมูลคู่แข่งจาก ALLMAP เช่น รหัสคู่แข่ง ชื่อ สาขา โซน วันที่เปิด/ปิด |
| ระบบทำอะไรโดยสรุป | ระบบตรวจว่างวดนั้นเคยนำเข้าหรือยัง คัดข้อมูลคู่แข่งที่เกี่ยวข้อง แล้วบันทึกเข้าฐานข้อมูลคู่แข่งของร้านถูกกระทบ |
| ผลลัพธ์ที่ต้องได้ | ข้อมูลคู่แข่งพร้อมถูกนำไปแสดงในเอกสารประกันรายได้หลังระบบสร้างเอกสาร |
| ผู้ใช้ติดตามได้จาก | Admin ตรวจได้จาก run history; ผู้พิจารณาเห็นคู่แข่งในหน้าเอกสารเมื่อ sync สำเร็จ |


#### 3.3.3.4 Job 4 - เตรียมและส่งคำขอยอดขายไป IAS

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | ส่งคำขอข้อมูลยอดขายรายวันไปยัง IAS/MIS สำหรับร้านที่ต้องใช้ยอดขายประกอบการคำนวณ |
| รับข้อมูล/เงื่อนไข | รายการร้านที่รอข้อมูลยอดขาย, วันที่เปิดร้านใหม่, งวดที่ต้องตรวจ, และพารามิเตอร์รอบส่งไฟล์ |
| ระบบทำอะไรโดยสรุป | ระบบคัดรายการที่ครบเงื่อนไข สร้างไฟล์คำขอยอดขาย ส่งออกไปยัง IAS/MIS และบันทึกสถานะว่ารอผลตอบกลับ |
| ผลลัพธ์ที่ต้องได้ | ไฟล์คำขอยอดขายถูกส่งออก และรายการที่เกี่ยวข้องถูกตั้งสถานะรอข้อมูลขายกลับมา |
| ผู้ใช้ติดตามได้จาก | Admin เห็นชื่อไฟล์ จำนวนรายการ และสถานะส่งออก; งานที่ยังรอยอดขายไม่ควรถูกสร้างเอกสารก่อนครบข้อมูล |


#### 3.3.3.5 Job 5 - รับยอดขายจาก IAS + คำนวณ Growth

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | รับยอดขายจาก IAS/MIS แล้วคำนวณผลกระทบยอดขายก่อน/หลังร้านเปิดใหม่ |
| รับข้อมูล/เงื่อนไข | ไฟล์ยอดขายรายวันจาก IAS/MIS, รายการร้านที่เคยส่งคำขอ, และกฎจำนวนวัน/ช่วงเวลาที่ต้องเปรียบเทียบ |
| ระบบทำอะไรโดยสรุป | ระบบอ่านยอดขาย แยกช่วงก่อนและหลังเปิดร้านใหม่ทั้งปีก่อนหน้าและปีปัจจุบัน คำนวณอัตราเติบโตและผลต่าง แล้วตรวจความครบของวันทำการ |
| ผลลัพธ์ที่ต้องได้ | สรุปยอดขายและค่า growth rate ถูกบันทึก; รายการที่ข้อมูลไม่ครบหรือผิดเงื่อนไขถูกแยกให้ตรวจสอบก่อนเดิน workflow |
| ผู้ใช้ติดตามได้จาก | ผู้ใช้เห็นผลผ่านสถานะข้อมูลผิดปกติ/ข้อมูลพร้อมสร้างเอกสาร และ Admin เห็นจำนวน success/reject ใน run history |


#### 3.3.3.6 Job 6 - ซิงก์สถานะ + ส่งค่าชดเชยไป STA

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | ส่งข้อมูลชดเชยที่ผ่านเงื่อนไขไปยังระบบ Statement/บัญชี |
| รับข้อมูล/เงื่อนไข | เอกสารหรือรายการชดเชยที่อนุมัติแล้ว, ข้อมูล QSSI ที่เกี่ยวข้อง, และสถานะรายการที่ต้องส่ง Statement |
| ระบบทำอะไรโดยสรุป | ระบบคัดรายการที่พร้อมส่ง ตรวจเงื่อนไขสำคัญ สร้างข้อมูลส่งออกไป STA และบันทึก tracking เพื่อรอการตอบกลับ |
| ผลลัพธ์ที่ต้องได้ | รายการชดเชยถูกส่งไป STA/Statement และระบบมีรายการติดตาม ACK สำหรับ reconcile |
| ผู้ใช้ติดตามได้จาก | ทีมบัญชีและ Admin เห็นสถานะส่งออก/รอ ACK ผ่านรายงานและ Batch Job Console |


#### 3.3.3.7 Job 7 - บันทึกข้อมูลคู่แข่งเข้าเอกสาร

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | บันทึกข้อมูลคู่แข่งที่เกี่ยวข้องเข้าเอกสารประกันรายได้ |
| รับข้อมูล/เงื่อนไข | ข้อมูลคู่แข่งล่าสุดของร้านถูกกระทบและเอกสารประกันรายได้ที่สร้างแล้ว |
| ระบบทำอะไรโดยสรุป | ระบบจับคู่ข้อมูลคู่แข่งกับเอกสารที่เกี่ยวข้อง และบันทึกเข้ารายการคู่แข่งของเอกสารโดยไม่ให้ซ้ำ |
| ผลลัพธ์ที่ต้องได้ | หน้าเอกสารมีข้อมูลคู่แข่งครบสำหรับผู้พิจารณาใช้ประกอบการตัดสินใจ |
| ผู้ใช้ติดตามได้จาก | ผู้พิจารณาเห็นข้อมูลคู่แข่งในหน้าเอกสาร; Admin เห็นจำนวนรายการที่ sync สำเร็จหรือรอเอกสาร |


#### 3.3.3.8 Job 8 - สร้างเอกสารประกันรายได้อัตโนมัติ

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | สร้างเอกสารประกันรายได้อัตโนมัติจากข้อมูลร้านที่ผ่านเงื่อนไข |
| รับข้อมูล/เงื่อนไข | ข้อมูล impact process, ร้านถูกกระทบ, ร้านเปิดใหม่, ยอดชดเชยตั้งต้น, และสถานะพร้อมสร้างเอกสาร |
| ระบบทำอะไรโดยสรุป | ระบบตรวจว่าข้อมูลหลักครบหรือยัง สร้างเลขเอกสาร ผูกเอกสารกับ impact process และกันการสร้างเอกสารซ้ำ |
| ผลลัพธ์ที่ต้องได้ | เกิดเอกสารประกันรายได้พร้อมสถานะเริ่มต้น เพื่อรอเปิด workflow และเติมข้อมูลประกอบจาก job อื่น |
| ผู้ใช้ติดตามได้จาก | ผู้ใช้เห็นเอกสารใหม่ในรายการเมื่อสิทธิ์และ workflow พร้อม; Admin เห็นจำนวนเอกสารที่สร้าง/ข้ามเพราะมีอยู่แล้ว |


#### 3.3.3.9 Job 8b - เปิด Workflow ภายใน

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | เปิด workflow ภายในสำหรับเอกสารที่ผ่านเงื่อนไข Gen Flow Gate |
| รับข้อมูล/เงื่อนไข | เอกสารที่สร้างแล้ว, สถานะรอเปิด workflow, เงื่อนไข branch type, DV, นิติบุคคล, growth rate และ sales status |
| ระบบทำอะไรโดยสรุป | ระบบตรวจเงื่อนไข Gen Flow Gate ถ้าผ่านจะสร้าง workflow instance และ task แรก ถ้าไม่ผ่านจะคง/ปรับสถานะตามสาเหตุเพื่อให้ตรวจสอบหรือรันซ้ำได้ |
| ผลลัพธ์ที่ต้องได้ | เอกสารถูกส่งเข้าสู่ workflow และมี task ให้ผู้รับผิดชอบดำเนินการ หรือถูกคงสถานะรอแก้ไขเมื่อยังไม่ครบเงื่อนไข |
| ผู้ใช้ติดตามได้จาก | ผู้รับผิดชอบเห็นงานใน Inbox; Admin เห็นรายการผ่าน/ไม่ผ่าน gate และเหตุผลใน run history |


#### 3.3.3.10 Job 9 - บันทึกร้านเปิดใหม่เข้าเอกสาร

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | บันทึกร้านเปิดใหม่และสัดส่วนชดเชยเข้าเอกสารประกันรายได้ |
| รับข้อมูล/เงื่อนไข | ข้อมูลร้านเปิดใหม่ ค่า forecast/adjust และเอกสารที่เกี่ยวข้องกับ impact process |
| ระบบทำอะไรโดยสรุป | ระบบจับคู่ร้านเปิดใหม่กับเอกสาร บันทึกยอด/เปอร์เซ็นต์ชดเชย และตรวจว่าข้อมูลรวมพร้อมให้ผู้ใช้พิจารณาต่อ |
| ผลลัพธ์ที่ต้องได้ | หน้าเอกสารมีรายการร้านเปิดใหม่พร้อมยอดและเปอร์เซ็นต์ชดเชยสำหรับตรวจสอบ |
| ผู้ใช้ติดตามได้จาก | ผู้พิจารณาเห็นร้านเปิดใหม่ในหน้าเอกสาร; Admin เห็นจำนวนรายการ sync สำเร็จหรือรอเอกสาร |


#### 3.3.3.11 Job 10 - Watchdog เฝ้าระวัง ACK ค้าง

| หัวข้อ | รายละเอียด |
| --- | --- |
| เป้าหมาย | เฝ้าระวังรายการส่ง Statement ที่ยังไม่ได้รับผลตอบกลับจาก STA |
| รับข้อมูล/เงื่อนไข | รายการ interface ที่ส่งไป STA แล้วแต่ยังไม่มี ACK/ผลตอบกลับเกินระยะเวลาที่กำหนด |
| ระบบทำอะไรโดยสรุป | ระบบค้นหารายการค้าง จัดกลุ่มตามประเภทข้อมูลและไฟล์/ช่องทางส่ง แล้วส่งแจ้งเตือนให้ผู้เกี่ยวข้องติดตาม |
| ผลลัพธ์ที่ต้องได้ | เกิดอีเมลหรือรายการแจ้งเตือน pending ACK เพื่อให้ทีมงานตรวจสอบกับระบบปลายทาง |
| ผู้ใช้ติดตามได้จาก | Admin และทีมบัญชีเห็นรายการค้างผ่าน dashboard/report และได้รับการแจ้งเตือนตาม rule |


### 3.3.4 Required job outcomes

- ทุก job ต้องแสดงสถานะล่าสุดและประวัติการรันให้ Admin ตรวจสอบได้
- ผลลัพธ์ของ job ต้องตรวจนับได้ เช่น จำนวนไฟล์ จำนวนรายการที่อ่าน สำเร็จ ข้าม รอข้อมูล หรือผิดพลาด
- เมื่อ job ล้มเหลว ต้องมีข้อความสาเหตุที่ผู้ดูแลระบบใช้ติดตามกับทีมที่เกี่ยวข้องได้
- เมื่อไม่มีข้อมูลให้ประมวลผล ระบบต้องบันทึกเป็น no data หรือ skipped อย่างชัดเจน ไม่ถือว่าเป็น error โดยอัตโนมัติ
- job ที่ส่งหรือรับข้อมูลจากระบบภายนอกต้องมีสถานะติดตามปลายทาง เช่น รอ ACK, ได้รับ ACK, หรือค้างเกินกำหนด
- การรันซ้ำต้องไม่ทำให้เอกสาร รายการร้าน คู่แข่ง ยอดขาย หรือข้อมูล Statement ซ้ำ

---


## 3.4 K2 Screen Requirements

> Committed implementation scope ของหน้าจอ SBP Mall คือ 10 หน้า + 1 placeholder/deferred: SCR-05 ข้อมูลผิดปกติ / แจกงานยังเป็น OPEN item ใช้อธิบายกฎยอดขายไม่ครบ 60 วันเท่านั้น และไม่ถูกนับเป็นงานสร้างหน้า FE/BE จนกว่าจะมีคำตัดสิน keep/drop


### SCR-01 Overview / Dashboard

![รูปที่ 13: Overview / Dashboard - ส่วนที่ 1/2](index-01.png)

![รูปที่ 14: Overview / Dashboard - ส่วนที่ 2/2](index-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงงานค้าง ร้านที่เข้าเกณฑ์ ยอดชดเชย ข้อมูลผิดปกติ กราฟ และทางลัดตามสิทธิ์ |
| Actor | ทุก role ที่ login |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ผู้ใช้เห็นสถานะและงานสำคัญตามสิทธิ์ พร้อมเปิดรายการเป้าหมายจากทางลัดได้ |
| Scope status | Committed |


#### Actions

งานรอท่านดำเนินการ · เอกสารร้านถูกกระทบ · เปิดเอกสารร้านถูกกระทบ · ออกรายงานสรุปสถานะ


#### Business rules / acceptance

- ตัวเลขต้อง aggregate จากข้อมูลจริงและรองรับ cache ไม่เกิน 5 นาที
- ทางลัดและ sidebar ต้องสร้างตาม menu_permissions
- ค่าชื่อผู้ใช้/role ต้องมาจาก JWT ไม่ใช้ข้อมูล mock

### SCR-02 สร้างเอกสาร

![รูปที่ 15: สร้างเอกสาร](k2-create-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | สร้างเอกสารนอกเงื่อนไขอัตโนมัติ หรือส่งสร้างผ่าน FS |
| Actor | HQ 02, User Admin 03 และผู้ที่ได้รับสิทธิ์ |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ระบบสร้างเอกสารเพียงหนึ่งรายการต่อร้าน/งวด ออกเลขเอกสาร และเปิดงานเริ่มต้นสำเร็จ |
| Scope status | Committed |


#### Input / filter fields

รหัสร้านถูกกระทบ * · ชื่อร้านถูกกระทบ (อัตโนมัติ) · ภาค (อัตโนมัติ) · ประเภทร้าน · วันที่โอนเป็นร้าน SP · เดือน/ปีที่ถูกกระทบ * · ครั้งที่ · รหัสร้านเปิดใหม่ (ที่ทำให้กระทบ) * · เหตุผลการสร้างเอกสารนอกเงื่อนไข * · Period Statement (From - To)


#### Displayed tables

- Table: รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ

#### Actions

เคลียร์ค่าเริ่มใหม่ · สร้างเอกสาร · ส่งสร้างที่ FS


#### Business rules / acceptance

- Manual tab ต้องระบุรหัสร้าน เดือน/ปี ร้านเปิดใหม่ และเหตุผล
- FS tab ต้องระบุรหัสร้าน เดือน/ปี และ Period Statement
- ตรวจ duplicate ร้าน+งวดก่อนสร้าง
- ออกเลขเอกสารอัตโนมัติและเปิด workflow Section 06

### SCR-03 เอกสารรอดำเนินการ

![รูปที่ 16: เอกสารรอดำเนินการ - ส่วนที่ 1/2](k2-list-waiting-01.png)

![รูปที่ 17: เอกสารรอดำเนินการ - ส่วนที่ 2/2](k2-list-waiting-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | Task inbox แสดงเฉพาะ OPEN task ที่ผู้ใช้/section ปัจจุบันต้องดำเนินการ |
| Actor | ผู้ดำเนินการ workflow |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ผู้ใช้เปิดดำเนินการเฉพาะ task ที่ตนรับผิดชอบและเห็นรายการผิดปกติอย่างชัดเจน |
| Scope status | Committed |


#### Input / filter fields

ค้นหา · สถานะ · ภาค · ประเภทร้าน · วันที่สร้าง · ยอดขายที่ลดลง (%) · เงินชดเชย (บาท) · รอ (วัน)


#### Displayed tables

- tblK2: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง | จำนวนเงินที่ชดเชย | สถานะ | รอ (วัน)
- tblRelated: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง | จำนวนเงินที่ชดเชย | สถานะ | รอ (วัน)

#### Actions

ล้างตัวกรอง


#### Business rules / acceptance

- filter ด้วยข้อความ สถานะ ภาค ประเภทร้าน วันที่ ยอดขายลด เงินชดเชย และวันค้าง
- คลิกแถวเปิดเอกสาร; งานข้อมูลยอดขายไม่ครบ 60 วันเป็นแถวแดง
- Role switcher เป็น prototype aid เท่านั้น Production ใช้ JWT/assignment จริง

### SCR-04 เอกสารที่เกี่ยวข้อง

![รูปที่ 18: เอกสารที่เกี่ยวข้อง - ส่วนที่ 1/2](k2-list-related-01.png)

![รูปที่ 19: เอกสารที่เกี่ยวข้อง - ส่วนที่ 2/2](k2-list-related-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงเอกสารทั้งหมดที่ผู้ใช้เคยมีส่วนร่วม โดยแก้ไขได้เฉพาะงานที่อยู่ในสิทธิ์ปัจจุบัน |
| Actor | ผู้ใช้งานทั่วไปตามสิทธิ์ |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ผู้ใช้ค้นและเปิดเอกสารที่เกี่ยวข้องได้ โดยรายการนอก task ปัจจุบันเป็น read-only |
| Scope status | Committed |


#### Input / filter fields

ค้นหา · สถานะ · ภาค · ประเภทร้าน · วันที่สร้าง · ยอดขายที่ลดลง (%) · เงินชดเชย (บาท) · รอ (วัน)


#### Displayed tables

- tblK2: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง | จำนวนเงินที่ชดเชย | สถานะ | รอ (วัน)
- tblRelated: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง | จำนวนเงินที่ชดเชย | สถานะ | รอ (วัน)

#### Actions

ล้างตัวกรอง


#### Business rules / acceptance

- filter และ columns เหมือนหน้ารอดำเนินการ
- เอกสารนอก task ปัจจุบันต้องเป็น read-only
- ผลการค้นหาต้องจำกัดตาม role และ record-level access

### SCR-05 ข้อมูลผิดปกติ / แจกงาน (placeholder/deferred)

![รูปที่ 20: ข้อมูลผิดปกติ / แจกงาน (placeholder/deferred)](k2-list-abnormal-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | Placeholder สำหรับค้นหาและมอบหมายรายการผิดปกติ โดยใช้กฎยอดขายไม่ครบ 60 วัน |
| Actor | Assign Job 05 และ Admin |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ยังไม่มีผลลัพธ์ที่ commit; หากอนุมัติ scope ระบบต้องบันทึกผู้รับผิดชอบและสถานะ assignment |
| Scope status | Deferred / OPEN |


#### Input / filter fields

ค้นหา · ภาค · สาเหตุผิดปกติ · สถานะ · ผู้รับผิดชอบ


#### Displayed tables

- tblAbnormal: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ | Action

#### Actions

แจกงานที่เลือก · ล้างตัวกรอง


#### Business rules / acceptance

- OPEN: ไม่เป็นหน้าจอ committed ใน scope FE/BE รอบนี้
- ถ้าเปิด scope ในอนาคต ต้องรองรับ multi-select และแจกงานเฉพาะรายการที่เลือก
- ถ้าเปิด scope ในอนาคต ต้องแสดงสาเหตุ ผู้รับผิดชอบ และสถานะ assignment
- OPEN: เมนูนี้และ API 2 เส้นถูก comment ไว้ รอคำตัดสิน keep/drop

### SCR-06 เอกสารข้อมูลร้านถูกกระทบ

![รูปที่ 21: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 1/3](k2-document-01.png)

![รูปที่ 22: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 2/3](k2-document-02.png)

![รูปที่ 23: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 3/3](k2-document-03.png)

| Item | Requirement |
| --- | --- |
| Purpose | หน้าหลักสำหรับดู แก้ คำนวณ พิจารณา แนบไฟล์ และเดิน workflow |
| Actor | ผู้ดำเนินการตาม Section และผู้มีสิทธิ์อ่าน |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ข้อมูลที่แก้ไขถูกตรวจสอบ บันทึก audit และเปลี่ยนสถานะ workflow ตาม action ที่ได้รับอนุญาต |
| Scope status | Committed |


#### Input / filter fields

เงินชดเชยร้านถูกกระทบ (ตั้งต้น) · รวม %ชดเชยร้านเปิดใหม่ · เงินชดเชยรวม (ร้านเปิดใหม่ 1+2) · อำนาจอนุมัติ · ความคิดเห็นเพิ่มเติม * · ชื่อผู้พิจารณา · ตำแหน่ง · ผลการพิจารณา · วัน/เวลา · รายละเอียดการพิจารณา


#### Displayed tables

- tbldocument_new_stores: ลำดับ | รหัสร้าน | ชื่อร้านเปิดใหม่ | ภาค | ประเภทร้าน | เจ้าของร้าน | นิติบุคคล | วันที่เปิดร้าน | วันที่ปิดร้าน | ระยะห่าง (กม.) | %ชดเชย | เงินชดเชย (ร้านใหม่)
- tblCompetitor: ร้านคู่แข่ง | วันที่เปิดกระทบ | รายละเอียดเพิ่มเติม | Action
- tblFactorsDoc: ปัจจัยภายนอก | วันที่เริ่มต้น | วันที่สิ้นสุด | รายละเอียดเพิ่มเติม | Action
- Table: ไฟล์แนบ | ตำแหน่ง | ผู้สร้างแนบไฟล์ | รายละเอียดเพิ่มเติม | วัน/เดือน/ปี
- tblCompHistory: ครั้ง | เดือน/ปีที่กระทบ | จำนวนเงินที่ชดเชย | เดือน/ปีที่ส่งบัญชี | สถานะเอกสาร | ผลการพิจารณา | เอกสาร
- tblDecisionHistory: ชื่อผู้พิจารณา | ตำแหน่ง | ผลการพิจารณา | รายละเอียดการพิจารณา | วัน/เวลา

#### Actions

พิมพ์ · ข้อมูลยอดขายเพิ่มเติม · Link To ALLMAP · รีเฟรช · คืนค่าก่อนแก้ไข · คำนวณเงินชดเชย · เพิ่ม · บันทึก · เพิ่มข้อมูล · แนบไฟล์ · แนบรูป · ส่งดำเนินการ · OK · ปิด


#### Business rules / acceptance

- แสดงหัวเอกสาร ร้านถูกกระทบ ร้านเปิดใหม่ แผนที่ คู่แข่ง ปัจจัย เอกสารแนบ ชดเชย ประวัติ และผลพิจารณา
- สิทธิ์แก้ไขต้องประเมินต่อ section/role; ส่วนอื่นเป็น read-only
- % ชดเชยร้านเปิดใหม่รวมต้องเท่ากับ 100%
- วันที่สิ้นสุดปัจจัยต้องไม่ก่อนวันที่เริ่มต้น
- ไฟล์แนบไม่เกิน 5 MB และต้องบันทึก section/uploader/time
- ส่งดำเนินการต้องเลือกผล; ข้อความ popup ต้องตรงตาม SRS

### SCR-07 รายงานสรุปสถานะ

![รูปที่ 24: รายงานสรุปสถานะ - ส่วนที่ 1/2](k2-report-01.png)

![รูปที่ 25: รายงานสรุปสถานะ - ส่วนที่ 2/2](k2-report-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหา แสดงกราฟ/ผล 19 คอลัมน์ และ Export CSV to Batch |
| Actor | Admin 01, HQ 02, Report Admin 04, Report Admin Special 06 |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ผลบนหน้าจอและไฟล์ CSV ตรงกันภายใต้ filter เดียวกันและนำไปตรวจสอบบัญชีได้ |
| Scope status | Committed |


#### Input / filter fields

รหัสร้านที่ถูกกระทบ · ชื่อร้านที่ถูกกระทบ · รหัสร้านเปิดกระทบ (ร้านเปิดใหม่) · เดือน/ปี (เริ่มต้น) · ถึง (สิ้นสุด) · ประเภทร้าน (เลือกได้มากกว่า 1) · A · B · C · D · สถานะ * (บังคับ · เลือก 1 สถานะ) · ผลการพิจารณา * (บังคับ) · ประกันรายได้ · ไม่ประกันรายได้ · ภาค (เลือกได้มากกว่า 1 · เพิ่มภาคใหม่อัตโนมัติ) · BE · BS · NEU · REU · RSU · BG · BW · RC · RN · BN · NEL · REL · RSL · Period Statement (From - To)


#### Displayed tables

- Table: รหัสร้านถูกกระทบ | ชื่อร้านถูกกระทบ | ภาค | ประเภทร้าน | เดือนปีที่ถูกกระทบ | วันที่โอนเป็นร้าน SP | Period Statement | รหัสร้านเปิดใหม่ | ชื่อร้านเปิดใหม่ | ภาค (ร้านใหม่) | ประเภทร้าน (ร้านใหม่) | ยอดเงินชดเชย | สถานะ | ชื่อ-นามสกุลผู้ดำเนินการ | ผลการพิจารณา | รอดำเนินการ (วัน) | ครั้งที่ | วันที่สร้าง | เลขที่เอกสาร

#### Actions

Export CSV to Batch · เคลียร์ค่าเริ่มใหม่ · Preview Report


#### Business rules / acceptance

- บังคับระบุปีและคืนเฉพาะรายการที่มีเลขเอกสาร
- ประเภทร้านและภาคเลือกหลายค่า; สถานะและผลพิจารณาเลือกหนึ่งค่า
- ผลและ CSV Export to Batch ต้องใช้ dataset/เงื่อนไขเดียวกัน
- บัญชีใช้รายงานนี้เพื่อตรวจยอดและกระทบ SAP นอก workflow หลังเอกสารเสร็จสิ้น
- แถวข้อมูลยอดขายไม่ครบ 60 วันต้องเป็นสีแดง

### SCR-08 กำหนดผู้ปฏิบัติงาน

![รูปที่ 26: กำหนดผู้ปฏิบัติงาน](k2-operators-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการผู้ปฏิบัติงานต่อ section และ zone |
| Actor | Admin 01, HQ 02, User Admin 03 |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | assignment ต่อ section/zone มีผลกับการแจก task และตรวจสอบประวัติการเปลี่ยนแปลงได้ |
| Scope status | Committed |


#### Displayed tables

- tblOperators: ชื่อผู้ปฏิบัติงาน | E-Mail | ชื่อตำแหน่ง | ภาคที่รับผิดชอบ | Action
- Table: วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม -> ข้อมูลใหม่ | เหตุผลการแก้ไข

#### Actions

ค้นหาพนักงาน (Pop Up) · เพิ่มผู้ปฏิบัติงาน · เคลียร์ค่าเริ่มใหม่ · x


#### Business rules / acceptance

- ชื่อพนักงานและตำแหน่งเป็น required; เลือกพนักงานจาก popup
- แสดงภาคเมื่อเป็นตำแหน่งส่งเสริมธุรกิจพันธมิตรฯ
- เพิ่ม/แก้/ลบต้องบันทึก audit และเหตุผลเมื่อแก้ไข

### SCR-09 กำหนดปัจจัยภายนอก

![รูปที่ 27: กำหนดปัจจัยภายนอก](k2-factors-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการ external factor master และประวัติแก้ไข |
| Actor | Admin 01, HQ 02, User Admin 03 |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | external factor master พร้อมใช้งานในเอกสารและตรวจสอบผู้แก้/เหตุผลย้อนหลังได้ |
| Scope status | Committed |


#### Displayed tables

- tblFactors: รหัสปัจจัย | ชื่อปัจจัย | รายละเอียดเพิ่มเติม | Action
- Table: วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม -> ข้อมูลใหม่ | เหตุผลการแก้ไข

#### Actions

เพิ่มปัจจัยภายนอก · เคลียร์ค่าเริ่มใหม่


#### Business rules / acceptance

- factor_code และ factor_name เป็น required; factor_code ห้ามซ้ำ
- แก้ได้เฉพาะชื่อและรายละเอียด; ต้องระบุเหตุผล
- ทุก mutation ต้องบันทึก audit_logs

### SCR-10 สิทธิ์การเข้าถึงเมนู

![รูปที่ 28: สิทธิ์การเข้าถึงเมนู - ส่วนที่ 1/2](k2-permissions-01.png)

![รูปที่ 29: สิทธิ์การเข้าถึงเมนู - ส่วนที่ 2/2](k2-permissions-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงและบริหาร RBAC 8 role ต่อ main menu และ master forms |
| Actor | Admin และผู้ดูแลสิทธิ์ที่ได้รับมอบหมาย |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | เมนูและ API บังคับสิทธิ์จาก policy เดียวกันและการเปลี่ยนสิทธิ์มี audit |
| Scope status | Committed |


#### Displayed tables

- tblRoles: Code | Role | คำอธิบาย | Action
- tblAudit: วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม -> ข้อมูลใหม่ | เหตุผลการแก้ไข

#### Actions

เพิ่ม Role · เพิ่มเมนู · บันทึกสิทธิ์ 0 · x · ยกเลิก · ตกลง


#### Business rules / acceptance

- sidebar ต้องอิงสิทธิ์จาก backend ไม่ใช่ซ่อนเฉพาะฝั่ง FE
- API ต้องตรวจ role/record access ซ้ำทุก request
- การเปลี่ยนสิทธิ์ต้อง audit และมีผลกับ token/session ตามนโยบาย

### SCR-11 ตั้งค่าระบบ (Global Config)

![รูปที่ 30: ตั้งค่าระบบ (Global Config) - ส่วนที่ 1/2](system-config-01.png)

![รูปที่ 31: ตั้งค่าระบบ (Global Config) - ส่วนที่ 2/2](system-config-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการค่ากำหนดกลางที่ใช้ร่วมทั้งระบบ เช่น รัศมีผลกระทบ เกณฑ์ข้อมูล วงเงินอนุมัติ timeout และ notification switch |
| Actor | Admin และผู้ดูแลระบบที่ได้รับมอบหมาย |
| Pre-condition | ผ่านการยืนยันตัวตนจาก platform กลาง และมีสิทธิ์เมนู/ข้อมูล |
| Post-condition / expected outcome | ค่ากำหนดที่ผ่าน validation ถูกเผยแพร่ให้บริการที่เกี่ยวข้องโดยไม่เปิดเผย secret |
| Scope status | Committed |


#### Displayed tables

- tblConfigs: Config Key | หมวดหมู่ | ค่า (Value) | ชนิดข้อมูล | หน่วย | คำอธิบาย | แก้ไขได้ | Action
- Table: วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม -> ข้อมูลใหม่ | เหตุผลการแก้ไข

#### Actions

เพิ่ม Config · Invalidate Cache


#### Business rules / acceptance

- config_key ต้องเป็น dot notation และห้ามซ้ำ
- value_type ต้อง validate ค่า NUMBER, STRING, BOOLEAN, JSON หรือ CRON ก่อนบันทึก
- ค่าที่ is_editable=false เป็นค่าคงที่ทางธุรกิจ แก้หรือลบผ่าน UI/API ไม่ได้
- ห้ามเก็บ secret เช่น password, API key หรือ connection string ใน system_configs
- ทุกการเพิ่ม แก้ ลบ และ invalidate cache ต้องบันทึก audit_logs พร้อมเหตุผล

### 3.4.13 Notification template requirements

> ระบบต้องรองรับการจัดการเนื้อหาและกฎการส่ง notification ตามรายการในหัวข้อนี้ โดยหน้าจอจัดการ template เป็นส่วนหนึ่งของขอบเขตผู้ดูแลระบบ

![รูปที่ 32: Email Template Administration - ส่วนที่ 1/3](plan-email-01.png)

![รูปที่ 33: Email Template Administration - ส่วนที่ 2/3](plan-email-02.png)

![รูปที่ 34: Email Template Administration - ส่วนที่ 3/3](plan-email-03.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการเนื้อหาอีเมล 8 template ของ Notification Service และจุดส่ง workflow/batch |
| Scope status | Committed - ครอบคลุมหน้าจอผู้ดูแล template และพฤติกรรม Notification Service |

- รองรับ template EM-01 ถึง EM-08 ครอบคลุม workflow transition, reminder, escalation, batch error และ STA ACK watchdog
- แก้ไขได้เฉพาะ subject/body และตัวแปร merge ที่รองรับของ template นั้น
- From/To/Cc ต้องล็อกตาม status_email_rules หรือ config ต่อ job ไม่ให้แก้ใน template
- ต้องรีเซ็ตกลับ Default ได้ทั้งราย template และทั้งหมด
- ทุกการแก้ไขหรือรีเซ็ตต้องบันทึก audit_logs พร้อมเหตุผล

### 3.4.14 Shared UI contract

- ทุกหน้าจอต้องมี metadata สำหรับ page, nav, module, breadcrumb, sidebar mount และ main content
- Header/sidebar ถูกสร้างโดย shared shell; ห้ามทำซ้ำในแต่ละหน้า
- Schema modal อ้างชื่อ table header แบบ exact match; การเปลี่ยน label ต้องแก้ mapping และทดสอบ add/view/edit/delete
- รองรับ desktop และ responsive layout; ตารางกว้างต้องเลื่อนแนวนอนโดยไม่ตัดข้อมูล
- ข้อความ popup/validation ภาษาไทยและ source tag (FGI/FCS), (K2), (ใหม่) ต้องคงตามข้อกำหนด

## 3.5 API Requirements

> หัวข้อนี้กำหนด capability ของ API วิธีเรียกใช้ สิทธิ์ และพฤติกรรมร่วมที่ต้องตรวจรับ บริการ Auth Group 1 จัดหาโดย platform กลางและไม่อยู่ในขอบเขตการพัฒนา Login/SSO ของ SBP Mall


### 3.5.1 Interface requirements

| Topic | Requirement |
| --- | --- |
| User identity and access | ระบบต้องตรวจสิทธิ์ผู้ใช้ทุกหน้าจอและทุกการเปลี่ยนข้อมูลตาม role/menu/current task owner |
| Consistent user feedback | ข้อความ error, popup และ validation ที่มีใน SRS ต้องแสดงตรงตัวและไม่ตีความใหม่ในแต่ละหน้าจอ |
| Document action | ระบบต้องรับผลพิจารณาจากผู้ถือสิทธิ์ปัจจุบัน ตรวจ result ที่อนุญาต และคืน statusCode ตาม convention กลาง |
| Search and report lists | รายการค้นหาและรายงานต้องรองรับข้อมูลจำนวนมากโดยแบ่งหน้า/จำกัดผลลัพธ์ตามสิทธิ์ |
| Lookup data | สถานะเอกสาร, workflow section, role/menu และ master data ต้องมีแหล่งข้อมูลกลางเพื่อให้ FE/BE ใช้ค่าเดียวกัน |
| Audit | ทุกการเปลี่ยนข้อมูลต้องบันทึกผู้กระทำ เวลา เหตุผล/ผลพิจารณา และค่าก่อน/หลังตามโดเมนที่เกี่ยวข้อง |
| Duplicate prevention | การสร้างเอกสาร เปิด workflow รับ callback และสั่ง batch ต้องป้องกันข้อมูลซ้ำจากการรันซ้ำหรือกดซ้ำ |
| Contract consistency | ทุก endpoint ต้องใช้รูปแบบ payload, field naming, status code, error envelope, pagination และ security mechanism ตามข้อกำหนดร่วมใน 3.5.3 |


### 3.5.2 Endpoint catalog

| Group | Method | Path | Roles | Purpose |
| --- | --- | --- | --- | --- |
| Auth & สิทธิ์ผู้ใช้ (platform service) | POST | /api/v1/auth/login | ทุกคน (public) | เข้าสู่ระบบด้วยบัญชีพนักงาน แลก JWT พร้อม role และ section สำหรับใช้ทุกเส้นถัดไป |
| Auth & สิทธิ์ผู้ใช้ (platform service) | POST | /api/v1/auth/refresh | ผู้ถือ refreshToken | ต่ออายุ accessToken โดยไม่ต้อง login ใหม่ |
| Auth & สิทธิ์ผู้ใช้ (platform service) | GET | /api/v1/auth/me | ทุก role | ข้อมูลผู้ใช้ปัจจุบันจาก JWT - FE ใช้แสดงชื่อ/role มุมขวาบน |
| Auth & สิทธิ์ผู้ใช้ (platform service) | GET | /api/v1/me/menus | ทุก role | เมนูที่ role ของผู้ใช้เข้าถึงได้ - FE ใช้สร้าง sidebar (แทนตารางสิทธิ์ 8 role ในหน้าสิทธิ์การเข้าถึงเมนู) |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/tasks | role ที่มีสิทธิ์เมนูเอกสาร | งานรอท่านดำเนินการ - เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า Task Inbox) |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents | ตามสิทธิ์เมนู | ค้นหาเอกสารที่เกี่ยวข้อง - บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS) |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo} | ตามสิทธิ์เมนู | เอกสารฉบับเต็ม 12 ส่วนย่อย (Document Detail) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents | 02 HQ, 03 User Admin | สร้างเอกสารใหม่นอกเงื่อนไข หรือสร้างเอกสารที่ FS (สองแท็บของ Create Document) |
| งาน & เอกสารประกันรายได้ | PUT | /api/v1/documents/{docNo} | ตาม section ปัจจุบัน | บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่ |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents/{docNo}/actions | เจ้าของ task ปัจจุบัน | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน - หัวใจ workflow 5 ขั้น · กฎวงเงิน 100,000 ใช้ทั้งกรณีชดเชยและไม่ชดเชย |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo}/timeline | ตามสิทธิ์เมนู | ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร) |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents/{docNo}/attachments | ตาม section ปัจจุบัน | แนบไฟล์เข้าเอกสาร - จำกัด 5MB ต่อไฟล์ตาม SRS |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo}/attachments/{attachId}/download | ตามสิทธิ์อ่านเอกสาร | ดาวน์โหลดไฟล์แนบผ่าน BE stream โดยตรวจสิทธิ์เอกสารและ scanStatus=CLEAN ก่อนส่ง binary |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo}/sales | ตามสิทธิ์เมนู | ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง x 15 วัน) - ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร Document Detail |
| ข้อมูล Lookup | GET | /api/v1/stores/search | ตามสิทธิ์เมนูเอกสาร | ค้นหาร้าน (แว่นขยายในหน้า Create Document) - ร้านถูกกระทบ (SP) หรือร้านเปิดใหม่ 7-Eleven ตาม type |
| ข้อมูล Lookup | GET | /api/v1/competitors | ตาม section ปัจจุบัน | รายการร้านคู่แข่ง master 24 ราย - dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (Document Detail) |
| ข้อมูล Lookup | GET | /api/v1/document-statuses | ทุก role | รายการสถานะเอกสารทั้งหมด - เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (เอกสารที่เกี่ยวข้อง) และรายงาน (รายงานสรุปสถานะ) |
| ข้อมูล Lookup | GET | /api/v1/workflow-sections | ทุก role | รายการ Section 5 ขั้น - dropdown เลือกตำแหน่ง/ขั้น (หน้ากำหนดผู้ปฏิบัติงาน) และตัวกรองตาม section |
| Master Data | GET | /api/v1/operators | 03 User Admin | รายชื่อผู้ปฏิบัติงาน (operator_assignments) พร้อมค้นหา/แบ่งหน้า |
| Master Data | POST | /api/v1/operators | 03 User Admin | เพิ่มผู้ปฏิบัติงานใหม่ (จากหน้าค้นหาพนักงานด้วยแว่นขยาย) |
| Master Data | PUT | /api/v1/operators/{id} | 03 User Admin | แก้ไขข้อมูลผู้ปฏิบัติงาน |
| Master Data | DELETE | /api/v1/operators/{id} | 03 User Admin | ลบผู้ปฏิบัติงาน พร้อมบันทึกเหตุผล |
| Master Data | GET | /api/v1/factors | 03 User Admin | รายการปัจจัยภายนอก (external_factors) |
| Master Data | POST | /api/v1/factors | 03 User Admin | เพิ่มปัจจัยภายนอก - รหัสห้ามซ้ำ (กติกา SRS) |
| Master Data | PUT | /api/v1/factors/{code} | 03 User Admin | แก้ไขปัจจัยภายนอก |
| Master Data | DELETE | /api/v1/factors/{code} | 03 User Admin | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) |
| Master Data | GET | /api/v1/employees/search | 03 User Admin | ค้นหาพนักงานจากระบบ HR (popup แว่นขยายในหน้ากำหนดผู้ปฏิบัติงาน) |
| Master Data | GET | /api/v1/menu-permissions | 01 Admin, 02 HQ | ตาราง matrix สิทธิ์เมนูทั้งหมด (8 role x เมนู) - หน้าจอสิทธิ์การเข้าถึงเมนู |
| Master Data | PUT | /api/v1/menu-permissions/{menuCode} | 01 Admin, 02 HQ | แก้สิทธิ์การเข้าถึงเมนูหนึ่งรายการต่อทุก role - บันทึก audit เสมอ |
| Master Data | GET | /api/v1/roles | 01 Admin, 02 HQ | รายการ Role ทั้งหมด (ตารางกลุ่มผู้ใช้งานในหน้าสิทธิ์การเข้าถึงเมนู และ dropdown ที่อื่น) |
| Master Data | POST | /api/v1/roles | 01 Admin, 02 HQ | เพิ่ม Role ใหม่ - ระบบสร้างสิทธิ์เมนูเริ่มต้นเป็น "ไม่มีสิทธิ์" ทุกเมนู |
| Master Data | PUT | /api/v1/roles/{roleCode} | 01 Admin, 02 HQ | แก้ชื่อ/คำอธิบาย Role - ต้องระบุเหตุผล บันทึก audit เสมอ |
| Master Data | DELETE | /api/v1/roles/{roleCode} | 01 Admin, 02 HQ | ลบ Role - ลบไม่ได้ถ้าเป็น Role ระบบ (is_system) หรือยังมีผู้ใช้อ้างอยู่ |
| Master Data | POST | /api/v1/menus | 01 Admin, 02 HQ | เพิ่มเมนูใหม่เข้าระบบ - สิทธิ์เริ่มต้นเป็น "ไม่มีสิทธิ์" ทุก Role |
| Master Data | PUT | /api/v1/menus/{menuCode} | 01 Admin, 02 HQ | แก้ชื่อ/กลุ่ม/ลำดับเมนู - ต้องระบุเหตุผล บันทึก audit เสมอ |
| Master Data | DELETE | /api/v1/menus/{menuCode} | 01 Admin, 02 HQ | ลบเมนูพร้อมสิทธิ์ทุก Role ของเมนูนั้น (cascade) - เมนูระบบลบไม่ได้ |
| Master Data | GET | /api/v1/audit-logs | 01 Admin, 02 HQ, 03 User Admin | ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม->ใหม่ · เหตุผล · เมื่อไร) - แผงประวัติท้ายหน้าจอ 3.1.8 / 3.1.9 |
| System Config (Global) | GET | /api/v1/configs | 01 Admin | รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ Global Config) |
| System Config (Global) | GET | /api/v1/configs/{key} | ทุก role (อ่าน) / service token | อ่านค่ากำหนดรายตัว - เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที |
| System Config (Global) | POST | /api/v1/configs | 01 Admin | เพิ่มค่ากำหนดใหม่ - key ห้ามซ้ำ และ validate ค่าตาม value_type |
| System Config (Global) | PUT | /api/v1/configs/{key} | 01 Admin | แก้ค่ากำหนด - ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้ |
| System Config (Global) | DELETE | /api/v1/configs/{key} | 01 Admin | ลบค่ากำหนด - ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล |
| Email Template (Notification) | GET | /api/v1/email-templates | 01 Admin | รายการ 8 email template (EM-01-08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ Email Template) |
| Email Template (Notification) | GET | /api/v1/email-templates/{code} | 01 Admin | อ่าน template รายตัว (EM-01-08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น |
| Email Template (Notification) | PUT | /api/v1/email-templates/{code} | 01 Admin | บันทึกเนื้อหา template - แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules) |
| Email Template (Notification) | POST | /api/v1/email-templates/{code}/reset | 01 Admin | รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ) |
| Email Template (Notification) | POST | /api/v1/email-templates/reset-all | 01 Admin | รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default") |
| รายงาน | GET | /api/v1/reports/status-summary | บัญชี / 06 Report Admin | รายงานตรวจสอบประกันรายได้ (SBP Mall) - Preview Report · บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) |
| รายงาน | GET | /api/v1/reports/status-summary/export | 04 / 06 Report Admin | Export CSV to Batch - ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไขเดียวกับเส้นค้นหา |
| Batch Job Admin | GET | /api/v1/jobs | 01 Admin | รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด (หน้าจอ Batch Job Console) |
| Batch Job Admin | GET | /api/v1/jobs/{jobNo} | 01 Admin | รายละเอียด job หนึ่งตัว: schedule, input/configurable parameters, output, current status และ run controls |
| Batch Job Admin | PUT | /api/v1/jobs/{jobNo}/params | 01 Admin | แก้พารามิเตอร์ที่แก้ได้ของ job (เวลารัน, path, เกณฑ์) - ค่าคงที่ทางธุรกิจแก้ผ่าน API ไม่ได้ |
| Batch Job Admin | POST | /api/v1/jobs/{jobNo}/run | 01 Admin | สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล - มี guard กันรันซ้อน |
| Batch Job Admin | PUT | /api/v1/jobs/{jobNo}/enabled | 01 Admin | เปิด/ปิดการทำงานของ job ตามรอบเวลา |
| Batch Job Admin | GET | /api/v1/jobs/{jobNo}/runs | 01 Admin | ประวัติการรันของ job (แท็บประวัติในหน้า Batch Monitor) |
| Workflow ภายใน | POST | /api/v1/workflows/instances | service token (ภายใน) | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate - เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม |
| Workflow ภายใน | GET | /api/v1/workflows/instances/{id} | 01 Admin / เจ้าของงาน | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) |
| Workflow ภายใน | GET | /api/v1/workflows/summary | 01 Admin | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น |
| Interface & Dashboard | GET | /api/v1/interfaces/tracking | 01 Admin | สถานะการรับ-ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) |
| Interface & Dashboard | POST | /api/v1/interfaces/sta/ack | API key ของระบบ STA | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง - แทนการรออัปเดต return_code ฝั่งเดียว |
| Interface & Dashboard | GET | /api/v1/interfaces/pending-ack | 01 Admin | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) - ใช้ทั้งหน้า dashboard และอีเมลเตือน |
| Interface & Dashboard | GET | /api/v1/dashboard/summary | ทุก role | ตัวเลขหน้า Dashboard: งานค้าง, ร้านประกันรายได้เดือนนี้, ยอดชดเชย, ข้อมูลผิดปกติ + ข้อมูลกราฟ |


### 3.5.3 API contract requirements

- Request/response JSON ใช้ camelCase และ Content-Type application/json; file download ต้องระบุ content type และ filename ที่ถูกต้อง
- ผลสำเร็จต้องคืน HTTP status ที่สอดคล้องกับการทำงาน เช่น 200, 201, 202 หรือ 204 และ payload ต้องมีข้อมูลที่ FE ใช้อัปเดตหน้าจอได้
- ข้อผิดพลาดต้องคืนโครงสร้างกลางอย่างน้อย code, message และ correlationId; validation error ต้องระบุ field ที่ไม่ผ่านเมื่อทำได้
- List/search/report ต้องรองรับ page, size, sort และ filter ที่ระบุ พร้อม totalElements/totalPages หรือ cursor ที่มีความหมายเทียบเท่า
- วันที่เวลาใน API ใช้ ISO 8601 และ UTC; UI แปลงเป็น Asia/Bangkok ส่วนรอบเดือน/ปีต้องระบุรูปแบบใน field อย่างชัดเจน
- Endpoint ที่สร้างเอกสาร เปิด workflow ส่ง action รับ callback หรือสั่ง batch ต้องรองรับ duplicate guard/idempotency
- ทุก request ต้องตรวจ token, role, menu permission, record access และ current task owner ที่ฝั่ง server ก่อนอ่านหรือเปลี่ยนข้อมูล
- Mutation ต้องบันทึก actor, เวลา, correlationId, เหตุผลหรือผลพิจารณา และค่าก่อน/หลังตามโดเมนที่เกี่ยวข้อง

---


# 4. Non-Functional Requirements

ข้อกำหนดในหัวข้อนี้ใช้กับทุกหน้าจอ API batch และ interface เว้นแต่ระบุเป็นอย่างอื่น ค่าใดที่ยังไม่มีตัวเลขอนุมัติ ต้องถูกติดตามเป็น OPEN item และห้ามสมมติเป็น production SLA


## 4.1 Operational quality

| Category | Requirement | Verification / evidence |
| --- | --- | --- |
| Performance | รองรับผู้ใช้พร้อมกันเฉลี่ย 80 คน สูงสุด 100 คน; interaction ปกติตอบภายใน 30 วินาที; API list/report ต้องกำหนด SLA แยกก่อน production | ผล load test ตาม workload ที่อนุมัติ พร้อม percentile, error rate และ resource usage |
| Availability | บริการ 7x24 ยกเว้น maintenance window; Batch Scheduler ต้อง resume/reconcile หลัง restart | restart/failover test และหลักฐาน reconcile งานที่ค้าง |
| Reliability | Transaction ที่สำเร็จต้อง durable; error ต้องไม่เขียนข้อมูลบางส่วน; file interface ต้อง reconcile row/file/tracking | failure injection, transaction rollback และ rerun/idempotency test |
| Backup/Recovery | กำหนด RPO/RTO, backup DB/config/object files และทดสอบ restore อย่างน้อยตามรอบองค์กร | restore drill พร้อมเวลาจริงและรายการข้อมูลที่ตรวจคืน |
| Observability | Metrics/log/trace สำหรับ API, batch, workflow, interface ACK, queue lag และ e-mail failure พร้อม alert threshold | monitoring dashboard, alert test และ correlation trace |


## 4.2 Security and product quality

| Category | Requirement | Verification / evidence |
| --- | --- | --- |
| Security | SSO/AD หรือ LDAP, JWT อายุจำกัด, refresh token revoke, least privilege, secrets vault, TLS, API key rotation และ server-side RBAC | security test, dependency/secret scan และหลักฐาน server-side authorization |
| Auditability | บันทึก login, document mutation, workflow action, master change, job action และ external callback พร้อม actor/time/correlation id | trace sample จาก request/run ไปยัง audit log และผลลัพธ์ปลายทาง |
| Usability | รองรับ Chrome รุ่นองค์กร, ภาษาไทย, keyboard focus, responsive table/modal และข้อความ validation ตรงตาม SRS | browser/responsive/keyboard test และ UAT ตามข้อความที่กำหนด |
| Maintainability | แยก FE/BE, OpenAPI 3.0 contract, configuration versioning, migration scripts และ automated tests สำหรับ business rules | contract validation, migration rehearsal และ automated test report |
| Portability | Deployment ต้องไม่ผูก credential/path กับเครื่อง; ใช้ environment/config/secret manager | deploy ด้วย environment ใหม่โดยไม่แก้ source code |


---


# 5. Acceptance and Traceability

การตรวจรับต้องยืนยันทั้งผลลัพธ์ทางธุรกิจ สิทธิ์ ความถูกต้องของข้อมูล และหลักฐานตรวจสอบย้อนหลัง รายการต่อไปนี้เป็นเกณฑ์สำคัญขั้นต่ำและต้องเชื่อมกับ test case/UAT evidence ในรอบส่งมอบ


## 5.1 High-priority acceptance criteria

- เอกสารหนึ่งรายการ trace ได้ครบ impact_process_id -> doc_no -> instance_id -> task_id
- กฎ threshold 100,000 บาทใช้กับชั้นอนุมัติถูกต้องทั้งค่าต่ำกว่า เท่ากับ และสูงกว่า
- หน้า Document Detail แสดง visible/editable/action options ตาม role profile ของผู้ใช้จริงและไม่มี role switcher ใน production
- ผลรวม % ชดเชย 100% ถูกตรวจทั้ง FE และ BE
- ร้านยอดขายไม่ครบ 60 วันถูก flag ใน inbox/report และมีเหตุผลตรวจสอบย้อนกลับ
- Jobs 1-10/8b รันซ้ำตาม runbook โดยไม่สร้างข้อมูลซ้ำหรือสูญหาย
- API capability 62 endpoints ใน scope ต้องผ่าน authorization, validation, audit, duplicate guard/idempotency, pagination และ error-contract test; Auth Group 1 เป็น platform service
- ข้อมูล export/import ทุก interface ผ่าน golden-file test เรื่อง encoding/date/delimiter/field count
- หน้าจอรายงานและ CSV Export to Batch ให้ผลตรงกันภายใต้ filter เดียวกัน

## 5.2 Traceability matrix

| ID | Requirement area | Scope coverage | SRS section |
| --- | --- | --- | --- |
| REQ-BUS-001/002 | Impact radius | กฎรัศมี 1 กม. กรุงเทพฯ/ปริมณฑล และ 2 กม. ต่างจังหวัด | 3.0, 3.1.2, Job 2 |
| REQ-BUS-003 | Gen Flow Gate | gate SQL และผล Y/W/N | 3.0, 3.1.2, Job 8b |
| REQ-BUS-004 | Abnormal sales | เกณฑ์ 60 วันและแถวผิดปกติ | 3.0, SCR-03/04/07 |
| REQ-BUS-005 | Allocation | ผลรวมเปอร์เซ็นต์ชดเชยเท่ากับ 100% | 3.0, SCR-06, Job 9 |
| REQ-BUS-006 | Approval threshold | routing ที่ 100,000 บาท | 3.0, 3.1.3, SCR-06 |
| REQ-DOC-001/002/003 | Document integrity | เลขเอกสาร duplicate guard และ data spine | 3.0, 3.2, SCR-02/06 |
| REQ-WFL-001/002/003 | Workflow integrity | ownership, audit และ optimistic concurrency | 3.0, 3.1.3, 3.2 |
| REQ-INT-001/002/003 | Interface reliability | durable file/outbox, ACK/purge และ typed FK | 3.0, 3.2.4, 3.3 |
| REQ-SEC-001/002 | Identity and secrets | platform identity, Secret Manager และ TLS | 1.5, 3.0, 4.2 |
| REQ-FIL-001 | Attachment | 5 MB, type/AV scan และ authorization | 3.0, SCR-06, 3.5 |
| REQ-RPT-001 | Report export | 19 columns และ preview/export reconciliation | 3.0, SCR-07 |
| REQ-OPS-001 | Batch rerun | idempotency และ run reconciliation | 3.0, 3.3 |
| REQ-SCR-001 | Committed screens | SCR-01..04 และ SCR-06..11 | 3.4 |
| SYS-API-001 | API capability | 62 endpoints / 10 groups | 3.5 |
| SYS-DAT-001 | Data model | 34 tables and integrity controls | 3.2 |
| SYS-NFR-001 | Observability | correlation/metrics/alert/audit evidence | 4 |
| FLOW-01 | Batch pipeline | ขั้นตอนนำเข้า คำนวณ สร้างเอกสาร ส่ง Statement และติดตาม ACK | 3.1, 3.3 |
| FLOW-02 | Approval workflow | Section 06 -> 08 -> 01 -> 02 และ Section 03 ตามวงเงิน | 3.1.1, 3.1.3 |
| DATA-01 | Logical data model | Data subjects, relationships, controls และ remediation | 3.2 |
| JOB-01 | Batch Job Console | 11 entry points, common controls และผลลัพธ์ที่ตรวจรับได้ | 3.3 |
| K2-01 | Overview / Dashboard | Dashboard | SCR-01 |
| K2-02 | Create Document | Create document | SCR-02 |
| K2-03 | Task Inbox | Task inbox | SCR-03 |
| K2-04 | Related Documents | Related documents | SCR-04 |
| K2-05 | Abnormal Assignment | Abnormal assignment | SCR-05 / OPEN |
| K2-06 | Document Detail | Document detail/action | SCR-06 |
| K2-07 | Status Report | Status report | SCR-07 |
| K2-08 | Operator Master | Operator master | SCR-08 |
| K2-09 | External Factor Master | External factor master | SCR-09 |
| K2-10 | RBAC Matrix | RBAC matrix | SCR-10 |
| K2-11 | Global Config | Global system configuration | SCR-11 |
| EMAIL-01 | Email Template | หน้าจอผู้ดูแล template และกฎ Notification Service | 3.4.13 |
| API-01 | REST API | Capability catalog 62 endpoints และข้อกำหนด contract กลาง | 3.5 |


---


# 6. Decisions and Open Items

หัวข้อนี้แยกมติที่ปิดแล้วออกจากประเด็นที่ยังเปิด เพื่อให้ทีมพัฒนาไม่ต้องอนุมานจากรายละเอียดเชิงออกแบบ รายการ CLOSED ถือเป็น baseline ของ SRS ฉบับนี้ ส่วน OPEN ยังห้ามนำไปพัฒนาเป็นข้อยุติโดยอัตโนมัติ


## 6.1 Closed decisions

| ID | Status | Effective date | Baseline decision |
| --- | --- | --- | --- |
| OPEN-01 | CLOSED | 22/07/2026 | เลขเอกสารใช้ปี พ.ศ. รูป YYYY/xxxxx และเก็บ be_year/running_no เพื่อ uniqueness; วันที่/เดือนใน API และฐานข้อมูลเชิงเวลาใช้ ISO-8601 ปี ค.ศ.; FE แปลงเป็น พ.ศ. เฉพาะการแสดงผล |
| OPEN-03 | CLOSED | 22/07/2026 | Job 8b ใช้ event/dependency trigger หลัง Job 8 สร้างเอกสารสำเร็จ ไม่ใช้เวลา wall-clock คงที่; Operations สั่ง manual rerun ตาม period ได้ โดยใช้ run lock และ idempotency key เดิม |


## 6.2 Open decisions required

รายการต่อไปนี้ยังไม่ถือเป็น requirement ที่อนุมัติ เมื่อได้ข้อยุติต้องบันทึกผล วันที่มีผล และปรับ baseline ก่อนพัฒนาส่วนที่เกี่ยวข้อง

| ID | Topic | Decision required | Impact if unresolved |
| --- | --- | --- | --- |
| OPEN-02 | Abnormal screen | ตัดสินใจ keep/drop หน้าจอและ API 2 เส้น พร้อมปรับ role 05 | ขอบเขต FE/BE, API และ UAT |
| OPEN-04 | NULL growth_rate | อนุมัติรอตรวจสอบแทน auto-accept หรือกำหนดกฎใหม่ | การคัดรายการและ workflow generation |
| OPEN-05 | Legacy date routing | ยืนยันเงื่อนไข routing สำหรับร้านก่อน/หลัง 1/10/2557 | routing และผลพิจารณา |
| OPEN-06 | NFR SLA/RPO/RTO | กำหนด SLA API/report/batch และ RPO/RTO production | capacity, HA, backup และ acceptance |
| OPEN-07 | File retention | กำหนด retention, encryption และ purge ของ attachment/interface/archive | storage, compliance และ recovery |
| OPEN-08 | Permission matrix | ยืนยัน menu/master/record permission ต่อ role | sidebar, API authorization และ UAT |


---


# 7. Appendices

ภาคผนวกรวบรวมคำย่อและหลักการระบุ requirement เพื่อให้ business, development และ test evidence ใช้ความหมายเดียวกัน


## 7.1 Definitions and abbreviations

| Term | Definition |
| --- | --- |
| SBPGI | Target integrated system for FGI/FCS processing and K2-style documents/workflow |
| SP / Store Partner | ร้าน Franchise ที่อยู่ในขอบเขตประกันรายได้ |
| FGI/FCS | Legacy batch domains for impact and QSSI data |
| K2 | Legacy BPM/workflow platform and original K2 SRS scope |
| STA | Statement/accounting interface system |
| IAS/MIS | Sales data interface |
| QSSI | Monthly score source |
| ALLMAP | Store/competitor/map source |
| Gen Flow Gate | ชุดเงื่อนไขก่อนสร้าง/เปิด workflow |


## 7.2 Requirement conventions

- REQ ใช้กับข้อกำหนดเชิงหน้าที่และกฎธุรกิจที่ต้องทดสอบได้
- SYS ใช้กับข้อกำหนดร่วมด้านสถาปัตยกรรม ข้อมูล ความปลอดภัย และการปฏิบัติการ
- PROTO ระบุข้อมูลหรือพฤติกรรมตัวอย่างที่ใช้ยืนยัน UX แต่ไม่ใช่ข้อมูล Production
- OPEN ระบุประเด็นที่ยังไม่อนุมัติและต้องไม่ถูกนำไปพัฒนาเป็นข้อยุติโดยอัตโนมัติ
- Acceptance evidence ต้องเชื่อมกลับมายัง section หรือ requirement area ในตาราง traceability