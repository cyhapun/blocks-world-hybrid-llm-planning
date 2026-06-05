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