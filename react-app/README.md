# SBP Management System — React + Vite + TypeScript + Tailwind

พอร์ตของ prototype `ระบบประกันรายได้ (K2/SBPGI)` จาก static HTML (`../`) มาเป็น SPA

## เริ่มใช้งาน

```bash
cd react-app
npm install
npm run dev:mock  # ★ แนะนำ — เปิดพร้อม mock API (MSW) ที่ /api/v1/*
npm run dev       # เปิดเฉย ๆ (ไม่มี mock — หน้า data จะขึ้น error ให้รัน dev:mock)
npm run build     # typecheck + build production (dist/)
npm run preview   # ดู build
```

## Mock API (MSW)

`npm run dev:mock` เปิด **Mock Service Worker** intercept `/api/v1/*` ตามสเปกใน `api.md`
- handler: `src/mocks/handlers.ts` · ข้อมูล: `src/mocks/db.ts` · worker: `public/mockServiceWorker.js`
- เปิด/ปิดผ่าน env `VITE_MOCK` (start ใน `src/main.tsx`)
- หน้า data ดึงผ่าน `useApi()` (`src/hooks/useApi.ts`) → `apiGet()` (`src/lib/api.ts`)
- endpoint ที่ mock แล้ว: `dashboard/summary` · `tasks` · `documents(/:docNo)` · `reports/status-summary` · `operators` · `factors` · `configs` · `jobs` · `roles` · `menu-permissions` · `email-templates` · `competitors` · `stores/search` · `document-statuses` · `workflow-sections`

## โครงสร้างโฟลเดอร์ (มาตรฐาน)

```
react-app/
├─ index.html                # entry (โหลดฟอนต์ Prompt/Sarabun)
├─ vite.config.ts            # alias @ → src
├─ tailwind.config.ts        # design tokens จาก sbp.css :root
├─ postcss.config.js
├─ tsconfig*.json
└─ src/
   ├─ main.tsx               # bootstrap
   ├─ App.tsx                # Router (ครบทุก route)
   ├─ styles/globals.css     # Tailwind + component class (.card/.pill/.btn/table.data ฯลฯ)
   ├─ types/                 # TypeScript types (ModuleItem, PillKind ฯลฯ)
   ├─ data/                  # modules.ts = MODULES registry (ขับ sidebar+breadcrumb)
   ├─ lib/                   # helper (cn, format)
   ├─ hooks/                 # useToast (แทน window.SBP.toast)
   ├─ components/
   │  ├─ layout/             # AppLayout · Header · Sidebar
   │  ├─ ui/                 # Card · Pill · StatCard · Button · Tabs · PageHead · PagePlaceholder
   │  └─ charts/             # BarChart · DonutChart · SparkChart (พอร์ตจาก sbp.js)
   └─ pages/                 # หนึ่งไฟล์ต่อหนึ่งหน้าจอ
```

## สถานะการพอร์ต (ครบทุกหน้า)

| หน้า | route | สถานะ |
|---|---|---|
| Overview (dashboard) | `/` | ✅ `dashboard/summary` + กราฟ + module grid |
| สร้างเอกสาร | `/create` | ✅ 2 แท็บ (Create New / FS) + ค้นหาร้าน `stores/search` |
| เอกสาร รอ/ที่เกี่ยวข้อง | `/documents/waiting` `/related` | ✅ role switcher + stepper 5 ขั้น + status 6 ค่า |
| รายละเอียดเอกสาร | `/documents/:docNo` | ✅ role switcher + แผนที่ AllMap + กราฟยอดขาย + คำนวณ + ไฟล์แนบ + timeline |
| รายงานสรุปสถานะ | `/report` | ✅ ฟอร์มกรอง + กราฟ + ตาราง **19 คอลัมน์** |
| ผู้ปฏิบัติงาน / ปัจจัย | `/operators` `/factors` | ✅ **CRUD** (modal) + ประวัติแก้ไข (audit_logs) |
| ตั้งค่าระบบ / Batch Job | `/config` `/jobs` | ✅ config: donut+แก้ค่า · jobs: **detail panel** (params/flowchart/db/history) |
| Email Template | `/email-templates` | ✅ **WYSIWYG editor** (toolbar + ตัวแปร + ตาราง + save/reset) |
| สิทธิ์การเข้าถึงเมนู | `/permissions` | ✅ matrix **toggle** + **Roles CRUD** |
| Flow (fgi/k2/combined) | `/flow/*` | ✅ Flowchart (SVG) + stage strip + lane compare |
| DB (fgi/k2/combined) | `/db/*` | ✅ Zone Map + Data Spine + **Data Dictionary 34 ตาราง** + cross-keys |
| API | `/api` | ✅ catalog **62 เส้น** → modal (Flow · Request/Response · Database+SQL · Flowchart) |

> ทุกหน้าต่อ mock API (MSW) · CRUD จริง (mutate in-memory) · path ทั้งหมดมาจาก `src/constants/{routes,api}.ts`

## หลักการพอร์ต

- **CSS**: token จาก `sbp.css :root` → `tailwind.config.ts` · class ที่ใช้ซ้ำ (`.card/.pill/.stat/.btn/table.data`) นิยามใน `globals.css` ด้วย `@apply`
- **sbp.js**: `MODULES` → `data/modules.ts` · header/sidebar/breadcrumb → `components/layout/*` · chart engine → `components/charts/*` · toast → `hooks/useToast`
- **ไอคอน**: ใช้ `lucide-react` (สไตล์ stroke เดียวกับ prototype) แทนการฝัง path SVG มือ
- prototype HTML เดิมยังอยู่ครบใน `../` (ไม่ถูกแตะ)
