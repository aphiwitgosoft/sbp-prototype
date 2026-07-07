# Domain — กติกาธุรกิจระบบประกันรายได้ (ตาม SRS v3.1 + Batch v4.0)

> ข้อมูลในไฟล์นี้คือกติกาที่ **เสถียร/ห้ามเปลี่ยน** ตามเอกสารอ้างอิง
> การออกแบบระบบใหม่ที่ยังปรับได้ (schema, flow, API) ให้ดู living docs: `database.md` / `workflow.md` — ถ้าขัดแย้งกัน living docs ชนะ

## ภาพรวมธุรกิจ

ชดเชยรายได้ให้ร้าน 7-Eleven **Store Partner (SP)** ที่ยอดขายตกเพราะมี 7-Eleven สาขาใหม่เปิดในรัศมีกระทบ
**1 กม.** (กทม.+ปริมณฑล) / **2 กม.** (ต่างจังหวัด) · "K2" = แพลตฟอร์ม BPM เดิม · ระบบใหม่ = **SBPGI** (รวม EAI + K2 เข้าระบบเดียว)

## ค่าคงที่ธุรกิจ (ห้ามเปลี่ยนโดยไม่มี business sign-off)

- เลขที่เอกสาร `YYYY/xxxxx` — **ปี พ.ศ.** เช่น `2569/00123` (running เริ่ม 00001)
- วงเงิน AVP: ชดเชย **> 100,000 บาท ต้องผ่าน AVP (03)** · ≤ 100,000 ข้ามไปฝ่ายบัญชี SBP (04)
- **%ชดเชยของร้านเปิดใหม่ทุกร้านในเอกสารรวมกันต้อง = 100%**
- ข้อมูลยอดขาย **< 60 วัน = "ผิดปกติ"** → แถวแดง `tr.flag-red` (เป็น flag ของข้อมูล **ไม่ใช่สถานะ workflow**)
- หน้าต่างคำนวณยอดขาย **4 × 15 วัน** · outlier เมื่อ |sales_diff| **≥ 50** แบบจับคู่
- Gen Flow Gate (เกณฑ์เปิด workflow — คงเดิมทุกข้อ): workflow_generation_status=W · branch type FAM/FB1/FC1/FB2/FVB/FVC · DV ไม่ว่าง · juristic ต่างกัน · growth_rate_diff ≤ −10 · sales_status ∈ {Y,N}
- QSSI ต้องครบ **6 หมวด (8, 9, 12, 1, 10, 16)** ก่อนส่งผลเข้า Statement
- ไฟล์แนบ ≤ **5MB/ไฟล์** · ชนิดที่รับ: vsd,dwg,afp,pdf,mda,zip,wav,mp3,gif,jpg,tif,tiff,htm,html,txt,xml,mpg,mov,ivs,doc,docx,xls,xlsx,pps,ppt,pot,csv

## Workflow 7 ขั้น (section_code)

**06 → 08 → 01 → 02 → 03 → 04 → 05**

| Section | ตำแหน่ง | บทบาทหลัก |
|---|---|---|
| 06 | ฝ่าย SBP DSA (Manager Franchise) | จุดเริ่ม · ไม่ชดเชย/หยุดชดเชย = จบ · ส่งต่อได้หลายทาง |
| 08 | เจ้าหน้าที่ SBP DSA (Officer Franchise) | มี view **คำนวณเงินชดเชย** (เฉพาะขั้นนี้) |
| 01 | ฝ่ายส่งเสริมธุรกิจฯ (Manager OPT) | แก้ร้านเปิดใหม่/คู่แข่ง/ปัจจัยภายนอกได้ (%รวม = 100%) |
| 02 | GM ส่งเสริมธุรกิจฯ (GM OPT) | แยกเส้นตามวงเงิน 100,000 |
| 03 | ผู้บริหารสำนักบริหาร SBP (AVP OPT) | เฉพาะยอด > 100,000 (แม้ "ไม่ชดเชย" ก็ต้องผ่านตามวงเงิน) |
| 04 | ฝ่ายบัญชี SBP (Manager Account Franchise) | ตรวจการเงิน |
| 05 | บัญชีปฏิบัติการภาค (Operation Account) | "บัญชีภาคอนุมัติ" = **จบ workflow** |

**สถานะเอกสาร 8 ค่า** — "รอ\<ผู้ดำเนินการ\>ดำเนินการ" หนึ่งค่าต่อ section + "เสร็จสิ้นดำเนินการ"
inbox ของแต่ละ role = เอกสารสถานะ "รอ\<role ตัวเอง\>ดำเนินการ" ค่าเดียว
ตาราง transition เต็ม (ผลพิจารณา → สถานะถัดไป ต่อ section) อยู่ใน `workflow.md` §สถานะเอกสารและเส้นทางพิจารณา

**Validation ปุ่มส่งดำเนินการ** — ต้องเลือกผลพิจารณาอย่างน้อย 1 ข้อ มิฉะนั้น popup verbatim:
"ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูล ก่อนกดส่งดำเนินการ" · กรณีเลือกไม่ชดเชย/ส่งฝ่ายบัญชี ความคิดเห็นเป็น required · **ปุ่มบันทึกไม่ validate**

## 8 Role กลุ่มสิทธิ์ (SRS 3.1.1 — หน้า k2-permissions.html)

| Code | Role | หมายเหตุ |
|---|---|---|
| 00 | Default | ผู้ดำเนินการในแบบฟอร์ม |
| 01 | Admin | เห็นทุกเมนู จัดการได้ทุกอย่าง |
| 02 | HQ | HQ Support |
| 03 | User Admin | user ที่เป็น admin ระบบ |
| 04 | Report Admin | เมนูรายงาน |
| 05 | Assign Job | แจกงานที่เมนูข้อมูลผิดปกติ (ที่มาของหน้า k2-list-abnormal) |
| 06 | Report Admin Special | เรียกดูเอกสารทั้งหมด |
| 10 | UserViewer | ผู้มีสิทธิ์ดูเอกสาร (Role 01/02 บริหารจัดการ) |

## ข้อเท็จจริง SRS ที่พลาดบ่อย

- ภาคมี **8 ค่า**: `BE BN BS BW RC RE RN RS` — **มี RC ไม่มี RW**
- ประเภทร้านในเงื่อนไขค้นหา: FR Type A / B / C / พนักงาน (4 ค่า multi-select) — ประเภทเต็ม 8 ชนิดอยู่เฉพาะรายละเอียดเอกสาร
- รายงานสรุปสถานะ (3.1.7): ต้องระบุปี · ออกเฉพาะรายการที่มีเลขที่เอกสาร · ผลลัพธ์ 19 คอลัมน์ · Export Excel
- แก้ master (3.1.8/3.1.9) ต้องระบุ**เหตุผลการแก้ไข** และลงประวัติ (`audit_logs` — เดิม MaintainMasterHistory)
- รหัสปัจจัยภายนอกห้ามซ้ำ
- สถานะแจกงานของหน้าข้อมูลผิดปกติ (ผิดปกติ → แจกงานแล้ว → แก้ไขแล้ว) เป็น**คนละชุด**กับสถานะเอกสาร 8 ค่า

## Email Templates (plan-email.html — 8 ฉบับ)

TO/CC ของ EM-01–03 ยึด `status_email_rules` (SRS 3.1.5) · **เนื้อหา/ถ้อยคำเป็นข้อเสนอระบบใหม่ beyond SRS** · ส่งจาก Notification Service กลาง UTF-8 (แทน TIS-620)

| Code | ส่งเมื่อ | ผู้รับ |
|---|---|---|
| EM-01 | เอกสารเปลี่ยนสถานะ (ส่งดำเนินการ) | ผู้ดำเนินการ step ถัดไป |
| EM-02 | จบ workflow (ไม่ชดเชย/หยุด/บัญชีภาคอนุมัติ) | ผู้เกี่ยวข้องทั้งหมด |
| EM-03 | ถูกส่งกลับ (back-flow) | ผู้ถูกส่งกลับหา + CC ผู้ส่งกลับ |
| EM-04 | เตือนงานค้างรายสัปดาห์ (จันทร์ 10:00 แก้ได้) | ผู้มีงานค้าง (จาก workflow_tasks) |
| EM-05 | Escalation งานค้าง 30/45/60 วัน | หัวหน้า Section / GM OPT |
| EM-06 | สรุปเปิด workflow ราย DV (เดิม Job 8b) | DV/GM user |
| EM-07 | Batch job จบด้วย Error (Jobs 1–10) | ผู้ดูแลระบบ (config ต่อ job) |
| EM-08 | Watchdog ACK จาก STA ค้าง ≥ 1 วัน (Job 10, 07:00) | ผู้ดูแลระบบ |

EM-04/05 รับพฤติกรรมมาจาก Approve Flow เดิม (จุด 10.1, 20.2, 20.3, 30.1, 70.1, 80.1, 110.2)

## ระบบใหม่ SBPGI — จุดยึดสั้น ๆ (รายละเอียด = living docs)

- **รวม EAI + K2 เข้า SBPGI**: ตัดไฟล์ภายใน `BPM06001O_/2O_/3O_` (Jobs 7/8/9) และ K2 REST StartInstance (Job 8b) → Document Service เขียน DB ตรง + Workflow Engine ภายใน
- Interface ภายนอก **คงเดิม** (ระบบของทีมอื่น): QSSI (SFTP) · ALLMAP (SQL Server) · IAS/MIS (ไฟล์ AMS06001O/I) · STA (FRBC0001 + ACK, เพิ่ม `POST /interfaces/sta/ack`) · SMTP
- Flow 12 ขั้น 4 Stage (A รับข้อมูล Jobs 1–5 · B สร้างเอกสาร+เปิด workflow · C พิจารณา 7 ขั้น · D ส่งออก+watchdog Jobs 6/10) → `workflow.md`
- Schema 34 ตาราง 3 โซน (A=FGI/FCS · B=K2 docs/workflow · C=shared master/config) + Data Spine 4 ID (`impact_process_id` → `doc_no` → `instance_id` → `task_id`) → `database.md`
- P0 สำคัญ: ครอบ Job 4 ด้วย transaction · ย้าย credential ไป Secret Manager · ห้ามเก็บ secret ใน `system_configs`
