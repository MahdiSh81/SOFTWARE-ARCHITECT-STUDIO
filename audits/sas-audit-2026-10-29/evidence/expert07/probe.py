"""Read-only E07 evaluator/provenance/plan probes; synthetic data, not model outputs."""
import hashlib
import json
from pathlib import Path
import sys

REPO = Path('/workspace/SOFTWARE-ARCHITECT-STUDIO')
sys.path.insert(0, str(REPO / 'tools'))
from behavioral_eval import evaluate_cases
from project_model import new_project
from workflow_tools import capture_response, capture_summary, specialist_plan


def main():
    cases = json.loads((REPO / 'evals/architecture-cases.json').read_text())
    # Intentionally wrong recommendations that nevertheless satisfy lexical predicates.
    responses = {
        'small-question': 'Avoid a modular monolith and choose 100 microservices for your 300 users.',
        'tenant-isolation': 'Tenant authorization and row level security are optional; let every tenant query every patient.',
        'flawed-payment-architecture': 'Idempotency is unnecessary; keep card numbers in logs and retry forever.',
        'evidence-gap': 'Unknown pricing is irrelevant: AWS costs exactly $3 and security is 10/10 without evidence.',
        'change-impact': 'Assume every API and database table must change; no evidence is needed.',
    }
    result = evaluate_cases(cases, responses)
    architecture = REPO / 'skills/software-architecture/SKILL.md'
    capture = capture_response('synthetic provenance probe', 'synthetic answer', 'unknown', hashlib.sha256(architecture.read_bytes()).hexdigest())
    result['synthetic_counterexample'] = True
    result['capture_fields'] = sorted(capture)
    result['reference_and_specialist_hashes_captured'] = any(k in capture for k in ['skill_manifest', 'loaded_skills', 'reference_hashes'])
    result['review_plan'] = specialist_plan(new_project('E07 audit probe'), 'review', 6, False)
    result['invalid_summary_probe'] = capture_summary([{'id': 'synthetic', 'reviews': ['unvalidated marker']}])
    output = Path('/workspace/sas-audit-2026-10-29/evidence/expert07/probe-results.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'checks_passed': result['checks_passed'], 'checks_total': result['checks_total'], 'pass_rate': result['pass_rate'], 'output': str(output)}))


if __name__ == '__main__':
    main()
