#!/usr/bin/env python3
"""Load the task files shipped in this release."""
from __future__ import annotations

import json
from pathlib import Path

RELEASE = Path(__file__).resolve().parents[1]
DATA = RELEASE / "data"

PROPERTIES = (
    "dipole",
    "gap",
    "infrared",
    "raman",
    "ultraviolet_visible",
    "proton_nmr_peaks",
    "proton_nmr_integration",
    "proton_nmr_atom",
    "carbon_nmr_peaks",
    "carbon_nmr_degeneracy",
    "carbon_nmr_atom",
    "electronic",
    "magnetic_resonance",
    "vibrational",
    "all_properties",
)
CONDITIONS = ("correct", "shuffled", "counterfactual")
FIELDS = ("record_id", "masked_smiles", "mask", "properties", "candidate_completed_smiles")


def task_path(property_name: str, condition: str) -> Path:
    if property_name not in PROPERTIES:
        raise ValueError(f"unknown property: {property_name}")
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    return DATA / property_name / f"{condition}.jsonl"


def load_tasks(property_name: str, condition: str) -> list[dict]:
    path = task_path(property_name, condition)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for record in records:
        missing = [field for field in FIELDS if field not in record]
        if missing:
            raise ValueError(f"{path.name} record {record.get('record_id')} missing {missing}")
    return records


def main() -> None:
    counts = {}
    for property_name in PROPERTIES:
        counts[property_name] = {
            condition: len(load_tasks(property_name, condition))
            for condition in CONDITIONS
        }
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
