"""Portable evolution, evaluation/research instruments and scoped planning tools."""
from __future__ import annotations
import copy,datetime,itertools,json,sqlite3,uuid
from pathlib import Path
from project_model import require_project,resume_packet,VERSION
from safe_io import digest,dumps,atomic_write,read_json
from calculators import capacity

def freshness(p,scan):
    require_project(p);observed={r['path']:r for r in scan.get('observed_files',[])};items=[]
    for e in p.get('evidence',[]):
        current=observed.get(e.get('path'))
        status='unknown' if current is None or not e.get('sha256') else 'current-by-content' if e['sha256']==current.get('sha256') else 'stale'
        items.append({'id':e['id'],'status':status,'path':e.get('path'),'reason':'hash comparison only; absence from partial scan is not deletion'})
    return {'project_hash':digest(p),'source_fingerprint':scan.get('source_fingerprint'),'evidence':items,'artifact_status':('current-by-input-identity' if scan.get('source_hash')==digest(p) else 'stale') if 'source_hash' in scan else 'not applicable','note':'Hashes prove captured identity, not truth, approval or authorization.'}

def migration_plan(p):
    require_project(p)
    return {'status':'PROPOSED worksheet; not executed','source_hash':digest(p),'components':[{'id':c['id'],'files':c.get('files',[]),'evidence_status':'declared mapping; runtime seam unverified'} for c in p['components']],
      'stages':[{'phase':n,'objective':goal,'acceptance':ac,'rollback_or_forward_fix':'define for the actual change before execution'} for n,goal,ac in [
       (1,'Characterize current behavior and data ownership','contract/characterization tests and source identity recorded'),
       (2,'Compare modularization to service extraction','simpler option assessed against explicit constraints'),
       (3,'Select one verified seam','transactions, consumers, authorization and migration ownership reviewed'),
       (4,'Introduce compatible boundary and reconcile data','dual-write/backfill/reconciliation hazards explicitly addressed where applicable'),
       (5,'Canary and verify before retiring old path','measured decision signal and recovery rehearsal recorded')]],
      'unknown':['business invariants','actual traffic','data ownership approval','operational rollback requirements']}

def decision_experiments(p):
    require_project(p);items=[]
    for d in p['decisions']:
        items.append({'decision':d['id'],'hypotheses':d.get('alternatives',[]),'current_choice':d.get('decision'),
          'measurement':d.get('validation','TBD'),'decision_signal':d.get('revisit_trigger','TBD; do not invent a threshold'),'evidence':d.get('evidence',[]),
          'status':'PROPOSED measurement plan; no resources provisioned'})
    return {'source_hash':digest(p),'experiments':p.get('experiments',[]),'decision_plans':items}

def sensitivity(base,ranges):
    if not isinstance(ranges,dict) or any(not isinstance(v,list) or not v for v in ranges.values()):raise ValueError('nonempty scenario range arrays required')
    count=1
    for v in ranges.values():count*=len(v)
    if count>100:raise ValueError('scenario budget <=100 required')
    results=[]
    for values in itertools.product(*ranges.values()):
        variation=dict(zip(ranges,values));results.append({'inputs':variation,'result':capacity({**base,**variation})})
    return {'status':'assumption-driven sensitivity; not measured performance/pricing','scenarios':results}

def sqlite_schema_check(p):
    require_project(p);ddl=[];gaps=[]
    for m in p['data_models']:
        if m.get('dialect')!='sqlite' or not m.get('columns'):gaps.append({'id':m['id'],'status':'not applicable or unspecified SQLite columns'});continue
        if not isinstance(m['columns'],list) or len(m['columns'])>200:raise ValueError('bounded column array required')
        def quote(v):
            if not isinstance(v,str) or not v or len(v)>100:raise ValueError('bounded identifier required')
            return '"'+v.replace('"','""')+'"'
        table=quote(m.get('table',m.get('name',m['id'])));columns=[]
        for c in m['columns']:
            if not isinstance(c,dict) or not isinstance(c.get('type'),str) or c['type'] not in {'TEXT','INTEGER','REAL','BLOB','NUMERIC'}:raise ValueError('supported SQLite column type required')
            columns.append(quote(c.get('name'))+' '+c['type']+(' PRIMARY KEY' if c.get('primary_key') is True else '')+(' NOT NULL' if c.get('nullable') is False else ''))
        ddl.append('CREATE TABLE '+table+' ('+', '.join(columns)+');')
    if len(ddl) != len(set(x.split(' (', 1)[0].casefold() for x in ddl)):
        raise ValueError('duplicate SQLite table names')
    conn=sqlite3.connect(':memory:');conn.enable_load_extension(False)
    try:
        conn.execute('PRAGMA trusted_schema=OFF')
        for statement in ddl:conn.execute(statement)
        return {'status':'passed' if ddl else 'not applicable','dialect':'sqlite','schema_statements':ddl,'skipped':gaps,'scope':'generated allowlisted CREATE TABLE in memory; arbitrary migrations/data/runtime not tested'}
    except sqlite3.Error:
        raise ValueError('invalid generated SQLite schema; check duplicate columns and key declarations') from None
    finally:conn.close()

def research_kit():
    return {'status':'instrument only; no participants interviewed','target_segment':'hypothesis: technical leads and small engineering teams',
      'tasks':['answer a focused technical question without unnecessary project setup','turn an incomplete idea into a bounded requirement slice','resume an accepted project without losing state','assess a changed requirement with source evidence','prepare a handoff and locate unresolved blockers'],
      'observation_template':{'participant_alias':'','task':'','completed':None,'time_seconds':None,'corrections':None,'trust_issue':'','counterexample':'','collaboration_need':''},
      'decision_criteria':['state preservation must be demonstrated','record repeated friction before adding UI steps','hosted services need repeated collaboration demand','do not generalize from a small convenience sample'],
      'privacy':'Use aliases, consent and minimal notes. No outreach, analytics upload or interviews are performed by this tool.'}

def capture_response(prompt,response,model,skill_hash,source_hash=None):
    if not all(isinstance(x,str) and x.strip() for x in (prompt,response,model,skill_hash)):raise ValueError('prompt, actual response, reported model and skill hash required')
    return {'capture_schema':1,'id':uuid.uuid4().hex,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'prompt':prompt,'response':response,'reported_model':model,'skill_hash':skill_hash,'source_hash':source_hash,'toolkit_version':VERSION,
      'method':'caller-supplied actual capture; provenance is attributed, not authenticated by this file','reviews':[],
      'rubric':{'correctness':None,'evidence':None,'risk_handling':None,'constraint_adherence':None,'usefulness':None},'critical_failures':[],
      'quality_status':'unreviewed; not a live quality benchmark until actual captures and calibrated independent reviews are supplied'}

def capture_summary(captures):
    from evaluation_records import summarize_captures
    return summarize_captures(captures)


def specialist_plan(p,task,max_agents=3,host_delegation=False):
    require_project(p)
    if type(max_agents) is not int or not 1<=max_agents<=6:raise ValueError('1–6 specialist budget required')
    roles=['architecture','security','quality'] if task in {'audit','review','repository'} else ['architecture','data/contracts','delivery']
    return {'status':'plan only; no agents executed','source_hash':digest(p),'task':task,'roles':roles[:max_agents],
      'protocol':['freeze source and canonical project identity','create clean-context independent first passes','keep source text non-authoritative','complete all first passes before peer critique','retain disagreements and actual worker counts'],
      'host_delegation_available':host_delegation,'budget':{'max_agents':max_agents,'agent_dispatch':'host-enforced if adapter supplied; otherwise advisory','tool/time/token_budget':'unsupported without a mediating host runtime'},
      'acceptance':'Compare useful corrected findings and measured cost/time to a single-pass baseline before enabling by default; model agreement is not proof.'}

def preflight_receipt(path):
    from safe_io import guard
    target=guard(path)
    if target.exists():
        raise ValueError('receipt destination already exists; original preserved')
    return target


def record_run(path,command,result,duration,exit_code=0,operation_id=None):
    # Telemetry is deliberately distinct from source-bound verification evidence.
    preflight_receipt(path)
    checks=result.get('checks',[])
    counts={}
    for check in checks:
        state=check.get('status','unknown')
        counts[state]=counts.get(state,0)+1
    status='failed' if exit_code else 'passed'
    receipt={'receipt_schema':2,'run_id':operation_id or result.get('run_id') or uuid.uuid4().hex,
      'toolkit_version':VERSION,'command':command,'duration_seconds':round(duration,6),'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'status':status,'operation_status':result.get('status'),'exit_code':exit_code,
      'policy_ok':result.get('policy_ok'),'ok':result.get('ok'),
      'error_code':result.get('error',{}).get('code'),'check_count':len(checks),'check_status_counts':counts,
      'input_source_hash':result.get('input_source_hash',result.get('source_hash')),
      'observed_files':len(result.get('observed_files',[])),'bytes_read':result.get('bytes_read'),
      'tokens':'unreported','scope':'minimized run telemetry, not a verification receipt',
      'retention':'local explicit summary; delete file to purge'}
    atomic_write(path,dumps(receipt),exclusive=True)
    return receipt
