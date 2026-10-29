---
name: security-review
description: Review concrete security risks and orchestrate only available, authorized security checks.
---
# Security Review
Identify assets, actors, trust boundaries, attack surfaces, and assumptions. Review authentication/authorization, tenant isolation, secrets, input handling, logging, retention, dependencies, and deployment configuration as applicable. Separate observed defects from plausible threats and unknowns. Run SAST/SCA/secret scans only when connected, authorized, and suitable. Prioritize by impact, exploitability, scope, and compensating controls. Provide evidence, preconditions, remediation, regression tests, checks not run, and residual risk.
Do not expose secrets, run unsafe production probes, or claim certification from structural checks. Tool availability is not authorization; a clean scan does not prove absence of vulnerabilities.
