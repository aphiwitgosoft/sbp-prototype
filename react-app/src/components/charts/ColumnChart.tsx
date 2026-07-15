/** พอร์ตจาก colChart ใน index.html — คอลัมน์รายเดือน หัวมน · ป้ายค่าเฉพาะแท่งสุดท้าย · gridline */
export function ColumnChart({
  rows,
  color = '#2f6fed',
  unit = 'ล้านบาท',
}: {
  rows: { label: string; value: number }[];
  color?: string;
  unit?: string;
}) {
  const W = 520;
  const H = 205;
  const base = H - 26;
  const top = 22;
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  const slot = W / rows.length;
  const bw = 30;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="ยอดชดเชยรายเดือน" className="block w-full">
      {[0.33, 0.66, 1].map((t) => {
        const gy = base - (base - top) * t;
        return <line key={t} x1={4} y1={gy} x2={W - 4} y2={gy} stroke="#eef2f8" strokeWidth={1.2} />;
      })}
      <line x1={4} y1={base} x2={W - 4} y2={base} stroke="#e4ebf3" strokeWidth={1.4} />
      {rows.map((r, i) => {
        const h = Math.max(6, Math.round((base - top) * (r.value / max)));
        const x = Math.round(i * slot + (slot - bw) / 2);
        const y = base - h;
        const last = i === rows.length - 1;
        return (
          <g key={i}>
            <title>{`${r.label}: ${r.value.toFixed(2)} ${unit}`}</title>
            <path
              className="cb-bar transition-opacity hover:opacity-80"
              fill={color}
              d={`M${x},${base} v-${h - 4} a4,4 0 0 1 4,-4 h${bw - 8} a4,4 0 0 1 4,4 v${h - 4} z`}
            />
            {last && (
              <text x={x + bw / 2} y={y - 7} textAnchor="middle" fontSize={11.5} fontWeight={700} fill="#2b3440" fontFamily="Sarabun,sans-serif">{r.value}</text>
            )}
            <text x={x + bw / 2} y={H - 8} textAnchor="middle" fontSize={11} fill="#8493a5" fontFamily="Prompt,Sarabun,sans-serif">{r.label}</text>
          </g>
        );
      })}
    </svg>
  );
}
