"""Isolated optional validators. Diagnostics omit input values by default."""
import json
import sys
from pathlib import Path
from codec import strict_json_loads


def unique_yaml(text):
    import yaml

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        loader.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                if key in result:
                    raise ValueError('duplicate YAML mapping key')
                result[key] = loader.construct_object(value_node, deep=deep)
            except TypeError:
                raise ValueError('YAML mapping keys must be scalars') from None
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    return yaml.load(text, Loader=UniqueLoader)


if __name__ == '__main__':
    try:
        mode = sys.argv[1]
        text = Path(sys.argv[2]).read_text()
        if mode == 'yaml':
            print(json.dumps(unique_yaml(text), allow_nan=False))
            sys.exit(0)
        data = strict_json_loads(text)
        if mode == 'openapi':
            from openapi_spec_validator import validate_spec
            from validation_engine import _external_refs
            if _external_refs(data):
                raise ValueError('external references forbidden')
            validate_spec(data)
        elif mode == 'project':
            from jsonschema import Draft202012Validator
            schema = strict_json_loads((Path(__file__).resolve().parents[1] / 'schemas/project-v2.schema.json').read_text())
            Draft202012Validator(schema).validate(data)
        else:
            raise ValueError('unknown validator')
        print(json.dumps({'status': 'passed'}))
    except Exception as error:
        # Third-party exception strings frequently include entire confidential instances.
        location = list(getattr(error, 'absolute_path', []))
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__,
                          'location': [str(x) for x in location],
                          'error': 'Input failed the requested validation; values omitted.'}))
        sys.exit(1)
