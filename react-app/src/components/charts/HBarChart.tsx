/** พอร์ตจาก hbarChart ใน index.html/k2-report — แท่งแนวนอน + dot สถานะ + ป้ายค่าท้ายแท่ง */
export function HBarChart({
  rows,
  color = '#2f6fed',
  left = 224,
  unit = 'รายการ',
}: {
  rows: { label: string; value: number; dot?: string }[];
  color?: string;
  left?: number;
  unit?: string;
}) {
  const rowH = 30;
  const barH = 17;
  const W = 640;
  const right = 56;
  const H = rows.length * rowH + 8;
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  const span = W - left - right;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="เอกสารค้างตามขั้นตอน" className="block w-full">
      <line x1={left} y1={3} x2={left} y2={H - 4} stroke="#e4ebf3" strokeWidth={1.4} />
      {rows.map((r, i) => {
        const y = i * rowH + 7;
        const w = Math.max(5, Math.round(span * (r.value / max)));
        return (
          <g key={i}>
            <title>{`${r.label}: ${r.value} ${unit}`}</title>
            {r.dot && <circle cx={10} cy={y + barH / 2} r={4.5} fill={r.dot} />}
            <text x={r.dot ? 22 : 8} y={y + barH / 2 + 4} fontSize={11.5} fill="#55677d" fontFamily="Prompt,Sarabun,sans-serif">{r.label}</text>
            <path
              className="hb-bar transition-opacity hover:opacity-80"
              fill={color}
              d={`M${left},${y} h${w - 4} a4,4 0 0 1 4,4 v${barH - 8} a4,4 0 0 1 -4,4 h-${w - 4} z`}
            />
            <text x={left + w + 8} y={y + barH / 2 + 4} fontSize={11.5} fontWeight={600} fill="#2b3440" fontFamily="Sarabun,sans-serif">{r.value}</text>
          </g>
        );
      })}
    </svg>
  );
}
