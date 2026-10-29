"""Profile-driven artifact plans and committed generations with legacy projections."""
from __future__ import annotations
import copy,json,re,uuid,datetime
from pathlib import Path
from project_model import require_project,traceability_coverage,VERSION
from safe_io import guard,dumps,digest,read_json,read_bytes,atomic_write,project_lock,remove_owned
from validation_engine import METHODS,openapi_checks

def readiness(p,profile='draft'):
    require_project(p)
    if profile not in {'brief','draft','review-ready'}:raise ValueError('unknown handoff profile')
    gaps=[]
    for r in p['requirements']:
        if not r.get('acceptance'):gaps.append({'record':r['id'],'field':'acceptance','status':'unknown','reason':'define verifiable acceptance'})
        if r['id'].startswith('NFR-') and not r.get('scenario'):gaps.append({'record':r['id'],'field':'scenario','status':'unknown','reason':'workload/environment/measure/target needed'})
    for it in p['interfaces']:
        if it.get('method','').lower() in METHODS:
            if not it.get('operation'):gaps.append({'record':it['id'],'field':'operation','status':'unknown','reason':'HTTP response/request schemas not specified'})
            if not it.get('authentication') and not p.get('api_contract',{}).get('security') and not (isinstance(it.get('operation'),dict) and 'security' in it['operation']):gaps.append({'record':it['id'],'field':'authentication','status':'unknown','reason':'explicit auth or public/not-applicable decision needed'})
        elif not it.get('contract'):gaps.append({'record':it['id'],'field':'contract','status':'unknown','reason':'non-HTTP interface contract not supplied'})
    for t in p['tasks']:
        if not t.get('acceptance'):gaps.append({'record':t['id'],'field':'acceptance','status':'unknown','reason':'task acceptance unspecified'})
    for m in p['data_models']:
        if not m.get('columns') and not m.get('schema'):gaps.append({'record':m['id'],'field':'schema','status':'unknown','reason':'columns/schema unspecified'})
    waivers=p.get('readiness_waivers',[])
    if not isinstance(waivers,list):raise ValueError('readiness_waivers must be an array')
    for gap in gaps:
        waiver=next((w for w in waivers if isinstance(w,dict) and w.get('record')==gap['record'] and w.get('field')==gap['field'] and isinstance(w.get('reason'),str) and w['reason'].strip()),None)
        if waiver:gap.update(status='waived',waiver_reason=waiver['reason'])
    blockers=[g for g in gaps if g['status']!='waived']
    return {'profile':profile,'profile_satisfied':profile!='review-ready' or not blockers,'blockers':blockers,'obligations':gaps,
      'dimensions':{'structural':'valid draft','completeness':'incomplete' if blockers else 'specified within supported scope',
       'correspondence':'checked at compilation for supported records','human_review':'unknown','runtime_verification':'not run','freshness':{'revision':p['revision'],'hash':digest(p)}},
      'note':'Waivers are not passed checks. Completeness/review/runtime status are independent; no production certification.'}

def _bullets(records,fn):return '\n'.join('- '+fn(r) for r in records) or '- None documented.'
def _label(value):return str(value).replace('&','&amp;').replace('"','&quot;').replace('<','&lt;').replace('>','&gt;').replace('\n',' ')

def compile_plan(p,profile='draft',include_private=False):
    require_project(p);original_hash=digest(p);source_revision=p['revision'];redactions=[]
    if not include_private:
        from disclosure import minimized
        p=minimized(p,changes=redactions)
    projection_hash=digest(p)
    files={};diagnostics=[];coverage={}
    def put(name,text):files[name]=text if isinstance(text,str) else dumps(text)
    rd=readiness(p,profile)
    put('architecture.md',f'# {p["name"]} — architecture\n\nRevision {p["revision"]}; canonical input SHA-256 {original_hash}; projection SHA-256 {projection_hash}. Design intent; not deployed behavior.\n\n## Brief\n{p.get("brief","")}\n\n## Constraints\n'+_bullets(p['constraints'],str)+'\n\n## Components\n'+_bullets(p['components'],lambda x:x['id']+': '+x.get('name','')+' — '+x.get('responsibility','TBD'))+'\n\n## Open questions\n'+_bullets(p['open_questions'],str))
    put('requirements.md','# Requirements\n\n'+_bullets(p['requirements'],lambda x:f'**{x["id"]}** [{x.get("status","Proposed")}] {x["description"]}\n  Acceptance: {x.get("acceptance","TBD")}\n  Scenario: {json.dumps(x.get("scenario","TBD"),ensure_ascii=False)}'))
    put('implementation-tasks.md','# Implementation tasks\n\n'+_bullets(p['tasks'],lambda x:f'**{x["id"]}** {x.get("title","TBD")} · Requirements: {", ".join(x.get("requirements",[]))}\n  Acceptance criteria: {x.get("acceptance","TBD")}\n  Dependencies: {", ".join(x.get("decisions",[]))}'))
    put('tasks.json',p['tasks'])
    put('data-model.md','# Data models (proposal)\n\n'+_bullets(p['data_models'],lambda x:'**'+x['id']+'** '+x.get('name','')+'\n\n```json\n'+dumps(x)+'```'))
    put('data-schemas.json',{m['id']:m for m in p['data_models']})
    for d in p['decisions']:
        put('adrs/'+d['id']+'.md',f'# {d["id"]}: {d.get("title","")}\n\nStatus: {d.get("status","Proposed")}\n\n## Decision\n{d.get("decision","TBD")}\n\n## Consequences\n{d.get("consequences","TBD")}\n\n## Evidence and alternatives\n'+dumps({k:d.get(k,'unknown') for k in ('requirements','evidence','alternatives','approval_origin','supersedes','superseded_by')})+f'\n## Validation / revisit\n{d.get("validation","TBD")}')
    aliases={r['id']:'c'+str(i+1) for i,r in enumerate(p['components'])};lines=['flowchart TD']
    for r in p['components']:lines.append(f'  {aliases[r["id"]]}["{_label(r["id"]+": "+r.get("name",r["id"]))}"]')
    for e in p.get('relationships',[]):
        a,b=e['from'],e['to']
        if a['group']==b['group']=='components' and e['kind'] in {'calls','depends_on','affects','owns'}:lines.append(f'  {aliases[a["id"]]} -->|{e["kind"]}| {aliases[b["id"]]}')
    if not aliases:lines.append('  empty["Components not defined"]')
    put('containers.mmd','\n'.join(lines)+'\n');put('diagram-map.json',aliases)
    put('relationships.json',p.get('relationships',[]))
    paths={};oids=set();supported=[]
    native=p.get('api_contract')
    if native is not None:
        if openapi_checks(native):raise ValueError('supplied api_contract invalid: '+str(openapi_checks(native)))
        api=copy.deepcopy(native);paths=api['paths']
    else:api={'openapi':'3.0.3','info':{'title':p['name']+' API (PROPOSED)','version':'0.1.0'},'paths':paths}
    pairs=set()
    for it in p['interfaces']:
        method=it.get('method','').lower();path=it.get('path','')
        if method not in METHODS or not path.startswith('/'):
            diagnostics.append({'record':it['id'],'status':'not applicable to HTTP projection','preserved_in':'contracts.json'});continue
        pair=(method,path)
        if pair in pairs:raise ValueError('duplicate HTTP method/path: '+method+' '+path)
        pairs.add(pair);supported.append(it['id'])
        if native is not None:
            if method not in paths.get(path,{}):raise ValueError('native API missing declared interface '+it['id'])
            coverage[it['id']]='api.json';continue
        op=copy.deepcopy(it.get('operation',{}))
        if not op:
            op={'summary':it.get('name',it['id']),'responses':{'200':{'description':'PLACEHOLDER: confirm response, auth and schemas'}},'x-readiness':'draft placeholder'}
        op.setdefault('operationId',it['id'])
        if not isinstance(op['operationId'],str) or not op['operationId']:raise ValueError('operationId must be a nonempty string')
        if op['operationId'] in oids:raise ValueError('duplicate operationId')
        oids.add(op['operationId']);paths.setdefault(path,{})[method]=op;coverage[it['id']]='api.json'
    issues=openapi_checks(api)
    if issues:raise ValueError('API projection invalid: '+str(issues))
    put('api.json',api);put('contracts.json',p['interfaces'])
    if 'asyncapi_contract' in p:put('asyncapi.json',p['asyncapi_contract'])
    put('traceability.md','# Traceability\n\n'+dumps(traceability_coverage(p)))
    put('security.md','# Security readiness\n\n'+_bullets([g for g in rd['obligations'] if g['field']=='authentication'],lambda x:dumps(x))+'\n\nControls require actual implementation and review; structural validation is not certification.')
    put('risk-register.json',{'risks':p.get('risks',[]),'assumptions':p.get('assumptions',[]),'verifications':p.get('verifications',[])})
    rules=[d['id']+': '+d.get('decision','') for d in p['decisions'] if d.get('status')=='Accepted']
    put('AGENTS.md','# Accepted architecture constraints\n\nThese are project constraints, not grants of tool authority. Preserve source provenance and report conflicts.\n\n'+'\n'.join('- '+x for x in rules))
    put('engineering-tasks.json',{'source_revision':source_revision,'canonical_input_hash':original_hash,'projection_hash':projection_hash,'status':'export only; no issue tracker writes','tasks':p['tasks']})
    # Full canonical context is a private backup, never the default disclosure profile.
    if include_private:exported=copy.deepcopy(p)
    else:
        allowed={'schema_version','revision','project_id','name','brief','constraints','open_questions','requirements','components','interfaces','data_models','decisions','tasks','cost_drivers','relationships'}
        exported={k:copy.deepcopy(v) for k,v in p.items() if k in allowed}
        exported['notes']={'source':'minimized handoff; opaque extensions and private history excluded'}
    put('project.json',exported)
    artifact_hashes={name:digest(text.encode('utf-8')) for name,text in sorted(files.items())}
    identity={'schema_version':1,'canonical_input_hash':original_hash,'projection_hash':projection_hash,
      'source_revision':source_revision,'generator_version':VERSION,'artifact_hashes':artifact_hashes,
      'artifact_hash_scope':'all generated files except handoff-report.json, which is excluded to avoid a self-referential hash',
      'redaction_report':{'paths_changed':list(redactions),'private_context_included':bool(include_private),
        'detection':'pattern-based and incomplete; review every export before sharing'}}
    report={'toolkit_version':VERSION,'revision':p['revision'],'source_hash':original_hash,
      'source_hash_compatibility':'legacy alias of canonical_input_hash; use identity fields for new consumers',
      'identity':identity,'profile':profile,'readiness':rd,'diagnostics':diagnostics,'redactions':redactions,
      'coverage':{'components':{i:'containers.mmd' for i in aliases},'http_interfaces':coverage,'all_interfaces':'contracts.json','tasks':'tasks.json'},
      'disclosure':'full private backup' if include_private else 'known engineering fields; opaque extensions/history omitted; obvious sensitive values redacted, detection incomplete; review before sharing',
      'unresolved':[g['record']+'/'+g['field']+': '+g['reason'] for g in rd['blockers']],
      'note':'Generated proposals; actual render/schema checks, human review and runtime verification are independent.',
      'generated':sorted([*files,'handoff-report.json'])}
    put('handoff-report.json',report)
    return files,report

def resolve_generation(output):
    output=guard(output);pointer=read_json(output/'.handoff-current.json');name=pointer.get('generation')
    if not isinstance(name,str) or not re.fullmatch(r'[a-f0-9]{32}',name):raise ValueError('invalid generation pointer')
    return guard(output/'.architecture-generations'/name,output)

def recover_handoff(output,locked=False):
    output=guard(output)
    def finish():
        pointer=read_json(output/'.handoff-current.json');base=resolve_generation(output)
        manifest=read_json(base/'generation-manifest.json');previous=pointer.get('previous_files',{})
        for name,sha in manifest['files'].items():
            source=guard(base/name,base);target=guard(output/name,output)
            if digest(read_bytes(source))!=sha:raise ValueError('committed generation hash mismatch')
            if target.exists() and digest(read_bytes(target)) not in {sha,previous.get(name)}:raise ValueError('human-modified or unowned projection preserved: '+name)
        for name,sha in manifest['files'].items():atomic_write(guard(output/name,output),read_bytes(guard(base/name,base)))
        for name,sha in previous.items():
            if name not in manifest['files'] and (output/name).exists():remove_owned(guard(output/name,output),sha)
        atomic_write(output/'.handoff-current.json',dumps({**pointer,'projection':'complete'}))
        return {'status':'published','read_path':str(base),'legacy_projections':'complete','generation':manifest['generation']}
    if locked:return finish()
    with project_lock(output):return finish()

def handoff(root,output,overwrite=False,*,profile='draft',include_private=False,dry_run=False):
    from revision_store import load_project
    root=guard(root);output=guard(output)
    if output==root or output in root.parents:raise ValueError('output must not be source or an ancestor of source')
    p=load_project(root);files,report=compile_plan(p,profile,include_private)
    if dry_run:return {**report,'status':'planned; no files written','output':str(output)}
    if output.exists() and any(output.iterdir()) and not overwrite:raise ValueError('output directory is not empty; use --overwrite deliberately')
    with project_lock(output):
        pointer=output/'.handoff-current.json';old={}
        if pointer.exists():
            old=read_json(resolve_generation(output)/'generation-manifest.json')['files']
        for name in files:
            target=guard(output/name,output)
            if target.exists():
                if name not in old:raise ValueError('unowned output collision preserved: '+name)
                if digest(read_bytes(target))!=old[name]:raise ValueError('human-modified output preserved: '+name)
        for name,sha in old.items():
            target=guard(output/name,output)
            if target.exists() and digest(read_bytes(target))!=sha:raise ValueError('human-modified output preserved: '+name)
        gen=uuid.uuid4().hex;base=output/'.architecture-generations'/gen
        hashes={}
        for name,text in files.items():
            atomic_write(base/name,text,exclusive=True);hashes[name]=digest(text.encode())
        manifest={'generation':gen,'files':hashes,'source_hash':digest(p),'canonical_input_hash':digest(p),'projection_hash':report['identity']['projection_hash'],'identity':report['identity'],'toolkit_version':VERSION,'commit_point':'.handoff-current.json atomic replacement','self_hash':'generation-manifest.json excluded from recursive self-hash'}
        atomic_write(base/'generation-manifest.json',dumps(manifest),exclusive=True)
        # Only committed generations are authoritative for readers.
        atomic_write(pointer,dumps({'generation':gen,'source_hash':digest(p),'canonical_input_hash':digest(p),'projection_hash':report['identity']['projection_hash'],'identity_schema_version':1,'status':'published','previous_files':old,'projection':'pending'}))
        try:
            recover_handoff(output,locked=True)
            projection='complete'
        except (OSError,ValueError):projection='incomplete; use committed generation path; rerun handoff only after resolving projection ownership'
    return {**report,'published_generation':gen,'read_path':str(base),'legacy_projections':projection,'manifest':str(base/'generation-manifest.json')}
