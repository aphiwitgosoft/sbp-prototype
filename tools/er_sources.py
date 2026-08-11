#!/usr/bin/env python3
"""อ่านโครงสร้างตารางจากแหล่งจริงของ repo แล้วคืนเป็น dict เดียวกันทุกแหล่ง

แหล่งที่อ่าน
  1. SBP/db-schema-sps_store.md · SBP/db-schema-sps_auth.md   (dump ฐานข้อมูลจริง 07/08/2026)
  2. LLDD/md/LLDD-Database.md หัวข้อ 5 (Executable DDL)        (โครง SBPGI 20 ตาราง)

ใช้โดย tools/build_er_diagram.py — ไม่แก้ไฟล์ต้นทาง อ่านอย่างเดียว
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    default: str = ""
    is_pk: bool = False
    is_fk: bool = False
    is_uk: bool = False
    note: str = ""


@dataclass
class Table:
    schema: str            # sbpgi | sps_store | sps_auth
    name: str
    columns: list[Column] = field(default_factory=list)
    pk: list[str] = field(default_factory=list)
    fks: list[tuple[str, str, str]] = field(default_factory=list)  # (col, target_table, target_col)
    uniques: list[list[str]] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    indexes: list[str] = field(default_factory=list)
    rows: int | None = None
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.schema}.{self.name}"

    def col(self, name: str) -> Column | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None


# ---------------------------------------------------------------- schema dump

_H3 = re.compile(r"^### (\S+)\s*$")
_ROWS = re.compile(r"ประมาณ ([\d,\-]+) แถว")
_USED = re.compile(r"^\*\*ใช้ใน SBPGI:\*\* (.+?)(?: · ประมาณ [\d,\-]+ แถว)?$")
_COL = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*(🔑)?\s*\|\s*([^|]+?)\s*\|\s*([YN])\s*\|\s*(.*?)\s*\|$"
)
_PK = re.compile(r"^- \*\*PK:\*\* (.+)$")
_FK = re.compile(r"^- \*\*FK:\*\* `([^`]+)` → `([^`]+)`\.`([^`]+)`$")
_IDX = re.compile(r"^- `([^`]+)` — `(.+)`$")


def parse_schema_dump(path: Path, schema: str) -> dict[str, Table]:
    """แยกตารางจากไฟล์ db-schema-*.md (หัวข้อ ### <table> + ตารางคอลัมน์ + PK/FK/Index)"""
    tables: dict[str, Table] = {}
    cur: Table | None = None
    in_body = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            in_body = line.startswith("## โครงสร้างรายตาราง") or line.startswith("## View")
            if not in_body:
                cur = None
            continue
        if not in_body:
            continue
        m = _H3.match(line)
        if m:
            cur = Table(schema=schema, name=m.group(1))
            tables[cur.name] = cur
            continue
        if cur is None:
            continue
        m = _USED.match(line)
        if m:
            cur.note = m.group(1).strip()
        m = _ROWS.search(line)
        if m and cur.rows is None:
            val = m.group(1).replace(",", "")
            cur.rows = int(val) if val.lstrip("-").isdigit() else None
        m = _COL.match(line)
        if m:
            cur.columns.append(
                Column(
                    name=m.group(2),
                    type=_short_type(m.group(4)),
                    nullable=m.group(5) == "Y",
                    default=m.group(6),
                    is_pk=bool(m.group(3)),
                )
            )
            continue
        m = _PK.match(line)
        if m:
            cur.pk = re.findall(r"`([^`]+)`", m.group(1))
            continue
        m = _FK.match(line)
        if m:
            cur.fks.append((m.group(1), m.group(2), m.group(3)))
            continue
        m = _IDX.match(line)
        if m:
            cur.indexes.append(f"{m.group(1)} — {m.group(2)}")

    for t in tables.values():
        pk = set(t.pk)
        fk = {c for c, _, _ in t.fks}
        for c in t.columns:
            c.is_pk = c.is_pk or c.name in pk
            c.is_fk = c.name in fk
    return tables


_TYPE_MAP = [
    (re.compile(r"^character varying\((\d+)\)$"), r"varchar(\1)"),
    (re.compile(r"^character varying$"), "varchar"),
    (re.compile(r"^character\((\d+)\)$"), r"char(\1)"),
    (re.compile(r"^timestamp without time zone$"), "timestamp"),
    (re.compile(r"^timestamp with time zone$"), "timestamptz"),
    (re.compile(r"^double precision$"), "float8"),
    (re.compile(r"^numeric\((\d+),(\d+)\)$"), r"numeric(\1,\2)"),
]


def _short_type(t: str) -> str:
    t = t.strip()
    for pat, rep in _TYPE_MAP:
        if pat.match(t):
            return pat.sub(rep, t)
    return t


# ------------------------------------------------------------------- ddl (sbpgi)

_CREATE = re.compile(r"CREATE TABLE (\w+)\s*\((.*?)\n\);", re.S)


def parse_sbpgi_ddl(path: Path) -> dict[str, Table]:
    """แยก CREATE TABLE ของโครง SBPGI จาก LLDD-Database.md หัวข้อ 5 (DDL ที่รันได้จริง)"""
    text = path.read_text(encoding="utf-8")
    body = text.split("## 5. Executable DDL", 1)[1].split("## 6. Index", 1)[0]
    tables: dict[str, Table] = {}

    for m in _CREATE.finditer(body):
        name, inner = m.group(1), m.group(2)
        t = Table(schema="sbpgi", name=name)
        for stmt in _split_ddl(inner):
            _apply_ddl_stmt(t, stmt)
        tables[name] = t

    # ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY
    for am in re.finditer(
        r"ALTER TABLE (\w+)\s+ADD CONSTRAINT \w+ FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)",
        body,
    ):
        t = tables.get(am.group(1))
        if t and not any(f[0] == am.group(2) for f in t.fks):
            t.fks.append((am.group(2), am.group(3), am.group(4)))

    for name, t in tables.items():
        for idx in re.finditer(rf"CREATE INDEX (\w+) ON {name}\(([^)]*)\)", body):
            t.indexes.append(f"{idx.group(1)} — ({idx.group(2)})")
        pk, fk = set(t.pk), {c for c, _, _ in t.fks}
        uk = {c for cols in t.uniques for c in cols}
        for c in t.columns:
            c.is_pk = c.is_pk or c.name in pk
            c.is_fk = c.name in fk
            c.is_uk = c.name in uk and not c.is_pk
    return tables


def _split_ddl(inner: str) -> list[str]:
    """ตัด comment แล้วแยกเป็นคำสั่งย่อยด้วย comma ระดับบนสุด (ไม่ตัดในวงเล็บ)"""
    lines = []
    for line in inner.splitlines():
        line = re.sub(r"--.*$", "", line).strip()
        if line:
            lines.append(line)
    flat = " ".join(lines)
    out, depth, buf = [], 0, []
    for ch in flat:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return out


def _apply_ddl_stmt(t: Table, stmt: str) -> None:
    up = stmt.upper()
    if up.startswith("CONSTRAINT"):
        if "UNIQUE" in up:
            cols = re.search(r"UNIQUE\s*\(([^)]*)\)", stmt, re.I)
            if cols:
                t.uniques.append([c.strip() for c in cols.group(1).split(",")])
        elif "CHECK" in up:
            t.checks.append(stmt.split("CHECK", 1)[1].strip())
        elif "PRIMARY KEY" in up:
            cols = re.search(r"PRIMARY KEY\s*\(([^)]*)\)", stmt, re.I)
            if cols:
                t.pk = [c.strip() for c in cols.group(1).split(",")]
        return
    if up.startswith("PRIMARY KEY"):
        cols = re.search(r"PRIMARY KEY\s*\(([^)]*)\)", stmt, re.I)
        if cols:
            t.pk = [c.strip() for c in cols.group(1).split(",")]
        return

    m = re.match(r"^(\w+)\s+(.+)$", stmt)
    if not m:
        return
    name, rest = m.group(1), m.group(2)
    tm = re.match(
        r"^(BIGSERIAL|SERIAL|BIGINT|INTEGER|SMALLINT|BOOLEAN|TEXT|DATE|JSONB|"
        r"TIMESTAMP|VARCHAR\(\d+\)|CHAR\(\d+\)|NUMERIC\(\d+,\d+\))",
        rest,
        re.I,
    )
    col = Column(name=name, type=(tm.group(1).lower() if tm else rest.split()[0].lower()))
    col.nullable = "NOT NULL" not in rest.upper()
    if re.search(r"\bPRIMARY KEY\b", rest, re.I):
        col.is_pk = True
        t.pk = t.pk or [name]
    if re.search(r"\bUNIQUE\b", rest, re.I):
        col.is_uk = True
        t.uniques.append([name])
    ref = re.search(r"REFERENCES\s+(\w+)\((\w+)\)", rest, re.I)
    if ref:
        t.fks.append((name, ref.group(1), ref.group(2)))
    ck = re.search(r"CHECK\s*(\(.*)$", rest, re.I)
    if ck:
        t.checks.append(f"{name} {ck.group(1)}")
    dv = re.search(r"DEFAULT\s+([^\s].*?)(?:\s+CHECK|\s+REFERENCES|$)", rest, re.I)
    if dv:
        col.default = dv.group(1).strip()
    t.columns.append(col)


def load_all() -> dict[str, dict[str, Table]]:
    return {
        "sbpgi": parse_sbpgi_ddl(ROOT / "LLDD/md/LLDD-Database.md"),
        "sps_store": parse_schema_dump(ROOT / "SBP/db-schema-sps_store.md", "sps_store"),
        "sps_auth": parse_schema_dump(ROOT / "SBP/db-schema-sps_auth.md", "sps_auth"),
    }


if __name__ == "__main__":
    all_t = load_all()
    for schema, tabs in all_t.items():
        cols = sum(len(t.columns) for t in tabs.values())
        fks = sum(len(t.fks) for t in tabs.values())
        print(f"{schema:10s} tables={len(tabs):4d} columns={cols:5d} fk={fks:3d}")
    sbpgi = all_t["sbpgi"]
    print("\nSBPGI tables:", ", ".join(sorted(sbpgi)))
    for n in ("compensation_documents", "interface_transactions"):
        t = sbpgi[n]
        print(f"\n{n}: pk={t.pk} cols={len(t.columns)} fks={t.fks} uniques={t.uniques}")
