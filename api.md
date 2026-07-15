# API — REST /api/v1 (ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุป REST API ทั้งหมดของระบบใหม่ สำหรับ Frontend SPA และงานภายใน
> **แหล่งอ้างอิงหลัก:** `plan-api.html` (หน้า API · sidebar group `Plan`)
> **อ้างอิงประกอบ:** `database.md` / `plan-database.html` (ตารางที่แต่ละเส้นอ่าน/เขียน) · `workflow.md` / `plan-flow.html` (flow) · SRS ประกันรายได้-K2 v3.1 · เอกสาร Batch v4.0
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง API ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-api.html` ให้ตรงกัน · ถ้ากระทบตาราง/flow ต้องอัปเดต `database.md`/`workflow.md` คู่กันด้วย

## ภาพรวม

- **61 เส้น · 10 กลุ่มตามโดเมน** (+ กลุ่มข้อมูลผิดปกติ 2 เส้นที่ comment รอตัดสินใจ — ดูท้ายไฟล์)
- Base URL `/api/v1` · Auth: `Authorization: Bearer <JWT>` (Role 00–10) ยกเว้น login/refresh และ callback ภายนอก (API key/service token)
- แบ่งหน้า `?page=1&size=20` → ตอบ `{"page","size","total","items":[]}`
- Error รูปแบบเดียวกันทุกเส้น `{"code":"DOC_409","message":"ข้อความไทยตรงตาม SRS"}` — **ข้อความ popup ต้องตรงตัวตาม SRS**
- วันที่ใน payload = ISO-8601 + ปี ค.ศ. (FE แปลงแสดง พ.ศ.) · JSON UTF-8 ทุกเส้น (เลิก TIS-620)
- ป้ายที่มาต่อเส้น: **(FGI/FCS)** เอกสาร Batch v4.0 · **(K2)** SRS v3.1 · **(ใหม่)** เพิ่มในระบบใหม่ · **(ผสม)**

## โครงหน้าจอ plan-api (modal รายละเอียดต่อ endpoint)

catalog รวมทุกเส้น → คลิกแถว → เปิด modal ที่มีโครงดังนี้ (ดู `selectEp()` ใน `plan-api.html`):

1. **ชิป** ที่มา · สิทธิ์ · กลุ่ม
2. **Flow (ลำดับการทำงาน)** — แสดง **นอกแท็บ** (ไม่ใช่แท็บแล้ว) เหนือแท็บ · ถ้าเส้นนั้นมี flowchart จะมี pill "มี Flowchart ในแท็บ 3"
3. **แท็บ 1 · Request / Response** — request (query/body) + response + Error ที่ต้องรองรับ
4. **แท็บ 2 · Database + SQL** — ตารางที่เกี่ยวข้อง (R/W/RW) + **ตัวอย่าง SQL ต่อเส้น** (illustrative, bind params ขึ้นต้น `:`) เก็บใน `SQL_BY_PATH` keyed ด้วย `'METHOD path'` — ครบทั้ง 61 เส้น
5. **แท็บ 3 · Flowchart** — โผล่**เฉพาะ 4 เส้นที่ซับซ้อน** (มี branching/หลายขั้น) · เป็น inline SVG เรนเดอร์จาก node spec ใน `FLOWCHART_BY_PATH` ผ่าน mini-renderer `renderFlow()`

**4 เส้นที่มีแท็บ Flowchart:** `POST /documents/{docNo}/actions` (routing 5 ขั้น + กฎ 100,000) · `POST /workflows/instances` (Gen Flow Gate) · `POST /documents` (สร้าง + กันซ้ำ) · `POST /jobs/{jobNo}/run` (guard กันรันซ้อน)

## รายการ endpoint ทั้ง 10 กลุ่ม

### 1. Auth & สิทธิ์ผู้ใช้ · K2 3.1.1 (4 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| POST | `/auth/login` | login แลก JWT (accessToken 30 นาที / refreshToken 8 ชม.) |
| POST | `/auth/refresh` | ต่ออายุ accessToken |
| GET | `/auth/me` | ข้อมูลผู้ใช้ปัจจุบันจาก JWT |
| GET | `/me/menus` | เมนูที่ role เข้าถึงได้ (สร้าง sidebar) |

### 2. งาน & เอกสารประกันรายได้ · K2 3.1.2/3/4/6 (9 เส้น)
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
| GET/PUT | `/menu-permissions` · `/menu-permissions/{menuCode}` | matrix สิทธิ์เมนู 8 role |
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
| GET | `/jobs` · `/jobs/{jobNo}` | รายการ 11 entry points + รายละเอียด/พารามิเตอร์ |
| PUT | `/jobs/{jobNo}/params` · `/jobs/{jobNo}/enabled` | แก้พารามิเตอร์ (editable เท่านั้น) · เปิด/ปิด |
| POST | `/jobs/{jobNo}/run` | สั่งรันนอกรอบ — guard กันรันซ้อน (มี Flowchart) |
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
- **เลขเอกสาร YYYY/xxxxx** (ปี พ.ศ. · running ต่อปี เริ่ม 00001)
- **Gen Flow Gate** ใน `/workflows/instances` (เกณฑ์คงเดิมทุกข้อ — ดูขั้น 6 ใน `workflow.md`)
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

เปิดคืนได้โดยลบ comment (นับเป็น 63 เส้น 11 กลุ่ม)

## เอกสารที่เกี่ยวข้อง

- ตารางที่แต่ละเส้นอ่าน/เขียน: [database.md](database.md) · `plan-database.html` (34 ตาราง)
- Flow ที่ API ขับเคลื่อน: [workflow.md](workflow.md) · `plan-flow.html`
- Email จุดส่งในแต่ละสถานะ: `plan-email.html` (8 templates)
