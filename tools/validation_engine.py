"""Scoped gates with typed terminal results and opt-in external validators."""
from __future__ import annotations
import importlib.util,importlib.metadata,json,math,os,re,shutil,signal,subprocess,sys,tempfile,time,uuid
from pathlib import Path
from safe_io import read_text,read_json,digest,guard,io_capabilities
from project_model import project_checks,traceability_coverage,VERSION

METHODS={'get','put','post','delete','options','head','patch','trace'}
PATH_FIELDS={'$ref','summary','description','servers','parameters'}
MERMAID_TYPES=('flowchart','graph','sequenceDiagram','erDiagram','stateDiagram-v2','classDiagram','gantt','mindmap','journey','timeline','pie','gitGraph','quadrantChart','C4Context','C4Container')

def _external_refs(value):
    stack=[value];seen=set()
    while stack:
        x=stack.pop()
        if isinstance(x,(dict,list)):
            if id(x) in seen:continue
            seen.add(id(x))
        if isinstance(x,dict):
            if '$ref' in x and (not isinstance(x['$ref'],str) or not x['$ref'].startswith('#')):return True
            stack.extend(x.values())
        elif isinstance(x,list):stack.extend(x)
    return False

def openapi_checks(data):
    if not isinstance(data,dict):return ['OpenAPI root must be an object']
    issues=[]
    if not isinstance(data.get('openapi'),str) or not re.match(r'^3\.(0|1)\.\d+$',data['openapi']):issues.append('this pinned profile supports OpenAPI 3.0/3.1; unsupported versions are not coerced')
    info=data.get('info')
    if not isinstance(info,dict) or any(not isinstance(info.get(k),str) or not info[k] for k in ('title','version')):issues.append('OpenAPI info.title and info.version required')
    if not isinstance(data.get('paths'),dict):return issues+['OpenAPI paths must be an object']
    ids=set()
    for path,item in data['paths'].items():
        if path.startswith('x-'):continue
        if not path.startswith('/') or not isinstance(item,dict):issues.append('invalid path item: '+path);continue
        path_parameters=item.get('parameters',[])
        if not isinstance(path_parameters,list):issues.append(path+': parameters must be an array');path_parameters=[]
        for method,op in item.items():
            if method in PATH_FIELDS or method.startswith('x-'):continue
            if method not in METHODS:issues.append(path+': unknown path-item field '+method);continue
            if not isinstance(op,dict):issues.append(path+' '+method+': operation object required');continue
            responses=op.get('responses')
            if not isinstance(responses,dict) or not responses:issues.append(path+' '+method+': nonempty responses object required')
            else:
                for code,r in responses.items():
                    if not re.fullmatch(r'(default|[1-5](\d\d|XX)|x-.+)',str(code)):issues.append('invalid response key: '+str(code))
                    if not isinstance(r,dict) or ('$ref' not in r and not isinstance(r.get('description'),str)):issues.append('response description or reference required')
            oid=op.get('operationId')
            if oid is not None:
                if not isinstance(oid,str) or oid in ids:issues.append('duplicate/nonstring operationId')
                else:ids.add(oid)
            params=op.get('parameters',[])
            if not isinstance(params,list):issues.append('operation parameters must be an array');params=[]
            for name in re.findall(r'\{([^}]+)\}',path):
                if not any(isinstance(p,dict) and (p.get('$ref') or p.get('name')==name and p.get('in')=='path' and p.get('required') is True) for p in params+path_parameters):issues.append(path+': required path parameter missing: '+name)
    if _external_refs(data):issues.append('external references blocked by offline validation policy')
    return issues

def mermaid_checks(text):
    text=text.strip()
    if not text:return ['empty Mermaid file']
    lead=next((l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith('%%')),'')
    issues=[]
    if not any(lead==x or lead.startswith(x+' ') for x in MERMAID_TYPES):issues.append('unsupported or missing Mermaid diagram declaration')
    if '```' in text:issues.append('code fences should not occur inside .mmd')
    if any(l.rstrip().endswith(('-->','-.->','==>')) for l in text.splitlines()):issues.append('dangling flow arrow')
    # Delimiter counting is intentionally omitted: quoted labels make it unsound.
    return issues

def bounded_process(args,*,timeout=10,output_limit=200_000,cwd=None,memory_limit=None):
    """Killable process group, bounded file output. Not an OS authority sandbox."""
    def limits():
        import resource
        resource.setrlimit(resource.RLIMIT_FSIZE,(output_limit,output_limit))
        resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(timeout)+1),max(1,math.ceil(timeout)+1)))
        if memory_limit:resource.setrlimit(resource.RLIMIT_AS,(memory_limit,memory_limit))
    env={'PATH':os.environ.get('PATH',''),'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}
    with tempfile.TemporaryFile() as output:
        proc=subprocess.Popen(args,stdout=output,stderr=output,cwd=cwd,env=env,start_new_session=os.name=='posix',preexec_fn=limits if os.name=='posix' else None)
        try:proc.wait(timeout=timeout);status='passed' if proc.returncode==0 else 'failed'
        except subprocess.TimeoutExpired:
            if os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
            else:proc.kill()
            proc.wait();status='timed_out'
        output.seek(0);raw=output.read(output_limit+1)
        return {'status':status,'returncode':proc.returncode,'output':raw[:output_limit].decode('utf-8',errors='replace'),'truncated':len(raw)>output_limit,
                'isolation':'deadline/process group and POSIX file-size cap; inherited OS authority not sandboxed; network policy must be enforced by host'}

def parse_yaml(text,timeout=2):
    if importlib.util.find_spec('yaml') is None:raise ImportError('PyYAML not installed')
    with tempfile.TemporaryDirectory() as tmp:
        supplied=Path(tmp)/'input.yaml';supplied.write_text(text)
        r=bounded_process([sys.executable,str(Path(__file__).with_name('validator_worker.py')),'yaml',str(supplied)],timeout=max(.05,timeout),cwd=tmp,memory_limit=256*1024*1024)
        if r['status']!='passed':raise ValueError('bounded YAML parse '+r['status']+': '+r['output'][:300])
        return json.loads(r['output'])

def doctor():
    packages={}
    for p in ('PyYAML','jsonschema','openapi-spec-validator'):
        try:packages[p]=importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:packages[p]=None
    return {'toolkit_version':VERSION,'python':sys.version.split()[0],'platform':sys.platform,'packages':packages,'mmdc':shutil.which('mmdc'),
      'io':io_capabilities(),'network':'no automatic installs/fetching; host connector capabilities unprobed',
      'host_budgets':{'tokens':'unsupported','agent_count':'advisory; host must mediate','local_file_bytes':'enforced','subprocess_deadline':'enforced','external_tool_authority':'host enforcement required'}}

def validate(path,render=False,*,full_openapi=False,gate='report',max_files=500,max_bytes=10_000_000,deadline=15):
    path=guard(path)
    if not path.exists():raise FileNotFoundError(path)
    if gate not in {'report','structural','full'}:raise ValueError('unknown validation gate')
    if type(max_files) is not int or max_files<1 or type(max_bytes) is not int or max_bytes<1 or not isinstance(deadline,(int,float)) or isinstance(deadline,bool) or not math.isfinite(deadline) or not 0<deadline<=120:raise ValueError('invalid validation budget')
    begin=time.monotonic();checks=[];coverage={};seen=0;read=0;total=0;files=[];stops=[]
    def record(file,check,status,detail='',method='built-in',sha=None):
        checks.append({'file':file,'check':check,'status':status,'detail':detail,'method':method,'input_sha256':sha,'toolkit_version':VERSION})
    root=path if path.is_dir() else path.parent
    pointer=path/'.handoff-current.json' if path.is_dir() else None
    if pointer is not None and pointer.exists():
        p=read_json(pointer);name=p.get('generation')
        if not isinstance(name,str) or not re.fullmatch(r'[a-f0-9]{32}',name):raise ValueError('invalid handoff generation pointer')
        root=guard(path/'.architecture-generations'/name,path);path=root
    if path.is_file():files=[path]
    else:
        stack=[path]
        while stack:
            base=stack.pop()
            if time.monotonic()-begin>deadline:stops.append('enumeration deadline');break
            try:
                with os.scandir(base) as entries:
                    for ent in entries:
                        seen+=1
                        if seen>max_files*10 or len(files)>=max_files:stops.append('enumeration/file budget');break
                        if ent.is_symlink():record(str(Path(ent.path).relative_to(root)),'Input policy','blocked','symlink not followed');continue
                        if ent.is_dir(follow_symlinks=False):
                            if not ent.name.startswith('.') and ent.name not in {'node_modules','__pycache__'}:stack.append(Path(ent.path))
                        elif ent.is_file(follow_symlinks=False) and not ent.name.startswith('.'):files.append(Path(ent.path))
                        else:record(str(Path(ent.path).relative_to(root)),'Input policy','blocked','not a regular supported file')
                    if stops:break
            except OSError as e:record(str(base.relative_to(root)),'Input policy','blocked','directory could not be enumerated: '+type(e).__name__)
    parsed={}
    for f in sorted(files):
        loc=str(f.relative_to(root));sha=None
        if time.monotonic()-begin>deadline:record(loc,'Budget','not_run_due_to_budget','global deadline');continue
        suffix=f.suffix.lower()
        if suffix not in {'.json','.yaml','.yml','.mmd','.sql'}:continue
        if max_bytes-total<1:record(loc,'Budget','not_run_due_to_budget','total byte budget');continue
        try:
            text=read_text(f,min(1_000_000,max_bytes-total));total+=len(text.encode());read+=1;sha=digest(text.encode())
            if suffix=='.mmd':
                issues=mermaid_checks(text);record(loc,'Mermaid heuristic',('warning' if render and shutil.which('mmdc') else 'failed') if issues else 'passed','; '.join(issues),'heuristic only',sha)
                if render:
                    if re.search(r'(?i)https?://|file://|%%\{|<\s*(img|script)|!\[',text):record(loc,'Mermaid renderer','blocked','external resources/directives/active markup disallowed')
                    elif not shutil.which('mmdc'):record(loc,'Mermaid renderer','skipped','mmdc not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            src=Path(tmp)/'input.mmd';src.write_text(text);conf=Path(tmp)/'config.json';conf.write_text('{"securityLevel":"strict"}')
                            rendered=Path(tmp)/'output.svg'
                            r=bounded_process([shutil.which('mmdc'),'-i',str(src),'-o',str(rendered),'-c',str(conf)],timeout=max(.05,min(8,deadline-(time.monotonic()-begin))),cwd=tmp)
                            status=r['status']
                            if status=='passed' and not rendered.is_file():status='tool_error'
                            record(loc,'Mermaid renderer',status,r['output'][-1500:],'external mmdc; host authority boundary',sha)
                else:record(loc,'Mermaid renderer','skipped','rendering not requested')
                continue
            if suffix=='.sql':record(loc,'SQL execution','skipped','raw migration SQL never executed; use supported structured SQLite schema adapter');continue
            if suffix in {'.yaml','.yml'}:
                try:
                    data=parse_yaml(text,min(2,max(.05,deadline-(time.monotonic()-begin))))
                except ImportError:record(loc,'YAML parse','skipped','PyYAML not installed');continue
            else:data=json.loads(text,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON number')))
            parsed[loc]=data
            if f.name.lower()=='project.json':
                errors=project_checks(data);record(loc,'Project traceability integrity','failed' if errors else 'passed',str(errors) if errors else '',sha=sha)
                if not errors:coverage[loc]=traceability_coverage(data)
                if gate=='full' and not errors:
                    if importlib.util.find_spec('jsonschema') is None:record(loc,'Project JSON Schema','skipped','optional jsonschema not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            supplied=Path(tmp)/'project.json';supplied.write_text(json.dumps(data))
                            r=bounded_process([sys.executable,str(Path(__file__).with_name('validator_worker.py')),'project',str(supplied)],timeout=max(.05,min(5,deadline-(time.monotonic()-begin))),cwd=tmp,memory_limit=256*1024*1024)
                            record(loc,'Project JSON Schema',r['status'],r['output'][-1500:],'jsonschema '+importlib.metadata.version('jsonschema'),sha)
            elif isinstance(data,dict) and 'openapi' in data or f.name.lower() in {'api.json','api.yaml','api.yml','openapi.json','openapi.yaml','openapi.yml'}:
                issues=openapi_checks(data);record(loc,'OpenAPI basic structure','failed' if issues else 'passed','; '.join(issues),sha=sha)
                if full_openapi and not issues:
                    if importlib.util.find_spec('openapi_spec_validator') is None:record(loc,'OpenAPI full schema','skipped','optional openapi-spec-validator not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            supplied=Path(tmp)/'api.json';supplied.write_text(json.dumps(data))
                            r=bounded_process([sys.executable,str(Path(__file__).with_name('validator_worker.py')),'openapi',str(supplied)],timeout=max(.05,min(5,deadline-(time.monotonic()-begin))),cwd=tmp)
                            record(loc,'OpenAPI full schema',r['status'],r['output'][-1500:],'openapi-spec-validator '+importlib.metadata.version('openapi-spec-validator'),sha)
                else:record(loc,'OpenAPI full schema','skipped','not requested or basic gate failed')
            elif isinstance(data,dict) and 'asyncapi' in data:record(loc,'AsyncAPI declaration','passed' if isinstance(data.get('channels'),dict) and isinstance(data.get('info'),dict) else 'failed','basic envelope only; full schema not verified',sha=sha)
            else:record(loc,'JSON/YAML syntax','passed',sha=sha)
        except (OSError,ValueError,TypeError,AttributeError,UnicodeError,RecursionError) as e:record(loc,'Input parse/validation','failed',type(e).__name__+': '+str(e)[:1500],sha=sha)
        except Exception as e:record(loc,'Validator execution','tool_error',type(e).__name__+': '+str(e)[:500],sha=sha)
    p=parsed.get('project.json');api=parsed.get('api.json')
    if isinstance(p,dict) and not project_checks(p) and isinstance(api,dict):
        missing=[]
        for it in p['interfaces']:
            method=it.get('method','').lower();url=it.get('path','')
            if method in METHODS and url.startswith('/') and method not in api.get('paths',{}).get(url,{}):missing.append(it['id'])
        record('project.json ↔ api.json','Contract correspondence','failed' if missing else 'passed','missing supported HTTP interfaces: '+', '.join(missing) if missing else 'supported operation coverage only')
    failures=[c for c in checks if c['status'] in {'failed','tool_error','blocked','timed_out'}]
    required_incomplete=[c for c in checks if c['status']=='not_run_due_to_budget' or c['status']=='skipped' and (c['check']=='YAML parse' or gate=='full' and c['check'] in {'OpenAPI full schema','Mermaid renderer','Project JSON Schema'})]
    ok=not failures
    policy_ok=ok and not required_incomplete and not stops and bool(checks)
    return {'ok':ok,'gate':gate,'policy_ok':policy_ok,'run_id':uuid.uuid4().hex,'toolkit_version':VERSION,'duration_seconds':round(time.monotonic()-begin,6),
      'files_checked':read,'bytes_read':total,'checks':checks,'checks_run':[{'file':c['file'],'check':c['check']} for c in checks if c['status'] not in {'skipped','not_run_due_to_budget'}],
      'issues':[{'file':c['file'],'issue':c['detail']} for c in failures], 'verified':[{'file':c['file'],'gate':c['check']} for c in checks if c['status']=='passed'],
      'warnings':[{'file':c['file'],'detail':c['detail']} for c in checks if c['status']=='warning'],'traceability_coverage':coverage,'skipped':[c['file']+': '+c['detail'] for c in checks if c['status']=='skipped'],'stop_reasons':stops,
      'note':'Scoped structural gates only; no certification, runtime deployment or universal semantic correctness. Required incomplete gates are not green.'}
