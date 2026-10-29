"""Finite scenario arithmetic. Prices are user assumptions, not vendor quotes."""
import math
DIMENSIONS={'security':25,'reliability':20,'scalability':15,'maintainability':15,'observability':15,'cost':10}

def number(data,key,minimum=0,integer=False):
    v=data.get(key)
    try:valid=not isinstance(v,bool) and isinstance(v,(int,float)) and math.isfinite(v) and v>=minimum and (not integer or int(v)==v)
    except (OverflowError,ValueError):valid=False
    if not valid:raise ValueError(key+': finite '+('integer ' if integer else '')+'number >= '+str(minimum)+' required')
    return v

def capacity(data):
    if not isinstance(data,dict):raise ValueError('capacity object required')
    daily=number(data,'daily_requests',integer=True);peak=number(data,'peak_factor',1)
    payload=number(data,'average_payload_kib' if 'average_payload_kib' in data else 'average_payload_kb')
    records=number(data,'records_per_day',integer=True);size=number(data,'average_record_bytes');days=number(data,'retention_days',integer=True)
    overhead=number(data,'storage_overhead_multiplier',1);replicas=number(data,'replica_count',1,True);hours=number(data,'monthly_compute_hours')
    try:
        logical=records*size*days/1e9;physical=logical*overhead*replicas;network=daily*payload*1024*30
        raw={'average_qps':daily/86400,'peak_qps':daily*peak/86400,'logical_retained_gb':logical,'physical_storage_gb':physical,'monthly_network_gib':network/(1024**3),'monthly_network_gb':network/1e9}
        prices=['assumed_compute_price_per_hour','assumed_storage_price_per_gb_month','assumed_egress_price_per_gb']
        cost=None
        if all(data.get(k) is not None for k in prices):
            cp,sp,ep=[number(data,k) for k in prices];cost=hours*cp+physical*sp+network/1e9*ep
        if any(not math.isfinite(v) for v in raw.values()) or cost is not None and not math.isfinite(cost):raise ValueError('derived capacity/cost overflow')
    except OverflowError as e:raise ValueError('derived capacity/cost overflow') from e
    return {**{k:round(v,4) for k,v in raw.items()},'monthly_cost':round(cost,2) if cost is not None else None,
      'units':{'payload':'KiB (legacy average_payload_kb alias)','storage':'decimal GB','network':'GiB and decimal GB; egress price per decimal GB','currency':data.get('currency','USD')},
      'cost_coverage':'partial scenario using user-assumed prices; not a vendor quote' if cost is not None else 'not calculated: missing assumed unit prices',
      'omissions':['managed-service premiums','ingress/region transfer','gateway/NAT/LB','logs','backups','support','tax','engineering'],
      'notes':['Unrounded intermediate values used; only output is rounded.','One-way traffic is not necessarily billable egress.','Replication may already be included in provider pricing.']}

def score(data):
    if not isinstance(data,dict) or not isinstance(data.get('scores',{}),dict):raise ValueError('score object required')
    weights=data.get('weights',DIMENSIONS);ratings=data.get('scores',{})
    if not isinstance(weights,dict) or set(weights)!=set(DIMENSIONS):raise ValueError('weights must contain all six dimensions')
    for k in weights:number(weights,k)
    if abs(sum(weights.values())-100)>1e-9:raise ValueError('weights must sum to 100')
    if set(ratings)-set(DIMENSIONS):raise ValueError('unknown dimension')
    weighted=coverage=0
    for k,w in weights.items():
        r=ratings.get(k)
        if r is None:continue
        if type(r) is not int or not 0<=r<=4:raise ValueError('scores must be integer 0–4 or null')
        weighted+=w*r/4;coverage+=w
    return {'scores':{k:ratings.get(k) for k in DIMENSIONS},'weights':weights,'evaluated_weight_percent':round(coverage,2),
       'score_percent':round(weighted/coverage*100,2) if coverage else None,'status':'not evaluated' if not coverage else 'provisional — low evidence coverage' if coverage<60 else 'evidence-qualified (not a certification)',
       'unevaluated':[k for k in DIMENSIONS if ratings.get(k) is None],'evidence':data.get('evidence',{}),'note':'Ratings are source-attributed judgments; a high selected rating is not independent verification.'}
