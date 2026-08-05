# srm-sps-spsap-sbp-bff — เอกสารวิเคราะห์ Codebase

> เอกสารนี้สรุปจากการอ่าน source code จริงในโปรเจกต์ `/Users/bank_mac/gosoft/java/SBP/sbp-prototype/SBP/srm-sps-spsap-sbp-bff` (branch `main`) ทั้งหมด — ข้อความใดที่เป็นการตีความจากชื่อ/บริบทจะระบุกำกับไว้ว่า "ตีความ" หรือ "ไม่แน่ใจ"

---

## 1. ภาพรวม

โปรเจกต์นี้คือ **BFF (Backend For Frontend)** เขียนด้วย **NestJS 11 (TypeScript)** สำหรับระบบ **SBP (Store Business Partner)** ของ CP All / 7-Eleven — ชื่อ package ใน `package.json` คือ `sbp-cognito-bff` และ git remote คือ `git@bitbucket.org:gosoft-thailand/srm-sps-spsap-sbp-bff.git`

หน้าที่หลักของมันคือเป็น **ชั้นกลางระหว่าง Frontend (SBP Mall web) กับ backend microservices หลายตัว**:

- จัดการ **authentication ทั้งหมด** กับ AWS Cognito (OIDC/OAuth2) แล้วเก็บ token แบบเข้ารหัส (AES-256-GCM) ไว้ใน signed httpOnly cookie — frontend ไม่เคยเห็น token ตรง ๆ
- ตรวจ JWT (`id_token`) ทุก request ด้วย JWKS ของ Cognito
- **proxy / orchestrate** คำขอไปยัง backend ภายใน 6 ตัว (auth-backend, store backend, spm-backend, scm-backend, inv-backend, employee backend) โดยแนบ `x-api-key` และ header บริบทผู้ใช้ (`x-user-id`, `x-user-group-id`, `x-user-full-name`, `x-user-permissions`) ให้ backend
- ทำงานฝั่ง presentation บางส่วนเอง เช่น สร้างไฟล์ Excel (exceljs), รวมผล (aggregate) จากหลาย backend, mapping DTO

**BFF นี้ stateless — ไม่มีการต่อฐานข้อมูลเองเลย** (มี dependency `typeorm`/`pg` ใน package.json และมีไฟล์ entity อยู่ใน `modules/export-data/entities/` แต่ไม่มีการ register `TypeOrmModule` หรือใช้ `InjectRepository` ที่ใดในโค้ด — ดูข้อสังเกตข้อ 10)

### ชื่อ/คำย่อที่พบในโค้ด

| คำย่อ | ความหมายที่ยืนยันได้จากโค้ด | หลักฐาน |
|---|---|---|
| SBP | Store Business Partner | ชื่อ package `sbp-cognito-bff`, ชื่อ consent เช่น `SBP Store Partner` ใน `common/constant/constant.ts` |
| SRM / SPS / SPSAP | prefix ของกลุ่ม repository ใน Bitbucket `gosoft-thailand` (เช่น repo Java เดิม `srm-sps-spsap-smlws`) — **ความหมายเต็มไม่ปรากฏในโค้ด ไม่ยืนยัน** | git remote, comment ใน `relation.controller.ts` |
| BFF | Backend For Frontend | comment หลายแห่ง เช่น `relation.controller.ts`: "FE ใหม่เรียก BFF → BFF เรียก spm-backend" |
| auth-backend / ABS | backend สิทธิ์/ผู้ใช้ (users, groups, menus, lookups) — `menus.service.ts` log ว่า "Forwarding request to ABS" (ตีความ: Authorization Backend Service) | `API_AUTHORIZATION_BACKEND_URL` |
| SBS | store backend service (ตัวแปรในโค้ดชื่อ `sbsApiBaseUrl` ชี้ไป `API_STORE_BACKEND_URL`) — ความหมายเต็มไม่ระบุในโค้ด | `statement.service.ts`, `performance.service.ts` |
| spm-backend | Store Partner Management backend | comment ใน `relation.service.ts` ("เรียก spm-backend ผ่าน StorePartnerClientService (port 3005)"), `cm.constant.ts` |
| scm-backend / FCM | backend สัญญา/ต่อสัญญา (contract, extend-contract) — `contract.controller.ts`: "forward ข้อมูลทำสัญญาไป upsert ที่ scm-backend (ฝั่ง FCM)" | `API_CONTRACT_BACKEND_URL` |
| inv-backend | Investor backend (ผู้สมัคร/นักลงทุน) | `cm.constant.ts` (`CmBackendModule.INV`), `API_INVESTOR_BACKEND_URL` |
| smlws | ชื่อ Java BE เดิม (`srm-sps-spsap-smlws`) ที่ module `relation` ถูก migrate มาจาก | comment ใน `relation.controller.ts` |
| CM | โมดูลอัปโหลดไฟล์กลาง (content/file management) ที่มีอยู่ทั้งใน inv-backend และ spm-backend — ความหมายเต็มไม่ระบุ | `cm.constant.ts` |

### ความสัมพันธ์กับระบบประกันรายได้ (K2/SBPGI)

BFF นี้คือ "ระบบปัจจุบัน" ของ SBP Mall — **ไม่พบโค้ดใด ๆ เกี่ยวกับประกันรายได้ / income guarantee / K2 / FGI / FCS ในโปรเจกต์นี้เลย** (grep คำว่า guarantee, ประกันรายได้, income แล้วพบเพียง field `income` ใน DTO ประวัติธุรกิจผู้สมัคร) — รายละเอียดเพิ่มเติมดูข้อ 10

---

## 2. Tech Stack

### Framework และ runtime

| ส่วน | เทคโนโลยี | เวอร์ชัน |
|---|---|---|
| Runtime | Node.js (Docker base `node:20.18.1-alpine`) | 20.18.1 |
| Framework | NestJS (`@nestjs/common`, `@nestjs/core`, `@nestjs/platform-express`) | ^11.1.27 |
| ภาษา | TypeScript (target es2022, commonjs) | ^5.7.3 |
| HTTP server | Express (ผ่าน `@nestjs/platform-express`) | — |

### Dependencies หลัก (จาก package.json) และการใช้งานจริง

| Dependency | เวอร์ชัน | ใช้ทำอะไร (ยืนยันจากโค้ด) |
|---|---|---|
| `@nestjs/axios` + `axios` | ^4.0.1 / ^1.16.0 | HTTP client เรียก backend ภายในทั้งหมด (ผ่าน `ClientServiceAbstract`) |
| `@nestjs/passport` + `passport` | ^11.0.5 / ^0.7.0 | โครง auth guard/strategy |
| `passport-openidconnect` | ^0.1.2 | OIDC login flow กับ AWS Cognito (`OidcStrategy`) |
| `passport-jwt` | ^4.0.1 | ตรวจ `id_token` จาก cookie ทุก request (`JwtStrategy`) |
| `jwks-rsa` | ^3.2.2 | ดึง public key จาก `{AUTH_ISSUER}/.well-known/jwks.json` มา verify RS256 |
| `@nestjs/jwt` | ^11.0.2 | `JwtService.sign` ใน `CookieUtilService` (มีเมธอด `jwtSign` — ใช้เซ็น JWT ภายใน) |
| `cookie-parser` | ^1.4.7 | อ่าน signed cookies (เก็บ token) |
| `cookie-session` | ^2.1.1 | session ชั่วคราวชื่อ `oidc-flow-state` ระหว่าง OIDC redirect flow |
| `class-validator` + `class-transformer` | ^0.14.4 / ^0.5.1 | Global `ValidationPipe` (whitelist + transform + forbidNonWhitelisted) และ `MapperService` |
| `@nestjs/config` | ^4.0.4 | `ConfigModule.forRoot({isGlobal:true})` — แต่ค่า config จริงอ่านผ่าน `AppConfigService` ที่อ่าน `process.env` ตรง ๆ (ใช้ dotenv) |
| `@nestjs/cache-manager` + `cache-manager` | ^3.1.3 / ^7.2.8 | `CacheModule.register({isGlobal:true, ttl:60000, max:100})` — พบการใช้ `CacheInterceptor` จริงเพียงที่เดียวคือ `store-inquiry.controller.ts` |
| `exceljs` | ^4.4.0 | สร้าง/อ่าน Excel ฝั่ง BFF: `export-data`, `statement`, `report-sp-ad-status`, `store-association-activity`, `onboarding` |
| `multer` | ^2.2.0 | รับไฟล์อัปโหลด (`FileInterceptor`) แล้ว forward เป็น multipart ไป backend |
| `qs` | ^6.15.2 | serialize query string |
| `pg` + `typeorm` + `@nestjs/typeorm` | ^8.16.3 / ^0.3.30 / ^11.0.2 | **ประกาศไว้แต่ไม่ได้ใช้งานจริง** — ไม่มี `TypeOrmModule` / `InjectRepository` / `new Pool` ที่ใดในโค้ด (มีเพียงไฟล์ entity ใน `export-data/entities/` ที่ import decorator ของ typeorm) |
| `rxjs` | ^7.8.1 | `firstValueFrom` ครอบ HttpService, interceptors |

**ไม่มี** message queue, Redis, GraphQL, Swagger/OpenAPI, Prisma (README กล่าวถึง Prisma แต่เป็น boilerplate ของ template — ไม่มีโฟลเดอร์ `database/` จริง)

### Dev dependencies เด่น

Jest 30 + ts-jest (unit test, coverage v8), `jest-junit` (รายงาน CI), supertest (มีใน dev deps แต่ไม่มีโฟลเดอร์ e2e จริง), ESLint 9 (flat config `eslint.config.mjs`) + typescript-eslint + prettier

`overrides` ใน package.json ตรึงเวอร์ชันแพ็กเกจย่อยหลายตัว (fast-xml-parser, minimatch, path-to-regexp, lodash, form-data, multer) — ตีความว่าเพื่อปิด CVE ตามผล security scan (สอดคล้องกับไฟล์ `.trivyignore` ที่ ignore `CVE-2026-48779` ของ `ws` ที่มากับ Dynatrace agent)

---

## 3. วิธีรัน / สคริปต์ / CI

### npm scripts

| Script | คำสั่ง / หน้าที่ |
|---|---|
| `build` | `nest build` → คอมไพล์ลง `dist/` |
| `start` / `start:dev` / `start:debug` | `nest start` (ปกติ / `--watch` / `--debug --watch`) |
| `start:prod` | `node dist/main` |
| `format` | prettier เขียนทับ `src/**/*.ts`, `test/**/*.ts` |
| `lint` | eslint `{src,apps,libs,test}/**/*.ts --fix` |
| `test` / `test:watch` / `test:cov` / `test:debug` | jest unit tests (testRegex `.*\.spec\.ts$`, rootDir = `src`) |
| `test:e2e` | `jest --config ./test/jest-e2e.json` — **โฟลเดอร์ `test/` ไม่มีอยู่จริงใน repo** (มีแต่ `test.zip` ที่ root) ดังนั้นสคริปต์นี้รันไม่ได้ตามสภาพปัจจุบัน |
| `test:ci` | jest แบบ CI: `--runInBand --forceExit --collectCoverage` (lcov+text → `./coveragereport`), reporter `jest-junit` (output `test-reports`), `--bail` |

รัน local: ต้องมีไฟล์ env (มี `.env.local` ตัวอย่างอยู่ — ดูข้อ 4) แล้ว `npm run start:dev` — app ฟังที่ `PORT` (default 3000)

### Dockerfile (multi-stage, comment เป็นภาษาไทย)

1. **build stage** — `node:20.18.1-alpine`, `apk upgrade`, `npm ci` (mount `.npmrc` เป็น BuildKit secret เพื่อไม่ให้ credential ติดใน image), `npm run build`, แล้ว `npm prune --omit=dev`
2. **runtime stage** — alpine เดิม, **ลบ npm/npx ออกจาก image** (ลด CVE), **ติดตั้ง Dynatrace OneAgent** (`COPY --from=lss67296.live.dynatrace.com/linux/oneagent-codemodules-musl:nodejs`), คัดลอกเฉพาะ `node_modules`, `dist`, `package.json` เป็น owner `node`, รันด้วย user `node`, `EXPOSE 3000`, `HEALTHCHECK` ยิง `http://localhost:3000/api/health` (หมายเหตุ: ตัว app เสิร์ฟ `/health` ไม่มี prefix `api` — global prefix ถูก comment ไว้ใน `main.ts` ดังนั้น path ใน HEALTHCHECK อาจไม่ตรงกับ route จริง เว้นแต่มี reverse proxy เติม `/api` — ไม่แน่ใจ), CMD `node dist/main`

### bitbucket-pipelines.yml

ทั้งหมด **import จาก pipeline template กลาง** `srm-sps-spsap-pipeline-template` (ไม่เห็น step ภายในจาก repo นี้ — เห็นแต่ comment ภาษาไทยอธิบาย flow):

| Trigger | Template ที่ import | หน้าที่ (ตาม comment) |
|---|---|---|
| branch `feature/*` | `feature-branch-javascript-pipeline` | Security Scan โค้ดของ dev |
| PR `feature/*` → main | `feature-pull-request-merge-to-main-javascript-pipeline` | Scan ด้วย SonarQube |
| branch `main` | `main-branch-pipeline` | build container + sign signature ด้วย AWS profile |
| branch `dev` | `dev-branch-ecs-pipeline` | ตรวจลายเซ็น + deploy ไป DEV (**ECS**) |
| branch `uat` | `uat-branch-ecs-pipeline` | deploy ไป UAT |
| branch `production` | `production-branch-ecs-pipeline` | deploy Production (ต้องแนบหลักฐาน QC PASS) |

มี `scan.bat` ที่ root (สคริปต์ scan ฝั่ง Windows) และ `.trivyignore` — แสดงว่าใช้ Trivy scan ด้วย

---

## 4. Configuration / Environment Variables

ค่า config รวมศูนย์ที่ `src/config/app.config.service.ts` (`AppConfigService`, provider แบบ `@Global()` ผ่าน `AppConfigModule`) — อ่าน `process.env` ผ่าน dotenv โดยตรง มี default fallback ทุกตัว interface อยู่ใน `src/config/app-config.interfaces.ts`

### กลุ่ม Authentication (AWS Cognito)

| ตัวแปร | ความหมาย |
|---|---|
| `AUTH_CLIENT_ID` / `AUTH_CLIENT_SECRET` | OAuth2 client ของ Cognito app client |
| `AUTH_ISSUER` | issuer URL เช่น `https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_fsgFhUG9H` (ใช้ต่อ `/.well-known/jwks.json` ด้วย) |
| `AUTH_DOMAIN` | Cognito hosted domain (`cpalloidcuat.auth.ap-southeast-1.amazoncognito.com` ใน .env.local) — ใช้สร้าง `/oauth2/authorize`, `/oauth2/token`, `/oauth2/userinfo`, `/logout` |
| `AUTH_CALLBACK_URL` | redirect URI ของ BFF (`/auth/callback`) |
| `AUTH_LOGOUT_URL` | URL ที่ Cognito redirect ไปหลัง logout (ใน .env.local ชี้ `https://alloauthdev.cpall.co.th/cgi/logout`) |

### กลุ่ม Backend service URLs (6 backend, แต่ละตัวมี URL + ชื่อ header key + ค่า key)

| Prefix ตัวแปร | Backend | Default URL |
|---|---|---|
| `API_AUTHORIZATION_BACKEND_*` | auth-backend (ABS) — users/groups/menus/lookups/สิทธิ์ | `http://localhost:3003` |
| `API_STORE_BACKEND_*` | store backend (SBS) — ข้อมูลร้าน, statement, ประเมินร้าน | `http://localhost:3004` |
| `API_STORE_PARTNER_BACKEND_*` | spm-backend — โปรไฟล์ Store Partner (comment ในโค้ดระบุ port 3005 แต่ default ใน config เป็น 3003) | `http://localhost:3003` |
| `API_CONTRACT_BACKEND_*` | scm-backend — สัญญา/ต่อสัญญา/โอนร้าน (FCM) | `http://localhost:3006` |
| `API_INVESTOR_BACKEND_*` | inv-backend — ผู้สมัคร/นักลงทุน/blacklist (ใน .env.local ชี้ `https://sbp-api-dev.cpall.co.th/api/v1/investor`) | `http://localhost:3007` |
| `API_EMPLOYEE_BACKEND_*` | employee backend — ข้อมูลพนักงาน (ใช้ใน module relation) | `http://localhost:3008` |

แต่ละกลุ่มมี `..._URL`, `..._KEY_NAME` (default `x-api-key`), `..._KEY_VALUE` และมี `API_CONNECTION_TIMEOUT` กลาง (default 5000 ms)

### กลุ่ม Security / Cookie / อื่น ๆ

| ตัวแปร | ความหมาย |
|---|---|
| `JWT_SECRET`, `JWT_EXPIRATION` | เซ็น JWT ภายใน (`CookieUtilService.jwtSign`) |
| `ENCRYPTION_SECRET`, `ENCRYPTION_SALT` | คีย์ AES-256-GCM (scrypt) เข้ารหัส token ใน cookie |
| `DATA_ENCRYPTION_SECRET` | คีย์เข้ารหัสข้อมูล sensitive ที่แชร์ข้าม service (id_card, emp_id — ตาม comment ใน interface) |
| `COOKIE_SECRET`, `COOKIE_EXPIRATION` (default 2 วัน), `COOKIE_SECURE` | signed cookie + cookie-session |
| `CORS_ORIGINS` | รายการ origin คั่น comma |
| `NODE_ENV` | `local` / `development` / `uat` / `production` (มีผลกับ `sameSite` cookie, trust proxy) |
| `PORT` | พอร์ต (default 3000) |
| `STORE_DOMAIN` | อยู่ใน config (`store.domain`) — **ไม่พบการใช้งานที่อื่นในโค้ด** |
| `LOG_COLOR` | เปิดสี ANSI ใน `MyLogger` |
| `DOWNSTREAM_TIMEOUT_MS` | timeout เรียก backend ใน `uploads.service.ts` (default 600000) |
| `GET_EMPLOYEE_BY_STOREID` | base URL เฉพาะกิจใน `assistant-manager.service.ts` (เรียก `${GET_EMPLOYEE_BY_STOREID}/listEmp`) — อ่าน process.env ตรง ๆ นอก config กลาง |

⚠️ **`.env.local` ถูก commit เข้า repo พร้อมค่า client secret / API key / JWT secret จริงของ environment dev/uat**

---

## 5. โครงสร้าง `src/`

```
src/
├── main.ts                  # bootstrap: MyLogger, body limit 100MB, ValidationPipe, CORS,
│                            # ResponseInterceptor, HttpExceptionFilter, cookie-parser,
│                            # cookie-session (oidc-flow-state), passport init
├── app.module.ts            # root module — import ~54 module + CacheModule global,
│                            # ผูก HttpContextMiddleware ทุก route
├── app.controller.ts        # GET /health → "health check status 200"
├── app.service.ts
├── common/
│   ├── client-services/     # ชั้นเรียก backend ภายใน (หัวใจของ BFF)
│   │   ├── client-service.abstract.ts   # get/post/put/patch/delete/postFile/getFile/postStream
│   │   │                                # + CustomHttpException แปลง error จาก axios
│   │   ├── base-client.service.ts       # ต่อจาก abstract
│   │   ├── http-client.service.ts       # client เปล่า (ไม่ตั้ง baseUrl/key) — ผู้เรียกประกอบ URL เอง
│   │   ├── authorization-client.service.ts  # → auth-backend (ตั้ง x-api-key + baseUrl ตอน onModuleInit)
│   │   ├── store-client.service.ts          # → store backend (SBS)
│   │   ├── store-partner-client.service.ts  # → spm-backend
│   │   ├── contract-client.service.ts       # → scm-backend
│   │   ├── investor-client.service.ts       # → inv-backend
│   │   ├── employee-client.service.ts       # → employee backend
│   │   ├── cooperation-client.service.ts    # → store backend (ใช้ config.api.store)
│   │   ├── evaluate-client.service.ts       # → store backend; เลือก auth แบบ Bearer (ถอดรหัส token
│   │   │                                    #   จาก cookie) หรือ x-api-key ให้อัตโนมัติ
│   │   └── client-service.module.ts     # @Global() export ทุก client
│   ├── constant/constant.ts     # enum TYPE — ชื่อชุด consent ("SBP Investor", "SBP Privacy Notice" ฯลฯ)
│   ├── core/
│   │   ├── http-context.ts      # AsyncLocalStorage เก็บ requestId (UUID ต่อ request)
│   │   └── logger.ts            # MyLogger — custom LoggerService ใส่สี + requestId
│   ├── dto/                     # DTO กลาง: user, user-group, province/district/sub-districts,
│   │                            # postal-code, dropdown-option, lookup-value, base-response ฯลฯ
│   ├── encryption/              # EncryptionService — AES-256-GCM (iv12+tag16, base64url, scrypt key)
│   ├── filters/http-exception.filter.ts   # แปลง error → {success:false, data:null, error:{code,message}, requestId}
│   ├── interceptors/
│   │   ├── response.interceptor.ts  # ห่อ response → {success:true, data, requestId} (ข้าม StreamableFile)
│   │   └── logging.interceptor.ts   # log request/response + เวลา (ประกาศไว้ ไม่ได้ติด global ใน main.ts)
│   ├── mapper/mapper.service.ts     # plainToClass + excludeExtraneousValues (toDto/toDtos)
│   ├── middleware/http-context.middleware.ts  # ครอบทุก request ด้วย HttpContext.runInContext
│   └── utils/
│       ├── cookie-util.service.ts   # encryptToken/decryptToken/jwtSign
│       ├── declare-crypto.util.ts   # crypto util เฉพาะระบบ Declare (relation)
│       └── error-handler.util.ts
├── config/
│   ├── app-config.interfaces.ts # interface + enum NodeEnvironment
│   ├── app.config.service.ts    # อ่าน process.env ทั้งหมด (ดูข้อ 4)
│   └── app-config.module.ts     # @Global()
└── modules/                     # 55 โฟลเดอร์ feature module (ดูข้อ 6)
```

สถิติ: ไฟล์ `.ts` ใน src ทั้งหมด 699 ไฟล์ (เป็น `.spec.ts` 212 ไฟล์), controller 59 ไฟล์, endpoint รวม **~440** (นับจาก decorator `@Get/@Post/@Put/@Patch/@Delete` — มี 1–2 ตัวเป็นบรรทัด comment จึงอาจคลาดเคลื่อนเล็กน้อย)

Path aliases (tsconfig): `@common/*`, `@modules/*`, `@utils/*`, `@database/*` (+ jest moduleNameMapper `src/`, `common/`, `config/`, `modules/`)

---

## 6. รายการ Modules ทั้งหมด (55 โฟลเดอร์ / 54 ถูก register)

> ทุก controller ติด `@UseGuards(AuthGuard('jwt'))` ยกเว้นที่ระบุว่า **[ไม่มี guard]**
> คอลัมน์ "Backend" = ระบบปลายทางที่ service เรียกต่อ (ดูคำย่อในข้อ 1/8)
> คำอธิบาย endpoint เป็นการตีความจากชื่อ method/path/DTO — โค้ดส่วนใหญ่เป็น proxy ที่ไม่มี business logic ฝั่ง BFF (หลาย module มี comment ยืนยัน เช่น relation: "ไม่มี business logic เอง ทุกอย่างอยู่ที่ spm-backend")

### 6.1 กลุ่ม Auth / ผู้ใช้ / สิทธิ์ (→ auth-backend + Cognito)

#### `auth` — จัดการ login/logout กับ AWS Cognito
| Method | Path | หน้าที่ |
|---|---|---|
| GET | `/auth/login` | `OidcAuthGuard` redirect ไปหน้า login ของ Cognito (เก็บ `redirectUrl` ใน session) |
| GET | `/auth/callback` | รับ code จาก Cognito → เข้ารหัส id/access/refresh token → set signed httpOnly cookies (`ID_TOKEN`, `ACCESS_TOKEN`, `REFRESH_TOKEN`) → redirect กลับ URL เดิม |
| POST | `/auth/refresh` | ใช้ refresh_token จาก cookie ขอ token ใหม่จาก Cognito แล้ว set cookie ใหม่ |
| GET | `/auth/logout` | ลบ cookies + คืน `logoutUrl` ของ Cognito (`https://{domain}/logout?client_id=...&logout_uri=...`) ให้ FE redirect เอง |
| GET | `/auth/cognito-profile` | เรียก `oauth2/userInfo` ของ Cognito คืนโปรไฟล์ (มี custom attrs: `custom:EmployeeID`, `custom:EmployeeType`, `custom:JobCode`) |
| GET | `/auth/profile` | คืน `req.user` (AuthUserDto ที่ผ่าน JwtStrategy.validate แล้ว) |

โครงสร้างย่อย: `strategies/` (`jwt.strategy.ts`, `oidc.strategy.ts`), `guards/` (`base.guard.ts` factory, `jwt-auth.guard.ts`, `oidc.guard.ts`), `auth.constants.ts` (ชื่อ cookie)

#### `users` — ข้อมูลผู้ใช้ + consent (→ auth-backend `/users`, `/consents`; Cognito userinfo)
| Method | Path | หน้าที่ |
|---|---|---|
| GET | `/users` | ค้น user (ผ่าน `findByIdList`/`by-name-group` ตาม service) |
| GET | `/users/current` | user ปัจจุบันจาก JWT |
| GET | `/users/:id` · `/users/by-email/:email` · `/users/by-nationalId/:nationalId` | ค้น user รายคน |
| DELETE | `/users/:id` · `/users/bulk` | ลบ user (เดี่ยว/หลายคน) |
| GET | `/users/consents/init` · `/users/:userId/consents/init` · `/users/consents/eligibility` | สถานะ consent ตามประเภท (enum `TYPE`) |
| POST | `/users/consents` | บันทึก consent |
| GET | `/users/consents/policy` | **[ไม่มี guard — public]** ดึงนโยบาย consent (`users-public.controller.ts`) |

`UsersService.validate(payload)` คือจุดที่ JwtStrategy ใช้ map ตัวตน Cognito → user ในระบบ (เรียก auth-backend)

#### `groups` — กลุ่มผู้ใช้/สิทธิ์ (→ auth-backend `/groups`)
CRUD กลุ่ม: `POST/GET /groups`, `GET /groups/by-parent`, `GET/PUT/DELETE /groups/:id`, `POST /groups/subgroup` + สิทธิ์: `GET /groups/current-user/permissions`, `GET /groups/permissions/template`, `GET/PUT /groups/:groupId/permissions`

#### `userGroupMembers` — สมาชิกกลุ่ม (→ auth-backend `/user-group-memberships`)
`GET /user-group-memberships`, `GET /user-group-memberships/user/:userId`, `POST` (สร้าง user พร้อมกลุ่ม), `PUT /:id`

#### `menus` — เมนูตามสิทธิ์ผู้ใช้ (→ auth-backend `/menus`)
`GET /menus` — ส่ง userId ไปให้ ABS คืนเมนู

#### `lookups` — ค่า lookup (→ auth-backend `/lookups`)
`GET /lookups?parentName=...`

#### `common-code` — master common code (→ auth-backend `/common-code`)
`GET /common-code/list` (มีเงื่อนไข filter)

#### `addresses` — ที่อยู่ไทย (→ auth-backend `/addresses`)
`GET /addresses/provinces|districts|sub-districts|postcodes`

#### `sub-area-authorizations` — มอบอำนาจผู้ดูแล Sub Area (→ auth-backend `/sub-area/authorizations`)
CRUD + workflow: `POST/GET /sub-area/authorizations`, `POST .../verify-employee`, `GET .../screenings`, `GET .../screenings/:id`, `GET/PUT/DELETE .../:id`, `PUT .../:id/approve`, `PUT .../:id/return` (อนุมัติ/ตีกลับ)

#### `bellinee-authorizations` — มอบอำนาจร้าน Bellinee (เบลลินี่) (→ auth-backend `/bellinee/authorizations`)
โครงเดียวกับ sub-area: CRUD + screenings + approve/return

### 6.2 กลุ่มข้อมูลร้านและบริการร้าน (→ store backend SBS เป็นหลัก)

#### `store-service` — โครงสร้างพื้นที่/ร้าน (→ auth-backend `/store-service`)
`GET /store-service/sub-areas`, `GET .../sub-areas/:sub_area_id/stores`, `POST .../sub-areas/stores`, `GET .../zones`, `GET .../zones/:zone_id/stores`, `POST .../zones/stores`, `GET .../employees/by-email/:email`

#### `assistant-manager` — ตั้งผู้ช่วยผู้จัดการร้าน (→ auth-backend `/store-service/...` + env `GET_EMPLOYEE_BY_STOREID`)
`GET /stores/:storeId/employees`, `GET /stores-list` (ร้าน SBP ของ franchisee), `POST /assistant-manager/assign`

#### `statement` — รายงาน statement ร้าน (→ store backend `/statement/*`)
18 endpoints ใต้ `/store-statement`: dropdown ร้าน/ประเภทรายงาน/subtype (PTT), `POST search-report`, ดูไฟล์ (`view-file`, `view-file/stream/:id`, `preview-csv/:id`), ดาวน์โหลด EJ (`report/ej/download`), รายงาน daily P&L, pre-statement, ตรวจอากรแสตมป์ (`form1/popupCheckStampDuty`), ยืนยันแบบฟอร์ม `form1/rt040079/confirm`, `merge-file`, log การ export ให้ external audit ฯลฯ — บาง endpoint ใช้ exceljs ฝั่ง BFF

#### `performance` — รายงานผลประกอบการ/ยอดขายร้าน (→ store backend `/performance/*`)
13 endpoints ใต้ `/store-performance`: สรุปยอดขายรายปี/เดือน/ประเภท/โซน/type-group, `POST sales-summary` + export, รายงาน QSSI (`qssi-type-list`, `report-qssi`), `report-audit`, `report-open-store`(+count), `report-call-complaint`

#### `uploads` — อัปโหลดไฟล์นำเข้าข้อมูลร้าน (→ store backend `/uploads/*` + auth-backend `/master/sync-store-organize`)
`GET /store-uploads/master/group-report` (dropdown), `POST /general/upload` (multipart, มี callback `/general/upload-callback`), `GET /general/job-status`, `POST /general/template`, `GET /general/latest`, `GET /general/export`, `GET /mas-store-organize/structure|individual` — หลังอัปโหลด mas_store_organize จะ sync ไป auth-backend ด้วย

#### `confirm-import` — ยืนยันข้อมูลที่นำเข้า (→ store backend `/confirm-import/*`)
`GET /store-confirm-import/init`, `POST /search`, `POST /confirm`, `POST /delete`, `GET /file/view`

#### `external-audit` — ส่ง statement ให้ผู้ตรวจสอบภายนอก (→ store backend `/external-audit/*`) **[ไม่มี guard ทั้ง controller]**
10 endpoints ใต้ `/store-external-audit`: `insertAgreeStmtFile`, `getCountHistoryExportStmtFile`, `getHistoryExportStmtFileToExternalAudit`, `getStorePartnerStore`, `listReportStmtFile`, `getStorePartner`, `updateAuditEmail`, `exportStmtFileToExternalAudit`, `getReminderTo`, `getCommonCodeList` — ระบุตัวผู้ใช้ผ่าน query `userId` (ดูข้อสังเกตด้านความปลอดภัยข้อ 10)

#### `doc-cooperation` — เอกสารขอความร่วมมือร้าน (→ store backend `/docCooperation/*`)
22 endpoints ใต้ `/docCooperation`: master (storeActive, docType, docStatus, cooperationTopic), ค้นหา (`cooperationSearch`, `filterOptions`), รายละเอียด + ขั้นตอนปัจจุบัน (`cooperationDetail`, `currentStepCooperation`, `cooperationApproverList`, `searchApproverList`), ตรวจสิทธิ์แสดงผล (`checkCreateDepartment`, `checkDocType`, `checkDisplayPart`), การทำรายการ (`cooperationRequestorDoc` สร้าง/แก้เอกสาร, `cooperationApproveDoc` อนุมัติ, `cooperationConfirmDoc` ยืนยัน), export (`exportCooperationReport`, `exportSummary`, `cooperationExport`)

#### `store-inquiry` — สอบถาม/จัดการข้อมูลร้าน (→ auth + store + spm backends)
18 endpoints ใต้ `/store-inquiry`: ตัวเลือกค้นหา, ค้นหาออเดอร์ (`/search`), ค้นหาร้าน (`/store/search`, `/store/address/:storeId`, `/store/active-sbp`), นิติบุคคล (`/juristic`, `/juristic/:juristicId`), การบริหารร้าน (`/store-management/:storeId`), ที่อยู่ (district/sub-district), `store-partner`, `store-ref`, `new-store-transfer`, รายละเอียดออเดอร์ (`/detail/:orderId`, `/detail/form-options`), `POST /store-inquiry` (สร้าง), `PUT` (แก้ไข), `PATCH /:orders` (ลบ) — เป็น module เดียวที่ใช้ `CacheInterceptor`/`CacheTTL`

#### `store-association-activity` — กิจกรรมชมรม/สมาคมร้านค้า (→ auth + store + spm + inv backends)
12 endpoints ใต้ `/store/association/activities`: ค้นหา + form options, ผู้รับผิดชอบ (`responsible-users`), ดู/สร้าง/แก้/ลบกิจกรรม (`view/:activityId`, `create`, `PUT /:activityId`, `PATCH delete`, `detail/:activityId`), แนบไฟล์ (`attachments/:activityId/:attachmentId/download`, `POST view/save` แบบ multipart), export Excel (`export/:activityId/:activityType` — ใช้ exceljs + helper style ใน `report/`)

#### `label` — ป้าย/label ร้าน (→ store + spm backends)
`GET /label/init` (รวม dropdown: date_type_label, address_type_label จาก spm + area จาก store), `GET /label/filter`

#### `sap` — อัปโหลดไฟล์ CM Add ไป SAP interface (→ store backend `/api/sap`) **[ไม่มี guard]**
`POST /sap/upload-cmadd` — **⚠️ `SapModule` ไม่ได้ถูก import ใน `app.module.ts` — เป็น dead code, endpoint นี้ไม่ active**

### 6.3 กลุ่มประเมินร้าน (Evaluation/Assessment — ทั้งหมดผ่าน `EvaluateClientService` → store backend; แนบ Bearer token ของผู้ใช้หรือ x-api-key)

#### `assessment` — ผลประเมิน + audit (→ store backend `/assessment/*`)
13 endpoints ใต้ `/assessment`: `GET dvName`, `POST audit/search`, `POST performance/search` + `performance/exportExcel`, ราย evaluateId: `GET audit/:evaluateId/detail`, `POST .../recalculate`, `.../assessSave`, `.../sendback/confirm` (ตีกลับ), `.../approve`, `.../exportEvaluationform`, และ `POST audit/approves` (อนุมัติหลายรายการ), `audit/sendConclude`, `audit/export`

#### `evaluate-assessment` — แจ้งผลประเมิน (→ store backend `/informEvaluate/*`)
`GET /informEvaluate/stores`, `types-group`, `pseudonym-group` (กลุ่มนามแฝงผู้ประเมิน), `searchEvaluation-round`, `PUT note/update`, `POST two` / `midyear` (รอบประเมิน), `pseudonym-group-names`

#### `evaluation-process` — กระบวนการประเมิน (→ store backend `/evaluationProcess/*`)
15 endpoints: `checkPermission`, จัดการผู้ใช้ในกลุ่มนามแฝง (`pseudonym-group/:groupId/users`), ค้นหา/บันทึก/ส่งแบบประเมิน (`searchAssess`, `assessEvaluate/scoreKey`, `assessSubmit`, `assessEvaluate/:evaluateId`, `assessSave`, `recalculate`), ไฟล์เกณฑ์ (`assessCriteriafile` + download), export (`EvaluationformExport`, `assessExport`, `storeManagementexport`), `storeManagementsearch`, `dropdowns`

#### `evaluate-grades` — เกณฑ์เกรด (→ store backend `/grades/*`)
`GET /grades/gradeDatalist`, `GET/PUT /grades/gradesedit/:id`, `DELETE /grades/score-ranges`, `POST /grades/addgrades`, `DELETE /grades/gradeId`

#### `evaluate-summary` — สรุปผลประเมิน/เกรดร้าน (→ store backend `/evaluateSummary/*`)
`POST divisionsearchStore`, `PUT /:evaluateId/:storeId/confirmGrade`, `POST /:storeId/reportGrades`, `GET /:evaluateId/:storeId/viewGrade`, `POST viewMonthly`, `GET /:storeId/store`

#### `award-division` — รางวัลระดับ division (→ store backend `/awardDivision/*`)
`GET types-division`, `reportType`, `POST searchDataDivision`, export 2 แบบ (`exportGradeDivision`, `exportCollectDivisionReport`), `POST importData`, `PUT confirmDivision`

#### `report-division` — รายงานประเมินราย division (→ store backend `/reportdivision/*`)
10 endpoints: โหลด option/common code (`loadOptList`, `loadCommonCode`, `loadCommonCodeOrderByValue`, `criteriaDivision`, `loadDivision`, `loadCurrent`), ค้นหา (`searchDataAdmin`, `searchDataSbp`), export (`exportDivisionAdmin`, `exportDivisionSbp`)

#### `report-ptt` — รายงานเกรดร้าน PTT (→ store backend `/reportPtt/*`)
`POST reportSearchgrade`, `POST reportExport`, `GET reportFrom`

#### `manage-import` — จัดการข้อมูลนำเข้าคะแนน (→ store backend `/manage-import/*`)
`GET/POST find-real`, `POST searchreal`, `DELETE deletereal`, `POST premium`, `POST evaluation`, `POST import-grade`

#### `sbp-import` — นำเข้าคะแนน/เกรด (→ store backend `/import/*`)
`GET /import/premiumType`, `POST /import/real-score`, `/import/premium`, `/import/evaluation`, `/import/import-grade` (ชนกับ prefix ของ module `importer` ที่ใช้ `@Controller('import')` เหมือนกัน — path ไม่ซ้ำกันเพราะคนละ sub-path)

#### `importer` — นำเข้าข้อมูลกลาง (→ auth-backend `/import/*` + store backend `api/store-partner-contract/upload`)
`GET /import/template?type=`, `POST /import/upload` (multipart; ถ้า type = STORE_PARTNER ส่งไป store backend, อื่น ๆ ไป auth-backend), `GET /import/download` — template/ไฟล์คืนเป็น signed link

### 6.4 กลุ่มผู้สมัคร / นักลงทุน / การรับสมัคร (→ inv-backend)

#### `investors` — นักลงทุน/ผู้สนใจ (CRD) (→ inv-backend `/master`, `/applicants`; auth-backend)
- `investors/common`: `GET /investors/province`, `/district/:provinceId`, `/sub-district/:provinceId/:districtId`, `/reserved-area`
- `investors/crd` (14 endpoints ใต้ `/investors/crd`): form options (ค้นหา/แก้ไข), `POST send-application-links` (ส่งลิงก์ใบสมัคร), `POST register-crd`, `POST search`, `PATCH edit`, `DELETE delete`, export 2 รายงาน (`export-report`, `export-contact-report`), consent (`consent-master`, `consent-status`, `consent-filter`), `GET /:investorId` — "CRD" ตีความว่า candidate/lead ของนักลงทุน (ความหมายเต็มไม่ระบุในโค้ด)

#### `applicants` — ผู้สมัคร (→ auth-backend + inv-backend `/applicants`)
`GET /applicants/workflow-status`, `GET /applicants/consent-filter`, `GET/POST /applicants/:id/consents`

#### `application` — ใบสมัคร Store Partner (→ inv-backend `/api/application`, `/master`)
27 endpoints ใต้ `/bff/application` — module ที่ใหญ่ที่สุด: ค้นหา (`search`, `search/delete`, `search/approve`, `search/doWorkflowSearch`, `doWorkflowPage`, `search/applicant-by-name`, `search/applicant-by-status`), master data (`masterData`, `masterData/codeValue`, `fileTypeMapping`, `applicantDocumentByInvestType`, `applicantDocumentByType`), แบบฟอร์มสั้น (`short/init|save|submit`), แบบฟอร์มเต็ม 3 หน้า (`page1|page2|page3` × `init|save`), `GET detail`, ไฟล์แนบ (`file/upload` multipart, `file/view`, `file/delete`, `file/updateSeq`), `POST init-from-investor` (สร้างใบสมัครจากข้อมูล investor)

#### `blacklist` — บัญชีดำผู้สมัคร (→ inv-backend `/api/blacklist`, `/master`)
`GET /bff/blacklist/init`, `POST /search`, `PATCH /delete`, `POST /export`, `GET /:id`, `POST /check-duplicate`, `POST /save`, `GET /search/applicant`, `POST /delete/applicant` และ **public** (ไม่มี guard): `GET /bff/blacklist/check/id-card/:idCard` (`blacklist-public.controller.ts` — เช็ค blacklist ด้วยเลขบัตรประชาชน)

#### `onboarding` — กระบวนการรับ Store Partner ใหม่ (สัมภาษณ์/เอกสาร/อนุมัติ) (→ inv-backend `/onboarding/*` + auth-backend + scm-backend)
~24 endpoints ใต้ `/onboarding`: shared master (common-code, province/district/sub-district, ค้นร้าน by-name-or-code / by-code, area), ค้นหา (`/search` + export Excel, ค้นผู้รับผิดชอบ `responsible-by-name` / `fml-responsible-by-name`, ผู้สมัคร `applicant-by-name`), รายละเอียด (`/detail/init|save|next|cancel`, แนบไฟล์ `/detail/file/upload|view`), จัดการ (`/manage/init|save`), ธุรกรรม (`POST /transactions` สร้าง/อัปเดต, `POST /transactions/send-approval` ส่งอนุมัติ), รายงาน (`/report/application` ออกรายงานใบสมัคร PDF/stream, `POST /report/send-interview-email` ส่งอีเมลเอกสารสัมภาษณ์)

#### `cm` — อัปโหลดไฟล์เข้าโมดูล CM ของ backend (→ inv-backend หรือ spm-backend เลือกด้วย query `module=inv|spm`)
`POST /cm/upload` (multipart), `POST /cm/upload-with-s3-uri` (ส่ง S3 URI แทนตัวไฟล์)

### 6.5 กลุ่ม Store Partner / โปรไฟล์ (→ spm-backend)

#### `store-partner-profile` — โปรไฟล์ Store Partner (→ spm-backend `/store-partner-profile/*`)
21 endpoints ใต้ `/store-partner-profile`: ข้อมูลส่วนตัว (`store-partner-info/init|save|compare|update|search|search-by-name`), รูปโปรไฟล์ (`upload-profile-image`, `view-profile-image`, `file-info`, `store-partner-store-info/update-profile-image`), นิติบุคคล (`store-partner-legal-entity/init`), ข้อมูลร้าน SBP (`store-sbp-info/init`), ข้อมูลบุตร (`child-info/init|save`), กิจกรรม (`activity-info/init`), ที่อยู่ shared (province/district/sub-district → spm `/master/*`), consent (`consent-master`, `consent-status`, `POST consent`)

#### `store-partner` — ข้อมูล SP สำหรับหน้าจอ (→ auth-backend `/users/by-id-list` + spm-backend)
`GET /store-partner/consent`, `GET /store-partner/store-partner-data-change` (รายการเปลี่ยนแปลงข้อมูล SP)

#### `juristic` — กลุ่มนิติบุคคล (→ spm-backend `/juristic-group`)
`GET /juristic-group/filter`, `POST /juristic-group` (สร้าง), `POST /:id/detail` (แก้ชื่อ), `POST /delete`

#### `manage-executive` — จัดการข้อมูลผู้บริหาร (→ spm-backend `/manage-executive/*`, `/master/common`)
`GET /manage-executive/search`, `POST /delete`, `GET /getDetail`, `GET /getSharedData`, `POST /save`, `GET /common-code`

#### `relation` — ระบบรายงานความสัมพันธ์ (Declare) (→ spm-backend `/api/relation/*` + auth-backend + employee backend)
Migrate มาจาก Java BE `srm-sps-spsap-smlws`; BFF ดึง user info จาก JWT, ดึง permissions จาก auth-backend, ดึงโปรไฟล์/หัวหน้าจาก employee backend (`/employees/{empId}/profile`, `/employees/{managerEmployeeId}/manager`) แล้วส่งต่อไป spm-backend พร้อม headers (`x-user-id`, `x-user-group-id`, `x-user-permissions`); มีการเข้ารหัส empId (declare-crypto util)
`GET/POST /bff/relation/confirm` (ประวัติ/ส่งรายงานความสัมพันธ์), `GET /reply/:empId` + `POST /reply` (ตอบยืนยัน), `GET /common-codes`, `/permissions`, `/export` (Excel base64), `/validate-person`, `/validate-sbp`

#### `export-data` — export ข้อมูลแบบ dynamic ตาม report master (→ spm-backend + inv-backend `/export-data/*`)
`GET /export-data/common-code`, `/report-master-list`, `/report-column-master-list`, `GET /export-data/` (ดึงข้อมูลจาก view ฝั่ง backend แล้ว **สร้างไฟล์ Excel ฝั่ง BFF** ด้วย `generateExcelFile` เป็น StreamableFile) — โฟลเดอร์ `entities/` มี typeorm entity (view_sbp ฯลฯ) ที่ไม่ได้ถูกใช้ runtime

### 6.6 กลุ่มสัญญา / ต่อสัญญา / โอนร้าน (→ scm-backend `/api/extend-contract/*`, `/api/contract`)

#### `contract` — ทำสัญญา (→ scm-backend `/api/contract`)
`POST /contract/upsert-process` — forward ข้อมูลขั้นตอนทำสัญญา (ส่งอนุมัติ) ไป upsert ที่ scm-backend (ฝั่ง FCM)

#### `confirm-manage-sbp` — ยืนยันข้อมูลบริหารร้าน SBP ตอนต่อสัญญา (→ scm `/api/extend-contract/confirm-manage-sbp`)
10 endpoints ใต้ `/scm-extend-contract/confirm-manage-sbp`: `initForm`, `stores` (ตาม region), `POST search`, `expense-info`, `init-confirm-page`, `POST save-renew-confirm`, `POST reject-renew-manage-sbp`, `init-juristic-info`, `POST save-renew-juristic`, `GET result`

#### `verify-confirm-manage` — ตรวจสอบผลยืนยัน (→ scm `/api/extend-contract/verify-confirm-manage`, `/consider-approve`)
`initForm`, `stores`, `departments`, `POST search`, `detail`, `POST action` (ทำ action ใน workflow)

#### `consider-approve` — พิจารณาอนุมัติต่อสัญญา (→ scm `/api/extend-contract/consider-approve`)
`GET CheckVerify`, `initForm`, `onChangeRegion`, `POST search`, `POST workflow/action`

#### `unblock-contract` — ปลด block สัญญา (→ scm `/api/extend-contract/unblock`)
`GET filter-options`, `POST search`, `POST update-status`, `POST update-status/bulk`

#### `export-extend-contract` — export ข้อมูลต่อสัญญา (→ scm `/api/extend-contract/export-extend-contract`)
`GET initForm`, `onChangeRegion`, `POST export`

#### `store-transfer` — โอนย้ายร้าน (→ scm `/api/storeTranfer` [สะกดตามโค้ด] + auth + store backends)
8 endpoints ใต้ `/bff/storeTranfer` (ทั้งหมด POST): `getRegion`, `getProvince`, `getOptName`, `getStoreTransfer`, `updateStoreTranfer`, `getPresentOptions`, `getExportData`, `getExportStoreData` — เช็ค permission ผ่าน auth-backend `/groups/current-user/permissions`

#### `store-transfer-approval` — อนุมัติโอนร้าน (→ scm `/store-transfer/approval` + auth-backend)
`GET /store-transfer/approval/list`, `POST search`, `GET detail/:workflowTransactionId`, `POST workflow/action`, `POST workflow/initialize-transactions`, `GET download-link/:renewContractId`

### 6.7 กลุ่มรวมงาน / รายงานอื่น ๆ

#### `backlog` — งานค้างรออนุมัติรวมทุกระบบ (→ **5 backends พร้อมกัน**)
`GET /bff/backlog/pending` — ยิง `/api/workflow/pending` ไปที่ auth, store, storePartner, contract, investor backends แบบ `Promise.allSettled` แล้ว merge + prefix transactionId (`Auth_`, `Store_`, `StorePartner_`, `Contract_`, `Investor_`), คำนวณจำนวนวันรอ, เรียงตามวันรอมากสุด — เป็นตัวอย่าง aggregation ที่ชัดที่สุดของ BFF นี้

#### `report-sp-ad-status` — รายงานสถานะ SP/AD (→ auth-backend `/report-sp-ad-status`)
`GET /report-sp-ad-status`, `GET /report-sp-ad-status/export` (สร้าง Excel ด้วย exceljs ฝั่ง BFF)

#### `app` (root) — `GET /health` **[ไม่มี guard]** คืนข้อความ health check

---

## 7. Cross-cutting Concerns

### Authentication flow (สรุปกลไกทั้งหมด)

1. **Login**: `GET /auth/login` → `OidcAuthGuard` (passport-openidconnect) redirect ไป Cognito hosted UI (`https://{AUTH_DOMAIN}/oauth2/authorize`, scope `openid profile`); state เก็บใน cookie-session `oidc-flow-state`
2. **Callback**: Cognito ส่ง code กลับ → strategy แลก token ที่ `/oauth2/token` → **เข้ารหัสทุก token ด้วย AES-256-GCM** (`EncryptionService`: scrypt(ENCRYPTION_SECRET, ENCRYPTION_SALT) → key 32 byte, output base64url `[IV12][TAG16][DATA]`) → เก็บใน **signed httpOnly cookies** (`id_token`, `access_token`, `refresh_token`; `secure` ตาม env; `sameSite=lax` เมื่อ local, `none` เมื่อ deploy)
3. **ทุก request หลังจากนั้น**: `JwtAuthGuard` → `JwtStrategy` ดึง cookie `ID_TOKEN` → ถอดรหัส → verify RS256 กับ JWKS `{AUTH_ISSUER}/.well-known/jwks.json` (cache + rate limit 5 req/min ผ่าน jwks-rsa) → `UsersService.validate(payload)` map เป็น user ของระบบ (เรียก auth-backend) → ได้ `req.user` (AuthUserDto)
4. **Refresh**: `POST /auth/refresh` ใช้ refresh_token cookie แลก token ใหม่
5. **Guard กลาง**: `BaseAuthGuard(strategy)` เป็น factory — log error แล้วโยน error เดิมหรือ `UnauthorizedException`

**การส่งต่อตัวตนไป backend**: BFF ยืนยันตัวเองกับ backend ด้วย `x-api-key` (ค่าใน env ต่อ backend) และส่งบริบทผู้ใช้เป็น header เช่น `x-user-id`, `x-user-group-id`, `x-user-full-name` (encodeURIComponent), `x-user-permissions`, `accept-language` (เห็นชัดใน `export-data.service.ts`, `relation.service.ts`, `backlog.service.ts`) — เฉพาะ `EvaluateClientService` ที่ส่ง `Authorization: Bearer <access_token ถอดรหัสจาก cookie>` ไปยัง store backend เมื่อ token เป็น JWT

### Interceptors / Filters / Pipes / Middleware

| ชนิด | ตัว | พฤติกรรม |
|---|---|---|
| Global Pipe | `ValidationPipe` | `whitelist` + `forbidNonWhitelisted` + `transform` (+ `excludeExtraneousValues`, implicit conversion) — DTO เข้มงวด: field แปลกปลอม = error |
| Global Interceptor | `ResponseInterceptor` | ห่อทุก response เป็น `{success: true, data, requestId}` — ยกเว้น `StreamableFile` ส่งผ่านตรง |
| Global Filter | `HttpExceptionFilter` | แปลง `HttpException` เป็น `{success:false, data:null, error:{code,message}, requestId}` — `code` รองรับ custom code จาก backend |
| Interceptor (ไม่ global) | `LoggingInterceptor` | log request/response + เวลาประมวลผล (ประกาศไว้ใน common แต่ไม่ได้ติดตั้งใน `main.ts`) |
| Middleware | `HttpContextMiddleware` (ทุก route) | สร้าง UUID requestId ต่อ request เก็บใน `AsyncLocalStorage` (`HttpContext`) — logger และ response envelope ดึงไปใช้ |
| Logger | `MyLogger` | custom LoggerService: `[level] <requestId> <label> > message` + สี ANSI เมื่อ `LOG_COLOR=true` |
| Error จาก backend | `CustomHttpException` (ใน `client-service.abstract.ts`) | ดึง status/message/code จาก axios error หลายรูปแบบ แล้วโยนต่อเป็น HttpException ด้วย status เดิมของ backend |

**Decorators แบบ custom: ไม่พบ** — ใช้ decorator มาตรฐานของ Nest ทั้งหมด; ไม่มี role-based guard ใน BFF (การเช็ค permission ทำโดยเรียก auth-backend `/groups/current-user/permissions` ใน service ที่ต้องใช้ เช่น store-transfer, relation)

---

## 8. การเชื่อมต่อภายนอก (ระบบที่ BFF คุยด้วยทั้งหมด)

| ระบบปลายทาง | โปรโตคอล/การยืนยันตัว | ใครใช้ (modules) |
|---|---|---|
| **AWS Cognito** (`AUTH_ISSUER`, `AUTH_DOMAIN` — region ap-southeast-1, ผูกกับ SSO ของ CP All `alloauthdev.cpall.co.th`) | OIDC authorization code, `/oauth2/token`, `/oauth2/userinfo`, JWKS, `/logout` | `auth`, `users` (userinfo), `JwtStrategy` ทุก request |
| **auth-backend / ABS** (`API_AUTHORIZATION_BACKEND_URL`, x-api-key) | REST | users, groups, userGroupMembers, menus, lookups, common-code, addresses, sub-area-authorizations, bellinee-authorizations, store-service, assistant-manager, report-sp-ad-status, importer, applicants, investors, store-transfer(permissions), store-transfer-approval, relation(permissions), onboarding, store-inquiry, store-association-activity, store-partner, backlog, uploads(sync-store-organize) |
| **store backend / SBS** (`API_STORE_BACKEND_URL`, x-api-key; EvaluateClient อาจส่ง Bearer token ผู้ใช้) | REST (+ multipart, file stream) | statement, performance, uploads, confirm-import, external-audit, doc-cooperation, assessment, evaluate-assessment, evaluation-process, evaluate-grades, evaluate-summary, award-division, report-division, report-ptt, manage-import, sbp-import, importer(สัญญา SP), label, store-inquiry, store-association-activity, store-transfer, sap(dead), backlog |
| **spm-backend** (Store Partner Mgmt, `API_STORE_PARTNER_BACKEND_URL`, x-api-key) | REST | store-partner-profile, store-partner, juristic, manage-executive, relation, export-data, cm(spm), label, store-inquiry, store-association-activity, backlog |
| **scm-backend / FCM** (`API_CONTRACT_BACKEND_URL`, x-api-key) | REST | contract, confirm-manage-sbp, verify-confirm-manage, consider-approve, unblock-contract, export-extend-contract, store-transfer, store-transfer-approval, onboarding, backlog |
| **inv-backend** (`API_INVESTOR_BACKEND_URL`, x-api-key) | REST | investors, applicants, application, blacklist, cm(inv), onboarding, export-data, store-association-activity, backlog |
| **employee backend** (`API_EMPLOYEE_BACKEND_URL`, x-api-key) | REST | relation (โปรไฟล์พนักงาน/หัวหน้า) |
| **endpoint เฉพาะกิจ `GET_EMPLOYEE_BY_STOREID`** | REST (env ตรง) | assistant-manager (`/listEmp`) |
| **Dynatrace** (`lss67296.live.dynatrace.com`) | OneAgent ฝังใน Docker image | observability ทั้ง app |

ไม่มีการต่อ DB, message broker, S3 (การอ้าง S3 URI ใน `cm` เป็นเพียงส่งค่าให้ backend), หรือ SMTP โดยตรงจาก BFF (การส่งอีเมล เช่น interview email ทำผ่าน backend)

---

## 9. การทดสอบ

- **Unit tests**: colocate เป็น `*.spec.ts` ข้างไฟล์จริง — 212 ไฟล์ spec จาก 699 ไฟล์ ts; jest config อยู่ใน `package.json` (rootDir `src`, ts-jest, coverageProvider v8)
- **Coverage**: `coveragePathIgnorePatterns` ตัด `.dto.ts`, `.module.ts`, `.entity.ts` ออกจาก coverage; ผลรันล่าสุดถูก dump ไว้ใน `cov_output.txt` (UTF-16) ที่ root — ท้ายไฟล์ระบุ "Test Suites: 11 passed, Tests: 180 passed" แต่เป็นการรันเฉพาะ pattern `store-association-activity/clients` (ไม่ใช่ทั้งชุด) และหลาย module มี coverage 0%
- **CI**: `test:ci` ใช้ jest-junit → `test-reports/`, lcov → `coveragereport/` (สอดคล้อง SonarQube ใน pipeline)
- **E2E**: สคริปต์ `test:e2e` อ้าง `./test/jest-e2e.json` แต่**ไม่มีโฟลเดอร์ `test/` ใน repo** (มีเพียง `test.zip` ที่ root ซึ่งไม่ได้แตกไว้) — e2e จึงไม่พร้อมใช้งานตามสภาพโค้ดปัจจุบัน
- มี Postman collection `assessment-performance.postman_collection.json` (ยิง `/assessment/performance/*` ที่ localhost:3000) สำหรับทดสอบมือ

---

## 10. ข้อสังเกต

### ที่เกี่ยวกับระบบประกันรายได้ (K2/SBPGI)

1. **ไม่มีฟีเจอร์ประกันรายได้ใน BFF นี้** — ค้นทั้ง src ด้วยคำว่า guarantee / income / ประกันรายได้ / K2 / FGI / FCS แล้วไม่พบ (คำว่า `assessment`/`evaluate` ทั้งหมดในโปรเจกต์นี้คือ **การประเมินผลร้าน/ให้เกรดร้าน (store evaluation)** ไม่ใช่การประเมินชดเชยรายได้ของ K2) — สอดคล้องกับที่ K2 เป็นระบบแยก (BPM) ตามเอกสาร SRS ของ prototype
2. **จุดต่อที่เป็นไปได้ถ้าจะเอา K2/SBPGI มาเสียบ** (ตีความจากสถาปัตยกรรม): รูปแบบที่ระบบนี้ใช้ซ้ำ ๆ คือ backend ละ domain + BFF proxy พร้อม `x-api-key`/user-context headers, มี pattern พร้อมใช้หลายอย่างที่ตรงกับความต้องการของ K2 — `backlog` (`/api/workflow/pending` รวมงานรออนุมัติจากหลาย backend — ระบบ SBPGI ใหม่สามารถเพิ่มเป็น source ที่ 6 ได้), pattern `workflow/action` (consider-approve, store-transfer-approval), หน้า import/export Excel, และระบบ menus/groups/permissions จาก auth-backend ที่จะใช้คุม 8 role ของ K2 ได้
3. โครง response envelope `{success, data, error, requestId}` และ auth ผ่าน cookie ของ BFF นี้ คือสิ่งที่หน้าจอ K2 ใน prototype ต้องเรียกผ่านถ้าจะรวมเข้า SBP Mall จริง (ข้อนี้เป็นการอนุมานเชิงสถาปัตยกรรม ไม่ใช่สิ่งที่โค้ดระบุ)

### จุดที่น่าสนใจ / ผิดปกติ

4. **Dead code / dependency ไม่ได้ใช้**: `SapModule` ไม่ถูก import ใน `app.module.ts` (endpoint `/sap/upload-cmadd` ไม่ active); `typeorm` + `pg` + `@nestjs/typeorm` อยู่ใน dependencies แต่ไม่มีการเชื่อม DB จริง; `LoggingInterceptor` ไม่ได้ถูกติดตั้ง; `STORE_DOMAIN` อยู่ใน config แต่ไม่มีผู้ใช้; README ยังเป็น template ของ Nest (พูดถึง Prisma ที่ไม่มีจริง)
5. **ความปลอดภัย**: `.env.local` ที่มี client secret/API key จริงถูก commit; controller `external-audit` ทั้งตัว (10 endpoints) **ไม่มี JWT guard** และรับ `userId` จาก query string (ต่างจาก controller อื่นทั้งหมด); endpoint public โดยตั้งใจมี `/health`, `/users/consents/policy`, `/bff/blacklist/check/id-card/:idCard` (ตัวหลังเปิดเช็ค blacklist ด้วยเลขบัตรประชาชนโดยไม่ต้อง login — ควรทบทวน)
6. **ความไม่สม่ำเสมอของ convention** (ร่องรอยหลายทีม/หลายยุค): prefix ปนกัน — บาง module มี `/bff/` (application, backlog, blacklist, relation, storeTranfer) บางส่วนไม่มี; ตัวสะกดผิดใน path จริง `storeTranfer`; ชื่อ path ปน camelCase/kebab-case; `investors-crd` vs `applicants` ทับซ้อนเรื่อง consent; `sbp-import` กับ `importer` ใช้ `@Controller('import')` ซ้ำกัน (คนละ sub-path จึงไม่ชน); default URL ของ storePartner backend ใน config (3003) ไม่ตรงกับ comment ในโค้ด (3005)
7. **Migration จาก Java**: module `relation` ระบุชัดว่า migrate มาจาก Java BE `srm-sps-spsap-smlws` โดยเปลี่ยนรูปแบบจาก "FE เรียก Java BE ตรง" เป็น "FE → BFF → spm-backend" — บ่งชี้ทิศทางของทั้ง platform ว่ากำลังย้ายจาก Java monolith ไป NestJS microservices ผ่าน BFF (ยืนยันได้เฉพาะ module นี้)
8. **Dockerfile HEALTHCHECK** ยิง `/api/health` แต่ route จริงคือ `/health` (global prefix `api` ถูก comment ออกใน `main.ts`) — อาจตั้งใจให้ prefix มาจาก reverse proxy/ALB แต่ภายใน container ไม่มี prefix ดังกล่าว (ไม่แน่ใจว่าเป็นบั๊กหรือมีตัวเติม path อื่น)
9. ขนาด body limit ตั้งไว้ **100MB** (json + urlencoded) และ timeout ดาวน์โหลดฝั่ง uploads สูงถึง 10 นาที — รองรับงาน import/export ไฟล์ใหญ่เป็นหลัก

---

## ภาคผนวก: ตารางสรุป module → prefix → backend

| Module | URL prefix | Backend หลัก |
|---|---|---|
| auth | `/auth` | Cognito |
| users (+public) | `/users` | auth-backend, Cognito |
| groups | `/groups` | auth-backend |
| userGroupMembers | `/user-group-memberships` | auth-backend |
| menus / lookups / common-code / addresses | `/menus` `/lookups` `/common-code` `/addresses` | auth-backend |
| sub-area-authorizations | `/sub-area/authorizations` | auth-backend |
| bellinee-authorizations | `/bellinee/authorizations` | auth-backend |
| store-service | `/store-service` | auth-backend |
| assistant-manager | `/stores/*`, `/assistant-manager` | auth-backend (+env เฉพาะกิจ) |
| report-sp-ad-status | `/report-sp-ad-status` | auth-backend |
| importer | `/import` | auth-backend + store |
| statement | `/store-statement` | store (SBS) |
| performance | `/store-performance` | store |
| uploads | `/store-uploads` | store (+auth sync) |
| confirm-import | `/store-confirm-import` | store |
| external-audit | `/store-external-audit` | store |
| doc-cooperation | `/docCooperation` | store |
| assessment | `/assessment` | store |
| evaluate-assessment | `/informEvaluate` | store |
| evaluation-process | `/evaluationProcess` | store |
| evaluate-grades | `/grades` | store |
| evaluate-summary | `/evaluateSummary` | store |
| award-division | `/awardDivision` | store |
| report-division | `/reportdivision` | store |
| report-ptt | `/reportPtt` | store |
| manage-import | `/manage-import` | store |
| sbp-import | `/import/*` | store |
| label | `/label` | store + spm |
| store-inquiry | `/store-inquiry` | auth + store + spm |
| store-association-activity | `/store/association/activities` | auth + store + spm + inv |
| sap (dead) | `/sap` | store |
| investors | `/investors`, `/investors/crd` | inv + auth |
| applicants | `/applicants` | inv + auth |
| application | `/bff/application` | inv |
| blacklist (+public) | `/bff/blacklist` | inv |
| onboarding | `/onboarding` | inv + auth + scm |
| cm | `/cm` | inv หรือ spm (เลือกด้วย query) |
| store-partner-profile | `/store-partner-profile` | spm + auth |
| store-partner | `/store-partner` | spm + auth |
| juristic | `/juristic-group` | spm |
| manage-executive | `/manage-executive` | spm |
| relation | `/bff/relation` | spm + auth + employee |
| export-data | `/export-data` | spm + inv |
| contract | `/contract` | scm |
| confirm-manage-sbp | `/scm-extend-contract/confirm-manage-sbp` | scm |
| verify-confirm-manage | `/scm-extend-contract/verify-confirm-manage` | scm |
| consider-approve | `/scm-extend-contract/consider-approve` | scm |
| unblock-contract | `/scm-extend-contract/unblock-contract` | scm |
| export-extend-contract | `/scm-extend-contract/export-extend-contract` | scm |
| store-transfer | `/bff/storeTranfer` | scm + auth + store |
| store-transfer-approval | `/store-transfer/approval` | scm + auth |
| backlog | `/bff/backlog` | ทั้ง 5 backend พร้อมกัน |
