"""Typed, order-independent declared graph queries. Reachability is review scope."""
from collections import deque
from project_model import GROUPS,OPTIONAL,LINKS,require_project,traceability_coverage
from safe_io import digest

def graph(p):
    require_project(p)
    nodes={(g,r['id']):r for g in GROUPS+OPTIONAL for r in p.get(g,[])}
    edges=[]
    for group,targets in LINKS.items():
        for r in p.get(group,[]):
            for upstream in targets:
                for id in r.get(upstream,[]):
                    edges.append(((upstream,id),(group,r['id']),f'declared {upstream} association','DECLARED'))
    for e in p.get('relationships',[]):
        a=(e['from']['group'],e['from']['id']);b=(e['to']['group'],e['to']['id'])
        # A depends on/calls/uses B => a change in B makes A a review candidate.
        if e['kind'] in {'depends_on','calls','reads','writes','consumes','implements','verifies'}:a,b=b,a
        edges.append((a,b,e['kind']+':'+e['id'],e.get('evidence_status','DECLARED')))
    return nodes,sorted(edges)

def impacts_from_seeds(p, seeds):
    """Traverse typed records; every reached node is returned, including optional groups."""
    require_project(p)
    nodes, edges = graph(p)
    if not isinstance(seeds, list):
        raise ValueError('typed seeds must be an array')
    typed = set()
    for seed in seeds:
        if not isinstance(seed, dict) or not isinstance(seed.get('group'), str) or not isinstance(seed.get('id'), str):
            raise ValueError('seed must be typed {group,id}')
        key = (seed['group'], seed['id'])
        if key not in nodes:
            raise ValueError('Unknown impact seed: ' + str(key))
        typed.add(key)
    adjacency = {}
    for a, b, reason, status in edges:
        adjacency.setdefault(a, []).append((b, reason, status))
    witness = {key: [] for key in sorted(typed)}
    queue = deque(witness)
    while queue:
        current = queue.popleft()
        for target, reason, status in adjacency.get(current, []):
            if target not in witness:
                witness[target] = witness[current] + [{'from': {'group': current[0], 'id': current[1]}, 'to': {'group': target[0], 'id': target[1]}, 'relation': reason, 'evidence_status': status}]
                queue.append(target)
    affected = {g: [] for g in GROUPS + OPTIONAL}
    for key in sorted(witness):
        record = nodes[key]
        affected[key[0]].append({'id': key[1], 'name': record.get('name', record.get('title', key[1])), 'why': [step['relation'] for step in witness[key]], 'witness_path': witness[key], 'directly_changed': key in typed, 'status': 'review candidate; change not proven necessary'})
    return {'requirements': [key[1] for key in sorted(typed) if key[0] == 'requirements'], 'seeds': [{'group': key[0], 'id': key[1]} for key in sorted(typed)], 'seed_status': 'analyzed typed seeds' if typed else 'no changed record seeds', 'revision': p['revision'], 'source_hash': digest(p), 'affected': affected, 'unlinked_review_required': [group for group, records in affected.items() if not records], 'unreached_records': [{'group': group, 'id': identifier} for group, identifier in sorted(set(nodes) - set(witness))], 'traceability_coverage': {group: {'linked_affected': len(records), 'total': len(p.get(group, []))} for group, records in affected.items()}, 'caveat': 'Typed declared-link closure with connectivity witnesses, not semantic causality. Missing links and runtime effects require manual review.'}


def impacts(p, req_ids):
    """Compatibility wrapper for the original requirement-only CLI."""
    if isinstance(req_ids, str):
        req_ids = [req_ids]
    if not isinstance(req_ids, list) or any(not isinstance(x, str) for x in req_ids):
        raise ValueError('requirement IDs must be strings')
    known = {r['id'] for r in require_project(p)['requirements']}
    if set(req_ids) - known:
        raise ValueError('Unknown requirements: ' + ', '.join(sorted(set(req_ids) - known)))
    return impacts_from_seeds(p, [{'group': 'requirements', 'id': identifier} for identifier in req_ids])

def project_diff(before,after):
    require_project(before);require_project(after)
    result={}
    for g in GROUPS+OPTIONAL+('relationships',):
        a={r['id']:r for r in before.get(g,[])};b={r['id']:r for r in after.get(g,[])}
        result[g]={'added':sorted(b.keys()-a.keys()),'removed':sorted(a.keys()-b.keys()),
                   'changed':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])}
    result['metadata_changed']=sorted(k for k in set(before)|set(after) if k not in GROUPS+OPTIONAL+('relationships',) and before.get(k)!=after.get(k))
    return {'baseline_hash':digest(before),'proposed_hash':digest(after),'baseline_revision':before['revision'],'proposed_revision':after['revision'],'delta':result}

def change_bundle(before, after):
    delta = project_diff(before, after)
    requirement_delta = delta['delta']['requirements']
    ids = sorted(set(requirement_delta['added'] + requirement_delta['removed'] + requirement_delta['changed']))
    def seeds(project, baseline):
        result = set()
        for group in GROUPS + OPTIONAL:
            change = delta['delta'][group]
            names = change['changed'] + change['removed' if baseline else 'added']
            result.update((group, identifier) for identifier in names)
        # Changed relationships make their old/new endpoints review candidates.
        changes = delta['delta']['relationships']
        selected = set(changes['changed'] + changes['removed' if baseline else 'added'])
        for edge in project.get('relationships', []):
            if edge['id'] in selected:
                result.update((edge[side]['group'], edge[side]['id']) for side in ('from', 'to'))
        return [{'group': group, 'id': identifier} for group, identifier in sorted(result)]
    return {**delta, 'status': 'PROPOSED; not applied', 'changed_requirements': ids, 'baseline_impact': impacts_from_seeds(before, seeds(before, True)), 'proposed_impact': impacts_from_seeds(after, seeds(after, False)), 'review_obligations': ['API compatibility and consumers', 'data migration/retention/backups', 'authorization/privacy', 'NFR/cost assumptions', 'applicable validation and rollback/forward-fix'], 'apply_precondition': {'expected_hash': delta['baseline_hash']}, 'note': 'Accepted decisions are not automatically amended. All changed record kinds and relationship endpoints seed declared-link review.'}
