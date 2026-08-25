#!/usr/bin/env python3
"""สร้าง ER Diagram ฉบับสมบูรณ์ของ SBPGI → output/diagrams/

ผลลัพธ์
  output/diagrams/er-sbpgi-complete.svg     ภาพเวกเตอร์ (แหล่งจริงของรูป)
  output/diagrams/er-sbpgi-complete.html    หน้าโต้ตอบ (zoom/pan · คลิกตารางเพื่อไล่เส้น · ค้นหา · ภาคผนวกตารางทั้งหมด)
  output/diagrams/er-sbpgi-complete.md      รายการความสัมพันธ์ + mermaid erDiagram
  output/diagrams/er-sbpgi-complete.png     ภาพ raster (ถ้ามี Chrome — สคริปต์เรนเดอร์ให้เอง)

ใช้:  python3 tools/build_er_diagram.py [--no-png]
"""

from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from er_model import CROSS, FORBIDDEN, GROUPS, KEY_COLS, NOTES, WARNINGS  # noqa: E402
from er_sources import ROOT, Table, load_all  # noqa: E402

OUT = ROOT / "output" / "diagrams"
STEM = "er-sbpgi-complete"

# ------------------------------------------------------------------ ขนาด/ระยะ

ROW_H = 15.0
HEAD_H = 34.0
FOOT_H = 14.0
BOX_GAP_Y = 22.0
BOX_GAP_X = 26.0
GROUP_PAD = 16.0
GROUP_HEAD = 44.0
GRID_GAP_X = 90.0
GRID_GAP_Y = 70.0
CANVAS_PAD = 40.0
TITLE_H = 250.0
CHAR_W = 6.05          # ความกว้างต่อตัวอักษรของฟอนต์ monospace 10.2px
NAME_FS = 10.2
TYPE_FS = 8.9

# Data Spine ตาม database.md — ลำดับ ID ที่ใช้ trace หนึ่งรายการผลกระทบตั้งแต่ต้นจนจบ
SPINE = {
    "sbpgi.fgi_impact_processes": "1",
    "sbpgi.compensation_documents": "2",
    "sps_store.workflow_transaction": "3",
    "sps_store.workflow_approver": "4",
    "sps_store.business_user": "5",
}

KIND_STYLE = {
    "fk": {"dash": "", "w": 1.7, "op": 0.95},
    "logical": {"dash": "6 4", "w": 1.35, "op": 0.8},
    "api": {"dash": "9 3", "w": 2.3, "op": 1.0, "color": "#e11d48"},
    "snapshot": {"dash": "1.5 4", "w": 1.8, "op": 0.9, "color": "#7c3aed"},
}


class Box:
    def __init__(self, table: Table, group: dict, shown: list, hidden: int):
        self.t = table
        self.g = group
        self.shown = shown            # list[Column]
        self.hidden = hidden
        self.x = 0.0
        self.y = 0.0
        self.w = 0.0
        self.h = HEAD_H + ROW_H * len(shown) + (FOOT_H if hidden else 6.0)

    @property
    def key(self) -> str:
        return self.t.key

    def row_y(self, col_name: str) -> float:
        for i, c in enumerate(self.shown):
            if c.name == col_name:
                return self.y + HEAD_H + ROW_H * i + ROW_H / 2
        return self.y + HEAD_H / 2 + 6

    def has(self, col_name: str) -> bool:
        return any(c.name == col_name for c in self.shown)


# ------------------------------------------------------------------ ประกอบข้อมูล


def build_boxes(schemas: dict[str, dict[str, Table]]) -> tuple[dict[str, Box], list[dict]]:
    boxes: dict[str, Box] = {}
    groups: list[dict] = []
    for g in GROUPS:
        gg = dict(g)
        gg["boxes"] = []
        for column in g["columns"]:
            for name in column:
                src = g["schema"]
                # fcs_qssi_score อยู่ในโครงโซน A แต่ตัวตารางจริงอยู่ schema sps_store
                lookup = "sps_store" if name == "fcs_qssi_score" else src
                table = schemas[lookup].get(name)
                if table is None:
                    raise SystemExit(f"ไม่พบตาราง {lookup}.{name} ในแหล่งข้อมูล")
                key = f"{src}.{name}"
                if key in boxes:
                    continue
                shown, hidden = _shown_columns(key, table)
                b = Box(table, gg, shown, hidden)
                b.w = 0.0
                boxes[key] = b
                gg["boxes"].append(key)
        groups.append(gg)

    for g in groups:
        widest = 0.0
        for k in g["boxes"]:
            b = boxes[k]
            for c in b.shown:
                widest = max(widest, len(c.name) * CHAR_W + len(c.type) * CHAR_W * 0.87 + 42)
            widest = max(widest, len(b.t.name) * 6.9 + 74)
        widest = min(max(widest, 190.0), 372.0)
        for k in g["boxes"]:
            boxes[k].w = widest
    return boxes, groups


def _shown_columns(key: str, t: Table):
    if key in KEY_COLS:
        wanted = KEY_COLS[key]
        shown = [c for name in wanted for c in t.columns if c.name == name]
        return shown, len(t.columns) - len(shown)
    return list(t.columns), 0


def layout(boxes: dict[str, Box], groups: list[dict]) -> tuple[float, float]:
    # 1) ขนาดของแต่ละกลุ่ม
    for g in groups:
        col_w, col_h = [], []
        for column in g["columns"]:
            keys = [f"{g['schema']}.{n}" for n in column]
            col_w.append(max(boxes[k].w for k in keys))
            col_h.append(sum(boxes[k].h for k in keys) + BOX_GAP_Y * (len(keys) - 1))
        g["_w"] = sum(col_w) + BOX_GAP_X * (len(col_w) - 1) + GROUP_PAD * 2
        g["_h"] = max(col_h) + GROUP_HEAD + GROUP_PAD
        g["_colw"] = col_w

    # 2) วางกลุ่มเป็นแถว — ความกว้างของแต่ละแถวอิสระต่อกัน (กันช่องว่างใหญ่กลางรูป)
    rows = max(g["cell"][0] for g in groups) + 1
    gh = [max((g["_h"] for g in groups if g["cell"][0] == r), default=0) for r in range(rows)]
    gy = [TITLE_H + sum(gh[:r]) + GRID_GAP_Y * r for r in range(rows)]
    width = 0.0
    for r in range(rows):
        x = CANVAS_PAD
        for g in sorted((g for g in groups if g["cell"][0] == r), key=lambda g: g["cell"][1]):
            g["_x"], g["_y"] = x, gy[r]
            x += g["_w"] + GRID_GAP_X
        width = max(width, x - GRID_GAP_X + CANVAS_PAD)
        if r == 0:  # เผื่อที่ให้การ์ดหมายเหตุด้านขวาของแถวบน
            width = max(width, x - GRID_GAP_X + GRID_GAP_X * 0.6 + 555 + CANVAS_PAD)

    # 3) วางกล่องในกลุ่ม
    for g in groups:
        x = g["_x"] + GROUP_PAD
        for ci, column in enumerate(g["columns"]):
            y = g["_y"] + GROUP_HEAD
            for n in column:
                b = boxes[f"{g['schema']}.{n}"]
                b.x, b.y = x, y
                y += b.h + BOX_GAP_Y
            x += g["_colw"][ci] + BOX_GAP_X
    height = gy[-1] + gh[-1] + CANVAS_PAD
    return width, height


def build_edges(boxes: dict[str, Box]) -> list[dict]:
    edges: list[dict] = []
    seen: set[tuple] = set()

    def add(src, scol, dst, dcol, kind, card, label, ev, status):
        if src not in boxes or dst not in boxes:
            return
        sig = (src, scol, dst, dcol)
        if sig in seen:
            return
        seen.add(sig)
        edges.append({
            "src": src, "scol": scol, "dst": dst, "dcol": dcol, "kind": kind,
            "card": card, "label": label, "ev": ev, "status": status,
            "cross": boxes[src].g["key"] != boxes[dst].g["key"],
        })

    # FK จริงจาก DDL / dump
    for key, b in boxes.items():
        schema = key.split(".", 1)[0]
        for col, tgt, tcol in b.t.fks:
            tgt_key = f"{schema}.{tgt}"
            if tgt_key not in boxes and f"{b.t.schema}.{tgt}" in boxes:
                tgt_key = f"{b.t.schema}.{tgt}"
            add(key, col, tgt_key, tcol, "fk", "N:1", "FK", f"{schema} · DDL/dump", "confirmed")

    for row in CROSS:
        add(*row)
    return edges


def validate(boxes: dict[str, Box], edges: list[dict], schemas: dict) -> list[str]:
    """ตรวจว่าคอลัมน์ทุกเส้นมีอยู่จริงในแหล่งข้อมูล — คอลัมน์ในวงเล็บคือ pseudo-column ที่ตั้งใจ"""
    problems: list[str] = []
    declared = {(r[0], r[2]) for r in CROSS}
    for e in edges:
        for key, col in ((e["src"], e["scol"]), (e["dst"], e["dcol"])):
            if col.startswith("(") or col == "FK":
                continue
            b = boxes.get(key)
            if b is None:
                problems.append(f"ไม่มีตาราง {key}")
            elif not b.t.col(col):
                problems.append(f"ไม่มีคอลัมน์ {key}.{col} (เส้น {e['src']}→{e['dst']})")
    for key, b in boxes.items():
        if not any(e["src"] == key or e["dst"] == key for e in edges):
            problems.append(f"ตาราง {key} ไม่มีความสัมพันธ์เลย — ตรวจว่าตกหล่นหรือไม่")
    for src, dst in declared:
        if src not in boxes or dst not in boxes:
            problems.append(f"CROSS อ้างตารางที่ไม่ได้อยู่บนรูป: {src} → {dst}")
    return problems


# ---------------------------------------------------------------------- SVG


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def anchors(a: Box, b: Box, scol: str, dcol: str) -> tuple[float, float, float, float, str]:
    ay, by = a.row_y(scol), b.row_y(dcol)
    if a is b:  # ความสัมพันธ์กับตัวเอง (เช่น parent_id) — วนออกทางขวาของกล่อง
        return a.x + a.w, ay, a.x + a.w, by, "self"
    a_cx, b_cx = a.x + a.w / 2, b.x + b.w / 2
    overlap = not (b.x > a.x + a.w + 10 or a.x > b.x + b.w + 10)
    if overlap and abs(b_cx - a_cx) < max(a.w, b.w) * 0.75:
        # ซ้อนกันในแนวนอน → ออกทางบน/ล่าง
        if b.y > a.y:
            return a_cx, a.y + a.h, b_cx, b.y, "v"
        return a_cx, a.y, b_cx, b.y + b.h, "v"
    if b_cx > a_cx:
        return a.x + a.w, ay, b.x, by, "h"
    return a.x, ay, b.x + b.w, by, "h"


def ctrl_points(x1, y1, x2, y2, mode):
    if mode == "self":
        return (x1 + 34, y1), (x2 + 34, y2)
    if mode == "v":
        dy = max(28.0, min(abs(y2 - y1) * 0.45, 150.0))
        s = 1 if y2 > y1 else -1
        return (x1, y1 + s * dy), (x2, y2 - s * dy)
    dx = max(38.0, min(abs(x2 - x1) * 0.42, 210.0))
    s = 1 if x2 >= x1 else -1
    return (x1 + s * dx, y1), (x2 - s * dx, y2)


def edge_path(x1, y1, x2, y2, mode) -> str:
    c1, c2 = ctrl_points(x1, y1, x2, y2, mode)
    return (f"M {x1:.1f} {y1:.1f} C {c1[0]:.1f} {c1[1]:.1f} "
            f"{c2[0]:.1f} {c2[1]:.1f} {x2:.1f} {y2:.1f}")


def bezier_at(x1, y1, x2, y2, mode, t: float):
    """จุดบนเส้นโค้งที่สัดส่วน t — ใช้วางป้ายกำกับให้อยู่ใกล้ตารางต้นทาง ไม่ลอยกลางรูป"""
    c1, c2 = ctrl_points(x1, y1, x2, y2, mode)
    u = 1 - t
    bx = u**3 * x1 + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * x2
    by = u**3 * y1 + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * y2
    return bx, by


def render_svg(boxes: dict[str, Box], groups: list[dict], edges: list[dict], w: float, h: float,
               schemas: dict) -> str:
    p: list[str] = []
    p.append(
        f'<svg id="er" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">'
    )
    p.append("""<defs>
<marker id="many" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="9" markerHeight="9" orient="auto">
  <path d="M11 6 L1 1 M11 6 L1 6 M11 6 L1 11" fill="none" stroke="context-stroke" stroke-width="1.3"/>
</marker>
<marker id="many-s" viewBox="0 0 12 12" refX="1" refY="6" markerWidth="9" markerHeight="9" orient="auto">
  <path d="M1 6 L11 1 M1 6 L11 6 M1 6 L11 11" fill="none" stroke="context-stroke" stroke-width="1.3"/>
</marker>
<marker id="one" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="9" markerHeight="9" orient="auto">
  <path d="M8 1 L8 11" fill="none" stroke="context-stroke" stroke-width="1.6"/>
</marker>
<marker id="one-s" viewBox="0 0 12 12" refX="3" refY="6" markerWidth="9" markerHeight="9" orient="auto">
  <path d="M4 1 L4 11" fill="none" stroke="context-stroke" stroke-width="1.6"/>
</marker>
<style>
  .tname{font:700 12.5px ui-monospace,Menlo,monospace}
  .tmeta{font:9px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#ffffffcc}
  .cn{font:10.2px ui-monospace,Menlo,monospace;fill:#0f172a}
  .ct{font:8.9px ui-monospace,Menlo,monospace;fill:#94a3b8}
  .cpk{font:700 10.2px ui-monospace,Menlo,monospace;fill:#0f172a}
  .foot{font:8.6px "Noto Sans Thai",system-ui,sans-serif;fill:#94a3b8}
  .gt{font:700 17px "Noto Sans Thai","Sarabun",system-ui,sans-serif}
  .gs{font:11px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#64748b}
  .el{font:8.6px "Noto Sans Thai",system-ui,sans-serif;fill:#475569;paint-order:stroke;stroke:#fff;stroke-width:3.2px;stroke-linejoin:round}
  .h1{font:700 30px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#0f172a}
  .h2{font:14px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#475569}
  .lg{font:11.5px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#334155}
  .lgb{font:700 12px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#0f172a}
  .warn{font:10.5px "Noto Sans Thai","Sarabun",system-ui,sans-serif;fill:#9a3412}
</style></defs>""")
    p.append(f'<rect width="{w:.0f}" height="{h:.0f}" fill="#f8fafc"/>')
    p.append(_title_block(w, boxes, edges, schemas))
    p.append(_notes_card(groups, w))

    # กรอบกลุ่ม
    for g in groups:
        subs = "".join(
            f'<text class="gs" x="{g["_x"]+18:.0f}" y="{g["_y"]+39+i*13:.0f}">{esc(line)}</text>'
            for i, line in enumerate(g["subtitle"].split("\n"))
        )
        p.append(
            f'<g class="grp" data-g="{g["key"]}">'
            f'<rect x="{g["_x"]:.0f}" y="{g["_y"]:.0f}" width="{g["_w"]:.0f}" height="{g["_h"]:.0f}" rx="14" '
            f'fill="{g["tint"]}" stroke="{g["color"]}" stroke-width="1.6" stroke-opacity=".55"/>'
            f'<rect x="{g["_x"]:.0f}" y="{g["_y"]:.0f}" width="6" height="{g["_h"]:.0f}" rx="3" fill="{g["color"]}"/>'
            f'<text class="gt" x="{g["_x"]+18:.0f}" y="{g["_y"]+24:.0f}" fill="{g["color"]}">{esc(g["title"])}</text>'
            f'{subs}</g>'
        )

    # เส้นความสัมพันธ์ (วาดก่อนกล่อง เพื่อให้กล่องทับปลายเส้นไม่ได้ — ใช้ opacity ต่ำ)
    p.append('<g id="edges" fill="none">')
    for i, e in enumerate(edges):
        a, b = boxes[e["src"]], boxes[e["dst"]]
        x1, y1, x2, y2, mode = anchors(a, b, e["scol"], e["dcol"])
        st = KIND_STYLE[e["kind"]]
        color = st.get("color") or a.g["color"]
        op = st["op"] * (0.55 if e["status"].startswith("undecided") else 1.0)
        card = e["card"]
        ms = "many-s" if card.startswith("N") else "one-s"
        me = "many" if card.endswith("N") else "one"
        dash = f' stroke-dasharray="{st["dash"]}"' if st["dash"] else ""
        p.append(
            f'<path class="edge" id="e{i}" data-s="{esc(e["src"])}" data-t="{esc(e["dst"])}" '
            f'data-k="{e["kind"]}" data-st="{esc(e["status"])}" '
            f'd="{edge_path(x1, y1, x2, y2, mode)}" stroke="{color}" stroke-width="{st["w"]}"{dash} '
            f'stroke-opacity="{op:.2f}" marker-start="url(#{ms})" marker-end="url(#{me})">'
            f'<title>{esc(e["src"] + "." + e["scol"] + "  →  " + e["dst"] + "." + e["dcol"])}\n'
            f'{esc(e["card"])} · {esc(e["kind"])} · {esc(e["status"])}\n{esc(e["label"])}\n{esc(e["ev"])}</title></path>'
        )
    p.append("</g>")

    # ป้ายกำกับเส้นข้ามกลุ่ม
    p.append('<g id="elabels">')
    for i, e in enumerate(edges):
        if not e["cross"] or e["kind"] == "fk":
            continue
        a, b = boxes[e["src"]], boxes[e["dst"]]
        x1, y1, x2, y2, mode = anchors(a, b, e["scol"], e["dcol"])
        # สลับตำแหน่งป้ายตามลำดับเส้น กันป้ายทับกันเมื่อเส้นวิ่งไปทางเดียวกัน
        mx, my = bezier_at(x1, y1, x2, y2, mode, 0.22 + 0.07 * (i % 4))
        my -= 4
        txt = e["label"]
        if e["status"].startswith("undecided"):
            txt += f' [{e["status"].split("·")[-1].strip()}]'
        p.append(
            f'<text class="el" x="{mx:.0f}" y="{my:.0f}" text-anchor="middle" '
            f'data-s="{esc(e["src"])}" data-t="{esc(e["dst"])}">{esc(txt[:52])}</text>'
        )
    p.append("</g>")

    # กล่องตาราง
    warn = dict(WARNINGS)
    p.append('<g id="boxes">')
    for key, b in boxes.items():
        p.append(_box_svg(key, b, warn.get(key, "")))
    p.append("</g>")
    p.append("</svg>")
    return "\n".join(p)


def _box_svg(key: str, b: Box, warning: str) -> str:
    g, t = b.g, b.t
    color = g["color"]
    rows = []
    rows.append(
        f'<g class="tbl" id="{esc(key)}" data-key="{esc(key)}" data-g="{g["key"]}">'
        f'<rect x="{b.x:.0f}" y="{b.y:.0f}" width="{b.w:.0f}" height="{b.h:.0f}" rx="8" fill="#fff" '
        f'stroke="{color}" stroke-width="1.3"/>'
        f'<path d="M {b.x:.0f} {b.y+8:.0f} a8 8 0 0 1 8 -8 h {b.w-16:.0f} a8 8 0 0 1 8 8 '
        f'v {HEAD_H-8:.0f} h -{b.w:.0f} z" fill="{color}"/>'
        f'<text class="tname" x="{b.x+9:.0f}" y="{b.y+15:.0f}" fill="#fff">{esc(t.name)}</text>'
    )
    if t.schema != g["schema"]:
        meta = f"reuse จาก {t.schema} — ห้าม CREATE ใหม่"
    elif t.schema == "sbpgi":
        meta = f"sbpgi · โซน {g['key']} (ตารางใหม่)"
    else:
        meta = t.schema
    if t.rows and t.rows > 0:
        meta += f" · {t.rows:,} แถว"
    if b.hidden:
        meta += f" · {len(t.columns)} คอลัมน์"
    rows.append(f'<text class="tmeta" x="{b.x+9:.0f}" y="{b.y+27:.0f}">{esc(meta)}</text>')
    spine = SPINE.get(key)
    if spine:
        rows.append(
            f'<circle cx="{b.x+b.w-15:.0f}" cy="{b.y+16:.0f}" r="10" fill="#fff" stroke="{color}" stroke-width="2"/>'
            f'<text x="{b.x+b.w-15:.0f}" y="{b.y+20:.0f}" text-anchor="middle" font-size="12" '
            f'font-weight="700" fill="{color}">{spine}</text>'
        )

    fkcols = {c for c, _, _ in t.fks}
    for i, c in enumerate(b.shown):
        y = b.y + HEAD_H + ROW_H * i + ROW_H - 4
        if i % 2 == 1:
            rows.append(
                f'<rect x="{b.x+1:.0f}" y="{b.y+HEAD_H+ROW_H*i:.1f}" width="{b.w-2:.0f}" '
                f'height="{ROW_H:.1f}" fill="#f8fafc"/>'
            )
        mark, mcol = "", "#94a3b8"
        if c.is_pk:
            mark, mcol = "PK", "#b45309"
        elif c.name in fkcols:
            mark, mcol = "FK", "#2f6fed"
        elif c.is_uk:
            mark, mcol = "UK", "#0e7c6b"
        if mark:
            rows.append(
                f'<text x="{b.x+7:.0f}" y="{y:.1f}" font-size="7.4" font-weight="700" fill="{mcol}">{mark}</text>'
            )
        cls = "cpk" if c.is_pk else "cn"
        nn = c.name + ("" if c.nullable else " *")
        rows.append(f'<text class="{cls}" x="{b.x+26:.0f}" y="{y:.1f}">{esc(nn)}</text>')
        rows.append(
            f'<text class="ct" x="{b.x+b.w-8:.0f}" y="{y:.1f}" text-anchor="end">{esc(c.type)}</text>'
        )
    if b.hidden:
        rows.append(
            f'<text class="foot" x="{b.x+9:.0f}" y="{b.y+b.h-4:.0f}">+{b.hidden} คอลัมน์ที่ไม่ได้ใช้ใน SBPGI</text>'
        )
    if warning:
        rows.append(
            f'<rect x="{b.x:.0f}" y="{b.y-1:.0f}" width="{b.w:.0f}" height="{b.h+2:.0f}" rx="8" fill="none" '
            f'stroke="#dc2626" stroke-width="2" stroke-dasharray="4 3"/>'
            f'<text class="warn" x="{b.x:.0f}" y="{b.y-6:.0f}">⚠ {esc(warning)}</text>'
        )
    rows.append("</g>")
    return "".join(rows)


def _notes_card(groups: list[dict], canvas_w: float) -> str:
    """การ์ดสรุปมติ/ข้อค้าง วางในพื้นที่ว่างด้านขวาของแถวบนสุด"""
    row0 = [g for g in groups if g["cell"][0] == 0]
    right = max(g["_x"] + g["_w"] for g in groups if g["cell"][0] == 0)
    x = right + GRID_GAP_X * 0.6
    y = min(g["_y"] for g in row0)
    w = canvas_w - CANVAS_PAD - x
    h = max(g["_y"] + g["_h"] for g in row0) - y
    if w < 240:
        return ""
    p = [f'<g id="notes"><rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="14" '
         f'fill="#fff" stroke="#cbd5e1" stroke-width="1.4"/>']
    cy = y + 30
    for title, lines in NOTES:
        p.append(f'<text class="lgb" x="{x+16:.0f}" y="{cy:.0f}" fill="#0f172a">{esc(title)}</text>')
        cy += 8
        p.append(f'<line x1="{x+16:.0f}" y1="{cy:.0f}" x2="{x+w-16:.0f}" y2="{cy:.0f}" stroke="#e2e8f0"/>')
        cy += 15
        for line in lines:
            p.append(
                f'<text x="{x+16:.0f}" y="{cy:.0f}" font-size="10.4" '
                f'font-family="ui-monospace,Menlo,monospace" fill="#334155">{esc(line)}</text>'
            )
            cy += 14.5
        cy += 16
    p.append("</g>")
    return "".join(p)


def _title_block(w: float, boxes: dict[str, Box], edges: list[dict], schemas: dict) -> str:
    n_sbpgi = sum(1 for k in boxes if k.startswith("sbpgi."))
    n_store = sum(1 for k in boxes if k.startswith("sps_store."))
    n_auth = sum(1 for k in boxes if k.startswith("sps_auth."))
    kinds = {k: sum(1 for e in edges if e["kind"] == k) for k in KIND_STYLE}
    x = CANVAS_PAD
    p = [
        f'<text class="h1" x="{x:.0f}" y="{58:.0f}">ER Diagram ฉบับสมบูรณ์ · ระบบประกันรายได้ SBPGI</text>',
        f'<text class="h2" x="{x:.0f}" y="{84:.0f}">'
        f'FGI/FCS pipeline + K2 เอกสาร/workflow + master ใช้ร่วม + ฐานข้อมูลระบบ SBP เดิม '
        f'(schema sps_store · sps_auth) — เชื่อมความสัมพันธ์ครบทุกเส้น</text>',
        f'<text class="h2" x="{x:.0f}" y="{106:.0f}">'
        f'{n_sbpgi} ตาราง SBPGI · {n_store} ตาราง sps_store · {n_auth} ตาราง sps_auth · '
        f'{len(edges)} ความสัมพันธ์ '
        f'(FK {kinds["fk"]} · logical {kinds["logical"]} · ข้าม service {kinds["api"]} · snapshot {kinds["snapshot"]}) · '
        f'สร้างจาก LLDD-Database.md + SBP/db-schema-*.md (ดึงฐานจริง 07/08/2026)</text>',
    ]
    # legend
    lx = x
    ly = 136
    items = [
        ("เส้นทึบ", "fk", "Foreign key จริงในฐานข้อมูล"),
        ("เส้นประ", "logical", "Join key ที่ใช้จริงแต่ไม่มี FK (ฐานจริงมี FK แค่ 7 อันทั้ง schema)"),
        ("เส้นประยาวแดง", "api", "ข้ามขอบเขต service — เรียกผ่าน API/library ไม่ใช่ SQL join"),
        ("เส้นจุดม่วง", "snapshot", "คัดลอกค่าเก็บไว้ ณ เวลาหนึ่ง ไม่ใช่ join สด"),
    ]
    for i, (name, kind, desc) in enumerate(items):
        yy = ly + i * 19
        st = KIND_STYLE[kind]
        col = st.get("color", "#334155")
        dash = f' stroke-dasharray="{st["dash"]}"' if st["dash"] else ""
        p.append(
            f'<line x1="{lx:.0f}" y1="{yy-4:.0f}" x2="{lx+46:.0f}" y2="{yy-4:.0f}" stroke="{col}" '
            f'stroke-width="{st["w"]}"{dash}/>'
        )
        p.append(f'<text class="lgb" x="{lx+56:.0f}" y="{yy:.0f}">{esc(name)}</text>')
        p.append(f'<text class="lg" x="{lx+156:.0f}" y="{yy:.0f}">{esc(desc)}</text>')
    p.append(f'<text class="lgb" x="{lx:.0f}" y="{ly+82:.0f}">Data Spine — ID ที่ใช้ไล่หนึ่งรายการผลกระทบตั้งแต่ต้นจนจบ '
             f'<tspan class="lg">① impact_process_id → ② compensation_documents.id (= referenceId ที่ส่งให้ engine) '
             f'→ ③ transaction_id → ④ approver_id → ⑤ ผู้ปฏิบัติงาน (business_user)</tspan></text>')
    p.append(f'<text class="lg" x="{lx:.0f}" y="{ly+102:.0f}">'
             f'สัญลักษณ์ปลายเส้นเป็น crow\'s foot (ตีนกา = ด้าน "หลายแถว" · ขีดเดียว = ด้าน "หนึ่งแถว") · '
             f'ในกล่อง PK/FK/UK กำกับหน้าคอลัมน์ · เครื่องหมาย * ท้ายชื่อคอลัมน์ = NOT NULL · '
             f'กรอบแดงประ = ข้อควรระวังที่ต้องรู้ก่อนใช้ตารางนั้น</text>')

    fx = w - CANVAS_PAD - 640
    p.append(f'<text class="lgb" x="{fx:.0f}" y="{136:.0f}" fill="#9a3412">ตาราง/ชื่อที่ห้ามใช้</text>')
    for i, f in enumerate(FORBIDDEN):
        p.append(f'<text class="lg" x="{fx:.0f}" y="{155 + i*17:.0f}">✕ {esc(f)}</text>')
    return "\n".join(p)


# --------------------------------------------------------------------- HTML


def render_html(svg: str, boxes: dict[str, Box], edges: list[dict], schemas: dict) -> str:
    rel_rows = "".join(
        f"<tr data-k='{e['kind']}'><td><code>{esc(e['src'])}</code>.<b>{esc(e['scol'])}</b></td>"
        f"<td class='card'>{esc(e['card'])}</td>"
        f"<td><code>{esc(e['dst'])}</code>.<b>{esc(e['dcol'])}</b></td>"
        f"<td><span class='kind k-{e['kind']}'>{e['kind']}</span></td>"
        f"<td>{esc(e['label'])}</td>"
        f"<td class='{'undec' if e['status'].startswith('undecided') else ''}'>{esc(e['status'])}</td>"
        f"<td class='ev'>{esc(e['ev'])}</td></tr>"
        for e in sorted(edges, key=lambda e: (e["src"], e["scol"]))
    )
    drawn = set(boxes)
    cat = []
    for schema in ("sps_store", "sps_auth"):
        tabs = schemas[schema]
        rows = "".join(
            f"<tr class='{'on' if f'{schema}.{n}' in drawn else ''}'>"
            f"<td><code>{esc(n)}</code></td><td>{len(t.columns)}</td>"
            f"<td>{esc(','.join(t.pk) or '—')}</td>"
            f"<td>{t.rows if t.rows and t.rows > 0 else '—'}</td>"
            f"<td>{'●' if f'{schema}.{n}' in drawn else ''}</td>"
            f"<td>{esc(t.note)}</td></tr>"
            for n, t in sorted(tabs.items())
        )
        cat.append(
            f"<h3>schema <code>{schema}</code> — {len(tabs)} ตาราง/วิว "
            f"(บนรูป {sum(1 for k in drawn if k.startswith(schema + '.'))})</h3>"
            f"<table class='cat'><thead><tr><th>ตาราง</th><th>คอลัมน์</th><th>PK</th>"
            f"<th>แถว</th><th>บนรูป</th><th>หมายเหตุ (ใช้ใน SBPGI)</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    return f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ER Diagram ฉบับสมบูรณ์ · SBPGI</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#eef2f7;font-family:"Noto Sans Thai","Sarabun",system-ui,-apple-system,sans-serif;color:#0f172a}}
header{{position:sticky;top:0;z-index:9;background:#fff;border-bottom:1px solid #cbd5e1;padding:10px 16px;
 display:flex;gap:12px;align-items:center;flex-wrap:wrap;box-shadow:0 1px 4px #0f172a14}}
header b{{font-size:15px}}
input,select,button{{font:inherit;padding:5px 9px;border:1px solid #cbd5e1;border-radius:7px;background:#fff}}
button{{cursor:pointer}} button.on{{background:#0f172a;color:#fff;border-color:#0f172a}}
#wrap{{overflow:auto;height:calc(100vh - 52px);cursor:grab}} #wrap.drag{{cursor:grabbing}}
#stage{{transform-origin:0 0}}
svg .tbl{{cursor:pointer}}
body.focus svg .edge{{stroke-opacity:.05 !important}}
body.focus svg #elabels text{{opacity:.05}}
body.focus svg .tbl{{opacity:.28}}
body.focus svg .edge.hit{{stroke-opacity:1 !important;stroke-width:3}}
body.focus svg #elabels text.hit{{opacity:1}}
body.focus svg .tbl.hit{{opacity:1}}
svg .tbl.found rect:first-of-type{{stroke:#dc2626;stroke-width:3}}
#panel{{position:fixed;right:0;bottom:0;top:52px;width:min(560px,46vw);background:#fff;border-left:1px solid #cbd5e1;
 overflow:auto;padding:14px 18px;display:none;box-shadow:-4px 0 14px #0f172a14}}
#panel.show{{display:block}}
h2{{font-size:17px;margin:16px 0 6px}} h3{{font-size:14px;margin:18px 0 6px}}
table{{border-collapse:collapse;width:100%;font-size:11.5px}}
th,td{{border:1px solid #e2e8f0;padding:3px 6px;text-align:left;vertical-align:top}}
th{{background:#f1f5f9;position:sticky;top:0}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:11px}}
.card{{text-align:center;font-weight:700}}
.kind{{font-size:10px;padding:1px 6px;border-radius:99px;color:#fff}}
.k-fk{{background:#0f172a}} .k-logical{{background:#64748b}} .k-api{{background:#e11d48}} .k-snapshot{{background:#7c3aed}}
.undec{{color:#b45309;font-weight:700}} .ev{{color:#64748b;font-size:10.5px}}
tr.on td{{background:#ecfdf5}}
.cat td:nth-child(5){{text-align:center;color:#0e7c6b;font-weight:700}}
#tail{{background:#fff;padding:20px 26px;border-top:2px solid #cbd5e1}}
</style></head><body>
<header>
<b>ER Diagram ฉบับสมบูรณ์ · SBPGI</b>
<span style="color:#64748b;font-size:12px">{len(boxes)} ตาราง · {len(edges)} ความสัมพันธ์</span>
<input id="q" placeholder="ค้นหาตาราง/คอลัมน์…" size="22">
<button data-z="0.8">−</button><button data-z="1.25">+</button><button data-z="fit">พอดีจอ</button><button data-z="1">100%</button>
<button id="clr">ล้างการเลือก</button>
<button id="tgl">ตาราง/ภาคผนวก</button>
<span style="color:#64748b;font-size:12px">คลิกกล่องเพื่อดูเฉพาะเส้นของตารางนั้น · ลากเพื่อเลื่อน · Esc = ล้าง</span>
</header>
<div id="wrap"><div id="stage">{svg}</div></div>
<div id="panel"></div>
<div id="tail">
<h2>ความสัมพันธ์ทั้งหมด ({len(edges)} เส้น)</h2>
<table><thead><tr><th>จาก</th><th>ความสัมพันธ์</th><th>ไป</th><th>ชนิด</th><th>ความหมาย</th><th>สถานะ</th><th>หลักฐาน</th></tr></thead>
<tbody>{rel_rows}</tbody></table>
<h2>ภาคผนวก — ตารางทั้งหมดของฐานข้อมูลระบบ SBP เดิม</h2>
<p style="font-size:12.5px;color:#475569">แถวเขียว = ตารางที่ปรากฏบนรูป · ที่เหลือคือตารางอื่นของ schema เดียวกันที่ SBPGI ไม่ได้ใช้</p>
{''.join(cat)}
</div>
<script>
const wrap=document.getElementById('wrap'),stage=document.getElementById('stage'),svg=document.getElementById('er');
let z=1;
function setZ(v){{z=Math.max(.08,Math.min(3,v));stage.style.transform='scale('+z+')';
 stage.style.width=(svg.viewBox.baseVal.width*z)+'px';stage.style.height=(svg.viewBox.baseVal.height*z)+'px';}}
document.querySelectorAll('[data-z]').forEach(b=>b.onclick=()=>{{
 const v=b.dataset.z;
 if(v==='fit') setZ(Math.min(wrap.clientWidth/svg.viewBox.baseVal.width, wrap.clientHeight/svg.viewBox.baseVal.height));
 else if(v==='1') setZ(1); else setZ(z*parseFloat(v));}});
setZ(Math.min(wrap.clientWidth/svg.viewBox.baseVal.width,1));
let drag=null;
wrap.addEventListener('mousedown',e=>{{if(e.target.closest('.tbl'))return;drag={{x:e.clientX,y:e.clientY,l:wrap.scrollLeft,t:wrap.scrollTop}};wrap.classList.add('drag');}});
addEventListener('mousemove',e=>{{if(!drag)return;wrap.scrollLeft=drag.l-(e.clientX-drag.x);wrap.scrollTop=drag.t-(e.clientY-drag.y);}});
addEventListener('mouseup',()=>{{drag=null;wrap.classList.remove('drag');}});
wrap.addEventListener('wheel',e=>{{if(!e.ctrlKey&&!e.metaKey)return;e.preventDefault();setZ(z*(e.deltaY<0?1.12:0.89));}},{{passive:false}});

const REL={json.dumps([{k: e[k] for k in ('src','scol','dst','dcol','kind','card','label','status','ev')} for e in edges], ensure_ascii=False)};
const panel=document.getElementById('panel');
function focusTable(key){{
 document.body.classList.add('focus');
 document.querySelectorAll('.hit').forEach(n=>n.classList.remove('hit'));
 document.querySelectorAll('svg .edge, #elabels text').forEach(p=>{{
   if(p.dataset.s===key||p.dataset.t===key)p.classList.add('hit');}});
 const near=new Set([key]);
 REL.forEach(r=>{{if(r.src===key)near.add(r.dst);if(r.dst===key)near.add(r.src);}});
 document.querySelectorAll('svg .tbl').forEach(g=>{{if(near.has(g.dataset.key))g.classList.add('hit');}});
 const out=REL.filter(r=>r.src===key||r.dst===key);
 panel.innerHTML='<h3><code>'+key+'</code> — '+out.length+' ความสัมพันธ์</h3><table><thead><tr><th>จาก</th><th>ไป</th><th>ชนิด</th><th>ความหมาย</th><th>สถานะ</th></tr></thead><tbody>'
  +out.map(r=>'<tr><td><code>'+r.src+'</code>.<b>'+r.scol+'</b></td><td><code>'+r.dst+'</code>.<b>'+r.dcol+'</b></td>'
  +'<td><span class="kind k-'+r.kind+'">'+r.kind+'</span> '+r.card+'</td><td>'+r.label+'</td>'
  +'<td class="'+(r.status.startsWith('undecided')?'undec':'')+'">'+r.status+'</td></tr>').join('')
  +'</tbody></table>';
 panel.classList.add('show');
}}
svg.querySelectorAll('.tbl').forEach(g=>g.onclick=()=>focusTable(g.dataset.key));
function clearF(){{document.body.classList.remove('focus');panel.classList.remove('show');
 document.querySelectorAll('.hit,.found').forEach(n=>n.classList.remove('hit','found'));}}
document.getElementById('clr').onclick=clearF;
addEventListener('keydown',e=>{{if(e.key==='Escape')clearF();}});
document.getElementById('tgl').onclick=()=>document.getElementById('tail').scrollIntoView({{behavior:'smooth'}});
document.getElementById('q').oninput=e=>{{
 const v=e.target.value.trim().toLowerCase();
 document.querySelectorAll('svg .tbl').forEach(g=>g.classList.remove('found'));
 if(!v)return;
 svg.querySelectorAll('.tbl').forEach(g=>{{if(g.textContent.toLowerCase().includes(v))g.classList.add('found');}});
 const first=svg.querySelector('.tbl.found');
 if(first){{const b=first.getBBox();wrap.scrollTo({{left:b.x*z-80,top:b.y*z-80,behavior:'smooth'}});}}
}};
</script></body></html>"""


# ----------------------------------------------------------------------- MD


def render_md(boxes: dict[str, Box], edges: list[dict], schemas: dict) -> str:
    L: list[str] = []
    L.append("# ER Diagram ฉบับสมบูรณ์ — SBPGI + ฐานข้อมูลระบบ SBP เดิม\n")
    L.append("> สร้างอัตโนมัติด้วย `python3 tools/build_er_diagram.py` — **ห้ามแก้ไฟล์นี้ด้วยมือ**  ")
    L.append("> แหล่งข้อมูล: `LLDD/md/LLDD-Database.md` (DDL 20 ตาราง) · `SBP/db-schema-sps_store.md` · "
             "`SBP/db-schema-sps_auth.md` (ดึงฐานจริง 07/08/2026) · `database.md` (Cross-System Keys)  ")
    L.append("> รูป: `er-sbpgi-complete.svg` (เวกเตอร์) · `er-sbpgi-complete.png` · "
             "`er-sbpgi-complete.html` (โต้ตอบได้ · มีภาคผนวกตารางครบทุกตาราง)\n")

    n = {s: sum(1 for k in boxes if k.startswith(s + ".")) for s in ("sbpgi", "sps_store", "sps_auth")}
    L.append(f"**บนรูป:** {len(boxes)} ตาราง ({n['sbpgi']} SBPGI · {n['sps_store']} sps_store · "
             f"{n['sps_auth']} sps_auth) · {len(edges)} ความสัมพันธ์\n")

    for g in GROUPS:
        keys = [f"{g['schema']}.{t}" for col in g["columns"] for t in col]
        L.append(f"## {g['title']}\n")
        L.append(f"{g['subtitle']}\n")
        L.append("| ตาราง | คอลัมน์ | PK | ความสัมพันธ์ออก | แถวจริง |")
        L.append("|---|---|---|---|---|")
        for k in keys:
            b = boxes[k]
            out = sum(1 for e in edges if e["src"] == k)
            inc = sum(1 for e in edges if e["dst"] == k)
            rows = f"{b.t.rows:,}" if b.t.rows and b.t.rows > 0 else "—"
            L.append(f"| `{b.t.name}` | {len(b.t.columns)} | {', '.join(b.t.pk) or '—'} | "
                     f"ออก {out} · เข้า {inc} | {rows} |")
        L.append("")

    L.append("## ความสัมพันธ์ทั้งหมด\n")
    L.append("| จาก | | ไป | ชนิด | ความหมาย | สถานะ | หลักฐาน |")
    L.append("|---|---|---|---|---|---|---|")
    for e in sorted(edges, key=lambda e: (e["src"], e["scol"])):
        L.append(f"| `{e['src']}.{e['scol']}` | {e['card']} | `{e['dst']}.{e['dcol']}` | {e['kind']} | "
                 f"{e['label']} | {e['status']} | {e['ev']} |")
    L.append("")

    L.append("## ข้อควรระวังบนรูป\n")
    for k, v in WARNINGS:
        L.append(f"- `{k}` — {v}")
    L.append("\n## ตาราง/ชื่อที่ห้ามใช้\n")
    for f in FORBIDDEN:
        L.append(f"- ✕ {f}")

    L.append("\n## mermaid erDiagram (เฉพาะความสัมพันธ์ — ใช้ฝังในเอกสารอื่น)\n")
    L.append("```mermaid")
    L.append("erDiagram")
    for e in edges:
        s = e["src"].replace(".", "__")
        t = e["dst"].replace(".", "__")
        left = "}o" if e["card"].startswith("N") else "||"
        right = "o{" if e["card"].endswith("N") else "||"
        lbl = f'{e["scol"]}→{e["dcol"]}'
        L.append(f'    {s} {left}--{right} {t} : "{lbl}"')
    L.append("```")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------- เรนเดอร์ PNG


def render_png(html_path: Path, png_path: Path, width: int, height: int) -> bool:
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome).exists():
        return False
    svg_path = html_path.with_suffix(".svg")
    shell = OUT / "_png-shell.html"
    shell.write_text(
        f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#f8fafc}}'
        f'img{{display:block;width:{width}px;height:{height}px}}</style>'
        f'<img src="{svg_path.name}">',
        encoding="utf-8",
    )
    cmd = [
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={png_path}", f"--window-size={width},{height}",
        "--force-device-scale-factor=2", "--virtual-time-budget=15000",
        f"file://{shell}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=240)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! เรนเดอร์ PNG ไม่สำเร็จ: {exc}")
        return False
    finally:
        shell.unlink(missing_ok=True)
    return png_path.exists()


def main() -> None:
    schemas = load_all()
    boxes, groups = build_boxes(schemas)
    w, h = layout(boxes, groups)
    edges = build_edges(boxes)
    problems = validate(boxes, edges, schemas)
    for msg in problems:
        print(f"  ⚠ {msg}")
    svg = render_svg(boxes, groups, edges, w, h, schemas)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{STEM}.svg").write_text(svg, encoding="utf-8")
    (OUT / f"{STEM}.html").write_text(render_html(svg, boxes, edges, schemas), encoding="utf-8")
    (OUT / f"{STEM}.md").write_text(render_md(boxes, edges, schemas), encoding="utf-8")

    print(f"ตาราง {len(boxes)} · ความสัมพันธ์ {len(edges)} · ผืนผ้าใบ {w:.0f}×{h:.0f}")
    for s in ("sbpgi", "sps_store", "sps_auth"):
        print(f"  {s:10s} {sum(1 for k in boxes if k.startswith(s + '.')):3d} ตาราง")
    print(f"  → {OUT / (STEM + '.svg')}")
    print(f"  → {OUT / (STEM + '.html')}")
    print(f"  → {OUT / (STEM + '.md')}")

    if "--no-png" not in sys.argv:
        if render_png(OUT / f"{STEM}.html", OUT / f"{STEM}.png", int(w), int(h)):
            print(f"  → {OUT / (STEM + '.png')}")


if __name__ == "__main__":
    main()
