"""Pure resolution of declared API intent; never retrieves or executes contracts."""
import copy
import re
from urllib.parse import unquote
from codec import digest

METHODS = {'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'}


def semantic(value):
    """Compare supported authored semantics without documentation-only differences."""
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items()
                if k not in {'summary', 'description', 'example', 'examples', 'externalDocs'}
                and not k.startswith('x-')}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


def normalized(value, document, seen=(), depth=0):
    """Resolve local references for comparison only; retain bounded recursive refs."""
    if depth > 40:
        raise ValueError('contract reference nesting budget exceeded')
    if isinstance(value, dict):
        if '$ref' in value:
            ref = value['$ref']
            if not isinstance(ref, str) or not ref.startswith('#'):
                raise ValueError('only offline local references supported for correspondence')
            if ref in seen:
                return {'$recursive_ref': ref}
            target = document
            fragment = unquote(ref[1:])
            if fragment and not fragment.startswith('/'):
                raise ValueError('local JSON Pointer required')
            parts = fragment[1:].split('/') if fragment else []
            for part in parts:
                if re.search(r'~(?![01])', part):
                    raise ValueError('invalid reference escape')
                part = part.replace('~1', '/').replace('~0', '~')
                try:
                    if isinstance(target, list):
                        if not re.fullmatch(r'0|[1-9][0-9]*', part):
                            raise ValueError('invalid array pointer index')
                        target = target[int(part)]
                    elif isinstance(target, dict):
                        target = target[part]
                    else:
                        raise ValueError('pointer crosses scalar')
                except (KeyError, IndexError, ValueError, TypeError):
                    raise ValueError('unresolved local contract reference') from None
            expanded = normalized(target, document, seen + (ref,), depth + 1)
            siblings = normalized({k:v for k,v in value.items() if k != '$ref'}, document, seen, depth + 1)
            return {**expanded, **siblings} if isinstance(expanded, dict) else expanded
        return {k:normalized(v,document,seen,depth+1) for k,v in semantic(value).items()}
    if isinstance(value,list):
        return [normalized(v,document,seen,depth+1) for v in value]
    return value


def resolve_contracts(project):
    native = project.get('api_contract')
    api = copy.deepcopy(native) if isinstance(native, dict) else {
        'openapi': '3.0.3', 'info': {'title': project['name'] + ' API (PROPOSED)',
                                  'version': '0.1.0'}, 'paths': {}}
    if not native and project.get('security_schemes'):
        api['components'] = {'securitySchemes': copy.deepcopy(project['security_schemes'])}
    paths = api.setdefault('paths', {})
    resolved, conflicts, authentication, seen = {}, [], [], set()
    def conflict(record, field, reason):
        conflicts.append({'record': record, 'field': field, 'reason': reason})
    if not isinstance(paths, dict):
        conflict('project', 'api_contract/paths', 'OpenAPI paths must be an object')
        return {'api': api, 'resolved': {}, 'conflicts': conflicts, 'authentication': [], 'identity': digest(api)}
    for item in project.get('interfaces', []):
        method, path, rid = item.get('method', '').lower(), item.get('path', ''), item['id']
        if method not in METHODS or not path.startswith('/'):
            continue
        if (method, path) in seen:
            conflict(rid, 'operation', 'duplicate HTTP method/path: ' + method + ' ' + path)
        seen.add((method, path))
        authored = item.get('operation')
        path_item = paths.get(path, {})
        if not isinstance(path_item, dict):
            conflict(rid, 'operation', 'OpenAPI path item must be an object')
            path_item = {}
        operation = path_item.get(method) if native else copy.deepcopy(authored)
        if native and operation is None:
            conflict(rid, 'operation', 'native API missing declared interface')
            operation = {}
        if not isinstance(operation, dict):
            operation = {}
        if 'operationId' in operation and (not isinstance(operation['operationId'], str) or not operation['operationId']):
            conflict(rid, 'operationId', 'operationId must be a nonempty string')
        if native and isinstance(authored, dict):
            expected = copy.deepcopy(authored)
            actual = copy.deepcopy(operation)
            expected.setdefault('security', api.get('security', None))
            actual.setdefault('security', api.get('security', None))
            # Compare authored fields; native may add documentation and optional details.
            for field in expected:
                if normalized(expected[field], api) != normalized(actual.get(field), api):
                    conflict(rid, 'operation/' + field, 'native and interface contract disagree')
        security = operation.get('security', api.get('security'))
        intent = item.get('authentication')
        protected = isinstance(security,list) and bool(security) and all(isinstance(x,dict) and bool(x) for x in security)
        anonymous = isinstance(security,list) and (not security or any(x=={} for x in security))
        policy = 'required' if protected else 'public' if anonymous else 'unspecified'
        if isinstance(intent, dict):
            declared = intent.get('policy', 'unspecified')
            if declared == 'required' and not protected:
                conflict(rid, 'authentication', 'required authentication has no concrete security requirement')
            if declared == 'public' and protected:
                conflict(rid, 'authentication', 'public intent contradicts protected operation')
            if not isinstance(declared,str) or declared not in {'required', 'public', 'unspecified'}:
                conflict(rid, 'authentication', 'unknown authentication policy')
            if declared == 'public' and not protected:
                if not native:operation['security'] = []; security = []
                policy = 'public'
        elif isinstance(intent, str) and intent.strip():
            public = intent.strip().lower() in {'public', 'none', 'no authentication', 'not applicable'}
            if public and protected:
                conflict(rid, 'authentication', 'public intent contradicts protected operation')
            elif public and not protected:
                if not native:operation['security'] = []; security = []
                policy = 'public'
            elif not public and not protected:
                conflict(rid, 'authentication', 'prose authentication requires supplied concrete security schemes and requirements')
        if not native:
            if not operation:
                operation = {'responses': {'200': {'description': 'PLACEHOLDER: confirm contract'}},
                             'x-readiness': 'draft placeholder'}
            operation.setdefault('operationId', rid)
            paths.setdefault(path, {})[method] = operation
        resolved[rid] = operation
        authentication.append({'record': rid, 'policy': policy, 'security': security})
    return {'api': api, 'resolved': resolved, 'conflicts': conflicts,
            'authentication': authentication, 'identity': digest(api)}
