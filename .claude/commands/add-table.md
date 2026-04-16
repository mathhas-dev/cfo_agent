Add a new table to the Schema Registry.

Steps:
1. Ask the user for: table name, column names, and business meaning of each column in Portuguese (as directors use it).
2. Add the entry to `schema_registry/registry.py` (or the registry YAML/JSON if that's the format in use), following the existing pattern.
3. Verify the entry has: table name, column name, SQL data type, and a clear Portuguese business description.
4. Run `pytest tests/unit/test_schema_registry.py` to confirm the new entry passes validation.
5. Show the diff of what was added.
