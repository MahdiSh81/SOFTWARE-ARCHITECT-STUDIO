"""Canonical v2 draft contract. Unknown fields are preserved, never executed."""
from __future__ import annotations
import copy, math, re, uuid
from safe_io import digest, dumps

VERSION='0.7.1'
GROUPS=('requirements','components','interfaces','data_models','decisions','tasks','cost_drivers')
OPTIONAL=('evidence','assumptions','risks','verifications','fitness_rules','experiments')
ID=re.compile(r'^[A-Za-z][A-Za-z0-9_-]{1,63}$')
STATES={'Proposed','Accepted','Superseded','Rejected','Withdrawn','Draft','Implemented'}
KINDS={'owns','calls','reads','writes','publishes','consumes','implements','verifies','depends_on','affects'}
LINKS={
 'components':('requirements',),'interfaces':('requirements','components'),
 'data_models':('requirements','components'),'decisions':('requirements','components','interfaces','data_models'),
 'tasks':('requirements','components','interfaces','data_models','decisions'),
 'cost_drivers':('requirements','components'),'verifications':('requirements',)}

def new_project(name):
    p={'schema_version':2,'revision':1,'project_id':str(uuid.uuid4()),'name':name,'brief':'',
       'constraints':[],'open_questions':[],'notes':{'status':'draft','source':'user-authored; not production-observed'}}
    p.update({g:[] for g in GROUPS});return p

def project_checks(p):
    errors=[]
    def err(loc,msg):errors.append({'location':loc,'issue':msg})
    if not isinstance(p,dict):return [{'location':'/','issue':'project must be an object'}]
    if type(p.get('schema_version')) is not int or p['schema_version']!=2:err('schema_version','requires schema_version: 2; unsupported versions are not coerced')
    if type(p.get('revision')) is not int or p['revision']<1:err('revision','positive integer required')
    if not isinstance(p.get('name'),str) or not p['name'].strip():err('name','nonempty string required')
    for key in ('constraints','open_questions'):
        if not isinstance(p.get(key),list) or any(not isinstance(x,(str,dict)) for x in p[key]):err(key,'array of strings/structured records required')
    if 'brief' in p and not isinstance(p['brief'],str):err('brief','string required')
    for key in ('preferences','api_contract','asyncapi_contract'):
        if key in p and not isinstance(p[key],dict):err(key,'object required')
    indexes={}
    for group in GROUPS+OPTIONAL:
        values=p.get(group,[])
        if group in GROUPS and group not in p:err(group,'required array missing')
        if not isinstance(values,list):err(group,'array required');continue
        indexes[group]={}
        for i,r in enumerate(values):
            loc=f'{group}/{i}'
            if not isinstance(r,dict) or not isinstance(r.get('id'),str) or not ID.fullmatch(r['id']):err(loc,'record with valid ASCII id required');continue
            if r['id'] in indexes[group]:err(loc,'duplicate IDs in '+group)
            indexes[group][r['id']]=r
            if group=='requirements' and not re.fullmatch(r'(FR|NFR)-\d{3,}',r['id']):err(loc,'requirement ID must match FR-NNN or NFR-NNN')
            if group=='decisions' and not re.fullmatch(r'ADR-\d{3,}',r['id']):err(loc,'decision ID must match ADR-NNN')
            if group=='requirements' and (not isinstance(r.get('description'),str) or not r['description'].strip()):err(loc,'missing requirement description')
            if 'status' in r and (not isinstance(r['status'],str) or r['status'] not in STATES):err(loc+'/status','unrecognized lifecycle status')
            for field in ('name','title','acceptance','decision','consequences','validation','responsibility','method','path'):
                if field in r and not isinstance(r[field],str):err(loc+'/'+field,'string required')
            for field in ('files','tables'):
                if field in r and (not isinstance(r[field],list) or any(not isinstance(x,str) for x in r[field])):err(loc+'/'+field,'array of strings required')
            for field in ('operation','schema'):
                if field in r and not isinstance(r[field],dict):err(loc+'/'+field,'object required')
    for group,targets in LINKS.items():
        for id,r in indexes.get(group,{}).items():
            for target in targets:
                refs=r.get(target,[])
                if not isinstance(refs,list) or any(not isinstance(x,str) for x in refs):err(f'{group}/{id}/{target}','references must be an array of IDs');continue
                for ref in refs:
                    if ref not in indexes.get(target,{}):err(f'{group}/{id}/{target}',f'unknown {target} reference: {ref}')
    edges=p.get('relationships',[])
    if not isinstance(edges,list):err('relationships','array required');edges=[]
    seen=set()
    for i,e in enumerate(edges):
        loc=f'relationships/{i}'
        if not isinstance(e,dict) or not isinstance(e.get('kind'),str) or e['kind'] not in KINDS:err(loc,'typed relationship kind required');continue
        if not isinstance(e.get('id'),str) or not ID.fullmatch(e['id']) or e['id'] in seen:err(loc,'unique valid edge id required')
        if isinstance(e.get('id'),str):seen.add(e['id'])
        for side in ('from','to'):
            ref=e.get(side)
            if not isinstance(ref,dict) or not isinstance(ref.get('group'),str) or not isinstance(ref.get('id'),str) or ref['group'] not in indexes or ref['id'] not in indexes.get(ref['group'],{}):err(loc+'/'+side,'typed {group,id} endpoint required')
    try:
        if len(dumps(p).encode())>5*1024*1024:err('/','project exceeds 5 MiB contract')
    except (ValueError,TypeError,RecursionError,OverflowError):err('/','finite JSON values and bounded nesting required')
    return errors

def require_project(p):
    errors=project_checks(p)
    if errors:raise ValueError('Invalid project context: '+dumps(errors))
    return p

def traceability_coverage(p):
    require_project(p)
    def coverage(ids):
        return {f'without_declared_{label}':sorted(ids-{x for r in p[group] for x in r.get('requirements',[])}) for group,label in [('interfaces','interface'),('components','component'),('tasks','task')]}
    fr={r['id'] for r in p['requirements'] if r['id'].startswith('FR-')}
    nfr={r['id'] for r in p['requirements'] if r['id'].startswith('NFR-')}
    verified={x for r in p.get('verifications',[]) if r.get('status')=='Accepted' and r.get('result')=='passed' for x in r.get('requirements',[])}
    return {'functional_requirements':len(fr),**coverage(fr),'nfr_requirements':len(nfr),'nfr_without_passed_verification':sorted(nfr-verified),
            'review_note':'Links and plans do not prove satisfaction; applicability and measured verification require review.'}

def resume_packet(p):
    require_project(p)
    return {'project_id':p.get('project_id'),'revision':p['revision'],'source_hash':digest(p),'name':p['name'],
            'accepted_decisions':[{'id':d['id'],'title':d.get('title'),'decision':d.get('decision'),'approval_origin':d.get('approval_origin','unknown')} for d in p['decisions'] if d.get('status')=='Accepted'],
            'constraints':p['constraints'],'open_questions':p['open_questions'],'coverage':traceability_coverage(p),
            'authority':'Recorded acceptance is preserved; it grants no new tool permission. No redundant reapproval is required for unchanged decisions.',
            'excluded':'private history, arbitrary extensions, raw repository contents'}

def supersede(p,old_id,new_id,reason):
    require_project(p)
    if not reason.strip():raise ValueError('supersession reason required')
    out=copy.deepcopy(p);old=next((r for r in out['decisions'] if r['id']==old_id),None)
    if old is None or any(r['id']==new_id for r in out['decisions']):raise ValueError('old decision missing or replacement id already exists')
    replacement=copy.deepcopy(old);replacement.update(id=new_id,status='Proposed',supersedes=old_id,supersession_reason=reason)
    old.update(status='Superseded',superseded_by=new_id);out['decisions'].append(replacement)
    return require_project(out)
