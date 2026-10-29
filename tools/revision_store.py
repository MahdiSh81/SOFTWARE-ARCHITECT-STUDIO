"""Recoverable local revisions. project.json atomic replacement is the commit point.

History is a derived projection; journal entries retain messages before commit.
No cross-file atomicity, hostile-writer lock or power-loss certification claimed.
"""
from pathlib import Path
import copy,datetime,re,uuid
from project_model import new_project,require_project
from safe_io import atomic_write,read_json,read_bytes,dumps,digest,guard,project_lock

def load_project(root):return require_project(read_json(Path(root)/'project.json'))

def init_project(root,name):
    root=guard(root)
    for n in ('project.json','HISTORY.md','.architecture-journal.json','.architecture-history'):
        if (root/n).exists() or (root/n).is_symlink():raise ValueError(n+' already exists; refusing initialization')
    p=require_project(new_project(name))
    with project_lock(root):
        # Journal makes initialization recoverable if the history projection fails.
        atomic_write(root/'project.json',dumps(p),exclusive=True)
        atomic_write(root/'HISTORY.md','# Architecture change history\n\n- Revision 1: Initial project context.\n',exclusive=True)
    return {'project_file':str(root/'project.json'),'revision':1,'versioned':True,'warning':'Local files require actual backed-up storage/Git for cross-session continuity.'}

def _validated_journal(j):
    """Journal bytes are data, not path authority or proof of a valid payload."""
    if not isinstance(j,dict):raise ValueError('invalid recovery journal object; original preserved')
    if not isinstance(j.get('operation_id'),str) or not re.fullmatch(r'[a-f0-9]{32}',j['operation_id']):raise ValueError('invalid recovery journal operation id; original preserved')
    if not isinstance(j.get('status'),str) or j['status'] not in {'prepared','committed'}:raise ValueError('invalid recovery journal status')
    if any(type(j.get(k)) is not int or j[k]<1 for k in ('saved_revision','next_revision')) or j['next_revision']!=j['saved_revision']+1:raise ValueError('invalid recovery journal revisions')
    if any(not isinstance(j.get(k),str) or not re.fullmatch(r'[a-f0-9]{64}',j[k]) for k in ('old_hash','new_hash')):raise ValueError('invalid recovery journal hashes')
    if any(not isinstance(j.get(k),str) or not j[k].strip() for k in ('message','at','snapshot_file')):raise ValueError('invalid recovery journal metadata')
    try:p=require_project(j.get('new_project'))
    except ValueError as e:raise ValueError('invalid recovery journal project; original preserved') from e
    if p['revision']!=j['next_revision'] or digest(p)!=j['new_hash']:raise ValueError('recovery journal payload/hash mismatch; original preserved')
    return j

def _history(root,journal):
    records=[];folder=root/'.architecture-history'
    if folder.exists():
        for path in sorted(folder.glob('commit-*.json')):
            r=_validated_journal(read_json(path))
            if path.name!='commit-'+r['operation_id']+'.json':raise ValueError('history journal filename/identity mismatch')
            if r['status']=='committed':records.append(r)
    records.sort(key=lambda r:(r['next_revision'],r['operation_id']))
    if len({r['next_revision'] for r in records})!=len(records):raise ValueError('duplicate history journal revisions; original preserved')
    text='# Architecture change history\n\n- Revision 1: Initial project context.\n'
    text+=''.join(f'- Revision {r["next_revision"]}: {r["message"].replace(chr(10)," ")} ({r["at"]}; operation {r["operation_id"]})\n' for r in records)
    atomic_write(root/'HISTORY.md',text)

def _recover_locked(root):
    path=root/'.architecture-journal.json'
    if not path.exists():return None
    j=_validated_journal(read_json(path))
    if j.get('status')=='committed':
        current=load_project(root)
        if digest(current)!=j['new_hash']:
            raise ValueError('committed journal/current project hash mismatch; history projection refused and original preserved')
        _history(root,j);return j
    committed={**j,'status':'committed'}
    commit_path=guard(root/'.architecture-history'/('commit-'+j['operation_id']+'.json'),root)
    if commit_path.exists() and digest(_validated_journal(read_json(commit_path)))!=digest(committed):raise ValueError('history journal conflict; existing record and project preserved')
    current=load_project(root);h=digest(current)
    if h==j['old_hash']:atomic_write(root/'project.json',dumps(j['new_project']))
    elif h!=j['new_hash']:raise ValueError('recovery conflict: current project differs from both journal revisions; preserved without overwrite')
    j=committed
    if not commit_path.exists():atomic_write(commit_path,dumps(j),exclusive=True)
    atomic_write(path,dumps(j));_history(root,j)
    return j

def recover(root):
    root=guard(root)
    with project_lock(root):
        j=_recover_locked(root)
        if j is None and (root/'project.json').exists() and not (root/'HISTORY.md').exists():
            load_project(root);_history(root,None)
    return {'status':'no pending operation' if not j else j['status'],'operation_id':j.get('operation_id') if j else None,'commit_point':'atomic project.json replacement; history is recoverable projection'}

def commit_project(root,proposed,message,expected_hash):
    root=guard(root);require_project(proposed)
    if not isinstance(message,str) or not message.strip():raise ValueError('nonempty change message required')
    with project_lock(root):
        pending=root/'.architecture-journal.json'
        if pending.exists() and _validated_journal(read_json(pending))['status']!='committed':raise ValueError('pending operation; run recover before editing')
        old=load_project(root)
        if digest(old)!=expected_hash:raise ValueError('revision conflict: expected hash differs; both drafts preserved')
        new=copy.deepcopy(proposed);new['revision']=old['revision']+1;require_project(new)
        stamp=root/'.architecture-history'/f'revision-{old["revision"]:04d}.json'
        if stamp.exists():
            if digest(read_json(stamp))!=digest(old):raise ValueError('immutable snapshot conflict')
        else:atomic_write(stamp,dumps(old),exclusive=True)
        j={'operation_id':uuid.uuid4().hex,'status':'prepared','saved_revision':old['revision'],'next_revision':new['revision'],
           'old_hash':digest(old),'new_hash':digest(new),'new_project':new,'message':message.strip(),
           'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot_file':str(stamp)}
        atomic_write(root/'.architecture-journal.json',dumps(j))
        _recover_locked(root)
    return {'saved_revision':j['saved_revision'],'next_revision':j['next_revision'],'snapshot_file':str(stamp),
      'operation_id':j['operation_id'],'message':message.strip(),'source_hash':j['new_hash'],'status':'committed','note':'Local single-project commit; Git/backups required for durable shared history.'}

def snapshot(root,message):
    root=guard(root)
    pending=root/'.architecture-journal.json'
    if pending.exists():
        j=_validated_journal(read_json(pending))
        if j.get('status')!='committed':
            if j['message']!=message.strip():raise ValueError('pending different operation; recover first')
            recover(root);return {k:j[k] for k in ('saved_revision','next_revision','snapshot_file','operation_id','message')}
    p=load_project(root);return commit_project(root,p,message,digest(p))

def restore(root,revision,expected_hash,message):
    if type(revision) is not int or revision<1:raise ValueError('positive revision required')
    source=read_json(guard(Path(root)/'.architecture-history'/f'revision-{revision:04d}.json'))
    return commit_project(root,source,message,expected_hash)
