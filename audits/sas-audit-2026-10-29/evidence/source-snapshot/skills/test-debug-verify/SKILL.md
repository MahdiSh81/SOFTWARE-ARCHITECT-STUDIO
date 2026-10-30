---
name: test-debug-verify
description: Diagnose failures, design regression tests, and report evidence-backed verification status.
---
# Test, Debug, Verify
Establish expected behavior, observed symptom, source identity, environment, versions, and reproduction. Separate facts from hypotheses and identify the smallest discriminating test. Add/select a regression test; apply a minimal fix only when authorized and an actual editor exists. Run targeted tests, then relevant regression/build/security checks. Capture commands, source hash/commit, versions, status, logs/artifacts, and skipped checks. Reconcile results with acceptance criteria and residual uncertainty.
Use passed, failed, blocked, timed_out, skipped, partial, or unknown. A required skipped check is not green. One unit test does not establish runtime or production behavior. "Fixed" requires evidence the regression no longer occurs. Never fabricate logs or test output.
