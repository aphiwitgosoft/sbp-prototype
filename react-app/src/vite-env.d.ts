/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 'true' เมื่อรันผ่าน `npm run dev:mock` — เปิด MSW mock API */
  readonly VITE_MOCK?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
