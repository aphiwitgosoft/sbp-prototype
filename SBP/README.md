# ระบบ SBP (Store Business Partner) — ภาพรวมโปรเจกต์

> เอกสารนี้สรุป **ภาพรวมการใช้งาน** ของ 3 โฟลเดอร์ (repo) ในไดเรกทอรี `SBP/` ว่าแต่ละตัวคืออะไร เหมาะกับงานแบบไหน และรัน/ใช้งานอย่างไร
> รายละเอียดเชิงลึกของแต่ละ repo อ่านได้จากไฟล์วิเคราะห์ที่วางคู่กัน (ดูหัวข้อ [เอกสารเชิงลึก](#เอกสารเชิงลึกรายตัว))

ระบบ SBP คือแพลตฟอร์มบริหารงาน **Store Business Partner** ของ CP All / 7-Eleven (ระบบ "SBP Mall") ประกอบด้วย 3 ชั้น (3-tier): **Frontend → BFF → Backend** โดยแต่ละชั้นแยกเป็นคนละ repo

---

## 1. สรุปเร็ว (โฟลเดอร์ไหน ใช้ทำอะไร)

| โฟลเดอร์ | บทบาท | เทคโนโลยี | Port (dev) | ใช้ทำอะไร / เหมาะกับงาน |
|---|---|---|---|---|
| `srm-sps-spsap-web-frontend` | **FE** (Frontend / UI) | Next.js 16 + React 19 + TypeScript + PrimeReact + Tailwind | 3000 | หน้าจอทั้งหมดที่ผู้ใช้เห็น — build ได้ 3 portal (sml / siv / sbpm) จาก codebase เดียว |
| `srm-sps-spsap-sbp-bff` | **BFF** (Backend For Frontend) | NestJS 11 + TypeScript | 3000 (ปรับได้ผ่าน `PORT`) | ชั้นกลางระหว่าง FE กับ backend หลายตัว — จัดการ login (AWS Cognito), เก็บ token ใน cookie, proxy/รวมข้อมูลจาก 6 backend |
| `srm-sps-spsap-store-backend` | **BE** (Backend / Core API) | NestJS 11 + TypeORM + PostgreSQL | 3004 | บริการข้อมูล "ร้าน SBP" หลัก: statement, ประเมินผลร้าน (FES), ยอดขาย (FCS), หนังสือขอความร่วมมือ, upload, master data |

**ทิศทางการเรียก:** ผู้ใช้ → **FE** (เบราว์เซอร์) → **BFF** (แนบ cookie/ยืนยันตัวตน) → **BE** (store-backend + backend อื่นอีก 5 ตัว)

```
┌───────────────┐     HTTPS + cookie      ┌───────────────┐   x-api-key / Bearer   ┌────────────────────┐
│  web-frontend │  ───────────────────▶   │    sbp-bff    │  ───────────────────▶  │  store-backend     │ (:3004)
│  (Next.js)    │                         │  (NestJS)     │                        │  + auth-backend     │ (:3003)
│  :3000        │  ◀───────────────────   │  :3000        │  ◀───────────────────  │  + spm / scm / inv  │ (:3005-3008)
└───────────────┘   JSON {success,data}   └───────────────┘        REST            │  + employee backend │
                                                                                    └────────────────────┘
```

> หมายเหตุ: `store-backend` เป็น **1 ใน 6 backend** ที่ BFF เรียก (ตัวหลักด้านข้อมูลร้าน) ส่วน auth-backend, spm-backend, scm-backend, inv-backend, employee-backend เป็น repo แยกที่ไม่ได้อยู่ในโฟลเดอร์นี้

---

## 2. รายละเอียดแต่ละโฟลเดอร์

### 2.1 `srm-sps-spsap-web-frontend` — Frontend (FE)

**คืออะไร:** เว็บ UI ตัวเดียว (single codebase) ที่ build ออกได้เป็น **3 portal** ตามค่า env `NEXT_PUBLIC_APP_TARGET`:

| Target | ชื่อ portal | ผู้ใช้หลัก |
|---|---|---|
| `sml` | SML Store Partner Portal (SBP Mall) | Store Partner (ผู้บริหารร้าน SBP) |
| `siv` | SIV Investor Portal | ผู้สนใจลงทุน / ผู้สมัคร |
| `sbpm` | SBPM Company Portal | พนักงานบริษัท (back office) |

**เหมาะกับงาน:** ทำ/แก้หน้าจอ, ฟอร์ม, ตาราง, รายงาน, flow การอนุมัติฝั่งผู้ใช้ — มี **171 หน้า** ครอบคลุมใบสมัคร SBP, สัญญา/ต่อสัญญา, ประเมินเกรดร้าน, statement การเงิน, จัดการผู้ใช้/สิทธิ์, consent (PDPA) ฯลฯ

**เทคโนโลยีเด่น:** Next.js 16 (App Router, `output: "export"` = static SPA deploy บน S3/CloudFront), PrimeReact + Tailwind + Sass, react-hook-form + yup, Zustand + React Query, สร้าง PDF/Excel ฝั่ง client (jspdf / exceljs), i18n (ไทย/อังกฤษ)

**วิธีใช้งาน (คำสั่งใน `srm-sps-spsap-web-frontend/`):**
```sh
npm install
npm run dev              # dev server (Turbopack) → http://localhost:3000
npm run https            # dev server แบบ HTTPS (ใช้ตอนต้องเทสต์ secure cookie ข้าม domain กับ BFF)

# build แยกตาม portal × environment (มี 9 ชุด)
npm run build:sml:dev    # = SBP Mall / dev  (ผลลัพธ์ static อยู่ในโฟลเดอร์ out/)
npm run build:sbpm:prod  # = Company Portal / prod
# ...build:{sml,siv,sbpm}:{dev,uat,prod}

npm test                 # unit tests (Jest + Testing Library)
npm run lint
```
> `npm run dev` ค่าเริ่มต้นจะยิง API ไปที่ **BFF ของ environment dev บน cloud** (เช่น `https://sbpmall-bff-dev.cpall.co.th/api/v1`) ตามไฟล์ `.env.<target>.<env>` จึงรัน FE เดี่ยว ๆ ได้โดยไม่ต้องรัน BFF/BE ในเครื่อง

### 2.2 `srm-sps-spsap-sbp-bff` — Backend For Frontend (BFF)

**คืออะไร:** ชั้นกลาง (NestJS) ที่ FE เรียกเป็นด่านเดียว แล้ว BFF ไปคุยกับ backend ภายในหลายตัวแทน

**เหมาะกับงาน:**
- **Authentication ทั้งหมด** กับ AWS Cognito (OIDC) แล้วเก็บ token แบบเข้ารหัส (AES-256-GCM) ใน signed httpOnly cookie — FE ไม่เคยเห็น token ตรง ๆ
- ตรวจ JWT ทุก request ด้วย JWKS ของ Cognito
- **Proxy / รวมข้อมูล (aggregate)** ไป backend ภายใน 6 ตัว (auth, store, spm, scm, inv, employee) โดยแนบ `x-api-key` + header บริบทผู้ใช้
- งาน presentation บางส่วน เช่น สร้างไฟล์ Excel, รวมงานค้างรออนุมัติจากทุก backend (`/bff/backlog/pending`)

**สำคัญ:** BFF นี้ **stateless — ไม่ต่อฐานข้อมูลเอง** (business logic จริงอยู่ที่ backend) มี ~54 modules / ~440 endpoints ส่วนใหญ่เป็น proxy

**วิธีใช้งาน (คำสั่งใน `srm-sps-spsap-sbp-bff/`):**
```sh
npm install
# ต้องมีไฟล์ .env (มี .env.local ตัวอย่างให้) ตั้งค่า Cognito + URL ของ backend 6 ตัว
npm run start:dev        # nest start --watch → ฟังที่ PORT (default 3000)
npm run build            # nest build → dist/
npm run start:prod       # node dist/main

npm test                 # unit tests
npm run test:cov
npm run lint
```
> ⚠️ ถ้ารันพร้อม FE ในเครื่องเดียวกัน ให้เปลี่ยน `PORT` ของ BFF (เช่น 3001) เพราะ FE ใช้ 3000 อยู่แล้ว

### 2.3 `srm-sps-spsap-store-backend` — Core Backend (BE)

**คืออะไร:** API service ตัวหลัก (NestJS + TypeORM + PostgreSQL) ที่เก็บ business logic + ข้อมูลของ "ร้าน SBP"

**เหมาะกับงาน / โดเมนหลัก:**
- **Statement** — ใบแจ้งยอด/เอกสารการเงินของร้านทุกสายธุรกิจ (SBP, PTT, Sub-Area, Bellinee's, กัมพูชา, ลาว) + interface รับไฟล์จาก SAP/STA/OAS
- **FES (ประเมินผลร้าน)** — สร้างรอบประเมิน → ให้คะแนน → ตรวจสอบ → อนุมัติ → สรุปเกรด → ออกใบแจ้งเกรด PDF → การแข่งขัน Division
- **FCS** — ยอดขายรายเดือน, ต้นทุนตรวจนับ, คะแนน QSSI (ข้อมูลตั้งต้นของการคำนวณประกันรายได้)
- **หนังสือขอความร่วมมือ** — พร้อม approval workflow (ใช้ workflow engine `@srm/glb-workflow` จริงจัง)
- **Generic Upload Framework** + **Master data** (ร้าน, องค์กร, common code)

**เทคโนโลยีเด่น:** NestJS 11, TypeORM (PostgreSQL, schema `sps_store`, มี read-replica routing เขียนเอง), workflow state-machine engine, สร้าง PDF (pdfkit / pdf-lib / puppeteer + ฟอนต์ไทย), Excel (exceljs), S3, RabbitMQ, ส่งอีเมล — มี ~31 modules / ~243 endpoints

**วิธีใช้งาน (คำสั่งใน `srm-sps-spsap-store-backend/`):**
```sh
npm install              # ต้องเข้าถึง private registry (CodeArtifact) ผ่าน .npmrc สำหรับ @srm, @gosoft-sbp
# ตั้งค่า .env (มี .env-dev / .env.local ตัวอย่าง) — DB, S3, CM, EJ, SMTP, RabbitMQ
npm run dev              # nest start --watch → ฟังที่ PORT (default 3004)
npm run build            # tsc + copy assets → dist/
npm run start:prod       # node dist/main.js

# ฐานข้อมูล (TypeORM CLI)
npm run migration:run    # รัน migration
npm run migration:generate

npm test
npm run test:cov
```
> **หมายเหตุความปลอดภัย:** ตัว backend นี้ไม่ทำ login เอง — รับ request จาก BFF ผ่าน `x-api-key` หรือ Bearer JWT (login จริงอยู่ที่ Cognito ฝั่ง BFF/auth-backend) จึงต้องอยู่หลัง network layer ที่ให้เฉพาะ BFF เข้าถึงได้

---

## 3. การทำงานร่วมกัน (flow ตัวอย่าง)

1. ผู้ใช้เปิด FE → FE เรียก `GET /users/current` ไปที่ **BFF**
2. ถ้ายังไม่ล็อกอิน → BFF redirect ไป **AWS Cognito** (OIDC) → กลับมาพร้อม code → BFF แลก token → เข้ารหัสเก็บใน httpOnly cookie
3. ทุก request ถัดไป FE แนบ cookie อัตโนมัติ (`withCredentials`) → BFF ถอดรหัส + verify JWT
4. BFF แปลงเป็นการเรียก **backend** ที่เหมาะสม (เช่น ข้อมูลร้าน → `store-backend:3004`) พร้อมแนบ `x-api-key` + header ผู้ใช้ (`x-user-id`, `x-user-group-id`, ...)
5. backend ทำ business logic + query DB → คืนผล → BFF ห่อเป็น `{success, data, requestId}` → FE render

**Authentication:** อยู่ที่ BFF (Cognito OIDC + cookie) — FE ไม่แตะ token, BE เชื่อว่า request ที่มี `x-api-key` ถูกต้องมาจาก BFF
**Authorization:** สิทธิ์ต่อเมนู/ปุ่ม ดึงจาก auth-backend (`/groups/current-user/permissions`); เมนู sidebar มาจาก API (`/menus`) ไม่ hardcode

---

## 4. รันทั้งระบบใน local (สรุป port)

โดยทั่วไป **ไม่จำเป็นต้องรันครบทุกตัว** — รัน FE เดี่ยวแล้วชี้ไป BFF บน dev cloud ก็พัฒนา UI ได้ ถ้าต้องรันครบ:

| ลำดับ | บริการ | Port default | หมายเหตุ |
|---|---|---|---|
| 1 | store-backend (+ backend อื่น) | 3004 (auth 3003, spm 3005, scm 3006, inv 3007, employee 3008) | ต้องมี PostgreSQL + ตั้ง `.env` |
| 2 | sbp-bff | 3000 → **แนะนำเปลี่ยนเป็น 3001** | ตั้ง URL ของ backend ทั้ง 6 + Cognito |
| 3 | web-frontend | 3000 | ตั้ง `NEXT_PUBLIC_BFF_API_URL` ให้ชี้ BFF ในเครื่อง |

> ระวังชนกันที่ port 3000 (ทั้ง FE และ BFF ตั้ง default 3000)

---

## 5. บริบท: ความเชื่อมโยงกับระบบประกันรายได้ (K2 / SBPGI)

3 repo นี้คือ **"ระบบปัจจุบัน" (SBP Mall)** ที่ prototype ระบบประกันรายได้ K2/SBPGI (ไฟล์/หน้า HTML ในโฟลเดอร์แม่ `sbp-prototype/`) ออกแบบจะเข้าไปเป็นโมดูลหนึ่ง จุดเชื่อมที่พบจริงในโค้ด:

- **ข้อมูลตั้งต้น** มีอยู่แล้วใน store-backend: `fcs_monthly_sales` (ยอดขายรายเดือน), `fcs_audit_costs` (ตรวจนับ), `fr_store_insure` (เงินช่วยเหลือ/ประกันรายได้ต่อสัญญา) — แต่ยัง **ไม่มี logic คำนวณเงินชดเชย** และยังไม่มี workflow เอกสารประกันรายได้ (ปย.1) เต็มรูปแบบ
- **Workflow engine** `@srm/glb-workflow` มีและใช้งานจริงแล้ว (หนังสือขอความร่วมมือ) → ต่อยอด version ใหม่สำหรับ K2 ได้
- **FE** มีจุดเริ่มที่หน้า `sbp/data-management/store-inquiry` (`GuaranteeIncomeDetailSection/Popup` กรอกรายละเอียดประกันรายได้ต่อร้าน)
- **BFF** มี pattern พร้อมใช้: `backlog` (รวมงานรออนุมัติหลาย backend), `workflow/action`, import/export Excel, ระบบ menus/groups/permissions

รายละเอียด flow/หน้าจอ/DB ของ K2/SBPGI อยู่ในเอกสารระดับ prototype ของโฟลเดอร์แม่ (เช่น `plan-api.html`, `plan-database.html`, `workflow.md`, `SRS_Income_Compensation_v3.1.md`)

---

## 6. เอกสารเชิงลึกรายตัว

อ่านการวิเคราะห์ source code แบบละเอียด (tech stack, ทุก module/endpoint, DB, config, ข้อสังเกต) ได้จาก:

- [`srm-sps-spsap-web-frontend.md`](./srm-sps-spsap-web-frontend.md) — Frontend (Next.js) ครบทุกหน้า/route/service
- [`srm-sps-spsap-sbp-bff.md`](./srm-sps-spsap-sbp-bff.md) — BFF (NestJS) ครบทุก module/endpoint + auth flow
- [`srm-sps-spsap-store-backend.md`](./srm-sps-spsap-store-backend.md) — Store Backend (NestJS) ครบทุก module/entity/DB + workflow engine

---

## 7. เกร็ดชื่อ / คำย่อ

- **SBP** = Store Business Partner (ผู้บริหารร้าน 7-Eleven แบบพันธมิตร)
- **srm-sps-spsap-** = convention ตั้งชื่อ repo ของ Gosoft (`srm`=service code, `sps`=system code, `spsap`=application code) — ไม่มีนิยามเต็มในโค้ด
- **BFF** = Backend For Frontend
- **FES** = Franchise Evaluation System (ประเมินเกรดร้าน) · **FCS** = ชุดข้อมูลยอดขาย/ตรวจนับ/QSSI · **CM/CTM** = Content Manager (ระบบเก็บไฟล์เอกสาร) · **EJ** = Electronic Journal
- Portal: **sml** = SBP Mall (Store Partner) · **siv** = Investor · **sbpm** = Company back office

*เอกสารนี้เป็นภาพรวมเพื่อการใช้งาน — ตัวเลข module/endpoint และรายละเอียดอ้างอิงจากไฟล์วิเคราะห์ทั้งสามที่วางคู่กัน ณ เวลาที่จัดทำ*
