import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';
import type { ToastKind } from '@/types';

interface ToastItem {
  id: number;
  msg: string;
  kind: ToastKind;
}

interface ToastCtx {
  toast: (msg: string, kind?: ToastKind) => void;
}

const Ctx = createContext<ToastCtx | null>(null);

/** แทน window.SBP.toast เดิม — เรียกผ่าน useToast().toast(msg, kind) */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const seq = useRef(0);

  const toast = useCallback((msg: string, kind: ToastKind = '') => {
    const id = ++seq.current;
    setItems((prev) => [...prev, { id, msg, kind }]);
    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id));
    }, 2600);
  }, []);

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[200] flex flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              'flex items-center gap-2.5 rounded-xl px-4 py-3 text-[13px] text-white shadow-lg animate-fadeInUp',
              t.kind === 'del' ? 'bg-red-600' : t.kind === 'ok' ? 'bg-green-600' : 'bg-slate-800',
            )}
          >
            <span className="h-2 w-2 rounded-full bg-white/80" />
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useToast ต้องอยู่ภายใน <ToastProvider>');
  return ctx;
}
