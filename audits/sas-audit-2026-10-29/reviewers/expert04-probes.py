"""Read-only imports of audit target; all fixtures and output are outside checkout."""
import copy, json, os, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, '/workspace/SOFTWARE-ARCHITECT-STUDIO/tools')
from repository_evidence import repo_scan, fitness, evidence_delta
from graph_engine import impacts, change_bundle
from workflow_tools import freshness, migration_plan
from project_model import new_project, require_project
from safe_io import digest

OUT=Path('/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence')
FIX=OUT/'fixtures';FIX.mkdir(exist_ok=True)
results={}
def save(name, value):
    (OUT/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    return value
def scan_case(name, files, **kwargs):
    root=FIX/name;root.mkdir(exist_ok=True)
    for name2,text in files.items():
        file=root/name2;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(text)
    return save(name+'-scan',repo_scan(root,**kwargs))
def rule(path,target):
    p=new_project('probe')
    p['fitness_rules']=[{'id':'RULE-001','kind':'forbid_import','source_prefix':path,'target_prefix':target}]
    return p

# A cold parser failure must remain visible after a cache hit.
root=FIX/'parse-cache';root.mkdir(exist_ok=True)
(root/'broken.py').write_text('import forbidden\nthis is invalid Python !!!\n')
cache=OUT/'parse-cache.json'
cache.unlink(missing_ok=True)
cold=save('parse-cache-cold',repo_scan(root,cache=cache))
warm=save('parse-cache-warm',repo_scan(root,cache=cache))
results['parser_cache']={'cold_coverage':cold['coverage'],'cold_omissions':cold['omissions'],
    'warm_coverage':warm['coverage'],'warm_omissions':warm['omissions'],'warm_observed':warm['observed_files'],
    'fitness_cold':fitness(rule('broken.py','forbidden'),cold),'fitness_warm':fitness(rule('broken.py','forbidden'),warm)}

# Successful byte reads do not establish that a language adapter inspected imports.
go=scan_case('go-fitness',{'main.go':'package main\nimport "forbidden/secret"\nfunc main() {}\n'})
results['unsupported_language_fitness']=fitness(rule('main.go','forbidden'),go)
save('go-fitness',results['unsupported_language_fitness'])

# Preserve relative import syntax; an empty target cannot support forbid-import checks.
rel=scan_case('relative-python',{'pkg/consumer.py':'from . import forbidden\n','pkg/forbidden.py':''})
results['relative_python_fitness']=fitness(rule('pkg/consumer.py','forbidden'),rel)

# Descriptor edges can exceed the edge quota without exceeding declaration quota.
jobs={'consumer':{'needs':['job'+str(n) for n in range(100)]+['forbidden']}}
quota=scan_case('edge-quota',{'ci.json':json.dumps({'jobs':jobs})})
results['silent_edge_quota']={'edge_count':len(quota['dependency_edges']),'coverage':quota['coverage'],
    'omissions':quota['omissions'],'fitness':fitness(rule('ci.json','forbidden'),quota)}
importquota=scan_case('import-quota',{'a.py':'import os\n'*100+'import forbidden\n'})
results['import_quota_fitness']={'omissions':importquota['omissions'],'fitness':fitness(rule('a.py','forbidden'),importquota)}

# Token scanning must not turn an earlier non-module export into another import.
js=scan_case('js-bleed',{'a.ts':'export const marker = 1\nimport x from "forbidden";\n'})
results['javascript_declaration_bleed']={'declarations':js['static_declarations'],'edges':js['dependency_edges']}

# Manifest parse failures and listed non-JSON manifests have no terminal status.
descriptor=scan_case('invalid-descriptors',{'package.json':'{"dependencies": {broken',
    'pyproject.toml':'[project]\ndependencies = ["forbidden>=1"]\n',
    'requirements.txt':'forbidden==1.0\n'})
results['descriptor_failures']={'coverage':descriptor['coverage'],'omissions':descriptor['omissions'],
    'observed_files':descriptor['observed_files'],'declarations':descriptor['static_declarations'],
    'fitness':fitness(rule('package.json','forbidden'),descriptor)}

# Prefix semantics currently match sibling paths and unrelated package names.
prefix=scan_case('prefix-boundaries',{'src2/a.py':'import forbiddenly\n'})
results['fitness_prefix_boundaries']=fitness(rule('src','forbidden'),prefix)

# The evidence-delta API does not reject untyped JSON or unrelated repo identity.
a=scan_case('delta-a',{'a.py':'import a\n'})
b=scan_case('delta-b',{'a.py':'import b\n'})
results['unrelated_delta']=evidence_delta(a,b)
results['invalid_delta']=evidence_delta({}, {})
save('unrelated-delta',results['unrelated_delta'])
save('invalid-delta',results['invalid_delta'])

# Graph closure works for linked requirements, but change_bundle seeds requirements only.
p=new_project('change probe')
p['requirements']=[{'id':'FR-001','description':'Read a record'}]
p['components']=[{'id':'api','requirements':['FR-001']}]
p['interfaces']=[{'id':'API-001','requirements':['FR-001'],'components':['api'],'path':'/records','method':'GET'}]
p['tasks']=[{'id':'TASK-001','interfaces':['API-001']}]
p['verifications']=[{'id':'VER-001','requirements':['FR-001'],'status':'Accepted','result':'passed'}]
require_project(p)
q=copy.deepcopy(p);q['interfaces'][0]['path']='/records/v2'
bundle=save('interface-only-change',change_bundle(p,q))
results['interface_only_change']={'changed_interfaces':bundle['delta']['interfaces'],'changed_requirements':bundle['changed_requirements'],
    'baseline_affected':bundle['baseline_impact']['affected'],'proposed_affected':bundle['proposed_impact']['affected']}
res=save('optional-graph-impact',impacts(p,['FR-001']))
results['optional_graph_records']={'affected_groups':list(res['affected']),
    'verification_reported_in_affected':any(v.get('id')=='VER-001' for records in res['affected'].values() for v in records),
    'verification_reported_unreached':{'group':'verifications','id':'VER-001'} in res['unreached_records']}

# Freshness preserves missing hashes as unknown and detects actual content change.
p2=new_project('freshness probe');p2['evidence']=[{'id':'EVID-001','path':'a.py','sha256':a['observed_files'][0]['sha256']},
    {'id':'EVID-002','path':'missing.py','sha256':'0'*64}]
results['freshness_stale_and_unknown']=save('freshness-stale-and-unknown',freshness(p2,b))
results['migration_plan']=save('migration-plan',migration_plan(p))

# Symlinks and special files must be omitted without executing any inspected code.
root=FIX/'io-safety';root.mkdir(exist_ok=True)
(root/'safe.py').write_text('raise RuntimeError("must not be executed")\n')
link=root/'link.py'
if not link.exists():link.symlink_to(root/'safe.py')
fifo=root/'blocked.py'
if not fifo.exists():os.mkfifo(fifo)
results['io_safety']=save('io-safety-scan',repo_scan(root))

# The declaration output quota is applied after extracting/caching every item.
root=FIX/'large-declarations';root.mkdir(exist_ok=True)
(root/'a.py').write_text('import a\n'*20000)
budget={}
largecache=OUT/'large-declarations-cache.json';largecache.unlink(missing_ok=True)
for name,kwargs in [('no_cache',{}),('cache',{'cache':largecache}),('short_deadline',{'deadline':.01})]:
    started=time.monotonic()
    try:
        scanned=repo_scan(root,**kwargs)
        budget[name]={'status':'completed','elapsed_seconds':time.monotonic()-started,
            'scanned_count':scanned['scanned_count'],'declarations':len(scanned['static_declarations']),
            'omissions':scanned['omissions'],'stop_reasons':scanned['stop_reasons']}
    except Exception as error:
        budget[name]={'status':'error','elapsed_seconds':time.monotonic()-started,
            'type':type(error).__name__,'message':str(error)}
results['large_declaration_budget']=save('large-declaration-probe',budget)

save('probe-results',results)
summary={k:v for k,v in results.items() if k not in ('migration_plan','io_safety')}
print(json.dumps(summary,indent=2))
