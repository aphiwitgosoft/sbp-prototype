import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

/** โครงหลัก (แทน header/sidebar ที่ sbp.js inject) */
export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="min-h-screen">
      <Header onToggleSidebar={() => setCollapsed((v) => !v)} />
      <div className="flex items-start">
        <Sidebar collapsed={collapsed} />
        <main className="min-w-0 flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
