# -*- coding: utf-8 -*-
"""สร้างชุดแผนภาพ Flow K2 (SVG + PNG + หน้ารวม HTML) → output/flow/

แหล่งความจริง: k2-flow.html · workflow.md · workflow_status_document.md
รันซ้ำได้ทุกครั้งที่ flow เปลี่ยน:  python3 tools/build_k2_flow_diagram.py
"""
from __future__ import annotations
import io, os, re, subprocess, shutil, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "flow")
FONT = "Tahoma,'Segoe UI','Noto Sans Thai',sans-serif"

# ── palette ────────────────────────────────────────────────────────────────
INK, MUTE, LINE = "#1f2937", "#64748b", "#cbd5e1"
BLUE, VIOLET, AMBER, GREEN, RED, ORANGE, INDIGO, SLATE = (
    "#2f6fed", "#7c3aed", "#f59e0b", "#16a34a", "#dc2626", "#ea580c", "#4f46e5", "#64748b")
TINT = {BLUE: "#eef4ff", VIOLET: "#f5f3ff", AMBER: "#fff8ea", GREEN: "#eafaf0",
        RED: "#fdecec", ORANGE: "#fff2e8", INDIGO: "#eef0ff", SLATE: "#f1f5f9"}

def esc(t): return H.escape(str(t), quote=False)

# ── primitives ─────────────────────────────────────────────────────────────
def defs():
    m = []
    for name, col in (("g", MUTE), ("v", VIOLET), ("a", AMBER), ("r", RED), ("b", BLUE), ("n", GREEN)):
        m.append(f'<marker id="ar{name}" markerWidth="10" markerHeight="10" refX="7.2" refY="3.2" '
                 f'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L7.2,3.2 L0,6.4 Z" fill="{col}"/></marker>')
    return ('<defs>' + "".join(m) +
            '<filter id="sh" x="-30%" y="-30%" width="160%" height="160%">'
            '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.10"/></filter>'
            '</defs>')

def txt(x, y, s, size=13, col=INK, anchor="middle", weight="400", ls=""):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
            f'fill="{col}" font-weight="{weight}"{ls}>{esc(s)}</text>')

def lines(cx, y0, rows, size=12.5, col=INK, weight="400", gap=16, anchor="middle"):
    return "".join(txt(cx, y0 + i * gap, r, size, col, anchor, weight) for i, r in enumerate(rows))

def box(cx, cy, w, h, col, title, subs=(), badge=None, rx=12, tint=None):
    x, y = cx - w / 2, cy - h / 2
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{tint or TINT[col]}" '
         f'stroke="{col}" stroke-width="1.7" filter="url(#sh)"/>')
    tx = cx + (16 if badge else 0)
    n = len(subs)
    top = cy - (n * 15) / 2 + 4
    s += txt(tx, top, title, 13.5, INK, "middle", "700")
    s += lines(tx, top + 17, subs, 11.2, MUTE, gap=14.5)
    if badge:
        bx = x + 26
        s += (f'<circle cx="{bx}" cy="{cy}" r="15" fill="{col}"/>' +
              txt(bx, cy + 4.5, badge, 11.5, "#fff", "middle", "700"))
    return s

def diamond(cx, cy, hw, hh, rows, col=AMBER):
    p = f"{cx},{cy-hh} {cx+hw},{cy} {cx},{cy+hh} {cx-hw},{cy}"
    s = f'<polygon points="{p}" fill="{TINT[col]}" stroke="{col}" stroke-width="1.7" filter="url(#sh)"/>'
    return s + lines(cx, cy - (len(rows) - 1) * 7 + 4, rows, 11.5, "#92400e", "700", gap=14)

def pill(cx, cy, w, h, col, rows, weight="700"):
    x, y = cx - w / 2, cy - h / 2
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{TINT[col]}" '
         f'stroke="{col}" stroke-width="1.7" filter="url(#sh)"/>')
    return s + lines(cx, cy - (len(rows) - 1) * 7 + 4, rows, 12.5, col, weight, gap=15)

def path(d, col=MUTE, marker="arg", dash=None, w=1.9):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}"{da}{mk}/>'

def tag(x, y, s, col=MUTE, anchor="start", size=11, bg=None):
    out = ""
    if bg:
        w = len(s) * 6.0 + 12
        bx = x - (w / 2 if anchor == "middle" else (w - 6 if anchor == "end" else 6))
        out += f'<rect x="{bx}" y="{y-11}" width="{w}" height="16" rx="8" fill="{bg}" opacity="0.95"/>'
    return out + txt(x, y, s, size, col, anchor, "600")

PAD_TOP = 34   # ระยะหายใจระหว่างแถบหัวสีดำกับพื้นที่กราฟ (ทุกแผนภาพใช้ค่าเดียวกัน)

def svg(w, h, body, title=None, sub=None):
    """title มี → เลื่อนเนื้อหาลง PAD_TOP แล้วขยายความสูงตาม ไม่ต้องแก้พิกัดในแต่ละแผนภาพ"""
    head, pad = "", 0
    if title:
        pad = PAD_TOP
        head = (f'<rect x="0" y="0" width="{w}" height="62" fill="#0f172a"/>' +
                txt(28, 33, title, 19, "#fff", "start", "700") +
                (txt(28, 52, sub, 11.8, "#94a3b8", "start") if sub else ""))
    H = h + pad
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" '
            f'font-family="{FONT}">' + defs() +
            f'<rect x="0" y="0" width="{w}" height="{H}" fill="#ffffff"/>' + head +
            f'<g transform="translate(0,{pad})">' + body + '</g></svg>')

def legend(x, y, items, cols=3, colw=430):
    out = ""
    for i, (kind, col, label) in enumerate(items):
        cx, cy = x + (i % cols) * colw, y + (i // cols) * 26
        if kind == "line":
            out += path(f"M{cx},{cy-4} L{cx+30},{cy-4}", col, None, "6 5" if "dash" in label else None)
        elif kind == "dash":
            out += path(f"M{cx},{cy-4} L{cx+30},{cy-4}", col, None, "6 5")
        elif kind == "dia":
            out += f'<polygon points="{cx+15},{cy-14} {cx+29},{cy-4} {cx+15},{cy+6} {cx+1},{cy-4}" fill="{TINT[col]}" stroke="{col}" stroke-width="1.5"/>'
        else:
            out += f'<rect x="{cx}" y="{cy-13}" width="30" height="18" rx="5" fill="{TINT[col]}" stroke="{col}" stroke-width="1.5"/>'
        out += txt(cx + 40, cy, label, 12, "#334155", "start")
    return out


# ═══════════════════════════ 1 · SWIMLANE หลัก ═══════════════════════════
def diagram_swimlane() -> str:
    W, H = 1960, 1360
    LX, CX0 = 0, 210                       # คอลัมน์ชื่อ lane
    LANES = [
        (80,  150, GREEN,  "ระบบ / Batch",              "Auto · ไม่มีคนกดปุ่ม"),
        (230, 200, BLUE,   "ฝ่าย SBP DSA",              "Manager Franchise · section 06"),
        (430, 150, BLUE,   "เจ้าหน้าที่ SBP DSA",        "Officer Franchise · section 08"),
        (580, 190, BLUE,   "หน่วยงานส่งเสริมธุรกิจฯ",     "Manager OPT + Senior · 01"),
        (770, 175, ORANGE, "GM ส่งเสริมธุรกิจฯ",         "GM OPT · section 02"),
        (945, 145, INDIGO, "ผู้บริหารสำนักบริหาร SBP",    "AVP OPT · 03 · ยอด ≥ 100,000"),
        (1090,155, SLATE,  "บัญชี",                      "นอก workflow · ไม่มีสถานะ"),
    ]
    b = ""
    for i, (y, h, col, name, sub) in enumerate(LANES):
        b += f'<rect x="{LX}" y="{y}" width="{W}" height="{h}" fill="{"#fbfdff" if i%2==0 else "#ffffff"}"/>'
        b += f'<line x1="{LX}" y1="{y}" x2="{W}" y2="{y}" stroke="{LINE}" stroke-width="1"/>'
        b += f'<rect x="{LX}" y="{y}" width="{CX0-20}" height="{h}" fill="{TINT[col]}"/>'
        b += f'<rect x="{LX}" y="{y}" width="5" height="{h}" fill="{col}"/>'
        b += txt(20, y + h/2 - 4, name, 13, INK, "start", "700")
        b += txt(20, y + h/2 + 13, sub, 10.3, MUTE, "start")
    b += f'<line x1="{LX}" y1="{LANES[-1][0]+LANES[-1][1]}" x2="{W}" y2="{LANES[-1][0]+LANES[-1][1]}" stroke="{LINE}"/>'
    b += f'<line x1="{CX0-20}" y1="80" x2="{CX0-20}" y2="{LANES[-1][0]+LANES[-1][1]}" stroke="{LINE}"/>'

    cy1, cy2, cy3, cy4, cy5, cy6, cy7 = 155, 330, 505, 675, 857, 1017, 1167

    # ── โหนด ──
    b += pill(330, cy1, 210, 56, GREEN, ["เริ่ม · เอกสารเข้าระบบ", "Batch 17:00 · หรือสร้างที่ FS"])
    b += box(620, cy1, 250, 60, VIOLET, "ประเภทเคส ?  (ระบบตัดสิน)",
             ["① เปิดเรื่องใหม่ · ② ต่อเนื่อง · ③ ยอด 0"], tint="#f5f3ff")
    b += box(600, cy2, 260, 92, BLUE, "ตรวจสอบเอกสาร & พิจารณา",
             ["ยอดขาย < 60 วัน = แถวแดง", "แนบไฟล์ ≤ 5 MB/ไฟล์"], badge="06")
    b += diamond(860, cy2, 95, 54, ["ผลพิจารณา", "ฝ่าย SBP DSA"])
    b += box(1140, cy3, 260, 82, BLUE, "คำนวณเงินชดเชย",
             ["ผ่านระบบ FS (Franchise Statement)"], badge="08")
    b += box(1140, cy4, 260, 96, BLUE, "กลั่นกรอง · แก้ไขข้อมูล",
             ["ร้านเปิดใหม่ / คู่แข่ง / ปัจจัย", "%ชดเชยรวมต้อง = 100%"], badge="01")
    b += diamond(1420, cy4, 96, 52, ["ผลพิจารณา", "หน่วยงานส่งเสริมฯ"])
    b += box(1420, cy5, 250, 84, ORANGE, "พิจารณา + ตรวจวงเงิน",
             ["เกณฑ์เดียว 100,000 บาท/รายการ"], badge="02")
    b += diamond(1665, cy5, 88, 50, ["ผลพิจารณา", "+ วงเงิน"])
    b += box(1665, cy6, 250, 76, INDIGO, "อนุมัติวงเงินสูง",
             ["เฉพาะเอกสารยอด ≥ 100,000"], badge="03")
    b += box(700, cy7, 640, 84, SLATE, "ตรวจสอบยอด + จัดเก็บสร้างรายการบันทึกบัญชี",
             ["รายงานตรวจสอบประกันรายได้ (SBP Mall) → ค้นหาข้อมูล → Export Excel",
              "→ กระทบยอด SAP (FBL3H / SAPPOST) เอง · ไม่มีขั้นอนุมัติของบัญชีใน workflow"])
    b += pill(1830, cy7, 210, 60, GREEN, ["จบ · เสร็จสิ้นดำเนินการ"])

    # ── เส้นเดินหน้า ──
    b += path(f"M435,{cy1} L493,{cy1}")                                     # start → gate
    b += path(f"M620,{cy1+30} L620,{cy2-46}", VIOLET, "arv")                # ① → 06
    b += tag(632, cy2-58, "① เปิดเรื่องใหม่ → เริ่มที่ 06", VIOLET)
    b += path(f"M745,{cy1} L1240,{cy1} L1240,{cy3-41}", VIOLET, "arv")      # ② → 08 (รางอยู่ขวาของข้อความเส้นข้ามขั้น)
    b += tag(760, cy1-14, "② ชดเชยต่อเนื่อง · ระบบ Auto Approve → เข้า 08 (ข้ามขั้น 06)", VIOLET)
    # ③ ≤3 เดือน → 01 — ต้องเข้าคนละจุดกับเส้น 08→01 (x=1140) ไม่งั้นหัวลูกศรถูกทับหาย
    b += path(f"M620,{cy1-30} L620,{cy1-56} L1560,{cy1-56} L1560,{cy4-88} "
              f"L1225,{cy4-88} L1225,{cy4-48}", VIOLET, "arv")
    b += tag(1237, cy4-58, "③ เข้าขั้น 01 อัตโนมัติ", VIOLET)
    b += tag(1085, cy1-64, "③ ยอดชดเชย 0 ติดกัน ≤ 3 เดือน → เข้าขั้น 01 อัตโนมัติ (ข้ามทั้ง 06 และ 08)",
             VIOLET, "middle", 11.5)   # baseline เหนือเส้นแนวนอนที่ cy1-56
    b += path(f"M730,{cy2} L765,{cy2}")                                     # 06 → decision
    # 06 → 08 เข้าขอบซ้ายเหนือกึ่งกลาง 18px — ต้องแยกระดับจากเส้น "08 ส่งกลับ → 06" ที่ออกขอบเดียวกัน
    b += path(f"M860,{cy2+54} L860,{cy3-18} L1010,{cy3-18}")
    # ป้ายนี้ต้องอยู่ "ซ้าย" ของเส้นเดินหน้า x=860 เพราะฝั่งขวามีรางข้ามขั้น x=1000 พาดผ่าน
    b += tag(848, cy2+92, "ส่งเจ้าหน้าที่ SBP DSA (ให้คำนวณยอด)", MUTE, "end")
    # ราง "ข้ามขั้น 08" — ต้องห่างขอบซ้ายกล่อง 08/01 (x=1010) พอให้หัวลูกศรกางเต็ม
    b += path(f"M955,{cy2} L975,{cy2} L975,{cy4} L1010,{cy4}", BLUE, "arb")   # 06 → 01 ข้ามขั้น
    b += tag(986, cy2-18, "ส่งหน่วยงานส่งเสริมธุรกิจ SBP", BLUE)
    b += tag(986, cy2-3, "(ข้ามขั้น 08 — ทราบยอดจาก 08 แล้ว)", BLUE)
    b += path(f"M1140,{cy3+41} L1140,{cy4-48}")                             # 08 → 01
    b += tag(1152, cy3+58, "คำนวณเงินชดเชยเรียบร้อย")
    b += path(f"M1270,{cy4} L1324,{cy4}")                                   # 01 → decision
    b += path(f"M1420,{cy4+52} L1420,{cy5-42}")                             # 01 → 02
    b += tag(1432, cy4+84, "เห็นควรชดเชย")
    b += path(f"M1545,{cy5} L1577,{cy5}")                                   # 02 → วงเงิน
    b += path(f"M1665,{cy5+50} L1665,{cy6-38}")                             # ≥100k → AVP
    b += tag(1677, cy5+82, "เห็นควรชดเชย · ≥ 100,000", INDIGO)

    # ── รางจบกระบวนการ (ขวาสุด) ──
    b += path(f"M860,{cy2-54} L860,{cy2-78} L1900,{cy2-78} L1900,{cy7-30}", RED, "arr", dash="7 5")
    b += tag(874, cy2-86, "เห็นควรไม่ชดเชย / หยุดชดเชยประกันรายได้ → จบทันที",
             RED, "start", 11.5)
    b += path(f"M1516,{cy4} L1900,{cy4}", RED, None, dash="7 5")
    b += tag(1600, cy4-12, "เห็นควรไม่ชดเชย → จบทันที (SDD GI)", RED)
    # ผลพิจารณาขั้น 02 แยกเป็น 2 เส้นคนละสี — เห็นควรไม่ชดเชย (แดงประ เข้ารางจบ) · < 100,000 (เขียวทึบ ลงกล่องจบเอง)
    b += path(f"M1728,{cy5-14} L1900,{cy5-14}", RED, None, dash="7 5")
    b += tag(1836, cy5-26, "เห็นควรไม่ชดเชย → จบ", RED, "end", 11)
    b += path(f"M1728,{cy5+14} L1840,{cy5+14} L1840,{cy7-30}", GREEN, "arn")
    b += tag(1836, cy5+30, "< 100,000 → จบที่ GM", GREEN, "end", 11)
    b += path(f"M1780,{cy6+38} L1780,{cy7-30}", GREEN, "arn")
    b += tag(1768, cy6+64, "AVP เห็นควรชดเชย → จบ", GREEN, "end")
    b += path(f"M1725,{cy7} L1330,{cy7}", SLATE, "arg", dash="5 4")
    b += tag(1528, cy7-12, "เอกสารเสร็จสิ้น → ทีมบัญชีดึงข้อมูลผ่านรายงาน", SLATE, "middle")

    # ── เส้นส่งกลับ (รางซ้าย) ──
    RL = 320
    # รางรวมกลับ 06 (ซ้ายสุด) — วิ่งขึ้นจากจุดต่ำสุดของรางเข้ากล่อง 06
    b += path(f"M{RL},{cy4+32} L{RL},{cy2} L470,{cy2}", AMBER, "ara", dash="7 5")
    # 08 ส่งกลับ — ออกขอบซ้ายใต้กึ่งกลาง 18px (คนละระดับกับเส้นเดินหน้า 06 → 08 ที่เข้าขอบเดียวกัน)
    b += path(f"M1010,{cy3+18} L{RL},{cy3+18}", AMBER, None, dash="7 5")
    b += tag(RL+14, cy3+8, "08 ส่งกลับ → 06", "#b45309")
    b += path(f"M1010,{cy4+32} L{RL},{cy4+32}", AMBER, None, dash="7 5")
    b += tag(RL+14, cy4+22, "01 ส่งกลับ → 06", "#b45309")
    # เข้าขอบล่างของกล่อง 01 (รางแนวตั้งต้องอยู่นอกกล่อง ไม่งั้นเส้นทะลุกลางกล่อง)
    b += path(f"M1295,{cy5} L1060,{cy5} L1060,{cy4+48}", AMBER, "ara", dash="7 5")
    b += tag(1072, cy5-10, "02 ส่งกลับ → 01", "#b45309")
    # เข้าขอบล่างของกล่อง 02 พอดี (cy5+42) — เดิมจบที่ cy5+46 ซึ่งเลยขอบกล่องไป 4px หัวลูกศรจึงลอยนอกกล่อง
    b += path(f"M1540,{cy6} L1420,{cy6} L1420,{cy5+42}", AMBER, "ara", dash="7 5")
    b += tag(1432, cy6-10, "AVP ส่งกลับ → 02", "#b45309")
    b += path(f"M1540,{cy6+26} L1370,{cy6+26} L1370,{cy6+56} L{RL},{cy6+56} L{RL},{cy4+32}",
              AMBER, None, dash="7 5")
    b += tag(1000, cy6+48, "AVP เห็นควรไม่ชดเชย → กลับ 06", "#b45309", "middle")

    # ── หมายเหตุ + legend ──
    b += f'<rect x="{CX0}" y="1225" width="1180" height="86" rx="10" fill="#faf8ff" stroke="#ddd3fb"/>'
    b += txt(CX0+18, 1250, "กติกาที่ผูกกับปุ่มของขั้น 06 (SDD สไลด์ 46 · 48)", 12.5, "#5b21b6", "start", "700")
    b += txt(CX0+18, 1270, "• หยุดชดเชยประกันรายได้ → เอกสารจบ แต่ กลับมาแสดงในหน้ารอดำเนินการของ 06 ทันทีในเดือนนั้น เพื่อเปิดพิจารณาใหม่ได้เอง (ไม่ต้องเปิด SR)", 11.5, "#4c3a86", "start")
    b += txt(CX0+18, 1288, "• เห็นควรไม่ชดเชยรายได้ → เอกสารจบและ ไม่แสดง ในเดือนนั้น แล้วเดือนถัดไประบบดึงร้านเข้ามาใหม่อัตโนมัติ พร้อมเจ้าของงานคนเดิม", 11.5, "#4c3a86", "start")
    b += txt(CX0+18, 1306, "• เคสต่อเนื่อง → ระบบส่งงานให้เจ้าหน้าที่ SBP DSA คนเดิมอัตโนมัติ · resolve จาก consideration_logs ของรอบก่อน แล้วผูกด้วย addPreApprover()", 11.5, "#4c3a86", "start")
    b += legend(1430, 1252, [
        ("box", BLUE, "ขั้นตอนที่คนดำเนินการ"), ("dia", AMBER, "จุดตัดสินใจ"),
        ("box", VIOLET, "ระบบทำอัตโนมัติ"), ("line", MUTE, "เดินหน้า"),
        ("dash", AMBER, "ส่งกลับ"), ("dash", RED, "จบกระบวนการ"),
    ], cols=2, colw=250)
    return svg(W, H, b, "Flow K2 — Workflow อนุมัติประกันรายได้ (SBPGI)",
               "5 ขั้น 06→08→01→02→03 · 6 สถานะ · 3 จุดเข้าตามประเภทเคส · เกณฑ์วงเงินเดียว 100,000 (มติ 2026-08-18)")


# ═══════════════════════════ 2 · จุดเข้า flow ตามประเภทเคส ═══════════════════════════
def diagram_gate() -> str:
    W, H = 1760, 890
    b = ""
    b += pill(170, 200, 210, 62, GREEN, ["เริ่ม · เอกสารเข้าระบบ"])
    b += diamond(450, 200, 132, 66, ["ประเภทเคส ?", "จากข้อมูลรอบชดเชยของร้าน"], VIOLET)
    b += path("M282,200 L312,200")
    b += path("M582,200 L620,200", MUTE, None)          # stub กลาง (สีเดียว)

    rows = [
        (VIOLET, 112, "② ชดเชยต่อเนื่อง",
         "last_compensate_seq_no > 1   AND   flag_action = 'Y'",
         "จาก fgi_impact_processes (hub รอบชดเชยของร้าน · โซน A)",
         "ระบบ Auto Approve การเปิดเรื่อง — ข้ามขั้น 06",
         "08", "เจ้าหน้าที่ SBP DSA", "รอเจ้าหน้าที่ SBP DSA ดำเนินการ", BLUE, "arv"),
        (MUTE, 285, "① เปิดเรื่องใหม่",
         "last_compensate_seq_no = 1   (รอบใหม่ · last_compensate_seq +1)",
         "จาก fgi_impact_processes (hub รอบชดเชยของร้าน · โซน A)",
         "— ไม่มี auto · เดินตาม flow เดิม",
         "06", "ฝ่าย SBP DSA", "รอฝ่าย SBP DSA ดำเนินการ", BLUE, "arg"),
        (VIOLET, 452, "③ ยอด 0 · ≤ 3 เดือน",
         "COALESCE(adjust_amount, forecast_amount) = 0   งวดที่ 1–3",
         "จาก fgi_impact_compensations (ยอดชดเชยรายงวด · โซน A)",
         "Auto ส่งต่อ — ข้ามทั้งขั้น 06 และ 08",
         "01", "หน่วยงานส่งเสริมธุรกิจฯ", "รอหน่วยงานส่งเสริมธุรกิจ SBP", BLUE, "arv"),
        (RED, 608, "③ ยอด 0 · เดือนที่ 4",
         "COALESCE(adjust_amount, forecast_amount) = 0   งวดที่ 4 ขึ้นไป",
         "จาก fgi_impact_compensations (ยอดชดเชยรายงวด · โซน A)",
         "Auto หยุดชดเชยประกันรายได้ — ปิดเอกสารทันที",
         "—", "จบทันที", "เสร็จสิ้นดำเนินการ (หยุดชดเชยฯ)", RED, "arr"),
    ]
    for col, y, name, cond, srctbl, act, code, actor, status, tcol, mk in rows:
        b += path(f"M620,200 L620,{y} L740,{y}", col, mk)
        b += tag(632, y - 14, name, col)
        b += box(1060, y, 600, 92, col, cond, [srctbl, act], rx=10, tint="#ffffff")
        b += path(f"M1360,{y} L1400,{y}", col, mk)
        if code == "—":
            b += pill(1570, y, 300, 66, RED, ["จบทันที · ไม่เข้า flow พิจารณา", status])
        else:
            b += box(1570, y, 300, 74, tcol, actor, [status], badge=code, rx=10)

    # ── ที่มาของข้อมูลที่ใช้ตัดสิน (ระบบเดิม Oracle → ตารางของ SBPGI) ─────────────────────
    ty = 678
    b += f'<rect x="60" y="{ty}" width="1640" height="196" rx="12" fill="#faf8ff" stroke="#ddd3fb"/>'
    b += txt(80, ty + 26, "ที่มาของข้อมูลที่ใช้ตัดสินจุดเข้า — ทุกค่ามาจากโซน A (FGI/FCS) ที่ batch เขียนไว้ก่อนเปิดเอกสาร", 13.5, "#4c3a86", "start", "700")
    cols = [(80, "ค่าที่ใช้ในเงื่อนไข"), (390, "ระบบเดิม (Oracle FCS_FRN)"), (940, "ตาราง SBPGI"), (1270, "คอลัมน์ · ชนิด"), (1560, "เขียนโดย")]
    for cx, ch in cols:
        b += txt(cx, ty + 52, ch, 11.5, "#7b6aa8", "start", "700")
    b += f'<line x1="76" y1="{ty + 60}" x2="1684" y2="{ty + 60}" stroke="#ddd3fb"/>'
    src = [
        ("LAST_COMPENSATE_SEQ_NO", "FGI_IMPACT_STORE_ON_PROCESS .LAST_COMPENSATE_SEQ_NO", "fgi_impact_processes", "last_compensate_seq_no · INTEGER", "Job 2 (ImportJdbc)"),
        ("FLAG_ACTION", "FGI_IMPACT_STORE_ON_PROCESS .FLAG_ACTION  (Y/W/N)", "fgi_impact_processes", "flag_action · CHAR(1)", "Job 2 · ปิดรอบโดย Job 6"),
        ("forecast", "FGI_IMPACT_STORE_COMPENSATE .COMPENSATE_FORECAST", "fgi_impact_compensations", "forecast_amount · NUMERIC(14,2)", "Job 5 (IAS/MIS)"),
        ("adjust", "FGI_IMPACT_STORE_COMPENSATE .COMPENSATE_ADJUST", "fgi_impact_compensations", "adjust_amount · NUMERIC(14,2)", "จนท. SBP DSA คีย์"),
    ]
    for k, (val, ora, tbl, col, who) in enumerate(src):
        ry = ty + 82 + k * 26
        b += txt(80, ry, val, 12, "#1f2937", "start", "700")
        b += txt(390, ry, ora, 11.5, "#64748b", "start")
        b += txt(940, ry, tbl, 11.5, VIOLET, "start", "600")
        b += txt(1270, ry, col, 11.5, "#1f2937", "start")
        b += txt(1560, ry, who, 11.5, "#64748b", "start")
    b += txt(80, ty + 186, "ยอดที่ใช้จริง = COALESCE(adjust_amount, forecast_amount)  ·  ทุกเส้นทางอัตโนมัติต้องบันทึกลง consideration_logs ด้วยผู้ดำเนินการ SYSTEM เพื่อไม่ให้ timeline ขาดช่วง  ·  ⚠ ทั้ง 2 ตารางเป็น gap F8/F1 ที่เพิ่งรับเข้าโครง — ต้อง migrate ก่อนจึง implement ได้จริง",
              11.5, "#4c3a86", "start")
    return svg(W, H, b, "จุดเข้า flow ตามประเภทเคส (To-Be)",
               "ผัง To-Be 12/02/2026 · เอกสารไม่ได้เริ่มที่ขั้น 06 เสมอไป — มีเพียงเคส ① เท่านั้นที่เริ่มที่ 06")


# ═══════════════════════════ 3 · วงจรเปิดเรื่องซ้ำ + เจ้าของงาน ═══════════════════════════
def diagram_reopen() -> str:
    W, H = 1420, 690
    b = ""
    b += box(300, 165, 300, 86, BLUE, "ฝ่าย SBP DSA พิจารณา",
             ["เอกสารเดือนปัจจุบัน"], badge="06")
    b += diamond(660, 165, 120, 62, ["กดปุ่มไหน ?"])
    b += path("M450,165 L540,165")

    # หยุดชดเชย → กลับเข้าคิว 06 ทันที
    b += path("M660,103 L660,70 L1010,70 L1010,110", RED, "arr")
    b += tag(835, 60, "หยุดชดเชยประกันรายได้", RED, "middle")
    b += box(1120, 150, 480, 80, RED, "เอกสารจบ (เสร็จสิ้นดำเนินการ)",
             ["แต่ กลับมาแสดงในหน้ารอดำเนินการของ 06 ทันทีในเดือนนั้น",
              "ชิป ↺ หยุดชดเชยฯ · เห็นเฉพาะบทบาท 06 · เปิดพิจารณาใหม่ได้เอง (ไม่ต้องเปิด SR)"], rx=10)
    b += path("M1120,190 L1120,255 L300,255 L300,208", RED, "arr", dash="7 5")
    b += tag(860, 246, "กลับเข้าคิวของ 06 ทันที — เดือนเดียวกัน", RED, "middle", 11.5)

    # เห็นควรไม่ชดเชย → เดือนถัดไป
    b += path("M660,227 L660,330 L880,330", "#b45309", "ara")
    b += tag(672, 320, "เห็นควรไม่ชดเชยรายได้", "#b45309")
    b += box(1120, 330, 480, 80, AMBER, "เอกสารจบ (เสร็จสิ้นดำเนินการ)",
             ["ไม่แสดง ในหน้ารอดำเนินการของ 06 ในเดือนนั้น",
              "เดือนถัดไป ระบบดึงร้านเข้ามาใหม่อัตโนมัติ พร้อมเจ้าของงานคนเดิม"], rx=10)
    b += path("M1120,370 L1120,438 L300,438 L300,470", AMBER, "ara", dash="7 5")
    b += tag(710, 429, "เข้าคิวรอบเดือนถัดไป", "#b45309", "middle", 11.5, "#ffffff")
    b += box(300, 512, 300, 84, BLUE, "งานรอบเดือนถัดไป",
             ["ร้านเดิม · เจ้าของงานคนเดิม"], badge="06")

    # กล่องอธิบายวิธี resolve
    b += box(940, 545, 840, 150, VIOLET, "วิธี resolve “เจ้าของงานคนเดิม” (ไม่มีคอลัมน์ assignee ในตารางของ SBPGI)",
             ["1 · หาเอกสารรอบก่อนหน้าของร้านเดียวกัน (impacted_store_code เดิม · round_no/loop_no ก่อนหน้า)",
              "2 · อ่าน consideration_logs แถวล่าสุดที่ section_code = ขั้นที่จะมอบหมาย  →  consider_by",
              "3 · ผูกด้วย addPreApprover(versionId, referenceId, stateId, approver, seq) ของ @srm/glb-workflow",
              "4 · Fallback: รอบก่อนไม่เคยผ่านขั้นนั้น / พนักงานลาออก → มอบหมายตาม group ของ auth-backend",
              "5 · พนักงานลาออกยังต้องเปิด SR เพื่อแก้ชื่อผู้ดำเนินการ (SDD สไลด์ 48)"], rx=12)
    b += path("M450,512 L520,512", VIOLET, "arv")
    return svg(W, H, b, "หยุดชดเชย vs เห็นควรไม่ชดเชย — พฤติกรรมหน้ารายการต่างกันคนละแบบ",
               "SDD สไลด์ 46 ข้อ 1.9 · สไลด์ 48 · 64 — สองปุ่มนี้จบเอกสารเหมือนกัน แต่การแสดงผลตรงข้ามกัน")


# ═══════════════════════════ 4 · สถานะเอกสาร 6 ค่า ═══════════════════════════
def diagram_states() -> str:
    W, H = 1840, 470
    b = ""
    ST = [(170, "06", "รอฝ่าย SBP DSA", BLUE), (455, "08", "รอเจ้าหน้าที่ SBP DSA", BLUE),
          (740, "01", "รอหน่วยงานส่งเสริมธุรกิจ SBP", BLUE), (1025, "02", "รอ GM ส่งเสริมธุรกิจ SBP", ORANGE),
          (1310, "03", "รอผู้บริหารสำนักบริหาร SBP", INDIGO)]
    for x, code, name, col in ST:
        b += box(x, 190, 250, 82, col, name, ["ดำเนินการ"], badge=code, rx=10)
    b += pill(1660, 190, 230, 66, GREEN, ["เสร็จสิ้นดำเนินการ", "(End)"])
    for k in range(len(ST) - 1):
        b += path(f"M{ST[k][0]+125},190 L{ST[k+1][0]-125},190")
    b += path("M1435,190 L1545,190")
    for a, bb in ((455, 170), (740, 170), (1025, 740), (1310, 1025)):
        b += path(f"M{a},231 L{a},278 L{bb},278 L{bb},231", AMBER, "ara", dash="6 5")
    b += tag(330, 296, "08 / 01 ส่งกลับ → 06", "#b45309", "middle")
    b += tag(884, 296, "02 ส่งกลับ → 01", "#b45309", "middle")
    b += tag(1168, 296, "AVP ส่งกลับ → 02", "#b45309", "middle")
    for x in (170, 740, 1025):
        b += path(f"M{x},149 L{x},108 L1660,108 L1660,157", RED, "arr", dash="7 5")
    b += tag(900, 100, "เห็นควรไม่ชดเชย (06 · 01 · 02) และ หยุดชดเชยประกันรายได้ (06) → เสร็จสิ้นทันที  ·  02 ยอด < 100,000 อนุมัติแล้วจบที่ GM",
             RED, "middle", 11.5, "#ffffff")
    b += f'<rect x="60" y="340" width="1720" height="106" rx="10" fill="#f8fafc" stroke="{LINE}"/>'
    b += txt(78, 366, "อีเมลแจ้งเตือน และข้อควรระวัง", 12.5, INK, "start", "700")
    b += txt(78, 388, "• เปลี่ยนสถานะ → SBPGI เรียก sendEmail() ของ email-lib เอง โดยใช้เลข template จาก sps_store.workflow_route.email_id (ปิด DP-5 · ไม่มีตาราง status_email_rules)", 11.5, "#475569", "start")
    b += txt(78, 408, "• เตือนงานค้างทุกวันจันทร์ 10:00 น. · escalation เมื่อค้างครบ 30 / 45 / 60 วัน → หัวหน้า Section (เลข template เก็บที่ mas_param)", 11.5, "#475569", "start")
    b += txt(78, 428, "• สถานะเอกสารมี 6 ค่าเท่านั้น — “หยุดชดเชยประกันรายได้” เป็น ผลการพิจารณา ไม่ใช่สถานะที่ 7 (คัดจาก consideration_logs · FE แสดงเป็นชิป ↺ หยุดชดเชยฯ)", 11.5, "#475569", "start")
    return svg(W, H, b, "สถานะเอกสาร 6 ค่า และเส้นทางเปลี่ยนสถานะ",
               "ตัดสถานะบัญชี 04 / 05 ตาม SDD v7.5 · inbox ของแต่ละบทบาท = สถานะ “รอ<บทบาทตัวเอง>ดำเนินการ” ค่าเดียว")


# ═══════════════════════════ main ═══════════════════════════
DIAGRAMS = [
    ("01-swimlane",  1960, 1330, "Swimlane หลัก — Workflow 5 ขั้น",
     "ภาพรวมทั้งกระบวนการ: จุดเข้าตามประเภทเคส → 06 → 08 → 01 → 02 → 03 → จบ · เส้นส่งกลับ · ปลายทางบัญชี/SAP"),
    ("02-entry-gate", 1760, 700, "จุดเข้า flow ตามประเภทเคส",
     "เอกสารเริ่มที่ขั้นไหน ขึ้นกับว่าเป็นเคสเปิดเรื่องใหม่ / ต่อเนื่อง / ยอดชดเชยเป็น 0"),
    ("03-reopen",     1420, 690, "หยุดชดเชย vs เห็นควรไม่ชดเชย",
     "สองปุ่มที่จบเอกสารเหมือนกันแต่พฤติกรรมหน้ารายการตรงข้ามกัน + วิธี resolve เจ้าของงานคนเดิม"),
    ("04-states",     1840, 470, "สถานะเอกสาร 6 ค่า",
     "State machine ของเอกสาร + จุดส่งอีเมลแจ้งเตือน"),
]

def build():
    os.makedirs(OUT, exist_ok=True)
    gen = {"01-swimlane": diagram_swimlane, "02-entry-gate": diagram_gate,
           "03-reopen": diagram_reopen, "04-states": diagram_states}
    chrome = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    made = []
    size = {}
    for key, w, h, title, sub in DIAGRAMS:
        sp = os.path.join(OUT, key + ".svg")
        content = gen[key]()
        io.open(sp, "w", encoding="utf-8").write(content)
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', content)
        w, h = int(vb.group(1)), int(vb.group(2))
        size[key] = (w, h)
        made.append(key)
        if os.path.exists(chrome):
            subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={os.path.join(OUT, key + '.png')}",
                            f"--window-size={w},{h}", "--default-background-color=ffffff",
                            "file://" + sp], capture_output=True)
    # หน้ารวม
    cards = ""
    for key, _w, _h, title, sub in DIAGRAMS:
        w, h = size[key]
        cards += f'''  <section class="fig" id="{key}">
    <div class="fig-h"><h2>{esc(title)}</h2>
      <div class="dl"><a href="{key}.svg" download>SVG</a><a href="{key}.png" download>PNG</a></div></div>
    <p class="sub">{esc(sub)}</p>
    <div class="scroll"><img src="{key}.png" alt="{esc(title)}" width="{w}" height="{h}"></div>
  </section>
'''
    page = f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Flow K2 — ชุดแผนภาพ</title>
<style>
 *{{box-sizing:border-box}} body{{margin:0;background:#f1f5f9;color:#1f2937;font-family:{FONT}}}
 header{{background:#0f172a;color:#fff;padding:28px 40px}}
 header h1{{margin:0;font-size:24px}} header p{{margin:8px 0 0;color:#94a3b8;font-size:13.5px;line-height:1.8}}
 nav{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 40px;position:sticky;top:0;z-index:10;
      display:flex;gap:10px;flex-wrap:wrap}}
 nav a{{font-size:13px;text-decoration:none;color:#334155;background:#f1f5f9;border:1px solid #e2e8f0;
        padding:7px 14px;border-radius:999px}}
 nav a:hover{{background:#e0e7ff;border-color:#c7d2fe;color:#3730a3}}
 main{{padding:26px 40px 60px;max-width:2100px;margin:0 auto}}
 .fig{{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;margin-bottom:26px;
       box-shadow:0 1px 3px rgba(15,23,42,.06)}}
 .fig-h{{display:flex;align-items:center;gap:16px}} .fig-h h2{{margin:0;font-size:18px}}
 .dl{{margin-left:auto;display:flex;gap:8px}}
 .dl a{{font-size:12px;text-decoration:none;color:#2f6fed;border:1px solid #bfdbfe;background:#eff6ff;
        padding:5px 12px;border-radius:8px;font-weight:600}}
 .sub{{margin:8px 0 16px;color:#64748b;font-size:13px;line-height:1.7}}
 .scroll{{overflow-x:auto;border:1px solid #eef2f7;border-radius:10px;background:#fff}}
 .scroll img{{display:block;max-width:none;height:auto}}
 footer{{padding:0 40px 50px;color:#64748b;font-size:12.5px;line-height:1.9;max-width:2100px;margin:0 auto}}
 code{{background:#f1f5f9;padding:1px 6px;border-radius:5px;font-size:12px}}
</style></head><body>
<header>
  <h1>Flow K2 — ชุดแผนภาพ Workflow อนุมัติประกันรายได้ (SBPGI)</h1>
  <p>สร้างจาก <code>k2-flow.html</code> · <code>workflow.md</code> · <code>workflow_status_document.md</code> —
     แยกเป็น 4 แผนภาพตามประเด็น เพื่อให้อ่านง่ายกว่ารวมไว้รูปเดียว<br>
     regenerate: <code>python3 tools/build_k2_flow_diagram.py</code> · ห้ามแก้ไฟล์ใน <code>output/</code> ด้วยมือ</p>
</header>
<nav>{"".join(f'<a href="#{k}">{esc(t)}</a>' for k, _, _, t, _ in DIAGRAMS)}</nav>
<main>
{cards}</main>
<footer>
  <b>กติกาที่แผนภาพชุดนี้สะท้อน</b> — workflow 5 ขั้น <code>06 → 08 → 01 → 02 → 03</code> · สถานะเอกสาร 6 ค่า (ตัดขั้นบัญชี 04/05 ตาม SDD v7.5) ·
  วงเงินเกณฑ์เดียว <b>100,000</b> บาท/รายการ (มติประชุม 2026-08-18 — &lt; 100,000 จบที่ GM · ≥ 100,000 ส่ง AVP) ·
  เห็นควรไม่ชดเชยที่ขั้น 01/02 จบทันที · 3 จุดเข้าตามประเภทเคส (ผัง To-Be 12/02/2026) ·
  auto-assign เจ้าของงานคนเดิม (SDD สไลด์ 46 · 48)
</footer></body></html>'''
    io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    inject_into_k2_flow(gen)
    return made


# ═══════════════════════ ฝังแผนภาพชุดนี้ลง k2-flow.html ═══════════════════════
K2_FLOW = os.path.join(ROOT, "k2-flow.html")
BEGIN, END = "<!-- BEGIN generated-flow-diagrams -->", "<!-- END generated-flow-diagrams -->"


def _namespace_ids(svg_text: str, prefix: str) -> str:
    """4 แผนภาพอยู่หน้าเดียวกัน — marker/filter ใช้ id ชุดเดียวกันทุกไฟล์ ถ้าไม่เติม prefix
       ตัวหลังจะทับตัวแรก (หัวลูกศร/เงาเพี้ยนทั้งหน้า) จึงเปลี่ยนทั้งจุดประกาศและจุดอ้าง url(#..)"""
    ids = set(re.findall(r'<(?:marker|filter)\s+id="([\w-]+)"', svg_text))
    for i in sorted(ids, key=len, reverse=True):
        svg_text = svg_text.replace(f'id="{i}"', f'id="{prefix}-{i}"')
        svg_text = svg_text.replace(f'url(#{i})', f'url(#{prefix}-{i})')
    return svg_text


def inject_into_k2_flow(gen) -> bool:
    """เขียนทับบล็อกระหว่าง marker ใน k2-flow.html ด้วยแผนภาพชุดเดียวกับ output/flow
       (หน้า prototype จึงไม่ต้องพึ่งไฟล์ใน output/ และไม่มีวันหลุด sync กับสคริปต์)"""
    if not os.path.exists(K2_FLOW):
        return False
    page = io.open(K2_FLOW, encoding="utf-8").read()
    if BEGIN not in page or END not in page:
        return False
    cards = []
    for key, _w, _h, title, sub in DIAGRAMS:
        raw = gen[key]()
        # ตัดแถบหัวสีดำ + PAD_TOP ออก — หน้า prototype มีหัวการ์ดของตัวเองอยู่แล้ว
        body = raw.split(f'<g transform="translate(0,{PAD_TOP})">', 1)[1].rsplit("</g></svg>", 1)[0]
        defs_block = raw.split("<defs>", 1)[1].split("</defs>", 1)[0]
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', raw)
        w, h = int(vb.group(1)), int(vb.group(2)) - PAD_TOP
        inner = (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{esc(title)}" '
                 f'style="min-width:{min(w, 1100)}px;display:block;font-family:{FONT}">'
                 f'<defs>{defs_block}</defs>{body}</svg>')
        cards.append(
            f'      <div class="card">\n'
            f'        <div class="card-head"><h2>{esc(title)}</h2>'
            f'<span class="pill violet" style="margin-left:auto;">สร้างอัตโนมัติ</span></div>\n'
            f'        <p style="font-size:13px;color:#45525f;line-height:1.9;margin:0 0 12px;">{esc(sub)}</p>\n'
            f'        <div style="overflow-x:auto;">'
            + _namespace_ids(inner, key) +
            f'</div>\n      </div>\n')
    block = (BEGIN + "\n"
             + "      <!-- ที่มา: tools/build_k2_flow_diagram.py · ไฟล์ดาวน์โหลด SVG/PNG อยู่ที่ output/flow/ -->\n"
             + "".join(cards) + "      " + END)
    head = page.split(BEGIN, 1)[0]
    tail = page.split(END, 1)[1]
    io.open(K2_FLOW, "w", encoding="utf-8").write(head + block + tail)
    print("  ✅ ฝัง 4 แผนภาพลง k2-flow.html")
    return True

if __name__ == "__main__":
    for k in build():
        print("  ✅", k + ".svg / .png")
    print("  ✅ index.html →", os.path.relpath(OUT, ROOT))
