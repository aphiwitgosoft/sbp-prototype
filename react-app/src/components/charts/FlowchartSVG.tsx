/** พอร์ต renderFlow จาก plan-api.html — วาด flowchart จาก node/edge spec เป็น inline SVG */

export type FcType = 'term' | 'termOk' | 'proc' | 'dec' | 'err';
export interface FcNode {
  id: string;
  type: FcType;
  x: number;
  y: number;
  w?: number;
  h?: number;
  text: string;
  fs?: number;
}
export interface FcEdge {
  from: string;
  to: string;
  label?: string;
  dir?: 'right';
}
export interface FcSpec {
  w: number;
  h: number;
  nodes: FcNode[];
  edges: FcEdge[];
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const fcW = (n: FcNode) => n.w || (n.type === 'dec' ? 240 : n.type === 'proc' ? 280 : n.type === 'err' ? 220 : 240);
const fcH = (n: FcNode) => n.h || (n.type === 'dec' ? 68 : n.type === 'proc' ? 52 : 40);

function fcText(n: FcNode, x: number, y: number): string {
  const lines = String(n.text).split('\n');
  const fs = n.fs || 11;
  const lh = fs + 3;
  const startY = y - ((lines.length - 1) * lh) / 2 + fs / 3;
  const col = n.type === 'err' ? '#c0392b' : n.type === 'termOk' ? '#15803d' : '#2b3440';
  return lines
    .map(
      (l, i) =>
        `<text x="${x}" y="${startY + i * lh}" text-anchor="middle" font-size="${fs}" fill="${col}" font-family="Prompt,Sarabun,sans-serif">${esc(l)}</text>`,
    )
    .join('');
}

function fcNode(n: FcNode): string {
  const x = n.x, y = n.y, w = fcW(n), h = fcH(n), half = w / 2, hh = h / 2;
  if (n.type === 'dec') {
    const pts = `${x},${y - hh} ${x + half},${y} ${x},${y + hh} ${x - half},${y}`;
    return `<polygon points="${pts}" fill="#fff4d6" stroke="#d9a441" stroke-width="1.5"/>${fcText(n, x, y)}`;
  }
  let fill = '#fff', stroke = '#96b4f0';
  if (n.type === 'term') { fill = '#eef4ff'; stroke = '#2f6fed'; }
  else if (n.type === 'termOk') { fill = '#e7f7ee'; stroke = '#15803d'; }
  else if (n.type === 'err') { fill = '#fdecec'; stroke = '#d98a8a'; }
  const rx = n.type === 'proc' ? 9 : h / 2;
  return `<rect x="${x - half}" y="${y - hh}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>${fcText(n, x, y)}`;
}

function fcEdge(e: FcEdge, byId: Record<string, FcNode>): string {
  const a = byId[e.from], b = byId[e.to];
  let x1, y1, x2, y2, lx, ly, anchor = '';
  if (e.dir === 'right') {
    x1 = a.x + fcW(a) / 2; y1 = a.y; x2 = b.x - fcW(b) / 2; y2 = b.y;
    lx = (x1 + x2) / 2; ly = y1 - 5; anchor = ' text-anchor="middle"';
  } else {
    x1 = a.x; y1 = a.y + fcH(a) / 2; x2 = b.x; y2 = b.y - fcH(b) / 2;
    lx = x1 + 8; ly = (y1 + y2) / 2;
  }
  const line = `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#8493a5" stroke-width="1.6" marker-end="url(#fcArrow)"/>`;
  const lbl = e.label
    ? `<text x="${lx}" y="${ly}" font-size="10" fill="#5d6b7a" font-family="Prompt,Sarabun,sans-serif"${anchor}>${esc(e.label)}</text>`
    : '';
  return line + lbl;
}

export function FlowchartSVG({ spec }: { spec: FcSpec }) {
  const byId: Record<string, FcNode> = {};
  spec.nodes.forEach((n) => (byId[n.id] = n));
  const markup =
    '<defs><marker id="fcArrow" markerWidth="9" markerHeight="9" refX="6.5" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L6.5,3 L0,6 Z" fill="#8493a5"/></marker></defs>' +
    spec.edges.map((e) => fcEdge(e, byId)).join('') +
    spec.nodes.map((n) => fcNode(n)).join('');
  return (
    <svg
      viewBox={`0 0 ${spec.w} ${spec.h}`}
      width="100%"
      style={{ minWidth: Math.min(spec.w, 560), maxWidth: spec.w, display: 'block', margin: '0 auto' }}
      role="img"
      aria-label="flowchart"
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}
