"""Conservative data minimization; pattern detection is never a completeness claim."""
import re
SECRET_KEYS={'password','secret','token','api_key','apikey','authorization','credential','access_token','refresh_token'}
def redact_text(text):
    text=re.sub(r'(?i)TEST_ONLY_(?:SECRET|TOKEN|CREDENTIAL)[A-Z0-9_]*','[REDACTED_TEST_MARKER]',text)
    return re.sub(r'(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s\"\',;)]+',r'\1[REDACTED]',text)
def minimized(value,path='',changes=None):
    changes=[] if changes is None else changes
    if isinstance(value,dict):
        out={}
        for k,v in value.items():
            loc=path+'/'+k
            if k.lower() in SECRET_KEYS and isinstance(v,(str,int,float)) and v!='':out[k]='[REDACTED]';changes.append(loc)
            else:out[k]=minimized(v,loc,changes)
        return out
    if isinstance(value,list):return [minimized(x,path+'/'+str(i),changes) for i,x in enumerate(value)]
    if isinstance(value,str):
        out=redact_text(value)
        if out!=value:changes.append(path)
        return out
    return value
