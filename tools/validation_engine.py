"""Scoped gates with typed terminal results and opt-in external validators."""
from __future__ import annotations
import importlib.util,importlib.metadata,json,math,os,re,shutil,signal,subprocess,sys,tempfile,time,uuid
from pathlib import Path
from urllib.parse import unquote
from safe_io import read_text,read_json,digest,guard,io_capabilities
from project_model import project_checks,traceability_coverage,VERSION
from codec import strict_json_loads
import xml.etree.ElementTree as ET

METHODS={'get','put','post','delete','options','head','patch','trace'}
PATH_FIELDS={'$ref','summary','description','servers','parameters'}
MERMAID_TYPES=('flowchart','graph','sequenceDiagram','erDiagram','stateDiagram-v2','classDiagram','gantt','mindmap','journey','timeline','pie','gitGraph','quadrantChart','C4Context','C4Container')

def _iter_refs(value, location="$"):
    """Yield every JSON $ref with a stable location for diagnostics."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}/{str(key).replace('~', '~0').replace('/', '~1')}"
            if key == "$ref":
                yield child_location, child
            else:
                yield from _iter_refs(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_refs(child, f"{location}/{index}")


def _resolve_local_ref(document, ref):
    """Resolve a local JSON Pointer without network access; return (target, error)."""
    if not isinstance(ref, str):
        return None, "$ref must be a string"
    if not ref.startswith("#"):
        return None, "external references are blocked by offline validation policy"
    fragment = unquote(ref[1:])
    if fragment == "":
        return document, None
    if not fragment.startswith("/"):
        return None, "only local JSON Pointer fragments are supported"
    current = document
    for raw_token in fragment[1:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            return None, "invalid JSON Pointer escape"
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return None, "pointer target does not exist"
            current = current[token]
        elif isinstance(current, list):
            if not re.fullmatch(r"0|[1-9]\d*", token):
                return None, "array pointer index is invalid"
            index = int(token)
            if index >= len(current):
                return None, "array pointer index is out of range"
            current = current[index]
        else:
            return None, "pointer traverses a non-container value"
    return current, None


def _external_refs(value):
    return any(not isinstance(ref, str) or not ref.startswith("#") for _, ref in _iter_refs(value))


def _parameter_target(parameter, document):
    if not isinstance(parameter, dict):
        return None
    if "$ref" not in parameter:
        return parameter
    target, error = _resolve_local_ref(document, parameter["$ref"])
    return target if error is None and isinstance(target, dict) else None


def _check_security_requirements(value, schemes, location, issues):
    if value is None:
        return
    if not isinstance(value, list):
        issues.append(location + ": security must be an array of requirement objects")
        return
    for index, requirement in enumerate(value):
        if not isinstance(requirement, dict):
            issues.append(f"{location}/{index}: security requirement must be an object")
            continue
        for name, scopes in requirement.items():
            if name not in schemes:
                issues.append(f"{location}/{index}: security scheme is not declared: {name}")
            if not isinstance(scopes, list) or any(not isinstance(scope, str) for scope in scopes):
                issues.append(f"{location}/{index}/{name}: security scopes must be an array of strings")
            elif scopes and isinstance(schemes.get(name), dict):
                scheme = schemes[name]
                if "$ref" not in scheme and scheme.get("type") not in ("oauth2", "openIdConnect"):
                    issues.append(f"{location}/{index}/{name}: non-OAuth security scopes must be empty")


def openapi_checks(data):
    if not isinstance(data, dict):
        return ["OpenAPI root must be an object"]
    issues = []
    if not isinstance(data.get("openapi"), str) or not re.match(r"^3\.(0|1)\.\d+$", data["openapi"]):
        issues.append("this pinned profile supports OpenAPI 3.0/3.1; unsupported versions are not coerced")
    info = data.get("info")
    if not isinstance(info, dict) or any(not isinstance(info.get(k), str) or not info[k] for k in ("title", "version")):
        issues.append("OpenAPI info.title and info.version required")
    paths = data.get("paths")
    if not isinstance(paths, dict):
        return issues + ["OpenAPI paths must be an object"]

    components = data.get("components", {})
    if not isinstance(components, dict):
        issues.append("OpenAPI components must be an object")
        components = {}
    schemes = components.get("securitySchemes", {})
    if not isinstance(schemes, dict):
        issues.append("components.securitySchemes must be an object")
        schemes = {}
    resolved_schemes = {}
    for name, scheme in schemes.items():
        if not isinstance(name, str) or not name or not isinstance(scheme, dict):
            issues.append("each security scheme must have a nonempty name and object definition")
            continue
        seen_refs = set()
        while isinstance(scheme, dict) and "$ref" in scheme:
            ref = scheme["$ref"]
            if not isinstance(ref, str) or ref in seen_refs:
                issues.append("cyclic or invalid security scheme reference")
                scheme = None
                break
            seen_refs.add(ref)
            scheme, error = _resolve_local_ref(data, ref)
            if error:
                scheme = None
                break
        if isinstance(scheme, dict):
            if scheme.get("type") not in ("apiKey", "http", "oauth2", "openIdConnect", "mutualTLS"):
                issues.append("security scheme type is unsupported or missing")
            resolved_schemes[name] = scheme
    _check_security_requirements(data.get("security"), resolved_schemes, "security", issues)

    # Resolve every reference before relying on it. The built-in gate stays offline.
    for location, ref in _iter_refs(data):
        if not isinstance(ref, str):
            issues.append(f"{location}: $ref must be a string")
        elif not ref.startswith("#"):
            issues.append(f"{location}: external references blocked by offline validation policy")
        else:
            _, error = _resolve_local_ref(data, ref)
            if error:
                issues.append(f"{location}: unresolved/unsupported local reference {ref!r}: {error}")

    ids = set()
    for path, item in paths.items():
        if not isinstance(path, str):
            issues.append("path keys must be strings")
            continue
        if path.startswith("x-"):
            continue
        if not path.startswith("/") or not isinstance(item, dict):
            issues.append("invalid path item: " + str(path))
            continue
        path_parameters = item.get("parameters", [])
        if not isinstance(path_parameters, list):
            issues.append(path + ": parameters must be an array")
            path_parameters = []
        for method, operation in item.items():
            if not isinstance(method, str):
                issues.append("path-item field names must be strings")
                continue
            if method in PATH_FIELDS or method.startswith("x-"):
                continue
            if method not in METHODS:
                issues.append(path + ": unknown path-item field " + str(method))
                continue
            if not isinstance(operation, dict):
                issues.append(path + " " + method + ": operation object required")
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict) or not responses:
                issues.append(path + " " + method + ": nonempty responses object required")
            else:
                for code, response in responses.items():
                    if not re.fullmatch(r"(default|[1-5](\d\d|XX)|x-.+)", str(code)):
                        issues.append("invalid response key: " + str(code))
                    if not isinstance(response, dict):
                        issues.append("response object or reference required: " + path + " " + str(code))
                    elif "$ref" not in response and not isinstance(response.get("description"), str):
                        issues.append("response description or reference required")
                    elif "$ref" in response:
                        target, error = _resolve_local_ref(data, response["$ref"])
                        if error is None and not isinstance(target, dict):
                            issues.append("response reference must resolve to an object: " + str(response["$ref"]))
            operation_id = operation.get("operationId")
            if operation_id is not None:
                if not isinstance(operation_id, str) or not operation_id or operation_id in ids:
                    issues.append("duplicate/nonstring operationId")
                else:
                    ids.add(operation_id)
            _check_security_requirements(operation.get("security"), resolved_schemes, path + " " + method + " security", issues)
            parameters = operation.get("parameters", [])
            if not isinstance(parameters, list):
                issues.append(path + " " + method + ": operation parameters must be an array")
                parameters = []
            resolved_parameters = []
            for parameter in parameters + path_parameters:
                if not isinstance(parameter, dict):
                    issues.append(path + " " + method + ": each parameter must be an object or local reference")
                    continue
                target = _parameter_target(parameter, data)
                if target is None:
                    if "$ref" in parameter:
                        issues.append(path + " " + method + ": parameter $ref must resolve to a parameter object: " + str(parameter.get("$ref")))
                    continue
                resolved_parameters.append(target)
            for name in re.findall(r"\{([^}]+)\}", path):
                if not any(
                    p.get("name") == name and p.get("in") == "path" and p.get("required") is True
                    for p in resolved_parameters
                ):
                    issues.append(path + ": required path parameter missing or invalid: " + name)
    return list(dict.fromkeys(issues))


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
        return strict_json_loads(r['output'])

def doctor():
    packages={}
    for p in ('PyYAML','jsonschema','openapi-spec-validator'):
        try:packages[p]=importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:packages[p]=None
    return {'toolkit_version':VERSION,'python':sys.version.split()[0],'platform':sys.platform,'packages':packages,'mmdc':shutil.which('mmdc'),
      'io':io_capabilities(),'network':'no automatic installs/fetching; host connector capabilities unprobed',
      'host_budgets':{'tokens':'unsupported','agent_count':'advisory; host must mediate','local_file_bytes':'enforced','subprocess_deadline':'enforced','external_tool_authority':'host enforcement required'}}

def _worker_summary(result):
    """Keep raw worker stdout private: only controlled terminal type/location escapes."""
    if result.get('status')=='passed':return 'requested schema validation passed'
    try:
        doc=strict_json_loads(result.get('output',''))
        error_type=doc.get('error_type','ValidationError')
        if not isinstance(error_type,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,80}',error_type):error_type='ValidationError'
        return error_type+': schema validation failed; values omitted'
    except (ValueError,TypeError):return 'validator '+str(result.get('status','unknown'))+'; diagnostics omitted'


def _contract_value(value, document, seen=(), depth=0):
    """Normalize offline references for scoped contract comparisons, with a cycle bound."""
    if depth > 40:
        raise ValueError('contract comparison nesting budget exceeded')
    if isinstance(value, dict):
        if '$ref' in value:
            ref=value['$ref']
            if not isinstance(ref,str):raise ValueError('invalid contract reference')
            if ref in seen:return {'$recursive_ref':ref}
            target,error=_resolve_local_ref(document,ref)
            if error:raise ValueError('unresolved contract reference')
            expanded=_contract_value(target,document,seen+(ref,),depth+1)
            siblings={k:v for k,v in value.items() if k!='$ref'}
            if not siblings:return expanded
            if isinstance(expanded,dict):return {**expanded,**_contract_value(siblings,document,seen,depth+1)}
        return {k:_contract_value(v,document,seen,depth+1) for k,v in value.items()
                if k not in {'summary','description','example','examples','externalDocs'} and not k.startswith('x-')}
    if isinstance(value,list):return [_contract_value(v,document,seen,depth+1) for v in value]
    return value


def _effective_parameters(document,path,operation):
    """Operation-level parameters override path-item parameters by (name,in)."""
    merged={}
    values=document.get('paths',{}).get(path,{}).get('parameters',[])+operation.get('parameters',[])
    for item in values:
        parameter=_contract_value(item,document)
        if not isinstance(parameter,dict):raise ValueError('invalid parameter')
        merged[(str(parameter.get('name')),str(parameter.get('in')))]=parameter
    return [merged[key] for key in sorted(merged)]


def contract_correspondence(project,api):
    """Compare supported operation semantics, independent of input format or filename."""
    from contract_resolution import resolve_contracts
    if openapi_checks(api):return ['supplied API fails structural contract validation']
    result=resolve_contracts(project)
    conflicts=result.get('conflicts',[])
    if conflicts:return ['canonical interface/native contract conflict']
    expected=result['api']
    issues=[]
    keys=('responses','requestBody','parameters','security','callbacks','deprecated','operationId')
    for interface in project.get('interfaces',[]):
        method=interface.get('method','').lower();path=interface.get('path','')
        if method not in METHODS or not path.startswith('/'):continue
        wanted=expected.get('paths',{}).get(path,{}).get(method)
        actual=api.get('paths',{}).get(path,{}).get(method)
        if not isinstance(actual,dict):issues.append('missing supported interface '+interface['id']);continue
        if not isinstance(wanted,dict):continue
        for key in keys:
            left=wanted.get(key,expected.get('security') if key=='security' else None)
            right=actual.get(key,api.get('security') if key=='security' else None)
            try:
                if key=='parameters':
                    left=_effective_parameters(expected,path,wanted)
                    right=_effective_parameters(api,path,actual)
                else:
                    left=_contract_value(left,expected)
                    right=_contract_value(right,api)
                if left!=right:issues.append(interface['id']+': '+key+' differs')
            except (ValueError,TypeError,AttributeError,RecursionError):
                issues.append(interface['id']+': '+key+' comparison incomplete')
        security=wanted.get('security',expected.get('security',[]))
        for requirement in security if isinstance(security,list) else []:
            for scheme in requirement if isinstance(requirement,dict) else []:
                expected_scheme=expected.get('components',{}).get('securitySchemes',{}).get(scheme)
                actual_scheme=api.get('components',{}).get('securitySchemes',{}).get(scheme)
                try:
                    if _contract_value(expected_scheme,expected)!=_contract_value(actual_scheme,api):
                        issues.append(interface['id']+': security scheme definition differs')
                except (ValueError,TypeError,AttributeError,RecursionError):
                    issues.append(interface['id']+': security scheme comparison incomplete')
    return issues


def validate(path,render=False,*,full_openapi=False,gate='report',max_files=500,max_bytes=10_000_000,deadline=15,contract_kind=None):
    path=guard(path)
    if not path.exists():raise FileNotFoundError(path)
    if gate not in {'report','structural','full'}:raise ValueError('unknown validation gate')
    if type(max_files) is not int or max_files<1 or type(max_bytes) is not int or max_bytes<1 or not isinstance(deadline,(int,float)) or isinstance(deadline,bool) or not math.isfinite(deadline) or not 0<deadline<=120:raise ValueError('invalid validation budget')
    if contract_kind not in {None, 'capability', 'receipt'}:raise ValueError('unknown integration contract kind')
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
            text=read_text(f,min(5*1024*1024,max_bytes-total));total+=len(text.encode());read+=1;sha=digest(text.encode())
            if suffix=='.mmd':
                issues=mermaid_checks(text);record(loc,'Mermaid heuristic',('warning' if render and shutil.which('mmdc') else 'failed') if issues else 'passed','; '.join(issues),'heuristic only',sha)
                if render:
                    if re.search(r'(?i)https?://|file://|%%\{|<\s*(img|script)|!\[',text):record(loc,'Mermaid renderer','blocked','external resources/directives/active markup disallowed')
                    elif not shutil.which('mmdc'):record(loc,'Mermaid renderer','skipped','mmdc not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            src=Path(tmp)/'input.mmd';src.write_text(text);conf=Path(tmp)/'config.json';conf.write_text('{"securityLevel":"strict","flowchart":{"htmlLabels":false}}')
                            rendered=Path(tmp)/'output.svg'
                            r=bounded_process([shutil.which('mmdc'),'-i',str(src),'-o',str(rendered),'-c',str(conf)],timeout=max(.05,min(8,deadline-(time.monotonic()-begin))),cwd=tmp)
                            status=r['status']
                            if status=='passed':
                                try:
                                    rendered_raw = read_text(rendered, 2_000_000)
                                    if not rendered_raw.strip() or '<!DOCTYPE' in rendered_raw.upper() or '<!ENTITY' in rendered_raw.upper():
                                        raise ValueError('empty or active SVG')
                                    svg = ET.fromstring(rendered_raw)
                                    if svg.tag.split('}')[-1] != 'svg':raise ValueError('SVG root required')
                                    for node in svg.iter():
                                        if node.tag.split('}')[-1].lower() in {'script','foreignobject','iframe'}:raise ValueError('active SVG element')
                                        if node.text and re.search(r'(?i)(https?://|file:|javascript:|data:|url\((?![\s\"\']*#))',node.text):raise ValueError('external or active SVG style')
                                        for key,value in node.attrib.items():
                                            if key.split('}')[-1].lower().startswith('on'):raise ValueError('active SVG attribute')
                                            if re.search(r'(?i)(https?://|file:|javascript:|data:|url\((?![\s\"\']*#))',value):raise ValueError('external or active SVG resource')
                                    rendered_sha=digest(rendered_raw.encode())
                                except (OSError,ValueError,ET.ParseError):status='tool_error'
                            detail = 'validated nonempty SVG SHA-256 '+rendered_sha if status=='passed' else 'renderer '+status+'; raw diagnostics omitted'
                            record(loc,'Mermaid renderer',status,detail,'external mmdc; host authority boundary',sha)
                else:record(loc,'Mermaid renderer','skipped','rendering not requested')
                continue
            if suffix=='.sql':record(loc,'SQL execution','skipped','raw migration SQL never executed; use supported structured SQLite schema adapter');continue
            if suffix in {'.yaml','.yml'}:
                try:
                    data=parse_yaml(text,min(2,max(.05,deadline-(time.monotonic()-begin))))
                except ImportError:record(loc,'YAML parse','skipped','PyYAML not installed');continue
            else:data=strict_json_loads(text)
            parsed[loc]=data
            detected_kind = contract_kind
            if detected_kind is None and isinstance(data,dict):
                schema_id = str(data.get('$schema', ''))
                if 'capabilities' in data and 'tool_id' in data or 'tool-capability-v1' in schema_id:detected_kind='capability'
                elif 'operation_id' in data and 'input_source_hash' in data or 'verification-receipt-v1' in schema_id:detected_kind='receipt'
            if detected_kind:
                from integration_contracts import validate_capability_manifest,validate_verification_receipt
                checker=validate_capability_manifest if detected_kind=='capability' else validate_verification_receipt
                errors=checker(data)
                record(loc,'Integration '+detected_kind+' contract','failed' if errors else 'passed','; '.join(errors),sha=sha)
            elif f.name.lower()=='project.json':
                errors=project_checks(data);record(loc,'Project traceability integrity','failed' if errors else 'passed',str(errors) if errors else '',sha=sha)
                if not errors:coverage[loc]=traceability_coverage(data)
                if gate=='full' and not errors:
                    if importlib.util.find_spec('jsonschema') is None:record(loc,'Project JSON Schema','skipped','optional jsonschema not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            supplied=Path(tmp)/'project.json';supplied.write_text(json.dumps(data))
                            r=bounded_process([sys.executable,str(Path(__file__).with_name('validator_worker.py')),'project',str(supplied)],timeout=max(.05,min(5,deadline-(time.monotonic()-begin))),cwd=tmp,memory_limit=256*1024*1024)
                            record(loc,'Project JSON Schema',r['status'],_worker_summary(r),'jsonschema '+importlib.metadata.version('jsonschema'),sha)
            elif isinstance(data,dict) and 'openapi' in data or f.name.lower() in {'api.json','api.yaml','api.yml','openapi.json','openapi.yaml','openapi.yml'}:
                issues=openapi_checks(data);record(loc,'OpenAPI basic structure','failed' if issues else 'passed','; '.join(issues),sha=sha)
                if full_openapi and not issues:
                    if importlib.util.find_spec('openapi_spec_validator') is None:record(loc,'OpenAPI full schema','skipped','optional openapi-spec-validator not installed')
                    else:
                        with tempfile.TemporaryDirectory() as tmp:
                            supplied=Path(tmp)/'api.json';supplied.write_text(json.dumps(data))
                            r=bounded_process([sys.executable,str(Path(__file__).with_name('validator_worker.py')),'openapi',str(supplied)],timeout=max(.05,min(5,deadline-(time.monotonic()-begin))),cwd=tmp,memory_limit=512*1024*1024)
                            record(loc,'OpenAPI full schema',r['status'],_worker_summary(r),'openapi-spec-validator '+importlib.metadata.version('openapi-spec-validator'),sha)
                else:record(loc,'OpenAPI full schema','skipped','not requested or basic gate failed')
            elif isinstance(data,dict) and 'asyncapi' in data:record(loc,'AsyncAPI declaration','passed' if isinstance(data.get('channels'),dict) and isinstance(data.get('info'),dict) else 'failed','basic envelope only; full schema not verified',sha=sha)
            else:record(loc,'JSON/YAML syntax','passed',sha=sha)
        except (OSError,ValueError,TypeError,AttributeError,UnicodeError,RecursionError) as e:record(loc,'Input parse/validation','failed',type(e).__name__+': input rejected; values omitted',sha=sha)
        except Exception as e:record(loc,'Validator execution','tool_error',type(e).__name__+': validator failed; values omitted',sha=sha)
    projects=[(name,doc) for name,doc in parsed.items() if name.lower().split('/')[-1]=='project.json' and isinstance(doc,dict) and not project_checks(doc)]
    apis=[(name,doc) for name,doc in parsed.items() if isinstance(doc,dict) and 'openapi' in doc]
    for project_name,p in projects:
        if 'correspondence deadline' in stops:break
        for api_name,api in apis:
            if Path(project_name).parent != Path(api_name).parent:continue
            if time.monotonic()-begin>deadline:
                stops.append('correspondence deadline')
                record(project_name,'Contract correspondence','not_run_due_to_budget','global deadline')
                break
            try:
                issues=contract_correspondence(p,api)
                record(project_name+' ↔ '+api_name,'Contract correspondence','failed' if issues else 'passed','; '.join(issues) if issues else 'supported declared operation semantics match')
            except (ValueError,TypeError,AttributeError,RecursionError):
                record(project_name+' ↔ '+api_name,'Contract correspondence','failed','contract comparison incomplete; values omitted')
    failures=[c for c in checks if c['status'] in {'failed','tool_error','blocked','timed_out'}]
    required_incomplete=[c for c in checks if c['status']=='not_run_due_to_budget' or c['status']=='skipped' and (c['check']=='YAML parse' or render and c['check']=='Mermaid renderer' or gate=='full' and c['check'] in {'OpenAPI full schema','Mermaid renderer','Project JSON Schema'})]
    ok=not failures
    policy_ok=ok and not required_incomplete and not stops and bool(checks)
    return {'ok':ok,'gate':gate,'policy_ok':policy_ok,'run_id':uuid.uuid4().hex,'toolkit_version':VERSION,'duration_seconds':round(time.monotonic()-begin,6),
      'files_checked':read,'bytes_read':total,'checks':checks,'checks_run':[{'file':c['file'],'check':c['check']} for c in checks if c['status'] not in {'skipped','not_run_due_to_budget'}],
      'issues':[{'file':c['file'],'issue':c['detail']} for c in failures], 'verified':[{'file':c['file'],'gate':c['check']} for c in checks if c['status']=='passed'],
      'warnings':[{'file':c['file'],'detail':c['detail']} for c in checks if c['status']=='warning'],'traceability_coverage':coverage,'skipped':[c['file']+': '+c['detail'] for c in checks if c['status']=='skipped'],'stop_reasons':stops,
      'note':'Scoped structural gates only; no certification, runtime deployment or universal semantic correctness. Required incomplete gates are not green.'}
