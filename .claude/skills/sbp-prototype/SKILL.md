---
name: sbp-prototype
description: องค์ความรู้โปรเจกต์ sbp-prototype — ระบบประกันรายได้ K2/SBPGI (7-Eleven Store Partner income guarantee) ใช้เมื่อทำงานกับหน้า HTML prototype, sbp.js, การออกแบบ database/workflow/API, email template, สิทธิ์ role, batch jobs หรือเอกสาร SRS ในโปรเจกต์นี้ ครอบคลุมกติกาธุรกิจที่ห้ามเปลี่ยน ลำดับเอกสารอ้างอิง และ playbook งานที่ทำบ่อย
---

# SBP Prototype — ระบบประกันรายได้ (K2 → SBPGI)

Prototype HTML แบบ click-through ภาษาไทยของระบบชดเชยรายได้ให้ร้าน 7-Eleven Store Partner (SP)
ที่ยอดขายตกเมื่อมีสาขาใหม่เปิดในรัศมีกระทบ (1 กม. กทม./ปริมณฑล · 2 กม. ต่างจังหวัด)
ระบบใหม่ชื่อ **SBPGI** รวม EAI + K2 เข้าเป็นระบบเดียว ฐานข้อมูลเดียว

ไม่มี build/lint/test — เปิดด้วย `open index.html` หรือ `python3 -m http.server`
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
| 4 | `FGI_FCS_Batch_Job_Technical_Document_Improved_v4.0.pdf` | แหล่งความจริงเดียวของ batch Jobs 1–10 + 8b (ใช้กับ `job-batch.html`) |
| 5 | `database.md` / `workflow.md` / `api.md` | **living docs** — การออกแบบระบบใหม่ (schema 34 ตาราง / flow 12 ขั้น / API 61 เส้น 10 กลุ่ม) canonical กว่า HTML เมื่อขัดแย้ง |
| 6 | `PLAN-checklist-prototype.md` | checklist สถานะ implement — **ภายในขัดแย้งกันเอง** เช็ค HTML จริงก่อนเชื่อ |

`SRS_Income_Compensation_v3.1.md` เป็น markdown แปลงจาก SRS pdf · `workflow_status_document.md` = ตารางสถานะ/อีเมล

## Playbook งานที่ทำบ่อย

**เพิ่มหน้าใหม่** — (1) copy โครงจาก `k2-document.html` ตาม page contract (2) เพิ่ม entry ใน `MODULES` (`assets/sbp.js` ~บรรทัด 55)
รายละเอียด contract + behavior hooks: [references/architecture.md](references/architecture.md)

**แก้เรื่อง database** — อ่าน `database.md` → แก้ `database.md` + `plan-database.html` คู่กัน → ถ้ากระทบ API แก้ `api.md` + `plan-api.html` ด้วย

**แก้เรื่อง flow/workflow** — อ่าน `workflow.md` → แก้ `workflow.md` + `plan-flow.html` คู่กัน → เช็คว่ากระทบ `plan-email.html` (จุดส่งอีเมล) หรือไม่

**แก้เรื่อง API** — อ่าน `api.md` → แก้ `api.md` + `plan-api.html` คู่กัน → ถ้ากระทบตาราง/flow แก้ `database.md`/`workflow.md` ด้วย
โครง modal ต่อ endpoint ใน `plan-api.html`: Flow อธิบาย**นอกแท็บ** · แท็บ 1 Request/Response · แท็บ 2 Database + SQL (ตัวอย่าง SQL ต่อเส้นใน `SQL_BY_PATH` keyed `'METHOD path'` ครบทุกเส้น) · แท็บ 3 Flowchart **เฉพาะ 4 เส้นซับซ้อน** (spec ใน `FLOWCHART_BY_PATH` เรนเดอร์ด้วย `renderFlow()` inline SVG) — ดูรายละเอียดใน [references/architecture.md](references/architecture.md) §plan-api

**แก้ email template** — หน้า `plan-email.html` มี WYSIWYG editor ในตัว (toolbar + ชิปตัวแปร + ตาราง + sticky save)
โครงสร้าง 8 templates (EM-01–08) และ internals ของ editor: [references/architecture.md](references/architecture.md) §plan-email

**แก้สิทธิ์/role** — หน้า `k2-permissions.html` · 8 role (00–10) ดูตารางใน [references/domain.md](references/domain.md) · CRUD ผ่านตาราง `roles`/`menus`/`menu_permissions` ทุกการแก้ต้องมีเหตุผลลง `audit_logs`

**เรื่องหน้าข้อมูลผิดปกติ (`k2-list-abnormal.html`)** — ปิดชั่วคราวรอตัดสินใจ: comment อยู่ที่ MODULES, index.html shortcuts, กลุ่ม API 2 เส้นใน plan-api.html · ไฟล์ยังอยู่ครบ เปิดคืนได้โดย uncomment

## เอกสารอ้างอิงใน skill นี้

- [references/architecture.md](references/architecture.md) — page contract, sbp.js hooks, styling, รายการหน้า, internals ของ plan-email editor
- [references/domain.md](references/domain.md) — กติกาธุรกิจ: workflow 7 ขั้น + transition, สถานะ 8 ค่า, 8 role, ค่าคงที่ธุรกิจ, email templates, ข้อเท็จจริง SRS ที่พลาดบ่อย
