import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from llm_client import LLMClient, LLMConfig
from llm_only_baseline import load_prompt_template as load_text_prompt
from llm_only_baseline import parse_plan as parse_llm_plan
from llm_to_json import (
    parse_llm_json,
    plan_lines_to_validator_actions,
    run_planner_and_parse_plan,
    structured_json_to_problem_record,
    write_pddl_problem,
)
from validate_plan import validate_plan


METRICS_COLUMNS = [
    "id",
    "difficulty",
    "method",
    "parse_success",
    "planner_success",
    "plan_valid",
    "goal_achieved",
    "success",
    "plan_length",
    "runtime",
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_metrics_rows(output_path: Path, rows: List[Dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists()

    with output_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=METRICS_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)


def reset_metrics_file(output_path: Path) -> None:
    if output_path.exists():
        output_path.unlink()


def make_row(
    record: Dict[str, Any],
    method: str,
    parse_success: bool,
    planner_success: Optional[bool],
    plan_valid: bool,
    goal_achieved: bool,
    success: bool,
    plan_length: int,
    runtime: float,
    error_type: str,
) -> Dict[str, Any]:
    return {
        "id": record["id"],
        "difficulty": record["difficulty"],
        "method": method,
        "parse_success": parse_success,
        "planner_success": "" if planner_success is None else planner_success,
        "plan_valid": plan_valid,
        "goal_achieved": goal_achieved,
        "success": success,
        "plan_length": plan_length,
        "runtime": f"{runtime:.4f}",
        "error_type": error_type,
    }


def build_client_from_args(args: argparse.Namespace) -> LLMClient:
    load_dotenv()

    if args.mode is None:
        return LLMClient()

    temperature = (
        args.temperature
        if args.temperature is not None
        else float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )

    max_tokens = (
        args.max_tokens
        if args.max_tokens is not None
        else int(os.getenv("LLM_MAX_TOKENS", "512"))
    )

    if args.mode == "hf":
        return LLMClient(
            config=LLMConfig(
                mode="hf",
                model=args.model or os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                api_key=args.api_key or os.getenv("HF_TOKEN"),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

    if args.mode == "local":
        return LLMClient(
            config=LLMConfig(
                mode="local",
                model=args.model or os.getenv("LOCAL_LLM_MODEL", "local-model"),
                base_url=args.base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8000/v1"),
                api_key=args.api_key or os.getenv("LOCAL_LLM_API_KEY", ""),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

    raise ValueError("mode must be either 'hf' or 'local'")


def evaluate_llm_only(
    records: List[Dict[str, Any]],
    client: LLMClient,
    prompt_path: Path,
    raw_output_dir: Path,
) -> List[Dict[str, Any]]:
    prompt_template = load_text_prompt(prompt_path)
    rows = []

    for record in records:
        start_time = time.perf_counter()
        problem_id = record["id"]

        print(f"[llm_only] Running {problem_id}...")

        try:
            prompt = prompt_template.replace(
                "{natural_language}",
                record["natural_language"],
            )

            raw_output = client.generate(prompt)

            write_text(
                raw_output_dir / f"llm_only_{problem_id}.txt",
                raw_output,
            )

            parse_success, actions, parse_error = parse_llm_plan(raw_output)

            if not parse_success:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_row(
                        record=record,
                        method="llm_only",
                        parse_success=False,
                        planner_success=None,
                        plan_valid=False,
                        goal_achieved=False,
                        success=False,
                        plan_length=0,
                        runtime=runtime,
                        error_type=f"parse_error: {parse_error}",
                    )
                )
                print(f"[llm_only] FAIL {problem_id}: parse_error")
                continue

            validation = validate_plan(
                initial_state=record["initial_state"],
                goal=record["goal"],
                actions=actions,
                objects=record["objects"],
            )

            runtime = time.perf_counter() - start_time
            plan_valid = bool(validation["valid"])
            goal_achieved = bool(validation["goal_achieved"])
            success = bool(plan_valid and goal_achieved)

            rows.append(
                make_row(
                    record=record,
                    method="llm_only",
                    parse_success=True,
                    planner_success=None,
                    plan_valid=plan_valid,
                    goal_achieved=goal_achieved,
                    success=success,
                    plan_length=len(actions),
                    runtime=runtime,
                    error_type=validation["error_type"] or "",
                )
            )

            if success:
                print(f"[llm_only] OK {problem_id}: length={len(actions)}")
            else:
                print(f"[llm_only] FAIL {problem_id}: {validation['error_type']}")

        except Exception as exc:
            runtime = time.perf_counter() - start_time
            rows.append(
                make_row(
                    record=record,
                    method="llm_only",
                    parse_success=False,
                    planner_success=None,
                    plan_valid=False,
                    goal_achieved=False,
                    success=False,
                    plan_length=0,
                    runtime=runtime,
                    error_type=f"unexpected_error: {exc}",
                )
            )
            print(f"[llm_only] FAIL {problem_id}: unexpected_error")

    return rows


def evaluate_llm_planner(
    records: List[Dict[str, Any]],
    client: LLMClient,
    prompt_path: Path,
    domain_path: Path,
    raw_output_dir: Path,
    pddl_output_dir: Path,
    plan_output_dir: Path,
    heuristic: str,
    search: str,
) -> List[Dict[str, Any]]:
    prompt_template = load_text_prompt(prompt_path)
    rows = []

    for record in records:
        start_time = time.perf_counter()
        problem_id = record["id"]

        print(f"[llm_planner] Running {problem_id}...")

        try:
            prompt = prompt_template.replace(
                "{natural_language}",
                record["natural_language"],
            )

            raw_output = client.generate(prompt)

            write_text(
                raw_output_dir / f"llm_planner_{problem_id}.txt",
                raw_output,
            )

            try:
                structured = parse_llm_json(raw_output)
            except Exception as exc:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_row(
                        record=record,
                        method="llm_planner",
                        parse_success=False,
                        planner_success=False,
                        plan_valid=False,
                        goal_achieved=False,
                        success=False,
                        plan_length=0,
                        runtime=runtime,
                        error_type=f"json_parse_error: {exc}",
                    )
                )
                print(f"[llm_planner] FAIL {problem_id}: json_parse_error")
                continue

            try:
                generated_problem = structured_json_to_problem_record(
                    source_record=record,
                    structured=structured,
                )
                problem_path = write_pddl_problem(
                    problem_record=generated_problem,
                    output_dir=pddl_output_dir,
                )
            except Exception as exc:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_row(
                        record=record,
                        method="llm_planner",
                        parse_success=True,
                        planner_success=False,
                        plan_valid=False,
                        goal_achieved=False,
                        success=False,
                        plan_length=0,
                        runtime=runtime,
                        error_type=f"pddl_generation_error: {exc}",
                    )
                )
                print(f"[llm_planner] FAIL {problem_id}: pddl_generation_error")
                continue

            planner_success, plan_lines, planner_error = run_planner_and_parse_plan(
                domain_path=domain_path,
                problem_path=problem_path,
                plan_output_dir=plan_output_dir,
                problem_id=problem_id,
                heuristic=heuristic,
                search=search,
            )

            if not planner_success:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_row(
                        record=record,
                        method="llm_planner",
                        parse_success=True,
                        planner_success=False,
                        plan_valid=False,
                        goal_achieved=False,
                        success=False,
                        plan_length=0,
                        runtime=runtime,
                        error_type=planner_error or "planner_error",
                    )
                )
                print(f"[llm_planner] FAIL {problem_id}: {planner_error}")
                continue

            validator_actions = plan_lines_to_validator_actions(plan_lines)

            # Validate against the original dataset problem.
            # This catches incorrect LLM semantic parsing.
            validation = validate_plan(
                initial_state=record["initial_state"],
                goal=record["goal"],
                actions=validator_actions,
                objects=record["objects"],
            )

            runtime = time.perf_counter() - start_time
            plan_valid = bool(validation["valid"])
            goal_achieved = bool(validation["goal_achieved"])
            success = bool(plan_valid and goal_achieved)

            rows.append(
                make_row(
                    record=record,
                    method="llm_planner",
                    parse_success=True,
                    planner_success=True,
                    plan_valid=plan_valid,
                    goal_achieved=goal_achieved,
                    success=success,
                    plan_length=len(validator_actions),
                    runtime=runtime,
                    error_type=validation["error_type"] or "",
                )
            )

            if success:
                print(f"[llm_planner] OK {problem_id}: length={len(validator_actions)}")
            else:
                print(f"[llm_planner] FAIL {problem_id}: {validation['error_type']}")

        except Exception as exc:
            runtime = time.perf_counter() - start_time
            rows.append(
                make_row(
                    record=record,
                    method="llm_planner",
                    parse_success=False,
                    planner_success=False,
                    plan_valid=False,
                    goal_achieved=False,
                    success=False,
                    plan_length=0,
                    runtime=runtime,
                    error_type=f"unexpected_error: {exc}",
                )
            )
            print(f"[llm_planner] FAIL {problem_id}: unexpected_error")

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method",
        choices=["llm_only", "llm_planner", "all"],
        required=True,
    )
    parser.add_argument("--data", required=True)
    parser.add_argument("--limit", type=int, default=None)

    parser.add_argument(
        "--output",
        default="results/metrics.csv",
        help="Unified metrics CSV path",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove existing metrics file before writing",
    )

    parser.add_argument(
        "--llm-only-prompt",
        default="src/prompts/llm_only_prompt.txt",
    )
    parser.add_argument(
        "--llm-planner-prompt",
        default="src/prompts/llm_to_json_prompt.txt",
    )

    parser.add_argument(
        "--llm-only-raw-dir",
        default="results/raw_outputs/llm_only",
    )
    parser.add_argument(
        "--llm-planner-raw-dir",
        default="results/raw_outputs/llm_to_json",
    )
    parser.add_argument(
        "--llm-planner-pddl-dir",
        default="pddl/problems/llm_to_json",
    )
    parser.add_argument(
        "--llm-planner-plan-dir",
        default="results/plans/llm_to_json",
    )

    parser.add_argument(
        "--domain",
        default="pddl/domain_blocks_world.pddl",
    )
    parser.add_argument("-H", "--heuristic", default="hff")
    parser.add_argument("-s", "--search", default="gbf")

    parser.add_argument(
        "--mode",
        choices=["hf", "local"],
        default=None,
        help="Override LLM_MODE from .env",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)

    args = parser.parse_args()

    output_path = Path(args.output)

    if args.reset:
        reset_metrics_file(output_path)

    records = load_jsonl(Path(args.data), limit=args.limit)
    client = build_client_from_args(args)

    rows = []

    if args.method in {"llm_only", "all"}:
        rows.extend(
            evaluate_llm_only(
                records=records,
                client=client,
                prompt_path=Path(args.llm_only_prompt),
                raw_output_dir=Path(args.llm_only_raw_dir),
            )
        )

    if args.method in {"llm_planner", "all"}:
        rows.extend(
            evaluate_llm_planner(
                records=records,
                client=client,
                prompt_path=Path(args.llm_planner_prompt),
                domain_path=Path(args.domain),
                raw_output_dir=Path(args.llm_planner_raw_dir),
                pddl_output_dir=Path(args.llm_planner_pddl_dir),
                plan_output_dir=Path(args.llm_planner_plan_dir),
                heuristic=args.heuristic,
                search=args.search,
            )
        )

    append_metrics_rows(output_path, rows)

    print(f"Wrote {output_path}")
    print(f"Rows added: {len(rows)}")


if __name__ == "__main__":
    main()

# Run this command:
# python src/evaluate.py --method llm_only --data data/blocks_world_easy.jsonl --limit 3 --reset  
# python src/evaluate.py --method llm_planner --data data/blocks_world_easy.jsonl --limit 3 --reset
# python src/evaluate.py --method all --data data/blocks_world_easy.jsonl --limit 3 --reset