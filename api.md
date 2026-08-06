# API — REST /api/v1 (ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุป REST API ทั้งหมดของระบบใหม่ สำหรับ Frontend SPA และงานภายใน
> **แหล่งอ้างอิงหลัก:** `plan-api.html` (หน้า API · sidebar group `Plan`)
> **อ้างอิงประกอบ:** `database.md` / `plan-database.html` (ตารางที่แต่ละเส้นอ่าน/เขียน) · `workflow.md` / `plan-flow.html` (flow) · SRS ประกันรายได้-K2 v3.1 · เอกสาร Batch v4.0 · **SDD GI 24/02/2026** (`SDD-GI-Compensation/…md` — วงเงิน GM 50,000/AVP 300,000 · เปิดเรื่องซ้ำ · งานค้าง)
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง API ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-api.html` ให้ตรงกัน · ถ้ากระทบตาราง/flow ต้องอัปเดต `database.md`/`workflow.md` คู่กันด้วย

## ภาพรวม

- **48 เส้น · 9 กลุ่มตามโดเมน** เป็น reference contract สำหรับ FE/BE alignment (กลุ่มข้อมูลผิดปกติ 2 เส้น **ยกเลิกและลบทิ้ง 2026-08-06** พร้อมหน้าจอ — ดูท้ายไฟล์)
- Base URL `/api/v1` · การยืนยันตัวตน: ผ่าน BFF ของระบบ SBP เดิม — SBPGI รับ user context จาก header (`x-api-key` + `x-user-id`/`x-user-group-id`/`x-user-permissions`) · callback ภายนอกใช้ API key/service token
- **ตัดสินใจ 2026-08-05:** กลุ่ม Auth & สิทธิ์ผู้ใช้ (เดิมกลุ่ม 1 · 4 เส้น) และ API ผู้ปฏิบัติงาน/roles/menus/สิทธิ์เมนู (เดิมอยู่กลุ่ม Master Data · 14 เส้น) **ตัดออก — ใช้ระบบ SBP เดิม** (Cognito + BFF + auth-backend/ABS) ดูหัวข้อ "เส้นที่ตัดออก" ท้ายไฟล์ · เดิมนับเป็น 62 เส้น 10 กลุ่ม
- **ตัดสินใจ 2026-08-06 (รอบ 2) — ยึด API/DB ของระบบ SBP เดิมเป็นหลัก:** ตรวจ `SBP/README.md` + `srm-sps-spsap-store-backend` แล้วตัดอีก **3 เส้น** ที่มีของพร้อมใช้อยู่แล้ว (`/stores/search` → `GET /store/search` · `/zones` → `GET /store/all-regions` · `/branch-types` → `GET /common/common-code`) → **เหลือ 44 เส้น** · และเปลี่ยนแหล่งข้อมูลของอีก 4 เส้นให้ไปอ่าน/เขียนของระบบเดิมแทนตารางของ SBPGI (ดูตาราง "เส้นที่เปลี่ยนไปใช้ของระบบ SBP เดิม" ท้ายไฟล์)
- แบ่งหน้า `?page=1&size=20` → ตอบ `{"page","size","total","items":[]}`
- Error รูปแบบเดียวกันทุกเส้น `{"code":"DOC_409","message":"ข้อความไทยตรงตาม SRS"}` — **ข้อความ popup ต้องตรงตัวตาม SRS**
- **วันที่และเลขเอกสารเป็น ค.ศ. ทั้งหมด** (payload = ISO-8601 ค.ศ. · `docNo` = `YYYY/xxxxx` ค.ศ.) — ยึดตามระบบ SBP ปัจจุบัน (FE `DatePicker` default `buddhistEra=false` · BE helper `toAD()`), แสดงผล พ.ศ. เฉพาะจุดที่เปิด flag ที่ component · JSON UTF-8 ทุกเส้น (เลิก TIS-620)
- Code namespace ต้องไม่ตีความปนกัน: `roleCode` = RBAC role 00/01/02/03/04/05/06/10, `sectionCode` = workflow section 06/08/01/02/03, `statusCode` = document status lookup; ทุก response ที่ต้องแสดงสถานะให้ส่ง code เป็น canonical value แล้ว FE resolve label จาก `/document-statuses`
- Batch Monitor scope note: API กลุ่ม Batch Job Admin เป็น reference contract สำหรับ 2 tab ของ FE Batch Monitor เท่านั้น (`แบบฟอร์มพารามิเตอร์`, `ประวัติการรัน`); ไม่ออกแบบ tab Flowchart การทำงาน, step-by-step batch flow, หรือ Database ที่ใช้ของ batch job ใน `plan-api.html` และไม่ต้องใส่รายละเอียด endpoint รายเส้นในเอกสาร FE หน้านั้น
- ป้ายที่มาต่อเส้น: **(FGI/FCS)** เอกสาร Batch v4.0 · **(K2)** SRS v3.1 · **(ใหม่)** เพิ่มในระบบใหม่ · **(ผสม)**

## สัญญากลาง API/FE ที่ทุก endpoint ต้องใช้

> รายละเอียด LLDD กลาง: `LLDD/BE/LLDD-BE-API-Common-Contracts.md` และ `LLDD/FE/LLDD-FE-Integration-Contracts.md`

| หมวด | Contract กลาง | ผู้รับผิดชอบ / ใช้โดย |
|---|---|---|
| Transport | Base URL `/api/v1` · JSON `application/json; charset=utf-8` · multipart เฉพาะ attachments | BE ทุก controller · FE shared API client |
| Auth | ผู้ใช้ login ผ่าน BFF ระบบเดิม (Cognito · token เก็บใน httpOnly cookie ฝั่ง BFF) — SBPGI ตรวจ `x-api-key` + อ่าน user context จาก header ที่ BFF แนบมา; internal workflow/batch callback ใช้ service token | ระบบเดิม (BFF + auth-backend) จัดหา identity/สิทธิ์; BE validate header; FE ไม่แตะ token |
| Error | ทุก error คืน `{code,message}` เท่านั้น · `message` เป็นไทย verbatim ตาม SRS ถ้ามีข้อความกำหนด | BE error handler · FE แสดง `message` ตรง ๆ |
| HTTP status | 400 validation · 401 auth · 403 forbidden/RBAC · 404 not found · 409 duplicate/current-task conflict · 422 business rule · 413 file too large · 415 unsupported file | BE middleware/service · FE error state |
| Pagination | GET list ทุกเส้นรับ `page,size` และคืน `{page,size,total,items}` | BE repository/query · FE DataTable/Pager |
| Format | `docNo` = `YYYY/xxxxx` **ค.ศ.** (เช่น `2026/00123`) · `storeCode/newStoreCode` เป็น string 5 หลักคง leading zero · date/month ใน payload เป็น ค.ศ. ISO · amount/percent เป็น number 2 decimals | BE validate/serialize · FE format display |
| Workflow transition | `/documents/{docNo}/actions` รับ `{result,comment}` โดย `result` เป็น 6-enum ไทย verbatim (ค่า "ส่งฝ่ายส่งเสริมธุรกิจ SBP" เปลี่ยนชื่อเป็น "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" ตาม SDD GI 24/02/2026) และคืน `{nextSection,statusCode,message}`; positive path คือ `06→08→01→02→03→99` โดย `99` = เสร็จสิ้นและ `nextSection=null`; ที่ Section 02 ยอด ≤50,000 จบเป็น 99 โดยไม่ผ่าน 03 · 50,001–300,000 → 03 (SDD GI) | BE Workflow Action เป็น source of truth; FE ไม่คำนวณ route เอง |
| RBAC/Menu | sidebar/route guard ใช้ของระบบเดิม: BFF `GET /menus` + `GET /groups/current-user/permissions` (`canView/canManage/canExport/canOther` ต่อ URL) · `GET /documents/{docNo}` ยังคืน `permissions.canEditSections` และ `permissions.canAction` (ธงเชิง workflow ที่ SBPGI คำนวณเอง) | ระบบเดิมคุมเมนู/สิทธิ์เข้าหน้า · BE task-owner guard · FE เปิด/ปิด UI |
| Audit/Reason | mutation master/config/email/RBAC ต้องมี `reason`; workflow action ลง `consideration_logs`; batch ลง `job_run_histories` | BE transaction/audit service · FE บังคับ reason field |
| Idempotency | endpoint ที่สร้างจาก job/service ใช้ `requestId` หรือ business key; duplicate ต้องคืน existing result หรือ 409 ตามกฎ endpoint | BE service · Job rerun |

## โครงหน้าจอ plan-api (modal รายละเอียดต่อ endpoint)

catalog รวมทุกเส้น → คลิกแถว → เปิด modal ที่มีโครงดังนี้ (ดู `selectEp()` ใน `plan-api.html`):

1. **ชิป** ที่มา · สิทธิ์ · กลุ่ม
2. **Flow (ลำดับการทำงาน)** — แสดง **นอกแท็บ** (ไม่ใช่แท็บแล้ว) เหนือแท็บ · ถ้าเส้นนั้นมี flowchart จะมี pill "มี Flowchart ในแท็บ 3" · ยกเว้นกลุ่ม Batch Job Admin ซึ่งแสดงเป็น reference note เท่านั้น
3. **แท็บ 1 · Request / Response** — request (query/body) + response + Error ที่ต้องรองรับ
4. **แท็บ 2 · Database + SQL** — ตารางที่เกี่ยวข้อง (R/W/RW) + **ตัวอย่าง SQL ต่อเส้น** (illustrative, bind params ขึ้นต้น `:`) เก็บใน `SQL_BY_PATH` keyed ด้วย `'METHOD path'` — ไม่แสดงในกลุ่ม Batch Job Admin
5. **แท็บ 3 · Flowchart** — โผล่**เฉพาะ 3 เส้นที่ซับซ้อน** (มี branching/หลายขั้น) · เป็น inline SVG เรนเดอร์จาก node spec ใน `FLOWCHART_BY_PATH` ผ่าน mini-renderer `renderFlow()` · ไม่แสดงในกลุ่ม Batch Job Admin

**3 เส้นที่มีแท็บ Flowchart:** `POST /documents/{docNo}/actions` (routing 5 ขั้น + วงเงิน GM 50,000 / AVP 300,000) · `POST /workflows/instances` (Gen Flow Gate) · `POST /documents` (สร้าง + กันซ้ำเฉพาะเอกสาร active)

## รายการ endpoint ทั้ง 9 กลุ่ม

### 1. Auth & สิทธิ์ผู้ใช้ — **ตัดออก · ใช้ระบบ SBP เดิม** (ตัดสินใจ 2026-08-05)

ไม่มี endpoint ใน SBPGI — FE ใช้ของระบบเดิมผ่าน BFF: login redirect `{bffUrl}/auth/login` (Cognito · cookie httpOnly) · `POST /auth/refresh` (axios interceptor เดิม) · `GET /auth/profile`, `GET /users/current` (ข้อมูลผู้ใช้) · `GET /menus` + `GET /groups/current-user/permissions` (sidebar/สิทธิ์ต่อ URL) — เส้นเดิมของกลุ่มนี้ (`/auth/login` `/auth/refresh` `/auth/me` `/me/menus`) ดูหัวข้อ "เส้นที่ตัดออก" ท้ายไฟล์

### 2. งาน & เอกสารประกันรายได้ · K2 3.1.2/3/4/6 (11 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/tasks` | งานรอท่านดำเนินการ (inbox ของ section — k2-list-waiting) |
| GET | `/documents` | ค้นหาเอกสารที่เกี่ยวข้อง — **บังคับระบุปี** |
| GET | `/documents/{docNo}` | เอกสารฉบับเต็ม 12 ส่วน + ธงสิทธิ์แก้ต่อ role/section |
| POST | `/documents` | สร้างเอกสาร — ออกเลข YYYY/xxxxx + เปิด workflow (มี Flowchart) · **ตัดสินใจ 2026-08-06: ไม่มีฟอร์มสร้างเอกสารใน FE แล้ว** — ต้นทางสร้างที่ระบบ **FS** แล้วรอ **SBP Statement** ส่งข้อมูลกลับ (~1 วัน) จึงเรียกเส้นนี้โดย pipeline/service token · หน้า `k2-create.html` เหลือเป็นหน้าอธิบายกระบวนการ · การคีย์/ปรับข้อมูลร้านตาม SDD GI ทำในหน้าเอกสาร (`PUT /documents/{docNo}`) |
| PUT | `/documents/{docNo}` | บันทึกส่วนย่อย (ร้านใหม่/คู่แข่ง/ปัจจัย) · **%ชดเชยรวม = 100%** |
| POST | `/documents/{docNo}/actions` | ส่งผลพิจารณา — หัวใจ workflow 5 ขั้น · วงเงิน GM 50,000 / AVP 300,000 · SDD GI (มี Flowchart) |
| GET | `/documents/{docNo}/timeline` | ประวัติพิจารณาทุกขั้น |
| POST | `/documents/{docNo}/attachments` | แนบไฟล์ ≤ 5MB |
| GET | `/documents/{docNo}/attachments/{attachId}/download` | ดาวน์โหลดไฟล์แนบรายไฟล์ผ่าน BE authorization + AV clean guard · ไฟล์จริงใช้ service S3 ของระบบ SBP เดิม |
| GET | `/documents/{docNo}/attachments/download-all` | **(เพิ่ม 2026-08-06)** ดาวน์โหลดไฟล์แนบทั้งหมดเป็น `.zip` — ปุ่ม “ดาวน์โหลดทั้งหมด” ระดับการ์ด (เทียบเท่าปุ่ม `Download` ของ K2 เดิม) · 404 เมื่อไม่มีไฟล์แนบ |
| GET | `/documents/{docNo}/sales` | **(ใหม่ session นี้)** ยอดขาย 4 หน้าต่าง × 15 วัน — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" + กราฟยอดขายในหน้าเอกสาร |

### 3. ข้อมูลอ้างอิง (Lookup / Reference) · K2 + FGI/FCS **(4 เส้น · ตัด `/stores/search` `/zones` `/branch-types` 2026-08-06 — ใช้ของระบบ SBP เดิม)**

> **ใช้ของระบบ SBP ปัจจุบันแทน:** ค้นหาร้าน → `GET /store/search` (+ `/store/list` `/store/detail` `/store/opt-name`) · ภาค/โซน → `GET /store/all-regions` (+ `/store/regions-by-email` `/store/province-by-region`) · ประเภทสาขา → `GET /common/common-code` (+ `/master/common`) — ทั้งหมดอยู่ใน `srm-sps-spsap-store-backend` และเรียกผ่าน BFF ตัวเดียวกับที่ FE ใช้อยู่แล้ว

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/competitors` | **master แบรนด์ร้านคู่แข่ง 11 รายการ** (รหัส 01–11 · ชื่อไทย+อังกฤษ) — dropdown เพิ่มคู่แข่งในเอกสาร · จัดการที่หน้า `k2-competitors.html` (**ใหม่ 2026-08-06** ตามหน้าจอ K2 เดิม) · ต่างจาก `document_competitors` ที่เก็บ**รายสาขา**พร้อมรหัสจาก ALLMAP (อ้างอิงไฟล์ตัวอย่างจริง — ดู `docs/K2-interface-files.md`) |
| GET | `/document-statuses` | รายการสถานะเอกสาร — dropdown ตัวกรอง (ค้นหา/รายงาน) |
| GET | `/workflow-sections` | รายการ Section 5 ขั้น (06/08/01/02/03) + `approveLimitAmount` ต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE ใช้แสดงวงเงิน ไม่ hardcode |
| GET | `/decisions` | **(เพิ่ม 2026-08-06)** ผลพิจารณาจาก master `decisions` (`decisionName` = ข้อความปุ่มไทย verbatim) — FE เรนเดอร์ปุ่มพิจารณาจากเส้นนี้ ไม่ hardcode 6-enum |

### 4. Master Data · K2 3.1.9 (8 เส้น · เพิ่ม CRUD คู่แข่ง 3 เส้น 2026-08-06)
| Method | Path | ทำอะไร |
|---|---|---|
| GET/POST/PUT/DELETE | `/factors` · `/factors/{code}` | ปัจจัยภายนอก (external_factors) — รหัสห้ามซ้ำ · reason บังคับ |
| POST/PUT/DELETE | `/competitors` · `/competitors/{code}` | **(เพิ่ม 2026-08-06)** master แบรนด์คู่แข่ง (competitors) — `code` + `nameTh` + `nameEn` บังคับ · รหัสห้ามซ้ำ · reason บังคับ → `audit_logs` · หน้าจอ `k2-competitors.html` |
| GET | `/audit-logs` | ประวัติแก้ master (= MaintainMasterHistory เดิม) |

> เส้นผู้ปฏิบัติงาน (`/operators*` · `/employees/search`) และสิทธิ์เมนู (`/roles*` · `/menus*` · `/menu-permissions*`) รวม 14 เส้น **ตัดออก — ใช้ระบบ SBP เดิม** (ดูท้ายไฟล์)

### 5. System Config (Global) · เขียนลงตาราง `mas_param` ของระบบ SBP เดิม (5 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/configs` · `/configs/{key}` | ค่ากำหนดกลาง — อ่าน/เขียนตาราง **`mas_param`** ของระบบ SBP เดิม (ไม่สร้าง `system_configs` ใหม่ · ตัดสินใจ 2026-08-06) · อ่านรายตัว cache 5 นาที |
| POST/PUT/DELETE | `/configs` · `/configs/{key}` | เพิ่ม/แก้/ลบ · `is_editable=false` (ค่าคงที่ธุรกิจ ข้อ 8.2) แก้ผ่าน API ไม่ได้ · ห้ามเก็บ secret |

### 6. Email Template (Notification) · เขียนลงตาราง `email_template` ของระบบ SBP เดิม (5 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/email-templates` · `/email-templates/{code}` | 8 template (EM-01–08) subject/body + ตัวแปร merge — **8 แถวในตาราง `email_template` เดิม** (`subject_format`/`body_format`) การส่งใช้ `@gosoft-sbp/email-lib` และ log ลง `email_sent` |
| PUT | `/email-templates/{code}` | แก้ subject/body — From/To/Cc ล็อกตาม status_email_rules |
| POST | `/email-templates/{code}/reset` · `/email-templates/reset-all` | รีเซ็ตเป็น Default รายตัว/ทั้งหมด |

### 7. รายงาน · K2 3.1.7 + SDD v7.5 (2 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/reports/status-summary` | **รายงานตรวจสอบประกันรายได้ (SBP Mall)** — Preview Report · **บังคับระบุปี** · filter: `status`* (6 ค่า · บังคับเสมอ) · `periodStatement` (**บังคับเมื่อ status = เสร็จสิ้นดำเนินการ** · SDD GI — ปฏิทิน ค.ศ. หรือกรอกเอง) · `result`* (**ประกันรายได้/ไม่ประกันรายได้** · SDD) · `region` (13 รหัส + ภาคใหม่แสดง checkbox อัตโนมัติ) · `storeType` (**A/B/C/E** — ยืนยันจากหน้าจอ K2 จริง 2026-08-06 ไม่ใช่ A/B/C/D) · `impactedStoreCode` · `newStoreCode` |
| GET | `/reports/status-summary/export` | **Export CSV to Batch** — ส่งไฟล์ CSV เข้า Batch ให้ทีมบัญชีนำไปกระทบ SAP (เดิม export .xlsx) · เงื่อนไขเดียวกัน |

### 8. Batch Job Admin · FGI/FCS Jobs 1–10 (6 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/jobs` · `/jobs/{jobNo}` | รายการ 11 entry points + schedule/input/output/current status/run controls |
| PUT | `/jobs/{jobNo}/params` · `/jobs/{jobNo}/enabled` | แก้พารามิเตอร์ (editable เท่านั้น) · เปิด/ปิด |
| POST | `/jobs/{jobNo}/run` | สั่งรันนอกรอบ — รายละเอียด flow อยู่ใน BE/Runbook ไม่ใช่ tab ที่ต้องทำใน FE Batch Monitor |
| GET | `/jobs/{jobNo}/runs` | ประวัติการรัน |

### 9. Workflow ภายใน · K2 3.1.4 + FGI/FCS Job 8b (3 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| POST | `/workflows/instances` | เปิด workflow (แทน K2 StartInstance) — Gen Flow Gate (service token · มี Flowchart) |
| GET | `/workflows/instances/{id}` · `/workflows/summary` | สถานะ instance · ตัวเลขเฝ้าระวัง W/Y/N + งานค้างต่อ section |

### 10. Interface & Dashboard · FGI/FCS (4 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/interfaces/tracking` · `/interfaces/pending-ack` | สถานะรับ–ส่งไฟล์ (interface_transactions) · ACK ค้าง ≥ 1 วัน (Job 10) |
| POST | `/interfaces/sta/ack` | callback ให้ STA ยิง ACK ตรง (API key) |
| GET | `/dashboard/summary` | **ตัวเลข stat cards หน้างานรอดำเนินการ** (cache 5 นาที) — งานรอดำเนินการของ section ผู้ใช้ · ยอดขายไม่ครบ 60 วัน (แถวแดง) · รอเกิน 3 วัน · วงเงินเข้าเส้น AVP (> 50,000) · **ตัดสินใจ 2026-08-06: ยกเลิกหน้า Overview/Dashboard — เส้นนี้ย้ายไปป้อน stat cards ของหน้าแรกใหม่ (k2-list-waiting) แทน · ตัด field `abnormalStores` และ `chart.monthly` ของหน้า Overview เดิมออก** |

## กฎธุรกิจสำคัญที่ผูกกับ API

- **บังคับระบุปี (ค.ศ.)** ใน `/documents` และ `/reports/status-summary` ไม่งั้นตอบ 400 (กติกา SRS · BE ต้องผ่าน `toAD()` ก่อน query เผื่อ client ส่ง พ.ศ. มา)
- **เส้นทางข้ามขั้นที่ section 06** ใน `/documents/{docNo}/actions`: `result = "ส่งหน่วยงานส่งเสริมธุรกิจ SBP"` → `nextSection = "01"` (**ข้ามขั้น 08**) ใช้เมื่อยอดที่ระบบคำนวณถูกต้องแล้วไม่ต้องให้เจ้าหน้าที่คำนวณซ้ำ · `result = "ส่งเจ้าหน้าที่ SBP DSA"` → `nextSection = "08"` (เส้นทางปกติ ให้คำนวณยอดก่อน) · การส่งกลับจาก 01 กลับไปที่ 06 เสมอ ไม่ใช่ 08 (ดูตารางเทียบใน `workflow.md`)
- **กฎวงเงินอนุมัติ (SDD GI 24/02/2026)** ใน `/documents/{docNo}/actions`: เห็นควรชดเชย ≤ 50,000 → **จบที่ GM (02)** · 50,001–300,000 → AVP (03) แล้วจบ (เกิน 300,000 รอ confirm) · เห็นควรไม่ชดเชยที่ 01/02 → **เสร็จสิ้นทันที (ไม่อนุมัติในเดือนนั้น)** · 06 ไม่ชดเชย/หยุด → เสร็จสิ้น · **ตัดขั้นบัญชี 04/05 ตาม SDD v7.5** (ดูตารางเต็มใน `workflow.md`) · เดิมใช้เกณฑ์เดียว 100,000
- **เปิดเรื่องซ้ำได้ (SDD GI)** ใน `POST /documents`: 409 เฉพาะกรณีมีเอกสาร **active** ของร้าน+เดือนนั้น — เอกสารเดิมที่จบด้วยหยุดชดเชย/เห็นควรไม่ชดเชย เปิดเรื่องใหม่ได้ทั้งเดือนเดียวกันและเดือนถัดไป (ยกเลิกการเปิด SR) · กรณีเห็นควรไม่ชดเชย (06) เดือนถัดไประบบสร้างงานเข้า `GET /tasks` อัตโนมัติพร้อม assignee คนเดิม · ยอดชดเชย 0: เดือน 1–3 ส่งต่อ 01 · เดือนที่ 4 หยุดชดเชย
- **งานค้าง (SDD GI)** ใน `GET /tasks`: รองรับ filter + เลือกหลายเอกสาร (bulk action) · เจ้าหน้าที่/ฝ่าย SBP DSA เห็นเอกสารได้ทุกสาขา (ไม่จำกัดงานตน) · ทีมส่งเสริม/บัญชีตามสิทธิ์เดิม
- **filter `result`** ใน report = **ประกันรายได้ / ไม่ประกันรายได้** (SDD v7.5 · Radio บังคับ) อิง **ผลพิจารณาล่าสุด** (`consideration_logs.result_category` = APPROVE/REJECT) — ขั้นบัญชี 05 ที่เคยอ้างถูกตัดออกแล้ว
- **%ชดเชยรวม = 100%** ใน `PUT /documents/{docNo}` · **เงินชดเชยต่อร้านเปิดใหม่ = ยอดชดเชยของร้านถูกกระทบ × %ชดเชย** คำนวณและปัดเศษที่ **BE** แล้วส่งกลับเป็น `compensateAmount` (FE ห้ามคูณเอง — กันยอดปัดเศษไม่ตรงกับที่บัญชีใช้) · ผลรวม `compensateAmount` ทุกร้านต้องเท่ากับยอดชดเชยของร้านถูกกระทบพอดี — เป็นแหล่งข้อมูลของกราฟ "สัดส่วนเงินชดเชยรายร้านเปิดใหม่" ใน `k2-document.html` (ไม่มี endpoint แยกสำหรับกราฟ)
- API payload ใช้ `newStoreCode` สำหรับรหัสร้านเปิดใหม่ 5 หลัก (เช่น `"00990"`) เพื่อคง leading zero **ทั้งใน response ของ `GET /documents/{docNo}` และ request ของ `PUT /documents/{docNo}`** (ห้ามใช้ `storeCode` ในสองเส้นนี้ — สงวนไว้ให้ร้านถูกกระทบ); internal table `document_new_stores.id` เป็น key ภายใน ไม่ expose เป็น field code
- **ลบรายการที่เลือก (bulk remove)** ของร้านคู่แข่ง/ปัจจัยอื่นๆ ในหน้าเอกสาร ไม่มี endpoint แยก — FE ลบแถวใน state แล้วส่งอาร์เรย์ชุดใหม่ทั้งชุดผ่าน `PUT /documents/{docNo}` · BE ลบรายการที่หายไปจากอาร์เรย์ (DELETE ... NOT IN) ในทรานแซกชันเดียวกัน · ปุ่มลบ/checkbox แสดงเฉพาะ role ที่แก้ส่วนนั้นได้ (ปัจจุบันคือ section 01)
- **เลขเอกสาร YYYY/xxxxx** (ปี **ค.ศ.** · running ต่อปี เริ่ม 00001) · **เลขเอกสารและวันที่ทั้งระบบเป็น ค.ศ.** (ตัดสินใจ 2026-08-06 — ยึดตามระบบ SBP ปัจจุบัน: DatePicker ของ FE ตั้งค่า `buddhistEra = false` เป็นค่าเริ่มต้น และ BE มี helper `toAD(y) = y >= 2500 ? y - 543 : y` บังคับแปลงค่าที่หลุดมาเป็น พ.ศ. ให้เป็น ค.ศ. · แสดงผลเป็น พ.ศ. ได้เฉพาะจุดที่เปิด `buddhistEra` ที่ระดับ component เท่านั้น · ภาพหน้าจอ K2 จริงก็ใช้ ค.ศ. เช่นกัน เช่น `2026/01870`)
- **Gen Flow Gate** ใน `/workflows/instances` (เกณฑ์คงเดิมทุกข้อ — ดูขั้น 6 ใน `workflow.md`)
- `POST /workflows/instances` เป็น BE internal Workflow Engine contract สำหรับ Job 8b เท่านั้น ไม่ใช่งาน FE/Flow page: request `{impactProcessId, sourceJobNo:"8b", requestId}`; ผ่าน gate → สร้าง/คืน `{docNo, instanceId, workflowGenerationStatus:"Y", firstSection:"06", statusCode:"06"}`; fail ถาวร (branch type นอกเซ็ต, ระยะทางเกิน, DV หาย, นิติบุคคลเดียวกัน หรือ growth > −10) → ตั้ง `N`; เฉพาะ distance/juristic/growth เป็น NULL หรือ sales_status ยังไม่พร้อม → คง `W` และคืน 422/reason เพื่อ rerun
- **แก้ master ต้องระบุ reason → audit_logs** ทุกครั้ง (factors/configs/email-templates) · การแก้สิทธิ์/กลุ่มผู้ใช้ลง audit ของระบบเดิม
- ทุกเส้นที่แก้ข้อมูลบันทึกผู้ทำ (จาก JWT) ลง audit ตามโดเมน (consideration_logs / audit_logs / job_run_histories)

## การกระทบยอด SAP และแก้ข้อมูลผิดปกติ (SDD v7.5)

ยกเลิกหน้าจอ Approve ของบัญชีและ**ยกเลิกสถานะบัญชีในเอกสาร 2 ค่า** — To-Be ทีมบัญชี **ตรวจสอบยอด + จัดเก็บสร้างรายการบันทึกบัญชี ผ่านหน้ารายงาน**: `GET /reports/status-summary` (Preview Report · **สถานะเป็น dropdown บังคับ 6 ค่า ไม่มีสถานะบัญชี**) + `/export` (Export CSV to Batch) แล้วกระทบยอดกับ SAP เอง งานฝั่ง SAP อยู่นอก API ชุดนี้:
- **SAP** `FBL3H` (GL Account Line-Item Browser — กระทบยอด) · `SAPPOST` (Update Transaction to SAP) · `FS/FSWEB` (ตรวจ STATUS=Completed)
- **กรณี SBP ผิดแต่ SAP ถูก** → เปิด **SR (Service Request)** ให้ทีมดูแล SBP แก้รายครั้ง (ผ่านระบบ ticketing เดิม — ไม่เพิ่ม endpoint)
- **ข้อเสนอ:** SBP **Auto Update** จาก SAP โดยไม่ต้องเปิด SR ทุกครั้ง — **BSR = Out of Scope** ของโครงการ Replacement SBP

## กลุ่มข้อมูลผิดปกติ / แจกงาน — ยกเลิกและลบทิ้ง (ตัดสินใจ 2026-08-06 · 2 เส้น)

**ลบทิ้งแล้ว** — ทั้ง 2 endpoint ถูกเอาออกจาก `plan-api.html` (GROUPS) และไฟล์หน้าจอ `k2-list-abnormal.html` ถูกลบออกจากโปรเจกต์:
- `GET /abnormal-stores` — ร้านข้อมูลผิดปกติ (ยอดขาย < 60 วัน) จาก pipeline batch
- `POST /abnormal-stores/assign` — แจกงานให้เจ้าหน้าที่ตรวจสอบ (role 05)

**ทดแทนด้วย:** ข้อมูลผิดปกติเป็น *ธงของแถว* ไม่ใช่หน้าจอแยก — `GET /tasks` และ `GET /documents` คืน `salesDataDays` ให้ FE ทำแถวแดง + ตัวกรอง "ยอดขายไม่ครบ 60 วัน" · ตัวเลขสรุปอยู่ใน `GET /dashboard/summary` · การจ่ายงานใช้ auto-assign ของ SDD GI (เจ้าของงานคนเดิม) แทนการแจกงานด้วยมือ

## เส้นที่ตัดออก — ใช้ระบบ SBP เดิม (ตัดสินใจ 2026-08-05 · 18 เส้น)

comment ไว้ใน `plan-api.html` (GROUPS) พร้อมหมายเหตุ — ไม่ใช่ "รอตัดสินใจ" แต่เป็นการตัดถาวรเพราะระบบ SBP ปัจจุบันมีอยู่แล้ว (คู่กับหน้า `k2-permissions.html` / `k2-operators.html` ที่ถอดจาก sidebar):

| กลุ่มเดิม | เส้นที่ตัด | ใช้ของระบบเดิมแทน |
|---|---|---|
| Auth & สิทธิ์ผู้ใช้ (4) | `POST /auth/login` · `POST /auth/refresh` · `GET /auth/me` · `GET /me/menus` | BFF: login redirect (Cognito·cookie) · `/auth/refresh` · `/auth/profile`+`/users/current` · `/menus` |
| Master ผู้ปฏิบัติงาน (5) | `GET/POST/PUT/DELETE /operators` · `/operators/{id}` · `GET /employees/search` | group+scope ของ auth-backend (จัดการหน้า `/setting/manage-user-rights`) · ค้นพนักงานผ่าน employee backend เดิม |
| Master สิทธิ์เมนู (9) | `GET /menu-permissions` · `PUT /menu-permissions/{menuCode}` · `GET/POST/PUT/DELETE /roles` · `/roles/{roleCode}` · `POST/PUT/DELETE /menus` · `/menus/{menuCode}` | auth-backend: `/groups` · `/groups/{id}/permissions` · `/groups/permissions/template` · `/menus` |

## เส้นที่เปลี่ยนไปใช้ของระบบ SBP เดิม (ตัดสินใจ 2026-08-06 · 3 ตัด + 5 เปลี่ยนแหล่งข้อมูล)

ตรวจ `SBP/README.md` + repo `srm-sps-spsap-store-backend` (79 entity · 25 controller) แล้วยึด**ของที่มีอยู่จริงเป็นหลัก**:

### ตัดออก 3 เส้น — มี API พร้อมใช้อยู่แล้ว

| เส้นเดิมของ SBPGI | ใช้ของระบบ SBP แทน |
|---|---|
| `GET /stores/search` | `GET /store/search` · `/store/list` · `/store/detail` · `/store/opt-name` (ตาราง `store`/`mas_store`/`sevenshop`) |
| `GET /zones` | `GET /store/all-regions` · `/store/regions-by-email` · `/store/province-by-region` (ตาราง `mas_zone`) |
| `GET /branch-types` | `GET /common/common-code` · `/master/common` (ตาราง `common_code` — คนละ `code_type`) |

### คงเส้นไว้ แต่เปลี่ยนแหล่งข้อมูลไปที่ของระบบเดิม

| เส้น | เดิมอ่าน/เขียนตาราง | เปลี่ยนเป็น |
|---|---|---|
| `GET /tasks` | `workflow_tasks` ของ SBPGI | **`@srm/glb-workflow`** — `getPendingFlow({userData:{userId, groupId}, versionId})` แล้ว join ข้อมูลเอกสารของ SBPGI · inbox รวมทุกระบบที่มีอยู่แล้วคือ `GET /api/workflow/pending` (store-backend) |
| `POST /documents/{docNo}/actions` | `workflow_instances` + `workflow_tasks` | `triggerEvent({versionId, referenceId: docNo, event, remark, userId, nextApproverId})` ของ engine · ผู้อนุมัติขั้นถัดไปใช้ `addPreparedApprover()` |
| `GET /documents/{docNo}/timeline` | `consideration_logs` อย่างเดียว | `getHistory()` ของ engine (state transition) **join** `consideration_logs` ของ SBPGI (decision · ไฟล์แนบ · ความเห็น) |
| `GET /workflow-sections` · `GET /document-statuses` | `workflow_sections` / `document_statuses` | `workflow_state` / `workflow_route` / `workflow_status` ของ engine + **วงเงินอนุมัติจาก `common_code`** (`code_type = SBPGI_APPROVE_LIMIT`) |
| `GET/PUT /email-templates/*` | `email_templates` ของ SBPGI | ตาราง **`email_template`** เดิม (`email_template_id` · `subject_format` · `body_format`) · การส่งใช้ `@gosoft-sbp/email-lib` และ log ลง `email_sent` — ไม่เขียน mail sender เอง |
| `GET/PUT /configs` | `system_configs` ของ SBPGI | ตาราง **`mas_param`** เดิม (เพิ่มคอลัมน์ที่ขาดในตารางเดิม ไม่สร้างตารางใหม่) |
| `POST /documents/{docNo}/attachments` · `GET .../download` | เขียน storage layer เอง | เก็บ metadata ใน `document_attachments` ของ SBPGI แต่ **ไฟล์ใช้ service S3 เดิม** `POST /statement/upload-file-aws` · `POST /statement/download-file-aws` |

**Envelope ต้องตรงกับของเดิม:** สำเร็จ `{"success": true, "data": …}` · ผิดพลาด `{"success": false, "data": null, "error": {"code","message"}}` (ResponseInterceptor + HttpExceptionFilter ของ store-backend) — ข้อความ error ยังต้องเป็นไทย verbatim ตาม SRS

## ลิงก์ภายนอกและฟีเจอร์ที่ไม่มี endpoint (ยืนยันจากหน้าจอ K2 เดิม · 2026-08-06)

| จุดในหน้าจอ | เป็นอะไร |
|---|---|
| **ข้อมูลยอดขายเพิ่มเติม** | K2 เดิมลิงก์ออก **QlikView BI** (`bidashboard.cpall.co.th/qlikview/FormLogin.htm`) — ระบบใหม่ใช้ `GET /documents/{docNo}/sales` สำหรับกราฟในหน้า และ**คงลิงก์ BI ไว้เป็นทางเลือกเชิงลึก** (URL เก็บใน config ไม่ hardcode) |
| **คลิกเปิดเอกสาร Statement** | ลิงก์ตรงจาก `compensation_documents.statement_id` (ฟิลด์ที่ 10 ของไฟล์ `BPM06001O_`) — ไม่ใช่ endpoint ของ SBPGI |
| **แผนที่ AllMap** | `compensation_documents.allmap_url` (ฟิลด์ที่ 9 ของไฟล์ `BPM06001O_`) · **iframe ล้มได้จริง** (`Failed to fetch` ในภาพหน้าจอ) → FE ต้องมี fallback + ปุ่มเปิดแท็บใหม่ |
| **คำนวณเงินชดเชย (ขั้น 08)** | **iframe ของระบบ Finance & Account Unit (FS)** — ไม่ใช่หน้าจอของ SBPGI · ถ้าไม่ได้ล็อกอิน FS จะได้ `401 Unauthorized` → ต้องแสดงข้อความและปุ่มเปิดแท็บใหม่แทนกรอบเปล่า |
| **Copy Doc Link** · **Quick Search** · **Selected Filter (preset)** · **sort หัวคอลัมน์** | ฟีเจอร์ฝั่ง FE ล้วน — ไม่มี endpoint (preset เก็บใน `localStorage` ของเครื่องผู้ใช้) |

## เอกสารที่เกี่ยวข้อง

- ตารางที่แต่ละเส้นอ่าน/เขียน: [database.md](database.md) · `plan-database.html` (24 ตาราง)
- Flow ที่ API ขับเคลื่อน: [workflow.md](workflow.md) · `plan-flow.html`
- Email จุดส่งในแต่ละสถานะ: `email-template.html` (8 templates)
