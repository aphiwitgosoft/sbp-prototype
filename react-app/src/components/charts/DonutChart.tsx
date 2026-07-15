import { useEffect, useRef } from 'react';

const DEFAULT_COLORS = ['#2f6fed', '#15b6a6', '#f59e0b', '#ef4444', '#7c3aed'];

/** พอร์ตจาก donut() ใน sbp.js — วงกลม + เลขรวมตรงกลาง (animate เข้า) */
export function DonutChart({
  values,
  colors = DEFAULT_COLORS,
  center = 'รวม',
}: {
  values: number[];
  colors?: string[];
  center?: string;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const total = values.reduce((a, b) => a + b, 0) || 1;
  const r = 52;
  const c = 2 * Math.PI * r;
  const cx = 70;
  const cy = 70;

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      ref.current?.querySelectorAll<SVGCircleElement>('.donutSeg').forEach((s) => {
        s.style.strokeDashoffset = '0';
      });
    });
    return () => cancelAnimationFrame(id);
  }, [values]);

  let acc = 0;
  return (
    <svg ref={ref} viewBox="0 0 140 140" width={150} height={150}>
      {values.map((v, i) => {
        const len = (v / total) * c;
        const rot = (acc / total) * 360 - 90;
        acc += v;
        return (
          <circle
            key={i}
            className="donutSeg"
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={colors[i % colors.length]}
            strokeWidth={15}
            strokeDasharray={`${len.toFixed(2)} ${(c - len).toFixed(2)}`}
            strokeDashoffset={len.toFixed(2)}
            transform={`rotate(${rot.toFixed(2)} ${cx} ${cy})`}
            style={{ transitionDelay: `${i * 120}ms` }}
          />
        );
      })}
      <text x={70} y={65} textAnchor="middle" className="donutBig">
        {total.toLocaleString()}
      </text>
      <text x={70} y={85} textAnchor="middle" className="donutSub">
        {center}
      </text>
    </svg>
  );
}
