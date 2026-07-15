import { useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface TabDef {
  key: string;
  label: string;
  content: ReactNode;
}

/** กลุ่มแท็บ (แทน [data-tabs] เดิม) */
export function Tabs({ tabs, initial }: { tabs: TabDef[]; initial?: string }) {
  const [active, setActive] = useState(initial ?? tabs[0]?.key);
  return (
    <div>
      <div className="mb-4 flex gap-1 border-b border-line">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setActive(t.key)}
            className={cn(
              'px-4 py-2 text-[13.5px] font-medium -mb-px border-b-2 transition-colors',
              active === t.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted hover:text-ink',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tabs.map((t) => (
        <div key={t.key} hidden={t.key !== active}>
          {t.content}
        </div>
      ))}
    </div>
  );
}
