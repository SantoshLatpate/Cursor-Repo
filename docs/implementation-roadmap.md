# Implementation Roadmap

## Package order

1. Core
2. Event Registration
3. Payment
4. Grant Application

## Standard-object field rules

- Standard objects include only `fields/` metadata, never full object definitions.
- All standard-object custom fields are in `packages/core`.
- Use `EC_` prefix for every custom field API name.
