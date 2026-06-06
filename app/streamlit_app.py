import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import os
from dotenv import load_dotenv

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


def make_client(
    backend: str,
    model_name: str,
    local_api_url: str,
    temperature: float,
    max_tokens: int,
) -> LLMClient:
    load_dotenv()

    if backend == "hf":
        config = LLMConfig(
            mode="hf",
            model=model_name,
            api_key=os.getenv("HF_TOKEN"),
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        config = LLMConfig(
            mode="local",
            model=model_name,
            base_url=local_api_url,
            api_key=os.getenv("LOCAL_LLM_API_KEY", ""),
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

def format_bool(value: bool) -> str:
    return "✅ Yes" if value else "❌ No"


def format_plan_steps(plan_text: str) -> str:
    if not plan_text.strip():
        return "<no plan>"

    lines = [line.strip() for line in plan_text.splitlines() if line.strip()]
    return "\n".join(f"{idx}. {line}" for idx, line in enumerate(lines, start=1))


def summarize_validator_result(result: Dict[str, Any]) -> Dict[str, Any]:
    validator = result["validator_result"]

    return {
        "Valid": format_bool(bool(validator.get("valid"))),
        "Goal achieved": format_bool(bool(validator.get("goal_achieved"))),
        "Error type": validator.get("error_type") or "None",
        "Failed step": validator.get("failed_step") or "None",
        "Runtime": f"{result['runtime']:.2f}s",
    }


def show_problem_summary(problem: Dict[str, Any]) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Objects", len(problem["objects"]))

    with col2:
        st.metric("Initial facts", len(problem["initial_state"]))

    with col3:
        st.metric("Goals", len(problem["goal"]))

    st.caption(f"Difficulty: `{problem.get('difficulty', 'demo')}`")

def show_result(result: Dict[str, Any]) -> None:
    validator_result = result["validator_result"]
    problem = result["problem"]

    is_success = bool(
        validator_result.get("valid")
        and validator_result.get("goal_achieved")
    )

    st.subheader("Result")

    if is_success:
        st.success("Plan is valid and goal is achieved.")
    else:
        st.error(validator_result.get("reason", "Plan failed."))

    show_problem_summary(problem)

    summary = summarize_validator_result(result)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Valid", summary["Valid"])

    with col2:
        st.metric("Goal", summary["Goal achieved"])

    with col3:
        st.metric("Runtime", summary["Runtime"])

    with col4:
        error_type = summary["Error type"]
        st.metric("Error", error_type if error_type != "None" else "None")

    st.divider()

    st.subheader("Generated Plan")
    st.code(format_plan_steps(result.get("plan_text", "")), language="text")

    st.subheader("Step-by-step State")
    st.code(result.get("rendered_plan", "") or "<no rendered plan>", language="text")

    if result["method"] == "llm_planner":
        with st.expander("Structured JSON", expanded=False):
            structured_json = result.get("structured_json")

            if structured_json is None:
                st.info("JSON was not parsed.")
            else:
                st.json(structured_json)

        with st.expander("Generated PDDL", expanded=False):
            st.code(
                result.get("pddl_text", "") or "<PDDL was not generated>",
                language="lisp",
            )

    with st.expander("Raw LLM output", expanded=False):
        st.code(result.get("raw_output", "") or "<empty>", language="text")

    with st.expander("Full validator result", expanded=False):
        st.json(validator_result)


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

        st.header("Model Settings")

        backend = st.selectbox(
            "Backend",
            ["hf", "local"],
            format_func=lambda value: {
                "hf": "Hugging Face",
                "local": "Local API",
            }[value],
            help="Choose where the language model is served from.",
        )

        if backend == "hf":
            model_name = st.text_input(
                "Model name",
                value="Qwen/Qwen2.5-7B-Instruct",
                help="Hugging Face model id.",
            )
            local_api_url = ""
        else:
            model_name = st.text_input(
                "Model name",
                value="local-model",
                help="Model name exposed by your local API server.",
            )
            local_api_url = st.text_input(
                "Local API URL",
                value="http://localhost:8000/v1",
                help="OpenAI-compatible local API base URL.",
            )

        st.caption("API tokens are loaded from `.env`, not from the UI.")

        with st.expander("Advanced settings", expanded=False):
            temperature = st.number_input(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.1,
            )

            max_tokens = st.number_input(
                "Max output tokens",
                min_value=64,
                max_value=4096,
                value=512,
                step=64,
            )

            heuristic = st.text_input(
                "Planner heuristic",
                value="hff",
                help="Heuristic used by pyperplan.",
            )

            search = st.text_input(
                "Planner search",
                value="gbf",
                help="Search algorithm used by pyperplan.",
            )

    task_text = st.text_area(
        "Natural language task",
        key="task_text",
        height=180,
    )

    col1, col2 = st.columns(2)

    with col1:
        run_llm_only_clicked = st.button("Generate Direct Plan", use_container_width=True)

    with col2:
        run_llm_planner_clicked = st.button("Generate Planner-backed Plan", use_container_width=True)

    if run_llm_only_clicked or run_llm_planner_clicked:
        if not task_text.strip():
            st.warning("Please enter a natural language task.")
            return

        try:
            client = make_client(
                backend=backend,
                model_name=model_name,
                local_api_url=local_api_url,
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

    tab1, tab2 = st.tabs(["Direct LLM Plan", "LLM → JSON → Planner"])

    with tab1:
        result = st.session_state.llm_only_result

        if result is None:
            st.info("Click **Run LLM-only** to generate a plan directly from the task.")
        else:
            show_result(result)

    with tab2:
        result = st.session_state.llm_planner_result

        if result is None:
            st.info("Click **Run LLM + Planner** to convert the task to JSON/PDDL and solve it with pyperplan.")
        else:
            show_result(result)


if __name__ == "__main__":
    main()