"""Discriminating local adapter and output-boundary acceptance tests."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
import execution_adapter as adapter
import architect_cli
from integration_contracts import validate_capability_manifest, validate_tool_result
from project_model import new_project
from workflow_tools import sqlite_schema_check
from safe_io import read_json


class LocalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'app';self.root.mkdir()
        self.state=Path(self.tmp.name)/'state'
        (self.root/'calc.py').write_text('def double(x):\n    return x\n')
        (self.root/'test_calc.py').write_text('import unittest\nfrom calc import double\nclass TestMath(unittest.TestCase):\n def test_double(self): self.assertEqual(double(4),8)\n')
        self.policy={'schema_version':1,'root':str(self.root),'authorization_reference':'test-user-task',
                     'allow_write':True,'allowed_paths':['calc.py','test_calc.py'],
                     'allow_checks':True,'checks':{'unit':{'argv':[sys.executable,'-B','-m','unittest','discover'],
                                                        'timeout_seconds':10,'kind':'test','minimum_tests':1}}}
    def check(self,names=None,policy=None,op='checks-01'):
        return adapter.run_checks(self.root,names or ['unit'],policy or self.policy,
                                  expected_source_hash=adapter.inspect(self.root)['source_hash'],
                                  operation_id=op,state_root=self.state)
    def plan(self):
        return adapter.propose_change(self.root,[{'path':'calc.py','content':'def double(x):\n    return x * 2\n'},
            {'path':'test_calc.py','content':(self.root/'test_calc.py').read_text()+'\n# coherent consumer regression\n'}])
    def test_actual_multi_file_apply_test_and_reconcile(self):
        failed=self.check(op='before-check');self.assertEqual(failed['status'],'failed')
        plan=self.plan()
        result=adapter.apply_change(self.root,plan,self.policy,operation_id='apply-01',state_root=self.state)
        self.assertEqual(result['status'],'passed');self.assertEqual(len(result['observed_effects']),2)
        self.assertEqual(validate_tool_result(result),[])
        check=self.check();self.assertEqual(check['status'],'passed')
        self.assertEqual(check['details']['checks'][0]['tests_executed'],1)
        reconciled=adapter.reconcile(self.root,check,expected_operation='checks-01',
            expected_source_hash=check['input_source_hash'],required_checks=['unit'],state_root=self.state)
        self.assertEqual(reconciled['status'],'passed');self.assertFalse(reconciled['applied'])
        self.assertEqual(adapter.recover(self.root,'apply-01',state_root=self.state)['status'],'committed')
    def test_stale_source_and_path_escape_never_mutate(self):
        plan=self.plan();(self.root/'calc.py').write_text('later user edit\n')
        with self.assertRaisesRegex(ValueError,'source conflict'):
            adapter.apply_change(self.root,plan,self.policy,state_root=self.state)
        self.assertEqual((self.root/'calc.py').read_text(),'later user edit\n')
        for name in ('../outside.py','/outside.py','.git/config','__pycache__/x.py'):
            with self.assertRaises(ValueError):adapter.propose_change(self.root,[{'path':name,'content':'x'}])
    def test_apply_authorization_and_idempotency(self):
        plan=self.plan()
        bad={**self.policy,'allowed_paths':['different.py']}
        with self.assertRaises(ValueError):adapter.apply_change(self.root,plan,bad,state_root=self.state)
        first=adapter.apply_change(self.root,plan,self.policy,operation_id='repeat-01',state_root=self.state)
        self.assertEqual(adapter.apply_change(self.root,plan,self.policy,operation_id='repeat-01',state_root=self.state),first)
        (self.root/'calc.py').write_text('new user work\n')
        with self.assertRaisesRegex(ValueError,'already attempted'):
            adapter.apply_change(self.root,plan,self.policy,operation_id='repeat-01',state_root=self.state)
    def test_partial_apply_retains_exact_observed_effects(self):
        plan=self.plan();write=adapter.atomic_write
        def interrupted(path,data,*args,**kwargs):
            if Path(path)==self.root/'test_calc.py':raise OSError('simulated disk full')
            return write(path,data,*args,**kwargs)
        with patch.object(adapter,'atomic_write',side_effect=interrupted):
            result=adapter.apply_change(self.root,plan,self.policy,operation_id='partial-01',state_root=self.state)
        self.assertEqual(result['status'],'partial');self.assertEqual(result['observed_effects'],['calc.py'])
        self.assertEqual(adapter.recover(self.root,'partial-01',state_root=self.state)['status'],'partial')
    def test_timeout_unavailable_and_unapproved_checks(self):
        policy=copy.deepcopy(self.policy)
        policy['checks']['sleep']={'argv':[sys.executable,'-c','import time; time.sleep(5)'],'timeout_seconds':.1}
        self.assertEqual(self.check(['sleep'],policy,'timeout-01')['status'],'timed_out')
        policy['checks']['missing']={'argv':['/nonexistent/studio-runner'],'timeout_seconds':1}
        self.assertEqual(self.check(['missing'],policy,'missing-01')['status'],'blocked')
        with self.assertRaises(ValueError):self.check(['not-approved'])
        with self.assertRaises(ValueError):self.check(policy={**self.policy,'allow_checks':False})
    def test_fabricated_or_stale_receipt_cannot_reconcile(self):
        check=self.check()
        fake=copy.deepcopy(check);fake['status']='passed';fake['details']={'checks':[{'name':'unit','status':'passed'}]}
        from safe_io import digest
        fake['output_hash']=digest(fake['details'])
        result=adapter.reconcile(self.root,fake,expected_operation='checks-01',expected_source_hash=fake['input_source_hash'],required_checks=['unit'],state_root=self.state)
        self.assertEqual(result['status'],'blocked')
    def test_zero_test_run_is_not_passed_as_tests(self):
        policy=copy.deepcopy(self.policy)
        policy['checks']['unit']['argv']=[sys.executable,'-c','print("Ran 0 tests")']
        self.assertEqual(self.check(policy=policy)['status'],'failed')
    def test_skipped_tests_cannot_satisfy_required_execution_count(self):
        (self.root/'test_calc.py').write_text('import unittest\nclass TestMath(unittest.TestCase):\n @unittest.skip("fixture skipped")\n def test_skip(self): pass\n')
        result=self.check()
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['details']['checks'][0]['tests_executed'],0)
        self.assertEqual(result['details']['checks'][0]['tests_skipped'],1)
    def test_final_operation_record_failure_retains_observed_effects(self):
        plan=self.plan();write=adapter.atomic_write
        def interrupted(path,data,*args,**kwargs):
            if Path(path).name=='journal-failure.json' and '"receipt"' in data:
                raise OSError('record store full')
            return write(path,data,*args,**kwargs)
        with patch.object(adapter,'atomic_write',side_effect=interrupted):
            result=adapter.apply_change(self.root,plan,self.policy,operation_id='journal-failure',state_root=self.state)
        self.assertEqual(result['status'],'passed');self.assertEqual(result['receipt_status'],'failed')
        self.assertEqual(result['observed_effects'],['calc.py','test_calc.py'])
        self.assertEqual(adapter.recover(self.root,'journal-failure',state_root=self.state)['status'],'committed')
    def test_post_apply_observation_failure_keeps_partial_receipt(self):
        plan=self.plan();inspect=adapter.inspect;calls=[]
        def observe(root,*args,**kwargs):
            calls.append(root)
            if len(calls)>1:raise ValueError('observation budget exhausted')
            return inspect(root,*args,**kwargs)
        with patch.object(adapter,'inspect',side_effect=observe):
            receipt=adapter.apply_change(self.root,plan,self.policy,operation_id='observation-failure',state_root=self.state)
        self.assertEqual(receipt['status'],'partial');self.assertNotIn('output_source_hash',receipt)
        self.assertEqual(len(receipt['observed_effects']),2)
        self.assertEqual(adapter.recover(self.root,'observation-failure',state_root=self.state)['status'],'committed')
    def test_post_check_unobservable_source_is_partial_not_success(self):
        policy=copy.deepcopy(self.policy)
        policy['checks']['link']={'argv':[sys.executable,'-c','from pathlib import Path; Path("foreign-link").symlink_to("missing")'],'timeout_seconds':2}
        result=self.check(['link'],policy,'unobservable-check')
        self.assertEqual(result['status'],'partial');self.assertNotIn('output_source_hash',result)
        self.assertEqual(adapter.recover(self.root,'unobservable-check',state_root=self.state)['status'],'unknown')
    def test_aggregate_runtime_budget_rejected_before_checks(self):
        policy=copy.deepcopy(self.policy)
        policy['checks']['slow1']={'argv':[sys.executable,'-c','pass'],'timeout_seconds':100}
        policy['checks']['slow2']={'argv':[sys.executable,'-c','pass'],'timeout_seconds':100}
        with self.assertRaisesRegex(ValueError,'aggregate'):
            self.check(['slow1','slow2'],policy,'too-long')
        self.assertFalse((self.state/'too-long.json').exists())
    def test_contract_shapes_never_crash_and_null_output_rejected(self):
        manifest=adapter.capabilities();self.assertEqual(validate_capability_manifest(manifest),[])
        for value in ([],{},None,1):
            bad=copy.deepcopy(manifest);bad['capabilities'][0]['permission_class']=value
            self.assertTrue(validate_capability_manifest(bad))
            self.assertTrue(validate_tool_result({'status':value,'permission_class':value}))
        result=self.check();result['status']='passed';result['output_hash']=None
        self.assertTrue(validate_tool_result(result))
        bad=copy.deepcopy(manifest);bad['capabilities'][0]['input_schema']={'type':42}
        self.assertTrue(validate_capability_manifest(bad))
    def test_sqlite_errors_are_domain_errors(self):
        p=new_project('duplicate tables');p['data_models']=[{'id':'DATA-001','dialect':'sqlite','table':'same','columns':[{'name':'id','type':'INTEGER'}]},
            {'id':'DATA-002','dialect':'sqlite','table':'same','columns':[{'name':'id','type':'INTEGER'}]}]
        with self.assertRaises(ValueError):sqlite_schema_check(p)


class ReceiptTests(unittest.TestCase):
    def test_no_clobber_receipt_precedes_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);receipt=base/'source.py';receipt.write_text('preserve me')
            with contextlib.redirect_stderr(io.StringIO()):
                code=architect_cli.main(['--receipt',str(receipt),'init',str(base/'project'),'--name','New'])
            self.assertEqual(code,2);self.assertFalse((base/'project').exists());self.assertEqual(receipt.read_text(),'preserve me')
    def test_failed_gate_and_input_error_summaries_keep_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);bad=base/'api.json';bad.write_text('{')
            with contextlib.redirect_stdout(io.StringIO()):
                code=architect_cli.main(['--receipt',str(base/'gate.json'),'validate',str(bad),'--gate','structural'])
            receipt=read_json(base/'gate.json');self.assertEqual(code,1);self.assertEqual(receipt['exit_code'],1)
            self.assertFalse(receipt['policy_ok']);self.assertEqual(receipt['status'],'failed')
            with contextlib.redirect_stderr(io.StringIO()):
                code=architect_cli.main(['--receipt',str(base/'error.json'),'resume',str(base/'missing')])
            self.assertEqual(code,2);self.assertEqual(read_json(base/'error.json')['error_code'],'INPUT_OR_OPERATION_ERROR')
    def test_postcommit_receipt_error_preserves_successful_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);output=io.StringIO()
            with patch.object(architect_cli,'record_run',side_effect=OSError('receipt disk full')),contextlib.redirect_stdout(output):
                code=architect_cli.main(['--receipt',str(base/'receipt.json'),'init',str(base/'project'),'--name','Committed'])
            self.assertEqual(code,3);self.assertTrue((base/'project/project.json').is_file())
            self.assertEqual(json.loads(output.getvalue())['receipt_status'],'failed')

if __name__=='__main__':unittest.main()
