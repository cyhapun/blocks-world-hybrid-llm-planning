import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from json_to_pddl import problem_to_pddl
from llm_client import LLMClient, LLMConfig
from run_planner import find_solution_file, parse_plan_text, run_pyperplan
from validate_plan import validate_plan


CSV_COLUMNS = [
    "id",
    "difficulty",
    "method",
    "json_parse_success",
    "pddl_generated",
    "planner_success",
    "plan_valid",
    "goal_achieved",
    "success",
    "plan_length",
    "runtime",
    "error_type",
]

PREDICATE_ARITY = {
    "on_table": 1,
    "on": 2,
    "clear": 1,
    "holding": 1,
    "handempty": 0,
}


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


def extract_json_text(raw_output: str) -> str:
    text = raw_output.strip()

    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1].strip()

    return text


def normalize_predicate(predicate: str) -> str:
    predicate = predicate.strip()

    aliases = {
        "on-table": "on_table",
        "ontable": "on_table",
        "hand-empty": "handempty",
        "hand_empty": "handempty",
        "handempty": "handempty",
    }

    return aliases.get(predicate.lower(), predicate)


def normalize_atom(atom: Any) -> List[str]:
    if not isinstance(atom, list) or len(atom) == 0:
        raise ValueError(f"Invalid atom: {atom}")

    predicate = normalize_predicate(str(atom[0]))
    args = [str(arg).strip().upper() for arg in atom[1:]]

    return [predicate] + args


def normalize_structured_json(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")

    if "objects" not in data:
        raise ValueError("Missing required field: objects")

    if "init" in data:
        init_value = data["init"]
    elif "initial_state" in data:
        init_value = data["initial_state"]
    else:
        raise ValueError("Missing required field: init")

    if "goal" not in data:
        raise ValueError("Missing required field: goal")

    objects = [str(obj).strip().upper() for obj in data["objects"]]

    normalized = {
        "objects": objects,
        "init": [normalize_atom(atom) for atom in init_value],
        "goal": [normalize_atom(atom) for atom in data["goal"]],
    }

    validate_structured_json(normalized)

    return normalized


def validate_structured_json(data: Dict[str, Any]) -> None:
    objects = data["objects"]

    if not isinstance(objects, list) or not objects:
        raise ValueError("objects must be a non-empty list.")

    if len(objects) != len(set(objects)):
        raise ValueError("objects contains duplicated values.")

    object_set = set(objects)

    for field_name in ["init", "goal"]:
        atoms = data[field_name]

        if not isinstance(atoms, list):
            raise ValueError(f"{field_name} must be a list.")

        for atom in atoms:
            if not isinstance(atom, list) or not atom:
                raise ValueError(f"Invalid atom in {field_name}: {atom}")

            predicate = atom[0]

            if predicate not in PREDICATE_ARITY:
                raise ValueError(f"Unknown predicate '{predicate}' in {field_name}.")

            expected_arity = PREDICATE_ARITY[predicate]
            actual_arity = len(atom) - 1

            if actual_arity != expected_arity:
                raise ValueError(
                    f"Predicate '{predicate}' expects {expected_arity} argument(s), "
                    f"got {actual_arity}."
                )

            for obj in atom[1:]:
                if obj not in object_set:
                    raise ValueError(
                        f"Object '{obj}' in {field_name} does not exist in objects."
                    )


def parse_llm_json(raw_output: str) -> Dict[str, Any]:
    json_text = extract_json_text(raw_output)
    data = json.loads(json_text)

    return normalize_structured_json(data)


def structured_json_to_problem_record(
    source_record: Dict[str, Any],
    structured: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "id": source_record["id"],
        "difficulty": source_record["difficulty"],
        "objects": structured["objects"],
        "initial_state": structured["init"],
        "goal": structured["goal"],
        "natural_language": source_record["natural_language"],
    }


def write_raw_output(output_dir: Path, method: str, problem_id: str, raw_output: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{method}_{problem_id}.txt"
    output_path.write_text(raw_output, encoding="utf-8")

    return output_path


def write_pddl_problem(problem_record: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{problem_record['id']}.pddl"
    output_path.write_text(problem_to_pddl(problem_record), encoding="utf-8")

    return output_path


def solution_candidates(problem_path: Path) -> List[Path]:
    return [
        Path(str(problem_path) + ".soln"),
        problem_path.with_suffix(problem_path.suffix + ".soln"),
        problem_path.with_suffix(".soln"),
    ]


def remove_old_solution_files(problem_path: Path) -> None:
    for path in solution_candidates(problem_path):
        if path.exists():
            path.unlink()


def plan_lines_to_validator_actions(plan_lines: List[str]) -> List[List[str]]:
    actions = []

    for line in plan_lines:
        line = line.strip()

        match = re.match(r"^([A-Za-z_-]+)\((.*)\)$", line)
        if not match:
            raise ValueError(f"Invalid parsed plan line: {line}")

        action_name = match.group(1)
        args_text = match.group(2)
        args = [arg.strip().upper() for arg in args_text.split(",") if arg.strip()]

        actions.append([action_name] + args)

    return actions


def run_planner_and_parse_plan(
    domain_path: Path,
    problem_path: Path,
    plan_output_dir: Path,
    problem_id: str,
    heuristic: str,
    search: str,
) -> Tuple[bool, List[str], Optional[str]]:
    remove_old_solution_files(problem_path)

    result = run_pyperplan(
        domain=domain_path,
        problem=problem_path,
        heuristic=heuristic,
        search=search,
    )

    if result.returncode != 0:
        return False, [], "planner_error"

    solution_file = find_solution_file(problem_path)

    if solution_file is None:
        combined_output = (result.stdout + "\n" + result.stderr).strip()
        error_lines = combined_output.splitlines()[-8:]
        error_message = " | ".join(error_lines)
        return False, [], f"planner_no_solution_file: {error_message}"

    raw_plan_text = solution_file.read_text(encoding="utf-8")   
    plan_lines = parse_plan_text(raw_plan_text)

    if not plan_lines:
        return False, [], "plan_parse_error"

    plan_output_dir.mkdir(parents=True, exist_ok=True)
    plan_output_path = plan_output_dir / f"{problem_id}.txt"
    plan_output_path.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    return True, plan_lines, None


def write_csv(csv_path: Path, rows: List[Dict[str, Any]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


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
        config = LLMConfig(
            mode="hf",
            model=args.model or os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            api_key=args.api_key or os.getenv("HF_TOKEN"),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMClient(config=config)

    if args.mode == "local":
        config = LLMConfig(
            mode="local",
            model=args.model or os.getenv("LOCAL_LLM_MODEL", "local-model"),
            base_url=args.base_url or os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=args.api_key or os.getenv("LOCAL_LLM_API_KEY", ""),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMClient(config=config)

    raise ValueError("Mode must be either 'hf' or 'local'.")


def make_failure_row(
    record: Dict[str, Any],
    method: str,
    runtime: float,
    error_type: str,
    json_parse_success: bool = False,
    pddl_generated: bool = False,
    planner_success: bool = False,
    plan_valid: bool = False,
    goal_achieved: bool = False,
    plan_length: int = 0,
) -> Dict[str, Any]:
    return {
        "id": record["id"],
        "difficulty": record["difficulty"],
        "method": method,
        "json_parse_success": json_parse_success,
        "pddl_generated": pddl_generated,
        "planner_success": planner_success,
        "plan_valid": plan_valid,
        "goal_achieved": goal_achieved,
        "success": False,
        "plan_length": plan_length,
        "runtime": f"{runtime:.4f}",
        "error_type": error_type,
    }


def run_pipeline(
    data_path: Path,
    prompt_path: Path,
    domain_path: Path,
    pddl_output_dir: Path,
    raw_output_dir: Path,
    plan_output_dir: Path,
    csv_path: Path,
    limit: Optional[int],
    client: LLMClient,
    heuristic: str,
    search: str,
) -> None:
    records = load_jsonl(data_path, limit=limit)
    prompt_template = load_prompt_template(prompt_path)

    method = f"llm_to_json_planner_{client.config.mode}"
    rows = []

    for record in records:
        start_time = time.perf_counter()
        problem_id = record["id"]

        print(f"Running {method} for {problem_id}...")

        try:
            prompt = prompt_template.replace(
                "{natural_language}",
                record["natural_language"],
            )

            raw_output = client.generate(prompt)
            write_raw_output(raw_output_dir, method, problem_id, raw_output)

            try:
                structured = parse_llm_json(raw_output)
                json_parse_success = True
            except Exception as exc:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_failure_row(
                        record=record,
                        method=method,
                        runtime=runtime,
                        error_type=f"json_parse_error: {exc}",
                    )
                )
                print(f"FAIL {problem_id}: json_parse_error")
                continue

            try:
                generated_problem = structured_json_to_problem_record(record, structured)
                problem_path = write_pddl_problem(generated_problem, pddl_output_dir)
                pddl_generated = True
            except Exception as exc:
                runtime = time.perf_counter() - start_time
                rows.append(
                    make_failure_row(
                        record=record,
                        method=method,
                        runtime=runtime,
                        error_type=f"pddl_generation_error: {exc}",
                        json_parse_success=json_parse_success,
                    )
                )
                print(f"FAIL {problem_id}: pddl_generation_error")
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
                    make_failure_row(
                        record=record,
                        method=method,
                        runtime=runtime,
                        error_type=planner_error or "planner_error",
                        json_parse_success=json_parse_success,
                        pddl_generated=pddl_generated,
                    )
                )
                print(f"FAIL {problem_id}: {planner_error}")
                continue

            validator_actions = plan_lines_to_validator_actions(plan_lines)

            # Important:
            # Validate against the original dataset problem, not the LLM-generated JSON.
            # This catches cases where the LLM produced a valid but semantically wrong JSON problem.
            validation = validate_plan(
                initial_state=record["initial_state"],
                goal=record["goal"],
                actions=validator_actions,
                objects=record["objects"],
            )

            plan_valid = bool(validation["valid"])
            goal_achieved = bool(validation["goal_achieved"])
            success = bool(plan_valid and goal_achieved)
            plan_length = len(validator_actions)
            runtime = time.perf_counter() - start_time

            rows.append(
                {
                    "id": problem_id,
                    "difficulty": record["difficulty"],
                    "method": method,
                    "json_parse_success": json_parse_success,
                    "pddl_generated": pddl_generated,
                    "planner_success": planner_success,
                    "plan_valid": plan_valid,
                    "goal_achieved": goal_achieved,
                    "success": success,
                    "plan_length": plan_length,
                    "runtime": f"{runtime:.4f}",
                    "error_type": validation["error_type"] or "",
                }
            )

            if success:
                print(f"OK {problem_id}: success, length={plan_length}")
            else:
                print(f"FAIL {problem_id}: {validation['error_type']}")

        except Exception as exc:
            runtime = time.perf_counter() - start_time
            rows.append(
                make_failure_row(
                    record=record,
                    method=method,
                    runtime=runtime,
                    error_type=f"unexpected_error: {exc}",
                )
            )
            print(f"FAIL {problem_id}: unexpected_error")

    write_csv(csv_path, rows)
    print(f"Wrote {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to JSONL dataset")
    parser.add_argument("--limit", type=int, default=None)

    parser.add_argument(
        "--prompt",
        default="src/prompts/llm_to_json_prompt.txt",
        help="Path to prompt template",
    )
    parser.add_argument(
        "--domain",
        default="pddl/domain_blocks_world.pddl",
        help="Path to PDDL domain",
    )
    parser.add_argument(
        "--pddl-output-dir",
        default="pddl/problems/llm_to_json",
        help="Directory for generated PDDL problems",
    )
    parser.add_argument(
        "--raw-output-dir",
        default="results/raw_outputs/llm_to_json",
        help="Directory for raw LLM outputs",
    )
    parser.add_argument(
        "--plan-output-dir",
        default="results/plans/llm_to_json",
        help="Directory for parsed planner plans",
    )
    parser.add_argument(
        "--output-csv",
        default="results/llm_planner_results.csv",
        help="Path to output CSV",
    )

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

    parser.add_argument("-H", "--heuristic", default="hff")
    parser.add_argument("-s", "--search", default="gbf")

    args = parser.parse_args()

    client = build_client_from_args(args)

    run_pipeline(
        data_path=Path(args.data),
        prompt_path=Path(args.prompt),
        domain_path=Path(args.domain),
        pddl_output_dir=Path(args.pddl_output_dir),
        raw_output_dir=Path(args.raw_output_dir),
        plan_output_dir=Path(args.plan_output_dir),
        csv_path=Path(args.output_csv),
        limit=args.limit,
        client=client,
        heuristic=args.heuristic,
        search=args.search,
    )


if __name__ == "__main__":
    main()