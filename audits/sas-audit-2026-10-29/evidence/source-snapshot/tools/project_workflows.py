"""Compatibility exports; canonical implementation lives in focused modules."""
from project_model import new_project,project_checks,traceability_coverage,require_project
from revision_store import init_project,load_project,snapshot,recover,commit_project,restore
from graph_engine import impacts
from artifact_compiler import handoff
from repository_evidence import repo_scan
from safe_io import read_json as _load_file
