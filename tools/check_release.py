"""Run meaningful regression/conformance suites, writing an exact local report."""
import argparse,io,json,shutil,subprocess,sys,time,unittest
from pathlib import Path
from safe_io import atomic_write,dumps
from validation_engine import doctor
from project_model import VERSION

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--require-node',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];start=time.monotonic();stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(root/'tests'))
    r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    result={'toolkit_version':VERSION,'environment':doctor(),'python':{'run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'log':stream.getvalue()},'node':{'status':'skipped','reason':'Node not installed'},'claims':'Regression and code/DOM-model conformance; not live-model or user-study evidence.'}
    ok=r.wasSuccessful()
    if shutil.which('node'):
        node=subprocess.run(['node',str(root/'tests/test_workbench.cjs')],capture_output=True,text=True,timeout=15)
        result['node']={'status':'passed' if node.returncode==0 else 'failed','stdout':node.stdout,'stderr':node.stderr};ok=ok and node.returncode==0
    elif args.require_node:ok=False
    result.update(ok=ok,duration_seconds=round(time.monotonic()-start,6));atomic_write(args.output,dumps(result));print(dumps({k:result[k] for k in ('ok','duration_seconds','claims')}));return 0 if ok else 1
if __name__=='__main__':sys.exit(main())
