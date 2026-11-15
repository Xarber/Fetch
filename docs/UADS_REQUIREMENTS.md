# Fetch UADS requirements

The baseline uses the supplied UADS sections 1–52. The standard provided no independent version number. The [manifest](../uads.json) records Fetch applicability and verification status, and the [registry](../config/uads-requirements.json) maps stable IDs to their authoritative sections and verification methods. This initial registry groups related checks. Finer-grained requirements and evidence remain to be added.

Run `python scripts/validate-uads.py` with `jsonschema` installed. The check validates declarations, local references and the workspace JavaScript size budget. It does not run platform builds or establish release readiness. Other budgets in the configuration are targets awaiting measurement. See the [task queue](ACTIVE_TASKS.md) and [verification report](reports/VALIDATION.md).
