# API — REST /api/v1 (ระบบใหม่ SBPGI)

> **เอกสารมีชีวิต (living doc)** — สรุป REST API ทั้งหมดของระบบใหม่ สำหรับ Frontend SPA และงานภายใน
> **แหล่งอ้างอิงหลัก:** `plan-api.html` (หน้า API · sidebar group `Plan`)
> **อ้างอิงประกอบ:** `database.md` / `plan-database.html` (ตารางที่แต่ละเส้นอ่าน/เขียน) · `workflow.md` / `plan-flow.html` (flow) · SRS ประกันรายได้-K2 v3.1 · เอกสาร Batch v4.0 · **SDD GI 24/02/2026** (`SDD-GI-Compensation/…md` — วงเงิน เกณฑ์เดียว 100,000 · เปิดเรื่องซ้ำ · งานค้าง)
> **กติกา sync:** ทุกครั้งที่คุย/แก้ไขเรื่อง API ให้อ่านไฟล์นี้ก่อน และถ้ามีการตัดสินใจใหม่ ให้อัปเดตทั้งไฟล์นี้และ `plan-api.html` ให้ตรงกัน · ถ้ากระทบตาราง/flow ต้องอัปเดต `database.md`/`workflow.md` คู่กันด้วย

## ภาพรวม

- **29 เส้น · 6 กลุ่มตามโดเมน** เป็น reference contract สำหรับ FE/BE alignment (กลุ่มข้อมูลผิดปกติ 2 เส้น **ยกเลิกและลบทิ้ง 2026-08-06** พร้อมหน้าจอ · กลุ่ม System Config และ Email Template รวม 10 เส้น **ยกเลิกและลบทิ้ง 2026-08-06** พร้อมหน้าจอ — ดูท้ายไฟล์)
- Base URL `/api/v1` · การยืนยันตัวตน: ผ่าน BFF ของระบบ SBP เดิม — SBPGI รับ user context จาก header (`x-api-key` + `x-user-id`/`x-user-group-id`/`x-user-permissions`) · callback ภายนอกใช้ API key/service token
- **ตัดสินใจ 2026-08-05:** กลุ่ม Auth & สิทธิ์ผู้ใช้ (เดิมกลุ่ม 1 · 4 เส้น) และ API ผู้ปฏิบัติงาน/roles/menus/สิทธิ์เมนู (เดิมอยู่กลุ่ม Master Data · 14 เส้น) **ตัดออก — ใช้ระบบ SBP เดิม** (Cognito + BFF + auth-backend/ABS) ดูหัวข้อ "เส้นที่ตัดออก" ท้ายไฟล์ · เดิมนับเป็น 62 เส้น 10 กลุ่ม
- **ตัดสินใจ 2026-08-06 (รอบ 2) — ยึด API/DB ของระบบ SBP เดิมเป็นหลัก:** ตรวจ `SBP/README.md` + `srm-sps-spsap-store-backend` แล้วตัดอีก **3 เส้น** ที่มีของพร้อมใช้อยู่แล้ว (`/stores/search` → `GET /store/search` · `/zones` → `GET /store/all-regions` · `/branch-types` → `GET /common/common-code`) → เหลือ 47 เส้น (ต่อมาลดเหลือ 31 เส้น เมื่อลบกลุ่ม System Config + Email Template และกลุ่ม Batch Job Admin · แล้วเหลือ 30 เส้น เมื่อยกเลิกระบบ `audit_logs` 2026-08-07 · แล้วเหลือ **29 เส้น** เมื่อย้าย `decisions` ไป `common_code` ตามมติ DP-9 (2026-08-10)) · และเปลี่ยนแหล่งข้อมูลของอีก 4 เส้นให้ไปอ่าน/เขียนของระบบเดิมแทนตารางของ SBPGI (ดูตาราง "เส้นที่เปลี่ยนไปใช้ของระบบ SBP เดิม" ท้ายไฟล์)
- แบ่งหน้า `?page=1&size=20` → ตอบ `{"page","size","total","items":[]}`
- Error รูปแบบเดียวกันทุกเส้น `{"code":"DOC_409","message":"ข้อความไทยตรงตาม SRS"}` — **ข้อความ popup ต้องตรงตัวตาม SRS**
- **วันที่และเลขเอกสารเป็น ค.ศ. ทั้งหมด** (payload = ISO-8601 ค.ศ. · `docNo` = `YYYY/xxxxx` ค.ศ.) — ยึดตามระบบ SBP ปัจจุบัน (FE `DatePicker` default `buddhistEra=false` · BE helper `toAD()`), แสดงผล พ.ศ. เฉพาะจุดที่เปิด flag ที่ component · JSON UTF-8 ทุกเส้น (เลิก TIS-620)
- Code namespace ต้องไม่ตีความปนกัน: `roleCode` = RBAC role 00/01/02/03/04/05/06/10, `sectionCode` = workflow section 06/08/01/02/03, `statusCode` = document status lookup; ทุก response ที่ต้องแสดงสถานะให้ส่ง code เป็น canonical value แล้ว FE resolve label จาก `/sbpgi/lookup/document-statuses`
- **Batch Job — ตัด API ทั้งกลุ่ม (2026-08-06):** กลุ่ม Batch Job Admin 6 เส้น (`/jobs*`) ถูกลบออกจากแบบ · หน้า `job-batch.html` **ย้ายไปกลุ่มเมนู `Flow` ชื่อ "Flow Batch Job" และเหลือเฉพาะ 2 แท็บ `Flowchart การทำงาน` + `Database ที่ใช้`** (ตัดแบบฟอร์มพารามิเตอร์ · ประวัติการรัน · ปุ่มสั่งรัน/เปิด-ปิด job · stat cards · กราฟ · การ์ด audit ออกทั้งหมด) — เป็นเอกสารอ้างอิงสำหรับผู้พัฒนา ไม่ใช่หน้าจอควบคุม · **batch job ของ SBPGI ยังทำงานตามปกติ** แต่พารามิเตอร์/ตารางเวลากำหนดใน **backend config** (config file/env ฝั่ง BE) และผลการรันเก็บที่ application log / `interface_transactions` แทน ไม่มีหน้าจอและไม่มี API แก้ค่า
- ป้ายที่มาต่อเส้น: **(FGI/FCS)** เอกสาร Batch v4.0 · **(K2)** SRS v3.1 · **(ใหม่)** เพิ่มในระบบใหม่ · **(ผสม)**

## สัญญากลาง API/FE ที่ทุก endpoint ต้องใช้

> รายละเอียด LLDD กลาง: `LLDD/md/BE/LLDD-BE-API-Common-Contracts.md` และ `LLDD/md/FE/LLDD-FE-Integration-Contracts.md`

| หมวด | Contract กลาง | ผู้รับผิดชอบ / ใช้โดย |
|---|---|---|
| Transport | Base URL `/api/v1` · JSON `application/json; charset=utf-8` · multipart เฉพาะ attachments | BE ทุก controller · FE shared API client |
| Auth | ผู้ใช้ login ผ่าน BFF ระบบเดิม (Cognito · token เก็บใน httpOnly cookie ฝั่ง BFF) — SBPGI ตรวจ `x-api-key` + อ่าน user context จาก header ที่ BFF แนบมา; internal workflow/batch callback ใช้ service token | ระบบเดิม (BFF + auth-backend) จัดหา identity/สิทธิ์; BE validate header; FE ไม่แตะ token |
| Error | ทุก error คืน `{code,message}` เท่านั้น · `message` เป็นไทย verbatim ตาม SRS ถ้ามีข้อความกำหนด | BE error handler · FE แสดง `message` ตรง ๆ |
| HTTP status | 400 validation · 401 auth · 403 forbidden/RBAC · 404 not found · 409 duplicate/current-task conflict · 422 business rule · 413 file too large · 415 unsupported file | BE middleware/service · FE error state |
| Pagination | GET list ทุกเส้นรับ `page,size` และคืน `{page,size,total,items}` | BE repository/query · FE DataTable/Pager |
| Format | `docNo` = `YYYY/xxxxx` **ค.ศ.** (เช่น `2026/00123`) · `storeCode/newStoreCode` เป็น string 5 หลักคง leading zero · date/month ใน payload เป็น ค.ศ. ISO · amount/percent เป็น number 2 decimals | BE validate/serialize · FE format display |
| Workflow transition | `/sbpgi/document/{docNo}/actions` รับ `{result,comment}` โดย `result` เป็น 6-enum ไทย verbatim (ค่า "ส่งฝ่ายส่งเสริมธุรกิจ SBP" เปลี่ยนชื่อเป็น "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" ตาม SDD GI 24/02/2026) และคืน `{nextSection,statusCode,message}`; positive path คือ `06→08→01→02→03→99` โดย `99` = เสร็จสิ้นและ `nextSection=null`; ที่ Section 02 ยอด < 100,000 จบเป็น 99 โดยไม่ผ่าน 03 · ≥ 100,000 → 03 (SDD GI) | BE Workflow Action เป็น source of truth; FE ไม่คำนวณ route เอง |
| RBAC/Menu | sidebar/route guard ใช้ของระบบเดิม: BFF `GET /menus` + `GET /groups/current-user/permissions` (`canView/canManage/canExport/canOther` ต่อ URL) · `GET /sbpgi/document/{docNo}` ยังคืน `permissions.canEditSections` และ `permissions.canAction` (ธงเชิง workflow ที่ SBPGI คำนวณเอง) | ระบบเดิมคุมเมนู/สิทธิ์เข้าหน้า · BE task-owner guard · FE เปิด/ปิด UI |
| Audit | **ไม่มี audit กลางของ master แล้ว** (ยกเลิก `audit_logs` 2026-08-07 · mutation master ไม่ต้องส่ง `reason`); workflow action ลง `consideration_logs`; batch เขียน application log | BE ไม่ต้องมี audit service · FE ไม่มีช่องเหตุผล |
| Idempotency | endpoint ที่สร้างจาก job/service ใช้ `requestId` หรือ business key; duplicate ต้องคืน existing result หรือ 409 ตามกฎ endpoint | BE service · Job rerun |

## โครงหน้าจอ plan-api (modal รายละเอียดต่อ endpoint)

catalog รวมทุกเส้น → คลิกแถว → เปิด modal ที่มีโครงดังนี้ (ดู `selectEp()` ใน `plan-api.html`):

1. **ชิป** ที่มา · สิทธิ์ · กลุ่ม
2. **Flow (ลำดับการทำงาน)** — แสดง **นอกแท็บ** (ไม่ใช่แท็บแล้ว) เหนือแท็บ · ถ้าเส้นนั้นมี flowchart จะมี pill "มี Flowchart ในแท็บ 3"
3. **แท็บ 1 · Request / Response** — request (query/body) + response + Error ที่ต้องรองรับ
4. **แท็บ 2 · Database + SQL** — ตารางที่เกี่ยวข้อง (R/W/RW) + **ตัวอย่าง SQL ต่อเส้น** (illustrative, bind params ขึ้นต้น `:`) เก็บใน `SQL_BY_PATH` keyed ด้วย `'METHOD path'`
5. **แท็บ 3 · Flowchart** — โผล่**เฉพาะ 3 เส้นที่ซับซ้อน** (มี branching/หลายขั้น) · เป็น inline SVG เรนเดอร์จาก node spec ใน `FLOWCHART_BY_PATH` ผ่าน mini-renderer `renderFlow()`

**3 เส้นที่มีแท็บ Flowchart:** `POST /sbpgi/document/{docNo}/actions` (routing 5 ขั้น + วงเงิน เกณฑ์เดียว 100,000) · `POST /sbpgi/workflow/instances` (Gen Flow Gate) · `POST /sbpgi/document` (สร้าง + กันซ้ำเฉพาะเอกสาร active)

## Base path + กลุ่ม path ของ SBPGI (มติ 2026-08-25)

**ทุก endpoint ของงานประกันรายได้อยู่ใต้ `sbpgi` แล้วแตกเป็น 6 กลุ่มย่อยตามกลุ่มงาน** — ตรงกับ 6 กลุ่มในหัวข้อถัดไปแบบ 1:1

| กลุ่ม | prefix ของ API | route ของหน้าจอ | เส้น |
|---|---|---|---|
| 1. งาน & เอกสารประกันรายได้ | `/api/v1/sbpgi/document/*` | `/sbpgi/document/*` | 11 |
| 2. ข้อมูลอ้างอิง (Lookup) | `/api/v1/sbpgi/lookup/*` | — (ไม่มีหน้าจอดูแล) | 2 |
| 3. Master Data | `/api/v1/sbpgi/master/*` | `/sbpgi/master/*` | 8 |
| 4. รายงาน | `/api/v1/sbpgi/report/*` | `/sbpgi/report/*` | 2 |
| 5. Workflow ภายใน | `/api/v1/sbpgi/workflow/*` | — (service token) | 3 |
| 6. Interface (tracking / ACK) | `/api/v1/sbpgi/interface/*` | — (ไม่มีหน้าจอ) | 3 |

**ชื่อเดียวกัน 3 ชั้น:** URL ของ API `/api/v1/sbpgi/<กลุ่ม>/...` · route ของหน้าจอ `/sbpgi/<กลุ่ม>/...` · โฟลเดอร์ไฟล์ `src/app/(main)/sbpgi/*` · `src/services/sbpgi/*` · `src/types/sbpgi/*`

**ทำไมต้องมี prefix:** มติ **DP-10** ให้ SBPGI อยู่ใน **`srm-sps-spsap-store-backend` ตัวเดิม** ไม่แยก backend ใหม่ — และ backend ตัวนั้น**มีเส้นชื่อใกล้กันอยู่ก่อนแล้ว**:

| ระบบเดิมมีอยู่แล้ว | ของ SBPGI ถ้าไม่ใส่ prefix | ผล |
|---|---|---|
| `/document` · `/statement/...` | `/documents` | ชนเชิงความหมาย · คนอ่าน routing สับสน |
| `/report` · `/performance-report` · `/statement/report/ej` | `/reports/status-summary` | ชนเชิงความหมาย |
| **`/interface/sta/upload-cmadd`** · `/interface/add` | **`/interfaces/sta/ack`** | 🔴 เกือบเหมือนกัน — เสี่ยงยิงผิดเส้นจริง |
| `/common` · `/master` · `/store` | `/factors` `/competitors` `/document-statuses` | ปนกับ master ของโมดูลอื่น |

**Batch job ไม่มีกลุ่ม path ของตัวเอง** — Jobs 2-10 + 8b รันด้วย cron/CLI ไม่เปิด endpoint (กลุ่ม Batch Job Admin 6 เส้นถูกตัดทิ้ง 2026-08-06) · ผลการรัน job มองผ่าน **`/sbpgi/interface/*`** (tracking + ACK ของ `interface_transactions`) กับ application log เท่านั้น

**กติกา**

- ฝั่ง NestJS ประกาศ **`SbpgiModule` เดียว** ผูก prefix ที่ระดับโมดูล (`RouterModule.register([{ path: 'sbpgi', module: SbpgiModule }])`) แล้วแตกเป็น **6 controller ตามกลุ่ม** (`DocumentController` · `LookupController` · `MasterController` · `ReportController` · `WorkflowController` · `InterfaceController`) — **ห้ามเติม `sbpgi/` ในแต่ละ `@Controller()`** จะได้ย้าย/เปลี่ยน prefix ที่เดียว
- ในกลุ่ม `document` ต้องประกาศ route คงที่ (`/tasks`) **ก่อน** route ที่มีพารามิเตอร์ (`/{docNo}`) · `docNo` เป็น `YYYY/xxxxx` (มี `/`) จึงต้อง `encodeURIComponent` ทุกครั้งที่ประกอบ URL
- เส้นที่ **ไม่ใช่ของ SBPGI ไม่ต้องใส่ prefix** และห้ามแตะ: `GET /store/search` · `GET /store/all-regions` · `GET /common/common-code` · `GET /menus` · `GET /groups/current-user/permissions` · `POST /statement/upload-file-aws` · `GET /api/workflow/pending` — เป็นของระบบ SBP เดิม เรียกตรงตามเดิม
- BFF ส่งต่อทั้ง prefix (`/api/v1/sbpgi/*`) โดยไม่ตัดคำ · สิทธิ์เมนูยังผูกกับ URL ของ **หน้าจอ** (`/sbpgi/<กลุ่ม>/...`) ไม่ใช่ URL ของ API
- `tools/check_docs.py` มีกฎกันหลุด 2 ข้อ: **ต้องอยู่ใต้ `/api/v1/sbpgi/`** และ **ต้องอยู่ในกลุ่มใดกลุ่มหนึ่งใน 6 กลุ่ม**

## รายการ endpoint ทั้ง 6 กลุ่ม

> **การนับ:** หัวข้อย่อยด้านล่างเลข 1–7 แต่ **หัวข้อ 1 (Auth) ถูกตัดออกทั้งกลุ่มและไม่มี endpoint** — กลุ่มที่นับจริงคือหัวข้อ 2–7 รวม **6 กลุ่ม / 29 เส้น** (11 + 3 + 8 + 2 + 3 + 3) ตรงกับ `GROUPS` ใน `plan-api.html` ที่เรนเดอร์เลขกลุ่ม 1–6 (คงเลขหัวข้อเดิมไว้เพื่อไม่ให้ลิงก์อ้างอิงเดิมเสีย)

### 1. Auth & สิทธิ์ผู้ใช้ — **ตัดออก · ใช้ระบบ SBP เดิม** (ตัดสินใจ 2026-08-05)

ไม่มี endpoint ใน SBPGI — FE ใช้ของระบบเดิมผ่าน BFF: login redirect `{bffUrl}/auth/login` (Cognito · cookie httpOnly) · `POST /auth/refresh` (axios interceptor เดิม) · `GET /auth/profile`, `GET /users/current` (ข้อมูลผู้ใช้) · `GET /menus` + `GET /groups/current-user/permissions` (sidebar/สิทธิ์ต่อ URL) — เส้นเดิมของกลุ่มนี้ (`/auth/login` `/auth/refresh` `/auth/me` `/me/menus`) ดูหัวข้อ "เส้นที่ตัดออก" ท้ายไฟล์

### 2. งาน & เอกสารประกันรายได้ · K2 3.1.2/3/4/6 (11 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/sbpgi/document/tasks` | งานรอท่านดำเนินการ (inbox ของ section — k2-list-waiting) |
| GET | `/sbpgi/document` | ค้นหาเอกสารที่เกี่ยวข้อง — **บังคับระบุปี** · filter: สถานะ · ภาค · ประเภทร้าน · ช่วงวันที่สร้าง · ช่วงยอดขายที่ลดลง/เงินชดเชย/วันที่รอ · **`result` (ประกันรายได้ / ไม่ประกันรายได้ / ยังไม่มีผล — เพิ่ม 2026-08-06)** อิง `consideration_logs.result_category` ล่าสุด (APPROVE/REJECT · เอกสารที่ยังไม่จบ = ไม่มีค่า) |
| GET | `/sbpgi/document/{docNo}` | เอกสารฉบับเต็ม 12 ส่วน + ธงสิทธิ์แก้ต่อ role/section |
| POST | `/sbpgi/document` | สร้างเอกสาร — ออกเลข YYYY/xxxxx + เปิด workflow (มี Flowchart) · **ตัดสินใจ 2026-08-06: ไม่มีฟอร์มสร้างเอกสารใน FE แล้ว** — ต้นทางสร้างที่ระบบ **FS** แล้วรอ **SBP Statement** ส่งข้อมูลกลับ (~1 วัน) จึงเรียกเส้นนี้โดย pipeline/service token · หน้า `k2-create.html` เหลือเป็นหน้าอธิบายกระบวนการ · การคีย์/ปรับข้อมูลร้านตาม SDD GI ทำในหน้าเอกสาร (`PUT /sbpgi/document/{docNo}`) |
| PUT | `/sbpgi/document/{docNo}` | บันทึกส่วนย่อย (ร้านใหม่/คู่แข่ง/ปัจจัย) · **%ชดเชยรวม = 100%** |
| POST | `/sbpgi/document/{docNo}/actions` | ส่งผลพิจารณา — หัวใจ workflow 5 ขั้น · วงเงิน เกณฑ์เดียว 100,000 · SDD GI (มี Flowchart) |
| GET | `/sbpgi/document/{docNo}/timeline` | ประวัติพิจารณาทุกขั้น |
| POST | `/sbpgi/document/{docNo}/attachments` | แนบไฟล์ ≤ 5MB |
| GET | `/sbpgi/document/{docNo}/attachments/{attachId}/download` | ดาวน์โหลดไฟล์แนบรายไฟล์ผ่าน BE authorization + AV clean guard · ไฟล์จริงใช้ service S3 ของระบบ SBP เดิม |
| GET | `/sbpgi/document/{docNo}/attachments/download-all` | **(เพิ่ม 2026-08-06)** ดาวน์โหลดไฟล์แนบทั้งหมดเป็น `.zip` — ปุ่ม “ดาวน์โหลดทั้งหมด” ระดับการ์ด (เทียบเท่าปุ่ม `Download` ของ K2 เดิม) · 404 เมื่อไม่มีไฟล์แนบ |
| GET | `/sbpgi/document/{docNo}/sales` | ยอดขาย 4 หน้าต่าง × 15 วัน — ใช้กับปุ่ม "ข้อมูลยอดขายเพิ่มเติม" · **กราฟแนวโน้มยอดขายรายวันในหน้าเอกสารถูกถอดออก 2026-08-06** เหลือเป็นข้อมูลประกอบการตรวจสอบและลิงก์ออก QlikView BI |

### 3. ข้อมูลอ้างอิง (Lookup / Reference) · K2 + FGI/FCS **(2 เส้น · lookup อ่านอย่างเดียวที่ไม่มีหน้าจอดูแล master · ตัด `/stores/search` `/zones` `/branch-types` 2026-08-06 — ใช้ของระบบ SBP เดิม)**

> **ใช้ของระบบ SBP ปัจจุบันแทน:** ค้นหาร้าน → `GET /store/search` (+ `/store/list` `/store/detail` `/store/opt-name`) · ภาค/โซน → `GET /store/all-regions` (+ `/store/regions-by-email` `/store/province-by-region`) · ประเภทสาขา → `GET /common/common-code` (+ `/master/common`) — ทั้งหมดอยู่ใน `srm-sps-spsap-store-backend` และเรียกผ่าน BFF ตัวเดียวกับที่ FE ใช้อยู่แล้ว

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/sbpgi/lookup/document-statuses` | รายการสถานะเอกสาร — dropdown ตัวกรอง (ค้นหา/รายงาน) |
| GET | `/sbpgi/lookup/workflow-sections` | รายการ Section 5 ขั้น (06/08/01/02/03) + `approveLimitAmount` ต่อขั้น — dropdown ตำแหน่ง/ตัวกรอง · FE ใช้แสดงวงเงิน ไม่ hardcode |

> **✅ มติ DP-9 (2026-08-10) — แยกตัดสิน:** `decisions` **ย้ายไปใช้ `common_code`** ของระบบเดิม (`code_type = SBPGI_DECISION`) จึง**ตัดเส้น `GET /decisions` ออก** — FE เรียก `GET /common/common-code?codeType=SBPGI_DECISION` ของระบบเดิมแทน · ส่วน `external_factors` และ `competitors` **ยังเป็นตารางของ SBPGI ตามเดิม** เพราะมีหน้าจอ CRUD ของตัวเอง และช่อง remark ของ `common_code` จำกัด 50 ตัวอักษร ไม่คุ้มที่จะไปแก้ตารางที่ทุกโมดูลใช้ร่วม · ⚠ `common_code` ไม่มี unique constraint → กันรหัสซ้ำที่ระดับแอป และลงทะเบียน `code_type` ที่ `common_code_type` ก่อน

### 4. Master Data · K2 3.1.9 (8 เส้น · master ที่มีหน้าจอดูแลของตัวเอง — ปัจจัยภายนอก + รายชื่อคู่แข่ง · CRUD คู่แข่งเพิ่ม 2026-08-06 · ตัด `/audit-logs` 2026-08-07)
| Method | Path | ทำอะไร |
|---|---|---|
| GET `/sbpgi/master/factors` · POST `/sbpgi/master/factors` · PUT `/sbpgi/master/factors/{code}` · DELETE `/sbpgi/master/factors/{code}` | **4 เส้น** | ปัจจัยภายนอก (external_factors) — รหัสห้ามซ้ำ · *ไม่มี `GET /sbpgi/master/factors/{code}` และไม่มี `PUT`/`DELETE` ที่ระดับ collection* |
| GET `/sbpgi/master/competitors` · POST `/sbpgi/master/competitors` · PUT `/sbpgi/master/competitors/{code}` · DELETE `/sbpgi/master/competitors/{code}` | **4 เส้น** | **master แบรนด์ร้านคู่แข่ง 11 รายการ** (รหัส 01–11 · ชื่อไทย+อังกฤษ) — `code` + `nameTh` + `nameEn` บังคับ · รหัสห้ามซ้ำ · หน้าจอ `k2-competitors.html` (**ใหม่ 2026-08-06** ตามหน้าจอ K2 เดิม) · `GET` เป็นแหล่งของ dropdown "ร้านคู่แข่ง (Master)" ในหน้าเอกสารด้วย · ต่างจาก `document_competitors` ที่เก็บ**รายสาขา**พร้อมรหัสจาก ALLMAP (ดู `docs/K2-interface-files.md`) |

> **กติกาการจัดกลุ่ม (ปรับให้ตรงกันทั้ง `api.md` และ `plan-api.html` · 2026-08-06):** master ที่**มีหน้าจอดูแลของตัวเอง** (ปัจจัยภายนอก → `k2-factors.html` · รายชื่อคู่แข่ง → `k2-competitors.html`) ให้เก็บ **CRUD ทั้งชุดไว้ในกลุ่ม Master Data** แม้ `GET` จะถูกใช้เป็น dropdown ในหน้าเอกสารด้วยก็ตาม — ส่วนกลุ่ม **Lookup** เหลือเฉพาะรายการอ้างอิงที่**อ่านอย่างเดียวและไม่มีหน้าจอดูแล** (`/sbpgi/lookup/document-statuses` · `/sbpgi/lookup/workflow-sections` · `/decisions`) เดิมทั้งสองไฟล์จัด `/sbpgi/master/competitors` คนละกลุ่มกัน ทำให้ตัวเลขต่อกลุ่มไม่ตรง

> **✅ มติ DP-9 (2026-08-10):** ทั้ง 8 เส้นของกลุ่มนี้ผูกกับ `external_factors` และ `competitors` ซึ่ง**ยังเป็นตารางของ SBPGI ตามเดิม** ไม่ย้ายไป `common_code` — เฉพาะ `decisions` เท่านั้นที่ย้าย

> เส้นผู้ปฏิบัติงาน (`/operators*` · `/employees/search`) และสิทธิ์เมนู (`/roles*` · `/menus*` · `/menu-permissions*`) รวม 14 เส้น **ตัดออก — ใช้ระบบ SBP เดิม** (ดูท้ายไฟล์)

### 5. รายงาน · K2 3.1.7 + SDD v7.5 (2 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/sbpgi/report/status-summary` | **รายงานตรวจสอบประกันรายได้ (SBP Mall)** — ค้นหาข้อมูล · **บังคับระบุปี** · filter ตาม **SDD สไลด์ 60** 7 ตัว: `status`* (Drop-down 6 ค่า · บังคับ) · `impactedStoreCode` (numeric) · `newStoreCode` (numeric) · `periodStatementFrom`/`periodStatementTo` (ปฏิทิน **วัน/เดือน/ปี ค.ศ.** หรือกรอกเอง · **บังคับเมื่อ status = เสร็จสิ้นดำเนินการ**) · `storeType[]` (checkbox **7 ค่า `A B C D E PTT บริษัท` (BranchTypeProfile.BranchTypeFGIName · ห้าม hardcode)**) · `region[]` (checkbox 13 รหัส · ภาคใหม่แสดงอัตโนมัติ) · `result` (Radio ประกันรายได้/ไม่ประกันรายได้ · **ไม่บังคับ**) · กติกาคู่: ระบุ `impactedStoreCode` แล้วต้องระบุ `newStoreCode` ด้วย มิฉะนั้น 400 · ผลลัพธ์ **14 คอลัมน์ตาม SDD** |
| GET | `/sbpgi/report/status-summary/export` | **Export Excel** — ส่งออกผลการค้นหา 14 คอลัมน์เป็น Excel ให้ทีมบัญชีนำไปกระทบ SAP · เงื่อนไข filter เดียวกับ `/sbpgi/report/status-summary` |

### 6. Workflow ภายใน · K2 3.1.4 + FGI/FCS Job 8b (3 เส้น)
| Method | Path | ทำอะไร |
|---|---|---|
| POST | `/sbpgi/workflow/instances` | เปิด workflow (แทน K2 StartInstance) — Gen Flow Gate (service token · มี Flowchart) |
| GET | `/sbpgi/workflow/instances/{id}` · `/sbpgi/workflow/summary` | สถานะ instance · ตัวเลขเฝ้าระวัง W/Y/N + งานค้างต่อ section |

### 7. Interface (tracking / ACK) · FGI/FCS (3 เส้น · ตัด `/dashboard/summary` 2026-08-06 — ชื่อกลุ่มจึงไม่มีคำว่า Dashboard แล้ว)
| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/sbpgi/interface/tracking` · `/sbpgi/interface/pending-ack` | สถานะรับ–ส่งของ interface (`interface_transactions`) · ACK ค้าง ≥ 1 วัน (Job 10) — **นับเฉพาะ `direction = 'OUT'`** เพราะแถว `INTERNAL` ของ Jobs 7/8/9 จบที่ `COMPLETED` ทันที ไม่มี ACK ให้รอ (ตรงเจตนาเดิมของ Java ที่กรอง `interface_type != 'WS'`) |
| POST | `/sbpgi/interface/sta/ack` | callback ให้ STA ยิง ACK ตรง (API key) |
| ~~GET~~ | ~~`/dashboard/summary`~~ | **ตัดออกถาวร 2026-08-06** — ถอด stat cards ออกจากหน้ารอดำเนินการ/ที่เกี่ยวข้องแล้ว จึงไม่มีผู้เรียก (เดิมคืนตัวเลข: งานรอดำเนินการของ section · ยอดขายไม่ครบ 60 วัน · รอเกิน 3 วัน · วงเงินเข้าเส้น AVP) |

## กฎธุรกิจสำคัญที่ผูกกับ API

- **บังคับระบุปี (ค.ศ.)** ใน `/sbpgi/document` และ `/sbpgi/report/status-summary` ไม่งั้นตอบ 400 (กติกา SRS · BE ต้องผ่าน `toAD()` ก่อน query เผื่อ client ส่ง พ.ศ. มา)
- **เส้นทางข้ามขั้นที่ section 06** ใน `/sbpgi/document/{docNo}/actions`: `result = "ส่งหน่วยงานส่งเสริมธุรกิจ SBP"` → `nextSection = "01"` (**ข้ามขั้น 08**) ใช้เมื่อ**ทราบยอดเงินชดเชยจากเจ้าหน้าที่ SBP DSA แล้ว** (ข้อความอ้างอิง SDD สไลด์ 21: “ส่งต่อ Flow หลังทราบยอดเงินชดเชยรายได้จากเจ้าหน้าที่ SBP DSA ดำเนินการ”) · `result = "ส่งเจ้าหน้าที่ SBP DSA"` → `nextSection = "08"` (เส้นทางปกติ — ยังไม่ทราบยอด ต้องมอบหมายให้คำนวณก่อน) · การส่งกลับจาก 01 กลับไปที่ 06 เสมอ ไม่ใช่ 08 (ดูตารางเทียบใน `workflow.md`)
- **กฎวงเงินอนุมัติ (SDD GI 24/02/2026)** ใน `/sbpgi/document/{docNo}/actions`: เห็นควรชดเชย < 100,000 → **จบที่ GM (02)** · ≥ 100,000 → AVP (03) แล้วจบ  · เห็นควรไม่ชดเชยที่ 01/02 → **เสร็จสิ้นทันที (ไม่อนุมัติในเดือนนั้น)** · 06 ไม่ชดเชย/หยุด → เสร็จสิ้น · **ตัดขั้นบัญชี 04/05 ตาม SDD v7.5** (ดูตารางเต็มใน `workflow.md`) · เดิมใช้เกณฑ์เดียว 100,000
- **auto-assign เจ้าของงานคนเดิม (SDD สไลด์ 46 · 48 · ระบุละเอียด 2026-08-20)** — ผูกกับ `POST /sbpgi/document/{docNo}/actions` และ `GET /sbpgi/document/tasks`:
  - **06 เห็นควรไม่ชดเชย** → ปิดเอกสาร (`เสร็จสิ้นดำเนินการ`) และ **`GET /sbpgi/document/tasks` ของ 06 ต้องไม่คืนเอกสารนี้ในเดือนที่ถูกปฏิเสธ** · ระบบตั้งงาน**รอบเดือนถัดไป**ให้ร้านเดิม โดยมอบหมาย**ผู้ดำเนินการคนเดิม**
  - **เคสต่อเนื่อง** (ชดเชยติดกันหลายเดือน) → ระบบส่งงานให้ **เจ้าหน้าที่ SBP DSA คนเดิม** อัตโนมัติ ไม่ต้องแจกงานด้วยมือ
  - **วิธี resolve** — หาเอกสารรอบก่อนของ `impacted_store_code` เดียวกัน แล้วอ่าน `consideration_logs` แถวล่าสุดที่ `section_code` ตรงกับขั้นที่จะมอบหมาย → **`consider_by`** → ส่งเข้า **`addPreApprover(versionId, referenceId, stateId, approver, seq)`** ของ `@srm/glb-workflow` · **ไม่มีคอลัมน์ assignee ในตารางของ SBPGI** (`workflow_tasks` ถูกตัดไปแล้ว)
  - **Fallback** — รอบก่อนไม่เคยผ่านขั้นนั้น / พนักงานลาออก → มอบหมายตาม group ของ auth-backend ตามปกติ (พนักงานลาออกยังต้องเปิด SR แก้ชื่อผู้ดำเนินการ · SDD สไลด์ 48)
  - ⚠️ **ต่างจาก "หยุดชดเชยประกันรายได้"** ซึ่ง `GET /sbpgi/document/tasks` ของ 06 **ต้องคืนทันทีในเดือนนั้น** (ดูข้อถัดไป) — สองปุ่มนี้จบเอกสารเหมือนกันแต่พฤติกรรมหน้ารายการตรงข้ามกัน
- **เปิดเรื่องซ้ำได้ (SDD GI)** ใน `POST /sbpgi/document`: 409 เฉพาะกรณีมีเอกสาร **active** ของร้าน+เดือนนั้น — เอกสารเดิมที่จบด้วยหยุดชดเชย/เห็นควรไม่ชดเชย เปิดเรื่องใหม่ได้ทั้งเดือนเดียวกันและเดือนถัดไป (ยกเลิกการเปิด SR) · กรณีเห็นควรไม่ชดเชย (06) เดือนถัดไประบบสร้างงานเข้า `GET /sbpgi/document/tasks` อัตโนมัติพร้อม assignee คนเดิม · ยอดชดเชย 0: เดือน 1–3 ส่งต่อ 01 · เดือนที่ 4 หยุดชดเชย
- **งานค้าง (SDD GI)** ใน `GET /sbpgi/document/tasks`: รองรับ filter + เลือกหลายเอกสาร (bulk action) · เจ้าหน้าที่/ฝ่าย SBP DSA เห็นเอกสารได้ทุกสาขา (ไม่จำกัดงานตน) · ทีมส่งเสริม/บัญชีตามสิทธิ์เดิม
- **เอกสารที่หยุดชดเชยฯ กลับเข้าคิวของ 06 (SDD สไลด์ 46 ข้อ 1.9 · เพิ่ม 2026-08-20)** — `GET /sbpgi/document/tasks` เมื่อผู้เรียกอยู่ใน **section 06 (ฝ่าย SBP DSA)** ต้องคืน **2 ชุดรวมกัน**: (1) เอกสารสถานะ `รอฝ่าย SBP DSA ดำเนินการ` ตามปกติ + (2) เอกสารสถานะ `เสร็จสิ้นดำเนินการ` ที่**ผลการพิจารณาสุดท้ายเป็น "หยุดชดเชยประกันรายได้"** เพื่อให้ 06 พิจารณาคำขอชดเชยรายได้อีกครั้งได้เองโดยไม่ต้องเปิด SR · **บทบาทอื่น (08/01/02/03) ไม่เห็นชุดที่ (2)**
  - ชุดที่ (2) มาจากการ query `consideration_logs` แถวล่าสุดของเอกสารที่จบแล้ว (`result_code = หยุดชดเชยประกันรายได้`) — **ไม่ใช่สถานะที่ 7** สถานะเอกสารยังคงเป็น `เสร็จสิ้นดำเนินการ` ตามชุดสถานะ 6 ค่า
  - response ต้องมี flag `stoppedReopenable: true` ให้ FE ขึ้นชิป `↺ หยุดชดเชยฯ` และเปิดเอกสารด้วยโหมด "เปิดพิจารณาใหม่"
  - `GET /sbpgi/document/{docNo}` ของเอกสารกลุ่มนี้คืนข้อมูลเดิมครบทุกส่วน + `actionOptions` **ชุดเดียวกับ section 06** (เห็นควรไม่ชดเชย · หยุดชดเชยประกันรายได้ · ส่งหน่วยงานส่งเสริมธุรกิจ SBP · ส่งเจ้าหน้าที่ SBP DSA) · การกด `POST /sbpgi/document/{docNo}/actions` จะเปิดรอบพิจารณาใหม่ให้ร้าน+เดือนนั้น
  - ⚠️ ต้องกันไม่ให้เอกสารกลุ่มนี้ถูกนับซ้ำในตัวเลข "งานค้าง" ของ engine (`getPendingFlowByUser()` ไม่คืนเอกสารที่ instance ปิดแล้ว — ชุดที่ (2) เป็นการ union ฝั่ง SBPGI เอง)
- **filter `result`** ใน report = **4 ค่า** (Radio เลือกอย่างใดอย่างหนึ่ง · **ไม่บังคับ** — บังคับเฉพาะ `status`) อิง **ผลพิจารณาล่าสุด** `consideration_logs.result_category`: `APPROVE` = ประกันรายได้ · `REJECT` = ไม่ประกันรายได้ · **`CANCELLED` = ยกเลิกโดยระบบ (เพิ่ม 2026-08-10)** · `PENDING`/ไม่มีค่า = ยังไม่มีผล — SDD สไลด์ 60 แสดงเพียง 2 ค่าแรก แต่ master จริง (`DecisionProfile.DecisionResultName` ของ `CPA_FRN_FGI`) มี **ยกเลิกโดยระบบ** จาก decision 14 `CancelBySystem` ด้วย จึงแยกเป็นตัวเลือกที่ 4 (ตัดสินใจ 2026-08-10) — ขั้นบัญชี 05 ที่เคยอ้างถูกตัดออกแล้ว
- **%ชดเชยรวม = 100%** ใน `PUT /sbpgi/document/{docNo}` · **เงินชดเชยต่อร้านเปิดใหม่ = ยอดชดเชยของร้านถูกกระทบ × %ชดเชย** คำนวณและปัดเศษที่ **BE** แล้วส่งกลับเป็น `compensateAmount` (FE ห้ามคูณเอง — กันยอดปัดเศษไม่ตรงกับที่บัญชีใช้) · ผลรวม `compensateAmount` ทุกร้านต้องเท่ากับยอดชดเชยของร้านถูกกระทบพอดี — แสดงในคอลัมน์ "เงินชดเชย (ร้านใหม่)" ของตารางร้านเปิดใหม่ (**กราฟสัดส่วนเงินชดเชยถูกถอดออก 2026-08-06**)
- **เพิ่มร้านที่กระทบเพิ่มระหว่างทาง (B5)** — `newStores` ของ `PUT /sbpgi/document/{docNo}` รับได้ทั้งแถวที่ระบบดึงมาเอง (`sourceSystem = "ALLMAP"`) และแถวที่ผู้ใช้คีย์เอง (`sourceSystem = "USER"`) · **BE ต้อง validate `%ชดเชยรวม = 100%` ใหม่ทุกครั้งที่จำนวนแถวเปลี่ยน** แล้วคำนวณ `compensateAmount` ของทุกแถวใหม่ ไม่ใช่เฉพาะแถวที่เพิ่ม · กันซ้ำด้วย `UNIQUE (doc_no, new_store_code)` → ซ้ำให้คืน `409`
- API payload ใช้ `newStoreCode` สำหรับรหัสร้านเปิดใหม่ 5 หลัก (เช่น `"00990"`) เพื่อคง leading zero **ทั้งใน response ของ `GET /sbpgi/document/{docNo}` และ request ของ `PUT /sbpgi/document/{docNo}`** (ห้ามใช้ `storeCode` ในสองเส้นนี้ — สงวนไว้ให้ร้านถูกกระทบ); internal table `document_new_stores.id` เป็น key ภายใน ไม่ expose เป็น field code
- **require field ของแถวที่ผู้ใช้เพิ่มเองในส่วนร้านคู่แข่ง/ปัจจัยอื่นๆ ของ `PUT /sbpgi/document/{docNo}`** (ตัดสินใจ 2026-08-06): คู่แข่ง = **รหัสแบรนด์คู่แข่ง** (เลือกจาก master `GET /sbpgi/master/competitors` รหัส `01`–`11` เท่านั้น ไม่ใช่ free text — แถว `source_system = ALLMAP` ที่ pipeline นำเข้ามีรหัสรายสาขาของตัวเองอยู่แล้ว) + **วันที่เปิดกระทบ** · ปัจจัย = **รหัสปัจจัยภายนอก** (เลือกจาก master `GET /sbpgi/master/factors`) + **วันที่เริ่มต้น** (วันที่สิ้นสุดไม่บังคับ แต่ถ้ามีต้อง ≥ วันที่เริ่มต้น — SRS ข้อ 11) · ไม่ผ่าน → 400 พร้อมข้อความ **verbatim จาก SRS §10**: “กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ” · ส่วนฝั่งปัจจัย “กรุณาเลือกปัจจัยอื่นๆ ที่ท่านต้องการ” **ไม่ได้อยู่ใน SRS** — เราตั้งขึ้นให้ล้อกับข้อความคู่แข่ง (SRS §11 ระบุแต่กฎวันที่ ไม่ได้ให้ข้อความ) **ต้องให้ BA ยืนยันก่อน UAT** · UI: `k2-document.html` แสดง `*` แดงบน require field และไม่มีปุ่ม “บันทึก” ระดับการ์ดแล้ว (บันทึกผ่าน modal เพิ่ม/แก้ไขเท่านั้น)
- **การบันทึกส่วนร้านคู่แข่ง/ปัจจัยอื่นๆ เป็นแบบ “บันทึกทันทีรายรายการ”** (ตัดสินใจ 2026-08-06 — ไม่มีปุ่มบันทึกระดับการ์ดแล้ว): กด **เพิ่ม/แก้ไข** ใน modal แล้วกดบันทึกใน modal = ยิง `PUT /sbpgi/document/{docNo}` ทันที 1 ครั้ง · **ลบรายการที่เลือก (bulk remove)** ก็ยิง `PUT` ทันทีหลังผู้ใช้กดยืนยันใน popup (ไม่ค้างเป็น draft) — ไม่มี endpoint ลบแยก · ทุกครั้งส่ง**อาร์เรย์ชุดเต็มของส่วนนั้น** ให้ BE ลบรายการที่หายไป (`DELETE … NOT IN`) ในทรานแซกชันเดียวกัน · ปุ่มเพิ่ม/ลบ/checkbox แสดงเฉพาะ role ที่แก้ส่วนนั้นได้ (ปัจจุบันคือ section 01)
- **⚠️ ข้อค้าง (2026-08-11): วิว ALLMAP** — `workflow.md` จัด ALLMAP อยู่กลุ่ม interface ที่ใช้ **พ.ศ.** และ argument ของ Job 2/3 ก็เป็น `2569|06` แต่หัวข้อนี้ระบุข้อยกเว้นไว้แค่ STA/IAS · **ยังไม่ยืนยันว่าวิว ALLMAP เก็บปีเป็น พ.ศ. จริงหรือไม่** — ต้องถามเจ้าของ ALLMAP แล้วปรับให้ตรงกันทั้งสองไฟล์
- **ข้อยกเว้นเดียวของกติกา ค.ศ.:** ไฟล์ที่รับจาก IAS (`AMS06001I_…`) ยังใช้ **พ.ศ. + windows-874** และ **message ที่ส่งไป STA** (RabbitMQ `sta.compensation.result` · JSON UTF-8 · 14 ฟิลด์ตามสัญญา `FRBC0001` เดิม) ยังคง **ฟิลด์วันที่เป็น พ.ศ.** ตามสัญญาเดิมของระบบปลายทาง — แปลงเฉพาะตอนอ่านไฟล์/ประกอบ payload เท่านั้น ห้ามให้ปนเข้ามาใน DB/API · *ตัว windows-874 หายไปพร้อมกับไฟล์ `FRBC0001` เมื่อย้าย STA ไป RabbitMQ (มติ 2026-08-24) — เหลือรอยืนยันว่าจะเปลี่ยนฟิลด์วันที่เป็น ISO ค.ศ. ได้หรือไม่*
- **เลขเอกสาร YYYY/xxxxx** (ปี **ค.ศ.** · running ต่อปี เริ่ม 00001) · **เลขเอกสารและวันที่ทั้งระบบเป็น ค.ศ.** (ตัดสินใจ 2026-08-06 — ยึดตามระบบ SBP ปัจจุบัน: DatePicker ของ FE ตั้งค่า `buddhistEra = false` เป็นค่าเริ่มต้น และ BE มี helper `toAD(y) = y >= 2500 ? y - 543 : y` บังคับแปลงค่าที่หลุดมาเป็น พ.ศ. ให้เป็น ค.ศ. · แสดงผลเป็น พ.ศ. ได้เฉพาะจุดที่เปิด `buddhistEra` ที่ระดับ component เท่านั้น · ภาพหน้าจอ K2 จริงก็ใช้ ค.ศ. เช่นกัน เช่น `2026/01870`)
- **Gen Flow Gate** ใน `/sbpgi/workflow/instances` (เกณฑ์คงเดิมทุกข้อ — ดูขั้น 6 ใน `workflow.md`)
- `POST /sbpgi/workflow/instances` เป็น BE internal Workflow Engine contract สำหรับ Job 8b เท่านั้น ไม่ใช่งาน FE/Flow page: request `{impactProcessId, sourceJobNo:"8b", requestId}`; ผ่าน gate → สร้าง/คืน `{docNo, instanceId, workflowGenerationStatus:"Y", firstSection:"06", statusCode:"06"}`; fail ถาวร (branch type นอกเซ็ต, ระยะทางเกิน, DV หาย, นิติบุคคลเดียวกัน หรือ growth > −10) → ตั้ง `N`; เฉพาะ distance/juristic/growth เป็น NULL หรือ sales_status ยังไม่พร้อม → คง `W` และคืน 422/reason เพื่อ rerun
- **ยกเลิกระบบ audit ของ master ทั้งหมด (2026-08-07)** — ไม่มีตาราง `audit_logs` · ไม่มีเส้น `GET /audit-logs` · ไม่ต้องส่ง `reason` ตอนแก้ factors/competitors อีกต่อไป · การแก้สิทธิ์/กลุ่มผู้ใช้ และ config/email template ยังลง audit ของ**ระบบ SBP เดิม**ตามกลไกของระบบนั้น
- เส้นที่แก้**เอกสาร** ยังบันทึกผู้ทำและผลพิจารณาลง `consideration_logs` ตามเดิม (นี่ไม่ใช่ audit ของ master)

## การกระทบยอด SAP และแก้ข้อมูลผิดปกติ (SDD v7.5)


### C4 · checklist ที่ทีมบัญชีต้องตรวจ (SDD GI สไลด์ 40)

RPA ดึงข้อมูลร้านจาก SBP Mall ให้ทีมบัญชีตรวจ — **ตรวจ 5 ข้อ** ก่อนกระทบยอดกับ SAP และ Post คู่บัญชี

| # | สิ่งที่ต้องตรวจ | ข้อมูลที่ใช้ |
|---|---|---|
| 1 | **ยอดเงินคำนวณ 3 จุดตรงกัน** | รายงานประกันรายได้ · ไฟล์ที่ส่ง STA · SAP |
| 2 | **Performance Index** — คะแนนมาตรฐานมาจาก **QSSI** | `fcs_qssi_score` (ระบบ SBP เดิมนำเข้าให้) |
| 3 | **สาขาที่ถูกกระทบ และสาขาที่เปิดใกล้เคียง** | `document_new_stores` · `fgi_impact_stores` |
| 4 | **กรณีร้าน Take** — ตรวจเพิ่มสำหรับ "สาขาที่ถูกกระทบ" ที่เป็นร้าน Take | `impacted_stores` |
| 5 | **Center ตรวจจากรายงานประกันรายได้ของระบบ** แล้วกระทบยอดกับ SAP · Post คู่บัญชีถูกต้อง | `GET /sbpgi/report/status-summary` |

**กรณียอดไม่ตรง มี 2 สาเหตุ (SDD ระบุไว้):**
1. ระบบคำนวณจำนวนที่ชดเชย **ไม่ตรงกับ File PDF**
2. **ต้นทางแจ้งข้อมูลไม่ถูกต้อง/ไม่ครบถ้วน**

> ทั้งหมดนี้ทำ**นอก workflow** ผ่านหน้ารายงานตรวจสอบประกันรายได้ (ค้นหา + Export) — ไม่มีสถานะเอกสารรองรับตาม SDD v7.5

### C5 · ปริมาณงานจริงที่ใช้เป็นฐาน sizing / NFR (SDD GI สไลด์ 41)

| ตัวชี้วัด | ค่า | ที่มา |
|---|---|---|
| จำนวนเอกสารอนุมัติ | **150–170 ฉบับ/เดือน** | SDD สไลด์ 41 |
| เวลาอนุมัติต่อฉบับ | **~4 นาที** | SDD สไลด์ 41 |
| ภาระงานอนุมัติรวม | 4 นาที × 150 ฉบับ = **600 นาที ≈ 10 ชม./เดือน** | คำนวณใน SDD |
| ผจก.แผนกตรวจใน Flow K2 | **~5 นาที/ฉบับ** | SDD สไลด์ 41 |

**ใช้ทำอะไร** — เป็นฐานกำหนด NFR ของ `GET /sbpgi/document/tasks` · `GET /sbpgi/document` · `GET /sbpgi/report/status-summary`:
- ปริมาณข้อมูลระดับ **~170 เอกสาร/เดือน ≈ 2,000 เอกสาร/ปี** ไม่ใช่ระบบ high-volume → ไม่ต้องออกแบบ sharding/cache ซับซ้อน
- แต่ **`sps_store.workflow_transaction` มี 19,283 แถวและไม่มี index เลย** (DP-2) — ที่ปริมาณนี้ seq-scan ยังพอรับได้ แต่โตขึ้นทุกเดือน **ควรปิด DP-2 ก่อนขึ้น production**
- ปุ่ม **Export CSV to Batch** และ bulk action รองรับการเลือกทีละหลายฉบับได้จริง เพราะจำนวนต่อรอบไม่เกินหลักร้อย

ยกเลิกหน้าจอ Approve ของบัญชีและ**ยกเลิกสถานะบัญชีในเอกสาร 2 ค่า** — To-Be ทีมบัญชี **ตรวจสอบยอด + จัดเก็บสร้างรายการบันทึกบัญชี ผ่านหน้ารายงาน**: `GET /sbpgi/report/status-summary` (ค้นหาข้อมูล · **สถานะเป็น dropdown บังคับ 6 ค่า ไม่มีสถานะบัญชี**) + `/export` (Export Excel) แล้วกระทบยอดกับ SAP เอง งานฝั่ง SAP อยู่นอก API ชุดนี้:
- **SAP** `FBL3H` (GL Account Line-Item Browser — กระทบยอด) · `SAPPOST` (Update Transaction to SAP) · `FS/FSWEB` (ตรวจ STATUS=Completed)
- **กรณี SBP ผิดแต่ SAP ถูก** → เปิด **SR (Service Request)** ให้ทีมดูแล SBP แก้รายครั้ง (ผ่านระบบ ticketing เดิม — ไม่เพิ่ม endpoint)
- **ข้อเสนอ:** SBP **Auto Update** จาก SAP โดยไม่ต้องเปิด SR ทุกครั้ง — **BSR = Out of Scope** ของโครงการ Replacement SBP

## กลุ่มข้อมูลผิดปกติ / แจกงาน — ยกเลิกและลบทิ้ง (ตัดสินใจ 2026-08-06 · 2 เส้น)

**ลบทิ้งแล้ว** — ทั้ง 2 endpoint ถูกเอาออกจาก `plan-api.html` (GROUPS) และไฟล์หน้าจอ `k2-list-abnormal.html` ถูกลบออกจากโปรเจกต์:
- `GET /abnormal-stores` — ร้านข้อมูลผิดปกติ (ยอดขาย < 60 วัน) จาก pipeline batch
- `POST /abnormal-stores/assign` — แจกงานให้เจ้าหน้าที่ตรวจสอบ (role 05)

**ทดแทนด้วย:** ข้อมูลผิดปกติเป็น *ธงของแถว* ไม่ใช่หน้าจอแยก — `GET /sbpgi/document/tasks` และ `GET /sbpgi/document` คืน `salesDataDays` ให้ FE ทำ **แถวแดง** · **ตัดสินใจปิดประเด็นแล้ว 2026-08-06:** ไม่ทำตัวกรอง "ยอดขายไม่ครบ 60 วัน" ทดแทน — ข้อมูลผิดปกติเหลือเป็น **แถวแดง** อย่างเดียว ผู้ใช้สังเกตจากสีแถวในตาราง · ไม่มีตัวเลขสรุป (ตัด `GET /dashboard/summary` แล้ว) · การจ่ายงานใช้ auto-assign ของ SDD GI (เจ้าของงานคนเดิม) แทนการแจกงานด้วยมือ

## กลุ่ม System Config (Global) และ Email Template — ยกเลิกและลบทิ้ง (ตัดสินใจ 2026-08-06 · 10 เส้น)

**ลบทิ้งแล้ว** — ทั้ง 10 endpoint ถูกเอาออกจาก `plan-api.html` (GROUPS) และหน้าจอทั้งสองถูกลบออกจากโปรเจกต์ (`system-config.html`, `email-template.html`) พร้อม entry ใน `MODULES` และ `SCHEMAS.config` ของ `assets/sbp.js`:

| กลุ่มเดิม | เส้นที่ลบ |
|---|---|
| System Config (Global) · 5 | `GET /configs` · `GET /configs/{key}` · `POST /configs` · `PUT /configs/{key}` · `DELETE /configs/{key}` |
| Email Template (Notification) · 5 | `GET /email-templates` · `GET /email-templates/{code}` · `PUT /email-templates/{code}` · `POST /email-templates/{code}/reset` · `POST /email-templates/reset-all` |

**เหตุผล:** ทั้งสองกลุ่มออกแบบไว้เพื่อรองรับหน้าจอ admin 2 หน้านี้โดยตรง และ**เขียนลงตารางของระบบ SBP เดิมอยู่แล้ว** (`mas_param` / `email_template`) ซึ่งระบบเดิมมีหน้าจอบริหารจัดการของตัวเองอยู่ — SBPGI จึงไม่ต้องทำหน้าจอและ endpoint ซ้ำ

**สิ่งที่ยังอยู่ (ฝั่ง BE ภายใน ไม่ใช่ REST ของ SBPGI):**
- **ส่งอีเมลตามสถานะ** ยังทำงานเหมือนเดิม — SBPGI เรียก `sendEmail()` ของ email-lib กลาง (lib อ่าน `email_template` แล้ว log `email_sent` ให้เอง) · จุดส่งต่อสถานะดู `workflow_status_document.md` · **สัญญาเต็มดูหัวข้อ "อีเมล" ท้ายไฟล์**
- **ค่ากำหนดกลาง** ยังอ่านจาก **`sps_store.mas_param`** ของระบบเดิม (ตาราง config กลางของ store-backend · 93,752 แถว · ⚠️ ไม่มี PK/unique จึงต้อง `WHERE active_flag='Y'` + `LIMIT 1` · **มีเฉพาะ schema `sps_store`**) · 🔴 **ค่าของ SBPGI ยังไม่มีอยู่จริง ต้อง seed เองตอน setup** (ดู `LLDD-BE-Integration-SBP-Platform` 5.5) (รวมค่าที่หน้าจออื่นใช้ เช่น URL QlikView BI) · **วงเงินอนุมัติ GM/AVP** อ่านจาก `common_code` (`code_type = SBPGI_APPROVE_LIMIT`) ผ่าน `GET /sbpgi/lookup/workflow-sections` เหมือนเดิม
- การแก้ template/config เป็นงานของ**ระบบ SBP เดิม** — audit อยู่ที่ระบบเดิมทั้งหมด

## กลุ่ม Batch Job Admin — ลบออกจากแบบ (ตัดสินใจ 2026-08-06 · 6 เส้น)

**ลบทิ้งแล้ว** — ทั้ง 6 endpoint ถูกเอาออกจาก `plan-api.html` (GROUPS) · หน้า `job-batch.html` **ย้ายไปกลุ่มเมนู `Flow` ชื่อ "Flow Batch Job" และเหลือเฉพาะ 2 แท็บ `Flowchart การทำงาน` + `Database ที่ใช้`** (ตัดแบบฟอร์มพารามิเตอร์ · ประวัติการรัน · ปุ่มสั่งรัน/เปิด-ปิด job · stat cards · กราฟ · การ์ด audit ออกทั้งหมด) — เป็นเอกสารอ้างอิงสำหรับผู้พัฒนา ไม่ใช่หน้าจอควบคุม:

| เส้นที่ลบ |
|---|
| `GET /jobs` · `GET /jobs/{jobNo}` · `PUT /jobs/{jobNo}/params` · `PUT /jobs/{jobNo}/enabled` · `POST /jobs/{jobNo}/run` · `GET /jobs/{jobNo}/runs` |

**เหตุผล:** ทั้ง 6 เส้นมีไว้รองรับ 2 tab ที่ถูกตัดออกจากหน้าจอโดยตรง (`แบบฟอร์มพารามิเตอร์`, `ประวัติการรัน`) — ส่วนที่เหลือของหน้า (Flowchart + Database ที่ใช้) เป็นเนื้อหา static ไม่ต้องเรียก API

**สิ่งที่ยังอยู่:**
- **batch job ทั้ง 10 entry point (Jobs 2–10 + 8b · ตัด Job 1 ImportQSSI 2026-08-24) ยังทำงานตามปกติ** ตามเอกสาร Batch v4.0 — ไม่กระทบ pipeline FGI/FCS
- **พารามิเตอร์และตารางเวลา** ย้ายไปกำหนดใน **backend config** (config file/env ของฝั่ง BE) แทนตาราง `job_configs` — แก้ค่าโดยการ deploy config ไม่ใช่ผ่านหน้าจอ
- **ผลการรัน** เก็บที่ application log ของ BE และ `interface_transactions` (สถานะรับ–ส่งไฟล์/ACK ซึ่งยังมี endpoint กลุ่ม Interface อยู่) แทนตาราง `job_run_histories`
- ตาราง `job_configs` และ `job_run_histories` **ถูกลบจาก target schema** (24 → 22 ตาราง)

## ระบบ audit ของ master — ยกเลิกและลบทิ้ง (ตัดสินใจ 2026-08-07 · 1 เส้น)

**ลบทิ้งแล้ว** — `GET /audit-logs` ถูกเอาออกจาก `plan-api.html` (GROUPS + `SQL_BY_PATH`) · ตาราง `audit_logs` ถูกลบจาก target schema (22 → 21 ตาราง) · การ์ด "ประวัติการแก้ไขข้อมูล" ถูกลบจาก `k2-factors.html` และ `k2-competitors.html` · ฟิลด์ **"เหตุผลการแก้ไขข้อมูล"** ถูกลบจาก `SCHEMAS` ใน `assets/sbp.js` ทั้ง 4 จุด

**ผลที่ตามมาที่ต้องรับทราบ:** เดิมเก็บ `audit_logs` ไว้เพราะ**ระบบ SBP เดิมไม่มี audit กลางของ master** (มีเฉพาะ `general_upload_data_page_audit_log` ของงาน upload) — หลังยกเลิกจึง **ไม่มีร่องรอยว่าใครแก้ master ปัจจัยภายนอก/รายชื่อคู่แข่ง เมื่อไร จากค่าอะไรเป็นอะไร และด้วยเหตุผลใด** · ถ้าภายหลังต้องการ audit กลับมา ให้พิจารณาใช้กลไก audit ของระบบ SBP เดิมแทนการสร้างตารางใหม่

**สิ่งที่ยังอยู่:** `consideration_logs` (ประวัติผลพิจารณารายเอกสาร — คนละเรื่องกับ audit ของ master) · `interface_transactions` (tracking รับ–ส่งไฟล์) · audit ของ RBAC/config/email template ที่อยู่ฝั่งระบบ SBP เดิม

## มติจากการเทียบฐานข้อมูลจริง (2026-08-10 · DP-1 · DP-3 · DP-9)

| มติ | ผลต่อ API |
|---|---|
| **DP-9 = แยกตัดสิน** | **ตัด `GET /decisions`** (30 → 29 เส้น · Lookup 3 → 2) — FE ใช้ `GET /common/common-code?codeType=SBPGI_DECISION` ของระบบเดิม · เส้น `/sbpgi/master/factors*` และ `/sbpgi/master/competitors*` **คงเดิมทั้ง 8 เส้น** |
| **DP-1 = ทางเลือก B** | `POST /sbpgi/workflow/instances` ต้องส่ง **`referenceId` = `compensation_documents.id` (surrogate)** ไม่ใช่ `doc_no` · `GET /sbpgi/document/{docNo}/timeline` และเส้นที่ต้องคุยกับ engine ต้อง **join ผ่าน `id`** ก่อนเรียก engine · `docNo` ยังเป็น path parameter ที่ผู้ใช้เห็นเหมือนเดิม |
| **DP-3 = ทางเลือกที่ 3** | ไม่กระทบ endpoint — `impacted_stores` ยังเป็นตาราง (snapshot บางส่วน) เส้นที่อ่านข้อมูลร้านไม่เปลี่ยน |

**ยังค้าง 6 ข้อ** (DP-2 · DP-6 ถึง DP-8 · DP-11 · DP-12 — **DP-4 ปิดแล้ว 2026-08-24** เมื่อตัด Job 1 ImportQSSI · **DP-10 ปิดแล้ว** SBPGI อยู่ใน store-backend เดิม) — ดู [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md)

## เส้นที่ตัดออก — ใช้ระบบ SBP เดิม (ตัดสินใจ 2026-08-05 · 18 เส้น)

comment ไว้ใน `plan-api.html` (GROUPS) พร้อมหมายเหตุ — ไม่ใช่ "รอตัดสินใจ" แต่เป็นการตัดถาวรเพราะระบบ SBP ปัจจุบันมีอยู่แล้ว (คู่กับหน้า `k2-permissions.html` / `k2-operators.html` ที่ถอดจาก sidebar):

| กลุ่มเดิม | เส้นที่ตัด | ใช้ของระบบเดิมแทน |
|---|---|---|
| Auth & สิทธิ์ผู้ใช้ (4) | `POST /auth/login` · `POST /auth/refresh` · `GET /auth/me` · `GET /me/menus` | BFF: login redirect (Cognito·cookie) · `/auth/refresh` · `/auth/profile`+`/users/current` · `/menus` |
| Master ผู้ปฏิบัติงาน (5) | `GET/POST/PUT/DELETE /operators` · `/operators/{id}` · `GET /employees/search` | group+scope ของ auth-backend (จัดการหน้า `/setting/manage-user-rights`) · ค้นพนักงานผ่าน employee backend เดิม |
| Master สิทธิ์เมนู (9) | `GET /menu-permissions` · `PUT /menu-permissions/{menuCode}` · `GET/POST/PUT/DELETE /roles` · `/roles/{roleCode}` · `POST/PUT/DELETE /menus` · `/menus/{menuCode}` | auth-backend: `/groups` · `/groups/{id}/permissions` · `/groups/permissions/template` · `/menus` |

## เส้นที่เปลี่ยนไปใช้ของระบบ SBP เดิม (ตัดสินใจ 2026-08-06 · 3 ตัด + 5 เปลี่ยนแหล่งข้อมูล · เดิมมี `/email-templates/*` และ `/configs` ด้วย แต่ถูกลบทั้งกลุ่มแล้ว)

ตรวจ `SBP/README.md` + repo `srm-sps-spsap-store-backend` (79 entity · 25 controller) แล้วยึด**ของที่มีอยู่จริงเป็นหลัก**:

### ตัดออก 3 เส้น — มี API พร้อมใช้อยู่แล้ว

| เส้นเดิมของ SBPGI | ใช้ของระบบ SBP แทน |
|---|---|
| `GET /stores/search` | `GET /store/search` · `/store/list` · `/store/detail` · `/store/opt-name` (ตาราง `store`/`mas_store`/`sevenshop`) |
| `GET /zones` | `GET /store/all-regions` · `/store/regions-by-email` · `/store/province-by-region` (ตาราง `mas_zone`) |
| `GET /branch-types` | `GET /common/common-code` · `/master/common` (ตาราง `common_code` — คนละ `code_type`) |

### คงเส้นไว้ แต่เปลี่ยนแหล่งข้อมูลไปที่ของระบบเดิม

> **Workflow engine ของระบบเดิม — ข้อเท็จจริงจากฐานข้อมูลจริง** (ตรวจ 2026-08-10 · `SBP/db-schema-sps_store.md` · `SBP/db-schema-sps_auth.md`)
>
> - **engine มี 13 ตาราง ไม่ใช่ 10** (เอกสารเดิมของเราเขียนผิด): `workflow` · `workflow_version` · `workflow_state` · `workflow_status` · `workflow_event` · `workflow_route` · `workflow_group` · `workflow_group_map` · `workflow_transaction` · `workflow_history` · `workflow_approver` · `workflow_part` · `workflow_part_display`
> - **engine ตัวจริงที่ SBPGI ต้องต่อคือชุดใน schema `sps_store` ไม่ใช่ `sps_auth`** — ทั้งสอง schema มี 13 ตารางชื่อเดียวกันครบ แต่เป็นคนละชุดข้อมูลและ**คนละเวอร์ชัน** (`workflow_state` ของ `sps_auth` 3 คอลัมน์ / ของ `sps_store` 4 คอลัมน์)
>   - `sps_store`: `workflow_transaction` **19,283 แถว** · `workflow_history` **38,010** · `workflow_approver` **96,542** (ของใช้งานจริง)
>   - `sps_auth`: `workflow_transaction` 55 · `route` 41 · `state` 10 (ชุดของ auth-backend คนละเรื่อง)
>   - → ทุกที่ที่เอกสารนี้อ้างตาราง engine ให้อ่านว่า **`sps_store.<table>`**
> - ⚠️ **ความเสี่ยงที่ต้องคุยกับทีมเจ้าของ library:** `sps_store.workflow_transaction` **ไม่มี PK และไม่มี index เลย** ทั้งที่มี 19,283 แถว (ตารางชื่อเดียวกันใน `sps_auth` มี PK ปกติ) — กระทบ performance ของ `GET /sbpgi/document/tasks` / `POST /sbpgi/document/{docNo}/actions` ที่ต้อง query ตาราง**นี้ทุกครั้ง** · เป็นข้อเท็จจริงที่ตรวจพบ ไม่ใช่ข้อเสนอ · **ยังไม่ตัดสิน**ว่าจะแก้อย่างไร (เพิ่ม index / ขอ library เวอร์ชันใหม่ / อ่านผ่าน view)
> - **ข้อสังเกต (ยังไม่ตัดสิน):** `workflow_part` + `workflow_part_display` ของ engine คุมการแสดงผล**รายส่วนของหน้าจอ** (READ/WRITE ต่อ state) ซึ่ง**ทับซ้อน**กับกลไก `data-editrole` / `.edit-only` ที่ prototype ทำเอง และกับธง `permissions.canEditSections` ที่ `GET /sbpgi/document/{docNo}` คืน — ต้องเลือกว่าจะให้ engine เป็นเจ้าของสิทธิ์แก้รายส่วนหรือให้ SBPGI คำนวณเอง (ดู `SBP/SBPGI-vs-existing-system.md` หัวข้อ 4)
>
> **✅ ชื่อ function ของ engine — ยึดตาม LLDD ของ lib (ปิดข้อค้าง 2026-08-14)**
>
> **API สาธารณะของ `@srm/glb-workflow` = 8 function ตามชีต `Detail` ของ `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx`** ซึ่งเป็นเอกสารของ lib เอง จึงเป็นแหล่งความจริง · อีก 2 ชุดที่เคยขัดกันไม่ใช่ชื่อ API: ชีต **Mermaid seq / ชีต "2"** ใช้คำว่า *Trigger Event* เป็น **ชื่อหัวข้อของขั้นตอนภายใน** `eventWorkflow` · ส่วน `TriggerEventUseCase` / `AddPreparedApproverUseCase` / `GetPendingFlowUseCase` ใน `SBP/srm-sps-spsap-store-backend.md` §1.5 เป็น **UseCase class ที่ store-backend ห่อไว้ใช้เอง** ไม่ใช่ API ของ lib
>
> | # | function | พารามิเตอร์ (ตามชีต Detail) | SBPGI ใช้ที่ไหน |
> |---|---|---|---|
> | 1 | `initializeWorkflow` | `version, userId, referenceId` | เปิด flow ให้เอกสารใหม่ (Job 8b · `POST /sbpgi/workflow/instances`) |
> | 2 | `eventWorkflow` | `version, referenceId, event, eventParam, remark, userId` | `POST /sbpgi/document/{docNo}/actions` |
> | 3 | `getPermissionEvents` | `version, referenceId, userData` | ปุ่ม/ผลพิจารณาที่ user กดได้ในหน้าเอกสาร |
> | 4 | `getHistory` | `version, referenceId` | `GET /sbpgi/document/{docNo}/timeline` |
> | 5 | `getTransaction` | `version, referenceId` | สถานะ + ผู้ถืองานปัจจุบันของเอกสาร |
> | 6 | `getPendingFlowByUser` | `userData` | **หน้า เอกสาร → รอดำเนินการ** (`k2-list-waiting.html`) + reminder รายสัปดาห์ |
> | 7 | `getWorkflowsByUser` | `userData` | **หน้า เอกสาร → ที่เกี่ยวข้อง** (`k2-list-related.html`) — flow ที่ user อยู่ด้วย รวมที่ยังไม่ถึงคิวและที่อนุมัติไปแล้ว |
> | 8 | `addPreApprover` | `version, userId, referenceId, state_id, approver, seq` | ตั้งผู้อนุมัติล่วงหน้าของขั้นถัดไป |
>
> **`eventWorkflow` รับพารามิเตอร์มากกว่าที่ชีต Detail เขียนไว้** — ชีต "2" (รายละเอียดของ function นี้) ระบุ input จริงเป็น `versionId · referenceId · event · eventParam · remark · userData · userFullname · nextApproverId` โดย 3 ตัวหลังมาจากส่วนขยายลงวันที่ 29/04/2026 · 20/05/2026 · 16/06/2026 (`nextApproverId` ใช้เมื่อ `approver_type = user` · `userFullname` ลง `workflow_history.create_by_name`) — **ยึดชุดนี้เวลาเขียนโค้ด**
>
> 🎯 **จุดที่ตรงกับหน้าจอเราพอดี:** function 6 และ 7 คือฝาแฝด `k2-list-waiting` / `k2-list-related` — ไม่ต้องเขียน query งานค้างเอง

| เส้น | เดิมอ่าน/เขียนตาราง | เปลี่ยนเป็น |
|---|---|---|
| `GET /sbpgi/document/tasks` | `workflow_tasks` ของ SBPGI | **`@srm/glb-workflow`** (schema `sps_store`) — `getPendingFlowByUser({userData})` · **[✅ DP-1 ปิดแล้ว 2026-08-17 — `reference_id` = `compensation_documents.id` (surrogate) · ⚠️ DP-2 ยังไม่ตัดสิน]** และ `sps_store.workflow_transaction` ไม่มี PK/index (19,283 แถว) จึงเป็น seq-scan — [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) หัวข้อ 4 แล้ว join ข้อมูลเอกสารของ SBPGI · อ่าน `sps_store.workflow_transaction` + `workflow_approver` · inbox รวมทุกระบบที่มีอยู่แล้วคือ `GET /api/workflow/pending` (store-backend) |
| `POST /sbpgi/document/{docNo}/actions` | `workflow_instances` + `workflow_tasks` | `eventWorkflow({versionId, referenceId, event, remark, userId, nextApproverId})` — **[✅ DP-1 ปิดแล้ว 2026-08-17 — `referenceId` = `compensation_documents.id` (surrogate · ส่งเป็น string เพราะ `reference_id` ของ engine เป็น varchar(255))]** (หลักฐานจากระบบเดิม cooperation-request · inform-evaluate ใช้ surrogate id ทุกจุด) ของ engine · ผู้อนุมัติขั้นถัดไปใช้ `addPreApprover()` · เขียน `sps_store.workflow_transaction` / `workflow_history` / `workflow_approver` |
| `GET /sbpgi/document/{docNo}/timeline` | `consideration_logs` อย่างเดียว | `getHistory()` ของ engine (state transition) อ่าน `sps_store.workflow_history` **join** `consideration_logs` ของ SBPGI (decision · ไฟล์แนบ · ความเห็น) · **[✅ DP-7 ปิดแล้ว 2026-08-24]** `consideration_logs` เป็น **timeline เต็มของ SBPGI** (ตารางของเราเอง ผูก `transaction_id` ของ engine) ไม่ต่อยอดบน `workflow_history` · **[✅ DP-1 ปิดแล้ว 2026-08-17]** `referenceId` ที่ใช้เรียก `getHistory()` = `compensation_documents.id` |
| `GET /sbpgi/lookup/workflow-sections` · `GET /sbpgi/lookup/document-statuses` | `workflow_sections` / `document_statuses` | `sps_store.workflow_state` / `workflow_route` / `workflow_status` ของ engine + **วงเงินอนุมัติจาก `common_code`** (`code_type = SBPGI_APPROVE_LIMIT`) |
| `POST /sbpgi/document/{docNo}/attachments` · `GET .../download` | เขียน storage layer เอง | เก็บ metadata ใน `document_attachments` ของ SBPGI แต่ **ไฟล์ใช้ service S3 เดิม** `POST /statement/upload-file-aws` · `POST /statement/download-file-aws` · **[✅ DP-8 ปิดแล้ว 2026-08-24]** ใช้ตาราง `document_attachments` ของเราเอง (เก็บ metadata) + service S3 ของระบบเดิม ไม่ต่อยอด `upload_general` ของระบบเดิม (`job_id`/`audit_log_id` เป็น nullable ไม่ติด FK — เหตุผลจริงคือขาด `file_size`/`content_type`/`section_code`/`upload_status`/`purge_flag`) — [`SBP/SBPGI-vs-existing-system.md`](SBP/SBPGI-vs-existing-system.md) หัวข้อ 4 |

**Envelope ต้องตรงกับของเดิม:** สำเร็จ `{"success": true, "data": …}` · ผิดพลาด `{"success": false, "data": null, "error": {"code","message"}}` (ResponseInterceptor + HttpExceptionFilter ของ store-backend) — ข้อความ error ยังต้องเป็นไทย verbatim ตาม SRS

## ลิงก์ภายนอกและฟีเจอร์ที่ไม่มี endpoint (ยืนยันจากหน้าจอ K2 เดิม · 2026-08-06)

| จุดในหน้าจอ | เป็นอะไร |
|---|---|
| **ข้อมูลยอดขายเพิ่มเติม** | K2 เดิมลิงก์ออก **QlikView BI** (`bidashboard.cpall.co.th/qlikview/FormLogin.htm`) — ระบบใหม่คงลิงก์ BI ไว้เป็นช่องทางดูเชิงลึก (URL เก็บใน config ไม่ hardcode) · `GET /sbpgi/document/{docNo}/sales` ใช้เป็นข้อมูลประกอบ **ไม่มีกราฟในหน้าเอกสารแล้ว (2026-08-06)** |
| **คลิกเปิดเอกสาร Statement** | ลิงก์ตรงจาก `compensation_documents.statement_id` (ฟิลด์ที่ 10 ของไฟล์ `BPM06001O_`) — ไม่ใช่ endpoint ของ SBPGI |
| **แผนที่ AllMap** | `compensation_documents.allmap_url` (ฟิลด์ที่ 9 ของไฟล์ `BPM06001O_`) · **iframe ล้มได้จริง** (`Failed to fetch` ในภาพหน้าจอ) → FE ต้องมี fallback + ปุ่มเปิดแท็บใหม่ |
| **คำนวณเงินชดเชย (ขั้น 08)** | **iframe ของระบบ Finance & Account Unit (FS)** — ไม่ใช่หน้าจอของ SBPGI · ถ้าไม่ได้ล็อกอิน FS จะได้ `401 Unauthorized` → ต้องแสดงข้อความและปุ่มเปิดแท็บใหม่แทนกรอบเปล่า |
| **Copy Doc Link** · **Quick Search** · **Selected Filter (preset)** · **sort หัวคอลัมน์** | ฟีเจอร์ฝั่ง FE ล้วน — ไม่มี endpoint (preset เก็บใน `localStorage` ของเครื่องผู้ใช้) |

## อีเมล — SBPGI เป็นคนเรียก lib ส่งเอง (ปิด DP-5 · แก้มติ 2026-08-14)

> แหล่งความจริง: **`SBP/TSM-SRM-LLDD SBP EMAIL1.0.xlsx`** (v1.0 · 15/09/2025 · Sukol K. · reviewed Sudtida J.) — lib กลางสำหรับส่งอีเมล **ทำเสร็จและใช้งานจริงแล้ว** ให้ module อื่น import
> **ไม่ใช่ REST endpoint ของ SBPGI** — เป็นการเรียก library ภายใน จึงไม่นับรวมใน 29 เส้น

### สัญญาของ `sendEmail()`

| อาร์กิวเมนต์ | ความหมาย | SBPGI เติมค่าจากไหน |
|---|---|---|
| `emailId` | เลข template ใน `email_template` | **workflow ให้มา** — `sps_store.workflow_route.email_id` ของ route ที่เพิ่งเดิน (`"ถ้าไม่ระบุ จะไม่มีการส่งเมล์"`) · 🔴 **ต้องค้นด้วย `(version_id, from_state_id, event, to_state_id)` ครบทั้ง 4** — state 02 มี 2 route ตามวงเงิน (< 100,000 จบ · ≥ 100,000 ไป 03) ถ้าค้นแค่ `(from_state_id, event)` แล้ว `ORDER BY seq LIMIT 1` จะได้ template ผิดทุกครั้งที่เข้าเงื่อนไขที่สอง · เก็บ `from_state_id` จาก `getTransaction()` **ก่อน** เรียก `eventWorkflow()` และอ่าน `to_state_id` จาก `getTransaction()` **หลัง** สำเร็จ · เมลที่ไม่ใช่ transition (reminder/escalation/batch) เก็บเลขไว้ที่ `mas_param` |
| `mailTo` | ผู้รับ · หลายเมลคั่นด้วย `,` | ผู้อนุมัติลำดับถัดไปที่ engine resolve แล้ว (`workflow_transaction.current_approver` / `workflow_approver.current_approver` → ขยายกลุ่มด้วย `workflow_group_map`) → อีเมลจาก **`business_user.email`** |
| `mailCc` | สำเนา · รูปแบบเดียวกัน | **`fml_email_account`** (1,646 แถว) — ตารางนี้มี `template_id` อยู่แล้ว จึงเป็นกลไก "ใครรับ template ไหน" ของระบบเดิมโดยตรง: `SELECT string_agg(email, ',') FROM fml_email_account WHERE template_id = :emailId` · ไม่ต้องสร้างตารางกฎผู้รับใหม่ |
| `param` | ค่าที่ lib เอาไปแทน `{{key}}` ใน subject/body | SBPGI สร้างจากเอกสาร เช่น `{docNo, storeName, amount, sectionName}` |
| `fileAttach` | ไฟล์แนบ | ปกติไม่ใช้ในงาน workflow |
| `userId` | ผู้ดำเนินการ | → ลง `email_sent.send_by` |

ลำดับใน lib (ชีต MermaidSeq): `findById(emailId)` → แทนค่า `{{key}}` ใน subject/body → ส่ง → `INSERT email_sent` (`is_sent='Y'` หรือ `'N'` + `error`) → return `Success` / `Fail`

> ⚠️ **transport ยังไม่ยืนยัน — เอกสาร lib ขัดกันเองในไฟล์เดียว** (`SBP/TSM-SRM-LLDD SBP EMAIL1.0.xlsx`): ผังไฟล์เขียน *“ส่งเมล์ผ่าน **AWS SES**”* แต่ลำดับขั้นตอนเขียน *“ส่งเมล์ไปที่ **server mail SMTP**”* · และเอกสาร**ไม่ได้ระบุชื่อ package** (โครงไฟล์เขียนแค่ `email/`) → ดูข้อ 4.3 ใน [`DECISIONS-รอตัดสินใจ.md`](DECISIONS-รอตัดสินใจ.md)
> เรื่องที่**ยืนยันแล้ว**: อาร์กิวเมนต์ 6 ตัว · การแทนค่า `{{key}}` · การเขียน `email_sent` ทั้งกรณีสำเร็จและล้มเหลว · `is_sent` เป็น `'Y'`/`'N'` · เก็บ `error` เมื่อล้มเหลว

ตัวอย่างการแทนค่าจากเอกสาร: subject ใน DB = `[AD] ExportUserToAD ({{status}})` · ส่ง `param = {"status":"Success"}` → ได้ `[AD] ExportUserToAD (Success)`

### ทำไมไม่ให้ engine ส่งเอง

input ของ `eventWorkflow` มีแค่ `versionId · referenceId · event · eventParam · remark · userData · userFullname · nextApproverId` — **ไม่มี `mailTo`/`mailCc`/`param`/`fileAttach`** engine จึงเติมอาร์กิวเมนต์ที่ `sendEmail` บังคับไม่ได้ · และบรรทัดในชีต 2 ของ LLDD workflow ยังเขียนว่า *"เรียก function ส่งเมล์จาก lib **.....**"* ซึ่งเป็น **placeholder ที่ยังไม่เติมชื่อ function**

### 🔴 กับดักที่ dev ต้องรู้ก่อนเขียนโค้ด

1. **ชื่อคอลัมน์จริงคือ `email_sent.send_by` ไม่ใช่ `sent_by`** — ชีต Detail ของเอกสาร lib เขียน `sent_by` แต่ production (`SBP/db-schema-sps_store.md`) เป็น `send_by` · เขียนตามเอกสารแล้ว query พังทันที
2. **`email_template` จริงมี 12 คอลัมน์ ไม่ใช่ 8 และชื่อไม่ตรงเอกสาร** — เอกสาร lib เสนอ `email_id`/`email_name`/`subject_mail`/`body_mail`/`mail_from`/`mail_from_name` แต่ production คือ `email_template_id` · `email_template_name` · `email_template_desc` · `subject_format` · `body_format` · `sender` · `email_from` · `active_flag` · `create_by/date` · `update_by/date` · **seed template ของ SBPGI ต้องใช้ชื่อจริง** และอย่าลืม `active_flag='Y'`
3. **`sendEmail` คืนแค่ `Success`/`Fail` ไม่คืน `email_sent_id` และ lib ไม่ retry ให้** — ต้องเรียก**นอก transaction** ของ action เสมอ (อีเมลล้มต้องไม่ rollback การอนุมัติ) แล้วตามเก็บด้วยรายงาน `SELECT … FROM email_sent WHERE is_sent = 'N'`
4. **`fileAttach` ไม่ถูก log** — `email_sent` ไม่มีคอลัมน์ไฟล์แนบ ห้ามใช้เป็นหลักฐานว่าแนบไฟล์ไปแล้ว
5. **ต้องยืนยันกับทีมเจ้าของ `@srm/glb-workflow`:** ถ้า engine ส่งเมลเองด้วยบน route ที่มี `email_id` ผู้อนุมัติจะได้ **เมลซ้ำ 2 ฉบับ** — ทางแก้คือใช้ `workflow_route.email_id` เป็นค่า *อ่านอย่างเดียว* แล้วให้ SBPGI เรียก lib เอง
6. **ชื่อ package ยังไม่ยืนยัน** — เอกสาร lib ให้แค่โครงไฟล์ (`email.module.ts` · `email.service.ts` · `email-template.repository.ts` · `interfaces/`) ไม่ระบุชื่อ package · ชื่อ `@gosoft-sbp/email-lib` ที่อ้างในเอกสารชุดนี้มาจาก `SBP/srm-sps-spsap-store-backend.md` — confirm ก่อน import
7. **ช่องทางส่งขัดกันในเอกสารเดียวกัน** — ชีต Detail เขียน *"ส่งเมล์ผ่าน AWS SES"* แต่ MermaidSeq วาด participant เป็น `SMTP Server` · น่าจะเป็น SES ผ่าน SMTP interface แต่มีผลกับการตั้ง credential/allowlist จึงควรถามให้ชัด

## เอกสารที่เกี่ยวข้อง

- ตารางที่แต่ละเส้นอ่าน/เขียน: [database.md](database.md) · `plan-database.html` (**20 ตาราง** หลังตัด `audit_logs` 2026-08-07 และ `status_email_rules` 2026-08-11 · DP-5)
- เทียบ SBPGI กับระบบ SBP เดิม + **12 ข้อค้างตัดสินใจ (Decision Points)**: `SBP/SBPGI-vs-existing-system.md` หัวข้อ 4
- Schema จริงของระบบเดิม (ที่มาของตัวเลขทุกตัวในหัวข้อ workflow engine): `SBP/db-schema-sps_store.md` · `SBP/db-schema-sps_auth.md`
- LLDD ของ workflow engine (ที่มาของ API 8 function): `SBP/TSM-SRM-LLDD SBP workflow 1.2.xlsx` ชีต `Detail` · ฉบับแปลง `SBP/TSM-SRM-LLDD-SBP-workflow-1.2.md`
- LLDD ของ email lib (ที่มาของสัญญา `sendEmail`): `SBP/TSM-SRM-LLDD SBP EMAIL1.0.xlsx`
- Flow ที่ API ขับเคลื่อน: [workflow.md](workflow.md) · `plan-flow.html`
- Email จุดส่งในแต่ละสถานะ: `workflow_status_document.md` (ตารางสถานะ × action × ผู้รับ × อีเมล) — หน้าจอ Email Template ถูกลบ 2026-08-06 · template อยู่ในตาราง `email_template` ของระบบ SBP เดิม
