"""Regression tests for the 0.8.0 audit follow-ups."""
import json, sys, tempfile, unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))

from artifact_compiler import compile_plan, handoff, resolve_generation
from project_model import VERSION
from revision_store import init_project, load_project, recover, snapshot
from safe_io import atomic_write, digest, dumps, read_bytes, read_json
from validation_engine import openapi_checks
from integration_contracts import validate_capability_manifest, validate_tool_result, validate_verification_receipt


def api_fixture():
    return {
        "openapi": "3.0.3",
        "info": {"title": "Reference validation fixture", "version": "1.0.0"},
        "paths": {"/pets/{petId}": {"get": {
            "operationId": "getPet",
            "parameters": [{"$ref": "#/components/parameters/PetId"}],
            "responses": {"200": {"$ref": "#/components/responses/Pet"}},
            "security": [{"BearerAuth": []}],
        }}},
        "components": {
            "parameters": {"PetId": {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}}},
            "responses": {"Pet": {"description": "A pet"}},
            "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
        },
    }


def valid_result():
    return {
        "operation_id": "op-001", "tool_id": "ci.runner", "tool_version": "1.2.3",
        "capability": "run-tests", "permission_class": "read",
        "input_source_hash": "a" * 64, "input_schema_version": 1,
        "started_at": "2026-10-29T10:00:00Z", "completed_at": "2026-10-29T10:00:01Z",
        "status": "passed", "output_hash": "b" * 64,
        "checks_run": ["unit"], "checks_not_run": [], "warnings": [], "errors": [], "limitations": [],
    }


class AuditFollowupTests(unittest.TestCase):
    def test_openapi_local_references_resolve_and_escaped_pointer_is_supported(self):
        api = api_fixture()
        api["components"]["responses"]["Pet/Compact"] = {"description": "Compact"}
        api["paths"]["/pets/{petId}"]["get"]["responses"] = {"200": {"$ref": "#/components/responses/Pet~1Compact"}}
        self.assertEqual(openapi_checks(api), [])

    def test_openapi_unresolved_local_reference_fails(self):
        api = api_fixture()
        api["paths"]["/pets/{petId}"]["get"]["responses"]["200"] = {"$ref": "#/components/responses/DoesNotExist"}
        self.assertTrue(any("unresolved/unsupported local reference" in issue for issue in openapi_checks(api)))

    def test_openapi_security_scheme_must_be_declared(self):
        api = api_fixture()
        api["paths"]["/pets/{petId}"]["get"]["security"] = [{"MissingAuth": []}]
        self.assertTrue(any("security scheme is not declared: MissingAuth" in issue for issue in openapi_checks(api)))

    def test_openapi_path_parameter_reference_is_resolved_semantically(self):
        api = api_fixture()
        api["components"]["parameters"]["PetId"] = {
            "name": "otherId", "in": "query", "required": False, "schema": {"type": "string"}
        }
        self.assertTrue(any("required path parameter missing or invalid: petId" in issue for issue in openapi_checks(api)))

    def test_openapi_external_and_nonstring_refs_are_rejected(self):
        api = api_fixture()
        api["components"]["schemas"] = {"Bad": {"$ref": "https://example.invalid/schema.json"}}
        self.assertTrue(any("external references blocked" in issue for issue in openapi_checks(api)))
        api["components"]["schemas"]["Bad"] = {"$ref": 17}
        self.assertTrue(any("$ref must be a string" in issue for issue in openapi_checks(api)))

    def test_committed_journal_mismatch_preserves_current_project_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            init_project(root, "Mismatch")
            snapshot(root, "committed baseline")
            history_before = read_bytes(root / "HISTORY.md")
            changed = load_project(root)
            changed["brief"] = "external writer changed canonical state"
            atomic_write(root / "project.json", dumps(changed))
            changed_bytes = read_bytes(root / "project.json")
            with self.assertRaisesRegex(ValueError, "committed journal/current project hash mismatch"):
                recover(root)
            self.assertEqual(read_bytes(root / "project.json"), changed_bytes)
            self.assertEqual(read_bytes(root / "HISTORY.md"), history_before)

    def test_handoff_identity_distinguishes_canonical_and_projection_hashes(self):
        fixture = json.loads((BASE / "tests/fixtures/rich-project.json").read_text())
        files, report = compile_plan(fixture)
        identity = report["identity"]
        self.assertEqual(identity["canonical_input_hash"], digest(fixture))
        self.assertEqual(identity["source_revision"], fixture["revision"])
        self.assertEqual(identity["generator_version"], VERSION)
        self.assertIn("architecture.md", identity["artifact_hashes"])
        self.assertEqual(identity["artifact_hashes"]["architecture.md"], digest(files["architecture.md"].encode("utf-8")))
        self.assertIn("handoff-report.json", report["generated"])
        self.assertNotEqual(identity["canonical_input_hash"], identity["projection_hash"])
        self.assertIn("redaction_report", identity)

    def test_handoff_generation_manifest_preserves_identity(self):
        fixture = json.loads((BASE / "tests/fixtures/rich-project.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            atomic_write(root / "project.json", dumps(fixture))
            out = Path(tmp) / "handoff"
            result = handoff(root, out)
            manifest = read_json(resolve_generation(out) / "generation-manifest.json")
            self.assertEqual(manifest["canonical_input_hash"], digest(fixture))
            self.assertEqual(manifest["projection_hash"], result["identity"]["projection_hash"])
            self.assertEqual(manifest["identity"]["canonical_input_hash"], digest(fixture))

    def test_capability_manifest_rejects_duplicate_operation_ids(self):
        manifest = {
            "schema_version": 1, "tool_id": "ci.runner", "tool_version": "1.0.0",
            "capabilities": [
                {"operation_id": "run-tests", "description": "Run tests", "permission_class": "read",
                 "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
                 "idempotent": True, "timeout_seconds": 60},
                {"operation_id": "run-tests", "description": "Duplicate", "permission_class": "read",
                 "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
                 "idempotent": True, "timeout_seconds": 60},
            ],
        }
        self.assertTrue(any("duplicate capability operation_id" in e for e in validate_capability_manifest(manifest)))

    def test_passed_tool_result_requires_output_identity_and_valid_time(self):
        self.assertEqual(validate_tool_result(valid_result()), [])
        result = valid_result()
        result.pop("output_hash")
        self.assertTrue(any("output_hash" in e for e in validate_tool_result(result)))
        result = valid_result()
        result["completed_at"] = "2026-10-29T09:59:00Z"
        self.assertTrue(any("completed_at" in e for e in validate_tool_result(result)))

    def test_deployment_receipt_requires_authorization_reference(self):
        receipt = valid_result()
        receipt.update(permission_class="deploy", authorization_reference="")
        self.assertTrue(any("authorization_reference" in e for e in validate_verification_receipt(receipt)))


if __name__ == "__main__":
    unittest.main()
