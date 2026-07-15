/** พอร์ตจาก bar() ใน sbp.js — แท่งสีเดียว ปลายมน label ใต้แท่ง */
export function BarChart({ values, labels = [] }: { values: number[]; labels?: string[] }) {
  const max = Math.max(...values) || 1;
  const W = 100;
  const H = 60;
  const n = values.length;
  const bw = (W / n) * 0.56;
  const gap = W / n;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" width="100%" height={120}>
      {values.map((v, i) => {
        const h = (v / max) * (H - 14);
        const x = i * gap + (gap - bw) / 2;
        const y = H - 12 - h;
        return (
          <rect
            key={i}
            className="barRect"
            x={x.toFixed(1)}
            y={y.toFixed(1)}
            width={bw.toFixed(1)}
            height={h.toFixed(1)}
            rx={2.2}
            style={{ animationDelay: `${i * 70}ms` }}
          />
        );
      })}
      {values.map((_, i) => (
        <text
          key={`l${i}`}
          className="barLab"
          x={(i * gap + gap / 2).toFixed(1)}
          y={H - 2}
          textAnchor="middle"
        >
          {labels[i] ?? ''}
        </text>
      ))}
    </svg>
  );
}
