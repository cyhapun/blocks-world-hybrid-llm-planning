import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from llm_client import LLMClient, LLMConfig
from llm_only_baseline import parse_plan as parse_llm_plan
from llm_to_json import (
    parse_llm_json,
    plan_lines_to_validator_actions,
    run_planner_and_parse_plan,
    structured_json_to_problem_record,
    write_pddl_problem,
)
from render_plan import render_plan
from validate_plan import validate_plan


EXAMPLES = {
    "Example 1: Easy": {
        "id": "demo_easy",
        "difficulty": "easy",
        "objects": ["A", "B", "C"],
        "initial_state": [
            ["on_table", "A"],
            ["on_table", "B"],
            ["on", "C", "A"],
            ["clear", "C"],
            ["clear", "B"],
            ["handempty"],
        ],
        "goal": [
            ["on", "B", "C"],
        ],
        "natural_language": (
            "Initially, A and B are on the table, C is on A. "
            "C and B are clear. The hand is empty. "
            "The goal is to put B on C."
        ),
    },
    "Example 2: Medium": {
        "id": "demo_medium",
        "difficulty": "medium",
        "objects": ["A", "B", "C", "D"],
        "initial_state": [
            ["on_table", "A"],
            ["on", "B", "A"],
            ["on_table", "C"],
            ["on_table", "D"],
            ["clear", "B"],
            ["clear", "C"],
            ["clear", "D"],
            ["handempty"],
        ],
        "goal": [
            ["on", "D", "B"],
        ],
        "natural_language": (
            "Initially, A is on the table, B is on A, C is on the table, "
            "and D is on the table. B, C, and D are clear. "
            "The hand is empty. The goal is to put D on B."
        ),
    },
    "Example 3: Hard": {
        "id": "demo_hard",
        "difficulty": "hard",
        "objects": ["A", "B", "C", "D", "E"],
        "initial_state": [
            ["on_table", "A"],
            ["on", "B", "A"],
            ["on_table", "C"],
            ["on", "D", "C"],
            ["on_table", "E"],
            ["clear", "B"],
            ["clear", "D"],
            ["clear", "E"],
            ["handempty"],
        ],
        "goal": [
            ["on", "E", "B"],
            ["on", "D", "A"],
        ],
        "natural_language": (
            "Initially, A is on the table, B is on A, C is on the table, "
            "D is on C, and E is on the table. B, D, and E are clear. "
            "The hand is empty. The goal is to put E on B and D on A."
        ),
    },
}


LLM_ONLY_PROMPT = """You are solving a Blocks World planning task.

Available actions:
- pick-up(x)
- put-down(x)
- stack(x, y)
- unstack(x, y)

Return only the action list, one action per line.
Do not include explanations, markdown, comments, or extra text.

Task:
{natural_language}
"""


LLM_TO_JSON_PROMPT = """Convert the following Blocks World task into JSON.

Return only valid JSON with this schema:
{
  "objects": ["A", "B", "C"],
  "init": [
    ["on_table", "A"],
    ["on", "C", "A"],
    ["clear", "C"],
    ["handempty"]
  ],
  "goal": [
    ["on", "B", "C"]
  ]
}

Allowed predicates:
- on_table(x)
- on(x, y)
- clear(x)
- holding(x)
- handempty

Rules:
- Return JSON only.
- Do not include markdown.
- Do not include explanations.
- Use uppercase block names, such as A, B, C.
- Use "on_table", not "on-table".

Task:
{natural_language}
"""


def init_session_state() -> None:
    if "selected_example" not in st.session_state:
        st.session_state.selected_example = "Example 1: Easy"

    if "task_text" not in st.session_state:
        st.session_state.task_text = EXAMPLES["Example 1: Easy"]["natural_language"]

    if "current_problem" not in st.session_state:
        st.session_state.current_problem = EXAMPLES["Example 1: Easy"]

    if "llm_only_result" not in st.session_state:
        st.session_state.llm_only_result = None

    if "llm_planner_result" not in st.session_state:
        st.session_state.llm_planner_result = None


def set_example(example_name: str) -> None:
    example = EXAMPLES[example_name]
    st.session_state.selected_example = example_name
    st.session_state.task_text = example["natural_language"]
    st.session_state.current_problem = example
    st.session_state.llm_only_result = None
    st.session_state.llm_planner_result = None


def make_client(mode: str, model: str, base_url: str, api_key: str, temperature: float, max_tokens: int) -> LLMClient:
    if mode == "hf":
        config = LLMConfig(
            mode="hf",
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        config = LLMConfig(
            mode="local",
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return LLMClient(config=config)


def normalize_action_for_display(action: List[str]) -> str:
    name = action[0]
    args = action[1:]
    return f"{name}({','.join(args)})"


def parse_action_lines_for_render(plan_lines: List[str]) -> List[List[str]]:
    return plan_lines_to_validator_actions(plan_lines)


def make_problem_from_natural_language(natural_language: str) -> Dict[str, Any]:
    problem = dict(st.session_state.current_problem)
    problem["natural_language"] = natural_language
    return problem


def run_llm_only(
    natural_language: str,
    client: LLMClient,
) -> Dict[str, Any]:
    start_time = time.perf_counter()

    problem = make_problem_from_natural_language(natural_language)
    prompt = LLM_ONLY_PROMPT.replace("{natural_language}", natural_language)

    raw_output = ""
    actions: List[List[str]] = []
    parse_success = False
    validation: Dict[str, Any] = {
        "valid": False,
        "goal_achieved": False,
        "failed_step": None,
        "error_type": "not_run",
        "reason": "Validation was not run.",
    }

    try:
        raw_output = client.generate(prompt)
    except Exception as exc:
        runtime = time.perf_counter() - start_time
        return {
            "method": "llm_only",
            "problem": problem,
            "raw_output": raw_output,
            "actions": actions,
            "plan_text": "",
            "parse_success": False,
            "validator_result": validation | {
                "error_type": "llm_error",
                "reason": str(exc),
            },
            "runtime": runtime,
            "rendered_plan": "",
        }

    parse_success, actions, parse_error = parse_llm_plan(raw_output)

    if parse_success:
        validation = validate_plan(
            initial_state=problem["initial_state"],
            goal=problem["goal"],
            actions=actions,
            objects=problem["objects"],
        )
    else:
        validation = {
            "valid": False,
            "goal_achieved": False,
            "failed_step": None,
            "error_type": "parse_error",
            "reason": parse_error or "Failed to parse LLM output.",
        }

    plan_text = "\n".join(normalize_action_for_display(action) for action in actions)

    rendered_plan = ""
    if actions:
        try:
            rendered_plan = render_plan(problem, actions)
        except Exception as exc:
            rendered_plan = f"Could not render plan: {exc}"

    runtime = time.perf_counter() - start_time

    return {
        "method": "llm_only",
        "problem": problem,
        "raw_output": raw_output,
        "actions": actions,
        "plan_text": plan_text,
        "parse_success": parse_success,
        "validator_result": validation,
        "runtime": runtime,
        "rendered_plan": rendered_plan,
    }


def run_llm_planner(
    natural_language: str,
    client: LLMClient,
    heuristic: str,
    search: str,
) -> Dict[str, Any]:
    start_time = time.perf_counter()

    source_problem = make_problem_from_natural_language(natural_language)
    prompt = LLM_TO_JSON_PROMPT.replace("{natural_language}", natural_language)

    raw_output = ""
    structured_json: Optional[Dict[str, Any]] = None
    pddl_text = ""
    plan_lines: List[str] = []
    actions: List[List[str]] = []

    validation: Dict[str, Any] = {
        "valid": False,
        "goal_achieved": False,
        "failed_step": None,
        "error_type": "not_run",
        "reason": "Validation was not run.",
    }

    try:
        raw_output = client.generate(prompt)
    except Exception as exc:
        runtime = time.perf_counter() - start_time
        return {
            "method": "llm_planner",
            "problem": source_problem,
            "raw_output": raw_output,
            "structured_json": structured_json,
            "pddl_text": pddl_text,
            "plan_text": "",
            "validator_result": validation | {
                "error_type": "llm_error",
                "reason": str(exc),
            },
            "runtime": runtime,
            "rendered_plan": "",
        }

    try:
        structured_json = parse_llm_json(raw_output)
    except Exception as exc:
        runtime = time.perf_counter() - start_time
        return {
            "method": "llm_planner",
            "problem": source_problem,
            "raw_output": raw_output,
            "structured_json": structured_json,
            "pddl_text": pddl_text,
            "plan_text": "",
            "validator_result": validation | {
                "error_type": "json_parse_error",
                "reason": str(exc),
            },
            "runtime": runtime,
            "rendered_plan": "",
        }

    try:
        generated_problem = structured_json_to_problem_record(
            source_record=source_problem,
            structured=structured_json,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pddl_dir = tmp_path / "pddl"
            plan_dir = tmp_path / "plans"

            problem_path = write_pddl_problem(
                problem_record=generated_problem,
                output_dir=pddl_dir,
            )

            pddl_text = problem_path.read_text(encoding="utf-8")

            planner_success, plan_lines, planner_error = run_planner_and_parse_plan(
                domain_path=ROOT_DIR / "pddl" / "domain_blocks_world.pddl",
                problem_path=problem_path,
                plan_output_dir=plan_dir,
                problem_id=source_problem["id"],
                heuristic=heuristic,
                search=search,
            )

            if not planner_success:
                runtime = time.perf_counter() - start_time
                return {
                    "method": "llm_planner",
                    "problem": source_problem,
                    "raw_output": raw_output,
                    "structured_json": structured_json,
                    "pddl_text": pddl_text,
                    "plan_text": "",
                    "validator_result": validation | {
                        "error_type": "planner_error",
                        "reason": planner_error or "Planner failed.",
                    },
                    "runtime": runtime,
                    "rendered_plan": "",
                }

        actions = parse_action_lines_for_render(plan_lines)

        # Validate against the original problem, not LLM-generated problem.
        validation = validate_plan(
            initial_state=source_problem["initial_state"],
            goal=source_problem["goal"],
            actions=actions,
            objects=source_problem["objects"],
        )

    except Exception as exc:
        runtime = time.perf_counter() - start_time
        return {
            "method": "llm_planner",
            "problem": source_problem,
            "raw_output": raw_output,
            "structured_json": structured_json,
            "pddl_text": pddl_text,
            "plan_text": "\n".join(plan_lines),
            "validator_result": validation | {
                "error_type": "unexpected_error",
                "reason": str(exc),
            },
            "runtime": runtime,
            "rendered_plan": "",
        }

    plan_text = "\n".join(plan_lines)

    rendered_plan = ""
    if actions:
        try:
            rendered_plan = render_plan(source_problem, actions)
        except Exception as exc:
            rendered_plan = f"Could not render plan: {exc}"

    runtime = time.perf_counter() - start_time

    return {
        "method": "llm_planner",
        "problem": source_problem,
        "raw_output": raw_output,
        "structured_json": structured_json,
        "pddl_text": pddl_text,
        "plan_text": plan_text,
        "validator_result": validation,
        "runtime": runtime,
        "rendered_plan": rendered_plan,
    }


def show_result(result: Dict[str, Any]) -> None:
    validator_result = result["validator_result"]

    st.subheader("Validator Result")

    if validator_result.get("valid") and validator_result.get("goal_achieved"):
        st.success("Plan is valid and goal is achieved.")
    else:
        st.error("Plan failed validation or did not reach the goal.")

    st.json(validator_result)

    st.caption(f"Runtime: {result['runtime']:.4f}s")

    st.subheader("Raw LLM Output")
    st.code(result.get("raw_output", "") or "<empty>", language="text")

    if result["method"] == "llm_planner":
        st.subheader("Structured JSON")
        structured_json = result.get("structured_json")

        if structured_json is None:
            st.code("<JSON was not parsed>", language="text")
        else:
            st.json(structured_json)

        st.subheader("Generated PDDL")
        st.code(result.get("pddl_text", "") or "<PDDL was not generated>", language="lisp")

    st.subheader("Plan")
    st.code(result.get("plan_text", "") or "<no plan>", language="text")

    st.subheader("Step-by-step Blocks World State")
    st.code(result.get("rendered_plan", "") or "<no rendered plan>", language="text")


def main() -> None:
    st.set_page_config(
        page_title="Blocks World Planning Demo",
        page_icon="🧱",
        layout="wide",
    )

    init_session_state()

    st.title("Blocks World LLM Planning Demo")

    st.markdown(
        "Demo so sánh **LLM-only** và **LLM + symbolic planner** cho Blocks World."
    )

    with st.sidebar:
        st.header("Examples")

        example_name = st.selectbox(
            "Choose an example",
            list(EXAMPLES.keys()),
            index=list(EXAMPLES.keys()).index(st.session_state.selected_example),
        )

        if st.button("Load example"):
            set_example(example_name)
            st.rerun()

        st.header("LLM Settings")

        mode = st.selectbox(
            "LLM mode",
            ["hf", "local"],
            index=0,
            help="hf = Hugging Face Inference API, local = OpenAI-compatible local API",
        )

        default_model = "Qwen/Qwen2.5-7B-Instruct" if mode == "hf" else "local-model"

        model = st.text_input("Model", value=default_model)

        base_url = ""
        if mode == "local":
            base_url = st.text_input(
                "Local base URL",
                value="http://localhost:8000/v1",
            )

        api_key = st.text_input(
            "API key / token",
            value="",
            type="password",
            help="HF token for hf mode, optional local API key for local mode.",
        )

        temperature = st.number_input(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
        )

        max_tokens = st.number_input(
            "Max tokens",
            min_value=64,
            max_value=4096,
            value=512,
            step=64,
        )

        st.header("Planner Settings")

        heuristic = st.text_input("Heuristic", value="hff")
        search = st.text_input("Search", value="gbf")

    task_text = st.text_area(
        "Natural language task",
        key="task_text",
        height=180,
    )

    col1, col2 = st.columns(2)

    with col1:
        run_llm_only_clicked = st.button("Run LLM-only", use_container_width=True)

    with col2:
        run_llm_planner_clicked = st.button("Run LLM + Planner", use_container_width=True)

    if run_llm_only_clicked or run_llm_planner_clicked:
        if not task_text.strip():
            st.warning("Please enter a natural language task.")
            return

        try:
            client = make_client(
                mode=mode,
                model=model,
                base_url=base_url,
                api_key=api_key,
                temperature=float(temperature),
                max_tokens=int(max_tokens),
            )
        except Exception as exc:
            st.error(f"Could not initialize LLM client: {exc}")
            return

        if run_llm_only_clicked:
            with st.spinner("Running LLM-only baseline..."):
                st.session_state.llm_only_result = run_llm_only(
                    natural_language=task_text,
                    client=client,
                )

        if run_llm_planner_clicked:
            with st.spinner("Running LLM + Planner pipeline..."):
                st.session_state.llm_planner_result = run_llm_planner(
                    natural_language=task_text,
                    client=client,
                    heuristic=heuristic,
                    search=search,
                )

    tab1, tab2 = st.tabs(["LLM-only", "LLM + Planner"])

    with tab1:
        result = st.session_state.llm_only_result

        if result is None:
            st.info("Click **Run LLM-only** to generate a direct plan.")
        else:
            show_result(result)

    with tab2:
        result = st.session_state.llm_planner_result

        if result is None:
            st.info("Click **Run LLM + Planner** to run JSON/PDDL/planner pipeline.")
        else:
            show_result(result)


if __name__ == "__main__":
    main()