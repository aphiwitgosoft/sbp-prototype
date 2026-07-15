import { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { MODULES } from '@/data/modules';
import type { ModuleGroup, ModuleItem } from '@/types';
import { cn } from '@/lib/cn';

/** จัดกลุ่ม MODULES ตามลำดับ group ที่ปรากฏครั้งแรก */
function useGroups() {
  return useMemo(() => {
    const groups: { name: ModuleGroup; items: ModuleItem[] }[] = [];
    for (const m of MODULES) {
      let g = groups.find((x) => x.name === m.group);
      if (!g) {
        g = { name: m.group, items: [] };
        groups.push(g);
      }
      g.items.push(m);
    }
    return groups;
  }, []);
}

const itemBase =
  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] transition-colors';

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  const groups = useGroups();
  const { pathname } = useLocation();

  return (
    <aside
      className={cn(
        'sticky top-header h-[calc(100vh-64px)] shrink-0 overflow-y-auto border-r border-line bg-sidebar px-3 py-4 transition-[width]',
        collapsed ? 'w-0 overflow-hidden px-0' : 'w-sidebar',
      )}
    >
      <nav className="flex flex-col gap-1">
        {groups.map((g) => (
          <div key={g.name}>
            <div className="px-3 pb-1.5 pt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {g.name}
            </div>
            {g.items.map((m) =>
              m.children ? (
                <ParentItem key={m.key} item={m} currentPath={pathname} />
              ) : (
                <NavLink
                  key={m.key}
                  to={m.path!}
                  end={m.path === '/'}
                  className={({ isActive }) =>
                    cn(
                      itemBase,
                      isActive
                        ? 'bg-primary font-medium text-white shadow-sm'
                        : 'text-slate-600 hover:bg-white',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <m.icon size={20} strokeWidth={1.9} className="flex-none" />
                      <span className="flex-1">{m.label}</span>
                      {isActive && <ChevronRight size={18} />}
                    </>
                  )}
                </NavLink>
              ),
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
}

function ParentItem({ item, currentPath }: { item: ModuleItem; currentPath: string }) {
  const childActive = item.children!.some((c) => c.path === currentPath);
  // เปิดค้างเมื่อ child ตัวใดตัวหนึ่ง active (ไม่มี toggle collapse แยก เพื่อความเรียบง่าย)
  const open = childActive || true;

  return (
    <div>
      <div
        className={cn(
          itemBase,
          childActive ? 'font-medium text-primary' : 'text-slate-600',
        )}
      >
        <item.icon size={20} strokeWidth={1.9} className="flex-none" />
        <span className="flex-1">{item.label}</span>
        <ChevronRight size={16} className={cn('transition-transform', open && 'rotate-90')} />
      </div>
      {open && (
        <div className="ml-4 flex flex-col gap-1 border-l border-line pl-2">
          {item.children!.map((c) => (
            <NavLink
              key={c.key}
              to={c.path}
              className={({ isActive }) =>
                cn(
                  'rounded-lg px-3 py-2 text-[13px] transition-colors',
                  isActive
                    ? 'bg-primary font-medium text-white'
                    : 'text-slate-600 hover:bg-white',
                )
              }
            >
              {c.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}
