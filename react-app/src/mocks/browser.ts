import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

/** worker สำหรับ dev:mock — start ใน main.tsx เมื่อ VITE_MOCK=true */
export const worker = setupWorker(...handlers);

export async function startMockWorker() {
  await worker.start({
    onUnhandledRequest: 'bypass', // ปล่อย request อื่น (asset ฯลฯ) ผ่าน
    quiet: false,
  });
  // eslint-disable-next-line no-console
  console.info('%c[MSW] mock API พร้อมใช้งานที่ /api/v1/*', 'color:#2f6fed;font-weight:600');
}
