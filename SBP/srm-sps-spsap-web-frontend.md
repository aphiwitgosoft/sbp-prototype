# srm-sps-spsap-web-frontend — เอกสารวิเคราะห์ Codebase (ละเอียด)

> วิเคราะห์จาก source code จริงใน `/Users/bank_mac/gosoft/java/SBP/sbp-prototype/SBP/srm-sps-spsap-web-frontend`
> (git: `git@bitbucket.org:gosoft-thailand/srm-sps-spsap-web-frontend.git`, branch `main`)
> ข้อมูล ณ วันที่วิเคราะห์: 2026-08-05 — ทุกข้อความอ้างอิงจากไฟล์ในโปรเจกต์ ไม่มีการเดา

---

## 1. ภาพรวม

### 1.1 แอปนี้คืออะไร

เป็น **web frontend ตัวเดียว (single codebase) ที่ build ออกได้เป็น 3 portal** ของระบบ Store Business Partner (SBP) ของ CP All / 7-Eleven โดยเลือก "ร่าง" ของแอปด้วย env variable `NEXT_PUBLIC_APP_TARGET`:

| App target | ชื่อแอป (จาก `src/config/*.config.ts`) | Theme | BFF ที่เรียก (dev) | ผู้ใช้หลัก (ตีความจากชื่อ+เมนู) |
|---|---|---|---|---|
| `sml` | **SML Store Partner Portal** (SBP Mall) | blue | `https://sbpmall-bff-dev.cpall.co.th/api/v1` | Store Partner (ผู้บริหารร้าน SBP) — ดูร้านตัวเอง, statement, ประเมินผล, ยืนยันสิทธิ์ผู้ช่วยฯ |
| `siv` | **SIV Investor Portal** | green | `https://sbpinvestor-bff-dev.cpall.co.th/api/v1` | ผู้สนใจลงทุน (Investor) — ลงทะเบียน, สมัครเป็น SBP |
| `sbpm` | **SBPM Company Portal** | dark | `https://sbpm-bff-dev.cpall.co.th/api/v1` | พนักงานบริษัท (back office) — จัดการผู้สมัคร, สัญญา, ประเมินเกรด, รายงาน, สิทธิ์ผู้ใช้ |

ชื่อ package ใน `package.json` คือ `sbp-portal` (version 0.1.1)

**ความสัมพันธ์กับ workspace นี้:** แอปนี้คือ "ระบบปัจจุบัน" (SBP Mall / SBPM ตาม SDD) ที่ prototype ระบบประกันรายได้ K2/SBPGI (`sbp-prototype/`) ออกแบบจะเข้าไปเป็นโมดูลหนึ่ง — sidebar group ของ prototype ใช้ชื่อ "ระบบประกันรายได้ (SBP Mall)" สอดคล้องกับแอปนี้

### 1.2 ความหมาย SRM / SPS / SPSAP

ในโค้ด **ไม่มีการขยายความชื่อเต็ม** ของ srm/sps/spsap ที่ใดเลย หลักฐานที่ใกล้ที่สุดคือ README ส่วน CI/CD ระบุ `CI_SONAR_PROJECTKEY_PREFIX=<serviceCode>-<systemCode>-<applicationCode>` — จึงตีความได้เพียงว่า `srm` = service code, `sps` = system code, `spsap` = application code ตาม convention ตั้งชื่อ repo ของ Gosoft (pipeline template ก็ชื่อ `srm-sps-spsap-pipeline-template`)

### 1.3 สรุป README.md

README มี 2 ส่วน:
1. ส่วนแนะนำโปรเจกต์ "SBP Portal - Next.js Application" — ระบุ tech stack (แต่**ล้าสมัย**: เขียนว่า Next.js 15 ทั้งที่ package.json ใช้ 16.2.11 และไม่พูดถึง react-query/yup/PrimeReact icons ฯลฯ), วิธีรัน dev/build/test/lint, env variable `NEXT_PUBLIC_APP_TARGET` (sml/siv/sbpm), โครงสร้าง src
2. ส่วน "กิตติกรรมประกาศ" (ภาษาไทย) — เครดิตทีมที่แชร์ CI/CD template ภายใน Gosoft และคำแนะนำการตั้ง Repository Variables (SonarQube, AWS OIDC ECR role) + การสร้าง ECR / deployment ก่อน merge เข้า main

---

## 2. Tech Stack

| หมวด | ไลบรารี (เวอร์ชันจาก package.json) | หน้าที่ในโปรเจกต์ |
|---|---|---|
| Framework | **Next.js 16.2.11** — **App Router** (`src/app/`), `output: "export"` (static export/SPA) | โครงหลัก; ทุกหน้าเป็น `'use client'` เกือบทั้งหมด, ไม่มี API routes |
| UI runtime | **React 19.1.0** + react-dom 19.1.0 | |
| ภาษา | TypeScript 5 (`strict: true`, path alias `@/* → src/*`) | |
| Component library | **PrimeReact 10.9.8** + primeicons 7 | ตาราง, dialog, dropdown ฯลฯ — ห่อด้วย component กลางใน `src/components/Form`, `src/components/Table` |
| Styling | **Tailwind CSS 4** (@tailwindcss/postcss) + **Sass** (`src/styles/*.scss` — global override ของ PrimeReact checkbox/dropdown/inputtext/multiselect/radio/tooltip) + CSS Modules (`AppSider.module.scss`) + tailwind-merge | |
| Form | **react-hook-form 7.63** + **yup 1.7** + @hookform/resolvers | ฟอร์มทุกหน้า; มี **validation engine เขียนเอง** ใน `src/lib/validation/` (schema JSON → RegisterOptions ของ RHF, มี pattern registry, guards, context) |
| State management | **Zustand 5** (`src/stores/`: `loadingStore`, `permissionStore`, `userProfileStore`) + React Context (`src/contexts/`: `ApiContext`, `AuthContext`, `LayoutContext`, `HighlightedFieldsContext`) | |
| Data fetching | **axios 1.16** (instance กลาง `src/lib/apiClient.ts` — interceptor refresh token + global loading) + **@tanstack/react-query 5.100** (QueryClientProvider ประกาศใน `(main)/layout.tsx`) | |
| i18n | **i18next 25 + react-i18next 15** (`src/i18n.ts`) — ภาษา default `th-TH`, fallback `en-US`; ไฟล์แปล `public/locales/translation-{th-TH,en-US}.json` (เล็กมาก ~39 key ส่วนใหญ่เป็น label เมนู) | |
| Excel | **exceljs 3.4** + file-saver (dependencies), **xlsx 0.18** (devDependencies) | export/import รายงาน Excel |
| PDF | **jspdf 4.2 + jspdf-autotable 5** (ฝังฟอนต์ TH Sarabun New เป็น Base64 ใน `statement/services/thSarabunNew-*.ts`), **pdf-lib**, **pdfjs-dist** | สร้าง/รวม/แสดง statement, สัญญา, ใบแจ้งเกรด |
| อื่น ๆ | dayjs + date-fns (วันที่), dompurify + html-react-parser (render HTML consent อย่างปลอดภัย), lottie-react (animation ตัว loader `LottieLoader`), qs, use-debounce | |
| ไม่ใช้ | ไม่มี chart library (ไม่พบ recharts/chart.js/echarts), ไม่มี Redux, ไม่มี MUI/Antd | |

หมายเหตุ: มี `overrides` ใน package.json ล็อกเวอร์ชัน transitive deps (brace-expansion, minimatch, form-data, sharp, postcss ฯลฯ) — สอดคล้อง commit ล่าสุด `fix cve`

---

## 3. วิธีรัน / สคริปต์ / CI

### 3.1 npm scripts

| Script | คำสั่ง | หมายเหตุ |
|---|---|---|
| `dev` | `next dev --turbopack` | dev server ปกติ (HTTP :3000) |
| `build` | `node scripts/build.js sml dev` | ค่า default = build ร่าง sml/dev |
| `build:{sml,siv,sbpm}:{dev,uat,prod}` | `node scripts/build.js <target> <env>` | 9 ชุด build ครบทุก portal × env |
| `start` | `next start` | (ใช้ได้เฉพาะกรณีไม่ static export) |
| `https` | `node server.js` | dev server แบบ **HTTPS** |
| `lint` | `eslint` (flat config, extends `next/core-web-vitals` + `next/typescript`) | |
| `test` / `test:watch` / `test:cov` | jest | |
| `test:ci` | jest + coverage lcov + jest-junit → `test-reports/`, `coveragereport/` | ใช้ใน pipeline |

### 3.2 `scripts/build.js` — build หลาย tenant

- รับ argument `<projectType> <environment>` → validate กับ `['sml','siv','sbpm']` × `['dev','uat','prod']`
- อ่านไฟล์ `.env.<projectType>.<environment>` แล้ว merge เข้า process env พร้อม set `NEXT_PUBLIC_APP_TARGET`, `NEXT_PUBLIC_ENVIRONMENT`, `NODE_ENV`
- spawn `next build` แล้วตรวจว่ามีโฟลเดอร์ `out/` (static export) ถ้าไม่มีถือว่า build fail

### 3.3 `server.js` — custom HTTPS dev server

ไม่ใช่ custom server เพื่อ logic พิเศษ — เป็นเพียง wrapper `https.createServer` อ่าน cert จาก `./auth/key.pem` + `./auth/cert.pem` แล้ว handle ด้วย Next ปกติ ที่ port 3000 เพื่อให้ **รัน dev เป็น https://localhost:3000** (จำเป็นเวลาเทสต์ cookie ข้าม domain กับ BFF ที่เป็น HTTPS/secure cookie) — โฟลเดอร์ `auth/` ไม่ถูก commit

### 3.4 `next.config.ts`

- `output: "export"` — **สร้าง static site ล้วนใน `out/`** เหตุผลเขียนไว้ในคอมเมนต์: deploy บน **S3/CloudFront** ซึ่งรัน image optimizer ไม่ได้ → `images.unoptimized: true`
- `trailingSlash: true` (พฤติกรรม SPA บน S3)
- `remotePatterns` อนุญาตรูปจาก `i.pravatar.cc` (รูป avatar ตัวอย่าง)
- `reactStrictMode: true`, ปิด `experimental.turbopackFileSystemCacheForBuild`
- **ไม่มี** rewrites / proxy / basePath ใด ๆ — การเรียก API ทั้งหมดยิง cross-origin ตรงไปที่ BFF ด้วย cookie (`withCredentials`)

### 3.5 CI — `bitbucket-pipelines.yml`

ทุก step import จาก template กลาง `srm-sps-spsap-pipeline-template` (repo แยก):
1. push branch `feature/*` → security scan
2. PR `feature/* → main` → SonarQube scan
3. merge เข้า `main` → build container + sign signature ด้วย AWS profile
4. PR `main → dev` → ตรวจลายเซ็น + **deploy S3** ที่ DEV
5. PR `dev → uat` → deploy S3 ที่ UAT
6. PR `uat → production` (แนบหลักฐาน QC PASS) → deploy S3 ที่ Production

---

## 4. Configuration / Environment

### 4.1 ไฟล์ .env (10 ไฟล์ที่ root)

`.env.local` (ปัจจุบัน comment ทิ้งทั้งไฟล์) + `.env.{sml,siv,sbpm}.{dev,uat,prod}`

ตัวแปรที่ใช้จริงในโค้ด:

| ตัวแปร | ใช้ที่ | ความหมาย |
|---|---|---|
| `NEXT_PUBLIC_APP_TARGET` | `src/config/index.ts`, `landingPath.util.ts` | เลือก config sml/siv/sbpm |
| `NEXT_PUBLIC_ENVIRONMENT` | config | dev/uat/prod |
| `NEXT_PUBLIC_BFF_API_URL` | config ทุกตัว (`api.bffUrl`) | base URL ของ BFF เช่น `https://sbpmall-bff.cpall.co.th/api/v1` (prod sml), `sbpm-bff.cpall.co.th` (prod sbpm), `sbpinvestor-bff-dev` (siv) |
| `NEXT_PUBLIC_API_BASE_URL` | `config/index.ts` | override bffUrl ได้ (ไม่ตั้งในไฟล์ env ใด) |
| `NEXT_PUBLIC_LOGIN_URL` / `REFRESH_URL` / `PROFILE_URL` / `LOGOUT_URL` | `sml.config.ts`, `apiClient.ts`, `apiService.ts` | path auth ของ BFF (คอมเมนต์ในโค้ดบอกว่าแยกไว้เพราะ "**Eko** ยังใช้ path ไม่เหมือน **Cognito**") — default `/auth/login`, `/auth/refresh`, `/auth/profile`, `/auth/logout` |
| `NEXT_PUBLIC_LANDING_PAGE` | `landingPath.util.ts` | landing fallback เช่น `/sbp/main-remain` (dev/uat) หรือ `/main` (prod) |
| `NEXT_PUBLIC_SBPM_BFF_API` | (ประกาศใน env sml/sbpm) | URL BFF ฝั่ง SBPM — ในโค้ด src ปัจจุบันหน้าที่ใช้จริงคือหน้า uploads/login ผ่าน `NEXT_PUBLIC_BFF_API_URL` เป็นหลัก |
| `NEXT_PUBLIC_TES00002_FILE_PATTERN` | `(main)/uploads/page.tsx` | regex ตรวจชื่อไฟล์ Call_Complaint (`^Call_Complaint_((0[1-9])|(1[0-2]))\d{4}$`) |
| `NEXT_PUBLIC_LOGIN_STOREPARTNER_URL` | `components/login/LoginContainer.tsx` | ลิงก์ "เข้าสู่ระบบสำหรับ Store Partner" เปิดไปที่ **ekoapp.com** (`https://develop-staging.ekoapp.com` ใน siv dev) |

### 4.2 `src/config/`

- `index.ts` — `getConfig()`: อ่าน `NEXT_PUBLIC_APP_TARGET` → คืน config ของ target นั้น + normalize environment + flag `isDevelopment/isProduction`; มี fallback พิเศษสำหรับ `NODE_ENV === 'test'`
- `sml.config.ts` / `siv.config.ts` / `sbpm.config.ts` — ต่างกันที่ `appName`, `appTheme`, auth path (เฉพาะ sml มี loginPath/refreshPath/profilePath/logoutPath จาก env) และ `consentConfig` (ข้อความ label/title ของ consent notice 3 ประเภท: `store_partner` privacy notice, `applicant` privacy notice, `store_employee_marketing` direct marketing)

---

## 5. Routing / หน้าจอทั้งหมด (หัวใจของเอกสาร)

โครงสร้าง `src/app/` เป็น App Router มี **171 ไฟล์ `page.tsx`** แบ่งเป็น 2 โซนใหญ่:
- **นอก route group `(main)`** — หน้า public / หน้าเปิดเป็น popup window แยก (ไม่มี header/sidebar)
- **ใน `(main)`** — หน้าในระบบหลังล็อกอิน ครอบด้วย `(main)/layout.tsx` (AppHeader + AppSider + LottieLoader + ConsentPopupContainer + QueryClientProvider)

Convention ภายใน route: โฟลเดอร์ขึ้นต้น `_` (`_components`, `_services`, `_sections`, `_popup`, `_hooks`, `_types`, `_mocks`, `_shared`) และวงเล็บ `(components)`, `(hooks)`, `(search)`, `(details)` = ไม่ใช่ route

### 5.1 หน้า public / นอก (main)

| Route | หน้าที่ (จากโค้ด) |
|---|---|
| `/` | หน้า bootstrap: เรียก `GET /users/current` → เก็บลง `userProfileStore` → ตรวจ email pattern `s\d{7}@7sbp.store` (บัญชี username เก่า → โชว์ `UsernameWarningPopup01`), ถ้า 404 โชว์ Popup02, ปกติ redirect ไป landing page ตาม group ของผู้ใช้ (`getLandingPath`) |
| `/login` | ไม่มี UI จริง — redirect ทันทีไป `${NEXT_PUBLIC_BFF_API_URL}/auth/login?redirectUrl=<origin>` (เริ่ม OIDC flow ที่ BFF) |
| `/auth/login` | หน้า login แบบมีฟอร์ม username/password (Carousel + WelcomeSection + `LoginContainer`) — validate password ≥12 ตัวมีตัวอักษร+ตัวเลข, submit ผ่าน `auth.service.ts` → `POST {bffUrl}/auth/login` (cookie), มีปุ่มแยก "Store Partner" เปิด ekoapp.com, ลิงก์ไป `/registration` และไฟล์คู่มือ `/files/tutorial_new.pdf` |
| `/registration` | ลงทะเบียนผู้ใช้ใหม่ (มี validation "บัญชีผู้ใช้นี้มีอยู่ในระบบแล้ว...") — ใช้ `register.service.ts` (`/registration`, `/identity-check/sp`, `/identity-check/pttor`) |
| `/resetPassword` | ตั้ง/รีเซ็ตรหัสผ่านผ่าน token (`resetPassword.service.ts`: `/auth/password-reset/request`, `/auth/reset-password/${token}`) |
| `/investors/registration` | ลงทะเบียนผู้สนใจลงทุน (public, ฝั่ง SIV) |
| `/investors/sbp/registration` | ลงทะเบียนเข้าใช้งาน SBP (public) |
| `/investors/sbp/set-password` | ตั้งรหัสผ่านเข้าใช้งาน SBP |
| `/consent` | หน้าเก่า — ในโค้ดเขียนว่า "หน้านี้ไม่ได้ใช้แล้ว" |
| `/confirm-declare` | หน้า public ยืนยัน "แจ้งความสัมพันธ์" (ข้อความ "บริษัท ซีพี ออลล์ จำกัด (มหาชน) ได้จัดทำ...") — คู่กับ domain declare (`/bff/relation/*`) |
| `/bellinee-consent`, `/bellinee-consent/success` | ให้ผู้รับมอบอำนาจร้าน **Bellinee's** (เบลลินี) กด consent ผ่านลิงก์/token (`bellineeConsent.service.ts`: `GET /{nationalId}/consent/init`, `POST /{authorizationId}/consent-by-auth`, `/confirm/${token}`) |
| `/sub-area-consent`, `/sub-area-consent/success` | consent ของ **Franchise Sub Area** ผ่าน token (`subAreaConsent.service.ts` โครงเดียวกับ bellinee) |
| `/contract-management-doc` | หน้าแสดง "แบบพิมพ์สัญญา" (เปิดเป็นเอกสาร/print แยกหน้าต่าง) |
| `/contract-management-popup/import-doc` | popup นำเข้าเอกสาร (ต้องมี processId) |
| `/contract-management-popup/repair-reprint` | popup ระบุช่วงหน้าที่จะพิมพ์ซ่อม |
| `/contract-management-popup/store-lookup` | popup ค้นหารหัสร้าน |
| `/example` + 12 หน้าย่อย (`button`, `calendar`, `color`, `datepicker`, `dropdown`, `form1`, `popup`, `selector`, `stepper`, `table`, `typography`) | **UI kit sandbox** ภายในทีม — ตัวอย่างการใช้ component กลาง (ถูก exclude จาก coverage) |

### 5.2 กลุ่ม SBP core (back office จัดการ Store Partner) — `(main)/sbp/*`

| Route | หน้าที่ |
|---|---|
| `/sbp/main-remain` | **งานคงค้าง (backlog/pending)** — landing page ของ dev/uat: `GET /bff/backlog/pending` แสดงตารางงานที่รอดำเนินการ |
| `/main` | หน้าหลัก (landing prod) |
| `/sbp/investor-sbp-application/page1..page3` | **ใบสมัครตัวเต็ม Store Business Partner** 3 ขั้น (ข้อมูลผู้สมัคร/ครอบครัว/ประวัติงานกับ CPALL/เอกสารแนบ PDF ≤20MB) ขับเคลื่อนด้วย workflow (`doWorkflowPage` — event approve/sendback/save/submit/cancel) |
| `/sbp/investor-sbp-application/short` | ใบสมัครตัวย่อ |
| `/sbp/investor-sbp-application/manage-applicant` (+ `detail`, `delete-applicant`) | จัดการผู้สมัคร: ค้นหา, ดูรายละเอียด, ลบผู้สมัคร (กรอกเลขบัตร/Passport ยืนยัน) |
| `/sbp/investor-sbp-application/redirect-page` | หน้า redirect กลางของ flow ใบสมัคร |
| `/sbp/onboarding` (+ `detail`) | ขั้นตอน **สัมภาษณ์/รับเป็น SBP** ฝั่งผู้ปฏิบัติ: ค้นหาใบสมัคร, เอกสารสัมภาษณ์, ส่งอีเมลนัดสัมภาษณ์ (`/report/send-interview-email`), บันทึกผลรายขั้น (`/detail/save`, `/detail/next`, `/detail/cancel`) |
| `/sbp/manage-onboarding` (+ `detail`) | "จัดการข้อมูล ขั้นตอนการเป็น SBP" — ฝั่ง admin ตั้งค่า/แก้ไข process onboarding |
| `/sbp/manage-executive` (+ `detail`) | จัดการข้อมูล **ผู้บริหารร้าน (executive)** — ค้นหา/ดู/แก้ไขประวัติส่วนตัว ผ่าน `manage-executive.service.ts` |
| `/sbp/store-partner-profile/[context]` | **โปรไฟล์ Store Partner** (dynamic `[context]` = บริบทผู้ใช้ เช่น admin/store-partner) — หน้า search + กลุ่มหน้า details: `store-partner-info` (ข้อมูลส่วนตัว + รูปโปรไฟล์), `family-info`, `activity-info` (กิจกรรมที่เข้าร่วม), `legal-entity-info` / `juristic-info` (นิติบุคคล), `sbp-store-info` (ข้อมูลร้าน), `sp-declare` (แจ้งความสัมพันธ์), `store-partner-info-compare` (เทียบข้อมูลเก่า-ใหม่ `/store-partner-info/compare`) |
| `/sbp/association/activity` (+ `search`, `view`) | กิจกรรม **สมาคม/ชมรม Store Partner** — สร้าง/ค้นหา/ดู/ลบกิจกรรม (`activity.service.ts`) |
| `/sbp/consent` | รายงาน/จัดการ consent ของ Store Partner (ศาสนา ฯลฯ — sensitive data) ผ่าน `sbpConsent.service.ts` (`/applicants/consent-filter`, `/store-partner/consent`, `/store-partner/store-partner-data-change`, `/applicants/workflow-status`) |
| `/sbp/consent/pdpa` | "รายงานการขอใช้สิทธิแก้ไข เปลี่ยนแปลงข้อมูลผ่าน SBP Mall" (PDPA data-change requests) |
| `/sbp/data-management/blacklist` (+ `detail`) | จัดการ **Blacklist** (`dataManagmentBlacklist.service.ts` + `blacklist.logic.ts`) |
| `/sbp/data-management/store-inquiry` (`search`/`create`/`edit`) | **ทะเบียนข้อมูลร้าน (store inquiry)** — จุดที่มี **GuaranteeIncomeDetailSection/Popup**: บันทึกรายละเอียด "ประกันรายได้" ต่อร้าน (ประเภทร้าน, ประเภทพนักงาน, สาขาที่ได้รับผลกระทบ, วันที่ได้รับผลกระทบ, เดือน/ปี, ยอด guaranteeIncome, split, หมายเหตุ) |
| `/sbp/data-management/store-sbp-info` (+ `detail`) | ข้อมูลร้าน SBP (มุมมองบริษัท) |
| `/sbp/data-management/export` | export ข้อมูล (เลือก report/columns จาก `/report-master-list`, `/report-column-master-list`, ยิง `/export-data`) |
| `/sbp/juristic-management` | จัดการกลุ่มนิติบุคคล (`juristic.service.ts`: `/juristic-group*`) |
| `/sbp/opt-declare` | แบบแจ้งความสัมพันธ์ฝั่ง **OPT** ("มีความสัมพันธ์กับผู้ประสงค์ดำเนินการ/ผู้ดำเนินการร้าน SBP") |
| `/sbp/export-data-declare` | export ข้อมูลแจ้งความสัมพันธ์ (`/bff/relation/export`) |
| `/sbp/employee-benefit` | สวัสดิการพนักงานร้าน |

### 5.3 กลุ่มผู้สนใจลงทุน / ผู้สมัคร (CRD)

| Route | หน้าที่ |
|---|---|
| `/investors/management/search`, `/registration`, `/edit`, `/sbp/registration` | (ใน main) "หน้าจอค้นหา/ลงทะเบียน/แก้ไขข้อมูลผู้สนใจลงทุน (CRD)" + ลงทะเบียนเข้าใช้งาน SBP ให้ผู้สนใจ |
| `/sbp-interest-investor/search`, `/detail` | ข้อมูลผู้สนใจลงทุน (ข้อกำหนดและเงื่อนไขการลงทะเบียน, พื้นที่สนใจ, จองพื้นที่ — ใช้ component `Investors/*` เช่น `InterestAreaSection`, `ReserveAreaDialog`) |
| `/sbp-crd-manage-applicant/search` | จัดการผู้สมัครฝั่ง CRD (service ยังเป็น template `/api/xx`) — export รายงานผ่าน `investors.service.ts` (`POST investors/crd/export-report`, `export-contact-report`) |
| `/sbp-applicant-process` | กรอกข้อมูลผู้สมัคร (applicant process) |
| `/sbp-register-user` | "ลงทะเบียนเข้าใช้งานระบบ SBP" (ในระบบ) |
| `/sbp-register-reset-password` | ตั้งค่ารหัสผ่านผู้ใช้ (ในระบบ) |

### 5.4 กลุ่มสัญญา (Contract) — 4 โมดูลแยกกัน

| Route | หน้าที่ |
|---|---|
| `/contract` | หน้า hub ("กำหนดสิทธิ์การใช้งาน") ของโมดูลสัญญา |
| `/contract/crate-contract` (+ `[contractId]`, `print`) | สร้างสัญญา (สะกดผิดจาก create เป็น **crate** ใน route จริง) — มี `_services/contract-export.service.ts`, `_mocks`, `_tests`, พิมพ์สัญญา |
| `/contract/extend-contract/*` (11 หน้า) | **ต่อสัญญาร้าน SBP** เรียก BFF prefix `/scm-extend-contract/*`: `search-confirm-manage-sbp` → `confirm-manage-sbp` → `confirm-manage-sbp-result` (+ `-auto`), `decline-manage-sbp-result`, `search-verify-confirm-manage` → `verify-confirm-manage`, `consider-approve` (พิจารณาอนุมัติ), `unlock-contract` (ปลดล็อคต่อสัญญา — endpoint `unblock-contract`), `export-extend-contract`, `juristic-information` |
| `/contract-management` | redirect → `/contract-management/promote`; โมดูลจัดการ **แบบพิมพ์/อนุมัติสัญญา**: `promote`, `new-contract/detail`, `print-contract/detail`, `repair-reprint/detail` (พิมพ์ซ่อม), `approve-dept/detail`, `approve-division/detail`, `approve-license/detail`, `approve-reprint/detail` — หน้า detail ทุกหน้ายังมี `mock.ts` ประกบ (ข้อมูลตัวอย่าง) |
| `/legal-contract` | โมดูลสัญญาฝ่ายกฎหมาย: `create-contract` (+detail "ใบอนุมัติ - Type บจก."), `legal-approve` (+detail), `edit-template` (+create/detail — แม่แบบสัญญา "สาขาใหม่/ขยายสาขา") — ในโค้ดมีคอมเมนต์ "จะเปลี่ยนเป็น API จริงทีหลัง" (ยัง mock) |
| `/general-contract` | สัญญาทั่วไป: `check-status` (+detail — เตรียมบันทึก/นำเข้าเอกสาร สาขาใหม่/ขยายสาขา, เช็คเอกสารเช่นสำเนาบัตรประชาชนคู่สมรส), `accounting-report` |
| `/management-approve-contract` | อนุมัติสัญญาระดับผู้บริหาร: `mm1-approve` (+detail), `mm2-approve` (+detail) — มีข้อมูลประวัติลูกค้า |
| `/store-transfer` | **โอนร้าน**: `list`, `approval/list`, `approval/detail` — approval มี `_services/api.ts` เรียก `/store-transfer/approval/{list,search,detail/${workflowTransactionId},workflow/action,workflow/initialize-transactions}` (มี workflow engine ฝั่ง BFF) |

### 5.5 กลุ่มการเงิน / รายงาน (ฝั่ง SBPM/บัญชี)

| Route | หน้าที่ |
|---|---|
| `/statement` | ศูนย์รวม **Statement/งบร้าน** — service ภายในหน้าจำนวนมาก (`dailyPL`, `preStatement`, `searchStmtOpt/Sub/Cam/Laos`, `unifiedSearch/unifiedStores/unifiedReportTypes`, `viewFiles/viewMergedFiles` (รวม PDF), `ejDownload` (EJ = electronic journal, `/store-statement/report/ej/download`), `popupStamp` (อากรแสตมป์ `/store-statement/form1/popupCheckStampDuty`, `/store-statement/form1/rt040079/confirm`), `exportSubAreaCsvWorkbook`) — ครอบคลุมประเภทรายงาน: sbp, operation, cambodia, laos, sub_area, sub_area_total, bellinee (จาก `REPORT_TO_TYPE`) พร้อม permission ต่อประเภทรายงาน (`STMT_RPT_TYPE_PERM`) |
| `/sbp-store/statement/daily` | statement รายวันมุมมอง Store Partner (SML) |
| `/externalAudit` | "ส่งออกข้อมูลทางการเงินให้กับสำนักงานบัญชี" — `/store-external-audit/*` (insertAgreeStmtFile, getCountHistoryExportStmtFile, getHistoryExportStmtFileToExternalAudit ฯลฯ) |
| `/externalAuditLog` | log การส่งออกให้ external audit |
| `/performance/summary`, `/performance/open-store`, `/performance/qssi`, `/performance/audit`, `/performance/call-complaint` | รายงานผลการดำเนินงานร้าน: ยอดขายสรุป (`/sales-summary`, `/list-month-sales-summary`, `/list-year-sales-summary`, `/list-zone-summary`, `/list-type-group-summary`), ร้านเปิดใหม่, คะแนน **QSSI**, ผล audit (`/report-audit`), เรื่องร้องเรียน (Call Complaint) |
| `/report-sp-ad-status` | รายงานสถานะ AD (ผู้ช่วยผู้จัดการ?) ของ SP — `reportSpAdStatus.service.ts` (`/report-sp-ad-status`, `/common-code/list`, `${API_REPORT}/export`) |
| `/report-sp-cooperation` (+ `[context]`) | **เอกสารขอความร่วมมือ (Cooperation Doc)** — service ใหญ่ `reportSpCooperation.service.ts` เรียก `/docCooperation/*` ~20 endpoints (สร้าง/ค้นหา/อนุมัติ/export เอกสาร, ตรวจ docType, approver list, region/ประเภทร้าน) |
| `/uploads` | หน้า **Dynamic Upload console** (ไฟล์เดียว ~2,000 บรรทัด): อัปโหลดไฟล์รายงานเข้าระบบตาม group/type จาก master (`/store-uploads/master/group-report`), ตรวจชื่อไฟล์ Call_Complaint ด้วย `NEXT_PUBLIC_TES00002_FILE_PATTERN`, ติดตาม job status (`/store-uploads/general/job-status?jobId=`), ดาวน์โหลด template/export, ดูโครงสร้างองค์กรร้าน (`/store-uploads/mas-store-organize/*`) — คุมสิทธิ์ด้วย `hasPermission("/uploads", ...)` |
| `/confirm-import` | ยืนยันการนำเข้า/ส่ง "ใบแจ้งเกรด" (รอส่งใบแจ้งเกรด) |

### 5.6 กลุ่มประเมินผล SBP — `/sbp-evaluate/*` (ระบบประเมินเกรดร้าน)

เรียก BFF กลุ่ม `/Evaluationprocess/*`, `/assessment/*`, `/awardDivision/*`, `/reportdivision/*`, `/reportPtt/*`, `/manage-import/*` ผ่าน `evaluate.service.ts` (ไฟล์ service ใหญ่สุดของโปรเจกต์):

| Route | หน้าที่ |
|---|---|
| `/sbp-evaluate/evaluation` (+ `/evaluation`, `/key-score`) | ทำแบบประเมินร้าน (assessSearch/assessSave/assessSubmit/recalculate), กำหนด key score |
| `/sbp-evaluate/result` (+ `/evaluation`) | ผลการประเมิน (รวมคะแนน) |
| `/sbp-evaluate/summary` | สรุปการประเมิน (มีรอบ "การประเมินครั้งที่ 2") |
| `/sbp-evaluate/graderesult/[context]` (+ `grade-summary`, `monthly-detail`) | ผลเกรดรายร้าน/รายเดือน (context = มุมมอง เช่น admin/store) |
| `/sbp-evaluate/admingraderesult` | ผลเกรดมุมมอง admin (มี mapping active-menu พิเศษใน AppSider) |
| `/sbp-evaluate/listgrade` (+ `gradeSetting`) | รายการเกรด + ตั้งค่าเกณฑ์เกรด |
| `/sbp-evaluate/performance` (+ `/performance`) | ผล performance ร้านที่ใช้ประเมิน (`/assessment/performance/exportExcel`) |
| `/sbp-evaluate/audit` (ผ่าน `/assessment/audit/*`) | (ฝังใน evaluation flow) ตรวจทาน/อนุมัติผลประเมิน: search, approves, sendback/confirm, sendConclude, exportEvaluationform |
| `/sbp-evaluate/division/[context]` | ประเมินระดับฝ่าย/เขต (division) |
| `/sbp-evaluate/reward` | รางวัล (awardDivision export) |
| `/sbp-evaluate/reminder` | แจ้งเตือนการประเมิน |
| `/sbp-evaluate/manageImport` | นำเข้า/ลบข้อมูลประเมิน (`/manage-import/deletereal`) |
| `/sbp-evaluate/reportevaluationgrade` | รายงานผลเกรดการประเมิน |

### 5.7 กลุ่มจัดการผู้ใช้/สิทธิ์ และหน่วยธุรกิจอื่น

| Route | หน้าที่ |
|---|---|
| `/setting/manage-user-group` (+ `form`) | จัดการกลุ่มผู้ใช้ (tree group/subgroup — `/groups`, `/groups/by-parent`, `/groups/subgroup`) |
| `/setting/manage-user-rights` (+ `form`) | จัดการสิทธิ์ per เมนู (canView/canManage/canExport/canOther — `/groups/{id}/permissions`, template) + สมาชิกกลุ่ม (`/user-group-memberships`, ลบผู้ใช้ `/users/{id}`, `/users/bulk`) |
| `/assistant-manage-users` | **ยืนยันสิทธิ์ผู้ช่วยผู้บริหารร้าน** — ค้นพนักงาน/ร้าน แล้ว assign (`assistantManagerAssignments.service.ts`: `/employees/{userId}/stores`, `/stores/{storeId}/employees`, `/stores-list`, `POST /assistant-manager/assign`) |
| `/bellinees/manage-user`, `/bellinees/screening-user` (+ `form`) | จัดการ/คัดกรองผู้ใช้ร้าน **Bellinee's Bake & Brew** (`bellineeAuthorizations.service.ts`: `/bellinee/authorizations`) |
| `/franchise-sub-area/manage-user`, `/screening-user` (+ `form`) | จัดการ/คัดกรองผู้ใช้ **Franchise Sub Area** (`subAreaAuthorizations.service.ts`, `subAreaStore.service.ts`: `/sub-area/authorizations`, `/store-service`) |
| `/sbp-management-system/sbp-connection/label` | ระบบ label/ป้าย ของ SBP connection (`label.service.ts`: `/label/init`, `/label/filter`) |

### 5.8 middleware

- `src/middleware.ts` — matcher เฉพาะ `/login`: เรียก `clearCookies()` จาก `src/middlewares/clear-cookies.ts` (ลบ cookie ทุกตัวของ request ก่อนเข้า `/login` = force fresh login)
- **ข้อสังเกต:** เนื่องจาก production ใช้ `output: "export"` deploy บน S3/CloudFront middleware นี้จะ**ทำงานเฉพาะตอนรันผ่าน Next server** (dev / `next start`) ไม่ทำงานบน S3
- **ไม่มี auth guard ใน middleware** — การกันสิทธิ์ทำฝั่ง client (axios 401 → redirect BFF login + `permissionStore.hasPermission` + component `Permission/AccessDenied`)

---

## 6. Authentication & Authorization

### 6.1 สถาปัตยกรรม: BFF + cookie session (ไม่เก็บ token ฝั่ง FE)

- axios instance กลาง (`src/lib/apiClient.ts`) ตั้ง `baseURL = config.api.bffUrl` และ `withCredentials: true` — **token/session อยู่ใน HTTP-only cookie ที่ BFF ออกให้** โค้ด FE ไม่แตะ token เลย (ไม่มี localStorage/sessionStorage token)
- login มี 2 ทาง:
  1. **Redirect flow**: `/login` (หรือ interceptor เมื่อ 401) พาไป `${bffUrl}/auth/login?redirectUrl=<origin>` ให้ BFF จัดการ OIDC แล้วเด้งกลับ
  2. **Form flow**: `/auth/login` โพสต์ username/password ตรงไป `POST {bffUrl}/auth/login` (`src/services/auth.service.ts` ใช้ fetch + `credentials: 'include'`)
- คอมเมนต์ในโค้ดระบุ IdP 2 ระบบ: **Eko** (ekoapp.com — ใช้กับ Store Partner; path auth จึง config ได้ผ่าน env) และ **Cognito**
- logout: `window.location.href = ${bffUrl}/auth/logout` (`src/services/api.ts`)

### 6.2 Refresh token flow (ใน `apiClient.ts`)

- Response interceptor: ถ้า 401 (และไม่ใช่ request ไป `/auth/refresh` เอง) → ตั้ง lock `isRefreshing`, ยิง `POST /auth/refresh`, ระหว่างนั้น request อื่นที่ 401 จะเข้า `failedQueue` แล้ว retry เมื่อ refresh สำเร็จ
- ถ้า refresh fail หรือ request ที่ retry แล้วยัง 401 (`_retry` flag) → redirect ไป BFF login พร้อม `redirectUrl`
- Request/response interceptor ยังผูก **global loading**: นับ `activeRequests` แล้วสั่ง `useLoadingStore.setLoading` (แสดง `LottieLoader` เต็มหน้า main)

### 6.3 Profile / Landing / Permission

- `/` เรียก `GET /users/current` → เก็บใน `userProfileStore` (zustand; มี field `group.smlLandingPage / sivLandingPage / sbpmLandingPage`)
- `getLandingPath()` เลือก landing ตาม app target + group ของผู้ใช้ → fallback `NEXT_PUBLIC_LANDING_PAGE` → `/main`
- **เมนู sidebar มาจาก API** `GET /menus` (ไม่ hardcode) → `menuHelper.transformAndSortMenuItems` แปลง+sort ตาม `sortOrder` แล้ว map icon ด้วย `iconMap`
- **Permission per URL**: `permissionStore` โหลด `GET /groups/current-user/permissions` แล้วให้ `hasPermission(targetUrl, 'canView'|'canManage'|'canExport'|'canOther')` — หน้าต่าง ๆ เช็คเองแล้ว render `AccessDenied` ถ้าไม่มีสิทธิ์
- `AuthContext` (`src/contexts/AuthContext.tsx`) มีอยู่แต่เป็น flow เก่า (เรียก `authService.getProfile`) — โค้ดปัจจุบันใช้ zustand stores เป็นหลัก
- Consent gate: `(main)/layout.tsx` ฝัง `ConsentPopupContainer` (บังคับ popup consent ประเภท applicant / store_partner / sub_area; ตัว store_employee ถูก comment ไว้)

---

## 7. โครงสร้าง src ส่วนที่เหลือ

### 7.1 `src/components/` (24 กลุ่ม)

| กลุ่ม | เนื้อหา |
|---|---|
| `Form/` | **Design system ภายใน** ห่อ PrimeReact: AutoComplete, Button, Calendar, CheckBox, DatePicker, Dropdown, FileUpload, FileView, GroupSelection, InputText, Layout(Container), MultiSelect, Password, RadioButton, TimePicker, ToggleSwitch |
| `Table/` | ตารางกลาง (`table.tsx`, `Column`), `table-action-button`, `table-status-chip` |
| `layout/` | `AppHeader`, `AppSider` (เมนู recursive จาก API, collapse ได้, active ตาม pathname), `Breadcrumb`, `LanguageSelector`, `UserProfile`, `I18nProvider` |
| `ConfirmDialog`, `ContentDialog`, `Modal`, `Toast`, `Tooltip` | dialog/แจ้งเตือนกลาง (ConfirmDialog มี mode confirm/alert ใช้ทั่วระบบ) |
| `ConsentPopup/` | `ConsentPopupContainer`, `ConsentStoreEmpPopupContainer`, `ConsentPopupWithNoteContainer` — popup PDPA หลัง login |
| `Investors/` | ฟอร์มผู้สนใจลงทุน: PersonalDataSection, ContactSection, InterestAreaForm/Section, ReserveAreaDialog, InvestorsSbpRegistrationForm, ConsentSection |
| `Permission/` | `AccessDenied` |
| `login/`, `GradientBackground`, `Carousel`, `welcomeSection`, `topbar` | องค์ประกอบหน้า login |
| `Loader/` | `LottieLoader` (global loading) |
| `UsernameWarningPopup/` | popup เตือนบัญชี username เก่ารูปแบบ `sXXXXXXX@7sbp.store` |
| `Stepper`, `SectionScroller`, `ColumnDropdown`, `Sbp/consent-popup`, `common/Logo`, `icon.tsx`, `icons/` | อื่น ๆ |

### 7.2 `src/hooks/`
- `useResponsive` — ตรวจ breakpoint
- `useScrollToError` — scroll ไปยัง field ที่ validate ไม่ผ่าน
- `investors/useInvestorForm` — logic ฟอร์มผู้สนใจลงทุน
- (hooks เฉพาะหน้าอยู่ในโฟลเดอร์ route เช่น `sbp/onboarding/hooks`, `extend-contract/_hooks`)

### 7.3 `src/services/` — รายการ API service ทั้งหมด (endpoint ของ BFF)

service กลาง (`src/services/`):

| ไฟล์ | Endpoint หลักที่เรียก |
|---|---|
| `api.ts` | `/auth/login` (redirect), `/auth/logout`, `GET /auth/profile`, `GET /main`, consent: `GET/POST /users/consents*`, `/applicants/{id}/consents`, `/users/consents/{init,policy,eligibility}`, `/store-employee/consent*` |
| `apiService.ts` | `GET /menus`; groups: `GET/POST/PUT/DELETE /groups`, `/groups/by-parent`, `/groups/subgroup`, `/groups/{id}/permissions`, `/groups/permissions/template`, `GET /groups/current-user/permissions`; `GET /auth/profile`, `GET /users/current` |
| `auth.service.ts` | `POST /auth/login` (username/password) |
| `resetPassword.service.ts` | `POST /auth/password-reset/request`, `/auth/reset-password`, `GET /auth/reset-password/{token}` |
| `register.service.ts` | `/registration`, `/identity-check/sp`, `/identity-check/pttor` |
| `address.service.ts` / `lookup.service.ts` / `commonCode.service.ts` | `/addresses`, `/lookups`, common code |
| `userRightsManagement.service.ts` | `/user-group-memberships` (+`/{id}`, `/user/{userId}`), `DELETE /users/{id}`, `DELETE /users/bulk` |
| `assistantManagerAssignments.service.ts` | `/employees/{userId}/stores`, `/stores/{storeId}/employees`, `/stores-list`, `POST /assistant-manager/assign` |
| `bellineeAuthorizations.service.ts` / `subAreaAuthorizations.service.ts` / `subAreaStore.service.ts` | `/bellinee/authorizations`, `/sub-area/authorizations`, `/store-service` |
| `bellineeConsent.service.ts` / `subAreaConsent.service.ts` | `GET /{nationalId}/consent/init`, `POST /{authorizationId}/consent-by-auth`, `/confirm/{token}` |
| `sbpConsent.service.ts` / `store-partner-consent.service.ts` | `/applicants/consent-filter`, `/applicants/workflow-status`, `/store-partner/consent`, `/store-partner/store-partner-data-change` |
| `evaluate.service.ts` | `/Evaluationprocess/{searchAssess,assessSave,assessSubmit,assessEvaluate/{id},assessEvaluate/scoreKey,recalculate,assessExport,assessCriteriafile/download,EvaluationformExport,storeManagementsearch,storeManagementexport}`, `/assessment/audit/{search,approves,export,{id}/detail,{id}/assessSave,{id}/recalculate,{id}/sendback/confirm,sendConclude,{ids}/exportEvaluationform}`, `/assessment/performance/exportExcel`, `/awardDivision/{exportGradeDivision,exportCollectDivisionReport}`, `/reportdivision/{exportDivisionAdmin,exportDivisionSbp}`, `/reportPtt/reportExport`, `DELETE /manage-import/deletereal` |
| `reportSpAdStatus.service.ts` | `/report-sp-ad-status`, `/common-code/list`, `{API_REPORT}/export` |
| `reportSpCooperation.service.ts` | `/docCooperation/*` ~20 endpoints (cooperationSearch/Detail/Topic/ApproveDoc/RequestorDoc/Export, docType, docStatus, filterOptions, approver list, codeRegion, codetypeShop ฯลฯ) |
| `storePartnerProfile.service.ts` + `sbp/storePartnerProfile-declare.service.ts` | **declare (แจ้งความสัมพันธ์)**: `/bff/relation/{common-codes,confirm,permissions,reply,reply/{empId},validate-person,validate-sbp,export}` |
| `interestInvestorSearch/Detail`, `crdManageApplicant`, `exportDataManagement`, `sbpServiceTemplate`, `juristic`, `label`, `pdpaExport` | ตามชื่อ (บางตัวยังเป็น template `/api/xx` ยังไม่ต่อ API จริง) |

service โดเมน SBP (`src/services/sbp/`):

| ไฟล์ | Endpoint หลัก |
|---|---|
| `investor-registration.service.ts` | `/bff/application/*`: `page1/init`, `page2/init`, `page3/init`, `short/init`, `init-from-investor`, `detail`, `search*` (applicant-by-name, applicant-status, approve, delete), `doWorkflowPage` (state machine ใบสมัคร), `file/{upload,delete,updateSeq}`, `fileTypeMapping`, `applicantDocumentBy{Type,InvestType}`, `applicantOtherDocument`, `masterData*` |
| `onboarding.service.ts` | `/onboarding`, `/search*`, `/detail/{init,save,next,cancel,file/upload,file/view}`, `/manage/{init,save}`, `/report/{application,send-interview-email}`, `/shared/{area,province,district,common-code}` |
| `store-partner-profile.service.ts` | `/store-partner-profile`, `/store-partner-info/{init,save,update,search,search-by-name,compare,file-info,upload-profile-image,view-profile-image}`, `/child-info/*`, `/activity-info/init`, `/store-partner-legal-entity/init`, `/consent*`, `/shared/{province,district,sub-district}` |
| `manage-executive.service.ts` | `/manage-executive` + `/search`, `/getDetail`, `/save`, `/delete`, `/getSharedData` |
| `main-remain.service.ts` | `GET /bff/backlog/pending` (งานคงค้าง) |
| `storeTransfer.service.ts` | `/bff/storeTranfer` (สะกดตามโค้ด) |
| `exportData.service.ts` | `/export-data`, `/report-master-list`, `/report-column-master-list`, `/common-code` |
| `storeInquiry.service.ts` | `PATCH store-inquiry/{orders}` ฯลฯ |
| `activity.service.ts` | `store/association/activities*` (รวม `PATCH .../delete`) |
| `investors.service.ts` | `POST investors/crd/export-report`, `export-contact-report` |
| `dataManagmentBlacklist.service.ts`, `DataManagmentJuristicGroup.service.ts`, `exportDataDeclare.service.ts` | blacklist / juristic group / export declare (`/bff/relation/export`) |

service ในโฟลเดอร์ route (`src/app/(main)/**/_services`, `services/`):

| กลุ่ม | Endpoint prefix |
|---|---|
| `contract/extend-contract/*/_services` | `/scm-extend-contract/{confirm-manage-sbp,verify-confirm-manage,consider-approve,unblock-contract,export-extend-contract}` |
| `store-transfer/approval/_services` | `/store-transfer/approval/{list,search,detail/{workflowTransactionId},workflow/action,workflow/initialize-transactions}` |
| `statement/services` (23 ไฟล์) | `/store-statement/{dropdown/subtype,form1/resolve,form1/popupCheckStampDuty,form1/rt040079/confirm,report/ej/download}` + logic export CSV/PDF (ฟอนต์ TH Sarabun ฝังในไฟล์) |
| `externalAudit/services`, `externalAuditLog/services` | `/store-external-audit/*` |
| `uploads` (ในตัว page) | `/store-uploads/{master/group-report,general/{latest,template,upload,job-status,export},mas-store-organize/{structure,individual}}` |
| `performance/*` (ในตัว page) | `/sales-summary`, `/sales-summary/export`, `/list-{month,year,zone,type-group}-…summary`, `/report-audit` |

### 7.4 `src/stores/` (Zustand)
- `loadingStore` — global loading flag (ผูกกับ axios interceptor)
- `userProfileStore` — โปรไฟล์ผู้ใช้ + group + landing pages
- `permissionStore` — permissions ต่อ targetUrl + `hasPermission()`

### 7.5 `src/contexts/`
- `ApiContext` — แจก axios instance ผ่าน `useApiClient()`
- `AuthContext` — auth flow เก่า (getProfile)
- `LayoutContext` — สถานะ layout (sidebar ฯลฯ)
- `HighlightedFieldsContext` — ไฮไลต์ field (ใช้กับหน้าเทียบ/ตรวจข้อมูล)

### 7.6 `src/lib/`
- `apiClient.ts` — axios กลาง (รายละเอียดในหัวข้อ 6)
- `validation/` — **mini validation framework**: `engine.ts` compile schema (JSON rule: required/pattern/min/max ฯลฯ + pattern registry email/hasUpper/numericOnly...) เป็น `RegisterOptions` ของ react-hook-form, `guards.ts`, `context.tsx`, `pathUtil(s).ts`, `_example.ts`

### 7.7 `src/types/` — TypeScript models แยกตามโดเมน (address, bellinee, commonCode, consent, declare, evaluate/ (12 ไฟล์), investors/, sbp/ (ครบทุก sub-domain), store-partner-profile, store-transfer, menu, pagination, permissions, userProfile, userGroup ฯลฯ)

### 7.8 `src/utils/`
- `dateUtil` / `mapAllDates` (แปลงวันที่ รวม ISO↔วันที่ไทย), `commonUtil`, `commonCodeMapping.util`, `inputTextUtil`, `normalizeEmptyToNull`, `object.util`, `table`, `validation.util`
- `menuHelper` (แปลงเมนู API → sidebar), `iconMap` (map ชื่อ icon จาก API → component), `landingPath.util`
- `workflow.ts` — `createHandleWorkflow()` helper กลางของ flow ใบสมัคร SBP: ผูก event `approve/sendback/save/submit/cancel/back` เข้ากับ ConfirmDialog ข้อความไทยมาตรฐาน แล้วเรียก `doWorkflowPage` (ข้อความยืนยัน เช่น "ท่านยืนยันส่งใบสมัคร Store Business Partner 7-Eleven", ตอบกลับภายใน 3 วันทำการ)
- `sbp-evaluate/utils`

### 7.9 i18n
- รองรับ **th (default `th-TH`) และ en (fallback `en-US`)** — แต่ไฟล์แปลมีเพียง ~39 key (ส่วนใหญ่ = ชื่อเมนู เช่น "หน้าหลัก", "สัญญาบริหารร้าน", "statement", "evaluation") ขณะที่ข้อความในหน้า ส่วนใหญ่ **hardcode ภาษาไทยตรงใน component** — i18n ยังใช้จริงแค่บางส่วน (เมนู/label ผ่าน `t()` ใน AppSider)
- มี `LanguageSelector` ใน layout

---

## 8. การทดสอบ

- **Jest 30** ผ่าน `next/jest` (`jest.config.js`) + `babel.config.jest.js` (`next/babel`), environment **jsdom** (url `http://localhost:3000`), coverageProvider v8
- `jest.setup.js` — โหลด `@testing-library/jest-dom` + **mock `HTMLCanvasElement.getContext/toDataURL`** (จำเป็นเพราะ jspdf/chart canvas)
- moduleNameMapper: `@/* → src/*`, ไฟล์ scss/css → `identity-obj-proxy`; patch `transformIgnorePatterns` ให้ transform ESM packages (`html-react-parser`, `domhandler`, `domelementtype`)
- **coverage ignore**: `src/components/` ทั้งหมด และ `src/app/example/` (วัด coverage เน้น services/utils/pages)
- เทสต์เขียนแบบ **colocated `.test.ts(x)` ประกบไฟล์จริง** เกือบทุก service/util/store/context + มี `src/__test__/` (เช่น `PerformanceQssiPage.test.jsx` — ถูก include ใน tsconfig ตรง ๆ) และ `_tests` ในบาง route; ใช้ `@testing-library/react`, `user-event`, `axios-mock-adapter`
- `__mocks__/fileMock.js` — mock ไฟล์ static; `test/consent-success.txt` — ตัวอย่าง JSON response ของ consent ไว้อ้างอิง
- `test:ci` — runInBand + coverage lcov → `coveragereport/` + รายงาน junit → `test-reports/` (ใช้กับ SonarQube ใน pipeline)

---

## 9. ข้อสังเกต / ประเด็นน่าสนใจ

1. **จุดเชื่อมกับระบบประกันรายได้ (K2/SBPGI)**: มีอยู่จุดเดียวที่ชัดเจน — หน้า `sbp/data-management/store-inquiry` มี `GuaranteeIncomeDetailSection.tsx` + `GuaranteeIncomeDetailPopup.tsx` เป็นตาราง+popup กรอก "รายละเอียดประกันรายได้" ของร้าน (field: `storeTypeId`, `empTypeId`, `affectedBranch` สาขาที่ได้รับผลกระทบ, `affectedDate`, `monthYear`, `guaranteeIncome` จำนวนเงิน, `split`, `remark`) — สอดคล้องแนวคิดร้านถูกกระทบจากสาขาเปิดใหม่ของ K2 แต่**ยังไม่มีโมดูล workflow อนุมัติเอกสารประกันรายได้แบบใน prototype** (ไม่พบหน้า/route ใดเกี่ยวกับเอกสาร ปย.1/อนุมัติ 5 ขั้นเลย) — ยืนยันว่า flow K2 เต็มรูปแบบเป็นของใหม่ที่จะเพิ่มเข้ามา
2. **สถาปัตยกรรม multi-tenant จาก codebase เดียว**: build 3 portal (sml/siv/sbpm) ด้วย env target — เมนู, landing page, สิทธิ์ ล้วนมาจาก BFF (dynamic) ทำให้ 3 แอปใช้หน้าเดียวกันแต่เห็นเมนูต่างกัน
3. **Static export ล้วน (SPA บน S3/CloudFront)** — ไม่มี SSR/API routes; ผลข้างเคียงคือ `middleware.ts` (clear cookies ที่ `/login`) ไม่ทำงานบน production S3 และการกันหน้า (auth guard) เป็น client-side ทั้งหมด โดยพึ่ง BFF cookie + 401-refresh-redirect ใน axios interceptor
4. **สองระบบ IdP**: คอมเมนต์ในโค้ดระบุ Eko (สำหรับ Store Partner — ekoapp.com) กับ Cognito path ต่างกัน จึงต้อง config auth path ผ่าน env; มี popup เตือนบัญชีอีเมลรูปแบบเก่า `s0000000@7sbp.store` ให้ผู้ใช้ไปแก้
5. **โฟลเดอร์/ไฟล์แปลก ๆ**: ไฟล์ `npm` (0 byte) และ `error_log.txt` (ข้อความ UTF-16 ของคำสั่ง `sbp-portal test jest TableHistoryData.test.tsx --coverage`) — เป็นขยะจากการ redirect output ผิดพลาด ไม่ได้ถูกใช้; `node_modules/` มีอยู่แต่โปรเจกต์นี้อยู่ *ใน* โฟลเดอร์ SBP ของ workspace prototype (ถูก clone มาเพื่อศึกษา)
6. **คุณภาพ/ความไม่สม่ำเสมอที่พบจริง**: route สะกดผิด `crate-contract` (create), endpoint `storeTranfer` (transfer), หลายหน้าใน `contract-management`/`legal-contract` ยังใช้ `mock.ts` ("จะเปลี่ยนเป็น API จริงทีหลัง"), service template ค้าง `/api/xx` หลายไฟล์ (`crdManageApplicant`, `exportDataManagement`, `sbpServiceTemplate`), README ระบุเวอร์ชัน Next เก่ากว่าจริง, root layout ยังใช้ title "Create Next App", `AuthContext` เป็นโค้ดตกค้างจาก flow เก่า, i18n ครอบคลุมแค่เมนู
7. **หน้า `/uploads` เป็น "dynamic form console" ขนาด ~2,000+ บรรทัดในไฟล์เดียว** รองรับการอัปโหลดไฟล์รายงานหลายประเภทแบบ config-driven (master จาก BFF) พร้อมติดตาม job แบบ polling — ใกล้เคียงแนวคิด batch-import ที่สุดในระบบนี้
8. **การสร้างเอกสารฝั่ง client หนักมาก**: statement/สัญญา/ใบแจ้งเกรด สร้าง PDF ด้วย jspdf (ฝังฟอนต์ TH Sarabun Base64 ~2 ไฟล์ใหญ่), รวมไฟล์ด้วย pdf-lib, แสดงด้วย pdfjs-dist, Excel ด้วย exceljs — ตรรกะรายงานจำนวนมากอยู่ฝั่ง frontend
9. **ครอบคลุมธุรกิจกว้างกว่าร้าน 7-Eleven SBP**: มีโมดูลของ Bellinee's, Franchise Sub Area, statement ต่างประเทศ (Cambodia/Laos), PTT OR (`/identity-check/pttor`, `reportPtt`) แสดงว่า portal นี้เป็นศูนย์รวมงาน Store Business Partner หลาย business unit
10. **ขนาด**: ไฟล์ TS/TSX ใน src = **1,131 ไฟล์**, หน้า (page.tsx) = **171 หน้า**, layout 9 ไฟล์, service กลาง ~40 ไฟล์ + service ใน route อีก ~40 ไฟล์
