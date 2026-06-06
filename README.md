# Blocks World LLM Planning Evaluation

A lightweight framework for evaluating LLM-based planning on Blocks World tasks. The project includes a PDDL domain, JSONL problem datasets, plan validation, planner integration, evaluation utilities, visualization, and an optional Streamlit interface.

## Project Structure

```text
blocks-world-hybrid-llm-planing
├── README.md
├── requirements.txt
├── config.yaml
├── data/
│   ├── blocks_world_easy.jsonl
│   ├── blocks_world_medium.jsonl
│   └── blocks_world_hard.jsonl
├── pddl/
│   ├── domain_blocks_world.pddl
│   └── generated_problems/
├── src/
│   ├── generate_dataset.py
│   ├── check_dataset.py
│   ├── llm_baseline.py
│   ├── llm_to_json.py
│   ├── json_to_pddl.py
│   ├── run_planner.py
│   ├── validate_plan.py
│   ├── evaluate.py
│   └── visualize.py
├── tests/
│   └── test_validator.py
├── results/
│   ├── raw_outputs/
│   ├── metrics.csv
│   └── figures/
└── app/
    └── streamlit_app.py
```

## Setup

```bash
pip install -r requirements.txt
```

## Dataset

Blocks World tasks are stored as JSONL files under `data/`.

Each line contains one problem instance:

```json
{
  "id": "bw_easy_001",
  "difficulty": "easy",
  "objects": ["A", "B", "C"],
  "initial_state": [
    ["on_table", "A"],
    ["on_table", "B"],
    ["on", "C", "A"],
    ["clear", "C"],
    ["clear", "B"],
    ["handempty"]
  ],
  "goal": [
    ["on", "B", "C"]
  ],
  "natural_language": "Initially, A and B are on the table, C is on A. C and B are clear. The hand is empty. The goal is to put B on C."
}
```

Dataset files:

```text
data/blocks_world_easy.jsonl
data/blocks_world_medium.jsonl
data/blocks_world_hard.jsonl
```

Validate dataset files:

```bash
python src/check_dataset.py --data data/blocks_world_easy.jsonl
python src/check_dataset.py --data data/blocks_world_medium.jsonl
python src/check_dataset.py --data data/blocks_world_hard.jsonl
```

## PDDL Domain

The Blocks World domain is defined in:

```text
pddl/domain_blocks_world.pddl
```

Supported actions:

```text
pick-up(x)
put-down(x)
stack(x, y)
unstack(x, y)
```

Core predicates:

```text
on(x, y)
on_table(x)
clear(x)
holding(x)
handempty
```

## Plan Validator

The validator is implemented in:

```text
src/validate_plan.py
```

It simulates Blocks World actions, checks preconditions, applies effects, and verifies final goal satisfaction.

Run demo:

```bash
python src/validate_plan.py --demo
```

Example result:

```json
{
  "valid": true,
  "goal_achieved": true,
  "failed_step": null,
  "error_type": null,
  "reason": "Plan is valid and goal is achieved."
}
```

Possible error types include:

```text
invalid_problem
invalid_action_format
unknown_action
invalid_action
unknown_object
precondition_violation
goal_not_achieved
```

## Tests

Run validator tests:

```bash
pytest tests/test_validator.py
```

Run syntax check:

```bash
python -m py_compile src/check_dataset.py src/validate_plan.py tests/test_validator.py
```

## Typical Workflow

Generate or validate dataset:

```bash
python src/generate_dataset.py
python src/check_dataset.py --data data/blocks_world_easy.jsonl
```

Convert JSON problems to PDDL:

```bash
python src/json_to_pddl.py
```

Run external planner:

```bash
python src/run_planner.py
```

Validate generated plan:

```bash
python src/validate_plan.py --demo
```

Evaluate results:

```bash
python src/evaluate.py
```

Visualize metrics:

```bash
python src/visualize.py
```

Launch app:

```bash
streamlit run app/streamlit_app.py
```

## Outputs

Generated artifacts are stored under:

```text
pddl/generated_problems/
results/raw_outputs/
results/metrics.csv
results/figures/
```

## Symbolic Planner

Convert JSONL problem to PDDL:

```bash
python src/json_to_pddl.py --input data/blocks_world_easy.jsonl --index 0
```

Run pyperplan:

```bash
python src/run_planner.py --problem pddl/problems/bw_easy_001.pddl
```

Validate generated plan:

```bash
python src/validate_plan.py --problem-id bw_easy_001 --plan results/example_plan.txt
```

## LLM-only Baseline

The LLM-only baseline asks a language model to generate a Blocks World plan directly from the natural-language task description.

Supported modes:

```text
hf      Hugging Face Inference API
local   Local OpenAI-compatible chat completion API
```

Create local environment config:

```bash
cp .env.example .env
```

Run with Hugging Face:

```bash
LLM_MODE=hf python src/llm_only_baseline.py --data data/blocks_world_easy.jsonl --limit 3
```

Run with local API:

```bash
LLM_MODE=local python src/llm_only_baseline.py --data data/blocks_world_easy.jsonl --limit 3
```

Outputs:

```text
results/raw_outputs/llm_only/
results/llm_only_results.csv
```

CSV columns:

```text
id,difficulty,method,raw_output,parse_success,plan_valid,goal_achieved,success,plan_length,error_type
```

## LLM-to-JSON-to-PDDL Pipeline

This pipeline asks an LLM to convert a natural-language Blocks World task into structured JSON. The JSON is converted to a PDDL problem, solved by pyperplan, and validated against the original dataset problem.

Run with Hugging Face mode:

```bash
LLM_MODE=hf python src/llm_to_json.py --data data/blocks_world_easy.jsonl --limit 3
```

Run with local API mode:

```bash
LLM_MODE=local python src/llm_to_json.py --data data/blocks_world_easy.jsonl --limit 3
```

Outputs:

```text
results/raw_outputs/llm_to_json/
pddl/problems/llm_to_json/
results/plans/llm_to_json/
results/llm_planner_results.csv
```

CSV columns:

```text
id,difficulty,method,json_parse_success,pddl_generated,planner_success,plan_valid,goal_achieved,success,plan_length,runtime,error_type
```

## Troubleshooting

If the planner fails with no solution found, even after pyperplan exits successfully, it may be due to an unsolvable problem generated from the LLM's JSON output.

Check error messages in results/llm_planner_results.csv under the error_type column, which may contain detailed pyperplan output indicating unsolvability.

Examples:

```text
planner_no_solution_file: 2026-06-06 11:58:40,765 INFO     24 Operators created | 2026-06-06 11:58:40,765 INFO     Search start: bw_easy_003 | 2026-06-06 11:58:40,765 INFO     Initial h value: inf | 2026-06-06 11:58:40,765 INFO     No operators left. Task unsolvable. | 2026-06-06 11:58:40,765 INFO     1 Nodes expanded | 2026-06-06 11:58:40,765 INFO     Search end: bw_easy_003 | 2026-06-06 11:58:40,765 INFO     Search time: 0.0 | 2026-06-06 11:58:40,765 WARNING  No solution could be found
```