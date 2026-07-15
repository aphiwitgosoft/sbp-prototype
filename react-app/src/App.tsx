import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ToastProvider } from '@/hooks/useToast';
import { PagePlaceholder } from '@/components/ui/PagePlaceholder';
import { ROUTES } from '@/constants/routes';
import Overview from '@/pages/Overview';
import K2Create from '@/pages/K2Create';
import DocumentList from '@/pages/DocumentList';
import K2Document from '@/pages/K2Document';
import K2Report from '@/pages/K2Report';
import K2Operators from '@/pages/K2Operators';
import K2Factors from '@/pages/K2Factors';
import K2Permissions from '@/pages/K2Permissions';
import SystemConfig from '@/pages/SystemConfig';
import JobBatch from '@/pages/JobBatch';
import PlanEmail from '@/pages/PlanEmail';
import PlanApi from '@/pages/PlanApi';
import { FlowFgi, K2Flow, PlanFlow, FgiDatabase, K2Database, PlanDatabase } from '@/pages/reference';

/** route relative (ตัด '/' นำหน้า) ให้ child ของ layout ที่เป็น pathless */
const rel = (p: string) => p.replace(/^\//, '');

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Overview />} />
            <Route path={rel(ROUTES.create)} element={<K2Create />} />
            <Route path={rel(ROUTES.docsWaiting)} element={<DocumentList mode="waiting" />} />
            <Route path={rel(ROUTES.docsRelated)} element={<DocumentList mode="related" />} />
            <Route path={rel(ROUTES.documentPattern)} element={<K2Document />} />
            <Route path={rel(ROUTES.report)} element={<K2Report />} />
            <Route path={rel(ROUTES.operators)} element={<K2Operators />} />
            <Route path={rel(ROUTES.factors)} element={<K2Factors />} />
            <Route path={rel(ROUTES.permissions)} element={<K2Permissions />} />
            <Route path={rel(ROUTES.config)} element={<SystemConfig />} />
            <Route path={rel(ROUTES.jobs)} element={<JobBatch />} />
            <Route path={rel(ROUTES.emailTemplates)} element={<PlanEmail />} />
            <Route path={rel(ROUTES.flowFgi)} element={<FlowFgi />} />
            <Route path={rel(ROUTES.flowK2)} element={<K2Flow />} />
            <Route path={rel(ROUTES.flowCombined)} element={<PlanFlow />} />
            <Route path={rel(ROUTES.dbFgi)} element={<FgiDatabase />} />
            <Route path={rel(ROUTES.dbK2)} element={<K2Database />} />
            <Route path={rel(ROUTES.dbCombined)} element={<PlanDatabase />} />
            <Route path={rel(ROUTES.api)} element={<PlanApi />} />
            <Route path={ROUTES.notFound} element={<PagePlaceholder title="ไม่พบหน้า (404)" note="เส้นทางนี้ไม่มีในระบบ" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
