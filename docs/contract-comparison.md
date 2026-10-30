# Supported API contract comparison

Studio compares declared interface operations with native/exported OpenAPI operations. It resolves bounded offline JSON Pointers and checks supported structure; it does not prove arbitrary JSON Schema logical equivalence or runtime compatibility.

Comparison preserves user-defined property/header/media/security names, including names such as `description`, `example`, `x-customer`, and `$ref`. Documentation fields are ignored only in object contexts where they are annotations. Literal `enum`, `const`, and `default` values, and opaque schema vocabularies, remain data: their keys are neither removed nor followed as references.

OpenAPI version and object context matter:

- In OpenAPI 3.0, extra Reference Object properties are ignored and cannot override the referenced contract.
- In OpenAPI 3.1, ordinary Reference Objects still cannot add arbitrary contract properties. Their supported `summary`/`description` annotations do not change structural comparison.
- Within an OpenAPI 3.1 Schema Object, `$ref` and adjacent constraints both apply. Studio represents that conjunction as `allOf`; it never overwrites the referenced schema with sibling keywords. Equivalent schemas expressed differently may conservatively require review because general schema satisfiability/equivalence is outside this check.

Remote references and unsupported pointer fragments are rejected. Recursive references remain bounded attributed references. A structural/schema pass is independent of runtime behavior, authorization enforcement, and deployment verification.

The version distinctions were checked against the official [OpenAPI 3.0.4 Reference Object](https://spec.openapis.org/oas/v3.0.4.html#reference-object), [OpenAPI 3.1.1 Reference Object](https://spec.openapis.org/oas/v3.1.1.html#reference-object), and [3.1.1 Schema Object](https://spec.openapis.org/oas/v3.1.1.html#schema-object) specifications. These constraints apply to the supported 3.0/3.1 comparison paths.
