import { Link, useLocation } from 'react-router-dom';
import { Menu, ChevronRight, ChevronDown } from 'lucide-react';
import { findModuleByPath } from '@/data/modules';
import { ROUTES } from '@/constants/routes';
import { useToast } from '@/hooks/useToast';

export function Header({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  const { pathname } = useLocation();
  const { crumb } = findModuleByPath(pathname);
  const { toast } = useToast();
  const isHome = pathname === '/';

  return (
    <header className="sticky top-0 z-40 flex h-header items-center gap-4 border-b border-line bg-card px-6">
      <button
        onClick={onToggleSidebar}
        aria-label="เมนู"
        className="flex rounded-lg p-1.5 text-slate-600 hover:bg-slate-100"
      >
        <Menu size={24} />
      </button>

      <Link to={ROUTES.home} className="flex flex-none items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-seven-green font-bold text-white">
          7
        </span>
        <span className="hidden text-[15px] font-semibold text-ink sm:block">
          SBP Management
        </span>
      </Link>

      <nav className="ml-1.5 flex items-center gap-2 text-[14px] text-muted">
        <Link to={ROUTES.home} className="hover:text-primary">
          Home
        </Link>
        <ChevronRight size={16} className="opacity-55" />
        {isHome ? (
          <span>SBP Management System</span>
        ) : (
          <Link to={ROUTES.home} className="hover:text-primary">
            SBP Management System
          </Link>
        )}
        {crumb && !isHome && (
          <>
            <ChevronRight size={16} className="opacity-55" />
            <span className="font-medium text-slate-700">{crumb}</span>
          </>
        )}
      </nav>

      <div className="ml-auto flex items-center gap-4">
        <button
          onClick={() => toast('สลับภาษา: ไทย / English (ตัวอย่าง)')}
          className="flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1.5 font-medium text-slate-600 hover:bg-slate-50"
        >
          <span className="overflow-hidden rounded-[2px] leading-none shadow-[0_0_0_1px_rgba(0,0,0,.06)]">
            <span className="block h-[3px] w-[22px] bg-[#A51931]" />
            <span className="block h-[3px] w-[22px] bg-white" />
            <span className="block h-[6px] w-[22px] bg-[#2D2A4A]" />
            <span className="block h-[3px] w-[22px] bg-white" />
            <span className="block h-[3px] w-[22px] bg-[#A51931]" />
          </span>
          TH <ChevronDown size={16} />
        </button>

        <button
          onClick={() => toast('โปรไฟล์ผู้ใช้ (ตัวอย่าง)')}
          className="flex items-center gap-2.5"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-brandteal to-brandteal/70 font-semibold text-white">
            P
          </span>
          <span className="hidden text-left leading-tight md:block">
            <span className="block text-[13.5px] font-semibold text-ink">Phatcharida P.</span>
            <span className="block text-[12px] text-muted">Administrator</span>
          </span>
        </button>
      </div>
    </header>
  );
}
