import json
import re
import time
import audit_sql_recheck_20260916 as a

r=a.run(['docker','run','-d','--name',a.NAME,'--network','none','-e','POSTGRES_PASSWORD=isolated-audit-only','-e','POSTGRES_DB=sgi','postgres:16-alpine'])
if r.returncode: raise RuntimeError(r.stderr)
try:
    for _ in range(40):
        if a.run(['docker','exec',a.NAME,'pg_isready','-U','postgres']).returncode==0: break
        time.sleep(.5)
    for f in ('sgi_existing_stub.sql','sgi_schema.sql','sgi_seed_data.sql'):
        a.sql((a.SQL/f).read_text())
    wrong=[]
    for row in a.checker.collect():
        if row['kind']=='mssql' and row['file'].split('-')[1] not in ('2','3'):
            r=a.sql('PREPARE q AS '+row['sql']+';',check=False)
            wrong.append({'file':row['file'],'returncode':r.returncode,'error':r.stderr.strip()})
    a.record('misclassified_pg_queries',wrong)
    dump=a.stubgen.DUMP.read_text()
    strict=[]
    for table in a.stubgen.TABLES:
        section=re.search(r'^### '+table+r'\n(.*?)(?=^### |\Z)',dump,re.S|re.M)[1]
        for name,nullable,default in re.findall(r'^\| \d+ \| `([^`]+)`[^|]*\| [^|]+ \| ([YN]) \|([^|]*)\|',section,re.M):
            if nullable=='N': strict.append(f'ALTER TABLE sps_store.{table} ALTER COLUMN {name} SET NOT NULL;')
            if default.strip() and 'nextval' not in default:
                strict.append(f'ALTER TABLE sps_store.{table} ALTER COLUMN {name} SET DEFAULT {default.strip()};')
    a.sql('\n'.join(strict))
    a.sql((a.SQL/'sgi_seed_data.sql').read_text())
    a.record('seed_on_stricter_dump_columns','PASS: dump NOT NULL and non-sequence defaults applied, seed rerun succeeded')
    a.record('null_type_name_rejected',a.sql("INSERT INTO sps_store.common_code_type(code_type,code_type_name,active_flag) VALUES ('AUDIT_BAD',NULL,'Y');",check=False).stderr.strip())
    a.record('repeat_schema',a.sql((a.SQL/'sgi_schema.sql').read_text(),check=False).stderr.strip())
    a.record('pending_false_truth_table',a.query("SELECT pending, outbox_status FROM (VALUES (false),(true)) p(pending) CROSS JOIN (VALUES ('CONFIRMED'),('PUBLISHED')) s(outbox_status) WHERE (pending IS NULL OR outbox_status IS DISTINCT FROM 'CONFIRMED');"))
    # Reconstruct dump-derived tables for typed PREPARE of failed reference snippets.
    api=a.lookup_sql()
    for table in ('store','workflow_approver'):
        section=re.search(r'^### '+table+r'\n(.*?)(?=^### |\Z)',dump,re.S|re.M)[1]
        cols=re.findall(r'^\| \d+ \| `([^`]+)`[^|]*\| ([^|]+) \| [YN] \|',section,re.M)
        a.sql('CREATE TABLE sps_store.'+table+'('+','.join(n+' '+a.stubgen.pg_type(t) for n,t in cols)+');')
    typed={
      'GET /api/v1/sgi/master/competitors': ['text','boolean'],
      'GET /api/v1/sgi/master/factors': ['text','boolean'],
      'GET /api/v1/sgi/workflow/summary': ['text'],
      'GET /api/v1/sgi/interface/tracking': ['text','boolean','text','timestamp','timestamp','integer','integer'],
      'GET /api/v1/sgi/interface/pending-ack': ['numeric','text'],
      'GET /api/v1/sgi/report/status-summary': ['integer','text','text','text','date','date','text[]','text[]','text','integer','integer'],
    }
    result=[]
    for key,types in typed.items():
        binds={}
        q=a.gen.strip_comments(api[key]).rstrip(';')
        q=re.sub(r'(?<!:):([A-Za-z]\w*)',lambda m:'$'+str(binds.setdefault(m[1],len(binds)+1)),q)
        r=a.sql('SET search_path TO sps_store; PREPARE q('+','.join(types)+') AS '+q+';',check=False)
        result.append({'endpoint':key,'binds':binds,'returncode':r.returncode,'error':r.stderr.strip()})
    a.record('typed_api_prepare',result)
finally:
    a.record('container_removed',a.run(['docker','rm','-f',a.NAME]).returncode==0)
    (a.ROOT/'tmp/sql-audit-followup-20260916-results.json').write_text(json.dumps(a.RESULTS,ensure_ascii=False,indent=2))
