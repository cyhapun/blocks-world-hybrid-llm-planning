import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from llm_client import LLMClient, LLMConfig
from validate_plan import validate_plan


CSV_COLUMNS = [
    "id",
    "difficulty",
    "method",
    "raw_output",
    "parse_success",
    "plan_valid",
    "goal_achieved",
    "success",
    "plan_length",
    "error_type",
]


def load_jsonl(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    records = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            records.append(json.loads(line))

            if limit is not None and len(records) >= limit:
                break

    return records


def load_prompt_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_action_name(name: str) -> str:
    aliases = {
        "pickup": "pick-up",
        "pick_up": "pick-up",
        "pick-up": "pick-up",
        "putdown": "put-down",
        "put_down": "put-down",
        "put-down": "put-down",
        "stack": "stack",
        "unstack": "unstack",
    }

    return aliases.get(name.strip().lower(), name.strip())


def parse_action_line(line: str) -> Optional[List[str]]:
    line = line.strip()

    if not line:
        return None

    if line.startswith("```"):
        return None

    if line.startswith("-"):
        line = line[1:].strip()

    numbered = re.match(r"^\d+[\.\)]\s*(.+)$", line)
    if numbered:
        line = numbered.group(1).strip()

    if line.startswith("(") and line.endswith(")"):
        line = line[1:-1].strip()

    function_call = re.match(r"^([A-Za-z_-]+)\((.*)\)$", line)
    if function_call:
        action_name = normalize_action_name(function_call.group(1))
        args_text = function_call.group(2)
        args = [arg.strip().upper() for arg in args_text.split(",") if arg.strip()]
        return [action_name] + args

    parts = line.replace(",", " ").split()

    if not parts:
        return None

    action_name = normalize_action_name(parts[0])
    args = [arg.strip().upper() for arg in parts[1:]]

    return [action_name] + args


def parse_plan(raw_output: str) -> Tuple[bool, List[List[str]], Optional[str]]:
    actions = []

    for line in raw_output.splitlines():
        parsed = parse_action_line(line)

        if parsed is not None:
            actions.append(parsed)

    if not actions:
        return False, [], "No valid action lines could be parsed."

    return True, actions, None


def write_raw_output(output_dir: Path, method: str, problem_id: str, raw_output: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{method}_{problem_id}.txt"
    output_path.write_text(raw_output, encoding="utf-8")

    return output_path


def write_csv(csv_path: Path, rows: List[Dict[str, Any]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_client_from_args(args: argparse.Namespace) -> LLMClient:
    if args.mode is None:
        return LLMClient()

    if args.mode == "hf":
        config = LLMConfig(
            mode="hf",
            model=args.model,
            api_key=args.api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        return LLMClient(config=config)

    if args.mode == "local":
        config = LLMConfig(
            mode="local",
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        return LLMClient(config=config)

    raise ValueError("Mode must be either 'hf' or 'local'.")


def run_baseline(
    data_path: Path,
    prompt_path: Path,
    raw_output_dir: Path,
    csv_path: Path,
    limit: Optional[int],
    client: LLMClient,
) -> None:
    records = load_jsonl(data_path, limit=limit)
    prompt_template = load_prompt_template(prompt_path)

    rows = []
    method = f"llm_only_{client.config.mode}"

    for record in records:
        problem_id = record["id"]
        prompt = prompt_template.format(
            natural_language=record["natural_language"]
        )

        print(f"Running {method} for {problem_id}...")

        raw_output = client.generate(prompt)
        write_raw_output(raw_output_dir, method, problem_id, raw_output)

        parse_success, actions, parse_error = parse_plan(raw_output)

        if parse_success:
            validation = validate_plan(
                initial_state=record["initial_state"],
                goal=record["goal"],
                actions=actions,
                objects=record["objects"],
            )

            plan_valid = bool(validation["valid"])
            goal_achieved = bool(validation["goal_achieved"])
            success = bool(plan_valid and goal_achieved)
            plan_length = len(actions)
            error_type = validation["error_type"] or ""
        else:
            plan_valid = False
            goal_achieved = False
            success = False
            plan_length = 0
            error_type = "parse_error"

        rows.append(
            {
                "id": problem_id,
                "difficulty": record["difficulty"],
                "method": method,
                "raw_output": raw_output,
                "parse_success": parse_success,
                "plan_valid": plan_valid,
                "goal_achieved": goal_achieved,
                "success": success,
                "plan_length": plan_length,
                "error_type": error_type,
            }
        )

        if success:
            print(f"OK {problem_id}: valid plan, length={plan_length}")
        else:
            print(f"FAIL {problem_id}: {parse_error or error_type}")

    write_csv(csv_path, rows)
    print(f"Wrote {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to JSONL dataset")
    parser.add_argument("--limit", type=int, default=None)

    parser.add_argument(
        "--prompt",
        default="src/prompts/basic/llm_only_prompt.txt",
        help="Path to prompt template",
    )
    parser.add_argument(
        "--raw-output-dir",
        default="results/raw_outputs/llm_only",
        help="Directory for raw LLM outputs",
    )
    parser.add_argument(
        "--output-csv",
        default="results/llm_only_results.csv",
        help="Path to output CSV",
    )

    parser.add_argument(
        "--mode",
        choices=["hf", "local"],
        default=None,
        help="Override LLM_MODE from .env",
    )
    parser.add_argument("--model", default=None, help="Override model name")
    parser.add_argument("--base-url", default=None, help="Local LLM base URL")
    parser.add_argument("--api-key", default=None, help="HF token or local API key")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=512)

    args = parser.parse_args()

    client = build_client_from_args(args)

    run_baseline(
        data_path=Path(args.data),
        prompt_path=Path(args.prompt),
        raw_output_dir=Path(args.raw_output_dir),
        csv_path=Path(args.output_csv),
        limit=args.limit,
        client=client,
    )


if __name__ == "__main__":
    main()