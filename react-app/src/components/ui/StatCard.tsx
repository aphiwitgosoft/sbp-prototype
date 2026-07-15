import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/cn';

const BG: Record<string, string> = {
  blue: 'bg-primary',
  teal: 'bg-brandteal',
  amber: 'bg-warn',
  rose: 'bg-danger',
  navy: 'bg-indigo-500',
  green: 'bg-success',
};

export function StatCard({
  icon: Icon,
  value,
  label,
  tone = 'blue',
  onClick,
  active,
}: {
  icon: LucideIcon;
  value: string | number;
  label: string;
  tone?: keyof typeof BG;
  onClick?: () => void;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'stat text-left w-full',
        onClick && 'cursor-pointer hover:shadow-md transition-shadow',
        active && 'ring-2 ring-primary/50',
      )}
    >
      <span className={cn('si', BG[tone])}>
        <Icon size={22} strokeWidth={1.9} />
      </span>
      <span>
        <span className="sv num block">{value}</span>
        <span className="sl block">{label}</span>
      </span>
    </button>
  );
}
