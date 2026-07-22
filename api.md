# API — REST /api/v1 (ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุป REST API ทั้งหมดของระบบใหม่ สำหรับ Frontend SPA และงานภายใน
> **แหล่งอ้างอิงหลัก:** `plan-api.html` (หน้า API · sidebar group `Plan`)
> **อ้างอิงประกอบ:** `database.md` / `plan-database.html` (ตารางที่แต่ละเส้นอ่าน/เขียน) · `workflow.md` / `plan-flow.html` (flow) · SRS ประกันรายได้-K2 v3.1 · เอกสาร Batch v4.0
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง API ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-api.html` ให้ตรงกัน · ถ้ากระทบตาราง/flow ต้องอัปเดต `database.md`/`workflow.md` คู่กันด้วย

## ภาพรวม

- **62 เส้น · 10 กลุ่มตามโดเมน** เป็น reference contract สำหรับ FE/BE alignment (+ กลุ่มข้อมูลผิดปกติ 2 เส้นที่ comment รอตัดสินใจ — ดูท้ายไฟล์)
- Base URL `/api/v1` · Auth: `Authorization: Bearer <JWT>` (Role 00–10) ยกเว้น login/refresh และ callback ภายนอก (API key/service token)
- **Scope note:** Auth Group 1 เป็น platform-provided/reference contract นอกงาน implement Login/Auth ของ SBP Mall; FE ใช้ `/auth/me` และ `/me/menus` เมื่อ platform token/menu service พร้อมเท่านั้น
- แบ่งหน้า `?page=1&size=20` → ตอบ `{"page","size","total","items":[]}`
- Error รูปแบบเดียวกันทุกเส้น `{"code":"DOC_409","message":"ข้อความไทยตรงตาม SRS"}` — **ข้อความ popup ต้องตรงตัวตาม SRS**
- วันที่ใน payload = ISO-8601 + ปี ค.ศ. (FE แปลงแสดง พ.ศ.) · JSON UTF-8 ทุกเส้น (เลิก TIS-620)
- Code namespace ต้องไม่ตีความปนกัน: `roleCode` = RBAC role 00/01/02/03/04/05/06/10, `sectionCode` = workflow section 06/08/01/02/03, `statusCode` = document status lookup; ทุก response ที่ต้องแสดงสถานะให้ส่ง code เป็น canonical value แล้ว FE resolve label จาก `/document-statuses`
- Batch Monitor scope note: API กลุ่ม Batch Job Admin เป็น reference contract สำหรับ 2 tab ของ FE Batch Monitor เท่านั้น (`แบบฟอร์มพารามิเตอร์`, `ประวัติการรัน`); ไม่ออกแบบ tab Flowchart การทำงาน, step-by-step batch flow, หรือ Database ที่ใช้ของ batch job ใน `plan-api.html` และไม่ต้องใส่รายละเอียด endpoint รายเส้นในเอกสาร FE หน้านั้น
- ป้ายที่มาต่อเส้น: **(FGI/FCS)** เอกสาร Batch v4.0 · **(K2)** SRS v3.1 · **(ใหม่)** เพิ่มในระบบใหม่ · **(ผสม)**

## สัญญากลาง API/FE ที่ทุก endpoint ต้องใช้

> รายละเอียด LLDD กลาง: `LLDD/BE/LLDD-BE-API-Common-Contracts.md` และ `LLDD/FE/LLDD-FE-Integration-Contracts.md`

| หมวด | Contract กลาง | ผู้รับผิดชอบ / ใช้โดย |
|---|---|---|
| Transport | Base URL `/api/v1` · JSON `application/json; charset=utf-8` · multipart เฉพาะ attachments | BE ทุก controller · FE shared API client |
| Auth | User endpoint ใช้ `Authorization: Bearer <JWT>`; internal workflow/batch callback ใช้ service token; Auth Group 1 เป็น platform reference | Platform/IAM จัดหา token/menu; BE validate; FE consume |
| Error | ทุก error คืน `{code,message}` เท่านั้น · `message` เป็นไทย verbatim ตาม SRS ถ้ามีข้อความกำหนด | BE error handler · FE แสดง `message` ตรง ๆ |
| HTTP status | 400 validation · 401 auth · 403 forbidden/RBAC · 404 not found · 409 duplicate/current-task conflict · 422 business rule · 413 file too large · 415 unsupported file | BE middleware/service · FE error state |
| Pagination | GET list ทุกเส้นรับ `page,size` และคืน `{page,size,total,items}` | BE repository/query · FE DataTable/Pager |
| Format | `docNo` = `YYYY/xxxxx` พ.ศ. · `storeCode/newStoreCode` เป็น string 5 หลักคง leading zero · date/month ใน payload เป็น ค.ศ. ISO · amount/percent เป็น number 2 decimals | BE validate/serialize · FE format display |
| Workflow transition | `/documents/{docNo}/actions` รับ `{result,comment}` โดย `result` เป็น 6-enum ไทย verbatim และคืน `{nextSection,statusCode,message}`; positive path คือ `06→08→01→02→03→99` โดย `99` = เสร็จสิ้นและ `nextSection=null`; ที่ Section 02 ยอด ≤100,000 จบเป็น 99 โดยไม่ผ่าน 03 | BE Workflow Action เป็น source of truth; FE ไม่คำนวณ route เอง |
| RBAC/Menu | `/me/menus` เป็น source ของ sidebar/route guard · `GET /documents/{docNo}` คืน `permissions.canEditSections` และ `permissions.canAction` | BE RBAC/task-owner guard · FE เปิด/ปิด UI |
| Audit/Reason | mutation master/config/email/RBAC ต้องมี `reason`; workflow action ลง `consideration_logs`; batch ลง `job_run_histories` | BE transaction/audit service · FE บังคับ reason field |
| Idempotency | endpoint ที่สร้างจาก job/service ใช้ `requestId` หรือ business key; duplicate ต้องคืน existing result หรือ 409 ตามกฎ endpoint | BE service · Job rerun |

## โครงหน้าจอ plan-api (modal รายละเอียดต่อ endpoint)

catalog รวมทุกเส้น → คลิกแถว → เปิด modal ที่มีโครงดังนี้ (ดู `selectEp()` ใน `plan-api.html`):

1. **ชิป** ที่มา · สิทธิ์ · กลุ่ม
2. **Flow (ลำดับการทำงาน)** — แสดง **นอกแท็บ** (ไม่ใช่แท็บแล้ว) เหนือแท็บ · ถ้าเส้นนั้นมี flowchart จะมี pill "มี Flowchart ในแท็บ 3" · ยกเว้นกลุ่ม Batch Job Admin ซึ่งแสดงเป็น reference note เท่านั้น
3. **แท็บ 1 · Request / Response** — request (query/body) + response + Error ที่ต้องรองรับ
4. **แท็บ 2 · Database + SQL** — ตารางที่เกี่ยวข้อง (R/W/RW) + **ตัวอย่าง SQL ต่อเส้น** (illustrative, bind params ขึ้นต้น `:`) เก็บใน `SQL_BY_PATH` keyed ด้วย `'METHOD path'` — ไม่แสดงในกลุ่ม Batch Job Admin
5. **แท็บ 3 · Flowchart** — โผล่**เฉพาะ 3 เส้นที่ซับซ้อน** (มี branching/หลายขั้น) · เป็น inline SVG เรนเดอร์จาก node spec ใน `FLOWCHART_BY_PATH` ผ่าน mini-renderer `renderFlow()` · ไม่แสดงในกลุ่ม Batch Job Admin

**3 เส้นที่มีแท็บ Flowchart:** `POST /documents/{docNo}/actions` (routing 5 ขั้น + กฎ 100,000) · `POST /workflows/instances` (Gen Flow Gate) · `POST /documents` (สร้าง + กันซ้ำ)

## รายการ endpoint ทั้ง 10 กลุ่ม

### 1. Auth & สิทธิ์ผู้ใช้ · K2 3.1.1 (4 เส้น · platform reference)
| Method | Path | ทำอะไร |
|---|---|---|
| POST | `/auth/login` | login แลก JWT (accessToken 30 นาที / refreshToken 8 ชม.) |
| POST | `/auth/refresh` | ต่ออายุ accessToken |
| GET | `/auth/me` | ข้อมูลผู้ใช้ปัจจุบันจาก JWT |
| GET | `/me/menus` | เมนูที่ role เข้าถึงได้ (สร้าง sidebar) |

### 2. งาน & เอกสารประกันรายได้ · K2 3.1.2/3/4/6 (10 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/tasks` | งานรอท่านดำเนินการ (inbox ของ section — k2-list-waiting) |
| GET | `/documents` | ค้นหาเอกสารที่เกี่ยวข้อง — **บังคับระบุปี** |
| GET | `/documents/{docNo}` | เอกสารฉบับเต็ม 12 ส่วน + ธงสิทธิ์แก้ต่อ role/section |
| POST | `/documents` | สร้างเอกสาร (MANUAL/FS) — ออกเลข YYYY/xxxxx + เปิด workflow (มี Flowchart) |
| PUT | `/documents/{docNo}` | บันทึกส่วนย่อย (ร้านใหม่/คู่แข่ง/ปัจจัย) · **%ชดเชยรวม = 100%** |
| POST | `/documents/{docNo}/actions` | ส่งผลพิจารณา — หัวใจ workflow 5 ขั้น · กฎ 100,000 (มี Flowchart) |
| GET | `/documents/{docNo}/timeline` | ประวัติพิจารณาทุกขั้น |
| POST | `/documents/{docNo}/attachments` | แนบไฟล์ ≤ 5MB |
| GET | `/documents/{docNo}/attachments/{attachId}/download` | ดาวน์โหลดไฟล์แนบผ่าน BE authorization + AV clean guard |
| GET | `/documents/{docNo}/sales` | **(ใหม่ session นี้)** ยอดขาย 4 หน้าต่าง × 15 วัน — ปุ่ม "ข้อมูลยอดขายเพิ่มเติม" + กราฟยอดขายในหน้าเอกสาร |

### 3. ข้อมูลอ้างอิง (Lookup / Reference) · K2 + FGI/FCS **(ใหม่ session นี้ · 4 เส้น)**
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/stores/search` | ค้นหาร้าน (`type=impacted`→impacted_stores / `type=new`→stores) — แว่นขยายใน k2-create |
| GET | `/competitors` | master ร้านคู่แข่ง 24 ราย — dropdown เพิ่มคู่แข่งในเอกสาร |
| GET | `/document-statuses` | รายการสถานะเอกสาร — dropdown ตัวกรอง (ค้นหา/รายงาน) |
| GET | `/workflow-sections` | รายการ Section 5 ขั้น (06/08/01/02/03) — dropdown ตำแหน่ง/ตัวกรอง |

### 4. Master Data · K2 3.1.1/8/9 (19 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET/POST/PUT/DELETE | `/operators` · `/operators/{id}` | ผู้ปฏิบัติงาน (operator_assignments) — แก้/ลบต้องระบุ reason → audit_logs |
| GET/POST/PUT/DELETE | `/factors` · `/factors/{code}` | ปัจจัยภายนอก (external_factors) — รหัสห้ามซ้ำ · reason บังคับ |
| GET | `/employees/search` | ค้นหาพนักงานจาก master `employees` (popup 3.1.8) |
| GET | `/menu-permissions` | matrix สิทธิ์เมนู 8 role |
| PUT | `/menu-permissions/{menuCode}` | บันทึกสิทธิ์รายเมนู |
| GET/POST/PUT/DELETE | `/roles` · `/roles/{roleCode}` | CRUD Role — role ระบบ (is_system) กันลบ/แก้รหัส |
| POST/PUT/DELETE | `/menus` · `/menus/{menuCode}` | CRUD เมนู — เพิ่ม/ลบ cascade สิทธิ์ทุก role |
| GET | `/audit-logs` | ประวัติแก้ master (= MaintainMasterHistory เดิม) |

### 5. System Config (Global) · ใหม่ (5 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/configs` · `/configs/{key}` | ค่ากำหนดกลาง (system_configs) · อ่านรายตัว cache 5 นาที |
| POST/PUT/DELETE | `/configs` · `/configs/{key}` | เพิ่ม/แก้/ลบ · `is_editable=false` (ค่าคงที่ธุรกิจ ข้อ 8.2) แก้ผ่าน API ไม่ได้ · ห้ามเก็บ secret |

### 6. Email Template (Notification) · ใหม่ (5 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/email-templates` · `/email-templates/{code}` | 8 template (EM-01–08) subject/body + ตัวแปร merge |
| PUT | `/email-templates/{code}` | แก้ subject/body — From/To/Cc ล็อกตาม status_email_rules |
| POST | `/email-templates/{code}/reset` · `/email-templates/reset-all` | รีเซ็ตเป็น Default รายตัว/ทั้งหมด |

### 7. รายงาน · K2 3.1.7 + SDD v7.5 (2 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/reports/status-summary` | **รายงานตรวจสอบประกันรายได้ (SBP Mall)** — Preview Report · **บังคับระบุปี** · filter: `status`* (6 ค่า) · `result`* (**ประกันรายได้/ไม่ประกันรายได้** · SDD) · `region` (13 รหัส) · `storeType` (A/B/C/D) · `impactedStoreCode` · `newStoreCode` |
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
| GET | `/dashboard/summary` | ตัวเลขหน้า Dashboard (cache 5 นาที) |

## กฎธุรกิจสำคัญที่ผูกกับ API

- **บังคับระบุปี (พ.ศ.)** ใน `/documents` และ `/reports/status-summary` ไม่งั้นตอบ 400 (กติกา SRS)
- **กฎวงเงิน 100,000** ใน `/documents/{docNo}/actions`: ชดเชย/ไม่ชดเชย > 100,000 → AVP (03) แล้วจบ · ชดเชย ≤ 100,000 → **จบที่ GM (02)** · 06 ไม่ชดเชย/หยุด → เสร็จสิ้น · **ตัดขั้นบัญชี 04/05 ตาม SDD v7.5** (ดูตารางเต็มใน `workflow.md`)
- **filter `result`** ใน report = **ประกันรายได้ / ไม่ประกันรายได้** (SDD v7.5 · Radio บังคับ) อิง **ผลพิจารณาล่าสุด** (`consideration_logs.result_category` = APPROVE/REJECT) — ขั้นบัญชี 05 ที่เคยอ้างถูกตัดออกแล้ว
- **%ชดเชยรวม = 100%** ใน `PUT /documents/{docNo}`
- API payload ใช้ `newStoreCode` สำหรับรหัสร้านเปิดใหม่ 5 หลัก (เช่น `"00990"`) เพื่อคง leading zero; internal table `document_new_stores.id` เป็น key ภายใน ไม่ expose เป็น field code
- **เลขเอกสาร YYYY/xxxxx** (ปี พ.ศ. · running ต่อปี เริ่ม 00001)
- **Gen Flow Gate** ใน `/workflows/instances` (เกณฑ์คงเดิมทุกข้อ — ดูขั้น 6 ใน `workflow.md`)
- `POST /workflows/instances` เป็น BE internal Workflow Engine contract สำหรับ Job 8b เท่านั้น ไม่ใช่งาน FE/Flow page: request `{impactProcessId, sourceJobNo:"8b", requestId}`; ผ่าน gate → สร้าง/คืน `{docNo, instanceId, workflowGenerationStatus:"Y", firstSection:"06", statusCode:"06"}`; fail ถาวร (branch type นอกเซ็ต, ระยะทางเกิน, DV หาย, นิติบุคคลเดียวกัน หรือ growth > −10) → ตั้ง `N`; เฉพาะ distance/juristic/growth เป็น NULL หรือ sales_status ยังไม่พร้อม → คง `W` และคืน 422/reason เพื่อ rerun
- **แก้ master ต้องระบุ reason → audit_logs** ทุกครั้ง (operators/factors/roles/menus/configs/email-templates)
- ทุกเส้นที่แก้ข้อมูลบันทึกผู้ทำ (จาก JWT) ลง audit ตามโดเมน (consideration_logs / audit_logs / job_run_histories)

## การกระทบยอด SAP และแก้ข้อมูลผิดปกติ (SDD v7.5)

ยกเลิกหน้าจอ Approve ของบัญชี — ทีมบัญชีใช้ `GET /reports/status-summary` (Preview) + `/export` (Export CSV to Batch) แล้วกระทบยอดกับ SAP เอง งานฝั่ง SAP อยู่นอก API ชุดนี้:
- **SAP** `FBL3H` (GL Account Line-Item Browser — กระทบยอด) · `SAPPOST` (Update Transaction to SAP) · `FS/FSWEB` (ตรวจ STATUS=Completed)
- **กรณี SBP ผิดแต่ SAP ถูก** → เปิด **SR (Service Request)** ให้ทีมดูแล SBP แก้รายครั้ง (ผ่านระบบ ticketing เดิม — ไม่เพิ่ม endpoint)
- **ข้อเสนอ:** SBP **Auto Update** จาก SAP โดยไม่ต้องเปิด SR ทุกครั้ง — **BSR = Out of Scope** ของโครงการ Replacement SBP

## กลุ่มที่ comment รอตัดสินใจ

**ข้อมูลผิดปกติ / แจกงาน (2 เส้น)** — comment อยู่ใน `plan-api.html` (GROUPS) คู่กับหน้า `k2-list-abnormal.html` ที่ปิดชั่วคราว:
- `GET /abnormal-stores` — ร้านข้อมูลผิดปกติ (ยอดขาย < 60 วัน) จาก pipeline batch
- `POST /abnormal-stores/assign` — แจกงานให้เจ้าหน้าที่ตรวจสอบ (role 05)

เปิดคืนได้โดยลบ comment (นับเป็น 64 เส้น 11 กลุ่ม)

## เอกสารที่เกี่ยวข้อง

- ตารางที่แต่ละเส้นอ่าน/เขียน: [database.md](database.md) · `plan-database.html` (34 ตาราง)
- Flow ที่ API ขับเคลื่อน: [workflow.md](workflow.md) · `plan-flow.html`
- Email จุดส่งในแต่ละสถานะ: `plan-email.html` (8 templates)
