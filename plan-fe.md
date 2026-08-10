# plan-fe.md — Spec สร้าง Frontend ระบบ SBPGI (โมดูลใน Next.js portal `sbpm`) ฉบับละเอียด

> **เอกสารนี้คือ spec สมบูรณ์สำหรับ AI/นักพัฒนา สร้าง Frontend จริงจาก prototype HTML ในโฟลเดอร์นี้ — อ่านจบต้องสร้างได้โดยไม่ต้องถาม**
> อ่านคู่กับ: `checklist-fe.md` (ลำดับงาน + เกณฑ์ตรวจรับ) · `REACT-TODO-CHECKLIST.md` (แตก component ต่อหน้า ครบทุกหน้า) · `api.md` (**30 endpoint / 6 กลุ่ม** — Lookup 3 · Master Data 8 · เอกสาร 11 · รายงาน 2 · Workflow 3 · Interface 3 · Auth/RBAC/ผู้ปฏิบัติงานตัดไปใช้ระบบ SBP เดิม ตัดสินใจ 2026-08-05) · `workflow.md` (flow/สถานะ) · `database.md` (**21 ตาราง**) · `plan-be.md` (ฝั่ง Backend)
> **prototype HTML = spec หน้าจอที่ผูกมัด** — layout, ป้ายข้อความไทย, สี, ตาราง, modal ต้องตรงกับหน้า `*.html` เดิม ข้อความ popup/validation ห้าม paraphrase (verbatim จาก SRS)

**กติกาเหล็ก (ผิดข้อใดข้อหนึ่ง = ไม่ผ่าน — ซ้ำกับ checklist-fe.md โดยตั้งใจ):**
1. workflow 5 ขั้น `06 → 08 → 01 → 02 → 03` เท่านั้น — **ห้ามอ้าง section 04/05 หรือสถานะบัญชีในทุกที่** (SDD v7.5 ตัดแล้ว)
2. สถานะเอกสาร **6 ค่า** verbatim (ดู `DOC_STATUSES` ใน §7)
3. กฎวงเงินอนุมัติ (SDD GI 24/02/2026 — แทนเกณฑ์เดียว 100,000 เดิม): **≤ 50,000 → จบที่ GM(02)** · **50,001–300,000 → ผ่าน AVP(03) แล้วจบ** · **เกิน 300,000 SDD ยังไม่ระบุเส้นทาง (รอ confirm)** — logic routing อยู่ BE, FE แค่แสดงผล · เห็นควรไม่ชดเชยที่ขั้น 01/02 = **จบกระบวนการทันที** (ไม่ตีกลับ 06 · ขั้น 03 คงเดิม รอ confirm)
4. ข้อความไทย verbatim ห้าม paraphrase เช่น `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`
5. ภาค **13 รหัส** `BE BS NEU REU RSU BG BW RC RN BN NEL REL RSL` (SDD v7.5 · ใช้ชุดเดียวทั้งหน้ารายการและรายงาน) — โหลดจาก `GET /store/all-regions` (ระบบ SBP เดิม) **ห้าม hardcode** · ภาคใหม่ต้องขึ้นเองโดยไม่แก้หน้าจอ
6. %ชดเชยรวมทุกร้านเปิดใหม่ = **100%** พอดีก่อน submit
7. ไฟล์แนบ ≤ **5MB** + นามสกุลใน `ATTACH_EXTS`
8. เลขเอกสาร `YYYY/xxxxx` ปี **พ.ศ.** · วันที่แสดงผลเป็น พ.ศ. ทุกจุด
9. แถวยอดขายไม่ครบ 60 วัน = `tr.flag-red`
10. ใช้ **design system ของ portal เดิม** (PrimeReact + Tailwind) — ห้ามพอร์ต `assets/sbp.css` มาทับ และห้ามเพิ่ม UI/chart library ตัวใหม่ (กราฟเขียน SVG เองตาม prototype)

---

## Alignment กับระบบ SBP เดิม (สรุปจาก SBP/srm-sps-spsap-web-frontend.md + SBP/srm-sps-spsap-sbp-bff.md)

FE ของระบบ SBP ปัจจุบัน (repo `srm-sps-spsap-web-frontend` · package `sbp-portal`) คือ:
- **Next.js 16 App Router** ตั้ง `output: "export"` — **static export ขึ้น S3/CloudFront** (ไม่มี API routes, middleware ไม่ทำงานบน S3, กันสิทธิ์ฝั่ง client ทั้งหมด)
- **PrimeReact 10** (ห่อเป็น design system ภายใน `components/Form`/`Table`) + **Tailwind CSS 4** + Sass + **Zustand 5** (`loadingStore`/`permissionStore`/`userProfileStore`) + **@tanstack/react-query 5** + axios instance กลาง + **i18next** (default `th-TH`)
- **build 3 portal จาก codebase เดียว** ด้วย env `NEXT_PUBLIC_APP_TARGET` = `sml` (SBP Mall) / `siv` (Investor) / `sbpm` (Company back office)
- **Auth แบบ BFF cookie**: FE ไม่แตะ token — redirect `{bffUrl}/auth/login` ให้ BFF (NestJS + AWS Cognito OIDC) set token เข้ารหัสใน signed httpOnly cookie · axios `withCredentials` + interceptor 401 → `POST /auth/refresh` (lock + failedQueue) → retry · เมนูจาก `GET /menus` · สิทธิ์ต่อ URL จาก `GET /groups/current-user/permissions` (`canView/canManage/canExport/canOther`)

> ✅ **ข้อสรุป (ตัดสินใจ 2026-08-05): ยึดตามงานเดิม — เลือกทาง (ข)** พัฒนา SBPGI FE เป็น **โมดูลใหม่ใน `srm-sps-spsap-web-frontend` portal `sbpm` (Company back office)** ตาม convention ของ codebase นั้นทุกข้อ (Next.js 16 App Router · static export · PrimeReact + Tailwind · Zustand + react-query · axios interceptor · auth BFF cookie)
> — ใช้ shell/เมนู/สิทธิ์/design system/pipeline S3+CloudFront ร่วมกับ portal เดิม ไม่ deploy แยก
> **โฟลเดอร์ `react-app/` (React + Vite) ถูกลบทิ้งแล้ว 2026-08-06** (กู้จาก git history commit `003b661` ได้ถ้าจำเป็น) — ไม่ใช้เป็นฐานงานอีกต่อไป · โครงหน้าจอ/รายการ component ต่อหน้าใช้ `REACT-TODO-CHECKLIST.md` แทน
> ถ้าภายหลังจำเป็นต้องแยกเป็น standalone app จริง ๆ ค่อยยกประเด็นใหม่ — baseline คือโมดูลใน portal เดิม

## 0. สัญญากลาง FE/API Integration

> LLDD อ้างอิง: `LLDD/FE/LLDD-FE-Integration-Contracts.md` + `LLDD/BE/LLDD-BE-API-Common-Contracts.md` · ทุก feature hook/component ต้องยึดสัญญานี้ก่อนอ่าน endpoint รายตัวใน `api.md`

| หมวด | Contract ที่ FE ต้องยึด |
|---|---|
| API client | มี axios instance เดียวใน `shared/api/client.ts` ตั้ง `withCredentials: true`; component/page ห้ามสร้าง client เองและห้าม set auth header เอง (FE ไม่แตะ token — อยู่ใน httpOnly cookie ฝั่ง BFF) |
| Auth | **ใช้ระบบ SBP เดิมผ่าน BFF (ตัดสินใจ 2026-08-05)** — ไม่มี login form ของตัวเอง: redirect `{bffUrl}/auth/login?redirectUrl=<origin>` (Cognito OIDC · token ใน httpOnly cookie); 401 non-auth endpoint ต้อง refresh แบบ single-flight `POST {bffUrl}/auth/refresh` แล้ว replay request เดิม (แบบ interceptor ของระบบเดิม); refresh fail ให้ redirect กลับ `{bffUrl}/auth/login` |
| Error | type กลาง `ApiError { code: string; message: string }`; แสดง `message` จาก BE ตรง ๆ ผ่าน `apiErrorMessage()`; fallback ไทยใช้เฉพาะ network/no response |
| Pagination | type กลาง `PageResponse<T> { page; size; total; items }`; `<DataTable>`/`<Pager>` ทุกหน้าใช้ shape นี้ |
| Format | payload date/month เป็น ค.ศ. ISO; แสดงผลเป็น พ.ศ. ผ่าน `shared/lib/format.ts` เท่านั้น; `storeCode/newStoreCode` เป็น string 5 หลักเพื่อคง leading zero |
| Workflow action | `DecisionPanel` ส่ง `POST /documents/{docNo}/actions` ด้วย `{result, comment}` เท่านั้น; result เป็น 6-enum ไทย verbatim; consume response `{nextSection,statusCode,status}` แล้ว invalidate detail/timeline/tasks |
| RBAC/Menu | **ใช้ของระบบเดิมผ่าน BFF**: sidebar จาก `GET /menus` + route guard/ปุ่ม จาก `GET /groups/current-user/permissions` (`canView/canManage/canExport/canOther` ต่อ URL — เก็บใน permission store แล้วเช็คผ่าน `hasPermission(url, action)`); หน้า detail ใช้ `permissions.canEditSections`/`canAction` จาก `GET /documents/{docNo}` (ธงเชิง workflow ที่ SBPGI คำนวณเอง); FE ไม่คำนวณ transition หรือ owner เอง |
| Audit/Reason | master/config/email mutation ต้องมีช่อง reason และส่งให้ BE; FE ไม่เขียน audit เอง (การแก้สิทธิ์/กลุ่มผู้ใช้ทำในระบบเดิม `/setting/manage-user-rights` — ลง audit ของระบบเดิม) |

## 1. Stack และเวอร์ชัน (ตัดสินใจแล้ว — ห้ามเปลี่ยนเอง)

| ส่วน | เลือกใช้ | เหตุผล |
|---|---|---|
| Framework | **Next.js 16 App Router** ใน repo `srm-sps-spsap-web-frontend` (portal `sbpm`) · `output: "export"` → **static export ขึ้น S3/CloudFront** | ตัดสินใจ 2026-08-05 — ยึด stack เดิมของระบบ SBP |
| Runtime | **React 19 + TypeScript** (strict) | ตามระบบเดิม |
| Router | **App Router** — หน้าอยู่ `src/app/(main)/<route>/page.tsx` (ไม่มี react-router) | convention ของ portal เดิม |
| Server state | **@tanstack/react-query v5** | cache/refetch ต่อ endpoint, retry, invalidate หลัง mutation (มีอยู่แล้วในระบบเดิม) |
| Client state | **Zustand 5** (`userProfileStore` / `permissionStore` / `loadingStore` **ที่มีอยู่แล้ว** — ห้ามสร้าง store ผู้ใช้/สิทธิ์ชุดใหม่) | ใช้ของ portal ร่วมกัน |
| Form | **react-hook-form + yup** (ตาม validation engine ของระบบเดิม) | validation message ไทย verbatim |
| HTTP | **axios instance กลางของ portal** (`src/services/*.service.ts` + interceptor เดิม) | `withCredentials` (cookie BFF) + auto-refresh single-flight — ไม่มี JWT ฝั่ง FE |
| UI / CSS | **PrimeReact 10 + Tailwind CSS 4 + Sass** ตาม design system ของ portal · ใช้ prototype HTML เป็น **spec ของ layout/ข้อความ** แล้ว map เป็น component ของระบบเดิม | ห้ามพอร์ต `assets/sbp.css` มาทับ design system เดิม (เปลี่ยนจากแผนเดิม) |
| Chart | **เขียน SVG component เอง** (พอร์ตจาก engine `data-chart` ใน sbp.js) | prototype ใช้ inline SVG ทั้งหมด ห้ามเพิ่ม chart lib |
| Font | Google Fonts **Prompt + Sarabun** (link ใน index.html) | ตามเดิม |
| Lint/Format | eslint (typescript + react-hooks) + prettier | มาตรฐาน |
| Test | **jest + @testing-library/react** (ตาม setup ของ repo เดิม) + mock service | ดู checklist |

Node >= 20 · pnpm (ถ้าไม่มีใช้ npm ได้)

เครื่องมือคุณภาพโค้ด (ติดตั้งตั้งแต่ Phase 0):
- **husky + lint-staged** — pre-commit รัน eslint+prettier เฉพาะไฟล์ที่แก้
- **commitlint** (`@commitlint/config-conventional`) — บังคับ Conventional Commits
- **CI ของ repo เดิม (Bitbucket Pipelines)** — ทุก PR รัน `lint → typecheck → jest → next build`
- **path alias `@/`** = `src/` (ตั้งใน tsconfig ของ portal อยู่แล้ว) — ห้าม relative import ลึก ๆ (`../../..`)

## 2. เริ่มงานในโปรเจกต์เดิม (ไม่สร้าง repo ใหม่)

**ไม่ใช้ `create vite` และไม่ตั้ง repo ใหม่** — SBPGI FE เป็นโมดูลใน `SBP/srm-sps-spsap-web-frontend` (portal `sbpm`)

```bash
cd SBP/srm-sps-spsap-web-frontend
npm install
NEXT_PUBLIC_APP_TARGET=sbpm npm run dev      # ทำงานบน portal Company back office
npm run build                                 # next build + static export (output: "export") → S3/CloudFront
npm run lint && npx jest                      # ตาม pipeline เดิมของ repo
```

Dependency ที่ต้องใช้ **มีอยู่แล้วทั้งหมด** (Next.js 16, React 19, PrimeReact, Tailwind 4, Zustand, react-query, axios, react-hook-form + yup, i18next, jspdf/exceljs) — **ห้ามเพิ่ม dependency ใหม่โดยไม่จำเป็น** โดยเฉพาะ UI/chart library ตัวที่สอง

**สิ่งที่เพิ่มเข้าไปในโปรเจกต์เดิม:**

| เพิ่มที่ไหน | ของอะไร |
|---|---|
| `src/app/(main)/sbpgi/**` | หน้าจอทั้งหมดของระบบประกันรายได้ (ดูตาราง route §4) |
| `src/services/sbpgi/*.service.ts` | service ต่อกลุ่ม API ตาม convention เดิม (axios instance กลาง + `withCredentials`) |
| `src/components/sbpgi/**` | component เฉพาะโดเมน (DecisionPanel, DocumentSections, WorkflowSteps ฯลฯ) — component กลาง (Table/Form/Pager/Toast) **ใช้ของ portal เดิม** |
| `src/types/sbpgi/*.ts` | DTO ตาม §8 |
| เมนู sidebar | **ไม่ hardcode** — เพิ่มรายการเมนูในระบบสิทธิ์เดิม (auth-backend) แล้ว portal จะ render จาก `GET /menus` เอง |

**env** (เพิ่มใน `.env` ของ portal เดิม — ไม่ตั้งไฟล์ env ชุดใหม่):
```
NEXT_PUBLIC_APP_TARGET=sbpm
NEXT_PUBLIC_BFF_URL=https://sbpm-bff-dev.cpall.co.th/api/v1   # BFF เดิม — ทุก request ผ่าน BFF (auth + proxy ไป SBPGI BE)
```
> ข้อจำกัดที่ต้องรู้จาก static export: **ไม่มี API routes และ middleware ไม่ทำงานบน S3** → route guard/สิทธิ์ต้องเช็คฝั่ง client ด้วย `permissionStore.hasPermission(url, action)` เหมือนหน้าอื่นของ portal · หน้าไหนต้องใช้ dynamic segment ให้ใช้ query param หรือ `generateStaticParams` ตามที่ portal เดิมทำ


## 3. โครงสร้างไฟล์ในโปรเจกต์เดิม (บังคับ — ตาม convention ของ `srm-sps-spsap-web-frontend`)

ทุกอย่างวางใต้ repo เดิม **ห้ามสร้างโครง feature-based ชุดใหม่ทับ convention ของ portal**

```
srm-sps-spsap-web-frontend/
  src/
    app/(main)/sbpgi/                      # ★ หน้าจอ SBPGI ทั้งหมด (App Router)
      documents/waiting/page.tsx           #   หน้าแรกของโมดูล — งานรอดำเนินการ
      documents/related/page.tsx
      documents/[year]/[running]/page.tsx  #   เอกสาร (docNo = `${year}/${running}` — ห้าม encode "/" เป็น %2F)
      documents/create/page.tsx            #   หน้าอธิบายกระบวนการ FS (ไม่มีฟอร์ม · 2026-08-06)
      reports/income-audit/page.tsx
      masters/factors/page.tsx
      # ไม่มีโฟลเดอร์ admin/ แล้ว — Global Config + Email Template ลบทั้งฟีเจอร์ · Batch Job ย้ายไปกลุ่ม Flow เหลือ Flowchart + DB (2026-08-06)
    components/sbpgi/                      # ★ component เฉพาะโดเมน
      DecisionPanel.tsx  WorkflowSteps.tsx  DocumentSections/*        # ไม่มี StatCards แล้ว (2026-08-06)
      charts/DonutChart.tsx                                   # SVG เขียนเอง (พอร์ตจาก prototype · กราฟยอดขาย/สัดส่วนชดเชยถอดออก 2026-08-06)
    services/sbpgi/                        # ★ service ต่อกลุ่ม API (axios instance กลางของ portal)
      documents.service.ts  tasks.service.ts  reports.service.ts  masters.service.ts  lookups.service.ts
    types/sbpgi/                           # ★ DTO ตาม §8
    hooks/sbpgi/                           # ★ react-query hook ต่อ endpoint (query keys §6)
    lib/sbpgi/constants.ts                 # ★ ค่าคงที่ธุรกิจ §7 (สถานะ/section/วงเงิน/ext)
```

**ของที่ใช้ร่วมกับ portal เดิม — ห้ามสร้างใหม่:** axios instance + interceptor · `userProfileStore`/`permissionStore`/`loadingStore` (Zustand) · component กลาง `Form/*`, `Table/*`, `Pager`, `Toast`, `Permission/AccessDenied` · layout/sidebar/breadcrumb ของ portal · i18n · date/number formatter

Convention การตั้งชื่อ (ตาม repo เดิม):
- Component = `PascalCase.tsx` · hook = `useXxx.ts` · service = `<domain>.service.ts` · type = `<domain>.types.ts`
- หน้าใน App Router เป็น **client component** (`"use client"`) เพราะ static export + ต้องใช้ store/permission ฝั่ง client
- 1 component ต่อไฟล์ · props type ชื่อ `XxxProps` ประกาศในไฟล์เดียวกัน · import ผ่าน alias `@/`


## 4. ตาราง Route (1:1 กับ prototype)

> ไม่มี route `/login` — auth ใช้ redirect ไป `{bffUrl}/auth/login` ของระบบเดิม (ดู §5) · คอลัมน์สิทธิ์ = role อ้างอิงตาม SRS (map เป็น group ของระบบเดิม) — **route guard จริงเช็ค `canView` ต่อ URL** จาก `GET /groups/current-user/permissions`

| Route (ใต้ portal `sbpm`) | หน้า prototype | Page | สิทธิ์ (role อ้างอิง) | Endpoints หลัก |
|---|---|---|---|---|
| `/sbpgi/documents/waiting` ★ | k2-list-waiting.html | `documents/waiting/page.tsx` — **หน้าแรกของโมดูล** (ยกเลิกหน้า Overview 2026-08-06) | ทุก role | `GET /tasks` (ไม่มี stat cards แล้ว) |
| `/sbgpi/documents/related` | k2-list-related.html | `documents/related/page.tsx` | ทุก role | `GET /documents` (ปี required) |
| `/sbpgi/documents/create` | k2-create.html | `documents/create/page.tsx` — **หน้าอธิบายกระบวนการ ไม่มีฟอร์ม** (2026-08-06 · ต้นทางสร้างที่ FS แล้วรอ SBP Statement ~1 วัน) | ตามสิทธิ์เมนู | — (ไม่เรียก API) |
| `/sbpgi/documents/[year]/[running]` | k2-document.html | `documents/[year]/[running]/page.tsx` | ตาม role/section | `GET/PUT /documents/{docNo}` + ลูก ๆ |
| `/sbpgi/reports/income-audit` | k2-report.html | `reports/income-audit/page.tsx` | 01/04/06 | `GET /reports/status-summary` (+`/export`) · `GET /store/all-regions` (ระบบ SBP เดิม) (checkbox ภาคอัตโนมัติ) |
| `/sbpgi/masters/factors` | k2-factors.html | `masters/factors/page.tsx` | 01/03 | `/factors` CRUD |

หมายเหตุ route:
- **ไม่มีกลุ่ม `/admin/*` แล้ว (2026-08-06):** `system-config.html` (ตั้งค่าระบบ Global Config) และ `email-template.html` (Email Template) **ถูกลบทั้งฟีเจอร์** — ค่ากำหนดกลางและ template อีเมลบริหารจัดการที่ระบบ SBP เดิม (`mas_param` / `email_template`) · `job-batch.html` **ย้ายไปกลุ่มเมนู Flow ("Flow Batch Job") และเหลือแค่ Flowchart + Database ที่ใช้** — batch job ยังรันปกติแต่พารามิเตอร์/ตารางเวลากำหนดใน backend config
- **หน้า `k2-operators.html` / `k2-permissions.html` ไม่พอร์ต** (ตัดสินใจ 2026-08-05) — กำหนดผู้ปฏิบัติงานและสิทธิ์เมนูใช้ระบบ SBP เดิม (auth-backend: groups/menus/permissions ต่อ URL · จัดการผ่านหน้า `/setting/manage-user-rights` ที่มีอยู่แล้ว)
- **หน้า Overview และหน้าข้อมูลผิดปกติ/แจกงานถูกยกเลิก** (2026-08-06) — หน้าแรกของโมดูลคือ `documents/waiting` · ข้อมูลผิดปกติเหลือเป็นแถวแดง + ตัวกรอง "ยอดขายไม่ครบ 60 วัน" ในหน้ารายการ
- `docNo` มี `/` ข้างใน (`2026/00123`) → route เป็น `[year]/[running]` แล้วประกอบเป็น docNo ใน page (`${year}/${running}`) — ห้าม encode `/` เป็น `%2F`
- หน้ากลุ่ม Flow/Database/Plan (`flow-fgi`, `k2-flow`, `plan-*`, `*-database`) เป็น**เอกสารออกแบบ ไม่พอร์ต**เข้าแอปจริง
- **DocListPage ใช้ component เดียว 2 mode** (prototype เป็นไฟล์ฝาแฝด ต่างแค่ `MODE`): `waiting` → `GET /tasks` (inbox: เฉพาะสถานะ "รอ<role ตัวเอง>ดำเนินการ") · `related` → `GET /documents` (**บังคับเลือกปี พ.ศ. ก่อนค้นหา** — ไม่เลือก = ห้ามยิง API + error ใต้ช่องปี)

## 5. Auth — ใช้ระบบ SBP เดิมผ่าน BFF (Cognito · httpOnly cookie · ตัดสินใจ 2026-08-05)

**ไม่มี login form ของตัวเอง** — การไหลแบบเดียวกับ FE ระบบเดิม (`apiClient.ts` ของ `sbp-portal`):
1. ผู้ใช้ยังไม่มี session (เรียก API แล้วได้ 401 และ refresh ไม่ผ่าน) → `window.location.assign(`${bffUrl}/auth/login?redirectUrl=${origin}`)` — BFF จัดการ OIDC กับ **AWS Cognito** แล้ว set token (เข้ารหัส) ใน **signed httpOnly cookie** เด้งกลับมา · FE **ไม่แตะ token เลย** (ไม่มี localStorage/memory token)
2. ตอน boot แอป: ยิง `GET /users/current` (โปรไฟล์+group) → เก็บใน profile store · `GET /menus` → **สร้าง sidebar จาก response** (ห้าม hardcode เมนูต่อ role ฝั่ง FE; MODULES registry เป็นแค่ meta icon/route/label แล้ว filter ด้วยเมนูจาก API) · `GET /groups/current-user/permissions` → เก็บใน permission store
3. ทุก request ใช้ axios `withCredentials: true` · 401 → auto-refresh single-flight แล้ว replay (ข้อ 5.2)
4. Logout: เรียก `GET {bffUrl}/auth/logout` (BFF ลบ cookie + คืน `logoutUrl` ของ Cognito) → redirect ตาม response

### 5.1 `features/auth/store.ts` (zustand — แนว `userProfileStore`/`permissionStore` ของระบบเดิม)
```ts
import { create } from 'zustand';
import type { UserProfile, MenuItem, PermissionEntry } from '@/shared/types/dto';

interface AuthState {
  user: UserProfile | null;            // จาก GET /users/current — ไม่มี token ใด ๆ ฝั่ง FE (อยู่ใน httpOnly cookie)
  menus: MenuItem[];                   // จาก GET /menus (BFF ระบบเดิม)
  permissions: PermissionEntry[];      // จาก GET /groups/current-user/permissions
  setUser: (u: UserProfile) => void;
  setMenus: (m: MenuItem[]) => void;
  setPermissions: (p: PermissionEntry[]) => void;
  hasPermission: (url: string, action: 'canView' | 'canManage' | 'canExport' | 'canOther') => boolean;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null, menus: [], permissions: [],
  setUser: (user) => set({ user }),
  setMenus: (menus) => set({ menus }),
  setPermissions: (permissions) => set({ permissions }),
  hasPermission: (url, action) => !!get().permissions.find((p) => p.url === url)?.[action],
  clear: () => set({ user: null, menus: [], permissions: [] }),
}));

export const useAuth = () => useAuthStore((s) => ({ user: s.user, isAuthed: !!s.user, menus: s.menus, hasPermission: s.hasPermission }));
```

### 5.2 `shared/api/client.ts` (axios เต็ม — cookie BFF + refresh single-flight แบบระบบเดิม)
```ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { env } from '@/shared/lib/env';

export interface ApiError { code: string; message: string }   // message = ไทยตาม SRS แสดงตรง ๆ

/** session อยู่ใน httpOnly cookie ของ BFF — ห้าม set Authorization header เอง */
export const api = axios.create({ baseURL: env.apiBase, timeout: 30_000, withCredentials: true });

export const redirectToLogin = () =>
  window.location.assign(`${env.apiBase}/auth/login?redirectUrl=${encodeURIComponent(window.location.origin)}`);

/* ---- refresh single-flight: 401 หลายเส้นพร้อมกัน → ยิง /auth/refresh ครั้งเดียว (แบบ isRefreshing+failedQueue ของระบบเดิม) ---- */
let refreshing: Promise<void> | null = null;

async function refreshSession(): Promise<void> {
  // ใช้ axios ดิบ (ไม่ใช่ instance) กัน interceptor วนซ้ำ — BFF อ่าน refresh_token จาก cookie เอง
  await axios.post(`${env.apiBase}/auth/refresh`, null, { withCredentials: true });
}

api.interceptors.response.use(undefined, async (error: AxiosError<ApiError>) => {
  const cfg = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
  if (error.response?.status === 401 && !cfg._retried && !cfg.url?.includes('/auth/refresh')) {
    cfg._retried = true;
    try {
      refreshing ??= refreshSession().finally(() => { refreshing = null; });
      await refreshing;
      return api(cfg);                                   // replay request เดิม (cookie ใหม่ติดไปเอง)
    } catch {
      redirectToLogin();                                 // refresh fail → กลับหน้า login ของ BFF
    }
  }
  return Promise.reject(error);
});

/** ดึงข้อความ error ไทยจาก BE — FE ห้ามแต่งเอง */
export const apiErrorMessage = (e: unknown): string =>
  (axios.isAxiosError<ApiError>(e) && e.response?.data?.message) || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง';
```

### 5.3 RequireAuth / RequirePermission (สิทธิ์ต่อ URL — แทน RequireRole เดิม)
```tsx
// ⚠️ portal เดิม bootstrap session (users/current + menus + permissions) ให้แล้วที่ layout ของโซน (main)
//    โมดูล SBPGI จึง "ไม่ต้อง" เขียน RequireAuth ใหม่ — ใช้ของ portal · เหลือแค่ guard สิทธิ์ต่อ URL ในหน้า

// src/components/sbpgi/RequirePermission.tsx — guard ต่อ URL ตาม canView ของระบบเดิม
'use client';
import { usePathname } from 'next/navigation';
import { usePermissionStore } from '@/stores/permissionStore';
import { AccessDenied } from '@/components/Permission/AccessDenied';

export function RequirePermission({ children }: { children: React.ReactNode }) {
  const hasPermission = usePermissionStore(s => s.hasPermission);
  const pathname = usePathname();
  return hasPermission(pathname, 'canView') ? <>{children}</> : <AccessDenied />;
}

// ใช้ในแต่ละหน้า: export default function Page(){ return <RequirePermission><WaitingList/></RequirePermission>; }
// หมายเหตุ static export: middleware ไม่ทำงานบน S3 → guard ต้องอยู่ฝั่ง client แบบนี้ (เหมือนหน้าอื่นของ portal)
```
ใช้ในแต่ละ `page.tsx` ของโมดูล: ครอบด้วย `<RequirePermission>` — ปุ่ม/การกระทำในหน้าเช็ค `hasPermission(url,'canManage'|'canExport')` เพิ่มตามจุด (คอลัมน์สิทธิ์ role ใน §4 เป็น mapping อ้างอิงตอนตั้งค่า group ในระบบเดิม)

## 6. ชั้น API + query keys

- hook ต่อกลุ่มอยู่ `features/*/api/` (เช่น `features/documents/api/useDocument.ts`) — เรียกผ่าน `api` instance กลางเสมอ
- ทุก mutation สำเร็จ → `invalidateQueries` ด้วย key จาก factory + `toast(msg,'ok')`
- Error ทุกเส้นรูปแบบ `{code, message}` — แสดง `message` ผ่าน `apiErrorMessage()` ตรง ๆ
- pagination: ส่ง `?page&size` รับ `{page,size,total,items}` → ผูกกับ `<Pager>`
- วันที่จาก API = ISO + ค.ศ. → แปลงแสดง **พ.ศ.** ที่ `formatDateThai()` จุดเดียว

### 6.1 `shared/api/query-keys.ts` (factory ครบ 6 กลุ่มตาม api.md + ชุด auth ของระบบเดิม)
```ts
export const authKeys = {                 // เส้นของระบบเดิมผ่าน BFF (ไม่ใช่ SBPGI)
  profile: ['auth', 'profile'] as const,          // GET /users/current
  menus: ['auth', 'menus'] as const,              // GET /menus
  permissions: ['auth', 'permissions'] as const,  // GET /groups/current-user/permissions
};
export const taskKeys = {
  all: ['tasks'] as const,
  list: (params: Record<string, unknown>) => ['tasks', 'list', params] as const,
};
export const documentKeys = {
  all: ['documents'] as const,
  list: (params: Record<string, unknown>) => ['documents', 'list', params] as const,
  detail: (docNo: string) => ['documents', 'detail', docNo] as const,
  timeline: (docNo: string) => ['documents', 'timeline', docNo] as const,
  sales: (docNo: string) => ['documents', 'sales', docNo] as const,
};
export const lookupKeys = {
  stores: (q: string, type: 'impacted' | 'new') => ['lookup', 'stores', type, q] as const,
  competitors: ['lookup', 'competitors'] as const,
  docStatuses: ['lookup', 'document-statuses'] as const,
  sections: ['lookup', 'workflow-sections'] as const,
};
export const masterKeys = {
  factors: ['masters', 'factors'] as const,
  auditLogs: (table: string) => ['masters', 'audit-logs', table] as const,
  // operators/employees/roles/menus/menuPermissions ตัดออก — ใช้ระบบ SBP เดิม (2026-08-05)
};
// configKeys / emailKeys / jobKeys ตัดออก 2026-08-06 — ลบหน้า Global Config + Email Template ทั้งฟีเจอร์
// และตัด API ของ Batch Job (ไม่มี endpoint /configs · /email-templates · /jobs แล้ว)
export const reportKeys = {
  statusSummary: (params: Record<string, unknown>) => ['reports', 'status-summary', params] as const,
};
```
กติกา: **ห้าม**พิมพ์ array key มือเปล่าในไฟล์ hook — import จาก factory เท่านั้น (grep `useQuery({ queryKey: ['` ต้องไม่เจอ)

## 7. ค่าคงที่ธุรกิจ — `shared/lib/constants.ts` (เต็ม)

```ts
/* workflow 5 ขั้น — SDD v7.5 ตัดขั้นบัญชี 04/05 ออกแล้ว ห้ามอ้างถึง */
export const SECTIONS = [
  { code: '06', name: 'ฝ่าย SBP DSA' },
  { code: '08', name: 'เจ้าหน้าที่ SBP DSA' },
  { code: '01', name: 'หน่วยงานส่งเสริมธุรกิจ SBP' },   // SDD GI: เดิม "ฝ่ายส่งเสริมธุรกิจ SBP" — ผู้ใช้งานขั้นนี้คือ ผู้จัดการฝ่าย/ผู้เชี่ยวชาญ + เจ้าหน้าที่อาวุโส (ยกเว้น GM) · ชื่อสถานะเปลี่ยนตามเป็น "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ" (2026-08-06)
  { code: '02', name: 'GM ส่งเสริมธุรกิจ SBP' },
  { code: '03', name: 'ผู้บริหารสำนักบริหาร SBP (AVP)' },
] as const;

/* สถานะเอกสาร 6 ค่า — string เต็ม verbatim ห้ามแก้แม้แต่วรรค · ขั้น 01 ใช้ "รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ" ตามการเปลี่ยนคำเรียกทั้งระบบ (2026-08-06) */
export const DOC_STATUSES = [
  'รอฝ่าย SBP DSA ดำเนินการ',            // section 06
  'รอเจ้าหน้าที่ SBP DSA ดำเนินการ',      // section 08
  'รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ',   // section 01
  'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ',   // section 02
  'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', // section 03
  'เสร็จสิ้นดำเนินการ',                   // จบ
] as const;
export type DocStatus = (typeof DOC_STATUSES)[number];

/* map สถานะ → variant ของ <Pill> (สีตาม prototype) */
export const STATUS_PILL: Record<DocStatus, string> = {
  'รอฝ่าย SBP DSA ดำเนินการ': 'wait',
  'รอเจ้าหน้าที่ SBP DSA ดำเนินการ': 'violet',
  'รอหน่วยงานส่งเสริมธุรกิจ SBP ดำเนินการ': 'info',
  'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ': 'orange',
  'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ': 'navy',
  'เสร็จสิ้นดำเนินการ': 'ok',
};

/* วงเงินอนุมัติ (SDD GI 24/02/2026 — แทน AVP_THRESHOLD 100_000 เดิม) — ใช้แสดงป้ายเท่านั้น routing อยู่ BE */
export const GM_APPROVE_LIMIT = 50_000;   // ≤50,000 → จบที่ GM(02)
export const AVP_APPROVE_LIMIT = 300_000; // 50,001–300,000 → ผ่าน AVP(03) แล้วจบ · เกิน 300,000 รอ confirm (SDD ยังไม่ระบุเส้นทาง)

/* ภาค 8 ค่า (ตัวกรองเอกสาร) — มี RC ไม่มี RW */
/* ภาค 13 รหัส (SDD v7.5) — ค่าเริ่มต้นสำหรับ fallback เท่านั้น · runtime ต้องโหลดจาก GET /store/all-regions (ระบบ SBP เดิม) เพราะภาคใหม่เพิ่มได้เอง */
export const REGIONS = ['BE', 'BS', 'NEU', 'REU', 'RSU', 'BG', 'BW', 'RC', 'RN', 'BN', 'NEL', 'REL', 'RSL'] as const;

/* ภาค 13 รหัสของหน้ารายงาน (checkbox ตาม k2-report.html — ลำดับตามหน้าจอ) */
export const REPORT_REGIONS13 = [
  'BE', 'BS', 'NEU', 'REU', 'RSU', 'BG', 'BW', 'RC', 'RN', 'BN', 'NEL', 'REL', 'RSL',
] as const;

/* เงื่อนไขค้นหา 4 ค่า (multi-select ในตัวกรอง) — คนละชุดกับประเภทร้าน 8 ค่าในฟอร์มสร้างเอกสาร */
export const SEARCH_STORE_TYPES = ['FR Type A', 'FR Type B', 'FR Type C', 'พนักงาน'] as const;

/* ประเภทร้าน 8 ตัวเลือกในฟอร์ม k2-create */
export const CREATE_STORE_TYPES = ['FR Type A', 'FR Type B', 'FR Type C', 'FR Type C r', 'บริษัท', 'พนักงาน', 'PTT', 'BGC'] as const;

export const MAX_FILE_MB = 5;
export const ATTACH_EXTS = [
  'vsd','dwg','afp','pdf','mda','zip','wav','mp3','gif','jpg','tif','tiff','htm','html',
  'txt','xml','mpg','mov','ivs','doc','docx','xls','xlsx','pps','ppt','pot','csv',
] as const;

/* ข้อความ verbatim จาก SRS/prototype — ห้ามแก้แม้แต่วรรค */
export const MSG = {
  NO_DECISION: 'ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ',
  EMPTY_TABLE: 'ไม่พบรายการตามเงื่อนไขที่กรอง',
  FLAG_RED_NOTE: 'แดง = ยอดขายไม่ครบ 60 วัน',
  // AUDIT_REASON_LABEL — **ตัดออก 2026-08-07** พร้อมตาราง `audit_logs` (22 → 21 ตาราง) · mutation master ไม่ต้องส่ง `reason` อีกต่อไป
  // (การเอา audit ของ master กลับมาโดยใช้ของระบบเดิม `user_log`/`user_audit_events`/`common_log` ยังไม่ตัดสิน — DP-12 ใน SBP/SBPGI-vs-existing-system.md)
  /* ข้อความ popup อื่น ๆ คัดจากหน้า html เดิม + RDM-SRS-…-รายการหน้าจอ.md ตอน implement หน้านั้น */
} as const;
```

### 7.1 `shared/lib/format.ts`
```ts
/** ISO ค.ศ. → แสดง พ.ศ. เช่น '2026-01-15' → '15/01/2026' — จุดเดียวทั้งแอป */
export function formatDateThai(iso: string | null | undefined): string {
  if (!iso) return '-';
  const d = new Date(iso);
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `${dd}/${mm}/${d.getFullYear() + 543}`;
}

/** คั่นหลักพัน ทศนิยม 2 เช่น 1234567 → '1,234,567.00' */
export function formatMoney(n: number | null | undefined): string {
  if (n == null) return '-';
  return n.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** เลขเอกสาร YYYY/xxxxx ปี พ.ศ. เช่น (2569, 123) → '2026/00123' */
export function formatDocNo(yearBE: number, running: number): string {
  return `${yearBE}/${String(running).padStart(5, '0')}`;
}
```

FE ต้อง enforce (BE ตรวจซ้ำ):
- ปุ่ม **ส่งดำเนินการ**: ไม่เลือกผลพิจารณา → popup `MSG.NO_DECISION` · เลือก "ไม่ชดเชย"/"หยุดชดเชย" → ช่องความคิดเห็น required · ปุ่ม **บันทึก** ไม่ validate (draft ได้เสมอ)
- **%ชดเชยรวมทุกร้านเปิดใหม่ = 100%** ก่อนยิง `PUT /documents/{docNo}`
- แถวข้อมูล `<60 วัน` → class `flag-red`
- ค้นหาเอกสาร (related) / รายงาน: **ปี พ.ศ. เป็น required** — ไม่เลือก = ไม่ยิง API
- ไฟล์แนบ: เช็ค ext ∈ `ATTACH_EXTS` + ขนาด ≤ 5MB ก่อน upload — ผิด = toast error ไม่ยิง API

## 8. DTO types หลัก — `shared/types/dto.ts` (สัญญาตรง api.md)

```ts
/* ---- ห่อทุก list endpoint ---- */
export interface PagedResponse<T> { page: number; size: number; total: number; items: T[] }

/* ---- Auth (ของระบบ SBP เดิมผ่าน BFF — ตัดสินใจ 2026-08-05 · ไม่มี LoginResponse/token ฝั่ง FE) ---- */
export interface UserProfile {                       // GET /users/current — shape ตาม auth-backend ระบบเดิม
  employeeId: string; fullName: string; email: string;
  group: { id: string; name: string };               // group ระบบเดิม (map 8 role SRS ตอนตั้งค่า)
  sectionCode?: '06' | '08' | '01' | '02' | '03';    // ขั้น workflow ของผู้ใช้ (ถ้ามีบทบาทพิจารณา — SBPGI ผูกจาก group/HR)
}
export interface MenuItem { url: string; label: string; sortOrder: number; parentUrl?: string }  // GET /menus (BFF)
export interface PermissionEntry {                   // GET /groups/current-user/permissions — สิทธิ์ต่อ URL
  url: string; canView: boolean; canManage: boolean; canExport: boolean; canOther: boolean;
}

/* ---- Tasks / Documents ---- */
export interface TaskItem {
  docNo: string;                    // '2026/00123'
  roundNo: number;                  // ครั้งที่
  impactedStoreCode: string; impactedStoreName: string;
  regionCode: string;               // REGIONS
  salesDeclinePercent: number;      // ยอดขายที่ลดลง (%)
  totalCompensationAmount: number;  // จำนวนเงินที่ชดเชย (บาท)
  status: DocStatus;                // 1 ใน 6 ค่า verbatim
  daysPending: number;              // รอ (วัน)
  salesDataDays: number;            // < 60 วัน → tr.flag-red (internal red-flag)
  createdAt: string;                // ISO ค.ศ.
}

export interface DocumentDetail {
  docNo: string; round: number; impactMonth: string; status: DocStatus; createdAt: string;
  impactedStore: {
    storeCode: string; storeName: string; region: string; storeType: string;
    owner: string; juristic: string; spTransferDate: string;
  };
  operatorName: string;
  salesDropPct: number; latestCompensation: number;
  newStores: NewStoreRow[];
  competitors: CompetitorRow[];
  externalFactors: FactorRow[];
  attachments: AttachmentRow[];
  compensationHistory: CompensationHistoryRow[];
  /* ---- ธงสิทธิ์จาก BE — FE render ตามนี้ ห้ามเดา role เอง ---- */
  myRoleView: { sectionCode: string; sectionName: string; stepIndex: number; stepTotal: 5 };
  editableSections: string[];    // เช่น ['newStores','competitors','factors','action']
  resultOptions: { value: string; label: string; commentRequired: boolean }[];  // radio ตามขั้นปัจจุบัน; value = result ไทย verbatim 6-enum
}
export interface NewStoreRow {
  seq: number; storeCode: string; storeName: string; region: string; storeType: string;
  owner: string; juristic: string; openDate: string; closeDate: string | null;
  distanceKm: number; compensationPct: number; compensationAmount: number;
}
export interface CompetitorRow { id: number; name: string; impactOpenDate: string; remark: string; source: 'ALM' | 'USER' }
export interface FactorRow { factorCode: string; factorName: string; startDate: string; endDate: string; remark: string }
export interface AttachmentRow { fileName: string; section: string; uploadedBy: string; remark: string; uploadedAt: string }
export interface CompensationHistoryRow {
  round: number; impactMonth: string; amount: number; accountingMonth: string;
  status: DocStatus; result: string; docNo: string;
}
export interface TimelineEntry { name: string; position: string; result: string; detail: string; at: string }
export interface SalesWindow { label: string; days: { date: string; amount: number }[] }  // 4 หน้าต่าง × 15 วัน
```

types เฉพาะ feature (OperatorRow, FactorMasterRow, RoleRow, ConfigRow, EmailTemplate, JobItem, ReportRow 14 คอลัมน์ (SDD สไลด์ 60) ฯลฯ) ประกาศใน `features/*/types/` ของตัวเอง — field ตรงคอลัมน์ตารางใน REACT-TODO-CHECKLIST.md ของหน้านั้น

## 9. Shared components — spec props ต่อตัว

### 9.1 `<Pill>` / `<Chip>`
```ts
interface PillProps { variant: 'wait'|'violet'|'info'|'orange'|'navy'|'teal'|'muted'|'ok'|'fail'|'del'; children: ReactNode }
interface ChipProps { source?: 'fgi'|'k2'|'new'|'mix'; children: ReactNode }
```
Pill = สถานะ (มีจุดสี) · Chip = ป้ายข้อมูล — **ห้ามใช้สลับ** · `<StatusPill status={docStatus}/>` = wrapper map ผ่าน `STATUS_PILL`

### 9.2 `<DataTable>`
```ts
interface Column<T> {
  key: string; header: string;                      // header = ข้อความ th ตาม prototype verbatim
  render?: (row: T) => ReactNode;
  sortable?: boolean; sortType?: 'text'|'num'|'date';  // แทน data-stype
  align?: 'left'|'right'|'center';
}
interface DataTableProps<T> {
  columns: Column<T>[]; rows: T[];
  rowKey: (r: T) => string;
  onRowClick?: (r: T) => void;
  rowClassName?: (r: T) => string | undefined;      // คืน 'flag-red' เมื่อ row.flagRed
  selectable?: boolean;                             // checkbox column + select-all
  selected?: string[]; onSelectChange?: (keys: string[]) => void;
  actions?: { view?: (r:T)=>void; edit?: (r:T)=>void; del?: (r:T)=>void };  // icon buttons ต่อแถว
  emptyText?: string;                               // default = MSG.EMPTY_TABLE verbatim
}
```
ต้องห่อ `.table-wrap` เสมอ (scroll แนวนอน — body ห้าม scroll แนวนอน)

### 9.3 `<Pager>`
```ts
interface PagerProps {
  page: number; size: number; total: number; filteredFrom?: number;  // แสดง "(กรองจาก M)"
  sizeOptions?: number[];        // default [10,20,50,100] + suffix ' / หน้า'
  onChange: (page: number, size: number) => void;   // มีปุ่ม ‹ › + เลขหน้า + … + "ไปหน้า" goto input
}
```
info text: `แสดง X–Y จาก N รายการ` (+`(กรองจาก M)` ถ้ามี filter)

### 9.4 `<EntityModal>` (schema-driven — แทน SCHEMAS/data-entity ของ sbp.js)
```ts
interface EntityField {
  name: string; label: string;                       // label = header คอลัมน์ตรงตัว
  type: 'text'|'email'|'select'|'textarea'|'date'|'month'|'number'|'readonly';
  options?: { value: string; label: string }[];
  required?: boolean;
  visibleWhen?: (values: Record<string, unknown>) => boolean;  // ช่องโผล่ตามค่า field อื่น (เช่น ช่องที่ขึ้นกับค่าที่เลือกในฟอร์ม master)
  lockedOnEdit?: boolean;                            // เช่น factor_code แก้ไม่ได้ตอน edit
}
interface EntityModalProps {
  mode: 'view'|'edit'|'add';
  title: string; fields: EntityField[];
  initialValues?: Record<string, unknown>;
  // requireReason — **ตัดออก 2026-08-07** พร้อม `audit_logs` · master mutation ไม่มีช่องเหตุผลแล้ว (DP-12 ยังไม่ตัดสินว่าจะเอา audit กลับมา)
  onSubmit: (values: Record<string, unknown>) => Promise<void>;
  onClose: () => void;
}
```
คู่กับ `<ConfirmDeleteDialog message onConfirm onClose>` (ลบต้องมี reason ด้วยสำหรับ master)

### 9.5 Charts (`shared/charts/` — SVG ล้วน)
```ts
interface DonutChartProps { values: number[]; labels: string[]; colors: string[]; center?: string }  // เลขกลาง + legend
interface BarChartProps { values: number[]; labels: string[]; color?: string }
interface SparkChartProps { values: number[]; color?: string }
interface HBarChartProps {                            // แนวนอน + dot สถานะ + tooltip (ยังไม่มีผู้ใช้หลังถอดกราฟ 2026-08-06)
  rows: { label: string; value: number; dotColor?: string }[];
  color?: string; formatValue?: (v: number) => string;
  tip?: (row) => string;                              // HTML tooltip — <ChartTooltip> fixed กันหลุด viewport
}
interface ColumnChartProps { values: number[]; labels: string[]; lastLabelOnly?: boolean }  // รายเดือน มุมโค้ง
```

### 9.6 อื่น ๆ
- `<Tabs tabs={[{key,label}]} active onChange>` + render pane ตาม key
- `<StatCard icon value label variant clickable active onClick>` + `<StatGrid>`
- `<InfoCard>` / `<NoticeCard>` (callout ขอบซ้ายน้ำเงิน + ไอคอน) · `<FlowLegend>`
- `<AuditHistoryTable rows>` — 6 คอลัมน์มาตรฐาน `วันที่แก้ไข | ผู้แก้ไข | คำสั่ง | รายการ | ข้อมูลเดิม → ข้อมูลใหม่ | เหตุผลการแก้ไข` · คำสั่ง = pill (`แก้ไข`=info / `เพิ่ม`=ok / `ลบ`/`รีเซ็ต`=fail) · เรียงล่าสุดก่อน — ใช้ทุกหน้า master/admin ผูก `GET /audit-logs?table=<ชื่อตาราง>`
- `<PageSkeleton>` (ระหว่าง lazy load) · `<WarningPopup>` (popup เตือน SRS เช่น MSG.NO_DECISION)
- `useToast()` จาก ToastProvider — kind `ok`/`del`/default หน้าตา/ตำแหน่งเหมือน `#toast-stack` เดิม

## 10. เมนู — **ไม่มี MODULES registry ใน FE** (ใช้เมนู/สิทธิ์ของ portal เดิม)

> sidebar ของ portal render จาก `GET /menus` + `GET /groups/current-user/permissions` — การเพิ่มเมนู SBPGI ทำที่ **auth-backend (หน้า `/setting/manage-user-rights`)** ไม่ใช่แก้โค้ด FE
> ตารางด้านล่างเป็น **สเปกรายการเมนูที่ต้องไปตั้งค่าในระบบเดิม** (label + URL + สิทธิ์) ไม่ใช่ไฟล์ที่ต้องสร้าง

พอร์ตจาก `assets/sbp.js` (~บรรทัด 52) เฉพาะกลุ่มแอปจริง (กลุ่ม Flow/Database/Plan ไม่พอร์ต):

```ts
import { isFeatureEnabled } from '@/shared/lib/env';

export interface ModuleEntry {
  key: string;                 // match กับเมนู (url) จากผล GET /menus ของ BFF ระบบเดิม
  label: string; icon: string; group: string;
  route?: string;
  children?: { key: string; label: string; route: string }[];
}

export const MODULES: ModuleEntry[] = [
  { key: 'home',           label: 'Overview',              route: '/',                      icon: 'home',      group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'k2-create',      label: 'สร้างเอกสาร',           route: '/documents/create',      icon: 'plus',      group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'k2-docs',        label: 'เอกสาร',                icon: 'badge',                   group: 'ระบบประกันรายได้ (SBP Mall)',
    children: [
      { key: 'k2-list-waiting', label: 'รอดำเนินการ',  route: '/documents/waiting' },
      { key: 'k2-list-related', label: 'ที่เกี่ยวข้อง', route: '/documents/related' },
      ...(isFeatureEnabled('abnormal')
        ? [{ key: 'k2-list-abnormal', label: 'ข้อมูลผิดปกติ', route: '/documents/abnormal' }]
        : []),
    ] },
  { key: 'k2-report',      label: 'รายงานสรุปสถานะ',       route: '/reports/income-audit',  icon: 'statement', group: 'ระบบประกันรายได้ (SBP Mall)' },
  // k2-operators (กำหนดผู้ปฏิบัติงาน) และ k2-permissions (สิทธิ์การเข้าถึงเมนู) ตัดออก — ใช้ระบบ SBP เดิม (/setting/manage-user-rights · ตัดสินใจ 2026-08-05)
  { key: 'k2-factors',     label: 'กำหนดปัจจัยภายนอก',     route: '/masters/factors',       icon: 'db',        group: 'ระบบประกันรายได้ (SBP Mall)' },
  // system-config (Global Config) และ email-template ลบทั้งฟีเจอร์ · job-batch ย้ายไปกลุ่ม Flow — ไม่มีกลุ่ม Admin ในเมนู (2026-08-06)
];
```

Sidebar render: group ตามลำดับ first-appearance · **filter รายการด้วยเมนูจากผล `GET /menus` ของ BFF ระบบเดิม + เช็ค `canView` ต่อ URL** (MODULES เป็น meta เท่านั้น — เมนูที่ API ไม่ส่งมา = ไม่แสดง) · active-item: exact route match → key ตรง → same path prefix · submenu "เอกสาร" พับได้ · Breadcrumb: `Home › SBP Management System › <label ของ route>` (leaf จาก meta ของ route แทน `data-crumb`)

## 11. Spec ต่อหน้า (ครบ 11 route — ตัด /login, operators, permissions ออกแล้ว)

> คอลัมน์/ป้าย verbatim เต็ม ๆ ดู REACT-TODO-CHECKLIST.md ต่อหน้า — ที่นี่สรุป endpoint + ฟอร์ม/validation + mutation + เงื่อนไข role ให้ครบพอสร้างได้

### 11.1 Auth bootstrap — **ไม่มีหน้า login ของตัวเอง** (ตัดสินใจ 2026-08-05)
- ไม่มี LoginPage/ฟอร์ม username-password — ผู้ใช้ไม่มี session → `redirectToLogin()` พาไป `{bffUrl}/auth/login?redirectUrl=<origin>` (Cognito ผ่าน BFF ระบบเดิม) แล้วเด้งกลับพร้อม httpOnly cookie
- หลังกลับมา `<RequireAuth>` bootstrap: `GET /users/current` + `GET /menus` + `GET /groups/current-user/permissions` → เก็บใน stores (§5.1) → เข้าแอป
- ระหว่างโหลด/refresh แสดง `<PageSkeleton>` — 401/refresh fail → redirect BFF login (ไม่ crash)

### 11.2 `/` — **ไม่มี HomePage/Overview แล้ว (2026-08-06)**
- `index.html` เหลือเป็น redirect stub เท่านั้น — **landing page คือ `เอกสาร → รอดำเนินการ` (`/documents/waiting`)**
- `GET /dashboard/summary` และ `dashboardKeys` **ตัดออกถาวร** พร้อมกับการถอด stat cards ทั้งหมด · route `/` ให้ `redirect('/sbpgi/documents/waiting')` ฝั่ง Next.js

### 11.3 `/documents/waiting` + `/documents/related` — DocListPage (1 component 2 mode)
- mode `waiting` → `GET /tasks` (`taskKeys.list(params)`) — inbox เฉพาะสถานะของ role ตัวเอง · mode `related` → `GET /documents` (`documentKeys.list`)
- **related: ปี พ.ศ. required** — ไม่เลือกแล้วกดค้นหา → error ใต้ช่องปี + **ไม่ยิง API** (enabled: false)
- FilterBar: ปี* (dropdown พ.ศ.) · เดือน · สถานะ (select `DOC_STATUSES` — **ซ่อนใน waiting**) · ภาค (`REGIONS` multi (13 รหัส · โหลดจาก GET /store/all-regions ของระบบ SBP เดิม)) · ประเภทร้าน (`SEARCH_STORE_TYPES` multi) · รหัส/ชื่อร้าน · เลขเอกสาร · ยอดขายลดลง% / เงินชดเชย / รอ(วัน) (RangeInput min–max) · ปุ่ม `ล้างตัวกรอง`
- Stat cards คลิกกรองตาราง: waiting 4 ใบ (ทั้งหมด / flag60 / รอเกิน 3 วัน / วงเงิน >50,000 เข้า AVP — วงเงินใหม่ SDD GI) · related = ทั้งหมด + ต่อสถานะ
- ตาราง: `ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง(%) | จำนวนเงินที่ชดเชย | สถานะ(pill) | รอ (วัน)` — sortable, `rowClassName` = flag-red, คลิกแถว → `/documents/:docNo`
- **งานค้าง mode waiting (SDD GI 24/02/2026)**: ต้องมี FilterBar (ข้างบน) + **checkbox เลือกหลายเอกสาร** (`selectable` ของ `<DataTable>` + select-all) + ปุ่ม bulk action → **popup ยืนยันก่อนดำเนินการ** · เอกสารที่ 06 ลง "เห็นควรไม่ชดเชย" เดือนก่อน BE จะ auto-queue เข้า inbox เดือนถัดไปให้**เจ้าของงานคนเดิม** — FE แค่แสดงจาก `GET /tasks` ไม่คำนวณเอง
- **สิทธิ์การมองเห็น (SDD GI)**: เจ้าหน้าที่/ฝ่าย SBP DSA เห็นเอกสารได้**ทุกสาขา** (ไม่จำกัดเฉพาะงานตน) — BE เป็นคนกรอง, FE ไม่ filter เพิ่ม · ทีมส่งเสริม/บัญชีตามสิทธิ์เดิม
- `<Pager>` ผูก `?page&size` ↔ `PagedResponse<TaskItem>` + NoticeCard `แดง = ยอดขายไม่ครบ 60 วัน …`
- mutation: เฉพาะ bulk action ของ waiting (ผ่าน endpoint action ตามชนิดงาน) — นอกนั้นไม่มี

### 11.4 `/documents/create` — CreateDocPage (k2-create.html)
- S1 pill `เลขที่เอกสารถัดไป · <จาก API>` · Tabs 2 แท็บ
- **Tab `สร้างเอกสารใหม่ (นอกเงื่อนไข)`** — ฟิลด์: `รหัสร้านถูกกระทบ*` (`StoreSearchInput` → `GET /store/search` (ระบบ SBP เดิม)) · `ชื่อร้านถูกกระทบ` (readonly auto) · `ภาค` (readonly) · `ประเภทร้าน` (select `CREATE_STORE_TYPES` 8 ค่า) · `วันที่โอนเป็นร้าน SP` (date) · `เดือน/ปีที่ถูกกระทบ*` (month) · `ครั้งที่` · `รหัสร้านเปิดใหม่*` (search `type=new`) · `เหตุผลการสร้างเอกสารนอกเงื่อนไข*` (textarea) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` / `สร้างเอกสาร`
- zod: ช่อง `*` ทั้งหมด required — message ไทยตามหน้าเดิม
- mutation: `POST /documents` → toast เลขเอกสาร `YYYY/xxxxx` → invalidate `documentKeys.all`+`taskKeys.all` → navigate ไปเอกสาร
- **Tab `สร้างเอกสารที่ FS`**: `รหัสร้านถูกกระทบ*` · `ชื่อร้าน` (readonly) · `เดือน/ปีที่ถูกกระทบ*` · `Period Statement (From–To)` · ปุ่ม `เคลียร์` / `ส่งสร้างที่ FS` → `POST /documents` (mode FS) + `<PendingStatementTable>` "เอกสารที่รอ SBP Statement ส่งกลับ": `รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ` (pill รอ/ส่งกลับแล้ว)
- **เปิดเรื่องซ้ำได้ (SDD GI)**: `POST /documents` ตอบ 409 เฉพาะกรณีมีเอกสาร **active** ของร้าน+เดือนนั้น — เอกสารเดิมที่จบด้วย "หยุดชดเชย/เห็นควรไม่ชดเชย" สร้างใหม่ทับได้ (ทั้งเดือนเดียวกันและเดือนถัดไป · ไม่ต้องเปิด SR) — FE แสดง `message` จาก 409 ตรง ๆ ไม่ block ล่วงหน้า
- สิทธิ์: role อ้างอิง 00/01/02 — guard จริงคือ `canView`/`canManage` ต่อ URL จากระบบเดิม

### 11.5 `/documents/:docNo` — DocumentPage ⭐ (k2-document.html — ซับซ้อนสุด)
- โหลด `GET /documents/{docNo}` (`documentKeys.detail`) ครั้งเดียว → ได้ `myRoleView` + `editableSections` + `resultOptions` — **render 12 ส่วนตามธงจาก BE ไม่เดา role เอง** (แทนกลไก `data-editrole`/`data-roleonly`/`.edit-only` ของ prototype)
  > ⚠️ **ข้อค้างตัดสินใจ — ที่มาของธง `editableSections` ยังไม่สรุป:** workflow engine `@srm/glb-workflow` มีตาราง **`workflow_part` + `workflow_part_display`** (schema `sps_store`) ที่คุม **READ/WRITE รายส่วนของหน้าจอต่อ state อยู่แล้ว** (`workflow_part_display` มี 12 ส่วน) ซึ่ง**ทับซ้อน**กับกลไกสิทธิ์แก้ไขที่ prototype ทำเอง (`data-editrole`/`.edit-only`) และกับธงที่ SBPGI จะคำนวณเอง · **ยังไม่ตัดสิน**ว่าจะให้ธงมาจาก engine หรือ SBPGI คำนวณเอง — **ยังไม่เปลี่ยนดีไซน์ ทำตามสเปกนี้ไปก่อน** · ข้อมูลประกอบ: wrapper ของระบบเดิม register entity แค่ 10 ตัว ยังไม่รวม `WorkflowPart`/`WorkflowPartDisplay` จึงใช้ทันทีไม่ได้ · ดู `SBP/SBPGI-vs-existing-system.md` §3.1 + หัวข้อ 4 (Decision Points)
- S2 head: `เอกสารข้อมูลร้านถูกกระทบ <docNo>` + `<StatusPill>` + ปุ่ม `พิมพ์` (window.print) · `<WorkflowStepper>` 5 ขั้น `06›08›01›02›03` + pill `ขั้นตอนที่ N/5`
- S3 `<DocMetaGrid>`: รอบ/ครั้งที่/เดือน, สถานะ, เลขที่, วันที่สร้าง (พ.ศ.), รหัส/ชื่อร้าน, ภาค, ประเภท, เจ้าของ, นิติบุคคล, วันที่โอน, ผู้ดำเนินการ, ยอดขายลดลง %, ชดเชยล่าสุด, ไฟล์แนบ + ปุ่ม `ข้อมูลยอดขายเพิ่มเติม`
- ~~S4 กราฟยอดขาย~~ **ถอดออก 2026-08-06** — หน้าเอกสารไม่มีกราฟแล้ว · `GET /documents/{docNo}/sales` (`documentKeys.sales`) คงไว้เป็นข้อมูลประกอบ และมีปุ่ม `ข้อมูลยอดขายเพิ่มเติม` ลิงก์ออก QlikView BI
- S5 `<NewStoresTable>` (แก้ได้เมื่อ `'newStores' ∈ editableSections`): คอลัมน์ 12 ตาม checklist · `%ชดเชย` เป็น input · แสดงสด `เงินชดเชย = ยอดตั้งต้น × %/100` · ปุ่ม `รีเฟรช`/`คืนค่าก่อนแก้ไข`/`คำนวณเงินชดเชย` — **%รวม ≠ 100 → `<WarningPopup>` (ข้อความ verbatim จากหน้าเดิม) และไม่ยิง PUT** · %รวม = 100 → `PUT /documents/{docNo}` → invalidate detail + toast ok
- S6 `<AllMapPoi>` SVG (วงรัศมี, pulse, หมุดร้านใหม่, คู่แข่ง, legend) + ปุ่ม `Link To ALLMAP`
- S7 คู่แข่ง (editable ตามธง): dropdown จาก `GET /competitors` · ป้ายที่มา ALM/USER · เพิ่ม/แก้/ลบ ผ่าน `<EntityModal>` → `PUT /documents/{docNo}`
- S8 ปัจจัยอื่นๆ: dropdown จาก `GET /factors` · โครงเดียวกับ S7
- S9 `<AttachmentsTable>` + ปุ่ม `แนบไฟล์` → validate ext+5MB ฝั่ง FE ก่อน → `POST /documents/{docNo}/attachments` (multipart) → invalidate detail
- S10 `<CompensationCalcPanel>` readonly (ยอดตั้งต้น / %รวม / รวมร้านใหม่ / อำนาจอนุมัติ `≤50,000 GM · 50,001–300,000 AVP` — เกิน 300,000 รอ confirm · SDD GI) — **แสดงเฉพาะ view section 08 ตามธง API**
- S11 `<CompensationHistoryTable>` (คลิก → เปิดเอกสารครั้งนั้น) · S12 `<DecisionHistoryTable>` + modal — จาก `GET /documents/{docNo}/timeline`
- S13 `<DecisionPanel>`: radio จาก `resultOptions` + textarea `ความคิดเห็นเพิ่มเติม` + ปุ่ม `แนบรูป`/`บันทึก`/`ส่งดำเนินการ`
  - ตัวเลือก "ส่งฝ่ายส่งเสริมธุรกิจ SBP" **เปลี่ยนชื่อเป็น "ส่งหน่วยงานส่งเสริมธุรกิจ SBP"** (SDD GI — label มาจาก `resultOptions` ของ BE, FE ห้าม hardcode ชื่อเก่า)
  - `ส่งดำเนินการ` ไม่เลือกผล → popup `MSG.NO_DECISION` — ไม่ยิง API
  - เลือกตัวเลือกที่ `commentRequired` (ไม่ชดเชย/หยุดชดเชย) แต่ comment ว่าง → popup เตือน — ไม่ยิง API
  - `บันทึก` → ไม่ validate, save draft ได้เสมอ
  - ผ่าน → `POST /documents/{docNo}/actions` `{result, comment}` — **routing อยู่ BE ทั้งหมด (SDD GI)**: วงเงิน GM 50,000 / AVP 300,000 (เกิน 300,000 รอ confirm) · เห็นควรไม่ชดเชยที่ขั้น 01/02 → เสร็จสิ้นทันที (ไม่ตีกลับ 06 · ขั้น 03 คงเดิม รอ confirm) · ยอดชดเชย 0: เดือน 1–3 ผู้ใช้กด "ส่งหน่วยงานส่งเสริมธุรกิจ SBP" ต่อ, เดือนที่ 4 กด "หยุดชดเชยรายได้" (BE ช่วย validate) → toast ok + invalidate detail+timeline+`taskKeys.all` → สถานะ/stepper ขยับ

### 11.6 `/reports/income-audit` — ReportPage (k2-report.html, SRS 3.1.7 + SDD v7.5)
- ฟอร์ม `<ReportSearchForm>` (**7 ตัวกรองตาม SDD สไลด์ 60** · เรียง: สถานะ\*|รหัสร้านถูกกระทบ · รหัสร้านเปิดกระทบ|ประเภทร้าน · Period Statement From–To เต็มแถว · ภาคเต็มแถว · ผลการพิจารณาเต็มแถว): ปี\* · **สถานะ\* (select `DOC_STATUSES` — Required Field ตัวเดียวของหน้านี้)** · รหัสร้านถูกกระทบ (numeric) · รหัสร้านเปิดกระทบ (numeric · **ระบุร้านถูกกระทบแล้วต้องระบุร้านเปิดกระทบด้วย** ไม่งั้น 400) · ประเภทร้าน (checkbox **A/B/C/E**) · **Period Statement From–To** (`DateRangeInput` เต็มแถว · `input[type=date]` ปฏิทิน **วัน/เดือน/ปี ค.ศ.** · บังคับเมื่อสถานะ = เสร็จสิ้นดำเนินการ) · ภาค (checkbox `REPORT_REGIONS13` — **ภาคใหม่ที่เพิ่มในระบบต้องแสดงเป็น checkbox อัตโนมัติ**: render จาก lookup API ไม่ hardcode 13 ค่าใน UI · SDD GI/v7.5) · **radio ผลการพิจารณา (ไม่บังคับ): `ประกันรายได้` / `ไม่ประกันรายได้`** · ปุ่ม `เคลียร์ค่าเริ่มใหม่` / `ค้นหาข้อมูล` / `Export Excel` · **คอนโทรลทุกชนิดสูง 46px เท่ากัน** · **ตารางผล sort ได้ทุกคอลัมน์** (ตัดฟิลด์ ชื่อร้านที่ถูกกระทบ + เดือน/ปีที่ถูกกระทบ From–To ออก 2026-08-06 — ไม่มีใน SDD)
- ไม่เลือกปี → error + ไม่ยิง API (กฎเดียวกับ related)
- **`periodStatement` บังคับเมื่อสถานะ = `เสร็จสิ้นดำเนินการ`** (SDD GI) — zod refine: status เป็นเสร็จสิ้นฯ แต่ Period Statement ว่าง → error ใต้ช่อง + ไม่ยิง API
- `ค้นหาข้อมูล` → `GET /reports/status-summary` (`reportKeys.statusSummary`) → `<SummaryLine>` (พบ N รายการ / ยอดชดเชยรวม / วงเงิน 50,001–300,000 เข้า AVP / แถวแดง) · **ไม่มีกราฟในหน้ารายงาน (ถอด 2026-08-06)**
- ตารางผล **14 คอลัมน์ ตาม SDD สไลด์ 60** (scroll ใน `.table-wrap`) ตาม checklist · flag-red · เงินคั่นหลักพัน · **วันที่/เดือน-ปี แสดงเป็น ค.ศ.** (ตรงกับตัวอย่างใน SDD และระบบ K2 เดิม) · ประเภทร้าน/ภาคเป็นรหัสสั้น
- ปุ่ม `Export Excel` → `GET /reports/status-summary/export` (query เดียวกับการค้นหา) → ดาวน์โหลด `.xlsx` 14 คอลัมน์

### 11.7 ~~`/masters/operators` — OperatorsPage~~ **ตัดออก — ใช้ระบบ SBP เดิม (ตัดสินใจ 2026-08-05)**
- ไม่พอร์ต `k2-operators.html` (SRS 3.1.8) — กำหนดผู้ปฏิบัติงานทำผ่าน group + scope ของ auth-backend ระบบเดิม (หน้า `/setting/manage-user-rights`) · ผูกผู้อนุมัติรายเอกสารด้วย prepared approvers ของ workflow engine เดิม (`@srm/glb-workflow` — **13 ตาราง บน schema `sps_store`** · ชื่อ function ที่ใช้เรียก **ยังไม่ยืนยัน เอกสาร 3 ชุดขัดกัน** ดู `plan-be.md` §Alignment)
- API ที่เคยอ้าง (`/operators*` · `GET /employees/search`) ถูกตัดจาก api.md แล้ว — ค้นพนักงานใช้ employee backend เดิม
- ข้อจำกัดจาก HR Connect (SDD GI): ผู้รักษาการ (acting) ตั้งเป็นผู้อนุมัติไม่ได้ (ระบบยึดตำแหน่งจริง) · พนักงานลาออกยังต้องเปิด SR แก้ชื่อผู้ดำเนินการ

### 11.8 `/masters/factors` — FactorsPage (k2-factors.html, SRS 3.1.9)
- `GET /factors` · ตาราง `☑ | รหัสปัจจัย | ชื่อปัจจัย | รายละเอียดเพิ่มเติม | Action` + toolbar ค้นหา/`เคลียร์`
- schema: `factor_code` (lockedOnEdit) / `factor_name` / `factor_remark` / เหตุผล — **แก้ได้เฉพาะชื่อ+รายละเอียด**
- รหัสซ้ำ → BE ตอบ error → แสดง `message` ตรง ๆ · mutations CRUD `/factors` `/factors/{code}` → invalidate factors + auditLogs('external_factors')

### 11.9 ~~`/masters/permissions` — PermissionsPage~~ **ตัดออก — ใช้ระบบ SBP เดิม (ตัดสินใจ 2026-08-05)**
- ไม่พอร์ต `k2-permissions.html` (SRS 3.1.1) — สิทธิ์เมนู/กลุ่มผู้ใช้จัดการผ่านหน้า `/setting/manage-user-rights` ของ FE เดิม (auth-backend: `/groups` · `/groups/{id}/permissions` · template — `canView/canManage/canExport/canOther` ต่อ URL)
- 8 role ตาม SRS (00 Default … 10 UserViewer) map เป็น **group** ของระบบเดิมตอนตั้งค่า — ไม่มีตาราง/หน้า RBAC ใน SBPGI
- ฝั่ง SBPGI FE เหลือแค่**ผู้บริโภคสิทธิ์**: `GET /menus` + `GET /groups/current-user/permissions` (ดู §5)

### 11.10–11.12 กลุ่ม `/admin/*` — **ตัดออกทั้งหมด (2026-08-06)**
- `/admin/system-config` (SystemConfigPage) และ `/admin/email-templates` (EmailTemplatesPage) **ลบทั้งฟีเจอร์** พร้อม endpoint 10 เส้น — ค่ากำหนดกลางอยู่ใน `mas_param` และ template อีเมลอยู่ใน `email_template` ของระบบ SBP เดิม ซึ่งมีหน้าจอบริหารจัดการของตัวเองแล้ว · FE ของ SBPGI ไม่มีหน้าจอทั้งสอง
- `/admin/batch-jobs` (BatchJobsPage) **ไม่ทำ** พร้อมตัด endpoint กลุ่ม Batch Job Admin 6 เส้น และตาราง `job_configs`/`job_run_histories` — หน้า `job-batch.html` ย้ายไปกลุ่มเมนู **Flow** ("Flow Batch Job") และเหลือเฉพาะ **Flowchart การทำงาน + Database ที่ใช้** (ตัด 2 tab ควบคุมออก) — เป็นเอกสารอ้างอิงผู้พัฒนา ไม่มีงาน FE/BE ให้ทำใน phase นี้ · batch job ทั้ง 11 entry point ยังรันตามปกติ แต่พารามิเตอร์/ตารางเวลากำหนดใน **backend config** (config file/env ฝั่ง BE) และผลการรันเก็บที่ application log · ถ้าทำ 2 tab ควบคุมใน phase ถัดไปให้กลับมาเปิดทั้ง 3 ส่วน (tab + endpoint + ตาราง) พร้อมกัน
- อีเมลตามสถานะ **ยังส่งเหมือนเดิม** — service ฝั่ง BE อ่าน `email_template` แล้วส่งผ่าน `@gosoft-sbp/email-lib` (log ลง `email_sent`) โดยไม่ต้องมีหน้าจอใน SBPGI

### 11.13 `/documents/abnormal` — AbnormalListPage (k2-list-abnormal.html — **ปิด flag**)
- สร้างครบแต่เปิด/ปิดด้วย `isFeatureEnabled('abnormal')` จุดเดียว (route + เมนู + card หน้าแรก) — flag ปิดแล้วเข้า URL ตรง → redirect `/`
- Stat 4 ใบ (ทั้งหมด/ยังไม่แจกงาน/แจกงานแล้ว/แก้ไขแล้ว — assignment status แยกจากสถานะเอกสาร) · filter (ภาค 8, สาเหตุ 4, สถานะ 3, ผู้รับผิดชอบ)
- ตาราง `☑ | ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ | Action(view+assign)` + flag-red + bulk `แจกงานที่เลือก` + `<AssignJobModal>`
- endpoints (commented ใน api.md): `GET /abnormal-stores` · `POST /abnormal-stores/assign` — สิทธิ์ role 05

## 12. Best practices สากลที่บังคับใช้

- **Testing pyramid**: unit (util/business rule — เยอะสุด) → component (Testing Library + **msw** mock ระดับ network — ห้าม mock axios ตรง ๆ) → e2e smoke (Playwright 1 เส้น: จำลอง session BFF (cookie/mock — ไม่มีหน้า login ของตัวเอง) → inbox → เปิดเอกสาร → ส่งดำเนินการ → toast)
- **ErrorBoundary** ระดับ route + fallback ภาษาไทย · query error แสดงใน `<NoticeCard>` ไม่ crash ทั้งแอป
- **`lazy()` + Suspense ต่อ page** (code-splitting ต่อ route) + `<PageSkeleton>` ระหว่างโหลด
- **Accessibility**: label ทุก input · modal focus-trap + Esc ปิด · `aria-label` ปุ่มไอคอน · contrast ตาม token เดิม
- **Env 12-factor**: ผ่าน `NEXT_PUBLIC_*` ของ portal เดิม (`NEXT_PUBLIC_APP_TARGET`, `NEXT_PUBLIC_BFF_URL`) · ไม่มี secret ฝั่ง FE
- อัปเดตหลัง mutation ใช้ `invalidateQueries` เป็นหลัก — optimistic update เฉพาะ permission matrix
- **README.md**: วิธีรัน dev/test/build + ตาราง env + โครงสร้างโฟลเดอร์ย่อ

## 13. ข้อห้ามรวม (ผิด = ไม่ผ่าน review)

1. ห้ามเพิ่ม UI library / chart library / Tailwind
2. ห้าม paraphrase ข้อความไทยใด ๆ จาก prototype/SRS
3. ห้าม hardcode เมนู/สิทธิ์ต่อ role ฝั่ง FE (ใช้ `GET /menus` + `GET /groups/current-user/permissions` ของระบบเดิมผ่าน BFF)
4. ห้ามใส่ logic routing workflow (กฎวงเงิน GM 50,000 / AVP 300,000, เห็นควรไม่ชดเชยจบทันที, ขั้นถัดไป) ใน FE — หน้าที่ BE
5. ห้ามอ้าง section 04/05 หรือสถานะบัญชีในทุกที่ (SDD v7.5 ตัดแล้ว)
6. วันที่แสดงผลเป็น พ.ศ. ผ่าน `formatDateThai()` เท่านั้น — ห้ามแปลงเองกระจายตามหน้า
7. ห้าม import ข้าม feature · ห้าม barrel index.ts

## 14. Definition of Done (ทั้งโปรเจกต์ FE)

1. ครบ 11 route ใช้งานได้จริงกับ BE (`plan-be.md`) ผ่าน `docker compose up` — เดิน workflow ครบทั้งเคส ≤50,000 (จบที่ GM) และ 50,001–300,000 (ผ่าน AVP แล้วจบ) + เคสเห็นควรไม่ชดเชยที่ 01/02 จบทันที
2. ทุกหน้าเทียบตากับหน้า prototype แล้วตรง: layout, สี pill/chip, ตาราง, ข้อความ (script grep เทียบ string สำคัญผ่าน)
3. validation ครบ: popup verbatim · %รวม 100% · ปี required · ไฟล์ ≤5MB+ext · comment required เมื่อไม่ชดเชย
4. CI ของ repo เดิมเขียว (lint/typecheck/jest/next build) · unit test ครอบ constants/format/DecisionPanel
5. ไม่มี dependency นอกรายการ §1-2 ใน package.json · bundle ไม่มี lib แปลกปลอม
6. AbnormalListPage สร้างเสร็จแต่ปิด flag — เปิดได้ด้วยแก้ env ตัวเดียว
