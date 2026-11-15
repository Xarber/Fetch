#!/usr/bin/env python3
"""Check declarations and local evidence links for the Fetch UADS manifest."""

import json
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check_file(path):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        raise ValueError(f"Missing or external repository reference: {path}")


def validate():
    manifest = load("uads.json")
    schema = load("config/uads-schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
    registry = load("config/uads-requirements.json")
    entries = manifest["requirements"]
    ids = {entry["id"] for entry in entries}
    if len(ids) != len(entries) or ids != registry.keys():
        raise ValueError("Requirement IDs must be unique and match the registry")
    exceptions = {}
    for record in manifest["exceptions"]:
        key = record["id"]
        if key in exceptions or key not in ids:
            raise ValueError(f"Duplicate or unknown exception: {key}")
        if not date.fromisoformat(record["approvedOn"]) <= date.today() <= date.fromisoformat(record["reviewOn"]):
            raise ValueError(f"Exception needs review: {key}")
        exceptions[key] = record
    for entry in entries:
        key = entry["id"]
        check_file(registry[key]["reference"])
        if entry["state"] == "passed" and not entry["evidence"]:
            raise ValueError(f"No verification evidence for {key}")
        waived = entry["state"] == "waived"
        if waived != (key in exceptions) or waived != (entry["applicability"] == "approved-exception"):
            raise ValueError(f"Inconsistent exception state for {key}")
        for evidence in entry["evidence"]:
            check_file(evidence)
    for path in manifest["quality"].values():
        check_file(path)
    budgets = load(manifest["quality"]["budgets"])
    if (ROOT / "web/app.js").stat().st_size > budgets["web"]["workspaceJsBytes"]:
        raise ValueError("Workspace JavaScript exceeds its size budget")
    print(f"Validated {len(entries)} requirement declarations and workspace JavaScript budget")


if __name__ == "__main__":
    try:
        validate()
    except Exception as error:
        raise SystemExit(f"UADS validation failed: {error}") from None
