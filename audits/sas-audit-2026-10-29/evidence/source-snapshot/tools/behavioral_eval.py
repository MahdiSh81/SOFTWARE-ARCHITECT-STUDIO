"""Bounded supplied-response checks. Semantic quality requires reviewed captures."""
from __future__ import annotations
import multiprocessing as mp,re,time

def _regex_worker(pattern,text,connection):
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    except (ImportError,ValueError):pass
    try:connection.send(bool(re.search(pattern,text,flags=re.I|re.M)))
    finally:connection.close()

def _pattern_found(pattern,text,timeout=.3):
    if not isinstance(pattern,str) or not pattern or len(pattern)>240:raise ValueError('nonempty pattern <=240 characters required')
    try:re.compile(pattern)
    except re.error as e:raise ValueError('Invalid regex: '+str(e)) from e
    ctx=mp.get_context('spawn');parent,child=ctx.Pipe(False)
    p=ctx.Process(target=_regex_worker,args=(pattern,text,child));p.start();child.close()
    try:
        if not parent.poll(timeout):raise TimeoutError('regex time budget exceeded')
        try:return parent.recv()
        except EOFError as e:raise RuntimeError('regex worker ended without a result') from e
    finally:
        if p.is_alive():p.terminate()
        p.join(timeout=1);parent.close()

def _check_fixture(cases,responses):
    if not isinstance(cases,dict) or not isinstance(cases.get('cases'),list) or not isinstance(responses,dict):raise ValueError('Expect cases array and response map')
    if not 1<=len(cases['cases'])<=50:raise ValueError('1–50 cases supported per bounded run')
    seen=set();total=0
    for case in cases['cases']:
        if not isinstance(case,dict) or not isinstance(case.get('id'),str) or case['id'] in seen:raise ValueError('unique string case id required')
        seen.add(case['id']);checks=case.get('checks')
        if not isinstance(checks,list) or not checks:raise ValueError('nonempty checks required')
        check_ids=set()
        for check in checks:
            total+=1
            if not isinstance(check,dict):raise ValueError('check object required')
            cid=check.get('id')
            if cid is not None and (not isinstance(cid,str) or cid in check_ids):raise ValueError('unique check ids required')
            if cid is not None:check_ids.add(cid)
            if not any(k in check for k in ('any_of','none_of','max_chars','max_words','max_sentences')):raise ValueError('check predicate required')
            for key in ('any_of','none_of'):
                if key in check:
                    v=check[key]
                    if not isinstance(v,list) or not v or len(v)>10:raise ValueError('nonempty bounded pattern array required')
                    for pattern in v:
                        if not isinstance(pattern,str) or not pattern or len(pattern)>240:raise ValueError('bounded nonempty pattern required')
                        try:re.compile(pattern)
                        except re.error as e:raise ValueError('Invalid regex: '+str(e)) from e
            for key in ('max_chars','max_words','max_sentences'):
                if key in check and (type(check[key]) is not int or check[key]<1):raise ValueError('positive constraint required')
    if total>200:raise ValueError('check budget exceeded')
    for response in responses.values():
        text=response.get('text') if isinstance(response,dict) else response
        if not isinstance(text,str) or len(text)>100_000:raise ValueError('response must be text <=100000 characters')

def _run(cases,responses,deadline=15):
    _check_fixture(cases,responses);start=time.monotonic();results=[];passed=0;total=0
    for case in cases['cases']:
        response=responses.get(case['id']);text=response.get('text') if isinstance(response,dict) else response;checks=[]
        for i,check in enumerate(case['checks']):
            total+=1;status='evaluated';positive=True;negative=True;ok=False
            if text is None:status='not supplied'
            elif time.monotonic()-start>deadline:status='not_run_due_to_budget'
            else:
                try:
                    def match(pattern):
                        remaining=deadline-(time.monotonic()-start)
                        if remaining<=0:raise TimeoutError('evaluation deadline')
                        return _pattern_found(pattern,text,min(.3,remaining))
                    positive=any(match(p) for p in check['any_of']) if 'any_of' in check else True
                    negative=not any(match(p) for p in check['none_of']) if 'none_of' in check else True
                    constraints=all(len(text)<=check[k] if k=='max_chars' else len(text.split())<=check[k] if k=='max_words' else len([s for s in re.split(r'[.!?؟]+(?:\s+|$)',text) if s.strip()])<=check[k] for k in ('max_chars','max_words','max_sentences') if k in check)
                    ok=positive and negative and constraints
                except TimeoutError:status='timed_out'
                except (OSError,RuntimeError):status='tool_error'
            passed+=int(ok);checks.append({'id':check.get('id',str(i)),'pass':ok,'status':status,'positive_match':positive,'forbidden_absent':negative})
        results.append({'id':case['id'],'status':'not supplied' if text is None else 'evaluated','checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)})
    return {'checks_passed':passed,'checks_total':total,'pass_rate':round(passed/total*100,2),'cases':results,
      'quality_status':'lexical/deterministic checks only; no semantic quality certification','limitations':'Supplied responses only. Real accuracy, safety and generalization require captured provenance and independent semantic review.'}

def evaluate_cases(cases,responses,baseline=None):
    current=_run(cases,responses)
    if baseline is not None:
        prior=_run(cases,baseline);current.update(baseline_pass_rate=prior['pass_rate'],delta_percentage_points=round(current['pass_rate']-prior['pass_rate'],2),baseline_checks_passed=prior['checks_passed'])
    return current
