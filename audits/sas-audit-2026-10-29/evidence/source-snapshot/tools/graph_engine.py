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

def impacts(p,req_ids):
    require_project(p)
    if isinstance(req_ids,str):req_ids=[req_ids]
    if not isinstance(req_ids,list) or any(not isinstance(x,str) for x in req_ids):raise ValueError('requirement IDs must be strings')
    known={r['id'] for r in p['requirements']}
    if set(req_ids)-known:raise ValueError('Unknown requirements: '+', '.join(sorted(set(req_ids)-known)))
    nodes,edges=graph(p);adj={}
    for a,b,why,status in edges:adj.setdefault(a,[]).append((b,why,status))
    witness={('requirements',id):[] for id in sorted(set(req_ids))};queue=deque(witness)
    while queue:
        a=queue.popleft()
        for b,why,status in adj.get(a,[]):
            if b not in witness:
                witness[b]=witness[a]+[{'from':{'group':a[0],'id':a[1]},'to':{'group':b[0],'id':b[1]},'relation':why,'evidence_status':status}];queue.append(b)
    affected={g:[] for g in GROUPS if g!='requirements'}
    for key in sorted(witness):
        if key[0] in affected:
            r=nodes[key];affected[key[0]].append({'id':key[1],'name':r.get('name',r.get('title',key[1])),
              'why':[x['relation'] for x in witness[key]],'witness_path':witness[key],'status':'review candidate; change not proven necessary'})
    return {'requirements':req_ids,'revision':p['revision'],'source_hash':digest(p),'affected':affected,
      'unlinked_review_required':[g for g,items in affected.items() if not items],
      'unreached_records':[{'group':g,'id':i} for g,i in sorted(set(nodes)-set(witness))],
      'traceability_coverage':{g:{'linked_affected':len(v),'total':len(p[g])} for g,v in affected.items()},
      'caveat':'Typed declared-link closure with connectivity witnesses, not semantic causality. Missing links and runtime effects require manual review.'}

def project_diff(before,after):
    require_project(before);require_project(after)
    result={}
    for g in GROUPS+OPTIONAL+('relationships',):
        a={r['id']:r for r in before.get(g,[])};b={r['id']:r for r in after.get(g,[])}
        result[g]={'added':sorted(b.keys()-a.keys()),'removed':sorted(a.keys()-b.keys()),
                   'changed':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])}
    result['metadata_changed']=sorted(k for k in set(before)|set(after) if k not in GROUPS+OPTIONAL+('relationships',) and before.get(k)!=after.get(k))
    return {'baseline_hash':digest(before),'proposed_hash':digest(after),'baseline_revision':before['revision'],'proposed_revision':after['revision'],'delta':result}

def change_bundle(before,after):
    d=project_diff(before,after);r=d['delta']['requirements'];ids=sorted(set(r['added']+r['removed']+r['changed']))
    return {**d,'status':'PROPOSED; not applied','changed_requirements':ids,
      'baseline_impact':impacts(before,[i for i in ids if i in {r['id'] for r in before['requirements']}]),
      'proposed_impact':impacts(after,[i for i in ids if i in {r['id'] for r in after['requirements']}]),
      'review_obligations':['API compatibility and consumers','data migration/retention/backups','authorization/privacy','NFR/cost assumptions','applicable validation and rollback/forward-fix'],
      'apply_precondition':{'expected_hash':d['baseline_hash']},'note':'Accepted decisions are not automatically amended. Review the semantic delta before an explicitly requested commit.'}
