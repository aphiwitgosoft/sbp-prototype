"""Isolated SQL audit; never connects to project databases or rewrites delivered SQL."""
import ast
import concurrent.futures
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import build_sgi_schema_sql as gen
import build_sgi_existing_stub_sql as stubgen
import check_sgi_sql_columns as checker

SQL = ROOT / 'output/sql'
NAME = 'sgi-audit-20260916-' + uuid.uuid4().hex[:8]
RESULTS = {}

def record(key, value):
    RESULTS[key] = value
    print(key + ': ' + json.dumps(value, ensure_ascii=False), flush=True)

def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, **kwargs)

def sql(source, db='sgi', check=True):
    r = run(['docker', 'exec', '-i', NAME, 'psql', '-X', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', db, '-qAt'], input=source)
    if check and r.returncode:
        raise RuntimeError(r.stderr)
    return r

def query(q, db='sgi'):
    return sql('SET search_path TO sps_store;\n' + q, db).stdout.strip()

def counts(db='sgi'):
    return query("SELECT json_build_object('types',(SELECT count(*) FROM common_code_type),'codes',(SELECT count(*) FROM common_code),'params',(SELECT count(*) FROM mas_param),'templates',(SELECT count(*) FROM email_template),'competitors',(SELECT count(*) FROM sgi_competitors),'factors',(SELECT count(*) FROM sgi_external_factors),'running',(SELECT count(*) FROM sgi_document_running_numbers));", db)

def seed_twice(db):
    source = (SQL / 'sgi_seed_data.sql').read_text()
    # Hold the first seed lock until the second seed has reached its lock request.
    held = source.replace('SELECT pg_advisory_xact_lock(861000, 1);', 'SELECT pg_advisory_xact_lock(861000, 1); SELECT pg_sleep(2);')
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        first = pool.submit(sql, held, db)
        time.sleep(.3)
        second = pool.submit(sql, source, db)
        first.result(); second.result()
    return counts(db)

def lookup_sql():
    html = (ROOT / 'plan-api.html').read_text()
    body = html[html.index('var SQL_BY_PATH = {'):html.index('var FLOWCHART_BY_PATH = {')]
    return {m[1]: ast.literal_eval(m[2]) for m in re.finditer(r"'([^'\n]+)':\s*('(?:\\.|[^'\\])*')", body)}

def main():
    record('sql_sha256', {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in SQL.glob('*.sql')})
    with tempfile.TemporaryDirectory(prefix='sgi-generator-audit-') as d:
        gen.OUT_DIR = Path(d)
        gen.build(); gen.build_seed()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            stubgen.main()
        record('generator_equal', {**{f.name: f.read_bytes() == (SQL / f.name).read_bytes() for f in Path(d).glob('*.sql')}, 'sgi_existing_stub.sql': out.getvalue() == (SQL / 'sgi_existing_stub.sql').read_text()})
    record('container', NAME)
    r = run(['docker','run','-d','--name',NAME,'--network','none','-e','POSTGRES_PASSWORD=isolated-audit-only','-e','POSTGRES_DB=sgi','postgres:16-alpine'])
    if r.returncode:
        raise RuntimeError(r.stderr)
    try:
        for _ in range(40):
            if run(['docker','exec',NAME,'pg_isready','-U','postgres']).returncode == 0:
                break
            time.sleep(.5)
        record('postgres', query('SHOW server_version;'))
        for f in ('sgi_existing_stub.sql','sgi_schema.sql','sgi_seed_data.sql'):
            sql((SQL / f).read_text())
        record('fresh_counts', counts())
        sql((SQL / 'sgi_seed_data.sql').read_text())
        record('sequential_counts', counts())
        record('catalog', query("SELECT json_build_object('tables',(SELECT count(*) FROM pg_tables WHERE schemaname='sps_store' AND tablename LIKE 'sgi\_%'),'secondary_indexes',(SELECT count(*) FROM pg_indexes WHERE schemaname='sps_store' AND tablename LIKE 'sgi\_%' AND indexname LIKE 'idx\_%'),'fks',(SELECT count(*) FROM pg_constraint WHERE contype='f' AND conrelid IN (SELECT oid FROM pg_class WHERE relnamespace='sps_store'::regnamespace AND relname LIKE 'sgi\_%')));"))
        record('fk_without_leading_index', query("SELECT c.conrelid::regclass || ':' || a.attname FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1] WHERE c.contype='f' AND c.conrelid::regclass::text LIKE '%sgi_%' AND NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid=c.conrelid AND i.indisvalid AND i.indpred IS NULL AND i.indkey[0]=c.conkey[1]) ORDER BY 1;"))
        dump = stubgen.DUMP.read_text()
        null_drift, default_drift = [], []
        for table in stubgen.TABLES:
            section = re.search(r'^### '+table+r'\n(.*?)(?=^### |\Z)',dump,re.S|re.M)[1]
            for name, nullable, default in re.findall(r'^\| \d+ \| `([^`]+)`[^|]*\| [^|]+ \| ([YN]) \|([^|]*)\|',section,re.M):
                actual = query(f"SELECT is_nullable || '|' || coalesce(column_default,'') || '|' || is_identity FROM information_schema.columns WHERE table_schema='sps_store' AND table_name='{table}' AND column_name='{name}';")
                parts=actual.split('|')
                if nullable=='N' and parts[0]!='NO': null_drift.append(table+'.'+name)
                if default.strip() and 'nextval' not in default and not parts[1]: default_drift.append(table+'.'+name)
        record('stub_missing_not_null',null_drift)
        record('stub_missing_defaults',default_drift)
        api = lookup_sql()
        for key, source in api.items():
            if '/lookup/' in key:
                record(key, query(source))
        sections = api['GET /api/v1/sgi/lookup/workflow-sections']
        for case, mutation in {
            'missing': "DELETE FROM common_code WHERE code_type='SGI_APPROVE_LIMIT';",
            'inactive': "UPDATE common_code SET active_flag='N' WHERE code_type='SGI_APPROVE_LIMIT';",
            'invalid': "UPDATE common_code SET code_name='invalid' WHERE code_type='SGI_APPROVE_LIMIT';",
            'duplicate': "INSERT INTO common_code SELECT * FROM common_code WHERE code_type='SGI_APPROVE_LIMIT';",
        }.items():
            r=sql('BEGIN; SET search_path TO sps_store; '+mutation+'\n'+sections+'\nROLLBACK;',check=False)
            record('lookup_'+case,{'returncode':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()})
        for case, mutation in {
            'duplicate_param': "INSERT INTO sps_store.mas_param SELECT * FROM sps_store.mas_param WHERE param_name='SGI_ZERO_AMOUNT_MAX_MONTHS';",
            'invalid_threshold': "UPDATE sps_store.common_code SET code_name='invalid' WHERE code_type='SGI_APPROVE_LIMIT';",
            'inactive_type': "UPDATE sps_store.common_code_type SET active_flag='N' WHERE code_type='SGI_DOC_STATUS';",
            'foreign_owner': "UPDATE sps_store.common_code SET create_user='OTHER-TEAM' WHERE code_type='SGI_APPROVE_LIMIT';",
        }.items():
            source=(SQL/'sgi_seed_data.sql').read_text().replace('BEGIN;', 'BEGIN;\n'+mutation,1).replace('COMMIT;','ROLLBACK;')
            r=sql(source,check=False)
            record('seed_accepts_'+case,{'returncode':r.returncode,'notices':r.stderr.strip()})
        sql('CREATE DATABASE concurrent;')
        for f in ('sgi_existing_stub.sql','sgi_schema.sql'):
            sql((SQL/f).read_text(),'concurrent')
        record('concurrent_fresh',seed_twice('concurrent'))
        sql("DELETE FROM sps_store.common_code; DELETE FROM sps_store.email_template;",'concurrent')
        record('concurrent_partial',seed_twice('concurrent'))
        record('empty_email_bodies',query("SELECT count(*) FROM email_template WHERE active_flag='Y' AND coalesce(body_format,'')='';"))
        rows=checker.collect(); passed=[]; failures=[]; skipped=[]
        for row in rows:
            if row['kind']!='pg':
                skipped.append({'file':row['file'],'reason':row['kind']});continue
            r=sql('PREPARE q AS '+row['sql']+';',check=False)
            if r.returncode:
                failures.append({'file':row['file'],'error':r.stderr.strip(),'sql':row['sql']})
            else: passed.append(row['file'])
        record('batch_prepare',{'total':len(rows),'passed':len(passed),'skipped':skipped,'failed':failures})
        # Create only the extra legacy relation shapes referenced in API SQL, from the dump.
        refs=set(re.findall(r'\b(?:FROM|JOIN|INTO|UPDATE)\s+(?:sps_store\.)?(\w+)', '\n'.join(api.values()),re.I))
        for table in refs:
            if table in stubgen.TABLES or table.startswith('sgi_'): continue
            m=re.search(r'^### '+re.escape(table)+r'\n(.*?)(?=^### |\Z)',dump,re.S|re.M)
            if not m:continue
            cols=re.findall(r'^\| \d+ \| `([^`]+)`[^|]*\| ([^|]+) \| [YN] \|',m[1],re.M)
            if cols: sql('CREATE TABLE sps_store.'+table+'('+','.join(n+' '+stubgen.pg_type(t) for n,t in cols)+');')
        api_bad=[]; api_ok=0
        for key,source in api.items():
            for statement in gen.split_statements(source):
                q=gen.strip_comments(statement)
                if not q:continue
                # Untyped named binds become positional binds, consistently within each statement.
                binds={}
                def bind(m):
                    return '$'+str(binds.setdefault(m[1],len(binds)+1))
                q=re.sub(r'(?<!:):([A-Za-z]\w*)',bind,q)
                r=sql('SET search_path TO sps_store; PREPARE q AS '+q+';',check=False)
                if r.returncode: api_bad.append({'endpoint':key,'sql':q,'error':r.stderr.strip()})
                else:api_ok+=1
        record('api_prepare',{'endpoints':len(api),'statements_passed':api_ok,'failed':api_bad})
        # A read-only view owned by another module illustrates CASCADE's actual reach.
        sql('CREATE SCHEMA audit_other; CREATE VIEW audit_other.dependent AS SELECT competitor_code FROM sps_store.sgi_competitors;')
        r=sql((SQL/'sgi_schema_rollback.sql').read_text())
        sql((SQL/'sgi_schema_rollback.sql').read_text())
        record('rollback',{'sgi_objects':query("SELECT count(*) FROM pg_class WHERE relnamespace='sps_store'::regnamespace AND relname LIKE 'sgi\_%';"),'dependent_view_exists':query("SELECT to_regclass('audit_other.dependent');"),'shared_counts':query("SELECT (SELECT count(*) FROM common_code_type)||'/'||(SELECT count(*) FROM common_code)||'/'||(SELECT count(*) FROM mas_param)||'/'||(SELECT count(*) FROM email_template);"),'notices':r.stderr.strip()})
        sql((SQL/'sgi_schema.sql').read_text());sql((SQL/'sgi_seed_data.sql').read_text())
        record('reinstall',counts())
    finally:
        r=run(['docker','rm','-f',NAME])
        record('container_removed',r.returncode==0)

if __name__=='__main__':
    try: main()
    finally:
        (ROOT/'tmp/sql-audit-20260916-results.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
