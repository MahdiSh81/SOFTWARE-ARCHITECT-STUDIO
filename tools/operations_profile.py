"""Pure optional operational handoff. Intent is distinct from drill evidence."""
import copy

FIELDS = ('owner', 'workload', 'slis', 'slos', 'resource_limits', 'dependency_policy',
          'build', 'deployment', 'configuration_references', 'smoke_checks',
          'migration', 'rollback', 'backup', 'recovery', 'observability')


def operational_readiness(project):
    supplied = project.get('operations')
    if supplied is None:
        return {'status': 'not_applicable', 'reason': 'No operational profile requested',
                'runtime_verification': 'not_run'}
    if not isinstance(supplied, dict):
        raise ValueError('operations must be a structured object')
    unknown = [name for name in FIELDS if not supplied.get(name)]
    return {'schema_version': 1, 'status': 'partial' if unknown else 'specified',
            'intent': copy.deepcopy(supplied), 'unknown': unknown,
            'runtime_verification': 'not_run', 'deployment_verification': 'not_run',
            'restore_drill': 'not_run',
            'note': 'Declared operational intent only. Actual environment-bound receipts are required for execution claims.'}
