import argparse
import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "id",
    "difficulty",
    "objects",
    "initial_state",
    "goal",
    "natural_language",
}

PREDICATE_ARITY = {
    "on_table": 1,
    "on": 2,
    "clear": 1,
    "holding": 1,
    "handempty": 0,
}


def validate_atom(atom, objects, line_no, field_name):
    errors = []

    if not isinstance(atom, list) or len(atom) == 0:
        return [f"Line {line_no}: atom in '{field_name}' must be a non-empty list"]

    predicate = atom[0]

    if not isinstance(predicate, str):
        return [f"Line {line_no}: predicate must be a string in atom {atom}"]

    if predicate not in PREDICATE_ARITY:
        errors.append(f"Line {line_no}: unknown predicate '{predicate}' in atom {atom}")
        return errors

    expected_arity = PREDICATE_ARITY[predicate]
    actual_arity = len(atom) - 1

    if actual_arity != expected_arity:
        errors.append(
            f"Line {line_no}: predicate '{predicate}' expects {expected_arity} "
            f"object(s), got {actual_arity} in atom {atom}"
        )
        return errors

    for obj in atom[1:]:
        if obj not in objects:
            errors.append(
                f"Line {line_no}: object '{obj}' in atom {atom} is not listed in objects"
            )

    return errors


def validate_record(record, line_no, seen_ids):
    errors = []

    if not isinstance(record, dict):
        return [f"Line {line_no}: each line must be a JSON object"]

    missing_fields = REQUIRED_FIELDS - set(record.keys())
    if missing_fields:
        errors.append(f"Line {line_no}: missing fields: {sorted(missing_fields)}")

    if errors:
        return errors

    record_id = record["id"]

    if not isinstance(record_id, str) or not record_id:
        errors.append(f"Line {line_no}: 'id' must be a non-empty string")
    elif record_id in seen_ids:
        errors.append(f"Line {line_no}: duplicated id '{record_id}'")
    else:
        seen_ids.add(record_id)

    objects = record["objects"]

    if not isinstance(objects, list) or not all(isinstance(o, str) for o in objects):
        errors.append(f"Line {line_no}: 'objects' must be a list of strings")
        objects = []

    if len(objects) != len(set(objects)):
        errors.append(f"Line {line_no}: 'objects' contains duplicated values")

    for field_name in ["initial_state", "goal"]:
        value = record[field_name]

        if not isinstance(value, list):
            errors.append(f"Line {line_no}: '{field_name}' must be a list")
            continue

        for atom in value:
            errors.extend(validate_atom(atom, objects, line_no, field_name))

    if not isinstance(record["natural_language"], str) or not record["natural_language"]:
        errors.append(f"Line {line_no}: 'natural_language' must be a non-empty string")

    if not isinstance(record["difficulty"], str) or not record["difficulty"]:
        errors.append(f"Line {line_no}: 'difficulty' must be a non-empty string")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to JSONL dataset file")
    args = parser.parse_args()

    data_path = Path(args.data)

    if not data_path.exists():
        print(f"ERROR: file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    seen_ids = set()
    total = 0

    with data_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            total += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"Line {line_no}: invalid JSON: {e}")
                continue

            all_errors.extend(validate_record(record, line_no, seen_ids))

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {data_path} has {len(all_errors)} error(s)", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {data_path} passed validation with {total} records.")


if __name__ == "__main__":
    main()

# To check the data
# python src/check_dataset.py --data data/blocks_world_easy.jsonl
# python src/check_dataset.py --data data/blocks_world_medium.jsonl
# python src/check_dataset.py --data data/blocks_world_hard.jsonl