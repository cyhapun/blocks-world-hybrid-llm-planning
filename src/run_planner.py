import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def parse_lisp_action(line: str) -> Optional[Tuple[str, List[str]]]:
    line = line.strip()

    if not line or line.startswith(";"):
        return None

    if line.startswith("(") and line.endswith(")"):
        line = line[1:-1].strip()

    parts = line.replace(",", " ").split()

    if not parts:
        return None

    name = parts[0]
    args = parts[1:]

    return name, args


def parse_plan_text(text: str) -> List[str]:
    actions = []

    for line in text.splitlines():
        parsed = parse_lisp_action(line)

        if parsed is None:
            continue

        name, args = parsed

        if name not in {"pick-up", "put-down", "stack", "unstack"}:
            continue

        args = [arg.upper() for arg in args]
        actions.append(f"{name}({','.join(args)})")

    return actions


def find_solution_file(problem_path: Path) -> Optional[Path]:
    candidates = [
        Path(str(problem_path) + ".soln"),
        problem_path.with_suffix(problem_path.suffix + ".soln"),
        problem_path.with_suffix(".soln"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def build_pyperplan_command(domain: Path, problem: Path, heuristic: str, search: str) -> List[str]:
    executable = shutil.which("pyperplan")

    if executable:
        return [executable, "-H", heuristic, "-s", search, str(domain), str(problem)]

    return [
        sys.executable,
        "-m",
        "pyperplan",
        "-H",
        heuristic,
        "-s",
        search,
        str(domain),
        str(problem),
    ]


def run_pyperplan(domain: Path, problem: Path, heuristic: str, search: str) -> subprocess.CompletedProcess:
    command = build_pyperplan_command(domain, problem, heuristic, search)

    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="pddl/domain_blocks_world.pddl")
    parser.add_argument("--problem", required=True)
    parser.add_argument("--output", default="results/example_plan.txt")
    parser.add_argument("-H", "--heuristic", default="hff")
    parser.add_argument("-s", "--search", default="gbf")
    args = parser.parse_args()

    domain_path = Path(args.domain)
    problem_path = Path(args.problem)
    output_path = Path(args.output)

    if not domain_path.exists():
        raise FileNotFoundError(f"Domain file not found: {domain_path}")

    if not problem_path.exists():
        raise FileNotFoundError(f"Problem file not found: {problem_path}")

    result = run_pyperplan(
        domain=domain_path,
        problem=problem_path,
        heuristic=args.heuristic,
        search=args.search,
    )

    combined_output = result.stdout + "\n" + result.stderr

    if result.returncode != 0:
        print(combined_output)
        raise RuntimeError(f"pyperplan failed with exit code {result.returncode}")

    solution_file = find_solution_file(problem_path)

    if solution_file:
        raw_plan_text = solution_file.read_text(encoding="utf-8")
    else:
        raw_plan_text = combined_output

    actions = parse_plan_text(raw_plan_text)

    if not actions:
        print(combined_output)
        raise RuntimeError("No valid plan actions found in pyperplan output.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(actions) + "\n", encoding="utf-8")

    print(f"Wrote {output_path}")
    for action in actions:
        print(action)


if __name__ == "__main__":
    main()