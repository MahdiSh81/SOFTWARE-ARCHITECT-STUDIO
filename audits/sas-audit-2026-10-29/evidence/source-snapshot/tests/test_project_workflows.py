import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from project_workflows import init_project,load_project,project_checks,snapshot,impacts,handoff,repo_scan
from architect_cli import validate
from behavioral_eval import evaluate_cases

SAMPLE=Path(__file__).resolve().parents[1]/'examples/atlas-project/project.json'

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.example=json.loads(SAMPLE.read_text())
    def test_links_valid(self):
        self.assertEqual(project_checks(self.example),[])
    def test_dangling_ids(self):
        self.example['tasks'][0]['components']=['not-real']
        self.assertIn('unknown components',str(project_checks(self.example)))
    def test_requirement_ids(self):
        self.example['requirements'][0]['id']='R-1'
        self.assertTrue(project_checks(self.example))
    def test_duplicate_rejected(self):
        self.example['components'].append(self.example['components'][0])
        self.assertTrue(project_checks(self.example))
    def test_project_context_version_and_snapshot(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            init_project(root,'My App')
            self.assertEqual(load_project(root)['revision'],1)
            s=snapshot(root,'Approved primary DB')
            self.assertTrue(Path(s['snapshot_file']).exists())
            self.assertEqual(load_project(root)['revision'],2)
            self.assertIn('Approved primary DB',(root/'HISTORY.md').read_text())
            with self.assertRaises(ValueError):snapshot(root,'')
    def test_impact_declared_links(self):
        result=impacts(self.example,['FR-001'])
        self.assertEqual({x['id'] for x in result['affected']['interfaces']},{'API-001','API-002'})
        self.assertEqual(result['affected']['decisions'][0]['id'],'ADR-001')
        self.assertEqual(result['affected']['tasks'][0]['id'],'TASK-001')
        self.assertIn('COST-001',[x['id'] for x in result['affected']['cost_drivers']])
        with self.assertRaises(ValueError):impacts(self.example,['FR-999'])
    def test_handoff_and_validators(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'project';root.mkdir()
            (root/'project.json').write_text(json.dumps(self.example))
            export=Path(t)/'handoff'
            report=handoff(root,export)
            self.assertIn('implementation-tasks.md',report['generated'])
            self.assertIn('adrs/ADR-001.md',report['generated'])
            self.assertIn('acceptance',(export/'implementation-tasks.md').read_text().lower())
            self.assertTrue(validate(export)['ok'],validate(export)['issues'])
            with self.assertRaises(ValueError):handoff(root,export)
    def test_repo_file_line_evidence_and_drift(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t); (base/'src').mkdir()
            (base/'src/app.py').write_text('from fastapi import FastAPI\napp = FastAPI()\n@app.get("/records")\ndef list_records(): pass\n')
            (base/'requirements.txt').write_text('fastapi\n')
            (base/'node_modules').mkdir();(base/'node_modules/noise.py').write_text('')
            scan=repo_scan(base,self.example)
            self.assertTrue(any(x['path']=='src/app.py' and x['line']==3 for x in scan['static_declarations']))
            self.assertEqual(len(scan['drift_candidates']),1)
            self.assertIn('database',[] if not scan['drift_candidates'] else [x['component'] for x in scan['drift_candidates']])
            self.assertFalse(any('node_modules' in x['path'] for x in scan['observed_files']))
    def test_validating_project_json_checks_links(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'project.json').write_text(json.dumps(self.example))
            r=validate(root)
            self.assertTrue(r['ok'])
            self.assertIn('Project traceability integrity',[x['check'] for x in r['checks_run']])
            self.example['decisions'][0]['requirements']=['FR-404']
            (root/'project.json').write_text(json.dumps(self.example))
            self.assertFalse(validate(root)['ok'])

class BehavioralTests(unittest.TestCase):
    def test_evaluate_and_baseline(self):
        cases={'cases':[{'id':'abc','checks':[{'id':'positive','any_of':['evidence']},{'id':'negative','none_of':['guaranteed']}]}]}
        result=evaluate_cases(cases,{'abc':'evidence supported'},{'abc':'guaranteed yes'})
        self.assertEqual(result['checks_passed'],2)
        self.assertEqual(result['baseline_checks_passed'],0)
        self.assertEqual(result['delta_percentage_points'],100)
    def test_missing_outputs_are_not_pass(self):
        cases={'cases':[{'id':'abc','checks':[{'id':'positive','any_of':['evidence']}]}]}
        r=evaluate_cases(cases,{})
        self.assertEqual(r['pass_rate'],0)
        self.assertEqual(r['cases'][0]['status'],'not supplied')
    def test_bad_regex_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_cases({'cases':[{'id':'a','checks':[{'any_of':['[']}]}]},{'a':'anything'})

if __name__=='__main__': unittest.main()
