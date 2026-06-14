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


def load_css() -> None:
    """Load custom CSS theme from styles.css."""
    css_path = Path(__file__).parent / "styles.css"

    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


def render_app_header() -> None:
    """Render the styled application header."""
    st.markdown(
        '<div class="app-title"><h1>Blocks World LLM Planning</h1></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="app-subtitle">'
        "So sánh <strong>LLM‑only</strong> và "
        "<strong>LLM + Symbolic Planner</strong> "
        "cho bài toán Blocks World"
        "</p>",
        unsafe_allow_html=True,
    )


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
APP_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


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

from block_visualizer import render_plan_visual
from pipeline_viz import pipeline_html_for_result


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


DEFAULT_LLM_ONLY_PROMPT = """You are solving a Blocks World planning task.

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


DEFAULT_LLM_TO_JSON_PROMPT = """Convert the following Blocks World task into JSON.

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

    if "llm_only_prompt" not in st.session_state:
        st.session_state.llm_only_prompt = DEFAULT_LLM_ONLY_PROMPT

    if "llm_to_json_prompt" not in st.session_state:
        st.session_state.llm_to_json_prompt = DEFAULT_LLM_TO_JSON_PROMPT


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
    prompt_template = st.session_state.get("llm_only_prompt", DEFAULT_LLM_ONLY_PROMPT)
    prompt = prompt_template.replace("{natural_language}", natural_language)

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
    prompt_template = st.session_state.get("llm_to_json_prompt", DEFAULT_LLM_TO_JSON_PROMPT)
    prompt = prompt_template.replace("{natural_language}", natural_language)

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
                error_code, error_reason = normalize_pipeline_error(
                    planner_error,
                    "planner_error",
                )

                return {
                    "method": "llm_planner",
                    "problem": source_problem,
                    "raw_output": raw_output,
                    "structured_json": structured_json,
                    "pddl_text": pddl_text,
                    "plan_text": "",
                    "validator_result": validation | {
                        "error_type": error_code,
                        "reason": error_reason,
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
        "actions": actions,
        "validator_result": validation,
        "runtime": runtime,
        "rendered_plan": rendered_plan,
    }

def format_bool(value: bool) -> str:
    return "Yes" if value else "No"


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

def split_error_message(error_type: str | None, reason: str | None) -> tuple[str, str]:
    raw = reason or error_type or ""

    if ":" in raw:
        short_error, technical_detail = raw.split(":", 1)
        return short_error.strip(), technical_detail.strip()

    return raw.strip() or "none", ""


def humanize_error(error_type: str | None, reason: str | None) -> tuple[str, str, str]:
    short_error, technical_detail = split_error_message(error_type, reason)

    if short_error in {"none", "None", ""}:
        return "No error", "The plan passed validation.", technical_detail

    messages = {
        "parse_error": "The model output could not be parsed into actions.",
        "json_parse_error": "The model output could not be parsed into valid structured JSON.",
        "pddl_generation_error": "The structured JSON could not be converted into a PDDL problem.",
        "planner_error": "The planner failed while solving the generated PDDL problem.",
        "planner_no_solution_file": "The planner could not find a solution for the generated problem.",
        "plan_parse_error": "The planner output could not be parsed into actions.",
        "precondition_violation": "The plan contains an action whose preconditions are not satisfied.",
        "goal_not_achieved": "The plan ran successfully, but the final goal was not achieved.",
        "unknown_action": "The plan contains an unsupported action.",
        "unknown_object": "The plan uses an object that does not exist in the problem.",
        "invalid_action": "The plan contains an invalid action.",
        "invalid_action_format": "The action format is invalid.",
        "invalid_problem": "The problem definition is invalid.",
        "llm_error": "The language model request failed.",
        "unexpected_error": "An unexpected error occurred.",
        "not_run": "This step was not run.",
    }

    friendly = messages.get(short_error, "An error occurred during the pipeline.")
    return short_error, friendly, technical_detail

def normalize_pipeline_error(raw_error: str | None, fallback: str) -> tuple[str, str]:
    if not raw_error:
        return fallback, fallback

    if ":" in raw_error:
        code, detail = raw_error.split(":", 1)
        return code.strip(), detail.strip()

    return raw_error.strip(), raw_error.strip()

def show_result(result: Dict[str, Any]) -> None:
    validator_result = result["validator_result"]
    error_code, error_message, technical_detail = humanize_error(
        validator_result.get("error_type"),
        validator_result.get("reason"),
    )
    problem = result["problem"]

    is_success = bool(
        validator_result.get("valid")
        and validator_result.get("goal_achieved")
    )

    # Pipeline progress indicator
    st.markdown(pipeline_html_for_result(result), unsafe_allow_html=True)

    st.subheader("Result")

    if is_success:
        st.success("Plan is valid and goal is achieved.")
    else:
        st.error(error_message)

        if error_code and error_code != "No error":
            st.caption(f"Error code: `{error_code}`")

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
        st.metric("Error", "None" if is_success else error_code)

    st.divider()

    st.subheader("Generated Plan")
    st.code(format_plan_steps(result.get("plan_text", "")), language="text")

    st.subheader("Step-by-step State")

    # Visual block rendering
    actions = result.get("actions", [])
    problem = result.get("problem", {})

    if actions and problem:
        try:
            visual_html = render_plan_visual(problem, actions)
            st.markdown(visual_html, unsafe_allow_html=True)
        except Exception:
            st.code(
                result.get("rendered_plan", "") or "<no rendered plan>",
                language="text",
            )
    else:
        st.info("No plan actions to visualize.")

    with st.expander("ASCII state trace", expanded=False):
        st.code(
            result.get("rendered_plan", "") or "<no rendered plan>",
            language="text",
        )

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

    if technical_detail:
        with st.expander("Technical error details", expanded=False):
            st.code(technical_detail, language="text")

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

    load_css()
    init_session_state()

    render_app_header()

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

        st.header("Prompt Templates")

        with st.expander("LLM-only prompt", expanded=False):
            st.markdown(
                '<div class="prompt-editor-label">Direct plan prompt</div>',
                unsafe_allow_html=True,
            )
            st.session_state.llm_only_prompt = st.text_area(
                "LLM-only prompt template",
                value=st.session_state.llm_only_prompt,
                height=200,
                key="_llm_only_prompt_editor",
                help="Use {natural_language} as placeholder for the task.",
                label_visibility="collapsed",
            )

            if st.button("↩ Reset", key="reset_llm_only_prompt"):
                st.session_state.llm_only_prompt = DEFAULT_LLM_ONLY_PROMPT
                st.rerun()

        with st.expander("LLM → JSON prompt", expanded=False):
            st.markdown(
                '<div class="prompt-editor-label">Structured JSON prompt</div>',
                unsafe_allow_html=True,
            )
            st.session_state.llm_to_json_prompt = st.text_area(
                "LLM-to-JSON prompt template",
                value=st.session_state.llm_to_json_prompt,
                height=300,
                key="_llm_to_json_prompt_editor",
                help="Use {natural_language} as placeholder for the task.",
                label_visibility="collapsed",
            )

            if st.button("↩ Reset", key="reset_llm_to_json_prompt"):
                st.session_state.llm_to_json_prompt = DEFAULT_LLM_TO_JSON_PROMPT
                st.rerun()

    task_text = st.text_area(
        "Natural language task",
        key="task_text",
        height=140,
    )

    # ── Action buttons ────────────────────────────────────────
    btn_col1, btn_col2, btn_col3 = st.columns([2, 3, 2])

    with btn_col1:
        run_llm_only_clicked = st.button(
            "LLM-only",
            use_container_width=True,
        )

    with btn_col2:
        st.markdown('<div class="run-both-btn">', unsafe_allow_html=True)
        run_both_clicked = st.button(
            "Run Both Methods",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with btn_col3:
        run_llm_planner_clicked = st.button(
            "LLM + Planner",
            use_container_width=True,
        )

    # Merge button flags
    if run_both_clicked:
        run_llm_only_clicked = True
        run_llm_planner_clicked = True

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

    # ── Comparison summary (when both results exist) ──────────
    r_llm = st.session_state.llm_only_result
    r_planner = st.session_state.llm_planner_result

    if r_llm is not None and r_planner is not None:
        _render_comparison_summary(r_llm, r_planner)

    # ── Side-by-side results ──────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown(
            '<div class="comparison-header">'
            '<span class="comparison-badge llm-only">LLM-only</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        if r_llm is None:
            st.info("Click **LLM-only** or **Run Both** to generate a direct plan.")
        else:
            show_result(r_llm)

    with right:
        st.markdown(
            '<div class="comparison-header">'
            '<span class="comparison-badge llm-planner">LLM + Planner</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        if r_planner is None:
            st.info("Click **LLM + Planner** or **Run Both** to solve via JSON/PDDL.")
        else:
            show_result(r_planner)


def _render_comparison_summary(r_llm: Dict, r_planner: Dict) -> None:
    """Render a compact comparison banner above the side-by-side results."""
    v_llm = r_llm["validator_result"]
    v_plan = r_planner["validator_result"]

    llm_ok = bool(v_llm.get("valid") and v_llm.get("goal_achieved"))
    plan_ok = bool(v_plan.get("valid") and v_plan.get("goal_achieved"))

    def _badge(ok: bool) -> str:
        if ok:
            return '<span class="status-badge success">Valid</span>'
        return '<span class="status-badge error">Failed</span>'

    st.markdown(
        '<div style="'
        "display:flex;align-items:center;justify-content:space-around;"
        "padding:0.75rem 1rem;margin:1rem 0;"
        "background:rgba(26,29,41,0.8);"
        "border:1px solid rgba(255,255,255,0.06);"
        "border-radius:12px;"
        '">'
        '<div style="text-align:center;">'
        '<div style="font-size:0.7rem;color:#8B92A5;margin-bottom:0.25rem;">LLM-only</div>'
        f"{_badge(llm_ok)}"
        f'<div style="font-size:0.7rem;color:#5A6178;margin-top:0.2rem;">{r_llm["runtime"]:.2f}s</div>'
        "</div>"
        '<div style="color:#3A3F4D;font-size:1.25rem;">vs</div>'
        '<div style="text-align:center;">'
        '<div style="font-size:0.7rem;color:#8B92A5;margin-bottom:0.25rem;">LLM + Planner</div>'
        f"{_badge(plan_ok)}"
        f'<div style="font-size:0.7rem;color:#5A6178;margin-top:0.2rem;">{r_planner["runtime"]:.2f}s</div>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()