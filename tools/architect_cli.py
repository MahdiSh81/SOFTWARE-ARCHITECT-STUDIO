#!/usr/bin/env python3
"""Software Architect Studio: bounded local architecture workflows, v0.7."""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
from calculators import capacity,score
from safe_io import read_json,read_text,dumps,digest,atomic_write
from project_model import project_checks,traceability_coverage,require_project,resume_packet,supersede,VERSION
from revision_store import init_project,load_project,snapshot,recover,commit_project,restore
from graph_engine import impacts,project_diff,change_bundle
from artifact_compiler import handoff,readiness,recover_handoff
from repository_evidence import repo_scan,evidence_delta,fitness
from validation_engine import validate,mermaid_checks,openapi_checks,doctor
from workflow_tools import freshness,migration_plan,decision_experiments,sensitivity,sqlite_schema_check,research_kit,capture_response,capture_summary,specialist_plan,record_run

def validate_mermaid(path):return mermaid_checks(read_text(path))
def _validate_openapi_json(path):return openapi_checks(read_json(path))
def _validate_openapi(path):
    try:
        import yaml
    except ImportError:return ['YAML parser unavailable']
    return openapi_checks(yaml.safe_load(read_text(path)))
def _project(path):return load_project(path) if path.is_dir() else require_project(read_json(path))

def main(argv=None):
    parser=argparse.ArgumentParser(description='Versioned, evidence-aware local architecture toolkit. No network installs, model calls or repository execution.')
    parser.add_argument('--receipt',type=Path,help='Explicit local minimized run receipt (no raw prompts/source)')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Report installed tools and enforcement limits')
    for cmd in ('capacity','score'):
        s=sub.add_parser(cmd);s.add_argument('--input',type=Path,required=True)
    s=sub.add_parser('init');s.add_argument('path',type=Path);s.add_argument('--name',required=True)
    s=sub.add_parser('snapshot');s.add_argument('path',type=Path);s.add_argument('--message',required=True)
    for cmd in ('resume','recover','readiness','experiments','migration-plan','data-check'):
        s=sub.add_parser(cmd);s.add_argument('path',type=Path)
        if cmd=='readiness':s.add_argument('--profile',choices=['brief','draft','review-ready'],default='draft')
    s=sub.add_parser('restore');s.add_argument('path',type=Path);s.add_argument('--revision',type=int,required=True);s.add_argument('--expected-hash',required=True);s.add_argument('--message',required=True)
    s=sub.add_parser('commit');s.add_argument('path',type=Path);s.add_argument('--proposed',type=Path,required=True);s.add_argument('--expected-hash',required=True);s.add_argument('--message',required=True)
    s=sub.add_parser('impact');s.add_argument('path',type=Path);s.add_argument('--requirement',action='append',required=True)
    for cmd in ('diff','change'):
        s=sub.add_parser(cmd);s.add_argument('--baseline',type=Path,required=True);s.add_argument('--proposed',type=Path,required=True)
    s=sub.add_parser('handoff');s.add_argument('path',type=Path);s.add_argument('--output',type=Path,required=True);s.add_argument('--overwrite',action='store_true');s.add_argument('--profile',choices=['brief','draft','review-ready'],default='draft');s.add_argument('--include-private',action='store_true',help='Include opaque fields and private canonical backup; review before sharing');s.add_argument('--dry-run',action='store_true')
    s=sub.add_parser('handoff-recover');s.add_argument('path',type=Path)
    s=sub.add_parser('validate');s.add_argument('path',type=Path);s.add_argument('--render',action='store_true');s.add_argument('--full-openapi',action='store_true');s.add_argument('--gate',choices=['report','structural','full'],default='structural');s.add_argument('--max-files',type=int,default=500);s.add_argument('--max-bytes',type=int,default=10_000_000);s.add_argument('--deadline',type=float,default=15)
    s=sub.add_parser('repo-scan');s.add_argument('path',type=Path);s.add_argument('--project',type=Path);s.add_argument('--limit',type=int,default=400);s.add_argument('--max-entries',type=int,default=10000);s.add_argument('--max-bytes',type=int,default=10_000_000);s.add_argument('--deadline',type=float,default=5);s.add_argument('--snippets',action='store_true');s.add_argument('--cache',type=Path)
    s=sub.add_parser('evidence-delta');s.add_argument('--baseline',type=Path,required=True);s.add_argument('--current',type=Path,required=True)
    for cmd in ('fitness','freshness'):
        s=sub.add_parser(cmd);s.add_argument('path',type=Path);s.add_argument('--scan',type=Path,required=True)
    s=sub.add_parser('evaluate');s.add_argument('--cases',type=Path,required=True);s.add_argument('--responses',type=Path,required=True);s.add_argument('--baseline',type=Path);s.add_argument('--gate',action='store_true');s.add_argument('--min-pass',type=float,default=100)
    s=sub.add_parser('capture');s.add_argument('--prompt',type=Path,required=True);s.add_argument('--response',type=Path,required=True);s.add_argument('--model',required=True);s.add_argument('--source-hash');s.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('quality-summary');s.add_argument('--captures',type=Path,required=True)
    s=sub.add_parser('sensitivity');s.add_argument('--input',type=Path,required=True);s.add_argument('--ranges',type=Path,required=True)
    s=sub.add_parser('review-plan');s.add_argument('path',type=Path);s.add_argument('--task',default='review');s.add_argument('--max-agents',type=int,default=3);s.add_argument('--host-delegation',action='store_true')
    sub.add_parser('research-kit',help='Export research protocol; does not interview users')
    args=parser.parse_args(argv);start=time.monotonic();code=0
    try:
        c=args.command
        if c=='doctor':result=doctor()
        elif c=='capacity':result=capacity(read_json(args.input))
        elif c=='score':result=score(read_json(args.input))
        elif c=='init':result=init_project(args.path,args.name)
        elif c=='snapshot':result=snapshot(args.path,args.message)
        elif c=='recover':result=recover(args.path)
        elif c=='restore':result=restore(args.path,args.revision,args.expected_hash,args.message)
        elif c=='commit':result=commit_project(args.path,_project(args.proposed),args.message,args.expected_hash)
        elif c=='resume':result=resume_packet(_project(args.path))
        elif c=='impact':result=impacts(_project(args.path),args.requirement)
        elif c=='diff':result=project_diff(_project(args.baseline),_project(args.proposed))
        elif c=='change':result=change_bundle(_project(args.baseline),_project(args.proposed))
        elif c=='readiness':result=readiness(_project(args.path),args.profile)
        elif c=='handoff':
            result=handoff(args.path,args.output,args.overwrite,profile=args.profile,include_private=args.include_private,dry_run=args.dry_run)
            if args.profile=='review-ready' and not result['readiness']['profile_satisfied']:code=1
        elif c=='handoff-recover':result=recover_handoff(args.path)
        elif c=='validate':
            result=validate(args.path,args.render,full_openapi=args.full_openapi,gate=args.gate,max_files=args.max_files,max_bytes=args.max_bytes,deadline=args.deadline)
            if args.gate!='report' and not result['policy_ok']:code=1
        elif c=='repo-scan':result=repo_scan(args.path,_project(args.project) if args.project else None,args.limit,max_entries=args.max_entries,max_bytes=args.max_bytes,deadline=args.deadline,include_snippets=args.snippets,cache=args.cache)
        elif c=='evidence-delta':result=evidence_delta(read_json(args.baseline),read_json(args.current))
        elif c=='fitness':result=fitness(_project(args.path),read_json(args.scan))
        elif c=='freshness':result=freshness(_project(args.path),read_json(args.scan))
        elif c=='evaluate':
            from behavioral_eval import evaluate_cases
            if not 0<=args.min_pass<=100:raise ValueError('min-pass must be 0–100')
            result=evaluate_cases(read_json(args.cases),read_json(args.responses),read_json(args.baseline) if args.baseline else None)
            if args.gate and (result['pass_rate']<args.min_pass or any(x['status']!='evaluated' for r in result['cases'] for x in r['checks'])):code=1
            result['gate']='enforced lexical/constraint threshold' if args.gate else 'report only'
        elif c=='experiments':result=decision_experiments(_project(args.path))
        elif c=='migration-plan':result=migration_plan(_project(args.path))
        elif c=='data-check':result=sqlite_schema_check(_project(args.path))
        elif c=='sensitivity':result=sensitivity(read_json(args.input),read_json(args.ranges))
        elif c=='review-plan':result=specialist_plan(_project(args.path),args.task,args.max_agents,args.host_delegation)
        elif c=='research-kit':result=research_kit()
        elif c=='capture':
            skill=Path(__file__).resolve().parents[1]/'skills/software-architecture/SKILL.md'
            result=capture_response(read_text(args.prompt),read_text(args.response),args.model,digest(skill.read_bytes()),args.source_hash);atomic_write(args.output,dumps(result),exclusive=True)
        elif c=='quality-summary':result=capture_summary(read_json(args.captures))
        else:raise ValueError('unhandled command')
        if args.receipt:record_run(args.receipt,c,result,time.monotonic()-start)
        print(dumps(result),end='');return code
    except (ValueError,FileNotFoundError,OSError,TypeError,KeyError,AttributeError,RecursionError,UnicodeError) as e:
        print(dumps({'error':{'code':'INPUT_OR_OPERATION_ERROR','type':type(e).__name__,'message':str(e)[:2500]},'command':args.command,'toolkit_version':VERSION}),file=sys.stderr,end='');return 2

if __name__=='__main__':sys.exit(main())
