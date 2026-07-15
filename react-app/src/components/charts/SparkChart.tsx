import { useEffect, useId, useRef } from 'react';

/** พอร์ตจาก spark() ใน sbp.js — เส้นพื้นที่ gradient (animate วาดเส้น) */
export function SparkChart({ values }: { values: number[] }) {
  const gid = useId().replace(/:/g, '');
  const pathRef = useRef<SVGPathElement>(null);
  const W = 240;
  const H = 60;
  const max = Math.max(...values);
  const min = Math.min(...values);

  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - 6 - ((v - min) / (max - min || 1)) * (H - 16);
    return [x, y] as const;
  });
  const line = 'M' + pts.map((p) => `${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' L');
  const area = `${line} L${W} ${H} L0 ${H} Z`;

  useEffect(() => {
    const p = pathRef.current;
    if (!p) return;
    const L = p.getTotalLength();
    p.style.strokeDasharray = String(L);
    p.style.strokeDashoffset = String(L);
    const id = requestAnimationFrame(() => {
      p.style.transition = 'stroke-dashoffset 1.3s ease';
      p.style.strokeDashoffset = '0';
    });
    return () => cancelAnimationFrame(id);
  }, [values]);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2f6fed" stopOpacity=".28" />
          <stop offset="1" stopColor="#2f6fed" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path
        ref={pathRef}
        className="sparkLine"
        d={line}
        fill="none"
        stroke="#2f6fed"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
