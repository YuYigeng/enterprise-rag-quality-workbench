"""Check launch gates from a product report summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_summary(path: Path) -> dict[str, Any]:
    with path.open() as f:
        summary = json.load(f)
    if not isinstance(summary, dict):
        raise ValueError(f"{path}: expected JSON object")
    return summary


def check_summary(summary: dict[str, Any]) -> bool:
    gates = summary.get("gate_results", [])
    if not isinstance(gates, list):
        raise ValueError("summary missing gate_results array")

    all_passed = True
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        name = gate.get("name", "unknown")
        passed = bool(gate.get("passed"))
        actual = gate.get("actual")
        operator = gate.get("operator")
        expected = gate.get("expected")
        status = "PASS" if passed else "FAIL"
        print(f"{status} {name}: {actual} {operator} {expected}")
        all_passed = all_passed and passed

    launch_status = summary.get("launch_status")
    if launch_status != "pass":
        all_passed = False
    print(f"Launch status: {launch_status}")
    return all_passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Check product report quality gates.")
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    if not args.summary.exists():
        raise FileNotFoundError(args.summary)

    passed = check_summary(load_summary(args.summary))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

