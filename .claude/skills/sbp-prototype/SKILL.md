---
name: sbp-prototype
description: องค์ความรู้โปรเจกต์ sbp-prototype — ระบบประกันรายได้ K2/SGI (7-Eleven Store Partner income guarantee) ใช้เมื่อทำงานกับหน้า HTML prototype, sbp.js, การออกแบบ database/workflow/API, email template, สิทธิ์ role, batch jobs หรือเอกสาร SRS ในโปรเจกต์นี้ ครอบคลุมกติกาธุรกิจที่ห้ามเปลี่ยน ลำดับเอกสารอ้างอิง และ playbook งานที่ทำบ่อย
---

# SBP Prototype — ระบบประกันรายได้ (K2 → SGI)

Prototype HTML แบบ click-through ภาษาไทยของระบบชดเชยรายได้ให้ร้าน 7-Eleven Store Partner (SP)
ที่ยอดขายตกเมื่อมีสาขาใหม่เปิดในรัศมีกระทบ (1 กม. กทม./ปริมณฑล · 2 กม. ต่างจังหวัด)
ระบบใหม่ชื่อ **SGI** รวม EAI + K2 เข้าเป็นระบบเดียว ฐานข้อมูลเดียว

ไม่มี build/lint/test — เปิดด้วย `open index.html` หรือ `python3 -m http.server` (ทั้งคู่เด้งไปหน้าแรกจริงคือ `k2-list-waiting.html` — `index.html` เหลือเป็น redirect stub)
Dependency ภายนอกมีแค่ Google Fonts — **ทุกอย่างต้องทำงาน offline ห้ามเพิ่ม CDN/library**

## กติกาเหล็ก (อ่านก่อนแก้อะไรทุกครั้ง)

1. **Living docs ต้อง sync** — คุยเรื่อง database ให้อ่าน `database.md` ก่อน · เรื่อง flow/workflow ให้อ่าน `workflow.md` ก่อน · เรื่อง API ให้อ่าน `api.md` ก่อน
   ตัดสินใจใหม่เมื่อไร ต้องอัปเดตทั้ง `.md` และ HTML คู่ของมัน (`plan-database.html` / `plan-flow.html` / `plan-api.html`) **ในการแก้ครั้งเดียวกัน** · ทั้งสาม cross-coupled (แก้ API มักกระทบตาราง/flow — อัปเดตคู่ที่เกี่ยวข้องพร้อมกัน)
2. **ข้อความ popup/validation ภาษาไทยเป็น verbatim จาก SRS** — ห้าม paraphrase (เช่น "ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูล ก่อนกดส่งดำเนินการ")
3. **กติกาธุรกิจห้ามเปลี่ยน** (ดูรายการเต็มใน [references/domain.md](references/domain.md)) — เปลี่ยนได้เฉพาะกลไกเทคนิค การเปลี่ยนเชิงธุรกิจต้องขอ business sign-off
4. **ชื่อไฟล์มีภาษาไทย — quote path เสมอ** ในคำสั่ง shell
5. ชื่อ object ใน target schema เป็นอังกฤษ `lower_snake_case` · ป้ายที่มา **(FGI/FCS) (K2) (ใหม่)** ต้องคงไว้เสมอ
6. หน้า `k2-list-waiting.html` / `k2-list-related.html` เป็นฝาแฝด (ต่างแค่ `MODE`, title, body attrs) — **แก้อะไรต้องแก้ทั้งคู่**

## ลำดับเอกสารอ้างอิง (source-of-truth order)

| ลำดับ | ไฟล์ | คืออะไร |
|---|---|---|
| 1 | `RDM-SRS ประกันรายได้-K2.pdf` | SRS v3.1 — แหล่งความจริงสูงสุดฝั่งหน้าจอ K2 |
| 2 | `RDM-SRS-ประกันรายได้-K2-รายการหน้าจอ.md` (455 บรรทัด) | รายละเอียดต่อหน้าจอ: ฟิลด์ validation ข้อความ popup ตาราง role |
| 3 | `ประกันรายได้-K2-รายการหน้าจอ.md` (160 บรรทัด) | ฉบับย่อ keyed ตามเลข section SRS + section_code + 8 role — **ไม่ใช่ไฟล์ซ้ำ** กับข้อ 2 |
| 4 | `FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf` | แหล่งความจริงเดียวของ batch Jobs 1–10 + 8b (หน้า `job-batch.html` = **“Flow Batch Job” ในกลุ่มเมนู Flow ตั้งแต่ 2026-08-06** เหลือแค่ Flowchart + Database ที่ใช้ — เอกสารนี้ยังเป็นแหล่งความจริงของทั้งหน้าและงาน BE ของ job) |
| 5 | `database.md` / `workflow.md` / `api.md` | **living docs** — การออกแบบระบบใหม่ (schema **20 ตาราง** — 19 CREATE + `fcs_qssi_score` ที่ reuse / flow 12 ขั้น (ขั้น 1 เป็นหมายเหตุว่าตัด Job 1 แล้ว จึงทำจริง 11 ขั้น) / API **29 เส้น 6 กลุ่ม** — RBAC/ผู้ปฏิบัติงาน + workflow engine + store/zone/employee master + email template + config **ใช้ของระบบ SBP เดิม** · ตัดสินใจ 2026-08-05 และ 2026-08-06) canonical กว่า HTML เมื่อขัดแย้ง |
| 6 | `PLAN-checklist-prototype.md` | checklist สถานะ implement — **ภายในขัดแย้งกันเอง** เช็ค HTML จริงก่อนเชื่อ |
| 7 | **`SDD ปรับปรุงการชดเชยรายได้ในระบบ SBP GI(2402026).pptx`** (แปลงไว้ที่ `SDD-GI-Compensation/SDD-ปรับปรุงการชดเชยรายได้-SBP-GI.md`) | **"SDD GI" — SDD ฉบับเดียวที่เหลือใน repo · ใหม่สุด 24/02/2026 · ชนะเมื่อขัดแย้งกับเอกสารเก่า** (วงเงินเกณฑ์เดียว 100,000/AVP 300,000 · เจ้าหน้าที่อาวุโส · เปิดเรื่องซ้ำ · auto-assign งานค้าง) · SDD v7.5 (08102025) **ถูกลบออกจาก repo 2026-08-06** ข้อกำหนดรวมเข้าการออกแบบแล้ว |

`SRS_Income_Compensation_v3.1.md` เป็น markdown แปลงจาก SRS pdf · `workflow_status_document.md` = ตารางสถานะ/อีเมล

## Playbook งานที่ทำบ่อย

**เพิ่มหน้าใหม่** — (1) copy โครงจาก `k2-document.html` ตาม page contract (2) เพิ่ม entry ใน `MODULES` (`assets/sbp.js` ~บรรทัด 55)
รายละเอียด contract + behavior hooks: [references/architecture.md](references/architecture.md)

**แก้เรื่อง database** — อ่าน `database.md` → แก้ `database.md` + `plan-database.html` คู่กัน → ถ้ากระทบ API แก้ `api.md` + `plan-api.html` ด้วย

**แก้เรื่อง flow/workflow** — อ่าน `workflow.md` → แก้ `workflow.md` + `plan-flow.html` คู่กัน → เช็คว่ากระทบ `workflow_status_document.md` (ตารางสถานะ × ผู้รับ × อีเมล) หรือไม่

**แก้เรื่อง API** — อ่าน `api.md` → แก้ `api.md` + `plan-api.html` คู่กัน → ถ้ากระทบตาราง/flow แก้ `database.md`/`workflow.md` ด้วย
โครง modal ต่อ endpoint ใน `plan-api.html`: Flow อธิบาย**นอกแท็บ** · แท็บ 1 Request/Response · แท็บ 2 Database + SQL (ตัวอย่าง SQL ต่อเส้นใน `SQL_BY_PATH` keyed `'METHOD path'` ครบทุกเส้น) · แท็บ 3 Flowchart **เฉพาะ 3 เส้นซับซ้อน** (spec ใน `FLOWCHART_BY_PATH` เรนเดอร์ด้วย `renderFlow()` inline SVG) — ดูรายละเอียดใน [references/architecture.md](references/architecture.md) §plan-api

**แก้ email template / ค่ากำหนดกลาง** — **ไม่มีหน้าจอใน SGI แล้ว (ลบทั้งฟีเจอร์ 2026-08-06)** · template 8 ฉบับ (EM-01–08) อยู่ในตาราง `email_template` และค่ากำหนดกลางอยู่ใน `mas_param` ของ**ระบบ SBP เดิม** ซึ่งมีหน้าจอบริหารจัดการอยู่แล้ว · SGI อ่านอย่างเดียวแล้วส่งผ่าน `@gosoft-sbp/email-lib` (log ลง `email_sent`)

**แก้สิทธิ์/role** — **ตัดสินใจ 2026-08-05: ใช้ระบบ SBP เดิม** (auth-backend/ABS: groups/menus/permissions ต่อ URL · จัดการผ่านหน้า `/setting/manage-user-rights` ของ FE เดิม) — SGI ไม่มีตาราง `roles`/`menus`/`menu_permissions`/`user_accounts`/`operator_assignments` และไม่มีหน้า/เมนู `k2-permissions.html` · `k2-operators.html` แล้ว (ไฟล์เก็บไว้อ้างอิง · 8 role ดูตารางใน [references/domain.md](references/domain.md) — map เป็น group ของระบบเดิม)

**หน้าที่ตัดออกถาวร 2026-08-06** — (1) **Overview** (`index.html`) เหลือเป็น redirect stub · หน้าแรกคือ `k2-list-waiting.html` (ค่าคุมอยู่ที่ `HOME_KEY`/`HOME_HREF` ใน sbp.js) (2) **ข้อมูลผิดปกติ / แจกงาน** — **ลบไฟล์ `k2-list-abnormal.html` ทิ้งแล้ว** พร้อมเมนูใน MODULES และกลุ่ม API 2 เส้นใน plan-api.html · ข้อมูลผิดปกติเหลือเป็นธงแถวแดง + stat card "ยอดขายไม่ครบ 60 วัน" ในหน้ารอดำเนินการ/ที่เกี่ยวข้อง

## เอกสารอ้างอิงใน skill นี้

- [references/architecture.md](references/architecture.md) — page contract, sbp.js hooks, styling, รายการหน้า, internals ของ plan-api
- [references/domain.md](references/domain.md) — กติกาธุรกิจ: workflow 5 ขั้น + transition, สถานะ 6 ค่า, 8 role, ค่าคงที่ธุรกิจ, email templates, ข้อเท็จจริง SRS ที่พลาดบ่อย
