# plan-fe.md — Spec สร้าง Frontend ระบบ SBPGI (React + Vite) ฉบับละเอียด

> **เอกสารนี้คือ spec สมบูรณ์สำหรับ AI/นักพัฒนา สร้าง Frontend จริงจาก prototype HTML ในโฟลเดอร์นี้ — อ่านจบต้องสร้างได้โดยไม่ต้องถาม**
> อ่านคู่กับ: `checklist-fe.md` (ลำดับงาน + เกณฑ์ตรวจรับ) · `REACT-TODO-CHECKLIST.md` (แตก component ต่อหน้า ครบทุกหน้า) · `api.md` (62 endpoint / 10 กลุ่ม) · `workflow.md` (flow/สถานะ) · `plan-be.md` (ฝั่ง Backend)
> **prototype HTML = spec หน้าจอที่ผูกมัด** — layout, ป้ายข้อความไทย, สี, ตาราง, modal ต้องตรงกับหน้า `*.html` เดิม ข้อความ popup/validation ห้าม paraphrase (verbatim จาก SRS)

**กติกาเหล็ก (ผิดข้อใดข้อหนึ่ง = ไม่ผ่าน — ซ้ำกับ checklist-fe.md โดยตั้งใจ):**
1. workflow 5 ขั้น `06 → 08 → 01 → 02 → 03` เท่านั้น — **ห้ามอ้าง section 04/05 หรือสถานะบัญชีในทุกที่** (SDD v7.5 ตัดแล้ว)
2. สถานะเอกสาร **6 ค่า** verbatim (ดู `DOC_STATUSES` ใน §7)
3. กฎ 100,000: >100k → ผ่าน AVP(03) แล้ว**จบ** · ≤100k → **จบที่ GM(02)** — logic routing อยู่ BE, FE แค่แสดงผล
4. ข้อความไทย verbatim ห้าม paraphrase เช่น `ท่านยังไม่เลือกผลการพิจารณา กรุณาเลือกข้อมูลก่อนกดส่งดำเนินการ`
5. ภาค 8 ค่า `BE BN BS BW RC RE RN RS` — **มี RC ไม่มี RW** (รายงานใช้อีกชุด 13 รหัส)
6. %ชดเชยรวมทุกร้านเปิดใหม่ = **100%** พอดีก่อน submit
7. ไฟล์แนบ ≤ **5MB** + นามสกุลใน `ATTACH_EXTS`
8. เลขเอกสาร `YYYY/xxxxx` ปี **พ.ศ.** · วันที่แสดงผลเป็น พ.ศ. ทุกจุด
9. แถวยอดขายไม่ครบ 60 วัน = `tr.flag-red`
10. **ห้าม** Tailwind / UI library / chart library — CSS Modules + SVG เขียนเองเท่านั้น

---

## 0. สัญญากลาง FE/API Integration

> LLDD อ้างอิง: `LLDD/FE/LLDD-FE-Integration-Contracts.md` + `LLDD/BE/LLDD-BE-API-Common-Contracts.md` · ทุก feature hook/component ต้องยึดสัญญานี้ก่อนอ่าน endpoint รายตัวใน `api.md`

| หมวด | Contract ที่ FE ต้องยึด |
|---|---|
| API client | มี axios instance เดียวใน `shared/api/client.ts`; component/page ห้ามสร้าง client เองและห้าม set auth header เอง |
| Auth | ใช้ access token ใน memory + refresh token ใน `localStorage`; 401 non-auth endpoint ต้อง refresh แบบ single-flight แล้ว replay request เดิม; refresh fail ให้ clear session + redirect `/login` |
| Error | type กลาง `ApiError { code: string; message: string }`; แสดง `message` จาก BE ตรง ๆ ผ่าน `apiErrorMessage()`; fallback ไทยใช้เฉพาะ network/no response |
| Pagination | type กลาง `PageResponse<T> { page; size; total; items }`; `<DataTable>`/`<Pager>` ทุกหน้าใช้ shape นี้ |
| Format | payload date/month เป็น ค.ศ. ISO; แสดงผลเป็น พ.ศ. ผ่าน `shared/lib/format.ts` เท่านั้น; `storeCode/newStoreCode` เป็น string 5 หลักเพื่อคง leading zero |
| Workflow action | `DecisionPanel` ส่ง `POST /documents/{docNo}/actions` ด้วย `{result, comment}` เท่านั้น; result เป็น 6-enum ไทย verbatim; consume response `{nextSection,statusCode,status}` แล้ว invalidate detail/timeline/tasks |
| RBAC/Menu | sidebar และ route guard ใช้ `/me/menus`; หน้า detail ใช้ `permissions.canEditSections`/`canAction` จาก BE; FE ไม่คำนวณ transition หรือ owner เอง |
| Audit/Reason | master/config/email/RBAC mutation ต้องมีช่อง reason และส่งให้ BE; FE ไม่เขียน audit เอง |

## 1. Stack และเวอร์ชัน (ตัดสินใจแล้ว — ห้ามเปลี่ยนเอง)

| ส่วน | เลือกใช้ | เหตุผล |
|---|---|---|
| Build | **Vite 5+** + **React 18+** + **TypeScript** (strict) | ตามโจทย์ |
| Router | **react-router-dom v6** (createBrowserRouter) | route ต่อหน้า ตรงกับไฟล์ html เดิม |
| Server state | **@tanstack/react-query v5** | cache/refetch ต่อ endpoint, retry, invalidate หลัง mutation |
| Client state | **zustand** (เฉพาะ auth/session + UI เล็กน้อย) | ห้ามใช้ Redux — เกินจำเป็น |
| Form | **react-hook-form** + **zod** (`@hookform/resolvers`) | validation message ไทย verbatim |
| HTTP | **axios** instance เดียว (`shared/api/client.ts`) | interceptor JWT + refresh + error map |
| CSS | **CSS Modules + CSS variables** — **พอร์ต `assets/sbp.css` ตรง ๆ** เป็น `src/styles/tokens.css` + `global.css` | prototype คือ design spec; **ห้ามใช้ Tailwind/MUI/AntD** เพื่อให้หน้าตาตรง 100% |
| Chart | **เขียน SVG component เอง** (พอร์ตจาก engine `data-chart` ใน sbp.js) | prototype ใช้ inline SVG ทั้งหมด ห้ามเพิ่ม chart lib |
| Font | Google Fonts **Prompt + Sarabun** (link ใน index.html) | ตามเดิม |
| Lint/Format | eslint (typescript + react-hooks) + prettier | มาตรฐาน |
| Test | vitest + @testing-library/react + msw (util + business rule + component สำคัญ) | ดู checklist |

Node >= 20 · pnpm (ถ้าไม่มีใช้ npm ได้)

เครื่องมือคุณภาพโค้ด (ติดตั้งตั้งแต่ Phase 0):
- **husky + lint-staged** — pre-commit รัน eslint+prettier เฉพาะไฟล์ที่แก้
- **commitlint** (`@commitlint/config-conventional`) — บังคับ Conventional Commits
- **GitHub Actions CI** — ทุก PR รัน `lint → typecheck (tsc --noEmit) → test → build`
- **path alias `@/`** = `src/` (ตั้งใน tsconfig + vite) — ห้าม relative import ลึก ๆ (`../../..`)

## 2. คำสั่งเริ่มโปรเจกต์ + config files

```bash
pnpm create vite sbpgi-fe --template react-ts
cd sbpgi-fe && pnpm i react-router-dom @tanstack/react-query zustand axios react-hook-form zod @hookform/resolvers
pnpm i -D vitest @testing-library/react @testing-library/jest-dom jsdom msw eslint prettier \
  husky lint-staged @commitlint/cli @commitlint/config-conventional
pnpm dlx husky init   # + ตั้ง lint-staged ใน package.json
```

`.env.development`:
```
VITE_API_BASE=http://localhost:3000/api/v1
VITE_FEATURE_ABNORMAL=false
```

`vite.config.ts` (เต็ม — proxy กัน CORS ตอน dev + alias + vitest):
```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:3000', changeOrigin: true } },
  },
  test: {                       // vitest (ใช้ vitest/config type ผ่าน /// <reference types="vitest" />)
    environment: 'jsdom',
    setupFiles: ['src/test/setup.ts'],
    globals: true,
  },
});
```

`src/shared/lib/env.ts` — validate env ตอน boot:
```ts
const required = ['VITE_API_BASE'] as const;
for (const k of required) if (!import.meta.env[k]) throw new Error(`Missing env: ${k}`);
export const env = {
  apiBase: import.meta.env.VITE_API_BASE as string,
  featureAbnormal: import.meta.env.VITE_FEATURE_ABNORMAL === 'true',
};
export const isFeatureEnabled = (f: 'abnormal') =>
  ({ abnormal: env.featureAbnormal })[f];
```

## 3. โครงสร้างโฟลเดอร์ (บังคับ — **feature-based** ตามแนว bulletproof-react)

หลักการ: โค้ดจัดตาม **feature (โดเมนธุรกิจ)** ไม่ใช่ตามชนิดไฟล์ · `shared/` มีเฉพาะของที่ >1 feature ใช้จริง · **กติกา dependency ทางเดียว**: `app → features → shared` — feature import ข้าม feature กันตรง ๆ ไม่ได้ (ผ่าน route/props เท่านั้น) · ตั้ง eslint rule `import/no-restricted-paths` คุม

```
src/
  app/                        # ชั้นประกอบแอป (composition root)
    main.tsx                  # ReactDOM.createRoot
    App.tsx                   # QueryClientProvider + RouterProvider + ToastProvider + ErrorBoundary
    router.tsx                # ตาราง route ทั้งหมด (ข้อ 4) — lazy() ต่อ page
    providers/                # query-client.ts, toast, error-boundary
  features/                   # 1 โฟลเดอร์ = 1 โดเมน — ภายในมี api/ components/ hooks/ types/ ของตัวเอง
    auth/                     #   LoginPage, store (zustand), RequireAuth/RequireRole, useAuth
    dashboard/                #   HomePage + ActivityFeed + ModuleGrid
    documents/                #   DocListPage(waiting/related), DocumentPage 12 ส่วน, CreateDocPage, DecisionPanel, แนบไฟล์
    reports/                  #   ReportPage + Export CSV to Batch
    masters/                  #   operators, factors, permissions (แชร์ EntityModal+AuditHistoryTable ผ่าน shared)
    admin/                    #   system-config, email-templates, batch-jobs
    abnormal/                 #   AbnormalListPage (ปิดด้วย feature flag)
  shared/
    api/client.ts             # axios instance + interceptors (JWT, refresh single-flight, error)
    api/query-keys.ts         # query key factory รวมศูนย์ (กัน invalidate พลาด)
    components/               # UI primitives: Pill Chip DataTable Pager EntityModal Tabs … (§9)
    charts/                   # DonutChart BarChart SparkChart HBarChart ColumnChart ChartTooltip
    layout/                   # AppLayout Header Sidebar Breadcrumb + MODULES registry (§10)
    lib/                      # format.ts (พ.ศ./เงิน/docNo) · constants.ts (§7) · env.ts · utils
    types/                    # DTO types กลางตรงกับ api.md (§8)
  styles/
    tokens.css                # :root variables พอร์ตจาก sbp.css (--primary #2f6fed, teal, --seven-*, --header-h 64px)
    global.css                # base + table.data + .pill/.chip/.card + tr.flag-red + modal + toast ฯลฯ
  test/setup.ts               # vitest setup + msw server
```

Convention การตั้งชื่อ (บังคับสม่ำเสมอทั้ง repo):
- Component = `PascalCase.tsx` · hook = `useXxx.ts` · util/อื่น = `kebab-case.ts` · CSS Module = `<Component>.module.css` วางข้างไฟล์ component
- ไม่ใช้ barrel `index.ts` re-export ทั้งโฟลเดอร์ — import ตรงไฟล์ผ่าน alias `@/`
- 1 component ต่อไฟล์ · type ของ props ชื่อ `XxxProps` ประกาศในไฟล์เดียวกัน

## 4. ตาราง Route (1:1 กับ prototype)

| Route | หน้า prototype | Page component | สิทธิ์ | Endpoints หลัก |
|---|---|---|---|---|
| `/login` | *(ไม่มีใน prototype — ฟอร์มเรียบง่ายโทนเดียวกัน)* | LoginPage | public | `POST /auth/login` · `GET /auth/me` · `GET /me/menus` |
| `/` | index.html | HomePage | ทุก role | `GET /dashboard/summary` |
| `/documents/waiting` | k2-list-waiting.html | DocListPage mode=waiting | ทุก role | `GET /tasks` |
| `/documents/related` | k2-list-related.html | DocListPage mode=related | ทุก role | `GET /documents` (ปี required) |
| `/documents/create` | k2-create.html | CreateDocPage | 00/01/02 | `POST /documents` · `GET /stores/search` |
| `/documents/:docNo` | k2-document.html | DocumentPage | ตาม role/section | `GET/PUT /documents/{docNo}` + ลูก ๆ |
| `/reports/income-audit` | k2-report.html | ReportPage | 01/04/06 | `GET /reports/status-summary` (+`/export`) |
| `/masters/operators` | k2-operators.html | OperatorsPage | 01/03 | `/operators` CRUD · `GET /employees/search` |
| `/masters/factors` | k2-factors.html | FactorsPage | 01/03 | `/factors` CRUD |
| `/masters/permissions` | k2-permissions.html | PermissionsPage | 01/03 | `/roles` `/menus` `/menu-permissions` |
| `/admin/system-config` | system-config.html | SystemConfigPage | 01 | `/configs` CRUD |
| `/admin/email-templates` | plan-email.html | EmailTemplatesPage | 01 | `/email-templates` |
| `/admin/batch-jobs` | job-batch.html | BatchJobsPage | 01 | `/jobs` + params/enabled/run/runs |
| `/documents/abnormal` | k2-list-abnormal.html | AbnormalListPage — **สร้างแต่ปิดด้วย flag** `VITE_FEATURE_ABNORMAL=false` | 05 | `GET /abnormal-stores` (commented) |

หมายเหตุ route:
- `:docNo` มี `/` ข้างใน (`2569/00123`) → ใช้ route pattern `/documents/:year/:running` แล้วประกอบเป็น docNo ใน page (`${year}/${running}`) — ห้าม encode `/` เป็น `%2F`
- หน้ากลุ่ม Flow/Database/Plan (`flow-fgi`, `k2-flow`, `plan-*`, `*-database`) เป็น**เอกสารออกแบบ ไม่พอร์ต**เข้าแอปจริง
- **DocListPage ใช้ component เดียว 2 mode** (prototype เป็นไฟล์ฝาแฝด ต่างแค่ `MODE`): `waiting` → `GET /tasks` (inbox: เฉพาะสถานะ "รอ<role ตัวเอง>ดำเนินการ") · `related` → `GET /documents` (**บังคับเลือกปี พ.ศ. ก่อนค้นหา** — ไม่เลือก = ห้ามยิง API + error ใต้ช่องปี)

## 5. Auth (JWT) — โค้ดอ้างอิง

การไหล: `POST /auth/login` → `{accessToken(30 นาที), refreshToken(8 ชม.), user}` — access เก็บใน **memory (zustand)**, refresh ใน `localStorage` · หลัง login ยิง `GET /auth/me` + `GET /me/menus` → **สร้าง sidebar จาก response** (ห้าม hardcode เมนูต่อ role ฝั่ง FE; MODULES registry เป็นแค่ meta icon/route/label แล้ว filter ด้วย `menuCode` จาก API)

### 5.1 `features/auth/store.ts` (zustand)
```ts
import { create } from 'zustand';
import type { UserInfo, MenuItem } from '@/shared/types/dto';

interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;          // memory เท่านั้น — หายเมื่อ refresh หน้า → re-login ด้วย refreshToken
  menus: MenuItem[];
  setSession: (u: UserInfo, access: string, refresh: string) => void;
  setMenus: (m: MenuItem[]) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null, accessToken: null, menus: [],
  setSession: (user, accessToken, refresh) => {
    localStorage.setItem('sbpgi.refreshToken', refresh);
    set({ user, accessToken });
  },
  setMenus: (menus) => set({ menus }),
  clear: () => { localStorage.removeItem('sbpgi.refreshToken'); set({ user: null, accessToken: null, menus: [] }); },
}));

export const useAuth = () => useAuthStore((s) => ({ user: s.user, isAuthed: !!s.accessToken, menus: s.menus }));
```

### 5.2 `shared/api/client.ts` (axios เต็ม — refresh single-flight)
```ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { env } from '@/shared/lib/env';
import { useAuthStore } from '@/features/auth/store';

export interface ApiError { code: string; message: string }   // message = ไทยตาม SRS แสดงตรง ๆ

export const api = axios.create({ baseURL: env.apiBase, timeout: 30_000 });

api.interceptors.request.use((cfg) => {
  const token = useAuthStore.getState().accessToken;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

/* ---- refresh single-flight: 401 หลายเส้นพร้อมกัน → ยิง /auth/refresh ครั้งเดียว ---- */
let refreshing: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = localStorage.getItem('sbpgi.refreshToken');
  if (!refreshToken) throw new Error('no refresh token');
  // ใช้ axios ดิบ (ไม่ใช่ instance) กัน interceptor วนซ้ำ
  const { data } = await axios.post(`${env.apiBase}/auth/refresh`, { refreshToken });
  useAuthStore.setState({ accessToken: data.accessToken });
  return data.accessToken as string;
}

api.interceptors.response.use(undefined, async (error: AxiosError<ApiError>) => {
  const cfg = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
  if (error.response?.status === 401 && !cfg._retried && !cfg.url?.includes('/auth/')) {
    cfg._retried = true;
    try {
      refreshing ??= refreshAccessToken().finally(() => { refreshing = null; });
      const token = await refreshing;
      cfg.headers.Authorization = `Bearer ${token}`;
      return api(cfg);                                   // replay request เดิม
    } catch {
      useAuthStore.getState().clear();
      window.location.assign('/login');
    }
  }
  return Promise.reject(error);
});

/** ดึงข้อความ error ไทยจาก BE — FE ห้ามแต่งเอง */
export const apiErrorMessage = (e: unknown): string =>
  (axios.isAxiosError<ApiError>(e) && e.response?.data?.message) || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง';
```

### 5.3 RequireAuth / RequireRole
```tsx
// features/auth/components/RequireAuth.tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/features/auth/store';

export function RequireAuth() {
  const { isAuthed } = useAuth();
  const loc = useLocation();
  return isAuthed ? <Outlet /> : <Navigate to="/login" state={{ from: loc }} replace />;
}

// features/auth/components/RequireRole.tsx
export function RequireRole({ roles }: { roles: string[] }) {
  const { user } = useAuth();
  return user && roles.includes(user.roleCode) ? <Outlet /> : <Navigate to="/" replace />;
}
```
ใช้ใน `router.tsx`: `<RequireAuth>` ครอบทุก route ยกเว้น `/login` · `<RequireRole roles={['01','03']}>` ครอบกลุ่ม masters ฯลฯ ตามคอลัมน์สิทธิ์ใน §4

## 6. ชั้น API + query keys

- hook ต่อกลุ่มอยู่ `features/*/api/` (เช่น `features/documents/api/useDocument.ts`) — เรียกผ่าน `api` instance กลางเสมอ
- ทุก mutation สำเร็จ → `invalidateQueries` ด้วย key จาก factory + `toast(msg,'ok')`
- Error ทุกเส้นรูปแบบ `{code, message}` — แสดง `message` ผ่าน `apiErrorMessage()` ตรง ๆ
- pagination: ส่ง `?page&size` รับ `{page,size,total,items}` → ผูกกับ `<Pager>`
- วันที่จาก API = ISO + ค.ศ. → แปลงแสดง **พ.ศ.** ที่ `formatDateThai()` จุดเดียว

### 6.1 `shared/api/query-keys.ts` (factory ครบ 10 กลุ่มตาม api.md)
```ts
export const authKeys = {
  me: ['auth', 'me'] as const,
  menus: ['auth', 'menus'] as const,
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
  operators: ['masters', 'operators'] as const,
  factors: ['masters', 'factors'] as const,
  employees: (q: string) => ['masters', 'employees', q] as const,
  roles: ['masters', 'roles'] as const,
  menus: ['masters', 'menus'] as const,
  menuPermissions: ['masters', 'menu-permissions'] as const,
  auditLogs: (table: string) => ['masters', 'audit-logs', table] as const,
};
export const configKeys = {
  all: ['configs'] as const,
  detail: (key: string) => ['configs', key] as const,
};
export const emailKeys = {
  all: ['email-templates'] as const,
  detail: (code: string) => ['email-templates', code] as const,
};
export const reportKeys = {
  statusSummary: (params: Record<string, unknown>) => ['reports', 'status-summary', params] as const,
};
export const jobKeys = {
  all: ['jobs'] as const,
  detail: (jobNo: string) => ['jobs', jobNo] as const,
  runs: (jobNo: string) => ['jobs', jobNo, 'runs'] as const,
};
export const dashboardKeys = {
  summary: ['dashboard', 'summary'] as const,
};
```
กติกา: **ห้าม**พิมพ์ array key มือเปล่าในไฟล์ hook — import จาก factory เท่านั้น (grep `useQuery({ queryKey: ['` ต้องไม่เจอ)

## 7. ค่าคงที่ธุรกิจ — `shared/lib/constants.ts` (เต็ม)

```ts
/* workflow 5 ขั้น — SDD v7.5 ตัดขั้นบัญชี 04/05 ออกแล้ว ห้ามอ้างถึง */
export const SECTIONS = [
  { code: '06', name: 'ฝ่าย SBP DSA' },
  { code: '08', name: 'เจ้าหน้าที่ SBP DSA' },
  { code: '01', name: 'ฝ่ายส่งเสริมธุรกิจ SBP' },
  { code: '02', name: 'GM ส่งเสริมธุรกิจ SBP' },
  { code: '03', name: 'ผู้บริหารสำนักบริหาร SBP (AVP)' },
] as const;

/* สถานะเอกสาร 6 ค่า — string เต็ม verbatim ห้ามแก้แม้แต่วรรค */
export const DOC_STATUSES = [
  'รอฝ่าย SBP DSA ดำเนินการ',            // section 06
  'รอเจ้าหน้าที่ SBP DSA ดำเนินการ',      // section 08
  'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ',   // section 01
  'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ',   // section 02
  'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ', // section 03
  'เสร็จสิ้นดำเนินการ',                   // จบ
] as const;
export type DocStatus = (typeof DOC_STATUSES)[number];

/* map สถานะ → variant ของ <Pill> (สีตาม prototype) */
export const STATUS_PILL: Record<DocStatus, string> = {
  'รอฝ่าย SBP DSA ดำเนินการ': 'wait',
  'รอเจ้าหน้าที่ SBP DSA ดำเนินการ': 'violet',
  'รอฝ่ายส่งเสริมธุรกิจ SBP ดำเนินการ': 'info',
  'รอ GM ส่งเสริมธุรกิจ SBP ดำเนินการ': 'orange',
  'รอผู้บริหารสำนักบริหาร SBP ดำเนินการ': 'navy',
  'เสร็จสิ้นดำเนินการ': 'ok',
};

export const AVP_THRESHOLD = 100_000; // >100k → AVP(03) แล้วจบ · ≤100k → จบที่ GM(02) — ใช้แสดงป้ายเท่านั้น routing อยู่ BE

/* ภาค 8 ค่า (ตัวกรองเอกสาร) — มี RC ไม่มี RW */
export const REGIONS8 = ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS'] as const;

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
  AUDIT_REASON_LABEL: 'เหตุผลการแก้ไข (บันทึกลง audit_logs)',
  /* ข้อความ popup อื่น ๆ คัดจากหน้า html เดิม + RDM-SRS-…-รายการหน้าจอ.md ตอน implement หน้านั้น */
} as const;
```

### 7.1 `shared/lib/format.ts`
```ts
/** ISO ค.ศ. → แสดง พ.ศ. เช่น '2026-01-15' → '15/01/2569' — จุดเดียวทั้งแอป */
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

/** เลขเอกสาร YYYY/xxxxx ปี พ.ศ. เช่น (2569, 123) → '2569/00123' */
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

/* ---- Auth ---- */
export interface UserInfo {
  employeeId: string; fullName: string;
  roleCode: string;              // '00'..'10' (8 role groups)
  roleName: string;
  sectionCode?: '06' | '08' | '01' | '02' | '03';   // ขั้น workflow ของผู้ใช้ (ถ้ามีบทบาทพิจารณา)
  email: string;
}
export interface LoginResponse { accessToken: string; refreshToken: string; user: UserInfo }
export interface MenuItem { menuCode: string; label: string; group: string; parentCode?: string }

/* ---- Tasks / Documents ---- */
export interface TaskItem {
  docNo: string;                    // '2569/00123'
  roundNo: number;                  // ครั้งที่
  impactedStoreCode: string; impactedStoreName: string;
  regionCode: string;               // REGIONS8
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

types เฉพาะ feature (OperatorRow, FactorMasterRow, RoleRow, ConfigRow, EmailTemplate, JobItem, ReportRow 19 คอลัมน์ ฯลฯ) ประกาศใน `features/*/types/` ของตัวเอง — field ตรงคอลัมน์ตารางใน REACT-TODO-CHECKLIST.md ของหน้านั้น

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
  visibleWhen?: (values: Record<string, unknown>) => boolean;  // เช่น ช่องภาคโผล่เมื่อตำแหน่ง=ฝ่ายส่งเสริมธุรกิจ SBP
  lockedOnEdit?: boolean;                            // เช่น factor_code แก้ไม่ได้ตอน edit
}
interface EntityModalProps {
  mode: 'view'|'edit'|'add';
  title: string; fields: EntityField[];
  initialValues?: Record<string, unknown>;
  requireReason?: boolean;   // mode edit/add ของ master = true → บังคับช่อง MSG.AUDIT_REASON_LABEL
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
interface HBarChartProps {                            // แนวนอน + dot สถานะ + tooltip (index, k2-report)
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

## 10. MODULES registry — `shared/layout/modules.ts` (ตัวอย่างเต็ม)

พอร์ตจาก `assets/sbp.js` (~บรรทัด 52) เฉพาะกลุ่มแอปจริง (กลุ่ม Flow/Database/Plan ไม่พอร์ต):

```ts
import { isFeatureEnabled } from '@/shared/lib/env';

export interface ModuleEntry {
  key: string;                 // = menuCode ที่ match กับ GET /me/menus
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
  { key: 'k2-operators',   label: 'กำหนดผู้ปฏิบัติงาน',    route: '/masters/operators',     icon: 'idcog',     group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'k2-factors',     label: 'กำหนดปัจจัยภายนอก',     route: '/masters/factors',       icon: 'db',        group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'k2-permissions', label: 'สิทธิ์การเข้าถึงเมนู',   route: '/masters/permissions',   icon: 'lock',      group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'system-config',  label: 'ตั้งค่าระบบ (Config)',  route: '/admin/system-config',   icon: 'cog',       group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'job-batch',      label: 'Batch Job',             route: '/admin/batch-jobs',      icon: 'clock',     group: 'ระบบประกันรายได้ (SBP Mall)' },
  { key: 'plan-email',     label: 'Email Template',        route: '/admin/email-templates', icon: 'mail',      group: 'ระบบประกันรายได้ (SBP Mall)' },
];
```

Sidebar render: group ตามลำดับ first-appearance · **filter รายการด้วย `menuCode` จากผล `GET /me/menus`** (MODULES เป็น meta เท่านั้น — เมนูที่ API ไม่ส่งมา = ไม่แสดง) · active-item: exact route match → key ตรง → same path prefix · submenu "เอกสาร" พับได้ · Breadcrumb: `Home › SBP Management System › <label ของ route>` (leaf จาก meta ของ route แทน `data-crumb`)

## 11. Spec ต่อหน้า (ครบ 14 route)

> คอลัมน์/ป้าย verbatim เต็ม ๆ ดู REACT-TODO-CHECKLIST.md ต่อหน้า — ที่นี่สรุป endpoint + ฟอร์ม/validation + mutation + เงื่อนไข role ให้ครบพอสร้างได้

### 11.1 `/login` — LoginPage
- ฟอร์ม username/password (react-hook-form + zod: ทั้งสองช่อง required)
- submit → `POST /auth/login` → `setSession()` → ยิง `GET /auth/me` + `GET /me/menus` → `setMenus()` → redirect ไป `state.from` หรือ `/`
- login ผิด → แสดง `apiErrorMessage(e)` ใต้ฟอร์ม (ข้อความจาก BE ตรง ๆ) — ไม่ crash
- หน้าตา: การ์ดกลางจอ โทน `--primary` เดียวกับแอป (ไม่มีใน prototype — ออกแบบเรียบง่าย)

### 11.2 `/` — HomePage (index.html)
- โหลด: `GET /dashboard/summary` (`dashboardKeys.summary` — BE cache 5 นาที)
- S1 Hero: `สวัสดี, คุณ<ชื่อจาก /auth/me>` + ปุ่ม `งานรอท่านดำเนินการ` (→`/documents/waiting`) · `เอกสารร้านถูกกระทบ`
- S2 StatGrid 4 ใบ: เอกสารรอท่านดำเนินการ · สาขาประกันรายได้เดือนนี้ · ยอดชดเชยเดือนนี้ (ล้านบาท) · ยอดขายไม่ครบ 60 วัน
- S3: `<ColumnChart>` "ยอดชดเชยประกันรายได้รายเดือน" + `<HBarChart>` "เอกสารค้างตามขั้นตอน Workflow" — **แถว = 5 section + เสร็จสิ้น เท่านั้น (ห้ามมี 04/05)** · ตัวเลข sync กับ stat cards
- S4 `<ModuleGrid>` การ์ดทางลัด (card abnormal ซ่อนตาม flag) · S5 `<ActivityFeed>` + `<QuickLinks>`
- ไม่มี mutation

### 11.3 `/documents/waiting` + `/documents/related` — DocListPage (1 component 2 mode)
- mode `waiting` → `GET /tasks` (`taskKeys.list(params)`) — inbox เฉพาะสถานะของ role ตัวเอง · mode `related` → `GET /documents` (`documentKeys.list`)
- **related: ปี พ.ศ. required** — ไม่เลือกแล้วกดค้นหา → error ใต้ช่องปี + **ไม่ยิง API** (enabled: false)
- FilterBar: ปี* (dropdown พ.ศ.) · เดือน · สถานะ (select `DOC_STATUSES` — **ซ่อนใน waiting**) · ภาค (`REGIONS8` multi) · ประเภทร้าน (`SEARCH_STORE_TYPES` multi) · รหัส/ชื่อร้าน · เลขเอกสาร · ยอดขายลดลง% / เงินชดเชย / รอ(วัน) (RangeInput min–max) · ปุ่ม `ล้างตัวกรอง`
- Stat cards คลิกกรองตาราง: waiting 4 ใบ (ทั้งหมด / flag60 / รอเกิน 3 วัน / วงเงิน>100,000 เข้า AVP) · related = ทั้งหมด + ต่อสถานะ
- ตาราง: `ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้านถูกกระทบ | ภาค | ยอดขายที่ลดลง(%) | จำนวนเงินที่ชดเชย | สถานะ(pill) | รอ (วัน)` — sortable, `rowClassName` = flag-red, คลิกแถว → `/documents/:docNo`
- `<Pager>` ผูก `?page&size` ↔ `PagedResponse<TaskItem>` + NoticeCard `แดง = ยอดขายไม่ครบ 60 วัน …`
- ไม่มี mutation

### 11.4 `/documents/create` — CreateDocPage (k2-create.html)
- S1 pill `เลขที่เอกสารถัดไป · <จาก API>` · Tabs 2 แท็บ
- **Tab `สร้างเอกสารใหม่ (นอกเงื่อนไข)`** — ฟิลด์: `รหัสร้านถูกกระทบ*` (`StoreSearchInput` → `GET /stores/search?type=impacted`) · `ชื่อร้านถูกกระทบ` (readonly auto) · `ภาค` (readonly) · `ประเภทร้าน` (select `CREATE_STORE_TYPES` 8 ค่า) · `วันที่โอนเป็นร้าน SP` (date) · `เดือน/ปีที่ถูกกระทบ*` (month) · `ครั้งที่` · `รหัสร้านเปิดใหม่*` (search `type=new`) · `เหตุผลการสร้างเอกสารนอกเงื่อนไข*` (textarea) · ปุ่ม `เคลียร์ค่าเริ่มใหม่` / `สร้างเอกสาร`
- zod: ช่อง `*` ทั้งหมด required — message ไทยตามหน้าเดิม
- mutation: `POST /documents` → toast เลขเอกสาร `YYYY/xxxxx` → invalidate `documentKeys.all`+`taskKeys.all` → navigate ไปเอกสาร
- **Tab `สร้างเอกสารที่ FS`**: `รหัสร้านถูกกระทบ*` · `ชื่อร้าน` (readonly) · `เดือน/ปีที่ถูกกระทบ*` · `Period Statement (From–To)` · ปุ่ม `เคลียร์` / `ส่งสร้างที่ FS` → `POST /documents` (mode FS) + `<PendingStatementTable>` "เอกสารที่รอ SBP Statement ส่งกลับ": `รหัสร้าน | ชื่อร้านถูกกระทบ | เดือน/ปี | ส่งเข้า FS เมื่อ | สถานะ` (pill รอ/ส่งกลับแล้ว)
- สิทธิ์: RequireRole 00/01/02

### 11.5 `/documents/:docNo` — DocumentPage ⭐ (k2-document.html — ซับซ้อนสุด)
- โหลด `GET /documents/{docNo}` (`documentKeys.detail`) ครั้งเดียว → ได้ `myRoleView` + `editableSections` + `resultOptions` — **render 12 ส่วนตามธงจาก BE ไม่เดา role เอง** (แทนกลไก `data-editrole`/`data-roleonly`/`.edit-only` ของ prototype)
- S2 head: `เอกสารข้อมูลร้านถูกกระทบ <docNo>` + `<StatusPill>` + ปุ่ม `พิมพ์` (window.print) · `<WorkflowStepper>` 5 ขั้น `06›08›01›02›03` + pill `ขั้นตอนที่ N/5`
- S3 `<DocMetaGrid>`: รอบ/ครั้งที่/เดือน, สถานะ, เลขที่, วันที่สร้าง (พ.ศ.), รหัส/ชื่อร้าน, ภาค, ประเภท, เจ้าของ, นิติบุคคล, วันที่โอน, ผู้ดำเนินการ, ยอดขายลดลง %, ชดเชยล่าสุด, ไฟล์แนบ + ปุ่ม `ข้อมูลยอดขายเพิ่มเติม`
- S4 กราฟ: `GET /documents/{docNo}/sales` (`documentKeys.sales`) → `<SalesTrendChart>` (เส้น/พื้นที่ ก่อน–หลัง + marker วันเปิดสาขา + เส้นเฉลี่ย) + `<SalesAvgBarChart>` (2 แท่ง + badge −%) — 4 หน้าต่าง × 15 วัน
- S5 `<NewStoresTable>` (แก้ได้เมื่อ `'newStores' ∈ editableSections`): คอลัมน์ 12 ตาม checklist · `%ชดเชย` เป็น input · แสดงสด `เงินชดเชย = ยอดตั้งต้น × %/100` · ปุ่ม `รีเฟรช`/`คืนค่าก่อนแก้ไข`/`คำนวณเงินชดเชย` — **%รวม ≠ 100 → `<WarningPopup>` (ข้อความ verbatim จากหน้าเดิม) และไม่ยิง PUT** · %รวม = 100 → `PUT /documents/{docNo}` → invalidate detail + toast ok
- S6 `<AllMapPoi>` SVG (วงรัศมี, pulse, หมุดร้านใหม่, คู่แข่ง, legend) + ปุ่ม `Link To ALLMAP`
- S7 คู่แข่ง (editable ตามธง): dropdown จาก `GET /competitors` · ป้ายที่มา ALM/USER · เพิ่ม/แก้/ลบ ผ่าน `<EntityModal>` → `PUT /documents/{docNo}`
- S8 ปัจจัยอื่นๆ: dropdown จาก `GET /factors` · โครงเดียวกับ S7
- S9 `<AttachmentsTable>` + ปุ่ม `แนบไฟล์` → validate ext+5MB ฝั่ง FE ก่อน → `POST /documents/{docNo}/attachments` (multipart) → invalidate detail
- S10 `<CompensationCalcPanel>` readonly (ยอดตั้งต้น / %รวม / รวมร้านใหม่ / อำนาจอนุมัติ `≤100,000 GM · >100,000 AVP`) — **แสดงเฉพาะ view section 08 ตามธง API**
- S11 `<CompensationHistoryTable>` (คลิก → เปิดเอกสารครั้งนั้น) · S12 `<DecisionHistoryTable>` + modal — จาก `GET /documents/{docNo}/timeline`
- S13 `<DecisionPanel>`: radio จาก `resultOptions` + textarea `ความคิดเห็นเพิ่มเติม` + ปุ่ม `แนบรูป`/`บันทึก`/`ส่งดำเนินการ`
  - `ส่งดำเนินการ` ไม่เลือกผล → popup `MSG.NO_DECISION` — ไม่ยิง API
  - เลือกตัวเลือกที่ `commentRequired` (ไม่ชดเชย/หยุดชดเชย) แต่ comment ว่าง → popup เตือน — ไม่ยิง API
  - `บันทึก` → ไม่ validate, save draft ได้เสมอ
  - ผ่าน → `POST /documents/{docNo}/actions` `{result, comment}` — **routing (กฎ 100k) อยู่ BE** → toast ok + invalidate detail+timeline+`taskKeys.all` → สถานะ/stepper ขยับ

### 11.6 `/reports/income-audit` — ReportPage (k2-report.html, SRS 3.1.7 + SDD v7.5)
- ฟอร์ม `<ReportSearchForm>`: ปี* · เดือน/ปีเริ่ม–ถึง (month) · รหัสร้านกระทบ (+`StorePickerModal` → `GET /stores/search`) · ชื่อร้าน (readonly) · รหัสร้านเปิดใหม่ · สถานะ (select `DOC_STATUSES`) · **radio ผลการพิจารณา\* (บังคับ): `ประกันรายได้` / `ไม่ประกันรายได้`** · ภาค (checkbox `REPORT_REGIONS13`) · ประเภทร้าน (checkbox) · Period Statement From–To · ปุ่ม `เคลียร์` / `Preview Report`
- ไม่เลือกปี → error + ไม่ยิง API (กฎเดียวกับ related)
- `Preview Report` → `GET /reports/status-summary` (`reportKeys.statusSummary`) → `<SummaryLine>` (พบ N รายการ / ยอดชดเชยรวม / วงเงิน>100,000 / แถวแดง) + `<HBarChart>` ×2 (ตามสถานะ 6 ค่า / ยอดเงินตามภาค)
- ตารางผล **19 คอลัมน์** (scroll ใน `.table-wrap`) ตาม checklist · flag-red · pill สถานะ · เงินคั่นหลักพัน · วันที่ พ.ศ.
- ปุ่ม `Export CSV to Batch` → `GET /reports/status-summary/export` (query เดียวกับ preview) → ดาวน์โหลด CSV (UTF-8 BOM เปิด Excel ไทยไม่เพี้ยน)

### 11.7 `/masters/operators` — OperatorsPage (k2-operators.html, SRS 3.1.8)
- โหลด `GET /operators` (`masterKeys.operators`) · ตาราง `☑ | ชื่อผู้ปฏิบัติงาน | E-Mail | ชื่อตำแหน่ง | ภาคที่รับผิดชอบ | Action(view/edit/del)`
- `<EntityModal>` schema: ชื่อ / อีเมล (type email) / ชื่อตำแหน่ง (select จาก `GET /workflow-sections`) / ภาค (select `REGIONS8` + `-`, `visibleWhen: ตำแหน่ง === 'ฝ่ายส่งเสริมธุรกิจ SBP'`) / เหตุผล (requireReason)
- `<EmployeeSearchModal>`: ปุ่ม `ค้นหาพนักงาน (Pop Up)` → `GET /employees/search?q=` → เลือก → เติมฟอร์ม + toast
- mutations: `POST /operators` · `PUT/DELETE /operators/{id}` (reason บังคับ) → invalidate `masterKeys.operators` + `masterKeys.auditLogs('operator_assignments')`
- `<AuditHistoryTable>` ผูก `GET /audit-logs?table=operator_assignments` + `<SrsConditionsCard>`

### 11.8 `/masters/factors` — FactorsPage (k2-factors.html, SRS 3.1.9)
- `GET /factors` · ตาราง `☑ | รหัสปัจจัย | ชื่อปัจจัย | รายละเอียดเพิ่มเติม | Action` + toolbar ค้นหา/`เคลียร์`
- schema: `factor_code` (lockedOnEdit) / `factor_name` / `factor_remark` / เหตุผล — **แก้ได้เฉพาะชื่อ+รายละเอียด**
- รหัสซ้ำ → BE ตอบ error → แสดง `message` ตรง ๆ · mutations CRUD `/factors` `/factors/{code}` → invalidate factors + auditLogs('external_factors')

### 11.9 `/masters/permissions` — PermissionsPage (k2-permissions.html, SRS 3.1.1)
- โหลด: `GET /roles` + `GET /menu-permissions` (`masterKeys.roles`/`menuPermissions`)
- `<RolesTable>`: `Code | Role | คำอธิบาย | Action` — 8 role (00 Default … 10 UserViewer) · role `is_system` → ปุ่มลบ/แก้รหัส **disabled**
- `<PermissionMatrix>` ×2 (เมนู main / เมนู master — master ตัด role 00, off = `✗`): cell toggle `✓/–` local state, cell dirty = amber + badge นับ dirty · ปุ่ม `บันทึกสิทธิ์` → `PUT /menu-permissions/{menuCode}` ต่อเมนูที่ dirty (optimistic update ได้เฉพาะจุดนี้)
- CRUD role `/roles/{roleCode}` · CRUD เมนู `POST/PUT/DELETE /menus/{menuCode}` (ลบ = confirm cascade สิทธิ์ทุก role) · เพิ่ม/ลบ role → คอลัมน์ matrix sync
- `<AuditLogTable>` + `<AcceptanceCriteriaCard>` (เฉพาะ Role 01/02 จัดการได้)

### 11.10 `/admin/system-config` — SystemConfigPage (system-config.html)
- `GET /configs` (`configKeys.all`) · `<DonutChart>` สัดส่วนตามหมวด · ตาราง `☑ | Config Key | หมวดหมู่ | ค่า (Value) | ชนิดข้อมูล | หน่วย | คำอธิบาย | แก้ไขได้ | Action` + filter หมวด + ค้นหา
- แถว `is_editable=false` → ไอคอน lock, edit/del disabled (BE ปฏิเสธซ้ำ)
- `<EntityModal>` schema config — **validate ค่า ตาม `value_type`** (number/boolean/string/json — zod refine) ก่อน `PUT /configs/{key}` · `POST /configs` เพิ่ม · ปุ่ม `Invalidate Cache`
- invalidate `configKeys.all` + auditLogs('system_configs')

### 11.11 `/admin/email-templates` — EmailTemplatesPage (plan-email.html, EM-01–08)
- `GET /email-templates` (`emailKeys.all`) · ตาราง map (คลิกแถวเลื่อนไป card) + Tabs 3 กลุ่ม (Workflow EM-01–03 / เตือนงานค้าง EM-04–05 / Batch EM-06–08)
- `<EmailTemplateCard>` ×8: meta grid + `<MailPreview>` (From/To/Cc/Subject + body) — **From/To/Cc read-only ตาม status_email_rules** · EM-01 มี selector 6 สถานะ live-rewrite preview
- Editor: `<RichTextToolbar>` + `<MergeVariableChips>` ต่อ template (subject แทรก text, body แทรก atom) — ห้าม execCommand ตรง, ห้ามเพิ่ม lib ใหญ่เกินจำเป็น (contentEditable + Selection API เขียนเอง)
- mutations: `PUT /email-templates/{code}` · `POST /email-templates/{code}/reset` · `POST /email-templates/reset-all` (confirm ก่อน) → invalidate `emailKeys` + auditLogs('email_templates')

### 11.12 `/admin/batch-jobs` — BatchJobsPage (job-batch.html, Jobs 1–10 + 8b)
- `GET /jobs` (`jobKeys.all`) · Stat 4 ใบ + Donut/Bar/Spark + `<PhaseStrip>` เฟส A–E (chip คลิก→select job)
- `<JobTable>`: `Job | ชื่องาน / Main Class | เฟส | ประเภท | กำหนดการ (Cron) | รอบล่าสุด | ผลล่าสุด | รอบถัดไป | สถานะ | (action)` — คลิก → `<JobDetailPanel>`
- DetailPanel: toggle เปิด/ปิด → `PUT /jobs/{jobNo}/enabled` · Tabs 4: พารามิเตอร์ (แก้เฉพาะ editable → `PUT /jobs/{jobNo}/params`) / Flowchart SVG / Database ที่ใช้ / ประวัติการรัน (`GET /jobs/{jobNo}/runs` — เรียงล่าสุดก่อน + ปุ่ม `ดู Log`)
- run bar: เลือกเดือน + `สั่งรันทันที` → `POST /jobs/{jobNo}/run` — BE guard กันรันซ้อน → error แสดง message ตรง ๆ ไม่ crash
- invalidate `jobKeys` หลังทุก mutation + `<AuditHistoryTable>` (job_configs)

### 11.13 `/documents/abnormal` — AbnormalListPage (k2-list-abnormal.html — **ปิด flag**)
- สร้างครบแต่เปิด/ปิดด้วย `isFeatureEnabled('abnormal')` จุดเดียว (route + เมนู + card หน้าแรก) — flag ปิดแล้วเข้า URL ตรง → redirect `/`
- Stat 4 ใบ (ทั้งหมด/ยังไม่แจกงาน/แจกงานแล้ว/แก้ไขแล้ว — assignment status แยกจากสถานะเอกสาร) · filter (ภาค 8, สาเหตุ 4, สถานะ 3, ผู้รับผิดชอบ)
- ตาราง `☑ | ครั้งที่ | เลขที่เอกสาร | รหัสร้าน | ชื่อร้าน | ภาค | สาเหตุผิดปกติ | ผู้รับผิดชอบ | สถานะ | Action(view+assign)` + flag-red + bulk `แจกงานที่เลือก` + `<AssignJobModal>`
- endpoints (commented ใน api.md): `GET /abnormal-stores` · `POST /abnormal-stores/assign` — สิทธิ์ role 05

## 12. Best practices สากลที่บังคับใช้

- **Testing pyramid**: unit (util/business rule — เยอะสุด) → component (Testing Library + **msw** mock ระดับ network — ห้าม mock axios ตรง ๆ) → e2e smoke (Playwright 1 เส้น: login → inbox → เปิดเอกสาร → ส่งดำเนินการ → toast)
- **ErrorBoundary** ระดับ route + fallback ภาษาไทย · query error แสดงใน `<NoticeCard>` ไม่ crash ทั้งแอป
- **`lazy()` + Suspense ต่อ page** (code-splitting ต่อ route) + `<PageSkeleton>` ระหว่างโหลด
- **Accessibility**: label ทุก input · modal focus-trap + Esc ปิด · `aria-label` ปุ่มไอคอน · contrast ตาม token เดิม
- **Env 12-factor**: ผ่าน `VITE_*` + validate ตอน boot (`shared/lib/env.ts`) · ไม่มี secret ฝั่ง FE · feature flag ผ่าน `isFeatureEnabled()` จุดเดียว
- อัปเดตหลัง mutation ใช้ `invalidateQueries` เป็นหลัก — optimistic update เฉพาะ permission matrix
- **README.md**: วิธีรัน dev/test/build + ตาราง env + โครงสร้างโฟลเดอร์ย่อ

## 13. ข้อห้ามรวม (ผิด = ไม่ผ่าน review)

1. ห้ามเพิ่ม UI library / chart library / Tailwind
2. ห้าม paraphrase ข้อความไทยใด ๆ จาก prototype/SRS
3. ห้าม hardcode เมนูต่อ role ฝั่ง FE (ใช้ `/me/menus`)
4. ห้ามใส่ logic routing workflow (กฎ 100k, ขั้นถัดไป) ใน FE — หน้าที่ BE
5. ห้ามอ้าง section 04/05 หรือสถานะบัญชีในทุกที่ (SDD v7.5 ตัดแล้ว)
6. วันที่แสดงผลเป็น พ.ศ. ผ่าน `formatDateThai()` เท่านั้น — ห้ามแปลงเองกระจายตามหน้า
7. ห้าม import ข้าม feature · ห้าม barrel index.ts

## 14. Definition of Done (ทั้งโปรเจกต์ FE)

1. ครบ 14 route ใช้งานได้จริงกับ BE (`plan-be.md`) ผ่าน `docker compose up` — เดิน workflow ครบทั้งเคส ≤100k และ >100k
2. ทุกหน้าเทียบตากับหน้า prototype แล้วตรง: layout, สี pill/chip, ตาราง, ข้อความ (script grep เทียบ string สำคัญผ่าน)
3. validation ครบ: popup verbatim · %รวม 100% · ปี required · ไฟล์ ≤5MB+ext · comment required เมื่อไม่ชดเชย
4. CI เขียว (lint/tsc/test/build) · vitest ครอบ constants/format/DecisionPanel · Playwright e2e ผ่าน
5. ไม่มี dependency นอกรายการ §1-2 ใน package.json · bundle ไม่มี lib แปลกปลอม
6. AbnormalListPage สร้างเสร็จแต่ปิด flag — เปิดได้ด้วยแก้ env ตัวเดียว
