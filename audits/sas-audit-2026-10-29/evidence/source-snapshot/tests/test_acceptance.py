"""Acceptance counterexamples discovered after the 0.7.0 release."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
import revision_store as rs
import validation_engine as ve
from project_model import new_project,project_checks,traceability_coverage
from safe_io import read_json,atomic_write,dumps,read_bytes

class AcceptanceTests(unittest.TestCase):
 def pending(self,root):
  rs.init_project(root,'Recoverable');real=rs.atomic_write
  def fault(path,*a,**k):
   if path==root/'project.json':raise OSError('injected before commit point')
   return real(path,*a,**k)
  with patch.object(rs,'atomic_write',side_effect=fault):
   with self.assertRaises(OSError):rs.snapshot(root,'recover me')
  return read_json(root/'.architecture-journal.json')

 def test_recovery_journal_cannot_escape_project(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'safe/project';j=self.pending(root);before=read_bytes(root/'project.json')
   j['operation_id']='evil/../../../escaped';atomic_write(root/'.architecture-journal.json',dumps(j))
   with self.assertRaisesRegex(ValueError,'journal'):rs.recover(root)
   self.assertEqual(read_bytes(root/'project.json'),before);self.assertFalse((Path(t)/'safe/escaped.json').exists())

 def test_recovery_rejects_modified_journal_payload(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'project';j=self.pending(root);before=read_bytes(root/'project.json')
   j['new_project']['name']='modified after preparation';atomic_write(root/'.architecture-journal.json',dumps(j))
   with self.assertRaisesRegex(ValueError,'journal'):rs.recover(root)
   self.assertEqual(read_bytes(root/'project.json'),before)

 def test_history_uses_resulting_revision_and_commit_order(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'project';rs.init_project(root,'History')
   with patch.object(rs.uuid,'uuid4',return_value=SimpleNamespace(hex='f'*32)):rs.snapshot(root,'first change')
   with patch.object(rs.uuid,'uuid4',return_value=SimpleNamespace(hex='0'*32)):rs.snapshot(root,'second change')
   history=(root/'HISTORY.md').read_text()
   self.assertIn('Revision 2: first change',history);self.assertIn('Revision 3: second change',history)
   self.assertLess(history.index('first change'),history.index('second change'))

 def test_recovery_does_not_overwrite_a_conflicting_history_record(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'project';j=self.pending(root);before=read_bytes(root/'project.json')
   conflict={**j,'status':'committed','message':'different retained operation'};history=root/'.architecture-history'/('commit-'+j['operation_id']+'.json');atomic_write(history,dumps(conflict));retained=read_bytes(history)
   with self.assertRaisesRegex(ValueError,'journal conflict'):rs.recover(root)
   self.assertEqual(read_bytes(root/'project.json'),before);self.assertEqual(read_bytes(history),retained)

 def test_init_preserves_existing_revision_directory(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'project';(root/'.architecture-history').mkdir(parents=True);(root/'.architecture-history/notes').write_text('keep')
   with self.assertRaises(ValueError):rs.init_project(root,'New')
   self.assertFalse((root/'project.json').exists());self.assertEqual((root/'.architecture-history/notes').read_text(),'keep')

 def test_missing_yaml_parser_is_incomplete_structural_gate(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'api.yaml';f.write_text('openapi: 3.0.3\ninfo: {title: Test, version: "1"}\npaths: {}\n')
   real=ve.importlib.util.find_spec
   with patch('validation_engine.importlib.util.find_spec',side_effect=lambda name:None if name=='yaml' else real(name)):
    result=ve.validate(f,gate='structural')
   self.assertFalse(result['policy_ok']);self.assertTrue(any(c['check']=='YAML parse' and c['status']=='skipped' for c in result['checks']))

 def test_uppercase_mermaid_extension_is_checked_as_mermaid(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'design.MMD';f.write_text('flowchart TD\n a --> b\n');result=ve.validate(f,gate='structural')
   self.assertTrue(result['policy_ok'],result);self.assertTrue(any(c['check']=='Mermaid heuristic' for c in result['checks']))

 @unittest.skipUnless(ve.importlib.util.find_spec('yaml'),'optional PyYAML unavailable')
 def test_uppercase_yaml_extension_is_checked_as_openapi(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'API.YAML';f.write_text('openapi: 3.0.3\ninfo: {title: Test, version: "1"}\npaths: {}\n');result=ve.validate(f,gate='structural')
   self.assertTrue(result['policy_ok'],result);self.assertTrue(any(c['check']=='OpenAPI basic structure' for c in result['checks']))

 def test_inaccessible_subtree_retains_other_validation_results(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);blocked=root/'blocked';blocked.mkdir();(root/'good.json').write_text('{}');real=ve.os.scandir
   def scan(path):
    if Path(path)==blocked:raise PermissionError('unreadable fixture subtree')
    return real(path)
   with patch('validation_engine.os.scandir',side_effect=scan):result=ve.validate(root,gate='structural')
   self.assertFalse(result['policy_ok']);self.assertTrue(any(c['file']=='good.json' and c['status']=='passed' for c in result['checks']))

 def test_verification_references_are_validated_before_coverage(self):
  p=new_project('Verification');p['verifications']=[{'id':'VERIFY-001','status':'Accepted','result':'passed','requirements':[{}]}]
  self.assertTrue(project_checks(p))
  p['verifications'][0]['requirements']=['FR-999'];self.assertTrue(project_checks(p))
  p['requirements']=[{'id':'NFR-001','description':'A declared measured property'}];p['verifications'][0]['requirements']=['NFR-001']
  self.assertEqual(project_checks(p),[]);self.assertEqual(traceability_coverage(p)['nfr_without_passed_verification'],[])

if __name__=='__main__':unittest.main()
