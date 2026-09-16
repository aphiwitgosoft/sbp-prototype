#!/usr/bin/env python3
"""ตรวจว่า **SQL ทุกคำสั่งของ batch job SGI** อ้างตาราง/คอลัมน์ที่มีอยู่จริง

    python3 tools/check_sgi_sql_columns.py            # ยกฐานเอง ตรวจ แล้วลบ container
    python3 tools/check_sgi_sql_columns.py --keep     # ไม่ลบ container (ไว้ไล่ดูต่อ)

วิธีทำงาน — ให้ **PostgreSQL เป็นคนตรวจ** ไม่ใช่ regex
──────────────────────────────────────────────────────
1. สร้างฐานชั่วคราว + ตารางระบบเดิมจาก dump จริง (`tools/build_sgi_existing_stub_sql.py`)
   และตารางใหม่จาก `output/sql/sgi_schema.sql`
2. ดึง template literal ที่เป็น SQL ออกจาก `src/modules/sgi/*.ts` ทุกไฟล์
3. `PREPARE` ทีละคำสั่ง — PostgreSQL จะ parse + resolve ชื่อคอลัมน์ + อนุมานชนิด parameter
   โดย **ไม่รันจริง** · ชื่อผิด/ชนิดขัดกันจะโผล่ทันที

ทำไมถึงต้องมี
─────────────
รอบ 2026-09-14 เครื่องมือนี้จับได้ 6 จุดที่เทสอื่นทั้งหมดมองไม่เห็น เพราะ stub ที่เขียนมือ
"มีคอลัมน์ที่โค้ดเรียกหา" เสมอ:
  - `dv_code` ไม่มีใน `mas_store` และ `business_user` (ชื่อจริงคือ `zone_cd`) — Job 8, 12
  - `branch_id` ไม่มีใน `fr_store` (ชื่อจริงคือ `store_id`) — Job 6
  - `juristic_id` ไม่มีใน `mas_store` (นิติบุคคลผูกกับสัญญาใน `fr_store`) — Job 8b
  - `user_id` ของ `business_user` เป็น bigint เทียบกับ varchar ตรง ๆ ไม่ได้ — Job 8b
  - `$1` ถูกอนุมานเป็นสองชนิดในคำสั่งเดียว — Job 6 mutation ⑤

คำสั่งที่ข้าม (นับแยก ไม่ใช่ error)
───────────────────────────────────
  - คิวรี ALLMAP ของ Job 2/3 — รันบน **SQL Server** ไม่ใช่ PostgreSQL
  - ข้อความร้อยแก้วในคอมเมนต์ที่บังเอิญมีคำว่า SELECT/UPDATE
  - คำสั่งที่ประกอบ fragment แบบ dynamic (`${whereSql}`) จนเหลือไม่ครบประโยค
"""
import argparse, collections, io, os, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SGI = ROOT / 'SBP' / 'srm-sps-spsap-sop-sgi-batch' / 'src' / 'modules' / 'sgi'
CONTAINER = os.environ.get('SGI_SQLCHECK_CONTAINER', 'sgi-sqlcheck')
PORT = os.environ.get('SGI_SQLCHECK_PORT', '55502')

# คิวรีที่รันบน SQL Server (ALLMAP) — PostgreSQL parse ไม่ได้โดยธรรมชาติ
MSSQL_HINT = re.compile(r'\b(STORECODE_I|BRANDCODE|NEWSTORECODE|WITH\s*\(NOLOCK\)|TOP\s+\(?\d)', re.I)


def literals(text: str):
    out, i = [], 0
    while True:
        i = text.find('`', i)
        if i < 0:
            break
        j, depth = i + 1, 0
        while j < len(text):
            c = text[j]
            if c == '\\':
                j += 2
                continue
            if c == '`' and depth == 0:
                break
            if text.startswith('${', j):
                depth += 1
                j += 2
                continue
            if c == '}' and depth > 0:
                depth -= 1
            j += 1
        body, i = text[i + 1:j], j + 1
        # ต้องมีทั้งกริยาและเป้าหมาย — กันคำในคอมเมนต์อย่าง `SELECT distinct *` ที่อยู่ใน backtick
        if (re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|WITH)\b', body, re.I)
                and re.search(r'\b(FROM|INTO|UPDATE\s+\S|SET)\b', body, re.I)):
            out.append(body)
    return out


def fill_values(sql: str) -> str:
    """VALUES ${tuples.join(',')} → tuple ของ NULL ตามจำนวนคอลัมน์ที่ INSERT ระบุ"""
    m = re.search(r'INSERT\s+INTO\s+[\w.${}]+\s*\(([^)]*)\)', sql, re.I | re.S)
    if not m:
        return sql
    n = len([c for c in m.group(1).split(',') if c.strip()])
    return re.sub(r'(VALUES\s*)\$\{[^}]*\}', r'\1(' + ','.join(['NULL'] * n) + ')', sql, flags=re.I)


def collect():
    rows = []
    for f in sorted(SGI.glob('*.ts')):
        if f.name.endswith('.spec.ts'):
            continue
        text = io.open(f, encoding='utf-8').read()
        for lit in literals(text):
            sql = lit.replace('${this.schema}', 'sps_store')
            sql = fill_values(sql)
            sql = re.sub(r'\$\{[^}]*\}', ' ', sql)
            sql = re.sub(r'^\s*--.*$', '', sql, flags=re.M).strip().rstrip(';')
            if not re.match(r'^(SELECT|INSERT|UPDATE|DELETE|WITH)\b', sql, re.I):
                continue
            kind = 'mssql' if MSSQL_HINT.search(sql) else ('prose' if '...' in sql else 'pg')
            rows.append({'file': f.name, 'sql': sql, 'kind': kind})
    return rows


def psql(sql: str):
    return subprocess.run(['docker', 'exec', '-i', CONTAINER, 'psql', '-U', 'postgres', '-d', 'sgi', '-q'],
                          input=sql, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true', help='ไม่ลบ container หลังตรวจเสร็จ')
    args = ap.parse_args()

    schema_sql = ROOT / 'output' / 'sql' / 'sgi_schema.sql'
    stub_sql = ROOT / 'output' / 'sql' / 'sgi_existing_stub.sql'
    if not schema_sql.exists():
        print('ไม่พบ output/sql/sgi_schema.sql — รัน tools/build_sgi_schema_sql.py ก่อน', file=sys.stderr)
        return 1
    subprocess.run(['python3', str(ROOT / 'tools' / 'build_sgi_existing_stub_sql.py')],
                   stdout=io.open(stub_sql, 'w'), check=True)

    subprocess.run(['docker', 'rm', '-f', CONTAINER], capture_output=True)
    subprocess.run(['docker', 'run', '-d', '--name', CONTAINER, '-e', 'POSTGRES_PASSWORD=TestOnly123',
                    '-e', 'POSTGRES_DB=sgi', '-p', f'{PORT}:5432', 'postgres:16-alpine'],
                   capture_output=True, check=True)
    for _ in range(60):
        if subprocess.run(['docker', 'exec', CONTAINER, 'pg_isready', '-U', 'postgres'],
                          capture_output=True).returncode == 0:
            break
        time.sleep(1)
    else:
        print('ฐานไม่พร้อมใน 60 วินาที', file=sys.stderr)
        return 1
    try:
        for f in (stub_sql, schema_sql):
            r = psql(io.open(f, encoding='utf-8').read())
            # ⚠️ ต้องดัก connection error ด้วย — ไม่มีคำว่า ERROR แต่แปลว่าไม่ได้ติดตั้งอะไรเลย
            if 'ERROR' in r.stderr or 'could not connect' in r.stderr:
                print(f'ติดตั้ง {f.name} ไม่สำเร็จ:\n{r.stderr}', file=sys.stderr)
                return 1

        rows = collect()
        bad = collections.defaultdict(list)
        skipped = collections.Counter()
        for r in rows:
            if r['kind'] != 'pg':
                skipped[r['kind']] += 1
                continue
            q = psql('PREPARE q AS\n' + r['sql'] + ';')
            if 'ERROR' in q.stderr:
                first = next(l for l in q.stderr.split('\n') if 'ERROR' in l).strip()
                # fragment ที่ถูกตัดจน parse ไม่ได้ — ไม่ใช่ข้อผิดพลาดของโค้ด
                if 'syntax error' in first or 'relation "eval"' in first:
                    skipped['dynamic'] += 1
                    continue
                bad[r['file']].append(first)

        checked = len(rows) - sum(skipped.values())
        print(f'SQL ทั้งหมด {len(rows)} คำสั่ง · ตรวจจริง {checked} · '
              f'ข้าม {sum(skipped.values())} (SQL Server {skipped["mssql"]} · '
              f'ร้อยแก้ว {skipped["prose"]} · fragment {skipped["dynamic"]})')
        if bad:
            print('\n❌ พบปัญหา:')
            for f in sorted(bad):
                for e in bad[f]:
                    print(f'  {f}: {e}')
            return 1
        print('✅ ทุกคำสั่งอ้างตาราง/คอลัมน์ที่มีอยู่จริง และชนิด parameter ไม่ขัดกัน')
        return 0
    finally:
        if not args.keep:
            subprocess.run(['docker', 'rm', '-f', CONTAINER], capture_output=True)


if __name__ == '__main__':
    raise SystemExit(main())
