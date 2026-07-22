# Workflow / Flow — FGI/FCS + K2 (ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุป flow การทำงานต้นทางถึงปลายทางของระบบใหม่ เทียบกับระบบเดิม
> **แหล่งอ้างอิงหลัก:** `plan-flow.html` (หน้า Flow FGI/FCS + K2) · `old-flow.png` (sequence diagram ระบบเดิม) · `new-flow.png` (sequence diagram ระบบใหม่) · `Flow ประกันรายได้.png` (BPMN approve flow ระบบเดิม)
> **อ้างอิงประกอบ:** `flow-fgi.html`, `k2-flow.html`, `job-batch.html`, เอกสาร Batch v4.0, SRS ประกันรายได้-K2 v3.1 (หน้า 30–38: ผลพิจารณาต่อ role), `workflow_status_document.md` (ตารางสถานะ/อีเมล)
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง flow หรือ workflow ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-flow.html` ให้ตรงกัน

## แนวคิดหลักของระบบใหม่

**รวม EAI และ K2 เข้าเป็นส่วนหนึ่งของ SBPGI** — งาน FGI/FCS batch ทำงานร่วมกับงานเอกสาร/workflow ของ K2 ในระบบเดียว **โดยไม่ผ่าน EAI อีกต่อไป**

เปรียบเทียบ lane ใน sequence diagram:

| | Lanes |
|---|---|
| **ระบบเดิม** (`old-flow.png`) | AllMap · SBPGI · MIS · **EAI** · STA · SAP · **K2** (7 lanes) |
| **ระบบใหม่** (`new-flow.png`) | AllMap · SBPGI · MIS · STA · SAP (5 lanes) |

สิ่งที่หายไปจากภาพระบบใหม่:
- **par block "Job Export data"** ทั้งก้อน — Jobs `FGI_ExportImpactStoreToBPM.sh` / `FGI_ExportNewStoreToBPM.sh` / `FGI_ExportCompetitorToBPM.sh` (17:30 วันที่ 7–31) ที่วางไฟล์ `BPM06001O_` / `BPM06002O_` / `BPM06003O_` ให้ EAI → **ตัดทิ้ง**
- **lane K2** — ขั้น "ดึงข้อมูลจากไฟล์", "นำเข้าข้อมูลร้านค้าที่ได้รับผลกระทบ" และการยิง `/fgiService/confirmDataFromBPM` กลับมา → กลายเป็น **self-step ภายใน SBPGI** (ในภาพใหม่ label ขึ้นต้นด้วย "(K2)")

สิ่งที่**คงเดิม**ในทั้งสองภาพ (interface กับระบบภายนอกของทีมอื่น):
- AllMap → SBPGI: ส่งข้อมูลร้านค้าที่ได้รับผลกระทบ
- opt: STA → SBPGI ผ่าน API `/fgiService/updateCompensateFromFS` (กรณีร้านได้รับผลกระทบแต่ไม่ได้ส่งข้อมูลสาขามาให้คำนวณ และต้องชดเชยย้อนหลัง)
- SBPGI ↔ MIS: ไฟล์ `AMS06001O_` (Job FGI_ExportImpactStoreToAMS, 16:00 วันที่ 7–16) / `AMS06001I_` (Job FGI_ImportImpactStoreSale.sh, 16:30 วันที่ 7–16)
- SBPGI → STA: ไฟล์ `FRBC0001_` (Job FGI_ExportImpactStoreToSTA.sh, 17:00 ทุกวัน)
- STA alt 3 กรณี: **Approve = A** → ตรวจสอบยอดอนุมัติ + บันทึกบัญชีไป SAP · **Stop Flow = S** · **Initial = I** → ตั้ง Flow + วางไฟล์ `RT040035`, `RT040078` + API `updateCompensateFromFS` (ยอดศูนย์ = Z, ยอดไม่เท่ากับศูนย์ = W)
- opt Adjust: STA → SBPGI ส่งข้อมูล Adjust เงินชดเชยประกันรายได้

> **หมายเหตุ:** ในภาพ new-flow ยังคงเห็น `/fgiService/confirmDataFromBPM` เป็นขั้นภายใน SBPGI — เมื่อไม่มีการส่งไฟล์ข้ามระบบแล้ว ขั้นนี้เหลือความหมายเป็นการอัปเดตสถานะ "รับข้อมูลเข้าระบบเอกสารแล้ว" ภายใน ไม่ใช่ API ข้ามระบบอีกต่อไป

## สถาปัตยกรรมใหม่ — แยก Frontend / Backend

```
Frontend (Web SPA — ใช้หน้าจอ prototype ชุดนี้เป็น spec)
        │  REST API /api/v1 · JSON + JWT · 62 เส้น 10 กลุ่ม (ดู plan-api.html)
        ▼
Backend Services
  ├─ Auth & RBAC            (K2 · SRS 3.1.1)  JWT · Role 00–10 · สิทธิ์เมนูต่อ Role
  ├─ Document & Compensation (K2 · SRS 3.1.6)  เอกสาร YYYY/xxxxx · คำนวณชดเชย · แนบไฟล์
  ├─ Workflow Engine ภายใน   (K2 · SRS 3.1.4)  5 ขั้น 06→08→01→02→03 · กฎ 100,000 — แทน K2 REST (Job 8b) · **ตัดขั้นบัญชี 04/05 ตาม SDD v7.5**
  ├─ Batch Scheduler         (FGI/FCS)         Jobs 1–10 · คง cron เดิม · พารามิเตอร์แก้ได้ · กันรันซ้อน
  ├─ Interface Service       (FGI/FCS)         SFTP/ไฟล์/ACK · QSSI · IAS · STA · encoding ต่อ interface
  └─ Report & Notification   (K2 3.1.5/3.1.7 + FGI)  รายงาน 19 คอลัมน์ + **รายงานตรวจสอบประกันรายได้ (SBP Mall) — Preview + Export CSV to Batch (SDD v7.5)** · อีเมลตามสถานะ (UTF-8 แทน TIS-620)
        │
        ▼
Database รวม — โซน A (FGI/FCS) · B (K2) · C (Shared)   → ดู database.md
        │  SFTP / ไฟล์ / DB Link (กลไกเดิมกับระบบภายนอก)
        ▼
QSSI (SFTP รายเดือน, Job 1) · ALLMAP (SQL Server, Jobs 2–3) · IAS/MIS (ไฟล์ยอดขาย, Jobs 4–5) · STA (FRBC0001 + ACK, Jobs 6/10) · SMTP
```

**จุดเปลี่ยนสำคัญ:** ไม่มี BPM/K2 engine ภายนอกอีกต่อไป — การเปิดและเดิน workflow ทำโดย Workflow Engine ใน Backend เอง (แทนไฟล์ BPM06001O/2O/3O + K2 REST StartInstance ของ Jobs 8/8b/9) · interface กับระบบภายนอก (QSSI, ALLMAP, IAS, STA) คงกลไกไฟล์/SFTP เดิมเพราะเป็นระบบของทีมอื่น

**สัญญากลางที่ผูกกับ workflow:** ดู `LLDD/BE/LLDD-BE-API-Common-Contracts.md` และ `LLDD/FE/LLDD-FE-Integration-Contracts.md` ก่อน implement ทุกจุดที่เรียก workflow API — `/documents/{docNo}/actions` รับ `{result, comment}` โดย result เป็น 6-enum ไทย verbatim และคืน `{statusCode, nextSection, message}`; positive path คือ `06→08→01→02→03→99` โดย `99` = เสร็จสิ้นและ `nextSection=null` (Section 02 ยอด ≤100,000 จบที่ 99); `/workflows/instances` ใช้ service token และ Gen Flow Gate W/Y/N เป็นเจ้าของโดย BE Workflow Engine

## Flow ต้นทางถึงปลายทาง (12 ขั้น · เดือนละ 1 รอบใหญ่)

### Stage A — รับและวิเคราะห์ข้อมูลผลกระทบ · Jobs 1–5

1. **นำเข้าคะแนน QSSI รายเดือน** (FGI/FCS · Job 1) — SFTP จาก QSSI (4 ไฟล์ mrs*) → dedup + จับคู่หมวด → `fcs_qssi_scores` · งวด DB = เดือนก่อนหน้า (off-by-one โดยตั้งใจ)
2. **นำเข้าคู่ร้านถูกกระทบ + ร้านคู่แข่ง** (FGI/FCS · Jobs 2–3) — ทุกวันที่ 7 เวลา 07:00 จาก ALLMAP (SQL Server) → `fgi_impact_stores` (กฎ DENY/ON_PROCESS → W/N/P) และ `fgi_impact_competitors`
3. **ขอยอดขายรายวันจาก IAS** (FGI/FCS · Job 4) — วันที่ 7–16 เวลา 16:00 · เงื่อนไขอายุร้าน 12 เดือน 15 วัน / +16 วัน → ไฟล์ `AMS06001O` · ระบบใหม่ครอบด้วย transaction (แก้ P0 auto-commit)
4. **รับยอดขาย + คำนวณ Growth Rate** (FGI/FCS · Job 5) — 16:30 รับ `AMS06001I` → `sales_transactions` → คำนวณ sales_diff 4 หน้าต่าง × 15 วัน (outlier |sales_diff| ≥ 50) → `sales_status` Y/N · ระบบใหม่เพิ่ม review case เมื่อ growth_rate_diff เป็น NULL (แก้ P1 auto-accept)

### Stage B — เชื่อม FGI/FCS เข้าสู่ระบบเอกสารและ Workflow (จุดที่เปลี่ยนกลไก)

5. **สร้างเอกสารประกันรายได้อัตโนมัติ** (FGI/FCS → K2 · **เปลี่ยนกลไก**) — เดิม: Jobs 7/8/9 เขียนไฟล์ BPM06003O/BPM06001O/BPM06002O ส่ง SFTP ผ่าน EAI ให้ BPM · ใหม่: **Document Service สร้าง `compensation_documents` (เลขที่ YYYY/xxxxx) + `document_new_stores` + `document_competitors` ตรงใน DB โซนเดียวกัน — ไม่มีไฟล์ ไม่มี SFTP ภายใน**
6. **เปิด Workflow ตาม Gen Flow Gate** (FGI/FCS Job 8b → K2 · **เปลี่ยนกลไก**) — เกณฑ์คงเดิมทุกข้อ: คู่ร้านผ่านกฎรัศมี ≤1 กม.(กทม./ปริมณฑล) หรือ ≤2 กม.(ต่างจังหวัด) · workflow_generation_status=W · branch type FAM/FB1/FC1/FB2/FVB/FVC · DV ไม่ว่าง · juristic ต่างกัน · growth_rate_diff ≤ −10 · sales_status ∈ {Y,N} — เดิมยิง K2 REST StartInstance / ใหม่เรียก `POST /workflows/instances` ภายในด้วย service token; ผ่าน gate ตั้ง Y; fail ถาวร (branch type นอกเซ็ต, ระยะทางเกิน, DV หาย, นิติบุคคลเดียวกัน หรือ growth > −10) ตั้ง N; เฉพาะ distance/juristic/growth เป็น NULL หรือ sales_status ยังไม่พร้อมจึงคง W เพื่อ rerun

### Stage C — ผู้ใช้ตรวจสอบและอนุมัติ · Section 06–03 (workflow 5 ขั้นของ K2)

7. **ขั้น 1–2: ฝ่าย SBP DSA ตรวจสอบ + คำนวณเงินชดเชย** (K2 · Section 06 → 08) — ผู้ใช้ทำงานบน FE (หน้างานรอดำเนินการ / เอกสารร้านถูกกระทบ) · เปิดเอกสารด้วย `GET /documents/{docNo}` และดูยอดขายรายวันเพิ่มเติม (4 หน้าต่าง × 15 วัน) ผ่าน `GET /documents/{docNo}/sales` · ส่งพิจารณาด้วย `POST /documents/{docNo}/actions` payload เดียว `{result, comment}` โดย `result` เป็น 6-enum verbatim: เห็นควรชดเชย / เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้ / ส่งฝ่ายส่งเสริมธุรกิจ SBP / ส่งเจ้าหน้าที่ SBP DSA / ส่งกลับ · บันทึก `consideration_logs` + อีเมลตาม `status_email_rules`
8. **ขั้น 3: ฝ่ายส่งเสริมธุรกิจฯ ปรับข้อมูล** (K2 · Section 01) — แก้ไขร้านเปิดใหม่ / ร้านคู่แข่ง (เลือกจาก master `GET /competitors`) / ปัจจัยภายนอก (`GET /factors`) (**%ชดเชยรวมต้อง = 100%**) บันทึกด้วย `PUT /documents/{docNo}` แล้วส่งพิจารณาต่อ หรือส่งกลับ (back-flow)
9. **ขั้น 4–5: GM → AVP ตามวงเงิน** (K2 · Section 02 → 03) — **ยอดชดเชย > 100,000 บาท ต้องผ่าน AVP (03) แล้วจบงาน · ≤ 100,000 จบที่ GM (02)** — ไม่มีขั้นบัญชีในระบบแล้ว (ตัด 04/05 ตาม SDD v7.5)
10. **บัญชีตรวจสอบนอก workflow** (SDD v7.5 · **เปลี่ยนกระบวนการ**) — ยกเลิกหน้าจอ Approve ของบัญชีทั้งใน K2 และ SBP Mall · เมื่อเอกสาร "เสร็จสิ้นดำเนินการ" แล้ว ทีมบัญชีเปิด **รายงานตรวจสอบประกันรายได้ (SBP Mall)** ดูยอดชดเชยรายสาขา → Export CSV to Batch → กระทบยอดกับ SAP (`FBL3H`) และ Post (`SAPPOST`) เอง · **กรณี SBP ผิดแต่ SAP ถูก** → เปิด SR ให้ทีมดูแล SBP แก้รายครั้ง (ข้อเสนอ: Auto Update จาก SAP · BSR = Out of Scope)

### Stage D — ส่งผลออกและเฝ้าระวัง ACK · Jobs 6 และ 10

11. **ส่งผลชดเชยเข้า Statement** (FGI/FCS · Job 6) — ทุกวัน 17:00 · sync สถานะ 10 ขั้น → ตรวจ QSSI ครบ 6 หมวด (8,9,12,1,10,16) → ไฟล์ `FRBC0001` (windows-874 · พ.ศ.) SFTP ไป STA · ระบบใหม่แก้บั๊ก purge tracking (E20) — ฝั่ง STA: Approve=A → บันทึกบัญชี SAP · Stop Flow=S · Initial=I → ตั้ง Flow + ไฟล์ RT040035/RT040078 กลับมา
12. **เฝ้าระวัง ACK จาก STA** (FGI/FCS · Job 10 · **เพิ่ม callback**) — เดิม: watchdog อ่าน tracking ทุก 07:00 แล้วส่งเมลเมื่อค้าง ≥ 1 วัน · ใหม่: เพิ่ม `POST /interfaces/sta/ack` ให้ STA ยิงตอบกลับตรง — watchdog คงไว้เป็น safety net

## Migration Map — จุดเชื่อมต่อที่เปลี่ยนจากระบบเดิม

| จุดเชื่อมต่อ | กลไกเดิม | กลไกใหม่ |
|---|---|---|
| ส่งข้อมูลชดเชย/ร้านใหม่/คู่แข่ง เข้าระบบเอกสาร | ไฟล์ BPM06001O (48 ฟิลด์) / BPM06002O / BPM06003O ผ่าน SFTP + EAI ไป BPM (Jobs 7, 8, 9) | Document Service เขียน DB ตรง (compensation_documents / document_new_stores / document_competitors) — **ตัดไฟล์ SFTP และ EAI ภายในทิ้ง** |
| เปิด Workflow | Job 8b ยิง K2 REST StartInstance (HTTP + Basic Auth hardcoded — P0) | Workflow Engine ภายใน · POST /workflows/instances · Gen Flow Gate W/Y/N คงเกณฑ์เดิมทุกข้อ |
| รับ ACK ผลประมวลจาก STA | รอ STA อัปเดต return_code ใน tracking · Job 10 ตรวจทุกเช้า | เพิ่ม POST /interfaces/sta/ack (API key) · Job 10 คงไว้เป็น safety net |
| ตาราง tracking interface | FGI_CONFIRM_RECEIVE_DATA — polymorphic FK + บั๊ก purge (E20) | interface_transactions — typed FK + purge ทำงานจริง |
| อีเมลแจ้งเตือน | แต่ละ job ต่อ SMTP เอง · TIS-620 · ผู้รับ hardcoded บางจุด (template 34) | Notification Service กลาง · UTF-8 · ผู้รับตาม status_email_rules + config ต่อ job |
| Interface ภายนอก QSSI / ALLMAP / IAS / STA | SFTP + ไฟล์ตาม encoding เฉพาะ (WINDOWS-874 / UTF-8 / พ.ศ.) | **คงเดิม** (ระบบของทีมอื่น) — ย้าย credential ไป Secret Manager + บังคับ known_hosts |
| สิทธิ์ผู้ใช้และเมนู | ตารางสิทธิ์ 8 role ใน SRS (จัดการในระบบ BPM เดิม) | Auth & RBAC + JWT · menu_permissions ต่อ role · จัดการผ่านหน้าสิทธิ์การเข้าถึงเมนู |

## สถานะเอกสารและเส้นทางพิจารณา (ตาม SRS 3.1.6 + workflow_status_document.md)

> ฝั่งเอกสาร/Workflow (โซน B) ล้วน — **ไม่กระทบ FGI/FCS pipeline**

**สถานะเอกสารมี 6 ค่า** (เดิม 8 — ตัดสถานะบัญชี 04/05 ตาม SDD v7.5) — รูปแบบ "รอ\<ผู้ดำเนินการ\>ดำเนินการ" หนึ่งค่าต่อ section + สถานะจบ · inbox ของแต่ละ role คือเอกสารในสถานะ "รอ\<role ตัวเอง\>ดำเนินการ" ค่าเดียว:

1. รอฝ่าย SBP DSA ดำเนินการ (06)
2. รอเจ้าหน้าที่ SBP DSA ดำเนินการ (08)
3. รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ (01)
4. รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ (02)
5. รอผู้บริหารสำนักบริหาร SBP ดำเนินการ (03)
6. เสร็จสิ้นดำเนินการ

> FE โหลดรายการสถานะ 6 ค่านี้และ Section 5 ขั้น (06/08/01/02/03) สำหรับ dropdown ตัวกรองในหน้าค้นหาเอกสาร/รายงานผ่านกลุ่ม Lookup: `GET /document-statuses` และ `GET /workflow-sections`

**ตารางเส้นทางพิจารณา (transition)** — อีเมล TO = ผู้ดำเนินการลำดับถัดไป (ตาม `status_email_rules`):

| Section | ตัวเลือกพิจารณา | สถานะถัดไป |
|---|---|---|
| 06 ฝ่าย SBP DSA | เห็นควรไม่ชดเชย · หยุดชดเชยประกันรายได้ | เสร็จสิ้นดำเนินการ |
| | ส่งฝ่ายส่งเสริมธุรกิจ SBP | รอ 01 |
| | ส่งเจ้าหน้าที่ SBP DSA | รอ 08 |
| 08 เจ้าหน้าที่ SBP DSA | คำนวณเงินชดเชยเรียบร้อย | รอ 01 |
| | ส่งกลับฝ่าย SBP DSA | รอ 06 |
| 01 ฝ่ายส่งเสริมธุรกิจ SBP | เห็นควรชดเชย | รอ 02 |
| | เห็นควรไม่ชดเชย / ส่งกลับ | รอ 06 |
| 02 GM ส่งเสริมธุรกิจ SBP | เห็นควรชดเชย **> 100,000** | รอ 03 (AVP) |
| | เห็นควรชดเชย **≤ 100,000** | **เสร็จสิ้นดำเนินการ** (จบที่ GM — ไม่มีขั้นบัญชี) |
| | เห็นควรไม่ชดเชย **> 100,000** | รอ 03 (AVP) — ไม่ชดเชยก็ต้องผ่าน AVP ตามวงเงิน |
| | เห็นควรไม่ชดเชย **≤ 100,000** | รอ 06 |
| | ส่งกลับฝ่ายส่งเสริมธุรกิจ SBP | รอ 01 |
| 03 ผู้บริหารสำนักบริหาร SBP (AVP) | เห็นควรชดเชย | **เสร็จสิ้นดำเนินการ** (จบที่ AVP) |
| | เห็นควรไม่ชดเชย | รอ 06 |
| | ส่งกลับ GM ส่งเสริมฯ | รอ 02 |

> **ตัดขั้นบัญชี 04/05 ตาม SDD v7.5** — เดิมผล ≤100,000 และผลอนุมัติของ AVP จะส่งต่อ "รอ 04 ฝ่ายบัญชี SBP → รอ 05 บัญชีปฏิบัติการภาค → เสร็จสิ้น" · ตอนนี้เอกสารจบที่ GM (≤100k) หรือ AVP (>100k) ทันที · ทีมบัญชีตรวจสอบยอดผ่านรายงาน SBP Mall + กระทบ SAP นอก workflow (ดูขั้น 10) · ทางเลือกเดิม "06 → ส่งฝ่ายบัญชี SBP (ข้ามได้)" ถูกยกเลิกไปด้วย

**ข้อเท็จจริงจาก SRS ที่ FE ต้องใช้ให้ตรง:**
- ภาคในรายงานตรวจสอบประกันรายได้ (SBP Mall) = **13 รหัส**: `BE BS NEU REU RSU BG BW RC RN BN NEL REL RSL` + **เพิ่มภาคใหม่อัตโนมัติ** (SDD v7.5) · เดิม SRS 3.1.7 = 8 ค่า (`BE BN BS BW` + `RC RE RN RS` — มี RC ไม่มี RW)
- ประเภทร้านในตัวกรองรายงานตรวจสอบประกันรายได้ (SBP Mall): `A / B / C / D` (4 ค่า เลือกได้มากกว่า 1 · SDD v7.5) · หน้าค้นหา K2 เดิมใช้ `FR Type A/B/C/พนักงาน` — ประเภทเต็ม 8 ชนิดปรากฏเฉพาะในรายละเอียดเอกสาร
- Validation ก่อนส่งดำเนินการ: ต้องเลือกผลพิจารณาอย่างน้อย 1 ข้อ — popup verbatim: "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ" · ปุ่มบันทึกไม่ validate
- ไฟล์แนบ ≤ 5MB ต่อไฟล์ · ประเภท: vsd,dwg,afp,pdf,mda,zip,wav,mp3,gif,jpg,tif,tiff,htm,html,txt,xml,mpg,mov,ivs,doc,docx,xls,xlsx,pps,ppt,pot,csv
- ข้อ "ยอดขายไม่ครบ 60 วัน" เป็น**คุณสมบัติของข้อมูล (flag แถวแดง)** ไม่ใช่สถานะ workflow

**หน้าข้อมูลผิดปกติ / แจกงาน (`k2-list-abnormal.html`) — ที่มาและขอบเขต:**

> **สถานะปัจจุบัน: ปิดชั่วคราวรอตัดสินใจ — comment ไว้ที่ MODULES (sbp.js), shortcut ใน index.html, กลุ่ม API 2 เส้นใน plan-api.html และตัดชื่อหน้าจอออกจาก plan-flow.html · ตัวไฟล์และฟังก์ชันยังอยู่ครบ เปิดคืนได้โดย uncomment**
- มีที่มาจาก SRS 3.1.1: role `05 Assign Job` มีหน้าที่ "แจกงานที่เมนูข้อมูลผิดปกติ" — เมนูนี้จึงเป็น requirement ตรงจากตารางสิทธิ์ ไม่ใช่หน้าที่แต่งเพิ่ม
- ระบบใหม่ยิ่งจำเป็น: การแก้ P1 ของ Job 5 (growth_rate_diff = NULL → ตั้ง "รอตรวจสอบ" แทน auto-accept) สร้างคิวงานผิดปกติที่ต้องมีคนถูก assign มาตรวจ
- สถานะในหน้านี้ (ผิดปกติ → แจกงานแล้ว → แก้ไขแล้ว) เป็น **สถานะการแจกงาน (assignment status)** แยกคนละชุดกับสถานะเอกสาร 6 ค่าของ workflow — เอกสารที่ถูกแจกงานยังเดิน workflow ตามสถานะ "รอ<ผู้ดำเนินการ>ดำเนินการ" ของมันตามปกติ

## พฤติกรรมจาก Approve Flow เดิม (Flow ประกันรายได้.png)

แผนภาพ BPMN "A-Document Approve Flow ประกันรายได้" ของระบบเดิม (8 lanes: admin, ฝ่าย OPT, GM OPT, บัญชี, บัญชีปฏิบัติการภาค, ฝ่าย บชฟ, เจ้าหน้าที่ บชฟ, GM ส่งเสริม) เป็น flow อนุมัติรุ่นก่อน SRS v3.1 — เรื่อง role/ลำดับขั้นให้ยึด workflow 5 ขั้น (06→08→01→02→03 · ตัดบัญชี 04/05 ตาม SDD v7.5) แต่มี 4 พฤติกรรมที่รับเข้าระบบใหม่ **ทั้งหมดอยู่ฝั่งเอกสาร/Workflow (โซน B/C) ไม่กระทบ FGI/FCS pipeline (Jobs 1–10) และ interface ภายนอก**:

1. **อีเมลเตือนงานค้างรายสัปดาห์** — flow เดิมส่งเตือนผู้ดำเนินการทุกวันจันทร์ 10:00 แทบทุกขั้น (จุด 10.1, 20.2, 30.1, 70.1, 80.1, 110.2) → ระบบใหม่: Notification Service เพิ่ม reminder job รายสัปดาห์ อ่านงานค้างจาก `workflow_tasks` ผู้รับตาม `status_email_rules` รอบเวลาแก้ได้ใน config
2. **Escalation งานค้าง 30/45/60 วัน** — flow เดิมส่งต่อ GM OPT เมื่อครบ 30/45/60 วัน (จุด 20.3) → ระบบใหม่: Workflow Engine ตรวจ waiting_days ของ `workflow_tasks` แล้วแจ้ง/ส่งต่อหัวหน้า Section ตามเกณฑ์ (ค่ากำหนดแก้ได้)
3. **สร้างเอกสารแบบ manual** — ขั้น 15 ของ flow เดิม (กรอกข้อมูลร้านเอง เมื่อระบบคำนวณให้ไม่ได้) → ระบบใหม่: หน้า "สร้างเอกสาร" (k2-create) ค้นหาร้านถูกกระทบ/ร้านเปิดใหม่ผ่าน `GET /stores/search` แล้ว `POST /documents` ลงตารางชุดเดียวกับเส้นอัตโนมัติ — จุดเข้าเสริม ไม่แตะ batch
4. **เงื่อนไขร้านก่อน/หลัง 1/10/2557** — โน้ต 10.1–10.4 แยกจุดเริ่มเอกสารตามวันที่โอนร้านแฟรนไชส์ → ระบบใหม่: ถ้ายืนยันตาม SRS จะเป็นกฎ routing ตอนเปิด instance ใน Workflow Engine — **เกณฑ์ Gen Flow Gate ฝั่ง batch คงเดิมทุกข้อ · สถานะ: รอ verify กับ SRS v3.1**

สิ่งที่อยู่ในภาพแต่**ไม่รับเข้า**: โครง role 8 lanes (ถูกแทนด้วย 5 ขั้น section_code · ตัดบัญชี 04/05 ตาม SDD v7.5 · SRS v3.1 ซึ่งใหม่กว่า และภาพนี้ยังไม่มีกฎวงเงิน 100,000 / lane SBP DSA)

## กติกาธุรกิจที่ห้ามเปลี่ยน

กติกาธุรกิจทั้งหมด**คงเดิมตามเอกสารอ้างอิง** — การเปลี่ยนแปลงจำกัดที่กลไกทางเทคนิค (ไฟล์ภายใน → DB/API, K2 engine → Workflow ภายใน) และการแก้ความเสี่ยง P0/P1 เท่านั้น การเปลี่ยนพฤติกรรมเชิงธุรกิจต้องขออนุมัติแยกตามข้อ 8.2 ของเอกสาร v4.0:

- เกณฑ์ Gen Flow Gate ทุกข้อ (ดูขั้นที่ 6)
- กฎวงเงิน 100,000 บาท (AVP routing)
- หน้าต่างคำนวณยอดขาย 4×15 วัน · เกณฑ์ outlier ≥ 50 · เกณฑ์ข้อมูล 60 วัน (ร้าน < 60 วัน = ผิดปกติ/flag-red)
- QSSI ครบ 6 หมวด (8,9,12,1,10,16)
- %ชดเชยรวมต่อเอกสาร = 100%
- เลขเอกสาร YYYY/xxxxx (ปี พ.ศ.)
- workflow 5 ขั้น: 06 → 08 → 01 → 02 → 03 (**ตัดขั้นบัญชี 04/05 ตาม SDD v7.5** — บัญชีตรวจสอบผ่านรายงาน SBP Mall นอก workflow)

## เอกสารที่เกี่ยวข้อง

- โครงสร้างตารางที่ flow นี้ใช้: [database.md](database.md) · `plan-database.html`
- API ทุกเส้น: [api.md](api.md) · `plan-api.html` (62 endpoints 10 กลุ่ม — รวมกลุ่ม **Lookup** 4 เส้น (`GET /stores/search` · `/competitors` · `/document-statuses` · `/workflow-sections`) และ `GET /documents/{docNo}/sales` ที่เพิ่มให้ครบตามหน้าจอ · แต่ละเส้นมีแท็บ Request/Response + Database (พร้อมตัวอย่าง SQL) และ 4 เส้นที่ซับซ้อนมีแท็บ Flowchart · กลุ่มข้อมูลผิดปกติ 2 เส้นถูก comment รอตัดสินใจ)
- Email template ทุกจุดส่งใน flow: `plan-email.html` (8 templates: EM-01–03 เปลี่ยนสถานะ/จบงาน/ส่งกลับ ตาม status_email_rules · EM-04–05 เตือนงานค้างรายสัปดาห์/escalation 30-45-60 วัน · EM-06–08 ฝั่ง batch: สรุปเปิด workflow ราย DV, job error, watchdog ACK — ผู้รับ TO/CC ตาม SRS 3.1.5, เนื้อหาอีเมลเป็นข้อเสนอระบบใหม่ beyond SRS · Subject/เนื้อหาแก้ไขได้ในหน้า (เก็บ localStorage ต่อเครื่อง, From/To/Cc ล็อกตาม rules) และรีเซ็ตกลับ Default ได้รายตัวหรือทั้งหมด)
- Flow ต้นฉบับแยกระบบ: `flow-fgi.html` (FGI/FCS pipeline) · `k2-flow.html` (K2 approval BPMN) · `job-batch.html` (Batch console)
- Sequence diagram: `old-flow.png` (เดิม, มี EAI + K2) · `new-flow.png` (ใหม่, รวมเข้า SBPGI แล้ว)
