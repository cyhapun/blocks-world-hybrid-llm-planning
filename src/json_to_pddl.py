import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def pddl_symbol(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = value.strip("-")
    if not value:
        raise ValueError("Empty PDDL symbol")
    return value


def load_jsonl_record(path: Path, index: int) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    if index < 0 or index >= len(records):
        raise IndexError(f"Index {index} out of range for {path}; total records: {len(records)}")

    return records[index]


def atom_to_pddl(atom: List[str]) -> str:
    predicate = atom[0]
    args = [pddl_symbol(arg) for arg in atom[1:]]

    if args:
        return f"({predicate} {' '.join(args)})"

    return f"({predicate})"


def problem_to_pddl(problem: Dict[str, Any]) -> str:
    problem_id = pddl_symbol(problem["id"])
    objects = [pddl_symbol(obj) for obj in problem["objects"]]

    init_atoms = [atom_to_pddl(atom) for atom in problem["initial_state"]]
    goal_atoms = [atom_to_pddl(atom) for atom in problem["goal"]]

    init_block = "\n    ".join(init_atoms)

    if len(goal_atoms) == 1:
        goal_block = goal_atoms[0]
    else:
        goal_block = "(and\n      " + "\n      ".join(goal_atoms) + "\n    )"

    return f"""(define (problem {problem_id})
  (:domain blocks-world)

  (:objects
    {' '.join(objects)} - block
  )

  (:init
    {init_block}
  )

  (:goal
    {goal_block}
  )
)
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to JSONL dataset file")
    parser.add_argument("--index", type=int, default=0, help="Problem index in JSONL file")
    parser.add_argument("--output-dir", default="pddl/problems", help="Output directory")
    parser.add_argument("--output", default=None, help="Optional explicit output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    problem = load_jsonl_record(input_path, args.index)

    pddl_text = problem_to_pddl(problem)

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{problem['id']}.pddl"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pddl_text, encoding="utf-8")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()