import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from validate_plan import apply_effects, check_preconditions


Atom = Tuple[str, ...]
State = Set[Atom]


def load_problem_by_id(problem_id: str, data_dir: Path) -> Dict:
    for path in sorted(data_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                record = json.loads(line)

                if record.get("id") == problem_id:
                    return record

    raise FileNotFoundError(f"Problem id '{problem_id}' not found in {data_dir}")


def parse_action_line(line: str) -> Optional[List[str]]:
    line = line.strip()

    if not line or line.startswith(";"):
        return None

    if line.startswith("(") and line.endswith(")"):
        line = line[1:-1].strip()

    function_call = re.match(r"^([A-Za-z_-]+)\((.*)\)$", line)

    if function_call:
        name = function_call.group(1).strip()
        args = [
            arg.strip().upper()
            for arg in function_call.group(2).split(",")
            if arg.strip()
        ]
        return [name] + args

    parts = line.replace(",", " ").split()

    if not parts:
        return None

    name = parts[0].strip()
    args = [arg.strip().upper() for arg in parts[1:]]

    return [name] + args


def load_plan(path: Path) -> List[List[str]]:
    actions = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            action = parse_action_line(line)

            if action is not None:
                actions.append(action)

    return actions


def resolve_plan_path(problem_id: str, explicit_plan: Optional[str]) -> Path:
    if explicit_plan:
        path = Path(explicit_plan)

        if not path.exists():
            raise FileNotFoundError(f"Plan file not found: {path}")

        return path

    candidates = [
        Path("results/plans/llm_to_json") / f"{problem_id}.txt",
        Path("results/plans") / f"{problem_id}.txt",
        Path("results/example_plan.txt"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No plan file found. Pass --plan explicitly, for example: "
        f"--plan results/plans/llm_to_json/{problem_id}.txt"
    )


def state_from_atoms(atoms: Sequence[Sequence[str]]) -> State:
    return {tuple(atom) for atom in atoms}


def build_stacks(state: State) -> List[List[str]]:
    table_blocks = sorted(atom[1] for atom in state if atom[0] == "on_table")

    above: Dict[str, str] = {}

    for atom in state:
        if atom[0] == "on":
            upper = atom[1]
            lower = atom[2]
            above[lower] = upper

    stacks = []

    for bottom in table_blocks:
        stack = [bottom]
        seen = {bottom}
        current = bottom

        while current in above:
            current = above[current]

            if current in seen:
                stack.append(f"CYCLE({current})")
                break

            stack.append(current)
            seen.add(current)

        stacks.append(stack)

    return stacks


def render_stacks(state: State) -> str:
    stacks = build_stacks(state)

    if not stacks:
        return "  <empty table>"

    cell_width = 8
    max_height = max(len(stack) for stack in stacks)
    lines = []

    for level in range(max_height - 1, -1, -1):
        cells = []

        for stack in stacks:
            if level < len(stack):
                cells.append(stack[level].center(cell_width))
            else:
                cells.append("".center(cell_width))

        lines.append("".join(cells).rstrip())

    table_cells = ["table".center(cell_width) for _ in stacks]
    lines.append("".join(table_cells).rstrip())

    return "\n".join(lines)


def format_action(action: List[str]) -> str:
    name = action[0]
    args = action[1:]

    return f"{name}({','.join(args)})"


def render_plan(problem: Dict, actions: List[List[str]]) -> str:
    state = state_from_atoms(problem["initial_state"])

    chunks = []
    chunks.append("Step 0:")
    chunks.append(render_stacks(state))

    for index, action in enumerate(actions, start=1):
        name = action[0]
        args = action[1:]

        precondition_error = check_preconditions(name, args, state)

        chunks.append("")
        chunks.append(f"Step {index}: {format_action(action)}")

        if precondition_error:
            chunks.append(f"ERROR: {precondition_error}")
            chunks.append(render_stacks(state))
            break

        state = apply_effects(name, args, state)
        chunks.append(render_stacks(state))

    return "\n".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem-id", required=True)
    parser.add_argument("--plan", default=None)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    problem = load_problem_by_id(
        problem_id=args.problem_id,
        data_dir=Path(args.data_dir),
    )

    plan_path = resolve_plan_path(
        problem_id=args.problem_id,
        explicit_plan=args.plan,
    )

    actions = load_plan(plan_path)
    rendered = render_plan(problem, actions)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()