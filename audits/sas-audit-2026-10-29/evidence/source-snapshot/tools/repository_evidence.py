"""Bounded, read-only source adapters. No repository code or build is executed."""
from __future__ import annotations
import ast,copy,datetime,io,json,os,re,stat,time,tokenize
from pathlib import Path
from project_model import require_project,VERSION
from safe_io import digest,read_bytes,guard

IGNORE={'.git','node_modules','.next','dist','build','__pycache__','vendor','.venv','coverage','.architecture-history','.architecture-generations'}
MANIFESTS={'package.json','pyproject.toml','requirements.txt','go.mod','Cargo.toml','pom.xml','build.gradle','Dockerfile','docker-compose.yml','compose.yaml','Makefile'}
SOURCE={'.py','.js','.ts','.tsx','.jsx','.go','.rs','.java','.cs','.php','.rb','.sql','.kt'}
CONFIG={'.json','.yaml','.yml','.toml','.tf'}

def minimize(text):
    # Snippets are off by default; this defense-in-depth filter is not perfect secret detection.
    from disclosure import redact_text
    text=redact_text(text)
    text=re.sub(r'(?i)(token|secret|password|api[_-]?key)\s*[:=]\s*[\"\']?[^\s\"\',;)]+',r'\1=[REDACTED]',text)
    text=re.sub(r'([\"\'])(?:(?!\1).)*?\1','[literal withheld]',text)
    return text[:160]

def _python(text):
    tree=ast.parse(text);items=[];edges=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
            for name in names:items.append({'line':node.lineno,'end_line':getattr(node,'end_lineno',node.lineno),'observation':'parsed Python import','target':name,'class':'PARSED'});edges.append({'kind':'imports','target':name,'line':node.lineno})
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in {'get','post','put','patch','delete','head','options'}:
                    if dec.args and isinstance(dec.args[0],ast.Constant) and isinstance(dec.args[0].value,str):
                        items.append({'line':dec.lineno,'end_line':getattr(dec,'end_lineno',dec.lineno),'observation':'parsed route decorator candidate','method':dec.func.attr.upper(),'route':dec.args[0].value,'class':'PARSED; framework binding unverified'})
    return items,edges

def _javascript(text):
    # Narrow token adapter: ignores comments, quoted bodies and entire template literals.
    # Static import/export-from only; regex literals, symbols/frameworks remain unverified.
    token=re.compile(r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<template>`(?:\\.|[^`\\])*`)|(?P<word>[A-Za-z_$][\w$]*)|(?P<punct>[^\s])')
    tokens=[];line=1;end=0
    for m in token.finditer(text):
        line+=text[end:m.start()].count('\n');at=line;line+=m[0].count('\n');end=m.end()
        if m.lastgroup not in {'comment','template'}:tokens.append((m.lastgroup,m[0],at))
    items=[];edges=[]
    for i,(kind,value,at) in enumerate(tokens):
        if kind!='word' or value not in {'import','export'}:continue
        tail=tokens[i+1:i+80];target=None
        if value=='import' and tail and tail[0][0]=='string':target=tail[0][1][1:-1]
        else:
            for j,t in enumerate(tail[:-1]):
                if t[1]==';' or t[2]>at+8:break
                if t[0]=='word' and t[1]=='from' and tail[j+1][0]=='string':target=tail[j+1][1][1:-1];break
        if target:items.append({'line':at,'observation':'JS/TS static module token declaration','target':target,'class':'TOKENIZED; unresolved'});edges.append({'kind':'imports','target':target,'line':at})
    return items,edges

def _descriptor(name,text,timeout=2):
    data=None
    try:
        if name.endswith('.json'):data=json.loads(text)
        elif name.endswith(('.yaml','.yml')):
            from validation_engine import parse_yaml
            data=parse_yaml(text,timeout)
    except (ValueError,ImportError,Exception):return [],[]
    if not isinstance(data,dict):return [],[]
    items=[];edges=[]
    if name=='package.json':
        for kind in ('dependencies','devDependencies','peerDependencies'):
            if isinstance(data.get(kind),dict):
                for target in sorted(data[kind]):items.append({'line':1,'observation':kind,'target':target,'class':'DECLARED CONFIG'});edges.append({'kind':'package-depends-on','target':target,'line':1})
    for key in ('services','jobs'):
        if isinstance(data.get(key),dict):
            for id,entry in data[key].items():
                items.append({'line':1,'observation':key+' descriptor','target':id,'class':'DECLARED CONFIG; not deployed'})
                if isinstance(entry,dict):
                    deps=entry.get('depends_on',[]) if key=='services' else entry.get('needs',[])
                    if isinstance(deps,str):deps=[deps]
                    if isinstance(deps,(list,dict)):
                        for target in deps:edges.append({'kind':'depends-on','source':id,'target':target,'line':1})
    if 'openapi' in data or 'asyncapi' in data:
        collection='paths' if 'openapi' in data else 'channels'
        if isinstance(data.get(collection),dict):
            for name in data[collection]:items.append({'line':1,'observation':collection+' contract entry','target':name,'class':'DECLARED CONTRACT'})
    return items,edges

def repo_scan(root,project=None,limit=400,*,max_entries=10000,max_bytes=10_000_000,deadline=5.0,include_snippets=False,cache=None):
    root=guard(root)
    if not root.is_dir():raise ValueError('Expected a local repository directory')
    for k,v in [('limit',limit),('max_entries',max_entries),('max_bytes',max_bytes)]:
        if type(v) is not int or not 1<=v<=10_000_000:raise ValueError(k+' must be a positive bounded integer')
    if isinstance(deadline,bool) or not isinstance(deadline,(int,float)) or not 0<deadline<=60:raise ValueError('deadline must be in (0,60] seconds')
    start=time.monotonic();stack=[root];candidates=[];visited=0;files=0;omissions=[];stop=[];complete=True
    while stack:
        base=stack.pop()
        if time.monotonic()-start>deadline:stop.append('enumeration deadline');complete=False;break
        children=[]
        try:
            with os.scandir(base) as entries:
                for ent in entries:
                    if visited>=max_entries or time.monotonic()-start>deadline:complete=False;stop.append('entry/time budget');break
                    visited+=1;rel=Path(ent.path).relative_to(root).as_posix()
                    try:
                        s=ent.stat(follow_symlinks=False)
                        if stat.S_ISLNK(s.st_mode):omissions.append({'path':rel,'reason':'symlink'});continue
                        if stat.S_ISDIR(s.st_mode):
                            if ent.name in IGNORE:omissions.append({'path':rel,'reason':'excluded directory'})
                            else:children.append(Path(ent.path))
                            continue
                        files+=1
                        if not stat.S_ISREG(s.st_mode):omissions.append({'path':rel,'reason':'special file; never opened'});continue
                        path=Path(ent.path);suffix=path.suffix.lower()
                        kind='manifest' if path.name in MANIFESTS else 'infrastructure/config' if suffix in CONFIG or '.github' in path.parts else 'source' if suffix in SOURCE else None
                        if kind is None:omissions.append({'path':rel,'reason':'unsupported extension'});continue
                        priority=0 if kind=='manifest' or '.github' in path.parts else 1 if kind=='infrastructure/config' else 2
                        candidates.append((priority,rel,path,kind))
                    except OSError:omissions.append({'path':rel,'reason':'inaccessible metadata'})
        except OSError:omissions.append({'path':str(base.relative_to(root)),'reason':'inaccessible directory'})
        if not complete:break
        stack.extend(sorted(children,reverse=True))
    observed=[];declarations=[];dependencies=[];read=0;byte_count=0;cache_hits=0
    cached={}
    if cache is not None and Path(cache).exists():
        from safe_io import read_json
        saved=read_json(cache)
        if not isinstance(saved,dict) or saved.get('cache_schema')!=1 or not isinstance(saved.get('entries'),dict):raise ValueError('Unowned or invalid cache file preserved; choose a new cache path')
        if saved.get('adapter_version')==VERSION and saved.get('root')==str(root):
            cached={k:v for k,v in saved['entries'].items() if isinstance(v,dict) and isinstance(v.get('items'),list) and isinstance(v.get('edges'),list) and all(isinstance(x,dict) for x in v['items']+v['edges'])}
    new_cache={}
    for _,rel,path,kind in sorted(candidates):
        if read>=limit or time.monotonic()-start>deadline:stop.append('read count/time budget');omissions.append({'path':rel,'reason':'not read due to budget'});continue
        try:
            remaining=min(300_000,max_bytes-byte_count)
            if remaining<1:stop.append('total byte budget');omissions.append({'path':rel,'reason':'not read due to byte budget'});continue
            blob=read_bytes(path,remaining);byte_count+=len(blob);read+=1;sha=digest(blob);text=blob.decode('utf-8',errors='replace')
            obs={'path':rel,'kind':kind,'line':1,'observation':'regular file read; static evidence only','bytes':len(blob),'sha256':sha,'source':'local','source_revision':'unpinned local tree','extractor_version':VERSION}
            observed.append(obs);key=rel+':'+sha
            if key in cached:items,edges=cached[key]['items'],cached[key]['edges'];cache_hits+=1
            else:
                try:
                    if path.suffix=='.py':items,edges=_python(text)
                    elif path.suffix in {'.js','.ts','.tsx','.jsx'}:items,edges=_javascript(text)
                    elif kind in {'manifest','infrastructure/config'}:items,edges=_descriptor(path.name,text,max(.05,min(2,deadline-(time.monotonic()-start))))
                    else:items,edges=[],[];obs['extraction']='filename/content identity only; no language adapter'
                except SyntaxError as e:items,edges=[],[];obs['extraction']='unsupported/invalid parser input';omissions.append({'path':rel,'reason':'parser error','line':e.lineno})
            from disclosure import minimized
            items=minimized(items);edges=minimized(edges)
            new_cache[key]={'items':items,'edges':edges}
            for item in items[:100]:
                item=copy.deepcopy(item);item.update(path=rel,sha256=sha)
                if include_snippets:item['snippet']=minimize(text.splitlines()[max(0,item.get('line',1)-1)])
                declarations.append(item)
            dependencies.extend({**e,'path':rel,'sha256':sha} for e in edges[:100])
            if len(items)>100:omissions.append({'path':rel,'reason':'declaration quota','count':len(items)-100})
        except (OSError,ValueError,UnicodeError):omissions.append({'path':rel,'reason':'unread: unavailable, nonregular or byte budget exceeded'})
    if cache is not None:
        from safe_io import atomic_write,dumps
        atomic_write(cache,dumps({'cache_schema':1,'adapter_version':VERSION,'root':str(root),'entries':new_cache,'retention':'local opt-in; delete this file to purge extraction cache'}))
    result={'schema_version':1,'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_ref':'unpinned local tree; resolved commit not inferred','claim_class':'OBSERVED STATIC SOURCE','root':str(root),'adapter':'local-static','adapter_version':VERSION,'observed_files':observed,'static_declarations':declarations,'dependency_edges':dependencies,
      'scanned_count':read,'total_candidate_files':files if complete else None,'discovered_files':files,'entries_visited':visited,'eligible_discovered':len(candidates),
      'bytes_read':byte_count,'skipped_files':len(omissions),'omissions':omissions,'enumeration_complete':complete,'coverage':'partial' if stop or omissions else 'complete within supported static scope',
      'stop_reasons':sorted(set(stop)),'cache_hits':cache_hits,'source_fingerprint':digest([{k:r[k] for k in ('path','sha256')} for r in observed]),
      'coverage_note':'Read-only bounded static evidence. Python AST and narrow JS imports/config adapters; no runtime, full dependency or framework-binding guarantee. Local source is not commit-pinned. Snippets off by default.'}
    if project is not None:
        require_project(project);deviations=[]
        for c in project['components']:
            for rel in c.get('files',[]):
                try:
                    if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('escaping path')
                    p=guard(root/rel,root)
                    if not p.exists():status='not found'
                    elif not p.is_file():status='not a regular file'
                    elif rel not in {o['path'] for o in observed}:status='exists but unread/excluded'
                    else:continue
                except (OSError,ValueError):status='unverifiable path; symlink/escape/inaccessible'
                deviations.append({'component':c['id'],'path':rel,'status':status,'reason':'mapped path requires scoped review; absence of behavior not proven'})
        result['drift_candidates']=deviations;result['unmapped_components']=[c['id'] for c in project['components'] if not c.get('files')]
    return result

def evidence_delta(before,after):
    if before.get('adapter_version')!=after.get('adapter_version'):return {'status':'unknown','reason':'extractor versions differ; recollect within budgets'}
    a={r['path']:r['sha256'] for r in before.get('observed_files',[])};b={r['path']:r['sha256'] for r in after.get('observed_files',[])}
    return {'added':sorted(b.keys()-a.keys()),'removed_or_unread':sorted(a.keys()-b.keys()),'changed':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),'scope':'observed files only; unread is not deleted'}

def fitness(p,scan):
    require_project(p);results=[]
    for rule in p.get('fitness_rules',[]):
        if rule.get('kind')!='forbid_import':results.append({'id':rule['id'],'status':'unknown','reason':'unsupported rule kind'});continue
        prefix=rule.get('source_prefix');target=rule.get('target_prefix')
        if not isinstance(prefix,str) or not isinstance(target,str):raise ValueError('fitness source_prefix/target_prefix required')
        bad=[e for e in scan.get('dependency_edges',[]) if e['path'].startswith(prefix) and e.get('target','').startswith(target)]
        scope=[r for r in scan.get('observed_files',[]) if r['path'].startswith(prefix)]
        results.append({'id':rule['id'],'status':'violation' if bad else 'satisfied-in-scope' if scope else 'unknown','counterexamples':bad,'coverage':scan.get('coverage'),'note':'No global compliance inferred from partial static evidence.'})
    return {'rules':results,'source_fingerprint':scan.get('source_fingerprint'),'project_hash':digest(p)}
