#!/usr/bin/env python3
"""Score a prediction file against the labels for one property and condition."""

import argparse
import json
import sys
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


def load_jsonl(path):
    rows = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
        if not isinstance(row, dict) or "record_id" not in row:
            raise ValueError(f"{path}:{line_number}: missing record_id")
        rows.append(row)
    return rows


def load_task(property_name, condition):
    if property_name not in PROPERTIES or condition not in CONDITIONS:
        raise ValueError(f"unknown property or condition: {property_name} {condition}")
    tasks = load_jsonl(DATA / property_name / f"{condition}.jsonl")
    labels = load_jsonl(DATA / property_name / f"{condition}.labels.jsonl")
    if [row["record_id"] for row in tasks] != [row["record_id"] for row in labels]:
        raise ValueError(f"task and label record_id lists differ: {property_name} {condition}")
    scored = []
    for task, label in zip(tasks, labels):
        if not isinstance(label.get("label"), int):
            raise ValueError(f"label is not an integer: {label['record_id']}")
        n_candidates = len(task["candidate_completed_smiles"])
        if not 0 <= label["label"] < n_candidates:
            raise ValueError(f"label out of range: {label['record_id']}")
        scored.append((task["record_id"], label["label"], n_candidates))
    return scored


def load_predictions(path):
    chosen = {}
    for row in load_jsonl(path):
        record_id = row["record_id"]
        if record_id in chosen:
            raise ValueError(f"duplicate prediction: {record_id}")
        if row.get("invalid") is True or "selected_candidate_index" not in row:
            chosen[record_id] = None
            continue
        index = row["selected_candidate_index"]
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError(f"selected_candidate_index is not an integer: {record_id}")
        chosen[record_id] = index
    return chosen


def score(property_name, condition, predictions):
    hits = 0
    invalid = 0
    missing = 0
    out_of_range = 0
    tasks = load_task(property_name, condition)
    for record_id, label, n_candidates in tasks:
        if record_id not in predictions:
            missing += 1
            continue
        choice = predictions[record_id]
        if choice is None:
            invalid += 1
            continue
        if not 0 <= choice < n_candidates:
            out_of_range += 1
            continue
        hits += choice == label
    n = len(tasks)
    return {
        "property": property_name,
        "condition": condition,
        "n": n,
        "hits": hits,
        "accuracy": hits / n if n else None,
        "missing": missing,
        "invalid": invalid,
        "out_of_range": out_of_range,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--property", required=True, choices=PROPERTIES)
    parser.add_argument("--condition", required=True, choices=CONDITIONS)
    parser.add_argument("--predictions", required=True, type=Path)
    args = parser.parse_args()
    result = score(args.property, args.condition, load_predictions(args.predictions))
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
