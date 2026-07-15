# SOFTWARE REQUIREMENT SPECIFICATION

## ระบบประกันรายได้ SBPGI

Version 3.2 Draft

> Generated from repository requirements and prototype screens. See source-of-truth and open-item sections.


# 1. SRS Overview


## 1.1 Purpose

เอกสารนี้กำหนดความต้องการของระบบประกันรายได้ SBPGI แบบรวม โดยสกัดจากต้นแบบหน้าจอ เอกสาร SRS K2 Version 3.1 เอกสาร Batch Job Technical Document Version 4.0 และเอกสารออกแบบ Flow/Database ที่อยู่ใน Repository เดียวกัน

ขอบเขตเนื้อหาจัดเรียงตามที่ร้องขอ: Flow, Database, Batch Job, หน้าจอ K2 ที่เหลือ และ API เพื่อใช้เป็นฐานร่วมสำหรับ Business, Developer, Tester, Operations และผู้อนุมัติการออกแบบ


## 1.2 Requirement classification

| Tag | ความหมาย | การใช้งาน |
| --- | --- | --- |
| REQ | ข้อกำหนดที่มีแหล่งอ้างอิงจาก SRS หรือเอกสาร Batch | ต้องพัฒนาและทดสอบตามข้อความที่กำหนด |
| DES | Target design ที่เพิ่มในหน้าจอ plan-flow / plan-database / plan-api / system-config / plan-email | ต้องผ่าน Architecture และ Business sign-off |
| PROTO | พฤติกรรมหรือข้อมูลตัวอย่างใน prototype | ใช้ยืนยัน UX ไม่ใช่ข้อมูล Production |
| OPEN | ประเด็นขัดแย้งหรือยังไม่ตัดสินใจ | ห้ามถือเป็นข้อยุติจนกว่าจะมีผู้อนุมัติ |


## 1.3 Source of truth

- REQ: RDM-SRS ประกันรายได้-K2 Version 3.1 เป็นแหล่งอ้างอิงหลักของหน้าจอและ workflow ฝั่ง K2
- REQ: FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0 เป็นแหล่งอ้างอิงหลักของ Jobs 1-10 และ Job 8b
- DES: เอกสาร workflow และหน้าจอ Flow เป็น Target flow ของระบบใหม่ที่รวม EAI และ K2 เข้า SBPGI
- DES: เอกสาร database และหน้าจอ Database เป็น Target schema 34 ตาราง
- DES: หน้าจอ API Specification เป็น REST API target 61 endpoints / 10 กลุ่ม
- DES: หน้าจอ Global Config และ Email Template เป็นหน้าจอเสริมสำหรับค่ากำหนดกลางและ Notification Service
- PROTO: Prototype ทุกหน้าจอและ shared shell ใช้ยืนยัน fields, actions, modal schema, labels และ navigation

# 2. Overall of System


## 2.1 Product perspective

ระบบประกันรายได้ใช้บริหารการชดเชยรายได้ของร้าน Store Partner ที่ได้รับผลกระทบจากร้านเปิดใหม่ โดยรับข้อมูลผลกระทบ ยอดขาย และคะแนน QSSI ประมวลผลเงื่อนไข สร้างเอกสาร เดิน workflow อนุมัติ และส่งผลชดเชยไปยังระบบบัญชี/Statement


## 2.2 Target architecture

| Layer | องค์ประกอบ | หน้าที่ |
| --- | --- | --- |
| Frontend | Web SPA จากต้นแบบหน้าจอ | Dashboard, K2 forms, report, batch monitor และ administration |
| Backend | Auth/RBAC, Document, Workflow, Batch Scheduler, Interface, Report/Notification | ให้บริการ REST API /api/v1 และ orchestration ภายใน |
| Database | Schema รวม Zone A/B/C | เก็บ pipeline, เอกสาร/workflow, master/config และ audit |
| External | QSSI, ALLMAP, IAS/MIS, STA, SAP, SMTP | คง file/SFTP/API ตามขอบเขตระบบภายนอก |

> DES: ระบบใหม่รวม EAI และ K2 engine เข้าเป็นส่วนหนึ่งของ SBPGI ไฟล์ BPM06001O/BPM06002O/BPM06003O และ K2 StartInstance เดิมถูกแทนด้วย DB write และ Workflow Engine ภายใน


## 2.3 User roles

| Code | Role | ขอบเขต |
| --- | --- | --- |
| 00 | Default | ผู้ดำเนินการในแบบฟอร์ม |
| 01 | Admin | เห็นทุกเมนูและจัดการข้อมูลทั้งหมด |
| 02 | HQ | HQ Support และงานบริหารข้อมูล |
| 03 | User Admin | ผู้ดูแลระบบระดับผู้ใช้งาน |
| 04 | Report Admin | รายงานและรายงานสรุป |
| 05 | Assign Job | แจกงานข้อมูลผิดปกติ |
| 06 | Report Admin Special | เรียกดูเอกสารทั้งหมด |
| 10 | UserViewer | อ่านเอกสารตามรายการที่ได้รับสิทธิ์ |


## 2.4 External interfaces

| System | Direction | Mechanism | Requirement |
| --- | --- | --- | --- |
| QSSI | Inbound | SFTP, mrs* 4 files | WINDOWS-874; คะแนน 6 หมวด 8,9,12,1,10,16 |
| ALLMAP | Inbound | SQL Server views / link | คู่ร้านถูกกระทบ ร้านคู่แข่ง และ POI map |
| IAS/MIS | Outbound/Inbound | AMS06001O / AMS06001I | ยอดขาย 4 windows x 15 days |
| STA | Outbound/Inbound | FRBC0001 + ACK/API callback | ส่งผลชดเชยและเฝ้าระวัง ACK |
| SAP | Downstream via STA | Accounting posting | รับรายการเมื่อ STA approve |
| SMTP | Outbound | E-mail | แจ้งผู้ดำเนินการ เตือนงานค้าง และ batch errors |


---


# 3. Specific Requirements


## 3.1 Flow Requirements

![รูปที่ 1: Flow FGI/FCS (Batch Pipeline) - ส่วนที่ 1/2](flow-fgi-01.png)

![รูปที่ 2: Flow FGI/FCS (Batch Pipeline) - ส่วนที่ 2/2](flow-fgi-02.png)

![รูปที่ 3: Flow K2 - Workflow อนุมัติ - ส่วนที่ 1/3](k2-flow-01.png)

![รูปที่ 4: Flow K2 - Workflow อนุมัติ - ส่วนที่ 2/3](k2-flow-02.png)

![รูปที่ 5: Flow K2 - Workflow อนุมัติ - ส่วนที่ 3/3](k2-flow-03.png)

![รูปที่ 6: Flow FGI/FCS + K2 - Target System - ส่วนที่ 1/3](plan-flow-01.png)

![รูปที่ 7: Flow FGI/FCS + K2 - Target System - ส่วนที่ 2/3](plan-flow-02.png)

![รูปที่ 8: Flow FGI/FCS + K2 - Target System - ส่วนที่ 3/3](plan-flow-03.png)


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
| C3 | GM/AVP อนุมัติ | Section 02; ยอด > 100,000 ผ่าน Section 03, ยอด <= 100,000 ข้ามไปบัญชี |
| C4 | บัญชีอนุมัติ | Section 04 และ 05 ตรวจและปิดเอกสาร |
| D1 | ส่ง Statement | Job 6 ส่ง FRBC0001 ไป STA เวลา 17:00 ทุกวัน |
| D2 | ติดตาม ACK | STA callback อัปเดต ACK และ Job 10 เป็น safety net เมื่อค้าง >= 1 วัน |


### 3.1.2 Gen Flow Gate

- workflow_generation_status ต้องเป็น W
- branch_type อยู่ใน FAM, FB1, FC1, FB2, FVB, FVC
- opt_dv_user_id ต้องไม่ว่าง
- นิติบุคคลของร้านเปิดใหม่ต้องต่างจากร้านถูกกระทบ
- growth_rate_diff ต้องน้อยกว่าหรือเท่ากับ -10
- sales_status ต้องเป็น Y หรือ N
- กรณี branch type ไม่เข้าเกณฑ์ให้สถานะ N; กรณีอื่นที่ยังไม่พร้อมให้คง W เพื่อแก้ไขและรันซ้ำ

### 3.1.3 Approval workflow

| Order | Section | Operator | Primary transition |
| --- | --- | --- | --- |
| 1 | 06 | ฝ่าย SBP DSA | ยุติ/หยุด หรือส่ง 08/01/04 |
| 2 | 08 | เจ้าหน้าที่ SBP DSA | คำนวณเสร็จส่ง 01 หรือส่งกลับ 06 |
| 3 | 01 | ฝ่ายส่งเสริมธุรกิจฯ | เห็นควรชดเชยส่ง 02; ไม่ชดเชยส่ง 06 |
| 4 | 02 | GM ส่งเสริมธุรกิจฯ | >100,000 ส่ง 03; <=100,000 ส่ง 04 |
| 5 | 03 | ผู้บริหารสำนักบริหาร SBP | เห็นควรชดเชยส่ง 04 หรือส่งกลับตามสิทธิ์ |
| 6 | 04 | ฝ่ายบัญชี SBP | ส่ง 05 หรือส่งกลับ 06 |
| 7 | 05 | บัญชีปฏิบัติการภาค | อนุมัติและปิด workflow |


### 3.1.4 Status and e-mail transition matrix

| State | Status/Operator | Before | Action | After | Next operator | TO |
| --- | --- | --- | --- | --- | --- | --- |
| - | สร้างเอกสาร | ผู้สร้างเอกสาร | - | - | - | - |
| 06 | ฝ่าย SBP DSA | รอฝ่าย SBP DSA ดำเนินการ | เห็นควรไม่ชดเชย | เสร็จสิ้นดำเนินการ | - | - |
| 06 | ฝ่าย SBP DSA | รอฝ่าย SBP DSA ดำเนินการ | หยุดชดเชยประกันรายได้ | เสร็จสิ้นดำเนินการ | - | - |
| 06 | ฝ่าย SBP DSA | รอฝ่าย SBP DSA ดำเนินการ | ฝ่ายส่งเสริมธุรกิจ SBP | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | ฝ่ายส่งเสริมธุรกิจ SBP | ฝ่ายส่งเสริมธุรกิจ SBP |
| 06 | ฝ่าย SBP DSA | รอฝ่าย SBP DSA ดำเนินการ | ฝ่ายบัญชี SBP ดำเนินการ | รอฝ่ายบัญชี SBP ดำเนินการ | ฝ่ายบัญชี SBP | ฝ่ายบัญชี SBP |
| 06 | ฝ่าย SBP DSA | รอฝ่าย SBP DSA ดำเนินการ | เจ้าหน้าที่ SBP DSA ดำเนินการ | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | เจ้าหน้าที่ SBP DSA | เจ้าหน้าที่ SBP DSA |
| 08 | เจ้าหน้าที่ SBP DSA | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | คำนวณเงินชดเชยเรียบร้อย | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | ฝ่ายส่งเสริมธุรกิจ SBP | ฝ่ายส่งเสริมธุรกิจ SBP |
| 08 | เจ้าหน้าที่ SBP DSA | รอเจ้าหน้าที่ SBP DSA ดำเนินการ | ฝ่าย SBP DSA ดำเนินการ | รอฝ่าย SBP DSA ดำเนินการ | ฝ่าย SBP DSA | ฝ่าย SBP DSA |
| 01 | ฝ่ายส่งเสริมธุรกิจ | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | เห็นควรชดเชย | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | GM ส่งเสริมธุรกิจ | GM ส่งเสริมธุรกิจ |
| 01 | ฝ่ายส่งเสริมธุรกิจ | รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ | เห็นควรไม่ชดเชย | รอฝ่าย SBP DSA ดำเนินการ | ฝ่าย SBP DSA | ฝ่าย SBP DSA |
| 02 | GM ส่งเสริมธุรกิจ | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | เห็นควรชดเชย (>100,000) | รอผู้บริหารสำนักบริหาร SBP ดำเนินการ | ผู้บริหารสำนักบริหาร SBP | ผู้บริหารสำนักบริหาร SBP |
| 02 | GM ส่งเสริมธุรกิจ | รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ | เห็นควรชดเชย (<=100,000) | รอฝ่ายบัญชี SBP ดำเนินการ | ฝ่ายบัญชี SBP | ฝ่ายบัญชี SBP |
| 03 | ผู้บริหารสำนักบริหาร SBP | รอผู้บริหารสำนักบริหาร SBP ดำเนินการ | เห็นควรชดเชย | รอฝ่ายบัญชี SBP ดำเนินการ | ฝ่ายบัญชี SBP | ฝ่ายบัญชี SBP |
| 04 | ฝ่ายบัญชี SBP | รอฝ่ายบัญชี SBP ดำเนินการ | บัญชีปฏิบัติการภาคดำเนินการ | รอบัญชีปฏิบัติการภาคดำเนินการ | บัญชีปฏิบัติการภาค | บัญชีปฏิบัติการภาค |
| 05 | บัญชีปฏิบัติการภาค | รอบัญชีปฏิบัติการภาคดำเนินการ | บัญชีภาคอนุมัติ | เสร็จสิ้นดำเนินการ | - | - |


### 3.1.5 Migration map

| Connection | Legacy | Target | Source |
| --- | --- | --- | --- |
| ส่งข้อมูลชดเชย/ร้านใหม่/คู่แข่ง เข้าระบบเอกสาร | ไฟล์ BPM06001O (48 ฟิลด์) / BPM06002O / BPM06003O ผ่าน SFTP ไป BPM (Jobs 7, 8, 9) | Document Service เขียน DB ตรง (compensation_documents / document_new_stores / document_competitors) - ตัดไฟล์และ SFTP ภายในทิ้ง | FGI/FCS -> K2 |
| เปิด Workflow | Job 8b ยิง K2 REST StartInstance (HTTP + Basic Auth hardcoded - ความเสี่ยง P0) | Workflow Engine ภายใน · POST /workflows/instances · เกณฑ์ Gen Flow Gate คงเดิมทุกข้อ | FGI/FCS -> K2 |
| รับ ACK ผลประมวลจาก STA | รอ STA อัปเดต return_code ใน tracking · Job 10 ตรวจทุกเช้า | เพิ่ม POST /interfaces/sta/ack (API key) · Job 10 คงไว้เป็น safety net | FGI/FCS ใหม่ |
| ตาราง tracking interface | FGI_CONFIRM_RECEIVE_DATA - transaction_key เป็น polymorphic FK + บั๊ก purge (E20) | interface_transactions - typed FK ต่อประเภทข้อมูล + งาน purge ทำงานจริง | FGI/FCS ใหม่ |
| อีเมลแจ้งเตือน | แต่ละ job ต่อ SMTP เอง · encoding TIS-620 · ผู้รับ hardcoded บางจุด (template 34) | Notification Service กลาง · UTF-8 · ผู้รับตาม status_email_rules + config ต่อ job | ทั้งสอง |
| Interface ภายนอก QSSI / ALLMAP / IAS / STA | SFTP + ไฟล์ตาม encoding เฉพาะ (WINDOWS-874 / UTF-8 / พ.ศ.) | คงเดิม (ระบบของทีมอื่น) - ย้าย credential ไป Secret Manager + บังคับ known_hosts | FGI/FCS |
| สิทธิ์ผู้ใช้และเมนู | ตารางสิทธิ์ 8 role ในเอกสาร SRS (จัดการในระบบ BPM เดิม) | Auth & RBAC + JWT · menu_permissions ต่อ role · จัดการผ่านหน้าสิทธิ์การเข้าถึงเมนู | K2 · 3.1.1 |


### 3.1.6 Flow controls

- รายการที่ข้อมูลยอดขายไม่ครบ 60 วันต้องแสดงเป็นข้อมูลผิดปกติและแถวสีแดง
- ระบบต้องกันเปิด workflow ซ้ำต่อ impact process/document
- งานเตือนรายสัปดาห์ทำงานวันจันทร์ 10:00 และ escalation งานค้าง 30/45/60 วันต้องอ่านค่าจาก config
- การเปลี่ยนกฎธุรกิจ เช่น -10, 50, 60 วัน และ 100,000 บาท ต้องผ่าน Business sign-off
- ทุก transition ต้องบันทึก consideration_logs, ผู้กระทำ, เวลา, สถานะก่อน/หลัง และ correlation id
![รูปที่ 9: Approve Flow เดิม ใช้ประกอบการเทียบพฤติกรรม](Flow ประกันรายได้.png)


---


## 3.2 Database Requirements

![รูปที่ 10: Database FGI/FCS - ส่วนที่ 1/3](fgi-database-01.png)

![รูปที่ 11: Database FGI/FCS - ส่วนที่ 2/3](fgi-database-02.png)

![รูปที่ 12: Database FGI/FCS - ส่วนที่ 3/3](fgi-database-03.png)

![รูปที่ 13: Database K2 - ส่วนที่ 1/4](k2-database-01.png)

![รูปที่ 14: Database K2 - ส่วนที่ 2/4](k2-database-02.png)

![รูปที่ 15: Database K2 - ส่วนที่ 3/4](k2-database-03.png)

![รูปที่ 16: Database K2 - ส่วนที่ 4/4](k2-database-04.png)

![รูปที่ 17: Database FGI/FCS + K2 - Target Schema - ส่วนที่ 1/3](plan-database-01.png)

![รูปที่ 18: Database FGI/FCS + K2 - Target Schema - ส่วนที่ 2/3](plan-database-02.png)

![รูปที่ 19: Database FGI/FCS + K2 - Target Schema - ส่วนที่ 3/3](plan-database-03.png)


### 3.2.1 Data architecture

Target database เป็น schema รวม 34 ตาราง แบ่งเป็น Zone A: FGI/FCS impact pipeline, Zone B: K2 documents/workflow และ Zone C: shared master/config/audit โดยใช้ชื่อ table/column แบบ English lower_snake_case

| Order | Core key | Purpose |
| --- | --- | --- |
| 1 | impact_process_id | Hub ของหนึ่งร้านถูกกระทบและหนึ่งงวด |
| 2 | doc_no | เลขเอกสาร YYYY/xxxxx |
| 3 | instance_id | Workflow instance ต่อเอกสาร |
| 4 | task_id | งานต่อ Section/assignee |
| 5 | employee_id / role_code | ผู้ใช้ สิทธิ์ และผู้ปฏิบัติงาน |


### 3.2.2 Data dictionary overview

| Table | Zone | Source | PK | FK / Relation | Purpose |
| --- | --- | --- | --- | --- | --- |
| Zone A · FGI/FCS - Impact Pipeline และ External Interfaces |  |  |  |  |  |
| fgi_impact_stores | A | FGI/FCS | id | impact_process_id -> fgi_impact_processes · impacted_store_code -> impacted_stores | คู่ร้านกระทบ-เปิดใหม่ · verify_status (W/P/Y/N) · workflow_generation_status (W/Y/N) |
| fgi_impact_processes | A | FGI/FCS | id | impacted_store_code · แม่ของตารางรายรอบทั้งหมด | hub รอบชดเชย · action_status (Y/W/N) · last_compensation_amount |
| fgi_impact_sales_summaries | A | FGI/FCS | id | impact_process_id -> fgi_impact_processes · -> sales_transactions (1:N) | หัวยอดขาย · growth_rate_diff · total_working_days (เกณฑ์ 60 วัน) |
| sales_transactions | A | FGI/FCS | id | sales_summary_id -> fgi_impact_sales_summaries | ยอดขายรายวันจาก IAS · sales_diff/outlier >= 50 แบบจับคู่ |
| fgi_impact_competitors | A | FGI/FCS | id | impact_process_id -> fgi_impact_processes · -> document_competitors (นำเข้า) | คู่แข่งจาก ALLMAP (data_source=ALM) · งวดล่าสุดต่อร้าน |
| fcs_qssi_scores | A | FGI/FCS | id | UK: store_id + category_code + งวด | คะแนน QSSI 6 หมวด (8,9,12,1,10,16) จาก Job 1 |
| interface_transactions | A | ใหม่ | id | typed FK: impact_process_id / sales_summary_id / doc_no | แทน FGI_CONFIRM_RECEIVE_DATA - เลิก polymorphic PK + purge ทำงานจริง (แก้ E20) |
| Zone B · K2 - เอกสารประกันรายได้และ Workflow ภายใน |  |  |  |  |  |
| compensation_documents | B | K2 | doc_no (YYYY/xxxxx) | status_code · current_section_code · impacted_store_code · impact_process_id (ใหม่) | เอกสารประกันรายได้ - หัวใจโซน B · FK ใหม่เชื่อม hub โซน A แทนไฟล์ 48 ฟิลด์ |
| document_new_stores | B | K2 | id | doc_no -> compensation_documents | ร้านเปิดใหม่ · distance_km · %ชดเชย (ผลรวมต้อง 100%) |
| document_competitors | B | K2 | id | doc_no · competitor_code -> competitors | คู่แข่งในเอกสาร · source_system ALM/USER |
| document_external_factors | B | K2 | id | doc_no · factor_code -> external_factors | ปัจจัยภายนอกที่ใช้ในเอกสาร + ช่วงวันที่ |
| consideration_logs | B | K2 | id | doc_no -> compensation_documents | ประวัติพิจารณา (ผู้พิจารณา · Section · ผล · เวลา) · result_category (APPROVE/REJECT/PENDING) สำหรับ filter อนุมัติ/ไม่อนุมัติ หน้ารายงาน |
| document_attachments | B | K2 | id | doc_no -> compensation_documents | ไฟล์แนบ <= 5MB ต่อไฟล์ · Section ที่แนบ |
| compensation_histories | B | K2 | id | store_code · ref_doc_no | ประวัติชดเชยต่อร้าน/รอบ · เดือนส่งบัญชี (ผูกไฟล์ FRBC0001 ของ Job 6) |
| workflow_instances | B | ใหม่ | instance_id | doc_no -> compensation_documents | instance workflow ภายใน (แทน K2 engine) · สถานะแทน workflow_generation_status=Y |
| workflow_tasks | B | ใหม่ | task_id | instance_id · section_code · assignee_employee_id | งานค้างต่อ Section - แหล่งข้อมูลหน้างานรอดำเนินการ (inbox) |
| Zone C · Shared - Master, RBAC, Configuration และ Audit |  |  |  |  |  |
| stores | C | FGI/FCS | store_code | <- impacted_stores (subset SP) · <- document_new_stores.new_store_code | master สาขา 7-Eleven ทุกประเภท (SP / เปิดใหม่ / ปิด renovate) - แหล่งค้นหาร้านของหน้า k2-create (API /stores/search) |
| impacted_stores | C | K2 | store_code | = impacted_store_code ของโซน A (สะพานหลักสองระบบ) · subset SP ของ stores | ข้อมูลร้าน SP master |
| workflow_sections / document_statuses | C | K2 | section_code / status_code | อ้างโดย compensation_documents · workflow_tasks · status_email_rules | ขั้นตอน 06/08/01/02/03/04/05 · สถานะเอกสาร |
| roles / menus / menu_permissions | C | K2 · 3.1.1 | role_code / menu_code (composite) | menu_permissions = composite PK | สิทธิ์เมนู 8 role (00-10) - แหล่งข้อมูล RBAC ของ Auth · CRUD ผ่านหน้าจอ 3.1.1 (API /roles /menus /menu-permissions) · is_system กันลบ role/เมนูหลัก · menus มี menu_group (MAIN/MASTER) + sort_order · ประวัติลง audit_logs |
| operator_assignments | C | K2 · 3.1.8 | id | section_code · zone_code · employee_id -> employees | ผู้ปฏิบัติงานต่อ section_code/zone_code · เลือกชื่อผ่าน popup ค้นหาพนักงาน |
| employees | C | FGI/FCS | employee_id | <- user_accounts.employee_id · <- operator_assignments (เลือกผ่าน popup) | master พนักงานองค์กร (HR) - batch join อยู่แล้ว · ป้อน popup ค้นหาพนักงาน (API /employees/search) หน้า 3.1.8 |
| external_factors | C | K2 · 3.1.9 | factor_code | <- document_external_factors | ปัจจัยภายนอก master · รหัสห้ามซ้ำ |
| competitors | C | K2 | competitor_code | <- document_competitors | ร้านคู่แข่ง 24 ราย |
| audit_logs | C | K2 | id | table_name + ref_key (generic) | ประวัติแก้ไข master แบบหลายรายการ: action · old_value -> new_value · เหตุผล · ผู้แก้ · เวลา (= MaintainMasterHistory เดิม) |
| status_email_rules | C | K2 · 3.1.5 | status_code | to_section_code · cc_section_code -> workflow_sections | ผู้รับอีเมลเมื่อเปลี่ยนสถานะ - ใช้โดย Notification Service |
| email_templates | C | ใหม่ | template_code (EM-01-08) | อ่านคู่กับ status_email_rules โดย Notification Service | เนื้อหา 8 email template (subject/body + ตัวแปร merge) แก้ได้จากหน้า Email Template · From/To/Cc ล็อกตาม status_email_rules · ประวัติแก้ไข/รีเซ็ต -> audit_logs · ถ้อยคำเป็น beyond SRS (SRS กำหนดเฉพาะผู้รับ/จังหวะส่ง) |
| user_accounts | C | ใหม่ | employee_id | role_code -> roles | บัญชีผู้ใช้สำหรับ JWT (เดิมพึ่งระบบ BPM) |
| job_configs | C | ใหม่ | job_no | <- job_run_histories | cron + พารามิเตอร์ที่แก้ได้ของ 11 jobs (หน้า Batch Monitor) |
| job_run_histories | C | ใหม่ | run_id | job_no -> job_configs | ประวัติรันต่อรอบ (เวลา · แถว · ไฟล์ · ผล) - เดิมอยู่ใน log ไฟล์ |
| system_configs | C | ใหม่ | config_key | อ่านโดยทุก service · ประวัติแก้ไข -> audit_logs | Global config แบบ key-value (หน้า Global Config) · category (IMPACT/WORKFLOW/DOCUMENT/AUTH/NOTIFICATION/BATCH) · value_type (NUMBER/STRING/BOOLEAN/JSON/CRON) · is_editable กันแก้ค่าคงที่ทางธุรกิจ (ข้อ 8.2) · ห้ามเก็บ secret (อยู่ Secret Manager) · cache 5 นาที + invalidate เมื่อแก้ไข |


### 3.2.3 Detailed entities - FGI/FCS


#### fgi_impact_processes (FGI/FCS · Hub)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| impacted_store_code | varchar(5) | รหัสร้านคง leading zero |
| impact_month · impact_year | smallint | UK ต่อร้านและงวด |
| action_status | char(1) | Y / W / N |
| last_compensation_amount | decimal(14,2) | ยอดล่าสุดของรอบ |
| created_at · updated_at | timestamp | UTC ใน DB |


#### fgi_impact_stores (Job 2 / 8b)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| impact_process_id | bigint | FK |
| impacted_store_code · new_store_code | varchar(5) | Business key |
| branch_type | varchar(3) | FAM / FB1 / FC1 / FB2 / FVB / FVC |
| verify_status | char(1) | W / P / Y / N |
| workflow_generation_status | char(1) | W / Y / N |
| opt_dv_user_id | varchar(30) | Gen Flow Gate |


#### fgi_impact_sales_summaries (Jobs 4-5)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| impact_process_id | bigint | FK |
| total_working_days | smallint | ผิดปกติเมื่อ < 60 วัน |
| growth_rate_diff | decimal(9,4) | Gen Flow Gate <= -10 |
| sales_status | char(1) | Y / N |
| calculated_at | timestamp | ผลคำนวณ Job 5 |


#### sales_transactions (IAS / Job 5)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| sales_summary_id | bigint | FK |
| sales_date | date | UK ต่อ summary |
| sales_amount | decimal(14,2) | ยอดขายรายวัน |
| sales_diff | decimal(9,4) | จับคู่ 4 x 15 วัน |
| is_outlier | boolean | \|sales_diff\| >= 50 |


#### fgi_impact_competitors (ALLMAP / Job 3)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| impact_process_id | bigint | FK |
| competitor_code · competitor_name | varchar | ข้อมูลจาก ALLMAP |
| open_date | date | วันที่เปิดกระทบ |
| distance_meters | decimal(10,2) | หน่วยมาตรฐานเป็นเมตร |
| data_source | varchar(10) | ALM |


#### fcs_qssi_scores (QSSI / Job 1)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| store_id · category_code | varchar | UK ต่องวด |
| impact_month · impact_year | smallint | งวดเดือนก่อนหน้า |
| score_value | decimal(9,4) | หมวด 8, 9, 12, 1, 10, 16 |
| source_file_name | varchar(255) | Traceability |
| imported_at | timestamp | เวลานำเข้า |


#### interface_transactions (ใหม่)

| Column | Type | Key / Rule |
| --- | --- | --- |
| id | bigint | PK |
| data_name · direction | varchar | Enum / INBOUND-OUTBOUND |
| impact_process_id | bigint | FK nullable |
| sales_summary_id | bigint | FK nullable |
| doc_no | varchar(10) | FK เมื่อเชื่อม K2 |
| return_code | varchar(20) | ACK จากปลายทาง |
| sent_at · received_at | timestamp | Monitoring / watchdog |

> ใช้ typed FK แทน FGI_CONFIRM_RECEIVE_DATA.transaction_key แบบ polymorphic เพื่อรักษา leading zero และ enforce referential integrity


### 3.2.4 Detailed entities - K2 / Workflow


#### operator_assignments (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | int | PK |
| employee_name_en | varchar(150) |  |
| employee_email | varchar(120) |  |
| section_code | varchar(2) | FK |
| zone_code | varchar(3) |  |


#### external_factors (SRS)

| Column | Type | Key |
| --- | --- | --- |
| factor_code | varchar(10) | PK |
| factor_name | varchar(150) |  |
| factor_remark | varchar(255) |  |


#### audit_logs (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| table_name | varchar(60) |  |
| ref_key | varchar(60) |  |
| action_type | varchar(10) |  |
| old_value · new_value | text |  |
| reason | varchar(255) |  |
| updated_by · updated_at | varchar · datetime |  |


#### competitors (ออกแบบ)

| Column | Type | Key |
| --- | --- | --- |
| competitor_code | varchar(10) | PK |
| competitor_name | varchar(100) |  |

> 24 ร้านตาม Master ในเอกสาร (108 Shop, Lotus Express, CJ Express ... Thai Shop)


#### workflow_sections / document_statuses (SRS)

| Column | Type | Key |
| --- | --- | --- |
| section_code / status_code | varchar(2) | PK |
| section_name / status_name | varchar(80) |  |

> Section: 06/08/01/02/03/04/05 · Status 8 ค่า: "รอ<ผู้ดำเนินการ>ดำเนินการ" ของ 7 section + "เสร็จสิ้นดำเนินการ" (ตารางเส้นทางดู workflow.md)


#### roles / menus (SRS)

| Column | Type | Key |
| --- | --- | --- |
| role_code / menu_code | varchar(4) | PK |
| role_name / menu_name | varchar(80) |  |
| role_desc | varchar(200) |  |
| menu_group (MAIN/MASTER) | varchar(10) |  |
| sort_order | int |  |
| is_system | bit |  |

> Role 00-10 ตามตารางสิทธิ์ (3.1.1) · เพิ่ม/แก้/ลบผ่านหน้าจอ 3.1.1 - is_system กัน role/เมนูหลักถูกลบ · ประวัติลง audit_logs


#### compensation_documents (ออกแบบ)

| Column | Type | Key |
| --- | --- | --- |
| doc_no | varchar(10) | PK |
| document_round · compensation_round · impact_month | int · int · varchar(7) |  |
| status_code | varchar(2) | FK |
| current_section_code | varchar(2) | FK |
| impacted_store_code | varchar(5) | FK |
| impact_process_id | bigint | FK FGI/FCS |
| compensation_amount | decimal(12,2) |  |
| sales_drop_percent | decimal(5,2) |  |
| created_at | datetime |  |


#### impacted_stores (SRS)

| Column | Type | Key |
| --- | --- | --- |
| store_code | varchar(5) | PK |
| store_name · zone_code | varchar · varchar(3) |  |
| store_type · owner_name | varchar |  |
| juristic_name | varchar(150) |  |
| transfer_date | date |  |


#### document_new_stores (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| doc_no | varchar(10) | FK |
| store_code · store_type | varchar |  |
| owner_name · juristic_name | varchar |  |
| open_date · close_date | date |  |
| distance_km | decimal(5,2) |  |
| compensation_percent | decimal(5,2) |  |
| compensation_amount | decimal(12,2) |  |


#### document_competitors (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| doc_no | varchar(10) | FK |
| competitor_code | varchar(10) | FK |
| open_date · remark | date · varchar |  |
| source_system (ALM/USER) | varchar(10) |  |


#### document_external_factors (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| doc_no | varchar(10) | FK |
| factor_code | varchar(10) | FK |
| start_date · end_date | date |  |
| remark | varchar(255) |  |


#### consideration_logs (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| doc_no | varchar(10) | FK |
| reviewer_name · section_code | varchar |  |
| result · detail | varchar |  |
| action_at | datetime |  |


#### compensation_histories (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| store_code | varchar(5) | FK |
| compensation_round · impact_month | int · varchar(7) |  |
| compensation_amount | decimal(12,2) |  |
| submit_account_month | varchar(7) |  |
| status_code · result | varchar |  |
| ref_doc_no | varchar(10) | FK |


#### document_attachments (SRS)

| Column | Type | Key |
| --- | --- | --- |
| id | bigint | PK |
| doc_no | varchar(10) | FK |
| file_name · section_code | varchar |  |
| created_by_name · remark | varchar |  |
| created_at | datetime |  |


#### workflow_instances (ระบบใหม่)

| Column | Type | Key |
| --- | --- | --- |
| instance_id | bigint | PK |
| doc_no | varchar(10) | FK |
| instance_status | varchar(20) | RUNNING / COMPLETED / STOPPED |
| started_at · completed_at | timestamp |  |
| lock_version | int | Optimistic locking |


#### workflow_tasks (ระบบใหม่)

| Column | Type | Key |
| --- | --- | --- |
| task_id | bigint | PK |
| instance_id | bigint | FK |
| section_code | varchar(2) | FK |
| assignee_employee_id | varchar(30) | FK |
| task_status | varchar(20) | OPEN / COMPLETED / CANCELLED |
| opened_at · completed_at | timestamp |  |


#### user_accounts (ระบบใหม่)

| Column | Type | Key |
| --- | --- | --- |
| employee_id | varchar(30) | PK |
| role_code | varchar(4) | FK |
| section_code · zone_code | varchar | FK |
| is_active | boolean | Default true |
| last_login_at | timestamp |  |


#### status_email_rules (SRS 3.1.5)

| Column | Type | Key |
| --- | --- | --- |
| status_code | varchar(2) | PK FK |
| to_section_code | varchar(2) | FK |
| cc_section_code | varchar(2) | FK |

> กำหนดผู้รับอีเมล (TO/CC) เมื่อเปลี่ยนสถานะ


#### menu_permissions (SRS 3.1.1)

| Column | Type | Key |
| --- | --- | --- |
| role_code | varchar(4) | PK FK |
| menu_code | varchar(4) | PK FK |
| can_access | bit |  |

> สิทธิ์เมนูต่อ Role (Composite PK) · แก้จากหน้าจอ 3.1.1 (PUT /api/v1/menu-permissions) · เพิ่ม role/เมนูใหม่ = สร้างแถว can_access=false ทุกช่อง · ลบ role/เมนู = cascade


### 3.2.5 Constraints and controls

- Store code ต้องเก็บเป็น varchar(5) เพื่อรักษา leading zero
- doc_no ต้อง unique และรูปแบบ YYYY/xxxxx; running แยกต่อปี
- document_new_stores.compensation_percent รวมต่อเอกสารต้องเท่ากับ 100%
- ใช้ foreign key จริงระหว่าง compensation_documents.impact_process_id และ fgi_impact_processes.id
- system_configs เป็นแหล่งค่ากำหนดกลางแบบ key-value; ค่าธุรกิจที่ is_editable=false แก้ผ่าน UI/API ไม่ได้
- email_templates เก็บเฉพาะ subject/body และตัวแปร merge; ผู้รับ From/To/Cc ต้องอ้าง status_email_rules
- ใช้ enum/check constraint สำหรับ W/P/Y/N, Y/W/N, I/C/A/N/S/Z และ task status
- ใช้ optimistic locking กับเอกสาร/workflow ที่มีการแก้พร้อมกัน
- ทุก master mutation ต้องบันทึก audit_logs ค่าเดิม ค่าใหม่ เหตุผล ผู้แก้ และเวลา
- Timestamp ภายใน DB ใช้ UTC; UI แสดง Asia/Bangkok และปี พ.ศ. ตามข้อยุติด้าน format

### 3.2.6 Required remediation

| Priority | Issue | Target requirement |
| --- | --- | --- |
| P0 | Job 4 transaction | ใช้ transaction/outbox ไม่ให้ W->P commit ก่อนสร้างไฟล์สำเร็จ |
| P0 | Secrets/TLS | ย้าย credential ไป Secret Manager และบังคับ TLS |
| P0 | Tracking purge | แก้ SQL purge data_name และทำ migration/test |
| P1 | Polymorphic FK | ใช้ typed FK ใน interface_transactions |
| P1 | NULL growth rate | ส่งรอตรวจสอบแทน auto-accept; ต้องมี Business sign-off |
| P1 | Master joins | รายงาน reject/reconcile แทนการทำแถวหายเงียบ |
| P1 | Golden files | ทดสอบ encoding วันที่ พ.ศ. delimiter และ field count ทุก interface |


---


## 3.3 Batch Job Requirements

![รูปที่ 20: Batch Job Console - Job 1 Detail - ส่วนที่ 1/3](job-batch-01.png)

![รูปที่ 21: Batch Job Console - Job 1 Detail - ส่วนที่ 2/3](job-batch-02.png)

![รูปที่ 22: Batch Job Console - Job 1 Detail - ส่วนที่ 3/3](job-batch-03.png)


### 3.3.1 Batch console

หน้า Batch Job Console สำหรับ Admin แสดง pipeline A-E, รายการ 11 entry points, สถานะรอบล่าสุด/ถัดไป, เปิดปิดงาน, พารามิเตอร์, manual run, flow, database และ run history

| Job | Name | Thai name | Phase | Schedule | Output |
| --- | --- | --- | --- | --- | --- |
| 1 | ImportQSSI | นำเข้าคะแนน QSSI รายเดือน | A | Monthly (รายเดือน (ต้นเดือน)) | fcs_qssi_scores |
| 2 | ImportImpactStore | นำเข้าคู่ร้านถูกกระทบจาก ALLMAP | A | 0 07 7 * * (ทุกวันที่ 7 เวลา 07:00) | fgi_impact_stores |
| 3 | ImportImpactCompetitor | นำเข้าร้านคู่แข่งจาก ALLMAP | A | 0 07 7 * * (ทุกวันที่ 7 เวลา 07:00) | fgi_impact_competitors |
| 4 | PrepareImpactStoreToIAS | เตรียมและส่งคำขอยอดขายไป IAS | B | 0 16 7-16 * * (วันที่ 7-16 เวลา 16:00) | AMS06001O (UTF-8) |
| 5 | ImportImpactSaleFromIAS | รับยอดขายจาก IAS + คำนวณ Growth | B | 30 16 7-16 * * (วันที่ 7-16 เวลา 16:30) | AMS06001I (รับเข้า) |
| 6 | ExportImpactStoreToFS | ซิงก์สถานะ + ส่งค่าชดเชยไป STA | D | 0 17 * * * (ทุกวัน 17:00) | FRBC0001 (windows-874) |
| 7 | ExportCompetitor | ส่งข้อมูลคู่แข่งไป BPM | C | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | BPM06003O (UTF-8) |
| 8 | ExportImpactStoreFlowToBPM | ส่งข้อมูลชดเชยไป BPM (ไฟล์อย่างเดียว) | C | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | BPM06001O (UTF-8, 48 ฟิลด์) |
| 8b | StartK2WorkFlow | เปิด K2 Workflow (FIA) | D | แยกอิสระ (ยืนยันรอบกับ Operations) | K2 StartInstance (REST) |
| 9 | ExportOpenStore | ส่งข้อมูลร้านเปิดใหม่ไป BPM | C | 30 17 7-31 * * (วันที่ 7-31 เวลา 17:30) | BPM06002O (UTF-8, 24 ฟิลด์) |
| 10 | NotifyNoReceiveData | Watchdog เฝ้าระวัง ACK ค้าง | E | 0 07 * * * (ทุกวัน 07:00) | อีเมลเตือน (TIS-620) |


### 3.3.2 Common controls

- สิทธิ์จัดการ Batch Job เป็น Admin 01 เท่านั้น
- Manual run ต้องระบุงวดข้อมูลและสร้าง run_id; API ตอบ 202 Accepted
- ห้ามรัน job เดียวกันซ้อน และต้องป้องกัน shared temp resource ของ Job 1
- แก้ไขได้เฉพาะ parameter ที่ระบุ editable; business constants ต้องถูก lock
- ทุกการเปิด/ปิด แก้ parameter และ manual run ต้องบันทึก audit
- run history ต้องเก็บ start/end, status, row count, file, error, correlation id และผู้สั่งรัน
- การ re-run ต้องปฏิบัติตาม runbook ของแต่ละ job โดยตรวจ DB, tracking, backup และปลายทางก่อน

### 3.3.J1 Job 1 - นำเข้าคะแนน QSSI รายเดือน

| Item | Detail |
| --- | --- |
| Main class | fcs.main.ImportQSSI |
| Script | FCS_ImportQSSI.sh |
| Schedule | Monthly - รายเดือน (ต้นเดือน) |
| Phase / Type | A / IMPORT |
| Output | fcs_qssi_scores |
| Purpose | ดาวน์โหลดไฟล์คะแนน QSSI 4 ไฟล์ต่อเดือนผ่าน SFTP โหลดเข้าตารางพัก ทำ dedup และจับคู่หมวดคะแนนแบบ stateful แล้วลบงวดเดิมและ insert ลง fcs_qssi_scores เพื่อให้ Job 6 ใช้ตรวจความครบของคะแนน 6 หมวดก่อนปล่อยสถานะ INIT |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | Monthly | Editable | ตั้งเวลาใน crontab ผ่านสคริปต์ FCS_ImportQSSI.sh |
| งวดข้อมูล (เดือนที่รัน) | 07/2569 | Editable | ชื่อไฟล์ใช้เดือนปัจจุบัน แต่งวดใน DB คือเดือนก่อนหน้า (off-by-one โดยตั้งใจ - Errata E10) |
| SFTP Server | sezfssa02-office.cpall.co.th | Editable |  |
| SFTP Port | 218 | Editable | พอร์ตไม่มาตรฐาน - ที่มาของ retry / type-mismatch (Errata E11) |
| Remote Directory | /export/qssishare/onl/qssi/textfile/SBP/QSSI_Monthly/ | Editable |  |
| Local Directory | /appshare/SPS/FCS/interface_data/in/ | Editable |  |
| File Prefix (4 ไฟล์) | mrs1trnf_, mrs2trnf_, mrs3trnf_, mrs5trnf_ | Fixed |  |
| Encoding | WINDOWS-874 | Fixed |  |
| Batch Insert Size | 10000 | Editable | จำนวนแถวต่อรอบ insert |


#### Processing flow

1. เริ่ม
1. กำหนดงวด: ชื่อไฟล์ = เดือนปัจจุบัน / งวด DB = เดือนก่อนหน้า - off-by-one โดยตั้งใจตามเอกสาร (Errata E10)
1. เชื่อมต่อ SFTP พอร์ต 218 ดาวน์โหลดไฟล์ทั้ง 4 prefix - mrs1trnf_, mrs2trnf_, mrs3trnf_, mrs5trnf_ (WINDOWS-874)
1. ดาวน์โหลดสำเร็จ และไฟล์ถูกต้อง? - ถ้าล้มเหลวจะไม่วนซ้ำอัตโนมัติ เพราะไฟล์ถูกย้ายเข้า backup เสมอ | No: FAIL - ไม่มี auto-retry ข้ามไปขั้นย้ายไฟล์เข้า backup
1. เปิด transaction ต่อไฟล์ โหลดลง staging data - TransactionTemplate + savepoint ต่อไฟล์
1. Dedup + จับคู่หมวดแบบ stateful (RS1 / RS2 / RS3 / RS5) - RS1 เรียงตามลำดับ: D+E, F+G+H, I+J, K+L และ H ออกหมวด 16 เพิ่ม
1. ลบงวด/หมวดเดิม แล้ว batch insert ลง fcs_qssi_scores - insert ครั้งละ 10,000 แถว แล้ว commit ต่อไฟล์
1. ย้ายไฟล์ต้นทางเข้า backup เสมอ (ทั้งสำเร็จและล้มเหลว) - เหตุผลที่ห้ามหวังผล auto-retry - ต้องนำไฟล์กลับมาเองก่อนรันซ้ำ
1. กรณี exception: rollback ถึง savepoint + ส่งเมลแจ้งล้มเหลว - ไฟล์ต้นทางยังถูกย้ายเข้า backup ตามปกติ
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fcs_qssi_scores | W | ตารางคะแนนปลายทาง (ลบงวด/หมวดเดิมแล้ว insert ใหม่) โดยผ่านการ staging ข้อมูล |

| Operational control | Requirement |
| --- | --- |
| Transaction | ต่อไฟล์ (TransactionTemplate + savepoint) |
| Re-run | ไฟล์ถูกย้าย backup แม้ล้มเหลว - ก่อนรันซ้ำต้องนำไฟล์กลับ ตรวจงวดปลายทาง และตารางพัก |
| Mail routing | storeretention (Cc ว่าง) |
| Known risk | convertStrToDouble แปลงพลาดกลายเป็น 0.0 เงียบ ๆ / ห้ามรันพร้อมกัน (temp table ใช้ร่วมทั้งระบบ) |


### 3.3.J2 Job 2 - นำเข้าคู่ร้านถูกกระทบจาก ALLMAP

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ImportImpactStore |
| Script | FGI_ImportImpactStore.sh |
| Schedule | 0 07 7 * * - ทุกวันที่ 7 เวลา 07:00 |
| Phase / Type | A / IMPORT + RULES |
| Output | fgi_impact_stores |
| Purpose | นำคู่ร้านถูกกระทบ-ร้านเปิดใหม่จากวิว ALLMAP เข้า fgi_impact_stores เติมข้อมูลจากตาราง master แล้วใช้กฎ DENY และ ON_PROCESS ตั้งค่า verify_status เป็น W / N / P |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 0 07 7 * * | Editable | ทุกวันที่ 7 ของเดือน เวลา 07:00 |
| Argument (ขอบเขต\|งวด) | ALL\|2569\|06 | Editable | รูปแบบ ZONES\|YYYY\|MM หรือ ALL\|YYYY\|MM - ไม่ระบุจะใช้งวดตาม modifyDateToString |
| Source View | allmapssa.SEVEN_IMPACT_VIEW (SQL Server GSMALLMAP) | Fixed | dedup ด้วย ROW_NUMBER |
| Branch Type ที่เข้าเกณฑ์ | B, FAM, FB1, FB2, FC1, FVB, FVC, FPT1 | Fixed | FPT1 เข้าเกณฑ์เฉพาะเมื่อ SBP_CANCEL_TYPE_I = 06 |
| กฎ DENY (ตรวจก่อน ON_PROCESS) | สาขา N=F / juristic เดียวกัน / สัญญาไม่คลุมงวด / เก่ากว่า 12 เดือน | Fixed |  |
| PK Sequence | SEQ_fgi_impact_stores | Fixed |  |


#### Processing flow

1. เริ่ม
1. อ่าน SEVEN_IMPACT_VIEW จาก ALLMAP (ROW_NUMBER dedup) - เชื่อม SQL Server GSMALLMAP ด้วย user allmapssa
1. มีข้อมูลต้นทาง? | No: จบการทำงาน
1. เป็นคู่ร้านใหม่ (ยังไม่มีใน Oracle)? - Errata E4: รันซ้ำจะไม่อัปเดตคู่เดิม | No: ข้ามรายการ - ของเดิมไม่ถูกอัปเดต (updateList เป็น dead code)
1. insert คู่ใหม่ verify_status = W, created_by = ALM - PK จาก SEQ_fgi_impact_stores
1. เติมข้อมูล master และ enrichment data - INNER JOIN - ถ้า master ไม่ครบ แถวจะหลุดหายเงียบ ๆ
1. ผ่านกฎ DENY? (ตรวจก่อน ON_PROCESS) - DENY: สาขา N=F / juristic เดียวกัน / สัญญา SBP ไม่คลุมงวด / เก่ากว่า 12 เดือน | No: verify_status = N (Deny)
1. เข้าเงื่อนไข ON_PROCESS หรือ created_by = STA? - แหล่ง STA เข้าสถานะ P ได้อัตโนมัติ | No: คงค่า W (รอตรวจสอบ)
1. verify_status = P (On Process) แล้ววนจนครบทุกแถว
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | W | insert คู่ใหม่ / ตั้ง verify_status W-N-P / created_by=ALM รวมทั้งข้อมูล external |

| Operational control | Requirement |
| --- | --- |
| Transaction | หนึ่ง transaction + savepoint |
| Re-run | คู่เดิมถูกข้าม - รันซ้ำไม่อัปเดตของเดิม ต้องลบ/แก้คู่ที่ต้องการอย่างจงใจก่อน |
| Mail routing | go-sbp (hardcoded, template 34) |
| Known risk | E4: updateList เป็น dead code / INNER JOIN ทำแถวที่ master ไม่ครบหายเงียบ (P1) |


### 3.3.J3 Job 3 - นำเข้าร้านคู่แข่งจาก ALLMAP

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ImportImpactCompetitor |
| Script | (ยืนยันสคริปต์กับ Ops) |
| Schedule | 0 07 7 * * - ทุกวันที่ 7 เวลา 07:00 |
| Phase / Type | A / IMPORT |
| Output | fgi_impact_competitors |
| Purpose | นำข้อมูลร้านคู่แข่งรายงวดจากวิว COMPETITOR_IMPACT_VIEW เข้า fgi_impact_competitors ทีละ 10,000 แถว กันซ้ำระดับงวด (ถ้างวดมีข้อมูลแล้วจะข้ามทั้งงวด ไม่มี upsert) |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 0 07 7 * * | Editable | สคริปต์ scheduler จริงต้องยืนยันกับ Operations |
| Argument (งวด) | 2569\|06 | Editable | รูปแบบ YYYY\|MM |
| Chunk Size | 10000 | Editable | จำนวนแถวต่อรอบ insert |
| Source View | COMPETITOR_IMPACT_VIEW | Fixed | SELECT DISTINCT / map คอลัมน์ NAMT -> NAME_TH, BRANCHT -> BRANCH_TH |


#### Processing flow

1. เริ่ม
1. เป็นงวดใหม่ (ยังไม่เคยนำเข้า)? - กันซ้ำระดับงวด (Errata E15) | No: ข้ามทั้งงวด - ไม่มี upsert ต้องลบงวดก่อนจึงนำเข้าใหม่ได้
1. SELECT DISTINCT จาก COMPETITOR_IMPACT_VIEW
1. พบข้อมูลต้นทาง? | No: จบการทำงาน
1. insert ทีละ 10,000 แถว พร้อม data_source = ALM - map คอลัมน์ NAMT -> NAME_TH และ BRANCHT -> BRANCH_TH
1. จำนวนที่ insert = จำนวนต้นทาง? - ตรวจ reconcile จำนวนแถวก่อน commit | No: Rollback + ส่งเมลแจ้งล้มเหลว
1. Commit / จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_competitors | W | insert รายงวด data_source=ALM (งวดล่าสุดต่อร้าน) ดึงจาก ALLMAP |

| Operational control | Requirement |
| --- | --- |
| Transaction | หนึ่ง transaction + savepoint (insert เป็น chunk ละ 10,000) |
| Re-run | ต้องลบข้อมูลงวดเองก่อน re-import แล้วตรวจจำนวนแถวเทียบต้นทาง |
| Mail routing | config mailTo / storeretention |
| Known risk | กันซ้ำระดับงวดเท่านั้น - ไม่ใช่ upsert (E15) |


### 3.3.J4 Job 4 - เตรียมและส่งคำขอยอดขายไป IAS

| Item | Detail |
| --- | --- |
| Main class | fgi.main.PrepareImpactStoreToIAS |
| Script | FGI_ExportImpactStoreToAMS.sh |
| Schedule | 0 16 7-16 * * - วันที่ 7-16 เวลา 16:00 |
| Phase / Type | B / PREPARE + EXPORT |
| Output | AMS06001O (UTF-8) |
| Purpose | สร้างข้อมูลตั้งต้น fgi_impact_sales_summaries จากคู่ร้านสถานะ P (ALM) พลิกธง W -> P แบบ auto-commit แล้วเขียนไฟล์คำขอ AMS06001O ส่งให้ IAS/MIS คำนวณยอดขาย - เป็น Job เดียวที่ไม่มี transaction (ความเสี่ยง P0) |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 0 16 7-16 * * | Editable | ทุกวันที่ 7-16 ของเดือน เวลา 16:00 |
| เงื่อนไขอายุร้านถูกกระทบ | OPENDATE_I <= OPENDATE_N − 12 เดือน 15 วัน | Fixed | เกณฑ์ธุรกิจ - เปลี่ยนต้องอนุมัติ |
| เงื่อนไขวันปัจจุบัน | SYSDATE > OPENDATE_N + 16 วัน | Fixed |  |
| Output File | AMS06001O_yyyyMMddHHmm.txt (UTF-8, 1 logical record) | Fixed | COPY ไป backup - ไฟล์จริงคงไว้ให้ Job 5 |
| ปลายทาง | IAS / MIS | Editable |  |


#### Processing flow

1. เริ่ม
1. seed fgi_impact_sales_summaries จากคู่ร้านสถานะ P / ALM - ตัดรายการที่มี process (fgi_impact_processes) active ออก
1. เข้าเงื่อนไขวันที่? (12 เดือน 15 วัน และ +16 วัน) - OPENDATE_I <= OPENDATE_N−12ด.15ว. และ SYSDATE > OPENDATE_N+16ว. | No: จบการทำงาน
1. อัปเดต SALES W -> P แบบ AUTO-COMMIT ก่อนเขียนไฟล์ - ไม่มี transaction - rollback ไม่ได้ (ความเสี่ยง P0 หลักของระบบ)
1. เขียนไฟล์ AMS06001O (UTF-8) แล้ว COPY ไป backup - ไฟล์จริงคงไว้ที่เดิมเพื่อให้ Job 5 อ่านตอบกลับ
1. เขียนไฟล์สำเร็จ? | No: DB เป็น P แล้วแต่ไฟล์พัง - ต้อง reconcile ธง/ไฟล์/tracking ด้วยมือ
1. insert tracking data_name = IMPACT_STORE_SALES - transaction_pk = parseInt(impacted_store_code) - เลขศูนย์นำหน้าหาย / return code และ receive date เป็น NULL
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_sales_summaries | W | seed หัวตารางยอดขาย + พลิกธง W -> P (auto-commit) |
| fgi_impact_stores | R | แหล่ง seed (สถานะ P / created_by=ALM) |
| fgi_impact_processes | R | กรองรายการที่มี process ค้างอยู่ออก |
| interface_transactions | W | tracking: data_name=IMPACT_STORE_SALES · typed FK = sales_summary_id / impact_process_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | ไม่มี transaction - auto-commit (เสี่ยง DB/ไฟล์ไม่ตรงกันสูงสุดในระบบ, P0) |
| Re-run | ก่อนรันซ้ำต้อง reconcile ธง SALES + ไฟล์จริง + backup + tracking ด้วยมือทุกครั้ง |
| Mail routing | go-sbp (ผ่าน shared helper) |
| Known risk | P0: commit W->P เกิดก่อนเขียนไฟล์ - แนะนำ transactional outbox ในระบบใหม่ |


### 3.3.J5 Job 5 - รับยอดขายจาก IAS + คำนวณ Growth

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ImportImpactSaleFromIAS |
| Script | FGI_ImportImpactStoreSale.sh |
| Schedule | 30 16 7-16 * * - วันที่ 7-16 เวลา 16:30 |
| Phase / Type | B / IMPORT + CALC |
| Output | AMS06001I (รับเข้า) |
| Purpose | อ่านไฟล์ตอบกลับยอดขาย AMS06001I จาก IAS บันทึกยอดขายรายวันลง sales_transactions คำนวณ sales_diff และ outlier ในหน้าต่าง 4 ช่วง x 15 วันรอบวันเปิดร้านใหม่ แล้วตัดสิน verify_status = Y / N จาก growth_rate_diff |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 30 16 7-16 * * | Editable | 30 นาทีหลัง Job 4 |
| Input File | AMS06001I_yyyyMMddHHmm.txt (WINDOWS-874, 4 ฟิลด์) | Fixed | impacted_store_code \| OPENDATE_N \| SALES_DATE \| SALES_AMOUNT |
| หน้าต่างคำนวณ | 4 ช่วง x 15 วัน รอบ OPENDATE_N (ไม่รวมวันเปิด) | Fixed |  |
| เกณฑ์ Outlier | \|sales_diff\| >= 50 | Fixed | literal ในโค้ด - เปลี่ยนต้องอนุมัติธุรกิจ (8.2) |
| วันทำการคาดหวัง | 60 | Fixed | ถ้าไม่เท่า 60 -> pre-accept เป็น Y ทันที |
| กฎ Pre-accept | อายุร้าน < 12 เดือน 15 วัน หรือวันทำการ != 60 -> Y | Fixed |  |


#### Processing flow

1. เริ่ม
1. อ่านไฟล์ WINDOWS-874 จัดกลุ่มตามร้าน + วันเปิด
1. เป็นงวดที่ยังไม่นำเข้า? | No: จบ (idempotency guard กันนำเข้าซ้ำ)
1. เปิด transaction ต่อไฟล์ แล้ว insert sales_transactions แถวดิบ - ระวัง: catch ใน DAO บางจุดอาจทำให้ rollback ไม่ทำงาน
1. total_working_days = จำนวนแถวดิบทั้งหมด - นับรวมแถวนอกหน้าต่างคำนวณด้วย (raw count)
1. ต้องคำนวณ sales_diff? (ไม่เข้าเงื่อนไข pre-accept) - pre-accept เมื่ออายุร้าน < 12ด.15ว. หรือวันทำการ != 60 | No: Pre-accept: verify_status = Y ทันที
1. คำนวณ sales_diff รายวัน + outlier แบบจับคู่ (|sales_diff| >= 50) - 4 หน้าต่าง x 15 วัน ไม่รวมวันเปิดร้านใหม่ / ธงรวมอดีต-ปัจจุบันต้องตรงกัน
1. NVL(growth_rate_diff, −1) < 0 ? - NULL ถูกแทนด้วย −1 = accept อัตโนมัติ (ความเสี่ยง P1) | No: verify_status = N (ไม่เข้าเกณฑ์ชดเชย)
1. verify_status = Y แล้ว insert tracking IMPORT_SALES_FROM_IAS
1. ย้ายไฟล์เข้า backup
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| sales_transactions | W | ยอดขายรายวันดิบจากไฟล์ (4 หน้าต่างเวลา) |
| fgi_impact_sales_summaries | R/W | อัปเดต total_working_days, growth_rate_diff, verify_status Y/N |
| interface_transactions | W | tracking: data_name=IMPORT_SALES_FROM_IAS · typed FK = sales_summary_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | ต่อไฟล์ + savepoint (ระวัง inner catch ทำให้ rollback ไม่ทำงาน) |
| Re-run | มี period guard - ถ้าจะซ้ำต้องลบ/แก้ sales_transactions อย่างระวังและคำนวณหัวตารางใหม่ |
| Mail routing | go-sbp (ผ่าน shared helper) |
| Known risk | P1: growth_rate_diff = NULL ถูก accept อัตโนมัติ / ต้องทดสอบ ก.พ. ปีอธิกสุรทิน และร้านไม่มียอดขาย |


### 3.3.J6 Job 6 - ซิงก์สถานะ + ส่งค่าชดเชยไป STA

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ExportImpactStoreToFS |
| Script | FGI_ExportImpactStoreToSTA.sh |
| Schedule | 0 17 * * * - ทุกวัน 17:00 |
| Phase / Type | D / STATE SYNC + EXPORT |
| Output | FRBC0001 (windows-874) |
| Purpose | รัน 10 mutation ตามลำดับบนตารางสถานะ ตรวจความครบของคะแนน QSSI 6 หมวด สร้างชุดสถานะที่ส่งออกได้ แล้วเขียนไฟล์ FRBC0001 (14 ฟิลด์ ปี พ.ศ.) ส่งให้ระบบ Statement (STA) ภายใน transaction เดียว |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 0 17 * * * | Editable | ทุกวัน 17:00 |
| dateStartInitToSTA | 7 | Editable | วันของเดือนที่เริ่มปล่อยสถานะ I, C |
| numWaitPay | 3 | Editable | จำนวนงวดรอจ่าย |
| หมวด QSSI ที่ตรวจ | 8, 9, 12, 1, 10, 16 | Fixed | ต้องครบทั้ง 6 หมวดจากงวด max เดียว ในกรอบ 3 เดือน |
| Output File | FRBC0001_yyyyMMddHHmmss.txt (windows-874, 14 ฟิลด์, พ.ศ.) | Fixed | ฟิลด์ 3/5/6 เป็นวันที่แบบไทย/พุทธศักราช |
| ปลายทาง SFTP | sestabr01.cpall.co.th (STA) | Editable |  |


#### Processing flow

1. เริ่ม
1. รัน 10 mutation ตามลำดับ บน fgi_impact_processes และ fgi_impact_stores - state sync ก่อน export - ตรวจครบทั้ง 10 ขั้นตอน post-run
1. QSSI ครบ 6 หมวด? (งวด max เดียว ในกรอบ 3 เดือน) - หมวด 8, 9, 12, 1, 10, 16 จาก fcs_qssi_scores (Job 1) | No: ข้ามเส้นทาง INIT - สาย APPROVE ยังไปต่อ
1. สร้างชุดสถานะส่งออก: A, N, S (+ I, C เมื่อวันที่ >= 7 และ QSSI ครบ + Z ค้าง) - Z จะถูกแปลงเป็น S เฉพาะในไฟล์ - ใน DB ยังเป็น Z
1. มีแถวส่งออก? | No: จบการทำงาน
1. เขียนไฟล์ FRBC0001 14 ฟิลด์ (windows-874 + พ.ศ.) - วันที่ผิดตัวเดียวทำให้ mapData คืน null และยกเลิกทั้งไฟล์
1. insert tracking: I,C -> COMPENSATE_INIT_I/N · A,N,S,Z -> COMPENSATE_APPROVE_I/N
1. SFTP ไฟล์ไป STA
1. SFTP สำเร็จ? - transaction เดียวคลุม sync + ไฟล์ + tracking + SFTP | No: Rollback ทั้ง transaction + ลบไฟล์
1. ย้ายไฟล์เข้า backup
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_processes | R/W | หนึ่งใน 10 mutation (สถานะ process / last_compensation_amount) |
| fgi_impact_stores | R/W | สถานะค่าชดเชย I/C/A/N/S/Z และข้อมูลร้าน/ผู้อนุมัติ/ค่าชดเชยร้านใหม่ |
| fcs_qssi_scores | R | ตรวจความครบคะแนน 6 หมวด (จาก Job 1) |
| interface_transactions | W | tracking COMPENSATE_INIT / APPROVE (I,N) · typed FK = impact_process_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | หนึ่ง transaction คลุม sync + ไฟล์ + tracking + SFTP |
| Re-run | transaction ป้องกันตามปกติ แต่ต้อง reconcile 10 mutation และระวังการ overwrite ไฟล์ปลายทางก่อนยืนยันผล |
| Mail routing | storeretention + mailToBPM เมื่อสร้างไฟล์ |
| Known risk | บั๊กจริง E20: SQL purge ต่อ data_name สองค่าเป็น string เดียว - tracking ไม่เคยถูกลบ สะสมโตขึ้นเรื่อย ๆ |


### 3.3.J7 Job 7 - ส่งข้อมูลคู่แข่งไป BPM

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ExportCompetitor |
| Script | FGI_ExportCompetitorToBPM.sh |
| Schedule | 30 17 7-31 * * - วันที่ 7-31 เวลา 17:30 |
| Phase / Type | C / EXPORT BPM |
| Output | BPM06003O (UTF-8) |
| Purpose | เลือกงวดคู่แข่งล่าสุดต่อร้านที่อยู่ใน process ALM ที่ active และมี forecast เริ่มต้น เขียนไฟล์ BPM06003O 14 ฟิลด์ แล้ว SFTP ไปเส้นทาง competition ของ BPM |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 30 17 7-31 * * | Editable | ทุกวันที่ 7-31 เวลา 17:30 |
| ปลายทาง SFTP | BPM (path competition) | Editable |  |
| Output File | BPM06003O_yyyyMMddHHmm.txt (UTF-8, 14 ฟิลด์) | Fixed | create_by = "system" (literal) |
| เงื่อนไขเลือกข้อมูล | งวดคู่แข่งล่าสุดต่อร้าน (dense rank) + forecast เริ่มต้น + ยังไม่ส่ง | Fixed | เดือน/ปีในไฟล์มาจาก fgi_impact_processes last_compensation_amount ไม่ใช่งวดคู่แข่ง |


#### Processing flow

1. เริ่ม
1. query คู่แข่งงวดล่าสุดต่อร้าน + forecast เริ่มต้น + ยังไม่ส่ง - dense rank ตามงวดต้นทางของคู่แข่ง
1. ข้อมูลผู้จัดการ SBP ครบ? (checkProcesssError) | No: ตัดแถวทิ้งเงียบ ๆ - ไม่มีการแจ้งเตือน
1. มีแถวเหลือส่งออก? | No: จบการทำงาน
1. เขียนไฟล์ BPM06003O 14 ฟิลด์ (UTF-8) - เดือน/ปี export มาจาก fgi_impact_processes last_compensation_amount period
1. insert tracking data_name = IMPACT_COMPETITOR, receive_date = now
1. SFTP ไป BPM (เส้นทาง competition)
1. SFTP สำเร็จ? | No: Rollback + ลบไฟล์
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_competitors | R | งวดคู่แข่งล่าสุดต่อร้าน (จาก Job 3) |
| fgi_impact_processes | R | กรอง process ALM ที่ active / งวด export จาก last_compensation_amount |
| interface_transactions | W | tracking: data_name=IMPACT_COMPETITOR · typed FK = impact_process_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | หนึ่ง transaction + savepoint |
| Re-run | tracking กันส่งซ้ำ - ตรวจ backup + tracking + ไฟล์ปลายทางก่อนรันซ้ำ |
| Mail routing | storeretention + mailToBPM เมื่อสร้างไฟล์ |
| Known risk | แถวที่ข้อมูลผู้จัดการ SBP ไม่ครบถูกตัดทิ้งเงียบ ๆ - ควรมี metric นับ |


### 3.3.J8 Job 8 - ส่งข้อมูลชดเชยไป BPM (ไฟล์อย่างเดียว)

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ExportImpactStoreFlowToBPM |
| Script | FGI_ExportImpactStoreToBPM.sh |
| Schedule | 30 17 7-31 * * - วันที่ 7-31 เวลา 17:30 |
| Phase / Type | C / EXPORT BPM |
| Output | BPM06001O (UTF-8, 48 ฟิลด์) |
| Purpose | ส่งออกข้อมูล impact profile ค่าชดเชย และผู้อนุมัติ SBP เป็นไฟล์ BPM06001O (48 ฟิลด์) ไปยัง BPM - ทำหน้าที่ SFTP อย่างเดียว ห้ามมี logic เรียก K2 เด็ดขาด (การเปิด workflow เป็นของ Job 8b เท่านั้น) |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 30 17 7-31 * * | Editable | ทุกวันที่ 7-31 เวลา 17:30 |
| ปลายทาง SFTP | BPM/FGI/Inbound/compensateflow/ | Editable |  |
| Output File | BPM06001O_yyyyMMddHHmm.txt (UTF-8, 48 ฟิลด์) | Fixed | growth_rate_diff = NULL เมื่อ data_source = STA |
| เงื่อนไขเลือกข้อมูล | สถานะ I + forecast + ยังไม่ส่ง | Fixed | ไม่มี Gen Flow Gate ในเงื่อนไข - gate อยู่ที่ Job 8b |
| ข้อห้ามเชิงสถาปัตยกรรม | ห้ามมี K2 StartInstance ใน Job นี้ | Fixed | Separation of Concerns - ความเสี่ยง P0 ถ้ารวมกัน |


#### Processing flow

1. เริ่ม
1. updateSeqToBpm ใน transaction แยก (commit อิสระ) - กำหนดเลข seq สำหรับ BPM - ไม่ถูก rollback แม้หลักล้มเหลว
1. เติมข้อมูลผู้อนุมัติ SBP
1. query impact profile สถานะ I + forecast + ยังไม่ส่ง - ชื่อบุคคลประกอบเป็น ชื่อ + เว้นวรรค + นามสกุล
1. ข้อมูลผู้อนุมัติครบ? (checkProcesssError) | No: ตัดแถวทิ้งเงียบ ๆ
1. มีแถวเหลือส่งออก? | No: จบการทำงาน
1. เขียนไฟล์ BPM06001O 48 ฟิลด์ (UTF-8) - growth_rate_diff = NULL เมื่อแหล่งข้อมูลเป็น STA
1. insert tracking data_name = IMPACT_STORE, return_code = W - transaction_pk = id / Job 8b จะอ่านสถานะ W ต่อ
1. SFTP ไป compensateflow
1. SFTP สำเร็จ? | No: Rollback tracking + ลบไฟล์ (transaction แยกของ seq ไม่ถูก rollback)
1. จบ - ไม่เรียก K2 (เป็นหน้าที่ Job 8b)

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | R | impact profile สถานะ I + forecast (key = id) พร้อมข้อมูลผู้อนุมัติ SBP |
| interface_transactions | W | tracking: data_name=IMPACT_STORE, return_code=W · typed FK = impact_process_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | สอง transaction - กำหนดเลข seq แยกจาก transaction หลัก |
| Re-run | tracking กันซ้ำ - ตรวจ backup + tracking + ไฟล์ปลายทางก่อนรันซ้ำ |
| Mail routing | storeretention + mailToBPM เมื่อสร้างไฟล์ |
| Known risk | P0: ห้ามรวม Job 8 กับ 8b - การกู้คืนไฟล์ export กับการเปิด workflow ต้องแยกจากกันเสมอ |


### 3.3.J8b Job 8b - เปิด K2 Workflow (FIA)

| Item | Detail |
| --- | --- |
| Main class | fgi.main.StartK2WorkFlow |
| Script | (scheduler แยก - ยืนยันกับ Ops) |
| Schedule | แยกอิสระ - ยืนยันรอบกับ Operations |
| Phase / Type | D / K2 REST |
| Output | K2 StartInstance (REST) |
| Purpose | Job เดียวในระบบที่เรียก K2 workflow engine - คัดรายการที่ผ่าน Gen Flow Gate จากสถานะ workflow_generation_status = W แล้วยิง REST StartInstance เปิด workflow FIA และ reconcile สถานะ W / Y / N พร้อมส่งอีเมลสรุปราย DV |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| Scheduler | แยกจาก Job 8 - ยืนยันเจ้าของรอบกับ Operations | Editable | ตั้งใจแยกเพื่อกู้คืนอิสระจากไฟล์ export |
| K2 REST Endpoint | sesomapua01.7eleven.cp.co.th:81 (HTTP) | Editable | เป้าหมาย: ย้ายเป็น HTTPS + Secret Manager (P0) |
| Basic Auth User | 7ELEVEN\bpmk2_fcs | Editable | ปัจจุบัน hardcoded ในโค้ด - ความเสี่ยง P0 |
| เกณฑ์ Growth Rate | growth_rate_diff <= −10 | Fixed | literal ในโค้ด - เปลี่ยนต้องอนุมัติธุรกิจ |
| Branch Type ผ่าน Gate | FAM, FB1, FC1, FB2, FVB, FVC | Fixed | นอกเซ็ตนี้ถูกตั้ง N ทันที |
| เงื่อนไข Gate อื่น | workflow_generation_status=W · opt_dv_user_id ไม่ว่าง · new_store_juristic_name != impacted_store_juristic_name · sales_status ∈ {Y, N} | Fixed |  |


#### Processing flow

1. เริ่ม
1. updateBeforeSelect: ตั้ง W -> Y เมื่อพบ K2 process เดิมอยู่แล้ว - กันเปิด workflow ซ้ำ
1. ผ่าน Gen Flow Gate ครบทุกเงื่อนไข? - W + branch type + DV ไม่ว่าง + juristic ต่างกัน + growth <= −10 + sales status Y/N | No: branch type นอกเซ็ต -> N / กรณีอื่นคง W ไว้
1. POST K2 REST StartInstance (HTTP + Basic Auth) - endpoint sesomapua01.7eleven.cp.co.th:81
1. HTTP 200 และ body มีคำว่า "Running"? | No: log ล้มเหลว คงค่า W ไว้ reconcile - ไม่มี auto-retry
1. workflow_generation_status = Y (เปิด workflow สำเร็จ) - flag เขียนแบบ auto-commit - ไม่มี transaction
1. ส่งอีเมลสรุปราย DV (group ตาม opt_dv_user_id)
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | R/W | อ่าน candidate workflow_generation_status=W + เขียนสถานะ W -> Y / N |
| K2 process instance | R | ตรวจว่ามี workflow ของร้านนี้อยู่แล้วหรือไม่ (กันซ้ำ) |

| Operational control | Requirement |
| --- | --- |
| Transaction | ไม่มี transaction - flag เขียนแบบ auto-commit |
| Re-run | ห้าม reset workflow_generation_status จนกว่าจะตรวจแล้วว่า K2 instance มีจริงหรือไม่ |
| Mail routing | อีเมลราย DV / GM user |
| Known risk | P0: credential hardcoded + endpoint เป็น HTTP / เฝ้า metric: จำนวน candidate, HTTP "Running", start ล้มเหลว, นับ W/Y/N |


### 3.3.J9 Job 9 - ส่งข้อมูลร้านเปิดใหม่ไป BPM

| Item | Detail |
| --- | --- |
| Main class | fgi.main.ExportOpenStore |
| Script | FGI_Exportdocument_new_storesToBPM.sh |
| Schedule | 30 17 7-31 * * - วันที่ 7-31 เวลา 17:30 |
| Phase / Type | C / EXPORT BPM |
| Output | BPM06002O (UTF-8, 24 ฟิลด์) |
| Purpose | ส่งออกโปรไฟล์ร้านเปิดใหม่พร้อมค่า forecast เป็นไฟล์ BPM06002O (24 ฟิลด์) ไปยัง BPM โดยใช้กฎ NVL(adjust_n, forecast_n) - ค่า adjust มีลำดับความสำคัญเหนือ forecast |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 30 17 7-31 * * | Editable | ทุกวันที่ 7-31 เวลา 17:30 |
| ปลายทาง SFTP | BPM/FGI/Inbound/impactprofile/ | Editable |  |
| Output File | BPM06002O_yyyyMMddHHmm.txt (UTF-8, 24 ฟิลด์) | Fixed | ฟิลด์ 19-20 เว้นว่างโดยตั้งใจ / distance_unit ถูก select แต่ไม่ส่งออก |
| กฎ Forecast / Percent | NVL(adjust_n, forecast_n) | Fixed | ค่า adjust มาก่อน forecast เสมอ |
| เงื่อนไขเลือกข้อมูล | ร้านเปิดใหม่ สถานะ I + forecast + ยังไม่ส่ง | Fixed |  |


#### Processing flow

1. เริ่ม
1. query ร้านเปิดใหม่ สถานะ I + forecast + ยังไม่ส่ง
1. มีแถวส่งออก? | No: จบการทำงาน
1. เขียนไฟล์ BPM06002O 24 ฟิลด์ (UTF-8) - Forecast/Percent = NVL(adjust_n, forecast_n) / ฟิลด์ 19-20 ว่างโดยตั้งใจ
1. insert tracking data_name = NEW_STORE
1. SFTP ไป impactprofile
1. SFTP สำเร็จ? - หนึ่ง transaction + savepoint คุ้มครอง DB กับไฟล์ให้สอดคล้องกัน | No: Rollback transaction + ลบไฟล์
1. ย้ายไฟล์เข้า backup
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | R | โปรไฟล์ร้านเปิดใหม่ สถานะ I (คอลัมน์ adjust_n, forecast_n, distance_unit) และค่า forecast/adjust รายงวด |
| interface_transactions | W | tracking: data_name=NEW_STORE · typed FK = doc_no / impact_process_id |

| Operational control | Requirement |
| --- | --- |
| Transaction | หนึ่ง transaction - rollback + ลบไฟล์เมื่อ SFTP ล้มเหลว |
| Re-run | tracking กันซ้ำ - ตรวจ backup + tracking + ไฟล์ปลายทางก่อนรันซ้ำ |
| Mail routing | storeretention + mailToBPM เมื่อสร้างไฟล์ |
| Known risk | ฟิลด์ 19-20 ว่างโดยตั้งใจ - อย่าตีความว่าเป็นบั๊กตอน re-implement |


### 3.3.J10 Job 10 - Watchdog เฝ้าระวัง ACK ค้าง

| Item | Detail |
| --- | --- |
| Main class | fgi.main.NotifyNoReceiveData |
| Script | FGI_NotifyNoReceiveData.sh |
| Schedule | 0 07 * * * - ทุกวัน 07:00 |
| Phase / Type | E / WATCHDOG |
| Output | อีเมลเตือน (TIS-620) |
| Purpose | งานอ่านอย่างเดียว - ตรวจตาราง tracking หา dataset ค่าชดเชยฝั่ง STA ที่ยังไม่ได้รับ ACK เกิน 1 วัน แล้วส่งอีเมลเตือนผู้ดูแลระบบ ไม่สร้างไฟล์และไม่เขียนฐานข้อมูลใด ๆ |


#### Parameters

| Parameter | Value / Example | Mode | Note |
| --- | --- | --- | --- |
| กำหนดการรัน (Cron) | 0 07 * * * | Editable | ทุกวัน 07:00 |
| data_name ที่เฝ้าดู | COMPENSATE_INIT_I, COMPENSATE_APPROVE_I | Fixed | เฉพาะฝั่ง STA - ไม่เฝ้า dataset ของ BPM |
| เกณฑ์ค้าง | return_code IS NULL และ INTERFACE_TYPE != WS และ CREATE_DATE <= SYSDATE − 1 | Fixed | เกณฑ์อายุ 1 วันเป็น literal - candidate พารามิเตอร์ในระบบใหม่ |
| SMTP Route | เมลเตือนผู้ดูแล (storeretention warning) | Editable |  |


#### Processing flow

1. เริ่ม
1. query interface_transactions เฉพาะ dataset ฝั่ง STA - COMPENSATE_INIT_I และ COMPENSATE_APPROVE_I เท่านั้น
1. พบ ACK ค้างเกิน 1 วัน? - return_code IS NULL + interface แบบไฟล์ + อายุ >= 1 วัน | No: จบ - ไม่ส่งอีเมล
1. สรุปจำนวนค้าง group ตาม data_name + interface_type - จำนวนค้าง = count_data − count_return_code
1. ส่งอีเมลเตือนผู้ดูแลผ่าน SMTP
1. จบ

#### Database access

| Table/View | Access | Role |
| --- | --- | --- |
| interface_transactions | R | อ่านอย่างเดียว (data_name, return_code, sent_at, received_at) - ไม่มีการเขียน DB |

| Operational control | Requirement |
| --- | --- |
| Transaction | อ่านอย่างเดียว - รันซ้ำปลอดภัย (เสี่ยงแค่อีเมลเตือนซ้ำ) |
| Re-run | รันซ้ำได้ทุกเมื่อ |
| Mail routing | storeretention (warning) |
| Known risk | บั๊ก purge ของ Job 6 (E20) ทำให้ตารางที่เฝ้าโตขึ้นเรื่อย ๆ - ระวังเวลา query ช้าลง |


---


## 3.4 K2 Screen Requirements


### SCR-01 Overview / Dashboard

![รูปที่ 23: Overview / Dashboard - ส่วนที่ 1/2](index-01.png)

![รูปที่ 24: Overview / Dashboard - ส่วนที่ 2/2](index-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงงานค้าง ร้านที่เข้าเกณฑ์ ยอดชดเชย ข้อมูลผิดปกติ กราฟ และทางลัดตามสิทธิ์ |
| Actor | ทุก role ที่ login |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


#### Actions

งานรอท่านดำเนินการ · เอกสารร้านถูกกระทบ · เปิดเอกสารร้านถูกกระทบ · ออกรายงานสรุปสถานะ


#### Business rules / acceptance

- ตัวเลขต้อง aggregate จากข้อมูลจริงและรองรับ cache ไม่เกิน 5 นาที
- ทางลัดและ sidebar ต้องสร้างตาม menu_permissions
- ค่าชื่อผู้ใช้/role ต้องมาจาก JWT ไม่ใช้ข้อมูล mock

### SCR-02 สร้างเอกสาร

![รูปที่ 25: สร้างเอกสาร](k2-create-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | สร้างเอกสารนอกเงื่อนไขอัตโนมัติ หรือส่งสร้างผ่าน FS |
| Actor | HQ 02, User Admin 03 และผู้ที่ได้รับสิทธิ์ |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

![รูปที่ 26: เอกสารรอดำเนินการ - ส่วนที่ 1/2](k2-list-waiting-01.png)

![รูปที่ 27: เอกสารรอดำเนินการ - ส่วนที่ 2/2](k2-list-waiting-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | Task inbox แสดงเฉพาะ OPEN task ที่ผู้ใช้/section ปัจจุบันต้องดำเนินการ |
| Actor | ผู้ดำเนินการ workflow |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

![รูปที่ 28: เอกสารที่เกี่ยวข้อง - ส่วนที่ 1/2](k2-list-related-01.png)

![รูปที่ 29: เอกสารที่เกี่ยวข้อง - ส่วนที่ 2/2](k2-list-related-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงเอกสารทั้งหมดที่ผู้ใช้เคยมีส่วนร่วม โดยแก้ไขได้เฉพาะงานที่อยู่ในสิทธิ์ปัจจุบัน |
| Actor | ผู้ใช้งานทั่วไปตามสิทธิ์ |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

### SCR-05 ข้อมูลผิดปกติ / แจกงาน

![รูปที่ 30: ข้อมูลผิดปกติ / แจกงาน](k2-list-abnormal-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหาและมอบหมายรายการผิดปกติให้ผู้รับผิดชอบ |
| Actor | Assign Job 05 และ Admin |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


#### Input / filter fields

ค้นหา · ภาค · สาเหตุผิดปกติ · สถานะ · ผู้รับผิดชอบ


#### Displayed tables

- tblAbnormal: ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ | Action

#### Actions

แจกงานที่เลือก · ล้างตัวกรอง


#### Business rules / acceptance

- รองรับ multi-select และแจกงานเฉพาะรายการที่เลือก
- แสดงสาเหตุ ผู้รับผิดชอบ และสถานะ assignment
- OPEN: เมนูนี้และ API 2 เส้นถูก comment ไว้ รอคำตัดสิน keep/drop

### SCR-06 เอกสารข้อมูลร้านถูกกระทบ

![รูปที่ 31: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 1/3](k2-document-01.png)

![รูปที่ 32: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 2/3](k2-document-02.png)

![รูปที่ 33: เอกสารข้อมูลร้านถูกกระทบ - ส่วนที่ 3/3](k2-document-03.png)

| Item | Requirement |
| --- | --- |
| Purpose | หน้าหลักสำหรับดู แก้ คำนวณ พิจารณา แนบไฟล์ และเดิน workflow |
| Actor | ผู้ดำเนินการตาม Section และผู้มีสิทธิ์อ่าน |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

พิมพ์ · ข้อมูลยอดขายเพิ่มเติม · รีเฟรช · คืนค่าก่อนแก้ไข · คำนวณเงินชดเชย · Link To ALLMAP · เพิ่ม · บันทึก · เพิ่มข้อมูล · แนบไฟล์ · แนบรูป · ส่งดำเนินการ · OK · ปิด


#### Business rules / acceptance

- แสดงหัวเอกสาร ร้านถูกกระทบ ร้านเปิดใหม่ แผนที่ คู่แข่ง ปัจจัย เอกสารแนบ ชดเชย ประวัติ และผลพิจารณา
- สิทธิ์แก้ไขต้องประเมินต่อ section/role; ส่วนอื่นเป็น read-only
- % ชดเชยร้านเปิดใหม่รวมต้องเท่ากับ 100%
- วันที่สิ้นสุดปัจจัยต้องไม่ก่อนวันที่เริ่มต้น
- ไฟล์แนบไม่เกิน 5 MB และต้องบันทึก section/uploader/time
- ส่งดำเนินการต้องเลือกผล; ข้อความ popup ต้องตรงตาม SRS

### SCR-07 รายงานสรุปสถานะ

![รูปที่ 34: รายงานสรุปสถานะ - ส่วนที่ 1/2](k2-report-01.png)

![รูปที่ 35: รายงานสรุปสถานะ - ส่วนที่ 2/2](k2-report-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหา แสดงกราฟ/ผล 19 คอลัมน์ และ Export Excel |
| Actor | Admin 01, HQ 02, Report Admin 04, Report Admin Special 06 |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


#### Input / filter fields

รหัสร้านที่ถูกกระทบ · ชื่อร้านที่ถูกกระทบ · เดือน/ปี (เริ่มต้น) · ถึง (สิ้นสุด) · ประเภทร้าน (เลือกได้มากกว่า 1) · FR Type A · FR Type B · FR Type C · FR Type พนักงาน · ภาค (เลือกได้มากกว่า 1) · BE · BN · BS · BW · RC · RE · RN · RS · สถานะ (ค้นหาได้ทีละ 1 สถานะ) · ผลการพิจารณา (อนุมัติ/ไม่อนุมัติ) · Period Statement (From - To)


#### Displayed tables

- Table: รหัสร้านถูกกระทบ | ชื่อร้านถูกกระทบ | ภาค | ประเภทร้าน | เดือนปีที่ถูกกระทบ | วันที่โอนเป็นร้าน SP | Period Statement | รหัสร้านเปิดใหม่ | ชื่อร้านเปิดใหม่ | ภาค (ร้านใหม่) | ประเภทร้าน (ร้านใหม่) | ยอดเงินชดเชย | สถานะ | ชื่อ-นามสกุลผู้ดำเนินการ | ผลการพิจารณา | รอดำเนินการ (วัน) | ครั้งที่ | วันที่สร้าง | เลขที่เอกสาร

#### Actions

Export Excel · เคลียร์ค่าเริ่มใหม่ · ค้นหาข้อมูล


#### Business rules / acceptance

- บังคับระบุปีและคืนเฉพาะรายการที่มีเลขเอกสาร
- ประเภทร้านและภาคเลือกหลายค่า; สถานะเลือกหนึ่งค่า
- ผลและ Excel ต้องใช้ dataset/เงื่อนไขเดียวกัน
- แถวข้อมูลยอดขายไม่ครบ 60 วันต้องเป็นสีแดง

### SCR-08 กำหนดผู้ปฏิบัติงาน

![รูปที่ 36: กำหนดผู้ปฏิบัติงาน](k2-operators-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการผู้ปฏิบัติงานต่อ section และ zone |
| Actor | Admin 01, HQ 02, User Admin 03 |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

![รูปที่ 37: กำหนดปัจจัยภายนอก](k2-factors-01.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการ external factor master และประวัติแก้ไข |
| Actor | Admin 01, HQ 02, User Admin 03 |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

![รูปที่ 38: สิทธิ์การเข้าถึงเมนู - ส่วนที่ 1/2](k2-permissions-01.png)

![รูปที่ 39: สิทธิ์การเข้าถึงเมนู - ส่วนที่ 2/2](k2-permissions-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | แสดงและบริหาร RBAC 8 role ต่อ main menu และ master forms |
| Actor | Admin และผู้ดูแลสิทธิ์ที่ได้รับมอบหมาย |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

![รูปที่ 40: ตั้งค่าระบบ (Global Config) - ส่วนที่ 1/2](system-config-01.png)

![รูปที่ 41: ตั้งค่าระบบ (Global Config) - ส่วนที่ 2/2](system-config-02.png)

| Item | Requirement |
| --- | --- |
| Purpose | จัดการค่ากำหนดกลางที่ใช้ร่วมทั้งระบบ เช่น รัศมีผลกระทบ เกณฑ์ข้อมูล วงเงินอนุมัติ token และ notification switch |
| Actor | Admin และผู้ดูแลระบบที่ได้รับมอบหมาย |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


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

### SCR-12 Email Template

![รูปที่ 42: Email Template - ส่วนที่ 1/3](plan-email-01.png)

![รูปที่ 43: Email Template - ส่วนที่ 2/3](plan-email-02.png)

![รูปที่ 44: Email Template - ส่วนที่ 3/3](plan-email-03.png)

| Item | Requirement |
| --- | --- |
| Purpose | กำหนดเนื้อหาอีเมล 8 template ของ Notification Service และผูกจุดส่งกับ workflow/batch |
| Actor | Admin และผู้ดูแล notification |
| Pre-condition | ผ่านการ login และมีสิทธิ์เมนู/ข้อมูล |


#### Displayed tables

- tplMap: Template | ชื่อ | จุดที่ส่งใน Flow | ผู้รับ (TO) | แหล่งกติกาผู้รับ | ความถี่
- Table: วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม -> ข้อมูลใหม่ | เหตุผลการแก้ไข

#### Actions

รีเซ็ตทั้งหมดเป็น Default


#### Business rules / acceptance

- รองรับ template EM-01 ถึง EM-08 ครอบคลุม workflow transition, reminder, escalation, batch error และ STA ACK watchdog
- แก้ไขได้เฉพาะ subject/body และตัวแปร merge ที่รองรับของ template นั้น
- From/To/Cc ต้องล็อกตาม status_email_rules หรือ config ต่อ job ไม่ให้แก้ใน template
- ต้องรีเซ็ตกลับ Default ได้ทั้งราย template และทั้งหมด
- ทุกการแก้ไขหรือรีเซ็ตต้องบันทึก audit_logs พร้อมเหตุผล

### 3.4.13 Shared UI contract

- ทุกหน้าจอต้องมี metadata สำหรับ page, nav, module, breadcrumb, sidebar mount และ main content
- Header/sidebar ถูกสร้างโดย shared shell; ห้ามทำซ้ำในแต่ละหน้า
- Schema modal อ้างชื่อ table header แบบ exact match; การเปลี่ยน label ต้องแก้ mapping และทดสอบ add/view/edit/delete
- รองรับ desktop และ responsive layout; ตารางกว้างต้องเลื่อนแนวนอนโดยไม่ตัดข้อมูล
- ข้อความ popup/validation ภาษาไทยและ source tag (FGI/FCS), (K2), (ใหม่) ต้องคงตามข้อกำหนด

---


## 3.5 API Requirements

![รูปที่ 45: API Specification - ส่วนที่ 1/4](plan-api-01.png)

![รูปที่ 46: API Specification - ส่วนที่ 2/4](plan-api-02.png)

![รูปที่ 47: API Specification - ส่วนที่ 3/4](plan-api-03.png)

![รูปที่ 48: API Specification - ส่วนที่ 4/4](plan-api-04.png)


### 3.5.1 Common conventions

| Topic | Requirement |
| --- | --- |
| Base URL | /api/v1 |
| Authentication | Authorization: Bearer <JWT>; login/refresh public; callbacks ใช้ API key; internal workflow ใช้ service token |
| Format | JSON UTF-8; วันที่ ISO-8601 ปี ค.ศ.; FE แปลงปีแสดงผลตามข้อยุติ |
| Pagination | ?page=1&size=20 -> {page,size,total,items:[]} |
| Error | {"code":"DOC_409","message":"ข้อความภาษาไทยตรงตาม SRS"} |
| Audit | ทุก mutation บันทึก actor จาก JWT/service identity, correlation id และ before/after ที่เหมาะสม |
| Idempotency | create/action/callback/manual run ต้องรองรับ idempotency key หรือ business duplicate guard |


### 3.5.2 Endpoint catalog

| Group | Method | Path | Roles | Purpose | Source |
| --- | --- | --- | --- | --- | --- |
| Auth & สิทธิ์ผู้ใช้ | POST | /api/v1/auth/login | ทุกคน (public) | เข้าสู่ระบบด้วยบัญชีพนักงาน แลก JWT พร้อม role และ section สำหรับใช้ทุกเส้นถัดไป | K2 · 3.1.1 |
| Auth & สิทธิ์ผู้ใช้ | POST | /api/v1/auth/refresh | ผู้ถือ refreshToken | ต่ออายุ accessToken โดยไม่ต้อง login ใหม่ | ใหม่ |
| Auth & สิทธิ์ผู้ใช้ | GET | /api/v1/auth/me | ทุก role | ข้อมูลผู้ใช้ปัจจุบันจาก JWT - FE ใช้แสดงชื่อ/role มุมขวาบน | K2 |
| Auth & สิทธิ์ผู้ใช้ | GET | /api/v1/me/menus | ทุก role | เมนูที่ role ของผู้ใช้เข้าถึงได้ - FE ใช้สร้าง sidebar (แทนตารางสิทธิ์ 8 role ในหน้าจอ 3.1.1) | K2 · 3.1.1 |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/tasks | role ที่มีสิทธิ์เมนูเอกสาร | งานรอท่านดำเนินการ - เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า Task Inbox) | K2 · 3.1.2 |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents | ตามสิทธิ์เมนู | ค้นหาเอกสารที่เกี่ยวข้อง - บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS) | K2 · 3.1.3 / 3.1.7 |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo} | ตามสิทธิ์เมนู | เอกสารฉบับเต็ม 12 ส่วนย่อย (Document Detail) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน | K2 · 3.1.6 |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents | 02 HQ, 03 User Admin | สร้างเอกสารใหม่นอกเงื่อนไข หรือสร้างเอกสารที่ FS (สองแท็บของ Create Document) | K2 · 3.1.6 |
| งาน & เอกสารประกันรายได้ | PUT | /api/v1/documents/{docNo} | ตาม section ปัจจุบัน | บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่ | K2 · 3.1.6 |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents/{docNo}/actions | เจ้าของ task ปัจจุบัน | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน - หัวใจ workflow 7 ขั้น · กฎวงเงิน 100,000 ใช้ทั้งกรณีชดเชยและไม่ชดเชย | K2 · 3.1.4 |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo}/timeline | ตามสิทธิ์เมนู | ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร) | K2 · 3.1.6 |
| งาน & เอกสารประกันรายได้ | POST | /api/v1/documents/{docNo}/attachments | ตาม section ปัจจุบัน | แนบไฟล์เข้าเอกสาร - จำกัด 5MB ต่อไฟล์ตาม SRS | K2 · 3.1.6 |
| งาน & เอกสารประกันรายได้ | GET | /api/v1/documents/{docNo}/sales | ตามสิทธิ์เมนู | ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง x 15 วัน) - ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร Document Detail | K2 · 3.1.6 |
| ข้อมูลอ้างอิง (Lookup / Reference) | GET | /api/v1/stores/search | ตามสิทธิ์เมนูเอกสาร | ค้นหาร้าน (แว่นขยายในหน้า Create Document) - ร้านถูกกระทบ (SP) หรือร้านเปิดใหม่ 7-Eleven ตาม type | FGI/FCS master + K2 |
| ข้อมูลอ้างอิง (Lookup / Reference) | GET | /api/v1/competitors | ตาม section ปัจจุบัน | รายการร้านคู่แข่ง master 24 ราย - dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (Document Detail) | K2 · master คู่แข่ง |
| ข้อมูลอ้างอิง (Lookup / Reference) | GET | /api/v1/document-statuses | ทุก role | รายการสถานะเอกสารทั้งหมด - เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report) | K2 · 3.1.3 / 3.1.7 |
| ข้อมูลอ้างอิง (Lookup / Reference) | GET | /api/v1/workflow-sections | ทุก role | รายการ Section 7 ขั้น - dropdown เลือกตำแหน่ง/ขั้น (หน้า 3.1.8) และตัวกรองตาม section | K2 · master section |
| Master Data | GET | /api/v1/operators | 03 User Admin | รายชื่อผู้ปฏิบัติงาน (operator_assignments) พร้อมค้นหา/แบ่งหน้า | K2 · 3.1.8 |
| Master Data | POST | /api/v1/operators | 03 User Admin | เพิ่มผู้ปฏิบัติงานใหม่ (จากหน้าค้นหาพนักงานด้วยแว่นขยาย) | K2 · 3.1.8 |
| Master Data | PUT | /api/v1/operators/{id} | 03 User Admin | แก้ไขข้อมูลผู้ปฏิบัติงาน | K2 · 3.1.8 |
| Master Data | DELETE | /api/v1/operators/{id} | 03 User Admin | ลบผู้ปฏิบัติงาน พร้อมบันทึกเหตุผล | K2 · 3.1.8 |
| Master Data | GET | /api/v1/factors | 03 User Admin | รายการปัจจัยภายนอก (external_factors) | K2 · 3.1.9 |
| Master Data | POST | /api/v1/factors | 03 User Admin | เพิ่มปัจจัยภายนอก - รหัสห้ามซ้ำ (กติกา SRS) | K2 · 3.1.9 |
| Master Data | PUT | /api/v1/factors/{code} | 03 User Admin | แก้ไขปัจจัยภายนอก | K2 · 3.1.9 |
| Master Data | DELETE | /api/v1/factors/{code} | 03 User Admin | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) | K2 · 3.1.9 |
| Master Data | GET | /api/v1/employees/search | 03 User Admin | ค้นหาพนักงานจากระบบ HR (popup แว่นขยายในหน้า 3.1.8) | K2 3.1.8 + master FGI/FCS |
| Master Data | GET | /api/v1/menu-permissions | 01 Admin, 02 HQ | ตาราง matrix สิทธิ์เมนูทั้งหมด (8 role x เมนู) - หน้าจอสิทธิ์การเข้าถึงเมนู | K2 · 3.1.1 |
| Master Data | PUT | /api/v1/menu-permissions/{menuCode} | 01 Admin, 02 HQ | แก้สิทธิ์การเข้าถึงเมนูหนึ่งรายการต่อทุก role - บันทึก audit เสมอ | K2 · 3.1.1 |
| Master Data | GET | /api/v1/roles | 01 Admin, 02 HQ | รายการ Role ทั้งหมด (ตารางกลุ่มผู้ใช้งานในหน้าจอ 3.1.1 และ dropdown ที่อื่น) | K2 · 3.1.1 |
| Master Data | POST | /api/v1/roles | 01 Admin, 02 HQ | เพิ่ม Role ใหม่ - ระบบสร้างสิทธิ์เมนูเริ่มต้นเป็น "ไม่มีสิทธิ์" ทุกเมนู | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | PUT | /api/v1/roles/{roleCode} | 01 Admin, 02 HQ | แก้ชื่อ/คำอธิบาย Role - ต้องระบุเหตุผล บันทึก audit เสมอ | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | DELETE | /api/v1/roles/{roleCode} | 01 Admin, 02 HQ | ลบ Role - ลบไม่ได้ถ้าเป็น Role ระบบ (is_system) หรือยังมีผู้ใช้อ้างอยู่ | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | POST | /api/v1/menus | 01 Admin, 02 HQ | เพิ่มเมนูใหม่เข้าระบบ - สิทธิ์เริ่มต้นเป็น "ไม่มีสิทธิ์" ทุก Role | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | PUT | /api/v1/menus/{menuCode} | 01 Admin, 02 HQ | แก้ชื่อ/กลุ่ม/ลำดับเมนู - ต้องระบุเหตุผล บันทึก audit เสมอ | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | DELETE | /api/v1/menus/{menuCode} | 01 Admin, 02 HQ | ลบเมนูพร้อมสิทธิ์ทุก Role ของเมนูนั้น (cascade) - เมนูระบบลบไม่ได้ | ใหม่ · หน้าจอ 3.1.1 |
| Master Data | GET | /api/v1/audit-logs | 01 Admin, 02 HQ, 03 User Admin | ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม->ใหม่ · เหตุผล · เมื่อไร) - แผงประวัติท้ายหน้าจอ 3.1.8 / 3.1.9 | K2 · 3.1.8 / 3.1.9 |
| System Config (Global) | GET | /api/v1/configs | 01 Admin | รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ Global Config) | ใหม่ · Global Config |
| System Config (Global) | GET | /api/v1/configs/{key} | ทุก role (อ่าน) / service token | อ่านค่ากำหนดรายตัว - เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที | ใหม่ · Global Config |
| System Config (Global) | POST | /api/v1/configs | 01 Admin | เพิ่มค่ากำหนดใหม่ - key ห้ามซ้ำ และ validate ค่าตาม value_type | ใหม่ · Global Config |
| System Config (Global) | PUT | /api/v1/configs/{key} | 01 Admin | แก้ค่ากำหนด - ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้ | ใหม่ · Global Config |
| System Config (Global) | DELETE | /api/v1/configs/{key} | 01 Admin | ลบค่ากำหนด - ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล | ใหม่ · Global Config |
| Email Template (Notification) | GET | /api/v1/email-templates | 01 Admin | รายการ 8 email template (EM-01-08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ Email Template) | ใหม่ · Notification |
| Email Template (Notification) | GET | /api/v1/email-templates/{code} | 01 Admin | อ่าน template รายตัว (EM-01-08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น | ใหม่ · Notification |
| Email Template (Notification) | PUT | /api/v1/email-templates/{code} | 01 Admin | บันทึกเนื้อหา template - แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules) | ใหม่ · Notification |
| Email Template (Notification) | POST | /api/v1/email-templates/{code}/reset | 01 Admin | รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ) | ใหม่ · Notification |
| Email Template (Notification) | POST | /api/v1/email-templates/reset-all | 01 Admin | รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default") | ใหม่ · Notification |
| รายงาน | GET | /api/v1/reports/status-summary | 04 / 06 Report Admin | รายงานสรุปสถานะ 19 คอลัมน์ - บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) | K2 · 3.1.7 |
| รายงาน | GET | /api/v1/reports/status-summary/export | 04 / 06 Report Admin | Export รายงานเป็นไฟล์ Excel เงื่อนไขเดียวกับเส้นค้นหา | K2 · 3.1.7 |
| Batch Job Admin | GET | /api/v1/jobs | 01 Admin | รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด (หน้าจอ Batch Job Console) | FGI/FCS |
| Batch Job Admin | GET | /api/v1/jobs/{jobNo} | 01 Admin | รายละเอียด job หนึ่งตัว: พารามิเตอร์ (แยกแก้ได้/คงที่), flow, ตารางที่ใช้ | FGI/FCS |
| Batch Job Admin | PUT | /api/v1/jobs/{jobNo}/params | 01 Admin | แก้พารามิเตอร์ที่แก้ได้ของ job (เวลารัน, path, เกณฑ์) - ค่าคงที่ทางธุรกิจแก้ผ่าน API ไม่ได้ | FGI/FCS + ข้อ 8.2 |
| Batch Job Admin | POST | /api/v1/jobs/{jobNo}/run | 01 Admin | สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล - มี guard กันรันซ้อน | FGI/FCS · Runbook 7.1 |
| Batch Job Admin | PUT | /api/v1/jobs/{jobNo}/enabled | 01 Admin | เปิด/ปิดการทำงานของ job ตามรอบเวลา | FGI/FCS |
| Batch Job Admin | GET | /api/v1/jobs/{jobNo}/runs | 01 Admin | ประวัติการรันของ job (แท็บประวัติในหน้า Batch Monitor) | FGI/FCS |
| Workflow ภายใน | POST | /api/v1/workflows/instances | service token (ภายใน) | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate - เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม | แทน K2 StartInstance (Job 8b) |
| Workflow ภายใน | GET | /api/v1/workflows/instances/{id} | 01 Admin / เจ้าของงาน | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) | ใหม่ |
| Workflow ภายใน | GET | /api/v1/workflows/summary | 01 Admin | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น | FGI/FCS · Monitoring 7.4 |
| Interface & Dashboard | GET | /api/v1/interfaces/tracking | 01 Admin | สถานะการรับ-ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) | FGI/FCS |
| Interface & Dashboard | POST | /api/v1/interfaces/sta/ack | API key ของระบบ STA | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง - แทนการรออัปเดต return_code ฝั่งเดียว | ใหม่ (เสริม Job 10) |
| Interface & Dashboard | GET | /api/v1/interfaces/pending-ack | 01 Admin | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) - ใช้ทั้งหน้า dashboard และอีเมลเตือน | FGI/FCS · Job 10 |
| Interface & Dashboard | GET | /api/v1/dashboard/summary | ทุก role | ตัวเลขหน้า Dashboard: งานค้าง, ร้านประกันรายได้เดือนนี้, ยอดชดเชย, ข้อมูลผิดปกติ + ข้อมูลกราฟ | K2 (หน้าหลัก) |


### 3.5.3 Endpoint details


### API Group 1: Auth & สิทธิ์ผู้ใช้ (K2 · SRS 3.1.1)


#### API-01 POST /api/v1/auth/login

| Item | Requirement |
| --- | --- |
| Purpose | เข้าสู่ระบบด้วยบัญชีพนักงาน แลก JWT พร้อม role และ section สำหรับใช้ทุกเส้นถัดไป |
| Roles | ทุกคน (public) |
| Source | K2 · 3.1.1 |

Flow:

1. ตรวจ username/password กับ AD/LDAP ขององค์กร
1. โหลด user_accounts + role (00-10) และ section_code ของผู้ใช้
1. ออก accessToken (30 นาที) + refreshToken (8 ชั่วโมง)
| Table | Access | Role |
| --- | --- | --- |
| user_accounts | R | บัญชีผู้ใช้ + role (ตารางใหม่) |
| roles | R | ชื่อ role 00-10 (K2 3.1.1) |

Request

```text
{
  "username": "phatcharida.p",
  "password": "********"
}
```

Response

```text
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "d2f8a1...",
  "user": {
    "empId": "57123",
    "name": "ภัชริดา ประเสริฐ",
    "roles": ["03"],
    "sectionCode": "06"
  }
}
```

Errors

- 401 - ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง
- 423 - บัญชีถูกล็อกจากการลองผิดเกินกำหนด

#### API-02 POST /api/v1/auth/refresh

| Item | Requirement |
| --- | --- |
| Purpose | ต่ออายุ accessToken โดยไม่ต้อง login ใหม่ |
| Roles | ผู้ถือ refreshToken |
| Source | ใหม่ |

Flow:

1. ตรวจ refreshToken ยังไม่หมดอายุ/ไม่ถูกเพิกถอน
1. ออก accessToken ใหม่
| Table | Access | Role |
| --- | --- | --- |
| user_accounts | R | ตรวจสถานะบัญชียัง active |

Request

```text
{
  "refreshToken": "d2f8a1..."
}
```

Response

```text
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

Errors

- 401 - token หมดอายุหรือถูกเพิกถอน ให้ login ใหม่

#### API-03 GET /api/v1/auth/me

| Item | Requirement |
| --- | --- |
| Purpose | ข้อมูลผู้ใช้ปัจจุบันจาก JWT - FE ใช้แสดงชื่อ/role มุมขวาบน |
| Roles | ทุก role |
| Source | K2 |

Flow:

1. ถอด JWT -> คืนข้อมูลผู้ใช้และ section ปัจจุบัน
| Table | Access | Role |
| --- | --- | --- |
| user_accounts | R | ข้อมูลผู้ใช้ล่าสุด |

Request

```text
(ไม่มี body - ใช้ JWT ใน header)
```

Response

```text
{
  "empId": "57123",
  "name": "ภัชริดา ประเสริฐ",
  "roles": ["03"],
  "sectionCode": "06",
  "zone": "RS"
}
```

Errors

- 401 - token หมดอายุ

#### API-04 GET /api/v1/me/menus

| Item | Requirement |
| --- | --- |
| Purpose | เมนูที่ role ของผู้ใช้เข้าถึงได้ - FE ใช้สร้าง sidebar (แทนตารางสิทธิ์ 8 role ในหน้าจอ 3.1.1) |
| Roles | ทุก role |
| Source | K2 · 3.1.1 |

Flow:

1. อ่าน role จาก JWT
1. join menu_permissions x menus เอาเฉพาะ can_access = true
1. คืนรายการเมนูเรียงตามกลุ่ม
| Table | Access | Role |
| --- | --- | --- |
| menu_permissions | R | สิทธิ์ต่อ role (composite PK) |
| menus | R | ชื่อ/กลุ่มเมนู |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "menus": [
    { "code": "M02", "name": "เอกสาร · รอดำเนินการ", "group": "ระบบประกันรายได้" },
    { "code": "M08", "name": "Batch Job", "group": "ระบบประกันรายได้" }
  ]
}
```

Errors

- 401

### API Group 2: งาน & เอกสารประกันรายได้ (K2 · SRS 3.1.2 / 3.1.3 / 3.1.6)


#### API-05 GET /api/v1/tasks

| Item | Requirement |
| --- | --- |
| Purpose | งานรอท่านดำเนินการ - เอกสารที่ค้างอยู่ที่ section ของผู้ใช้ (หน้า Task Inbox) |
| Roles | role ที่มีสิทธิ์เมนูเอกสาร |
| Source | K2 · 3.1.2 |

Flow:

1. อ่าน sectionCode ของผู้ใช้จาก JWT
1. query workflow_tasks สถานะ OPEN ของ section นั้น
1. join compensation_documents + impacted_stores คืน 9 คอลัมน์ตามหน้าจอ
| Table | Access | Role |
| --- | --- | --- |
| workflow_tasks | R | งานค้างต่อ section (ตารางใหม่ - inbox) |
| compensation_documents | R | ข้อมูลเอกสาร |
| impacted_stores | R | ชื่อ/ภาคของร้าน |

Request

```text
Query: ?page=1&size=20&q=00788
(q = เลขที่เอกสาร / รหัสร้าน / ชื่อร้าน)
```

Response

```text
{
  "page": 1, "total": 24,
  "items": [{
    "docNo": "2569/00123",
    "storeCode": "00788",
    "storeName": "รัตนอุทิศ ซ.13",
    "impactMonth": "2026-06",
    "status": "รอฝ่าย SBP DSA ดำเนินการ",
    "currentSection": "06",
    "waitingDays": 3
  }]
}
```

Errors

- 401

#### API-06 GET /api/v1/documents

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหาเอกสารที่เกี่ยวข้อง - บังคับระบุปี และคืนเฉพาะเอกสารที่มีเลขที่แล้ว (กติกา SRS) |
| Roles | ตามสิทธิ์เมนู |
| Source | K2 · 3.1.3 / 3.1.7 |

Flow:

1. validate: ต้องระบุ year เสมอ ไม่งั้นตอบ 400
1. ค้น compensation_documents ตามเงื่อนไข (เลขที่ / ร้าน / สถานะ / เดือน)
1. คืนแบบแบ่งหน้า
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents | R | เอกสารตามเงื่อนไข |
| impacted_stores | R | ข้อมูลร้าน |

Request

```text
Query: ?year=2569&storeCode=00788&status=06&page=1
(status = section ที่รออยู่ 06/08/01/02/03/04/05 หรือ END)
```

Response

```text
{
  "page": 1, "total": 6,
  "items": [{ "docNo": "2569/00123", "status": "รอฝ่าย SBP DSA ดำเนินการ", ... }]
}
```

Errors

- 400 - กรุณาระบุปีที่ต้องการค้นหา (กติกา SRS)
- 401

#### API-07 GET /api/v1/documents/{docNo}

| Item | Requirement |
| --- | --- |
| Purpose | เอกสารฉบับเต็ม 12 ส่วนย่อย (Document Detail) พร้อมธงสิทธิ์แก้ไขต่อส่วนตาม role/section ปัจจุบัน |
| Roles | ตามสิทธิ์เมนู |
| Source | K2 · 3.1.6 |

Flow:

1. โหลดเอกสาร + ร้านใหม่ + คู่แข่ง + ปัจจัย + ไฟล์แนบ + สรุปชดเชย ในคำขอเดียว
1. คำนวณ permissions: ส่วนไหนแก้ได้ตาม role + current_section_code (data-editrole เดิม)
1. FE ใช้ธงนี้แสดงป้าย "อ่านอย่างเดียว" ต่อส่วน
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents | R | หัวเอกสาร |
| document_new_stores / document_competitors / document_external_factors | R | ส่วนย่อย |
| document_attachments / consideration_logs | R | ไฟล์แนบ + ประวัติ |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "docNo": "2569/00123",
  "status": "รอฝ่าย SBP DSA ดำเนินการ",
  "currentSection": "06",
  "impactedStore": { "storeCode": "00788", ... },
  "newStores": [ { "storeCode": "15211", "compensatePercent": 60.0 } ],
  "competitors": [ ... ],
  "factors": [ ... ],
  "compensation": { "amount": 95000.00, "salesDropPercent": 12.5 },
  "permissions": { "canEditSections": ["competitor","factor"], "canAction": true }
}
```

Errors

- 404 - ไม่พบเอกสาร
- 401

#### API-08 POST /api/v1/documents

| Item | Requirement |
| --- | --- |
| Purpose | สร้างเอกสารใหม่นอกเงื่อนไข หรือสร้างเอกสารที่ FS (สองแท็บของ Create Document) |
| Roles | 02 HQ, 03 User Admin |
| Source | K2 · 3.1.6 |

Flow:

1. ตรวจซ้ำ: ร้าน + เดือนที่ถูกกระทบ ต้องยังไม่มีเอกสาร
1. ออกเลขที่ YYYY/xxxxx (running ต่อปี เริ่ม 00001 - กติกา SRS)
1. insert compensation_documents สถานะเริ่มต้น + เปิด workflow_instances / workflow_tasks แรก (Section 06)
1. ส่งอีเมลตาม status_email_rules
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents | W | เอกสารใหม่ |
| workflow_instances / workflow_tasks | W | เปิด workflow + งานแรก |
| status_email_rules | R | ผู้รับอีเมล TO/CC |

Request

```text
{
  "impactedStoreCode": "00788",
  "impactMonth": "2026-06",
  "source": "MANUAL"   // MANUAL | FS
}
```

Response

```text
201 Created
{
  "docNo": "2569/00124"
}
```

Errors

- 409 - ร้านนี้ในเดือนนี้มีเอกสารอยู่แล้ว
- 422 - ข้อมูลบังคับไม่ครบ

#### API-09 PUT /api/v1/documents/{docNo}

| Item | Requirement |
| --- | --- |
| Purpose | บันทึกแก้ไขส่วนย่อยของเอกสาร (ร้านใหม่ / คู่แข่ง / ปัจจัย) ตามสิทธิ์ของขั้นที่ถืออยู่ |
| Roles | ตาม section ปัจจุบัน |
| Source | K2 · 3.1.6 |

Flow:

1. ตรวจว่า role + section ปัจจุบันมีสิทธิ์แก้ส่วนที่ส่งมา (เช่น Section 01 แก้คู่แข่ง/ปัจจัยได้)
1. validate %ชดเชยของร้านใหม่รวมกันต้องเท่ากับ 100%
1. บันทึกและคืนเอกสารล่าสุด
| Table | Access | Role |
| --- | --- | --- |
| document_new_stores | R/W | %ชดเชย · ระยะห่าง |
| document_competitors | R/W | คู่แข่ง |
| document_external_factors | R/W | ปัจจัยภายนอก |

Request

```text
{
  "newStores": [ { "newStoreId": 88, "compensatePercent": 60.0 },
                 { "newStoreId": 89, "compensatePercent": 40.0 } ]
}
```

Response

```text
200 OK - เอกสารฉบับล่าสุด (โครงเดียวกับ GET)
```

Errors

- 403 - ไม่มีสิทธิ์แก้ส่วนนี้ในขั้นปัจจุบัน
- 422 - "%ชดเชย ... รวมกันแล้วไม่เท่ากับ 100%" (ข้อความตรงตาม SRS)

#### API-10 POST /api/v1/documents/{docNo}/actions

| Item | Requirement |
| --- | --- |
| Purpose | ส่งผลพิจารณาตามตัวเลือกของขั้นปัจจุบัน - หัวใจ workflow 7 ขั้น · กฎวงเงิน 100,000 ใช้ทั้งกรณีชดเชยและไม่ชดเชย |
| Roles | เจ้าของ task ปัจจุบัน |
| Source | K2 · 3.1.4 |

Flow:

1. ตรวจว่าผู้ใช้เป็นเจ้าของ workflow_tasks ขั้นปัจจุบัน
1. validate เลือกผลแล้ว - ไม่งั้น 422 ข้อความ SRS ตรงตัว
1. คำนวณขั้นถัดไปตามตารางเส้นทาง (workflow.md): 06 ไม่ชดเชย/หยุดชดเชย -> เสร็จสิ้น · 06 ส่งข้าม 04 ได้ · 02 ชดเชย/ไม่ชดเชย > 100,000 -> 03 · ชดเชย <= 100,000 -> 04 · ไม่ชดเชย <= 100,000 -> กลับ 06 · ทุกขั้นมีเส้นส่งกลับ
1. insert consideration_logs + ปิด task เดิม เปิด task ใหม่
1. ส่งอีเมล TO/CC ตาม status_email_rules
| Table | Access | Role |
| --- | --- | --- |
| workflow_tasks | R/W | ปิดงานเดิม เปิดงานขั้นถัดไป |
| compensation_documents | W | อัปเดต Status + CurSection |
| consideration_logs | W | บันทึกผลพิจารณา |
| status_email_rules | R | ผู้รับอีเมล |

Request

```text
{
  "action": "COMPENSATE",
  // ตัวเลือกตามขั้นปัจจุบัน เช่น COMPENSATE / NOT_COMPENSATE / STOP
  // CALC_DONE (08) / SEND_BACK / SKIP_TO_ACCT (06->04)
  "comment": "เห็นควรชดเชยตามหลักเกณฑ์"
}
```

Response

```text
{
  "docNo": "2569/00123",
  "nextSection": "02",
  "status": "รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ"
}
```

Errors

- 422 - "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูล ก่อนกดส่งดำเนินการ"
- 403 - ไม่ใช่เจ้าของงานขั้นนี้
- 409 - งานถูกดำเนินการไปแล้วโดยผู้อื่น

#### API-11 GET /api/v1/documents/{docNo}/timeline

| Item | Requirement |
| --- | --- |
| Purpose | ประวัติการพิจารณาทุกขั้นของเอกสาร (timeline ในหน้าเอกสาร) |
| Roles | ตามสิทธิ์เมนู |
| Source | K2 · 3.1.6 |

Flow:

1. อ่าน consideration_logs เรียงตามเวลา
| Table | Access | Role |
| --- | --- | --- |
| consideration_logs | R | ประวัติครบทุกขั้น |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{
    "section": "06",
    "considerName": "สมชาย ใจดี",
    "result": "ชดเชย",
    "detail": "ตรวจสอบแล้วเข้าเกณฑ์",
    "actionDateTime": "2026-06-18T10:42:00"
  }]
}
```

Errors

- 404

#### API-12 POST /api/v1/documents/{docNo}/attachments

| Item | Requirement |
| --- | --- |
| Purpose | แนบไฟล์เข้าเอกสาร - จำกัด 5MB ต่อไฟล์ตาม SRS |
| Roles | ตาม section ปัจจุบัน |
| Source | K2 · 3.1.6 |

Flow:

1. รับ multipart/form-data (file + sectionCode)
1. ตรวจขนาด <= 5MB และชนิดไฟล์ที่อนุญาต
1. บันทึกไฟล์ + insert document_attachments
| Table | Access | Role |
| --- | --- | --- |
| document_attachments | W | เมทาดาต้าไฟล์ + section ที่แนบ |

Request

```text
multipart/form-data
  file: (binary <= 5MB)
  sectionCode: "06"
```

Response

```text
201 Created
{ "attachId": 771, "fileName": "หนังสือแจ้งผล.pdf" }
```

Errors

- 413 - ไฟล์เกิน 5MB
- 415 - ชนิดไฟล์ไม่อนุญาต

#### API-13 GET /api/v1/documents/{docNo}/sales

| Item | Requirement |
| --- | --- |
| Purpose | ข้อมูลยอดขายเพิ่มเติมของเอกสาร (4 หน้าต่าง x 15 วัน) - ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" ในหน้าเอกสาร Document Detail |
| Roles | ตามสิทธิ์เมนู |
| Source | K2 · 3.1.6 |

Flow:

1. หา impact_process_id ของเอกสารจาก compensation_documents
1. อ่าน fgi_impact_sales_summaries (หัว) + sales_transactions (รายวัน) ของงวดนั้น (โซน A)
1. คืน growth_rate_diff · total_working_days + แถวยอดขายรายวันแยก 4 หน้าต่าง
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents | R | หา impact_process_id ของเอกสาร |
| fgi_impact_sales_summaries | R | หัวยอดขาย · growth_rate_diff · total_working_days |
| sales_transactions | R | ยอดขายรายวัน 4 หน้าต่าง x 15 วัน |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "growthRateDiff": -12.45,
  "totalWorkingDays": 60,
  "windows": [
    { "label": "ก่อนเปิด 15 วัน",
      "rows": [ { "date": "2026-05-01", "amount": 42500.00 } ] }
  ]
}
```

Errors

- 404 - ไม่พบเอกสารหรือยอดขายของงวดนี้
- 401

### API Group 3: ข้อมูลอ้างอิง (Lookup / Reference) (K2 + FGI/FCS · master สำหรับ dropdown)


#### API-14 GET /api/v1/stores/search

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหาร้าน (แว่นขยายในหน้า Create Document) - ร้านถูกกระทบ (SP) หรือร้านเปิดใหม่ 7-Eleven ตาม type |
| Roles | ตามสิทธิ์เมนูเอกสาร |
| Source | FGI/FCS master + K2 |

Flow:

1. รับ q (รหัส/ชื่อร้าน) + type (impacted | new)
1. type=impacted -> ค้น impacted_stores (ร้าน SP)
1. type=new -> ค้น stores (master สาขา 7-Eleven ทุกประเภท)
1. คืนรายการสั้นสำหรับ popup เลือก (คงเลขศูนย์นำหน้ารหัสร้าน)
| Table | Access | Role |
| --- | --- | --- |
| stores | R | master สาขา 7-Eleven - ร้านเปิดใหม่ (โซน C) |
| impacted_stores | R | ร้าน SP - ร้านถูกกระทบ |

Request

```text
Query: ?q=00788&type=impacted
(type = impacted | new)
```

Response

```text
{
  "items": [{ "storeCode": "00788", "storeName": "รัตนอุทิศ ซ.13", "storeType": "SP" }]
}
```

Errors

- 401

#### API-15 GET /api/v1/competitors

| Item | Requirement |
| --- | --- |
| Purpose | รายการร้านคู่แข่ง master 24 ราย - dropdown ตอนกดปุ่ม "เพิ่ม" ตารางร้านคู่แข่งเปิดกระทบ (Document Detail) |
| Roles | ตาม section ปัจจุบัน |
| Source | K2 · master คู่แข่ง |

Flow:

1. query competitors ทั้งหมด / ตามคำค้น
1. คืนรหัส + ชื่อคู่แข่งสำหรับเลือกใส่ document_competitors
| Table | Access | Role |
| --- | --- | --- |
| competitors | R | master ร้านคู่แข่ง 24 ราย (108 Shop, Lotus Express, CJ ...) |

Request

```text
Query: ?q=lotus
```

Response

```text
{
  "items": [{ "competitorCode": "C007", "competitorName": "Lotus Express" }]
}
```

Errors

- 401

#### API-16 GET /api/v1/document-statuses

| Item | Requirement |
| --- | --- |
| Purpose | รายการสถานะเอกสารทั้งหมด - เติม dropdown ตัวกรองสถานะในหน้าค้นหาเอกสาร (k2-list-related) และรายงาน (k2-report) |
| Roles | ทุก role |
| Source | K2 · 3.1.3 / 3.1.7 |

Flow:

1. อ่าน document_statuses ทั้งหมดเรียงตามลำดับ workflow
| Table | Access | Role |
| --- | --- | --- |
| document_statuses | R | สถานะเอกสาร (06/08/01/02/03/04/05/END) |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{ "statusCode": "06", "statusName": "รอฝ่าย SBP DSA ดำเนินการ" }]
}
```

Errors

- 401

#### API-17 GET /api/v1/workflow-sections

| Item | Requirement |
| --- | --- |
| Purpose | รายการ Section 7 ขั้น - dropdown เลือกตำแหน่ง/ขั้น (หน้า 3.1.8) และตัวกรองตาม section |
| Roles | ทุก role |
| Source | K2 · master section |

Flow:

1. อ่าน workflow_sections ทั้งหมดเรียงตามลำดับ 06->08->01->02->03->04->05
| Table | Access | Role |
| --- | --- | --- |
| workflow_sections | R | ขั้นตอน 06/08/01/02/03/04/05 |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{ "sectionCode": "06", "sectionName": "ฝ่าย SBP DSA" }]
}
```

Errors

- 401

### API Group 4: Master Data (K2 · SRS 3.1.8 / 3.1.9)


#### API-18 GET /api/v1/operators

| Item | Requirement |
| --- | --- |
| Purpose | รายชื่อผู้ปฏิบัติงาน (operator_assignments) พร้อมค้นหา/แบ่งหน้า |
| Roles | 03 User Admin |
| Source | K2 · 3.1.8 |

Flow:

1. query ตามเงื่อนไข (ชื่อ / section / zone)
| Table | Access | Role |
| --- | --- | --- |
| operator_assignments | R | master ผู้ปฏิบัติงาน (เทียบจาก SRS) |

Request

```text
Query: ?q=สมชาย&sectionCode=06&page=1
```

Response

```text
{
  "items": [{
    "operatorAssignmentId": 12,
    "empName": "สมชาย ใจดี",
    "empMail": "somchai@cpall.co.th",
    "sectionCode": "06",
    "zoneCode": "RS"
  }]
}
```

Errors

- 401
- 403

#### API-19 POST /api/v1/operators

| Item | Requirement |
| --- | --- |
| Purpose | เพิ่มผู้ปฏิบัติงานใหม่ (จากหน้าค้นหาพนักงานด้วยแว่นขยาย) |
| Roles | 03 User Admin |
| Source | K2 · 3.1.8 |

Flow:

1. validate พนักงานมีจริง (จากเส้น employees/search)
1. insert + บันทึก audit_logs (ADD)
| Table | Access | Role |
| --- | --- | --- |
| operator_assignments | W | แถวใหม่ |
| audit_logs | W | audit การเพิ่ม |

Request

```text
{
  "empId": "57123",
  "empName": "สมชาย ใจดี",
  "empMail": "somchai@cpall.co.th",
  "sectionCode": "06",
  "zoneCode": "RS"
}
```

Response

```text
201 Created - { "operatorAssignmentId": 31 }
```

Errors

- 409 - พนักงานคนนี้อยู่ใน section นี้แล้ว

#### API-20 PUT /api/v1/operators/{id}

| Item | Requirement |
| --- | --- |
| Purpose | แก้ไขข้อมูลผู้ปฏิบัติงาน |
| Roles | 03 User Admin |
| Source | K2 · 3.1.8 |

Flow:

1. validate: ต้องระบุ reason เสมอ (กติกา SRS)
1. update + บันทึก audit_logs (EDIT · old_value -> new_value · เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| operator_assignments | W | แก้ไข |
| audit_logs | W | audit |

Request

```text
{
  "empMail": "somchai.j@cpall.co.th",
  "zoneCode": "RN",
  "reason": "ปรับพื้นที่รับผิดชอบตามโครงสร้างใหม่"   // บังคับ (SRS)
}
```

Response

```text
200 OK
```

Errors

- 422 - กรุณาระบุเหตุผลการแก้ไขข้อมูล
- 404

#### API-21 DELETE /api/v1/operators/{id}

| Item | Requirement |
| --- | --- |
| Purpose | ลบผู้ปฏิบัติงาน พร้อมบันทึกเหตุผล |
| Roles | 03 User Admin |
| Source | K2 · 3.1.8 |

Flow:

1. ตรวจว่าไม่ถืองานค้างใน workflow_tasks
1. ลบ + บันทึก audit_logs (DELETE + เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| operator_assignments | W | ลบแถว |
| audit_logs | W | audit + เหตุผล |
| workflow_tasks | R | ตรวจงานค้าง |

Request

```text
{ "reason": "ย้ายหน่วยงาน" }
```

Response

```text
204 No Content
```

Errors

- 409 - ยังถืองานค้างอยู่ ต้องแจกงานใหม่ก่อน

#### API-22 GET /api/v1/factors

| Item | Requirement |
| --- | --- |
| Purpose | รายการปัจจัยภายนอก (external_factors) |
| Roles | 03 User Admin |
| Source | K2 · 3.1.9 |

Flow:

1. query ทั้งหมด / ตามคำค้น
| Table | Access | Role |
| --- | --- | --- |
| external_factors | R | master ปัจจัย (เทียบจาก SRS) |

Request

```text
Query: ?q=ถนน
```

Response

```text
{
  "items": [{ "factorCode": "F001", "factorName": "ปิดถนน/ซ่อมถนน", "factorRemark": "..." }]
}
```

Errors

- 401

#### API-23 POST /api/v1/factors

| Item | Requirement |
| --- | --- |
| Purpose | เพิ่มปัจจัยภายนอก - รหัสห้ามซ้ำ (กติกา SRS) |
| Roles | 03 User Admin |
| Source | K2 · 3.1.9 |

Flow:

1. ตรวจ factor_code ไม่ซ้ำ
1. insert + audit_logs
| Table | Access | Role |
| --- | --- | --- |
| external_factors | W | แถวใหม่ |
| audit_logs | W | audit |

Request

```text
{ "factorCode": "F009", "factorName": "คู่แข่งจัดโปรโมชัน", "factorRemark": "" }
```

Response

```text
201 Created
```

Errors

- 409 - รหัสปัจจัยนี้มีอยู่แล้ว

#### API-24 PUT /api/v1/factors/{code}

| Item | Requirement |
| --- | --- |
| Purpose | แก้ไขปัจจัยภายนอก |
| Roles | 03 User Admin |
| Source | K2 · 3.1.9 |

Flow:

1. validate: ต้องระบุ reason เสมอ (กติกา SRS)
1. update + audit_logs (EDIT · old_value -> new_value · เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| external_factors | W | แก้ไข |
| audit_logs | W | audit |

Request

```text
{
  "factorName": "คู่แข่งจัดโปรโมชันใหญ่",
  "reason": "ขยายนิยามให้ชัดเจนขึ้น"   // บังคับ (SRS)
}
```

Response

```text
200 OK
```

Errors

- 422 - กรุณาระบุเหตุผลการแก้ไขข้อมูล
- 404

#### API-25 DELETE /api/v1/factors/{code}

| Item | Requirement |
| --- | --- |
| Purpose | ลบปัจจัยภายนอก (ต้องไม่ถูกใช้ในเอกสารใด) |
| Roles | 03 User Admin |
| Source | K2 · 3.1.9 |

Flow:

1. ตรวจไม่ถูกอ้างใน document_external_factors
1. ลบ + audit_logs
| Table | Access | Role |
| --- | --- | --- |
| external_factors | W | ลบแถว |
| document_external_factors | R | ตรวจการใช้งาน |
| audit_logs | W | audit |

Request

```text
{ "reason": "เลิกใช้" }
```

Response

```text
204 No Content
```

Errors

- 409 - ปัจจัยถูกใช้ในเอกสารอยู่ ลบไม่ได้

#### API-26 GET /api/v1/employees/search

| Item | Requirement |
| --- | --- |
| Purpose | ค้นหาพนักงานจากระบบ HR (popup แว่นขยายในหน้า 3.1.8) |
| Roles | 03 User Admin |
| Source | K2 3.1.8 + master FGI/FCS |

Flow:

1. ค้นจาก employees (ตาราง master ที่ฝั่ง batch ใช้ join อยู่แล้ว)
1. คืนรายการสั้นสำหรับ popup เลือก
| Table | Access | Role |
| --- | --- | --- |
| employees | R | master พนักงาน (โซน master เดิมของ FGI/FCS) |

Request

```text
Query: ?q=สมชาย (ชื่อ / รหัสพนักงาน)
```

Response

```text
{
  "items": [{ "empId": "57123", "name": "สมชาย ใจดี", "mail": "somchai@cpall.co.th", "dept": "SBP DSA" }]
}
```

Errors

- 401

#### API-27 GET /api/v1/menu-permissions

| Item | Requirement |
| --- | --- |
| Purpose | ตาราง matrix สิทธิ์เมนูทั้งหมด (8 role x เมนู) - หน้าจอสิทธิ์การเข้าถึงเมนู |
| Roles | 01 Admin, 02 HQ |
| Source | K2 · 3.1.1 |

Flow:

1. อ่าน menu_permissions ทั้งหมด join menus + roles
1. คืนเป็น matrix ต่อเมนู
| Table | Access | Role |
| --- | --- | --- |
| menu_permissions | R | สิทธิ์ต่อ role (composite PK) |
| menus / roles | R | ชื่อเมนูและ role 00-10 |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "menus": [{
    "menuCode": "M07",
    "menuName": "รายงานสรุปสถานะ",
    "access": { "00": false, "01": true, "02": false, "03": false, "04": true, "05": false, "06": true, "10": false }
  }]
}
```

Errors

- 401
- 403

#### API-28 PUT /api/v1/menu-permissions/{menuCode}

| Item | Requirement |
| --- | --- |
| Purpose | แก้สิทธิ์การเข้าถึงเมนูหนึ่งรายการต่อทุก role - บันทึก audit เสมอ |
| Roles | 01 Admin, 02 HQ |
| Source | K2 · 3.1.1 |

Flow:

1. validate role code อยู่ในเซ็ต 00-10
1. update menu_permissions ของเมนูนั้น
1. บันทึก audit_logs (ผู้แก้ + ค่าเดิม/ใหม่)
| Table | Access | Role |
| --- | --- | --- |
| menu_permissions | W | สิทธิ์ใหม่ต่อ role |
| audit_logs | W | audit การแก้สิทธิ์ |

Request

```text
{
  "access": { "04": true, "06": true }
}
```

Response

```text
200 OK
```

Errors

- 404 - ไม่พบเมนู
- 403

#### API-29 GET /api/v1/roles

| Item | Requirement |
| --- | --- |
| Purpose | รายการ Role ทั้งหมด (ตารางกลุ่มผู้ใช้งานในหน้าจอ 3.1.1 และ dropdown ที่อื่น) |
| Roles | 01 Admin, 02 HQ |
| Source | K2 · 3.1.1 |

Flow:

1. อ่าน roles ทั้งหมดเรียงตาม role_code
| Table | Access | Role |
| --- | --- | --- |
| roles | R | role_code · role_name · role_desc · is_system |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{ "roleCode": "01", "roleName": "Admin", "roleDesc": "ผู้ดูแลระบบ BPM ...", "isSystem": true }]
}
```

Errors

- 401
- 403

#### API-30 POST /api/v1/roles

| Item | Requirement |
| --- | --- |
| Purpose | เพิ่ม Role ใหม่ - ระบบสร้างสิทธิ์เมนูเริ่มต้นเป็น "ไม่มีสิทธิ์" ทุกเมนู |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. validate role_code ไม่ซ้ำ
1. insert roles (is_system = false)
1. insert menu_permissions ทุกเมนู can_access = false
1. บันทึก audit_logs
| Table | Access | Role |
| --- | --- | --- |
| roles | W | role ใหม่ |
| menu_permissions | W | สิทธิ์เริ่มต้น false ทุกเมนู |
| audit_logs | W | audit การเพิ่ม |

Request

```text
{
  "roleCode": "11",
  "roleName": "Zone Viewer",
  "roleDesc": "ดูเอกสารเฉพาะภาคของตน"
}
```

Response

```text
201 Created
```

Errors

- 409 - รหัส Role ซ้ำกับที่มีอยู่
- 403

#### API-31 PUT /api/v1/roles/{roleCode}

| Item | Requirement |
| --- | --- |
| Purpose | แก้ชื่อ/คำอธิบาย Role - ต้องระบุเหตุผล บันทึก audit เสมอ |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. ตรวจ role มีอยู่
1. update roles (role_code ของ role ระบบแก้ไม่ได้)
1. บันทึก audit_logs (ค่าเดิม/ใหม่ + เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| roles | W | ชื่อ/คำอธิบายใหม่ |
| audit_logs | W | audit การแก้ไข |

Request

```text
{
  "roleName": "Report Admin",
  "roleDesc": "สำหรับดูเมนูรายงานทุกภาค",
  "reason": "ขยายขอบเขตการดูรายงาน"
}
```

Response

```text
200 OK
```

Errors

- 404 - ไม่พบ Role
- 403

#### API-32 DELETE /api/v1/roles/{roleCode}

| Item | Requirement |
| --- | --- |
| Purpose | ลบ Role - ลบไม่ได้ถ้าเป็น Role ระบบ (is_system) หรือยังมีผู้ใช้อ้างอยู่ |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. ตรวจ is_system = false และไม่มี user_accounts อ้างถึง
1. ลบ menu_permissions ของ role ทั้งหมด แล้วลบ roles
1. บันทึก audit_logs พร้อมเหตุผล
| Table | Access | Role |
| --- | --- | --- |
| roles | W | ลบ role |
| menu_permissions | W | ลบสิทธิ์ของ role (cascade) |
| audit_logs | W | audit การลบ |

Request

```text
{ "reason": "ยุบรวมกับ Role 04" }
```

Response

```text
204 No Content
```

Errors

- 409 - Role หลักของระบบ (00-10) ลบไม่ได้
- 409 - ยังมีผู้ใช้อยู่ใน Role นี้ ลบไม่ได้
- 403

#### API-33 POST /api/v1/menus

| Item | Requirement |
| --- | --- |
| Purpose | เพิ่มเมนูใหม่เข้าระบบ - สิทธิ์เริ่มต้นเป็น "ไม่มีสิทธิ์" ทุก Role |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. validate ชื่อเมนูไม่ว่าง / menu_group อยู่ในเซ็ต MAIN, MASTER
1. insert menus (running menu_code + sort_order ท้ายกลุ่ม)
1. insert menu_permissions ทุก role can_access = false
1. บันทึก audit_logs
| Table | Access | Role |
| --- | --- | --- |
| menus | W | เมนูใหม่ (menu_group + sort_order) |
| menu_permissions | W | สิทธิ์เริ่มต้น false ทุก role |
| audit_logs | W | audit การเพิ่ม |

Request

```text
{
  "menuName": "รายงานผลชดเชยรายเดือน",
  "menuGroup": "MAIN"
}
```

Response

```text
201 Created
{ "menuCode": "M07" }
```

Errors

- 422 - กรุณาระบุชื่อเมนู
- 403

#### API-34 PUT /api/v1/menus/{menuCode}

| Item | Requirement |
| --- | --- |
| Purpose | แก้ชื่อ/กลุ่ม/ลำดับเมนู - ต้องระบุเหตุผล บันทึก audit เสมอ |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. ตรวจเมนูมีอยู่
1. update menus
1. บันทึก audit_logs (ค่าเดิม/ใหม่ + เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| menus | W | ชื่อ/กลุ่ม/ลำดับใหม่ |
| audit_logs | W | audit การแก้ไข |

Request

```text
{
  "menuName": "รายงานสรุปสถานะ (ใหม่)",
  "sortOrder": 5,
  "reason": "ปรับชื่อให้ตรงรายงานฉบับปรับปรุง"
}
```

Response

```text
200 OK
```

Errors

- 404 - ไม่พบเมนู
- 403

#### API-35 DELETE /api/v1/menus/{menuCode}

| Item | Requirement |
| --- | --- |
| Purpose | ลบเมนูพร้อมสิทธิ์ทุก Role ของเมนูนั้น (cascade) - เมนูระบบลบไม่ได้ |
| Roles | 01 Admin, 02 HQ |
| Source | ใหม่ · หน้าจอ 3.1.1 |

Flow:

1. ตรวจ is_system = false
1. ลบ menu_permissions ของเมนู แล้วลบ menus
1. บันทึก audit_logs พร้อมเหตุผล
| Table | Access | Role |
| --- | --- | --- |
| menus | W | ลบเมนู |
| menu_permissions | W | ลบสิทธิ์ทุก role ของเมนู (cascade) |
| audit_logs | W | audit การลบ |

Request

```text
{ "reason": "ยุบรวมกับเมนูรายงานสรุปสถานะ" }
```

Response

```text
204 No Content
```

Errors

- 409 - เมนูหลักของระบบลบไม่ได้
- 403

#### API-36 GET /api/v1/audit-logs

| Item | Requirement |
| --- | --- |
| Purpose | ประวัติการแก้ไขข้อมูล master แบบหลายรายการ (ใคร · ทำอะไร · ค่าเดิม->ใหม่ · เหตุผล · เมื่อไร) - แผงประวัติท้ายหน้าจอ 3.1.8 / 3.1.9 |
| Roles | 01 Admin, 02 HQ, 03 User Admin |
| Source | K2 · 3.1.8 / 3.1.9 |

Flow:

1. query audit_logs ตาม table_name (+ ref_key ถ้าระบุเฉพาะรายการ)
1. เรียงล่าสุดก่อน แบ่งหน้า
| Table | Access | Role |
| --- | --- | --- |
| audit_logs | R | ประวัติหลายรายการต่อข้อมูล (= MaintainMasterHistory เดิม) |

Request

```text
Query: ?table=operator_assignments&refKey=12&page=1
```

Response

```text
{
  "items": [{
    "actionType": "EDIT",
    "refKey": "12",
    "oldValue": "zoneCode=RS",
    "newValue": "zoneCode=RN",
    "reason": "ปรับพื้นที่รับผิดชอบตามโครงสร้างใหม่",
    "updatedBy": "ภัชริดา ประดิษฐ์ทองใส",
    "updatedAt": "2026-07-02T14:20:00"
  }]
}
```

Errors

- 401
- 403

### API Group 5: System Config (Global) (ใหม่ · system_configs)


#### API-37 GET /api/v1/configs

| Item | Requirement |
| --- | --- |
| Purpose | รายการค่ากำหนดกลางทั้งหมด กรองตามหมวด/คำค้นได้ (หน้าจอ Global Config) |
| Roles | 01 Admin |
| Source | ใหม่ · Global Config |

Flow:

1. query system_configs ตาม category / คำค้น
1. คืนครบทุก field รวม value_type · unit · is_editable
| Table | Access | Role |
| --- | --- | --- |
| system_configs | R | ค่ากำหนดกลางทั้งหมด (ตารางใหม่) |

Request

```text
Query: ?category=WORKFLOW&q=escalation
```

Response

```text
{
  "items": [{
    "configKey": "workflow.escalation_days",
    "category": "WORKFLOW",
    "value": "[30, 45, 60]",
    "valueType": "JSON",
    "unit": "วัน",
    "description": "ลำดับวัน escalation งานค้าง",
    "isEditable": true
  }]
}
```

Errors

- 401
- 403

#### API-38 GET /api/v1/configs/{key}

| Item | Requirement |
| --- | --- |
| Purpose | อ่านค่ากำหนดรายตัว - เส้นที่ทุก service เรียกตอนใช้งานจริง พร้อม cache 5 นาที |
| Roles | ทุก role (อ่าน) / service token |
| Source | ใหม่ · Global Config |

Flow:

1. อ่าน system_configs ด้วย config_key
1. ตอบพร้อม header Cache-Control (TTL 5 นาที) - service ฝั่งเรียก cache ตาม
1. ค่า BOOLEAN/NUMBER/JSON ตอบเป็น typed value ตาม value_type ไม่ใช่ string ล้วน
| Table | Access | Role |
| --- | --- | --- |
| system_configs | R | ค่ารายตัว |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "configKey": "workflow.avp_amount_threshold",
  "value": 100000,
  "valueType": "NUMBER",
  "unit": "บาท"
}
```

Errors

- 404 - ไม่พบ config key นี้
- 401

#### API-39 POST /api/v1/configs

| Item | Requirement |
| --- | --- |
| Purpose | เพิ่มค่ากำหนดใหม่ - key ห้ามซ้ำ และ validate ค่าตาม value_type |
| Roles | 01 Admin |
| Source | ใหม่ · Global Config |

Flow:

1. validate config_key รูปแบบ dot notation และไม่ซ้ำ
1. validate ค่า parse ได้ตาม value_type (NUMBER/BOOLEAN/JSON/CRON)
1. ปฏิเสธค่าที่เป็น secret (รหัสผ่าน/API key ต้องอยู่ Secret Manager)
1. insert + บันทึก audit_logs (ADD)
| Table | Access | Role |
| --- | --- | --- |
| system_configs | W | แถวใหม่ |
| audit_logs | W | audit การเพิ่ม |

Request

```text
{
  "configKey": "report.export_max_rows",
  "category": "DOCUMENT",
  "value": "50000",
  "valueType": "NUMBER",
  "unit": "แถว",
  "description": "จำนวนแถวสูงสุดต่อไฟล์ export"
}
```

Response

```text
201 Created
```

Errors

- 409 - Config Key นี้มีอยู่แล้ว
- 422 - ค่าไม่ตรงกับชนิดข้อมูล (value_type)

#### API-40 PUT /api/v1/configs/{key}

| Item | Requirement |
| --- | --- |
| Purpose | แก้ค่ากำหนด - ต้องระบุเหตุผล · ค่าคงที่ทางธุรกิจ (is_editable=false) แก้ผ่าน API ไม่ได้ |
| Roles | 01 Admin |
| Source | ใหม่ · Global Config |

Flow:

1. ตรวจ is_editable - ค่าคงที่ทางธุรกิจ (รัศมี · วงเงิน 100,000 · เกณฑ์ 60 วัน · เกณฑ์ −10 ตามข้อ 8.2) ตอบ 422
1. validate ค่าใหม่ตาม value_type + ต้องระบุ reason เสมอ
1. update + บันทึก audit_logs (EDIT · old_value -> new_value · เหตุผล)
1. broadcast invalidate cache ให้ทุก service อ่านค่าใหม่ทันที
| Table | Access | Role |
| --- | --- | --- |
| system_configs | W | ค่าใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ + เหตุผล |

Request

```text
{
  "value": "[30, 45, 60]",
  "reason": "เพิ่มขั้นเตือน 45 วันตามมติที่ประชุม"   // บังคับ
}
```

Response

```text
200 OK
```

Errors

- 422 - key นี้เป็นค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้
- 422 - กรุณาระบุเหตุผลการแก้ไขข้อมูล
- 404

#### API-41 DELETE /api/v1/configs/{key}

| Item | Requirement |
| --- | --- |
| Purpose | ลบค่ากำหนด - ลบได้เฉพาะ key ที่ไม่ใช่ค่าระบบ และต้องระบุเหตุผล |
| Roles | 01 Admin |
| Source | ใหม่ · Global Config |

Flow:

1. ตรวจ is_editable = true (ค่าคงที่ทางธุรกิจ/ค่าระบบลบไม่ได้)
1. ลบ + บันทึก audit_logs (DELETE + เหตุผล)
1. broadcast invalidate cache
| Table | Access | Role |
| --- | --- | --- |
| system_configs | W | ลบแถว |
| audit_logs | W | audit + เหตุผล |

Request

```text
{ "reason": "เลิกใช้หลังย้ายไปกำหนดใน job_configs" }
```

Response

```text
204 No Content
```

Errors

- 409 - ค่าระบบ/ค่าคงที่ทางธุรกิจ ลบไม่ได้
- 404

### API Group 6: Email Template (Notification) (ใหม่ · email_templates)


#### API-42 GET /api/v1/email-templates

| Item | Requirement |
| --- | --- |
| Purpose | รายการ 8 email template (EM-01-08) พร้อมสถานะว่าถูกแก้จาก Default หรือยัง (หน้าจอ Email Template) |
| Roles | 01 Admin |
| Source | ใหม่ · Notification |

Flow:

1. query email_templates ทั้ง 8 รหัส
1. join จุดส่งใน flow (status_email_rules) เพื่อแสดงผู้รับ TO/CC ที่ล็อกไว้
1. คืน subject/body ปัจจุบัน + is_customized
| Table | Access | Role |
| --- | --- | --- |
| email_templates | R | เนื้อหา template ทั้งหมด (ตารางใหม่) |
| status_email_rules | R | ผู้รับ TO/CC ที่ล็อกต่อสถานะ |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{
    "templateCode": "EM-01",
    "name": "แจ้งผู้ดำเนินการลำดับถัดไป",
    "subject": "[SBPGI] เอกสารประกันรายได้ {{doc_no}} - {{next_status}}",
    "isCustomized": false
  }]
}
```

Errors

- 401
- 403

#### API-43 GET /api/v1/email-templates/{code}

| Item | Requirement |
| --- | --- |
| Purpose | อ่าน template รายตัว (EM-01-08) พร้อมชุดตัวแปร merge ที่ใช้ได้ในฉบับนั้น |
| Roles | 01 Admin |
| Source | ใหม่ · Notification |

Flow:

1. อ่าน email_templates ด้วย template_code
1. คืน subject/body + รายการตัวแปร merge ที่รองรับ + ผู้รับ TO/CC (อ่านอย่างเดียว)
| Table | Access | Role |
| --- | --- | --- |
| email_templates | R | เนื้อหารายตัว |
| status_email_rules | R | ผู้รับ TO/CC (ล็อก) |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "templateCode": "EM-01",
  "subject": "[SBPGI] เอกสารประกันรายได้ {{doc_no}} - {{next_status}}",
  "body": "<p>เรียน {{next_actor}} ...</p>",
  "variables": ["doc_no", "store_code", "next_status", "doc_url"],
  "lockedRecipients": { "to": "ผู้ดำเนินการลำดับถัดไป", "cc": "ตาม status_email_rules" }
}
```

Errors

- 404 - ไม่พบ template code นี้
- 401

#### API-44 PUT /api/v1/email-templates/{code}

| Item | Requirement |
| --- | --- |
| Purpose | บันทึกเนื้อหา template - แก้ได้เฉพาะ subject/body และตัวแปร · ผู้รับ From/To/Cc แก้ผ่านเส้นนี้ไม่ได้ (ล็อกตาม status_email_rules) |
| Roles | 01 Admin |
| Source | ใหม่ · Notification |

Flow:

1. validate ใช้เฉพาะตัวแปร merge ที่รองรับของ template นั้น
1. ปฏิเสธการแก้ From/To/Cc - ผู้รับกำหนดที่ status_email_rules เท่านั้น
1. update email_templates + set is_customized = true
1. บันทึก audit_logs (EDIT · old -> new · เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| email_templates | W | subject/body ใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ + เหตุผล |

Request

```text
{
  "subject": "[SBPGI] เอกสาร {{doc_no}} - {{next_status}}",
  "body": "<p>เรียน {{next_actor}} ...</p>",
  "reason": "เพิ่มลิงก์เปิดเอกสาร {{doc_url}}"   // บังคับ
}
```

Response

```text
200 OK
```

Errors

- 422 - ใช้ตัวแปร merge ที่ไม่รองรับใน template นี้
- 422 - แก้ผู้รับ From/To/Cc ผ่านเส้นนี้ไม่ได้
- 422 - กรุณาระบุเหตุผลการแก้ไข
- 404

#### API-45 POST /api/v1/email-templates/{code}/reset

| Item | Requirement |
| --- | --- |
| Purpose | รีเซ็ต template ฉบับเดียวกลับเป็น Default (ปุ่ม "รีเซ็ต" รายตัวในหน้าจอ) |
| Roles | 01 Admin |
| Source | ใหม่ · Notification |

Flow:

1. คืน subject/body เป็นชุด Default ของ template นั้น
1. set is_customized = false
1. บันทึก audit_logs (RESET + เหตุผล)
| Table | Access | Role |
| --- | --- | --- |
| email_templates | W | คืนค่า Default |
| audit_logs | W | audit การรีเซ็ต |

Request

```text
{ "reason": "ยกเลิกถ้อยคำที่ทดลองปรับ" }
```

Response

```text
200 OK
```

Errors

- 404 - ไม่พบ template code นี้
- 401

#### API-46 POST /api/v1/email-templates/reset-all

| Item | Requirement |
| --- | --- |
| Purpose | รีเซ็ต template ทั้ง 8 ฉบับกลับเป็น Default พร้อมกัน (ปุ่ม "รีเซ็ตทั้งหมดเป็น Default") |
| Roles | 01 Admin |
| Source | ใหม่ · Notification |

Flow:

1. คืน subject/body ของทุก template เป็นชุด Default
1. set is_customized = false ทุกฉบับ
1. บันทึก audit_logs หนึ่งรายการต่อ template ที่เปลี่ยนจริง
| Table | Access | Role |
| --- | --- | --- |
| email_templates | W | คืนค่า Default ทั้ง 8 |
| audit_logs | W | audit ต่อ template ที่เปลี่ยน |

Request

```text
{ "reason": "ล้างค่าทดสอบทั้งหมดก่อนส่งมอบ" }
```

Response

```text
200 OK
{ "resetCount": 3 }
```

Errors

- 401
- 403

### API Group 7: รายงาน (K2 · SRS 3.1.7)


#### API-47 GET /api/v1/reports/status-summary

| Item | Requirement |
| --- | --- |
| Purpose | รายงานสรุปสถานะ 19 คอลัมน์ - บังคับระบุปี และเอาเฉพาะเอกสารที่มีเลขที่ (กติกา SRS) |
| Roles | 04 / 06 Report Admin |
| Source | K2 · 3.1.7 |

Flow:

1. validate ปี (ไม่ระบุ -> 400)
1. query compensation_documents + compensation_histories ตามเงื่อนไข
1. กรอง result (APPROVE/REJECT/PENDING) จากผลพิจารณาล่าสุดใน consideration_logs - filter "อนุมัติ/ไม่อนุมัติ" หน้า k2-report
1. คืนแบบแบ่งหน้า 19 คอลัมน์ตามหน้าจอ Status Report
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents | R | สถานะเอกสาร |
| compensation_histories | R | ยอด/งวดชดเชย |
| impacted_stores | R | ข้อมูลร้าน |
| consideration_logs | R | ผลพิจารณาล่าสุด (กรองอนุมัติ/ไม่อนุมัติ) |

Request

```text
Query: ?year=2569&month=6&zone=RS&status=END&result=APPROVE&page=1
(result = APPROVE | REJECT | PENDING - อนุมัติ / ไม่อนุมัติ / ยังไม่พิจารณา)
```

Response

```text
{
  "page": 1, "total": 212,
  "items": [{ "docNo": "2569/00098", "storeCode": "00788", "status": "เสร็จสิ้นดำเนินการ", "compensateAmount": 85000.00, ... }]
}
```

Errors

- 400 - กรุณาระบุปีที่ต้องการค้นหา

#### API-48 GET /api/v1/reports/status-summary/export

| Item | Requirement |
| --- | --- |
| Purpose | Export รายงานเป็นไฟล์ Excel เงื่อนไขเดียวกับเส้นค้นหา |
| Roles | 04 / 06 Report Admin |
| Source | K2 · 3.1.7 |

Flow:

1. เงื่อนไขเดียวกับ status-summary
1. สร้างไฟล์ .xlsx แล้ว stream กลับ
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents / compensation_histories | R | ข้อมูลชุดเดียวกับรายงาน |

Request

```text
Query: ?year=2569&month=6&result=APPROVE
(เงื่อนไขชุดเดียวกับเส้นค้นหา รวม result อนุมัติ/ไม่อนุมัติ)
```

Response

```text
200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="status-summary-2569-06.xlsx"
```

Errors

- 400 - ไม่ระบุปี

### API Group 8: Batch Job Admin (FGI/FCS · Jobs 1-10)


#### API-49 GET /api/v1/jobs

| Item | Requirement |
| --- | --- |
| Purpose | รายการ batch job ทั้ง 11 entry points พร้อมสถานะรอบล่าสุด (หน้าจอ Batch Job Console) |
| Roles | 01 Admin |
| Source | FGI/FCS |

Flow:

1. อ่าน job_configs ทั้งหมด
1. join ผลรันล่าสุดจาก job_run_histories
| Table | Access | Role |
| --- | --- | --- |
| job_configs | R | cron + enabled + params (ตารางใหม่) |
| job_run_histories | R | ผลรันล่าสุด |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "items": [{
    "jobNo": "6",
    "name": "ExportImpactStoreToFS",
    "cron": "0 17 * * *",
    "enabled": true,
    "lastRun": { "status": "SUCCESS", "rows": 1254, "startedAt": "2026-07-01T17:00:00" }
  }]
}
```

Errors

- 401
- 403

#### API-50 GET /api/v1/jobs/{jobNo}

| Item | Requirement |
| --- | --- |
| Purpose | รายละเอียด job หนึ่งตัว: พารามิเตอร์ (แยกแก้ได้/คงที่), flow, ตารางที่ใช้ |
| Roles | 01 Admin |
| Source | FGI/FCS |

Flow:

1. อ่าน job_configs + เมทาดาต้า job (จากเอกสาร v4.0)
| Table | Access | Role |
| --- | --- | --- |
| job_configs | R | พารามิเตอร์ปัจจุบัน |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "jobNo": "1",
  "name": "ImportQSSI",
  "params": [
    { "key": "sftpPort", "value": "218", "editable": true },
    { "key": "encoding", "value": "WINDOWS-874", "editable": false }
  ]
}
```

Errors

- 404

#### API-51 PUT /api/v1/jobs/{jobNo}/params

| Item | Requirement |
| --- | --- |
| Purpose | แก้พารามิเตอร์ที่แก้ได้ของ job (เวลารัน, path, เกณฑ์) - ค่าคงที่ทางธุรกิจแก้ผ่าน API ไม่ได้ |
| Roles | 01 Admin |
| Source | FGI/FCS + ข้อ 8.2 |

Flow:

1. validate: แก้ได้เฉพาะ key ที่ editable (เกณฑ์ธุรกิจ เช่น −10, 50, 60 ต้องขออนุมัติตามข้อ 8.2 - ตอบ 422)
1. update job_configs + บันทึก audit_logs
| Table | Access | Role |
| --- | --- | --- |
| job_configs | W | พารามิเตอร์ใหม่ |
| audit_logs | W | audit ผู้แก้ + ค่าเดิม/ใหม่ |

Request

```text
{
  "params": { "cron": "0 18 * * *", "batchSize": 20000 }
}
```

Response

```text
200 OK
```

Errors

- 422 - key นี้เป็นค่าคงที่ทางธุรกิจ แก้ผ่าน API ไม่ได้
- 404

#### API-52 POST /api/v1/jobs/{jobNo}/run

| Item | Requirement |
| --- | --- |
| Purpose | สั่งรัน job นอกรอบ พร้อมระบุงวดข้อมูล - มี guard กันรันซ้อน |
| Roles | 01 Admin |
| Source | FGI/FCS · Runbook 7.1 |

Flow:

1. ตรวจ job เปิดใช้งานอยู่
1. ตรวจไม่มีรอบที่กำลังรัน (สำคัญมากกับ Job 1 - temp table ใช้ร่วม ห้ามซ้อน)
1. enqueue ให้ Batch Scheduler + insert job_run_histories สถานะ RUNNING
1. ตอบ 202 พร้อม runId ให้ FE ตาม poll ได้
| Table | Access | Role |
| --- | --- | --- |
| job_run_histories | W | รอบใหม่สถานะ RUNNING |
| job_configs | R | ตรวจ enabled |

Request

```text
{
  "period": "2026-07"   // งวดข้อมูล (YYYY-MM)
}
```

Response

```text
202 Accepted
{ "runId": 4451 }
```

Errors

- 409 - Job กำลังรันอยู่ ห้ามรันซ้อน
- 422 - job ถูกปิดใช้งาน

#### API-53 PUT /api/v1/jobs/{jobNo}/enabled

| Item | Requirement |
| --- | --- |
| Purpose | เปิด/ปิดการทำงานของ job ตามรอบเวลา |
| Roles | 01 Admin |
| Source | FGI/FCS |

Flow:

1. update job_configs.enabled + audit
| Table | Access | Role |
| --- | --- | --- |
| job_configs | W | ธง enabled |
| audit_logs | W | audit |

Request

```text
{ "enabled": false, "reason": "ปิดชั่วคราวช่วงปิดงบ" }
```

Response

```text
200 OK
```

Errors

- 404

#### API-54 GET /api/v1/jobs/{jobNo}/runs

| Item | Requirement |
| --- | --- |
| Purpose | ประวัติการรันของ job (แท็บประวัติในหน้า Batch Monitor) |
| Roles | 01 Admin |
| Source | FGI/FCS |

Flow:

1. query job_run_histories เรียงล่าสุดก่อน แบ่งหน้า
| Table | Access | Role |
| --- | --- | --- |
| job_run_histories | R | เวลา · แถว · ไฟล์ · ผล · หมายเหตุ |

Request

```text
Query: ?page=1&size=20
```

Response

```text
{
  "items": [{
    "runId": 4451, "status": "SUCCESS", "rows": 48220,
    "file": "mrs1-mrs5 (4 ไฟล์)", "startedAt": "2026-07-01T06:00:00", "durationSec": 252
  }]
}
```

Errors

- 404

### API Group 9: Workflow ภายใน (K2 3.1.4 + FGI/FCS Job 8b)


#### API-55 POST /api/v1/workflows/instances

| Item | Requirement |
| --- | --- |
| Purpose | เปิด workflow ให้รายการที่ผ่าน Gen Flow Gate - เส้นภายในที่ Batch Scheduler เรียกแทนการยิง K2 REST เดิม |
| Roles | service token (ภายใน) |
| Source | แทน K2 StartInstance (Job 8b) |

Flow:

1. ตรวจ service token (ไม่ใช่ JWT ผู้ใช้)
1. ตรวจ Gen Flow Gate เกณฑ์เดิมทุกข้อ: workflow_generation_status=W · branch type FAM/FB1/FC1/FB2/FVB/FVC · opt_dv_user_id ไม่ว่าง · new_store_juristic_name != impacted_store_juristic_name · growth_rate_diff <= −10 · sales_status ∈ {Y,N}
1. ไม่ผ่าน: branch type นอกเซ็ต -> workflow_generation_status=N · กรณีอื่นคง W (ตอบ 422 พร้อมเหตุผล)
1. ผ่าน: สร้าง compensation_documents (ถ้ายังไม่มี) + workflow_instances + workflow_tasks แรก (06) แล้วตั้ง workflow_generation_status=Y
1. ส่งอีเมลสรุปราย DV (พฤติกรรมเดิมของ Job 8b)
| Table | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | R/W | ตรวจ gate + อัปเดต workflow_generation_status W->Y/N |
| compensation_documents | W | เอกสารอัตโนมัติ (ถ้ายังไม่มี) |
| workflow_instances / workflow_tasks | W | เปิด instance + งานแรก |

Request

```text
{
  "impactProcessId": 88123
}
```

Response

```text
201 Created
{
  "instanceId": 501,
  "docNo": "2569/00124",
  "flagGenFlow": "Y"
}
```

Errors

- 422 - ไม่ผ่าน Gen Flow Gate (ตอบเหตุผล + สถานะ W/N ที่ตั้งให้)
- 401 - service token ไม่ถูกต้อง

#### API-56 GET /api/v1/workflows/instances/{id}

| Item | Requirement |
| --- | --- |
| Purpose | สถานะ instance และงานขั้นปัจจุบัน (ใช้ debug/ติดตาม) |
| Roles | 01 Admin / เจ้าของงาน |
| Source | ใหม่ |

Flow:

1. อ่าน workflow_instances + workflow_tasks ปัจจุบัน + เอกสารที่ผูก
| Table | Access | Role |
| --- | --- | --- |
| workflow_instances / workflow_tasks | R | สถานะ + งานปัจจุบัน |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "instanceId": 501,
  "docNo": "2569/00124",
  "status": "ACTIVE",
  "currentTask": { "section": "02", "openedAt": "2026-07-01T09:00:00" }
}
```

Errors

- 404

#### API-57 GET /api/v1/workflows/summary

| Item | Requirement |
| --- | --- |
| Purpose | ตัวเลขเฝ้าระวังตามเอกสาร: นับ workflow_generation_status W/Y/N, จำนวน start ล้มเหลว, งานค้างต่อขั้น |
| Roles | 01 Admin |
| Source | FGI/FCS · Monitoring 7.4 |

Flow:

1. aggregate จาก fgi_impact_stores + workflow_instances/workflow_tasks
| Table | Access | Role |
| --- | --- | --- |
| fgi_impact_stores | R | นับ W/Y/N |
| workflow_tasks | R | งานค้างต่อ section |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "genFlow": { "W": 12, "Y": 58, "N": 4 },
  "failedStarts": 0,
  "openTasksBySection": { "06": 24, "02": 7 }
}
```

Errors

- 401

### API Group 10: Interface & Dashboard (FGI/FCS · tracking / watchdog)


#### API-58 GET /api/v1/interfaces/tracking

| Item | Requirement |
| --- | --- |
| Purpose | สถานะการรับ-ส่งไฟล์กับระบบภายนอก (interface_transactions ใหม่ แทน FGI_CONFIRM_RECEIVE_DATA) |
| Roles | 01 Admin |
| Source | FGI/FCS |

Flow:

1. query ตาม dataName / สถานะค้าง / ช่วงเวลา แบ่งหน้า
| Table | Access | Role |
| --- | --- | --- |
| interface_transactions | R | tracking typed FK (ตารางใหม่) |

Request

```text
Query: ?dataName=COMPENSATE_INIT_I&pending=true&page=1
```

Response

```text
{
  "items": [{
    "trackingId": 9912,
    "dataName": "COMPENSATE_INIT_I",
    "docNo": "2569/00098",
    "sentAt": "2026-06-30T17:02:00",
    "returnCode": null
  }]
}
```

Errors

- 401

#### API-59 POST /api/v1/interfaces/sta/ack

| Item | Requirement |
| --- | --- |
| Purpose | Callback ให้ระบบ STA ยิงตอบรับ (ACK) ตรง - แทนการรออัปเดต return_code ฝั่งเดียว |
| Roles | API key ของระบบ STA |
| Source | ใหม่ (เสริม Job 10) |

Flow:

1. ตรวจ API key เฉพาะของ STA
1. update interface_transactions.returnCode + receiveDate
1. รายการหายจากจอ pending-ack ทันที (watchdog Job 10 ยังคงเป็น safety net)
| Table | Access | Role |
| --- | --- | --- |
| interface_transactions | W | บันทึก ACK |

Request

```text
{
  "trackingId": 9912,
  "returnCode": "W",
  "receiveDate": "2026-07-02T08:15:00"
}
```

Response

```text
200 OK
```

Errors

- 401 - API key ไม่ถูกต้อง
- 404 - ไม่พบ tracking

#### API-60 GET /api/v1/interfaces/pending-ack

| Item | Requirement |
| --- | --- |
| Purpose | รายการ ACK ค้างเกิน 1 วัน (เกณฑ์เดียวกับ watchdog) - ใช้ทั้งหน้า dashboard และอีเมลเตือน |
| Roles | 01 Admin |
| Source | FGI/FCS · Job 10 |

Flow:

1. เกณฑ์เดิมของ Job 10: returnCode IS NULL · interface แบบไฟล์ · อายุ >= 1 วัน
1. เฉพาะ dataset ฝั่ง STA (COMPENSATE_INIT_I / COMPENSATE_APPROVE_I)
| Table | Access | Role |
| --- | --- | --- |
| interface_transactions | R | รายการค้าง |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "count": 2,
  "items": [{ "dataName": "COMPENSATE_INIT_I", "docNo": "2569/00098", "ageDays": 2 }]
}
```

Errors

- 401

#### API-61 GET /api/v1/dashboard/summary

| Item | Requirement |
| --- | --- |
| Purpose | ตัวเลขหน้า Dashboard: งานค้าง, ร้านประกันรายได้เดือนนี้, ยอดชดเชย, ข้อมูลผิดปกติ + ข้อมูลกราฟ |
| Roles | ทุก role |
| Source | K2 (หน้าหลัก) |

Flow:

1. aggregate จากเอกสาร + งานค้าง + ผลชดเชยเดือนปัจจุบัน
1. cache 5 นาที
| Table | Access | Role |
| --- | --- | --- |
| compensation_documents / workflow_tasks | R | งานค้าง + สถานะ |
| compensation_histories | R | ยอดชดเชยรายเดือน |
| fgi_impact_sales_summaries | R | จำนวนข้อมูลผิดปกติ |

Request

```text
(ไม่มี body)
```

Response

```text
{
  "waitingTasks": 24,
  "storesThisMonth": 342,
  "compensationThisMonth": 8420000.00,
  "abnormalStores": 5,
  "chart": { "monthly": [ ... ] }
}
```

Errors

- 401

---


# 4. Non-Functional Requirements

| Category | Requirement |
| --- | --- |
| Performance | รองรับผู้ใช้พร้อมกันเฉลี่ย 80 คน สูงสุด 100 คน; interaction ปกติตอบภายใน 30 วินาทีตาม SRS เดิม; API list/report ต้องกำหนด SLA แยกก่อน production |
| Availability | บริการ 7x24 ยกเว้น maintenance window; Batch Scheduler ต้อง resume/reconcile หลัง restart |
| Reliability | Transaction ที่สำเร็จต้อง durable; error ต้องไม่เขียนข้อมูลบางส่วน; file interface ต้อง reconcile row/file/tracking |
| Security | SSO/AD หรือ LDAP, JWT อายุจำกัด, refresh token revoke, least privilege, secrets vault, TLS, API key rotation และ server-side RBAC |
| Auditability | บันทึก login, document mutation, workflow action, master change, job action และ external callback พร้อม actor/time/correlation id |
| Usability | รองรับ Chrome รุ่นองค์กร, ภาษาไทย, keyboard focus, responsive table/modal และข้อความ validation ตรงตาม SRS |
| Maintainability | แยก FE/BE, OpenAPI 3.0 contract, configuration versioning, migration scripts และ automated tests สำหรับ business rules |
| Portability | Deployment ต้องไม่ผูก credential/path กับเครื่อง; ใช้ environment/config/secret manager |
| Backup/Recovery | กำหนด RPO/RTO, backup DB/config/object files และทดสอบ restore อย่างน้อยตามรอบองค์กร |
| Observability | Metrics/log/trace สำหรับ API, batch, workflow, interface ACK, queue lag และ e-mail failure พร้อม alert threshold |


# 5. Acceptance and Traceability


## 5.1 High-priority acceptance criteria

- เอกสารหนึ่งรายการ trace ได้ครบ impact_process_id -> doc_no -> instance_id -> task_id
- กฎ route 100,000 บาททำงานถูกต้องทั้งค่าต่ำกว่า เท่ากับ และสูงกว่า
- ผลรวม % ชดเชย 100% ถูกตรวจทั้ง FE และ BE
- ร้านยอดขายไม่ครบ 60 วันถูก flag ใน inbox/report และมีเหตุผลตรวจสอบย้อนกลับ
- Jobs 1-10/8b รันซ้ำตาม runbook โดยไม่สร้างข้อมูลซ้ำหรือสูญหาย
- API 61 เส้นผ่าน authentication/authorization, validation, audit, idempotency และ error contract
- ข้อมูล export/import ทุก interface ผ่าน golden-file test เรื่อง encoding/date/delimiter/field count
- หน้าจอและ Excel report ให้ผลตรงกันภายใต้ filter เดียวกัน

## 5.2 Traceability matrix

| ID | Screen / Artifact | Scope | SRS section |
| --- | --- | --- | --- |
| FLOW-01 | Flow FGI/FCS | FGI/FCS batch pipeline A-E | 3.1, 3.3 |
| FLOW-02 | Flow K2 | K2 approval workflow | 3.1.3-3.1.4 |
| FLOW-03 | Integrated Target Flow | Integrated target architecture/flow | 2.2, 3.1 |
| DB-01 | Database FGI/FCS | FGI/FCS detailed entities | 3.2.3 |
| DB-02 | Database K2 | K2 detailed entities | 3.2.4 |
| DB-03 | Target Database Schema | 34-table target schema | 3.2.1-3.2.2 |
| JOB-01 | Batch Job Console | 11 entry points and console | 3.3 |
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
| K2-12 | Email Template | Notification email templates | SCR-12 |
| API-01 | API Specification | 61 REST endpoints | 3.5 |


# 6. Open Items and Decisions Required

| ID | Topic | Decision required |
| --- | --- | --- |
| OPEN-01 | Document year | Prototype/CLAUDE use พ.ศ. 2569/xxxxx แต่เอกสาร inventory บางส่วนระบุ ค.ศ.; ต้องยืนยัน canonical storage/display |
| OPEN-02 | Abnormal screen | หน้าจอข้อมูลผิดปกติและ 2 API endpoints ถูก comment; ต้องตัดสินใจ keep/drop และปรับ role 05 |
| OPEN-03 | Job 8b schedule | เวลา scheduler จริงต้องยืนยันกับ Operations |
| OPEN-04 | NULL growth_rate | Target เสนอรอตรวจสอบแทน auto-accept; ต้องมี Business sign-off |
| OPEN-05 | Legacy date routing | เงื่อนไขร้านก่อน/หลัง 1/10/2557 จาก flow เดิมยังต้อง verify กับ SRS v3.1 |
| OPEN-06 | NFR SLA/RPO/RTO | SRS เดิมให้ค่ารวมระดับสูง; ต้องกำหนด SLA API/report/batch และ RPO/RTO production |
| OPEN-07 | File retention | กำหนด retention, encryption และ purge สำหรับ attachment/interface/archive |
| OPEN-08 | Exact permission matrix | ยืนยัน menu/master permission ต่อ role ก่อน implementation backend |


# 7. Appendices


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


## 7.2 References

- RDM-SRS ประกันรายได้-K2.pdf - Version 3.1
- FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf
- RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md
- ประกันรายได้-K2-รายการหน้าจอ.md
- Workflow design documents and Flow screens
- Database design documents and Database screens
- Batch Job, API Specification, Global Config, Email Template, K2 screens and shared shell